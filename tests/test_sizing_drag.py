"""Guards for the flooring-drag measurement.

THE POSITION TABLE IS REPORT 24'S AND REPORT 26'S, NOT A NEW ONE. If the
population diverged -- a different warm-up, a different signal definition, a
dropped two-sided bar -- every drag figure would be a ratio against a different
denominator and would still look entirely reasonable. The counts are therefore
asserted against 11,384 and 6,021 exactly.

THE THREE LOSS FRACTIONS ARE ONE NUMBER. Flooring scales quantity, notional and
realised risk by the same factor, so `drag_fraction`, `qty_lost_fraction` and
`notional_lost_fraction` are identical per position. That is asserted rather
than left for a reader to assume they are three independent measurements -- and
it is why the POOLED figures differ: risk is equally weighted and notional is
not.

THE TICK IS A SCHEDULE. SOLUSDT changed grid inside the window, so a test
asserts the tick actually used differs across that boundary. Using one tick per
symbol would round two and a half years of SOL levels onto the wrong grid and
nothing downstream would notice.
"""

import ast
import datetime as dt
import os

import numpy as np
import pandas as pd
import pytest

from src.analysis import budget_cost as bc
from src.analysis import sizing_drag as sd
from src.timeframe import resample as rs

import sys  # noqa: E402
sys.path.insert(0, os.path.join(rs.ROOT, "src", "engine"))

import sizing  # noqa: E402


REPORT_24_POSITIONS = {"BTCUSDT": 3735, "ETHUSDT": 3715, "SOLUSDT": 3934}
REPORT_24_TOTAL = 11_384
REPORT_26_TAKEN = 6_021

#: Report 24 §2.2's notional-weighted flooring loss, the figure this step must
#: reproduce on the same population.
REPORT_24_NOTIONAL_LOST = {"BTCUSDT": 0.002063, "ETHUSDT": 0.012639,
                           "SOLUSDT": 0.006668}

SOL_TICK_CHANGE_MS = 1_723_608_300_000  # 2024-08-14T04:05:00Z


@pytest.fixture(scope="module")
def measured():
    return sd.measure()


def _module_ast():
    return ast.parse(open(sd.__file__).read())


def _hand_frame(rows):
    return pd.DataFrame(rows, columns=["ts", "symbol", "direction",
                                       "entry_price", "atr", "taken"])


# ---------------------------------------------------------------------------
# 1. SYNTHETIC POSITIVE CONTROL -- hand arithmetic, element by element.
# ---------------------------------------------------------------------------

def test_positive_control_the_drag_is_the_hand_computed_one():
    """THE CONTROL. Two positions whose flooring is computed by hand.

    SOLUSDT LONG, entry 100.0, ATR 1.0, after the 2024 tick change so the grid
    is 0.001 and the quantity step is 0.1:

        stop distance  max(2.25 x 1.0, 1.50% x 100) = 2.25   (ATR term wins)
        stop price     100 - 2.25 = 97.75, already on the grid
        denominator    2.25 + 100 x 0.0006 + 97.75 x 0.0006 + 97.75 x 0.0010
                       = 2.25 + 0.06 + 0.05865 + 0.09775 = 2.46640
        unfloored      20 / 2.46640 = 8.108985...
        FLOORED        8.1
        realised       8.1 x 2.46640 = 19.977840
        drag           (20 - 19.977840) / 20 = 0.0011080

    BTCUSDT LONG, entry 30000.0, ATR 300.0, grid 0.1, step 0.0001:

        denominator    675 + 18 + 17.595 + 14.6625 = 725.2575
        unfloored      20 / 725.2575 = 0.02757617...
        FLOORED        0.0275
        realised       0.0275 x 725.2575 = 19.94458125
        drag           (20 - 19.94458125) / 20 = 0.0027709375

    Asserted element by element, not as an aggregate.
    """
    after = SOL_TICK_CHANGE_MS + 3_600_000
    frame = _hand_frame([
        (after, "SOLUSDT", "long", 100.0, 1.0, True),
        (after, "BTCUSDT", "long", 30_000.0, 300.0, True),
    ])
    out = sd.size_population(frame)
    assert len(out) == 2

    sol = out.iloc[0]
    assert sol["price_tick"] == pytest.approx(0.001)
    assert sol["qty_step"] == pytest.approx(0.1)
    assert sol["stop_price"] == pytest.approx(97.75)
    assert sol["denominator"] == pytest.approx(2.46640, rel=1e-12)
    assert sol["qty_unfloored"] == pytest.approx(20.0 / 2.46640, rel=1e-12)
    assert sol["qty"] == pytest.approx(8.1)
    assert sol["realised_risk_usd"] == pytest.approx(19.977840, rel=1e-12)
    assert sol["drag_fraction"] == pytest.approx(0.0011080, rel=1e-6)
    assert sol["notional"] == pytest.approx(810.0)

    btc = out.iloc[1]
    assert btc["price_tick"] == pytest.approx(0.1)
    assert btc["qty_step"] == pytest.approx(0.0001)
    assert btc["denominator"] == pytest.approx(725.2575, rel=1e-12)
    assert btc["qty"] == pytest.approx(0.0275)
    assert btc["realised_risk_usd"] == pytest.approx(19.94458125, rel=1e-12)
    assert btc["drag_fraction"] == pytest.approx(0.0027709375, rel=1e-9)

    totals = sd.drag_totals(out)
    assert totals["nominal_total"] == pytest.approx(40.0)
    assert totals["drag_total"] == pytest.approx(
        (20.0 - 19.977840) + (20.0 - 19.94458125), rel=1e-9)


