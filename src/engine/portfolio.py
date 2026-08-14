"""THE PORTFOLIO EXECUTION PATH. Built here, proven here, RUN AFTER POINT 4.

WHAT THIS IS. The one place that carries the frozen aggregate risk budget
(document 05 and its two amendments), the frozen exit resolution specification
(document 06 and its amendment) and report 28's exchange-real sizing. Nothing
else in this repository holds all three, and nothing else is permitted to
resolve an exit.

WHY IT IS NEW AND WHY `simulate.py` IS NOT PATCHED. That module carries its own
"one open position per symbol, no pyramiding" rule, its own margin refusal at a
placeholder ceiling report 26 section 12.1 measured as binding on 16.14% of
bars, and dollar-solved targets report 28 section 3 showed move when the
quantity is floored. Report 26 section 12.1 and report 28 section 13.5 both
record that it must be REPLACED rather than adapted. It is left alone: its tests
pin its behaviour and other work depends on it.

    THIS MODULE IS BUILT AND PROVEN. IT IS NOT RUN.

WHY NOT. The moment this resolves an exit against a real 1m bar, `exit_reason`
exists, and counting one value of it IS the win rate. The performance firewall
holds until the validation design is pre-registered at Point 4, because a
validation design chosen after seeing results is a design chosen to fit them.
The only real-data execution this step performs is the `max_hold` regression,
which evaluates no level and reads no 1m bar, and which reproduces report 26
exactly.

TWO MODES, AND THE SECOND CANNOT BE ENTERED BY ACCIDENT:

    max_hold   every position runs to its time exit. NO level is evaluated and
               no 1m bar is read. The regression path, and the default.
    full       levels are resolved on 1m per document 06. REQUIRES the explicit
               token below, whose value names what enabling it costs.

A BOOLEAN FLAG WOULD BE WRONG HERE. Someone flipping `evaluate_exits=True` has
not necessarily registered that they are spending the firewall; someone typing
FIREWALL_ACKNOWLEDGED_POINT_4_COMMITTED has, and the string is greppable across
the whole repository afterwards.

EVERY FROZEN VALUE IS READ, NEVER RESTATED. The budget, the risk unit, the
rotation table, the intra-bar order and the charging basis come from
`src/risk/budget.py`; the fill rules, the funding rate and the settlement count
come from `src/risk/exit_spec.py`; the lot steps and price ticks come from
`config/contracts_cache.json` through `contracts.py`; the geometry and the
reward-to-risk come from `sizing.py`. A test asserts NO numeric literal here
equals any of them. A restated constant is a constant that can drift.

THE TIME EXIT IS SUPPLIED, NOT RE-DERIVED, AND THAT IS DELIBERATE. Document 06
section 6.1 records that thesis section 5.3's `n = 3` is used as a settlement
INDEX in the exit rule and as a COUNT of settlements crossed in the funding
budget, that those are different quantities, and that they coincide only on 3
entry hours in 24. `FUNDING_SETTLEMENTS_CHARGED` is the COUNT. Re-deriving the
time exit from it here would conflate the two -- numerically invisibly, because
both are 3 -- so the max-hold bar arrives per candidate from the frozen calendar
function that owns the index, and this module never computes it.

PATH DEPENDENCE IS STRUCTURAL. In `full` mode whether a signal is taken depends
on when earlier positions exited, which depends on how they resolved. Document
05 section 6 pre-registered exactly this. There is therefore NO pre-computed
exit schedule, no two-pass design that resolves exits before entries across the
window, and no lookahead: the loop walks the hourly grid once, forward, and asks
for 1m bars only inside the hour it is standing on.

IT EMITS ROWS AND COMPUTES NO AGGREGATE. No win rate, no expectancy, no account
curve, no R-multiple summary, and NOTHING is counted by exit reason -- that
count is the firewalled quantity itself. The two flags document 06 requires be
counted are counted, because they are flags and not outcomes.
"""

import os
import sys
from dataclasses import dataclass, field

import pandas as pd

from src.risk import budget as rb
from src.risk import exit_spec as es
from src.timeframe import sealed_1m as sealed

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "src", "engine"))

import contracts  # noqa: E402
import costs  # noqa: E402
import sizing  # noqa: E402

