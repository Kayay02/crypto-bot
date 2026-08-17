"""THE HOLDOUT-BOUNDARY EXCLUSION, AND THE PROOF IT REPLACED.

WHAT CHANGED AND WHY THIS FILE EXISTS. Until the exclusion was implemented, the
seal's proof in the execution path was a CRASH: a `full`-mode run over the whole
in-sample window walked its hourly grid past 2024-12-31, asked the sealed loader
for a 2025 hour, and was refused. That refusal was live evidence the seal held,
and `docs/design/04_2c_run_structure.md` section 4.4's rule removes it -- after
the exclusion the run completes and the crash never happens.

    A PROOF THAT DISAPPEARS WHEN A DEFECT IS FIXED WAS NEVER A PROOF OF THE
    THING IT SEEMED TO PROVE. IT IS REPLACED HERE BY TWO PROPERTIES THAT SURVIVE
    THE FIX.

THE FIRST -- THE LOADER STILL REFUSES. Handed a sealed partition, a sealed year
or a sealed range directly, it raises. That is asserted here on the REAL loader,
because the property is about the real loader and a fake one cannot carry it.
Nothing here disables a pre-read guard, so per report 29 section 9.3 facing the
real directory is permitted: every one of these requests is refused BEFORE a file
is opened, which each assertion checks rather than assumes.

THE SECOND -- THE RUN NEVER ASKS. A population carrying a boundary-crossing
candidate excludes it and requests no sealed hour. This is the property the
crash could never establish: a refusal proves the barrier works, and only a
silent, complete run with an empty request log proves the barrier was never
approached.

THE ORDERING IS THE POINT, AND IT IS WHAT MAKES THE SECOND TEST MEANINGFUL. The
decision is arithmetic on the entry stamp -- the scheduled exit is a calendar
function of it -- so no sealed bar is touched to find out whether a sealed bar is
needed. A test that let the exclusion run after a loader complaint would be
asserting nothing: refusals would be routine and would stop carrying information.

NO OUTCOME QUANTITY IS COMPUTED OR INSPECTED ANYWHERE IN THIS FILE. Every
assertion is over a count of exclusions, a request log, a timestamp or an
exception type. `docs/design/04_2d_aggregation.md` section 7.1 records why a
count of exclusions is not an outcome: it requires no exit to be resolved and no
level to be evaluated.
"""

import ast
import os
import sys

import pandas as pd
import pytest

from src.timeframe import sealed_1m as sealed

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src", "engine"))

import portfolio as pf  # noqa: E402
import sizing  # noqa: E402

from src.analysis import exposure_profile as ep  # noqa: E402

LONG = pf.LONG
BAR_MS = pf.BAR_MS
MINUTE_MS = pf.MINUTE_MS

#: Synthetic reference cells. Hand-written prices; no bar is read to obtain one.
CELLS = (("BTCUSDT", 30_000.0, 100.0),
         ("ETHUSDT", 2_000.0, 5.0),
         ("SOLUSDT", 100.0, 0.3))


@pytest.fixture(scope="module")
def cfg():
    return ep.cost_config()


@pytest.fixture(scope="module")
def specs():
    return sizing.load_symbol_specs()


@pytest.fixture(scope="module")
def ticks():
    return sizing.load_tick_schedules()


def _candidate(symbol, direction, signal_bar_ts, entry_price, atr):
    """One candidate row, with the time exit from the FROZEN calendar function.

    `exposure_profile.max_hold_exit` owns the settlement index and is called
    here rather than reimplemented, so a fixture cannot drift from the rule the
    exclusion is testing against.
    """
    exit_bar, exit_close, _ = ep.max_hold_exit(signal_bar_ts)
    return {
        "ts": int(signal_bar_ts),
        "symbol": symbol,
        "direction": direction,
        "entry_price": float(entry_price),
        "atr": float(atr),
        "entry_close_ms": int(ep.bar_close_ms(signal_bar_ts)),
        "exit_bar_ts": int(exit_bar),
        "exit_close_ms": int(exit_close),
    }


def _frame(rows):
    return pd.DataFrame(rows)