def test_positive_control_the_tick_is_resolved_per_bar_not_per_symbol():
    """SOLUSDT changed grid on 2024-08-14. THE SAME POSITION MUST SIZE
    DIFFERENTLY ON EITHER SIDE OF IT, or the schedule is not being read."""
    before = SOL_TICK_CHANGE_MS - 3_600_000
    after = SOL_TICK_CHANGE_MS + 3_600_000
    out = sd.size_population(_hand_frame([
        (before, "SOLUSDT", "long", 100.0, 1.0, True),
        (after, "SOLUSDT", "long", 100.0, 1.0, True),
    ]))
    assert out.iloc[0]["price_tick"] == pytest.approx(0.0001)
    assert out.iloc[1]["price_tick"] == pytest.approx(0.001)
    assert out.iloc[0]["price_tick"] != out.iloc[1]["price_tick"]


# ---------------------------------------------------------------------------
# 2. SYNTHETIC NEGATIVE CONTROL.
# ---------------------------------------------------------------------------

def test_negative_control_an_empty_population_produces_zero_rows():
    """ZERO ROWS, not a silent success with an empty aggregate."""
    empty = _hand_frame([])
    out = sd.size_population(empty)
    assert len(out) == 0
    assert list(out.columns) == list(sd.COLUMNS)

    prof = sd.profile(out)
    assert prof["n"] == 0
    assert prof["viability"]["n"] == 0
    assert prof["viability"][sizing.BELOW_MIN_QTY] == 0
    assert prof["totals"]["n"] == 0
    assert prof["totals"]["drag_total"] == 0.0
    assert np.isnan(prof["realised_risk_usd"]["mean"])
    assert np.isnan(prof["cost_ratio"]["fraction_above_tolerance"])


# ---------------------------------------------------------------------------
# 3. THE POPULATION IDENTITY.
# ---------------------------------------------------------------------------

def test_the_population_is_report_24s_and_report_26s(measured):
    """A DIVERGENCE HERE WOULD MAKE EVERY DRAG FIGURE A RATIO OF TWO DIFFERENT
    THINGS while still looking entirely reasonable."""
    sized = measured["sized"]
    assert len(sized) == REPORT_24_TOTAL
    assert int(sized["taken"].sum()) == REPORT_26_TAKEN
    for symbol, expected in REPORT_24_POSITIONS.items():
        assert int((sized["symbol"] == symbol).sum()) == expected, symbol
    assert measured["populations"]["candidates"]["n"] == REPORT_24_TOTAL
    assert measured["populations"]["taken"]["n"] == REPORT_26_TAKEN


def test_the_risk_unit_is_the_frozen_one_reached_through_budget_cost(measured):
    """NOT RETYPED. `budget_cost.UNIT_USD` is the frozen constant's own object,
    and this module reaches it through the one module permitted to hold it."""
    assert sd.RISK_USD is bc.UNIT_USD
    assert sd.RISK_USD == 20.0
    assert measured["risk_usd"] == 20.0
    assert measured["reward_to_risk"] == 1.5
    assert sd.REWARD_TO_RISK is sizing.REWARD_TO_RISK
    # And the module does not name the risk package's dotted path.
    src = open(sd.__file__).read()
    assert "src.risk" not in src


# ---------------------------------------------------------------------------
# 4. THE INVARIANTS ON THE REAL RUN.
# ---------------------------------------------------------------------------

def test_the_three_loss_fractions_are_one_number(measured):
    """Flooring scales quantity, notional and realised risk by the SAME factor.

    Asserted so nobody reads them as three independent measurements -- and so
    the pooled forms, which do differ because one is notional-weighted, are
    understood as a weighting difference rather than a measurement difference.
    """
    sized = measured["sized"]
    a = sized["drag_fraction"].to_numpy(float)
    b = sized["qty_lost_fraction"].to_numpy(float)
    c = sized["notional_lost_fraction"].to_numpy(float)
    assert float(np.abs(a - b).max()) < 1e-12
    assert float(np.abs(a - c).max()) < 1e-12


