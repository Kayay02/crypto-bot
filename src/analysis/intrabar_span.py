"""Could one 1h bar contain both a trade's stop and its target?

WHAT IS BEING ASKED. The frozen strategy exits at a stop or at a 1:1.5 target.
If both levels lie inside one 1h bar, NO 1h DATA CAN SAY WHICH WAS REACHED
FIRST, and the trade is decided by a convention rather than by evidence.
Evaluating exits on 1m would nearly eliminate the ambiguity but requires closing
the 1m holdout seal gap first, which is the largest single piece of work in
Point 5.3. THIS STEP MEASURES THE EXPOSURE SO THE CHOICE RESTS ON A NUMBER.

THIS IS A DISTRIBUTION OVER BARS. IT NEVER PAIRS A BAR WITH A TRADE. No
position, entry, exit or trade object is constructed anywhere; no level is
compared against any bar to ask whether it was reached; no outcome is evaluated.
The measurement is: how often is a bar's RANGE larger than the price distance
between a stop and a target that a trade open on that bar could have carried.
That is geometry over bar ranges and nothing else, and a test asserts the module
contains no identifier or string naming a touch, a reach, a crossing or an exit
reason.

THE SPAN IS DERIVED FROM THE ENGINE, NOT INHERITED. The distance between stop
and target is NOT 2.5 x the stop distance: cost-inclusive sizing solves the
target NET of costs and places it FURTHER OUT than 1.5 x the stop distance
(amendment 1 section 5). The naive form is reported alongside so the gap is
visible, and it is the naive form that is the looser bound -- a narrower span
counts MORE bars, so the naive threshold OVERSTATES the exposure and the derived
one is the honest figure.

TWO DERIVATIONS, REQUIRED TO AGREE. The span is derived analytically from the
`CostConfig` fields AND numerically by calling the engine's own target solver on
SYNTHETIC reference inputs -- a handful of hand-chosen (entry, ATR) pairs. THE
SOLVER IS NEVER CALLED ON A REAL BAR: the per-bar sweep uses the analytic form
exclusively, which is also the marginally narrower of the two because it carries
no tick rounding, and tick rounding is always AWAY from the position.

WHICH ATR, WHICH IS THE PART THAT IS EASY TO GET WRONG. The stop is set from the
ATR at the ENTRY bar, which may be up to 24 bars before the bar being tested,
and ATR moves in between. Two ratios are computed per bar:

    (a) range[t] / ATR[t]                       the own-bar ratio
    (b) range[t] / min(ATR[t-24] .. ATR[t-1])   the worst case over every bar
                                                that could have been the entry

(b) IS THE DECISION-RELEVANT ONE. The smallest ATR in the window gives the
tightest possible stop and therefore the narrowest possible span. (a) IS NOT
CONSERVATIVE IN RISING VOLATILITY and must not drive the conclusion.

ONLY THE ATR TERM OF THE STOP IS USED. The frozen stop is
max(2.25 x ATR, 1.50% of entry); the floor can only WIDEN the stop and therefore
only widen the span, so ignoring it counts MORE bars. That is the conservative
direction and it is deliberate.

NO 1m DATA IS READ. Not one bar. The 1m loading path carries an unclosed holdout
seal gap and closing it is a separate, later step. This module reads the derived
1h series only, and a test asserts no 1m path is reachable from it.

THE HOLDOUT IS SEALED. The window is inherited whole from `resample.py`; this
module defines no window constant of its own and a test asserts it defines none.

GAP RISK IS OUT OF SCOPE AND CANNOT BE MEASURED HERE. This assumes fills occur
AT the stop or target price. A bar OPENING beyond a level would fill worse, and
Bitget's `open` field is synthesised from the carried-forward previous close --
renamed `open_synth` in the derived layer and dropped at every load boundary --
so gaps are invisible in this data BY CONSTRUCTION. Recorded as a named
limitation for 5.3.2, not attempted.
"""

import os
import sys

import numpy as np
import pandas as pd

from src.analysis import exposure_profile as ep
from src.analysis import sweep_population as sp
from src.timeframe import resample as rs

