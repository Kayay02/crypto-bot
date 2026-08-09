"""Guards for the cost envelope.

Every expected value here is computed independently in the test from the
formula in report 17, not copied from module output. The module is the thing
under test; it does not get to supply its own answers.

Three vacuous guards have been found in this project, so the factor-of-2 guard
at the bottom is written as a planted mutation: the test states the mutation it
is defending against and would fail if that mutation were made.
"""

import json
import math
import os

import pytest

from src.costs import envelope as ev


# ---------------------------------------------------------------------------
# Fixtures. `synthetic_fees` uses rates DELIBERATELY UNLIKE Bitget's so that a
# test passing against it cannot be passing because a real rate leaked into the
# module as a constant.
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def fees():
    return ev.load_fees()


@pytest.fixture
def synthetic_fees():
    return ev.Fees(
        maker_rate=0.00013,
        taker_rate=0.00047,
        tier="synthetic",
        product="synthetic",
        source_url="test",
        retrieved_at="2026-01-01T00:00:00+00:00",
        retrieval_method="automated",
        notes="fixture scaffolding, not a real schedule",
    )


def _artifact(**overrides):
    """A minimal well-formed artifact dict, with fields overridden or removed.

    Passing a field as `ev` (the module object) is the sentinel for "delete it";
    None is a legitimate malformed value we want to be able to inject.
    """
    base = {
        "maker_rate": 0.0002,
        "taker_rate": 0.0006,
        "tier": "base",
        "product": "USDT-M perpetual futures",
        "source_url": "https://example.invalid",
        "retrieved_at": "2026-01-01T00:00:00+00:00",
        "retrieval_method": "automated",
        "notes": "",
    }
    base.update(overrides)
    return {k: v for k, v in base.items() if v is not ev}


def _write(tmp_path, payload):
    p = tmp_path / "bitget_fees.json"
    p.write_text(json.dumps(payload))
    return str(p)


# ---------------------------------------------------------------------------
# 1. Equity independence -- the module's central claim.
# ---------------------------------------------------------------------------

def test_cost_in_r_is_independent_of_equity(synthetic_fees):
    """cost_in_r has no equity parameter, so equity cannot move it.

    Stated as a signature fact and then as a numeric fact: the dollar cost is
    recomputed by hand at two account sizes and both give the same cost in R.
    """
    import inspect
    params = set(inspect.signature(ev.cost_in_r).parameters)
    assert "equity" not in params
    assert "risk_dollars" not in params

    s, mf, slip = 0.02, 0.5, 0.0003
    got = ev.cost_in_r(s, mf, slip, synthetic_fees)

    f_eff = 0.5 * 0.00013 + 0.5 * 0.00047
    for equity in (2000.0, 200000.0):
        # Rebuild the whole chain from dollars at this account size. Both legs
        # pay a fee; only the (1 - mf) taker legs pay slippage.
        risk_dollars = 20.0
        notion = risk_dollars / s
        dollar_cost = (2.0 * f_eff + 2.0 * (1.0 - mf) * slip) * notion
        assert dollar_cost / risk_dollars == pytest.approx(got, rel=1e-12)
        # Equity only ever appears in leverage.
        assert ev.implied_leverage(s, risk_dollars, equity) == pytest.approx(
            notion / equity, rel=1e-12)


def test_cost_in_r_is_independent_of_risk_dollars_too(synthetic_fees):
    """The same cancellation removes R$, not only equity."""
    s, mf, slip = 0.015, 0.25, 0.0002
    f_eff = 0.25 * 0.00013 + 0.75 * 0.00047
    rate = 2.0 * f_eff + 2.0 * (1.0 - mf) * slip
    expected = rate / s
    assert ev.cost_in_r(s, mf, slip, synthetic_fees) == pytest.approx(expected, rel=1e-12)
    for risk_dollars in (5.0, 20.0, 5000.0):
        notion = risk_dollars / s
        assert rate * notion / risk_dollars == pytest.approx(expected, rel=1e-12)


# ---------------------------------------------------------------------------
# 2. Closed-form consistency -- round-trip the solver against the forward fn.
# ---------------------------------------------------------------------------

def test_solver_round_trips_against_forward_function(synthetic_fees):
    for tol in (0.05, 0.11, 0.2, 0.5):
        for mf in ev.MAKER_FRAC_AXIS:
            for slip in ev.SLIP_AXIS:
                s_star = ev.min_admissible_stop(tol, mf, slip, synthetic_fees)
                back = ev.cost_in_r(s_star, mf, slip, synthetic_fees)
                assert back == pytest.approx(tol, rel=1e-12, abs=1e-15)


def test_solver_round_trips_on_the_real_artifact(fees):
    for mf in ev.MAKER_FRAC_AXIS:
        for slip in ev.SLIP_AXIS:
            s_star = ev.min_admissible_stop(ev.COST_TOLERANCE_R, mf, slip, fees)
            assert ev.cost_in_r(s_star, mf, slip, fees) == pytest.approx(
                ev.COST_TOLERANCE_R, rel=1e-12)


