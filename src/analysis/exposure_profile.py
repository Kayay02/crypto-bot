"""Maximum-hold exposure of the frozen thesis: how much is open at once.

WHAT IS BEING ASKED. The closing record section 3.1 concluded that leverage
"does not bind at present values" from 20 / (2000 x 3) = 0.333%. That is a
SINGLE-POSITION check: it says what the tightest stop ONE trade could carry is,
and nothing whatever about what is open when several trades overlap. The frozen
time exit holds a position to the third funding settlement after entry --
16 to 24 hours at 1h -- across three symbols, so overlap is the expected case
rather than the exceptional one. Its frequency has never been measured. This
module measures it.

THE ASSUMPTION THIS RESTS ON, STATED ONCE. Every position runs the FULL maximum
hold. No stop is evaluated, no target is evaluated, no exit of any kind is
tested. A position is opened at the close of its signal bar and is carried,
unconditionally, to the close of the bar preceding the third funding settlement
after that instant. THE RESULT IS THEREFORE AN UPPER BOUND ON OCCUPANCY, and
that is the correct direction for a risk measurement: a real position that
stops out early frees its slot sooner, never later.

THREE SEPARATE REASONS EVERY FIGURE HERE IS AN UPPER BOUND, none of which
cancels the others:

  * MAX HOLD. No exit is evaluated, so no position ever leaves early.
  * UNQUANTISED SIZING. `position_size` returns a raw fractional quantity; the
    engine performs no lot-size rounding (closing record section 6.1). Flooring
    to the quantity step reduces EVERY quantity, so every notional here is at
    or above what an exchange would have accepted.
  * UNCAPPED CONCURRENCY. Every signal opens an additional position, including
    on a symbol that already has one open. No cap of any kind is applied --
    setting one is the next sub-point's job, and it cannot be set without this
    number.

NOTHING IS SWEPT AND NOTHING IS PROPOSED. Donchian-10, 1h, 2.25 x ATR(14) with
a 1.50% floor, n = 3 settlements: one configuration, all of it frozen upstream
and transcribed here. This step has no free parameter and produces no grid.

THE QUANTITY IS DERIVED FROM THE IMPLEMENTATION, NOT FROM A FORMULA. Position
size comes from `src/engine/costs.py::position_size` called directly with the
real symbol config, so the measurement reflects the fees and slippage the
system actually charges. The cost tolerance is a BUDGET CEILING and is not a
cost: nothing here computes a cost from it.

THE PERFORMANCE FIREWALL IS ARMED. Counts, timestamps, notional and occupancy
are bar-level and signal-level quantities of the same admissible class as
report 21's signal counts. No trade outcome is computed, inspected or estimated;
no stop or target is evaluated; and NO BAR AFTER THE ENTRY BAR IS READ FOR ANY
PURPOSE -- the maximum-hold exit is located on the FUNDING CALENDAR, which is
arithmetic on a timestamp and reads no data at all. A test walks this module's
AST and refuses any performance name as an identifier or a string literal.

THE HOLDOUT IS SEALED. The window is inherited whole from
`src/timeframe/resample.py` by way of `sweep_population`; this module defines no
window constant of its own and a test asserts it defines none. The position
table passes back through `resample.assert_sealed`, so no position can be opened
on a sealed bar. Exit timestamps are CALENDAR VALUES and a late-window entry's
exit falls past the window end; the occupancy timeline is clipped to the
measured window and the clipped positions are counted and reported.

BAR TIMESTAMPS ARE OPEN TIMES. `src/data/backfill_bitget.py` records the venue
convention -- "Timestamps are the bar's OPEN time" -- and every layer above it
keeps it: `resample.resample` labels each bucket with `ts - ts % period_ms`, its
START, and `schedule.LAST_BAR_OFFSET_MS` puts the last 15m bar of a day at
23:45. So a 1h bar labelled T covers [T, T + 1h) and CLOSES at T + 1h. Entry
instant, settlement crossing and occupancy alignment all depend on this and all
use `bar_close_ms`.

NO OPEN PRICE. `open_synth` is dropped at the load boundary by the loader reused
here. The trigger needs high, low and close; sizing needs the close.
"""

import os
import sys

import numpy as np
import pandas as pd

from src.analysis import sweep_population as sp
from src.timeframe import resample as rs

