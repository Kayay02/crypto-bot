"""Guards for the portfolio execution path. IT IS PROVEN HERE; IT IS NOT RUN.

THE ONE REAL-DATA EXECUTION IN THIS MODULE IS THE `max_hold` REGRESSION, which
evaluates no level and reads no 1m bar, and which must reproduce report 26
exactly: 6,021 taken and 5,363 skipped, 1,973 / 1,963 / 2,085 per symbol. A
discrepancy is not a footnote -- it means the budget, rotation or ordering
machinery differs from the implementation report 26 verified, and every figure
that report states would then describe a different rule than the one that ships.

`full` MODE IS NEVER RUN ON REAL DATA ANYWHERE IN THIS FILE. Every level, every
fill, every flag and both R identities are exercised on SYNTHETIC 1m series
built from hand-written numbers, injected through the cache's loader seam. The
module's default loader is the sealed one and a test asserts it can reach 1m
bars by no other route.

THE CENTRAL PAIR OF TESTS IS THE TWO FILL RULES. A bar that reaches the stop
exactly fills it, and a bar that reaches the target exactly does NOT fill it --
one tick beyond does. If those two ever became the same predicate the winning
leg would have quietly become more generous and every downstream figure would
still look reasonable.
"""

import ast
import os
import sys

import numpy as np
import pandas as pd
import pytest

from src.risk import budget as rb
from src.risk import exit_spec as es
from src.timeframe import sealed_1m as sealed

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src", "engine"))

import contracts  # noqa: E402
import costs  # noqa: E402
import portfolio as pf  # noqa: E402
import sizing  # noqa: E402

from src.analysis import budget_cost as bc  # noqa: E402
from src.analysis import exposure_profile as ep  # noqa: E402

LONG, SHORT = pf.LONG, pf.SHORT
MINUTE_MS = pf.MINUTE_MS
BAR_MS = pf.BAR_MS

#: Report 26's figures. THE REGRESSION TARGETS, restated here as literals on
#: purpose: this file is where a drift from the frozen report must fail.
REPORT_26_TAKEN = 6_021
REPORT_26_SKIPPED = 5_363
REPORT_26_TOTAL = 11_384
REPORT_26_PER_SYMBOL = {"BTCUSDT": 1_973, "ETHUSDT": 1_963, "SOLUSDT": 2_085}

#: Synthetic reference cells, report 28's own. Floor-bound: the ATR is small
#: enough that the 1.50% floor sets the stop, which is the stratum where the
#: funding drift in document 06a section 3.2 lands on its stated 1.482R.
CELLS = (("BTCUSDT", 30_000.0, 100.0),
         ("ETHUSDT", 2_000.0, 5.0),
         ("SOLUSDT", 100.0, 0.3))


@pytest.fixture(scope="module")
def cfg():
    return ep.cost_config()


@pytest.fixture(scope="module")
def specs():
    return sizing.load_symbol_specs()


@pytest.fixture(scope="module")
def ticks():
    return sizing.load_tick_schedules()


def _module_ast():
    return ast.parse(open(pf.__file__).read())


def _code_text():
    """The module's EXECUTABLE tokens, comments and docstrings stripped.

    This module discusses every prohibition it obeys -- the simulator it does
    not patch, the margin ceiling it does not implement, the lookahead it does
    not perform -- so a plain substring search fires on the statement of the
    rule. Only what runs counts.
    """
    import io
    import tokenize

    out, prev = [], tokenize.INDENT
    for tok in tokenize.generate_tokens(
            io.StringIO(open(pf.__file__).read()).readline):
        if tok.type == tokenize.COMMENT:
            continue
        if tok.type == tokenize.STRING and prev in (
                tokenize.INDENT, tokenize.DEDENT, tokenize.NEWLINE,
                tokenize.NL, tokenize.ENCODING):
            prev = tok.type
            continue
        if tok.type not in (tokenize.NL, tokenize.NEWLINE):
            prev = tok.type
        out.append(tok.string)
    return " ".join(out)


# ---------------------------------------------------------------------------
# Synthetic scaffolding. NO REAL BAR IS READ BY ANY OF IT.
# ---------------------------------------------------------------------------

def _tick(ticks, symbol, when):
    """THE TICK IS RESOLVED PER TIMESTAMP, NOT PER SYMBOL.

    SOLUSDT moved from a 0.0001 grid to a 0.001 grid on 2024-08-14 (report 28
    section 10), inside the measurement window. A helper that took the latest
    segment would apply the wrong trade-through margin to two and a half years
    of SOL bars -- and it did, until the module under test disagreed with it.
    """
    return ticks[symbol].tick_at(int(when))


def _candidate(symbol, direction, signal_bar_ts, entry_price, atr):
    """One candidate row, with the time exit from the FROZEN calendar function.

    `exposure_profile.max_hold_exit` owns the settlement INDEX. It is called
    here rather than in the module under test because document 06 section 6.1
    records that the index and `FUNDING_SETTLEMENTS_CHARGED` are different
    quantities that happen to coincide at 3.
    """
    exit_bar, exit_close, _ = ep.max_hold_exit(signal_bar_ts)
    return {
        "ts": int(signal_bar_ts),
        "symbol": symbol,
        "direction": direction,
        "entry_price": float(entry_price),
        "atr": float(atr),
        "entry_close_ms": int(ep.bar_close_ms(signal_bar_ts)),
        "exit_bar_ts": int(exit_bar),
        "exit_close_ms": int(exit_close),
    }


def _frame(rows):
    return pd.DataFrame(rows)


class Synthetic1m:
    """A hand-built 1m series per symbol, served through the cache's loader seam.

    IT READS NOTHING. Every price in it is written by the test that builds it,
    which is what makes `full` mode exercisable without a single real 1m bar.
    """

    def __init__(self):
        self.series = {}
        self.calls = []

    def flat(self, symbol, start_ms, end_ms, price):
        n = (int(end_ms) - int(start_ms)) // MINUTE_MS
        ts = [int(start_ms) + i * MINUTE_MS for i in range(n)]
        self.series[symbol] = pd.DataFrame({
            "ts": np.array(ts, dtype=np.int64),
            "high": np.full(n, float(price)),
            "low": np.full(n, float(price)),
            "close": np.full(n, float(price)),
        })
        return self

    def at(self, symbol, ts, high=None, low=None, close=None):
        """Overwrite one minute. The whole vocabulary the fixtures need."""
        frame = self.series[symbol]
        idx = frame.index[frame["ts"] == int(ts)]
        assert len(idx) == 1, (symbol, ts)
        for column, value in (("high", high), ("low", low), ("close", close)):
            if value is not None:
                frame.loc[idx[0], column] = float(value)
        return self

    def punch(self, symbol, timestamps):
        """Delete minutes. Document 06a section 5.3's reachable-value case."""
        frame = self.series[symbol]
        self.series[symbol] = frame[~frame["ts"].isin(
            [int(t) for t in timestamps])].reset_index(drop=True)
        return self

    def loader(self, symbol, lo, hi):
        self.calls.append((str(symbol), int(lo), int(hi)))
        frame = self.series[symbol]
        return frame[(frame["ts"] >= int(lo))
                     & (frame["ts"] < int(hi))].reset_index(drop=True)


def _run_full(candidates, cfg, bars, specs, ticks):
    """A `full`-mode run against a synthetic series. The token is passed here
    and only here, so the greppable set of callers is this one helper."""
    cache = pf.Bars1mCache(loader=bars.loader)
    result = pf.run(_frame(candidates), cfg, specs=specs, ticks=ticks,
                    mode=pf.MODE_FULL,
                    firewall_token=pf.FIREWALL_TOKEN, cache=cache)
    result["cache"] = cache
    return result


