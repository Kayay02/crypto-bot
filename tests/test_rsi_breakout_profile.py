"""Guards for the 1R.5 reversal-breakout population measurement.

THE RESULT THIS PROTECTS IS A NEGATIVE ONE, which makes the guards load-bearing
in a way they are not when a measurement finds something. An empty population is
what a broken detector also produces. Three of the tests below exist purely so
that "we found nothing" is distinguishable from "we could not have found
anything":

  * the Donchian exclusion test -- an off-by-one that puts the current bar in
    its own lookback window makes `close > max(high)` nearly unsatisfiable and
    empties the population silently;
  * the synthetic positive control -- a series that DOES contain a low-RSI
    breakout, which the detector must find;
  * the real-data non-vacuity check -- breakouts must exist at all.

The RSI expectation is hand-computed from Wilder's definition. It is NOT checked
against another library: a second implementation agreeing with the first proves
they share an author's assumptions, not that either is right. The comparison
against the engine's `rsi_wilder` that does appear here is a CONVERGENCE
measurement between two seeding conventions, not a correctness check, and it is
labelled as such.
"""

import ast
import datetime as dt
import os

import numpy as np
import pandas as pd
import pytest

from src.analysis import rsi_breakout_profile as rbp
from src.folds import schedule as sch
from src.timeframe import resample as rs


HOUR_MS = 3_600_000
T0 = 1_640_995_200_000  # 2022-01-01T00:00:00Z


def _frame(close, high=None, low=None, step=HOUR_MS, t0=T0):
    close = np.asarray(close, dtype=float)
    n = len(close)
    return pd.DataFrame({
        "ts": t0 + np.arange(n) * step,
        "high": close if high is None else np.asarray(high, dtype=float),
        "low": close if low is None else np.asarray(low, dtype=float),
        "close": close,
    })


# ---------------------------------------------------------------------------
# 1. Wilder RSI, hand-computed.
# ---------------------------------------------------------------------------

def test_rsi_seed_is_the_simple_mean_of_the_first_fourteen_deltas():
    """Fourteen deltas of +1 then one delta of -14, arithmetic by inspection.

    Seed: avg_gain = 1.0, avg_loss = 0.0 -> the zero-loss branch -> RSI 100.
    Next: avg_gain = (1.0*13 + 0)/14 = 13/14; avg_loss = (0*13 + 14)/14 = 1.0.
           RS = 13/14, RSI = 100 - 100/(1 + 13/14) = 48.148148...
    """
    close = np.concatenate([[100.0], 100.0 + np.arange(1, 15, dtype=float)])
    rsi = rbp.wilder_rsi(close)
    assert np.isnan(rsi[:14]).all(), "no RSI may exist before the seed lands"
    assert rsi[14] == pytest.approx(100.0, rel=1e-15)

    rsi2 = rbp.wilder_rsi(np.append(close, close[-1] - 14.0))
    assert rsi2[15] == pytest.approx(100.0 - 100.0 / (1.0 + (13.0 / 14.0)),
                                     rel=1e-15)
    assert rsi2[15] == pytest.approx(48.148148148148145, rel=1e-12)


def test_rsi_on_a_balanced_series_oscillates_about_fifty():
    """Alternating +1 / -1. The SEED is exactly 50; the recursion then swings.

    Seed: the first 14 deltas are seven +1s and seven -1s, so avg_gain =
    avg_loss = 0.5, RS = 1 and RSI = 50 exactly.

    Bar 15 is a gain: avg_gain = (0.5*13 + 1)/14 = 7.5/14, avg_loss = 0.5*13/14
    = 6.5/14, RS = 7.5/6.5 and RSI = 100 * 7.5/14 = 53.571428...

    Stated because it is the trap in the indicator: a balanced series does NOT
    sit at 50 under Wilder smoothing, it oscillates about it. Anything reading
    a single bar's RSI as "balanced == 50" is reading a phase, not a level.
    """
    close = 100.0 + np.array([0, 1, 0, 1] * 30, dtype=float)
    rsi = rbp.wilder_rsi(close)
    assert rsi[14] == pytest.approx(50.0, rel=1e-15)
    assert rsi[15] == pytest.approx(100.0 * 7.5 / 14.0, rel=1e-15)
    tail = rsi[14:]
    assert tail.min() > 48.0 and tail.max() < 53.6, "no drift, only phase"
    assert np.mean(rsi[-2:]) == pytest.approx(50.0, abs=0.01)


