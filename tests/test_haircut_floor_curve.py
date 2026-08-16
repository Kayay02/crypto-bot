"""Guards for the revised floor derivation, sub-point 4.1a.

THE GRID WAS COMMITTED ALONE AT `532e9334`, before this module's solver existed.
The denomination it solves under was committed at `02992c7a`.

THE CLOSED FORM IS NOT TRUSTED, IT IS CHECKED. Every solved width is fed back
through `costs.position_size`, the unvalidated sum is recovered by difference,
and the resulting ratio is required to equal the tolerance it was solved for.

THE NUMERATOR IS A SET, AND THAT IS PROBED RATHER THAN ASSERTED IN PROSE.
`test_PROBE_the_numerator_is_a_set_not_a_hardcoded_term` switches on a second
unvalidated term and requires the numerator, the ratio and the solved width all
to move. A set with one member behaves identically to a hardcoded term until a
second member exists, so nothing short of adding one tests the difference.

ALL SOURCE-TEXT CHECKS RUN OVER EXECUTABLE TOKENS. Standing rule adopted at
`docs/design/04_1a_denomination_amendment_1.md` §7, after three consecutive steps
in which raw-text checks fired falsely against clean modules.
"""

import ast
import dataclasses
import io
import os
import sys
import tokenize

import numpy as np
import pytest

from src.analysis import haircut_floor_curve as hfc
from src.timeframe import resample as rs

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src", "engine"))

import costs  # noqa: E402

from src.analysis import exposure_profile as ep  # noqa: E402

LONG, SHORT = hfc.LONG, hfc.SHORT


@pytest.fixture(scope="module")
def cfg():
    return ep.cost_config()


@pytest.fixture(scope="module")
def curve(cfg):
    return hfc.floor_curve(cfg)


def _module_ast():
    return ast.parse(open(hfc.__file__).read())


def _code_text():
    """The module's executable tokens, comments and docstrings stripped."""
    out, prev = [], tokenize.INDENT
    for tok in tokenize.generate_tokens(
            io.StringIO(open(hfc.__file__).read()).readline):
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
# 1. THE GRID, COMMITTED FIRST AND CHOSEN FROM THE ALGEBRA.
# ---------------------------------------------------------------------------

def test_the_grid_is_the_one_that_was_committed():
    assert len(hfc.TAU_GRID) == 37
    assert hfc.TAU_GRID[0] == 0.030
    assert hfc.TAU_GRID[-1] == 0.120
    assert all(abs((b - a) - 0.0025) < 1e-12
               for a, b in zip(hfc.TAU_GRID, hfc.TAU_GRID[1:]))


def test_a_narrowed_grid_is_refused_at_import():
    original = hfc.TAU_GRID
    try:
        hfc.TAU_GRID = original[:10]
        with pytest.raises(ValueError, match="no longer ends"):
            hfc._refuse_a_narrowed_grid()
        hfc.TAU_GRID = original[5:]
        with pytest.raises(ValueError, match="no longer starts"):
            hfc._refuse_a_narrowed_grid()
    finally:
        hfc.TAU_GRID = original
    hfc._refuse_a_narrowed_grid()


def test_the_grid_is_not_report_32s(cfg):
    """A DIFFERENT QUANTITY NEEDS A DIFFERENT RANGE. Carrying report 32's grid
    over by analogy is the defect this asserts against."""
    from src.analysis import floor_curve as old
    assert hfc.TAU_GRID != old.TAU_GRID
    assert hfc.TAU_GRID[0] != old.TAU_GRID[0]
    assert hfc.TAU_GRID[-1] != old.TAU_GRID[-1]


def test_the_grid_bounds_are_the_structural_ones_claimed(cfg):
    """LOWER: every cell is satisfiable within the frozen `stop_max_pct` cap.
    UPPER: every cell has fallen below the thesis's frozen 1.50% floor."""
    at_lo = [hfc.required_floor_fraction(hfc.TAU_GRID[0], cfg, s, d)
             for s in rs.SYMBOLS for d in (LONG, SHORT)]
    assert max(at_lo) < cfg.stop_max_pct, max(at_lo)
    # And just below the grid the most demanding cell breaches that cap.
    below = hfc.required_floor_fraction(0.029, cfg, "SOLUSDT", SHORT)
    assert below > cfg.stop_max_pct

    at_hi = [hfc.required_floor_fraction(hfc.TAU_GRID[-1], cfg, s, d)
             for s in rs.SYMBOLS for d in (LONG, SHORT)]
    assert max(at_hi) < 0.0150, max(at_hi)


# ---------------------------------------------------------------------------
# 2. THE CLOSED FORM -- SYNTHETIC POSITIVE CONTROL, HAND-COMPUTED.
# ---------------------------------------------------------------------------

