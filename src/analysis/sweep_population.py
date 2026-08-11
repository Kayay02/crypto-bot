"""The wick-and-reject sweep population at 1h, and whether the frozen stop fits it.

WHAT IS BEING ASKED. The new thesis is a FAILED BREAKOUT / LIQUIDITY SWEEP. Its
trigger is a bar whose EXTREME breaks a Donchian-10 channel intrabar but whose
CLOSE returns inside it -- price reached for the liquidity beyond the level and
was rejected. The stop geometry was frozen independently: 2.25 x ATR(14) with a
1.50% floor as a guard rail.

THE INTERNAL-CONSISTENCY PROBLEM. A wick-and-reject bar is BY CONSTRUCTION a
large-range bar -- it has to travel beyond the channel and come back within one
bar. If the distance from its close to its own sweep extreme exceeds 2.25 x ATR,
then a 2.25 x ATR stop sits INSIDE that extreme, and a mere retest of the level
the thesis claims was rejected would take the stop out. The stop would
contradict the mechanism it is supposed to protect. That is decidable from
indicator distributions alone, on bars, with nothing simulated.

THE ARITHMETIC IS REPORTED, THE DECISION IS NOT MADE HERE. m = 2.25 is frozen.
This module computes the fraction of signals each candidate multiplier would
leave inside the extreme, and the coverage quantiles. It proposes nothing.

N = 10 IS FROZEN. Fixed as a one-time structural choice: sweeps target recent
local liquidity, not multi-day boundaries. The Donchian-20 figures reported
alongside are A COMPARISON FOR THE RECORD -- so the effect of the choice is
visible and quantified rather than assumed -- and NOT a sweep. Nothing here
selects a period.

THE FIREWALL IS RE-ARMED. Signal counts, pass rates and indicator distributions
are permitted pre-firewall quantities. No trade is simulated: no entry is taken,
no exit is computed, no position is sized, no outcome is evaluated. NOTHING HERE
READS A BAR LATER THAN THE ONE IT DESCRIBES -- every quantity is a function of
the signal bar and its own prior channel, so there is no forward return to
compute even by accident. A test walks this module's AST and refuses any
performance name as an identifier or a string literal.

THE HOLDOUT IS SEALED. The window is 2022-01-01 to 2024-12-31, inherited whole
from `src/timeframe/resample.py`; this module defines no window constant of its
own and a test asserts it defines none. Every frame passes back through
`resample.assert_sealed` on the way out. Fold boundaries come from the tracked
`folds.json`, whose nine in-sample folds all end at 2024-12-31; the holdout
entry in that file is never read.

NO OPEN. `open_synth` is dropped at the load boundary by the loader reused here.
The trigger needs high, low and close; it has no use for an open.
"""

import os
import sys

import numpy as np
import pandas as pd

from src.analysis import rsi_breakout_profile as rbp
from src.folds import schedule as sch
from src.timeframe import atr_profile as ap
from src.timeframe import resample as rs

# The engine's Donchian channel, the same one report 20 measured against and
# the same one Point 4 used. Imported the way src/analysis/structural_pass.py
# already imports it; src/engine is not a package.
sys.path.insert(0, os.path.join(rs.ROOT, "src", "engine"))

import signals  # noqa: E402


# ---------------------------------------------------------------------------
# FROZEN INPUTS. Transcribed, not chosen here. Not swept. A test pins each one.
# ---------------------------------------------------------------------------

TIMEFRAME = "1h"
"""Selected by the rule frozen at 96c96cf (report 19, 74e3ca9)."""

DONCHIAN_PERIOD = 10
"""FROZEN as a one-time structural choice: sweeps target recent local
liquidity, not multi-day boundaries. Will not be swept or revisited."""

DONCHIAN_COMPARISON_PERIOD = 20
"""A SINGLE FIXED COMPARISON so the effect of N = 10 is visible rather than
assumed. Not a sweep, and nothing selects between the two."""

ATR_PERIOD = 14

STOP_ATR_MULT = 2.25
"""FROZEN stop geometry. Reported against, never adjusted here."""

STOP_FLOOR_PCT = 1.50
"""The guard-rail floor, in PERCENT of entry. Report 18 section 4."""