def test_rsi_second_hand_computed_case_with_a_non_uniform_seed():
    """Deltas 1..14 then a single -105.

    avg_gain seed = mean(1..14) = 7.5, avg_loss seed = 0.
    Next bar: avg_gain = 7.5*13/14 = 6.964285714...,
              avg_loss = 105/14 = 7.5, RS = 0.9285714285...,
              RSI = 100 - 100/(1 + RS) = 48.148148...
    """
    close = np.concatenate([[100.0],
                            100.0 + np.cumsum(np.arange(1, 15, dtype=float))])
    rsi = rbp.wilder_rsi(close)
    assert rsi[14] == pytest.approx(100.0, rel=1e-15)
    rsi2 = rbp.wilder_rsi(np.append(close, close[-1] - 105.0))
    ag, al = 7.5 * 13.0 / 14.0, 105.0 / 14.0
    assert rsi2[15] == pytest.approx(100.0 - 100.0 / (1.0 + ag / al), rel=1e-15)


def test_rsi_is_wilder_smoothing_not_a_rolling_mean():
    """A rolling mean forgets after 14 bars; Wilder never fully does.

    One big loss, then fourteen flat bars. Under a 14-bar rolling mean the loss
    would have left the window entirely and RSI would be back at its pre-shock
    value. Under Wilder it is still visibly depressed.
    """
    close = list(100.0 + np.array([0, 1] * 40, dtype=float))
    base = rbp.wilder_rsi(np.array(close))[-1]
    shocked = close[:60] + [close[59] - 30.0] + [close[59] - 30.0] * 14
    rsi = rbp.wilder_rsi(np.array(shocked))
    assert 48.0 < base < 54.0, "the pre-shock series is balanced"
    assert rsi[-1] < 20.0, "a 14-bar rolling mean would have forgotten the shock"


def test_rsi_zero_loss_branch_is_one_hundred():
    close = 100.0 + np.arange(30, dtype=float)
    assert rbp.wilder_rsi(close)[-1] == 100.0


def test_rsi_too_short_is_all_nan():
    rsi = rbp.wilder_rsi(np.arange(14, dtype=float))
    assert len(rsi) == 14 and np.all(np.isnan(rsi))


def test_rsi_convention_gap_against_the_engine_is_a_rounding_difference():
    """CONVERGENCE, NOT CORRECTNESS. Correctness is the hand-computed tests.

    This module seeds Wilder's averages with a simple mean (report 19's ATR
    convention); the engine's `rsi_wilder` is the EWM form, which seeds from the
    first value. The seed's weight decays as (13/14)^k, so after the 114-bar
    warm-up discard the two conventions cannot differ materially -- and if they
    ever did, every comparison in this step against Point 3's figures would be
    unsound. Asserted rather than assumed.
    """
    rng = np.random.default_rng(20)
    close = 100.0 * np.exp(np.cumsum(rng.normal(0.0, 0.01, 4000)))
    assert rbp.rsi_convention_gap(close) < 0.05


# ---------------------------------------------------------------------------
# 2. The Donchian exclusion convention.
# ---------------------------------------------------------------------------

