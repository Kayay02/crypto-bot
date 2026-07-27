"""Build the derived Parquet layer from the immutable raw JSONL layer.

Read-only with respect to data/raw/. Deterministic and re-runnable: deleting
data/derived/ and re-running reproduces byte-identical Parquet output (the
_manifest.json differs only in its run timestamp).

No indicators, no strategy, no backtest logic. Transport only:
  parse -> dedupe on ts (keep first) -> sort ascending -> slice -> truncate
  -> write Parquet (ZSTD level 3).

Bars are never patched, filled, or corrected. `open` is renamed `open_synth`
because Bitget synthesizes it from the previous close; code that expects a real
open should fail loudly rather than silently consume a synthesized price.
"""

import datetime as dt
import hashlib
import json
import os
import sys

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

SCRIPT_VERSION = "1.0.0"

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RAW = os.path.join(ROOT, "data", "raw")
DERIVED = os.path.join(ROOT, "data", "derived")

SYMBOLS = ["BTCUSDT", "ETHUSDT", "SOLUSDT"]
START_TS = 1640995200000          # 2022-01-01T00:00:00Z
BAR_15M_MS = 900_000
BAR_1M_MS = 60_000
COMPRESSION = "zstd"
COMPRESSION_LEVEL = 3

OHLCV_COLS = ["ts", "open_synth", "high", "low", "close", "volume",
              "quote_volume"]
OHLCV_SCHEMA = pa.schema([
    ("ts", pa.int64()),
    ("open_synth", pa.float64()),
    ("high", pa.float64()),
    ("low", pa.float64()),
    ("close", pa.float64()),
    ("volume", pa.float64()),
    ("quote_volume", pa.float64()),
])
FUNDING_SCHEMA = pa.schema([
    ("ts", pa.int64()),
    ("funding_rate", pa.float64()),
])

# Bars where the 15m aggregate disagrees with the sum/extrema of its own 15
# constituent 1m bars. A Bitget-side artifact (late-reported trades landing in
# the 15m aggregate without 1m backfill). Emitted as a FLAG LIST, never as an
# exclusion filter — Point 4 decides policy after measuring overlap with signal
# bars. `ohlc_flag` marks the rare case where a price field diverges, not just
# volume; those are the only ones that can affect intrabar stop/target logic.
DIVERGENCE_SCHEMA = pa.schema([
    ("symbol", pa.string()),
    ("ts", pa.int64()),
    ("field", pa.string()),
    ("val_15m", pa.float64()),
    ("val_1m", pa.float64()),
    ("rel_err", pa.float64()),
    ("ohlc_flag", pa.bool_()),
])

# Binance klines: 12 fields, kept verbatim as a cross-venue reference series.
BINANCE_COLS = ["open_time", "open", "high", "low", "close", "volume",
                "close_time", "quote_volume", "trades", "taker_buy_base",
                "taker_buy_quote", "ignore"]
BINANCE_SCHEMA = pa.schema([
    ("open_time", pa.int64()),
    ("open", pa.float64()),
    ("high", pa.float64()),
    ("low", pa.float64()),
    ("close", pa.float64()),
    ("volume", pa.float64()),
    ("close_time", pa.int64()),
    ("quote_volume", pa.float64()),
    ("trades", pa.int64()),
    ("taker_buy_base", pa.float64()),
    ("taker_buy_quote", pa.float64()),
    ("ignore", pa.float64()),
])


# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------

def log(msg):
    print(msg, flush=True)


