"""The composition of the two per-unit cost denominators, asserted FROM THE CODE.

WHY THIS EXISTS. Report 34 §1.3 and closing record §3.5 make statements about
"the sizing denominator" that cannot both hold of one object. Report 35 audits
them and finds two distinct denominators. These assertions pin that finding to
the implementation so it cannot silently rot: if a funding term is ever added to
`costs.position_size`, or removed from `portfolio.size_position`, a test fails.

THEY ASSERT AGAINST THE CODE, NOT AGAINST REPORT 35's PROSE. The five terms of
the sizing path are reconstructed from the config's own rates and compared to the
engine's answer; the portfolio path's extra term is asserted over the AST of the
assignment that introduces it.

THE PORTFOLIO ENGINE IS NOT INVOKED. `portfolio.size_position` is never called.
Its denominator's composition is established structurally, over AST nodes, which
is what report 35 §2 relies on and is why that report can make the claim without
running anything.
"""

import ast
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src", "engine"))

import costs  # noqa: E402
import sizing  # noqa: E402

from src.analysis import exposure_profile as ep  # noqa: E402

LONG, SHORT = costs.LONG, costs.SHORT

COSTS_PY = os.path.join(ROOT, "src", "engine", "costs.py")
PORTFOLIO_PY = os.path.join(ROOT, "src", "engine", "portfolio.py")


@pytest.fixture(scope="module")
def cfg():
    return ep.cost_config()


def _func(path, name):
    for node in ast.walk(ast.parse(open(path).read())):
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return node
    raise AssertionError("%s not found in %s" % (name, path))


# ---------------------------------------------------------------------------
# PATH 1 -- costs.position_size, reached through sizing.per_unit_denominator.
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("symbol", ["BTCUSDT", "ETHUSDT", "SOLUSDT"])
@pytest.mark.parametrize("direction", [LONG, SHORT])
def test_the_sizing_denominator_is_EXACTLY_FIVE_TERMS(cfg, symbol, direction):
    """Reconstructed from the config's rates and compared to the engine.

        move + entry x taker + stop x taker + entry x slippage + stop x haircut

    An added or dropped term breaks the equality. The reconstruction is written
    from `src/engine/costs.py:330-336` and is deliberately a second expression of
    it, so the two can disagree.
    """
    entry = 30_000.0
    stop = entry * (1.0 - 0.02) if direction == LONG else entry * (1.0 + 0.02)
    move = abs(entry - stop)

    expected = (move
                + entry * cfg.taker_fee
                + stop * cfg.taker_fee
                + entry * cfg.entry_slippage_bps / 10_000.0
                + stop * cfg.haircut_bps(symbol) / 10_000.0)

    got = sizing.per_unit_denominator(entry, stop, direction, cfg, symbol)
    assert got == pytest.approx(expected, rel=1e-15)


def test_every_term_of_the_sizing_denominator_MOVES_IT(cfg):
    """A term nothing can perturb is a term that is not really there.

    Each rate is raised in turn and the denominator must respond. Entry slippage
    is frozen at zero, so it is exercised at a value where it is reachable --
    the treatment document 05 §4 gave the inert partial branch.
    """
    from dataclasses import replace
    entry, symbol, direction = 30_000.0, "BTCUSDT", LONG
    stop = entry * 0.98
    base = sizing.per_unit_denominator(entry, stop, direction, cfg, symbol)

    assert sizing.per_unit_denominator(
        entry, stop, direction, replace(cfg, taker_fee=cfg.taker_fee * 2),
        symbol) > base
    assert sizing.per_unit_denominator(
        entry, stop, direction, replace(cfg, entry_slippage_bps=5.0),
        symbol) > base
    assert sizing.per_unit_denominator(
        entry, stop, direction,
        replace(cfg, stop_haircut_bps=dict(cfg.stop_haircut_bps,
                                           BTCUSDT=50.0)), symbol) > base
    # The move.
    assert sizing.per_unit_denominator(entry, entry * 0.97, direction, cfg,
                                       symbol) > base


def test_the_maker_fee_is_NOT_in_the_sizing_denominator(cfg):
    """The stop leg is taker. A maker term here would mean the denomination
    named at 04_1a §5 is not what the code computes."""
    from dataclasses import replace
    entry, stop = 30_000.0, 29_400.0
    base = sizing.per_unit_denominator(entry, stop, LONG, cfg, "BTCUSDT")
    bumped = sizing.per_unit_denominator(
        entry, stop, LONG, replace(cfg, maker_fee=cfg.maker_fee * 10),
        "BTCUSDT")
    assert bumped == pytest.approx(base, rel=1e-15)


