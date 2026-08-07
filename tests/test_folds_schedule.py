"""Fold schedule: the calendar rule, its structure, determinism, holdout seal.

The schedule is a pure function of the constants in src/folds/schedule.py. It
reads no data file, so almost everything here runs without the dataset present
-- which is the point: a fold boundary that depended on data could be a channel
for fitting, and §4.1 forbids regime labels from touching fold boundaries at
all.
"""

import datetime as dt
import json
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from src.folds import schedule as sch  # noqa: E402

D = dt.date


@pytest.fixture(scope="module")
def folds():
    return sch.build_schedule()


# ---------------------------------------------------------------------------
# (c) schedule structure
# ---------------------------------------------------------------------------

def test_exactly_nine_folds(folds):
    assert len(folds) == 9
    assert [f["fold_id"] for f in folds] == list(range(1, 10))


def test_fold_nine_test_ends_on_the_in_sample_boundary(folds):
    assert folds[-1]["test_end"] == D(2024, 12, 31)
    assert folds[-1]["test_end"] == sch.IS_END


def test_fold_one_starts_at_the_in_sample_start(folds):
    assert folds[0]["train_start"] == D(2022, 4, 1) == sch.IS_START


def test_the_full_schedule_matches_the_hand_computed_calendar(folds):
    """The rule spelled out, so a silent change to the arithmetic is caught."""
    expect = [
        (1, D(2022, 2, 15), D(2022, 4, 1), D(2022, 9, 30), D(2022, 10, 1), D(2022, 12, 31)),
        (2, D(2022, 5, 17), D(2022, 7, 1), D(2022, 12, 31), D(2023, 1, 1), D(2023, 3, 31)),
        (3, D(2022, 8, 17), D(2022, 10, 1), D(2023, 3, 31), D(2023, 4, 1), D(2023, 6, 30)),
        (4, D(2022, 11, 17), D(2023, 1, 1), D(2023, 6, 30), D(2023, 7, 1), D(2023, 9, 30)),
        (5, D(2023, 2, 15), D(2023, 4, 1), D(2023, 9, 30), D(2023, 10, 1), D(2023, 12, 31)),
        (6, D(2023, 5, 17), D(2023, 7, 1), D(2023, 12, 31), D(2024, 1, 1), D(2024, 3, 31)),
        (7, D(2023, 8, 17), D(2023, 10, 1), D(2024, 3, 31), D(2024, 4, 1), D(2024, 6, 30)),
        (8, D(2023, 11, 17), D(2024, 1, 1), D(2024, 6, 30), D(2024, 7, 1), D(2024, 9, 30)),
        (9, D(2024, 2, 16), D(2024, 4, 1), D(2024, 9, 30), D(2024, 10, 1), D(2024, 12, 31)),
    ]
    got = [(f["fold_id"], f["warmup_start"], f["train_start"], f["train_end"],
            f["test_start"], f["test_end"]) for f in folds]
    assert got == expect


def test_train_and_test_are_contiguous_within_each_fold(folds):
    for f in folds:
        assert f["test_start"] == f["train_end"] + dt.timedelta(days=1)


def test_train_and_test_never_overlap_within_a_fold(folds):
    for f in folds:
        assert f["train_start"] <= f["train_end"] < f["test_start"] <= f["test_end"]


def test_test_periods_are_contiguous_and_non_overlapping(folds):
    for a, b in zip(folds, folds[1:]):
        assert b["test_start"] == a["test_end"] + dt.timedelta(days=1), (
            "test periods must tile the in-sample span with no gap")
    spans = [(f["test_start"], f["test_end"]) for f in folds]
    for i, (s1, e1) in enumerate(spans):
        for s2, e2 in spans[i + 1:]:
            assert e1 < s2 or e2 < s1, "test periods overlap"


