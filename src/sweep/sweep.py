"""Step 2 of the §4.4 sequence: THE SWEEP.

Simulates every A3-surviving grid point across all folds, symbols and arms, and
produces the per-cell statistics that steps 3 through 8 consume. It performs NO
band identification, NO plateau selection, NO collapse, NO two-of-three, NO D5
drop decision, NO top-5% removal and NO sensitivity probe. Those are later
steps, reviewed between each. This module produces inputs and stops.

Appendix K.2's acceptance definition is deliberately NOT applied here either:
expectancy and counts are reported, and whether a grid point passes is decided
at step 3.

THE POPULATION CONTRACT
=======================

Five significant defects in Point 4 have been the same error -- a quantity
measured on one population and applied to another, invisible because both had
the same name (Appendices F.1, H, M.1, M.2, and report 12's n_ungated). This
module spans more populations than any previous one, so every figure it emits
carries its population explicitly, drawn from a closed set:

    ungated     every simulated signal, before any RVOL filter
    breakout    bars passing Donchian-20 + EMA20/EMA50, pre-RVOL (a BAR
                population, not a trade population -- it has counts and binding
                rates and no expectancy)
    gated_30    ungated filtered at the 30% pass-rate threshold
    gated_50    ungated filtered at the 50% pass-rate threshold
    gated_70    ungated filtered at the 70% pass-rate threshold

crossed with exactly one of train / test and exactly one of long / short / both.
`validate_records` refuses any record missing a label, and a test plants the
mutation of stripping one.

ARMS, AND WHICH ARE FILTERS
===========================

§4.5 runs signal mode so gated arms are FILTERS of one ungated simulation and
share an identical trade universe by construction. That holds for the RVOL
arms. It does NOT hold for two of the five decomposition arms, so this module
states for each how it was produced:

    full             FILTER of the base simulation, at gated_30/50/70.
    minus_rvol       FILTER of the base simulation, at ungated. Same universe.
    minus_ema        RE-SIMULATED. Dropping the trend filter ADMITS bars the
                     baseline never generated, so the arm is a strict SUPERSET
                     and cannot be a filter of anything.
    minus_time_stop  RE-SIMULATED. Identical signal universe -- the checkpoint
                     changes when a trade exits, not whether it exists.
    minus_max_hold   NOT RUNNABLE. See MAX_HOLD_BLOCKER below.

MAX_HOLD_BLOCKER. `costs.CostConfig.max_hold_bars` is a read-only property
fixed at 2 x donchian_period and documented "NOT independently sweepable".
Removing the cap therefore requires either changing donchian_period, which
changes the signal itself and so is not a leave-one-out, or introducing a
replacement holding horizon. No such horizon is pre-registered, and inventing
one post-lift is exactly the move this design forbids. The arm is reported as
BLOCKED rather than run against a fabricated parameter. §4.4 never drops
max-hold in any case -- it is a GUARD RAIL, "measured and reported, NEVER
dropped" -- so the arm is descriptive and nothing downstream is gated on it.
"""

import json
import math
import os
import sys

import numpy as np
import pandas as pd

from src.folds import schedule as sch
from src.sweep import grid as gr

sys.path.insert(0, os.path.join(sch.ROOT, "src", "engine"))

import contracts  # noqa: E402
import costs  # noqa: E402
import signals as sg  # noqa: E402
import simulate  # noqa: E402

SYMBOLS = gr.SYMBOLS
OUT_DIR = os.path.join(sch.DERIVED, "sweep")
TRADES_DIR = os.path.join(OUT_DIR, "trades")
CELLS_PATH = os.path.join(OUT_DIR, "sweep_cells.jsonl")
ARTIFACT_PATH = os.path.join(OUT_DIR, "sweep.json")
CHECKPOINT_PATH = os.path.join(OUT_DIR, "sweep_checkpoint.json")
REPORT_PATH = os.path.join(sch.ROOT, "reports", "14_sweep.md")

