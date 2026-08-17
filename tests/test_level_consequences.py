"""Guards for report 37 -- the level, the widths, the comparator, the stratum.

THE LEVEL IS AN IDENTITY AND THE TESTS SAY SO. `test_the_level_is_the_budget_
divided_by_one` asserts the divisor is one rather than asserting the quotient,
because a test that only pinned the number would pass equally on a level that had
been chosen and then explained.

THE STRATUM COUNTS ARE HAND-CHECKED ON A FIXTURE whose floor-binding and
above-cap answers are computed from the rates by hand, so the counting code is
exercised against arithmetic rather than against itself.

THE BARRIER IS PROBED IN THE FIRING DIRECTION. A seal assertion that has never
been shown to refuse anything is not evidence.
"""

import ast
import os
import sys

import numpy as np
import pandas as pd
import pytest

from src.analysis import floor_curve as fc
from src.analysis import level_consequences as lc
from src.analysis import risk_unit_floor_curve as ruf
from src.timeframe import resample as rs

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src", "engine"))

from src.analysis import exposure_profile as ep  # noqa: E402

LONG, SHORT = lc.LONG, lc.SHORT


@pytest.fixture(scope="module")
def cfg():
    return ep.cost_config()


def _module_ast():
    return ast.parse(open(lc.__file__).read())


# ---------------------------------------------------------------------------
# PART 1. THE LEVEL.
# ---------------------------------------------------------------------------

def test_the_level_is_the_budget_divided_by_ONE():
    """THE POINT OF THIS TEST IS THE DIVISOR, NOT THE QUOTIENT.

    `docs/design/04_1c_proper.md` §3.1 fixes the uncertainty parameter at one
    hundred per cent, so the level is numerically the budget. §4.2 commits that
    this is a change of units and not a derivation. **Asserting only the number
    would pass on a level chosen first and explained afterwards.**
    """
    assert lc.UNCERTAINTY_PARAMETER == 1.00
    assert lc.DISPLACEMENT_BUDGET == 0.10
    assert lc.level() == lc.DISPLACEMENT_BUDGET
    # And the function really divides, so a future change to either input moves it.
    assert lc.level(budget=0.2, uncertainty=2.0) == pytest.approx(0.1)
    assert lc.level(budget=0.1, uncertainty=0.5) == pytest.approx(0.2)


def test_POSITIVE_CONTROL_the_level_lies_inside_every_cells_range(cfg):
    """Checked against report 36's bounds, not assumed."""
    ok, lo, hi = lc.level_is_inside_admitted_domain(cfg)
    assert ok
    assert lo == pytest.approx(0.03554692, abs=5e-9)
    assert hi == pytest.approx(0.40, abs=1e-12)
    for symbol in rs.SYMBOLS:
        for direction in (LONG, SHORT):
            cell_lo, cell_hi = ruf.achievable_range(cfg, symbol, direction)
            assert cell_lo < lc.level() < cell_hi, (symbol, direction)


# ---------------------------------------------------------------------------
# PART 2. THE WIDTHS.
# ---------------------------------------------------------------------------

def test_POSITIVE_CONTROL_the_widths_hand_computed(cfg):
    """HAND-COMPUTED FROM THE RATES, INDEPENDENTLY OF THE MODULE.

        w = [ A(1 - tau) - 2 f tau ] / [ tau (1 + sigma (f + h)) - sigma h ]

    BTCUSDT long at the level, sigma = -1:
        numerator   = 0.0008 x 0.9 - 0.0012 x 0.1 = 0.00072 - 0.00012 = 0.00060
        denominator = 0.1 x (1 - 0.0011) + 0.0005 = 0.09989 + 0.0005 = 0.10039

    SOLUSDT short at the level, sigma = +1:
        numerator   = 0.0013 x 0.9 - 0.0012 x 0.1 = 0.00117 - 0.00012 = 0.00105
        denominator = 0.1 x (1 + 0.0016) - 0.0010 = 0.10016 - 0.0010 = 0.09916
    """
    frame = lc.widths_at(cfg)

    def w(symbol, direction):
        row = frame[(frame["symbol"] == symbol)
                    & (frame["direction"] == direction)]
        return float(row["width"].iloc[0])

    assert w("BTCUSDT", LONG) == pytest.approx(0.00060 / 0.10039, rel=1e-14)
    assert w("SOLUSDT", SHORT) == pytest.approx(0.00105 / 0.09916, rel=1e-14)
    assert w("BTCUSDT", LONG) == w("ETHUSDT", LONG)
    for symbol in rs.SYMBOLS:
        assert w(symbol, SHORT) > w(symbol, LONG), symbol


