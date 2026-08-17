"""Guards for report 39 -- candidate stop-cap rules against the committed limbs.

THE DERIVED CAP IS HAND-COMPUTED FROM A FIXTURE whose median and 95th percentile
are both known by construction, so `m_star` and `derived_cap` are checked against
arithmetic rather than against themselves.

THE BARRIER IS PROBED IN THE FIRING DIRECTION.

THE CLIPPED COUNT IS HAND-CHECKED, and the fold-dependence counter is exercised on
a fixture where the three strata are known by construction -- otherwise a counter
returning zeroes everywhere would report determinacy that is not there.
"""

import ast
import os
import sys

import numpy as np
import pandas as pd
import pytest

from src.analysis import cap_candidates as cc
from src.analysis import floor_curve as fc
from src.analysis import stop_cap_audit as sca
from src.sweep import grid as gr
from src.timeframe import resample as rs

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src", "engine"))

import sizing  # noqa: E402

from src.analysis import exposure_profile as ep  # noqa: E402

LONG, SHORT = cc.LONG, cc.SHORT


@pytest.fixture(scope="module")
def cfg():
    return ep.cost_config()


@pytest.fixture(scope="module")
def specs():
    return sizing.load_symbol_specs()


def _module_ast():
    return ast.parse(open(cc.__file__).read())


# ---------------------------------------------------------------------------
# CANDIDATE A. THE DERIVED CAP.
# ---------------------------------------------------------------------------

def test_POSITIVE_CONTROL_the_derived_cap_hand_computed():
    """HAND-COMPUTED FROM A FIXTURE WITH A KNOWN MEDIAN AND PERCENTILE.

    One hundred copies of 0.51 have median 0.51 and 95th percentile 0.51. With
    BTCUSDT's derived cost floor at 1.02 per cent:

        m*  = 1.02 / 0.51                      = 2.0
        cap = (m* + 2.5) x P95 = 4.5 x 0.51    = 2.295 per cent

    The rule and its inputs are `src/sweep/grid.py`'s and are called, not
    restated.
    """
    atr_pct = np.full(100, 0.51)
    assert gr.stop_min_pct("BTCUSDT") == pytest.approx(1.02, rel=1e-12)

    m, median = gr.m_star("BTCUSDT", atr_pct)
    assert median == pytest.approx(0.51, rel=1e-14)
    assert m == pytest.approx(2.0, rel=1e-12)

    cap_pct, p95 = gr.derived_cap(m, atr_pct)
    assert p95 == pytest.approx(0.51, rel=1e-14)
    assert cap_pct == pytest.approx(4.5 * 0.51, rel=1e-12)
    assert cap_pct == pytest.approx(2.295, rel=1e-12)

    # And the offset really is the top grid point, not a separate constant.
    assert gr.CAP_OFFSET == gr.GRID_OFFSET_MAX == 2.5
    assert gr.CAP_PERCENTILE == 95.0


def test_the_rule_is_IMPORTED_not_reimplemented():
    tree = _module_ast()
    functions = {n.name for n in ast.walk(tree)
                 if isinstance(n, ast.FunctionDef)}
    assert "derived_cap" not in functions
    assert "m_star" not in functions
    imported = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.ImportFrom) and n.module:
            for alias in n.names:
                imported.add("%s.%s" % (n.module, alias.name))
    assert "src.sweep.grid" in imported


def test_the_cap_is_returned_as_a_FRACTION_not_a_percent():
    """`grid.atr_pct` and `grid.stop_min_pct` are both in percent, so the rule
    returns percent. A module mixing the two units would place every cap a
    hundredfold wrong and every clipped count at zero."""
    tree = _module_ast()
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == "derived_caps":
            divisors = [n.right.value for n in ast.walk(node)
                        if isinstance(n, ast.BinOp) and isinstance(n.op, ast.Div)
                        and isinstance(n.right, ast.Constant)]
            assert 100.0 in divisors, divisors
            return
    raise AssertionError("derived_caps not found")


# ---------------------------------------------------------------------------
# FOLD DEPENDENCE -- LIMB 4's QUANTITY.
# ---------------------------------------------------------------------------

def _fold_fixture():
    """Three BTCUSDT candidates at an entry of 30,000, against two fold caps.

    The predicate is `2.25 x ATR > cap x entry`.

        cap 0.030 -> threshold  900   cap 0.050 -> threshold 1500

        ATR 200 -> 2.25 x ATR =  450   clipped under NEITHER
        ATR 500 -> 2.25 x ATR = 1125   clipped under 0.030 ONLY
        ATR 800 -> 2.25 x ATR = 1800   clipped under BOTH

    EXPECTED: one never, one some-but-not-all, one always.
    """
    return pd.DataFrame({
        "symbol": ["BTCUSDT"] * 3,
        "direction": [LONG] * 3,
        "entry_price": [30_000.0] * 3,
        "atr": [200.0, 500.0, 800.0],
    })


