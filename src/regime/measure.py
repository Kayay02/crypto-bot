"""Per-symbol rolling regime measurement over 15m bars.

Two labelled axes (m*, Kaufman efficiency ratio) and two reported covariates
(drift, liquidity), each computed on a trailing window ending AT bar T and
emitted one row per bar.

CAUSALITY. Every window is trailing and right-aligned on T inclusive: the value
at bar T is a function of bars [T-N+1, T] only. Bar T's own contribution is
legitimately included -- unlike the RVOL slot baseline, where the bar's own
volume had to be excluded because it would damp the very spike the gate exists
to detect. Here the label describes the window ending at T, which is entirely
observable once T has closed. Partial windows emit NaN; they are never filled.

The single mutation this module's guard exists to catch is a window whose right
edge slips to T+1 (a dropped or reversed shift). `_ROLL` and `_LAG` are the two
places that alignment lives, and both are indirected through module-level hooks
so a test can mutate exactly that and prove the guard fires. A generic
truncation check is known to pass vacuously in this project -- three such guards
have been found -- so the guard is tested against its own target mutation
rather than assumed to work.

FIREWALL. OHLCV in, regime labels out. No trade data is read. `open_synth` is
dropped at the boundary and the real `open` field does not exist, so any
reference raises KeyError.
"""

import os
import subprocess
import sys

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "src", "engine"))

import costs  # noqa: E402
import signals as sg  # noqa: E402

DERIVED = os.path.join(ROOT, "data", "derived")
REGIME_DIR = os.path.join(DERIVED, "regime")
SYMBOLS = ("BTCUSDT", "ETHUSDT", "SOLUSDT")

BAR_15M_MS = 900_000
DAY_MS = 86_400_000
BARS_PER_DAY = DAY_MS // BAR_15M_MS          # 96, derived not hardcoded

# Storage conventions, matching src/data/build_derived.py.
COMPRESSION = "zstd"
COMPRESSION_LEVEL = 3

# The fit window for frozen terciles, and the hard end of everything this
# module is authorised to compute. 2025-01-01 onward is the sealed holdout.
FIT_START_MS = 1_640_995_200_000             # 2022-01-01T00:00:00Z
HOLDOUT_START_MS = 1_735_689_600_000         # 2025-01-01T00:00:00Z

WINDOW_DAYS_PRIMARY = 30
WINDOW_DAYS_SENSITIVITY = (14, 60)

ATR_PERIOD = 14
EMA_FAST = 20
EMA_SLOW = 50


def log(msg):
    print(msg, flush=True)


def git_revision():
    """Commit hash of the code that produced this output.

    Suffixed '-dirty' when the working tree has uncommitted changes, so an
    artifact can never claim provenance it cannot actually reproduce.
    """
    try:
        rev = subprocess.run(["git", "-C", ROOT, "rev-parse", "HEAD"],
                             capture_output=True, text=True, timeout=10)
        if rev.returncode != 0:
            return "unknown"
        head = rev.stdout.strip()
        st = subprocess.run(["git", "-C", ROOT, "status", "--porcelain"],
                            capture_output=True, text=True, timeout=10)
        if st.returncode != 0:
            return f"{head}-dirty"
        return f"{head}-dirty" if st.stdout.strip() else head
    except (OSError, subprocess.SubprocessError):
        return "unknown"


def bars_for_days(days):
    """Window length in 15m bars. DERIVED from the timeframe, never hardcoded."""
    if days <= 0:
        raise ValueError(f"window days must be positive, got {days}")
    return int(days) * BARS_PER_DAY


# ---------------------------------------------------------------------------
# the two alignment primitives -- the only place a shift can be dropped
# ---------------------------------------------------------------------------

def _roll(series, n):
    """Trailing window of `n` bars ending AT the current bar, inclusive.

    pandas `rolling(n)` is right-aligned on the current row, which is exactly
    the intended alignment. min_periods=n so a partial window yields NaN rather
    than a value computed from fewer bars than requested.
    """
    return series.rolling(n, min_periods=n)


