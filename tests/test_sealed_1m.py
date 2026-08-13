"""Guards for the sealed 1m loader. THE SEAL IS THE DELIVERABLE, NOT THE BARS.

THE CENTRAL TEST IS `test_CENTRAL_discovery_with_a_post_read_filter_is_caught`.
It plants the exact defect this module exists to prevent -- hand a partition
root to the reader, let it discover and open every year, then filter the rows
afterwards -- and requires the on-disk audit to catch it. That mutation RETURNS
CORRECT OUTPUT. Every row is in the readable window, every column is right, and
the sealed partitions were opened and read to produce it. If the suite passes
under that mutation the seal is decorative, so the assertion that fails under it
is named in the test rather than left to be discovered.

LAYERS 1 AND 2 CANNOT CATCH IT AND THAT IS WHY LAYER 3 EXISTS. Both reason over
the loader's own list of files. A wrong list is asserted over by the same wrong
list and passes twice. Layer 3 walks the disk, subtracts the allowed set, and
requires every remainder to be sealed or a sidecar.

NO 1m BAR IS READ FOR ANY ANALYTICAL PURPOSE. The loader is exercised on
in-sample ranges to prove it returns correct BARS -- row counts, timestamp
continuity, columns and dtypes -- and no price, volume, range or distribution of
1m values is computed, printed or asserted anywhere in this module.
"""

import ast
import datetime as dt
import os
import shutil

import pytest

from src.folds import schedule as sch
from src.timeframe import resample as rs
from src.timeframe import sealed_1m as s1


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

MINUTE_MS = 60_000

#: The three symbols and the five year partitions the layer was built with.
SEALED_YEARS = (2025, 2026)


def _ms(year, month, day, hour=0, minute=0):
    return int(dt.datetime(year, month, day, hour, minute,
                           tzinfo=dt.timezone.utc).timestamp() * 1000)


def _module_ast():
    return ast.parse(open(s1.__file__).read())


def _docstrings(tree):
    found = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef,
                             ast.ClassDef)):
            doc = ast.get_docstring(node, clean=False)
            if doc is not None:
                found.add(doc)
        for stmt in getattr(node, "body", []):
            if (isinstance(stmt, ast.Expr)
                    and isinstance(stmt.value, ast.Constant)
                    and isinstance(stmt.value.value, str)):
                found.add(stmt.value.value)
    return found


def _literals():
    """Every non-docstring constant in the module."""
    tree = _module_ast()
    docs = _docstrings(tree)
    out = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            if isinstance(node.value, str) and node.value in docs:
                continue
            out.append(node.value)
    return out


@pytest.fixture(scope="module")
def inventory():
    return s1.audit()


# ---------------------------------------------------------------------------
# 1. THE BOUNDARY IS DEFINED ONCE.
# ---------------------------------------------------------------------------

def test_the_module_declares_no_boundary_of_its_own():
    """L1. TWO DEFINITIONS ARE TWO THINGS THAT CAN DRIFT APART.

    The readable years and the sealed instant are READ from
    `src.timeframe.resample`, which derives them from
    `src.folds.schedule.HOLDOUT_TEST_START`. This module assigns no constant of
    its own that could disagree, asserted over the AST rather than by reading
    the values back -- a second copy that happened to be equal today would pass
    a value check and fail the day one of them moved.
    """
    assigned = set()
    for node in ast.walk(_module_ast()):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    assigned.add(target.id)
    forbidden = {"WINDOW_START", "WINDOW_END", "ALLOWED_YEARS",
                 "HOLDOUT_TEST_START", "HOLDOUT_START_MS", "HOLDOUT_YEAR"}
    assert not (forbidden & assigned), forbidden & assigned

    # AND NO SEALED YEAR IS A VALUE ANYWHERE IN THE MODULE. Checked over the
    # AST's literals rather than the raw text: the docstring NAMES the sealed
    # window in order to state what is sealed, so a text search would fire on
    # the statement of the rule. What matters is that no executable literal
    # carries the boundary -- the module must be unable to disagree with
    # `resample` about where the seal is, not unable to mention it.
    for literal in _literals():
        for year in SEALED_YEARS:
            assert literal != year, year
            assert str(year) not in str(literal), (literal, year)


