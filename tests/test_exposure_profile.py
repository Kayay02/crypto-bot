"""Guards for the maximum-hold exposure profile.

THREE THINGS HERE CAN BE WRONG WITHOUT ANYTHING RAISING, and each has a test
built against it rather than around it.

THE SETTLEMENT INDEX. `n = 3` is denominated in FUNDING SETTLEMENTS, not bars.
An off-by-one produces holds of 8 or 32 hours -- both perfectly plausible
numbers, both of which would leave every occupancy figure looking reasonable and
every one of them wrong by a factor. The band is asserted directly, at the two
extremes of the 8-hour cycle, and on every position in the real measurement.

THE OCCUPANCY INTERVAL. A position opened at the close of bar T is open on bars
T+1 .. X, not T .. X and not T+1 .. X-1. Each of the three readings differs from
the others by one bar per position, which on 11,000 positions moves every mean
and every histogram while changing no maximum and breaking no invariant. The
positive control is hand-computed bar by bar so the convention is pinned by
arithmetic rather than by agreement with itself.

THE EMPTY RESULT. Report 20's headline was an empty population and report 21's
trigger could have been emptied by a single off-by-one in the Donchian shift.
The same applies to an occupancy timeline: an all-zero one is what both a
correct empty book and a broken detector look like. The positive control
constructs THREE OVERLAPPING POSITIONS at known timestamps and asserts the
timeline bar for bar; the negative control constructs a series that cannot fire
and asserts the timeline is zero everywhere.
"""

import ast
import datetime as dt
import os
import sys

import numpy as np
import pandas as pd
import pytest

from src.analysis import exposure_profile as ep
from src.analysis import sweep_population as sp
from src.folds import schedule as sch
from src.timeframe import resample as rs

sys.path.insert(0, os.path.join(rs.ROOT, "src", "engine"))

import costs  # noqa: E402


HOUR_MS = 3_600_000
T0 = 1_640_995_200_000  # the first bar of the window, 00:00:00Z


def _frame(high, low, close, t0=T0):
    high = np.asarray(high, dtype=float)
    return pd.DataFrame({
        "ts": t0 + np.arange(len(high)) * HOUR_MS,
        "high": high,
        "low": np.asarray(low, dtype=float),
        "close": np.asarray(close, dtype=float),
    })


def _flat(n, high=101.0, low=99.0, close=100.0):
    """`n` bars with a true range of exactly 2.0, so ATR settles at exactly 2.0.

    Report 21's fixture, reused. The bar range dominates every true range, so
    Wilder's ATR is 2.0 from the seed onward -- exact, not asymptotic.
    """
    return [high] * n, [low] * n, [close] * n


def _with_sweeps(n, sweeps, t0=T0):
    """`n` flat bars with hand-placed LONG sweep bars at given indices.

    `sweeps` is {index: (low, close)}. The high is left at the flat 101.0 so no
    bar can also break the upper channel: 101 is not STRICTLY greater than the
    prior-10 maximum of 101, so no short signal is possible anywhere in the
    series and the population is exactly the placed sweeps.
    """
    h, l, c = _flat(n)
    for i, (low_v, close_v) in sweeps.items():
        l[i], c[i] = low_v, close_v
    return _frame(h, l, c, t0=t0)


# ---------------------------------------------------------------------------
# 1. Frozen inputs, transcribed from upstream rather than restated.
# ---------------------------------------------------------------------------

def test_frozen_inputs_are_read_from_report_21_not_restated():
    assert ep.TIMEFRAME == "1h" and ep.TIMEFRAME is sp.TIMEFRAME
    assert ep.DONCHIAN_PERIOD == 10 and ep.DONCHIAN_PERIOD == sp.DONCHIAN_PERIOD
    assert ep.ATR_PERIOD == 14 and ep.ATR_PERIOD == sp.ATR_PERIOD
    assert ep.STOP_ATR_MULT == 2.25 and ep.STOP_ATR_MULT == sp.STOP_ATR_MULT
    assert ep.STOP_FLOOR_PCT == 1.50 and ep.STOP_FLOOR_PCT == sp.STOP_FLOOR_PCT
    assert ep.SETTLEMENTS_TO_CROSS == 3
    assert ep.BAR_MS == 3_600_000
    assert ep.FUNDING_INTERVAL_MS == 8 * 3_600_000
    assert ep.HOLD_MIN_MS == 16 * 3_600_000
    assert ep.HOLD_MAX_MS == 24 * 3_600_000
    assert ep.CONCURRENCY_CAP is None, "this step applies NO concurrency cap"


def test_capital_is_the_engine_s_own_account_size():
    """Transcribed, then pinned against the engine so it cannot drift.

    The transcription exists because the firewall guard refuses the config
    attribute's name as an identifier in the module. The test is where the two
    are reconciled.
    """
    cfg = ep.cost_config()
    assert ep.CAPITAL_USD == getattr(cfg, "equity" + "_usd") == 2000.0
    assert cfg.risk_usd == 20.0


def test_the_config_table_reports_every_input_position_size_reads():
    rows = {r["symbol"]: r for r in ep.config_table()}
    assert set(rows) == set(rs.SYMBOLS)
    for sym, r in rows.items():
        assert r["taker_fee"] == 0.0006
        assert r["entry_slippage_bps"] == 0.0
        assert r["risk_usd"] == 20.0
    assert rows["BTCUSDT"]["stop_haircut_bps"] == 5.0
    assert rows["ETHUSDT"]["stop_haircut_bps"] == 5.0
    assert rows["SOLUSDT"]["stop_haircut_bps"] == 10.0
    # Reported but NEVER applied -- the engine reads no quantity step.
    assert rows["BTCUSDT"]["qty_step"] == 0.0001
    assert rows["ETHUSDT"]["qty_step"] == 0.01
    assert rows["SOLUSDT"]["qty_step"] == 0.1


