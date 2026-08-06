"""Causality guard for the regime module, tested against its own mutations.

THIS IS THE LOAD-BEARING TEST FILE.

A generic `assert_causal` is known to pass vacuously in this codebase: three
such guards have already been found. The RVOL slot baseline was the clearest
case -- it is indexed by (day, slot), so truncating history at bar T leaves bar
T's own cell intact, a dropped day-shift recomputes identically, and the guard
reports success while testing nothing.

So this file does not assert that the guard passes on correct code. That proves
nothing. It DELIBERATELY INTRODUCES the specific bug the guard exists to catch
-- a window whose right edge slips from T to T+1 -- and asserts the guard FAILS.
A guard that cannot detect its own target mutation is worthless.

Three distinct mutations are planted, each hitting a different axis, so a guard
that happens to catch one by luck cannot pass this file.
"""

import os
import sys

import numpy as np
import pandas as pd
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))

from regime import labels as lb  # noqa: E402
from regime import measure as ms  # noqa: E402

WINDOW_DAYS = 2                      # 192 bars: enough to be real, fast to run
SYMBOL = "ETHUSDT"


def synth(days=12, seed=7, ts0=1_640_995_200_000):
    """A deterministic random walk on a whole-day 15m grid, from a UTC midnight."""
    n = days * ms.BARS_PER_DAY
    rng = np.random.default_rng(seed)
    close = 100 + np.cumsum(rng.normal(0, 0.5, n))
    high = close + np.abs(rng.normal(0, 0.3, n)) + 0.05
    low = close - np.abs(rng.normal(0, 0.3, n)) - 0.05
    vol = np.abs(rng.normal(1000, 200, n)) + 1.0
    return pd.DataFrame({
        "ts": [ts0 + i * ms.BAR_15M_MS for i in range(n)],
        "high": high, "low": low, "close": close,
        "volume": vol, "quote_volume": vol * close,
    })


# ---------------------------------------------------------------------------
# the mutations
# ---------------------------------------------------------------------------

def _roll_ahead_one(series, n):
    """MUTANT: window right edge at T+1 instead of T.

    This is the dropped-shift bug in its exact form: every rolling statistic
    silently includes one bar the strategy could not have seen.
    """
    return series.shift(-1).rolling(n, min_periods=n)


def _lag_short_one(series, n):
    """MUTANT: reach back n-1 bars instead of n.

    Subtler than the above -- it does not read the future directly, but it
    misaligns the numerator against the denominator, so the window's span no
    longer matches what the label claims to describe.
    """
    return series.shift(n - 1)


def _lag_ahead_one(series, n):
    """MUTANT: reach FORWARD one bar. Reads close[T+1] outright."""
    return series.shift(n).shift(-1)


# ---------------------------------------------------------------------------
# (a) THE MUTATION TESTS -- the guard must fail on each
# ---------------------------------------------------------------------------

def test_guard_catches_rolling_window_shifted_one_bar_forward(monkeypatch):
    """The primary target: a rolling window whose right edge slips to T+1.

    Hits median(ATR%) inside m*, the efficiency denominator, the EMA fraction
    and the liquidity median simultaneously.
    """
    df = synth()
    # Sanity: the guard passes on the UNMUTATED module. If this ever fails,
    # the mutation test below would be meaningless.
    assert ms.assert_causal(df, SYMBOL, WINDOW_DAYS, n_checks=6) > 0

    monkeypatch.setattr(ms, "_ROLL", _roll_ahead_one)
    with pytest.raises(AssertionError, match="look-ahead"):
        ms.assert_causal(df, SYMBOL, WINDOW_DAYS, n_checks=6)


def test_guard_catches_lag_reaching_one_bar_forward(monkeypatch):
    """A lag that reads close[T+1] directly -- efficiency numerator and drift."""
    df = synth()
    monkeypatch.setattr(ms, "_LAG", _lag_ahead_one)
    with pytest.raises(AssertionError, match="look-ahead"):
        ms.assert_causal(df, SYMBOL, WINDOW_DAYS, n_checks=6)


