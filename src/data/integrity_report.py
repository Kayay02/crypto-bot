"""READ-ONLY data integrity diagnostic for the raw 15m capture.

Loads the raw JSONL files, dedupes Bitget's deliberate page-seam overlaps IN
MEMORY, and prints a sectioned integrity report to stdout + reports/
integrity_report.txt. Optionally writes PNG plots to reports/.

HARD CONSTRAINT: this script NEVER writes, cleans, patches, fills, drops, or
otherwise modifies any data under data/. It creates no derived layer, no
Parquet. Its only outputs are the text report and optional plots. Its purpose
is to inform later cleaning decisions — not to make them.

Run:  python -u src/data/integrity_report.py
"""

import json
import os
import sys

import numpy as np
import pandas as pd

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, _REPO_ROOT)

RAW_BITGET = os.path.join(_REPO_ROOT, "data", "raw", "bitget")
RAW_BINANCE = os.path.join(_REPO_ROOT, "data", "raw", "binance")
REPORTS_DIR = os.path.join(_REPO_ROOT, "reports")
BAR_MS = 900_000
SYMBOLS = ["BTCUSDT", "ETHUSDT", "SOLUSDT"]

# ------------------------------------------------------------------ reporter
_BUF = []


def out(line=""):
    print(line, flush=True)
    _BUF.append(str(line))


def section(title):
    out("\n" + "=" * 80)
    out(title)
    out("=" * 80)


# ------------------------------------------------------------------ loaders
def load_bitget(symbol):
    """Return deduped, timestamp-sorted DataFrame for a Bitget symbol.

    Dedupe keeps the first occurrence of each timestamp (page-seam overlaps
    are byte-identical, verified at capture time, so choice is immaterial).
    """
    path = os.path.join(RAW_BITGET, f"{symbol}_15m.jsonl")
    rows = []
    with open(path) as fh:
        for line in fh:
            if not line.strip():
                continue
            rec = json.loads(line)
            rows.extend(rec.get("response") or [])
    df = pd.DataFrame(rows, columns=["ts", "open", "high", "low", "close",
                                     "base_vol", "quote_vol"])
    dup_before = len(df)
    df["ts"] = df["ts"].astype("int64")
    for c in ["open", "high", "low", "close", "base_vol", "quote_vol"]:
        df[c] = df[c].astype(float)
    df = df.drop_duplicates(subset="ts", keep="first").sort_values("ts")
    df = df.reset_index(drop=True)
    df["dt"] = pd.to_datetime(df["ts"], unit="ms", utc=True)
    return df, dup_before


def load_binance_btc():
    path = os.path.join(RAW_BINANCE, "BTCUSDT_15m.jsonl")
    cols = ["open_time", "open", "high", "low", "close", "volume",
            "close_time", "quote_vol", "trades", "taker_buy_base",
            "taker_buy_quote", "ignore"]
    rows = []
    with open(path) as fh:
        for line in fh:
            if not line.strip():
                continue
            rec = json.loads(line)
            rows.extend(rec.get("response") or [])
    df = pd.DataFrame(rows, columns=cols)
    df["ts"] = df["open_time"].astype("int64")
    for c in ["open", "high", "low", "close", "volume", "quote_vol",
              "taker_buy_base", "taker_buy_quote"]:
        df[c] = df[c].astype(float)
    df["trades"] = df["trades"].astype("int64")
    df = df.drop_duplicates(subset="ts", keep="first").sort_values("ts")
    df = df.reset_index(drop=True)
    df["dt"] = pd.to_datetime(df["ts"], unit="ms", utc=True)
    return df


def pct_line(label, series, qs):
    vals = series.dropna()
    parts = []
    for q in qs:
        parts.append(f"p{q:g}={vals.quantile(q / 100):.6g}")
    out(f"  {label}: " + "  ".join(parts))


# ------------------------------------------------------------------ sections
def structural(symbol, df, dup_before):
    section(f"[{symbol}] A. STRUCTURAL")
    out(f"  raw rows (with overlaps): {dup_before}")
    out(f"  rows after dedupe        : {len(df)}")
    # 1. duplicate timestamps after dedupe
    dups = int(df["ts"].duplicated().sum())
    out(f"  A1 duplicate timestamps after dedupe: {dups} (expect 0)")
    # 2. strictly increasing
    inc = bool((df["ts"].diff().dropna() > 0).all())
    out(f"  A2 timestamps strictly increasing   : {inc} (expect True)")
    # 3. OHLC validity
    o, h, l, c = df["open"], df["high"], df["low"], df["close"]
    bad = df[(h < o) | (h < c) | (l > o) | (l > c) | (h < l)]
    out(f"  A3 OHLC validity violations         : {len(bad)}")
    if len(bad):
        out("     up to 10 examples (ts, o/h/l/c):")
        for _, r in bad.head(10).iterrows():
            out(f"       {r['dt']}  {r['open']}/{r['high']}/{r['low']}/{r['close']}")


