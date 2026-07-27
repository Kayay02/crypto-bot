"""Bitget 1m historical backfill — RAW LAYER ONLY.

Adapted from backfill_bitget.py (the completed 15m run). Mechanics are IDENTICAL
to that script; only the granularity constants change (BAR_MS 60000, output dir,
file names, expected totals). Walks the public history-candles endpoint backward
from now to 2022-01-01 for BTCUSDT / ETHUSDT / SOLUSDT and appends every raw
response to a per-symbol JSONL with full provenance. No cleaning, no dataframes,
no derived output, no strategy code.

Verified endpoint facts (NOT re-tested here):
  - endTime backward-looking and EXCLUSIVE: endTime=T -> newest bar T-60000.
  - timestamps OPEN time. Results ASCENDING. limit=200 -> 200 rows.
  - Chaining: next_endTime = current_oldest_ts + 60000 (1-bar overlap per page).

Scale: ~12,015 pages/symbol, ~36k total, ~2h at 5 req/s. Resumable per page.

Run:  python -u src/data/backfill_bitget_1m.py
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
GRANULARITY = "1m"
BAR_MS = 60_000  # 1-minute bars (vs 900_000 for 15m)
LIMIT = 200
# Rate: bumped to 10 req/s for this bulk job (Bitget IP limit is 20/s, so this
# keeps a 2x margin). The global settings default (5) stays conservative for
# the probe scripts.
REQUESTS_PER_SECOND = 10
MIN_INTERVAL = 1.0 / REQUESTS_PER_SECOND
OUT_DIR = os.path.join(_REPO_ROOT, "data", "raw", "bitget_1m")

TARGET_START_ISO = "2022-01-01T00:00:00.000Z"

MAX_ATTEMPTS = 4
RETRY_HTTP = {429}
RETRY_API_CODES = {"45001", "40725", "40808"}
BASE_BACKOFF = 0.5

_last_request_ts = 0.0


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


def fmt_dur(seconds):
    seconds = int(max(0, seconds))
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    return f"{h}h{m:02d}m{s:02d}s"


# --------------------------------------------------------------------------- #
class BackfillError(Exception):
    """Fatal, non-retryable condition — fail loudly."""


def _throttle():
    global _last_request_ts
    wait = MIN_INTERVAL - (time.monotonic() - _last_request_ts)
    if wait > 0:
        time.sleep(wait)
    _last_request_ts = time.monotonic()


def _backoff(attempt):
    return BASE_BACKOFF * (2 ** (attempt - 1)) + random.uniform(0, 0.25)


def fetch_page(symbol, end_time_ms, retry_counter):
    params = {
        "symbol": symbol,
        "productType": settings.PRODUCT_TYPE,
        "granularity": GRANULARITY,
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

        if status == 200 and code == "00000":
            rows = body.get("data")
            if not isinstance(rows, list):
                raise BackfillError(
                    f"{symbol}: 200/00000 but data is not a list: {body!r}")
            return params, status, code, rows

        retryable = (status in RETRY_HTTP) or (500 <= status < 600) \
            or (code in RETRY_API_CODES)
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


# --------------------------------------------------------------------------- #
def jsonl_path(symbol):
    return os.path.join(OUT_DIR, f"{symbol}_1m.jsonl")


def manifest_path(symbol):
    return os.path.join(OUT_DIR, f"{symbol}_manifest.json")


def read_manifest(symbol):
    p = manifest_path(symbol)
    if os.path.exists(p):
        with open(p) as fh:
            return json.load(fh)
    return None


def write_manifest(symbol, m):
    p = manifest_path(symbol)
    tmp = p + ".tmp"
    with open(tmp, "w") as fh:
        json.dump(m, fh, indent=2)
        fh.flush()
        os.fsync(fh.fileno())
    os.replace(tmp, p)


def append_page(symbol, params, status, code, rows):
    line = {
        "fetched_at_utc": stamp(),
        "request": params,
        "http_status": status,
        "api_code": code,
        "response": rows,
    }
    with open(jsonl_path(symbol), "a") as fh:
        fh.write(json.dumps(line) + "\n")
        fh.flush()
        os.fsync(fh.fileno())


# --------------------------------------------------------------------------- #
def validate_field_count(symbol, rows):
    for r in rows:
        if len(r) != 7:
            raise BackfillError(
                f"{symbol}: FIELD COUNT halt — row has {len(r)} fields "
                f"(expected 7): {r!r}")


def check_spacing(symbol, ts_sorted, spacing_violations):
    for a, b in zip(ts_sorted[:-1], ts_sorted[1:]):
        gap = b - a
        if gap != BAR_MS:
            spacing_violations.append({
                "symbol": symbol, "from_ts": a, "to_ts": b, "gap_ms": gap,
                "from_utc": utc_iso(a), "to_utc": utc_iso(b),
            })
            log(f"SPACING violation {symbol}: {utc_iso(a)} -> {utc_iso(b)} "
                f"gap {gap} ms ({gap / BAR_MS:.2f} bars)")


# --------------------------------------------------------------------------- #
def backfill_symbol(symbol, target_start_ts, report):
    log(f"=== {symbol}: starting 1m backfill (target start "
        f"{utc_iso(target_start_ts)}) ===")
    t_sym0 = time.time()

    m = read_manifest(symbol)
    retry_counter = report["retries_by_symbol"].setdefault(symbol, [0])
    spacing_violations = report["spacing_violations"]

    if m and m.get("oldest_ts_fetched"):
        oldest_prev = int(m["oldest_ts_fetched"])
        next_end = oldest_prev + BAR_MS
        pages = int(m.get("pages_fetched", 0))
        rows_written = int(m.get("rows_written", 0))
        newest_overall = int(m.get("newest_ts_fetched", oldest_prev))
        oldest_overall = oldest_prev
        log(f"{symbol}: resuming from oldest_ts {utc_iso(oldest_prev)} "
            f"({pages} pages already done)")
        if oldest_prev <= target_start_ts:
            log(f"{symbol}: manifest already reached target; nothing to do.")
            report["symbols"][symbol] = _finalize(symbol, spacing_violations)
            return
    else:
        next_end = now_ms()
        pages = 0
        rows_written = 0
        newest_overall = None
        oldest_overall = None
        os.makedirs(OUT_DIR, exist_ok=True)
        open(jsonl_path(symbol), "a").close()

    prev_oldest_ts = oldest_overall
    prev_oldest_row = None
    if m and os.path.exists(jsonl_path(symbol)):
        prev_oldest_row = _last_line_oldest_row(symbol)

    # Anchor for ETA (fixed reference so ETA reflects this run's rate).
    run_start = time.time()
    pages_this_run = 0
    newest_anchor = None

    while True:
        params, status, code, rows = fetch_page(symbol, next_end, retry_counter)

        if not rows:
            log(f"{symbol}: empty page at endTime {utc_iso(next_end)} — "
                f"no more history. Stopping.")
            break

        validate_field_count(symbol, rows)
        ts = sorted(int(r[0]) for r in rows)
        by_ts = {int(r[0]): r for r in rows}
        page_oldest, page_newest = ts[0], ts[-1]
        if newest_anchor is None:
            newest_anchor = page_newest

        # OVERLAP IDENTITY halt.
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

        # ANTI-LOOP RAIL.
        if prev_oldest_ts is not None and page_oldest >= prev_oldest_ts:
            raise BackfillError(
                f"{symbol}: ANTI-LOOP halt — oldest_ts did not decrease "
                f"(prev {utc_iso(prev_oldest_ts)}, now {utc_iso(page_oldest)})")

        check_spacing(symbol, ts, spacing_violations)

        append_page(symbol, params, status, code, rows)
        pages += 1
        pages_this_run += 1
        rows_written += len(rows)
        newest_overall = page_newest if newest_overall is None \
            else max(newest_overall, page_newest)
        oldest_overall = page_oldest if oldest_overall is None \
            else min(oldest_overall, page_oldest)

        write_manifest(symbol, {
            "symbol": symbol,
            "granularity": GRANULARITY,
            "endpoint": ENDPOINT,
            "target_start_ts": target_start_ts,
            "oldest_ts_fetched": oldest_overall,
            "newest_ts_fetched": newest_overall,
            "pages_fetched": pages,
            "rows_written": rows_written,
            "last_run_utc": stamp(),
            "status": "in_progress",
        })

        # Progress every 100 pages: pages, oldest date, elapsed, ETA.
        if pages_this_run % 100 == 0 or pages == 1:
            elapsed = time.time() - run_start
            done_ms = (newest_anchor - page_oldest)
            total_ms = (newest_anchor - target_start_ts)
            frac = done_ms / total_ms if total_ms > 0 else 0
            rate = pages_this_run / elapsed if elapsed > 0 else 0
            eta = ((total_ms - done_ms) / (BAR_MS * LIMIT) / rate) \
                if rate > 0 else 0
            log(f"{symbol}: page {pages} (this run {pages_this_run}), oldest "
                f"{utc_iso(page_oldest)}, {frac*100:.1f}% of span, "
                f"elapsed {fmt_dur(elapsed)}, ~{rate:.1f} pg/s, "
                f"ETA {fmt_dur(eta)}")

        if page_oldest <= target_start_ts:
            log(f"{symbol}: reached target start "
                f"({utc_iso(page_oldest)} <= {utc_iso(target_start_ts)}). Done.")
            break

        prev_oldest_ts = page_oldest
        prev_oldest_row = by_ts[page_oldest]
        next_end = page_oldest + BAR_MS

    m_final = read_manifest(symbol) or {}
    m_final["status"] = "complete"
    m_final["last_run_utc"] = stamp()
    write_manifest(symbol, m_final)
    log(f"{symbol}: symbol elapsed {fmt_dur(time.time() - t_sym0)}")
    report["symbols"][symbol] = _finalize(symbol, spacing_violations)


def _last_line_oldest_row(symbol):
    last = None
    with open(jsonl_path(symbol)) as fh:
        for line in fh:
            if line.strip():
                last = line
    if not last:
        return None
    rows = json.loads(last).get("response") or []
    if not rows:
        return None
    return min(rows, key=lambda r: int(r[0]))


def _finalize(symbol, spacing_violations):
    total_rows = 0
    seen = set()
    lo = hi = None
    with open(jsonl_path(symbol)) as fh:
        for line in fh:
            if not line.strip():
                continue
            for r in json.loads(line).get("response") or []:
                t = int(r[0])
                total_rows += 1
                seen.add(t)
                lo = t if lo is None else min(lo, t)
                hi = t if hi is None else max(hi, t)
    sym_viol = [v for v in spacing_violations if v["symbol"] == symbol]
    size_bytes = os.path.getsize(jsonl_path(symbol))
    return {
        "total_rows": total_rows,
        "unique_ts": len(seen),
        "overlap_rows": total_rows - len(seen),
        "oldest_ts": lo,
        "newest_ts": hi,
        "spacing_violations": sym_viol,
        "file_size_bytes": size_bytes,
    }


# --------------------------------------------------------------------------- #
def release_window_warning():
    n = datetime.now(timezone.utc)
    if n.weekday() in (1, 2, 3) and 6 <= n.hour < 9:
        log("WARNING: running during Bitget release window "
            "(Tue/Wed/Thu 06:00-09:00 UTC). Elevated chance of transient errors.")


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    target_start_ts = iso_to_ms(TARGET_START_ISO)
    release_window_warning()
    log(f"1m backfill start. Symbols {settings.SYMBOLS}, target start "
        f"{TARGET_START_ISO} ({target_start_ts}).")

    report = {"symbols": {}, "spacing_violations": [],
              "retries_by_symbol": {}, "halt": None}

    t0 = time.time()
    try:
        for symbol in settings.SYMBOLS:
            backfill_symbol(symbol, target_start_ts, report)
    except BackfillError as e:
        report["halt"] = str(e)
        log(f"HALT: {e}")

    _print_report(report, target_start_ts, time.time() - t0)


def _print_report(report, target_start_ts, elapsed):
    EXPECTED_BARS = 2_402_900
    EXPECTED_PAGES = 12_015

    print("\n" + "#" * 78)
    print("1m BACKFILL FINAL REPORT")
    print("#" * 78)
    print(f"Elapsed: {fmt_dur(elapsed)}   Target start: {utc_iso(target_start_ts)}")

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
        print(f"  delta vs expected  : bars {s['unique_ts'] - EXPECTED_BARS:+d} "
              f"(exp ~{EXPECTED_BARS}), pages "
              f"{(pages or 0) - EXPECTED_PAGES:+d} (exp ~{EXPECTED_PAGES})")
        print(f"  output file size   : {s['file_size_bytes'] / 1e6:.1f} MB")
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
