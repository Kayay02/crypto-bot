"""Funding snapshot + Binance-proxy validation.

PART A — snapshot Bitget's full available funding history (pageNo 1-3 per
  symbol) to data/raw/bitget_funding/ before it ages out of the 90-day window.
PART B — pull Binance funding history (2022-01-01 -> now) to
  data/raw/binance_funding/, then analyze coverage, magnitude, and whether
  Binance funding is a reliable proxy for Bitget funding.

Does NOT touch data/raw/bitget_1m/ or the running 1m backfill. requests only,
no ccxt. No cleaning, no derived layer, no strategy code. Writes raw snapshots
(append-only provenance) + a read-only report to reports/probe_funding3.txt.

Run:  python -u src/data/probe_funding3.py
"""

import json
import os
import sys
import time
from collections import Counter
from datetime import datetime, timezone

import numpy as np
import pandas as pd
import requests

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, _REPO_ROOT)

from config import settings  # noqa: E402

BITGET_EP = settings.BASE_URL + "/api/v2/mix/market/history-fund-rate"
BINANCE_EP = "https://fapi.binance.com/fapi/v1/fundingRate"
MIN_INTERVAL = 1.0 / settings.MAX_REQUESTS_PER_SECOND
SYMBOLS = ["BTCUSDT", "ETHUSDT", "SOLUSDT"]

BITGET_FUND_DIR = os.path.join(_REPO_ROOT, "data", "raw", "bitget_funding")
BINANCE_FUND_DIR = os.path.join(_REPO_ROOT, "data", "raw", "binance_funding")
REPORTS_DIR = os.path.join(_REPO_ROOT, "reports")

EIGHT_H = 28_800_000

_BUF = []
_last_request_ts = 0.0


def out(line=""):
    print(line, flush=True)
    _BUF.append(str(line))


def section(t):
    out("\n" + "=" * 78)
    out(t)
    out("=" * 78)


def utc_iso(ms):
    return datetime.fromtimestamp(int(ms) / 1000, tz=timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%S.%fZ"
    )


def stamp():
    return datetime.now(timezone.utc).isoformat()


def _throttle():
    global _last_request_ts
    wait = MIN_INTERVAL - (time.monotonic() - _last_request_ts)
    if wait > 0:
        time.sleep(wait)
    _last_request_ts = time.monotonic()


def _get(url, params):
    _throttle()
    resp = requests.get(url, params=params, timeout=30)
    try:
        body = resp.json()
    except ValueError:
        body = {"_non_json": resp.text}
    return resp, body


def append_jsonl(path, record):
    with open(path, "a") as fh:
        fh.write(json.dumps(record) + "\n")
        fh.flush()
        os.fsync(fh.fileno())


# ------------------------------------------------------------------ PART A
def part_a():
    section("PART A — SNAPSHOT BITGET FUNDING (pageNo 1-3 per symbol)")
    os.makedirs(BITGET_FUND_DIR, exist_ok=True)
    bitget_by_symbol = {}
    for sym in SYMBOLS:
        path = os.path.join(BITGET_FUND_DIR, f"{sym}_funding.jsonl")
        open(path, "w").close()  # fresh snapshot file
        recs = {}
        for page in (1, 2, 3):
            params = {"symbol": sym, "productType": settings.PRODUCT_TYPE,
                      "pageSize": "100", "pageNo": str(page)}
            resp, body = _get(BITGET_EP, params)
            code = body.get("code") if isinstance(body, dict) else None
            data = body.get("data") if isinstance(body, dict) else None
            rows = data if isinstance(data, list) else []
            append_jsonl(path, {
                "fetched_at_utc": stamp(),
                "request": {"url": resp.url, "params": params},
                "http_status": resp.status_code,
                "api_code": code,
                "response": rows,
            })
            for r in rows:
                recs[int(r["fundingTime"])] = float(r["fundingRate"])
        bitget_by_symbol[sym] = recs
        if recs:
            ts = sorted(recs)
            out(f"  {sym}: {len(recs)} records  {utc_iso(ts[0])} .. "
                f"{utc_iso(ts[-1])}  -> {os.path.relpath(path, _REPO_ROOT)}")
        else:
            out(f"  {sym}: 0 records")
    return bitget_by_symbol


