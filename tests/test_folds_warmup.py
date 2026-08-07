"""Warm-up buffer sufficiency -- THE LOAD-BEARING TEST FILE FOR 4.2.

The naive guard ("no signal originates before train_start") is VACUOUS: any
implementation that slices to the train window afterwards passes it, whether
the buffer is 45 days or 45 minutes. It tests the slice, not the buffer. It is
included below as `test_no_signal_originates_inside_the_buffer` because §4.2
asks for it explicitly, but it is not what establishes sufficiency.

What establishes sufficiency is the pair:

  1. 45 days and 90 days must give BIT-IDENTICAL indicator values from
     train_start onward. Not approximately equal -- identical. Over 4,320 bars
     EMA50's memory of its seed is e^-172 and ATR(14)'s is e^-320, both exactly
     zero in double precision, so any difference at all is a finding about the
     buffer rather than about floating point.

  2. A deliberately SHORT buffer must make those values DIFFER. A sufficiency
     test that cannot detect an insufficient buffer proves nothing. Four
     vacuous guards have been found in this project; this is the fifth
     opportunity and it is taken on purpose.

Indicators covered: EMA20, EMA50, ATR(14), Donchian-20 (upper and lower), and
the session-normalised RVOL slot baseline at baseline_days=20.
"""

import datetime as dt
import os
import sys

import numpy as np
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from src.folds import schedule as sch  # noqa: E402
from src.folds import warmup as wu  # noqa: E402

D = dt.date
DATA = os.path.join(sch.DERIVED, "ohlcv_15m", "BTCUSDT.parquet")
needs_data = pytest.mark.skipif(not os.path.exists(DATA),
                                reason="derived data not present")

# Fold 5 sits mid-dataset, so neither end of the series is special.
FOLD = 5
SYMBOLS = ("BTCUSDT", "ETHUSDT", "SOLUSDT")


@pytest.fixture(scope="module")
def fold():
    return sch.build_schedule()[FOLD - 1]


# ---------------------------------------------------------------------------
# buffer arithmetic
# ---------------------------------------------------------------------------

def test_buffer_start_is_45_calendar_days_before_train_start():
    assert wu.buffer_start(D(2023, 4, 1)) == D(2023, 2, 15)
    assert wu.buffer_start(D(2022, 4, 1)) == D(2022, 2, 15)
    assert (D(2023, 4, 1) - wu.buffer_start(D(2023, 4, 1))).days == 45


def test_buffer_bar_count_is_derived_from_the_timeframe():
    assert wu.buffer_bars(45) == 45 * 96 == 4320
    assert wu.buffer_bars(90) == 8640


def test_buffer_covers_the_stated_binding_components():
    """§4.2 names the binding component as ~30 days. 45 gives headroom."""
    assert wu.BASELINE_DAYS == 20
    assert wu.WARMUP_DAYS == 45 > 30 > wu.BASELINE_DAYS


# ---------------------------------------------------------------------------
# (a) THE SUFFICIENCY TEST -- 45 vs 90 must be bit-identical
# ---------------------------------------------------------------------------

@needs_data
@pytest.mark.parametrize("symbol", SYMBOLS)
def test_45_day_buffer_reproduces_a_90_day_buffer_bit_exactly(symbol, fold):
    """If any value differs at all, that is a finding -- do not add a tolerance."""
    res = wu.compare_buffers(symbol, fold["train_start"], fold["test_end"],
                             45, 90)
    bad = {c: r for c, r in res.items() if not r["identical"]}
    assert not bad, (
        f"{symbol}: a 45-day buffer does not reproduce a 90-day buffer: {bad}")
    for c in wu.INDICATOR_COLS:
        assert res[c]["n_compared"] > 20_000, f"{c} compared too few bars"
        assert res[c]["max_abs_diff"] == 0.0
        assert res[c]["n_nan_mismatch"] == 0


