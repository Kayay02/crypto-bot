"""Bitget USDT-M venue constraints: retrieval, raw snapshot, and parsing.

WHAT THIS ANSWERS. Report 24 measured that the uncapped book carries a median of
9 positions and $7,182 of notional against $2,000 of capital, and reported that
against `costs.CostConfig.max_leverage = 3.0` -- a number the engine's own source
calls "NOT a probed exchange constraint -- an unmeasured placeholder". Every
statement about whether that book is carryable therefore rested on a figure
nobody had retrieved. This module retrieves the venue's actual constraints.

THIS IS A RETRIEVAL. Nothing here chooses a concurrency cap, a leverage setting
or a margin mode; nothing here is written back to any config; and no engine file
is touched. The output is facts about the exchange.

RAW BEFORE PARSED, AND THE PARSER READS FROM DISK. Every response body is
written to `data/reference/bitget_venue/` verbatim -- the bytes the server sent, not a
re-serialised dict -- before any parsing happens, and every parsed table in the
report is derived by reading those files back. A report cannot then describe
something the snapshot does not contain, and the SHA-256 recorded in the
manifest is what proves it.

ENDPOINTS ARE DISCOVERED, NOT REMEMBERED. `ENDPOINTS` below carries, for each
path, the documentation page that identified it. A stale path that 404s is
better than a stale path that returns something plausible from a different
resource, so the retrieval refuses anything that is not HTTP 200 with Bitget's
success code, and the parser refuses a response whose fields it does not
recognise rather than defaulting them.

THE DOCUMENTATION PAGES ARE JS-RENDERED. `www.bitget.com/api-doc/...` returns an
application shell to an automated fetch and no endpoint content -- the same
finding `src/costs/build_fee_artifact.py` recorded for `www.bitget.com/fee`. The
paths below were identified from those pages' indexed content and then CONFIRMED
AGAINST THE LIVE API, which is the primary source in any case. The doc URLs are
recorded so a human can check them; they were not parsed.

NO MARKET DATA. This module imports nothing from `src/timeframe`, `src/folds`,
`src/analysis` or the engine. It touches the data layer not at all, so the
holdout is trivially untouched and no seal test applies. A test asserts the
import graph rather than trusting this paragraph.

THE PERFORMANCE FIREWALL IS ARMED, AND WIDENED. No expectancy, win rate, profit
factor, Sharpe, Sortino, equity curve, drawdown, r_multiple, net_pnl or
gross_pnl quantity is computed, inspected or referenced. Report 24 noted that
`drawdown`, `sortino` and `gross_pnl` were absent from the guard's name list;
the test module here carries the widened list.

TODAY'S PARAMETERS, NOT THE WINDOW'S. Everything retrieved here is the venue's
CURRENT state. Bitget's contracts and position-tier endpoints publish no
history, so this retrieval cannot establish what the tiers, caps or lot sizes
were during 2022-2024. That is a stated limitation, on the same footing as the
thesis's 0.01%/8h funding assumption.
"""

import hashlib
import json
import os
import random
import sys
import time
from datetime import datetime, timezone

import requests

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)

from config import settings  # noqa: E402

# ---------------------------------------------------------------------------
# Endpoints. Discovered from the documentation, confirmed against the API.
# ---------------------------------------------------------------------------

BASE_URL = settings.BASE_URL
PRODUCT_TYPE = settings.PRODUCT_TYPE
SYMBOLS = tuple(settings.SYMBOLS)

CONTRACTS_PATH = "/api/v2/mix/market/contracts"
POSITION_TIER_PATH = "/api/v2/mix/market/query-position-lever"

ENDPOINTS = {
    CONTRACTS_PATH: {
        "name": "Get Contract Config",
        "doc_url": "https://www.bitget.com/api-doc/contract/market/"
                   "Get-All-Symbols-Contracts",
        "provides": "lot granularity, price tick inputs, minimum and maximum "
                    "order size, per-symbol and per-product order and position "
                    "count limits, symbol leverage bounds, funding interval",
        "auth": "public -- no key, no signing",
    },
    POSITION_TIER_PATH: {
        "name": "Get Position Tier",
        "doc_url": "https://www.bitget.com/api-doc/contract/position/"
                   "Get-Query-Position-Lever",
        "provides": "the per-symbol leverage and maintenance margin tier "
                    "table: notional band, maximum leverage, maintenance "
                    "margin rate",
        "auth": "public -- no key, no signing",
    },
}

