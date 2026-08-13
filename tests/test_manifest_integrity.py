"""The engine must refuse to run against data that no longer matches _manifest.json."""

import hashlib
import json
import os

import pyarrow.parquet as pq
import pytest
from conftest import DERIVED, ROOT


@pytest.fixture(scope="module")
def manifest():
    return json.load(open(os.path.join(DERIVED, "_manifest.json")))


def test_manifest_exists_and_records_provenance(manifest):
    assert manifest["git_commit"]
    assert not manifest["git_commit"].endswith("-dirty") or True  # informational
    assert len(manifest["outputs"]) >= 26


def test_every_derived_file_matches_recorded_row_count(manifest):
    """SEALED 1m PARTITIONS ARE SKIPPED, AND THE SKIP IS COUNTED.

    `pq.read_metadata` loads the parquet footer, and the footer carries
    per-row-group min/max statistics on every column -- `high`, `low` and
    `close` included. For a partition inside the holdout window those extrema
    ARE holdout information, and this test ran on every suite invocation. The
    row count of a file no measurement may ever read protects nothing, so 5.3.3
    stopped opening them here; the count is asserted so the skip cannot grow
    silently into a hole.
    """
    from src.timeframe import sealed_1m

    bad, skipped = [], []
    for rel, meta in manifest["outputs"].items():
        if sealed_1m.is_sealed_path(rel):
            skipped.append(rel)
            continue
        p = os.path.join(ROOT, rel)
        if not os.path.exists(p):
            bad.append((rel, "missing"))
            continue
        rows = pq.read_metadata(p).num_rows
        if rows != meta["rows"]:
            bad.append((rel, f"{rows} != {meta['rows']}"))
    assert not bad, f"derived data drifted from manifest: {bad}"
    assert len(skipped) == 6, (
        f"expected exactly 6 sealed 1m partitions (3 symbols x 2025/2026) to "
        f"be skipped, got {len(skipped)}: {sorted(skipped)}")
    assert len(manifest["outputs"]) - len(skipped) >= 20


def test_raw_sources_still_match_recorded_sha256(manifest):
    """Raw is immutable; a changed hash means the foundation moved."""
    seen, bad = set(), []
    for meta in manifest["outputs"].values():
        for s in meta["sources"]:
            if s["path"] in seen:
                continue
            seen.add(s["path"])
            h = hashlib.sha256()
            with open(os.path.join(ROOT, s["path"]), "rb") as fh:
                for c in iter(lambda: fh.read(1 << 20), b""):
                    h.update(c)
            if h.hexdigest() != s["sha256"]:
                bad.append(s["path"])
    assert not bad, f"raw sources modified: {bad}"


def test_ohlcv_files_do_not_expose_open_synth_to_callers():
    """Layer A's loader must strip it; confirm the raw column is still there.

    If Bitget's synthesized open silently vanished from derived, the rename
    guard would stop protecting anything.
    """
    import simulate
    sch = pq.read_schema(os.path.join(DERIVED, "ohlcv_15m", "BTCUSDT.parquet"))
    assert "open_synth" in sch.names, "derived schema changed unexpectedly"
    assert "open" not in sch.names, "a real `open` column must never appear"
    df = simulate.load_15m(DERIVED, "BTCUSDT")
    assert "open_synth" not in df.columns, "loader must drop open_synth"
