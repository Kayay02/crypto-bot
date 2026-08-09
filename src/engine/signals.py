"""Layer A -- vectorized signal generation on 15m bars only.

Never touches 1m data. Never reads open_synth: the loaders drop the column
outright, so any accidental reference raises KeyError rather than silently
computing on a carried-forward previous close.

Look-ahead is prevented structurally, not by convention:
  * every indicator is causal by construction and shifted where the definition
    requires it (the RVOL slot baseline reads STRICTLY PRIOR COMPLETED DAYS, so
    neither the signal bar nor any other bar of its own day can inflate its own
    baseline);
  * the breakout level compared against bar T is the Donchian channel of bars
    ending at T-1, shifted before comparison;
  * assert_causal() re-derives every signal from a truncated array and requires
    an identical answer, which is what actually catches a leak.

POINT 3R changed the entry rule:
  * RVOL's baseline is session-normalised (median of the same 15m UTC slot over
    the trailing `baseline_days` completed prior days), quote-denominated. The
    flat 20-bar mean tracked the SLOPE of the diurnal cycle, so the gate partly
    measured what time it was: pass rate on breakout bars swung 32-51pp by hour
    of UTC day.
  * RSI is NO LONGER AN ENTRY CONDITION. rsi_lower rejected zero of 11,711
    breakout bars over 2022-23 (minimum RSI on a long breakout bar was 54.18);
    rsi_upper was removed earlier for violating the Guard Rail Principle. RSI
    is retained as an informational column only.
  * vwap_position was proposed and KILLED on measurement. It is deliberately
    absent -- see docs/handoff/06_structural_outcome.md.
"""

from dataclasses import dataclass

import numpy as np
import pandas as pd

LONG = "long"
SHORT = "short"

BAR_15M_MS = 900_000
DAY_MS = 86_400_000
SLOTS_PER_DAY = DAY_MS // BAR_15M_MS  # 96

# Both the RVOL numerator and its baseline read this field. They must always be
# the same field: mixing base and quote denomination silently divides a
# quantity by a value in different units.
VOLUME_FIELD = "quote_volume"


@dataclass(frozen=True)
class SignalParams:
    ema_fast: int = 20
    ema_slow: int = 50
    donchian: int = 20
    rsi_period: int = 14        # informational column only; NOT an entry term
    atr_period: int = 14


# --------------------------------------------------------------------------
# indicators -- all causal
# --------------------------------------------------------------------------

def ema(values, period):
    """Standard EMA, alpha = 2/(n+1), seeded with the first value."""
    return pd.Series(values).ewm(span=period, adjust=False).mean().to_numpy()


def rsi_wilder(close, period):
    """Wilder's RSI. Uses Wilder smoothing (alpha = 1/n), not a simple mean.

    Retained and recorded on signal rows, but NO ENTRY CONDITION READS IT.
    """
    c = pd.Series(close)
    delta = c.diff()
    gain = delta.clip(lower=0.0)
    loss = (-delta).clip(lower=0.0)
    avg_gain = gain.ewm(alpha=1.0 / period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1.0 / period, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0.0, np.nan)
    out = 100.0 - (100.0 / (1.0 + rs))
    # avg_loss == 0 means no down move in the window -> RSI 100 by definition.
    out = out.where(avg_loss != 0.0, 100.0)
    out.iloc[:period] = np.nan
    return out.to_numpy()


def atr_wilder(high, low, close, period):
    """Wilder's ATR from true range."""
    h, l = pd.Series(high), pd.Series(low)
    pc = pd.Series(close).shift(1)
    tr = pd.concat([h - l, (h - pc).abs(), (l - pc).abs()], axis=1).max(axis=1)
    out = tr.ewm(alpha=1.0 / period, adjust=False).mean()
    out.iloc[:period] = np.nan
    return out.to_numpy()


def donchian_prior(high, low, period):
    """Channel of the `period` bars ENDING AT T-1.

    Shifted by one: comparing bar T's close to a channel that already contains
    bar T's own high would make the break trivially self-satisfying.
    """
    upper = pd.Series(high).rolling(period).max().shift(1).to_numpy()
    lower = pd.Series(low).rolling(period).min().shift(1).to_numpy()
    return upper, lower


# --------------------------------------------------------------------------
# session-normalised RVOL (B1)
# --------------------------------------------------------------------------

