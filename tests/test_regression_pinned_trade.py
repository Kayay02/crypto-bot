"""Pin the hand-verified trade so no future pass may disturb its arithmetic.

BTCUSDT short, signal_bar_ts=1673881200000, verified by hand in the previous
pass to reconcile to -1.0001R. The cost arithmetic, sizing, target solve and
slippage placement are locked; this test fails if any of them move.
"""

import pytest
import run as engine_run

SIG_TS = 1673881200000
SLICE = dict(symbols=["BTCUSDT"], start_ts=1672531200000, end_ts=1675209600000)

# Values verified by hand, not copied from a later run.
EXPECTED = {
    "direction": "short",
    "entry_ts": 1673882100000,
    "entry_price": 20741.5,
    "stop_price": 20949.0,
    "qty": 0.08230832,
    "exit_price": 20959.5,
    "exit_reason": "stop",
    "resolution": "observed",
    "stop_fill_quality": "normal",
    "r_multiple": -1.0001,
}


@pytest.fixture(scope="module")
def pinned():
    trades, _, _ = engine_run.run(variant="gated", **SLICE)
    row = trades[trades["signal_bar_ts"] == SIG_TS]
    assert len(row) == 1, f"pinned trade missing from the universe: {len(row)}"
    return row.iloc[0]


def test_pinned_trade_entry_and_levels(pinned):
    assert pinned["direction"] == EXPECTED["direction"]
    assert pinned["entry_ts"] == EXPECTED["entry_ts"]
    assert pinned["entry_price"] == pytest.approx(EXPECTED["entry_price"])
    assert pinned["stop_price"] == pytest.approx(EXPECTED["stop_price"])


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
    assert pinned["net_pnl"] == pytest.approx(-20.002617, abs=1e-5)
