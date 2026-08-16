"""Guards for the Bitget venue-constraint retrieval and its parser.

THE MOST DANGEROUS FAILURE HERE IS A PARSER THAT RETURNS NOTHING. A tier table
that parses to an empty list, or a contract spec whose fields all default,
produces a report stating that the venue imposes no constraint the project could
breach -- which is both the most reassuring possible answer and the one most
likely to be wrong. Every parse path therefore RAISES on absence rather than
defaulting, and the negative controls below feed it a truncated response and a
field-renamed response and assert it raises on both.

NO NETWORK IS TOUCHED BY ANY TEST. Everything reads the committed snapshot under
`data/reference/bitget_venue/`. A test suite that re-fetched would be measuring the
venue's mood on the day it ran, and would fail offline for reasons that have
nothing to do with the code.

NO MARKET DATA, ASSERTED STRUCTURALLY. The module is walked for imports and must
not reach `src/timeframe`, `src/folds`, `src/analysis` or the engine's
simulation path. That is a stronger statement than "it does not read bars",
because it cannot become false by accident.
"""

import ast
import copy
import json
import os

import pytest

from src.venue import bitget_constraints as vc


SNAPSHOT_DIR = vc.SNAPSHOT_DIR
SYMBOLS = vc.SYMBOLS


# ---------------------------------------------------------------------------
# Fixtures. The committed snapshot, read from disk exactly as the report reads it.
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def manifest():
    return vc.load_manifest()


@pytest.fixture(scope="module")
def parsed():
    return vc.parse_snapshot()


def _raw_text(name):
    with open(os.path.join(SNAPSHOT_DIR, name), "rb") as fh:
        return fh.read().decode("utf-8")


def _contract_body(symbol):
    return vc.load_raw(vc.snapshot_name(vc.CONTRACTS_PATH, symbol))


def _tier_body(symbol):
    return vc.load_raw(vc.snapshot_name(vc.POSITION_TIER_PATH, symbol))


# ---------------------------------------------------------------------------
# 1. The snapshot exists, is complete, and hashes to what the manifest claims.
# ---------------------------------------------------------------------------

def test_every_endpoint_and_symbol_is_in_the_snapshot(manifest):
    assert manifest["base_url"] == "https://api.bitget.com"
    assert manifest["product_type"] == "USDT-FUTURES"
    assert list(manifest["symbols"]) == list(SYMBOLS)

    seen = {(c["endpoint_path"], c["params"]["symbol"])
            for c in manifest["calls"]}
    expected = {(p, s) for p in (vc.CONTRACTS_PATH, vc.POSITION_TIER_PATH)
                for s in SYMBOLS}
    assert seen == expected, "one file per endpoint per symbol, no more, no less"

    for call in manifest["calls"]:
        assert call["http_status"] == 200
        assert call["params"]["productType"] == "USDT-FUTURES"
        assert call["request_url"].startswith("https://api.bitget.com/api/v2/")
        assert call["doc_url"].startswith("https://www.bitget.com/api-doc/")
        assert "no key" in call["auth"], "both endpoints must be public"


def test_the_recorded_sha256_matches_the_file_on_disk(manifest):
    """THE SNAPSHOT IS THE ARTIFACT AND THE HASH IS WHAT PROVES IT.

    If a raw file were edited after retrieval -- to tidy it, to fix a value that
    looked wrong -- every parsed table would still be internally consistent and
    the report would describe something the venue never sent.
    """
    for call in manifest["calls"]:
        path = os.path.join(SNAPSHOT_DIR, call["snapshot_file"])
        assert os.path.exists(path), path
        assert vc.sha256_of(path) == call["sha256"], call["snapshot_file"]
        assert os.path.getsize(path) == call["bytes"]


def test_raw_files_are_verbatim_bodies_not_reserialised(manifest):
    """A re-serialised dict would round-trip but would not be what was sent.

    Bitget's response is compact JSON with `": "` separators and no trailing
    newline. `json.dumps(indent=2)` of the same object is a different byte
    string, so this catches a snapshot that was pretty-printed on the way out.
    """
    for call in manifest["calls"]:
        text = _raw_text(call["snapshot_file"])
        assert not text.endswith("\n"), "no newline may be appended"
        assert text.startswith('{"code":'), text[:40]
        assert "\n" not in text, "the venue sends one line; indentation is ours"


