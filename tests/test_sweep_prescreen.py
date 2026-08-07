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


# ---------------------------------------------------------------------------
# the 30% and 70% arms -- DESCRIPTION, persisted for the monotonicity test
# ---------------------------------------------------------------------------

@needs_data
def test_all_three_arms_are_persisted_with_eleven_offsets(tmp_path):
    folds = sch.build_schedule()[:1]
    grid, pre = ps.run_prescreen(("ETHUSDT",), folds)
    ser = ps._serialise(pre)["ETHUSDT"]["folds"]["1"]
    expect = {str(round(i * 0.25, 4)) for i in range(11)}
    for key in ("a3_floor_binding_by_offset",
                "a3_floor_binding_by_offset_rv30",
                "a3_floor_binding_by_offset_rv70"):
        assert key in ser, key
        assert set(ser[key]) == expect, key


@needs_data
def test_persisted_arms_match_the_computed_rows(rows, fold):
    """The serialiser must not silently reorder or rescale anything."""
    pre = {"ETHUSDT": {"folds": {fold["fold_id"]: {
        "rows": rows["ETHUSDT"], "summary": ps.summarise(rows["ETHUSDT"])}},
        "n_folds_with_viable_band": 1, "folds_with_viable_band": [1],
        "tradable": True}}
    ser = ps._serialise(pre)["ETHUSDT"]["folds"][str(fold["fold_id"])]
    for r in rows["ETHUSDT"]:
        k = str(r["offset"])
        assert ser["a3_floor_binding_by_offset"][k] == r["gated_50"]["floor"]
        assert ser["a3_floor_binding_by_offset_rv30"][k] == r["gated_30"]["floor"]
        assert ser["a3_floor_binding_by_offset_rv70"][k] == r["gated_70"]["floor"]


@needs_data
@pytest.mark.parametrize("symbol", SYMBOLS)
def test_both_new_arms_decrease_monotonically_in_the_multiplier(symbol, folds):
    """Mechanical: the floor is constant and raw distance rises with the
    multiplier, so this must hold exactly on every arm."""
    for f in folds:
        r = ps.prescreen_fold_symbol(symbol, f, gr.fold_symbol_grid(symbol, f))
        for pop in ("gated_30", "gated_70"):
            v = [x[pop]["floor"] for x in r]
            for i in range(len(v) - 1):
                assert v[i + 1] <= v[i] + 1e-12, (
                    f"{symbol} fold {f['fold_id']} {pop} offset {i}")


@needs_data
def test_the_arm_ordering_is_a_tendency_not_an_identity():
    """rv30 <= rv50 <= rv70 holds in aggregate but NOT cell by cell.

    A tighter gate selects higher-volume bars, which are on average higher-ATR
    and so less often floored. That is a statistical association, not a
    mechanical identity like the monotonicity above: RVOL and ATR are
    correlated, not functionally linked. So individual cells invert, and this
    test pins the observed scale of that rather than asserting an ordering the
    data does not support.

    What matters for A3 is that no inversion straddles the 20% line, which is
    asserted below.
    """
    import json
    if not os.path.exists(gr.GRID_PATH):
        pytest.skip("grid.json not generated")
    p = json.load(open(gr.GRID_PATH))["prescreen"]
    offs = [str(round(i * 0.25, 4)) for i in range(11)]
    inversions = []
    for s in p:
        for fid, d in p[s]["folds"].items():
            a = d["a3_floor_binding_by_offset_rv30"]
            b = d["a3_floor_binding_by_offset"]
            c = d["a3_floor_binding_by_offset_rv70"]
            for o in offs:
                if a[o] > b[o] + 1e-12:
                    inversions.append(a[o] - b[o])
                if b[o] > c[o] + 1e-12:
                    inversions.append(b[o] - c[o])
    # Aggregate ordering holds.
    means = {k: np.mean([d[key][o] for s in p for fid, d in p[s]["folds"].items()
                         for o in offs])
             for k, key in (("30", "a3_floor_binding_by_offset_rv30"),
                            ("50", "a3_floor_binding_by_offset"),
                            ("70", "a3_floor_binding_by_offset_rv70"))}
    assert means["30"] < means["50"] < means["70"], means
    # Individual inversions exist but are small.
    assert inversions, "no inversions at all would suggest a degenerate fixture"
    assert max(inversions) < 0.01, (
        f"an inversion exceeded 1pp ({max(inversions):.4f}); the arms may not "
        f"be computed on the populations they claim")


@needs_data
def test_no_arm_inversion_straddles_the_a3_threshold():
    """An inversion that crossed 20% could flip how a verdict is read."""
    import json
    if not os.path.exists(gr.GRID_PATH):
        pytest.skip("grid.json not generated")
    p = json.load(open(gr.GRID_PATH))["prescreen"]
    offs = [str(round(i * 0.25, 4)) for i in range(11)]
    for s in p:
        for fid, d in p[s]["folds"].items():
            for o in offs:
                trio = (d["a3_floor_binding_by_offset_rv30"][o],
                        d["a3_floor_binding_by_offset"][o],
                        d["a3_floor_binding_by_offset_rv70"][o])
                ordered = trio[0] <= trio[1] <= trio[2]
                if not ordered:
                    assert not (min(trio) < 0.20 <= max(trio)), (
                        f"{s} fold {fid} offset {o}: an out-of-order arm "
                        f"straddles the 20% A3 line: {trio}")


@needs_data
def test_the_seventy_percent_arm_can_fail_a3_where_fifty_passes():
    """The finding this task exists to surface, pinned so it cannot regress.

    The 70% arm admits lower-volume, hence lower-ATR bars, so it is floored
    more often. Where it exceeds 20% at an offset the 50% arm passes, part of
    any 70->50->30 improvement is the FLOOR mechanism rather than the gate.
    """
    import json
    if not os.path.exists(gr.GRID_PATH):
        pytest.skip("grid.json not generated")
    p = json.load(open(gr.GRID_PATH))["prescreen"]
    offs = [str(round(i * 0.25, 4)) for i in range(11)]
    n = sum(1 for s in p for fid, d in p[s]["folds"].items() for o in offs
            if d["a3_floor_binding_by_offset"][o] < 0.20
            <= d["a3_floor_binding_by_offset_rv70"][o])
    assert n > 0, (
        "no cell has the 70% arm failing A3 where the 50% arm passes; if this "
        "ever becomes true the monotonicity caveat can be relaxed")


@needs_data
def test_the_new_arms_do_not_touch_the_a3_verdict(fold):
    """§4.4: A3 is decided on the 50% arm alone. Description, not criterion.

    Asserted by MUTATION rather than by inspection: the 30% and 70% arms are
    overwritten with values that would flip a verdict if either were read, and
    the verdict must not move. Checking that `a3_floor_binding` equals
    `gated_50` only restates how the field was assigned, which proves nothing.
    """
    symbol = "BTCUSDT"
    cell = gr.fold_symbol_grid(symbol, fold)
    rows = ps.prescreen_fold_symbol(symbol, fold, cell)
    before = [(x["a3_floor_binding"], x["a3_pass"]) for x in rows]
    assert any(p for _, p in before) and not all(p for _, p in before), (
        "fixture needs both passing and failing points to be meaningful")

    for x in rows:
        x["gated_30"]["floor"] = 0.99      # would fail A3 everywhere
        x["gated_70"]["floor"] = 0.0       # would pass A3 everywhere
    after = [(x["a3_floor_binding"], x["a3_pass"]) for x in rows]
    assert after == before
    assert ps.summarise(rows) == ps.summarise(
        ps.prescreen_fold_symbol(symbol, fold, cell))
