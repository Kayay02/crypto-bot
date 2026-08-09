"""ATR(14) distributions per timeframe, and the frozen rule applied to them.

THE RULE IS NOT DEFINED HERE. It is pre-registered in
`docs/handoff/19_timeframe_rule.md`, committed alone at 96c96cf before this
module existed and before any bar was read. The constants below transcribe it;
they do not get to reinterpret it, and a test pins each one.

WHAT IS BEING ASKED. Point 4 used 1.5 x ATR(14) floored at 1%, and the floor
bound 65-81% of breakout bars -- so the ATR term almost never set the stop and
the rule was a fixed-percentage stop wearing an ATR costume. A stop at the
report 18 cost floor is only OPERATIVE on a timeframe where typical bar range
is large enough that a multiplier in a sane band reaches the floor. This module
computes, per symbol per timeframe, the multiplier that would be required.

THE FIREWALL IS RE-ARMED. ATR percentiles are an explicitly permitted
pre-firewall quantity. Nothing here reads a trade outcome, and no trade is
simulated -- there is no entry rule yet to simulate. A test walks this module's
AST and refuses any performance name as an identifier or string literal.
"""

import numpy as np
import pandas as pd

from src.timeframe import resample as rs

# ---------------------------------------------------------------------------
# TRANSCRIBED FROM THE FROZEN RULE. Do not edit without amending the handoff
# document, which is itself frozen -- which means: do not edit.
# ---------------------------------------------------------------------------

COST_FLOOR_PCT = 1.50
"""The all-taker slippage-headroom floor, in PERCENT of entry.

From report 18 section 4, itself derived from COST_TOLERANCE_R = 0.11. Not a
new number and not adjustable in this step.
"""

M_MIN, M_MAX = 1.0, 3.0
"""The admissible ATR-multiplier band. A JUDGEMENT and the rule's only free
parameter: below 1.0 the stop sits inside typical bar range and is hit by
noise; above 3.0 the multiplier rather than the volatility is setting the stop.
Recorded as a judgement, not a derivation."""

ATR_PERIOD = 14

WARMUP_STABILISATION_BARS = 100
"""Bars discarded BEYOND the ATR seed, so the seed cannot move the answer.

Wilder's recursion is ATR_i = ATR_{i-1} * (n-1)/n + TR_i / n, so the seed's
weight after k further bars is (13/14)^k. At k = 100 that is 6.0e-4 -- the seed
contributes under 0.06% of the reported ATR, which is far below the resolution
of any figure in report 19.

TOTAL DISCARDED IS 114 BARS: 1 (the first bar has no previous close, so no true
range) + 13 (true ranges before the seed window completes) + 100 (ATR values
after the seed, discarded for stabilisation). The first ATR lands ON the 14th
true range, so counting the seed as a further 14 would double-count that bar --
it is already the first of the 100.
"""

PERCENTILES = (10, 25, 50, 75, 90)

ADMISSIBLE, TOO_FINE, TOO_COARSE = "ADMISSIBLE", "TOO FINE", "TOO COARSE"


# ---------------------------------------------------------------------------
# Wilder ATR.
# ---------------------------------------------------------------------------

def true_range(high, low, close):
    """TR_i = max(H_i - L_i, |H_i - C_{i-1}|, |L_i - C_{i-1}|), for i >= 1.

    Returns an array of length len(high) - 1. The first bar has no previous
    close, so it has no true range at all -- it is dropped rather than given
    the H-L fallback some implementations use, because that fallback is a
    different statistic silently sharing a name.
    """
    high = np.asarray(high, dtype=float)
    low = np.asarray(low, dtype=float)
    close = np.asarray(close, dtype=float)
    if not (len(high) == len(low) == len(close)):
        raise ValueError("high, low and close must be the same length")
    if len(high) < 2:
        return np.empty(0, dtype=float)
    prev_close = close[:-1]
    h, l = high[1:], low[1:]
    return np.maximum.reduce([h - l, np.abs(h - prev_close),
                              np.abs(l - prev_close)])


def wilder_atr(tr, period=ATR_PERIOD):
    """Wilder's smoothed ATR over an array of true ranges.

    Seeded with the SIMPLE MEAN of the first `period` true ranges, which is
    Wilder's own definition, then ATR_i = (ATR_{i-1} * (period - 1) + TR_i)
    / period. Returns an array aligned to `tr` with NaN before the seed
    completes.

    Implemented directly rather than as an EWM alpha=1/period, which seeds
    differently and would not reproduce a hand-computed value.
    """
    tr = np.asarray(tr, dtype=float)
    out = np.full(len(tr), np.nan, dtype=float)
    if len(tr) < period:
        return out
    seed = float(np.mean(tr[:period]))
    out[period - 1] = seed
    prev = seed
    for i in range(period, len(tr)):
        prev = (prev * (period - 1) + tr[i]) / period
        out[i] = prev
    return out


