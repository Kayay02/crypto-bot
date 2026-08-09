"""Tick size, one live price, and the structural floor under per-side slippage.

WHY THIS IS CHEAP, AND WHY IT IS ENOUGH TO TRY FIRST. Report 17 left the
slippage question as a single comparison: measure realised per-side slippage and
read one cell of the break-even table. The obvious way to do that is expensive
-- book snapshots or live fills. But a market order that does not exhaust
top-of-book depth pays half the bid-ask spread and nothing else, and at $400 to
$5,500 of notional on BTC/ETH/SOL perpetuals it does not come close to
exhausting top of book. So slippage is approximately half the spread, book depth
drops out, and the spread has a hard floor of one tick. Tick size is published
and a price is one HTTP call.

That gives a LOWER BOUND, which is the useful direction: if the break-even
tolerance is many multiples of the one-tick floor, no measurement can change the
verdict and the question closes without spending anything.

WHAT THIS MODULE MAY NOT DO. It reads instrument specifications and ONE
point-in-time price per symbol, used solely to convert a tick into basis points.
That price is not a bar, not a series, not an input to any strategy or
parameter, and it touches no historical window and no holdout. There is no
candle endpoint here, no parquet, no engine import. If a future edit needs a
second price for the same symbol, it has left the scope of this module.

THE BOUND IS ON NORMAL CONDITIONS ONLY. See `NORMAL_CONDITIONS_ONLY` below --
the stop leg is always a taker fill during an adverse move, which is exactly
when spreads widen. This module cannot see that and does not pretend to.

DENOMINATION. Tick sizes and prices are absolute; everything derived is in basis
points of price, per side, matching `slip` in `src/costs/envelope.py` after a
factor of 1e4. Break-even figures are IMPORTED from that module, never restated.
"""

import argparse
import json
import math
import os
import sys
from datetime import datetime, timezone

import requests

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
REFERENCE_DIR = os.path.join(ROOT, "data", "reference")
INSTRUMENTS_PATH = os.path.join(REFERENCE_DIR, "bitget_instruments.json")
FEES_PATH = os.path.join(REFERENCE_DIR, "bitget_fees.json")

CONTRACTS_URL = (
    "https://api.bitget.com/api/v2/mix/market/contracts?productType=USDT-FUTURES"
)
TICKERS_URL = (
    "https://api.bitget.com/api/v2/mix/market/tickers?productType=USDT-FUTURES"
)

SYMBOLS = ("BTCUSDT", "ETHUSDT", "SOLUSDT")

#: Spread widths tabulated in report 18, in ticks.
TICK_COUNTS = (1, 2, 3, 5, 10)

REQUIRED_PER_SYMBOL = (
    "tick_size", "qty_step", "min_trade_qty", "price", "price_field",
)

TIMEOUT_S = 30

NORMAL_CONDITIONS_ONLY = """\
This floor bounds slippage under NORMAL spread conditions and nothing else.

A stop-loss exit is a market order that fires during a fast adverse move --
precisely when spreads widen and top-of-book depth thins. The stop leg is ALWAYS
taker; it cannot be worked as a maker order, because the whole point of it is
that it must execute now. A tick-size floor therefore UNDERSTATES stop-leg
slippage, by an unknown amount.

The headroom multiple (tolerable spread / one-tick floor) is the margin
available to absorb that widening. Where it is large the asymmetry is
immaterial; where it is small it is not, and this method cannot resolve it.
This module does NOT estimate how far spreads widen in fast markets -- that
needs data it does not have.
"""


class InstrumentArtifactError(Exception):
    """The instrument artifact is absent, unreadable, or fails its contract."""


class RetrievalFailed(Exception):
    """Retrieval failed or did not validate. Nothing is guessed or remembered."""