def test_POSITIVE_CONTROL_the_closed_form_at_hand_computed_values(cfg):
    """HAND-COMPUTED FROM THE RATES, INDEPENDENTLY OF THE MODULE.

        long   w = (a + b) / (tau + a)
        short  w = (a + b) / (tau - a)

    with `a` the unvalidated rate on the stop price -- the haircut, 0.0005 on
    BTCUSDT and ETHUSDT and 0.0010 on SOLUSDT -- and `b` the unvalidated rate on
    the entry price, which is 0.0 at this commit.
    """
    b = 0.0
    assert cfg.entry_slippage_bps == 0.0

    for symbol, a in (("BTCUSDT", 0.0005), ("ETHUSDT", 0.0005),
                      ("SOLUSDT", 0.0010)):
        assert cfg.haircut_bps(symbol) / 10_000.0 == a
        for tau in (0.030, 0.0675, 0.120):
            want_long = (a + b) / (tau + a)
            want_short = (a + b) / (tau - a)
            assert hfc.required_floor_fraction(tau, cfg, symbol, LONG) \
                == pytest.approx(want_long, rel=1e-12)
            assert hfc.required_floor_fraction(tau, cfg, symbol, SHORT) \
                == pytest.approx(want_short, rel=1e-12)


def test_CENTRAL_every_solved_width_reproduces_its_tolerance(curve):
    """THE CENTRAL TEST. The closed form is checked against the implementation,
    not against itself: the unvalidated sum is recovered from
    `costs.position_size` by difference at every solved width."""
    assert len(curve) == len(hfc.TAU_GRID) * len(rs.SYMBOLS) * 2
    assert np.isfinite(curve["floor_fraction"]).all()
    assert hfc.max_residual(curve) < 1e-12, hfc.max_residual(curve)


def test_the_width_is_invariant_to_the_entry_price(cfg):
    """`P` cancels. ASSERTED AT THREE WIDELY SEPARATED PRICES, as report 32 §3.5
    did, rather than inferred from the algebra."""
    for symbol in rs.SYMBOLS:
        for direction in (LONG, SHORT):
            w = hfc.required_floor_fraction(0.0675, cfg, symbol, direction)
            for price in (30_000.0, 1_000.0, 100.0):
                got = hfc.realised_unvalidated_ratio(price, w, cfg, symbol,
                                                     direction)
                assert got == pytest.approx(0.0675, rel=1e-12), (symbol, price)


def test_MONOTONICITY_is_verified_not_assumed(curve, cfg):
    """Strictly DECREASING in the tolerance, on all six curves."""
    for symbol in rs.SYMBOLS:
        for direction in (LONG, SHORT):
            assert hfc.curve_is_monotone_decreasing(curve, symbol, direction)
            sub = curve[(curve["symbol"] == symbol)
                        & (curve["direction"] == direction)].sort_values("tau")
            assert np.all(np.diff(sub["floor_fraction"].to_numpy(float)) < 0.0)


# ---------------------------------------------------------------------------
# 3. THE DIRECTION SPLIT AND THE POLE, DERIVED RATHER THAN INHERITED.
# ---------------------------------------------------------------------------

def test_a_direction_split_ARISES_and_the_short_needs_the_wider_floor(cfg):
    """The stop-attached unvalidated rate is charged on a price that sits below
    entry on a long and above it on a short, so a split still arises."""
    for tau in (0.030, 0.0675, 0.120):
        for symbol in rs.SYMBOLS:
            long_w = hfc.required_floor_fraction(tau, cfg, symbol, LONG)
            short_w = hfc.required_floor_fraction(tau, cfg, symbol, SHORT)
            assert short_w > long_w, (tau, symbol)


def test_WHAT_WOULD_HAVE_SHOWN_NO_SPLIT_zero_stop_attached_rate(cfg):
    """THE NEGATIVE RESULT MADE CHECKABLE.

    The split collapses exactly when no unvalidated term is charged on the stop
    price. Constructed here by moving the whole unvalidated rate onto the entry
    price: the two directions then coincide and the pole disappears.
    """
    moved = dataclasses.replace(
        cfg, stop_haircut_bps={s: 0.0 for s in cfg.stop_haircut_bps},
        entry_slippage_bps=5.0)
    for tau in (0.030, 0.120):
        for symbol in rs.SYMBOLS:
            long_w = hfc.required_floor_fraction(tau, moved, symbol, LONG)
            short_w = hfc.required_floor_fraction(tau, moved, symbol, SHORT)
            assert long_w == pytest.approx(short_w, rel=1e-12)
    assert hfc.pole(moved, "SOLUSDT") == 0.0


def test_POLE_PROBE_the_short_form_is_undefined_at_and_below_the_stop_rate(cfg):
    """The pole sits at the stop-attached unvalidated rate. REPORT 32'S SAT
    ELSEWHERE -- at the taker fee plus the haircut -- so it has moved, and the
    move is asserted rather than described."""
    from src.analysis import floor_curve as old

    for symbol in rs.SYMBOLS:
        p = hfc.pole(cfg, symbol)
        assert p == cfg.haircut_bps(symbol) / 10_000.0
        assert hfc.required_floor_fraction(p, cfg, symbol, SHORT) == float("inf")
        assert hfc.required_floor_fraction(p / 2.0, cfg, symbol,
                                           SHORT) == float("inf")
        assert np.isfinite(hfc.required_floor_fraction(p * 2.0, cfg, symbol,
                                                       SHORT))
        # The long leg has no pole anywhere at or above zero.
        assert np.isfinite(hfc.required_floor_fraction(p / 2.0, cfg, symbol,
                                                       LONG))
        # It has MOVED relative to report 32's, and sits below it.
        assert p < old.pole(cfg, symbol)
        # And it is far below the committed grid, so no grid point nears it.
        assert p < hfc.TAU_GRID[0]


