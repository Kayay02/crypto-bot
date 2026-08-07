"""A3 floor-binding pre-screen across the full grid (step 0, PRE-LIFT).

Everything here is an ENTRY-TIME computation:

    stop_pct_raw = stop_atr_mult x ATR%(t)
    floor binds when stop_pct_raw < stop_min_pct
    cap   binds when stop_pct_raw > stop_max_pct

No lifecycle resolution is needed to know that, so Layer B is never run and no
trade outcome is read. Per Appendix F.2 this is not a partial lift: it inspects
no performance figure at all.

TWO POPULATIONS, and A3 is evaluated on the second:
  (a) breakout bars       -- where the m* construction lives
  (b) gated signal bars   -- the traded population, which is what A3 is about

A3 CRITERION: floor binding < 20%, PER SYMBOL, never pooled (§4.4 -- the floors
differ, so pooling would let SOL rescue BTC on an intrinsically per-symbol
question). Applied on the 50% RVOL arm only, because that is where selection
happens; the 30% and 70% arms are reported as description.

THE RANGE IS NOT EXTENDED, and step 0 is not rerun with a different range if it
eliminates a symbol (§4.3, Appendix F.2). A symbol failing across all nine folds
is the pre-registered tradability finding, not a prompt to widen anything.
"""

import numpy as np

from src.folds import schedule as sch
from . import grid as gr

log = sch.log


def binding_rates(atr_pct_values, multiplier, floor_pct, cap_pct):
    """Floor and cap binding over one population at one multiplier.

    Both are decided on the RAW distance, before any tick rounding, exactly as
    the engine's `stop_geometry` decides its `stop_binding_mechanism`.
    """
    a = np.asarray(atr_pct_values, float)
    a = a[np.isfinite(a)]
    n = int(len(a))
    if n == 0:
        return {"n": 0, "floor": float("nan"), "cap": float("nan"),
                "atr": float("nan")}
    raw = multiplier * a
    floor = raw < floor_pct
    cap = raw > cap_pct
    return {"n": n,
            "floor": float(floor.mean()),
            "cap": float(cap.mean()),
            "atr": float((~floor & ~cap).mean())}


def gated_atr_pct(ind, rvol_threshold):
    """ATR% over breakout bars that also clear the RVOL gate.

    This is the traded population -- the one A3 is a statement about.
    """
    lo, sh = gr.breakout_masks(ind)
    brk = lo | sh
    r = ind["rvol"].to_numpy(float)
    a = gr.atr_pct(ind)
    m = brk & np.isfinite(r) & (r >= rvol_threshold) & np.isfinite(a)
    return a[m]


def prescreen_fold_symbol(symbol, fold, cell, derived_dir=sch.DERIVED,
                          baseline_days=gr.BASELINE_DAYS):
    """A3 across all eleven multipliers for one (fold, symbol).

    `cell` is the corresponding `grid.fold_symbol_grid` output, so m*, the grid
    and the cap are taken from the training fold and never recomputed here.
    """
    floor_pct = cell["stop_min_pct"]
    cap_pct = cell["stop_max_pct"]

    train = gr.breakout_frame(symbol, fold["train_start"], fold["train_end"],
                              baseline_days=baseline_days,
                              derived_dir=derived_dir)
    a_brk = gr.breakout_atr_pct(train)
    gated = {t: gated_atr_pct(train, cell["rvol_thresholds"][t]["threshold"])
             for t in gr.RVOL_TARGETS}

    # Test-period binding, DESCRIPTION ONLY. The criterion is a training-fold
    # quantity (§4.4); this is reported so drift is visible, never to select.
    test = gr.breakout_frame(symbol, fold["test_start"], fold["test_end"],
                             baseline_days=baseline_days,
                             derived_dir=derived_dir)
    a_test = gr.breakout_atr_pct(test)
    gated_test = gated_atr_pct(
        test, cell["rvol_thresholds"][gr.RVOL_TARGET_PRIMARY]["threshold"])

    rows = []
    for i, mult in enumerate(cell["multipliers"]):
        row = {
            "index": i,
            "offset": round(i * gr.GRID_STEP, 4),
            "multiplier": mult,
            "breakout": binding_rates(a_brk, mult, floor_pct, cap_pct),
            "test_breakout": binding_rates(a_test, mult, floor_pct, cap_pct),
            "test_gated_50": binding_rates(gated_test, mult, floor_pct, cap_pct),
        }
        for t in gr.RVOL_TARGETS:
            row[f"gated_{int(t * 100)}"] = binding_rates(
                gated[t], mult, floor_pct, cap_pct)
        # A3 is decided on the traded population at the 50% arm.
        row["a3_floor_binding"] = row[
            f"gated_{int(gr.RVOL_TARGET_PRIMARY * 100)}"]["floor"]
        row["a3_pass"] = bool(row["a3_floor_binding"] < gr.A3_MAX_FLOOR_BINDING)
        rows.append(row)
    return rows


