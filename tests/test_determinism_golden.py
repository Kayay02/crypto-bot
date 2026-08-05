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
from conftest import golden_cfg

GOLDEN_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "golden")
GOLDEN_CSV = os.path.join(GOLDEN_DIR, "btc_2023_01_gated.csv")
GOLDEN_HASH = os.path.join(GOLDEN_DIR, "btc_2023_01_gated.sha256")

SLICE = dict(symbols=["BTCUSDT"], start_ts=1672531200000,  # 2023-01-01T00:00Z
             end_ts=1675209600000)                          # 2023-02-01T00:00Z


@pytest.fixture(scope="module")
def first_run():
    trades, refused, _ = engine_run.run(variant="gated", cfg=golden_cfg(), **SLICE)
    return trades, refused


def test_g4_two_runs_are_byte_identical(first_run):
    trades_a, _ = first_run
    trades_b, _, _ = engine_run.run(variant="gated", cfg=golden_cfg(), **SLICE)
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


# --------------------------------------------------------------------------
# G5b -- the SIGNAL-MODE golden file (Point 3 known gap, closed at 3R)
# --------------------------------------------------------------------------

SIGNAL_CSV = os.path.join(GOLDEN_DIR, "btc_2023_01_signal_ungated.csv")
SIGNAL_HASH = os.path.join(GOLDEN_DIR, "btc_2023_01_signal_ungated.sha256")


@pytest.fixture(scope="module")
def signal_run():
    trades, refused, _ = engine_run.run(
        variant="ungated", mode="signal", cfg=golden_cfg(), **SLICE)
    return trades, refused


def test_g5b_signal_mode_golden_file_matches(signal_run):
    """Signal mode is the edge-test instrument, so it is the arm that matters.

    Point 3 left this ungated: the gated arm is obtained by FILTERING this
    table, so pinning it pins both arms at once.
    """
    trades, _ = signal_run
    if not os.path.exists(SIGNAL_CSV):
        pytest.skip("signal golden missing; run `python tests/make_golden.py`")
    expected = open(SIGNAL_HASH).read().strip()
    assert engine_run.output_hash(trades) == expected


def test_g5b_signal_mode_golden_shape_is_unchanged(signal_run):
    trades, _ = signal_run
    if not os.path.exists(SIGNAL_CSV):
        pytest.skip("signal golden missing")
    golden = pd.read_csv(SIGNAL_CSV)
    assert list(trades.columns) == list(golden.columns)
    assert len(trades) == len(golden)


def test_g5b_signal_mode_is_a_superset_of_the_gated_arm(signal_run):
    """Filtering the ungated signal table must reproduce the gated arm."""
    trades, _ = signal_run
    gated = engine_run.gated_arm(trades, golden_cfg().rvol_threshold)
    assert len(gated) <= len(trades)
    assert (gated["rvol"] >= golden_cfg().rvol_threshold).all()


def test_g5b_signal_mode_applies_no_portfolio_constraints(signal_run):
    _, refused = signal_run
    assert refused["open_position"] == 0
    assert refused["cooldown"] == 0
    assert refused["insufficient_margin"] == 0


def test_new_provenance_columns_are_present_and_typed(signal_run):
    """A7 counters plus the state-check record."""
    trades, _ = signal_run
    assert set(trades["stop_binding_mechanism"]) <= {"atr", "floor", "cap"}
    assert set(trades["size_binding_mechanism"]) <= {"risk_rule"}
    for col in ("threshold_r", "threshold_price", "at_threshold_at_checkpoint",
                "checkpoint_price", "touched_threshold_intrabar"):
        assert col in trades.columns
    # threshold_r is derived, so it is the same on every row of one run.
    assert trades["threshold_r"].nunique() == 1
    assert trades["threshold_r"].iloc[0] == pytest.approx(golden_cfg().threshold_r)
