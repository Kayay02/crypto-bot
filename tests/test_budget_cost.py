"""Guards for the frozen budget's cost measurement.

THREE THINGS CAN BE WRONG HERE WITHOUT ANYTHING RAISING.

THE ALLOCATION ORDER. Rule C (exits before entries) and Rule A (rotation within
a bar) each change which signals are taken without changing how many bars carry
signals, how many positions exist, or any distributional shape. A reversed Rule
C simply skips a few hundred more signals and reports a slightly higher skip
rate, which is exactly the number this report exists to produce. The positive
control therefore pins the taken/skipped sequence ELEMENT BY ELEMENT against a
hand-computed one, including the two cases the rules exist for.

THE POPULATION IDENTITY. `taken + skipped` must equal report 24's uncapped
count exactly, per symbol and pooled. If the two populations diverged -- a
different warm-up, a different signal definition, a dropped two-sided bar -- every
skip rate here would be a ratio of two different things and would still look
entirely reasonable. That identity is asserted as a STOP condition.

THE CONSTANTS. Every rule value must be the frozen module's object, not a copy
of its value. A local `120.0` would agree today and would stop agreeing silently
the moment an amendment changed it, which is the failure the whole
pre-registration chain exists to prevent.
"""

import ast
import datetime as dt
import hashlib
import os

import numpy as np
import pandas as pd
import pytest

from src.analysis import budget_cost as bc
from src.analysis import exposure_profile as ep
from src.analysis import sweep_population as sp
from src.folds import schedule as sch
from src.risk import budget as rb
from src.timeframe import resample as rs


HOUR_MS = 3_600_000
T0 = 1_640_995_200_000  # 2022-01-01T00:00:00Z, rotation 0

#: Report 24's uncapped population, frozen at 4e08e1b §3.4.
REPORT_24_POSITIONS = {"BTCUSDT": 3735, "ETHUSDT": 3715, "SOLUSDT": 3934}
REPORT_24_TOTAL = 11_384

DESIGN_HASHES = {
    "05_aggregate_risk_budget.md":
        "d5ac7bd61323d04e75a854baf14086932470175408f5e2db4ca6f4d3afad268f",
    "05a_aggregate_risk_budget_amendment_1.md":
        "50da5aed3fabb86c3c7b54b41642444e50c7a7790de8dc93ab401ab53071522c",
    "05b_aggregate_risk_budget_amendment_2.md":
        "1d115df2272a4e231da41afbbd0b7c82020d0092ec2b3b483062d57c0e95f7bd",
}


@pytest.fixture(scope="module")
def measured():
    return bc.measure()


def _module_ast():
    return ast.parse(open(bc.__file__).read())


def _cand(rows):
    """A hand-specified candidate frame, sorted the way the rule reads it.

    `(ts, rotation rank)` is the arrival order Rule A defines; sorting here is
    what `candidates()` does on the real population.
    """
    frame = pd.DataFrame(rows)
    frame["rank"] = [bc.priority_rank(t, s)
                     for t, s in zip(frame["ts"], frame["symbol"])]
    frame["notional"] = 1000.0
    frame["direction"] = ep.LONG
    frame["stop_pct"] = 2.0
    return frame.sort_values(["ts", "rank"],
                             kind="mergesort").reset_index(drop=True)


def _row(bar, symbol, exit_bar):
    return {"ts": T0 + bar * HOUR_MS, "symbol": symbol,
            "exit_bar_ts": T0 + exit_bar * HOUR_MS}


# ---------------------------------------------------------------------------
# 1. CONSTANTS PROVENANCE -- every value is the frozen module's.
# ---------------------------------------------------------------------------

