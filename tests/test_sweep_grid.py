"""Sweep grid: population invariance, m*, the 11 points, the cap, RVOL.

The load-bearing test here is (a): the breakout-bar population must be
INVARIANT to `stop_atr_mult`, `stop_max_pct` and `rvol_threshold`. If it moved
with any of them, the grid would depend on a quantity the grid exists to help
select, and every downstream number would be circular.

The two identity checks -- floor binding is ~50% at m*, cap binding is ~5% at
m*+2.5 -- are not decoration. They are the constructions that justify searching
upward from m* (§4.3) and the Amendment 6 correction (Appendix H). If either
drifts, the population definition or the binding computation is wrong.
"""

import os
import sys

import numpy as np
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from src.folds import schedule as sch  # noqa: E402
from src.sweep import grid as gr  # noqa: E402

DATA = os.path.join(sch.DERIVED, "ohlcv_15m", "BTCUSDT.parquet")
needs_data = pytest.mark.skipif(not os.path.exists(DATA),
                                reason="derived data not present")
SYMBOLS = gr.SYMBOLS


@pytest.fixture(scope="module")
def folds():
    return sch.build_schedule()


@pytest.fixture(scope="module")
def fold(folds):
    return folds[4]                      # fold 5, mid-dataset


# ---------------------------------------------------------------------------
# (a) the population must not move with any swept parameter
# ---------------------------------------------------------------------------

@needs_data
@pytest.mark.parametrize("symbol", SYMBOLS)
def test_breakout_population_is_invariant_to_swept_parameters(symbol, fold):
    """Appendix F.1: breakout bars depend only on FIXED components.

    stop_atr_mult, stop_max_pct and rvol_threshold must not move the set by a
    single bar. Anchoring to a swept parameter would make the grid depend on
    the quantity it exists to help select.
    """
    ind = gr.breakout_frame(symbol, fold["train_start"], fold["train_end"])
    base_lo, base_sh = gr.breakout_masks(ind)
    base_atr = gr.breakout_atr_pct(ind)

    for kw in ({"stop_atr_mult": 99.0}, {"stop_max_pct": 0.999},
               {"rvol_threshold": 99.0},
               {"stop_atr_mult": 0.01, "stop_max_pct": 0.001,
                "rvol_threshold": 0.0}):
        cfg = gr.base_cfg(**kw)
        assert cfg.baseline_days == gr.BASELINE_DAYS
        ind2 = gr.breakout_frame(symbol, fold["train_start"], fold["train_end"],
                                 baseline_days=cfg.baseline_days)
        lo2, sh2 = gr.breakout_masks(ind2)
        assert np.array_equal(base_lo, lo2), kw
        assert np.array_equal(base_sh, sh2), kw
        assert np.array_equal(base_atr, gr.breakout_atr_pct(ind2)), kw


@needs_data
def test_breakout_masks_read_no_rvol_and_no_rsi(fold):
    """Corrupt rvol and rsi outright; the population must not notice."""
    ind = gr.breakout_frame("BTCUSDT", fold["train_start"], fold["train_end"])
    lo, sh = gr.breakout_masks(ind)
    poisoned = ind.copy()
    poisoned["rvol"] = np.nan
    poisoned["rsi"] = -999.0
    lo2, sh2 = gr.breakout_masks(poisoned)
    assert np.array_equal(lo, lo2) and np.array_equal(sh, sh2)
    assert lo.sum() > 0 and sh.sum() > 0, "degenerate fixture proves nothing"


@needs_data
def test_breakout_population_is_a_superset_of_the_gated_one(fold):
    """The gate can only ever remove bars from the breakout set."""
    from src.sweep import prescreen as ps
    ind = gr.breakout_frame("BTCUSDT", fold["train_start"], fold["train_end"])
    n_brk = len(gr.breakout_atr_pct(ind))
    thr, _, _ = gr.rvol_threshold_for_pass_rate(ind, 0.50)
    n_gated = len(ps.gated_atr_pct(ind, thr))
    assert 0 < n_gated < n_brk
    assert abs(n_gated / n_brk - 0.50) < 0.02


# ---------------------------------------------------------------------------
# (b) m* and the 50% identity
# ---------------------------------------------------------------------------

@needs_data
@pytest.mark.parametrize("symbol", SYMBOLS)
def test_floor_binds_on_half_the_breakout_bars_at_m_star(symbol, folds):
    """The construction that justifies searching upward from m* (§4.3).

    floor = m* x median(ATR%), so at multiplier m* the floor binds exactly when
    ATR% < median -- 50% by definition of the median.
    """
    from src.sweep import prescreen as ps
    for f in folds:
        ind = gr.breakout_frame(symbol, f["train_start"], f["train_end"])
        a = gr.breakout_atr_pct(ind)
        m, _ = gr.m_star(symbol, a)
        r = ps.binding_rates(a, m, gr.stop_min_pct(symbol), float("inf"))
        assert abs(r["floor"] - 0.50) < 0.01, (
            f"{symbol} fold {f['fold_id']}: floor binds {r['floor']:.3%} at "
            f"m*, expected ~50%. Either the population definition or the "
            f"binding computation is wrong.")