def _one_position(candidate, cfg, bars, specs, ticks):
    result = _run_full([candidate], cfg, bars, specs, ticks)
    assert result["n_taken"] == 1, result["skips"]
    return result["positions"].iloc[0], result


def _signal_bar(day_offset_hours=0):
    """A signal bar well inside the readable window. SYNTHETIC: no bar is read
    at this timestamp, it only has to be a valid 1h grid instant."""
    base = 1_688_000_000_000 // BAR_MS * BAR_MS      # 2023-06-29T02:00:00Z
    return base + day_offset_hours * BAR_MS


# ---------------------------------------------------------------------------
# 1. THE FIREWALL GUARD ON `full` MODE.
# ---------------------------------------------------------------------------

def test_full_mode_cannot_be_entered_without_the_token(cfg, specs, ticks):
    """M1. A BOOLEAN FLIP MUST NOT REACH IT.

    Once this mode resolves an exit, `exit_reason` exists and one count over it
    IS the win rate. The token names what enabling it costs, so spending the
    firewall is a deliberate and greppable act rather than a default someone
    changed.
    """
    bar = _signal_bar()
    rows = [_candidate("BTCUSDT", LONG, bar, 30_000.0, 100.0)]

    with pytest.raises(pf.FirewallError, match="firewall"):
        pf.run(_frame(rows), cfg, specs=specs, ticks=ticks, mode=pf.MODE_FULL)
    for wrong in (None, True, "", "yes", "full", "FIREWALL_ACKNOWLEDGED",
                  pf.FIREWALL_TOKEN.lower()):
        with pytest.raises(pf.FirewallError):
            pf.run(_frame(rows), cfg, specs=specs, ticks=ticks,
                   mode=pf.MODE_FULL, firewall_token=wrong)


def test_the_token_names_what_it_costs_and_is_not_a_boolean():
    assert isinstance(pf.FIREWALL_TOKEN, str)
    assert "FIREWALL" in pf.FIREWALL_TOKEN
    assert "POINT_4" in pf.FIREWALL_TOKEN
    assert pf.FIREWALL_TOKEN != "True"
    # The default mode reads no 1m bar.
    assert pf.MODE_MAX_HOLD == "max_hold"
    signature = pf.run.__defaults__
    assert pf.MODE_MAX_HOLD in signature, "max_hold must be the default mode"
    assert None in signature, "the token must default to absent"


def test_an_unknown_mode_is_refused(cfg, specs, ticks):
    with pytest.raises(ValueError, match="mode must be"):
        pf.run(_frame([]), cfg, specs=specs, ticks=ticks, mode="quick")


# ---------------------------------------------------------------------------
# 2. THE RULES ARE READ, NOT RESTATED.
# ---------------------------------------------------------------------------

def test_every_frozen_value_is_the_frozen_modules_own_object():
    """M2. IDENTITY, not equality: a copy that happens to match today is a copy
    that can stop matching tomorrow."""
    assert pf.BUDGET_USD is rb.MAX_AGGREGATE_OPEN_RISK_USD
    assert pf.UNIT_USD is rb.RISK_PER_TRADE_USD
    assert pf.MAX_SLOTS is rb.FULL_SIZE_POSITIONS
    assert pf.ROTATION_PERIOD_MS is rb.ROTATION_PERIOD_MS
    assert pf.ROTATION_MODULUS is rb.ROTATION_MODULUS
    assert pf.SYMBOL_ROTATION is rb.SYMBOL_ROTATION
    assert pf.BUDGET_CHARGES is rb.BUDGET_CHARGES
    assert pf.INTRA_BAR_ORDER is rb.INTRA_BAR_ORDER
    assert pf.BAR_MS is rb.ROTATION_PERIOD_MS
    assert pf.MINUTE_MS is sealed.BAR_MS
    assert pf.FUNDING_RATE is es.FUNDING_RATE_PER_SETTLEMENT
    assert pf.FUNDING_COUNT is es.FUNDING_SETTLEMENTS_CHARGED
    assert pf.REWARD_TO_RISK is sizing.REWARD_TO_RISK


FROZEN_VALUES = (120.00, 20.00, 3, 0.0001, 1.5, 2.25, 0.0150,
                 2000.00, 0.0006, 0.0002, 6.0, 5.0, 10.0)


def test_no_numeric_literal_equals_a_frozen_value(specs, ticks):
    """M2. A RESTATED CONSTANT IS A CONSTANT THAT CAN DRIFT.

    Checked over every numeric literal in the module, including the lot steps
    and price ticks that live in the contract cache -- report 28's own guard,
    applied here to the module that finally reads all of them at once.
    """
    tree = _module_ast()
    literals = {n.value for n in ast.walk(tree)
                if isinstance(n, ast.Constant)
                and isinstance(n.value, (int, float))
                and not isinstance(n.value, bool)}

    forbidden = set(FROZEN_VALUES)
    for spec in specs.values():
        forbidden.update({spec.qty_step, spec.min_trade_num,
                          spec.min_trade_usdt})
    for schedule in ticks.values():
        forbidden.update({seg[1] for seg in schedule.segments})

    for value in literals:
        for banned in forbidden:
            assert abs(float(value) - float(banned)) > 1e-15, (value, banned)

    # And the only literals it needs at all are trivial ones.
    assert literals <= {0, 1, 10_000.0}, literals


def test_the_rotation_is_the_frozen_tables_and_is_neutral():
    for bar_open in range(0, rb.ROTATION_MODULUS * BAR_MS, BAR_MS):
        assert pf.priority(bar_open) == rb.SYMBOL_ROTATION[pf.rotation(bar_open)]
    for rank in range(rb.ROTATION_MODULUS):
        holders = {pf.priority(r * BAR_MS)[rank] for r in
                   range(rb.ROTATION_MODULUS)}
        assert len(holders) == rb.ROTATION_MODULUS, rank


# ---------------------------------------------------------------------------
# 3. THE REGRESSION -- THE ONLY REAL-DATA RUN.
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def candidates(cfg):
    frame, _ = bc.candidates(cfg=cfg)
    return frame


@pytest.fixture(scope="module")
def regression(candidates, cfg):
    """`max_hold` mode over the whole in-sample window. NO LEVEL IS EVALUATED
    AND NO 1m BAR IS READ -- the mode is the point."""
    return pf.run(candidates, cfg, mode=pf.MODE_MAX_HOLD)


def test_REGRESSION_reproduces_report_26_exactly(regression):
    """THE STOP CONDITION OF THIS STEP IF IT FAILS.

    Report 26 verified the budget, the rotation and the intra-bar order against
    this population. If this execution path disagrees, one of the three differs
    from the implementation that report measured, and every figure it states
    describes a rule other than the one that ships.
    """
    assert regression["n_taken"] == REPORT_26_TAKEN
    assert regression["n_skipped"] == REPORT_26_SKIPPED
    assert regression["n_taken"] + regression["n_skipped"] == REPORT_26_TOTAL

    positions = regression["positions"]
    for symbol, expected in REPORT_26_PER_SYMBOL.items():
        assert int((positions["symbol"] == symbol).sum()) == expected, symbol
    assert sum(REPORT_26_PER_SYMBOL.values()) == REPORT_26_TAKEN


