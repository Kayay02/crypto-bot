"""Guards for exchange-real position sizing.

THE CENTRAL TEST IS `test_CENTRAL_the_target_price_is_invariant_to_quantity`.
It calls the target solver with two quantities differing by a factor of ten and
requires the answer to be identical. That single assertion catches the entire
defect class this module exists to fix -- a target solved for a DOLLAR amount
moves when the quantity is floored, and the thesis's 40.0% breakeven and 53.6%
detectable-edge arithmetic then stops describing the system -- including any
future reintroduction of a quantity-dependent solve.

THE R IDENTITIES ARE THE SECOND LAYER. A stop must return exactly -1.0 and a
target exactly +1.5 REALISED risk units, on both directions, AT A FLOORED
QUANTITY, which is the case the fix exists for. They are asserted to FAIL when
the target is solved against nominal risk instead of realised, so the correct
and the incorrect forms are distinguishable by test rather than only by prose.

THE VIABILITY BRANCHES ARE UNREACHABLE AT THE FROZEN VALUES AND ARE TESTED AT
VALUES WHERE THEY ARE REACHABLE. A dead branch with no test is
`MAKER_NONFILL_COST_R` again: a term invisible to all 545 tests then in the
suite because every one of them multiplied it by zero.
"""

import ast
import math
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src", "engine"))

import costs  # noqa: E402
import sizing  # noqa: E402


LONG, SHORT = sizing.LONG, sizing.SHORT

#: The frozen fee/slippage configuration reports 24, 26 and 27 all size against.
CFG_KW = dict(stop_atr_mult=2.25, stop_max_pct=0.035,
              rvol_threshold=1.5, baseline_days=20)


@pytest.fixture(scope="module")
def cfg():
    return costs.CostConfig(**CFG_KW)


@pytest.fixture(scope="module")
def specs():
    return sizing.load_symbol_specs()


@pytest.fixture(scope="module")
def ticks():
    return sizing.load_tick_schedules()


def _module_ast():
    return ast.parse(open(sizing.__file__).read())


def _tick(ticks, symbol):
    """The CURRENT segment's tick, adequate for a synthetic reference."""
    return ticks[symbol].segments[-1][1]


# ---------------------------------------------------------------------------
# 1. THE CENTRAL TEST.
# ---------------------------------------------------------------------------

def test_CENTRAL_the_target_price_is_invariant_to_quantity(cfg, ticks):
    """THE CENTRAL TEST OF THIS MODULE, AND IT IS NAMED AS ONE.

    The target is solved PER UNIT, so quantity cancels exactly and the target
    price cannot depend on it. `costs.solve_target` solves for a DOLLAR amount
    and does NOT have this property -- that is the defect, and the contrast is
    asserted here so the two are distinguishable rather than merely described.
    """
    entry, denominator = 30_000.0, 500.0
    tick = _tick(ticks, "BTCUSDT")

    for direction in (LONG, SHORT):
        # The new solver takes no quantity at all: there is no argument to vary,
        # which is the strongest form of the invariance.
        target = sizing.target_price_on_tick(entry, denominator, direction,
                                             cfg, tick)
        again = sizing.target_price_on_tick(entry, denominator, direction,
                                            cfg, tick)
        assert target == again

        # And the whole sizing gives the same target at quantities differing by
        # a factor of ten, driven by a tenfold change in the risk unit.
        spec = sizing.SymbolSpec("BTCUSDT", 0.0001, 0.0001, 5.0)
        small = sizing.size(entry, 300.0, direction, "BTCUSDT", spec, cfg,
                            tick, risk_usd=20.0)
        large = sizing.size(entry, 300.0, direction, "BTCUSDT", spec, cfg,
                            tick, risk_usd=200.0)
        assert large.qty > 9.0 * small.qty, "the fixture must vary quantity"
        assert small.target_price == large.target_price, (
            "THE TARGET PRICE MUST NOT DEPEND ON QUANTITY")
        assert small.stop_price == large.stop_price
        assert small.denominator == large.denominator


