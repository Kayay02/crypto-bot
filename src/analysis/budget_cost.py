"""What the frozen aggregate risk budget costs: skips, composition, exposure.

WHAT IS BEING ASKED. Report 24 measured the book with NO cap -- a median of 9
concurrent positions, a maximum of 28, 11,384 positions over the window. The
budget was then frozen at 120.00 USDT in three commits, deliberately BEFORE this
measurement existed, so the level could not be fitted to preserve statistical
power. THIS STEP APPLIES THE FROZEN RULE AND REPORTS WHAT IT COSTS. It changes
no rule, chooses no parameter, and sweeps nothing.

THE RULE IS READ, NOT RETYPED. Every value comes from `src/risk/budget.py`:
the budget, the risk unit, the slot count, the rotation table, the rotation
period and modulus, the charging basis and the intra-bar order. A test asserts
each figure used here is that module's object, so a divergence between the
frozen specification and this measurement is impossible by construction.

THE RULE, AS AMENDED, IN THE FORM IMPLEMENTED:

  * A HARD CAP OF SIX CONCURRENT FULL-SIZE POSITIONS WITH ARRIVAL-ORDER SKIP.
    Amendment 1 Rule B charges the NOMINAL risk unit and never the realised one,
    and the budget is an exact multiple of it, so the allocation is always
    exactly one unit or exactly zero and zero is never viable. The partial
    branch is therefore unreachable -- and a counter asserts it is never taken
    rather than trusting the argument.
  * RULE C, within a bar close: ALL exits are processed first, each returning
    one unit, and only then are that bar's signals evaluated.
  * RULE A, within a bar: signals are ordered by the cyclic rotation of the
    bar's own open timestamp.
  * A skipped signal is SKIPPED: not queued, not deferred, not resized later.

ONE CONTINUOUS PASS, AND THE BUDGET DOES NOT RESET AT A FOLD BOUNDARY. It is an
account property and it is continuous over the window. FOLDS ARE AN ATTRIBUTION
OF RESULTS, NOT SEPARATE RUNS: a position or a skip belongs to the fold period
containing its SIGNAL BAR, which is report 24's convention. A fold-independent
run -- one that restarted with an empty book at each boundary -- would differ at
fold edges, and would also not be a thing the account could do.

TWO CAVEATS THAT ARE NOT THE SAME CAVEAT, AND MUST NOT BE MERGED:

  1. THIS MEASUREMENT IS DETERMINISTIC AND THE CAPPED POPULATION IS A STRICT
     SUBSET of the uncapped one, because exits are located on the funding
     calendar and depend on nothing but the entry timestamp.
  2. THE REAL BACKTEST WILL NOT HAVE PROPERTY 1. Document 05 section 6 accepts
     that under real exits the traded population is a function of realised
     outcomes -- a stop-out frees its slot hours before a max-hold exit would --
     so the capped population then depends on the path and is not a subset of
     anything knowable in advance.

EVERY SKIP FIGURE HERE IS AN UPPER BOUND. Under real exits, positions closing
early free budget early and admit signals this measurement skips. The magnitude
is unknowable until the validation design exists.

THE PERFORMANCE FIREWALL IS ARMED. No expectancy, win rate, profit factor,
Sharpe, Sortino, equity curve, drawdown, r_multiple, net_pnl or gross_pnl is
computed, inspected, estimated or referenced. NO STOP OR TARGET IS EVALUATED
ANYWHERE. No bar after the entry bar is read except to locate the max-hold exit
on the funding calendar, which is arithmetic on a timestamp. A test walks this
module's AST and refuses all twelve names.

`src/engine/simulate.py` IS NOT IMPORTED AND MUST NOT BE. Its portfolio mode
carries its own "one open position per symbol, no pyramiding" rule and its own
margin refusal at `max_leverage = 3.0`, which report 25 section 10.1 established
is an unmeasured placeholder 33-50x more restrictive than the venue and which
would bind at six floor-bound positions. EITHER WOULD SILENTLY CONTAMINATE THIS
MEASUREMENT, and a test asserts the module is unreachable from here.

THE HOLDOUT IS SEALED. The window is inherited whole from `resample.py` by way
of `sweep_population` and `exposure_profile`; this module defines no window
constant of its own and a test asserts it defines none.

NOTHING IS REIMPLEMENTED. The signal population is report 21's, the position
table is report 24's, and the floor-binding fraction is report 21's own
function, so every figure below is the same quantity those reports measured.
"""

