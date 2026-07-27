"""Bitget history-candles endpoint probe.

Characterizes the PUBLIC endpoint
    GET https://api.bitget.com/api/v2/mix/market/history-candles
so we understand its semantics before building any backfill fetcher.

This script makes at most 6 API requests, throttled to <=5 req/s. It writes
every raw response immutably to data/raw/probe/ and prints a human-readable
report to stdout. It does NOT clean, interpret, or store derived data.

No API key, signing, or auth headers are needed — this is a public endpoint.
"""

import json
import os
import sys
import time
from datetime import datetime, timezone

import requests

# Make the repo's config package importable regardless of CWD.
_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, _REPO_ROOT)

from config import settings  # noqa: E402

ENDPOINT = settings.BASE_URL + settings.HISTORY_CANDLES_PATH
BAR_MS = settings.GRANULARITY_MS  # 900_000
MIN_INTERVAL = 1.0 / settings.MAX_REQUESTS_PER_SECOND  # >=5 req/s throttle
RAW_DIR = os.path.join(_REPO_ROOT, settings.RAW_PROBE_DIR)

_last_request_ts = 0.0
_request_count = 0


def _throttle():
    global _last_request_ts
    wait = MIN_INTERVAL - (time.monotonic() - _last_request_ts)
    if wait > 0:
        time.sleep(wait)
    _last_request_ts = time.monotonic()


def utc_iso(ms):
    """ms epoch -> ISO-8601 UTC string."""
    return datetime.fromtimestamp(ms / 1000, tz=timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%S.%fZ"
    )


def iso_to_ms(iso):
    return int(
        datetime.strptime(iso, "%Y-%m-%dT%H:%M:%SZ")
        .replace(tzinfo=timezone.utc)
        .timestamp()
        * 1000
    )


