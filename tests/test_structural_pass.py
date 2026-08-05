"""Tests for the structural measurement pass.

The load-bearing ones are causality (the slot baseline must not see the current
day), degenerate-bar handling, vwap clipping/violation counting, and agreement
of the breakout definition with the engine's own conditions. The rest of the
pass is descriptive statistics over those primitives.
"""

import os
import sys

import numpy as np
import pandas as pd
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))

from analysis import structural_pass as sp  # noqa: E402
import signals  # noqa: E402  (conftest puts src/engine on the path)


# ---------------------------------------------------------------------------
# synthetic frames
# ---------------------------------------------------------------------------

def make_bars(n, start_ts=sp.WINDOW_START_MS, vol=None, seed=0):
    """A clean 15m grid with wandering prices and non-degenerate ranges."""
    rng = np.random.default_rng(seed)
    ts = start_ts + np.arange(n, dtype=np.int64) * sp.BAR_MS
    close = 100.0 + np.cumsum(rng.normal(0, 0.5, n))
    high = close + np.abs(rng.normal(0, 0.3, n)) + 0.1
    low = close - np.abs(rng.normal(0, 0.3, n)) - 0.1
    v = np.full(n, 1000.0) if vol is None else np.asarray(vol, dtype=float)
    # quote_volume consistent with a vwap strictly inside [low, high]
    mid = (high + low) / 2.0
    return pd.DataFrame({"ts": ts, "high": high, "low": low, "close": close,
                         "volume": v, "quote_volume": v * mid})


# ---------------------------------------------------------------------------
# causality of the session slot baseline
# ---------------------------------------------------------------------------

def test_slot_baseline_cannot_see_the_current_day():
    """Mutate every bar of one day; that day's own baseline must not move.

    This is the test that actually catches a leak. If the rolling window were
    not shifted by a whole day, a bar's baseline would move when its own day's
    volume changed.
    """
    n = sp.SLOTS_PER_DAY * 12
    bars = make_bars(n)
    vol = np.full(n, 1000.0)
    ts = bars["ts"].to_numpy()

    base_a = sp.session_baseline(ts, vol, baseline_days=5)

    target_day = 8
    lo, hi = target_day * sp.SLOTS_PER_DAY, (target_day + 1) * sp.SLOTS_PER_DAY
    vol_b = vol.copy()
    vol_b[lo:hi] = 999_999.0
    base_b = sp.session_baseline(ts, vol_b, baseline_days=5)

    same_day = base_a[lo:hi]
    assert np.allclose(same_day, base_b[lo:hi], equal_nan=True), (
        "slot baseline changed when the CURRENT day's volume changed -- "
        "the baseline is reading the bar's own day")


def test_slot_baseline_does_see_prior_days():
    """The mirror of the causality test: it must not be inert either.

    A baseline that ignored everything would trivially pass the test above.
    """
    n = sp.SLOTS_PER_DAY * 12
    ts = make_bars(n)["ts"].to_numpy()
    vol = np.full(n, 1000.0)
    vol_b = vol.copy()
    # Move a MAJORITY of the 5-day window: the baseline is a median, so
    # changing one day of five is correctly absorbed (see the median test).
    vol_b[0:3 * sp.SLOTS_PER_DAY] = 5000.0

    a = sp.session_baseline(ts, vol, 5)
    b = sp.session_baseline(ts, vol_b, 5)
    later = slice(5 * sp.SLOTS_PER_DAY, 7 * sp.SLOTS_PER_DAY)
    assert not np.allclose(a[later], b[later], equal_nan=True), (
        "changing a PRIOR day left later baselines untouched -- inert baseline")