def test_the_engines_dollar_solver_is_NOT_quantity_invariant(cfg, ticks):
    """THE DEFECT, PINNED. `costs.solve_target` moves with the quantity.

    Asserted so that the fix cannot be mistaken for a no-op, and so that anyone
    tempted to route the new sizing back through the old solver sees why not.
    `costs.py` is NOT modified -- this documents its behaviour, it does not
    change it.
    """
    entry, tick = 30_000.0, _tick(ticks, "BTCUSDT")
    a = costs.solve_target(entry, 0.0275, LONG, cfg, tick)
    b = costs.solve_target(entry, 0.0276, LONG, cfg, tick)
    assert a != b, "the dollar-denominated solve depends on quantity"


# ---------------------------------------------------------------------------
# 2. THE R IDENTITIES -- the recorded carve-out.
# ---------------------------------------------------------------------------

def _identities(cfg, specs, ticks, symbol, direction, entry, atr,
                risk_usd=20.0):
    spec = specs[symbol]
    tick = _tick(ticks, symbol)
    p = sizing.size(entry, atr, direction, symbol, spec, cfg, tick,
                    risk_usd=risk_usd)
    haircut = cfg.haircut_bps(symbol) / 10_000.0
    at_stop = sizing.net_proceeds_per_unit(p.entry_price, p.stop_price,
                                           direction, cfg, cfg.taker_fee,
                                           haircut) * p.qty
    at_target = sizing.net_proceeds_per_unit(p.entry_price, p.target_price,
                                             direction, cfg,
                                             cfg.maker_fee) * p.qty
    return p, at_stop, at_target


@pytest.mark.parametrize("symbol,entry,atr", [
    ("BTCUSDT", 30_000.0, 300.0),
    ("ETHUSDT", 2_000.0, 15.0),
    ("SOLUSDT", 100.0, 1.0),
])
@pytest.mark.parametrize("direction", [LONG, SHORT])
def test_the_R_identities_hold_at_a_floored_quantity(cfg, specs, ticks,
                                                     symbol, entry, atr,
                                                     direction):
    """A stop returns exactly -1.0 and a target exactly +1.5 REALISED units.

    AT A FLOORED QUANTITY, which is the case the fix exists for: the fixtures
    are chosen so `qty < qty_unfloored` on every one of the six cells.

    THE STOP IDENTITY IS EXACT because the denominator is recomputed from the
    ROUNDED stop price. THE TARGET IDENTITY IS EXACT UP TO ONE TICK, always in
    the favourable direction, because the target is rounded AWAY from entry and
    can therefore only deliver more than the reward, never less.
    """
    p, at_stop, at_target = _identities(cfg, specs, ticks, symbol, direction,
                                        entry, atr)
    assert p.qty < p.qty_unfloored, "the fixture must actually floor"
    assert p.realised_risk_usd > 0.0

    assert at_stop == pytest.approx(-p.realised_risk_usd, rel=1e-12)

    one_tick = p.qty * p.price_tick
    assert at_target >= sizing.REWARD_TO_RISK * p.realised_risk_usd - 1e-12
    assert at_target == pytest.approx(
        sizing.REWARD_TO_RISK * p.realised_risk_usd, abs=one_tick)


def test_the_identity_FAILS_against_nominal_risk(cfg, specs, ticks):
    """THE TWO FORMS MUST BE DISTINGUISHABLE BY TEST, NOT ONLY BY PROSE.

    Solving the target for `1.5 x NOMINAL` over a FLOORED quantity puts it
    further out than the per-unit solve, so the realised reward overshoots +1.5
    realised units by exactly the flooring residue. That is the defect: the
    trade no longer returns the R multiple the thesis's arithmetic assumes.
    """
    symbol, entry, atr = "ETHUSDT", 2_000.0, 15.0
    spec, tick = specs[symbol], _tick(ticks, symbol)
    p = sizing.size(entry, atr, LONG, symbol, spec, cfg, tick, risk_usd=20.0)
    assert p.qty < p.qty_unfloored

    wrong_cfg = costs.CostConfig(target_r_multiple=sizing.REWARD_TO_RISK,
                                 **CFG_KW)
    wrong_target = costs.solve_target(entry, p.qty, LONG, wrong_cfg, tick)
    wrong = sizing.net_proceeds_per_unit(entry, wrong_target, LONG, cfg,
                                         cfg.maker_fee) * p.qty

    assert wrong_target > p.target_price, "nominal solving pushes it further"
    assert wrong > sizing.REWARD_TO_RISK * p.realised_risk_usd * 1.0001, (
        "the nominal-solved target must MISS the realised identity")
    assert wrong == pytest.approx(sizing.REWARD_TO_RISK * p.nominal_risk_usd,
                                 abs=p.qty * tick)