def test_donchian_window_excludes_the_current_bar():
    """PLANTED-MUTATION GUARD: the current bar admitted to its own lookback.

    THE MUTATION. Drop or shorten the `.shift(1)` in `donchian_prior`, so
    `upper[T] = max(high[T-19..T])` instead of `max(high[T-20..T-1])`.

    WHY IT WOULD OTHERWISE PASS UNNOTICED. It does not raise and it does not
    produce an obviously wrong number. It SILENTLY REDEFINES THE POPULATION:
    close is bounded above by its own high, so admitting the current bar makes
    `close > max(high)` satisfiable only on a bar that closes exactly at its
    high -- the breakout population all but vanishes, and this step's headline
    result is that a population vanishes. The two failure modes are
    indistinguishable in the output table.

    Asserted three ways: the window contents directly, the first defined index,
    and the behavioural consequence on a constructed bar.
    """
    rng = np.random.default_rng(7)
    high = 100.0 + rng.random(200) * 10.0
    low = high - 1.0
    upper, lower = rbp.donchian_prior(high, low, rbp.DONCHIAN_PERIOD)
    p = rbp.DONCHIAN_PERIOD

    # First defined value sits at index `period`, not `period - 1`.
    assert np.isnan(upper[:p]).all(), "channel defined before it can be"
    assert np.isfinite(upper[p]), "channel must be defined at index period"

    # The window contents, stated directly.
    differs = 0
    for i in range(p, len(high)):
        assert upper[i] == pytest.approx(high[i - p:i].max(), rel=1e-15)
        assert lower[i] == pytest.approx(low[i - p:i].min(), rel=1e-15)
        if upper[i] != pytest.approx(high[i - p + 1:i + 1].max(), rel=1e-15):
            differs += 1
    assert differs > 0, (
        "the series must contain bars where including the current bar CHANGES "
        "the window max, or this test cannot detect the off-by-one")


def test_a_bar_breaks_out_on_prior_highs_not_its_own():
    """Behavioural form of the same guard.

    Twenty bars with high 10, then a bar with high 100, low 9 and close 11.
    Correct exclusion: the channel is 10, the close of 11 clears it -> BREAKOUT.
    Off-by-one: the channel becomes 100, the close of 11 does not clear it ->
    no breakout, and the population is quietly emptied.
    """
    p = rbp.DONCHIAN_PERIOD
    high = np.array([10.0] * p + [100.0])
    low = np.array([9.0] * p + [9.0])
    close = np.array([9.5] * p + [11.0])
    up, dn = rbp.breakout_masks(high, low, close, p)
    assert up[p], "close above the PRIOR 20-bar high must be a long breakout"
    assert not dn[p]
    assert not up[:p].any(), "no breakout may fire during the channel warm-up"

    # The mirror: a bar with a low far below the prior channel, closing above
    # the prior 20-bar low, must NOT be a short breakout.
    low2 = np.array([9.0] * p + [1.0])
    close2 = np.array([9.5] * p + [9.4])
    _, dn2 = rbp.breakout_masks(np.array([10.0] * (p + 1)), low2, close2, p)
    assert not dn2[p], "a wick below the channel is not a close below it"


def test_short_breakout_is_a_close_below_the_prior_channel_low():
    p = rbp.DONCHIAN_PERIOD
    high = np.array([10.0] * p + [10.0])
    low = np.array([9.0] * p + [1.0])
    close = np.array([9.5] * p + [8.0])
    up, dn = rbp.breakout_masks(high, low, close, p)
    assert dn[p] and not up[p]


def test_donchian_and_rsi_periods_are_point_fours_and_are_not_swept():
    assert rbp.DONCHIAN_PERIOD == 20
    assert rbp.RSI_PERIOD == 14
    assert rbp.donchian_prior is not None


# ---------------------------------------------------------------------------
# 3. SYNTHETIC POSITIVE CONTROL.
# ---------------------------------------------------------------------------

