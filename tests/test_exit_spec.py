"""Guards for the pre-registered exit resolution specification.

THE FUNDING SETTLEMENT COUNT IS THE ONE VALUE HERE THAT IS DERIVED RATHER THAN
CHOSEN, and it is the one most likely to be wrong in a way nothing notices:
thesis section 5.3 uses `n = 3` as both a settlement INDEX and a count of
settlements CROSSED, and those are different quantities. The count is therefore
re-derived here from the frozen time-exit definition over all 24 entry hours,
and the constant is asserted equal to the maximum that derivation produces --
never to a literal. A planted wrong value fails.

THE TWO FILL RULES MUST BE DISTINGUISHABLE. E2 fills the stop on a touch and E3
requires the target to be traded through by one tick. On a synthetic bar that
touches the target exactly, touch fills and trade-through does not; if the two
ever became the same predicate, every figure downstream would still look
reasonable and the winning leg would have quietly become more generous.

NO BAR IS READ AND NO EXIT IS EVALUATED. The module under test imports nothing
at all -- asserted -- so it could not reach a bar if it tried, and these tests
exercise the fill predicates on hand-written numbers, never on market data.
"""

import ast
import datetime as dt
import hashlib
import json
import os
import re

import pytest

from src.risk import exit_spec as es
from src.venue import trigger_basis as tb


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOC_PATH = os.path.join(ROOT, "docs", "design", "06_exit_resolution_spec.md")

HOUR_MS = 3_600_000
SETTLEMENT_MS = 8 * HOUR_MS

FROZEN_DESIGN_HASHES = {
    # THE AMENDED DOCUMENT ITSELF. Amendment 1 changes not one character of it,
    # and this is what makes that assertion rather than a claim.
    "06_exit_resolution_spec.md":
        "773bbafe94ba136c9bddbdc443284af96c021eb4e0894677438e0cb7622f71a0",
    "05_aggregate_risk_budget.md":
        "d5ac7bd61323d04e75a854baf14086932470175408f5e2db4ca6f4d3afad268f",
    "05a_aggregate_risk_budget_amendment_1.md":
        "50da5aed3fabb86c3c7b54b41642444e50c7a7790de8dc93ab401ab53071522c",
    "05b_aggregate_risk_budget_amendment_2.md":
        "1d115df2272a4e231da41afbbd0b7c82020d0092ec2b3b483062d57c0e95f7bd",
}


@pytest.fixture(scope="module")
def doc():
    assert os.path.exists(DOC_PATH), DOC_PATH
    with open(DOC_PATH) as fh:
        return fh.read()


def _module_ast():
    return ast.parse(open(es.__file__).read())


# ---------------------------------------------------------------------------
# 1. THE CONSTANTS, AND THE DOCUMENT THAT STATES THEM.
# ---------------------------------------------------------------------------

def test_the_frozen_values():
    assert es.EXIT_RESOLUTION == "1m"
    assert es.STOP_FILL_RULE == "touch_inclusive"
    assert es.TARGET_FILL_RULE == "trade_through_one_tick"
    assert es.INTRABAR_PRECEDENCE == "stop_first"
    assert es.TIME_EXIT_VS_STOP == "stop_first"
    assert es.FUNDING_CHARGED == "in_sizing_denominator_at_entry"
    assert es.FUNDING_SETTLEMENTS_CHARGED == 3
    assert es.FUNDING_RATE_PER_SETTLEMENT == 0.0001
    assert es.MISSING_BAR_RULE == "flag_and_count"
    assert es.TRIGGER_PRICE_BASIS == "fill_price"
    assert es.TRIGGER_PRICE_PARAMETER == "triggerType"


CANONICAL_RE = re.compile(r"^([A-Z][A-Z_]+)\s*=\s*(.+?)\s*$", re.MULTILINE)


def _canonical_block(text):
    blocks = re.findall(r"```\n(.*?)```", text, re.DOTALL)
    hits = [b for b in blocks if "EXIT_RESOLUTION" in b]
    assert len(hits) == 1, (
        "the document must carry exactly ONE canonical block; found %d"
        % len(hits))
    return dict(CANONICAL_RE.findall(hits[0]))


def test_the_document_and_the_module_agree_on_every_constant(doc):
    stated = _canonical_block(doc)
    assert set(stated) == {
        "EXIT_RESOLUTION", "STOP_FILL_RULE", "TARGET_FILL_RULE",
        "INTRABAR_PRECEDENCE", "TIME_EXIT_VS_STOP", "FUNDING_CHARGED",
        "FUNDING_SETTLEMENTS_CHARGED", "FUNDING_RATE_PER_SETTLEMENT",
        "MISSING_BAR_RULE", "TRIGGER_PRICE_BASIS", "TRIGGER_PRICE_PARAMETER"}

    for name in ("EXIT_RESOLUTION", "STOP_FILL_RULE", "TARGET_FILL_RULE",
                 "INTRABAR_PRECEDENCE", "TIME_EXIT_VS_STOP", "FUNDING_CHARGED",
                 "MISSING_BAR_RULE", "TRIGGER_PRICE_BASIS",
                 "TRIGGER_PRICE_PARAMETER"):
        assert stated[name].strip('"') == getattr(es, name), name
    assert int(stated["FUNDING_SETTLEMENTS_CHARGED"]) == \
        es.FUNDING_SETTLEMENTS_CHARGED
    assert float(stated["FUNDING_RATE_PER_SETTLEMENT"]) == \
        es.FUNDING_RATE_PER_SETTLEMENT


def test_a_planted_drift_between_document_and_module_is_detected(doc):
    stated = _canonical_block(doc)
    stated["INTRABAR_PRECEDENCE"] = '"target_first"'
    assert stated["INTRABAR_PRECEDENCE"].strip('"') != es.INTRABAR_PRECEDENCE


def test_the_document_carries_its_required_sections(doc):
    headings = re.findall(r"^## (\d+)\.\s+(.+)$", doc, re.MULTILINE)
    assert [int(n) for n, _ in headings] == list(range(1, 13))
    titles = {int(n): t.upper() for n, t in headings}
    assert "BLINDER COMMITMENT" in titles[1]
    assert "RESOLUTION" in titles[2]
    assert "STOP FILL" in titles[3]
    assert "TARGET FILL" in titles[4]
    assert "FUNDING" in titles[6]
    assert "TRIGGER PRICE BASIS" in titles[7]
    assert "MISSING 1M BARS" in titles[8]
    assert "CONVENTION" in titles[9]
    assert "CONSTANTS" in titles[10]
    assert "PRE-REGISTRATION" in titles[11]
    assert "MAY NOT BE EDITED" in titles[12]

    parts = re.split(r"^## \d+\.\s+", doc, flags=re.MULTILINE)[1:]
    required = {
        1: ("counting", "win rate", "not on equal footing"),
        2: ("10.21%", "2.0%", "upper bound"),
        3: ("unmeasured placeholder", "5 bps", "10 bps"),
        4: ("one tick", "more conservative", "MAKER_NONFILL"),
        5: ("stop first", "rejected", "overcharge", "counted"),
        6: ("21 of the 24", "0.022R", "not repaired"),
        7: ("triggerType", "fill_price", "shell"),
        8: ("1,578,240", "100.000%", "inert"),
        9: ("open_synth" if "open_synth" in doc else "synthesised", "queue"),
        11: ("git log", "df14a68", "a323237"),
        12: ("Amendment", "wrong granularity"),
    }
    for number, tokens in required.items():
        for token in tokens:
            assert token.lower() in parts[number - 1].lower(), (number, token)