def test_the_carve_out_is_exactly_one_function():
    """THE RECORDED FIREWALL CARVE-OUT, ASSERTED OVER THE AST.

    Computing proceeds at a price is outcome-adjacent ground. It is permitted in
    exactly one named function, on synthetic inputs only, with the blanket name
    ban otherwise intact.
    """
    tree = _module_ast()
    proceeds = [n.name for n in ast.walk(tree)
                if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
                and "proceeds" in n.name]
    assert proceeds == ["net_proceeds_per_unit"], proceeds

    callers = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for inner in ast.walk(node):
                if (isinstance(inner, ast.Name)
                        and inner.id == "net_proceeds_per_unit"):
                    callers.add(node.name)
    assert callers == set(), (
        "nothing inside the module may call it; only tests do", callers)


# ---------------------------------------------------------------------------
# 3. FLOORING.
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("symbol,entry,atr", [
    ("BTCUSDT", 30_000.0, 300.0), ("BTCUSDT", 16_500.0, 120.0),
    ("ETHUSDT", 2_000.0, 15.0), ("ETHUSDT", 1_200.0, 30.0),
    ("SOLUSDT", 100.0, 1.0), ("SOLUSDT", 22.0, 0.9),
])
@pytest.mark.parametrize("direction", [LONG, SHORT])
def test_flooring_invariants(cfg, specs, ticks, symbol, entry, atr, direction):
    spec, tick = specs[symbol], _tick(ticks, symbol)
    p = sizing.size(entry, atr, direction, symbol, spec, cfg, tick,
                    risk_usd=20.0)

    steps = p.qty / spec.qty_step
    assert abs(steps - round(steps)) < 1e-9, "qty must be a whole step multiple"
    assert p.qty <= p.qty_unfloored + 1e-15
    assert p.realised_risk_usd <= p.nominal_risk_usd + 1e-12
    assert p.notional == pytest.approx(p.qty * p.entry_price)
    assert p.realised_risk_usd == pytest.approx(p.qty * p.denominator)


def test_equality_holds_exactly_when_the_quantity_is_an_exact_multiple(cfg):
    """`realised == nominal` if and only if flooring removes nothing."""
    step = 0.25
    assert sizing.floor_to_step(1.0, step) == 1.0
    assert sizing.floor_to_step(1.25, step) == 1.25
    assert sizing.floor_to_step(1.24, step) == 1.0
    assert sizing.floor_to_step(0.24, step) == 0.0
    assert sizing.floor_to_step(1e-18, step) == 0.0

    # Integer-domain: a value that is a grid multiple to within float noise
    # must snap to it rather than truncating a whole step.
    assert sizing.floor_to_step(3.0 * 0.0001, 0.0001) == pytest.approx(0.0003)
    with pytest.raises(ValueError):
        sizing.floor_to_step(1.0, 0.0)


def test_a_planted_round_half_up_FAILS_the_flooring_invariants(cfg, specs,
                                                               ticks):
    """THE PLANTED ALTERNATIVE. Rounding to nearest can breach the risk unit.

    The closing record section 6.1 states it: "Floor is the only rounding
    direction that cannot breach the 1% rule; round-to-nearest and ceil both
    can." Asserted rather than quoted.
    """
    symbol, entry, atr = "SOLUSDT", 100.0, 1.0
    spec, tick = specs[symbol], _tick(ticks, symbol)
    p = sizing.size(entry, atr, SHORT, symbol, spec, cfg, tick, risk_usd=20.0)

    rounded = round(p.qty_unfloored / spec.qty_step) * spec.qty_step
    breaches = rounded * p.denominator
    assert rounded > p.qty_unfloored, "the fixture must round UP"
    assert breaches > p.nominal_risk_usd, (
        "round-to-nearest breaches the risk unit; flooring cannot")
    assert p.realised_risk_usd <= p.nominal_risk_usd