def test_every_rule_value_comes_from_the_frozen_module():
    """IDENTITY, not equality. A local copy would agree today and drift later."""
    assert bc.BUDGET_USD is rb.MAX_AGGREGATE_OPEN_RISK_USD
    assert bc.UNIT_USD is rb.RISK_PER_TRADE_USD
    assert bc.MAX_SLOTS is rb.FULL_SIZE_POSITIONS
    assert bc.ROTATION_PERIOD_MS is rb.ROTATION_PERIOD_MS
    assert bc.ROTATION_MODULUS is rb.ROTATION_MODULUS
    assert bc.SYMBOL_ROTATION is rb.SYMBOL_ROTATION
    assert bc.BUDGET_CHARGES is rb.BUDGET_CHARGES
    assert bc.INTRA_BAR_ORDER is rb.INTRA_BAR_ORDER
    assert bc.CAPITAL_USD is ep.CAPITAL_USD

    assert bc.BUDGET_USD == 120.00
    assert bc.UNIT_USD == 20.00
    assert bc.MAX_SLOTS == 6
    assert bc.BUDGET_CHARGES == "nominal"
    assert bc.INTRA_BAR_ORDER == "exits_before_entries"


def test_the_module_retypes_no_rule_value():
    """No numeric literal in the module may equal a rule value.

    A transcribed 120.0 or 20.0 would satisfy every equality above and would be
    a second copy of a frozen number.
    """
    literals = [n.value for n in ast.walk(_module_ast())
                if isinstance(n, ast.Constant)
                and isinstance(n.value, (int, float))
                and not isinstance(n.value, bool)]
    for banned in (120.0, 20.0, 120, 20):
        assert banned not in literals, banned


def test_the_three_design_documents_are_unchanged():
    """The rule this measurement applies must still be the rule that was frozen."""
    for name, expected in DESIGN_HASHES.items():
        path = os.path.join(rs.ROOT, "docs", "design", name)
        with open(path, "rb") as fh:
            assert hashlib.sha256(fh.read()).hexdigest() == expected, name


def test_the_rotation_helpers_apply_the_frozen_table():
    assert bc.rotation(T0) == 0
    assert bc.priority(T0) == ("BTCUSDT", "ETHUSDT", "SOLUSDT")
    assert bc.rotation(T0 + HOUR_MS) == 1
    assert bc.priority(T0 + HOUR_MS) == ("ETHUSDT", "SOLUSDT", "BTCUSDT")
    assert bc.rotation(T0 + 2 * HOUR_MS) == 2
    assert bc.priority_rank(T0, "BTCUSDT") == 0
    assert bc.priority_rank(T0, "SOLUSDT") == 2
    # Report 24 §7.5's worst bar, pinned in Amendment 1 §5.
    worst = int(dt.datetime(2024, 7, 15, 22,
                            tzinfo=dt.timezone.utc).timestamp() * 1000)
    assert bc.rotation(worst) == 1


# ---------------------------------------------------------------------------
# 2. SYNTHETIC POSITIVE CONTROL -- the take/skip sequence, hand-computed.
# ---------------------------------------------------------------------------

