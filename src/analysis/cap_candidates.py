"""CANDIDATE STOP-CAP RULES, MEASURED AGAINST THE COMMITTED REQUIREMENT.

`docs/design/04_1f_cap_requirement.md` commits four limbs and what would show each
failed. **This module measures; it selects nothing and recommends nothing.**

THE CANDIDATES:

  * `src/sweep/grid.py`'s `derived_cap` -- the committed rule, per symbol and per
    training fold. **IMPORTED AND CALLED, NEVER REIMPLEMENTED.**
  * NO CAP AT ALL -- the candidate the audit's findings most directly support,
    measured rather than waved past.

WHAT IS MEASURED PER CANDIDATE: the cap value where applicable; the clipped
fraction over the candidate population per symbol, pooled and per fold period;
whether the venue minimum lot or minimum notional binds anywhere; and, for a
fold-dependent rule, how many candidates are clipped under some folds and not
others.

THE ADMITTED DOMAIN IS RECOMPUTED under each candidate as
`docs/handoff/36_point_4_1c_risk_unit_derivation.md` derived it, and the committed
level's position inside it is checked. **THAT IS A CHECK ON POSITION AND NOT A
RE-ARGUMENT OF THE LEVEL**, whose ground is the displacement budget at
`docs/design/04_1c_proper.md` §2 and is untouched by any cap.

NO OUTCOME QUANTITY. NO EXIT RESOLVED. THE EXECUTION LOOP IS NOT INVOKED.
Nothing sealed is opened and the barrier is asserted immediately before each read.
"""

import os
import sys
from dataclasses import replace

import numpy as np
import pandas as pd

from src.analysis import floor_curve as fc
from src.analysis import risk_unit_floor_curve as ruf
from src.analysis import stop_cap_audit as sca
from src.folds import schedule as sch
from src.sweep import grid as gr
from src.timeframe import resample as rs
from src.timeframe import sealed_1m as sealed

sys.path.insert(0, os.path.join(rs.ROOT, "src", "engine"))

import sizing  # noqa: E402

LONG, SHORT = ruf.LONG, ruf.SHORT
DIRECTIONS = ruf.DIRECTIONS

#: The committed level, from `docs/design/04_1c_proper.md` §2 and §3 as reported
#: at `docs/handoff/37_point_4_1c_level_and_consequences.md` §2. QUOTED, not
#: re-derived: this module checks whether it lies inside a domain, nothing more.
COMMITTED_LEVEL = 0.10


# ---------------------------------------------------------------------------
# CANDIDATE A. `grid.derived_cap`, per symbol and per training fold.
# ---------------------------------------------------------------------------

def derived_caps(symbols=None, derived_dir=None):
    """`grid.derived_cap` per symbol and fold, as a FRACTION.

    THE RULE IS `src/sweep/grid.py`'s AND IS CALLED, NOT REIMPLEMENTED. Its
    inputs -- `m_star` and the breakout ATR percentiles -- come from that module
    too. `grid.atr_pct` is in PERCENT, so the result is divided by one hundred.

    THE BARRIER IS ASSERTED IMMEDIATELY BEFORE EACH READ.
    """
    symbols = tuple(rs.SYMBOLS) if symbols is None else tuple(symbols)
    derived_dir = rs.DERIVED if derived_dir is None else derived_dir
    out = {}
    for symbol in symbols:
        for fold in sch.build_schedule():
            fc.assert_paths_unsealed(
                sealed.allowed_paths(symbol, derived_dir=derived_dir),
                "cap_candidates.derived_caps(%s fold %d)"
                % (symbol, fold["fold_id"]))
            ind = gr.breakout_frame(symbol, fold["train_start"],
                                    fold["train_end"])
            atr_pct = gr.breakout_atr_pct(ind)
            m, _median = gr.m_star(symbol, atr_pct)
            cap_pct, _p95 = gr.derived_cap(m, atr_pct)
            out[(symbol, int(fold["fold_id"]))] = cap_pct / 100.0
    return out


