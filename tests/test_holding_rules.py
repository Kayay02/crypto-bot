"""Fix-pass fixtures: the two separate holding rules (B1) and net +1R (B2).

Built on the same hand-computed frame as the original fixtures: entry 100.00,
ATR 2.0, ETHUSDT tick 0.01, so stop = 97.00 and stop distance = 3.00.
"""

import costs
import pytest
import simulate
from conftest import make_1m, make_signal

SIG_TS = 1_600_000_000_000
ENTRY_TS = SIG_TS + simulate.BAR_15M_MS
TICK = 0.01
ENTRY_BAR = (100.10, 99.90, 100.0)


def flat(n, price=100.0):
    return [(price + 0.10, price - 0.10, price)] * n


def run(bars, direction="long", atr=2.0, cfg=None, symbol="ETHUSDT"):
    cfg = cfg or costs.CostConfig()
    sig = make_signal(symbol=symbol, direction=direction, sig_ts=SIG_TS, atr=atr)
    tr = simulate.Trace(enabled=False)
    return simulate.simulate_trade(sig, make_1m(ENTRY_TS, bars), cfg, TICK,
                                   trace=tr), cfg


def levels(cfg=None):
    """The net +1R and target levels for the standard fixture trade."""
    cfg = cfg or costs.CostConfig()
    q = costs.position_size(100.0, 97.0, "long", cfg, "ETHUSDT")
    r1 = costs.solve_r_level(100.0, q, "long", cfg, TICK)
    tgt = costs.solve_target(100.0, q, "long", cfg, TICK)
    return q, r1, tgt


def minute_touching(price):
    return (price + 0.05, price - 0.05, price)


# --------------------------------------------------------------------------
# B1 -- time stop vs max hold are different rules
# --------------------------------------------------------------------------

def test_config_rejects_max_hold_not_greater_than_time_stop():
    with pytest.raises(ValueError, match="max_hold_bars"):
        costs.CostConfig(time_stop_bars=16, max_hold_bars=16)
    with pytest.raises(ValueError, match="max_hold_bars"):
        costs.CostConfig(time_stop_bars=16, max_hold_bars=8)


def test_walk_buffer_is_derived_and_outlasts_max_hold():
    """The buffer must never be able to end a trade before max_hold_bars."""
    for mh in (20, 48, 96):
        cfg = costs.CostConfig(time_stop_bars=16, max_hold_bars=mh)
        need_minutes = (mh + 1) * 15      # through the execution minute
        assert simulate.max_walk_minutes(cfg) > need_minutes - 15, (
            "walk buffer could terminate a trade before max_hold")


def test_reached_1r_then_target_before_max_hold():
    """+1R reached, trade continues past bar 16, exits on target."""
    q, r1, tgt = levels()
    # Touch +1R early, drift past bar 16, then trade through the target.
    bars = ([ENTRY_BAR, minute_touching(r1 + 0.10)]
            + flat(300, price=101.0)
            + [(tgt + 5 * TICK, 101.0, tgt)]
            + flat(50, price=101.0))
    t, cfg = run(bars)
    assert t["reached_1r"] is True
    assert t["exit_reason"] == "target"
    assert t["bars_held"] > cfg.time_stop_bars, (
        "trade must survive past the time stop once +1R is reached")
    assert t["bars_held"] < cfg.max_hold_bars


def test_reached_1r_then_max_hold_cap():
    """+1R reached, never resolves, capped by max_hold (not by the buffer)."""
    q, r1, tgt = levels()
    cfg = costs.CostConfig()
    bars = ([ENTRY_BAR, minute_touching(r1 + 0.10)]
            + flat(simulate.max_walk_minutes(cfg), price=101.0))
    t, cfg = run(bars)
    assert t["reached_1r"] is True
    assert t["exit_reason"] == "max_hold"
    assert t["bars_held"] == cfg.max_hold_bars
    assert t["exit_ts"] == SIG_TS + simulate.BAR_15M_MS * (cfg.max_hold_bars + 1)


def test_reached_1r_then_stop():
    """+1R reached, trade continues, later stops out."""
    q, r1, tgt = levels()
    bars = ([ENTRY_BAR, minute_touching(r1 + 0.10)]
            + flat(300, price=101.0)
            + [(101.0, 96.0, 96.5)]
            + flat(50, price=97.0))
    t, cfg = run(bars)
    assert t["reached_1r"] is True
    assert t["exit_reason"] == "stop"
    assert t["bars_held"] > cfg.time_stop_bars


def test_walk_end_is_no_longer_reachable():
    """Running out of data is a DATA condition, never a trading decision."""
    # Deliberately short 1m path: fewer bars than the trade could need.
    bars = [ENTRY_BAR] + flat(30, price=100.0)
    t, _ = run(bars)
    assert t["exit_reason"] == "insufficient_data"
    assert t["exit_reason"] != "walk_end"


def test_insufficient_data_is_counted_separately():
    dist = simulate.EXIT_REASONS
    assert "insufficient_data" in dist
    assert "walk_end" not in dist


# --------------------------------------------------------------------------
# B2 -- +1R must be net of costs
# --------------------------------------------------------------------------

def test_net_1r_level_is_above_gross_1r_level():
    q, r1, tgt = levels()
    gross_r1 = 100.0 + (100.0 - 97.0)      # naive entry + stop distance
    assert r1 > gross_r1, (
        "net +1R must sit beyond gross +1R; otherwise a trade that has not "
        "made 1R after costs survives the time stop")


def test_net_1r_level_actually_delivers_1r():
    cfg = costs.CostConfig()
    q, r1, tgt = levels()
    _, _, net = costs.trade_pnl(100.0, r1, q, "long",
                                cfg.taker_fee, cfg.taker_fee)
    assert net >= cfg.risk_usd - 1e-9
    assert net == pytest.approx(cfg.risk_usd, abs=2 * q * TICK)


def test_gross_1r_touch_without_net_1r_is_still_time_stopped():
    """The B2 boundary case: gross +1R touched, net +1R not."""
    cfg = costs.CostConfig()
    q, r1, tgt = levels()
    gross_r1 = 100.0 + (100.0 - 97.0)
    assert gross_r1 < r1, "fixture requires a gap between gross and net levels"
    # Touch a price between the two levels, then drift flat forever.
    between = round((gross_r1 + r1) / 2.0, 2)
    bars = ([ENTRY_BAR, minute_touching(between)]
            + flat(simulate.max_walk_minutes(cfg), price=100.0))
    t, _ = run(bars)
    assert t["reached_1r"] is False, (
        "a touch below the NET +1R level must not count as reaching 1R")
    assert t["exit_reason"] == "time_stop"


def test_net_1r_uses_taker_not_maker():
    """Taker is the conservative assumption for the continuing exit."""
    cfg = costs.CostConfig()
    q, _, _ = levels()
    taker_level = costs.solve_r_level(100.0, q, "long", cfg, TICK)
    maker_level = costs.solve_price_for_net(
        100.0, q, "long", cfg, TICK, cfg.risk_usd, cfg.maker_fee)
    assert taker_level > maker_level


def test_short_side_net_1r_is_symmetric():
    cfg = costs.CostConfig()
    q = costs.position_size(100.0, 103.0, "short", cfg, "ETHUSDT")
    r1 = costs.solve_r_level(100.0, q, "short", cfg, TICK)
    gross_r1 = 100.0 - 3.0
    assert r1 < gross_r1
    _, _, net = costs.trade_pnl(100.0, r1, q, "short",
                                cfg.taker_fee, cfg.taker_fee)
    assert net >= cfg.risk_usd - 1e-9