LONG, SHORT = sizing.LONG, sizing.SHORT

# ---------------------------------------------------------------------------
# THE RULE. Every one of these is the frozen module's object, never a copy of
# its value. A test asserts identity, so specification and execution cannot
# drift apart.
# ---------------------------------------------------------------------------

BUDGET_USD = rb.MAX_AGGREGATE_OPEN_RISK_USD
UNIT_USD = rb.RISK_PER_TRADE_USD
MAX_SLOTS = rb.FULL_SIZE_POSITIONS
ROTATION_PERIOD_MS = rb.ROTATION_PERIOD_MS
ROTATION_MODULUS = rb.ROTATION_MODULUS
SYMBOL_ROTATION = rb.SYMBOL_ROTATION
BUDGET_CHARGES = rb.BUDGET_CHARGES
INTRA_BAR_ORDER = rb.INTRA_BAR_ORDER

#: The 1h bar period. THE SAME OBJECT the rotation advances on -- Rule A's
#: period IS the bar period, and its docstring says so, so reading it here
#: rather than declaring an hour keeps one definition instead of two.
BAR_MS = rb.ROTATION_PERIOD_MS

#: The 1m bar period, from the sealed loader.
MINUTE_MS = sealed.BAR_MS

FUNDING_RATE = es.FUNDING_RATE_PER_SETTLEMENT
FUNDING_COUNT = es.FUNDING_SETTLEMENTS_CHARGED
REWARD_TO_RISK = sizing.REWARD_TO_RISK

MODE_MAX_HOLD = "max_hold"
MODE_FULL = "full"

FIREWALL_TOKEN = "FIREWALL_ACKNOWLEDGED_POINT_4_COMMITTED"
"""The literal a caller must pass to resolve levels against 1m bars.

IT NAMES WHAT ENABLING IT COSTS. Point 4's validation design must be committed
first, because once an exit resolves, `exit_reason` exists and one count over it
is the win rate. The token is a string rather than a flag so that enabling
evaluation is a deliberate and greppable act."""

EXIT_STOP = "stop"
EXIT_TARGET = "target"
EXIT_TIME = "time"

SKIP_BUDGET_FULL = "BUDGET_FULL"
"""No budget remained when this signal arrived. It is SKIPPED -- not queued, not
deferred, not resized later -- exactly as document 05 section 3 specifies."""

SKIP_PARTIAL = "PARTIAL_ALLOCATION"
"""UNREACHABLE under Amendment 1 Rule B, and counted rather than assumed away:
the budget is an exact multiple of the unit, so an allocation is one unit or
nothing. A partial here means Rule B's nominal charging has been broken."""

POSITION_COLUMNS = (
    "symbol", "direction", "entry_ts", "entry_price",
    "stop_price", "target_price", "qty",
    "nominal_risk_usd", "realised_risk_usd",
    "funding_per_unit", "funding_usd",
    "exit_ts", "exit_price", "exit_reason",
    "both_levels_one_bar", "missing_1m_bars",
)

SKIP_COLUMNS = ("ts", "symbol", "direction", "reason")


class FirewallError(RuntimeError):
    """`full` mode was requested without the token. NEVER caught in this module.

    Degrading to `max_hold` would silently return a different population than
    the caller asked for; refusing is the only honest answer.
    """


# ---------------------------------------------------------------------------
# Rule A. Read from the frozen table, never restated.
# ---------------------------------------------------------------------------