@needs_data
def test_m_star_uses_the_per_symbol_floor_from_config():
    assert gr.stop_min_pct("BTCUSDT") == pytest.approx(1.020)
    assert gr.stop_min_pct("ETHUSDT") == pytest.approx(1.020)
    assert gr.stop_min_pct("SOLUSDT") == pytest.approx(1.320)


def test_m_star_is_floor_over_median_exactly():
    a = np.array([1.0, 2.0, 3.0, 4.0])          # median 2.5
    m, med = gr.m_star("ETHUSDT", a)
    assert med == 2.5
    assert m == pytest.approx(1.020 / 2.5)


def test_m_star_refuses_degenerate_input():
    with pytest.raises(ValueError, match="cannot derive"):
        gr.m_star("ETHUSDT", np.array([1.0]))
    with pytest.raises(ValueError, match="undefined"):
        gr.m_star("ETHUSDT", np.zeros(10))


# ---------------------------------------------------------------------------
# (d) the grid is exactly 11 points spanning exactly 2.5
# ---------------------------------------------------------------------------

def test_grid_is_eleven_points_spanning_two_and_a_half():
    for m in (0.5, 1.0, 2.2367, 4.75):
        g = gr.multiplier_grid(m)
        assert len(g) == 11
        assert g[0] == pytest.approx(m)
        assert g[-1] == pytest.approx(m + 2.5)
        assert g[-1] - g[0] == pytest.approx(2.5)
        steps = np.diff(g)
        assert np.allclose(steps, 0.25)


@needs_data
@pytest.mark.parametrize("symbol", SYMBOLS)
def test_grid_is_eleven_points_on_every_fold(symbol, folds):
    for f in folds:
        cell = gr.fold_symbol_grid(symbol, f)
        g = cell["multipliers"]
        assert len(g) == gr.GRID_POINTS == 11
        assert g[-1] - g[0] == pytest.approx(2.5)
        assert g[0] == pytest.approx(cell["m_star"])


def test_the_range_constants_are_the_pre_registered_ones():
    """§4.3: the range is NOT extended for any reason."""
    assert (gr.GRID_OFFSET_MIN, gr.GRID_OFFSET_MAX) == (0.0, 2.5)
    assert gr.GRID_STEP == 0.25 and gr.GRID_POINTS == 11
    assert gr.BASELINE_DAYS == 20
    assert gr.A3_MAX_FLOOR_BINDING == 0.20
    assert gr.CAP_PERCENTILE == 95.0


# ---------------------------------------------------------------------------
# (c) the cap: Amendment 6
# ---------------------------------------------------------------------------

@needs_data
@pytest.mark.parametrize("symbol", SYMBOLS)
def test_cap_binds_on_five_percent_at_the_top_grid_point(symbol, folds):
    """Appendix H. The superseded median form would bind on 50% here."""
    from src.sweep import prescreen as ps
    for f in folds:
        ind = gr.breakout_frame(symbol, f["train_start"], f["train_end"])
        a = gr.breakout_atr_pct(ind)
        m, med = gr.m_star(symbol, a)
        cap, p95 = gr.derived_cap(m, a)
        top = m + 2.5
        r = ps.binding_rates(a, top, 0.0, cap)
        assert abs(r["cap"] - 0.05) < 0.01, (
            f"{symbol} fold {f['fold_id']}: cap binds {r['cap']:.3%} at the "
            f"top grid point, expected ~5%")
        # And the defect Amendment 6 corrects is real: the median form binds 50%.
        r_med = ps.binding_rates(a, top, 0.0, top * med)
        assert abs(r_med["cap"] - 0.50) < 0.01


@needs_data
@pytest.mark.parametrize("symbol", SYMBOLS)
def test_cap_binding_is_monotonically_lower_at_lower_multipliers(symbol, fold):
    from src.sweep import prescreen as ps
    ind = gr.breakout_frame(symbol, fold["train_start"], fold["train_end"])
    a = gr.breakout_atr_pct(ind)
    m, _ = gr.m_star(symbol, a)
    cap, _ = gr.derived_cap(m, a)
    rates = [ps.binding_rates(a, mult, 0.0, cap)["cap"]
             for mult in gr.multiplier_grid(m)]
    assert all(rates[i] <= rates[i + 1] + 1e-12 for i in range(len(rates) - 1))
    assert rates[0] < rates[-1], "cap binding should rise with the multiplier"


def test_derived_cap_is_the_p95_form_not_the_median_form():
    a = np.concatenate([np.full(95, 1.0), np.full(5, 10.0)])   # P95 = 1.0
    cap, p95 = gr.derived_cap(2.0, a)
    assert p95 == pytest.approx(np.percentile(a, 95))
    assert cap == pytest.approx((2.0 + 2.5) * p95)
    assert cap != pytest.approx((2.0 + 2.5) * np.median(a))


# ---------------------------------------------------------------------------
# (e) RVOL thresholds hit their target pass rates
# ---------------------------------------------------------------------------

