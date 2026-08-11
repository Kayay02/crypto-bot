"""Guards for the wick-and-reject sweep population and the stop-geometry check.

THE DECISION-CRITICAL QUANTITY IS A SINGLE FRACTION -- the share of signals whose
sweep extreme lies beyond a 2.25 x ATR stop. Every distributional figure in the
report can be correct while that fraction is the complement of itself, because
inverting the comparison inside `fraction_inside` changes no percentile, no
count, and no ATR table. It is invisible to every test here except the one that
targets it, which is why that test exists and why the report says so.

The trigger's two conditions pull in opposite directions -- the extreme must be
OUTSIDE the channel and the close must be INSIDE it -- so the negative control
(a bar that breaks and closes outside) is not a formality: dropping the second
condition silently converts the population from wick-and-reject into plain
channel-break, roughly doubling it while leaving every column plausible.
"""

import ast
import datetime as dt
import os

import numpy as np
import pandas as pd
import pytest

from src.analysis import sweep_population as sp
from src.folds import schedule as sch
from src.timeframe import resample as rs


HOUR_MS = 3_600_000
T0 = 1_640_995_200_000  # 2022-01-01T00:00:00Z


def _frame(high, low, close, t0=T0):
    high = np.asarray(high, dtype=float)
    return pd.DataFrame({
        "ts": t0 + np.arange(len(high)) * HOUR_MS,
        "high": high,
        "low": np.asarray(low, dtype=float),
        "close": np.asarray(close, dtype=float),
    })


def _flat(n, high=101.0, low=99.0, close=100.0):
    """`n` bars with a true range of exactly 2.0, so ATR settles at exactly 2.0.

    H-L = 2, |H - Cprev| = 1, |L - Cprev| = 1, so the bar range dominates every
    true range and Wilder's ATR is 2.0 from the seed onward -- no convergence
    argument needed, the value is exact.
    """
    return [high] * n, [low] * n, [close] * n


# ---------------------------------------------------------------------------
# 1. The Donchian exclusion convention.
# ---------------------------------------------------------------------------

def test_donchian_window_excludes_the_current_bar():
    """PLANTED-MUTATION GUARD: the current bar admitted to its own lookback.

    THE MUTATION. Drop or shorten the `.shift(1)` in `donchian_prior`, so
    `lower[T] = min(low[T-9..T])` instead of `min(low[T-10..T-1])`.

    WHY IT WOULD OTHERWISE PASS UNNOTICED, AND WHY IT IS WORSE HERE THAN FOR A
    CLOSE-BASED BREAKOUT. The first condition of this trigger is
    `low[T] < lower[T]`. If the bar's own low is inside the window that produced
    the minimum, then `lower[T] <= low[T]` always and the condition becomes
    STRICTLY UNSATISFIABLE -- the population is empty, not merely distorted.
    Shifted the other way it becomes trivial. Neither raises.

    Asserted three ways: the window contents, the first defined index, and the
    behavioural consequence.
    """
    rng = np.random.default_rng(4)
    high = 100.0 + rng.random(200) * 10.0
    low = high - 1.0 - rng.random(200)
    p = sp.DONCHIAN_PERIOD
    m = sp.sweep_masks(high, low, high - 0.5, p)
    upper, lower = m["donchian_upper"], m["donchian_lower"]

    assert np.isnan(upper[:p]).all() and np.isnan(lower[:p]).all()
    assert np.isfinite(upper[p]) and np.isfinite(lower[p])

    differs = 0
    for i in range(p, len(high)):
        assert lower[i] == pytest.approx(low[i - p:i].min(), rel=1e-15)
        assert upper[i] == pytest.approx(high[i - p:i].max(), rel=1e-15)
        if lower[i] != pytest.approx(low[i - p + 1:i + 1].min(), rel=1e-15):
            differs += 1
    assert differs > 0, (
        "the series must contain bars where including the current bar CHANGES "
        "the window minimum, or this test cannot detect the off-by-one")


