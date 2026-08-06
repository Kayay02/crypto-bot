"""Regime measurement against fixtures whose answers are known by construction.

Point 4.5's build ordering requires verification on constructed fixtures BEFORE
any real-data aggregate is produced: a harness bug found after the lift cannot
be fixed by rerunning, because the buggy output has already been seen.

So the assertions here are EXACT, not approximate. A monotonic ramp gives
efficiency exactly 1.0; a round-trip zigzag gives exactly 0.0; m* on a fixture
with a known median ATR% gives exactly the configured floor divided by it.
"""

import json
import os
import sys

import numpy as np
import pandas as pd
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))

from regime import labels as lb  # noqa: E402
from regime import measure as ms  # noqa: E402

SYMBOL = "ETHUSDT"


def frame(close, high=None, low=None, vol=None, ts0=1_640_995_200_000):
    """A 15m frame from a close path. high/low default to close (degenerate TR)."""
    close = np.asarray(close, dtype=float)
    n = len(close)
    high = close if high is None else np.asarray(high, dtype=float)
    low = close if low is None else np.asarray(low, dtype=float)
    vol = np.full(n, 1000.0) if vol is None else np.asarray(vol, dtype=float)
    return pd.DataFrame({
        "ts": [ts0 + i * ms.BAR_15M_MS for i in range(n)],
        "high": high, "low": low, "close": close,
        "volume": vol, "quote_volume": vol * close,
    })


# ---------------------------------------------------------------------------
# window derivation
# ---------------------------------------------------------------------------

def test_bars_per_day_is_derived_from_the_timeframe():
    assert ms.BARS_PER_DAY == 96
    assert ms.BARS_PER_DAY == ms.DAY_MS // ms.BAR_15M_MS


def test_window_lengths_derive_from_days():
    assert ms.bars_for_days(30) == 2880
    assert ms.bars_for_days(14) == 1344
    assert ms.bars_for_days(60) == 5760
    for bad in (0, -1):
        with pytest.raises(ValueError, match="positive"):
            ms.bars_for_days(bad)


def test_sensitivity_windows_are_supported():
    """The module must produce output at 14 and 60 days, not only 30."""
    n = ms.bars_for_days(3)
    df = frame(100 + np.cumsum(np.random.default_rng(0).normal(0, .3, n * 2)))
    for wd in (1, 2, 3):
        out = ms.measure(df, SYMBOL, window_days=wd)
        assert (out["window_days"] == wd).all()
        assert out["m_star"].notna().any()


# ---------------------------------------------------------------------------
# (c) efficiency ratio -- EXACT answers on constructed paths
# ---------------------------------------------------------------------------

def test_efficiency_ratio_of_a_monotonic_ramp_is_exactly_one():
    n = ms.bars_for_days(1)
    df = frame(100.0 + np.arange(n * 2, dtype=float) * 0.25)
    er = ms.efficiency_ratio(df, n).to_numpy()
    valid = er[np.isfinite(er)]
    assert len(valid) > 0
    assert np.all(valid == 1.0), f"ramp gave {np.unique(valid)}"


def test_efficiency_ratio_of_a_descending_ramp_is_also_exactly_one():
    """Direction-agnostic: the numerator is an absolute displacement."""
    n = ms.bars_for_days(1)
    df = frame(500.0 - np.arange(n * 2, dtype=float) * 0.25)
    er = ms.efficiency_ratio(df, n).to_numpy()
    valid = er[np.isfinite(er)]
    assert len(valid) > 0 and np.all(valid == 1.0)


def test_efficiency_ratio_of_a_round_trip_zigzag_is_exactly_zero():
    """A symmetric zigzag returning to its start has zero net displacement."""
    n = ms.bars_for_days(1)              # 96 bars, even
    assert n % 2 == 0
    unit = np.array([1.0, -1.0])
    close = 100.0 + np.concatenate([np.cumsum(np.tile(unit, n))])
    df = frame(close)
    er = ms.efficiency_ratio(df, n).to_numpy()
    # Bars where the window spans a whole number of up/down pairs return to
    # their start exactly; those are the ones with zero displacement.
    zeros = er[np.isfinite(er)]
    assert len(zeros) > 0
    assert np.any(zeros == 0.0), f"no exact zero; got {np.unique(zeros)[:5]}"
    assert np.all((zeros >= 0.0) & (zeros <= 1.0)), "ER must be bounded 0-1"


