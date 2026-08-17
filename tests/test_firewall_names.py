"""THE BANNED-NAME LIST IS DEFINED ONCE, AND THIS IS WHAT KEEPS IT THAT WAY.

THIS MODULE IS THE POINT OF THE CHANGE THAT CREATED IT. Centralising the list
fixes the drift that existed; only this test stops it recurring. Before it,
eighteen modules each wrote the list out and four of them had fallen three names
behind, silently, with every test passing.

    A GUARD COPIED IS A GUARD THAT WILL DIVERGE. THE COPY IS THE DEFECT, NOT THE
    DIVERGENCE.

DETECTION RUNS OVER AST NODES, NEVER RAW TEXT, per the standing verification rule
at `docs/design/04_1a_denomination_amendment_1.md` §7 and
`docs/prompts/STANDING_RULES.md` §6.1. A raw-text search would fire on every
module that names the list in a docstring in order to state the prohibition it
obeys, which is content those modules are required to carry.
"""

import ast
import os

import pytest

from src import firewall
from src.firewall import PERFORMANCE_NAMES

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

#: Trees searched for competing definitions. `data/` is never walked.
SEARCHED = ("src", "tests")

#: The one file allowed to bind the list as a literal.
CANONICAL = os.path.join("src", "firewall.py")

#: This module. It imports the list to test it and enforces no guard of its own.
THIS_FILE = os.path.join("tests", "test_firewall_names.py")


def _python_files():
    for tree_root in SEARCHED:
        for base, dirs, files in os.walk(os.path.join(ROOT, tree_root)):
            dirs[:] = [d for d in dirs if d != "__pycache__"]
            for fn in sorted(files):
                if fn.endswith(".py"):
                    yield os.path.relpath(os.path.join(base, fn), ROOT)


def _literal_string_collections(path):
    """Every assignment in `path` binding a literal collection of strings.

    Yields (lineno, target_name, values). Over AST nodes; the file's text is
    parsed, never searched.
    """
    tree = ast.parse(open(os.path.join(ROOT, path)).read())
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue
        try:
            value = ast.literal_eval(node.value)
        except Exception:
            continue
        if not isinstance(value, (list, tuple, set, frozenset)):
            continue
        value = tuple(value)
        if not value or not all(isinstance(v, str) for v in value):
            continue
        for target in node.targets:
            if isinstance(target, ast.Name):
                yield node.lineno, target.id, value


# ---------------------------------------------------------------------------
# THE CENTRAL ASSERTION.
# ---------------------------------------------------------------------------

def test_NO_MODULE_DEFINES_ITS_OWN_COPY_OF_THE_BANNED_LIST():
    """THE ASSERTION THIS MODULE EXISTS FOR.

    A copy is a literal collection of strings that is a SUBSET of the canonical
    twelve. That is the right discriminator and it is structural rather than a
    tuned threshold:

      * the old twelve-name copies were the full set -- a subset of itself;
      * the old nine-name variant was a proper subset;
      * `src/analysis/dispersion.py`'s `FORBIDDEN_TERMS` is NOT a subset, because
        it bans prose forms and other quantities entirely -- "mean r", "median
        r", "holding time", "exit_reason" -- and is a different guard protecting
        a different thing. It is not caught, and it must not be, because
        replacing it with this list would REMOVE protections.

    A count-based rule would have had to choose a number and would have caught or
    missed `FORBIDDEN_TERMS` depending on that choice.
    """
    offenders = []
    for path in _python_files():
        if path == CANONICAL:
            continue
        for lineno, name, values in _literal_string_collections(path):
            if set(values) <= set(PERFORMANCE_NAMES):
                offenders.append("%s:%d %s = %d names" % (path, lineno, name,
                                                          len(values)))
    assert not offenders, (
        "these bind a copy of the banned-name list; import it from "
        "src.firewall instead:\n  " + "\n  ".join(offenders))


#: The eighteen modules that enforced the list when it was centralised. Named by
#: extension rather than counted, so that a module DROPPING its guard fails while
#: a new module ADDING one does not. A bare count would have done the opposite.
ENFORCING_MODULES = tuple(os.path.join("tests", name) for name in (
    "test_budget_cost.py", "test_exit_spec.py", "test_exposure_profile.py",
    "test_floor_curve.py", "test_haircut_floor_curve.py",
    "test_haircut_share.py", "test_haircut_share_rerun.py",
    "test_intrabar_span.py", "test_portfolio_path.py", "test_risk_budget.py",
    "test_risk_unit_floor_curve.py", "test_rsi_breakout_profile.py",
    "test_sealed_1m.py", "test_sizing.py", "test_sizing_drag.py",
    "test_sweep_population.py", "test_timeframe_resample.py",
    "test_venue_constraints.py"))