# The engine's cost model. Used ONLY for the synthetic reference cross-check in
# `reference_span_from_engine`; the per-bar sweep never calls it.
sys.path.insert(0, os.path.join(rs.ROOT, "src", "engine"))

import costs  # noqa: E402


# ---------------------------------------------------------------------------
# FROZEN INPUTS. Transcribed from upstream, not chosen here.
# ---------------------------------------------------------------------------

TIMEFRAME = sp.TIMEFRAME
ATR_PERIOD = sp.ATR_PERIOD
STOP_ATR_MULT = sp.STOP_ATR_MULT
STOP_FLOOR_PCT = sp.STOP_FLOOR_PCT
WARMUP_BARS = sp.WARMUP_BARS
LONG, SHORT = sp.LONG, sp.SHORT

MAX_HOLD_BARS = 24
"""The longest a position can be open, from report 24 section 5.2: the hold is
17-24 hours, so a position open on bar t entered on one of bars t-24 .. t-1.
That window is what ratio (b) minimises the ATR over."""

MIN_HOLD_BARS = 17

HOLD_HISTOGRAM = {17: 1493, 18: 1431, 19: 1451, 20: 1226,
                  21: 1391, 22: 1368, 23: 1592, 24: 1432}
"""Report 24 section 5.2's measured hold distribution over all 11,384 positions.
Transcribed, not recomputed -- no position is constructed here."""

TARGET_R_MULTIPLE = 1.5
"""THE FROZEN REWARD-TO-RISK, thesis section 5.2: 1 : 1.5, solved NET of costs.

TRANSCRIBED FROM THE THESIS AND SUPPLIED EXPLICITLY, BECAUSE THE ENGINE'S
DEFAULT IS 2.0, NOT 1.5. `CostConfig.target_r_multiple` defaults to Point 4's
1:2 and amendment 1 section 3 records the difference by name: "the engine's
default target_r_multiple is 2.0 (Point 4's 1:2) ... The thesis sets 1.5. That
is a configuration value, not a code path."

A CONFIGURATION VALUE THAT NOBODY SUPPLIES IS A CHOSEN VALUE NOBODY CHOSE, which
is the failure Point 3R removed the other defaults to prevent. Taking the
default here would have widened every span by ~20% and UNDERSTATED the exposure
this step exists to bound -- the unsafe direction. A test pins this at 1.5 and
pins that it differs from the engine default."""

NAIVE_SPAN_MULT = 1.0 + TARGET_R_MULTIPLE
"""2.5: stop distance plus 1.5 x stop distance, as a multiple of the stop
distance. THE NAIVE FORM. It ignores that the target is solved NET of costs and
therefore sits further out than 1.5 x the stop distance. Reported for comparison
only."""

NAIVE_ATR_THRESHOLD = NAIVE_SPAN_MULT * STOP_ATR_MULT
"""5.625. The naive threshold on range/ATR. A NARROWER span than the truth, so
it counts MORE bars and overstates the exposure."""

REFERENCE_STOP_FRACTION = STOP_FLOOR_PCT / 100.0
"""The stop width at which the single-number span multiplier is quoted: the
frozen 1.50% floor, which is the binding case on nearly half of BTCUSDT's
signals. STATED, because the multiplier is NOT constant -- it varies with the
stop width, and the per-bar sweep uses the exact per-bar value rather than this
one."""

PERCENTILES = (50, 90, 95, 99, 99.9)

#: Hand-chosen (entry, ATR) pairs for the synthetic reference cross-check.
#: SYNTHETIC ONLY. None of these is a real bar, a real signal or a real level.
REFERENCE_INPUTS = ((30_000.0, 200.0), (30_000.0, 300.0), (2_000.0, 15.0),
                    (2_000.0, 30.0), (100.0, 1.0), (100.0, 2.5))


