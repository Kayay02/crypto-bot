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

def max_walk_minutes(cfg):
    """1m bars to load per trade. DERIVED from max_hold_bars, never a rule.

    Entry minute, then bars 1..max_hold_bars, then the single execution minute
    of bar max_hold_bars+1. Sizing this buffer from the time stop is what made
    the walk act as an unconditional exit (defect B1); it must always be large
    enough that running out of buffer means running out of DATA.
    """
    return cfg.max_hold_bars * 15 + 2


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
    checkpoint_close_ts = (entry_ts + BAR_15M_MS * cfg.time_stop_bars
                           + BAR_15M_MS - BAR_1M_MS)
    time_stop_exec_ts = entry_ts + BAR_15M_MS * (cfg.time_stop_bars + 1)
    max_hold_deadline = entry_ts + BAR_15M_MS * cfg.max_hold_bars
    tr(f"  WALK    {len(walk) - 1} 1m bars after the entry minute")
    tr(f"          checkpoint CLOSE   {checkpoint_close_ts} (close of 15m bar "
       f"{cfg.time_stop_bars} after entry) -- STATE CHECK")
    tr(f"          time-stop execution {time_stop_exec_ts} (only if BELOW "
       f"threshold at that close)")
    tr(f"          max-hold execution  {max_hold_deadline} (bar "
       f"{cfg.max_hold_bars} after entry)")
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
        if ts >= max_hold_deadline:
            exit_reason, resolution = "max_hold", "observed"
            exit_px = round_to_tick(float(b["close"]), tick, "nearest")
            exit_ts = ts
            tr(f"    [{i:3d}] ts={ts} MAX HOLD ({cfg.max_hold_bars} bars) "
               f"-> exit at 1m close {_fmt(exit_px)}")
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


def load_1m(derived_dir, symbol, years=None):
    """1m bars as a numpy structured array of ts/high/low/close ONLY.

    open_synth and volume are dropped at the boundary: the spec forbids reading
    1m volume and 1m open, and the cheapest way to guarantee that is to not
    carry the columns at all.
    """
    import glob
    import pandas as pd
    import pyarrow.parquet as pq

    paths = sorted(glob.glob(
        f"{derived_dir}/ohlcv_1m/symbol={symbol}/year=*/data.parquet"))
    if years is not None:
        paths = [p for p in paths
                 if int(p.split("year=")[1].split("/")[0]) in years]
    frames = [pq.read_table(p, columns=["ts", "high", "low", "close"]).to_pandas()
              for p in paths]
    df = pd.concat(frames, ignore_index=True).sort_values(
        "ts", kind="mergesort").reset_index(drop=True)
    return df.to_records(index=False)


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
                 order_specs=None):
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
               "no_1m_coverage": 0, "min_qty": 0}
    traces = {}

    for _, s in sig.iterrows():
        sym = s["symbol"]
        direction = s["direction"]
        sig_ts = int(s["signal_bar_ts"])
        entry_ts = sig_ts + BAR_15M_MS

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