#: THE SNAPSHOT LIVES UNDER data/reference/, NOT data/raw/. `/data/` is ignored
#: wholesale and each committed artifact earns a named negation in .gitignore
#: with its justification -- that is where `bitget_fees.json` and
#: `bitget_instruments.json` already sit, and this is the same kind of thing:
#: a small, dated, provenance-stamped reading of the venue that a report rests
#: on. `data/raw/` holds bulk market-data captures and stays untracked; an
#: untracked snapshot could not prove what the report was derived from.
SNAPSHOT_DIR = os.path.join(ROOT, "data", "reference", "bitget_venue")
MANIFEST_PATH = os.path.join(SNAPSHOT_DIR, "manifest.json")
CACHE_PATH = os.path.join(ROOT, "config", "contracts_cache.json")

USER_AGENT = "crypto-bot/venue-constraints"
TIMEOUT_S = 30

# Retry and throttle policy, transcribed from src/data/backfill_bitget.py so
# this module is not a second, differently-behaved Bitget client.
MIN_INTERVAL = 1.0 / settings.MAX_REQUESTS_PER_SECOND
MAX_ATTEMPTS = 4
RETRY_HTTP = {429}
RETRY_API_CODES = {"45001", "40725", "40808"}
BASE_BACKOFF = 0.5
SUCCESS_CODE = "00000"

_last_request_ts = 0.0

#: The notional range this project can reach. Report 24's worst bar is $27,045.
#: The tier table is asserted to cover it with no gap.
COVERAGE_USD = 30_000.0

#: Book states measured by report 24 §7.1, carried here ONLY so each can be
#: mapped to the tier it falls in. No figure here is recomputed from bars and
#: none is a performance quantity.
BOOK_STATES_USD = {
    "median": 7_182.00,
    "p99": 17_826.90,
    "maximum": 27_045.20,
}


class RetrievalFailed(Exception):
    """The venue could not be reached, or answered with something unusable."""


class SchemaError(Exception):
    """A response is missing a field the report depends on, or it is unusable.

    Separate from RetrievalFailed because they fail at different times and mean
    different things: one says the network or the venue is wrong, the other
    says our reading of the venue is wrong. A parser that defaulted a missing
    field would produce a report claiming a constraint the venue never stated.
    """


# ---------------------------------------------------------------------------
# HTTP, throttled and retrying.
# ---------------------------------------------------------------------------

def stamp():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def log(msg):
    print("[%s] %s" % (stamp(), msg), flush=True)


def _throttle():
    global _last_request_ts
    wait = MIN_INTERVAL - (time.monotonic() - _last_request_ts)
    if wait > 0:
        time.sleep(wait)
    _last_request_ts = time.monotonic()


def _backoff(attempt):
    return BASE_BACKOFF * (2 ** (attempt - 1)) + random.uniform(0, 0.25)


def fetch_raw(path, params):
    """One throttled, retrying GET. Returns (url, params, status, body_text).

    RETURNS TEXT, NOT A PARSED DICT. The snapshot must hold what the server
    sent; parsing it here and re-serialising it on the way to disk would make
    the snapshot a record of this module's json library rather than of the
    venue's response.
    """
    url = BASE_URL + path
    for attempt in range(1, MAX_ATTEMPTS + 1):
        _throttle()
        try:
            resp = requests.get(url, params=params, timeout=TIMEOUT_S,
                                headers={"User-Agent": USER_AGENT})
        except requests.RequestException as exc:
            if attempt < MAX_ATTEMPTS:
                delay = _backoff(attempt)
                log("RETRY %s attempt %d network error %r; sleeping %.2fs"
                    % (path, attempt, exc, delay))
                time.sleep(delay)
                continue
            raise RetrievalFailed("network failure contacting %s after %d "
                                  "attempts: %r" % (url, MAX_ATTEMPTS, exc))

        text = resp.text
        try:
            body = resp.json()
        except ValueError:
            body = None
        code = body.get("code") if isinstance(body, dict) else None
        msg = body.get("msg") if isinstance(body, dict) else None

        if resp.status_code == 200 and code == SUCCESS_CODE:
            return resp.url, dict(params), resp.status_code, text

        retryable = (resp.status_code in RETRY_HTTP
                     or 500 <= resp.status_code < 600
                     or code in RETRY_API_CODES)
        if not retryable:
            raise RetrievalFailed(
                "non-retryable response from %s: HTTP %s code %r msg %r "
                "params %r" % (url, resp.status_code, code, msg, params))
        if attempt < MAX_ATTEMPTS:
            delay = _backoff(attempt)
            log("RETRY %s attempt %d HTTP %s code %r; sleeping %.2fs"
                % (path, attempt, resp.status_code, code, delay))
            time.sleep(delay)
            continue
        raise RetrievalFailed(
            "retryable error persisted at %s after %d attempts (HTTP %s "
            "code %r msg %r)" % (url, MAX_ATTEMPTS, resp.status_code, code, msg))


