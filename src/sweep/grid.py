"""The sweep grid: m*, the eleven multipliers, the derived cap, RVOL thresholds.

All four quantities are derived per TRAINING fold per symbol over BREAKOUT BARS
(Appendix F.1): bars passing Donchian-20 and the EMA20/EMA50 filter, BEFORE the
RVOL gate.

WHY THAT POPULATION. The argument for searching upward from m* is that the
floor binds on half the population at m* by construction. That holds only if the
median's population is the population A3 measures binding over. Gated signal
bars were rejected because they depend on `rvol_threshold`, which is itself
selected per fold -- anchoring the grid to them would make the grid depend on a
quantity the grid exists to help select. Breakout bars depend only on fixed
components, and a test asserts the population is invariant to `stop_atr_mult`,
`stop_max_pct` and `rvol_threshold`.

THE CAP IS P95, NOT THE MEDIAN (Appendix H / Amendment 6). The median form binds
on 49.9-50.0% of breakout bars at the top grid point -- a second stop rule, not
a guard rail. P95 binds on ~5%.

THE RANGE IS NOT EXTENDED. §4.3 and Appendix F.2: if the range is exhausted
without clearing A3, that is the finding, not a prompt to widen.
"""

import json
import os
import sys

import numpy as np
import pandas as pd

from src.folds import schedule as sch
from src.folds import warmup as wu

sys.path.insert(0, os.path.join(sch.ROOT, "src", "engine"))

import costs  # noqa: E402
import signals as sg  # noqa: E402

SYMBOLS = ("BTCUSDT", "ETHUSDT", "SOLUSDT")
GRID_DIR = os.path.join(sch.DERIVED, "sweep")
GRID_PATH = os.path.join(GRID_DIR, "grid.json")

# ---- the grid, §4.3. Eleven points, m* -> m*+2.5, step 0.25. --------------
GRID_OFFSET_MIN = 0.0
GRID_OFFSET_MAX = 2.5
GRID_STEP = 0.25
GRID_POINTS = 11

# ---- Appendix H: the cap anchors on the 95th percentile -------------------
CAP_PERCENTILE = 95.0
CAP_OFFSET = GRID_OFFSET_MAX          # the top grid point

# ---- §4.3: baseline_days FIXED at 20, not swept ---------------------------
BASELINE_DAYS = 20

# ---- §4.3: 50% pass rate, with pre-registered sensitivity at 30% and 70% --
RVOL_TARGET_PRIMARY = 0.50
RVOL_TARGETS = (0.30, 0.50, 0.70)

# ---- §4.4: A3 is floor binding < 20%, per symbol, never pooled ------------
A3_MAX_FLOOR_BINDING = 0.20
# §4.3 plateau rule needs a contiguous run of at least three surviving points.
MIN_PLATEAU_RUN = 3

log = sch.log
git_revision = sch.git_revision


# The four Point 3R parameters have no defaults. None of them enters any
# quantity derived here -- the breakout population is fixed-component only, and
# a test asserts the invariance. They are explicitly-arbitrary scaffolding.
def base_cfg(baseline_days=BASELINE_DAYS, **kw):
    p = dict(stop_atr_mult=1.0, stop_max_pct=0.035, rvol_threshold=1.5,
             baseline_days=baseline_days)
    p.update(kw)
    return costs.CostConfig(**p)


def stop_min_pct(symbol, cfg=None):
    """The DERIVED per-symbol cost floor, as a PERCENT of price.

    Read from the engine's config so there is one definition of the floor in
    the repo: 1.020% BTC/ETH, 1.320% SOL.
    """
    return (cfg or base_cfg()).stop_min_pct(symbol) * 100.0


# ---------------------------------------------------------------------------
# the breakout-bar population (Appendix F.1)
# ---------------------------------------------------------------------------

def breakout_frame(symbol, period_start, period_end, buffer_days=None,
                   baseline_days=BASELINE_DAYS, derived_dir=sch.DERIVED):
    """Indicators over [period_start, period_end], computed from the buffer.

    Indicators start at `period_start - buffer_days`, never at period_start:
    §4.2's warm-up is drawn from data PRECEDING the period.
    """
    buffer_days = sch.WARMUP_DAYS if buffer_days is None else buffer_days
    return wu.indicators_with_buffer(symbol, period_start, period_end,
                                     buffer_days, baseline_days, derived_dir)