def test_including_the_current_bar_would_empty_the_population():
    """The consequence, stated as a property rather than left as an argument.

    On any series, a bar's own low is never below the minimum of a window that
    contains it. So under the off-by-one there is no long sweep anywhere,
    which is exactly the shape of a correct-looking empty result.
    """
    rng = np.random.default_rng(9)
    high = 100.0 + rng.random(300) * 5.0
    low = high - rng.random(300) * 3.0
    p = sp.DONCHIAN_PERIOD
    inclusive_low = pd.Series(low).rolling(p).min().to_numpy()   # NO shift
    assert not np.any(low < inclusive_low), (
        "a bar cannot break a channel it is itself part of")
    # And the correct convention does find breaks on the same series.
    assert sp.sweep_masks(high, low, (high + low) / 2.0, p)["break_long"].sum() > 0


# ---------------------------------------------------------------------------
# 2 and 3. Trigger correctness and the NEGATIVE CONTROL.
# ---------------------------------------------------------------------------

def _one_sweep_bar(low_v, close_v, high_v=101.0, n=200):
    """`n` flat bars (prior-10 low = 99.0) then one hand-specified bar."""
    h, l, c = _flat(n)
    return _frame(h + [high_v], l + [low_v], c + [close_v])


def test_break_and_close_back_inside_is_a_long_sweep():
    """low 95 < prior-10 low 99, close 100.5 > 99 -> detected."""
    f = sp.analysis_frame(_one_sweep_bar(95.0, 100.5))
    row = f.iloc[-1]
    assert row["donchian_lower"] == pytest.approx(99.0)
    assert bool(row["break_long"]), "the channel WAS broken intrabar"
    assert bool(row["sweep_long"]), "and the close returned inside it"
    assert not bool(row["sweep_short"])
    assert int(f["sweep_long"].sum()) == 1, "exactly one, not a run"


def test_negative_control_a_close_outside_the_channel_is_not_a_sweep():
    """NEGATIVE CONTROL. Break the channel and close BELOW it: not a sweep.

    Dropping the second condition converts the population from wick-and-reject
    into plain channel-break and roughly doubles it, with every column still
    looking reasonable. Asserted explicitly rather than implied.
    """
    f = sp.analysis_frame(_one_sweep_bar(95.0, 96.0))
    row = f.iloc[-1]
    assert bool(row["break_long"]), "the break itself must still be counted"
    assert not bool(row["sweep_long"]), (
        "a close OUTSIDE the channel is a breakout, not a rejection")
    assert int(f["sweep_long"].sum()) == 0
    assert int(f["break_long"].sum()) == 1


def test_a_bar_that_never_leaves_the_channel_is_neither():
    f = sp.analysis_frame(_one_sweep_bar(99.5, 100.2))
    row = f.iloc[-1]
    assert not bool(row["break_long"]) and not bool(row["sweep_long"])


def test_strictness_ties_are_excluded_on_both_conditions():
    """< and > throughout: touching the level is not breaking it.

    A low exactly ON the prior minimum has not broken the channel, and a close
    landing exactly ON the level has not returned inside it.
    """
    touched = sp.analysis_frame(_one_sweep_bar(99.0, 100.5)).iloc[-1]
    assert not bool(touched["break_long"]), "low == lower is not a break"
    assert not bool(touched["sweep_long"])

    closed_on = sp.analysis_frame(_one_sweep_bar(95.0, 99.0)).iloc[-1]
    assert bool(closed_on["break_long"])
    assert not bool(closed_on["sweep_long"]), (
        "close == lower has not returned INSIDE the channel")


def test_tie_counts_can_actually_count():
    """The tie reporter must be able to find a tie, or its zeros prove nothing."""
    h, l, c = _flat(30)
    bars = _frame(h + [101.0], l + [99.0], c + [100.5])
    ties = sp.tie_counts(bars["high"].to_numpy(float),
                         bars["low"].to_numpy(float),
                         bars["close"].to_numpy(float), sp.DONCHIAN_PERIOD)
    assert ties["low_equals_lower"] > 0
    assert ties["high_equals_upper"] > 0


# ---------------------------------------------------------------------------
# 4. excursion_atr arithmetic, hand-computed.
# ---------------------------------------------------------------------------

