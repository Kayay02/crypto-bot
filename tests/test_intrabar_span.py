"""Guards for the intrabar stop-to-target span measurement.

THREE THINGS CAN BE WRONG HERE WITHOUT ANYTHING RAISING.

THE SPAN MULTIPLIER. The naive 2.5 and the derived ~2.72 are both plausible
numbers that both vary sensibly with the inputs, and using the naive one counts
MORE bars, so the error hides behind a conservative-looking answer. Worse, the
engine's `target_r_multiple` DEFAULTS TO 2.0 while the thesis freezes 1.5:
inheriting the default gives k ~ 3.28, a ~20% wider span, FEWER exceedances and
a materially less alarming verdict. Both forms are pinned, and the default is
pinned as different from the frozen value.

WHICH ATR. Ratio (a) uses the bar's own ATR and ratio (b) the minimum over the
24 bars that could have been the entry. On this data they give OPPOSITE
verdicts. A test asserts (b) <= (a) whenever ATR is non-increasing, and asserts
the lookback excludes the current bar -- an off-by-one there would let a bar set
the stop it is then tested against.

THE FIREWALL BOUNDARY. This is a distribution over BARS and never pairs a bar
with a trade. The module is asserted to contain no identifier or string naming a
touch, a reach, a crossing or an exit reason, and the engine's solver is
asserted to be called only from the synthetic reference path.
"""

import ast
import datetime as dt
import os

import numpy as np
import pandas as pd
import pytest

from src.analysis import intrabar_span as isp
from src.analysis import sweep_population as sp
from src.folds import schedule as sch
from src.timeframe import atr_profile as ap
from src.timeframe import resample as rs


HOUR_MS = 3_600_000
T0 = 1_640_995_200_000  # 2022-01-01T00:00:00Z


@pytest.fixture(scope="module")
def measured():
    return isp.measure()


def _module_ast():
    return ast.parse(open(isp.__file__).read())


def _frame(high, low, close, t0=T0):
    high = np.asarray(high, dtype=float)
    return pd.DataFrame({
        "ts": t0 + np.arange(len(high)) * HOUR_MS,
        "high": high,
        "low": np.asarray(low, dtype=float),
        "close": np.asarray(close, dtype=float),
    })


def _flat(n, high=101.0, low=99.0, close=100.0):
    """`n` bars with a true range of exactly 2.0, so ATR is exactly 2.0.

    Report 21's fixture, reused: the bar range dominates every true range, so
    Wilder's ATR is 2.0 from the seed onward -- exact, not asymptotic.
    """
    return [high] * n, [low] * n, [close] * n


# ---------------------------------------------------------------------------
# 1. THE SPAN MULTIPLIER -- two derivations, and the two forms that are wrong.
# ---------------------------------------------------------------------------

def test_the_frozen_reward_multiple_is_supplied_not_inherited():
    """THE ENGINE DEFAULTS TO 2.0. THE THESIS FREEZES 1.5.

    Amendment 1 §3 records the difference by name. Inheriting the default would
    widen every span by ~20%, count fewer bars and understate the exposure --
    the unsafe direction, and invisible in any output.
    """
    import costs
    engine_default = costs.CostConfig(
        stop_atr_mult=2.25, stop_max_pct=0.035,
        rvol_threshold=1.5, baseline_days=20).target_r_multiple
    assert engine_default == 2.0, "the engine default is Point 4's 1:2"
    assert isp.TARGET_R_MULTIPLE == 1.5, "the thesis freezes 1:1.5"
    assert isp.TARGET_R_MULTIPLE != engine_default

    cfg = isp.cost_config()
    assert cfg.target_r_multiple == 1.5
    assert isp.NAIVE_SPAN_MULT == 2.5 == 1.0 + isp.TARGET_R_MULTIPLE
    assert isp.NAIVE_ATR_THRESHOLD == pytest.approx(5.625)


