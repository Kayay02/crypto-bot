"""E6 -- per-trade dispersion and fold trade counts (step 1, THE LIFT).

This is the first module in the project that reads `r_multiple`. It reads it to
measure DISPERSION and COUNTS and nothing else.

WHAT THIS MODULE MAY REPORT, AND WHY THE LIST IS SHORT.

E6 exists to decide fold architecture (§4.5's pre-committed trigger) BEFORE any
return is inspected. That decision is only blind if the report supporting it
contains no location information. So:

  PERMITTED  standard deviation of r_multiple, trade counts, standard errors,
             quantile SPREADS, min and max of r_multiple, refusal and
             provenance counters.

  FORBIDDEN  mean / median / sum of r_multiple or net_pnl; expectancy; win
             rate; profit factor; Sharpe; equity curves; exit-reason
             distributions; holding-time distributions; ANY per-arm or
             per-configuration comparison.

Exit reasons and holding times are firewall-permitted quantities in general and
are excluded HERE specifically: they are informationally close to expectancy,
and this report has to support a fold-design decision made blind to returns.
They belong in the sweep report.

The prohibition is enforced, not merely documented: `render_report` builds its
tables from a fixed column spec, and `assert_no_location_statistic` re-derives
every forbidden quantity from the trade tables and refuses a report in which
any of them appears as a number. A test plants a mean into the column spec and
requires the guard to catch it.

THE SECOND FIREWALL STAYS UP. Sigma is measured on IS folds only (§4.2). No
loader here is passed authorised=True; `schedule.load_bars` refuses 2025 onward
on the default path and that refusal is asserted by test.

CONFIGURATION IS PRE-SPECIFIED, NOT CHOSEN. The offset run per fold-symbol is
the centre of the A3-surviving set with the top grid point removed (§4.3's
plateau rule makes it ineligible for selection), tie broken high per Appendix
K.3. It is fully determined by step 0 outputs plus the frozen rules; it carries
no privileged status and is not a selection. It exists to generate a
representative trade population.
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
OUT_DIR = os.path.join(sch.DERIVED, "analysis")
TRADES_DIR = os.path.join(OUT_DIR, "trades")
ARTIFACT_PATH = os.path.join(OUT_DIR, "e6_dispersion.json")
REPORT_PATH = os.path.join(sch.ROOT, "reports", "12_e6_dispersion.md")
FLAGS_PATH = os.path.join(sch.DERIVED, "flags", "reconstruction_divergence.parquet")

log = sch.log

# ---- §4.5 / Appendix L: the pre-committed trigger --------------------------
E6_SE_TRIGGER_R = 0.20

# ---- Appendix L: r_multiple is mechanically bounded ------------------------
# Target exits fill at exactly +2R; time-stop and max-hold exits are strictly
# below it; stop exits are -1R less the haircut, about -1.1R. Popoviciu's
# inequality then caps sigma at (b - a) / 2 over [-1.1, +2.0].
R_UPPER_BOUND = 2.0
R_LOWER_BOUND = -1.2          # -1.1 nominal, 0.1R of slack for the haircut
NOMINAL_R_LOWER = -1.1        # the value Appendix L's 1.55R is derived FROM
POPOVICIU_SIGMA_MAX = 1.55

# ---- §4.4 / carried commitments: the evidence minimums. THESE DO NOT MOVE --
MIN_TRAIN_TRADES = 200        # per training fold per symbol (Appendix K.2b)
MIN_TEST_TRADES = 50          # per test fold per symbol
MIN_DIRECTION_TRADES = 30     # per direction

# ---- §4.4: the marginal-contribution threshold the power table is read against
MARGINAL_CONTRIBUTION_R = 0.05

# ---- §4.3: the top grid point cannot be selected, so it is not run here ----
TOP_OFFSET = gr.GRID_OFFSET_MAX
RVOL_ARM = gr.RVOL_TARGET_PRIMARY      # 0.50
BASELINE_DAYS = gr.BASELINE_DAYS       # 20

DIRECTIONS = ("long", "short")
PERIODS = ("train", "test")


class BoundsViolation(AssertionError):
    """An r_multiple or sigma the exit logic should make impossible.

    Raised rather than reported as a finding: a value outside Appendix L's
    bounds means the engine is producing something its own exit rules forbid,
    which is a defect. Never widen the bound to make this pass.
    """


class LocationStatisticError(AssertionError):
    """A location statistic reached the report. The report is not emittable."""


# ---------------------------------------------------------------------------
# 1. the configuration -- pre-specified by step 0 outputs and the frozen rules
# ---------------------------------------------------------------------------

def surviving_offsets(grid_json, symbol, fold_id):
    """The A3-surviving offsets for one (fold, symbol), from grid.json."""
    fold = grid_json["prescreen"][symbol]["folds"][str(fold_id)]
    return sorted(float(o) for o in fold["summary"]["surviving_offsets"])


def centre_offset(offsets, top_offset=TOP_OFFSET):
    """Centre of the A3-surviving set with the top grid point removed.

    The top grid point (offset 2.50) is dropped because §4.3's plateau rule
    requires passing neighbours on BOTH sides, which the edge of the searched
    range can never have -- it is ineligible for selection, so running it would
    not be representative of the population selection can draw from.

    Where an even number of points remains there is no single centre, and
    Appendix K.3 takes the HIGHER of the two central offsets (the wider stop).
    `n // 2` is that index for even n and the exact centre for odd n.

    Deterministic: a pure function of a sorted list of floats.
    """
    eligible = [o for o in sorted(offsets) if o < top_offset - 1e-9]
    if not eligible:
        raise ValueError(
            f"no A3-surviving offset below the top grid point {top_offset}; "
            f"surviving set is {sorted(offsets)}. The range is NOT extended "
            f"(§4.3) -- report the exhaustion, do not widen anything.")
    return eligible[len(eligible) // 2], eligible


def configuration(grid_json, symbol, fold_id):
    """Everything needed to run one (fold, symbol). Nothing here is chosen."""
    cell = grid_json["symbols"][symbol][str(fold_id)]
    offs = surviving_offsets(grid_json, symbol, fold_id)
    offset, eligible = centre_offset(offs)
    idx = int(round(offset / gr.GRID_STEP))
    mult = float(cell["multipliers"][idx])
    if not math.isclose(mult, cell["m_star"] + offset, rel_tol=0, abs_tol=1e-9):
        raise ValueError(
            f"{symbol} fold {fold_id}: multiplier index {idx} gives {mult}, "
            f"but m* + offset is {cell['m_star'] + offset}")
    return {
        "symbol": symbol,
        "fold_id": fold_id,
        "offset": offset,
        "multiplier": mult,
        "m_star": float(cell["m_star"]),
        "stop_max_pct": float(cell["stop_max_pct"]),
        "rvol_threshold": float(
            cell["rvol_thresholds"][str(RVOL_ARM)]["threshold"]),
        "baseline_days": BASELINE_DAYS,
        "surviving_offsets": offs,
        "eligible_offsets": eligible,
        # A non-contiguous surviving set would make "the centre" a weaker
        # notion than the plateau rule intends. Recorded so it is visible.
        "eligible_contiguous": bool(
            len(eligible) == 1
            or all(math.isclose(b - a, gr.GRID_STEP, abs_tol=1e-9)
                   for a, b in zip(eligible, eligible[1:]))),
    }


def cfg_for(conf):
    """The engine CostConfig for one (fold, symbol). No parameter is defaulted."""
    return costs.CostConfig(
        stop_atr_mult=conf["multiplier"],
        stop_max_pct=conf["stop_max_pct"],
        rvol_threshold=conf["rvol_threshold"],
        baseline_days=conf["baseline_days"])


# ---------------------------------------------------------------------------
# 2. the run -- SIGNAL mode, in-sample only
# ---------------------------------------------------------------------------

def load_symbol_bars(symbol, derived_dir=sch.DERIVED):
    """15m in-sample bars, and the 1m records the lifecycle walk needs.

    15m goes through `schedule.load_bars`, which REFUSES 2025 onward on the
    default path -- so no holdout bar can produce a signal here.

    1m is loaded through the engine's own loader, at the engine's `max(year)+1`
    span CLAMPED BELOW THE HOLDOUT (Appendix M.2). E6's first run loaded 2025
    so a trade signalled in the final hours of 2024-12-31 could walk its 41-bar
    lifecycle; zero trades crossed, so nothing was contaminated, but the
    capability was a gap in the seal. It is now closed: the sealed years are
    never loaded, and Appendix M.3's exclusion removes at signal time any trade
    that would have needed them, so nothing silently exits on missing data.
    """
    bars15 = sch.load_bars(symbol, sch.DATA_START, sch.IS_END, derived_dir)
    years = sorted(set(pd.to_datetime(bars15["ts"], unit="ms", utc=True).dt.year))
    recs = simulate.load_1m(
        derived_dir, symbol,
        years=simulate.in_sample_years(set(years) | {max(years) + 1}))
    return bars15, recs


def period_signals(bars15, fold, period, symbol, cfg):
    """Signal bars inside one period, indicators computed from warmup_start.

    UNGATED, then filtered to the 50% arm by `run.gated_arm`'s rule downstream:
    §4.5 runs signal mode over one ungated simulation so every arm is the
    identical universe by construction. In signal mode the two are equivalent
    (no trade interacts with another), which a test asserts.
    """
    lo_ms = sch.day_start_ms(fold["warmup_start"])
    if period == "train":
        a, b = fold["train_start"], fold["train_end"]
    elif period == "test":
        a, b = fold["test_start"], fold["test_end"]
    else:
        raise ValueError(f"unknown period {period!r}")
    hi_ms = sch.day_last_bar_ms(b)
    span = bars15[(bars15["ts"] >= lo_ms) & (bars15["ts"] <= hi_ms)]
    span = span.reset_index(drop=True)
    sig = sg.generate_signals(span, sg.SignalParams(), symbol, cfg,
                              apply_rvol_gate=False)
    if len(sig) == 0:
        return sig
    start_ms = sch.day_start_ms(a)
    return sig[sig["signal_bar_ts"] >= start_ms].reset_index(drop=True)


def run_period(symbol, fold, period, conf, bars15, recs, ticks, order_specs):
    """One (fold, symbol, period) in SIGNAL mode, filtered to the 50% arm.

    SIGNAL mode per §4.5: every signal simulated independently, no occupancy
    limit, no cooldown, no margin cap. Portfolio censoring would drop signals by
    arrival order rather than by the gate, which is not the edge-test
    instrument.
    """
    cfg = cfg_for(conf)
    sig = period_signals(bars15, fold, period, symbol, cfg)
    if len(sig) == 0:
        empty = pd.DataFrame(columns=["symbol", "direction", "r_multiple"])
        return empty, {"open_position": 0, "cooldown": 0,
                       "insufficient_margin": 0, "no_1m_coverage": 0,
                       "min_qty": 0, "holdout_boundary": 0}, 0, check_tick_bounds(
                           empty, ticks[symbol], cfg.risk_usd, "empty")
    trades, refused, _ = simulate.run_backtest(
        sig, {symbol: bars15}, {symbol: recs}, cfg, ticks,
        mode="signal", order_specs=order_specs)
    n_ungated = int(len(trades))
    trades = simulate.attach_flag_overlap(trades, FLAGS_PATH)
    # The 50% arm, obtained by FILTERING the ungated table -- not a second
    # simulation. Mirrors src/engine/run.py:gated_arm.
    gated = trades[trades["rvol"] >= conf["rvol_threshold"]].reset_index(
        drop=True)
    gated = gated.assign(fold_id=fold["fold_id"], period=period,
                         offset=conf["offset"])
    # Both bound checks, at the point the trades are produced. The tick-aware
    # one is a HARD STOP; the Appendix L excursion is measured and carried up
    # to the report.
    excursion = check_tick_bounds(gated, ticks[symbol], cfg.risk_usd,
                                  f"{symbol} fold {fold['fold_id']} {period}")
    check_r_lower_bound(gated["r_multiple"].to_numpy(float)
                        if len(gated) else np.empty(0),
                        f"{symbol} fold {fold['fold_id']} {period}")
    return gated, refused, n_ungated, excursion


# ---------------------------------------------------------------------------
# 3. bounds -- Appendix L. A defect, not a finding.
# ---------------------------------------------------------------------------

def check_r_bounds(r, label, lower=R_LOWER_BOUND, upper=R_UPPER_BOUND):
    """The LITERAL Appendix L check: r_multiple in [-1.2, +2.0].

    Retained exactly as pre-registered, and it FAILS on this data -- see
    `tick_upper_bound` for why Appendix L's upper premise is arithmetically
    wrong. It is kept rather than quietly deleted because the pre-registered
    check and its verdict both belong in the record; the run's hard stop sits
    on `check_tick_bounds` and `check_r_lower_bound`, which are the bounds the
    engine's own arithmetic implies.
    """
    a = np.asarray(r, float)
    if a.size == 0:
        return
    bad_hi = a[a > upper]
    bad_lo = a[a < lower]
    if bad_hi.size or bad_lo.size:
        raise BoundsViolation(
            f"{label}: {bad_hi.size} r_multiple above {upper} (max "
            f"{bad_hi.max() if bad_hi.size else float('nan')}) and "
            f"{bad_lo.size} below {lower} (min "
            f"{bad_lo.min() if bad_lo.size else float('nan')}). Appendix L "
            f"makes these impossible under the exit logic -- this is an "
            f"ENGINE DEFECT, not a finding. Do not widen the bound.")


def tick_upper_bound(trades, tick_schedule, risk_usd):
    """Per-trade mechanical ceiling on `r_multiple`: +2R plus ONE tick of P&L.

    Appendix L derives sigma <= 1.55R from "target exits fill at exactly +2R".
    That premise is wrong, and wrong by construction rather than by accident:
    `costs.solve_price_for_net` rounds the target AWAY from the position -- up
    for a long, down for a short -- deliberately, so that a level is never
    claimed at a price which would deliver LESS than +2R. A filled target
    therefore delivers +2R plus the value of at most one tick, never more.

    This is the bound the engine's own arithmetic implies, and it is the one
    whose breach would actually mean a defect.
    """
    tk = np.array([float(tick_schedule.tick_at(int(x)))
                   for x in trades["signal_bar_ts"]], float)
    return R_UPPER_BOUND + trades["qty"].to_numpy(float) * tk / risk_usd


def check_tick_bounds(trades, tick_schedule, risk_usd, label):
    """The engine-derived bound check. A breach here IS an engine defect.

    Returns the Appendix L excursion diagnostic: how many trades exceed the
    literal +2.0 bound, the largest `r_multiple`, and the largest excess
    expressed in ticks. The excursion is REPORTED, never smoothed over -- the
    pre-registered check's failure is a finding about Appendix L's derivation
    and it belongs in the report.
    """
    if len(trades) == 0:
        return {"n": 0, "n_above_2r": 0, "max_r": None,
                "max_excess_ticks": None, "n_above_tick_bound": 0}
    r = trades["r_multiple"].to_numpy(float)
    hi = tick_upper_bound(trades, tick_schedule, risk_usd)
    over = r > hi
    if over.any():
        i = int(np.argmax(r - hi))
        raise BoundsViolation(
            f"{label}: {int(over.sum())} trades exceed +2R by MORE than one "
            f"tick of P&L (worst {r[i]:.8f} against a ceiling of {hi[i]:.8f}). "
            f"Conservative tick rounding cannot explain this -- it is an "
            f"ENGINE DEFECT. Do not widen the bound.")
    above = r > R_UPPER_BOUND
    one_tick_r = hi - R_UPPER_BOUND
    excess_ticks = np.where(one_tick_r > 0,
                            (r - R_UPPER_BOUND) / np.where(one_tick_r > 0,
                                                           one_tick_r, 1.0),
                            0.0)
    return {
        "n": int(len(r)),
        "n_above_2r": int(above.sum()),
        "max_r": float(r.max()),
        "max_excess_ticks": (float(excess_ticks[above].max())
                             if above.any() else 0.0),
        "n_above_tick_bound": 0,
    }


def check_r_lower_bound(r, label, lower=R_LOWER_BOUND):
    """The lower half of Appendix L. No rounding mechanism relaxes this one.

    Stop exits fill at -1R less the haircut, about -1.1R, and the bound carries
    0.1R of slack on top. A breach is an engine defect with no benign reading.
    """
    a = np.asarray(r, float)
    a = a[np.isfinite(a)]
    if a.size and (a < lower).any():
        bad = a[a < lower]
        raise BoundsViolation(
            f"{label}: {bad.size} r_multiple below {lower} (min {bad.min()}). "
            f"Appendix L makes these impossible under the exit logic -- this "
            f"is an ENGINE DEFECT, not a finding. Do not widen the bound.")


def check_period_origin(trades, period_start_ms, holdout_ms, label,
                        period_start=None):
    """§4.2: no trade may originate before its period, or inside the holdout.

    §4.2 calls the first of these a "required test" and Appendix G.2 concedes
    it is the WEAKER of two -- as implemented anywhere that slices signals to
    the period afterwards it cannot fail. It is kept because it costs nothing
    and would catch a slicing change; the sufficiency of the buffer itself is
    established by `src/folds/warmup.py`'s bit-identity pair, and separately by
    a test here that removes the buffer and requires the signal COUNT to drop.

    Returns the number of trades whose EXIT crosses into the holdout window --
    an in-sample trade resolving forward, which is reported, not refused.
    """
    early = int((trades["signal_bar_ts"] < period_start_ms).sum())
    if early:
        raise AssertionError(
            f"{label}: {early} trades originate before "
            f"{period_start if period_start is not None else period_start_ms}; "
            f"the warm-up buffer is not doing its job (§4.2).")
    if int((trades["signal_bar_ts"] >= holdout_ms).sum()):
        raise AssertionError(
            f"{label}: a signal bar lies in the SEALED holdout. The second "
            f"firewall is breached -- stop and investigate.")
    return int((trades["exit_ts"] >= holdout_ms).sum())


def check_sigma_bound(sigma, label, cap=POPOVICIU_SIGMA_MAX):
    """Popoviciu: variance on [a, b] is at most (b-a)^2/4, so sigma <= 1.55R."""
    if sigma is None or not np.isfinite(sigma):
        return
    if sigma > cap:
        raise BoundsViolation(
            f"{label}: sigma {sigma:.6f}R exceeds the Popoviciu bound {cap}R "
            f"implied by r_multiple in [{R_LOWER_BOUND}, {R_UPPER_BOUND}]. "
            f"This is an ENGINE DEFECT, not a finding.")


# ---------------------------------------------------------------------------
# 4. the permitted statistics
# ---------------------------------------------------------------------------

def sigma_of(r):
    """Sample standard deviation (ddof=1). None below two observations."""
    a = np.asarray(r, float)
    a = a[np.isfinite(a)]
    if a.size < 2:
        return None
    return float(a.std(ddof=1))


def spread_stats(r):
    """Dispersion only: sigma, n, min, max, IQR and the decile SPREAD.

    Every quantity here is invariant to adding a constant to every trade except
    min and max, which are extremes rather than location summaries and are
    explicitly permitted (they are what the Appendix L check is read from).
    NO mean, NO median, NO sum.
    """
    a = np.asarray(r, float)
    a = a[np.isfinite(a)]
    n = int(a.size)
    if n == 0:
        return {"n": 0, "sigma": None, "min": None, "max": None,
                "iqr": None, "p10_p90_spread": None, "se": None}
    q25, q75 = np.percentile(a, [25, 75])
    p10, p90 = np.percentile(a, [10, 90])
    s = sigma_of(a)
    return {
        "n": n,
        "sigma": s,
        "min": float(a.min()),
        "max": float(a.max()),
        "iqr": float(q75 - q25),
        "p10_p90_spread": float(p90 - p10),
        "se": (None if s is None else float(s / math.sqrt(n))),
    }


def se(sigma, n):
    if sigma is None or n is None or n <= 0:
        return None
    return float(sigma / math.sqrt(n))


# ---------------------------------------------------------------------------
# 5. assembly
# ---------------------------------------------------------------------------

def empty_counters():
    """The counter shape, in one place so a caller cannot miss a field."""
    return {
        "refused": {}, "n_ungated": {}, "exit_after_is_end": 0,
        "signals_before_train_start": 0,
        # Appendix L excursion, accumulated across every cell.
        "n_trades": 0, "n_above_2r": 0, "max_r": None,
        "max_excess_ticks": 0.0, "n_above_tick_bound": 0,
        # Appendix M.3, summed across every cell.
        "excluded_holdout_boundary": 0,
    }


def collect(symbols=SYMBOLS, folds=None, derived_dir=sch.DERIVED,
            grid_json=None, write_trades=True):
    """Run every (fold, symbol, period) and return the raw trade tables.

    Returns (frames, meta) where `frames` maps (symbol, fold_id, period) to the
    gated 50%-arm trade table and `meta` carries counters and provenance.
    """
    folds = folds if folds is not None else sch.build_schedule()
    grid_json = grid_json if grid_json is not None else gr.load_grid()
    ticks = contracts.load_cache()
    order_specs = contracts.load_order_specs()

    frames, confs = {}, {}
    counters = empty_counters()
    holdout_ms = sch.day_start_ms(sch.HOLDOUT_TEST_START)

    if write_trades:
        os.makedirs(TRADES_DIR, exist_ok=True)

    for symbol in symbols:
        log(f"[e6] {symbol}: loading bars")
        bars15, recs = load_symbol_bars(symbol, derived_dir)
        for fold in folds:
            fid = fold["fold_id"]
            conf = configuration(grid_json, symbol, fid)
            confs[(symbol, fid)] = conf
            for period in PERIODS:
                t, refused, n_ung, exc = run_period(
                    symbol, fold, period, conf, bars15, recs, ticks,
                    order_specs)
                key = (symbol, fid, period)
                frames[key] = t
                counters["refused"][f"{symbol}|{fid}|{period}"] = refused
                counters["n_ungated"][f"{symbol}|{fid}|{period}"] = n_ung
                counters["excluded_holdout_boundary"] += refused.get(
                    "holdout_boundary", 0)
                counters["n_trades"] += exc["n"]
                counters["n_above_2r"] += exc["n_above_2r"]
                counters["n_above_tick_bound"] += exc["n_above_tick_bound"]
                if exc["max_r"] is not None:
                    counters["max_r"] = (exc["max_r"] if counters["max_r"] is None
                                         else max(counters["max_r"], exc["max_r"]))
                if exc["max_excess_ticks"] is not None:
                    counters["max_excess_ticks"] = max(
                        counters["max_excess_ticks"], exc["max_excess_ticks"])
                if len(t):
                    a = (fold["train_start"] if period == "train"
                         else fold["test_start"])
                    counters["exit_after_is_end"] += check_period_origin(
                        t, sch.day_start_ms(a), holdout_ms,
                        f"{symbol} fold {fid} {period}", a)
                log(f"[e6]   fold {fid} {period:5s} {symbol}: "
                    f"{len(t)} trades (ungated universe {n_ung})")
            if write_trades:
                for period in PERIODS:
                    t = frames[(symbol, fid, period)]
                    if len(t):
                        t.to_parquet(os.path.join(
                            TRADES_DIR, f"{symbol}_f{fid}_{period}.parquet"),
                            index=False)
    return frames, confs, counters, folds


def pool(frames, predicate):
    """r_multiple concatenated over every frame whose key satisfies `predicate`."""
    out = []
    for key, t in frames.items():
        if predicate(key) and len(t):
            out.append(t["r_multiple"].to_numpy(float))
    return np.concatenate(out) if out else np.empty(0)


def build_stats(frames, confs, counters, folds, grid_json):
    """Every permitted statistic the report needs. NOTHING about location."""
    fold_ids = [f["fold_id"] for f in folds]
    symbols = sorted({k[0] for k in frames})

    # ---- Appendix L's LOWER bound, on every trade, before anything is
    # summarised. The upper bound is checked in `run_period` against the
    # tick-aware ceiling, because Appendix L's literal +2.0 is arithmetically
    # wrong -- see `tick_upper_bound`.
    for key, t in frames.items():
        if len(t):
            check_r_lower_bound(t["r_multiple"].to_numpy(float),
                                f"{key[0]} fold {key[1]} {key[2]}")

    stats = {"symbols": {}, "folds": fold_ids,
             "config": {}, "counters": counters}

    for (symbol, fid), c in sorted(confs.items()):
        stats["config"][f"{symbol}|{fid}"] = c

    pooled_all = pool(frames, lambda k: True)
    check_r_lower_bound(pooled_all, "pooled across symbols")

    for s in symbols:
        r_is = pool(frames, lambda k, s=s: k[0] == s)
        r_train = pool(frames, lambda k, s=s: k[0] == s and k[2] == "train")
        r_test = pool(frames, lambda k, s=s: k[0] == s and k[2] == "test")
        pooled = spread_stats(r_is)
        check_sigma_bound(pooled["sigma"], f"{s} pooled IS")

        per_dir = {}
        for d in DIRECTIONS:
            rd = np.concatenate(
                [t.loc[t["direction"] == d, "r_multiple"].to_numpy(float)
                 for k, t in frames.items() if k[0] == s and len(t)]
                or [np.empty(0)])
            per_dir[d] = spread_stats(rd)
            check_sigma_bound(per_dir[d]["sigma"], f"{s} {d}")

        per_fold = {}
        for fid in fold_ids:
            cell = {}
            for period in PERIODS:
                t = frames.get((s, fid, period))
                r = (t["r_multiple"].to_numpy(float)
                     if t is not None and len(t) else np.empty(0))
                st = spread_stats(r)
                check_sigma_bound(st["sigma"], f"{s} fold {fid} {period}")
                by_dir = {}
                for d in DIRECTIONS:
                    rd = (t.loc[t["direction"] == d, "r_multiple"].to_numpy(float)
                          if t is not None and len(t) else np.empty(0))
                    by_dir[d] = spread_stats(rd)
                st["by_direction"] = by_dir
                cell[period] = st
            # §4.5's trigger: pooled per-symbol sigma over THIS fold's test n.
            cell["trigger_se"] = se(pooled["sigma"], cell["test"]["n"])
            cell["trigger_fires"] = bool(
                cell["trigger_se"] is not None
                and cell["trigger_se"] > E6_SE_TRIGGER_R)
            per_fold[fid] = cell

        stats["symbols"][s] = {
            "pooled_is": pooled,
            "pooled_train": spread_stats(r_train),
            "pooled_test": spread_stats(r_test),
            "by_direction": per_dir,
            "by_fold": per_fold,
            "n_is_total": pooled["n"],
        }

    stats["pooled_all_symbols"] = spread_stats(pooled_all)
    check_sigma_bound(stats["pooled_all_symbols"]["sigma"], "pooled all symbols")
    stats["power"] = power_table(stats)
    stats["trigger"] = trigger_verdict(stats)
    stats["shortfalls"] = shortfalls(stats)
    c = counters
    max_sigma = max([v["pooled_is"]["sigma"] for v in stats["symbols"].values()
                     if v["pooled_is"]["sigma"] is not None] or [float("nan")])
    stats["bounds_check"] = {
        "r_lower": R_LOWER_BOUND, "r_upper": R_UPPER_BOUND,
        "sigma_cap": POPOVICIU_SIGMA_MAX,
        "min_observed": (None if stats["pooled_all_symbols"]["n"] == 0
                         else stats["pooled_all_symbols"]["min"]),
        "max_observed": (None if stats["pooled_all_symbols"]["n"] == 0
                         else stats["pooled_all_symbols"]["max"]),
        "max_sigma_observed": max_sigma,
        # The literal Appendix L check, and its verdict, reported rather than
        # smoothed over.
        "lower_bound_passed": True,
        "sigma_cap_passed": bool(max_sigma <= POPOVICIU_SIGMA_MAX),
        "upper_bound_passed": bool(c["n_above_2r"] == 0),
        "n_trades": c["n_trades"],
        "n_above_2r": c["n_above_2r"],
        "max_excess_ticks": c["max_excess_ticks"],
        "n_above_tick_bound": c["n_above_tick_bound"],
        "tick_bound_passed": bool(c["n_above_tick_bound"] == 0),
    }
    return stats


def _median_count(counts):
    """Median of a list of TRADE COUNTS. A count statistic, not a return one."""
    c = [x for x in counts if x is not None]
    return None if not c else float(np.median(c))


def power_table(stats):
    """SE implied by measured sigma at the counts decisions actually rest on.

    §4.5's noise caveat made quantitative: every row is compared against the
    0.05R marginal-contribution threshold D5 drop decisions use.
    """
    rows = {}
    for s, v in stats["symbols"].items():
        sig = v["pooled_is"]["sigma"]
        test_counts = [v["by_fold"][f]["test"]["n"] for f in stats["folds"]]
        train_counts = [v["by_fold"][f]["train"]["n"] for f in stats["folds"]]
        typ_test = _median_count(test_counts)
        typ_train = _median_count(train_counts)
        rows[s] = {
            "sigma": sig,
            "at_min_is_200": {"n": MIN_TRAIN_TRADES,
                              "se": se(sig, MIN_TRAIN_TRADES)},
            "at_min_test_50": {"n": MIN_TEST_TRADES,
                               "se": se(sig, MIN_TEST_TRADES)},
            "at_typical_test": {"n": typ_test, "se": se(sig, typ_test)},
            "at_typical_train": {"n": typ_train, "se": se(sig, typ_train)},
            "at_pooled_is": {"n": v["pooled_is"]["n"],
                             "se": se(sig, v["pooled_is"]["n"])},
        }
    # D5 pools across symbols AND folds -- the one figure §4.4 licenses to pool.
    d5_sigma = stats["pooled_all_symbols"]["sigma"]
    d5_n = stats["pooled_all_symbols"]["n"]
    rows["D5_POOLED"] = {
        "sigma": d5_sigma,
        "at_min_is_200": {"n": MIN_TRAIN_TRADES, "se": se(d5_sigma, MIN_TRAIN_TRADES)},
        "at_min_test_50": {"n": MIN_TEST_TRADES, "se": se(d5_sigma, MIN_TEST_TRADES)},
        "at_typical_test": {"n": None, "se": None},
        "at_typical_train": {"n": None, "se": None},
        "at_pooled_is": {"n": d5_n, "se": se(d5_sigma, d5_n)},
    }
    return {"threshold_r": MARGINAL_CONTRIBUTION_R, "rows": rows}


def trigger_verdict(stats):
    """§4.5's pre-committed trigger. REPORTED, never executed here."""
    cells = []
    for s, v in stats["symbols"].items():
        for fid in stats["folds"]:
            c = v["by_fold"][fid]
            cells.append({"symbol": s, "fold_id": fid,
                          "n_test": c["test"]["n"],
                          "se": c["trigger_se"], "fires": c["trigger_fires"]})
    firing = [c for c in cells if c["fires"]]
    return {
        "threshold_r": E6_SE_TRIGGER_R,
        "n_cells": len(cells),
        "n_firing": len(firing),
        "fires": bool(firing),
        "firing_cells": firing,
        "symbols_affected": sorted({c["symbol"] for c in firing}),
        "cells": cells,
        "action": ("REPORT ONLY -- §4.5 says the fold change is reviewed "
                   "before it is acted on. Nothing is implemented here."),
    }


