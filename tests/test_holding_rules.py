"""Holding rules: derived bar counts, derived threshold_R, and the STATE CHECK.

Built on the same hand-computed frame as the original fixtures: entry 100.00,
ATR 2.0, ETHUSDT tick 0.01, stop_atr_mult 1.5, so the raw ATR distance is 3.00.
The DERIVED floor for ETHUSDT is 1.020% of entry = 1.02, well below 3.00, so
the ATR term still sets the stop at 97.00 and the fixture arithmetic carries
over from Point 3 unchanged.

POINT 3R CHANGED THE TIME STOP FROM A LATCH TO A STATE CHECK. The tests that
previously asserted "touched +1R intrabar => survives the time stop" are
updated below, deliberately, with the reason recorded on each: intrabar touch
is no longer the test, the checkpoint CLOSE is.
"""

import costs
import pytest
import simulate
from conftest import make_1m, make_cfg, make_signal

SIG_TS = 1_600_000_000_000
ENTRY_TS = SIG_TS + simulate.BAR_15M_MS
TICK = 0.01
ENTRY_BAR = (100.10, 99.90, 100.0)


def flat(n, price=100.0):
    return [(price + 0.10, price - 0.10, price)] * n


def run(bars, direction="long", atr=2.0, cfg=None, symbol="ETHUSDT"):
    cfg = cfg or make_cfg()
    sig = make_signal(symbol=symbol, direction=direction, sig_ts=SIG_TS, atr=atr)
    tr = simulate.Trace(enabled=False)
    return simulate.simulate_trade(sig, make_1m(ENTRY_TS, bars), cfg, TICK,
                                   trace=tr), cfg


def levels(cfg=None):
    """The net threshold_R and target levels for the standard fixture trade."""
    cfg = cfg or make_cfg()
    q = costs.position_size(100.0, 97.0, "long", cfg, "ETHUSDT")
    r1 = costs.solve_r_level(100.0, q, "long", cfg, TICK)
    tgt = costs.solve_target(100.0, q, "long", cfg, TICK)
    return q, r1, tgt


def minute_touching(price):
    return (price + 0.05, price - 0.05, price)


# --------------------------------------------------------------------------
# derived bar counts and threshold_R
# --------------------------------------------------------------------------

def test_time_stop_and_max_hold_derive_from_donchian_period():
    cfg = make_cfg(donchian_period=20, tau=1.0)
    assert cfg.time_stop_bars == 20
    assert cfg.max_hold_bars == 40
    # The old values are void.
    assert cfg.time_stop_bars != 16 and cfg.max_hold_bars != 48


def test_tau_scales_the_time_stop_only():
    cfg = make_cfg(donchian_period=20, tau=0.8)
    assert cfg.time_stop_bars == 16
    assert cfg.max_hold_bars == 40, "max_hold is not independently sweepable"


def test_max_hold_and_time_stop_are_not_independently_settable():
    with pytest.raises(TypeError):
        make_cfg(max_hold_bars=48)
    with pytest.raises(TypeError):
        make_cfg(time_stop_bars=16)


def test_threshold_r_is_derived_from_phi():
    cfg = make_cfg(donchian_period=20, tau=1.0, phi=1.0, target_r_multiple=2.0)
    # phi = (thr/target) / (time_stop/max_hold)  =>  thr = phi*target*20/40
    assert cfg.threshold_r == pytest.approx(1.0)


def test_phi_of_1_5_reproduces_the_old_geometry():
    """The old +1R-at-bar-16 geometry was phi = (1/2)/(16/48) = 1.5.

    Nobody chose it; it fell out of two unrelated placeholders. Recovering it
    from phi is what makes that visible.
    """
    old_phi = (1.0 / 2.0) / (16.0 / 48.0)
    assert old_phi == pytest.approx(1.5)

    cfg = make_cfg(donchian_period=16, tau=1.0, phi=1.5, target_r_multiple=2.0)
    assert cfg.time_stop_bars == 16
    assert cfg.max_hold_bars == 32
    assert cfg.threshold_r == pytest.approx(1.5)


def test_front_loading_is_a_choice_not_a_default():
    assert make_cfg().phi == 1.0
    assert make_cfg(phi=1.5).threshold_r > make_cfg(phi=1.0).threshold_r


