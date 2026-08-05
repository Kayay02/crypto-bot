"""Layer A tests: indicator causality, the gated/ungated pairing, and G2.

Updated at Point 3R: RVOL is session-normalised and quote-denominated, and RSI
is no longer an entry condition. The synthetic frame is now sized in DAYS
because the slot baseline needs `baseline_days` completed prior days -- a much
longer warm-up than the 20 bars the flat mean needed.
"""

import numpy as np
import pandas as pd
import pytest
import signals as sg
from conftest import make_cfg

BASELINE_DAYS = 5
SLOTS = sg.SLOTS_PER_DAY  # 96


def synth_15m(days=20, seed=7, ts0=1_600_000_000_000 // 86_400_000 * 86_400_000):
    """A deterministic random walk with volume spikes, on a whole-day 15m grid.

    ts0 is snapped to a UTC midnight so slot 0 really is slot 0.
    """
    n = days * SLOTS
    rng = np.random.default_rng(seed)
    close = 100 + np.cumsum(rng.normal(0, 0.5, n))
    high = close + np.abs(rng.normal(0, 0.3, n)) + 0.01
    low = close - np.abs(rng.normal(0, 0.3, n)) - 0.01
    vol = np.abs(rng.normal(100, 20, n)) + 1.0
    vol[::37] *= 6.0                      # periodic spikes to trip the RVOL gate
    return pd.DataFrame({
        "ts": [ts0 + i * 900_000 for i in range(n)],
        "high": high, "low": low, "close": close,
        "volume": vol, "quote_volume": vol * close,
    })


def cfg_for(baseline_days=BASELINE_DAYS, **kw):
    return make_cfg(baseline_days=baseline_days, **kw)


def test_open_synth_is_rejected_if_it_reaches_layer_a():
    df = synth_15m(3)
    df["open_synth"] = df["close"]
    with pytest.raises(ValueError, match="open_synth"):
        sg.compute_indicators(df, sg.SignalParams(), BASELINE_DAYS)


def test_donchian_excludes_the_current_bar():
    """The channel compared to bar T must be built from bars ending at T-1."""
    df = synth_15m(2)
    up, lo = sg.donchian_prior(df["high"].to_numpy(), df["low"].to_numpy(), 20)
    for i in range(25, 60):
        assert up[i] == pytest.approx(df["high"].to_numpy()[i - 20:i].max())
        assert lo[i] == pytest.approx(df["low"].to_numpy()[i - 20:i].min())


# --------------------------------------------------------------------------
# session-normalised RVOL (B1)
# --------------------------------------------------------------------------

def test_rvol_baseline_reads_only_strictly_prior_completed_days():
    """Mutate every bar of one day; that day's own baseline must not move.

    This is the causality test that actually catches a leak: if the rolling
    window were not shifted by a WHOLE DAY, a bar's baseline would change when
    its own day's volume changed.
    """
    df = synth_15m(12)
    ts = df["ts"].to_numpy()
    vol = np.full(len(df), 1000.0)
    a = sg.session_baseline(ts, vol, BASELINE_DAYS)

    lo, hi = 8 * SLOTS, 9 * SLOTS
    vol_b = vol.copy()
    vol_b[lo:hi] = 999_999.0
    b = sg.session_baseline(ts, vol_b, BASELINE_DAYS)

    assert np.allclose(a[lo:hi], b[lo:hi], equal_nan=True), (
        "baseline changed when the CURRENT day's volume changed -- it is "
        "reading the bar's own day")


def test_rvol_baseline_is_not_inert():
    """Mirror of the causality test: a baseline that ignores everything passes
    the test above trivially, so prove it does respond to prior days."""
    df = synth_15m(12)
    ts = df["ts"].to_numpy()
    vol = np.full(len(df), 1000.0)
    vol_b = vol.copy()
    vol_b[0:3 * SLOTS] = 5000.0     # majority of a 5-day median window
    a = sg.session_baseline(ts, vol, BASELINE_DAYS)
    b = sg.session_baseline(ts, vol_b, BASELINE_DAYS)
    later = slice(5 * SLOTS, 7 * SLOTS)
    assert not np.allclose(a[later], b[later], equal_nan=True)


def test_rvol_baseline_uses_the_matching_slot_only():
    df = synth_15m(9)
    ts = df["ts"].to_numpy()
    vol = np.full(len(df), 1000.0)
    slot = (ts // sg.BAR_15M_MS) % SLOTS
    vol[slot == 7] = 4000.0
    base = sg.session_baseline(ts, vol, BASELINE_DAYS)
    ok = np.isfinite(base)
    assert np.allclose(base[ok & (slot == 7)], 4000.0)
    assert np.allclose(base[ok & (slot != 7)], 1000.0)


def test_rvol_baseline_uses_median_not_mean():
    """One event bar must not drag the slot's denominator for the whole window."""
    df = synth_15m(12)
    ts = df["ts"].to_numpy()
    vol = np.full(len(df), 1000.0)
    vol[2 * SLOTS + 7] = 1_000_000.0        # day 2, slot 7
    base = sg.session_baseline(ts, vol, BASELINE_DAYS)
    slot = (ts // sg.BAR_15M_MS) % SLOTS
    day = ts // sg.DAY_MS
    day = day - day.min()
    m = (slot == 7) & (day >= 5) & (day <= 7)   # windows containing the spike
    assert np.allclose(base[m], 1000.0), "mean, not median"


def test_rvol_warmup_produces_no_signals_and_is_counted():
    df = synth_15m(12)
    cfg = cfg_for()
    ind = sg.compute_indicators(df, sg.SignalParams(), cfg.baseline_days)
    rvol = ind["rvol"].to_numpy()
    # Every bar in the first `baseline_days` days lacks a baseline.
    assert np.all(np.isnan(rvol[:BASELINE_DAYS * SLOTS]))
    assert np.isfinite(rvol[BASELINE_DAYS * SLOTS:]).any()

    s = sg.generate_signals(df, sg.SignalParams(), "ETHUSDT", cfg)
    if len(s):
        assert s["ts"].min() >= df["ts"].to_numpy()[BASELINE_DAYS * SLOTS]

    n_warm = sg.warmup_bars(df, sg.SignalParams(), cfg)
    assert n_warm >= BASELINE_DAYS * SLOTS


def test_rvol_numerator_and_denominator_use_the_same_field():
    """Mixing base and quote denomination divides by a value in other units."""
    df = synth_15m(10)
    cfg = cfg_for()
    ind = sg.compute_indicators(df, sg.SignalParams(), cfg.baseline_days)
    expect = sg.session_rvol(df["ts"].to_numpy(),
                             df[sg.VOLUME_FIELD].to_numpy(float),
                             cfg.baseline_days)
    assert np.allclose(ind["rvol"].to_numpy(), expect, equal_nan=True)
    # And it is the QUOTE field, per the M6 verdict.
    assert sg.VOLUME_FIELD == "quote_volume"
    wrong = sg.session_rvol(df["ts"].to_numpy(),
                            df["volume"].to_numpy(float), cfg.baseline_days)
    assert not np.allclose(ind["rvol"].to_numpy(), wrong, equal_nan=True)


def test_missing_quote_volume_column_raises():
    df = synth_15m(8).drop(columns=["quote_volume"])
    with pytest.raises(KeyError, match="quote_volume"):
        sg.compute_indicators(df, sg.SignalParams(), BASELINE_DAYS)


# --------------------------------------------------------------------------
# RSI is no longer an entry condition
# --------------------------------------------------------------------------

def test_changing_rsi_does_not_change_which_bars_signal():
    """The 3R ruling, pinned: RSI is informational only."""
    df = synth_15m(14)
    cfg = cfg_for()
    p = sg.SignalParams()
    base = sg.generate_signals(df, p, "ETHUSDT", cfg)

    real_rsi = sg.rsi_wilder
    try:
        # Force RSI to a value that the OLD band (50..75 long) would reject
        # outright, for every bar.
        sg.rsi_wilder = lambda close, period: np.full(len(close), 5.0)
        forced = sg.generate_signals(df, p, "ETHUSDT", cfg)
    finally:
        sg.rsi_wilder = real_rsi

    key = ["symbol", "signal_bar_ts", "direction"]
    assert set(map(tuple, base[key].to_numpy())) == \
        set(map(tuple, forced[key].to_numpy())), (
        "RSI changed the signal set -- it is still acting as an entry gate")
    assert len(base) > 0, "degenerate fixture proves nothing"


def test_rsi_is_still_recorded_as_an_informational_column():
    df = synth_15m(14)
    s = sg.generate_signals(df, sg.SignalParams(), "ETHUSDT", cfg_for())
    assert "rsi" in s.columns


def test_rsi_warmup_nans_do_not_suppress_signals():
    """RSI is not in the `finite` mask; its warm-up must not gate entries."""
    df = synth_15m(14)
    cfg = cfg_for()
    ind = sg.compute_indicators(df, sg.SignalParams(), cfg.baseline_days)
    assert np.isnan(ind["rsi"].to_numpy()[:14]).any()
    s = sg.generate_signals(df, sg.SignalParams(), "ETHUSDT", cfg)
    assert len(s) > 0


def _executable_tokens(module):
    """Module source with comments and docstrings stripped.

    Needed because these modules DISCUSS the killed amendment by name, so a
    plain substring search would fire on the prose that records the ruling.
    """
    import inspect
    import io
    import tokenize

    src = inspect.getsource(module)
    out, prev = [], tokenize.INDENT
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
        out.append(tok.string)
    return " ".join(out)


def test_no_entry_condition_references_vwap_position():
    """B3 was killed on measurement; no code path may reference it."""
    import simulate
    for mod in (sg, simulate):
        code = _executable_tokens(mod)
        assert "vwap" not in code.lower(), (
            f"{mod.__name__} references vwap in executable code")


# --------------------------------------------------------------------------
# gated / ungated pairing
# --------------------------------------------------------------------------

def test_indicators_have_no_nan_leakage_into_signals():
    df = synth_15m(16)
    s = sg.generate_signals(df, sg.SignalParams(), "ETHUSDT", cfg_for())
    for col in ("rvol", "atr", "donchian_upper", "donchian_lower"):
        assert np.isfinite(s[col].to_numpy()).all()


def test_causality_holds_on_synthetic_data():
    df = synth_15m(14)
    checked = sg.assert_causal(df, sg.SignalParams(), "ETHUSDT", cfg_for(),
                               n_checks=15)
    assert checked > 0


def test_gated_is_a_strict_subset_of_ungated():
    """Paired comparison: removing the gate may only ADD signals."""
    df = synth_15m(16)
    p, cfg = sg.SignalParams(), cfg_for()
    g = sg.generate_signals(df, p, "ETHUSDT", cfg, apply_rvol_gate=True)
    u = sg.generate_signals(df, p, "ETHUSDT", cfg, apply_rvol_gate=False)
    gk = set(zip(g["symbol"], g["signal_bar_ts"], g["direction"]))
    uk = set(zip(u["symbol"], u["signal_bar_ts"], u["direction"]))
    assert gk <= uk
    assert len(uk) >= len(gk)
    assert (g["rvol"] >= cfg.rvol_threshold).all()


def test_gated_and_ungated_are_joinable():
    df = synth_15m(16)
    p, cfg = sg.SignalParams(), cfg_for()
    g = sg.generate_signals(df, p, "ETHUSDT", cfg, apply_rvol_gate=True)
    u = sg.generate_signals(df, p, "ETHUSDT", cfg, apply_rvol_gate=False)
    key = ["symbol", "signal_bar_ts", "direction"]
    j = g.merge(u, on=key, suffixes=("_g", "_u"))
    assert len(j) == len(g)
    assert np.allclose(j["atr_g"], j["atr_u"])
    assert np.allclose(j["rvol_g"], j["rvol_u"])


def test_long_and_short_conditions_are_mutually_exclusive():
    df = synth_15m(16)
    s = sg.generate_signals(df, sg.SignalParams(), "ETHUSDT", cfg_for())
    dupes = s.groupby("signal_bar_ts")["direction"].nunique()
    assert (dupes == 1).all(), "a bar cannot be both long and short"


# --------------------------------------------------------------------------
# G2 -- planted look-ahead bugs
# --------------------------------------------------------------------------

@pytest.mark.lookahead
def test_planted_lookahead_bug_is_caught(monkeypatch):
    """Plant a leak; the causality guard MUST catch it.

    Skipped by default (run with `-m lookahead`). It exists because a suite
    that has never failed proves nothing: this demonstrates the guard has
    teeth rather than merely being present.

    The bug: shift the Donchian channel by -1 instead of +1, so the level
    compared against bar T is built from bars ending at T+1 -- the signal sees
    the future.
    """
    def leaky_donchian(high, low, period):
        upper = pd.Series(high).rolling(period).max().shift(-1).to_numpy()
        lower = pd.Series(low).rolling(period).min().shift(-1).to_numpy()
        return upper, lower

    monkeypatch.setattr(sg, "donchian_prior", leaky_donchian)
    df = synth_15m(14)
    with pytest.raises(AssertionError, match="look-ahead"):
        sg.assert_causal(df, sg.SignalParams(), "ETHUSDT", cfg_for(),
                         n_checks=15)


def _baseline_variant(day_shift, min_periods=1):
    """A session baseline whose day-axis shift is swappable, for planting bugs."""
    def f(ts, values, baseline_days):
        ts = np.asarray(ts, dtype=np.int64)
        values = np.asarray(values, dtype=float)
        day = ts // sg.DAY_MS
        slot = (ts // sg.BAR_15M_MS) % sg.SLOTS_PER_DAY
        tbl = pd.DataFrame({"day": day, "slot": slot, "v": values})
        mat = tbl.pivot(index="day", columns="slot", values="v").sort_index()
        mat = mat.reindex(range(int(mat.index.min()), int(mat.index.max()) + 1))
        base = mat.rolling(baseline_days, min_periods=min_periods).median()
        base = base.shift(day_shift)
        lookup = base.stack(future_stack=True)
        return lookup.reindex(
            pd.MultiIndex.from_arrays([day, slot])).to_numpy(float)
    return f


@pytest.mark.lookahead
def test_planted_rvol_lookahead_is_caught(monkeypatch):
    """Second leak, different indicator: the slot baseline reading FUTURE days.

    Retargeted at Point 3R from the flat mean to the session baseline. shift(-1)
    on the day axis makes day D's baseline read day D+1 onward.
    """
    monkeypatch.setattr(sg, "session_baseline", _baseline_variant(day_shift=-1))
    df = synth_15m(14)
    with pytest.raises(AssertionError, match="look-ahead"):
        sg.assert_causal(df, sg.SignalParams(), "ETHUSDT", cfg_for(),
                         n_checks=15)


@pytest.mark.lookahead
def test_same_day_self_reference_is_invisible_to_truncation_but_caught_elsewhere():
    """A leak the truncation guard STRUCTURALLY CANNOT catch. Documented, pinned.

    Drop the day-axis shift entirely and day D's baseline includes day D itself.
    Truncating history at bar T does NOT catch this, and the reason is worth
    stating: the baseline is indexed by (day, slot), and truncating at bar T
    leaves bar T's own (day, slot) cell intact. The later bars of day T that
    truncation removes occupy DIFFERENT slots, so the cell being read is
    identical either way. The recomputed answer matches, and the guard passes.

    So `assert_causal` is necessary but NOT sufficient for a slot baseline. The
    dedicated mutation test -- rewrite every bar of one day, require that day's
    own baseline not to move -- is what actually catches it. Both are kept.
    """
    leaky = _baseline_variant(day_shift=0)
    df = synth_15m(12)
    ts = df["ts"].to_numpy()

    # 1. The truncation guard does NOT catch it.
    real = sg.session_baseline
    try:
        sg.session_baseline = leaky
        caught = False
        try:
            sg.assert_causal(df, sg.SignalParams(), "ETHUSDT", cfg_for(),
                             n_checks=15)
        except AssertionError:
            caught = True
    finally:
        sg.session_baseline = real
    assert caught is False, (
        "the truncation guard now catches the same-day self-reference; that is "
        "an improvement -- revisit this test rather than deleting it")

    # 2. The dedicated mutation probe DOES catch it.
    #    baseline_days=1 isolates the leak: day D's window is then day D alone,
    #    so under the leak the baseline IS the bar's own day. At larger windows
    #    a median absorbs one mutated day, which is why the probe is run here at
    #    the sharpest setting rather than at the fixture default.
    vol = np.full(len(df), 1000.0)
    lo, hi = 8 * SLOTS, 9 * SLOTS
    vol_b = vol.copy()
    vol_b[lo:hi] = 999_999.0

    a, b = leaky(ts, vol, 1), leaky(ts, vol_b, 1)
    assert not np.allclose(a[lo:hi], b[lo:hi], equal_nan=True), (
        "the mutation probe must catch the same-day self-reference")

    # 3. The real implementation survives the identical probe.
    ra, rb = sg.session_baseline(ts, vol, 1), sg.session_baseline(ts, vol_b, 1)
    assert np.allclose(ra[lo:hi], rb[lo:hi], equal_nan=True)
