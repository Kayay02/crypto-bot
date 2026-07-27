"""Binance BTCUSDT 15m reference series — RAW LAYER ONLY, QUALITY CHECK USE.

This series exists SOLELY for cross-venue anomaly detection against the Bitget
data in data/raw/bitget/. It is NOT a trading data source and will never feed
the strategy. No cleaning, no Parquet, no comparison here — raw capture only.

Endpoint (public, no auth):
  GET https://fapi.binance.com/fapi/v1/klines
  params: symbol=BTCUSDT, interval=15m, startTime, endTime, limit=1000

Binance differs from Bitget (verified by a probe call at startup, not assumed):
  - startTime-anchored FORWARD pagination (opposite of Bitget's backward walk).
  - limit up to 1000 per call.
  - kline timestamp = OPEN time.
  - each row has 12 fields (kept unmodified).
  - weight-based rate limits (we stay conservative at 5 req/s).

Pagination: next startTime = last open_time + 900000. Anti-loop: newest ts must
strictly INCREASE each page or HALT.

Run:  python -u src/data/backfill_binance.py
"""

import json
import os
import random
import sys
import time
from datetime import datetime, timezone

import requests

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, _REPO_ROOT)

from config import settings  # noqa: E402

ENDPOINT = "https://fapi.binance.com/fapi/v1/klines"
SYMBOL = "BTCUSDT"
INTERVAL = "15m"
BAR_MS = settings.GRANULARITY_MS  # 900_000
LIMIT = 1000
EXPECTED_FIELDS = 12
MIN_INTERVAL = 1.0 / settings.MAX_REQUESTS_PER_SECOND  # 5 req/s
OUT_DIR = os.path.join(_REPO_ROOT, "data", "raw", "binance")

START_ISO = "2021-12-30T00:00:00.000Z"

MAX_ATTEMPTS = 4
BASE_BACKOFF = 0.5

_last_request_ts = 0.0


# --------------------------------------------------------------------------- #
def now_ms():
    return int(time.time() * 1000)


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


def stamp():
    return datetime.now(timezone.utc).isoformat()


def log(msg):
    print(f"[{stamp()}] {msg}", flush=True)


class BackfillError(Exception):
    """Fatal, non-retryable — fail loudly."""


def _throttle():
    global _last_request_ts
    wait = MIN_INTERVAL - (time.monotonic() - _last_request_ts)
    if wait > 0:
        time.sleep(wait)
    _last_request_ts = time.monotonic()


def _backoff(attempt):
    return BASE_BACKOFF * (2 ** (attempt - 1)) + random.uniform(0, 0.25)


def fetch_page(start_ms, end_ms, retry_counter):
    """One throttled, retrying klines request. Returns (params, status, rows).

    Retries HTTP 429 (respecting Retry-After) and 5xx up to MAX_ATTEMPTS.
    400-class errors fail loudly.
    """
    params = {
        "symbol": SYMBOL,
        "interval": INTERVAL,
        "startTime": str(start_ms),
        "endTime": str(end_ms),
        "limit": str(LIMIT),
    }

    for attempt in range(1, MAX_ATTEMPTS + 1):
        _throttle()
        try:
            resp = requests.get(ENDPOINT, params=params, timeout=30)
            status = resp.status_code
        except requests.RequestException as e:
            if attempt < MAX_ATTEMPTS:
                delay = _backoff(attempt)
                retry_counter[0] += 1
                log(f"RETRY attempt {attempt} network error {e!r}; "
                    f"sleeping {delay:.2f}s")
                time.sleep(delay)
                continue
            raise BackfillError(f"network failure after {MAX_ATTEMPTS} "
                                f"attempts: {e!r}")

        if status == 200:
            try:
                body = resp.json()
            except ValueError:
                raise BackfillError(f"200 but non-JSON body: {resp.text[:300]!r}")
            if not isinstance(body, list):
                # Binance error payloads are objects: {"code":..,"msg":..}
                raise BackfillError(f"200 but data is not a list: {body!r}")
            return params, status, body

        retryable = status == 429 or (500 <= status < 600)
        if not retryable:
            raise BackfillError(
                f"non-retryable HTTP {status}: {resp.text[:300]!r} "
                f"params {params}")

        if attempt < MAX_ATTEMPTS:
            retry_after = resp.headers.get("Retry-After")
            delay = float(retry_after) if retry_after else _backoff(attempt)
            retry_counter[0] += 1
            log(f"RETRY attempt {attempt} HTTP {status} "
                f"(Retry-After={retry_after}); sleeping {delay:.2f}s")
            time.sleep(delay)
            continue
        raise BackfillError(f"retryable HTTP {status} persisted after "
                            f"{MAX_ATTEMPTS} attempts")


