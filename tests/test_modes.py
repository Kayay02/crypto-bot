"""Signal mode vs portfolio mode, and the cooldown_bars knob."""

import costs
import pandas as pd
import pytest
import simulate
from conftest import make_1m, make_cfg
from test_portfolio import (BAR, ENTRY_BAR, STOP_MIN, T0, TICK, ConstTick,
                            bars15, flat, minutes_with_stop_after, sig,
                            sig_frame)


SYMS2 = ("ETHUSDT", "BTCUSDT")


def go(signals, cfg=None, mode="portfolio", df15=None, mins=None, n=60,
       symbols=("ETHUSDT",)):
    cfg = cfg or make_cfg()
    df15 = df15 if df15 is not None else bars15(n)
    mins = mins if mins is not None else make_1m(T0, [ENTRY_BAR] + flat(4000))
    return simulate.run_backtest(
        signals, {s: df15 for s in symbols}, {s: mins for s in symbols}, cfg,
        {s: ConstTick(TICK) for s in symbols}, mode=mode)


# --------------------------------------------------------------------------
# mode isolation
# --------------------------------------------------------------------------

def test_signal_mode_allows_overlapping_trades_on_one_symbol():
    """Portfolio mode refuses the second; signal mode simulates both."""
    signals = sig_frame([
        sig("ETHUSDT", "long", T0 + BAR * 5),
        sig("ETHUSDT", "long", T0 + BAR * 7),      # first trade still open
    ])
    pf, pf_ref, _ = go(signals, mode="portfolio")
    sg_, sg_ref, _ = go(signals, mode="signal")

    assert len(pf) == 1
    assert pf_ref["open_position"] == 1

    assert len(sg_) == 2, "signal mode must simulate every signal"
    assert sg_ref["open_position"] == 0
    # And they genuinely overlap in time.
    a, b = sg_.iloc[0], sg_.iloc[1]
    assert b["entry_ts"] < a["exit_ts"]


def test_signal_mode_ignores_cooldown():
    """UPDATED at 3R: cooldown_bars must now be set explicitly.

    The old version relied on the 20-bar-extreme rule binding at the default
    cooldown_bars=0. That rule is gone (logical no-op), so the mode difference
    is now demonstrated with a positive bar count.
    """
    cfg = make_cfg(cooldown_bars=100)
    signals = sig_frame([
        sig("ETHUSDT", "long", T0 + BAR * 5),
        sig("ETHUSDT", "long", T0 + BAR * 30),
    ])
    mins = minutes_with_stop_after([T0 + BAR * 6, T0 + BAR * 31])
    pf, pf_ref, _ = go(signals, cfg=cfg, mode="portfolio", mins=mins)
    sg_, sg_ref, _ = go(signals, cfg=cfg, mode="signal", mins=mins)
    assert pf_ref["cooldown"] == 1 and len(pf) == 1
    assert sg_ref["cooldown"] == 0 and len(sg_) == 2


def test_signal_mode_ignores_margin_cap():
    """UPDATED at 3R: a SINGLE trade can no longer be unfundable.

    The derived floor's leverage term guarantees notional < E * L_max, so the
    cap now binds only on CONCURRENT positions. Two overlapping signals on
    different symbols are used instead of one oversized trade.
    """
    cfg = make_cfg(max_leverage=0.35)     # cap $700; one trade is ~$630
    signals = sig_frame([
        sig("ETHUSDT", "long", T0 + BAR * 5),
        sig("BTCUSDT", "long", T0 + BAR * 5),
    ])
    pf, pf_ref, _ = go(signals, cfg=cfg, mode="portfolio", symbols=SYMS2)
    sg_, sg_ref, _ = go(signals, cfg=cfg, mode="signal", symbols=SYMS2)
    assert len(pf) == 1 and pf_ref["insufficient_margin"] == 1
    assert len(sg_) == 2 and sg_ref["insufficient_margin"] == 0