def test_analytic_and_numeric_span_multipliers_agree(measured):
    """A DISAGREEMENT IS A STOP CONDITION. Asserted at every reference input.

    The numeric form calls the engine's own `position_size` and `solve_target`;
    the analytic form is closed-form from the CostConfig fields. They are two
    independent routes to the same number and they must not merely be close.
    """
    rows = measured["reference"]
    assert len(rows) == len(rs.SYMBOLS) * 2 * len(isp.REFERENCE_INPUTS)
    for row in rows:
        assert row["k_analytic"] == pytest.approx(row["k_numeric"], abs=1e-7), (
            row["symbol"], row["direction"], row["entry"], row["atr"])
        assert row["abs_error"] < 1e-7


def test_the_derived_multiplier_is_NOT_the_naive_one(measured):
    """The two must be distinguishable, or they can be silently conflated.

    The derived span is WIDER, because cost-inclusive sizing solves the target
    net of costs and pushes it further out. A wider span counts FEWER bars, so
    the naive form is the looser bound and the derived one is the honest figure.
    """
    for (symbol, direction), k in measured["quoted_k"].items():
        assert k > isp.NAIVE_SPAN_MULT, (symbol, direction, k)
        assert k == pytest.approx(2.72, abs=0.06), (symbol, direction, k)
        assert abs(k - isp.NAIVE_SPAN_MULT) > 0.15, (
            "derived and naive must not be confusable")


def test_the_multiplier_is_not_constant_in_the_stop_width():
    """k = 2.5 x (1 + cost/s) to first order, so it FALLS as the stop widens.

    Quoting a single k is therefore a reading at a stated width, which is why
    the per-bar sweep evaluates the span at each bar's own width instead.
    """
    cfg = isp.cost_config()
    wide = isp.span_multiplier_analytic(0.05, isp.LONG, cfg, "BTCUSDT")
    narrow = isp.span_multiplier_analytic(0.005, isp.LONG, cfg, "BTCUSDT")
    reference = isp.span_multiplier_analytic(isp.REFERENCE_STOP_FRACTION,
                                             isp.LONG, cfg, "BTCUSDT")
    assert narrow > reference > wide > isp.NAIVE_SPAN_MULT
    assert narrow - wide > 0.5, "the variation must be material, not cosmetic"


def test_long_and_short_spans_differ_because_the_legs_are_not_symmetric():
    """The fee and haircut legs are charged on the stop price, which is below
    entry for a long and above it for a short."""
    cfg = isp.cost_config()
    for symbol in rs.SYMBOLS:
        lo = isp.span_multiplier_analytic(isp.REFERENCE_STOP_FRACTION,
                                          isp.LONG, cfg, symbol)
        sh = isp.span_multiplier_analytic(isp.REFERENCE_STOP_FRACTION,
                                          isp.SHORT, cfg, symbol)
        assert lo != sh
        assert sh > lo, "the short's legs sit on a higher stop price"
        assert abs(sh - lo) < 0.02, "and the asymmetry is small"
    with pytest.raises(ValueError):
        isp.span_multiplier_analytic(0.015, "sideways", cfg, "BTCUSDT")


def test_solus_haircut_widens_its_span():
    """SOL's 10 bps stop haircut against BTC/ETH's 5 bps, showing through."""
    cfg = isp.cost_config()
    k = isp.quoted_multipliers(cfg)
    assert k[("SOLUSDT", isp.LONG)] > k[("BTCUSDT", isp.LONG)]
    assert k[("BTCUSDT", isp.LONG)] == pytest.approx(k[("ETHUSDT", isp.LONG)])


# ---------------------------------------------------------------------------
# 2. SYNTHETIC POSITIVE CONTROL -- exceeding bars by index, not by count.
# ---------------------------------------------------------------------------

def _hand_series(n, wide_at):
    """`n` flat bars with ATR exactly 2.0, widened at the given indices.

    The widened bars keep the same close, so ATR after them is disturbed only
    through the true range -- which is what makes the hand count checkable: the
    controls below place the wide bars far apart and assert the indices.
    """
    h, l, c = _flat(n)
    for i, half in wide_at.items():
        h[i] = 100.0 + half
        l[i] = 100.0 - half
    return _frame(h, l, c)