def _reversal_breakout_series():
    """A crash, a flat 20-bar base, then a small break of the base high.

    THE CONSTRUCTION IS THE ARGUMENT. A single large up-bar clearing a 20-bar
    high from a falling market does NOT produce a low RSI -- the breakout bar's
    own gain enters the average with weight 1/14 and drags RSI up with it. The
    only way a Donchian break coincides with a depressed RSI is if the break is
    SMALL, which requires the 20-bar high to sit right on top of current price,
    which requires a flat base. So:

      bars   0-149 : alternating 100 / 101, establishing avg_gain ~ avg_loss
      bars 150-169 : twenty bars of -3%, driving avg_gain to ~0
      bars 170-189 : twenty bars perfectly flat -- both averages decay by the
                     same (13/14) factor each bar, so RSI holds near 0 while
                     the 20-bar channel collapses onto current price
      bar      190 : +0.5%, which clears the flat channel by 0.5% and adds a
                     gain far too small to lift RSI back to 50

    Bar 190 is past the 114-bar warm-up, so it survives into the analysis frame.
    """
    close = [100.0 if i % 2 == 0 else 101.0 for i in range(150)]
    p = close[-1]
    for _ in range(20):
        p *= 0.97
        close.append(p)
    flat = close[-1]
    close.extend([flat] * 20)
    close.append(flat * 1.005)

    close = np.array(close)
    high, low = close.copy(), close.copy()
    high[:150] = close[:150] + 0.5
    low[:150] = close[:150] - 0.5
    for i in range(150, 170):          # falling bars span from the prior close
        high[i], low[i] = close[i - 1], close[i]
    high[-1], low[-1] = close[-1], flat
    return _frame(close, high, low)


def test_positive_control_a_low_rsi_breakout_is_found():
    """WITHOUT THIS TEST AN EMPTY RESULT IS UNINTERPRETABLE.

    The detector must find a breakout that fires from a depressed RSI when one
    is actually present in the data. Run through the FULL pipeline -- resampled
    bar frame in, warm-up discarded, verdict machinery out -- not through the
    indicator functions in isolation, because the defect being guarded against
    could live anywhere along that path.
    """
    frame = rbp.analysis_frame(_reversal_breakout_series())
    mask = frame["breakout_long"].to_numpy()
    assert mask.sum() == 1, "expected exactly one constructed long breakout"

    row = frame[mask].iloc[0]
    assert row["rsi"] < rbp.NEGLIGIBLE_RSI_LEVEL, (
        "the constructed breakout must sit BELOW RSI 50 -- it is the population "
        "whose absence this step reports")
    assert row["rsi"] < 20.0, "and comfortably below, not marginally"
    assert row["close"] > row["donchian_upper"]

    # The verdict machinery must carry it through, not just the detector.
    rsi = frame["rsi"].to_numpy(float)
    n_long = int(mask.sum())
    pct = 100.0 * rbp.count_below(rsi[mask]) / n_long
    assert pct == pytest.approx(100.0)
    assert not rbp.is_negligible(pct)
    assert rbp.verdict({("SYNTH", "1h"): pct}) == rbp.SCALE_DEPENDENT


def test_positive_control_is_not_trivially_satisfied():
    """A NEGATIVE control beside the positive one.

    The same pipeline on a steadily rising series must find breakouts and find
    NONE of them below RSI 50. A detector that flagged everything would pass the
    positive control and fail here.
    """
    rng = np.random.default_rng(11)
    close = 100.0 * np.exp(np.cumsum(rng.normal(0.0008, 0.004, 1200)))
    frame = rbp.analysis_frame(_frame(close, close * 1.001, close * 0.999))
    mask = frame["breakout_long"].to_numpy()
    assert mask.sum() > 20, "a rising series must produce breakouts"
    assert rbp.count_below(frame["rsi"].to_numpy(float)[mask]) == 0


def test_rejection_table_counts_the_right_side_of_the_threshold():
    """LONG rejects BELOW the level; SHORT rejects ABOVE it. Not interchangeable."""
    vals = np.array([10.0, 45.0, 50.0, 55.0, 90.0])
    rows = {r["threshold"]: r for r in rbp.rejection_table(vals, (50,), rbp.LONG)}
    assert rows[50]["rejected"] == 2       # 10, 45 -- 50 itself passes
    assert rows[50]["n_exactly_at"] == 1
    assert rows[50]["rejected_pct"] == pytest.approx(40.0)

    rows = {r["threshold"]: r for r in rbp.rejection_table(vals, (50,), rbp.SHORT)}
    assert rows[50]["rejected"] == 2       # 55, 90
    with pytest.raises(ValueError):
        rbp.rejection_table(vals, (50,), "sideways")


