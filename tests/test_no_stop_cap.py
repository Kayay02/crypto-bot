"""THERE IS NO STOP CAP, AND THIS IS THE GUARD THAT WOULD CATCH ONE COMING BACK.

WHAT IS COMMITTED. `docs/design/04_1g_cap_adoption.md` §0:

    CANDIDATE B IS ADOPTED. THERE IS NO STOP CAP.
    THE STOP IS THE ATR RULE FLOORED AT THE COST FLOOR, WITH NO UPPER BOUND.

WHY A GUARD AND NOT THE ADOPTION ALONE. The specification committed that rule on
2026-08-17 and `costs.stop_geometry` went on clipping every stop at
`stop_max_pct` afterwards, which is the divergence
`docs/design/04_2b_point_4_decomposition.md` §4.3 records against freeze
precondition 3. **A rule enforced only by intention is the shape of every defect
in the ledger.** The divergence's whole content is that a cap is applied where
the specification says none is, so the test that closes it must be able to detect
a cap being applied.

    THE DETECTION PRINCIPLE: FEED A WIDTH NO PLAUSIBLE CAP WOULD ADMIT, AND
    REQUIRE IT TO SURVIVE UNCLIPPED ALL THE WAY TO SIZING.

THE WIDTH IS NOT INVENTED. `docs/handoff/39_point_4_cap_candidates.md` §4.1
measured the widest ATR-implied stop the frozen rule reaches over the candidate
population: **SOLUSDT, 49.7087 per cent of entry, at an entry of 10.0108 with an
ATR of 2.2117.** That cell is used verbatim below, so the guard admits a width of
the order the population actually produces and not a width chosen to make the
point. The frozen cap that was retired was 0.035 -- the measured width exceeds it
by more than fourteen times, so any cap anywhere near the retired one clips it and
the guard fires.

WHAT THIS FILE DOES NOT ASSERT. It does not assert that `stop_max_pct` is gone.
`docs/design/04_1g_cap_adoption.md` §5 keeps it as a required `CostConfig`
parameter for consumers the adoption left alive, and §4 below pins that it is
still required -- **a parameter that survives for a live consumer is not a
divergence; a parameter applied on the stop rule is.**

NO OUTCOME QUANTITY IS COMPUTED OR INSPECTED. Every assertion is over a price, a
distance, a quantity, a mechanism label or an AST node. No bar is read at any
resolution and no artifact is opened.
"""

import ast
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src", "engine"))

import costs  # noqa: E402
import portfolio as pf  # noqa: E402
import sizing  # noqa: E402

from conftest import make_cfg  # noqa: E402

LONG, SHORT = costs.LONG, costs.SHORT

#: `docs/handoff/39_point_4_cap_candidates.md` §4.1's widest measured cell, and
#: the two narrower ones beside it. Entry, ATR and the width the frozen ATR
#: multiple implies, as that report states them.
WIDEST = {
    "SOLUSDT": (10.0108, 2.2117, 0.497087),
    "ETHUSDT": (1908.89, 100.2939, 0.118216),
    "BTCUSDT": (28062.00, 1064.0431, 0.085315),
}

#: The retired constant, named here ONLY as the thing that must not be applied.
#: `docs/design/04_1e_stop_cap.md` records it as WRONG on four computable
#: grounds and `04_1g` §0 removes it; it survives as a `CostConfig` field for
#: the consumers §5 of that document leaves alive.
RETIRED_CAP = 0.035

#: A tick fine enough that rounding cannot account for any difference asserted
#: below. The stop is rounded AWAY from entry, so a surviving width can only be
#: understated by rounding, never overstated -- which is the safe direction for
#: every assertion here.
TICK = 0.0001

#: Agreement with report 39 section 4.1 to a hundredth of a percentage point.
#: THE REPORT'S ENTRY AND ATR ARE STATED TO THE PRECISION THEY ARE DISPLAYED AT,
#: so recomputing the width from them reproduces the report's figure to about
#: 2e-5 and not exactly. The tolerance is set to what the displayed precision
#: supports rather than to what the recomputation happens to give, and it is far
#: tighter than any clipping this guard exists to catch -- a cap at the retired
#: level would move SOLUSDT's width by 0.46, which is four orders of magnitude
#: larger.
WIDTH_TOLERANCE = 1e-4