def test_positive_control_the_exceeding_bars_are_the_hand_chosen_ones():
    """THE CONTROL. Known ranges, known ATR, hand-computed threshold.

    THE CONSTRUCTION. 400 flat bars with ATR exactly 2.0 and range exactly 2.0,
    so no bar exceeds. Three bars are widened to a range of 40.0 -- far above
    any threshold near 6.2 x ATR -- at indices 150, 250 and 350, spaced more than
    24 bars apart so each is the only wide bar in its own lookback window.

    ASSERTED BY INDEX, not by count: a count alone would pass if the detector
    fired on the wrong bars.
    """
    wide = {150: 20.0, 250: 20.0, 350: 20.0}
    frame = isp.bar_frame(_hand_series(400, wide), symbol="BTCUSDT")
    idx = np.nonzero(isp.exceedance(frame)["mask"])[0]
    expected = np.array(sorted(i - isp.WARMUP_BARS for i in wide))
    np.testing.assert_array_equal(idx, expected)
    assert len(idx) == 3

    # And the ratios at those bars are the hand-computed ones.
    #
    # WILDER'S ATR INCLUDES THE CURRENT BAR'S OWN TRUE RANGE, so the own-bar
    # ratio is NOT 40/2: atr = (13 x 2.0 + 40.0)/14 = 66/14, giving
    # 40 / (66/14) = 8.4848... The prior-min ratio divides by the untouched
    # flat ATR of 2.0 and IS 40/2 = 20. The gap between the two is exactly the
    # effect that makes ratio (b) the decision-relevant one.
    own_expected = 40.0 / ((13.0 * 2.0 + 40.0) / 14.0)
    assert own_expected == pytest.approx(8.484848484848, abs=1e-9)

    # EXACT at the FIRST spike, where the prior ATR is exactly 2.0.
    assert frame["ratio_own"].iloc[expected[0]] == pytest.approx(own_expected,
                                                                 rel=1e-12)
    assert frame["ratio_prior_min"].iloc[expected[0]] == pytest.approx(
        20.0, rel=1e-12)

    # NEAR, BUT NOT EXACT, AT THE LATER TWO, AND THE REASON IS RECORDED:
    # Wilder's smoothing decays a spike GEOMETRICALLY and never returns exactly
    # to the pre-spike value -- 100 bars after a spike the residue is still
    # (13/14)^100 = 6.0e-4 of it. Asserting exact equality there would be
    # asserting something false about the estimator.
    for i in expected[1:]:
        assert frame["ratio_own"].iloc[i] == pytest.approx(own_expected,
                                                           rel=1e-3)
        assert frame["ratio_prior_min"].iloc[i] == pytest.approx(20.0,
                                                                 rel=1e-3)
    assert (13.0 / 14.0) ** 100 == pytest.approx(6.03e-4, rel=0.02)


def test_positive_control_the_threshold_is_where_the_arithmetic_says():
    """One bar, swept across the threshold, must flip exactly once.

    ATR is exactly 2.0 and close exactly 100.0, so the stop distance is
    2.25 x 2.0 = 4.5 and the span is k x 4.5 for the k this module derives at
    that stop width. The bar flips from non-exceeding to exceeding as its range
    crosses that span and nowhere else.
    """
    cfg = isp.cost_config()
    s = isp.STOP_ATR_MULT * 2.0 / 100.0
    k = min(isp.span_multiplier_analytic(s, d, cfg, "BTCUSDT")
            for d in (isp.LONG, isp.SHORT))
    span = k * isp.STOP_ATR_MULT * 2.0

    for delta, expected in ((-0.01, 0), (+0.01, 1)):
        half = (span + delta) / 2.0
        frame = isp.bar_frame(_hand_series(300, {200: half}), symbol="BTCUSDT")
        assert isp.exceedance(frame)["n_exceeding"] == expected, (delta, span)


# ---------------------------------------------------------------------------
# 3. SYNTHETIC NEGATIVE CONTROL.
# ---------------------------------------------------------------------------