log = sch.log

# ---- the closed label sets. Nothing may be emitted outside them. ----------
POPULATIONS = ("ungated", "breakout", "gated_30", "gated_50", "gated_70")
PERIODS = ("train", "test")
DIRECTIONS = ("both", "long", "short")
ARMS = ("full", "minus_rvol", "minus_ema", "minus_time_stop", "minus_max_hold")
LABEL_KEYS = ("population", "period", "direction", "arm")

# Which population each arm is reported on, and how it was produced.
ARM_SPEC = {
    "full":            {"populations": ("gated_30", "gated_50", "gated_70"),
                        "production": "filter", "simulation": "base"},
    "minus_rvol":      {"populations": ("ungated",),
                        "production": "filter", "simulation": "base"},
    "minus_ema":       {"populations": ("gated_50",),
                        "production": "resimulated", "simulation": "no_ema"},
    "minus_time_stop": {"populations": ("gated_50",),
                        "production": "resimulated", "simulation": "no_time_stop"},
    "minus_max_hold":  {"populations": (),
                        "production": "BLOCKED", "simulation": None},
}

RVOL_POP = {0.30: "gated_30", 0.50: "gated_50", 0.70: "gated_70"}

# ---- §4.4 evidence minimums. THESE DO NOT MOVE. --------------------------
MIN_TRAIN_TRADES = 200
MIN_TEST_TRADES = 50
MIN_DIRECTION_TRADES = 30
PERIOD_MINIMUM = {"train": MIN_TRAIN_TRADES, "test": MIN_TEST_TRADES}

# ---- Appendix M.1: the engine-derived bound on r_multiple ----------------
R_LOWER_BOUND = -1.2
R_UPPER_BOUND = 2.0

TOP_OFFSET = gr.GRID_OFFSET_MAX          # 2.50, ineligible per §4.3
BASELINE_DAYS = gr.BASELINE_DAYS
RISK_USD = 20.0


class PopulationLabelError(AssertionError):
    """A figure was emitted without saying what population it came from."""


# ---------------------------------------------------------------------------
# configuration
# ---------------------------------------------------------------------------

def eligible_offsets(grid_json, symbol, fold_id, top_offset=TOP_OFFSET):
    """A3-surviving offsets with the top grid point removed.

    §4.3's plateau rule requires passing neighbours on BOTH sides, which the
    edge of the searched range can never have, so offset 2.50 is ineligible for
    selection and is not simulated.
    """
    fold = grid_json["prescreen"][symbol]["folds"][str(fold_id)]
    surv = sorted(float(o) for o in fold["summary"]["surviving_offsets"])
    return [o for o in surv if o < top_offset - 1e-9]


def cfg_for(cell, offset, time_stop_enabled=True):
    """The engine config for one grid point. No parameter is defaulted."""
    idx = int(round(offset / gr.GRID_STEP))
    return costs.CostConfig(
        stop_atr_mult=float(cell["multipliers"][idx]),
        stop_max_pct=float(cell["stop_max_pct"]),
        # Irrelevant to an ungated simulation; the arms are cut afterwards.
        rvol_threshold=float(cell["rvol_thresholds"]["0.5"]["threshold"]),
        baseline_days=BASELINE_DAYS,
        time_stop_enabled=time_stop_enabled)


def rvol_thresholds(cell):
    return {t: float(cell["rvol_thresholds"][str(t)]["threshold"])
            for t in (0.30, 0.50, 0.70)}


# ---------------------------------------------------------------------------
# signals -- generated ONCE per (fold, symbol, period), reused at every offset
# ---------------------------------------------------------------------------

def period_bounds(fold, period):
    if period == "train":
        return fold["train_start"], fold["train_end"]
    if period == "test":
        return fold["test_start"], fold["test_end"]
    raise ValueError(f"unknown period {period!r}")


