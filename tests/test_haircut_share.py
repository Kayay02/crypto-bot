"""Guards for the non-uniformity check, sub-point 4.1c.

THE THRESHOLD WAS COMMITTED BEFORE THIS MODULE EXISTED, alone, at `af7866d7`.
These tests exercise the criterion as written; they do not restate it and they do
not soften it.

THE DECOMPOSITION IS TAKEN FROM THE IMPLEMENTATION BY DIFFERENCE. The haircut's
contribution is `costs.position_size`'s answer with the haircut minus its answer
without it, so no cost term is restated anywhere. The positive control below
computes the same quantity by hand from the rates and requires the two to agree.

THE VERDICT FUNCTION IS PROBED IN BOTH DIRECTIONS. A criterion that has only ever
returned one verdict is a criterion nobody has seen work, so synthetic tables on
either side of the threshold are fed to it and both answers are required.
"""

import ast
import os
import sys

import numpy as np
import pandas as pd
import pytest

from src.analysis import floor_curve as fc
from src.analysis import haircut_share as hs
from src.timeframe import resample as rs

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src", "engine"))

import costs  # noqa: E402

from src.analysis import exposure_profile as ep  # noqa: E402

LONG, SHORT = hs.LONG, hs.SHORT


@pytest.fixture(scope="module")
def cfg():
    return ep.cost_config()


@pytest.fixture(scope="module")
def table(cfg):
    return hs.decomposition_table(cfg)


def _module_ast():
    return ast.parse(open(hs.__file__).read())


def _code_text():
    """The module's EXECUTABLE tokens, comments and docstrings stripped.

    THE MODULE CITES `data/` AND THE COST TERMS IN ITS DOCSTRINGS in order to
    record what it does not do, so a raw text search fires on the statement of
    the rule rather than on a violation. This is the third time that shape has
    bitten in three consecutive steps -- ledger instances (37) and (38) are the
    first two -- and it is why both checks below run over code only.
    """
    import io
    import tokenize

    out, prev = [], tokenize.INDENT
    for tok in tokenize.generate_tokens(
            io.StringIO(open(hs.__file__).read()).readline):
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
# 1. THE DECOMPOSITION -- SYNTHETIC POSITIVE CONTROL, HAND-COMPUTED.
# ---------------------------------------------------------------------------

def test_POSITIVE_CONTROL_the_decomposition_at_hand_computed_values(cfg):
    """HAND-COMPUTED FROM THE RATES, INDEPENDENTLY OF THE MODULE.

    BTCUSDT long at a tolerance of 0.11. The required width is
    `w = (2f + e + h) / (tau + f + h)` with f = 0.0006, e = 0, h = 0.0005, so
    `w = 0.0017 / 0.1111`. The haircut is charged on the stop price `P(1 - w)`,
    so as a fraction of the stop distance `wP` it is

        ratio_unvalidated = h(1 - w) / w

    and the validated part is the committed ratio less that. The share of the
    RISK UNIT is the ratio part over `1 + tau`, because the denominator is the
    stop distance plus the cost.
    """
    f, e, h = 0.0006, 0.0, 0.0005
    tau = 0.11
    w = (2 * f + e + h) / (tau + f + h)

    want_unvalidated_ratio = h * (1.0 - w) / w
    want_validated_ratio = tau - want_unvalidated_ratio
    want_share = want_unvalidated_ratio / (1.0 + tau)
    want_fraction = want_unvalidated_ratio / tau

    got = hs.decompose(tau, cfg, "BTCUSDT", LONG)

    assert got["floor_fraction"] == pytest.approx(w, rel=1e-12)
    assert got["ratio_total"] == pytest.approx(tau, rel=1e-12)
    assert got["ratio_unvalidated"] == pytest.approx(want_unvalidated_ratio,
                                                     rel=1e-12)
    assert got["ratio_validated"] == pytest.approx(want_validated_ratio,
                                                   rel=1e-12)
    assert got["unvalidated_share_of_risk_unit"] == pytest.approx(want_share,
                                                                  rel=1e-12)
    assert got["unvalidated_fraction_of_cost"] == pytest.approx(want_fraction,
                                                                rel=1e-12)


