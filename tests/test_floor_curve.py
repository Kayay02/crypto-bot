"""Guards for the parametric floor derivation, sub-point 4.0 step 3.

THE CLOSED FORM IS NOT TRUSTED, IT IS CHECKED AGAINST THE IMPLEMENTATION. Every
width the algebra returns is fed back through `costs.position_size` and the
resulting `c/s` is required to equal the tolerance it was solved for. A closed
form that agrees with itself is worth nothing; this project's defect ledger is
largely a list of quantities derived from a mental model of an implementation
rather than from the implementation.

THE SEAL BARRIER IS PROBED, NOT ASSUMED. `test_the_sealed_barrier_actually_fires`
hands the assertion a sealed path and requires it to raise. Report 29 section 9
records a barrier that was armed, silently reverted, and never re-checked, and
six sealed partitions were opened as a result. A barrier nobody has seen fire is
a barrier nobody knows is connected.

NO OUTCOME QUANTITY, NO ENGINE. Asserted structurally: the module imports no
simulator and no portfolio path, and calls no engine entry point.
"""

import ast
import os
import sys

import numpy as np
import pytest

from src.analysis import floor_curve as fc
from src.timeframe import resample as rs

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src", "engine"))

import costs  # noqa: E402
import sizing  # noqa: E402

from src.analysis import exposure_profile as ep  # noqa: E402

LONG, SHORT = fc.LONG, fc.SHORT


@pytest.fixture(scope="module")
def cfg():
    return ep.cost_config()


def _module_ast():
    return ast.parse(open(fc.__file__).read())


# ---------------------------------------------------------------------------
# 1. THE GRID, COMMITTED BEFORE THE SOLVER.
# ---------------------------------------------------------------------------

def test_the_grid_is_the_one_that_was_committed():
    assert len(fc.TAU_GRID) == 57
    assert fc.TAU_GRID[0] == 0.02
    assert fc.TAU_GRID[-1] == 0.30
    assert all(abs((b - a) - 0.005) < 1e-12
               for a, b in zip(fc.TAU_GRID, fc.TAU_GRID[1:]))
    # The frozen tolerance is on the grid and carries no special status.
    assert 0.11 in fc.TAU_GRID


def test_a_narrowed_grid_is_refused_at_import():
    """The import-time check must actually fire, not merely exist."""
    original = fc.TAU_GRID
    try:
        fc.TAU_GRID = original[:10]
        with pytest.raises(ValueError, match="no longer ends"):
            fc._refuse_a_narrowed_grid()
        fc.TAU_GRID = original[5:]
        with pytest.raises(ValueError, match="no longer starts"):
            fc._refuse_a_narrowed_grid()
    finally:
        fc.TAU_GRID = original
    fc._refuse_a_narrowed_grid()


# ---------------------------------------------------------------------------
# 2. DERIVATION A -- SYNTHETIC POSITIVE CONTROL, HAND-COMPUTED.
# ---------------------------------------------------------------------------

def test_POSITIVE_CONTROL_the_closed_form_at_hand_computed_values(cfg):
    """HAND-COMPUTED FROM THE RATES, INDEPENDENTLY OF THE MODULE.

        w_long  = (2f + e + h) / (tau + f + h)
        w_short = (2f + e + h) / (tau - f - h)

    with f = 0.0006, e = 0, h = 0.0005 on BTCUSDT and ETHUSDT and 0.0010 on
    SOLUSDT. At tau = 0.11 the four values are computed here by hand and
    required to match the module to twelve decimal places.
    """
    f, e = 0.0006, 0.0
    assert cfg.taker_fee == f
    assert cfg.entry_slippage_bps == 0.0

    expected = {
        ("BTCUSDT", LONG): (2 * f + e + 0.0005) / (0.11 + f + 0.0005),
        ("BTCUSDT", SHORT): (2 * f + e + 0.0005) / (0.11 - f - 0.0005),
        ("SOLUSDT", LONG): (2 * f + e + 0.0010) / (0.11 + f + 0.0010),
        ("SOLUSDT", SHORT): (2 * f + e + 0.0010) / (0.11 - f - 0.0010),
    }
    for (symbol, direction), want in expected.items():
        got = fc.required_floor_fraction(0.11, cfg, symbol, direction)
        assert got == pytest.approx(want, rel=1e-12), (symbol, direction)

    # The four percentages, to four decimal places, stated so a drift is visible.
    assert fc.required_floor_fraction(0.11, cfg, "BTCUSDT", LONG) * 100 \
        == pytest.approx(1.5302, abs=5e-5)
    assert fc.required_floor_fraction(0.11, cfg, "BTCUSDT", SHORT) * 100 \
        == pytest.approx(1.5611, abs=5e-5)
    assert fc.required_floor_fraction(0.11, cfg, "SOLUSDT", LONG) * 100 \
        == pytest.approx(1.9713, abs=5e-5)
    assert fc.required_floor_fraction(0.11, cfg, "SOLUSDT", SHORT) * 100 \
        == pytest.approx(2.0295, abs=5e-5)


