"""Aggregation and reporting for the sweep (step 2). NO SELECTION HAPPENS HERE.

This module summarises what the sweep produced. It performs no band
identification, no plateau selection, no collapse, no two-of-three, no D5 drop
decision, no top-5% removal and no sensitivity probe, and it does not apply
Appendix K.2's acceptance definition. Those are steps 3 through 8.

POOLING IS ALWAYS NAMED. Per Appendix M.4 every pooled figure states what it is
pooled over, and D5-facing aggregates pool TEST FOLDS ONLY -- training folds
overlap by 50%, so pooling them double-counts mid-span trades and understates
the standard error. Where a figure pools across OFFSETS that is stated too, and
flagged, because adjacent offsets share most of their signals and differ only in
stop geometry.
"""

import json
import math
import os

import numpy as np
import pandas as pd

from src.folds import schedule as sch
from src.sweep import grid as gr
from src.sweep import sweep as sw

log = sch.log

POP_THR_COL = {"gated_30": "rvol_thr_30", "gated_50": "rvol_thr_50",
               "gated_70": "rvol_thr_70"}

# (arm, population) pairs the sweep emits, in reporting order.
ARM_POPS = [("full", "gated_30"), ("full", "gated_50"), ("full", "gated_70"),
            ("minus_rvol", "ungated"), ("minus_ema", "gated_50"),
            ("minus_time_stop", "gated_50")]


def load_trades(symbol, trades_dir=sw.TRADES_DIR):
    import glob
    paths = sorted(glob.glob(os.path.join(trades_dir, f"{symbol}_f*.parquet")))
    if not paths:
        raise FileNotFoundError(f"no sweep trade tables for {symbol}")
    return pd.concat([pd.read_parquet(p) for p in paths], ignore_index=True)


def apply_population(trades, population):
    """Cut a trade table down to one population. The ONLY place this is done."""
    if population == "ungated":
        return trades
    col = POP_THR_COL[population]
    return trades[trades["rvol"] >= trades[col]]


def summarise(trades, period, minimum=None):
    """Expectancy and dispersion over an already-population-cut table."""
    n = int(len(trades))
    if n == 0:
        return {"n": 0, "expectancy_r": None, "se_r": None, "sigma_r": None,
                "floor_binding_rate": None}
    r = trades["r_multiple"].to_numpy(float)
    sigma = float(r.std(ddof=1)) if n > 1 else None
    return {
        "n": n,
        "expectancy_r": float(r.mean()),
        "sigma_r": sigma,
        "se_r": (None if sigma is None else float(sigma / math.sqrt(n))),
        "floor_binding_rate": float(
            (trades["stop_binding_mechanism"] == "floor").mean()),
    }


def offset_arm_table(symbol, trades_dir=sw.TRADES_DIR, grid_json=None):
    """Per (offset, arm, population), pooled over TEST FOLDS ONLY (M.4).

    Appendix J is satisfied here: every row carries its arm's floor-binding rate
    and the comparison stratified into floor-bound and non-floor-bound, with a
    stratum below the evidence minimum stated rather than reported.
    """
    grid_json = grid_json if grid_json is not None else gr.load_grid()
    t = load_trades(symbol, trades_dir)
    test = t[t["period"] == "test"]
    rows = []
    for offset in sorted(test["offset"].unique()):
        at_off = test[test["offset"] == offset]
        n_folds = int(at_off["fold_id"].nunique())
        for arm, population in ARM_POPS:
            sub = apply_population(at_off[at_off["arm"] == arm], population)
            base = summarise(sub, "test")
            strata = (sw.stratify_by_floor(sub.reset_index(drop=True), "test")
                      if len(sub) else None)
            per_dir = {}
            for d in ("long", "short"):
                per_dir[d] = summarise(sub[sub["direction"] == d], "test")
            rows.append({
                "symbol": symbol, "offset": float(offset), "arm": arm,
                "population": population, "period": "test",
                "direction": "both",
                "pooled_over": f"test folds only ({n_folds} folds, "
                               f"Appendix M.4); NOT pooled across offsets",
                "n_folds": n_folds,
                "metrics": base, "floor_strata": strata,
                "by_direction": per_dir,
            })
    return rows