def test_the_boundary_agrees_with_the_single_definition():
    assert s1.allowed_years() == rs.ALLOWED_YEARS == (2022, 2023, 2024)
    assert s1.sealed_boundary_ms() == sch.day_start_ms(sch.HOLDOUT_TEST_START)
    assert s1.readable_bounds_ms() == rs.window_bounds_ms()
    # The readable window ends exactly where the sealed window begins.
    assert s1.readable_bounds_ms()[1] == s1.sealed_boundary_ms()
    assert rs.WINDOW_END + dt.timedelta(days=1) == sch.HOLDOUT_TEST_START


def test_the_breach_type_is_the_packages_own():
    """A caller already refusing `HoldoutBreach` cannot let this one past."""
    assert issubclass(s1.SealBreach, rs.HoldoutBreach)
    assert issubclass(s1.SealBreach, PermissionError)


# ---------------------------------------------------------------------------
# 2. LAYER 1 -- EXPLICIT ENUMERATION, NO DISCOVERY.
# ---------------------------------------------------------------------------

def test_the_module_hands_no_directory_or_glob_to_the_reader():
    """L2. THE LOAD-BEARING PROPERTY, ASSERTED STRUCTURALLY.

    A query engine handed a directory PRUNES PARTITIONS BEFORE IT READS ROWS,
    so a date predicate applied after the load opens the sealed partition and
    then filters it out of the answer. This module must never give the reader
    anything but an individual file path.

    Asserted three ways: it imports no globbing module, it calls no glob
    function, and the only argument its reader call receives is the loop
    variable of a list it built itself.
    """
    tree = _module_ast()

    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imported.add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imported.add(node.module)
    assert "glob" not in imported, "a glob is a directory handed to a reader"

    called = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                called.add(func.id)
            elif isinstance(func, ast.Attribute):
                called.add(func.attr)
    for banned in ("glob", "iglob", "read_parquet", "dataset",
                   "ParquetDataset", "read_metadata", "read_schema"):
        assert banned not in called, banned

    # The reader is called exactly once, on a single path parameter.
    readers = [n for n in ast.walk(tree)
               if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
               and n.func.attr == "read_table"]
    assert len(readers) == 1, "exactly one read site, so it can be audited"
    assert isinstance(readers[0].args[0], ast.Name), (
        "the reader takes a single named path, never an expression that could "
        "be a directory")


def test_the_enumeration_names_the_years_and_never_discovers_them(inventory):
    """L2. Sealed years exist on disk and are never named."""
    for symbol in rs.SYMBOLS:
        paths = s1.allowed_paths(symbol)
        assert paths, symbol
        years = {s1.year_in_path(p) for p in paths}
        assert years <= set(s1.allowed_years()), (symbol, years)
        for path in paths:
            for sealed in SEALED_YEARS:
                assert "year=%d" % sealed not in path, path
            assert not os.path.basename(path).startswith("_"), path

    # The sealed directories DO exist -- the seal is not maintained by absence.
    assert inventory["sealed_years_present"] == list(SEALED_YEARS)


def test_naming_a_sealed_year_raises_rather_than_being_narrowed():
    """A caller that asked for 2025 has a defect, and silence would hide it."""
    with pytest.raises(s1.SealBreach, match="sealed"):
        s1.allowed_paths("BTCUSDT", years={2024, 2025})
    with pytest.raises(s1.SealBreach):
        s1.allowed_paths("BTCUSDT", years={2026})
    # Narrowing WITHIN the allowed set is fine.
    assert len(s1.allowed_paths("BTCUSDT", years={2023})) == 1


def test_a_request_opens_only_the_partitions_it_needs():
    one_hour = s1.paths_for("BTCUSDT", _ms(2023, 6, 1), _ms(2023, 6, 1, 1))
    assert len(one_hour) == 1
    assert "year=2023" in one_hour[0]

    across = s1.paths_for("SOLUSDT", _ms(2022, 12, 31, 23), _ms(2023, 1, 1, 1))
    assert len(across) == 2
    assert {s1.year_in_path(p) for p in across} == {2022, 2023}