def test_test_periods_tile_the_in_sample_span_exactly(folds):
    assert folds[0]["test_start"] == D(2022, 10, 1)
    assert folds[-1]["test_end"] == sch.IS_END
    covered = sum((f["test_end"] - f["test_start"]).days + 1 for f in folds)
    total = (sch.IS_END - folds[0]["test_start"]).days + 1
    assert covered == total


def test_adjacent_training_windows_overlap_by_exactly_fifty_percent(folds):
    """The 50% overlap is why the nine folds are a stability probe, not nine
    independent trials. If they are ever counted as trials, the arithmetic is
    wrong -- so the overlap is pinned here."""
    for a, b in zip(folds, folds[1:]):
        assert b["train_start"] > a["train_start"]
        assert b["train_start"] <= a["train_end"]
        overlap_days = (a["train_end"] - b["train_start"]).days + 1
        a_days = (a["train_end"] - a["train_start"]).days + 1
        assert 0.49 <= overlap_days / a_days <= 0.51, (
            f"folds {a['fold_id']}/{b['fold_id']} overlap "
            f"{overlap_days}/{a_days}")
        # And structurally: the step is exactly half the train length.
        assert sch.STEP_MONTHS * 2 == sch.TRAIN_MONTHS


def test_train_length_is_six_months_and_test_three(folds):
    for f in folds:
        assert sch.add_months(f["train_start"], 6) == f["test_start"]
        assert sch.add_months(f["test_start"], 3) == f["test_end"] + dt.timedelta(days=1)


def test_every_warmup_start_is_exactly_45_days_before_its_train_start(folds):
    for f in folds:
        assert (f["train_start"] - f["warmup_start"]).days == 45 == sch.WARMUP_DAYS


def test_no_separate_buffer_before_test_start(folds):
    """Train and test are contiguous, so one buffer covers both. `fold_periods`
    must emit exactly warmup/train/test -- not a second warm-up."""
    for f in folds:
        names = [n for n, _, _ in sch.fold_periods(f)]
        assert names == ["warmup", "train", "test"]


# ---------------------------------------------------------------------------
# (f) fold 1's buffer is fully available
# ---------------------------------------------------------------------------

def test_fold_one_warmup_start_is_at_or_after_the_first_available_bar(folds):
    """§4.2 grants no truncated-first-fold exception. Assert, do not assume."""
    assert folds[0]["warmup_start"] == D(2022, 2, 15)
    assert folds[0]["warmup_start"] >= sch.DATA_START
    available = (folds[0]["train_start"] - sch.DATA_START).days
    assert available == 90 >= sch.WARMUP_DAYS


def test_fold_one_warmup_start_matches_the_real_dataset():
    """Against the actual parquet, not just the DATA_START constant."""
    import pyarrow.parquet as pq
    p = os.path.join(sch.DERIVED, "ohlcv_15m", "BTCUSDT.parquet")
    if not os.path.exists(p):
        pytest.skip("derived data not present")
    first = int(pq.read_table(p, columns=["ts"]).to_pandas()["ts"].min())
    assert sch.build_schedule()[0]["warmup_start"] >= sch.DATA_START
    assert sch.day_start_ms(sch.DATA_START) == first


def test_generation_raises_if_the_buffer_would_be_truncated():
    """A later data start must fail loudly, not silently shorten the buffer."""
    with pytest.raises(ValueError, match="truncated-first-fold"):
        sch.build_schedule(data_start=D(2022, 3, 1))


# ---------------------------------------------------------------------------
# (d) determinism, and independence from data
# ---------------------------------------------------------------------------

def test_generating_the_schedule_twice_is_identical(folds):
    assert sch.build_schedule() == sch.build_schedule() == folds


def test_schedule_payload_is_identical_apart_from_nothing():
    a = sch.schedule_payload()
    b = sch.schedule_payload()
    assert a == b