# ---------------------------------------------------------------------------
# 2. Schema assertions -- every field the report depends on.
# ---------------------------------------------------------------------------

def test_contract_specs_parse_with_every_required_field(parsed):
    for symbol in SYMBOLS:
        spec = parsed["contracts"][symbol]
        assert spec["symbol"] == symbol
        for field in ("qty_step", "min_trade_qty", "min_trade_usdt",
                      "tick_size", "max_order_qty", "max_market_order_qty",
                      "min_leverage", "max_leverage"):
            assert isinstance(spec[field], float)
            assert spec[field] > 0.0, (symbol, field)
        for field in ("max_orders_per_symbol", "max_orders_per_product",
                      "max_positions", "qty_decimals", "price_decimals",
                      "price_end_step", "funding_interval_hours"):
            assert isinstance(spec[field], int)
        assert spec["symbol_status"] == "normal"
        assert spec["margin_coins"] == ["USDT"]
        assert spec["funding_interval_hours"] == 8, (
            "the thesis's time exit is denominated in 8-hour settlements")


def test_the_price_tick_is_end_step_times_ten_to_the_minus_place(parsed):
    """NOT 10**-pricePlace, which coincides today only because the step is 1.

    `src/engine/contracts.py` states the same rule in its module docstring and
    the two derivations must not diverge.
    """
    for symbol in SYMBOLS:
        spec = parsed["contracts"][symbol]
        assert spec["price_end_step"] == 1
        assert spec["tick_size"] == pytest.approx(
            spec["price_end_step"] * 10.0 ** -spec["price_decimals"])
    assert parsed["contracts"]["BTCUSDT"]["tick_size"] == pytest.approx(0.1)
    assert parsed["contracts"]["ETHUSDT"]["tick_size"] == pytest.approx(0.01)
    assert parsed["contracts"]["SOLUSDT"]["tick_size"] == pytest.approx(0.001)


def test_a_missing_contract_field_raises_rather_than_defaulting():
    body = _contract_body("BTCUSDT")
    for field in vc.CONTRACT_REQUIRED:
        mutated = copy.deepcopy(body)
        del mutated["data"][0][field]
        if field == "symbol":
            # Without it the row cannot be identified at all, which is a
            # different refusal and must still be a refusal.
            with pytest.raises(vc.SchemaError, match="exactly one row"):
                vc.parse_contract(mutated, "BTCUSDT")
            continue
        with pytest.raises(vc.SchemaError, match="required field"):
            vc.parse_contract(mutated, "BTCUSDT")


def test_a_missing_tier_field_raises_rather_than_defaulting():
    body = _tier_body("BTCUSDT")
    for field in vc.TIER_REQUIRED:
        mutated = copy.deepcopy(body)
        del mutated["data"][0][field]
        with pytest.raises(vc.SchemaError, match="required field"):
            vc.parse_tiers(mutated, "BTCUSDT")


def test_non_numeric_and_non_finite_values_raise():
    body = _contract_body("ETHUSDT")
    for bad in ("", "n/a", None, "NaN", "Infinity"):
        mutated = copy.deepcopy(body)
        mutated["data"][0]["sizeMultiplier"] = bad
        with pytest.raises(vc.SchemaError):
            vc.parse_contract(mutated, "ETHUSDT")

    mutated = copy.deepcopy(body)
    mutated["data"][0]["sizeMultiplier"] = "0"
    with pytest.raises(vc.SchemaError, match="is zero"):
        vc.parse_contract(mutated, "ETHUSDT")


def test_a_non_success_code_raises_at_load():
    """A body carrying an error code must not reach the parser at all."""
    path = os.path.join(SNAPSHOT_DIR, "bad_code__probe.json")
    body = json.loads(_raw_text(vc.snapshot_name(vc.CONTRACTS_PATH, "BTCUSDT")))
    body["code"] = "40404"
    body["msg"] = "Request URL NOT FOUND"
    with open(path, "wb") as fh:
        fh.write(json.dumps(body, separators=(",", ":")).encode("utf-8"))
    try:
        with pytest.raises(vc.SchemaError, match="not success"):
            vc.load_raw("bad_code__probe.json")
    finally:
        os.remove(path)


