"""Guards for the tick-size slippage floor.

Every expected value is computed independently in the test from the formula in
report 18, not copied from module output. The synthetic cases use round numbers
chosen so the answer can be checked by hand.

Three vacuous guards have been found in this project, so the factor-of-2 guard
at the bottom is written as a planted mutation and was verified by planting it.
"""

import json
import math
import os

import pytest

from src.costs import envelope as ev
from src.costs import tick_probe as tp


@pytest.fixture(scope="module")
def artifact():
    return tp.load_instruments()


def _payload(**symbol_overrides):
    """A minimal well-formed artifact. `tp` as a value means "delete this key"."""
    base = {
        "instruments": {
            sym: {
                "tick_size": 0.1,
                "qty_step": "0.0001",
                "min_trade_qty": "0.0001",
                "price": 100000.0,
                "price_field": "lastPr",
            }
            for sym in tp.SYMBOLS
        },
        "retrieved_at": "2026-01-01T00:00:00+00:00",
        "retrieval_method": "automated",
        "source_urls": {"contracts": "x", "tickers": "y"},
    }
    for sym, over in symbol_overrides.items():
        if sym in base["instruments"]:
            base["instruments"][sym].update(over)
            base["instruments"][sym] = {
                k: v for k, v in base["instruments"][sym].items() if v is not tp
            }
    return base


def _write(tmp_path, payload):
    p = tmp_path / "bitget_instruments.json"
    p.write_text(json.dumps(payload))
    return str(p)


# ---------------------------------------------------------------------------
# 1. Unit conversion, hand-checkable.
# ---------------------------------------------------------------------------

def test_one_tick_bps_known_case():
    """tick 0.1 at price 100,000 is one part in a million = 0.01 bps, exactly."""
    assert tp.one_tick_bps(0.1, 100000.0) == pytest.approx(0.01, rel=1e-15)
    # And the half-spread floor is half of that.
    assert tp.half_spread_bps(0.1, 100000.0, 1) == pytest.approx(0.005, rel=1e-15)


def test_one_tick_bps_second_known_case():
    """tick 0.001 at price 100 is one part in 100,000 = 0.1 bps."""
    assert tp.one_tick_bps(0.001, 100.0) == pytest.approx(0.1, rel=1e-12)
    assert tp.half_spread_bps(0.001, 100.0, 1) == pytest.approx(0.05, rel=1e-12)


def test_ticks_for_slip_is_the_exact_inverse():
    for tick, price in ((0.1, 100000.0), (0.01, 2000.0), (0.001, 77.0)):
        for n in (1, 2, 3, 5, 10, 137):
            bps = tp.half_spread_bps(tick, price, n)
            assert tp.ticks_for_slip(bps, tick, price) == pytest.approx(n, rel=1e-12)


# ---------------------------------------------------------------------------
# 2. Linear in n_ticks, inverse in price.
# ---------------------------------------------------------------------------

def test_linear_in_n_ticks():
    tick, price = 0.01, 2000.0
    one = tp.half_spread_bps(tick, price, 1)
    for n in (1, 2, 3, 5, 10, 50):
        assert tp.half_spread_bps(tick, price, n) == pytest.approx(n * one, rel=1e-12)
    # Additivity, which linearity implies and a quadratic term would break.
    assert (tp.half_spread_bps(tick, price, 3) ==
            pytest.approx(tp.half_spread_bps(tick, price, 1)
                          + tp.half_spread_bps(tick, price, 2), rel=1e-12))


def test_inverse_in_price():
    tick = 0.01
    base = tp.half_spread_bps(tick, 1000.0, 1)
    assert tp.half_spread_bps(tick, 2000.0, 1) == pytest.approx(base / 2.0, rel=1e-12)
    assert tp.half_spread_bps(tick, 500.0, 1) == pytest.approx(base * 2.0, rel=1e-12)
    # Doubling tick and doubling price leaves bps unchanged -- it is a ratio.
    assert tp.half_spread_bps(0.02, 2000.0, 1) == pytest.approx(base, rel=1e-12)


def test_linear_in_tick_size():
    price = 1000.0
    base = tp.half_spread_bps(0.01, price, 1)
    assert tp.half_spread_bps(0.03, price, 1) == pytest.approx(3.0 * base, rel=1e-12)


def test_rejects_bad_inputs():
    for bad in (0.0, -1.0, float("nan"), float("inf")):
        with pytest.raises(ValueError):
            tp.one_tick_bps(bad, 100.0)
        with pytest.raises(ValueError):
            tp.one_tick_bps(0.1, bad)
    for bad_n in (0, -1, float("nan")):
        with pytest.raises(ValueError):
            tp.half_spread_bps(0.1, 100.0, bad_n)
    with pytest.raises(ValueError):
        tp.ticks_for_slip(-1.0, 0.1, 100.0)


