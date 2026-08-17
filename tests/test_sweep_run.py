"""Tests for the sweep (step 2 of the §4.4 sequence) -- src/sweep/sweep.py.

THE POPULATION CONTRACT IS THE POINT OF THIS FILE. Five significant Point 4
defects were the same error: a quantity measured on one population and applied
to another, invisible because both had the same name. So the label guard here
is planted against its own target mutation rather than merely asserted, as are
the arm-universe, warm-up, determinism and bound checks.

Seven vacuous guards have been found in this project.
"""

import datetime as dt
import glob
import json
import os
import sys

import numpy as np
import pandas as pd
import pytest

from src.folds import schedule as sch
from src.sweep import grid as gr
from src.sweep import sweep as sw

sys.path.insert(0, os.path.join(sch.ROOT, "src", "engine"))

import contracts  # noqa: E402
import signals as sg  # noqa: E402
import simulate  # noqa: E402


# ---------------------------------------------------------------------------
# shared fixtures -- one real (fold, symbol) at one offset, computed once
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def one_cell():
    """One real (fold, symbol, offset) swept end to end. Slow but real."""
    grid_json = gr.load_grid()
    fold = sch.build_schedule()[0]
    symbol = "BTCUSDT"
    cell = grid_json["symbols"][symbol][str(fold["fold_id"])]
    offsets = sw.eligible_offsets(grid_json, symbol, fold["fold_id"])[:1]
    bars15 = sch.load_bars(symbol, sch.DATA_START, sch.IS_END)
    years = sorted(set(pd.to_datetime(bars15["ts"], unit="ms", utc=True).dt.year))
    recs = simulate.load_1m(
        sch.DERIVED, symbol,
        years=simulate.in_sample_years(set(years) | {max(years) + 1}))
    ticks = contracts.load_cache()
    records, frames, excluded = sw.sweep_fold_symbol(
        symbol, fold, cell, offsets, bars15, recs, ticks,
        contracts.load_order_specs())
    return {"symbol": symbol, "fold": fold, "cell": cell,
            "offsets": offsets, "bars15": bars15, "recs": recs,
            "ticks": ticks, "records": records,
            "trades": pd.concat(frames, ignore_index=True),
            "excluded": excluded}


# ===========================================================================
# (a) POPULATION LABELS -- and the planted mutation
# ===========================================================================

def test_every_record_carries_all_four_labels(one_cell):
    n = sw.validate_records(one_cell["records"])
    assert n == len(one_cell["records"]) > 0


def test_MUTATION_stripping_the_population_label_is_caught(one_cell):
    """THE PLANTED MUTATION. One record loses its population; the guard must fire."""
    recs = [dict(r) for r in one_cell["records"]]
    del recs[3]["population"]
    with pytest.raises(sw.PopulationLabelError, match="population"):
        sw.validate_records(recs)


@pytest.mark.parametrize("label", ["population", "period", "direction", "arm"])
def test_MUTATION_stripping_any_label_is_caught(one_cell, label):
    recs = [dict(r) for r in one_cell["records"]]
    del recs[0][label]
    with pytest.raises(sw.PopulationLabelError, match=label):
        sw.validate_records(recs)


def test_MUTATION_a_label_outside_the_closed_set_is_caught(one_cell):
    """Relabelling is as dangerous as omitting: the set is CLOSED."""
    recs = [dict(r) for r in one_cell["records"]]
    recs[0] = dict(recs[0], population="gated_60")
    with pytest.raises(sw.PopulationLabelError, match="closed set"):
        sw.validate_records(recs)


def test_validate_refuses_an_empty_record_list():
    """A guard with nothing to check would otherwise pass vacuously."""
    with pytest.raises(sw.PopulationLabelError, match="vacuous"):
        sw.validate_records([])


def test_record_constructor_rejects_an_unknown_population():
    with pytest.raises(sw.PopulationLabelError):
        sw.record(1, "BTCUSDT", 0.5, 2.7, "full", "gated_99", "train",
                  "both", {})


def test_every_population_in_the_artifact_is_from_the_closed_set(one_cell):
    seen = {r["population"] for r in one_cell["records"]}
    assert seen <= set(sw.POPULATIONS)
    # The RVOL arms and the ungated arm must all be present, or the sweep is
    # not producing what §4.3's monotonicity test needs.
    assert {"gated_30", "gated_50", "gated_70", "ungated"} <= seen