def period_signals(bars15, fold, period, symbol, cfg, apply_ema_filter=True):
    """Ungated signal bars inside one period, indicators from warmup_start.

    Signals do NOT depend on stop_atr_mult or stop_max_pct, so this is computed
    once per (fold, symbol, period, ema-variant) and reused at every offset.
    That is a pure saving, not an approximation: a test asserts the signal set
    is invariant to the swept parameters.
    """
    lo = sch.day_start_ms(fold["warmup_start"])
    a, b = period_bounds(fold, period)
    hi = sch.day_last_bar_ms(b)
    span = bars15[(bars15["ts"] >= lo) & (bars15["ts"] <= hi)].reset_index(
        drop=True)
    sig = sg.generate_signals(span, sg.SignalParams(), symbol, cfg,
                              apply_rvol_gate=False,
                              apply_ema_filter=apply_ema_filter)
    if len(sig) == 0:
        return sig
    return sig[sig["signal_bar_ts"] >= sch.day_start_ms(a)].reset_index(
        drop=True)


# ---------------------------------------------------------------------------
# metrics -- every one of them labelled by its caller
# ---------------------------------------------------------------------------

def _mean(a):
    a = np.asarray(a, float)
    return float(a.mean()) if a.size else None


def expectancy_metrics(trades):
    """Every per-cell figure §4.5 asks for. Carries NO labels of its own.

    Labels are attached by `record()`, which is the only way a figure reaches
    the artifact -- so a figure cannot arrive unlabelled by accident.
    """
    n = int(len(trades))
    if n == 0:
        return {"n": 0, "expectancy_r": None, "se_r": None, "sigma_r": None,
                "expectancy_per_bar_r": None, "floor_binding_rate": None,
                "cap_binding_rate": None, "atr_binding_rate": None,
                "exit_reasons": {}, "holding_stop": None,
                "holding_target": None, "min_r": None, "max_r": None}
    r = trades["r_multiple"].to_numpy(float)
    bars = trades["bars_held"].to_numpy(float)
    sigma = float(r.std(ddof=1)) if n > 1 else None
    mech = trades["stop_binding_mechanism"]
    total_bars = float(bars.sum())
    out = {
        "n": n,
        "expectancy_r": _mean(r),
        "sigma_r": sigma,
        "se_r": (None if sigma is None else float(sigma / math.sqrt(n))),
        # R per BAR OF EXPOSURE: total R over total bars held. §4.5's secondary
        # metric, which exists so a per-trade result driven purely by holding
        # time is visible as such. It never overrides the primary metric.
        "expectancy_per_bar_r": (float(r.sum() / total_bars)
                                 if total_bars > 0 else None),
        "floor_binding_rate": float((mech == "floor").mean()),
        "cap_binding_rate": float((mech == "cap").mean()),
        "atr_binding_rate": float((mech == "atr").mean()),
        "exit_reasons": {k: int((trades["exit_reason"] == k).sum())
                         for k in simulate.EXIT_REASONS},
        "min_r": float(r.min()),
        "max_r": float(r.max()),
    }
    # §4.5's D6: holding time is degenerate by construction for the time-stop
    # and max-hold exits, so the question is answerable ONLY on stop and target.
    for reason in ("stop", "target"):
        sub = trades[trades["exit_reason"] == reason]
        if len(sub) == 0:
            out[f"holding_{reason}"] = None
            continue
        b = sub["bars_held"].to_numpy(float)
        out[f"holding_{reason}"] = {
            "n": int(len(b)), "min": float(b.min()), "max": float(b.max()),
            "median": float(np.median(b)), "mean": float(b.mean()),
            "p90": float(np.percentile(b, 90)),
        }
    return out


