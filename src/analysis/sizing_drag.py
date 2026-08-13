"""What lot flooring costs across 2022-2024, on the real signal population.

WHAT IS BEING ASKED. `src/engine/sizing.py` makes sizing exchange-real: the
quantity is FLOORED to the venue's lot step, the stop and target land on the
price tick, and the target is solved per unit so that flooring cannot move it.
Flooring only ever reduces quantity, so the realised risk of every position sits
BELOW the nominal risk unit. THIS MODULE MEASURES THAT GAP -- the drag -- on the
population reports 24 and 26 already characterised.

TWO POPULATIONS, AND EVERY COUNT NAMES WHICH ONE IT IS:

  * ALL CANDIDATES -- the 11,384 positions the uncapped rule would open
    (report 24). Obtained from `exposure_profile`, unmodified.
  * TAKEN -- the 6,021 the frozen aggregate budget admits (report 26).
    Obtained from `budget_cost`, unmodified, by its `taken` column.

Neither module is altered and neither is re-implemented; this one imports both
and adds a sizing column to their answer.

NOTHING HERE EVALUATES AN EXIT. No bar after a signal bar is read, for any
purpose. No position is paired with a subsequent price. Nothing asks whether a
level was reached. The measurement is a distribution over SIZED POSITIONS at
their entry instant, and the stop and target prices are computed geometry that
is never compared to anything.

THE RISK UNIT IS READ FROM THE FROZEN BUDGET, THROUGH `budget_cost`. This module
does not import the risk package directly -- report 26's narrowed assertion
permits exactly one importer and this is not it -- and it does not retype
$20.00 either. `budget_cost.UNIT_USD` IS the frozen constant's own object.

THE PRICE TICK IS RESOLVED PER BAR. SOLUSDT moved from a 0.0001 grid to a 0.001
grid on 2024-08-14, inside the measurement window, so the tick is looked up by
BAR TIMESTAMP through the contract cache's own schedule. Using one tick per
symbol would round two and a half years of SOL stops and targets onto the wrong
grid.

THE HISTORICAL QUANTITY STEP IS AN ASSUMPTION, NOT A MEASUREMENT. Report 25
section 8 established that no Bitget endpoint publishes lot-size history and
that it cannot be recovered. Every figure here applies TODAY'S steps to
2022-2024 bars. If the 2022 steps were coarser the true drag was larger, and
nothing in this project can say by how much.

THE PERFORMANCE FIREWALL IS ARMED. No expectancy, win rate, profit factor,
Sharpe, Sortino, equity curve, drawdown, r_multiple, net_pnl or gross_pnl is
computed, inspected, estimated or referenced, and a test walks this module's AST
and refuses all twelve names. The sizing module's one recorded carve-out --
`net_proceeds_per_unit` -- is NOT called from here, asserted by test.

THE HOLDOUT IS SEALED and no 1m data is read. The window is inherited whole from
`resample.py` by way of the modules above; this module defines no window
constant of its own.
"""

import os
import sys

import numpy as np
import pandas as pd

from src.analysis import budget_cost as bc
from src.analysis import exposure_profile as ep
from src.analysis import sweep_population as sp
from src.timeframe import resample as rs

sys.path.insert(0, os.path.join(rs.ROOT, "src", "engine"))

import sizing  # noqa: E402


# ---------------------------------------------------------------------------
# Inputs, all read rather than restated.
# ---------------------------------------------------------------------------

RISK_USD = bc.UNIT_USD
"""The frozen risk unit, reached through `budget_cost`, which is the one module
permitted to hold it. Not retyped, and a test asserts it is that object."""

REWARD_TO_RISK = sizing.REWARD_TO_RISK
STOP_ATR_MULT = sizing.STOP_ATR_MULT
STOP_FLOOR_FRACTION = sizing.STOP_FLOOR_FRACTION

