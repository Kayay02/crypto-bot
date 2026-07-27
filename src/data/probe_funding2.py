"""READ-ONLY funding-rate probe #2 — pagination depth and time-range support.

  T1 — where does pageNo pagination stop (BTCUSDT)? binary-search the boundary.
  T2 — does history-fund-rate accept startTime/endTime? one 2022 window call.
  T3 — was funding ever large? summary over the deepest records retrieved.

HARD CONSTRAINT: read-only. Does NOT touch data/raw/bitget_1m/ or the running
1m backfill. No backfill, no cleaning, no strategy code. Max 12 API requests.
Raw -> data/raw/probe_funding2/; report -> reports/probe_funding2.txt.

Run:  python -u src/data/probe_funding2.py
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
RAW_DIR = os.path.join(_REPO_ROOT, "data", "raw", "probe_funding2")
REPORTS_DIR = os.path.join(_REPO_ROOT, "reports")

_BUF = []
_last_request_ts = 0.0
_request_count = 0
_ALL_BTC_RECORDS = {}  # ts -> rate, accumulated for T3


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


def fetch(label, extra_params):
    global _request_count
    if _request_count >= 12:
        raise RuntimeError("API request budget (12) exhausted.")
    _throttle()
    _request_count += 1
    params = {"symbol": "BTCUSDT", "productType": settings.PRODUCT_TYPE,
              "pageSize": "100"}
    params.update(extra_params)
    resp = requests.get(ENDPOINT, params=params, timeout=30)
    try:
        body = resp.json()
    except ValueError:
        body = {"_non_json": resp.text}
    os.makedirs(RAW_DIR, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S_%f")
    with open(os.path.join(RAW_DIR, f"{stamp}_{label}.json"), "w") as fh:
        json.dump({"request": {"url": resp.url, "params": params},
                   "http_status": resp.status_code, "response": body},
                  fh, indent=2)
    code = body.get("code") if isinstance(body, dict) else None
    data = body.get("data") if isinstance(body, dict) else None
    rows = data if isinstance(data, list) else []
    for r in rows:  # accumulate BTC records for T3
        _ALL_BTC_RECORDS[int(r["fundingTime"])] = float(r["fundingRate"])
    return resp.status_code, code, body, rows


def _range(rows):
    ts = sorted(int(r["fundingTime"]) for r in rows)
    return ts[0], ts[-1]


# ------------------------------------------------------------------ T1
def test1():
    section("TEST 1 — WHERE DOES pageNo PAGINATION STOP? (BTCUSDT)")
    deepest_with_data = None
    oldest_reached = None
    for pageNo in (2, 3, 4, 5, 10, 20, 30):
        status, code, body, rows = fetch(f"t1_page{pageNo}", {"pageNo": str(pageNo)})
        if rows:
            lo, hi = _range(rows)
            out(f"  pageNo={pageNo:<3} HTTP {status} code {code} recs {len(rows)}  "
                f"{utc_iso(lo)} .. {utc_iso(hi)}")
            deepest_with_data = pageNo
            oldest_reached = lo if oldest_reached is None else min(oldest_reached, lo)
        else:
            out(f"  pageNo={pageNo:<3} HTTP {status} code {code} recs 0  (EMPTY)")

    # Adaptive: tighten the boundary with one or two calls just beyond the
    # deepest page that returned data (pageNo=40 is known empty from probe #1).
    if deepest_with_data is None:
        out("  no page returned data among 5/10/20/30 — nothing to bracket.")
    else:
        # Probe one page just beyond the deepest-with-data if budget allows,
        # to tighten the boundary (unless it's already 30 and 40 is known empty).
        candidates = []
        if deepest_with_data == 5:
            candidates = [6, 7]
        elif deepest_with_data == 10:
            candidates = [12, 15]
        elif deepest_with_data == 20:
            candidates = [22, 25]
        elif deepest_with_data == 30:
            candidates = [31, 32]
        for p in candidates:
            if _request_count >= 8:  # keep budget for T2/T3
                break
            status, code, body, rows = fetch(f"t1_adapt{p}", {"pageNo": str(p)})
            if rows:
                lo, hi = _range(rows)
                out(f"  pageNo={p:<3} HTTP {status} code {code} recs {len(rows)}  "
                    f"{utc_iso(lo)} .. {utc_iso(hi)}  (adaptive)")
                deepest_with_data = max(deepest_with_data, p)
                oldest_reached = min(oldest_reached, lo)
            else:
                out(f"  pageNo={p:<3} HTTP {status} code {code} recs 0  "
                    f"(EMPTY, adaptive)")

    out(f"\n  deepest pageNo returning data: {deepest_with_data}")
    if oldest_reached is not None:
        out(f"  oldest date reached via pageNo: {utc_iso(oldest_reached)}")
        reaches = oldest_reached <= 1640995200000
        out(f"  can a pageNo walk reach 2022-01-01? {reaches} "
            f"(oldest {utc_iso(oldest_reached)})")
    return oldest_reached


def test2():
    section("TEST 2 — DOES THIS ENDPOINT ACCEPT A TIME RANGE?")
    start, end = 1640995200000, 1643673600000  # 2022-01-01 .. 2022-02-01
    status, code, body, rows = fetch("t2_timerange",
                                     {"pageNo": "1", "startTime": str(start),
                                      "endTime": str(end)})
    out(f"  request: startTime={start} ({utc_iso(start)}), "
        f"endTime={end} ({utc_iso(end)})")
    out(f"  HTTP {status}  code {code}  records {len(rows)}")
    if rows:
        lo, hi = _range(rows)
        out(f"  returned range: {utc_iso(lo)} .. {utc_iso(hi)}")
        if lo <= end and hi >= start:
            out("  => records fall in the requested 2022 window: TIME RANGE "
                "HONORED. This is a path to a full backfill.")
        else:
            out("  => records are OUTSIDE the requested window (recent data). "
                "startTime/endTime are being IGNORED.")
    else:
        out(f"  no records returned (msg="
            f"{body.get('msg') if isinstance(body, dict) else None}).")


def test3():
    section("TEST 3 — WAS FUNDING EVER LARGE? (BTCUSDT, deepest data retrieved)")
    items = sorted(_ALL_BTC_RECORDS.items())
    rates = [r for _, r in items]
    if not rates:
        out("  no BTC records accumulated.")
        return
    lo_ts, hi_ts = items[0][0], items[-1][0]
    out(f"  pooled unique BTC records: {len(rates)}  "
        f"({utc_iso(lo_ts)} .. {utc_iso(hi_ts)})")
    over = [(t, r) for t, r in items if abs(r) > 0.0001]
    out(f"  3a min={min(rates):.8f}  max={max(rates):.8f}  "
        f"mean={statistics.mean(rates):.8f}  median={statistics.median(rates):.8f}")
    out(f"     records with |rate| > 0.0001: {len(over)} of {len(rates)}")
    # 3b cap vs baseline.
    amax = max(abs(r) for r in rates)
    if amax <= 0.0001 + 1e-12:
        out(f"  3b 0.0001 behaves as a HARD CAP — no record exceeds it "
            f"(max abs = {amax:.8f}).")
    else:
        out(f"  3b 0.0001 behaves as a NEUTRAL BASELINE — values regularly "
            f"exceed it ({len(over)} records; max abs = {amax:.8f}).")
    # 3c pre-2025 extreme.
    y2025 = int(datetime(2025, 1, 1, tzinfo=timezone.utc).timestamp() * 1000)
    pre = [(t, r) for t, r in items if t < y2025]
    if pre:
        tmax, rmax = max(pre, key=lambda x: abs(x[1]))
        out(f"  3c records predating 2025: {len(pre)}; max abs rate "
            f"{rmax:.8f} at {utc_iso(tmax)}")
    else:
        out("  3c no records predate 2025 in the retrieved data.")


def main():
    os.makedirs(REPORTS_DIR, exist_ok=True)
    out("BITGET FUNDING-RATE PROBE #2 (READ-ONLY — no data modified)")
    out(f"generated: {datetime.now(timezone.utc).isoformat()}")
    test1()
    test2()
    test3()
    out(f"\nTotal API requests made: {_request_count} (budget 12)")
    path = os.path.join(REPORTS_DIR, "probe_funding2.txt")
    with open(path, "w") as fh:
        fh.write("\n".join(_BUF) + "\n")
    out(f"Report saved to {path}")


if __name__ == "__main__":
    main()
