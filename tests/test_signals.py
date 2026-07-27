"""Layer A tests: indicator causality, the gated/ungated pairing, and G2."""

import numpy as np
import pandas as pd
import pytest
import signals as sg


def synth_15m(n=400, seed=7):
    """A deterministic random walk with volume spikes, on 15m boundaries."""
    rng = np.random.default_rng(seed)
    close = 100 + np.cumsum(rng.normal(0, 0.5, n))
    high = close + np.abs(rng.normal(0, 0.3, n))
    low = close - np.abs(rng.normal(0, 0.3, n))
    vol = np.abs(rng.normal(100, 20, n))
    vol[::37] *= 6.0                      # periodic spikes to trip the RVOL gate
    return pd.DataFrame({
        "ts": [1_600_000_000_000 + i * 900_000 for i in range(n)],
        "high": high, "low": low, "close": close,
        "volume": vol, "quote_volume": vol * close,
    })


def test_open_synth_is_rejected_if_it_reaches_layer_a():
    df = synth_15m(60)
    df["open_synth"] = df["close"]
    with pytest.raises(ValueError, match="open_synth"):
        sg.compute_indicators(df, sg.SignalParams())


def test_donchian_excludes_the_current_bar():
    """The channel compared to bar T must be built from bars ending at T-1."""
    df = synth_15m(60)
    up, lo = sg.donchian_prior(df["high"].to_numpy(), df["low"].to_numpy(), 20)
    for i in range(25, 60):
        assert up[i] == pytest.approx(df["high"].to_numpy()[i - 20:i].max())
        assert lo[i] == pytest.approx(df["low"].to_numpy()[i - 20:i].min())


def test_rvol_denominator_excludes_the_current_bar():
    """Including the signal bar would damp the very spike the gate detects."""
    df = synth_15m(60)
    r = sg.rvol_prior(df["volume"].to_numpy(), 20)
    v = df["volume"].to_numpy()
    for i in range(25, 60):
        assert r[i] == pytest.approx(v[i] / v[i - 20:i].mean())


def test_indicators_have_no_nan_leakage_into_signals():
    df = synth_15m(300)
    s = sg.generate_signals(df, sg.SignalParams(), "ETHUSDT")
    for col in ("rsi", "rvol", "atr", "donchian_upper", "donchian_lower"):
        assert np.isfinite(s[col].to_numpy()).all()


def test_causality_holds_on_synthetic_data():
    df = synth_15m(400)
    checked = sg.assert_causal(df, sg.SignalParams(), "ETHUSDT", n_checks=20)
    assert checked > 0


def test_gated_is_a_strict_subset_of_ungated():
    """Paired comparison: removing the gate may only ADD signals."""
    df = synth_15m(400)
    p = sg.SignalParams()
    g = sg.generate_signals(df, p, "ETHUSDT", apply_rvol_gate=True)
    u = sg.generate_signals(df, p, "ETHUSDT", apply_rvol_gate=False)
    gk = set(zip(g["symbol"], g["signal_bar_ts"], g["direction"]))
    uk = set(zip(u["symbol"], u["signal_bar_ts"], u["direction"]))
    assert gk <= uk
    assert len(uk) >= len(gk)
    # And every gated signal genuinely cleared the gate.
    assert (g["rvol"] >= p.rvol_min).all()


def test_gated_and_ungated_are_joinable():
    df = synth_15m(400)
    p = sg.SignalParams()
    g = sg.generate_signals(df, p, "ETHUSDT", apply_rvol_gate=True)
    u = sg.generate_signals(df, p, "ETHUSDT", apply_rvol_gate=False)
    key = ["symbol", "signal_bar_ts", "direction"]
    j = g.merge(u, on=key, suffixes=("_g", "_u"))
    assert len(j) == len(g)
    # Same bar -> identical indicator values in both variants.
    assert np.allclose(j["atr_g"], j["atr_u"])
    assert np.allclose(j["rsi_g"], j["rsi_u"])


def test_long_and_short_conditions_are_mutually_exclusive():
    df = synth_15m(400)
    s = sg.generate_signals(df, sg.SignalParams(), "ETHUSDT")
    dupes = s.groupby("signal_bar_ts")["direction"].nunique()
    assert (dupes == 1).all(), "a bar cannot be both long and short"


# --------------------------------------------------------------------------
# G2 -- planted look-ahead bug
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
    df = synth_15m(400)
    with pytest.raises(AssertionError, match="look-ahead"):
        sg.assert_causal(df, sg.SignalParams(), "ETHUSDT", n_checks=20)


@pytest.mark.lookahead
def test_planted_rvol_lookahead_is_caught(monkeypatch):
    """Second leak, different indicator: RVOL baseline including future bars."""
    def leaky_rvol(volume, window):
        v = pd.Series(volume)
        base = v.rolling(window).mean().shift(-1)
        return (v / base.replace(0.0, np.nan)).to_numpy()

    monkeypatch.setattr(sg, "rvol_prior", leaky_rvol)
    df = synth_15m(400)
    with pytest.raises(AssertionError, match="look-ahead"):
        sg.assert_causal(df, sg.SignalParams(), "ETHUSDT", n_checks=20)