def _in_sample_bar(hours_before_boundary):
    """A 1h grid instant that many hours before the seal. SYNTHETIC: no bar is
    read at this timestamp, it only has to be a valid grid instant."""
    return sealed.sealed_boundary_ms() - hours_before_boundary * BAR_MS


class Recording1m:
    """A synthetic 1m series that REFUSES anything at or past the boundary.

    It stands in for the real loader's refusal without facing the real
    directory, so a test can assert both halves at once: that the run completed,
    and that had it asked for a sealed minute it would have been caught here.
    """

    def __init__(self):
        self.series = {}
        self.calls = []

    def flat(self, symbol, start_ms, end_ms, price):
        n = (int(end_ms) - int(start_ms)) // MINUTE_MS
        ts = [int(start_ms) + i * MINUTE_MS for i in range(n)]
        self.series[symbol] = pd.DataFrame({
            "ts": ts,
            "high": [float(price)] * n,
            "low": [float(price)] * n,
            "close": [float(price)] * n,
        })
        return self

    def loader(self, symbol, lo, hi):
        self.calls.append((str(symbol), int(lo), int(hi)))
        if int(hi) > sealed.sealed_boundary_ms():
            raise sealed.SealBreach(
                "the fixture loader was asked for [%d, %d), which meets the "
                "sealed window; the exclusion did not run" % (int(lo), int(hi)))
        frame = self.series[symbol]
        return frame[(frame["ts"] >= int(lo))
                     & (frame["ts"] < int(hi))].reset_index(drop=True)


# ---------------------------------------------------------------------------
# 1. THE FIRST REPLACEMENT PROOF -- THE LOADER STILL REFUSES.
# ---------------------------------------------------------------------------

def test_the_sealed_loader_REFUSES_a_sealed_partition_handed_to_it_directly():
    """THE PROPERTY THE CRASH USED TO DEMONSTRATE, ASSERTED ON ITS OWN.

    Four ways of handing the loader a sealed partition, and all four are
    refused. None of them opens a file: the year check, the range check and the
    opened-set assertion are all path and integer arithmetic, which is the whole
    design of the three layers.
    """
    boundary = sealed.sealed_boundary_ms()
    symbol = CELLS[0][0]

    # (1) NAMING A SEALED YEAR. Refused rather than quietly narrowed.
    with pytest.raises(sealed.SealBreach):
        sealed.allowed_paths(symbol, years=[2025])

    # (2) A RANGE WHOLLY INSIDE THE SEALED WINDOW.
    with pytest.raises(sealed.SealBreach):
        sealed.load(symbol, boundary, boundary + BAR_MS)

    # (3) A RANGE THAT MERELY MEETS IT -- one millisecond past the largest
    #     readable request. Refused, not truncated to the readable part.
    with pytest.raises(sealed.SealBreach):
        sealed.load(symbol, boundary - BAR_MS, boundary + 1)

    # (4) A SEALED PATH HANDED TO THE OPENED-SET ASSERTION. The path is built by
    #     string arithmetic and is never opened, listed or stat-ed.
    sealed_path = sealed.partition_dir(symbol, 2025) + os.sep + "part.parquet"
    assert sealed.is_sealed_path(sealed_path)
    with pytest.raises(sealed.SealBreach):
        sealed.assert_opened([sealed_path], "a test handing it one directly")


def test_the_largest_readable_request_is_still_permitted():
    """THE OTHER HALF, WITHOUT WHICH THE FIRST TEST IS SATISFIED BY A LOADER
    THAT REFUSES EVERYTHING. The boundary is exclusive on the end, so a request
    ending exactly at it is the largest readable one and must succeed."""
    boundary = sealed.sealed_boundary_ms()
    frame = sealed.load(CELLS[0][0], boundary - BAR_MS, boundary)
    assert len(frame), "the readable side of the boundary must still load"
    assert int(frame["ts"].max()) < boundary


# ---------------------------------------------------------------------------
# 2. THE SECOND REPLACEMENT PROOF -- THE RUN EXCLUDES AND NEVER ASKS.
#
# THIS IS THE TEST THAT MUST FAIL IF THE EXCLUSION IS REMOVED.
# ---------------------------------------------------------------------------

