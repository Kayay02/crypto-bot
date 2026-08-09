"""Does the 1R.5 "reversal breakout" population exist at 1h? -- Point 1 reopened.

WHAT IS BEING ASKED. Point 1R.5 removed `rsi_upper` on guard-rail grounds and
left `rsi_lower` as a filter meant to reject breakouts firing without momentum
confirmation. Point 3's structural pass found ZERO rejections in 11,711 breakout
bars at 15m over 2022-23, with a minimum RSI of 54.18 on long breakout bars. The
filter was inert because the population it targets was empty, so the closing
record classified the hypothesis as UNEXERCISED, NOT REFUTED.

THE CLAIM UNDER TEST. That emptiness is STRUCTURAL, not a fact about 15m. A
Donchian-N breakout means price just made an N-bar high; RSI(14) measures recent
gains against recent losses; making an N-bar high entails recent gains having
dominated. Both indicators are defined in BAR units, so the relationship should
be scale-invariant and the population equally empty at 1h. 1h is the timeframe
selected by the rule frozen at 96c96cf (report 19). 15m is carried as the
CONTROL, because a measurement that finds nothing at 1h is uninterpretable
unless the same code reproduces the 15m result it is being compared against.

THE POPULATION IS DELIBERATELY BROADER THAN POINT 3'S. Point 3 measured the
engine's trend AND Donchian conditions together (EMA20 > EMA50 and close above
the channel). This measures the Donchian condition ALONE. Dropping the trend
filter can only ADMIT bars, never remove them, and the bars it admits are
exactly the ones most likely to carry a depressed RSI -- breakouts against the
prevailing trend. Measuring the narrower population would be assuming the
answer. `reconcile_point_3` re-applies the trend filter on the 15m control so
the two populations can be compared directly.

THE FIREWALL IS RE-ARMED. Signal counts, pass rates and indicator distributions
are explicitly permitted pre-firewall quantities. No trade is simulated: no
entry is taken, no exit is computed, no position is sized. `src/engine/simulate`
is not imported. A test walks this module's AST and refuses any performance name
as an identifier or a string literal.

THE HOLDOUT IS SEALED. The window is 2022-01-01 to 2024-12-31, inherited whole
from `src/timeframe/resample.py` rather than restated here -- there is one
window constant in the project and this module does not get its own. Every frame
this module produces passes back through `resample.assert_sealed` on the way
out.

NO OPEN. `open_synth` is dropped at the load boundary by the loader this module
reuses. Nothing here reads or reconstructs an open.
"""

import os
import sys

import numpy as np
import pandas as pd

from src.timeframe import resample as rs

# The engine's own Donchian channel and EMA. This step tests the POINT 4
# OPERATIONALISATION, so it must use the same channel Point 4 used -- a second
# implementation that happened to agree would prove only that it shared an
# author's assumptions. Imported the way src/analysis/structural_pass.py already
# imports it; src/engine is not a package.
sys.path.insert(0, os.path.join(rs.ROOT, "src", "engine"))

import signals  # noqa: E402


# ---------------------------------------------------------------------------
# FIXED BEFORE THE MEASUREMENT. Not swept, not tuned, not chosen in light of a
# number computed below.
# ---------------------------------------------------------------------------

RSI_PERIOD = 14
DONCHIAN_PERIOD = 20
"""Point 4's periods, unchanged. This is a test OF that operationalisation, so
they are transcribed rather than selected, and a test pins both."""

WARMUP_STABILISATION_BARS = 100
"""Bars discarded BEYOND the RSI seed, so the seed cannot move the answer.

Report 19's ATR convention, applied unchanged to RSI. Wilder's recursion is
avg_i = avg_{i-1} * (n-1)/n + x_i / n, so the seed's weight after k further bars
is (13/14)^k. At k = 100 that is 6.0e-4.
"""

WARMUP_BARS = 1 + (RSI_PERIOD - 1) + WARMUP_STABILISATION_BARS
"""114 BARS DISCARDED, the same arithmetic as report 19's ATR warm-up:
1 (the first bar has no previous close, so no delta at all) + 13 (deltas before
the 14-delta seed window completes) + 100 (RSI values after the seed, discarded
for stabilisation). The first RSI lands ON the 14th delta, so counting the seed
as a further 14 would double-count that bar -- it is already the first of the
100. Donchian's own 20-bar warm-up is strictly inside this and never binds.
"""

