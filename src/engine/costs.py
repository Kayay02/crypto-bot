"""Fees, slippage, position sizing, target solving, tick rounding.

All of this is closed-form. Nothing here iterates to a solution, and nothing
here reads market data -- it takes prices as arguments so it can be unit-tested
against hand arithmetic.
"""

from dataclasses import dataclass, field

LONG = "long"
SHORT = "short"


@dataclass(frozen=True)
class CostConfig:
    """Every cost knob. Defaults are the Point 3 spec values.

    entry_slippage_bps is 0 by design: the one-minute fill convention already
    absorbs latency (~200ms measured round trip, so the convention over-covers
    by roughly 300x). It exists as a config value purely so it can be
    sensitivity-tested later -- do NOT raise it to "be safe", that double-counts.
    """
    taker_fee: float = 0.0006
    maker_fee: float = 0.0002
    risk_usd: float = 20.0
    entry_slippage_bps: float = 0.0
    # Stop-market haircut, bps of the stop price. Placeholders, per spec.
    stop_haircut_bps: dict = field(
        default_factory=lambda: {"BTCUSDT": 5.0, "ETHUSDT": 5.0,
                                 "SOLUSDT": 10.0})
    stop_atr_mult: float = 1.5
    stop_min_pct: float = 0.010
    stop_max_pct: float = 0.035
    target_r_multiple: float = 2.0
    # Funding check: refuse trades whose notional could not have been carried.
    equity_usd: float = 2000.0
    max_leverage: float = 3.0

    def haircut_bps(self, symbol):
        if symbol not in self.stop_haircut_bps:
            raise KeyError(f"no stop haircut configured for {symbol}")
        return self.stop_haircut_bps[symbol]


def round_to_tick(price, tick, mode="nearest"):
    """Round a price onto the tick grid.

    Integer-domain arithmetic: dividing by a tick like 0.0001 in binary floats
    leaves values such as 1.9999999999 that then truncate a whole tick the
    wrong way.
    """
    if tick <= 0:
        raise ValueError(f"tick must be positive, got {tick}")
    import math

    q = price / tick
    nearest = round(q)
    # If q is a grid multiple to within float noise, snap to it before any
    # floor/ceil -- otherwise 2.0/0.0001 == 19999.999999999996 would floor a
    # whole tick the wrong way.
    if abs(q - nearest) < 1e-9:
        n = nearest
    elif mode == "nearest":
        n = nearest
    elif mode == "up":
        n = math.ceil(q)
    elif mode == "down":
        n = math.floor(q)
    else:
        raise ValueError(f"bad mode {mode}")
    return round(n * tick, 12)


def stop_price(entry, atr, direction, cfg, tick):
    """1.5*ATR from entry, floored at 1.0% and capped at 3.5% of entry."""
    dist = cfg.stop_atr_mult * atr
    lo, hi = cfg.stop_min_pct * entry, cfg.stop_max_pct * entry
    dist = min(max(dist, lo), hi)
    raw = entry - dist if direction == LONG else entry + dist
    # Round the stop AWAY from entry so rounding never tightens the risk.
    return round_to_tick(raw, tick, "down" if direction == LONG else "up")


def solve_target(entry, qty, direction, cfg, tick):
    """Price at which net P&L equals +target_r_multiple * R after all costs.

    Long, with T the target and P the entry fill:
        net = q*(T - P) - q*P*f_taker - q*T*f_maker  =  2R
    Solving for T:
        T = ( 2R/q + P*(1 + f_taker) ) / (1 - f_maker)

    "2 x stop distance" is NOT equivalent: it ignores that the winner pays two
    fee legs on a larger notional, so realised winners land short of 2R while
    losers still pay a full 1R.
    """
    if qty <= 0:
        raise ValueError("qty must be positive")
    target_pnl = cfg.target_r_multiple * cfg.risk_usd
    if direction == LONG:
        raw = (target_pnl / qty + entry * (1 + cfg.taker_fee)) / (1 - cfg.maker_fee)
        # Round away from entry: never claim a fill at a price that pays < 2R.
        return round_to_tick(raw, tick, "up")
    raw = (entry * (1 - cfg.taker_fee) - target_pnl / qty) / (1 + cfg.maker_fee)
    return round_to_tick(raw, tick, "down")


def position_size(entry, stop, direction, cfg, symbol):
    """Closed-form qty giving exactly risk_usd loss if the stop is hit.

    Denominator is the all-in cost of one unit on a losing trade: the price
    move plus both fee legs plus both slippage legs. Sizing on (P - S) alone
    risks risk_usd PLUS costs -- about 7% oversized.

    s_stop is the stop-market haircut. Omitting it would size against a fill at
    the stop level that the engine then never grants, so realised losses would
    exceed risk_usd by the haircut.
    """
    s_entry = entry * cfg.entry_slippage_bps / 10_000.0
    s_stop = stop * cfg.haircut_bps(symbol) / 10_000.0
    move = (entry - stop) if direction == LONG else (stop - entry)
    if move <= 0:
        raise ValueError(f"stop on wrong side of entry: {entry=} {stop=} "
                         f"{direction=}")
    denom = move + entry * cfg.taker_fee + stop * cfg.taker_fee + s_entry + s_stop
    if denom <= 0:
        raise ValueError("non-positive risk denominator")
    return cfg.risk_usd / denom


def stop_fill_price(stop, direction, cfg, symbol, tick):
    """Stop-market fills through the level by the configured haircut."""
    h = stop * cfg.haircut_bps(symbol) / 10_000.0
    raw = stop - h if direction == LONG else stop + h
    return round_to_tick(raw, tick, "down" if direction == LONG else "up")


def entry_fill_price(raw_close, direction, cfg, tick):
    """Entry slippage applied to the 1m close convention (default 0)."""
    s = raw_close * cfg.entry_slippage_bps / 10_000.0
    raw = raw_close + s if direction == LONG else raw_close - s
    return round_to_tick(raw, tick, "nearest")


def trade_pnl(entry, exit_px, qty, direction, entry_fee_rate, exit_fee_rate):
    """Gross/fees/net for one round trip. Fees are charged on both notionals."""
    gross = qty * ((exit_px - entry) if direction == LONG else (entry - exit_px))
    fees = qty * entry * entry_fee_rate + qty * exit_px * exit_fee_rate
    return gross, fees, gross - fees


def r_multiple(net_pnl, cfg):
    return net_pnl / cfg.risk_usd