@pytest.fixture
def cfg():
    """The frozen ATR multiple, and `stop_max_pct` still supplied.

    IT IS SUPPLIED DELIBERATELY. If the guard passed only because the parameter
    were absent it would prove nothing about whether the parameter is applied.
    """
    return make_cfg(stop_atr_mult=sizing.STOP_ATR_MULT,
                    stop_max_pct=RETIRED_CAP)


# ---------------------------------------------------------------------------
# 1. THE GEOMETRY THAT USED TO CLIP.
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("symbol", sorted(WIDEST))
def test_the_widest_measured_width_SURVIVES_stop_geometry(cfg, symbol):
    """THE TEST THAT FAILS IF A CAP IS REINTRODUCED.

    `costs.stop_geometry` is the one function that ever applied a cap, reached
    from `costs.stop_price` and from `src/engine/simulate.py` and from nowhere
    else -- `docs/design/04_1g_cap_adoption.md` §4.1. It must now return the raw
    ATR distance whatever its width.
    """
    entry, atr, expected_width = WIDEST[symbol]
    stop, mech = costs.stop_geometry(entry, atr, LONG, cfg, TICK, symbol)

    raw = cfg.stop_atr_mult * atr
    width = (entry - stop) / entry

    assert width == pytest.approx(expected_width, abs=WIDTH_TOLERANCE), (
        "the fixture no longer reproduces report 39 section 4.1's width")
    assert (entry - stop) == pytest.approx(raw, abs=TICK), (
        "the stop was clipped: the surviving distance is not the raw ATR one")
    assert mech == costs.ATR, mech
    assert mech != costs.CAP

    # AND EVERY ONE OF THE THREE IS PAST THE RETIRED CAP BY A MARGIN NO
    # ROUNDING ACCOUNTS FOR, so none can pass by accident.
    assert width > RETIRED_CAP * 2.0, width


def test_the_widest_cell_of_all_is_more_than_fourteen_TIMES_the_retired_cap(cfg):
    """THE SINGLE STRONGEST CASE, ASSERTED ON ITS OWN.

    Report 39 section 4.1's widest cell is SOLUSDT's. It exceeds the retired
    0.035 by more than fourteen times, so a cap reintroduced anywhere near the
    retired level clips it by an enormous margin and cannot be mistaken for a
    rounding artifact.
    """
    entry, atr, _ = WIDEST["SOLUSDT"]
    stop, mech = costs.stop_geometry(entry, atr, LONG, cfg, TICK, "SOLUSDT")
    width = (entry - stop) / entry
    assert mech == costs.ATR
    assert width > RETIRED_CAP * 14.0, width


@pytest.mark.parametrize("symbol", sorted(WIDEST))
def test_the_widest_measured_width_SURVIVES_on_the_short_side(cfg, symbol):
    """The band is on distance, not on side, so both sides must be uncapped."""
    entry, atr, expected_width = WIDEST[symbol]
    stop, mech = costs.stop_geometry(entry, atr, SHORT, cfg, TICK, symbol)
    assert (stop - entry) / entry == pytest.approx(expected_width,
                                                   abs=WIDTH_TOLERANCE)
    assert mech == costs.ATR


def test_the_CAP_MECHANISM_IS_UNREACHABLE_at_every_width(cfg):
    """SWEPT ACROSS WIDTHS RATHER THAN ASSERTED AT ONE.

    A cap reintroduced at any level inside this sweep is caught. The sweep runs
    from a width the floor sets, through the retired cap, to well past the
    widest measured cell -- so it crosses every level a reintroduced cap could
    plausibly take.
    """
    entry = 100.0
    seen = set()
    steps = 200
    for i in range(1, steps + 1):
        # widths from 0.005 to 1.000 of entry, in even steps
        width = i / float(steps)
        atr = width * entry / cfg.stop_atr_mult
        stop, mech = costs.stop_geometry(entry, atr, LONG, cfg, TICK, "ETHUSDT")
        seen.add(mech)
        if mech == costs.ATR:
            assert (entry - stop) == pytest.approx(cfg.stop_atr_mult * atr,
                                                   abs=TICK), width

    assert costs.CAP not in seen, "a cap was applied somewhere in the sweep"
    assert seen == {costs.FLOOR, costs.ATR}, seen


