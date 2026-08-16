"""Guards for the risk-unit stop floor, report 36.

NOTHING IS INHERITED FROM REPORT 33 AND A TEST ENFORCES THAT: this module must
not import `haircut_floor_curve`, and its grid must satisfy the rule stated in
its own source rather than reproduce report 33's numbers.

THE NEGATIVE CONDITIONS ARE EXERCISED, NOT MERELY THE POSITIVE ONES. The
direction split is shown to VANISH under the exact condition the module claims
would remove it, so a finding of "no split" would have been checkable. The
achievable range is shown to REFUSE a tolerance above a symbol's ceiling, on the
symbol whose ceiling is lower, while the other symbol still solves.
"""

import ast
import io
import os
import sys
import tokenize
from dataclasses import replace

import pytest

from src.analysis import risk_unit_floor_curve as ru
from src.timeframe import resample as rs

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src", "engine"))

from src.analysis import exposure_profile as ep  # noqa: E402

LONG, SHORT = ru.LONG, ru.SHORT


@pytest.fixture(scope="module")
def cfg():
    return ep.cost_config()


@pytest.fixture(scope="module")
def rows(cfg):
    return ru.curve(cfg)


def _module_ast():
    return ast.parse(open(ru.__file__).read())


def _code_text():
    out, prev = [], tokenize.INDENT
    for tok in tokenize.generate_tokens(
            io.StringIO(open(ru.__file__).read()).readline):
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
# PART A. THE ACHIEVABLE RANGE.
# ---------------------------------------------------------------------------

def test_POSITIVE_CONTROL_the_zero_width_limit_hand_computed(cfg):
    """HAND-COMPUTED. At zero width the stop price IS the entry price, so

        limit = A / (A + 2f)

    with A the unvalidated total. BTCUSDT: 0.0008 / (0.0008 + 0.0012) = 0.40.
    SOLUSDT: 0.0013 / (0.0013 + 0.0012) = 0.52.
    """
    assert ru.limit_ratio_as_width_to_zero(cfg, "BTCUSDT") == pytest.approx(
        0.0008 / 0.0020, rel=1e-15)
    assert ru.limit_ratio_as_width_to_zero(cfg, "SOLUSDT") == pytest.approx(
        0.0013 / 0.0025, rel=1e-15)


@pytest.mark.parametrize("symbol", ["BTCUSDT", "ETHUSDT", "SOLUSDT"])
def test_LIMIT_the_ratio_approaches_that_limit_as_the_width_vanishes(cfg, symbol):
    """THE CLAIM PART A MAKES, TESTED AS A LIMIT AND FROM THE ENGINE.

    The limit is DIRECTION-INDEPENDENT because the direction enters only through
    the width, so both directions must converge to the same value.

    THE ORDER OF CONVERGENCE IS ASSERTED, NOT MERELY CLOSENESS. The approach is
    first order in the width, so the gap must fall by a factor of ten for each
    decade. A test that only checked closeness at one small width would pass on a
    curve converging to the wrong value from far away.
    """
    want = ru.limit_ratio_as_width_to_zero(cfg, symbol)
    for direction in (LONG, SHORT):
        gaps = [abs(ru.ratio_at_width(w, cfg, symbol, direction) - want)
                for w in (1e-6, 1e-7, 1e-8, 1e-9, 1e-10, 1e-11, 1e-12)]
        for before, after in zip(gaps, gaps[1:]):
            assert after < before
            assert before / after == pytest.approx(10.0, rel=1e-3)
        assert gaps[-1] < 1e-9


@pytest.mark.parametrize("symbol", ["BTCUSDT", "ETHUSDT", "SOLUSDT"])
@pytest.mark.parametrize("direction", [LONG, SHORT])
def test_MONOTONICITY_measured_not_assumed(cfg, symbol, direction):
    """A dense sweep over the whole domain, twenty thousand steps."""
    kind, step, n = ru.monotonicity(cfg, symbol, direction)
    assert kind == "decreasing", (symbol, direction, kind)
    assert n >= 20_000
    assert step > 0.0