def volume_integrity(symbol, df):
    section(f"[{symbol}] B. VOLUME INTEGRITY")
    v = df["base_vol"]
    # 4. exactly-zero base volume
    zero = df[v == 0]
    out(f"  B4 exactly-zero base_volume bars: {len(zero)}")
    for _, r in zero.head(20).iterrows():
        out(f"       {r['dt']}  o/h/l/c={r['open']}/{r['high']}/{r['low']}/{r['close']}")
    # 5. volume percentiles
    pct_line("B5 base_vol percentiles", v,
             [0.01, 0.1, 1, 5, 25, 50, 75, 95, 99])
    # 6. frozen bars
    frozen = df[(df["open"] == df["high"]) & (df["high"] == df["low"]) &
                (df["low"] == df["close"])]
    out(f"  B6 frozen bars (o==h==l==c): {len(frozen)}")
    for _, r in frozen.head(20).iterrows():
        out(f"       {r['dt']}  price={r['close']}  base_vol={r['base_vol']}")
    if len(frozen):
        out(f"     frozen-bar base_vol: min={frozen['base_vol'].min()} "
            f"median={frozen['base_vol'].median()} max={frozen['base_vol'].max()}")
    # 7. monthly profile
    out("  B7 MONTHLY PROFILE (median base_vol, zero-vol count):")
    m = df.copy()
    m["month"] = m["dt"].dt.strftime("%Y-%m")
    grp = m.groupby("month").agg(
        bars=("base_vol", "size"),
        median_vol=("base_vol", "median"),
        zero_vol=("base_vol", lambda s: int((s == 0).sum())),
    )
    out(f"     {'month':<9} {'bars':>6} {'median_vol':>14} {'zero_vol':>9}")
    for month, r in grp.iterrows():
        out(f"     {month:<9} {int(r['bars']):>6} {r['median_vol']:>14.4f} "
            f"{int(r['zero_vol']):>9}")