def test_the_floor_is_UNTOUCHED_and_still_binds_below_it(cfg):
    """THE ADOPTION REMOVES THE UPPER BOUND AND NOTHING ELSE.

    `docs/design/04_1g_cap_adoption.md` §0 keeps the stop floored at the cost
    floor. A guard that only checked the cap's absence would pass on a geometry
    that had lost the floor too.
    """
    for symbol, expect in (("BTCUSDT", 0.01020), ("ETHUSDT", 0.01020),
                           ("SOLUSDT", 0.01320)):
        assert cfg.stop_min_pct(symbol) == pytest.approx(expect)
        entry = 100.0
        stop, mech = costs.stop_geometry(entry, 1e-6, LONG, cfg, TICK, symbol)
        assert mech == costs.FLOOR
        assert (entry - stop) == pytest.approx(entry * expect, abs=TICK)


# ---------------------------------------------------------------------------
# 2. THE GOVERNING PATH, END TO END.
# ---------------------------------------------------------------------------

def test_the_widest_width_SURVIVES_TO_SIZING_on_the_governing_path(cfg):
    """`portfolio.size_position` IS THE RISK UNIT, per
    `docs/design/04_1c_path_and_scope.md` §2.1, and it must size against the
    full uncapped distance.

    THIS IS THE LIMB THAT MATTERS. A cap reintroduced anywhere upstream of
    sizing would shrink the stop distance, which would inflate the quantity for
    a fixed risk allocation -- so the assertion is on the distance the
    denominator was built from, not merely on a label.
    """
    symbol = "SOLUSDT"
    entry, atr, expected_width = WIDEST[symbol]
    specs = sizing.load_symbol_specs()
    ticks = sizing.load_tick_schedules()
    # A timestamp inside the readable window. NO BAR IS READ AT IT; it only
    # selects which tick segment applies.
    price_tick = ticks[symbol].tick_at(1_688_000_000_000)

    sized = pf.size_position(entry, atr, LONG, symbol, specs[symbol], cfg,
                             price_tick, allocation_usd=pf.UNIT_USD)

    distance = entry - sized.stop_price
    assert distance == pytest.approx(cfg.stop_atr_mult * atr,
                                     abs=2.0 * price_tick), (
        "the governing path clipped the stop")
    assert distance / entry > RETIRED_CAP * 10.0

    # AND THE UNCLIPPED DISTANCE IS WHAT THE DENOMINATOR WAS BUILT FROM.
    assert sized.denominator > distance, (
        "the denominator must exceed the bare stop distance by the cost terms")
    assert sized.qty_unfloored == pytest.approx(
        pf.UNIT_USD / sized.denominator, rel=1e-12)


def test_sizing_stop_distance_has_no_upper_bound_by_construction():
    """`sizing.stop_distance` is `max(ATR multiple, floor)` and takes no cap
    argument at all. Asserted over the signature and over a width no cap would
    admit, so the claim does not rest on reading the body."""
    params = sizing.stop_distance.__code__.co_varnames[
        :sizing.stop_distance.__code__.co_argcount]
    assert set(params) == {"entry_price", "atr", "mult", "floor_fraction"}, params

    entry, atr, expected_width = WIDEST["SOLUSDT"]
    d = sizing.stop_distance(entry, atr)
    assert d == pytest.approx(sizing.STOP_ATR_MULT * atr, rel=1e-12)
    assert d / entry == pytest.approx(expected_width, abs=WIDTH_TOLERANCE)


# ---------------------------------------------------------------------------
# 3. STRUCTURAL: NOTHING ON THE STOP RULE COMPARES AGAINST THE PARAMETER.
# ---------------------------------------------------------------------------

def _tree(path):
    return ast.parse(open(path).read())


def _docstrings(tree):
    out = set()
    for n in ast.walk(tree):
        if isinstance(n, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef,
                          ast.ClassDef)):
            d = ast.get_docstring(n, clean=False)
            if d is not None:
                out.add(d)
    return out


def test_stop_geometry_does_not_READ_the_cap_parameter():
    """OVER AST NODES, NOT OVER TEXT.

    The function's docstring now states at length that the parameter exists and
    is not applied -- content this repository's modules are required to carry --
    so a raw-text search would fire on the statement of the rule. Only the
    executable body counts.
    """
    tree = _tree(costs.__file__)
    fn = [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)
          and n.name == "stop_geometry"][0]
    docs = _docstrings(tree)

    attrs = {n.attr for n in ast.walk(fn) if isinstance(n, ast.Attribute)}
    assert "stop_max_pct" not in attrs, (
        "stop_geometry reads the cap parameter again")
    assert "stop_min_pct" in attrs, (
        "the floor must still be read, or this check passes on a gutted "
        "function rather than on an uncapped one")

    strings = {n.value for n in ast.walk(fn)
               if isinstance(n, ast.Constant) and isinstance(n.value, str)
               and n.value not in docs}
    assert "cap" not in strings, strings

    # AND NO COMPARISON IN THE BODY HAS THE CAP ON EITHER SIDE.
    for node in ast.walk(fn):
        if isinstance(node, ast.Compare):
            names = {n.attr for n in ast.walk(node)
                     if isinstance(n, ast.Attribute)}
            assert "stop_max_pct" not in names, ast.dump(node)