def test_min_admissible_stop_is_the_boundary_not_merely_a_point(synthetic_fees):
    """Just inside s* must fail the tolerance; just outside must pass it."""
    tol, mf, slip = ev.COST_TOLERANCE_R, 0.5, 0.0004
    s_star = ev.min_admissible_stop(tol, mf, slip, synthetic_fees)
    assert ev.cost_in_r(s_star * 0.999, mf, slip, synthetic_fees) > tol
    assert ev.cost_in_r(s_star * 1.001, mf, slip, synthetic_fees) < tol


# ---------------------------------------------------------------------------
# 3. Monotonicity.
# ---------------------------------------------------------------------------

def test_cost_strictly_decreasing_in_s(synthetic_fees):
    prev = None
    for s in ev.S_AXIS:
        c = ev.cost_in_r(s, 0.5, 0.0003, synthetic_fees)
        if prev is not None:
            assert c < prev
        prev = c


def test_cost_strictly_increasing_in_slip(synthetic_fees):
    prev = None
    for slip in ev.SLIP_AXIS:
        c = ev.cost_in_r(0.02, 0.5, slip, synthetic_fees)
        if prev is not None:
            assert c > prev
        prev = c


def test_cost_non_increasing_in_maker_frac(synthetic_fees, fees):
    """Non-increasing, not strictly decreasing: maker == taker is admissible.

    The artifact loader already refuses maker > taker, so the weak direction is
    the only one guaranteed. Asserted on both the synthetic rates and the real
    ones, and separately shown to be STRICT whenever maker < taker.
    """
    for f in (synthetic_fees, fees):
        prev = None
        for mf in ev.MAKER_FRAC_AXIS:
            c = ev.cost_in_r(0.02, mf, 0.0003, f)
            if prev is not None:
                assert c <= prev
                if f.maker_rate < f.taker_rate:
                    assert c < prev
            prev = c

    equal = ev.Fees(0.0004, 0.0004, "t", "p", "u", "r", "automated", "n")
    costs = [ev.cost_in_r(0.02, mf, 0.0, equal) for mf in ev.MAKER_FRAC_AXIS]
    assert all(c == pytest.approx(costs[0], rel=1e-12) for c in costs)


# ---------------------------------------------------------------------------
# 4. Boundary values.
# ---------------------------------------------------------------------------

def test_maker_frac_zero_is_exactly_all_taker(synthetic_fees):
    assert ev.effective_fee_rate(0.0, synthetic_fees) == synthetic_fees.taker_rate
    s, slip = 0.018, 0.0002
    assert ev.cost_in_r(s, 0.0, slip, synthetic_fees) == pytest.approx(
        2.0 * (synthetic_fees.taker_rate + slip) / s, rel=1e-12)


def test_maker_frac_one_is_exactly_all_maker(synthetic_fees):
    """All-maker pays two fees and NO slippage -- there is no taker leg to pay it."""
    assert ev.effective_fee_rate(1.0, synthetic_fees) == synthetic_fees.maker_rate
    s, slip = 0.018, 0.0002
    assert ev.cost_in_r(s, 1.0, slip, synthetic_fees) == pytest.approx(
        2.0 * synthetic_fees.maker_rate / s, rel=1e-12)


def test_maker_frac_outside_unit_interval_is_refused(synthetic_fees):
    for bad in (-0.01, 1.01, float("nan")):
        with pytest.raises(ValueError):
            ev.cost_in_r(0.02, bad, 0.0, synthetic_fees)


def test_non_positive_stop_and_negative_slip_are_refused(synthetic_fees):
    for bad_s in (0.0, -0.01, float("inf"), float("nan")):
        with pytest.raises(ValueError):
            ev.cost_in_r(bad_s, 0.5, 0.0, synthetic_fees)
    with pytest.raises(ValueError):
        ev.cost_in_r(0.02, 0.5, -1e-6, synthetic_fees)
    with pytest.raises(ValueError):
        ev.min_admissible_stop(0.0, 0.5, 0.0, synthetic_fees)


# ---------------------------------------------------------------------------
# 5. Leverage identity.
# ---------------------------------------------------------------------------

def test_leverage_identity(synthetic_fees):
    """implied_leverage(s) * s * equity == risk_dollars, for all s."""
    for equity in (2000.0, 200000.0):
        for risk_dollars in (20.0, 250.0):
            for s in ev.S_AXIS:
                lev = ev.implied_leverage(s, risk_dollars, equity)
                assert lev * s * equity == pytest.approx(risk_dollars, rel=1e-12)


def test_notional_is_risk_over_stop(synthetic_fees):
    assert ev.notional(0.02, 20.0) == pytest.approx(1000.0, rel=1e-12)
    assert ev.implied_leverage(0.02, 20.0, 2000.0) == pytest.approx(0.5, rel=1e-12)


