"""Guards for report 40 -- the fold schedule's geometry and what reaches the engine.

THESE PIN THE FACTS SUB-POINT 4.2's AGGREGATION RULE WILL REST ON. Report 40
establishes them; without these they are true today and unenforced tomorrow.

THE REACHABILITY ASSERTION IS THE LOAD-BEARING ONE.
`test_the_engine_imports_neither_the_folds_nor_the_sweep` is what makes "nothing
train-estimated reaches a position sized by the frozen thesis" checkable rather
than argued. It runs over AST import nodes, never raw text.

NO BAR IS READ AND NO SEALED PATH IS TOUCHED. The schedule is a pure function of
calendar constants, which is what lets the geometry be asserted without data.
"""

import ast
import datetime as dt
import os

import pytest

from src.folds import schedule as sch
from src.sweep import bands

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

ENGINE_DIR = os.path.join(ROOT, "src", "engine")


def _imports(path):
    tree = ast.parse(open(path).read())
    out = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                out.add(alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module:
            out.add(node.module)
    return out


def _overlap_days(a_start, a_end, b_start, b_end):
    lo, hi = max(a_start, b_start), min(a_end, b_end)
    return (hi - lo).days + 1 if lo <= hi else 0


@pytest.fixture(scope="module")
def folds():
    return sch.build_schedule()


# ---------------------------------------------------------------------------
# REACHABILITY -- THE ASSERTION REPORT 40 §4 TURNS ON.
# ---------------------------------------------------------------------------

def test_the_engine_imports_neither_the_folds_nor_the_sweep():
    """NO TRAIN-ESTIMATED QUANTITY CAN REACH A POSITION BY IMPORT.

    Every module under `src/engine/` is checked. A future import of either
    package would open a channel through which a per-fold estimate could reach
    `portfolio.size_position`, and this fails the moment one appears.
    """
    offenders = {}
    for name in sorted(os.listdir(ENGINE_DIR)):
        if not name.endswith(".py"):
            continue
        mods = _imports(os.path.join(ENGINE_DIR, name))
        bad = sorted(m for m in mods
                     if m.startswith("src.folds") or m.startswith("src.sweep")
                     or m in ("schedule", "grid", "bands", "sweep",
                              "prescreen"))
        if bad:
            offenders["src/engine/" + name] = bad
    assert not offenders, offenders


def test_the_sweep_DOES_import_the_engine_so_the_direction_is_one_way():
    """The discrimination check: the dependency exists, and it runs sweep ->
    engine. A test asserting only the absence above would pass on two packages
    that never spoke at all."""
    mods = _imports(os.path.join(ROOT, "src", "sweep", "sweep.py"))
    assert "simulate" in mods
    assert "costs" in mods


def test_the_sweep_simulates_through_simulate_not_through_portfolio():
    """WHICH ENGINE PATH THE SELECTION WAS MADE ON. `simulate.run_backtest`
    applies `costs.stop_geometry`; `portfolio.size_position` does not."""
    tree = ast.parse(open(os.path.join(ROOT, "src", "sweep",
                                       "sweep.py")).read())
    called = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            f = node.func
            name = f.attr if isinstance(f, ast.Attribute) else (
                f.id if isinstance(f, ast.Name) else None)
            if name:
                called.add(name)
    assert "run_backtest" in called
    assert "size_position" not in called


def test_selection_is_on_TRAIN_and_the_literal_is_not_indirected():
    """`bands.py` selects on the training fold. The module hard-codes the
    literal separately from `SELECT_PERIOD` so that flipping the selector
    raises rather than silently reading the wrong population; that structure is
    asserted here, not just the constant."""
    assert bands.SELECT_PERIOD == "train"
    src = open(os.path.join(ROOT, "src", "sweep", "bands.py")).read()
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and \
                node.name == "_acceptance_metrics":
            literals = {n.value for n in ast.walk(node)
                        if isinstance(n, ast.Constant)
                        and isinstance(n.value, str)}
            assert "train" in literals
            names = {n.id for n in ast.walk(node) if isinstance(n, ast.Name)}
            assert "SELECT_PERIOD" not in names
            return
    raise AssertionError("_acceptance_metrics not found")


# ---------------------------------------------------------------------------
# WINDOW GEOMETRY.
# ---------------------------------------------------------------------------

def test_nine_folds_ending_exactly_on_the_in_sample_end(folds):
    assert len(folds) == 9
    assert folds[0]["train_start"] == dt.date(2022, 4, 1)
    assert folds[-1]["test_end"] == dt.date(2024, 12, 31)
    assert sch.TRAIN_MONTHS == 6 and sch.TEST_MONTHS == 3
    assert sch.STEP_MONTHS == 3


def test_the_TEST_windows_are_DISJOINT_and_contiguous(folds):
    """No candidate can fall in two test windows, and the union has no gaps."""
    windows = sorted((f["test_start"], f["test_end"]) for f in folds)
    for (a_start, a_end), (b_start, b_end) in zip(windows, windows[1:]):
        assert _overlap_days(a_start, a_end, b_start, b_end) == 0
        assert (b_start - a_end).days == 1, "gap between test windows"
    assert windows[0][0] == dt.date(2022, 10, 1)
    assert windows[-1][1] == dt.date(2024, 12, 31)


def test_the_TRAIN_windows_overlap_ADJACENT_folds_by_about_half(folds):
    """The 50 per cent figure, verified against the schedule rather than
    repeated. Non-adjacent training windows do not overlap."""
    for a, b in zip(folds, folds[1:]):
        days = _overlap_days(a["train_start"], a["train_end"],
                             b["train_start"], b["train_end"])
        span = (a["train_end"] - a["train_start"]).days + 1
        assert 0.49 < days / span < 0.51, (a["fold_id"], days, span)

    for i, a in enumerate(folds):
        for b in folds[i + 2:]:
            assert _overlap_days(a["train_start"], a["train_end"],
                                 b["train_start"], b["train_end"]) == 0


def test_every_TEST_window_becomes_TRAINING_DATA_for_later_folds(folds):
    """THE FACT THAT MAKES THE FOLDS NOT INDEPENDENT TRIALS.

    Each fold's test window falls inside the next two folds' training windows.
    Asserted in the forward direction only -- no fold trains on a LATER fold's
    test window, which would be lookahead.
    """
    cross = []
    for a in folds:
        for b in folds:
            if a["fold_id"] == b["fold_id"]:
                continue
            days = _overlap_days(a["test_start"], a["test_end"],
                                 b["train_start"], b["train_end"])
            if days:
                cross.append((a["fold_id"], b["fold_id"], days))
    assert len(cross) == 15

    # Every one runs forward: the training fold is always LATER.
    for test_fold, train_fold, _days in cross:
        assert train_fold > test_fold, (test_fold, train_fold)

    # And each test window is consumed by exactly the next two folds.
    for a in folds[:-2]:
        consumers = sorted(t for t, _tr, _d in
                           [(b["fold_id"], None, None) for b in folds
                            if _overlap_days(a["test_start"], a["test_end"],
                                             b["train_start"], b["train_end"])
                            and b["fold_id"] != a["fold_id"]])
        assert consumers == [a["fold_id"] + 1, a["fold_id"] + 2], a["fold_id"]


def test_the_holdout_carries_no_train_window():
    holdout = sch.holdout_definition()
    assert holdout["train_start"] is None
    assert holdout["train_end"] is None
    assert holdout["test_start"] == dt.date(2025, 1, 1)
    assert holdout["test_end"] == dt.date(2026, 7, 26)


def test_the_test_union_starts_after_the_data_does(folds):
    """WHY CANDIDATES FALL IN NO TEST WINDOW. The first test window opens on
    2022-10-01 while the derived layer begins in January, so everything before
    that is in a training window or in none."""
    assert min(f["test_start"] for f in folds) == dt.date(2022, 10, 1)
    assert sch.DATA_START == dt.date(2022, 1, 1)
    assert sch.IS_START == dt.date(2022, 4, 1)
    assert folds[0]["train_start"] == sch.IS_START


def test_the_schedule_is_a_pure_function_of_the_constants():
    """It reads no bar, so the geometry above is checkable without data and
    cannot drift with the dataset."""
    tree = ast.parse(open(sch.__file__).read())
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == "build_schedule":
            called = {n.func.attr for n in ast.walk(node)
                      if isinstance(n, ast.Call)
                      and isinstance(n.func, ast.Attribute)}
            for banned in ("read_parquet", "read_table", "build", "load_1m"):
                assert banned not in called, banned
            return
    raise AssertionError("build_schedule not found")