# ---------------------------------------------------------------------------
# 4. VIABILITY -- the dead branches, exercised where they are reachable.
# ---------------------------------------------------------------------------

def test_BELOW_MIN_QTY_is_reached_at_a_tiny_risk_unit(cfg, ticks):
    """A risk unit small enough that flooring zeroes the position.

    UNREACHABLE AT THE FROZEN VALUES -- report 24 section 6.5 gives the smallest
    per-position notional over the whole window as $40 on SOL, eight times the
    $5.00 threshold -- and implemented and tested anyway.
    """
    spec = sizing.SymbolSpec("BTCUSDT", 0.0001, 0.0001, 5.0)
    p = sizing.size(30_000.0, 300.0, LONG, "BTCUSDT", spec, cfg,
                    _tick(ticks, "BTCUSDT"), risk_usd=0.01)
    assert p.qty == 0.0
    assert p.viable is False
    assert p.reason == sizing.BELOW_MIN_QTY
    assert p.realised_risk_usd == 0.0
    assert p.qty_unfloored > 0.0, "it is flooring that zeroes it, not the solve"


def test_BELOW_MIN_NOTIONAL_is_reached_at_a_coarse_step_and_high_price(cfg,
                                                                       ticks):
    """A configuration whose notional falls under the $5.00 minimum.

    Constructed with a HIGH minimum notional so the branch is reached without a
    zero quantity -- the two conditions must be separately reachable or the
    second reason code could never be returned.
    """
    spec = sizing.SymbolSpec("BTCUSDT", 0.0001, 0.0001, 5_000.0)
    p = sizing.size(30_000.0, 300.0, LONG, "BTCUSDT", spec, cfg,
                    _tick(ticks, "BTCUSDT"), risk_usd=20.0)
    assert p.qty > 0.0, "the quantity condition must PASS here"
    assert p.notional < spec.min_trade_usdt
    assert p.viable is False
    assert p.reason == sizing.BELOW_MIN_NOTIONAL


def test_the_two_reason_codes_are_distinct_and_a_viable_position_says_so():
    assert sizing.BELOW_MIN_QTY != sizing.BELOW_MIN_NOTIONAL
    assert sizing.OK not in (sizing.BELOW_MIN_QTY, sizing.BELOW_MIN_NOTIONAL)
    spec = sizing.SymbolSpec("X", 0.1, 0.1, 5.0)
    assert sizing.viability(1.0, 100.0, spec) == (True, sizing.OK)
    assert sizing.viability(0.0, 100.0, spec) == (False, sizing.BELOW_MIN_QTY)
    assert sizing.viability(0.05, 100.0, spec) == (False,
                                                   sizing.BELOW_MIN_QTY)
    assert sizing.viability(0.1, 1.0, spec) == (False,
                                                sizing.BELOW_MIN_NOTIONAL)


def test_min_trade_num_coincides_with_qty_step_on_all_three_symbols(specs):
    """RECORDED, because it makes the two quantity conditions one condition
    here. They are still written separately: they are separate constraints at
    the venue and a future symbol could separate them."""
    for symbol in ("BTCUSDT", "ETHUSDT", "SOLUSDT"):
        assert specs[symbol].min_trade_num == specs[symbol].qty_step, symbol
        assert specs[symbol].min_trade_usdt == 5.0


# ---------------------------------------------------------------------------
# 5. TICK ROUNDING -- direction per leg, and every level on the grid.
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("symbol,entry,atr", [
    ("BTCUSDT", 30_017.37, 301.7), ("ETHUSDT", 2_003.77, 15.31),
    ("SOLUSDT", 101.337, 1.017),
])
@pytest.mark.parametrize("direction", [LONG, SHORT])
def test_every_level_lands_on_the_price_tick(cfg, specs, ticks, symbol, entry,
                                             atr, direction):
    spec, tick = specs[symbol], _tick(ticks, symbol)
    p = sizing.size(entry, atr, direction, symbol, spec, cfg, tick,
                    risk_usd=20.0)
    for level in (p.stop_price, p.target_price):
        q = level / tick
        assert abs(q - round(q)) < 1e-6, (symbol, direction, level, tick)