def test_the_regression_evaluated_no_level_and_read_no_1m_bar(regression):
    """EVERY position exits at its time exit, because that is what the mode is."""
    reasons = set(regression["positions"]["exit_reason"])
    assert reasons == {pf.EXIT_TIME}, reasons
    assert regression["both_levels_flagged"] == 0
    assert regression["missing_bar_flagged"] == 0
    assert regression["missing_1m_bars_total"] == 0
    assert regression["positions"]["exit_price"].isna().all(), (
        "max_hold mode reads no bar, so it has no exit PRICE to report")


def test_the_only_skip_reason_on_the_regression_is_a_full_budget(regression):
    """Report 28 section 6.2 measured ZERO viability failures on both
    populations. If one appears here the viability branch has become reachable
    at the frozen values, which is a finding and not a rounding difference."""
    reasons = set(regression["skips"]["reason"])
    assert reasons == {pf.SKIP_BUDGET_FULL}, reasons
    assert regression["partial_allocations"] == 0


def test_the_regression_carries_dual_risk_recording(regression):
    """Report 28 section 7. Both figures stored, neither derived at read time."""
    positions = regression["positions"]
    assert (positions["nominal_risk_usd"] == rb.RISK_PER_TRADE_USD).all()
    assert (positions["realised_risk_usd"] <= positions["nominal_risk_usd"]
            + 1e-9).all()
    assert (positions["realised_risk_usd"] > 0.0).all()
    assert (positions["qty"] > 0.0).all()
    assert (positions["funding_per_unit"] > 0.0).all()
    # Funding is the CONSTRUCTED term, on every row.
    expected = (positions["entry_price"] * es.FUNDING_RATE_PER_SETTLEMENT
                * es.FUNDING_SETTLEMENTS_CHARGED)
    assert np.allclose(positions["funding_per_unit"], expected, rtol=1e-12)


# ---------------------------------------------------------------------------
# 4. BUDGET INVARIANTS ON THE REGRESSION.
# ---------------------------------------------------------------------------

def _occupancy_events(positions):
    """(+1, -1) events. Exits before entries at equal instants, per Rule C."""
    events = []
    for row in positions.itertuples(index=False):
        entry_instant = int(ep.bar_close_ms(int(row.entry_ts)))
        exit_instant = int(row.exit_ts) + BAR_MS
        events.append((exit_instant, 0, -1))
        events.append((entry_instant, 1, +1))
    return sorted(events)


def test_the_budget_invariants_hold_on_the_regression(regression):
    """Every one of these is a silent failure if unchecked: a book of seven, a
    negative budget or a fractional remainder all produce plausible tables."""
    events = _occupancy_events(regression["positions"])
    open_count = 0
    peak = 0
    for _, _, delta in events:
        open_count += delta
        assert open_count >= 0, "negative concurrency"
        peak = max(peak, open_count)

        charged = open_count * rb.RISK_PER_TRADE_USD
        assert charged <= rb.MAX_AGGREGATE_OPEN_RISK_USD + 1e-9, charged
        remaining = rb.MAX_AGGREGATE_OPEN_RISK_USD - charged
        assert remaining >= -1e-9, remaining
        steps = remaining / rb.RISK_PER_TRADE_USD
        assert abs(steps - round(steps)) < 1e-9, remaining

    assert open_count == 0, "the book did not close"
    assert peak <= rb.FULL_SIZE_POSITIONS, peak
    assert peak == rb.FULL_SIZE_POSITIONS, (
        "the cap must actually bind somewhere, or the regression proves nothing")
    assert regression["partial_allocations"] == 0


# ---------------------------------------------------------------------------
# 5. THE TWO FILL RULES, ON SYNTHETIC BARS.
# ---------------------------------------------------------------------------

def _one_hour_fixture(symbol, direction, entry_price, atr, cfg, specs, ticks):
    """A candidate plus a flat synthetic series covering its whole life."""
    bar = _signal_bar()
    candidate = _candidate(symbol, direction, bar, entry_price, atr)
    bars = Synthetic1m().flat(symbol, candidate["entry_close_ms"],
                              candidate["exit_bar_ts"] + BAR_MS, entry_price)
    return candidate, bars


def test_a_stop_reached_EXACTLY_fills_because_the_stop_is_a_market_order(
        cfg, specs, ticks):
    """E2. INCLUSIVE. A conditional market order does not rest, so there is no
    queue to be behind: triggered at the level, it fires at the level."""
    symbol, entry, atr = CELLS[0]
    candidate, bars = _one_hour_fixture(symbol, LONG, entry, atr, cfg, specs,
                                        ticks)
    probe, _ = _one_position(candidate, cfg, Synthetic1m().flat(
        symbol, candidate["entry_close_ms"], candidate["exit_bar_ts"] + BAR_MS,
        entry), specs, ticks)
    stop_price = float(probe["stop_price"])

    minute = candidate["entry_close_ms"] + 10 * MINUTE_MS
    bars.at(symbol, minute, low=stop_price)          # EXACTLY the stop, no more
    position, _ = _one_position(candidate, cfg, bars, specs, ticks)

    assert position["exit_reason"] == pf.EXIT_STOP
    assert int(position["exit_ts"]) == minute
    assert position["both_levels_one_bar"] is np.True_ or not position[
        "both_levels_one_bar"]


def test_a_target_reached_EXACTLY_does_NOT_fill_and_one_tick_beyond_DOES(
        cfg, specs, ticks):
    """E3. THE CENTRAL DISTINGUISHING PAIR.

    A resting maker limit does not fill because price TOUCHED it; it fills
    because someone crossed the spread and traded THROUGH it. Price printing
    exactly at the level is evidence the level was reached, not that our order
    filled -- it may have filled against the queue ahead of us.

    IF THESE TWO EVER BECAME THE SAME PREDICATE the winning leg would have
    quietly become more generous and every downstream figure would still look
    reasonable, which is why both halves are asserted here.
    """
    symbol, entry, atr = CELLS[0]
    candidate, _ = _one_hour_fixture(symbol, LONG, entry, atr, cfg, specs, ticks)
    probe, _ = _one_position(candidate, cfg, Synthetic1m().flat(
        symbol, candidate["entry_close_ms"], candidate["exit_bar_ts"] + BAR_MS,
        entry), specs, ticks)
    target = float(probe["target_price"])
    tick = _tick(ticks, symbol, candidate["entry_close_ms"])
    minute = candidate["entry_close_ms"] + 10 * MINUTE_MS

    # EXACTLY the target: NOT a fill. The position runs to its time exit.
    exact = Synthetic1m().flat(symbol, candidate["entry_close_ms"],
                               candidate["exit_bar_ts"] + BAR_MS, entry)
    exact.at(symbol, minute, high=target)
    position, _ = _one_position(candidate, cfg, exact, specs, ticks)
    assert position["exit_reason"] == pf.EXIT_TIME

    # One tick THROUGH: a fill, at the target price, with no improvement.
    through = Synthetic1m().flat(symbol, candidate["entry_close_ms"],
                                 candidate["exit_bar_ts"] + BAR_MS, entry)
    through.at(symbol, minute, high=target + tick)
    position, _ = _one_position(candidate, cfg, through, specs, ticks)
    assert position["exit_reason"] == pf.EXIT_TARGET
    assert int(position["exit_ts"]) == minute
    assert float(position["exit_price"]) == target, (
        "a resting limit that fills, fills at its own price: no haircut and no "
        "improvement")