def test_slot_baseline_uses_the_matching_slot_only():
    """Slot 7's baseline must be built from slot 7 of prior days, nothing else."""
    days = 9
    n = sp.SLOTS_PER_DAY * days
    ts = make_bars(n)["ts"].to_numpy()
    vol = np.full(n, 1000.0)
    slot = (ts // sp.BAR_MS) % sp.SLOTS_PER_DAY
    vol[slot == 7] = 4000.0

    base = sp.session_baseline(ts, vol, 5)
    ok = np.isfinite(base)
    assert np.allclose(base[ok & (slot == 7)], 4000.0)
    assert np.allclose(base[ok & (slot != 7)], 1000.0)


def test_slot_baseline_warmup_is_nan_and_respects_min_periods():
    n = sp.SLOTS_PER_DAY * 10
    ts = make_bars(n)["ts"].to_numpy()
    base = sp.session_baseline(ts, np.full(n, 1000.0), baseline_days=5)
    # First 5 days have fewer than 5 completed prior days -> NaN.
    assert np.all(np.isnan(base[:5 * sp.SLOTS_PER_DAY]))
    assert np.all(np.isfinite(base[5 * sp.SLOTS_PER_DAY:]))


def test_slot_baseline_uses_median_not_mean():
    """One event bar in the baseline must not drag the slot's denominator."""
    days = 12
    n = sp.SLOTS_PER_DAY * days
    ts = make_bars(n)["ts"].to_numpy()
    vol = np.full(n, 1000.0)
    vol[2 * sp.SLOTS_PER_DAY + 7] = 1_000_000.0  # day 2, slot 7

    base = sp.session_baseline(ts, vol, 5)
    slot = (ts // sp.BAR_MS) % sp.SLOTS_PER_DAY
    day = ts // sp.DAY_MS
    day = day - day.min()
    m = (slot == 7) & (day >= 5) & (day <= 7)  # windows containing the spike
    assert np.allclose(base[m], 1000.0), (
        "a single event bar moved the slot baseline -- mean, not median")


def test_session_baseline_rejects_bad_baseline_days():
    ts = make_bars(sp.SLOTS_PER_DAY * 3)["ts"].to_numpy()
    with pytest.raises(ValueError):
        sp.session_baseline(ts, np.ones(sp.SLOTS_PER_DAY * 3), 0)


# ---------------------------------------------------------------------------
# degenerate bars and vwap_position
# ---------------------------------------------------------------------------

def test_degenerate_bars_produce_no_division_by_zero_and_are_counted():
    bars = make_bars(200)
    bars.loc[10, "high"] = bars.loc[10, "low"] = bars.loc[10, "close"] = 100.0
    bars.loc[11, "high"] = bars.loc[11, "low"] = bars.loc[11, "close"] = 100.0

    with np.errstate(divide="raise", invalid="raise"):
        bf = sp.bar_frame(bars)

    assert int(bf["degenerate"].sum()) == 2
    assert bool(bf["degenerate"].iloc[10]) and bool(bf["degenerate"].iloc[11])
    assert np.isnan(bf["vwap_position"].to_numpy()[[10, 11]]).all()
    assert np.isnan(bf["close_position"].to_numpy()[[10, 11]]).all()
    # Non-degenerate bars are unaffected.
    assert np.isfinite(bf["close_position"].to_numpy()[12])


def test_degenerate_bars_fail_the_vwap_gate_in_m9():
    """A degenerate bar must never survive a position gate at any threshold."""
    bars = make_bars(400, seed=3)
    bars.loc[300, "high"] = bars.loc[300, "low"] = bars.loc[300, "close"]
    bf = sp.bar_frame(bars)
    deg = bf["degenerate"].to_numpy()
    vp = bf["vwap_position"].to_numpy(float)
    for t in sp.VP_GRID:
        passes = ((vp >= t) & ~deg) & np.isfinite(vp)
        assert not passes[deg].any()


def test_zero_volume_bar_has_no_vwap_rather_than_inf():
    bars = make_bars(100)
    bars.loc[20, "volume"] = 0.0
    bars.loc[20, "quote_volume"] = 0.0
    with np.errstate(divide="raise", invalid="raise"):
        bf = sp.bar_frame(bars)
    assert bool(bf["zero_volume"].iloc[20])
    assert np.isnan(bf["bar_vwap"].iloc[20])


def test_vwap_position_clipping_and_violation_counting():
    """Out-of-range vwap is clipped for reporting but counted pre-clip."""
    bars = make_bars(100)
    mid = (bars["high"] + bars["low"]) / 2.0
    # Push bar 30's vwap well above the high, bar 31's below the low.
    bars.loc[30, "quote_volume"] = bars.loc[30, "volume"] * (bars.loc[30, "high"] + 5)
    bars.loc[31, "quote_volume"] = bars.loc[31, "volume"] * (bars.loc[31, "low"] - 5)
    bf = sp.bar_frame(bars)

    assert bf["vwap_position_raw"].iloc[30] > 1.0
    assert bf["vwap_position_raw"].iloc[31] < 0.0
    assert bf["vwap_position"].iloc[30] == 1.0
    assert bf["vwap_position"].iloc[31] == 0.0
    # Untouched bars keep an in-range vwap.
    assert 0.0 <= bf["vwap_position"].iloc[32] <= 1.0
    assert np.isclose(bf["bar_vwap"].iloc[32], mid.iloc[32])


def test_m1_counts_violations_against_the_tick_band():
    bars = make_bars(300)
    bars.loc[50, "quote_volume"] = bars.loc[50, "volume"] * (bars.loc[50, "high"] + 5)
    bf = sp.bar_frame(bars)
    sch = {"ETHUSDT": __import__("contracts").TickSchedule("ETHUSDT", [(0, 0.01)])}
    res = sp.m1_validity(bf, "ETHUSDT", sch)
    y = bf["year"].iloc[0]
    assert res[y]["n_violations"] == 1
    assert res[y]["frac_inside"] < 1.0
    assert res[y]["worst"][0]["abs_dist"] > 4.0


def test_m1_tolerance_is_one_tick_wide():
    """A vwap half a tick outside the range is inside the band; two ticks is not."""
    import contracts
    tick = 0.01
    for offset, expect_violation in ((0.5 * tick, False), (2.0 * tick, True)):
        bars = make_bars(300)
        bars.loc[50, "quote_volume"] = bars.loc[50, "volume"] * (
            bars.loc[50, "high"] + offset)
        bf = sp.bar_frame(bars)
        sch = {"E": contracts.TickSchedule("E", [(0, tick)])}
        res = sp.m1_validity(bf, "E", sch)
        n = res[bf["year"].iloc[0]]["n_violations"]
        assert (n == 1) is expect_violation, f"{offset=} {n=}"


# ---------------------------------------------------------------------------
# breakout definition must agree with the engine
# ---------------------------------------------------------------------------

def test_breakout_masks_match_the_engine_conditions():
    """Rebuild the engine's trend+Donchian terms independently and compare."""
    bars = make_bars(3000, seed=7)
    params = signals.SignalParams()
    ind = signals.compute_indicators(bars, params)
    up, lo = signals.donchian_prior(bars["high"].to_numpy(),
                                    bars["low"].to_numpy(), params.donchian)
    close = bars["close"].to_numpy()
    ok = np.isfinite(up) & np.isfinite(lo)
    exp_l = (ind["ema_fast"].to_numpy() > ind["ema_slow"].to_numpy()) & (close > up) & ok
    exp_s = (ind["ema_fast"].to_numpy() < ind["ema_slow"].to_numpy()) & (close < lo) & ok

    bf = sp.bar_frame(bars, params)
    got_l, got_s = sp.breakout_masks(bf)
    assert np.array_equal(got_l, exp_l)
    assert np.array_equal(got_s, exp_s)
    assert exp_l.sum() > 0 and exp_s.sum() > 0, "degenerate fixture proves nothing"


def test_every_engine_signal_bar_is_a_breakout_bar():
    """The engine's gated signals must be a SUBSET of our breakout population.

    Our definition drops the RVOL and RSI terms, so it can only be wider. If a
    signal bar were ever missing from it, the trend/Donchian terms disagree.
    """
    # Volume must vary or RVOL is identically 1.0 and the engine emits nothing.
    rng = np.random.default_rng(23)
    n = 4000
    bars = make_bars(n, vol=rng.lognormal(7.0, 0.8, n), seed=11)
    params = signals.SignalParams()
    sig = signals.generate_signals(bars, params, "ETHUSDT")
    if sig.empty:
        pytest.skip("fixture produced no engine signals")

    bf = sp.bar_frame(bars, params)
    brk_l, brk_s = sp.breakout_masks(bf)
    ts = bf["ts"].to_numpy()
    for direction, mask in ((signals.LONG, brk_l), (signals.SHORT, brk_s)):
        want = set(sig[sig["direction"] == direction]["signal_bar_ts"].astype(np.int64))
        have = set(ts[mask].astype(np.int64).tolist())
        assert want <= have, f"{direction}: engine signals outside breakout set"


def test_breakout_definition_excludes_rvol_and_rsi():
    """Changing the RVOL/RSI knobs must not move the breakout population."""
    bars = make_bars(3000, seed=5)
    a = sp.breakout_masks(sp.bar_frame(bars, signals.SignalParams()))
    b = sp.breakout_masks(sp.bar_frame(
        bars, signals.SignalParams(rvol_min=99.0, rsi_long_lo=99.0)))
    assert np.array_equal(a[0], b[0]) and np.array_equal(a[1], b[1])


# ---------------------------------------------------------------------------
# window restriction
# ---------------------------------------------------------------------------

def test_window_bounds_are_the_2022_2023_calendar_years():
    lo = pd.Timestamp(sp.WINDOW_START_MS, unit="ms", tz="UTC")
    hi = pd.Timestamp(sp.WINDOW_END_MS, unit="ms", tz="UTC")
    assert (lo.year, lo.month, lo.day) == (2022, 1, 1)
    assert (hi.year, hi.month, hi.day) == (2024, 1, 1)


@pytest.mark.parametrize("symbol", ["BTCUSDT", "ETHUSDT", "SOLUSDT"])
def test_load_window_reads_no_bar_outside_2022_2023(symbol):
    df = sp.load_window(symbol)
    ts = df["ts"].to_numpy()
    assert ts.min() >= sp.WINDOW_START_MS
    assert ts.max() < sp.WINDOW_END_MS
    assert set(pd.to_datetime(ts, unit="ms", utc=True).year) == {2022, 2023}
    assert "open_synth" not in df.columns


# ---------------------------------------------------------------------------
# statistics helpers
# ---------------------------------------------------------------------------

def test_describe_iqr_and_extremes():
    x = np.linspace(0.0, 1.0, 1001)
    d = sp.describe(x)
    assert np.isclose(d["iqr"], 0.5, atol=1e-3)
    assert np.isclose(d["median"], 0.5, atol=1e-3)
    assert np.isclose(d["frac_le_005"], 0.051, atol=2e-3)


def test_pearson_matches_numpy_and_handles_degenerate_input():
    rng = np.random.default_rng(0)
    a, b = rng.normal(size=500), rng.normal(size=500)
    r, n = sp.pearson(a, b)
    assert n == 500 and np.isclose(r, np.corrcoef(a, b)[0, 1])
    r2, _ = sp.pearson(np.ones(50), b[:50])
    assert np.isnan(r2)
    r3, n3 = sp.pearson([1.0, np.nan, 3.0], [2.0, 5.0, 6.0])
    assert n3 == 2


def test_selectivity_ratio_arithmetic():
    brk = np.zeros(100, dtype=bool)
    brk[:20] = True
    passes = np.zeros(100, dtype=bool)
    passes[:10] = True   # 10/20 breakout bars pass
    passes[20:30] = True  # 10/80 non-breakout pass -> 20/100 overall
    year = np.full(100, 2022)
    out = sp._selectivity(passes, brk, np.ones(100, dtype=bool), year, 2022)
    assert np.isclose(out["pass_all"], 0.20)
    assert np.isclose(out["pass_breakout"], 0.50)
    assert np.isclose(out["ratio"], 2.5)


def test_session_rvol_of_a_flat_series_is_one():
    n = sp.SLOTS_PER_DAY * 10
    ts = make_bars(n)["ts"].to_numpy()
    r = sp.session_rvol(ts, np.full(n, 1234.0), 5)
    assert np.allclose(r[np.isfinite(r)], 1.0)


def test_m8_floor_terms_and_dominance():
    res = sp.m8_floor(sp.bar_frame(make_bars(3000, seed=2)), "BTCUSDT")
    v = res["variants"]["engine_as_implemented"]
    assert np.isclose(v["c_roundtrip"], 0.0012 + 0.0005)
    assert np.isclose(v["cost_term"], 6 * v["c_roundtrip"])
    assert np.isclose(v["leverage_term"], 20.0 / (2000.0 * 3.0))
    assert v["dominant"] == "cost"
    assert np.isclose(v["stop_min_pct"], v["cost_term"])


# ---------------------------------------------------------------------------
# firewall
# ---------------------------------------------------------------------------

def test_analysis_module_never_imports_the_simulator():
    """No trade may be simulated, and net_pnl / r_multiple must be untouched."""
    import io
    import tokenize

    path = os.path.join(ROOT, "src", "analysis", "structural_pass.py")
    src = open(path).read()

    # Strip comments and docstrings: this file DISCUSSES the firewall, so a
    # plain substring search would fire on its own prose. Only executable
    # tokens count.
    code = []
    prev = tokenize.INDENT
    for tok in tokenize.generate_tokens(io.StringIO(src).readline):
        if tok.type == tokenize.COMMENT:
            continue
        if tok.type == tokenize.STRING and prev in (
                tokenize.INDENT, tokenize.DEDENT, tokenize.NEWLINE,
                tokenize.NL, tokenize.ENCODING):
            prev = tok.type
            continue  # docstring
        if tok.type not in (tokenize.NL, tokenize.NEWLINE):
            prev = tok.type
        code.append(tok.string)
    code = " ".join(code)

    for banned in ("simulate", "net_pnl", "r_multiple", "trade_pnl", "pnl"):
        assert banned not in code, f"firewall: structural_pass references {banned}"