def test_the_frozen_design_documents_are_unchanged():
    for name, expected in FROZEN_DESIGN_HASHES.items():
        path = os.path.join(ROOT, "docs", "design", name)
        with open(path, "rb") as fh:
            assert hashlib.sha256(fh.read()).hexdigest() == expected, name


# ---------------------------------------------------------------------------
# 2. THE FUNDING SETTLEMENT COUNT -- DERIVED, NOT ASSUMED.
# ---------------------------------------------------------------------------

def _settlements_crossed(bar_open_ms):
    """Re-derive the count from the FROZEN time-exit definition.

    Entry is the close of the 1h bar, i.e. `bar_open + 1h` (bar timestamps are
    OPEN times, report 24 §1.1). The exit is the close of the bar preceding the
    third settlement strictly after entry, which at 1h alignment is that
    settlement instant itself. The position is held across `[entry, exit)`.
    """
    entry = bar_open_ms + HOUR_MS
    third = (entry // SETTLEMENT_MS + 3) * SETTLEMENT_MS
    return sum(1 for k in range(-2, 6)
               if entry <= (entry // SETTLEMENT_MS + k) * SETTLEMENT_MS < third)


def test_the_settlement_count_is_derived_over_all_24_entry_hours():
    """THE ENUMERATION. 21 hours cross two settlements, 3 cross three.

    The three are exactly the hours whose ENTRY INSTANT coincides with a
    settlement -- 08:00, 16:00 and 00:00, from bar opens 07:00, 15:00 and 23:00
    -- and those are also exactly the 24-hour holds.
    """
    counts = {}
    three = []
    for hour in range(24):
        bar = int(dt.datetime(2023, 6, 1, hour,
                              tzinfo=dt.timezone.utc).timestamp() * 1000)
        n = _settlements_crossed(bar)
        counts[n] = counts.get(n, 0) + 1
        if n == 3:
            three.append(hour)
    assert counts == {2: 21, 3: 3}, counts
    assert three == [7, 15, 23]
    assert max(counts) == 3


def test_the_constant_equals_the_derived_maximum_not_a_literal():
    """A PLANTED WRONG VALUE MUST FAIL. The constant is the enumeration's
    maximum, re-derived here rather than copied from the module."""
    derived = max(
        _settlements_crossed(int(dt.datetime(2023, 6, 1, h,
                                             tzinfo=dt.timezone.utc)
                                 .timestamp() * 1000))
        for h in range(24))
    assert es.FUNDING_SETTLEMENTS_CHARGED == derived
    for wrong in (1, 2, 4, 5):
        assert es.FUNDING_SETTLEMENTS_CHARGED != wrong


def test_the_settlement_count_is_independent_of_the_day_chosen():
    """The funding grid is the multiples of 8h from the epoch, so the answer
    cannot depend on which date the enumeration is run over."""
    for day in (dt.date(2022, 1, 1), dt.date(2023, 6, 1), dt.date(2024, 12, 31)):
        counts = {}
        for hour in range(24):
            bar = int(dt.datetime(day.year, day.month, day.day, hour,
                                  tzinfo=dt.timezone.utc).timestamp() * 1000)
            n = _settlements_crossed(bar)
            counts[n] = counts.get(n, 0) + 1
        assert counts == {2: 21, 3: 3}, day


def test_the_funding_charge_stays_inside_the_frozen_budget():
    """Thesis §5.3's budget is 0.022R at the 1.50% floor stop.

    At the charged maximum of three settlements the funding is 0.0200R, inside
    it; at the typical two it is 0.0133R. The rule is MORE conservative than its
    own derivation assumed, which is the safe direction and is why §6.1 records
    the discrepancy as a finding rather than a repair.
    """
    floor_stop = 0.0150
    charged = es.FUNDING_RATE_PER_SETTLEMENT * es.FUNDING_SETTLEMENTS_CHARGED \
        / floor_stop
    typical = es.FUNDING_RATE_PER_SETTLEMENT * 2 / floor_stop
    assert charged == pytest.approx(0.0200, abs=1e-9)
    assert typical == pytest.approx(0.013333, abs=1e-6)
    assert charged <= 0.022
    assert typical < charged, "the typical position is overcharged"


# ---------------------------------------------------------------------------
# 3. THE FILL RULES MUST BE DISTINGUISHABLE.
# ---------------------------------------------------------------------------

def _touch_fills_long(high, target):
    """The rule E3 REJECTS, written here so the two can be compared."""
    return high >= target


def _trade_through_fills_long(high, target, tick):
    """E3 as specified."""
    return high >= target + tick


def _touch_fills_short(low, target):
    return low <= target


def _trade_through_fills_short(low, target, tick):
    return low <= target - tick


def test_trade_through_is_STRICTLY_more_conservative_than_touch():
    """THE CENTRAL DISTINGUISHING TEST FOR E3.

    On a bar that touches the target EXACTLY, touch fills and trade-through does
    not. If the two ever became the same predicate the winning leg would have
    quietly become more generous and every downstream figure would still look
    reasonable.
    """
    target, tick = 2_000.00, 0.01

    # Touches exactly: touch fills, trade-through does NOT.
    assert _touch_fills_long(target, target) is True
    assert _trade_through_fills_long(target, target, tick) is False
    assert _touch_fills_short(target, target) is True
    assert _trade_through_fills_short(target, target, tick) is False

    # One tick through: BOTH fill.
    assert _trade_through_fills_long(target + tick, target, tick) is True
    assert _trade_through_fills_short(target - tick, target, tick) is True

    # Strictly more conservative: anything trade-through fills, touch fills too.
    for delta in (-2, -1, 0, 1, 2, 5):
        high = target + delta * tick
        if _trade_through_fills_long(high, target, tick):
            assert _touch_fills_long(high, target)


def test_the_stop_touch_is_inclusive():
    """E2. A conditional MARKET order does not rest, so there is no queue to be
    behind: triggered at the level, it fires at the level."""
    stop = 1_950.00
    assert (stop <= stop) is True, "long: low == stop fills"
    assert (stop >= stop) is True, "short: high == stop fills"
    assert (stop + 0.01 <= stop) is False
    assert (stop - 0.01 >= stop) is False


def test_the_tick_is_resolved_per_timestamp_not_per_symbol():
    """E3. SOLUSDT's tick changed on 2024-08-14, inside the window.

    A fill rule that used one tick per symbol would apply the wrong margin to
    two and a half years of SOL bars.
    """
    import sys
    sys.path.insert(0, os.path.join(ROOT, "src", "engine"))
    import contracts

    schedules = contracts.load_cache()
    change_ms = 1_723_608_300_000  # 2024-08-14T04:05:00Z
    before = schedules["SOLUSDT"].tick_at(change_ms - HOUR_MS)
    after = schedules["SOLUSDT"].tick_at(change_ms + HOUR_MS)
    assert before == pytest.approx(0.0001)
    assert after == pytest.approx(0.001)
    assert before != after, "the fixture must straddle the change"

    # And the trade-through margin therefore differs on the two sides.
    target = 100.0
    assert _trade_through_fills_long(target + 0.0005, target, before) is True
    assert _trade_through_fills_long(target + 0.0005, target, after) is False

    # BTC and ETH have a single segment each over the same window.
    for symbol in ("BTCUSDT", "ETHUSDT"):
        assert schedules[symbol].is_constant(), symbol


def test_stop_first_precedence_resolves_a_bar_that_satisfies_both():
    """E4 and E5, as predicates on hand-written numbers.

    No bar is read; these are the two comparisons the engine will make, checked
    against the specification's stated answer.
    """
    assert es.INTRABAR_PRECEDENCE == "stop_first"
    assert es.TIME_EXIT_VS_STOP == "stop_first"

    # A 1m bar spanning both levels on a long: low <= stop AND high >= target+tick
    stop, target, tick = 1_950.0, 2_000.0, 0.01
    low, high = 1_949.0, 2_001.0
    stop_hits = low <= stop
    target_hits = high >= target + tick
    assert stop_hits and target_hits, "the fixture must satisfy BOTH"
    resolved = "stop" if es.INTRABAR_PRECEDENCE == "stop_first" else "target"
    assert resolved == "stop"


# ---------------------------------------------------------------------------
# 4. THE VENUE RETRIEVAL -- schema and negative controls.
# ---------------------------------------------------------------------------

def test_the_trigger_basis_snapshot_exists_and_hashes_to_its_manifest():
    manifest = tb.load_manifest()
    assert manifest["retrieval_method"].startswith("automated")
    assert len(manifest["calls"]) == 3
    for call in manifest["calls"]:
        path = os.path.join(tb.SNAPSHOT_DIR, call["snapshot_file"])
        assert os.path.exists(path), path
        assert tb.sha256_of(path) == call["sha256"], call["snapshot_file"]
        assert call["http_status"] == 200
        assert call["requested_url"].startswith("https://")


def test_the_retrieved_trigger_basis_is_last_price():
    """THE ANSWER THE SPECIFICATION DEPENDS ON, read back from disk."""
    finding = tb.summarise()
    assert finding["parameter_name"] == "triggerType" == \
        es.TRIGGER_PRICE_PARAMETER
    assert finding["last_price_token"] == "fill_price" == es.TRIGGER_PRICE_BASIS
    assert "market_price" in finding["values_found"]
    assert finding["selectable_per_order"] is True
    assert finding["documented_default"] == "fill_price"
    assert finding["default_is_last_price"] is True
    assert finding["rows_requiring_it"] >= 1, (
        "some endpoints require it outright; that is part of the answer")
    # The v2 pages returned a shell, confirming report 25's finding.
    assert all(finding["v2_pages_returned_a_shell"].values())


def test_negative_control_a_truncated_response_raises():
    """A body cut short must not parse to an empty finding.

    An empty finding would be reported as "the venue documents no trigger
    basis", which is the most dangerous sentence this retrieval could produce.
    """
    text = tb.load_raw("v1_mix_doc")
    with pytest.raises(tb.SchemaError, match="empty or truncated"):
        tb.parse_trigger_basis(text[:500])
    with pytest.raises(tb.SchemaError):
        tb.parse_trigger_basis("")


def test_negative_control_a_renamed_field_raises():
    """The failure mode a documentation change actually produces."""
    text = tb.load_raw("v1_mix_doc")

    renamed = text.replace("triggerType", "triggerBasis")
    with pytest.raises(tb.SchemaError, match="triggerType"):
        tb.parse_trigger_basis(renamed)

    no_last = text.replace("fill_price", "execution_price")
    with pytest.raises(tb.SchemaError, match="last-price token"):
        tb.parse_trigger_basis(no_last)

    no_mark = text.replace("market_price", "index_price").replace(
        "mark_price", "index_price")
    with pytest.raises(tb.SchemaError, match="mark-price token"):
        tb.parse_trigger_basis(no_mark)


def test_a_page_naming_the_parameter_with_no_row_raises():
    """Named but not tabulated is not an answer."""
    fake = ("x" * 2000) + " triggerType fill_price market_price " + ("y" * 2000)
    with pytest.raises(tb.SchemaError, match="no parameter ROW"):
        tb.parse_trigger_basis(fake)


def test_two_conflicting_defaults_raise():
    """If the page ever declared two, the parser must refuse rather than pick."""
    fake = ("x" * 2000 + " triggerType Words Description fill_price fill price "
            "market_price mark price "
            "triggerType String No Trigger Type default &#39;fill_price&#39; "
            "triggerType String No Trigger Type default &#39;market_price&#39; ")
    with pytest.raises(tb.SchemaError, match="more than one default"):
        tb.parse_trigger_basis(fake)


def test_the_entity_unescaping_is_load_bearing():
    """The default is rendered as `&#39;fill_price&#39;`.

    A parser that left entities encoded would find the parameter, find its
    values, and SILENTLY MISS the one row that declares a default -- reporting
    UNRETRIEVED for a fact the page states.
    """
    raw = tb.load_raw("v1_mix_doc")
    assert "&#39;" in raw, "the fixture must actually contain entities"
    flat = tb.plain_text(raw)
    assert "default 'fill_price'" in flat
    assert "&#39;" not in flat


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


def test_the_module_imports_nothing_at_all():
    """The strongest available form of "this is constants only".

    A module with no imports cannot reach a bar, cannot reach the 1m loader
    whose seal gap is still open, and cannot acquire a dependency without
    someone editing this assertion.
    """
    assert _imports() == set(), _imports()
    banned = ("src.timeframe", "src.folds", "src.analysis", "src.engine",
              "src.sweep", "src.regime", "pandas", "numpy", "pyarrow")
    for mod in _imports():
        for bad in banned:
            assert not (mod == bad or mod.startswith(bad + ".")), mod


def test_the_module_carries_no_logic():
    """No fill function, no comparison against a bar, no simulation."""
    tree = _module_ast()
    assert [n.name for n in ast.walk(tree)
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))] == []
    assert [n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)] == []
    src = open(es.__file__).read()
    for word in ("load_1m", "ohlcv", "parquet", "read_", "def "):
        assert word not in src, word


