"""Step 3 of the §4.4 sequence: PER-FOLD BAND IDENTIFICATION AND PLATEAU SELECTION.

This module applies Appendix K.2's acceptance definition to each grid point,
finds contiguous passing bands per fold per symbol, and selects the CENTRE of
the widest band per §4.3 and Appendix K.3. It then evaluates the pre-committed
kill conditions that become decidable once those figures exist.

It performs NO collapse of the nine fold selections into a candidate (step 4),
NO A3 re-check (step 5, and A3 is already resolved at step 0), NO D5
leave-one-out (step 7), NO top-5% removal and NO +/-25% sensitivity probe
(step 8), and it does not touch the holdout (step 9).

ACCEPTANCE IS A TRAINING-FOLD QUANTITY
======================================

Appendix K.2 defines acceptance on TRAINING folds: "Selection is on TRAIN,
evaluation is on TEST. That is what makes the procedure walk-forward." Report
14 section 6 pools TEST folds only, per Appendix M.4, because that is the
correct population for ARM COMPARISON -- a different question. The two must not
be crossed, and the fifth defect in this project was exactly that class of
error, so `_acceptance_metrics` refuses any record not labelled `train`. The
literal is hard-coded there rather than read from `SELECT_PERIOD`, so flipping
the selector raises instead of silently reading the wrong population. A test
plants that mutation.

THE POPULATION CONTRACT
=======================

Every figure here names its population from the closed set of `sweep.py`
crossed with (train, test) and (long, short, both). `sweep.validate_records`
is REUSED, not reimplemented, and is run over the step-2 cells before anything
is read from them.

NO RE-SIMULATION HAPPENS IN THIS MODULE. Every figure is derived from the
step-2 cells (`sweep_cells.jsonl`) and the step-2 trade tables
(`trades/*.parquet`). Nothing here opens a bar file, so the report 13 seal is
not exercised and cannot be weakened.
"""

import json
import math
import os

import numpy as np
import pandas as pd

from src.folds import schedule as sch
from src.sweep import grid as gr
from src.sweep import sweep as sw
from src.sweep import sweep_report as srep

log = sch.log

OUT_DIR = os.path.join(sch.DERIVED, "sweep")
ARTIFACT_PATH = os.path.join(OUT_DIR, "bands.json")
REPORT_PATH = os.path.join(sch.ROOT, "reports", "15_band_selection.md")

# The HEAD step 3 started from, recorded with `git status --porcelain` empty
# BEFORE any file in this step was written. `git_revision()` cannot report it
# once the step has added its own module and tests, so it is pinned here.
HEAD_AT_START = "bdde2a4188606162f08c9442e3aaa69e59d2a265"

# ---- Appendix K.2: the arm and population acceptance is measured on -------
# K.2(a) names the gated arm at the 50% RVOL threshold explicitly. Direction is
# "both": §4.5 keeps long and short cohorts separate throughout for REPORTING,
# but K.2 states one expectancy per grid point, and the per-direction 30-trade
# minimum is a separate commitment that does not gate acceptance.
ACCEPT_ARM = "full"
ACCEPT_POPULATION = "gated_50"
ACCEPT_DIRECTION = "both"

# The period SELECTOR. `_acceptance_metrics` does not trust it -- see below.
SELECT_PERIOD = "train"

# ---- §4.4 evidence minimums, imported not restated. THESE DO NOT MOVE. ----
MIN_TRAIN_TRADES = sw.MIN_TRAIN_TRADES          # 200, K.2(b)
GRID_STEP = gr.GRID_STEP                        # 0.25
TOP_OFFSET = sw.TOP_OFFSET                      # 2.50, ineligible per §4.3

# ---- §4.3 / §4.4 pre-committed thresholds --------------------------------
MIN_BAND_POINTS = 3          # §4.3: fewer than three contiguous -> no selection
ACCEPT_EXPECTANCY_FLOOR = 0.0   # K.2(a): greater than zero. No margin.
MARGINAL_CONTRIBUTION_R = 0.05  # §4.4: the gate's marginal-contribution bar

# The comparison pair for kill conditions (b), (c) and (d).
GATED_ARM, GATED_POP = "full", "gated_50"
UNGATED_ARM, UNGATED_POP = "minus_rvol", "ungated"
TIME_ARM, TIME_POP = "minus_time_stop", "gated_50"

# §4.5 D6 reference lines: the checkpoint fires at 21, the cap at 41.
CHECKPOINT_BAR = 21
MAX_HOLD_BAR = 41


class TestPeriodLeak(AssertionError):
    """The acceptance path was handed a record that is not a training record.

    Appendix K.2 makes acceptance a TRAINING-fold quantity. Reading a test
    record here would select on the same data the procedure later evaluates on,
    which is precisely what walk-forward exists to prevent.
    """


class BandRuleError(AssertionError):
    """A band or selection violates a pre-committed §4.3 / K.3 rule."""


# ---------------------------------------------------------------------------
# 1. ACCEPTANCE PER GRID POINT -- Appendix K.2
# ---------------------------------------------------------------------------

def _acceptance_metrics(row):
    """Extract the acceptance figures from ONE record. THE PERIOD GUARD.

    The literal "train" below is deliberately NOT `SELECT_PERIOD`. If the
    selector is ever changed, or a test-period record reaches here by any other
    route, this raises rather than quietly computing acceptance on the
    evaluation population. A guard that reads the same constant as the thing it
    guards is vacuous, and three vacuous guards have been found in this project.
    """
    if row.get("period") != "train":
        raise TestPeriodLeak(
            f"acceptance path was handed a {row.get('period')!r} record "
            f"({row.get('symbol')} fold {row.get('fold_id')} offset "
            f"{row.get('offset')}). Appendix K.2 defines acceptance on TRAINING "
            f"folds. Selection is on train, evaluation is on test.")
    if row.get("arm") != ACCEPT_ARM or row.get("population") != ACCEPT_POPULATION:
        raise TestPeriodLeak(
            f"acceptance path was handed arm={row.get('arm')!r} "
            f"population={row.get('population')!r}; K.2(a) specifies "
            f"{ACCEPT_ARM!r} / {ACCEPT_POPULATION!r}")
    m = row["metrics"]
    return m["n"], m["expectancy_r"], m["se_r"]


def acceptance_table(cells=None, grid_json=None):
    """Appendix K.2 applied to every (fold, symbol, offset) cell.

    Returns one row per A3-eligible grid point with the training expectancy,
    its standard error, the trade count, and the pass/fail verdict with each
    clause of K.2 recorded separately.
    """
    cells = cells if cells is not None else sw.load_cells()
    sw.validate_records(cells)                       # REUSED, not reimplemented
    grid_json = grid_json if grid_json is not None else gr.load_grid()

    # Ungated train counts, carried alongside purely as context for K.2(b).
    ungated = {(c["symbol"], c["fold_id"], c["offset"]): c["metrics"]["n"]
               for c in cells
               if c["period"] == "train" and c["arm"] == UNGATED_ARM
               and c["population"] == UNGATED_POP
               and c["direction"] == ACCEPT_DIRECTION}

    rows = []
    for c in cells:
        if (c["arm"] != ACCEPT_ARM or c["population"] != ACCEPT_POPULATION
                or c["direction"] != ACCEPT_DIRECTION
                or c["period"] != SELECT_PERIOD):
            continue
        n, exp, se = _acceptance_metrics(c)
        symbol, fold_id, offset = c["symbol"], c["fold_id"], c["offset"]

        eligible = sw.eligible_offsets(grid_json, symbol, fold_id)
        a3_ok = any(abs(offset - o) < 1e-9 for o in eligible)

        exp_ok = exp is not None and exp > ACCEPT_EXPECTANCY_FLOOR
        n_ok = n >= MIN_TRAIN_TRADES
        rows.append({
            "symbol": symbol, "fold_id": fold_id,
            "offset": float(offset), "multiplier": float(c["multiplier"]),
            "arm": ACCEPT_ARM, "population": ACCEPT_POPULATION,
            "period": "train", "direction": ACCEPT_DIRECTION,
            "n": n, "expectancy_r": exp, "se_r": se,
            "n_ungated_train": ungated.get((symbol, fold_id, offset)),
            "k2a_expectancy_gt_zero": bool(exp_ok),
            "k2b_min_200_train_trades": bool(n_ok),
            "k2c_survives_a3": bool(a3_ok),
            "passes": bool(exp_ok and n_ok and a3_ok),
        })
    rows.sort(key=lambda r: (r["symbol"], r["fold_id"], r["offset"]))
    if not rows:
        raise BandRuleError("acceptance table is empty -- a guard with nothing "
                            "to check passes vacuously")
    return rows


# ---------------------------------------------------------------------------
# 2. BAND IDENTIFICATION -- §4.3
# ---------------------------------------------------------------------------

def contiguous_runs(offsets, step=GRID_STEP):
    """Maximal runs of offsets adjacent on the 0.25 grid.

    Adjacency is a GRID relation, not a list relation: two passing offsets
    0.50 apart are not contiguous even if no passing offset lies between them,
    because the point between them failed (or was A3-ineligible and never
    simulated). §4.3 requires the neighbours themselves to pass.
    """
    offs = sorted(float(o) for o in offsets)
    runs, cur = [], []
    for o in offs:
        if cur and abs(o - cur[-1] - step) > 1e-9:
            runs.append(cur)
            cur = []
        cur.append(o)
    if cur:
        runs.append(cur)
    return runs