# The engine's own sizing, imported the way src/analysis/dispersion.py already
# imports it; src/engine is not a package. NOTHING here reimplements a quantity
# the engine computes.
sys.path.insert(0, os.path.join(rs.ROOT, "src", "engine"))

import contracts  # noqa: E402
import costs  # noqa: E402


# ---------------------------------------------------------------------------
# FROZEN INPUTS. Transcribed, not chosen here. Not swept. A test pins each one.
# ---------------------------------------------------------------------------

TIMEFRAME = sp.TIMEFRAME
DONCHIAN_PERIOD = sp.DONCHIAN_PERIOD
ATR_PERIOD = sp.ATR_PERIOD
STOP_ATR_MULT = sp.STOP_ATR_MULT
STOP_FLOOR_PCT = sp.STOP_FLOOR_PCT
"""Every one of these is READ FROM report 21's module rather than restated, so
a divergence between the two reports is impossible by construction."""

BAR_MS = 3_600_000
"""One 1h bar, in milliseconds. The timeframe is frozen at 1h."""

FUNDING_INTERVAL_MS = 8 * BAR_MS
"""Bitget USDT-M settles funding every 8 hours at 00:00, 08:00 and 16:00 UTC.
The Unix epoch begins at 00:00:00Z, and 8h divides a day exactly, so the
settlement instants are precisely the multiples of this interval -- no offset
term is needed and none is accepted. A settlement schedule carrying an origin
would be one whose alignment could drift between callers."""

SETTLEMENTS_TO_CROSS = 3
"""n = 3, thesis 5.3. DENOMINATED IN SETTLEMENTS, NOT BARS. Derived there from
a 0.022R funding budget at an assumed 0.01% per 8h and the 1.50% floor:
0.022 x 0.0150 / 0.0001 = 3.3, ROUNDED DOWN. Not revisited here."""

HOLD_MIN_MS = 16 * BAR_MS
HOLD_MAX_MS = 24 * BAR_MS
"""The elapsed hold the settlement rule must produce, thesis 5.3. These are an
ASSERTED CONSEQUENCE of the rule, not an input to it: nothing below computes an
exit from them. `assert_hold_admissible` refuses any hold outside the band."""

CAPITAL_USD = 2000.0
"""Account size, transcribed from the engine config's own account constant. It
enters ONE quantity -- required leverage = notional / capital -- and nothing
else. A test pins it against the engine rather than trusting the transcription.
It is spelled out here rather than read through the config attribute because
the firewall guard refuses that attribute's name as an identifier."""

CONCURRENCY_CAP = None
"""NO CAP. Stated as a constant so the absence is a recorded decision rather
than an omission. Every signal opens an additional position, including on a
symbol that already carries one. Setting a cap is sub-point 5.2's job and it
cannot be set before this measurement exists."""

PERCENTILES = (50, 90, 95, 99)
"""Median, P90, P95, P99. `distribution` adds min and max; `summary` adds the
mean. Reported for occupancy and notional alike."""

LONG, SHORT = sp.LONG, sp.SHORT

#: One percentile-summary implementation in the project, not four. Report 20's
#: is already guarded by hand-checked tests and report 21 reuses it too.
distribution = sp.distribution


# ---------------------------------------------------------------------------
# The engine config. Supplied, never invented.
# ---------------------------------------------------------------------------

_UNUSED_SIZING_PARAMS = dict(stop_max_pct=0.035, rvol_threshold=1.5,
                             baseline_days=20)
"""Three of the four parameters that have NO DEFAULT after Point 3R. None of
them enters `position_size`, which reads only the taker fee, the entry slippage,
the per-symbol stop haircut and the risk unit. They are supplied purely to
construct the object and are NEVER read; a test varies all three and asserts
every quantity produced here is unchanged, so this cannot become a channel
through which a strategy parameter reaches the exposure figures. The fourth,
`stop_atr_mult`, IS supplied at its frozen thesis value -- and is also not read,
because the stop distance is computed from the thesis rule below rather than
from `stop_geometry`, whose floor is the engine's DERIVED per-symbol floor and
not the thesis's 1.50%."""