def test_no_1m_loader_is_touched():
    """THE 1m SEAL GAP IS STILL OPEN. This step must not touch that path.

    Checked over the module's VALUES and identifiers, not its prose: the
    docstrings NAME the seal and the 1m loader in order to record that neither
    is touched, so a raw text search would fire on the statement of the rule.
    The real guarantee is that the module imports nothing at all, asserted
    above -- a module with no imports cannot reach a loader.
    """
    tree = _module_ast()
    docstrings = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.FunctionDef, ast.ClassDef)):
            d = ast.get_docstring(node, clean=False)
            if d is not None:
                docstrings.add(d)
        for stmt in getattr(node, "body", []):
            if (isinstance(stmt, ast.Expr)
                    and isinstance(stmt.value, ast.Constant)
                    and isinstance(stmt.value.value, str)):
                docstrings.add(stmt.value.value)
    values = " ".join(
        n.value for n in ast.walk(tree)
        if isinstance(n, ast.Constant) and isinstance(n.value, str)
        and n.value not in docstrings).lower()
    for word in ("load_1m", "bar_1m_ms", "authorised", "holdout", "parquet"):
        assert word not in values, word
    assert _imports() == set()


#: 5.3.4 DID THE WIRING, AND IT IS ONE FILE. The docstring above said "5.3.4
#: does the wiring"; report 30's execution path is that module. Every other
#: engine file is still refused unconditionally.
PERMITTED_ENGINE_IMPORTER = "portfolio.py"


