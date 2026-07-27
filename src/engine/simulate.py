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

from costs import (LONG, SHORT, CostConfig, entry_fill_price, position_size,
                   r_multiple, round_to_tick, solve_target, stop_fill_price,
                   stop_price, trade_pnl)

BAR_15M_MS = 900_000
BAR_1M_MS = 60_000

TIME_STOP_BARS = 16          # decide at the close of the 16th 15m bar after entry
# Entry minute, then bars T+1..T+16, then the single T+17 execution minute.
MAX_1M_WALK = TIME_STOP_BARS * 15 + 1


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


def simulate_trade(signal, bars_1m, cfg, tick, trace=None):
    """Simulate one trade from a signal row.

    `bars_1m` is a structured view of the 1m bars from the first minute of the
    15m bar AFTER the signal bar, ascending, with fields ts/high/low/close.
    Returns a dict (the trade row) or None if the trade could not be entered.
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
    stop = stop_price(entry, atr, direction, cfg, tick)
    raw_dist = cfg.stop_atr_mult * atr
    pct = abs(entry - stop) / entry
    tr(f"  STOP    atr={_fmt(atr)} x{cfg.stop_atr_mult} = {_fmt(raw_dist)}  "
       f"floor {cfg.stop_min_pct:.3%} cap {cfg.stop_max_pct:.3%} of "
       f"{_fmt(entry)} -> stop {_fmt(stop)} ({pct:.4%} of entry)")

    qty = position_size(entry, stop, direction, cfg, symbol)
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
    r1_level = (entry + (entry - stop) if direction == LONG
                else entry - (stop - entry))
    tr(f"  LEVELS  stop {_fmt(stop)} | target {_fmt(target)} "
       f"| tp needs trade-through >= {_fmt(fill_level)} "
       f"| +1R level {_fmt(r1_level)}")

    # ---- walk the 1m path -------------------------------------------------
    exit_ts = exit_px = None
    exit_reason = resolution = None
    stop_quality = "normal"
    tp_touched_not_filled = False
    tp_touch_then = None
    reached_1r = False
    mfe = mae = 0.0
    exit_fee_rate = cfg.taker_fee

    walk = bars_1m[:MAX_1M_WALK]
    time_stop_deadline = sig_ts + BAR_15M_MS * (TIME_STOP_BARS + 1)
    tr(f"  WALK    {len(walk) - 1} 1m bars after the entry minute, "
       f"time-stop execution at {time_stop_deadline}")

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
                reached_1r = True
        else:
            mfe = max(mfe, (entry - lo) * qty)
            mae = min(mae, (entry - hi) * qty)
            hit_stop = hi >= stop
            hit_tp = lo <= fill_level
            touched_tp = lo <= target
            if lo <= r1_level:
                reached_1r = True

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
            if beyond > abs(entry - stop) * 0.5:
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

        # ---- time stop ----------------------------------------------------
        # Decision is taken on the CLOSE of the 16th 15m bar after entry; the
        # exit executes on the first 1m bar of T+17, mirroring entry.
        if ts >= time_stop_deadline and not reached_1r:
            exit_reason, resolution = "time_stop", "observed"
            exit_px = round_to_tick(float(b["close"]), tick, "nearest")
            exit_ts = ts
            tr(f"    [{i:3d}] ts={ts} TIME STOP: +1R ({_fmt(r1_level)}) never "
               f"touched -> exit at 1m close {_fmt(exit_px)}")
            break

    if exit_ts is None:
        # Walk exhausted without stop/target and +1R was reached: close out at
        # the last available minute so no trade is left dangling.
        last = walk[-1]
        exit_reason, resolution = "walk_end", "observed"
        exit_px = round_to_tick(float(last["close"]), tick, "nearest")
        exit_ts = int(last["ts"])
        tr(f"  END     walk exhausted, exit at {_fmt(exit_px)} "
           f"(reached_1r={reached_1r})")

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
        "reached_1r": reached_1r,
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

def new_extreme_flags(df15, period):
    """Per-bar: did this bar set a new `period`-bar high / low?"""
    import pandas as pd
    hi = df15["high"].to_numpy()
    lo = df15["low"].to_numpy()
    prior_hi = pd.Series(hi).rolling(period).max().shift(1).to_numpy()
    prior_lo = pd.Series(lo).rolling(period).min().shift(1).to_numpy()
    return hi > prior_hi, lo < prior_lo


def run_backtest(signals, bars15_by_symbol, bars1m_by_symbol, cfg, ticks,
                 donchian_period=20, trace_signal_ts=None):
    """Walk signals in time order, applying portfolio constraints.

    Constraints, in the order they are checked:
      1. one open position per symbol, no pyramiding;
      2. cooldown -- after a stop-out, that symbol+direction is blocked until a
         new `donchian_period`-bar extreme in that direction;
      3. funding -- refuse a trade whose notional, added to positions already
         open at its entry, would exceed equity * max_leverage.
    """
    import pandas as pd

    sig = signals.sort_values(
        ["signal_bar_ts", "symbol", "direction"], kind="mergesort"
    ).reset_index(drop=True)

    extremes = {}
    for sym, df15 in bars15_by_symbol.items():
        nh, nl = new_extreme_flags(df15, donchian_period)
        extremes[sym] = (df15["ts"].to_numpy(), nh, nl)

    open_positions = []          # dicts with symbol, entry_ts, exit_ts, notional
    blocked = {}                 # (symbol, direction) -> ts of stop-out
    trades = []
    refused = {"open_position": 0, "cooldown": 0, "funding": 0,
               "no_1m_coverage": 0}
    traces = {}

    for _, s in sig.iterrows():
        sym = s["symbol"]
        direction = s["direction"]
        sig_ts = int(s["signal_bar_ts"])
        entry_ts = sig_ts + BAR_15M_MS

        open_positions = [p for p in open_positions if p["exit_ts"] > entry_ts]

        if any(p["symbol"] == sym for p in open_positions):
            refused["open_position"] += 1
            continue

        key = (sym, direction)
        if key in blocked:
            ts_arr, nh, nl = extremes[sym]
            flags = nh if direction == LONG else nl
            window = (ts_arr > blocked[key]) & (ts_arr <= sig_ts)
            if not bool(np.any(flags[window] & np.isfinite(flags[window]))):
                refused["cooldown"] += 1
                continue
            del blocked[key]

        recs = bars1m_by_symbol[sym]
        walk = slice_1m(recs, entry_ts, MAX_1M_WALK)
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
        t = simulate_trade(s, walk, cfg, tick, trace=tr)
        if t is None:
            refused["no_1m_coverage"] += 1
            continue

        # Funding: could this notional have been carried alongside the rest?
        concurrent = sum(p["notional"] for p in open_positions)
        cap = cfg.equity_usd * cfg.max_leverage
        if concurrent + t["notional"] > cap:
            refused["funding"] += 1
            if want_trace:
                tr(f"  REFUSED funding: {_fmt(concurrent, 2)} + "
                   f"{_fmt(t['notional'], 2)} > cap {_fmt(cap, 2)}")
                traces[sig_ts] = tr.text()
            continue

        t["variant"] = s.get("variant", "gated")
        trades.append(t)
        open_positions.append({"symbol": sym, "entry_ts": t["entry_ts"],
                               "exit_ts": t["exit_ts"],
                               "notional": t["notional"]})
        if t["exit_reason"] == "stop":
            blocked[key] = t["exit_ts"]
        if want_trace:
            traces[sig_ts] = tr.text()

    cols = ["symbol", "direction", "signal_bar_ts", "entry_ts", "entry_price",
            "stop_price", "target_price", "qty", "notional", "exit_ts",
            "exit_price", "exit_reason", "gross_pnl", "fees_paid",
            "slippage_paid", "net_pnl", "r_multiple", "mfe", "mae",
            "bars_held", "variant", "resolution", "tp_touched_not_filled",
            "tp_after_touch", "stop_fill_quality", "reached_1r"]
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
    out = {
        "trades": n,
        "resolved_by_observation": int((trades["resolution"] == "observed").sum()) if n else 0,
        "decided_by_assumption": int((trades["resolution"] == "assumed").sum()) if n else 0,
        "tp_touched_not_filled": int(trades["tp_touched_not_filled"].sum()) if n else 0,
        "stop_fill_unresolved": int((trades["stop_fill_quality"] == "unresolved").sum()) if n else 0,
        "flagged_bar_overlap": int(trades["flagged_bar_overlap"].sum()) if n and "flagged_bar_overlap" in trades else 0,
        "refused_open_position": refused["open_position"],
        "refused_cooldown": refused["cooldown"],
        "refused_funding": refused["funding"],
        "refused_no_1m_coverage": refused["no_1m_coverage"],
    }
    return out