def test_excursion_atr_is_hand_computable():
    """Every quantity below is exact, not approximate.

    200 flat bars: every true range is 2.0, so ATR is exactly 2.0 at bar 199.

    The sweep bar: high 101, low 95, close 100.5, previous close 100.
        TR   = max(101-95, |101-100|, |95-100|) = max(6, 1, 5) = 6
        ATR  = (2.0 x 13 + 6) / 14 = 32/14 = 2.285714...
        excursion     = close - low = 100.5 - 95 = 5.5
        excursion_atr = 5.5 / (32/14) = 77/32 = 2.40625   EXACTLY
        range_atr     = 6 / (32/14) = 84/32 = 2.625       EXACTLY

    2.40625 is deliberately ABOVE 2.25, so this bar also exercises the geometry
    check's failing branch.
    """
    f = sp.analysis_frame(_one_sweep_bar(95.0, 100.5))
    row = f.iloc[-1]
    assert row["atr"] == pytest.approx(32.0 / 14.0, rel=1e-15)
    assert row["excursion_atr_long"] == pytest.approx(77.0 / 32.0, rel=1e-15)
    assert row["excursion_atr_long"] == pytest.approx(2.40625, rel=1e-15)
    assert row["range_atr"] == pytest.approx(2.625, rel=1e-15)
    assert row["stop_pct"] == pytest.approx(
        100.0 * 2.25 * (32.0 / 14.0) / 100.5, rel=1e-15)

    exc = sp.excursion_of(f, sp.LONG)
    assert len(exc) == 1 and exc[0] == pytest.approx(2.40625, rel=1e-15)
    assert sp.fraction_inside(exc, 2.25) == pytest.approx(1.0)
    assert sp.fraction_inside(exc, 2.5) == pytest.approx(0.0)


def test_excursion_is_never_negative_on_real_bars():
    """low <= close <= high, so both excursions are non-negative by geometry."""
    bars, _ = rs.build("BTCUSDT", sp.TIMEFRAME)
    f = sp.analysis_frame(bars)
    assert (f["excursion_atr_long"] >= 0).all()
    assert (f["excursion_atr_short"] >= 0).all()
    assert (f["range_atr"] >= f["excursion_atr_long"] - 1e-12).all()
    assert (f["range_atr"] >= f["excursion_atr_short"] - 1e-12).all()


def test_excursion_of_rejects_an_unknown_direction():
    f = sp.analysis_frame(_one_sweep_bar(95.0, 100.5))
    with pytest.raises(ValueError):
        sp.excursion_of(f, "sideways")


# ---------------------------------------------------------------------------
# 5. Direction symmetry.
# ---------------------------------------------------------------------------

def test_short_logic_is_the_exact_mirror_of_long():
    """Reflect the price axis; long sweeps must become short sweeps exactly.

    Under p -> K - p the high and low swap roles, so
        low' < min(low')  <=>  high > max(high)      and
        close' > min(low') <=> close < max(high),
    which is the short trigger. Counts AND the excursion values must agree
    element for element, not merely in aggregate -- an aggregate match would
    survive a mirrored-but-misaligned implementation.
    """
    rng = np.random.default_rng(21)
    close = 100.0 * np.exp(np.cumsum(rng.normal(0.0, 0.006, 2000)))
    span = np.abs(rng.normal(0.0, 0.004, 2000)) * close
    high, low = close + span, close - span * 0.8

    K = 400.0
    original = _frame(high, low, close)
    mirrored = _frame(K - low, K - high, K - close)

    a = sp.analysis_frame(original)
    b = sp.analysis_frame(mirrored)

    assert int(a["sweep_long"].sum()) == int(b["sweep_short"].sum())
    assert int(a["sweep_short"].sum()) == int(b["sweep_long"].sum())
    assert int(a["break_long"].sum()) == int(b["break_short"].sum())
    assert int(a["sweep_long"].sum()) > 20, "the series must contain sweeps"

    # rtol 1e-9, not 1e-12: `K - p` is not an exact float operation, so the
    # reflected series carries ~1e-12 of representation noise that has nothing
    # to do with the logic. A misaligned mirror would differ by whole ATR
    # units, not by the twelfth decimal.
    np.testing.assert_allclose(sp.excursion_of(a, sp.LONG),
                               sp.excursion_of(b, sp.SHORT), rtol=1e-9)
    np.testing.assert_allclose(sp.excursion_of(a, sp.SHORT),
                               sp.excursion_of(b, sp.LONG), rtol=1e-9)
    np.testing.assert_allclose(a["atr"].to_numpy(), b["atr"].to_numpy(),
                               rtol=1e-9)