def test_the_cap_label_survives_and_is_assigned_nowhere_in_the_geometry():
    """`docs/design/04_1g_cap_adoption.md` §4.4: the reject-over-clip rule is
    inoperative rather than repealed, and would govern again the moment a cap
    existed. The label is kept for that step; it must simply be unreachable."""
    assert costs.CAP == "cap"
    tree = _tree(costs.__file__)
    fn = [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)
          and n.name == "stop_geometry"][0]
    names = {n.id for n in ast.walk(fn) if isinstance(n, ast.Name)}
    assert "CAP" not in names, "stop_geometry can still return CAP"
    assert {"FLOOR", "ATR"} <= names


def test_the_only_callers_of_stop_geometry_are_the_two_the_adoption_NAMES():
    """`docs/design/04_1g_cap_adoption.md` §4.1 states that `stop_geometry` is
    called from `costs.stop_price`, from `src/engine/simulate.py`, and from
    nowhere else. If a third caller appears, the reachability finding that
    scoped this change no longer holds and the change's scope must be revisited.
    """
    callers = set()
    for base in ("src",):
        for d, dirs, files in os.walk(os.path.join(ROOT, base)):
            dirs[:] = [x for x in dirs if x != "__pycache__"]
            for f in sorted(files):
                if not f.endswith(".py"):
                    continue
                path = os.path.join(d, f)
                for n in ast.walk(_tree(path)):
                    if not isinstance(n, ast.Call):
                        continue
                    nm = n.func.attr if isinstance(n.func, ast.Attribute) else (
                        n.func.id if isinstance(n.func, ast.Name) else None)
                    if nm == "stop_geometry":
                        callers.add(os.path.relpath(path, ROOT))
    assert callers == {os.path.join("src", "engine", "costs.py"),
                       os.path.join("src", "engine", "simulate.py")}, callers


# ---------------------------------------------------------------------------
# 4. THE PARAMETER SURVIVES, AND THAT IS NOT A DIVERGENCE.
# ---------------------------------------------------------------------------

def test_stop_max_pct_is_STILL_A_REQUIRED_PARAMETER():
    """`docs/design/04_1g_cap_adoption.md` §5 item 2 keeps it.

    It is read by the analysis modules that compute the admitted domain and set
    by the sweep, which derives a cap per fold for its own grid and whose
    disposition §5 expressly leaves to whoever next touches the sweep.
    REMOVING IT HERE WOULD DECIDE THAT QUESTION BY SIDE EFFECT.
    """
    assert "stop_max_pct" in costs.NO_DEFAULT_PARAMS
    # REFUSED AT CONSTRUCTION, not at first read: `__post_init__` raises, which
    # is what makes every construction site a place the parameter is still
    # supplied rather than a place it could quietly lapse to a default.
    with pytest.raises(ValueError, match="stop_max_pct"):
        costs.CostConfig(stop_atr_mult=2.25, rvol_threshold=1.5,
                         baseline_days=20)


def test_the_sweep_still_supplies_its_derived_cap_and_is_NOT_withdrawn():
    """§5's closing paragraph: the sweep's `derived_cap` is not withdrawn.

    Asserted structurally over the sweep's own config builder, so that a later
    step removing the parameter cannot do it quietly through this path. What
    changed is that the value is no longer APPLIED, which is §5's own phrasing:
    "a cap it no longer supplies to the engine".
    """
    from src.sweep import sweep as sw
    tree = _tree(sw.__file__)
    fn = [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)
          and n.name == "cfg_for"][0]
    kwargs = {k.arg for n in ast.walk(fn) if isinstance(n, ast.Call)
              for k in n.keywords if k.arg}
    assert "stop_max_pct" in kwargs, (
        "the sweep stopped supplying its derived cap, which section 5 leaves "
        "alive and routes to whoever next touches the sweep")