def test_single_isolated_trade_is_identical_in_both_modes():
    """The constraint set is the ONLY difference; lifecycle code is shared."""
    signals = sig_frame([sig("ETHUSDT", "long", T0 + BAR * 5)])
    pf, _, _ = go(signals, mode="portfolio")
    sg_, _, _ = go(signals, mode="signal")
    assert len(pf) == 1 and len(sg_) == 1
    a = pf.drop(columns=["variant"]).to_csv(index=False)
    b = sg_.drop(columns=["variant"]).to_csv(index=False)
    assert a == b, "an isolated trade must be byte-identical across modes"


def test_unknown_mode_raises():
    signals = sig_frame([sig("ETHUSDT", "long", T0 + BAR * 5)])
    with pytest.raises(ValueError, match="unknown mode"):
        go(signals, mode="portfolios")


# --------------------------------------------------------------------------
# the gated arm is a FILTER of the ungated table, not a second simulation
# --------------------------------------------------------------------------

def test_gated_arm_is_a_partition_of_the_ungated_table():
    import run as engine_run

    signals = sig_frame([
        {**sig("ETHUSDT", "long", T0 + BAR * 5), "rvol": 3.0},
        {**sig("ETHUSDT", "long", T0 + BAR * 25), "rvol": 1.1},
    ])
    trades, _, _ = go(signals, mode="signal")
    assert len(trades) == 2
    gated = engine_run.gated_arm(trades, 1.5)
    assert len(gated) == 1
    assert gated.iloc[0]["rvol"] == 3.0
    # Every gated row is literally a row of the ungated table.
    key = ["symbol", "signal_bar_ts", "direction"]
    assert set(map(tuple, gated[key].values)) <= set(map(tuple, trades[key].values))


def test_rvol_is_recorded_on_every_trade():
    signals = sig_frame([sig("ETHUSDT", "long", T0 + BAR * 5)])
    trades, _, _ = go(signals, mode="signal")
    assert "rvol" in trades.columns
    assert trades["rvol"].notna().all()


# --------------------------------------------------------------------------
# cooldown_bars
# --------------------------------------------------------------------------

# The first signal must sit past the 20-bar rolling warm-up, otherwise the
# extreme flags are all NaN and the extreme rule blocks regardless of the knob.
FIRST_SIG_BAR = 30


def _cooldown_bars_run(cooldown_bars, gap_bars):
    """Stop out just after FIRST_SIG_BAR, re-signal `gap_bars` bars later.

    Every bar from the stop-out onward is a new 20-bar high, so the extreme
    rule clears immediately and cooldown_bars is the ONLY thing that can bind.
    Otherwise this would just be re-testing the extreme rule.
    """
    cfg = make_cfg(cooldown_bars=cooldown_bars)
    df15 = bars15(90)
    for i in range(FIRST_SIG_BAR + 2, 90):
        df15.loc[i, "high"] = 200.0 + i
    entry_bar = FIRST_SIG_BAR + 1
    mins = minutes_with_stop_after([T0 + BAR * entry_bar], total=6000)
    signals = sig_frame([
        sig("ETHUSDT", "long", T0 + BAR * FIRST_SIG_BAR),
        sig("ETHUSDT", "long", T0 + BAR * (entry_bar + gap_bars)),
    ])
    return go(signals, cfg=cfg, mode="portfolio", df15=df15, mins=mins, n=90)


def test_cooldown_bars_zero_blocks_nothing():
    trades, refused, _ = _cooldown_bars_run(cooldown_bars=0, gap_bars=1)
    assert refused["cooldown"] == 0
    assert len(trades) == 2


def test_cooldown_bars_three_blocks_inside_the_window():
    trades, refused, _ = _cooldown_bars_run(cooldown_bars=3, gap_bars=2)
    assert refused["cooldown"] == 1
    assert len(trades) == 1


def test_cooldown_bars_three_permits_after_the_window():
    trades, refused, _ = _cooldown_bars_run(cooldown_bars=3, gap_bars=4)
    assert refused["cooldown"] == 0
    assert len(trades) == 2


def test_cooldown_bars_default_is_zero():
    assert make_cfg().cooldown_bars == 0


def test_negative_cooldown_bars_rejected():
    with pytest.raises(ValueError, match="cooldown_bars"):
        make_cfg(cooldown_bars=-1)