def test_nothing_is_wired_in_yet():
    """NO ENGINE FILE IMPORTS THE RISK PACKAGE EXCEPT THE EXECUTION PATH.

    Report 26's assertion is enforced from its own test module; this asserts the
    narrower fact that matters here -- the constants are not reachable from any
    engine file other than the one 5.3.4 built to read them.
    """
    engine_dir = os.path.join(ROOT, "src", "engine")
    for name in os.listdir(engine_dir):
        if not name.endswith(".py") or name == PERMITTED_ENGINE_IMPORTER:
            continue
        text = open(os.path.join(engine_dir, name)).read()
        assert "exit_spec" not in text, name
        assert "src.risk" not in text, name


def test_the_execution_path_reads_the_spec_rather_than_restating_it():
    """THE ONE PERMITTED IMPORTER, AND WHAT IT IS PERMITTED TO DO.

    It may READ these constants. It may not carry a second copy of any of them:
    `tests/test_portfolio.py` asserts no numeric literal in it equals a frozen
    value, and this asserts the values it uses are this module's own objects.
    """
    sys.path.insert(0, os.path.join(ROOT, "src", "engine"))
    import portfolio

    assert portfolio.FUNDING_RATE is es.FUNDING_RATE_PER_SETTLEMENT
    assert portfolio.FUNDING_COUNT is es.FUNDING_SETTLEMENTS_CHARGED
    text = open(portfolio.__file__).read()
    assert "exit_spec" in text, "the execution path must READ the spec"


PERFORMANCE_NAMES = ("expectancy", "win_rate", "winrate", "profit_factor",
                     "sharpe", "sortino", "net_pnl", "gross_pnl", "drawdown",
                     "r_multiple", "equity", "pnl")


def test_no_performance_quantity_appears_in_the_module():
    """THE TWELVE-NAME GUARD, over identifiers and non-docstring literals."""
    tree = _module_ast()
    docstrings = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.FunctionDef, ast.ClassDef)):
            d = ast.get_docstring(node, clean=False)
            if d is not None:
                docstrings.add(d)
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
        elif isinstance(node, ast.Constant) and isinstance(node.value, str):
            if node.value not in docstrings:
                names.add(node.value)
    blob = " ".join(names).lower()
    for banned in PERFORMANCE_NAMES:
        assert banned not in blob, banned


