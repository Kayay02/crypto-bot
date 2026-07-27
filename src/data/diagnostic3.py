"""READ-ONLY diagnostic #3 on the raw 15m capture.

Investigates (1) whether Bitget's bar OPEN is a real first-trade price or a
carried-forward previous close, (2) the apparent volume-timeline contradiction,
(3) era-stability of an rvol gate, and (4) a bidirectional frozen/zero-volume
artifact scan. Same sources as integrity_report.py; Bitget seam overlaps are
deduped in memory.

HARD CONSTRAINT: never writes, cleans, patches, or modifies any data under
data/. No derived layer, no Parquet. Only outputs the text report to stdout and
reports/diagnostic3.txt.

Run:  python -u src/data/diagnostic3.py
"""

import json
import os
import sys

import numpy as np
import pandas as pd

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
RAW_BITGET = os.path.join(_REPO_ROOT, "data", "raw", "bitget")
RAW_BINANCE = os.path.join(_REPO_ROOT, "data", "raw", "binance")
REPORTS_DIR = os.path.join(_REPO_ROOT, "reports")
SYMBOLS = ["BTCUSDT", "ETHUSDT", "SOLUSDT"]

_BUF = []


def out(line=""):
    print(line, flush=True)
    _BUF.append(str(line))


def section(t):
    out("\n" + "=" * 80)
    out(t)
    out("=" * 80)


# ------------------------------------------------------------------ loaders
def load_bitget(symbol):
    """Deduped, sorted Bitget frame. Keeps RAW STRING open/close for bitwise
    equality tests, plus float columns for arithmetic."""
    path = os.path.join(RAW_BITGET, f"{symbol}_15m.jsonl")
    rows = []
    with open(path) as fh:
        for line in fh:
            if line.strip():
                rows.extend(json.loads(line).get("response") or [])
    df = pd.DataFrame(rows, columns=["ts", "open", "high", "low", "close",
                                     "base_vol", "quote_vol"])
    df["ts"] = df["ts"].astype("int64")
    df = df.drop_duplicates(subset="ts", keep="first").sort_values("ts")
    df = df.reset_index(drop=True)
    df["open_s"] = df["open"].astype(str)
    df["close_s"] = df["close"].astype(str)
    for c in ["open", "high", "low", "close", "base_vol", "quote_vol"]:
        df[c] = df[c].astype(float)
    df["dt"] = pd.to_datetime(df["ts"], unit="ms", utc=True)
    df["year"] = df["dt"].dt.year
    df["month"] = df["dt"].dt.strftime("%Y-%m")
    df["hour"] = df["dt"].dt.hour
    return df


def load_binance_btc():
    path = os.path.join(RAW_BINANCE, "BTCUSDT_15m.jsonl")
    cols = ["open_time", "open", "high", "low", "close", "volume",
            "close_time", "quote_vol", "trades", "taker_buy_base",
            "taker_buy_quote", "ignore"]
    rows = []
    with open(path) as fh:
        for line in fh:
            if line.strip():
                rows.extend(json.loads(line).get("response") or [])
    df = pd.DataFrame(rows, columns=cols)
    df["ts"] = df["open_time"].astype("int64")
    df = df.drop_duplicates(subset="ts", keep="first").sort_values("ts")
    df = df.reset_index(drop=True)
    df["open_s"] = df["open"].astype(str)
    df["close_s"] = df["close"].astype(str)
    for c in ["open", "high", "low", "close", "volume", "quote_vol"]:
        df[c] = df[c].astype(float)
    df["trades"] = df["trades"].astype("int64")
    df["dt"] = pd.to_datetime(df["ts"], unit="ms", utc=True)
    df["year"] = df["dt"].dt.year
    df["month"] = df["dt"].dt.strftime("%Y-%m")
    df["hour"] = df["dt"].dt.hour
    return df


def pct_open_eq_prevclose(df):
    """% of bars whose raw open string == previous bar's raw close string."""
    prev_close_s = df["close_s"].shift(1)
    mask = df["open_s"] == prev_close_s
    mask = mask[prev_close_s.notna()]
    return 100.0 * mask.mean(), int(mask.sum()), int(mask.size)


