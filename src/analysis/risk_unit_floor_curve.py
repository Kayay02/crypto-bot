"""THE STOP FLOOR UNDER THE RISK-UNIT DENOMINATOR. Point 4, sub-point 4.1c.

THE GOVERNING CONSTRAINT, as committed at `docs/design/04_1c_denominator_choice.md`
§2.1: the unvalidated sum over the RISK UNIT, at most the tolerance. The risk unit
is path two's denominator -- `portfolio.size_position`'s, being
`sizing.per_unit_denominator` plus `portfolio.funding_per_unit`. Funding appears in
BOTH the numerator and the denominator.

NOTHING IS INHERITED FROM REPORT 33. Its closed form was solved over the STOP
DISTANCE as denominator and over path one. Its grid bounds, its pole, its direction
split and its grid-selection reasoning are properties of that form. This module
imports nothing from it and re-establishes each question from this algebra.
Carrying any of them across by analogy is the recurring defect class the ledger
tracks.

THE COST ALGEBRA IS CALLED, NEVER REIMPLEMENTED. The risk unit comes from
`sizing.per_unit_denominator` plus `portfolio.funding_per_unit`; the unvalidated sum
is recovered BY DIFFERENCE against a zeroed-set configuration. No fee, no haircut
rate and no funding rate is retyped here.

THE UNVALIDATED SET IS A SET WITH ATTACHMENT POINTS, not a list of hardcoded terms.
A term is named, given a rate source, and given the price it is charged against.
An unknown attachment point RAISES; it is never silently dropped.

NO TOLERANCE IS SELECTED, NO FLOOR IS RECOMMENDED, NO OUTCOME QUANTITY IS
COMPUTED, NO EXIT IS RESOLVED, AND NOTHING UNDER `data/` IS OPENED. This module is
over rates and algebra.
"""

import os
import sys
from dataclasses import replace

import numpy as np

from src.timeframe import resample as rs

sys.path.insert(0, os.path.join(rs.ROOT, "src", "engine"))

import costs  # noqa: E402
import portfolio as pf  # noqa: E402
import sizing  # noqa: E402

LONG, SHORT = costs.LONG, costs.SHORT
DIRECTIONS = (LONG, SHORT)

#: Reference entry price. Every quantity below is a FRACTION, and §3 of the report
#: verifies invariance to this choice at three widely separated prices.
REFERENCE_PRICE = 30_000.0

# ---------------------------------------------------------------------------
# THE UNVALIDATED SET, WITH ATTACHMENT POINTS.
# ---------------------------------------------------------------------------

ATTACH_ENTRY = "entry"
ATTACH_STOP = "stop"
ATTACHMENT_POINTS = (ATTACH_ENTRY, ATTACH_STOP)


class UnknownAttachmentPoint(ValueError):
    """A term names a price this module does not know how to charge against.

    RAISED RATHER THAN DROPPED. A term silently skipped would leave the numerator
    short and every solved width wrong, with nothing failing.
    """


#: name -> attachment point. THE MEMBERSHIP IS `docs/design/04_1c_path_and_scope.md`
#: §3's: the stop haircut, entry slippage, and funding. The attachment point is
#: WHICH PRICE the term is charged against, and it is what makes the direction
#: question answerable rather than assumed.
UNVALIDATED_TERMS = {
    "stop_haircut_bps": ATTACH_STOP,
    "entry_slippage_bps": ATTACH_ENTRY,
    "funding": ATTACH_ENTRY,
}


def attachment_price(point, entry_price, stop):
    """The price a term at `point` is charged against."""
    if point == ATTACH_ENTRY:
        return float(entry_price)
    if point == ATTACH_STOP:
        return float(stop)
    raise UnknownAttachmentPoint(
        "unknown attachment point %r; known points are %r" % (point,
                                                              ATTACHMENT_POINTS))


