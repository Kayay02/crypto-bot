"""Retrieve Bitget's published USDT-M perpetual fee schedule and stamp it.

WHY AN ARTIFACT AND NOT A CONSTANT. A fee rate typed into a module is a rate
nobody can date. The admissibility line derived in report 17 is only meaningful
against a schedule whose retrieval time and source are provable, so the rates
live in a committed, provenance-stamped JSON file and `envelope.py` refuses to
run without it.

RETRIEVAL ORDER, AND THE REFUSAL. This script tries the official Bitget v2
public API first. If that fails for any reason -- network, non-200, schema
change, rate limit, disagreement between contracts -- it does NOT guess and does
NOT fall back to a remembered number. It prints what it attempted, what failed,
and a block for the operator to paste the rates in by hand, then exits non-zero.
A wrong fee rate silently substituted for a retrieved one would corrupt every
downstream admissibility figure while looking exactly like a correct run.

WHICH ENDPOINT, AND WHY THAT ONE. https://www.bitget.com/fee is the human fee
schedule and is JS-rendered -- it returns a shell with no table in it, so it
cannot be parsed. The v2 `mix/market/contracts` endpoint is the machine-readable
form of the same base-tier schedule: it carries `makerFeeRate` / `takerFeeRate`
per contract, and it also carries the lot-granularity fields (`minTradeNum`,
`sizeMultiplier`, `minTradeUSDT`) that the report's minimum-notional check
needs, from the same response and the same timestamp.

WHAT THIS SCRIPT CANNOT ESTABLISH. The endpoint publishes the schedule's BASE
tier. It cannot see an account, so it cannot confirm the operator's actual VIP
tier, whether a BGB deduction is switched on, or whether a maker rebate applies.
Those need credentials and are left to the operator checklist in report 17.
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
ARTIFACT_PATH = os.path.join(REFERENCE_DIR, "bitget_fees.json")

API_URL = (
    "https://api.bitget.com/api/v2/mix/market/contracts?productType=USDT-FUTURES"
)
HUMAN_SCHEDULE_URL = "https://www.bitget.com/fee"

# The three symbols the project trades. Their contract specs are recorded
# alongside the rates so the minimum-notional check reads from the same
# retrieval as the fees rather than from a second, differently-dated one.
SYMBOLS = ("BTCUSDT", "ETHUSDT", "SOLUSDT")

PRODUCT = "USDT-M perpetual futures"
TIER = "base tier (regular user, VIP 0 -- no volume, balance or BGB tier applied)"

TIMEOUT_S = 30


class RetrievalFailed(Exception):
    """Raised when the schedule could not be retrieved or did not validate.

    Carries the human-readable description of the attempt so the caller can
    print it verbatim rather than paraphrasing it.
    """


def _fetch(url, timeout=TIMEOUT_S):
    # `requests` rather than urllib to match src/data/backfill_bitget.py, and
    # because urllib on this machine's Python has no usable CA bundle while
    # requests carries certifi's.
    resp = requests.get(
        url, timeout=timeout, headers={"User-Agent": "crypto-bot/fee-artifact"}
    )
    if resp.status_code != 200:
        raise RetrievalFailed("HTTP %s from %s" % (resp.status_code, url))
    return resp.json()


def _as_rate(raw, label):
    """Parse a rate string into a finite positive decimal fraction."""
    try:
        v = float(raw)
    except (TypeError, ValueError):
        raise RetrievalFailed("%s is not numeric: %r" % (label, raw))
    if not math.isfinite(v) or v <= 0.0:
        raise RetrievalFailed("%s is not a finite positive rate: %r" % (label, raw))
    if v >= 0.01:
        # 1% per side on a perp would be two orders of magnitude off the
        # published schedule and is far more likely a units change (percent
        # rather than fraction) than a real rate. Refuse rather than absorb it.
        raise RetrievalFailed(
            "%s = %r is implausibly large for a perp fee expressed as a "
            "decimal fraction; the endpoint's units may have changed" % (label, v)
        )
    return v


def retrieve():
    """Return (payload_dict, retrieved_at_iso). Raises RetrievalFailed."""
    retrieved_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()

    try:
        body = _fetch(API_URL)
    except requests.RequestException as exc:
        raise RetrievalFailed("network error contacting %s: %s" % (API_URL, exc))
    except json.JSONDecodeError as exc:
        raise RetrievalFailed("%s did not return JSON: %s" % (API_URL, exc))

    if body.get("code") != "00000":
        raise RetrievalFailed(
            "Bitget returned code=%r msg=%r" % (body.get("code"), body.get("msg"))
        )
    rows = body.get("data")
    if not isinstance(rows, list) or not rows:
        raise RetrievalFailed("Bitget returned no contract rows")

    by_symbol = {r.get("symbol"): r for r in rows if isinstance(r, dict)}
    missing = [s for s in SYMBOLS if s not in by_symbol]
    if missing:
        raise RetrievalFailed("contracts response is missing %s" % ", ".join(missing))

    # The base-tier schedule is one pair of rates for the whole product. If the
    # endpoint ever publishes per-contract rates, a single (maker, taker) pair
    # stops being a faithful summary and the artifact's shape is wrong -- so
    # disagreement is a refusal, not a majority vote.
    pairs = {(r.get("makerFeeRate"), r.get("takerFeeRate")) for r in rows}
    if len(pairs) != 1:
        raise RetrievalFailed(
            "USDT-M contracts do not share one (maker, taker) pair: found %d "
            "distinct pairs, e.g. %s" % (len(pairs), sorted(pairs)[:4])
        )

    ref = by_symbol[SYMBOLS[0]]
    maker = _as_rate(ref.get("makerFeeRate"), "makerFeeRate")
    taker = _as_rate(ref.get("takerFeeRate"), "takerFeeRate")
    if maker > taker:
        raise RetrievalFailed(
            "maker_rate %r exceeds taker_rate %r; the envelope's monotonicity "
            "in maker_frac assumes maker <= taker" % (maker, taker)
        )

    specs = {}
    for sym in SYMBOLS:
        r = by_symbol[sym]
        specs[sym] = {
            "min_trade_qty": r.get("minTradeNum"),
            "qty_step": r.get("sizeMultiplier"),
            "qty_decimals": r.get("volumePlace"),
            "price_decimals": r.get("pricePlace"),
            "min_notional_usdt": r.get("minTradeUSDT"),
            "max_leverage": r.get("maxLever"),
        }

    payload = {
        "maker_rate": maker,
        "taker_rate": taker,
        "tier": TIER,
        "product": PRODUCT,
        "source_url": API_URL,
        "retrieved_at": retrieved_at,
        "retrieval_method": "automated",
        "notes": NOTES,
        "corroborating_sources": CORROBORATING_SOURCES,
        "contracts_seen": len(rows),
        "contract_specs": specs,
        "spec_units": {
            "min_trade_qty": "base-coin units (BTC / ETH / SOL)",
            "qty_step": "base-coin units; order quantity must be a multiple",
            "min_notional_usdt": "USDT",
            "max_leverage": "x, exchange maximum for the symbol",
        },
        "unverifiable_without_credentials": [
            "the account's actual VIP / fee tier",
            "whether a BGB fee deduction is switched on for the account",
            "whether any maker rebate or market-maker programme applies",
        ],
    }
    return payload, retrieved_at


NOTES = (
    "Rates are BASE TIER (regular user, no VIP level, no discount applied) and "
    "are decimal fractions: 0.0002 = 0.02% maker, 0.0006 = 0.06% taker per "
    "side. All 741 USDT-M perpetual contracts returned by the endpoint carry "
    "this same pair, so the rate is a product-level schedule, not a "
    "per-symbol one. CONDITIONALS FOUND: (1) VIP TIERS -- Bitget publishes a "
    "VIP ladder whose futures maker fee falls toward 0% and taker toward "
    "0.02-0.03% at the top levels; it does NOT apply at base tier and the "
    "exact per-level thresholds could not be read, because the VIP page "
    "(bitget.com/vip/vipIntroduce) and the human fee schedule "
    "(bitget.com/fee) are both JS-rendered and return no table to a fetch. "
    "(2) BGB DISCOUNT -- Bitget's academy and support pages state the 20% "
    "fee reduction for paying fees in BGB applies to SPOT and MARGIN trading; "
    "the futures fee pages do not offer it. Third-party summaries disagree on "
    "this point, so it is recorded as NOT applying to USDT-M futures at base "
    "tier and flagged for operator confirmation against the account UI. "
    "(3) MAKER REBATE -- no negative maker fee or rebate programme is offered "
    "at base tier; rebate-grade maker pricing appears only at high VIP / "
    "market-maker levels. (4) PROMOTIONAL RATES -- none found applying to "
    "USDT-M perpetuals at base tier. Fee-rate promotions Bitget was "
    "publishing at retrieval time concerned stock / metal / commodity / index "
    "futures, which this project does not trade. NOT COVERED BY THESE RATES: "
    "funding payments, which are a separate transfer between longs and shorts "
    "on an 8-hour interval (fundInterval=8) and are not a fee."
)

CORROBORATING_SOURCES = [
    {
        "url": "https://www.bitget.com/support/articles/12560603817155",
        "states": "0.02% maker / 0.06% taker for USDT-M futures, 'actual fee "
                  "varies by account level'",
    },
    {
        "url": "https://www.bitget.com/academy/Fee-Structure-and-Fee-Calculations-on-Bitget",
        "states": "0.02% maker / 0.06% taker; BGB 20% deduction described as "
                  "spot-only",
    },
    {
        "url": HUMAN_SCHEDULE_URL,
        "states": "canonical human fee schedule; JS-rendered, returned no fee "
                  "table to an automated fetch and was NOT used as the source "
                  "of the recorded rates",
    },
]


OPERATOR_BLOCK = """
================================================================================
  RETRIEVAL FAILED -- MANUAL OPERATOR ENTRY REQUIRED