def stratify_by_floor(trades, period):
    """Appendix J: expectancy split into floor-bound and non-floor-bound.

    Required for EVERY arm comparison, not just gated-versus-ungated: the
    reasoning in Appendix I.1 is about differing floor-binding composition, and
    that is not specific to the RVOL pair.

    A stratum below the period's evidence minimum is REPORTED AS SUCH and its
    expectancy is withheld. The minimums do not move.
    """
    mech = trades["stop_binding_mechanism"]
    minimum = PERIOD_MINIMUM[period]
    out = {}
    for name, sub in (("floor_bound", trades[mech == "floor"]),
                      ("not_floor_bound", trades[mech != "floor"])):
        n = int(len(sub))
        if n < minimum:
            out[name] = {"n": n, "expectancy_r": None, "se_r": None,
                         "below_evidence_minimum": True, "minimum": minimum}
        else:
            r = sub["r_multiple"].to_numpy(float)
            sigma = float(r.std(ddof=1))
            out[name] = {"n": n, "expectancy_r": _mean(r),
                         "se_r": float(sigma / math.sqrt(n)),
                         "below_evidence_minimum": False, "minimum": minimum}
    return out


def record(fold_id, symbol, offset, multiplier, arm, population, period,
           direction, metrics, extra=None):
    """The ONLY constructor for an artifact record. Labels are mandatory."""
    if population not in POPULATIONS:
        raise PopulationLabelError(f"unknown population {population!r}")
    if period not in PERIODS:
        raise PopulationLabelError(f"unknown period {period!r}")
    if direction not in DIRECTIONS:
        raise PopulationLabelError(f"unknown direction {direction!r}")
    if arm not in ARMS:
        raise PopulationLabelError(f"unknown arm {arm!r}")
    row = {"fold_id": int(fold_id), "symbol": symbol,
           "offset": float(offset), "multiplier": float(multiplier),
           "arm": arm, "population": population, "period": period,
           "direction": direction, "metrics": metrics}
    if extra:
        row.update(extra)
    return row


def validate_records(records, populations=POPULATIONS, arms=ARMS):
    """Every record must say which population, period, direction and arm.

    THE GUARD THE POPULATION CONTRACT RESTS ON. A record carrying figures but
    no population is exactly the defect that produced Appendices F.1, H, M.1
    and M.2, and it is invisible on inspection because the numbers look fine.

    A test strips a label and requires this to raise.
    """
    if not records:
        raise PopulationLabelError("no records to validate -- a guard with "
                                   "nothing to check passes vacuously")
    allowed = {"population": set(populations), "period": set(PERIODS),
               "direction": set(DIRECTIONS), "arm": set(arms)}
    for i, r in enumerate(records):
        for key in LABEL_KEYS:
            if key not in r:
                raise PopulationLabelError(
                    f"record {i} ({r.get('symbol')} fold {r.get('fold_id')}) "
                    f"carries figures but no {key!r} label. Every figure must "
                    f"name the population it was computed on.")
            if r[key] not in allowed[key]:
                raise PopulationLabelError(
                    f"record {i} has {key}={r[key]!r}, outside the closed set "
                    f"{sorted(allowed[key])}")
        if "metrics" not in r:
            raise PopulationLabelError(f"record {i} has no metrics block")
    return len(records)


def check_r_bounds(trades, label, tick_schedule):
    """Appendix M.1's engine-derived bound: -1.2R to +2R plus one tick."""
    if len(trades) == 0:
        return
    r = trades["r_multiple"].to_numpy(float)
    if (r < R_LOWER_BOUND).any():
        raise AssertionError(
            f"{label}: r_multiple {r.min()} below {R_LOWER_BOUND}. Appendix "
            f"M.1 makes this impossible -- ENGINE DEFECT, do not widen.")
    tk = np.array([float(tick_schedule.tick_at(int(x)))
                   for x in trades["signal_bar_ts"]], float)
    hi = R_UPPER_BOUND + trades["qty"].to_numpy(float) * tk / RISK_USD
    if (r > hi).any():
        i = int(np.argmax(r - hi))
        raise AssertionError(
            f"{label}: r_multiple {r[i]} exceeds +2R by more than one tick "
            f"(ceiling {hi[i]}). ENGINE DEFECT -- do not widen.")