# ---------------------------------------------------------------------------
# 6. PLANTED MUTATION -- the holdout seal.
# ---------------------------------------------------------------------------

def test_the_window_is_inherited_and_cannot_reach_the_holdout():
    """PLANTED MUTATION GUARD: the date filter widened to admit 2025.

    THE MUTATION. In `src/timeframe/resample.py`, widen either half of the
    filter -- `WINDOW_END` past 2024-12-31 or `ALLOWED_YEARS` to include 2025.

    WHY IT WOULD OTHERWISE PASS UNNOTICED. The 1m layer physically holds
    year=2025 and year=2026; the seal is not maintained by absence. A widened
    filter raises nothing, and every figure here would simply become
    better-sampled while the holdout was spent without anyone deciding to spend
    it. This module defines NO window constant of its own -- it inherits
    `resample`'s -- so this asserts the inherited one.
    """
    assert rs.WINDOW_START == dt.date(2022, 1, 1)
    assert rs.WINDOW_END == dt.date(2024, 12, 31)
    assert rs.WINDOW_END < sch.HOLDOUT_TEST_START
    assert rs.WINDOW_END + dt.timedelta(days=1) == sch.HOLDOUT_TEST_START
    assert rs.ALLOWED_YEARS == (2022, 2023, 2024)
    assert max(rs.ALLOWED_YEARS) < sch.HOLDOUT_TEST_START.year

    assigned = set()
    for node in ast.walk(_module_ast()):
        if isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name):
                    assigned.add(t.id)
    assert not {"WINDOW_START", "WINDOW_END", "ALLOWED_YEARS"} & assigned
    assert "2025" not in open(sp.__file__).read()


def test_analysis_frame_refuses_a_holdout_bar():
    """The runtime guard must be able to REFUSE, or it proves nothing."""
    sealed = rs.holdout_start_ms()
    h, l, c = _flat(200)
    bad = _frame(h, l, c, t0=sealed - 195 * HOUR_MS)
    assert int(bad["ts"].max()) >= sealed
    with pytest.raises(rs.HoldoutBreach, match="sealed holdout boundary"):
        sp.analysis_frame(bad)


def test_no_measured_bar_reaches_the_holdout():
    """End to end on the real data."""
    sealed = rs.holdout_start_ms()
    for sym in rs.SYMBOLS:
        bars, _ = rs.build(sym, sp.TIMEFRAME)
        f = sp.analysis_frame(bars)
        assert len(f) == 26_190
        assert int(f["ts"].max()) < sealed
        assert int((f["ts"] >= sealed).sum()) == 0
        last = dt.datetime.fromtimestamp(int(f["ts"].max()) / 1000,
                                         dt.timezone.utc)
        assert last.year == 2024


def test_fold_windows_are_in_sample_only_and_fully_warmed():
    """Nine folds, eighteen periods, none touching the seal.

    Also asserts the property the whole per-fold table rests on: the 114-bar
    warm-up ends BEFORE fold 1's train_start, so no fold is counted on a
    partially-formed indicator.
    """
    w = sp.fold_windows()
    assert len(w) == 18, "nine folds x (train, test)"
    assert {fid for fid, _, _, _ in w} == set(range(1, 10))
    sealed = rs.holdout_start_ms()
    for fid, period, lo, hi in w:
        assert lo < hi
        assert hi < sealed, (fid, period)

    bars, _ = rs.build("BTCUSDT", sp.TIMEFRAME)
    first_measured = int(sp.analysis_frame(bars)["ts"].min())
    earliest = min(lo for _, _, lo, _ in w)
    assert first_measured < earliest, (
        "the warm-up discard must end before the first fold begins")
    # The holdout entry exists in the artifact and must NOT have been walked.
    payload = sch.load_schedule()
    assert payload["holdout"]["test_start"] == "2025-01-01"
    assert all(fid != "holdout" for fid, _, _, _ in w)