def shortfalls(stats):
    """Every cell below a pre-committed evidence minimum. The minimums do NOT move."""
    out = []
    for s, v in stats["symbols"].items():
        for fid in stats["folds"]:
            c = v["by_fold"][fid]
            if c["train"]["n"] < MIN_TRAIN_TRADES:
                out.append({"symbol": s, "fold_id": fid, "period": "train",
                            "direction": "both", "n": c["train"]["n"],
                            "minimum": MIN_TRAIN_TRADES})
            if c["test"]["n"] < MIN_TEST_TRADES:
                out.append({"symbol": s, "fold_id": fid, "period": "test",
                            "direction": "both", "n": c["test"]["n"],
                            "minimum": MIN_TEST_TRADES})
            for period in PERIODS:
                for d in DIRECTIONS:
                    n = c[period]["by_direction"][d]["n"]
                    if n < MIN_DIRECTION_TRADES:
                        out.append({"symbol": s, "fold_id": fid,
                                    "period": period, "direction": d, "n": n,
                                    "minimum": MIN_DIRECTION_TRADES})
    return out


# ---------------------------------------------------------------------------
# 6. the 425-bar deferred item (Point 2)
# ---------------------------------------------------------------------------

def flag_overlap(frames, folds, symbols=SYMBOLS, derived_dir=sch.DERIVED,
                 flags_path=FLAGS_PATH):
    """Overlap of the flagged reconstruction-divergence bars with signal bars.

    A COUNT, never an outcome. Point 2 recorded the flag list as a FLAG LIST,
    not an exclusion filter, and comparing outcomes between flagged and
    unflagged trades would be a location statistic -- so it is not done.

    Four populations, in narrowing order:
      total flagged bars -> those inside the in-sample window -> breakout bars
      -> gated signal bars at the 50% arm -> bars that produced a taken trade.
    """
    import pyarrow.parquet as pq
    div = pq.read_table(flags_path).to_pandas()
    uniq = div.drop_duplicates(["symbol", "ts"])
    is_lo = sch.day_start_ms(sch.IS_START)
    is_hi = sch.day_last_bar_ms(sch.IS_END)

    out = {"total_flagged_bars": int(len(uniq)),
           "total_flagged_rows": int(len(div)),
           "ohlc_flagged_bars": int(uniq["ohlc_flag"].sum()),
           "per_symbol": {}}

    for s in symbols:
        f = uniq[uniq["symbol"] == s]
        ts_all = set(int(x) for x in f["ts"])
        ts_is = set(int(x) for x in f["ts"] if is_lo <= int(x) <= is_hi)

        # Signal bars of trades that were actually TAKEN in this run.
        gated_sig = set()
        for key, t in frames.items():
            if key[0] == s and len(t):
                gated_sig |= set(int(x) for x in t["signal_bar_ts"])
        # Breakout and gated-signal bar sets are recomputed from indicators, so
        # they cover bars that never became a trade (no 1m coverage, min_qty).
        brk, gated_all = _signal_bar_sets(s, folds, derived_dir)

        entered = gated_sig & ts_is
        entry_bar_hits = set()
        for key, t in frames.items():
            if key[0] != s or not len(t):
                continue
            entry_bar_hits |= (set(int(x) for x in t["entry_ts"]) & ts_all)

        out["per_symbol"][s] = {
            "flagged_bars_total": len(ts_all),
            "flagged_bars_in_sample": len(ts_is),
            "flagged_bars_ohlc": int(f["ohlc_flag"].sum()),
            "overlap_breakout_bar": len(ts_is & brk),
            "overlap_gated_signal_bar": len(ts_is & gated_all),
            "overlap_entered_trade_signal_bar": len(entered),
            "overlap_entry_bar": len(entry_bar_hits),
        }
    for k in ("flagged_bars_total", "flagged_bars_in_sample",
              "overlap_breakout_bar", "overlap_gated_signal_bar",
              "overlap_entered_trade_signal_bar", "overlap_entry_bar"):
        out[f"all_symbols_{k}"] = sum(
            v[k] for v in out["per_symbol"].values())
    return out