# ------------------------------------------------------------------ TEST 1
def test1(bitget_frames, bn):
    section("TEST 1 — IS BITGET'S BAR OPEN A REAL PRICE?")
    for symbol in SYMBOLS:
        df = bitget_frames[symbol].copy()
        df["prev_close_s"] = df["close_s"].shift(1)
        df["move"] = (df["close"] - df["open"]).abs() / df["open"]

        p_all, n_all, tot = pct_open_eq_prevclose(df)
        # top 1% by absolute move and by volume (exclude first row w/o prev).
        sub = df.iloc[1:]
        vol_thr = sub["base_vol"].quantile(0.99)
        mov_thr = sub["move"].quantile(0.99)
        hi_move = sub[sub["move"] >= mov_thr]
        hi_vol = sub[sub["base_vol"] >= vol_thr]
        p_move = 100.0 * (hi_move["open_s"] == hi_move["prev_close_s"]).mean()
        p_vol = 100.0 * (hi_vol["open_s"] == hi_vol["prev_close_s"]).mean()

        out(f"\n[{symbol}] (Bitget)")
        out(f"  1a open==prev_close (bitwise): {p_all:.3f}%  "
            f"({n_all}/{tot})")
        out(f"  1b top1% by |move| (>= {mov_thr*100:.3f}%): {p_move:.3f}%  "
            f"(n={len(hi_move)})")
        out(f"  1b top1% by volume  (>= {vol_thr:.2f}): {p_vol:.3f}%  "
            f"(n={len(hi_vol)})")

    # 1c Binance control.
    bnf = bn.copy()
    bnf["prev_close_s"] = bnf["close_s"].shift(1)
    bnf["move"] = (bnf["close"] - bnf["open"]).abs() / bnf["open"]
    p_all, n_all, tot = pct_open_eq_prevclose(bnf)
    sub = bnf.iloc[1:]
    vt = sub["volume"].quantile(0.99)
    mt = sub["move"].quantile(0.99)
    hm = sub[sub["move"] >= mt]
    hv = sub[sub["volume"] >= vt]
    out("\n[BTCUSDT] (Binance CONTROL)")
    out(f"  1c open==prev_close (bitwise): {p_all:.3f}%  ({n_all}/{tot})")
    out(f"  1c top1% by |move|: "
        f"{100.0*(hm['open_s']==hm['prev_close_s']).mean():.3f}%  (n={len(hm)})")
    out(f"  1c top1% by volume: "
        f"{100.0*(hv['open_s']==hv['prev_close_s']).mean():.3f}%  (n={len(hv)})")

    # 1d side-by-side highest-volatility BTC bars.
    out("\n  1d 20 highest-volatility BTC bars (by Bitget |move|), "
        "Bitget vs Binance:")
    bg = bitget_frames["BTCUSDT"].copy()
    bg["prev_close"] = bg["close"].shift(1)
    bg["move"] = (bg["close"] - bg["open"]).abs() / bg["open"]
    j = bg.merge(bn[["ts", "open", "high", "low", "close", "volume"]]
                 .rename(columns={"open": "bn_o", "high": "bn_h", "low": "bn_l",
                                  "close": "bn_c", "volume": "bn_v"}),
                 on="ts", how="left")
    j["bn_prev_c"] = j["bn_c"].shift(1)
    top = j.sort_values("move", ascending=False).head(20)
    for _, r in top.iterrows():
        out(f"    {r['dt']}  move={r['move']*100:.2f}%")
        out(f"       BG prevC={r['prev_close']:.2f} o={r['open']:.2f} "
            f"h={r['high']:.2f} l={r['low']:.2f} c={r['close']:.2f} "
            f"v={r['base_vol']:.2f}  open==prevC:{r['open_s']==bg['close_s'].shift(1).loc[r.name]}")
        out(f"       BN prevC={r['bn_prev_c']:.2f} o={r['bn_o']:.2f} "
            f"h={r['bn_h']:.2f} l={r['bn_l']:.2f} c={r['bn_c']:.2f} "
            f"v={r['bn_v']:.2f}")

    out("\n  1e FINDING: see percentages above. If open==prev_close stays near "
        "100% even in the top-1% most volatile / highest-volume bars, the open "
        "is carried forward, not a real first trade. Binance is the control.")


