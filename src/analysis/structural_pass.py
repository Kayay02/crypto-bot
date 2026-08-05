"""Structural measurement pass -- the Point 1R pre-checks (M1-M9).

Measures whether several 1R amendments are worth building, against the numeric
kill thresholds fixed in Section 13 of docs/handoff/05_point_1r.md BEFORE this
was run. Nothing here decides anything: it reports measurements and the verdict
each pre-committed threshold implies.

FIREWALL. No trade is simulated. No P&L, expectancy, win rate, profit factor,
Sharpe, return or equity figure is computed, and `net_pnl` / `r_multiple` are
never touched -- the engine's simulate module is not imported at all.

WINDOW. Hard-restricted to 2022-01-01 -> 2023-12-31 by the 1R.2 contamination
ledger (B0). Bars outside that range are dropped at load, before any indicator
is computed, so no downstream statistic can see the holdout. The derived layer
starts exactly at 2022-01-01, so NO pre-window warm-up data exists: warm-up is
consumed inside 2022 and the affected measurements say so.

Indicator definitions are imported from src/engine/signals.py. The breakout-bar
definition below is the engine's own trend and Donchian conditions with the
RVOL, RSI and vwap terms removed -- those are the things being measured against
it, so including them would condition the population on the measurement.
"""

import hashlib
import json
import os
import sys

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "src", "engine"))

import contracts  # noqa: E402
import costs  # noqa: E402
import signals  # noqa: E402

DERIVED = os.path.join(ROOT, "data", "derived")
SYMBOLS = ("BTCUSDT", "ETHUSDT", "SOLUSDT")
YEARS = (2022, 2023)

# Window bounds, epoch ms, inclusive start / exclusive end.
WINDOW_START_MS = 1_640_995_200_000  # 2022-01-01T00:00:00Z
WINDOW_END_MS = 1_704_067_200_000    # 2024-01-01T00:00:00Z

BAR_MS = 900_000
DAY_MS = 86_400_000
SLOTS_PER_DAY = DAY_MS // BAR_MS  # 96

LONG, SHORT = signals.LONG, signals.SHORT


# ---------------------------------------------------------------------------
# manifest integrity -- runs before any data is read
# ---------------------------------------------------------------------------

def check_manifest(derived_dir=DERIVED, root=ROOT):
    """Refuse to measure against data that no longer matches _manifest.json.

    Same contract as tests/test_manifest_integrity.py: recorded row counts must
    still hold, and raw sources must still hash to what was recorded.
    """
    import pyarrow.parquet as pq

    manifest = json.load(open(os.path.join(derived_dir, "_manifest.json")))
    row_drift, seen, hash_drift = [], set(), []
    for rel, meta in manifest["outputs"].items():
        p = os.path.join(root, rel)
        if not os.path.exists(p):
            row_drift.append((rel, "missing"))
            continue
        rows = pq.read_metadata(p).num_rows
        if rows != meta["rows"]:
            row_drift.append((rel, f"{rows} != {meta['rows']}"))
        for s in meta["sources"]:
            if s["path"] in seen:
                continue
            seen.add(s["path"])
            h = hashlib.sha256()
            with open(os.path.join(root, s["path"]), "rb") as fh:
                for c in iter(lambda: fh.read(1 << 20), b""):
                    h.update(c)
            if h.hexdigest() != s["sha256"]:
                hash_drift.append(s["path"])
    ok = not row_drift and not hash_drift
    return {"ok": ok, "git_commit": manifest.get("git_commit"),
            "outputs": len(manifest["outputs"]), "raw_sources": len(seen),
            "row_drift": row_drift, "hash_drift": hash_drift}


# ---------------------------------------------------------------------------
# loading -- window truncation happens HERE, before anything is computed
# ---------------------------------------------------------------------------