def test_every_enforcing_module_imports_the_canonical_list():
    """THE OTHER HALF: the guards must still exist, and must reach the list by
    import. A module that dropped its guard entirely would pass the test above.

    STATED AS A SUPERSET RELATION, NOT A COUNT. The count form asserted exactly
    eighteen importers and fired against `tests/test_level_consequences.py`,
    which legitimately imports the list to check a module is clean. **A criterion
    written from a snapshot of how many modules happened to enforce the guard is
    the recurring defect class applied to a test.** The membership is what
    matters and it is named by extension.
    """
    importers = set()
    for path in _python_files():
        if path == CANONICAL:
            continue
        tree = ast.parse(open(os.path.join(ROOT, path)).read())
        for node in ast.walk(tree):
            if (isinstance(node, ast.ImportFrom)
                    and node.module == "src.firewall"
                    and any(a.name == "PERFORMANCE_NAMES" for a in node.names)):
                importers.add(path)
    missing = sorted(set(ENFORCING_MODULES) - importers)
    assert not missing, (
        "these enforced the banned-name guard and no longer import the list: %s"
        % missing)
    assert len(ENFORCING_MODULES) == 18


# ---------------------------------------------------------------------------
# THE LIST ITSELF.
# ---------------------------------------------------------------------------

def test_the_list_is_report_25s_twelve():
    assert len(PERFORMANCE_NAMES) == 12
    assert len(set(PERFORMANCE_NAMES)) == 12
    assert set(PERFORMANCE_NAMES) == {
        "expectancy", "win_rate", "winrate", "profit_factor", "sharpe",
        "sortino", "net_pnl", "gross_pnl", "drawdown", "r_multiple", "equity",
        "pnl"}


def test_the_widening_is_pinned_so_a_removal_FAILS():
    """`drawdown`, `sortino` and `gross_pnl` are the three report 24 §9.5 found
    missing and report 25 added. Four modules were still missing them when the
    list was centralised."""
    assert set(firewall.WIDENED_IN_REPORT_25) <= set(PERFORMANCE_NAMES)
    assert set(firewall.WIDENED_IN_REPORT_25) == {"drawdown", "sortino",
                                                  "gross_pnl"}
    assert set(firewall.INHERITED_FROM_REPORT_24) < set(PERFORMANCE_NAMES)
    assert set(firewall.INHERITED_FROM_REPORT_24) | set(
        firewall.WIDENED_IN_REPORT_25) == set(PERFORMANCE_NAMES)


def test_the_list_only_ever_grows():
    """Stated in the source and asserted here: the historical list is a STRICT
    subset, so a name can be added and none can be dropped without failing."""
    assert len(firewall.INHERITED_FROM_REPORT_24) == 9
    assert set(PERFORMANCE_NAMES) - set(firewall.INHERITED_FROM_REPORT_24) == {
        "drawdown", "sortino", "gross_pnl"}


# ---------------------------------------------------------------------------
# THE HELPERS.
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("name,expected", [
    ("net_pnl", True),
    ("net_pnl_total", True),
    ("total_gross_pnl", True),
    ("SharpeRatio", True),
    ("stop_distance", False),
    ("taker_fee", False),
    ("", False),
])
def test_is_banned_matches_on_substring_case_insensitively(name, expected):
    assert firewall.is_banned(name) is expected


def test_banned_in_returns_every_hit_in_list_order():
    assert firewall.banned_in("sharpe and sortino and equity") == (
        "sharpe", "sortino", "equity")
    assert firewall.banned_in("stop distance") == ()


def test_the_canonical_module_imports_nothing():
    """It is a list and two helpers. An import here would give the firewall a
    dependency, and a dependency is something that can fail to load."""
    tree = ast.parse(open(os.path.join(ROOT, CANONICAL)).read())
    assert not [n for n in ast.walk(tree)
                if isinstance(n, (ast.Import, ast.ImportFrom))]
