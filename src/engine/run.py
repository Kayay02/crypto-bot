"""Engine entry point: load -> signals -> simulate -> summarize.

Deliberately produces trade rows and provenance counters only. It does not
compute or print aggregate performance -- validation design is a later phase
and seeing results now would contaminate it.
"""

import argparse
import hashlib
import os

import pandas as pd

import contracts
import costs
import signals as sg
import simulate

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DERIVED = os.path.join(ROOT, "data", "derived")
SYMBOLS = ["BTCUSDT", "ETHUSDT", "SOLUSDT"]

# Columns whose float values are rounded before hashing, so that determinism
# checks are not defeated by last-bit noise from a different numpy build.
FLOAT_COLS = ["entry_price", "stop_price", "target_price", "qty", "notional",
              "exit_price", "gross_pnl", "fees_paid", "slippage_paid",
              "net_pnl", "r_multiple", "mfe", "mae"]


def run(symbols=SYMBOLS, start_ts=None, end_ts=None, params=None, cfg=None,
        variant="gated", derived=DERIVED, trace_signal_ts=None):
    params = params or sg.SignalParams()
    cfg = cfg or costs.CostConfig()
    ticks = contracts.load_cache()

    bars15, bars1m, sigs = {}, {}, []
    for sym in symbols:
        df = simulate.load_15m(derived, sym)
        if start_ts is not None:
            df = df[df["ts"] >= start_ts]
        if end_ts is not None:
            df = df[df["ts"] <= end_ts]
        df = df.reset_index(drop=True)
        bars15[sym] = df
        years = sorted(set(pd.to_datetime(df["ts"], unit="ms", utc=True).dt.year))
        # +1 year so a trade opened near a year boundary can still walk forward.
        bars1m[sym] = simulate.load_1m(derived, sym,
                                       years=set(years) | {max(years) + 1})
        s = sg.generate_signals(df, params, sym,
                                apply_rvol_gate=(variant == "gated"))
        if len(s):
            sigs.append(s)

    if not sigs:
        empty = pd.DataFrame()
        return empty, {"open_position": 0, "cooldown": 0, "funding": 0,
                       "no_1m_coverage": 0}, {}

    allsig = pd.concat(sigs, ignore_index=True)
    trades, refused, traces = simulate.run_backtest(
        allsig, bars15, bars1m, cfg, ticks,
        donchian_period=params.donchian, trace_signal_ts=trace_signal_ts)
    trades = simulate.attach_flag_overlap(
        trades, os.path.join(derived, "flags",
                             "reconstruction_divergence.parquet"))
    return trades, refused, traces


def canonical_bytes(trades, ndigits=10):
    """Stable serialization for hashing: fixed column order, rounded floats."""
    if len(trades) == 0:
        return b"EMPTY"
    df = trades.copy().sort_values(
        ["symbol", "signal_bar_ts", "direction"], kind="mergesort"
    ).reset_index(drop=True)
    for c in FLOAT_COLS:
        if c in df.columns:
            df[c] = df[c].astype(float).round(ndigits)
    return df.to_csv(index=False).encode()


def output_hash(trades):
    return hashlib.sha256(canonical_bytes(trades)).hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--symbols", nargs="+", default=SYMBOLS)
    ap.add_argument("--start", type=int, default=None, help="start ts (ms)")
    ap.add_argument("--end", type=int, default=None, help="end ts (ms)")
    ap.add_argument("--variant", choices=["gated", "ungated"], default="gated")
    ap.add_argument("--trace-signal-ts", type=int, default=None,
                    help="dump a full hand-checkable trace for this signal bar")
    ap.add_argument("--out", default=None, help="write trades CSV here")
    ap.add_argument("--summary", action="store_true",
                    help="print provenance counters (never performance)")
    a = ap.parse_args()

    trades, refused, traces = run(
        symbols=a.symbols, start_ts=a.start, end_ts=a.end, variant=a.variant,
        trace_signal_ts=a.trace_signal_ts)

    if a.trace_signal_ts is not None:
        for ts, txt in traces.items():
            print(txt)

    if a.out:
        trades.to_csv(a.out, index=False)
        print(f"wrote {a.out} ({len(trades)} rows)")

    if a.summary:
        s = simulate.summarize(trades, refused)
        print("\n--- provenance counters (no performance figures) ---")
        for k, v in s.items():
            print(f"  {k:28s} {v}")
        print(f"  output_sha256                {output_hash(trades)}")


if __name__ == "__main__":
    main()