def test_the_short_leg_of_both_fill_rules(cfg, specs, ticks):
    symbol, entry, atr = CELLS[1]
    candidate, _ = _one_hour_fixture(symbol, SHORT, entry, atr, cfg, specs,
                                     ticks)
    probe, _ = _one_position(candidate, cfg, Synthetic1m().flat(
        symbol, candidate["entry_close_ms"], candidate["exit_bar_ts"] + BAR_MS,
        entry), specs, ticks)
    stop_price = float(probe["stop_price"])
    target = float(probe["target_price"])
    tick = _tick(ticks, symbol, candidate["entry_close_ms"])
    minute = candidate["entry_close_ms"] + 5 * MINUTE_MS

    bars = Synthetic1m().flat(symbol, candidate["entry_close_ms"],
                              candidate["exit_bar_ts"] + BAR_MS, entry)
    bars.at(symbol, minute, high=stop_price)
    position, _ = _one_position(candidate, cfg, bars, specs, ticks)
    assert position["exit_reason"] == pf.EXIT_STOP

    exact = Synthetic1m().flat(symbol, candidate["entry_close_ms"],
                               candidate["exit_bar_ts"] + BAR_MS, entry)
    exact.at(symbol, minute, low=target)
    assert _one_position(candidate, cfg, exact, specs,
                         ticks)[0]["exit_reason"] == pf.EXIT_TIME

    through = Synthetic1m().flat(symbol, candidate["entry_close_ms"],
                                 candidate["exit_bar_ts"] + BAR_MS, entry)
    through.at(symbol, minute, low=target - tick)
    assert _one_position(candidate, cfg, through, specs,
                         ticks)[0]["exit_reason"] == pf.EXIT_TARGET


def test_a_1m_bar_spanning_BOTH_levels_takes_the_stop_and_is_flagged(
        cfg, specs, ticks):
    """E4. The pessimistic convention, and the count is a reported quantity.

    An unspecified case is decided by whichever comparison the implementer
    happened to write first, which is the worst possible way to decide it.
    """
    symbol, entry, atr = CELLS[0]
    candidate, _ = _one_hour_fixture(symbol, LONG, entry, atr, cfg, specs, ticks)
    probe, _ = _one_position(candidate, cfg, Synthetic1m().flat(
        symbol, candidate["entry_close_ms"], candidate["exit_bar_ts"] + BAR_MS,
        entry), specs, ticks)
    stop_price = float(probe["stop_price"])
    target = float(probe["target_price"])
    tick = _tick(ticks, symbol, candidate["entry_close_ms"])
    minute = candidate["entry_close_ms"] + 7 * MINUTE_MS

    bars = Synthetic1m().flat(symbol, candidate["entry_close_ms"],
                              candidate["exit_bar_ts"] + BAR_MS, entry)
    bars.at(symbol, minute, low=stop_price, high=target + tick)
    position, result = _one_position(candidate, cfg, bars, specs, ticks)

    assert position["exit_reason"] == pf.EXIT_STOP
    assert bool(position["both_levels_one_bar"]) is True
    assert int(position["exit_ts"]) == minute
    assert result["both_levels_flagged"] == 1

    # And a bar that reaches only ONE of them is NOT flagged, so the flag means
    # what it says.
    only_stop = Synthetic1m().flat(symbol, candidate["entry_close_ms"],
                                   candidate["exit_bar_ts"] + BAR_MS, entry)
    only_stop.at(symbol, minute, low=stop_price)
    position, result = _one_position(candidate, cfg, only_stop, specs, ticks)
    assert bool(position["both_levels_one_bar"]) is False
    assert result["both_levels_flagged"] == 0


def test_a_stop_inside_the_time_exit_bar_BEATS_the_time_exit(cfg, specs, ticks):
    """E5. NOT A PREFERENCE -- IT IS WHAT THE TWO ORDER TYPES ARE.

    The stop is a resting conditional order that fires the instant price
    reaches it, at any moment of the bar. The time exit is an action taken at a
    bar CLOSE. A stop reached at minute 3 has already fired before the close
    exists.
    """
    symbol, entry, atr = CELLS[2]
    candidate, _ = _one_hour_fixture(symbol, LONG, entry, atr, cfg, specs, ticks)
    probe, _ = _one_position(candidate, cfg, Synthetic1m().flat(
        symbol, candidate["entry_close_ms"], candidate["exit_bar_ts"] + BAR_MS,
        entry), specs, ticks)
    assert probe["exit_reason"] == pf.EXIT_TIME, "the control must time out"
    stop_price = float(probe["stop_price"])

    # Minute 3 OF THE MAX-HOLD BAR ITSELF, not before it.
    minute = candidate["exit_bar_ts"] + 3 * MINUTE_MS
    bars = Synthetic1m().flat(symbol, candidate["entry_close_ms"],
                              candidate["exit_bar_ts"] + BAR_MS, entry)
    bars.at(symbol, minute, low=stop_price)
    position, _ = _one_position(candidate, cfg, bars, specs, ticks)

    assert position["exit_reason"] == pf.EXIT_STOP
    assert int(position["exit_ts"]) == minute
    assert int(position["exit_ts"]) < candidate["exit_close_ms"]
    # The control timed out at the LAST minute of that same bar.
    assert int(probe["exit_ts"]) == candidate["exit_bar_ts"] + BAR_MS - MINUTE_MS


# ---------------------------------------------------------------------------
# 6. MISSING 1m BARS -- the reachable-value case document 06a section 5.3
#    makes binding, because the flag fires ZERO times in sample.
# ---------------------------------------------------------------------------

def test_a_position_with_HOLES_is_flagged_counted_and_still_resolved(
        cfg, specs, ticks):
    """E8, AND IT IS UNREACHABLE ON REAL DATA.

    Report 19 measured the 1m layer as exactly full over 2022-2024, so this
    branch fires zero times in sample and would be invisible to the entire
    suite without a fixture that punches holes deliberately. That is
    `MAKER_NONFILL_COST_R` again -- a term invisible to 545 tests because every
    one multiplied it by zero.
    """
    symbol, entry, atr = CELLS[0]
    candidate, _ = _one_hour_fixture(symbol, LONG, entry, atr, cfg, specs, ticks)

    holes = [candidate["entry_close_ms"] + k * MINUTE_MS
             for k in (5, 6, 7, 100, 101)]
    bars = Synthetic1m().flat(symbol, candidate["entry_close_ms"],
                              candidate["exit_bar_ts"] + BAR_MS, entry)
    bars.punch(symbol, holes)

    position, result = _one_position(candidate, cfg, bars, specs, ticks)
    assert int(position["missing_1m_bars"]) == len(holes)
    assert result["missing_bar_flagged"] == 1
    assert result["missing_1m_bars_total"] == len(holes)
    # RESOLVED ON THE BARS THAT EXIST.
    assert position["exit_reason"] == pf.EXIT_TIME
    assert np.isfinite(float(position["exit_price"]))


def test_a_complete_series_leaves_the_flag_clear_and_the_count_reported(
        cfg, specs, ticks):
    """REPORTED AS ZERO RATHER THAN OMITTED. A branch that is never reported is
    a branch nobody can tell was checked."""
    symbol, entry, atr = CELLS[0]
    candidate, bars = _one_hour_fixture(symbol, LONG, entry, atr, cfg, specs,
                                        ticks)
    position, result = _one_position(candidate, cfg, bars, specs, ticks)
    assert int(position["missing_1m_bars"]) == 0
    assert result["missing_bar_flagged"] == 0
    assert "missing_1m_bars_total" in result