def test_negative_control_nothing_fires_until_one_bar_crosses():
    """Zero exceedances -- and widening ONE bar past the span gives exactly one.

    A detector that never fires and a detector that is broken look identical
    without the second half of this test.

    THE FIXTURE IS A FLAT SERIES (ATR exactly 2.0, range exactly 2.0) with ONE
    bar placed deliberately JUST BELOW the span. Setting every bar near the span
    would not work and the reason is worth recording: a series whose every range
    is 12 has an ATR of 12, which puts the stop at 2.25 x 12 and the span far
    above 12 again. The span scales with the series' own volatility, so
    "just below the threshold" is only meaningful for a bar that is large
    relative to its own history.
    """
    cfg = isp.cost_config()
    s = isp.STOP_ATR_MULT * 2.0 / 100.0
    k = min(isp.span_multiplier_analytic(s, d, cfg, "BTCUSDT")
            for d in (isp.LONG, isp.SHORT))
    span = k * isp.STOP_ATR_MULT * 2.0
    assert span > 2.0, "the flat bars must sit well below the span"

    below = isp.bar_frame(_hand_series(300, {250: (span - 0.02) / 2.0}),
                          symbol="BTCUSDT")
    assert isp.exceedance(below)["n_exceeding"] == 0

    above = isp.bar_frame(_hand_series(300, {250: (span + 0.02) / 2.0}),
                          symbol="BTCUSDT")
    out = isp.exceedance(above)
    assert out["n_exceeding"] == 1
    assert np.nonzero(out["mask"])[0].tolist() == [250 - isp.WARMUP_BARS]


def test_a_flat_series_produces_no_exceedance_anywhere():
    h, l, c = _flat(400)
    frame = isp.bar_frame(_frame(h, l, c), symbol="SOLUSDT")
    assert isp.exceedance(frame)["n_exceeding"] == 0
    assert frame["ratio_own"].max() == pytest.approx(1.0)


# ---------------------------------------------------------------------------
# 4. ATR PROVENANCE AND THE TWO RATIOS.
# ---------------------------------------------------------------------------

def test_atr_is_the_existing_implementation_exactly():
    """IDENTICAL, not close. Reused from report 21, which reuses report 19's."""
    bars, _ = rs.build("ETHUSDT", isp.TIMEFRAME)
    mine = isp.bar_frame(bars, symbol="ETHUSDT")["atr"].to_numpy(float)
    theirs = sp.atr_series(bars, isp.ATR_PERIOD)[isp.WARMUP_BARS:]
    np.testing.assert_array_equal(mine, theirs)

    tr = ap.true_range(bars["high"].to_numpy(float),
                       bars["low"].to_numpy(float),
                       bars["close"].to_numpy(float))
    direct = np.full(len(bars), np.nan)
    direct[1:] = ap.wilder_atr(tr, period=14)
    np.testing.assert_array_equal(mine, direct[isp.WARMUP_BARS:])


def test_the_prior_min_lookback_excludes_the_current_bar():
    """AN OFF-BY-ONE HERE WOULD LET A BAR SET THE STOP IT IS TESTED AGAINST.

    Asserted on the window contents directly, not on a consequence.
    """
    values = np.arange(1.0, 61.0)
    out = isp.rolling_prior_min(values, window=isp.MAX_HOLD_BARS)
    assert np.isnan(out[:isp.MAX_HOLD_BARS]).all()
    for i in range(isp.MAX_HOLD_BARS, len(values)):
        assert out[i] == values[i - isp.MAX_HOLD_BARS:i].min()
        assert out[i] != values[i - isp.MAX_HOLD_BARS + 1:i + 1].min(), (
            "the fixture must distinguish the two windows")
    assert isp.MAX_HOLD_BARS == 24


def test_ratio_b_is_at_or_below_ratio_a_when_atr_is_non_increasing():
    """(b) divides by the SMALLEST prior ATR, so it is the larger ratio whenever
    ATR has fallen -- and equal when ATR is flat. The direction is the whole
    reason (b) is the decision-relevant one."""
    n = 400
    rng = np.random.default_rng(7)
    # A series whose true range shrinks monotonically: ATR is non-increasing.
    half = np.linspace(20.0, 2.0, n)
    frame = isp.bar_frame(_frame(100.0 + half, 100.0 - half,
                                 np.full(n, 100.0)), symbol="BTCUSDT")
    a = frame["ratio_own"].to_numpy(float)
    b = frame["ratio_prior_min"].to_numpy(float)
    ok = np.isfinite(a) & np.isfinite(b)
    assert np.all(b[ok] <= a[ok] + 1e-9), "falling ATR: prior min >= own ATR"

    # Flat ATR: the two coincide.
    h, l, c = _flat(300)
    flat = isp.bar_frame(_frame(h, l, c), symbol="BTCUSDT")
    fa = flat["ratio_own"].to_numpy(float)
    fb = flat["ratio_prior_min"].to_numpy(float)
    ok = np.isfinite(fa) & np.isfinite(fb)
    np.testing.assert_allclose(fa[ok], fb[ok], rtol=1e-12)
    assert rng is not None