def test_rejection_counts_are_monotone_in_the_threshold():
    rng = np.random.default_rng(3)
    vals = rng.uniform(0.0, 100.0, 5000)
    long_rows = rbp.rejection_table(vals, rbp.RSI_LOWER_CANDIDATES, rbp.LONG)
    counts = [r["rejected"] for r in long_rows]
    assert counts == sorted(counts), "a higher rsi_lower cannot reject fewer bars"
    short_rows = rbp.rejection_table(vals, rbp.RSI_UPPER_CANDIDATES, rbp.SHORT)
    counts = [r["rejected"] for r in short_rows]
    assert counts == sorted(counts), "a lower rsi_upper cannot reject fewer bars"


# ---------------------------------------------------------------------------
# 4. PLANTED MUTATION -- the holdout seal.
# ---------------------------------------------------------------------------

def test_the_window_is_inherited_and_cannot_reach_the_holdout():
    """PLANTED MUTATION GUARD: the date filter widened to admit 2025.

    THE MUTATION. In `src/timeframe/resample.py`, widen either half of the
    filter -- `WINDOW_END` past 2024-12-31 or `ALLOWED_YEARS` to include 2025.

    WHY IT WOULD OTHERWISE PASS UNNOTICED. The 1m layer physically holds
    year=2025 and year=2026; the seal is not maintained by absence. A widened
    filter raises nothing, and every RSI figure in this report would simply
    become better-sampled while the holdout was spent without anyone deciding
    to spend it.

    This module deliberately has NO window constant of its own -- it inherits
    `resample`'s -- so this asserts the inherited one.
    """
    assert rs.WINDOW_START == dt.date(2022, 1, 1)
    assert rs.WINDOW_END == dt.date(2024, 12, 31)
    assert rs.WINDOW_END < sch.HOLDOUT_TEST_START
    assert rs.WINDOW_END + dt.timedelta(days=1) == sch.HOLDOUT_TEST_START
    assert rs.ALLOWED_YEARS == (2022, 2023, 2024)
    assert max(rs.ALLOWED_YEARS) < sch.HOLDOUT_TEST_START.year
    # And this module defines no second window that could drift from it.
    assigned = set()
    for node in ast.walk(_module_ast()):
        if isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name):
                    assigned.add(t.id)
    assert not {"WINDOW_START", "WINDOW_END", "ALLOWED_YEARS"} & assigned, (
        "a second window constant here could drift from resample's")
    assert "2025" not in open(rbp.__file__).read()


def test_analysis_frame_refuses_a_holdout_bar():
    """The runtime guard must be able to REFUSE, or it proves nothing."""
    sealed = rs.holdout_start_ms()
    n = 200
    close = 100.0 + np.arange(n, dtype=float)
    bad = _frame(close, t0=sealed - (n - 5) * HOUR_MS)
    assert int(bad["ts"].max()) >= sealed
    with pytest.raises(rs.HoldoutBreach, match="sealed holdout boundary"):
        rbp.analysis_frame(bad)


@pytest.mark.parametrize("timeframe", list(rbp.TIMEFRAMES))
def test_no_measured_bar_reaches_the_holdout(timeframe):
    """End to end on the real data, at both timeframes this step reads."""
    sealed = rs.holdout_start_ms()
    for sym in rs.SYMBOLS:
        bars, _ = rs.build(sym, timeframe)
        frame = rbp.analysis_frame(bars)
        assert len(frame)
        assert int(frame["ts"].max()) < sealed
        assert int((frame["ts"] >= sealed).sum()) == 0
        last = dt.datetime.fromtimestamp(int(frame["ts"].max()) / 1000,
                                         dt.timezone.utc)
        assert last.year == 2024


# ---------------------------------------------------------------------------
# 5. PLANTED MUTATION -- the negligibility comparison inverted.
# ---------------------------------------------------------------------------

