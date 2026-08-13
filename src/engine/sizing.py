"""Exchange-real position sizing: lot flooring, price-space targets, viability.

WHAT THIS FIXES. The closing record section 6.1 established that `qty_step` is
parsed, stored, serialised and printed and NEVER READ: every backtest to date
sized in fractional quantities no exchange would accept. Report 24 section 2.2
measured the notional that misstates at 0.21% / 1.26% / 0.67% pooled and 9.21%
on the worst single position. This module makes sizing exchange-real.

THE SECOND DEFECT IS THE MORE CONSEQUENTIAL ONE AND IT IS THE REASON THIS MODULE
EXISTS AT ALL. Once quantity is floored, the realised risk of a position falls
BELOW the nominal risk unit. `costs.solve_target` solves for a DOLLAR amount --
`net = RR x risk_usd` -- so its answer depends on the quantity, and a floored
quantity therefore moves the target. A stop-out then no longer returns exactly
-1.0R and a target no longer returns exactly +1.5R, and the thesis's 40.0%
breakeven and 53.6% detectable-edge arithmetic stops describing the system.

    THE FIX: SOLVE THE TARGET PER UNIT, IN PRICE SPACE.

        long   (T - entry) - cost_at_target(T) = RR x d
        short  (entry - T) - cost_at_target(T) = RR x d

    with `d` the per-unit risk denominator. QUANTITY APPEARS ON NEITHER SIDE AND
    CANCELS EXACTLY, so the target price is INVARIANT to the quantity. That
    invariance is the central test of this module.

`costs.py` IS NOT MODIFIED AND MUST NOT BE. Reports 24, 26 and 27 all call
`position_size`, and changing it would silently invalidate three closed reports.
This module IMPORTS its cost algebra and reuses it verbatim: the per-unit
denominator is obtained by DIVIDING `risk_usd` BY `costs.position_size`, so the
algebra cannot drift from the engine's even in principle. Nothing here
reimplements a cost term.

NO LEVERAGE CHECK, DELIBERATELY. `costs.CostConfig.max_leverage` stays at 3.0
for the legacy paths whose tests pin it, and this module implements no leverage
refusal: report 26 section 12.1 established the value is an unmeasured
placeholder that would bind on 16.14% of bars and censor the population the
aggregate budget already governs. A test asserts the name appears nowhere here.

THE RISK PACKAGE IS NOT IMPORTED. Sizing is a function of (entry, stop
distance, risk_usd, symbol config) and the CALLER supplies the risk unit. This
keeps `src/engine` unwired from `src/risk`, which report 26's narrowed assertion
still enforces unconditionally for engine files -- and that assertion is a TEXT
search, so this file must not contain the dotted module path even in prose. A
test asserts the package is unreachable.

NO DATA ACCESS, NO I/O EXCEPT THE CONTRACT CACHE, NO GLOBAL STATE. Every
function is pure. The symbol specifications are READ from
`config/contracts_cache.json` -- report 25 section 2 cross-checked that file
against the live venue, twelve fields of twelve agreeing -- and a test asserts no
numeric literal here equals any quantity step or price tick.

NO EXIT IS EVALUATED ANYWHERE. Nothing in this module reads a bar, pairs a
position with a subsequent price, or asks whether a level was reached. It
computes prices and quantities and stops.
"""

import math
import os
import sys
from dataclasses import dataclass

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "src", "engine"))

import contracts  # noqa: E402
import costs  # noqa: E402

LONG, SHORT = costs.LONG, costs.SHORT

CACHE_PATH = os.path.join(ROOT, "config", "contracts_cache.json")

# ---------------------------------------------------------------------------
# FROZEN GEOMETRY. Transcribed from the thesis; not chosen here, not swept.
# ---------------------------------------------------------------------------

STOP_ATR_MULT = 2.25
"""Thesis section 5.1."""

STOP_FLOOR_FRACTION = 0.0150
"""Thesis section 5.1: the 1.50% cost-admissibility floor, as a fraction."""

REWARD_TO_RISK = 1.5
"""THE FROZEN REWARD-TO-RISK, thesis section 5.2, solved NET of costs.

SUPPLIED EXPLICITLY AND NEVER READ FROM THE CONFIG. `CostConfig` defaults its
reward multiple to 2.0 -- Point 4's 1:2 -- while the thesis freezes 1.5.
Amendment 1 section 3 records the divergence and report 27 section 3.2 is where
it first became load-bearing. A test asserts this value is 1.5 AND that it
differs from the engine default, so an inherited default fails rather than
passes."""