def test_config_rejects_max_hold_not_greater_than_time_stop():
    # tau >= 2.0 makes time_stop_bars reach or pass max_hold_bars.
    with pytest.raises(ValueError, match="max_hold_bars"):
        make_cfg(donchian_period=20, tau=2.0)
    with pytest.raises(ValueError, match="max_hold_bars"):
        make_cfg(donchian_period=20, tau=3.0)


def test_walk_buffer_is_derived_and_outlasts_max_hold():
    """The buffer must never be able to end a trade before max_hold can fire.

    TIGHTENED by the 3R fix pass: max hold now executes on the first minute of
    bar max_hold_bars+1, so the buffer must reach that minute index, not merely
    the previous bar.
    """
    for dp in (10, 20, 48):
        cfg = make_cfg(donchian_period=dp, tau=1.0)
        need_minutes = (cfg.max_hold_bars + 1) * 15
        assert simulate.max_walk_minutes(cfg) > need_minutes, (
            "walk buffer could terminate a trade before max_hold")


# --------------------------------------------------------------------------
# STATE CHECK vs LATCH -- the Point 3R behavioural change
# --------------------------------------------------------------------------

def test_touch_then_retrace_IS_time_stopped():
    """THE behavioural change. Under the old latch this trade survived.

    A wick to +1R that immediately retraces is the liquidity-vacuum failure
    mode the state check exists to catch, so it is now cut at the checkpoint.
    """
    cfg = make_cfg()
    q, r1, tgt = levels(cfg)
    bars = ([ENTRY_BAR, minute_touching(r1 + 0.10)]
            + flat(simulate.max_walk_minutes(cfg), price=100.0))
    t, _ = run(bars, cfg=cfg)
    assert t["touched_threshold_intrabar"] is True, "fixture must touch +1R"
    assert t["at_threshold_at_checkpoint"] is False
    assert t["exit_reason"] == "time_stop", (
        "touched-then-retraced must now be time-stopped; the latch is gone")


def test_at_threshold_at_the_checkpoint_close_continues():
    """Held ABOVE threshold at the checkpoint close -> trade continues."""
    cfg = make_cfg()
    q, r1, tgt = levels(cfg)
    above = round(r1 + 0.50, 2)
    bars = [ENTRY_BAR] + flat(simulate.max_walk_minutes(cfg), price=above)
    t, _ = run(bars, cfg=cfg)
    assert t["at_threshold_at_checkpoint"] is True
    assert t["exit_reason"] == "max_hold"
    # UPDATED by the 3R fix pass: max hold now decides on the CLOSE of bar
    # max_hold_bars and executes on the next bar, like every other exit.
    assert t["bars_held"] == cfg.max_hold_bars + 1


def test_exactly_at_threshold_at_the_checkpoint_continues():
    """Boundary: >= is the test, so exactly at threshold survives."""
    cfg = make_cfg()
    q, r1, tgt = levels(cfg)
    bars = [ENTRY_BAR] + flat(simulate.max_walk_minutes(cfg), price=r1)
    t, _ = run(bars, cfg=cfg)
    assert t["checkpoint_price"] == pytest.approx(r1)
    assert t["at_threshold_at_checkpoint"] is True
    assert t["exit_reason"] != "time_stop"


def test_one_tick_below_threshold_at_the_checkpoint_is_time_stopped():
    cfg = make_cfg()
    q, r1, tgt = levels(cfg)
    bars = ([ENTRY_BAR]
            + flat(simulate.max_walk_minutes(cfg), price=round(r1 - TICK, 2)))
    t, _ = run(bars, cfg=cfg)
    assert t["at_threshold_at_checkpoint"] is False
    assert t["exit_reason"] == "time_stop"


def test_checkpoint_decides_on_a_close_and_executes_on_the_next_bar():
    cfg = make_cfg()
    bars = [ENTRY_BAR] + flat(simulate.max_walk_minutes(cfg), price=100.0)
    t, _ = run(bars, cfg=cfg)
    assert t["exit_ts"] == ENTRY_TS + simulate.BAR_15M_MS * (cfg.time_stop_bars + 1)


def test_short_side_state_check_is_symmetric():
    cfg = make_cfg()
    q = costs.position_size(100.0, 103.0, "short", cfg, "ETHUSDT")
    r1 = costs.solve_r_level(100.0, q, "short", cfg, TICK)
    # Held BELOW the short threshold price => at/above threshold in P&L terms.
    bars = ([ENTRY_BAR]
            + flat(simulate.max_walk_minutes(cfg), price=round(r1 - 0.50, 2)))
    t, _ = run(bars, direction="short", cfg=cfg)
    assert t["at_threshold_at_checkpoint"] is True
    assert t["exit_reason"] != "time_stop"