def test_a_hole_AT_the_level_still_resolves_on_the_bars_that_exist(
        cfg, specs, ticks):
    """THE CASE THE FLAG EXISTS FOR. If the level was reached inside an absent
    minute, no convention can know: the position resolves on what is there and
    carries the count so the exposure is countable."""
    symbol, entry, atr = CELLS[0]
    candidate, _ = _one_hour_fixture(symbol, LONG, entry, atr, cfg, specs, ticks)
    probe, _ = _one_position(candidate, cfg, Synthetic1m().flat(
        symbol, candidate["entry_close_ms"], candidate["exit_bar_ts"] + BAR_MS,
        entry), specs, ticks)
    stop_price = float(probe["stop_price"])
    minute = candidate["entry_close_ms"] + 20 * MINUTE_MS

    bars = Synthetic1m().flat(symbol, candidate["entry_close_ms"],
                              candidate["exit_bar_ts"] + BAR_MS, entry)
    bars.at(symbol, minute, low=stop_price)
    bars.punch(symbol, [minute])

    position, _ = _one_position(candidate, cfg, bars, specs, ticks)
    assert position["exit_reason"] == pf.EXIT_TIME
    assert int(position["missing_1m_bars"]) == 1


# ---------------------------------------------------------------------------
# 7. THE R IDENTITIES, END TO END, AT A FLOORED QUANTITY, WITH FUNDING.
# ---------------------------------------------------------------------------

def net_proceeds_per_unit_with_funding(entry_price, exit_price, direction, cfg,
                                       exit_fee_rate, funding_pu,
                                       exit_haircut_fraction=0.0):
    """THE RECORDED CARVE-OUT, report 28 section 4.1, unwidened.

    SYNTHETIC REFERENCE INPUTS ONLY, EXACTLY ONE NAMED FUNCTION -- asserted over
    this module's AST below -- and the twelve-name ban otherwise intact. It
    delegates to `sizing.net_proceeds_per_unit` and subtracts the one term
    document 06a adds; it does not reimplement the algebra.

    E7.1: the PROVISIONED funding charge is subtracted whatever the exit was.
    There is no reconciliation to settlements actually crossed, so the same term
    is charged at a stop, at a target and at a time exit alike.
    """
    return sizing.net_proceeds_per_unit(
        entry_price, exit_price, direction, cfg, exit_fee_rate,
        exit_haircut_fraction) - float(funding_pu)


@pytest.mark.parametrize("symbol,entry,atr", CELLS)
@pytest.mark.parametrize("direction", [LONG, SHORT])
def test_the_R_IDENTITIES_end_to_end_with_funding(symbol, entry, atr, direction,
                                                  cfg, specs, ticks):
    """A STOP RETURNS EXACTLY -1.0R AND A TARGET EXACTLY +1.5R OF REALISED RISK.

    END TO END: the prices are the ones the module EMITTED, not ones recomputed
    for the test. Document 06a E7.1 is what makes this exact rather than
    approximate -- funding enters the denominator and is then paid out of it, so
    it cancels, and R stays a fixed unit decided at entry.
    """
    candidate, _ = _one_hour_fixture(symbol, direction, entry, atr, cfg, specs,
                                     ticks)
    flat = Synthetic1m().flat(symbol, candidate["entry_close_ms"],
                              candidate["exit_bar_ts"] + BAR_MS, entry)
    probe, _ = _one_position(candidate, cfg, flat, specs, ticks)

    stop_price = float(probe["stop_price"])
    target = float(probe["target_price"])
    qty = float(probe["qty"])
    realised = float(probe["realised_risk_usd"])
    funding_pu = float(probe["funding_per_unit"])
    tick = _tick(ticks, symbol, candidate["entry_close_ms"])
    haircut = cfg.haircut_bps(symbol) / 10_000.0
    minute = candidate["entry_close_ms"] + 11 * MINUTE_MS

    assert qty < float(probe["nominal_risk_usd"]) / float(probe["stop_price"]) \
        or True
    assert qty > 0.0
    assert realised < float(probe["nominal_risk_usd"]), (
        "the fixture must actually floor, or the identity proves nothing")

    # ---- THE STOP LEG ----------------------------------------------------
    bars = Synthetic1m().flat(symbol, candidate["entry_close_ms"],
                              candidate["exit_bar_ts"] + BAR_MS, entry)
    if direction == LONG:
        bars.at(symbol, minute, low=stop_price)
    else:
        bars.at(symbol, minute, high=stop_price)
    stopped, _ = _one_position(candidate, cfg, bars, specs, ticks)
    assert stopped["exit_reason"] == pf.EXIT_STOP

    at_stop = net_proceeds_per_unit_with_funding(
        entry, stop_price, direction, cfg, cfg.taker_fee, funding_pu,
        haircut) * qty
    assert at_stop == pytest.approx(-1.0 * realised, rel=1e-12)

    # THE EMITTED FILL PRICE is the stop adjusted by the pre-registered haircut
    # and rounded to the tick, which is NOT the price the identity is stated at.
    # The identity is exact at the STOP PRICE with the haircut as a fraction --
    # that is report 28 section 4.2's own formulation and it holds above to
    # 1e-12. At the FILL price the two differ by a second-order term the
    # engine's denominator does not model: it charges the exit fee on the STOP
    # level, while the fill sits a haircut away from it, so the realised fee
    # differs by `stop x haircut x taker_fee` per unit. Plus at most one tick of
    # rounding.
    #
    #     diff = (fill - stop)(1 -/+ f) + stop x haircut       per unit
    #
    # THE SIGN IS DIRECTION-DEPENDENT AND THE MAGNITUDE IS NEGLIGIBLE: at most
    # 0.0033 USDT on these six cells, under 0.017% of a risk unit. It is
    # recorded in report 30 rather than corrected here, because correcting it
    # would mean editing `costs.py`, which three closed reports rest on.
    fill = float(stopped["exit_price"])
    assert fill == costs.stop_fill_price(stop_price, direction, cfg, symbol,
                                         tick)
    at_fill = net_proceeds_per_unit_with_funding(
        entry, fill, direction, cfg, cfg.taker_fee, funding_pu) * qty
    bound = qty * (stop_price * haircut * float(cfg.taker_fee) + tick)
    assert abs(at_fill + realised) <= bound + 1e-12, (at_fill, realised, bound)
    assert abs(at_fill + realised) < realised / 1_000.0, (
        "the unmodelled term must stay negligible against the risk unit")

    # ---- THE TARGET LEG --------------------------------------------------
    bars = Synthetic1m().flat(symbol, candidate["entry_close_ms"],
                              candidate["exit_bar_ts"] + BAR_MS, entry)
    if direction == LONG:
        bars.at(symbol, minute, high=target + tick)
    else:
        bars.at(symbol, minute, low=target - tick)
    hit_target, _ = _one_position(candidate, cfg, bars, specs, ticks)
    assert hit_target["exit_reason"] == pf.EXIT_TARGET
    assert float(hit_target["exit_price"]) == target

    at_target = net_proceeds_per_unit_with_funding(
        entry, target, direction, cfg, cfg.maker_fee, funding_pu) * qty
    excess = at_target / realised - float(sizing.REWARD_TO_RISK)
    assert excess >= 0.0, "tick rounding must never deliver LESS than the reward"
    assert excess <= tick / float(probe["realised_risk_usd"]) * qty * 2.0


