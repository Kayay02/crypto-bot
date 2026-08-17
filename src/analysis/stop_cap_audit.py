"""THE FROZEN STOP CAP, AUDITED. Point 4, report 38.

`src/engine/costs.py`'s `stop_geometry` clamps the raw stop distance at
`cfg.stop_max_pct * entry`. Every analysis in the 4.1 chain supplies 0.035 for
that parameter. **No committed document derives the value, records it as a
judgement, or states what it protects against.**

WHAT THIS MODULE ESTABLISHES, ALL FROM THE IMPLEMENTATION:

  * WHERE THE PARAMETER IS READ, over AST nodes rather than raw text.
  * THE GRANULARITY CONSTRAINT: as the stop widens at fixed risk the solved
    quantity falls, and the venue's lot step consumes a growing share. The width
    at which the minimum lot binds is solved from the risk unit, per symbol, at
    three widely separated entry prices.
  * THE COMMITTED DERIVATION THAT ALREADY EXISTS. `src/sweep/grid.py`'s
    `derived_cap` computes the cap as `(m* + 2.5) x P95(ATR%)` over each training
    fold, per symbol, citing Appendix H. **That rule is committed and it is not
    what supplies 0.035.** This module evaluates it so the two can be compared.
  * THE CLIPPED COUNT at a committed range of candidate cap values.

NO OUTCOME QUANTITY. NO EXIT RESOLVED. THE EXECUTION LOOP IS NOT INVOKED.
Whether a stop clipped narrower than volatility implies is more often hit is an
OUTCOME question and is not computed here; report 38 §5 names it as the
uncomputable side.

NOTHING SEALED IS OPENED. The barrier is asserted immediately before each read,
and bar data is limited to the in-sample window.
"""

import ast
import os
import sys

import numpy as np
import pandas as pd

from src.analysis import floor_curve as fc
from src.analysis import risk_unit_floor_curve as ruf
from src.folds import schedule as sch
from src.sweep import grid as gr
from src.timeframe import resample as rs
from src.timeframe import sealed_1m as sealed

sys.path.insert(0, os.path.join(rs.ROOT, "src", "engine"))

import sizing  # noqa: E402

LONG, SHORT = ruf.LONG, ruf.SHORT
DIRECTIONS = ruf.DIRECTIONS

#: The nominal risk unit the sizing layer divides. `docs/design/00_standing_brief.md` §2.
RISK_USD = fc.RISK_USD

#: Three widely separated entry prices. Quantity depends on price; the binding
#: WIDTH may not, and reporting at three prices is what shows which.
REFERENCE_PRICES = (120.5, 3_000.0, 95_000.0)


# ---------------------------------------------------------------------------
# PART 1. WHERE THE PARAMETER IS READ.
# ---------------------------------------------------------------------------

def read_sites(roots=("src", "tests")):
    """Every site naming `stop_max_pct`, over AST nodes and never raw text.

    Classified by node kind: an attribute read is a live consumption; a string
    literal is usually a dictionary key or a sweep dimension name; a parameter is
    a declaration.
    """
    out = []
    for root in roots:
        base = os.path.join(rs.ROOT, root)
        for folder, dirs, files in os.walk(base):
            dirs[:] = [d for d in dirs if d != "__pycache__"]
            for name in sorted(files):
                if not name.endswith(".py"):
                    continue
                path = os.path.relpath(os.path.join(folder, name), rs.ROOT)
                try:
                    tree = ast.parse(open(os.path.join(rs.ROOT, path)).read())
                except SyntaxError:
                    continue
                for node in ast.walk(tree):
                    kind = None
                    if isinstance(node, ast.Attribute) and \
                            node.attr == "stop_max_pct":
                        kind = "attribute read"
                    elif isinstance(node, ast.Name) and \
                            node.id == "stop_max_pct":
                        kind = "name"
                    elif isinstance(node, ast.arg) and \
                            node.arg == "stop_max_pct":
                        kind = "parameter"
                    elif isinstance(node, ast.keyword) and \
                            node.arg == "stop_max_pct":
                        kind = "keyword argument"
                    elif isinstance(node, ast.Constant) and \
                            node.value == "stop_max_pct":
                        kind = "string literal"
                    if kind:
                        out.append({"path": path, "line": node.lineno,
                                    "kind": kind})
    frame = pd.DataFrame(out).drop_duplicates(subset=["path", "line"])
    return frame.sort_values(["path", "line"]).reset_index(drop=True)


# ---------------------------------------------------------------------------
# PART 2. THE GRANULARITY CONSTRAINT.
# ---------------------------------------------------------------------------

def risk_unit_at_width(w, cfg, symbol, direction, entry_price):
    """The governing risk unit at fractional stop width `w`.

    PATH TWO's denominator, per `docs/design/04_1c_path_and_scope.md` §2.1 --
    `ruf.risk_unit` -- which is what divides the allocation into a quantity.
    """
    stop = ruf.stop_from_width(entry_price, w, direction)
    return ruf.risk_unit(entry_price, stop, direction, cfg, symbol)