# ---------------------------------------------------------------------------
# 3. NEGATIVE CONTROLS ON THE PARSER.
# ---------------------------------------------------------------------------

def test_negative_control_a_truncated_response_raises(tmp_path):
    """TRUNCATION. A body cut mid-object is not JSON and must not parse to {}.

    Truncated at 60% of its length, which lands inside the data array on every
    one of these files, so the failure is a genuine mid-structure cut rather
    than a missing closing brace.
    """
    for name in (vc.snapshot_name(vc.CONTRACTS_PATH, "BTCUSDT"),
                 vc.snapshot_name(vc.POSITION_TIER_PATH, "BTCUSDT")):
        text = _raw_text(name)
        cut = text[:int(len(text) * 0.6)]
        assert cut != text
        target = tmp_path / name
        target.write_bytes(cut.encode("utf-8"))
        with pytest.raises(vc.SchemaError, match="not valid JSON"):
            vc.load_raw(name, snapshot_dir=str(tmp_path))


def test_negative_control_a_renamed_field_raises():
    """RENAMING. The failure mode a schema change actually produces.

    `keepMarginRate` renamed is the dangerous one: a parser that shrugged would
    report every tier's maintenance margin rate as absent-and-defaulted, and a
    defaulted rate of zero says liquidation never happens.
    """
    tiers = _tier_body("SOLUSDT")
    renamed = copy.deepcopy(tiers)
    for row in renamed["data"]:
        row["maintMarginRate"] = row.pop("keepMarginRate")
    with pytest.raises(vc.SchemaError, match="keepMarginRate"):
        vc.parse_tiers(renamed, "SOLUSDT")

    contracts = _contract_body("SOLUSDT")
    renamed = copy.deepcopy(contracts)
    renamed["data"][0]["lotSize"] = renamed["data"][0].pop("sizeMultiplier")
    with pytest.raises(vc.SchemaError, match="sizeMultiplier"):
        vc.parse_contract(renamed, "SOLUSDT")


def test_negative_control_an_empty_tier_table_raises():
    """THE FAILURE THIS WHOLE FILE EXISTS FOR.

    Empty tiers would be reported as "the venue publishes no leverage limit",
    which is the most dangerous sentence this report could contain.
    """
    body = _tier_body("BTCUSDT")
    for empty in ([], None, {}):
        mutated = copy.deepcopy(body)
        mutated["data"] = empty
        with pytest.raises(vc.SchemaError):
            vc.parse_tiers(mutated, "BTCUSDT")

    mutated = copy.deepcopy(_contract_body("BTCUSDT"))
    mutated["data"] = []
    with pytest.raises(vc.SchemaError, match="EMPTY"):
        vc.parse_contract(mutated, "BTCUSDT")


def test_a_gap_or_inversion_in_the_tier_bands_raises():
    """A gap leaves a notional that maps to no tier; both directions refuse."""
    body = _tier_body("BTCUSDT")

    gapped = copy.deepcopy(body)
    gapped["data"][1]["startUnit"] = str(
        float(gapped["data"][1]["startUnit"]) + 1.0)
    with pytest.raises(vc.SchemaError, match="GAP"):
        vc.parse_tiers(gapped, "BTCUSDT")

    falling = copy.deepcopy(body)
    falling["data"][1]["keepMarginRate"] = "0.0001"
    with pytest.raises(vc.SchemaError, match="rate FALLS"):
        vc.parse_tiers(falling, "BTCUSDT")

    rising = copy.deepcopy(body)
    rising["data"][1]["leverage"] = "999"
    with pytest.raises(vc.SchemaError, match="leverage RISES"):
        vc.parse_tiers(rising, "BTCUSDT")

    shuffled = copy.deepcopy(body)
    shuffled["data"] = list(reversed(shuffled["data"]))
    assert [t["level"] for t in vc.parse_tiers(shuffled, "BTCUSDT")] == \
        list(range(1, len(body["data"]) + 1)), "out-of-order rows are sorted"

    missing_level = copy.deepcopy(body)
    del missing_level["data"][3]
    with pytest.raises(vc.SchemaError, match="consecutive"):
        vc.parse_tiers(missing_level, "BTCUSDT")


# ---------------------------------------------------------------------------
# 4. COVERAGE -- the range this project can actually reach.
# ---------------------------------------------------------------------------

