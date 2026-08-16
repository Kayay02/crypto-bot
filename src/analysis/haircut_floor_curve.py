"""THE REVISED STOP FLOOR: THE UNVALIDATED FRICTION TERMS OVER THE STOP DISTANCE.

Sub-point 4.1a, the revised derivation. The denomination this solves under was
committed at `02992c7a`; the grid below was committed ALONE at `532e9334`,
before this solver existed. `git log` is the check on both.

WHAT THIS SOLVES. `docs/design/04_1a_denomination_amendment_1.md` §3.1 binds the
constraint to the unvalidated term's contribution over the stop distance --
numerator narrowed, denominator unchanged. This module derives the required stop
width as a function of that tolerance, per symbol and per direction, and VERIFIES
it against `costs.position_size` rather than against itself.

THE NUMERATOR IS DEFINED BY PRINCIPLE, NOT BY ENUMERATION. It is the sum of the
cost model's UNVALIDATED friction terms. At this commit that sum has exactly one
non-zero member -- the stop haircut -- because `entry_slippage_bps` is 0.0 at
`src/engine/costs.py:71`. It is implemented as a sum over a NAMED SET so that a
later non-zero slippage model JOINS the constrained quantity rather than escaping
it. `docs/design/04_0_divergence_disposition_amendment_2.md` §7 adopts a standing
rule against scopes stated by enumeration, and this is that rule applied.

REPORT 32'S FORM IS NOT CARRIED OVER BY ANALOGY. The fee terms leaving the
numerator changes the algebra's shape and moves the pole, and both are derived
here rather than assumed.

NO TOLERANCE VALUE IS SELECTED. No non-uniformity verdict is returned -- that is
the next step's question, against its own committed threshold.

NO OUTCOME QUANTITY, NO ENGINE, NO DATA. This derivation is over rates and
algebra and opens no file under `data/`.

THE GRID, COMMITTED SEPARATELY AND FIRST. `docs/design/04_0_decision_rule.md` §7 requires a grid to be
committed before it is solved, and the same discipline is applied here even
though a closed form exists, because the grid is what the curve is REPORTED over
and a grid trimmed after the curve is visible is a grid nobody can audit.

THE GRID IS CHOSEN FROM THE ALGEBRA, NOT FROM REPORT 32. The revised ratio --
the unvalidated friction terms over the stop distance -- is a DIFFERENT quantity
from the one report 32 solved, with a different achievable range and a pole in a
different place. Reusing report 32's 0.02 to 0.30 grid because it is the one that
exists would be the recurring defect class: a range carried over by analogy
rather than derived from the quantity it ranges over.

KNOWING THE ALGEBRA BEFORE FIXING THE GRID IS REQUIRED HERE, NOT A LEAK. The
bounds below are derived FROM the closed form's structure -- where it meets the
frozen stop cap and where it falls under the frozen floor -- which is the method
this step specifies. What the order protects is that the grid is fixed before the
curve is reported over it.

THE TWO BOUNDS, AND WHAT FIXES THEM:

  LOWER, 0.030. `costs.stop_geometry` caps the stop distance at
  `cfg.stop_max_pct * entry` -- frozen at 0.035 -- so a required floor wider than
  that collides with the cap and cannot be honoured. The most demanding cell
  reaches that cap just below 0.0296, so 0.030 is the first clean grid point at
  which EVERY cell is satisfiable within the frozen cap.

  UPPER, 0.120. Running the other way, the required width falls; the most
  demanding cell drops below the thesis's frozen 1.50% floor just below 0.0677.
  0.120 carries the grid comfortably past that for every cell, so the grid
  BRACKETS both structural boundaries rather than stopping at one of them.

  STEP, 0.0025. Thirty-seven points across a range about a third as wide as
  report 32's, so the resolution in the reported quantity is comparable.

THE POLE IS OUTSIDE THE GRID AND THAT IS DELIBERATE. The short-leg form is
undefined at and below a tolerance equal to the haircut rate itself. Both poles
sit far below the lower bound, so no grid point approaches one; the solver is
still required to return infinity there rather than a negative width, and a test
probes it.

NO TOLERANCE VALUE IS SELECTED BY THIS FILE OR BY ANYTHING IN THIS STEP.
"""

import dataclasses
import os
import sys

import numpy as np
import pandas as pd

from src.timeframe import resample as rs

sys.path.insert(0, os.path.join(rs.ROOT, "src", "engine"))

import costs  # noqa: E402
import sizing  # noqa: E402