# ---------------------------------------------------------------------------
# 3. LAYER 2 -- THE ASSERTION ON WHAT WAS OPENED.
# ---------------------------------------------------------------------------

def test_the_opened_set_assertion_refuses_a_sealed_path():
    good = s1.allowed_paths("BTCUSDT")
    assert s1.assert_opened(good, "test") == good

    sealed = os.path.join(s1.partition_dir("BTCUSDT", 2025), "data.parquet")
    with pytest.raises(s1.SealBreach, match="sealed"):
        s1.assert_opened(good + [sealed], "test")


def test_the_opened_set_assertion_refuses_a_sidecar_and_an_unclassifiable_path():
    """L5 AND ITS COMPANION. A sidecar describes ALL partitions, sealed ones
    included; a path with no year is not evidence of safety."""
    root = os.path.join(rs.DERIVED, s1.LAYER_DIR)
    with pytest.raises(s1.SealBreach, match="sidecar"):
        s1.assert_opened(
            [os.path.join(s1.partition_dir("BTCUSDT", 2023), "_metadata")],
            "test")
    with pytest.raises(s1.SealBreach, match="unclassifiable"):
        s1.assert_opened([os.path.join(root, "data.parquet")], "test")


def test_the_seal_classifier_is_the_only_one_and_it_is_correct():
    for year in s1.allowed_years():
        assert s1.is_sealed_path("ohlcv_1m/symbol=BTCUSDT/year=%d/d.parquet"
                                 % year) is False
    for year in SEALED_YEARS:
        assert s1.is_sealed_path("ohlcv_1m/symbol=BTCUSDT/year=%d/d.parquet"
                                 % year) is True
    # A path with no year component is not a partition of this layer.
    assert s1.is_sealed_path("data/derived/ohlcv_15m/BTCUSDT.parquet") is False
    # A directory that merely contains the text is not a partition key.
    assert s1.year_in_path("data/derived/notayear=2025/x.parquet") is None


# ---------------------------------------------------------------------------
# 4. LAYER 3 -- THE INDEPENDENT ON-DISK AUDIT.
# ---------------------------------------------------------------------------

def test_the_on_disk_audit_partitions_the_tree_exhaustively(inventory):
    """L4. EVERY FILE ON DISK IS ALLOWED, SEALED, OR A SIDECAR. NO REMAINDER.

    This is the only check here that does not reason over the loader's own
    bookkeeping: the tree is walked directly and the allowed set is SUBTRACTED
    from it. A partition nobody anticipated lands in `unexplained`, which is
    exactly what layers 1 and 2 cannot see.
    """
    assert inventory["partitions"] == 15, inventory["partitions"]
    assert inventory["files_on_disk"] == 15
    assert len(inventory["allowed"]) == 9
    assert len(inventory["complement"]) == 6
    assert len(inventory["sealed"]) == 6
    assert inventory["sidecars"] == []
    assert inventory["unexplained"] == [], inventory["unexplained"]
    assert inventory["sealed_in_allowed"] == []
    assert inventory["ok"] is True

    # Allowed and complement partition the tree with no overlap.
    allowed, complement = set(inventory["allowed"]), set(inventory["complement"])
    assert not (allowed & complement)
    assert len(allowed | complement) == inventory["files_on_disk"]

    # Every complement file is sealed; no allowed file is.
    for path in inventory["complement"]:
        assert s1.is_sealed_path(path), path
    for path in inventory["allowed"]:
        assert not s1.is_sealed_path(path), path


def test_the_audit_reports_that_it_has_something_to_guard_against(inventory):
    """THE SEAL IS NOT MAINTAINED BY ABSENCE, and the audit says so."""
    assert inventory["sealed_years_present"] == [2025, 2026]
    for (symbol, year), files in inventory["inventory"].items():
        assert len(files) == 1, (symbol, year, files)
    assert s1.assert_seal_holds()["ok"] is True