# --------------------------------------------------------------------------- #
def jsonl_path():
    return os.path.join(OUT_DIR, f"{SYMBOL}_15m.jsonl")


def manifest_path():
    return os.path.join(OUT_DIR, f"{SYMBOL}_manifest.json")


def read_manifest():
    p = manifest_path()
    if os.path.exists(p):
        with open(p) as fh:
            return json.load(fh)
    return None


def write_manifest(m):
    p = manifest_path()
    tmp = p + ".tmp"
    with open(tmp, "w") as fh:
        json.dump(m, fh, indent=2)
    os.replace(tmp, p)


def append_page(params, status, rows):
    line = {
        "fetched_at_utc": stamp(),
        "request": params,
        "http_status": status,
        "response": rows,  # unmodified, all 12 fields per row
    }
    with open(jsonl_path(), "a") as fh:
        fh.write(json.dumps(line) + "\n")
        fh.flush()
        os.fsync(fh.fileno())


# --------------------------------------------------------------------------- #
def validate_field_count(rows):
    for r in rows:
        if len(r) != EXPECTED_FIELDS:
            raise BackfillError(
                f"FIELD COUNT halt — row has {len(r)} fields "
                f"(expected {EXPECTED_FIELDS}): {r!r}")


def check_spacing(open_times_sorted, violations):
    for a, b in zip(open_times_sorted[:-1], open_times_sorted[1:]):
        gap = b - a
        if gap != BAR_MS:
            violations.append({
                "from_ts": a, "to_ts": b, "gap_ms": gap,
                "from_utc": utc_iso(a), "to_utc": utc_iso(b),
            })
            log(f"SPACING violation: {utc_iso(a)} -> {utc_iso(b)} "
                f"gap {gap} ms ({gap / BAR_MS:.2f} bars)")


# --------------------------------------------------------------------------- #
def probe():
    """One call to confirm response shape before the full run."""
    log("PROBE: confirming Binance response shape ...")
    start = iso_to_ms(START_ISO)
    params, status, rows = fetch_page(start, now_ms(), [0])
    print("PROBE HTTP status:", status)
    print("PROBE rows returned:", len(rows))
    print("PROBE raw first 2 rows (unmodified):")
    print(json.dumps(rows[:2], indent=2))
    if rows:
        print("PROBE field count per row:", len(rows[0]))
    if not rows or len(rows[0]) != EXPECTED_FIELDS:
        raise BackfillError("PROBE: unexpected shape; aborting before full run.")
    log(f"PROBE OK: {len(rows[0])} fields/row, forward window starts "
        f"{utc_iso(int(rows[0][0]))}.")