@needs_data
@pytest.mark.parametrize("symbol", SYMBOLS)
def test_rvol_thresholds_hit_their_targets(symbol, folds):
    for f in folds:
        cell = gr.fold_symbol_grid(symbol, f)
        for t in gr.RVOL_TARGETS:
            got = cell["rvol_thresholds"][t]["realised_pass_rate"]
            assert abs(got - t) < 0.01, (
                f"{symbol} fold {f['fold_id']} target {t}: realised {got:.4f}")


@needs_data
def test_rvol_thresholds_are_ordered(fold):
    """A 30% pass rate needs a HIGHER threshold than a 70% pass rate."""
    for s in SYMBOLS:
        cell = gr.fold_symbol_grid(s, fold)
        t = cell["rvol_thresholds"]
        assert t[0.30]["threshold"] > t[0.50]["threshold"] > t[0.70]["threshold"]


def test_baseline_days_is_fixed_at_twenty_and_not_swept():
    """§4.3: zero grid resolution is spent on baseline_days."""
    assert gr.BASELINE_DAYS == 20
    assert gr.base_cfg().baseline_days == 20


# ---------------------------------------------------------------------------
# (g) causality -- training data only
# ---------------------------------------------------------------------------

@needs_data
@pytest.mark.parametrize("symbol", SYMBOLS)
def test_derived_quantities_use_training_data_only(symbol, fold):
    """Recompute with the test period truncated away; require identity.

    Every selected parameter must be a function of the training fold alone. If
    a test-period bar reached m*, the cap or an RVOL threshold, the sweep would
    be selecting on data it is later evaluated against.
    """
    full = gr.fold_symbol_grid(symbol, fold)

    # A fold whose data simply stops at train_end: nothing later exists to leak.
    truncated_fold = dict(fold)
    truncated_fold["test_start"] = fold["train_end"]
    truncated_fold["test_end"] = fold["train_end"]
    trunc = gr.fold_symbol_grid(symbol, truncated_fold)

    for k in ("m_star", "median_atr_pct", "p95_atr_pct", "stop_max_pct",
              "stop_min_pct", "n_breakout_bars"):
        assert full[k] == trunc[k], f"{k} moved when the test period was removed"
    assert full["multipliers"] == trunc["multipliers"]
    for t in gr.RVOL_TARGETS:
        assert (full["rvol_thresholds"][t]["threshold"]
                == trunc["rvol_thresholds"][t]["threshold"])


@needs_data
def test_indicators_start_at_the_buffer_not_at_train_start(fold):
    """§4.2: warm-up is drawn from data PRECEDING the fold."""
    ind = gr.breakout_frame("BTCUSDT", fold["train_start"], fold["train_end"])
    assert ind["ts"].min() == sch.day_start_ms(fold["train_start"])
    # RVOL is populated from the very first training bar, which it could not be
    # if computation had started at train_start (a 20-day baseline needs 20
    # prior days).
    assert np.isfinite(ind["rvol"].to_numpy(float)[0])


# ---------------------------------------------------------------------------
# (h)/(i) firewall and holdout
# ---------------------------------------------------------------------------

def test_sweep_package_never_imports_the_simulator_or_regime():
    import ast
    for name in ("grid.py", "prescreen.py", "__init__.py"):
        tree = ast.parse(open(os.path.join(ROOT, "src", "sweep", name)).read())
        imported = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(a.name for a in node.names)
            elif isinstance(node, ast.ImportFrom):
                base = node.module or ""
                imported.add(base)
                imported.update(f"{base}.{a.name}" for a in node.names)
        for banned in ("simulate", "regime"):
            hits = [m for m in imported if banned in m.split(".")]
            assert not hits, f"{name} imports {hits}"


def test_no_outcome_derived_token_in_executable_code():
    import io
    import tokenize
    for name in ("grid.py", "prescreen.py"):
        src = open(os.path.join(ROOT, "src", "sweep", name)).read()
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
                       "win_rate", "sharpe", "equity_curve"):
            assert banned not in code, f"{name} references {banned}"


def test_runtime_does_not_pull_in_simulate_or_regime():
    import subprocess
    code = ("import sys; import src.sweep.prescreen; "
            "bad=[m for m in sys.modules if m=='simulate' "
            "or m.startswith('regime') or m.startswith('src.regime')]; "
            "print(','.join(sorted(bad)))")
    r = subprocess.run([sys.executable, "-c", code], cwd=ROOT,
                       capture_output=True, text=True, timeout=180)
    assert r.returncode == 0, r.stderr
    assert r.stdout.strip() == "", f"pulled in: {r.stdout.strip()}"


@needs_data
def test_no_grid_computation_reaches_the_holdout(folds):
    for f in folds:
        start = sch.day_start_ms(f["train_start"])
        assert not sch.is_holdout_range(f["train_start"], f["test_end"])
        assert start < sch.day_start_ms(sch.HOLDOUT_TEST_START)


def test_holdout_load_still_refuses_by_default():
    import datetime as dt
    with pytest.raises(PermissionError, match="SEALED"):
        gr.breakout_frame("BTCUSDT", dt.date(2025, 1, 1), dt.date(2025, 2, 1))