def _fetch(url, timeout=TIMEOUT_S):
    resp = requests.get(
        url, timeout=timeout, headers={"User-Agent": "crypto-bot/tick-probe"}
    )
    if resp.status_code != 200:
        raise RetrievalFailed("HTTP %s from %s" % (resp.status_code, url))
    body = resp.json()
    if body.get("code") != "00000":
        raise RetrievalFailed(
            "Bitget returned code=%r msg=%r for %s"
            % (body.get("code"), body.get("msg"), url)
        )
    rows = body.get("data")
    if not isinstance(rows, list) or not rows:
        raise RetrievalFailed("%s returned no rows" % url)
    return rows


def _positive_float(raw, label):
    try:
        v = float(raw)
    except (TypeError, ValueError):
        raise RetrievalFailed("%s is not numeric: %r" % (label, raw))
    if not math.isfinite(v) or v <= 0.0:
        raise RetrievalFailed("%s is not finite and positive: %r" % (label, raw))
    return v


def _tick_size(row):
    """Minimum price increment = priceEndStep * 10**-pricePlace.

    Bitget publishes the increment as a pair: `pricePlace` decimal places and
    `priceEndStep` steps of the last place. Both are needed -- a contract with
    pricePlace=1 and priceEndStep=5 ticks in 0.5, not 0.1 -- so reading only
    pricePlace would silently understate the tick on any instrument that uses
    a coarser end step.
    """
    place = row.get("pricePlace")
    end_step = row.get("priceEndStep")
    if place is None or end_step is None:
        raise RetrievalFailed(
            "contract %r is missing pricePlace/priceEndStep" % row.get("symbol")
        )
    try:
        place_i = int(place)
        end_i = int(end_step)
    except (TypeError, ValueError):
        raise RetrievalFailed(
            "contract %r has non-integer pricePlace=%r priceEndStep=%r"
            % (row.get("symbol"), place, end_step)
        )
    if place_i < 0 or end_i <= 0:
        raise RetrievalFailed(
            "contract %r has out-of-range pricePlace=%r priceEndStep=%r"
            % (row.get("symbol"), place, end_step)
        )
    return end_i * (10.0 ** -place_i)


def retrieve(price_field="lastPr"):
    """Return the artifact payload. Raises RetrievalFailed; never substitutes."""
    retrieved_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()

    try:
        contracts = _fetch(CONTRACTS_URL)
        tickers = _fetch(TICKERS_URL)
    except requests.RequestException as exc:
        raise RetrievalFailed("network error: %s" % exc)
    except json.JSONDecodeError as exc:
        raise RetrievalFailed("endpoint did not return JSON: %s" % exc)

    cby = {r.get("symbol"): r for r in contracts if isinstance(r, dict)}
    tby = {r.get("symbol"): r for r in tickers if isinstance(r, dict)}
    missing = [s for s in SYMBOLS if s not in cby or s not in tby]
    if missing:
        raise RetrievalFailed(
            "missing from contracts or tickers response: %s" % ", ".join(missing)
        )

    instruments = {}
    for sym in SYMBOLS:
        c, t = cby[sym], tby[sym]
        tick = _tick_size(c)
        price = _positive_float(t.get(price_field), "%s %s" % (sym, price_field))
        if tick >= price:
            raise RetrievalFailed(
                "%s tick %r is not smaller than price %r; one of the two is "
                "wrong and the bps conversion would be meaningless" % (sym, tick, price)
            )
        entry = {
            "tick_size": tick,
            "price_place": int(c["pricePlace"]),
            "price_end_step": int(c["priceEndStep"]),
            "qty_step": c.get("sizeMultiplier"),
            "min_trade_qty": c.get("minTradeNum"),
            "min_notional_usdt": c.get("minTradeUSDT"),
            "price": price,
            "price_field": price_field,
            "price_ts_ms": t.get("ts"),
        }
        # Corroboration only: the instantaneous top of book at the same instant
        # as `price`. ONE reading, not a distribution -- it can show that the
        # book was at N ticks then, and nothing whatever about typical or
        # adverse conditions.
        bid = t.get("bidPr")
        ask = t.get("askPr")
        if bid is not None and ask is not None:
            b, a = float(bid), float(ask)
            if a > b > 0:
                entry["observed_bid"] = b
                entry["observed_ask"] = a
                entry["observed_spread_ticks"] = round((a - b) / tick, 4)
        instruments[sym] = entry

    return {
        "instruments": instruments,
        "source_urls": {"contracts": CONTRACTS_URL, "tickers": TICKERS_URL},
        "retrieved_at": retrieved_at,
        "retrieval_method": "automated",
        "price_semantics": (
            "A SINGLE POINT-IN-TIME reading per symbol, used only to convert a "
            "tick size into basis points. It is not a bar, not a series, not an "
            "input to any strategy or parameter, and no historical window or "
            "holdout was touched to obtain it."
        ),
        "tick_size_derivation": "priceEndStep * 10**-pricePlace",
        "notes": NORMAL_CONDITIONS_ONLY,
    }