def test_NO_FUNDING_TERM_IS_REACHABLE_FROM_position_size():
    """THE CLAIM REPORT 34 §1.3 RESTS ON, asserted over the AST.

    Every name, attribute and call reachable in `costs.position_size`, plus every
    module-level name `costs.py` binds -- nothing funding-shaped exists in either.
    """
    node = _func(COSTS_PY, "position_size")
    reachable = set()
    for n in ast.walk(node):
        if isinstance(n, ast.Name):
            reachable.add(n.id)
        elif isinstance(n, ast.Attribute):
            reachable.add(n.attr)
    assert not [n for n in reachable if "funding" in n.lower()], sorted(reachable)

    module = ast.parse(open(COSTS_PY).read())
    bound = set()
    for n in ast.walk(module):
        if isinstance(n, (ast.FunctionDef, ast.ClassDef)):
            bound.add(n.name)
        elif isinstance(n, ast.Name) and isinstance(n.ctx, ast.Store):
            bound.add(n.id)
        elif isinstance(n, ast.arg):
            bound.add(n.arg)
        elif isinstance(n, ast.AnnAssign) and isinstance(n.target, ast.Name):
            bound.add(n.target.id)
    assert not [n for n in bound if "funding" in n.lower()], sorted(bound)


def test_per_unit_denominator_ADDS_NOTHING_to_position_size(cfg):
    """`sizing.per_unit_denominator` is `risk_usd / position_size`, so the two
    carry identical terms. A term added in `sizing.py` would break this."""
    entry, stop, symbol = 30_000.0, 29_400.0, "SOLUSDT"
    qty = costs.position_size(entry, stop, LONG, cfg, symbol)
    assert sizing.per_unit_denominator(entry, stop, LONG, cfg, symbol) == \
        pytest.approx(cfg.risk_usd / qty, rel=1e-15)


# ---------------------------------------------------------------------------
# PATH 2 -- portfolio.size_position. STRUCTURAL ONLY; NOTHING IS INVOKED.
# ---------------------------------------------------------------------------

def test_the_portfolio_denominator_is_PATH_ONE_PLUS_FUNDING():
    """Asserted over the AST of the assignment, not by running the engine.

    The statement must be `denominator = <call to per_unit_denominator> +
    <funding name>`. This is the whole of the difference between the two paths
    and report 35 §2 turns on it.
    """
    node = _func(PORTFOLIO_PY, "size_position")
    found = None
    for n in ast.walk(node):
        if (isinstance(n, ast.Assign) and len(n.targets) == 1
                and isinstance(n.targets[0], ast.Name)
                and n.targets[0].id == "denominator"):
            found = n.value
    assert found is not None, "no denominator assignment in size_position"

    assert isinstance(found, ast.BinOp) and isinstance(found.op, ast.Add), \
        ast.dump(found)

    left, right = found.left, found.right
    assert isinstance(left, ast.Call)
    assert isinstance(left.func, ast.Attribute)
    assert left.func.attr == "per_unit_denominator"
    assert isinstance(right, ast.Name) and "funding" in right.id.lower()


def test_the_funding_term_is_price_times_rate_times_count():
    """`entry x rate x count`, from the constants, with no back-solve.

    Called directly -- it is one multiplication over three scalars and reads no
    bar, opens no file and resolves no exit.
    """
    from src.risk import exit_spec as es
    sys.path.insert(0, os.path.join(ROOT, "src", "engine"))
    import portfolio as pf

    entry = 30_000.0
    assert pf.funding_per_unit(entry) == pytest.approx(
        entry * es.FUNDING_RATE_PER_SETTLEMENT
        * es.FUNDING_SETTLEMENTS_CHARGED, rel=1e-15)
    assert es.FUNDING_SETTLEMENTS_CHARGED == 3
    assert es.FUNDING_RATE_PER_SETTLEMENT == 0.0001

    # It does not depend on quantity, the stop, or the symbol.
    assert pf.funding_per_unit(2 * entry) == pytest.approx(
        2 * pf.funding_per_unit(entry), rel=1e-15)


def test_the_two_paths_differ_by_the_funding_term_AND_BY_NOTHING_ELSE(cfg):
    """Arithmetic, not invocation: path 1's denominator plus the funding term is
    what the AST above shows `size_position` assigns."""
    sys.path.insert(0, os.path.join(ROOT, "src", "engine"))
    import portfolio as pf

    entry, stop, symbol = 30_000.0, 29_400.0, "SOLUSDT"
    one = sizing.per_unit_denominator(entry, stop, LONG, cfg, symbol)
    two = one + pf.funding_per_unit(entry)
    assert two > one
    assert two - one == pytest.approx(entry * 0.0001 * 3, rel=1e-15)


# ---------------------------------------------------------------------------
# WHICH PATH THE COST-TOLERANCE CONSTRAINT IS MEASURED AGAINST.
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("module_path", [
    "src/analysis/haircut_floor_curve.py",
    "src/analysis/haircut_share.py",
    "src/analysis/haircut_share_rerun.py",
])
def test_the_constraint_chain_calls_PATH_ONE_and_never_PATH_TWO(module_path):
    """The 4.1a / report 33 / report 34 chain reaches the denominator through
    `per_unit_denominator` alone. If one of them ever routes through the
    portfolio path instead, report 35 §2's reconciliation stops holding."""
    tree = ast.parse(open(os.path.join(ROOT, module_path)).read())
    called = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Call):
            f = n.func
            name = f.attr if isinstance(f, ast.Attribute) else (
                f.id if isinstance(f, ast.Name) else None)
            if name:
                called.add(name)
    assert "per_unit_denominator" in called
    assert "size_position" not in called
    assert "funding_per_unit" not in called
    assert not [c for c in called if "funding" in c.lower()], sorted(called)