def longest_run(flags):
    """Longest contiguous run of True, and the index it starts at."""
    best = cur = 0
    best_start = cur_start = None
    for i, f in enumerate(flags):
        if f:
            if cur == 0:
                cur_start = i
            cur += 1
            if cur > best:
                best, best_start = cur, cur_start
        else:
            cur = 0
    return best, best_start


def summarise(rows):
    """Surviving grid points and whether a plateau of three could exist."""
    flags = [r["a3_pass"] for r in rows]
    run, start = longest_run(flags)
    return {
        "n_surviving": int(sum(flags)),
        "surviving_offsets": [r["offset"] for r in rows if r["a3_pass"]],
        "surviving_multipliers": [r["multiplier"] for r in rows if r["a3_pass"]],
        "longest_contiguous_run": int(run),
        "run_start_offset": (None if start is None else rows[start]["offset"]),
        "viable_band": bool(run >= gr.MIN_PLATEAU_RUN),
    }


def run_prescreen(symbols=gr.SYMBOLS, folds=None, derived_dir=sch.DERIVED):
    folds = folds if folds is not None else sch.build_schedule()
    grid = gr.build_grid(symbols, folds, derived_dir)
    out = {}
    for s in symbols:
        per = {}
        for f in folds:
            cell = grid[s][f["fold_id"]]
            rows = prescreen_fold_symbol(s, f, cell, derived_dir)
            per[f["fold_id"]] = {"rows": rows, "summary": summarise(rows)}
        viable = [fid for fid, v in per.items() if v["summary"]["viable_band"]]
        out[s] = {
            "folds": per,
            "n_folds_with_viable_band": len(viable),
            "folds_with_viable_band": sorted(viable),
            # §4.4: a symbol failing throughout is a TRADABILITY finding, not a
            # kill condition, and other symbols continue independently.
            "tradable": bool(viable),
        }
    return grid, out


def _serialise(prescreen):
    out = {}
    for s, v in prescreen.items():
        out[s] = {
            "n_folds_with_viable_band": v["n_folds_with_viable_band"],
            "folds_with_viable_band": v["folds_with_viable_band"],
            "tradable": v["tradable"],
            "folds": {str(fid): {
                "summary": d["summary"],
                "a3_floor_binding_by_offset": {
                    str(r["offset"]): r["a3_floor_binding"] for r in d["rows"]},
                # The 30% and 70% arms are DESCRIPTION, never a criterion: §4.4
                # decides A3 on the 50% arm alone. They are persisted because
                # §4.3's 30/50/70 monotonicity test is the sharpest check on
                # whether the gate is real, and it cannot be read without
                # knowing how much of any observed ordering is the FLOOR
                # mechanism rather than the gate. The 70% arm admits
                # lower-volume, hence lower-ATR bars, so its floor binding is
                # higher; where it crosses 20% at an offset the 50% arm passes,
                # part of any monotonic improvement is structural.
                "a3_floor_binding_by_offset_rv30": {
                    str(r["offset"]): r["gated_30"]["floor"] for r in d["rows"]},
                "a3_floor_binding_by_offset_rv70": {
                    str(r["offset"]): r["gated_70"]["floor"] for r in d["rows"]},
                "cap_binding_by_offset": {
                    str(r["offset"]): r["gated_50"]["cap"] for r in d["rows"]},
                "breakout_floor_binding_by_offset": {
                    str(r["offset"]): r["breakout"]["floor"] for r in d["rows"]},
            } for fid, d in v["folds"].items()},
        }
    return out


if __name__ == "__main__":
    grid, pre = run_prescreen()
    payload = gr.grid_payload(grid, _serialise(pre))
    path = gr.write_grid(payload=payload)
    log(f"[grid] commit {payload['git_commit']}")
    for s in gr.SYMBOLS:
        v = pre[s]
        log(f"  {s}: viable band in {v['n_folds_with_viable_band']}/9 folds "
            f"-> {'TRADABLE' if v['tradable'] else 'NOT TRADABLE'}")
    log(f"[artifact] {path}")