def test_the_tier_table_covers_zero_to_thirty_thousand_with_no_gap(parsed):
    assert vc.COVERAGE_USD == 30_000.0
    for symbol in SYMBOLS:
        tiers = parsed["tiers"][symbol]
        assert vc.assert_covers(tiers) is True
        assert tiers[0]["start_usd"] == 0.0
        assert tiers[-1]["end_usd"] >= vc.COVERAGE_USD
        for lo, hi in zip(tiers, tiers[1:]):
            assert hi["start_usd"] == lo["end_usd"], (symbol, lo["level"])


def test_a_tier_table_that_stops_short_of_the_range_raises():
    body = _tier_body("SOLUSDT")
    short = vc.parse_tiers(body, "SOLUSDT")[:1]
    short[0]["end_usd"] = 1_000.0
    with pytest.raises(vc.SchemaError, match="reaches only"):
        vc.assert_covers(short)


def test_each_book_state_maps_to_exactly_one_tier(parsed):
    """Report 24 §7.1's median, P99 and maximum, each in one tier and no other."""
    assert set(vc.BOOK_STATES_USD) == {"median", "p99", "maximum"}
    assert vc.BOOK_STATES_USD["maximum"] == pytest.approx(27_045.20)
    for symbol in SYMBOLS:
        tiers = parsed["tiers"][symbol]
        for name, value in vc.BOOK_STATES_USD.items():
            hits = [t for t in tiers
                    if t["start_usd"] <= value <= t["end_usd"]]
            assert len(hits) == 1, (symbol, name, [t["level"] for t in hits])
            assert vc.tier_for(tiers, value)["level"] == hits[0]["level"]
            assert parsed["book_tiers"][symbol][name]["tier"] == hits[0]["level"]


def test_every_book_state_sits_in_tier_one_on_every_symbol(parsed):
    """The retrieved fact the report turns on. Stated as an assertion so a
    future tier change that moved a book state out of tier 1 would fail here
    rather than be absorbed into a table."""
    for symbol in SYMBOLS:
        for name in vc.BOOK_STATES_USD:
            assert parsed["book_tiers"][symbol][name]["tier"] == 1, (symbol, name)


def test_tier_lookup_boundaries_and_refusals(parsed):
    tiers = parsed["tiers"]["SOLUSDT"]
    assert vc.tier_for(tiers, 0.0)["level"] == 1
    edge = tiers[0]["end_usd"]
    assert vc.tier_for(tiers, edge)["level"] == 1, "a boundary belongs to the lower tier"
    assert vc.tier_for(tiers, edge + 0.01)["level"] == 2
    with pytest.raises(ValueError):
        vc.tier_for(tiers, -1.0)
    with pytest.raises(vc.SchemaError, match="outside the tier table"):
        vc.tier_for(tiers, tiers[-1]["end_usd"] + 1.0)


# ---------------------------------------------------------------------------
# 5. The maintenance margin arithmetic.
# ---------------------------------------------------------------------------

def test_tier_one_offset_is_zero_and_the_two_formulas_agree_inside_it(parsed):
    """The progressive change cannot move a figure that stays inside tier 1."""
    for symbol in SYMBOLS:
        tiers = parsed["tiers"][symbol]
        assert vc.tier_offset(tiers, 1) == 0.0
        for value in list(vc.BOOK_STATES_USD.values()) + [0.0, 1_000.0]:
            assert vc.maintenance_margin(tiers, value) == pytest.approx(
                vc.maintenance_margin_flat(tiers, value))
            assert vc.maintenance_margin(tiers, value) == pytest.approx(
                value * tiers[0]["maintenance_margin_rate"])


def test_the_offset_reproduces_the_progressive_sum_at_every_band_edge(parsed):
    """The derivation is CHECKED, not asserted.

    The offset is reconstructed from the bands because the endpoint does not
    publish it. It is correct only if `value * rate_k - offset_k` equals the
    slice-by-slice sum, so that identity is tested at every band edge and at a
    point inside every band.
    """
    for symbol in SYMBOLS:
        tiers = parsed["tiers"][symbol]
        for t in tiers:
            for value in (t["start_usd"] + 1.0,
                          (t["start_usd"] + t["end_usd"]) / 2.0,
                          t["end_usd"]):
                progressive = 0.0
                for band in tiers:
                    lo = max(band["start_usd"], 0.0)
                    hi = min(band["end_usd"], value)
                    if hi > lo:
                        progressive += (hi - lo) * band["maintenance_margin_rate"]
                assert vc.maintenance_margin(tiers, value) == pytest.approx(
                    progressive, rel=1e-9), (symbol, t["level"], value)