import heapq
import os
import sys

import numpy as np
import pandas as pd

from src.analysis import exposure_profile as ep
from src.analysis import sweep_population as sp
from src.risk import budget as rb
from src.timeframe import resample as rs

# The engine's sizing, imported the way report 24 imports it. `costs` only:
# `simulate` is refused by test.
sys.path.insert(0, os.path.join(rs.ROOT, "src", "engine"))

import costs  # noqa: E402  (imported for the config object report 24 sizes with)


# ---------------------------------------------------------------------------
# THE RULE. Read from the frozen module, never restated.
# ---------------------------------------------------------------------------

BUDGET_USD = rb.MAX_AGGREGATE_OPEN_RISK_USD
UNIT_USD = rb.RISK_PER_TRADE_USD
MAX_SLOTS = rb.FULL_SIZE_POSITIONS
ROTATION_PERIOD_MS = rb.ROTATION_PERIOD_MS
ROTATION_MODULUS = rb.ROTATION_MODULUS
SYMBOL_ROTATION = rb.SYMBOL_ROTATION
BUDGET_CHARGES = rb.BUDGET_CHARGES
INTRA_BAR_ORDER = rb.INTRA_BAR_ORDER
CAPITAL_USD = ep.CAPITAL_USD
"""Every one of these is the frozen module's object, not a copy of its value.
A test asserts identity, so the specification and the measurement cannot drift."""

BAR_MS = ep.BAR_MS
PERCENTILES = ep.PERCENTILES

#: The holdout's span, from the CALENDAR only. Used by the out-of-sample
#: projection in `project_holdout`, which reads no bar of it -- the figure is a
#: count of hours between two dates, and the dates are already public in
#: `folds.json`'s holdout entry and in `schedule.py`'s constants.
HOLDOUT_DAYS = 572
"""2025-01-01 through 2026-07-26 inclusive: 365 + 207 days. Derived in
`holdout_bars` from `schedule`'s own two dates rather than trusted here; this
constant exists so the test can pin the arithmetic."""


