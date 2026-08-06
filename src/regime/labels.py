"""Tercile fitting, freezing, application, and cross-symbol concordance.

Both labelled axes use terciles fitted ONLY on the pre-registered fit window,
then FROZEN and applied unchanged to all later data.

Later data WILL produce unbalanced buckets. That is expected and CORRECT: an
imbalance is a finding about how the market changed, not a defect to be
corrected. Nothing here rebalances or refits, and the frozen artifact refuses
to be silently regenerated for a different fit window.

Fitting on the full sample would be a full-sample quantile -- exactly the
look-ahead 4.1 forbids -- so the fit window is an explicit argument everywhere
and never defaults to "whatever data you happen to have".
"""

import json
import os

import numpy as np
import pandas as pd

from . import measure as ms

LOW, MID, HIGH = "low", "mid", "high"
LABELS = (LOW, MID, HIGH)
AXES = ("m_star", "efficiency_ratio")

TERCILES_PATH = os.path.join(ms.REGIME_DIR, "terciles.json")


# ---------------------------------------------------------------------------
# fit / apply
# ---------------------------------------------------------------------------

def fit_terciles(series, fit_start, fit_end, ts=None):
    """The two cut values splitting `series` into terciles on the fit window.

    `fit_start` / `fit_end` are epoch-ms bounds, inclusive of start and
    EXCLUSIVE of end, applied against `ts`. Passing the bounds explicitly is
    deliberate: a quantile fitted on "all the data present" is a full-sample
    quantile, which is the look-ahead this module exists to avoid.

    NaNs are excluded from the fit rather than filled. They mark bars where the
    window was not yet full, and inventing a value for them would fabricate the
    very warm-up the design is careful about.
    """
    s = pd.Series(series).reset_index(drop=True)
    if ts is None:
        raise ValueError("fit_terciles requires the ts column to bound the "
                         "fit window; fitting on an unbounded series is a "
                         "full-sample quantile")
    t = pd.Series(np.asarray(ts, dtype="int64")).reset_index(drop=True)
    if len(t) != len(s):
        raise ValueError(f"ts length {len(t)} != series length {len(s)}")
    if fit_end <= fit_start:
        raise ValueError(f"empty fit window [{fit_start}, {fit_end})")

    sel = s[(t >= fit_start) & (t < fit_end)].dropna()
    if len(sel) < 3:
        raise ValueError(
            f"fit window [{fit_start}, {fit_end}) holds {len(sel)} finite "
            f"values; cannot fit terciles")
    c1, c2 = (float(np.quantile(sel.to_numpy(), 1.0 / 3.0)),
              float(np.quantile(sel.to_numpy(), 2.0 / 3.0)))
    if not (c1 < c2):
        raise ValueError(
            f"degenerate terciles: cuts {c1} and {c2} do not separate; the "
            f"axis has too little variance on the fit window to label")
    return c1, c2


def apply_terciles(series, cuts):
    """Labels {low, mid, high} from frozen cuts. NaN in -> None out.

    Boundaries: value <= cuts[0] is low, value > cuts[1] is high. A NaN is
    never assigned a bucket and is never filled.
    """
    c1, c2 = float(cuts[0]), float(cuts[1])
    if not (c1 < c2):
        raise ValueError(f"cuts must be increasing, got {c1}, {c2}")
    s = pd.Series(series).reset_index(drop=True)
    out = pd.Series([None] * len(s), dtype=object)
    finite = s.notna()
    out[finite & (s <= c1)] = LOW
    out[finite & (s > c1) & (s <= c2)] = MID
    out[finite & (s > c2)] = HIGH
    return out


# ---------------------------------------------------------------------------
# freezing
# ---------------------------------------------------------------------------

def _key(symbol, axis, window_days):
    return f"{symbol}|{axis}|{window_days}d"