#: Reason codes for a position the venue would refuse. A refused position is a
#: SKIP: it is not sized down and not retried, degrading into the skip tail
#: exactly as document 05 section 3 specifies.
OK = "ok"
BELOW_MIN_QTY = "BELOW_MIN_QTY"
BELOW_MIN_NOTIONAL = "BELOW_MIN_NOTIONAL"


@dataclass(frozen=True)
class SymbolSpec:
    """Venue lot constraints for one symbol, READ from the contract cache.

    `min_trade_num` is carried separately from `qty_step` even though the two
    COINCIDE on all three symbols this project trades. They are different
    constraints at the venue and a future symbol could separate them; collapsing
    them here would hide that.
    """

    symbol: str
    qty_step: float
    min_trade_num: float
    min_trade_usdt: float


@dataclass(frozen=True)
class SizedPosition:
    """One sized position. DUAL RISK RECORDING IS MANDATORY, not derived.

    `nominal_risk_usd` is what the aggregate budget charges -- Amendment 1
    Rule B, which charges the nominal figure BEFORE flooring and never the
    realised one. `realised_risk_usd` is `qty x denominator`: the true 1.0R
    denominator for THIS trade, against which its R multiples are computed.

    BOTH ARE STORED. Neither is recomputed from the other at read time, because
    the two answer different questions and a reader who has only one of them
    cannot recover the other without knowing the flooring residue.
    """

    symbol: str
    direction: str
    entry_price: float
    atr: float
    price_tick: float
    qty_step: float

    stop_distance_raw: float
    stop_price: float
    stop_distance_effective: float
    floor_bound: bool

    denominator: float
    qty_unfloored: float
    qty: float

    nominal_risk_usd: float
    realised_risk_usd: float
    notional: float

    target_price: float
    target_distance: float

    tick_shift_stop: float
    tick_shift_target: float

    viable: bool
    reason: str


# ---------------------------------------------------------------------------
# The symbol specifications. READ, never retyped.
# ---------------------------------------------------------------------------

def load_symbol_specs(path=CACHE_PATH):
    """Lot constraints per symbol, from the committed contract cache.

    Report 25 section 2 cross-checked every one of these against the live venue
    -- twelve fields, twelve agreeing -- so the cache is the authority and this
    module reads it rather than restating it.
    """
    specs = contracts.load_order_specs(path)
    if not specs:
        raise ValueError("%s carries no order specs" % path)
    return {sym: SymbolSpec(symbol=sym,
                            qty_step=float(s.qty_step),
                            min_trade_num=float(s.min_trade_num),
                            min_trade_usdt=float(s.min_trade_usdt))
            for sym, s in specs.items()}


def load_tick_schedules(path=CACHE_PATH):
    """Piecewise-constant price tick per symbol, from the same cache.

    THE TICK IS A SCHEDULE, NOT A SCALAR. SOLUSDT moved from a 0.0001 grid to a
    0.001 grid inside the measurement window, so the caller must resolve it by
    BAR TIMESTAMP via `TickSchedule.tick_at`. A single tick per symbol would
    round two and a half years of SOL prices onto the wrong grid.
    """
    return contracts.load_cache(path)


# ---------------------------------------------------------------------------
# The pieces, in the order the sizing applies them.
# ---------------------------------------------------------------------------

def stop_distance(entry_price, atr, mult=STOP_ATR_MULT,
                  floor_fraction=STOP_FLOOR_FRACTION):
    """max(2.25 x ATR, 1.50% of entry). Thesis section 5.1, unchanged."""
    return max(mult * float(atr), floor_fraction * float(entry_price))


def floor_binds(entry_price, atr, mult=STOP_ATR_MULT,
                floor_fraction=STOP_FLOOR_FRACTION):
    """Did the floor -- not the volatility -- set the stop? STRICTLY below.

    Report 21's convention, so the stratification here is the same predicate
    reports 21, 24 and 26 stratified on.
    """
    return (mult * float(atr)) < (floor_fraction * float(entry_price))