def unvalidated_rates(cfg, symbol):
    """Each unvalidated term's rate, as a fraction of the price it attaches to.

    READ FROM THE IMPLEMENTATION. The haircut and slippage come from the cost
    config; the funding rate and settlement count come from the constants
    `portfolio.py` itself reads, at `src/risk/exit_spec.py:115` and `:101`.
    """
    out = {}
    for name, point in UNVALIDATED_TERMS.items():
        if point not in ATTACHMENT_POINTS:
            raise UnknownAttachmentPoint(
                "term %r names unknown attachment point %r" % (name, point))
        if name == "stop_haircut_bps":
            out[name] = (point, cfg.haircut_bps(symbol) / 10_000.0)
        elif name == "entry_slippage_bps":
            out[name] = (point, float(cfg.entry_slippage_bps) / 10_000.0)
        elif name == "funding":
            out[name] = (point, pf.FUNDING_RATE * pf.FUNDING_COUNT)
        else:
            raise KeyError("no rate source for unvalidated term %r" % name)
    return out


def zero_unvalidated(cfg):
    """The config with every CONFIG-BORNE unvalidated rate set to zero.

    Funding is not config-borne -- `portfolio.funding_per_unit` reads module
    constants -- so it is excluded from the risk unit by OMISSION at the call site
    rather than by zeroing here. `bare_denominator` is where that happens.
    """
    return replace(cfg,
                   entry_slippage_bps=0.0,
                   stop_haircut_bps={s: 0.0 for s in cfg.stop_haircut_bps})


# ---------------------------------------------------------------------------
# THE TWO QUANTITIES, FROM THE IMPLEMENTATION.
# ---------------------------------------------------------------------------

def stop_from_width(entry_price, w, direction):
    """The stop price at fractional width `w`."""
    entry_price = float(entry_price)
    if direction == LONG:
        return entry_price * (1.0 - float(w))
    if direction == SHORT:
        return entry_price * (1.0 + float(w))
    raise ValueError("direction must be %r or %r, got %r" % (LONG, SHORT,
                                                             direction))


def risk_unit(entry_price, stop, direction, cfg, symbol):
    """PATH TWO's denominator: `sizing.per_unit_denominator` plus `funding_pu`.

    THE SAME ASSEMBLY `portfolio.size_position` PERFORMS at
    `src/engine/portfolio.py:298-299`, composed here from the same two functions
    rather than retyped, and WITHOUT invoking `size_position` itself -- which
    would floor a quantity and solve a target this derivation has no use for.
    """
    return (sizing.per_unit_denominator(entry_price, stop, direction, cfg, symbol)
            + pf.funding_per_unit(entry_price))


def bare_denominator(entry_price, stop, direction, cfg, symbol):
    """The risk unit with the whole unvalidated set removed.

    Config-borne terms are zeroed; funding is omitted -- it is not added. The
    difference against `risk_unit` is therefore the unvalidated sum exactly.
    """
    return sizing.per_unit_denominator(entry_price, stop, direction,
                                       zero_unvalidated(cfg), symbol)


def unvalidated_sum(entry_price, stop, direction, cfg, symbol):
    """THE NUMERATOR, RECOVERED BY DIFFERENCE AND NEVER RESTATED."""
    return (risk_unit(entry_price, stop, direction, cfg, symbol)
            - bare_denominator(entry_price, stop, direction, cfg, symbol))


def ratio_at_width(w, cfg, symbol, direction, entry_price=REFERENCE_PRICE):
    """The constrained ratio at fractional width `w`: unvalidated over risk unit."""
    stop = stop_from_width(entry_price, w, direction)
    return (unvalidated_sum(entry_price, stop, direction, cfg, symbol)
            / risk_unit(entry_price, stop, direction, cfg, symbol))


# ---------------------------------------------------------------------------
# PART A. THE ACHIEVABLE RANGE, ESTABLISHED BEFORE ANY GRID EXISTS.
# ---------------------------------------------------------------------------

def rate_constants(cfg, symbol):
    """`(A, f)` -- the width-independent unvalidated total and the taker rate.

    `A` is the sum of every unvalidated rate, each as a fraction of the price it
    attaches to. It is what the zero-width limit is built from.
    """
    a = sum(rate for _, rate in unvalidated_rates(cfg, symbol).values())
    return float(a), float(cfg.taker_fee)


def limit_ratio_as_width_to_zero(cfg, symbol):
    """THE CEILING. `A / (A + 2f)`, and it is DIRECTION-INDEPENDENT.

    At zero width the stop price equals the entry price, so every term collapses
    onto one price and the direction drops out. The risk unit is then the
    unvalidated total plus two taker legs; the numerator is the unvalidated total.

    IT IS THE SUPREMUM OF THE RATIO OVER POSITIVE WIDTHS, and therefore the
    tolerance above which the constraint imposes no floor at all: the ratio is
    already below such a tolerance at every width, so nothing is required.
    """
    a, f = rate_constants(cfg, symbol)
    return a / (a + 2.0 * f)