def test_positive_control_the_sequence_of_takes_and_skips():
    """THE CONTROL. Every rule exercised, and the answer known by hand.

    THE CONSTRUCTION, on bars 0..10 from 2022-01-01T00:00:00Z. Exit bars are
    hand-chosen to place the two cases the rules exist for; they are not
    max-hold exits, because this control tests the ALLOCATION and not the
    funding calendar.

        bar 0..5   one signal each, book fills to exactly SIX      -> TAKEN x6
                   the bar-3 position exits at bar 7
                   the bar-4 position exits at bar 10
        bar 6      one signal, book full, no exit                  -> SKIPPED
        bar 7      one signal AND one exit at the same close       -> TAKEN
                   (RULE C: the exit releases before the entry is evaluated;
                    under entries-first this would be skipped)
        bar 10     THREE signals and ONE freed slot                -> rotation
                   bar 10 has rotation 1 -> ETH, SOL, BTC, so ETH takes it and
                   SOL and BTC are skipped (RULE A decided the outcome)

    Asserted element by element, not as counts.
    """
    cand = _cand([
        _row(0, "BTCUSDT", 100), _row(1, "BTCUSDT", 100),
        _row(2, "BTCUSDT", 100), _row(3, "BTCUSDT", 7),
        _row(4, "BTCUSDT", 10), _row(5, "BTCUSDT", 100),
        _row(6, "BTCUSDT", 100),
        _row(7, "BTCUSDT", 100),
        _row(10, "BTCUSDT", 100), _row(10, "ETHUSDT", 100),
        _row(10, "SOLUSDT", 100),
    ])
    assert bc.rotation(T0 + 10 * HOUR_MS) == 1
    assert bc.priority(T0 + 10 * HOUR_MS) == ("ETHUSDT", "SOLUSDT", "BTCUSDT")
    # The frame is in arrival order: bar 10's three signals are ETH, SOL, BTC.
    assert list(cand["symbol"])[-3:] == ["ETHUSDT", "SOLUSDT", "BTCUSDT"]

    out = bc.allocate(cand)
    taken = list(out["positions"]["taken"])

    hand = [True, True, True, True, True, True,   # bars 0..5 fill the book
            False,                                 # bar 6 -- full, skipped
            True,                                  # bar 7 -- RULE C
            True, False, False]                    # bar 10 -- RULE A: ETH wins
    assert taken == hand, list(zip(cand["ts"], cand["symbol"], taken))

    assert out["n_taken"] == 8
    assert out["n_skipped"] == 3
    assert out["partial_allocations"] == 0

    bars = out["bars"].set_index("ts")
    six = bars.loc[T0 + 5 * HOUR_MS]
    assert int(six["open_after_exits"]) + int(six["n_taken"]) == bc.MAX_SLOTS

    full = bars.loc[T0 + 6 * HOUR_MS]
    assert int(full["n_exits"]) == 0
    assert int(full["free_after_exits"]) == 0
    assert int(full["n_taken"]) == 0

    rule_c = bars.loc[T0 + 7 * HOUR_MS]
    assert int(rule_c["n_exits"]) == 1
    assert int(rule_c["free_before_exits"]) == 0, "entries-first would skip it"
    assert int(rule_c["free_after_exits"]) == 1
    assert int(rule_c["n_taken"]) == 1
    assert int(rule_c["rule_c_gain"]) == 1

    rule_a = bars.loc[T0 + 10 * HOUR_MS]
    assert int(rule_a["n_signals"]) == 3
    assert int(rule_a["free_after_exits"]) == 1
    assert bool(rule_a["contested"]) and bool(rule_a["rule_a_decided"])
    assert int(rule_a["n_taken"]) == 1


def test_positive_control_entries_first_would_skip_the_rule_C_signal():
    """THE COUNTERFACTUAL, on the same fixture: the bar-7 signal is the one
    Rule C bought, and it is exactly one position."""
    cand = _cand([
        _row(0, "BTCUSDT", 100), _row(1, "BTCUSDT", 100),
        _row(2, "BTCUSDT", 100), _row(3, "BTCUSDT", 7),
        _row(4, "BTCUSDT", 100), _row(5, "BTCUSDT", 100),
        _row(7, "BTCUSDT", 100),
    ])
    out = bc.allocate(cand)
    assert list(out["positions"]["taken"]) == [True] * 6 + [True]
    assert int(out["bars"]["rule_c_gain"].sum()) == 1


def test_positive_control_a_seventh_concurrent_position_is_refused():
    """The cap is SIX. A seventh simultaneous signal is skipped, not resized."""
    cand = _cand([_row(b, "BTCUSDT", 100) for b in range(8)])
    out = bc.allocate(cand)
    assert list(out["positions"]["taken"]) == [True] * 6 + [False, False]
    assert out["partial_allocations"] == 0, (
        "a seventh position must be SKIPPED, never partially allocated")