def fold_dependence(population, caps, symbols=None):
    """Candidates clipped under SOME of a symbol's fold caps and not others.

    THE QUANTITY LIMB 4 RANGES OVER. A rule computed per fold makes the clipped
    population a function of which fold is asked, and this counts the candidates
    for which the answer actually differs.
    """
    symbols = tuple(rs.SYMBOLS) if symbols is None else tuple(symbols)
    rows = []
    for symbol in symbols:
        sel = population["symbol"].to_numpy() == symbol
        sub = population[sel]
        values = sorted(v for (s, _f), v in caps.items() if s == symbol)
        clipped = np.array([sca.clipped_at(sub, v) for v in values])
        always = clipped.all(axis=0)
        ever = clipped.any(axis=0)
        rows.append({
            "symbol": symbol, "n": int(len(sub)),
            "n_fold_caps": len(values),
            "cap_min": float(min(values)), "cap_max": float(max(values)),
            "clipped_under_all": int(always.sum()),
            "clipped_under_some": int((ever & ~always).sum()),
            "clipped_under_none": int((~ever).sum()),
        })
    frame = pd.DataFrame(rows)
    frame.loc[len(frame)] = {
        "symbol": "POOLED", "n": int(frame["n"].sum()),
        "n_fold_caps": int(frame["n_fold_caps"].max()),
        "cap_min": float(frame["cap_min"].min()),
        "cap_max": float(frame["cap_max"].max()),
        "clipped_under_all": int(frame["clipped_under_all"].sum()),
        "clipped_under_some": int(frame["clipped_under_some"].sum()),
        "clipped_under_none": int(frame["clipped_under_none"].sum()),
    }
    return frame


def clipped_under_own_fold(population, caps, phase="test"):
    """Each candidate judged by the cap of the fold period it falls in.

    THE OPERATIVE READING OF A PER-FOLD RULE: the sweep derives the cap on a
    training fold and applies it to that fold's period. A candidate outside every
    such period has no cap under this rule and is reported separately rather than
    assigned one.
    """
    stamps = population["entry_close_ms"].to_numpy(np.int64)
    symbols = population["symbol"].to_numpy()
    entry = population["entry_price"].to_numpy(float)
    atr = population["atr"].to_numpy(float)

    verdict = np.full(len(population), None, dtype=object)
    for fold in sch.build_schedule():
        lo = _ms(fold["%s_start" % phase])
        hi = _ms(fold["%s_end" % phase], end_of_day=True)
        window = (stamps >= lo) & (stamps <= hi)
        for symbol in rs.SYMBOLS:
            cap = caps[(symbol, int(fold["fold_id"]))]
            mask = window & (symbols == symbol)
            if not mask.any():
                continue
            over = (sizing.STOP_ATR_MULT * atr) > (cap * entry)
            verdict[mask & over] = True
            verdict[mask & ~over] = False
    return verdict


def _ms(day, end_of_day=False):
    import datetime as dt
    stamp = dt.datetime(day.year, day.month, day.day, tzinfo=dt.timezone.utc)
    base = int(stamp.timestamp() * 1000)
    return base + sch.LAST_BAR_OFFSET_MS if end_of_day else base


# ---------------------------------------------------------------------------
# CANDIDATE B. NO CAP AT ALL.
# ---------------------------------------------------------------------------

def widest_atr_width(population, symbols=None):
    """The widest ATR-implied stop width in the population, per symbol.

    UNDER REMOVAL THIS IS THE WIDEST STOP THE RULE CAN PRODUCE, so it is where
    limb 3 is tested. `sizing.STOP_ATR_MULT` is read, not retyped.
    """
    symbols = tuple(rs.SYMBOLS) if symbols is None else tuple(symbols)
    entry = population["entry_price"].to_numpy(float)
    atr = population["atr"].to_numpy(float)
    width = sizing.STOP_ATR_MULT * atr / entry
    rows = []
    for symbol in symbols:
        sel = population["symbol"].to_numpy() == symbol
        i = int(np.argmax(np.where(sel, width, -np.inf)))
        rows.append({"symbol": symbol, "n": int(sel.sum()),
                     "widest_width": float(width[i]),
                     "widest_width_pct": 100.0 * float(width[i]),
                     "at_entry_price": float(entry[i]),
                     "at_atr": float(atr[i])})
    return pd.DataFrame(rows)


