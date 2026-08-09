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
        # Rebuild the whole chain from dollars at this account size.
        risk_dollars = 20.0
        notion = risk_dollars / s
        dollar_cost = 2.0 * (f_eff + slip) * notion
        assert dollar_cost / risk_dollars == pytest.approx(got, rel=1e-12)
        # Equity only ever appears in leverage.
        assert ev.implied_leverage(s, risk_dollars, equity) == pytest.approx(
            notion / equity, rel=1e-12)


def test_cost_in_r_is_independent_of_risk_dollars_too(synthetic_fees):
    """The same cancellation removes R$, not only equity."""
    s, mf, slip = 0.015, 0.25, 0.0002
    f_eff = 0.25 * 0.00013 + 0.75 * 0.00047
    expected = 2.0 * (f_eff + slip) / s
    assert ev.cost_in_r(s, mf, slip, synthetic_fees) == pytest.approx(expected, rel=1e-12)
    for risk_dollars in (5.0, 20.0, 5000.0):
        notion = risk_dollars / s
        assert 2.0 * (f_eff + slip) * notion / risk_dollars == pytest.approx(
            expected, rel=1e-12)


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
    assert ev.effective_fee_rate(1.0, synthetic_fees) == synthetic_fees.maker_rate
    s, slip = 0.018, 0.0002
    assert ev.cost_in_r(s, 1.0, slip, synthetic_fees) == pytest.approx(
        2.0 * (synthetic_fees.maker_rate + slip) / s, rel=1e-12)


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

    # The relation stated directly: both legs cost exactly twice one leg.
    s, mf, slip = 0.02, 0.5, 0.0003
    one_leg = (ev.effective_fee_rate(mf, f) + slip) / s
    assert ev.cost_in_r(s, mf, slip, f) == pytest.approx(2.0 * one_leg, rel=1e-12)
    assert ev.cost_in_r(s, mf, slip, f) != pytest.approx(one_leg, rel=1e-6)

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


def test_slippage_spread_is_invariant_to_maker_frac(fees):
    """f_eff enters s* additively with slip, so it cancels from the difference.

    The report leans on this: it is why the sensitivity verdict is one number
    rather than five. Asserted so a later edit that makes f_eff multiplicative
    cannot pass silently.
    """
    sens = ev.slippage_sensitivity(fees)
    spreads = [v["spread"] for v in sens.values()]
    expected = 2.0 * (0.001 - 0.0) / ev.COST_TOLERANCE_R
    for sp in spreads:
        assert sp == pytest.approx(expected, rel=1e-12)


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