def _lag(series, n):
    """The value `n` bars BEFORE the current bar. Positive shift = backward."""
    return series.shift(n)


# Indirection hooks. Production code calls these; the causality mutation test
# rebinds them to a one-bar-forward variant and requires the guard to fire.
_ROLL = _roll
_LAG = _lag


# ---------------------------------------------------------------------------
# config access -- stop_min_pct only, and provably nothing else
# ---------------------------------------------------------------------------

# CostConfig requires four parameters that have no defaults (Point 3R). None of
# them enters stop_min_pct, which depends only on n_cost, the fee schedule, the
# per-symbol stop haircut, risk_usd, equity and max_leverage. They are supplied
# here purely to construct the object and are NEVER read; the value's
# independence from them is asserted by a test, so this cannot become a channel
# through which a strategy parameter reaches the regime axis.
_UNUSED_SWEEP_PARAMS = dict(stop_atr_mult=1.0, stop_max_pct=0.035,
                            rvol_threshold=1.5, baseline_days=20)


def stop_min_pct(symbol, cfg=None):
    """The DERIVED per-symbol cost floor, as a FRACTION of price.

    Read from the engine's config rather than restated, so there is one
    definition of the floor in the repo. 1.020% for BTC/ETH, 1.320% for SOL.
    """
    cfg = cfg or costs.CostConfig(**_UNUSED_SWEEP_PARAMS)
    return cfg.stop_min_pct(symbol)


# ---------------------------------------------------------------------------
# loading
# ---------------------------------------------------------------------------

def load_15m(symbol, derived_dir=DERIVED, end_ts_exclusive=HOLDOUT_START_MS):
    """15m bars up to (not including) `end_ts_exclusive`.

    `open_synth` is dropped at the boundary for the same reason the engine's
    loader drops it: no downstream code may read a synthesized open. There is
    no real `open` column to read.

    Truncation happens HERE, before any indicator is computed, so no rolling
    window can reach a bar the caller is not authorised to see. The default
    end is the holdout boundary: 2025-01-01.
    """
    import pyarrow.parquet as pq

    path = os.path.join(derived_dir, "ohlcv_15m", f"{symbol}.parquet")
    df = pq.read_table(path).to_pandas()
    if "open" in df.columns:
        raise ValueError(
            f"{path} exposes a real `open` column; Point 2 forbids it")
    df = df.drop(columns=["open_synth"])
    if end_ts_exclusive is not None:
        df = df[df["ts"] < end_ts_exclusive]
    return df.sort_values("ts", kind="mergesort").reset_index(drop=True)


# ---------------------------------------------------------------------------
# axes
# ---------------------------------------------------------------------------

def atr_pct(df, period=ATR_PERIOD):
    """ATR(14) as a PERCENTAGE of close. Causal: ATR at T uses bars <= T.

    Wilder's ATR is imported from the engine rather than reimplemented, so
    "ATR" means the same thing here as it does in a trade.
    """
    atr = sg.atr_wilder(df["high"].to_numpy(), df["low"].to_numpy(),
                        df["close"].to_numpy(), period)
    return pd.Series(atr / df["close"].to_numpy() * 100.0, index=df.index)


def m_star(df, symbol, window_bars, cfg=None):
    """m* = stop_min_pct / median(ATR%) over the trailing window.

    Both terms are expressed in PERCENT. The ratio is dimensionless, so it is
    invariant to that choice as long as the two agree -- which is the point of
    computing them in one place.

    Low m* = volatility comfortably above the cost structure. High m* = the
    floor dominates and the strategy is structurally squeezed.
    """
    floor_pct = stop_min_pct(symbol, cfg) * 100.0
    med = _ROLL(atr_pct(df), window_bars).median()
    # A zero or non-finite median has no defined ratio. NaN, never a filled 0.
    med = med.where(med > 0.0)
    return floor_pct / med


