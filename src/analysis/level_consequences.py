"""THE LEVEL AND ITS CONSEQUENCES. Point 4, sub-point 4.1c, step 2.

WHAT THIS COMPUTES, ALL FROM COMMITTED INPUTS:

  * THE LEVEL, from `docs/design/04_1c_proper.md` §2's displacement budget and
    §3's uncertainty parameter. Nothing else enters it.
  * THE FLOOR WIDTHS at that level, from report 36's closed form, which is
    IMPORTED and not reimplemented.
  * THE STRESS COMPARATOR of §5 -- the level that would follow if the
    uncertainty parameter ranged over the haircut alone -- with §5.3's
    reconciliation rule applied.
  * THE STRATUM over the candidate population, and the first count of the
    ATR-above-cap rejection population.

THE LEVEL IS NOT DERIVED HERE AND THIS MODULE DOES NOT PRETEND IT IS.
`docs/design/04_1c_proper.md` §4.2 commits that the calibration RE-DESCRIBES the
tolerance rather than deriving it, and §4.3 pre-committed that the result may be
a round figure and that the defence is the commit order rather than the
arithmetic. `level()` below is a quotient whose divisor is one.

NOTHING UNDER A SEALED PARTITION IS OPENED. The population comes from
`floor_curve.candidate_population`, which asserts the barrier IMMEDIATELY BEFORE
EACH READ rather than once per run, per report 29 §9.1's account of the barrier
that silently reverted. This module adds its own assertion at its own entry
point rather than relying on that one.

NO OUTCOME QUANTITY. NO EXIT RESOLVED. THE EXECUTION LOOP IS NOT INVOKED -- only
sizing functions are called, and `portfolio.size_position` is not among them.
"""

import os
import sys

import numpy as np
import pandas as pd

from src.analysis import floor_curve as fc
from src.analysis import risk_unit_floor_curve as ruf
from src.folds import schedule as sch
from src.timeframe import resample as rs
from src.timeframe import sealed_1m as sealed

sys.path.insert(0, os.path.join(rs.ROOT, "src", "engine"))

import sizing  # noqa: E402

LONG, SHORT = ruf.LONG, ruf.SHORT
DIRECTIONS = ruf.DIRECTIONS

#: `docs/design/04_1c_proper.md` §2.1. Ten per cent of one risk unit.
DISPLACEMENT_BUDGET = 0.10

#: `docs/design/04_1c_proper.md` §3.1. One hundred per cent proportional error.
UNCERTAINTY_PARAMETER = 1.00

#: The retired constant floor, quoted for ORIENTATION ONLY at report §2.3.
#: `docs/design/04_1c_pre_commitments.md` §4.3(a) makes closeness to it a
#: DISQUALIFYING property of a level-setting method. It is not a comparator and
#: nothing here is argued from it.
RETIRED_CONSTANT_FLOOR_PCT = 1.50


# ---------------------------------------------------------------------------
# PART 1. THE LEVEL.
# ---------------------------------------------------------------------------

def level(budget=DISPLACEMENT_BUDGET, uncertainty=UNCERTAINTY_PARAMETER):
    """The tolerance the committed calibration yields.

    `docs/design/04_1c_proper.md` §4.1: a proportional error in the unvalidated
    estimates displaces the risk unit by that error multiplied by the unvalidated
    share, and the constraint binds that share, so the admitted share is the
    budget divided by the error.

        THE DIVISOR IS ONE. THIS IS A CHANGE OF UNITS, NOT A CALCULATION.

    That §3.1 fixed the uncertainty parameter at one hundred per cent is what
    makes the level numerically equal to the budget. §4.3 disclosed in advance
    that the result might be round and committed that the defence is the commit
    order rather than the arithmetic. Reporting this quotient as a derivation
    would be the manufactured argument §4.2 forbids.
    """
    return float(budget) / float(uncertainty)


