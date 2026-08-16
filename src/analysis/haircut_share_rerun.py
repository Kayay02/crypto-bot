"""THE NON-UNIFORMITY CHECK, RE-RUN UNDER THE REVISED DENOMINATION.

Sub-point 4.1a. The question: does the revised tolerance have authority over the
cross-symbol distribution of the protected quantity, or has the problem been
moved rather than fixed?

NOTHING IS REIMPLEMENTED AND NO THRESHOLD IS RETUNED. This module composes two
existing ones and adds no algebra of its own:

  * `haircut_floor_curve.required_floor_fraction` supplies the revised width,
    derived and verified at report 33.
  * `haircut_share.threshold_verdict` supplies the criterion, UNCHANGED from the
    construction committed at `af7866d7` before the original run's numbers
    existed. Reusing the function rather than restating it is what makes the two
    verdicts comparable: a retuned criterion would compare nothing.
  * `sizing.per_unit_denominator` supplies the risk unit, and the unvalidated sum
    is recovered from it BY DIFFERENCE against a zeroed-set configuration.

THE PROTECTED QUANTITY IS UNCHANGED. `docs/design/04_1b_tolerance_and_branch.md`
§3.2 defines it as the share of the RISK UNIT determined by estimate, and that is
what is measured here, exactly as the original run measured it. Only the floor at
which it is evaluated has changed, because the denomination changed.

THE CENTRAL RESULT IS THE CROSS-SYMBOL RATIO'S CONSTANCY, NOT THE VERDICT. Under
the old denomination that ratio was flat to within 1e-12 across a fifteen-fold
parameter range, which is what established that the parameter had zero authority.
The same flatness test is applied here at the same precision.

NO TOLERANCE VALUE IS SELECTED. NO OUTCOME QUANTITY, NO ENGINE, NO DATA -- this
is over rates and algebra and opens no file under `data/`.
"""

import os
import sys

import numpy as np
import pandas as pd

from src.analysis import haircut_floor_curve as hfc
from src.analysis import haircut_share as hs
from src.timeframe import resample as rs

sys.path.insert(0, os.path.join(rs.ROOT, "src", "engine"))

import sizing  # noqa: E402

LONG, SHORT = hfc.LONG, hfc.SHORT
DIRECTIONS = hfc.DIRECTIONS

#: Report 33's committed grid, reused unchanged. This module introduces no grid.
TAU_GRID = hfc.TAU_GRID

#: The column the committed criterion is denominated in. Reused, not restated.
PROTECTED = hs.PROTECTED

REFERENCE_PRICE = hfc.REFERENCE_PRICE

#: The pair the cross-symbol ratio is taken over. BTCUSDT and ETHUSDT share every
#: rate the constraint touches, so the ratio has one degree of freedom and
#: SOLUSDT against either of them is the whole of it.
RATIO_NUMERATOR = "SOLUSDT"
RATIO_DENOMINATOR = "BTCUSDT"


def measure_cell(tau, cfg, symbol, direction, entry_price=REFERENCE_PRICE):
    """The protected quantity at the revised floor, for one cell.

    THE UNVALIDATED SUM IS RECOVERED FROM THE ENGINE BY DIFFERENCE, never
    restated: the denominator with the unvalidated set live, less the same
    denominator with it zeroed.

    `ratio_over_stop` is returned so that every row carries its own verification
    that the width really does solve the constraint it was solved for.
    """
    w = hfc.required_floor_fraction(tau, cfg, symbol, direction)
    entry_price = float(entry_price)
    stop = entry_price * (1.0 - w) if direction == LONG \
        else entry_price * (1.0 + w)
    move = abs(entry_price - stop)

    full = sizing.per_unit_denominator(entry_price, stop, direction, cfg, symbol)
    bare = sizing.per_unit_denominator(entry_price, stop, direction,
                                       hfc.zero_unvalidated(cfg), symbol)
    unvalidated = full - bare
    validated = bare - move

    return {
        "tau": float(tau),
        "symbol": symbol,
        "direction": direction,
        "floor_fraction": w,
        "floor_pct": 100.0 * w,
        "denominator": full,
        "cost_unvalidated": unvalidated,
        "cost_validated": validated,
        "cost_total": full - move,
        "ratio_over_stop": unvalidated / move,
        PROTECTED: unvalidated / full,
        "total_share_of_risk_unit": (full - move) / full,
        "exceeds_cap": bool(w > cfg.stop_max_pct),
    }


