"""READ-ONLY 1m-granularity probe of the Bitget history-candles endpoint.

Answers four questions before any 1m backfill is considered:
  T1 — how far back does 1m history reach (retention depth)?
  T2 — spacing (60000 ms), 7-field shape, limit=200?
  T3 — are 1m opens synthesized (open==prev_close) like the 15m data?
  T4 — do 15 x 1m bars reconstruct the corresponding 15m bar (H/L/C/volume)?

Endpoint facts (verified previously, not re-tested): endTime backward-looking
and EXCLUSIVE; timestamps OPEN time; results ASCENDING.

HARD CONSTRAINT: read-only. No backfill, no derived layer, no cleaning, no
strategy code. Max 10 API requests. Raw responses saved to data/raw/probe_1m/;
report saved to reports/probe_1m.txt.

Run:  python -u src/data/probe_1m.py
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

ENDPOINT = settings.BASE_URL + settings.HISTORY_CANDLES_PATH
MINUTE_MS = 60_000
BAR15_MS = 900_000
MIN_INTERVAL = 1.0 / settings.MAX_REQUESTS_PER_SECOND  # 5 req/s
RAW_DIR = os.path.join(_REPO_ROOT, "data", "raw", "probe_1m")
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


def _throttle():
    global _last_request_ts
    wait = MIN_INTERVAL - (time.monotonic() - _last_request_ts)
    if wait > 0:
        time.sleep(wait)
    _last_request_ts = time.monotonic()


def fetch(label, symbol, granularity, end_time_ms, limit=200):
    global _request_count
    if _request_count >= 10:
        raise RuntimeError("API request budget (10) exhausted.")
    _throttle()
    _request_count += 1
    params = {
        "symbol": symbol,
        "productType": settings.PRODUCT_TYPE,
        "granularity": granularity,
        "endTime": str(end_time_ms),
        "limit": str(limit),
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
    return resp.status_code, code, rows


# ------------------------------------------------------------------ tests
def test1_and_2():
    section("TEST 1 — 1m RETENTION DEPTH (endTime = 2022-01-15T00:00:00Z)")
    end_ms = iso_to_ms("2022-01-15T00:00:00.000Z")
    got = {}
    for sym in SYMBOLS:
        status, code, rows = fetch("t1_retention", sym, "1m", end_ms, 200)
        got[sym] = rows
        if rows:
            ts = sorted(int(r[0]) for r in rows)
            out(f"  {sym}: HTTP {status} code {code} rows {len(rows)}  "
                f"min {utc_iso(ts[0])}  max {utc_iso(ts[-1])}")
        else:
            out(f"  {sym}: HTTP {status} code {code} rows 0  (empty/no data)")

    section("TEST 2 — SPACING AND SHAPE (symbols that returned data)")
    for sym in SYMBOLS:
        rows = got[sym]
        if not rows:
            out(f"  {sym}: no data returned in T1 — skipped.")
            continue
        ts = sorted(int(r[0]) for r in rows)
        diffs = [b - a for a, b in zip(ts[:-1], ts[1:])]
        spacing_ok = all(d == MINUTE_MS for d in diffs)
        field_counts = {len(r) for r in rows}
        out(f"  {sym}: limit=200 -> {len(rows)} rows; "
            f"consecutive diff == 60000ms: {spacing_ok}; "
            f"field counts per row: {sorted(field_counts)}")
        if not spacing_ok:
            bad = [(utc_iso(ts[i]), diffs[i]) for i in range(len(diffs))
                   if diffs[i] != MINUTE_MS][:10]
            out(f"     non-60000 diffs (up to 10): {bad}")


def test3():
    section("TEST 3 — ARE 1m OPENS SYNTHESIZED? (recent BTCUSDT 200-bar 1m)")
    status, code, rows = fetch("t3_opens", "BTCUSDT", "1m", int(time.time()*1000))
    if not rows:
        out(f"  no rows (HTTP {status} code {code}).")
        return
    rows = sorted(rows, key=lambda r: int(r[0]))
    open_s = [str(r[1]) for r in rows]
    close_s = [str(r[4]) for r in rows]
    eq = sum(1 for i in range(1, len(rows)) if open_s[i] == close_s[i - 1])
    tot = len(rows) - 1
    ts = [int(r[0]) for r in rows]
    out(f"  window {utc_iso(ts[0])} .. {utc_iso(ts[-1])}, {len(rows)} bars")
    out(f"  open == previous close (string equality): "
        f"{100.0*eq/tot:.3f}%  ({eq}/{tot})")


def _load_recent_15m_btc():
    """Return one recent, fully-inside 15m BTC bar from the raw file."""
    path = os.path.join(_REPO_ROOT, "data", "raw", "bitget", "BTCUSDT_15m.jsonl")
    last = None
    with open(path) as fh:
        for line in fh:
            if line.strip():
                last = line
    rows = json.loads(last)["response"]
    rows = sorted(rows, key=lambda r: int(r[0]))
    # Pick a bar a few back from the newest so it is definitely closed/settled.
    return rows[-5]


def test4():
    section("TEST 4 — DO 1m BARS RECONSTRUCT THE 15m BAR? (BTCUSDT)")
    bar15 = _load_recent_15m_btc()
    t15 = int(bar15[0])
    h15, l15, c15, v15 = (float(bar15[2]), float(bar15[3]),
                          float(bar15[4]), float(bar15[5]))
    out(f"  reference 15m bar @ {utc_iso(t15)}")
    out(f"    15m  high={h15} low={l15} close={c15} base_vol={v15}")

    # The 15m bar opens at t15 and covers [t15, t15+900000). Its 1m opens are
    # t15 .. t15+14*60000. endTime is EXCLUSIVE, so to include the 1m bar
    # opening at t15+14*60000 we request endTime = t15 + 15*60000.
    end_ms = t15 + 15 * MINUTE_MS
    status, code, rows = fetch("t4_reconstruct", "BTCUSDT", "1m", end_ms, 200)
    if not rows:
        out(f"  no 1m rows returned (HTTP {status} code {code}).")
        return
    rows = sorted(rows, key=lambda r: int(r[0]))
    # Keep exactly the 15 bars whose open is within [t15, t15+900000).
    seg = [r for r in rows if t15 <= int(r[0]) < t15 + BAR15_MS]
    ts = [int(r[0]) for r in seg]
    out(f"  fetched {len(rows)} 1m bars; segment inside the 15m window: "
        f"{len(seg)} (expect 15)")
    if seg:
        out(f"    segment range {utc_iso(ts[0])} .. {utc_iso(ts[-1])}")

    if len(seg) != 15:
        out(f"  WARNING: segment has {len(seg)} bars, not 15 — comparison "
            f"below uses what was returned.")

    m_high = max(float(r[2]) for r in seg)
    m_low = min(float(r[3]) for r in seg)
    m_close = float(seg[-1][4])
    m_vol = sum(float(r[5]) for r in seg)

    out("  reconstruction checks:")
    out(f"    max(1m highs) = {m_high}   vs 15m high = {h15}   "
        f"match: {m_high == h15}  (diff {m_high - h15:+.10g})")
    out(f"    min(1m lows)  = {m_low}   vs 15m low  = {l15}   "
        f"match: {m_low == l15}  (diff {m_low - l15:+.10g})")
    out(f"    last 1m close = {m_close}   vs 15m close = {c15}   "
        f"match: {m_close == c15}  (diff {m_close - c15:+.10g})")
    out(f"    sum(1m vols)  = {m_vol:.10g}   vs 15m vol  = {v15}   "
        f"match: {m_vol == v15}  (diff {m_vol - v15:+.10g})")


def main():
    os.makedirs(REPORTS_DIR, exist_ok=True)
    out("BITGET 1m PROBE (READ-ONLY — no data modified)")
    out(f"generated: {datetime.now(timezone.utc).isoformat()}")
    test1_and_2()
    test3()
    test4()
    out(f"\nTotal API requests made: {_request_count} (budget 10)")
    path = os.path.join(REPORTS_DIR, "probe_1m.txt")
    with open(path, "w") as fh:
        fh.write("\n".join(_BUF) + "\n")
    out(f"Report saved to {path}")


if __name__ == "__main__":
    main()
