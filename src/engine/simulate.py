"""Layer B -- trade lifecycle simulation.

Loops over TRADES, not bars. Each trade walks at most 240 1m bars (16 x 15m
plus the T+17 execution minute), so this is deliberately written to be read and
checked by hand rather than to be fast.

1m data is used for exactly two things, per spec: the entry fill price and
intrabar stop-vs-target ordering. 1m volume is never read -- the loaders drop
the column so a reference raises KeyError. 1m open is likewise never read.
"""

from dataclasses import dataclass, field

import numpy as np

from costs import (LONG, SHORT, MIN_QTY, RISK_RULE, CostConfig, check_min_qty,
                   entry_fill_price, position_size, r_multiple, round_to_tick,
                   solve_r_level, solve_target, stop_fill_price, stop_geometry,
                   trade_pnl)

BAR_15M_MS = 900_000
BAR_1M_MS = 60_000

# --------------------------------------------------------------------------
# the second firewall (Appendix M.2) -- the holdout, DEFINED here, never LOADED
#
# src/folds/ sealed its own loaders; this path predates that seal and was not
# covered by it. The boundary is duplicated rather than imported because the
# engine deliberately has no dependency on src/ -- it is importable standalone.
# A test asserts this constant equals src.folds.schedule.HOLDOUT_TEST_START, so
# the duplication cannot silently drift.
# --------------------------------------------------------------------------
HOLDOUT_START_MS = 1_735_689_600_000        # 2025-01-01T00:00:00Z
HOLDOUT_START_ISO = "2025-01-01"
HOLDOUT_YEAR = 2025


class HoldoutSealError(PermissionError):
    """1m data at or after the holdout boundary was requested.

    RAISED, never degraded. Appendix M.3 excludes boundary-crossing trades at
    SIGNAL TIME, before any 1m bar is requested, so in normal operation this
    can never fire. If it fires, the exclusion did not run -- which is a defect
    in the caller, not a data condition to be handled. Falling back to partial
    data here would convert a bug into a silently wrong number.
    """


def in_sample_years(years, holdout_year=HOLDOUT_YEAR):
    """`years` with everything at or after the holdout year removed.

    Callers add `max(year) + 1` so a trade opened near a year boundary can walk
    forward into the next year's 1m file. That convention is correct everywhere
    except at the holdout boundary, where it would reach for sealed data. This
    clamps it; Appendix M.3's exclusion is what makes the clamp safe, because
    no surviving trade needs the years it removes.
    """
    return {y for y in years if y < holdout_year}


def max_walk_minutes(cfg):
    """1m bars to load per trade. DERIVED from max_hold_bars, never a rule.

    The last minute any rule can fire is the FIRST minute of bar
    max_hold_bars+1, which sits at minute index (max_hold_bars+1)*15 from the
    entry minute -- so the buffer needs that index to exist, plus slack.

    Sizing this buffer from the time stop is what made the walk act as an
    unconditional exit (defect B1); it must always be large enough that running
    out of buffer means running out of DATA, never that a rule fired.
    """
    return (cfg.max_hold_bars + 1) * 15 + 2


def last_1m_ts_needed(entry_ts, cfg):
    """Timestamp of the LAST 1m bar this trade's lifecycle walk could read.

    PURE ARITHMETIC on the entry timestamp and max_hold_bars. It reads no data,
    which is the whole point: Appendix M.3's exclusion has to be decidable
    BEFORE any 1m bar is requested, or the seal would have to be breached to
    find out whether it should have been.

    Anchored on `max_walk_minutes`, the buffer actually sliced, rather than on
    the max-hold execution bar. The buffer is two minutes wider, so the answer
    is the true data requirement and not merely the expected exit.
    """
    return entry_ts + (max_walk_minutes(cfg) - 1) * BAR_1M_MS


def crosses_holdout(entry_ts, cfg, holdout_start_ms=HOLDOUT_START_MS):
    """Would resolving this trade require data at or after the holdout?

    DELIBERATELY CONSERVATIVE. It asks whether the MAXIMUM possible walk
    reaches the boundary, not whether the actual exit would. Deciding on the
    actual exit bar would mean resolving the trade, which needs the very data
    the seal forbids. So a trade signalled from roughly 2024-12-31 13:45 onward
    is excluded even though most such trades would have exited before midnight.
    That over-exclusion uses no future information; the alternative does.
    """
    return last_1m_ts_needed(entry_ts, cfg) >= holdout_start_ms


