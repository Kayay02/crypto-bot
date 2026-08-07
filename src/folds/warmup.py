"""Warm-up buffer computation and SUFFICIENCY checking (§4.2).

45 calendar days of bars preceding each fold, drawn from data BEFORE the fold
and never consumed from within it. Indicators are computed continuously from
`warmup_start`; the traded population begins at `train_start`. Train and test
are contiguous, so one buffer before train_start covers both -- there is
deliberately no second buffer before test_start.

WHAT "SUFFICIENT" MEANS, AND WHY THE OBVIOUS TEST IS VACUOUS.

The naive check -- "no signal originates before train_start" -- passes whether
or not 45 days is enough, because any implementation that slices to the train
window afterwards satisfies it trivially. It tests the slice, not the buffer.

The real question is whether the buffer is long enough that indicator values
inside the fold no longer remember where computation started. That is answered
by recomputing with a LONGER buffer and requiring the values from train_start
onward to be IDENTICAL -- bit-identical, not approximately equal.

Bit-identity is the right bar, not a strict one. EMA50's memory of its seed
decays as (1 - 2/51)^n; over a 45-day buffer (4,320 bars) that is e^-172, which
is exactly zero in double precision. ATR(14) decays as (13/14)^n -> e^-320.
Donchian-20 and the 20-day slot baseline are finite windows and forget
completely once passed. So if any value differs at all, that is a finding about
the buffer, not a tolerance to be loosened.

And a sufficiency check that cannot detect an INSUFFICIENT buffer proves
nothing, so `compare_buffers` is also run against a deliberately short buffer
and required to show a difference. Four vacuous guards have been found in this
project; this is the fifth opportunity and it is taken deliberately.

FIREWALL. Indicator values, bar counts and signal COUNTS only. No trade
outcome is read and `simulate` is never imported.
"""

import datetime as dt
import os
import sys

import numpy as np
import pandas as pd

from . import schedule as sch

ROOT = sch.ROOT
sys.path.insert(0, os.path.join(ROOT, "src", "engine"))

import costs  # noqa: E402
import signals as sg  # noqa: E402

# Columns compared for sufficiency. These are exactly the indicators the entry
# rule reads after Point 3R: EMA20/EMA50 (trend), Donchian-20 (trigger),
# session-normalised RVOL (gate), plus ATR(14) which sets the stop.
INDICATOR_COLS = ("ema_fast", "ema_slow", "donchian_upper", "donchian_lower",
                  "rvol", "atr")
# Recorded on signal rows but read by no entry condition (3R). Compared and
# reported separately so it cannot quietly pass or fail with the real ones.
INFORMATIONAL_COLS = ("rsi",)

BASELINE_DAYS = 20          # §4.3 fixes this; sweep maximum is also 20
WARMUP_DAYS = sch.WARMUP_DAYS


# The four Point 3R parameters have no defaults. None of them affects any
# indicator compared here -- rvol_threshold gates which bars SIGNAL, not what
# the baseline computes -- so they are explicitly-arbitrary scaffolding, and a
# test asserts the indicator values are invariant to them.
def _cfg(baseline_days=BASELINE_DAYS, **kw):
    p = dict(stop_atr_mult=1.0, stop_max_pct=0.035, rvol_threshold=1.5,
             baseline_days=baseline_days)
    p.update(kw)
    return costs.CostConfig(**p)


def buffer_start(train_start, warmup_days=WARMUP_DAYS):
    """warmup_start = train_start minus `warmup_days` calendar days."""
    return train_start - dt.timedelta(days=warmup_days)