# ---------------------------------------------------------------------------
# one (fold, symbol) -- the checkpoint unit
# ---------------------------------------------------------------------------

def sweep_fold_symbol(symbol, fold, cell, offsets, bars15, recs, ticks,
                      order_specs):
    """Every arm at every offset for one (fold, symbol). Returns records+trades.

    Three simulations per (period, offset):
      base           signals WITH the EMA filter, checkpoint ON
      no_ema         signals WITHOUT the EMA filter, checkpoint ON
      no_time_stop   signals WITH the EMA filter, checkpoint OFF

    `full` and `minus_rvol` are cut out of `base` by RVOL threshold, so they are
    the identical universe by construction. The other two are re-simulated for
    the reasons given in the module docstring.
    """
    thr = rvol_thresholds(cell)
    records, trade_frames = [], []
    excluded = {}

    for period in PERIODS:
        # Signals do not depend on the swept parameters, so they are built once
        # per period per ema-variant and reused across every offset.
        probe = cfg_for(cell, offsets[0])
        sig_ema = period_signals(bars15, fold, period, symbol, probe,
                                 apply_ema_filter=True)
        sig_noema = period_signals(bars15, fold, period, symbol, probe,
                                   apply_ema_filter=False)

        for offset in offsets:
            base_cfg = cfg_for(cell, offset, time_stop_enabled=True)
            nots_cfg = cfg_for(cell, offset, time_stop_enabled=False)
            mult = base_cfg.stop_atr_mult

            sims = {}
            for name, sig, ccfg in (("base", sig_ema, base_cfg),
                                    ("no_ema", sig_noema, base_cfg),
                                    ("no_time_stop", sig_ema, nots_cfg)):
                if len(sig) == 0:
                    sims[name] = (pd.DataFrame(), {"holdout_boundary": 0})
                    continue
                tr, refused, _ = simulate.run_backtest(
                    sig, {symbol: bars15}, {symbol: recs}, ccfg, ticks,
                    mode="signal", order_specs=order_specs)
                check_r_bounds(tr, f"{symbol} f{fold['fold_id']} {period} "
                                   f"off{offset} {name}", ticks[symbol])
                sims[name] = (tr, refused)
                if name == "base":
                    excluded.setdefault(period, 0)
                    excluded[period] += refused.get("holdout_boundary", 0)

            for arm, spec in ARM_SPEC.items():
                if spec["production"] == "BLOCKED":
                    continue
                trades_all, _ = sims[spec["simulation"]]
                for population in spec["populations"]:
                    if population == "ungated":
                        sub = trades_all
                    else:
                        t = float(population.split("_")[1]) / 100.0
                        sub = (trades_all[trades_all["rvol"] >= thr[t]]
                               if len(trades_all) else trades_all)
                    sub = sub.reset_index(drop=True) if len(sub) else sub
                    for direction in DIRECTIONS:
                        d = (sub if direction == "both" or not len(sub)
                             else sub[sub["direction"] == direction])
                        m = expectancy_metrics(d)
                        extra = None
                        if direction == "both" and len(d):
                            extra = {"floor_strata": stratify_by_floor(
                                d, period)}
                        records.append(record(
                            fold["fold_id"], symbol, offset, mult, arm,
                            population, period, direction, m, extra))
            # Trade tables: one row per trade, labelled with arm+population so
            # the table can never be read against the wrong population either.
            for arm, spec in ARM_SPEC.items():
                if spec["production"] == "BLOCKED":
                    continue
                t, _ = sims[spec["simulation"]]
                if not len(t):
                    continue
                keep = t.assign(fold_id=fold["fold_id"], period=period,
                                offset=offset, arm=arm,
                                rvol_thr_30=thr[0.30], rvol_thr_50=thr[0.50],
                                rvol_thr_70=thr[0.70])
                trade_frames.append(keep)

    return records, trade_frames, excluded


