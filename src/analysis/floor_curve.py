"""THE PARAMETRIC STOP FLOOR, AND WHAT FLOOR WIDTH DOES TO THE POPULATION.

Sub-point 4.0, step 3. Governed by `docs/design/04_0_decision_rule.md`, which
this module does not restate and does not soften.

WHAT THIS PRODUCES:

  A. THE REQUIRED STOP FLOOR AS A FUNCTION OF THE TOLERANCE. A closed form in
     the tolerance, per symbol and per direction, solved from the cost algebra
     `src/engine/costs.py` already implements. NOT a set of point values at one
     chosen tolerance -- step 2B section 7 forbids that, because a point set
     embeds a chosen tolerance in the measurement and makes step 2B section 4's
     order rule unenforceable.
  B. THE MAGNITUDE OF THE BREACH document 06 section 5.4 rejected without ever
     stating a numeral.
  C. THE STRUCTURAL STRATIFICATION as a function of the tolerance, on the
     CANDIDATE population only.

WHAT THIS MUST NOT DO, AND DOES NOT:

  * NO TOLERANCE VALUE IS SELECTED. No branch is preferred. No floor is
    recommended. This module computes curves; which point on one governs is
    sub-point 4.1's decision and step 2B section 4 requires the justification to
    be committed before any candidate value is evaluated.
  * NO OUTCOME QUANTITY IS COMPUTED, INSPECTED OR ESTIMATED. Nothing here reads
    an exit reason, simulates an exit, or invokes the portfolio engine. Every
    quantity below is a cost, a price distance, a count or a fraction.
  * THE COST ALGEBRA IS NOT REIMPLEMENTED. The terms are READ from
    `costs.position_size` and the geometry from `sizing.py`, and the closed form
    is VERIFIED against the implementation rather than trusted.

THE DENOMINATION QUESTION, RESOLVED FROM THE IMPLEMENTATION AND NOT BY CHOICE.
Step 2B section 8 anticipated that `c/s <= tolerance` might be under-specified as
to WHICH cost term `c` denominates, since the stop leg fills taker and the target
leg fills maker. It is not under-specified for the ratio report 28 section 9
measured. That ratio is built at `src/analysis/sizing_drag.py:177` as
`(denominator - stop_span) / stop_span`, the denominator being
`costs.position_size`'s, which at `src/engine/costs.py:336` reads

    denom = move + entry * taker_fee + stop * taker_fee + s_entry + s_stop

so `c = denom - move` is the ENTRY TAKER FEE plus the STOP-LEG TAKER FEE plus the
ENTRY SLIPPAGE plus the STOP HAIRCUT. THE MAKER FEE DOES NOT APPEAR IN IT. The
measured ratio is the cost of the STOP PATH, unambiguously.

THAT RESOLVES WHAT WAS MEASURED. IT DOES NOT RESOLVE WHAT THE CONSTRAINT SHOULD
BE DENOMINATED IN, which remains a specification decision owed to 4.1 under step
2B section 8. This module derives the floor that enforces the tolerance on the
ratio as measured, and says so; it does not decide that this is the right ratio
to constrain.

THE HOLDOUT IS SEALED. Every read asserts, immediately before it happens, that
the paths being opened carry no sealed year partition. The assertion is made per
read and never once at the start: a barrier verified once is a barrier assumed
thereafter, which is how the 5.3.3 breach happened.
"""

import os
import sys

import numpy as np
import pandas as pd

from src.timeframe import resample as rs
from src.timeframe import sealed_1m as sealed

sys.path.insert(0, os.path.join(rs.ROOT, "src", "engine"))

import costs  # noqa: E402
import sizing  # noqa: E402

LONG, SHORT = sizing.LONG, sizing.SHORT
DIRECTIONS = (LONG, SHORT)

RISK_USD = 20.0
"""The nominal risk unit the drag is denominated against. Report 28's own
figure; used only as a scale for the granularity fraction, which is invariant to
it up to the lot step."""

# ---------------------------------------------------------------------------
# THE TOLERANCE GRID. COMMITTED AT 12e32a6b, BEFORE THIS SOLVER EXISTED.
#
# `docs/design/04_0_decision_rule.md` section 7 requires the grid to be
# committed before it is solved. A grid chosen after the curve is visible can be
# centred, truncated or refined around the region whose answers are comfortable,
# and no later reader can tell that it was. THE COMMIT HASH IS THE EVIDENCE.
#
# NOTHING BELOW MAY EDIT IT. `_refuse_a_narrowed_grid` runs at import.
# ---------------------------------------------------------------------------

