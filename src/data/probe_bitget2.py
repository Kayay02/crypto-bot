"""Bitget history-candles probe #2 — cross-venue timestamp confirmation.

Builds on probe #1 (endTime is backward-looking and EXCLUSIVE: endTime=T
returns newest bar T-900000; limit=200; ASCENDING; excludes in-progress bar).

Three small tests, <=12 API requests total, public endpoints, no auth:
  TEST 1 — definitive OPEN vs CLOSE via cross-check against Binance klines
           (documented OPEN time) over the same 20-bar 15m window.
  TEST 2 — exact 15m history start per symbol at 2022-01-01.
  TEST 3 — overlap chaining with byte-identical bar comparison.

Raw responses are saved immutably to data/raw/probe2/. No fetcher, no strategy.
"""

import json
import os
import sys
import time
from datetime import datetime, timezone

import requests

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, _REPO_ROOT)

from config import settings  # noqa: E402

BITGET_URL = settings.BASE_URL + settings.HISTORY_CANDLES_PATH
BINANCE_URL = "https://fapi.binance.com/fapi/v1/klines"
BAR_MS = settings.GRANULARITY_MS  # 900_000
MIN_INTERVAL = 1.0 / settings.MAX_REQUESTS_PER_SECOND
RAW_DIR = os.path.join(_REPO_ROOT, "data", "raw", "probe2")

_last_request_ts = 0.0
_request_count = 0


def _throttle():
    global _last_request_ts
    wait = MIN_INTERVAL - (time.monotonic() - _last_request_ts)
    if wait > 0:
        time.sleep(wait)
    _last_request_ts = time.monotonic()


def utc_iso(ms):
    return datetime.fromtimestamp(ms / 1000, tz=timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%S.%fZ"
    )


def iso_to_ms(iso):
    return int(
        datetime.strptime(iso, "%Y-%m-%dT%H:%M:%S.%fZ")
        .replace(tzinfo=timezone.utc)
        .timestamp()
        * 1000
    )