# ---------------------------------------------------------------------------
# the run
# ---------------------------------------------------------------------------

def load_checkpoint(path=CHECKPOINT_PATH):
    if os.path.exists(path):
        return json.load(open(path))
    return {"done": []}


def save_checkpoint(state, path=CHECKPOINT_PATH):
    with open(path, "w") as fh:
        json.dump(state, fh, indent=2, sort_keys=True)
        fh.write("\n")


def run_sweep(symbols=SYMBOLS, folds=None, grid_json=None,
              derived_dir=sch.DERIVED, resume=True):
    """Every (fold, symbol, offset, arm, period) cell. Checkpointed per unit."""
    folds = folds if folds is not None else sch.build_schedule()
    grid_json = grid_json if grid_json is not None else gr.load_grid()
    ticks = contracts.load_cache()
    order_specs = contracts.load_order_specs()
    os.makedirs(TRADES_DIR, exist_ok=True)

    state = load_checkpoint() if resume else {"done": []}
    done = set(tuple(x) for x in state["done"])
    if not resume and os.path.exists(CELLS_PATH):
        os.remove(CELLS_PATH)

    excluded_all, n_cells = {}, 0
    for symbol in symbols:
        log(f"[sweep] {symbol}: loading bars")
        bars15 = sch.load_bars(symbol, sch.DATA_START, sch.IS_END, derived_dir)
        years = sorted(set(pd.to_datetime(bars15["ts"], unit="ms",
                                          utc=True).dt.year))
        recs = simulate.load_1m(
            derived_dir, symbol,
            years=simulate.in_sample_years(set(years) | {max(years) + 1}))
        for fold in folds:
            fid = fold["fold_id"]
            key = (symbol, fid)
            cell = grid_json["symbols"][symbol][str(fid)]
            offsets = eligible_offsets(grid_json, symbol, fid)
            if key in done:
                log(f"[sweep]   fold {fid} {symbol}: cached, skipped")
                continue
            recs_out, frames, excluded = sweep_fold_symbol(
                symbol, fold, cell, offsets, bars15, recs, ticks, order_specs)
            validate_records(recs_out)
            with open(CELLS_PATH, "a") as fh:
                for r in recs_out:
                    fh.write(json.dumps(r, sort_keys=True,
                                        default=_json_default) + "\n")
            if frames:
                pd.concat(frames, ignore_index=True).to_parquet(
                    os.path.join(TRADES_DIR, f"{symbol}_f{fid}.parquet"),
                    index=False)
            excluded_all[f"{symbol}|{fid}"] = excluded
            n_cells += len(recs_out)
            done.add(key)
            state["done"] = sorted([list(k) for k in done])
            state.setdefault("excluded", {}).update(
                {f"{symbol}|{fid}": excluded})
            save_checkpoint(state)
            log(f"[sweep]   fold {fid} {symbol}: {len(offsets)} offsets, "
                f"{len(recs_out)} records, excluded {excluded}")
    return n_cells, state


def load_cells(path=CELLS_PATH):
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"sweep cells missing at {path}; run `python -m src.sweep.sweep`")
    return [json.loads(ln) for ln in open(path) if ln.strip()]


def _json_default(o):
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating,)):
        return None if not np.isfinite(o) else float(o)
    if isinstance(o, (np.bool_,)):
        return bool(o)
    raise TypeError(f"not JSON serialisable: {type(o)}")


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--fresh", action="store_true",
                    help="ignore the checkpoint and rerun every cell")
    a = ap.parse_args()
    rev = sch.git_revision()
    if rev.endswith("-dirty"):
        raise RuntimeError(
            f"working tree is dirty ({rev}); a dirty hash makes the sweep "
            f"unprovable. Commit or stash before running.")
    log(f"[sweep] HEAD {rev}")
    n, st = run_sweep(resume=not a.fresh)
    log(f"[sweep] {n} records written to {CELLS_PATH}")