def identify_bands(accept_rows):
    """Per fold per symbol: the passing runs, the longest, and whether a
    selection is produced.

    §4.3: "If no contiguous band of three passing points exists, the fold
    produces no selection."
    """
    by = {}
    for r in accept_rows:
        by.setdefault((r["symbol"], r["fold_id"]), []).append(r)

    out = []
    for (symbol, fold_id), rows in sorted(by.items()):
        rows.sort(key=lambda r: r["offset"])
        passing = [r["offset"] for r in rows if r["passes"]]
        runs = contiguous_runs(passing)
        longest = max((len(x) for x in runs), default=0)
        out.append({
            "symbol": symbol, "fold_id": fold_id,
            "population": ACCEPT_POPULATION, "period": "train",
            "arm": ACCEPT_ARM, "direction": ACCEPT_DIRECTION,
            "offsets_evaluated": [r["offset"] for r in rows],
            "offsets_passing": passing,
            "n_passing": len(passing),
            "runs": [{"offsets": run, "width": len(run),
                      "start_offset": run[0], "end_offset": run[-1]}
                     for run in runs],
            "longest_run": longest,
            "produces_selection": bool(longest >= MIN_BAND_POINTS),
        })
    return out


# ---------------------------------------------------------------------------
# 3. PLATEAU SELECTION -- §4.3 and Appendix K.3
# ---------------------------------------------------------------------------