def test_positive_control_the_rotation_decides_a_fully_contested_bar():
    """Three signals on an empty-slot-free book at each of the three rotations."""
    for bar, expected in ((0, "BTCUSDT"), (1, "ETHUSDT"), (2, "SOLUSDT")):
        rows = [_row(b, "BTCUSDT", 500) for b in range(-10, -5)]   # 5 open
        rows += [_row(bar, s, 500) for s in ("BTCUSDT", "ETHUSDT", "SOLUSDT")]
        out = bc.allocate(_cand(rows))
        pos = out["positions"]
        at_bar = pos[pos["ts"] == T0 + bar * HOUR_MS]
        winners = list(at_bar[at_bar["taken"]]["symbol"])
        assert winners == [expected], (bar, winners)


# ---------------------------------------------------------------------------
# 3. SYNTHETIC NEGATIVE CONTROL.
# ---------------------------------------------------------------------------

def test_negative_control_nothing_fires():
    """Zero signals, zero takes, zero skips, an all-zero occupancy timeline."""
    empty = pd.DataFrame({c: pd.Series(dtype=t) for c, t in (
        ("ts", "int64"), ("symbol", "object"), ("exit_bar_ts", "int64"),
        ("rank", "int64"), ("notional", "float64"), ("direction", "object"),
        ("stop_pct", "float64"))})
    out = bc.allocate(empty)
    assert out["n_taken"] == 0 and out["n_skipped"] == 0
    assert out["partial_allocations"] == 0
    assert len(out["bars"]) == 0

    grid = ep.hourly_grid(T0, T0 + 200 * HOUR_MS)
    tl = ep.occupancy(out["positions"], grid)
    np.testing.assert_array_equal(tl["positions_open"],
                                  np.zeros(len(grid), dtype=np.int64))
    np.testing.assert_array_equal(tl["notional_open"], np.zeros(len(grid)))


def test_negative_control_a_real_series_that_cannot_signal():
    """A flat bar series produces no signal, so no candidate and no skip."""
    n = 300
    frame = pd.DataFrame({
        "ts": T0 + np.arange(n) * HOUR_MS,
        "high": np.full(n, 101.0), "low": np.full(n, 99.0),
        "close": np.full(n, 100.0),
    })
    analysed = sp.analysis_frame(frame)
    assert int(analysed["sweep_long"].sum()) == 0
    assert int(analysed["sweep_short"].sum()) == 0
    assert len(ep.positions(analysed, "BTCUSDT")) == 0


# ---------------------------------------------------------------------------
# 4. THE POPULATION IDENTITY -- a STOP condition if it fails.
# ---------------------------------------------------------------------------

def test_taken_plus_skipped_equals_report_24s_uncapped_population(measured):
    """THE STOP CONDITION. A discrepancy means the populations diverged.

    Every skip rate in the report is a ratio against this denominator; if it is
    not report 24's denominator, every figure is a ratio of two different
    things and still looks entirely reasonable.
    """
    for sym, expected in REPORT_24_POSITIONS.items():
        c = measured["per_symbol"][sym]
        assert c["n_taken"] + c["n_skipped"] == c["n_signals"]
        assert c["n_signals"] == expected, (sym, c["n_signals"], expected)
    pooled = measured["pooled"]
    assert pooled["n_signals"] == REPORT_24_TOTAL
    assert pooled["n_taken"] + pooled["n_skipped"] == REPORT_24_TOTAL
    assert sum(measured["per_symbol"][s]["n_taken"]
               for s in REPORT_24_POSITIONS) == pooled["n_taken"]


def test_the_capped_population_is_a_strict_subset_of_the_uncapped_one(measured):
    """Deterministic exits make this true HERE and it will not be true of the
    real backtest -- document 05 §6. Asserted so the caveat is anchored."""
    pos = measured["positions"]
    assert len(pos) == REPORT_24_TOTAL
    assert pos["taken"].sum() == measured["pooled"]["n_taken"]
    assert set(pos.loc[pos["taken"], "ts"]) <= set(pos["ts"])


