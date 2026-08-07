"""A3 pre-screen: binding arithmetic, monotonicity, populations, survival.

The load-bearing test here is (f): floor binding must be monotonically
DECREASING in the multiplier. A wider stop cannot be floored more often -- the
floor is a constant and the raw distance rises with the multiplier, so a
violation anywhere is a bug in the binding computation, not a market fact.

A3 is evaluated on the GATED population at the 50% arm, per symbol, never
pooled (§4.4 -- the floors differ, so pooling would let SOL rescue BTC).
"""

import os
import sys

import numpy as np
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from src.folds import schedule as sch  # noqa: E402
from src.sweep import grid as gr  # noqa: E402
from src.sweep import prescreen as ps  # noqa: E402

DATA = os.path.join(sch.DERIVED, "ohlcv_15m", "BTCUSDT.parquet")
needs_data = pytest.mark.skipif(not os.path.exists(DATA),
                                reason="derived data not present")
SYMBOLS = gr.SYMBOLS


@pytest.fixture(scope="module")
def folds():
    return sch.build_schedule()


@pytest.fixture(scope="module")
def fold(folds):
    return folds[4]


@pytest.fixture(scope="module")
def rows(fold):
    return {s: ps.prescreen_fold_symbol(s, fold, gr.fold_symbol_grid(s, fold))
            for s in SYMBOLS}


# ---------------------------------------------------------------------------
# binding arithmetic, on fixtures with known answers
# ---------------------------------------------------------------------------

def test_binding_rates_are_exact_on_a_constructed_fixture():
    a = np.array([1.0, 2.0, 3.0, 4.0])       # ATR%
    # multiplier 1: raw = 1,2,3,4. floor 2.5 -> binds on 1,2 = 50%.
    #                              cap 3.5   -> binds on 4    = 25%.
    r = ps.binding_rates(a, 1.0, 2.5, 3.5)
    assert r["n"] == 4
    assert r["floor"] == 0.50 and r["cap"] == 0.25 and r["atr"] == 0.25
    assert r["floor"] + r["cap"] + r["atr"] == 1.0


def test_binding_uses_strict_inequalities_on_the_raw_distance():
    a = np.array([1.0])
    assert ps.binding_rates(a, 1.0, 1.0, 2.0)["floor"] == 0.0   # not <
    assert ps.binding_rates(a, 1.0, 1.01, 2.0)["floor"] == 1.0
    assert ps.binding_rates(a, 1.0, 0.5, 1.0)["cap"] == 0.0     # not >
    assert ps.binding_rates(a, 1.0, 0.5, 0.99)["cap"] == 1.0


def test_binding_rates_handle_an_empty_population():
    r = ps.binding_rates(np.array([]), 1.0, 1.0, 2.0)
    assert r["n"] == 0 and np.isnan(r["floor"])


def test_the_three_mechanisms_partition_the_population():
    rng = np.random.default_rng(0)
    a = rng.lognormal(-1, 0.5, 500)
    for mult in (0.5, 1.0, 3.0):
        r = ps.binding_rates(a, mult, 0.4, 1.2)
        assert r["floor"] + r["cap"] + r["atr"] == pytest.approx(1.0)


# ---------------------------------------------------------------------------
# (f) monotonicity -- a wider stop cannot be floored more often
# ---------------------------------------------------------------------------

@needs_data
@pytest.mark.parametrize("symbol", SYMBOLS)
def test_floor_binding_is_monotonically_decreasing(symbol, folds):
    for f in folds:
        r = ps.prescreen_fold_symbol(symbol, f, gr.fold_symbol_grid(symbol, f))
        for pop in ("breakout", "gated_30", "gated_50", "gated_70"):
            v = [x[pop]["floor"] for x in r]
            for i in range(len(v) - 1):
                assert v[i + 1] <= v[i] + 1e-12, (
                    f"{symbol} fold {f['fold_id']} {pop}: floor binding rose "
                    f"from {v[i]:.4f} to {v[i+1]:.4f} between grid points "
                    f"{i} and {i+1}. A wider stop cannot be floored more "
                    f"often -- this is a bug.")


@needs_data
def test_cap_binding_is_monotonically_increasing(rows):
    for s, r in rows.items():
        v = [x["breakout"]["cap"] for x in r]
        assert all(v[i] <= v[i + 1] + 1e-12 for i in range(len(v) - 1)), s


@needs_data
def test_a3_pass_flags_are_monotone_once_true(rows):
    """Since binding decreases monotonically, survivors form one suffix run."""
    for s, r in rows.items():
        flags = [x["a3_pass"] for x in r]
        if any(flags):
            first = flags.index(True)
            assert all(flags[first:]), s
            assert not any(flags[:first]), s


# ---------------------------------------------------------------------------
# populations
# ---------------------------------------------------------------------------

@needs_data
@pytest.mark.parametrize("symbol", SYMBOLS)
def test_gated_floor_binding_is_below_breakout_binding(symbol, folds):
    """Gated bars are higher-volume and, as hypothesised, higher-ATR."""
    for f in folds:
        r = ps.prescreen_fold_symbol(symbol, f, gr.fold_symbol_grid(symbol, f))
        for x in r:
            assert x["gated_50"]["floor"] <= x["breakout"]["floor"] + 1e-12, (
                f"{symbol} fold {f['fold_id']} offset {x['offset']}: gated "
                f"binding {x['gated_50']['floor']:.4f} exceeds breakout "
                f"{x['breakout']['floor']:.4f}")