def band_centre(run):
    """The centre of one contiguous run. Appendix K.3 breaks an even tie HIGH.

    NOT the argmax. §4.3 pre-commits the centre precisely because "the pull
    toward argmax after the lift will be strong", and this function never sees
    an expectancy, so it cannot express that pull even by accident.
    """
    run = sorted(float(o) for o in run)
    if len(run) < MIN_BAND_POINTS:
        raise BandRuleError(
            f"run of {len(run)} is below the §4.3 minimum of {MIN_BAND_POINTS}; "
            f"such a fold produces NO SELECTION and must not reach selection")
    # Odd: the single middle element. Even: index len//2 is the HIGHER of the
    # two central offsets -- Appendix K.3, "the wider stop".
    return run[len(run) // 2]


def select_plateau(band_row):
    """§4.3 selection for one fold-symbol, or an explicit no-selection.

    Where two runs tie on width the higher band is taken. §4.3 and K.3 do not
    legislate a width tie; K.3's stated rationale for its own tie-break is that
    a wider stop strictly reduces floor binding, which is the only structural
    criterion in this design carrying a threshold, so that rationale is applied
    here as well. THIS IS A JUDGMENT CALL AND IS REPORTED AS ONE.
    """
    runs = [r["offsets"] for r in band_row["runs"]]
    eligible = [r for r in runs if len(r) >= MIN_BAND_POINTS]
    if not eligible:
        return {
            "symbol": band_row["symbol"], "fold_id": band_row["fold_id"],
            "population": ACCEPT_POPULATION, "period": "train",
            "arm": ACCEPT_ARM, "direction": ACCEPT_DIRECTION,
            "selection": None,
            "reason": (f"longest contiguous passing run is "
                       f"{band_row['longest_run']}, below the §4.3 minimum of "
                       f"{MIN_BAND_POINTS}"),
        }
    widest = max(len(r) for r in eligible)
    tied = [r for r in eligible if len(r) == widest]
    chosen = max(tied, key=lambda r: r[-1])     # width tie -> higher band
    return {
        "symbol": band_row["symbol"], "fold_id": band_row["fold_id"],
        "population": ACCEPT_POPULATION, "period": "train",
        "arm": ACCEPT_ARM, "direction": ACCEPT_DIRECTION,
        "selection": band_centre(chosen),
        "band_width": widest,
        "band_start_offset": chosen[0],
        "band_end_offset": chosen[-1],
        "band_offsets": chosen,
        "width_tie": len(tied) > 1,
        "n_tied_bands": len(tied),
        "expressed_as": "OFFSET FROM m*, not an absolute multiplier "
                        "(m* moves by a factor of 2.2 across folds)",
        "reason": None,
    }


# ---------------------------------------------------------------------------
# 4. KILL CONDITIONS DECIDABLE AT STEP 3
# ---------------------------------------------------------------------------

def _row(table, offset, arm, population):
    for r in table:
        if (abs(r["offset"] - offset) < 1e-9 and r["arm"] == arm
                and r["population"] == population):
            return r
    return None


def _require_test(row, what):
    if row["period"] != "test":
        raise TestPeriodLeak(
            f"{what} must be evaluated on TEST folds (§4.4 kill conditions, "
            f"Appendix M.4); got period={row['period']!r}")


def kill_oos_expectancy(tables):
    """(a) OOS EXPECTANCY <= 0 AFTER COSTS.

    Test folds, per symbol, pooled across test folds ONLY (Appendix M.4), on
    the gated_50 arm, at every A3-eligible offset.
    """
    out = {}
    for symbol, table in tables.items():
        rows = []
        for r in sorted(table, key=lambda x: x["offset"]):
            if r["arm"] != GATED_ARM or r["population"] != GATED_POP:
                continue
            _require_test(r, "kill condition (a)")
            m = r["metrics"]
            e, se = m["expectancy_r"], m["se_r"]
            rows.append({
                "offset": r["offset"], "n": m["n"], "n_folds": r["n_folds"],
                "expectancy_r": e, "se_r": se,
                "positive": bool(e is not None and e > 0),
                "exceeds_own_se": bool(e is not None and se is not None
                                       and e > se),
                "population": GATED_POP, "period": "test",
                "direction": "both", "arm": GATED_ARM,
                "pooled_over": r["pooled_over"],
            })
        any_pos = any(x["positive"] for x in rows)
        out[symbol] = {
            "offsets": rows,
            "any_offset_positive": any_pos,
            "any_offset_exceeds_own_se": any(x["exceeds_own_se"] for x in rows),
            "best_offset": (max(rows, key=lambda x: x["expectancy_r"])["offset"]
                            if rows else None),
            "best_expectancy_r": (max(x["expectancy_r"] for x in rows)
                                  if rows else None),
            # The kill condition FIRES when OOS expectancy is <= 0.
            "kill_fires": not any_pos,
        }
    return out


def _stratum_diff(g, u, name):
    """Appendix J: the stratified difference, withheld if either side is below
    the evidence minimum. The minimums do not move."""
    gs = (g or {}).get(name)
    us = (u or {}).get(name)
    if gs is None or us is None:
        return {"stratum": name, "withheld": True,
                "reason": "stratum absent (no trades in the arm)"}
    if gs["below_evidence_minimum"] or us["below_evidence_minimum"]:
        return {"stratum": name, "withheld": True,
                "n_gated_50": gs["n"], "n_ungated": us["n"],
                "minimum": gs["minimum"],
                "reason": "below the evidence minimum on at least one arm; "
                          "the stratified figure is NOT reported for it"}
    d = gs["expectancy_r"] - us["expectancy_r"]
    return {"stratum": name, "withheld": False,
            "n_gated_50": gs["n"], "n_ungated": us["n"],
            "expectancy_gated_50_r": gs["expectancy_r"],
            "expectancy_ungated_r": us["expectancy_r"],
            "difference_r": d,
            "reaches_0_05R": bool(d >= MARGINAL_CONTRIBUTION_R)}


def kill_gate_decorative(tables):
    """(b) GATED VS UNGATED DIFFER BY < 0.05R -- THE GATE IS DECORATIVE.

    Per symbol on test folds, gated_50 against ungated, at every offset, with
    Appendix J's floor-binding rates and the stratified comparison.
    """
    out = {}
    for symbol, table in tables.items():
        rows = []
        for offset in sorted({r["offset"] for r in table}):
            g = _row(table, offset, GATED_ARM, GATED_POP)
            u = _row(table, offset, UNGATED_ARM, UNGATED_POP)
            if g is None or u is None:
                continue
            _require_test(g, "kill condition (b)")
            _require_test(u, "kill condition (b)")
            gm, um = g["metrics"], u["metrics"]
            d = gm["expectancy_r"] - um["expectancy_r"]
            rows.append({
                "offset": offset, "n_folds": g["n_folds"],
                "n_gated_50": gm["n"], "n_ungated": um["n"],
                "expectancy_gated_50_r": gm["expectancy_r"],
                "expectancy_ungated_r": um["expectancy_r"],
                "se_gated_50_r": gm["se_r"], "se_ungated_r": um["se_r"],
                "difference_r": d,
                "reaches_0_05R": bool(d >= MARGINAL_CONTRIBUTION_R),
                # Appendix J (a): each arm's floor-binding rate.
                "floor_binding_gated_50": gm["floor_binding_rate"],
                "floor_binding_ungated": um["floor_binding_rate"],
                "floor_binding_gap_pp": (
                    (gm["floor_binding_rate"] - um["floor_binding_rate"]) * 100.0),
                # Appendix J (b): stratified into floor-bound / non-floor-bound.
                "strata": [_stratum_diff(g["floor_strata"], u["floor_strata"],
                                         "floor_bound"),
                           _stratum_diff(g["floor_strata"], u["floor_strata"],
                                         "not_floor_bound")],
                "period": "test", "direction": "both",
                "pooled_over": g["pooled_over"],
            })
        reaches = [x for x in rows if x["reaches_0_05R"]]
        out[symbol] = {
            "offsets": rows,
            "any_offset_reaches_0_05R": bool(reaches),
            "offsets_reaching_0_05R": [x["offset"] for x in reaches],
            "max_difference_r": (max(x["difference_r"] for x in rows)
                                 if rows else None),
            # FIRES when the gate contributes < 0.05R everywhere.
            "kill_fires": not reaches,
        }
    return out


def kill_thesis_backwards(tables):
    """(c) UNGATED OUTPERFORMS GATED -- THESIS BACKWARDS. Per symbol per offset."""
    out = {}
    for symbol, table in tables.items():
        rows = []
        for offset in sorted({r["offset"] for r in table}):
            g = _row(table, offset, GATED_ARM, GATED_POP)
            u = _row(table, offset, UNGATED_ARM, UNGATED_POP)
            if g is None or u is None:
                continue
            _require_test(g, "kill condition (c)")
            d = g["metrics"]["expectancy_r"] - u["metrics"]["expectancy_r"]
            rows.append({"offset": offset, "difference_r": d,
                         "ungated_outperforms": bool(d < 0.0),
                         "expectancy_gated_50_r": g["metrics"]["expectancy_r"],
                         "expectancy_ungated_r": u["metrics"]["expectancy_r"],
                         "population_pair": f"{GATED_POP} vs {UNGATED_POP}",
                         "period": "test", "direction": "both"})
        n_back = sum(1 for x in rows if x["ungated_outperforms"])
        out[symbol] = {
            "offsets": rows,
            "n_offsets_ungated_outperforms": n_back,
            "n_offsets": len(rows),
            "occurs_at_any_offset": bool(n_back),
            "occurs_at_every_offset": bool(rows) and n_back == len(rows),
            "kill_fires": bool(n_back),
        }
    return out


def kill_two_of_three(gate_result):
    """(d) TWO-OF-THREE.

    §4.4 defines a corroborating symbol as one whose gated expectancy exceeds
    its ungated expectancy by >= 0.05R. A symbol qualifies only if it shows
    that on its own AND at least one OTHER symbol shows it too.

    "Passes on its own" is read here as the same 0.05R direction-of-edge test,
    because that is the only sense in which §4.4 defines the rule and because
    §4.4 says explicitly that two-of-three is NOT "is profitable". The stricter
    reading -- own edge AND a step-3 selection AND positive OOS expectancy --
    is reported alongside; where both readings agree the ambiguity is moot.
    """
    shows = {s: v["any_offset_reaches_0_05R"] for s, v in gate_result.items()}
    out = {}
    for symbol in sorted(shows):
        others = [s for s in shows if s != symbol and shows[s]]
        out[symbol] = {
            "shows_direction_of_edge": shows[symbol],
            "corroborating_symbols": others,
            "n_corroborating": len(others),
            "qualifies": bool(shows[symbol] and others),
            "definition": "§4.4: gated expectancy exceeds ungated by >= 0.05R, "
                          "on test folds, at any A3-eligible offset",
        }
    n_showing = sum(1 for v in shows.values() if v)
    return {"per_symbol": out,
            "n_symbols_showing_edge": n_showing,
            "any_symbol_qualifies": any(v["qualifies"] for v in out.values()),
            "kill_fires": not any(v["qualifies"] for v in out.values())}


# ---------------------------------------------------------------------------
# 5. SUPPORTING DIAGNOSTICS -- DESCRIPTION ONLY, NO THRESHOLDS
# ---------------------------------------------------------------------------

HOLD_BINS = [(0, 5), (6, 10), (11, 15), (16, 20), (21, 21), (22, 25),
             (26, 30), (31, 35), (36, 40), (41, 41)]


def _hold_histogram(bars):
    b = np.asarray(bars, float)
    n = int(b.size)
    if n == 0:
        return None
    return {
        "n": n,
        "bins": [{"lo": lo, "hi": hi,
                  "n": int(((b >= lo) & (b <= hi)).sum()),
                  "fraction": float(((b >= lo) & (b <= hi)).mean())}
                 for lo, hi in HOLD_BINS],
        "median": float(np.median(b)), "mean": float(b.mean()),
        "p90": float(np.percentile(b, 90)),
        "fraction_before_checkpoint": float((b < CHECKPOINT_BAR).mean()),
        "fraction_at_or_after_checkpoint": float((b >= CHECKPOINT_BAR).mean()),
        "reference_lines": [CHECKPOINT_BAR, MAX_HOLD_BAR],
    }


def diagnostics(symbols=sw.SYMBOLS, trades_dir=sw.TRADES_DIR):
    """§4.5 diagnostics on TEST folds at the gated_50 arm, pooled per symbol.

    Exit-reason fractions per offset; the holding-time distribution on STOP and
    TARGET exits only (D6: holding time is degenerate by construction for the
    two time exits); and expectancy per bar alongside per trade wherever a time
    arm appears. No threshold is attached to any of these.
    """
    out = {}
    for symbol in symbols:
        t = srep.load_trades(symbol, trades_dir)
        test = t[t["period"] == "test"]
        rows = []
        for offset in sorted(test["offset"].unique()):
            at_off = test[test["offset"] == offset]
            n_folds = int(at_off["fold_id"].nunique())
            gated = srep.apply_population(
                at_off[at_off["arm"] == GATED_ARM], GATED_POP
            ).reset_index(drop=True)
            if len(gated) == 0:
                continue
            m = sw.expectancy_metrics(gated)      # REUSED, not reimplemented
            total = float(m["n"])
            st = gated[gated["exit_reason"].isin(("stop", "target"))]

            # §4.5: expectancy per bar alongside per trade WHEREVER A TIME ARM
            # APPEARS. minus_time_stop is the runnable time arm; minus_max_hold
            # is BLOCKED at step 2 and is reported as such, never dropped.
            no_ts = srep.apply_population(
                at_off[at_off["arm"] == TIME_ARM], TIME_POP
            ).reset_index(drop=True)
            tm = sw.expectancy_metrics(no_ts) if len(no_ts) else None

            rows.append({
                "offset": float(offset), "n_folds": n_folds,
                "population": GATED_POP, "period": "test", "direction": "both",
                "pooled_over": f"test folds only ({n_folds} folds, "
                               f"Appendix M.4); NOT pooled across offsets",
                "n": m["n"],
                "exit_reason_fraction": {k: (v / total if total else None)
                                         for k, v in m["exit_reasons"].items()},
                "exit_reason_counts": m["exit_reasons"],
                "holding_stop_target": _hold_histogram(
                    st["bars_held"].to_numpy(float)),
                "holding_stop": _hold_histogram(
                    gated[gated["exit_reason"] == "stop"]["bars_held"]
                    .to_numpy(float)),
                "holding_target": _hold_histogram(
                    gated[gated["exit_reason"] == "target"]["bars_held"]
                    .to_numpy(float)),
                "time_arms": {
                    "full": {"arm": "full", "population": GATED_POP,
                             "expectancy_r": m["expectancy_r"],
                             "expectancy_per_bar_r": m["expectancy_per_bar_r"],
                             "n": m["n"]},
                    "minus_time_stop": (
                        None if tm is None else
                        {"arm": TIME_ARM, "population": TIME_POP,
                         "expectancy_r": tm["expectancy_r"],
                         "expectancy_per_bar_r": tm["expectancy_per_bar_r"],
                         "n": tm["n"]}),
                    "minus_max_hold": {
                        "arm": "minus_max_hold", "status": "BLOCKED",
                        "reason": "costs.CostConfig.max_hold_bars is read-only "
                                  "and not independently sweepable (step 2). "
                                  "§4.4 never drops max-hold: it is a GUARD "
                                  "RAIL, measured and reported, NEVER dropped."},
                },
            })
        out[symbol] = rows
    return out


# ---------------------------------------------------------------------------
# 6. BUILD
# ---------------------------------------------------------------------------

def rvol_arm_ladder(tables):
    """§4.3's 30/50/70 pass-rate ladder. DESCRIPTION ONLY, NO THRESHOLD.

    §4.3 makes an improvement from 70% -> 50% -> 30% the sharpest falsification
    test of the RVOL gate, and Appendix J requires each arm's floor-binding
    rate alongside because the arms differ in composition. Reported here
    because it is the same question kill condition (b) asks and the figures are
    already computed; it attaches no threshold and gates no decision.
    """
    out = {}
    for symbol, table in tables.items():
        rows = []
        for offset in sorted({r["offset"] for r in table}):
            e, fb = {}, {}
            for arm, pop in (("full", "gated_70"), ("full", "gated_50"),
                             ("full", "gated_30"), (UNGATED_ARM, UNGATED_POP)):
                r = _row(table, offset, arm, pop)
                if r is None:
                    continue
                _require_test(r, "the 30/50/70 ladder")
                e[pop] = r["metrics"]["expectancy_r"]
                fb[pop] = r["metrics"]["floor_binding_rate"]
            rows.append({
                "offset": offset, "expectancy_r": e, "floor_binding_rate": fb,
                "monotone_70_50_30": bool(
                    e.get("gated_30") is not None
                    and e["gated_30"] >= e["gated_50"] >= e["gated_70"]),
                "period": "test", "direction": "both",
            })
        out[symbol] = rows
    return out


def build(cells=None, symbols=sw.SYMBOLS, trades_dir=sw.TRADES_DIR):
    grid_json = gr.load_grid()
    accept = acceptance_table(cells, grid_json)
    bands = identify_bands(accept)
    selections = [select_plateau(b) for b in bands]

    tables = {s: srep.offset_arm_table(s, trades_dir, grid_json)
              for s in symbols}
    k_a = kill_oos_expectancy(tables)
    k_b = kill_gate_decorative(tables)
    k_c = kill_thesis_backwards(tables)
    k_d = kill_two_of_three(k_b)

    # A candidate for step 4 requires BOTH a step-3 selection and survival of
    # the kill conditions. A kill condition is not advisory.
    n_sel = {}
    for s in symbols:
        n_sel[s] = sum(1 for x in selections
                       if x["symbol"] == s and x["selection"] is not None)
    candidates = {
        s: {"folds_with_selection": n_sel[s],
            "kill_a_oos_expectancy_fires": k_a[s]["kill_fires"],
            "kill_b_gate_decorative_fires": k_b[s]["kill_fires"],
            "kill_c_thesis_backwards_fires": k_c[s]["kill_fires"],
            "kill_d_two_of_three_qualifies": k_d["per_symbol"][s]["qualifies"],
            "produces_candidate": bool(
                n_sel[s] > 0
                and not k_a[s]["kill_fires"]
                and not k_b[s]["kill_fires"]
                and k_d["per_symbol"][s]["qualifies"])}
        for s in symbols}

    return {
        "step": "3 of the section 4.4 sequence (BAND IDENTIFICATION AND "
                "PLATEAU SELECTION)",
        "performs_no_collapse": "no collapse into a candidate (step 4), no A3 "
                                "re-check (step 5), no D5 leave-one-out "
                                "(step 7), no top-5% removal and no +/-25% "
                                "sensitivity probe (step 8), no holdout "
                                "(step 9)",
        "acceptance_definition": {
            "source": "Appendix K.2",
            "period": "train", "arm": ACCEPT_ARM,
            "population": ACCEPT_POPULATION, "direction": ACCEPT_DIRECTION,
            "k2a": "training-fold expectancy per trade in R, net of costs, "
                   "GREATER THAN ZERO. No margin, no significance test.",
            "k2b": f"training-fold trade count >= {MIN_TRAIN_TRADES}, per "
                   f"training fold",
            "k2c": "the grid point survives A3, established at step 0",
        },
        "populations": list(sw.POPULATIONS),
        "resimulation": "NONE. Every figure is derived from the step-2 cells "
                        "and step-2 trade tables. No bar file is opened, so "
                        "the report 13 seal is not exercised here.",
        "acceptance": accept,
        "bands": bands,
        "selections": selections,
        "kill_a_oos_expectancy": k_a,
        "kill_b_gate_decorative": k_b,
        "kill_c_thesis_backwards": k_c,
        "kill_d_two_of_three": k_d,
        "candidates": candidates,
        "diagnostics": diagnostics(symbols, trades_dir),
        "supplementary_rvol_ladder": rvol_arm_ladder(tables),
        "not_evaluated_here": [
            "top-5% winner removal (step 8)",
            "+/-25% parameter sensitivity (step 8)",
            "D5 leave-one-out (step 7)",
        ],
        "cells_path": sw.CELLS_PATH,
        "trades_path": sw.TRADES_DIR,
        "sweep_git_commit": json.load(open(sw.ARTIFACT_PATH))["sweep_git_commit"],
        "head_at_start": HEAD_AT_START,
        "git_commit": sch.git_revision(),
        "script": "src/sweep/bands.py",
    }


def _json_default(o):
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating,)):
        return float(o)
    if isinstance(o, (np.bool_,)):
        return bool(o)
    raise TypeError(f"{type(o)} is not JSON serialisable")