def test_the_retrieval_module_reads_no_market_data():
    tree = ast.parse(open(tb.__file__).read())
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                imported.add(a.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imported.add(node.module)
    banned = ("src.timeframe", "src.folds", "src.analysis", "src.engine",
              "pandas", "numpy", "pyarrow")
    for mod in imported:
        for bad in banned:
            assert not (mod == bad or mod.startswith(bad + ".")), mod
    src = open(tb.__file__).read()
    for word in ("ohlcv", "parquet", "load_1m", "load_bars"):
        assert word not in src, word


# ---------------------------------------------------------------------------
# 6. THE COMPLETENESS CITATION.
# ---------------------------------------------------------------------------

def test_the_1m_completeness_figure_is_the_one_report_19_states(doc):
    """CITED, NOT RE-MEASURED. No 1m bar is read by this step."""
    report_19 = os.path.join(ROOT, "reports", "19_timeframe_selection.md")
    text = open(report_19).read()
    assert "1,578,240" in text
    assert "1096 × 1440 = 1,578,240" in text or "1096 x 1440" in text
    assert "1,578,240" in doc, "the design document must cite the figure"
    # 1096 days over 2022-2024, and the per-year arithmetic in the document.
    assert 365 * 1440 == 525_600
    assert 366 * 1440 == 527_040
    assert 525_600 + 525_600 + 527_040 == 1_578_240
    assert "525,600" in doc and "527,040" in doc


# ---------------------------------------------------------------------------
# AMENDMENT 1 -- funding in P&L, funding in the target solve, and E8's
# out-of-sample status.
#
# docs/design/06a_exit_resolution_spec_amendment_1.md
#
# THE CENTRAL ASSERTION OF THIS BLOCK IS THAT THE TWO FUNDING FORMS ARE
# DISTINGUISHABLE. Funding in the denominator ALONE leaves the stop identity
# exact -- the denominator is both what sizes the position and what is lost at
# the stop, so a term added there is added to both sides at once -- while the
# target identity drifts to about 1.482R. That is 1.2% of the reward, it raises
# no exception, and the identity an implementer would check first keeps passing.
# It is asserted here in both forms so a future implementation that omits the
# term fails loudly rather than returning a slightly smaller number forever.
#
# THE CARVE-OUT IS REPORT 28 SECTION 4.1's, UNWIDENED. Verifying the identities
# requires computing net proceeds at a price. It is permitted on SYNTHETIC
# REFERENCE INPUTS ONLY, through EXACTLY ONE named function -- asserted over the
# AST of this module -- with the twelve-name ban otherwise intact. Nothing here
# reads a bar or asks whether a price was reached.
# ---------------------------------------------------------------------------

import sys  # noqa: E402  (amendment block, kept together)

sys.path.insert(0, os.path.join(ROOT, "src", "engine"))

import costs  # noqa: E402
import sizing  # noqa: E402

AMENDMENT_PATH = os.path.join(
    ROOT, "docs", "design", "06a_exit_resolution_spec_amendment_1.md")

FROZEN_SPEC_SHA256 = FROZEN_DESIGN_HASHES["06_exit_resolution_spec.md"]
"""docs/design/06_exit_resolution_spec.md as frozen at 6def4cb."""

LONG, SHORT = sizing.LONG, sizing.SHORT

REWARD_TO_RISK = 1.5
"""Thesis §5.2, supplied explicitly and never read from the config."""

#: The frozen fee/slippage configuration reports 24, 26, 27 and 28 all size
#: against. Report 28 §3.1's carve-out conditions apply to every use of it here.
CFG_KW = dict(stop_atr_mult=2.25, stop_max_pct=0.035,
              rvol_threshold=1.5, baseline_days=20)

#: SYNTHETIC REFERENCE CELLS. Hand-chosen prices, never a bar and never a
#: signal. The ATR on each is small enough that the 1.50% floor sets the stop,
#: which is the stratum §4.2's `0.0200R` comparison figure is pinned to.
FLOOR_BOUND_CELLS = [("BTCUSDT", 30_000.0, 100.0),
                     ("ETHUSDT", 2_000.0, 5.0),
                     ("SOLUSDT", 100.0, 0.3)]

#: The same, with the ATR setting the stop instead of the floor. Report 28 §9
#: measured 8,457 of 11,384 candidates in this stratum.
ATR_BOUND_CELLS = [("BTCUSDT", 30_000.0, 300.0),
                   ("ETHUSDT", 2_000.0, 20.0),
                   ("SOLUSDT", 100.0, 1.0)]


@pytest.fixture(scope="module")
def cfg():
    return costs.CostConfig(**CFG_KW)


@pytest.fixture(scope="module")
def specs():
    return sizing.load_symbol_specs()


@pytest.fixture(scope="module")
def ticks():
    return sizing.load_tick_schedules()


@pytest.fixture(scope="module")
def amendment():
    assert os.path.exists(AMENDMENT_PATH), AMENDMENT_PATH
    with open(AMENDMENT_PATH) as fh:
        return fh.read()


def _tick(ticks, symbol):
    """The CURRENT segment's tick, adequate for a synthetic reference."""
    return ticks[symbol].segments[-1][1]


def funding_per_unit(entry_price):
    """E7.3. THE CONSTRUCTION RULE, AND IT IS THE ONLY ONE.

    Three inputs and one multiplication: entry price, rate, count. NOT derived
    from, back-solved from, or cross-checked against any R-share figure --
    neither document 06 §6.1's 0.0200R, which is `rate x n / s` at the FLOOR
    stop and is a comparison against the frozen budget, nor the 0.0180R realised
    share `rate x n / (s + c)`. Both are right for their own purpose and neither
    is the way to compute this term.
    """
    return (float(entry_price)
            * es.FUNDING_RATE_PER_SETTLEMENT
            * es.FUNDING_SETTLEMENTS_CHARGED)


def _funded_reference(cfg, specs, ticks, symbol, direction, entry, atr,
                      risk_usd=20.0, funding_in_bracket=True):
    """One SYNTHETIC sized position with funding in the denominator.

    Report 28's order of operations, unchanged, with `funding_pu` added to the
    denominator per E7.2. `funding_in_bracket` selects between the SPECIFIED
    target solve and the defective one that omits the term from the cost
    bracket, so the two can be compared by test rather than by prose.

    NO BAR IS READ. Entry price and ATR are hand-written numbers.
    """
    spec = specs[symbol]
    tick = _tick(ticks, symbol)

    raw = sizing.stop_distance(entry, atr)
    stop = sizing.stop_price_on_tick(entry, raw, direction, tick)
    effective = sizing.effective_stop_distance(entry, stop, direction)

    d_no_funding = sizing.per_unit_denominator(entry, stop, direction, cfg,
                                               symbol)
    funding_pu = funding_per_unit(entry)
    d = d_no_funding + funding_pu

    qty_unfloored = risk_usd / d
    qty = sizing.floor_to_step(qty_unfloored, spec.qty_step)
    realised = qty * d

    f = float(cfg.taker_fee)
    m = float(cfg.maker_fee)
    e = float(cfg.entry_slippage_bps) / 10_000.0
    bracket = funding_pu if funding_in_bracket else 0.0

    if direction == LONG:
        target = (REWARD_TO_RISK * d + bracket + entry * (1.0 + f + e)) \
            / (1.0 - m)
        on_tick = costs.round_to_tick(target, tick, "up")
    else:
        target = (entry * (1.0 - f - e) - REWARD_TO_RISK * d - bracket) \
            / (1.0 + m)
        on_tick = costs.round_to_tick(target, tick, "down")

    return dict(symbol=symbol, direction=direction, entry=entry, tick=tick,
                stop=stop, stop_distance=effective,
                denominator_ex_funding=d_no_funding, funding_pu=funding_pu,
                denominator=d, qty_unfloored=qty_unfloored, qty=qty,
                realised_risk_usd=realised, target=target,
                target_on_tick=on_tick,
                floor_bound=sizing.floor_binds(entry, atr))


def net_proceeds_per_unit_with_funding(entry_price, exit_price, direction, cfg,
                                       exit_fee_rate, funding_pu,
                                       exit_haircut_fraction=0.0):
    """THE RECORDED CARVE-OUT, AND THIS MODULE'S ONLY ONE.

    Report 28 §4.1 permits computing net proceeds at a price under three
    conditions, all asserted below: SYNTHETIC REFERENCE INPUTS ONLY, EXACTLY ONE
    NAMED FUNCTION, and the twelve-name ban otherwise intact. This is that one
    function for the exit specification, and it does not widen the carve-out --
    it reuses `sizing.net_proceeds_per_unit` verbatim and subtracts the single
    term Amendment 1 adds.

    E7.1: `funding_pu` is the PROVISIONED charge and it is subtracted whatever
    the exit was. There is no reconciliation to the settlements actually
    crossed, so the same term is charged at a stop, at a target and at a time
    exit alike.

    IT DOES NOT ASK WHETHER A PRICE WAS REACHED. The exit price is supplied by
    the caller. It is arithmetic on two prices.
    """
    return sizing.net_proceeds_per_unit(
        entry_price, exit_price, direction, cfg, exit_fee_rate,
        exit_haircut_fraction) - float(funding_pu)


# ---------------------------------------------------------------------------
# A1. THE CONSTANTS, AND THE AMENDMENT THAT STATES THEM.
# ---------------------------------------------------------------------------

def test_the_amendment_constants():
    assert es.FUNDING_REALISED_TREATMENT == "provisioned_not_reconciled"
    assert es.FUNDING_IN_TARGET_SOLVE is True
    assert es.MISSING_BAR_INERT_IN_SAMPLE is True


def test_no_frozen_constant_changed_value():
    """AMENDMENT 1 REVERSES NO RULE. E1-E6 and E9 are untouched, and every
    value document 06 §10 states stands exactly as frozen."""
    assert es.EXIT_RESOLUTION == "1m"
    assert es.STOP_FILL_RULE == "touch_inclusive"
    assert es.TARGET_FILL_RULE == "trade_through_one_tick"
    assert es.INTRABAR_PRECEDENCE == "stop_first"
    assert es.TIME_EXIT_VS_STOP == "stop_first"
    assert es.FUNDING_CHARGED == "in_sizing_denominator_at_entry"
    assert es.FUNDING_SETTLEMENTS_CHARGED == 3
    assert es.FUNDING_RATE_PER_SETTLEMENT == 0.0001
    assert es.MISSING_BAR_RULE == "flag_and_count"
    assert es.TRIGGER_PRICE_BASIS == "fill_price"
    assert es.TRIGGER_PRICE_PARAMETER == "triggerType"


def _flat(text):
    """Whitespace-collapsed, so a prose assertion is about the SENTENCE and not
    about where the paragraph happened to wrap."""
    return re.sub(r"\s+", " ", text)


def _amendment_block(text):
    blocks = re.findall(r"```\n(.*?)```", text, re.DOTALL)
    hits = [b for b in blocks if "FUNDING_REALISED_TREATMENT" in b]
    assert len(hits) == 1, (
        "the amendment must carry exactly ONE constants block; found %d"
        % len(hits))
    return dict(CANONICAL_RE.findall(hits[0]))


def test_the_amendment_document_states_the_same_constants(amendment):
    """PARSED FROM THE MARKDOWN, so a transcription drift fails."""
    import ast as _ast

    stated = _amendment_block(amendment)
    assert set(stated) == {"FUNDING_REALISED_TREATMENT",
                           "FUNDING_IN_TARGET_SOLVE",
                           "MISSING_BAR_INERT_IN_SAMPLE"}
    for name, raw in stated.items():
        assert _ast.literal_eval(raw) == getattr(es, name), name
    assert _ast.literal_eval(stated["FUNDING_IN_TARGET_SOLVE"]) is True
    assert _ast.literal_eval(stated["MISSING_BAR_INERT_IN_SAMPLE"]) is True


def test_a_planted_drift_between_amendment_and_module_is_detected(amendment):
    stated = _amendment_block(amendment)
    stated["FUNDING_REALISED_TREATMENT"] = '"provisioned_then_reconciled"'
    assert stated["FUNDING_REALISED_TREATMENT"].strip('"') \
        != es.FUNDING_REALISED_TREATMENT


def test_the_frozen_canonical_block_is_untouched_by_the_amendment(doc,
                                                                  amendment):
    """DOCUMENT 06 §10 STILL CARRIES EXACTLY ITS ELEVEN ORIGINAL NAMES.

    The amendment ADDS constants; it does not edit the frozen block, and it does
    not restate it either -- a second copy of the canonical block would make
    `_canonical_block`'s "exactly one" assertion a matter of which file was read.
    """
    stated = _canonical_block(doc)
    assert len(stated) == 11
    assert "FUNDING_REALISED_TREATMENT" not in stated
    assert "EXIT_RESOLUTION" not in _amendment_block(amendment)


def test_the_amendment_names_the_hashes_of_all_four_frozen_documents(amendment):
    """THE AMENDMENT MUST NAME WHAT IT LEAVES UNALTERED."""
    for name, expected in FROZEN_DESIGN_HASHES.items():
        assert expected in amendment, name
    assert FROZEN_SPEC_SHA256 in amendment
    assert "6def4cb" in amendment, "the commit document 06 is frozen at"


def test_document_06_is_byte_for_byte_unchanged():
    """THE AMENDMENT PROCEDURE IS THE POINT, AND THIS IS WHAT ENFORCES IT.

    Document 06 §8: an amendment is a new document with its own commit; a silent
    edit is a contamination event. This test must fail if document 06 ever
    differs by a single character, whatever the reason.
    """
    with open(DOC_PATH, "rb") as fh:
        digest = hashlib.sha256(fh.read()).hexdigest()
    assert digest == FROZEN_SPEC_SHA256, (
        "docs/design/06_exit_resolution_spec.md HAS BEEN EDITED. It is frozen "
        "at 6def4cb and a correction is a new document, never an edit.")


def test_the_amendment_carries_its_required_sections(amendment):
    headings = re.findall(r"^## (\d+)\.\s+(.+)$", amendment, re.MULTILINE)
    assert [int(n) for n, _ in headings] == list(range(1, 11))
    titles = {int(n): t.upper() for n, t in headings}
    assert "NOT REVERSED" in titles[1]
    assert "NOT RECONCILED" in titles[2]
    assert "BOTH SIDES" in titles[3]
    assert "CONSTRUCTION" in titles[4]
    assert "INERT IN-SAMPLE" in titles[5]
    assert "CONSTANTS" in titles[6]
    assert "UNMODIFIED" in titles[7]
    assert "ESCALATION CLAUSE" in titles[8]
    assert "PRE-REGISTRATION" in titles[9]
    assert "MAY NOT BE EDITED" in titles[10]

    parts = [_flat(p) for p
             in re.split(r"^## \d+\.\s+", amendment, flags=re.MULTILINE)[1:]]
    required = {
        1: ("E1 through E6 and E9 are untouched", "not one character",
            "gaps, not corrections"),
        2: ("−1.0R", "+1.5R", "40.0%", "39.7%", "0.0067R", "21 of"),
        3: ("1.482R", "invisible without looking", "invariant to the quantity"),
        4: ("0.0200R", "0.0180R", "entry × rate × count", "floor"),
        5: ("1,578,240", "zero times", "unknown", "MAKER_NONFILL_COST_R",
            "even when it is zero", "separately"),
        6: ("provisioned_not_reconciled", "no logic"),
        7: ("supersedes nothing", "6def4cb"),
        8: ("one amendment", "re-specify", "not to write amendment 2"),
        9: ("git log", "synthetic reference inputs only", "no 1m bar was read"),
        10: ("contamination event", "in advance"),
    }
    for number, tokens in required.items():
        for token in tokens:
            assert token.lower() in parts[number - 1].lower(), (number, token)


# ---------------------------------------------------------------------------
# A2. THE TWO IDENTITIES -- funding on BOTH sides, and the form that fails.
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("symbol,entry,atr", ATR_BOUND_CELLS + FLOOR_BOUND_CELLS)
@pytest.mark.parametrize("direction", [LONG, SHORT])
def test_the_R_identities_hold_with_funding_on_BOTH_sides(
        cfg, specs, ticks, symbol, entry, atr, direction):
    """E7.1 AND E7.2 TOGETHER, AT A FLOORED QUANTITY, LONG AND SHORT.

    With `funding_pu` in the denominator AND in the target cost bracket, a stop
    exit returns exactly -1.0 realised risk units and a target exactly +1.5.
    That is what E7.1 buys: report 28's identities and the thesis's 40.0% / 53.6%
    arithmetic hold EXACTLY rather than approximately.

    THE TARGET IS ASSERTED TWICE -- exactly on the unrounded solve, and within
    ONE TICK and always FAVOURABLE on the tick-rounded price, which is report 28
    §4.2's own result and its reason: the target rounds AWAY from entry and can
    therefore only deliver more than the reward, never less.
    """
    p = _funded_reference(cfg, specs, ticks, symbol, direction, entry, atr)
    assert p["qty"] < p["qty_unfloored"], "the fixture must actually floor"
    assert p["funding_pu"] > 0.0

    haircut = cfg.haircut_bps(symbol) / 10_000.0
    at_stop = net_proceeds_per_unit_with_funding(
        entry, p["stop"], direction, cfg, cfg.taker_fee, p["funding_pu"],
        haircut) * p["qty"]
    assert at_stop == pytest.approx(-1.0 * p["realised_risk_usd"], rel=1e-12)

    at_target = net_proceeds_per_unit_with_funding(
        entry, p["target"], direction, cfg, cfg.maker_fee,
        p["funding_pu"]) * p["qty"]
    assert at_target == pytest.approx(1.5 * p["realised_risk_usd"], rel=1e-12)

    on_tick = net_proceeds_per_unit_with_funding(
        entry, p["target_on_tick"], direction, cfg, cfg.maker_fee,
        p["funding_pu"]) * p["qty"]
    excess = on_tick / p["realised_risk_usd"] - 1.5
    assert excess >= 0.0, "tick rounding must never deliver LESS than 1.5R"
    assert excess <= p["tick"] / p["denominator"], "never more than one tick"


@pytest.mark.parametrize("symbol,entry,atr", FLOOR_BOUND_CELLS)
@pytest.mark.parametrize("direction", [LONG, SHORT])
def test_the_target_identity_FAILS_with_funding_in_the_DENOMINATOR_ONLY(
        cfg, specs, ticks, symbol, entry, atr, direction):
    """THE FAILURE E7.2 EXISTS TO PREVENT, ASSERTED SO IT CANNOT RETURN.

    Funding in `d` alone leaves the STOP identity exact -- the denominator is
    both what sizes the position and what is lost at the stop, so a term added
    there is added to both sides at once -- while the TARGET identity drifts to
    `1.5R - funding_pu / d`, about 1.482R at the floor stop.

    The two forms must be distinguishable BY TEST, not only by prose, so a
    future implementation that omits the term from the cost bracket fails loudly
    instead of returning a slightly smaller number forever.
    """
    bad = _funded_reference(cfg, specs, ticks, symbol, direction, entry, atr,
                            funding_in_bracket=False)
    good = _funded_reference(cfg, specs, ticks, symbol, direction, entry, atr)
    assert bad["floor_bound"] is True, "the 1.482R figure is a floor-stop one"
    assert bad["denominator"] == good["denominator"], (
        "the two forms must differ ONLY in the cost bracket")
    assert bad["target"] != good["target"]

    haircut = cfg.haircut_bps(symbol) / 10_000.0

    # THE STOP IDENTITY STILL PASSES. That is exactly why the defect is
    # invisible: the identity an implementer checks first is unaffected.
    at_stop = net_proceeds_per_unit_with_funding(
        entry, bad["stop"], direction, cfg, cfg.taker_fee, bad["funding_pu"],
        haircut) * bad["qty"]
    assert at_stop == pytest.approx(-1.0 * bad["realised_risk_usd"], rel=1e-12)

    # THE TARGET IDENTITY DOES NOT.
    at_target = net_proceeds_per_unit_with_funding(
        entry, bad["target"], direction, cfg, cfg.maker_fee,
        bad["funding_pu"]) * bad["qty"]
    ratio = at_target / bad["realised_risk_usd"]
    drift = bad["funding_pu"] / bad["denominator"]

    assert ratio != pytest.approx(1.5, rel=1e-9), (
        "THE DEFECTIVE SOLVE MUST MISS THE TARGET IDENTITY")
    assert ratio == pytest.approx(1.5 - drift, rel=1e-12)
    assert 1.4820 < ratio < 1.4830, ratio
    assert 0.0170 < drift < 0.0180, drift


def test_QUANTITY_INVARIANCE_is_preserved_with_funding_present(cfg, specs,
                                                               ticks):
    """REPORT 28 §3.2's CENTRAL TEST, RE-RUN WITH THE NEW TERM.

    `funding_pu` depends on entry price, rate and count and NOT on quantity, so
    it cancels from both sides of the solve exactly as the fee and slippage legs
    do. ASSERTED, NOT ASSUMED: a term introduced as a DOLLAR charge rather than
    a per-unit PRICE charge would break the invariance while looking correct in
    every other respect, reinstating the exact defect report 28 exists to fix.
    """
    for symbol, entry, atr in ATR_BOUND_CELLS:
        for direction in (LONG, SHORT):
            small = _funded_reference(cfg, specs, ticks, symbol, direction,
                                      entry, atr, risk_usd=20.0)
            large = _funded_reference(cfg, specs, ticks, symbol, direction,
                                      entry, atr, risk_usd=200.0)
            assert large["qty"] > 9.0 * small["qty"], (
                "the fixture must vary quantity")
            assert small["target_on_tick"] == large["target_on_tick"], (
                "THE TARGET PRICE MUST NOT DEPEND ON QUANTITY")
            assert small["target"] == large["target"]
            assert small["denominator"] == large["denominator"]
            assert small["funding_pu"] == large["funding_pu"]


# ---------------------------------------------------------------------------
# A3. E7.3 -- CONSTRUCTION, NOT BACK-SOLVE.
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("symbol,entry,atr", ATR_BOUND_CELLS)
def test_funding_pu_is_CONSTRUCTED_and_is_not_confusable_with_0_0200R(
        cfg, specs, ticks, symbol, entry, atr):
    """E7.3. THE CONSTRUCTION RULE AND THE COMPARISON FIGURES MUST NOT BE
    CONFUSABLE.

    `funding_pu` is `entry x rate x count`. It is NOT `0.0200 x s` -- document
    06 §6.1's figure is `rate x n / s` at the 1.50% FLOOR stop, correct for
    comparison against thesis §5.3's budget and wrong as a construction rule --
    and it is NOT `0.0180 x d`, the realised share of the risk unit.

    THESE CELLS ARE NOT FLOOR-BOUND ON PURPOSE. At the floor the back-solve and
    the construction COINCIDE exactly, which is why they are confusable at all;
    the next test pins that coincidence so the reason is on the record.
    """
    p = _funded_reference(cfg, specs, ticks, symbol, LONG, entry, atr)
    assert p["floor_bound"] is False, "this cell must be ATR-bound"

    assert p["funding_pu"] == (entry * es.FUNDING_RATE_PER_SETTLEMENT
                               * es.FUNDING_SETTLEMENTS_CHARGED)
    assert p["funding_pu"] == funding_per_unit(entry)

    back_solved_from_the_stop = 0.0200 * p["stop_distance"]
    back_solved_from_the_unit = 0.0180 * p["denominator"]
    assert p["funding_pu"] != pytest.approx(back_solved_from_the_stop,
                                            rel=1e-6)
    assert p["funding_pu"] != pytest.approx(back_solved_from_the_unit,
                                            rel=1e-6)
    assert back_solved_from_the_stop > p["funding_pu"], (
        "0.0200 x s OVERSTATES the term away from the floor")

    # The realised share is neither comparison figure either.
    share = p["funding_pu"] / p["denominator"]
    assert share != pytest.approx(0.0200, rel=1e-3)
    assert share != pytest.approx(0.0180, rel=1e-3)


def test_the_back_solve_COINCIDES_with_the_construction_at_the_floor_stop(
        cfg, specs, ticks):
    """WHY THE TRAP IS REAL, PINNED RATHER THAN ASSERTED.

    At the 1.50% floor stop, `0.0200 x s` EQUALS `entry x rate x count`
    exactly -- 9.00 against 9.00 on the BTCUSDT reference -- so an
    implementation that back-solved the term would pass any test written at the
    floor and be wrong by half on the 8,457 of 11,384 candidates that are not
    floor-bound (report 28 §9).
    """
    symbol, entry, atr = FLOOR_BOUND_CELLS[0]
    p = _funded_reference(cfg, specs, ticks, symbol, LONG, entry, atr)
    assert p["floor_bound"] is True
    assert p["stop_distance"] == pytest.approx(0.0150 * entry, rel=1e-12)
    assert 0.0200 * p["stop_distance"] == pytest.approx(p["funding_pu"],
                                                        rel=1e-12)
    assert p["funding_pu"] == pytest.approx(9.00, abs=1e-9)

    wide = _funded_reference(cfg, specs, ticks, symbol, LONG,
                             entry, ATR_BOUND_CELLS[0][2])
    assert wide["floor_bound"] is False
    assert 0.0200 * wide["stop_distance"] == pytest.approx(13.50, abs=1e-9)
    assert wide["funding_pu"] == pytest.approx(9.00, abs=1e-9), (
        "the term does not move with the stop; the back-solve does")


# ---------------------------------------------------------------------------
# A4. E8.1 -- THE INERT BRANCH, EXERCISED AT VALUES WHERE IT IS REACHABLE.
# ---------------------------------------------------------------------------

MINUTE_MS = 60_000


def _missing_1m_bars(present_ms, open_ms, close_ms, step_ms=MINUTE_MS):
    """E8, as a predicate on HAND-WRITTEN integer timestamps.

    Returns `(flagged, count)` for a position held across `[open, close)`. No
    market data of any resolution is involved and the 1m seal is not touched:
    the series here are built by `range`, not loaded.
    """
    have = set(int(t) for t in present_ms)
    missing = [t for t in range(int(open_ms), int(close_ms), int(step_ms))
               if t not in have]
    return (len(missing) > 0, len(missing))


def test_E8_a_synthetic_1m_series_WITH_HOLES_sets_the_flag_and_counts_them():
    """THE REACHABLE-VALUE TEST DOCUMENT 05 §4's TREATMENT REQUIRES.

    E8's flag fires zero times in-sample -- report 19 measured the 1m layer as
    exactly full over 2022-2024 -- so without this test the branch would be
    invisible to the entire suite. THAT IS `MAKER_NONFILL_COST_R` AGAIN: a term
    invisible to all 545 tests then in the suite because every one of them
    multiplied it by zero.
    """
    open_ms = 1_700_000_000_000
    close_ms = open_ms + 60 * MINUTE_MS
    full = list(range(open_ms, close_ms, MINUTE_MS))
    assert len(full) == 60

    for holes in ([5], [5, 6, 7], [0], [59], [3, 17, 42, 58]):
        punched = [t for i, t in enumerate(full) if i not in set(holes)]
        flagged, count = _missing_1m_bars(punched, open_ms, close_ms)
        assert flagged is True, holes
        assert count == len(holes), (holes, count)

    # The count is the COUNT OF MISSING BARS, not a boolean in disguise.
    one = _missing_1m_bars([t for i, t in enumerate(full) if i != 5],
                           open_ms, close_ms)
    many = _missing_1m_bars([t for i, t in enumerate(full) if i not in (5, 6, 7)],
                            open_ms, close_ms)
    assert one[1] == 1 and many[1] == 3
    assert many[1] > one[1]


def test_E8_a_COMPLETE_synthetic_1m_series_leaves_the_flag_clear():
    """THE IN-SAMPLE CASE. Report 19's layer is exactly full, so this is the
    branch every real 2022-2024 position will take: flag clear, count zero."""
    open_ms = 1_700_000_000_000
    close_ms = open_ms + 24 * 60 * MINUTE_MS
    full = list(range(open_ms, close_ms, MINUTE_MS))
    assert len(full) == 1_440

    flagged, count = _missing_1m_bars(full, open_ms, close_ms)
    assert flagged is False
    assert count == 0

    # AND THE ZERO IS REPORTED, NOT OMITTED. Report 28 §6.2's rule: a branch
    # that is never reported is a branch nobody can tell was checked.
    assert count == 0 and isinstance(count, int)


def test_E8_holes_OUTSIDE_the_open_interval_do_not_flag_the_position():
    """THE RULE IS ABOUT THE POSITION'S OWN OPEN INTERVAL.

    A hole before entry or after exit is not this position's exposure, and a
    flag that fired on it would make the flagged fraction a property of the
    dataset rather than of the trade.
    """
    open_ms = 1_700_000_000_000
    close_ms = open_ms + 60 * MINUTE_MS
    inside = list(range(open_ms, close_ms, MINUTE_MS))

    before = list(range(open_ms - 30 * MINUTE_MS, open_ms, MINUTE_MS))
    after = list(range(close_ms, close_ms + 30 * MINUTE_MS, MINUTE_MS))

    # Series complete inside the interval, punched outside it.
    punched_outside = ([t for i, t in enumerate(before) if i != 3]
                       + inside
                       + [t for i, t in enumerate(after) if i != 4])
    flagged, count = _missing_1m_bars(punched_outside, open_ms, close_ms)
    assert flagged is False
    assert count == 0

    # And a single hole INSIDE flags, so the interval bound is load-bearing.
    flagged, count = _missing_1m_bars(
        [t for t in punched_outside if t != inside[10]], open_ms, close_ms)
    assert flagged is True
    assert count == 1


def test_E8_is_inert_in_sample_and_the_constant_says_so():
    """THE CONSTANT IS A STATEMENT ABOUT THE MEASUREMENT WINDOW ONLY.

    Report 19's per-symbol figures reproduce the pooled total exactly, and the
    document cites them rather than re-measuring: no 1m bar is read here.
    """
    assert es.MISSING_BAR_INERT_IN_SAMPLE is True
    assert es.MISSING_BAR_RULE == "flag_and_count"
    assert 525_600 + 525_600 + 527_040 == 1_578_240
    assert 1_096 * 1_440 == 1_578_240


def test_the_amendment_states_the_out_of_sample_status_of_E8(amendment):
    """E8 IS THE ONE CONVENTION WHOSE FIRST REAL EXERCISE MAY BE OUT OF SAMPLE,
    and the amendment must say so rather than leave it to be noticed."""
    flat = _flat(amendment).lower()
    assert "first real exercise may occur out of sample" in flat
    assert "cannot be examined without opening the seal" in flat
    for token in ("REPORT THE FLAGGED FRACTION EVEN WHEN IT IS ZERO",
                  "MUST REPORT IT SEPARATELY"):
        assert token.lower() in flat, token


# ---------------------------------------------------------------------------
# A5. THE CARVE-OUT, AND THE FIREWALL AFTER THE AMENDMENT.
# ---------------------------------------------------------------------------

def test_the_carve_out_is_EXACTLY_ONE_NAMED_FUNCTION_in_this_module():
    """REPORT 28 §4.1's SECOND CONDITION, ASSERTED OVER THE AST.

    A firewall with an undocumented exception is a firewall nobody can audit.
    The carve-out is one function, it is named in the amendment's §9, and it is
    not widened here: it delegates to report 28's own carve-out and subtracts
    one term.
    """
    tree = ast.parse(open(__file__).read())
    proceeds = [n.name for n in ast.walk(tree)
                if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
                and "proceeds" in n.name]
    assert proceeds == ["net_proceeds_per_unit_with_funding"], proceeds

    # AND THE SPECIFICATION MODULE HAS NO FUNCTIONS AT ALL, so it cannot hold a
    # second copy of the arithmetic.
    assert [n.name for n in ast.walk(_module_ast())
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))] == []