@needs_data
def test_a3_is_decided_on_the_gated_fifty_percent_arm(rows):
    for s, r in rows.items():
        for x in r:
            assert x["a3_floor_binding"] == x["gated_50"]["floor"]
            assert x["a3_pass"] is (x["a3_floor_binding"] < 0.20)


@needs_data
def test_gated_population_is_about_half_the_breakout_population(rows):
    for s, r in rows.items():
        assert 0.48 < r[0]["gated_50"]["n"] / r[0]["breakout"]["n"] < 0.52


@needs_data
def test_all_three_rvol_arms_are_reported(rows):
    for s, r in rows.items():
        for x in r:
            for t in (30, 50, 70):
                assert f"gated_{t}" in x
            # A 70% arm admits more bars than a 30% arm.
            assert x["gated_70"]["n"] > x["gated_50"]["n"] > x["gated_30"]["n"]


@needs_data
def test_test_period_binding_is_reported_but_not_used_for_a3(rows):
    for s, r in rows.items():
        for x in r:
            assert "test_breakout" in x and "test_gated_50" in x
            # The criterion reads the TRAINING gated arm and nothing else.
            assert x["a3_floor_binding"] == x["gated_50"]["floor"]


# ---------------------------------------------------------------------------
# survival and plateau
# ---------------------------------------------------------------------------

def test_longest_run_arithmetic():
    assert ps.longest_run([False] * 5) == (0, None)
    assert ps.longest_run([True] * 4) == (4, 0)
    assert ps.longest_run([False, True, True, False, True]) == (2, 1)
    assert ps.longest_run([True, False, True, True, True]) == (3, 2)


def test_summarise_reports_survivors_and_the_plateau_flag():
    rows = [{"offset": i * 0.25, "multiplier": 1 + i * 0.25,
             "a3_pass": i >= 4} for i in range(11)]
    s = ps.summarise(rows)
    assert s["n_surviving"] == 7
    assert s["longest_contiguous_run"] == 7
    assert s["run_start_offset"] == 1.0
    assert s["viable_band"] is True


def test_viable_band_needs_three_contiguous_points():
    """§4.3: no contiguous run of three means the fold produces no selection."""
    assert gr.MIN_PLATEAU_RUN == 3
    two = [{"offset": i * 0.25, "multiplier": i, "a3_pass": i >= 9}
           for i in range(11)]
    assert ps.summarise(two)["viable_band"] is False
    three = [{"offset": i * 0.25, "multiplier": i, "a3_pass": i >= 8}
             for i in range(11)]
    assert ps.summarise(three)["viable_band"] is True


@needs_data
@pytest.mark.parametrize("symbol", SYMBOLS)
def test_every_fold_reports_a_summary(symbol, folds):
    for f in folds:
        r = ps.prescreen_fold_symbol(symbol, f, gr.fold_symbol_grid(symbol, f))
        s = ps.summarise(r)
        assert 0 <= s["n_surviving"] <= 11
        assert s["longest_contiguous_run"] <= s["n_surviving"]
        assert isinstance(s["viable_band"], bool)


@needs_data
def test_a3_never_passes_at_the_bottom_of_the_range(folds):
    """At m* the floor binds ~50% on breakout bars; the gated arm is lower but
    still well above 20%, so the range correctly starts where it does."""
    for s in SYMBOLS:
        for f in folds:
            r = ps.prescreen_fold_symbol(s, f, gr.fold_symbol_grid(s, f))
            assert not r[0]["a3_pass"], (
                f"{s} fold {f['fold_id']} passes A3 at m* itself, which would "
                f"mean the search range starts too high")


# ---------------------------------------------------------------------------
# the range is not extended
# ---------------------------------------------------------------------------

@needs_data
def test_prescreen_never_evaluates_a_point_outside_the_grid(rows):
    for s, r in rows.items():
        assert len(r) == 11
        offs = [x["offset"] for x in r]
        assert offs == [round(i * 0.25, 4) for i in range(11)]
        assert max(offs) == 2.5


def test_a3_threshold_is_the_pre_registered_twenty_percent():
    assert gr.A3_MAX_FLOOR_BINDING == 0.20
    assert gr.RVOL_TARGET_PRIMARY == 0.50


# ---------------------------------------------------------------------------
# artifact
# ---------------------------------------------------------------------------

@needs_data
def test_written_artifact_round_trips(tmp_path):
    folds = sch.build_schedule()[:1]
    grid, pre = ps.run_prescreen(("ETHUSDT",), folds)
    payload = gr.grid_payload(grid, ps._serialise(pre))
    path = str(tmp_path / "grid.json")
    gr.write_grid(path=path, payload=payload)
    got = gr.load_grid(path)
    assert got["git_commit"]
    cell = got["symbols"]["ETHUSDT"]["1"]
    assert len(cell["multipliers"]) == 11
    assert cell["stop_max_pct"] > 0
    assert set(got["prescreen"]["ETHUSDT"]["folds"]["1"]
               ["a3_floor_binding_by_offset"]) == {
        str(round(i * 0.25, 4)) for i in range(11)}


def test_load_grid_raises_when_missing(tmp_path):
    with pytest.raises(FileNotFoundError, match="grid missing"):
        gr.load_grid(str(tmp_path / "nope.json"))


@needs_data
def test_committed_artifact_matches_the_current_design():
    if not os.path.exists(gr.GRID_PATH):
        pytest.skip("grid.json not generated")
    on_disk = gr.load_grid()
    assert on_disk["design"]["stop_max_pct"].startswith("(m* + 2.5) x P95")
    for s in SYMBOLS:
        assert len(on_disk["symbols"][s]) == 9
        assert len(on_disk["symbols"][s]["1"]["multipliers"]) == 11