# ===========================================================================
# (b) ARM UNIVERSE IDENTITY -- asserted by TRADE ID, not by count
# ===========================================================================

def _ids(t):
    return set(zip(t["symbol"], t["signal_bar_ts"].astype("int64"),
                   t["direction"]))


def test_gated_arms_are_strict_subsets_of_ungated_by_trade_id(one_cell):
    """§4.5: the gated arms are FILTERS, so identity holds by construction."""
    t = one_cell["trades"]
    base = t[(t["arm"] == "full") & (t["period"] == "train")]
    assert len(base) > 0
    thr = sw.rvol_thresholds(one_cell["cell"])
    ung = _ids(base)
    prev = None
    for pct in (0.70, 0.50, 0.30):
        sub = _ids(base[base["rvol"] >= thr[pct]])
        assert sub <= ung, f"gated_{int(pct*100)} is not a subset of ungated"
        if prev is not None:
            assert sub <= prev, "the arms are not nested by threshold"
        prev = sub
    assert _ids(base[base["rvol"] >= thr[0.30]]) < ung


def test_minus_time_stop_has_the_IDENTICAL_universe(one_cell):
    """The checkpoint changes WHEN a trade exits, never WHETHER it exists."""
    t = one_cell["trades"]
    a = _ids(t[(t["arm"] == "full") & (t["period"] == "train")])
    b = _ids(t[(t["arm"] == "minus_time_stop") & (t["period"] == "train")])
    assert a == b, "the time-stop arm changed the trade universe"


def test_minus_ema_is_a_strict_SUPERSET_and_so_cannot_be_a_filter(one_cell):
    """This is why the arm is re-simulated rather than cut from the base table."""
    t = one_cell["trades"]
    a = _ids(t[(t["arm"] == "full") & (t["period"] == "train")])
    b = _ids(t[(t["arm"] == "minus_ema") & (t["period"] == "train")])
    assert a < b, "dropping the EMA filter did not widen the universe"


def test_minus_max_hold_is_reported_blocked_not_silently_omitted():
    """A missing arm must be a stated refusal, not an absence."""
    assert sw.ARM_SPEC["minus_max_hold"]["production"] == "BLOCKED"
    assert sw.ARM_SPEC["minus_max_hold"]["populations"] == ()
    # The blocker is real: the cap is a read-only property of donchian_period.
    import costs
    cfg = costs.CostConfig(stop_atr_mult=3.0, stop_max_pct=0.05,
                           rvol_threshold=2.0, baseline_days=20)
    assert cfg.max_hold_bars == 2 * cfg.donchian_period
    with pytest.raises(AttributeError):
        cfg.max_hold_bars = 999


# ---------------------------------------------------------------------------
# the EMA switch must not have changed engine semantics
# ---------------------------------------------------------------------------

def test_ema_switch_default_is_bit_identical_to_the_baseline_rule():
    """Adding the counterfactual switch must not move the baseline at all."""
    from conftest import make_cfg
    bars = sch.load_bars("ETHUSDT", dt.date(2023, 3, 1), dt.date(2023, 5, 31))
    cfg = make_cfg()
    a = sg.generate_signals(bars, sg.SignalParams(), "ETHUSDT", cfg)
    b = sg.generate_signals(bars, sg.SignalParams(), "ETHUSDT", cfg,
                            apply_ema_filter=True)
    assert len(a) == len(b) > 0
    assert np.array_equal(a["signal_bar_ts"].to_numpy(),
                          b["signal_bar_ts"].to_numpy())
    assert list(a["direction"]) == list(b["direction"])


def test_ema_switch_off_admits_bars_the_baseline_rejects():
    """The mutation the switch exists to produce, proven to bite."""
    from conftest import make_cfg
    bars = sch.load_bars("ETHUSDT", dt.date(2023, 3, 1), dt.date(2023, 5, 31))
    cfg = make_cfg()
    on = sg.generate_signals(bars, sg.SignalParams(), "ETHUSDT", cfg,
                             apply_rvol_gate=False, apply_ema_filter=True)
    off = sg.generate_signals(bars, sg.SignalParams(), "ETHUSDT", cfg,
                              apply_rvol_gate=False, apply_ema_filter=False)
    assert len(off) > len(on)
    key = lambda d: set(zip(d["signal_bar_ts"], d["direction"]))
    assert key(on) < key(off)


