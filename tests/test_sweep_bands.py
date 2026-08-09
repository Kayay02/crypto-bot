"""Step 3 guards: acceptance is a TRAINING quantity, and the plateau is a CENTRE.

Every test here is either a rule from §4.3 / Appendix K.2 / K.3 stated as an
assertion, or a planted mutation proving a guard has teeth. Three vacuous
guards have been found in this project, so a guard is not accepted until it has
been shown to refuse.
"""

import copy
import json

import pytest

from src.sweep import bands as bd
from src.sweep import grid as gr
from src.sweep import sweep as sw
from src.sweep import sweep_report as srep


# ---------------------------------------------------------------------------
# fixtures -- the real step-2 artifact, read once
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def cells():
    return sw.load_cells()


@pytest.fixture(scope="module")
def grid_json():
    return gr.load_grid()


@pytest.fixture(scope="module")
def accept(cells, grid_json):
    return bd.acceptance_table(cells, grid_json)


def _cell(symbol="BTCUSDT", fold_id=1, offset=0.5, period="train",
          arm="full", population="gated_50", n=300, expectancy=0.1):
    return {"symbol": symbol, "fold_id": fold_id, "offset": offset,
            "multiplier": 3.0, "arm": arm, "population": population,
            "period": period, "direction": "both",
            "metrics": {"n": n, "expectancy_r": expectancy, "se_r": 0.06}}


# ---------------------------------------------------------------------------
# (a) ACCEPTANCE IS COMPUTED ON TRAIN, NEVER ON TEST
# ---------------------------------------------------------------------------

def test_every_acceptance_row_is_a_training_row(accept):
    assert accept, "acceptance table is empty"
    assert {r["period"] for r in accept} == {"train"}


def test_acceptance_reads_only_the_gated_50_full_arm(accept):
    assert {r["arm"] for r in accept} == {"full"}
    assert {r["population"] for r in accept} == {"gated_50"}
    assert {r["direction"] for r in accept} == {"both"}


def test_MUTATION_a_test_period_record_in_the_acceptance_path_raises():
    """THE GUARD THIS STEP RESTS ON.

    Appendix K.2 makes acceptance a training-fold quantity. If a test record
    ever reaches the extractor it must raise, not compute.
    """
    with pytest.raises(bd.TestPeriodLeak):
        bd._acceptance_metrics(_cell(period="test"))


def test_MUTATION_flipping_the_period_selector_to_test_raises(cells, grid_json,
                                                              monkeypatch):
    """The guard does not read the selector, so moving the selector fires it.

    A guard that reads the same constant as the thing it guards is vacuous.
    This proves `_acceptance_metrics` holds the literal independently.
    """
    monkeypatch.setattr(bd, "SELECT_PERIOD", "test")
    with pytest.raises(bd.TestPeriodLeak):
        bd.acceptance_table(cells, grid_json)


def test_MUTATION_a_wrong_arm_record_in_the_acceptance_path_raises():
    with pytest.raises(bd.TestPeriodLeak):
        bd._acceptance_metrics(_cell(arm="minus_rvol", population="ungated"))
    with pytest.raises(bd.TestPeriodLeak):
        bd._acceptance_metrics(_cell(population="gated_30"))


def test_acceptance_counts_match_the_stored_train_trade_tables(accept):
    """Ties the `train` LABEL to the stored data, not just to itself.

    A record could carry period='train' and hold test figures; this recomputes
    the count straight off the trade table for a sample of cells.
    """
    sample = [r for r in accept
              if r["symbol"] == "BTCUSDT" and r["fold_id"] in (1, 5)]
    assert sample
    t = srep.load_trades("BTCUSDT")
    for r in sample:
        sub = t[(t["period"] == "train") & (t["arm"] == "full")
                & (t["offset"] == r["offset"]) & (t["fold_id"] == r["fold_id"])]
        n = int(len(srep.apply_population(sub, "gated_50")))
        assert n == r["n"], (r["fold_id"], r["offset"], n, r["n"])


# ---------------------------------------------------------------------------
# (b) POPULATION LABELS AND THE REUSED STEP-2 VALIDATOR
# ---------------------------------------------------------------------------

def test_the_step_2_validator_is_reused_on_the_input(cells):
    assert sw.validate_records(cells) == len(cells)


def test_MUTATION_stripping_a_population_label_still_raises(cells):
    """The step-2 planted mutation, re-run through step 3's entry point."""
    bad = copy.deepcopy(cells[:5])
    del bad[0]["population"]
    with pytest.raises(sw.PopulationLabelError):
        bd.acceptance_table(bad, gr.load_grid())