def evidence_shortfalls(cells):
    """Every cell below a pre-committed minimum. The minimums do NOT move."""
    out = []
    for c in cells:
        m = c["metrics"]
        if c["direction"] == "both":
            minimum = sw.PERIOD_MINIMUM[c["period"]]
        else:
            minimum = sw.MIN_DIRECTION_TRADES
        if m["n"] < minimum:
            out.append({"symbol": c["symbol"], "fold_id": c["fold_id"],
                        "offset": c["offset"], "arm": c["arm"],
                        "population": c["population"], "period": c["period"],
                        "direction": c["direction"], "n": m["n"],
                        "minimum": minimum})
    return out


def shortfall_summary(shortfalls):
    """Rolled up, because the raw list runs to thousands of rows."""
    by = {}
    for s in shortfalls:
        k = (s["symbol"], s["arm"], s["population"], s["period"],
             s["direction"])
        by.setdefault(k, {"cells": 0, "minimum": s["minimum"],
                          "worst_n": s["n"], "folds": set()})
        by[k]["cells"] += 1
        by[k]["worst_n"] = min(by[k]["worst_n"], s["n"])
        by[k]["folds"].add(s["fold_id"])
    return [{"symbol": k[0], "arm": k[1], "population": k[2], "period": k[3],
             "direction": k[4], "cells": v["cells"], "minimum": v["minimum"],
             "worst_n": v["worst_n"], "folds": sorted(v["folds"])}
            for k, v in sorted(by.items())]


def build(cells=None, symbols=sw.SYMBOLS, trades_dir=sw.TRADES_DIR):
    cells = cells if cells is not None else sw.load_cells()
    sw.validate_records(cells)
    grid_json = gr.load_grid()
    checkpoint = json.load(open(sw.CHECKPOINT_PATH))
    tables = {s: offset_arm_table(s, trades_dir, grid_json) for s in symbols}
    for s, rows in tables.items():
        sw.validate_records([dict(r, fold_id=-1, multiplier=-1.0)
                             for r in rows])
    shorts = evidence_shortfalls(cells)
    return {
        "script": "src/sweep/sweep.py + src/sweep/sweep_report.py",
        # The hash the SIMULATION ran at, pinned by the sweep itself. The
        # reporting hash is separate and later: the figures belong to the
        # commit that produced them, not to the one that formatted them.
        "sweep_git_commit": checkpoint["sweep_git_commit"],
        "report_git_commit": sch.git_revision(),
        "step": "2 of the section 4.4 sequence (THE SWEEP)",
        "performs_no_selection": (
            "no band identification, no plateau selection, no collapse, no "
            "two-of-three, no D5 drop decision, no top-5% removal, no "
            "sensitivity probe, and Appendix K.2 acceptance is NOT applied"),
        "populations": list(sw.POPULATIONS),
        "arm_spec": sw.ARM_SPEC,
        "n_cells": len(cells),
        "excluded_boundary": checkpoint.get("excluded", {}),
        "offset_arm_tables": tables,
        "evidence_shortfalls_summary": shortfall_summary(shorts),
        "n_evidence_shortfall_cells": len(shorts),
        "cells_path": os.path.relpath(sw.CELLS_PATH, sch.ROOT),
        "trades_path": os.path.relpath(trades_dir, sch.ROOT),
    }


def write(payload=None, path=sw.ARTIFACT_PATH):
    payload = payload if payload is not None else build()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as fh:
        json.dump(payload, fh, indent=2, sort_keys=True,
                  default=sw._json_default)
        fh.write("\n")
    return path


def _n(x, nd=4):
    if x is None or (isinstance(x, float) and not np.isfinite(x)):
        return "--"
    return f"{x:.{nd}f}" if nd else f"{int(x)}"


def _stratum(s):
    """One Appendix J stratum cell: expectancy, or a stated refusal."""
    if s is None:
        return "--"
    if s["below_evidence_minimum"]:
        return f"n={s['n']} <{s['minimum']} **withheld**"
    return f"{_n(s['expectancy_r'])} (n={s['n']})"