def _synthetic_tree(tmp_path, years, sidecar=None):
    """A partition tree of EMPTY files. Path arithmetic only; nothing is read."""
    for symbol in ("BTCUSDT",):
        for year in years:
            directory = os.path.join(str(tmp_path), "ohlcv_1m",
                                     "symbol=%s" % symbol, "year=%d" % year)
            os.makedirs(directory, exist_ok=True)
            open(os.path.join(directory, "data.parquet"), "wb").close()
    if sidecar:
        open(os.path.join(str(tmp_path), "ohlcv_1m",
                          "symbol=BTCUSDT", "year=2023", sidecar), "wb").close()
    return str(tmp_path)


def test_the_audit_CATCHES_a_partition_nobody_anticipated(tmp_path):
    """L4's REASON FOR EXISTING, ON A SYNTHETIC TREE.

    A year the enumeration never heard of is, by this module's classifier,
    sealed -- because anything not explicitly readable is sealed, never the
    other way round. The audit puts it in the complement rather than passing it
    through, which is the direction that fails safe.
    """
    derived = _synthetic_tree(tmp_path, (2022, 2023, 2024, 2031))
    result = s1.audit(derived_dir=derived)
    assert result["partitions"] == 4
    assert len(result["allowed"]) == 3
    assert len(result["complement"]) == 1
    assert s1.year_in_path(result["complement"][0]) == 2031
    assert result["sealed"] == result["complement"]
    assert result["unexplained"] == []
    assert result["ok"] is True


def test_the_audit_flags_an_unexplained_file_and_assert_seal_holds_raises(
        tmp_path):
    derived = _synthetic_tree(tmp_path, (2022, 2023))
    stray = os.path.join(derived, "ohlcv_1m", "symbol=BTCUSDT", "year=2023",
                         "extra.txt")
    open(stray, "wb").close()
    result = s1.audit(derived_dir=derived)
    assert result["unexplained"] == [stray]
    assert result["ok"] is False
    with pytest.raises(s1.SealBreach, match="neither allowed"):
        s1.assert_seal_holds(derived_dir=derived)


# ---------------------------------------------------------------------------
# 5. L5 -- NO METADATA SIDE CHANNEL.
# ---------------------------------------------------------------------------

def test_no_dataset_level_metadata_file_exists_on_disk():
    """ESTABLISHED, NOT ASSUMED. If one appeared, the next test is what stops
    it being opened."""
    root = os.path.join(rs.DERIVED, s1.LAYER_DIR)
    found = []
    for base, _, files in os.walk(root):
        for name in files:
            if name.startswith("_"):
                found.append(os.path.join(base, name))
    assert found == [], found


def test_a_metadata_sidecar_is_EXCLUDED_from_the_enumeration(tmp_path):
    """L5. THE SUBTLEST WAY IN, ON A SYNTHETIC TREE THAT HAS ONE.

    A dataset-level `_metadata` describes ALL partitions -- row counts and
    per-column min/max statistics. MIN/MAX ON A PRICE COLUMN FOR A SEALED
    PARTITION IS HOLDOUT INFORMATION, and it arrives without a single row being
    decoded. The enumeration excludes every underscore-prefixed name at the one
    place a file name enters the list.

    `_metadata.parquet` IS IN THE FIXTURE DELIBERATELY, AND IT IS THE ONLY CASE
    THAT MAKES THE UNDERSCORE RULE LOAD-BEARING. The mutation battery found that
    removing the underscore exclusion changed nothing, because none of the three
    real sidecar names ends in `.parquet` and the suffix check alone had been
    doing the work -- the exclusion was decorative and no test could tell. A
    sidecar that survives the suffix filter is what gives it teeth, and M4 fails
    the suite only because this case is here.
    """
    for case, sidecar in enumerate(("_metadata", "_common_metadata", "_SUCCESS",
                                    "_metadata.parquet")):
        derived = _synthetic_tree(tmp_path / ("case%d" % case),
                                  (2022, 2023, 2024), sidecar=sidecar)
        paths = s1.allowed_paths("BTCUSDT", derived_dir=derived)
        assert len(paths) == 3, paths
        for path in paths:
            assert not os.path.basename(path).startswith("_"), path
        assert not any(os.path.basename(p) == sidecar for p in paths)

        # And it is classified as a sidecar by the audit, not silently allowed.
        result = s1.audit(derived_dir=derived)
        assert len(result["sidecars"]) == 1
        assert result["unexplained"] == []