def breakout_masks(ind):
    """Donchian-20 + EMA20/EMA50 only. NOT the RVOL gate, NOT RSI.

    Deliberately excludes every swept term: this population must not move when
    a swept parameter moves, or the grid would depend on what it helps select.
    """
    c = ind["close"].to_numpy(float)
    ef, es = ind["ema_fast"].to_numpy(float), ind["ema_slow"].to_numpy(float)
    up, dn = (ind["donchian_upper"].to_numpy(float),
              ind["donchian_lower"].to_numpy(float))
    ok = np.isfinite(up) & np.isfinite(dn) & np.isfinite(ef) & np.isfinite(es)
    return (ef > es) & (c > up) & ok, (ef < es) & (c < dn) & ok


def atr_pct(ind):
    """ATR(14) as a PERCENTAGE of close, matching stop_min_pct's units."""
    return ind["atr"].to_numpy(float) / ind["close"].to_numpy(float) * 100.0


def breakout_atr_pct(ind, direction=None):
    """ATR% over breakout bars. Both directions pooled unless one is named."""
    lo, sh = breakout_masks(ind)
    m = lo if direction == "long" else sh if direction == "short" else (lo | sh)
    a = atr_pct(ind)
    return a[m & np.isfinite(a)]


# ---------------------------------------------------------------------------
# m*, the grid, the derived cap
# ---------------------------------------------------------------------------

def m_star(symbol, atr_pct_breakout, cfg=None):
    """m* = stop_min_pct / median(ATR%) over training-fold breakout bars.

    By construction the floor binds on ~50% of that population at
    stop_atr_mult = m*: the floor equals m* x median, so it binds exactly when
    ATR% < median. That identity is the reason the search runs upward from m*,
    and it is asserted by test rather than assumed.
    """
    a = np.asarray(atr_pct_breakout, float)
    a = a[np.isfinite(a)]
    if len(a) < 2:
        raise ValueError(f"{symbol}: {len(a)} finite breakout ATR% values; "
                         f"cannot derive m*")
    med = float(np.median(a))
    if not med > 0:
        raise ValueError(f"{symbol}: median breakout ATR% is {med}; "
                         f"m* is undefined")
    return stop_min_pct(symbol, cfg) / med, med


def multiplier_grid(m):
    """Eleven points: m*, m*+0.25, ..., m*+2.50. The range is NOT extended."""
    g = [m + GRID_OFFSET_MIN + i * GRID_STEP for i in range(GRID_POINTS)]
    if len(g) != GRID_POINTS:
        raise ValueError(f"grid has {len(g)} points, expected {GRID_POINTS}")
    if not np.isclose(g[-1] - g[0], GRID_OFFSET_MAX):
        raise ValueError(f"grid spans {g[-1] - g[0]}, expected {GRID_OFFSET_MAX}")
    return g


def derived_cap(m, atr_pct_breakout):
    """stop_max_pct = (m* + 2.5) x P95(ATR%) over training-fold breakout bars.

    Appendix H. At the top grid point the cap binds when
    (m*+2.5) x ATR% > (m*+2.5) x P95, i.e. when ATR% > P95 -- 5% of bars by
    construction, and strictly less at every lower multiplier.

    The superseded median form binds on 50% at the same point, which is a
    second stop rule rather than a guard rail.
    """
    a = np.asarray(atr_pct_breakout, float)
    a = a[np.isfinite(a)]
    p95 = float(np.percentile(a, CAP_PERCENTILE))
    return (m + CAP_OFFSET) * p95, p95


# ---------------------------------------------------------------------------
# RVOL thresholds -- structural, never a performance criterion
# ---------------------------------------------------------------------------

def rvol_threshold_for_pass_rate(ind, target, direction=None):
    """The RVOL value admitting `target` of breakout bars in this fold.

    Session-normalised and quote-denominated (the engine's `rvol` column at
    baseline_days=20). Selected on PASS RATE alone: choosing the threshold that
    performed best in training and then running 4.4's attribution would ask the
    data the same question twice.
    """
    lo, sh = breakout_masks(ind)
    m = lo if direction == "long" else sh if direction == "short" else (lo | sh)
    r = ind["rvol"].to_numpy(float)
    v = r[m & np.isfinite(r)]
    if len(v) < 2:
        raise ValueError(f"{len(v)} finite RVOL values on breakout bars")
    thr = float(np.quantile(v, 1.0 - target))
    realised = float((v >= thr).mean())
    return thr, realised, int(len(v))