def stop_price_on_tick(entry_price, distance, direction, price_tick):
    """The stop, rounded AWAY FROM ENTRY onto the price grid.

    THE DIRECTION IS THE REPOSITORY'S EXISTING CONVENTION, not a new choice:
    `costs.stop_geometry` rounds "down" for a long and "up" for a short with the
    comment "Round the stop AWAY from entry so rounding never tightens the
    risk", and `costs.solve_price_for_net` rounds targets the same way. This
    module follows it on both legs.

    THE ARGUMENT FOR THIS LEG. Rounding a stop away from entry makes it WIDER.
    A wider stop is not a larger loss: the quantity is solved from the ROUNDED
    stop, so the position simply gets smaller and the loss still caps at one
    risk unit. Rounding the other way would move the stop INSIDE the level the
    geometry was chosen for, which report 21's excursion check exists to
    prevent.
    """
    if direction == LONG:
        return costs.round_to_tick(entry_price - distance, price_tick, "down")
    if direction == SHORT:
        return costs.round_to_tick(entry_price + distance, price_tick, "up")
    raise ValueError("direction must be %r or %r, got %r"
                     % (LONG, SHORT, direction))


def effective_stop_distance(entry_price, stop, direction):
    """The distance implied by the ROUNDED stop price.

    STEP 3 OF THE ORDER OF OPERATIONS, AND IT IS NOT COSMETIC. Everything
    downstream -- the denominator, the quantity, the realised risk, the target --
    is computed from THIS distance and not from the pre-rounding one. A stop
    price that is not on a tick is not a stop price, so the distance that
    matters is the one the exchange would actually honour.
    """
    move = (entry_price - stop) if direction == LONG else (stop - entry_price)
    if move <= 0.0:
        raise ValueError("stop on the wrong side of entry: entry=%r stop=%r "
                         "direction=%r" % (entry_price, stop, direction))
    return move


def per_unit_denominator(entry_price, stop, direction, cfg, symbol):
    """`d`: the all-in per-unit loss if the stop is hit, in price units.

    REUSED FROM THE ENGINE RATHER THAN REIMPLEMENTED. `costs.position_size`
    returns `risk_usd / d`, so dividing the config's own risk unit by its answer
    recovers `d` exactly. The cost algebra therefore cannot drift from the
    engine's -- there is only one copy of it and it is `costs.py`'s.

    `d` is the price move PLUS both fee legs PLUS both slippage legs. Sizing on
    the move alone is the naive form that report 24 section 2.1 measured as 7.4%
    wrong.
    """
    qty_for_cfg = costs.position_size(entry_price, stop, direction, cfg, symbol)
    if qty_for_cfg <= 0.0:
        raise ValueError("non-positive quantity from the engine denominator")
    return float(cfg.risk_usd) / float(qty_for_cfg)


def floor_to_step(qty, qty_step):
    """FLOOR, never round, never ceil.

    Flooring is the ONLY direction that cannot push realised risk above the risk
    unit -- the closing record section 6.1 states it: "Floor is the only rounding
    direction that cannot breach the 1% rule; round-to-nearest and ceil both
    can."

    Integer-domain, for the reason `costs.round_to_tick` gives: dividing by a
    step like 0.0001 in binary floats leaves values such as 1.9999999999 that
    then truncate a whole step the wrong way.
    """
    if qty_step <= 0.0:
        raise ValueError("qty_step must be positive, got %r" % (qty_step,))
    q = float(qty) / float(qty_step)
    nearest = round(q)
    n = nearest if abs(q - nearest) < 1e-9 else math.floor(q)
    return max(0.0, round(n * float(qty_step), 12))