================================================================================
  No rate has been written. Nothing has been guessed and no remembered value
  has been substituted.

  Open Bitget's published USDT-M perpetual futures fee schedule:

      %s

  Read the BASE TIER (regular user / VIP 0) row and paste the two rates back,
  as decimal fractions, in this form:

      maker_rate = 0.0002
      taker_rate = 0.0006

  Then re-run with:

      python src/costs/build_fee_artifact.py --maker <rate> --taker <rate>

  which records retrieval_method = "manual_operator_entry".
================================================================================
""" % HUMAN_SCHEDULE_URL


def manual_payload(maker, taker):
    """Build the artifact from operator-supplied rates.

    The contract-spec block is absent on this path: the operator was asked for
    two fee rates, not for lot sizes, and inventing the rest of the response
    would be exactly the guess this script refuses to make elsewhere.
    """
    maker = _as_rate(maker, "operator maker_rate")
    taker = _as_rate(taker, "operator taker_rate")
    if maker > taker:
        raise RetrievalFailed(
            "maker_rate %r exceeds taker_rate %r" % (maker, taker)
        )
    return {
        "maker_rate": maker,
        "taker_rate": taker,
        "tier": TIER,
        "product": PRODUCT,
        "source_url": HUMAN_SCHEDULE_URL,
        "retrieved_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "retrieval_method": "manual_operator_entry",
        "notes": (
            "ENTERED BY HAND. The automated retrieval path failed and the "
            "operator read these rates off Bitget's published schedule. No "
            "contract specs were captured on this path. " + NOTES
        ),
        "corroborating_sources": [],
        "contract_specs": {},
    }


def write(payload, path=ARTIFACT_PATH):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as fh:
        json.dump(payload, fh, indent=2, sort_keys=True)
        fh.write("\n")
    return path


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--maker", type=str, default=None,
                    help="operator-supplied maker rate, decimal fraction")
    ap.add_argument("--taker", type=str, default=None,
                    help="operator-supplied taker rate, decimal fraction")
    args = ap.parse_args(argv)

    if (args.maker is None) != (args.taker is None):
        print("--maker and --taker must be given together.", file=sys.stderr)
        return 2

    if args.maker is not None:
        payload = manual_payload(args.maker, args.taker)
    else:
        print("Attempting automated retrieval.")
        print("  GET %s" % API_URL)
        try:
            payload, _ = retrieve()
        except RetrievalFailed as exc:
            print("", file=sys.stderr)
            print("ATTEMPTED:", file=sys.stderr)
            print("  GET %s" % API_URL, file=sys.stderr)
            print("  (the human schedule at %s is JS-rendered and is not a "
                  "parseable fallback)" % HUMAN_SCHEDULE_URL, file=sys.stderr)
            print("FAILED:", file=sys.stderr)
            print("  %s" % exc, file=sys.stderr)
            print(OPERATOR_BLOCK, file=sys.stderr)
            return 1

    path = write(payload)
    print("maker_rate = %.6f  (%.4f%%)" % (payload["maker_rate"],
                                           payload["maker_rate"] * 100.0))
    print("taker_rate = %.6f  (%.4f%%)" % (payload["taker_rate"],
                                           payload["taker_rate"] * 100.0))
    print("tier       = %s" % payload["tier"])
    print("method     = %s" % payload["retrieval_method"])
    print("wrote %s" % path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