# ---------------------------------------------------------------------------
# 7. PLANTED MUTATION -- the geometry comparison inverted.
# ---------------------------------------------------------------------------

def test_geometry_comparison_is_not_inverted():
    """PLANTED MUTATION GUARD: `x > mult` -> `x < mult` in `fraction_inside`.

    THE MUTATION. In `sweep_population.fraction_inside`, flip the comparison.

    WHY IT IS INVISIBLE TO EVERYTHING ELSE. It changes NO distributional figure.
    Every percentile of `excursion_atr`, every count, every rejection rate,
    every ATR table and every fold row stays byte-identical. The mutated
    function still returns a number in [0, 1] that still moves with `mult` in a
    plausible-looking way. The only thing that changes is THE ANSWER TO THE
    QUESTION THIS STEP EXISTS TO ANSWER -- 2.3% of signals becoming 97.7% --
    and with it the verdict on whether the frozen stop contradicts the trigger.
    No other test in this file can catch it, which is why the asymmetric
    fixture, the monotonicity property and the quantile cross-check are all
    asserted here rather than left to inference.

    `excursion_atr > mult` is the FAILURE direction: the extreme is FURTHER from
    the close than the stop is, so the stop sits INSIDE the extreme.
    """
    x = np.array([0.5, 1.0, 2.0, 3.0, 4.0])
    # Asymmetric about 2.25, so the two readings cannot coincide.
    assert sp.fraction_inside(x, 2.25) == pytest.approx(0.4)
    assert sp.fraction_inside(x, 2.25) != pytest.approx(0.6)
    assert sp.fraction_inside(x, 0.0) == pytest.approx(1.0)
    assert sp.fraction_inside(x, 10.0) == pytest.approx(0.0)

    # The property: a WIDER stop can only leave FEWER extremes outside it.
    fr = [sp.fraction_inside(x, m) for m in (0.0, 1.5, 2.25, 3.5, 10.0)]
    assert fr == sorted(fr, reverse=True), (
        "fraction_inside must be non-increasing in the multiplier; an "
        "inversion makes it non-decreasing")
    assert fr[0] > fr[-1]

    # Cross-check against the coverage quantile: a stop at the 90th percentile
    # of the excursion distribution must leave ~10% outside, not ~90%.
    rng = np.random.default_rng(2)
    real = np.abs(rng.normal(1.0, 0.5, 20_000))
    m90 = sp.coverage_multiplier(real, 90)
    assert sp.fraction_inside(real, m90) == pytest.approx(0.10, abs=0.005)
    assert sp.coverage_multiplier(real, 95) > m90


def test_floor_binding_counts_the_stop_falling_BELOW_the_floor():
    """The mirrored direction trap in Part D.

    The floor BINDS when the ATR term is SMALLER than the guard rail, so the
    rail sets the stop. Counting the other side would report the floor as
    nearly always binding on SOL, where it almost never does.
    """
    x = np.array([0.5, 1.0, 1.49, 1.50, 1.51, 3.0])
    assert sp.floor_binding_fraction(x, 1.50) == pytest.approx(3.0 / 6.0)
    assert sp.floor_binding_fraction(np.array([9.0, 9.0]), 1.50) == 0.0
    assert sp.floor_binding_fraction(np.array([0.1, 0.1]), 1.50) == 1.0


def test_coverage_multiplier_is_the_quantile_it_claims_to_be():
    x = np.arange(1.0, 101.0)
    assert sp.coverage_multiplier(x, 50) == pytest.approx(np.percentile(x, 50))
    assert sp.coverage_multiplier(x, 90) == pytest.approx(np.percentile(x, 90))
    assert np.isnan(sp.coverage_multiplier([], 90))
    assert np.isnan(sp.fraction_inside([]))


# ---------------------------------------------------------------------------
# Frozen constants, warm-up, and the fold minimum rule.
# ---------------------------------------------------------------------------