def cost_config(**kw):
    """The engine `CostConfig` this measurement sizes against.

    THE FLOOR DIVERGENCE, RECORDED RATHER THAN RESOLVED. `costs.stop_geometry`
    floors the stop at `cfg.stop_min_pct(symbol)` -- a DERIVED figure, 1.020%
    for BTC and ETH and 1.320% for SOL -- while the thesis freezes a 1.50%
    floor from report 18. They are different numbers and the thesis wins here:
    `stop_distance` below implements the thesis rule. `stop_geometry` is
    deliberately NOT called. Only `position_size` is, and it takes the stop as
    an argument rather than deriving it.
    """
    p = dict(_UNUSED_SIZING_PARAMS)
    p.update(kw)
    return costs.CostConfig(stop_atr_mult=STOP_ATR_MULT, **p)


def config_table(cfg=None, symbols=rs.SYMBOLS):
    """Every input `position_size` reads, on the record, per symbol.

    `qty_step` is included and is NOT USED by anything here. It is reported
    because the closing record section 6.1 found that the engine parses, stores,
    serialises and prints it and never applies it -- so every quantity below is
    unquantised, and the step is the size of the correction 5.3 will make.
    """
    cfg = cost_config() if cfg is None else cfg
    specs = contracts.load_order_specs()
    rows = []
    for sym in symbols:
        spec = specs.get(sym)
        rows.append({
            "symbol": sym,
            "taker_fee": float(cfg.taker_fee),
            "entry_slippage_bps": float(cfg.entry_slippage_bps),
            "stop_haircut_bps": float(cfg.haircut_bps(sym)),
            "risk_usd": float(cfg.risk_usd),
            "qty_step": None if spec is None else float(spec.qty_step),
            "min_trade_num": None if spec is None else float(spec.min_trade_num),
            "min_trade_usdt": None if spec is None else float(spec.min_trade_usdt),
        })
    return rows


# ---------------------------------------------------------------------------
# The funding calendar. Arithmetic on a timestamp; reads nothing.
# ---------------------------------------------------------------------------

def bar_close_ms(bar_ts):
    """The instant a bar labelled `bar_ts` CLOSES.

    Bar timestamps are OPEN times (module docstring), so a 1h bar labelled T
    covers [T, T + 1h) and closes at T + 1h. ENTRY IS AT THIS INSTANT: the
    thesis freezes entry at the close of the signal bar, as a taker.
    """
    return np.asarray(bar_ts, dtype=np.int64) + BAR_MS