def atr_percent(bars, period=ATR_PERIOD,
                stabilisation=WARMUP_STABILISATION_BARS):
    """ATR(14) as a PERCENT of the bar's own close, warm-up discarded.

    DENOMINATOR: the CLOSE OF THE SAME BAR the ATR is stated at. Stated here
    once and used nowhere else, so the convention cannot vary between tables.
    Close rather than an average or a midpoint because close is the price the
    next bar's entry would be referenced to, and because it is the only price
    in the frame that is not itself derived from the high and low the ATR is
    already built from.

    Returns a Series indexed to match the surviving rows of `bars`.
    """
    if len(bars) < 2:
        return pd.Series(dtype=float)
    tr = true_range(bars["high"].to_numpy(), bars["low"].to_numpy(),
                    bars["close"].to_numpy())
    atr = wilder_atr(tr, period=period)
    # tr[i] belongs to bars[i + 1]; realign to the bar frame.
    closes = bars["close"].to_numpy()[1:]
    pct = 100.0 * atr / closes
    keep = (period - 1) + stabilisation
    if keep >= len(pct):
        return pd.Series(dtype=float)
    vals = pct[keep:]
    idx = bars.index[1:][keep:]
    return pd.Series(vals, index=idx, name="atr_pct").dropna()


def distribution(series, percentiles=PERCENTILES):
    """Percentiles of an ATR% series, plus the count they are computed over."""
    s = pd.Series(series).dropna()
    out = {"n_bars": int(len(s))}
    if not len(s):
        for p in percentiles:
            out["p%d" % p] = float("nan")
        return out
    for p in percentiles:
        out["p%d" % p] = float(np.percentile(s.to_numpy(), p))
    return out


# ---------------------------------------------------------------------------
# The frozen rule.
# ---------------------------------------------------------------------------

def m_required(median_atr_pct, floor_pct=COST_FLOOR_PCT):
    """Multiplier needed to place the stop at the cost floor: floor / median."""
    if not np.isfinite(median_atr_pct) or median_atr_pct <= 0.0:
        raise ValueError("median ATR%% must be positive and finite, got %r"
                         % (median_atr_pct,))
    return floor_pct / median_atr_pct


def classify(m, m_min=M_MIN, m_max=M_MAX):
    """ADMISSIBLE / TOO FINE / TOO COARSE for one symbol-timeframe cell.

        m in [m_min, m_max]  -> ADMISSIBLE
        m > m_max            -> TOO FINE   (the multiplier would do the work:
                                            bar range is too small for the
                                            floor to be reached sanely)
        m < m_min            -> TOO COARSE (typical volatility already exceeds
                                            the floor; the floor is not binding)

    THE DIRECTION IS THE EASY THING TO INVERT AND THE HARD THING TO NOTICE.
    A large `m` means the median bar range is SMALL relative to the floor,
    which happens on FINE timeframes -- so a large m is TOO FINE, not too
    coarse. Reading it the other way round produces a table that looks
    perfectly sensible and selects the opposite end of the candidate set. A
    planted mutation inverts exactly this and a test is required to catch it.
    """
    if not np.isfinite(m):
        raise ValueError("m must be finite, got %r" % (m,))
    if m > m_max:
        return TOO_FINE
    if m < m_min:
        return TOO_COARSE
    return ADMISSIBLE


def timeframe_admissible(marks):
    """A timeframe passes only if ALL symbols are ADMISSIBLE. No partial pass."""
    marks = list(marks)
    return bool(marks) and all(mk == ADMISSIBLE for mk in marks)


def select_finest(admissible_by_tf, order=rs.TIMEFRAME_ORDER):
    """The FINEST admissible timeframe, or None.

    `order` is finest-first, so this is the first passing entry. Returning None
    rather than a fallback is deliberate: the frozen rule says that nothing
    being admissible is a FINDING, and a fallback would convert a finding into
    a silent second choice.
    """
    for tf in order:
        if admissible_by_tf.get(tf):
            return tf
    return None


# ---------------------------------------------------------------------------
# The measurement.
# ---------------------------------------------------------------------------

def profile(symbols=rs.SYMBOLS, timeframes=rs.TIMEFRAME_ORDER,
            derived_dir=rs.DERIVED, progress=None):
    """Build every symbol x timeframe cell. Returns (cells, bucket_stats).

    `cells[(symbol, timeframe)]` carries the ATR% percentiles, the bar count,
    `m_required` at the median, and the classification; plus `m_at_p25` and
    `m_at_p75`, which are INFORMATION ONLY and do not enter the test.
    """
    cells, stats = {}, {}
    for tf in timeframes:
        for sym in symbols:
            bars, st = rs.build(sym, tf, derived_dir=derived_dir)
            pct = atr_percent(bars)
            dist = distribution(pct)
            med = dist["p50"]
            cell = dict(dist)
            cell.update({
                "symbol": sym,
                "timeframe": tf,
                "m_required": m_required(med),
                "mark": classify(m_required(med)),
                # Information only -- explicitly NOT part of the rule.
                "m_at_p25": m_required(dist["p25"]),
                "m_at_p75": m_required(dist["p75"]),
                "first_ts": int(bars["ts"].min()) if len(bars) else None,
                "last_ts": int(bars["ts"].max()) if len(bars) else None,
            })
            cells[(sym, tf)] = cell
            stats[(sym, tf)] = st
            if progress:
                progress(sym, tf, cell, st)
    return cells, stats


def verdicts(cells, symbols=rs.SYMBOLS, timeframes=rs.TIMEFRAME_ORDER):
    """{timeframe: bool} admissibility, and the selected timeframe."""
    adm = {tf: timeframe_admissible(cells[(s, tf)]["mark"] for s in symbols)
           for tf in timeframes}
    return adm, select_finest(adm, order=timeframes)
