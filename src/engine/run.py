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
        variant="gated", derived=DERIVED, trace_signal_ts=None,
        mode="portfolio"):
    """Run one evaluation mode.

    In SIGNAL mode the caller should pass variant="ungated": the simulation is
    run ONCE over the full ungated universe and the gated arm is obtained by
    filtering the resulting table on rvol (see gated_arm), guaranteeing the two
    arms are the identical universe by construction.

    `cfg` is REQUIRED. There is no default CostConfig because four of its
    parameters have no default (Point 3R): the engine must not be runnable
    against a stale placeholder.
    """
    params = params or sg.SignalParams()
    if cfg is None:
        raise ValueError(
            "run() requires an explicit CostConfig: stop_atr_mult, "
            "stop_max_pct, rvol_threshold and baseline_days have no defaults. "
            "Choosing them is a Point 4 sweep decision.")
    ticks = contracts.load_cache()
    order_specs = contracts.load_order_specs()

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
        # +1 year so a trade opened near a year boundary can still walk forward,
        # then CLAMPED below the holdout (Appendix M.2): that convention is
        # right at every year boundary except the sealed one. Appendix M.3's
        # exclusion in run_backtest is what makes the clamp safe -- no
        # surviving trade needs a year this removes.
        bars1m[sym] = simulate.load_1m(
            derived, sym,
            years=simulate.in_sample_years(set(years) | {max(years) + 1}))
        s = sg.generate_signals(df, params, sym, cfg,
                                apply_rvol_gate=(variant == "gated"))
        if len(s):
            sigs.append(s)

    if not sigs:
        empty = pd.DataFrame()
        return empty, {"open_position": 0, "cooldown": 0,
                       "insufficient_margin": 0, "no_1m_coverage": 0,
                       "min_qty": 0, "holdout_boundary": 0}, {}

    allsig = pd.concat(sigs, ignore_index=True)
    trades, refused, traces = simulate.run_backtest(
        allsig, bars15, bars1m, cfg, ticks,
        donchian_period=params.donchian, trace_signal_ts=trace_signal_ts,
        mode=mode, order_specs=order_specs)
    trades = simulate.attach_flag_overlap(
        trades, os.path.join(derived, "flags",
                             "reconstruction_divergence.parquet"))
    return trades, refused, traces


def gated_arm(trades, rvol_threshold):
    """The gated arm, obtained by FILTERING the ungated trade table.

    Not a second simulation. Partitioning one table guarantees both arms are
    the identical universe by construction, and lets the RVOL threshold be
    swept later at zero additional simulation cost.
    """
    return trades[trades["rvol"] >= rvol_threshold].reset_index(drop=True)


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
    ap.add_argument("--mode", choices=["portfolio", "signal"],
                    default="portfolio")
    ap.add_argument("--trace-signal-ts", type=int, default=None,
                    help="dump a full hand-checkable trace for this signal bar")
    ap.add_argument("--out", default=None, help="write trades CSV here")
    ap.add_argument("--summary", action="store_true",
                    help="print provenance counters (never performance)")
    # No defaults, deliberately: argparse `required=True` mirrors the config
    # contract so the CLI cannot run against a stale placeholder either.
    ap.add_argument("--stop-atr-mult", type=float, required=True)
    ap.add_argument("--stop-max-pct", type=float, required=True)
    ap.add_argument("--rvol-threshold", type=float, required=True)
    ap.add_argument("--baseline-days", type=int, required=True)
    ap.add_argument("--tau", type=float, default=1.0)
    ap.add_argument("--phi", type=float, default=1.0)
    ap.add_argument("--no-time-stop", action="store_true",
                    help="NO_TIME_STOP counterfactual arm (D1). Not baseline.")
    a = ap.parse_args()

    cfg = costs.CostConfig(
        stop_atr_mult=a.stop_atr_mult, stop_max_pct=a.stop_max_pct,
        rvol_threshold=a.rvol_threshold, baseline_days=a.baseline_days,
        tau=a.tau, phi=a.phi, time_stop_enabled=not a.no_time_stop)

    trades, refused, traces = run(
        symbols=a.symbols, start_ts=a.start, end_ts=a.end, variant=a.variant,
        trace_signal_ts=a.trace_signal_ts, mode=a.mode, cfg=cfg)

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
