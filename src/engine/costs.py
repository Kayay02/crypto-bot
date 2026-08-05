"""Fees, slippage, position sizing, target solving, tick rounding.

All of this is closed-form. Nothing here iterates to a solution, and nothing
here reads market data -- it takes prices as arguments so it can be unit-tested
against hand arithmetic.

Point 3R changed the shape of this module in three ways:

  * Four parameters have NO DEFAULT and raise if not supplied
    (stop_atr_mult, stop_max_pct, rvol_threshold, baseline_days). Each was a
    placeholder that silently acted as a chosen value; a stale default is
    exactly the failure 3R exists to correct.
  * stop_min_pct is DERIVED per symbol from the cost structure, never chosen.
    It is per-symbol because its INPUTS are per-symbol (the stop-market
    haircut), not because it was tuned per symbol. N_cost is the shared knob.
  * time_stop_bars, max_hold_bars and threshold_r are DERIVED from
    donchian_period, tau and phi. The old values 16 / 48 / +1R-as-input are
    void.
"""

from dataclasses import dataclass, field

LONG = "long"
SHORT = "short"


class _Required:
    """Sentinel for a parameter that must be supplied explicitly.

    A dataclass field needs *some* default for ordering, so the absence of a
    value is represented rather than omitted, and __post_init__ turns it into
    an error. The alternative -- a plausible-looking number -- is what let
    stop_atr_mult=1.5 survive as a "default" nobody had chosen.
    """

    def __repr__(self):
        return "<REQUIRED>"

    def __bool__(self):
        raise TypeError("REQUIRED sentinel used as a value")


REQUIRED = _Required()

# Parameters with no default. Named here so the error message and the tests
# can share one list.
NO_DEFAULT_PARAMS = ("stop_atr_mult", "stop_max_pct", "rvol_threshold",
                     "baseline_days")