def cost_config(**kw):
    """Report 24's config, reused rather than redefined -- WITH RR SET TO 1.5.

    One config object in the project, not two: the fee, slippage and haircut
    fields are `exposure_profile`'s, unchanged, so the cost model here is the
    one reports 24 and 26 sized against.

    `target_r_multiple` IS OVERRIDDEN TO THE THESIS'S 1.5. Reports 24 and 26
    called only `position_size`, which never reads that field, so their figures
    are unaffected by the engine's 2.0 default. THIS report solves a TARGET, so
    it is the first measurement in the project for which the field is
    load-bearing, and it is supplied rather than inherited.
    """
    kw.setdefault("target_r_multiple", TARGET_R_MULTIPLE)
    return ep.cost_config(**kw)


# ---------------------------------------------------------------------------
# THE SPAN. Derived from the cost model, two ways.
# ---------------------------------------------------------------------------

def cost_terms(cfg, symbol):
    """(taker, maker, entry slippage, stop haircut, reward multiple), fractions."""
    return (float(cfg.taker_fee), float(cfg.maker_fee),
            float(cfg.entry_slippage_bps) / 10_000.0,
            float(cfg.haircut_bps(symbol)) / 10_000.0,
            float(cfg.target_r_multiple))


def span_fraction_analytic(stop_fraction, direction, cfg, symbol):
    """Stop-to-target distance as a fraction of ENTRY PRICE. Closed form.

    DERIVED FROM THE CostConfig FIELDS, following the engine's own algebra.
    With `s` the stop distance as a fraction of entry, `f` taker, `m` maker,
    `e` entry slippage, `h` the stop haircut and `RR` the reward multiple:

      sizing (costs.position_size), as a fraction of entry --
          LONG   d = s + f + (1-s) f + e + (1-s) h
          SHORT  d = s + f + (1+s) f + e + (1+s) h
      the risk unit divided by d is the quantity, so RR x R / q = RR x d x P.

      target (costs.solve_price_for_net, exiting MAKER) --
          LONG   X_t = ( RR d + 1 + f ) / (1 - m)          x P
          SHORT  X_t = ( 1 - f - RR d ) / (1 + m)          x P

      span = X_t - X_stop for a long, X_stop - X_t for a short, with
      X_stop = (1 -/+ s) x P.

    THE MAKER EXIT MATTERS. The target leg is solved against `maker_fee`, not
    `taker_fee`, so the span is narrower than a round-trip-taker model would
    give. Using the wrong leg here would widen the span and UNDERSTATE the
    exposure, which is the unsafe direction.
    """
    s = np.asarray(stop_fraction, dtype=float)
    f, m, e, h, rr = cost_terms(cfg, symbol)
    if direction == LONG:
        d = s + f + (1.0 - s) * f + e + (1.0 - s) * h
        target = (rr * d + 1.0 + f) / (1.0 - m)
        return target - (1.0 - s)
    if direction == SHORT:
        d = s + f + (1.0 + s) * f + e + (1.0 + s) * h
        target = (1.0 - f - rr * d) / (1.0 + m)
        return (1.0 + s) - target
    raise ValueError("direction must be %r or %r, got %r"
                     % (LONG, SHORT, direction))


def span_multiplier_analytic(stop_fraction, direction, cfg, symbol):
    """`k`: the span as a multiple of the STOP DISTANCE.

    NOT A CONSTANT. `k = 2.5 x (1 + cost/s)` to first order, so it FALLS as the
    stop widens. A single quoted `k` is therefore a reading at a stated stop
    width and the per-bar sweep does not use one -- it evaluates the span at
    each bar's own stop width. `REFERENCE_STOP_FRACTION` is the width the
    reported figure is quoted at.
    """
    s = np.asarray(stop_fraction, dtype=float)
    return span_fraction_analytic(s, direction, cfg, symbol) / s