def test_leverage_refuses_non_positive_equity():
    with pytest.raises(ValueError):
        ev.implied_leverage(0.02, 20.0, 0.0)


# ---------------------------------------------------------------------------
# 6. Artifact contract.
# ---------------------------------------------------------------------------

def test_missing_artifact_raises(tmp_path):
    with pytest.raises(ev.FeeArtifactError, match="not found"):
        ev.load_fees(str(tmp_path / "does_not_exist.json"))


def test_unparseable_artifact_raises(tmp_path):
    p = tmp_path / "bitget_fees.json"
    p.write_text("{not json")
    with pytest.raises(ev.FeeArtifactError, match="not valid JSON"):
        ev.load_fees(str(p))


@pytest.mark.parametrize("field", ev.REQUIRED_FIELDS)
def test_each_missing_required_field_raises(tmp_path, field):
    path = _write(tmp_path, _artifact(**{field: ev}))
    with pytest.raises(ev.FeeArtifactError, match="missing required field"):
        ev.load_fees(path)


@pytest.mark.parametrize("bad", [0.0, -0.0002, float("nan"), float("inf"),
                                 "0.0002", None, True])
@pytest.mark.parametrize("field", ["maker_rate", "taker_rate"])
def test_non_finite_positive_rates_are_refused(tmp_path, field, bad):
    path = _write(tmp_path, _artifact(**{field: bad}))
    with pytest.raises(ev.FeeArtifactError):
        ev.load_fees(path)


def test_inverted_schedule_is_refused(tmp_path):
    path = _write(tmp_path, _artifact(maker_rate=0.0009, taker_rate=0.0006))
    with pytest.raises(ev.FeeArtifactError, match="maker_rate"):
        ev.load_fees(path)


def test_unknown_retrieval_method_is_refused(tmp_path):
    path = _write(tmp_path, _artifact(retrieval_method="remembered"))
    with pytest.raises(ev.FeeArtifactError, match="retrieval_method"):
        ev.load_fees(path)


def test_no_fee_literal_is_hard_coded_in_the_module():
    """A rate typed into envelope.py would make the artifact decorative.

    Scans the source for the two real Bitget rates and for any bare 0.000N
    literal outside the axis constants. The check is textual on purpose: it
    catches a constant reintroduced by a later edit, which is the failure mode
    a behavioural test cannot see because the artifact would agree with it.
    """
    src = open(ev.__file__).read()
    for forbidden in ("0.0002", "0.0006", "0.02%", "0.06%"):
        assert forbidden not in src, (
            "a fee rate literal (%s) appears in envelope.py; rates must come "
            "from the artifact only" % forbidden
        )


def test_committed_artifact_meets_the_contract(fees):
    """The artifact actually in the repo loads and carries real provenance."""
    assert 0.0 < fees.maker_rate <= fees.taker_rate < 0.01
    assert fees.retrieval_method in ("automated", "manual_operator_entry")
    assert fees.source_url.startswith("https://")
    assert "USDT-M" in fees.product
    assert fees.retrieved_at


# ---------------------------------------------------------------------------
# 7. PLANTED MUTATION -- the factor of 2.
# ---------------------------------------------------------------------------

def test_round_trip_charges_both_legs():
    """PLANTED MUTATION GUARD: `2.0 *` dropped from cost_in_r / min_admissible_stop.

    THE MUTATION. In `cost_in_r`, change

        return 2.0 * (f_eff + slip) / s      ->      return (f_eff + slip) / s

    i.e. charge one side of the round trip instead of both. This is the most
    consequential silent error available in this module: it halves every cost
    figure and doubles every admissible stop, and nothing about the resulting
    surface looks wrong.

    THE ARITHMETIC. With f_eff = 0.0006 (all taker at a 0.02/0.06 schedule),
    slip = 0.0001 and s = 0.01:

        correct : 2 * (0.0006 + 0.0001) / 0.01 = 0.14
        mutated :     (0.0006 + 0.0001) / 0.01 = 0.07

    A ratio test alone would not catch it -- halving every value leaves every
    ratio intact -- so this asserts the ABSOLUTE value, and separately asserts
    that the two-leg cost is exactly twice the one-leg cost built from the same
    parts. Confirmed to fail under the mutation before being committed.
    """
    f = ev.Fees(0.0002, 0.0006, "t", "p", "u", "r", "automated", "n")
    assert ev.cost_in_r(0.01, 0.0, 0.0001, f) == pytest.approx(0.14, rel=1e-12)
    assert ev.cost_in_r(0.01, 1.0, 0.0000, f) == pytest.approx(0.04, rel=1e-12)

    # The relation stated directly on the FEE term, which is the part the
    # factor of 2 governs: an all-taker round trip costs exactly twice a
    # one-legged one built from the same parts. Taken at slip = 0 so the
    # slippage term cannot absorb the mutation.
    s, mf = 0.02, 0.5
    one_leg_fee = ev.effective_fee_rate(mf, f) / s
    assert ev.cost_in_r(s, mf, 0.0, f) == pytest.approx(2.0 * one_leg_fee, rel=1e-12)
    assert ev.cost_in_r(s, mf, 0.0, f) != pytest.approx(one_leg_fee, rel=1e-6)

    # And the same guard on the solver, which carries its own factor of 2.
    assert ev.min_admissible_stop(0.11, 0.0, 0.0001, f) == pytest.approx(
        2.0 * 0.0007 / 0.11, rel=1e-12)
    assert ev.min_admissible_stop(0.11, 0.0, 0.0001, f) == pytest.approx(
        0.0127272727272727, rel=1e-9)