def test_fold_attribution_accounts_for_the_overlapping_training_windows(
        measured):
    """FOLDS ATTRIBUTE, THEY DO NOT SEGMENT -- and they OVERLAP.

    Adjacent training windows overlap by 50%, so the per-fold counts sum to
    MORE than the pooled count and a position can belong to two periods. The
    identity that must hold is against the sum of per-position membership, not
    against the population size.
    """
    pos = measured["positions"]
    per_fold_total = sum(measured["pooled_per_fold"][k]["n_signals"]
                         for k in measured["pooled_per_fold"])
    assert per_fold_total == int(pos["n_fold_periods"].sum())
    assert per_fold_total > len(pos), "the overlap must actually be present"
    assert per_fold_total == 25_451
    # THREE, not two: a bar in fold k's TEST period also sits in fold k+1's and
    # fold k+2's TRAINING windows, because train is 6 months and the step is 3.
    assert int(pos["n_fold_periods"].max()) == 3
    assert int((pos["n_fold_periods"] == 0).sum()) > 0, (
        "bars before fold 1 belong to no period")
    assert int((pos["n_fold_periods"] == 0).sum()) == 889

    for key, c in measured["pooled_per_fold"].items():
        by_symbol = sum(measured["per_symbol_per_fold"][key][s]["n_signals"]
                        for s in rs.SYMBOLS)
        assert by_symbol == c["n_signals"], key
        assert c["n_taken"] + c["n_skipped"] == c["n_signals"], key


# ---------------------------------------------------------------------------
# 5. INVARIANTS ON THE REAL RUN.
# ---------------------------------------------------------------------------

def test_the_invariants_hold_at_every_bar(measured):
    book = measured["book_timeline"]
    count = book["positions_open"]
    assert int(count.max()) <= bc.MAX_SLOTS
    assert int(count.min()) >= 0

    charged = count * bc.UNIT_USD
    assert float(charged.max()) <= bc.BUDGET_USD + 1e-9
    remaining = bc.BUDGET_USD - charged
    assert float(remaining.min()) >= -1e-9
    steps = remaining / bc.UNIT_USD
    assert float(np.abs(steps - np.round(steps)).max()) < 1e-9, (
        "the remaining budget must stay a whole multiple of the risk unit")

    assert measured["diagnostics"]["partial_allocations"] == 0
    assert measured["book"]["concurrency"]["max"] == float(bc.MAX_SLOTS)
    assert measured["book"]["nominal_risk_usd"]["max"] == bc.BUDGET_USD


def test_assert_invariants_refuses_a_breach():
    """The guard must be able to REFUSE, or it proves nothing."""
    cand = _cand([_row(b, "BTCUSDT", 500) for b in range(8)])
    out = bc.allocate(cand)
    grid = ep.hourly_grid(T0, T0 + 600 * HOUR_MS)
    bc.assert_invariants(out, grid)

    breached = dict(out)
    breached["partial_allocations"] = 1
    with pytest.raises(ValueError, match="partial-allocation branch"):
        bc.assert_invariants(breached, grid)

    # A book of seven, planted by forcing every candidate taken.
    forced = out["positions"].copy()
    forced["taken"] = True
    with pytest.raises(ValueError, match="above the .*-slot cap"):
        bc.assert_invariants({"positions": forced, "partial_allocations": 0},
                             grid)


def test_a_skip_happens_exactly_when_the_budget_is_full(measured):
    """Rule B again: allocation is the unit or nothing, so a skip is always a
    full book and never a partial size."""
    d = measured["diagnostics"]
    assert d["full_at_arrival"] == measured["pooled"]["n_skipped"]
    assert d["partial_allocations"] == 0


# ---------------------------------------------------------------------------
# 6. RULE A NEUTRALITY ON REAL DATA.
# ---------------------------------------------------------------------------