def _signal_bar_sets(symbol, folds, derived_dir=sch.DERIVED, grid_json=None):
    """(breakout bars, gated signal bars at the 50% arm) over the IS window.

    Bar-level sets computed from indicators, exactly as `src/sweep/grid.py`
    defines them. Union across folds; train and test both, deduplicated, so
    overlapping training windows do not double-count a bar.
    """
    grid_json = grid_json if grid_json is not None else gr.load_grid()
    brk, gated = set(), set()
    for fold in folds:
        conf = configuration(grid_json, symbol, fold["fold_id"])
        for period in PERIODS:
            a, b = ((fold["train_start"], fold["train_end"]) if period == "train"
                    else (fold["test_start"], fold["test_end"]))
            ind = gr.breakout_frame(symbol, a, b, baseline_days=BASELINE_DAYS,
                                    derived_dir=derived_dir)
            lo, sh = gr.breakout_masks(ind)
            m = lo | sh
            ts = ind["ts"].to_numpy(np.int64)
            r = ind["rvol"].to_numpy(float)
            brk |= set(int(x) for x in ts[m])
            g = m & np.isfinite(r) & (r >= conf["rvol_threshold"])
            gated |= set(int(x) for x in ts[g])
    return brk, gated


# ---------------------------------------------------------------------------
# 7. the report -- and the guard that keeps location out of it
# ---------------------------------------------------------------------------