def quantity_at_width(w, cfg, symbol, direction, entry_price,
                      risk_usd=RISK_USD):
    """The unfloored quantity at width `w`. Falls as the stop widens."""
    return float(risk_usd) / risk_unit_at_width(w, cfg, symbol, direction,
                                                entry_price)


def granularity_drag_at_width(w, cfg, symbol, direction, entry_price, spec,
                              risk_usd=RISK_USD):
    """The fraction of nominal risk lost to lot flooring at width `w`.

    `sizing.floor_to_step` is CALLED, not reimplemented.
    """
    unfloored = quantity_at_width(w, cfg, symbol, direction, entry_price,
                                  risk_usd)
    floored = sizing.floor_to_step(unfloored, spec.qty_step)
    if unfloored <= 0.0:
        return float("nan")
    return (unfloored - floored) / unfloored


def min_lot_binding_width(cfg, symbol, direction, entry_price, spec,
                          risk_usd=RISK_USD):
    """The width at which the solved quantity falls to ONE minimum lot.

    SOLVED, NOT SEARCHED. The risk unit is affine in the width -- report 36 §3.1
    -- so `risk_unit = risk_usd / min_trade_num` is linear in it. Writing the
    risk unit per unit of entry price as `A + 2f + w (1 + sigma (f + h))` with
    the constants report 36's `form_constants` supplies:

        w* = ( risk_usd / (min_trade_num * entry) - A - 2f )
             / ( 1 + sigma (f + h) )

    Below `w*` the quantity exceeds one lot and the position is viable; at or
    beyond it flooring drives the quantity to a single lot and then to zero,
    which `sizing.viability` refuses as BELOW_MIN_QTY.
    """
    a, f, h, sigma = ruf.form_constants(cfg, symbol, direction)
    entry_price = float(entry_price)
    target_unit = float(risk_usd) / (float(spec.min_trade_num) * entry_price)
    w = (target_unit - a - 2.0 * f) / (1.0 + sigma * (f + h))
    return w


def granularity_table(cfg, specs, widths, prices=REFERENCE_PRICES,
                      symbols=None):
    """Drag and quantity across widths, per symbol, direction and price."""
    symbols = tuple(rs.SYMBOLS) if symbols is None else tuple(symbols)
    rows = []
    for symbol in symbols:
        for direction in DIRECTIONS:
            for price in prices:
                for w in widths:
                    rows.append({
                        "symbol": symbol, "direction": direction,
                        "entry_price": float(price),
                        "width": float(w), "width_pct": 100.0 * float(w),
                        "qty_unfloored": quantity_at_width(
                            w, cfg, symbol, direction, price),
                        "drag_fraction": granularity_drag_at_width(
                            w, cfg, symbol, direction, price, specs[symbol]),
                    })
    return pd.DataFrame(rows)


def min_lot_table(cfg, specs, prices=REFERENCE_PRICES, symbols=None):
    """The min-lot binding width per symbol, direction and price."""
    symbols = tuple(rs.SYMBOLS) if symbols is None else tuple(symbols)
    rows = []
    for symbol in symbols:
        for direction in DIRECTIONS:
            for price in prices:
                w = min_lot_binding_width(cfg, symbol, direction, price,
                                          specs[symbol])
                rows.append({
                    "symbol": symbol, "direction": direction,
                    "entry_price": float(price),
                    "qty_step": float(specs[symbol].qty_step),
                    "min_trade_num": float(specs[symbol].min_trade_num),
                    "binding_width": w, "binding_width_pct": 100.0 * w,
                })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# THE COMMITTED DERIVATION THAT ALREADY EXISTS.
# ---------------------------------------------------------------------------

def derived_cap_table(symbols=None, derived_dir=None):
    """`src/sweep/grid.py`'s `derived_cap`, evaluated per symbol and per fold.

    THE RULE IS COMMITTED AND IS NOT THIS MODULE'S. `grid.derived_cap` states it:
    `(m* + 2.5) x P95(ATR%)` over training-fold breakout bars, citing Appendix H,
    with the stated design intent that at the top grid point **the cap binds when
    ATR% exceeds P95 -- five per cent of bars by construction, and strictly less
    at every lower multiplier.**

    RETURNED AS A FRACTION. `grid.atr_pct` and `grid.stop_min_pct` are both in
    PERCENT, so `derived_cap` returns percent and is divided by one hundred here.

    THE BARRIER IS ASSERTED IMMEDIATELY BEFORE EACH READ. Training windows only,
    which lie wholly inside the in-sample period.
    """
    symbols = tuple(rs.SYMBOLS) if symbols is None else tuple(symbols)
    derived_dir = rs.DERIVED if derived_dir is None else derived_dir
    rows = []
    for symbol in symbols:
        for fold in sch.build_schedule():
            fc.assert_paths_unsealed(
                sealed.allowed_paths(symbol, derived_dir=derived_dir),
                "stop_cap_audit.derived_cap_table(%s fold %d)"
                % (symbol, fold["fold_id"]))
            ind = gr.breakout_frame(symbol, fold["train_start"],
                                    fold["train_end"])
            atr_pct = gr.breakout_atr_pct(ind)
            m, median = gr.m_star(symbol, atr_pct)
            cap_pct, p95 = gr.derived_cap(m, atr_pct)
            rows.append({
                "symbol": symbol, "fold_id": int(fold["fold_id"]),
                "m_star": m, "median_atr_pct": median, "p95_atr_pct": p95,
                "derived_cap_pct": cap_pct,
                "derived_cap_fraction": cap_pct / 100.0,
                "n_breakout_bars": int(len(atr_pct)),
            })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# THE COMMITTED SENSITIVITY RANGE. Fixed before anything is counted over it.