def test_the_module_never_reads_a_footer():
    """`read_metadata` and `read_schema` load the footer, statistics included.

    Neither appears here. The only reader call is `read_table` with an explicit
    column list, asserted above.

    Checked over identifiers and non-docstring literals: the module's docstring
    NAMES the sidecars in order to state that they are never opened, so a raw
    text search would fire on the statement of the rule.
    """
    blob = " ".join(str(x) for x in _identifiers_and_literals()).lower()
    for banned in ("read_metadata", "read_schema", "parquetdataset",
                   "parquetfile", "_metadata", "_common_metadata"):
        assert banned not in blob, banned

    # And no sidecar name can be constructed from the module's own literals:
    # the only underscore-prefixed literal is the EXCLUSION prefix itself.
    underscored = [x for x in _literals()
                   if isinstance(x, str) and x.startswith("_")]
    assert underscored == ["_"], underscored


def test_the_manifest_check_no_longer_opens_sealed_footers():
    """THE PRE-EXISTING SIDE CHANNEL THIS STEP CLOSED (report 29 P4).

    `structural_pass.check_manifest` and `tests/test_manifest_integrity.py`
    called `pq.read_metadata` on all 26 manifest outputs, six of which are
    sealed 1m partitions. Both now classify with THIS module's predicate and
    skip them, and the skip is reported rather than silent.
    """
    from src.analysis import structural_pass as sp

    result = sp.check_manifest()
    assert len(result["sealed_skipped"]) == 6, result["sealed_skipped"]
    for rel in result["sealed_skipped"]:
        assert s1.is_sealed_path(rel), rel
        assert s1.LAYER_DIR in rel, rel
    assert result["ok"] is True


# ---------------------------------------------------------------------------
# 6. THE CENTRAL MUTATION -- discovery with a post-read filter.
# ---------------------------------------------------------------------------

def test_CENTRAL_discovery_with_a_post_read_filter_is_caught(tmp_path):
    """THE EXACT FAILURE THIS MODULE EXISTS TO PREVENT, PLANTED IN FULL.

    The defective loader hands the PARTITION ROOT to a discovery-style
    enumeration, opens every year it finds, and filters the rows to the readable
    window afterwards. ITS OUTPUT IS INDISTINGUISHABLE FROM THE CORRECT ONE --
    every returned row is in the readable window -- and it read both sealed
    partitions to produce it.

    NEITHER LAYER 1 NOR LAYER 2 CAN SEE IT. Both reason over the loader's own
    list, and the defective loader's list is internally consistent: it opened
    exactly what it meant to open. THE ON-DISK AUDIT IS WHAT CATCHES IT,
    because it derives the forbidden set from the DISK and not from the loader,
    and the defective list then contains files the audit says are sealed.

    Run on a synthetic tree of EMPTY files: the mutation is proved to select
    sealed paths without any sealed byte being decoded.
    """
    derived = _synthetic_tree(tmp_path, (2022, 2023, 2024, 2025, 2026))

    def defective_paths(symbol, derived_dir):
        """Discovery: hand it the partition root and take what is there."""
        root = os.path.join(derived_dir, "ohlcv_1m", "symbol=%s" % symbol)
        found = []
        for year_dir in sorted(os.listdir(root)):
            directory = os.path.join(root, year_dir)
            for name in sorted(os.listdir(directory)):
                found.append(os.path.join(directory, name))
        return found

    opened = defective_paths("BTCUSDT", derived)
    assert len(opened) == 5, "the mutation must reach every partition on disk"

    # LAYER 1 IS BYPASSED (the list was not built from `allowed_years`) and
    # LAYER 3 CATCHES IT: the audit's forbidden set comes from the disk.
    forbidden = set(s1.audit(derived_dir=derived)["complement"])
    caught = sorted(set(opened) & forbidden)
    assert len(caught) == 2, caught
    assert {s1.year_in_path(p) for p in caught} == {2025, 2026}

    # LAYER 2 catches it too once the list is presented to it -- which is the
    # point: the defective loader would have had to route through this call.
    with pytest.raises(s1.SealBreach, match="sealed"):
        s1.assert_opened(opened, "defective discovery loader")

    # AND THE ROW FILTER LEAVES NO TRACE. Filtering the CORRECT rows out of a
    # sealed read is what makes the defect invisible in the output, so the
    # assertion is made on the opened SET and never on the returned frame.
    survivors = [p for p in opened if not s1.is_sealed_path(p)]
    assert len(survivors) == 3, (
        "a post-read filter yields exactly the correct three partitions' worth "
        "of paths, which is why the output cannot reveal the mutation")