# ------------------------------------------------------------------ TEST 2
def test2(bitget_frames, bn):
    section("TEST 2 — VOLUME TIMELINE")
    for symbol in SYMBOLS:
        df = bitget_frames[symbol]
        g = df.groupby("month")["base_vol"].agg(
            median="median",
            p10=lambda s: s.quantile(0.10),
            p90=lambda s: s.quantile(0.90),
            bars="size",
        )
        out(f"\n[{symbol}] 2a monthly base_vol (median / p10 / p90):")
        out(f"   {'month':<9}{'bars':>7}{'median':>14}{'p10':>13}{'p90':>15}")
        for m, r in g.iterrows():
            out(f"   {m:<9}{int(r['bars']):>7}{r['median']:>14.2f}"
                f"{r['p10']:>13.2f}{r['p90']:>15.2f}")
        peak = g["median"].idxmax()
        after = g.loc[g.index > peak, "median"]
        decl = (after.iloc[-1] < g.loc[peak, "median"]) if len(after) else False
        out(f"   peak median month = {peak} ({g.loc[peak,'median']:.2f}); "
            f"declined by series end: {decl}")

        # 2b bottom-1% whole-series bars per month.
        thr = df["base_vol"].quantile(0.01)
        b = df[df["base_vol"] <= thr]
        cnt = b.groupby("month").size()
        out(f"   2b bottom-1% (<= {thr:.2f}) bars per month "
            f"(months with any):")
        for m, c in cnt.items():
            out(f"      {m}: {int(c)}")

    # 2c BTC Bitget vs Binance vol & trades.
    bg = bitget_frames["BTCUSDT"]
    gb = bg.groupby("month")["base_vol"].median()
    gn = bn.groupby("month").agg(bn_vol=("volume", "median"),
                                 bn_trades=("trades", "median"))
    out("\n[BTCUSDT] 2c monthly medians: Bitget base_vol | Binance volume | "
        "Binance trades")
    out(f"   {'month':<9}{'BG_vol':>14}{'BN_vol':>14}{'BN_trades':>12}")
    for m in gn.index:
        bgv = gb.get(m, float('nan'))
        out(f"   {m:<9}{bgv:>14.2f}{gn.loc[m,'bn_vol']:>14.2f}"
            f"{gn.loc[m,'bn_trades']:>12.0f}")

    # 2d hour-of-day median volume by year (BTC).
    out("\n[BTCUSDT] 2d hour-of-day (UTC) median base_vol by year:")
    piv = bg.pivot_table(index="hour", columns="year", values="base_vol",
                         aggfunc="median")
    hdr = "   hour " + "".join(f"{int(y):>12}" for y in piv.columns)
    out(hdr)
    for h, row in piv.iterrows():
        out(f"   {h:>4} " + "".join(f"{row[y]:>12.1f}" for y in piv.columns))

    out("\n  2e RECONCILIATION: compare the peak-then-decline in 2a/2c against "
        "the monthly bottom-1% clustering in 2b, and the hour profile in 2d.")


# ------------------------------------------------------------------ TEST 3
def test3(bitget_frames):
    section("TEST 3 — IS THE RVOL GATE ERA-STABLE?")
    for symbol in SYMBOLS:
        df = bitget_frames[symbol].copy()
        v = df["base_vol"]
        df["rvol"] = v / v.shift(1).rolling(20).mean()
        df["rvol"] = df["rvol"].replace([np.inf, -np.inf], np.nan)
        out(f"\n[{symbol}] 3a rvol percentiles by year:")
        out(f"   {'year':<6}{'p50':>9}{'p75':>9}{'p90':>9}{'p95':>9}{'p99':>9}"
            f"{'%>=1.5':>10}")
        pass_rates = {}
        for y, grp in df.groupby("year"):
            r = grp["rvol"].dropna()
            if len(r) == 0:
                continue
            rate = 100.0 * (r >= 1.5).mean()
            pass_rates[y] = rate
            out(f"   {int(y):<6}{r.quantile(.50):>9.3f}{r.quantile(.75):>9.3f}"
                f"{r.quantile(.90):>9.3f}{r.quantile(.95):>9.3f}"
                f"{r.quantile(.99):>9.3f}{rate:>9.2f}%")
        if pass_rates:
            lo, hi = min(pass_rates.values()), max(pass_rates.values())
            out(f"   3b/3c %>=1.5 spread across years: {lo:.2f}% .. {hi:.2f}%  "
                f"(range {hi-lo:.2f} pts)")