def reference_span_from_engine(entry, atr, direction, cfg, symbol, tick):
    """The same span, computed by CALLING THE ENGINE. Synthetic inputs only.

    NEVER CALLED ON A REAL BAR, A REAL SIGNAL OR A REAL LEVEL. Its only callers
    are `reference_table` and the tests, both on `REFERENCE_INPUTS`. The per-bar
    sweep uses the analytic form exclusively -- a test asserts the sweep's own
    code calls nothing from `costs`.

    `position_size` and `solve_target` are the engine's, unmodified. The tick is
    supplied fine so that the solver's rounding -- always AWAY from the position,
    so always widening the span -- cannot mask a disagreement between the two
    derivations.
    """
    stop_distance = STOP_ATR_MULT * float(atr)
    stop = entry - stop_distance if direction == LONG else entry + stop_distance
    qty = costs.position_size(entry, stop, direction, cfg, symbol)
    target = costs.solve_target(entry, qty, direction, cfg, tick)
    return (target - stop) if direction == LONG else (stop - target)


def reference_table(cfg=None, symbols=rs.SYMBOLS, tick=1e-8):
    """Both derivations at every reference input, for the report's k table."""
    cfg = cost_config() if cfg is None else cfg
    rows = []
    for symbol in symbols:
        for direction in (LONG, SHORT):
            for entry, atr in REFERENCE_INPUTS:
                stop_distance = STOP_ATR_MULT * atr
                s = stop_distance / entry
                analytic = float(span_multiplier_analytic(s, direction, cfg,
                                                          symbol))
                numeric = reference_span_from_engine(
                    entry, atr, direction, cfg, symbol, tick) / stop_distance
                rows.append({
                    "symbol": symbol, "direction": direction,
                    "entry": entry, "atr": atr, "stop_fraction": s,
                    "k_analytic": analytic, "k_numeric": float(numeric),
                    "k_naive": NAIVE_SPAN_MULT,
                    "abs_error": abs(analytic - float(numeric)),
                })
    return rows


def quoted_multipliers(cfg=None, symbols=rs.SYMBOLS,
                       stop_fraction=REFERENCE_STOP_FRACTION):
    """`k` per symbol per direction at the reference stop width."""
    cfg = cost_config() if cfg is None else cfg
    return {(symbol, direction): float(span_multiplier_analytic(
                stop_fraction, direction, cfg, symbol))
            for symbol in symbols for direction in (LONG, SHORT)}


# ---------------------------------------------------------------------------
# THE PER-BAR SWEEP. Analytic span only; the engine is not called here.
# ---------------------------------------------------------------------------

def rolling_prior_min(values, window=MAX_HOLD_BARS):
    """min over the `window` bars ENDING AT t-1. The current bar is EXCLUDED.

    Same exclusion convention as the Donchian channel in report 21, and for the
    same reason: bar t cannot have been its own entry bar, because a position
    open on bar t was entered at the close of an EARLIER bar. Including bar t
    would let a bar set the stop it is then tested against.
    """
    return pd.Series(np.asarray(values, dtype=float)).rolling(
        window).min().shift(1).to_numpy()


def bar_frame(bars, cfg=None, symbol=None, warmup=WARMUP_BARS,
              window=MAX_HOLD_BARS):
    """Per-bar ranges, ATR, both ratios, and the narrowest admissible span.

    THE COLUMNS:

      range               high - low, in price units
      atr                 Wilder ATR(14), the project's own implementation
      ratio_own           range / atr[t]                       -- ratio (a)
      ratio_prior_min     range / min(atr[t-24 .. t-1])        -- ratio (b)
      span_long/short     the span a position entered at THIS bar would carry
      min_span            the NARROWEST span over bars t-24 .. t-1, both
                          directions -- the tightest geometry any position open
                          on bar t could have

    `min_span` IS THE DECISION-RELEVANT COLUMN. It is computed in PRICE units
    from each candidate entry bar's own close and ATR, so it needs no single
    span multiplier and inherits none of the error in quoting one.
    """
    cfg = cost_config() if cfg is None else cfg
    if symbol is None:
        raise ValueError("symbol is required: the haircut is per symbol")

    high = bars["high"].to_numpy(float)
    low = bars["low"].to_numpy(float)
    close = bars["close"].to_numpy(float)
    atr = sp.atr_series(bars, ATR_PERIOD)

    with np.errstate(divide="ignore", invalid="ignore"):
        safe_atr = np.where(atr > 0.0, atr, np.nan)
        stop_distance = STOP_ATR_MULT * safe_atr
        stop_fraction = stop_distance / close
        span_long = span_fraction_analytic(stop_fraction, LONG, cfg,
                                           symbol) * close
        span_short = span_fraction_analytic(stop_fraction, SHORT, cfg,
                                            symbol) * close
        narrower = np.minimum(span_long, span_short)
        bar_range = high - low
        out = pd.DataFrame({
            "ts": bars["ts"].to_numpy(),
            "high": high, "low": low, "close": close, "atr": atr,
            "range": bar_range,
            "ratio_own": bar_range / safe_atr,
            "ratio_prior_min": bar_range / rolling_prior_min(safe_atr, window),
            "span_long": span_long,
            "span_short": span_short,
            "min_span": rolling_prior_min(narrower, window),
        })
    out = out.iloc[warmup:].reset_index(drop=True)
    return rs.assert_sealed(out, "bar_frame(%s)" % symbol)