def test_on_real_data_the_two_ratios_give_opposite_verdicts(measured):
    """THE FINDING THAT MAKES THE CHOICE OF RATIO LOAD-BEARING.

    Ratio (a) would put the per-trade bound below the 2.0% criterion on every
    symbol; ratio (b) puts it far above. Asserted so that a future change which
    silently switched ratios would fail here rather than flip a verdict.
    """
    for symbol in rs.SYMBOLS:
        frame = measured["frames"][symbol]
        k = measured["quoted_k"][(symbol, isp.LONG)]
        own = frame["ratio_own"].to_numpy(float)
        own = own[np.isfinite(own)]
        p_own = float((own > k * isp.STOP_ATR_MULT).sum()) / len(own)
        p_prior = measured["symbols"][symbol]["derived"]["fraction"]
        assert p_own < p_prior, symbol
        assert p_own * isp.MAX_HOLD_BARS < 0.02, (
            "ratio (a) would clear the criterion", symbol)
        assert p_prior * isp.MAX_HOLD_BARS > 0.02, (
            "ratio (b) does not", symbol)


# ---------------------------------------------------------------------------
# 5. THE PER-TRADE CONVERSION.
# ---------------------------------------------------------------------------

def test_the_hold_histogram_is_report_24s():
    assert sum(isp.HOLD_HISTOGRAM.values()) == 11_384
    assert set(isp.HOLD_HISTOGRAM) == set(range(17, 25))
    mean = sum(h * n for h, n in isp.HOLD_HISTOGRAM.items()) / 11_384
    assert mean == pytest.approx(20.5129, abs=0.0005)
    assert isp.MIN_HOLD_BARS == 17 and isp.MAX_HOLD_BARS == 24


def test_the_per_trade_conversion_is_a_union_bound():
    out = isp.per_trade_bound(0.01)
    assert out["weighted"] == pytest.approx(0.01 * out["mean_hold_bars"])
    assert out["max_hold"] == pytest.approx(0.01 * 24)
    assert out["max_hold"] > out["weighted"], "max hold is the stricter form"
    assert isp.per_trade_bound(0.0)["weighted"] == 0.0
    with pytest.raises(ValueError):
        isp.per_trade_bound(0.01, histogram={})


def test_the_verdict_is_1m_required(measured):
    """THE DECISION, PINNED. 2.0% is the criterion stated before the run."""
    criterion = 0.05 / 2.5
    assert criterion == pytest.approx(0.02)
    pooled = measured["pooled"]["per_trade"]
    assert pooled["weighted"] > criterion
    assert pooled["max_hold"] > criterion
    for symbol in rs.SYMBOLS:
        assert measured["symbols"][symbol]["per_trade"]["weighted"] > criterion


# ---------------------------------------------------------------------------
# 6. NO 1m DATA, NO SIMULATE, NO TRADE.
# ---------------------------------------------------------------------------