def freeze_terciles(entries, path=TERCILES_PATH, fit_start=None, fit_end=None):
    """Persist fitted cuts. Refuses to overwrite a different fit window.

    Once written the file is not regenerated silently. If it exists and the
    requested fit window differs, this RAISES rather than overwriting -- a
    frozen cut that can be quietly refitted is not frozen, and the whole point
    of the artifact is that it provably predates the data it is applied to.
    """
    payload = {
        "fit_start_ms": int(fit_start),
        "fit_end_ms": int(fit_end),
        "fit_start_utc": _utc(fit_start),
        "fit_end_utc_exclusive": _utc(fit_end),
        "git_commit": ms.git_revision(),
        "cuts": entries,
    }
    if os.path.exists(path):
        prior = json.load(open(path))
        if (int(prior["fit_start_ms"]) != int(fit_start)
                or int(prior["fit_end_ms"]) != int(fit_end)):
            raise ValueError(
                f"frozen terciles at {path} were fitted on "
                f"[{prior['fit_start_utc']}, {prior['fit_end_utc_exclusive']}) "
                f"but a fit on [{payload['fit_start_utc']}, "
                f"{payload['fit_end_utc_exclusive']}) was requested. Refusing "
                f"to overwrite: refitting frozen cuts on a different window "
                f"destroys the pre-registration. Delete the file deliberately "
                f"if a refit is genuinely intended.")
        return prior

    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as fh:
        json.dump(payload, fh, indent=2, sort_keys=True)
        fh.write("\n")
    return payload


def load_terciles(path=TERCILES_PATH):
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"frozen terciles missing at {path}; fit them on the "
            f"pre-registered window first")
    return json.load(open(path))


def cuts_for(frozen, symbol, axis, window_days):
    k = _key(symbol, axis, window_days)
    if k not in frozen["cuts"]:
        raise KeyError(f"no frozen cuts for {k}")
    e = frozen["cuts"][k]
    return e["cut_low"], e["cut_high"]


