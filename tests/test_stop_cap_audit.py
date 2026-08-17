"""Guards for report 38 -- the frozen stop cap, audited.

THE POSITIVE CONTROLS ARE HAND-COMPUTED FROM THE RATES, so the granularity
relation is checked against arithmetic rather than against itself.

THE BARRIER IS PROBED IN THE FIRING DIRECTION. A seal assertion never shown to
refuse anything is not evidence.

THE CLIPPED COUNT IS HAND-CHECKED ON A FIXTURE whose answers follow from one
multiplication each.
"""

import ast
import os
import sys

import pandas as pd
import pytest

from src.analysis import floor_curve as fc
from src.analysis import risk_unit_floor_curve as ruf
from src.analysis import stop_cap_audit as sca
from src.timeframe import resample as rs

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src", "engine"))

import sizing  # noqa: E402

from src.analysis import exposure_profile as ep  # noqa: E402

LONG, SHORT = sca.LONG, sca.SHORT


@pytest.fixture(scope="module")
def cfg():
    return ep.cost_config()


@pytest.fixture(scope="module")
def specs():
    return sizing.load_symbol_specs()


def _module_ast():
    return ast.parse(open(sca.__file__).read())


# ---------------------------------------------------------------------------
# PART 2. THE GRANULARITY RELATION.
# ---------------------------------------------------------------------------

def test_POSITIVE_CONTROL_min_lot_binding_width_hand_computed(cfg, specs):
    """HAND-COMPUTED FROM THE RATES.

        w* = ( risk_usd / (min_trade_num x entry) - A - 2f )
             / ( 1 + sigma (f + h) )

    BTCUSDT long at an entry of 30,000, min_trade_num 0.0001, risk 20:
        target unit = 20 / (0.0001 x 30000) = 20 / 3
        numerator   = 20/3 - 0.0008 - 0.0012
        denominator = 1 - 0.0011
    """
    assert specs["BTCUSDT"].min_trade_num == 0.0001
    want = (20.0 / (0.0001 * 30_000.0) - 0.0008 - 0.0012) / (1.0 - 0.0011)
    got = sca.min_lot_binding_width(cfg, "BTCUSDT", LONG, 30_000.0,
                                    specs["BTCUSDT"])
    assert got == pytest.approx(want, rel=1e-14)

    # SOLUSDT short, sigma = +1, min_trade_num 0.1.
    want_sol = (20.0 / (0.1 * 60.0) - 0.0013 - 0.0012) / (1.0 + 0.0016)
    got_sol = sca.min_lot_binding_width(cfg, "SOLUSDT", SHORT, 60.0,
                                        specs["SOLUSDT"])
    assert got_sol == pytest.approx(want_sol, rel=1e-14)


def test_the_binding_width_really_is_where_one_lot_remains(cfg, specs):
    """THE SOLVE IS CHECKED AGAINST THE QUANTITY IT CLAIMS TO SOLVE FOR.

    At the solved width the unfloored quantity must equal exactly one minimum
    lot; just inside it must exceed one, and just outside fall below.
    """
    for symbol, price in (("BTCUSDT", 30_000.0), ("ETHUSDT", 2_000.0),
                          ("SOLUSDT", 60.0)):
        for direction in (LONG, SHORT):
            w = sca.min_lot_binding_width(cfg, symbol, direction, price,
                                          specs[symbol])
            step = specs[symbol].min_trade_num
            at = sca.quantity_at_width(w, cfg, symbol, direction, price)
            assert at == pytest.approx(step, rel=1e-10), (symbol, direction)
            assert sca.quantity_at_width(w * 0.99, cfg, symbol, direction,
                                         price) > step
            assert sca.quantity_at_width(w * 1.01, cfg, symbol, direction,
                                         price) < step


def test_quantity_FALLS_as_the_stop_widens(cfg):
    """The relation the whole granularity argument rests on. Measured."""
    for symbol in rs.SYMBOLS:
        for direction in (LONG, SHORT):
            q = [sca.quantity_at_width(w, cfg, symbol, direction, 3_000.0)
                 for w in (0.005, 0.01, 0.02, 0.035, 0.08)]
            assert all(b < a for a, b in zip(q, q[1:])), (symbol, direction)


#: Each symbol's observed entry-price range over the candidate population, from
#: report 38 §3.1. The reference prices are deliberately symbol-independent, so
#: some combinations are prices a symbol never trades at; those are reported and
#: are not the finding.
OBSERVED_RANGE = {"BTCUSDT": (15_639.0, 107_284.0),
                  "ETHUSDT": (990.2, 4_066.84),
                  "SOLUSDT": (9.14, 259.90)}