def test_schedule_does_not_read_any_data_file(monkeypatch):
    """Make every load path explode; the schedule must still build.

    This is what "the calendar rule, never the data" means operationally.
    """
    def boom(*a, **k):
        raise AssertionError("build_schedule touched a data file")
    monkeypatch.setattr(sch, "load_bars", boom)
    import pyarrow.parquet as pq
    monkeypatch.setattr(pq, "read_table", boom)
    assert len(sch.build_schedule()) == 9


def test_schedule_module_does_not_import_regime_labels():
    """§4.1: labels must never touch fold boundaries.

    Checked on the parsed IMPORT statements, not on a substring search: the
    module legitimately mentions "regime labels" in the provenance string it
    writes into folds.json, and a text search would fire on that prose while
    telling you nothing about what the code actually depends on.
    """
    import ast

    for name in ("schedule.py", "__init__.py"):
        tree = ast.parse(open(os.path.join(ROOT, "src", "folds", name)).read())
        imported = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(a.name for a in node.names)
            elif isinstance(node, ast.ImportFrom):
                base = node.module or ""
                imported.add(base)
                imported.update(f"{base}.{a.name}" for a in node.names)
        for banned in ("regime", "labels", "simulate"):
            hits = [m for m in imported if banned in m.split(".")]
            assert not hits, f"{name} imports {hits}"


def test_importing_the_schedule_does_not_pull_in_the_regime_package():
    """Runtime check: no transitive dependency either."""
    import subprocess
    code = ("import sys; import src.folds.schedule; "
            "bad=[m for m in sys.modules if m.startswith('regime') "
            "or m.startswith('src.regime') or m=='simulate']; "
            "print(','.join(sorted(bad)))")
    r = subprocess.run([sys.executable, "-c", code], cwd=ROOT,
                       capture_output=True, text=True, timeout=120)
    assert r.returncode == 0, r.stderr
    assert r.stdout.strip() == "", f"pulled in: {r.stdout.strip()}"


def test_calendar_rule_constants_are_the_pre_registered_ones():
    assert (sch.IS_START, sch.IS_END) == (D(2022, 4, 1), D(2024, 12, 31))
    assert (sch.TRAIN_MONTHS, sch.TEST_MONTHS, sch.STEP_MONTHS) == (6, 3, 3)
    assert sch.WARMUP_DAYS == 45 and sch.EXPECTED_FOLDS == 9


def test_rule_refuses_to_be_bent_to_produce_nine_folds():
    """A rule adjusted until the count comes out right is not pre-registered."""
    with pytest.raises(ValueError, match="expected 9"):
        sch.build_schedule(train_months=12)
    with pytest.raises(ValueError, match="expected 9"):
        sch.build_schedule(test_months=6)


# ---------------------------------------------------------------------------
# boundary conventions
# ---------------------------------------------------------------------------

def test_start_is_midnight_and_end_is_the_last_15m_bar():
    d = D(2023, 4, 1)
    assert sch.day_start_ms(d) % sch.DAY_MS == 0
    assert sch.day_last_bar_ms(d) - sch.day_start_ms(d) == sch.DAY_MS - sch.BAR_15M_MS
    assert sch.day_end_exclusive_ms(d) - sch.day_last_bar_ms(d) == sch.BAR_15M_MS
    ts = dt.datetime.fromtimestamp(sch.day_last_bar_ms(d) / 1000, dt.timezone.utc)
    assert (ts.hour, ts.minute) == (23, 45)


def test_add_months_handles_month_length_and_year_rollover():
    assert sch.add_months(D(2022, 10, 1), 3) == D(2023, 1, 1)
    assert sch.add_months(D(2024, 1, 31), 1) == D(2024, 2, 29)   # leap clamp
    assert sch.add_months(D(2023, 1, 31), 1) == D(2023, 2, 28)
    assert sch.add_months(D(2022, 4, 1), 0) == D(2022, 4, 1)


# ---------------------------------------------------------------------------
# (e) holdout: DEFINED, never LOADED
# ---------------------------------------------------------------------------

