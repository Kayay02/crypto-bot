"""THE UNVALIDATED TERM'S SHARE OF THE RISK UNIT, PER SYMBOL AND DIRECTION.

Sub-point 4.1c, commit two. The threshold this derivation is judged against was
committed ALONE at `af7866d7`, in `docs/design/04_1c_non_uniformity_check.md`
§4, BEFORE this module existed. `git log` is the check.

WHAT THIS ANSWERS. `docs/design/04_1b_tolerance_and_branch.md` §5 declined to
re-denominate the cost-tolerance constraint onto the haircut alone, on the ground
that the haircut sits inside the stop-path cost so constraining the whole
constrains the part. THAT GROUND IS TRUE AND INCOMPLETE: it establishes that the
whole bounds the part, not that it bounds it UNIFORMLY ACROSS SYMBOLS. This
module measures the uniformity.

THE HAIRCUT'S CONTRIBUTION IS TAKEN FROM THE IMPLEMENTATION, NOT RE-DERIVED.
`costs.position_size` is called twice -- once with the frozen configuration and
once with a configuration whose haircut rates are zeroed -- and the difference IS
the haircut's contribution to the denominator. Nothing here restates a cost term,
and a second copy of the algebra could not drift from the engine's because there
is no second copy.

THE WIDTH COMES FROM THE COMMITTED CLOSED FORM. `floor_curve.required_floor_fraction`
is imported and used unchanged; report 32 verified it against the implementation
to 5.662e-15 and this module does not re-verify what is already pinned.

NO TOLERANCE VALUE IS SELECTED. Every quantity is reported ACROSS the committed
grid. Selecting a point on it is forbidden by
`docs/design/04_0_decision_rule.md` §4 and is not done here.

NO OUTCOME QUANTITY, NO ENGINE, NO DATA. This derivation is over rates and
algebra. It opens no file under `data/`, resolves no exit, and invokes no engine
entry point -- asserted by test.
"""

import dataclasses
import os
import sys

import numpy as np
import pandas as pd

from src.analysis import floor_curve as fc
from src.timeframe import resample as rs

sys.path.insert(0, os.path.join(rs.ROOT, "src", "engine"))

import costs  # noqa: E402
import sizing  # noqa: E402

LONG, SHORT = fc.LONG, fc.SHORT
DIRECTIONS = fc.DIRECTIONS

#: The grid committed at `src/analysis/floor_curve.py`, reused unchanged. This
#: module introduces no grid of its own and narrows nothing.
TAU_GRID = fc.TAU_GRID

REFERENCE_PRICE = 1_000.0
"""Entry price cancels from every ratio here, exactly as it cancels from the
required width (report 32 §3.1). A reference price is needed only because the
engine's denominator is stated in price units; a test asserts every reported
share is invariant to it."""


def zero_haircut_config(cfg):
    """The same configuration with every stop haircut set to zero.

    THE INSTRUMENT THAT SEPARATES THE VALIDATED FROM THE UNVALIDATED TERM. The
    haircut's contribution to the denominator is obtained by DIFFERENCE against
    the engine's own answer, so this module never states what the haircut term
    is -- it asks `costs.position_size` twice and subtracts.

    `dataclasses.replace` rather than mutation: the frozen configuration is
    shared and must not be altered by having been measured.
    """
    zeroed = {symbol: 0.0 for symbol in cfg.stop_haircut_bps}
    return dataclasses.replace(cfg, stop_haircut_bps=zeroed)


def _stop_price(entry_price, w, direction):
    """The stop level implied by a width, on the side the direction puts it."""
    if direction == LONG:
        return float(entry_price) * (1.0 - float(w))
    if direction == SHORT:
        return float(entry_price) * (1.0 + float(w))
    raise ValueError("direction must be %r or %r, got %r"
                     % (LONG, SHORT, direction))