# --------------------------------------------------------------------------
# surviving trades still reach target / stop / max hold
# --------------------------------------------------------------------------

def test_above_threshold_then_target_before_max_hold():
    """UPDATED at 3R: the trade must now HOLD above threshold, not just touch."""
    cfg = make_cfg()
    q, r1, tgt = levels(cfg)
    above = round(r1 + 0.50, 2)
    bars = ([ENTRY_BAR]
            + flat((cfg.time_stop_bars + 2) * 15, price=above)
            + [(tgt + 5 * TICK, above, tgt)]
            + flat(50, price=above))
    t, _ = run(bars, cfg=cfg)
    assert t["at_threshold_at_checkpoint"] is True
    assert t["exit_reason"] == "target"
    assert t["bars_held"] > cfg.time_stop_bars
    assert t["bars_held"] < cfg.max_hold_bars


def test_above_threshold_then_max_hold_cap():
    """UPDATED at 3R: held above threshold, never resolves, capped by max_hold."""
    cfg = make_cfg()
    q, r1, tgt = levels(cfg)
    bars = ([ENTRY_BAR]
            + flat(simulate.max_walk_minutes(cfg), price=round(r1 + 0.50, 2)))
    t, _ = run(bars, cfg=cfg)
    assert t["exit_reason"] == "max_hold"
    # UPDATED by the 3R fix pass: see test_at_threshold_at_the_checkpoint_close_continues.
    assert t["bars_held"] == cfg.max_hold_bars + 1
    assert t["exit_ts"] == ENTRY_TS + simulate.BAR_15M_MS * (cfg.max_hold_bars + 1)


def test_above_threshold_then_stop():
    """UPDATED at 3R: held above threshold past the checkpoint, later stops."""
    cfg = make_cfg()
    q, r1, tgt = levels(cfg)
    above = round(r1 + 0.50, 2)
    bars = ([ENTRY_BAR]
            + flat((cfg.time_stop_bars + 2) * 15, price=above)
            + [(above, 96.0, 96.5)]
            + flat(50, price=97.0))
    t, _ = run(bars, cfg=cfg)
    assert t["at_threshold_at_checkpoint"] is True
    assert t["exit_reason"] == "stop"
    assert t["bars_held"] > cfg.time_stop_bars


def test_walk_end_is_no_longer_reachable():
    """Running out of data is a DATA condition, never a trading decision."""
    bars = [ENTRY_BAR] + flat(30, price=100.0)
    t, _ = run(bars)
    assert t["exit_reason"] == "insufficient_data"
    assert t["exit_reason"] != "walk_end"


def test_insufficient_data_is_counted_separately():
    assert "insufficient_data" in simulate.EXIT_REASONS
    assert "walk_end" not in simulate.EXIT_REASONS


# --------------------------------------------------------------------------
# NO_TIME_STOP counterfactual arm (D1)
# --------------------------------------------------------------------------

def test_no_time_stop_arm_disables_the_checkpoint():
    cfg = make_cfg(time_stop_enabled=False)
    bars = [ENTRY_BAR] + flat(simulate.max_walk_minutes(cfg), price=100.0)
    t, _ = run(bars, cfg=cfg)
    assert t["exit_reason"] == "max_hold", "time stop should not have fired"
    assert t["at_threshold_at_checkpoint"] is None


def test_no_time_stop_arm_changes_nothing_else():
    """It must disable the checkpoint and ONLY the checkpoint."""
    on = make_cfg(time_stop_enabled=True)
    off = make_cfg(time_stop_enabled=False)
    # A trade that stops out before the checkpoint is unaffected either way.
    bars = [ENTRY_BAR] + flat(20, 100.0) + [(100.0, 96.0, 96.5)] + flat(50, 97.0)
    a, _ = run(bars, cfg=on)
    b, _ = run(bars, cfg=off)
    for k in ("exit_reason", "exit_ts", "exit_price", "qty", "stop_price",
              "target_price", "entry_price", "net_pnl"):
        assert a[k] == b[k], f"{k} differs between time-stop arms"


# --------------------------------------------------------------------------
# threshold_R must be net of costs
# --------------------------------------------------------------------------