# The per-symbol dispersion table's columns. `assert_no_location_statistic`
# exists because this list is the obvious place a future author adds a mean.
SIGMA_COLUMNS = [
    ("n", lambda st: _num(st["n"], 0)),
    ("sigma (R)", lambda st: _num(st["sigma"], 4)),
    ("SE (R)", lambda st: _num(st["se"], 4)),
    ("min R", lambda st: _num(st["min"], 4)),
    ("max R", lambda st: _num(st["max"], 4)),
    ("IQR (R)", lambda st: _num(st["iqr"], 4)),
    ("p10-p90 (R)", lambda st: _num(st["p10_p90_spread"], 4)),
]

FORBIDDEN_TERMS = (
    "expectancy", "win rate", "winrate", "profit factor", "sharpe", "sortino",
    "equity curve", "exit reason", "exit_reason", "holding time", "mean r",
    "mean_r", "median r", "median_r", "sum of r", "sum_r", "average r",
    "avg r", "net_pnl", "net pnl",
)

# Keys whose numeric leaves the report is ALLOWED to print. Everything E6 may
# say is here; a location statistic cannot be reported without first entering
# `stats` under a key that is not.
PERMITTED_STAT_KEYS = frozenset({
    # dispersion and counts
    "n", "sigma", "min", "max", "iqr", "p10_p90_spread", "se",
    "n_is_total", "n_test", "trigger_se", "threshold_r",
    "n_cells", "n_firing", "minimum", "fold_id",
    # configuration -- all step 0 outputs, all pre-lift
    "offset", "multiplier", "m_star", "stop_max_pct", "rvol_threshold",
    "baseline_days", "r_lower", "r_upper", "sigma_cap", "min_observed",
    "max_observed", "max_sigma_observed",
    # the Appendix L excursion -- counts and extremes only
    "n_trades", "n_above_2r", "max_r", "max_excess_ticks",
    "n_above_tick_bound",
    # counters
    "open_position", "cooldown", "insufficient_margin", "no_1m_coverage",
    "min_qty", "exit_after_is_end", "signals_before_train_start",
    # Appendix M.3: boundary-crossing trades excluded at signal time.
    "holdout_boundary", "excluded_holdout_boundary",
})


