"""THE TREE-WIDE CONTAINMENT GUARD, AND THE FIXTURE CARVE-OUT'S CONDITIONS.

WHAT THIS ENFORCES. `docs/design/04_2a_artifact_containment.md` section 3.2
prohibits opening the outcome-bearing artifacts its section 3.1 names, section
3.3 enumerates the existing readers as a CLOSED SET, and section 3.6 commits this
file:

    A RULE ENFORCED ONLY BY INTENTION IS THE SHAPE OF EVERY DEFECT IN THE LEDGER.

The ledger's recurring class is a criterion written from a mental model rather
than from what the code does. A prohibition nobody can check is exactly that: a
belief about the repository's behaviour, held in place by care. THE GUARD IS WHAT
CONVERTS IT INTO A PROPERTY.

WHAT IT ADDS TO `tests/test_artifact_containment.py`, which report 41 committed.
That file asserts that no ENGINE module and no POINT 4 ANALYSIS module names
these artifacts. It does not cover the whole tree, and section 3.6 says so. This
one covers every `.py` file under `src/` and `tests/`.

ASSERTED AGAINST THE CLOSED SET, NEVER AGAINST A COUNT. A count would pass when
one reader was removed and another added, which is the substitution the closed
set exists to forbid. The permitted set below is transcribed from section 3.3 and
from report 41 section 4.1, and NO NEW READER JOINS IT WITHOUT AMENDING THAT
DOCUMENT -- editing the tuple here is not amending it.

DETECTION RUNS OVER AST NODES, NEVER OVER RAW TEXT, per the standing rule at
`docs/design/04_1a_denomination_amendment_1.md` section 7. This repository's
modules are written to state the prohibitions they obey, so a raw-text search
fires on every docstring that names an artifact in order to record that it must
not be opened -- and a check that cannot distinguish a citation from a violation
will demand the removal of the citation.

    NO ARTIFACT IS OPENED HERE, INCLUDING TO TEST THE GUARD. Every assertion runs
    over parsed Python source, over path strings assembled by arithmetic, and
    over `os.path.exists`. Not one test reads a byte out of any artifact named
    below. A containment test that opened what it contains would be the defect it
    exists to prevent -- and section 3.2 is explicit that the confirming read and
    the offending read are the same read.
"""

import ast
import os

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

#: The artifacts `docs/design/04_2a_artifact_containment.md` section 3.1 covers,
#: by basename. Basenames rather than paths because what matters is that no
#: reader appears, not the route it would take to the file.
#:
#: Items 4 and 5 are covered BECAUSE THEIR CONTENTS ARE UNKNOWN, not because they
#: are known to offend: an unknown is treated as containing, since the only way
#: to establish otherwise is to open the file.
PROHIBITED = ("sweep.json", "bands.json", "sweep_cells.jsonl",
              "e6_dispersion.json", "07_structural_pass_raw.json")

#: Section 3.1(6). Governed by section 4's carve-out rather than by section
#: 3.2's prohibition, so they carry their own permitted set below.
GOLDEN = ("btc_2023_01_gated.csv", "btc_2023_01_signal_ungated.csv")

#: Path constants the sweep's own modules export. A module reaching one of these
#: names the artifact WITHOUT writing its basename, which is the indirect channel
#: a basename-only check would miss.
INDIRECT = ("CELLS_PATH", "ARTIFACT_PATH", "CHECKPOINT_PATH", "TRADES_DIR")

#: SECTION 3.3's CLOSED SET, CLASS ONE -- the sweep's own modules. The apparatus
#: may read its own artifacts: being dead relative to the frozen thesis is a
#: statement about what it feeds, not a prohibition on it functioning.
SWEEP_MODULES = (os.path.join("src", "sweep", "grid.py"),
                 os.path.join("src", "sweep", "bands.py"),
                 os.path.join("src", "sweep", "sweep.py"),
                 os.path.join("src", "sweep", "sweep_report.py"))