# ---------------------------------------------------------------------------
# The surface, the tolerance and the firewall.
# ---------------------------------------------------------------------------

def test_cost_tolerance_is_the_pre_committed_value():
    """0.11 is pre-registered. A test pinning it is what makes the freeze real."""
    assert ev.COST_TOLERANCE_R == 0.11


def test_axes_match_the_specified_grid():
    assert len(ev.S_AXIS) == 91
    assert ev.S_AXIS[0] == 0.005 and ev.S_AXIS[-1] == 0.05
    assert len(ev.SLIP_AXIS) == 11
    assert ev.SLIP_AXIS[0] == 0.0 and ev.SLIP_AXIS[-1] == 0.001
    assert ev.MAKER_FRAC_AXIS == (0.0, 0.25, 0.50, 0.75, 1.0)
    # Steps are exact, not accumulated-float approximations.
    for i in range(1, len(ev.S_AXIS)):
        assert ev.S_AXIS[i] - ev.S_AXIS[i - 1] == pytest.approx(0.0005, abs=1e-12)


def test_surface_shape_and_internal_consistency(fees):
    rows = ev.envelope_surface(fees)
    assert len(rows) == 91 * 5 * 11
    for r in rows:
        assert r["admissible"] == (r["cost_in_r"] <= ev.COST_TOLERANCE_R)
        # `admissible` and `min_stop` must agree to within the float boundary.
        if r["s"] > r["min_stop"] * (1 + 1e-9):
            assert r["admissible"]
        if r["s"] < r["min_stop"] * (1 - 1e-9):
            assert not r["admissible"]
        assert r["notional_usdt"] == pytest.approx(ev.RISK_DOLLARS / r["s"], rel=1e-12)


def test_slippage_spread_shrinks_with_maker_frac_and_vanishes_at_all_maker(fees):
    """REPLACES the prior invariance test, which encoded the uncorrected model.

    The first pass asserted the spread was identically 2*(slip_hi-slip_lo)/tol
    at every maker fraction, and it passed -- against a model that charged
    slippage on maker legs. Under the corrected model the spread carries a
    (1 - maker_frac) factor: it shrinks linearly and is exactly zero when there
    are no taker legs left to pay slippage.
    """
    sens = ev.slippage_sensitivity(fees)
    span = 0.001 - 0.0
    for mf, v in sens.items():
        expected = 2.0 * (1.0 - mf) * span / ev.COST_TOLERANCE_R
        assert v["spread"] == pytest.approx(expected, rel=1e-12, abs=1e-18)
    assert sens[1.0]["spread"] == pytest.approx(0.0, abs=1e-18)
    spreads = [sens[mf]["spread"] for mf in ev.MAKER_FRAC_AXIS]
    assert spreads == sorted(spreads, reverse=True)
    assert spreads[0] > spreads[-1]


# ---------------------------------------------------------------------------
# THE CORRECTED SLIPPAGE-LEG MODEL.
# ---------------------------------------------------------------------------

def test_all_maker_is_invariant_to_slippage(synthetic_fees, fees):
    """THE DEFINING PROPERTY OF THE CORRECTION.

    At maker_frac = 1.0 both legs rested at their own price. There is no taker
    leg, so there is nothing for slippage to be charged on, and cost must be
    bit-identical across the whole slip axis -- not merely close.
    """
    for f in (synthetic_fees, fees):
        for s in (0.005, 0.0102, 0.02, 0.05):
            base = ev.cost_in_r(s, 1.0, 0.0, f)
            assert ev.cost_in_r(s, 1.0, 0.0010, f) == base
            for slip in ev.SLIP_AXIS:
                assert ev.cost_in_r(s, 1.0, slip, f) == base
            assert base == pytest.approx(2.0 * f.maker_rate / s, rel=1e-12)