def test_signals_are_invariant_to_the_swept_parameters():
    """Justifies generating signals ONCE per period and reusing every offset."""
    from conftest import make_cfg
    bars = sch.load_bars("BTCUSDT", dt.date(2023, 3, 1), dt.date(2023, 5, 31))
    a = sg.generate_signals(bars, sg.SignalParams(), "BTCUSDT",
                            make_cfg(stop_atr_mult=2.0, stop_max_pct=0.03),
                            apply_rvol_gate=False)
    b = sg.generate_signals(bars, sg.SignalParams(), "BTCUSDT",
                            make_cfg(stop_atr_mult=6.0, stop_max_pct=0.09),
                            apply_rvol_gate=False)
    assert np.array_equal(a["signal_bar_ts"].to_numpy(),
                          b["signal_bar_ts"].to_numpy())


# ===========================================================================
# (c) THE SEAL AND THE BOUNDARY EXCLUSION ARE ACTIVE
# ===========================================================================

def test_sweep_never_loads_a_sealed_1m_partition():
    import ast
    src = open(os.path.join(sch.ROOT, "src", "sweep", "sweep.py")).read()
    for node in ast.walk(ast.parse(src)):
        if isinstance(node, ast.Call):
            for kw in node.keywords:
                if kw.arg in ("authorised", "authorised_1m"):
                    assert isinstance(kw.value, ast.Constant) and not kw.value.value
    assert "in_sample_years" in src, "the sweep must clamp the 1m year span"


def test_sweep_run_backtest_leaves_the_exclusion_on(one_cell):
    """The default is ON; the sweep must not pass exclude_holdout_crossing=False."""
    import ast
    src = open(os.path.join(sch.ROOT, "src", "sweep", "sweep.py")).read()
    for node in ast.walk(ast.parse(src)):
        if isinstance(node, ast.Call):
            for kw in node.keywords:
                if kw.arg == "exclude_holdout_crossing":
                    pytest.fail("the sweep overrides the boundary exclusion")


def test_no_swept_trade_reaches_the_holdout(one_cell):
    t = one_cell["trades"]
    assert int(t["signal_bar_ts"].max()) < simulate.HOLDOUT_START_MS
    assert int(t["exit_ts"].max()) < simulate.HOLDOUT_START_MS


# ===========================================================================
# (d) WARM-UP
# ===========================================================================

def test_no_trade_originates_before_its_period_start(one_cell):
    fold = one_cell["fold"]
    t = one_cell["trades"]
    for period in ("train", "test"):
        sub = t[t["period"] == period]
        a, b = sw.period_bounds(fold, period)
        assert len(sub) > 0
        assert int(sub["signal_bar_ts"].min()) >= sch.day_start_ms(a)
        assert int(sub["signal_bar_ts"].max()) <= sch.day_last_bar_ms(b)


def test_removing_the_warmup_buffer_changes_the_signal_count():
    """The buffer is load-bearing, so removing it must be detectable."""
    from conftest import make_cfg
    fold = sch.build_schedule()[0]
    bars = sch.load_bars("BTCUSDT", sch.DATA_START, sch.IS_END)
    cfg = make_cfg()
    full = sw.period_signals(bars, fold, "train", "BTCUSDT", cfg)
    none = sw.period_signals(bars, dict(fold, warmup_start=fold["train_start"]),
                             "train", "BTCUSDT", cfg)
    assert len(none) < len(full)


# ===========================================================================
# (e) DETERMINISM
# ===========================================================================

def test_rerunning_a_cell_reproduces_bit_identical_r_multiples(one_cell):
    """Bit-identical, not approximately equal."""
    again, frames, _ = sw.sweep_fold_symbol(
        one_cell["symbol"], one_cell["fold"], one_cell["cell"],
        one_cell["offsets"], one_cell["bars15"], one_cell["recs"],
        one_cell["ticks"], contracts.load_order_specs())
    t2 = pd.concat(frames, ignore_index=True)
    t1 = one_cell["trades"]
    assert len(t1) == len(t2)
    assert np.array_equal(t1["r_multiple"].to_numpy(),
                          t2["r_multiple"].to_numpy())
    assert json.dumps(again, sort_keys=True, default=sw._json_default) == \
        json.dumps(one_cell["records"], sort_keys=True, default=sw._json_default)