#: SECTION 3.3's CLOSED SET, CLASS TWO -- FOUR test modules, with whether they
#: should continue reading these artifacts named as owed.
#:
#: `docs/design/04_2a_artifact_containment.md` section 3.3 recorded THREE, built
#: on `docs/handoff/41_point_4_2_artifact_audit.md` section 4.1's enumeration,
#: which missed a reader.
#:
#:     `docs/design/04_2e_housekeeping.md` SECTION 2.2 IS THE AMENDMENT THAT
#:     ADMITTED THE FOURTH. It states: "CLASS TWO OF SECTION 3.3 IS FOUR TEST
#:     MODULES, NOT THREE ... AND `tests/test_sweep_bands.py`."
#:
#: `tests/test_sweep_bands.py` MOVED HERE FROM `UNDECLARED_READERS` under that
#: document's section 2.6, which names the move as owed to a code step and
#: requires the exactness assertion below to be kept. THE SET REMAINS CLOSED ON
#: THE SAME TERMS: no fifth module joins without amending section 2.2.
GRANDFATHERED_TESTS = (os.path.join("tests", "test_sweep_prescreen.py"),
                       os.path.join("tests", "test_sweep_run.py"),
                       os.path.join("tests", "test_dispersion.py"),
                       os.path.join("tests", "test_sweep_bands.py"))

#: THE PRODUCERS, AND THEIR STATUS IS RECORDED RATHER THAN DECIDED. Each of these
#: opens its own output for WRITING and never reads it back. Section 3.3
#: enumerates READERS and report 41 section 4.1 is titled "every reader", so the
#: document's frame is reading; whether a producing write is an "opening" under
#: section 3.2's wording is NOT SETTLED BY THAT DOCUMENT. Rather than assume
#: either way, the write-only property is asserted below.
PRODUCERS = (os.path.join("src", "analysis", "dispersion.py"),
             os.path.join("src", "analysis", "structural_pass.py"),
             os.path.join("tests", "make_golden.py"))

#: SECTION 4.2 CONDITION (c) -- exactly these readers for the golden files.
CARVE_OUT_READERS = (os.path.join("tests", "test_regression_pinned_trade.py"),
                     os.path.join("tests", "test_determinism_golden.py"))

#: The guards themselves. They necessarily CONTAIN the patterns they search for
#: -- that is what makes them searches -- and neither opens an artifact, which
#: the last section asserts directly.
GUARDS = (os.path.join("tests", "test_containment_guard.py"),
          os.path.join("tests", "test_artifact_containment.py"))

#: UNDECLARED READERS. THE LIST IS NOW EMPTY, AND THE ASSERTION OVER IT IS NOT.
#:
#: THE HISTORY, KEPT BECAUSE THE EMPTY TUPLE DOES NOT EXPLAIN ITSELF.
#: `docs/handoff/41_point_4_2_artifact_audit.md` section 4.1 recorded
#: "`bands.json` -- written by `src/sweep/bands.py`; NO READER FOUND", and
#: `docs/design/04_2a_artifact_containment.md` section 3.3 built a closed set of
#: THREE test modules on that enumeration. `tests/test_sweep_bands.py` read a
#: prohibited artifact on every suite invocation. THIS GUARD FOUND IT, and pinned
#: it here rather than adding it to the closed set, because section 3.3 requires
#: an amendment and editing a tuple in a test is not amending a document.
#:
#:     `docs/design/04_2e_housekeeping.md` SECTION 2.2 IS THAT AMENDMENT, AND
#:     SECTION 2.6 DIRECTS THE MOVE. The gap this list existed to keep visible is
#:     closed by a document, which is the only way it was ever going to close.
#:
#: THE EXACTNESS ASSERTION IS KEPT, AND KEEPING IT IS THE WHOLE POINT OF LEAVING
#: THE LIST IN PLACE RATHER THAN DELETING IT. An empty tuple asserted as EXACT
#: says that no undeclared reader exists at all, so a FIFTH reader appearing
#: anywhere under `src/` or `tests/` still fails the guard, exactly as a second
#: one would have before the move. A deleted list would have asserted nothing.
UNDECLARED_READERS = ()