# ---------------------------------------------------------------------------

CAP_STEP = 0.005

CAP_GRID = tuple(round(0.030 + i * CAP_STEP, 10) for i in range(11))
"""0.030 to 0.080 inclusive, step 0.005, eleven points.

THE SELECTION RULE, STATED ONCE: the range spans every computable constraint
this report locates, with one step of margin at each end.

  * THE LOWER END sits one step below the frozen 0.035, so the frozen value is
    interior rather than an endpoint.
  * THE UPPER END sits above the largest committed derived cap this report
    evaluates, so the whole of `grid.derived_cap`'s per-fold, per-symbol range is
    inside the sweep.
  * THE MINIMUM-LOT CONSTRAINT IS NOT SPANNED, because it binds one to two orders
    of magnitude further out; §4 of the report states where, and a range reaching
    it would carry ten points of empty space to no purpose.

THE STEP IS A RESOLUTION CHOICE AND IS NOT DERIVED. No finding depends on it.

COMMITTED IN ITS OWN COMMIT, BEFORE THE COUNTING FUNCTION EXISTS. `clipped_at`
and `sensitivity_table` are absent from the tree that carries this constant."""


def drag_reference_crossings(cfg, specs, symbol, direction, entry_price,
                             references, widths, risk_usd=RISK_USD):
    """The smallest width at which granularity drag first reaches each reference.

    THE CURVE IS A SAWTOOTH, NOT A MONOTONE FUNCTION. Flooring drops the quantity
    to the lot below, so drag falls discontinuously each time a new lot boundary
    is crossed and climbs between them. **"The width at which drag reaches X" is
    therefore a FIRST CROSSING and not a threshold the curve stays above**, and it
    is reported as such.

    The references are supplied by the caller. This module states none of its own:
    `docs/handoff/28_point_5_3_1_sizing.md` §8.2's measured figures are the ones
    report 38 uses, and choosing an ACCEPTABILITY level is a decision this report
    does not make.
    """
    out = {}
    for reference in references:
        hit = None
        for w in widths:
            drag = granularity_drag_at_width(w, cfg, symbol, direction,
                                             entry_price, specs[symbol],
                                             risk_usd)
            if np.isfinite(drag) and drag >= reference:
                hit = float(w)
                break
        out[float(reference)] = hit
    return out


# ---------------------------------------------------------------------------
# PART 5. THE CLIPPED COUNT ACROSS THE COMMITTED RANGE.
# ---------------------------------------------------------------------------

def clipped_at(population, cap_fraction):
    """Candidates whose RAW ATR-derived stop exceeds `cap_fraction * entry`.

    `sizing.STOP_ATR_MULT` is read, not retyped. This is bar geometry: it does
    not depend on the cost tolerance, on the floor, or on any exit, and it is a
    COUNT rather than an outcome quantity.
    """
    entry = population["entry_price"].to_numpy(float)
    atr = population["atr"].to_numpy(float)
    return (sizing.STOP_ATR_MULT * atr) > (float(cap_fraction) * entry)


def sensitivity_table(population, caps=CAP_GRID, symbols=None):
    """Clipped counts per symbol and pooled, at each candidate cap."""
    symbols = tuple(rs.SYMBOLS) if symbols is None else tuple(symbols)
    rows = []
    for cap in caps:
        mask = clipped_at(population, cap)
        for symbol in symbols:
            sel = (population["symbol"].to_numpy() == symbol)
            n = int(sel.sum())
            rows.append({"cap_fraction": float(cap),
                         "cap_pct": 100.0 * float(cap),
                         "cell": symbol, "n": n,
                         "clipped": int((mask & sel).sum()),
                         "clipped_fraction": (float((mask & sel).sum()) / n)
                         if n else float("nan")})
        n = int(len(population))
        rows.append({"cap_fraction": float(cap), "cap_pct": 100.0 * float(cap),
                     "cell": "POOLED", "n": n, "clipped": int(mask.sum()),
                     "clipped_fraction": (float(mask.sum()) / n) if n
                     else float("nan")})
    return pd.DataFrame(rows)
