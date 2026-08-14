"""THE TOLERANCE GRID. COMMITTED BEFORE THE SOLVER THAT USES IT EXISTS.

THIS COMMIT CONTAINS THE GRID AND NOTHING ELSE. No solver, no curve, no
stratification, no derivation. `docs/design/04_0_decision_rule.md` §7 requires
that where a numerical solution over a grid of the tolerance parameter is used,
THE GRID IS COMMITTED BEFORE IT IS SOLVED. This file is that commit.

WHY THE ORDER MATTERS AND IS NOT CEREMONY. A grid chosen after the curve is
visible can be centred, truncated or refined around the region whose answers are
comfortable, and no later reader can tell that it was. The grid is a statement
about which questions are asked; committing it first is what makes the answer to
each of them non-optional. It is the same mechanism as step 2B §4's order rule
and the same mechanism as the performance firewall: the commit hash is the
evidence, and it survives everyone's account of what they were thinking.

THE GRID IS NOT NARROWED FROM THE ONE THE STEP SPECIFIED. It runs from 0.02 to
0.30 inclusive in steps of 0.005, which is the suggested grid exactly. Widening
was permitted and narrowing was not; nothing here is narrower.

NO TOLERANCE VALUE IS SELECTED BY THIS FILE OR BY ANYTHING IN THIS STEP. The
grid is the set of tolerances at which the required floor is REPORTED. Which one
governs, or whether any does, is sub-point 4.1's decision under step 2B §3's
two-way fork, and step 2B §4's order rule requires the justification to be
committed before any candidate value is evaluated.
"""

#: The tolerance values at which every curve in this step is reported.
#:
#: 0.02 to 0.30 inclusive, step 0.005, fifty-seven points. The frozen
#: `COST_TOLERANCE_R = 0.11` lies inside it and is not distinguished: it is one
#: grid point among fifty-seven and carries no special status here.
TAU_GRID = tuple(round(0.02 + i * 0.005, 4) for i in range(57))

TAU_GRID_LO = 0.02
TAU_GRID_HI = 0.30
TAU_GRID_STEP = 0.005


def _refuse_a_narrowed_grid():
    """Refuse to import on a grid that has been narrowed or re-centred.

    THE FAILURE THIS CATCHES. Editing the grid after the curves are visible --
    to trim an endpoint, to refine around a region, to drop a point whose answer
    is awkward -- leaves a module that still imports and still produces a curve,
    and no reader can tell the grid moved. These are the only three properties
    the committing document asserted about it, so they are checked where they
    cannot be skipped.
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
