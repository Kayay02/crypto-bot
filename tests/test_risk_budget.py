"""Guards for the pre-registered aggregate open risk budget.

THE FAILURE THESE EXIST TO CATCH IS TRANSCRIPTION DRIFT. The rule lives in two
places -- `docs/design/05_aggregate_risk_budget.md` states it and
`src/risk/budget.py` transcribes it -- and two copies of a frozen number are two
chances for them to disagree. A module edited without its document would still
import, still export plausible values, and would no longer describe the rule
that was pre-registered. So the document is PARSED and every constant is
required to equal what it says, twice: once from the canonical block and once
from the prose.

NOTHING HERE MEASURES ANYTHING. No market data, no bars, no folds, no counts.
The module under test imports nothing at all, which is asserted rather than
assumed: a constants module that could reach the data layer could stop being a
constants module without anyone editing this file.

THE PRE-REGISTRATION IS ONLY WORTH WHAT ITS COMMIT PROVES. These tests cannot
check that the level was chosen before the skip rate was known -- `git log` is
the check for that. What they can check is that the committed artifact says what
it is claimed to say, and that nothing is wired in yet.
"""

import ast
import os
import re

import pytest

from src.risk import budget


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOC_PATH = os.path.join(ROOT, "docs", "design", "05_aggregate_risk_budget.md")


@pytest.fixture(scope="module")
def doc():
    assert os.path.exists(DOC_PATH), DOC_PATH
    with open(DOC_PATH) as fh:
        return fh.read()


def _module_ast():
    return ast.parse(open(budget.__file__).read())


# ---------------------------------------------------------------------------
# 1. The constants, and the two relations the document asserts about them.
# ---------------------------------------------------------------------------

def test_the_frozen_values():
    assert budget.MAX_AGGREGATE_OPEN_RISK_USD == 120.00
    assert budget.RISK_PER_TRADE_USD == 20.00
    assert budget.ACCOUNT_CAPITAL_USD == 2000.00
    assert budget.MARGIN_MODE == "cross"
    assert budget.POSITION_MODE == "hedge"


def test_the_derived_values_are_derived_and_exact():
    """120/2000 == 0.06 and 120/20 == 6, asserted as the document states them."""
    assert 120.0 / 2000.0 == 0.06
    assert 120.0 / 20.0 == 6
    assert budget.BUDGET_FRACTION_OF_CAPITAL == 0.06
    assert budget.FULL_SIZE_POSITIONS == 6
    assert isinstance(budget.FULL_SIZE_POSITIONS, int)

    # DERIVED, not typed twice: recomputed from the primitives here, so a
    # hardcoded 0.06 or 6 in the module would still have to agree with them.
    assert budget.BUDGET_FRACTION_OF_CAPITAL == (
        budget.MAX_AGGREGATE_OPEN_RISK_USD / budget.ACCOUNT_CAPITAL_USD)
    assert budget.FULL_SIZE_POSITIONS == (
        budget.MAX_AGGREGATE_OPEN_RISK_USD / budget.RISK_PER_TRADE_USD)


def test_the_derived_values_are_assigned_from_expressions_not_literals():
    """A literal 0.06 or 6 would satisfy the equalities above and still be a
    second copy of a number that must only exist once."""
    assigned = {}
    for node in ast.walk(_module_ast()):
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            target = node.targets[0]
            if isinstance(target, ast.Name):
                assigned[target.id] = node.value
    for name in ("BUDGET_FRACTION_OF_CAPITAL", "FULL_SIZE_POSITIONS"):
        assert name in assigned, name
        assert not isinstance(assigned[name], ast.Constant), (
            "%s must be computed from the primitives, not typed" % name)


def test_the_budget_is_an_exact_multiple_of_the_risk_unit():
    """SECTION 4 DEPENDS ON THIS. If the ratio is not integral, the partial
    allocation branch becomes reachable and "a hard cap of six concurrent
    full-size positions" stops describing the rule."""
    ratio = budget.MAX_AGGREGATE_OPEN_RISK_USD / budget.RISK_PER_TRADE_USD
    assert ratio == float(budget.FULL_SIZE_POSITIONS)
    assert budget.MAX_AGGREGATE_OPEN_RISK_USD == (
        budget.FULL_SIZE_POSITIONS * budget.RISK_PER_TRADE_USD)


def test_the_risk_unit_matches_the_engines_standing_value():
    """$20 is the project's risk unit, not a second one invented here.

    Imported inside the test rather than by the module, which imports nothing:
    the module must not depend on the engine, but the two values must agree.
    """
    import sys
    sys.path.insert(0, os.path.join(ROOT, "src", "engine"))
    import costs
    cfg = costs.CostConfig(stop_atr_mult=2.25, stop_max_pct=0.035,
                           rvol_threshold=1.5, baseline_days=20)
    assert budget.RISK_PER_TRADE_USD == cfg.risk_usd
    assert budget.ACCOUNT_CAPITAL_USD == getattr(cfg, "equity" + "_usd")