def test_all_taker_column_is_unchanged_by_the_correction(synthetic_fees):
    """The correction must not move the all-taker case.

    At maker_frac = 0 the (1 - maker_frac) factor is 1, so the corrected model
    and the prior one agree exactly. Asserted against the PRIOR model's formula
    written out longhand, so this is a genuine cross-check rather than a
    restatement of the new expression.
    """
    for s in (0.005, 0.0102, 0.02, 0.05):
        for slip in ev.SLIP_AXIS:
            prior_model = 2.0 * (synthetic_fees.taker_rate + slip) / s
            assert ev.cost_in_r(s, 0.0, slip, synthetic_fees) == pytest.approx(
                prior_model, rel=1e-12)
            prior_s_star = prior_model * s / ev.COST_TOLERANCE_R
            assert ev.min_admissible_stop(
                ev.COST_TOLERANCE_R, 0.0, slip, synthetic_fees) == pytest.approx(
                    prior_s_star, rel=1e-12)


def test_corrected_model_round_trips(synthetic_fees, fees):
    for f in (synthetic_fees, fees):
        for tol in (0.05, 0.11, 0.2, 0.5):
            for mf in ev.MAKER_FRAC_AXIS:
                for slip in ev.SLIP_AXIS:
                    s_star = ev.min_admissible_stop(tol, mf, slip, f)
                    assert ev.cost_in_r(s_star, mf, slip, f) == pytest.approx(
                        tol, rel=1e-12, abs=1e-15)


def test_cost_monotone_in_maker_frac_under_the_corrected_model(synthetic_fees):
    """Non-increasing at slip = 0, STRICTLY decreasing once slip > 0.

    With maker < taker the fee term already falls with maker_frac; the slippage
    term adds a second strictly-falling component whenever slip > 0.
    """
    fine = [i / 20.0 for i in range(21)]
    for slip in (0.0, 0.0001, 0.0005, 0.0010):
        prev = None
        for mf in fine:
            c = ev.cost_in_r(0.02, mf, slip, synthetic_fees)
            if prev is not None:
                assert c <= prev
                assert c < prev  # strict: maker_rate < taker_rate in the fixture
            prev = c

    equal = ev.Fees(0.0004, 0.0004, "t", "p", "u", "r", "automated", "n")
    at_zero_slip = [ev.cost_in_r(0.02, mf, 0.0, equal) for mf in fine]
    assert all(c == pytest.approx(at_zero_slip[0], rel=1e-12) for c in at_zero_slip)
    with_slip = [ev.cost_in_r(0.02, mf, 0.0005, equal) for mf in fine]
    for a, b in zip(with_slip, with_slip[1:]):
        assert b < a


# ---------------------------------------------------------------------------
# THE BREAK-EVEN INVERSE.
# ---------------------------------------------------------------------------

def test_max_tolerable_slip_round_trips(synthetic_fees, fees):
    """Where the answer is finite and positive, feeding it back yields the budget."""
    checked = 0
    for f in (synthetic_fees, fees):
        for tol in (0.08, 0.11, 0.25):
            for mf in (0.0, 0.25, 0.5, 0.75):
                for s in ev.BREAKEVEN_S_AXIS:
                    got = ev.max_tolerable_slip(s, mf, tol, f)
                    if got is None or got == ev.SLIP_UNCONSTRAINED or got <= 0.0:
                        continue
                    assert ev.cost_in_r(s, mf, got, f) == pytest.approx(
                        tol, rel=1e-12, abs=1e-15)
                    checked += 1
    assert checked > 50, "round trip exercised too few cells to mean anything"


def test_max_tolerable_slip_at_all_maker_is_unconstrained_or_none(fees):
    """maker_frac = 1.0 is its own case: the divisor vanishes.

    Below 2*f_maker/tol the stop fails on fees alone and no slippage figure can
    rescue it; at or above, slippage is not a constraint at all.
    """
    tol = ev.COST_TOLERANCE_R
    boundary = 2.0 * fees.maker_rate / tol
    assert ev.max_tolerable_slip(boundary * 1.01, 1.0, tol, fees) is ev.SLIP_UNCONSTRAINED
    assert ev.max_tolerable_slip(boundary, 1.0, tol, fees) is ev.SLIP_UNCONSTRAINED
    assert ev.max_tolerable_slip(boundary * 0.99, 1.0, tol, fees) is None
    assert math.isinf(ev.SLIP_UNCONSTRAINED)
    # Unconstrained really means unconstrained: any slip stays inside budget.
    for slip in ev.SLIP_AXIS:
        assert ev.cost_in_r(boundary * 1.01, 1.0, slip, fees) <= tol


def test_inadmissible_on_fees_alone_returns_none_not_a_negative(fees):
    """A negative break-even would format into a table and read as a bound.

    The whole point of returning None is that it fails at the point of use
    instead of being silently minimised over or compared with `<`.
    """
    tol = ev.COST_TOLERANCE_R
    for mf in ev.MAKER_FRAC_AXIS:
        # A stop far below the fee-only floor cannot be admissible at any slip.
        floor = 2.0 * ev.effective_fee_rate(mf, fees) / tol
        got = ev.max_tolerable_slip(floor * 0.5, mf, tol, fees)
        assert got is None, "expected None, got %r" % (got,)
        assert not isinstance(got, float)
        # And the claim it encodes is true: zero slippage still breaches.
        assert ev.cost_in_r(floor * 0.5, mf, 0.0, fees) > tol

    # At exactly the fee-only floor the answer is 0.0 -- a real boundary, not
    # a refusal. It must NOT be collapsed into None.
    for mf in (0.0, 0.5, 0.75):
        floor = 2.0 * ev.effective_fee_rate(mf, fees) / tol
        assert ev.max_tolerable_slip(floor, mf, tol, fees) == pytest.approx(0.0, abs=1e-15)