def test_the_min_lot_constraint_binds_FAR_from_the_frozen_cap(cfg, specs):
    """THE FINDING, PINNED -- AT PRICES EACH SYMBOL ACTUALLY TRADES AT.

    Asserted over each symbol's own observed range rather than over the
    cross-product of symbols and reference prices, because a lot step is
    calibrated to a price scale and a symbol evaluated at another symbol's price
    is not a case the venue ever presents.
    """
    cap = cfg.stop_max_pct
    for symbol, (lo, hi) in OBSERVED_RANGE.items():
        for price in (lo, (lo + hi) / 2.0, hi):
            for direction in (LONG, SHORT):
                w = sca.min_lot_binding_width(cfg, symbol, direction, price,
                                              specs[symbol])
                assert w > 10.0 * cap, (symbol, direction, price, w)


def test_a_NEGATIVE_binding_width_means_one_lot_exceeds_the_risk_unit(cfg,
                                                                     specs):
    """AN ARTEFACT OF THE CROSS-PRODUCT, PINNED SO IT IS NOT READ AS A FINDING.

    At 95,000 a single SOLUSDT lot of 0.1 costs 9,500 of notional, and no
    positive stop width makes one lot fit inside a 20.00 risk unit. The solve
    returns a negative width, which is the correct answer to an impossible
    question. **SOLUSDT never trades near that price** -- its observed range is
    9.14 to 259.90 -- so the combination is a property of the reference grid and
    not of the venue.
    """
    w = sca.min_lot_binding_width(cfg, "SOLUSDT", LONG, 95_000.0,
                                  specs["SOLUSDT"])
    assert w < 0.0
    assert sca.quantity_at_width(0.035, cfg, "SOLUSDT", LONG, 95_000.0) < \
        specs["SOLUSDT"].min_trade_num
    # And at a price SOLUSDT does reach, one lot fits comfortably.
    assert sca.quantity_at_width(0.035, cfg, "SOLUSDT", LONG, 60.0) > \
        specs["SOLUSDT"].min_trade_num


def test_drag_reference_crossings_are_FIRST_crossings_of_a_sawtooth(cfg, specs):
    """The curve is not monotone, so the crossing is a first crossing and the
    function is required to say so rather than imply a threshold."""
    widths = [0.002 + i * 0.0005 for i in range(400)]
    out = sca.drag_reference_crossings(cfg, specs, "SOLUSDT", LONG, 60.0,
                                       (0.008, 0.0921), widths)
    assert set(out) == {0.008, 0.0921}
    for reference, hit in out.items():
        if hit is not None:
            drag = sca.granularity_drag_at_width(hit, cfg, "SOLUSDT", LONG,
                                                 60.0, specs["SOLUSDT"])
            assert drag >= reference

    # NOT MONOTONE: some later width must show LESS drag than an earlier one,
    # or "first crossing" would be an unnecessary distinction.
    series = [sca.granularity_drag_at_width(w, cfg, "SOLUSDT", LONG, 60.0,
                                            specs["SOLUSDT"])
              for w in widths]
    assert any(b < a for a, b in zip(series, series[1:]))


def test_the_module_states_no_acceptability_level(cfg, specs):
    """`drag_reference_crossings` takes its references from the caller. A
    module-level constant naming an acceptable drag would be this report
    choosing what it was told not to choose."""
    assigned = set()
    for node in ast.walk(_module_ast()):
        if isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name):
                    assigned.add(t.id)
    for banned in ("ACCEPTABLE_DRAG", "MAX_DRAG", "DRAG_LIMIT",
                   "RECOMMENDED_CAP", "CHOSEN_CAP"):
        assert banned not in assigned, banned


# ---------------------------------------------------------------------------
# PART 5. THE CLIPPED COUNT.
# ---------------------------------------------------------------------------

def _fixture_population():
    """Four candidates at an entry of 30,000, all BTCUSDT.

    The predicate is `2.25 x ATR > cap x entry`. At the frozen cap of 0.035 the
    threshold in price is 0.035 x 30,000 = 1,050, so `2.25 x ATR` must exceed
    1,050, needing ATR above 466.67.

        ATR 100 -> 2.25 x ATR =   225.0   not clipped
        ATR 400 -> 2.25 x ATR =   900.0   not clipped
        ATR 500 -> 2.25 x ATR = 1,125.0   CLIPPED
        ATR 900 -> 2.25 x ATR = 2,025.0   CLIPPED

    EXPECTED at 0.035: two clipped. At 0.070 the threshold is 2,100 and only the
    last survives it -- ATR 900 gives 2,025, which is BELOW 2,100 -- so ZERO are
    clipped, which is what makes the sensitivity direction checkable.
    """
    return pd.DataFrame({
        "symbol": ["BTCUSDT"] * 4,
        "direction": [LONG] * 4,
        "entry_price": [30_000.0] * 4,
        "atr": [100.0, 400.0, 500.0, 900.0],
    })