def test_rule_A_is_exactly_neutral_on_any_three_consecutive_real_bars(measured):
    grid = ep.hourly_grid(measured["grid"]["lo"], measured["grid"]["hi"])
    for start in range(0, 900, 7):
        orders = [bc.priority(int(grid[start + k])) for k in range(3)]
        for rank in range(3):
            assert sorted(o[rank] for o in orders) == sorted(rs.SYMBOLS)


def test_rule_A_holds_each_rank_on_about_one_bar_in_three_across_the_window(
        measured):
    grid = ep.hourly_grid(measured["grid"]["lo"], measured["grid"]["hi"])
    n = len(grid)
    for rank in range(3):
        counts = {s: 0 for s in rs.SYMBOLS}
        for ts in grid:
            counts[bc.priority(int(ts))[rank]] += 1
        for sym, c in counts.items():
            assert abs(c / n - 1.0 / 3.0) < 0.001, (rank, sym, c)
        assert sum(counts.values()) == n


# ---------------------------------------------------------------------------
# 7. DETERMINISM.
# ---------------------------------------------------------------------------

def test_two_runs_produce_identical_output(measured):
    again = bc.measure()
    pd.testing.assert_frame_equal(measured["positions"], again["positions"])
    assert measured["pooled"] == again["pooled"]
    assert measured["diagnostics"] == again["diagnostics"]
    assert measured["per_symbol"] == again["per_symbol"]
    assert measured["worst_bar"] == again["worst_bar"]
    assert measured["projection"] == again["projection"]


# ---------------------------------------------------------------------------
# 8. THE PROJECTION reads no sealed bar.
# ---------------------------------------------------------------------------

def test_the_holdout_projection_is_calendar_arithmetic_only():
    days, bars = bc.holdout_bars()
    assert days == bc.HOLDOUT_DAYS == 572
    assert bars == 572 * 24 == 13_728
    assert (sch.HOLDOUT_TEST_END - sch.HOLDOUT_TEST_START).days + 1 == days

    projected = bc.project_holdout({"BTCUSDT": 1000}, 26_190)
    assert projected["holdout_bars"] == 13_728
    assert projected["per_symbol"]["BTCUSDT"]["projected"] == pytest.approx(
        1000 * 13_728 / 26_190)


def test_the_projection_clears_the_out_of_sample_minimum(measured):
    """Reported as a projection against the 50-trade minimum, not as a count."""
    for sym, d in measured["projection"]["per_symbol"].items():
        assert d["projected"] > 50, sym


# ---------------------------------------------------------------------------
# 9. THE HOLDOUT SEAL.
# ---------------------------------------------------------------------------

def test_the_module_defines_no_window_constant_and_names_no_sealed_year():
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
    src = open(bc.__file__).read()
    assert str(sch.HOLDOUT_TEST_START.year) not in src.replace(
        "2025-01-01 through 2026-07-26", "")


def test_candidates_refuse_a_holdout_bar():
    """The runtime guard must be able to REFUSE."""
    sealed = rs.holdout_start_ms()
    n = 300
    frame = pd.DataFrame({
        "ts": sealed - (n - 1 - np.arange(n)) * HOUR_MS,
        "high": np.full(n, 101.0), "low": np.full(n, 99.0),
        "close": np.full(n, 100.0),
    })
    assert int(frame["ts"].max()) >= sealed
    with pytest.raises(rs.HoldoutBreach, match="sealed holdout boundary"):
        sp.analysis_frame(frame)


def test_no_measured_position_touches_the_seal(measured):
    sealed = rs.holdout_start_ms()
    pos = measured["positions"]
    assert int(pos["ts"].max()) < sealed
    assert int(measured["grid"]["hi"]) < sealed
    last = dt.datetime.fromtimestamp(int(pos["ts"].max()) / 1000,
                                     dt.timezone.utc)
    assert last.year == 2024
    for _, period, lo, hi in measured["windows"]:
        assert hi < sealed, period