def test_a_boundary_crossing_candidate_is_EXCLUDED_and_no_sealed_hour_is_ASKED(
        cfg, specs, ticks):
    """THE COMMITTED RULE, END TO END, ON A MIXED POPULATION.

    `docs/design/04_2c_run_structure.md` section 4.4: a candidate whose
    scheduled max-hold exit falls at or after the seal is excluded, and excluded
    BEFORE any 1m bar is requested on its behalf.

    THE POPULATION IS MIXED ON PURPOSE. A run containing only crossing
    candidates would pass with a loop that never executed; one containing only
    in-sample candidates would pass with no exclusion at all. Both must hold at
    once: the crossing candidate is dropped, the in-sample one is evaluated, and
    the request log stops short of the boundary.

    IF THE EXCLUSION IS REMOVED THIS TEST FAILS. The grid runs to
    `max(exit_bar)`, which the crossing candidate puts inside the sealed window,
    and the fixture loader is asked for an hour past the boundary.
    """
    boundary = sealed.sealed_boundary_ms()
    symbol, entry, atr = CELLS[0]

    crossing = _candidate(symbol, LONG, _in_sample_bar(1), entry, atr)
    assert crossing["exit_close_ms"] >= boundary, "the fixture must cross it"

    inside = _candidate(symbol, LONG, _in_sample_bar(72), entry, atr)
    assert inside["exit_close_ms"] < boundary, "the fixture must NOT cross it"

    bars = Recording1m().flat(symbol, inside["entry_close_ms"] - BAR_MS,
                              boundary, entry)
    cache = pf.Bars1mCache(loader=bars.loader)
    result = pf.run(_frame([inside, crossing]), cfg, specs=specs, ticks=ticks,
                    mode=pf.MODE_FULL, firewall_token=pf.FIREWALL_TOKEN,
                    cache=cache)

    # THE CROSSING CANDIDATE IS GONE, AND IT IS THE ONE THAT WENT.
    assert result["seal_excluded"] == 1
    excluded = result["seal_excluded_rows"]
    assert int(excluded["ts"].iloc[0]) == crossing["ts"]
    assert int(excluded["exit_close_ms"].iloc[0]) == crossing["exit_close_ms"]

    # THE IN-SAMPLE ONE WAS EVALUATED, so the exclusion is not a blanket refusal.
    assert result["n_taken"] == 1
    assert int(result["positions"]["entry_ts"].iloc[0]) == inside["ts"]

    # AND NO SEALED HOUR WAS ASKED FOR -- by the cache, or by the loader behind
    # it. Asserted over what was REQUESTED, not over what came back: a row
    # filter cannot tell you which hours were asked for.
    assert cache.requests, "the run must actually have asked for 1m bars"
    for _, lo, hi in cache.requests:
        assert hi <= boundary, (lo, hi)
    assert bars.calls == cache.requests
    assert max(hi for _, _, hi in cache.requests) <= boundary


def test_a_population_of_ONLY_crossing_candidates_asks_the_REAL_loader_nothing(
        cfg, specs, ticks):
    """THE SAME PROPERTY AGAINST THE LOADER THE MODULE IS ACTUALLY WIRED TO.

    This is the direct replacement for the refusal that used to stand here. The
    cache faces the REAL sealed loader and the run completes in `full` mode
    without raising, because every candidate was excluded before a request was
    formed. `requests` is empty, which is the assertion: not that a sealed read
    was refused, but that none was attempted.

    NO REAL BAR IS READ. The population is entirely crossing, so there is no
    in-sample position to resolve either, and the request log's emptiness is
    checked rather than assumed.
    """
    boundary = sealed.sealed_boundary_ms()
    rows = [_candidate(sym, LONG, _in_sample_bar(1), entry, atr)
            for sym, entry, atr in CELLS]
    for row in rows:
        assert row["exit_close_ms"] >= boundary

    cache = pf.Bars1mCache()
    assert cache._loader is sealed.load, "this one faces the REAL loader"
    result = pf.run(_frame(rows), cfg, specs=specs, ticks=ticks,
                    mode=pf.MODE_FULL, firewall_token=pf.FIREWALL_TOKEN,
                    cache=cache)

    assert cache.requests == [], cache.requests
    assert cache.misses == 0 and cache.hits == 0
    assert result["n_taken"] == 0 and result["n_skipped"] == 0
    assert result["seal_excluded"] == len(rows)


