"""G1 -- synthetic fixtures whose correct answer is known by construction.

Every path is built by hand around entry=100.00, ATR=2.0 on ETHUSDT
(tick 0.01, haircut 5bps), which gives:
    stop distance = 1.5 * 2.0 = 3.00  (3.0% of entry, inside the 1%-3.5% band)
    stop          = 97.00
so a stop-out must lose exactly 1R and a target fill must make exactly 2R.
"""

import costs
import pytest
import simulate
from conftest import make_1m, make_signal

SIG_TS = 1_600_000_000_000              # a 15m boundary
ENTRY_TS = SIG_TS + simulate.BAR_15M_MS
TICK = 0.01


def run(bars, direction="long", atr=2.0, cfg=None, symbol="ETHUSDT",
        trace=False):
    cfg = cfg or costs.CostConfig()
    sig = make_signal(symbol=symbol, direction=direction, sig_ts=SIG_TS, atr=atr)
    tr = simulate.Trace(enabled=trace)
    t = simulate.simulate_trade(sig, make_1m(ENTRY_TS, bars), cfg, TICK, trace=tr)
    return t, tr


def flat(n, price=100.0):
    """n uneventful minutes hugging the entry price."""
    return [(price + 0.10, price - 0.10, price)] * n


# Bar 0 of every path is the ENTRY minute: its close sets the fill at 100.00,
# and its own high/low are pre-entry, so no fixture may rely on them.
ENTRY_BAR = (100.10, 99.90, 100.0)


# --------------------------------------------------------------------------

def test_fixture_1_stop_hit_first():
    bars = [ENTRY_BAR] + flat(2) + [(100.1, 96.50, 96.80)] + flat(5)
    t, _ = run(bars)
    assert t["exit_reason"] == "stop"
    assert t["resolution"] == "observed"
    # Fill is stop minus 5bps haircut, rounded away from entry.
    expected_fill = costs.round_to_tick(97.0 - 97.0 * 5 / 10_000, TICK, "down")
    assert t["exit_price"] == pytest.approx(expected_fill)
    assert t["net_pnl"] == pytest.approx(-20.0, abs=2 * t["qty"] * TICK)
    assert t["r_multiple"] == pytest.approx(-1.0, abs=0.01)


def test_fixture_2_target_hit_first():
    t0, _ = run([ENTRY_BAR] + flat(2))
    target = t0["target_price"]
    bars = [ENTRY_BAR] + flat(1) + [(target + 5 * TICK, 100.0, target)] + flat(3)
    t, _ = run(bars)
    assert t["exit_reason"] == "target"
    assert t["resolution"] == "observed"
    assert t["exit_price"] == pytest.approx(target)
    # Maker fee on the way out; must deliver a full +2R.
    assert t["net_pnl"] >= 2 * 20.0 - 1e-9
    assert t["net_pnl"] == pytest.approx(40.0, abs=0.10)
    assert t["r_multiple"] == pytest.approx(2.0, abs=0.01)


def test_fixture_3_both_levels_same_minute_takes_stop_and_flags_assumed():
    t0, _ = run([ENTRY_BAR] + flat(2))
    target = t0["target_price"]
    # One minute spanning both the stop and the target-through level.
    bars = [ENTRY_BAR, (target + 5 * TICK, 96.0, 99.0)] + flat(3)
    t, _ = run(bars)
    assert t["exit_reason"] == "stop"
    assert t["resolution"] == "assumed"        # unresolvable from 1m OHLC
    assert t["net_pnl"] < 0


def test_fixture_4_target_touched_but_not_traded_through_does_not_fill():
    t0, _ = run([ENTRY_BAR] + flat(2))
    target = t0["target_price"]
    # High reaches the target EXACTLY but not target + 1 tick.
    bars = [ENTRY_BAR, (target, 99.9, 100.2)] + flat(4) + [(100.0, 96.0, 96.5)]
    t, _ = run(bars)
    assert t["tp_touched_not_filled"] is True
    assert t["exit_reason"] != "target"        # the limit did NOT fill
    assert t["exit_reason"] == "stop"          # and the trade continued to a stop
    assert t["tp_after_touch"] == "continued"


def test_fixture_4b_one_tick_through_does_fill():
    """Boundary partner to fixture 4: target + 1 tick is a fill."""
    t0, _ = run([ENTRY_BAR] + flat(2))
    target = t0["target_price"]
    bars = [ENTRY_BAR, (target + TICK, 99.9, target)] + flat(3)
    t, _ = run(bars)
    assert t["exit_reason"] == "target"
    assert t["tp_touched_not_filled"] is False


def test_fixture_5_price_far_beyond_stop_is_flagged_unresolved():
    # Stop is 97.00; this minute trades down to 92.00, far past it.
    bars = [ENTRY_BAR, (99.9, 92.00, 93.0)] + flat(3)
    t, _ = run(bars)
    assert t["exit_reason"] == "stop"
    assert t["stop_fill_quality"] == "unresolved"


def test_fixture_5b_shallow_breach_is_normal_quality():
    bars = [ENTRY_BAR, (99.9, 96.95, 97.0)] + flat(3)
    t, _ = run(bars)
    assert t["exit_reason"] == "stop"
    assert t["stop_fill_quality"] == "normal"


def test_fixture_6_time_stop_when_1R_never_reached():
    cfg = costs.CostConfig()
    # Flat drift that never touches +1R net or the stop (97.00).
    bars = [ENTRY_BAR] + flat(simulate.max_walk_minutes(cfg) - 1, price=100.0)
    t, _ = run(bars)
    assert t["exit_reason"] == "time_stop"
    assert t["reached_1r"] is False
    # Decision at the close of bar 16, execution on the first minute of bar 17
    # -- mirroring the entry convention.
    assert t["exit_ts"] == SIG_TS + simulate.BAR_15M_MS * (cfg.time_stop_bars + 1)
    assert t["bars_held"] == cfg.time_stop_bars


def test_fixture_6b_no_time_stop_once_1R_reached():
    """+1R net touched intrabar suppresses the time stop; max_hold caps it."""
    cfg = costs.CostConfig()
    bars = ([ENTRY_BAR, (104.50, 99.9, 103.0)]
            + flat(simulate.max_walk_minutes(cfg) - 2, price=101.0))
    t, _ = run(bars)
    assert t["reached_1r"] is True
    assert t["exit_reason"] != "time_stop"
    assert t["exit_reason"] == "max_hold"


def test_short_direction_is_symmetric():
    sig_atr = 2.0
    bars = [ENTRY_BAR, (103.60, 100.0, 103.4)] + flat(3)
    t, _ = run(bars, direction="short", atr=sig_atr)
    assert t["stop_price"] == pytest.approx(103.0)
    assert t["exit_reason"] == "stop"
    assert t["net_pnl"] == pytest.approx(-20.0, abs=2 * t["qty"] * TICK)


def test_engine_never_reads_1m_open_or_volume():
    """The 1m fixture array has no open/volume fields at all.

    If any engine path ever reaches for them this raises, which is a stronger
    guarantee than a convention or a code review.
    """
    arr = make_1m(ENTRY_TS, [ENTRY_BAR] + flat(5))
    assert arr.dtype.names == ("ts", "high", "low", "close")
    t, _ = run([ENTRY_BAR] + flat(5))
    assert t is not None