def exceedance(frame, column="min_span"):
    """Bars whose RANGE is larger than the narrowest admissible span.

    THE CRITERION, STATED ONCE: `range[t] > min_span[t]`. A bar this large COULD
    contain both levels. It says nothing about whether it DID -- a bar large
    enough is usually not POSITIONED to contain them -- which is why every figure
    downstream is an upper bound and is labelled as one.
    """
    r = frame["range"].to_numpy(float)
    limit = frame[column].to_numpy(float)
    ok = np.isfinite(r) & np.isfinite(limit)
    mask = ok & (r > limit)
    return {
        "n_bars": int(ok.sum()),
        "n_exceeding": int(mask.sum()),
        "fraction": (float(mask.sum()) / int(ok.sum())) if int(ok.sum())
                    else float("nan"),
        "mask": mask,
    }


def ratio_exceedance(frame, column, threshold):
    """The same count against a fixed ratio threshold, for comparability."""
    x = frame[column].to_numpy(float)
    ok = np.isfinite(x)
    mask = ok & (x > threshold)
    return {
        "n_bars": int(ok.sum()),
        "n_exceeding": int(mask.sum()),
        "fraction": (float(mask.sum()) / int(ok.sum())) if int(ok.sum())
                    else float("nan"),
        "threshold": float(threshold),
        "mask": mask,
    }


def summary(values, percentiles=PERCENTILES):
    """min, the percentiles, max, mean and n."""
    x = np.asarray(values, dtype=float)
    x = x[np.isfinite(x)]
    out = {"n": int(len(x))}
    if not len(x):
        out["min"] = out["max"] = out["mean"] = float("nan")
        for p in percentiles:
            out["p%s" % p] = float("nan")
        return out
    out["min"] = float(x.min())
    out["max"] = float(x.max())
    out["mean"] = float(x.mean())
    for p in percentiles:
        out["p%s" % p] = float(np.percentile(x, p))
    return out


# ---------------------------------------------------------------------------
# PER-BAR TO PER-TRADE.
# ---------------------------------------------------------------------------

def per_trade_bound(p_bar, histogram=None, max_hold=MAX_HOLD_BARS):
    """Convert a per-bar fraction into a per-trade upper bound.

    A UNION BOUND, AND IT IS LOOSE ON PURPOSE. A trade open for `n` bars is
    exposed on `n` bars, so the chance that at least one of them is large enough
    is AT MOST `n x p`. That assumes independence across a trade's bars, which
    is false -- large bars cluster -- and it assumes every large bar resolves the
    trade ambiguously, which is also false. Both errors run the same way: the
    true figure is BELOW this bound.

    Two forms, both reported:
      weighted   -- report 24's measured hold histogram, bar-count weighted
      max_hold   -- every trade held the full 24 bars, the strictest form
    """
    histogram = HOLD_HISTOGRAM if histogram is None else histogram
    total = sum(histogram.values())
    if total <= 0:
        raise ValueError("the hold histogram is empty")
    mean_bars = sum(h * n for h, n in histogram.items()) / total
    return {
        "p_bar": float(p_bar),
        "mean_hold_bars": float(mean_bars),
        "weighted": float(p_bar) * float(mean_bars),
        "max_hold": float(p_bar) * float(max_hold),
        "max_hold_bars": int(max_hold),
    }