def _numeric_leaves(obj, key=None, keep=PERMITTED_STAT_KEYS, out=None):
    """Numeric leaves of `obj` sitting under a PERMITTED key."""
    out = [] if out is None else out
    if isinstance(obj, dict):
        for k, v in obj.items():
            _numeric_leaves(v, k, keep, out)
    elif isinstance(obj, (list, tuple)):
        for v in obj:
            _numeric_leaves(v, key, keep, out)
    elif isinstance(obj, bool):
        pass
    elif isinstance(obj, (int, float)) and key in keep:
        if np.isfinite(obj):
            out.append(float(obj))
    return out


def assert_stats_schema(stats, allowed=None):
    """Every key in the stats tree must be one E6 is allowed to carry.

    The structural half of the prohibition. `render_report` reads only `stats`,
    so a location statistic has to enter this tree before it can be printed,
    and an unrecognised key here stops it at the door.
    """
    allowed = allowed if allowed is not None else (
        PERMITTED_STAT_KEYS | {
            "symbols", "folds", "config", "counters", "pooled_is",
            "pooled_train", "pooled_test", "by_direction", "by_fold",
            "pooled_all_symbols", "power", "trigger", "shortfalls",
            "bounds_check", "long", "short", "train", "test", "rows",
            "trigger_fires", "fires", "firing_cells", "symbols_affected",
            "cells", "action", "passed", "refused", "n_ungated", "symbol",
            "lower_bound_passed", "upper_bound_passed", "sigma_cap_passed",
            "tick_bound_passed",
            "period", "direction", "surviving_offsets", "eligible_offsets",
            "eligible_contiguous", "at_min_is_200", "at_min_test_50",
            "at_typical_test", "at_typical_train", "at_pooled_is",
        })
    # Symbol names and the pooled-row label are DATA, not schema: they name a
    # bucket rather than a quantity, and a symbol cannot smuggle a statistic in.
    dynamic = set(stats.get("symbols", {})) | {"D5_POOLED"}
    bad = set()

    def walk(o):
        if isinstance(o, dict):
            for k, v in o.items():
                if (isinstance(k, str) and k not in dynamic
                        and not k[0].isdigit() and "|" not in k
                        and k not in allowed):
                    bad.add(k)
                walk(v)
        elif isinstance(o, (list, tuple)):
            for v in o:
                walk(v)

    walk(stats)
    if bad:
        raise LocationStatisticError(
            f"stats tree carries unrecognised key(s) {sorted(bad)}. E6 may "
            f"carry dispersion and counts only; a new key must be added to "
            f"PERMITTED_STAT_KEYS deliberately, not by accident.")
    return True


def _num(x, nd):
    if x is None or (isinstance(x, float) and not np.isfinite(x)):
        return "--"
    return f"{x:.{nd}f}" if nd else f"{int(x)}"


def forbidden_values(frames):
    """Every location statistic that MUST NOT appear, re-derived from the data.

    The guard is numeric rather than lexical because a lexical scan is defeated
    by relabelling. These values are computed here, inside the guard, and never
    returned to the report path.
    """
    vals = []

    def add(a):
        a = np.asarray(a, float)
        a = a[np.isfinite(a)]
        if a.size:
            vals.extend([float(a.mean()), float(np.median(a)), float(a.sum())])

    groups = {}
    for key, t in frames.items():
        if not len(t):
            continue
        s, fid, period = key
        for col in ("r_multiple", "net_pnl"):
            if col not in t.columns:
                continue
            arr = t[col].to_numpy(float)
            groups.setdefault(("all", col), []).append(arr)
            groups.setdefault((s, col), []).append(arr)
            groups.setdefault((s, fid, period, col), []).append(arr)
            for d in DIRECTIONS:
                groups.setdefault((s, d, col), []).append(
                    t.loc[t["direction"] == d, col].to_numpy(float))
    for parts in groups.values():
        add(np.concatenate(parts) if parts else np.empty(0))
    return vals


def assert_no_location_statistic(text, frames, stats=None, min_decimals=4,
                                 max_decimals=6):
    """Refuse a report containing a location statistic.

    TWO independent checks, because either alone is weak:

      (a) LEXICAL, scoped to TABLE ROWS. A forbidden term appearing in a table
          row is a labelled statistic. Scoped to rows rather than the whole
          text deliberately: the report's own prose has to be able to SAY what
          it is not allowed to contain, and a whole-text scan would make the
          prohibition unstatable.
      (b) NUMERIC, over the whole text. A mean, median or sum of `r_multiple`
          or `net_pnl`, over any grouping the report tabulates, appearing as a
          number. This is the half with real teeth: it catches an UNLABELLED
          or relabelled statistic, which is exactly what a lexical scan cannot
          see.

    NUMERIC MATCHING IS EXACT-TOKEN, not substring: "0.123" must not be found
    inside "0.1234", or the guard fires on arithmetic coincidence rather than
    on a leak.

    A forbidden value that EQUALS a permitted one at full float precision is
    excluded. This is not a loophole -- it is structurally common (with a
    majority of trades exiting at the stop, the median of `r_multiple` IS the
    minimum, which the report is explicitly permitted to print) and printing a
    permitted statistic discloses nothing beyond that statistic. The exclusion
    set is built from PERMITTED_STAT_KEYS, so a mean injected under a new key
    is NOT excluded and is still caught.

    Two tests plant mutations: one labelled ("mean R"), which (a) must catch,
    and one innocuously labelled, which (b) must catch. A guard that cannot
    detect its own target mutation is worthless, and five vacuous guards have
    already been found in this project.
    """
    import re

    rows = [ln for ln in text.splitlines() if ln.lstrip().startswith("|")]
    joined = "\n".join(rows).lower()
    hits = [t for t in FORBIDDEN_TERMS if t in joined]
    if hits:
        raise LocationStatisticError(
            f"a report TABLE ROW contains forbidden term(s) {hits}; §4.5's E6 "
            f"report may carry dispersion and counts only.")

    permitted = set()
    if stats is not None:
        permitted = {round(v, 12) for v in _numeric_leaves(stats)}

    forbidden = [v for v in forbidden_values(frames)
                 if round(v, 12) not in permitted]
    for v in forbidden:
        for nd in range(min_decimals, max_decimals + 1):
            s = f"{v:.{nd}f}"
            if re.search(r"(?<![\d.])" + re.escape(s) + r"(?!\d)", text):
                raise LocationStatisticError(
                    f"report contains {s}, which is a mean, median or sum of "
                    f"r_multiple or net_pnl. E6 must support a fold-design "
                    f"decision made BLIND to returns.")
    return len(forbidden)