def test_the_module_refuses_an_inexact_transcription():
    """The import-time guard must have teeth, or it proves nothing.

    Exercised by calling it against mutated module state and restoring, because
    the guard's whole purpose is to fire on an edit that leaves the module
    otherwise importable.
    """
    original = (budget.MAX_AGGREGATE_OPEN_RISK_USD,
                budget.RISK_PER_TRADE_USD,
                budget.BUDGET_FRACTION_OF_CAPITAL,
                budget.FULL_SIZE_POSITIONS)
    try:
        # (a) the budget moved off 6% of capital
        budget.MAX_AGGREGATE_OPEN_RISK_USD = 130.00
        with pytest.raises(ValueError, match="not the frozen 0.06"):
            budget._refuse_inexact_transcription()

        # (b) the ratio stopped being integral -- section 4's dead branch wakes
        budget.MAX_AGGREGATE_OPEN_RISK_USD = 120.00
        budget.RISK_PER_TRADE_USD = 16.00
        with pytest.raises(ValueError, match="not an integer"):
            budget._refuse_inexact_transcription()

        # (c) a DERIVED constant hand-edited away from its primitives
        budget.RISK_PER_TRADE_USD = 20.00
        budget.FULL_SIZE_POSITIONS = 7
        with pytest.raises(ValueError, match="derived constant disagrees"):
            budget._refuse_inexact_transcription()
        budget.FULL_SIZE_POSITIONS = 6
        budget.BUDGET_FRACTION_OF_CAPITAL = 0.05
        with pytest.raises(ValueError, match="derived constant disagrees"):
            budget._refuse_inexact_transcription()
    finally:
        (budget.MAX_AGGREGATE_OPEN_RISK_USD, budget.RISK_PER_TRADE_USD,
         budget.BUDGET_FRACTION_OF_CAPITAL,
         budget.FULL_SIZE_POSITIONS) = original
    budget._refuse_inexact_transcription()


# ---------------------------------------------------------------------------
# 2. THE DOCUMENT AND THE MODULE MUST AGREE. Parsed, not eyeballed.
# ---------------------------------------------------------------------------

CANONICAL_RE = re.compile(r"^([A-Z][A-Z_]+)\s*=\s*(.+?)\s*$", re.MULTILINE)


def _canonical_block(text):
    """The fenced block in section 1 that states the values verbatim."""
    blocks = re.findall(r"```\n(.*?)```", text, re.DOTALL)
    hits = [b for b in blocks if "MAX_AGGREGATE_OPEN_RISK_USD" in b]
    assert len(hits) == 1, (
        "the document must carry exactly ONE canonical value block; found %d"
        % len(hits))
    return dict(CANONICAL_RE.findall(hits[0]))


def test_the_document_canonical_block_matches_the_module(doc):
    """EVERY constant, parsed out of the markdown and required equal."""
    stated = _canonical_block(doc)
    assert set(stated) == {
        "MAX_AGGREGATE_OPEN_RISK_USD", "RISK_PER_TRADE_USD",
        "ACCOUNT_CAPITAL_USD", "BUDGET_FRACTION_OF_CAPITAL",
        "FULL_SIZE_POSITIONS", "MARGIN_MODE", "POSITION_MODE"}

    assert float(stated["MAX_AGGREGATE_OPEN_RISK_USD"]) == \
        budget.MAX_AGGREGATE_OPEN_RISK_USD
    assert float(stated["RISK_PER_TRADE_USD"]) == budget.RISK_PER_TRADE_USD
    assert float(stated["ACCOUNT_CAPITAL_USD"]) == budget.ACCOUNT_CAPITAL_USD
    assert float(stated["BUDGET_FRACTION_OF_CAPITAL"]) == \
        budget.BUDGET_FRACTION_OF_CAPITAL
    assert int(stated["FULL_SIZE_POSITIONS"]) == budget.FULL_SIZE_POSITIONS
    assert stated["MARGIN_MODE"].strip('"') == budget.MARGIN_MODE
    assert stated["POSITION_MODE"].strip('"') == budget.POSITION_MODE


def test_a_planted_drift_between_document_and_module_is_detected(doc):
    """The comparison must have teeth. Mutate the parsed document and require
    the same equality check to fail."""
    stated = _canonical_block(doc)
    stated["MAX_AGGREGATE_OPEN_RISK_USD"] = "100.00"
    assert float(stated["MAX_AGGREGATE_OPEN_RISK_USD"]) != \
        budget.MAX_AGGREGATE_OPEN_RISK_USD