MULTIPLIERS = (2.0, 2.25, 2.5, 3.0, 3.5)
"""Candidate multipliers for the sensitivity column. 2.25 is the frozen one;
the others exist so the shape of the answer around it is visible."""

COVERAGE_LEVELS = (90, 95)
"""Coverage quantiles of the excursion distribution, reported as arithmetic."""

MIN_TRAIN_SIGNALS = 200
MIN_TEST_SIGNALS = 50
"""Per-fold signal minimums this step checks the population against."""

WARMUP_STABILISATION_BARS = 100
WARMUP_BARS = 1 + (ATR_PERIOD - 1) + WARMUP_STABILISATION_BARS
"""114 BARS DISCARDED -- report 19's ATR convention, unchanged, so this report
describes exactly the bars reports 19 and 20 describe.

1 (the first bar has no previous close, so no true range at all) + 13 (true
ranges before the seed window completes) + 100 (ATR values after the seed,
discarded for stabilisation; the seed's residual weight is (13/14)^100 =
6.0e-4). Donchian-10's own 10-bar warm-up and Donchian-20's 20-bar warm-up are
both strictly inside this and never bind.

THE DISCARD ENDS AT 2022-01-05T18:00Z, nearly three months before fold 1's
train_start of 2022-04-01, so every fold period below is fully warmed and no
fold is measured on a partially-formed indicator.
"""

PERCENTILES = (10, 25, 50, 75, 90, 95, 99)

LONG, SHORT = rbp.LONG, rbp.SHORT

#: One percentile-summary implementation in the project, not two. Report 20's is
#: already guarded by hand-checked tests; re-declaring it here would create two
#: that must agree.
distribution = rbp.distribution


# ---------------------------------------------------------------------------
# Indicators.
# ---------------------------------------------------------------------------

def atr_series(bars, period=ATR_PERIOD):
    """Wilder ATR(14) in PRICE units, aligned to `bars`.

    Built from `src/timeframe/atr_profile.py`'s `true_range` and `wilder_atr` --
    reused, not reimplemented, so this report's ATR is report 19's ATR. Those
    functions are seeded with the simple mean of the first 14 true ranges and
    are hand-checked by test; an EWM would seed differently.

    `true_range` drops bar 0 (no previous close, so no true range), so element i
    of its output belongs to bar i+1 and the result is realigned here. Bars
    0..13 carry NaN.
    """
    high = np.asarray(bars["high"], dtype=float)
    low = np.asarray(bars["low"], dtype=float)
    close = np.asarray(bars["close"], dtype=float)
    out = np.full(len(close), np.nan, dtype=float)
    if len(close) < 2:
        return out
    out[1:] = ap.wilder_atr(ap.true_range(high, low, close), period=period)
    return out


# ---------------------------------------------------------------------------
# The trigger.
# ---------------------------------------------------------------------------

def sweep_masks(high, low, close, period=DONCHIAN_PERIOD):
    """Channel-break and wick-and-reject masks, both directions.

    THE EXCLUSION CONVENTION, STATED ONCE:

        upper[T] = max( high[T-period] .. high[T-1] )    the current bar's own
        lower[T] = min( low[T-period]  .. low[T-1]  )    high and low are NOT in
                                                         its own window

    THE TRIGGER:

        LONG SWEEP  (downside sweep, rejected -> long signal)
            low[T]   <  lower[T]        the extreme breaks the channel intrabar
            close[T] >  lower[T]        the close returns INSIDE the channel

        SHORT SWEEP (upside sweep, rejected -> short signal)
            high[T]  >  upper[T]
            close[T] <  upper[T]

    CHANNEL BREAK is the FIRST condition alone -- the channel was broken
    intrabar, whatever the close then did. Wick-and-reject is a subset of it,
    and the ratio between them is the rejection rate.

    STRICTNESS: all four comparisons are STRICT. A bar whose low exactly equals
    the prior minimum has not broken the channel, and a close landing exactly ON
    the level has not returned inside it. Ties are counted and reported rather
    than argued about -- `tie_counts` returns them.

    AN OFF-BY-ONE HERE IS NOT AN ERROR THAT RAISES. Admitting the current bar to
    its own window makes `low < min(low)` UNSATISFIABLE -- the bar's own low is
    in the minimum, so nothing can be below it -- and the population becomes
    empty. Shifting the other way makes it trivial. A test asserts the window
    contents directly and fails under either.
    """
    upper, lower = signals.donchian_prior(high, low, period)
    high = np.asarray(high, dtype=float)
    low = np.asarray(low, dtype=float)
    close = np.asarray(close, dtype=float)
    ok_up, ok_dn = np.isfinite(upper), np.isfinite(lower)

    break_long = (low < lower) & ok_dn
    break_short = (high > upper) & ok_up
    return {
        "donchian_upper": upper,
        "donchian_lower": lower,
        "break_long": break_long,
        "break_short": break_short,
        "sweep_long": break_long & (close > lower),
        "sweep_short": break_short & (close < upper),
    }