def efficiency_ratio(df, window_bars):
    """Kaufman efficiency ratio over the trailing window. Bounded 0-1.

        |close[t] - close[t-N]|  /  sum(|close[i] - close[i-1]|, i in (t-N, t])

    Numerator and denominator span the SAME N intervals, which is what makes a
    monotonic ramp give exactly 1.0 and a round-trip zigzag exactly 0.0.

    A zero denominator (a perfectly flat window) leaves the ratio undefined and
    emits NaN. It is NOT 0: zero would assert maximal inefficiency, when in
    fact nothing moved at all and efficiency is not a meaningful question.
    """
    close = df["close"]
    numer = (close - _LAG(close, window_bars)).abs()
    denom = _ROLL(close.diff().abs(), window_bars).sum()
    return numer / denom.where(denom > 0.0)


def drift(df, window_bars):
    """Signed log return over the window, and the EMA20>EMA50 bar fraction.

    Reported, never bucketed: long/short cohorts are already reported
    separately, which absorbs most of what a drift label would carry.
    """
    close = df["close"]
    log_ret = np.log(close / _LAG(close, window_bars))
    fast = sg.ema(close.to_numpy(), EMA_FAST)
    slow = sg.ema(close.to_numpy(), EMA_SLOW)
    above = pd.Series((fast > slow).astype(float), index=df.index)
    return log_ret, _ROLL(above, window_bars).mean()


def median_daily_quote_volume(df, window_bars):
    """Liquidity level: median trailing-24h quote volume over the window.

    See report 09 for the judgment call -- "median daily quote volume" is
    implemented as the median over the window of the rolling 24-hour quote
    volume sum, rather than of calendar-day totals. This keeps the quantity
    per-bar and causal with no calendar-boundary artifact, and at day
    boundaries the two coincide.

    Does not affect the RVOL gate (session-normalised over trailing days, so
    self-normalising to level) but does affect slippage realism.
    """
    daily = _ROLL(df["quote_volume"], BARS_PER_DAY).sum()
    return _ROLL(daily, window_bars).median()


# ---------------------------------------------------------------------------
# assembly
# ---------------------------------------------------------------------------

MEASURE_COLS = ("m_star", "efficiency_ratio", "drift_log_return",
                "ema_fraction", "median_daily_quote_volume")


def warmup_bars(window_days=WINDOW_DAYS_PRIMARY):
    """Leading bars that cannot carry a COMPLETE regime observation.

    The five measured columns do not all become computable at the same bar:

      ema_fraction   window                          -> index n-1
      efficiency     window + 1 bar for the diff     -> index n
      drift          window                          -> index n
      m_star         window + ATR(14) warm-up        -> index n+13
      liquidity      window + 24h sum warm-up        -> index n+94

    A single boundary is imposed at the LARGEST of these and every column is
    masked before it, so a row is either a complete regime observation or it is
    entirely NaN. Emitting ema_fraction at bar n-1 while m_star is still NaN
    would produce partial rows, and partial rows invite downstream code to
    filter on whichever column happens to be populated. One boundary, stated
    here, is the loud version.
    """
    n = bars_for_days(window_days)
    return n + max(BARS_PER_DAY - 1, ATR_PERIOD) - 1


def measure(df, symbol, window_days=WINDOW_DAYS_PRIMARY, cfg=None):
    """All axes and covariates for one symbol at one window length.

    One row per input bar. Bars before a full window is available carry NaN in
    EVERY measured column -- never a partial-window value, and never a filled
    one. See warmup_bars() for why the boundary is uniform.
    """
    n = bars_for_days(window_days)
    if len(df) == 0:
        raise ValueError(f"{symbol}: no bars to measure")
    log_ret, ema_frac = drift(df, n)
    out = pd.DataFrame({
        "ts": df["ts"].to_numpy(),
        "m_star": m_star(df, symbol, n, cfg),
        "efficiency_ratio": efficiency_ratio(df, n),
        "drift_log_return": log_ret,
        "ema_fraction": ema_frac,
        "median_daily_quote_volume": median_daily_quote_volume(df, n),
    })
    warm = warmup_bars(window_days)
    if warm:
        out.loc[out.index[:warm], list(MEASURE_COLS)] = np.nan
    out["window_days"] = int(window_days)
    return out.reset_index(drop=True)