#: Trees walked. `data/` is never walked and no artifact directory is listed.
SEARCHED = ("src", "tests")

READ_CALLS = ("read_csv", "read_json", "read_parquet", "read_table",
              "load_cells", "load_grid", "load_bands", "read_pickle")


def _python_files():
    for tree_root in SEARCHED:
        for base, dirs, files in os.walk(os.path.join(ROOT, tree_root)):
            dirs[:] = [d for d in dirs if d != "__pycache__"]
            for name in sorted(files):
                if name.endswith(".py"):
                    path = os.path.join(base, name)
                    yield os.path.relpath(path, ROOT), path


def _tree(path):
    return ast.parse(open(path).read())


def _docstrings(tree):
    out = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef,
                             ast.ClassDef)):
            doc = ast.get_docstring(node, clean=False)
            if doc is not None:
                out.add(doc)
    return out


def _executable_strings(tree):
    """String constants that are NOT docstrings.

    A docstring naming an artifact is a citation of the rule, which the modules
    are required to carry. Only what runs counts.
    """
    docs = _docstrings(tree)
    return {n.value for n in ast.walk(tree)
            if isinstance(n, ast.Constant) and isinstance(n.value, str)
            and n.value not in docs}


def _attribute_names(tree):
    return {n.attr for n in ast.walk(tree) if isinstance(n, ast.Attribute)}


def _assigned_names(tree):
    out = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    out.add(target.id)
    return out


def _called_names(tree):
    out = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            f = node.func
            name = f.attr if isinstance(f, ast.Attribute) else (
                f.id if isinstance(f, ast.Name) else None)
            if name:
                out.add(name)
    return out


def _names_an_artifact(path, artifacts, indirect=False):
    """Does this module name one of `artifacts`, directly or indirectly?

    DIRECTLY: a non-docstring string constant carrying the basename. Path
    assembly in this repository is `os.path.join(DIR, "<basename>")`, so the
    basename is a literal wherever a path is built.

    INDIRECTLY: an attribute access to one of the sweep modules' exported path
    constants, which reaches the artifact without writing its name. A module that
    DEFINES such a constant is naming its own, which the direct check catches on
    its own terms.

    `indirect` IS OFF BY DEFAULT AND IS TURNED ON ONLY FOR THE SWEEP FAMILY.
    The constants at `INDIRECT` belong to `src/sweep/`; applying them to the
    golden fixtures would report every sweep module as a reader of a file it has
    never heard of, which is a check wrong about what it matches -- the ledger's
    recurring class applied to a verification criterion.
    """
    tree = _tree(path)
    literals = " ".join(_executable_strings(tree))
    hits = {a for a in artifacts if a in literals}
    if indirect:
        reached = _attribute_names(tree) & set(INDIRECT)
        if reached and _called_names(tree) & set(READ_CALLS + ("open",)):
            hits.add("|".join(sorted(reached)))
    return hits


# ---------------------------------------------------------------------------
# 1. THE TREE-WIDE READ GUARD. Section 3.6.
# ---------------------------------------------------------------------------

def test_NOTHING_outside_the_closed_set_names_a_prohibited_artifact():
    """SECTION 3.6's GUARD, OVER EVERY `.py` FILE UNDER `src/` AND `tests/`.

    THE PERMITTED SET IS THE CLOSED SET SECTION 3.3 NAMES, PLUS THE PRODUCERS
    WHOSE WRITE-ONLY STATUS IS ASSERTED SEPARATELY, PLUS THE TWO GUARDS. It is
    compared as a SET and never as a count: a count passes when one reader is
    removed and another added.
    """
    permitted = set(SWEEP_MODULES) | set(GRANDFATHERED_TESTS) | set(
        PRODUCERS) | set(GUARDS) | set(UNDECLARED_READERS)

    offenders = {}
    for relative, path in _python_files():
        if relative in permitted:
            continue
        hits = _names_an_artifact(path, PROHIBITED, indirect=True)
        if hits:
            offenders[relative] = sorted(hits)

    assert offenders == {}, (
        "these modules name a prohibited artifact and are not in "
        "docs/design/04_2a_artifact_containment.md section 3.3's closed set: "
        "%r. A new reader joins by AMENDING THAT DOCUMENT, not by editing this "
        "tuple." % offenders)