def level_is_inside_admitted_domain(cfg, value=None):
    """Is the level inside every cell's achievable range? Checked, not assumed.

    The admitted domain of `docs/design/04_1c_pre_commitments.md` §2.1 is the
    intersection across cells: bounded below by the largest per-cell value at the
    cap and above by the SMALLEST zero-width ceiling.
    """
    value = level() if value is None else float(value)
    lo, hi = ruf.common_achievable_range(cfg)
    return bool(lo < value < hi), lo, hi


# ---------------------------------------------------------------------------
# PART 2. THE FLOOR WIDTHS.
# ---------------------------------------------------------------------------

def widths_at(cfg, value=None, symbols=None):
    """Report 36's closed form at the level, per symbol and per direction.

    EACH WIDTH IS FED BACK through the path-two denominator and the ratio
    recovered, so the row carries its own verification rather than the report
    asserting one. `ruf.solve_and_feed_back` does both.
    """
    value = level() if value is None else float(value)
    symbols = tuple(rs.SYMBOLS) if symbols is None else tuple(symbols)
    rows = []
    for symbol in symbols:
        for direction in DIRECTIONS:
            row = ruf.solve_and_feed_back(value, cfg, symbol, direction)
            row["width_vs_retired_floor_pp"] = (row["width_pct"]
                                                - RETIRED_CONSTANT_FLOOR_PCT)
            rows.append(row)
    return pd.DataFrame(rows)


def feedback_residual(frame):
    """Largest failure of a solved width to reproduce the level it solved for."""
    return float(np.max(np.abs(frame["ratio"].to_numpy(float)
                               - frame["tau"].to_numpy(float))))


# ---------------------------------------------------------------------------
# PART 3. THE STRESS COMPARATOR.
# ---------------------------------------------------------------------------

def haircut_share_of_unvalidated(cfg, symbol, w=0.0, direction=LONG):
    """The haircut's share of the unvalidated sum.

    THE QUANTITY §5.3's RECONCILIATION RULE RANKS CELLS BY. It is width-dependent
    -- the haircut is charged on a stop price that moves -- so the width is a
    parameter and the caller states it. At zero width it is `h / A`.
    """
    a, _f, h, sigma = ruf.form_constants(cfg, symbol, direction)
    w = float(w)
    return (h * (1.0 + sigma * w)) / (a + sigma * w * h)


def worst_cell(cfg, symbols=None):
    """The symbol whose haircut is the largest fraction of its unvalidated sum.

    `docs/design/04_1c_proper.md` §5.3 committed the rule and DELIBERATELY DID
    NOT NAME THE SYMBOL, leaving the identification to this step because it is a
    comparison of rates and therefore a computation.
    """
    symbols = tuple(rs.SYMBOLS) if symbols is None else tuple(symbols)
    shares = {s: haircut_share_of_unvalidated(cfg, s) for s in symbols}
    top = max(shares.values())
    winners = sorted(s for s in symbols if shares[s] == top)
    return winners[0], shares, winners


def comparator_width(cfg, symbol, direction, budget=DISPLACEMENT_BUDGET,
                     uncertainty=UNCERTAINTY_PARAMETER):
    """The width at which the HAIRCUT ALONE, stressed, exhausts the budget.

    Under haircut-only scoping the displacement is the error multiplied by the
    haircut's share of the RISK UNIT, so the binding condition is

        e * h (1 + sigma w) / d(w)  =  B

    which is again linear in the width, for the reason report 36 §3.1 gives --
    both sides are affine in it. Solving:

        w = ( B (A + 2f) / e  -  h ) / ( sigma h  -  (B / e)(1 + sigma (f + h)) )
    """
    a, f, h, sigma = ruf.form_constants(cfg, symbol, direction)
    b = float(budget) / float(uncertainty)
    denom = sigma * h - b * (1.0 + sigma * (f + h))
    if denom == 0.0:
        raise ValueError("comparator has no solution for %s %s" % (symbol,
                                                                   direction))
    w = (b * (a + 2.0 * f) - h) / denom
    if not w > 0.0:
        raise ValueError(
            "no positive comparator width for %s %s: the haircut's share of the "
            "risk unit never reaches the budget" % (symbol, direction))
    return w