# ---------------------------------------------------------------------------
# The whole pass.
# ---------------------------------------------------------------------------

def measure(symbols=rs.SYMBOLS, timeframe=TIMEFRAME, cfg=None,
            derived_dir=rs.DERIVED, max_listed=50):
    """Every figure the report states, per symbol per fold period and pooled."""
    cfg = cost_config() if cfg is None else cfg
    windows = sp.fold_windows()
    out = {
        "reference": reference_table(cfg, symbols),
        "quoted_k": quoted_multipliers(cfg, symbols),
        "naive_k": NAIVE_SPAN_MULT,
        "naive_atr_threshold": NAIVE_ATR_THRESHOLD,
        "symbols": {},
        "frames": {},
        "folds": {},
    }
    pooled_own, pooled_prior, pooled_mask, pooled_naive = [], [], [], []

    for symbol in symbols:
        bars, _ = rs.build(symbol, timeframe, derived_dir=derived_dir)
        frame = bar_frame(bars, cfg=cfg, symbol=symbol)
        out["frames"][symbol] = frame
        derived = exceedance(frame)
        naive = ratio_exceedance(frame, "ratio_prior_min",
                                 NAIVE_ATR_THRESHOLD)
        listed = frame.loc[derived["mask"], "ts"].to_numpy()
        out["symbols"][symbol] = {
            "bars": int(len(frame)),
            "ratio_own": summary(frame["ratio_own"]),
            "ratio_prior_min": summary(frame["ratio_prior_min"]),
            "derived": {k: v for k, v in derived.items() if k != "mask"},
            "naive": {k: v for k, v in naive.items() if k != "mask"},
            "exceeding_ts": ([int(t) for t in listed]
                             if len(listed) <= max_listed else None),
            "per_trade": per_trade_bound(derived["fraction"]),
            "per_trade_naive": per_trade_bound(naive["fraction"]),
        }
        pooled_own.append(frame["ratio_own"].to_numpy(float))
        pooled_prior.append(frame["ratio_prior_min"].to_numpy(float))
        pooled_mask.append(derived["mask"])
        pooled_naive.append(naive["mask"])

        out["folds"][symbol] = {}
        ts = frame["ts"].to_numpy(np.int64)
        for fold_id, period, lo, hi in windows:
            inw = (ts >= lo) & (ts <= hi)
            sub = frame.loc[inw].reset_index(drop=True)
            d = exceedance(sub)
            n = ratio_exceedance(sub, "ratio_prior_min", NAIVE_ATR_THRESHOLD)
            out["folds"][symbol][(fold_id, period)] = {
                "bars": int(inw.sum()),
                "ratio_prior_min": summary(sub["ratio_prior_min"]),
                "derived": {k: v for k, v in d.items() if k != "mask"},
                "naive": {k: v for k, v in n.items() if k != "mask"},
            }

    n_bars = sum(int(np.isfinite(a).sum()) for a in pooled_prior)
    n_exc = int(sum(int(m.sum()) for m in pooled_mask))
    n_naive = int(sum(int(m.sum()) for m in pooled_naive))
    out["pooled"] = {
        "bars": n_bars,
        "ratio_own": summary(np.concatenate(pooled_own)),
        "ratio_prior_min": summary(np.concatenate(pooled_prior)),
        "derived": {"n_bars": n_bars, "n_exceeding": n_exc,
                    "fraction": n_exc / n_bars if n_bars else float("nan")},
        "naive": {"n_bars": n_bars, "n_exceeding": n_naive,
                  "fraction": n_naive / n_bars if n_bars else float("nan"),
                  "threshold": NAIVE_ATR_THRESHOLD},
    }
    out["pooled"]["per_trade"] = per_trade_bound(
        out["pooled"]["derived"]["fraction"])
    out["pooled"]["per_trade_naive"] = per_trade_bound(
        out["pooled"]["naive"]["fraction"])
    out["windows"] = windows
    return out
