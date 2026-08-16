"""THE REVISED TOLERANCE GRID. COMMITTED BEFORE THE SOLVER THAT USES IT.

THIS COMMIT CONTAINS THE GRID AND NOTHING ELSE. No solver, no closed form, no
verification. `docs/design/04_0_decision_rule.md` §7 requires a grid to be
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