def session_baseline(ts, values, baseline_days):
    """Median of the same 15m UTC slot over the trailing COMPLETED prior days.

    Causality is structural, not conventional: the day/slot matrix is rolled
    over the day axis and then shifted by one WHOLE DAY, so the value returned
    for any bar of day D is a function of days [D-baseline_days, D-1] only. Bar
    T's own day contributes nothing -- not even earlier slots of it.

    Median, not mean: one event bar in the baseline would inflate a mean and
    suppress RVOL for that slot every day for the rest of the window.

    min_periods == baseline_days, so a slot with a gap in its history yields
    NaN rather than a baseline quietly computed from fewer days than requested.
    """
    if baseline_days < 1:
        raise ValueError("baseline_days must be >= 1")
    ts = np.asarray(ts, dtype=np.int64)
    values = np.asarray(values, dtype=float)
    day = ts // DAY_MS
    slot = (ts // BAR_15M_MS) % SLOTS_PER_DAY

    tbl = pd.DataFrame({"day": day, "slot": slot, "v": values})
    # Duplicate (day, slot) cannot occur on a deduped 15m series; assert it.
    if tbl.duplicated(["day", "slot"]).any():
        raise ValueError("duplicate (day, slot) -- series is not a clean 15m grid")
    mat = tbl.pivot(index="day", columns="slot", values="v").sort_index()
    # Reindex onto a contiguous day axis so a MISSING calendar day consumes a
    # slot of the trailing window rather than being skipped over.
    mat = mat.reindex(range(int(mat.index.min()), int(mat.index.max()) + 1))
    base = mat.rolling(baseline_days, min_periods=baseline_days).median().shift(1)

    lookup = base.stack(future_stack=True)
    idx = pd.MultiIndex.from_arrays([day, slot])
    return lookup.reindex(idx).to_numpy(float)


def session_rvol(ts, values, baseline_days):
    """Bar volume / same-slot median of the trailing completed prior days.

    Numerator and denominator are the SAME array by construction here, which is
    the structural form of the "must use the same field" rule.
    """
    base = session_baseline(ts, values, baseline_days)
    base = np.where(base > 0.0, base, np.nan)
    return np.asarray(values, dtype=float) / base


# --------------------------------------------------------------------------
# signal generation
# --------------------------------------------------------------------------

def compute_indicators(df, params, baseline_days):
    """Attach every indicator to a copy of the 15m frame. Causal throughout."""
    if "open_synth" in df.columns:
        raise ValueError(
            "open_synth reached compute_indicators; it must be dropped at load")
    if VOLUME_FIELD not in df.columns:
        raise KeyError(
            f"RVOL is {VOLUME_FIELD}-denominated (M6 verdict, 3 of 3 symbols) "
            f"but the frame has no {VOLUME_FIELD} column")
    out = df.copy()
    close = out["close"].to_numpy()
    high = out["high"].to_numpy()
    low = out["low"].to_numpy()

    out["ema_fast"] = ema(close, params.ema_fast)
    out["ema_slow"] = ema(close, params.ema_slow)
    up, lo = donchian_prior(high, low, params.donchian)
    out["donchian_upper"] = up
    out["donchian_lower"] = lo
    # Numerator and denominator are the same field, passed once.
    vol = out[VOLUME_FIELD].to_numpy(float)
    out["rvol"] = session_rvol(out["ts"].to_numpy(), vol, baseline_days)
    out["rsi"] = rsi_wilder(close, params.rsi_period)   # informational only
    out["atr"] = atr_wilder(high, low, close, params.atr_period)
    return out


def generate_signals(df, params, symbol, cfg, apply_rvol_gate=True,
                     apply_ema_filter=True):
    """Signal bars for one symbol. `df` must be 15m, ascending, deduped.

    Entry rule after 3R, long: EMA20 > EMA50 AND close > Donchian-20 upper AND
    session-normalised RVOL >= cfg.rvol_threshold. Short is the symmetric
    inverse. That is the whole rule -- no RSI, no vwap_position, no cooldown
    condition.

    Setting apply_rvol_gate=False produces the `ungated` variant over the
    identical bar universe, so the two are joinable on
    (symbol, signal_bar_ts, direction).

    Setting apply_ema_filter=False produces the MINUS-EMA arm of section 4.5's
    decomposition. Unlike the RVOL gate this cannot be applied as a filter of
    the gated table -- dropping the trend condition ADMITS bars the baseline
    never generated, so the arm is a SUPERSET and has to be simulated
    separately. Both switches default to the baseline rule, so neither changes
    engine semantics; a test asserts the defaults are bit-identical.

    §4.5 pre-commits that EMA failing attribution is REPORTED AS A THESIS
    FAILURE, NOT EXECUTED AS A DROP: the whole edge claim is trend
    continuation, so a strategy without it is a different strategy.
    """
    ind = compute_indicators(df, params, cfg.baseline_days)

    close = ind["close"].to_numpy()
    if apply_ema_filter:
        trend_up = ind["ema_fast"].to_numpy() > ind["ema_slow"].to_numpy()
        trend_dn = ind["ema_fast"].to_numpy() < ind["ema_slow"].to_numpy()
    else:
        # Direction is then set by the BREAKOUT alone: a close above the upper
        # channel is a long, below the lower channel a short. The bar universe
        # widens; it does not become directionless.
        trend_up = np.ones(len(ind), dtype=bool)
        trend_dn = np.ones(len(ind), dtype=bool)
    brk_up = close > ind["donchian_upper"].to_numpy()
    brk_dn = close < ind["donchian_lower"].to_numpy()
    rvol = ind["rvol"].to_numpy()

    gate = (rvol >= cfg.rvol_threshold) if apply_rvol_gate else np.ones(
        len(ind), dtype=bool)
    # NaN in any input must not produce a signal. RSI is NOT in this list: it
    # is informational, so its warm-up NaNs must not suppress signals.
    finite = (np.isfinite(rvol)
              & np.isfinite(ind["atr"].to_numpy())
              & np.isfinite(ind["donchian_upper"].to_numpy())
              & np.isfinite(ind["donchian_lower"].to_numpy()))

    long_sig = trend_up & brk_up & gate & finite
    short_sig = trend_dn & brk_dn & gate & finite

    rows = []
    for mask, direction in ((long_sig, LONG), (short_sig, SHORT)):
        idx = np.nonzero(mask)[0]
        if not len(idx):
            continue
        sub = ind.iloc[idx].copy()
        sub["direction"] = direction
        rows.append(sub)
    if not rows:
        cols = list(ind.columns) + ["direction", "symbol", "signal_bar_ts"]
        return pd.DataFrame(columns=cols)

    sig = pd.concat(rows, ignore_index=True)
    sig["symbol"] = symbol
    sig["signal_bar_ts"] = sig["ts"].astype(np.int64)
    sig["variant"] = "gated" if apply_rvol_gate else "ungated"
    return sig.sort_values(["signal_bar_ts", "direction"],
                           kind="mergesort").reset_index(drop=True)


def warmup_bars(df, params, cfg):
    """Bars that cannot produce a signal because an input is still warming up.

    Counted and reported rather than silently dropped: the session baseline
    needs `baseline_days` completed prior days, which is a much longer warm-up
    than the flat 20-bar mean it replaced, and the difference should be visible.
    """
    ind = compute_indicators(df, params, cfg.baseline_days)
    finite = (np.isfinite(ind["rvol"].to_numpy())
              & np.isfinite(ind["atr"].to_numpy())
              & np.isfinite(ind["donchian_upper"].to_numpy())
              & np.isfinite(ind["donchian_lower"].to_numpy()))
    return int((~finite).sum())


INDICATOR_COLS = ("ema_fast", "ema_slow", "donchian_upper", "donchian_lower",
                  "rvol", "rsi", "atr")


def assert_causal_indicators(df, params, cfg, n_checks=25, seed=0):
    """Every indicator at bar T must be unchanged by truncating history at T.

    Checked at ARBITRARY bars, not just signal bars. Checking only signal bars
    is vacuous when a leak suppresses signals entirely -- the guard then finds
    nothing to compare and reports success.
    """
    full = compute_indicators(df, params, cfg.baseline_days)
    rng = np.random.default_rng(seed)
    lo = max(params.ema_slow, params.donchian, params.rsi_period,
             params.atr_period, cfg.baseline_days * SLOTS_PER_DAY) + 5
    if len(df) <= lo:
        raise ValueError("history too short to check causality")
    picks = rng.choice(np.arange(lo, len(df)),
                       size=min(n_checks, len(df) - lo), replace=False)
    for i in picks:
        trunc = compute_indicators(df.iloc[:i + 1], params, cfg.baseline_days)
        for col in INDICATOR_COLS:
            a = full[col].to_numpy()[i]
            b = trunc[col].to_numpy()[i]
            if not (np.isnan(a) and np.isnan(b)) and not np.isclose(
                    a, b, rtol=1e-12, atol=1e-12, equal_nan=True):
                raise AssertionError(
                    f"look-ahead: {col} at bar index {i} (ts "
                    f"{int(df['ts'].to_numpy()[i])}) is {a} on full history "
                    f"but {b} when truncated at that bar")
    return len(picks)


def assert_causal(df, params, symbol, cfg, n_checks=25, seed=0):
    """Recompute signals on truncated history and require identical answers.

    This is the structural look-ahead check. If any indicator or comparison
    reads bar T+1, a signal computed on bars[:T+1] will disagree with the same
    bar computed on the full array, and this raises.

    Always runs the indicator-level check too, so a leak that suppresses all
    signals cannot pass by leaving nothing to compare.
    """
    n_ind = assert_causal_indicators(df, params, cfg, n_checks=n_checks,
                                     seed=seed)
    full = generate_signals(df, params, symbol, cfg)
    if full.empty:
        return n_ind
    rng = np.random.default_rng(seed)
    ts_all = df["ts"].to_numpy()
    picks = rng.choice(full["signal_bar_ts"].to_numpy(),
                       size=min(n_checks, len(full)), replace=False)
    for ts in picks:
        end = int(np.nonzero(ts_all == ts)[0][0]) + 1
        truncated = generate_signals(df.iloc[:end], params, symbol, cfg)
        a = full[full["signal_bar_ts"] == ts]
        b = truncated[truncated["signal_bar_ts"] == ts]
        if len(a) != len(b):
            raise AssertionError(
                f"look-ahead: bar {ts} yields {len(a)} signals on full history "
                f"but {len(b)} when truncated at that bar")
        for col in INDICATOR_COLS:
            x = a[col].to_numpy()
            y = b[col].to_numpy()
            if not np.allclose(x, y, rtol=1e-12, atol=1e-12, equal_nan=True):
                raise AssertionError(
                    f"look-ahead: {col} at bar {ts} differs when truncated "
                    f"({x} vs {y})")
    return len(picks)