def rotation(bar_open_ms):
    """Amendment 1 Rule A: the rotation value for a bar, from its OPEN time."""
    return (int(bar_open_ms) // ROTATION_PERIOD_MS) % ROTATION_MODULUS


def priority(bar_open_ms):
    """The symbol priority order for a bar, highest priority first."""
    return SYMBOL_ROTATION[rotation(bar_open_ms)]


def priority_rank(bar_open_ms, symbol):
    """A symbol's rank on a bar. 0 is first. Used to sort contested bars."""
    return priority(bar_open_ms).index(symbol)


# ---------------------------------------------------------------------------
# THE CANDIDATE POPULATION. Report 24's, unmodified.
# ---------------------------------------------------------------------------

def candidates(symbols=rs.SYMBOLS, timeframe=ep.TIMEFRAME,
               period=ep.DONCHIAN_PERIOD, cfg=None, derived_dir=rs.DERIVED):
    """Every position the UNCAPPED rule would open, from report 24's own code.

    `sweep_population.analysis_frame` produces the signals and
    `exposure_profile.positions` produces the table -- both imported unmodified,
    so this is the same 11,384-row population report 24 measured, sorted into
    one arrival-ordered frame.

    THE SORT IS THE ARRIVAL ORDER THE RULE ACTS ON: by signal bar, then by the
    bar's own rotation rank. Ties beyond that are impossible -- a bar yields at
    most one signal per symbol, because thesis 4.1 skips two-sided bars.
    """
    cfg = ep.cost_config() if cfg is None else cfg
    frames, tables = {}, []
    for sym in symbols:
        bars, _ = rs.build(sym, timeframe, derived_dir=derived_dir)
        frame = sp.analysis_frame(bars, period=period)
        frames[sym] = frame
        tables.append(ep.positions(frame, sym, cfg=cfg))
    out = pd.concat(tables, ignore_index=True)
    out["rank"] = [priority_rank(t, s)
                   for t, s in zip(out["ts"].to_numpy(np.int64),
                                   out["symbol"].to_numpy())]
    out = out.sort_values(["ts", "rank"], kind="mergesort").reset_index(drop=True)
    return rs.assert_sealed(out, "candidates"), frames


# ---------------------------------------------------------------------------
# THE ALLOCATION WALK. One continuous pass.
# ---------------------------------------------------------------------------

def allocate(cand, budget_usd=BUDGET_USD, unit_usd=UNIT_USD):
    """Apply the frozen rule to the candidate population. One pass, in order.

    WHERE THE REFERENCE LOGIC LIVES, STATED HERE BECAUSE IT MATTERS. Amendment
    2's behavioural pin needed an allocation implementation and it sits in
    `tests/test_risk_budget.py::_process_bar` -- a per-bar counter model of the
    two candidate loop orders, with no notion of individual positions, exit
    scheduling or the rotation. `src/risk/budget.py` holds VALUES ONLY plus its
    import-time integrity check, exactly as its three prompts required. THIS
    FUNCTION IS THE FIRST FULL IMPLEMENTATION, and a test cross-checks it
    against that per-bar model on the cases the model can express.

    THE WALK, per bar carrying signals, in ascending bar order:

      1. release every open position whose exit bar is EARLIER than this bar
         (they closed on their own bars, which carried no signals);
      2. RULE C -- release every open position whose exit bar IS this bar,
         counting them, so the diagnostic can see what Rule C bought;
      3. RULE A -- evaluate this bar's signals in rotation-rank order, each
         taking `min(unit, remaining)`.

    A MIN-HEAP CARRIES THE OPEN POSITIONS' EXIT BARS, so releasing is O(log n)
    and the pass is one sweep rather than a scan per bar.

    RETURNS the candidate frame with a `taken` column added, plus per-bar
    diagnostics and the invariant counters.
    """
    ts = cand["ts"].to_numpy(np.int64)
    exit_bar = cand["exit_bar_ts"].to_numpy(np.int64)
    symbols = cand["symbol"].to_numpy()

    taken = np.zeros(len(cand), dtype=bool)
    open_exits = []                      # min-heap of exit bar timestamps
    charged = 0.0
    partial_allocations = 0
    full_at_arrival = 0
    rows = []

    i, n = 0, len(cand)
    while i < n:
        bar = int(ts[i])
        j = i
        while j < n and int(ts[j]) == bar:
            j += 1
        n_signals = j - i

        # 1. exits on EARLIER bars -- they released when they happened.
        while open_exits and open_exits[0] < bar:
            heapq.heappop(open_exits)
            charged -= unit_usd
        open_before_exits = len(open_exits)

        # 2. RULE C -- this bar's exits, before this bar's entries.
        n_exits_here = 0
        while open_exits and open_exits[0] == bar:
            heapq.heappop(open_exits)
            charged -= unit_usd
            n_exits_here += 1
        open_after_exits = len(open_exits)

        # 3. RULE A -- this bar's signals, in rotation-rank order.
        n_taken_here = 0
        for k in range(i, j):
            remaining = budget_usd - charged
            if remaining <= 0.0:
                full_at_arrival += 1
                continue
            allocation = min(unit_usd, remaining)
            if allocation != unit_usd:
                # UNREACHABLE under Rule B. Counted rather than assumed away:
                # a partial allocation here would mean the budget stopped being
                # a whole multiple of the unit, which is the silent failure
                # Amendment 1 Rule B exists to prevent.
                partial_allocations += 1
                continue
            taken[k] = True
            charged += unit_usd
            heapq.heappush(open_exits, int(exit_bar[k]))
            n_taken_here += 1

        free_before = MAX_SLOTS - open_before_exits
        free_after = MAX_SLOTS - open_after_exits
        rows.append({
            "ts": bar,
            "n_signals": n_signals,
            "n_exits": n_exits_here,
            "open_before_exits": open_before_exits,
            "open_after_exits": open_after_exits,
            "free_before_exits": free_before,
            "free_after_exits": free_after,
            "n_taken": n_taken_here,
            "n_skipped": n_signals - n_taken_here,
            "contested": bool(n_signals >= 2),
            # RULE A changed an outcome only when it had to choose: more
            # contenders than slots.
            "rule_a_decided": bool(n_signals >= 2 and free_after < n_signals),
            # RULE C bought exactly the takes beyond what was free BEFORE this
            # bar's exits were released. A LOCAL counterfactual on processing
            # order at this bar, holding the rest of the run fixed -- not an
            # alternative run, which would diverge globally.
            "rule_c_gain": int(max(0, n_taken_here - max(0, free_before))),
            "symbols": tuple(symbols[i:j]),
        })
        i = j

    out = cand.copy()
    out["taken"] = taken
    return {
        "positions": out,
        "bars": pd.DataFrame(rows),
        "partial_allocations": int(partial_allocations),
        "full_at_arrival": int(full_at_arrival),
        "n_taken": int(taken.sum()),
        "n_skipped": int((~taken).sum()),
    }


# ---------------------------------------------------------------------------
# Invariants, checked on the real run.
# ---------------------------------------------------------------------------

def assert_invariants(result, grid, budget_usd=BUDGET_USD, unit_usd=UNIT_USD):
    """Refuse a run that breaks any property the frozen rule guarantees.

    Every one of these is a silent failure if unchecked: a book of seven, a
    negative budget, a fractional remainder or a partial allocation would all
    produce a plausible-looking table.
    """
    if result["partial_allocations"] != 0:
        raise ValueError(
            "the partial-allocation branch was taken %d times; Amendment 1 "
            "Rule B says it is unreachable at these values"
            % result["partial_allocations"])

    took = result["positions"][result["positions"]["taken"]]
    timeline = ep.occupancy(took.reset_index(drop=True), grid)
    count = timeline["positions_open"]
    if count.size:
        if int(count.max()) > MAX_SLOTS:
            raise ValueError("concurrency reached %d, above the %d-slot cap"
                             % (int(count.max()), MAX_SLOTS))
        if int(count.min()) < 0:
            raise ValueError("negative concurrency")
    charged = count * unit_usd
    if charged.size and float(charged.max()) > budget_usd + 1e-9:
        raise ValueError("open nominal risk reached %r, above the budget %r"
                         % (float(charged.max()), budget_usd))
    remaining = budget_usd - charged
    if remaining.size:
        if float(remaining.min()) < -1e-9:
            raise ValueError("remaining budget went negative")
        steps = remaining / unit_usd
        if float(np.abs(steps - np.round(steps)).max()) > 1e-9:
            raise ValueError(
                "the remaining budget is not a whole multiple of the risk "
                "unit; Rule B's nominal charging has been broken")
    return timeline


# ---------------------------------------------------------------------------
# Attribution and composition.
# ---------------------------------------------------------------------------

def folds_of(ts, windows):
    """EVERY (fold_id, period) whose window contains a signal bar.

    ATTRIBUTION, NOT SEGMENTATION. The run is continuous; a position or a skip
    is attributed to the fold period containing its SIGNAL BAR, which is report
    24's convention.

    A TUPLE, NOT A SINGLE KEY, AND THE REASON IS THE FOLD ARCHITECTURE.
    Adjacent TRAINING windows overlap by 50% (`src/folds/schedule.py`: the nine
    folds are a stability probe, not nine independent trials), so one bar can
    fall in two training periods. Returning the first match would silently drop
    the second and make the per-fold tables disagree with their own total.
    Train and test within one fold are disjoint, and bars before fold 1 belong
    to no period at all.
    """
    return tuple((fold_id, period) for fold_id, period, lo, hi in windows
                 if lo <= ts <= hi)


def attribute(positions, windows):
    """Add the fold-period attribution to a position table.

    `fold_periods` is every period containing the signal bar and `n_fold_periods`
    is how many. The per-fold tables are built by filtering on the windows
    themselves, so these columns are provenance rather than an input to any
    figure -- but they make the overlap visible in the table rather than only in
    a footnote.
    """
    out = positions.copy()
    keys = [folds_of(int(t), windows) for t in out["ts"].to_numpy(np.int64)]
    out["fold_periods"] = keys
    out["n_fold_periods"] = [len(k) for k in keys]
    return out


def floor_binding(positions):
    """Report 21's own function on this sub-population. An identity, not a
    re-derivation: the same predicate on the same `stop_pct` column."""
    if not len(positions):
        return float("nan")
    return sp.floor_binding_fraction(positions["stop_pct"].to_numpy(float))


def composition(positions):
    """Counts and floor-binding for a population and its two sub-populations."""
    took = positions[positions["taken"]]
    skipped = positions[~positions["taken"]]
    return {
        "n_signals": int(len(positions)),
        "n_taken": int(len(took)),
        "n_skipped": int(len(skipped)),
        "skip_rate": (float(len(skipped)) / len(positions)) if len(positions)
                     else float("nan"),
        "floor_binds_all": floor_binding(positions),
        "floor_binds_taken": floor_binding(took),
        "floor_binds_skipped": floor_binding(skipped),
    }


def same_symbol_opposite_direction_bars(positions, grid):
    """Bars on which ONE symbol carries an open long AND an open short.

    THE EVIDENCE FOR THE HEDGE-MODE DECISION. Report 25 section 5.1 established
    that under one-way mode an opposite-direction signal OFFSETS an open
    position rather than opening a trade. If this count is zero the decision was
    merely prudent; if it is non-zero it was necessary, because those bars are
    exactly the ones one-way mode could not have represented.
    """
    out = {}
    for sym in sorted(set(positions["symbol"])):
        rows = positions[positions["symbol"] == sym]
        longs = rows[rows["direction"] == ep.LONG].reset_index(drop=True)
        shorts = rows[rows["direction"] == ep.SHORT].reset_index(drop=True)
        lo_tl = ep.occupancy(longs, grid)["positions_open"]
        sh_tl = ep.occupancy(shorts, grid)["positions_open"]
        both = (lo_tl > 0) & (sh_tl > 0)
        out[sym] = {
            "bars_both_open": int(both.sum()),
            "fraction": (float(both.sum()) / len(grid)) if len(grid)
                        else float("nan"),
            "bars_long_open": int((lo_tl > 0).sum()),
            "bars_short_open": int((sh_tl > 0).sum()),
        }
    return out


# ---------------------------------------------------------------------------
# The out-of-sample projection. CALENDAR ARITHMETIC; NO SEALED BAR IS READ.
# ---------------------------------------------------------------------------

def holdout_bars():
    """Hourly bars in the holdout span, from `schedule`'s two DATES.

    THIS READS NO DATA. It is a count of hours between two dates already
    published in `folds.json` and in `schedule.py`'s constants. No parquet is
    opened, no bar is loaded, and the sealed window is not touched -- the seal
    forbids reading the holdout's CONTENT, not knowing how long it is.
    """
    from src.folds import schedule as sch
    days = (sch.HOLDOUT_TEST_END - sch.HOLDOUT_TEST_START).days + 1
    return days, days * 24


def project_holdout(taken_per_symbol, in_sample_bars):
    """Extrapolate the in-sample taken-position rate over the holdout's span.

    AN EXTRAPOLATION, NOT A MEASUREMENT, and it rests on one stated assumption:
    that signal density is STATIONARY between the two periods. Nothing in this
    project supports that assumption and nothing here tests it -- the holdout is
    sealed, which is exactly why the figure has to be projected rather than
    counted.
    """
    days, bars = holdout_bars()
    return {
        "holdout_days": days,
        "holdout_bars": bars,
        "in_sample_bars": int(in_sample_bars),
        "per_symbol": {
            sym: {
                "taken_in_sample": int(n),
                "rate_per_bar": float(n) / in_sample_bars,
                "projected": float(n) * bars / in_sample_bars,
            }
            for sym, n in taken_per_symbol.items()
        },
    }


# ---------------------------------------------------------------------------
# The whole pass.
# ---------------------------------------------------------------------------

def measure(symbols=rs.SYMBOLS, cfg=None, derived_dir=rs.DERIVED):
    """Every figure the report states. One continuous pass, folds attributed."""
    cfg = ep.cost_config() if cfg is None else cfg
    windows = sp.fold_windows()
    cand, frames = candidates(symbols=symbols, cfg=cfg, derived_dir=derived_dir)

    lo = min(int(f["ts"].min()) for f in frames.values())
    hi = max(int(f["ts"].max()) for f in frames.values())
    grid = ep.hourly_grid(lo, hi)

    result = allocate(cand)
    timeline_taken = assert_invariants(result, grid)
    positions = attribute(result["positions"], windows)

    took = positions[positions["taken"]].reset_index(drop=True)
    per_symbol_taken = {s: took[took["symbol"] == s].reset_index(drop=True)
                        for s in symbols}
    per_symbol_all = {s: positions[positions["symbol"] == s].reset_index(drop=True)
                      for s in symbols}

    tls = {s: ep.occupancy(p, grid) for s, p in per_symbol_taken.items()}
    book = {
        "ts": grid,
        "positions_open": sum(t["positions_open"] for t in tls.values()),
        "notional_open": sum(t["notional_open"] for t in tls.values()),
        "long_open": sum(t["long_open"] for t in tls.values()),
        "short_open": sum(t["short_open"] for t in tls.values()),
        "n_positions": sum(t["n_positions"] for t in tls.values()),
        "n_clipped_at_end": sum(t["n_clipped_at_end"] for t in tls.values()),
    }

    bars = result["bars"]
    diagnostics = {
        "bars_with_signals": int(len(bars)),
        "contested_bars": int(bars["contested"].sum()),
        "rule_a_decided_bars": int(bars["rule_a_decided"].sum()),
        "bars_with_exit_and_signal": int(((bars["n_exits"] > 0)
                                          & (bars["n_signals"] > 0)).sum()),
        "rule_c_gain_positions": int(bars["rule_c_gain"].sum()),
        "rule_c_gain_bars": int((bars["rule_c_gain"] > 0).sum()),
        "full_at_arrival": result["full_at_arrival"],
        "partial_allocations": result["partial_allocations"],
        "signals_on_contested_bars": int(
            bars.loc[bars["contested"], "n_signals"].sum()),
        "signals_on_rule_a_bars": int(
            bars.loc[bars["rule_a_decided"], "n_signals"].sum()),
    }

    out = {
        "rule": {
            "budget_usd": BUDGET_USD, "unit_usd": UNIT_USD,
            "max_slots": MAX_SLOTS, "charges": BUDGET_CHARGES,
            "intra_bar_order": INTRA_BAR_ORDER,
            "rotation": SYMBOL_ROTATION,
        },
        "grid": {"lo": lo, "hi": hi, "bars": int(len(grid))},
        "windows": windows,
        "positions": positions,
        "pooled": composition(positions),
        "per_symbol": {s: composition(p) for s, p in per_symbol_all.items()},
        "per_symbol_per_fold": {},
        "pooled_per_fold": {},
        "book": ep.timeline_summary(book, cfg=cfg),
        "book_timeline": book,
        "per_symbol_book": {s: ep.timeline_summary(t, cfg=cfg)
                            for s, t in tls.items()},
        "worst_bar": ep.worst_bar(book, tls),
        "diagnostics": diagnostics,
        "opposite_direction_capped": same_symbol_opposite_direction_bars(
            took, grid),
        "opposite_direction_uncapped": same_symbol_opposite_direction_bars(
            positions, grid),
        "projection": project_holdout(
            {s: int(len(p)) for s, p in per_symbol_taken.items()},
            len(grid)),
        "timeline_taken": timeline_taken,
    }

    for fold_id, period, w_lo, w_hi in windows:
        key = (fold_id, period)
        inw = positions[(positions["ts"] >= w_lo) & (positions["ts"] <= w_hi)]
        out["pooled_per_fold"][key] = composition(inw)
        out["per_symbol_per_fold"][key] = {
            s: composition(inw[inw["symbol"] == s]) for s in symbols}
    return out
