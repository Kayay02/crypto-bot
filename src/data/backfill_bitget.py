"""Bitget 15m historical backfill — RAW LAYER ONLY.

Walks the public history-candles endpoint backward from now to 2022-01-01,
for BTCUSDT / ETHUSDT / SOLUSDT, and appends every raw API response to a
per-symbol JSONL file with full provenance. No cleaning, no dataframes, no
derived output, no funding rates, no Binance — raw capture only.

Verified endpoint facts (established by two prior probes, NOT re-tested here):
  - GET https://api.bitget.com/api/v2/mix/market/history-candles
    params: symbol, productType=USDT-FUTURES, granularity=15m, endTime(ms), limit=200
    Public. No key/signing/auth.
  - endTime is BACKWARD-looking and EXCLUSIVE: endTime=T -> newest bar T-900000.
  - Timestamps are the bar's OPEN time. Results ASCENDING. limit=200 -> 200 rows.
  - In-progress candle is not returned.
  - Chaining: next_endTime = current_oldest_ts + 900000  (deliberate 1-bar overlap).

Run:  python src/data/backfill_bitget.py
Resumable: re-running continues from the manifest's oldest_ts_fetched.
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

ENDPOINT = settings.BASE_URL + settings.HISTORY_CANDLES_PATH
BAR_MS = settings.GRANULARITY_MS  # 900_000
LIMIT = 200
MIN_INTERVAL = 1.0 / settings.MAX_REQUESTS_PER_SECOND  # 5 req/s -> 0.2s spacing
OUT_DIR = os.path.join(_REPO_ROOT, "data", "raw", "bitget")

TARGET_START_ISO = "2022-01-01T00:00:00.000Z"

# Retry policy.
MAX_ATTEMPTS = 4
RETRY_HTTP = {429}  # plus any 5xx
RETRY_API_CODES = {"45001", "40725", "40808"}
BASE_BACKOFF = 0.5  # seconds

_last_request_ts = 0.0


# --------------------------------------------------------------------------- #
# Time helpers
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


# --------------------------------------------------------------------------- #
# HTTP with throttle + retries
# --------------------------------------------------------------------------- #
def _throttle():
    global _last_request_ts
    wait = MIN_INTERVAL - (time.monotonic() - _last_request_ts)
    if wait > 0:
        time.sleep(wait)
    _last_request_ts = time.monotonic()


class BackfillError(Exception):
    """Fatal, non-retryable condition — fail loudly."""


def fetch_page(symbol, end_time_ms, retry_counter):
    """One throttled, retrying request. Returns (params, status, code, rows).

    Retries HTTP 429/5xx and Bitget codes in RETRY_API_CODES with exponential
    backoff + jitter, up to MAX_ATTEMPTS. 400-class param errors fail loudly.
    """
    params = {
        "symbol": symbol,
        "productType": settings.PRODUCT_TYPE,
        "granularity": settings.GRANULARITY,
        "endTime": str(end_time_ms),
        "limit": str(LIMIT),
    }

    for attempt in range(1, MAX_ATTEMPTS + 1):
        _throttle()
        try:
            resp = requests.get(ENDPOINT, params=params, timeout=30)
            status = resp.status_code
            try:
                body = resp.json()
            except ValueError:
                body = None
        except requests.RequestException as e:
            # Network-level failure: treat as retryable.
            if attempt < MAX_ATTEMPTS:
                delay = _backoff(attempt)
                retry_counter[0] += 1
                log(f"RETRY {symbol} attempt {attempt} network error {e!r}; "
                    f"sleeping {delay:.2f}s")
                time.sleep(delay)
                continue
            raise BackfillError(f"{symbol}: network failure after "
                                f"{MAX_ATTEMPTS} attempts: {e!r}")

        code = body.get("code") if isinstance(body, dict) else None
        msg = body.get("msg") if isinstance(body, dict) else None

        # Success.
        if status == 200 and code == "00000":
            rows = body.get("data")
            if not isinstance(rows, list):
                raise BackfillError(
                    f"{symbol}: 200/00000 but data is not a list: {body!r}")
            return params, status, code, rows

        # Decide retry vs fail.
        retryable = (status in RETRY_HTTP) or (500 <= status < 600) \
            or (code in RETRY_API_CODES)
        # 400-class parameter errors: fail loudly, no retry.
        if not retryable:
            raise BackfillError(
                f"{symbol}: non-retryable response HTTP {status} code {code} "
                f"msg {msg!r} params {params}")

        if attempt < MAX_ATTEMPTS:
            delay = _backoff(attempt)
            retry_counter[0] += 1
            log(f"RETRY {symbol} attempt {attempt} HTTP {status} code {code} "
                f"msg {msg!r}; sleeping {delay:.2f}s")
            time.sleep(delay)
            continue
        raise BackfillError(
            f"{symbol}: retryable error persisted after {MAX_ATTEMPTS} "
            f"attempts (HTTP {status} code {code} msg {msg!r})")


def _backoff(attempt):
    return BASE_BACKOFF * (2 ** (attempt - 1)) + random.uniform(0, 0.25)


# --------------------------------------------------------------------------- #
# Manifest / file helpers
# --------------------------------------------------------------------------- #
def jsonl_path(symbol):
    return os.path.join(OUT_DIR, f"{symbol}_15m.jsonl")


def manifest_path(symbol):
    return os.path.join(OUT_DIR, f"{symbol}_manifest.json")


def read_manifest(symbol):
    p = manifest_path(symbol)
    if os.path.exists(p):
        with open(p) as fh:
            return json.load(fh)
    return None


def write_manifest(symbol, m):
    # Atomic-ish write: temp then replace, so a crash can't corrupt manifest.
    p = manifest_path(symbol)
    tmp = p + ".tmp"
    with open(tmp, "w") as fh:
        json.dump(m, fh, indent=2)
    os.replace(tmp, p)


def append_page(symbol, params, status, code, rows):
    """Append one raw response line and fsync so a crash keeps completed pages."""
    line = {
        "fetched_at_utc": stamp(),
        "request": params,
        "http_status": status,
        "api_code": code,
        "response": rows,  # unmodified
    }
    with open(jsonl_path(symbol), "a") as fh:
        fh.write(json.dumps(line) + "\n")
        fh.flush()
        os.fsync(fh.fileno())


# --------------------------------------------------------------------------- #
# Inline validation (halt conditions)
# --------------------------------------------------------------------------- #
def validate_field_count(symbol, rows):
    for r in rows:
        if len(r) != 7:
            raise BackfillError(
                f"{symbol}: FIELD COUNT halt — row has {len(r)} fields "
                f"(expected 7): {r!r}")


def check_spacing(symbol, ts_sorted, spacing_violations):
    """Record (do not halt) any consecutive gap != 900000 ms."""
    for a, b in zip(ts_sorted[:-1], ts_sorted[1:]):
        gap = b - a
        if gap != BAR_MS:
            spacing_violations.append({
                "symbol": symbol,
                "from_ts": a, "to_ts": b, "gap_ms": gap,
                "from_utc": utc_iso(a), "to_utc": utc_iso(b),
            })
            log(f"SPACING violation {symbol}: {utc_iso(a)} -> {utc_iso(b)} "
                f"gap {gap} ms ({gap / BAR_MS:.2f} bars)")


# --------------------------------------------------------------------------- #
# Per-symbol backfill
# --------------------------------------------------------------------------- #
def backfill_symbol(symbol, target_start_ts, report):
    log(f"=== {symbol}: starting backfill (target start "
        f"{utc_iso(target_start_ts)}) ===")

    m = read_manifest(symbol)
    retry_counter = report["retries_by_symbol"].setdefault(symbol, [0])
    spacing_violations = report["spacing_violations"]

    # Determine starting endTime.
    if m and m.get("oldest_ts_fetched"):
        oldest_prev = int(m["oldest_ts_fetched"])
        next_end = oldest_prev + BAR_MS  # chaining rule; reproduces overlap bar
        pages = int(m.get("pages_fetched", 0))
        rows_written = int(m.get("rows_written", 0))
        newest_overall = int(m.get("newest_ts_fetched", oldest_prev))
        oldest_overall = oldest_prev
        log(f"{symbol}: resuming from oldest_ts {utc_iso(oldest_prev)} "
            f"({pages} pages already done)")
        if oldest_prev <= target_start_ts:
            log(f"{symbol}: manifest already reached target; nothing to do.")
            report["symbols"][symbol] = _finalize(symbol, target_start_ts,
                                                   spacing_violations)
            return
    else:
        next_end = now_ms()  # first page: newest closed bars before now
        pages = 0
        rows_written = 0
        newest_overall = None
        oldest_overall = None
        # Ensure output file exists (append-only from here).
        os.makedirs(OUT_DIR, exist_ok=True)
        open(jsonl_path(symbol), "a").close()

    prev_oldest_ts = oldest_overall  # for anti-loop + overlap identity
    # Cache the previous page's oldest ROW for overlap-identity comparison.
    prev_oldest_row = None
    if m and os.path.exists(jsonl_path(symbol)):
        prev_oldest_row = _last_line_oldest_row(symbol)

    while True:
        params, status, code, rows = fetch_page(symbol, next_end, retry_counter)

        if not rows:
            log(f"{symbol}: empty page at endTime {utc_iso(next_end)} — "
                f"no more history. Stopping.")
            break

        # FIELD COUNT halt.
        validate_field_count(symbol, rows)

        ts = sorted(int(r[0]) for r in rows)
        by_ts = {int(r[0]): r for r in rows}
        page_oldest, page_newest = ts[0], ts[-1]

        # OVERLAP IDENTITY halt: page's newest bar must equal prev page's
        # oldest bar, identical in every field.
        if prev_oldest_row is not None:
            shared_ts = int(prev_oldest_row[0])
            new_version = by_ts.get(shared_ts)
            if new_version is None:
                raise BackfillError(
                    f"{symbol}: OVERLAP IDENTITY halt — expected overlap bar "
                    f"{utc_iso(shared_ts)} absent from new page "
                    f"(new range {utc_iso(page_oldest)}..{utc_iso(page_newest)})")
            if new_version != prev_oldest_row:
                raise BackfillError(
                    f"{symbol}: OVERLAP IDENTITY halt — overlap bar "
                    f"{utc_iso(shared_ts)} differs across pages.\n"
                    f"  prev: {prev_oldest_row}\n  new : {new_version}")

        # ANTI-LOOP RAIL: oldest_ts must strictly decrease each page.
        if prev_oldest_ts is not None and page_oldest >= prev_oldest_ts:
            raise BackfillError(
                f"{symbol}: ANTI-LOOP halt — oldest_ts did not decrease "
                f"(prev {utc_iso(prev_oldest_ts)}, now {utc_iso(page_oldest)})")

        # SPACING (record only).
        check_spacing(symbol, ts, spacing_violations)

        # Persist page immediately (flush + fsync inside).
        append_page(symbol, params, status, code, rows)
        pages += 1
        rows_written += len(rows)
        newest_overall = page_newest if newest_overall is None \
            else max(newest_overall, page_newest)
        oldest_overall = page_oldest if oldest_overall is None \
            else min(oldest_overall, page_oldest)

        # Update manifest after every page.
        write_manifest(symbol, {
            "symbol": symbol,
            "granularity": settings.GRANULARITY,
            "endpoint": ENDPOINT,
            "target_start_ts": target_start_ts,
            "oldest_ts_fetched": oldest_overall,
            "newest_ts_fetched": newest_overall,
            "pages_fetched": pages,
            "rows_written": rows_written,
            "last_run_utc": stamp(),
            "status": "in_progress",
        })

        if pages % 25 == 0 or pages == 1:
            log(f"{symbol}: page {pages}, oldest reached "
                f"{utc_iso(page_oldest)}, rows {rows_written}")

        # Stop when we've walked back past the target start.
        if page_oldest <= target_start_ts:
            log(f"{symbol}: reached target start "
                f"({utc_iso(page_oldest)} <= {utc_iso(target_start_ts)}). Done.")
            break

        # Prepare next backward page.
        prev_oldest_ts = page_oldest
        prev_oldest_row = by_ts[page_oldest]
        next_end = page_oldest + BAR_MS

    # Mark complete + build final per-symbol report.
    m_final = read_manifest(symbol) or {}
    m_final["status"] = "complete"
    m_final["last_run_utc"] = stamp()
    write_manifest(symbol, m_final)
    report["symbols"][symbol] = _finalize(symbol, target_start_ts,
                                           spacing_violations)


def _last_line_oldest_row(symbol):
    """Oldest row of the last appended page (for resume overlap identity)."""
    last = None
    with open(jsonl_path(symbol)) as fh:
        for line in fh:
            if line.strip():
                last = line
    if not last:
        return None
    rec = json.loads(last)
    rows = rec.get("response") or []
    if not rows:
        return None
    return min(rows, key=lambda r: int(r[0]))


def _finalize(symbol, target_start_ts, spacing_violations):
    """Read the JSONL once to compute report stats (not derived output)."""
    total_rows = 0
    seen = set()
    lo = hi = None
    with open(jsonl_path(symbol)) as fh:
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
    sym_viol = [v for v in spacing_violations if v["symbol"] == symbol]
    return {
        "total_rows": total_rows,
        "unique_ts": len(seen),
        "overlap_rows": total_rows - len(seen),
        "oldest_ts": lo,
        "newest_ts": hi,
        "spacing_violations": sym_viol,
    }


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #
def release_window_warning():
    n = datetime.now(timezone.utc)
    if n.weekday() in (1, 2, 3) and 6 <= n.hour < 9:  # Tue/Wed/Thu 06-09 UTC
        log("WARNING: running during Bitget release window "
            "(Tue/Wed/Thu 06:00-09:00 UTC). Elevated chance of transient errors.")


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    target_start_ts = iso_to_ms(TARGET_START_ISO)
    release_window_warning()

    log(f"Backfill start. Symbols {settings.SYMBOLS}, target start "
        f"{TARGET_START_ISO} ({target_start_ts}).")

    report = {
        "symbols": {},
        "spacing_violations": [],
        "retries_by_symbol": {},
        "halt": None,
    }

    t0 = time.time()
    try:
        for symbol in settings.SYMBOLS:
            backfill_symbol(symbol, target_start_ts, report)
    except BackfillError as e:
        report["halt"] = str(e)
        log(f"HALT: {e}")

    elapsed = time.time() - t0
    _print_report(report, target_start_ts, elapsed)


def _print_report(report, target_start_ts, elapsed):
    EXPECTED_BARS = 160_100
    EXPECTED_PAGES = 805

    print("\n" + "#" * 78)
    print("BACKFILL FINAL REPORT")
    print("#" * 78)
    print(f"Elapsed: {elapsed:.1f}s   Target start: {utc_iso(target_start_ts)}")

    for symbol in settings.SYMBOLS:
        s = report["symbols"].get(symbol)
        m = read_manifest(symbol) or {}
        retries = report["retries_by_symbol"].get(symbol, [0])[0]
        print("\n" + "-" * 78)
        print(f"SYMBOL {symbol}   status={m.get('status')}")
        if not s:
            print("  (not processed — see HALT below)")
            continue
        pages = m.get("pages_fetched")
        print(f"  total rows written : {s['total_rows']}")
        print(f"  unique timestamps  : {s['unique_ts']} "
              f"(overlap duplicate rows: {s['overlap_rows']})")
        if s["oldest_ts"] is not None:
            print(f"  date range covered : {utc_iso(s['oldest_ts'])} .. "
                  f"{utc_iso(s['newest_ts'])}")
        print(f"  pages fetched      : {pages}")
        print(f"  delta vs expected  : rows {s['unique_ts'] - EXPECTED_BARS:+d} "
              f"(exp ~{EXPECTED_BARS}), pages "
              f"{(pages or 0) - EXPECTED_PAGES:+d} (exp ~{EXPECTED_PAGES})")
        print(f"  retries            : {retries}")
        viol = s["spacing_violations"]
        print(f"  spacing violations : {len(viol)}")
        if viol:
            top = sorted(viol, key=lambda v: abs(v["gap_ms"]), reverse=True)[:10]
            print("    10 largest gaps:")
            for v in top:
                print(f"      {v['from_utc']} -> {v['to_utc']}  "
                      f"gap {v['gap_ms']} ms ({v['gap_ms'] / BAR_MS:.1f} bars)")

    print("\n" + "-" * 78)
    print(f"HALT CONDITIONS TRIGGERED: "
          f"{report['halt'] if report['halt'] else 'none'}")
    total_retries = sum(v[0] for v in report["retries_by_symbol"].values())
    print(f"TOTAL RETRIES (all symbols): {total_retries}")
    print("#" * 78)


if __name__ == "__main__":
    main()