def tie_counts(high, low, close, period=DONCHIAN_PERIOD):
    """Bars sitting exactly ON a boundary, where < and <= would disagree.

    Reported for the same reason report 20 reported them: a strictness
    convention asserted without evidence that it never bites is an assumption,
    not a convention.
    """
    upper, lower = signals.donchian_prior(high, low, period)
    high = np.asarray(high, dtype=float)
    low = np.asarray(low, dtype=float)
    close = np.asarray(close, dtype=float)
    return {
        "low_equals_lower": int(np.sum(low == lower)),
        "high_equals_upper": int(np.sum(high == upper)),
        "close_equals_lower": int(np.sum(close == lower)),
        "close_equals_upper": int(np.sum(close == upper)),
    }


# ---------------------------------------------------------------------------
# The measurement frame.
# ---------------------------------------------------------------------------

def analysis_frame(bars, period=DONCHIAN_PERIOD, atr_period=ATR_PERIOD,
                   warmup=WARMUP_BARS):
    """Attach ATR, the channel, both masks and the geometry columns.

    ORDER MATTERS. Indicators are computed on the FULL bar frame and the warm-up
    is trimmed afterwards, so no rolling window is starved at the seam.

    THE GEOMETRY COLUMNS, defined for every bar and selected by mask when
    reported, so the two directions cannot pick up different conventions:

        excursion_long  = close - low       entry to the swept extreme, a long
        excursion_short = high - close      entry to the swept extreme, a short
        excursion_atr_* = excursion / ATR
        range_atr       = (high - low) / ATR
        stop_pct        = 100 * 2.25 * ATR / close

    Both excursions are non-negative by construction on any real bar, since
    low <= close <= high. Every one of these reads the signal bar and nothing
    after it.
    """
    high = bars["high"].to_numpy(float)
    low = bars["low"].to_numpy(float)
    close = bars["close"].to_numpy(float)
    atr = atr_series(bars, atr_period)
    m = sweep_masks(high, low, close, period)

    safe_atr = np.where(atr > 0.0, atr, np.nan)
    out = pd.DataFrame({
        "ts": bars["ts"].to_numpy(),
        "high": high, "low": low, "close": close, "atr": atr,
        "donchian_upper": m["donchian_upper"],
        "donchian_lower": m["donchian_lower"],
        "break_long": m["break_long"], "break_short": m["break_short"],
        "sweep_long": m["sweep_long"], "sweep_short": m["sweep_short"],
        "excursion_atr_long": (close - low) / safe_atr,
        "excursion_atr_short": (high - close) / safe_atr,
        "range_atr": (high - low) / safe_atr,
        "stop_pct": 100.0 * STOP_ATR_MULT * atr / close,
    })
    out = out.iloc[warmup:].reset_index(drop=True)
    return rs.assert_sealed(out, "analysis_frame")


def excursion_of(frame, direction):
    """The excursion_atr values ON the wick-and-reject bars of one direction."""
    if direction == LONG:
        return frame.loc[frame["sweep_long"].to_numpy(),
                         "excursion_atr_long"].to_numpy(float)
    if direction == SHORT:
        return frame.loc[frame["sweep_short"].to_numpy(),
                         "excursion_atr_short"].to_numpy(float)
    raise ValueError("direction must be %r or %r, got %r"
                     % (LONG, SHORT, direction))


# ---------------------------------------------------------------------------
# THE GEOMETRY CHECK.
# ---------------------------------------------------------------------------