def test_CENTRAL_the_closed_form_is_verified_against_the_implementation(cfg):
    """THE CENTRAL TEST. Every width solved for a tolerance must reproduce that
    tolerance when fed back through `costs.position_size`."""
    for tau in fc.TAU_GRID:
        for symbol in rs.SYMBOLS:
            for direction in (LONG, SHORT):
                w = fc.required_floor_fraction(tau, cfg, symbol, direction)
                assert np.isfinite(w), (tau, symbol, direction)
                got = fc.realised_cost_ratio(1_000.0, w, cfg, symbol, direction)
                assert got == pytest.approx(tau, rel=1e-12), (
                    tau, symbol, direction, got)


def test_the_width_is_invariant_to_the_entry_price(cfg):
    """`P` cancels from `c/s`. ASSERTED AT THREE PRICES, not inferred."""
    for symbol in rs.SYMBOLS:
        for direction in (LONG, SHORT):
            w = fc.required_floor_fraction(0.11, cfg, symbol, direction)
            ratios = [fc.realised_cost_ratio(p, w, cfg, symbol, direction)
                      for p in (30_000.0, 2_000.0, 100.0)]
            for r in ratios:
                assert r == pytest.approx(0.11, rel=1e-12)


def test_MONOTONICITY_every_curve_claimed_monotone_is_verified(cfg):
    """The required width is STRICTLY DECREASING in the tolerance, on all six
    curves. Claimed in the report, so checked here rather than by inspection."""
    curve = fc.floor_curve(cfg)
    for symbol in rs.SYMBOLS:
        for direction in (LONG, SHORT):
            assert fc.curve_is_monotone_decreasing(curve, symbol, direction), (
                symbol, direction)
            sub = curve[(curve["symbol"] == symbol)
                        & (curve["direction"] == direction)].sort_values("tau")
            widths = sub["floor_fraction"].to_numpy(float)
            assert np.all(np.diff(widths) < 0.0)


def test_the_short_leg_needs_a_wider_floor_than_the_long_leg(cfg):
    """THE DIRECTION SPLIT, WHICH IS GEOMETRIC RATHER THAN A CONVENTION.

    The stop sits below entry on a long and above it on a short, so the taker
    fee and the haircut -- both charged on the stop price -- are larger on a
    short at the same width.
    """
    for tau in (0.05, 0.11, 0.20):
        for symbol in rs.SYMBOLS:
            long_w = fc.required_floor_fraction(tau, cfg, symbol, LONG)
            short_w = fc.required_floor_fraction(tau, cfg, symbol, SHORT)
            assert short_w > long_w, (tau, symbol)


def test_the_short_form_has_a_pole_and_returns_infinity_below_it(cfg):
    """No finite width meets a tolerance tighter than the stop-leg rate itself.

    Returning a NEGATIVE width there would be a silently wrong answer with the
    right sign flipped, which is why the module returns infinity instead.
    """
    for symbol in rs.SYMBOLS:
        p = fc.pole(cfg, symbol)
        assert fc.required_floor_fraction(p, cfg, symbol, SHORT) == float("inf")
        assert fc.required_floor_fraction(p / 2.0, cfg, symbol,
                                          SHORT) == float("inf")
        assert np.isfinite(fc.required_floor_fraction(p * 2.0, cfg, symbol,
                                                      SHORT))
        # The pole is far below the committed grid, so no grid point hits it.
        assert p < fc.TAU_GRID[0]


