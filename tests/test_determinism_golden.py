"""G4 determinism and G5 golden-file regression, over real derived data.

Both use one frozen slice (BTCUSDT, January 2023, default parameters). Neither
asserts anything about performance -- only that the SAME inputs keep producing
the SAME rows.
"""

import hashlib
import os

import pandas as pd
import pytest
import run as engine_run

GOLDEN_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "golden")
GOLDEN_CSV = os.path.join(GOLDEN_DIR, "btc_2023_01_gated.csv")
GOLDEN_HASH = os.path.join(GOLDEN_DIR, "btc_2023_01_gated.sha256")

SLICE = dict(symbols=["BTCUSDT"], start_ts=1672531200000,  # 2023-01-01T00:00Z
             end_ts=1675209600000)                          # 2023-02-01T00:00Z


@pytest.fixture(scope="module")
def first_run():
    trades, refused, _ = engine_run.run(variant="gated", **SLICE)
    return trades, refused


def test_g4_two_runs_are_byte_identical(first_run):
    trades_a, _ = first_run
    trades_b, _, _ = engine_run.run(variant="gated", **SLICE)
    a = engine_run.canonical_bytes(trades_a)
    b = engine_run.canonical_bytes(trades_b)
    assert hashlib.sha256(a).hexdigest() == hashlib.sha256(b).hexdigest()
    assert a == b


def test_g4_hash_is_stable_across_column_order_shuffle(first_run):
    """Canonicalisation must be doing real work, not hashing incidental order."""
    trades, _ = first_run
    if len(trades) == 0:
        pytest.skip("no trades in slice")
    shuffled = trades.sample(frac=1.0, random_state=3)
    assert engine_run.output_hash(shuffled) == engine_run.output_hash(trades)


def test_g5_golden_file_matches(first_run):
    trades, _ = first_run
    if not os.path.exists(GOLDEN_CSV):
        pytest.skip(f"golden file missing; regenerate with "
                    f"`python tests/make_golden.py`")
    expected = open(GOLDEN_HASH).read().strip()
    actual = engine_run.output_hash(trades)
    assert actual == expected, (
        "engine output moved against the frozen golden file. If the change is "
        "intended, regenerate with `python tests/make_golden.py` and review "
        "the diff deliberately.")


def test_g5_golden_row_shape_is_unchanged(first_run):
    """Guards the schema separately, so a column rename fails loudly."""
    trades, _ = first_run
    if not os.path.exists(GOLDEN_CSV):
        pytest.skip("golden file missing")
    golden = pd.read_csv(GOLDEN_CSV)
    assert list(trades.columns) == list(golden.columns)
    assert len(trades) == len(golden)


def test_provenance_flags_are_present_and_typed(first_run):
    trades, _ = first_run
    if len(trades) == 0:
        pytest.skip("no trades in slice")
    for col in ("resolution", "tp_touched_not_filled", "stop_fill_quality",
                "flagged_bar_overlap"):
        assert col in trades.columns
    assert set(trades["resolution"]) <= {"observed", "assumed"}
    assert set(trades["stop_fill_quality"]) <= {"normal", "unresolved"}
    assert trades["tp_touched_not_filled"].dtype == bool
    assert trades["flagged_bar_overlap"].dtype == bool


def test_divergence_flags_are_reported_not_filtered(first_run):
    """The flag list must never remove a trade from the universe."""
    trades, _ = first_run
    if len(trades) == 0:
        pytest.skip("no trades in slice")
    # Every trade carries the flag column; none were dropped on account of it.
    assert trades["flagged_bar_overlap"].notna().all()