def test_the_exclusion_applies_in_max_hold_mode_too(cfg, specs, ticks):
    """SECTION 4.5 COMMITS A POPULATION, NOT A MODE-CONDITIONAL FILTER.

    `max_hold` reads no 1m bar, so nothing here is about the seal's mechanics. A
    candidate held to a scheduled exit inside the seal still occupies a budget
    unit until then and still changes which other candidates are taken, so a
    rule applied in one mode and not the other would make the evaluated
    population depend on how exits resolve -- which is the path dependence the
    boundary rule exists to refuse.
    """
    boundary = sealed.sealed_boundary_ms()
    symbol, entry, atr = CELLS[0]
    crossing = _candidate(symbol, LONG, _in_sample_bar(1), entry, atr)
    inside = _candidate(symbol, LONG, _in_sample_bar(72), entry, atr)

    result = pf.run(_frame([inside, crossing]), cfg, specs=specs, ticks=ticks,
                    mode=pf.MODE_MAX_HOLD)
    assert result["seal_excluded"] == 1
    assert result["n_taken"] == 1
    assert int(result["positions"]["exit_ts"].max()) < boundary


# ---------------------------------------------------------------------------
# 3. THE RULE'S OWN TERMS.
# ---------------------------------------------------------------------------

def test_the_boundary_is_READ_and_is_the_single_definition():
    """A SECOND DECLARATION IS A SECOND THING THAT CAN DRIFT."""
    assert pf.seal_boundary_ms() == sealed.sealed_boundary_ms()
    tree = ast.parse(open(pf.__file__).read())
    literals = {n.value for n in ast.walk(tree)
                if isinstance(n, ast.Constant)
                and isinstance(n.value, (int, float))
                and not isinstance(n.value, bool)}
    assert sealed.sealed_boundary_ms() not in literals
    for year in (2025, 2026):
        assert year not in literals


def test_at_or_after_is_the_comparison_and_strictly_before_is_the_other_side():
    """THE RULE'S WORDING, ON THE THREE CASES THAT DISTINGUISH IT.

    A candidate exiting one millisecond before the seal is evaluated; one
    exiting exactly AT it is excluded; one exiting after it is excluded. The
    middle case is the one a `>` would get wrong, and it is reachable: the seal
    falls on a funding settlement instant, so a scheduled exit lands on it
    exactly.
    """
    boundary = sealed.sealed_boundary_ms()
    assert not pf.crosses_seal(boundary - 1, boundary)
    assert pf.crosses_seal(boundary, boundary)
    assert pf.crosses_seal(boundary + 1, boundary)


def test_the_decision_reads_no_bar_and_touches_only_the_schedule_stamps():
    """ARITHMETIC ON A STAMP THE FROZEN CALENDAR FUNCTION ALREADY DERIVED.

    Asserted structurally: the predicate's body is one comparison over its two
    arguments, so there is no route from it to a loader, a frame or a file.
    """
    tree = ast.parse(open(pf.__file__).read())
    predicate = [n for n in ast.walk(tree)
                 if isinstance(n, ast.FunctionDef) and n.name == "crosses_seal"]
    assert len(predicate) == 1
    calls = {n.func.id for n in ast.walk(predicate[0])
             if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)}
    assert calls == {"int"}, calls
    attributes = {n.attr for n in ast.walk(predicate[0])
                  if isinstance(n, ast.Attribute)}
    assert attributes == set(), attributes


