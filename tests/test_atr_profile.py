"""Guards for Wilder ATR and for the frozen admissibility rule.

The ATR expectation is hand-computed in the test from Wilder's definition, NOT
checked against another library -- a second implementation agreeing with the
first proves they share an author's assumptions, not that either is right.

The classification guard is a planted mutation: inverting TOO FINE and TOO
COARSE produces a table that reads perfectly sensibly and selects the opposite
end of the candidate set.
"""

import ast
import math

import numpy as np
import pytest

from src.timeframe import atr_profile as ap
from src.timeframe import resample as rs


# ---------------------------------------------------------------------------
# 3. Wilder ATR, hand-computed.
# ---------------------------------------------------------------------------

def test_true_range_definition():
    """TR = max(H-L, |H-Cprev|, |L-Cprev|), and bar 0 has none."""
    high = [10.0, 12.0, 11.0]
    low = [8.0, 9.0, 5.0]
    close = [9.0, 11.0, 6.0]
    tr = ap.true_range(high, low, close)
    assert len(tr) == 2, "bar 0 has no previous close and must yield no TR"
    # Bar 1: H-L = 3, |12-9| = 3, |9-9| = 0  -> 3
    assert tr[0] == pytest.approx(3.0)
    # Bar 2: H-L = 6, |11-11| = 0, |5-11| = 6 -> 6
    assert tr[1] == pytest.approx(6.0)


def test_true_range_picks_the_gap_not_the_bar_range():
    """A gap up: |H - Cprev| dominates H - L. This is the whole point of TR."""
    tr = ap.true_range([10.0, 30.0], [9.0, 29.0], [9.5, 29.5])
    assert tr[0] == pytest.approx(30.0 - 9.5)  # 20.5, not the 1.0 bar range


def test_wilder_atr_matches_a_hand_computed_value():
    """Seed = mean of the first 14 TRs, then ATR_i = (ATR_prev*13 + TR_i)/14.

    Fifteen true ranges: fourteen 1.0s then a single 15.0. The seed is 1.0 by
    inspection, and the next step is (1.0*13 + 15.0)/14 = 28/14 = 2.0 exactly.
    Chosen so the arithmetic is checkable without a calculator.
    """
    tr = np.array([1.0] * 14 + [15.0])
    atr = ap.wilder_atr(tr, period=14)
    assert math.isnan(atr[12])
    assert atr[13] == pytest.approx(1.0, rel=1e-15)
    assert atr[14] == pytest.approx(2.0, rel=1e-15)


def test_wilder_atr_second_hand_computed_case():
    """Non-uniform seed: mean(1..14) = 7.5, then (7.5*13 + 105)/14 = 14.464285..."""
    tr = np.array([float(i) for i in range(1, 15)] + [105.0])
    atr = ap.wilder_atr(tr, period=14)
    assert atr[13] == pytest.approx(7.5, rel=1e-15)
    assert atr[14] == pytest.approx((7.5 * 13 + 105.0) / 14.0, rel=1e-15)


def test_wilder_is_not_a_simple_moving_average():
    """A guard against silently swapping the recursion for a rolling mean."""
    tr = np.array([1.0] * 14 + [15.0])
    atr = ap.wilder_atr(tr, period=14)
    sma = float(np.mean(tr[1:15]))  # 2.0 as it happens -- so check the NEXT step
    tr2 = np.append(tr, 1.0)
    atr2 = ap.wilder_atr(tr2, period=14)
    assert atr2[15] == pytest.approx((2.0 * 13 + 1.0) / 14.0, rel=1e-12)
    assert atr2[15] != pytest.approx(float(np.mean(tr2[2:16])), rel=1e-6)
    assert sma == pytest.approx(2.0)


def test_wilder_atr_too_short_returns_all_nan():
    atr = ap.wilder_atr(np.ones(13), period=14)
    assert len(atr) == 13 and np.all(np.isnan(atr))


