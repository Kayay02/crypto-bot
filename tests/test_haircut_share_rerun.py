"""Guards for the non-uniformity re-run, sub-point 4.1a.

THE DISCRIMINATION TEST IS THE ONE THAT MATTERS.
`test_the_flatness_test_TELLS_THE_TWO_DENOMINATIONS_APART` applies the same
flatness predicate to the OLD table and the REVISED one and requires opposite
answers. A flatness test that returned False on everything would report the
re-denomination as a success whatever happened, so it is shown to return True on
the case that actually is flat.

THE THRESHOLD IS NOT RETUNED. `haircut_share.threshold_verdict` is imported and
called, not restated, so the two verdicts are comparable by construction.

ALL SOURCE-TEXT CHECKS RUN OVER EXECUTABLE TOKENS, per the standing rule at
`docs/design/04_1a_denomination_amendment_1.md` §7.
"""

import ast
import io
import os
import sys
import tokenize

import numpy as np
import pandas as pd
import pytest

from src.analysis import haircut_floor_curve as hfc
from src.analysis import haircut_share as hs
from src.analysis import haircut_share_rerun as hr
from src.timeframe import resample as rs

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src", "engine"))

from src.analysis import exposure_profile as ep  # noqa: E402

LONG, SHORT = hr.LONG, hr.SHORT


@pytest.fixture(scope="module")
def cfg():
    return ep.cost_config()


@pytest.fixture(scope="module")
def table(cfg):
    return hr.measurement_table(cfg)


@pytest.fixture(scope="module")
def old_table(cfg):
    """The ORIGINAL run's table, under the old denomination."""
    return hs.decomposition_table(cfg)


def _module_ast():
    return ast.parse(open(hr.__file__).read())


def _code_text():
    out, prev = [], tokenize.INDENT
    for tok in tokenize.generate_tokens(
            io.StringIO(open(hr.__file__).read()).readline):
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


# ---------------------------------------------------------------------------
# 1. THE PROTECTED QUANTITY -- SYNTHETIC POSITIVE CONTROL, HAND-COMPUTED.
# ---------------------------------------------------------------------------

def test_POSITIVE_CONTROL_the_protected_quantity_hand_computed(cfg):
    """HAND-COMPUTED FROM THE RATES, INDEPENDENTLY OF THE MODULE.

    At the revised floor the unvalidated sum over the stop distance IS the
    tolerance, by construction, so the share of the RISK UNIT is

        u = tau / (1 + c/s)

    with `c/s` the FULL stop-path cost ratio at that width -- the sizing
    denominator is unchanged by the re-denomination. With `e = 0`, width
    `w = a / (tau + a)` and the full cost ratio `(2f + a)/w - (f + a)`:

        BTCUSDT long at tau = 0.030:
            w    = 0.0005 / 0.0305
            c/s  = 0.0017 * (0.0305 / 0.0005) - 0.0011 = 0.1037 - 0.0011
            u    = 0.030 / 1.1026
    """
    f, a = 0.0006, 0.0005
    tau = 0.030
    assert cfg.taker_fee == f
    assert cfg.entry_slippage_bps == 0.0
    assert cfg.haircut_bps("BTCUSDT") / 10_000.0 == a

    w = a / (tau + a)
    cost_ratio = (2 * f + a) / w - (f + a)
    want = tau / (1.0 + cost_ratio)
    assert cost_ratio == pytest.approx(0.1026, abs=1e-12)

    got = hr.measure_cell(tau, cfg, "BTCUSDT", LONG)
    assert got[hr.PROTECTED] == pytest.approx(want, rel=1e-12)
    assert got["floor_fraction"] == pytest.approx(w, rel=1e-12)


def test_every_width_solves_the_constraint_it_was_solved_for(table):
    """The unvalidated sum over the stop distance must equal the tolerance at
    every cell, or the shares are measured at the wrong floor."""
    assert len(table) == len(hr.TAU_GRID) * len(rs.SYMBOLS) * 2
    assert hr.solve_residual(table) < 1e-12, hr.solve_residual(table)


def test_the_decomposition_sums_to_the_total(table):
    assert hr.decomposition_residual(table) < 1e-12


def test_the_total_share_is_still_uniform_but_the_unvalidated_share_is_not(table):
    """The constraint's denominator is unchanged, so the TOTAL cost share of the
    risk unit is not what carries the question -- the unvalidated fraction is."""
    for tau in (0.030, 0.0675, 0.120):
        rows = table[table["tau"] == tau]
        assert rows[hr.PROTECTED].max() > rows[hr.PROTECTED].min()


# ---------------------------------------------------------------------------
# 2. THE DISCRIMINATION TEST.
# ---------------------------------------------------------------------------