# ---------------------------------------------------------------------------
# 10. THE FIREWALL, AND THE FORBIDDEN IMPORT.
# ---------------------------------------------------------------------------

from src.firewall import PERFORMANCE_NAMES  # noqa: E402
"""The canonical twelve-name list, defined once at `src/firewall.py`.

Previously written out in full here. Eighteen copies had drifted into two
different lists; this module now imports the one definition."""


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


def test_simulate_is_not_reachable_from_this_module():
    """SIMULATE WOULD SILENTLY CONTAMINATE THIS MEASUREMENT.

    Its portfolio mode carries "one open position per symbol, no pyramiding"
    and a margin refusal at max_leverage = 3.0 -- which report 25 §10.1
    established is an unmeasured placeholder, and which WOULD BIND here: the
    measured maximum notional is 3.596x capital. Either constraint would change
    the traded population while leaving every table plausible.
    """
    banned = ("simulate", "src.engine.simulate", "src.sweep", "src.folds.run",
              "src.engine.run", "src.engine.diagnostics")
    for mod in _imports():
        for bad in banned:
            assert not (mod == bad or mod.startswith(bad + ".")), mod

    # Over IDENTIFIERS, not prose: the module NAMES simulate in a docstring and
    # a comment in order to record that it is deliberately not imported.
    called = {node.id for node in ast.walk(_module_ast())
              if isinstance(node, ast.Name)}
    called |= {node.attr for node in ast.walk(_module_ast())
               if isinstance(node, ast.Attribute)}
    assert not any("simulate" in name for name in called), called

    # And transitively: nothing this module imports may pull it in either.
    for name in ("src.analysis.exposure_profile", "src.analysis.sweep_population",
                 "src.risk.budget"):
        mod = __import__(name, fromlist=["x"])
        text = open(mod.__file__).read()
        assert "import simulate" not in text, name


def test_no_performance_quantity_appears_in_the_module():
    """FIREWALL GUARD, over identifiers and non-docstring string literals."""
    tree = _module_ast()
    docstrings = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.FunctionDef, ast.ClassDef)):
            d = ast.get_docstring(node, clean=False)
            if d is not None:
                docstrings.add(d)
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            names.add(node.id)
        elif isinstance(node, ast.Attribute):
            names.add(node.attr)
        elif isinstance(node, ast.arg):
            names.add(node.arg)
        elif isinstance(node, (ast.FunctionDef, ast.ClassDef)):
            names.add(node.name)
        elif isinstance(node, ast.Constant) and isinstance(node.value, str):
            if node.value not in docstrings:
                names.add(node.value)
    blob = " ".join(names).lower()
    for banned in PERFORMANCE_NAMES:
        assert banned not in blob, "%r used as a name in %s" % (banned,
                                                               bc.__file__)


def test_no_stop_or_target_is_evaluated():
    src = open(bc.__file__).read()
    assert ".shift(-" not in src
    for word in ("solve_target", "stop_geometry", "was_hit", "exit_reason",
                 "trade_pnl", "summarize", "target_price"):
        assert word not in src, word


def test_only_position_size_is_taken_from_the_engine():
    """`costs` is imported for the config object report 24 sizes with."""
    used = {node.attr for node in ast.walk(_module_ast())
            if isinstance(node, ast.Attribute)
            and isinstance(node.value, ast.Name) and node.value.id == "costs"}
    assert used <= {"position_size", "CostConfig"}, used


def test_report_exists_and_states_the_frozen_rule():
    path = os.path.join(rs.ROOT, "docs", "handoff",
                        "26_point_5_2_budget_cost.md")
    assert os.path.exists(path), path
    text = open(path).read()
    for token in ("120.00", "upper bound", "hedge", "rotation", "Rule C"):
        assert token.lower() in text.lower(), token
    for name, digest in DESIGN_HASHES.items():
        assert digest in text, name