def test_HAND_CHECKED_clipped_count_on_a_fixture():
    frame = _fixture_population()
    assert sizing.STOP_ATR_MULT == 2.25

    at_frozen = sca.clipped_at(frame, 0.035)
    assert list(at_frozen) == [False, False, True, True]
    assert int(at_frozen.sum()) == 2

    at_double = sca.clipped_at(frame, 0.070)
    assert int(at_double.sum()) == 0

    at_tight = sca.clipped_at(frame, 0.005)
    assert int(at_tight.sum()) == 4


def test_the_clipped_count_falls_MONOTONICALLY_as_the_cap_widens():
    frame = _fixture_population()
    counts = [int(sca.clipped_at(frame, c).sum()) for c in sca.CAP_GRID]
    assert all(b <= a for a, b in zip(counts, counts[1:])), counts


def test_the_sensitivity_table_totals_reconcile():
    frame = _fixture_population()
    table = sca.sensitivity_table(frame)
    for cap in sca.CAP_GRID:
        rows = table[table["cap_fraction"] == cap]
        pooled = rows[rows["cell"] == "POOLED"]["clipped"].iloc[0]
        per_symbol = rows[rows["cell"] != "POOLED"]["clipped"].sum()
        assert pooled == per_symbol, cap


def test_clipping_is_INDEPENDENT_of_the_cost_tolerance_and_the_floor():
    """Bar geometry. `clipped_at` reads no config at all."""
    tree = _module_ast()
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == "clipped_at":
            args = [a.arg for a in node.args.args]
            assert args == ["population", "cap_fraction"], args
            names = {n.id for n in ast.walk(node) if isinstance(n, ast.Name)}
            assert "cfg" not in names
            return
    raise AssertionError("clipped_at not found")


# ---------------------------------------------------------------------------
# THE COMMITTED RANGE.
# ---------------------------------------------------------------------------

def test_the_range_spans_the_frozen_value_as_an_INTERIOR_point(cfg):
    assert len(sca.CAP_GRID) == 11
    assert sca.CAP_GRID[0] == 0.030
    assert sca.CAP_GRID[-1] == 0.080
    assert sca.CAP_GRID[0] < cfg.stop_max_pct < sca.CAP_GRID[-1]
    assert cfg.stop_max_pct in sca.CAP_GRID
    steps = {round(b - a, 10) for a, b in zip(sca.CAP_GRID, sca.CAP_GRID[1:])}
    assert steps == {sca.CAP_STEP}


# ---------------------------------------------------------------------------
# THE BARRIER.
# ---------------------------------------------------------------------------

def test_BARRIER_PROBE_the_seal_assertion_FIRES_on_a_sealed_path():
    for year in (2025, 2026):
        sealed_path = os.path.join("data", "derived", "ohlcv_1m",
                                   "symbol=SOLUSDT", "year=%d" % year,
                                   "part.parquet")
        with pytest.raises(fc.SealedPathRefused):
            fc.assert_paths_unsealed([sealed_path], "cap audit barrier probe")
    allowed = os.path.join("data", "derived", "ohlcv_1m", "symbol=SOLUSDT",
                           "year=2024", "part.parquet")
    assert fc.assert_paths_unsealed([allowed], "probe") == [allowed]


def test_the_derived_cap_reader_asserts_the_barrier_inside_its_loop():
    """Once per symbol-fold immediately before the read, not once at entry."""
    for node in ast.walk(_module_ast()):
        if isinstance(node, ast.FunctionDef) and \
                node.name == "derived_cap_table":
            calls = [n for n in ast.walk(node) if isinstance(n, ast.Call)
                     and isinstance(n.func, ast.Attribute)
                     and n.func.attr == "assert_paths_unsealed"]
            assert calls, "no barrier assertion in derived_cap_table"
            loops = [n for n in ast.walk(node) if isinstance(n, ast.For)]
            inner = [n for loop in loops for n in ast.walk(loop)
                     if isinstance(n, ast.Call)
                     and isinstance(n.func, ast.Attribute)
                     and n.func.attr == "assert_paths_unsealed"]
            assert inner, "the assertion sits outside the loop"
            return
    raise AssertionError("derived_cap_table not found")


# ---------------------------------------------------------------------------
# WHAT THE MODULE MAY NOT DO.
# ---------------------------------------------------------------------------

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


def test_the_committed_derivation_is_imported_not_restated():
    """`grid.derived_cap` is the project's rule and this module calls it."""
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