def test_both_legs_round_AWAY_from_entry(cfg, ticks):
    """THE REPOSITORY'S EXISTING CONVENTION, followed on both legs.

    `costs.stop_geometry` rounds the stop away with the comment "Round the stop
    AWAY from entry so rounding never tightens the risk";
    `costs.solve_price_for_net` rounds targets away so a level never delivers
    less than it claims. Both are asserted here on prices chosen to be off-grid.
    """
    tick = _tick(ticks, "BTCUSDT")
    entry = 30_000.0

    # STOP: away from entry means DOWN for a long, UP for a short -- wider.
    long_stop = sizing.stop_price_on_tick(entry, 675.37, LONG, tick)
    short_stop = sizing.stop_price_on_tick(entry, 675.37, SHORT, tick)
    assert long_stop <= entry - 675.37
    assert short_stop >= entry + 675.37
    assert entry - long_stop >= 675.37, "a long stop rounds WIDER"
    assert short_stop - entry >= 675.37, "a short stop rounds WIDER"

    # TARGET: away from entry means UP for a long, DOWN for a short -- harder.
    raw_long = sizing._unrounded_target(entry, 500.0, LONG, cfg)
    raw_short = sizing._unrounded_target(entry, 500.0, SHORT, cfg)
    assert sizing.target_price_on_tick(entry, 500.0, LONG, cfg, tick) >= raw_long
    assert sizing.target_price_on_tick(entry, 500.0, SHORT, cfg,
                                       tick) <= raw_short


def test_the_effective_stop_distance_is_recomputed_from_the_rounded_price(cfg,
                                                                          ticks):
    """STEP 3, AND IT IS NOT COSMETIC. Everything downstream uses the effective
    distance, so the stop identity is exact rather than off by the rounding."""
    tick = _tick(ticks, "BTCUSDT")
    spec = sizing.SymbolSpec("BTCUSDT", 0.0001, 0.0001, 5.0)
    entry, atr = 30_017.37, 301.7
    p = sizing.size(entry, atr, LONG, "BTCUSDT", spec, cfg, tick,
                    risk_usd=20.0)
    assert p.stop_distance_effective == pytest.approx(entry - p.stop_price)
    assert p.stop_distance_effective >= p.stop_distance_raw
    assert p.stop_distance_effective != p.stop_distance_raw, (
        "the fixture must actually be off-grid")
    with pytest.raises(ValueError):
        sizing.effective_stop_distance(100.0, 100.0, LONG)


def test_the_stop_floor_and_its_binding_flag(cfg):
    assert sizing.stop_distance(100.0, 1.0) == pytest.approx(2.25)
    assert sizing.stop_distance(100.0, 0.1) == pytest.approx(1.5)
    assert sizing.floor_binds(100.0, 0.1) is True
    assert sizing.floor_binds(100.0, 1.0) is False
    # Exactly on the floor: STRICTLY below is binding, so a tie is not.
    assert sizing.floor_binds(100.0, 1.5 / 2.25) is False


# ---------------------------------------------------------------------------
# 6. THE REWARD MULTIPLE, AND THE ENGINE DEFAULT IT IS NOT.
# ---------------------------------------------------------------------------

def test_the_reward_multiple_is_the_thesis_value_not_the_engine_default(cfg):
    assert sizing.REWARD_TO_RISK == 1.5
    assert cfg.target_r_multiple == 2.0, "the engine default is Point 4's 1:2"
    assert sizing.REWARD_TO_RISK != cfg.target_r_multiple

    # And the module never reads the config field.
    src = open(sizing.__file__).read()
    assert "target_r_multiple" not in src