def comparator_level(cfg, symbol, direction, budget=DISPLACEMENT_BUDGET,
                     uncertainty=UNCERTAINTY_PARAMETER):
    """The TOLERANCE implied by the comparator width for one cell.

    The constraint is still the unvalidated sum over the risk unit; what changes
    is what the budget is spent on. So the comparator's level is that ratio,
    evaluated at the width where the haircut alone exhausts the budget.
    """
    w = comparator_width(cfg, symbol, direction, budget, uncertainty)
    return ruf.ratio_at_width(w, cfg, symbol, direction), w


def comparator_table(cfg, symbols=None):
    """Every cell's comparator width and implied level."""
    symbols = tuple(rs.SYMBOLS) if symbols is None else tuple(symbols)
    rows = []
    for symbol in symbols:
        for direction in DIRECTIONS:
            tau, w = comparator_level(cfg, symbol, direction)
            rows.append({
                "symbol": symbol, "direction": direction,
                "comparator_width": w, "comparator_width_pct": 100.0 * w,
                "comparator_level": tau,
                "haircut_share_at_that_width": haircut_share_of_unvalidated(
                    cfg, symbol, w, direction),
            })
    return pd.DataFrame(rows)


def binding_comparator_level(cfg, symbols=None):
    """§5.3's rule applied: the level satisfying the budget on the WORST cell.

    The worst cell is the symbol whose haircut is the largest fraction of its
    unvalidated sum. Its level binds; every other symbol is then protected MORE
    tightly than the budget requires, which is what that section says happens.
    """
    symbol, shares, _ = worst_cell(cfg, symbols)
    table = comparator_table(cfg, symbols)
    cells = table[table["symbol"] == symbol]
    binding = float(cells["comparator_level"].min())
    row = cells.loc[cells["comparator_level"].idxmin()]
    return binding, symbol, str(row["direction"]), shares


# ---------------------------------------------------------------------------
# PARTS 4 AND 5. THE POPULATION.
# ---------------------------------------------------------------------------

def candidate_population(cfg, derived_dir=None):
    """The candidate positions, through `floor_curve`'s reader.

    THE BARRIER IS ASSERTED HERE AND AGAIN INSIDE THAT READER, once per symbol
    immediately before each read. Two assertions rather than one, because a
    barrier verified in one module and relied on from another is a barrier
    assumed at the call site.
    """
    derived_dir = rs.DERIVED if derived_dir is None else derived_dir
    for symbol in rs.SYMBOLS:
        fc.assert_paths_unsealed(
            sealed.allowed_paths(symbol, derived_dir=derived_dir),
            "level_consequences.candidate_population(%s)" % symbol)
    return fc.candidate_population(cfg, derived_dir=derived_dir)


def fold_periods():
    """The eighteen fold periods: nine folds, train and test each.

    Boundaries are `src/folds/schedule.py`'s and are not restated. Start dates
    are inclusive at 00:00:00Z and end dates inclusive at 23:45:00Z, that
    module's own convention.
    """
    out = []
    for fold in sch.build_schedule():
        for phase in ("train", "test"):
            out.append({
                "fold_id": int(fold["fold_id"]),
                "phase": phase,
                "start": fold["%s_start" % phase],
                "end": fold["%s_end" % phase],
            })
    return out


def _ms(day, end_of_day=False):
    import datetime as dt
    stamp = dt.datetime(day.year, day.month, day.day, tzinfo=dt.timezone.utc)
    base = int(stamp.timestamp() * 1000)
    return base + sch.LAST_BAR_OFFSET_MS if end_of_day else base