COST_TOLERANCE_R = 0.11
"""The frozen cost budget, thesis section 6 and amendment 1 section 6.

TRANSCRIBED AS A COMPARISON THRESHOLD ONLY. Nothing here changes it, and its
disposition -- the closing record section 10.2 flagged that a floor-bound SOLUSDT
stop already charges 0.145-0.148 on the `c/s` reading -- belongs to the
validation design. This step turns an inference into a measured distribution."""

REPORT_24_POSITIONS = 11_384
REPORT_26_TAKEN = 6_021

PERCENTILES = (1, 5, 25, 50, 75, 95, 99)

COLUMNS = ("ts", "symbol", "direction", "taken", "entry_price", "atr",
           "price_tick", "qty_step", "floor_bound", "stop_price",
           "stop_distance_effective", "target_price", "denominator",
           "qty_unfloored", "qty", "nominal_risk_usd", "realised_risk_usd",
           "notional", "notional_unfloored", "drag_fraction",
           "qty_lost_fraction", "notional_lost_fraction",
           "tick_shift_stop_fraction", "tick_shift_target_fraction",
           "cost_over_stop", "viable", "reason")


def cost_config(**kw):
    """Report 24's config, reused. One config object in the project, not two."""
    return ep.cost_config(**kw)


# ---------------------------------------------------------------------------
# The population, from the modules that already own it.
# ---------------------------------------------------------------------------

def population(cfg=None, derived_dir=rs.DERIVED):
    """Report 24's candidates with report 26's `taken` flag. Neither recomputed.

    `budget_cost.measure` runs the frozen allocation over the whole window and
    returns the position table with its `taken` column, which is exactly the two
    populations this step reports on. Calling it is cheaper than reproducing it
    and cannot disagree with it.
    """
    cfg = cost_config() if cfg is None else cfg
    result = bc.measure(cfg=cfg, derived_dir=derived_dir)
    return result["positions"], result["windows"]


def size_population(positions, cfg=None, risk_usd=RISK_USD,
                    specs=None, schedules=None):
    """Apply the new sizing to every candidate. One row in, one row out.

    THE TICK IS RESOLVED BY BAR TIMESTAMP, not by symbol alone -- see the module
    docstring. `TickSchedule.tick_at` is the contract module's own lookup.
    """
    cfg = cost_config() if cfg is None else cfg
    specs = sizing.load_symbol_specs() if specs is None else specs
    schedules = sizing.load_tick_schedules() if schedules is None else schedules

    rows = []
    for rec in positions.itertuples(index=False):
        tick = schedules[rec.symbol].tick_at(int(rec.ts))
        sized = sizing.size(rec.entry_price, rec.atr, rec.direction,
                            rec.symbol, specs[rec.symbol], cfg, tick,
                            risk_usd=risk_usd)
        notional_unfloored = sized.qty_unfloored * sized.entry_price
        stop_span = sized.stop_distance_effective
        rows.append({
            "ts": int(rec.ts),
            "symbol": rec.symbol,
            "direction": rec.direction,
            "taken": bool(getattr(rec, "taken", True)),
            "entry_price": sized.entry_price,
            "atr": sized.atr,
            "price_tick": sized.price_tick,
            "qty_step": sized.qty_step,
            "floor_bound": sized.floor_bound,
            "stop_price": sized.stop_price,
            "stop_distance_effective": stop_span,
            "target_price": sized.target_price,
            "denominator": sized.denominator,
            "qty_unfloored": sized.qty_unfloored,
            "qty": sized.qty,
            "nominal_risk_usd": sized.nominal_risk_usd,
            "realised_risk_usd": sized.realised_risk_usd,
            "notional": sized.notional,
            "notional_unfloored": notional_unfloored,
            "drag_fraction": (sized.nominal_risk_usd - sized.realised_risk_usd)
                             / sized.nominal_risk_usd,
            "qty_lost_fraction": (sized.qty_unfloored - sized.qty)
                                 / sized.qty_unfloored,
            "notional_lost_fraction": (notional_unfloored - sized.notional)
                                      / notional_unfloored,
            "tick_shift_stop_fraction": sized.tick_shift_stop / stop_span,
            "tick_shift_target_fraction": sized.tick_shift_target / stop_span,
            # `c/s`: the cost term as a fraction of the stop term. The
            # denominator is the move PLUS the cost legs, so the cost legs are
            # the denominator less the move.
            "cost_over_stop": (sized.denominator - stop_span) / stop_span,
            "viable": sized.viable,
            "reason": sized.reason,
        })
    out = pd.DataFrame(rows, columns=list(COLUMNS))
    return rs.assert_sealed(out, "size_population")