def backfill():
    os.makedirs(OUT_DIR, exist_ok=True)
    start_ms = iso_to_ms(START_ISO)
    end_ms = now_ms()

    report = {"pages": 0, "retries": [0], "spacing": [], "halt": None}
    retry_counter = report["retries"]

    m = read_manifest()
    if m and m.get("newest_ts_fetched"):
        next_start = int(m["newest_ts_fetched"]) + BAR_MS  # resume forward
        pages = int(m.get("pages_fetched", 0))
        rows_written = int(m.get("rows_written", 0))
        oldest_overall = int(m.get("oldest_ts_fetched"))
        newest_overall = int(m["newest_ts_fetched"])
        prev_newest = newest_overall
        log(f"Resuming from newest_ts {utc_iso(newest_overall)} "
            f"({pages} pages already done).")
    else:
        next_start = start_ms
        pages = 0
        rows_written = 0
        oldest_overall = None
        newest_overall = None
        prev_newest = None
        open(jsonl_path(), "a").close()

    while next_start <= end_ms:
        params, status, rows = fetch_page(next_start, end_ms, retry_counter)
        report["pages"] += 1

        if not rows:
            log(f"Empty page at startTime {utc_iso(next_start)} — reached end.")
            break

        # FIELD COUNT halt.
        validate_field_count(rows)

        open_times = sorted(int(r[0]) for r in rows)
        page_oldest, page_newest = open_times[0], open_times[-1]

        # ANTI-LOOP: newest ts must strictly INCREASE each page.
        if prev_newest is not None and page_newest <= prev_newest:
            raise BackfillError(
                f"ANTI-LOOP halt — newest_ts did not increase "
                f"(prev {utc_iso(prev_newest)}, now {utc_iso(page_newest)})")

        check_spacing(open_times, report["spacing"])

        append_page(params, status, rows)
        pages += 1
        rows_written += len(rows)
        oldest_overall = page_oldest if oldest_overall is None \
            else min(oldest_overall, page_oldest)
        newest_overall = page_newest if newest_overall is None \
            else max(newest_overall, page_newest)

        write_manifest({
            "symbol": SYMBOL,
            "granularity": INTERVAL,
            "endpoint": ENDPOINT,
            "requested_start_ts": start_ms,
            "oldest_ts_fetched": oldest_overall,
            "newest_ts_fetched": newest_overall,
            "pages_fetched": pages,
            "rows_written": rows_written,
            "last_run_utc": stamp(),
            "status": "in_progress",
        })

        if pages % 20 == 0 or pages == 1:
            log(f"page {pages}, newest reached {utc_iso(page_newest)}, "
                f"rows {rows_written}")

        # If fewer than a full page came back, we've hit the live edge.
        if len(rows) < LIMIT:
            log(f"Partial page ({len(rows)} < {LIMIT}) — reached live edge "
                f"at {utc_iso(page_newest)}.")
            break

        prev_newest = page_newest
        next_start = page_newest + BAR_MS

    m_final = read_manifest() or {}
    m_final["status"] = "complete"
    m_final["last_run_utc"] = stamp()
    write_manifest(m_final)
    return report


# --------------------------------------------------------------------------- #
def _finalize_stats():
    total_rows = 0
    seen = set()
    lo = hi = None
    with open(jsonl_path()) as fh:
        for line in fh:
            if not line.strip():
                continue
            rec = json.loads(line)
            for r in rec.get("response") or []:
                t = int(r[0])
                total_rows += 1
                seen.add(t)
                lo = t if lo is None else min(lo, t)
                hi = t if hi is None else max(hi, t)
    return total_rows, seen, lo, hi


def print_report(report, elapsed):
    EXPECTED_BARS = 160_200
    total_rows, seen, lo, hi = _finalize_stats()
    m = read_manifest() or {}

    print("\n" + "#" * 78)
    print("BINANCE BTCUSDT REFERENCE BACKFILL — FINAL REPORT")
    print("#" * 78)
    print(f"Elapsed: {elapsed:.1f}s   status={m.get('status')}")
    print(f"pages fetched      : {m.get('pages_fetched')}")
    print(f"total rows written : {total_rows}")
    print(f"unique bars (dedupe): {len(seen)}")
    if lo is not None:
        print(f"date range covered : {utc_iso(lo)} .. {utc_iso(hi)}")
    print(f"delta vs expected  : {len(seen) - EXPECTED_BARS:+d} "
          f"(exp ~{EXPECTED_BARS})")

    viol = report["spacing"]
    print(f"spacing violations : {len(viol)}")
    if viol:
        top = sorted(viol, key=lambda v: abs(v["gap_ms"]), reverse=True)[:10]
        print("  10 largest gaps:")
        for v in top:
            print(f"    {v['from_utc']} -> {v['to_utc']}  gap {v['gap_ms']} ms "
                  f"({v['gap_ms'] / BAR_MS:.1f} bars)")

    print(f"total retries      : {report['retries'][0]}")
    print(f"HALT conditions    : {report['halt'] if report['halt'] else 'none'}")
    print("#" * 78)


def main():
    t0 = time.time()
    log(f"Binance reference backfill start. {SYMBOL} {INTERVAL}, "
        f"{START_ISO} -> now.")
    report = {"pages": 0, "retries": [0], "spacing": [], "halt": None}
    try:
        probe()
        report = backfill()
    except BackfillError as e:
        report["halt"] = str(e)
        log(f"HALT: {e}")
    print_report(report, time.time() - t0)


if __name__ == "__main__":
    main()
