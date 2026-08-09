"""Bucket aggregation from the existing 1m and 15m layers. No download, no API.

SOURCES, FIXED. 5m is aggregated from the 1m layer (5 x 1m); 15m is the
existing 15m layer used directly; 1h, 4h and 1d are aggregated from 15m
(4, 16 and 96 x 15m). Nothing here fetches anything -- this is Point 1 work on
data Point 2 already built.

BUCKET ALIGNMENT. Buckets are epoch-floored: `bucket_start = ts - ts % period_ms`.
The Unix epoch begins at 1970-01-01T00:00:00Z and every candidate period
(5m, 15m, 1h, 4h, 1d) divides a 86,400,000 ms day exactly, so epoch flooring
puts 1d buckets on UTC midnight and intraday buckets on natural clock
boundaries -- :00/:05/:10 for 5m, :00/:15/:30/:45 for 15m, the top of the hour
for 1h, and 00/04/08/12/16/20 UTC for 4h. No offset or origin argument is
needed and none is accepted; a resampler that took an origin would be a
resampler whose alignment could drift between callers.

INCOMPLETE BUCKETS ARE DROPPED. A gap in the source produces a bucket with
fewer than its full complement of sub-bars, and its high and low are then taken
over a partial window -- they UNDERSTATE the true range, which biases ATR
downward, which is the direction that would make a timeframe look admissible
when it is not. Constituent bars are counted explicitly and any bucket that is
not full is dropped. Forward-filling, interpolating or padding would all invent
a range that did not happen; dropping is the only permitted treatment.

NO OPEN. `open_synth` is dropped at every load boundary and never read.
"""

import datetime as dt
import glob
import os

import pandas as pd

from src.folds import schedule as sch

ROOT = sch.ROOT
DERIVED = sch.DERIVED

# ---------------------------------------------------------------------------
# The window. NOTHING outside it is read by any code path in this package.
#
# WINDOW_END is 2024-12-31, one day before `schedule.HOLDOUT_TEST_START`. The
# two are asserted adjacent by test, so widening this constant to reach into
# the holdout breaks a test rather than silently succeeding.
# ---------------------------------------------------------------------------
WINDOW_START = dt.date(2022, 1, 1)
WINDOW_END = dt.date(2024, 12, 31)

#: Only these year partitions of the 1m layer may be opened. The layer contains
#: year=2025 and year=2026 directories on disk; the seal here is an explicit
#: filter, not an accident of what happens to exist.
ALLOWED_YEARS = (2022, 2023, 2024)

SYMBOLS = ("BTCUSDT", "ETHUSDT", "SOLUSDT")

MINUTE_MS = 60_000
BAR_1M_MS = MINUTE_MS
BAR_15M_MS = 15 * MINUTE_MS

#: name -> (period_ms, source layer, constituent count required for a full bucket)
TIMEFRAMES = {
    "5m": (5 * MINUTE_MS, "1m", 5),
    "15m": (15 * MINUTE_MS, "15m", 1),
    "1h": (60 * MINUTE_MS, "15m", 4),
    "4h": (240 * MINUTE_MS, "15m", 16),
    "1d": (1440 * MINUTE_MS, "15m", 96),
}

#: Finest first. The frozen rule selects the FINEST admissible timeframe, so
#: this ordering is part of applying it and is asserted by test.
TIMEFRAME_ORDER = ("5m", "15m", "1h", "4h", "1d")

OHLC_COLS = ("high", "low", "close", "volume")


class HoldoutBreach(PermissionError):
    """A frame reached at or past 2025-01-01. Never caught inside this package."""


def holdout_start_ms():
    return sch.day_start_ms(sch.HOLDOUT_TEST_START)


def window_bounds_ms():
    """[lo, hi) in epoch ms for the permitted window."""
    return sch.day_start_ms(WINDOW_START), sch.day_end_exclusive_ms(WINDOW_END)


def assert_sealed(df, where):
    """Refuse any frame containing a bar at or after the holdout boundary.

    Called on the output of every loader and every resample in this package.
    The seal is not maintained by the source data's absence -- the 1m layer has
    2025 and 2026 on disk -- so it is maintained here, on the way out, where a
    widened filter upstream cannot slip past it.
    """
    if len(df):
        hi = int(df["ts"].max())
        if hi >= holdout_start_ms():
            raise HoldoutBreach(
                "%s returned a bar at ts=%d (%s), at or past the sealed "
                "holdout boundary %s. The holdout is evaluated ONCE, at step 9 "
                "of the 4.4 sequence; every other read of it is a leak."
                % (where, hi,
                   dt.datetime.fromtimestamp(hi / 1000, dt.timezone.utc)
                     .isoformat(),
                   sch.HOLDOUT_TEST_START)
            )
    return df


# ---------------------------------------------------------------------------
# Loading.
# ---------------------------------------------------------------------------

def _drop_open(df, path):
    if "open" in df.columns:
        raise ValueError("%s exposes a real `open` column; Point 2 forbids it"
                         % path)
    return df.drop(columns=[c for c in ("open_synth",) if c in df.columns])