def test_breakeven_table_shape_and_cell_types(fees):
    t = ev.breakeven_table(fees)
    assert set(t) == set(ev.BREAKEVEN_S_AXIS)
    for s, row in t.items():
        assert set(row) == set(ev.MAKER_FRAC_AXIS)
        for mf, cell in row.items():
            assert cell is None or cell == ev.SLIP_UNCONSTRAINED or cell >= 0.0
    # Break-even slippage rises with stop width and with maker fraction.
    finite = [(s, t[s][0.5]) for s in ev.BREAKEVEN_S_AXIS if t[s][0.5] is not None]
    vals = [v for _, v in finite]
    assert vals == sorted(vals)


def test_max_tolerable_slip_rejects_bad_inputs(fees):
    for bad_s in (0.0, -0.01, float("nan")):
        with pytest.raises(ValueError):
            ev.max_tolerable_slip(bad_s, 0.5, 0.11, fees)
    with pytest.raises(ValueError):
        ev.max_tolerable_slip(0.02, 1.5, 0.11, fees)
    with pytest.raises(ValueError):
        ev.max_tolerable_slip(0.02, 0.5, 0.0, fees)


# ---------------------------------------------------------------------------
# THE UNMODELLED MAKER NON-FILL TERM.
# ---------------------------------------------------------------------------

def test_maker_nonfill_term_is_zero_and_declared_unmodelled():
    assert ev.MAKER_NONFILL_SLIP == 0.0
    doc = ev.__doc__ + (ev.nonfill_rate.__doc__ or "")
    src = open(ev.__file__).read().lower()
    # The docstring must say what it is, in terms a reader cannot skim past.
    for phrase in ("unmodelled", "understatement", "optimistic",
                   "fraction of price", "uncon"):
        assert phrase in src, "MAKER_NONFILL_SLIP docstring lost %r" % phrase
    assert doc
    # The old R-denominated name must not survive as an IDENTIFIER: a name that
    # keeps asserting the wrong unit is how the ambiguity comes back. It is
    # allowed to appear in prose, where it records what was corrected and why.
    import ast
    tree = ast.parse(open(ev.__file__).read())
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            names.add(node.id)
        elif isinstance(node, ast.Attribute):
            names.add(node.attr)
        elif isinstance(node, (ast.FunctionDef, ast.ClassDef)):
            names.add(node.name)
    assert "MAKER_NONFILL_COST_R" not in names
    assert "nonfill_cost_r" not in names
    assert "MAKER_NONFILL_SLIP" in names


def test_maker_nonfill_term_is_a_price_fraction_not_an_r_quantity(monkeypatch, fees):
    """UNIT-CONSISTENCY GUARD. Fails on the PLACEMENT, not merely on the value.

    THE AMBIGUITY THIS PINS. The term can sit in either of two places:

        price-fraction : (2*f_eff + 2*(1-mf)*slip + 2*mf*C) / s
        R-denominated  : (2*f_eff + 2*(1-mf)*slip) / s + 2*mf*C

    They differ by a factor of 1/s on that term -- 20x at s = 5%, 200x at
    s = 0.5%. At C = 0 they are numerically identical, so no ordinary test can
    tell them apart. This one raises C to a non-zero probe and pins the
    placement at TWO values of s, which is what makes it a unit test rather
    than a value test: a constant offset cannot fit both.
    """
    probe = 0.0005
    mf, slip = 0.5, 0.0002
    f_eff = ev.effective_fee_rate(mf, fees)
    shared = 2.0 * f_eff + 2.0 * (1.0 - mf) * slip

    monkeypatch.setattr(ev, "MAKER_NONFILL_SLIP", probe)
    for s in (0.005, 0.05):
        price_fraction = (shared + 2.0 * mf * probe) / s
        r_denominated = shared / s + 2.0 * mf * probe

        assert ev.cost_in_r(s, mf, slip, fees) == pytest.approx(
            price_fraction, rel=1e-12)
        assert ev.cost_in_r(s, mf, slip, fees) != pytest.approx(
            r_denominated, rel=1e-9)
        # The two candidate placements really are distinguishable here.
        assert price_fraction != pytest.approx(r_denominated, rel=1e-9)

    # THE DISCRIMINATING FACT: the gap between the two placements is itself
    # s-dependent (it is 2*mf*probe*(1/s - 1)), so it is 10x larger at
    # s = 0.005 than at s = 0.05. No single R-denominated constant can
    # reproduce the price-fraction answer at both s. Asserting the ratio is
    # what makes this a test of the DIVISION, not of the number.
    gaps = []
    for s in (0.005, 0.05):
        gaps.append(ev.cost_in_r(s, mf, slip, fees) - (shared / s + 2.0 * mf * probe))
    assert gaps[0] / gaps[1] == pytest.approx(
        (1.0 / 0.005 - 1.0) / (1.0 / 0.05 - 1.0), rel=1e-9)

    # The term must scale like slip, because it IS dimensionally slip: adding
    # `d` to MAKER_NONFILL_SLIP at all-maker must move cost by exactly the same
    # amount as adding `d` to slip does at all-taker.
    base_maker = ev.cost_in_r(0.02, 1.0, 0.0, fees)
    monkeypatch.setattr(ev, "MAKER_NONFILL_SLIP", probe * 2.0)
    bumped_maker = ev.cost_in_r(0.02, 1.0, 0.0, fees)
    monkeypatch.setattr(ev, "MAKER_NONFILL_SLIP", 0.0)
    taker_delta = (ev.cost_in_r(0.02, 0.0, probe, fees)
                   - ev.cost_in_r(0.02, 0.0, 0.0, fees))
    assert bumped_maker - base_maker == pytest.approx(taker_delta, rel=1e-12)