LONG, SHORT = sizing.LONG, sizing.SHORT
DIRECTIONS = (LONG, SHORT)

#: The revised tolerances at which the curve is reported. 0.030 to 0.120
#: inclusive, step 0.0025, thirty-seven points.
TAU_GRID = tuple(round(0.030 + i * 0.0025, 6) for i in range(37))

TAU_GRID_LO = 0.030
TAU_GRID_HI = 0.120
TAU_GRID_STEP = 0.0025


def _refuse_a_narrowed_grid():
    """Refuse to import on a grid whose endpoints or step have moved.

    THE FAILURE THIS CATCHES. Trimming an endpoint or refining around a region
    after the curve is visible leaves a module that still imports and still
    produces a curve, and no reader can tell the grid moved.
    """
    if TAU_GRID[0] != TAU_GRID_LO:
        raise ValueError("the grid no longer starts at %r; it starts at %r"
                         % (TAU_GRID_LO, TAU_GRID[0]))
    if TAU_GRID[-1] != TAU_GRID_HI:
        raise ValueError("the grid no longer ends at %r; it ends at %r"
                         % (TAU_GRID_HI, TAU_GRID[-1]))
    for a, b in zip(TAU_GRID, TAU_GRID[1:]):
        if abs((b - a) - TAU_GRID_STEP) > 1e-12:
            raise ValueError(
                "the grid is not uniform at step %r: %r follows %r"
                % (TAU_GRID_STEP, b, a))


_refuse_a_narrowed_grid()


REFERENCE_PRICE = 1_000.0
"""Entry price cancels from the ratio and from the width. A reference price is
needed only because the engine states its denominator in price units; a test
asserts invariance at three widely separated prices."""

# ---------------------------------------------------------------------------
# THE UNVALIDATED SET. A SET, NOT A TERM.
# ---------------------------------------------------------------------------

UNVALIDATED_TERMS = {
    "stop_haircut_bps": "stop",
    "entry_slippage_bps": "entry",
}
"""The cost model's unvalidated friction terms, and the price each is charged on.

WHY A SET AND NOT THE ONE TERM THAT IS CURRENTLY NON-ZERO. `entry_slippage_bps`
is 0.0 today, so the sum has one effective member. But `src/engine/costs.py`
records that it "exists as a config value purely so it can be sensitivity-tested
later", so a non-zero value is anticipated by the cost model itself. A numerator
naming only the haircut would let that term escape the constraint at exactly the
moment it started to matter.

THE ATTACHMENT POINT IS PART OF THE DEFINITION, not decoration: a term charged on
the STOP price and one charged on the ENTRY price enter the closed form
differently, because the stop price moves with the width and the entry price does
not. `src/engine/costs.py:330` charges entry slippage on `entry` and line 331
charges the haircut on `stop`.
"""


def zero_unvalidated(cfg):
    """The same configuration with every member of the unvalidated set zeroed.

    THE INSTRUMENT THAT ISOLATES THE NUMERATOR. The unvalidated sum is obtained
    by DIFFERENCE against the engine's own denominator, so this module never
    states what those terms are -- it asks `costs.position_size` twice and
    subtracts. `dataclasses.replace` rather than mutation: the frozen
    configuration is shared and must not be altered by having been measured.
    """
    fields = {}
    for name in UNVALIDATED_TERMS:
        current = getattr(cfg, name)
        fields[name] = ({key: 0.0 for key in current}
                        if isinstance(current, dict) else 0.0)
    return dataclasses.replace(cfg, **fields)


def unvalidated_rates(cfg, symbol):
    """(on_stop, on_entry): the unvalidated rates, summed by attachment point.

    READ FROM THE CONFIG, never retyped. A term whose attachment point is not
    one this module knows how to place raises rather than being dropped, because
    a silently omitted term is exactly what the set exists to prevent.
    """
    on_stop, on_entry = 0.0, 0.0
    for name, attaches_to in UNVALIDATED_TERMS.items():
        value = getattr(cfg, name)
        rate = (float(value[symbol]) if isinstance(value, dict)
                else float(value)) / 10_000.0
        if attaches_to == "stop":
            on_stop += rate
        elif attaches_to == "entry":
            on_entry += rate
        else:
            raise ValueError("unknown attachment point %r for %r"
                             % (attaches_to, name))
    return on_stop, on_entry


# ---------------------------------------------------------------------------
# THE CLOSED FORM, DERIVED RATHER THAN CARRIED OVER.
# ---------------------------------------------------------------------------