def test_the_achievable_range_DIFFERS_BY_SYMBOL(cfg):
    """THE STRUCTURAL FINDING. The ceiling is set by the unvalidated total, which
    differs across symbols through the haircut alone."""
    btc = ru.limit_ratio_as_width_to_zero(cfg, "BTCUSDT")
    eth = ru.limit_ratio_as_width_to_zero(cfg, "ETHUSDT")
    sol = ru.limit_ratio_as_width_to_zero(cfg, "SOLUSDT")
    assert btc == eth
    assert sol > btc
    for direction in (LONG, SHORT):
        lo, hi = ru.achievable_range(cfg, "SOLUSDT", direction)
        assert lo < hi
        assert ru.achievable_range(cfg, "BTCUSDT", direction)[0] < lo, (
            "SOLUSDT must need more width at the cap than BTCUSDT")


def test_a_tolerance_above_a_SYMBOLS_CEILING_REFUSES_on_that_symbol_only(cfg):
    """THE NEGATIVE CONDITION, EXERCISED.

    At 0.40 BTCUSDT's constraint imposes no floor at any width and the solver
    must refuse. SOLUSDT's ceiling is higher, so it must still solve. A solver
    that returned a number for both would hide the finding.
    """
    with pytest.raises(ValueError):
        ru.required_floor_fraction(0.40, cfg, "BTCUSDT", LONG)
    with pytest.raises(ValueError):
        ru.required_floor_fraction(0.45, cfg, "ETHUSDT", SHORT)
    assert ru.required_floor_fraction(0.45, cfg, "SOLUSDT", LONG) > 0.0
    with pytest.raises(ValueError):
        ru.required_floor_fraction(0.52, cfg, "SOLUSDT", LONG)

    # AND THE BOUNDARY IS THE CEILING ITSELF, NOT AN EPSILON EITHER SIDE OF IT.
    # Just below, a positive width exists and shrinks toward zero.
    for symbol in ("BTCUSDT", "SOLUSDT"):
        ceiling = ru.limit_ratio_as_width_to_zero(cfg, symbol)
        near = ru.required_floor_fraction(ceiling * (1.0 - 1e-9), cfg, symbol,
                                          LONG)
        assert 0.0 < near < 1e-8


# ---------------------------------------------------------------------------
# THE GRID.
# ---------------------------------------------------------------------------

def test_the_grid_SATISFIES_ITS_STATED_RULE_rather_than_recording_numbers(cfg):
    """Re-derived from the achievable range: every multiple of the step lying
    strictly inside the common achievable interval."""
    import math
    lo, hi = ru.common_achievable_range(cfg)
    step = ru.TAU_STEP
    first = math.floor(lo / step) + 1
    last = math.ceil(hi / step) - 1
    assert ru.TAU_GRID == tuple(round(k * step, 10)
                                for k in range(first, last + 1))
    assert ru.TAU_GRID[0] > lo and ru.TAU_GRID[-1] < hi
    assert len(ru.TAU_GRID) == 91


def test_the_grid_is_NOT_report_33s(cfg):
    """Different bounds, step and count, and no import of that module."""
    from src.analysis import haircut_floor_curve as old
    assert ru.TAU_GRID != old.TAU_GRID
    assert ru.TAU_GRID[0] != old.TAU_GRID[0]
    assert ru.TAU_STEP != (old.TAU_GRID[1] - old.TAU_GRID[0])

    imported = set()
    for node in ast.walk(_module_ast()):
        if isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module)
        elif isinstance(node, ast.Import):
            for a in node.names:
                imported.add(a.name)
    assert not [m for m in imported if "haircut" in m or "floor_curve" in m]


# ---------------------------------------------------------------------------
# PART B. THE CLOSED FORM.
# ---------------------------------------------------------------------------

def test_POSITIVE_CONTROL_the_closed_form_hand_computed(cfg):
    """HAND-COMPUTED FROM THE RATES, INDEPENDENTLY OF THE MODULE.

        w = [ A(1 - tau) - 2 f tau ] / [ tau (1 + sigma (f + h)) - sigma h ]

    BTCUSDT long at tau = 0.100, sigma = -1:
        numerator   = 0.0008 x 0.9 - 0.0012 x 0.1 = 0.00072 - 0.00012 = 0.00060
        denominator = 0.1 x (1 - 0.0011) + 0.0005 = 0.09989 + 0.0005 = 0.10039
        w           = 0.00060 / 0.10039

    SOLUSDT short at tau = 0.100, sigma = +1:
        numerator   = 0.0013 x 0.9 - 0.0012 x 0.1 = 0.00117 - 0.00012 = 0.00105
        denominator = 0.1 x (1 + 0.0016) - 0.0010 = 0.10016 - 0.0010 = 0.09916
        w           = 0.00105 / 0.09916
    """
    assert ru.required_floor_fraction(0.100, cfg, "BTCUSDT", LONG) == \
        pytest.approx(0.00060 / 0.10039, rel=1e-14)
    assert ru.required_floor_fraction(0.100, cfg, "SOLUSDT", SHORT) == \
        pytest.approx(0.00105 / 0.09916, rel=1e-14)