def require_in_sample_window(entry_ts, cfg, symbol, authorised=False,
                             holdout_start_ms=HOLDOUT_START_MS):
    """Backstop at the POINT OF USE. Raises if the walk reaches the holdout.

    WHY THIS EXISTS AS WELL AS THE LOADER CHECK. Refusing inside `load_1m` is
    necessary but NOT sufficient: once the holdout years are simply not loaded,
    a boundary-crossing trade does not trigger any refusal -- it runs off the
    end of the available records and exits `insufficient_data`, which is a
    silently wrong number rather than a loud failure. Only a check on the
    REQUIREMENT, evaluated per trade, turns that into a raise.
    """
    if authorised:
        return
    if crosses_holdout(entry_ts, cfg, holdout_start_ms):
        raise HoldoutSealError(
            f"{symbol}: a trade entering at {entry_ts} would need 1m data "
            f"through {last_1m_ts_needed(entry_ts, cfg)}, at or after the "
            f"holdout boundary ({HOLDOUT_START_ISO}), which is SEALED. "
            f"Appendix M.3 excludes such trades at signal time, so reaching "
            f"this point means the exclusion did not run -- fix the caller. "
            f"Pass authorised=True only for the single pre-registered holdout "
            f"evaluation at step 9 of the 4.4 sequence.")


@dataclass
class Trace:
    """Human-readable step-by-step record of one trade."""
    lines: list = field(default_factory=list)
    enabled: bool = False

    def __call__(self, msg):
        if self.enabled:
            self.lines.append(msg)

    def text(self):
        return "\n".join(self.lines)


def _fmt(x, nd=8):
    return f"{x:.{nd}f}".rstrip("0").rstrip(".") if isinstance(x, float) else str(x)