def test_the_haircut_is_the_only_term_that_differs_by_symbol(cfg):
    """BTCUSDT and ETHUSDT share a haircut and must share a curve."""
    for tau in (0.05, 0.11, 0.20):
        for direction in (LONG, SHORT):
            assert fc.required_floor_fraction(tau, cfg, "BTCUSDT", direction) \
                == fc.required_floor_fraction(tau, cfg, "ETHUSDT", direction)
            assert fc.required_floor_fraction(tau, cfg, "SOLUSDT", direction) \
                > fc.required_floor_fraction(tau, cfg, "BTCUSDT", direction)


# ---------------------------------------------------------------------------
# 3. DERIVATION B -- SYNTHETIC POSITIVE CONTROL, HAND-COMPUTED.
# ---------------------------------------------------------------------------

def test_POSITIVE_CONTROL_the_rejected_treatment_excess(cfg):
    """HAND-COMPUTED ON REPORT 30 SECTION 7.2's BTCUSDT CELL.

    Entry 30,000 at the 1.50% floor, long. The denominator without funding is

        move  = 450.000
        entry x taker = 30,000 x 0.0006 = 18.000
        stop  x taker = 29,550 x 0.0006 = 17.730
        s_entry = 0
        stop x haircut = 29,550 x 0.0005 = 14.775
        d0 = 500.505

    Two settlements crossed at 0.0001 gives an excess of
    30,000 x 0.0001 x 2 = 6.000 per unit, and 6.000 / 500.505 = 0.0119879.
    """
    result = fc.rejected_treatment_excess(30_000.0, 0.0150, cfg, "BTCUSDT",
                                          LONG, 2, 0.0001)
    assert result["excess_per_unit"] == pytest.approx(6.0, abs=1e-12)
    assert result["denominator_ex_funding"] == pytest.approx(500.505, abs=1e-9)
    assert result["fraction_of_unit_ex_funding"] == pytest.approx(
        6.0 / 500.505, rel=1e-12)
    assert result["fraction_of_unit_inc_funding"] == pytest.approx(
        6.0 / (500.505 + 9.0), rel=1e-12)


def test_the_excess_scales_linearly_in_the_settlement_count(cfg):
    a = fc.rejected_treatment_excess(30_000.0, 0.0150, cfg, "BTCUSDT", LONG,
                                     2, 0.0001)
    b = fc.rejected_treatment_excess(30_000.0, 0.0150, cfg, "BTCUSDT", LONG,
                                     3, 0.0001)
    assert b["excess_per_unit"] == pytest.approx(
        1.5 * a["excess_per_unit"], rel=1e-12)


def test_the_two_normalisations_bracket_and_do_not_change_the_order(cfg):
    """5.4 does not say whether the funding term also leaves the denominator.

    BOTH NORMALISATIONS ARE REPORTED AND NEITHER IS CHOSEN. The test asserts
    they bracket each other and that the spread is small enough that no
    order-of-magnitude conclusion depends on the choice.
    """
    for symbol, price in (("BTCUSDT", 30_000.0), ("ETHUSDT", 2_000.0),
                          ("SOLUSDT", 100.0)):
        for direction in (LONG, SHORT):
            r = fc.rejected_treatment_excess(price, 0.0150, cfg, symbol,
                                             direction, 2, 0.0001)
            hi = r["fraction_of_unit_ex_funding"]
            lo = r["fraction_of_unit_inc_funding"]
            assert hi > lo > 0.0
            assert (hi - lo) / hi < 0.02


def test_the_rejected_excess_dwarfs_the_accepted_fill_price_term(cfg):
    """Report 30 section 7.3 accepted a term under 0.017% of a risk unit. The
    rejected one is two orders of magnitude larger, on every reference cell."""
    for symbol, price in (("BTCUSDT", 30_000.0), ("ETHUSDT", 2_000.0),
                          ("SOLUSDT", 100.0)):
        r = fc.rejected_treatment_excess(price, 0.0150, cfg, symbol, LONG,
                                         2, 0.0001)
        assert r["fraction_of_unit_ex_funding"] > 50 * 0.00017


# ---------------------------------------------------------------------------
# 4. DERIVATION C -- SYNTHETIC POSITIVE CONTROL.
# ---------------------------------------------------------------------------