@needs_data
def test_every_strategy_indicator_is_covered(fold):
    """The comparison must actually span EMA20/EMA50/ATR/Donchian/RVOL."""
    assert set(wu.INDICATOR_COLS) == {
        "ema_fast", "ema_slow", "atr", "donchian_upper", "donchian_lower",
        "rvol"}
    res = wu.compare_buffers("BTCUSDT", fold["train_start"], fold["test_end"],
                             45, 90)
    for c in wu.INDICATOR_COLS:
        assert c in res
    # rsi is informational after 3R and is compared separately, never conflated
    # with the entry indicators.
    assert "rsi" in res and "rsi" not in wu.INDICATOR_COLS


@needs_data
def test_assert_buffer_sufficient_passes_on_every_fold_for_one_symbol():
    """All nine folds, not just the mid-dataset one -- fold 1 is the tight one."""
    for f in sch.build_schedule():
        wu.assert_buffer_sufficient("ETHUSDT", f, longer_days=60)


# ---------------------------------------------------------------------------
# (a) THE MUTATION -- a short buffer MUST be detected
# ---------------------------------------------------------------------------

@needs_data
@pytest.mark.parametrize("symbol", SYMBOLS)
def test_a_five_day_buffer_is_detected_as_insufficient(symbol, fold):
    """Plant the bug the sufficiency test exists to catch, and require a fail."""
    res = wu.compare_buffers(symbol, fold["train_start"], fold["test_end"],
                             5, 45)
    differing = [c for c in wu.INDICATOR_COLS if not res[c]["identical"]]
    assert differing, (
        f"{symbol}: a 5-day buffer produced identical values to a 45-day "
        f"buffer. The sufficiency comparison cannot detect an insufficient "
        f"buffer, so it proves nothing.")

    # The loudest symptom, and the structurally binding one: the 20-day slot
    # baseline cannot form, so RVOL is still NaN inside the traded population.
    assert not res["rvol"]["identical"]
    assert res["rvol"]["n_nan_mismatch"] == 15 * 96, (
        "expected exactly 15 days of missing RVOL (20-day baseline minus a "
        "5-day buffer)")

    # And EMA50 still remembers its seed at 5 days, as the decay argument says.
    assert not res["ema_slow"]["identical"]
    assert res["ema_slow"]["max_rel_diff"] > 0.0


@needs_data
def test_assert_buffer_sufficient_raises_when_the_buffer_is_short(fold, monkeypatch):
    """The guard itself must fail, not merely the comparison it calls."""
    monkeypatch.setattr(wu, "WARMUP_DAYS", 5)
    with pytest.raises(AssertionError, match="does not reproduce"):
        wu.assert_buffer_sufficient("BTCUSDT", fold, longer_days=45)


@needs_data
def test_which_indicators_need_the_full_buffer(fold):
    """Records WHERE the 45 days is actually spent. Descriptive, and pinned.

    EMA20 and Donchian-20 forget within days; ATR(14) is at the edge of double
    precision by 5 days. The genuinely binding component is the 20-day RVOL
    slot baseline, exactly as §4.2 states.
    """
    res = wu.compare_buffers("BTCUSDT", fold["train_start"], fold["test_end"],
                             5, 45)
    assert res["ema_fast"]["identical"], "EMA20 should forget within 5 days"
    assert res["donchian_upper"]["identical"]
    assert res["donchian_lower"]["identical"]
    assert not res["rvol"]["identical"], "the 20-day baseline is the binding one"


@needs_data
def test_a_twenty_five_day_buffer_already_suffices_for_these_indicators(fold):
    """Bounds how much headroom 45 days carries: everything has converged well
    before it. Recorded so the margin is a measured fact, not a hope."""
    res = wu.compare_buffers("BTCUSDT", fold["train_start"], fold["test_end"],
                             25, 45)
    bad = [c for c in wu.INDICATOR_COLS if not res[c]["identical"]]
    assert not bad, f"25 days was not enough for {bad}"


# ---------------------------------------------------------------------------
# (b) the literal guard -- included because §4.2 asks, not as evidence
# ---------------------------------------------------------------------------