def _save(label, meta, status, body):
    global _request_count
    os.makedirs(RAW_DIR, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S_%f")
    fname = f"{stamp}_{label}.json"
    with open(os.path.join(RAW_DIR, fname), "w") as fh:
        json.dump({"meta": meta, "http_status": status, "response": body},
                  fh, indent=2)
    return fname


def get_bitget(label, symbol, end_time_ms, limit=200):
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
    resp = requests.get(BITGET_URL, params=params, timeout=30)
    try:
        body = resp.json()
    except ValueError:
        body = {"_non_json": resp.text}
    fname = _save(f"bitget_{label}", {"url": resp.url, "params": params},
                  resp.status_code, body)
    rows = body.get("data") if isinstance(body, dict) else None
    return resp.status_code, body, (rows if isinstance(rows, list) else []), fname


def get_binance(label, symbol, start_ms, end_ms, limit=200):
    """Binance klines. startTime/endTime are inclusive OPEN-time bounds."""
    global _request_count
    _throttle()
    _request_count += 1
    params = {
        "symbol": symbol,
        "interval": "15m",
        "startTime": str(start_ms),
        "endTime": str(end_ms),
        "limit": str(limit),
    }
    resp = requests.get(BINANCE_URL, params=params, timeout=30)
    try:
        body = resp.json()
    except ValueError:
        body = {"_non_json": resp.text}
    fname = _save(f"binance_{label}", {"url": resp.url, "params": params},
                  resp.status_code, body)
    rows = body if isinstance(body, list) else []
    return resp.status_code, body, rows, fname


def hr(title):
    print("\n" + "=" * 78)
    print(title)
    print("=" * 78)


# ---------------------------------------------------------------------------
def test1():
    hr("TEST 1 — TIMESTAMP CONVENTION, DEFINITIVE (Bitget vs Binance)")
    # Pick a window ~10 days ago (comfortably closed, plenty of movement).
    now_ms = int(time.time() * 1000)
    # Align an endTime to a bar boundary ~10 days back.
    end_aligned = ((now_ms - 10 * 24 * 60 * 60 * 1000) // BAR_MS) * BAR_MS
    # Bitget endTime is EXCLUSIVE -> newest bar = end_aligned - 900000.
    # We want 20 bars. Bitget newest open = end_aligned - BAR_MS.
    n = 20
    bg_status, _, bg_rows, bg_file = get_bitget("t1_window", "BTCUSDT",
                                                end_aligned, limit=n)
    if not bg_rows:
        print("Bitget returned no rows; cannot run test 1.")
        return
    bg = {int(r[0]): r for r in bg_rows}
    bg_ts = sorted(bg)
    # Fetch the matching Binance window by OPEN-time bounds.
    b_start, b_end = bg_ts[0], bg_ts[-1]
    bn_status, _, bn_rows, bn_file = get_binance("t1_window", "BTCUSDT",
                                                 b_start, b_end, limit=n + 2)
    bn = {int(r[0]): r for r in bn_rows}

    print(f"Bitget rows: {len(bg_rows)} (file {bg_file}), "
          f"Binance rows: {len(bn_rows)} (file {bn_file})")
    print(f"Bitget ts range : {utc_iso(bg_ts[0])} .. {utc_iso(bg_ts[-1])}")
    if bn:
        bn_ts = sorted(bn)
        print(f"Binance ts range: {utc_iso(bn_ts[0])} .. {utc_iso(bn_ts[-1])}")
    print()
    hdr = (f"{'timestamp (UTC)':<26} | {'Bitget O/H/L/C':<38} | "
           f"{'Binance@T O/H/L/C':<38}")
    print(hdr)
    print("-" * len(hdr))

    exact_at_T = 0
    exact_at_T_minus = 0
    compared = 0
    for t in bg_ts:
        r = bg[t]
        bg_ohlc = f"{r[1]}/{r[2]}/{r[3]}/{r[4]}"
        same_T = bn.get(t)
        bnT = f"{same_T[1]}/{same_T[2]}/{same_T[3]}/{same_T[4]}" if same_T else "-"
        print(f"{utc_iso(t):<26} | {bg_ohlc:<38} | {bnT:<38}")
        # Alignment scoring.
        if same_T:
            compared += 1
            if _ohlc_close(r, same_T):
                exact_at_T += 1
        prev = bn.get(t - BAR_MS)
        if prev and _ohlc_close(r, prev):
            exact_at_T_minus += 1

    print()
    print(f"Bars where Bitget[T] OHLC matches Binance[T]      : "
          f"{exact_at_T}/{compared}")
    print(f"Bars where Bitget[T] OHLC matches Binance[T-900000]: "
          f"{exact_at_T_minus}/{len(bg_ts)}")
    print("\nANSWER:")
    if compared == 0:
        print("  INCONCLUSIVE — no overlapping timestamps to compare.")
    elif exact_at_T > exact_at_T_minus and exact_at_T >= max(1, compared // 2):
        print("  Bitget bar at T aligns with Binance bar at T (same OPEN time).")
        print("  => Bitget timestamps are OPEN time.")
    elif exact_at_T_minus > exact_at_T:
        print("  Bitget bar at T aligns with Binance bar at T-900000.")
        print("  => Bitget timestamps are CLOSE time.")
    else:
        print("  AMBIGUOUS — venues diverge too much to judge cleanly "
              "(see match counts above).")
    print("EVIDENCE: match-count comparison above; Binance klines open-time is "
          "the reference. Exact OHLC equality is not required across venues "
          "(different liquidity); we look at which offset matches best.")


def _ohlc_close(bg_row, bn_row, rel=0.001):
    """Compare OHLC with a small relative tolerance (cross-venue)."""
    try:
        for i in range(1, 5):
            a, b = float(bg_row[i]), float(bn_row[i])
            denom = max(abs(a), abs(b), 1e-9)
            if abs(a - b) / denom > rel:
                return False
        return True
    except (ValueError, IndexError):
        return False


# ---------------------------------------------------------------------------
def test2():
    hr("TEST 2 — EXACT HISTORY START PER SYMBOL (endTime = 2022-01-01T00:00:00Z)")
    end_ms = iso_to_ms("2022-01-01T00:00:00.000Z")
    print(f"endTime = {end_ms} ({utc_iso(end_ms)})\n")
    for sym in settings.SYMBOLS:
        status, body, rows, fname = get_bitget(f"t2_{sym}", sym, end_ms, limit=200)
        code = body.get("code") if isinstance(body, dict) else None
        if rows:
            ts = [int(r[0]) for r in rows]
            print(f"{sym:<9} rows={len(rows):<4} code={code} "
                  f"min={utc_iso(min(ts))} max={utc_iso(max(ts))}  ({fname})")
        else:
            print(f"{sym:<9} rows=0    code={code}  NO DATA before 2022-01-01  "
                  f"({fname})")
    print("\nANSWER: per-symbol rows/min/max above. A symbol with rows whose max "
          "reaches ~2021-12-31T23:45 has 15m history at our 2022-01-01 start; "
          "rows=0 means its perp history begins later.")


# ---------------------------------------------------------------------------
def test3():
    hr("TEST 3 — OVERLAP CHAINING (byte-identical bar check)")
    now_ms = int(time.time() * 1000)
    end1 = ((now_ms - 5 * 24 * 60 * 60 * 1000) // BAR_MS) * BAR_MS
    _, _, rows1, f1 = get_bitget("t3_call1", "BTCUSDT", end1, limit=200)
    if not rows1:
        print("call1 returned no rows.")
        return
    ts1 = sorted(int(r[0]) for r in rows1)
    oldest1 = ts1[0]
    call1_by_ts = {int(r[0]): r for r in rows1}

    end2 = oldest1 + BAR_MS  # exclusive endTime => newest returned == oldest1
    _, _, rows2, f2 = get_bitget("t3_call2", "BTCUSDT", end2, limit=200)
    call2_by_ts = {int(r[0]): r for r in rows2}
    ts2 = sorted(call2_by_ts)

    print(f"call1 oldest ts = {oldest1} ({utc_iso(oldest1)})  file {f1}")
    print(f"call2 endTime   = {end2} ({utc_iso(end2)})  file {f2}")
    if ts2:
        print(f"call2 newest ts = {ts2[-1]} ({utc_iso(ts2[-1])})")
    reappears = oldest1 in call2_by_ts
    print(f"\nANSWER: call1's oldest bar reappears as call2's newest bar: {reappears}")
    if reappears:
        a = call1_by_ts[oldest1]
        b = call2_by_ts[oldest1]
        identical = a == b
        print(f"EVIDENCE: shared bar @ {utc_iso(oldest1)}")
        print(f"  call1: {a}")
        print(f"  call2: {b}")
        print(f"  byte-identical across responses: {identical}")
        if not identical:
            labels = ["ts", "open", "high", "low", "close", "base_vol", "quote_vol"]
            for i, lab in enumerate(labels):
                if i < len(a) and i < len(b) and a[i] != b[i]:
                    print(f"    DIFFERS [{lab}]: call1={a[i]!r} call2={b[i]!r}")
    else:
        print("EVIDENCE: shared timestamp not present in call2 "
              f"(call2 newest = {utc_iso(ts2[-1]) if ts2 else 'none'}).")


def main():
    print("Bitget probe #2")
    print("Run time (UTC):", datetime.now(timezone.utc).isoformat())
    print("Raw responses ->", RAW_DIR)
    test1()
    test2()
    test3()
    hr("DONE")
    print(f"Total API requests made: {_request_count} (budget: 12)")


if __name__ == "__main__":
    main()