def simulate_trade(signal, bars_1m, cfg, tick, trace=None, order_spec=None):
    """Simulate one trade from a signal row.

    `bars_1m` is a structured view of the 1m bars from the first minute of the
    15m bar AFTER the signal bar, ascending, with fields ts/high/low/close.
    Returns a dict (the trade row), or None if the trade could not be entered.

    The time stop is a STATE CHECK, not a latch: at the close of the 15m bar
    `time_stop_bars` after entry, the trade must BE at or above threshold_r,
    net of costs. "Did it ever touch" is deliberately not the test -- a wick to
    +1R that immediately retraces is a liquidity-vacuum failure, not a healthy
    trade. This supersedes the Point 3 intrabar-touch rule.
    """
    tr = trace or Trace()
    direction = signal["direction"]
    symbol = signal["symbol"]
    sig_ts = int(signal["signal_bar_ts"])

    if len(bars_1m) == 0:
        return None

    # ---- entry: close of the FIRST 1m bar of 15m bar T+1 ------------------
    e_bar = bars_1m[0]
    entry_ts = int(e_bar["ts"])
    expected = sig_ts + BAR_15M_MS
    if entry_ts != expected:
        # Missing 1m coverage for the execution minute -> not takeable.
        return None
    entry = entry_fill_price(float(e_bar["close"]), direction, cfg, tick)
    tr(f"  ENTRY   1m bar ts={entry_ts} close={_fmt(float(e_bar['close']))} "
       f"-> fill {_fmt(entry)}  (entry_slippage_bps={cfg.entry_slippage_bps})")

    # ---- stop, size, target ----------------------------------------------
    atr = float(signal["atr"])
    stop, stop_mech = stop_geometry(entry, atr, direction, cfg, tick, symbol)
    raw_dist = cfg.stop_atr_mult * atr
    floor_pct = cfg.stop_min_pct(symbol)
    pct = abs(entry - stop) / entry
    tr(f"  STOP    atr={_fmt(atr)} x{cfg.stop_atr_mult} = {_fmt(raw_dist)}  "
       f"floor {floor_pct:.4%} (DERIVED: max({cfg.n_cost} x c_roundtrip "
       f"{cfg.c_roundtrip(symbol):.4%}, lev {cfg.leverage_term():.4%})) "
       f"cap {cfg.stop_max_pct:.3%} of "
       f"{_fmt(entry)} -> stop {_fmt(stop)} ({pct:.4%} of entry) "
       f"[stop_binding_mechanism={stop_mech}]")

    qty = position_size(entry, stop, direction, cfg, symbol)

    # Exchange minimum-order guard rail, denominated in QUANTITY and NOTIONAL
    # (never percent -- stop_max_pct already guards width in percent). Reject
    # loudly rather than let a sub-minimum order round silently to nothing.
    ok, why = check_min_qty(qty, entry, order_spec)
    if not ok:
        tr(f"  REFUSED min_qty: {why}")
        return {"_refused": MIN_QTY, "symbol": symbol, "direction": direction,
                "signal_bar_ts": sig_ts, "reason": why}
    s_entry = entry * cfg.entry_slippage_bps / 10_000.0
    s_stop = stop * cfg.haircut_bps(symbol) / 10_000.0
    move = abs(entry - stop)
    denom = move + entry * cfg.taker_fee + stop * cfg.taker_fee + s_entry + s_stop
    tr(f"  SIZE    denom = |P-S| {_fmt(move)} + P*f_taker "
       f"{_fmt(entry * cfg.taker_fee)} + S*f_taker {_fmt(stop * cfg.taker_fee)} "
       f"+ P*s_entry {_fmt(s_entry)} + S*s_stop {_fmt(s_stop)} = {_fmt(denom)}")
    tr(f"          qty = risk {cfg.risk_usd} / {_fmt(denom)} = {_fmt(qty)}")

    notional = qty * entry
    target = solve_target(entry, qty, direction, cfg, tick)
    tr(f"  TARGET  solve: ({cfg.target_r_multiple}R/q + P*(1+f_taker)) / "
       f"(1-f_maker) -> {_fmt(target)}   notional {_fmt(notional, 4)}")

    # Trade-through requirement: touch is not a fill for a resting limit.
    fill_level = round_to_tick(
        target + tick if direction == LONG else target - tick, tick, "nearest")
    # threshold_R NET of costs, exiting taker. threshold_r is DERIVED from phi,
    # never supplied. A naive entry +/- stop_distance level is reached while the
    # trade has not actually made 1R.
    thr_r = cfg.threshold_r
    r1_level = solve_r_level(entry, qty, direction, cfg, tick, r=thr_r)
    r1_gross = (entry + (entry - stop) if direction == LONG
                else entry - (stop - entry))
    tr(f"  LEVELS  stop {_fmt(stop)} | target {_fmt(target)} "
       f"| tp needs trade-through >= {_fmt(fill_level)}")
    tr(f"          threshold_R = phi {cfg.phi} x target_R "
       f"{cfg.target_r_multiple} x {cfg.time_stop_bars}/{cfg.max_hold_bars} "
       f"= {thr_r:.6g}R")
    tr(f"          +{thr_r:.6g}R net {_fmt(r1_level)} (gross 1R would be "
       f"{_fmt(r1_gross)}) -- the STATE CHECK tests the NET level")

    # ---- walk the 1m path -------------------------------------------------
    exit_ts = exit_px = None
    exit_reason = resolution = None
    stop_quality = "normal"
    tp_touched_not_filled = False
    tp_touch_then = None
    touched_threshold = False        # informational only -- NOT a rule
    at_threshold_at_checkpoint = None
    checkpoint_price = None
    mfe = mae = 0.0
    exit_fee_rate = cfg.taker_fee

    walk = bars_1m[:max_walk_minutes(cfg)]
    # Decision on the CLOSE of the 15m bar `time_stop_bars` after entry;
    # execution on the first 1m bar of the NEXT 15m bar, mirroring the entry
    # convention (decide on a closed bar, act on the next one).
    # BOTH exits use the SAME convention, matching entry: decide on a CLOSED
    # 15m bar, execute at the first 1m close of the following bar. Realised
    # holds are therefore time_stop_bars+1 and max_hold_bars+1 bars.
    checkpoint_close_ts = (entry_ts + BAR_15M_MS * cfg.time_stop_bars
                           + BAR_15M_MS - BAR_1M_MS)
    time_stop_exec_ts = entry_ts + BAR_15M_MS * (cfg.time_stop_bars + 1)
    max_hold_close_ts = (entry_ts + BAR_15M_MS * cfg.max_hold_bars
                         + BAR_15M_MS - BAR_1M_MS)
    max_hold_exec_ts = entry_ts + BAR_15M_MS * (cfg.max_hold_bars + 1)
    tr(f"  WALK    {len(walk) - 1} 1m bars after the entry minute")
    tr(f"          checkpoint CLOSE   {checkpoint_close_ts} (close of 15m bar "
       f"{cfg.time_stop_bars} after entry) -- STATE CHECK")
    tr(f"          time-stop execution {time_stop_exec_ts} (first 1m close of "
       f"bar {cfg.time_stop_bars + 1}; only if BELOW threshold at that close)")
    tr(f"          max-hold CLOSE     {max_hold_close_ts} (close of 15m bar "
       f"{cfg.max_hold_bars} after entry)")
    tr(f"          max-hold execution  {max_hold_exec_ts} (first 1m close of "
       f"bar {cfg.max_hold_bars + 1})")
    if not cfg.time_stop_enabled:
        tr(f"          NO_TIME_STOP arm: checkpoint disabled")

    # Exit detection starts at the minute AFTER entry. The entry minute's own
    # high/low happened before the fill, so testing them would exit on price
    # action the position was never exposed to.
    for i, b in enumerate(walk[1:], start=1):
        ts = int(b["ts"])
        hi, lo = float(b["high"]), float(b["low"])

        if direction == LONG:
            mfe = max(mfe, (hi - entry) * qty)
            mae = min(mae, (lo - entry) * qty)
            hit_stop = lo <= stop
            hit_tp = hi >= fill_level
            touched_tp = hi >= target
            if hi >= r1_level:
                touched_threshold = True
        else:
            mfe = max(mfe, (entry - lo) * qty)
            mae = min(mae, (entry - hi) * qty)
            hit_stop = hi >= stop
            hit_tp = lo <= fill_level
            touched_tp = lo <= target
            if lo <= r1_level:
                touched_threshold = True

        if touched_tp and not hit_tp:
            tp_touched_not_filled = True

        if hit_stop and hit_tp:
            # Both levels inside one minute -> ordering unknowable from 1m OHLC.
            exit_reason, resolution = "stop", "assumed"
            exit_px = stop_fill_price(stop, direction, cfg, symbol, tick)
            exit_ts = ts
            tr(f"    [{i:3d}] ts={ts} h={_fmt(hi)} l={_fmt(lo)}  BOTH levels "
               f"in one minute -> stop-first (assumed)")
            break
        if hit_stop:
            exit_reason, resolution = "stop", "observed"
            exit_px = stop_fill_price(stop, direction, cfg, symbol, tick)
            exit_ts = ts
            # "Unresolved" = price ran well past the stop inside the trigger
            # minute, so the haircut is a guess. True gaps are undetectable
            # because 1m opens are synthetic.
            beyond = (stop - lo) if direction == LONG else (hi - stop)
            if beyond > abs(entry - stop) * cfg.stop_unresolved_frac:
                stop_quality = "unresolved"
            tr(f"    [{i:3d}] ts={ts} h={_fmt(hi)} l={_fmt(lo)}  STOP "
               f"(observed) fill {_fmt(exit_px)} quality={stop_quality}")
            break
        if hit_tp:
            exit_reason, resolution = "target", "observed"
            exit_px = target
            exit_fee_rate = cfg.maker_fee
            exit_ts = ts
            tr(f"    [{i:3d}] ts={ts} h={_fmt(hi)} l={_fmt(lo)}  TARGET "
               f"(observed) traded through {_fmt(fill_level)}, fill "
               f"{_fmt(target)} maker")
            break

        if tp_touched_not_filled and tp_touch_then is None:
            tp_touch_then = "continued"
        tr(f"    [{i:3d}] ts={ts} h={_fmt(hi)} l={_fmt(lo)}")

        # ---- checkpoint STATE CHECK ---------------------------------------
        # Is the trade AT OR ABOVE threshold_R right now, at this bar's close?
        # Not "did it ever touch". Evaluated at the first 1m bar at or after
        # the checkpoint close, so a data gap cannot skip the decision.
        if (cfg.time_stop_enabled and at_threshold_at_checkpoint is None
                and ts >= checkpoint_close_ts):
            checkpoint_price = float(b["close"])
            at_threshold_at_checkpoint = bool(
                checkpoint_price >= r1_level if direction == LONG
                else checkpoint_price <= r1_level)
            tr(f"    [{i:3d}] ts={ts} CHECKPOINT close={_fmt(checkpoint_price)} "
               f"vs threshold {_fmt(r1_level)} -> "
               f"{'AT/ABOVE -> continue' if at_threshold_at_checkpoint else 'BELOW -> time stop'}"
               f"   (touched intrabar earlier: {touched_threshold} -- "
               f"informational, NOT the test)")

        # ---- time stop: executes only if the STATE CHECK failed ------------
        if (cfg.time_stop_enabled and ts >= time_stop_exec_ts
                and at_threshold_at_checkpoint is False):
            exit_reason, resolution = "time_stop", "observed"
            exit_px = round_to_tick(float(b["close"]), tick, "nearest")
            exit_ts = ts
            tr(f"    [{i:3d}] ts={ts} TIME STOP: below threshold at the "
               f"checkpoint close -> exit at 1m close {_fmt(exit_px)}")
            break

        # ---- max hold: the cap for trades that passed the checkpoint -------
        # Decided on the close of bar max_hold_bars, executed on the first 1m
        # close of bar max_hold_bars+1 -- the same convention as the time stop
        # and as entry. The trade therefore holds max_hold_bars COMPLETE bars.
        if ts >= max_hold_exec_ts:
            exit_reason, resolution = "max_hold", "observed"
            exit_px = round_to_tick(float(b["close"]), tick, "nearest")
            exit_ts = ts
            tr(f"    [{i:3d}] ts={ts} MAX HOLD (open at the close of bar "
               f"{cfg.max_hold_bars}) -> exit at 1m close {_fmt(exit_px)}")
            break

    if exit_ts is None:
        # The buffer is derived from max_hold_bars, so exhausting it means the
        # DATA ran out (end of dataset or a 1m coverage hole), not that a
        # trading rule fired. Counted separately; never a trading decision.
        last = walk[-1]
        exit_reason, resolution = "insufficient_data", "observed"
        exit_px = round_to_tick(float(last["close"]), tick, "nearest")
        exit_ts = int(last["ts"])
        tr(f"  END     INSUFFICIENT DATA: only {len(walk)} 1m bars available, "
           f"need {max_walk_minutes(cfg)}; exit at last close {_fmt(exit_px)} "
           f"(at_threshold_at_checkpoint={at_threshold_at_checkpoint})")

    gross, fees, net = trade_pnl(entry, exit_px, qty, direction,
                                 cfg.taker_fee, exit_fee_rate)
    slip = qty * abs(entry - float(e_bar["close"]))
    if exit_reason == "stop":
        slip += qty * abs(stop - exit_px)
    tr(f"  PNL     gross = q {_fmt(qty)} x ({_fmt(exit_px)} - {_fmt(entry)}) "
       f"= {_fmt(gross, 6)}")
    tr(f"          fees  = q*P*{cfg.taker_fee} "
       f"{_fmt(qty * entry * cfg.taker_fee, 6)} + q*X*{exit_fee_rate} "
       f"{_fmt(qty * exit_px * exit_fee_rate, 6)} = {_fmt(fees, 6)}")
    tr(f"          net   = {_fmt(gross, 6)} - {_fmt(fees, 6)} = {_fmt(net, 6)}"
       f"   R = {net / cfg.risk_usd:.4f}")

    bars_held = int((exit_ts - entry_ts) // BAR_15M_MS)
    return {
        "symbol": symbol,
        "direction": direction,
        "signal_bar_ts": sig_ts,
        "entry_ts": entry_ts,
        "entry_price": entry,
        "stop_price": stop,
        "target_price": target,
        "qty": qty,
        "notional": notional,
        "exit_ts": exit_ts,
        "exit_price": exit_px,
        "exit_reason": exit_reason,
        "gross_pnl": gross,
        "fees_paid": fees,
        "slippage_paid": slip,
        "net_pnl": net,
        "r_multiple": r_multiple(net, cfg),
        "mfe": mfe,
        "mae": mae,
        "bars_held": bars_held,
        "resolution": resolution,
        "tp_touched_not_filled": tp_touched_not_filled,
        "tp_after_touch": tp_touch_then or "",
        "stop_fill_quality": stop_quality,
        "stop_binding_mechanism": stop_mech,
        "size_binding_mechanism": RISK_RULE,
        "threshold_r": thr_r,
        "threshold_price": r1_level,
        "at_threshold_at_checkpoint": at_threshold_at_checkpoint,
        "checkpoint_price": checkpoint_price,
        # Informational only. Records whether the OLD latch rule would have
        # given a different answer; no rule reads it.
        "touched_threshold_intrabar": touched_threshold,
    }


# --------------------------------------------------------------------------
# data loading -- drops forbidden columns at the boundary
# --------------------------------------------------------------------------

def load_15m(derived_dir, symbol):
    """15m bars. open_synth is dropped here so no downstream code can read it."""
    import pyarrow.parquet as pq
    df = pq.read_table(
        f"{derived_dir}/ohlcv_15m/{symbol}.parquet").to_pandas()
    return df.drop(columns=["open_synth"]).sort_values(
        "ts", kind="mergesort").reset_index(drop=True)


def load_1m(derived_dir, symbol, years=None, authorised=False,
            holdout_year=HOLDOUT_YEAR, holdout_start_ms=HOLDOUT_START_MS):
    """1m bars as a numpy structured array of ts/high/low/close ONLY.

    REFUSES THE HOLDOUT BY DEFAULT (Appendix M.2). `authorised` defaults to
    False and must be passed explicitly to read a partition at or after
    `holdout_year`, matching the pattern `src/folds/schedule.load_bars` already
    uses. Passing `years=None` means every partition on disk, which includes
    the holdout, so the default path refuses that too rather than quietly
    loading it.

    open_synth and volume are dropped at the boundary: the spec forbids reading
    1m volume and 1m open, and the cheapest way to guarantee that is to not
    carry the columns at all.
    """
    import glob
    import pandas as pd
    import pyarrow.parquet as pq

    paths = sorted(glob.glob(
        f"{derived_dir}/ohlcv_1m/symbol={symbol}/year=*/data.parquet"))

    def _year(p):
        return int(p.split("year=")[1].split("/")[0])

    if years is not None:
        paths = [p for p in paths if _year(p) in years]
    if not authorised:
        sealed = sorted({_year(p) for p in paths if _year(p) >= holdout_year})
        if sealed:
            raise HoldoutSealError(
                f"{symbol}: 1m partition(s) {sealed} lie at or after the "
                f"holdout boundary ({HOLDOUT_START_ISO}), which is SEALED. "
                f"Use simulate.in_sample_years() to clamp the requested set. "
                f"Pass authorised=True only for the single pre-registered "
                f"holdout evaluation at step 9 of the 4.4 sequence.")
    if not paths:
        raise FileNotFoundError(
            f"{symbol}: no 1m partitions selected from {derived_dir} for "
            f"years={years}")
    frames = [pq.read_table(p, columns=["ts", "high", "low", "close"]).to_pandas()
              for p in paths]
    df = pd.concat(frames, ignore_index=True).sort_values(
        "ts", kind="mergesort").reset_index(drop=True)
    recs = df.to_records(index=False)
    # Belt and braces: a mislabelled partition would defeat the year check.
    if not authorised and len(recs) and int(recs["ts"][-1]) >= holdout_start_ms:
        raise HoldoutSealError(
            f"{symbol}: 1m partitions for years {sorted(set(years)) if years else 'ALL'} "
            f"contain a bar at {int(recs['ts'][-1])}, at or after the SEALED "
            f"holdout boundary. The partition labels do not match their "
            f"contents -- report this rather than working around it.")
    return recs


def slice_1m(recs, start_ts, n):
    """The n 1m bars starting at start_ts (inclusive), by binary search on ts."""
    ts = recs["ts"]
    i = int(np.searchsorted(ts, start_ts, side="left"))
    return recs[i:i + n]


# --------------------------------------------------------------------------
# portfolio-level run
# --------------------------------------------------------------------------

def run_backtest(signals, bars15_by_symbol, bars1m_by_symbol, cfg, ticks,
                 donchian_period=20, trace_signal_ts=None, mode="portfolio",
                 order_specs=None, exclude_holdout_crossing=True,
                 authorised_1m=False, holdout_start_ms=HOLDOUT_START_MS):
    """Walk signals in time order. `mode` selects which constraints apply.

    PORTFOLIO mode (realism instrument -- equity curve, drawdown, occupancy):
      1. one open position per symbol, no pyramiding;
      2. cooldown -- after a stop-out, that symbol+direction is blocked for
         cfg.cooldown_bars bars. The old "until a new donchian_period-bar
         extreme" condition was REMOVED in 3R: a long entry requires a close
         above the Donchian-20 upper, which IS a new 20-bar high, so the
         clearing condition was entailed by the triggering condition and the
         rule could never bind. cooldown_bars survives as a registered sweep
         dimension and is inert at its default of 0;
      3. margin -- refuse a trade whose notional, added to positions already
         open at its entry, would exceed equity * max_leverage.

    SIGNAL mode (edge-test instrument): every signal is simulated
    independently. No position limit, no cooldown, no margin cap, no
    interaction of any kind. Trades may overlap. This is the only mode in
    which a gated-vs-ungated comparison is interpretable, because portfolio
    censoring drops ~30% of signals by arrival order rather than by the gate.

    Both modes share simulate_trade; only the constraint set differs.
    """
    if mode not in ("portfolio", "signal"):
        raise ValueError(f"unknown mode {mode!r}")
    import pandas as pd

    sig = signals.sort_values(
        ["signal_bar_ts", "symbol", "direction"], kind="mergesort"
    ).reset_index(drop=True)

    order_specs = order_specs or {}
    open_positions = []          # dicts with symbol, entry_ts, exit_ts, notional
    blocked = {}                 # (symbol, direction) -> ts of stop-out
    trades = []
    refused = {"open_position": 0, "cooldown": 0, "insufficient_margin": 0,
               "no_1m_coverage": 0, "min_qty": 0, "holdout_boundary": 0}
    traces = {}

    for _, s in sig.iterrows():
        sym = s["symbol"]
        direction = s["direction"]
        sig_ts = int(s["signal_bar_ts"])
        entry_ts = sig_ts + BAR_15M_MS

        # ---- Appendix M.3: exclusion runs FIRST, before any 1m data is
        # requested. It is decided by arithmetic on `entry_ts` alone, so no
        # sealed bar is touched to find out whether a sealed bar is needed.
        # Ordering is what makes the seal provable: because this runs first, a
        # `require_in_sample_window` raise below is unambiguous evidence of a
        # bug. If exclusion ran only after the loader complained, refusals
        # would be routine and would stop carrying information.
        if exclude_holdout_crossing and crosses_holdout(entry_ts, cfg,
                                                        holdout_start_ms):
            refused["holdout_boundary"] += 1
            continue
        require_in_sample_window(entry_ts, cfg, sym, authorised_1m,
                                 holdout_start_ms)

        open_positions = [p for p in open_positions if p["exit_ts"] > entry_ts]

        if mode == "portfolio":
            if any(p["symbol"] == sym for p in open_positions):
                refused["open_position"] += 1
                continue

            key = (sym, direction)
            if key in blocked:
                # Bar count only. The new-extreme condition was a logical
                # no-op and is gone; see the docstring.
                bars_elapsed = (sig_ts - blocked[key]) // BAR_15M_MS
                if bars_elapsed < cfg.cooldown_bars:
                    refused["cooldown"] += 1
                    continue
                del blocked[key]

        recs = bars1m_by_symbol[sym]
        walk = slice_1m(recs, entry_ts, max_walk_minutes(cfg))
        if len(walk) == 0 or int(walk[0]["ts"]) != entry_ts:
            refused["no_1m_coverage"] += 1
            continue

        want_trace = (trace_signal_ts is not None and sig_ts == trace_signal_ts)
        tr = Trace(enabled=want_trace)
        if want_trace:
            tr(f"TRACE {sym} {direction} signal_bar_ts={sig_ts}")
            for c in ("close", "ema_fast", "ema_slow", "donchian_upper",
                      "donchian_lower", "rvol", "rsi", "atr"):
                tr(f"  SIGNAL  {c:16s} = {_fmt(float(s[c]))}")

        tick = ticks[sym].tick_at(sig_ts)
        t = simulate_trade(s, walk, cfg, tick, trace=tr,
                           order_spec=order_specs.get(sym))
        if t is None:
            refused["no_1m_coverage"] += 1
            continue
        if "_refused" in t:
            # Below the exchange minimum order size. Refused loudly, in BOTH
            # modes: it is an exchange constraint, not a portfolio policy.
            refused["min_qty"] += 1
            if want_trace:
                traces[sig_ts] = tr.text()
            continue

        # Margin: could this notional have been carried alongside the rest?
        # Named insufficient_margin, NOT funding -- funding rate is banned from
        # trade logic and real funding code will sit beside this later.
        if mode == "portfolio":
            concurrent = sum(p["notional"] for p in open_positions)
            cap = cfg.equity_usd * cfg.max_leverage
            if concurrent + t["notional"] > cap:
                refused["insufficient_margin"] += 1
                if want_trace:
                    tr(f"  REFUSED insufficient_margin: {_fmt(concurrent, 2)} "
                       f"+ {_fmt(t['notional'], 2)} > cap {_fmt(cap, 2)}")
                    traces[sig_ts] = tr.text()
                continue

        t["variant"] = s.get("variant", "gated")
        # rvol travels with the trade so the gated arm can be obtained by
        # FILTERING this table rather than by a second simulation.
        t["rvol"] = float(s["rvol"])
        trades.append(t)
        if mode == "portfolio":
            open_positions.append({"symbol": sym, "entry_ts": t["entry_ts"],
                                   "exit_ts": t["exit_ts"],
                                   "notional": t["notional"]})
            if t["exit_reason"] == "stop":
                blocked[(sym, direction)] = t["exit_ts"]
        if want_trace:
            traces[sig_ts] = tr.text()

    cols = ["symbol", "direction", "signal_bar_ts", "entry_ts", "entry_price",
            "stop_price", "target_price", "qty", "notional", "exit_ts",
            "exit_price", "exit_reason", "gross_pnl", "fees_paid",
            "slippage_paid", "net_pnl", "r_multiple", "mfe", "mae",
            "bars_held", "variant", "resolution", "tp_touched_not_filled",
            "tp_after_touch", "stop_fill_quality", "stop_binding_mechanism",
            "size_binding_mechanism", "threshold_r", "threshold_price",
            "at_threshold_at_checkpoint", "checkpoint_price",
            "touched_threshold_intrabar", "rvol"]
    df = pd.DataFrame(trades, columns=cols) if trades else pd.DataFrame(
        columns=cols)
    return df, refused, traces


def attach_flag_overlap(trades, divergence_path):
    """Mark trades whose SIGNAL bar appears in the reconstruction flag list.

    Reported, never filtered -- the flag list is not an exclusion filter.
    """
    import pyarrow.parquet as pq
    if len(trades) == 0:
        trades["flagged_bar_overlap"] = []
        return trades
    div = pq.read_table(divergence_path).to_pandas()
    flagged = set(zip(div["symbol"], div["ts"]))
    trades = trades.copy()
    trades["flagged_bar_overlap"] = [
        (s, int(t)) in flagged
        for s, t in zip(trades["symbol"], trades["signal_bar_ts"])]
    return trades


def summarize(trades, refused):
    """Provenance counters. These are deliverables, not diagnostics."""
    n = len(trades)
    return {
        "trades": n,
        "resolved_by_observation": int((trades["resolution"] == "observed").sum()) if n else 0,
        "decided_by_assumption": int((trades["resolution"] == "assumed").sum()) if n else 0,
        "tp_touched_not_filled": int(trades["tp_touched_not_filled"].sum()) if n else 0,
        "stop_fill_unresolved": int((trades["stop_fill_quality"] == "unresolved").sum()) if n else 0,
        "flagged_bar_overlap": int(trades["flagged_bar_overlap"].sum()) if n and "flagged_bar_overlap" in trades else 0,
        "refused_open_position": refused["open_position"],
        "refused_cooldown": refused["cooldown"],
        "refused_insufficient_margin": refused["insufficient_margin"],
        "refused_no_1m_coverage": refused["no_1m_coverage"],
        # Appendix M.3. Trades whose resolution would have needed sealed data,
        # removed at signal time. Reported per fold per symbol by the caller.
        "refused_holdout_boundary": refused.get("holdout_boundary", 0),
        "refused_min_qty": refused.get("min_qty", 0),
        # stop_binding_mechanism, per A7. Closes the question of whether the
        # "volatility-adaptive" stop is actually running as one.
        "stop_binding_atr": int((trades["stop_binding_mechanism"] == "atr").sum()) if n else 0,
        "stop_binding_floor": int((trades["stop_binding_mechanism"] == "floor").sum()) if n else 0,
        "stop_binding_cap": int((trades["stop_binding_mechanism"] == "cap").sum()) if n else 0,
        # size_binding_mechanism, per A7. Taken trades are always risk_rule
        # because leverage_cap and min_qty REFUSE rather than resize -- see
        # reports/08_point_3r.md section 9.
        "size_binding_risk_rule": int((trades["size_binding_mechanism"] == "risk_rule").sum()) if n else 0,
        "size_binding_leverage_cap": refused["insufficient_margin"],
        "size_binding_min_qty": refused.get("min_qty", 0),
    }


EXIT_REASONS = ["target", "stop", "time_stop", "max_hold", "insufficient_data"]


def exit_reason_distribution(trades):
    """Counts and percentages per exit reason. Report-only."""
    n = len(trades)
    out = {}
    for r in EXIT_REASONS:
        c = int((trades["exit_reason"] == r).sum()) if n else 0
        out[r] = (c, (100.0 * c / n) if n else 0.0)
    unknown = set(trades["exit_reason"]) - set(EXIT_REASONS) if n else set()
    if unknown:
        raise AssertionError(f"unexpected exit_reason values: {unknown}")
    return out


def stop_band_binding(trades, cfg=None):
    """How often the ATR stop was clamped by the derived floor or the cap.

    Reads the recorded `stop_binding_mechanism` rather than re-deriving the
    band from prices: the floor is now per-symbol, so a single cfg-wide
    threshold could not classify a mixed-symbol table correctly, and the
    mechanism is decided on the RAW distance before tick rounding anyway.
    """
    n = len(trades)
    if n == 0:
        return {"floor": (0, 0.0), "cap": (0, 0.0), "atr": (0, 0.0)}
    out = {}
    for mech in ("floor", "cap", "atr"):
        c = int((trades["stop_binding_mechanism"] == mech).sum())
        out[mech] = (c, 100.0 * c / n)
    return out


def holding_time_distribution(trades):
    """bars_held summary overall and per exit reason. Report-only."""
    n = len(trades)
    if n == 0:
        return {}
    out = {}
    for r in ["ALL"] + EXIT_REASONS:
        sub = trades if r == "ALL" else trades[trades["exit_reason"] == r]
        if len(sub) == 0:
            out[r] = None
            continue
        b = sub["bars_held"].to_numpy()
        out[r] = {
            "n": int(len(b)),
            "min": int(b.min()), "median": float(np.median(b)),
            "mean": float(b.mean()), "max": int(b.max()),
            "p90": float(np.percentile(b, 90)),
        }
    return out