def load_15m(symbol, derived_dir=DERIVED):
    """15m bars over the permitted window, via the existing sealed loader.

    Delegates to `schedule.load_bars`, which refuses the holdout on its default
    `authorised=False` path and drops `open_synth` at the boundary. Reusing it
    rather than re-reading the parquet means this package inherits the seal
    that already exists instead of standing up a second one that could drift.
    """
    df = sch.load_bars(symbol, WINDOW_START, WINDOW_END, derived_dir=derived_dir)
    return assert_sealed(df.reset_index(drop=True), "load_15m(%s)" % symbol)


def _one_minute_paths(symbol, derived_dir=DERIVED):
    """Parquet paths for the ALLOWED year partitions only.

    Globbing `year=*` would pick up 2025 and 2026, which are present on disk.
    The years are enumerated explicitly so that the set of files opened is a
    stated constant rather than whatever the filesystem happens to hold.
    """
    paths = []
    for year in ALLOWED_YEARS:
        pat = os.path.join(derived_dir, "ohlcv_1m", "symbol=%s" % symbol,
                           "year=%d" % year, "*.parquet")
        paths.extend(sorted(glob.glob(pat)))
    return paths


def load_1m(symbol, derived_dir=DERIVED):
    """1m bars over the permitted window. Reads ALLOWED_YEARS partitions only."""
    paths = _one_minute_paths(symbol, derived_dir=derived_dir)
    if not paths:
        raise FileNotFoundError(
            "no 1m partitions found for %s in years %s under %s"
            % (symbol, ALLOWED_YEARS, derived_dir))
    frames = [_drop_open(pd.read_parquet(p), p) for p in paths]
    df = pd.concat(frames, ignore_index=True)
    lo, hi = window_bounds_ms()
    df = df[(df["ts"] >= lo) & (df["ts"] < hi)]
    df = df.sort_values("ts", kind="mergesort").reset_index(drop=True)
    return assert_sealed(df, "load_1m(%s)" % symbol)


def load_source(symbol, layer, derived_dir=DERIVED):
    if layer == "15m":
        return load_15m(symbol, derived_dir=derived_dir)
    if layer == "1m":
        return load_1m(symbol, derived_dir=derived_dir)
    raise ValueError("unknown source layer %r" % (layer,))


# ---------------------------------------------------------------------------
# Aggregation.
# ---------------------------------------------------------------------------

def resample(df, period_ms, expected_bars):
    """Aggregate to `period_ms` buckets, dropping any bucket that is not full.

    Returns (bars, stats) where `stats` carries the bucket accounting -- how
    many buckets were formed, how many were dropped for being short, and the
    percentage. That accounting is a reported figure, not a debug aid: a
    measurement resting on a thinned sample has to say so.

        high   = max of constituent highs
        low    = min of constituent lows
        close  = last constituent close
        volume = sum of constituent volumes

    No open is produced. `close` is taken by position within the bucket after a
    stable sort on ts, so it is the chronologically last close and not whatever
    a hash-ordered groupby happened to visit last.
    """
    if expected_bars < 1:
        raise ValueError("expected_bars must be >= 1, got %r" % (expected_bars,))
    if period_ms <= 0:
        raise ValueError("period_ms must be positive, got %r" % (period_ms,))
    for col in ("ts", "high", "low", "close"):
        if col not in df.columns:
            raise ValueError("input is missing required column %r" % col)

    src = df.sort_values("ts", kind="mergesort").reset_index(drop=True)
    bucket = src["ts"] - (src["ts"] % period_ms)

    agg = {"high": "max", "low": "min", "close": "last", "ts": "count"}
    if "volume" in src.columns:
        agg["volume"] = "sum"
    out = src.groupby(bucket, sort=True).agg(agg)
    out = out.rename(columns={"ts": "n_bars"})
    out.index.name = "ts"
    out = out.reset_index()

    n_formed = len(out)
    full = out["n_bars"] == expected_bars
    n_dropped = int((~full).sum())
    over = int((out["n_bars"] > expected_bars).sum())
    if over:
        # More sub-bars than the period can hold means duplicate timestamps in
        # the source. That is a data-integrity fault, not a gap, and silently
        # dropping it would hide it.
        raise ValueError(
            "%d bucket(s) contain MORE than the expected %d sub-bars; the "
            "source has duplicate timestamps" % (over, expected_bars))

    bars = out[full].drop(columns=["n_bars"]).reset_index(drop=True)
    stats = {
        "buckets_formed": n_formed,
        "buckets_kept": int(len(bars)),
        "buckets_dropped": n_dropped,
        "dropped_pct": (100.0 * n_dropped / n_formed) if n_formed else 0.0,
        "expected_bars": expected_bars,
        "period_ms": period_ms,
    }
    return bars, stats


def build(symbol, timeframe, derived_dir=DERIVED):
    """Load the right source layer and aggregate. Returns (bars, stats)."""
    if timeframe not in TIMEFRAMES:
        raise ValueError("unknown timeframe %r; candidates are %s"
                         % (timeframe, TIMEFRAME_ORDER))
    period_ms, layer, expected = TIMEFRAMES[timeframe]
    src = load_source(symbol, layer, derived_dir=derived_dir)
    bars, stats = resample(src, period_ms, expected)
    stats.update({"symbol": symbol, "timeframe": timeframe,
                  "source_layer": layer, "source_bars": int(len(src))})
    return assert_sealed(bars, "build(%s, %s)" % (symbol, timeframe)), stats