def stratify(population, cfg, value=None):
    """Floor binding and the two rejection populations, per candidate.

    THE FLOOR IS PER SYMBOL AND PER DIRECTION, because report 36's curve is.

    THREE PREDICATES, AND THEY ARE NOT THE SAME QUESTION:

      * `floor_bound` -- the required floor, not the volatility, set the stop.
      * `pop_b_atr_above_cap` -- the RAW ATR-derived stop exceeds the frozen cap.
        Bar geometry, independent of the level entirely.
      * `pop_a_floor_above_cap` -- the required floor exceeds the cap. A property
        of the level and the rates, identical for every candidate in a cell.

    `sizing.floor_binds` and `sizing.stop_distance` are CALLED, not reimplemented.
    """
    value = level() if value is None else float(value)
    cap = float(cfg.stop_max_pct)

    entry = population["entry_price"].to_numpy(float)
    atr = population["atr"].to_numpy(float)
    symbols = population["symbol"].to_numpy()
    directions = population["direction"].to_numpy()

    n = len(population)
    width = np.empty(n, dtype=float)
    bound = np.empty(n, dtype=bool)
    pop_a = np.empty(n, dtype=bool)
    pop_b = np.empty(n, dtype=bool)

    cache = {}
    for i in range(n):
        key = (symbols[i], directions[i])
        if key not in cache:
            cache[key] = ruf.required_floor_fraction(value, cfg, key[0], key[1])
        w = cache[key]
        width[i] = w
        bound[i] = bool(sizing.floor_binds(entry[i], atr[i],
                                           floor_fraction=w))
        pop_a[i] = bool(w > cap)
        pop_b[i] = bool(sizing.STOP_ATR_MULT * atr[i] > cap * entry[i])

    out = population.copy()
    out["level"] = value
    out["floor_fraction"] = width
    out["floor_bound"] = bound
    out["pop_a_floor_above_cap"] = pop_a
    out["pop_b_atr_above_cap"] = pop_b
    return out


def by_symbol(frame):
    rows = []
    for symbol, group in frame.groupby("symbol", sort=True):
        rows.append(_counts(symbol, "all", group))
    rows.append(_counts("POOLED", "all", frame))
    return pd.DataFrame(rows)


def by_fold_period(frame):
    """Per fold period. A candidate is assigned by its entry bar's close stamp.

    CANDIDATES OUTSIDE EVERY FOLD PERIOD EXIST -- the schedule's in-sample window
    opens after the first derived bar -- and are reported as their own row rather
    than dropped, because a count that silently loses rows is a count nobody can
    reconcile.
    """
    stamps = frame["entry_close_ms"].to_numpy(np.int64)
    rows = []
    assigned = np.zeros(len(frame), dtype=bool)
    for period in fold_periods():
        lo = _ms(period["start"])
        hi = _ms(period["end"], end_of_day=True)
        mask = (stamps >= lo) & (stamps <= hi)
        assigned |= mask
        rows.append(_counts("fold %d %s" % (period["fold_id"],
                                            period["phase"]),
                            "period", frame[mask]))
    rows.append(_counts("OUTSIDE ANY FOLD PERIOD", "period",
                        frame[~assigned]))
    return pd.DataFrame(rows)


def _counts(label, kind, group):
    n = int(len(group))
    bound = int(group["floor_bound"].sum()) if n else 0
    return {
        "cell": label, "kind": kind, "n": n,
        "floor_bound": bound,
        "floor_binding_fraction": (bound / n) if n else float("nan"),
        "not_floor_bound": n - bound,
        "pop_a": int(group["pop_a_floor_above_cap"].sum()) if n else 0,
        "pop_b": int(group["pop_b_atr_above_cap"].sum()) if n else 0,
    }


def overlap(frame):
    """How populations B and the floor-bound stratum interact.

    A REJECTED CANDIDATE IS NOT FLOOR-BOUND -- it is not a position at all --
    so the two predicates cannot both describe the same admitted candidate.
    Whether they overlap AS PREDICATES over the candidate population is a
    different question and is what this measures.
    """
    b = frame["pop_b_atr_above_cap"].to_numpy(bool)
    f = frame["floor_bound"].to_numpy(bool)
    return {
        "n": int(len(frame)),
        "both": int(np.sum(b & f)),
        "b_only": int(np.sum(b & ~f)),
        "floor_bound_only": int(np.sum(~b & f)),
        "neither": int(np.sum(~b & ~f)),
    }