def utc_iso(ms):
    if ms is None or (isinstance(ms, float) and np.isnan(ms)):
        return None
    return dt.datetime.fromtimestamp(int(ms) / 1000, dt.timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%SZ")


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def iter_pages(path):
    """Yield the `response` payload of each JSONL page record, in file order."""
    with open(path) as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            yield json.loads(line)["response"]


def raw_path(*parts):
    return os.path.join(RAW, *parts)


# --------------------------------------------------------------------------
# loaders — each returns a deduped, ascending DataFrame
# --------------------------------------------------------------------------

def load_bitget_ohlcv(path):
    """Bitget candle rows: [ts, open, high, low, close, volume, quote_volume].

    Pages descend in time; rows within a page ascend. Seam overlaps repeat a
    bar verbatim, so keep-first on file order is safe and deterministic.
    """
    rows = []
    for resp in iter_pages(path):
        rows.extend(resp)
    if not rows:
        raise RuntimeError(f"no rows in {path}")

    arr = np.array(rows, dtype=object)
    df = pd.DataFrame({
        "ts": arr[:, 0].astype(np.int64),
        "open_synth": arr[:, 1].astype(np.float64),
        "high": arr[:, 2].astype(np.float64),
        "low": arr[:, 3].astype(np.float64),
        "close": arr[:, 4].astype(np.float64),
        "volume": arr[:, 5].astype(np.float64),
        "quote_volume": arr[:, 6].astype(np.float64),
    })
    n_raw = len(df)
    df = df.drop_duplicates(subset="ts", keep="first")
    n_dupes = n_raw - len(df)
    df = df.sort_values("ts", kind="mergesort").reset_index(drop=True)
    return df, n_raw, n_dupes


def load_funding(path, venue):
    """Funding records -> ts (fundingTime) + funding_rate."""
    recs = []
    for resp in iter_pages(path):
        recs.extend(resp)
    df = pd.DataFrame({
        "ts": [int(r["fundingTime"]) for r in recs],
        "funding_rate": [float(r["fundingRate"]) for r in recs],
    })
    n_raw = len(df)
    df = df.drop_duplicates(subset="ts", keep="first")
    n_dupes = n_raw - len(df)
    df = df.sort_values("ts", kind="mergesort").reset_index(drop=True)
    return df, n_raw, n_dupes


def load_binance_reference(path):
    """Binance 15m klines, all 12 fields preserved."""
    rows = []
    for resp in iter_pages(path):
        rows.extend(resp)
    arr = np.array(rows, dtype=object)
    df = pd.DataFrame({
        "open_time": arr[:, 0].astype(np.int64),
        "open": arr[:, 1].astype(np.float64),
        "high": arr[:, 2].astype(np.float64),
        "low": arr[:, 3].astype(np.float64),
        "close": arr[:, 4].astype(np.float64),
        "volume": arr[:, 5].astype(np.float64),
        "close_time": arr[:, 6].astype(np.int64),
        "quote_volume": arr[:, 7].astype(np.float64),
        "trades": arr[:, 8].astype(np.int64),
        "taker_buy_base": arr[:, 9].astype(np.float64),
        "taker_buy_quote": arr[:, 10].astype(np.float64),
        "ignore": arr[:, 11].astype(np.float64),
    })
    n_raw = len(df)
    df = df.drop_duplicates(subset="open_time", keep="first")
    n_dupes = n_raw - len(df)
    df = df.sort_values("open_time", kind="mergesort").reset_index(drop=True)
    return df, n_raw, n_dupes


# --------------------------------------------------------------------------
# reconstruction
# --------------------------------------------------------------------------

RECON_TOL = 1e-9


def _rel_err(x, y):
    denom = np.maximum(np.abs(x), np.abs(y))
    denom = np.where(denom == 0, 1.0, denom)
    return np.abs(x - y) / denom


def reconstruct(df_1m):
    """Aggregate 1m bars into 15m buckets: high/low/close/volume + bar count."""
    a = df_1m[["ts", "high", "low", "close", "volume"]].copy()
    a["bucket"] = (a["ts"] // BAR_15M_MS) * BAR_15M_MS
    g = a.groupby("bucket", sort=True)
    return pd.DataFrame({
        "high": g["high"].max(),
        "low": g["low"].min(),
        "close": g["close"].last(),
        "volume": g["volume"].sum(),
        "n_1m": g.size(),
    })


def divergence_rows(sym, df_15m, rec):
    """One row per (bar, field) that fails the 1e-9 relative tolerance."""
    j = df_15m.set_index("ts").join(rec, how="inner", rsuffix="_r")
    fields = ["high", "low", "close", "volume"]
    errs = {f: _rel_err(j[f].to_numpy(), j[f + "_r"].to_numpy()) for f in fields}
    bad = {f: errs[f] > RECON_TOL for f in fields}
    ohlc_bad = bad["high"] | bad["low"] | bad["close"]

    out = []
    for f in fields:
        idx = np.nonzero(bad[f])[0]
        if not len(idx):
            continue
        out.append(pd.DataFrame({
            "symbol": sym,
            "ts": j.index.to_numpy()[idx],
            "field": f,
            "val_15m": j[f].to_numpy()[idx],
            "val_1m": j[f + "_r"].to_numpy()[idx],
            "rel_err": errs[f][idx],
            "ohlc_flag": ohlc_bad[idx],
        }))
    if not out:
        return pd.DataFrame(columns=[f.name for f in DIVERGENCE_SCHEMA])
    return pd.concat(out, ignore_index=True)


# --------------------------------------------------------------------------
# writer
# --------------------------------------------------------------------------

def write_parquet(df, schema, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    table = pa.Table.from_pandas(df, schema=schema, preserve_index=False)
    pq.write_table(
        table, path,
        compression=COMPRESSION,
        compression_level=COMPRESSION_LEVEL,
        # Fixed row-group sizing keeps output byte-stable across runs.
        row_group_size=256 * 1024,
        version="2.6",
        store_schema=False,
    )
    return os.path.getsize(path)


# --------------------------------------------------------------------------
# build
# --------------------------------------------------------------------------

def main():
    run_ts = dt.datetime.now(dt.timezone.utc).isoformat()
    log("=" * 78)
    log(f"BUILD DERIVED LAYER  v{SCRIPT_VERSION}   {run_ts}")
    log("=" * 78)

    manifest = {
        "script": "src/data/build_derived.py",
        "script_version": SCRIPT_VERSION,
        "run_utc": run_ts,
        "start_ts_filter": START_TS,
        "start_utc_filter": utc_iso(START_TS),
        "compression": f"{COMPRESSION}:{COMPRESSION_LEVEL}",
        "outputs": {},
    }

    # ---- load every OHLCV series -----------------------------------------
    log("\n[load] bitget OHLCV")
    m15, m1 = {}, {}
    load_stats = {}
    for sym in SYMBOLS:
        p = raw_path("bitget", f"{sym}_15m.jsonl")
        df, n_raw, n_dupes = load_bitget_ohlcv(p)
        m15[sym] = df
        load_stats[("15m", sym)] = (p, n_raw, n_dupes)
        log(f"  15m {sym}: raw rows {n_raw:>9,}  dupes dropped {n_dupes:>6,}  "
            f"-> {len(df):>9,}")
    for sym in SYMBOLS:
        p = raw_path("bitget_1m", f"{sym}_1m.jsonl")
        df, n_raw, n_dupes = load_bitget_ohlcv(p)
        m1[sym] = df
        load_stats[("1m", sym)] = (p, n_raw, n_dupes)
        log(f"  1m  {sym}: raw rows {n_raw:>9,}  dupes dropped {n_dupes:>6,}  "
            f"-> {len(df):>9,}")

    # ---- common end ------------------------------------------------------
    # Floor to a 15m boundary, and require the closing 15m bar to be fully
    # covered by every 1m series so V3 can reconstruct every 15m bar.
    end_15m = min(int(m15[s]["ts"].max()) for s in SYMBOLS)
    end_1m = min(int(m1[s]["ts"].max()) for s in SYMBOLS)
    cand_a = (end_15m // BAR_15M_MS) * BAR_15M_MS
    cand_b = ((end_1m - 14 * BAR_1M_MS) // BAR_15M_MS) * BAR_15M_MS
    common_end = min(cand_a, cand_b)
    end_1m_incl = common_end + 14 * BAR_1M_MS

    log("\n[truncate] common end")
    log(f"  min 15m max ts : {end_15m} ({utc_iso(end_15m)})")
    log(f"  min 1m  max ts : {end_1m} ({utc_iso(end_1m)})")
    log(f"  COMMON END 15m : {common_end} ({utc_iso(common_end)})")
    log(f"  COMMON END 1m  : {end_1m_incl} ({utc_iso(end_1m_incl)})  "
        f"(closing 15m bar fully covered)")
    manifest["common_end_ts_15m"] = common_end
    manifest["common_end_utc_15m"] = utc_iso(common_end)
    manifest["common_end_ts_1m"] = end_1m_incl
    manifest["common_end_utc_1m"] = utc_iso(end_1m_incl)

    def slice_series(df, end_ts):
        out = df[(df["ts"] >= START_TS) & (df["ts"] <= end_ts)]
        return out.reset_index(drop=True)

    for sym in SYMBOLS:
        m15[sym] = slice_series(m15[sym], common_end)
        m1[sym] = slice_series(m1[sym], end_1m_incl)

    # ---- write 15m -------------------------------------------------------
    log("\n[write] ohlcv_15m")
    for sym in SYMBOLS:
        df = m15[sym][OHLCV_COLS]
        out = os.path.join(DERIVED, "ohlcv_15m", f"{sym}.parquet")
        size = write_parquet(df, OHLCV_SCHEMA, out)
        src, n_raw, n_dupes = load_stats[("15m", sym)]
        manifest["outputs"][os.path.relpath(out, ROOT)] = {
            "sources": [{"path": os.path.relpath(src, ROOT),
                         "sha256": sha256_file(src)}],
            "rows": int(len(df)),
            "ts_min": int(df["ts"].iloc[0]),
            "ts_max": int(df["ts"].iloc[-1]),
            "utc_min": utc_iso(df["ts"].iloc[0]),
            "utc_max": utc_iso(df["ts"].iloc[-1]),
            "raw_rows": n_raw,
            "duplicate_ts_dropped": n_dupes,
            "bytes": size,
        }
        log(f"  {sym}: {len(df):>9,} rows  {size/1e6:7.2f} MB  {out}")

    # ---- write 1m (hive partitioned by symbol/year) -----------------------
    log("\n[write] ohlcv_1m (hive: symbol=/year=)")
    for sym in SYMBOLS:
        df = m1[sym]
        years = pd.to_datetime(df["ts"], unit="ms", utc=True).dt.year
        src, n_raw, n_dupes = load_stats[("1m", sym)]
        src_sha = sha256_file(src)
        for year in sorted(years.unique()):
            part = df[years == year][OHLCV_COLS].reset_index(drop=True)
            out = os.path.join(DERIVED, "ohlcv_1m", f"symbol={sym}",
                               f"year={year}", "data.parquet")
            size = write_parquet(part, OHLCV_SCHEMA, out)
            manifest["outputs"][os.path.relpath(out, ROOT)] = {
                "sources": [{"path": os.path.relpath(src, ROOT),
                             "sha256": src_sha}],
                "rows": int(len(part)),
                "ts_min": int(part["ts"].iloc[0]),
                "ts_max": int(part["ts"].iloc[-1]),
                "utc_min": utc_iso(part["ts"].iloc[0]),
                "utc_max": utc_iso(part["ts"].iloc[-1]),
                "raw_rows": n_raw,
                "duplicate_ts_dropped": n_dupes,
                "bytes": size,
            }
            log(f"  {sym} {year}: {len(part):>9,} rows  {size/1e6:7.2f} MB")

    # ---- funding ---------------------------------------------------------
    # Funding is not an OHLCV series: no 2022 slice, no common-end truncation.
    log("\n[write] funding")
    for venue, subdir in (("bitget", "bitget_funding"),
                          ("binance", "binance_funding")):
        for sym in SYMBOLS:
            src = raw_path(subdir, f"{sym}_funding.jsonl")
            df, n_raw, n_dupes = load_funding(src, venue)
            out = os.path.join(DERIVED, "funding", venue, f"{sym}.parquet")
            size = write_parquet(df, FUNDING_SCHEMA, out)
            manifest["outputs"][os.path.relpath(out, ROOT)] = {
                "sources": [{"path": os.path.relpath(src, ROOT),
                             "sha256": sha256_file(src)}],
                "rows": int(len(df)),
                "ts_min": int(df["ts"].iloc[0]),
                "ts_max": int(df["ts"].iloc[-1]),
                "utc_min": utc_iso(df["ts"].iloc[0]),
                "utc_max": utc_iso(df["ts"].iloc[-1]),
                "raw_rows": n_raw,
                "duplicate_ts_dropped": n_dupes,
                "bytes": size,
            }
            log(f"  {venue:7s} {sym}: {len(df):>6,} rows  {size/1e3:7.1f} KB")

    # ---- binance reference ----------------------------------------------
    log("\n[write] reference")
    src = raw_path("binance", "BTCUSDT_15m.jsonl")
    df, n_raw, n_dupes = load_binance_reference(src)
    out = os.path.join(DERIVED, "reference", "binance_15m_BTCUSDT.parquet")
    size = write_parquet(df[BINANCE_COLS], BINANCE_SCHEMA, out)
    manifest["outputs"][os.path.relpath(out, ROOT)] = {
        "sources": [{"path": os.path.relpath(src, ROOT),
                     "sha256": sha256_file(src)}],
        "rows": int(len(df)),
        "ts_min": int(df["open_time"].iloc[0]),
        "ts_max": int(df["open_time"].iloc[-1]),
        "utc_min": utc_iso(df["open_time"].iloc[0]),
        "utc_max": utc_iso(df["open_time"].iloc[-1]),
        "raw_rows": n_raw,
        "duplicate_ts_dropped": n_dupes,
        "bytes": size,
    }
    log(f"  binance 15m BTCUSDT: {len(df):>9,} rows  {size/1e6:7.2f} MB")

    # ---- reconstruction divergence flags ---------------------------------
    # Flag list only. Nothing is excluded, filtered, or corrected here.
    log("\n[write] flags/reconstruction_divergence")
    recs = {sym: reconstruct(m1[sym]) for sym in SYMBOLS}
    div = pd.concat([divergence_rows(sym, m15[sym], recs[sym])
                     for sym in SYMBOLS], ignore_index=True)
    div = div.sort_values(["symbol", "ts", "field"],
                          kind="mergesort").reset_index(drop=True)
    out = os.path.join(DERIVED, "flags", "reconstruction_divergence.parquet")
    size = write_parquet(div, DIVERGENCE_SCHEMA, out)
    n_bars = int(div["ts"].nunique()) if len(div) else 0
    n_ohlc = int(div["ohlc_flag"].sum()) if len(div) else 0
    manifest["outputs"][os.path.relpath(out, ROOT)] = {
        "sources": [{"path": os.path.relpath(raw_path("bitget", f"{s}_15m.jsonl"),
                                             ROOT),
                     "sha256": sha256_file(raw_path("bitget",
                                                    f"{s}_15m.jsonl"))}
                    for s in SYMBOLS]
        + [{"path": os.path.relpath(raw_path("bitget_1m", f"{s}_1m.jsonl"),
                                    ROOT),
            "sha256": sha256_file(raw_path("bitget_1m", f"{s}_1m.jsonl"))}
           for s in SYMBOLS],
        "rows": int(len(div)),
        "distinct_bars_flagged": n_bars,
        "ohlc_flagged_rows": n_ohlc,
        "ts_min": int(div["ts"].min()) if len(div) else None,
        "ts_max": int(div["ts"].max()) if len(div) else None,
        "utc_min": utc_iso(div["ts"].min()) if len(div) else None,
        "utc_max": utc_iso(div["ts"].max()) if len(div) else None,
        "tolerance": RECON_TOL,
        "semantics": "flag list, NOT an exclusion filter",
        "bytes": size,
    }
    log(f"  rows {len(div)}  distinct bars {n_bars}  ohlc-flagged {n_ohlc}  "
        f"{size/1e3:.1f} KB")

    # ---- manifest --------------------------------------------------------
    mpath = os.path.join(DERIVED, "_manifest.json")
    os.makedirs(DERIVED, exist_ok=True)
    with open(mpath, "w") as fh:
        json.dump(manifest, fh, indent=2, sort_keys=True)
        fh.write("\n")
    log(f"\n[manifest] {mpath}  ({len(manifest['outputs'])} outputs)")

    return m15, m1, manifest, div


# --------------------------------------------------------------------------
# verification gate
# --------------------------------------------------------------------------

def verify(m15, m1, div):
    failures = []

    def hdr(t):
        log("\n" + "=" * 78)
        log(t)
        log("=" * 78)

    # V1 -------------------------------------------------------------------
    hdr("V1  FULL 1m CONTIGUITY (60000 ms)")
    for sym in SYMBOLS:
        ts = m1[sym]["ts"].to_numpy()
        d = np.diff(ts)
        bad = np.nonzero(d != BAR_1M_MS)[0]
        log(f"  {sym}: bars {len(ts):>9,}  "
            f"{utc_iso(ts[0])} .. {utc_iso(ts[-1])}  gaps {len(bad)}")
        for i in bad:
            log(f"    GAP {utc_iso(ts[i])} -> {utc_iso(ts[i+1])}  "
                f"{d[i]} ms ({d[i]/60000:.1f} min)")
        if len(bad):
            failures.append(f"V1 {sym}: {len(bad)} gaps")

    # V2 -------------------------------------------------------------------
    hdr("V2  FULL 15m CONTIGUITY (900000 ms)")
    for sym in SYMBOLS:
        ts = m15[sym]["ts"].to_numpy()
        d = np.diff(ts)
        bad = np.nonzero(d != BAR_15M_MS)[0]
        log(f"  {sym}: bars {len(ts):>9,}  "
            f"{utc_iso(ts[0])} .. {utc_iso(ts[-1])}  gaps {len(bad)}")
        for i in bad:
            log(f"    GAP {utc_iso(ts[i])} -> {utc_iso(ts[i+1])}  "
                f"{d[i]} ms ({d[i]/60000:.1f} min)")
        if len(bad):
            failures.append(f"V2 {sym}: {len(bad)} gaps")

    # V3 -------------------------------------------------------------------
    # STRUCTURAL coverage is a hard gate: every 15m bar must be backed by
    # exactly 15 1m bars, because intrabar stop-vs-target ordering depends on
    # it. VALUE divergence is a known Bitget-side artifact, so it is reported
    # and flagged, not treated as a build failure — the exclude/keep policy is
    # a Point 4 decision, taken after measuring overlap with signal bars.
    hdr("V3  RECONSTRUCTION 15m from 1m")
    for sym in SYMBOLS:
        rec = reconstruct(m1[sym])
        ref = m15[sym].set_index("ts")
        joined = ref.join(rec, how="inner", rsuffix="_r")
        checked = len(joined)
        missing = len(ref) - checked
        wrong_n = int((joined["n_1m"].to_numpy() != 15).sum())

        d = div[div["symbol"] == sym]
        bars_flagged = int(d["ts"].nunique()) if len(d) else 0
        ohlc_bars = int(d[d["ohlc_flag"]]["ts"].nunique()) if len(d) else 0
        vol_bars = bars_flagged - ohlc_bars

        log(f"  {sym}: 15m bars {len(ref):>8,}  checked {checked:>8,}  "
            f"exact {checked - bars_flagged:>8,}  flagged {bars_flagged:>5,}  "
            f"(volume-only {vol_bars}, OHLC {ohlc_bars})")
        log(f"       structural: no-1m-coverage {missing}, n_1m!=15 {wrong_n}  "
            f"{'PASS' if not (missing or wrong_n) else 'FAIL'}")
        if missing:
            failures.append(f"V3 {sym}: {missing} 15m bars lack 1m coverage")
        if wrong_n:
            failures.append(f"V3 {sym}: {wrong_n} bars with n_1m != 15")
        for _, r in d[d["ohlc_flag"]].iterrows():
            log(f"    OHLC-FLAG {utc_iso(r['ts'])} {r['field']}: "
                f"15m {r['val_15m']} vs 1m {r['val_1m']}  "
                f"rel_err {r['rel_err']:.3e}")
    log(f"\n  divergence flag list -> "
        f"data/derived/flags/reconstruction_divergence.parquet "
        f"({len(div)} rows). Flag list, NOT an exclusion filter.")

    # V4 -------------------------------------------------------------------
    hdr("V4  NO DUPLICATE ts; ts STRICTLY INCREASING")
    for label, store in (("15m", m15), ("1m", m1)):
        for sym in SYMBOLS:
            ts = store[sym]["ts"].to_numpy()
            dupes = len(ts) - len(np.unique(ts))
            mono = bool(np.all(np.diff(ts) > 0))
            ok = dupes == 0 and mono
            log(f"  {label:3s} {sym}: duplicates {dupes}  "
                f"strictly_increasing {mono}  {'PASS' if ok else 'FAIL'}")
            if not ok:
                failures.append(f"V4 {label} {sym}")

    # V5 -------------------------------------------------------------------
    hdr("V5  high >= low, high >= close, low <= close  (open_synth NOT checked)")
    for label, store in (("15m", m15), ("1m", m1)):
        for sym in SYMBOLS:
            d = store[sym]
            v1 = int((d["high"] < d["low"]).sum())
            v2 = int((d["high"] < d["close"]).sum())
            v3 = int((d["low"] > d["close"]).sum())
            ok = (v1 + v2 + v3) == 0
            log(f"  {label:3s} {sym}: high<low {v1}  high<close {v2}  "
                f"low>close {v3}  {'PASS' if ok else 'FAIL'}")
            if not ok:
                failures.append(f"V5 {label} {sym}")

    # V6 -------------------------------------------------------------------
    hdr("V6  COMMON END CONSISTENCY")
    ends15 = {s: int(m15[s]["ts"].iloc[-1]) for s in SYMBOLS}
    ends1 = {s: int(m1[s]["ts"].iloc[-1]) for s in SYMBOLS}
    starts15 = {s: int(m15[s]["ts"].iloc[0]) for s in SYMBOLS}
    starts1 = {s: int(m1[s]["ts"].iloc[0]) for s in SYMBOLS}
    for s in SYMBOLS:
        log(f"  {s}: 15m {utc_iso(starts15[s])} .. {utc_iso(ends15[s])} | "
            f"1m {utc_iso(starts1[s])} .. {utc_iso(ends1[s])}")
    same15 = len(set(ends15.values())) == 1
    same1 = len(set(ends1.values())) == 1
    e15 = next(iter(ends15.values()))
    e1 = next(iter(ends1.values()))
    consistent = same15 and same1 and (e1 == e15 + 14 * BAR_1M_MS)
    log(f"  identical 15m end across symbols : {same15}")
    log(f"  identical 1m  end across symbols : {same1}")
    log(f"  1m end == 15m end + 14min        : {e1 == e15 + 14 * BAR_1M_MS} "
        f"(last 15m bar fully covered)")
    log(f"  {'PASS' if consistent else 'FAIL'}")
    if not consistent:
        failures.append("V6 end mismatch")

    # V7 -------------------------------------------------------------------
    hdr("V7  ROW COUNTS VS EXPECTED")
    EXP_1M, EXP_15M = 2_402_900, 160_100
    for sym in SYMBOLS:
        n1, n15 = len(m1[sym]), len(m15[sym])
        log(f"  {sym}: 1m {n1:>9,} (exp ~{EXP_1M:,}, delta {n1-EXP_1M:+,})   "
            f"15m {n15:>8,} (exp ~{EXP_15M:,}, delta {n15-EXP_15M:+,})")
    log("  (informational — expected counts are approximate)")

    return failures


if __name__ == "__main__":
    m15, m1, manifest, div = main()
    fails = verify(m15, m1, div)
    log("\n" + "=" * 78)
    if fails:
        log("VERIFICATION GATE: FAIL")
        for f in fails:
            log("  " + f)
        log("=" * 78)
        sys.exit(1)
    log("VERIFICATION GATE: PASS (V1-V7)")
    log("=" * 78)