def fetch(label, symbol, end_time_ms, limit=200):
    """Make one throttled request, save the raw response, return parsed JSON."""
    global _request_count
    _throttle()
    _request_count += 1

    params = {
        "symbol": symbol,
        "productType": settings.PRODUCT_TYPE,
        "granularity": settings.GRANULARITY,
        "endTime": str(end_time_ms),
        "limit": str(limit),
    }
    resp = requests.get(ENDPOINT, params=params, timeout=30)
    try:
        body = resp.json()
    except ValueError:
        body = {"_non_json_body": resp.text}

    os.makedirs(RAW_DIR, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S_%f")
    fname = f"{stamp}_{label}_{symbol}.json"
    record = {
        "request": {
            "url": resp.url,
            "params": params,
            "requested_at_utc": datetime.now(timezone.utc).isoformat(),
        },
        "http_status": resp.status_code,
        "response": body,
    }
    with open(os.path.join(RAW_DIR, fname), "w") as fh:
        json.dump(record, fh, indent=2)

    return resp.status_code, body, fname


def rows_of(body):
    """Return the candle list from a parsed response, or []."""
    data = body.get("data") if isinstance(body, dict) else None
    return data if isinstance(data, list) else []


def ts_list(rows):
    return [int(r[0]) for r in rows]


def hr(title):
    print("\n" + "=" * 72)
    print(title)
    print("=" * 72)


def main():
    now_ms = int(time.time() * 1000)
    thirty_days_ago_ms = now_ms - 30 * 24 * 60 * 60 * 1000

    print("Bitget history-candles probe")
    print("Endpoint:", ENDPOINT)
    print("Run time (UTC):", datetime.now(timezone.utc).isoformat())
    print("Raw responses -> ", RAW_DIR)

    # ---- Primary call: ~30 days ago, BTCUSDT, limit 200 (covers Q1-Q4). ----
    status1, body1, file1 = fetch("q1_4_anchor", "BTCUSDT", thirty_days_ago_ms, 200)
    code1 = body1.get("code") if isinstance(body1, dict) else None
    rows1 = rows_of(body1)
    ts1 = ts_list(rows1)

    hr("HTTP / RESPONSE ENVELOPE (primary call)")
    print(f"HTTP status : {status1}")
    print(f"Bitget code : {code1}")
    print(f"msg         : {body1.get('msg') if isinstance(body1, dict) else None}")
    print(f"raw file    : {file1}")
    print(f"requested endTime : {thirty_days_ago_ms}  ({utc_iso(thirty_days_ago_ms)})")

    if not rows1:
        print("\nNo rows returned on primary call; cannot continue analysis.")
        print("Full body:", json.dumps(body1, indent=2)[:2000])
        return

    tmin, tmax = min(ts1), max(ts1)

    # ---- ALSO REPORT: raw first 2 rows + field-order interpretation. ----
    hr("RAW FIELD INSPECTION")
    print("Raw unmodified first 2 rows (as returned by the API):")
    print(json.dumps(rows1[:2], indent=2))
    print("\nExpected field order: [timestamp, open, high, low, close, base_vol, quote_vol]")
    if len(rows1[0]) >= 7:
        r = rows1[0]
        try:
            o, h, l, c = float(r[1]), float(r[2]), float(r[3]), float(r[4])
            consistent = (h >= max(o, c)) and (l <= min(o, c)) and (h >= l)
            print(f"Row0 -> open={o} high={h} low={l} close={c} "
                  f"base_vol={r[5]} quote_vol={r[6]}")
            print(f"OHLC self-consistency (high>=max(o,c)>=min(o,c)>=low): {consistent}")
            print(f"Field count per row: {len(r)}")
        except (ValueError, IndexError) as e:
            print("Could not parse row as expected OHLCV:", e)
    else:
        print(f"Row has {len(rows1[0])} fields, fewer than expected 7.")

    # ---- Q3: LIMIT ----
    hr("Q3 — LIMIT")
    print(f"ANSWER  : limit=200 returned {len(rows1)} rows.")
    print(f"EVIDENCE: len(data) == {len(rows1)}")

    # ---- Q4: SORT ORDER ----
    hr("Q4 — SORT ORDER")
    ascending = ts1 == sorted(ts1)
    descending = ts1 == sorted(ts1, reverse=True)
    order = "ASCENDING" if ascending else "DESCENDING" if descending else "UNSORTED/MIXED"
    print(f"ANSWER  : array is {order} by timestamp.")
    print(f"EVIDENCE: first ts={ts1[0]} ({utc_iso(ts1[0])}), "
          f"last ts={ts1[-1]} ({utc_iso(ts1[-1])})")

    # ---- Q2: TIMESTAMP CONVENTION (spacing + relation to endTime) ----
    hr("Q2 — TIMESTAMP CONVENTION (open vs close)")
    diffs = [b - a for a, b in zip(ts1[:-1], ts1[1:])]
    uniform = all(abs(d) == BAR_MS for d in diffs)
    print(f"Consecutive spacing all == {BAR_MS} ms (900000): {uniform}")
    if not uniform:
        odd = [d for d in diffs if abs(d) != BAR_MS]
        print(f"  Non-900000 diffs found: {odd[:10]}")
    newest = tmax
    rel = "<=" if newest <= thirty_days_ago_ms else ">"
    print(f"newest ts ({newest}, {utc_iso(newest)}) {rel} requested endTime "
          f"({thirty_days_ago_ms}, {utc_iso(thirty_days_ago_ms)})")
    gap = thirty_days_ago_ms - newest
    print(f"endTime - newest = {gap} ms ({gap / BAR_MS:.3f} bars)")
    print("REASONING:")
    print("  If timestamps are OPEN times, the newest returned OPEN is typically")
    print("  <= endTime, and the bar it opens may extend up to endTime.")
    print("  If they were CLOSE times, a newest CLOSE <= endTime would imply the")
    print("  bar opened one interval earlier. Interpret the gap above accordingly;")
    print("  if endTime does not fall on a bar boundary the result may be ambiguous.")
    print(f"NOTE: requested endTime aligned to 900000-boundary? "
          f"{thirty_days_ago_ms % BAR_MS == 0} (offset {thirty_days_ago_ms % BAR_MS} ms)")

    # ---- Q1: ANCHORING ----
    hr("Q1 — ANCHORING (backward vs forward looking)")
    span_bars = (tmax - tmin) / BAR_MS
    if tmax <= thirty_days_ago_ms:
        anchor = "BACKWARD-looking: the 200 candles END at/around endTime."
    elif tmin >= thirty_days_ago_ms:
        anchor = "FORWARD-looking: the 200 candles START at/around endTime."
    else:
        anchor = "AMBIGUOUS: endTime falls inside the returned range."
    print(f"ANSWER  : {anchor}")
    print(f"EVIDENCE: returned range [{utc_iso(tmin)} .. {utc_iso(tmax)}], "
          f"{span_bars:.0f}-bar span.")
    print(f"          min ts={tmin}, max ts={tmax}, requested endTime={thirty_days_ago_ms}")

    # ---- OVERLAP TEST: chained backward call (call 2 endTime = oldest of call 1). ----
    hr("OVERLAP TEST — pagination validation")
    call2_end = tmin  # oldest timestamp from call 1
    status2, body2, file2 = fetch("overlap_call2", "BTCUSDT", call2_end, 200)
    rows2 = rows_of(body2)
    ts2 = ts_list(rows2)
    print(f"call 2 endTime = call1 oldest ts = {call2_end} ({utc_iso(call2_end)})")
    print(f"call 2 raw file: {file2}, rows: {len(rows2)}")
    if ts2:
        c2_newest = max(ts2)
        reappears = call2_end in ts2
        print(f"call 1 oldest bar ({call2_end}, {utc_iso(call2_end)})")
        print(f"call 2 newest bar ({c2_newest}, {utc_iso(c2_newest)})")
        print(f"ANSWER  : call1's oldest bar reappears in call2: {reappears}")
        overlap = c2_newest - call2_end
        print(f"EVIDENCE: (call2 newest - call1 oldest) = {overlap} ms "
              f"({overlap / BAR_MS:.2f} bars). One-bar overlap expected if "
              f"newest==oldest (0 ms) OR endTime is exclusive.")
    else:
        print("call 2 returned no rows.")

    # ---- Q5: IN-PROGRESS CANDLE (endTime = now). ----
    hr("Q5 — IN-PROGRESS CANDLE")
    status5, body5, file5 = fetch("q5_now", "BTCUSDT", now_ms, 200)
    rows5 = rows_of(body5)
    ts5 = ts_list(rows5)
    current_boundary = (now_ms // BAR_MS) * BAR_MS
    print(f"now = {now_ms} ({utc_iso(now_ms)})")
    print(f"current 15m boundary (open of forming bar) = {current_boundary} "
          f"({utc_iso(current_boundary)})")
    print(f"raw file: {file5}, rows: {len(rows5)}")
    if ts5:
        newest5 = max(ts5)
        includes = newest5 >= current_boundary
        print(f"newest returned ts = {newest5} ({utc_iso(newest5)})")
        print(f"ANSWER  : includes still-forming candle: {includes}")
        print(f"EVIDENCE: newest ts {'>=' if includes else '<'} current boundary. "
              f"Gap now-newest = {(now_ms - newest5) / BAR_MS:.2f} bars.")
    else:
        print("Q5 call returned no rows.")

    # ---- SOL AVAILABILITY CHECK. ----
    hr("SOL HISTORY AVAILABILITY")
    sol_end = iso_to_ms("2022-01-15T00:00:00Z")
    status6, body6, file6 = fetch("sol_avail", "SOLUSDT", sol_end, 200)
    code6 = body6.get("code") if isinstance(body6, dict) else None
    rows6 = rows_of(body6)
    print(f"symbol=SOLUSDT, endTime={sol_end} ({utc_iso(sol_end)})")
    print(f"HTTP {status6}, Bitget code {code6}, raw file {file6}")
    print(f"rows returned: {len(rows6)}")
    if rows6:
        s = ts_list(rows6)
        print(f"ANSWER  : DATA RETURNED — range [{utc_iso(min(s))} .. {utc_iso(max(s))}]")
        print("          SOL perp history reaches at/around 2022-01-15.")
    else:
        print("ANSWER  : NO DATA at 2022-01-15 — SOL perp history may start later.")
        print("Full body:", json.dumps(body6, indent=2)[:800])

    hr("DONE")
    print(f"Total API requests made: {_request_count} (budget: 6)")
    print(f"Raw responses saved under: {RAW_DIR}")


if __name__ == "__main__":
    main()