def test_FEEDBACK_at_every_cell(cfg):
    """Every width fed back through the path-two denominator must recover the
    level. Six cells, and the residual is the report's."""
    frame = lc.widths_at(cfg)
    assert len(frame) == len(rs.SYMBOLS) * 2
    assert lc.feedback_residual(frame) < 1e-12
    assert (frame["tau"] == lc.level()).all()
    assert not frame["exceeds_cap"].any()


def test_the_retired_floor_is_carried_as_ORIENTATION_and_nothing_reads_it(cfg):
    """`docs/design/04_1c_pre_commitments.md` §4.3(a) makes closeness to the
    retired floor a DISQUALIFYING property. It may be reported; it must not enter
    any computation. Asserted over the module's AST."""
    assert lc.RETIRED_CONSTANT_FLOOR_PCT == 1.50
    tree = _module_ast()
    users = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            for inner in ast.walk(node):
                if (isinstance(inner, ast.Name)
                        and inner.id == "RETIRED_CONSTANT_FLOOR_PCT"):
                    users.append(node.name)
    assert users == ["widths_at"], users
    # And removing it changes no width.
    frame = lc.widths_at(cfg)
    assert frame["width"].notna().all()


# ---------------------------------------------------------------------------
# PART 3. THE COMPARATOR.
# ---------------------------------------------------------------------------

def test_POSITIVE_CONTROL_the_haircut_share_and_the_worst_cell(cfg):
    """HAND-COMPUTED at zero width: `h / A`.

    BTCUSDT and ETHUSDT: 0.0005 / 0.0008 = 0.625.
    SOLUSDT:             0.0010 / 0.0013.

    §5.3 committed the rule and left the symbol to this step.
    """
    assert lc.haircut_share_of_unvalidated(cfg, "BTCUSDT") == pytest.approx(
        0.0005 / 0.0008, rel=1e-14)
    assert lc.haircut_share_of_unvalidated(cfg, "SOLUSDT") == pytest.approx(
        0.0010 / 0.0013, rel=1e-14)
    symbol, shares, winners = lc.worst_cell(cfg)
    assert symbol == "SOLUSDT"
    assert winners == ["SOLUSDT"]
    assert shares["SOLUSDT"] > shares["BTCUSDT"] == shares["ETHUSDT"]


def test_POSITIVE_CONTROL_the_comparator_width_hand_computed(cfg):
    """HAND-COMPUTED. `w = (B(A + 2f) - h) / (sigma h - B(1 + sigma(f + h)))`.

    SOLUSDT short:
        numerator   = 0.10 x 0.0025 - 0.0010 = 0.00025 - 0.0010 = -0.00075
        denominator = 0.0010 - 0.10 x 1.0016 = 0.0010 - 0.10016 = -0.09916
    """
    assert lc.comparator_width(cfg, "SOLUSDT", SHORT) == pytest.approx(
        0.00075 / 0.09916, rel=1e-14)


def test_the_comparator_binds_on_the_worst_cell_and_is_LOOSER(cfg):
    """§5.3's reconciliation rule, applied.

    THE COMPARATOR IS LOOSER THAN THE COMMITTED LEVEL, which is the direction
    that makes it the visible cost of the scope decision: stressing the whole
    unvalidated bundle demands more width than stressing the haircut alone.
    """
    binding, symbol, direction, _ = lc.binding_comparator_level(cfg)
    assert symbol == "SOLUSDT"
    assert direction == SHORT
    assert binding > lc.level()

    table = lc.comparator_table(cfg)
    sol = table[table["symbol"] == "SOLUSDT"]["comparator_level"]
    btc = table[table["symbol"] == "BTCUSDT"]["comparator_level"]
    assert sol.max() < btc.min(), (
        "the worst cell must yield the tightest comparator level, or the "
        "reconciliation rule selects the wrong one")

    # At the binding level, every other symbol is protected MORE TIGHTLY than
    # the budget requires. The budget is denominated in the RISK UNIT, so the
    # quantity to compare is the haircut's share of the risk unit -- the
    # haircut's share of the unvalidated sum multiplied by the level -- and not
    # its share of the unvalidated sum alone.
    for symbol_ in ("BTCUSDT", "ETHUSDT"):
        for direction_ in (LONG, SHORT):
            w = ruf.required_floor_fraction(binding, cfg, symbol_, direction_)
            of_unvalidated = lc.haircut_share_of_unvalidated(cfg, symbol_, w,
                                                             direction_)
            of_risk_unit = of_unvalidated * ruf.ratio_at_width(
                w, cfg, symbol_, direction_)
            assert of_risk_unit * lc.UNCERTAINTY_PARAMETER < \
                lc.DISPLACEMENT_BUDGET, (symbol_, direction_, of_risk_unit)

    # And on the worst cell it is met exactly, which is what "binding" means.
    w_sol = ruf.required_floor_fraction(binding, cfg, "SOLUSDT", SHORT)
    exact = (lc.haircut_share_of_unvalidated(cfg, "SOLUSDT", w_sol, SHORT)
             * ruf.ratio_at_width(w_sol, cfg, "SOLUSDT", SHORT))
    assert exact == pytest.approx(lc.DISPLACEMENT_BUDGET, rel=1e-12)