def test_the_carve_out_is_reachable_from_no_source_file():
    """SYNTHETIC REFERENCE INPUTS ONLY -- enforced by unreachability.

    Nothing under `src/` names this function, so no module code path can call
    it on a real signal, a real bar or a real position. Only the tests do, on
    hand-chosen values.
    """
    for base, _, files in os.walk(os.path.join(ROOT, "src")):
        for name in files:
            if not name.endswith(".py"):
                continue
            text = open(os.path.join(base, name)).read()
            assert "net_proceeds_per_unit_with_funding" not in text, name


def test_the_amended_module_still_imports_nothing_at_all():
    """THE IMPORT-GRAPH ASSERTION, RE-RUN AFTER THE AMENDMENT'S CONSTANTS.

    THE 1m SEAL GAP IS STILL OPEN. A module with no imports cannot reach the 1m
    loader, cannot reach a bar, and cannot acquire a dependency without someone
    editing this assertion.
    """
    assert _imports() == set(), _imports()
    banned = ("src.timeframe", "src.folds", "src.analysis", "src.engine",
              "src.sweep", "src.regime", "pandas", "numpy", "pyarrow")
    for mod in _imports():
        for bad in banned:
            assert not (mod == bad or mod.startswith(bad + ".")), mod


def test_the_amendment_constants_carry_no_performance_name():
    """THE TWELVE-NAME GUARD, ARMED AND UNCONDITIONAL AFTER THE AMENDMENT.

    A GUARD FIRED WHILE THIS AMENDMENT WAS BEING WRITTEN AND IT FIRED CORRECTLY:
    the first constant was to be named `FUNDING_PNL_TREATMENT`, which contains
    the bare token this list bans. THE NAME WAS CHANGED, NOT THE GUARD -- adding
    an exemption would have passed the suite and quietly turned an unconditional
    assertion into one with a carve-out, which is the move report 28 §11.1
    refused for the same reason.
    """
    names = ("FUNDING_REALISED_TREATMENT", "FUNDING_IN_TARGET_SOLVE",
             "MISSING_BAR_INERT_IN_SAMPLE")
    for name in names:
        assert hasattr(es, name), name
        for word in PERFORMANCE_NAMES:
            assert word not in name.lower(), (name, word)
            assert word not in str(getattr(es, name)).lower(), (name, word)

    # The rejected name is not present anywhere in the module, under any guard.
    assert "FUNDING_PNL_TREATMENT" not in open(es.__file__).read()

    # And the guard itself is not relaxed: the banned token is still banned.
    assert "pnl" in PERFORMANCE_NAMES