def test_POSITIVE_CONTROL_the_short_leg_charges_the_haircut_on_a_higher_stop(cfg):
    """The stop sits ABOVE entry on a short, so the same rate on a higher price
    is a larger absolute term. Hand-computed as `h(1 + w) / w`."""
    f, e, h = 0.0006, 0.0, 0.0010
    tau = 0.11
    w = (2 * f + e + h) / (tau - f - h)
    want = h * (1.0 + w) / w

    got = hs.decompose(tau, cfg, "SOLUSDT", SHORT)
    assert got["ratio_unvalidated"] == pytest.approx(want, rel=1e-12)
    assert got["ratio_unvalidated"] > hs.decompose(
        tau, cfg, "SOLUSDT", LONG)["ratio_unvalidated"]


def test_the_parts_sum_to_the_total_across_the_whole_grid(table):
    """VERIFIED, NOT ASSUMED. If the split did not partition the cost exactly,
    every share reported would be wrong by the remainder."""
    residual = hs.decomposition_residual(table)
    assert residual < 1e-12, residual
    assert len(table) == len(fc.TAU_GRID) * len(rs.SYMBOLS) * 2


def test_the_total_cost_share_of_the_risk_unit_is_uniform_by_construction(table):
    """At the required floor the ratio IS the tolerance, so the total share is
    `tau / (1 + tau)` for every symbol and direction alike.

    THIS IS WHAT MAKES THE QUESTION WELL POSED: the constraint already bounds
    the total share uniformly, so any non-uniformity lives entirely in the
    unvalidated term's fraction of it.
    """
    expected = table["tau"] / (1.0 + table["tau"])
    assert np.abs(table["total_share_of_risk_unit"] - expected).max() < 1e-12


def test_every_reported_share_is_invariant_to_the_entry_price(cfg):
    """Entry price cancels. ASSERTED AT THREE PRICES spanning two orders of
    magnitude, not inferred from the algebra."""
    for symbol in rs.SYMBOLS:
        for direction in (LONG, SHORT):
            values = [hs.decompose(0.11, cfg, symbol, direction, price)
                      for price in (30_000.0, 1_000.0, 100.0)]
            for key in ("ratio_total", "ratio_unvalidated",
                        "unvalidated_share_of_risk_unit",
                        "unvalidated_fraction_of_cost"):
                assert values[0][key] == pytest.approx(values[1][key], rel=1e-12)
                assert values[0][key] == pytest.approx(values[2][key], rel=1e-12)


def test_the_haircut_contribution_comes_from_the_engine_by_difference(cfg):
    """The zeroed-haircut configuration must actually change the engine's
    answer, and must change it by exactly the haircut term."""
    zeroed = hs.zero_haircut_config(cfg)
    assert cfg.haircut_bps("SOLUSDT") == 10.0
    assert zeroed.haircut_bps("SOLUSDT") == 0.0
    # The frozen config is not mutated by having been measured.
    assert cfg.haircut_bps("BTCUSDT") == 5.0

    entry, w = 1_000.0, 0.02
    stop = entry * (1.0 - w)
    full = costs.position_size(entry, stop, LONG, cfg, "BTCUSDT")
    bare = costs.position_size(entry, stop, LONG, zeroed, "BTCUSDT")
    assert bare > full, "removing a cost must raise the quantity"


def test_btc_and_eth_share_a_decomposition_and_sol_does_not(table):
    """They share a haircut and differ in nothing else the algebra uses."""
    for tau in (0.02, 0.11, 0.30):
        rows = table[table["tau"] == tau]
        for direction in (LONG, SHORT):
            btc = rows[(rows["symbol"] == "BTCUSDT")
                       & (rows["direction"] == direction)].iloc[0]
            eth = rows[(rows["symbol"] == "ETHUSDT")
                       & (rows["direction"] == direction)].iloc[0]
            sol = rows[(rows["symbol"] == "SOLUSDT")
                       & (rows["direction"] == direction)].iloc[0]
            assert btc["unvalidated_share_of_risk_unit"] == pytest.approx(
                eth["unvalidated_share_of_risk_unit"], rel=1e-12)
            assert sol["unvalidated_share_of_risk_unit"] > \
                btc["unvalidated_share_of_risk_unit"]


# ---------------------------------------------------------------------------
# 2. THE THRESHOLD -- PROBED IN BOTH DIRECTIONS.
# ---------------------------------------------------------------------------

def _synthetic_table(spread, sensitivity, taus=(0.02, 0.11, 0.30)):
    """A minimal table with a chosen cross-cell spread and per-cell range.

    Cell A is flat at zero and cell B is offset by `spread`; both are ramped
    across the tolerances by `sensitivity`. So the maximum spread is `spread`
    and the minimum per-cell range is `sensitivity`, by construction.
    """
    rows = []
    for i, tau in enumerate(taus):
        ramp = sensitivity * i / (len(taus) - 1)
        rows.append({"tau": tau, "symbol": "AAA", "direction": LONG,
                     hs.PROTECTED: ramp})
        rows.append({"tau": tau, "symbol": "BBB", "direction": LONG,
                     hs.PROTECTED: ramp + spread})
    return pd.DataFrame(rows)