# ------------------------------------------------------------------ PART B pull
def part_b_pull():
    section("PART B — PULL BINANCE FUNDING (2022-01-01 -> now)")
    os.makedirs(BINANCE_FUND_DIR, exist_ok=True)
    start_ms = int(datetime(2022, 1, 1, tzinfo=timezone.utc).timestamp() * 1000)
    now_ms = int(time.time() * 1000)

    # Verify time-range support with one bounded probe call first.
    probe_end = start_ms + 30 * 24 * 3600 * 1000
    resp, body = _get(BINANCE_EP, {"symbol": "BTCUSDT", "startTime": start_ms,
                                   "endTime": probe_end, "limit": 1000})
    if isinstance(body, list) and body:
        pr = sorted(int(x["fundingTime"]) for x in body)
        honored = pr[0] <= probe_end and pr[-1] >= start_ms
        out(f"  time-range verify (BTC, Jan-2022 window): {len(body)} recs, "
            f"{utc_iso(pr[0])} .. {utc_iso(pr[-1])} -> honored: {honored}")
    else:
        out(f"  time-range verify returned unexpected: {str(body)[:200]}")

    binance_by_symbol = {}
    for sym in SYMBOLS:
        path = os.path.join(BINANCE_FUND_DIR, f"{sym}_funding.jsonl")
        open(path, "w").close()
        recs = {}
        cursor = start_ms
        prev_newest = None
        pages = 0
        halted = False
        while cursor < now_ms and pages < 12:
            params = {"symbol": sym, "startTime": cursor, "endTime": now_ms,
                      "limit": 1000}
            resp, body = _get(BINANCE_EP, params)
            if not isinstance(body, list):
                out(f"  {sym}: non-list response, stopping: {str(body)[:200]}")
                break
            append_jsonl(path, {
                "fetched_at_utc": stamp(),
                "request": {"url": resp.url, "params": params},
                "http_status": resp.status_code,
                "response": body,
            })
            pages += 1
            if not body:
                break
            ts = sorted(int(x["fundingTime"]) for x in body)
            newest = ts[-1]
            # Anti-loop rail.
            if prev_newest is not None and newest <= prev_newest:
                out(f"  {sym}: ANTI-LOOP HALT — newest ts did not increase "
                    f"(prev {utc_iso(prev_newest)}, now {utc_iso(newest)})")
                halted = True
                break
            prev_newest = newest
            for x in body:
                recs[int(x["fundingTime"])] = float(x["fundingRate"])
            if len(body) < 1000:
                break
            cursor = newest + 1
        binance_by_symbol[sym] = recs
        tsr = sorted(recs)
        out(f"  {sym}: {len(recs)} records over {pages} pages  "
            f"{utc_iso(tsr[0])} .. {utc_iso(tsr[-1])}"
            f"{'  [HALTED]' if halted else ''}")
    return binance_by_symbol


# ------------------------------------------------------------------ analysis
def to_series(recs):
    s = pd.Series(recs, dtype=float).sort_index()
    s.index = s.index.astype("int64")
    return s


def b1_coverage(binance):
    section("B1 — BINANCE COVERAGE & INTERVAL")
    out("  NOTE: Binance settlement timestamps carry up to ~30 ms of jitter "
        "around the exact boundary; gaps are bucketed to the nearest hour so "
        "genuine interval changes are separated from that sub-second noise.")
    HOUR = 3_600_000
    for sym in SYMBOLS:
        s = to_series(binance[sym])
        ts = s.index.to_numpy()
        diffs = np.diff(ts)
        # Bucket each gap to the nearest whole hour.
        buckets = np.round(diffs / HOUR).astype(int)
        dist = Counter(int(b) for b in buckets)
        out(f"\n[{sym}] {len(s)} records  {utc_iso(ts[0])} .. {utc_iso(ts[-1])}")
        out(f"  gap distribution (hours -> count): "
            f"{dict(sorted(dist.items()))}")
        # max raw jitter off the nearest hour boundary.
        jitter = int(np.max(np.abs(diffs - buckets * HOUR)))
        out(f"  max deviation from exact hour boundary: {jitter} ms")
        non8 = {k: v for k, v in dist.items() if k != 8}
        if non8:
            out(f"  interval DIFFERED from 8h (bucketed): {non8}")
            for h in sorted(non8):
                idx = np.where(buckets == h)[0]
                out(f"    {h}h interval: count {len(idx)}, "
                    f"first {utc_iso(ts[idx[0]])}, last {utc_iso(ts[idx[-1]+1])}")
        else:
            out("  interval NEVER differed from 8h (all gaps ~8h).")