def test_the_progressive_form_is_never_harsher_than_the_flat_form(parsed):
    """The documented change reduces the requirement; it cannot raise it."""
    for symbol in SYMBOLS:
        tiers = parsed["tiers"][symbol]
        for t in tiers:
            value = (t["start_usd"] + t["end_usd"]) / 2.0
            assert vc.maintenance_margin(tiers, value) <= \
                vc.maintenance_margin_flat(tiers, value) + 1e-9
            assert vc.tier_offset(tiers, t["level"]) >= 0.0


def test_the_retrieved_maintenance_rates_are_the_ones_the_report_states(parsed):
    """The assumed "about 0.5%" is checked against what the venue publishes.

    Pinned so that a future retrieval which moved these rates would fail here
    rather than silently change the report's central argument.
    """
    assert parsed["tiers"]["BTCUSDT"][0]["maintenance_margin_rate"] == pytest.approx(0.0040)
    assert parsed["tiers"]["ETHUSDT"][0]["maintenance_margin_rate"] == pytest.approx(0.0040)
    assert parsed["tiers"]["SOLUSDT"][0]["maintenance_margin_rate"] == pytest.approx(0.0050)
    for symbol in SYMBOLS:
        assert parsed["tiers"][symbol][0]["maintenance_margin_rate"] <= 0.0050, (
            "the assumed 0.5% must be an upper bound on the tier-1 rate, or the "
            "argument built on it does not hold")


def test_tier_one_leverage_caps_are_the_ones_the_report_states(parsed):
    assert parsed["tiers"]["BTCUSDT"][0]["max_leverage"] == pytest.approx(150.0)
    assert parsed["tiers"]["ETHUSDT"][0]["max_leverage"] == pytest.approx(150.0)
    assert parsed["tiers"]["SOLUSDT"][0]["max_leverage"] == pytest.approx(100.0)
    for symbol in SYMBOLS:
        spec = parsed["contracts"][symbol]
        assert spec["max_leverage"] == parsed["tiers"][symbol][0]["max_leverage"], (
            "the contract's maxLever and tier 1's leverage must agree, or "
            "'the maximum' means two things")


# ---------------------------------------------------------------------------
# 6. CACHE CROSS-CHECK -- reported, never resolved.
# ---------------------------------------------------------------------------

def test_live_specs_are_compared_against_the_committed_cache_field_by_field(parsed):
    fields = {"qty_step", "min_trade_qty", "min_trade_usdt", "tick_size"}
    for symbol in SYMBOLS:
        rows = parsed["cache_check"][symbol]
        assert {r["field"] for r in rows} == fields
        for row in rows:
            assert row["cached"] is not None, (symbol, row["field"])
            assert row["cache_source"].startswith("cache: symbols.%s" % symbol)


def test_the_cache_and_the_venue_agree_on_every_field(parsed):
    """AGREEMENT IS THE FINDING, and it is asserted rather than assumed.

    Report 24 §2 used qty_step 0.0001 / 0.01 / 0.1 and a $5 minimum notional
    from this cache. If the live values had moved, 5.3's quantisation fix would
    be built against a stale grid. They have not.
    """
    disagreements = [(s, r) for s in SYMBOLS
                     for r in parsed["cache_check"][s] if not r["agrees"]]
    assert disagreements == [], disagreements


def test_a_planted_cache_disagreement_is_detected_not_absorbed(parsed):
    """The cross-check must have teeth, or "they agree" means nothing."""
    cache = copy.deepcopy(vc.load_cache())
    cache["symbols"]["ETHUSDT"]["order"]["qty_step"] = 0.001
    rows = vc.cross_check_cache(parsed["contracts"]["ETHUSDT"], cache=cache)
    by_field = {r["field"]: r for r in rows}
    assert by_field["qty_step"]["agrees"] is False
    assert by_field["qty_step"]["live"] == pytest.approx(0.01)
    assert by_field["qty_step"]["cached"] == pytest.approx(0.001)
    assert by_field["tick_size"]["agrees"] is True, "only the planted field moves"