NEGLIGIBLE_RSI_LEVEL = 50.0
NEGLIGIBLE_MAX_PCT = 1.0
"""THE NEGLIGIBILITY THRESHOLD, FIXED BEFORE THE MEASUREMENT.

"Negligible" means: fewer than 1% of long breakout bars below RSI 50, on ALL
THREE symbols. Written here as a named constant, and stated in the report as
having been fixed first, because a threshold chosen after seeing the
distribution is not a threshold.
"""

RSI_LOWER_CANDIDATES = (40, 45, 50, 55, 60)
RSI_UPPER_CANDIDATES = (60, 55, 50, 45, 40)
"""Candidate filter levels for the rejection-rate table. The short list is the
long list mirrored about 50, so the two directions are asked the same question.
"""

TIMEFRAMES = ("1h", "15m")
"""1h is the selected timeframe; 15m is the control. Finest-first ordering is
not meaningful here and is not used."""

PERCENTILES = (1, 5, 10, 25, 50, 75, 90)

LONG, SHORT = "long", "short"

STRUCTURAL = "STRUCTURAL"
SCALE_DEPENDENT = "SCALE-DEPENDENT"

#: Point 3's window, for the overlapping-period figure. 2024-01-01T00:00:00Z.
POINT_3_END_MS = 1_704_067_200_000

#: Point 3's headline numbers, quoted from report 07 section 5.7 for comparison.
POINT_3_MIN_RSI_LONG = {"BTCUSDT": 54.18, "ETHUSDT": 54.56, "SOLUSDT": 55.73}
POINT_3_BREAKOUT_BARS_TOTAL = 11_711


# ---------------------------------------------------------------------------
# Wilder RSI.
# ---------------------------------------------------------------------------

def _rsi_point(avg_gain, avg_loss):
    """RSI = 100 - 100 / (1 + avg_gain/avg_loss), with the zero-loss branch.

    `avg_loss == 0` means no down move survives in the smoothed window, which
    is RSI 100 by definition and is the branch the engine's `rsi_wilder` takes.
    Followed here rather than improved on, because a different convention on a
    boundary case is exactly how two implementations of the same indicator stop
    being comparable. The sub-case where avg_gain is ALSO zero -- a perfectly
    flat 14-bar stretch -- inherits 100 from the same branch; it does not occur
    on any bar in this window and the count is reported.
    """
    if avg_loss == 0.0:
        return 100.0
    return 100.0 - 100.0 / (1.0 + avg_gain / avg_loss)


def wilder_rsi(close, period=RSI_PERIOD):
    """Wilder's RSI on close, seeded with the SIMPLE MEAN of the first `period`
    gains and losses, then avg_i = (avg_{i-1} * (period - 1) + x_i) / period.

    Returns an array aligned to `close`, NaN before the seed lands. The seed
    sits on bar index `period`: delta[j] = close[j+1] - close[j] belongs to bar
    j+1, so the first `period` deltas belong to bars 1..period.

    Implemented directly rather than as an EWM alpha = 1/period, which seeds
    differently and would not reproduce a hand-computed value. Report 19's ATR
    uses the same construction for the same reason. The engine's `rsi_wilder`
    IS the EWM form; `rsi_convention_gap` measures how far apart the two land
    after the warm-up discard, and the answer is reported rather than assumed.
    """
    c = np.asarray(close, dtype=float)
    out = np.full(len(c), np.nan, dtype=float)
    if len(c) <= period:
        return out
    delta = np.diff(c)
    gain = np.where(delta > 0.0, delta, 0.0)
    loss = np.where(delta < 0.0, -delta, 0.0)
    avg_gain = float(gain[:period].mean())
    avg_loss = float(loss[:period].mean())
    out[period] = _rsi_point(avg_gain, avg_loss)
    for j in range(period, len(delta)):
        avg_gain = (avg_gain * (period - 1) + gain[j]) / period
        avg_loss = (avg_loss * (period - 1) + loss[j]) / period
        out[j + 1] = _rsi_point(avg_gain, avg_loss)
    return out