def test_tick_size_derivation_uses_both_fields():
    """priceEndStep is not always 1; ignoring it understates the tick."""
    assert tp._tick_size({"symbol": "X", "pricePlace": "1", "priceEndStep": "1"}) == (
        pytest.approx(0.1, rel=1e-12))
    assert tp._tick_size({"symbol": "X", "pricePlace": "1", "priceEndStep": "5"}) == (
        pytest.approx(0.5, rel=1e-12))
    assert tp._tick_size({"symbol": "X", "pricePlace": "3", "priceEndStep": "1"}) == (
        pytest.approx(0.001, rel=1e-12))
    for bad in ({"symbol": "X", "pricePlace": "1"},
                {"symbol": "X", "pricePlace": "a", "priceEndStep": "1"},
                {"symbol": "X", "pricePlace": "1", "priceEndStep": "0"}):
        with pytest.raises(tp.RetrievalFailed):
            tp._tick_size(bad)


# ---------------------------------------------------------------------------
# 3. Artifact contract.
# ---------------------------------------------------------------------------

def test_missing_artifact_raises(tmp_path):
    with pytest.raises(tp.InstrumentArtifactError, match="not found"):
        tp.load_instruments(str(tmp_path / "nope.json"))


def test_unparseable_artifact_raises(tmp_path):
    p = tmp_path / "bitget_instruments.json"
    p.write_text("{not json")
    with pytest.raises(tp.InstrumentArtifactError, match="not valid JSON"):
        tp.load_instruments(str(p))


@pytest.mark.parametrize("field", ["instruments", "retrieved_at",
                                   "retrieval_method", "source_urls"])
def test_missing_top_level_field_raises(tmp_path, field):
    payload = _payload()
    del payload[field]
    with pytest.raises(tp.InstrumentArtifactError, match="missing required field"):
        tp.load_instruments(_write(tmp_path, payload))


@pytest.mark.parametrize("symbol", list(tp.SYMBOLS))
def test_missing_symbol_raises(tmp_path, symbol):
    payload = _payload()
    del payload["instruments"][symbol]
    with pytest.raises(tp.InstrumentArtifactError, match="missing symbol"):
        tp.load_instruments(_write(tmp_path, payload))


@pytest.mark.parametrize("field", list(tp.REQUIRED_PER_SYMBOL))
def test_missing_per_symbol_field_raises(tmp_path, field):
    payload = _payload(SOLUSDT={field: tp})
    with pytest.raises(tp.InstrumentArtifactError, match="missing required field"):
        tp.load_instruments(_write(tmp_path, payload))


@pytest.mark.parametrize("bad", [0.0, -0.1, float("nan"), float("inf"),
                                 "0.1", None, True])
@pytest.mark.parametrize("field", ["tick_size", "price"])
def test_non_finite_positive_tick_or_price_raises(tmp_path, field, bad):
    payload = _payload(ETHUSDT={field: bad})
    with pytest.raises(tp.InstrumentArtifactError):
        tp.load_instruments(_write(tmp_path, payload))


def test_tick_not_smaller_than_price_raises(tmp_path):
    payload = _payload(BTCUSDT={"tick_size": 500.0, "price": 100.0})
    with pytest.raises(tp.InstrumentArtifactError, match="not smaller than price"):
        tp.load_instruments(_write(tmp_path, payload))


def test_committed_artifact_meets_the_contract(artifact):
    assert artifact["retrieval_method"] == "automated"
    assert artifact["retrieved_at"]
    for sym in tp.SYMBOLS:
        spec = artifact["instruments"][sym]
        assert 0.0 < float(spec["tick_size"]) < float(spec["price"])
        # A tick worth more than 10 bps of price would make the whole
        # half-spread argument shaky; none of these three is close.
        assert tp.one_tick_bps(spec["tick_size"], spec["price"]) < 10.0


# ---------------------------------------------------------------------------
# 4. Cross-check against report 17 section 6.
# ---------------------------------------------------------------------------

def test_qty_specs_match_the_report_17_artifact(artifact):
    """Report 17 section 6 was rendered from data/reference/bitget_fees.json.

    Compared against that artifact rather than the markdown, because the
    markdown is a presentation of it. A mismatch means the contract spec moved
    between the two retrievals and the two reports disagree about the
    instrument -- which must fail loudly, not be reconciled silently.
    """
    mismatches = tp.cross_check_against_fees(artifact)
    assert mismatches == [], "report 17 cross-check failed: %s" % "; ".join(mismatches)


def test_cross_check_detects_a_planted_disagreement(artifact, tmp_path):
    """The cross-check must be able to REFUSE, or it proves nothing."""
    tampered = json.loads(json.dumps(artifact))
    tampered["instruments"]["SOLUSDT"]["qty_step"] = "0.5"
    mism = tp.cross_check_against_fees(tampered)
    assert any("SOLUSDT" in m and "qty_step" in m for m in mism), mism

    tampered2 = json.loads(json.dumps(artifact))
    tampered2["instruments"]["BTCUSDT"]["min_trade_qty"] = "0.002"
    assert any("BTCUSDT" in m and "min_trade_qty" in m
               for m in tp.cross_check_against_fees(tampered2))


def test_cross_check_raises_when_the_fee_artifact_is_absent(artifact, tmp_path):
    with pytest.raises(tp.InstrumentArtifactError, match="fee artifact absent"):
        tp.cross_check_against_fees(artifact, fees_path=str(tmp_path / "nope.json"))