def test_every_acceptance_row_names_its_population(accept):
    for r in accept:
        for k in ("population", "period", "direction", "arm"):
            assert r[k], f"{k} missing on {r['symbol']} fold {r['fold_id']}"
        assert r["population"] in sw.POPULATIONS


def test_kill_condition_rows_all_name_test_as_their_period():
    payload = json.load(open(bd.ARTIFACT_PATH))
    for sym, v in payload["kill_a_oos_expectancy"].items():
        for row in v["offsets"]:
            assert row["period"] == "test"
            assert row["population"] == "gated_50"
    for sym, v in payload["kill_b_gate_decorative"].items():
        for row in v["offsets"]:
            assert row["period"] == "test"


def test_MUTATION_a_train_row_reaching_a_kill_condition_raises():
    row = {"period": "train", "arm": "full", "population": "gated_50"}
    with pytest.raises(bd.TestPeriodLeak):
        bd._require_test(row, "kill condition (a)")


# ---------------------------------------------------------------------------
# (c) THE PLATEAU IS THE CENTRE, NOT THE ARGMAX
# ---------------------------------------------------------------------------

def test_band_centre_is_the_centre_not_the_argmax():
    """Constructed so the argmax is NOT the centre.

    Expectancies rise monotonically across the band, so argmax is the LAST
    point. §4.3 requires the centre and pre-commits it precisely because the
    pull toward argmax after the lift is strong.
    """
    run = [0.75, 1.00, 1.25, 1.50, 1.75]
    expectancy = {0.75: 0.01, 1.00: 0.02, 1.25: 0.03, 1.50: 0.04, 1.75: 0.99}
    argmax = max(expectancy, key=expectancy.get)
    centre = bd.band_centre(run)
    assert centre == 1.25
    assert centre != argmax


def test_band_centre_ignores_expectancy_entirely():
    """`band_centre` takes offsets only, so it CANNOT express an argmax pull."""
    assert bd.band_centre([0.5, 0.75, 1.0]) == 0.75
    assert bd.band_centre([1.0, 1.25, 1.5, 1.75, 2.0]) == 1.5


def test_selection_from_a_full_band_row_is_the_centre():
    row = {"symbol": "BTCUSDT", "fold_id": 1, "longest_run": 5,
           "runs": [{"offsets": [0.75, 1.0, 1.25, 1.5, 1.75], "width": 5,
                     "start_offset": 0.75, "end_offset": 1.75}]}
    out = bd.select_plateau(row)
    assert out["selection"] == 1.25
    assert out["band_width"] == 5
    assert (out["band_start_offset"], out["band_end_offset"]) == (0.75, 1.75)


# ---------------------------------------------------------------------------
# (d) THE EVEN-COUNT TIE-BREAK RETURNS THE HIGHER CENTRAL OFFSET (K.3)
# ---------------------------------------------------------------------------

def test_even_band_takes_the_HIGHER_central_offset():
    """Appendix K.3's worked case: a four-point band, offsets 1.50 to 2.25."""
    assert bd.band_centre([1.50, 1.75, 2.00, 2.25]) == 2.00


def test_even_band_tie_break_is_higher_not_lower_at_other_widths():
    assert bd.band_centre([0.5, 0.75, 1.0, 1.25]) == 1.0
    assert bd.band_centre([0.5, 0.75, 1.0, 1.25, 1.5, 1.75]) == 1.25


