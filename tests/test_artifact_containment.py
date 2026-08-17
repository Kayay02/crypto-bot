"""Guards for report 41 -- the committed sweep artifacts and what may read them.

REPORT 41 FOUND NO BREACH, and the finding rests on two reachability facts:
nothing under `src/engine/` reads a sweep artifact, and no Point 4 analysis
module loads one. **Those are true today and unenforced without this file.**

NO ARTIFACT IS OPENED HERE. Every assertion runs over AST nodes and over path
constants; not one test reads a value out of `data/`. That is deliberate -- a
containment test that opened the thing it contains would be the defect it exists
to prevent.
"""

import ast
import os

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENGINE_DIR = os.path.join(ROOT, "src", "engine")

#: The tracked artifacts report 41 §3 identifies as carrying, or built from,
#: outcome quantities. Named by basename because what matters is that no reader
#: appears, not where a reader would look.
OUTCOME_BEARING = ("sweep.json", "bands.json", "sweep_cells.jsonl",
                   "e6_dispersion")

#: The Point 4 analysis chain. These may import `src.sweep.grid` -- two of them
#: do -- but must recompute from bars rather than load the committed grid.
POINT_4_CHAIN = ("risk_unit_floor_curve.py", "level_consequences.py",
                 "stop_cap_audit.py", "cap_candidates.py",
                 "haircut_floor_curve.py", "haircut_share.py",
                 "haircut_share_rerun.py", "floor_curve.py")


def _tree(path):
    return ast.parse(open(path).read())


def _string_constants(tree):
    return {n.value for n in ast.walk(tree)
            if isinstance(n, ast.Constant) and isinstance(n.value, str)}


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


# ---------------------------------------------------------------------------
# THE ENGINE.
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("module", sorted(
    f for f in os.listdir(ENGINE_DIR) if f.endswith(".py")))
def test_no_engine_module_names_an_outcome_bearing_artifact(module):
    """THE FILE-READ CHANNEL, CHECKED DIRECTLY.

    `docs/handoff/40_point_4_2_fold_audit.md` §4 established that `src/engine/`
    imports neither `src.folds` nor `src.sweep`. **An artifact read by path would
    not appear as an import**, so the path constants are checked too.
    """
    tree = _tree(os.path.join(ENGINE_DIR, module))
    literals = " ".join(_string_constants(tree)).lower()
    for name in OUTCOME_BEARING:
        assert name not in literals, (module, name)
    assert "derived/sweep" not in literals
    assert "derived/analysis" not in literals


def test_the_engine_reads_only_the_contract_cache_and_bars():
    """The discrimination check: the engine DOES read files, so the absence
    above is not the absence of any file access at all."""
    contracts = _tree(os.path.join(ENGINE_DIR, "contracts.py"))
    literals = " ".join(_string_constants(contracts))
    assert "contracts_cache.json" in literals

    simulate = _tree(os.path.join(ENGINE_DIR, "simulate.py"))
    assert "read_table" in _called_names(simulate)


# ---------------------------------------------------------------------------
# THE POINT 4 ANALYSIS CHAIN.
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("module", POINT_4_CHAIN)
def test_no_point_4_module_LOADS_the_committed_grid(module):
    """Two of these import `src.sweep.grid`. They must call its FUNCTIONS on
    bars, never `load_grid`, which would read the committed artifact."""
    path = os.path.join(ROOT, "src", "analysis", module)
    if not os.path.exists(path):
        pytest.skip("%s absent" % module)
    tree = _tree(path)
    called = _called_names(tree)
    for banned in ("load_grid", "load_cells", "load_bands", "build_grid"):
        assert banned not in called, (module, banned)
    literals = " ".join(_string_constants(tree)).lower()
    for name in OUTCOME_BEARING + ("grid.json",):
        assert name not in literals, (module, name)


def test_the_two_cap_modules_recompute_from_bars():
    """The discrimination check for the pair that DO import the sweep: they must
    call the derivation on a breakout frame, or the test above would pass on
    modules that simply never touched the sweep at all."""
    for module in ("stop_cap_audit.py", "cap_candidates.py"):
        tree = _tree(os.path.join(ROOT, "src", "analysis", module))
        called = _called_names(tree)
        assert "derived_cap" in called, module
        assert "breakout_frame" in called, module
        assert "m_star" in called, module


# ---------------------------------------------------------------------------
# THE ARTIFACTS THEMSELVES ARE NOT OPENED BY THIS FILE.
# ---------------------------------------------------------------------------

def test_this_module_opens_no_artifact():
    """A containment test that opened what it contains would be the defect.

    ASSERTED OVER CALLS, NOT OVER STRING CONSTANTS. This file necessarily
    CONTAINS the substrings it searches for -- that is what makes it a search --
    so a constant-based check would fire on its own patterns, which is the
    raw-text failure mode the standing verification rule exists to prevent.
    What matters is that nothing here READS a data file.
    """
    tree = _tree(os.path.abspath(__file__))
    called = _called_names(tree)

    for banned in ("read_csv", "read_json", "read_parquet", "read_table",
                   "load", "loads", "glob", "listdir_data"):
        assert banned not in called, banned

    # `open` appears, and only inside `_tree`, which parses Python source.
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name != "_tree":
            assert "open" not in _called_names(node), node.name