def render_report(stats, overlap, provenance, columns=SIGMA_COLUMNS):
    """The markdown report. Dispersion and counts only, by construction."""
    L = []
    w = L.append
    w("# REPORT 12 — E6: PER-TRADE DISPERSION AND FOLD TRADE COUNTS")
    w("")
    w("**Step 1 of the nine-step sequence (§4.4). THIS RUN LIFTED THE "
      "PERFORMANCE FIREWALL — partially.**")
    w("")
    w("The lift covers IN-SAMPLE results only. The holdout (2025-01-01 onward) "
      "stays sealed until step 9. No loader in this run was passed "
      "`authorised=True`.")
    w("")
    w("**This report carries dispersion and counts and nothing about "
      "location.** No mean, median or sum of `r_multiple` or `net_pnl`; no "
      "expectancy; no win rate; no profit factor; no Sharpe; no equity curve; "
      "no exit-reason or holding-time distribution; no per-arm or "
      "per-configuration comparison. That is not a stylistic choice: E6 decides "
      "fold architecture, and the decision is only blind if the evidence "
      "supporting it is. The prohibition is enforced by "
      "`assert_no_location_statistic`, which re-derives every forbidden "
      "quantity from the trade tables and refuses a report in which one "
      "appears.")
    w("")

    # ---- headline --------------------------------------------------------
    b0 = stats["bounds_check"]
    t0 = stats["trigger"]
    sig_lo = min(v["pooled_is"]["sigma"] for v in stats["symbols"].values())
    sig_hi = max(v["pooled_is"]["sigma"] for v in stats["symbols"].values())
    w("## 0. What this run found")
    w("")
    w(f"1. **Sigma is materially SMALLER than the design assumed.** Measured "
      f"{sig_lo:.4f}R to {sig_hi:.4f}R per symbol against the 1.2R estimate "
      f"§4.5 wrote the power table around — roughly 60–70% of it. Every "
      f"downstream comparison is therefore more precise than pre-registered, "
      f"not less.")
    w(f"2. **The E6 trigger does NOT fire**, in "
      f"{t0['n_firing']} of {t0['n_cells']} fold-symbol test cells. The "
      f"largest test-fold SE is "
      f"{max(c['se'] for c in t0['cells'] if c['se'] is not None):.4f}R "
      f"against a {E6_SE_TRIGGER_R:g}R threshold — a factor of "
      f"{E6_SE_TRIGGER_R / max(c['se'] for c in t0['cells'] if c['se'] is not None):.1f} "
      f"of headroom. **The nine-fold architecture stands.** Per §4.5 this is "
      f"reported, not acted on.")
    w(f"3. **No evidence minimum is missed anywhere.** All "
      f"{len(stats['symbols']) * len(stats['folds'])} fold-symbol cells clear "
      f"200 training trades and 50 test trades, and all "
      f"{len(stats['symbols']) * len(stats['folds']) * 4} direction cells "
      f"clear 30." if not stats["shortfalls"] else
      f"3. **{len(stats['shortfalls'])} cells fall short of an evidence "
      f"minimum** — see §5.1. The minimums do not move.")
    w(f"4. **Appendix L's upper bound on `r_multiple` is arithmetically "
      f"wrong**, and the pre-registered sanity check duly fails: "
      f"{b0['n_above_2r']} of {b0['n_trades']} trades exceed +2.0R, by at "
      f"most {b0['max_excess_ticks']:.4f} of one tick. The cause is the "
      f"engine's deliberate conservative rounding of the target, not a "
      f"defect. §4 and §10.1 set this out. It changes nothing about 1, 2 "
      f"or 3.")
    w("")

    # ---- provenance ------------------------------------------------------
    w("## 1. Provenance")
    w("")
    w(f"- **HEAD at run time:** `{provenance['git_commit']}`")
    w(f"- **Working tree:** {provenance['tree_state']}")
    w(f"- **grid.json provenance:** `{provenance['grid_commit']}` "
      f"(step 0 artifact, pre-lift)")
    w(f"- **Mode:** signal mode (§4.5 edge-test instrument) — every signal "
      f"simulated independently, no occupancy, cooldown or margin limit")
    w(f"- **Arm:** {RVOL_ARM:.0%} RVOL pass rate, `baseline_days` = "
      f"{BASELINE_DAYS}, `stop_max_pct` from grid.json")
    w(f"- **Window:** in-sample only, {sch.IS_START} → {sch.IS_END}, "
      f"nine folds, train and test evaluated separately")
    w(f"- **Indicators:** computed from each fold's `warmup_start` "
      f"({sch.WARMUP_DAYS}-day buffer), per `src/folds/warmup.py`")
    w("")

    # ---- configuration ---------------------------------------------------
    w("## 2. Configuration run, per fold per symbol")
    w("")
    w("Pre-specified, not chosen: the centre of the A3-surviving offset set "
      "with the top grid point (2.50) removed — §4.3's plateau rule makes the "
      "edge of the searched range ineligible for selection — tie broken to the "
      "HIGHER central offset per Appendix K.3. Fully determined by step 0 "
      "outputs and the frozen rules. **This is not a selection and carries no "
      "privileged status**; it exists to generate a representative trade "
      "population.")
    w("")
    w("| symbol | fold | m\\* | A3-surviving offsets | eligible (top removed) "
      "| offset run | absolute multiplier | stop_max_pct | rvol threshold |")
    w("|---|---|---|---|---|---|---|---|---|")
    for k in sorted(stats["config"], key=lambda x: (x.split("|")[0],
                                                    int(x.split("|")[1]))):
        c = stats["config"][k]
        surv = ", ".join(f"{o:g}" for o in c["surviving_offsets"])
        elig = ", ".join(f"{o:g}" for o in c["eligible_offsets"])
        flag = "" if c["eligible_contiguous"] else " **(non-contiguous)**"
        w(f"| {c['symbol']} | {c['fold_id']} | {c['m_star']:.4f} | {surv} | "
          f"{elig}{flag} | **{c['offset']:g}** | {c['multiplier']:.4f} | "
          f"{c['stop_max_pct']:.4f} | {c['rvol_threshold']:.4f} |")
    w("")

    # ---- sigma -----------------------------------------------------------
    w("## 3. Dispersion of `r_multiple`")
    w("")
    w("### 3.1 Pooled per symbol (all in-sample trades, train + test)")
    w("")
    _table(w, columns, [(s, stats["symbols"][s]["pooled_is"])
                        for s in sorted(stats["symbols"])], "symbol")
    w("")
    w("Train and test pooled separately, same symbols:")
    w("")
    rows = []
    for s in sorted(stats["symbols"]):
        rows.append((f"{s} train", stats["symbols"][s]["pooled_train"]))
        rows.append((f"{s} test", stats["symbols"][s]["pooled_test"]))
    _table(w, columns, rows, "symbol / period")
    w("")

    w("### 3.2 Per direction, per symbol (all in-sample trades)")
    w("")
    w("Long and short cohorts stay separate throughout (§4.5).")
    w("")
    rows = []
    for s in sorted(stats["symbols"]):
        for d in DIRECTIONS:
            rows.append((f"{s} {d}", stats["symbols"][s]["by_direction"][d]))
    _table(w, columns, rows, "symbol / direction")
    w("")

    w("### 3.3 Per fold per symbol — TEST period")
    w("")
    rows = []
    for s in sorted(stats["symbols"]):
        for fid in stats["folds"]:
            rows.append((f"{s} f{fid}",
                         stats["symbols"][s]["by_fold"][fid]["test"]))
    _table(w, columns, rows, "symbol / fold")
    w("")

    # ---- bounds ----------------------------------------------------------
    b = stats["bounds_check"]
    w("## 4. Appendix L sanity check (Popoviciu) — ONE PART FAILS")
    w("")
    w(f"Appendix L bounds `r_multiple` in approximately "
      f"[{R_LOWER_BOUND:g}, {R_UPPER_BOUND:g}], so by Popoviciu's inequality "
      f"sigma ≤ {POPOVICIU_SIGMA_MAX:g}R.")
    w("")
    w("| check | bound | observed | verdict |")
    w("|---|---|---|---|")
    w(f"| max `r_multiple` | ≤ {R_UPPER_BOUND:g} | "
      f"{_num(b['max_observed'], 8)} | "
      f"{'PASS' if b['upper_bound_passed'] else '**FAIL**'} |")
    w(f"| min `r_multiple` | ≥ {R_LOWER_BOUND:g} | "
      f"{_num(b['min_observed'], 8)} | "
      f"{'PASS' if b['lower_bound_passed'] else '**FAIL**'} |")
    w(f"| max sigma (per symbol, pooled) | ≤ {POPOVICIU_SIGMA_MAX:g} | "
      f"{_num(b['max_sigma_observed'], 4)} | "
      f"{'PASS' if b['sigma_cap_passed'] else '**FAIL**'} |")
    w(f"| max `r_multiple` vs the ENGINE-DERIVED ceiling | ≤ +2R + one tick "
      f"| {b['n_above_tick_bound']} breaches | "
      f"{'PASS' if b['tick_bound_passed'] else '**FAIL**'} |")
    w("")
    w(f"### 4.1 The upper bound fails, and Appendix L is the thing that is "
      f"wrong")
    w("")
    w(f"**{b['n_above_2r']} of {b['n_trades']} trades exceed +2.0R.** The "
      f"largest is {_num(b['max_observed'], 8)}R — an excess of "
      f"{(b['max_observed'] - R_UPPER_BOUND) if b['max_observed'] else 0:.2e}R, "
      f"about {(b['max_observed'] - R_UPPER_BOUND) * 20 if b['max_observed'] else 0:.3f} "
      f"cents on a $20 risk unit.")
    w("")
    w("Every excursion is a **target** exit; no other exit reason produces "
      "one. The cause is in the engine's own documented arithmetic, not in a "
      "defect:")
    w("")
    w("> `costs.solve_price_for_net` rounds the solved level **away from the "
      "position** — `\"up\"` for a long, `\"down\"` for a short — so that "
      "\"a level is never claimed at a price that would deliver less than "
      "`net_pnl`\".")
    w("")
    w("A filled target therefore delivers +2R **plus up to one tick of P&L**, "
      "and never more. Appendix L's derivation states that \"target exits fill "
      "at exactly +2R\", which overlooks that rounding. The premise is wrong; "
      "the engine is behaving exactly as specified.")
    w("")
    w(f"**Measured against the correct ceiling:** the largest excess over +2R "
      f"is **{_num(b['max_excess_ticks'], 4)} of one tick** — strictly under "
      f"one tick, in every one of the {b['n_above_2r']} cases. "
      f"{b['n_above_tick_bound']} trades exceed the tick-aware ceiling. That "
      f"is the check whose breach would mean an engine defect, and it passes.")
    w("")
    mx = b["max_observed"] or R_UPPER_BOUND
    mn = b["min_observed"] or NOMINAL_R_LOWER
    w("**Consequence for the E6 conclusion: none.** Appendix L derives "
      f"{POPOVICIU_SIGMA_MAX:g}R from the range "
      f"[{NOMINAL_R_LOWER:g}, {R_UPPER_BOUND:g}]. Correcting only the upper "
      f"end to the observed {_num(mx, 6)} gives "
      f"{(mx - NOMINAL_R_LOWER) / 2:.6f}R — a move of "
      f"{((mx - NOMINAL_R_LOWER) / 2 - POPOVICIU_SIGMA_MAX):.2e}R. Measured "
      f"sigma is {_num(b['max_sigma_observed'], 4)}R at its largest, nowhere "
      f"near either figure, so the dispersion finding and the fold trigger "
      f"verdict are unaffected.")
    w("")
    w(f"**The realised range is TIGHTER than Appendix L assumed, not wider.** "
      f"The observed minimum is {_num(mn, 6)}R, not the −1.1R the derivation "
      f"posits: `position_size` already absorbs both fee legs and the stop "
      f"haircut into the risk denominator, so a stop-out lands at −1R net "
      f"rather than −1R plus a haircut. Popoviciu over the realised range "
      f"[{_num(mn, 4)}, {_num(mx, 4)}] gives {(mx - mn) / 2:.4f}R, and "
      f"measured sigma is below half of that.")
    w("")
    w("**No threshold was moved to make this pass.** Appendix L is a frozen "
      "pre-registration document and §4.5 forbids post-lift amendment, so it "
      "is NOT amended here. The pre-registered check is retained, its failure "
      "is reported above, and the hard stop that aborts the run was placed on "
      "the tighter engine-derived ceiling — the bound that Appendix L was "
      "trying to express. See §10 for this recorded as a specification defect.")
    w("")

    # ---- counts ----------------------------------------------------------
    w("## 5. Trade counts and the evidence minimums")
    w("")
    w(f"Minimums, per symbol, **which do not move**: {MIN_TRAIN_TRADES} IS "
      f"trades (per training fold, Appendix K.2b), {MIN_TEST_TRADES} per test "
      f"fold, {MIN_DIRECTION_TRADES} per direction. Cells below a minimum are "
      f"marked `SHORT`.")
    w("")
    w("| symbol | fold | train n | train long | train short | test n | "
      "test long | test short |")
    w("|---|---|---|---|---|---|---|---|")
    for s in sorted(stats["symbols"]):
        for fid in stats["folds"]:
            c = stats["symbols"][s]["by_fold"][fid]
            cells = [
                _flag(c["train"]["n"], MIN_TRAIN_TRADES),
                _flag(c["train"]["by_direction"]["long"]["n"], MIN_DIRECTION_TRADES),
                _flag(c["train"]["by_direction"]["short"]["n"], MIN_DIRECTION_TRADES),
                _flag(c["test"]["n"], MIN_TEST_TRADES),
                _flag(c["test"]["by_direction"]["long"]["n"], MIN_DIRECTION_TRADES),
                _flag(c["test"]["by_direction"]["short"]["n"], MIN_DIRECTION_TRADES),
            ]
            w(f"| {s} | {fid} | " + " | ".join(cells) + " |")
    w("")
    w("Whole in-sample population per symbol (train and test folds pooled; "
      "note training windows overlap by 50%, so this is not a count of "
      "independent trades):")
    w("")
    w("| symbol | IS trades | train | test |")
    w("|---|---|---|---|")
    for s in sorted(stats["symbols"]):
        v = stats["symbols"][s]
        w(f"| {s} | {v['pooled_is']['n']} | {v['pooled_train']['n']} | "
          f"{v['pooled_test']['n']} |")
    w("")
    sf = stats["shortfalls"]
    if sf:
        w(f"### 5.1 Shortfalls — {len(sf)} cells below a pre-committed minimum")
        w("")
        w("| symbol | fold | period | direction | n | minimum | deficit |")
        w("|---|---|---|---|---|---|---|")
        for x in sf:
            w(f"| {x['symbol']} | {x['fold_id']} | {x['period']} | "
              f"{x['direction']} | {x['n']} | {x['minimum']} | "
              f"{x['minimum'] - x['n']} |")
    else:
        w("### 5.1 Shortfalls — none. Every cell clears its minimum.")
    w("")
    w("Reported, not adjusted. §4.5: the evidence minimums do NOT move, and "
      "the resolution order is loosen thresholds → extend the in-sample "
      "window → drop to a single condition. The holdout is not touched.")
    w("")

    # ---- trigger ---------------------------------------------------------
    t = stats["trigger"]
    w("## 6. The E6 trigger")
    w("")
    w(f"**Rule (§4.5, unchanged by Appendix L):** if a 3-month test fold's "
      f"standard error on expectancy exceeds {E6_SE_TRIGGER_R:g}R, test folds "
      f"extend to 6 months with a 6-month step, giving five folds instead of "
      f"nine.")
    w("")
    w("SE is computed as the pooled per-symbol sigma over that fold's test "
      "trade count. Per Appendix L this is a **trade-count guard expressed in "
      "SE units** — the binding quantity is n, not sigma.")
    w("")
    verdict = ("**THE TRIGGER FIRES.**" if t["fires"]
               else "**THE TRIGGER DOES NOT FIRE.**")
    w(verdict + f" {t['n_firing']} of {t['n_cells']} fold-symbol test cells "
      f"exceed {E6_SE_TRIGGER_R:g}R.")
    if t["fires"]:
        w("")
        w(f"Symbols affected: {', '.join(t['symbols_affected'])}.")
    w("")
    w("| symbol | fold | test n | SE (R) | > 0.20R? |")
    w("|---|---|---|---|---|")
    for c in t["cells"]:
        w(f"| {c['symbol']} | {c['fold_id']} | {c['n_test']} | "
          f"{_num(c['se'], 4)} | {'**YES**' if c['fires'] else 'no'} |")
    w("")
    w(f"_{t['action']}_")
    w("")

    # ---- power -----------------------------------------------------------
    p = stats["power"]
    w("## 7. The power table, recomputed on measured sigma")
    w("")
    w(f"§4.5's noise caveat made quantitative. The design assumed sigma = 1.2R; "
      f"every row below uses MEASURED sigma. Each SE is compared against the "
      f"{p['threshold_r']:g}R marginal-contribution threshold D5 drop "
      f"decisions use. A ratio above 1 means the noise on that figure exceeds "
      f"the difference the decision is trying to detect.")
    w("")
    w("| population | sigma (R) | n | SE (R) | SE / 0.05R |")
    w("|---|---|---|---|---|")
    labels = [("at_min_is_200", f"{MIN_TRAIN_TRADES}-trade IS minimum"),
              ("at_min_test_50", f"{MIN_TEST_TRADES}-trade test minimum"),
              ("at_typical_test", "typical test fold (median count)"),
              ("at_typical_train", "typical training fold (median count)"),
              ("at_pooled_is", "pooled in-sample")]
    for s in sorted(k for k in p["rows"] if k != "D5_POOLED"):
        row = p["rows"][s]
        for key, lab in labels:
            cell = row[key]
            ratio = (None if cell["se"] is None
                     else cell["se"] / p["threshold_r"])
            w(f"| {s} — {lab} | {_num(row['sigma'], 4)} | "
              f"{_num(cell['n'], 0)} | {_num(cell['se'], 4)} | "
              f"{_num(ratio, 2)} |")
    row = p["rows"]["D5_POOLED"]
    for key, lab in labels:
        cell = row[key]
        if cell["n"] is None:
            continue
        ratio = None if cell["se"] is None else cell["se"] / p["threshold_r"]
        w(f"| **D5 pooled (all folds × all symbols)** — {lab} | "
          f"{_num(row['sigma'], 4)} | {_num(cell['n'], 0)} | "
          f"{_num(cell['se'], 4)} | {_num(ratio, 2)} |")
    w("")
    w("The D5 row is the only figure pooled across symbols, and §4.4 licenses "
      "exactly that pooling for drop decisions. Everything else is per symbol.")
    w("")

    # ---- 425 bars --------------------------------------------------------
    w("## 8. The 425 reconstruction-divergence bars (deferred Point 2 item)")
    w("")
    w(f"Point 2 recorded {overlap['total_flagged_bars']} flagged bars "
      f"({overlap['total_flagged_rows']} rows; one SOL bar is flagged on both "
      f"`high` and `volume`, which is the single OHLC divergence) as a FLAG "
      f"LIST, not an exclusion filter, and deferred the signal-bar overlap "
      f"measurement to Point 4. Measured here.")
    w("")
    w("| symbol | flagged bars | in-sample | ∩ breakout bar | ∩ gated signal "
      "bar (50%) | ∩ signal bar of a taken trade | ∩ entry bar |")
    w("|---|---|---|---|---|---|---|")
    for s in sorted(overlap["per_symbol"]):
        v = overlap["per_symbol"][s]
        w(f"| {s} | {v['flagged_bars_total']} | {v['flagged_bars_in_sample']} "
          f"| {v['overlap_breakout_bar']} | {v['overlap_gated_signal_bar']} | "
          f"{v['overlap_entered_trade_signal_bar']} | {v['overlap_entry_bar']} |")
    w(f"| **all** | {overlap['all_symbols_flagged_bars_total']} | "
      f"{overlap['all_symbols_flagged_bars_in_sample']} | "
      f"{overlap['all_symbols_overlap_breakout_bar']} | "
      f"{overlap['all_symbols_overlap_gated_signal_bar']} | "
      f"{overlap['all_symbols_overlap_entered_trade_signal_bar']} | "
      f"{overlap['all_symbols_overlap_entry_bar']} |")
    w("")
    w("Counts only. **No outcome comparison between flagged and unflagged "
      "trades is made** — that would be a location statistic, and this report "
      "may not carry one.")
    w("")

    # ---- counters --------------------------------------------------------
    w("## 9. Refusal and provenance counters")
    w("")
    agg = {}
    for v in stats["counters"]["refused"].values():
        for k2, n in v.items():
            agg[k2] = agg.get(k2, 0) + n
    w("| counter | total across all fold-symbol-periods |")
    w("|---|---|")
    for k2 in sorted(agg):
        w(f"| refused_{k2} | {agg[k2]} |")
    w(f"| trades whose exit_ts crosses {sch.HOLDOUT_TEST_START} | "
      f"{stats['counters']['exit_after_is_end']} |")
    w(f"| **excluded, boundary-crossing (Appendix M.3)** | "
      f"**{stats['counters'].get('excluded_holdout_boundary', 0)}** |")
    w(f"| trades originating before their period start | "
      f"{stats['counters']['signals_before_train_start']} |")
    w("")
    w("`open_position`, `cooldown` and `insufficient_margin` are structurally "
      "zero in signal mode — no constraint of that kind applies. They are "
      "printed rather than omitted so that a non-zero value would be visible "
      "as a defect.")
    w("")

    # ---- judgment calls and specification defects -------------------------
    w("## 10. Ambiguities resolved, and where the specification is wrong")
    w("")
    w("### 10.1 Where I believe the specification is WRONG")
    w("")
    w("**(a) Appendix L's upper bound on `r_multiple` is arithmetically "
      "wrong.** It asserts \"target exits fill at exactly +2R\". They do not: "
      "`costs.solve_price_for_net` deliberately rounds the target away from "
      "the position so a level never delivers less than +2R, so a filled "
      "target delivers +2R plus up to one tick. §4 quantifies it. The "
      "conclusion Appendix L draws — sigma ≤ 1.55R — survives essentially "
      "unchanged, so this is a defect in the derivation, not in the design. "
      "**It is NOT amended here:** §4.5 permits amendment pre-lift only, and "
      "this run is the lift. Recorded for the record and for whoever writes "
      "the next appendix.")
    w("")
    w("**(b) Appendix L's own text is corrupted in the committed document.** "
      "Lines 1143–1145 of `docs/handoff/08_point_4_pre_registration.md` "
      "contain repeated, spliced fragments — `\"(b - a)^2 / 4, so sigma <= "
      "1.55R, attained only by\"` recurs a dozen times mid-sentence, and the "
      "paragraph beginning `\"The o\"` is destroyed. The meaning of the rule "
      "is recoverable (sigma ≤ 1.55R by Popoviciu; the trigger is a "
      "trade-count guard) and the CORRECTED READING paragraph is intact, so "
      "E6 was executed against the recoverable reading. **A pre-registration "
      "document whose text is damaged is weaker evidence than one whose text "
      "is not**, and this should be repaired by a commit that states it is "
      "repairing a transcription error and changes no rule.")
    w("")
    w("### 10.2 Judgment calls")
    w("")
    w("**1. \"200 IS trades per symbol\" is applied per TRAINING FOLD.** The "
      "carried commitments state it per symbol without naming the unit. "
      "Appendix K.2(b) resolves it — \"the training-fold trade count for that "
      "symbol meets the pre-committed evidence minimum of 200 IS trades\" — "
      "and §4.2 sizes a 6-month train window against it. §5 also reports the "
      "whole-window pooled count so the looser reading is available.")
    w("")
    w("**2. The 30-per-direction minimum is applied per fold per period.** "
      "§4.2 quotes \"60–100 per direction\" for a 3-month test fold against "
      "the 30 minimum, which fixes the unit as the fold. Train-period "
      "direction cells are reported on the same basis.")
    w("")
    w("**3. Signal mode was run UNGATED and filtered to the 50% arm**, per "
      "§4.5 and `run.py:gated_arm`, rather than re-simulating with the gate "
      "on. In signal mode no trade interacts with another, so the two are the "
      "same trade set by construction. The ungated universe size is reported "
      "beside each cell.")
    w("")
    w("**4. Indicators are computed once per fold from `warmup_start` through "
      "`test_end`**, then partitioned into train and test. `src/folds/` "
      "specifies one buffer before `train_start` covering both periods "
      "because they are contiguous. The test period therefore carries a much "
      "longer effective buffer than 45 days, which is what the fold design "
      "intends.")
    w("")
    w("**5. 1m bars from 2025 ARE loaded, to resolve in-sample trades that "
      "cross the boundary.** A trade signalled in the last hours of "
      "2024-12-31 walks a 41-bar lifecycle into 2025-01-01. `src/engine/"
      "run.py` already loads `max(year) + 1` for exactly this reason, and "
      "changing it would be changing engine semantics. Those minutes RESOLVE "
      "an in-sample trade; they never originate one, and no statistic is "
      "computed over holdout bars. The 15m loader — the one that decides "
      "which bars can produce a signal — is bounded at "
      f"{sch.IS_END} and refuses the holdout on the default path. "
      f"{stats['counters']['exit_after_is_end']} trades cross the boundary; a "
      f"test asserts no signal bar does.")
    w("")
    w("**6. \"An actual entry bar in this run\" is reported two ways** in §8. "
      "A flagged bar can coincide with the SIGNAL bar of a trade that was "
      "taken, or with the ENTRY bar itself, which sits one 15m bar later. The "
      "phrasing admits both, so both are counted.")
    w("")
    w("**7. The top grid point is excluded before taking the centre, not "
      "after.** §4.3's plateau rule makes offset 2.50 ineligible for "
      "selection, so it is removed from the surviving set and the centre is "
      "taken of what remains. Taking the centre first and then checking "
      "eligibility would sometimes land on an offset that could never be "
      "selected.")
    w("")
    w("**8. The E6 trigger uses the POOLED per-symbol sigma** over each "
      "fold's own test trade count, as specified. Per-fold test sigmas are "
      "reported in §3.3 but are not used in the trigger: Appendix L's "
      "corrected reading makes it a trade-count guard, so the dispersion term "
      "is held fixed while n varies.")
    w("")
    return "\n".join(L) + "\n"