def target_price_on_tick(entry_price, denominator, direction, cfg, price_tick,
                         reward_to_risk=REWARD_TO_RISK):
    """The target, solved PER UNIT and rounded AWAY FROM ENTRY. THE CENTRAL FIX.

    THE CONDITION, per unit of quantity:

        long    (T - entry) - [ entry x f + T x m + entry x e ]  =  RR x d
        short   (entry - T) - [ entry x f + T x m + entry x e ]  =  RR x d

    with `f` the entry taker fee, `m` the exit MAKER fee, `e` the entry
    slippage, and `d` the per-unit denominator. Solving:

        long    T = ( RR d + entry (1 + f + e) ) / (1 - m)
        short   T = ( entry (1 - f - e) - RR d ) / (1 + m)

    QUANTITY APPEARS NOWHERE. It cancels exactly, which is the whole point: the
    target price is INVARIANT to the quantity, so flooring the quantity cannot
    move it. `costs.solve_target` solves for a DOLLAR amount and therefore does
    not have this property -- that is the defect, and this is the fix.

    THE EXIT LEG IS MAKER, NOT TAKER. Report 27 section 3.3 established this
    from the engine's own algebra. Using the taker fee would place the target
    further out and quietly change the reward the strategy is aiming at.

    ENTRY SLIPPAGE APPEARS ON BOTH SIDES. `d` includes it via
    `position_size`, so the target cost includes it too; the treatment is
    symmetric. At the frozen configuration `entry_slippage_bps` is 0, so this
    term moves no number today -- it is written for consistency rather than for
    effect, and `costs.solve_price_for_net` omits it for the same reason it
    never mattered.

    ROUNDED AWAY FROM ENTRY, following the repository convention. The argument
    for THIS leg is not the stop's: rounding a target away from entry makes it
    HARDER to reach and can only cost reward, never add it. The two legs are not
    symmetric and the report says so.
    """
    f = float(cfg.taker_fee)
    m = float(cfg.maker_fee)
    e = float(cfg.entry_slippage_bps) / 10_000.0
    rr = float(reward_to_risk)
    d = float(denominator)
    entry_price = float(entry_price)

    if direction == LONG:
        raw = (rr * d + entry_price * (1.0 + f + e)) / (1.0 - m)
        return costs.round_to_tick(raw, price_tick, "up")
    if direction == SHORT:
        raw = (entry_price * (1.0 - f - e) - rr * d) / (1.0 + m)
        return costs.round_to_tick(raw, price_tick, "down")
    raise ValueError("direction must be %r or %r, got %r"
                     % (LONG, SHORT, direction))


def viability(qty, entry_price, spec):
    """(viable, reason). Two conditions, both from the venue.

        qty > 0 and qty >= min_trade_num       flooring did not zero it
        qty x entry_price >= min_trade_usdt    the $5.00 minimum notional

    BOTH ARE UNREACHABLE AT THE FROZEN VALUES AND BOTH ARE IMPLEMENTED ANYWAY.
    Under the frozen budget the allocation is always exactly one $20.00 risk
    unit (Amendment 1 Rule B, confirmed on the real population by report 26
    section 6.1), so the notional is risk / (s + c) and report 24 section 6.5
    gives the smallest per-position notional over the whole window as $230 /
    $167 / $40 -- the smallest is eight times the $5.00 threshold.

    THEY ARE TREATED EXACTLY AS DOCUMENT 05 SECTION 4 TREATED THE INERT PARTIAL
    BRANCH: specified, documented as unreachable at present values, and carrying
    tests that exercise them at values where they ARE reachable. A dead branch
    with no test is `MAKER_NONFILL_COST_R` again -- a term invisible to all 545
    tests then in the suite because every one of them multiplied it by zero.

    A REFUSED POSITION IS NOT SIZED DOWN AND NOT RETRIED. It is a skip with a
    reason code.

    `min_trade_num` COINCIDES WITH `qty_step` on all three symbols this project
    trades, so the two quantity conditions are one condition here. They are
    written separately because they are separate constraints at the venue.
    """
    if qty <= 0.0 or qty < spec.min_trade_num:
        return False, BELOW_MIN_QTY
    if qty * float(entry_price) < spec.min_trade_usdt:
        return False, BELOW_MIN_NOTIONAL
    return True, OK


# ---------------------------------------------------------------------------
# The whole sizing, in one function, in the stated order.
# ---------------------------------------------------------------------------