def rsi_convention_gap(close, period=RSI_PERIOD, warmup=WARMUP_BARS):
    """Max |this module's RSI - the engine's RSI| after the warm-up discard.

    Not a correctness check -- correctness is established against hand-computed
    arithmetic. This measures whether the seeding difference between the two
    conventions is still visible where the figures are actually read.
    """
    mine = wilder_rsi(close, period)[warmup:]
    theirs = signals.rsi_wilder(np.asarray(close, dtype=float), period)[warmup:]
    ok = np.isfinite(mine) & np.isfinite(theirs)
    if not ok.any():
        return float("nan")
    return float(np.max(np.abs(mine[ok] - theirs[ok])))


# ---------------------------------------------------------------------------
# Donchian breakouts.
# ---------------------------------------------------------------------------

#: The engine's channel, re-exported so this module has no second copy of it.
donchian_prior = signals.donchian_prior


def breakout_masks(high, low, close, period=DONCHIAN_PERIOD):
    """LONG and SHORT Donchian-`period` breakout masks.

    THE EXCLUSION CONVENTION, STATED ONCE:

        upper[T] = max(high[T-period] .. high[T-1])   -- the current bar's own
        lower[T] = min(low[T-period]  .. low[T-1])       high and low are NOT in
                                                         its own window

        LONG breakout  at T : close[T] > upper[T]
        SHORT breakout at T : close[T] < lower[T]

    `signals.donchian_prior` implements it as `rolling(period).max().shift(1)`,
    so the first defined value is at index `period`, not `period - 1`.

    AN OFF-BY-ONE HERE DOES NOT RAISE, IT REDEFINES THE POPULATION. Including
    the current bar makes `close > max(high)` nearly unsatisfiable -- close is
    bounded above by its own high -- and would empty the population silently,
    which is the very answer this step is trying to establish. Dropping the
    shift entirely makes it trivially satisfiable instead. A test asserts the
    window contents directly and fails under either.

    No trend, RVOL, vwap or RSI term enters here: RSI is the quantity being
    measured against this population, and conditioning the population on it
    would be assuming the answer.
    """
    upper, lower = donchian_prior(high, low, period)
    close = np.asarray(close, dtype=float)
    ok_up = np.isfinite(upper)
    ok_dn = np.isfinite(lower)
    return ((close > upper) & ok_up, (close < lower) & ok_dn)


# ---------------------------------------------------------------------------
# The measurement frame.
# ---------------------------------------------------------------------------

def analysis_frame(bars, rsi_period=RSI_PERIOD, donchian=DONCHIAN_PERIOD,
                   warmup=WARMUP_BARS):
    """Attach RSI and both breakout masks, then discard the warm-up.

    ORDER MATTERS. Indicators are computed on the FULL bar frame and the
    warm-up is trimmed afterwards, so no rolling window is starved at the seam.
    Trimming first would silently shorten every lookback that straddles it.

    Causality is unaffected by the trim: RSI and the prior-bar Donchian channel
    at bar T are functions of bars <= T only, so a bar's indicator values do not
    depend on what comes after it -- which is what makes the sub-period
    restriction in `reconcile_point_3` equivalent to having loaded that
    sub-period alone.
    """
    high = bars["high"].to_numpy(float)
    low = bars["low"].to_numpy(float)
    close = bars["close"].to_numpy(float)
    upper, lower = donchian_prior(high, low, donchian)
    brk_up, brk_dn = breakout_masks(high, low, close, donchian)
    out = pd.DataFrame({
        "ts": bars["ts"].to_numpy(),
        "high": high, "low": low, "close": close,
        "rsi": wilder_rsi(close, rsi_period),
        "donchian_upper": upper, "donchian_lower": lower,
        "breakout_long": brk_up, "breakout_short": brk_dn,
    })
    out = out.iloc[warmup:].reset_index(drop=True)
    return rs.assert_sealed(out, "analysis_frame")


def distribution(values, percentiles=PERCENTILES):
    """MIN, the requested percentiles, MAX and the count they rest on."""
    x = np.asarray(values, dtype=float)
    x = x[np.isfinite(x)]
    out = {"n": int(len(x))}
    if not len(x):
        out["min"] = out["max"] = float("nan")
        for p in percentiles:
            out["p%d" % p] = float("nan")
        return out
    out["min"] = float(x.min())
    out["max"] = float(x.max())
    for p in percentiles:
        out["p%d" % p] = float(np.percentile(x, p))
    return out