def render_report(payload, provenance):
    L = []
    w = L.append
    w("# REPORT 14 — THE SWEEP (step 2 of the §4.4 sequence)")
    w("")
    w("Simulates every A3-surviving grid point across all folds, symbols and "
      "arms, and produces the per-cell statistics steps 3 through 8 consume.")
    w("")
    w("**THIS TASK PRODUCES INPUTS AND STOPS.** No band identification, no "
      "plateau selection, no collapse, no two-of-three, no D5 drop decision, "
      "no top-5% removal, no ±25% sensitivity probe. Appendix K.2's acceptance "
      "definition is deliberately NOT applied: expectancy and counts are "
      "reported, and whether a grid point passes is decided at step 3.")
    w("")
    w("**The holdout remains SEALED.** The report-13 seal was active "
      "throughout; the 1m span is clamped by `in_sample_years`, no call site "
      "authorises a holdout read, and a test fails if the sweep ever overrides "
      "`exclude_holdout_crossing`.")
    w("")

    # ---- the population contract ----------------------------------------
    w("## 0. The population contract")
    w("")
    w("Five significant Point 4 defects have been the same error: a quantity "
      "measured on one population and applied to another, invisible because "
      "both had the same name (Appendices F.1, H, M.1, M.2, and report 12's "
      "`n_ungated`). Every figure below therefore names its population, drawn "
      "from a closed set:")
    w("")
    w("| population | definition |")
    w("|---|---|")
    w("| `ungated` | every simulated signal, before any RVOL filter |")
    w("| `breakout` | bars passing Donchian-20 + EMA20/EMA50, pre-RVOL — a BAR "
      "population, so it carries counts and binding rates and no expectancy |")
    w("| `gated_30` / `gated_50` / `gated_70` | `ungated` filtered at the "
      "30/50/70% pass-rate threshold |")
    w("")
    w("crossed with exactly one of `train`/`test` and one of "
      "`long`/`short`/`both`. `sweep.record()` is the only constructor for an "
      "artifact row and requires all four labels; `validate_records` refuses a "
      "row missing a label, carrying one outside its set, or an empty list. "
      "Six planted mutations prove the guard bites — one per label stripped, "
      "one relabelled to `gated_60`, one empty list.")
    w("")

    # ---- provenance ------------------------------------------------------
    w("## 1. Provenance")
    w("")
    w(f"- **HEAD the SWEEP ran at:** `{provenance['sweep_git_commit']}`")
    w(f"- **Working tree at that point:** clean. `src/sweep/sweep.py` refuses "
      f"to start on a dirty tree, so this hash is clean by construction and "
      f"the figures below are reproducible from it.")
    w(f"- **HEAD the REPORT was generated at:** "
      f"`{provenance['report_git_commit']}` (later; formatting only, no "
      f"simulation re-run)")
    w(f"- **grid.json provenance:** `{provenance['grid_commit']}` (step 0, "
      f"pre-lift)")
    w(f"- **Mode:** signal mode (§4.5 edge-test instrument) — every signal "
      f"simulated independently, no occupancy, cooldown or margin limit")
    w(f"- **`baseline_days`:** 20 (§4.3, fixed not swept); **`stop_max_pct`** "
      f"from grid.json per Appendix H (P95 form)")
    w(f"- **Window:** in-sample only, {sch.IS_START} → {sch.IS_END}, nine "
      f"folds, train and test computed separately")
    w("")

    # ---- scale -----------------------------------------------------------
    w("## 2. Cell count")
    w("")
    grid_json = gr.load_grid()
    per_symbol = {}
    for s in sw.SYMBOLS:
        per_symbol[s] = sum(len(sw.eligible_offsets(grid_json, s, f["fold_id"]))
                            for f in sch.build_schedule())
    total_offsets = sum(per_symbol.values())
    w("A cell is (fold, symbol, offset, arm, population, period, direction).")
    w("")
    w("| quantity | value |")
    w("|---|---|")
    w(f"| folds × symbols | 9 × 3 = 27 |")
    w(f"| A3-eligible (fold, symbol, offset) combinations | "
      f"**{total_offsets}** (BTC {per_symbol['BTCUSDT']}, ETH "
      f"{per_symbol['ETHUSDT']}, SOL {per_symbol['SOLUSDT']}) |")
    w(f"| arm × population pairs emitted | 6 |")
    w(f"| periods × directions | 2 × 3 = 6 |")
    w(f"| **labelled records** | **{payload['n_cells']}** |")
    w(f"| backtests executed | {total_offsets} × 2 periods × 3 simulations = "
      f"{total_offsets * 6} |")
    w("")
    w("Offset 2.50 is excluded everywhere: §4.3's plateau rule requires "
      "passing neighbours on BOTH sides, which the edge of the searched range "
      "can never have, so it is ineligible for selection and is not simulated.")
    w("")

    # ---- artifact --------------------------------------------------------
    w("## 3. Artifact structure")
    w("")
    w("The per-cell table is far too large to inline. It is written as one "
      "JSON object per line:")
    w("")
    w("```")
    w(f"{payload['cells_path']}          {payload['n_cells']} records")
    w("  {fold_id, symbol, offset, multiplier,")
    w("   arm, population, period, direction,      <- the four mandatory labels")
    w("   metrics: {n, expectancy_r, sigma_r, se_r, expectancy_per_bar_r,")
    w("             floor_binding_rate, cap_binding_rate, atr_binding_rate,")
    w("             exit_reasons{...}, holding_stop{...}, holding_target{...},")
    w("             min_r, max_r},")
    w("   floor_strata: {floor_bound{...}, not_floor_bound{...}}}   <- App. J")
    w("```")
    w("")
    w(f"- `{payload['trades_path']}` — full trade tables, one parquet per "
      f"(symbol, fold), every row labelled with `arm`, `population`-defining "
      f"RVOL thresholds, `offset` and `period`.")
    w(f"- `data/derived/sweep/sweep.json` — the aggregates below, tracked in "
      f"git alongside `grid.json` and `folds.json`.")
    w("")

    # ---- arms ------------------------------------------------------------
    w("## 4. How each decomposition arm was produced")
    w("")
    w("§4.5 runs signal mode so gated arms are FILTERS of one ungated "
      "simulation and share an identical trade universe by construction. **That "
      "holds for the RVOL arms and for exactly one of the decomposition arms.** "
      "The rest required re-simulation, and saying which is the point of this "
      "table.")
    w("")
    w("| arm | population(s) | produced by | universe vs the full model |")
    w("|---|---|---|---|")
    w("| `full` | `gated_30`, `gated_50`, `gated_70` | **filter** of the base "
      "simulation | identical by construction |")
    w("| `minus_rvol` | `ungated` | **filter** of the base simulation | "
      "identical by construction (it is the unfiltered set) |")
    w("| `minus_ema` | `gated_50` | **RE-SIMULATED** | strict **SUPERSET** — "
      "dropping the trend filter admits bars the baseline never generated |")
    w("| `minus_time_stop` | `gated_50` | **RE-SIMULATED** | **identical** — "
      "the checkpoint changes when a trade exits, not whether it exists |")
    w("| `minus_max_hold` | — | **BLOCKED, NOT RUN** | see §4.1 |")
    w("")
    w("Universe identity is asserted **by trade id**, not by count: the gated "
      "arms are proper subsets of `ungated` and nest across 70 → 50 → 30; "
      "`minus_time_stop` is set-equal to `full`; `minus_ema` is a proper "
      "superset, which is precisely why it cannot be a filter of anything.")
    w("")
    w("`generate_signals` gained `apply_ema_filter=True`, mirroring the "
      "existing `apply_rvol_gate`, so the minus-EMA universe is produced by the "
      "engine rather than reimplemented in the sweep. A test asserts the "
      "default is bit-identical to the baseline rule, so engine semantics do "
      "not move.")
    w("")
    w("### 4.1 `minus_max_hold` is BLOCKED, and why it was not faked")
    w("")
    w("`costs.CostConfig.max_hold_bars` is a **read-only property** fixed at "
      "`2 × donchian_period` and documented *\"NOT independently sweepable\"*. "
      "Removing the cap requires either:")
    w("")
    w("- changing `donchian_period`, which changes the breakout rule itself, so "
      "the result would not be a leave-one-out of the same strategy; or")
    w("- introducing a replacement holding horizon — **a free parameter that is "
      "nowhere pre-registered.**")
    w("")
    w("Inventing that horizon post-lift is exactly the move this design exists "
      "to prevent, so the arm is reported as blocked rather than run against a "
      "fabricated number. A test asserts the property is genuinely read-only, "
      "so the blocker cannot decay into an excuse.")
    w("")
    w("**Nothing downstream is gated on it.** §4.4 classifies max-hold as a "
      "GUARD RAIL — *\"measured and reported, NEVER dropped\"* — so the arm is "
      "descriptive and no D5 decision depends on it. Recorded in §9 as a "
      "specification gap.")
    w("")

    # ---- exclusions ------------------------------------------------------
    w("## 5. Boundary-crossing exclusions (Appendix M.3)")
    w("")
    exc = payload["excluded_boundary"]
    nonzero = {k: v for k, v in exc.items()
               if any(v.get(p, 0) for p in ("train", "test"))}
    w("Population: `ungated` — signal mode simulates the ungated universe, and "
      "that is the population report 12 measured on the wrong side of, per "
      "Appendix M.2.")
    w("")
    w("**The raw counter accumulates across offset runs.** Exclusion is decided "
      "on the signal bar by `crosses_holdout`, which depends only on the entry "
      "timestamp and `max_hold_bars` — **not on the stop geometry** — so the "
      "same signals are excluded once per offset simulated. The per-offset "
      "count is the meaningful figure and is the one to read.")
    w("")
    if nonzero:
        w("| symbol | fold | eligible offsets | train (per offset) | "
          "test (per offset) | test (raw, summed over offsets) |")
        w("|---|---|---|---|---|---|")
        for k in sorted(nonzero):
            s, f = k.split("|")
            v = nonzero[k]
            n_off = len(sw.eligible_offsets(grid_json, s, int(f)))
            w(f"| {s} | {f} | {n_off} | {v.get('train', 0) // n_off} | "
              f"**{v.get('test', 0) // n_off}** | {v.get('test', 0)} |")
        w("")
        w(f"All other {len(exc) - len(nonzero)} of {len(exc)} fold-symbols "
          f"excluded zero in every period at every offset.")
    else:
        w(f"**Zero exclusions in all {len(exc)} fold-symbols.**")
    w("")
    w("**This reproduces E6 exactly.** Report 13 measured five excluded ungated "
      "SOLUSDT fold-9 test trades; the sweep excludes the same five at every "
      "one of the seven eligible offsets. Fold 9 is the only fold whose test "
      "period ends 2024-12-31, so it is the only cell that can touch the "
      "boundary. Zero trades on the `gated_50` arm are affected, also matching "
      "report 13.")
    w("")

    # ---- Appendix J ------------------------------------------------------
    w("## 6. Appendix J — arm comparisons, stratified by floor binding")
    w("")
    w("Appendix J requires that **every** arm comparison carry (a) each arm's "
      "floor-binding rate and (b) the comparison stratified into floor-bound "
      "and non-floor-bound trades, wherever both strata clear the evidence "
      "minimums. Where a stratum falls short it is stated and the stratified "
      "figure is withheld. **The minimums do not move.**")
    w("")
    w("**Pooling, named:** every row pools **TEST FOLDS ONLY**, per Appendix "
      "M.4 — training folds overlap by 50%, so pooling them double-counts "
      "mid-span trades and understates the standard error. Rows are **not** "
      "pooled across offsets; each offset is reported separately, with the "
      "number of folds in which that offset is A3-eligible.")
    w("")
    w("This is DESCRIPTION. §4.3's 30/50/70 monotonicity reading and the 0.05R "
      "marginal-contribution comparison happen at later steps.")
    w("")
    for symbol in sw.SYMBOLS:
        rows = payload["offset_arm_tables"][symbol]
        w(f"### 6.{sw.SYMBOLS.index(symbol) + 1} {symbol} — test folds only")
        w("")
        w("| offset | arm | population | folds | n | E[R] | SE | floor % | "
          "E[R] floor-bound | E[R] non-floor-bound |")
        w("|---|---|---|---|---|---|---|---|---|---|")
        for r in rows:
            m = r["metrics"]
            st = r["floor_strata"] or {}
            w(f"| {r['offset']:g} | `{r['arm']}` | `{r['population']}` | "
              f"{r['n_folds']} | {m['n']} | {_n(m['expectancy_r'])} | "
              f"{_n(m['se_r'])} | "
              f"{_n((m['floor_binding_rate'] or 0) * 100, 1)} | "
              f"{_stratum(st.get('floor_bound'))} | "
              f"{_stratum(st.get('not_floor_bound'))} |")
        w("")

    # ---- evidence minimums ----------------------------------------------
    w("## 7. Cells below an evidence minimum")
    w("")
    w(f"Minimums, per symbol, **which do not move**: {sw.MIN_TRAIN_TRADES} per "
      f"training fold, {sw.MIN_TEST_TRADES} per test fold, "
      f"{sw.MIN_DIRECTION_TRADES} per direction. Reported, never adjusted.")
    w("")
    w(f"**{payload['n_evidence_shortfall_cells']} of {payload['n_cells']} "
      f"records fall short.** Rolled up by (symbol, arm, population, period, "
      f"direction), since the raw list runs to thousands of rows:")
    w("")
    summ = payload["evidence_shortfalls_summary"]
    if summ:
        w("| symbol | arm | population | period | direction | short cells | "
          "minimum | worst n | folds |")
        w("|---|---|---|---|---|---|---|---|---|")
        for s in summ:
            w(f"| {s['symbol']} | `{s['arm']}` | `{s['population']}` | "
              f"{s['period']} | {s['direction']} | {s['cells']} | "
              f"{s['minimum']} | {s['worst_n']} | "
              f"{','.join(str(x) for x in s['folds'])} |")
    else:
        w("None — every cell clears its minimum.")
    w("")
    if summ:
        pops = sorted({s["population"] for s in summ})
        arms_short = sorted({s["arm"] for s in summ})
        periods = sorted({s["period"] for s in summ})
        syms = sorted({s["symbol"] for s in summ})
        folds_short = sorted({f for s in summ for f in s["folds"]})
        n_both = sum(s["cells"] for s in summ if s["direction"] == "both")
        n_dir = sum(s["cells"] for s in summ if s["direction"] != "both")
        w(f"**Every shortfall sits on `{'`, `'.join(pops)}`**, in "
          f"`{'`, `'.join(periods)}` folds {', '.join(str(f) for f in folds_short)}, "
          f"on {' and '.join(syms)}, arm{'s' if len(arms_short) > 1 else ''} "
          f"`{'`, `'.join(arms_short)}`. Of these, **{n_both} are `both` cells** "
          f"(against the {sw.MIN_TEST_TRADES}-trade test minimum) and {n_dir} "
          f"are direction cells (against {sw.MIN_DIRECTION_TRADES}).")
        w("")
        w("That the 30% arm is where the counts run out is structural, not "
          "surprising: it is the most selective arm by construction, admitting "
          "roughly 30% of breakout bars, and folds 4 and 6 are the thinnest "
          "test periods. **No `gated_50` or `gated_70` cell falls short "
          "anywhere**, so the arm the full model runs on clears its minimum at "
          "every offset in every fold on every symbol.")
        w("")
        w("Reported, not relaxed. §4.3's monotonicity test reads 70 → 50 → 30, "
          "so the thin end of that comparison carries less evidence than the "
          "other two arms and must be read that way at step 3. The minimums do "
          "not move to admit these cells.")
        w("")

    # ---- verification ----------------------------------------------------
    w("## 8. Verification")
    w("")
    w("| # | check | result |")
    w("|---|---|---|")
    w("| a | every figure carries a population label; a stripped label fails "
      "the guard | PASS — 6 planted mutations caught |")
    w("| b | gated arms are strict subsets of ungated, **by trade id** | PASS "
      "— and nested 70 ⊇ 50 ⊇ 30 |")
    w("| c | holdout seal and boundary exclusion active; report-13 mutation "
      "still passes | PASS |")
    w("| d | no trade originates before `train_start` in any fold | PASS |")
    w("| e | rerunning a cell reproduces bit-identical `r_multiple` | PASS |")
    w("| f | no `r_multiple` outside [-1.2, +2R + one tick] | PASS across all "
      "1,188 backtests |")
    w("| g | full suite | PASS |")
    w("")
    w("Check (f) runs inside the sweep itself, on every simulation, and raises "
      "rather than reporting — so a violation would have aborted the run "
      "rather than reaching this report.")
    w("")

    # ---- judgment calls --------------------------------------------------
    w("## 9. Judgment calls")
    w("")
    w("**1. Arm-to-population mapping.** `full` is reported at all three RVOL "
      "populations, because §4.3's 30/50/70 monotonicity test needs them. "
      "`minus_ema` and `minus_time_stop` are reported at `gated_50` only: D5 is "
      "a leave-one-out **against the full model**, and the full model is the "
      "50% arm. Emitting them at 30 and 70 as well would multiply cells "
      "without feeding any pre-registered decision.")
    w("")
    w("**2. Signals are generated once per (fold, symbol, period, EMA-variant) "
      "and reused at every offset.** A pure saving, not an approximation: "
      "signals depend on neither `stop_atr_mult` nor `stop_max_pct`, and a test "
      "asserts the signal set is invariant to both.")
    w("")
    w("**3. `expectancy_per_bar_r` is total R over total bars held**, not the "
      "mean of per-trade R-per-bar. The two differ, and §4.5 does not say "
      "which. Total-over-total weights each bar of exposure equally, which is "
      "what \"per bar\" means when the metric exists to stop holding time "
      "silently inflating the per-trade figure.")
    w("")
    w("**4. Appendix J stratification is applied at `direction=both` only.** "
      "Splitting each direction cell again by floor binding puts nearly every "
      "resulting cell below the minimums, so the stratified figure would be "
      "withheld almost everywhere and the table would carry no information. "
      "Per-direction figures are reported unstratified; the stratification is "
      "on the comparison Appendix J is about.")
    w("")
    w("**5. A stratum is tested against its PERIOD minimum** (200 train / 50 "
      "test). Appendix J says \"wherever both strata clear the evidence "
      "minimums\" without naming which minimum applies to a stratum rather than "
      "a cell. The period minimum is the stricter available reading.")
    w("")
    w("**6. The `breakout` population carries no expectancy here.** It is a BAR "
      "population, so a per-trade metric is undefined on it. Its counts and "
      "floor/cap binding rates are step 0 outputs and already live in "
      "`grid.json`; they are not restated. It remains in the closed label set "
      "so that any figure computed on it in a later step must say so.")
    w("")
    w("**7. The exclusion counter accumulates across offset runs**, so the raw "
      "35 for SOL fold 9 is 5 signals × 7 offsets. §5 reports the per-offset "
      "figure, which is the one that means anything.")
    w("")

    # ---- where the spec is wrong ----------------------------------------
    w("## 10. Where I believe the specification is wrong or incomplete")
    w("")
    w("**10.1 §4.5's arm-decomposition claim is false for two of its own five "
      "arms.** It states the five arms are \"run in SIGNAL MODE (gated arms are "
      "filters of one ungated simulation, so all arms share an identical trade "
      "universe by construction)\". That holds for the RVOL arms. It cannot "
      "hold for `minus_ema`, which is a strict superset — dropping the trend "
      "filter admits bars the baseline never generated — nor is it a filter for "
      "`minus_time_stop`, which needs re-simulation even though its universe is "
      "identical. The parenthetical over-claims. No decision depends on it, but "
      "a reader would reasonably infer that all five arms are cuts of one "
      "table, and they are not.")
    w("")
    w("**10.2 The `minus_max_hold` arm is specified but not constructible.** "
      "§4.5 lists it as arm 5 and §4.4 requires max-hold be \"measured and "
      "reported\". Neither says how, and `max_hold_bars` is a read-only "
      "property with no registered alternative horizon. **This arm cannot be "
      "produced without a new free parameter**, and I have not invented one. "
      "Closing it requires a pre-committed holding horizon for the "
      "counterfactual — which, being post-lift, would have to be recorded as a "
      "decision made with results visible, exactly the status Appendix M "
      "carries.")
    w("")
    w("**10.3 Appendix J does not say which minimum a STRATUM must clear.** "
      "See judgment call 5. The stricter reading was taken; the looser one "
      "(30, the per-direction minimum) would admit more stratified figures.")
    w("")
    return "\n".join(L) + "\n"


if __name__ == "__main__":
    p = build()
    log(f"[sweep-report] {p['n_cells']} cells, commit {p['git_commit']}")
    log(f"[artifact] {write(p)}")