# ---------------------------------------------------------------------------
# 7. CORRECTNESS, ON IN-SAMPLE DATA ONLY.
# ---------------------------------------------------------------------------

def test_a_known_short_range_returns_the_expected_rows():
    """ROW COUNTS AND TIMESTAMP CONTINUITY ONLY. No price is inspected."""
    start = _ms(2023, 6, 1)
    frame = s1.load("BTCUSDT", start, start + 60 * MINUTE_MS)
    assert len(frame) == 60
    assert list(frame.columns) == list(s1.COLUMNS)
    assert frame["ts"].iloc[0] == start
    assert frame["ts"].iloc[-1] == start + 59 * MINUTE_MS
    assert frame["ts"].is_monotonic_increasing
    assert not frame["ts"].duplicated().any()
    gaps = frame["ts"].diff().dropna().unique()
    assert list(gaps) == [MINUTE_MS], gaps


def test_a_full_day_returns_1440_bars_on_every_symbol():
    start = _ms(2023, 3, 15)
    for symbol in rs.SYMBOLS:
        frame = s1.load(symbol, start, start + 1_440 * MINUTE_MS)
        assert len(frame) == 1_440, symbol
        assert not frame["ts"].duplicated().any(), symbol
        assert list(frame["ts"].diff().dropna().unique()) == [MINUTE_MS], symbol


def test_the_columns_and_dtypes_follow_the_derived_layer_convention():
    frame = s1.load("ETHUSDT", _ms(2024, 2, 1), _ms(2024, 2, 1, 0, 10))
    assert list(frame.columns) == ["ts", "high", "low", "close"]
    assert str(frame["ts"].dtype) == "int64"
    for column in ("high", "low", "close"):
        assert str(frame[column].dtype) == "float64", column
    # `open_synth` is DROPPED at the boundary (report 27 §8), and volume is not
    # carried at all (Point 3R: "No 1m volume. No 1m open").
    for forbidden in ("open", "open_synth", "volume", "quote_volume"):
        assert forbidden not in frame.columns, forbidden


def test_open_synth_is_in_the_file_and_never_in_the_answer():
    """THE DROP IS REAL, NOT VACUOUS.

    Asserted against the schema of an ALLOWED partition -- reading the schema of
    a readable file is not a side channel -- so the column is shown to exist in
    the source and to be absent from the loader's output.
    """
    import pyarrow.parquet as pq

    path = s1.allowed_paths("BTCUSDT", years={2023})[0]
    assert not s1.is_sealed_path(path)
    names = set(pq.read_schema(path).names)
    assert "open_synth" in names, "the fixture must actually carry it"
    assert "open" not in names
    frame = s1.load("BTCUSDT", _ms(2023, 6, 1), _ms(2023, 6, 1, 0, 5))
    assert "open_synth" not in frame.columns