@dataclass(frozen=True)
class CostConfig:
    """Every cost and geometry knob.

    entry_slippage_bps is 0 by design: the one-minute fill convention already
    absorbs latency (~200ms measured round trip, so the convention over-covers
    by roughly 300x). It exists as a config value purely so it can be
    sensitivity-tested later -- do NOT raise it to "be safe", that double-counts.
    """

    # ---- required: no default, must be supplied -------------------------
    stop_atr_mult: float = REQUIRED
    stop_max_pct: float = REQUIRED
    rvol_threshold: float = REQUIRED
    baseline_days: int = REQUIRED

    # ---- fees and slippage ----------------------------------------------
    taker_fee: float = 0.0006
    maker_fee: float = 0.0002
    risk_usd: float = 20.0
    entry_slippage_bps: float = 0.0
    # Stop-market haircut, bps of the stop price. Placeholders, per spec.
    stop_haircut_bps: dict = field(
        default_factory=lambda: {"BTCUSDT": 5.0, "ETHUSDT": 5.0,
                                 "SOLUSDT": 10.0})

    # ---- derived stop floor ---------------------------------------------
    # The one chosen number in the floor: costs may consume at most ~1/N_cost
    # of the risk distance. Shared across symbols.
    n_cost: float = 6.0

    target_r_multiple: float = 2.0

    # ---- holding-period geometry, all DERIVED ---------------------------
    # time_stop_bars = tau * donchian_period; max_hold_bars = 2 * donchian.
    # At bar `donchian_period` post-entry every bar in the Donchian lookback
    # is post-breakout: the high that was broken has rolled out of the window,
    # so the reference frame that generated the signal no longer exists.
    donchian_period: int = 20
    tau: float = 1.0
    # Pace factor. threshold_r is an OUTPUT of phi, not an input.
    # phi = (threshold_R/target_R) / (time_stop_bars/max_hold_bars).
    # phi = 1.0 is linear pace. The old geometry implied phi = 1.5 -- 50% of
    # the price journey in 33% of the time budget -- which nobody chose.
    phi: float = 1.0

    # NO_TIME_STOP counterfactual arm (D1), for the D5 leave-one-out pass.
    time_stop_enabled: bool = True

    # Cooldown after a stop-out, in 15m bars. 0 preserves prior behaviour.
    # The 20-bar-extreme condition was REMOVED in 3R (logical no-op); this
    # bar count is retained because it was registered as a sweep dimension
    # before the firewall, and at 0 it is behaviourally inert.
    cooldown_bars: int = 0

    # Fraction of stop distance travelled beyond the level within the trigger
    # minute, past which the stop fill is flagged "unresolved". Admittedly
    # arbitrary, hence configurable.
    stop_unresolved_frac: float = 0.5

    # Margin check: refuse trades whose notional could not have been carried.
    # NOT a probed exchange constraint -- an unmeasured placeholder.
    equity_usd: float = 2000.0
    max_leverage: float = 3.0

    def __post_init__(self):
        missing = [p for p in NO_DEFAULT_PARAMS
                   if isinstance(getattr(self, p), _Required)]
        if missing:
            raise ValueError(
                f"required parameter(s) not supplied: {', '.join(missing)}. "
                f"These have no default by design (Point 3R): a stale "
                f"placeholder acting as a chosen value is the failure mode "
                f"being corrected. Supply them explicitly.")

        if self.donchian_period <= 0:
            raise ValueError("donchian_period must be positive")
        if self.tau <= 0:
            raise ValueError("tau must be positive")
        if self.phi <= 0:
            raise ValueError("phi must be positive")
        if self.max_hold_bars <= self.time_stop_bars:
            raise ValueError(
                f"max_hold_bars ({self.max_hold_bars}) must exceed "
                f"time_stop_bars ({self.time_stop_bars}); otherwise the "
                f"max-hold cap would pre-empt the time stop")
        if self.cooldown_bars < 0:
            raise ValueError("cooldown_bars must be >= 0")
        if not 0.0 < self.stop_unresolved_frac:
            raise ValueError("stop_unresolved_frac must be positive")
        if self.baseline_days < 1:
            raise ValueError("baseline_days must be >= 1")

    # ---- derived geometry ------------------------------------------------

    @property
    def time_stop_bars(self):
        """tau * donchian_period. Only tau is sweepable."""
        return int(round(self.tau * self.donchian_period))

    @property
    def max_hold_bars(self):
        """2 * donchian_period. NOT independently sweepable."""
        return 2 * self.donchian_period

    @property
    def threshold_r(self):
        """Checkpoint threshold in R, SOLVED from phi -- never supplied.

        phi = (threshold_R / target_R) / (time_stop_bars / max_hold_bars)
          => threshold_R = phi * target_R * time_stop_bars / max_hold_bars

        With target_R=2, time_stop_bars=20, max_hold_bars=40 and phi=1.0 this
        gives exactly +1R -- the original value, now for a reason.
        """
        return (self.phi * self.target_r_multiple
                * self.time_stop_bars / self.max_hold_bars)

    # ---- derived stop floor ---------------------------------------------

    def haircut_bps(self, symbol):
        if symbol not in self.stop_haircut_bps:
            raise KeyError(f"no stop haircut configured for {symbol}")
        return self.stop_haircut_bps[symbol]

    def c_roundtrip(self, symbol):
        """Round-trip cost on the STOP path, as a fraction of price.

        Entry taker + stop taker + entry slippage + stop-market haircut. The
        haircut applies on the stop leg only; entry slippage is deliberately 0
        (the 1m-close fill convention absorbs latency). Charging the haircut on
        both legs would overstate the floor by ~0.05-0.10pp -- see report 07
        section 7.5.
        """
        return (2 * self.taker_fee
                + self.entry_slippage_bps / 10_000.0
                + self.haircut_bps(symbol) / 10_000.0)

    def leverage_term(self):
        """risk_usd / (E * L_max). Nowhere near binding at present values.

        Kept in the formula so that a future downward revision of n_cost cannot
        silently make it load-bearing without anyone noticing.
        """
        return self.risk_usd / (self.equity_usd * self.max_leverage)

    def stop_min_pct(self, symbol):
        """DERIVED floor: max(N_cost * c_roundtrip, risk_usd / (E * L_max)).

        Per-symbol because its INPUTS are per-symbol (the haircut), not because
        it was tuned per symbol. n_cost is the shared parameter.
        """
        return max(self.n_cost * self.c_roundtrip(symbol), self.leverage_term())


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


ATR, FLOOR, CAP = "atr", "floor", "cap"