def test_frozen_inputs_are_transcribed_not_chosen():
    assert sp.DONCHIAN_PERIOD == 10
    assert sp.DONCHIAN_COMPARISON_PERIOD == 20
    assert sp.ATR_PERIOD == 14
    assert sp.STOP_ATR_MULT == 2.25
    assert sp.STOP_FLOOR_PCT == 1.50
    assert sp.TIMEFRAME == "1h"
    assert sp.MIN_TRAIN_SIGNALS == 200 and sp.MIN_TEST_SIGNALS == 50
    assert 2.25 in sp.MULTIPLIERS


def test_warmup_discard_is_exactly_114_bars():
    """Report 19's ATR convention, unchanged, so all three reports agree."""
    assert sp.WARMUP_STABILISATION_BARS == 100
    assert sp.WARMUP_BARS == 114
    for n in (200, 500, 1000):
        h, l, c = _flat(n)
        f = sp.analysis_frame(_frame(h, l, c))
        assert len(f) == n - 114
        assert f["atr"].notna().all(), "no NaN ATR may survive the discard"
        assert f["atr"].to_numpy() == pytest.approx(np.full(n - 114, 2.0),
                                                    rel=1e-12)


def test_fold_minimum_is_the_minimum_not_the_mean():
    """The binding number is the worst fold. A mean hides the fold that fails."""
    rows = [{"fold_id": i, "period": "train", "n_signals": v}
            for i, v in enumerate([900, 900, 900, 900, 40], start=1)]
    assert sp.fold_minimum(rows, "train") == 40
    assert sp.fold_minimum(rows, "train") != int(np.mean(
        [r["n_signals"] for r in rows]))
    assert not sp.meets_minimum(40, "train")
    assert sp.meets_minimum(200, "train")
    assert sp.meets_minimum(50, "test")
    assert not sp.meets_minimum(49, "test")
    with pytest.raises(ValueError):
        sp.fold_minimum(rows, "test")
    with pytest.raises(ValueError):
        sp.meets_minimum(10, "validation")


def test_fold_counts_do_not_double_count_a_two_sided_bar():
    """An outside bar can sweep both channels. It is ONE signal bar, counted
    once, with the overlap reported separately rather than dropped."""
    bars, _ = rs.build("BTCUSDT", sp.TIMEFRAME)
    f = sp.analysis_frame(bars)
    rows = sp.fold_counts(f)
    for r in rows:
        assert r["n_signals"] == r["n_long"] + r["n_short"] - r["n_both_directions"]
        assert r["n_signals"] <= r["bars"]
    assert sum(r["n_both_directions"] for r in rows) > 0, (
        "two-sided bars must actually occur, or this test is vacuous")


def test_the_real_population_is_not_vacuous_and_reject_is_a_subset_of_break():
    for sym in rs.SYMBOLS:
        bars, _ = rs.build(sym, sp.TIMEFRAME)
        f = sp.analysis_frame(bars)
        for brk, swp in (("break_long", "sweep_long"),
                         ("break_short", "sweep_short")):
            nb, ns = int(f[brk].sum()), int(f[swp].sum())
            assert nb > 1000, (sym, brk, nb)
            assert 0 < ns < nb, (sym, swp, ns, nb)
            assert bool((~f[brk] & f[swp]).sum() == 0), (
                "every wick-and-reject bar must also be a channel break")
            assert 0.3 < ns / nb < 0.8, (sym, swp, ns / nb)


def test_a_shorter_channel_admits_more_bars():
    """Donchian-10 must be a superset-sized population relative to Donchian-20.

    Not a sweep and not a selection -- a sanity property. A shorter lookback has
    a nearer channel, so it is broken more often. If this ever inverted, the
    period argument would not be reaching the channel.
    """
    bars, _ = rs.build("BTCUSDT", sp.TIMEFRAME)
    f10 = sp.analysis_frame(bars, period=10)
    f20 = sp.analysis_frame(bars, period=20)
    assert int(f10["break_long"].sum()) > int(f20["break_long"].sum())
    assert int(f10["sweep_long"].sum()) > int(f20["sweep_long"].sum())