def test_the_cache_tick_is_compared_against_its_CURRENT_segment(parsed):
    """SOLUSDT's tick is a schedule, not a scalar: 0.0001 before 2024-08-14 and
    0.001 after. Comparing the live tick against the FIRST segment would report
    a disagreement that is really a history."""
    cache = vc.load_cache()
    sol = cache["symbols"]["SOLUSDT"]["segments"]
    assert len(sol) == 2, "the fixture for this test is SOL's two-segment tick"
    assert float(sol[0][1]) != float(sol[-1][1])
    row = {r["field"]: r for r in parsed["cache_check"]["SOLUSDT"]}["tick_size"]
    assert row["cached"] == pytest.approx(float(sol[-1][1]))
    assert row["agrees"] is True


# ---------------------------------------------------------------------------
# 7. ROUND TRIP -- the report cannot describe what the snapshot does not hold.
# ---------------------------------------------------------------------------

def test_every_parsed_value_reconstructs_from_the_raw_file_on_disk(parsed):
    """Re-derive both tables from the file bytes, independently of the module's
    own loader, and require equality."""
    for symbol in SYMBOLS:
        raw = json.loads(_raw_text(vc.snapshot_name(vc.CONTRACTS_PATH, symbol)))
        row = [r for r in raw["data"] if r["symbol"] == symbol][0]
        spec = parsed["contracts"][symbol]
        assert float(row["sizeMultiplier"]) == spec["qty_step"]
        assert float(row["minTradeNum"]) == spec["min_trade_qty"]
        assert float(row["minTradeUSDT"]) == spec["min_trade_usdt"]
        assert float(row["maxLever"]) == spec["max_leverage"]
        assert float(row["maxOrderQty"]) == spec["max_order_qty"]
        assert int(row["maxSymbolOrderNum"]) == spec["max_orders_per_symbol"]
        assert int(row["maxProductOrderNum"]) == spec["max_orders_per_product"]
        assert int(row["maxPositionNum"]) == spec["max_positions"]

        raw = json.loads(_raw_text(vc.snapshot_name(vc.POSITION_TIER_PATH,
                                                    symbol)))
        tiers = parsed["tiers"][symbol]
        assert len(raw["data"]) == len(tiers)
        by_level = {int(r["level"]): r for r in raw["data"]}
        for t in tiers:
            r = by_level[t["level"]]
            assert float(r["startUnit"]) == t["start_usd"]
            assert float(r["endUnit"]) == t["end_usd"]
            assert float(r["leverage"]) == t["max_leverage"]
            assert float(r["keepMarginRate"]) == t["maintenance_margin_rate"]


def test_parse_snapshot_reads_disk_and_fails_without_it(tmp_path):
    with pytest.raises(vc.SchemaError, match="snapshot file missing"):
        vc.parse_snapshot(snapshot_dir=str(tmp_path))


def test_snapshot_names_are_one_file_per_endpoint_per_symbol():
    assert vc.snapshot_name(vc.CONTRACTS_PATH, "BTCUSDT") == \
        "contracts__BTCUSDT.json"
    assert vc.snapshot_name(vc.POSITION_TIER_PATH, "SOLUSDT") == \
        "query-position-lever__SOLUSDT.json"
    names = {vc.snapshot_name(p, s)
             for p in (vc.CONTRACTS_PATH, vc.POSITION_TIER_PATH)
             for s in SYMBOLS}
    assert len(names) == 6


# ---------------------------------------------------------------------------
# 8. NO MARKET DATA, NO ENGINE, NO SIMULATION -- asserted over the import graph.
# ---------------------------------------------------------------------------

def _module_ast():
    return ast.parse(open(vc.__file__).read())


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


def test_the_module_touches_no_market_data_and_no_engine():
    """Structural, not conventional. A module that cannot import the data layer
    cannot read a bar, and the holdout is then untouched by construction rather
    than by a seal test that would have nothing to guard."""
    banned = ("src.timeframe", "src.folds", "src.analysis", "src.engine",
              "src.sweep", "src.regime", "simulate", "pandas", "pyarrow",
              "numpy")
    for mod in _imports():
        for bad in banned:
            assert not (mod == bad or mod.startswith(bad + ".")), mod
    assert "config" in _imports() or "config.settings" in _imports()