def count_below(values, level=NEGLIGIBLE_RSI_LEVEL):
    x = np.asarray(values, dtype=float)
    return int(np.sum(x[np.isfinite(x)] < level))


def count_above(values, level=NEGLIGIBLE_RSI_LEVEL):
    x = np.asarray(values, dtype=float)
    return int(np.sum(x[np.isfinite(x)] > level))


def rejection_table(values, thresholds, direction):
    """Bars a candidate filter WOULD REJECT, as a count and as a percentage.

    LONG: `rsi_lower` passes a bar when rsi >= threshold, so it REJECTS
    rsi < threshold. SHORT: the mirrored `rsi_upper` passes rsi <= threshold and
    REJECTS rsi > threshold.

    STRICTNESS. The boundary is stated so it is not left to the reader, but it
    cannot matter at the resolution of this measurement: exact equality with an
    integer threshold on a smoothed continuous quantity is a measure-zero event,
    and `n_exactly_at` reports how many times it actually happens.

    THIS IS A PASS-RATE MEASUREMENT AND NOTHING MORE. Whether a rejected bar
    would have been a good trade is not asked, not computed and not estimable
    from anything returned here.
    """
    x = np.asarray(values, dtype=float)
    x = x[np.isfinite(x)]
    n = int(len(x))
    rows = []
    for t in thresholds:
        if direction == LONG:
            rejected = int(np.sum(x < t))
        elif direction == SHORT:
            rejected = int(np.sum(x > t))
        else:
            raise ValueError("direction must be %r or %r, got %r"
                             % (LONG, SHORT, direction))
        rows.append({
            "threshold": t,
            "rejected": rejected,
            "rejected_pct": (100.0 * rejected / n) if n else float("nan"),
            "n_exactly_at": int(np.sum(x == t)),
            "n": n,
        })
    return rows


# ---------------------------------------------------------------------------
# The verdict.
# ---------------------------------------------------------------------------

def is_negligible(pct_below, max_pct=NEGLIGIBLE_MAX_PCT):
    """Fewer than `max_pct` percent of long breakout bars below RSI 50.

    THE DIRECTION IS THE EASY THING TO INVERT. A SMALL percentage is the empty
    population -- the hypothesis stays unexercised. A LARGE percentage is the
    live finding. Reading the comparison the other way round flips STRUCTURAL
    and SCALE-DEPENDENT while leaving every number in every table untouched,
    and the report would then state the opposite conclusion over a correct set
    of figures. A planted mutation inverts exactly this and a test catches it.

    Strict: exactly 1.00% is NOT negligible. "Fewer than 1%" was fixed before
    the measurement and is read as written.
    """
    if not np.isfinite(pct_below):
        raise ValueError("pct_below must be finite, got %r" % (pct_below,))
    return bool(pct_below < max_pct)


def verdict(pct_below_by_cell, max_pct=NEGLIGIBLE_MAX_PCT):
    """STRUCTURAL only if EVERY cell is negligible. No partial pass.

    `pct_below_by_cell` maps (symbol, timeframe) -> percent of long breakout
    bars below RSI 50. STRUCTURAL means the entailment held everywhere it was
    looked for; a single symbol-timeframe carrying a real low-RSI population is
    enough to make the emptiness a fact about where it was measured rather than
    a property of the indicators.
    """
    if not pct_below_by_cell:
        raise ValueError("no cells to adjudicate")
    ok = all(is_negligible(v, max_pct) for v in pct_below_by_cell.values())
    return STRUCTURAL if ok else SCALE_DEPENDENT


# ---------------------------------------------------------------------------
# Point 3 reconciliation, on the 15m control only.
# ---------------------------------------------------------------------------

