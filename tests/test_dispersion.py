"""Tests for E6 -- src/analysis/dispersion.py.

TWO LAYERS, deliberately separated.

  LAYER 1 (fixtures) runs against synthetic data with answers known by
  construction. §4.5's build ordering requires the harness to be verified this
  way BEFORE it touches real data, because a harness bug found after the lift
  cannot be fixed by rerunning -- the buggy output has already been seen.

  LAYER 2 (artifact) runs against the persisted output of the real run and is
  the regression guard on it. These tests FAIL rather than skip when the
  artifact is absent: a guard that quietly skips is a vacuous guard, and five
  vacuous guards have already been found in this project.

Every mutation test here plants the specific defect its guard exists to catch.
"""

import datetime as dt
import glob
import json
import os

import numpy as np
import pandas as pd
import pytest

from src.analysis import dispersion as dp
from src.folds import schedule as sch
from src.sweep import grid as gr

ROOT = sch.ROOT


# ---------------------------------------------------------------------------
# synthetic fixtures -- answers known by construction
# ---------------------------------------------------------------------------

def make_trades(symbol, fold_id, period, n, seed, lo=-1.05, hi=1.9):
    """A synthetic trade table with r_multiple inside Appendix L's bounds."""
    rng = np.random.default_rng(seed)
    r = rng.uniform(lo, hi, size=n)
    d = np.where(rng.random(n) < 0.5, "long", "short")
    base = sch.day_start_ms(dt.date(2022, 4, 1)) + fold_id * 10_000_000
    ts = base + np.arange(n) * 900_000
    return pd.DataFrame({
        "symbol": symbol, "direction": d, "signal_bar_ts": ts,
        "entry_ts": ts + 900_000, "exit_ts": ts + 40 * 900_000,
        "r_multiple": r, "net_pnl": r * 20.0, "rvol": 3.0,
        "fold_id": fold_id, "period": period, "offset": 1.5,
    })


@pytest.fixture
def synthetic():
    """frames / confs / counters / folds for a two-symbol, two-fold world."""
    symbols = ["AAAUSDT", "BBBUSDT"]
    folds = [{"fold_id": 1, "warmup_start": dt.date(2022, 2, 15),
              "train_start": dt.date(2022, 4, 1), "train_end": dt.date(2022, 9, 30),
              "test_start": dt.date(2022, 10, 1), "test_end": dt.date(2022, 12, 31)},
             {"fold_id": 2, "warmup_start": dt.date(2022, 5, 17),
              "train_start": dt.date(2022, 7, 1), "train_end": dt.date(2022, 12, 31),
              "test_start": dt.date(2023, 1, 1), "test_end": dt.date(2023, 3, 31)}]
    frames, confs = {}, {}
    seed = 0
    for s in symbols:
        for f in folds:
            fid = f["fold_id"]
            confs[(s, fid)] = {
                "symbol": s, "fold_id": fid, "offset": 1.5, "multiplier": 3.75,
                "m_star": 2.25, "stop_max_pct": 5.5, "rvol_threshold": 2.4,
                "baseline_days": 20, "surviving_offsets": [0.5, 0.75, 1.0],
                "eligible_offsets": [0.5, 0.75, 1.0],
                "eligible_contiguous": True,
            }
            for period, n in (("train", 260), ("test", 130)):
                seed += 1
                frames[(s, fid, period)] = make_trades(s, fid, period, n, seed)
    counters = {"refused": {}, "n_ungated": {}, "exit_after_is_end": 0,
                "signals_before_train_start": 0}
    for k in frames:
        counters["refused"]["|".join(str(x) for x in k)] = {
            "open_position": 0, "cooldown": 0, "insufficient_margin": 0,
            "no_1m_coverage": 0, "min_qty": 0}
        counters["n_ungated"]["|".join(str(x) for x in k)] = 500
    return frames, confs, counters, folds


