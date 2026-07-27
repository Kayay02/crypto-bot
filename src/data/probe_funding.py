"""READ-ONLY probe of the Bitget history-fund-rate endpoint.

Characterizes the funding-rate feed before any backfill is designed:
  T1 — response shape / field meanings / max pageSize.
  T2 — timestamp semantics, settlement interval, backward vs forward looking.
  T3 — interval stability across symbols and time; retention depth.
  T4 — sign convention and magnitude (decimal fraction vs percentage).

Pagination here is pageNo/pageSize (NOT the candles endTime cursor). No
assumptions from the candle mechanics are carried over.

HARD CONSTRAINT: read-only. Does NOT touch data/raw/bitget_1m/ or the running
backfill. No backfill, no derived layer, no cleaning, no strategy code. Max 12
API requests. Raw responses -> data/raw/probe_funding/; report ->
reports/probe_funding.txt.

Run:  python -u src/data/probe_funding.py
"""

import json
import os
import statistics
import sys
import time
from datetime import datetime, timezone

import requests

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, _REPO_ROOT)

from config import settings  # noqa: E402

ENDPOINT = settings.BASE_URL + "/api/v2/mix/market/history-fund-rate"
MIN_INTERVAL = 1.0 / settings.MAX_REQUESTS_PER_SECOND
RAW_DIR = os.path.join(_REPO_ROOT, "data", "raw", "probe_funding")
REPORTS_DIR = os.path.join(_REPO_ROOT, "reports")
SYMBOLS = ["BTCUSDT", "ETHUSDT", "SOLUSDT"]

_BUF = []
_last_request_ts = 0.0
_request_count = 0


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


def _throttle():
    global _last_request_ts
    wait = MIN_INTERVAL - (time.monotonic() - _last_request_ts)
    if wait > 0:
        time.sleep(wait)
    _last_request_ts = time.monotonic()


