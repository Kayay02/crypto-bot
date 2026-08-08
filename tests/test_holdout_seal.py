"""The 1m holdout seal and the boundary-crossing exclusion (Appendix M.2/M.3).

THE ORDER MATTERS, AND THE TESTS ENCODE IT.

Exclusion (M.3) runs at SIGNAL TIME, decided by arithmetic on the entry
timestamp, before any 1m bar is requested. The loader refusal and the
point-of-use refusal (M.2) are BACKSTOPS which must never fire in normal
operation. That ordering is what makes the seal provable: because exclusion
runs first, a refusal is unambiguous evidence of a bug rather than a routine
data condition.

A backstop never shown to fire proves nothing, so the central test here
disables the exclusion, asserts the refusal FIRES on real fold-9 data, then
restores it and asserts the refusal does NOT fire and the excluded count is
positive. Six vacuous guards have been found in this project.
"""

import datetime as dt
import os
import sys

import numpy as np
import pandas as pd
import pytest

from src.folds import schedule as sch
from src.sweep import grid as gr
from src.analysis import dispersion as dp

sys.path.insert(0, os.path.join(sch.ROOT, "src", "engine"))

import simulate  # noqa: E402

from conftest import make_cfg, make_signal, make_1m  # noqa: E402

DERIVED = sch.DERIVED


# ---------------------------------------------------------------------------
# the boundary constant is duplicated -- prove it has not drifted
# ---------------------------------------------------------------------------

def test_engine_holdout_constant_matches_the_folds_definition():
    """The engine cannot import src/folds/, so the date is duplicated.

    Duplication is a real risk and this is the guard against it: if either
    definition moves, the two disagree and this fails.
    """
    assert simulate.HOLDOUT_START_MS == sch.day_start_ms(sch.HOLDOUT_TEST_START)
    assert simulate.HOLDOUT_START_ISO == sch.HOLDOUT_TEST_START.isoformat()
    assert simulate.HOLDOUT_YEAR == sch.HOLDOUT_TEST_START.year


# ---------------------------------------------------------------------------
# step 1 -- the arithmetic, which reads no data
# ---------------------------------------------------------------------------

def test_last_1m_ts_needed_is_pure_arithmetic_on_the_entry_bar():
    cfg = make_cfg()
    entry = 1_700_000_000_000
    want = entry + (simulate.max_walk_minutes(cfg) - 1) * simulate.BAR_1M_MS
    assert simulate.last_1m_ts_needed(entry, cfg) == want
    # 40 max-hold bars -> 41 realised bars -> 617 minutes of buffer.
    assert simulate.max_walk_minutes(cfg) == (cfg.max_hold_bars + 1) * 15 + 2


def test_crosses_holdout_is_conservative_by_the_full_walk():
    """A trade entering just before the boundary crosses; long before, it does not."""
    cfg = make_cfg()
    h = simulate.HOLDOUT_START_MS
    span = (simulate.max_walk_minutes(cfg) - 1) * simulate.BAR_1M_MS
    assert simulate.crosses_holdout(h - span, cfg) is True        # exactly reaches
    assert simulate.crosses_holdout(h - span - 60_000, cfg) is False
    assert simulate.crosses_holdout(h, cfg) is True
    # ~10h17m of 2024-12-31 is excluded: conservative, and deliberately so.
    assert 10 * 3600_000 < span < 11 * 3600_000


def test_crosses_holdout_reads_no_data():
    """It must be decidable with no bars present at all, or the seal is circular."""
    cfg = make_cfg()
    assert simulate.crosses_holdout(simulate.HOLDOUT_START_MS - 1, cfg) is True


def test_in_sample_years_clamps_below_the_holdout():
    assert simulate.in_sample_years({2022, 2023, 2024, 2025}) == {2022, 2023, 2024}
    assert simulate.in_sample_years({2025, 2026}) == set()
    assert simulate.in_sample_years({2022, 2023}) == {2022, 2023}


# ---------------------------------------------------------------------------
# step 3 -- the loader backstop
# ---------------------------------------------------------------------------

def test_load_1m_refuses_a_holdout_partition_by_default():
    with pytest.raises(simulate.HoldoutSealError, match="SEALED"):
        simulate.load_1m(DERIVED, "BTCUSDT", years={2024, 2025})


def test_load_1m_refuses_years_none_because_that_includes_the_holdout():
    """The lazy call must not be the unsealed one."""
    with pytest.raises(simulate.HoldoutSealError, match="SEALED"):
        simulate.load_1m(DERIVED, "BTCUSDT")


def test_load_1m_accepts_an_in_sample_span():
    recs = simulate.load_1m(DERIVED, "BTCUSDT", years={2023, 2024})
    assert len(recs) > 0
    assert int(recs["ts"].max()) < simulate.HOLDOUT_START_MS