# ===========================================================================
# (f) THE APPENDIX M.1 BOUND
# ===========================================================================

def test_no_r_multiple_outside_the_engine_derived_bound(one_cell):
    sw.check_r_bounds(one_cell["trades"], "one_cell",
                      one_cell["ticks"][one_cell["symbol"]])


def test_the_bound_check_has_teeth(one_cell):
    t = one_cell["trades"].head(50).copy()
    t.loc[t.index[0], "r_multiple"] = 3.0
    with pytest.raises(AssertionError, match="ENGINE DEFECT"):
        sw.check_r_bounds(t, "planted", one_cell["ticks"][one_cell["symbol"]])
    t2 = one_cell["trades"].head(50).copy()
    t2.loc[t2.index[0], "r_multiple"] = -2.0
    with pytest.raises(AssertionError, match="ENGINE DEFECT"):
        sw.check_r_bounds(t2, "planted", one_cell["ticks"][one_cell["symbol"]])


# ===========================================================================
# Appendix J stratification, and the evidence minimums
# ===========================================================================

def test_floor_strata_are_reported_on_every_both_direction_cell(one_cell):
    both = [r for r in one_cell["records"] if r["direction"] == "both"
            and r["metrics"]["n"] > 0]
    assert both
    for r in both:
        assert "floor_strata" in r, "Appendix J stratification missing"
        for name in ("floor_bound", "not_floor_bound"):
            s = r["floor_strata"][name]
            assert "n" in s and "below_evidence_minimum" in s


def test_a_stratum_below_the_minimum_withholds_its_expectancy(one_cell):
    """The minimums do not move; a thin stratum is stated, not reported."""
    t = one_cell["trades"]
    sub = t[(t["arm"] == "full") & (t["period"] == "test")].head(40)
    out = sw.stratify_by_floor(sub, "test")
    for name in ("floor_bound", "not_floor_bound"):
        if out[name]["n"] < sw.MIN_TEST_TRADES:
            assert out[name]["below_evidence_minimum"] is True
            assert out[name]["expectancy_r"] is None


def test_evidence_minimums_are_the_pre_committed_values():
    assert sw.MIN_TRAIN_TRADES == 200
    assert sw.MIN_TEST_TRADES == 50
    assert sw.MIN_DIRECTION_TRADES == 30


def test_top_grid_point_is_never_swept():
    """§4.3's plateau rule makes offset 2.50 ineligible for selection."""
    grid_json = gr.load_grid()
    for f in sch.build_schedule():
        for s in sw.SYMBOLS:
            offs = sw.eligible_offsets(grid_json, s, f["fold_id"])
            assert offs, f"{s} fold {f['fold_id']} has no eligible offset"
            assert max(offs) < sw.TOP_OFFSET


def test_expectancy_per_bar_is_total_R_over_total_bars(one_cell):
    """The secondary metric's definition, pinned so it cannot drift."""
    t = one_cell["trades"]
    sub = t[(t["arm"] == "full") & (t["period"] == "train")].reset_index(drop=True)
    m = sw.expectancy_metrics(sub)
    want = float(sub["r_multiple"].sum() / sub["bars_held"].sum())
    assert m["expectancy_per_bar_r"] == pytest.approx(want)


# ===========================================================================
# the persisted artifact
# ===========================================================================