def test_the_UNDECLARED_readers_are_exactly_the_ones_the_audit_missed():
    """THE FINDING THIS GUARD PRODUCED. THE LIST IS NOW EMPTY AND STILL ASSERTED.

    `docs/handoff/41_point_4_2_artifact_audit.md` section 4.1 recorded that
    `bands.json` has NO READER, and `docs/design/04_2a_artifact_containment.md`
    section 3.3's closed set of three test modules rested on that enumeration.
    `tests/test_sweep_bands.py` read a prohibited artifact on every suite
    invocation, and this guard found it.

        `docs/design/04_2e_housekeeping.md` SECTION 2.2 AMENDED THE CLOSED SET TO
        FOUR, AND SECTION 2.6 DIRECTED THE MOVE. THE READER IS NOW
        GRANDFATHERED AND `UNDECLARED_READERS` IS EMPTY.

    THE NAME OF THIS TEST IS DELIBERATELY UNCHANGED. It is the identity under
    which the finding was pinned, and a reader following the trail from that
    document to this module should land on it rather than on a renamed test with
    no history.

    WHAT IT ASSERTS NOW IS STRICTLY STRONGER THAN WHAT IT ASSERTED BEFORE: that
    the set of modules reaching a prohibited artifact and not named in a
    committed document is EMPTY. A fifth reader appearing anywhere under `src/`
    or `tests/` fails here, which is what section 2.6 requires be kept.
    """
    for relative in UNDECLARED_READERS:
        path = os.path.join(ROOT, relative)
        assert os.path.exists(path), relative
        assert _names_an_artifact(path, PROHIBITED, indirect=True), (
            "%s no longer reads a prohibited artifact; if that is deliberate, "
            "remove it from UNDECLARED_READERS and record that the gap closed"
            % relative)

    declared = set(SWEEP_MODULES) | set(GRANDFATHERED_TESTS) | set(
        PRODUCERS) | set(GUARDS)
    found = {relative for relative, path in _python_files()
             if relative not in declared
             and _names_an_artifact(path, PROHIBITED, indirect=True)}
    assert found == set(UNDECLARED_READERS), sorted(found)


def test_the_guard_is_not_vacuous_and_the_grandfathered_readers_still_read():
    """THE DISCRIMINATION CHECK. Seven vacuous guards have been found in this
    project, so a guard that would pass over a tree containing no artifact
    reference at all proves nothing.

    Each named class must actually reach an artifact, or the closed set has
    drifted from what the code does -- which is the ledger's recurring defect
    applied to a verification criterion.
    """
    reaching = set()
    for relative, path in _python_files():
        if _names_an_artifact(path, PROHIBITED, indirect=True):
            reaching.add(relative)

    for module in SWEEP_MODULES[1:]:          # grid.py names grid.json only
        assert module in reaching, module
    for module in GRANDFATHERED_TESTS[1:]:    # prescreen reads grid.json only
        assert module in reaching, module
    assert set(PRODUCERS[:2]) <= reaching, sorted(PRODUCERS[:2])


def test_the_closed_set_members_all_exist():
    """A CLOSED SET NAMING A FILE THAT IS GONE IS A SET NOBODY CHECKED."""
    for relative in (SWEEP_MODULES + GRANDFATHERED_TESTS + PRODUCERS
                     + CARVE_OUT_READERS + GUARDS + UNDECLARED_READERS):
        assert os.path.exists(os.path.join(ROOT, relative)), relative