def test_a_different_reward_multiple_moves_the_target_and_nothing_else(cfg,
                                                                       ticks):
    """The reward multiple enters the target and no other quantity."""
    tick = _tick(ticks, "BTCUSDT")
    spec = sizing.SymbolSpec("BTCUSDT", 0.0001, 0.0001, 5.0)
    a = sizing.size(30_000.0, 300.0, LONG, "BTCUSDT", spec, cfg, tick,
                    risk_usd=20.0, reward_to_risk=1.5)
    b = sizing.size(30_000.0, 300.0, LONG, "BTCUSDT", spec, cfg, tick,
                    risk_usd=20.0, reward_to_risk=2.0)
    assert b.target_price > a.target_price
    assert a.qty == b.qty
    assert a.stop_price == b.stop_price
    assert a.realised_risk_usd == b.realised_risk_usd


# ---------------------------------------------------------------------------
# 7. WHAT THE MODULE MAY NOT DO.
# ---------------------------------------------------------------------------

def _imports():
    out = set()
    for node in ast.walk(_module_ast()):
        if isinstance(node, ast.Import):
            for a in node.names:
                out.add(a.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                out.add(node.module)
                for a in node.names:
                    out.add("%s.%s" % (node.module, a.name))
    return out


def _identifiers():
    names = set()
    for node in ast.walk(_module_ast()):
        if isinstance(node, ast.Name):
            names.add(node.id)
        elif isinstance(node, ast.Attribute):
            names.add(node.attr)
        elif isinstance(node, ast.arg):
            names.add(node.arg)
        elif isinstance(node, (ast.FunctionDef, ast.ClassDef)):
            names.add(node.name)
    return names


def test_the_risk_package_is_not_reachable():
    """`src/engine` STAYS UNWIRED FROM THE RISK PACKAGE.

    Report 26's narrowed assertion enforces this unconditionally for engine
    files, with no allowlist entry available. The risk unit is a PARAMETER.
    """
    src = open(sizing.__file__).read()
    assert "src.risk" not in src
    assert "from src import risk" not in src
    for mod in _imports():
        assert not mod.startswith("src.risk"), mod
    # `risk_usd` is an argument on every path that needs it.
    for name in ("size", "per_unit_denominator"):
        fn = [n for n in ast.walk(_module_ast())
              if isinstance(n, ast.FunctionDef) and n.name == name][0]
        args = {a.arg for a in fn.args.args}
        if name == "size":
            assert "risk_usd" in args


def test_no_leverage_check_exists_anywhere_in_the_module():
    """REPORT 26 SECTION 12.1: `max_leverage` is an unmeasured placeholder that
    would bind on 16.14% of bars. It stays at 3.0 for the legacy paths and this
    module implements no leverage refusal."""
    # Over IDENTIFIERS, not raw text: the module docstring NAMES `max_leverage`
    # in order to record that it is deliberately absent, and a text search would
    # fire on the statement of the rule rather than on a violation of it.
    for name in _identifiers():
        assert "leverage" not in name.lower(), name
    for node in ast.walk(_module_ast()):
        if isinstance(node, ast.Attribute):
            assert "leverage" not in node.attr.lower(), node.attr
    # No non-docstring string literal names it either.
    docstrings = set()
    for node in ast.walk(_module_ast()):
        if isinstance(node, (ast.Module, ast.FunctionDef, ast.ClassDef)):
            d = ast.get_docstring(node, clean=False)
            if d is not None:
                docstrings.add(d)
    for node in ast.walk(_module_ast()):
        if (isinstance(node, ast.Constant) and isinstance(node.value, str)
                and node.value not in docstrings):
            assert "leverage" not in node.value.lower(), node.value


def test_no_numeric_literal_equals_a_qty_step_or_a_price_tick(specs, ticks):
    """THE SPECS ARE READ, NOT RETYPED."""
    banned = set()
    for spec in specs.values():
        banned.add(float(spec.qty_step))
        banned.add(float(spec.min_trade_num))
        banned.add(float(spec.min_trade_usdt))
    for schedule in ticks.values():
        for _, tick in schedule.segments:
            banned.add(float(tick))
    assert 0.0001 in banned and 5.0 in banned, "the fixture must be populated"

    literals = [n.value for n in ast.walk(_module_ast())
                if isinstance(n, ast.Constant)
                and isinstance(n.value, (int, float))
                and not isinstance(n.value, bool)]
    for value in literals:
        assert float(value) not in banned, value


def test_no_data_layer_and_no_1m_path_is_reachable():
    banned = ("src.timeframe", "src.folds", "src.analysis", "src.sweep",
              "src.regime", "pandas", "numpy", "pyarrow", "simulate")
    for mod in _imports():
        for bad in banned:
            assert not (mod == bad or mod.startswith(bad + ".")), mod
    src = open(sizing.__file__).read()
    for word in ("ohlcv", "parquet", "load_1m", "load_bars", "read_parquet"):
        assert word not in src, word


PERFORMANCE_NAMES = ("expectancy", "win_rate", "winrate", "profit_factor",
                     "sharpe", "sortino", "net_pnl", "gross_pnl", "drawdown",
                     "r_multiple", "equity", "pnl")


def test_no_performance_quantity_appears_in_the_module():
    """THE TWELVE-NAME GUARD, NOT RELAXED FOR THE CARVE-OUT.

    `net_proceeds_per_unit` contains none of the twelve, so the recorded
    carve-out needed no exception to the name ban -- only to the conceptual
    boundary, which is why it is documented rather than exempted.
    """
    tree = _module_ast()
    docstrings = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.FunctionDef, ast.ClassDef)):
            d = ast.get_docstring(node, clean=False)
            if d is not None:
                docstrings.add(d)
    blob = set(_identifiers())
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            if node.value not in docstrings:
                blob.add(node.value)
    text = " ".join(blob).lower()
    for banned in PERFORMANCE_NAMES:
        assert banned not in text, banned