def test_guard_catches_a_shortened_lag(monkeypatch):
    """A lag off by one BACKWARD.

    Not look-ahead, so truncation alone would not catch it -- and it does not:
    this asserts the value MOVES, which is what a separate span-consistency
    test must catch. Recorded here so the boundary of what the causality guard
    can and cannot see is explicit rather than assumed.
    """
    df = synth()
    good = ms.measure(df, SYMBOL, WINDOW_DAYS)
    monkeypatch.setattr(ms, "_LAG", _lag_short_one)
    bad = ms.measure(df, SYMBOL, WINDOW_DAYS)

    # The causality guard does NOT fire -- the mutation reads no future bar.
    caught = False
    try:
        ms.assert_causal(df, SYMBOL, WINDOW_DAYS, n_checks=6)
    except AssertionError:
        caught = True
    assert caught is False, (
        "the causality guard now catches a purely backward misalignment; that "
        "is an improvement -- revisit this test rather than deleting it")

    # But the values genuinely differ, so the span-consistency fixtures in
    # test_regime_measure.py (exact ramp = 1.0, exact zigzag = 0.0) are what
    # stand between this bug and the output.
    a = good["efficiency_ratio"].to_numpy()
    b = bad["efficiency_ratio"].to_numpy()
    both = np.isfinite(a) & np.isfinite(b)
    assert both.any()
    assert not np.allclose(a[both], b[both]), (
        "a shortened lag left the efficiency ratio unchanged; the fixture is "
        "too degenerate to demonstrate anything")


def test_guard_is_not_vacuous_because_it_checks_arbitrary_bars():
    """The guard must inspect bars regardless of whether they carry values.

    Checking only non-NaN rows is the vacuity mode: a leak that turns rows into
    NaN leaves nothing to compare and the guard reports success.
    """
    df = synth()
    n = ms.bars_for_days(WINDOW_DAYS)
    checked = ms.assert_causal(df, SYMBOL, WINDOW_DAYS, n_checks=25, seed=3)
    assert checked > 0
    # And there really are NaN rows in range, so "arbitrary bars" is meaningful.
    full = ms.measure(df, SYMBOL, WINDOW_DAYS)
    assert full["m_star"].isna().sum() >= n


def test_guard_refuses_a_history_too_short_to_test():
    """Silently passing on a series with no testable bars is a vacuity mode."""
    df = synth(days=1)
    with pytest.raises(ValueError, match="too short"):
        ms.assert_causal(df, SYMBOL, WINDOW_DAYS)