def _name_blob():
    """Every identifier and non-docstring string literal in the module.

    Docstrings are excluded because they STATE what the module does not do --
    they name `holdout`, `CostConfig` and the prohibited quantities in order to
    record the prohibition -- so a raw text search would fire on the statement
    of the rule rather than on a violation of it.
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


def test_the_module_reads_no_parquet_and_no_derived_path():
    blob = _name_blob()
    for word in ("parquet", "ohlcv", "read_parquet", "load_bars", "holdout",
                 "assert_sealed", "folds.json"):
        assert word not in blob, word


def test_the_client_conventions_come_from_the_existing_settings():
    """Base URL, product type, symbols and the rate limit are the project's,
    not a second set typed here."""
    from config import settings
    assert vc.BASE_URL == settings.BASE_URL
    assert vc.PRODUCT_TYPE == settings.PRODUCT_TYPE
    assert vc.SYMBOLS == tuple(settings.SYMBOLS)
    assert vc.MIN_INTERVAL == pytest.approx(
        1.0 / settings.MAX_REQUESTS_PER_SECOND)
    assert vc.MAX_ATTEMPTS == 4 and vc.SUCCESS_CODE == "00000"
    assert 429 in vc.RETRY_HTTP


# ---------------------------------------------------------------------------
# 9. THE FIREWALL, over the module's AST. WIDENED.
# ---------------------------------------------------------------------------

from src.firewall import (PERFORMANCE_NAMES,  # noqa: E402
                          INHERITED_FROM_REPORT_24)
"""The canonical twelve-name list, defined once at `src/firewall.py`.

Previously written out in full here. Eighteen copies had drifted into two
different lists; this module now imports the one definition."""


def test_the_widened_banned_list_is_a_superset_of_report_24s():
    """The widening is asserted, so it cannot be quietly dropped later."""
    inherited = INHERITED_FROM_REPORT_24
    assert set(inherited) <= set(PERFORMANCE_NAMES)
    assert {"drawdown", "sortino", "gross_pnl"} <= set(PERFORMANCE_NAMES)


def test_no_performance_quantity_appears_in_the_module():
    """FIREWALL GUARD, over identifiers and string literals, not prose.

    The docstrings NAME the prohibited quantities in order to state the
    prohibition, so a raw grep would fire on the statement of the rule rather
    than on a violation of it. Docstrings are excluded; everything else is not.
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
    blob = " ".join(names).lower()
    for banned in PERFORMANCE_NAMES:
        assert banned not in blob, "%r used as a name in %s" % (banned,
                                                               vc.__file__)


def test_nothing_here_writes_to_config_or_to_the_engine():
    """This step chooses no parameter. It must not be able to persist one."""
    src = open(vc.__file__).read()
    assert "contracts_cache.json" in src, "the cache is READ, for cross-check"
    written = [node for node in ast.walk(_module_ast())
               if isinstance(node, ast.Call)
               and isinstance(node.func, ast.Name) and node.func.id == "open"]
    modes = set()
    for call in written:
        for arg in call.args[1:]:
            if isinstance(arg, ast.Constant):
                modes.add(arg.value)
        for kw in call.keywords:
            if kw.arg == "mode" and isinstance(kw.value, ast.Constant):
                modes.add(kw.value.value)
    assert modes <= {"rb", "wb", "w"}, modes
    # The only write targets are the snapshot directory and its manifest. The
    # engine's config object is named in a docstring, to record what this step
    # replaces, and must appear nowhere in the module's vocabulary.
    blob = _name_blob()
    assert "costconfig" not in blob
    assert "settings.py" not in blob and "engine" not in blob


# ---------------------------------------------------------------------------
# 10. The report.
# ---------------------------------------------------------------------------

def test_report_exists_and_states_the_retrieved_figures():
    path = os.path.join(vc.ROOT, "docs", "handoff",
                        "25_point_5_2_venue_constraints.md")
    assert os.path.exists(path), path
    text = open(path).read()
    for token in ("query-position-lever", "keepMarginRate", "0.40%", "0.50%",
                  "150", "one-way", "hedge", "temporal"):
        assert token in text.lower() or token in text, token