def test_negligibility_comparison_is_not_inverted():
    """PLANTED MUTATION GUARD: `pct_below < max_pct` -> `pct_below > max_pct`.

    THE MUTATION. In `rsi_breakout_profile.is_negligible`, flip the comparison.

    WHY IT IS EASY TO GET WRONG AND HARD TO SPOT. Every number in every table
    stays identical. The only thing that changes is the single word at the end
    of the report -- STRUCTURAL becomes SCALE-DEPENDENT -- and the report then
    states the opposite conclusion over a correct set of figures, which is the
    most expensive kind of defect this step can ship. There is no arithmetic
    anywhere else that would look wrong.

    A SMALL percentage is the EMPTY population (hypothesis stays unexercised);
    a LARGE percentage is the LIVE finding. Asserted as the ordering, not as a
    single point, so an inversion reverses a sequence rather than one label.
    """
    assert rbp.NEGLIGIBLE_MAX_PCT == 1.0
    assert rbp.NEGLIGIBLE_RSI_LEVEL == 50.0

    assert rbp.is_negligible(0.0) is True
    assert rbp.is_negligible(0.5) is True
    assert rbp.is_negligible(0.999) is True
    # Strict: "fewer than 1%" is read as written, so exactly 1.00% is NOT.
    assert rbp.is_negligible(1.0) is False
    assert rbp.is_negligible(5.0) is False
    assert rbp.is_negligible(100.0) is False

    seen = [rbp.is_negligible(p) for p in (0.0, 0.1, 0.9, 1.0, 2.0, 50.0)]
    assert seen == [True, True, True, False, False, False]
    with pytest.raises(ValueError):
        rbp.is_negligible(float("nan"))


def test_verdict_requires_every_cell_and_has_no_partial_pass():
    """One live cell is enough to make the emptiness a local fact, not a law."""
    ok = {("BTCUSDT", "1h"): 0.0, ("ETHUSDT", "1h"): 0.08,
          ("SOLUSDT", "1h"): 0.9}
    assert rbp.verdict(ok) == rbp.STRUCTURAL
    for key in list(ok):
        broken = dict(ok)
        broken[key] = 4.0
        assert rbp.verdict(broken) == rbp.SCALE_DEPENDENT
    with pytest.raises(ValueError):
        rbp.verdict({})


# ---------------------------------------------------------------------------
# Warm-up, and agreement with report 19's bar accounting.
# ---------------------------------------------------------------------------

def test_warmup_discard_is_exactly_114_bars():
    """1 (no previous close) + 13 (before the seed lands) + 100 (stabilisation).

    The same arithmetic as report 19's ATR warm-up, so the two measurements
    describe the same bars.
    """
    assert rbp.WARMUP_STABILISATION_BARS == 100
    assert rbp.WARMUP_BARS == 114
    for n in (200, 500, 1000):
        frame = rbp.analysis_frame(_frame(100.0 + np.arange(n, dtype=float)))
        assert len(frame) == n - 114
    assert (13.0 / 14.0) ** 100 < 1e-3
    assert frame["rsi"].notna().all(), "no NaN RSI may survive the discard"


def test_bar_counts_match_report_19():
    """26,190 at 1h and 105,102 at 15m -- report 19 section 3, same window."""
    expected = {"1h": (26_304, 26_190), "15m": (105_216, 105_102)}
    for tf, (formed, analysed) in expected.items():
        for sym in rs.SYMBOLS:
            bars, st = rs.build(sym, tf)
            assert len(bars) == formed, (sym, tf)
            assert st["buckets_dropped"] == 0, (sym, tf)
            assert len(rbp.analysis_frame(bars)) == analysed, (sym, tf)


# ---------------------------------------------------------------------------
# Non-vacuity and the Point 3 reconciliation, on the real window.
# ---------------------------------------------------------------------------

