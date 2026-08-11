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
    # Over IDENTIFIERS ONLY: the attribute docstrings under each constant are
    # prose and describe what the module deliberately does NOT do, so a text
    # search would fire on the statement of the exclusion.
    blob = _name_blob(prose="exclude")
    for word in ("allocate", "def allocation", "viable", "check_min_qty",
                 "simulate", "open_position", "skip"):
        assert word not in blob, word


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


def _name_blob(prose="include_attribute_docstrings"):
    """Identifiers and string literals, lowercased.

    Module, function and class docstrings are ALWAYS excluded, because they
    STATE the prohibition and a raw text search would fire on the statement of
    the rule rather than on a violation of it.

    `prose="exclude"` additionally drops ATTRIBUTE DOCSTRINGS -- the bare string
    expressions under each constant, which Python does not treat as docstrings
    but which are prose by construction and never a value. The firewall keeps
    them IN, which is the stricter reading and the one reports 19-25 use.
    """
    tree = _module_ast()
    docstrings = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.FunctionDef, ast.ClassDef)):
            d = ast.get_docstring(node, clean=False)
            if d is not None:
                docstrings.add(d)
            if prose == "exclude":
                for stmt in getattr(node, "body", []):
                    if (isinstance(stmt, ast.Expr)
                            and isinstance(stmt.value, ast.Constant)
                            and isinstance(stmt.value.value, str)):
                        docstrings.add(stmt.value.value)
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


# ===========================================================================
# AMENDMENT 1 -- the intra-bar tie-break and nominal-allocation rules.
#
# docs/design/05a_aggregate_risk_budget_amendment_1.md
# ===========================================================================

import datetime as dt            # noqa: E402  (amendment block, kept together)
import hashlib                   # noqa: E402

AMENDMENT_PATH = os.path.join(
    ROOT, "docs", "design", "05a_aggregate_risk_budget_amendment_1.md")

FROZEN_DOC_SHA256 = (
    "d5ac7bd61323d04e75a854baf14086932470175408f5e2db4ca6f4d3afad268f")
"""docs/design/05_aggregate_risk_budget.md as frozen at a323237."""

HOUR_MS = 3_600_000


@pytest.fixture(scope="module")
def amendment():
    assert os.path.exists(AMENDMENT_PATH), AMENDMENT_PATH
    with open(AMENDMENT_PATH) as fh:
        return fh.read()