def ratio_at_cap(cfg, symbol, direction):
    """The ratio at the frozen stop cap, `cfg.stop_max_pct`. THE OTHER END."""
    return ratio_at_width(float(cfg.stop_max_pct), cfg, symbol, direction)


def achievable_range(cfg, symbol, direction):
    """The open interval of tolerances a width in `(0, cap)` can deliver.

    THE RATIO IS VERIFIED MONOTONE SEPARATELY -- `monotonicity` -- and this
    function's result is only meaningful given that. It is not assumed here.
    """
    return (ratio_at_cap(cfg, symbol, direction),
            limit_ratio_as_width_to_zero(cfg, symbol))


def monotonicity(cfg, symbol, direction, n=20_001):
    """Is the ratio monotone in the width over `(0, cap]`? MEASURED, NOT ASSUMED.

    Returns `(kind, max_step, n)` with `kind` in {"decreasing", "increasing",
    "neither"}, over a dense sweep from just above zero to the cap.
    """
    cap = float(cfg.stop_max_pct)
    widths = np.linspace(cap / n, cap, n)
    values = np.array([ratio_at_width(w, cfg, symbol, direction)
                       for w in widths], dtype=float)
    steps = np.diff(values)
    if np.all(steps < 0.0):
        kind = "decreasing"
    elif np.all(steps > 0.0):
        kind = "increasing"
    else:
        kind = "neither"
    return kind, float(np.max(np.abs(steps))), int(n)


def range_table(cfg, symbols=None):
    """Part A over every symbol-direction cell."""
    symbols = tuple(rs.SYMBOLS) if symbols is None else tuple(symbols)
    rows = []
    for symbol in symbols:
        for direction in DIRECTIONS:
            lo, hi = achievable_range(cfg, symbol, direction)
            kind, step, n = monotonicity(cfg, symbol, direction)
            rows.append({
                "symbol": symbol, "direction": direction,
                "ratio_at_cap": lo, "limit_width_to_zero": hi,
                "monotone": kind, "max_abs_step": step, "sweep_points": n,
            })
    return rows


def common_achievable_range(cfg, symbols=None):
    """The interval every cell can deliver: the highest floor, the lowest ceiling.

    A GRID OUTSIDE THIS INTERVAL WOULD CARRY CELLS WITH NO ADMISSIBLE WIDTH, and
    the report's §2 states which cell fixes each end.
    """
    rows = range_table(cfg, symbols)
    return (max(r["ratio_at_cap"] for r in rows),
            min(r["limit_width_to_zero"] for r in rows))


# ---------------------------------------------------------------------------
# THE GRID. COMMITTED FROM PART A's BOUNDS, BEFORE THE SOLVER EXISTS.
# ---------------------------------------------------------------------------

TAU_STEP = 0.004

TAU_GRID = tuple(round(9 * TAU_STEP + i * TAU_STEP, 10) for i in range(91))
"""0.036 to 0.396 inclusive, step 0.004, ninety-one points.

THE SELECTION RULE, STATED ONCE AND TESTED: the grid is every multiple of the step
lying STRICTLY INSIDE the common achievable interval of `common_achievable_range`.
Both ends are therefore fixed by Part A and by nothing else.

  * THE LOWER END IS FIXED BY THE CELL WITH THE HIGHEST RATIO AT THE CAP.
    Below it that cell would need a width the frozen cap forbids.
  * THE UPPER END IS FIXED BY THE CELL WITH THE LOWEST ZERO-WIDTH LIMIT.
    At or above it that cell's constraint imposes no floor at all.

NOTHING HERE IS CARRIED FROM REPORT 33. Its grid ran 0.030 to 0.120 at step
0.0025 and was chosen so that every cell was satisfiable within the cap under a
DIFFERENT denominator. Both bounds, the step and the count are re-derived here
from this ratio's own achievable range, and a test asserts this grid satisfies the
rule above rather than merely recording the numbers.

THE STEP IS A RESOLUTION CHOICE AND IS NOT DERIVED. It is stated as chosen: it
divides both bounds exactly and yields a grid dense enough to exhibit the curve.
No property of the derivation depends on it."""