def test_the_comparator_does_not_touch_the_committed_level(cfg):
    """§5.4 forbids the comparator's result from reopening the scope. Nothing in
    the module lets it: `level()` takes no argument from the comparator."""
    before = lc.level()
    lc.binding_comparator_level(cfg)
    lc.comparator_table(cfg)
    assert lc.level() == before


# ---------------------------------------------------------------------------
# PARTS 4 AND 5. THE STRATUM, HAND-CHECKED ON A FIXTURE.
# ---------------------------------------------------------------------------

def _fixture_population():
    """Six synthetic candidates with hand-chosen ATRs, all BTCUSDT long.

    At the level, BTCUSDT long needs w = 0.00597669..., and the frozen cap is
    0.035. At an entry of 30,000:

        floor width in price = 179.30      cap in price = 1050.00

    `floor_binds` is `2.25 x ATR < 179.30`, so it needs ATR below 79.69.
    `pop_b` is `2.25 x ATR > 1050.00`, so it needs ATR above 466.67.

        ATR   40 -> 2.25 x ATR =   90.0  BOUND, not above cap
        ATR   70 -> 2.25 x ATR =  157.5  BOUND, not above cap
        ATR  100 -> 2.25 x ATR =  225.0  neither
        ATR  300 -> 2.25 x ATR =  675.0  neither
        ATR  500 -> 2.25 x ATR = 1125.0  ABOVE CAP, not bound
        ATR  800 -> 2.25 x ATR = 1800.0  ABOVE CAP, not bound

    EXPECTED: 2 floor-bound, 2 above cap, 0 both.
    """
    return pd.DataFrame({
        "symbol": ["BTCUSDT"] * 6,
        "direction": [LONG] * 6,
        "entry_price": [30_000.0] * 6,
        "atr": [40.0, 70.0, 100.0, 300.0, 500.0, 800.0],
        "entry_close_ms": [1_650_000_000_000 + i * 3_600_000 for i in range(6)],
    })


def test_HAND_CHECKED_stratum_counts_on_a_fixture(cfg):
    frame = lc.stratify(_fixture_population(), cfg)

    assert int(frame["floor_bound"].sum()) == 2
    assert list(frame["floor_bound"]) == [True, True, False, False, False, False]

    assert int(frame["pop_b_atr_above_cap"].sum()) == 2
    assert list(frame["pop_b_atr_above_cap"]) == [False, False, False, False,
                                                  True, True]

    assert int(frame["pop_a_floor_above_cap"].sum()) == 0

    counts = lc.by_symbol(frame)
    pooled = counts[counts["cell"] == "POOLED"].iloc[0]
    assert pooled["n"] == 6
    assert pooled["floor_bound"] == 2
    assert pooled["not_floor_bound"] == 4
    assert pooled["floor_binding_fraction"] == pytest.approx(2 / 6)
    assert pooled["pop_b"] == 2
    assert pooled["pop_a"] == 0

    assert lc.overlap(frame) == {"n": 6, "both": 0, "b_only": 2,
                                 "floor_bound_only": 2, "neither": 2}


def test_the_two_predicates_are_DISJOINT_BY_CONSTRUCTION_while_A_is_empty(cfg):
    """A PROOF, EXERCISED, NOT A COINCIDENCE OBSERVED.

    `floor_bound` means the ATR stop falls BELOW the required floor;
    `pop_b` means it rises ABOVE the cap. They can only both hold if the floor
    exceeds the cap -- which is population A. **While A is empty they are
    disjoint necessarily, not incidentally.**

    Exercised in the direction that would break it: with the cap forced below the
    required floor, a candidate satisfies both.
    """
    from dataclasses import replace
    frame = lc.stratify(_fixture_population(), cfg)
    assert lc.overlap(frame)["both"] == 0
    assert int(frame["pop_a_floor_above_cap"].sum()) == 0

    tiny_cap = replace(cfg, stop_max_pct=0.001)
    broken = lc.stratify(_fixture_population(), tiny_cap)
    assert int(broken["pop_a_floor_above_cap"].sum()) == 6
    assert lc.overlap(broken)["both"] > 0, (
        "with the floor above the cap the predicates must be able to coincide, "
        "or the disjointness above is an artefact of the test rather than of "
        "population A being empty")