# ------------------------------------------------------------------ TEST 4
def test4(bitget_frames, bn):
    section("TEST 4 — BIDIRECTIONAL ARTIFACT SCAN (BTC)")
    # 4a Binance frozen / zero volume.
    bn_zero = bn[bn["volume"] == 0]
    bn_frozen = bn[(bn["open"] == bn["high"]) & (bn["high"] == bn["low"]) &
                   (bn["low"] == bn["close"])]
    out(f"  4a Binance volume==0 bars: {len(bn_zero)}")
    for _, r in bn_zero.head(20).iterrows():
        out(f"       {r['dt']}  price~{r['close']:.2f} trades={r['trades']}")
    out(f"  4a Binance frozen (o==h==l==c) bars: {len(bn_frozen)}")
    for _, r in bn_frozen.head(20).iterrows():
        out(f"       {r['dt']}  price={r['close']:.2f} vol={r['volume']:.2f} "
            f"trades={r['trades']}")

    # 4b Bitget confirm.
    bg = bitget_frames["BTCUSDT"]
    bg_zero = bg[bg["base_vol"] == 0]
    bg_frozen = bg[(bg["open"] == bg["high"]) & (bg["high"] == bg["low"]) &
                   (bg["low"] == bg["close"])]
    out(f"  4b Bitget volume==0 bars: {len(bg_zero)}; "
        f"frozen bars: {len(bg_frozen)}")

    # 4c label the 20 largest close divergences.
    j = bg[["ts", "dt", "open", "high", "low", "close", "base_vol"]].merge(
        bn[["ts", "open", "high", "low", "close", "volume", "trades"]]
        .rename(columns={"open": "bn_o", "high": "bn_h", "low": "bn_l",
                         "close": "bn_c", "volume": "bn_v"}),
        on="ts", how="inner")
    j["div_bps"] = (j["close"] - j["bn_c"]).abs() / j["bn_c"] * 1e4
    bn_vol_med = bn["volume"].median()
    bg_vol_med = bg["base_vol"].median()
    out("\n  4c 20 largest close divergences, labelled:")
    for _, r in j.sort_values("div_bps", ascending=False).head(20).iterrows():
        bg_froz = (r["open"] == r["high"] == r["low"] == r["close"])
        bn_froz = (r["bn_o"] == r["bn_h"] == r["bn_l"] == r["bn_c"])
        one_frozen = bg_froz or bn_froz or r["base_vol"] == 0 or r["bn_v"] == 0
        both_active = (r["base_vol"] > 0.1 * bg_vol_med
                       and r["bn_v"] > 0.1 * bn_vol_med
                       and not bg_froz and not bn_froz)
        if one_frozen:
            label = "likely artifact (one venue frozen/zero-volume)"
        elif both_active:
            label = "likely real (both venues active, high volume)"
        else:
            label = "indeterminate (low volume, neither frozen)"
        out(f"    {r['dt']}  {r['div_bps']:.2f}bps -> {label}")
        out(f"       BG o/h/l/c={r['open']:.2f}/{r['high']:.2f}/{r['low']:.2f}/"
            f"{r['close']:.2f} v={r['base_vol']:.2f}")
        out(f"       BN o/h/l/c={r['bn_o']:.2f}/{r['bn_h']:.2f}/{r['bn_l']:.2f}/"
            f"{r['bn_c']:.2f} v={r['bn_v']:.2f} trades={int(r['trades'])}")


def main():
    os.makedirs(REPORTS_DIR, exist_ok=True)
    out("DIAGNOSTIC #3 (READ-ONLY — no data modified)")
    out(f"generated: {pd.Timestamp.utcnow()}")
    bitget_frames = {s: load_bitget(s) for s in SYMBOLS}
    bn = load_binance_btc()
    test1(bitget_frames, bn)
    test2(bitget_frames, bn)
    test3(bitget_frames)
    test4(bitget_frames, bn)
    path = os.path.join(REPORTS_DIR, "diagnostic3.txt")
    with open(path, "w") as fh:
        fh.write("\n".join(_BUF) + "\n")
    out(f"\nReport saved to {path}")


if __name__ == "__main__":
    main()