def measurement_table(cfg, taus=TAU_GRID, symbols=rs.SYMBOLS,
                      entry_price=REFERENCE_PRICE):
    rows = [measure_cell(tau, cfg, symbol, direction, entry_price)
            for tau in taus for symbol in symbols for direction in DIRECTIONS]
    return pd.DataFrame(rows)


def solve_residual(table):
    """Largest failure of a solved width to reproduce its own tolerance.

    VERIFIED, NOT ASSUMED. If the widths did not solve the constraint, every
    share below would be measured at the wrong floor.
    """
    values = (table["ratio_over_stop"].to_numpy(float)
              - table["tau"].to_numpy(float))
    return float(np.max(np.abs(values)))


def decomposition_residual(table):
    """Largest failure of the validated and unvalidated parts to sum to the
    total cost."""
    parts = (table["cost_validated"].to_numpy(float)
             + table["cost_unvalidated"].to_numpy(float))
    return float(np.max(np.abs(parts - table["cost_total"].to_numpy(float))))


def cross_symbol_ratio(table, direction, numerator=RATIO_NUMERATOR,
                       denominator=RATIO_DENOMINATOR):
    """The protected quantity's cross-symbol ratio, AT EVERY GRID POINT.

    THE CENTRAL QUANTITY OF THIS RE-RUN. Under the old denomination it was a
    constant, which is what established that the parameter had no authority over
    it. Returned per grid point so its constancy is a measurement rather than a
    claim.
    """
    num = table[(table["symbol"] == numerator)
                & (table["direction"] == direction)].sort_values("tau")
    den = table[(table["symbol"] == denominator)
                & (table["direction"] == direction)].sort_values("tau")
    return pd.DataFrame({
        "tau": num["tau"].to_numpy(float),
        "ratio": (num[PROTECTED].to_numpy(float)
                  / den[PROTECTED].to_numpy(float)),
    })


def ratio_is_flat(table, direction, tolerance=1e-12):
    """Is the cross-symbol ratio invariant across the grid?

    THE SAME TEST AT THE SAME PRECISION THE ORIGINAL RUN APPLIED, so that a flat
    result here and a flat result there mean the same thing.
    """
    values = cross_symbol_ratio(table, direction)["ratio"].to_numpy(float)
    return bool(values.max() - values.min() < tolerance)


def ratio_span(table, direction):
    """(min, max, direction of travel) of the cross-symbol ratio."""
    frame = cross_symbol_ratio(table, direction)
    values = frame["ratio"].to_numpy(float)
    rising = bool(np.all(np.diff(values) > 0.0))
    falling = bool(np.all(np.diff(values) < 0.0))
    travel = "rising" if rising else ("falling" if falling else "neither")
    return float(values.min()), float(values.max()), travel


# ---------------------------------------------------------------------------
# THE CAP-CLIPPED STRATUM.
# ---------------------------------------------------------------------------

def cap_crossing_tolerance(cfg, symbol, direction):
    """The tolerance at which the required floor equals the frozen cap.

    Solved from report 33's closed form rather than searched: with `a` the
    stop-attached unvalidated rate and `b` the entry-attached one, the width
    equals the cap when

        long   tau = (a + b) / cap - a        short  tau = (a + b) / cap + a

    Below that tolerance on a long, and below it on a short likewise, the
    required floor exceeds the cap.
    """
    on_stop, on_entry = hfc.unvalidated_rates(cfg, symbol)
    cap = float(cfg.stop_max_pct)
    total = on_stop + on_entry
    return (total / cap - on_stop) if direction == LONG \
        else (total / cap + on_stop)


def cap_clipped_count(table):
    """Grid cells whose required floor exceeds the frozen cap, per cell and
    pooled."""
    per_cell = []
    for (symbol, direction), group in table.groupby(["symbol", "direction"],
                                                    sort=True):
        per_cell.append({
            "symbol": symbol, "direction": direction,
            "n": int(len(group)),
            "exceeds_cap": int(group["exceeds_cap"].sum()),
        })
    return pd.DataFrame(per_cell), int(table["exceeds_cap"].sum())


# ---------------------------------------------------------------------------
# THE VERDICT. The committed criterion, reused unchanged.
# ---------------------------------------------------------------------------

def verdict(table):
    """`haircut_share.threshold_verdict`, applied to the revised table.

    THE CRITERION IS NOT RETUNED AND IS NOT RESTATED HERE -- it is the same
    function object the original run used, so the two verdicts are comparable by
    construction rather than by assertion.
    """
    return hs.threshold_verdict(table, protected=PROTECTED)