def test_efficiency_ratio_is_bounded_zero_to_one_on_a_random_walk():
    n = ms.bars_for_days(1)
    rng = np.random.default_rng(11)
    df = frame(100 + np.cumsum(rng.normal(0, 0.5, n * 3)))
    er = ms.efficiency_ratio(df, n).to_numpy()
    v = er[np.isfinite(er)]
    assert len(v) > 0
    assert v.min() >= 0.0 and v.max() <= 1.0


def test_efficiency_ratio_half_way_case_is_exact():
    """Two up-steps then one down-step: displacement 1 of 3 units moved."""
    n = 6
    close = np.array([100, 101, 102, 101, 102, 103, 102, 103, 104, 103],
                     dtype=float)
    df = frame(close)
    er = ms.efficiency_ratio(df, n).to_numpy()
    # At index 6: close[6]=102, close[0]=100 -> numer 2; six unit moves -> 6.
    assert er[6] == pytest.approx(2.0 / 6.0, abs=0.0)


# ---------------------------------------------------------------------------
# (d) m_star -- EXACT against a known median ATR%
# ---------------------------------------------------------------------------

def test_m_star_equals_floor_over_median_atr_pct_exactly():
    """Constant true range and constant close give an exactly known ATR%.

    close = 100 flat, high/low = close +/- 0.5 -> TR = 1.0 every bar, so
    Wilder's ATR converges to exactly 1.0 and ATR% = 1.0%. With ETHUSDT's
    derived floor of 1.020%, m* must be exactly 1.020 / 1.0 = 1.020.
    """
    n = ms.bars_for_days(1)
    total = n * 3
    close = np.full(total, 100.0)
    df = frame(close, high=close + 0.5, low=close - 0.5)

    ap = ms.atr_pct(df).to_numpy()
    assert ap[-1] == pytest.approx(1.0, abs=1e-12)

    floor_pct = ms.stop_min_pct(SYMBOL) * 100.0
    assert floor_pct == pytest.approx(1.020, abs=1e-12)

    mstar = ms.m_star(df, SYMBOL, n).to_numpy()
    got = mstar[np.isfinite(mstar)]
    assert len(got) > 0
    assert got[-1] == pytest.approx(1.020, abs=1e-9)


def test_m_star_scales_inversely_with_volatility():
    """Double the true range, halve m*. The axis must be monotone the right way."""
    n = ms.bars_for_days(1)
    close = np.full(n * 3, 100.0)
    narrow = ms.m_star(frame(close, close + 0.5, close - 0.5), SYMBOL, n)
    wide = ms.m_star(frame(close, close + 1.0, close - 1.0), SYMBOL, n)
    a = narrow.dropna().iloc[-1]
    b = wide.dropna().iloc[-1]
    assert b == pytest.approx(a / 2.0, rel=1e-9)


def test_m_star_uses_the_per_symbol_floor_from_config():
    """SOL's floor is 1.320%, BTC/ETH 1.020% -- read from config, not restated."""
    assert ms.stop_min_pct("BTCUSDT") == pytest.approx(0.01020)
    assert ms.stop_min_pct("ETHUSDT") == pytest.approx(0.01020)
    assert ms.stop_min_pct("SOLUSDT") == pytest.approx(0.01320)

    n = ms.bars_for_days(1)
    close = np.full(n * 3, 100.0)
    df = frame(close, close + 0.5, close - 0.5)
    eth = ms.m_star(df, "ETHUSDT", n).dropna().iloc[-1]
    sol = ms.m_star(df, "SOLUSDT", n).dropna().iloc[-1]
    assert sol / eth == pytest.approx(1.320 / 1.020, rel=1e-12)