def test_realised_risk_never_exceeds_nominal_on_any_position(measured):
    sized = measured["sized"]
    assert float((sized["realised_risk_usd"] - sized["nominal_risk_usd"]).max()) \
        <= 1e-12
    assert float(sized["realised_risk_usd"].min()) > 0.0
    assert float(sized["drag_fraction"].min()) >= 0.0
    assert bool((sized["qty"] <= sized["qty_unfloored"] + 1e-15).all())


def test_every_quantity_is_a_whole_multiple_of_its_step(measured):
    sized = measured["sized"]
    steps = sized["qty"].to_numpy(float) / sized["qty_step"].to_numpy(float)
    assert float(np.abs(steps - np.round(steps)).max()) < 1e-9


def test_no_position_fails_either_viability_condition(measured):
    """EXPECTED ZERO ON BOTH, AND REPORTED AS ZERO rather than omitted."""
    for name in ("candidates", "taken"):
        v = measured["populations"][name]["viability"]
        assert v[sizing.BELOW_MIN_QTY] == 0, name
        assert v[sizing.BELOW_MIN_NOTIONAL] == 0, name
        assert v["n_viable"] == v["n"], name


def test_the_weighted_notional_loss_reproduces_report_24(measured):
    """THE CROSS-CHECK AGAINST A CLOSED REPORT.

    Report 24 §2.2 measured the NOTIONAL-WEIGHTED flooring loss. It is
    reproduced here to within a few thousandths of a percentage point; the
    residual is the effect of recomputing the denominator from the TICK-ROUNDED
    stop, which report 24 did not do because it applied no tick rounding.
    """
    for symbol, expected in REPORT_24_NOTIONAL_LOST.items():
        got = measured["per_symbol"]["candidates"][symbol]["totals"][
            "notional_lost_weighted"]
        assert got == pytest.approx(expected, abs=0.0005), (symbol, got,
                                                            expected)
        assert got > expected, (
            "the tick-rounded stop is wider, so the quantity is smaller and "
            "the loss slightly larger", symbol)


def test_the_worst_single_position_matches_report_24(measured):
    """Report 24 §2.2's worst single position was 9.21% on ETHUSDT."""
    eth = measured["per_symbol"]["candidates"]["ETHUSDT"]
    assert eth["drag_fraction"]["max"] == pytest.approx(0.0921, abs=0.0005)
    for symbol in ("BTCUSDT", "SOLUSDT"):
        worst = measured["per_symbol"]["candidates"][symbol][
            "drag_fraction"]["max"]
        assert worst < eth["drag_fraction"]["max"], symbol


def test_the_cost_ratio_is_measured_and_the_floor_bound_stratum_is_above(
        measured):
    """`c/s` AGAINST THE FROZEN 0.11 TOLERANCE. Reported, not resolved.

    Every floor-bound position exceeds the tolerance -- at a 1.50% stop the
    charged round trip is 0.112 on BTC/ETH and 0.145-0.148 on SOL, which the
    closing record §10.2 derived and this measures.
    """
    cr = measured["populations"]["candidates"]["cost_ratio"]
    assert cr["tolerance"] == 0.11
    assert cr["n_above_tolerance"] > 0
    assert cr["floor_bound"]["min"] > 0.11, (
        "a floor-bound stop always exceeds the tolerance")
    assert cr["n_above_and_floor_bound"] == cr["n_floor_bound"]
    assert cr["not_floor_bound"]["min"] < 0.11
    assert cr["all"]["max"] == pytest.approx(0.1483, abs=0.0005)
    assert cr["n_above_tolerance"] == (cr["n_above_and_floor_bound"]
                                       + cr["n_above_not_floor_bound"])


def test_tick_rounding_is_negligible_against_the_stop_distance(measured):
    """THE MAGNITUDE QUESTION A7 ASKS. If it were material the DIRECTION would
    deserve pre-registration; it is not."""
    for leg in ("tick_shift_stop_fraction", "tick_shift_target_fraction"):
        s = measured["populations"]["candidates"][leg]
        assert s["max"] < 0.001, (leg, s["max"])
        assert s["mean"] < 0.0002, (leg, s["mean"])


def test_per_fold_rows_are_complete(measured):
    for name in ("candidates", "taken"):
        folds = measured["per_fold"][name]
        assert len(folds) == 18
        assert {f for f, _ in folds} == set(range(1, 10))
        for key, row in folds.items():
            assert row["pooled"]["n"] > 0, (name, key)
            assert set(row["per_symbol"]) == set(rs.SYMBOLS)