@pytest.mark.parametrize("relative", PRODUCERS[:2])
def test_a_producer_opens_its_own_output_for_WRITING_and_never_reads_it(
        relative):
    """THE STATUS SECTION 3.3 DOES NOT SETTLE, ASSERTED RATHER THAN ASSUMED.

    Section 3.3 enumerates READERS and report 41 section 4.1 is titled "every
    reader"; whether a producing WRITE is an "opening" under section 3.2's
    wording is not stated anywhere. This does not decide it. It asserts the
    narrower fact that makes the question moot for these two modules: the only
    call that reaches the artifact opens it in a write mode.
    """
    tree = _tree(os.path.join(ROOT, relative))
    docs = _docstrings(tree)

    for node in ast.walk(tree):
        if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                and node.func.id == "open"):
            continue
        target = ast.dump(node.args[0]) if node.args else ""
        if not any(a in target for a in PROHIBITED):
            continue
        modes = [a.value for a in node.args[1:]
                 if isinstance(a, ast.Constant)]
        modes += [k.value.value for k in node.keywords
                  if k.arg == "mode" and isinstance(k.value, ast.Constant)]
        assert modes, "%s: opened an artifact with no explicit mode" % relative
        for mode in modes:
            assert mode[0] in ("w", "a", "x"), (relative, mode)

    # AND NO READING CALL REACHES ONE EITHER.
    literals = " ".join(_executable_strings(tree))
    if any(a in literals for a in PROHIBITED):
        for node in ast.walk(tree):
            if (isinstance(node, ast.Call)
                    and isinstance(node.func, ast.Attribute)
                    and node.func.attr in READ_CALLS):
                dumped = ast.dump(node)
                for artifact in PROHIBITED:
                    assert artifact not in dumped, (relative, artifact)
    assert docs, "%s: the producer must state what it writes" % relative


# ---------------------------------------------------------------------------
# 2. THE FIXTURE CARVE-OUT. Section 4.2's four conditions, section 4.3's four
#    voiding cases.
# ---------------------------------------------------------------------------

def test_condition_c_EXACTLY_these_artifacts_and_EXACTLY_these_readers():
    """SECTION 4.2(c). No further fixture and no further reader.

    THE CARVE-OUT HAS TWO HALVES AND THEY ARE NOT THE SAME ACT. Section 4.2
    reads: "THE TWO GOLDEN FILES AND THE PINNED-TRADE REGRESSION MAY READ
    OUTCOME-NAMED VALUES."

      * `tests/test_determinism_golden.py` OPENS the fixture files.
      * `tests/test_regression_pinned_trade.py` OPENS NO FIXTURE AT ALL. It runs
        the engine on a frozen slice and asserts outcome-named values on one
        row, which is the other thing the carve-out permits.

    Checked separately, because a single check would either miss a new fixture
    reader or demand that the pinned trade read a file it has never read.

    `tests/make_golden.py` builds the names with an f-string and so carries no
    literal. It is the PRODUCER, named at section 4.2's own list and permitted
    below; running it does not void the carve-out, but taking an expected value
    out of what it produced does.
    """
    permitted = {CARVE_OUT_READERS[1], PRODUCERS[2]} | set(GUARDS)

    touching = set()
    for relative, path in _python_files():
        if _names_an_artifact(path, GOLDEN):
            touching.add(relative)

    assert touching - permitted == set(), (
        "a reader of the golden fixtures joined without amending "
        "docs/design/04_2a_artifact_containment.md section 4.2: %r"
        % sorted(touching - permitted))
    assert CARVE_OUT_READERS[1] in touching, (
        "the determinism fixture is no longer read; the carve-out's first half "
        "has nothing left to permit")

    # THE PINNED TRADE READS NO FIXTURE, AND THAT IS ASSERTED RATHER THAN
    # ASSUMED -- it is what keeps it inside condition (a)'s single-position
    # limb rather than inside the file-reading one.
    assert not _names_an_artifact(
        os.path.join(ROOT, CARVE_OUT_READERS[0]), GOLDEN), CARVE_OUT_READERS[0]

    # AND EXACTLY THESE ARTIFACTS: no third golden fixture appeared beside them.
    golden_dir = os.path.join(ROOT, "tests", "golden")
    present = {f for f in os.listdir(golden_dir) if f.endswith(".csv")}
    assert present == set(GOLDEN), present