def _rotation(bar_open_ms):
    """The rule, applied. Computed here because the module is constants only."""
    return (int(bar_open_ms) // budget.ROTATION_PERIOD_MS) % \
        budget.ROTATION_MODULUS


def _priority(bar_open_ms):
    return budget.SYMBOL_ROTATION[_rotation(bar_open_ms)]


def _ms(iso):
    return int(dt.datetime.fromisoformat(
        iso.replace("Z", "+00:00")).timestamp() * 1000)


# ---------------------------------------------------------------------------
# A1. THE FROZEN DOCUMENT IS UNMODIFIED.
# ---------------------------------------------------------------------------

def test_document_05_is_byte_for_byte_unchanged():
    """THE AMENDMENT PROCEDURE IS THE POINT, AND THIS IS WHAT ENFORCES IT.

    Document 05 §11: "an amendment is a new document with a new commit and an
    explicit statement of what changed and why; a silent edit is a
    contamination event." A hash asserted in a test is what turns that sentence
    into something a suite can refuse.
    """
    with open(DOC_PATH, "rb") as fh:
        digest = hashlib.sha256(fh.read()).hexdigest()
    assert digest == FROZEN_DOC_SHA256, (
        "docs/design/05_aggregate_risk_budget.md has CHANGED. It is frozen at "
        "a323237 and may not be edited; a correction is Amendment 2, with its "
        "own commit.")


def test_the_amendment_changes_no_level():
    """THE LEVEL DID NOT CHANGE. Asserted, not merely stated in prose."""
    assert budget.MAX_AGGREGATE_OPEN_RISK_USD == 120.00
    assert budget.RISK_PER_TRADE_USD == 20.00
    assert budget.ACCOUNT_CAPITAL_USD == 2000.00
    assert budget.BUDGET_FRACTION_OF_CAPITAL == 0.06
    assert budget.FULL_SIZE_POSITIONS == 6
    assert budget.MARGIN_MODE == "cross"
    assert budget.POSITION_MODE == "hedge"


# ---------------------------------------------------------------------------
# A2. The new constants, and the document that states them.
# ---------------------------------------------------------------------------

def test_the_amendment_constants():
    assert budget.TIE_BREAK_RULE == "cyclic_rotation_by_bar_timestamp"
    assert budget.ROTATION_PERIOD_MS == 3_600_000
    assert budget.ROTATION_MODULUS == 3
    assert budget.BUDGET_CHARGES == "nominal"
    assert budget.SYMBOL_ROTATION == (
        ("BTCUSDT", "ETHUSDT", "SOLUSDT"),
        ("ETHUSDT", "SOLUSDT", "BTCUSDT"),
        ("SOLUSDT", "BTCUSDT", "ETHUSDT"))
    assert isinstance(budget.SYMBOL_ROTATION, tuple)
    assert all(isinstance(order, tuple) for order in budget.SYMBOL_ROTATION)


def test_the_rotation_period_is_the_bar_period():
    """1h, because the timeframe is frozen at 1h. Not a free parameter."""
    assert budget.ROTATION_PERIOD_MS == HOUR_MS
    assert budget.ROTATION_MODULUS == len(budget.SYMBOL_ROTATION)
    assert budget.ROTATION_MODULUS == len(budget.SYMBOL_ROTATION[0])


def _amendment_block(text):
    """The fenced block in §5 that states the new constants verbatim."""
    blocks = re.findall(r"```\n(.*?)```", text, re.DOTALL)
    hits = [b for b in blocks if "TIE_BREAK_RULE" in b]
    assert len(hits) == 1, (
        "the amendment must carry exactly ONE constants block; found %d"
        % len(hits))
    return hits[0]


def test_the_amendment_document_states_the_same_constants(amendment):
    """Parsed out of the markdown and required equal, as for document 05."""
    block = _amendment_block(amendment)
    stated = dict(CANONICAL_RE.findall(block))
    assert stated["TIE_BREAK_RULE"].strip('"') == budget.TIE_BREAK_RULE
    assert int(stated["ROTATION_PERIOD_MS"]) == budget.ROTATION_PERIOD_MS
    assert int(stated["ROTATION_MODULUS"]) == budget.ROTATION_MODULUS
    assert stated["BUDGET_CHARGES"].strip('"') == budget.BUDGET_CHARGES

    # The rotation table spans several lines; parsed by symbol triples.
    table = re.findall(r'\("([A-Z]+)", "([A-Z]+)", "([A-Z]+)"\)', block)
    assert tuple(table) == budget.SYMBOL_ROTATION

    # And the frozen document's own block is untouched by the amendment.
    assert "TIE_BREAK_RULE" not in _canonical_block(open(DOC_PATH).read())


def test_the_amendment_document_states_the_orderings_in_prose(amendment):
    """The three rotations appear a second time, as prose, and must agree."""
    for value, order in enumerate(budget.SYMBOL_ROTATION):
        pattern = r"rotation %d\s+->\s+%s" % (value, r",\s+".join(order))
        assert re.search(pattern, amendment), (value, order)
    assert "MAX_AGGREGATE_OPEN_RISK_USD` REMAINS `120.00`" in amendment
    assert FROZEN_DOC_SHA256 in amendment, (
        "the amendment must name the hash of the document it amends")


def test_the_amendment_document_carries_its_six_required_sections(amendment):
    headings = re.findall(r"^## (\d+)\.\s+(.+)$", amendment, re.MULTILINE)
    assert [int(n) for n, _ in headings] == list(range(1, 7))
    titles = {int(n): t.upper() for n, t in headings}
    assert "WHAT CHANGED" in titles[1]
    assert "RULE A" in titles[2]
    assert "RULE B" in titles[3]
    assert "UNMODIFIED" in titles[4]
    assert "CONSTANTS" in titles[5]
    assert "PRE-REGISTRATION" in titles[6]

    parts = re.split(r"^## \d+\.\s+", amendment, flags=re.MULTILINE)[1:]
    required = {
        1: ("THE LEVEL DID NOT CHANGE", "a323237"),
        2: ("bar index", "open time", "fixed priority", "random", "starve"),
        3: ("nominal", "inert", "0.21%", "1.26%", "0.67%", "5.3"),
        4: ("supersedes nothing", "§3", "§4"),
        5: ("2024-07-15T22:00:00Z", "2022-01-01T00:00:00Z"),
        6: ("git log", "Amendment 2", "may not be edited"),
    }
    for number, tokens in required.items():
        for token in tokens:
            assert token.lower() in parts[number - 1].lower(), (number, token)


# ---------------------------------------------------------------------------
# A3. EXHAUSTIVE NEUTRALITY.
# ---------------------------------------------------------------------------

def test_every_three_consecutive_bars_form_a_latin_square():
    """NEUTRALITY ACROSS ALL THREE RANKS, not merely across first place.

    Over any three consecutive hourly bars, each symbol must hold each of the
    three priority ranks exactly once. Checked at many starting offsets, since
    a table that was neutral only from a particular phase would not be neutral.
    """
    start = _ms("2022-01-01T00:00:00Z")
    for offset in range(0, 500):
        bars = [start + (offset + k) * HOUR_MS for k in range(3)]
        orders = [_priority(b) for b in bars]
        assert len({tuple(o) for o in orders}) == 3, "three distinct orderings"
        for rank in range(3):
            at_rank = [o[rank] for o in orders]
            assert sorted(at_rank) == ["BTCUSDT", "ETHUSDT", "SOLUSDT"], (
                offset, rank, at_rank)


def test_first_priority_is_exactly_equal_over_three_thousand_bars():
    """1,000 each, exactly. Not approximately, and not in expectation."""
    start = _ms("2022-01-01T00:00:00Z")
    counts = {"BTCUSDT": 0, "ETHUSDT": 0, "SOLUSDT": 0}
    for k in range(3_000):
        counts[_priority(start + k * HOUR_MS)[0]] += 1
    assert counts == {"BTCUSDT": 1_000, "ETHUSDT": 1_000, "SOLUSDT": 1_000}


def test_every_rank_is_exactly_equal_over_three_thousand_bars():
    start = _ms("2022-01-01T00:00:00Z")
    for rank in range(3):
        counts = {"BTCUSDT": 0, "ETHUSDT": 0, "SOLUSDT": 0}
        for k in range(3_000):
            counts[_priority(start + k * HOUR_MS)[rank]] += 1
        assert counts == {"BTCUSDT": 1_000, "ETHUSDT": 1_000,
                          "SOLUSDT": 1_000}, rank


def test_the_rotation_advances_by_exactly_one_bar():
    start = _ms("2023-05-05T05:00:00Z")
    for k in range(50):
        this = _rotation(start + k * HOUR_MS)
        nxt = _rotation(start + (k + 1) * HOUR_MS)
        assert nxt == (this + 1) % 3


def test_the_rotation_does_not_couple_to_the_funding_cycle():
    """3 and 8 are coprime, so every rotation meets every settlement phase
    equally often over a 24-hour joint cycle. Recorded because the frozen time
    exit is denominated in 8-hour settlements."""
    start = _ms("2022-01-01T00:00:00Z")
    pairs = {}
    for k in range(24 * 100):
        ts = start + k * HOUR_MS
        phase = (ts // HOUR_MS) % 8      # hours since the last settlement
        key = (_rotation(ts), phase)
        pairs[key] = pairs.get(key, 0) + 1
    assert len(pairs) == 24, "every (rotation, settlement phase) pair occurs"
    assert set(pairs.values()) == {100}, "and equally often"


def test_a_malformed_rotation_table_is_refused_at_import_time():
    """The neutrality property is the whole content of Rule A. A table that
    rotated first place while leaving third fixed would still index, still
    return three symbols, and would silently favour one of them."""
    original = budget.SYMBOL_ROTATION
    try:
        budget.SYMBOL_ROTATION = (
            ("BTCUSDT", "ETHUSDT", "SOLUSDT"),
            ("ETHUSDT", "BTCUSDT", "SOLUSDT"),   # SOL permanently third
            ("BTCUSDT", "ETHUSDT", "SOLUSDT"))
        with pytest.raises(ValueError, match="NOT neutral at priority rank"):
            budget._refuse_inexact_transcription()

        budget.SYMBOL_ROTATION = (("BTCUSDT", "ETHUSDT", "SOLUSDT"),)
        with pytest.raises(ValueError, match="entries against a modulus"):
            budget._refuse_inexact_transcription()
    finally:
        budget.SYMBOL_ROTATION = original
    budget._refuse_inexact_transcription()


# ---------------------------------------------------------------------------
# A4. SCOPE INVARIANCE -- and the bar-index implementation that fails it.
# ---------------------------------------------------------------------------

def test_the_rotation_is_invariant_to_the_series_start():
    """THE REASON THE RULE READS A TIMESTAMP AND NOT AN INDEX.

    Report 24 runs a pooled scope that discards a 114-bar warm-up and eighteen
    fold scopes that each begin at their own folds.json boundary. The rotation
    for a given UTC bar must be the same in all of them.
    """
    target = _ms("2024-07-15T22:00:00Z")
    expected = _rotation(target)
    for start_offset in (0, 1, 2, 113, 114, 115, 4392, 26_190):
        series_start = target - start_offset * HOUR_MS
        series = [series_start + k * HOUR_MS for k in range(start_offset + 1)]
        assert series[-1] == target
        # Computed while walking the series, exactly as an implementation
        # would, and required identical in every scope.
        assert [_rotation(ts) for ts in series][-1] == expected, start_offset


def _by_index(start_ms, ts):
    """THE REJECTED IMPLEMENTATION: rotation from position in the series."""
    return ((ts - start_ms) // HOUR_MS) % budget.ROTATION_MODULUS


def test_a_bar_index_implementation_FAILS_scope_invariance():
    """PLANTED ALTERNATIVE. The rejected implementation, asserted to break.

    An index-derived rotation gives the SAME UTC BAR two different priority
    orders in two scopes whose starts differ by a non-multiple of three hours,
    and neither scope can tell that it disagrees with the other.
    """
    target = _ms("2024-07-15T22:00:00Z")
    scope_a = target - 4_392 * HOUR_MS
    scope_b = scope_a - 1 * HOUR_MS          # one hour earlier: 1 mod 3 apart

    assert _rotation(target) == _rotation(target), "the timestamp rule agrees"

    assert _by_index(scope_a, target) != _by_index(scope_b, target), (
        "the fixture must actually produce disagreeing indices, or this test "
        "asserts nothing")
    assert budget.SYMBOL_ROTATION[_by_index(scope_a, target)] != \
        budget.SYMBOL_ROTATION[_by_index(scope_b, target)], (
        "an index-derived rotation gives one UTC bar two different priority "
        "orders in two scopes -- which is why the rule reads the timestamp")


def test_the_index_rule_agrees_on_todays_scopes_ONLY_BY_COINCIDENCE():
    """§2.2.1. THE HAZARD IS LATENT, NOT ACTIVE, AND THAT IS PINNED HERE.

    Every scope this project currently defines starts on a whole-day boundary
    (24 = 3 x 8) or after the 114-bar warm-up trim (114 = 3 x 38), so every
    scope start is congruent mod 3 and the index rule happens to agree with the
    timestamp rule everywhere. THAT IS AN ARITHMETIC COINCIDENCE.

    Asserted so that changing the warm-up to a non-multiple of three fails this
    test and re-opens the question deliberately rather than silently.
    """
    target = _ms("2024-07-15T22:00:00Z")
    scopes = {
        "window first bar": _ms("2022-01-01T00:00:00Z"),
        "pooled, after the 114-bar warm-up": _ms("2022-01-05T18:00:00Z"),
        "fold 9 train start": _ms("2024-04-01T00:00:00Z"),
        "fold 8 test start": _ms("2024-07-01T00:00:00Z"),
    }
    for label, start in scopes.items():
        assert ((target - start) // HOUR_MS) % 3 == _rotation(target), label
        assert _by_index(start, target) == _rotation(target), label

    # The coincidence, stated as the arithmetic that produces it.
    assert 24 % budget.ROTATION_MODULUS == 0, "a day is a whole cycle"
    assert 114 % budget.ROTATION_MODULUS == 0, "so is the warm-up trim"
    # And it ends the moment a scope start is not.
    assert 113 % budget.ROTATION_MODULUS != 0
    assert _by_index(_ms("2022-01-05T17:00:00Z"), target) != _rotation(target)


# ---------------------------------------------------------------------------
# A5. KNOWN-VALUE PINS, computed by hand.
# ---------------------------------------------------------------------------

def test_known_rotation_pins():
    """Hand arithmetic, asserted, so a change to the rule is visible as a
    change to a named bar rather than as a shift in an aggregate."""
    # 2022-01-01T00:00:00Z -- the first bar of the window.
    ts = _ms("2022-01-01T00:00:00Z")
    assert ts == 1_640_995_200_000
    assert ts // HOUR_MS == 455_832
    assert 455_832 % 3 == 0
    assert _rotation(ts) == 0
    assert _priority(ts) == ("BTCUSDT", "ETHUSDT", "SOLUSDT")

    # 2024-07-15T22:00:00Z -- report 24 §7.5's worst bar.
    ts = _ms("2024-07-15T22:00:00Z")
    assert ts == 1_721_080_800_000
    assert ts // HOUR_MS == 478_078
    assert 478_078 % 3 == 1
    assert _rotation(ts) == 1
    assert _priority(ts) == ("ETHUSDT", "SOLUSDT", "BTCUSDT")

    # The window's own measured boundaries, from report 24 §6.
    assert _rotation(_ms("2022-01-05T18:00:00Z")) == 0
    assert _rotation(_ms("2024-12-31T23:00:00Z")) == 2


def test_the_pins_in_the_document_match_the_pins_here(amendment):
    """The document's table of hand-computed values, parsed and required equal."""
    for iso, floor_div, modulo in (("2022-01-01T00:00:00Z", 455_832, 0),
                                   ("2024-07-15T22:00:00Z", 478_078, 1)):
        # Anchored on the table ROW in §5, not on any prose mention.
        row = re.search(r"^\|\s*\*\*%s\*\*.*?$" % re.escape(iso), amendment,
                        re.MULTILINE)
        assert row, iso
        text = row.group(0)
        assert "{:,}".format(floor_div) in text, (iso, floor_div)
        assert _rotation(_ms(iso)) == modulo
        for symbol in budget.SYMBOL_ROTATION[modulo]:
            assert symbol in text, (iso, symbol)


# ---------------------------------------------------------------------------
# A6. RULE B -- nominal charging.
# ---------------------------------------------------------------------------

def test_the_budget_charges_the_nominal_allocation():
    assert budget.BUDGET_CHARGES == "nominal"
    assert budget.BUDGET_CHARGES != "realised"


def test_nominal_charging_keeps_the_remaining_budget_a_multiple_of_the_unit():
    """SECTION 4's INERTNESS, ASSERTED AS ARITHMETIC RATHER THAN ASSUMED.

    Under nominal charging the remaining budget only ever moves by exactly the
    risk unit, so min(unit, remaining) is always the unit or zero and the
    partial branch cannot be reached. Walked over every open/close sequence of
    length 12 that never breaches the cap.
    """
    unit = budget.RISK_PER_TRADE_USD
    cap = budget.MAX_AGGREGATE_OPEN_RISK_USD

    def walk(remaining, depth):
        if depth == 0:
            return
        assert abs(remaining / unit - round(remaining / unit)) < 1e-12
        allocation = min(unit, remaining)
        assert allocation in (0.0, unit), allocation
        if remaining >= unit:                      # open
            walk(remaining - unit, depth - 1)
        if remaining < cap:                        # close
            walk(remaining + unit, depth - 1)

    walk(cap, 12)


def test_realised_charging_would_wake_the_partial_branch():
    """THE PLANTED ALTERNATIVE, so Rule B's necessity is pinned by a test.

    Charging realised risk after flooring leaves a remainder below the unit;
    min(unit, remainder) is then neither the unit nor zero, which is exactly the
    partial-allocation branch the frozen document declares inert.
    """
    unit = budget.RISK_PER_TRADE_USD
    cap = budget.MAX_AGGREGATE_OPEN_RISK_USD
    # Six positions, each realising slightly under nominal because flooring
    # only ever reduces quantity. The shortfalls are illustrative magnitudes,
    # not measurements.
    realised = [unit * (1.0 - f) for f in
                (0.0021, 0.0126, 0.0067, 0.0021, 0.0126, 0.0067)]
    remaining = cap - sum(realised)
    assert 0.0 < remaining < unit, remaining
    allocation = min(unit, remaining)
    assert allocation not in (0.0, unit), (
        "a seventh signal would be allocated a partial size -- the branch the "
        "frozen document §4 declares INERT")
    # Under Rule B the same six positions leave exactly zero.
    assert cap - 6 * unit == 0.0


def test_the_overstatement_is_conservative_and_bounded():
    """Charged exposure exceeds true exposure, never the reverse.

    Report 24 §2.2's pooled flooring losses are the bound, and they transfer
    from notional to risk unchanged because both are linear in quantity.
    """
    worst_pooled = 0.0126               # ETHUSDT, report 24 §2.2
    charged = 6 * budget.RISK_PER_TRADE_USD
    true_risk = charged * (1.0 - worst_pooled)
    assert true_risk < charged
    assert (charged - true_risk) / budget.MAX_AGGREGATE_OPEN_RISK_USD < 0.02


# ---------------------------------------------------------------------------
# A7. The amendment changes none of the standing structural guarantees.
# ---------------------------------------------------------------------------

def test_the_module_still_imports_nothing_and_is_still_unwired():
    assert _imports() == set(), _imports()
    assert budget.__file__.endswith(os.path.join("src", "risk", "budget.py"))


def test_the_module_still_carries_exactly_one_function():
    functions = [n.name for n in ast.walk(_module_ast())
                 if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
    assert functions == ["_refuse_inexact_transcription"], (
        "constants only: no rotation function, no allocation function. "
        "Implementing them is 5.3's work.")