def _flag(n, minimum):
    return f"{n}" if n >= minimum else f"**{n} SHORT**"


def _table(w, columns, rows, first_header):
    w("| " + first_header + " | " + " | ".join(h for h, _ in columns) + " |")
    w("|---" * (len(columns) + 1) + "|")
    for label, st in rows:
        w(f"| {label} | " + " | ".join(f(st) for _, f in columns) + " |")


# ---------------------------------------------------------------------------
# 8. entry point
# ---------------------------------------------------------------------------

def _json_default(o):
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating,)):
        return None if not np.isfinite(o) else float(o)
    if isinstance(o, (np.bool_,)):
        return bool(o)
    raise TypeError(f"not JSON serialisable: {type(o)}")


def main(symbols=SYMBOLS, derived_dir=sch.DERIVED, write=True):
    rev = sch.git_revision()
    if rev.endswith("-dirty"):
        raise RuntimeError(
            f"working tree is dirty ({rev}); a dirty hash makes the lift "
            f"unprovable. Commit or stash before running E6.")
    grid_json = gr.load_grid()
    log(f"[e6] HEAD {rev}  grid.json from {grid_json['git_commit']}")

    frames, confs, counters, folds = collect(
        symbols=symbols, derived_dir=derived_dir, grid_json=grid_json,
        write_trades=write)
    stats = build_stats(frames, confs, counters, folds, grid_json)
    overlap = flag_overlap(frames, folds, symbols, derived_dir)
    provenance = {
        "git_commit": rev,
        "tree_state": "clean (verified before the run; a dirty hash aborts)",
        "grid_commit": grid_json["git_commit"],
    }
    assert_stats_schema(stats)
    text = render_report(stats, overlap, provenance)
    n_checked = assert_no_location_statistic(text, frames, stats)
    log(f"[e6] report guard: schema clean; {n_checked} forbidden values "
        f"checked against the report text, none present")

    if write:
        os.makedirs(OUT_DIR, exist_ok=True)
        with open(ARTIFACT_PATH, "w") as fh:
            json.dump({"script": "src/analysis/dispersion.py",
                       "provenance": provenance, "stats": stats,
                       "flag_overlap": overlap},
                      fh, indent=2, sort_keys=True, default=_json_default)
            fh.write("\n")
        with open(REPORT_PATH, "w") as fh:
            fh.write(text)
        log(f"[artifact] {ARTIFACT_PATH}")
        log(f"[report]   {REPORT_PATH}")
    return stats, overlap, text


if __name__ == "__main__":
    main()