# ---------------------------------------------------------------------------
# 5. WHAT THE MODULE MAY NOT DO.
# ---------------------------------------------------------------------------

def _imports():
    out = set()
    for node in ast.walk(_module_ast()):
        if isinstance(node, ast.Import):
            for a in node.names:
                out.add(a.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                out.add(node.module)
                for a in node.names:
                    out.add("%s.%s" % (node.module, a.name))
    return out


def _identifiers():
    names = set()
    for node in ast.walk(_module_ast()):
        if isinstance(node, ast.Name):
            names.add(node.id)
        elif isinstance(node, ast.Attribute):
            names.add(node.attr)
        elif isinstance(node, ast.arg):
            names.add(node.arg)
        elif isinstance(node, (ast.FunctionDef, ast.ClassDef)):
            names.add(node.name)
    return names


def test_no_bar_after_a_signal_bar_is_read():
    """The measurement is a distribution over SIZED POSITIONS at their entry.

    Nothing pairs a position with a subsequent price and nothing asks whether a
    level was reached. Asserted over the vocabulary and over the absence of any
    forward shift.
    """
    src = open(sd.__file__).read()
    assert ".shift(-" not in src
    for name in _identifiers():
        low = name.lower()
        for banned in ("hit", "touch", "reached", "crossed", "exit_reason",
                       "was_hit"):
            assert banned not in low, name
    for word in ("high", "low_price", "future", "lookahead"):
        assert word not in {n.lower() for n in _identifiers()}, word


def test_simulate_and_the_carve_out_are_not_reachable():
    """The sizing module's one carve-out is NOT called from the measurement."""
    banned = ("simulate", "src.engine.simulate", "src.engine.run")
    for mod in _imports():
        for bad in banned:
            assert not (mod == bad or mod.startswith(bad + ".")), mod
    for name in _identifiers():
        assert "simulate" not in name
        assert "net_proceeds" not in name, (
            "the recorded carve-out must not be called from the measurement")


def test_no_1m_path_is_reachable():
    src = open(sd.__file__).read()
    for word in ("ohlcv_1m", "load_1m", "BAR_1M_MS"):
        assert word not in src, word


def test_the_module_defines_no_window_constant():
    assert rs.WINDOW_START == dt.date(2022, 1, 1)
    assert rs.WINDOW_END == dt.date(2024, 12, 31)
    assert rs.ALLOWED_YEARS == (2022, 2023, 2024)
    assigned = set()
    for node in ast.walk(_module_ast()):
        if isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name):
                    assigned.add(t.id)
    assert not {"WINDOW_START", "WINDOW_END", "ALLOWED_YEARS"} & assigned


def test_no_measured_position_reaches_the_holdout(measured):
    sealed = rs.holdout_start_ms()
    sized = measured["sized"]
    assert int(sized["ts"].max()) < sealed
    last = dt.datetime.fromtimestamp(int(sized["ts"].max()) / 1000,
                                     dt.timezone.utc)
    assert last.year == 2024


def test_size_population_refuses_a_holdout_bar():
    """The seal is carried on the way out, as in reports 24, 26 and 27."""
    sealed = rs.holdout_start_ms()
    frame = _hand_frame([(sealed, "BTCUSDT", "long", 30_000.0, 300.0, True)])
    with pytest.raises(rs.HoldoutBreach, match="sealed holdout boundary"):
        sd.size_population(frame)


PERFORMANCE_NAMES = ("expectancy", "win_rate", "winrate", "profit_factor",
                     "sharpe", "sortino", "net_pnl", "gross_pnl", "drawdown",
                     "r_multiple", "equity", "pnl")


def test_no_performance_quantity_appears_in_the_module():
    tree = _module_ast()
    docstrings = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.FunctionDef, ast.ClassDef)):
            d = ast.get_docstring(node, clean=False)
            if d is not None:
                docstrings.add(d)
    blob = set(_identifiers())
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            if node.value not in docstrings:
                blob.add(node.value)
    text = " ".join(blob).lower()
    for banned in PERFORMANCE_NAMES:
        assert banned not in text, banned


def test_report_exists_and_states_the_central_result():
    path = os.path.join(rs.ROOT, "docs", "handoff",
                        "28_point_5_3_1_sizing.md")
    assert os.path.exists(path), path
    text = open(path).read()
    for token in ("quantity", "invarian", "BELOW_MIN_QTY", "BELOW_MIN_NOTIONAL",
                  "0.11", "qty_step", "carve-out"):
        assert token.lower() in text.lower(), token