def fraction_inside(excursion_atr, mult=STOP_ATR_MULT):
    """Fraction of signals whose SWEEP EXTREME lies BEYOND a `mult` x ATR stop.

    `excursion_atr > mult` means the distance from the close to the swept
    extreme is LARGER than the stop distance, so the stop sits INSIDE the
    extreme and a retest of the swept level would take it out. That is the
    failure direction and this returns its frequency.

    THE COMPARISON IS THE EASY THING TO INVERT AND THE HARD THING TO NOTICE.
    Counting `excursion_atr < mult` instead returns the complement, which is
    also a number between 0 and 1, also varies sensibly with `mult`, and is
    monotone in the same-looking way. It changes NO distributional figure --
    every percentile, every count, every ATR table stays identical -- so it is
    invisible to any test that does not target it directly. It would simply
    reverse the report's conclusion. A planted mutation inverts exactly this.
    """
    x = np.asarray(excursion_atr, dtype=float)
    x = x[np.isfinite(x)]
    if not len(x):
        return float("nan")
    return float(np.sum(x > mult) / len(x))


def coverage_multiplier(excursion_atr, pct):
    """The multiplier placing the stop BEYOND the extreme on `pct`% of signals.

    That is the `pct`th percentile of the excursion distribution: a stop at that
    many ATR clears the swept extreme on `pct`% of the population by definition
    of the quantile. Arithmetic only -- no multiplier is proposed.
    """
    x = np.asarray(excursion_atr, dtype=float)
    x = x[np.isfinite(x)]
    if not len(x):
        return float("nan")
    return float(np.percentile(x, pct))


def floor_binding_fraction(stop_pct, floor=STOP_FLOOR_PCT):
    """Fraction of bars where 2.25 x ATR falls BELOW the cost floor.

    Below the floor means the ATR term is smaller than the guard rail, so the
    guard rail -- not the volatility -- sets the stop. That is the floor
    BINDING, the condition report 19 said should be rare at 1h.
    """
    x = np.asarray(stop_pct, dtype=float)
    x = x[np.isfinite(x)]
    if not len(x):
        return float("nan")
    return float(np.sum(x < floor) / len(x))


# ---------------------------------------------------------------------------
# Folds. Boundaries come from the tracked artifact, not from arithmetic here.
# ---------------------------------------------------------------------------

def fold_windows(path=sch.FOLDS_PATH):
    """(fold_id, period, lo_ms, hi_ms) for the nine IN-SAMPLE folds.

    Read from the tracked `folds.json` rather than recomputed, so the fold
    boundaries this report counts against are the ones the project committed at
    af9d314 and not a second derivation that could drift.

    THE HOLDOUT ENTRY IN THAT FILE IS NOT READ. Only `payload["folds"]` is
    walked, and every window returned is asserted to end before the seal.

    BOUNDARY CONVENTION ACROSS TIMEFRAMES. `folds.json` states ends in 15m
    terms -- `train_end_ms` is 23:45:00Z of the end day. Bars are assigned by
    `lo <= ts <= hi` on the BUCKET START. At 1h the last bucket of a day starts
    at 23:00, and no 1h bucket starts between 23:00 and midnight, so the 15m
    end admits exactly the 1h bars of the end day and nothing beyond it. The
    inclusive-inclusive form is therefore exact at 1h and needs no adjustment.
    """
    payload = sch.load_schedule(path)
    sealed = rs.holdout_start_ms()
    out = []
    for f in payload["folds"]:
        for period in ("train", "test"):
            lo, hi = f["%s_start_ms" % period], f["%s_end_ms" % period]
            if lo is None or hi is None:
                continue
            if hi >= sealed:
                raise rs.HoldoutBreach(
                    "fold %s %s ends at ts=%d, at or past the sealed holdout "
                    "boundary" % (f["fold_id"], period, hi))
            out.append((f["fold_id"], period, int(lo), int(hi)))
    return out