# ---------------------------------------------------------------------------
# The artifact.
# ---------------------------------------------------------------------------

def load_instruments(path=INSTRUMENTS_PATH):
    """Read and validate the instrument artifact. Raises, never defaults."""
    if not os.path.exists(path):
        raise InstrumentArtifactError(
            "instrument artifact not found at %s. Build it with "
            "`python src/costs/tick_probe.py`. This module has no default tick "
            "size or price and will not proceed without one." % path
        )
    try:
        with open(path) as fh:
            raw = json.load(fh)
    except json.JSONDecodeError as exc:
        raise InstrumentArtifactError(
            "instrument artifact at %s is not valid JSON: %s" % (path, exc)
        )
    if not isinstance(raw, dict):
        raise InstrumentArtifactError(
            "instrument artifact at %s must be a JSON object" % path
        )
    for field in ("instruments", "retrieved_at", "retrieval_method", "source_urls"):
        if field not in raw:
            raise InstrumentArtifactError(
                "instrument artifact at %s is missing required field %r"
                % (path, field)
            )
    inst = raw["instruments"]
    if not isinstance(inst, dict):
        raise InstrumentArtifactError("`instruments` must be an object")
    for sym in SYMBOLS:
        if sym not in inst:
            raise InstrumentArtifactError(
                "instrument artifact is missing symbol %r" % sym
            )
        for field in REQUIRED_PER_SYMBOL:
            if field not in inst[sym]:
                raise InstrumentArtifactError(
                    "instrument artifact: %s is missing required field %r"
                    % (sym, field)
                )
        for field in ("tick_size", "price"):
            v = inst[sym][field]
            if isinstance(v, bool) or not isinstance(v, (int, float)):
                raise InstrumentArtifactError(
                    "%s %s must be a number, got %r" % (sym, field, v)
                )
            if not math.isfinite(float(v)) or float(v) <= 0.0:
                raise InstrumentArtifactError(
                    "%s %s must be finite and positive, got %r" % (sym, field, v)
                )
        if float(inst[sym]["tick_size"]) >= float(inst[sym]["price"]):
            raise InstrumentArtifactError(
                "%s tick_size is not smaller than price" % sym
            )
    return raw


def cross_check_against_fees(instruments_artifact, fees_path=FEES_PATH):
    """Confirm qty step / min qty agree with the report 17 section 6 artifact.

    Compared against `data/reference/bitget_fees.json`, which is the artifact
    report 17 section 6 was rendered from -- not against the markdown, which is
    a presentation of it. Returns a list of mismatch strings; empty means clean.
    Read-only: this function never writes to the fees artifact.
    """
    if not os.path.exists(fees_path):
        raise InstrumentArtifactError(
            "cannot cross-check: fee artifact absent at %s" % fees_path
        )
    with open(fees_path) as fh:
        fees = json.load(fh)
    specs = fees.get("contract_specs") or {}

    mismatches = []
    for sym in SYMBOLS:
        here = instruments_artifact["instruments"].get(sym, {})
        there = specs.get(sym)
        if there is None:
            mismatches.append("%s: absent from the fee artifact's contract_specs" % sym)
            continue
        for mine, theirs in (("qty_step", "qty_step"),
                             ("min_trade_qty", "min_trade_qty")):
            a, b = here.get(mine), there.get(theirs)
            if a is None or b is None:
                mismatches.append("%s %s: missing on one side (%r vs %r)"
                                  % (sym, mine, a, b))
            elif float(a) != float(b):
                mismatches.append("%s %s: %r here vs %r in the fee artifact"
                                  % (sym, mine, a, b))
    return mismatches