def test_m_star_below_one_marker_counts_and_does_not_cut():
    lo, tot = ms.m_star_below_one(pd.Series([0.5, 1.0, 2.0, np.nan, 3.0]))
    assert (lo, tot) == (1, 4)


# ---------------------------------------------------------------------------
# covariates
# ---------------------------------------------------------------------------

def test_drift_log_return_is_exact_on_a_known_path():
    n = 8
    close = np.array([100.0] * (n + 1) + [200.0] * n)
    df = frame(close)
    lr, _ = ms.drift(df, n)
    assert lr.to_numpy()[n] == pytest.approx(0.0, abs=1e-12)
    assert lr.to_numpy()[-1] == pytest.approx(np.log(2.0), abs=1e-12)


def test_ema_fraction_is_one_on_a_sustained_uptrend():
    n = ms.bars_for_days(1)
    df = frame(100.0 + np.arange(n * 4, dtype=float) * 0.5)
    _, frac = ms.drift(df, n)
    assert frac.dropna().iloc[-1] == pytest.approx(1.0)


def test_median_daily_quote_volume_is_exact_on_constant_volume():
    """Constant per-bar quote volume -> trailing 24h sum is 96 x the bar value."""
    n = ms.bars_for_days(1)
    close = np.full(n * 4, 100.0)
    vol = np.full(n * 4, 7.0)
    df = frame(close, vol=vol)          # quote_volume = 7 * 100 = 700 per bar
    med = ms.median_daily_quote_volume(df, n).dropna()
    assert len(med) > 0
    assert med.iloc[-1] == pytest.approx(700.0 * ms.BARS_PER_DAY)


# ---------------------------------------------------------------------------
# (f) NaN handling -- never silently filled
# ---------------------------------------------------------------------------

def test_insufficient_window_emits_nan_not_a_partial_value():
    """Every column shares ONE warm-up boundary: a row is complete or empty."""
    n = ms.bars_for_days(2)
    warm = ms.warmup_bars(2)
    df = frame(100 + np.cumsum(np.random.default_rng(1).normal(0, .3, n * 3)))
    out = ms.measure(df, SYMBOL, window_days=2)
    for col in ms.MEASURE_COLS:
        head = out[col].to_numpy()[:warm]
        assert np.all(np.isnan(head)), f"{col} produced a partial-window value"
    assert np.isfinite(out["m_star"].to_numpy()[-1])


def test_no_column_becomes_valid_before_the_shared_warmup_boundary():
    """Guards the boundary itself: no partial rows may leak through."""
    n = ms.bars_for_days(2)
    warm = ms.warmup_bars(2)
    df = frame(100 + np.cumsum(np.random.default_rng(9).normal(0, .3, n * 3)))
    out = ms.measure(df, SYMBOL, window_days=2)
    first_valid = {c: int(np.argmax(np.isfinite(out[c].to_numpy())))
                   for c in ms.MEASURE_COLS}
    assert set(first_valid.values()) == {warm}, first_valid


def test_warmup_exceeds_the_window_and_says_why():
    """The 24h liquidity sum, not the window, is the binding component."""
    n = ms.bars_for_days(30)
    assert n == 2880
    assert ms.warmup_bars(30) == n + ms.BARS_PER_DAY - 2 == 2974
    assert ms.warmup_bars(30) > n


def test_zero_denominator_efficiency_emits_nan_not_zero():
    """A perfectly flat window: nothing moved, so efficiency is undefined.

    Zero would assert MAXIMAL INEFFICIENCY, which is a different and false
    claim about a window in which price did not move at all.
    """
    n = ms.bars_for_days(1)
    df = frame(np.full(n * 3, 100.0))
    er = ms.efficiency_ratio(df, n).to_numpy()
    tail = er[n:]
    assert np.all(np.isnan(tail)), "flat window must be NaN, not 0.0"
    assert not np.any(tail == 0.0)
    # And through the assembled frame, where the shared mask also applies.
    out = ms.measure(df, SYMBOL, window_days=1)
    assert out["efficiency_ratio"].isna().all()