def _utc(ms_ts):
    import datetime as dt
    return dt.datetime.fromtimestamp(
        int(ms_ts) / 1000, dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def tercile_entry(symbol, axis, window_days, cuts, n_fitted):
    return {"symbol": symbol, "axis": axis, "window_days": int(window_days),
            "cut_low": float(cuts[0]), "cut_high": float(cuts[1]),
            "n_fitted": int(n_fitted)}


# ---------------------------------------------------------------------------
# cross-symbol concordance
# ---------------------------------------------------------------------------

def concordance(labelled_by_symbol, axis_col, start_ts=None, end_ts=None):
    """Fraction of bars on which ALL symbols carry the same label.

    The two-of-three rule assumes BTC, ETH and SOL are partially independent
    observations. If all three sit in the same regime cell most of the time,
    "three symbols agree" is closer to one observation repeated three times,
    and two-of-three is weaker evidence than it appears. This puts a number on
    an assumption otherwise taken on faith.

    Bars where any symbol carries no label (warm-up NaN) are excluded from both
    numerator and denominator, and counted separately -- treating an unlabelled
    bar as a disagreement would understate concordance for a reason that has
    nothing to do with the market.

    Returns the fraction, the per-cell counts, and the excluded count.
    """
    if len(labelled_by_symbol) < 2:
        raise ValueError("concordance needs at least two symbols")

    frames = []
    for sym, df in labelled_by_symbol.items():
        d = df[["ts", axis_col]].copy()
        if start_ts is not None:
            d = d[d["ts"] >= start_ts]
        if end_ts is not None:
            d = d[d["ts"] < end_ts]
        frames.append(d.rename(columns={axis_col: sym}).set_index("ts"))

    joined = pd.concat(frames, axis=1, join="inner")
    total_bars = int(len(joined))
    complete = joined.dropna()
    n = int(len(complete))
    excluded = total_bars - n
    if n == 0:
        return {"fraction": float("nan"), "n_bars": 0,
                "n_excluded_unlabelled": excluded, "cells": {}, "agree": 0}

    first = complete.iloc[:, 0]
    agree_mask = np.ones(n, dtype=bool)
    for c in complete.columns[1:]:
        agree_mask &= (complete[c].to_numpy() == first.to_numpy())
    agree = int(agree_mask.sum())

    cells = {}
    for combo, cnt in complete.groupby(list(complete.columns)).size().items():
        key = "|".join(combo) if isinstance(combo, tuple) else str(combo)
        cells[key] = int(cnt)

    return {"fraction": agree / n, "n_bars": n,
            "n_excluded_unlabelled": excluded, "agree": agree, "cells": cells}


# ---------------------------------------------------------------------------
# build -- fit on the pre-registered window, freeze, apply, persist
# ---------------------------------------------------------------------------

def build(symbols=ms.SYMBOLS, window_days=ms.WINDOW_DAYS_PRIMARY,
          fit_start=ms.FIT_START_MS, fit_end=ms.HOLDOUT_START_MS,
          derived_dir=ms.DERIVED, out_dir=ms.REGIME_DIR,
          terciles_path=None, write=True):
    """Measure, fit terciles on the frozen window, label, and persist.

    `fit_end` defaults to the holdout boundary, which is also the hard end of
    what this module is authorised to load. Nothing from 2025 onward is read,
    fitted on, or labelled.
    """
    import datetime as dt

    terciles_path = terciles_path or TERCILES_PATH
    measured, entries = {}, {}

    for sym in symbols:
        df = ms.load_15m(sym, derived_dir, end_ts_exclusive=fit_end)
        m = ms.measure(df, sym, window_days)
        measured[sym] = m
        for axis in AXES:
            cuts = fit_terciles(m[axis], fit_start, fit_end, ts=m["ts"])
            n_fit = int(m[axis][(m["ts"] >= fit_start)
                                & (m["ts"] < fit_end)].notna().sum())
            entries[_key(sym, axis, window_days)] = tercile_entry(
                sym, axis, window_days, cuts, n_fit)

    frozen = freeze_terciles(entries, path=terciles_path,
                             fit_start=fit_start, fit_end=fit_end)

    manifest = {
        "script": "src/regime/labels.py:build",
        "git_commit": ms.git_revision(),
        "run_utc": dt.datetime.now(dt.timezone.utc).strftime(
            "%Y-%m-%dT%H:%M:%SZ"),
        "compression": f"{ms.COMPRESSION}:{ms.COMPRESSION_LEVEL}",
        "window_days": int(window_days),
        "warmup_bars": ms.warmup_bars(window_days),
        "fit_start_utc": _utc(fit_start),
        "fit_end_utc_exclusive": _utc(fit_end),
        "holdout_start_utc": _utc(ms.HOLDOUT_START_MS),
        "config": {
            "bars_per_day": ms.BARS_PER_DAY,
            "atr_period": ms.ATR_PERIOD,
            "ema_fast": ms.EMA_FAST, "ema_slow": ms.EMA_SLOW,
            "stop_min_pct": {s: ms.stop_min_pct(s) for s in symbols},
        },
        "outputs": {},
    }

    for sym in symbols:
        m = measured[sym]
        m["m_star_label"] = apply_terciles(
            m["m_star"], cuts_for(frozen, sym, "m_star", window_days))
        m["efficiency_label"] = apply_terciles(
            m["efficiency_ratio"],
            cuts_for(frozen, sym, "efficiency_ratio", window_days))
        if write:
            path = os.path.join(out_dir, f"{sym}.parquet")
            nbytes = ms.write_parquet(m, path)
            manifest["outputs"][os.path.relpath(path, ms.ROOT)] = {
                "rows": int(len(m)),
                "bytes": int(nbytes),
                "nan_rows": {c: int(m[c].isna().sum())
                             for c in ms.MEASURE_COLS},
                "first_ts": int(m["ts"].iloc[0]),
                "last_ts": int(m["ts"].iloc[-1]),
            }

    if write:
        os.makedirs(out_dir, exist_ok=True)
        with open(os.path.join(out_dir, "_manifest.json"), "w") as fh:
            json.dump(manifest, fh, indent=2, sort_keys=True)
            fh.write("\n")
    return measured, frozen, manifest


if __name__ == "__main__":
    measured, frozen, manifest = build()
    ms.log(f"[regime] window {manifest['window_days']}d  "
           f"warmup {manifest['warmup_bars']} bars")
    for rel, meta in sorted(manifest["outputs"].items()):
        ms.log(f"  {rel}: {meta['rows']} rows, {meta['bytes']} bytes")
    ms.log(f"[terciles] {TERCILES_PATH}")