def decompose(tau, cfg, symbol, direction, entry_price=REFERENCE_PRICE):
    """Split the constrained ratio into its validated and unvalidated parts.

    At the required floor `w(tau)` for this symbol and direction, returns the
    stop distance, the total cost, the two components, and the share of the RISK
    UNIT each holds.

    THE PROTECTED QUANTITY IS `unvalidated_share_of_risk_unit`. Document
    `04_1b_tolerance_and_branch.md` §3.2 defines what the constraint protects as
    the share of the risk unit determined by estimate rather than by observable
    price geometry, and the risk unit per unit of quantity is the denominator --
    the stop distance PLUS the cost, not the stop distance alone.

    THE TOTAL COST SHARE OF THE RISK UNIT IS `tau / (1 + tau)` AT THIS WIDTH, BY
    CONSTRUCTION, FOR EVERY SYMBOL AND DIRECTION. That is what makes the question
    well posed: the constraint already bounds the total share uniformly, so any
    non-uniformity lives entirely in the unvalidated term's fraction of it.
    """
    w = fc.required_floor_fraction(tau, cfg, symbol, direction)
    entry_price = float(entry_price)
    stop = _stop_price(entry_price, w, direction)
    move = abs(entry_price - stop)

    full = sizing.per_unit_denominator(entry_price, stop, direction, cfg, symbol)
    bare = sizing.per_unit_denominator(entry_price, stop, direction,
                                       zero_haircut_config(cfg), symbol)

    unvalidated = full - bare
    validated = bare - move
    total = full - move

    return {
        "tau": float(tau),
        "symbol": symbol,
        "direction": direction,
        "floor_fraction": w,
        "stop_distance": move,
        "denominator": full,
        "cost_total": total,
        "cost_validated": validated,
        "cost_unvalidated": unvalidated,
        "ratio_total": total / move,
        "ratio_validated": validated / move,
        "ratio_unvalidated": unvalidated / move,
        "unvalidated_fraction_of_cost": unvalidated / total,
        "unvalidated_share_of_risk_unit": unvalidated / full,
        "total_share_of_risk_unit": total / full,
    }


def decomposition_table(cfg, taus=TAU_GRID, symbols=rs.SYMBOLS,
                        entry_price=REFERENCE_PRICE):
    """The decomposition at every grid point, for all six cells."""
    rows = []
    for tau in taus:
        for symbol in symbols:
            for direction in DIRECTIONS:
                rows.append(decompose(tau, cfg, symbol, direction, entry_price))
    return pd.DataFrame(rows)


def decomposition_residual(table):
    """Maximum absolute failure of the two parts to sum to the total.

    VERIFIED RATHER THAN ASSUMED. If the split did not partition the cost term
    exactly, every share below would be wrong by the remainder and nothing else
    in this module would notice.
    """
    parts = (table["ratio_validated"].to_numpy(float)
             + table["ratio_unvalidated"].to_numpy(float))
    return float(np.max(np.abs(parts - table["ratio_total"].to_numpy(float))))


# ---------------------------------------------------------------------------
# THE THRESHOLD, AS COMMITTED AT `af7866d7`. NOT REVISED HERE.
# ---------------------------------------------------------------------------

PROTECTED = "unvalidated_share_of_risk_unit"
"""The column §4 of the committing document denominates the test in."""


def threshold_verdict(table, protected=PROTECTED):
    """Evaluate `docs/design/04_1c_non_uniformity_check.md` §4, as written.

    THE CRITERION, TRANSCRIBED AND NOT REINTERPRETED:

      S(tau)  the spread of the protected quantity across the six
              symbol-direction cells at one tolerance.
      S_max   the maximum of S over the committed grid.
      R(cell) the range of the protected quantity across the grid, for one cell.
      R_min   the minimum of R over the six cells.

      THE TRIGGER FIRES IF AND ONLY IF S_max >= R_min.

    MAXIMUM AGAINST MINIMUM IS DELIBERATELY BIASED TOWARD FIRING -- the most
    adverse spread against the least generous sensitivity -- so a non-firing
    verdict under it is the stronger verdict. §4.4 states that before the answer
    was known.

    THIS FUNCTION TAKES A TABLE RATHER THAN BUILDING ONE, so the criterion can
    be exercised on synthetic inputs either side of it and shown to return both
    verdicts.
    """
    spreads = []
    for tau, group in table.groupby("tau", sort=True):
        values = group[protected].to_numpy(float)
        spreads.append({"tau": float(tau),
                        "spread": float(values.max() - values.min())})
    spread_frame = pd.DataFrame(spreads)
    s_max = float(spread_frame["spread"].max())
    s_max_at = float(spread_frame.loc[spread_frame["spread"].idxmax(), "tau"])

    ranges = []
    for (symbol, direction), group in table.groupby(["symbol", "direction"],
                                                    sort=True):
        values = group[protected].to_numpy(float)
        ranges.append({"symbol": symbol, "direction": direction,
                       "range": float(values.max() - values.min())})
    range_frame = pd.DataFrame(ranges)
    r_min = float(range_frame["range"].min())
    r_min_cell = range_frame.loc[range_frame["range"].idxmin()]

    ratio = s_max / r_min if r_min > 0.0 else float("inf")
    return {
        "s_max": s_max,
        "s_max_at_tau": s_max_at,
        "r_min": r_min,
        "r_min_cell": (str(r_min_cell["symbol"]), str(r_min_cell["direction"])),
        "ratio": ratio,
        "fires": bool(s_max >= r_min),
        "spreads": spread_frame,
        "ranges": range_frame,
    }