def test_atr_percent_denominator_is_the_same_bars_close():
    """ATR% = 100 * ATR / close, on the bar the ATR is stated at."""
    import pandas as pd
    n = 400
    bars = pd.DataFrame({
        "ts": [i * 60_000 for i in range(n)],
        "high": [101.0] * n,
        "low": [99.0] * n,
        "close": [100.0] * n,
    })
    pct = ap.atr_percent(bars)
    # Every TR is 2.0 (H-L dominates), so ATR is 2.0 and ATR% is 2.0.
    assert len(pct) == n - 114
    assert pct.to_numpy() == pytest.approx(np.full(n - 114, 2.0), rel=1e-12)


def test_warmup_discard_is_exactly_114_bars():
    """1 (no previous close) + 13 (before the seed lands) + 100 (stabilisation)."""
    import pandas as pd
    assert ap.WARMUP_STABILISATION_BARS == 100
    assert ap.ATR_PERIOD == 14
    for n in (200, 500, 1000):
        bars = pd.DataFrame({
            "ts": [i * 60_000 for i in range(n)],
            "high": [101.0] * n, "low": [99.0] * n, "close": [100.0] * n,
        })
        assert len(ap.atr_percent(bars)) == n - 114
    # The seed's residual weight at 100 bars, which is why 100 was chosen.
    assert (13.0 / 14.0) ** 100 < 1e-3


# ---------------------------------------------------------------------------
# The frozen rule: constants and arithmetic.
# ---------------------------------------------------------------------------

def test_frozen_constants_match_the_pre_registered_rule():
    """docs/handoff/19_timeframe_rule.md, committed alone at 96c96cf."""
    assert ap.COST_FLOOR_PCT == 1.50
    assert (ap.M_MIN, ap.M_MAX) == (1.0, 3.0)
    assert ap.ATR_PERIOD == 14


def test_m_required_is_floor_over_median():
    assert ap.m_required(1.50) == pytest.approx(1.0, rel=1e-15)
    assert ap.m_required(0.75) == pytest.approx(2.0, rel=1e-15)
    assert ap.m_required(0.50) == pytest.approx(3.0, rel=1e-15)
    assert ap.m_required(3.00) == pytest.approx(0.5, rel=1e-15)
    for bad in (0.0, -1.0, float("nan"), float("inf")):
        with pytest.raises(ValueError):
            ap.m_required(bad)


def test_timeframe_admissible_requires_all_three():
    A, F, C = ap.ADMISSIBLE, ap.TOO_FINE, ap.TOO_COARSE
    assert ap.timeframe_admissible([A, A, A])
    assert not ap.timeframe_admissible([A, A, F])
    assert not ap.timeframe_admissible([A, A, C])
    assert not ap.timeframe_admissible([C, A, F])
    assert not ap.timeframe_admissible([])


def test_select_finest_takes_the_first_passing_in_finest_first_order():
    order = rs.TIMEFRAME_ORDER
    assert ap.select_finest({"5m": False, "15m": False, "1h": True,
                             "4h": True, "1d": False}, order) == "1h"
    assert ap.select_finest({"5m": True, "15m": True, "1h": True,
                             "4h": False, "1d": False}, order) == "5m"
    # Nothing admissible returns None -- a finding, never a fallback.
    assert ap.select_finest({tf: False for tf in order}, order) is None


# ---------------------------------------------------------------------------
# 8. PLANTED MUTATION -- the TOO FINE / TOO COARSE inversion.
# ---------------------------------------------------------------------------