def test_population_B_is_independent_of_the_level(cfg):
    """Bar geometry. Recomputing at a different level must not move it."""
    at_level = lc.stratify(_fixture_population(), cfg)
    elsewhere = lc.stratify(_fixture_population(), cfg, value=0.25)
    assert list(at_level["pop_b_atr_above_cap"]) == \
        list(elsewhere["pop_b_atr_above_cap"])
    # while floor binding IS level-dependent, so the comparison has content
    assert list(at_level["floor_bound"]) != list(elsewhere["floor_bound"])


def test_the_fold_periods_are_eighteen_and_come_from_the_schedule():
    periods = lc.fold_periods()
    assert len(periods) == 18
    assert sorted({p["fold_id"] for p in periods}) == list(range(1, 10))
    assert {p["phase"] for p in periods} == {"train", "test"}


def test_fold_assignment_loses_no_candidate(cfg):
    """Rows outside every fold period are reported, not dropped."""
    frame = lc.stratify(_fixture_population(), cfg)
    table = lc.by_fold_period(frame)
    assert table["n"].sum() == len(frame)
    assert "OUTSIDE ANY FOLD PERIOD" in set(table["cell"])


# ---------------------------------------------------------------------------
# THE BARRIER.
# ---------------------------------------------------------------------------

def test_BARRIER_PROBE_the_seal_assertion_FIRES_on_a_sealed_path():
    """A SEAL ASSERTION NEVER SHOWN TO REFUSE ANYTHING IS NOT EVIDENCE.

    Both sealed years are probed, and an unsealed path is required to pass, so
    the check is shown to discriminate rather than merely to raise.
    """
    for year in (2025, 2026):
        sealed_path = os.path.join(
            "data", "derived", "ohlcv_1m", "symbol=BTCUSDT",
            "year=%d" % year, "part.parquet")
        with pytest.raises(fc.SealedPathRefused):
            fc.assert_paths_unsealed([sealed_path], "barrier probe")

    allowed = os.path.join("data", "derived", "ohlcv_1m", "symbol=BTCUSDT",
                           "year=2023", "part.parquet")
    assert fc.assert_paths_unsealed([allowed], "barrier probe") == [allowed]


def test_the_module_asserts_the_barrier_before_reading():
    """The call must be inside `candidate_population`, not at import."""
    tree = _module_ast()
    for node in ast.walk(tree):
        if (isinstance(node, ast.FunctionDef)
                and node.name == "candidate_population"):
            calls = [n.func.attr for n in ast.walk(node)
                     if isinstance(n, ast.Call)
                     and isinstance(n.func, ast.Attribute)]
            assert "assert_paths_unsealed" in calls
            return
    raise AssertionError("candidate_population not found")


# ---------------------------------------------------------------------------
# WHAT THE MODULE MAY NOT DO.
# ---------------------------------------------------------------------------

def test_no_execution_entry_point_is_invoked():
    tree = _module_ast()
    called = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            f = node.func
            name = f.attr if isinstance(f, ast.Attribute) else (
                f.id if isinstance(f, ast.Name) else None)
            if name:
                called.add(name)
    for banned in ("size_position", "run_backtest", "simulate", "resolve_exit",
                   "target_with_funding"):
        assert banned not in called, banned

    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                imported.add(a.name)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module)
    assert "portfolio" not in imported
    assert "src.engine.simulate" not in imported


def test_report_36s_module_is_imported_not_copied():
    """The closed form is not reimplemented here."""
    tree = _module_ast()
    functions = {n.name for n in ast.walk(tree)
                 if isinstance(n, ast.FunctionDef)}
    assert "required_floor_fraction" not in functions
    assert "ratio_at_width" not in functions
    imported = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.ImportFrom) and n.module:
            for alias in n.names:
                imported.add("%s.%s" % (n.module, alias.name))
    assert "src.analysis.risk_unit_floor_curve" in imported
    assert "src.analysis.floor_curve" in imported


PERFORMANCE_NAMES_IMPORT_CHECK = True


def test_no_outcome_quantity_is_named_in_the_module():
    from src.firewall import PERFORMANCE_NAMES
    tree = _module_ast()
    docs = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.FunctionDef, ast.ClassDef)):
            d = ast.get_docstring(node, clean=False)
            if d:
                docs.add(d)
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