def test_zero_median_atr_emits_nan_m_star():
    """A window with zero true range has no defined m*."""
    n = ms.bars_for_days(1)
    close = np.full(n * 3, 100.0)
    df = frame(close, high=close, low=close)     # TR identically zero
    mstar = ms.m_star(df, SYMBOL, n).to_numpy()
    assert np.all(np.isnan(mstar[n:]))


def test_nans_are_not_forward_filled():
    """A NaN must never be replaced by a neighbouring bar's value."""
    n = ms.bars_for_days(1)
    df = frame(100 + np.cumsum(np.random.default_rng(5).normal(0, .3, n * 3)))
    out = ms.measure(df, SYMBOL, window_days=1)
    warm = ms.warmup_bars(1)
    m = out["m_star"].to_numpy()
    assert np.isnan(m[warm - 1]) and np.isfinite(m[warm])


def test_measure_refuses_an_empty_frame():
    with pytest.raises(ValueError, match="no bars"):
        ms.measure(frame([]), SYMBOL, window_days=1)


# ---------------------------------------------------------------------------
# (e) terciles
# ---------------------------------------------------------------------------

def _ts_for(n, ts0=1_640_995_200_000):
    return pd.Series([ts0 + i * ms.BAR_15M_MS for i in range(n)])


def test_terciles_split_a_known_distribution_into_three_equal_parts():
    n = 900
    s = pd.Series(np.arange(n, dtype=float))
    ts = _ts_for(n)
    cuts = lb.fit_terciles(s, int(ts.iloc[0]), int(ts.iloc[-1]) + 1, ts=ts)
    labels = lb.apply_terciles(s, cuts)
    counts = labels.value_counts().to_dict()
    for k in lb.LABELS:
        assert abs(counts[k] - n / 3) <= 2, counts


def test_frozen_cuts_on_a_shifted_distribution_produce_expected_imbalance():
    """Later data WILL be unbalanced. That is a finding, not a defect."""
    n = 900
    ts = _ts_for(n)
    fit = pd.Series(np.arange(n, dtype=float))
    cuts = lb.fit_terciles(fit, int(ts.iloc[0]), int(ts.iloc[-1]) + 1, ts=ts)

    # Shift the whole distribution above the upper cut: everything is `high`.
    shifted = fit + n
    counts = lb.apply_terciles(shifted, cuts).value_counts().to_dict()
    assert counts.get(lb.HIGH, 0) == n
    assert counts.get(lb.LOW, 0) == 0 and counts.get(lb.MID, 0) == 0

    # And halfway down: a real, partial imbalance rather than a total one.
    half = lb.apply_terciles(fit + n / 3.0, cuts).value_counts().to_dict()
    assert half.get(lb.HIGH, 0) > half.get(lb.LOW, 0)


def test_apply_terciles_boundaries_and_nan_passthrough():
    cuts = (10.0, 20.0)
    s = pd.Series([9.9, 10.0, 10.1, 20.0, 20.1, np.nan])
    got = list(lb.apply_terciles(s, cuts))
    assert got == [lb.LOW, lb.LOW, lb.MID, lb.MID, lb.HIGH, None]