def test_a_range_crossing_a_year_partition_boundary_is_continuous():
    """The seam between two partitions must not produce a gap or a duplicate."""
    start = _ms(2022, 12, 31, 23, 0)
    frame = s1.load("SOLUSDT", start, start + 120 * MINUTE_MS)
    assert len(frame) == 120
    assert list(frame["ts"].diff().dropna().unique()) == [MINUTE_MS]
    assert not frame["ts"].duplicated().any()
    assert frame["ts"].iloc[0] == start
    # It really did span two partitions.
    assert len(s1.paths_for("SOLUSDT", start, start + 120 * MINUTE_MS)) == 2


def test_the_largest_readable_request_ends_exactly_at_the_boundary():
    _, hi = s1.readable_bounds_ms()
    frame = s1.load("BTCUSDT", hi - 10 * MINUTE_MS, hi)
    assert len(frame) == 10
    assert frame["ts"].max() == hi - MINUTE_MS
    assert frame["ts"].max() < s1.sealed_boundary_ms()


# ---------------------------------------------------------------------------
# 8. L6 -- A REQUEST THAT MEETS THE SEAL RAISES.
# ---------------------------------------------------------------------------

def test_a_request_one_millisecond_past_the_boundary_raises():
    """AND IT DOES NOT TRUNCATE. Silent truncation would let a caller believe
    it received the full range it asked for."""
    _, hi = s1.readable_bounds_ms()
    with pytest.raises(s1.SealBreach) as excinfo:
        s1.load("BTCUSDT", hi - 10 * MINUTE_MS, hi + 1)
    message = str(excinfo.value)
    assert "SEALED" in message
    assert str(sch.HOLDOUT_TEST_START) in message
    assert "REFUSED" in message and "narrowed" in message


def test_a_request_wholly_inside_the_sealed_window_raises():
    with pytest.raises(s1.SealBreach, match="SEALED"):
        s1.load("BTCUSDT", _ms(2025, 3, 1), _ms(2025, 3, 2))
    with pytest.raises(s1.SealBreach, match="SEALED"):
        s1.load("ETHUSDT", _ms(2026, 7, 1), _ms(2026, 7, 2))


def test_a_request_before_the_readable_window_raises_too():
    lo, _ = s1.readable_bounds_ms()
    with pytest.raises(ValueError, match="precedes"):
        s1.load("BTCUSDT", lo - MINUTE_MS, lo + MINUTE_MS)


def test_an_empty_or_reversed_range_raises():
    start = _ms(2023, 6, 1)
    with pytest.raises(ValueError, match="empty or reversed"):
        s1.load("BTCUSDT", start, start)
    with pytest.raises(ValueError, match="empty or reversed"):
        s1.load("BTCUSDT", start, start - MINUTE_MS)


def test_the_seal_message_names_the_seal_rather_than_failing_obscurely():
    """A caller that meets the seal must learn WHICH rule refused it."""
    with pytest.raises(s1.SealBreach) as excinfo:
        s1.load("BTCUSDT", _ms(2024, 12, 31), _ms(2025, 1, 2))
    message = str(excinfo.value)
    for token in ("SEALED", "readable window", str(sch.HOLDOUT_TEST_START)):
        assert token in message, token


# ---------------------------------------------------------------------------
# 9. L7 -- NO ANALYTICAL CAPABILITY, AND THE FIREWALL.
# ---------------------------------------------------------------------------

def _identifiers_and_literals():
    tree = _module_ast()
    docstrings = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.FunctionDef, ast.ClassDef)):
            doc = ast.get_docstring(node, clean=False)
            if doc is not None:
                docstrings.add(doc)
        for stmt in getattr(node, "body", []):
            if (isinstance(stmt, ast.Expr)
                    and isinstance(stmt.value, ast.Constant)
                    and isinstance(stmt.value.value, str)):
                docstrings.add(stmt.value.value)
    blob = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            blob.add(node.id)
        elif isinstance(node, ast.Attribute):
            blob.add(node.attr)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef,
                               ast.ClassDef)):
            blob.add(node.name)
        elif isinstance(node, ast.Constant) and isinstance(node.value, str):
            if node.value not in docstrings:
                blob.add(node.value)
    return blob