def fold_counts(frame, windows=None):
    """Wick-and-reject signals per fold period, BOTH DIRECTIONS COMBINED.

    A signal is a bar carrying either mask. The two are disjoint in practice but
    not by construction -- an outside bar could sweep both channels and reject
    both -- so they are combined with OR and the overlap is counted separately
    rather than double-counted or silently dropped.
    """
    windows = fold_windows() if windows is None else windows
    ts = frame["ts"].to_numpy()
    lmask = frame["sweep_long"].to_numpy()
    smask = frame["sweep_short"].to_numpy()
    both = lmask & smask
    any_signal = lmask | smask
    rows = []
    for fold_id, period, lo, hi in windows:
        inw = (ts >= lo) & (ts <= hi)
        rows.append({
            "fold_id": fold_id,
            "period": period,
            "bars": int(inw.sum()),
            "n_long": int((lmask & inw).sum()),
            "n_short": int((smask & inw).sum()),
            "n_signals": int((any_signal & inw).sum()),
            "n_both_directions": int((both & inw).sum()),
        })
    return rows


def fold_minimum(rows, period):
    """The MINIMUM signal count across folds for one period. The binding number.

    A mean over nine folds hides the fold that fails; the design has to survive
    its worst fold, not its average one.
    """
    vals = [r["n_signals"] for r in rows if r["period"] == period]
    if not vals:
        raise ValueError("no rows for period %r" % (period,))
    return min(vals)


def meets_minimum(count, period):
    if period == "train":
        return bool(count >= MIN_TRAIN_SIGNALS)
    if period == "test":
        return bool(count >= MIN_TEST_SIGNALS)
    raise ValueError("period must be 'train' or 'test', got %r" % (period,))


# ---------------------------------------------------------------------------
# The whole pass.
# ---------------------------------------------------------------------------

def profile(symbols=rs.SYMBOLS, timeframe=TIMEFRAME,
            periods=(DONCHIAN_PERIOD, DONCHIAN_COMPARISON_PERIOD),
            derived_dir=rs.DERIVED):
    """Every symbol x Donchian-period cell, plus the per-fold counts."""
    windows = fold_windows()
    cells, frames = {}, {}
    for n in periods:
        for sym in symbols:
            bars, bucket_stats = rs.build(sym, timeframe,
                                          derived_dir=derived_dir)
            frame = analysis_frame(bars, period=n)
            n_bars = len(frame)
            cell = {
                "symbol": sym,
                "donchian": n,
                "bars": n_bars,
                "buckets_dropped": bucket_stats["buckets_dropped"],
                "ties": tie_counts(bars["high"].to_numpy(float),
                                   bars["low"].to_numpy(float),
                                   bars["close"].to_numpy(float), n),
                "folds": fold_counts(frame, windows),
            }
            for name, brk, swp in (("long", "break_long", "sweep_long"),
                                   ("short", "break_short", "sweep_short")):
                nb = int(frame[brk].sum())
                ns = int(frame[swp].sum())
                exc = excursion_of(frame, name)
                cell[name] = {
                    "n_break": nb,
                    "pct_break": 100.0 * nb / n_bars if n_bars else float("nan"),
                    "n_sweep": ns,
                    "pct_sweep": 100.0 * ns / n_bars if n_bars else float("nan"),
                    "rejection_rate": (ns / nb) if nb else float("nan"),
                    "excursion": distribution(exc, PERCENTILES),
                    "fraction_inside": {m: fraction_inside(exc, m)
                                        for m in MULTIPLIERS},
                    "coverage": {p: coverage_multiplier(exc, p)
                                 for p in COVERAGE_LEVELS},
                    "range_atr": distribution(
                        frame.loc[frame[swp].to_numpy(),
                                  "range_atr"].to_numpy(float), PERCENTILES),
                }
            sweep_any = (frame["sweep_long"] | frame["sweep_short"]).to_numpy()
            cell["stop_pct_sweep"] = distribution(
                frame.loc[sweep_any, "stop_pct"].to_numpy(float), PERCENTILES)
            cell["stop_pct_all"] = distribution(
                frame["stop_pct"].to_numpy(float), PERCENTILES)
            cell["floor_binds_sweep"] = floor_binding_fraction(
                frame.loc[sweep_any, "stop_pct"].to_numpy(float))
            cell["floor_binds_all"] = floor_binding_fraction(
                frame["stop_pct"].to_numpy(float))
            cell["range_atr_all"] = distribution(
                frame["range_atr"].to_numpy(float), PERCENTILES)
            cell["n_sweep_any"] = int(sweep_any.sum())
            cells[(sym, n)] = cell
            frames[(sym, n)] = frame
    return {"cells": cells, "frames": frames, "windows": windows}