def _imports():
    out = set()
    for node in ast.walk(_module_ast()):
        if isinstance(node, ast.Import):
            for a in node.names:
                out.add(a.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                out.add(node.module)
                for a in node.names:
                    out.add("%s.%s" % (node.module, a.name))
    return out


def _identifiers():
    names = set()
    for node in ast.walk(_module_ast()):
        if isinstance(node, ast.Name):
            names.add(node.id)
        elif isinstance(node, ast.Attribute):
            names.add(node.attr)
        elif isinstance(node, ast.arg):
            names.add(node.arg)
        elif isinstance(node, (ast.FunctionDef, ast.ClassDef)):
            names.add(node.name)
    return names


def test_no_1m_path_is_reachable():
    """THE 1m LOADING PATH CARRIES AN UNCLOSED HOLDOUT SEAL GAP.

    Closing it is a separate, later step; this module reads the derived 1h
    series only.
    """
    for name in _identifiers():
        assert "load_1m" not in name and "_1m" not in name, name
    src = open(isp.__file__).read()
    assert "ohlcv_1m" not in src
    assert "load_1m" not in src
    assert "BAR_1M_MS" not in src
    # `resample.build` is called with the 1h timeframe and nothing else.
    assert isp.TIMEFRAME == "1h"


def test_simulate_and_budget_cost_are_not_reachable():
    banned = ("simulate", "src.engine.simulate", "src.analysis.budget_cost",
              "src.sweep", "src.engine.run")
    for mod in _imports():
        for bad in banned:
            assert not (mod == bad or mod.startswith(bad + ".")), mod
    for name in _identifiers():
        assert "simulate" not in name and "budget_cost" not in name, name


def test_no_bar_is_ever_paired_with_a_trade():
    """THE FIREWALL BOUNDARY OF THIS STEP.

    This is a DISTRIBUTION OVER BARS. Nothing here asks whether a level was
    reached, and nothing constructs a position, entry, exit or trade.
    """
    tree = _module_ast()
    docstrings = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.FunctionDef, ast.ClassDef)):
            d = ast.get_docstring(node, clean=False)
            if d is not None:
                docstrings.add(d)
    blob = set(_identifiers())
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            if node.value not in docstrings:
                blob.add(node.value)
    text = " ".join(blob).lower()
    for banned in ("hit", "touch", "reached", "crossed", "exit_reason",
                   "was_hit"):
        assert banned not in text, banned


def test_the_engine_solver_is_called_only_from_the_reference_path():
    """`solve_target` and `position_size` NEVER touch a real bar.

    Asserted structurally: the only function whose body names them is
    `reference_span_from_engine`, whose inputs are the hand-chosen synthetic
    pairs. The per-bar sweep uses the closed form.
    """
    callers = set()
    for node in ast.walk(_module_ast()):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for inner in ast.walk(node):
                if (isinstance(inner, ast.Attribute)
                        and isinstance(inner.value, ast.Name)
                        and inner.value.id == "costs"
                        and inner.attr in ("solve_target", "position_size")):
                    callers.add(node.name)
    assert callers == {"reference_span_from_engine"}, callers

    sweep = [n for n in ast.walk(_module_ast())
             if isinstance(n, ast.FunctionDef) and n.name == "bar_frame"][0]
    used = {n.value.id for n in ast.walk(sweep)
            if isinstance(n, ast.Attribute) and isinstance(n.value, ast.Name)}
    assert "costs" not in used


from src.firewall import PERFORMANCE_NAMES  # noqa: E402
"""The canonical twelve-name list, defined once at `src/firewall.py`.

Previously written out in full here. Eighteen copies had drifted into two
different lists; this module now imports the one definition."""

ALLOWED_CONFIG_FIELDS = ("target_r_multiple",)
"""ONE CARVE-OUT, AND IT IS THE ENGINE'S OWN FIELD NAME.

`r_multiple` is banned to stop a TRADE'S R multiple being computed.
`CostConfig.target_r_multiple` is a frozen CONFIGURATION field -- the 1:1.5
reward-to-risk the target is solved against -- and this module must name it,
because inheriting the engine's 2.0 default is precisely the error this step
had to avoid. The blanket substring ban is kept and this single token is
stripped before the check, with a separate assertion below that it appears ONLY
as a config field and never as a computed quantity."""


def test_the_config_field_carve_out_is_used_only_as_a_config_field():
    """`target_r_multiple` may be READ from the config and SET as a keyword.

    It may never be assigned to, which is what a computed R multiple would look
    like. Asserted over the AST rather than the text.
    """
    tree = _module_ast()
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for t in node.targets:
                assert not (isinstance(t, ast.Name)
                            and "r_multiple" in t.id), ast.dump(t)
                assert not (isinstance(t, ast.Attribute)
                            and "r_multiple" in t.attr), ast.dump(t)
    # And the standalone name never appears.
    for name in _identifiers():
        assert name != "r_multiple", name