def rotation(bar_open_ms):
    """Amendment 1 Rule A: the rotation value for a bar, from its OPEN time.

    DERIVED FROM THE TIMESTAMP, NOT A BAR INDEX. An index depends on where the
    series starts, so the same UTC bar would draw different priorities in a
    pooled and a fold-scoped run.
    """
    return (int(bar_open_ms) // ROTATION_PERIOD_MS) % ROTATION_MODULUS


def priority(bar_open_ms):
    """The symbol priority order for a bar, highest priority first."""
    return SYMBOL_ROTATION[rotation(bar_open_ms)]


def priority_rank(bar_open_ms, symbol):
    """A symbol's rank on a bar. 0 is first."""
    return priority(bar_open_ms).index(symbol)


# ---------------------------------------------------------------------------
# Funding. Document 06a, sections 3 and 4.
# ---------------------------------------------------------------------------

def funding_per_unit(entry_price):
    """`entry_price x rate x count`. THREE INPUTS AND ONE MULTIPLICATION.

    NOT BACK-SOLVED FROM ANY R-SHARE FIGURE. Document 06a section 4 records that
    document 06 section 6.1's 0.0200R is `rate x n / s` at the 1.50% FLOOR stop
    -- correct for comparison against the frozen funding budget, wrong as a
    construction rule -- and that the realised share of the risk unit is about
    0.0180R because the risk unit includes costs. At the floor stop the
    back-solve COINCIDES with the true term exactly, which is why the two are
    confusable; away from it they diverge by half. Neither figure appears here.

    IT DOES NOT DEPEND ON QUANTITY, which is what preserves report 28 section
    3.2's quantity invariance once the term enters the target solve.
    """
    return float(entry_price) * FUNDING_RATE * FUNDING_COUNT


def target_with_funding(entry_price, denominator, direction, cfg, price_tick,
                        funding_pu, reward_to_risk=REWARD_TO_RISK):
    """The target, solved PER UNIT with funding on BOTH sides. Document 06a E7.2.

        long   (T - entry) - [ entry f + T m + entry e + funding_pu ] = RR d
        short  (entry - T) - [ entry f + T m + entry e + funding_pu ] = RR d

    with `d` -- supplied by the caller -- ALSO including `funding_pu`. Solving:

        long   T = ( RR d + funding_pu + entry (1 + f + e) ) / (1 - m)
        short  T = ( entry (1 - f - e) - RR d - funding_pu ) / (1 + m)

    THE FAILURE THIS AVOIDS. Funding in `d` alone leaves the stop identity exact
    -- the denominator is both what sizes the position and what is lost at the
    stop, so a term added there is added to both sides at once -- while the
    target identity drifts to about 1.482R. The error raises no exception and
    the identity an implementer checks first keeps passing. A test asserts the
    defective form MISSES.

    THIS IS `sizing.target_price_on_tick` WITH ONE TERM ADDED IN TWO PLACES, and
    a test pins that with `funding_pu = 0` the two agree exactly, so the added
    term cannot become a second copy of the engine's algebra that drifts.

    QUANTITY APPEARS NOWHERE and cancels exactly, so the target price is
    invariant to the floored quantity -- report 28 section 3.2's central result,
    re-asserted with the new term present.
    """
    f = float(cfg.taker_fee)
    m = float(cfg.maker_fee)
    e = float(cfg.entry_slippage_bps) / 10_000.0
    rr = float(reward_to_risk)
    d = float(denominator)
    entry_price = float(entry_price)
    funding_pu = float(funding_pu)

    if direction == LONG:
        raw = (rr * d + funding_pu + entry_price * (1.0 + f + e)) / (1.0 - m)
        return costs.round_to_tick(raw, price_tick, "up")
    if direction == SHORT:
        raw = (entry_price * (1.0 - f - e) - rr * d - funding_pu) / (1.0 + m)
        return costs.round_to_tick(raw, price_tick, "down")
    raise ValueError("direction must be %r or %r, got %r"
                     % (LONG, SHORT, direction))


@dataclass(frozen=True)
class Sized:
    """One sized position. DUAL RISK RECORDING, report 28 section 7."""

    symbol: str
    direction: str
    entry_price: float
    price_tick: float
    stop_price: float
    target_price: float
    denominator: float
    funding_per_unit: float
    qty_unfloored: float
    qty: float
    nominal_risk_usd: float
    realised_risk_usd: float
    viable: bool
    reason: str


def size_position(entry_price, atr, direction, symbol, spec, cfg, price_tick,
                  allocation_usd):
    """Report 28's order of operations, with funding in the denominator.

        1. stop distance   max(ATR multiple, the floor fraction of entry)
        2. stop price      rounded to the tick, AWAY from entry
        3. effective       RECOMPUTED from the rounded stop
        4. denominator     the engine's own cost algebra PLUS `funding_pu`
        5. qty_unfloored   allocation / d
        6. qty             FLOORED to the lot step
        7. realised risk   qty x d
        8. target price    solved per unit with funding on both sides
        9. viability       two conditions; refusal is a SKIP

    THE GEOMETRY IS `sizing.py`'s AND IS NOT REIMPLEMENTED. Steps 1, 2, 3, 5, 6
    and 9 are its functions called directly; step 4 is its denominator with one
    term added; step 8 is the solve above. Nothing here retypes a multiplier, a
    floor fraction or a fee.

    `allocation_usd` IS WHAT THE BUDGET ALLOCATED -- Rule B's nominal unit --
    and never a realised figure. Rule B is explicit that wiring the budget to
    realised risk would make the inert partial branch reachable.
    """
    raw_distance = sizing.stop_distance(entry_price, atr)
    stop_price = sizing.stop_price_on_tick(entry_price, raw_distance, direction,
                                           price_tick)
    sizing.effective_stop_distance(entry_price, stop_price, direction)

    funding_pu = funding_per_unit(entry_price)
    denominator = sizing.per_unit_denominator(entry_price, stop_price,
                                              direction, cfg, symbol) + funding_pu

    qty_unfloored = float(allocation_usd) / denominator
    qty = sizing.floor_to_step(qty_unfloored, spec.qty_step)
    realised = qty * denominator

    target_price = target_with_funding(entry_price, denominator, direction, cfg,
                                       price_tick, funding_pu)
    viable, reason = sizing.viability(qty, entry_price, spec)

    return Sized(symbol=symbol, direction=direction,
                 entry_price=float(entry_price), price_tick=float(price_tick),
                 stop_price=stop_price, target_price=target_price,
                 denominator=denominator, funding_per_unit=funding_pu,
                 qty_unfloored=qty_unfloored, qty=qty,
                 nominal_risk_usd=float(allocation_usd),
                 realised_risk_usd=realised, viable=viable, reason=reason)


# ---------------------------------------------------------------------------
# 1m access. THROUGH THE SEALED LOADER AND NOWHERE ELSE.
# ---------------------------------------------------------------------------

class Bars1mCache:
    """1m bars, cached at ONE HOUR of one symbol -- the loop's own granularity.

    WHY A CACHE. Up to six concurrent positions, each needing up to 24 hours of
    1m bars, would otherwise re-read the same minutes once per position per
    hour.

    WHY THE GRANULARITY IS AN HOUR AND NOT A DAY. A day-chunked cache would read
    1m bars from AFTER the bar the loop is standing on. That is lookahead in the
    only sense that matters here -- data crossing the boundary before the
    decision does -- even though nothing would consult it. Keying on the hour
    makes the cache incapable of it, rather than merely not doing it.

    A CACHE THAT SERVES THE WRONG SYMBOL'S OR THE WRONG RANGE'S BARS IS A
    CORRECTNESS DEFECT THAT SURFACES AS A WRONG EXIT. A test asserts a hit
    returns data identical to a fresh load, on every symbol.

    `requests` RECORDS EVERY RANGE ASKED OF THE LOADER, so a test can assert no
    request ever reaches past the hour the loop was on.
    """

    def __init__(self, loader=None, derived_dir=None):
        self._loader = sealed.load if loader is None else loader
        self._derived_dir = derived_dir
        self._frames = {}
        self.requests = []
        self.hits = 0
        self.misses = 0

    def hour(self, symbol, bar_open_ms):
        """The 1m bars of `[bar_open, bar_open + 1h)` for `symbol`."""
        key = (str(symbol), int(bar_open_ms))
        if key in self._frames:
            self.hits += 1
            return self._frames[key]
        self.misses += 1
        lo = int(bar_open_ms)
        hi = lo + BAR_MS
        self.requests.append((str(symbol), lo, hi))
        if self._derived_dir is None:
            frame = self._loader(symbol, lo, hi)
        else:
            frame = self._loader(symbol, lo, hi, derived_dir=self._derived_dir)
        self._frames[key] = frame
        return frame

    def release(self, before_ms):
        """Drop cached hours that ended before `before_ms`. Bounded memory."""
        stale = [k for k in self._frames if k[1] + BAR_MS <= int(before_ms)]
        for key in stale:
            del self._frames[key]


# ---------------------------------------------------------------------------
# The open book.
# ---------------------------------------------------------------------------

@dataclass
class Open:
    """One open position, and the state its resolution accumulates."""

    sized: Sized
    entry_ts: int
    entry_instant: int
    max_hold_bar_ts: int
    max_hold_close_ms: int
    cursor_ms: int
    missing_1m_bars: int = 0
    both_levels_one_bar: bool = False
    last_close: float = float("nan")
    exit_ts: int = -1
    exit_price: float = float("nan")
    exit_reason: str = ""

    @property
    def resolved(self):
        return self.exit_reason != ""


def _fills(row, sized, price_tick):
    """(stop_fills, target_fills) for one 1m bar. Document 06 E2 and E3.

    E2 -- THE STOP IS A CONDITIONAL MARKET ORDER, so a TOUCH fills it and the
    comparison is INCLUSIVE: a market order triggered at the level fires at the
    level, because a market order does not rest and has no queue to be behind.

    E3 -- THE TARGET IS A RESTING MAKER LIMIT ORDER, so it fills only on a
    TRADE-THROUGH BY ONE TICK. Price printing exactly at a resting limit is
    evidence the level was reached, NOT that our order filled -- it may have
    filled against the queue ahead of us. One tick because the tick is the
    smallest increment that exists and is therefore the only margin that is not
    a tunable parameter entering a pre-registration.

    THE TICK IS RESOLVED PER TIMESTAMP, not per symbol: report 28 section 10
    records SOLUSDT's tick changing inside the measurement window.
    """
    high = float(row["high"])
    low = float(row["low"])
    if sized.direction == LONG:
        return (low <= sized.stop_price,
                high >= sized.target_price + price_tick)
    return (high >= sized.stop_price,
            low <= sized.target_price - price_tick)


def _advance(position, frame, window_start, window_end, cfg, tick_schedule,
             is_max_hold_bar):
    """Walk one open position through the 1m bars of `[window_start, window_end)`.

    MISSING BARS ARE FLAGGED AND COUNTED, never silently absorbed -- document 06
    E8. A missing bar is not a price gap: a gap is something the market did, a
    hole is something the data does not know, so any fill convention over an
    absent minute records an event that may not have happened at a price nobody
    observed. The position resolves on the bars that EXIST.

    E4 -- when one 1m bar satisfies BOTH conditions the STOP is taken, and the
    trade is FLAGGED. At 1m the geometry that produced report 27's 10.21% at 1h
    makes this far rarer, but "far rarer" is not "specified", and an unspecified
    case is decided by whichever comparison the implementer wrote first.

    E5 -- on the bar carrying the time exit, the stop is evaluated across the
    WHOLE bar and the time exit only at its CLOSE. That is not a preference, it
    is what the two order types are: a resting conditional order fires the
    instant price touches it, while the time exit is an action taken at a close.
    """
    expected = max(0, (int(window_end) - int(window_start)) // MINUTE_MS)
    if len(frame):
        inside = frame[(frame["ts"] >= int(window_start))
                       & (frame["ts"] < int(window_end))]
    else:
        inside = frame
    position.missing_1m_bars += expected - len(inside)

    for row in inside.itertuples(index=False):
        bar_ts = int(row.ts)
        price_tick = tick_schedule.tick_at(bar_ts)
        stop_fills, target_fills = _fills(
            {"high": row.high, "low": row.low}, position.sized, price_tick)
        position.last_close = float(row.close)

        if stop_fills and target_fills:
            position.both_levels_one_bar = True
        if stop_fills:
            position.exit_ts = bar_ts
            position.exit_price = costs.stop_fill_price(
                position.sized.stop_price, position.sized.direction, cfg,
                position.sized.symbol, price_tick)
            position.exit_reason = EXIT_STOP
            position.cursor_ms = bar_ts + MINUTE_MS
            return position
        if target_fills:
            position.exit_ts = bar_ts
            position.exit_price = position.sized.target_price
            position.exit_reason = EXIT_TARGET
            position.cursor_ms = bar_ts + MINUTE_MS
            return position

    position.cursor_ms = int(window_end)

    if is_max_hold_bar:
        if position.last_close != position.last_close:
            raise ValueError(
                "%s: the position entered at %d reached its time exit with no "
                "observed 1m close anywhere in its open interval; there is no "
                "price to execute the market order at. %d 1m bars are missing."
                % (position.sized.symbol, position.entry_instant,
                   position.missing_1m_bars))
        position.exit_ts = int(window_end) - MINUTE_MS
        position.exit_price = position.last_close
        position.exit_reason = EXIT_TIME
    return position


# ---------------------------------------------------------------------------
# The run.
# ---------------------------------------------------------------------------

def _hourly_grid(lo_ms, hi_ms):
    return list(range(int(lo_ms), int(hi_ms) + BAR_MS, BAR_MS))


def run(candidates, cfg, specs=None, ticks=None, mode=MODE_MAX_HOLD,
        firewall_token=None, cache=None, derived_dir=None):
    """One continuous forward pass over the hourly grid. Document 05b Rule C.

    THE LOOP, PER 1h BAR, IN THIS ORDER:

      1. EXITS. Every position whose exit falls at or before this bar closes,
         and each returns the NOMINAL risk unit to the budget. In `full` mode
         resolution happens here, one hour at a time, against the 1m bars of
         THIS hour only.
      2. ENTRIES. This bar's signals are evaluated against the remaining budget
         in the priority order Rule A gives for THIS bar.

    EXITS BEFORE ENTRIES, AND THE SAME UNIT MAY FUND BOTH AT ONE CLOSE. Under
    report 24 section 5.3's half-open convention the closing position's last
    open bar is X and the opening position's first is X+1, so the two never
    overlap and no bar of the occupancy timeline carries both. Evaluating
    entries first would model a sequence that cannot occur live and would
    inflate the skip rate by an artefact of loop order.

    ONE PASS, FORWARD ONLY. The grid is walked once in ascending order, the
    candidate frame is consumed by a pointer that only advances, and in `full`
    mode no 1m bar outside the current hour is ever requested. There is no
    pre-computed exit schedule and no second pass: under real exits the traded
    population is a function of realised outcomes, which document 05 section 6
    pre-registered and which makes any two-pass design wrong rather than merely
    slower.

    THE BUDGET DOES NOT RESET AT A FOLD BOUNDARY. It is an account property and
    it is continuous over the window.
    """
    if mode not in (MODE_MAX_HOLD, MODE_FULL):
        raise ValueError("mode must be %r or %r, got %r"
                         % (MODE_MAX_HOLD, MODE_FULL, mode))
    if mode == MODE_FULL and firewall_token != FIREWALL_TOKEN:
        raise FirewallError(
            "%r mode resolves stops and targets against 1m bars. Once it runs, "
            "`exit_reason` exists and one count over it IS the win rate, which "
            "the performance firewall holds until the validation design is "
            "pre-registered at Point 4. Pass firewall_token=%r to acknowledge "
            "that Point 4 is committed and that this call spends the firewall."
            % (MODE_FULL, FIREWALL_TOKEN))

    specs = sizing.load_symbol_specs() if specs is None else specs
    ticks = sizing.load_tick_schedules() if ticks is None else ticks
    if mode == MODE_FULL and cache is None:
        cache = Bars1mCache(derived_dir=derived_dir)

    frame = candidates.reset_index(drop=True)
    if not len(frame):
        return _empty_result(mode)

    ts = [int(v) for v in frame["ts"]]
    symbol = list(frame["symbol"])
    direction = list(frame["direction"])
    entry_price = [float(v) for v in frame["entry_price"]]
    atr = [float(v) for v in frame["atr"]]
    entry_close = [int(v) for v in frame["entry_close_ms"]]
    exit_bar = [int(v) for v in frame["exit_bar_ts"]]
    exit_close = [int(v) for v in frame["exit_close_ms"]]

    order = sorted(range(len(frame)),
                   key=lambda i: (ts[i], priority_rank(ts[i], symbol[i])))

    charged = 0.0
    partial_allocations = 0
    book = []
    closed = []
    skips = []

    cursor = 0
    grid = _hourly_grid(min(ts), max(exit_bar))
    for bar_ts in grid:
        bar_end = bar_ts + BAR_MS

        # --- 1. EXITS ------------------------------------------------------
        still_open = []
        for position in book:
            if mode == MODE_MAX_HOLD:
                if position.max_hold_bar_ts <= bar_ts:
                    position.exit_ts = position.max_hold_bar_ts
                    position.exit_price = float("nan")
                    position.exit_reason = EXIT_TIME
            else:
                window_start = max(position.cursor_ms, bar_ts)
                if window_start < bar_end:
                    bars = cache.hour(position.sized.symbol, bar_ts)
                    _advance(position, bars, window_start, bar_end, cfg,
                             ticks[position.sized.symbol],
                             is_max_hold_bar=(position.max_hold_bar_ts == bar_ts))
            if position.resolved:
                charged -= UNIT_USD
                closed.append(position)
            else:
                still_open.append(position)
        book = still_open
        if cache is not None:
            cache.release(bar_ts)

        # --- 2. ENTRIES ----------------------------------------------------
        while cursor < len(order) and ts[order[cursor]] == bar_ts:
            i = order[cursor]
            cursor += 1
            remaining = BUDGET_USD - charged
            if remaining <= 0.0:
                skips.append((bar_ts, symbol[i], direction[i],
                              SKIP_BUDGET_FULL))
                continue
            allocation = min(UNIT_USD, remaining)
            if allocation != UNIT_USD:
                partial_allocations += 1
                skips.append((bar_ts, symbol[i], direction[i], SKIP_PARTIAL))
                continue

            price_tick = ticks[symbol[i]].tick_at(entry_close[i])
            sized = size_position(entry_price[i], atr[i], direction[i],
                                  symbol[i], specs[symbol[i]], cfg, price_tick,
                                  allocation)
            if not sized.viable:
                skips.append((bar_ts, symbol[i], direction[i], sized.reason))
                continue

            charged += UNIT_USD
            book.append(Open(
                sized=sized, entry_ts=ts[i], entry_instant=entry_close[i],
                max_hold_bar_ts=exit_bar[i], max_hold_close_ms=exit_close[i],
                cursor_ms=entry_close[i]))

    if book:
        raise ValueError(
            "%d position(s) were still open when the grid ended; the grid must "
            "extend to the last max-hold bar" % len(book))
    if cursor != len(order):
        raise ValueError(
            "%d candidate(s) were never evaluated; a signal bar fell outside "
            "the grid" % (len(order) - cursor))

    return _result(closed, skips, partial_allocations, mode)


def _row(position):
    sized = position.sized
    return {
        "symbol": sized.symbol,
        "direction": sized.direction,
        "entry_ts": position.entry_ts,
        "entry_price": sized.entry_price,
        "stop_price": sized.stop_price,
        "target_price": sized.target_price,
        "qty": sized.qty,
        "nominal_risk_usd": sized.nominal_risk_usd,
        "realised_risk_usd": sized.realised_risk_usd,
        "funding_per_unit": sized.funding_per_unit,
        "funding_usd": sized.funding_per_unit * sized.qty,
        "exit_ts": position.exit_ts,
        "exit_price": position.exit_price,
        "exit_reason": position.exit_reason,
        "both_levels_one_bar": position.both_levels_one_bar,
        "missing_1m_bars": position.missing_1m_bars,
    }


def _result(closed, skips, partial_allocations, mode):
    """Rows. NOTHING IS AGGREGATED BY EXIT REASON.

    The two counters below are over FLAGS, not over outcomes: document 06
    section 5.1 requires the intrabar-precedence count be reported and document
    06a section 5.3 requires the missing-bar flagged fraction be reported EVEN
    WHEN IT IS ZERO. Neither is a function of which exit a trade took.
    """
    positions = pd.DataFrame([_row(p) for p in closed],
                             columns=list(POSITION_COLUMNS))
    skipped = pd.DataFrame(list(skips), columns=list(SKIP_COLUMNS))
    return {
        "mode": mode,
        "positions": positions,
        "skips": skipped,
        "n_taken": int(len(positions)),
        "n_skipped": int(len(skipped)),
        "partial_allocations": int(partial_allocations),
        "both_levels_flagged": int(positions["both_levels_one_bar"].sum())
                               if len(positions) else 0,
        "missing_bar_flagged": int((positions["missing_1m_bars"] > 0).sum())
                               if len(positions) else 0,
        "missing_1m_bars_total": int(positions["missing_1m_bars"].sum())
                                 if len(positions) else 0,
    }


def _empty_result(mode):
    return _result([], [], 0, mode)
