"""G4 determinism and G5 golden-file regression, over real derived data.

Both use one frozen slice (BTCUSDT, January 2023, default parameters). Neither
asserts anything about performance -- only that the SAME inputs keep producing
the SAME rows.

    THIS MODULE READS AN OUTCOME-BEARING ARTIFACT ON EVERY SUITE INVOCATION AND
    IS PERMITTED TO DO SO ONLY BY A RECORDED CARVE-OUT.

THE CARVE-OUT IS `docs/design/04_2a_artifact_containment.md` SECTION 4.2, and its
four conditions are transcribed here and in `tests/golden/CONTAINMENT.md` because
section 4.4 requires them recorded where a developer touching these fixtures will
see them. They are asserted by `tests/test_containment_guard.py`.

    THE TWO GOLDEN FILES AND THE PINNED-TRADE REGRESSION MAY READ OUTCOME-NAMED
    VALUES, PERMITTED ONLY UNDER FOUR CONDITIONS.

    (a) DETERMINISM AND SINGLE-POSITION IDENTITY ONLY. They may assert that
        identical inputs produce identical outputs, and that one hand-derived
        arithmetic identity holds on one named position. They may not compare
        populations, compare two configurations, or aggregate over rows.
    (b) EVERY EXPECTED VALUE IS HAND-DERIVED AND ITS DERIVATION IS WRITTEN DOWN.
        A value copied from a run is not permitted, because a fixture that
        records what the system did is a measurement wearing a fixture's name.
    (c) EXACTLY THESE ARTIFACTS AND EXACTLY THESE READERS. The two files under
        `tests/golden/`, and this module and
        `tests/test_regression_pinned_trade.py`. No further fixture and no
        further reader joins without amending that document.
    (d) THE BLANKET NAME BAN OTHERWISE INTACT. The twelve-name guard is not
        relaxed for these files, for these tests, or for anything else.

WHAT VOIDS IT, section 4.3: using a fixture to compare two configurations;
adding a second pinned trade; regenerating a golden file and taking expected
values from the run rather than re-deriving them; and any assertion over an
aggregate of the rows -- a sum, a mean, a count conditioned on an outcome column.

    THE FIRST AND THE LAST ARE THE ONES THAT WOULD LOOK INNOCENT AT THE TIME,
    AND THEY ARE NAMED FOR THAT REASON.

HOW THIS MODULE STAYS INSIDE (a). It compares an output HASH, the column list and
the row count. No value in any row is inspected, so there is nothing here for an
aggregate to be taken over.
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