# ---------------------------------------------------------------------------
# The comparison is downstream of the envelope, never a restated constant.
# ---------------------------------------------------------------------------

def test_breakeven_is_imported_not_restated():
    """No figure from report 17 may be hard-coded in this module."""
    src = open(tp.__file__).read()
    for forbidden in ("0.11", "COST_TOLERANCE", "INADM", "UNCON",
                      "1.0909", "0.3636", "2.25", "10.50"):
        assert forbidden not in src, (
            "%r appears in tick_probe.py; break-even figures must be imported "
            "from src/costs/envelope.py" % forbidden
        )


def test_headroom_is_computed_from_the_envelope(artifact):
    """End-to-end: the verdict quantity is envelope output divided by a tick."""
    fees = ev.load_fees()
    be = ev.max_tolerable_slip(0.015, 0.0, ev.COST_TOLERANCE_R, fees)
    assert be is not None and be > 0.0
    spec = artifact["instruments"]["SOLUSDT"]
    n = tp.ticks_for_slip(be * 1e4, spec["tick_size"], spec["price"])
    # Re-derived independently from the definitions, not from module internals.
    expected = (be * 1e4) / (1e4 * spec["tick_size"] / (2.0 * spec["price"]))
    assert n == pytest.approx(expected, rel=1e-12)
    assert n > 1.0


def test_tick_table_shape(artifact):
    t = tp.tick_table(artifact)
    assert set(t) == set(tp.SYMBOLS)
    for sym, row in t.items():
        assert set(row) == set(tp.TICK_COUNTS)
        vals = [row[n] for n in sorted(tp.TICK_COUNTS)]
        assert vals == sorted(vals)


def test_sol_is_the_widest_in_relative_terms(artifact):
    """Tick size in dollars is not comparable across symbols; tick/price is.

    SOL has the SMALLEST tick in absolute dollars (0.001 against BTC's 0.1) and
    the LARGEST tick relative to price. A comparison made on the dollar tick
    would rank the three exactly backwards, so the ordering is asserted.
    """
    floors = {s: tp.half_spread_bps(artifact["instruments"][s]["tick_size"],
                                    artifact["instruments"][s]["price"], 1)
              for s in tp.SYMBOLS}
    assert floors["SOLUSDT"] > floors["ETHUSDT"] > floors["BTCUSDT"]
    ticks = {s: artifact["instruments"][s]["tick_size"] for s in tp.SYMBOLS}
    assert ticks["SOLUSDT"] < ticks["ETHUSDT"] < ticks["BTCUSDT"]


# ---------------------------------------------------------------------------
# 5. PLANTED MUTATION -- the half-spread factor of 2.
# ---------------------------------------------------------------------------

def test_taker_pays_half_the_spread_not_all_of_it():
    """PLANTED MUTATION GUARD: the factor of 2 dropped from `half_spread_bps`.

    THE MUTATION. In `half_spread_bps`, change

        1e4 * n_ticks * tick_size / (2.0 * price)
     -> 1e4 * n_ticks * tick_size / price

    i.e. charge the FULL spread as per-side slippage instead of half of it. A
    taker crossing an n-tick spread pays half of it relative to the mid; the
    other half is what the resting side gave up.

    WHY A SANITY CHECK WOULD NOT CATCH IT. This mutation DOUBLES every slippage
    figure and HALVES every headroom multiple, which makes the report's verdict
    strictly more conservative. A reviewer scanning for numbers that look too
    good would wave it straight through, and the resulting report would still
    read as careful. Guards have to be aimed at the direction nobody is
    watching.

    THE ARITHMETIC. tick 0.1 at price 100,000: one tick is 0.01 bps of price,
    so a one-tick spread costs a taker 0.005 bps per side.

        correct : 1e4 * 1 * 0.1 / (2 * 100000) = 0.005
        mutated : 1e4 * 1 * 0.1 /      100000  = 0.010

    Confirmed to fail under the mutation before being committed.
    """
    assert tp.half_spread_bps(0.1, 100000.0, 1) == pytest.approx(0.005, rel=1e-15)
    assert tp.half_spread_bps(0.1, 100000.0, 1) != pytest.approx(0.010, rel=1e-9)

    # The relation stated directly: per-side is exactly half of one tick in bps.
    for tick, price in ((0.1, 65000.0), (0.01, 1900.0), (0.001, 77.0)):
        assert tp.half_spread_bps(tick, price, 1) == pytest.approx(
            tp.one_tick_bps(tick, price) / 2.0, rel=1e-12)
        assert tp.half_spread_bps(tick, price, 1) != pytest.approx(
            tp.one_tick_bps(tick, price), rel=1e-9)

    # And the inverse carries the same factor, so a mutation must break both or
    # the round trip would silently paper over it.
    assert tp.ticks_for_slip(0.005, 0.1, 100000.0) == pytest.approx(1.0, rel=1e-12)
    assert tp.ticks_for_slip(0.010, 0.1, 100000.0) == pytest.approx(2.0, rel=1e-12)