def test_the_scheduled_exit_is_used_and_never_a_realised_one():
    """A REALISED EXIT IS AN OUTCOME. Making membership depend on it would make
    membership path-dependent, which section 4.4 refuses in terms.

    The predicate is reached from exactly one place in `run`, and that place
    reads the candidate frame's scheduled stamp. Nothing in the resolved-exit
    vocabulary appears in the exclusion at all.
    """
    tree = ast.parse(open(pf.__file__).read())
    run = [n for n in ast.walk(tree)
           if isinstance(n, ast.FunctionDef) and n.name == "run"][0]
    called = [n for n in ast.walk(run)
              if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
              and n.func.id == "_partition_on_seal"]
    assert len(called) == 1, "one exclusion site, and no second"

    split = [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)
             and n.name == "_partition_on_seal"][0]
    # THE DOCSTRING IS DROPPED BEFORE THE SEARCH. This project's modules are
    # written to state the rules they obey, so a check that cannot tell a
    # citation from a use will demand the removal of the citation.
    doc = ast.get_docstring(split, clean=False)
    read = {n.value for n in ast.walk(split)
            if isinstance(n, ast.Constant) and isinstance(n.value, str)
            and n.value != doc}
    assert read == {"exit_close_ms"}, read


def test_the_exclusion_runs_BEFORE_the_grid_and_before_any_1m_request():
    """ORDER IS LOAD-BEARING AND IS ASSERTED ON THE SOURCE, NOT ON A COMMENT.

    Inside `run`, the exclusion's statement index must precede both the grid's
    construction and the loop that holds the only `cache.hour` call. If the
    exclusion ran later, the grid would already have been built out to a sealed
    hour from a candidate the rule excludes.
    """
    tree = ast.parse(open(pf.__file__).read())
    run = [n for n in ast.walk(tree)
           if isinstance(n, ast.FunctionDef) and n.name == "run"][0]

    def line_of(predicate):
        return min(n.lineno for n in ast.walk(run) if predicate(n))

    exclusion = line_of(lambda n: isinstance(n, ast.Call)
                        and isinstance(n.func, ast.Name)
                        and n.func.id == "_partition_on_seal")
    grid = line_of(lambda n: isinstance(n, ast.Call)
                   and isinstance(n.func, ast.Name)
                   and n.func.id == "_hourly_grid")
    request = line_of(lambda n: isinstance(n, ast.Attribute)
                      and n.attr == "hour")
    assert exclusion < grid < request, (exclusion, grid, request)


# ---------------------------------------------------------------------------
# 4. THE COUNT'S SURFACE.
# ---------------------------------------------------------------------------

def test_the_count_is_reported_per_symbol_INCLUDING_ZEROS(cfg, specs, ticks):
    """`docs/design/04_2d_aggregation.md` section 7.3.

    A count that appears only when non-zero tells a reader nothing when absent,
    because absence is ambiguous between "zero" and "not checked". The keys come
    from the input population, so a symbol with no exclusion still appears.
    """
    rows = [_candidate(sym, LONG, _in_sample_bar(72), entry, atr)
            for sym, entry, atr in CELLS]
    rows.append(_candidate(CELLS[0][0], LONG, _in_sample_bar(1),
                           CELLS[0][1], CELLS[0][2]))

    result = pf.run(_frame(rows), cfg, specs=specs, ticks=ticks,
                    mode=pf.MODE_MAX_HOLD)
    per_symbol = result["seal_excluded_per_symbol"]
    assert set(per_symbol) == {sym for sym, _, _ in CELLS}
    assert per_symbol[CELLS[0][0]] == 1
    assert per_symbol[CELLS[1][0]] == 0
    assert per_symbol[CELLS[2][0]] == 0
    assert sum(per_symbol.values()) == result["seal_excluded"]


def test_a_population_with_no_crossing_candidate_reports_zero(cfg, specs,
                                                              ticks):
    """THE ZERO CASE IS THE ONE THAT MATTERS. A branch that is never reported is
    a branch nobody can tell was checked."""
    rows = [_candidate(sym, LONG, _in_sample_bar(72), entry, atr)
            for sym, entry, atr in CELLS]
    result = pf.run(_frame(rows), cfg, specs=specs, ticks=ticks,
                    mode=pf.MODE_MAX_HOLD)
    assert result["seal_excluded"] == 0
    assert result["seal_excluded_per_symbol"] == {
        sym: 0 for sym, _, _ in CELLS}
    assert list(result["seal_excluded_rows"].columns) == list(
        pf.SEAL_EXCLUDED_COLUMNS)
    assert len(result["seal_excluded_rows"]) == 0