def viability_under_no_cap(population, cfg, specs, risk_usd=None):
    """Does the venue minimum bind anywhere, with the stop uncapped?

    LIMB 3, MEASURED RATHER THAN ASSUMED. Every candidate is sized at its own
    ATR-implied width -- floored at the derived cost floor, as `stop_geometry`
    does -- and put through `sizing.viability`, which is CALLED and not
    reimplemented.

    Returns the per-candidate frame; the caller counts.
    """
    risk_usd = sca.RISK_USD if risk_usd is None else float(risk_usd)
    entry = population["entry_price"].to_numpy(float)
    atr = population["atr"].to_numpy(float)
    symbols = population["symbol"].to_numpy()
    directions = population["direction"].to_numpy()

    n = len(population)
    width = np.empty(n)
    qty = np.empty(n)
    notional = np.empty(n)
    viable = np.empty(n, dtype=bool)
    reason = np.empty(n, dtype=object)

    for i in range(n):
        symbol = symbols[i]
        floor = float(cfg.stop_min_pct(symbol))
        w = max(sizing.STOP_ATR_MULT * atr[i] / entry[i], floor)
        width[i] = w
        q = sca.quantity_at_width(w, cfg, symbol, directions[i], entry[i],
                                  risk_usd)
        floored = sizing.floor_to_step(q, specs[symbol].qty_step)
        qty[i] = floored
        notional[i] = floored * entry[i]
        ok, why = sizing.viability(floored, entry[i], specs[symbol])
        viable[i] = ok
        reason[i] = why

    out = population.copy()
    out["uncapped_width"] = width
    out["uncapped_width_pct"] = 100.0 * width
    out["qty"] = qty
    out["notional"] = notional
    out["viable"] = viable
    out["reason"] = reason
    return out


# ---------------------------------------------------------------------------
# THE ADMITTED DOMAIN UNDER A CANDIDATE.
# ---------------------------------------------------------------------------

def domain_under_cap(cfg, cap_fraction, symbols=None):
    """The admitted domain with `stop_max_pct` set to `cap_fraction`.

    RECOMPUTED AS REPORT 36 DERIVED IT, through `ruf.common_achievable_range`,
    which is imported rather than restated.

    A CHECK ON THE LEVEL'S POSITION, NOT A RE-ARGUMENT OF THE LEVEL.
    """
    altered = replace(cfg, stop_max_pct=float(cap_fraction))
    lo, hi = ruf.common_achievable_range(altered, symbols)
    return {"cap_fraction": float(cap_fraction), "domain_lo": lo,
            "domain_hi": hi,
            "level_inside": bool(lo < COMMITTED_LEVEL < hi)}


def domain_under_no_cap(cfg, population, symbols=None):
    """The domain when the widest stop the rule produces is the binding width.

    UNDER REMOVAL THERE IS NO CAP, so the domain's lower bound is set by the
    widest width the ATR rule actually reaches. That width is a property of the
    population and is measured, not assumed.
    """
    widest = float(widest_atr_width(population, symbols)["widest_width"].max())
    return dict(domain_under_cap(cfg, widest, symbols), basis="widest ATR width")


def domain_under_per_symbol_caps(cfg, caps_by_symbol, symbols=None):
    """The admitted domain when each symbol carries its OWN cap.

    THE DOMAIN IS THE INTERSECTION ACROSS CELLS, so with per-symbol caps the
    lower bound is the LARGEST of each cell's ratio at its own cap -- not the
    result of applying any one symbol's cap to all of them. Getting that wrong
    would understate the bound.
    """
    symbols = tuple(rs.SYMBOLS) if symbols is None else tuple(symbols)
    lows, highs = [], []
    for symbol in symbols:
        altered = replace(cfg, stop_max_pct=float(caps_by_symbol[symbol]))
        for direction in DIRECTIONS:
            lows.append(ruf.ratio_at_cap(altered, symbol, direction))
        highs.append(ruf.limit_ratio_as_width_to_zero(altered, symbol))
    lo, hi = max(lows), min(highs)
    return {"domain_lo": float(lo), "domain_hi": float(hi),
            "level_inside": bool(lo < COMMITTED_LEVEL < hi)}