# ---------------------------------------------------------------------------
# Summaries.
# ---------------------------------------------------------------------------

def summary(values, percentiles=PERCENTILES):
    """min, the percentiles, max, mean and n."""
    x = np.asarray(values, dtype=float)
    x = x[np.isfinite(x)]
    out = {"n": int(len(x))}
    if not len(x):
        out["min"] = out["max"] = out["mean"] = float("nan")
        for p in percentiles:
            out["p%s" % p] = float("nan")
        return out
    out["min"] = float(x.min())
    out["max"] = float(x.max())
    out["mean"] = float(x.mean())
    for p in percentiles:
        out["p%s" % p] = float(np.percentile(x, p))
    return out


def viability_counts(frame):
    """How many positions each refusal reason accounts for.

    BOTH ARE EXPECTED TO BE ZERO and both are REPORTED AS ZERO rather than
    omitted. A branch that is never reported is a branch nobody can tell was
    checked.
    """
    return {
        "n": int(len(frame)),
        "n_viable": int(frame["viable"].sum()) if len(frame) else 0,
        sizing.BELOW_MIN_QTY: int((frame["reason"] == sizing.BELOW_MIN_QTY).sum())
                              if len(frame) else 0,
        sizing.BELOW_MIN_NOTIONAL: int(
            (frame["reason"] == sizing.BELOW_MIN_NOTIONAL).sum())
            if len(frame) else 0,
    }


def drag_totals(frame):
    """The pooled drag, in dollars and as a fraction of nominal risk.

    TWO POOLED FORMS, AND THEY ARE NOT THE SAME NUMBER:

      `drag_fraction`            total risk lost / total nominal risk. Because
                                 every position carries the same $20.00 nominal
                                 unit, this equals the UNWEIGHTED MEAN of the
                                 per-position fractions.
      `notional_lost_weighted`   total notional lost / total unfloored notional,
                                 which is NOTIONAL-WEIGHTED. THIS IS THE FORM
                                 REPORT 24 SECTION 2.2 MEASURED, and it is the
                                 one to compare against its 0.21 / 1.26 / 0.67.

    The two differ because a large-notional position and a small one carry the
    same risk unit but not the same notional. Reporting only one of them and
    comparing it to report 24's would be comparing two different quantities.
    """
    if not len(frame):
        return {"nominal_total": 0.0, "realised_total": 0.0,
                "drag_total": 0.0, "drag_fraction": float("nan"),
                "notional_total": 0.0, "notional_unfloored_total": 0.0,
                "notional_lost_weighted": float("nan"), "n": 0}
    nominal = float(frame["nominal_risk_usd"].sum())
    realised = float(frame["realised_risk_usd"].sum())
    notional = float(frame["notional"].sum())
    notional_unfloored = float(frame["notional_unfloored"].sum())
    return {
        "n": int(len(frame)),
        "nominal_total": nominal,
        "realised_total": realised,
        "drag_total": nominal - realised,
        "drag_fraction": (nominal - realised) / nominal if nominal else
                         float("nan"),
        "notional_total": notional,
        "notional_unfloored_total": notional_unfloored,
        "notional_lost_weighted": (notional_unfloored - notional)
                                  / notional_unfloored if notional_unfloored
                                  else float("nan"),
    }