def test_the_even_tie_break_is_not_a_rounding_accident():
    """Explicitly asserts the LOWER central offset is never returned."""
    for run in ([1.50, 1.75, 2.00, 2.25], [0.5, 0.75, 1.0, 1.25],
                [0.75, 1.0, 1.25, 1.5, 1.75, 2.0]):
        lower = run[len(run) // 2 - 1]
        assert bd.band_centre(run) != lower
        assert bd.band_centre(run) == run[len(run) // 2]


# ---------------------------------------------------------------------------
# (e) A TWO-POINT RUN PRODUCES NO SELECTION
# ---------------------------------------------------------------------------

def test_a_two_point_run_produces_NO_SELECTION():
    row = {"symbol": "ETHUSDT", "fold_id": 3, "longest_run": 2,
           "runs": [{"offsets": [1.0, 1.25], "width": 2,
                     "start_offset": 1.0, "end_offset": 1.25}]}
    out = bd.select_plateau(row)
    assert out["selection"] is None
    assert "below the §4.3 minimum" in out["reason"]


def test_no_passing_points_produces_NO_SELECTION():
    row = {"symbol": "SOLUSDT", "fold_id": 7, "longest_run": 0, "runs": []}
    assert bd.select_plateau(row)["selection"] is None


def test_band_centre_refuses_a_run_below_three():
    with pytest.raises(bd.BandRuleError):
        bd.band_centre([1.0, 1.25])


def test_two_separate_two_point_runs_do_not_combine():
    """Two runs of two are not a run of four. Contiguity is a grid relation."""
    runs = bd.contiguous_runs([0.5, 0.75, 1.5, 1.75])
    assert [len(r) for r in runs] == [2, 2]
    row = {"symbol": "BTCUSDT", "fold_id": 2, "longest_run": 2,
           "runs": [{"offsets": r, "width": len(r), "start_offset": r[0],
                     "end_offset": r[-1]} for r in runs]}
    assert bd.select_plateau(row)["selection"] is None


def test_a_gap_breaks_contiguity_even_with_no_failing_point_between():
    """0.5 apart on a 0.25 grid means the point between did not pass."""
    assert [len(r) for r in bd.contiguous_runs([1.0, 1.5, 2.0])] == [1, 1, 1]
    assert [len(r) for r in bd.contiguous_runs([1.0, 1.25, 1.5])] == [3]


def test_widest_band_wins_and_a_width_tie_takes_the_higher_band():
    runs = [[0.5, 0.75, 1.0], [1.5, 1.75, 2.0]]
    row = {"symbol": "BTCUSDT", "fold_id": 1, "longest_run": 3,
           "runs": [{"offsets": r, "width": len(r), "start_offset": r[0],
                     "end_offset": r[-1]} for r in runs]}
    out = bd.select_plateau(row)
    assert out["selection"] == 1.75
    assert out["width_tie"] is True

    runs = [[0.5, 0.75, 1.0], [1.5, 1.75, 2.0, 2.25]]
    row["runs"] = [{"offsets": r, "width": len(r), "start_offset": r[0],
                    "end_offset": r[-1]} for r in runs]
    row["longest_run"] = 4
    out = bd.select_plateau(row)
    assert out["band_width"] == 4 and out["width_tie"] is False


# ---------------------------------------------------------------------------
# ACCEPTANCE CLAUSES ARE THE PRE-COMMITTED ONES, UNMOVED
# ---------------------------------------------------------------------------

def test_acceptance_threshold_is_strictly_greater_than_zero_with_no_margin():
    assert bd.ACCEPT_EXPECTANCY_FLOOR == 0.0
    assert bd.MIN_TRAIN_TRADES == 200 == sw.MIN_TRAIN_TRADES
    assert bd.MIN_BAND_POINTS == 3
    assert bd.MARGINAL_CONTRIBUTION_R == 0.05


def test_a_grid_point_at_exactly_zero_expectancy_FAILS():
    """K.2(a) says GREATER THAN zero. Zero is not greater than zero."""
    rows = bd.acceptance_table([_cell(expectancy=0.0),
                                _cell(offset=0.75, expectancy=1e-12)],
                               gr.load_grid())
    assert rows[0]["k2a_expectancy_gt_zero"] is False
    assert rows[1]["k2a_expectancy_gt_zero"] is True


def test_a_grid_point_below_200_train_trades_FAILS_regardless_of_expectancy():
    rows = bd.acceptance_table([_cell(n=199, expectancy=0.9)], gr.load_grid())
    assert rows[0]["k2b_min_200_train_trades"] is False
    assert rows[0]["passes"] is False


def test_offset_2_50_is_never_evaluated(accept):
    """§4.3: the top grid point is ineligible and was not simulated."""
    assert max(r["offset"] for r in accept) < 2.50


def test_every_evaluated_offset_is_A3_eligible(accept, grid_json):
    for r in accept:
        elig = sw.eligible_offsets(grid_json, r["symbol"], r["fold_id"])
        assert r["k2c_survives_a3"] == any(abs(r["offset"] - o) < 1e-9
                                           for o in elig)


# ---------------------------------------------------------------------------
# (f) DETERMINISM
# ---------------------------------------------------------------------------

def test_rerunning_reproduces_identical_verdicts(cells, grid_json):
    a = bd.acceptance_table(cells, grid_json)
    b = bd.acceptance_table(cells, grid_json)
    assert a == b
    sa = [bd.select_plateau(x) for x in bd.identify_bands(a)]
    sb = [bd.select_plateau(x) for x in bd.identify_bands(b)]
    assert sa == sb


def test_the_written_artifact_matches_a_fresh_build(cells):
    """The report's numbers are reproducible from the committed inputs."""
    stored = json.load(open(bd.ARTIFACT_PATH))
    fresh = bd.acceptance_table(cells, gr.load_grid())
    assert json.loads(json.dumps(stored["acceptance"],
                                 default=bd._json_default)) == \
        json.loads(json.dumps(fresh, default=bd._json_default))


# ---------------------------------------------------------------------------
# (g) THE HOLDOUT SEAL: NOTHING HERE OPENS A BAR FILE
# ---------------------------------------------------------------------------

def _analysis_source():
    """The module's CODE, excluding the report renderer.

    `render_report` embeds prose that necessarily names the later steps and
    the authorisation flag in order to describe them. Scanning it would make
    both guards below fail on their own descriptions, so the scan stops at the
    renderer -- which computes nothing and reads no data.
    """
    src = open(bd.__file__).read()
    cut = src.index("def render_report(")
    return src[:cut]


def test_step_3_never_passes_authorised_true():
    src = _analysis_source()
    assert "authorised=True" not in src
    assert "authorised" not in src, ("step 3 has no business naming the "
                                     "authorisation flag at all")


def test_no_trade_read_at_step_3_touches_the_holdout():
    """§4.2's seal, re-asserted over exactly the records step 3 reads."""
    from src.folds import schedule as sch
    cutoff = sch.day_start_ms(sch.HOLDOUT_TEST_START)
    for symbol in sw.SYMBOLS:
        t = srep.load_trades(symbol)
        assert int(t["signal_bar_ts"].max()) < cutoff
        assert int(t["entry_ts"].max()) < cutoff
        assert int(t["exit_ts"].max()) < cutoff


# ---------------------------------------------------------------------------
# STEP 3 STOPS WHERE STEP 3 STOPS
# ---------------------------------------------------------------------------

def test_step_3_performs_no_later_step():
    src = _analysis_source()
    for forbidden in ("top_5", "top5", "leave_one_out", "sensitivity_probe",
                      "collapse(", "intersect_bands"):
        assert forbidden not in src, f"step 3 must not implement {forbidden}"


# ---------------------------------------------------------------------------
# THE REPORT IS RENDERED, NOT TRANSCRIBED
# ---------------------------------------------------------------------------

def test_the_report_is_reproducible_from_the_artifact():
    """Rendering twice from the same payload gives the same bytes."""
    payload = json.load(open(bd.ARTIFACT_PATH))
    assert bd.render_report(payload) == bd.render_report(payload)


def test_the_committed_report_matches_a_render_of_the_committed_artifact():
    payload = json.load(open(bd.ARTIFACT_PATH))
    assert open(bd.REPORT_PATH).read() == bd.render_report(payload)


def test_the_pinned_start_head_is_the_step_2_report_commit():
    """The clean HEAD step 3 started from is pinned, not re-derived.

    `git_revision()` reports `-dirty` once this step has added its own module
    and tests, so the pre-start hash cannot be recovered from the tree. It is
    asserted here to be a full 40-character sha that git recognises.
    """
    import subprocess
    assert len(bd.HEAD_AT_START) == 40
    out = subprocess.run(["git", "cat-file", "-t", bd.HEAD_AT_START],
                         capture_output=True, text=True, cwd=".")
    assert out.stdout.strip() == "commit"


def test_the_report_states_the_kill_verdicts_it_computed():
    """The prose cannot drift from the artifact on the headline verdicts."""
    payload = json.load(open(bd.ARTIFACT_PATH))
    text = bd.render_report(payload)
    assert "NO SYMBOL PRODUCES A CANDIDATE FOR STEP 4" in text
    assert not any(c["produces_candidate"]
                   for c in payload["candidates"].values())
    for symbol, v in payload["kill_d_two_of_three"]["per_symbol"].items():
        assert v["qualifies"] is False


def test_supplementary_ladder_is_test_period_only():
    payload = json.load(open(bd.ARTIFACT_PATH))
    for symbol, rows in payload["supplementary_rvol_ladder"].items():
        for r in rows:
            assert r["period"] == "test"
            assert set(r["expectancy_r"]) <= {"gated_30", "gated_50",
                                              "gated_70", "ungated"}