def test_atr_matches_the_shared_implementation():
    """ATR is report 19's ATR, reused rather than reimplemented."""
    from src.timeframe import atr_profile as ap
    bars, _ = rs.build("ETHUSDT", sp.TIMEFRAME)
    atr = sp.atr_series(bars)
    tr = ap.true_range(bars["high"].to_numpy(float),
                       bars["low"].to_numpy(float),
                       bars["close"].to_numpy(float))
    expect = ap.wilder_atr(tr, period=14)
    assert np.isnan(atr[0])
    np.testing.assert_allclose(atr[1:], expect, rtol=0, atol=0, equal_nan=True)
    # And it agrees with report 19's ATR% table via the same denominator.
    pct = 100.0 * atr[114:] / bars["close"].to_numpy(float)[114:]
    assert np.median(pct) == pytest.approx(0.8440, abs=0.0005)


# ---------------------------------------------------------------------------
# The firewall, over the module's AST.
# ---------------------------------------------------------------------------

PERFORMANCE_NAMES = ("expectancy", "win_rate", "winrate", "profit_factor",
                     "sharpe", "net_pnl", "r_multiple", "equity", "pnl")


def _module_ast():
    return ast.parse(open(sp.__file__).read())


def test_no_performance_quantity_appears_in_the_module():
    """FIREWALL GUARD, over identifiers and string literals, not prose.

    The docstrings NAME the prohibited quantities in order to state the
    prohibition, so a raw grep would fire on the statement of the rule rather
    than on a violation of it. Docstrings are excluded; everything else is not.
    """
    tree = _module_ast()
    docstrings = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.FunctionDef, ast.ClassDef)):
            d = ast.get_docstring(node, clean=False)
            if d is not None:
                docstrings.add(d)
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            names.add(node.id)
        elif isinstance(node, ast.Attribute):
            names.add(node.attr)
        elif isinstance(node, ast.arg):
            names.add(node.arg)
        elif isinstance(node, (ast.FunctionDef, ast.ClassDef)):
            names.add(node.name)
        elif isinstance(node, ast.Constant) and isinstance(node.value, str):
            if node.value not in docstrings:
                names.add(node.value)
    blob = " ".join(names).lower()
    for banned in PERFORMANCE_NAMES:
        assert banned not in blob, "%r used as a name in %s" % (banned,
                                                               sp.__file__)


def test_module_simulates_nothing_and_reads_no_bar_after_the_signal():
    """Checked over the IMPORT GRAPH, not the source text.

    `simulate` is what may not be imported, and with it every exit, sizing and
    outcome path in the project. The engine's `signals` IS imported,
    deliberately, so the Donchian channel is the one Point 4 used.
    """
    banned = ("simulate", "src.engine.simulate", "src.sweep", "src.folds.run")
    imported = set()
    for node in ast.walk(_module_ast()):
        if isinstance(node, ast.Import):
            for a in node.names:
                imported.add(a.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imported.add(node.module)
                for a in node.names:
                    imported.add("%s.%s" % (node.module, a.name))
    for mod in imported:
        for bad in banned:
            assert not (mod == bad or mod.startswith(bad + ".")), mod
    assert "signals" in imported

    # No forward shift anywhere: a negative shift is how a future bar leaks in.
    src = open(sp.__file__).read()
    assert ".shift(-" not in src
    assert "shift(-1)" not in src


def test_no_open_price_is_read():
    for node in ast.walk(_module_ast()):
        if isinstance(node, ast.Attribute) and node.attr == "open_synth":
            pytest.fail("reads .open_synth")
        if isinstance(node, ast.Name) and node.id == "open_synth":
            pytest.fail("binds open_synth")
    for sym in rs.SYMBOLS:
        bars, _ = rs.build(sym, sp.TIMEFRAME)
        assert "open" not in bars.columns and "open_synth" not in bars.columns


def test_report_exists_and_states_the_frozen_geometry():
    path = os.path.join(rs.ROOT, "reports", "21_sweep_population.md")
    assert os.path.exists(path), path
    text = open(path).read()
    assert "2.25" in text and "1.50" in text
    assert "Donchian-10" in text