def test_the_equation_is_LINEAR_in_the_width_which_is_why_there_is_a_closed_form(cfg):
    """THE SELF-REFERENCE RESOLVES BECAUSE BOTH SIDES ARE AFFINE.

    Asserted rather than argued: the numerator and the risk unit are each affine
    in the width, so a three-point second difference is zero.
    """
    entry = ru.REFERENCE_PRICE
    for symbol in rs.SYMBOLS:
        for direction in (LONG, SHORT):
            def at(w):
                stop = ru.stop_from_width(entry, w, direction)
                return (ru.unvalidated_sum(entry, stop, direction, cfg, symbol),
                        ru.risk_unit(entry, stop, direction, cfg, symbol))
            u0, d0 = at(0.01)
            u1, d1 = at(0.02)
            u2, d2 = at(0.03)
            assert (u2 - 2 * u1 + u0) == pytest.approx(0.0, abs=1e-12)
            assert (d2 - 2 * d1 + d0) == pytest.approx(0.0, abs=1e-12)


def test_no_iteration_is_performed(cfg):
    """A closed form was found, so the module must contain no solver loop."""
    tree = _module_ast()
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name in (
                "required_floor_fraction", "pole", "form_constants"):
            assert not [n for n in ast.walk(node)
                        if isinstance(n, (ast.While, ast.For))], node.name
    code = _code_text()
    for banned in ("brentq", "fsolve", "bisect", "newton", "minimize"):
        assert banned not in code, banned


# ---------------------------------------------------------------------------
# THE DIRECTION SPLIT AND THE POLE.
# ---------------------------------------------------------------------------