def m_star_below_one(series):
    """Count of windows where m* < 1.0.

    A REPORTED STRUCTURAL MARKER, NOT A CUT (4.1, Appendix A). It is the level
    at which median volatility would exactly reach the cost floor. M8 measured
    m* at 1.71-4.08, so it is expected never to be crossed; a crossing would be
    notable in itself.
    """
    s = pd.Series(series)
    return int((s < 1.0).sum()), int(s.notna().sum())


# ---------------------------------------------------------------------------
# causality guard -- tested against its own target mutation
# ---------------------------------------------------------------------------

def assert_causal(df, symbol, window_days=WINDOW_DAYS_PRIMARY, n_checks=12,
                  seed=0, cfg=None):
    """Recompute on truncated history; every measured value at T must match.

    If any window's right edge reaches T+1, the truncated recomputation at T
    either yields NaN (the future bar is gone) or a different value, and this
    raises.

    Checked at ARBITRARY bars, not only at bars that happen to carry values:
    checking only non-NaN rows is vacuous when a leak turns rows into NaN.
    """
    n = bars_for_days(window_days)
    full = measure(df, symbol, window_days, cfg)
    if len(df) <= n + 2:
        raise ValueError("history too short to check causality")
    rng = np.random.default_rng(seed)
    picks = rng.choice(np.arange(n, len(df)),
                       size=min(n_checks, len(df) - n), replace=False)
    for i in picks:
        trunc = measure(df.iloc[:i + 1], symbol, window_days, cfg)
        for col in MEASURE_COLS:
            a = full[col].to_numpy()[i]
            b = trunc[col].to_numpy()[i]
            if np.isnan(a) and np.isnan(b):
                continue
            if not np.isclose(a, b, rtol=1e-12, atol=1e-12, equal_nan=True):
                raise AssertionError(
                    f"look-ahead: {col} at bar index {i} "
                    f"(ts {int(df['ts'].to_numpy()[i])}) is {a} on full "
                    f"history but {b} when truncated at that bar")
    return len(picks)


# ---------------------------------------------------------------------------
# output
# ---------------------------------------------------------------------------

OUTPUT_COLS = ["ts", "m_star", "efficiency_ratio", "drift_log_return",
               "ema_fraction", "median_daily_quote_volume",
               "m_star_label", "efficiency_label", "window_days"]


def _schema():
    import pyarrow as pa
    return pa.schema([
        ("ts", pa.int64()),
        ("m_star", pa.float64()),
        ("efficiency_ratio", pa.float64()),
        ("drift_log_return", pa.float64()),
        ("ema_fraction", pa.float64()),
        ("median_daily_quote_volume", pa.float64()),
        ("m_star_label", pa.string()),
        ("efficiency_label", pa.string()),
        ("window_days", pa.int32()),
    ])


def write_parquet(df, path):
    """ZSTD-3, fixed row groups -- same conventions as the derived layer."""
    import pyarrow as pa
    import pyarrow.parquet as pq

    os.makedirs(os.path.dirname(path), exist_ok=True)
    table = pa.Table.from_pandas(df[OUTPUT_COLS], schema=_schema(),
                                 preserve_index=False)
    pq.write_table(table, path, compression=COMPRESSION,
                   compression_level=COMPRESSION_LEVEL,
                   row_group_size=256 * 1024, version="2.6",
                   store_schema=False)
    return os.path.getsize(path)