#: THE ONE AGGREGATING CALL THAT ALREADY EXISTED, PINNED RATHER THAN JUDGED.
#: `tests/test_determinism_golden.py` asserts `trades["threshold_r"].nunique()
#: == 1`. See the test below for why it is neither removed nor waved through.
PINNED_AGGREGATE = (os.path.join("tests", "test_determinism_golden.py"),
                    "nunique", "threshold_r")


def test_condition_a_and_voiding_case_four_NO_AGGREGATE_OVER_THE_ROWS():
    """SECTION 4.2(a) AND SECTION 4.3's LAST VOIDING CASE.

    "ANY ASSERTION OVER AN AGGREGATE OF THE ROWS -- a sum, a mean, a count
    conditioned on an outcome column." It is named as one of the two that would
    look innocent at the time, which is why it is checked mechanically rather
    than left to review.

    OVER CALL NODES, NOT OVER TEXT: `len(...)` on a selection is a count of rows
    and is how the pinned-trade fixture asserts there is exactly ONE row, so the
    ban is on the aggregating REDUCTIONS rather than on every counting
    expression.

    ONE PRE-EXISTING CALL SURVIVES AND ITS STATUS IS NOT DECIDED HERE. See
    `test_the_ONE_pre_existing_aggregate_is_pinned_and_its_status_is_OPEN`.
    """
    banned = ("sum", "mean", "median", "std", "var", "quantile", "describe",
              "groupby", "value_counts", "nunique", "cumsum", "agg",
              "aggregate", "corr", "cov")
    module, allowed_call, _ = PINNED_AGGREGATE
    for relative in CARVE_OUT_READERS:
        called = _called_names(_tree(os.path.join(ROOT, relative)))
        for name in banned:
            if relative == module and name == allowed_call:
                continue
            assert name not in called, (relative, name)


def test_the_ONE_pre_existing_aggregate_is_pinned_and_its_status_is_OPEN():
    """A REQUIREMENT AND A COMMITTED CLAUSE MEET HERE, AND THIS DOES NOT RESOLVE
    THEM.

    THE CLAUSE. Section 4.2(a) says these tests "may not ... aggregate over
    rows", and section 4.3 voids the carve-out on "ANY ASSERTION OVER AN
    AGGREGATE OF THE ROWS -- a sum, a mean, a count conditioned on an outcome
    column." Under `docs/prompts/STANDING_RULES.md` section 5.1 the principle
    governs and the dash-list is illustration, so a distinct-count is an
    aggregate.

    THE CALL. `tests/test_determinism_golden.py` asserts that
    `trades["threshold_r"].nunique() == 1` -- that a config-DERIVED column is
    constant across the run's rows. It reads no golden-file row, it is not
    conditioned on an outcome column, and what it establishes is a derivation
    property rather than a measurement.

        WHETHER THAT FALLS INSIDE THE CLAUSE IS NOT SETTLED BY ANY COMMITTED
        DOCUMENT. IT PREDATES THE CLAUSE, AND THIS STEP IS NOT PERMITTED TO
        DECIDE IT.

    WHAT IS DONE INSTEAD. The call is pinned exactly -- one module, one
    reduction, one column -- so it cannot spread, cannot move to an outcome
    column, and cannot be joined by a second. A step that settles the question
    removes this test or removes the call.
    """
    module, call, column = PINNED_AGGREGATE
    tree = _tree(os.path.join(ROOT, module))

    sites = [n for n in ast.walk(tree)
             if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
             and n.func.attr == call]
    assert len(sites) == 1, "one pre-existing aggregate, and no second"

    subject = sites[0].func.value
    assert isinstance(subject, ast.Subscript), ast.dump(subject)
    key = subject.slice
    assert isinstance(key, ast.Constant) and key.value == column, ast.dump(key)

    from src.firewall import PERFORMANCE_NAMES
    assert column not in PERFORMANCE_NAMES, (
        "the pinned aggregate moved onto a banned name, which is the case the "
        "clause unambiguously forbids")