#: WHY THIS SKIPS RATHER THAN FAILS, AND IT USED TO FAIL.
#:
#: The original wording was "This FAILS rather than skips: a guard that skips
#: proves nothing", and the objection is right about a guard whose subject is
#: present. It is wrong about one whose subject cannot be in the repository at
#: all: `docs/design/04_2a_artifact_containment.md` section 3.5 decides that
#: `sweep_cells.jsonl` STAYS UNTRACKED, because tracking it would add a further
#: outcome-bearing file to version control and run directly against section 3.2.
#:
#:     A GUARD THAT FAILS ON A FILE THE REPOSITORY IS FORBIDDEN TO CARRY DOES
#:     NOT PROVE ANYTHING EITHER. IT MAKES A CLEAN CLONE UNABLE TO PASS.
#:
#: That is section 3.5's consequence 1, and section 7 item 4 names its repair as
#: owed: "making `tests/test_sweep_run.py` skip, or regenerating the file from
#: source." REGENERATION IS NOT AVAILABLE IN A CLEAN CLONE -- the bar layer the
#: sweep runs on is untracked too and is fetched from the venue -- so the first
#: option is the only one that reaches the stated objective.
#:
#: THE GUARD KEEPS ITS TEETH WHEREVER THE ARTIFACT EXISTS, and
#: `test_the_cells_guards_skip_ONLY_when_the_artifact_is_absent` asserts that
#: the skip is conditional on absence and on nothing else.
CELLS_ABSENT = (
    "sweep cells absent at %s. THEY ARE NOT IN THE REPOSITORY BY DESIGN: "
    "docs/design/04_2a_artifact_containment.md section 3.5 keeps this file "
    "untracked because section 3.2 bars adding an outcome-bearing file to "
    "version control. Regenerate with `python -m src.sweep.sweep`. This SKIPS "
    "rather than fails so a clean clone can pass; wherever the artifact "
    "exists the guard below runs in full.")


def _cells():
    if not os.path.exists(sw.CELLS_PATH):
        pytest.skip(CELLS_ABSENT % sw.CELLS_PATH)
    return sw.load_cells()


def test_artifact_every_record_is_labelled():
    assert sw.validate_records(_cells()) > 0


def test_artifact_covers_every_fold_symbol_and_arm():
    cells = _cells()
    grid_json = gr.load_grid()
    got = {(c["symbol"], c["fold_id"], c["offset"]) for c in cells}
    want = set()
    for f in sch.build_schedule():
        for s in sw.SYMBOLS:
            for o in sw.eligible_offsets(grid_json, s, f["fold_id"]):
                want.add((s, f["fold_id"], o))
    assert got == want, f"missing {sorted(want - got)[:10]}"
    arms = {c["arm"] for c in cells}
    assert arms == {a for a, v in sw.ARM_SPEC.items()
                    if v["production"] != "BLOCKED"}


def test_artifact_trade_tables_stay_inside_the_in_sample_window():
    """THE SAME REPAIR AS `_cells`, FOR THE SAME REASON.

    The trade tables are untracked for the same ground and are absent in a clean
    clone for the same reason, so a failure here defeats the same objective. It
    SKIPS on absence and asserts in full on presence.
    """
    paths = sorted(glob.glob(os.path.join(sw.TRADES_DIR, "*.parquet")))
    if not paths:
        pytest.skip(CELLS_ABSENT % sw.TRADES_DIR)
    for p in paths:
        ts = pd.read_parquet(p, columns=["signal_bar_ts"])["signal_bar_ts"]
        assert int(ts.max()) < simulate.HOLDOUT_START_MS


def test_the_cells_guards_skip_ONLY_when_the_artifact_is_absent(monkeypatch):
    """THE ANSWER TO "A GUARD THAT SKIPS PROVES NOTHING".

    The skip must be conditional on absence and on nothing else, or it becomes a
    permanent silence that nobody can distinguish from a passing guard. Both
    directions are asserted, and NEITHER TOUCHES THE ARTIFACT: the absent case
    points `CELLS_PATH` at a name that does not exist, and the present case
    checks only that the real path exists and that `_cells` does not skip.
    """
    absent = os.path.join(sw.OUT_DIR, "no_such_cells.jsonl")
    assert not os.path.exists(absent), "the fixture path must not exist"
    monkeypatch.setattr(sw, "CELLS_PATH", absent)
    # `Skipped` derives from BaseException, so `pytest.raises(Exception)` would
    # let it through and this test would itself skip -- which is the failure
    # mode it exists to detect.
    with pytest.raises(pytest.skip.Exception) as caught:
        _cells()
    assert "04_2a_artifact_containment" in str(caught.value)
    monkeypatch.undo()

    # THE OTHER DIRECTION: present means the guard runs, and does not skip.
    if os.path.exists(sw.CELLS_PATH):
        assert _cells(), "the artifact is present and the guard must run on it"