def test_HAND_CHECKED_fold_dependence_counts_all_three_strata():
    """A COUNTER THAT REPORTED ZERO EVERYWHERE WOULD SHOW DETERMINACY THAT IS NOT
    THERE, so the fixture is built so that each stratum has exactly one member."""
    frame = _fold_fixture()
    caps = {("BTCUSDT", 1): 0.030, ("BTCUSDT", 2): 0.050}
    out = cc.fold_dependence(frame, caps, symbols=("BTCUSDT",))
    row = out[out["symbol"] == "BTCUSDT"].iloc[0]
    assert row["n"] == 3
    assert row["n_fold_caps"] == 2
    assert row["clipped_under_none"] == 1
    assert row["clipped_under_some"] == 1
    assert row["clipped_under_all"] == 1
    assert (row["clipped_under_none"] + row["clipped_under_some"]
            + row["clipped_under_all"]) == row["n"]


def test_a_SINGLE_cap_leaves_no_some_but_not_all_stratum():
    """The discrimination check: with one cap the middle stratum must be empty,
    or the counter is finding fold-dependence in a rule that has none."""
    frame = _fold_fixture()
    out = cc.fold_dependence(frame, {("BTCUSDT", 1): 0.030},
                             symbols=("BTCUSDT",))
    row = out[out["symbol"] == "BTCUSDT"].iloc[0]
    assert row["clipped_under_some"] == 0
    assert row["clipped_under_all"] == 2
    assert row["clipped_under_none"] == 1


def test_HAND_CHECKED_clipped_count_on_a_fixture():
    frame = _fold_fixture()
    assert sizing.STOP_ATR_MULT == 2.25
    assert list(sca.clipped_at(frame, 0.030)) == [False, True, True]
    assert list(sca.clipped_at(frame, 0.050)) == [False, False, True]
    assert int(sca.clipped_at(frame, 0.070).sum()) == 0


# ---------------------------------------------------------------------------
# CANDIDATE B. NO CAP.
# ---------------------------------------------------------------------------

def test_widest_atr_width_finds_the_widest_and_reports_its_inputs():
    frame = _fold_fixture()
    out = cc.widest_atr_width(frame, symbols=("BTCUSDT",)).iloc[0]
    assert out["widest_width"] == pytest.approx(2.25 * 800.0 / 30_000.0)
    assert out["at_atr"] == 800.0
    assert out["at_entry_price"] == 30_000.0


def test_viability_is_CALLED_and_the_venue_minimums_can_still_refuse(cfg, specs):
    """Limb 3 must be capable of failing, or passing it means nothing.

    A candidate whose ATR-implied stop is absurdly wide drives the quantity below
    the lot step, and `sizing.viability` must refuse it.
    """
    # One lot of SOLUSDT is 0.1, so the quantity must fall below that. At an
    # entry of 60 the risk unit is about 60 x w, so w must exceed 20/(0.1 x 60)
    # -- about 333 per cent -- and an ATR of 200 gives 2.25 x 200 / 60 = 750.
    absurd = pd.DataFrame({
        "symbol": ["SOLUSDT"], "direction": [LONG],
        "entry_price": [60.0], "atr": [200.0],
    })
    out = cc.viability_under_no_cap(absurd, cfg, specs)
    assert not bool(out["viable"].iloc[0])
    assert out["reason"].iloc[0] == sizing.BELOW_MIN_QTY

    ordinary = pd.DataFrame({
        "symbol": ["SOLUSDT"], "direction": [LONG],
        "entry_price": [60.0], "atr": [1.0],
    })
    assert bool(cc.viability_under_no_cap(ordinary, cfg, specs)
                ["viable"].iloc[0])


def test_the_uncapped_width_is_floored_at_the_derived_cost_floor(cfg, specs):
    """Removal removes the CAP, not the floor. `stop_geometry` floors at
    `stop_min_pct`, and this must do the same or it measures a different rule."""
    tiny = pd.DataFrame({
        "symbol": ["BTCUSDT"], "direction": [LONG],
        "entry_price": [30_000.0], "atr": [1.0],
    })
    out = cc.viability_under_no_cap(tiny, cfg, specs)
    assert out["uncapped_width"].iloc[0] == pytest.approx(
        cfg.stop_min_pct("BTCUSDT"), rel=1e-12)


# ---------------------------------------------------------------------------
# THE ADMITTED DOMAIN.
# ---------------------------------------------------------------------------

def test_the_domain_is_recomputed_and_the_level_is_only_CHECKED(cfg):
    """The level is quoted and its position tested. Nothing re-derives it."""
    assert cc.COMMITTED_LEVEL == 0.10
    at_frozen = cc.domain_under_cap(cfg, 0.035)
    assert at_frozen["domain_lo"] == pytest.approx(0.03554692, abs=5e-9)
    assert at_frozen["level_inside"] is True

    # A wider cap lowers the bound; a narrower one raises it.
    assert cc.domain_under_cap(cfg, 0.070)["domain_lo"] < \
        at_frozen["domain_lo"] < cc.domain_under_cap(cfg, 0.020)["domain_lo"]

    tree = _module_ast()
    functions = {n.name for n in ast.walk(tree)
                 if isinstance(n, ast.FunctionDef)}
    assert "common_achievable_range" not in functions
    assert "required_floor_fraction" not in functions