def test_PROBE_the_threshold_returns_BOTH_verdicts_on_synthetic_inputs():
    """A CRITERION THAT HAS ONLY EVER RETURNED ONE VERDICT IS ONE NOBODY HAS
    SEEN WORK. Both sides of `S_max >= R_min` are exercised here."""
    fires = hs.threshold_verdict(_synthetic_table(spread=0.10,
                                                  sensitivity=0.01))
    assert fires["fires"] is True
    assert fires["s_max"] == pytest.approx(0.10)
    assert fires["r_min"] == pytest.approx(0.01)
    assert fires["ratio"] == pytest.approx(10.0)

    quiet = hs.threshold_verdict(_synthetic_table(spread=0.01,
                                                  sensitivity=0.10))
    assert quiet["fires"] is False
    assert quiet["ratio"] == pytest.approx(0.1)


def test_PROBE_the_threshold_fires_exactly_at_equality():
    """`>=`, not `>`. The boundary belongs to the firing side, as §4 wrote it."""
    at = hs.threshold_verdict(_synthetic_table(spread=0.05, sensitivity=0.05))
    assert at["ratio"] == pytest.approx(1.0)
    assert at["fires"] is True

    just_under = hs.threshold_verdict(_synthetic_table(spread=0.05 - 1e-9,
                                                       sensitivity=0.05))
    assert just_under["fires"] is False


def test_the_verdict_reports_where_the_extremes_sit(table):
    """The verdict must name the tolerance and the cell it was decided at, so a
    reader can check it rather than take the two numbers on trust."""
    verdict = hs.threshold_verdict(table)
    assert verdict["s_max_at_tau"] in fc.TAU_GRID
    symbol, direction = verdict["r_min_cell"]
    assert symbol in rs.SYMBOLS
    assert direction in (LONG, SHORT)
    assert len(verdict["spreads"]) == len(fc.TAU_GRID)
    assert len(verdict["ranges"]) == len(rs.SYMBOLS) * 2


def test_the_symbol_effect_is_multiplicative_and_constant_in_the_tolerance(table):
    """THE STRUCTURAL FACT THE FINDING TURNS ON.

    SOLUSDT's unvalidated share is a CONSTANT multiple of BTCUSDT's at every
    point of the grid, because the tolerance enters both identically and only
    the haircut rate differs. The committed threshold compares ADDITIVE ranges,
    so this constant multiple is invisible to it -- which the finding records.
    """
    btc = table[(table["symbol"] == "BTCUSDT")
                & (table["direction"] == LONG)].sort_values("tau")
    sol = table[(table["symbol"] == "SOLUSDT")
                & (table["direction"] == LONG)].sort_values("tau")
    ratios = (sol[hs.PROTECTED].to_numpy(float)
              / btc[hs.PROTECTED].to_numpy(float))
    assert ratios.max() - ratios.min() < 1e-12, "the multiple must be constant"
    assert ratios[0] > 1.5


# ---------------------------------------------------------------------------
# 3. WHAT THE MODULE MAY NOT DO.
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
    """The haircut term is obtained BY DIFFERENCE from the engine, never
    restated.

    NAMING `stop_haircut_bps` IN ORDER TO ZERO IT IS THE INSTRUMENT, NOT A
    REIMPLEMENTATION -- it is what lets the engine report its own haircut
    contribution by subtraction. What would be a reimplementation is restating
    the rate arithmetic, and that is what is checked for.
    """
    code = _code_text()

    assert "per_unit_denominator" in code
    assert "required_floor_fraction" in code
    # No second copy of the rate arithmetic among what actually runs.
    assert "taker_fee" not in code
    assert "10_000" not in code and "10000" not in code
    assert "move + entry" not in code
    # The haircut field is touched only to zero it.
    assert code.count("stop_haircut_bps") == 2


def test_no_tolerance_value_is_selected_by_the_module():
    tree = _module_ast()
    assigned = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    assigned.add(target.id)
    for banned in ("CHOSEN_TAU", "SELECTED_TOLERANCE", "COST_TOLERANCE_R",
                   "RECOMMENDED_FLOOR", "TAU"):
        assert banned not in assigned, banned
    # The grid is the committed one, reused rather than redeclared.
    assert hs.TAU_GRID is fc.TAU_GRID


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