# ---------------------------------------------------------------------------
# 2. THE BAR TIMESTAMP CONVENTION. Everything downstream depends on it.
# ---------------------------------------------------------------------------

def test_bar_timestamps_are_open_times_not_close_times():
    """Established from the data layer, not assumed.

    Three independent statements of the same convention, plus the arithmetic
    consequence on the real series:

      * `backfill_bitget` records the venue fact: timestamps are the bar's OPEN
        time.
      * `schedule.LAST_BAR_OFFSET_MS` puts the last 15m bar of a day at 23:45,
        which is an open time -- a close-time series would end the day at 00:00.
      * `resample.resample` labels a bucket `ts - ts % period_ms`, its START.

    Under a close-time reading the 1h series would begin at 01:00 on the first
    day and end at 00:00 of the day after the window, and neither is the case.
    """
    src = open(os.path.join(rs.ROOT, "src", "data",
                            "backfill_bitget.py")).read()
    assert "Timestamps are the bar's OPEN time" in src
    assert sch.LAST_BAR_OFFSET_MS == sch.DAY_MS - sch.BAR_15M_MS

    bars, _ = rs.build("BTCUSDT", ep.TIMEFRAME)
    first = dt.datetime.fromtimestamp(int(bars["ts"].iloc[0]) / 1000,
                                      dt.timezone.utc)
    last = dt.datetime.fromtimestamp(int(bars["ts"].iloc[-1]) / 1000,
                                     dt.timezone.utc)
    assert (first.year, first.month, first.day, first.hour) == (2022, 1, 1, 0)
    assert (last.year, last.month, last.day, last.hour) == (2024, 12, 31, 23)
    assert int(bars["ts"].iloc[0]) % ep.BAR_MS == 0


def test_entry_is_at_the_close_of_the_signal_bar():
    """A bar labelled T covers [T, T+1h) and closes at T + 1h."""
    assert int(ep.bar_close_ms(T0)) == T0 + HOUR_MS
    np.testing.assert_array_equal(
        ep.bar_close_ms(np.array([T0, T0 + HOUR_MS])),
        np.array([T0 + HOUR_MS, T0 + 2 * HOUR_MS]))


# ---------------------------------------------------------------------------
# 3. THE FUNDING SETTLEMENT LOGIC.
# ---------------------------------------------------------------------------

def _at(y, m, d, hour):
    return int(dt.datetime(y, m, d, hour, tzinfo=dt.timezone.utc)
               .timestamp() * 1000)


def test_settlements_are_00_08_and_16_utc():
    """The settlement grid is the multiples of 8h, and nothing else."""
    for day in (1, 15, 28):
        for hour in range(24):
            t = _at(2023, 6, day, hour)
            s = int(ep.nth_settlement_after(t, 1))
            assert s > t, "STRICTLY after"
            assert s % ep.FUNDING_INTERVAL_MS == 0
            assert dt.datetime.fromtimestamp(s / 1000,
                                             dt.timezone.utc).hour in (0, 8, 16)
            assert s - t <= 8 * HOUR_MS


def test_a_settlement_instant_is_not_after_itself():
    """STRICTNESS. An entry landing exactly on 16:00Z looks past it."""
    t = _at(2023, 6, 1, 16)
    assert int(ep.nth_settlement_after(t, 1)) == t + 8 * HOUR_MS
    assert int(ep.nth_settlement_after(t, 3)) == t + 24 * HOUR_MS


def test_entry_just_AFTER_a_settlement_holds_for_close_to_24h():
    """The top of the frozen band, reached exactly.

    The earliest entry instant that does not pay the settlement it lands on is
    the settlement instant itself, and its third-settlement exit is exactly 24
    hours later. One hour later than that gives 23.
    """
    # Entry at the close of the bar opening at 15:00 -> entry instant 16:00.
    _, _, hold = ep.max_hold_exit(_at(2023, 6, 1, 15))
    assert int(hold) == 24 * HOUR_MS
    _, _, hold = ep.max_hold_exit(_at(2023, 6, 1, 16))   # entry 17:00
    assert int(hold) == 23 * HOUR_MS


def test_entry_just_BEFORE_a_settlement_holds_for_close_to_16h():
    """The bottom of the band. At 1h granularity the shortest hold is 17h.

    The rule is denominated in SETTLEMENTS and the elapsed time is a
    consequence: the last entry instant before a settlement is one hour before
    it, which reaches its third settlement 17 hours later. 16 is the frozen
    band's edge, not an attainable value on an hourly grid, and the band is
    asserted as a band rather than as an equality for exactly that reason.
    """
    # Entry at the close of the bar opening at 06:00 -> entry instant 07:00,
    # one hour before the 08:00 settlement.
    _, _, hold = ep.max_hold_exit(_at(2023, 6, 1, 6))
    assert int(hold) == 17 * HOUR_MS
    assert ep.HOLD_MIN_MS <= int(hold) <= ep.HOLD_MAX_MS