EXIT_VOCABULARY = ("hit", "touch", "reached", "crossed", "exit_reason",
                   "was_hit", "stop", "target", "signal")


def test_the_loader_has_no_exit_vocabulary_anywhere():
    """L7. THE LOADER LOADS BARS. 5.3.4 resolves exits.

    Asserted over identifiers and non-docstring literals, and then AGAIN over
    the raw source text -- the stronger form, which holds because the module was
    written to avoid the words entirely rather than to hide them in prose.
    """
    blob = " ".join(_identifiers_and_literals()).lower()
    for banned in EXIT_VOCABULARY:
        assert banned not in blob, banned

    source = open(s1.__file__).read().lower()
    for banned in EXIT_VOCABULARY:
        assert banned not in source, (banned, "raw text")


PERFORMANCE_NAMES = ("expectancy", "win_rate", "winrate", "profit_factor",
                     "sharpe", "sortino", "net_pnl", "gross_pnl", "drawdown",
                     "r_multiple", "equity", "pnl")


def test_the_twelve_name_firewall_is_armed_over_the_loader():
    blob = " ".join(_identifiers_and_literals()).lower()
    for banned in PERFORMANCE_NAMES:
        assert banned not in blob, banned


def test_the_loader_computes_nothing():
    """No indicator, no comparison of a level, no pairing of a bar with a
    position. The public surface is enumeration, audit and load."""
    tree = _module_ast()
    functions = {n.name for n in ast.walk(tree)
                 if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
    assert functions == {
        "allowed_years", "sealed_boundary_ms", "readable_bounds_ms",
        "year_in_path", "is_sealed_path", "partition_dir", "allowed_paths",
        "years_overlapping", "_first_day", "paths_for", "assert_opened",
        "on_disk_inventory", "audit", "assert_seal_holds", "_read_one",
        "load"}, sorted(functions)

    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imported.add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imported.add(node.module)
    banned = ("numpy", "src.engine", "src.analysis", "src.sweep", "src.regime",
              "src.risk", "simulate", "costs", "signals", "contracts")
    for module in imported:
        for bad in banned:
            assert not (module == bad or module.startswith(bad + ".")), module


def test_nothing_in_the_engine_imports_the_sealed_loader_yet():
    """5.3.4 does the wiring. Nothing is wired in at this commit."""
    engine_dir = os.path.join(ROOT, "src", "engine")
    for name in sorted(os.listdir(engine_dir)):
        if name.endswith(".py"):
            text = open(os.path.join(engine_dir, name)).read()
            assert "sealed_1m" not in text, name


# ---------------------------------------------------------------------------
# 10. THE ROUTED CALLER.
# ---------------------------------------------------------------------------

def test_resample_routes_its_enumeration_through_this_module():
    """P4. NO SECOND ENUMERATION OF THE SAME TREE.

    `resample._one_minute_paths` used to build its own list with a glob per
    allowed year. It now delegates, so there is one enumeration in the
    repository and it is the one under test here.
    """
    source = open(rs.__file__).read()
    assert "import glob" not in source
    assert "glob.glob" not in source
    for symbol in rs.SYMBOLS:
        assert rs._one_minute_paths(symbol) == s1.allowed_paths(symbol), symbol


def test_the_sealed_loader_and_the_engine_loader_agree_on_the_boundary():
    """The engine's 1m loader is NOT modified by this step and does not need to
    be: its own constant is asserted equal to the single definition, so the two
    seals cannot disagree about where the window ends."""
    import sys
    sys.path.insert(0, os.path.join(ROOT, "src", "engine"))
    import simulate

    assert simulate.HOLDOUT_START_MS == s1.sealed_boundary_ms()
    assert simulate.HOLDOUT_YEAR == min(SEALED_YEARS)
    assert simulate.in_sample_years({2023, 2024, 2025, 2026}) == {2023, 2024}
    assert set(s1.allowed_years()) == simulate.in_sample_years(
        {2022, 2023, 2024, 2025})
