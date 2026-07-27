"""Counter and diagnostic pass. Report-only: no performance figures.

    python src/engine/diagnostics.py > /tmp/diag.txt
"""

import os
import sys

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import costs  # noqa: E402
import run as engine_run  # noqa: E402
import simulate  # noqa: E402

YEARS = {
    2022: (1640995200000, 1672531199999),
    2023: (1672531200000, 1704067199999),
}
SYMBOLS = ["BTCUSDT", "ETHUSDT", "SOLUSDT"]


def counter_block(trades, refused, label):
    s = simulate.summarize(trades, refused)
    lines = [f"  {label}"]
    for k in ("trades", "resolved_by_observation", "decided_by_assumption",
              "tp_touched_not_filled", "stop_fill_unresolved",
              "flagged_bar_overlap", "refused_open_position",
              "refused_cooldown", "refused_insufficient_margin",
              "refused_no_1m_coverage"):
        lines.append(f"    {k:30s} {s[k]}")
    return "\n".join(lines)


def diag_block(trades, cfg, label):
    lines = [f"  {label}  (n={len(trades)})"]
    if len(trades) == 0:
        return "\n".join(lines + ["    (no trades)"])

    lines.append("    exit-reason distribution:")
    for r, (c, pct) in simulate.exit_reason_distribution(trades).items():
        lines.append(f"      {r:20s} {c:6d}  {pct:6.2f}%")

    band = simulate.stop_band_binding(trades, cfg)
    lines.append("    stop-band binding:")
    for k, (c, pct) in band.items():
        name = {"floor": "1.0% floor", "cap": "3.5% cap",
                "atr": "1.5xATR (neither)"}[k]
        lines.append(f"      {name:20s} {c:6d}  {pct:6.2f}%")

    lines.append("    holding time (bars_held) by exit reason:")
    for r, d in simulate.holding_time_distribution(trades).items():
        if d is None:
            lines.append(f"      {r:20s} -")
            continue
        lines.append(f"      {r:20s} n={d['n']:5d}  min={d['min']:3d} "
                     f"med={d['median']:6.1f} mean={d['mean']:6.2f} "
                     f"p90={d['p90']:6.1f} max={d['max']:3d}")
    return "\n".join(lines)


def main():
    cfg = costs.CostConfig()
    params_rvol_min = 1.5
    out = []
    out.append("COUNTERS AND DIAGNOSTICS — report only, no performance figures")
    out.append(f"config: time_stop_bars={cfg.time_stop_bars} "
               f"max_hold_bars={cfg.max_hold_bars} "
               f"cooldown_bars={cfg.cooldown_bars} "
               f"max_leverage={cfg.max_leverage} "
               f"stop_unresolved_frac={cfg.stop_unresolved_frac}")

    for year, (lo, hi) in YEARS.items():
        out.append("\n" + "=" * 74)
        out.append(f"YEAR {year}")
        out.append("=" * 74)

        # ---- portfolio mode, gated (the realism instrument) --------------
        pf, pf_ref, _ = engine_run.run(symbols=SYMBOLS, start_ts=lo, end_ts=hi,
                                       variant="gated", mode="portfolio")
        out.append("\nPORTFOLIO MODE (gated) — all symbols")
        out.append(counter_block(pf, pf_ref, "counters"))
        out.append(diag_block(pf, cfg, "diagnostics"))
        out.append("\nPORTFOLIO MODE (gated) — per symbol")
        for sym in SYMBOLS:
            sub = pf[pf["symbol"] == sym] if len(pf) else pf
            out.append(diag_block(sub, cfg, sym))
            if len(sub):
                s = simulate.summarize(sub, pf_ref)
                out.append(f"      assumed={s['decided_by_assumption']} "
                           f"tp_touch_no_fill={s['tp_touched_not_filled']} "
                           f"stop_unresolved={s['stop_fill_unresolved']} "
                           f"flagged={s['flagged_bar_overlap']}")

        # ---- signal mode, ONE ungated run; gated arm is a filter ---------
        sg_, sg_ref, _ = engine_run.run(symbols=SYMBOLS, start_ts=lo, end_ts=hi,
                                        variant="ungated", mode="signal")
        out.append("\nSIGNAL MODE — one ungated simulation; gated arm is a "
                   "FILTER of the same table")
        out.append(counter_block(sg_, sg_ref, "counters (ungated universe)"))
        out.append(diag_block(sg_, cfg, "diagnostics (ungated universe)"))

        gated = engine_run.gated_arm(sg_, params_rvol_min)
        out.append(f"\n  gated arm (rvol >= {params_rvol_min}): {len(gated)} "
                   f"of {len(sg_)} rows "
                   f"({100.0 * len(gated) / max(len(sg_), 1):.1f}%)")
        out.append(diag_block(gated, cfg, f"diagnostics (gated arm)"))

        out.append("\nSIGNAL MODE — per symbol (ungated universe)")
        for sym in SYMBOLS:
            sub = sg_[sg_["symbol"] == sym] if len(sg_) else sg_
            out.append(diag_block(sub, cfg, sym))
            if len(sub):
                s = simulate.summarize(sub, sg_ref)
                out.append(f"      assumed={s['decided_by_assumption']} "
                           f"tp_touch_no_fill={s['tp_touched_not_filled']} "
                           f"stop_unresolved={s['stop_fill_unresolved']} "
                           f"flagged={s['flagged_bar_overlap']}")

    print("\n".join(out))


if __name__ == "__main__":
    main()