TAU_GRID = tuple(round(0.02 + i * 0.005, 4) for i in range(57))

TAU_GRID_LO = 0.02
TAU_GRID_HI = 0.30
TAU_GRID_STEP = 0.005


def _refuse_a_narrowed_grid():
    """Refuse to import on a grid that has been narrowed or re-centred.

    THE FAILURE THIS CATCHES. Editing the grid after the curves are visible --
    to trim an endpoint, to refine around a region, to drop a point whose answer
    is awkward -- leaves a module that still imports and still produces a curve,
    and no reader can tell the grid moved.
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


# ---------------------------------------------------------------------------
# THE SEALED BARRIER. Asserted immediately before EVERY read.
# ---------------------------------------------------------------------------

class SealedPathRefused(PermissionError):
    """A read was attempted whose path set touches a sealed partition."""


def assert_paths_unsealed(paths, where):
    """Refuse if any path carries a sealed year partition. NEVER CAUGHT HERE.

    ASSERTED IMMEDIATELY BEFORE EACH READ AND NEVER ONCE AT THE START. Report 29
    section 9.1 records a barrier that was verified when armed, silently
    reverted mid-run, and was not re-checked -- and six sealed partitions were
    opened as a result. A barrier verified once is a barrier assumed thereafter.

    Classification is delegated to `sealed_1m.is_sealed_path`, the project's
    single classifier, rather than to a second copy of the year arithmetic.
    """
    bad = [str(p) for p in paths if sealed.is_sealed_path(str(p))]
    if bad:
        raise SealedPathRefused(
            "%s would open %d sealed partition path(s): %s. The readable years "
            "are %s and the holdout is sealed."
            % (where, len(bad), bad, list(sealed.allowed_years())))
    return list(paths)


def _fifteen_minute_path(symbol, derived_dir):
    """The one file the candidate population is read from, per symbol."""
    return os.path.join(derived_dir, "ohlcv_15m", "%s.parquet" % symbol)


# ---------------------------------------------------------------------------
# THE COST TERMS, READ FROM THE IMPLEMENTATION.
# ---------------------------------------------------------------------------

def cost_terms(cfg, symbol):
    """(f, e, h): taker fee, entry slippage fraction, stop haircut fraction.

    READ FROM THE CONFIG THE ENGINE SIZES WITH, never retyped. These are exactly
    the three rates `costs.position_size` multiplies at `src/engine/costs.py`
    lines 330 to 336:

        s_entry = entry * cfg.entry_slippage_bps / 10_000.0
        s_stop  = stop  * cfg.haircut_bps(symbol) / 10_000.0
        denom   = move + entry * cfg.taker_fee + stop * cfg.taker_fee
                       + s_entry + s_stop

    THE HAIRCUT DIFFERS BY SYMBOL -- 5 bps on BTCUSDT and ETHUSDT, 10 bps on
    SOLUSDT -- so the curve differs by symbol through this term and through
    nothing else.
    """
    return (float(cfg.taker_fee),
            float(cfg.entry_slippage_bps) / 10_000.0,
            float(cfg.haircut_bps(symbol)) / 10_000.0)


# ---------------------------------------------------------------------------
# DERIVATION A. The required floor as a function of the tolerance.
# ---------------------------------------------------------------------------

def required_floor_fraction(tau, cfg, symbol, direction):
    """The stop width `w`, as a fraction of entry, at which `c/s` equals `tau`.

    THE DERIVATION, from the denominator above. Write the stop width as a
    fraction `w` of the entry price `P`. The stop price is then `P(1-w)` for a
    long and `P(1+w)` for a short, and the move is `wP`. Substituting into
    `c = denom - move`:

        long   c = P[(2f + e + h) - w(f + h)]
        short  c = P[(2f + e + h) + w(f + h)]

    and `s = wP`, so `P` cancels and `c/s` is a function of `w` alone. Setting
    `c/s = tau` and solving:

        long   w = (2f + e + h) / (tau + f + h)
        short  w = (2f + e + h) / (tau - f - h)

    THE TWO DIRECTIONS DIFFER, AND THE REASON IS GEOMETRIC RATHER THAN A
    CONVENTION. The stop sits BELOW entry on a long and ABOVE it on a short, so
    the taker fee and the haircut -- both charged on the stop price -- are
    smaller on a long and larger on a short at the same width. A short therefore
    needs a wider floor to meet the same tolerance.

    THE SHORT FORM HAS A POLE AT `tau = f + h` and is undefined at or below it:
    no finite stop width meets a tolerance tighter than the stop-leg rate itself,
    because widening the stop raises the cost as fast as it raises the move.
    Returns `float("inf")` there rather than a negative width, which would be a
    silently wrong answer with the right sign flipped.

    `P` CANCELS EXACTLY, so the answer is invariant to the entry price. That is
    asserted numerically by test at three prices spanning two orders of
    magnitude rather than inferred from this docstring.
    """
    f, e, h = cost_terms(cfg, symbol)
    numerator = 2.0 * f + e + h
    if direction == LONG:
        return numerator / (float(tau) + f + h)
    if direction == SHORT:
        denominator = float(tau) - f - h
        if denominator <= 0.0:
            return float("inf")
        return numerator / denominator
    raise ValueError("direction must be %r or %r, got %r"
                     % (LONG, SHORT, direction))


def realised_cost_ratio(entry_price, w, cfg, symbol, direction):
    """`c/s` at a given width, computed THROUGH `costs.position_size`.

    THE VERIFICATION PATH, and it is deliberately not the closed form. It
    reconstructs the ratio the way `sizing_drag.py:177` does -- denominator less
    move, over move -- so the closed form can be checked against the
    implementation rather than against itself.
    """
    entry_price = float(entry_price)
    stop = entry_price * (1.0 - float(w)) if direction == LONG \
        else entry_price * (1.0 + float(w))
    qty = costs.position_size(entry_price, stop, direction, cfg, symbol)
    denominator = float(cfg.risk_usd) / float(qty)
    move = abs(entry_price - stop)
    return (denominator - move) / move


def floor_curve(cfg, symbols=rs.SYMBOLS, taus=TAU_GRID,
                reference_price=1_000.0):
    """The whole curve: required floor width per tolerance, symbol, direction.

    Returns one row per (tau, symbol, direction) with the closed-form width and
    the ratio the implementation returns at that width, so every point carries
    its own verification.
    """
    rows = []
    for tau in taus:
        for symbol in symbols:
            for direction in DIRECTIONS:
                w = required_floor_fraction(tau, cfg, symbol, direction)
                if np.isfinite(w):
                    achieved = realised_cost_ratio(reference_price, w, cfg,
                                                   symbol, direction)
                    residual = achieved - float(tau)
                else:
                    achieved, residual = float("nan"), float("nan")
                rows.append({
                    "tau": float(tau),
                    "symbol": symbol,
                    "direction": direction,
                    "floor_fraction": w,
                    "floor_pct": 100.0 * w,
                    "achieved_cost_ratio": achieved,
                    "residual": residual,
                })
    return pd.DataFrame(rows)


def curve_is_monotone_decreasing(curve, symbol, direction):
    """Is the required width strictly decreasing in the tolerance? VERIFIED.

    STATED AND CHECKED RATHER THAN ASSUMED. The closed form makes it obvious by
    inspection, which is exactly the kind of obviousness this project's defect
    ledger is full of.
    """
    sub = curve[(curve["symbol"] == symbol)
                & (curve["direction"] == direction)].sort_values("tau")
    widths = sub["floor_fraction"].to_numpy(float)
    finite = widths[np.isfinite(widths)]
    if len(finite) < 2:
        return True
    return bool(np.all(np.diff(finite) < 0.0))


def pole(cfg, symbol):
    """`f + h`: the tolerance below which no finite short floor exists."""
    f, _, h = cost_terms(cfg, symbol)
    return f + h


# ---------------------------------------------------------------------------
# DERIVATION B. The magnitude document 06 section 5.4 rejected.
# ---------------------------------------------------------------------------

def rejected_treatment_excess(entry_price, w, cfg, symbol, direction,
                              settlements_crossed, funding_rate):
    """Per-unit excess loss on a stop-out under the treatment 5.4 rejected.

    WHAT 5.4 SAYS, AND WHAT IT DOES NOT. Document 06 section 5.4 rejects
    "charging funding as a realised cash flow per settlement actually crossed",
    on the ground that "it lets a stop-out return worse than -1.0R", and states
    that such a trade "would lose the risk unit plus the funding". IT STATES NO
    NUMERAL.

    THE ABSOLUTE EXCESS IS DETERMINATE FROM THAT SENTENCE. The loss is the risk
    unit PLUS the funding actually paid, so the excess over one risk unit is the
    funding actually paid:

        excess_per_unit = entry_price * funding_rate * settlements_crossed

    THE NORMALISATION IS NOT FULLY DETERMINATE, and this function does not
    resolve it. Expressing the excess as a fraction of a risk unit needs a
    denominator, and 5.4 does not say whether the rejected treatment also removes
    the funding term from the sizing denominator. Both candidates are returned:

        `fraction_of_unit_ex_funding` -- against `d0`, the denominator WITHOUT a
        funding term. This is the reading 5.4's own words support: the rejected
        treatment charges funding as a cash flow INSTEAD OF inside the
        denominator, and "the risk unit plus the funding" reads as a unit that
        does not already contain it.

        `fraction_of_unit_inc_funding` -- against `d0 + entry * rate * 3`, the
        adopted denominator, provided for the reader who takes the other reading.

    THE TWO DIFFER BY UNDER TWO PERCENT OF EACH OTHER at the frozen rate, so no
    conclusion that turns on order of magnitude depends on the choice. THE
    CHOICE IS NOT MADE HERE.

    `d0` IS THE ENGINE'S OWN DENOMINATOR, obtained through
    `sizing.per_unit_denominator`, not reconstructed.
    """
    entry_price = float(entry_price)
    stop = entry_price * (1.0 - float(w)) if direction == LONG \
        else entry_price * (1.0 + float(w))
    d0 = sizing.per_unit_denominator(entry_price, stop, direction, cfg, symbol)

    excess = entry_price * float(funding_rate) * int(settlements_crossed)
    provisioned = entry_price * float(funding_rate) * 3
    return {
        "excess_per_unit": excess,
        "denominator_ex_funding": d0,
        "denominator_inc_funding": d0 + provisioned,
        "fraction_of_unit_ex_funding": excess / d0,
        "fraction_of_unit_inc_funding": excess / (d0 + provisioned),
    }


# ---------------------------------------------------------------------------
# DERIVATION C. Structural stratification, CANDIDATE population only.
# ---------------------------------------------------------------------------

def candidate_population(cfg, derived_dir=rs.DERIVED):
    """The 11,384 candidate positions. EVERY SIGNAL, BEFORE ANY ALLOCATION.

    THE BUDGET IS NOT RUN AND THE ENGINE IS NOT INVOKED. Floor binding is pure
    bar geometry -- the floor binds when `2.25 x ATR` falls below the floor
    width -- so it is decidable on the candidate population with no exits, no
    allocation and no path dependence.

    THE TAKEN POPULATION IS NOT COMPUTED AND CANNOT BE. Report 31 section 5.6
    establishes that under the budget with real exits the traded population is a
    function of realised outcomes and is not knowable in advance.

    THE SEAL IS ASSERTED IMMEDIATELY BEFORE EACH SYMBOL'S READ, not once for the
    loop.
    """
    frames = []
    for symbol in rs.SYMBOLS:
        assert_paths_unsealed([_fifteen_minute_path(symbol, derived_dir)],
                              "candidate_population(%s) 15m read" % symbol)
        assert_paths_unsealed(
            sealed.allowed_paths(symbol, derived_dir=derived_dir),
            "candidate_population(%s) 1m allowed set" % symbol)
        bars, _ = rs.build(symbol, "1h", derived_dir=derived_dir)
        from src.analysis import sweep_population as sp
        from src.analysis import exposure_profile as ep
        frame = sp.analysis_frame(bars, period=ep.DONCHIAN_PERIOD)
        frames.append(ep.positions(frame, symbol, cfg=cfg))
    out = pd.concat(frames, ignore_index=True)
    return rs.assert_sealed(out.sort_values(["ts", "symbol"],
                                            kind="mergesort")
                            .reset_index(drop=True), "candidate_population")


def stratify_at(population, tau, cfg, specs, ticks, risk_usd=RISK_USD):
    """Floor binding and granularity drag at one tolerance, per position.

    THE FLOOR IS PER SYMBOL AND PER DIRECTION, because Derivation A's curve is.
    That is a change of predicate from every prior report, in which the floor was
    a single constant, and the report states it rather than letting the series
    look continuous.

    THE GEOMETRY IS `sizing.py`'s AND IS NOT REIMPLEMENTED. `stop_distance`
    takes the floor fraction as a parameter, which is what makes a parametric
    floor expressible without a second copy of the rule.
    """
    entry = population["entry_price"].to_numpy(float)
    atr = population["atr"].to_numpy(float)
    symbols = population["symbol"].to_numpy()
    directions = population["direction"].to_numpy()
    stamps = population["entry_close_ms"].to_numpy(np.int64)

    n = len(population)
    bound = np.empty(n, dtype=bool)
    drag = np.empty(n, dtype=float)
    width = np.empty(n, dtype=float)

    for i in range(n):
        symbol, direction = symbols[i], directions[i]
        w = required_floor_fraction(tau, cfg, symbol, direction)
        width[i] = w
        if not np.isfinite(w):
            bound[i] = True
            drag[i] = float("nan")
            continue
        bound[i] = bool(sizing.floor_binds(entry[i], atr[i], floor_fraction=w))
        distance = sizing.stop_distance(entry[i], atr[i], floor_fraction=w)
        tick = ticks[symbol].tick_at(int(stamps[i]))
        stop = sizing.stop_price_on_tick(entry[i], distance, direction, tick)
        denominator = sizing.per_unit_denominator(entry[i], stop, direction,
                                                  cfg, symbol)
        unfloored = risk_usd / denominator
        floored = sizing.floor_to_step(unfloored, specs[symbol].qty_step)
        drag[i] = (unfloored - floored) / unfloored if unfloored > 0.0 \
            else float("nan")

    out = population.copy()
    out["tau"] = float(tau)
    out["floor_fraction"] = width
    out["floor_bound"] = bound
    out["drag_fraction"] = drag
    return out


def _fold_windows():
    from src.analysis import sweep_population as sp
    return sp.fold_windows()


def stratification_curve(population, cfg, specs, ticks, taus=TAU_GRID,
                         risk_usd=RISK_USD):
    """Derivation C over the whole grid. Pooled, per symbol, and per fold."""
    windows = _fold_windows()
    stamps = population["ts"].to_numpy(np.int64)
    pooled, per_symbol, per_fold = [], [], []

    for tau in taus:
        sized = stratify_at(population, tau, cfg, specs, ticks, risk_usd)
        bound = sized["floor_bound"].to_numpy(bool)
        drag = sized["drag_fraction"].to_numpy(float)
        pooled.append({
            "tau": float(tau),
            "n": int(len(sized)),
            "floor_bound": int(bound.sum()),
            "floor_bound_fraction": float(bound.mean()),
            "non_floor_bound": int((~bound).sum()),
            "drag_mean": float(np.nanmean(drag)),
        })
        for symbol in rs.SYMBOLS:
            mask = (sized["symbol"] == symbol).to_numpy(bool)
            per_symbol.append({
                "tau": float(tau), "symbol": symbol,
                "n": int(mask.sum()),
                "floor_bound_fraction": float(bound[mask].mean()),
                "non_floor_bound": int((~bound[mask]).sum()),
                "drag_mean": float(np.nanmean(drag[mask])),
            })
        for fold_id, period, lo, hi in windows:
            inw = (stamps >= lo) & (stamps <= hi)
            if not inw.any():
                continue
            per_fold.append({
                "tau": float(tau), "fold_id": fold_id, "period": period,
                "n": int(inw.sum()),
                "floor_bound_fraction": float(bound[inw].mean()),
                "non_floor_bound": int((~bound[inw]).sum()),
            })
    return (pd.DataFrame(pooled), pd.DataFrame(per_symbol),
            pd.DataFrame(per_fold))


TARGET_TO_STOP_RATIO = 1.5
"""THE SCALING IDENTITY, STATED ONCE AND NOT COMPUTED PER TOLERANCE.

The target sits at 1.5 times the stop distance in price terms (thesis section
5.2), so absolute target distance scales linearly with the floor. THIS IS AN
IDENTITY, NOT A MEASUREMENT, and nothing here says anything about whether a
target at that distance is reached -- that is an outcome quantity and is
firewalled."""