def fetch(label, symbol, page_size, page_no):
    global _request_count
    if _request_count >= 12:
        raise RuntimeError("API request budget (12) exhausted.")
    _throttle()
    _request_count += 1
    params = {
        "symbol": symbol,
        "productType": settings.PRODUCT_TYPE,
        "pageSize": str(page_size),
        "pageNo": str(page_no),
    }
    resp = requests.get(ENDPOINT, params=params, timeout=30)
    try:
        body = resp.json()
    except ValueError:
        body = {"_non_json": resp.text}
    os.makedirs(RAW_DIR, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S_%f")
    with open(os.path.join(RAW_DIR, f"{stamp}_{label}_{symbol}.json"), "w") as fh:
        json.dump({"request": {"url": resp.url, "params": params},
                   "http_status": resp.status_code, "response": body},
                  fh, indent=2)
    code = body.get("code") if isinstance(body, dict) else None
    data = body.get("data") if isinstance(body, dict) else None
    rows = data if isinstance(data, list) else []
    return resp.status_code, code, body, rows


def _ts_field(rec):
    """Funding settlement timestamp field (ms) — name confirmed in T1."""
    for k in ("fundingTime", "settleTime", "ts"):
        if k in rec:
            return int(rec[k])
    raise KeyError(f"no timestamp field in {rec}")


def _rate_field(rec):
    for k in ("fundingRate", "fundRate", "rate"):
        if k in rec:
            return float(rec[k])
    raise KeyError(f"no rate field in {rec}")


def gaps_report(label, recs):
    ts = sorted({_ts_field(r) for r in recs}, reverse=True)
    diffs = [a - b for a, b in zip(ts[:-1], ts[1:])]  # newest-first -> positive
    from collections import Counter
    dist = Counter(diffs)
    out(f"    {label}: {len(recs)} recs, range {utc_iso(ts[-1])} .. "
        f"{utc_iso(ts[0])}")
    out(f"      distinct gaps (ms -> count): "
        f"{ {int(k): int(v) for k, v in sorted(dist.items())} }")
    non8h = {int(k): int(v) for k, v in dist.items() if k != 28800000}
    out(f"      any gap != 28800000ms (8h): "
        f"{'YES ' + str(non8h) if non8h else 'no'}")
    return ts


# ------------------------------------------------------------------ tests
def test1():
    section("TEST 1 — RESPONSE SHAPE")
    status, code, body, rows = fetch("t1_shape", "BTCUSDT", 100, 1)
    out(f"  HTTP {status}  code {code}  records returned: {len(rows)}")
    out("  raw first 3 records (unmodified):")
    out(json.dumps(rows[:3], indent=2))
    if rows:
        out("  field names present and apparent meaning:")
        meanings = {
            "symbol": "trading pair",
            "fundingRate": "funding rate for the settlement (decimal fraction?)",
            "fundingTime": "settlement timestamp (ms epoch)",
        }
        for k in rows[0].keys():
            out(f"    - {k}: {meanings.get(k, 'unknown')}  "
                f"(sample={rows[0][k]!r})")
    # max pageSize probe.
    s100 = len(rows)
    st2, cd2, bd2, r2 = fetch("t1_pagesize200", "BTCUSDT", 200, 1)
    out(f"\n  pageSize=100 -> {s100} records.")
    out(f"  pageSize=200 -> HTTP {st2} code {cd2}, records {len(r2)}  "
        f"(msg={bd2.get('msg') if isinstance(bd2, dict) else None})")
    if len(r2) > s100:
        out(f"  => pageSize=200 accepted (returned {len(r2)}).")
    elif len(r2) == s100:
        out(f"  => pageSize=200 capped at {s100} (200 not honored, no error).")
    else:
        out("  => pageSize=200 behavior differs (see above).")
    return rows


def test2(page1_recs):
    section("TEST 2 — TIMESTAMP SEMANTICS AND INTERVAL")
    ts = sorted({_ts_field(r) for r in page1_recs}, reverse=True)
    out("  2a 20 most recent funding settlement times (UTC):")
    for t in ts[:20]:
        out(f"    {utc_iso(t)}")
    out("  2b consecutive gaps:")
    gaps_report("BTCUSDT page1", page1_recs)
    # 2c schedule alignment.
    hrs = sorted({datetime.fromtimestamp(t/1000, tz=timezone.utc).strftime(
        "%H:%M:%S") for t in ts})
    out(f"  2c distinct times-of-day observed: {hrs}")
    on_grid = all(datetime.fromtimestamp(t/1000, tz=timezone.utc).hour
                  in (0, 8, 16) and
                  datetime.fromtimestamp(t/1000, tz=timezone.utc).minute == 0
                  for t in ts)
    out(f"      all settlements on 00:00/08:00/16:00 UTC exactly: {on_grid}")
    # 2d backward vs forward.
    now = int(time.time() * 1000)
    newest = ts[0]
    rel = "PAST" if newest < now else "FUTURE"
    out(f"  2d newest funding ts = {utc_iso(newest)}; now = {utc_iso(now)}")
    out(f"      newest is in the {rel} "
        f"(delta {(newest - now)/1000/3600:+.2f} h from now).")
    out(f"      CONCLUSION: timestamp is "
        f"{'BACKWARD-looking (a settlement that occurred)' if rel=='PAST' else 'FORWARD-looking (next scheduled settlement)'}.")


def test3():
    section("TEST 3 — INTERVAL STABILITY ACROSS SYMBOLS AND TIME")
    for sym in SYMBOLS:
        out(f"\n[{sym}]")
        _, _, _, recent = fetch("t3_recent", sym, 100, 1)
        ts_r = gaps_report("recent (pageNo=1)", recent)
        _, cd, bd, deep = fetch("t3_deep", sym, 100, 40)
        if deep:
            ts_d = gaps_report("deep (pageNo=40)", deep)
        else:
            out(f"    deep (pageNo=40): no records (code {cd}, "
                f"msg {bd.get('msg') if isinstance(bd, dict) else None})")


def test4(page1_recs):
    section("TEST 4 — SIGN CONVENTION AND MAGNITUDE")

    def summarize(label, recs):
        rates = [_rate_field(r) for r in recs]
        pos = sum(1 for x in rates if x > 0)
        neg = sum(1 for x in rates if x < 0)
        zero = sum(1 for x in rates if x == 0)
        out(f"  [{label}] n={len(rates)}  min={min(rates):.8f}  "
            f"max={max(rates):.8f}  mean={statistics.mean(rates):.8f}  "
            f"median={statistics.median(rates):.8f}")
        out(f"           positive={pos}  negative={neg}  zero={zero}")
        return rates

    rates = summarize("BTCUSDT page1", page1_recs)
    # 4b decimal vs percentage evidence.
    amax = max(abs(x) for x in rates)
    out(f"  4b max abs rate = {amax:.8f}. Typical perp funding is ~0.01% = "
        f"0.0001 as a decimal fraction.")
    if amax < 0.05:
        out(f"      Evidence: magnitudes ~1e-4, far below 1.0 -> expressed as a "
            f"DECIMAL FRACTION (0.0001 = 0.01%), NOT a percentage "
            f"(a percentage would show ~0.01, or values near 1 for 1%).")
    else:
        out("      Evidence: magnitudes are large -> may be a percentage; see "
            "values above.")
    # 4c ETH and SOL (fetch fresh page 1 each).
    for sym in ("ETHUSDT", "SOLUSDT"):
        _, _, _, recs = fetch("t4", sym, 100, 1)
        summarize(f"{sym} page1", recs)


def main():
    os.makedirs(REPORTS_DIR, exist_ok=True)
    out("BITGET FUNDING-RATE PROBE (READ-ONLY — no data modified)")
    out(f"generated: {datetime.now(timezone.utc).isoformat()}")
    page1 = test1()
    test2(page1)
    test3()
    test4(page1)
    out(f"\nTotal API requests made: {_request_count} (budget 12)")
    path = os.path.join(REPORTS_DIR, "probe_funding.txt")
    with open(path, "w") as fh:
        fh.write("\n".join(_BUF) + "\n")
    out(f"Report saved to {path}")


if __name__ == "__main__":
    main()