def test_an_empty_population_still_carries_the_count(cfg, specs, ticks):
    result = pf.run(_frame([]), cfg, specs=specs, ticks=ticks,
                    mode=pf.MODE_MAX_HOLD)
    assert result["seal_excluded"] == 0
    assert result["seal_excluded_per_symbol"] == {}


def test_the_excluded_rows_carry_the_stamps_a_partition_cell_is_assigned_BY(
        cfg, specs, ticks):
    """SECTION 7.2 REQUIRES THE COUNT PER PARTITION CELL AND PER SYMBOL, and
    this module supplies per symbol plus the stamps.

    The partition is nine test windows plus an unassigned row and a position is
    assigned to a period by its entry bar. This module has no fold schedule and
    must not acquire one -- a test asserts it imports none -- so the cell
    decomposition is a projection of the entry stamps emitted here rather than
    something the module withholds.
    """
    symbol, entry, atr = CELLS[0]
    crossing = _candidate(symbol, LONG, _in_sample_bar(1), entry, atr)
    result = pf.run(_frame([crossing]), cfg, specs=specs, ticks=ticks,
                    mode=pf.MODE_MAX_HOLD)

    rows = result["seal_excluded_rows"]
    assert list(rows.columns) == list(pf.SEAL_EXCLUDED_COLUMNS)
    assert "ts" in rows.columns, "the stamp a partition cell is assigned by"
    assert int(rows["ts"].iloc[0]) == crossing["ts"]
    assert int(rows["entry_close_ms"].iloc[0]) == crossing["entry_close_ms"]

    # AND NOTHING RESOLVED, SIZED OR EVALUATED TRAVELS WITH THEM.
    for banned in ("exit_price", "exit_reason", "qty", "entry_price",
                   "realised_risk_usd", "nominal_risk_usd"):
        assert banned not in rows.columns, banned


# ---------------------------------------------------------------------------
# 5. WHAT THIS FILE MAY NOT DO.
# ---------------------------------------------------------------------------

def test_full_mode_here_faces_a_synthetic_loader_except_where_NOTHING_IS_ASKED():
    """THE CONSTRAINT OF THIS FILE, ASSERTED OVER ITS OWN AST.

    Report 29 section 9.3's rule is binding: a mutation that disables a pre-read
    guard never faces the real data directory. Nothing here disables one, and
    the single `full`-mode call that faces the real loader is the one whose own
    assertion is that the request log is EMPTY.
    """
    tree = ast.parse(open(__file__).read())
    exempt = {
        "test_a_population_of_ONLY_crossing_candidates_asks_the_REAL_loader_"
        "nothing"}

    for function in ast.walk(tree):
        if not isinstance(function, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for call in ast.walk(function):
            if not (isinstance(call, ast.Call)
                    and isinstance(call.func, ast.Attribute)
                    and call.func.attr == "run"):
                continue
            mode = [kw.value for kw in call.keywords if kw.arg == "mode"]
            if not mode:
                continue
            names = {n.attr for n in ast.walk(mode[0])
                     if isinstance(n, ast.Attribute)}
            if "MODE_FULL" not in names or function.name in exempt:
                continue
            assert "cache" in {kw.arg for kw in call.keywords}, (
                "%s runs full mode without a synthetic cache" % function.name)


def test_no_outcome_quantity_is_touched_by_this_file():
    """THE FIREWALL, OVER THIS FILE'S OWN NAMES AND STRINGS."""
    from src.firewall import PERFORMANCE_NAMES

    tree = ast.parse(open(__file__).read())
    docs = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef,
                             ast.ClassDef)):
            doc = ast.get_docstring(node, clean=False)
            if doc is not None:
                docs.add(doc)

    blob = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            blob.append(node.id)
        elif isinstance(node, ast.Attribute):
            blob.append(node.attr)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef,
                               ast.ClassDef)):
            blob.append(node.name)
        elif isinstance(node, ast.Constant) and isinstance(node.value, str):
            if node.value not in docs:
                blob.append(node.value)

    text = " ".join(blob).lower()
    for banned in PERFORMANCE_NAMES:
        assert banned not in text, banned
