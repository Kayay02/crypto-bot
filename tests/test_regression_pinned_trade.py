"""Pin the hand-verified trade so no future pass may disturb its arithmetic.

BTCUSDT short, signal_bar_ts=1673881200000. The cost arithmetic, sizing, target
solve and slippage placement are locked; this test fails if any of them move.

RE-PINNED AT POINT 3R, and the reason is recorded because a moved pin is
otherwise indistinguishable from a broken one. The stop on this trade is
FLOOR-BOUND, and the floor changed from a hardcoded 1.000% to the derived
1.020% for BTCUSDT. Nothing else about the trade moved: same signal bar, same
direction, same entry, same exit reason. Every value below is re-derived by
hand from the formula, not copied from a run:

    floor   = N_cost * c_roundtrip = 6 * (2*0.0006 + 0 + 5/10_000) = 0.010200
    stop    = ceil(20741.5 * 1.0102 / 0.1) * 0.1
            = ceil(20953.0633 / 0.1) * 0.1            = 20953.1
    s_stop  = 20953.1 * 5/10_000                      = 10.47655
    move    = 20953.1 - 20741.5                       = 211.6
    denom   = 211.6 + 20741.5*0.0006 + 20953.1*0.0006 + 10.47655
                                                      = 247.093310
    qty     = 20 / 247.093310                         = 0.08094108
    fill    = ceil((20953.1 + 10.47655) / 0.1) * 0.1  = 20963.6
    net     = qty*(20741.5 - 20963.6) - fees          = -20.002408
    R       = -20.002408 / 20                         = -1.0001204

The old pin (stop 20949.0, qty 0.08230832, fill 20959.5, net -20.002617) is the
same arithmetic against the old 1.000% floor.

    THIS MODULE ASSERTS OUTCOME-NAMED VALUES AND IS PERMITTED TO DO SO ONLY BY A
    RECORDED CARVE-OUT.

THE CARVE-OUT IS `docs/design/04_2a_artifact_containment.md` SECTION 4.2, and its
four conditions are transcribed here and in `tests/golden/CONTAINMENT.md` because
section 4.4 requires them recorded where a developer touching these fixtures will
see them. They are asserted by `tests/test_containment_guard.py`.

    THE TWO GOLDEN FILES AND THE PINNED-TRADE REGRESSION MAY READ OUTCOME-NAMED
    VALUES, PERMITTED ONLY UNDER FOUR CONDITIONS.

    (a) DETERMINISM AND SINGLE-POSITION IDENTITY ONLY. They may assert that
        identical inputs produce identical outputs, and that one hand-derived
        arithmetic identity holds on one named position. They may not compare
        populations, compare two configurations, or aggregate over rows.
    (b) EVERY EXPECTED VALUE IS HAND-DERIVED AND ITS DERIVATION IS WRITTEN DOWN.
        The derivation above is what discharges this. A value copied from a run
        is not permitted, because a fixture that records what the system did is a
        measurement wearing a fixture's name.
    (c) EXACTLY THESE ARTIFACTS AND EXACTLY THESE READERS. The two files under
        `tests/golden/`, and this module and `tests/test_determinism_golden.py`.
        No further fixture and no further reader joins without amending that
        document.
    (d) THE BLANKET NAME BAN OTHERWISE INTACT. The twelve-name guard is not
        relaxed for these files, for these tests, or for anything else.

WHAT VOIDS IT, section 4.3: using a fixture to compare two configurations;
ADDING A SECOND PINNED TRADE, because a count over two is a population of two and
condition (a) then fails by arithmetic rather than by intent; regenerating a
golden file and taking expected values from the run rather than re-deriving them;
and any assertion over an aggregate of the rows -- a sum, a mean, a count
conditioned on an outcome column.

    THE FIRST AND THE LAST ARE THE ONES THAT WOULD LOOK INNOCENT AT THE TIME,
    AND THEY ARE NAMED FOR THAT REASON.

HOW THIS MODULE STAYS INSIDE (a). ONE signal bar is selected by timestamp, the
fixture asserts there is exactly one such row, and every assertion below is on
that single row. There is no second pin and no population.
"""

import pytest
import run as engine_run
from conftest import golden_cfg

SIG_TS = 1673881200000
SLICE = dict(symbols=["BTCUSDT"], start_ts=1672531200000, end_ts=1675209600000)

# Values verified by hand, not copied from a later run.
EXPECTED = {
    "direction": "short",
    "entry_ts": 1673882100000,
    "entry_price": 20741.5,
    "stop_price": 20953.1,
    "qty": 0.08094108,
    "exit_price": 20963.6,
    "exit_reason": "stop",
    "resolution": "observed",
    "stop_fill_quality": "normal",
    "r_multiple": -1.0001204,
    "stop_binding_mechanism": "floor",
}


@pytest.fixture(scope="module")
def pinned():
    trades, _, _ = engine_run.run(variant="gated", cfg=golden_cfg(), **SLICE)
    row = trades[trades["signal_bar_ts"] == SIG_TS]
    assert len(row) == 1, f"pinned trade missing from the universe: {len(row)}"
    return row.iloc[0]


def test_pinned_trade_entry_and_levels(pinned):
    assert pinned["direction"] == EXPECTED["direction"]
    assert pinned["entry_ts"] == EXPECTED["entry_ts"]
    assert pinned["entry_price"] == pytest.approx(EXPECTED["entry_price"])
    assert pinned["stop_price"] == pytest.approx(EXPECTED["stop_price"])
    assert pinned["stop_binding_mechanism"] == EXPECTED["stop_binding_mechanism"]


def test_pinned_trade_stop_is_the_DERIVED_floor_not_a_hardcoded_one():
    """The stop must come from the formula, not from a literal 1.0%."""
    from conftest import golden_cfg
    cfg = golden_cfg()
    assert cfg.stop_min_pct("BTCUSDT") == pytest.approx(0.01020)
    assert cfg.stop_min_pct("BTCUSDT") != 0.010, "old hardcoded floor is void"


def test_pinned_trade_sizing_is_unchanged(pinned):
    assert pinned["qty"] == pytest.approx(EXPECTED["qty"], abs=1e-8)


def test_pinned_trade_exit_is_unchanged(pinned):
    assert pinned["exit_price"] == pytest.approx(EXPECTED["exit_price"])
    assert pinned["exit_reason"] == EXPECTED["exit_reason"]
    assert pinned["resolution"] == EXPECTED["resolution"]
    assert pinned["stop_fill_quality"] == EXPECTED["stop_fill_quality"]


def test_pinned_trade_still_reconciles_to_minus_one_R(pinned):
    """The headline number: -1.0001R, to four decimal places."""
    assert pinned["r_multiple"] == pytest.approx(EXPECTED["r_multiple"], abs=5e-5)


def test_pinned_trade_pnl_reconciles_by_hand(pinned):
    """Recompute from the row's own fields; do not trust the stored total."""
    q, entry, exit_px = pinned["qty"], pinned["entry_price"], pinned["exit_price"]
    gross = q * (entry - exit_px)                     # short
    fees = q * entry * 0.0006 + q * exit_px * 0.0006  # taker both legs
    assert pinned["gross_pnl"] == pytest.approx(gross)
    assert pinned["fees_paid"] == pytest.approx(fees)
    assert pinned["net_pnl"] == pytest.approx(gross - fees)
    assert pinned["net_pnl"] == pytest.approx(-20.002408, abs=1e-5)