def test_load_1m_still_carries_no_volume_or_open():
    recs = simulate.load_1m(DERIVED, "BTCUSDT", years={2024})
    assert set(recs.dtype.names) == {"ts", "high", "low", "close"}


# ---------------------------------------------------------------------------
# the point-of-use backstop -- necessary BECAUSE the loader check is not enough
# ---------------------------------------------------------------------------

def test_require_in_sample_window_raises_on_a_crossing_entry():
    cfg = make_cfg()
    with pytest.raises(simulate.HoldoutSealError, match="SEALED"):
        simulate.require_in_sample_window(
            simulate.HOLDOUT_START_MS - 60_000, cfg, "BTCUSDT")


def test_require_in_sample_window_passes_well_inside_the_sample():
    cfg = make_cfg()
    simulate.require_in_sample_window(
        sch.day_start_ms(dt.date(2024, 6, 1)), cfg, "BTCUSDT")


def _literal_authorisations(source, label="<src>"):
    """Call sites passing a LITERAL true value to an authorisation keyword.

    Literals only. Forwarding a defaulted parameter through
    (`authorised=authorised`) is how src/folds/warmup.py propagates its own
    False default, and banning that would ban the pattern the seal is built on.
    Any actual authorisation has to write the literal somewhere, and this
    catches it there.
    """
    import ast
    out = []
    for node in ast.walk(ast.parse(source)):
        if not isinstance(node, ast.Call):
            continue
        for kw in node.keywords:
            if kw.arg in ("authorised", "authorised_1m"):
                if isinstance(kw.value, ast.Constant) and kw.value.value:
                    out.append(f"{label}:{node.lineno}")
    return out


def _project_py_files():
    for root in (os.path.join(sch.ROOT, "src"), os.path.join(sch.ROOT, "tests")):
        for dirpath, _, names in os.walk(root):
            if "__pycache__" in dirpath:
                continue
            for name in sorted(names):
                if name.endswith(".py"):
                    yield os.path.join(dirpath, name)


def test_no_source_file_passes_authorised_true():
    """AST-level, across the engine, the analysis layer and the tests."""
    hits = []
    n = 0
    for path in _project_py_files():
        n += 1
        hits += _literal_authorisations(open(path).read(), path)
    assert n > 20, f"only scanned {n} files -- the walk is not finding the tree"
    assert hits == [], f"holdout authorisation passed at {hits}"


def test_the_authorisation_scanner_has_teeth():
    """The planted mutation it exists to catch, and the pattern it must allow."""
    assert len(_literal_authorisations(
        "load_1m(d, s, years=y, authorised=True)")) == 1
    assert len(_literal_authorisations(
        "run_backtest(sig, a, b, cfg, t, authorised_1m=True)")) == 1
    assert _literal_authorisations(
        "load_bars(s, a, b, d, authorised=authorised)") == []
    assert _literal_authorisations(
        "load_1m(d, s, years=y, authorised=False)") == []


# ---------------------------------------------------------------------------
# THE MUTATION TEST -- both directions, on real fold-9 data
# ---------------------------------------------------------------------------

def _fold9_boundary_signals(symbol="BTCUSDT"):
    """Signals from the last day of fold 9's test period, and the cfg for them.

    Fold 9's test period ends 2024-12-31, so this is the one place in the
    in-sample window where the boundary can be reached.
    """
    fold = sch.build_schedule()[-1]
    assert fold["test_end"] == dt.date(2024, 12, 31)
    conf = dp.configuration(gr.load_grid(), symbol, fold["fold_id"])
    cfg = dp.cfg_for(conf)
    bars15 = sch.load_bars(symbol, sch.DATA_START, sch.IS_END)
    sig = dp.period_signals(bars15, fold, "test", symbol, cfg)
    sig = sig[sig["rvol"] >= conf["rvol_threshold"]].reset_index(drop=True)
    return fold, cfg, bars15, sig


def _synthetic_crossing_signal(symbol="BTCUSDT"):
    """A signal bar guaranteed to cross, so the mutation test cannot go vacuous.

    Real fold-9 data may or may not happen to contain a signal in the final
    hours of 2024-12-31. The mutation must be provable either way, so the
    crossing case is constructed rather than hoped for. It is a SIGNAL ROW --
    no 1m bar is fabricated and none is read.
    """
    # 2024-12-31 23:45Z: the last 15m bar of the in-sample window.
    sig_ts = simulate.HOLDOUT_START_MS - 900_000
    return pd.DataFrame([make_signal(symbol=symbol, direction="long",
                                     sig_ts=sig_ts, atr=100.0, close=90_000.0,
                                     rvol=99.0)])


def test_MUTATION_disabling_exclusion_makes_the_backstop_FIRE():
    """Direction 1: exclusion off -> the seal must raise."""
    import contracts
    cfg = make_cfg()
    sig = _synthetic_crossing_signal()
    with pytest.raises(simulate.HoldoutSealError, match="SEALED"):
        simulate.run_backtest(
            sig, {}, {"BTCUSDT": np.empty(0, dtype=[("ts", "i8")])}, cfg,
            contracts.load_cache(), mode="signal",
            exclude_holdout_crossing=False)          # <-- THE MUTATION