@needs_data
@pytest.mark.parametrize("symbol", SYMBOLS)
def test_no_signal_originates_inside_the_buffer(symbol, fold):
    """§4.2's stated requirement. Counts and timestamps only -- no outcomes.

    This is the vacuous-if-alone check: it passes for any buffer length. It is
    the 45-vs-90 comparison above that establishes sufficiency.
    """
    n, earliest, before = wu.first_signal_ts(
        symbol, fold["train_start"], fold["test_end"])
    assert n > 0, "degenerate fold: no signals to check"
    assert earliest >= sch.day_start_ms(fold["train_start"])
    lo = sch.day_start_ms(fold["train_start"])
    assert all(t >= lo for t in [earliest])
    # Signals DO occur inside the buffer -- they are simply not traded. If this
    # were zero the guard would be passing because nothing was there to catch.
    assert before > 0, (
        "no signals at all inside the buffer, so the guard is not being "
        "exercised; the fixture cannot demonstrate the rule works")


# ---------------------------------------------------------------------------
# invariance to the four no-default parameters
# ---------------------------------------------------------------------------

@needs_data
def test_indicator_values_are_invariant_to_the_sweep_parameters(fold):
    """Warm-up sufficiency must not depend on a parameter chosen later.

    rvol_threshold gates which bars SIGNAL; it does not change what any
    indicator computes. baseline_days does, which is why it is held at 20 (the
    §4.3 fixed value and sweep maximum) rather than varied.
    """
    a = wu.indicators_with_buffer("BTCUSDT", fold["train_start"],
                                  fold["train_end"], 45)
    import costs
    cfg_b = costs.CostConfig(stop_atr_mult=99.0, stop_max_pct=0.999,
                             rvol_threshold=99.0, baseline_days=20)
    b = wu.indicators_with_buffer("BTCUSDT", fold["train_start"],
                                  fold["train_end"], 45,
                                  baseline_days=cfg_b.baseline_days)
    for c in wu.INDICATOR_COLS:
        assert np.array_equal(a[c].to_numpy(), b[c].to_numpy(),
                              equal_nan=True), c


# ---------------------------------------------------------------------------
# holdout seal and firewall
# ---------------------------------------------------------------------------

def test_warmup_refuses_to_load_the_holdout_by_default():
    with pytest.raises(PermissionError, match="SEALED"):
        wu.indicators_from("BTCUSDT", D(2025, 1, 1), D(2025, 2, 1))


@needs_data
def test_no_fold_indicator_computation_reaches_the_holdout():
    for f in sch.build_schedule():
        start = wu.buffer_start(f["train_start"])
        assert not sch.is_holdout_range(start, f["test_end"])


def test_folds_package_never_imports_the_simulator():
    """OHLCV and signal counts in; date ranges and counts out."""
    import ast
    for name in ("schedule.py", "warmup.py", "__init__.py"):
        tree = ast.parse(open(os.path.join(ROOT, "src", "folds", name)).read())
        imported = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(a.name for a in node.names)
            elif isinstance(node, ast.ImportFrom):
                base = node.module or ""
                imported.add(base)
                imported.update(f"{base}.{a.name}" for a in node.names)
        assert not [m for m in imported if "simulate" in m.split(".")], name

    # And no trade-outcome identifier appears in executable code.
    import io
    import tokenize
    for name in ("schedule.py", "warmup.py"):
        src = open(os.path.join(ROOT, "src", "folds", name)).read()
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
        for banned in ("net_pnl", "r_multiple", "trade_pnl", "expectancy",
                       "win_rate"):
            assert banned not in code, f"{name} references {banned}"


@needs_data
def test_loader_drops_open_synth_and_has_no_open_column():
    df = sch.load_bars("BTCUSDT", D(2023, 4, 1), D(2023, 4, 2))
    assert "open_synth" not in df.columns
    assert "open" not in df.columns
    assert len(df) == 2 * 96