def test_the_real_population_is_not_vacuous():
    """Breakouts must EXIST. An empty breakout population would make the
    headline result an artefact of the detector rather than of the market."""
    for tf in rbp.TIMEFRAMES:
        for sym in rs.SYMBOLS:
            bars, _ = rs.build(sym, tf)
            frame = rbp.analysis_frame(bars)
            n_long = int(frame["breakout_long"].sum())
            n_short = int(frame["breakout_short"].sum())
            assert n_long > 500, (sym, tf, n_long)
            assert n_short > 500, (sym, tf, n_short)
            # A few percent of bars, not a few tenths and not a third.
            assert 0.01 < n_long / len(frame) < 0.15, (sym, tf)


def test_fifteen_minute_control_reproduces_point_3():
    """The 15m control, narrowed to Point 3's own population and window.

    Point 3 measured the engine's trend AND Donchian conditions over 2022-23;
    this module measures Donchian alone over 2022-24. Narrowing one to the other
    must land on report 07 section 5.7's minimum RSI figures, or the two steps
    are not measuring the same thing and no comparison between them is valid.

    The residual is the warm-up: this module discards 114 bars where Point 3
    discarded about 50, so ~64 bars at the start of 2022 are absent here. That
    moves the counts by a handful of bars and cannot move a minimum by much.
    """
    total = 0
    for sym in rs.SYMBOLS:
        bars, _ = rs.build(sym, "15m")
        rec = rbp.reconcile_point_3(rbp.analysis_frame(bars))
        assert rec["min_rsi_long"] == pytest.approx(
            rbp.POINT_3_MIN_RSI_LONG[sym], abs=0.02), sym
        assert rec["min_rsi_long"] > rbp.NEGLIGIBLE_RSI_LEVEL, sym
        assert rec["max_rsi_short"] < rbp.NEGLIGIBLE_RSI_LEVEL, sym
        total += rec["n_long"] + rec["n_short"]
    assert abs(total - rbp.POINT_3_BREAKOUT_BARS_TOTAL) < 50, total


def test_distribution_percentiles_are_ordered():
    rng = np.random.default_rng(5)
    d = rbp.distribution(rng.uniform(0.0, 100.0, 10_000))
    assert d["min"] <= d["p1"] <= d["p5"] <= d["p10"] <= d["p25"]
    assert d["p25"] <= d["p50"] <= d["p75"] <= d["p90"] <= d["max"]
    assert d["n"] == 10_000
    empty = rbp.distribution([])
    assert empty["n"] == 0 and np.isnan(empty["p50"])


# ---------------------------------------------------------------------------
# The firewall, over the module's AST.
# ---------------------------------------------------------------------------

PERFORMANCE_NAMES = ("expectancy", "win_rate", "winrate", "profit_factor",
                     "sharpe", "net_pnl", "r_multiple", "equity", "pnl")


def _module_ast():
    return ast.parse(open(rbp.__file__).read())


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
                                                               rbp.__file__)


def test_module_simulates_nothing():
    """Checked over the IMPORT GRAPH, not the source text.

    The engine's `signals` IS imported, deliberately -- the Donchian channel and
    the EMA must be the ones Point 4 used. `simulate` is what may not be, and
    with it every exit, sizing and outcome path in the project.
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
    assert "signals" in imported, (
        "the engine's Donchian must be reused, not reimplemented")


def test_no_open_price_is_read():
    """`open_synth` is dropped by the loader; nothing here may reconstruct it."""
    for node in ast.walk(_module_ast()):
        if isinstance(node, ast.Attribute) and node.attr == "open_synth":
            pytest.fail("reads .open_synth")
        if isinstance(node, ast.Name) and node.id == "open_synth":
            pytest.fail("binds open_synth")
    for sym in rs.SYMBOLS:
        bars, _ = rs.build(sym, "1h")
        assert "open" not in bars.columns
        assert "open_synth" not in bars.columns


def test_report_exists_and_states_the_frozen_threshold():
    """The report must carry the pre-fixed threshold, not just the module."""
    path = os.path.join(rs.ROOT, "reports", "20_rsi_breakout_population.md")
    assert os.path.exists(path), path
    text = open(path).read()
    assert "1%" in text and "RSI 50" in text
    assert rbp.STRUCTURAL in text or rbp.SCALE_DEPENDENT in text