@pytest.fixture
def synthetic_report(synthetic):
    frames, confs, counters, folds = synthetic
    stats = dp.build_stats(frames, confs, counters, folds, None)
    overlap = {
        "total_flagged_bars": 425, "total_flagged_rows": 426,
        "ohlc_flagged_bars": 1, "per_symbol": {
            s: {"flagged_bars_total": 10, "flagged_bars_in_sample": 8,
                "flagged_bars_ohlc": 0, "overlap_breakout_bar": 3,
                "overlap_gated_signal_bar": 2,
                "overlap_entered_trade_signal_bar": 1, "overlap_entry_bar": 0}
            for s in sorted({k[0] for k in frames})}}
    for k in ("flagged_bars_total", "flagged_bars_in_sample",
              "overlap_breakout_bar", "overlap_gated_signal_bar",
              "overlap_entered_trade_signal_bar", "overlap_entry_bar"):
        overlap[f"all_symbols_{k}"] = sum(
            v[k] for v in overlap["per_symbol"].values())
    prov = {"git_commit": "deadbeef", "tree_state": "clean",
            "grid_commit": "cafebabe"}
    return frames, stats, overlap, prov


# ===========================================================================
# (a) THE CONFIGURATION SELECTION IS DETERMINISTIC
# ===========================================================================

def test_centre_offset_odd_count_takes_the_exact_centre():
    got, elig = dp.centre_offset([0.5, 0.75, 1.0, 1.25, 1.5])
    assert elig == [0.5, 0.75, 1.0, 1.25, 1.5]
    assert got == 1.0


def test_centre_offset_even_count_takes_the_HIGHER_central_offset():
    """Appendix K.3: the tie breaks to the wider stop, never the narrower."""
    got, elig = dp.centre_offset([0.5, 0.75, 1.0, 1.25])
    assert len(elig) == 4
    assert got == 1.0            # the higher of 0.75 and 1.00, not 0.75


def test_centre_offset_excludes_the_top_grid_point():
    """§4.3's plateau rule makes offset 2.50 ineligible, so it is not run."""
    full = [0.5, 0.75, 1.0, 1.25, 1.5, 1.75, 2.0, 2.25, 2.5]
    got, elig = dp.centre_offset(full)
    assert 2.5 not in elig
    assert len(elig) == 8
    assert got == 1.5            # higher of the two central of eight