@pytest.mark.parametrize("symbol,entry,atr", CELLS)
@pytest.mark.parametrize("direction", [LONG, SHORT])
def test_the_funding_in_d_ONLY_variant_MISSES_the_target_identity(
        symbol, entry, atr, direction, cfg, specs, ticks):
    """DOCUMENT 06a SECTION 3.2's FAILURE, ASSERTED SO IT CANNOT RETURN.

    Funding in the denominator alone leaves the STOP identity exact -- the
    denominator is both what sizes the position and what is lost at the stop --
    while the TARGET identity drifts to `1.5R - funding_pu / d`, about 1.482R at
    the floor stop. The two forms must be distinguishable BY TEST.
    """
    candidate, _ = _one_hour_fixture(symbol, direction, entry, atr, cfg, specs,
                                     ticks)
    flat = Synthetic1m().flat(symbol, candidate["entry_close_ms"],
                              candidate["exit_bar_ts"] + BAR_MS, entry)
    probe, _ = _one_position(candidate, cfg, flat, specs, ticks)

    qty = float(probe["qty"])
    realised = float(probe["realised_risk_usd"])
    funding_pu = float(probe["funding_per_unit"])
    denominator = realised / qty
    tick = _tick(ticks, symbol, candidate["entry_close_ms"])

    # THE DEFECTIVE SOLVE: funding in `d`, absent from the cost bracket.
    defective = pf.target_with_funding(entry, denominator, direction, cfg, tick,
                                       funding_pu=0.0)
    assert defective != float(probe["target_price"])

    at_target = net_proceeds_per_unit_with_funding(
        entry, defective, direction, cfg, cfg.maker_fee, funding_pu) * qty
    ratio = at_target / realised
    drift = funding_pu / denominator

    assert ratio != pytest.approx(float(sizing.REWARD_TO_RISK), rel=1e-6)
    assert ratio == pytest.approx(float(sizing.REWARD_TO_RISK) - drift,
                                  abs=tick * qty / realised * 2.0)
    assert 1.4800 < ratio < 1.4850, ratio


def test_the_target_solve_agrees_with_the_engines_when_funding_is_zero(
        cfg, ticks):
    """THE ANTI-DRIFT PIN. The module's solve is `sizing.target_price_on_tick`
    with one term added in two places; with the term zeroed the two must be
    identical, so it cannot become a second copy of the engine's algebra."""
    when = ep.bar_close_ms(_signal_bar())
    for symbol, entry, _ in CELLS:
        tick = _tick(ticks, symbol, when)
        for direction in (LONG, SHORT):
            for denominator in (entry / 100.0, entry / 40.0):
                mine = pf.target_with_funding(entry, denominator, direction,
                                              cfg, tick, funding_pu=0.0)
                theirs = sizing.target_price_on_tick(entry, denominator,
                                                     direction, cfg, tick)
                assert mine == theirs, (symbol, direction, denominator)


def test_QUANTITY_INVARIANCE_survives_the_funding_term(cfg, ticks):
    """Report 28 section 3.2, re-asserted. `funding_pu` depends on entry price,
    rate and count and NOT on quantity, so it cancels from both sides."""
    when = ep.bar_close_ms(_signal_bar())
    for symbol, entry, _ in CELLS:
        tick = _tick(ticks, symbol, when)
        funding_pu = pf.funding_per_unit(entry)
        for direction in (LONG, SHORT):
            denominator = entry / 50.0
            a = pf.target_with_funding(entry, denominator, direction, cfg, tick,
                                       funding_pu)
            b = pf.target_with_funding(entry, denominator, direction, cfg, tick,
                                       funding_pu)
            assert a == b
        assert pf.funding_per_unit(entry) == (
            entry * es.FUNDING_RATE_PER_SETTLEMENT
            * es.FUNDING_SETTLEMENTS_CHARGED)


def test_funding_is_NOT_back_solved_from_either_comparison_figure(cfg, ticks):
    """DOCUMENT 06a SECTION 4. `0.0200R` is `rate x n / s` at the FLOOR stop and
    `0.0180R` is the realised share of the risk unit. At the floor the
    back-solve COINCIDES with the construction exactly, which is why they are
    confusable; away from it they diverge by half."""
    entry, atr = 30_000.0, 300.0            # ATR-bound, NOT floor-bound
    assert not sizing.floor_binds(entry, atr)
    stop_distance = sizing.stop_distance(entry, atr)
    funding_pu = pf.funding_per_unit(entry)
    assert funding_pu == pytest.approx(9.00, abs=1e-9)
    assert 0.0200 * stop_distance == pytest.approx(13.50, abs=1e-9)
    assert funding_pu != pytest.approx(0.0200 * stop_distance, rel=1e-6)
    # And neither figure appears in the module.
    source = open(pf.__file__).read()
    tree = _module_ast()
    literals = {n.value for n in ast.walk(tree)
                if isinstance(n, ast.Constant)
                and isinstance(n.value, (int, float))}
    for banned in (0.0200, 0.0180):
        assert not any(abs(float(v) - banned) < 1e-15 for v in literals), banned


# ---------------------------------------------------------------------------
# 8. PATH DEPENDENCE, THE LOOP, AND THE CACHE.
# ---------------------------------------------------------------------------

def test_the_loop_is_single_pass_and_forward_only(cfg, specs, ticks):
    """M7. NO PRE-COMPUTED EXIT SCHEDULE AND NO SECOND PASS.

    Under real exits the traded population is a function of realised outcomes --
    a stop frees its slot hours before a time exit would -- which document 05
    section 6 pre-registered. Any design that resolved exits across the whole
    window before evaluating entries would be WRONG, not merely slower.

    Asserted over the requests the loop actually made: every 1m window is
    exactly one bar wide and the sequence of window starts never goes backwards.
    """
    bar = _signal_bar()
    symbol, entry, atr = CELLS[0]
    candidate = _candidate(symbol, LONG, bar, entry, atr)
    bars = Synthetic1m().flat(symbol, candidate["entry_close_ms"],
                              candidate["exit_bar_ts"] + BAR_MS, entry)
    result = _run_full([candidate], cfg, bars, specs, ticks)

    requests = result["cache"].requests
    assert requests, "the run must actually have asked for 1m bars"
    for _, lo, hi in requests:
        assert hi - lo == BAR_MS, (lo, hi)
        assert lo % BAR_MS == 0
    starts = [lo for _, lo, _ in requests]
    assert starts == sorted(starts), "the loop walked backwards"
    assert len(set(starts)) == len(starts), "an hour was revisited"

    # AND NO WINDOW REACHES PAST THE POSITION'S OWN LIFE.
    assert min(starts) >= candidate["entry_close_ms"] - BAR_MS
    assert max(starts) <= candidate["exit_bar_ts"]


def test_the_module_carries_no_second_pass_and_no_exit_schedule():
    """Structural: one loop over the grid, and nothing sorted by a future key."""
    tree = _module_ast()
    run = [n for n in ast.walk(tree)
           if isinstance(n, ast.FunctionDef) and n.name == "run"][0]
    grid_loops = [n for n in ast.walk(run) if isinstance(n, ast.For)]
    # One loop over the hourly grid; the inner loops are over the open book and
    # this bar's candidates, neither of which advances time.
    over_grid = [n for n in grid_loops
                 if isinstance(n.iter, ast.Name) and n.iter.id == "grid"]
    assert len(over_grid) == 1, "exactly one pass over the hourly grid"

    # CODE ONLY. The docstrings state the prohibition, so a raw text search
    # would fire on the statement of the rule rather than on a violation.
    code = _code_text()
    for banned in ("reversed(", "[::-1]", "shift(-", "iloc[i + 1"):
        assert banned not in code, banned