def rvol_stress(symbol, df):
    section(f"[{symbol}] C. RVOL DENOMINATOR STRESS TEST")
    d = df.copy().reset_index(drop=True)
    v = d["base_vol"]
    # rolling mean of 20, EXCLUDING current bar (shift by 1 first).
    denom = v.shift(1).rolling(20).mean()
    d["rvol_denom"] = denom
    d["rvol"] = v / denom
    valid = d["rvol"].replace([np.inf, -np.inf], np.nan)
    d["rvol"] = valid
    med_vol = v.median()

    # 8. rvol percentiles
    pct_line("C8 rvol percentiles", d["rvol"], [50, 75, 90, 95, 99, 99.9])
    out(f"     rvol max = {d['rvol'].max():.6g}")
    # 9. count rvol > 10
    ext = d[d["rvol"] > 10].copy()
    out(f"  C9 bars with rvol > 10: {len(ext)}")

    # 10. context windows for up to 15 extreme bars
    out("  C10 context windows (20 before, extreme bar, 3 after):")
    show = ext.sort_values("rvol", ascending=False).head(15)
    for idx in show.index:
        r = d.loc[idx]
        out(f"    --- extreme @ {r['dt']}  rvol={r['rvol']:.2f}  "
            f"vol={r['base_vol']:.4f}  denom(mean20 excl)={r['rvol_denom']:.4f}")
        lo = max(0, idx - 20)
        hi = min(len(d) - 1, idx + 3)
        for j in range(lo, hi + 1):
            rr = d.loc[j]
            mark = "  <<<" if j == idx else ""
            rv = f"{rr['rvol']:.2f}" if pd.notna(rr["rvol"]) else "nan"
            out(f"        {rr['dt']}  close={rr['close']:.4g}  "
                f"vol={rr['base_vol']:.4f}  rvol={rv}{mark}")

    # 11. thin denominator vs genuine surge — evidence
    out("  C11 DENOMINATOR vs NUMERATOR at extreme-RVOL bars:")
    if len(ext):
        denom_ratio = ext["rvol_denom"] / med_vol  # <1 => thin preceding period
        numer_ratio = ext["base_vol"] / med_vol     # >1 => elevated current vol
        thin = int((denom_ratio < 0.5).sum())
        surge = int((numer_ratio > 2).sum())
        both = int(((denom_ratio < 0.5) & (numer_ratio > 2)).sum())
        out(f"     symbol median base_vol = {med_vol:.4f}")
        out(f"     preceding-mean/median (denominator) percentiles across "
            f"extreme bars:")
        pct_line("       denom/median", denom_ratio, [1, 10, 50, 90, 99])
        out(f"     current-vol/median (numerator) percentiles across "
            f"extreme bars:")
        pct_line("       numer/median", numer_ratio, [1, 10, 50, 90, 99])
        out(f"     extreme bars with depressed denominator (<0.5x median): "
            f"{thin}/{len(ext)}")
        out(f"     extreme bars with elevated numerator   (>2x median): "
            f"{surge}/{len(ext)}")
        out(f"     extreme bars with BOTH thin denom AND surge numerator: "
            f"{both}/{len(ext)}")
        # Plain statement based on which dominates.
        frac_thin = thin / len(ext)
        frac_surge = surge / len(ext)
        out("     FINDING:")
        if frac_thin > frac_surge:
            out(f"       Extreme RVOL is driven MORE by a depressed denominator "
                f"(thin preceding period): {frac_thin:.0%} of extreme bars have "
                f"<0.5x-median preceding mean vs {frac_surge:.0%} with "
                f">2x-median current volume.")
        elif frac_surge > frac_thin:
            out(f"       Extreme RVOL is driven MORE by an elevated numerator "
                f"(genuine volume surge): {frac_surge:.0%} of extreme bars have "
                f">2x-median current volume vs {frac_thin:.0%} with a "
                f"<0.5x-median preceding mean.")
        else:
            out(f"       Mixed: {frac_thin:.0%} thin-denominator vs "
                f"{frac_surge:.0%} elevated-numerator; neither dominates.")
    else:
        out("     no rvol>10 bars to analyze.")