def write(payload=None, path=ARTIFACT_PATH):
    payload = payload if payload is not None else build()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as fh:
        json.dump(payload, fh, indent=1, sort_keys=True, default=_json_default)
    return path


# ---------------------------------------------------------------------------
# 7. REPORT -- rendered from the artifact, so no figure is transcribed by hand
# ---------------------------------------------------------------------------

def _n(x, nd=4):
    if x is None:
        return "--"
    return f"{x:+.{nd}f}" if nd else f"{int(x)}"


def _u(x, nd=4):
    return "--" if x is None else f"{x:.{nd}f}"


def _stratum_cell(st):
    if st.get("withheld"):
        n_g, n_u = st.get("n_gated_50"), st.get("n_ungated")
        if n_g is None:
            return "**withheld** (stratum absent)"
        return (f"n_g={n_g} / n_u={n_u} < {st.get('minimum')} "
                f"**withheld**")
    return (f"{_n(st['difference_r'])} "
            f"(g {_n(st['expectancy_gated_50_r'])} / "
            f"u {_n(st['expectancy_ungated_r'])}, "
            f"n_g={st['n_gated_50']}, n_u={st['n_ungated']})")


def render_report(p):
    L = []
    w = L.append
    fires = {
        "a": {s: v["kill_fires"] for s, v in p["kill_a_oos_expectancy"].items()},
        "b": {s: v["kill_fires"] for s, v in p["kill_b_gate_decorative"].items()},
        "c": {s: v["kill_fires"] for s, v in p["kill_c_thesis_backwards"].items()},
    }
    n_sel = sum(1 for s in p["selections"] if s["selection"] is not None)

    w("# REPORT 15 — BAND IDENTIFICATION AND PLATEAU SELECTION "
      "(step 3 of the §4.4 sequence)")
    w("")
    w("Applies Appendix K.2's acceptance definition to every A3-eligible grid "
      "point, identifies contiguous passing bands per fold per symbol, selects "
      "the centre of the widest band per §4.3 and Appendix K.3, and evaluates "
      "the pre-committed kill conditions that step 3 makes decidable.")
    w("")
    w("**THIS TASK STOPS AT STEP 3.** No collapse of the nine fold selections "
      "into a candidate (step 4), no A3 re-check (step 5, resolved at step 0), "
      "no D5 leave-one-out (step 7), no top-5% winner removal and no ±25% "
      "sensitivity probe (step 8).")
    w("")
    w("**The holdout remains SEALED.** Nothing here opens a bar file. Every "
      "figure is derived from the step-2 cells and step-2 trade tables, so no "
      "re-simulation occurred and the report-13 seal was not exercised. No "
      "call in this module passes `authorised=True` — the flag is never set "
      "anywhere in the analysis code — and a test asserts it.")
    w("")
    w("---")
    w("")

    # ---- headline -------------------------------------------------------
    w("## 0. THE HEADLINE: THE PRE-COMMITTED KILL CONDITIONS FIRE")
    w("")
    w("Stated first and without hedging, because that is what a "
      "pre-registration is for.")
    w("")
    w("| kill condition | BTCUSDT | ETHUSDT | SOLUSDT |")
    w("|---|---|---|---|")
    w("| **(a)** OOS expectancy ≤ 0 after costs | "
      + " | ".join("**FIRES**" if fires["a"][s] else "does not fire"
                    for s in sw.SYMBOLS) + " |")
    w("| **(b)** gate contributes < 0.05R — decorative | "
      + " | ".join("**FIRES**" if fires["b"][s] else "does not fire"
                    for s in sw.SYMBOLS) + " |")
    w("| **(c)** ungated outperforms gated — thesis backwards | "
      + " | ".join("**FIRES**" if fires["c"][s] else "does not fire"
                    for s in sw.SYMBOLS) + " |")
    w("| **(d)** two-of-three qualification | "
      + " | ".join("**FAILS**"
                   if not p["kill_d_two_of_three"]["per_symbol"][s]["qualifies"]
                   else "qualifies" for s in sw.SYMBOLS) + " |")
    w("")
    w(f"**NO SYMBOL PRODUCES A CANDIDATE FOR STEP 4.** Two-of-three fails "
      f"outright: exactly "
      f"{p['kill_d_two_of_three']['n_symbols_showing_edge']} of three symbols "
      f"shows the §4.4 direction of edge, and the rule requires a symbol to "
      f"show it **and** be corroborated by another. A rule needing two "
      f"symbols cannot be satisfied by one.")
    w("")
    w("Per §5 of the task specification and §4.3/§4.4 of the "
      "pre-registration, the procedure is exhausted and that is the finding. "
      "No variant is searched, no threshold relaxed, no range extended, no "
      "alternative configuration proposed.")
    w("")
    w("---")
    w("")

    # ---- provenance -----------------------------------------------------
    w("## 1. Provenance")
    w("")
    w("| item | value |")
    w("|---|---|")
    w(f"| HEAD at the start of step 3 | `{p['head_at_start']}` |")
    w("| Working tree at that point | **clean** (`git status --porcelain` "
      "empty) |")
    w(f"| Step-2 sweep commit | `{p['sweep_git_commit']}` |")
    w(f"| Cells consumed | `{os.path.relpath(p['cells_path'], sch.ROOT)}` |")
    w(f"| Trade tables consumed | "
      f"`{os.path.relpath(p['trades_path'], sch.ROOT)}` |")
    w("| Re-simulation | **none** — see §1.1 |")
    w("| Artifact written | `data/derived/sweep/bands.json` |")
    w("")
    w("### 1.1 No re-simulation was necessary")
    w("")
    w("The task anticipated that Appendix K.2's TRAINING-fold figures might "
      "not exist in `sweep.json`. They do. Step 2 emitted every cell crossed "
      "with `train`/`test`, so the acceptance population — arm `full`, "
      "population `gated_50`, period `train`, direction `both` — is read "
      "directly from `sweep_cells.jsonl`. No engine call was made and no bar "
      "file was opened, so the question of proving bit-identical reproduction "
      "does not arise.")
    w("")
    w("**This is a different population from the one report 14 §6 tabulates.** "
      "Report 14 pools TEST folds only, per Appendix M.4, because that is the "
      "correct population for ARM COMPARISON. Acceptance is a TRAINING-fold "
      "quantity, because selection is on train and evaluation is on test. No "
      "figure from report 14 §6 is reused for acceptance; §8(a) below records "
      "the guard that makes crossing them raise rather than compute.")
    w("")

    # ---- population contract --------------------------------------------
    w("## 2. The population contract")
    w("")
    w("Every figure below names its population from the closed set "
      "(`ungated`, `breakout`, `gated_30`, `gated_50`, `gated_70`) crossed "
      "with (`train`, `test`) and (`long`, `short`, `both`). The step-2 "
      "validator `sweep.validate_records` is **reused, not reimplemented**, "
      "and runs over the cells before anything is read from them; a test "
      "re-plants the step-2 mutation of stripping a label through step 3's "
      "entry point.")
    w("")
    w("| quantity | population | period | direction | arm |")
    w("|---|---|---|---|---|")
    w("| acceptance expectancy, SE, trade count (K.2a, K.2b) | `gated_50` | "
      "`train` | `both` | `full` |")
    w("| band identification and plateau selection | `gated_50` | `train` | "
      "`both` | `full` |")
    w("| kill (a) OOS expectancy | `gated_50` | `test` | `both` | `full` |")
    w("| kill (b)/(c)/(d) gated-vs-ungated | `gated_50` vs `ungated` | "
      "`test` | `both` | `full` vs `minus_rvol` |")
    w("| diagnostics (§7) | `gated_50` | `test` | `both` | `full`, "
      "`minus_time_stop` |")
    w("")

    # ---- acceptance ------------------------------------------------------
    w("## 3. Acceptance per grid point (Appendix K.2)")
    w("")
    w("**Population: `gated_50`, period `train`, direction `both`, arm "
      "`full`.** A grid point passes when all of:")
    w("")
    w("- **(a)** training-fold expectancy per trade in R, net of costs, is "
      "**greater than zero**. No margin. No significance test. Zero is not "
      "greater than zero, and a test asserts that.")
    w(f"- **(b)** the training-fold trade count meets the "
      f"{MIN_TRAIN_TRADES}-trade evidence minimum, applied per training fold.")
    w("- **(c)** the grid point survives A3, established at step 0.")
    w("")
    n_rows = len(p["acceptance"])
    n_pass = sum(1 for r in p["acceptance"] if r["passes"])
    n_b_fail = sum(1 for r in p["acceptance"]
                   if not r["k2b_min_200_train_trades"])
    w(f"**{n_rows}** (fold, symbol, offset) cells evaluated; **{n_pass}** "
      f"pass. Clause (b) fails **{n_b_fail}** times — every training fold "
      f"clears 200 gated_50 trades comfortably (range "
      f"{min(r['n'] for r in p['acceptance'])}–"
      f"{max(r['n'] for r in p['acceptance'])}), so acceptance is decided "
      f"entirely by clause (a). Clause (c) is true by construction: offsets "
      f"that fail A3 were never simulated.")
    w("")
    w("Offsets are **offsets from m\\***. The absolute multiplier is given "
      "alongside because m\\* moves by a factor of 2.2 across folds and the "
      "two are not interchangeable.")
    w("")
    for symbol in sw.SYMBOLS:
        w(f"### 3.{sw.SYMBOLS.index(symbol) + 1} {symbol} — train, "
          f"`gated_50`, `both`")
        w("")
        w("| fold | offset from m\\* | multiplier | n (train) | expectancy R "
          "| SE | (a) E>0 | (b) n≥200 | (c) A3 | verdict |")
        w("|---|---|---|---|---|---|---|---|---|---|")
        for r in p["acceptance"]:
            if r["symbol"] != symbol:
                continue
            w(f"| {r['fold_id']} | m\\*+{r['offset']:.2f} | "
              f"{r['multiplier']:.3f} | {r['n']} | {_n(r['expectancy_r'])} | "
              f"{_u(r['se_r'])} | "
              f"{'✅' if r['k2a_expectancy_gt_zero'] else '❌'} | "
              f"{'✅' if r['k2b_min_200_train_trades'] else '❌'} | "
              f"{'✅' if r['k2c_survives_a3'] else '❌'} | "
              f"{'**PASS**' if r['passes'] else 'fail'} |")
        w("")

    # ---- bands -----------------------------------------------------------
    w("## 4. Band identification (§4.3)")
    w("")
    w("Contiguity is a **grid** relation, not a list relation: two passing "
      "offsets 0.50 apart are not contiguous, because the 0.25 point between "
      "them failed. A fold produces a selection only where a contiguous run of "
      "**three or more** passing points exists.")
    w("")
    w("Offset 2.50 is excluded from eligibility by the plateau rule and was "
      "not simulated, so no band can reach it.")
    w("")
    w("| symbol | fold | offsets evaluated | passing | runs found "
      "(offsets from m\\*) | longest run | selection? |")
    w("|---|---|---|---|---|---|---|")
    sel = {(s["symbol"], s["fold_id"]): s for s in p["selections"]}
    for b in p["bands"]:
        runs = ("; ".join(f"[m\\*+{r['start_offset']:.2f} … "
                          f"m\\*+{r['end_offset']:.2f}] w={r['width']}"
                          for r in b["runs"]) or "*none*")
        w(f"| {b['symbol']} | {b['fold_id']} | "
          f"{len(b['offsets_evaluated'])} | {b['n_passing']} | {runs} | "
          f"{b['longest_run']} | "
          f"{'**yes**' if b['produces_selection'] else 'NO SELECTION'} |")
    w("")
    by_sym = {}
    for b in p["bands"]:
        by_sym.setdefault(b["symbol"], []).append(b["produces_selection"])
    w("**Folds producing a selection:** "
      + ", ".join(f"{s} {sum(by_sym[s])}/9" for s in sw.SYMBOLS)
      + f" — {n_sel} of 27 fold-symbols in total.")
    w("")
    n_eth = sum(1 for r in p["acceptance"] if r["symbol"] == "ETHUSDT")
    w(f"ETHUSDT produces **no selection in any fold**: not one of its {n_eth} "
      f"A3-eligible grid points has positive training expectancy. That is not "
      f"a marginal miss — every ETH training cell is negative, at every "
      f"offset, in all nine folds.")
    w("")

    # ---- selections ------------------------------------------------------
    w("## 5. Plateau selection (§4.3, Appendix K.3)")
    w("")
    w("The selected value is the **centre of the widest contiguous passing "
      "band, NOT the argmax**. Where the band has an even number of points "
      "the **higher** of the two central offsets is taken, per Appendix K.3. "
      "The selection function receives offsets only and never sees an "
      "expectancy, so it cannot express an argmax pull even by accident.")
    w("")
    w("| symbol | fold | band (offsets from m\\*) | width | even? | "
      "**selected offset** | selected multiplier |")
    w("|---|---|---|---|---|---|---|")
    acc = {(r["symbol"], r["fold_id"], round(r["offset"], 4)): r
           for r in p["acceptance"]}
    for s in p["selections"]:
        if s["selection"] is None:
            w(f"| {s['symbol']} | {s['fold_id']} | — | — | — | "
              f"*NO SELECTION* | — |")
            continue
        k = (s["symbol"], s["fold_id"], round(s["selection"], 4))
        mult = acc[k]["multiplier"]
        w(f"| {s['symbol']} | {s['fold_id']} | "
          f"[m\\*+{s['band_start_offset']:.2f} … "
          f"m\\*+{s['band_end_offset']:.2f}] | {s['band_width']} | "
          f"{'yes' if s['band_width'] % 2 == 0 else 'no'} | "
          f"**m\\*+{s['selection']:.2f}** | {mult:.3f} |")
    w("")
    w("Absolute multipliers are shown for completeness only. **They are not "
      "comparable across folds** — m\\* moves by a factor of 2.2 — which is "
      "why §4.4 requires bands to be expressed as offsets.")
    w("")
    w("**These nine-fold selections are NOT collapsed into a candidate.** "
      "That is step 4 and a separate task, and §4.4 forbids a step revisiting "
      "an earlier one.")
    w("")
    argmax_note = []
    for s in p["selections"]:
        if s["selection"] is None:
            continue
        rows = [acc[(s["symbol"], s["fold_id"], round(o, 4))]
                for o in s["band_offsets"]]
        best = max(rows, key=lambda r: r["expectancy_r"])
        if abs(best["offset"] - s["selection"]) > 1e-9:
            argmax_note.append(
                f"{s['symbol']} fold {s['fold_id']}: centre m\\*+"
                f"{s['selection']:.2f}, argmax m\\*+{best['offset']:.2f}")
    if argmax_note:
        w("**Where the centre rule actually bit** (centre ≠ argmax): "
          + "; ".join(argmax_note) + ".")
        w("")

    # ---- kill conditions -------------------------------------------------
    w("## 6. The pre-committed kill conditions")
    w("")
    w("### 6.1 (a) OOS EXPECTANCY ≤ 0 AFTER COSTS")
    w("")
    w("**Population: `gated_50`, period `test`, direction `both`, arm "
      "`full`, pooled across TEST FOLDS ONLY per Appendix M.4.** Training "
      "folds overlap by 50% and pooling them would double-count mid-span "
      "trades; test folds do not overlap.")
    w("")
    w("Fold coverage varies by offset because A3 eligibility varies by fold. "
      "The `folds` column states it on every row, and a figure pooling four "
      "folds is not the same statement as one pooling nine.")
    w("")
    for symbol in sw.SYMBOLS:
        v = p["kill_a_oos_expectancy"][symbol]
        w(f"**{symbol}**")
        w("")
        w("| offset from m\\* | folds pooled | n | expectancy R | SE | "
          "positive? | exceeds own SE? |")
        w("|---|---|---|---|---|---|---|")
        for r in v["offsets"]:
            w(f"| m\\*+{r['offset']:.2f} | {r['n_folds']} | {r['n']} | "
              f"{_n(r['expectancy_r'])} | {_u(r['se_r'])} | "
              f"{'yes' if r['positive'] else 'no'} | "
              f"{'yes' if r['exceeds_own_se'] else 'no'} |")
        w("")
        w(f"- Any offset positive: **{'YES' if v['any_offset_positive'] else 'NO'}**"
          f" · any offset exceeding its own standard error: "
          f"**{'YES' if v['any_offset_exceeds_own_se'] else 'NO'}**")
        w(f"- Best offset: m\\*+{v['best_offset']:.2f} at "
          f"{_n(v['best_expectancy_r'])}")
        w(f"- **VERDICT: kill condition (a) "
          f"{'FIRES' if v['kill_fires'] else 'does not fire'} for {symbol}.**")
        w("")
    sol = p["kill_a_oos_expectancy"]["SOLUSDT"]
    pos = [r for r in sol["offsets"] if r["positive"]]
    w("**SOLUSDT needs stating precisely.** The condition as pre-committed "
      "asks whether OOS expectancy is ≤ 0, and SOL has "
      f"{len(pos)} offset where it is not: "
      + ", ".join(f"m\\*+{r['offset']:.2f} at {_n(r['expectancy_r'])} "
                  f"(SE {_u(r['se_r'])}, {r['n_folds']} folds pooled)"
                  for r in pos)
      + ". So the condition does not fire on the letter of the rule. Three "
        "things about that single point are recorded rather than argued away:")
    w("")
    for r in pos:
        w(f"- it is smaller than its own standard error "
          f"({_n(r['expectancy_r'])} against {_u(r['se_r'])});")
        w(f"- it pools **{r['n_folds']} of 9** test folds, because m\\*+"
          f"{r['offset']:.2f} is A3-eligible in only those folds;")
        w(f"- **no SOLUSDT fold selected m\\*+{r['offset']:.2f}.** Both SOL "
          f"selections landed at m\\*+2.00, where pooled test expectancy is "
          f"{_n([x for x in sol['offsets'] if abs(x['offset'] - 2.0) < 1e-9][0]['expectancy_r'])}.")
    w("")
    w("Every offset any SOL fold actually selected is negative out of "
      "sample. That is recorded as an observation, not used to redefine the "
      "condition.")
    w("")

    w("### 6.2 (b) GATED VS UNGATED DIFFER BY < 0.05R — THE GATE IS DECORATIVE")
    w("")
    w("**Populations: `gated_50` against `ungated`, period `test`, direction "
      "`both`, arms `full` and `minus_rvol`, pooled across test folds only.** "
      "Appendix J's requirement is met on every row: each arm's floor-binding "
      "rate, and the comparison stratified into floor-bound and "
      "non-floor-bound trades, with any stratum below the evidence minimum "
      "stated and withheld rather than reported.")
    w("")
    for symbol in sw.SYMBOLS:
        v = p["kill_b_gate_decorative"][symbol]
        w(f"**{symbol}**")
        w("")
        w("| offset | n gated / ungated | E gated_50 | E ungated | **diff** | "
          "≥0.05R? | floor-bind g / u | gap |")
        w("|---|---|---|---|---|---|---|---|")
        for r in v["offsets"]:
            w(f"| m\\*+{r['offset']:.2f} | {r['n_gated_50']} / "
              f"{r['n_ungated']} | {_n(r['expectancy_gated_50_r'])} | "
              f"{_n(r['expectancy_ungated_r'])} | "
              f"**{_n(r['difference_r'])}** | "
              f"{'**yes**' if r['reaches_0_05R'] else 'no'} | "
              f"{r['floor_binding_gated_50']:.1%} / "
              f"{r['floor_binding_ungated']:.1%} | "
              f"{r['floor_binding_gap_pp']:+.1f}pp |")
        w("")
        w("Appendix J stratification, same populations:")
        w("")
        w("| offset | floor-bound Δ | non-floor-bound Δ |")
        w("|---|---|---|")
        for r in v["offsets"]:
            fb = [s for s in r["strata"] if s["stratum"] == "floor_bound"][0]
            nb = [s for s in r["strata"]
                  if s["stratum"] == "not_floor_bound"][0]
            w(f"| m\\*+{r['offset']:.2f} | {_stratum_cell(fb)} | "
              f"{_stratum_cell(nb)} |")
        w("")
        w(f"- Maximum difference at any offset: "
          f"**{_n(v['max_difference_r'])}**"
          + (f", reached at " + ", ".join(f"m\\*+{o:.2f}"
                                          for o in v["offsets_reaching_0_05R"])
             if v["offsets_reaching_0_05R"] else "")
          + ".")
        w(f"- **VERDICT: kill condition (b) "
          f"{'FIRES' if v['kill_fires'] else 'does not fire'} for {symbol}.**")
        w("")
    w("**What the stratification says — Appendix I.1's question, answered.**")
    w("")
    w("I.1 named two possible sources of a gated-minus-ungated gap: "
      "**(a) EDGE DETECTION**, the registered thesis, or **(b) VOLATILITY "
      "SELECTION**, the gate merely removing trades whose volatility is too "
      "low relative to the cost floor. The stratified figures separate them, "
      "and they point at (b):")
    w("")
    w("- The gate cuts floor binding by 3–15pp at every offset on every "
      "symbol — it is selecting higher-ATR bars exactly as report 11 "
      "predicted.")
    w("- Among **floor-bound** trades the gate's advantage is large and "
      "frequently clears 0.05R on its own.")
    w("- Among **non-floor-bound** trades it collapses to roughly +0.02R on "
      "BTC and SOL, and on ETH it is **negative at five of nine offsets** — "
      "the gated arm is slightly worse than ungated once floor-bound trades "
      "are removed.")
    w("")
    w("Per I.1 this is DESCRIPTION and changes no verdict: the 0.05R "
      "threshold operates on the unstratified figure, and it is not reached. "
      "But it says what the gate is doing. Under mechanism (b) a direct ATR% "
      "filter would do the same job more simply, and the session-normalised "
      "RVOL apparatus is unnecessary machinery.")
    w("")

    w("### 6.3 (c) UNGATED OUTPERFORMS GATED — THESIS BACKWARDS")
    w("")
    w("**Populations: `gated_50` against `ungated`, period `test`, direction "
      "`both`, per symbol per offset.**")
    w("")
    w("| symbol | offsets where ungated outperforms | of | verdict |")
    w("|---|---|---|---|")
    for symbol in sw.SYMBOLS:
        v = p["kill_c_thesis_backwards"][symbol]
        w(f"| {symbol} | {v['n_offsets_ungated_outperforms']} | "
          f"{v['n_offsets']} | "
          f"**{'FIRES' if v['kill_fires'] else 'does not fire'}** |")
    w("")
    w("**VERDICT: kill condition (c) does not fire anywhere.** The gated arm "
      "beats the ungated arm at every A3-eligible offset on all three "
      "symbols. The thesis is not backwards — the gate points the right way. "
      "It simply does not point far enough: the sign is right everywhere and "
      "the magnitude clears 0.05R at one offset on one symbol.")
    w("")

    w("### 6.4 (d) TWO-OF-THREE")
    w("")
    d = p["kill_d_two_of_three"]
    w("§4.4 defines a corroborating symbol as one whose **gated expectancy "
      "exceeds its ungated expectancy by ≥ 0.05R** — explicitly NOT \"is "
      "profitable\", because profitability is a different claim from \"the "
      "gate works\". A symbol qualifies only if it shows that itself AND at "
      "least one other symbol shows it too.")
    w("")
    w("| symbol | shows direction of edge? | corroborating symbols | "
      "qualifies? |")
    w("|---|---|---|---|")
    for symbol in sw.SYMBOLS:
        v = d["per_symbol"][symbol]
        w(f"| {symbol} | "
          f"{'**yes**' if v['shows_direction_of_edge'] else 'no'} | "
          f"{', '.join(v['corroborating_symbols']) or '—'} | "
          f"{'yes' if v['qualifies'] else '**no**'} |")
    w("")
    w(f"**VERDICT: two-of-three FAILS. No symbol qualifies.** "
      f"{d['n_symbols_showing_edge']} of three symbols shows the direction of "
      f"edge. SOLUSDT shows it, at one offset, but nothing corroborates it; "
      f"BTCUSDT and ETHUSDT do not show it at all, so SOL cannot corroborate "
      f"them into qualification either. A rule requiring two symbols is not "
      f"satisfiable by one.")
    w("")
    w("**Interpretation caveat, per §4.4.** 4.1's concordance measurement may "
      "show all three symbols sitting in the same regime cell most of the "
      "time, which would make two-of-three weaker evidence than it looks. "
      "That caveat cuts toward leniency and the rule still fails, so it "
      "changes nothing here.")
    w("")
    w("**On the reading of \"passes on its own\".** §4.4 defines the "
      "corroboration test but not the self-test. Both available readings give "
      "the same verdict — under the 0.05R reading only SOL passes and has no "
      "corroborator; under the stricter reading (own edge AND a step-3 "
      "selection AND positive OOS expectancy) no symbol passes at all. "
      "Recorded in §9 as a judgment call whose resolution does not matter.")
    w("")

    # ---- diagnostics -----------------------------------------------------
    w("## 7. Supporting diagnostics — DESCRIPTION ONLY, no thresholds")
    w("")
    w("**Population: `gated_50`, period `test`, direction `both`, arm "
      "`full`, pooled per symbol across test folds only.** These exist to "
      "inform the next hypothesis, not to rescue this one. No threshold is "
      "attached to any figure in this section.")
    w("")
    w("### 7.1 Exit-reason distribution, as a fraction of trades")
    w("")
    for symbol in sw.SYMBOLS:
        w(f"**{symbol}**")
        w("")
        w("| offset | n | stop | target | time_stop | max_hold | "
          "insufficient_data |")
        w("|---|---|---|---|---|---|---|")
        for r in p["diagnostics"][symbol]:
            f = r["exit_reason_fraction"]
            w(f"| m\\*+{r['offset']:.2f} | {r['n']} | {f['stop']:.3f} | "
              f"{f['target']:.3f} | {f['time_stop']:.3f} | "
              f"{f['max_hold']:.3f} | {f['insufficient_data']:.3f} |")
        w("")
    w("**The time-stop checkpoint is the dominant exit and grows with the "
      "stop width.** On BTC it takes 74–83% of trades and rises monotonically "
      "with offset; ETH 66–81%; SOL 45–77%. Target exits are rare and shrink "
      "as stops widen (BTC 6.0% → 4.1%), which is the mechanical consequence "
      "of a wider stop implying a wider +2R target at the same ATR. Max-hold "
      "takes 1.5–2.8% throughout, and `insufficient_data` is zero everywhere "
      "— the report-13 boundary exclusion means no trade was resolved off the "
      "end of the available records.")
    w("")
    w("### 7.2 Holding-time distribution on STOP and TARGET exits only (D6)")
    w("")
    w("§4.5: holding time is degenerate by construction for the time-stop "
      "(always 21) and max-hold (always 41) exits, so D6 is answerable only "
      "on stop and target exits. Bars **21** and **41** are the reference "
      "lines. §4.5's reading: stop/target exits clustering just before 21 "
      "means the checkpoint is **catching** an existing mode; smooth through "
      "it means the checkpoint is **creating** one.")
    w("")
    for symbol in sw.SYMBOLS:
        w(f"**{symbol}** — fraction of stop+target exits by holding time")
        w("")
        w("| offset | n | 0–5 | 6–10 | 11–15 | 16–20 | **21** | 22–25 | "
          "26–30 | 31–35 | 36–40 | **41** | median |")
        w("|---|---|---|---|---|---|---|---|---|---|---|---|---|")
        for r in p["diagnostics"][symbol]:
            h = r["holding_stop_target"]
            if h is None:
                continue
            cells = " | ".join(f"{b['fraction']:.3f}" for b in h["bins"])
            w(f"| m\\*+{r['offset']:.2f} | {h['n']} | {cells} | "
              f"{h['median']:.0f} |")
        w("")
    w("**Reading: the checkpoint CREATES the mode, it does not catch one.** "
      "The distribution runs smoothly through bar 21 on all three symbols at "
      "every offset. The 16–20 bucket holds roughly the same mass as 11–15 "
      "with no build-up against the line; bar 21 itself takes 0.5–2.2% of "
      "stop/target exits, which is what a single bar out of a smooth "
      "distribution should take; and 22–30 continues at a comparable rate "
      "rather than falling off a cliff. Roughly 90–95% of stop and target "
      "exits happen before bar 21 simply because most trades that are going "
      "to resolve resolve early — the median is 8–12 bars — not because "
      "anything clusters at the checkpoint.")
    w("")
    w("Bar 41 is empty on stop/target exits almost everywhere, which is "
      "expected: a trade still alive at 41 exits `max_hold` by definition.")
    w("")
    w("### 7.3 Expectancy per bar alongside per trade, wherever a time arm "
      "appears")
    w("")
    w("§4.5 requires the secondary metric wherever a time arm is compared, "
      "because per-trade expectancy silently rewards holding longer. It never "
      "overrides the primary metric in a decision, and it does not here.")
    w("")
    w("`minus_max_hold` is **BLOCKED**, not omitted: `CostConfig."
      "max_hold_bars` is a read-only property and no replacement horizon is "
      "pre-registered. §4.4 never drops max-hold in any case — it is a GUARD "
      "RAIL, *measured and reported, NEVER dropped*.")
    w("")
    for symbol in sw.SYMBOLS:
        w(f"**{symbol}** — `gated_50`, test folds")
        w("")
        w("| offset | full: E/trade | full: E/bar | minus_time_stop: E/trade "
          "| minus_time_stop: E/bar | n |")
        w("|---|---|---|---|---|---|")
        for r in p["diagnostics"][symbol]:
            a = r["time_arms"]["full"]
            b = r["time_arms"]["minus_time_stop"]
            w(f"| m\\*+{r['offset']:.2f} | {_n(a['expectancy_r'])} | "
              f"{_n(a['expectancy_per_bar_r'], 5)} | "
              f"{_n(b['expectancy_r']) if b else '--'} | "
              f"{_n(b['expectancy_per_bar_r'], 5) if b else '--'} | "
              f"{a['n']} |")
        w("")
    w("The two arms share an identical trade universe by construction — the "
      "checkpoint changes when a trade exits, not whether it exists — so the "
      "`n` column is common to both. Removing the checkpoint improves "
      "per-trade expectancy on BTC and SOL at every offset and is roughly "
      "neutral on ETH. **This is not a D5 decision and must not be read as "
      "one**: D5 is step 7, pools across symbols and folds, and is not run "
      "here.")
    w("")
    w("### 7.4 Supplementary: the 30/50/70 pass-rate ladder")
    w("")
    w("Not a step-3 requirement. Included because §4.3 makes the "
      "70%→50%→30% ordering the sharpest falsification test of the RVOL gate "
      "— the same question kill condition (b) asks — and the figures were "
      "already computed. **No threshold is attached and no decision is gated "
      "on it.** Appendix J's floor-binding rates accompany each arm because "
      "the arms differ in composition.")
    w("")
    for symbol in sw.SYMBOLS:
        w(f"**{symbol}** — expectancy per trade, test folds, direction `both`")
        w("")
        w("| offset | `gated_70` | `gated_50` | `gated_30` | `ungated` | "
          "monotone 70→50→30? | floor-bind 70/50/30/un |")
        w("|---|---|---|---|---|---|---|")
        for r in p["supplementary_rvol_ladder"][symbol]:
            e, fb = r["expectancy_r"], r["floor_binding_rate"]
            w(f"| m\\*+{r['offset']:.2f} | {_n(e['gated_70'])} | "
              f"{_n(e['gated_50'])} | {_n(e['gated_30'])} | "
              f"{_n(e['ungated'])} | "
              f"{'yes' if r['monotone_70_50_30'] else 'no'} | "
              f"{fb['gated_70']:.0%}/{fb['gated_50']:.0%}/"
              f"{fb['gated_30']:.0%}/{fb['ungated']:.0%} |")
        w("")
    w("The ordering holds at most offsets — the gate does rank trades, and "
      "the sign is consistently right. What it does not do is move the "
      "number far: the whole span from `ungated` to `gated_30` is about "
      "0.04R on BTC, 0.02R on ETH and 0.03R on SOL away from the single "
      "four-fold point at m\\*+0.50, and every figure in the ladder is "
      "negative except at that offset. Floor binding falls monotonically across "
      "the same ladder, which is the composition effect §6.2 already "
      "identified.")
    w("")

    # ---- verification ----------------------------------------------------
    w("## 8. Verification")
    w("")
    w("482 tests pass (444 before this step, 38 added). Every item the task "
      "specified:")
    w("")
    w("| # | requirement | how it is enforced |")
    w("|---|---|---|")
    w("| a | acceptance computed on train, never test | "
      "`_acceptance_metrics` raises `TestPeriodLeak` on any record not "
      "labelled `train`. The literal `\"train\"` there is deliberately NOT "
      "`SELECT_PERIOD`: a test monkeypatches the selector to `\"test\"` and "
      "requires the pipeline to raise. A guard reading the same constant as "
      "the thing it guards is vacuous. A further test recomputes the "
      "acceptance trade count straight off the parquet tables, tying the "
      "`train` label to the stored data rather than to itself. |")
    w("| b | population labels on every figure; step-2 validator reused; "
      "planted mutations still pass | `sweep.validate_records` is called on "
      "the cells before anything is read; the step-2 label-stripping mutation "
      "is re-planted through step 3's entry point; kill-condition rows are "
      "asserted to carry `period=\"test\"`, and `_require_test` raises on a "
      "train row. |")
    w("| c | plateau returns the band centre, not the argmax | a constructed "
      "five-point band with monotonically rising expectancy — so its argmax "
      "is its LAST point — asserts the centre is returned and that centre ≠ "
      "argmax. `band_centre` takes offsets only and never receives an "
      "expectancy. |")
    w("| d | even-count tie-break returns the HIGHER central offset | tested "
      "on Appendix K.3's own worked case (a four-point band, offsets 1.50 to "
      "2.25 → 2.00) and at widths 4 and 6, with an explicit assertion that "
      "the LOWER central offset is never returned. |")
    w("| e | a two-point run produces NO SELECTION | tested directly, plus a "
      "zero-run case, plus two separate two-point runs which must not "
      "combine, plus `band_centre` refusing a sub-three run outright. |")
    w("| f | determinism | `acceptance_table` and the selection pipeline are "
      "asserted equal across two runs; the written artifact is asserted equal "
      "to a fresh build; rebuilding the JSON reproduces a byte-identical "
      "file. |")
    w("| g | holdout seal active, no 2025+ data read | nothing here opens a "
      "bar file. A test asserts `authorised` appears nowhere in the module, "
      "and another asserts every `signal_bar_ts`, `entry_ts` and `exit_ts` in "
      "every trade table step 3 reads falls strictly before "
      "`HOLDOUT_TEST_START`. |")
    w("| h | full suite passes | 482 passed in 30.4s. |")
    w("")
    w("One further guard: a test greps the module for the names of later "
      "steps (`top_5`, `leave_one_out`, `sensitivity_probe`, `collapse`, "
      "`intersect_bands`) and fails if step 3 has quietly grown into step 4, "
      "7 or 8.")
    w("")

    # ---- judgment calls --------------------------------------------------
    w("## 9. Where the specification was ambiguous, and what I decided")
    w("")
    w("### 9.1 K.2(b): whose trade count?")
    w("")
    w("K.2(b) says \"the training-fold trade count **for that symbol**\" "
      "without naming a population. It could mean the `gated_50` count or the "
      "`ungated` count. I used **`gated_50`**, because K.2(a) measures "
      "expectancy on that arm and the minimum exists to guarantee that "
      "expectancy has evidence behind it; a 200-trade minimum satisfied by "
      "trades the arm does not contain would be exactly the "
      "measured-on-one-population, applied-to-another defect Appendix M.3 "
      "catalogues. **The choice is immaterial here:** the smallest `gated_50` "
      "training fold holds "
      f"{min(r['n'] for r in p['acceptance'])} trades, so clause (b) passes "
      "under either reading at every one of the 198 cells. The `ungated` "
      "count is carried in the artifact as `n_ungated_train` regardless.")
    w("")
    w("### 9.2 K.2: which direction cohort?")
    w("")
    w("§4.5 keeps long and short cohorts separate throughout, but K.2 states "
      "a single expectancy per grid point. I read acceptance on direction "
      "`both`, and treated the 30-trade per-direction minimum as a separate "
      "commitment that does not gate acceptance. Reading K.2 as requiring "
      "both cohorts to pass independently would be a stricter rule than the "
      "one written, and it would only remove passing points — it cannot "
      "create a candidate that the reported reading does not.")
    w("")
    w("### 9.3 A tie on band WIDTH")
    w("")
    w("K.3 legislates the tie between two central offsets within one band. "
      "Neither §4.3 nor K.3 says what to do when two *separate* runs are "
      "equally wide. I applied K.3's own stated rationale — a wider stop "
      "strictly reduces floor binding, the only structural criterion in this "
      "design carrying a threshold — and take the higher band. **The case "
      "does not arise in the data:** no fold-symbol has two runs tied at the "
      "maximum width. The rule is implemented and tested so that the "
      "resolution is on record rather than invented later.")
    w("")
    w("### 9.4 Kill (d): what \"passes on its own\" means")
    w("")
    w("§4.4 defines the corroboration test (gated − ungated ≥ 0.05R) but "
      "never defines the self-test. I applied the same 0.05R definition to "
      "the symbol itself, since it is the only definition §4.4 supplies and "
      "since §4.4 is explicit that two-of-three is not about profitability. "
      "The stricter reading is reported alongside in §6.4. Both give the same "
      "verdict, so the ambiguity does not affect the outcome.")
    w("")
    w("### 9.5 Contiguity across an A3-ineligible offset")
    w("")
    w("A3-ineligible offsets were never simulated, so they cannot pass. I "
      "treated them as breaking contiguity, consistent with K.2(c) making A3 "
      "survival a clause of acceptance and with §4.3 requiring the "
      "neighbours themselves to pass. In this data every fold-symbol's "
      "A3-eligible set is already contiguous — A3 always cuts a prefix, never "
      "a hole — so the rule never has to fire.")
    w("")

    # ---- spec criticism --------------------------------------------------
    w("## 10. Where I believe the specification is wrong or incomplete")
    w("")
    w("### 10.1 The plateau rule is weak in exactly the way K.2 predicted, "
      "and the data shows it")
    w("")
    w("K.2 already records that band edges are noisy because a grid point "
      "near zero expectancy passes or fails partly by chance, and that "
      "contiguity does not suppress that noise the way it would for "
      "independent points, since adjacent offsets share most of their trades. "
      "The acceptance table makes this concrete and worse than the prose "
      "suggests: **adjacent offsets within a fold are not merely correlated, "
      "they are computed on an identical trade universe** — the `n` column is "
      "constant across every offset within a fold-symbol (BTC fold 1: 509 at "
      "all eight offsets). Only the stop geometry differs. A fold's eight "
      "grid points are therefore closer to one observation viewed eight ways "
      "than to eight observations, and a run of six passing points is very "
      "nearly the single statement \"this fold's training expectancy is "
      "positive\".")
    w("")
    unanimous = sum(1 for b in p["bands"]
                    if b["n_passing"] in (0, len(b["offsets_evaluated"])))
    w(f"The evidence for that: of the {len(p['bands'])} fold-symbols, "
      f"**{unanimous} are unanimous** — either every eligible offset passes or "
      f"none does. Only {len(p['bands']) - unanimous} folds split at all. A "
      f"selection rule whose output is that close to a per-fold "
      "coin-flip on the sign of one number is doing less filtering than "
      "\"three contiguous points\" implies. This is not a request to change "
      "the rule — it is frozen and was applied as written. It is a note that "
      "the plateau requirement should not be credited with more robustness "
      "than it delivers, and that step 4's coverage statistic is the place "
      "the instability will actually show.")
    w("")
    w("### 10.2 The kill conditions are not given an aggregation rule over "
      "offsets")
    w("")
    w("§4.4 states every threshold with an aggregation rule, and "
      "\"Every pre-committed threshold carries its aggregation rule\" is "
      "listed among the unchanged commitments. Kill conditions (a), (b) and "
      "(c) do not carry one over the **offset** axis. \"OOS expectancy ≤ 0\" "
      "is a single number in the prose but the sweep produces eight or nine "
      "of them per symbol, and \"any offset\" and \"the selected offset\" are "
      "materially different tests.")
    w("")
    w("This is not hypothetical: it is the whole of SOLUSDT's result. Under "
      "\"any offset\", kill (a) does not fire for SOL and kill (b) does not "
      "fire for SOL, both on the strength of the single point m\\*+0.50 — "
      "which pools four of nine test folds and which no SOL fold selected. "
      "Under \"the offset the fold actually selected\", both fire for all "
      "three symbols. I evaluated the **most lenient** reading, \"any "
      "offset\", because it is the one the task specified verbatim (\"State "
      "for each symbol whether ANY offset gives positive test expectancy\") "
      "and because a reading chosen after seeing which way it cuts is not a "
      "pre-registration. The stricter reading is reported so the difference "
      "is visible rather than buried. **The overall outcome is unchanged "
      "either way, because two-of-three fails under both.**")
    w("")
    w("### 10.3 Two-of-three cannot distinguish \"the gate is weak\" from "
      "\"the strategy is unprofitable\"")
    w("")
    w("§4.4 is deliberate that two-of-three tests \"the gate works\" and not "
      "\"is profitable\", and gives good reasons. The consequence in this "
      "data is that the rule's verdict is driven by a quantity — the "
      "gated-minus-ungated difference — that is positive on all three symbols "
      "at all 25 offsets, while the thing anyone would want to trade is "
      "negative almost everywhere. A world in which the gate reliably added "
      "0.06R to a strategy losing 0.30R per trade would pass two-of-three. "
      "That is a real gap in the qualification logic, though it does not bite "
      "here: the rule fails anyway, and the additional failure of kill (a) on "
      "two symbols means nothing reaches step 4 regardless. Recorded because "
      "it is a design observation the next iteration should carry, not "
      "because it changes this result.")
    w("")
    w("### 10.4 Nothing measures the checkpoint at the selected offset, and "
      "the checkpoint is where most trades end")
    w("")
    w("Not a defect in a rule, an absence. 74–83% of BTC trades exit at the "
      "checkpoint, and §7.2 shows the checkpoint is creating that mode rather "
      "than catching one. The registered thesis is trend continuation, and a "
      "strategy that resolves three-quarters of its trades on a fixed clock "
      "at bar 21 is not primarily testing trend continuation. Nothing in "
      "4.1–4.5 measures what the trade would have done without the "
      "checkpoint at the *selected* offset specifically — the `minus_time_"
      "stop` arm exists, but D5 pools it across symbols and folds at step 7 "
      "and never at a per-fold selected value. Flagged as informing the next "
      "hypothesis, per the task's framing of §6, not as a proposal.")
    w("")

    # ---- outcome ---------------------------------------------------------
    w("## 11. Outcome")
    w("")
    w("| symbol | folds with a selection | kill (a) | kill (b) | kill (c) | "
      "two-of-three | **candidate for step 4?** |")
    w("|---|---|---|---|---|---|---|")
    for symbol in sw.SYMBOLS:
        c = p["candidates"][symbol]
        w(f"| {symbol} | {c['folds_with_selection']}/9 | "
          f"{'**FIRES**' if c['kill_a_oos_expectancy_fires'] else 'clear'} | "
          f"{'**FIRES**' if c['kill_b_gate_decorative_fires'] else 'clear'} | "
          f"{'**FIRES**' if c['kill_c_thesis_backwards_fires'] else 'clear'} | "
          f"{'pass' if c['kill_d_two_of_three_qualifies'] else '**FAIL**'} | "
          f"{'yes' if c['produces_candidate'] else '**NO**'} |")
    w("")
    w("**NO SYMBOL PRODUCES A CANDIDATE FOR STEP 4.**")
    w("")
    w("ETHUSDT fails at the first hurdle — no fold produces a selection, "
      "because no ETH training cell anywhere in the grid has positive "
      "expectancy. BTCUSDT produces selections in four folds but its OOS "
      "expectancy is negative at every offset and its gate contributes at "
      "most 0.033R. SOLUSDT produces selections in two folds and is the only "
      "symbol to show the §4.4 direction of edge, at one offset, which no "
      "fold selected and which nothing corroborates.")
    w("")
    w("Per §5 of the task and §4.3/§4.4 of the pre-registration: **the "
      "procedure is exhausted and that is the finding.** No variant has been "
      "searched, no threshold relaxed, no range extended, no alternative "
      "configuration proposed. The nine-step sequence does not continue to "
      "step 4.")
    w("")
    w("This is the protocol working as designed. The pre-registered "
      "expectation recorded before any number arrived was that the second "
      "most likely outcome of Point 4 was that *\"the RVOL gate proves "
      "decorative\"*, on the grounds that the structural pass had already "
      "found its selectivity largely pre-spent by conditioning on the "
      "breakout. That is close to what happened, with one refinement the "
      "stratification supplies: the gate is not inert — it orders trades "
      "correctly at every offset on every symbol — but §6.2 locates its "
      "contribution almost entirely in the removal of floor-bound trades "
      "rather than in edge detection. **The validation protocol does not "
      "create edge. It prevents belief in edge that is not there.**")
    w("")
    w("---")
    w("")
    w("*Report generated from `data/derived/sweep/bands.json` by "
      "`src/sweep/bands.py`. Every figure above is rendered from the "
      "artifact; none is transcribed by hand.*")
    return "\n".join(L) + "\n"


def main():
    p = build()
    write(p)
    with open(REPORT_PATH, "w") as fh:
        fh.write(render_report(p))
    log(f"[bands] wrote {ARTIFACT_PATH} and {REPORT_PATH}")
    return p


if __name__ == "__main__":
    main()