def reconcile_point_3(frame, ema_fast=20, ema_slow=50, end_ms=POINT_3_END_MS):
    """Re-apply Point 3's trend filter and window to the 15m control frame.

    Point 3's breakout population was the engine's trend AND Donchian
    conditions over 2022-2023. This module's population is Donchian alone over
    2022-2024, so the two are not the same set and are not expected to agree by
    default. This narrows one to the other so the difference is a stated
    reconciliation rather than an unexplained discrepancy.

    Two residual differences remain and are not closed: this module discards
    114 warm-up bars where Point 3 discarded about 50, so roughly 64 bars at the
    very start of 2022 are absent here; and RSI is Wilder-seeded here against
    the engine's EWM seeding, a gap `rsi_convention_gap` quantifies.
    """
    ema_f = signals.ema(frame["close"].to_numpy(float), ema_fast)
    ema_s = signals.ema(frame["close"].to_numpy(float), ema_slow)
    in_window = frame["ts"].to_numpy() < end_ms
    trend_up = ema_f > ema_s
    trend_dn = ema_f < ema_s
    long_mask = frame["breakout_long"].to_numpy() & trend_up & in_window
    short_mask = frame["breakout_short"].to_numpy() & trend_dn & in_window
    rsi = frame["rsi"].to_numpy(float)
    return {
        "n_long": int(long_mask.sum()),
        "n_short": int(short_mask.sum()),
        "min_rsi_long": float(np.nanmin(rsi[long_mask])) if long_mask.any()
                        else float("nan"),
        "p1_rsi_long": float(np.percentile(rsi[long_mask], 1))
                       if long_mask.any() else float("nan"),
        "max_rsi_short": float(np.nanmax(rsi[short_mask])) if short_mask.any()
                         else float("nan"),
        "p99_rsi_short": float(np.percentile(rsi[short_mask], 99))
                         if short_mask.any() else float("nan"),
    }


def restrict(frame, end_ms=POINT_3_END_MS):
    """The Point 3 sub-period of a frame, Donchian-only population retained."""
    return frame[frame["ts"].to_numpy() < end_ms].reset_index(drop=True)


# ---------------------------------------------------------------------------
# The whole pass.
# ---------------------------------------------------------------------------

def profile(symbols=rs.SYMBOLS, timeframes=TIMEFRAMES, derived_dir=rs.DERIVED,
            progress=None):
    """Every symbol x timeframe cell. Returns a dict of measurement blocks."""
    cells, bucket_stats, frames = {}, {}, {}
    for tf in timeframes:
        for sym in symbols:
            bars, st = rs.build(sym, tf, derived_dir=derived_dir)
            frame = analysis_frame(bars)
            rsi = frame["rsi"].to_numpy(float)
            lmask = frame["breakout_long"].to_numpy()
            smask = frame["breakout_short"].to_numpy()
            n_long = int(lmask.sum())
            below = count_below(rsi[lmask])
            above = count_above(rsi[smask])
            cell = {
                "symbol": sym,
                "timeframe": tf,
                "bars_formed": int(len(bars)),
                "bars_analysed": int(len(frame)),
                "n_long": n_long,
                "n_short": int(smask.sum()),
                "dist_long": distribution(rsi[lmask]),
                "dist_short": distribution(rsi[smask]),
                "dist_all": distribution(rsi),
                "n_below_50_long": below,
                "pct_below_50_long": (100.0 * below / n_long) if n_long
                                     else float("nan"),
                "n_above_50_short": above,
                "pct_above_50_short": (100.0 * above / int(smask.sum()))
                                      if smask.any() else float("nan"),
                "reject_long": rejection_table(rsi[lmask], RSI_LOWER_CANDIDATES,
                                               LONG),
                "reject_short": rejection_table(rsi[smask], RSI_UPPER_CANDIDATES,
                                                SHORT),
                "convention_gap": rsi_convention_gap(
                    bars["close"].to_numpy(float)),
                "n_rsi_exactly_100": int(np.sum(rsi == 100.0)),
                "first_ts": int(frame["ts"].min()) if len(frame) else None,
                "last_ts": int(frame["ts"].max()) if len(frame) else None,
            }
            cells[(sym, tf)] = cell
            bucket_stats[(sym, tf)] = st
            frames[(sym, tf)] = frame
            if progress:
                progress(sym, tf, cell, st)
    return {"cells": cells, "bucket_stats": bucket_stats, "frames": frames}


def adjudicate(cells, symbols=rs.SYMBOLS, timeframes=TIMEFRAMES):
    """The pre-registered threshold applied to the completed table."""
    pct = {(s, tf): cells[(s, tf)]["pct_below_50_long"]
           for tf in timeframes for s in symbols}
    per_cell = {k: is_negligible(v) for k, v in pct.items()}
    return {"pct_below_50_long": pct, "negligible": per_cell,
            "verdict": verdict(pct)}