def test_the_flatness_test_TELLS_THE_TWO_DENOMINATIONS_APART(table, old_table):
    """THE TEST THAT MAKES THE CENTRAL RESULT MEAN ANYTHING.

    A flatness predicate that returned False on everything would report the
    re-denomination as a success whatever happened. It is therefore required to
    return TRUE on the OLD table -- whose cross-symbol ratio the original run
    found invariant to within 1e-12 -- and FALSE on the revised one.
    """
    for direction in (LONG, SHORT):
        assert hr.ratio_is_flat(old_table, direction) is True, (
            "the old denomination's ratio IS flat; a test that cannot see that "
            "cannot be trusted when it reports the revised one is not")
        assert hr.ratio_is_flat(table, direction) is False


def test_the_old_ratio_is_the_constant_the_original_run_reported(old_table):
    """1.5455, flat to 1e-12. Pinned so a change in the old table is visible."""
    for direction in (LONG, SHORT):
        lo, hi, _ = hr.ratio_span(old_table, direction)
        assert lo == pytest.approx(1.5455, abs=5e-5)
        assert hi - lo < 1e-12


def test_the_revised_ratio_varies_and_rises_with_the_tolerance(table):
    """It is no longer invariant, and the direction of travel is reported rather
    than left to be inferred: tighter tolerance gives the more uniform bound."""
    for direction in (LONG, SHORT):
        lo, hi, travel = hr.ratio_span(table, direction)
        assert travel == "rising"
        assert hi - lo > 1e-6
        assert lo > 1.0, "SOLUSDT still carries the larger share"
        frame = hr.cross_symbol_ratio(table, direction)
        assert frame["ratio"].iloc[0] < frame["ratio"].iloc[-1]
        assert len(frame) == len(hr.TAU_GRID)


# ---------------------------------------------------------------------------
# 3. THE THRESHOLD -- REUSED, NOT RETUNED, AND PROBED BOTH WAYS.
# ---------------------------------------------------------------------------

def test_the_criterion_is_the_committed_one_not_a_restatement():
    """THE SAME FUNCTION OBJECT the original run used. A retuned criterion would
    make the two verdicts incomparable."""
    assert hr.verdict.__module__ == hr.__name__
    code = _code_text()
    assert "threshold_verdict" in code
    # No second copy of the criterion's machinery in this module.
    tree = _module_ast()
    functions = {n.name for n in ast.walk(tree)
                 if isinstance(n, ast.FunctionDef)}
    assert "threshold_verdict" not in functions
    assert hr.PROTECTED is hs.PROTECTED


def _synthetic(spread, sensitivity, taus=(0.03, 0.07, 0.12)):
    rows = []
    for i, tau in enumerate(taus):
        ramp = sensitivity * i / (len(taus) - 1)
        rows.append({"tau": tau, "symbol": "AAA", "direction": LONG,
                     hr.PROTECTED: ramp})
        rows.append({"tau": tau, "symbol": "BBB", "direction": LONG,
                     hr.PROTECTED: ramp + spread})
    return pd.DataFrame(rows)


def test_PROBE_the_criterion_returns_BOTH_verdicts(cfg):
    """Exercised either side of `S_max >= R_min`, through the re-run's own
    entry point, so the wiring is probed and not only the underlying function."""
    fires = hr.verdict(_synthetic(spread=0.10, sensitivity=0.01))
    assert fires["fires"] is True
    assert fires["ratio"] == pytest.approx(10.0)

    quiet = hr.verdict(_synthetic(spread=0.01, sensitivity=0.10))
    assert quiet["fires"] is False
    assert quiet["ratio"] == pytest.approx(0.1)

    at = hr.verdict(_synthetic(spread=0.05, sensitivity=0.05))
    assert at["ratio"] == pytest.approx(1.0)
    assert at["fires"] is True


def test_the_verdict_names_where_its_extremes_sit(table):
    v = hr.verdict(table)
    assert v["s_max_at_tau"] in hr.TAU_GRID
    symbol, direction = v["r_min_cell"]
    assert symbol in rs.SYMBOLS and direction in (LONG, SHORT)
    assert len(v["spreads"]) == len(hr.TAU_GRID)
    assert len(v["ranges"]) == len(rs.SYMBOLS) * 2


# ---------------------------------------------------------------------------
# 4. THE CAP-CLIPPED STRATUM.
# ---------------------------------------------------------------------------