def test_no_performance_quantity_appears_in_the_module():
    tree = _module_ast()
    docstrings = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.FunctionDef, ast.ClassDef)):
            d = ast.get_docstring(node, clean=False)
            if d is not None:
                docstrings.add(d)
    blob = set(_identifiers())
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            if node.value not in docstrings:
                blob.add(node.value)
    text = " ".join(blob).lower()
    for allowed in ALLOWED_CONFIG_FIELDS:
        text = text.replace(allowed, " ")
    for banned in PERFORMANCE_NAMES:
        assert banned not in text, banned


# ---------------------------------------------------------------------------
# 7. THE HOLDOUT SEAL.
# ---------------------------------------------------------------------------

def test_the_module_defines_no_window_constant():
    assert rs.WINDOW_START == dt.date(2022, 1, 1)
    assert rs.WINDOW_END == dt.date(2024, 12, 31)
    assert rs.ALLOWED_YEARS == (2022, 2023, 2024)
    assigned = set()
    for node in ast.walk(_module_ast()):
        if isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name):
                    assigned.add(t.id)
    assert not {"WINDOW_START", "WINDOW_END", "ALLOWED_YEARS"} & assigned
    assert str(sch.HOLDOUT_TEST_START.year) not in open(isp.__file__).read()


def test_bar_frame_refuses_a_holdout_bar():
    sealed = rs.holdout_start_ms()
    n = 300
    h, l, c = _flat(n)
    bad = _frame(h, l, c, t0=sealed - (n - 5) * HOUR_MS)
    assert int(bad["ts"].max()) >= sealed
    with pytest.raises(rs.HoldoutBreach, match="sealed holdout boundary"):
        isp.bar_frame(bad, symbol="BTCUSDT")


def test_no_measured_bar_reaches_the_holdout(measured):
    sealed = rs.holdout_start_ms()
    for symbol, frame in measured["frames"].items():
        assert len(frame) == 26_190
        assert int(frame["ts"].max()) < sealed, symbol
        last = dt.datetime.fromtimestamp(int(frame["ts"].max()) / 1000,
                                         dt.timezone.utc)
        assert last.year == 2024
    for _, period, lo, hi in measured["windows"]:
        assert hi < sealed, period


# ---------------------------------------------------------------------------
# 8. Shape of the real result.
# ---------------------------------------------------------------------------

def test_the_measurement_is_not_vacuous(measured):
    assert measured["pooled"]["bars"] == 3 * 26_190
    assert measured["pooled"]["derived"]["n_exceeding"] > 0
    for symbol in rs.SYMBOLS:
        d = measured["symbols"][symbol]
        assert d["bars"] == 26_190
        assert d["derived"]["n_exceeding"] > 0
        # More than fifty exceeding bars, so no timestamp list is emitted.
        assert d["exceeding_ts"] is None
        assert d["ratio_prior_min"]["max"] > d["ratio_own"]["max"]


def test_the_naive_threshold_counts_more_bars_than_the_derived_one(measured):
    """The naive span is NARROWER, so it must count MORE bars. If this ever
    inverted, the two thresholds would have been swapped."""
    for symbol in rs.SYMBOLS:
        d = measured["symbols"][symbol]
        assert d["naive"]["n_exceeding"] > d["derived"]["n_exceeding"], symbol
    assert (measured["pooled"]["naive"]["n_exceeding"]
            > measured["pooled"]["derived"]["n_exceeding"])


def test_per_fold_rows_are_complete(measured):
    for symbol in rs.SYMBOLS:
        folds = measured["folds"][symbol]
        assert len(folds) == 18
        assert {f for f, _ in folds} == set(range(1, 10))
        for key, row in folds.items():
            assert row["bars"] > 0
            assert 0 <= row["derived"]["fraction"] <= 1.0


def test_report_exists_and_states_the_decision_rule():
    path = os.path.join(rs.ROOT, "docs", "handoff",
                        "27_point_5_3_0_intrabar_span.md")
    assert os.path.exists(path), path
    text = open(path).read()
    assert "q_max = 0.05 / 2.5 = 2.0% of" in text, "verbatim decision rule"
    assert "1m REQUIRED" in text
    assert "open_synth" in text
    for token in ("2.0%", "5.625", "24"):
        assert token in text, token