def size(entry_price, atr, direction, symbol, spec, cfg, price_tick,
         risk_usd, reward_to_risk=REWARD_TO_RISK, mult=STOP_ATR_MULT,
         floor_fraction=STOP_FLOOR_FRACTION):
    """One sized position. THE ORDER OF OPERATIONS IS NOT COMMUTATIVE.

        1. stop distance   max(2.25 x ATR, 1.50% of entry)
        2. stop price      entry -/+ distance, ROUNDED TO THE TICK, away
        3. effective       RECOMPUTED from the rounded stop price
        4. denominator     the engine's own cost algebra, not the naive move
        5. qty_unfloored   risk_usd / d
        6. qty             FLOORED to the quantity step
        7. realised risk   qty x d
        8. target price    solved PER UNIT, rounded to the tick, away
        9. viability       two conditions, refusal is a skip

    `risk_usd` IS A PARAMETER. The caller supplies the risk unit; this module
    does not import `src/risk` and does not know what the budget is.
    """
    entry_price = float(entry_price)
    risk_usd = float(risk_usd)
    if entry_price <= 0.0:
        raise ValueError("entry price must be positive, got %r" % entry_price)
    if risk_usd <= 0.0:
        raise ValueError("risk_usd must be positive, got %r" % risk_usd)

    raw_distance = stop_distance(entry_price, atr, mult, floor_fraction)
    stop = stop_price_on_tick(entry_price, raw_distance, direction, price_tick)
    effective = effective_stop_distance(entry_price, stop, direction)

    denominator = per_unit_denominator(entry_price, stop, direction, cfg,
                                       symbol)
    qty_unfloored = risk_usd / denominator
    qty = floor_to_step(qty_unfloored, spec.qty_step)
    realised = qty * denominator

    target = target_price_on_tick(entry_price, denominator, direction, cfg,
                                  price_tick, reward_to_risk)
    target_distance = (target - entry_price) if direction == LONG else (
        entry_price - target)

    viable, reason = viability(qty, entry_price, spec)

    unrounded_stop = (entry_price - raw_distance) if direction == LONG else (
        entry_price + raw_distance)
    unrounded_target = _unrounded_target(entry_price, denominator, direction,
                                         cfg, reward_to_risk)

    return SizedPosition(
        symbol=symbol, direction=direction, entry_price=entry_price,
        atr=float(atr), price_tick=float(price_tick),
        qty_step=float(spec.qty_step),
        stop_distance_raw=raw_distance, stop_price=stop,
        stop_distance_effective=effective,
        floor_bound=bool(floor_binds(entry_price, atr, mult, floor_fraction)),
        denominator=denominator, qty_unfloored=qty_unfloored, qty=qty,
        nominal_risk_usd=risk_usd, realised_risk_usd=realised,
        notional=qty * entry_price,
        target_price=target, target_distance=target_distance,
        tick_shift_stop=abs(stop - unrounded_stop),
        tick_shift_target=abs(target - unrounded_target),
        viable=viable, reason=reason)


def _unrounded_target(entry_price, denominator, direction, cfg,
                      reward_to_risk=REWARD_TO_RISK):
    """The target before tick rounding. Used only to measure the tick shift."""
    f = float(cfg.taker_fee)
    m = float(cfg.maker_fee)
    e = float(cfg.entry_slippage_bps) / 10_000.0
    rr = float(reward_to_risk)
    if direction == LONG:
        return (rr * denominator + entry_price * (1.0 + f + e)) / (1.0 - m)
    return (entry_price * (1.0 - f - e) - rr * denominator) / (1.0 + m)


# ---------------------------------------------------------------------------
# THE RECORDED CARVE-OUT. Synthetic reference only.
# ---------------------------------------------------------------------------

def net_proceeds_per_unit(entry_price, exit_price, direction, cfg,
                          exit_fee_rate, exit_haircut_fraction=0.0):
    """Per-unit net proceeds of a round trip at a GIVEN exit price.

    THIS IS THE MODULE'S ONE RECORDED CARVE-OUT AND IT IS RECORDED IN THE REPORT.
    Verifying that the stop returns exactly -1.0 realised risk units and the
    target exactly +1.5 requires computing proceeds at a price, which touches
    outcome-adjacent ground the performance firewall otherwise keeps shut.

    IT IS PERMITTED ONLY UNDER THREE CONDITIONS, ALL ASSERTED BY TEST:
      * SYNTHETIC REFERENCE INPUTS ONLY. It is never called on a real signal, a
        real bar or a real position -- the only callers are the tests and they
        pass hand-chosen values.
      * EXACTLY ONE FUNCTION. No other function in this module or in the drag
        measurement computes proceeds at a price; asserted over the AST.
      * THE BLANKET NAME BAN OTHERWISE INTACT. The twelve-name guard is not
        relaxed for this function or for anything else.

    IT DOES NOT ASK WHETHER A PRICE WAS REACHED. The exit price is supplied by
    the caller; nothing here reads a bar or compares a level to one. It is
    arithmetic on two prices.
    """
    entry_price = float(entry_price)
    exit_price = float(exit_price)
    f = float(cfg.taker_fee)
    e = float(cfg.entry_slippage_bps) / 10_000.0
    h = float(exit_haircut_fraction)
    if direction == LONG:
        gross = exit_price - entry_price
        return gross - entry_price * f - exit_price * exit_fee_rate \
            - entry_price * e - exit_price * h
    if direction == SHORT:
        gross = entry_price - exit_price
        return gross - entry_price * f - exit_price * exit_fee_rate \
            - entry_price * e - exit_price * h
    raise ValueError("direction must be %r or %r, got %r"
                     % (LONG, SHORT, direction))