def test_the_document_states_the_same_numbers_in_prose(doc):
    """Twice in the document, so they must agree twice.

    A canonical block a reader skips and prose a reader believes is exactly how
    two copies of one number drift apart.
    """
    assert "$120.00" in doc
    assert "$20.00" in doc
    assert "$2,000.00" in doc
    assert "6.0%" in doc
    assert re.search(r"\*\*6\*\* concurrent full-size positions", doc), (
        "the position count must appear in prose as well as in the block")
    for phrase in ('`MARGIN_MODE = "cross"`', '`POSITION_MODE = "hedge"`'):
        assert phrase in doc, phrase


def test_the_prose_dollar_figures_parse_to_the_constants(doc):
    """Parsed rather than merely present, so $120.00 cannot mean anything else."""
    def money(pattern):
        m = re.search(pattern, doc, re.IGNORECASE)
        assert m, pattern
        return float(m.group(1).replace(",", ""))

    # The statement of the rule itself, in section 1's blockquote.
    assert money(r"may not exceed \$([\d,]+\.\d\d), being ([\d.]+)% of") == \
        budget.MAX_AGGREGATE_OPEN_RISK_USD
    stated = re.search(r"may not exceed \$[\d,]+\.\d\d, being ([\d.]+)% of "
                       r"\$([\d,]+\.\d\d)", doc, re.IGNORECASE)
    assert stated, "the rule's own sentence must carry all three figures"
    assert float(stated.group(1)) / 100.0 == budget.BUDGET_FRACTION_OF_CAPITAL
    assert float(stated.group(2).replace(",", "")) == budget.ACCOUNT_CAPITAL_USD
    assert money(r"the budget is\s+\*\*\$([\d,]+\.\d\d)\*\*") == \
        budget.MAX_AGGREGATE_OPEN_RISK_USD
    assert money(r"risk per trade is \*\*\$([\d,]+\.\d\d)\*\*") == \
        budget.RISK_PER_TRADE_USD
    assert money(r"capital is \*\*\$([\d,]+\.\d\d)\*\*") == \
        budget.ACCOUNT_CAPITAL_USD

    pct = re.search(r"the budget\s+is\s+\*\*([\d.]+)%\*\* of capital", doc)
    assert pct, "the percentage must be stated in prose"
    assert float(pct.group(1)) / 100.0 == budget.BUDGET_FRACTION_OF_CAPITAL


# ---------------------------------------------------------------------------
# 3. The document states all eleven items.
# ---------------------------------------------------------------------------

REQUIRED_SECTIONS = {
    1: ("THE RULE", ("all three symbols", "not per symbol")),
    2: ("DERIVATION", ("30", "one fifth", "20.51%", "JUDGEMENT")),
    3: ("ALLOCATION", ("arrival order", "qty_step", "$5")),
    4: ("PARTIAL", ("HARD CAP OF SIX", "unreachable")),
    5: ("ARRIVAL ORDER", ("floor", "not correctable", "step 3")),
    6: ("PATH DEPENDENCE", ("realised outcomes", "570", "281")),
    7: ("ONE-BUDGET", ("REJECTED", "skip tail")),
    8: ("MARGIN MODE AND POSITION MODE", ("cross", "hedge", "one-way")),
    9: ("GUARD-RAIL", ("borderline", "proportional")),
    10: ("NOT DECIDED", ("max_leverage", "maxSymbolOrderNum", "R-multiple")),
    11: ("PRE-REGISTRATION STATEMENT", ("e735295", "without reference")),
}


def test_the_document_carries_a_heading_for_every_one_of_the_eleven_items(doc):
    headings = re.findall(r"^## (\d+)\.\s+(.+)$", doc, re.MULTILINE)
    numbers = [int(n) for n, _ in headings]
    assert numbers == list(range(1, 12)), (
        "sections must be 1..11, consecutive and in order; got %s" % numbers)
    titles = {int(n): t for n, t in headings}
    for number, (fragment, _) in REQUIRED_SECTIONS.items():
        assert fragment.upper() in titles[number].upper(), (
            "section %d is titled %r and does not name %r"
            % (number, titles[number], fragment))


def test_each_section_states_what_it_was_required_to_state(doc):
    """Headings alone would let an empty section pass. Each is checked for the
    substance the pre-registration is required to carry."""
    parts = re.split(r"^## \d+\.\s+", doc, flags=re.MULTILINE)[1:]
    assert len(parts) == 11
    for number, (_, required) in REQUIRED_SECTIONS.items():
        body = parts[number - 1]
        for token in required:
            assert token.lower() in body.lower(), (number, token)