def test_voiding_case_one_NO_COMPARISON_OF_TWO_CONFIGURATIONS():
    """SECTION 4.3's FIRST VOIDING CASE, "which converts a determinism check into
    a comparison" -- the other of the two named as looking innocent.

    ONE CONFIGURATION PER MODULE. Both readers build their config through
    `conftest.golden_cfg`, which takes no arguments, so there is no second
    configuration for a comparison to be made against. A direct `CostConfig`
    construction would be the way a second one arrived.
    """
    for relative in CARVE_OUT_READERS:
        tree = _tree(os.path.join(ROOT, relative))
        called = _called_names(tree)
        assert "CostConfig" not in called, relative
        assert "make_cfg" not in called, relative
        assert "golden_cfg" in called, relative
        for node in ast.walk(tree):
            if (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                    and node.func.id == "golden_cfg"):
                assert not node.args and not node.keywords, (
                    "%s: golden_cfg was parameterised, which is a second "
                    "configuration" % relative)


def test_voiding_case_two_THERE_IS_EXACTLY_ONE_PINNED_TRADE():
    """SECTION 4.3's SECOND VOIDING CASE.

    "A count over two is a population of two and condition (a) then fails by
    ARITHMETIC rather than by intent." So the check is arithmetic too: one
    signal-bar constant, one selection, and the fixture's own assertion that the
    selection returned exactly one row.
    """
    relative = CARVE_OUT_READERS[0]
    tree = _tree(os.path.join(ROOT, relative))
    assigned = _assigned_names(tree)
    pins = {n for n in assigned if n.startswith("SIG_TS")}
    assert pins == {"SIG_TS"}, pins

    expected = [n for n in ast.walk(tree) if isinstance(n, ast.Assign)
                and any(isinstance(t, ast.Name) and t.id == "EXPECTED"
                        for t in n.targets)]
    assert len(expected) == 1, "one expectation table, and no second"
    assert isinstance(expected[0].value, ast.Dict), (
        "EXPECTED must be one position's values, not a collection of positions")


def test_voiding_case_three_THE_HAND_DERIVATION_IS_WRITTEN_DOWN():
    """SECTION 4.2(b) AND SECTION 4.3's THIRD VOIDING CASE.

    "A value copied from a run is not permitted, because a fixture that records
    what the system did is a measurement wearing a fixture's name." What can be
    checked mechanically is that the derivation is present and that the
    regenerator is not reachable from the readers -- a reader that imported
    `make_golden` could refresh the fixture and then assert against it.
    """
    doc = ast.get_docstring(_tree(os.path.join(ROOT, CARVE_OUT_READERS[0])))
    # WHITESPACE IS NORMALISED BEFORE THE SEARCH. The statement is wrapped
    # across lines in the source, and a check that fails on a line break is a
    # check wrong about what it matches.
    flat = " ".join(doc.split())
    assert "re-derived by hand" in flat, (
        "the pinned trade's derivation must be written down in the docstring")
    assert "not copied from a run" in flat

    for relative in CARVE_OUT_READERS:
        tree = _tree(os.path.join(ROOT, relative))
        imported = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(a.name for a in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module)
        assert "make_golden" not in imported, relative
        assert "freeze" not in _called_names(tree), relative


def test_condition_d_THE_BLANKET_NAME_BAN_IS_NOT_RELAXED_ELSEWHERE():
    """SECTION 4.2(d). The carve-out permits the two readers to name outcome
    quantities. It relaxes nothing anywhere else, and the check is that the
    permission did not spread: no module outside the carve-out and the existing
    ones asserts on a golden file's outcome columns.
    """
    from src.firewall import PERFORMANCE_NAMES

    permitted = set(CARVE_OUT_READERS) | {PRODUCERS[2]} | set(GUARDS)
    for relative, path in _python_files():
        if relative in permitted:
            continue
        tree = _tree(path)
        if not _names_an_artifact(path, GOLDEN):
            continue
        literals = " ".join(_executable_strings(tree)).lower()
        for banned in PERFORMANCE_NAMES:
            assert banned not in literals, (relative, banned)


# ---------------------------------------------------------------------------
# 3. THE CARVE-OUT IS RECORDED WHERE A DEVELOPER WILL MEET IT. Section 4.4.
# ---------------------------------------------------------------------------