# ---------------------------------------------------------------------------
# per-fold-per-symbol assembly
# ---------------------------------------------------------------------------

def fold_symbol_grid(symbol, fold, derived_dir=sch.DERIVED,
                     baseline_days=BASELINE_DAYS, cfg=None):
    """Every derived quantity for one (fold, symbol), from TRAINING data only.

    Nothing here reads the test period. That is asserted by a test which
    recomputes with the test period truncated away and requires identity.
    """
    ind = breakout_frame(symbol, fold["train_start"], fold["train_end"],
                         baseline_days=baseline_days, derived_dir=derived_dir)
    a = breakout_atr_pct(ind)
    m, med = m_star(symbol, a, cfg)
    grid = multiplier_grid(m)
    cap, p95 = derived_cap(m, a)

    rvol = {}
    for t in RVOL_TARGETS:
        thr, realised, n = rvol_threshold_for_pass_rate(ind, t)
        rvol[t] = {"threshold": thr, "realised_pass_rate": realised,
                   "n_breakout": n}

    lo, sh = breakout_masks(ind)
    return {
        "symbol": symbol,
        "fold_id": fold["fold_id"],
        "train_start": sch.iso(fold["train_start"]),
        "train_end": sch.iso(fold["train_end"]),
        "stop_min_pct": stop_min_pct(symbol, cfg),
        "median_atr_pct": med,
        "p95_atr_pct": p95,
        "m_star": m,
        "multipliers": grid,
        "stop_max_pct": cap,
        "rvol_thresholds": rvol,
        "n_breakout_bars": int(len(a)),
        "n_breakout_long": int(lo.sum()),
        "n_breakout_short": int(sh.sum()),
    }


def build_grid(symbols=SYMBOLS, folds=None, derived_dir=sch.DERIVED):
    folds = folds if folds is not None else sch.build_schedule()
    return {s: {f["fold_id"]: fold_symbol_grid(s, f, derived_dir)
                for f in folds} for s in symbols}


def grid_payload(grid=None, prescreen=None):
    grid = grid if grid is not None else build_grid()
    payload = {
        "script": "src/sweep/grid.py",
        "git_commit": git_revision(),
        "design": {
            "population": (
                "breakout bars in the training fold: Donchian-20 + EMA20/EMA50, "
                "BEFORE the RVOL gate (Appendix F.1)"),
            "m_star": "stop_min_pct / median(ATR%) over that population",
            "grid": (f"{GRID_POINTS} points, m* to m*+{GRID_OFFSET_MAX} "
                     f"step {GRID_STEP}; the range is NOT extended (§4.3)"),
            "stop_max_pct": (f"(m* + {CAP_OFFSET}) x P{CAP_PERCENTILE:g}(ATR%) "
                             f"over the same population (Appendix H / "
                             f"Amendment 6, superseding the median form)"),
            "rvol_thresholds": (
                f"pass rates {RVOL_TARGETS} on breakout bars; "
                f"baseline_days fixed at {BASELINE_DAYS} (§4.3)"),
            "a3": (f"floor binding < {A3_MAX_FLOOR_BINDING:.0%} on the gated "
                   f"population at the {RVOL_TARGET_PRIMARY:.0%} arm, "
                   f"PER SYMBOL, never pooled (§4.4)"),
            "firewall": (
                "entry-time quantities only: binding rates, pass rates, signal "
                "counts, ATR percentiles. Layer B is never run."),
        },
        "symbols": {},
    }
    for s, byfold in grid.items():
        payload["symbols"][s] = {str(k): v for k, v in sorted(byfold.items())}
    if prescreen is not None:
        payload["prescreen"] = prescreen
    return payload


def write_grid(path=GRID_PATH, payload=None):
    payload = payload or grid_payload()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as fh:
        json.dump(payload, fh, indent=2, sort_keys=True, default=_json_default)
        fh.write("\n")
    return path


def _json_default(o):
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating,)):
        return None if not np.isfinite(o) else float(o)
    if isinstance(o, (np.bool_,)):
        return bool(o)
    raise TypeError(f"not JSON serialisable: {type(o)}")


def load_grid(path=GRID_PATH):
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"grid missing at {path}; generate it with "
            f"`python -m src.sweep.prescreen`")
    return json.load(open(path))