def test_POSITIVE_CONTROL_the_cap_crossings_hand_computed(cfg):
    """HAND-COMPUTED. The width equals the cap when

        long   tau = (a + b) / cap - a        short  tau = (a + b) / cap + a

    BTCUSDT long: 0.0005 / 0.035 - 0.0005. SOLUSDT short: 0.0010 / 0.035 + 0.0010.
    """
    cap = cfg.stop_max_pct
    assert cap == 0.035

    assert hr.cap_crossing_tolerance(cfg, "BTCUSDT", LONG) == pytest.approx(
        0.0005 / 0.035 - 0.0005, rel=1e-12)
    assert hr.cap_crossing_tolerance(cfg, "BTCUSDT", SHORT) == pytest.approx(
        0.0005 / 0.035 + 0.0005, rel=1e-12)
    assert hr.cap_crossing_tolerance(cfg, "SOLUSDT", LONG) == pytest.approx(
        0.0010 / 0.035 - 0.0010, rel=1e-12)
    assert hr.cap_crossing_tolerance(cfg, "SOLUSDT", SHORT) == pytest.approx(
        0.0010 / 0.035 + 0.0010, rel=1e-12)

    # And the crossing really is where the width equals the cap.
    for symbol in rs.SYMBOLS:
        for direction in (LONG, SHORT):
            crossing = hr.cap_crossing_tolerance(cfg, symbol, direction)
            at = hfc.required_floor_fraction(crossing, cfg, symbol, direction)
            assert at == pytest.approx(cap, rel=1e-12)
            just_below = hfc.required_floor_fraction(crossing * 0.99, cfg,
                                                     symbol, direction)
            assert just_below > cap


def test_the_cap_clipped_stratum_is_EMPTY_ON_THE_GRID_and_why(cfg, table):
    """ZERO -- AND BY CONSTRUCTION OF THE GRID, NOT BECAUSE IT CANNOT HAPPEN.

    Report 33 §4 chose the grid's lower bound so every cell is satisfiable
    within the cap. Below the grid the stratum is non-empty, which is asserted
    here so the zero is not read as impossibility.
    """
    per_cell, total = hr.cap_clipped_count(table)
    assert total == 0
    assert (per_cell["exceeds_cap"] == 0).all()

    # Every crossing sits below the grid's lower bound.
    for symbol in rs.SYMBOLS:
        for direction in (LONG, SHORT):
            assert hr.cap_crossing_tolerance(cfg, symbol,
                                             direction) < hr.TAU_GRID[0]

    # And below the grid it is not empty.
    below = hr.measurement_table(cfg, taus=(0.020,))
    assert int(below["exceeds_cap"].sum()) > 0


# ---------------------------------------------------------------------------
# 5. WHAT THE MODULE MAY NOT DO.
# ---------------------------------------------------------------------------

def test_no_engine_entry_point_is_invoked_and_no_data_is_opened():
    tree = _module_ast()
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imported.add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imported.add(node.module)
    for banned in ("simulate", "portfolio", "src.engine.portfolio", "run",
                   "src.sweep", "src.regime", "pyarrow", "glob"):
        assert banned not in imported, banned

    called = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                called.add(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                called.add(node.func.attr)
    for banned in ("run_backtest", "read_parquet", "read_table", "load_1m",
                   "load_bars", "build", "open"):
        assert banned not in called, banned

    code = _code_text()
    assert "exit_reason" not in code
    assert "data/" not in code
    assert "ohlcv" not in code


def test_the_cost_algebra_is_not_reimplemented():
    """The unvalidated sum comes from the engine by difference; the width comes
    from report 33's verified closed form."""
    code = _code_text()
    assert "per_unit_denominator" in code
    assert "required_floor_fraction" in code
    assert "taker_fee" not in code
    assert "move + entry" not in code


def test_no_tolerance_value_is_selected(cfg):
    tree = _module_ast()
    assigned = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    assigned.add(target.id)
    for banned in ("CHOSEN_TAU", "SELECTED_TOLERANCE", "COST_TOLERANCE_R",
                   "RECOMMENDED_FLOOR"):
        assert banned not in assigned, banned
    assert hr.TAU_GRID is hfc.TAU_GRID


from src.firewall import PERFORMANCE_NAMES  # noqa: E402
"""The canonical twelve-name list, defined once at `src/firewall.py`.

Previously written out in full here. Eighteen copies had drifted into two
different lists; this module now imports the one definition."""


def test_the_twelve_name_firewall_is_armed_over_the_module():
    tree = _module_ast()
    docs = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef,
                             ast.ClassDef)):
            doc = ast.get_docstring(node, clean=False)
            if doc is not None:
                docs.add(doc)
        body = getattr(node, "body", None)
        if isinstance(body, list):
            for stmt in body:
                if (isinstance(stmt, ast.Expr)
                        and isinstance(stmt.value, ast.Constant)
                        and isinstance(stmt.value.value, str)):
                    docs.add(stmt.value.value)
    blob = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            blob.add(node.id)
        elif isinstance(node, ast.Attribute):
            blob.add(node.attr)
        elif isinstance(node, (ast.FunctionDef, ast.ClassDef)):
            blob.add(node.name)
        elif isinstance(node, ast.Constant) and isinstance(node.value, str):
            if node.value not in docs:
                blob.add(node.value)
    text = " ".join(blob).lower()
    for banned in PERFORMANCE_NAMES:
        assert banned not in text, banned