def test_POSITIVE_CONTROL_floor_binding_is_pure_bar_geometry(cfg):
    """HAND-COMPUTED. The floor binds when 2.25 x ATR falls below w x entry.

    Entry 100, ATR 0.3, so 2.25 x 0.3 = 0.675. At a 1.50% floor the floor
    distance is 1.500 and BINDS; at a 0.50% floor it is 0.500 and the ATR binds.
    Asserted against `sizing.floor_binds`, which is the implementation the
    stratification calls.
    """
    assert 2.25 * 0.3 == pytest.approx(0.675)
    assert sizing.floor_binds(100.0, 0.3, floor_fraction=0.0150) is True
    assert sizing.floor_binds(100.0, 0.3, floor_fraction=0.0050) is False
    # And the boundary itself: 0.675 / 100 = 0.00675, strictly below binds.
    assert sizing.floor_binds(100.0, 0.3, floor_fraction=0.00676) is True
    assert sizing.floor_binds(100.0, 0.3, floor_fraction=0.00674) is False


def test_POSITIVE_CONTROL_stratify_at_on_a_hand_built_population(cfg):
    """A two-row synthetic population with a known answer at a known tolerance."""
    import pandas as pd

    specs = sizing.load_symbol_specs()
    ticks = sizing.load_tick_schedules()
    stamp = 1_688_000_000_000

    population = pd.DataFrame([
        {"ts": stamp, "symbol": "BTCUSDT", "direction": LONG,
         "entry_price": 30_000.0, "atr": 1.0, "entry_close_ms": stamp},
        {"ts": stamp, "symbol": "BTCUSDT", "direction": LONG,
         "entry_price": 30_000.0, "atr": 1_000.0, "entry_close_ms": stamp},
    ])
    out = fc.stratify_at(population, 0.11, cfg, specs, ticks)

    w = fc.required_floor_fraction(0.11, cfg, "BTCUSDT", LONG)
    # Row 0: 2.25 x 1 = 2.25 against w x 30,000 = about 459. Floor binds.
    # Row 1: 2.25 x 1,000 = 2,250 against about 459. ATR binds.
    assert bool(out.iloc[0]["floor_bound"]) is True
    assert bool(out.iloc[1]["floor_bound"]) is False
    assert out.iloc[0]["floor_fraction"] == pytest.approx(w)
    assert (out["drag_fraction"] >= 0.0).all()
    assert (out["drag_fraction"] < 1.0).all()


def test_the_floor_bound_fraction_falls_as_the_tolerance_loosens(cfg):
    """A looser tolerance permits a narrower floor, so fewer positions are
    floor-bound. Verified on a synthetic population across the grid."""
    import pandas as pd

    specs = sizing.load_symbol_specs()
    ticks = sizing.load_tick_schedules()
    stamp = 1_688_000_000_000
    rows = [{"ts": stamp, "symbol": "BTCUSDT", "direction": LONG,
             "entry_price": 30_000.0, "atr": a, "entry_close_ms": stamp}
            for a in np.linspace(1.0, 400.0, 60)]
    population = pd.DataFrame(rows)

    fractions = []
    for tau in (0.03, 0.06, 0.11, 0.20, 0.30):
        out = fc.stratify_at(population, tau, cfg, specs, ticks)
        fractions.append(float(out["floor_bound"].mean()))
    assert all(b <= a + 1e-12 for a, b in zip(fractions, fractions[1:])), \
        fractions


# ---------------------------------------------------------------------------
# 5. THE SEAL BARRIER -- PROBED.
# ---------------------------------------------------------------------------

def test_the_sealed_barrier_ACTUALLY_FIRES_when_handed_a_sealed_path():
    """THE PROBE. A barrier nobody has seen fire is a barrier nobody knows is
    connected. Report 29 section 9 is what this test exists because of."""
    sealed_path = os.path.join(rs.DERIVED, "ohlcv_1m", "symbol=BTCUSDT",
                               "year=2025", "data.parquet")
    with pytest.raises(fc.SealedPathRefused, match="sealed"):
        fc.assert_paths_unsealed([sealed_path], "probe")

    other = os.path.join(rs.DERIVED, "ohlcv_1m", "symbol=SOLUSDT",
                         "year=2026", "data.parquet")
    with pytest.raises(fc.SealedPathRefused):
        fc.assert_paths_unsealed([other], "probe")

    # And a mixed list is refused on account of the one sealed member.
    readable = os.path.join(rs.DERIVED, "ohlcv_1m", "symbol=BTCUSDT",
                            "year=2023", "data.parquet")
    with pytest.raises(fc.SealedPathRefused):
        fc.assert_paths_unsealed([readable, sealed_path], "probe")


