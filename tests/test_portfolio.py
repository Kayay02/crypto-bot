"""G1 fixtures 7 and 8 -- portfolio constraints: cooldown and funding."""

import costs
import numpy as np
import pandas as pd
import pytest
import simulate
from conftest import make_1m, make_cfg

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


def _cooldown_setup(new_extreme_between, cfg=None):
    """Two long signals on one symbol; the first stops out.

    The second is 25 bars later. `new_extreme_between` used to matter; after
    3R removed the extreme rule it is retained only to show that it does not.
    """
    cfg = cfg or make_cfg()
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


def test_fixture_7_new_extreme_rule_is_gone():
    """UPDATED at 3R: the 20-bar-extreme cooldown condition was a logical no-op.

    A long entry requires a close above the Donchian-20 upper band, which IS a
    new 20-bar high, so the condition that cleared the cooldown was entailed by
    the condition that triggered it. It could never bind. With cooldown_bars at
    its default of 0, nothing blocks re-entry regardless of whether a new
    extreme occurred -- which is the whole point of removing it.
    """
    for new_extreme_between in (False, True):
        trades, refused = _cooldown_setup(new_extreme_between=new_extreme_between)
        assert len(trades) == 2, "no rule should block re-entry at cooldown_bars=0"
        assert refused["cooldown"] == 0


def test_cooldown_is_now_a_pure_bar_count():
    """The surviving cooldown is cfg.cooldown_bars and nothing else."""
    trades, refused = _cooldown_setup(new_extreme_between=False,
                                      cfg=make_cfg(cooldown_bars=100))
    assert len(trades) == 1, "second entry must be blocked by the bar count"
    assert trades.iloc[0]["exit_reason"] == "stop"
    assert refused["cooldown"] == 1


def test_cooldown_is_direction_specific():
    """A stopped long must not block a short (the chosen convention)."""
    cfg = make_cfg()
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

def test_fixture_8_a_single_trade_can_never_be_unfundable_after_3R():
    """UPDATED at 3R, and it is a RESULT rather than a weakened test.

    The derived floor carries a leverage term risk_usd/(E*L_max), so when that
    term binds the stop is exactly wide enough that

        notional = risk_usd * P / (P*stop_pct + costs) < risk_usd / stop_pct
                 = risk_usd / (risk_usd/(E*L_max)) = E * L_max

    i.e. strictly below the margin cap, by construction. A SINGLE trade can
    therefore no longer be refused for margin at any leverage. This is what A2
    said the leverage term was for; the old fixture (0.1x cap refusing one
    ~630-notional trade) is unreachable because lowering max_leverage now also
    widens the floor and shrinks the position.

    Margin refusal survives only for CONCURRENT positions -- see the next test.
    """
    df15 = bars15(60)
    all_min = make_1m(T0, [ENTRY_BAR] + flat(1000))
    signals = sig_frame([sig("ETHUSDT", "long", T0 + BAR * 5)])
    for lev in (3.0, 0.65, 0.1, 0.02):
        cfg = make_cfg(max_leverage=lev)
        trades, refused, _ = simulate.run_backtest(
            signals, {"ETHUSDT": df15}, {"ETHUSDT": all_min}, cfg,
            {"ETHUSDT": ConstTick(TICK)})
        assert refused["insufficient_margin"] == 0, f"refused at {lev}x"
        assert len(trades) == 1
        assert trades.iloc[0]["notional"] <= cfg.equity_usd * cfg.max_leverage


def test_concurrent_positions_respect_the_leverage_cap():
    """Three symbols signalling together: the cap must bind on the third."""
    cfg = make_cfg(equity_usd=2000.0, max_leverage=0.65)  # cap $1300
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
    cfg = make_cfg()
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