def test_the_document_is_a_pre_registration_not_a_measurement(doc):
    """It must state what it is, and must not contain what it forbids."""
    assert "FROZEN at this commit" in doc
    assert "committed ALONE" in doc
    assert "e735295" in doc, "the state of the repository must be named"
    assert "4e08e1b" in doc
    # The cost of the rule is the NEXT step's measurement.
    assert "step 3" in doc.lower()
    for forbidden in ("skip rate of", "skip rate is %", "surviving signals:"):
        assert forbidden not in doc.lower(), forbidden


def test_the_document_records_the_unsourced_input_as_unsourced(doc):
    """THE 30-50% TOLERANCE IS NOT IN ANY COMMITTED ARTIFACT.

    A search of `docs/` and `reports/` at this commit finds no prior statement
    of it, so the document must say so rather than presenting it as sourced.
    This is the check that the disclosure survives an edit.
    """
    assert "NOT RECORDED IN ANY COMMITTED ARTIFACT" in doc
    assert "preference" in doc.lower()
    assert "is not derived" in doc.lower() or "NOT DERIVED" in doc


# ---------------------------------------------------------------------------
# 4. NO MEASUREMENT -- the import graph.
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


def test_the_module_cannot_reach_the_data_layer_or_the_engine():
    banned = ("src.timeframe", "src.folds", "src.analysis", "src.engine",
              "src.sweep", "src.regime", "src.venue", "src.data", "src.costs",
              "pandas", "numpy", "pyarrow", "requests", "simulate", "costs")
    for mod in _imports():
        for bad in banned:
            assert not (mod == bad or mod.startswith(bad + ".")), mod


def test_the_module_imports_nothing_at_all():
    """The strongest available form of "this is constants only".

    A constants module with no imports cannot acquire a dependency without
    someone editing this assertion, which is the point.
    """
    assert _imports() == set(), _imports()


def test_the_module_carries_constants_and_one_integrity_check_only():
    """No allocation function, no viability check, no simulation.

    The specification describes an allocation rule; implementing it is 5.3's
    work and a half-implementation committed here would be the thing the next
    step silently builds around.
    """
    tree = _module_ast()
    functions = [n.name for n in ast.walk(tree)
                 if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
    assert functions == ["_refuse_inexact_transcription"], functions
    assert not [n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]
    for word in ("allocate", "def allocation", "viable", "check_min_qty",
                 "simulate", "open_position", "skip"):
        assert word not in _name_blob(), word


def test_nothing_is_wired_in_yet():
    """NO ENGINE FILE IMPORTS src/risk AT THIS COMMIT. That wiring is 5.3's.

    Walked over the source of every module in the repository, so a new importer
    added anywhere fails here rather than being noticed at review.
    """
    importers = []
    for base, _, files in os.walk(os.path.join(ROOT, "src")):
        if "__pycache__" in base:
            continue
        for name in files:
            if not name.endswith(".py"):
                continue
            path = os.path.join(base, name)
            if os.path.abspath(path).startswith(
                    os.path.dirname(os.path.abspath(budget.__file__))):
                continue
            src = open(path).read()
            if "src.risk" in src or "from src import risk" in src:
                importers.append(path)
    assert importers == [], importers


# ---------------------------------------------------------------------------
# 5. THE FIREWALL -- the twelve-name guard from report 25.
# ---------------------------------------------------------------------------

PERFORMANCE_NAMES = ("expectancy", "win_rate", "winrate", "profit_factor",
                     "sharpe", "sortino", "net_pnl", "gross_pnl", "drawdown",
                     "r_multiple", "equity", "pnl")
"""The nine from reports 19-21 plus the three report 24 §9.5 flagged as missing
and report 25 added. The list only ever grows; a test pins that."""


def test_the_banned_list_is_the_twelve_name_one_from_report_25():
    inherited = ("expectancy", "win_rate", "winrate", "profit_factor",
                 "sharpe", "net_pnl", "r_multiple", "equity", "pnl")
    assert set(inherited) <= set(PERFORMANCE_NAMES)
    assert {"drawdown", "sortino", "gross_pnl"} <= set(PERFORMANCE_NAMES)
    assert len(PERFORMANCE_NAMES) == 12


def _name_blob():
    """Identifiers and non-docstring string literals, lowercased.

    Docstrings are excluded because they STATE the prohibition; a raw text
    search would fire on the statement of the rule rather than a violation.
    """
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
    return " ".join(names).lower()


def test_no_performance_quantity_appears_in_the_module():
    blob = _name_blob()
    for banned in PERFORMANCE_NAMES:
        assert banned not in blob, "%r used as a name in %s" % (
            banned, budget.__file__)


def test_the_package_docstring_states_that_nothing_is_wired_in():
    from src import risk
    assert risk.__doc__ is not None
    assert "5.3" in risk.__doc__
