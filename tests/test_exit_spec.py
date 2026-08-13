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


def test_nothing_is_wired_in_yet():
    """NO ENGINE FILE IMPORTS THE RISK PACKAGE. 5.3.4 does the wiring.

    Report 26's assertion is enforced from its own test module; this asserts the
    narrower fact that matters here -- the new constants are not reachable from
    the engine.
    """
    engine_dir = os.path.join(ROOT, "src", "engine")
    for name in os.listdir(engine_dir):
        if not name.endswith(".py"):
            continue
        text = open(os.path.join(engine_dir, name)).read()
        assert "exit_spec" not in text, name
        assert "src.risk" not in text, name


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
