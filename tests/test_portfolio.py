"""G1 fixtures 7 and 8 -- portfolio constraints: cooldown and funding."""

import costs
import numpy as np
import pandas as pd
import pytest
import simulate
from conftest import make_1m

BAR = simulate.BAR_15M_MS
T0 = 1_600_000_000_000
TICK = 0.01


def bars15(n, start=T0, high=101.0, low=99.0, close=100.0):
    return pd.DataFrame({
        "ts": [start + i * BAR for i in range(n)],
        "high": [high] * n, "low": [low] * n,
        "close": [close] * n, "volume": [1.0] * n,
        "quote_volume": [100.0] * n,
    })


def sig_frame(rows):
    return pd.DataFrame(rows)


def sig(sym, direction, ts, atr=2.0):
    return {"symbol": sym, "direction": direction, "signal_bar_ts": ts,
            "atr": atr, "close": 100.0, "ema_fast": 101.0, "ema_slow": 99.0,
            "donchian_upper": 99.5, "donchian_lower": 95.0, "rvol": 2.0,
            "rsi": 60.0, "variant": "gated"}


def path_1m(start_ts, minutes):
    return make_1m(start_ts, minutes)


class ConstTick:
    def __init__(self, v):
        self.v = v

    def tick_at(self, ts):
        return self.v


def flat(n, price=100.0):
    return [(price + 0.1, price - 0.1, price)] * n


ENTRY_BAR = (100.10, 99.90, 100.0)
STOP_MIN = (99.9, 96.0, 96.5)      # breaches the 97.00 stop


# --------------------------------------------------------------------------
# Fixture 7 -- cooldown
# --------------------------------------------------------------------------

def minutes_with_stop_after(entry_ts_list, total=3000):
    """A flat 1m series with a stop breach in the minute AFTER each given entry.

    The breach must land at the right absolute offset -- putting it at the head
    of the array simply means the trade never sees it.
    """
    mins = flat(total)
    for ets in entry_ts_list:
        i = (ets - T0) // 60_000
        mins[i] = ENTRY_BAR
        mins[i + 1] = STOP_MIN
    return make_1m(T0, mins)


def _cooldown_setup(new_extreme_between):
    """Two long signals on one symbol; the first stops out.

    The second is 25 bars later. If `new_extreme_between`, one intervening 15m
    bar sets a new 20-bar high, which must clear the cooldown.
    """
    cfg = costs.CostConfig()
    n = 60
    df15 = bars15(n)
    if new_extreme_between:
        # A bar between the two signals that makes a new 20-bar high.
        df15.loc[25, "high"] = 500.0

    e1 = T0 + BAR * 6
    e2 = T0 + BAR * 31
    all_min = minutes_with_stop_after([e1, e2])

    signals = sig_frame([
        sig("ETHUSDT", "long", T0 + BAR * 5),
        sig("ETHUSDT", "long", T0 + BAR * 30),
    ])
    trades, refused, _ = simulate.run_backtest(
        signals, {"ETHUSDT": df15}, {"ETHUSDT": all_min}, cfg,
        {"ETHUSDT": ConstTick(TICK)})
    return trades, refused


def test_fixture_7_cooldown_blocks_reentry_until_new_extreme():
    trades, refused = _cooldown_setup(new_extreme_between=False)
    assert len(trades) == 1, "second entry must be blocked by cooldown"
    assert trades.iloc[0]["exit_reason"] == "stop"
    assert refused["cooldown"] == 1


def test_fixture_7b_new_20_bar_extreme_clears_cooldown():
    trades, refused = _cooldown_setup(new_extreme_between=True)
    assert len(trades) == 2, "new 20-bar high must permit re-entry"
    assert refused["cooldown"] == 0


def test_cooldown_is_direction_specific():
    """A stopped long must not block a short (the chosen convention)."""
    cfg = costs.CostConfig()
    df15 = bars15(60)
    all_min = make_1m(T0, [ENTRY_BAR, STOP_MIN] + flat(1000))
    signals = sig_frame([
        sig("ETHUSDT", "long", T0 + BAR * 5),
        sig("ETHUSDT", "short", T0 + BAR * 30),
    ])
    trades, refused = simulate.run_backtest(
        signals, {"ETHUSDT": df15}, {"ETHUSDT": all_min}, cfg,
        {"ETHUSDT": ConstTick(TICK)})[:2]
    assert refused["cooldown"] == 0
    assert len(trades) == 2


# --------------------------------------------------------------------------
# Fixture 8 -- funding refusal
# --------------------------------------------------------------------------

def test_fixture_8_unfundable_trade_is_refused():
    """Notional beyond equity * max_leverage must be refused, not booked."""
    # One position is ~630 notional; a 0.1x cap (=$200) cannot fund it.
    cfg = costs.CostConfig(max_leverage=0.1)
    df15 = bars15(60)
    all_min = make_1m(T0, [ENTRY_BAR] + flat(1000))
    signals = sig_frame([sig("ETHUSDT", "long", T0 + BAR * 5)])
    trades, refused, _ = simulate.run_backtest(
        signals, {"ETHUSDT": df15}, {"ETHUSDT": all_min}, cfg,
        {"ETHUSDT": ConstTick(TICK)})
    assert len(trades) == 0
    assert refused["insufficient_margin"] == 1


def test_concurrent_positions_respect_the_leverage_cap():
    """Three symbols signalling together: the cap must bind on the third."""
    cfg = costs.CostConfig(equity_usd=2000.0, max_leverage=0.65)  # cap $1300
    syms = ["BTCUSDT", "ETHUSDT", "SOLUSDT"]
    df15 = {s: bars15(60) for s in syms}
    mins = {s: make_1m(T0, [ENTRY_BAR] + flat(1000)) for s in syms}
    ticks = {s: ConstTick(TICK) for s in syms}
    signals = sig_frame([sig(s, "long", T0 + BAR * 5) for s in syms])
    trades, refused, _ = simulate.run_backtest(
        signals, df15, mins, cfg, ticks)
    # Each position is ~630 notional, so two fit under 1300 and the third does not.
    assert len(trades) == 2
    assert refused["insufficient_margin"] == 1
    assert trades["notional"].sum() <= cfg.equity_usd * cfg.max_leverage


def test_one_position_per_symbol_no_pyramiding():
    cfg = costs.CostConfig()
    df15 = bars15(60)
    all_min = make_1m(T0, [ENTRY_BAR] + flat(1000))
    # Two signals only 2 bars apart -- the first trade is still open.
    signals = sig_frame([
        sig("ETHUSDT", "long", T0 + BAR * 5),
        sig("ETHUSDT", "long", T0 + BAR * 7),
    ])
    trades, refused, _ = simulate.run_backtest(
        signals, {"ETHUSDT": df15}, {"ETHUSDT": all_min}, cfg,
        {"ETHUSDT": ConstTick(TICK)})
    assert len(trades) == 1
    assert refused["open_position"] == 1