def nth_settlement_after(instant_ms, n=SETTLEMENTS_TO_CROSS):
    """The `n`th funding settlement STRICTLY AFTER `instant_ms`.

    STRICTLY. An instant landing exactly ON a settlement does not count that
    settlement as being after it, so an entry at exactly 16:00Z looks forward to
    00:00, 08:00 and 16:00 of the following day. Floor-then-add implements the
    strictness without a comparison: for an instant on the grid, `// interval`
    lands on that settlement and `+ n` steps past it; for one off the grid it
    lands on the previous settlement and `+ n` steps to the nth following one.
    """
    x = np.asarray(instant_ms, dtype=np.int64)
    return (x // FUNDING_INTERVAL_MS + n) * FUNDING_INTERVAL_MS


def max_hold_exit(signal_bar_ts, n=SETTLEMENTS_TO_CROSS):
    """(exit_bar_ts, exit_close_ms, hold_ms) for a position opened at a signal.

    THE RULE, thesis 5.3: closed at the CLOSE OF THE BAR PRECEDING THE THIRD
    FUNDING SETTLEMENT after the entry instant.

    THE BAR PRECEDING A SETTLEMENT is the bar whose OPEN is the last bar-open
    before it -- at 1h, `settlement - 1h` -- and that bar CLOSES at the
    settlement instant. Bars are labelled by open time, so "the bar preceding
    16:00" is the bar labelled 15:00, not the bar labelled 14:00. This is the
    reading that makes the thesis's own stated 24-hour upper bound attainable:
    an entry at exactly a settlement instant holds for exactly 24 hours. Under
    the other reading the maximum would be 23 and the frozen band's top edge
    could never be reached.

    ELAPSED HOLD IS A CONSEQUENCE, NOT A PARAMETER. At 1h every entry instant
    lands on an hour boundary, so the hold takes one of eight values from 17 to
    24 hours, inside the frozen 16-24 band. Nothing here is denominated in bars.
    """
    entry_close = bar_close_ms(signal_bar_ts)
    settlement = nth_settlement_after(entry_close, n)
    exit_close = settlement
    exit_bar = exit_close - BAR_MS
    return exit_bar, exit_close, exit_close - entry_close


def assert_hold_admissible(hold_ms):
    """Refuse any hold outside the frozen 16-24 hour band.

    A settlement bug is not the kind that raises: an off-by-one in the
    settlement index produces holds of 8 or 32 hours, which are perfectly
    plausible numbers that no occupancy figure would look wrong for. This is
    the check that makes them loud.
    """
    x = np.asarray(hold_ms, dtype=np.int64)
    if not len(x):
        return x
    bad = (x < HOLD_MIN_MS) | (x > HOLD_MAX_MS)
    if bool(bad.any()):
        i = int(np.argmax(bad))
        raise ValueError(
            "hold of %.4f hours falls outside the frozen 16-24 hour band "
            "(offending hold_ms=%d); the settlement logic is wrong, not the "
            "band" % (x[i] / BAR_MS, int(x[i])))
    return x


# ---------------------------------------------------------------------------
# Stop distance and size. The thesis rule, then the engine.
# ---------------------------------------------------------------------------

def stop_distance(entry_price, atr, mult=STOP_ATR_MULT, floor_pct=STOP_FLOOR_PCT):
    """max(2.25 x ATR, 1.50% of entry), in PRICE units. Thesis 5.1.

    The floor is a COST-ADMISSIBILITY CONSTRAINT, not a rail for outliers: a
    stop tighter than it cannot carry the cost budget. On BTCUSDT it sets the
    stop on nearly half of all signals.
    """
    entry_price = np.asarray(entry_price, dtype=float)
    atr = np.asarray(atr, dtype=float)
    return np.maximum(mult * atr, floor_pct / 100.0 * entry_price)


def floor_binds(entry_price, atr, mult=STOP_ATR_MULT, floor_pct=STOP_FLOOR_PCT):
    """Does the floor -- not the volatility -- set the stop?

    STRICTLY BELOW, which is report 21's convention: `stop_pct < 1.50` on the
    column `100 * 2.25 * atr / close`. Written the same way here so the binding
    rates this report cross-checks are the same quantity, not a near-neighbour
    of it.
    """
    entry_price = np.asarray(entry_price, dtype=float)
    atr = np.asarray(atr, dtype=float)
    return (mult * atr) < (floor_pct / 100.0 * entry_price)


def stop_from_distance(entry_price, distance, direction):
    """The stop PRICE, on the correct side of entry. No tick rounding.

    Deliberately unrounded: `position_size` takes the raw level, and rounding it
    onto the tick grid here would move the risk denominator by a tick's worth
    for no reason this measurement can justify. The engine rounds when it places
    an order; this is not that.
    """
    if direction == LONG:
        return entry_price - distance
    if direction == SHORT:
        return entry_price + distance
    raise ValueError("direction must be %r or %r, got %r"
                     % (LONG, SHORT, direction))


def size_and_notional(entry_price, stop_price, direction, cfg, symbol):
    """(quantity, notional) FROM THE ENGINE. Never recomputed by hand.

    `costs.position_size` is called directly. The whole point of the call is
    that the fees and slippage charged here are the ones the system charges:
    a hand-written `risk / (s + c)` with `c` taken from the cost TOLERANCE
    would be a budget ceiling wearing a cost's clothes, and 0.11 is a ceiling.

    NOTIONAL IS AN UPPER BOUND. The quantity returned is unquantised -- the
    engine reads no `qty_step` -- and flooring to the step in 5.3 can only
    reduce it.
    """
    qty = costs.position_size(entry_price, stop_price, direction, cfg, symbol)
    return qty, qty * entry_price


# ---------------------------------------------------------------------------
# The position table.
# ---------------------------------------------------------------------------

POSITION_COLUMNS = ("ts", "symbol", "direction", "entry_close_ms",
                    "entry_price", "atr", "stop_pct", "floor_binds",
                    "stop_distance", "stop_price", "quantity", "notional",
                    "exit_bar_ts", "exit_close_ms", "hold_ms")


def positions(frame, symbol, cfg=None, n=SETTLEMENTS_TO_CROSS):
    """One row per position the thesis would open, from a signal frame.

    TWO-SIDED BARS ARE SKIPPED, thesis 4.1. A bar that sweeps and rejects BOTH
    channels opens NO position -- not a long, not a short, not a coin flip. They
    are counted separately by `signal_counts` rather than dropped silently,
    because a skipped bar that nobody counts is indistinguishable from a bar the
    trigger failed to find.

    `ts` IS THE SIGNAL BAR'S OPEN TIME. Entry happens at `entry_close_ms`, one
    bar later. The distinction is load-bearing for occupancy: the position does
    not exist during the bar that produced it.
    """
    cfg = cost_config() if cfg is None else cfg
    ts = frame["ts"].to_numpy(np.int64)
    close = frame["close"].to_numpy(float)
    atr = frame["atr"].to_numpy(float)
    swp_long = frame["sweep_long"].to_numpy()
    swp_short = frame["sweep_short"].to_numpy()

    two_sided = swp_long & swp_short
    take_long = swp_long & ~two_sided
    take_short = swp_short & ~two_sided

    rows = []
    for direction, mask in ((LONG, take_long), (SHORT, take_short)):
        idx = np.nonzero(mask & np.isfinite(atr))[0]
        for i in idx:
            entry_price = float(close[i])
            dist = float(stop_distance(entry_price, atr[i]))
            stop = float(stop_from_distance(entry_price, dist, direction))
            qty, notional = size_and_notional(entry_price, stop, direction,
                                              cfg, symbol)
            exit_bar, exit_close, hold = max_hold_exit(ts[i], n)
            rows.append({
                "ts": int(ts[i]),
                "symbol": symbol,
                "direction": direction,
                "entry_close_ms": int(bar_close_ms(ts[i])),
                "entry_price": entry_price,
                "atr": float(atr[i]),
                "stop_pct": 100.0 * STOP_ATR_MULT * float(atr[i]) / entry_price,
                "floor_binds": bool(floor_binds(entry_price, atr[i])),
                "stop_distance": dist,
                "stop_price": stop,
                "quantity": float(qty),
                "notional": float(notional),
                "exit_bar_ts": int(exit_bar),
                "exit_close_ms": int(exit_close),
                "hold_ms": int(hold),
            })

    out = pd.DataFrame(rows, columns=list(POSITION_COLUMNS))
    if len(out):
        out = out.sort_values(["ts", "direction"],
                              kind="mergesort").reset_index(drop=True)
        assert_hold_admissible(out["hold_ms"].to_numpy(np.int64))
    # `ts` is the SIGNAL BAR, so this refuses any position opened on a sealed
    # bar. Exit timestamps are calendar values and are deliberately not sealed:
    # they read nothing.
    return rs.assert_sealed(out, "positions(%s)" % symbol)


def signal_counts(frame, windows=None):
    """Signal and two-sided counts per fold period. THE POPULATIONS ARE NAMED.

    `n_signal_bars`   -- bars carrying either mask, two-sided bars INCLUDED.
                         This is report 21's `n_signals` and it is what the
                         570 / 281 figures count.
    `n_two_sided`     -- bars carrying BOTH masks. Skipped by rule.
    `n_positions`     -- `n_signal_bars - n_two_sided`. THE TRADED POPULATION,
                         and the one every occupancy figure rests on.

    Three numbers rather than one because the closing record's transferable
    lesson is to name the population in the same sentence as the count.
    """
    windows = sp.fold_windows() if windows is None else windows
    ts = frame["ts"].to_numpy(np.int64)
    lmask = frame["sweep_long"].to_numpy()
    smask = frame["sweep_short"].to_numpy()
    both = lmask & smask
    any_signal = lmask | smask
    rows = []
    for fold_id, period, lo, hi in windows:
        inw = (ts >= lo) & (ts <= hi)
        n_any = int((any_signal & inw).sum())
        n_both = int((both & inw).sum())
        rows.append({
            "fold_id": fold_id,
            "period": period,
            "bars": int(inw.sum()),
            "n_signal_bars": n_any,
            "n_two_sided": n_both,
            "n_positions": n_any - n_both,
            "n_long": int((lmask & ~both & inw).sum()),
            "n_short": int((smask & ~both & inw).sum()),
        })
    return rows


# ---------------------------------------------------------------------------
# THE OCCUPANCY TIMELINE. The core measurement.
# ---------------------------------------------------------------------------

def hourly_grid(lo_ms, hi_ms):
    """Every 1h instant in [lo, hi], inclusive, on the epoch-aligned grid.

    Built from the CALENDAR rather than from the bar index, so a missing bucket
    would leave a hole in the bar series without silently shortening the
    timeline and inflating every per-bar fraction. At 1h over this window no
    bucket is dropped and the two coincide exactly, which is asserted rather
    than assumed.
    """
    lo, hi = int(lo_ms), int(hi_ms)
    if hi < lo:
        return np.empty(0, dtype=np.int64)
    lo -= lo % BAR_MS
    return np.arange(lo, hi + 1, BAR_MS, dtype=np.int64)


def occupancy(pos, grid):
    """Per-bar occupancy over `grid`: counts, notional and direction split.

    THE OCCUPANCY CONVENTION, STATED ONCE. A position opened at the close of bar
    T and closed at the close of bar X is open on the bars T+1 .. X inclusive --
    the half-open instant interval (close of T, close of X]. It is NOT open on
    its own signal bar, because at every moment of that bar it did not yet
    exist, and it IS open on its exit bar, because it is carried through that
    bar and closed at its end. The occupied bar count is then exactly the hold
    in hours, which is what makes the hand-computed control checkable.

    Accumulated as a difference array and cumulatively summed: one pass, and no
    quadratic scan over 11,000 positions x 26,000 bars.

    CLIPPED AT BOTH EDGES. A position entered near the end of the window exits
    past it; its occupancy is truncated at the last grid point and the
    truncation is COUNTED, never silently absorbed.
    """
    n = len(grid)
    out = {
        "ts": grid,
        "positions_open": np.zeros(n, dtype=np.int64),
        "notional_open": np.zeros(n, dtype=float),
        "long_open": np.zeros(n, dtype=np.int64),
        "short_open": np.zeros(n, dtype=np.int64),
        "n_positions": int(len(pos)),
        "n_clipped_at_end": 0,
        "n_clipped_at_start": 0,
    }
    if not n or not len(pos):
        return out

    entry_bar = pos["ts"].to_numpy(np.int64)
    exit_bar = pos["exit_bar_ts"].to_numpy(np.int64)
    notional = pos["notional"].to_numpy(float)
    is_long = (pos["direction"].to_numpy() == LONG)

    # First grid index strictly after the entry bar, and one past the exit bar.
    lo = np.searchsorted(grid, entry_bar, side="right")
    hi = np.searchsorted(grid, exit_bar, side="right")
    out["n_clipped_at_end"] = int((exit_bar > grid[-1]).sum())
    out["n_clipped_at_start"] = int((entry_bar < grid[0]).sum())
    lo = np.clip(lo, 0, n)
    hi = np.clip(hi, 0, n)

    d_count = np.zeros(n + 1, dtype=np.int64)
    d_long = np.zeros(n + 1, dtype=np.int64)
    d_short = np.zeros(n + 1, dtype=np.int64)
    d_notional = np.zeros(n + 1, dtype=float)
    keep = hi > lo
    np.add.at(d_count, lo[keep], 1)
    np.add.at(d_count, hi[keep], -1)
    np.add.at(d_notional, lo[keep], notional[keep])
    np.add.at(d_notional, hi[keep], -notional[keep])
    np.add.at(d_long, lo[keep & is_long], 1)
    np.add.at(d_long, hi[keep & is_long], -1)
    np.add.at(d_short, lo[keep & ~is_long], 1)
    np.add.at(d_short, hi[keep & ~is_long], -1)

    out["positions_open"] = np.cumsum(d_count)[:n]
    out["long_open"] = np.cumsum(d_long)[:n]
    out["short_open"] = np.cumsum(d_short)[:n]
    # Floating error accumulates over 26,000 cumulative sums; clamp the zeros
    # so an empty bar reads exactly 0.0 rather than 1e-12.
    notional_open = np.cumsum(d_notional)[:n]
    out["notional_open"] = np.where(out["positions_open"] > 0, notional_open, 0.0)
    return out


def signals_into_an_open_book(pos, timeline):
    """Fraction of positions opened while that book already had one open.

    "Already open" means open ON THE SIGNAL BAR -- strictly before the new
    position exists, since the new one starts at that bar's close and so
    contributes nothing to its own reading. This is the number that says whether
    overlap is the exception or the rule.
    """
    if not len(pos) or not len(timeline["ts"]):
        return {"n": int(len(pos)), "n_into_open": 0, "fraction": float("nan")}
    grid = timeline["ts"]
    idx = np.searchsorted(grid, pos["ts"].to_numpy(np.int64), side="left")
    inside = (idx < len(grid))
    idx = np.clip(idx, 0, len(grid) - 1)
    already = (timeline["positions_open"][idx] > 0) & inside
    return {"n": int(len(pos)), "n_into_open": int(already.sum()),
            "fraction": float(already.sum()) / float(len(pos))}


# ---------------------------------------------------------------------------
# Summaries.
# ---------------------------------------------------------------------------

def summary(values, percentiles=PERCENTILES):
    """`distribution` plus the mean. Min, percentiles, max, mean and n."""
    x = np.asarray(values, dtype=float)
    x = x[np.isfinite(x)]
    out = dict(distribution(x, percentiles))
    out["mean"] = float(x.mean()) if len(x) else float("nan")
    return out


def histogram(counts):
    """Bars at each concurrency level, as a count and as a fraction of bars.

    The FULL histogram, every level from 0 to the maximum, including levels
    that never occur -- a level silently missing from a sparse table reads as a
    level that was never reached.
    """
    c = np.asarray(counts, dtype=np.int64)
    n = int(len(c))
    top = int(c.max()) if n else 0
    return [{"level": k,
             "bars": int((c == k).sum()),
             "fraction": (float((c == k).sum()) / n) if n else float("nan")}
            for k in range(top + 1)]


def timeline_summary(timeline, capital=CAPITAL_USD, cfg=None):
    """Concurrency, notional, nominal risk and leverage over one timeline."""
    cfg = cost_config() if cfg is None else cfg
    count = timeline["positions_open"]
    notional = timeline["notional_open"]
    n_bars = int(len(count))
    occupied = count > 0
    same_side = (timeline["long_open"] == 0) | (timeline["short_open"] == 0)
    return {
        "bars": n_bars,
        "n_positions": timeline["n_positions"],
        "n_clipped_at_end": timeline["n_clipped_at_end"],
        "concurrency": summary(count),
        "notional": summary(notional),
        "leverage": summary(notional / capital if n_bars else notional),
        "nominal_risk_usd": summary(count * cfg.risk_usd),
        "histogram": histogram(count),
        "bars_occupied": int(occupied.sum()),
        "fraction_occupied": (float(occupied.sum()) / n_bars) if n_bars
                             else float("nan"),
        "bars_same_direction": int((occupied & same_side).sum()),
        "fraction_same_direction": (float((occupied & same_side).sum())
                                    / float(occupied.sum()))
                                   if int(occupied.sum()) else float("nan"),
    }


def worst_bar(book_timeline, per_symbol, capital=CAPITAL_USD):
    """The single most exposed bar, by open notional. Reported in full.

    Ranked on NOTIONAL rather than on position count, because required leverage
    is what a margin call is denominated in and two small positions are not
    worse than one large one. The position count at that bar is reported
    alongside so the two readings are both visible.
    """
    notional = book_timeline["notional_open"]
    if not len(notional) or not float(np.nanmax(notional)):
        return None
    i = int(np.argmax(notional))
    ts = int(book_timeline["ts"][i])
    per = {}
    for sym, tl in per_symbol.items():
        j = int(np.searchsorted(tl["ts"], ts, side="left"))
        if j < len(tl["ts"]) and int(tl["ts"][j]) == ts:
            per[sym] = {"positions": int(tl["positions_open"][j]),
                        "notional": float(tl["notional_open"][j]),
                        "long": int(tl["long_open"][j]),
                        "short": int(tl["short_open"][j])}
    return {
        "ts": ts,
        "iso": pd.Timestamp(ts, unit="ms", tz="UTC").isoformat(),
        "positions": int(book_timeline["positions_open"][i]),
        "notional": float(notional[i]),
        "leverage": float(notional[i] / capital),
        "long": int(book_timeline["long_open"][i]),
        "short": int(book_timeline["short_open"][i]),
        "per_symbol": per,
    }


# ---------------------------------------------------------------------------
# The whole pass.
# ---------------------------------------------------------------------------

def measure(symbols=rs.SYMBOLS, timeframe=TIMEFRAME, period=DONCHIAN_PERIOD,
            cfg=None, derived_dir=rs.DERIVED):
    """Every figure the report states, per symbol, per fold and across the book.

    THE FOLD CONVENTION. A fold's figures use the positions whose SIGNAL BAR
    falls inside that fold period, measured on that period's own grid. A
    position opened in the last hours of a period therefore has its tail
    truncated at the period boundary -- at most 24 bars of a ~4,300-bar training
    period -- and the count of truncated positions is carried on every summary
    rather than left to be inferred.
    """
    cfg = cost_config() if cfg is None else cfg
    windows = sp.fold_windows()

    per_symbol_pos, frames, counts = {}, {}, {}
    for sym in symbols:
        bars, bucket_stats = rs.build(sym, timeframe, derived_dir=derived_dir)
        frame = sp.analysis_frame(bars, period=period)
        frames[sym] = frame
        per_symbol_pos[sym] = positions(frame, sym, cfg=cfg)
        sweep_any = (frame["sweep_long"] | frame["sweep_short"]).to_numpy()
        counts[sym] = {
            "bars": int(len(frame)),
            "buckets_dropped": bucket_stats["buckets_dropped"],
            "folds": signal_counts(frame, windows),
            # Report 21's own population and its own function, so the
            # cross-check against the frozen binding rates is an identity and
            # not a re-derivation.
            "floor_binds_signal_bars": sp.floor_binding_fraction(
                frame.loc[sweep_any, "stop_pct"].to_numpy(float)),
            "floor_binds_positions": float(
                per_symbol_pos[sym]["floor_binds"].mean())
                if len(per_symbol_pos[sym]) else float("nan"),
            "n_signal_bars": int(sweep_any.sum()),
            "n_two_sided": int((frame["sweep_long"]
                                & frame["sweep_short"]).sum()),
            "n_positions": int(len(per_symbol_pos[sym])),
        }

    lo = min(int(f["ts"].min()) for f in frames.values())
    hi = max(int(f["ts"].max()) for f in frames.values())
    grid = hourly_grid(lo, hi)

    result = {
        "config": config_table(cfg, symbols),
        "windows": windows,
        "grid": {"lo": lo, "hi": hi, "bars": int(len(grid))},
        "counts": counts,
        "positions": per_symbol_pos,
        "symbols": {},
        "book": {},
    }

    def scope(pos_by_sym, g):
        tls = {s: occupancy(p, g) for s, p in pos_by_sym.items()}
        book = {
            "ts": g,
            "positions_open": sum(t["positions_open"] for t in tls.values()),
            "notional_open": sum(t["notional_open"] for t in tls.values()),
            "long_open": sum(t["long_open"] for t in tls.values()),
            "short_open": sum(t["short_open"] for t in tls.values()),
            "n_positions": sum(t["n_positions"] for t in tls.values()),
            "n_clipped_at_end": sum(t["n_clipped_at_end"] for t in tls.values()),
        }
        return tls, book

    tls, book_tl = scope(per_symbol_pos, grid)
    for sym in symbols:
        result["symbols"][sym] = {
            "pooled": timeline_summary(tls[sym], cfg=cfg),
            "into_open": signals_into_an_open_book(per_symbol_pos[sym],
                                                   tls[sym]),
            "hold_ms": summary(per_symbol_pos[sym]["hold_ms"].to_numpy(float)),
            "folds": {},
        }
    result["book"]["pooled"] = timeline_summary(book_tl, cfg=cfg)
    result["book"]["pooled"]["worst_bar"] = worst_bar(book_tl, tls)
    result["book"]["folds"] = {}

    for fold_id, period_name, w_lo, w_hi in windows:
        g = hourly_grid(max(w_lo, lo), min(w_hi, hi))
        sub = {s: p[(p["ts"] >= w_lo) & (p["ts"] <= w_hi)].reset_index(drop=True)
               for s, p in per_symbol_pos.items()}
        f_tls, f_book = scope(sub, g)
        key = (fold_id, period_name)
        for sym in symbols:
            result["symbols"][sym]["folds"][key] = {
                "summary": timeline_summary(f_tls[sym], cfg=cfg),
                "into_open": signals_into_an_open_book(sub[sym], f_tls[sym]),
                "floor_binds": float(sub[sym]["floor_binds"].mean())
                               if len(sub[sym]) else float("nan"),
            }
        result["book"]["folds"][key] = timeline_summary(f_book, cfg=cfg)
        result["book"]["folds"][key]["worst_bar"] = worst_bar(f_book, f_tls)

    all_pos = pd.concat(list(per_symbol_pos.values()), ignore_index=True)
    result["hold_hours"] = summary(all_pos["hold_ms"].to_numpy(float) / BAR_MS)
    result["hold_histogram"] = [
        {"hours": int(h), "positions": int((all_pos["hold_ms"] == h * BAR_MS).sum())}
        for h in range(HOLD_MIN_MS // BAR_MS, HOLD_MAX_MS // BAR_MS + 1)]
    result["n_positions"] = int(len(all_pos))
    return result