def test_maker_nonfill_term_is_structurally_present_in_cost_in_r(monkeypatch, fees):
    """The term must be IN the expression, not merely documented beside it.

    Its value is zero, so removing it changes no published number and no
    ordinary test would notice. This one raises the constant and requires every
    downstream figure to move by exactly the predicted amount -- so a later
    edit that deletes the term as dead code fails here.
    """
    s, slip = 0.02, 0.0003
    probe = 0.0002  # a plausible-magnitude chase distance: 2 bps.
    before = {mf: ev.cost_in_r(s, mf, slip, fees) for mf in ev.MAKER_FRAC_AXIS}

    monkeypatch.setattr(ev, "MAKER_NONFILL_SLIP", probe)
    for mf in ev.MAKER_FRAC_AXIS:
        after = ev.cost_in_r(s, mf, slip, fees)
        # Price fraction: the term is divided by s along with everything else.
        assert after == pytest.approx(before[mf] + 2.0 * mf * probe / s, rel=1e-12)
    # At all-taker there are no maker legs, so the term must NOT bite.
    assert ev.cost_in_r(s, 0.0, slip, fees) == pytest.approx(before[0.0], rel=1e-12)
    # At all-maker it is the entire difference.
    assert ev.cost_in_r(s, 1.0, slip, fees) - before[1.0] == pytest.approx(
        2.0 * probe / s, rel=1e-12)

    # And it must propagate into both inverses, not just the forward function.
    s_star = ev.min_admissible_stop(ev.COST_TOLERANCE_R, 0.5, slip, fees)
    assert ev.cost_in_r(s_star, 0.5, slip, fees) == pytest.approx(
        ev.COST_TOLERANCE_R, rel=1e-12)
    be = ev.max_tolerable_slip(0.03, 0.5, ev.COST_TOLERANCE_R, fees)
    assert be is not None and be > 0.0
    assert ev.cost_in_r(0.03, 0.5, be, fees) == pytest.approx(
        ev.COST_TOLERANCE_R, rel=1e-12)


def test_large_nonfill_term_makes_stops_inadmissible_through_the_normal_path(
        monkeypatch, fees):
    """REPLACES `test_nonfill_term_exhausting_the_budget_raises`.

    Under R denomination the term was subtracted from the budget, so a large
    value could consume it outright and the inverses had to raise. As a price
    fraction it competes with the fees inside the numerator instead, and a
    large value simply pushes s* out and turns cells inadmissible -- which is
    the ordinary mechanism, not a special case. There is no budget-exhaustion
    failure mode left to guard, and asserting one would be asserting the old
    denomination.
    """
    monkeypatch.setattr(ev, "MAKER_NONFILL_SLIP", 0.01)
    # 2*0.01 / 0.11 = 18.18% of entry: enormous, but a number, not an error.
    assert ev.min_admissible_stop(ev.COST_TOLERANCE_R, 1.0, 0.0, fees) == (
        pytest.approx(2.0 * (fees.maker_rate + 0.01) / ev.COST_TOLERANCE_R, rel=1e-12))
    # And an ordinary stop is now inadmissible on fixed costs alone.
    assert ev.max_tolerable_slip(0.02, 1.0, ev.COST_TOLERANCE_R, fees) is None
    assert ev.max_tolerable_slip(0.02, 0.5, ev.COST_TOLERANCE_R, fees) is None


# ---------------------------------------------------------------------------
# PLANTED MUTATION 2 -- the (1 - maker_frac) factor on the slippage term.
# ---------------------------------------------------------------------------