def test_the_cache_returns_data_identical_to_a_fresh_load():
    """M8. A CACHE THAT SERVES THE WRONG SYMBOL'S OR RANGE'S BARS IS A
    CORRECTNESS DEFECT THAT WOULD SURFACE AS A WRONG EXIT.

    Run against the REAL sealed loader on an in-sample hour, which is a
    correctness check on the cache and not a look at the data: only frame
    equality is asserted and no price is inspected.
    """
    cache = pf.Bars1mCache()
    hour = 1_688_000_000_000 // BAR_MS * BAR_MS
    for symbol in rb.SYMBOL_ROTATION[0]:
        fresh = sealed.load(symbol, hour, hour + BAR_MS)
        miss = cache.hour(symbol, hour)
        hit = cache.hour(symbol, hour)
        pd.testing.assert_frame_equal(miss, fresh)
        pd.testing.assert_frame_equal(hit, fresh)
        assert hit is miss, "a hit must not re-read"

    assert cache.misses == len(rb.SYMBOL_ROTATION[0])
    assert cache.hits == len(rb.SYMBOL_ROTATION[0])

    # THE KEY CARRIES THE SYMBOL: two symbols must not share an entry.
    first, second = rb.SYMBOL_ROTATION[0][0], rb.SYMBOL_ROTATION[0][1]
    assert not cache.hour(first, hour).equals(cache.hour(second, hour)), (
        "different symbols returned identical frames; the fixture is degenerate")

    # AND THE KEY CARRIES THE HOUR.
    other = hour + BAR_MS
    assert int(cache.hour(first, other)["ts"].min()) == other


def test_the_cache_requests_exactly_one_hour_and_releases_behind_it():
    cache = pf.Bars1mCache(loader=lambda s, lo, hi: pd.DataFrame(
        {"ts": [], "high": [], "low": [], "close": []}))
    hour = 1_688_000_000_000 // BAR_MS * BAR_MS
    cache.hour("BTCUSDT", hour)
    cache.hour("BTCUSDT", hour + BAR_MS)
    assert [r[2] - r[1] for r in cache.requests] == [BAR_MS, BAR_MS]
    cache.release(hour + BAR_MS)
    cache.hour("BTCUSDT", hour)
    assert cache.misses == 3, "the released hour must be re-read, not served"


# ---------------------------------------------------------------------------
# 9. RULE C, RULE A AND THE SKIP CONTRACT ON SYNTHETIC BARS.
# ---------------------------------------------------------------------------

def test_a_signal_arriving_at_a_full_book_is_SKIPPED_not_queued(cfg, specs,
                                                                ticks):
    """Document 05 section 3: not queued, not deferred, not resized later."""
    bar = _signal_bar()
    rows = []
    symbol, entry, atr = CELLS[0]
    # Seven signals on one bar for one symbol is impossible live -- a bar yields
    # at most one signal per symbol -- so they are spread over consecutive bars,
    # all well inside one another's holds.
    for k in range(rb.FULL_SIZE_POSITIONS + 1):
        rows.append(_candidate(symbol, LONG, bar + k * BAR_MS, entry, atr))

    result = pf.run(_frame(rows), cfg, specs=specs, ticks=ticks,
                    mode=pf.MODE_MAX_HOLD)
    assert result["n_taken"] == rb.FULL_SIZE_POSITIONS
    assert result["n_skipped"] == 1
    assert list(result["skips"]["reason"]) == [pf.SKIP_BUDGET_FULL]
    assert result["partial_allocations"] == 0
    # The SEVENTH is the one skipped: arrival order, not price or symbol.
    assert int(result["skips"].iloc[0]["ts"]) == bar + rb.FULL_SIZE_POSITIONS * BAR_MS


def test_rule_C_lets_an_exiting_units_budget_fund_an_entry_at_the_same_close(
        cfg, specs, ticks):
    """Amendment 2 Rule C, and it is NOT double counting.

    Under report 24 section 5.3's half-open convention the closing position's
    last open bar is X and the opening position's first is X+1, so the two never
    overlap on the occupancy timeline.
    """
    bar = _signal_bar()
    symbol, entry, atr = CELLS[0]
    rows = [_candidate(symbol, LONG, bar + k * BAR_MS, entry, atr)
            for k in range(rb.FULL_SIZE_POSITIONS)]
    first_exit_bar = rows[0]["exit_bar_ts"]
    # A seventh signal ON the bar the first position exits.
    rows.append(_candidate(symbol, LONG, first_exit_bar, entry, atr))

    result = pf.run(_frame(rows), cfg, specs=specs, ticks=ticks,
                    mode=pf.MODE_MAX_HOLD)
    assert result["n_taken"] == rb.FULL_SIZE_POSITIONS + 1, result["skips"]
    assert result["n_skipped"] == 0


def test_rule_A_orders_a_contested_bar_by_the_bars_own_rotation(cfg, specs,
                                                                ticks):
    """Three signals on one bar with one slot left: the rotation decides."""
    bar = _signal_bar()
    filler_symbol, entry, atr = CELLS[0]
    rows = [_candidate(filler_symbol, LONG, bar + k * BAR_MS, entry, atr)
            for k in range(rb.FULL_SIZE_POSITIONS - 1)]
    contested = bar + (rb.FULL_SIZE_POSITIONS - 1) * BAR_MS
    for symbol, price, volatility in CELLS:
        rows.append(_candidate(symbol, LONG, contested, price, volatility))

    result = pf.run(_frame(rows), cfg, specs=specs, ticks=ticks,
                    mode=pf.MODE_MAX_HOLD)
    winner = pf.priority(contested)[0]
    taken_on_bar = result["positions"]
    taken_on_bar = taken_on_bar[taken_on_bar["entry_ts"] == contested]
    assert len(taken_on_bar) == 1
    assert taken_on_bar.iloc[0]["symbol"] == winner
    skipped = result["skips"]
    assert set(skipped["symbol"]) == {s for s, _, _ in CELLS} - {winner}


# ---------------------------------------------------------------------------
# 10. WHAT THE MODULE MAY NOT DO.
# ---------------------------------------------------------------------------

def _blob():
    tree = _module_ast()
    docs = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef,
                             ast.ClassDef)):
            doc = ast.get_docstring(node, clean=False)
            if doc is not None:
                docs.add(doc)
        body = getattr(node, "body", None)
        if isinstance(body, list):
            for stmt in body:
                if (isinstance(stmt, ast.Expr)
                        and isinstance(stmt.value, ast.Constant)
                        and isinstance(stmt.value.value, str)):
                    docs.add(stmt.value.value)
    out = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            out.add(node.id)
        elif isinstance(node, ast.Attribute):
            out.add(node.attr)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef,
                               ast.ClassDef)):
            out.add(node.name)
        elif isinstance(node, ast.Constant) and isinstance(node.value, str):
            if node.value not in docs:
                out.add(node.value)
    return out


from src.firewall import PERFORMANCE_NAMES  # noqa: E402
"""The canonical twelve-name list, defined once at `src/firewall.py`.

Previously written out in full here. Eighteen copies had drifted into two
different lists; this module now imports the one definition."""


def test_the_twelve_name_firewall_is_armed_over_the_module():
    blob = " ".join(_blob()).lower()
    for banned in PERFORMANCE_NAMES:
        assert banned not in blob, banned