def test_net_threshold_level_is_above_gross_1r_level():
    q, r1, tgt = levels()
    gross_r1 = 100.0 + (100.0 - 97.0)
    assert r1 > gross_r1, (
        "net threshold must sit beyond gross 1R; otherwise a trade that has "
        "not made 1R after costs survives the checkpoint")


def test_net_threshold_level_actually_delivers_1r():
    cfg = make_cfg()
    q, r1, tgt = levels(cfg)
    _, _, net = costs.trade_pnl(100.0, r1, q, "long",
                                cfg.taker_fee, cfg.taker_fee)
    assert net >= cfg.risk_usd - 1e-9
    assert net == pytest.approx(cfg.risk_usd, abs=2 * q * TICK)


def test_gross_1r_close_without_net_1r_is_still_time_stopped():
    """Boundary: closing between gross and net 1R fails the state check."""
    cfg = make_cfg()
    q, r1, tgt = levels(cfg)
    gross_r1 = 100.0 + (100.0 - 97.0)
    assert gross_r1 < r1, "fixture requires a gap between gross and net levels"
    between = round((gross_r1 + r1) / 2.0, 2)
    bars = [ENTRY_BAR] + flat(simulate.max_walk_minutes(cfg), price=between)
    t, _ = run(bars, cfg=cfg)
    assert t["at_threshold_at_checkpoint"] is False
    assert t["exit_reason"] == "time_stop"


def test_net_threshold_uses_taker_not_maker():
    """Taker is the conservative assumption for the continuing exit."""
    cfg = make_cfg()
    q, _, _ = levels(cfg)
    taker_level = costs.solve_r_level(100.0, q, "long", cfg, TICK)
    maker_level = costs.solve_price_for_net(
        100.0, q, "long", cfg, TICK, cfg.threshold_r * cfg.risk_usd,
        cfg.maker_fee)
    assert taker_level > maker_level


def test_short_side_net_threshold_is_symmetric():
    cfg = make_cfg()
    q = costs.position_size(100.0, 103.0, "short", cfg, "ETHUSDT")
    r1 = costs.solve_r_level(100.0, q, "short", cfg, TICK)
    gross_r1 = 100.0 - 3.0
    assert r1 < gross_r1
    _, _, net = costs.trade_pnl(100.0, r1, q, "short",
                                cfg.taker_fee, cfg.taker_fee)
    assert net >= cfg.risk_usd - 1e-9


# --------------------------------------------------------------------------
# 3R fix pass -- symmetric exit timing
# --------------------------------------------------------------------------

def test_time_stop_holds_time_stop_bars_plus_one():
    cfg = make_cfg()
    bars = [ENTRY_BAR] + flat(simulate.max_walk_minutes(cfg), price=100.0)
    t, _ = run(bars, cfg=cfg)
    assert t["exit_reason"] == "time_stop"
    assert t["bars_held"] == cfg.time_stop_bars + 1


def test_max_hold_holds_max_hold_bars_plus_one():
    cfg = make_cfg()
    q, r1, tgt = levels(cfg)
    bars = ([ENTRY_BAR]
            + flat(simulate.max_walk_minutes(cfg), price=round(r1 + 0.50, 2)))
    t, _ = run(bars, cfg=cfg)
    assert t["exit_reason"] == "max_hold"
    assert t["bars_held"] == cfg.max_hold_bars + 1


def test_both_exits_use_the_same_decide_then_execute_convention():
    """Every exit decides on a CLOSED 15m bar and fills on the next one.

    This is the entry convention (signal on closed bar T, fill in T+1) applied
    to exits. Before the fix pass max hold cut at the START of bar
    max_hold_bars, so `max_hold_bars = 40` did not actually mean 40 bars.
    """
    cfg = make_cfg()
    q, r1, tgt = levels(cfg)

    below = [ENTRY_BAR] + flat(simulate.max_walk_minutes(cfg), price=100.0)
    above = ([ENTRY_BAR]
             + flat(simulate.max_walk_minutes(cfg), price=round(r1 + 0.50, 2)))

    ts_trade, _ = run(below, cfg=cfg)
    mh_trade, _ = run(above, cfg=cfg)

    for t, n in ((ts_trade, cfg.time_stop_bars), (mh_trade, cfg.max_hold_bars)):
        # Executed at the FIRST 1m bar of bar n+1 ...
        assert t["exit_ts"] == ENTRY_TS + simulate.BAR_15M_MS * (n + 1)
        # ... which is exactly one minute past the close of bar n, not at it.
        decision_close = (ENTRY_TS + simulate.BAR_15M_MS * n
                          + simulate.BAR_15M_MS - simulate.BAR_1M_MS)
        assert t["exit_ts"] == decision_close + simulate.BAR_1M_MS
        assert t["bars_held"] == n + 1