def test_classification_direction_is_not_inverted():
    """PLANTED MUTATION GUARD: TOO FINE and TOO COARSE swapped in `classify`.

    THE MUTATION. In `atr_profile.classify`, swap the two returns:

        if m > m_max: return TOO_FINE      ->  return TOO_COARSE
        if m < m_min: return TOO_COARSE    ->  return TOO_FINE

    WHY IT IS EASY TO GET WRONG AND HARD TO SPOT. The mapping runs opposite to
    the intuition the words suggest. A LARGE required multiplier means the
    median bar range is SMALL relative to the 1.50% floor, and small bars are
    what FINE timeframes have -- so large m is TOO FINE. Saying "m is large, so
    we need a lot of ATR, so the timeframe must be too coarse" is the natural
    misreading, and it produces a table where every cell still carries a
    plausible-looking label. The ADMISSIBLE band is symmetric about neither
    end, so the mutation does not change which cells pass -- only which
    direction they fail in, and therefore which end of the candidate set the
    rule points at.

    THE ARITHMETIC. At the 1.50% floor:

        median 0.20% -> m = 7.5  -> TOO FINE   (5m territory)
        median 0.75% -> m = 2.0  -> ADMISSIBLE
        median 4.00% -> m = 0.375 -> TOO COARSE (1d territory)

    Confirmed to fail under the mutation before being committed.
    """
    # A fine timeframe: tiny bars, huge multiplier required.
    assert ap.classify(ap.m_required(0.20)) == ap.TOO_FINE
    assert ap.classify(7.5) == ap.TOO_FINE
    # A coarse timeframe: bars already exceed the floor, no multiplier needed.
    assert ap.classify(ap.m_required(4.00)) == ap.TOO_COARSE
    assert ap.classify(0.375) == ap.TOO_COARSE
    # In band.
    assert ap.classify(ap.m_required(0.75)) == ap.ADMISSIBLE

    # Stated as the property rather than as three points: a SMALLER median
    # ATR% must never classify as TOO COARSE, and a LARGER one never TOO FINE.
    fine, coarse = ap.classify(ap.m_required(0.10)), ap.classify(ap.m_required(9.0))
    assert fine == ap.TOO_FINE and coarse == ap.TOO_COARSE
    assert fine != coarse

    # Monotone: as median ATR% rises, the mark walks FINE -> ADMISSIBLE -> COARSE
    # and never back. An inversion reverses this sequence.
    seen = [ap.classify(ap.m_required(med))
            for med in (0.10, 0.30, 0.50, 0.75, 1.50, 2.00, 4.00, 9.00)]
    assert seen[0] == ap.TOO_FINE
    assert seen[-1] == ap.TOO_COARSE
    assert seen.index(ap.ADMISSIBLE) < seen.index(ap.TOO_COARSE)
    assert seen == [ap.TOO_FINE, ap.TOO_FINE, ap.ADMISSIBLE, ap.ADMISSIBLE,
                    ap.ADMISSIBLE, ap.TOO_COARSE, ap.TOO_COARSE, ap.TOO_COARSE]


def test_boundaries_are_inclusive():
    assert ap.classify(1.0) == ap.ADMISSIBLE
    assert ap.classify(3.0) == ap.ADMISSIBLE
    assert ap.classify(3.0 + 1e-9) == ap.TOO_FINE
    assert ap.classify(1.0 - 1e-9) == ap.TOO_COARSE
    with pytest.raises(ValueError):
        ap.classify(float("nan"))


# ---------------------------------------------------------------------------
# End to end on the real window.
# ---------------------------------------------------------------------------

def test_profile_cells_are_internally_consistent():
    cells, stats = ap.profile(timeframes=("1h",))
    for sym in rs.SYMBOLS:
        c = cells[(sym, "1h")]
        assert c["n_bars"] > 0
        assert c["p10"] <= c["p25"] <= c["p50"] <= c["p75"] <= c["p90"]
        assert c["m_required"] == pytest.approx(ap.COST_FLOOR_PCT / c["p50"],
                                                rel=1e-12)
        assert c["mark"] == ap.classify(c["m_required"])
        # A wider bar needs a smaller multiplier, so P75 needs less than P25.
        assert c["m_at_p75"] < c["m_required"] < c["m_at_p25"]
        assert stats[(sym, "1h")]["buckets_dropped"] == 0


def test_module_declares_the_rule_is_transcribed_not_authored():
    src = open(ap.__file__).read()
    assert "19_timeframe_rule.md" in src
    assert "96c96cf" in src