def test_the_carve_out_conditions_are_recorded_in_source_and_beside_the_files():
    """SECTION 4.4: "WHATEVER CODE OR COMMENT RECORDS IT IS WRITTEN ELSEWHERE",
    on the model of `src/engine/sizing.py`'s, whose conditions are stated in the
    source and asserted by test.

    Both readers carry the four conditions in their module docstring, and the
    marker sits beside the fixtures themselves.
    """
    for relative in CARVE_OUT_READERS:
        doc = ast.get_docstring(_tree(os.path.join(ROOT, relative)))
        assert doc, relative
        assert "04_2a_artifact_containment" in doc, relative
        for marker in ("(a)", "(b)", "(c)", "(d)"):
            assert marker in doc, (relative, marker)
        assert "VOIDS IT" in doc.upper(), relative

    marker = os.path.join(ROOT, "tests", "golden", "CONTAINMENT.md")
    assert os.path.exists(marker), marker


# ---------------------------------------------------------------------------
# 4. THE DIRECTORY MARKERS. Section 3.4.
# ---------------------------------------------------------------------------

#: One per directory holding an artifact section 3.1 covers. A marker a step
#: meets before the file beats a rule it must remember.
MARKERS = (os.path.join("data", "derived", "sweep", "CONTAINMENT.md"),
           os.path.join("data", "derived", "analysis", "CONTAINMENT.md"),
           os.path.join("reports", "CONTAINMENT.md"),
           os.path.join("tests", "golden", "CONTAINMENT.md"))


@pytest.mark.parametrize("relative", MARKERS)
def test_the_directory_marker_exists_and_says_the_four_things(relative):
    """SECTION 3.4 requires each marker to state what the files are, which thesis
    they belong to, that they carry or may carry outcome quantities, and that
    section 3.2 prohibits opening them.

    READING A MARKER IS NOT READING AN ARTIFACT. The marker is this project's own
    prose, written by the step that placed it; the prohibition is on the data
    files beside it.
    """
    path = os.path.join(ROOT, relative)
    assert os.path.exists(path), relative
    text = open(path).read()

    assert "04_2a_artifact_containment" in text, relative
    assert "thesis" in text.lower(), relative
    assert "outcome" in text.lower(), relative
    if relative.startswith("tests"):
        assert "CARVE-OUT" in text.upper(), relative
    else:
        assert "OPEN" in text.upper(), relative
    assert len(text.splitlines()) > 20, relative


# ---------------------------------------------------------------------------
# 5. THIS FILE OPENS NO ARTIFACT.
# ---------------------------------------------------------------------------

def test_this_module_opens_no_artifact():
    """SECTION 3.2 IS EXPLICIT THAT THE CONFIRMING READ AND THE OFFENDING READ
    ARE THE SAME READ, so the guard must not open one to test itself.

    ASSERTED OVER CALLS AND OVER WHAT THEY ARE HANDED, NOT OVER STRING
    CONSTANTS. This file necessarily CONTAINS every basename it searches for --
    that is what makes it a search -- so a constant-based check would fire on its
    own patterns, which is the raw-text failure mode the standing verification
    rule exists to prevent.
    """
    tree = _tree(os.path.abspath(__file__))
    called = _called_names(tree)
    for banned in READ_CALLS + ("loads", "glob", "iglob", "walk_data"):
        assert banned not in called, banned

    # `open` appears, and every call site is handed Python source or a marker.
    for node in ast.walk(tree):
        if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                and node.func.id == "open"):
            continue
        dumped = ast.dump(node)
        for artifact in PROHIBITED + GOLDEN:
            assert artifact not in dumped, artifact

    # AND `os.listdir` is used once, on the fixture directory, for FILE NAMES.
    # Listing a directory is not reading a file, which is the same distinction
    # the sealed loader's layer 3 audit rests on.
    listings = [n for n in ast.walk(tree)
                if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                and n.func.attr == "listdir"]
    assert len(listings) == 1, "one directory listing, and no second"