def load_window(symbol, derived_dir=DERIVED):
    """15m bars for `symbol`, truncated to 2022-2023 at the boundary.

    open_synth is dropped for the same reason the engine's loader drops it.
    Truncation precedes indicator computation so no rolling window, and no
    session baseline, can reach a bar outside the permitted window.
    """
    import pyarrow.parquet as pq

    df = pq.read_table(
        os.path.join(derived_dir, "ohlcv_15m", f"{symbol}.parquet")).to_pandas()
    df = df.drop(columns=["open_synth"])
    df = df[(df["ts"] >= WINDOW_START_MS) & (df["ts"] < WINDOW_END_MS)]
    return df.sort_values("ts", kind="mergesort").reset_index(drop=True)


def _year_of(ts):
    return pd.to_datetime(ts, unit="ms", utc=True).dt.year.to_numpy()


# ---------------------------------------------------------------------------
# bar-level derived quantities
# ---------------------------------------------------------------------------

def bar_frame(df, params=None):
    """Attach engine indicators plus the position/vwap terms under measurement.

    Degenerate bars (high == low) are an explicit branch: `degenerate` is True,
    both position terms are NaN, and every position-based gate FAILS on them.
    They are never allowed to become a division by zero or a silent NaN.
    """
    params = params or signals.SignalParams()
    out = signals.compute_indicators(df, params)

    high = out["high"].to_numpy(float)
    low = out["low"].to_numpy(float)
    close = out["close"].to_numpy(float)
    vol = out["volume"].to_numpy(float)
    qvol = out["quote_volume"].to_numpy(float)

    rng = high - low
    degenerate = ~(rng > 0.0)
    out["degenerate"] = degenerate

    safe_rng = np.where(degenerate, np.nan, rng)
    out["close_position"] = (close - low) / safe_rng

    # bar_vwap needs a non-zero traded volume; zero-volume bars have no vwap.
    no_vol = ~(vol > 0.0)
    out["zero_volume"] = no_vol
    out["bar_vwap"] = np.where(no_vol, np.nan, qvol / np.where(no_vol, np.nan, vol))

    raw_vp = (out["bar_vwap"].to_numpy(float) - low) / safe_rng
    out["vwap_position_raw"] = raw_vp
    out["vwap_position"] = np.clip(raw_vp, 0.0, 1.0)

    out["atr_pct"] = out["atr"].to_numpy(float) / close
    out["year"] = _year_of(out["ts"])
    out["slot"] = (out["ts"].to_numpy() // BAR_MS) % SLOTS_PER_DAY
    out["day"] = out["ts"].to_numpy() // DAY_MS
    out["hour"] = (out["ts"].to_numpy() % DAY_MS) // 3_600_000
    return out


def breakout_masks(bf):
    """The engine's trend + Donchian conditions ONLY.

    RVOL, RSI and vwap_position are deliberately excluded -- they are the terms
    being measured against this population.
    """
    ema_f = bf["ema_fast"].to_numpy(float)
    ema_s = bf["ema_slow"].to_numpy(float)
    close = bf["close"].to_numpy(float)
    up = bf["donchian_upper"].to_numpy(float)
    dn = bf["donchian_lower"].to_numpy(float)
    ok = np.isfinite(up) & np.isfinite(dn)
    return ((ema_f > ema_s) & (close > up) & ok,
            (ema_f < ema_s) & (close < dn) & ok)


# ---------------------------------------------------------------------------
# session-normalised RVOL (B1 proposal) -- causal by construction
# ---------------------------------------------------------------------------

def session_baseline(ts, values, baseline_days):
    """Median of the same 15m UTC slot over the trailing COMPLETED prior days.

    Causality is structural, not conventional: the day/slot matrix is rolled
    over the day axis and then shifted by one whole day, so the value returned
    for any bar of day D is a function of days [D-baseline_days, D-1] only. Bar
    T's own day contributes nothing -- not even earlier slots of it.

    min_periods == baseline_days, so a slot with a gap in its history yields
    NaN rather than a baseline computed from fewer days than requested.
    """
    if baseline_days < 1:
        raise ValueError("baseline_days must be >= 1")
    ts = np.asarray(ts, dtype=np.int64)
    values = np.asarray(values, dtype=float)
    day = ts // DAY_MS
    slot = (ts // BAR_MS) % SLOTS_PER_DAY

    tbl = pd.DataFrame({"day": day, "slot": slot, "v": values})
    # Duplicate (day, slot) cannot occur on a deduped 15m series; assert it.
    if tbl.duplicated(["day", "slot"]).any():
        raise ValueError("duplicate (day, slot) -- series is not a clean 15m grid")
    mat = tbl.pivot(index="day", columns="slot", values="v").sort_index()
    # Reindex onto a contiguous day axis so a missing calendar day consumes a
    # slot of the trailing window rather than being skipped over.
    mat = mat.reindex(range(int(mat.index.min()), int(mat.index.max()) + 1))
    base = mat.rolling(baseline_days, min_periods=baseline_days).median().shift(1)

    lookup = base.stack(future_stack=True)
    idx = pd.MultiIndex.from_arrays([day, slot])
    return lookup.reindex(idx).to_numpy(float)


def session_rvol(ts, volume, baseline_days):
    base = session_baseline(ts, volume, baseline_days)
    base = np.where(base > 0.0, base, np.nan)
    return np.asarray(volume, dtype=float) / base


# ---------------------------------------------------------------------------
# small statistics helpers
# ---------------------------------------------------------------------------

def deciles(x):
    x = np.asarray(x, dtype=float)
    x = x[np.isfinite(x)]
    if not len(x):
        return {}
    qs = np.arange(0.1, 1.0, 0.1)
    return {f"d{int(round(q * 10))}": float(np.quantile(x, q)) for q in qs}


def describe(x):
    x = np.asarray(x, dtype=float)
    x = x[np.isfinite(x)]
    if not len(x):
        return {"n": 0}
    q1, q3 = float(np.quantile(x, 0.25)), float(np.quantile(x, 0.75))
    d = {"n": int(len(x)), "mean": float(x.mean()), "median": float(np.median(x)),
         "q1": q1, "q3": q3, "iqr": q3 - q1,
         "frac_le_005": float((x <= 0.05).mean()),
         "frac_ge_095": float((x >= 0.95).mean()),
         "n_distinct": int(len(np.unique(np.round(x, 6))))}
    d.update(deciles(x))
    return d


def pearson(a, b):
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    m = np.isfinite(a) & np.isfinite(b)
    if m.sum() < 3:
        return float("nan"), int(m.sum())
    if np.std(a[m]) == 0 or np.std(b[m]) == 0:
        return float("nan"), int(m.sum())
    return float(np.corrcoef(a[m], b[m])[0, 1]), int(m.sum())


# ---------------------------------------------------------------------------
# M1 -- B3 validity
# ---------------------------------------------------------------------------

def m1_validity(bf, symbol, schedules):
    """bar_vwap must land inside [low - 1 tick, high + 1 tick].

    The tick in force is looked up per bar timestamp, so SOL's 2024 grid change
    is handled by the same step function the engine uses (it falls outside this
    window anyway, but the lookup is not special-cased).
    """
    ts = bf["ts"].to_numpy()
    tick = np.array([schedules[symbol].tick_at(int(t)) for t in ts])
    vwap = bf["bar_vwap"].to_numpy(float)
    lo = bf["low"].to_numpy(float) - tick
    hi = bf["high"].to_numpy(float) + tick

    out = {}
    for year in YEARS:
        m = (bf["year"].to_numpy() == year) & np.isfinite(vwap)
        n = int(m.sum())
        if not n:
            out[year] = {"n": 0}
            continue
        below = np.maximum(lo[m] - vwap[m], 0.0)
        above = np.maximum(vwap[m] - hi[m], 0.0)
        dist = np.maximum(below, above)
        bad = dist > 0.0
        worst_idx = np.argsort(-dist)[:5]
        px = bf["close"].to_numpy(float)[m]
        out[year] = {
            "n": n,
            "n_no_vwap": int(((bf["year"].to_numpy() == year)
                              & ~np.isfinite(vwap)).sum()),
            "n_violations": int(bad.sum()),
            "frac_inside": float(1.0 - bad.mean()),
            "worst": [{"abs_dist": float(dist[i]),
                       "dist_ticks": float(dist[i] / tick[m][i]),
                       "dist_pct_of_close": float(dist[i] / px[i] * 100.0)}
                      for i in worst_idx if dist[i] > 0.0],
        }
    return out


# ---------------------------------------------------------------------------
# M2/M3 -- B3 non-redundancy and dispersion
# ---------------------------------------------------------------------------

def m2_m3(bf):
    brk_l, brk_s = breakout_masks(bf)
    brk = brk_l | brk_s
    vp = bf["vwap_position"].to_numpy(float)
    cp = bf["close_position"].to_numpy(float)
    year = bf["year"].to_numpy()

    out = {}
    for y in YEARS:
        ym = year == y
        rho_b, n_b = pearson(vp[ym & brk], cp[ym & brk])
        rho_a, n_a = pearson(vp[ym], cp[ym])
        dist = describe(vp[ym & brk])
        # Fraction rejected by a threshold sweep, for the 25-75% condition.
        sweep = {}
        for t in (0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9):
            v = vp[ym & brk]
            v = v[np.isfinite(v)]
            sweep[t] = float((v < t).mean()) if len(v) else float("nan")
        exists_25_75 = any(0.25 <= r <= 0.75 for r in sweep.values()
                           if np.isfinite(r))
        # Directional view. The gate is applied directionally -- longs test
        # vwap_position, shorts test (1 - vwap_position) -- so the population a
        # threshold actually sees is one direction at a time. Section 13's
        # dispersion check says only "on breakout bars" and does not say which
        # of these it means; the two disagree, so BOTH are reported and the
        # ambiguity is flagged rather than resolved here.
        directional = {}
        for dname, dmask, gated in ((LONG, brk_l, vp), (SHORT, brk_s, 1.0 - vp)):
            dm = ym & dmask
            rho_d, n_d = pearson(vp[dm], cp[dm])
            directional[dname] = {"dist_gated_term": describe(gated[dm]),
                                  "rho": rho_d, "n": n_d}
        out[y] = {"rho_breakout": rho_b, "n_breakout": n_b,
                  "rho_all": rho_a, "n_all": n_a,
                  "dist": dist, "reject_sweep": sweep,
                  "exists_threshold_25_75": exists_25_75,
                  "directional": directional,
                  "n_breakout_degenerate": int((ym & brk
                                                & bf["degenerate"].to_numpy()).sum())}
    return out


# ---------------------------------------------------------------------------
# M4 -- B5 selectivity of flat RVOL
# ---------------------------------------------------------------------------

def _selectivity(pass_mask, brk_mask, valid, year, y):
    ym = (year == y) & valid
    a = ym.sum()
    b = (ym & brk_mask).sum()
    if not a or not b:
        return {"n_all": int(a), "n_breakout": int(b)}
    pa = float(pass_mask[ym].mean())
    pb = float(pass_mask[ym & brk_mask].mean())
    return {"n_all": int(a), "n_breakout": int(b),
            "pass_all": pa, "pass_breakout": pb,
            "ratio": (pb / pa) if pa > 0 else float("nan")}


def m4_flat_selectivity(bf, rvol_min=1.5):
    brk_l, brk_s = breakout_masks(bf)
    brk = brk_l | brk_s
    rvol = bf["rvol"].to_numpy(float)
    valid = np.isfinite(rvol)
    year = bf["year"].to_numpy()
    return {y: _selectivity(rvol >= rvol_min, brk, valid, year, y) for y in YEARS}


# ---------------------------------------------------------------------------
# M5 -- session-normalised RVOL characterisation
# ---------------------------------------------------------------------------

def m5_session(bf, baseline_days_list=(5, 10, 20, 30), rvol_min=1.5):
    brk_l, brk_s = breakout_masks(bf)
    brk = brk_l | brk_s
    ts = bf["ts"].to_numpy()
    vol = bf["volume"].to_numpy(float)
    flat = bf["rvol"].to_numpy(float)
    year = bf["year"].to_numpy()
    hour = bf["hour"].to_numpy()

    out = {}
    for bd in baseline_days_list:
        srv = session_rvol(ts, vol, bd)
        valid = np.isfinite(srv)
        per_year = {}
        for y in YEARS:
            ym = year == y
            fb = ym & brk & np.isfinite(flat)
            sb = ym & brk & valid
            if not fb.sum() or not sb.sum():
                per_year[y] = {"n_breakout_session": int(sb.sum())}
                continue
            target = float((flat[fb] >= rvol_min).mean())
            # Threshold reproducing the SAME pass rate on breakout bars.
            thr = float(np.quantile(srv[sb], 1.0 - target)) if 0 < target < 1 \
                else float("nan")
            sel = _selectivity(srv >= thr, brk, valid, year, y) \
                if np.isfinite(thr) else {}
            per_year[y] = {
                "n_breakout_session": int(sb.sum()),
                "flat_pass_breakout": target,
                "equivalent_threshold": thr,
                "dist_breakout": describe(srv[sb]),
                "selectivity_at_equiv": sel,
                "warmup_first_ts": int(ts[valid][0]) if valid.any() else None,
            }
            # Pass rate by UTC hour, flat vs session, matched selectivity.
            by_hour = {}
            for h in range(24):
                hm = ym & brk & (hour == h)
                f = hm & np.isfinite(flat)
                s = hm & valid
                by_hour[h] = {
                    "n_flat": int(f.sum()),
                    "flat": float((flat[f] >= rvol_min).mean()) if f.sum() else None,
                    "n_session": int(s.sum()),
                    "session": (float((srv[s] >= thr).mean())
                                if s.sum() and np.isfinite(thr) else None),
                }
            per_year[y]["by_hour"] = by_hour
        out[bd] = per_year
    return out


# ---------------------------------------------------------------------------
# M6 -- B2 denomination stability
# ---------------------------------------------------------------------------

def m6_denomination(bf, window=20):
    """Stability of the trailing RVOL baseline, quote vs base denominated.

    Two statistics, because they answer different questions:

      within_window_cv -- median over the window of rolling_std/rolling_mean of
        the SAME trailing 20 bars that form the denominator. This is the local
        statistic, and it is the operative one: RVOL is always computed locally,
        so what matters is how noisy the denominator is at the moment it is
        used.

      global_cv -- std/mean of the baseline SERIES across the whole year. This
        is the drift statistic B2's justification appeals to, and for quote
        volume it necessarily inherits the year's price trajectory.

    Lower is more stable in both cases.
    """
    year = bf["year"].to_numpy()
    out = {}
    for field in ("volume", "quote_volume"):
        v = pd.Series(bf[field].to_numpy(float))
        base = v.rolling(window).mean().shift(1)
        roll_cv = (v.rolling(window).std().shift(1)
                   / base.replace(0.0, np.nan)).to_numpy(float)
        b = base.to_numpy(float)
        per_year = {}
        for y in YEARS:
            ym = (year == y) & np.isfinite(b)
            bb = b[ym]
            rr = roll_cv[(year == y) & np.isfinite(roll_cv)]
            per_year[y] = {
                "n": int(ym.sum()),
                "within_window_cv": float(np.median(rr)) if len(rr) else float("nan"),
                "global_cv": float(bb.std() / bb.mean()) if len(bb) else float("nan"),
            }
        out[field] = per_year
    return out


# ---------------------------------------------------------------------------
# M7 -- F2 rsi_lower rejection rate
# ---------------------------------------------------------------------------

def m7_rsi_lower(bf, lo=50.0):
    """Rejection by the LOWER RSI bound alone: long RSI<50, short RSI>50."""
    brk_l, brk_s = breakout_masks(bf)
    rsi = bf["rsi"].to_numpy(float)
    fin = np.isfinite(rsi)
    year = bf["year"].to_numpy()
    rej = ((brk_l & (rsi < lo)) | (brk_s & (rsi > lo))) & fin
    brk = (brk_l | brk_s) & fin

    out = {}
    for y in YEARS:
        ym = year == y
        b = ym & brk
        r = ym & rej
        if not b.sum():
            out[y] = {"n_breakout": 0}
            continue
        prof = {}
        for col in ("atr_pct", "close_position", "vwap_position"):
            x = bf[col].to_numpy(float)
            prof[col] = {
                "rejected_median": float(np.nanmedian(x[r])) if r.sum() else None,
                "accepted_median": float(np.nanmedian(x[b & ~rej])),
            }
        out[y] = {
            "n_breakout": int(b.sum()),
            "n_rejected": int(r.sum()),
            "reject_rate": float(r.sum() / b.sum()),
            "n_rejected_long": int((ym & brk_l & (rsi < lo) & fin).sum()),
            "n_rejected_short": int((ym & brk_s & (rsi > lo) & fin).sum()),
            "profile": prof,
        }
    return out


# ---------------------------------------------------------------------------
# M8 -- derived stop floor and ATR scale
# ---------------------------------------------------------------------------

def m8_floor(bf, symbol, cfg=None, n_cost=6.0):
    """The A2 floor, and the ATR multiplier m* at which median ATR% clears it.

    m* IS REPORTED FOR SCALE ONLY. Section 3 / A6 requires the operational
    anchor to be computed per walk-forward training fold at Point 4; a globally
    computed anchor would read the holdout. This number must never be used as
    the operational anchor.
    """
    cfg = cfg or costs.CostConfig()
    fees = 2 * cfg.taker_fee
    entry_slip = cfg.entry_slippage_bps / 10_000.0
    haircut = cfg.haircut_bps(symbol) / 10_000.0

    # As the engine actually applies it: entry slippage on the entry leg, the
    # stop-market haircut on the stop leg.
    c_engine = fees + entry_slip + haircut
    # As the prompt words it: the haircut on both sides.
    c_both = fees + 2 * haircut

    lev = cfg.risk_usd / (cfg.equity_usd * cfg.max_leverage)
    res = {"fees_roundtrip": fees, "entry_slippage": entry_slip,
           "stop_haircut": haircut, "leverage_term": lev, "n_cost": n_cost,
           "variants": {}}
    for name, c in (("engine_as_implemented", c_engine), ("haircut_both_sides", c_both)):
        cost_term = n_cost * c
        floor = max(cost_term, lev)
        res["variants"][name] = {
            "c_roundtrip": c, "cost_term": cost_term, "leverage_term": lev,
            "stop_min_pct": floor,
            "dominant": "cost" if cost_term >= lev else "leverage",
            "cost_over_leverage": cost_term / lev,
        }

    brk_l, brk_s = breakout_masks(bf)
    brk = brk_l | brk_s
    atr_pct = bf["atr_pct"].to_numpy(float)
    year = bf["year"].to_numpy()
    res["atr_pct"] = {}
    for y in YEARS:
        m = (year == y) & brk & np.isfinite(atr_pct)
        d = describe(atr_pct[m])
        med = d.get("median")
        d["m_star"] = {k: (v["stop_min_pct"] / med if med else None)
                       for k, v in res["variants"].items()}
        res["atr_pct"][y] = d
    return res


# ---------------------------------------------------------------------------
# M9 -- signal counts per gate arm
# ---------------------------------------------------------------------------

VP_GRID = (0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8)


def m9_counts(bf, rvol_min=1.5, rsi_lo=50.0, vp_grid=VP_GRID):
    """Counts of SIGNAL BARS surviving each arm. No trade is simulated.

    Portfolio-mode occupancy (one position per symbol) would reduce these
    further; signal mode is the edge-test instrument and is what the evidence
    minimums are denominated in.
    """
    brk_l, brk_s = breakout_masks(bf)
    rvol = bf["rvol"].to_numpy(float)
    rsi = bf["rsi"].to_numpy(float)
    vp = bf["vwap_position"].to_numpy(float)
    deg = bf["degenerate"].to_numpy()
    year = bf["year"].to_numpy()
    fin = np.isfinite(rvol) & np.isfinite(rsi)

    out = {}
    for y in YEARS:
        ym = year == y
        per_dir = {}
        for name, brk in ((LONG, brk_l), (SHORT, brk_s)):
            base = ym & brk & fin
            rv = base & (rvol >= rvol_min)
            rsi_ok = base & ((rsi >= rsi_lo) if name == LONG else (rsi <= rsi_lo))
            # vwap gate: degenerate bars FAIL by construction.
            curve, curve_both = {}, {}
            for t in vp_grid:
                g = ((vp >= t) if name == LONG else ((1.0 - vp) >= t)) & ~deg
                g = g & np.isfinite(vp)
                curve[t] = int((base & g).sum())
                curve_both[t] = int((rv & g).sum())
            per_dir[name] = {
                "ungated": int(base.sum()),
                "rvol_only": int(rv.sum()),
                "vwap_only_curve": curve,
                "both_curve": curve_both,
                "with_rsi_lower": int(rsi_ok.sum()),
                "rvol_and_rsi_lower": int((rv & rsi_ok).sum()),
            }
        out[y] = per_dir
    return out


# ---------------------------------------------------------------------------
# driver
# ---------------------------------------------------------------------------

def run_all(symbols=SYMBOLS, derived_dir=DERIVED):
    manifest = check_manifest(derived_dir)
    if not manifest["ok"]:
        raise RuntimeError(f"manifest integrity failed: {manifest}")
    schedules = contracts.load_cache()
    results = {"manifest": manifest, "symbols": {}}
    for sym in symbols:
        df = load_window(sym, derived_dir)
        bf = bar_frame(df)
        brk_l, brk_s = breakout_masks(bf)
        results["symbols"][sym] = {
            "bars": int(len(bf)),
            "first_ts": int(bf["ts"].iloc[0]), "last_ts": int(bf["ts"].iloc[-1]),
            "n_degenerate": int(bf["degenerate"].sum()),
            "n_zero_volume": int(bf["zero_volume"].sum()),
            "n_breakout_long": int(brk_l.sum()),
            "n_breakout_short": int(brk_s.sum()),
            "m1": m1_validity(bf, sym, schedules),
            "m2_m3": m2_m3(bf),
            "m4": m4_flat_selectivity(bf),
            "m5": m5_session(bf),
            "m6": m6_denomination(bf),
            "m7": m7_rsi_lower(bf),
            "m8": m8_floor(bf, sym),
            "m9": m9_counts(bf),
        }
    return results


def _json_safe(o):
    if isinstance(o, dict):
        return {str(k): _json_safe(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [_json_safe(v) for v in o]
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating,)):
        return None if not np.isfinite(o) else float(o)
    if isinstance(o, float):
        return None if not np.isfinite(o) else o
    if isinstance(o, (np.bool_,)):
        return bool(o)
    return o


if __name__ == "__main__":
    res = run_all()
    dest = os.path.join(ROOT, "reports", "07_structural_pass_raw.json")
    with open(dest, "w") as fh:
        json.dump(_json_safe(res), fh, indent=2, sort_keys=True)
        fh.write("\n")
    print(f"written: {dest}")