def test_centre_offset_tie_break_would_differ_if_the_rule_were_LOWER():
    """The K.3 mutation: taking the lower central offset must change the answer.

    Without this, `test_..._HIGHER_...` would pass for an implementation that
    silently rounded the other way on some inputs.
    """
    even = [0.5, 0.75, 1.0, 1.25]
    assert dp.centre_offset(even)[0] == even[len(even) // 2]
    assert even[len(even) // 2] != even[(len(even) - 1) // 2]


def test_centre_offset_refuses_when_only_the_top_point_survives():
    with pytest.raises(ValueError, match="NOT extended"):
        dp.centre_offset([2.5])


def test_configuration_is_reproducible_across_repeated_runs():
    """Same inputs -> same offset, every time, for all 27 fold-symbols."""
    g = gr.load_grid()
    folds = sch.build_schedule()
    first = {(s, f["fold_id"]): dp.configuration(g, s, f["fold_id"])
             for s in dp.SYMBOLS for f in folds}
    for _ in range(3):
        again = {(s, f["fold_id"]): dp.configuration(g, s, f["fold_id"])
                 for s in dp.SYMBOLS for f in folds}
        for k in first:
            assert again[k]["offset"] == first[k]["offset"]
            assert again[k]["multiplier"] == first[k]["multiplier"]
            assert again[k]["stop_max_pct"] == first[k]["stop_max_pct"]
            assert again[k]["rvol_threshold"] == first[k]["rvol_threshold"]
    assert len(first) == 27


def test_configuration_multiplier_is_m_star_plus_offset():
    g = gr.load_grid()
    for f in sch.build_schedule():
        for s in dp.SYMBOLS:
            c = dp.configuration(g, s, f["fold_id"])
            assert c["multiplier"] == pytest.approx(c["m_star"] + c["offset"],
                                                    abs=1e-9)
            assert c["offset"] < dp.TOP_OFFSET
            assert c["offset"] in c["surviving_offsets"]


def test_configuration_uses_the_50pct_arm_and_baseline_20():
    g = gr.load_grid()
    for f in sch.build_schedule():
        for s in dp.SYMBOLS:
            c = dp.configuration(g, s, f["fold_id"])
            cell = g["symbols"][s][str(f["fold_id"])]
            assert c["rvol_threshold"] == cell["rvol_thresholds"]["0.5"]["threshold"]
            assert c["baseline_days"] == 20
            assert c["stop_max_pct"] == cell["stop_max_pct"]


# ===========================================================================
# (b) THE POPOVICIU BOUND -- and the checker's teeth
# ===========================================================================

def test_r_bounds_accept_values_inside_appendix_L():
    dp.check_r_bounds([-1.1, 0.0, 2.0], "clean")


def test_r_bounds_catch_a_value_above_plus_2R():
    """Planted mutation: a target exit that filled above +2R is impossible."""
    with pytest.raises(dp.BoundsViolation, match="ENGINE DEFECT"):
        dp.check_r_bounds([0.5, 2.0001, -1.0], "planted")


def test_r_bounds_catch_a_value_below_minus_1_2R():
    with pytest.raises(dp.BoundsViolation, match="ENGINE DEFECT"):
        dp.check_r_bounds([0.5, -1.2001], "planted")


def test_sigma_bound_catches_a_sigma_above_popoviciu():
    dp.check_sigma_bound(1.5499, "clean")
    with pytest.raises(dp.BoundsViolation, match="Popoviciu"):
        dp.check_sigma_bound(1.5501, "planted")


def test_build_stats_raises_on_an_out_of_bounds_trade(synthetic):
    """The bound is enforced on the real path, not only in the helper."""
    frames, confs, counters, folds = synthetic
    key = ("AAAUSDT", 1, "test")
    bad = frames[key].copy()
    bad.loc[bad.index[0], "r_multiple"] = 2.5
    frames = {**frames, key: bad}
    with pytest.raises(dp.BoundsViolation):
        dp.build_stats(frames, confs, counters, folds, None)


def test_sigma_is_ddof_1_and_matches_numpy(synthetic):
    frames, confs, counters, folds = synthetic
    stats = dp.build_stats(frames, confs, counters, folds, None)
    r = np.concatenate([t["r_multiple"].to_numpy()
                        for k, t in frames.items() if k[0] == "AAAUSDT"])
    assert stats["symbols"]["AAAUSDT"]["pooled_is"]["sigma"] == pytest.approx(
        float(r.std(ddof=1)))
    assert stats["symbols"]["AAAUSDT"]["pooled_is"]["n"] == len(r)


def test_spread_stats_carries_no_location_key():
    st = dp.spread_stats([0.1, 0.2, 0.3, 0.4])
    assert set(st) == {"n", "sigma", "min", "max", "iqr", "p10_p90_spread",
                       "se"}
    for banned in ("mean", "median", "sum", "expectancy", "total"):
        assert banned not in st


# ===========================================================================
# (c) THE HOLDOUT IS SEALED
# ===========================================================================

def test_default_loader_path_still_refuses_the_holdout():
    with pytest.raises(PermissionError, match="SEALED"):
        sch.load_bars("BTCUSDT", dt.date(2024, 12, 1), dt.date(2025, 1, 5))


def test_a_range_wholly_inside_the_holdout_is_refused():
    with pytest.raises(PermissionError, match="SEALED"):
        sch.load_bars("BTCUSDT", dt.date(2025, 6, 1), dt.date(2025, 6, 30))


def _authorising_calls(path):
    """Call sites passing `authorised=` anything other than a literal False.

    Parsed rather than grepped: a prose mention of the keyword in a docstring
    is not a call, and a guard that cannot tell the difference would either
    fire on its own documentation or be silenced into uselessness.
    """
    import ast
    tree = ast.parse(open(path).read())
    out = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        for kw in node.keywords:
            if kw.arg == "authorised":
                if not (isinstance(kw.value, ast.Constant)
                        and kw.value.value is False):
                    out.append((path, node.lineno))
    return out


def test_dispersion_never_authorises_a_holdout_read():
    assert _authorising_calls(
        os.path.join(ROOT, "src", "analysis", "dispersion.py")) == []


def test_this_test_module_never_authorises_a_holdout_read():
    assert _authorising_calls(os.path.abspath(__file__)) == []


def test_the_authorisation_scanner_has_teeth(tmp_path):
    """The planted mutation the scanner exists to catch."""
    p = tmp_path / "leak.py"
    p.write_text("load_bars('BTCUSDT', a, b, authorised=True)\n")
    assert len(_authorising_calls(str(p))) == 1
    p.write_text("load_bars('BTCUSDT', a, b, authorised=False)\n")
    assert _authorising_calls(str(p)) == []


def test_load_symbol_bars_stops_at_the_in_sample_end():
    """E6's 15m loader is bounded by IS_END; no bar of 2025 can produce a signal."""
    bars = dp.sch.load_bars("BTCUSDT", sch.DATA_START, sch.IS_END)
    assert int(bars["ts"].max()) < sch.day_start_ms(sch.HOLDOUT_TEST_START)


# ===========================================================================
# (d) THE REPORT GENERATOR EMITS NO LOCATION STATISTIC
#     -- with the mutation planted, twice, one per half of the guard
# ===========================================================================

def test_clean_report_passes_the_guard(synthetic_report):
    frames, stats, overlap, prov = synthetic_report
    text = dp.render_report(stats, overlap, prov)
    n = dp.assert_no_location_statistic(text, frames, stats)
    assert n > 0, "the guard checked nothing -- it would pass vacuously"


def test_forbidden_values_actually_covers_mean_median_and_sum(synthetic_report):
    """The guard's target set must contain what it claims to contain."""
    frames, _, _, _ = synthetic_report
    vals = dp.forbidden_values(frames)
    r = np.concatenate([t["r_multiple"].to_numpy() for t in frames.values()])
    for expected in (float(r.mean()), float(np.median(r)), float(r.sum())):
        assert any(abs(v - expected) < 1e-12 for v in vals)


_REAL_SPREAD_STATS = dp.spread_stats


def _mutated_spread_stats(r):
    """THE PLANTED MUTATION: spread_stats also returns the mean."""
    st = _REAL_SPREAD_STATS(r)
    a = np.asarray(r, float)
    a = a[np.isfinite(a)]
    st["mean_r"] = float(a.mean()) if a.size else None
    return st


def test_guard_catches_a_LABELLED_mean_column(monkeypatch, synthetic_report):
    """Mutation 1: a 'mean R' column is added. The lexical half must fire."""
    frames, _, overlap, prov = synthetic_report
    confs, counters, folds = _rebuild(frames)
    monkeypatch.setattr(dp, "spread_stats", _mutated_spread_stats)
    stats = dp.build_stats(frames, confs, counters, folds, None)
    cols = dp.SIGMA_COLUMNS + [("mean R", lambda st: dp._num(st["mean_r"], 4))]
    text = dp.render_report(stats, overlap, prov, columns=cols)
    with pytest.raises(dp.LocationStatisticError, match="TABLE ROW"):
        dp.assert_no_location_statistic(text, frames, stats)


def test_guard_catches_an_UNLABELLED_mean_column(monkeypatch, synthetic_report):
    """Mutation 2: the same mean under an innocuous header.

    This is the test that proves the NUMERIC half has teeth. Relabelling the
    column defeats any lexical scan, so if this passed only because of the
    term list the guard would be worthless against a careless rename.
    """
    frames, _, overlap, prov = synthetic_report
    confs, counters, folds = _rebuild(frames)
    monkeypatch.setattr(dp, "spread_stats", _mutated_spread_stats)
    stats = dp.build_stats(frames, confs, counters, folds, None)
    cols = dp.SIGMA_COLUMNS + [("centre (R)", lambda st: dp._num(st["mean_r"], 4))]
    text = dp.render_report(stats, overlap, prov, columns=cols)
    with pytest.raises(dp.LocationStatisticError, match="mean, median or sum"):
        dp.assert_no_location_statistic(text, frames, stats)


def test_guard_catches_a_bare_injected_number(synthetic_report):
    """No column, no label -- just the pooled mean pasted into the prose."""
    frames, stats, overlap, prov = synthetic_report
    text = dp.render_report(stats, overlap, prov)
    r = np.concatenate([t["r_multiple"].to_numpy() for t in frames.values()])
    text += f"\n\nIncidentally, the figure is {float(r.mean()):.4f}.\n"
    with pytest.raises(dp.LocationStatisticError, match="mean, median or sum"):
        dp.assert_no_location_statistic(text, frames, stats)


def test_schema_guard_catches_a_new_key_in_the_stats_tree(monkeypatch,
                                                         synthetic_report):
    """The structural half: a mean cannot even enter `stats` unnoticed."""
    frames, _, _, _ = synthetic_report
    confs, counters, folds = _rebuild(frames)
    monkeypatch.setattr(dp, "spread_stats", _mutated_spread_stats)
    stats = dp.build_stats(frames, confs, counters, folds, None)
    with pytest.raises(dp.LocationStatisticError, match="mean_r"):
        dp.assert_stats_schema(stats)


def test_schema_guard_passes_on_the_clean_tree(synthetic_report):
    _, stats, _, _ = synthetic_report
    assert dp.assert_stats_schema(stats) is True


def test_guard_does_not_fire_on_a_permitted_extreme(synthetic_report):
    """A median equal to the min is common; printing the min is permitted.

    Without the permitted-value exclusion the guard would fire on a clean
    report whenever a majority of trades exit at the stop -- which is the
    normal shape of this population, not an anomaly.
    """
    frames, _, overlap, prov = synthetic_report
    key = list(frames)[0]
    t = frames[key].copy()
    t["r_multiple"] = [-1.05] * (len(t) - 1) + [1.5]     # median == min
    frames = {**frames, key: t}
    confs, counters, folds = _rebuild(frames)
    stats = dp.build_stats(frames, confs, counters, folds, None)
    text = dp.render_report(stats, overlap, prov)
    dp.assert_no_location_statistic(text, frames, stats)


def _rebuild(frames):
    """confs / counters / folds matching an arbitrary synthetic `frames`."""
    confs, counters = {}, {"refused": {}, "n_ungated": {},
                           "exit_after_is_end": 0,
                           "signals_before_train_start": 0}
    fids = sorted({k[1] for k in frames})
    for s, fid, _ in frames:
        confs[(s, fid)] = {
            "symbol": s, "fold_id": fid, "offset": 1.5, "multiplier": 3.75,
            "m_star": 2.25, "stop_max_pct": 5.5, "rvol_threshold": 2.4,
            "baseline_days": 20, "surviving_offsets": [0.5, 0.75, 1.0],
            "eligible_offsets": [0.5, 0.75, 1.0], "eligible_contiguous": True}
    folds = [{"fold_id": f} for f in fids]
    return confs, counters, folds


# ===========================================================================
# the trigger and the power table, on known inputs
# ===========================================================================

def test_trigger_fires_exactly_at_the_pre_committed_threshold(synthetic):
    """SE = sigma / sqrt(n) > 0.20R, and nothing else, decides it."""
    frames, confs, counters, folds = synthetic
    stats = dp.build_stats(frames, confs, counters, folds, None)
    for s, v in stats["symbols"].items():
        sig = v["pooled_is"]["sigma"]
        for fid in stats["folds"]:
            c = v["by_fold"][fid]
            assert c["trigger_se"] == pytest.approx(sig / np.sqrt(c["test"]["n"]))
            assert c["trigger_fires"] == (c["trigger_se"] > 0.20)


def test_trigger_is_reported_never_executed(synthetic):
    """§4.5: E6 reports the trigger; the fold change is reviewed before acting."""
    frames, confs, counters, folds = synthetic
    stats = dp.build_stats(frames, confs, counters, folds, None)
    assert "REPORT ONLY" in stats["trigger"]["action"]
    assert sch.TEST_MONTHS == 3 and sch.STEP_MONTHS == 3
    assert sch.EXPECTED_FOLDS == 9
    assert len(sch.build_schedule()) == 9


def test_power_table_rows_are_sigma_over_sqrt_n(synthetic):
    frames, confs, counters, folds = synthetic
    stats = dp.build_stats(frames, confs, counters, folds, None)
    p = stats["power"]
    assert p["threshold_r"] == 0.05
    for name, row in p["rows"].items():
        for key in ("at_min_is_200", "at_min_test_50", "at_pooled_is"):
            cell = row[key]
            assert cell["se"] == pytest.approx(row["sigma"] / np.sqrt(cell["n"]))
    assert p["rows"]["AAAUSDT"]["at_min_test_50"]["n"] == 50
    assert p["rows"]["AAAUSDT"]["at_min_is_200"]["n"] == 200


def test_evidence_minimums_are_the_pre_committed_values():
    """These do NOT move. A test so a future edit has to be deliberate."""
    assert dp.MIN_TRAIN_TRADES == 200
    assert dp.MIN_TEST_TRADES == 50
    assert dp.MIN_DIRECTION_TRADES == 30
    assert dp.E6_SE_TRIGGER_R == 0.20
    assert dp.MARGINAL_CONTRIBUTION_R == 0.05
    assert dp.POPOVICIU_SIGMA_MAX == 1.55


def test_shortfalls_flag_every_cell_below_a_minimum(synthetic):
    frames, confs, counters, folds = synthetic
    key = ("AAAUSDT", 1, "test")
    frames = {**frames, key: frames[key].head(20)}
    stats = dp.build_stats(frames, confs, counters, folds, None)
    hit = [x for x in stats["shortfalls"]
           if x["symbol"] == "AAAUSDT" and x["fold_id"] == 1
           and x["period"] == "test" and x["direction"] == "both"]
    assert hit and hit[0]["n"] == 20 and hit[0]["minimum"] == 50


# ===========================================================================
# (e) WARM-UP -- no trade originates before its period start
# ===========================================================================

def test_origin_check_raises_on_a_trade_predating_its_period(synthetic):
    """The §4.2 guard, planted: a signal bar one day before train_start."""
    frames, _, _, folds = synthetic
    fold = folds[0]
    lo = sch.day_start_ms(fold["train_start"])
    holdout = sch.day_start_ms(sch.HOLDOUT_TEST_START)
    t = frames[("AAAUSDT", 1, "train")].copy()

    dp.check_period_origin(t, lo, holdout, "clean")          # passes as-is

    t.loc[t.index[0], "signal_bar_ts"] = lo - 86_400_000
    with pytest.raises(AssertionError, match="warm-up buffer is not doing"):
        dp.check_period_origin(t, lo, holdout, "planted")


def test_origin_check_raises_on_a_signal_bar_inside_the_holdout(synthetic):
    """The second firewall, planted: a signal bar dated 2025-06-01."""
    frames, _, _, folds = synthetic
    lo = sch.day_start_ms(folds[0]["train_start"])
    holdout = sch.day_start_ms(sch.HOLDOUT_TEST_START)
    t = frames[("AAAUSDT", 1, "train")].copy()
    t.loc[t.index[0], "signal_bar_ts"] = sch.day_start_ms(dt.date(2025, 6, 1))
    with pytest.raises(AssertionError, match="SEALED holdout"):
        dp.check_period_origin(t, lo, holdout, "planted")


def test_origin_check_counts_boundary_crossing_exits(synthetic):
    """A trade that ORIGINATES in-sample may resolve past 2024-12-31.

    Counted and reported rather than refused: those minutes resolve an
    in-sample trade, they never originate one.
    """
    frames, _, _, folds = synthetic
    lo = sch.day_start_ms(folds[0]["train_start"])
    holdout = sch.day_start_ms(sch.HOLDOUT_TEST_START)
    t = frames[("AAAUSDT", 1, "train")].copy()
    t.loc[t.index[:3], "exit_ts"] = holdout + 60_000
    assert dp.check_period_origin(t, lo, holdout, "boundary") == 3


def test_period_signals_never_reach_before_the_period_start():
    """Real data, one fold-symbol, no simulation: signal bars only.

    Bar-level and count-level, so this reads no trade outcome.
    """
    g = gr.load_grid()
    fold = sch.build_schedule()[0]
    conf = dp.configuration(g, "BTCUSDT", fold["fold_id"])
    bars = sch.load_bars("BTCUSDT", sch.DATA_START, sch.IS_END)
    cfg = dp.cfg_for(conf)
    for period, a, b in (("train", fold["train_start"], fold["train_end"]),
                         ("test", fold["test_start"], fold["test_end"])):
        sig = dp.period_signals(bars, fold, period, "BTCUSDT", cfg)
        assert len(sig) > 0
        assert int(sig["signal_bar_ts"].min()) >= sch.day_start_ms(a)
        assert int(sig["signal_bar_ts"].max()) <= sch.day_last_bar_ms(b)


def test_period_signals_are_computed_from_the_warmup_buffer():
    """Indicators must come from warmup_start, not from the period start.

    The mutation this catches: computing indicators from `train_start` instead
    of `warmup_start`. That would leave the 20-day slot baseline NaN for the
    first weeks of the fold and suppress signals, so the two runs differ in
    COUNT -- which is what is asserted, no outcome involved.
    """
    g = gr.load_grid()
    fold = sch.build_schedule()[0]
    conf = dp.configuration(g, "BTCUSDT", fold["fold_id"])
    cfg = dp.cfg_for(conf)
    bars = sch.load_bars("BTCUSDT", sch.DATA_START, sch.IS_END)

    buffered = dp.period_signals(bars, fold, "train", "BTCUSDT", cfg)

    no_buffer = dict(fold, warmup_start=fold["train_start"])
    unbuffered = dp.period_signals(bars, no_buffer, "train", "BTCUSDT", cfg)

    assert len(unbuffered) < len(buffered), (
        "removing the warm-up buffer changed nothing -- the buffer is not "
        "doing its job, or this check is vacuous")


# ===========================================================================
# LAYER 2 -- the persisted output of the real run
# ===========================================================================

def _artifact():
    if not os.path.exists(dp.ARTIFACT_PATH):
        pytest.fail(
            f"E6 artifact missing at {dp.ARTIFACT_PATH}; generate it with "
            f"`python -m src.analysis.dispersion`. This test FAILS rather "
            f"than skips: a guard that skips proves nothing.")
    return json.load(open(dp.ARTIFACT_PATH))


def _trade_files():
    paths = sorted(glob.glob(os.path.join(dp.TRADES_DIR, "*.parquet")))
    if not paths:
        pytest.fail(f"no trade tables under {dp.TRADES_DIR}; run E6 first.")
    return paths


def test_artifact_every_r_multiple_is_inside_appendix_L():
    """Recomputed from the trade tables, not read back from the summary."""
    worst_lo, worst_hi, n = 0.0, 0.0, 0
    for p in _trade_files():
        r = pd.read_parquet(p, columns=["r_multiple"])["r_multiple"].to_numpy()
        n += len(r)
        if len(r):
            worst_lo = min(worst_lo, float(r.min()))
            worst_hi = max(worst_hi, float(r.max()))
        dp.check_r_bounds(r, os.path.basename(p))
    assert n > 0
    assert dp.R_LOWER_BOUND <= worst_lo and worst_hi <= dp.R_UPPER_BOUND


def test_artifact_every_sigma_is_below_the_popoviciu_bound():
    a = _artifact()
    seen = 0
    for s, v in a["stats"]["symbols"].items():
        for st in [v["pooled_is"], v["pooled_train"], v["pooled_test"]]:
            if st["sigma"] is not None:
                dp.check_sigma_bound(st["sigma"], s)
                seen += 1
        for d in ("long", "short"):
            if v["by_direction"][d]["sigma"] is not None:
                dp.check_sigma_bound(v["by_direction"][d]["sigma"], f"{s} {d}")
                seen += 1
        for fid, c in v["by_fold"].items():
            for period in ("train", "test"):
                if c[period]["sigma"] is not None:
                    dp.check_sigma_bound(c[period]["sigma"], f"{s} {fid}")
                    seen += 1
    assert seen >= 3 * (3 + 2 + 18), "far fewer sigmas than the design produces"


def test_artifact_no_trade_originates_before_its_period_start():
    """§4.2's warm-up requirement, checked on the real trades."""
    folds = {f["fold_id"]: f for f in sch.build_schedule()}
    checked = 0
    for p in _trade_files():
        base = os.path.basename(p).replace(".parquet", "")
        symbol, fpart, period = base.split("_")
        fold = folds[int(fpart[1:])]
        a = fold["train_start"] if period == "train" else fold["test_start"]
        b = fold["train_end"] if period == "train" else fold["test_end"]
        ts = pd.read_parquet(p, columns=["signal_bar_ts"])["signal_bar_ts"]
        assert int(ts.min()) >= sch.day_start_ms(a), f"{base} predates {a}"
        assert int(ts.max()) <= sch.day_last_bar_ms(b), f"{base} runs past {b}"
        checked += 1
    assert checked == 54, f"expected 9 folds x 3 symbols x 2 periods, got {checked}"


def test_artifact_no_signal_bar_lies_in_the_holdout():
    holdout = sch.day_start_ms(sch.HOLDOUT_TEST_START)
    for p in _trade_files():
        ts = pd.read_parquet(p, columns=["signal_bar_ts"])["signal_bar_ts"]
        assert int(ts.max()) < holdout


def test_artifact_records_a_clean_commit():
    a = _artifact()
    assert not a["provenance"]["git_commit"].endswith("-dirty")
    assert not a["provenance"]["grid_commit"].endswith("-dirty")


def test_artifact_schema_carries_no_location_key():
    a = _artifact()
    dp.assert_stats_schema(a["stats"])


def test_written_report_carries_no_location_statistic():
    """The report on disk, re-checked against the trade tables on disk."""
    if not os.path.exists(dp.REPORT_PATH):
        pytest.fail(f"{dp.REPORT_PATH} missing; run E6 first.")
    text = open(dp.REPORT_PATH).read()
    frames = {}
    for p in _trade_files():
        base = os.path.basename(p).replace(".parquet", "")
        symbol, fpart, period = base.split("_")
        frames[(symbol, int(fpart[1:]), period)] = pd.read_parquet(
            p, columns=["symbol", "direction", "r_multiple", "net_pnl"])
    a = _artifact()
    n = dp.assert_no_location_statistic(text, frames, a["stats"])
    assert n > 0


def test_artifact_configuration_matches_the_frozen_rule():
    """The persisted configuration must be the one the rule produces today."""
    a = _artifact()
    g = gr.load_grid()
    for f in sch.build_schedule():
        for s in dp.SYMBOLS:
            c = dp.configuration(g, s, f["fold_id"])
            rec = a["stats"]["config"][f"{s}|{f['fold_id']}"]
            assert rec["offset"] == c["offset"]
            assert rec["multiplier"] == pytest.approx(c["multiplier"])