def stop_geometry(entry, atr, direction, cfg, tick, symbol):
    """Stop price and which mechanism set it.

    Returns (stop_price, mechanism) with mechanism in {atr, floor, cap}. The
    mechanism is decided on the RAW distance before rounding, so a tick-level
    rounding artifact cannot relabel an ATR stop as a floor stop.
    """
    raw = cfg.stop_atr_mult * atr
    lo = cfg.stop_min_pct(symbol) * entry
    hi = cfg.stop_max_pct * entry
    if raw < lo:
        dist, mech = lo, FLOOR
    elif raw > hi:
        dist, mech = hi, CAP
    else:
        dist, mech = raw, ATR
    price = entry - dist if direction == LONG else entry + dist
    # Round the stop AWAY from entry so rounding never tightens the risk.
    return round_to_tick(price, tick, "down" if direction == LONG else "up"), mech


def stop_price(entry, atr, direction, cfg, tick, symbol):
    """stop_atr_mult * ATR, floored at the DERIVED floor, capped at the cap."""
    return stop_geometry(entry, atr, direction, cfg, tick, symbol)[0]


def solve_price_for_net(entry, qty, direction, cfg, tick, net_pnl,
                        exit_fee_rate):
    """Price at which net P&L equals `net_pnl` after entry taker + exit fee.

    Long, with X the exit price and P the entry fill:
        net = q*(X - P) - q*P*f_in - q*X*f_out
    Solving for X:
        X = ( net/q + P*(1 + f_in) ) / (1 - f_out)

    Always rounds AWAY from the position, so a level is never claimed at a
    price that would deliver less than `net_pnl`.
    """
    if qty <= 0:
        raise ValueError("qty must be positive")
    if direction == LONG:
        raw = (net_pnl / qty + entry * (1 + cfg.taker_fee)) / (1 - exit_fee_rate)
        return round_to_tick(raw, tick, "up")
    raw = (entry * (1 - cfg.taker_fee) - net_pnl / qty) / (1 + exit_fee_rate)
    return round_to_tick(raw, tick, "down")


def solve_target(entry, qty, direction, cfg, tick):
    """Take-profit price: net +target_r_multiple * R, exiting maker.

    "2 x stop distance" is NOT equivalent: it ignores that the winner pays two
    fee legs on a larger notional, so realised winners land short of 2R while
    losers still pay a full 1R.
    """
    return solve_price_for_net(
        entry, qty, direction, cfg, tick,
        net_pnl=cfg.target_r_multiple * cfg.risk_usd,
        exit_fee_rate=cfg.maker_fee)


def solve_r_level(entry, qty, direction, cfg, tick, r=None):
    """Price at which net P&L equals +r * R, exiting TAKER.

    This is the level the time-stop STATE CHECK tests, and it must be net of
    costs for the same reason the target is: a naive entry +/- stop_distance
    level is reached while the trade has NOT actually made 1R, so a
    losing-after-costs trade would survive the time stop.

    Taker is used because a trade continuing past the checkpoint will exit by
    stop, target or max-hold; taker is the conservative assumption of those.

    r defaults to cfg.threshold_r, which is itself derived from phi.
    """
    if r is None:
        r = cfg.threshold_r
    return solve_price_for_net(
        entry, qty, direction, cfg, tick,
        net_pnl=r * cfg.risk_usd,
        exit_fee_rate=cfg.taker_fee)


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


# --------------------------------------------------------------------------
# exchange minimum-quantity guard rail (A5, second job)
# --------------------------------------------------------------------------

RISK_RULE, LEVERAGE_CAP, MIN_QTY = "risk_rule", "leverage_cap", "min_qty"


def check_min_qty(qty, price, spec):
    """Is this order above the exchange minimum? Returns (ok, reason).

    Denominated in QUANTITY and NOTIONAL, deliberately -- not in percent. Per
    the Guard Rail Principle a guard rail must use a different unit from the
    mechanism it guards, and stop_max_pct already guards stop width in percent.
    Rejecting here is explicit and loud; the alternative is a silent rounding
    to zero that looks like a trade that never signalled.
    """
    if spec is None:
        return True, None
    if qty < spec.min_trade_num:
        return False, f"qty {qty:.10g} < minTradeNum {spec.min_trade_num:.10g}"
    if qty * price < spec.min_trade_usdt:
        return False, (f"notional {qty * price:.4f} < minTradeUSDT "
                       f"{spec.min_trade_usdt:.4g}")
    return True, None


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