def test_holdout_definition_matches_the_pre_registration():
    h = sch.holdout_definition()
    assert h["warmup_start"] == D(2024, 11, 17)
    assert h["test_start"] == D(2025, 1, 1)
    assert h["test_end"] == D(2026, 7, 26)
    assert (h["test_start"] - h["warmup_start"]).days == 45


def test_holdout_has_no_train_period():
    """One candidate, one look, whole window -- selected entirely elsewhere."""
    h = sch.holdout_definition()
    assert h["train_start"] is None and h["train_end"] is None


def test_holdout_is_not_among_the_nine_folds(folds):
    for f in folds:
        assert f["test_end"] < sch.HOLDOUT_TEST_START
        assert f["test_start"] < sch.HOLDOUT_TEST_START


def test_load_bars_refuses_the_holdout_by_default():
    """THE SEAL. The default path must raise."""
    with pytest.raises(PermissionError, match="SEALED"):
        sch.load_bars("BTCUSDT", D(2025, 1, 1), D(2025, 3, 31))
    with pytest.raises(PermissionError, match="SEALED"):
        sch.load_bars("BTCUSDT", D(2024, 12, 1), D(2025, 1, 2))


def test_authorised_defaults_to_false():
    import inspect
    sig = inspect.signature(sch.load_bars)
    assert sig.parameters["authorised"].default is False
    sig2 = inspect.signature(__import__("src.folds.warmup",
                                        fromlist=["x"]).indicators_from)
    assert sig2.parameters["authorised"].default is False


def test_in_sample_ranges_are_permitted():
    """The seal must not be so broad it blocks the folds themselves."""
    assert not sch.is_holdout_range(D(2024, 10, 1), D(2024, 12, 31))
    assert sch.is_holdout_range(D(2024, 12, 1), D(2025, 1, 1))


def test_no_fold_range_would_trip_the_seal(folds):
    for f in folds:
        for _, a, b in sch.fold_periods(f):
            assert not sch.is_holdout_range(a, b)


# ---------------------------------------------------------------------------
# artifact
# ---------------------------------------------------------------------------

def test_payload_records_the_rule_the_folds_and_the_commit():
    p = sch.schedule_payload()
    assert p["git_commit"]
    assert len(p["folds"]) == 9
    r = p["calendar_rule"]
    assert (r["train_months"], r["test_months"], r["step_months"],
            r["warmup_days"]) == (6, 3, 3, 45)
    assert r["in_sample_start"] == "2022-04-01" and r["in_sample_end"] == "2024-12-31"
    assert p["holdout"]["test_start"] == "2025-01-01"
    assert p["holdout"]["train_start"] is None
    f1 = p["folds"][0]
    assert f1["warmup_start"] == "2022-02-15"
    assert f1["train_start_ms"] == sch.day_start_ms(D(2022, 4, 1))
    assert f1["test_end_ms"] == sch.day_last_bar_ms(D(2022, 12, 31))


def test_written_artifact_round_trips(tmp_path):
    path = str(tmp_path / "folds.json")
    sch.write_schedule(path=path)
    got = sch.load_schedule(path)
    assert got == sch.schedule_payload() or got["folds"] == sch.schedule_payload()["folds"]
    assert len(got["folds"]) == 9


def test_load_schedule_raises_when_missing(tmp_path):
    with pytest.raises(FileNotFoundError, match="fold schedule missing"):
        sch.load_schedule(str(tmp_path / "nope.json"))


def test_committed_artifact_is_current():
    """The tracked folds.json must match what the rule produces today."""
    if not os.path.exists(sch.FOLDS_PATH):
        pytest.skip("folds.json not generated")
    on_disk = json.load(open(sch.FOLDS_PATH))
    assert on_disk["folds"] == sch.schedule_payload()["folds"]
    assert on_disk["calendar_rule"] == sch.schedule_payload()["calendar_rule"]