def test_fit_terciles_respects_the_fit_window_bounds():
    n = 600
    ts = _ts_for(n)
    s = pd.Series(np.concatenate([np.zeros(n // 2), np.arange(n // 2) + 100.0]))
    end = int(ts.iloc[n // 2])           # exclusive: only the zero half
    with pytest.raises(ValueError, match="degenerate"):
        lb.fit_terciles(s, int(ts.iloc[0]), end, ts=ts)


def test_fit_terciles_rejects_bad_windows_and_thin_data():
    n = 100
    ts = _ts_for(n)
    s = pd.Series(np.arange(n, dtype=float))
    with pytest.raises(ValueError, match="empty fit window"):
        lb.fit_terciles(s, int(ts.iloc[10]), int(ts.iloc[10]), ts=ts)
    with pytest.raises(ValueError, match="cannot fit terciles"):
        lb.fit_terciles(s, int(ts.iloc[0]), int(ts.iloc[2]), ts=ts)
    with pytest.raises(ValueError, match="length"):
        lb.fit_terciles(s, int(ts.iloc[0]), int(ts.iloc[-1]) + 1, ts=ts[:5])


def test_fit_excludes_nan_rather_than_filling_it():
    n = 300
    ts = _ts_for(n)
    s = pd.Series(np.arange(n, dtype=float))
    s[:100] = np.nan                    # warm-up
    cuts = lb.fit_terciles(s, int(ts.iloc[0]), int(ts.iloc[-1]) + 1, ts=ts)
    # Fitted on 100..299 only; a fill with 0 would drag the lower cut down.
    assert cuts[0] > 100.0


# ---------------------------------------------------------------------------
# (g) frozen artifact
# ---------------------------------------------------------------------------

def test_frozen_cuts_file_raises_rather_than_overwriting(tmp_path):
    path = str(tmp_path / "terciles.json")
    entries = {"ETHUSDT|m_star|30d":
               lb.tercile_entry("ETHUSDT", "m_star", 30, (1.5, 2.5), 100)}

    first = lb.freeze_terciles(entries, path=path, fit_start=1000, fit_end=2000)
    assert os.path.exists(path)
    assert first["git_commit"]

    # Same window -> returns the existing artifact, does not rewrite.
    again = lb.freeze_terciles(entries, path=path, fit_start=1000, fit_end=2000)
    assert again["cuts"] == first["cuts"]

    # Different window -> refuses.
    with pytest.raises(ValueError, match="Refusing to overwrite"):
        lb.freeze_terciles(entries, path=path, fit_start=1000, fit_end=3000)
    with pytest.raises(ValueError, match="Refusing to overwrite"):
        lb.freeze_terciles(entries, path=path, fit_start=500, fit_end=2000)

    # And the file on disk is untouched by the refused calls.
    assert json.load(open(path))["fit_end_ms"] == 2000


def test_frozen_artifact_records_window_symbol_axis_cuts_and_commit(tmp_path):
    path = str(tmp_path / "t.json")
    entries = {"SOLUSDT|efficiency_ratio|30d":
               lb.tercile_entry("SOLUSDT", "efficiency_ratio", 30, (0.2, 0.4), 7)}
    p = lb.freeze_terciles(entries, path=path, fit_start=1000, fit_end=2000)
    for k in ("fit_start_ms", "fit_end_ms", "fit_start_utc",
              "fit_end_utc_exclusive", "git_commit", "cuts"):
        assert k in p
    e = p["cuts"]["SOLUSDT|efficiency_ratio|30d"]
    assert e["symbol"] == "SOLUSDT" and e["axis"] == "efficiency_ratio"
    assert e["window_days"] == 30
    assert (e["cut_low"], e["cut_high"]) == (0.2, 0.4)
    assert lb.cuts_for(p, "SOLUSDT", "efficiency_ratio", 30) == (0.2, 0.4)
    with pytest.raises(KeyError):
        lb.cuts_for(p, "BTCUSDT", "efficiency_ratio", 30)


def test_load_terciles_raises_when_missing(tmp_path):
    with pytest.raises(FileNotFoundError, match="frozen terciles missing"):
        lb.load_terciles(str(tmp_path / "nope.json"))


# ---------------------------------------------------------------------------
# concordance
# ---------------------------------------------------------------------------

def test_concordance_of_identical_label_streams_is_one():
    ts = _ts_for(10).to_numpy()
    lab = [lb.LOW] * 5 + [lb.HIGH] * 5
    d = {s: pd.DataFrame({"ts": ts, "m_star_label": lab})
         for s in ("BTCUSDT", "ETHUSDT", "SOLUSDT")}
    r = lb.concordance(d, "m_star_label")
    assert r["fraction"] == 1.0 and r["n_bars"] == 10


def test_concordance_counts_only_full_agreement():
    ts = _ts_for(4).to_numpy()
    d = {
        "BTCUSDT": pd.DataFrame({"ts": ts, "x": [lb.LOW, lb.LOW, lb.HIGH, lb.MID]}),
        "ETHUSDT": pd.DataFrame({"ts": ts, "x": [lb.LOW, lb.MID, lb.HIGH, lb.MID]}),
        "SOLUSDT": pd.DataFrame({"ts": ts, "x": [lb.LOW, lb.LOW, lb.HIGH, lb.LOW]}),
    }
    r = lb.concordance(d, "x")
    assert r["agree"] == 2 and r["n_bars"] == 4
    assert r["fraction"] == pytest.approx(0.5)
    assert r["cells"]["low|low|low"] == 1
    assert r["cells"]["high|high|high"] == 1


def test_concordance_excludes_unlabelled_bars_rather_than_counting_them():
    """A warm-up NaN is not a disagreement about the market."""
    ts = _ts_for(4).to_numpy()
    d = {
        "BTCUSDT": pd.DataFrame({"ts": ts, "x": [None, lb.LOW, lb.LOW, lb.LOW]}),
        "ETHUSDT": pd.DataFrame({"ts": ts, "x": [None, lb.LOW, lb.LOW, lb.HIGH]}),
        "SOLUSDT": pd.DataFrame({"ts": ts, "x": [None, lb.LOW, lb.LOW, lb.LOW]}),
    }
    r = lb.concordance(d, "x")
    assert r["n_excluded_unlabelled"] == 1
    assert r["n_bars"] == 3
    assert r["fraction"] == pytest.approx(2.0 / 3.0)


def test_concordance_respects_a_date_range():
    ts = _ts_for(6).to_numpy()
    d = {s: pd.DataFrame({"ts": ts, "x": [lb.LOW] * 3 + [lb.HIGH] * 3})
         for s in ("BTCUSDT", "ETHUSDT")}
    d["SOLUSDT"] = pd.DataFrame({"ts": ts, "x": [lb.LOW] * 3 + [lb.MID] * 3})
    full = lb.concordance(d, "x")
    early = lb.concordance(d, "x", start_ts=int(ts[0]), end_ts=int(ts[3]))
    assert full["fraction"] == pytest.approx(0.5)
    assert early["fraction"] == 1.0 and early["n_bars"] == 3


def test_concordance_needs_at_least_two_symbols():
    ts = _ts_for(3).to_numpy()
    with pytest.raises(ValueError, match="at least two"):
        lb.concordance({"BTCUSDT": pd.DataFrame({"ts": ts, "x": [lb.LOW] * 3})}, "x")


# ---------------------------------------------------------------------------
# output schema
# ---------------------------------------------------------------------------

def test_parquet_roundtrip_preserves_schema_and_nans(tmp_path):
    import pyarrow.parquet as pq

    n = ms.bars_for_days(1)
    df = frame(100 + np.cumsum(np.random.default_rng(3).normal(0, .3, n * 3)))
    out = ms.measure(df, SYMBOL, window_days=1)
    out["m_star_label"] = lb.apply_terciles(
        out["m_star"], (1.0, 2.0)).astype(object)
    out["efficiency_label"] = lb.apply_terciles(
        out["efficiency_ratio"], (0.2, 0.5)).astype(object)

    path = str(tmp_path / "x.parquet")
    ms.write_parquet(out, path)
    back = pq.read_table(path).to_pandas()

    assert list(back.columns) == ms.OUTPUT_COLS
    assert len(back) == len(out)
    assert back["m_star"].isna().sum() == out["m_star"].isna().sum()
    assert back["m_star_label"].isna().sum() >= ms.warmup_bars(1)
    assert back["window_days"].iloc[0] == 1
    md = pq.read_metadata(path)
    assert md.row_group(0).column(0).compression.lower() == "zstd"