# ---------------------------------------------------------------------------
# (b) truncation invariance
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("window_days", [1, 2, 3])
def test_truncation_invariance_over_prefixes(window_days):
    """Values over bars 0..N must equal values over bars 0..M for M > N.

    Stronger than the sampled guard: this compares EVERY bar of the prefix, on
    every measured column, for several window lengths.
    """
    df = synth(days=14)
    n_bars = len(df)
    short = ms.measure(df.iloc[:n_bars // 2], SYMBOL, window_days)
    long_ = ms.measure(df, SYMBOL, window_days)
    for col in ms.MEASURE_COLS:
        a = short[col].to_numpy()
        b = long_[col].to_numpy()[:len(short)]
        assert np.allclose(a, b, rtol=1e-12, atol=1e-12, equal_nan=True), (
            f"{col} moved when later bars were appended")


def test_truncation_invariance_of_labels_with_frozen_cuts(tmp_path):
    """Labels must not move either -- frozen cuts, not full-sample quantiles."""
    df = synth(days=14)
    fit_end = int(df["ts"].to_numpy()[len(df) // 2])
    full = ms.measure(df, SYMBOL, WINDOW_DAYS)
    cuts = lb.fit_terciles(full["m_star"], int(df["ts"].to_numpy()[0]),
                           fit_end, ts=full["ts"])

    half = ms.measure(df.iloc[:len(df) // 2], SYMBOL, WINDOW_DAYS)
    lab_half = lb.apply_terciles(half["m_star"], cuts)
    lab_full = lb.apply_terciles(full["m_star"], cuts)[:len(half)]
    assert list(lab_half) == list(lab_full)


def test_refitting_cuts_on_all_data_is_detectable_as_a_leak():
    """MUTATION 3: fit terciles on everything instead of the frozen window.

    The failure mode has no shift in it at all, so no amount of truncation
    testing on `measure` would find it. It is caught by comparing the cuts
    themselves, which is why the fit window is a required argument rather than
    an optional one.
    """
    df = synth(days=14)
    full = ms.measure(df, SYMBOL, WINDOW_DAYS)
    ts = full["ts"]
    t0, mid, t1 = (int(ts.iloc[0]), int(ts.iloc[len(ts) // 2]),
                   int(ts.iloc[-1]) + 1)

    frozen = lb.fit_terciles(full["m_star"], t0, mid, ts=ts)
    leaked = lb.fit_terciles(full["m_star"], t0, t1, ts=ts)
    assert frozen != leaked, (
        "fitting on the full sample gave the same cuts as fitting on the "
        "frozen window; the fixture cannot demonstrate the leak")

    # And the API makes the leak impossible to commit by accident: an
    # unbounded fit raises rather than silently using everything present.
    with pytest.raises(ValueError, match="full-sample quantile"):
        lb.fit_terciles(full["m_star"], t0, mid, ts=None)


# ---------------------------------------------------------------------------
# firewall
# ---------------------------------------------------------------------------

def test_regime_module_never_imports_the_simulator():
    """OHLCV in, regime labels out. No trade outcome may be reachable."""
    import io
    import tokenize

    for name in ("measure.py", "labels.py", "__init__.py"):
        path = os.path.join(ROOT, "src", "regime", name)
        src = open(path).read()
        code, prev = [], tokenize.INDENT
        for tok in tokenize.generate_tokens(io.StringIO(src).readline):
            if tok.type == tokenize.COMMENT:
                continue
            if tok.type == tokenize.STRING and prev in (
                    tokenize.INDENT, tokenize.DEDENT, tokenize.NEWLINE,
                    tokenize.NL, tokenize.ENCODING):
                prev = tok.type
                continue
            if tok.type not in (tokenize.NL, tokenize.NEWLINE):
                prev = tok.type
            code.append(tok.string)
        code = " ".join(code)
        for banned in ("simulate", "net_pnl", "r_multiple", "trade_pnl",
                       "expectancy", "pnl", "win_rate"):
            assert banned not in code, f"{name} references {banned}"


def test_stop_min_pct_is_the_only_strategy_parameter_and_is_invariant():
    """The regime axis must not become a channel for a swept parameter.

    stop_min_pct is constructed through a CostConfig that requires four
    parameters with no defaults. None of them enters the floor. Proving that
    directly is what keeps the arbitrary values in _UNUSED_SWEEP_PARAMS from
    quietly becoming a choice.
    """
    import costs
    a = costs.CostConfig(stop_atr_mult=1.0, stop_max_pct=0.035,
                         rvol_threshold=1.5, baseline_days=20)
    b = costs.CostConfig(stop_atr_mult=99.0, stop_max_pct=0.999,
                         rvol_threshold=99.0, baseline_days=99)
    for sym in ms.SYMBOLS:
        assert ms.stop_min_pct(sym, a) == ms.stop_min_pct(sym, b)
        assert ms.stop_min_pct(sym) == ms.stop_min_pct(sym, a)


def test_no_bar_at_or_after_the_holdout_boundary_is_loaded():
    """2025-01-01 onward is sealed until a separate authorisation."""
    import datetime as dt
    b = dt.datetime.fromtimestamp(ms.HOLDOUT_START_MS / 1000, dt.timezone.utc)
    assert (b.year, b.month, b.day) == (2025, 1, 1)
    for sym in ms.SYMBOLS:
        df = ms.load_15m(sym)
        assert df["ts"].max() < ms.HOLDOUT_START_MS
        assert "open_synth" not in df.columns
        assert "open" not in df.columns