# ---------------------------------------------------------------------------
# The arithmetic. Two lines of it.
# ---------------------------------------------------------------------------

def _check_tick_price(tick_size, price):
    for label, v in (("tick_size", tick_size), ("price", price)):
        if not math.isfinite(v) or v <= 0.0:
            raise ValueError("%s must be finite and positive, got %r" % (label, v))


def one_tick_bps(tick_size, price):
    """One tick expressed in basis points of price: 1e4 * tick / price."""
    _check_tick_price(tick_size, price)
    return 1e4 * tick_size / price


def half_spread_bps(tick_size, price, n_ticks=1):
    """Per-side slippage implied by an `n_ticks`-wide spread, in bps.

        1e4 * n_ticks * tick_size / (2 * price)

    THE FACTOR OF 2 IS THE HALF-SPREAD. A taker crossing an n-tick spread pays
    half of it relative to the mid, not all of it. Dropping the 2 doubles every
    slippage figure -- which makes the verdict look MORE conservative, so a
    sanity check that only watches for implausibly good numbers would wave it
    through. A test plants exactly that mutation.
    """
    _check_tick_price(tick_size, price)
    if not math.isfinite(n_ticks) or n_ticks <= 0:
        raise ValueError("n_ticks must be positive and finite, got %r" % (n_ticks,))
    return 1e4 * n_ticks * tick_size / (2.0 * price)


def ticks_for_slip(slip_bps, tick_size, price):
    """Inverse: how many ticks of spread correspond to `slip_bps` per side.

    This is the number report 18 reads the verdict off -- a tolerance expressed
    in ticks is directly comparable to what a book can plausibly do, whereas a
    tolerance in bps is not.
    """
    _check_tick_price(tick_size, price)
    if not math.isfinite(slip_bps) or slip_bps < 0.0:
        raise ValueError("slip_bps must be non-negative and finite, got %r"
                         % (slip_bps,))
    return slip_bps / half_spread_bps(tick_size, price, 1)


def tick_table(artifact, tick_counts=TICK_COUNTS):
    """{symbol: {n_ticks: per-side slip in bps}} over the published grid."""
    out = {}
    for sym, spec in artifact["instruments"].items():
        tick, price = float(spec["tick_size"]), float(spec["price"])
        out[sym] = {n: half_spread_bps(tick, price, n) for n in tick_counts}
    return out


# ---------------------------------------------------------------------------
# QUANTITY GRANULARITY. Added to close report 17 section 6, which deferred the
# dollar-denominated check to "a later step permitted to read prices" -- and
# which, ranking on the wrong quantity, named the wrong symbol.
# ---------------------------------------------------------------------------

def step_value_usdt(qty_step, price):
    """What ONE quantity step is worth: qty_step * price.

    THIS IS THE QUANTITY THE RANKING MUST BE MADE ON, and getting it wrong is
    the error report 18 section 8 corrects. `qty_step` alone is not comparable
    across symbols -- 0.1 SOL and 0.0001 BTC are not the same kind of thing --
    and neither is the price at which a step reaches some fraction of notional,
    because that threshold says where the line is, not which side of it the
    instrument is standing on. Only step_value_usdt is a dollar amount, and
    only dollar amounts can be ranked. A test plants the qty_step-alone
    comparison, which is the original mistake.
    """
    for label, v in (("qty_step", qty_step), ("price", price)):
        if not math.isfinite(float(v)) or float(v) <= 0.0:
            raise ValueError("%s must be finite and positive, got %r" % (label, v))
    return float(qty_step) * float(price)