def buffer_bars(warmup_days=WARMUP_DAYS):
    """Nominal 15m bars in the buffer. 45 days -> 4,320 bars."""
    return warmup_days * (sch.DAY_MS // sch.BAR_15M_MS)


# ---------------------------------------------------------------------------
# indicator computation over a buffered span
# ---------------------------------------------------------------------------

def indicators_from(symbol, from_date, to_date, baseline_days=BASELINE_DAYS,
                    derived_dir=sch.DERIVED, authorised=False):
    """Every indicator, computed continuously over [from_date, to_date].

    Imported from `src/engine/signals.py`, never reimplemented, so an indicator
    means the same thing here as it does in a trade. Holdout access is refused
    unless explicitly authorised.
    """
    df = sch.load_bars(symbol, from_date, to_date, derived_dir,
                       authorised=authorised)
    if len(df) == 0:
        raise ValueError(f"{symbol}: no bars in {from_date} -> {to_date}")
    return sg.compute_indicators(df, sg.SignalParams(), baseline_days)


def indicators_with_buffer(symbol, train_start, to_date, buffer_days,
                           baseline_days=BASELINE_DAYS,
                           derived_dir=sch.DERIVED, authorised=False):
    """Indicators over the fold, computed from `buffer_days` before it.

    Returns only the rows at or after `train_start` -- the traded population.
    The buffer's whole job is to have already happened by then.
    """
    start = buffer_start(train_start, buffer_days)
    ind = indicators_from(symbol, start, to_date, baseline_days, derived_dir,
                          authorised)
    lo = sch.day_start_ms(train_start)
    return ind[ind["ts"] >= lo].reset_index(drop=True)


# ---------------------------------------------------------------------------
# the sufficiency comparison
# ---------------------------------------------------------------------------

def compare_buffers(symbol, train_start, to_date, buffer_a, buffer_b,
                    baseline_days=BASELINE_DAYS, derived_dir=sch.DERIVED,
                    cols=INDICATOR_COLS + INFORMATIONAL_COLS):
    """Per-indicator comparison of two buffer lengths over the same fold.

    Returns {col: {identical, n_compared, n_differing, max_abs_diff,
    max_rel_diff, n_nan_mismatch}}.

    NaN is compared as a VALUE, not skipped: a shorter buffer's most visible
    symptom is a column that is still NaN inside the fold (the 20-day slot
    baseline is the clearest case), and skipping NaNs would hide exactly that.
    """
    a = indicators_with_buffer(symbol, train_start, to_date, buffer_a,
                               baseline_days, derived_dir)
    b = indicators_with_buffer(symbol, train_start, to_date, buffer_b,
                               baseline_days, derived_dir)
    if not np.array_equal(a["ts"].to_numpy(), b["ts"].to_numpy()):
        raise ValueError(
            f"{symbol}: the two buffered runs cover different bars "
            f"({len(a)} vs {len(b)}); the comparison would be meaningless")

    out = {}
    for c in cols:
        x, y = a[c].to_numpy(float), b[c].to_numpy(float)
        nan_x, nan_y = np.isnan(x), np.isnan(y)
        nan_mismatch = int((nan_x ^ nan_y).sum())
        both = ~nan_x & ~nan_y
        diff = np.abs(x[both] - y[both])
        n_diff = int((diff > 0).sum())
        denom = np.maximum(np.abs(x[both]), 1e-300)
        out[c] = {
            "identical": bool(n_diff == 0 and nan_mismatch == 0),
            "n_compared": int(both.sum()),
            "n_differing": n_diff,
            "n_nan_mismatch": nan_mismatch,
            "max_abs_diff": float(diff.max()) if diff.size else 0.0,
            "max_rel_diff": float((diff / denom).max()) if diff.size else 0.0,
        }
    return out


def assert_buffer_sufficient(symbol, fold, longer_days, baseline_days=BASELINE_DAYS,
                             derived_dir=sch.DERIVED, cols=INDICATOR_COLS):
    """The 45-day buffer must give the same values as a longer one. Bit-exact.

    Raises with the offending column and the size of the discrepancy. Do not
    relax this to a tolerance: at 4,320 bars the seed's influence is e^-172,
    which is zero in double precision, so a non-zero difference means the
    buffer is not doing its job rather than that floating point is imprecise.
    """
    res = compare_buffers(symbol, fold["train_start"], fold["test_end"],
                          WARMUP_DAYS, longer_days, baseline_days, derived_dir,
                          cols=cols)
    bad = {c: r for c, r in res.items() if not r["identical"]}
    if bad:
        raise AssertionError(
            f"{symbol} fold {fold['fold_id']}: a {WARMUP_DAYS}-day buffer does "
            f"not reproduce a {longer_days}-day buffer from "
            f"{fold['train_start']} onward: {bad}")
    return res


def first_signal_ts(symbol, train_start, to_date, buffer_days=WARMUP_DAYS,
                    baseline_days=BASELINE_DAYS, derived_dir=sch.DERIVED,
                    cfg=None):
    """(count, earliest ts) of signals in the traded population.

    A COUNT and a TIMESTAMP. No trade is simulated and no outcome is read.
    Used for the literal §4.2 guard: no signal may originate inside the buffer.
    """
    cfg = cfg or _cfg(baseline_days)
    start = buffer_start(train_start, buffer_days)
    df = sch.load_bars(symbol, start, to_date, derived_dir)
    sig = sg.generate_signals(df, sg.SignalParams(), symbol, cfg)
    lo = sch.day_start_ms(train_start)
    if len(sig) == 0:
        return 0, None, 0
    inside = sig[sig["signal_bar_ts"] >= lo]
    before = int((sig["signal_bar_ts"] < lo).sum())
    earliest = int(inside["signal_bar_ts"].min()) if len(inside) else None
    return int(len(inside)), earliest, before