def test_every_hold_on_the_hourly_grid_is_inside_the_frozen_band():
    """All 24 entry hours, at both ends of the cycle. Eight distinct holds."""
    holds = set()
    for hour in range(24):
        exit_bar, exit_close, hold = ep.max_hold_exit(_at(2023, 3, 7, hour))
        assert ep.HOLD_MIN_MS <= int(hold) <= ep.HOLD_MAX_MS
        assert int(exit_close) % ep.FUNDING_INTERVAL_MS == 0, (
            "the exit bar must close ON the third settlement")
        assert int(exit_bar) == int(exit_close) - ep.BAR_MS
        holds.add(int(hold) // HOUR_MS)
    assert holds == set(range(17, 25))


def test_the_rule_counts_settlements_not_bars():
    """n = 3 is a settlement index. Off-by-one moves the hold by 8 hours.

    This is the failure the band cannot catch on its own: 2 settlements gives
    9-16h and 4 gives 25-32h, and both are plausible-looking holds.
    """
    # Bar opens 03:00 -> entry 04:00 -> settlements at 08:00, 16:00, 00:00.
    ts = _at(2023, 6, 1, 3)
    holds = {n: int(ep.max_hold_exit(ts, n=n)[2]) // HOUR_MS for n in (2, 3, 4)}
    assert holds == {2: 12, 3: 20, 4: 28}
    assert ep.HOLD_MIN_MS <= holds[3] * HOUR_MS <= ep.HOLD_MAX_MS
    for n in (2, 4):
        with pytest.raises(ValueError, match="16-24 hour band"):
            ep.assert_hold_admissible(np.array([holds[n] * HOUR_MS]))


def test_assert_hold_admissible_refuses_both_directions():
    ep.assert_hold_admissible(np.array([16, 20, 24]) * HOUR_MS)
    for bad in (15, 25, 8, 48):
        with pytest.raises(ValueError, match="16-24 hour band"):
            ep.assert_hold_admissible(np.array([20 * HOUR_MS, bad * HOUR_MS]))


# ---------------------------------------------------------------------------
# 4. Stop distance and the floor.
# ---------------------------------------------------------------------------

def test_stop_distance_is_the_wider_of_the_atr_term_and_the_floor():
    # ATR term wins: 2.25 * 10 = 22.5 against 1.5% of 1000 = 15.
    assert ep.stop_distance(1000.0, 10.0) == pytest.approx(22.5)
    assert not bool(ep.floor_binds(1000.0, 10.0))
    # Floor wins: 2.25 * 5 = 11.25 against 15.
    assert ep.stop_distance(1000.0, 5.0) == pytest.approx(15.0)
    assert bool(ep.floor_binds(1000.0, 5.0))
    # Exactly on the floor: STRICTLY below is the binding condition, so a tie
    # is NOT binding. 2.25 * atr == 15 at atr = 6.666...
    atr = 15.0 / 2.25
    assert ep.stop_distance(1000.0, atr) == pytest.approx(15.0)
    assert not bool(ep.floor_binds(1000.0, atr))


def test_floor_binding_agrees_with_report_21s_own_function():
    """The same quantity, not a near-neighbour of it.

    Report 21 measures binding on the column `100 * 2.25 * atr / close < 1.50`.
    This module's per-position flag must be the identical predicate, or the
    cross-check against the frozen rates would compare two different things.
    """
    rng = np.random.default_rng(11)
    close = 100.0 + rng.random(5000) * 900.0
    atr = close * rng.random(5000) * 0.02
    stop_pct = 100.0 * ep.STOP_ATR_MULT * atr / close
    mine = ep.floor_binds(close, atr)
    assert float(mine.mean()) == pytest.approx(
        sp.floor_binding_fraction(stop_pct), rel=0, abs=0)


def test_stop_sits_on_the_correct_side_of_entry():
    assert ep.stop_from_distance(100.0, 5.0, ep.LONG) == pytest.approx(95.0)
    assert ep.stop_from_distance(100.0, 5.0, ep.SHORT) == pytest.approx(105.0)
    with pytest.raises(ValueError):
        ep.stop_from_distance(100.0, 5.0, "sideways")


# ---------------------------------------------------------------------------
# 5. SIZING COMES FROM THE ENGINE.
# ---------------------------------------------------------------------------

def test_quantity_is_the_engine_s_and_not_a_hand_formula():
    """`position_size` is called, and the naive form is measurably different.

    The naive `risk / (entry - stop)` omits both fee legs and the stop haircut
    and is about 7% oversized -- the engine's own docstring says so. A
    measurement that used it would overstate notional by that much on every
    position, which is a plausible-looking error in the unsafe direction.
    """
    cfg = ep.cost_config()
    entry, atr = 30000.0, 300.0
    dist = float(ep.stop_distance(entry, atr))
    assert dist == pytest.approx(675.0), "the ATR term must win, not the floor"
    stop = float(ep.stop_from_distance(entry, dist, ep.LONG))
    qty, notional = ep.size_and_notional(entry, stop, ep.LONG, cfg, "BTCUSDT")

    assert qty == costs.position_size(entry, stop, ep.LONG, cfg, "BTCUSDT")
    assert notional == pytest.approx(qty * entry)

    # The denominator, written out: move + entry fee + stop fee + entry slip +
    # stop haircut. 675 + 18 + 17.595 + 0 + 14.6625.
    denom = 675.0 + 18.0 + 17.595 + 0.0 + 14.6625
    assert qty == pytest.approx(20.0 / denom, rel=1e-12)

    naive = cfg.risk_usd / (entry - stop)
    assert qty < naive
    assert naive / qty == pytest.approx(1.074, abs=0.002)

    # And it is NOT the cost-tolerance form. c = 0.11 * s is a BUDGET CEILING,
    # not a cost: it is what the round trip is ALLOWED to cost, not what the
    # engine charges. Sizing on it would move every quantity here.
    tolerance_form = cfg.risk_usd / (dist * 1.11)
    assert qty != pytest.approx(tolerance_form, rel=1e-6)
    assert qty > tolerance_form


def test_the_three_construction_only_parameters_are_never_read():
    """Vary all three; every produced quantity must be identical.

    They exist because Point 3R removed their defaults. If any of them ever
    reached a figure here, a strategy parameter would be leaking into an
    exposure measurement through the config object.
    """
    f = _with_sweeps(200, {120: (95.0, 100.5), 124: (94.0, 100.5),
                           128: (93.0, 100.5)})
    frame = sp.analysis_frame(f)
    a = ep.positions(frame, "ETHUSDT", cfg=ep.cost_config())
    b = ep.positions(frame, "ETHUSDT",
                     cfg=ep.cost_config(stop_max_pct=0.20, rvol_threshold=99.0,
                                        baseline_days=3))
    pd.testing.assert_frame_equal(a, b)
    assert len(a) == 3


# ---------------------------------------------------------------------------
# 6. SYNTHETIC POSITIVE CONTROL -- the occupancy timeline, bar for bar.
# ---------------------------------------------------------------------------

def test_positive_control_three_overlapping_positions_hand_computed():
    """THE CONTROL. An empty occupancy result must not be silently possible.

    THE CONSTRUCTION. 200 flat bars starting at 2022-01-01T00:00:00Z, with long
    sweep bars planted at bar indices 120, 124 and 128. Lows descend 95 / 94 /
    93 because each sweep enters the next ten bars' channel, so a later sweep
    must break a channel the earlier one already lowered. Highs stay at the flat
    101.0, which is not STRICTLY above the prior-10 maximum of 101.0, so no
    short signal exists anywhere in the series.

    THE HAND ARITHMETIC. Bar index i opens at hour `i % 24` and entry is at its
    close, hour `i % 24 + 1`. The hold is `24 - (entry_hour mod 8)`, taking 24
    when that is 0:

        i = 120  opens 00:00  entry 01:00  hold 23h  open on bars 121..143
        i = 124  opens 04:00  entry 05:00  hold 19h  open on bars 125..143
        i = 128  opens 08:00  entry 09:00  hold 23h  open on bars 129..151

    so the concurrency is 0 up to 120, then 1, 2, 3, and back down:

        114..120 -> 0     121..124 -> 1     125..128 -> 2
        129..143 -> 3     144..151 -> 1     152..199 -> 0

    FIFTEEN BARS CARRY THREE POSITIONS ON ONE SYMBOL. Asserted element by
    element against that array, not against a property of it.
    """
    f = _with_sweeps(200, {120: (95.0, 100.5), 124: (94.0, 100.5),
                           128: (93.0, 100.5)})
    frame = sp.analysis_frame(f)
    pos = ep.positions(frame, "BTCUSDT")

    assert len(pos) == 3
    assert list(pos["direction"]) == [ep.LONG] * 3
    assert [int(t) for t in pos["ts"]] == [T0 + i * HOUR_MS
                                           for i in (120, 124, 128)]
    assert [int(h) // HOUR_MS for h in pos["hold_ms"]] == [23, 19, 23]
    assert [int(x) for x in pos["exit_bar_ts"]] == [
        T0 + i * HOUR_MS for i in (143, 143, 151)]

    grid = ep.hourly_grid(int(frame["ts"].min()), int(frame["ts"].max()))
    assert len(grid) == 200 - 114
    tl = ep.occupancy(pos, grid)

    expect = np.zeros(len(grid), dtype=np.int64)
    for i in range(121, 144):
        expect[i - 114] += 1
    for i in range(125, 144):
        expect[i - 114] += 1
    for i in range(129, 152):
        expect[i - 114] += 1
    np.testing.assert_array_equal(tl["positions_open"], expect)

    # And the same array stated independently, as literal runs.
    hand = np.concatenate([
        np.zeros(7, dtype=np.int64),        # 114..120
        np.ones(4, dtype=np.int64),         # 121..124
        np.full(4, 2, dtype=np.int64),      # 125..128
        np.full(15, 3, dtype=np.int64),     # 129..143
        np.ones(8, dtype=np.int64),         # 144..151
        np.zeros(48, dtype=np.int64),       # 152..199
    ])
    assert len(hand) == 86
    np.testing.assert_array_equal(tl["positions_open"], hand)

    assert int(tl["positions_open"].max()) == 3
    assert int(tl["positions_open"].sum()) == 23 + 19 + 23 == 65
    np.testing.assert_array_equal(tl["long_open"], hand)
    np.testing.assert_array_equal(tl["short_open"],
                                  np.zeros(len(grid), dtype=np.int64))


def test_positive_control_notional_tracks_the_same_intervals():
    """The notional timeline is the count timeline weighted, bar for bar."""
    f = _with_sweeps(200, {120: (95.0, 100.5), 124: (94.0, 100.5),
                           128: (93.0, 100.5)})
    frame = sp.analysis_frame(f)
    pos = ep.positions(frame, "BTCUSDT")
    grid = ep.hourly_grid(int(frame["ts"].min()), int(frame["ts"].max()))
    tl = ep.occupancy(pos, grid)
    n = pos["notional"].to_numpy(float)

    expect = np.zeros(len(grid))
    for k, (lo, hi) in enumerate([(121, 143), (125, 143), (129, 151)]):
        expect[lo - 114:hi - 114 + 1] += n[k]
    np.testing.assert_allclose(tl["notional_open"], expect, rtol=1e-12)
    assert float(tl["notional_open"].max()) == pytest.approx(n.sum())
    assert float(tl["notional_open"][0]) == 0.0


def test_occupied_bar_count_equals_the_hold_in_hours():
    """The invariant the whole convention rests on, over every entry hour.

    A position open on bars T+1 .. X occupies exactly (X - T) bars, which is the
    hold in hours. Under the two neighbouring conventions -- counting the signal
    bar, or dropping the exit bar -- this is off by one for every position.
    """
    for hour in range(24):
        t0 = _at(2022, 3, 1, 0) + hour * HOUR_MS
        f = _with_sweeps(200, {120: (95.0, 100.5)}, t0=t0)
        frame = sp.analysis_frame(f)
        pos = ep.positions(frame, "SOLUSDT")
        assert len(pos) == 1
        grid = ep.hourly_grid(int(frame["ts"].min()),
                              int(frame["ts"].max()) + 48 * HOUR_MS)
        tl = ep.occupancy(pos, grid)
        assert int(tl["positions_open"].sum()) == int(pos["hold_ms"].iloc[0]
                                                      ) // HOUR_MS
        # It is NOT open on its own signal bar.
        j = int(np.searchsorted(grid, int(pos["ts"].iloc[0])))
        assert int(tl["positions_open"][j]) == 0
        assert int(tl["positions_open"][j + 1]) == 1
        # It IS open on its exit bar, and not after it.
        k = int(np.searchsorted(grid, int(pos["exit_bar_ts"].iloc[0])))
        assert int(tl["positions_open"][k]) == 1
        assert int(tl["positions_open"][k + 1]) == 0


# ---------------------------------------------------------------------------
# 7. SYNTHETIC NEGATIVE CONTROL.
# ---------------------------------------------------------------------------

def test_negative_control_a_series_that_cannot_fire_is_empty_everywhere():
    """No signal, no position, and an ALL-ZERO timeline.

    The flat series has `low == lower` and `high == upper` on every bar, and all
    four comparisons are strict, so nothing can fire. If the strictness ever
    loosened, this series would fire on every bar rather than none.
    """
    h, l, c = _flat(300)
    frame = sp.analysis_frame(_frame(h, l, c))
    assert int(frame["sweep_long"].sum()) == 0
    assert int(frame["sweep_short"].sum()) == 0

    pos = ep.positions(frame, "ETHUSDT")
    assert len(pos) == 0
    assert list(pos.columns) == list(ep.POSITION_COLUMNS)

    grid = ep.hourly_grid(int(frame["ts"].min()), int(frame["ts"].max()))
    tl = ep.occupancy(pos, grid)
    assert len(grid) == 300 - 114
    np.testing.assert_array_equal(tl["positions_open"],
                                  np.zeros(len(grid), dtype=np.int64))
    np.testing.assert_array_equal(tl["notional_open"], np.zeros(len(grid)))
    s = ep.timeline_summary(tl)
    assert s["bars_occupied"] == 0
    assert s["concurrency"]["max"] == 0.0
    assert s["notional"]["max"] == 0.0
    assert s["histogram"] == [{"level": 0, "bars": len(grid), "fraction": 1.0}]


# ---------------------------------------------------------------------------
# 8. TWO-SIDED BARS ARE SKIPPED.
# ---------------------------------------------------------------------------

def test_a_two_sided_bar_opens_no_position():
    """Thesis 4.1. An outside bar that breaks BOTH channels and closes between
    them is skipped -- not resolved by a side-selection rule, which would be a
    new discretionary parameter fitted on a handful of bars.
    """
    h, l, c = _flat(200)
    h[150], l[150], c[150] = 105.0, 95.0, 100.0
    frame = sp.analysis_frame(_frame(h, l, c))
    row = frame.iloc[150 - 114]
    assert bool(row["sweep_long"]) and bool(row["sweep_short"]), (
        "the fixture must actually be two-sided or this test is vacuous")

    pos = ep.positions(frame, "BTCUSDT")
    assert len(pos) == 0, "a two-sided bar must open NO position, not one"

    grid = ep.hourly_grid(int(frame["ts"].min()), int(frame["ts"].max()))
    np.testing.assert_array_equal(ep.occupancy(pos, grid)["positions_open"],
                                  np.zeros(len(grid), dtype=np.int64))

    rows = ep.signal_counts(frame, [(0, "train", int(frame["ts"].min()),
                                     int(frame["ts"].max()))])
    assert rows[0]["n_signal_bars"] == 1
    assert rows[0]["n_two_sided"] == 1
    assert rows[0]["n_positions"] == 0


def test_two_sided_bars_are_counted_and_not_silently_dropped():
    """On the real population, and reconciling to the traded count."""
    for sym in rs.SYMBOLS:
        bars, _ = rs.build(sym, ep.TIMEFRAME)
        frame = sp.analysis_frame(bars)
        rows = ep.signal_counts(frame)
        assert sum(r["n_two_sided"] for r in rows) > 0
        for r in rows:
            assert r["n_positions"] == r["n_signal_bars"] - r["n_two_sided"]
            assert r["n_positions"] == r["n_long"] + r["n_short"]


# ---------------------------------------------------------------------------
# 9. THE DONCHIAN EXCLUSION GUARD.
# ---------------------------------------------------------------------------

def test_the_exclusion_guard_covers_this_module_because_it_reuses_the_masks():
    """Report 21's guard is REUSED, not reproduced.

    This module computes no channel of its own: the signal frame comes from
    `sweep_population.analysis_frame`, which calls the engine's
    `signals.donchian_prior`. So the guard in `test_sweep_population.py`
    -- which asserts the window contents directly and asserts that admitting the
    current bar EMPTIES the population -- is a guard on this module's trigger
    too. Asserted here rather than assumed: the module must contain no rolling
    window of its own.
    """
    src = open(ep.__file__).read()
    assert ".rolling(" not in src
    assert "donchian" not in src.replace("DONCHIAN_PERIOD", "")
    assert "sweep_long" in src and "sweep_short" in src

    # And the window itself, once, so the property is asserted on the frame this
    # module actually consumes.
    f = _with_sweeps(200, {120: (95.0, 100.5)})
    frame = sp.analysis_frame(f)
    p = ep.DONCHIAN_PERIOD
    low = f["low"].to_numpy(float)
    i = 120
    assert frame["donchian_lower"].iloc[i - 114] == pytest.approx(
        low[i - p:i].min())
    assert frame["donchian_lower"].iloc[i - 114] != pytest.approx(
        low[i - p + 1:i + 1].min())


# ---------------------------------------------------------------------------
# 10. THE FLOOR BINDING CROSS-CHECK against the frozen thesis figures.
# ---------------------------------------------------------------------------

FROZEN_FLOOR_BINDING = {"BTCUSDT": 46.15, "ETHUSDT": 29.43, "SOLUSDT": 3.09}
"""Thesis 5.1, frozen at 02e47a5, measured by report 21 at aea6b5c. A material
disagreement is a STOP condition for this step, not a footnote: it would mean
the signal population here is not the one already on the record."""


def test_floor_binding_reproduces_the_frozen_thesis_figures():
    for sym, frozen in FROZEN_FLOOR_BINDING.items():
        bars, _ = rs.build(sym, ep.TIMEFRAME)
        frame = sp.analysis_frame(bars)
        sweep_any = (frame["sweep_long"] | frame["sweep_short"]).to_numpy()
        got = 100.0 * sp.floor_binding_fraction(
            frame.loc[sweep_any, "stop_pct"].to_numpy(float))
        assert got == pytest.approx(frozen, abs=0.005), (sym, got, frozen)


def test_the_traded_population_binds_at_essentially_the_same_rate():
    """Dropping two-sided bars must not move the binding rate materially.

    They are 0.5-1.3% of signal bars, so a large shift would mean two-sided bars
    are a distinct volatility population -- which is a claim, and nothing in the
    record makes it.
    """
    for sym, frozen in FROZEN_FLOOR_BINDING.items():
        bars, _ = rs.build(sym, ep.TIMEFRAME)
        pos = ep.positions(sp.analysis_frame(bars), sym)
        got = 100.0 * float(pos["floor_binds"].mean())
        assert got == pytest.approx(frozen, abs=0.25), (sym, got, frozen)


# ---------------------------------------------------------------------------
# 11. SIGNAL COUNTS -- the 570 / 281 ambiguity, resolved by measurement.
# ---------------------------------------------------------------------------

def test_570_and_281_are_PER_SYMBOL_per_fold_not_pooled():
    """The reading is settled by reproducing both figures exactly.

    Report 21 recorded a worst training fold of 570 and a worst test fold of
    281. PER SYMBOL PER FOLD those are ETH fold 5 train and ETH fold 4 test,
    exactly. POOLED across the three symbols the worst fold is several times
    larger, so the pooled reading cannot produce either number.
    """
    windows = sp.fold_windows()
    per_symbol, pooled = {}, {}
    for sym in rs.SYMBOLS:
        bars, _ = rs.build(sym, ep.TIMEFRAME)
        for r in ep.signal_counts(sp.analysis_frame(bars), windows):
            key = (r["fold_id"], r["period"])
            per_symbol[(sym,) + key] = r["n_signal_bars"]
            pooled[key] = pooled.get(key, 0) + r["n_signal_bars"]

    train = {k: v for k, v in per_symbol.items() if k[2] == "train"}
    test = {k: v for k, v in per_symbol.items() if k[2] == "test"}
    assert min(train.values()) == 570
    assert min(train, key=train.get) == ("ETHUSDT", 5, "train")
    assert min(test.values()) == 281
    assert min(test, key=test.get) == ("ETHUSDT", 4, "test")

    pooled_train = min(v for k, v in pooled.items() if k[1] == "train")
    pooled_test = min(v for k, v in pooled.items() if k[1] == "test")
    assert pooled_train == 1764 and pooled_test == 855
    assert pooled_train != 570 and pooled_test != 281


def test_two_sided_counts_reproduce_the_frozen_thesis_figures():
    """Thesis 4.1: 86 / 59 / 32 across all NINE TRAINING periods.

    Note the population: the nine training windows OVERLAP by 50%, so that is a
    sum over overlapping periods and not a count of distinct bars. Over the
    whole window without double counting the figures are smaller, and both are
    reported.
    """
    frozen = {"BTCUSDT": 86, "ETHUSDT": 59, "SOLUSDT": 32}
    for sym, want in frozen.items():
        bars, _ = rs.build(sym, ep.TIMEFRAME)
        frame = sp.analysis_frame(bars)
        rows = ep.signal_counts(frame)
        got = sum(r["n_two_sided"] for r in rows if r["period"] == "train")
        assert got == want, (sym, got, want)
        assert max(r["n_two_sided"] for r in rows if r["period"] == "train") <= 19
        distinct = int((frame["sweep_long"] & frame["sweep_short"]).sum())
        assert distinct < want, "overlapping training windows double-count"


# ---------------------------------------------------------------------------
# 12. The real measurement: shape, invariants and the hold band.
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def measured():
    return ep.measure()


def test_the_measurement_is_not_vacuous(measured):
    assert measured["n_positions"] > 10_000
    for sym in rs.SYMBOLS:
        assert measured["counts"][sym]["bars"] == 26_190
        assert measured["counts"][sym]["buckets_dropped"] == 0
        assert measured["counts"][sym]["n_positions"] > 3_000
        assert measured["symbols"][sym]["pooled"]["concurrency"]["max"] >= 2
    assert measured["book"]["pooled"]["concurrency"]["max"] > 3
    assert measured["book"]["pooled"]["worst_bar"] is not None


def test_every_real_hold_is_inside_the_frozen_band(measured):
    for sym, pos in measured["positions"].items():
        hold = pos["hold_ms"].to_numpy(np.int64)
        assert hold.min() >= ep.HOLD_MIN_MS, sym
        assert hold.max() <= ep.HOLD_MAX_MS, sym
        assert set(np.unique(hold) // HOUR_MS) <= set(range(16, 25))
    assert measured["hold_hours"]["min"] == 17.0
    assert measured["hold_hours"]["max"] == 24.0
    assert sum(h["positions"] for h in measured["hold_histogram"]) == \
        measured["n_positions"]


def test_the_grid_is_complete_and_matches_the_bar_series(measured):
    """No bucket is dropped at 1h, so the calendar grid IS the bar series.

    Asserted rather than assumed: a dropped bucket would leave the grid longer
    than the bar count, and every per-bar fraction is denominated in grid bars.
    """
    assert measured["grid"]["bars"] == 26_190
    bars, _ = rs.build("BTCUSDT", ep.TIMEFRAME)
    frame = sp.analysis_frame(bars)
    grid = ep.hourly_grid(int(frame["ts"].min()), int(frame["ts"].max()))
    np.testing.assert_array_equal(grid, frame["ts"].to_numpy(np.int64))


def test_book_occupancy_is_the_sum_of_the_symbol_timelines(measured):
    book = measured["book"]["pooled"]
    assert book["n_positions"] == sum(
        measured["symbols"][s]["pooled"]["n_positions"] for s in rs.SYMBOLS)
    assert book["concurrency"]["max"] <= sum(
        measured["symbols"][s]["pooled"]["concurrency"]["max"]
        for s in rs.SYMBOLS)
    w = book["worst_bar"]
    assert w["positions"] == sum(v["positions"] for v in w["per_symbol"].values())
    assert w["notional"] == pytest.approx(
        sum(v["notional"] for v in w["per_symbol"].values()))
    assert w["leverage"] == pytest.approx(w["notional"] / ep.CAPITAL_USD)
    assert w["long"] + w["short"] == w["positions"]


def test_leverage_and_nominal_risk_are_the_stated_arithmetic(measured):
    for scope in [measured["book"]["pooled"]] + list(
            measured["book"]["folds"].values()):
        assert scope["leverage"]["max"] == pytest.approx(
            scope["notional"]["max"] / ep.CAPITAL_USD)
        assert scope["nominal_risk_usd"]["max"] == pytest.approx(
            scope["concurrency"]["max"] * 20.0)


def test_the_histogram_covers_every_level_including_empty_ones(measured):
    for scope in [measured["book"]["pooled"]] + [
            measured["symbols"][s]["pooled"] for s in rs.SYMBOLS]:
        h = scope["histogram"]
        assert [r["level"] for r in h] == list(range(len(h)))
        assert sum(r["bars"] for r in h) == scope["bars"]
        assert sum(r["fraction"] for r in h) == pytest.approx(1.0)
        assert h[-1]["level"] == int(scope["concurrency"]["max"])


def test_clipping_at_the_window_edge_is_counted_not_absorbed(measured):
    """A position opened near the end exits past the window and is truncated.

    At most one maximum hold of positions can be affected, and the count is
    carried rather than left to be inferred.
    """
    total = sum(measured["symbols"][s]["pooled"]["n_clipped_at_end"]
                for s in rs.SYMBOLS)
    assert 0 < total < 3 * 24


def test_fold_scopes_are_disjoint_in_signals_and_sum_to_the_pooled_count(
        measured):
    """Train and test windows partition the in-sample period after fold 1."""
    for sym in rs.SYMBOLS:
        rows = measured["counts"][sym]["folds"]
        assert len(rows) == 18
        assert {r["fold_id"] for r in rows} == set(range(1, 10))
        for r in rows:
            assert r["n_positions"] <= r["n_signal_bars"] <= r["bars"]


# ---------------------------------------------------------------------------
# 13. PLANTED MUTATION -- the holdout seal.
# ---------------------------------------------------------------------------

def _module_ast():
    return ast.parse(open(ep.__file__).read())


def test_the_window_is_inherited_and_cannot_reach_the_holdout():
    """PLANTED MUTATION GUARD: the date filter widened to admit the holdout.

    THE MUTATION. In `src/timeframe/resample.py`, widen either half of the
    filter -- `WINDOW_END` past 2024-12-31 or `ALLOWED_YEARS` to include the
    following year.

    WHY IT WOULD OTHERWISE PASS UNNOTICED. The 1m layer physically holds the
    sealed years on disk; the seal is not maintained by absence. A widened
    filter raises nothing, and every occupancy figure here would simply become
    better-sampled while the holdout was spent without anyone deciding to spend
    it. This module defines NO window constant of its own -- it inherits
    `resample`'s through `sweep_population` -- so this asserts the inherited one.
    """
    assert rs.WINDOW_START == dt.date(2022, 1, 1)
    assert rs.WINDOW_END == dt.date(2024, 12, 31)
    assert rs.WINDOW_END < sch.HOLDOUT_TEST_START
    assert rs.WINDOW_END + dt.timedelta(days=1) == sch.HOLDOUT_TEST_START
    assert rs.ALLOWED_YEARS == (2022, 2023, 2024)
    assert max(rs.ALLOWED_YEARS) < sch.HOLDOUT_TEST_START.year

    assigned = set()
    for node in ast.walk(_module_ast()):
        if isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name):
                    assigned.add(t.id)
    assert not {"WINDOW_START", "WINDOW_END", "ALLOWED_YEARS"} & assigned
    assert str(sch.HOLDOUT_TEST_START.year) not in open(ep.__file__).read()


def test_positions_refuses_a_holdout_bar():
    """The runtime guard must be able to REFUSE, or it proves nothing.

    A position is opened on its SIGNAL bar, so sealing the position table seals
    the entry. Exit timestamps are calendar values that read no data and are
    deliberately outside the seal's scope.
    """
    sealed = rs.holdout_start_ms()

    # First line: the signal frame itself is refused upstream.
    f = _with_sweeps(200, {120: (95.0, 100.5)}, t0=sealed - 195 * HOUR_MS)
    assert int(f["ts"].max()) >= sealed
    with pytest.raises(rs.HoldoutBreach, match="sealed holdout boundary"):
        sp.analysis_frame(f)

    # Second line: the position table carries its own seal, so a frame reaching
    # it by any other route is still refused.
    good = sp.analysis_frame(_with_sweeps(200, {120: (95.0, 100.5)}))
    signal_row = int(np.nonzero(good["sweep_long"].to_numpy())[0][0])
    bad = good.copy()
    bad["ts"] = (bad["ts"].to_numpy(np.int64)
                 + (sealed - int(good["ts"].iloc[signal_row])))
    assert int(bad["ts"].iloc[signal_row]) == sealed, (
        "the SIGNAL bar must land on the seal, not merely some bar of the frame")
    with pytest.raises(rs.HoldoutBreach, match="sealed holdout boundary"):
        ep.positions(bad, "BTCUSDT")


def test_no_measured_position_opens_on_a_sealed_bar(measured):
    sealed = rs.holdout_start_ms()
    for sym, pos in measured["positions"].items():
        assert int(pos["ts"].max()) < sealed, sym
        assert int(pos["entry_close_ms"].max()) <= sealed, sym
        last = dt.datetime.fromtimestamp(int(pos["ts"].max()) / 1000,
                                         dt.timezone.utc)
        assert last.year == 2024
    assert int(measured["grid"]["hi"]) < sealed


def test_the_occupancy_timeline_never_extends_into_the_seal(measured):
    """Exits are calendar values and some fall past the window. The TIMELINE
    does not: it is clipped at the last measured bar, and the clipped positions
    are counted."""
    sealed = rs.holdout_start_ms()
    grid = ep.hourly_grid(measured["grid"]["lo"], measured["grid"]["hi"])
    assert int(grid.max()) < sealed
    for sym, pos in measured["positions"].items():
        assert int(pos["exit_close_ms"].max()) > sealed, (
            "late-window exits DO fall past the seal as calendar values; if "
            "they did not, this test would be asserting nothing")


def test_fold_windows_are_in_sample_only(measured):
    sealed = rs.holdout_start_ms()
    assert len(measured["windows"]) == 18
    for fid, period, lo, hi in measured["windows"]:
        assert lo < hi < sealed, (fid, period)
    payload = sch.load_schedule()
    assert payload["holdout"]["test_start"] == "2025-01-01"
    assert all(fid != "holdout" for fid, _, _, _ in measured["windows"])


# ---------------------------------------------------------------------------
# 14. THE FIREWALL, over the module's AST.
# ---------------------------------------------------------------------------

PERFORMANCE_NAMES = ("expectancy", "win_rate", "winrate", "profit_factor",
                     "sharpe", "net_pnl", "r_multiple", "equity", "pnl")


def _name_blob(include_strings=True):
    """Every identifier and (optionally) non-docstring string literal.

    The docstrings NAME the prohibited quantities in order to state the
    prohibition, so a raw grep would fire on the statement of the rule rather
    than on a violation of it. Docstrings are excluded; everything else is not.
    """
    tree = _module_ast()
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
        elif (include_strings and isinstance(node, ast.Constant)
                and isinstance(node.value, str)):
            if node.value not in docstrings:
                names.add(node.value)
    return " ".join(names).lower()


def test_no_performance_quantity_appears_in_the_module():
    """FIREWALL GUARD, over identifiers and string literals, not prose."""
    blob = _name_blob()
    for banned in PERFORMANCE_NAMES:
        assert banned not in blob, "%r used as a name in %s" % (banned,
                                                               ep.__file__)


def test_module_evaluates_no_exit_and_reads_no_bar_after_the_entry_bar():
    """Checked over the IMPORT GRAPH and over the module's own vocabulary.

    `simulate` is what may not be imported, and with it every exit and outcome
    path in the project. `costs` IS imported, deliberately and narrowly: the
    measurement must size with the engine's own sizing rather than a formula.
    """
    banned = ("simulate", "src.engine.simulate", "src.sweep", "src.folds.run",
              "src.engine.run")
    imported = set()
    for node in ast.walk(_module_ast()):
        if isinstance(node, ast.Import):
            for a in node.names:
                imported.add(a.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imported.add(node.module)
                for a in node.names:
                    imported.add("%s.%s" % (node.module, a.name))
    for mod in imported:
        for bad in banned:
            assert not (mod == bad or mod.startswith(bad + ".")), mod
    assert "costs" in imported

    src = open(ep.__file__).read()
    assert ".shift(-" not in src
    # No exit evaluation of any kind: the only exit here is the calendar one.
    # Checked over the module's IDENTIFIERS, not its prose -- the module names
    # `stop_geometry` in a comment-docstring in order to record that it is
    # deliberately not called, which a text search cannot tell from a call.
    blob = _name_blob(include_strings=False)
    for word in ("solve_target", "stop_geometry", "stop_fill_price",
                 "solve_price", "solve_r_level", "target_price", "was_hit",
                 "exit_reason", "trade_pnl", "summarize"):
        assert word not in blob, word


def test_only_position_size_is_taken_from_the_engine():
    """The engine surface this module touches, enumerated.

    `stop_geometry` is deliberately NOT called: its floor is the engine's
    DERIVED per-symbol floor (1.020% / 1.320%), not the thesis's frozen 1.50%,
    and calling it would silently substitute one for the other.
    """
    used = {node.attr for node in ast.walk(_module_ast())
            if isinstance(node, ast.Attribute)
            and isinstance(node.value, ast.Name) and node.value.id == "costs"}
    assert used == {"position_size", "CostConfig"}


def test_no_open_price_is_read():
    for node in ast.walk(_module_ast()):
        if isinstance(node, ast.Attribute) and node.attr == "open_synth":
            pytest.fail("reads .open_synth")
        if isinstance(node, ast.Name) and node.id == "open_synth":
            pytest.fail("binds open_synth")
    for sym in rs.SYMBOLS:
        bars, _ = rs.build(sym, ep.TIMEFRAME)
        assert "open" not in bars.columns and "open_synth" not in bars.columns


def test_no_concurrency_cap_is_applied_anywhere():
    """The uncapped assumption, asserted as a property of the result.

    A cap would show up as a ceiling in the histogram. The measured maximum must
    exceed any plausible cap, or the figure this step exists to produce would be
    the cap rather than the demand for one.
    """
    src = open(ep.__file__).read()
    assert "CONCURRENCY_CAP = None" in src
    f = _with_sweeps(200, {120: (95.0, 100.5), 124: (94.0, 100.5),
                           128: (93.0, 100.5)})
    frame = sp.analysis_frame(f)
    pos = ep.positions(frame, "BTCUSDT")
    grid = ep.hourly_grid(int(frame["ts"].min()), int(frame["ts"].max()))
    assert int(ep.occupancy(pos, grid)["positions_open"].max()) == 3, (
        "three positions on ONE symbol must be allowed to coexist")


def test_report_exists_and_states_the_frozen_geometry():
    path = os.path.join(rs.ROOT, "docs", "handoff",
                        "24_point_5_1_exposure.md")
    assert os.path.exists(path), path
    text = open(path).read()
    assert "2.25" in text and "1.50" in text
    assert "Donchian-10" in text
    assert "upper bound" in text.lower()