def b2_magnitude(binance):
    section("B2 — WAS BINANCE FUNDING EVER LARGE?")
    for sym in SYMBOLS:
        s = to_series(binance[sym])
        a = s.abs()
        n = len(s)
        out(f"\n[{sym}] n={n}")
        out(f"  min={s.min():.8f}  max={s.max():.8f}  mean={s.mean():.8f}  "
            f"median={s.median():.8f}")
        for thr in (0.0002, 0.0005, 0.001):
            c = int((a > thr).sum())
            out(f"  |rate| > {thr}: {c} ({100.0*c/n:.3f}%)")
        out("  20 largest |rate| with dates:")
        top = s.reindex(a.sort_values(ascending=False).index).head(20)
        for tsv, rate in top.items():
            out(f"    {utc_iso(tsv)}  {rate:+.8f}")
        # monthly mean & max abs.
        df = pd.DataFrame({"rate": s.values},
                          index=pd.to_datetime(s.index, unit="ms", utc=True))
        df["absr"] = df["rate"].abs()
        g = df.groupby(df.index.strftime("%Y-%m")).agg(
            mean_abs=("absr", "mean"), max_abs=("absr", "max"))
        out("  MONTHLY mean|rate| / max|rate|:")
        for month, r in g.iterrows():
            out(f"    {month}  mean={r['mean_abs']:.8f}  max={r['max_abs']:.8f}")


def b3_proxy(bitget, binance):
    section("B3 — PROXY VALIDATION (Bitget vs Binance, overlap window)")
    for sym in SYMBOLS:
        bg = to_series(bitget[sym])
        bn = to_series(binance[sym])
        common = bg.index.intersection(bn.index)
        out(f"\n[{sym}] matched settlements: {len(common)}")
        if len(common) < 3:
            out("  too few matched points to validate.")
            continue
        x = bg.loc[common]
        y = bn.loc[common]
        corr = float(np.corrcoef(x.values, y.values)[0, 1])
        mad = float((x - y).abs().mean())
        denom = float(x.abs().mean())
        pct = 100.0 * mad / denom if denom else float("nan")
        sign_disagree = int((np.sign(x.values) != np.sign(y.values)).sum())
        out(f"  overlap range {utc_iso(common.min())} .. {utc_iso(common.max())}")
        out(f"  Pearson correlation           : {corr:.4f}")
        out(f"  mean abs difference            : {mad:.8f}")
        out(f"  as % of mean|Bitget rate|      : {pct:.2f}%  "
            f"(mean|Bitget|={denom:.8f})")
        out(f"  sign disagreements             : {sign_disagree}/{len(common)}")
        diff = (x - y).abs().sort_values(ascending=False).head(10)
        out("  10 largest divergences (ts | Bitget | Binance | diff):")
        for tsv in diff.index:
            out(f"    {utc_iso(tsv)}  BG {x.loc[tsv]:+.8f}  "
                f"BN {y.loc[tsv]:+.8f}  diff {abs(x.loc[tsv]-y.loc[tsv]):.8f}")


def main():
    os.makedirs(REPORTS_DIR, exist_ok=True)
    out("FUNDING SNAPSHOT + BINANCE PROXY VALIDATION")
    out(f"generated: {stamp()}")
    bitget = part_a()
    binance = part_b_pull()
    b1_coverage(binance)
    b2_magnitude(binance)
    b3_proxy(bitget, binance)
    path = os.path.join(REPORTS_DIR, "probe_funding3.txt")
    with open(path, "w") as fh:
        fh.write("\n".join(_BUF) + "\n")
    out(f"\nReport saved to {path}")


if __name__ == "__main__":
    main()