def cost_ratio_report(frame, tolerance=COST_TOLERANCE_R):
    """The `c/s` distribution, stratified by whether the 1.50% floor bound.

    REPORTED, NOT RESOLVED. The thesis freezes the tolerance at 0.11 and the
    closing record section 10.2 already flagged that a floor-bound SOLUSDT stop
    charges more than that. This turns the inference into a distribution and a
    count; what to do about it belongs to the validation design.
    """
    if not len(frame):
        return {"all": summary([]), "floor_bound": summary([]),
                "not_floor_bound": summary([]), "n_above_tolerance": 0,
                "fraction_above_tolerance": float("nan"),
                "tolerance": float(tolerance), "n": 0}
    c_over_s = frame["cost_over_stop"].to_numpy(float)
    bound = frame["floor_bound"].to_numpy(bool)
    above = c_over_s > tolerance
    return {
        "n": int(len(frame)),
        "tolerance": float(tolerance),
        "all": summary(c_over_s),
        "floor_bound": summary(c_over_s[bound]),
        "not_floor_bound": summary(c_over_s[~bound]),
        "n_above_tolerance": int(above.sum()),
        "fraction_above_tolerance": float(above.sum()) / len(frame),
        "n_floor_bound": int(bound.sum()),
        "n_above_and_floor_bound": int((above & bound).sum()),
        "n_above_not_floor_bound": int((above & ~bound).sum()),
    }


def profile(frame):
    """Every distribution the report states, for one population."""
    return {
        "n": int(len(frame)),
        "realised_risk_usd": summary(frame["realised_risk_usd"]),
        "drag_fraction": summary(frame["drag_fraction"]),
        "qty_lost_fraction": summary(frame["qty_lost_fraction"]),
        "notional_lost_fraction": summary(frame["notional_lost_fraction"]),
        "notional": summary(frame["notional"]),
        "tick_shift_stop_fraction": summary(frame["tick_shift_stop_fraction"]),
        "tick_shift_target_fraction": summary(
            frame["tick_shift_target_fraction"]),
        "totals": drag_totals(frame),
        "viability": viability_counts(frame),
        "cost_ratio": cost_ratio_report(frame),
    }


# ---------------------------------------------------------------------------
# The whole pass.
# ---------------------------------------------------------------------------

def measure(cfg=None, derived_dir=rs.DERIVED, risk_usd=RISK_USD):
    """Both populations, per symbol per fold period and pooled."""
    cfg = cost_config() if cfg is None else cfg
    positions, windows = population(cfg=cfg, derived_dir=derived_dir)
    sized = size_population(positions, cfg=cfg, risk_usd=risk_usd)

    taken = sized[sized["taken"]].reset_index(drop=True)
    out = {
        "risk_usd": float(risk_usd),
        "reward_to_risk": float(REWARD_TO_RISK),
        "sized": sized,
        "windows": windows,
        "populations": {
            "candidates": profile(sized),
            "taken": profile(taken),
        },
        "per_symbol": {"candidates": {}, "taken": {}},
        "per_fold": {"candidates": {}, "taken": {}},
        "specs": {s: vars(v) for s, v in sizing.load_symbol_specs().items()},
    }

    for name, frame in (("candidates", sized), ("taken", taken)):
        for symbol in rs.SYMBOLS:
            sub = frame[frame["symbol"] == symbol].reset_index(drop=True)
            out["per_symbol"][name][symbol] = profile(sub)
        ts = frame["ts"].to_numpy(np.int64)
        for fold_id, period, lo, hi in windows:
            inw = (ts >= lo) & (ts <= hi)
            sub = frame.loc[inw].reset_index(drop=True)
            out["per_fold"][name][(fold_id, period)] = {
                "pooled": profile(sub),
                "per_symbol": {
                    symbol: profile(
                        sub[sub["symbol"] == symbol].reset_index(drop=True))
                    for symbol in rs.SYMBOLS},
            }
    return out


def fold_windows():
    """The tracked fold boundaries, from report 21's own reader."""
    return sp.fold_windows()