# ---------------------------------------------------------------------------
# 8. REGRESSION -- the untouched path is provably untouched.
# ---------------------------------------------------------------------------

def test_costs_position_size_is_byte_identical_to_what_reports_24_26_27_used(cfg):
    """`costs.py` IS NOT MODIFIED AND THIS PROVES IT ON THE CALLED PATH.

    Reports 24, 26 and 27 all call `position_size`. The values below are hand
    computed from the documented denominator -- move + entry fee + stop fee +
    entry slippage + stop haircut -- exactly as report 24 section 2.1 pinned it.
    """
    # BTCUSDT long, entry 30000, stop distance 675: the report 24 fixture.
    denom = 675.0 + 18.0 + 17.595 + 0.0 + 14.6625
    assert costs.position_size(30_000.0, 29_325.0, LONG, cfg,
                               "BTCUSDT") == pytest.approx(20.0 / denom,
                                                           rel=1e-12)
    # And the new module's denominator is that same number, reused not copied.
    assert sizing.per_unit_denominator(30_000.0, 29_325.0, LONG, cfg,
                                       "BTCUSDT") == pytest.approx(denom,
                                                                   rel=1e-12)


def test_the_denominator_is_the_engines_and_not_the_naive_move(cfg):
    """The naive form -- sizing on the price move alone -- is 7.4% wrong, which
    report 24 section 2.1 measured. Asserted so the two cannot be conflated."""
    d = sizing.per_unit_denominator(30_000.0, 29_325.0, LONG, cfg, "BTCUSDT")
    naive = 675.0
    assert d > naive
    assert d / naive == pytest.approx(1.074, abs=0.002)


def test_sized_positions_carry_both_risk_figures(cfg, specs, ticks):
    """DUAL RECORDING IS MANDATORY. Neither field is derived at read time."""
    p = sizing.size(2_000.0, 15.0, LONG, "ETHUSDT", specs["ETHUSDT"], cfg,
                    _tick(ticks, "ETHUSDT"), risk_usd=20.0)
    fields = set(type(p).__dataclass_fields__)
    assert {"nominal_risk_usd", "realised_risk_usd"} <= fields
    assert p.nominal_risk_usd == 20.0
    assert p.realised_risk_usd < p.nominal_risk_usd
    assert math.isfinite(p.realised_risk_usd)