def step_fraction_of_notional(qty_step, price, s, risk_dollars):
    """One quantity step as a fraction of position notional.

        notional      = risk_dollars / s
        step_fraction = qty_step * price / notional
                      = qty_step * price * s / risk_dollars

    LINEAR IN `s`, because notional is inverse in it: a wider stop is a smaller
    position, and the same step is a larger slice of it. Granularity is
    therefore worst exactly where the cost envelope is most comfortable.

    `risk_dollars` is REQUIRED, not defaulted. It is `RISK_DOLLARS` in
    `src/costs/envelope.py`; a test pins the two together. Defaulting it here
    would put a second copy of the project's risk size in a second module,
    which is how the two drift apart.
    """
    if not math.isfinite(s) or s <= 0.0:
        raise ValueError("stop fraction s must be positive and finite, got %r" % (s,))
    if not math.isfinite(risk_dollars) or risk_dollars <= 0.0:
        raise ValueError(
            "risk_dollars must be positive and finite, got %r" % (risk_dollars,)
        )
    return step_value_usdt(qty_step, price) * s / risk_dollars


def granularity_ranking(artifact):
    """Symbols ordered by step_value_usdt, coarsest first.

    Returns [(symbol, step_value_usdt), ...]. The ordering is the whole point
    of the function, so it is returned rather than a dict.
    """
    vals = [
        (sym, step_value_usdt(float(spec["qty_step"]), float(spec["price"])))
        for sym, spec in artifact["instruments"].items()
    ]
    return sorted(vals, key=lambda kv: -kv[1])


# ---------------------------------------------------------------------------
# Retrieval entry point.
# ---------------------------------------------------------------------------

def write(payload, path=INSTRUMENTS_PATH):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as fh:
        json.dump(payload, fh, indent=2, sort_keys=True)
        fh.write("\n")
    return path


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--price-field", default="lastPr",
                    choices=("lastPr", "markPrice", "indexPrice"),
                    help="which point-in-time price to record")
    args = ap.parse_args(argv)

    print("Attempting automated retrieval.")
    print("  GET %s" % CONTRACTS_URL)
    print("  GET %s" % TICKERS_URL)
    try:
        payload = retrieve(price_field=args.price_field)
    except RetrievalFailed as exc:
        print("", file=sys.stderr)
        print("ATTEMPTED:", file=sys.stderr)
        print("  GET %s" % CONTRACTS_URL, file=sys.stderr)
        print("  GET %s" % TICKERS_URL, file=sys.stderr)
        print("FAILED:", file=sys.stderr)
        print("  %s" % exc, file=sys.stderr)
        print("", file=sys.stderr)
        print("NOTHING HAS BEEN WRITTEN. No tick size has been substituted from "
              "memory and no price has been estimated. Re-run when the endpoint "
              "is reachable.", file=sys.stderr)
        return 1

    mismatches = cross_check_against_fees(payload)
    if mismatches:
        print("", file=sys.stderr)
        print("CROSS-CHECK FAILED against data/reference/bitget_fees.json "
              "(the artifact report 17 section 6 was rendered from):",
              file=sys.stderr)
        for m in mismatches:
            print("  %s" % m, file=sys.stderr)
        print("", file=sys.stderr)
        print("NOTHING HAS BEEN WRITTEN. The contract specification has changed "
              "since the fee artifact was retrieved, or one of the two is "
              "wrong. Resolve the discrepancy deliberately -- do not overwrite.",
              file=sys.stderr)
        return 2

    path = write(payload)
    print("cross-check against the fee artifact: CLEAN (qty step, min qty)")
    for sym in SYMBOLS:
        s = payload["instruments"][sym]
        print("%-8s tick=%-8s price=%-12s one tick=%.6f bps  half=%.6f bps"
              % (sym, s["tick_size"], s["price"],
                 one_tick_bps(s["tick_size"], s["price"]),
                 half_spread_bps(s["tick_size"], s["price"], 1)))
    print("wrote %s" % path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