def test_the_barrier_passes_a_readable_set_unchanged():
    readable = [os.path.join(rs.DERIVED, "ohlcv_1m", "symbol=BTCUSDT",
                             "year=%d" % y, "data.parquet")
                for y in (2022, 2023, 2024)]
    assert fc.assert_paths_unsealed(readable, "probe") == readable
    fifteen = os.path.join(rs.DERIVED, "ohlcv_15m", "BTCUSDT.parquet")
    assert fc.assert_paths_unsealed([fifteen], "probe") == [fifteen]


def test_the_barrier_is_called_once_per_read_not_once_per_run():
    """ASSERTED OVER THE AST. The call must sit INSIDE the per-symbol loop."""
    tree = _module_ast()
    fn = [n for n in ast.walk(tree)
          if isinstance(n, ast.FunctionDef) and n.name == "candidate_population"]
    assert len(fn) == 1
    loops = [n for n in ast.walk(fn[0]) if isinstance(n, ast.For)]
    assert len(loops) == 1, "one loop over symbols"
    inside = [n for n in ast.walk(loops[0])
              if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
              and n.func.id == "assert_paths_unsealed"]
    assert len(inside) == 2, (
        "both the 15m path and the 1m allowed set are asserted inside the loop")


# ---------------------------------------------------------------------------
# 6. WHAT THE MODULE MAY NOT DO.
# ---------------------------------------------------------------------------

def test_no_engine_entry_point_is_invoked():
    """NO SIMULATOR, NO PORTFOLIO PATH, NO BACKTEST. Asserted over imports and
    over every call name in the module."""
    tree = _module_ast()
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imported.add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imported.add(node.module)
                for alias in node.names:
                    imported.add("%s.%s" % (node.module, alias.name))
    for banned in ("simulate", "portfolio", "src.engine.portfolio", "run",
                   "src.sweep", "src.regime"):
        assert banned not in imported, banned

    called = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                called.add(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                called.add(node.func.attr)
    for banned in ("run_backtest", "run", "simulate", "measure", "allocate",
                   "resolve", "load_1m"):
        assert banned not in called, banned

    source = open(fc.__file__).read()
    assert "exit_reason" not in source


PERFORMANCE_NAMES = ("expectancy", "win_rate", "winrate", "profit_factor",
                     "sharpe", "sortino", "net_pnl", "gross_pnl", "drawdown",
                     "r_multiple", "equity", "pnl")


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


def _code_text():
    """The module's EXECUTABLE tokens, comments and docstrings stripped.

    THE MODULE QUOTES THE DENOMINATOR IN ORDER TO CITE IT, so a raw text search
    fires on the citation rather than on a reimplementation. This is the same
    false-positive shape the defect ledger records at instance (37) -- a check
    written from a mental model of what it matches -- and it fired here on the
    first run, against a clean module.
    """
    import io
    import tokenize

    out, prev = [], tokenize.INDENT
    for tok in tokenize.generate_tokens(
            io.StringIO(open(fc.__file__).read()).readline):
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


def test_the_cost_algebra_is_not_reimplemented():
    """The module must REACH the engine's denominator, never restate it.

    CHECKED OVER EXECUTABLE TOKENS ONLY, for the reason `_code_text` gives.
    """
    code = _code_text()
    assert "per_unit_denominator" in code
    assert "position_size" in code
    # No second copy of the denominator expression among what actually runs.
    assert "move + entry" not in code
    assert "taker_fee +" not in code
    assert "haircut_bps" not in code or "cost_terms" in code


def test_no_tolerance_value_is_selected_by_the_module():
    """The module reports curves. It names no chosen tolerance and no floor."""
    tree = _module_ast()
    assigned = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    assigned.add(target.id)
    for banned in ("CHOSEN_TAU", "SELECTED_TOLERANCE", "RECOMMENDED_FLOOR",
                   "COST_TOLERANCE_R", "STOP_FLOOR_FRACTION"):
        assert banned not in assigned, banned