# ---------------------------------------------------------------------------
# 4. THE SET PROBE -- THE ONE TEST THAT DISTINGUISHES A SET FROM A TERM.
# ---------------------------------------------------------------------------

def test_PROBE_the_numerator_is_a_set_not_a_hardcoded_term(cfg):
    """A SET WITH ONE MEMBER IS INDISTINGUISHABLE FROM A HARDCODED TERM UNTIL A
    SECOND MEMBER EXISTS. So one is added.

    `entry_slippage_bps` is 0.0 at this commit and `src/engine/costs.py` records
    that it exists so it can be sensitivity-tested later. Switching it on must
    move the numerator, the ratio and the solved width -- if any of the three is
    unmoved, the term has escaped the constraint.
    """
    with_slip = dataclasses.replace(cfg, entry_slippage_bps=3.0)

    on_stop_a, on_entry_a = hfc.unvalidated_rates(cfg, "BTCUSDT")
    on_stop_b, on_entry_b = hfc.unvalidated_rates(with_slip, "BTCUSDT")
    assert on_entry_a == 0.0
    assert on_entry_b == pytest.approx(0.0003)
    assert on_stop_a == on_stop_b, "the stop-attached rate must be untouched"

    # The measured ratio moves, through the engine.
    base = hfc.realised_unvalidated_ratio(1_000.0, 0.015, cfg, "BTCUSDT", LONG)
    more = hfc.realised_unvalidated_ratio(1_000.0, 0.015, with_slip, "BTCUSDT",
                                          LONG)
    assert more > base

    # And the solved width moves, because a larger numerator needs a wider stop.
    w_base = hfc.required_floor_fraction(0.0675, cfg, "BTCUSDT", LONG)
    w_more = hfc.required_floor_fraction(0.0675, with_slip, "BTCUSDT", LONG)
    assert w_more > w_base

    # The solved width still reproduces its tolerance with the second term live.
    assert hfc.realised_unvalidated_ratio(1_000.0, w_more, with_slip, "BTCUSDT",
                                          LONG) == pytest.approx(0.0675,
                                                                 rel=1e-12)


def test_the_unvalidated_set_is_declared_and_covers_both_terms():
    assert set(hfc.UNVALIDATED_TERMS) == {"stop_haircut_bps",
                                          "entry_slippage_bps"}
    assert hfc.UNVALIDATED_TERMS["stop_haircut_bps"] == "stop"
    assert hfc.UNVALIDATED_TERMS["entry_slippage_bps"] == "entry"


def test_an_unknown_attachment_point_raises_rather_than_being_dropped(cfg):
    """A SILENTLY OMITTED TERM IS WHAT THE SET EXISTS TO PREVENT."""
    original = dict(hfc.UNVALIDATED_TERMS)
    try:
        hfc.UNVALIDATED_TERMS["stop_haircut_bps"] = "somewhere_else"
        with pytest.raises(ValueError, match="attachment point"):
            hfc.unvalidated_rates(cfg, "BTCUSDT")
    finally:
        hfc.UNVALIDATED_TERMS.clear()
        hfc.UNVALIDATED_TERMS.update(original)
    hfc.unvalidated_rates(cfg, "BTCUSDT")


def test_zeroing_the_set_does_not_mutate_the_frozen_config(cfg):
    before = cfg.haircut_bps("SOLUSDT")
    zeroed = hfc.zero_unvalidated(cfg)
    assert zeroed.haircut_bps("SOLUSDT") == 0.0
    assert zeroed.entry_slippage_bps == 0.0
    assert cfg.haircut_bps("SOLUSDT") == before


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
    """The unvalidated sum is obtained BY DIFFERENCE from the engine."""
    code = _code_text()
    assert "per_unit_denominator" in code
    assert "taker_fee" not in code
    assert "move + entry" not in code
    # The rate conversion appears once, reading the config, not restating a term.
    assert code.count("10_000.0") == 1


def test_no_tolerance_value_is_selected_and_no_verdict_is_returned():
    """THIS STEP RETURNS NO NON-UNIFORMITY VERDICT. That is the next step's."""
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

    functions = {n.name for n in ast.walk(tree)
                 if isinstance(n, ast.FunctionDef)}
    for banned in ("threshold_verdict", "fires", "spread", "verdict"):
        assert banned not in functions, banned
    code = _code_text()
    assert "s_max" not in code.lower()
    assert "r_min" not in code.lower()


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
