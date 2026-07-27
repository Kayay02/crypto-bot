"""Unit tests for the closed-form cost/sizing/target math.

Every expected value here is computed independently in the test from the
formula in the spec, not copied from engine output.
"""

import costs
import pytest
from costs import LONG, SHORT

TICK = 0.01


def test_tick_rounding_modes():
    assert costs.round_to_tick(100.004, 0.01, "nearest") == pytest.approx(100.0)
    assert costs.round_to_tick(100.006, 0.01, "nearest") == pytest.approx(100.01)
    assert costs.round_to_tick(100.001, 0.01, "up") == pytest.approx(100.01)
    assert costs.round_to_tick(100.009, 0.01, "down") == pytest.approx(100.0)


def test_tick_rounding_survives_binary_float_error():
    """0.0001 grids are where naive //-based rounding drops a whole tick."""
    # 1.9999999999999998 / 0.0001 must not floor to 19999.
    assert costs.round_to_tick(2.0, 0.0001, "down") == pytest.approx(2.0)
    assert costs.round_to_tick(2.0, 0.0001, "up") == pytest.approx(2.0)
    assert costs.round_to_tick(0.0003, 0.0001, "nearest") == pytest.approx(0.0003)


def test_tick_rounding_rejects_bad_tick():
    with pytest.raises(ValueError):
        costs.round_to_tick(100.0, 0.0)


def test_stop_distance_floor_and_cap(cfg):
    # ATR tiny -> floored at 1.0% of entry.
    s = costs.stop_price(100.0, 0.01, LONG, cfg, TICK)
    assert s == pytest.approx(99.0)
    # ATR huge -> capped at 3.5% of entry.
    s = costs.stop_price(100.0, 50.0, LONG, cfg, TICK)
    assert s == pytest.approx(96.5)
    # In between -> 1.5 * ATR.
    s = costs.stop_price(100.0, 2.0, LONG, cfg, TICK)
    assert s == pytest.approx(97.0)


def test_stop_rounds_away_from_entry(cfg):
    """Rounding must never tighten the stop -- that would understate risk."""
    s_long = costs.stop_price(100.0, 2.0 / 1.5 * 1.0001, LONG, cfg, TICK)
    assert s_long <= 100.0 - 2.0 * 1.0001 + 1e-9 + TICK
    s_short = costs.stop_price(100.0, 2.0, SHORT, cfg, TICK)
    assert s_short >= 103.0 - 1e-9


def test_position_size_matches_spec_formula(cfg):
    entry, stop = 100.0, 97.0
    q = costs.position_size(entry, stop, LONG, cfg, "ETHUSDT")
    s_entry = entry * cfg.entry_slippage_bps / 10_000.0
    s_stop = stop * cfg.haircut_bps("ETHUSDT") / 10_000.0
    denom = ((entry - stop) + entry * cfg.taker_fee + stop * cfg.taker_fee
             + s_entry + s_stop)
    assert q == pytest.approx(cfg.risk_usd / denom)


def test_position_size_is_smaller_than_naive(cfg):
    """The cost-aware size must undercut 20/(P-S); spec expects roughly -7%."""
    entry, stop = 100.0, 97.0
    q = costs.position_size(entry, stop, LONG, cfg, "ETHUSDT")
    naive = cfg.risk_usd / (entry - stop)
    assert q < naive
    assert 0.90 < q / naive < 0.99


def test_position_size_rejects_stop_on_wrong_side(cfg):
    with pytest.raises(ValueError):
        costs.position_size(100.0, 103.0, LONG, cfg, "ETHUSDT")
    with pytest.raises(ValueError):
        costs.position_size(100.0, 97.0, SHORT, cfg, "ETHUSDT")


def test_losing_trade_costs_exactly_one_R(cfg):
    """The whole point of the closed form: a stop-out loses risk_usd, not more.

    Includes the stop haircut on the fill, which is why s_stop belongs in the
    sizing denominator.
    """
    for sym, direction, entry, stop in (
            ("ETHUSDT", LONG, 100.0, 97.0),
            ("ETHUSDT", SHORT, 100.0, 103.0),
            ("SOLUSDT", LONG, 20.0, 19.4),
    ):
        tick = 0.01 if sym == "ETHUSDT" else 0.001
        q = costs.position_size(entry, stop, direction, cfg, sym)
        fill = costs.stop_fill_price(stop, direction, cfg, sym, tick)
        _, _, net = costs.trade_pnl(entry, fill, q, direction,
                                    cfg.taker_fee, cfg.taker_fee)
        # The only slack is one tick of stop-fill rounding, worth q*tick.
        # It always rounds AWAY from entry, so the loss may marginally exceed
        # 1R but must never come in under it.
        assert net <= -cfg.risk_usd + 1e-9, (sym, direction)
        assert net == pytest.approx(-cfg.risk_usd, abs=2 * q * tick), (
            sym, direction)


def test_target_delivers_exactly_two_R(cfg):
    """Solved target must net +2R after taker in / maker out."""
    for direction, entry in ((LONG, 100.0), (SHORT, 100.0)):
        stop = 97.0 if direction == LONG else 103.0
        q = costs.position_size(entry, stop, direction, cfg, "ETHUSDT")
        t = costs.solve_target(entry, q, direction, cfg, TICK)
        _, _, net = costs.trade_pnl(entry, t, q, direction,
                                    cfg.taker_fee, cfg.maker_fee)
        assert net >= 2 * cfg.risk_usd - 1e-9
        assert net == pytest.approx(2 * cfg.risk_usd, abs=0.05)


def test_naive_2x_stop_target_falls_short_of_2R(cfg):
    """Documents WHY the solve exists: the naive target underdelivers."""
    entry, stop = 100.0, 97.0
    q = costs.position_size(entry, stop, LONG, cfg, "ETHUSDT")
    naive_target = entry + 2 * (entry - stop)
    _, _, net = costs.trade_pnl(entry, naive_target, q, LONG,
                                cfg.taker_fee, cfg.maker_fee)
    assert net < 2 * cfg.risk_usd
    solved = costs.solve_target(entry, q, LONG, cfg, TICK)
    assert solved > naive_target


def test_target_rounds_away_so_fill_never_underpays(cfg):
    entry, stop = 100.0, 97.0
    q = costs.position_size(entry, stop, LONG, cfg, "ETHUSDT")
    t = costs.solve_target(entry, q, LONG, cfg, TICK)
    raw = (2 * cfg.risk_usd / q + entry * (1 + cfg.taker_fee)) / (1 - cfg.maker_fee)
    assert t >= raw - 1e-12


def test_haircut_is_per_symbol(cfg):
    assert cfg.haircut_bps("SOLUSDT") == 10.0
    assert cfg.haircut_bps("BTCUSDT") == 5.0
    with pytest.raises(KeyError):
        cfg.haircut_bps("DOGEUSDT")


def test_entry_slippage_defaults_to_zero(cfg):
    assert cfg.entry_slippage_bps == 0.0
    assert costs.entry_fill_price(100.0, LONG, cfg, TICK) == pytest.approx(100.0)


def test_entry_slippage_is_configurable_and_directional():
    c = costs.CostConfig(entry_slippage_bps=10.0)
    assert costs.entry_fill_price(100.0, LONG, c, TICK) == pytest.approx(100.10)
    assert costs.entry_fill_price(100.0, SHORT, c, TICK) == pytest.approx(99.90)