def required_floor_fraction(tau, cfg, symbol, direction):
    """The stop width `w` at which the unvalidated sum over the stop distance
    equals `tau`.

    THE DERIVATION. Write the width as a fraction `w` of entry price `P`, so the
    stop price is `P(1-w)` on a long and `P(1+w)` on a short and the stop
    distance is `s = wP`. With `a` the unvalidated rate charged on the STOP price
    and `b` the unvalidated rate charged on the ENTRY price, the numerator is

        long   U = P(1-w)a + Pb        short  U = P(1+w)a + Pb

    so `P` cancels from `U / s` and

        long   U/s = [a + b - wa] / w    short  U/s = [a + b + wa] / w

    Setting each equal to `tau` and solving:

        long   w = (a + b) / (tau + a)
        short  w = (a + b) / (tau - a)

    A DIRECTION SPLIT STILL ARISES, AND ITS DRIVER HAS CHANGED. Under report 32
    both the taker fee and the haircut were charged on the stop price and both
    fed the split. Here only the stop-attached unvalidated rate does, so the
    split is driven by `a` alone. WHAT WOULD HAVE SHOWN NO SPLIT: the two forms
    coinciding, which happens only when `a` is zero -- that is, when no
    unvalidated term is charged on the stop price at all. It is not.

    THE POLE HAS MOVED. The short form is undefined at `tau = a`, where report
    32's sat at the taker fee plus the haircut. Returns infinity there rather
    than a negative width, which would be a wrong answer with the sign flipped.
    """
    on_stop, on_entry = unvalidated_rates(cfg, symbol)
    numerator = on_stop + on_entry
    if direction == LONG:
        return numerator / (float(tau) + on_stop)
    if direction == SHORT:
        denominator = float(tau) - on_stop
        if denominator <= 0.0:
            return float("inf")
        return numerator / denominator
    raise ValueError("direction must be %r or %r, got %r"
                     % (LONG, SHORT, direction))


def pole(cfg, symbol):
    """The tolerance below which no finite short-leg width exists."""
    on_stop, _ = unvalidated_rates(cfg, symbol)
    return on_stop


def realised_unvalidated_ratio(entry_price, w, cfg, symbol, direction):
    """`U / s` at a given width, computed THROUGH `costs.position_size`.

    THE VERIFICATION PATH, and deliberately not the closed form. The unvalidated
    sum is the engine's denominator less the engine's denominator with the set
    zeroed, so the closed form is checked against the implementation rather than
    against itself.
    """
    entry_price = float(entry_price)
    stop = entry_price * (1.0 - float(w)) if direction == LONG \
        else entry_price * (1.0 + float(w))
    full = sizing.per_unit_denominator(entry_price, stop, direction, cfg, symbol)
    bare = sizing.per_unit_denominator(entry_price, stop, direction,
                                       zero_unvalidated(cfg), symbol)
    return (full - bare) / abs(entry_price - stop)


def floor_curve(cfg, symbols=rs.SYMBOLS, taus=TAU_GRID,
                entry_price=REFERENCE_PRICE):
    """The whole curve, every point carrying its own verification."""
    rows = []
    for tau in taus:
        for symbol in symbols:
            for direction in DIRECTIONS:
                w = required_floor_fraction(tau, cfg, symbol, direction)
                if np.isfinite(w):
                    achieved = realised_unvalidated_ratio(entry_price, w, cfg,
                                                          symbol, direction)
                    residual = achieved - float(tau)
                else:
                    achieved, residual = float("nan"), float("nan")
                rows.append({
                    "tau": float(tau), "symbol": symbol,
                    "direction": direction,
                    "floor_fraction": w, "floor_pct": 100.0 * w,
                    "achieved_ratio": achieved, "residual": residual,
                })
    return pd.DataFrame(rows)


def curve_is_monotone_decreasing(curve, symbol, direction):
    """Is the required width strictly decreasing in the tolerance? VERIFIED.

    The closed form makes it look obvious, which is exactly the kind of
    obviousness this project's defect ledger is full of.
    """
    sub = curve[(curve["symbol"] == symbol)
                & (curve["direction"] == direction)].sort_values("tau")
    widths = sub["floor_fraction"].to_numpy(float)
    finite = widths[np.isfinite(widths)]
    if len(finite) < 2:
        return True
    return bool(np.all(np.diff(finite) < 0.0))


def max_residual(curve):
    """Largest absolute failure of a solved width to reproduce its tolerance."""
    values = curve["residual"].to_numpy(float)
    finite = values[np.isfinite(values)]
    return float(np.max(np.abs(finite))) if len(finite) else float("nan")