def test_PER_SYMBOL_domains_take_the_MAX_across_cells(cfg):
    """THE DOMAIN IS AN INTERSECTION. Applying one symbol's cap to all of them
    would understate the bound, so the per-symbol form is checked against the
    single-cap form on a case where they must agree, and against a case where
    they must not."""
    uniform = {s: 0.035 for s in rs.SYMBOLS}
    assert cc.domain_under_per_symbol_caps(cfg, uniform)["domain_lo"] == \
        pytest.approx(cc.domain_under_cap(cfg, 0.035)["domain_lo"], rel=1e-12)

    mixed = {"BTCUSDT": 0.045, "ETHUSDT": 0.049, "SOLUSDT": 0.068}
    per_symbol = cc.domain_under_per_symbol_caps(cfg, mixed)["domain_lo"]

    # IT IS THE MAX OVER EACH CELL AT ITS OWN CAP, which is the property that
    # matters and the one a wrong implementation would break.
    assert per_symbol == pytest.approx(
        max(cc.domain_under_cap(cfg, mixed[s], symbols=(s,))["domain_lo"]
            for s in rs.SYMBOLS), rel=1e-12)

    # AND IT IS NOT ANY ONE SYMBOL'S CAP APPLIED TO ALL. Applying BTCUSDT's
    # narrower cap globally gives a materially higher bound, because every
    # symbol would then be measured at a cap only BTCUSDT carries.
    assert per_symbol < cc.domain_under_cap(cfg, mixed["BTCUSDT"])["domain_lo"]

    # SOLUSDT happens to be the binding cell here, so its cap applied globally
    # COINCIDES -- recorded rather than asserted away, since a test that
    # demanded a difference would be demanding an accident.
    assert per_symbol == pytest.approx(
        cc.domain_under_cap(cfg, mixed["SOLUSDT"])["domain_lo"], rel=1e-12)


# ---------------------------------------------------------------------------
# THE BARRIER, AND WHAT THE MODULE MAY NOT DO.
# ---------------------------------------------------------------------------

def test_BARRIER_PROBE_the_seal_assertion_FIRES_on_a_sealed_path():
    for year in (2025, 2026):
        path = os.path.join("data", "derived", "ohlcv_1m", "symbol=ETHUSDT",
                            "year=%d" % year, "part.parquet")
        with pytest.raises(fc.SealedPathRefused):
            fc.assert_paths_unsealed([path], "cap candidates barrier probe")
    allowed = os.path.join("data", "derived", "ohlcv_1m", "symbol=ETHUSDT",
                           "year=2022", "part.parquet")
    assert fc.assert_paths_unsealed([allowed], "probe") == [allowed]


def test_the_barrier_is_asserted_inside_the_reading_loop():
    for node in ast.walk(_module_ast()):
        if isinstance(node, ast.FunctionDef) and node.name == "derived_caps":
            loops = [n for n in ast.walk(node) if isinstance(n, ast.For)]
            inner = [n for loop in loops for n in ast.walk(loop)
                     if isinstance(n, ast.Call)
                     and isinstance(n.func, ast.Attribute)
                     and n.func.attr == "assert_paths_unsealed"]
            assert inner
            return
    raise AssertionError("derived_caps not found")


def test_the_module_selects_nothing():
    assigned = set()
    for node in ast.walk(_module_ast()):
        if isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name):
                    assigned.add(t.id)
    for banned in ("ADOPTED_CAP", "CHOSEN_CAP", "RECOMMENDED_CAP",
                   "PREFERRED_CANDIDATE", "SELECTED_RULE"):
        assert banned not in assigned, banned


def test_no_execution_entry_point_and_no_outcome_quantity():
    tree = _module_ast()
    called = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            f = node.func
            name = f.attr if isinstance(f, ast.Attribute) else (
                f.id if isinstance(f, ast.Name) else None)
            if name:
                called.add(name)
    for banned in ("size_position", "run_backtest", "simulate", "resolve_exit"):
        assert banned not in called, banned

    from src.firewall import PERFORMANCE_NAMES
    docs = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.FunctionDef, ast.ClassDef)):
            doc = ast.get_docstring(node, clean=False)
            if doc:
                docs.add(doc)
    blob = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            blob.add(node.id)
        elif isinstance(node, ast.Attribute):
            blob.add(node.attr)
        elif isinstance(node, (ast.FunctionDef, ast.ClassDef)):
            blob.add(node.name)
        elif isinstance(node, ast.arg):
            blob.add(node.arg)
        elif isinstance(node, ast.Constant) and isinstance(node.value, str):
            if node.value not in docs:
                blob.add(node.value)
    text = " ".join(blob).lower()
    for banned in PERFORMANCE_NAMES:
        assert banned not in text, banned