def test_walk_buffer_still_covers_the_max_hold_execution_minute():
    """The buffer must outlast the LAST minute any rule can fire."""
    for dp in (10, 20, 48):
        cfg = make_cfg(donchian_period=dp, tau=1.0)
        last_rule_minute_index = (cfg.max_hold_bars + 1) * 15
        assert simulate.max_walk_minutes(cfg) > last_rule_minute_index, (
            "walk buffer could expire before max hold could fire, which would "
            "misreport a trading decision as insufficient_data")


def test_exhausting_the_buffer_is_still_insufficient_data_not_walk_end():
    cfg = make_cfg()
    bars = [ENTRY_BAR] + flat(30, price=100.0)
    t, _ = run(bars, cfg=cfg)
    assert t["exit_reason"] == "insufficient_data"
    assert "walk_end" not in simulate.EXIT_REASONS


def test_realised_pace_ratio_differs_from_the_parameter_ratio():
    """A footnote, pinned so it is not later mistaken for a bug.

    phi is defined on PARAMETERS (20/40 = 0.500), so threshold_R is unaffected
    by the fix. Realised holds are 21 and 41 bars, a ratio of ~0.512. Nothing
    derives from the realised ratio.
    """
    cfg = make_cfg(donchian_period=20, tau=1.0, phi=1.0)
    assert cfg.time_stop_bars / cfg.max_hold_bars == pytest.approx(0.500)
    realised = (cfg.time_stop_bars + 1) / (cfg.max_hold_bars + 1)
    assert realised == pytest.approx(21 / 41)
    assert realised == pytest.approx(0.5122, abs=1e-4)
    assert cfg.threshold_r == pytest.approx(1.0), "threshold_R must not move"


# --------------------------------------------------------------------------
# 3R fix pass -- threshold solve pinned to hand arithmetic
# --------------------------------------------------------------------------

def test_threshold_solve_matches_hand_arithmetic_at_a_coarse_tick():
    """Pin the solve where tick rounding CANNOT hide an error of report-08 size.

    reports/08_point_3r.md originally printed the unrounded solve as 103.2836
    where the formula gives 103.288673 -- a relative error of ~4.7e-5. At
    ETHUSDT's 0.01 tick on a ~100 price both round to 103.29, so the fixture
    could not tell them apart. On a BTCUSDT-scale price with a 0.1 tick the
    same relative error is ~1 unit, i.e. about 10 ticks, so it cannot hide.
    """
    cfg = make_cfg()
    tick = 0.1                      # BTCUSDT
    entry, stop = 20000.0, 19796.0  # ~1.02% stop, floor-scale
    q = costs.position_size(entry, stop, "long", cfg, "BTCUSDT")

    f = cfg.taker_fee
    net = cfg.threshold_r * cfg.risk_usd
    expected_raw = (net / q + entry * (1 + f)) / (1 - f)
    expected = costs.round_to_tick(expected_raw, tick, "up")

    got = costs.solve_r_level(entry, q, "long", cfg, tick)
    assert got == pytest.approx(expected)

    # The error in the report prose would have been ~10 ticks off here.
    bad_raw = expected_raw * (1.0 - 4.7e-5)
    assert abs(costs.round_to_tick(bad_raw, tick, "up") - got) > 5 * tick, (
        "fixture is too coarse to detect the error class it exists to catch")

    # And the level really does deliver threshold_R net of costs.
    _, _, realised = costs.trade_pnl(entry, got, q, "long", f, f)
    assert realised >= net - 1e-9
    assert realised == pytest.approx(net, abs=2 * q * tick)


def test_threshold_solve_short_side_at_a_coarse_tick():
    cfg = make_cfg()
    tick = 0.1
    entry, stop = 20000.0, 20204.0
    q = costs.position_size(entry, stop, "short", cfg, "BTCUSDT")
    f = cfg.taker_fee
    net = cfg.threshold_r * cfg.risk_usd
    expected = costs.round_to_tick(
        (entry * (1 - f) - net / q) / (1 + f), tick, "down")
    assert costs.solve_r_level(entry, q, "short", cfg, tick) == pytest.approx(expected)