def cross_venue(bg, bn):
    section("[BTCUSDT] D. CROSS-VENUE (Bitget vs Binance)")
    a = bg[["ts", "dt", "open", "high", "low", "close", "base_vol"]].rename(
        columns={"open": "bg_o", "high": "bg_h", "low": "bg_l",
                 "close": "bg_c", "base_vol": "bg_vol"})
    b = bn[["ts", "open", "high", "low", "close", "volume", "trades"]].rename(
        columns={"open": "bn_o", "high": "bn_h", "low": "bn_l",
                 "close": "bn_c", "volume": "bn_vol"})
    j = a.merge(b, on="ts", how="inner")

    # 12. join coverage
    only_bg = set(bg["ts"]) - set(bn["ts"])
    only_bn = set(bn["ts"]) - set(bg["ts"])
    out(f"  D12 matched bars (inner join): {len(j)}")
    out(f"      Bitget unique ts: {len(bg)}   Binance unique ts: {len(bn)}")
    out(f"      timestamps only in Bitget : {len(only_bg)}")
    for t in sorted(only_bg)[:10]:
        out(f"        {pd.to_datetime(t, unit='ms', utc=True)}")
    out(f"      timestamps only in Binance: {len(only_bn)}")
    for t in sorted(only_bn)[:10]:
        out(f"        {pd.to_datetime(t, unit='ms', utc=True)}")

    # 13. close divergence in bps
    j = j.copy()
    j["div_bps"] = (j["bg_c"] - j["bn_c"]).abs() / j["bn_c"] * 1e4
    pct_line("D13 close divergence (bps)", j["div_bps"], [50, 90, 99, 99.9])
    out(f"      max close divergence = {j['div_bps'].max():.4g} bps")
    out("      20 largest close divergences (ts, div_bps | Bitget o/h/l/c/vol | "
        "Binance o/h/l/c/vol):")
    for _, r in j.sort_values("div_bps", ascending=False).head(20).iterrows():
        out(f"        {r['dt']}  {r['div_bps']:.2f}bps | "
            f"BG {r['bg_o']:.2f}/{r['bg_h']:.2f}/{r['bg_l']:.2f}/{r['bg_c']:.2f}/"
            f"{r['bg_vol']:.2f} | "
            f"BN {r['bn_o']:.2f}/{r['bn_h']:.2f}/{r['bn_l']:.2f}/{r['bn_c']:.2f}/"
            f"{r['bn_vol']:.2f}")

    # 14. Bitget bottom-1% volume vs Binance trades
    thr = j["bg_vol"].quantile(0.01)
    thin = j[j["bg_vol"] <= thr].copy()
    out(f"  D14 Bitget bottom-1% volume bars (bg_vol <= {thr:.4f}): {len(thin)}")
    bn_trades_median_all = j["trades"].median()
    out(f"      Binance trades median over ALL matched bars: "
        f"{bn_trades_median_all:.0f}")
    out(f"      Binance trades median over these THIN bars : "
        f"{thin['trades'].median():.0f}")
    quiet = int((thin["trades"] < 0.25 * bn_trades_median_all).sum())
    normal = int((thin["trades"] >= 0.25 * bn_trades_median_all).sum())
    out(f"      of {len(thin)} thin-Bitget bars: {quiet} coincide with quiet "
        f"Binance activity (<0.25x median trades), {normal} with normal "
        f"Binance activity (>=0.25x median trades).")
    out("      sample (up to 20) — ts | bg_vol | bn_trades | bn_vol:")
    for _, r in thin.sort_values("bg_vol").head(20).iterrows():
        out(f"        {r['dt']}  bg_vol={r['bg_vol']:.4f}  "
            f"bn_trades={int(r['trades'])}  bn_vol={r['bn_vol']:.4f}")

    # 15. bar-to-bar jumps at both venues
    out("  D15 bar-to-bar jump abs(open - prev_close)/prev_close (bps):")
    for venue, oc, cc in [("Bitget", "bg_o", "bg_c"), ("Binance", "bn_o", "bn_c")]:
        s = j.sort_values("ts")
        jump = (s[oc] - s[cc].shift(1)).abs() / s[cc].shift(1) * 1e4
        pct_line(f"     {venue} jump (bps)", jump, [50, 90, 99, 99.9])
        out(f"       {venue} max jump = {jump.max():.4g} bps")
        tmp = s.assign(jump=jump).dropna(subset=["jump"])
        out(f"       {venue} 20 largest jumps (ts, jump_bps):")
        for _, r in tmp.sort_values("jump", ascending=False).head(20).iterrows():
            out(f"         {r['dt']}  {r['jump']:.2f} bps")


def maybe_plots(bitget_frames, j_available):
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except Exception as e:  # noqa: BLE001
        out(f"\n(plots skipped: matplotlib unavailable: {e})")
        return
    for symbol, df in bitget_frames.items():
        fig, ax = plt.subplots(2, 1, figsize=(11, 7))
        m = df.copy()
        m["month"] = m["dt"].dt.to_period("M").dt.to_timestamp()
        prof = m.groupby("month")["base_vol"].median()
        ax[0].plot(prof.index, prof.values)
        ax[0].set_title(f"{symbol} monthly median base_vol")
        ax[0].set_yscale("log")
        ax[1].hist(np.log10(df["base_vol"].replace(0, np.nan).dropna()), bins=80)
        ax[1].set_title(f"{symbol} log10(base_vol) distribution")
        fig.tight_layout()
        p = os.path.join(REPORTS_DIR, f"{symbol}_volume_profile.png")
        fig.savefig(p, dpi=90)
        plt.close(fig)
        out(f"(plot saved: {p})")


def main():
    os.makedirs(REPORTS_DIR, exist_ok=True)
    out("RAW DATA INTEGRITY REPORT (READ-ONLY — no data modified)")
    out(f"generated: {pd.Timestamp.utcnow()}")

    bitget_frames = {}
    for symbol in SYMBOLS:
        df, dup_before = load_bitget(symbol)
        bitget_frames[symbol] = df
        structural(symbol, df, dup_before)
        volume_integrity(symbol, df)
        rvol_stress(symbol, df)

    bn = load_binance_btc()
    cross_venue(bitget_frames["BTCUSDT"], bn)

    maybe_plots(bitget_frames, True)

    report_path = os.path.join(REPORTS_DIR, "integrity_report.txt")
    with open(report_path, "w") as fh:
        fh.write("\n".join(_BUF) + "\n")
    out(f"\nReport saved to {report_path}")


if __name__ == "__main__":
    main()