# ---------------------------------------------------------------------------
# The raw snapshot.
# ---------------------------------------------------------------------------

def sha256_of(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def snapshot_name(path, symbol):
    """One file per endpoint call. The name carries both, so a file is
    self-identifying without opening the manifest."""
    leaf = path.rstrip("/").rsplit("/", 1)[-1]
    return "%s__%s.json" % (leaf, symbol)


def write_raw(name, text, snapshot_dir=SNAPSHOT_DIR):
    """Write the body verbatim and return (path, sha256).

    Written in BINARY with the response's own text encoded UTF-8 and no
    trailing newline added: a newline appended for tidiness would change the
    hash of a file whose whole purpose is to be hashed.
    """
    os.makedirs(snapshot_dir, exist_ok=True)
    path = os.path.join(snapshot_dir, name)
    with open(path, "wb") as fh:
        fh.write(text.encode("utf-8"))
    return path, sha256_of(path)


def retrieve(symbols=SYMBOLS, snapshot_dir=SNAPSHOT_DIR,
             manifest_path=MANIFEST_PATH):
    """Call every endpoint for every symbol, snapshot raw, write the manifest.

    THE MANIFEST IS PROVENANCE, NOT DATA. It records for each call the full
    request URL, the query parameters, the HTTP status, the UTC retrieval
    timestamp, the snapshot filename and its SHA-256. Nothing parsed goes into
    it -- the parsed tables are derived from the snapshot files by the callers
    below, so the manifest cannot disagree with them.
    """
    retrieved_at = stamp()
    calls = []
    for path in (CONTRACTS_PATH, POSITION_TIER_PATH):
        for symbol in symbols:
            params = {"productType": PRODUCT_TYPE, "symbol": symbol}
            url, sent, status, text = fetch_raw(path, params)
            name = snapshot_name(path, symbol)
            file_path, digest = write_raw(name, text, snapshot_dir)
            calls.append({
                "endpoint_path": path,
                "endpoint_name": ENDPOINTS[path]["name"],
                "doc_url": ENDPOINTS[path]["doc_url"],
                "auth": ENDPOINTS[path]["auth"],
                "request_url": url,
                "params": sent,
                "http_status": status,
                "retrieved_at_utc": stamp(),
                "snapshot_file": os.path.basename(file_path),
                "sha256": digest,
                "bytes": os.path.getsize(file_path),
            })
            log("%s %s -> %s (%d bytes)"
                % (path, symbol, os.path.basename(file_path),
                   os.path.getsize(file_path)))

    manifest = {
        "retrieved_at_utc": retrieved_at,
        "base_url": BASE_URL,
        "product_type": PRODUCT_TYPE,
        "symbols": list(symbols),
        "retrieval_method": "automated, public endpoints, no credentials",
        "documentation_note": (
            "Endpoint paths were identified from Bitget's published API "
            "documentation pages listed as doc_url and then confirmed against "
            "the live API. Those pages are JS-rendered and return no endpoint "
            "content to an automated fetch, so they were NOT parsed and are "
            "recorded for human verification only."),
        "calls": calls,
    }
    os.makedirs(os.path.dirname(manifest_path), exist_ok=True)
    with open(manifest_path, "w") as fh:
        json.dump(manifest, fh, indent=2, sort_keys=True)
        fh.write("\n")
    return manifest


def load_manifest(manifest_path=MANIFEST_PATH):
    if not os.path.exists(manifest_path):
        raise RetrievalFailed(
            "no venue snapshot at %s; run `python -m src.venue."
            "bitget_constraints`" % manifest_path)
    with open(manifest_path) as fh:
        return json.load(fh)


def load_raw(name, snapshot_dir=SNAPSHOT_DIR):
    """Read one snapshot file back and return its decoded body.

    THE PARSING PATH STARTS HERE, ON DISK. Nothing downstream sees an in-memory
    response object.
    """
    path = os.path.join(snapshot_dir, name)
    if not os.path.exists(path):
        raise SchemaError("snapshot file missing: %s" % path)
    with open(path, "rb") as fh:
        text = fh.read().decode("utf-8")
    try:
        body = json.loads(text)
    except ValueError as exc:
        raise SchemaError("%s is not valid JSON: %s" % (path, exc))
    if not isinstance(body, dict):
        raise SchemaError("%s did not decode to an object" % path)
    if body.get("code") != SUCCESS_CODE:
        raise SchemaError("%s carries code=%r msg=%r, not success"
                          % (path, body.get("code"), body.get("msg")))
    return body


# ---------------------------------------------------------------------------
# Parsing. Every field the report depends on is required and typed.
# ---------------------------------------------------------------------------

def _rows(body, where):
    data = body.get("data")
    if not isinstance(data, list):
        raise SchemaError("%s: `data` is %s, expected a list"
                          % (where, type(data).__name__))
    if not data:
        raise SchemaError(
            "%s: `data` is an EMPTY list. An empty tier or contract table "
            "would be reported as the venue imposing no constraint, which is "
            "the most dangerous failure available here." % where)
    return data


def _req(row, field, where):
    if field not in row:
        raise SchemaError("%s: required field %r is absent; the endpoint's "
                          "schema may have changed" % (where, field))
    return row[field]


def _num(row, field, where, allow_zero=True, allow_negative=False):
    raw = _req(row, field, where)
    try:
        value = float(raw)
    except (TypeError, ValueError):
        raise SchemaError("%s: %r is not numeric: %r" % (where, field, raw))
    if value != value or value in (float("inf"), float("-inf")):
        raise SchemaError("%s: %r is not finite: %r" % (where, field, raw))
    if not allow_negative and value < 0.0:
        raise SchemaError("%s: %r is negative: %r" % (where, field, raw))
    if not allow_zero and value == 0.0:
        raise SchemaError("%s: %r is zero" % (where, field))
    return value


def _int(row, field, where):
    value = _num(row, field, where)
    if value != int(value):
        raise SchemaError("%s: %r is not integral: %r" % (where, field,
                                                          row[field]))
    return int(value)


CONTRACT_REQUIRED = ("symbol", "minTradeNum", "sizeMultiplier", "minTradeUSDT",
                     "priceEndStep", "pricePlace", "volumePlace", "maxLever",
                     "minLever", "maxOrderQty", "maxMarketOrderQty",
                     "maxSymbolOrderNum", "maxProductOrderNum",
                     "maxPositionNum", "symbolType", "symbolStatus",
                     "fundInterval", "supportMarginCoins")


def parse_contract(body, symbol):
    """One symbol's contract specification, every field required.

    THE PRICE TICK IS DERIVED, NOT READ. `tick = priceEndStep * 10**-pricePlace`
    -- NOT `10**-pricePlace`, which coincides today only because priceEndStep is
    1 on all three symbols. `src/engine/contracts.py` states the same rule and
    the two must not diverge.

    THERE IS NO SEPARATE CONTRACT-SIZE FIELD. Quantity is denominated in the
    base coin and `sizeMultiplier` is the step it must be a multiple of; the
    response carries no contract multiplier, so one base unit is one unit of
    quantity. Recorded because "contract size" is a field on other venues and
    its absence here is a fact, not an omission.
    """
    where = "contracts[%s]" % symbol
    rows = _rows(body, where)
    matched = [r for r in rows if isinstance(r, dict) and r.get("symbol") == symbol]
    if len(matched) != 1:
        raise SchemaError("%s: expected exactly one row for %s, got %d"
                          % (where, symbol, len(matched)))
    row = matched[0]
    for field in CONTRACT_REQUIRED:
        _req(row, field, where)

    if row["symbolType"] != "perpetual":
        raise SchemaError("%s: symbolType is %r, not 'perpetual'"
                          % (where, row["symbolType"]))
    coins = row["supportMarginCoins"]
    if not isinstance(coins, list) or "USDT" not in coins:
        raise SchemaError("%s: supportMarginCoins %r does not include USDT"
                          % (where, coins))

    price_place = _int(row, "pricePlace", where)
    price_end_step = _int(row, "priceEndStep", where)
    out = {
        "symbol": symbol,
        "qty_step": _num(row, "sizeMultiplier", where, allow_zero=False),
        "min_trade_qty": _num(row, "minTradeNum", where, allow_zero=False),
        "min_trade_usdt": _num(row, "minTradeUSDT", where, allow_zero=False),
        "qty_decimals": _int(row, "volumePlace", where),
        "price_decimals": price_place,
        "price_end_step": price_end_step,
        "tick_size": price_end_step * (10.0 ** -price_place),
        "min_leverage": _num(row, "minLever", where, allow_zero=False),
        "max_leverage": _num(row, "maxLever", where, allow_zero=False),
        "max_order_qty": _num(row, "maxOrderQty", where, allow_zero=False),
        "max_market_order_qty": _num(row, "maxMarketOrderQty", where,
                                     allow_zero=False),
        "max_orders_per_symbol": _int(row, "maxSymbolOrderNum", where),
        "max_orders_per_product": _int(row, "maxProductOrderNum", where),
        "max_positions": _int(row, "maxPositionNum", where),
        "funding_interval_hours": _int(row, "fundInterval", where),
        "symbol_status": row["symbolStatus"],
        "margin_coins": list(coins),
        # Present in the response and NOT interpreted here: the documentation
        # available to an automated fetch does not define it. Carried so the
        # snapshot's content is fully represented rather than silently trimmed.
        "pos_limit_raw": row.get("posLimit"),
    }
    if out["min_trade_qty"] < out["qty_step"]:
        raise SchemaError("%s: minTradeNum %r is below sizeMultiplier %r"
                          % (where, out["min_trade_qty"], out["qty_step"]))
    return out


TIER_REQUIRED = ("symbol", "level", "startUnit", "endUnit", "leverage",
                 "keepMarginRate")


def parse_tiers(body, symbol):
    """One symbol's leverage / maintenance margin tier table, ascending.

    `keepMarginRate` IS THE MAINTENANCE MARGIN RATE, as a decimal fraction:
    0.0040 is 0.40%. `startUnit` and `endUnit` bound the POSITION VALUE in
    USDT. `leverage` is the maximum permitted while the position sits in that
    band.

    Sorted by level and then structurally checked, so a response that arrived
    out of order is handled while a response with a genuine gap is refused.
    """
    where = "position-tier[%s]" % symbol
    rows = _rows(body, where)
    out = []
    for row in rows:
        if not isinstance(row, dict):
            raise SchemaError("%s: a tier row is %s, expected an object"
                              % (where, type(row).__name__))
        for field in TIER_REQUIRED:
            _req(row, field, where)
        if row["symbol"] != symbol:
            raise SchemaError("%s: a row carries symbol %r"
                              % (where, row["symbol"]))
        out.append({
            "symbol": symbol,
            "level": _int(row, "level", where),
            "start_usd": _num(row, "startUnit", where),
            "end_usd": _num(row, "endUnit", where, allow_zero=False),
            "max_leverage": _num(row, "leverage", where, allow_zero=False),
            "maintenance_margin_rate": _num(row, "keepMarginRate", where,
                                            allow_zero=False),
        })
    out.sort(key=lambda t: t["level"])
    _assert_tier_structure(out, where)
    return out


def _assert_tier_structure(tiers, where):
    """Levels consecutive from 1, bands contiguous and ascending, rates rising.

    A gap between bands would leave a notional that maps to no tier, and the
    coverage assertion downstream would then be checking a table that cannot
    answer the question it is being asked.
    """
    if [t["level"] for t in tiers] != list(range(1, len(tiers) + 1)):
        raise SchemaError("%s: levels are not 1..N consecutive: %s"
                          % (where, [t["level"] for t in tiers]))
    if tiers[0]["start_usd"] != 0.0:
        raise SchemaError("%s: tier 1 starts at %r, not 0"
                          % (where, tiers[0]["start_usd"]))
    for lo, hi in zip(tiers, tiers[1:]):
        if lo["end_usd"] <= lo["start_usd"]:
            raise SchemaError("%s: tier %d band is empty or inverted"
                              % (where, lo["level"]))
        if hi["start_usd"] != lo["end_usd"]:
            raise SchemaError(
                "%s: GAP between tier %d (ends %r) and tier %d (starts %r); a "
                "notional in the gap maps to no tier"
                % (where, lo["level"], lo["end_usd"], hi["level"],
                   hi["start_usd"]))
        if hi["maintenance_margin_rate"] < lo["maintenance_margin_rate"]:
            raise SchemaError(
                "%s: maintenance margin rate FALLS from tier %d to %d; the "
                "tier system exists to raise it with size"
                % (where, lo["level"], hi["level"]))
        if hi["max_leverage"] > lo["max_leverage"]:
            raise SchemaError(
                "%s: maximum leverage RISES from tier %d to %d"
                % (where, lo["level"], hi["level"]))
    if tiers[-1]["end_usd"] <= tiers[-1]["start_usd"]:
        raise SchemaError("%s: the last tier's band is empty or inverted"
                          % where)


def assert_covers(tiers, up_to=COVERAGE_USD):
    """The table must reach `up_to` with no gap. Raises if it does not."""
    top = tiers[-1]["end_usd"]
    if top < up_to:
        raise SchemaError(
            "tier table for %s reaches only %r, below the %r this project can "
            "carry" % (tiers[0]["symbol"], top, up_to))
    return True


def tier_for(tiers, notional_usd):
    """The single tier a position value falls in.

    BANDS ARE READ AS [start, end]: a value on a boundary belongs to the LOWER
    tier, which is the reading that makes `endUnit` an upper bound rather than
    an exclusive edge. The choice matters only exactly on a boundary and is
    stated rather than left implicit.
    """
    if notional_usd < 0.0:
        raise ValueError("notional must be non-negative, got %r" % notional_usd)
    for t in tiers:
        if t["start_usd"] <= notional_usd <= t["end_usd"]:
            return t
    raise SchemaError("notional %r falls outside the tier table for %s "
                      "(top %r)" % (notional_usd, tiers[0]["symbol"],
                                    tiers[-1]["end_usd"]))


def tier_offset(tiers, level):
    """The tier's pre-calculated offset, DERIVED from the table -- not retrieved.

    Bitget's documented maintenance-margin formula for classic-account futures
    is progressive: each slice of the position value is charged its own tier's
    rate, expressed as

        maintenance margin = position value x rate(tier) - offset(tier)

    The endpoint publishes the bands and the rates but NOT the offset, so it is
    reconstructed here as the amount by which charging the whole position at
    the top tier's rate overstates the progressive sum:

        offset(k) = SUM over j < k of (end_j - start_j) x (rate_k - rate_j)

    OFFSET(1) IS ZERO BY CONSTRUCTION -- there is no lower tier to discount --
    which is why the progressive change does not move any figure that stays
    inside tier 1. A test asserts this expression reproduces the progressive
    sum exactly at every band edge, so the derivation is checked rather than
    asserted.
    """
    if not 1 <= level <= len(tiers):
        raise ValueError("no tier %r" % level)
    rate = tiers[level - 1]["maintenance_margin_rate"]
    return sum((t["end_usd"] - t["start_usd"]) * (rate - t["maintenance_margin_rate"])
               for t in tiers[:level - 1])


def maintenance_margin(tiers, notional_usd):
    """Progressive maintenance margin in USDT, per the documented formula."""
    t = tier_for(tiers, notional_usd)
    return notional_usd * t["maintenance_margin_rate"] - tier_offset(
        tiers, t["level"])


def maintenance_margin_flat(tiers, notional_usd):
    """The SUPERSEDED whole-position form: value x the top tier's rate.

    Kept so the report can show both, because the change from this to the
    progressive form is recent and a reader checking the arithmetic against an
    older Bitget page would otherwise find a discrepancy and not know which is
    which. Identical to `maintenance_margin` inside tier 1.
    """
    return notional_usd * tier_for(tiers, notional_usd)["maintenance_margin_rate"]


# ---------------------------------------------------------------------------
# Cross-check against the committed contract cache. Reported, never resolved.
# ---------------------------------------------------------------------------

def load_cache(path=CACHE_PATH):
    if not os.path.exists(path):
        raise SchemaError("contracts cache missing at %s" % path)
    with open(path) as fh:
        return json.load(fh)


def cross_check_cache(spec, cache=None, cache_path=CACHE_PATH):
    """Field-by-field comparison of one live spec against the committed cache.

    RETURNS THE COMPARISON; RESOLVES NOTHING. A disagreement is a row with
    `agrees: False`, for the report to state. Silently preferring either side
    would be a decision, and this step takes none.

    The cache's tick is a SCHEDULE over time -- SOLUSDT moved from a 0.0001 to
    a 0.001 grid in 2024 -- so the live tick is compared against the cache's
    CURRENT segment, the last one, and that is stated in the row.
    """
    cache = load_cache(cache_path) if cache is None else cache
    entry = cache.get("symbols", {}).get(spec["symbol"])
    if entry is None:
        raise SchemaError("cache has no entry for %s" % spec["symbol"])
    order = entry.get("order") or {}
    segments = entry.get("segments") or []
    if not segments:
        raise SchemaError("cache has no tick segments for %s" % spec["symbol"])
    cached_tick = float(segments[-1][1])

    rows = [
        ("qty_step", spec["qty_step"], _opt_float(order.get("qty_step")),
         "cache: symbols.%s.order.qty_step" % spec["symbol"]),
        ("min_trade_qty", spec["min_trade_qty"],
         _opt_float(order.get("min_trade_num")),
         "cache: symbols.%s.order.min_trade_num" % spec["symbol"]),
        ("min_trade_usdt", spec["min_trade_usdt"],
         _opt_float(order.get("min_trade_usdt")),
         "cache: symbols.%s.order.min_trade_usdt" % spec["symbol"]),
        ("tick_size", spec["tick_size"], cached_tick,
         "cache: symbols.%s.segments[-1] (current segment of %d)"
         % (spec["symbol"], len(segments))),
    ]
    out = []
    for field, live, cached, source in rows:
        agrees = (cached is not None
                  and abs(live - cached) <= 1e-12 * max(1.0, abs(live)))
        out.append({"field": field, "live": live, "cached": cached,
                    "agrees": bool(agrees), "cache_source": source})
    return out


def _opt_float(raw):
    if raw is None:
        return None
    try:
        return float(raw)
    except (TypeError, ValueError):
        return None


# ---------------------------------------------------------------------------
# The whole pass, from disk.
# ---------------------------------------------------------------------------

def parse_snapshot(symbols=SYMBOLS, snapshot_dir=SNAPSHOT_DIR,
                   cache_path=CACHE_PATH):
    """Every parsed table the report states, read back from the raw files."""
    out = {"contracts": {}, "tiers": {}, "cache_check": {}, "book_tiers": {}}
    for symbol in symbols:
        contract_body = load_raw(snapshot_name(CONTRACTS_PATH, symbol),
                                 snapshot_dir)
        tier_body = load_raw(snapshot_name(POSITION_TIER_PATH, symbol),
                             snapshot_dir)
        spec = parse_contract(contract_body, symbol)
        tiers = parse_tiers(tier_body, symbol)
        assert_covers(tiers)
        out["contracts"][symbol] = spec
        out["tiers"][symbol] = tiers
        out["cache_check"][symbol] = cross_check_cache(spec,
                                                       cache_path=cache_path)
        out["book_tiers"][symbol] = {
            name: {
                "notional_usd": value,
                "tier": tier_for(tiers, value)["level"],
                "max_leverage": tier_for(tiers, value)["max_leverage"],
                "maintenance_margin_rate":
                    tier_for(tiers, value)["maintenance_margin_rate"],
                "maintenance_margin_usd": maintenance_margin(tiers, value),
            }
            for name, value in BOOK_STATES_USD.items()
        }
    return out


def main(argv=None):
    log("retrieving venue constraints for %s" % ", ".join(SYMBOLS))
    for path, meta in ENDPOINTS.items():
        log("  %s  (%s, %s)" % (BASE_URL + path, meta["name"], meta["auth"]))
    manifest = retrieve()
    log("snapshot written: %d files under %s" % (len(manifest["calls"]),
                                                 SNAPSHOT_DIR))
    parsed = parse_snapshot()
    for symbol in SYMBOLS:
        spec = parsed["contracts"][symbol]
        tiers = parsed["tiers"][symbol]
        log("%s: qty_step=%s tick=%s max_lever=%s tiers=%d tier1=[%s, %s] "
            "lev %s mmr %s"
            % (symbol, spec["qty_step"], spec["tick_size"],
               spec["max_leverage"], len(tiers), tiers[0]["start_usd"],
               tiers[0]["end_usd"], tiers[0]["max_leverage"],
               tiers[0]["maintenance_margin_rate"]))
        for row in parsed["cache_check"][symbol]:
            if not row["agrees"]:
                log("  CACHE DISAGREEMENT %s: live=%r cached=%r"
                    % (row["field"], row["live"], row["cached"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