def test_MUTATION_restoring_exclusion_makes_the_backstop_SILENT():
    """Direction 2: exclusion on -> no raise, and the trade is counted out."""
    import contracts
    cfg = make_cfg()
    sig = _synthetic_crossing_signal()
    trades, refused, _ = simulate.run_backtest(
        sig, {}, {"BTCUSDT": np.empty(0, dtype=[("ts", "i8")])}, cfg,
        contracts.load_cache(), mode="signal",
        exclude_holdout_crossing=True)              # <-- RESTORED
    assert len(trades) == 0
    assert refused["holdout_boundary"] == 1, (
        "the excluded count is zero -- the exclusion did not run, and the "
        "silent half of this mutation test would pass vacuously")


def test_MUTATION_on_real_fold_9_data_both_directions():
    """The same pair against the real fold-9 test period, end to end.

    Uses the genuine signal table rather than a constructed row, so the two
    directions are exercised on the data the sweep will actually run over.
    """
    import contracts
    symbol = "BTCUSDT"
    fold, cfg, bars15, sig = _fold9_boundary_signals(symbol)
    assert len(sig) > 0
    ticks = contracts.load_cache()
    recs = simulate.load_1m(
        DERIVED, symbol,
        years=simulate.in_sample_years({2024, 2025}))
    specs = contracts.load_order_specs()

    # Append the constructed crossing signal so the mutation is provable
    # whether or not this fold happens to signal in the final hours.
    mutated_input = pd.concat([sig, _synthetic_crossing_signal(symbol)],
                              ignore_index=True)

    with pytest.raises(simulate.HoldoutSealError):
        simulate.run_backtest(mutated_input, {}, {symbol: recs}, cfg, ticks,
                              mode="signal", order_specs=specs,
                              exclude_holdout_crossing=False)

    trades, refused, _ = simulate.run_backtest(
        mutated_input, {}, {symbol: recs}, cfg, ticks, mode="signal",
        order_specs=specs, exclude_holdout_crossing=True)
    assert refused["holdout_boundary"] >= 1
    assert len(trades) > 0
    ts = trades["signal_bar_ts"].to_numpy()
    assert int(ts.max()) < simulate.HOLDOUT_START_MS


def test_excluded_trades_never_reach_the_1m_path():
    """Exclusion must precede the slice, not merely undo it.

    The 1m record array is EMPTY here. If the exclusion ran after the walk was
    sliced, the trade would be refused as `no_1m_coverage` instead, so the
    counter it lands in proves the ordering.
    """
    import contracts
    cfg = make_cfg()
    trades, refused, _ = simulate.run_backtest(
        _synthetic_crossing_signal(), {},
        {"BTCUSDT": np.empty(0, dtype=[("ts", "i8")])}, cfg,
        contracts.load_cache(), mode="signal")
    assert refused["holdout_boundary"] == 1
    assert refused["no_1m_coverage"] == 0


# ---------------------------------------------------------------------------
# the exclusion must not disturb anything away from the boundary
# ---------------------------------------------------------------------------

def test_exclusion_is_inert_away_from_the_boundary():
    """A mid-2024 signal is untouched by the seal in either configuration."""
    import contracts
    cfg = make_cfg()
    ticks = contracts.load_cache()
    recs = simulate.load_1m(DERIVED, "BTCUSDT", years={2024})
    sig_ts = sch.day_start_ms(dt.date(2024, 6, 1)) + 96 * 900_000 // 2
    sig = pd.DataFrame([make_signal(symbol="BTCUSDT", direction="long",
                                    sig_ts=sig_ts, atr=100.0, close=90_000.0,
                                    rvol=99.0)])
    a, ra, _ = simulate.run_backtest(sig, {}, {"BTCUSDT": recs}, cfg, ticks,
                                     mode="signal",
                                     exclude_holdout_crossing=True)
    b, rb, _ = simulate.run_backtest(sig, {}, {"BTCUSDT": recs}, cfg, ticks,
                                     mode="signal",
                                     exclude_holdout_crossing=False)
    assert ra["holdout_boundary"] == 0
    assert len(a) == len(b) == 1
    assert a["r_multiple"].iloc[0] == b["r_multiple"].iloc[0]


def test_summarize_reports_the_excluded_count():
    import contracts
    cfg = make_cfg()
    trades, refused, _ = simulate.run_backtest(
        _synthetic_crossing_signal(), {},
        {"BTCUSDT": np.empty(0, dtype=[("ts", "i8")])}, cfg,
        contracts.load_cache(), mode="signal")
    s = simulate.summarize(trades, refused)
    assert s["refused_holdout_boundary"] == 1
