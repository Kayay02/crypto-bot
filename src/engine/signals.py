"""Layer A -- vectorized signal generation on 15m bars only.

Never touches 1m data. Never reads open_synth: the loaders drop the column
outright, so any accidental reference raises KeyError rather than silently
computing on a carried-forward previous close.

Look-ahead is prevented structurally, not by convention:
  * every indicator is causal by construction and shifted where the definition
    requires it (RVOL's denominator is the mean of the PRIOR 20 bars, so the
    signal bar's own volume cannot inflate its own baseline);
  * the breakout level compared against bar T is the Donchian channel of bars
    ending at T-1, shifted before comparison;
  * assert_causal() re-derives every signal from a truncated array and requires
    an identical answer, which is what actually catches a leak.
"""

from dataclasses import dataclass

import numpy as np
import pandas as pd

LONG = "long"
SHORT = "short"

BAR_15M_MS = 900_000


@dataclass(frozen=True)
class SignalParams:
    ema_fast: int = 20
    ema_slow: int = 50
    donchian: int = 20
    rvol_window: int = 20
    rvol_min: float = 1.5
    rsi_period: int = 14
    rsi_long_lo: float = 50.0
    rsi_long_hi: float = 75.0
    rsi_short_lo: float = 25.0
    rsi_short_hi: float = 50.0
    atr_period: int = 14


# --------------------------------------------------------------------------
# indicators -- all causal
# --------------------------------------------------------------------------

def ema(values, period):
    """Standard EMA, alpha = 2/(n+1), seeded with the first value."""
    return pd.Series(values).ewm(span=period, adjust=False).mean().to_numpy()


def rsi_wilder(close, period):
    """Wilder's RSI. Uses Wilder smoothing (alpha = 1/n), not a simple mean."""
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


def rvol_prior(volume, window):
    """Bar volume / mean volume of the PRIOR `window` bars.

    Denominator excludes the current bar. Including it would damp exactly the
    spike the gate exists to detect.
    """
    v = pd.Series(volume)
    base = v.rolling(window).mean().shift(1)
    return (v / base.replace(0.0, np.nan)).to_numpy()


# --------------------------------------------------------------------------
# signal generation
# --------------------------------------------------------------------------

def compute_indicators(df, params):
    """Attach every indicator to a copy of the 15m frame. Causal throughout."""
    if "open_synth" in df.columns:
        raise ValueError(
            "open_synth reached compute_indicators; it must be dropped at load")
    out = df.copy()
    close = out["close"].to_numpy()
    high = out["high"].to_numpy()
    low = out["low"].to_numpy()
    vol = out["volume"].to_numpy()

    out["ema_fast"] = ema(close, params.ema_fast)
    out["ema_slow"] = ema(close, params.ema_slow)
    up, lo = donchian_prior(high, low, params.donchian)
    out["donchian_upper"] = up
    out["donchian_lower"] = lo
    out["rvol"] = rvol_prior(vol, params.rvol_window)
    out["rsi"] = rsi_wilder(close, params.rsi_period)
    out["atr"] = atr_wilder(high, low, close, params.atr_period)
    return out


def generate_signals(df, params, symbol, apply_rvol_gate=True):
    """Signal bars for one symbol. `df` must be 15m, ascending, deduped.

    Returns one row per signal bar with every indicator value at signal time.
    Setting apply_rvol_gate=False produces the `ungated` variant over the
    identical bar universe, so the two are joinable on
    (symbol, signal_bar_ts, direction).
    """
    ind = compute_indicators(df, params)

    close = ind["close"].to_numpy()
    trend_up = ind["ema_fast"].to_numpy() > ind["ema_slow"].to_numpy()
    trend_dn = ind["ema_fast"].to_numpy() < ind["ema_slow"].to_numpy()
    brk_up = close > ind["donchian_upper"].to_numpy()
    brk_dn = close < ind["donchian_lower"].to_numpy()
    rsi = ind["rsi"].to_numpy()
    rvol = ind["rvol"].to_numpy()

    rsi_long = (rsi >= params.rsi_long_lo) & (rsi <= params.rsi_long_hi)
    rsi_short = (rsi >= params.rsi_short_lo) & (rsi <= params.rsi_short_hi)

    gate = (rvol >= params.rvol_min) if apply_rvol_gate else np.ones(
        len(ind), dtype=bool)
    # NaN in any input must not produce a signal.
    finite = (np.isfinite(rsi) & np.isfinite(rvol)
              & np.isfinite(ind["atr"].to_numpy())
              & np.isfinite(ind["donchian_upper"].to_numpy())
              & np.isfinite(ind["donchian_lower"].to_numpy()))

    long_sig = trend_up & brk_up & rsi_long & gate & finite
    short_sig = trend_dn & brk_dn & rsi_short & gate & finite

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


INDICATOR_COLS = ("ema_fast", "ema_slow", "donchian_upper", "donchian_lower",
                  "rvol", "rsi", "atr")


def assert_causal_indicators(df, params, n_checks=25, seed=0):
    """Every indicator at bar T must be unchanged by truncating history at T.

    Checked at ARBITRARY bars, not just signal bars. Checking only signal bars
    is vacuous when a leak suppresses signals entirely -- the guard then finds
    nothing to compare and reports success.
    """
    full = compute_indicators(df, params)
    rng = np.random.default_rng(seed)
    lo = max(params.ema_slow, params.donchian, params.rvol_window,
             params.rsi_period, params.atr_period) + 5
    if len(df) <= lo:
        raise ValueError("history too short to check causality")
    picks = rng.choice(np.arange(lo, len(df)),
                       size=min(n_checks, len(df) - lo), replace=False)
    for i in picks:
        trunc = compute_indicators(df.iloc[:i + 1], params)
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


def assert_causal(df, params, symbol, n_checks=25, seed=0):
    """Recompute signals on truncated history and require identical answers.

    This is the structural look-ahead check. If any indicator or comparison
    reads bar T+1, a signal computed on bars[:T+1] will disagree with the same
    bar computed on the full array, and this raises.

    Always runs the indicator-level check too, so a leak that suppresses all
    signals cannot pass by leaving nothing to compare.
    """
    n_ind = assert_causal_indicators(df, params, n_checks=n_checks, seed=seed)
    full = generate_signals(df, params, symbol)
    if full.empty:
        return n_ind
    rng = np.random.default_rng(seed)
    ts_all = df["ts"].to_numpy()
    picks = rng.choice(full["signal_bar_ts"].to_numpy(),
                       size=min(n_checks, len(full)), replace=False)
    for ts in picks:
        end = int(np.nonzero(ts_all == ts)[0][0]) + 1
        truncated = generate_signals(df.iloc[:end], params, symbol)
        a = full[full["signal_bar_ts"] == ts]
        b = truncated[truncated["signal_bar_ts"] == ts]
        if len(a) != len(b):
            raise AssertionError(
                f"look-ahead: bar {ts} yields {len(a)} signals on full history "
                f"but {len(b)} when truncated at that bar")
        for col in ("ema_fast", "ema_slow", "donchian_upper", "donchian_lower",
                    "rvol", "rsi", "atr"):
            x = a[col].to_numpy()
            y = b[col].to_numpy()
            if not np.allclose(x, y, rtol=1e-12, atol=1e-12, equal_nan=True):
                raise AssertionError(
                    f"look-ahead: {col} at bar {ts} differs when truncated "
                    f"({x} vs {y})")
    return len(picks)