def test_a_DIRECTION_SPLIT_ARISES_and_shorts_need_more_width(cfg):
    for symbol in rs.SYMBOLS:
        assert ru.direction_split_present(cfg, symbol) is True
        for tau in (ru.TAU_GRID[0], ru.TAU_GRID[len(ru.TAU_GRID) // 2]):
            lo = ru.required_floor_fraction(tau, cfg, symbol, LONG)
            hi = ru.required_floor_fraction(tau, cfg, symbol, SHORT)
            assert hi > lo


def test_THE_NEGATIVE_CONDITION_the_split_vanishes_under_the_stated_condition(cfg):
    """WHAT WOULD HAVE CONSTITUTED SHOWING NO SPLIT ARISES, EXERCISED.

    The direction enters only through the rates charged on the STOP price. Both
    must vanish for the split to go:

      * haircut zeroed alone -- the split SURVIVES, carried by the stop-leg
        taker fee;
      * haircut AND taker fee zeroed -- the split VANISHES exactly.

    A test that only checked the positive case could not have distinguished a
    real split from a broken comparison.
    """
    no_haircut = replace(cfg, stop_haircut_bps={s: 0.0
                                                for s in cfg.stop_haircut_bps})
    assert ru.direction_split_present(no_haircut, "BTCUSDT") is True

    neither = replace(no_haircut, taker_fee=0.0)
    assert ru.direction_split_present(neither, "BTCUSDT") is False
    for tau in (0.10, 0.30):
        assert ru.required_floor_fraction(tau, neither, "BTCUSDT", LONG) == \
            pytest.approx(
                ru.required_floor_fraction(tau, neither, "BTCUSDT", SHORT),
                rel=1e-15)


def test_POLE_PROBE_shorts_have_one_and_longs_do_not(cfg):
    """DERIVED, NOT INHERITED. `tau_pole = sigma h / (1 + sigma (f + h))`.

    Negative for a long, so no pole at any admissible tolerance. Positive for a
    short, and it is the ratio's asymptote as the width grows without bound.
    """
    for symbol in rs.SYMBOLS:
        assert ru.pole(cfg, symbol, LONG) is None
        p = ru.pole(cfg, symbol, SHORT)
        h = cfg.haircut_bps(symbol) / 10_000.0
        assert p == pytest.approx(h / (1.0 + cfg.taker_fee + h), rel=1e-15)

        # It really is the asymptote: the short ratio approaches it from above
        # at large width and never crosses it.
        far = [ru.ratio_at_width(w, cfg, symbol, SHORT)
               for w in (1.0, 10.0, 100.0, 1000.0)]
        assert all(v > p for v in far)
        assert far[-1] == pytest.approx(p, rel=1e-2)
        assert far[0] > far[-1]

        # And a tolerance below it has no positive width on a short.
        with pytest.raises(ValueError):
            ru.required_floor_fraction(p * 0.5, cfg, symbol, SHORT)


def test_the_pole_sits_far_below_the_committed_grid(cfg):
    """So no grid cell is near it, which is why the curve is well behaved."""
    for symbol in rs.SYMBOLS:
        assert ru.pole(cfg, symbol, SHORT) < ru.TAU_GRID[0] / 10.0


# ---------------------------------------------------------------------------
# PART C. VERIFICATION AGAINST THE IMPLEMENTATION.
# ---------------------------------------------------------------------------

def test_FEEDBACK_every_solved_width_reproduces_its_own_tolerance(rows, cfg):
    """THE CENTRAL CHECK. The ratio is rebuilt from the engine at the solved
    width, never from the closed form."""
    assert len(rows) == len(ru.TAU_GRID) * len(rs.SYMBOLS) * 2
    assert ru.feedback_residual(rows) < 1e-12, ru.feedback_residual(rows)


def test_the_decomposition_closes_exactly(rows):
    """Move plus validated plus unvalidated equals the risk unit."""
    assert ru.decomposition_residual(rows) == 0.0


def test_PRICE_INVARIANCE_at_three_widely_separated_prices(cfg):
    """The width is a fraction; every term is proportional to a price."""
    assert ru.price_invariance(cfg) == 0.0


def test_the_risk_unit_is_path_twos_and_carries_funding(cfg):
    """It must exceed path one's denominator by exactly the funding term."""
    sys.path.insert(0, os.path.join(ROOT, "src", "engine"))
    import portfolio as pf
    import sizing

    entry, stop = 30_000.0, 29_400.0
    one = sizing.per_unit_denominator(entry, stop, LONG, cfg, "SOLUSDT")
    two = ru.risk_unit(entry, stop, LONG, cfg, "SOLUSDT")
    assert two - one == pytest.approx(pf.funding_per_unit(entry), rel=1e-15)


def test_funding_is_in_the_NUMERATOR_too(cfg):
    """The decision at path-and-scope §3. Zeroing the config-borne terms must
    leave the numerator equal to the funding term alone, not zero."""
    sys.path.insert(0, os.path.join(ROOT, "src", "engine"))
    import portfolio as pf

    entry, stop = 30_000.0, 29_400.0
    only_funding = replace(cfg, entry_slippage_bps=0.0,
                           stop_haircut_bps={s: 0.0
                                             for s in cfg.stop_haircut_bps})
    assert ru.unvalidated_sum(entry, stop, LONG, only_funding, "BTCUSDT") == \
        pytest.approx(pf.funding_per_unit(entry), rel=1e-15)


# ---------------------------------------------------------------------------
# THE SET PROBE.
# ---------------------------------------------------------------------------

def test_SET_PROBE_switching_entry_slippage_on_moves_everything(cfg):
    """THE SET IS A SET, NOT HARDCODED TERMS.

    Entry slippage is frozen at zero. Switched on, the numerator, the ratio and
    the solved width must ALL move -- and the new width must still reproduce its
    tolerance, so the term entered both sides consistently.
    """
    live = replace(cfg, entry_slippage_bps=5.0)
    entry, stop = 30_000.0, 29_400.0
    tau, symbol = 0.100, "BTCUSDT"

    assert ru.unvalidated_sum(entry, stop, LONG, live, symbol) > \
        ru.unvalidated_sum(entry, stop, LONG, cfg, symbol)
    assert ru.ratio_at_width(0.02, live, symbol, LONG) > \
        ru.ratio_at_width(0.02, cfg, symbol, LONG)

    base_w = ru.required_floor_fraction(tau, cfg, symbol, LONG)
    live_w = ru.required_floor_fraction(tau, live, symbol, LONG)
    assert live_w > base_w

    got = ru.solve_and_feed_back(tau, live, symbol, LONG)
    assert got["ratio"] == pytest.approx(tau, abs=1e-12)

    # And the ceiling moves with it, since A grew.
    assert ru.limit_ratio_as_width_to_zero(live, symbol) > \
        ru.limit_ratio_as_width_to_zero(cfg, symbol)


def test_SET_PROBE_an_unknown_attachment_point_RAISES(cfg, monkeypatch):
    """A term the module cannot charge must never be silently dropped."""
    with pytest.raises(ru.UnknownAttachmentPoint):
        ru.attachment_price("mark_price", 30_000.0, 29_400.0)

    monkeypatch.setitem(ru.UNVALIDATED_TERMS, "some_new_term", "mark_price")
    with pytest.raises(ru.UnknownAttachmentPoint):
        ru.unvalidated_rates(cfg, "BTCUSDT")


def test_SET_PROBE_a_known_point_with_no_rate_source_RAISES(cfg, monkeypatch):
    """Membership without a rate source is a hole, not a zero."""
    monkeypatch.setitem(ru.UNVALIDATED_TERMS, "unsourced_term", ru.ATTACH_STOP)
    with pytest.raises(KeyError):
        ru.unvalidated_rates(cfg, "BTCUSDT")


def test_every_declared_term_names_a_known_attachment_point(cfg):
    for name, point in ru.UNVALIDATED_TERMS.items():
        assert point in ru.ATTACHMENT_POINTS, name
    assert set(ru.UNVALIDATED_TERMS) == {"stop_haircut_bps",
                                         "entry_slippage_bps", "funding"}


# ---------------------------------------------------------------------------
# WHAT THE MODULE MAY NOT DO.
# ---------------------------------------------------------------------------

def test_no_execution_entry_point_and_no_data_access():
    tree = _module_ast()
    called = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            f = node.func
            name = f.attr if isinstance(f, ast.Attribute) else (
                f.id if isinstance(f, ast.Name) else None)
            if name:
                called.add(name)
    for banned in ("size_position", "run_backtest", "simulate", "read_parquet",
                   "read_table", "load_1m", "load_bars", "open", "glob"):
        assert banned not in called, banned

    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                imported.add(a.name)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module)
    for banned in ("pyarrow", "glob", "src.engine.simulate", "src.sweep"):
        assert banned not in imported, banned

    code = _code_text()
    assert "exit_reason" not in code
    assert "data/" not in code
    assert "ohlcv" not in code


def test_the_cost_algebra_is_not_reimplemented():
    """Every term reaches the module through the engine's own functions."""
    code = _code_text()
    assert "per_unit_denominator" in code
    assert "funding_per_unit" in code
    assert "move + entry" not in code
    assert "FUNDING_RATE_PER_SETTLEMENT" not in code


def test_no_tolerance_value_is_selected():
    assigned = set()
    for node in ast.walk(_module_ast()):
        if isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name):
                    assigned.add(t.id)
    for banned in ("CHOSEN_TAU", "SELECTED_TOLERANCE", "COST_TOLERANCE_R",
                   "RECOMMENDED_FLOOR", "TAU", "TOLERANCE"):
        assert banned not in assigned, banned


PERFORMANCE_NAMES = ("expectancy", "win_rate", "winrate", "profit_factor",
                     "sharpe", "sortino", "net_pnl", "gross_pnl", "drawdown",
                     "r_multiple", "equity", "pnl")


def test_the_twelve_name_firewall_is_armed_over_the_module():
    tree = _module_ast()
    docs = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef,
                             ast.ClassDef)):
            d = ast.get_docstring(node, clean=False)
            if d is not None:
                docs.add(d)
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
        elif isinstance(node, ast.arg):
            blob.add(node.arg)
        elif isinstance(node, ast.Constant) and isinstance(node.value, str):
            if node.value not in docs:
                blob.add(node.value)
    text = " ".join(blob).lower()
    for banned in PERFORMANCE_NAMES:
        assert banned not in text, banned