def test_slippage_is_charged_on_taker_legs_only():
    """PLANTED MUTATION GUARD: `(1 - maker_frac)` dropped from the slippage term.

    THE MUTATION. In `price_cost_rate`, change

        2.0 * f_eff + 2.0 * (1.0 - maker_frac) * slip
     -> 2.0 * f_eff + 2.0 * slip

    i.e. charge slippage on maker legs too -- which restores exactly the error
    this pass exists to correct.

    WHY IT IS EASY TO MISS. It is INVISIBLE at maker_frac = 0, where
    (1 - maker_frac) = 1 and both models agree exactly. The all-taker column is
    the one most likely to be spot-checked, and it cannot detect this. So the
    guard is anchored at maker_frac = 1.0, where the mutation's effect is
    largest, and at 0.5, where it is half.

    THE ARITHMETIC. With f_maker = 0.0002, f_taker = 0.0006, slip = 0.0010,
    s = 0.02:

        maker_frac = 1.0   correct : (2*0.0002 + 0*0.0010) / 0.02 = 0.0200
                           mutated : (2*0.0002 + 2*0.0010) / 0.02 = 0.1200
        maker_frac = 0.5   correct : (2*0.0004 + 1*0.0010) / 0.02 = 0.0900
                           mutated : (2*0.0004 + 2*0.0010) / 0.02 = 0.1400
        maker_frac = 0.0   correct : (2*0.0006 + 2*0.0010) / 0.02 = 0.1600
                           mutated :          identical           = 0.1600

    The all-taker row is listed to show the guard could NOT have been built on
    it. Confirmed to fail under the mutation before being committed.
    """
    f = ev.Fees(0.0002, 0.0006, "t", "p", "u", "r", "automated", "n")

    assert ev.cost_in_r(0.02, 1.0, 0.0010, f) == pytest.approx(0.0200, rel=1e-12)
    assert ev.cost_in_r(0.02, 0.5, 0.0010, f) == pytest.approx(0.0900, rel=1e-12)
    assert ev.cost_in_r(0.02, 0.0, 0.0010, f) == pytest.approx(0.1600, rel=1e-12)

    # The property, stated directly: raising slip must move an all-maker cost
    # by exactly nothing, and an all-taker cost by the full 2*dslip/s.
    assert ev.cost_in_r(0.02, 1.0, 0.0010, f) == ev.cost_in_r(0.02, 1.0, 0.0, f)
    assert (ev.cost_in_r(0.02, 0.0, 0.0010, f) - ev.cost_in_r(0.02, 0.0, 0.0, f)
            ) == pytest.approx(2.0 * 0.0010 / 0.02, rel=1e-12)
    # Half the legs taker -> exactly half the slippage sensitivity.
    assert (ev.cost_in_r(0.02, 0.5, 0.0010, f) - ev.cost_in_r(0.02, 0.5, 0.0, f)
            ) == pytest.approx(0.5 * 2.0 * 0.0010 / 0.02, rel=1e-12)

    # The same factor lives in the solver and in the inverse; both must carry it.
    assert ev.min_admissible_stop(0.11, 1.0, 0.0010, f) == pytest.approx(
        ev.min_admissible_stop(0.11, 1.0, 0.0, f), rel=1e-12)
    assert ev.max_tolerable_slip(0.02, 0.5, 0.11, f) == pytest.approx(
        (0.11 * 0.02 - 2.0 * 0.0004) / (2.0 * 0.5), rel=1e-12)


def test_module_imports_no_market_data_layer():
    """The step is arithmetic on a fee schedule. Nothing may reach the data layer."""
    src = open(ev.__file__).read()
    for banned in ("pandas", "numpy", "parquet", "src.folds", "src.sweep",
                   "src.regime", "src.analysis", "simulate", "signals"):
        assert banned not in src, (
            "%r appears in envelope.py; this step reads no market data" % banned
        )


def test_no_performance_quantity_appears(fees):
    """The firewall is re-armed for the next hypothesis.

    Checked over IDENTIFIERS and string literals, not raw source text: the
    module docstring names the prohibited quantities in order to state the
    prohibition, and a grep over prose would fire on the statement of the rule
    rather than on a violation of it.
    """
    import ast
    tree = ast.parse(open(ev.__file__).read())
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
    for banned in ("r_multiple", "expectancy", "win_rate", "win rate",
                   "profit_factor", "profit factor", "equity_curve", "sharpe",
                   "net_pnl"):
        assert banned not in blob, "%r is used as a name in envelope.py" % banned
    keys = set(ev.envelope_surface(fees, s_axis=(0.02,), maker_fracs=(0.5,),
                                   slips=(0.0,))[0])
    assert keys == {"s", "maker_frac", "slip", "f_eff", "cost_in_r", "min_stop",
                    "admissible", "notional_usdt", "leverage_x"}