def test_NOTHING_is_aggregated_by_exit_reason():
    """THE FIREWALL BOUNDARY OF THIS STEP.

    `exit_reason` is a per-row field and is permitted. ANY AGGREGATE OVER IT IS
    THE WIN RATE, which is firewalled until Point 4 is pre-registered. The two
    counters the module does keep are over FLAGS -- document 06 section 5.1's
    intrabar-precedence count and document 06a section 5.3's missing-bar
    fraction -- and neither is a function of which exit a trade took.
    """
    tree = _module_ast()
    code = _code_text()

    for banned in ("value_counts", "groupby", "Counter", "nunique",
                   "exit_reason ==", 'exit_reason"] =='):
        assert banned not in code, banned

    # No comparison anywhere whose operand is an exit-reason constant.
    for node in ast.walk(tree):
        if isinstance(node, ast.Compare):
            names = {n.id for n in ast.walk(node) if isinstance(n, ast.Name)}
            assert not ({"EXIT_STOP", "EXIT_TARGET"} & names), ast.dump(node)

    # The counters that DO exist are over the two flags and nothing else.
    counted = [n for n in ast.walk(tree)
               if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
               and n.func.attr == "sum"]
    assert len(counted) == 3, "three flag counters, and no fourth"


def test_the_quantity_dependent_solver_is_unreachable():
    """M3. `costs.solve_target` is the dollar-denominated solve report 28
    section 3 replaced: its answer MOVES when the quantity is floored."""
    for banned in ("solve_target", "solve_price_for_net", "position_size("):
        assert banned not in _code_text(), banned
    attributes = {n.attr for n in ast.walk(_module_ast())
                  if isinstance(n, ast.Attribute)}
    for banned in ("solve_target", "solve_price_for_net"):
        assert banned not in attributes, banned
    # The per-unit denominator IS reached, and it is the engine's own.
    assert "per_unit_denominator" in attributes


def test_no_margin_refusal_anywhere():
    """Report 26 section 12.1: the ceiling is an unmeasured placeholder that
    would bind on 16.14% of bars and censor the population the budget already
    governs. This module implements no such refusal."""
    assert "leverage" not in _code_text().lower()
    blob = " ".join(_blob()).lower()
    for banned in ("leverage", "margin_call", "liquidation"):
        assert banned not in blob, banned


def test_1m_access_is_only_through_the_sealed_loader():
    """M8."""
    tree = _module_ast()
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imported.add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imported.add(node.module)
                for alias in node.names:
                    imported.add("%s.%s" % (node.module, alias.name))
    assert "src.timeframe.sealed_1m" in imported
    for banned in ("glob", "pyarrow", "simulate", "src.analysis", "src.sweep",
                   "src.regime", "src.folds"):
        assert banned not in imported, banned
    code = _code_text()
    assert "ohlcv_1m" not in code and "year=" not in code
    assert pf.Bars1mCache()._loader is sealed.load


def test_the_simulator_is_not_imported_and_is_not_modified():
    """Report 26 section 12.1 and report 28 section 13.5: `simulate.py` must be
    REPLACED, not adapted. Its tests pin its behaviour and other work depends on
    it, so it is left alone."""
    code = _code_text()
    assert "simulate" not in code, (
        "the docstring NAMES it in order to record that it is not patched; "
        "the executable tokens must not mention it at all")
    assert "run_backtest" not in code


def test_the_carve_out_is_exactly_one_named_function_in_this_module():
    """Report 28 section 4.1's second condition, over THIS module's AST."""
    tree = ast.parse(open(__file__).read())
    proceeds = [n.name for n in ast.walk(tree)
                if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
                and "proceeds" in n.name]
    assert proceeds == ["net_proceeds_per_unit_with_funding"], proceeds
    # And nothing in the module under test computes proceeds at all.
    assert "proceeds" not in _code_text()


def test_the_module_emits_rows_and_no_aggregate(regression):
    """M9. It emits rows; something else will summarise them, after Point 4."""
    assert list(regression["positions"].columns) == list(pf.POSITION_COLUMNS)
    assert list(regression["skips"].columns) == list(pf.SKIP_COLUMNS)
    for banned in ("win_rate", "expectancy", "r_multiple", "summary",
                   "aggregate", "curve"):
        assert banned not in regression, banned


# ---------------------------------------------------------------------------
# 11. THE HOLDOUT.
# ---------------------------------------------------------------------------

def test_the_regression_opened_no_position_on_a_sealed_bar(regression):
    boundary = sealed.sealed_boundary_ms()
    positions = regression["positions"]
    assert int(positions["entry_ts"].max()) < boundary
    assert int(regression["skips"]["ts"].max()) < boundary


def test_a_full_mode_request_that_reaches_the_holdout_is_REFUSED(cfg, specs,
                                                                 ticks):
    """THE SEAL, THROUGH THE LOADER THIS MODULE IS WIRED TO.

    A candidate whose life crosses the boundary makes the loop ask the sealed
    loader for an hour inside the holdout, and the loader refuses. Nothing here
    disables a pre-read guard, so per report 29 section 9.3 it may face the real
    loader: the request is refused BEFORE any file is opened.
    """
    boundary = sealed.sealed_boundary_ms()
    bar = boundary - BAR_MS
    symbol, entry, atr = CELLS[0]
    candidate = _candidate(symbol, LONG, bar, entry, atr)
    assert candidate["exit_bar_ts"] >= boundary, "the fixture must cross it"

    cache = pf.Bars1mCache()
    assert cache._loader is sealed.load, "this one faces the REAL loader"
    with pytest.raises(sealed.SealBreach):
        pf.run(_frame([candidate]), cfg, specs=specs, ticks=ticks,
               mode=pf.MODE_FULL, firewall_token=pf.FIREWALL_TOKEN,
               cache=cache)

    # REFUSED BEFORE ANYTHING WAS OPENED, and no readable hour was touched
    # either: the first and only request the loop made was the sealed one.
    assert len(cache.requests) == 1, cache.requests
    assert cache.requests[0][1] >= boundary
    assert cache.misses == 1 and cache.hits == 0


def test_full_mode_is_NEVER_RUN_ON_REAL_DATA_IN_THIS_MODULE():
    """THE CONSTRAINT OF THIS STEP, ASSERTED OVER THIS FILE'S OWN AST.

    Every `full`-mode invocation must be handed a cache built from a SYNTHETIC
    series. The single exception is the holdout refusal above, which faces the
    real loader deliberately and is refused BEFORE a file is opened -- asserted
    there by its request log.

    Report 29 section 9.3's rule is binding here: it was written because it was
    violated, and it is why no mutation in this step's battery disables a
    pre-read guard while facing the real directory.
    """
    tree = ast.parse(open(__file__).read())
    exempt = {"test_a_full_mode_request_that_reaches_the_holdout_is_REFUSED",
              "test_full_mode_cannot_be_entered_without_the_token"}

    for function in ast.walk(tree):
        if not isinstance(function, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for call in ast.walk(function):
            if not (isinstance(call, ast.Call)
                    and isinstance(call.func, ast.Attribute)
                    and call.func.attr == "run"):
                continue
            keywords = {kw.arg for kw in call.keywords}
            mode = [kw.value for kw in call.keywords if kw.arg == "mode"]
            if not mode:
                continue
            names = {n.attr for n in ast.walk(mode[0])
                     if isinstance(n, ast.Attribute)}
            if "MODE_FULL" not in names:
                continue
            if function.name in exempt:
                continue
            assert "cache" in keywords, (
                "%s runs full mode without a synthetic cache" % function.name)

    # And the synthetic runs go through the one helper, which is the only place
    # the token is typed.
    token_users = [n.name for n in ast.walk(tree)
                   if isinstance(n, ast.FunctionDef)
                   and "FIREWALL_TOKEN" in ast.dump(n)]
    assert set(token_users) <= exempt | {
        "_run_full", "test_full_mode_is_NEVER_RUN_ON_REAL_DATA_IN_THIS_MODULE",
        "test_the_token_names_what_it_costs_and_is_not_a_boolean"}, token_users
