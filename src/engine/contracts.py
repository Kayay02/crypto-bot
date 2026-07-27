"""Per-symbol contract specs: tick size, with a local cache.

Bitget's /api/v2/mix/market/contracts reports the CURRENT contract state only.
Tick is priceEndStep * 10**-pricePlace -- NOT 10**-pricePlace, which happens to
coincide today only because priceEndStep == 1 for all three symbols. Do not
collapse the two.

The current value is also not valid for the whole backtest window: SOLUSDT
traded on a 0.0001 grid until 2024-08-14T04:05Z and on 0.001 after. A tick is
therefore a step function of time, not a scalar, and the engine looks it up by
bar timestamp. BTC and ETH have a single segment each over the same window.

The historical segment boundaries cannot be recovered from the API -- they were
derived empirically from the derived layer (see verify_against_data) and are
frozen in the cache. Re-probing refreshes only the current segment.
"""

import json
import os

CACHE_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "config", "contracts_cache.json")

CONTRACTS_URL = "https://api.bitget.com/api/v2/mix/market/contracts"
PRODUCT_TYPE = "USDT-FUTURES"


class TickSchedule:
    """Piecewise-constant tick size over time.

    segments: list of (from_ts_inclusive, tick). Must be sorted ascending and
    start at 0 so every timestamp resolves.
    """

    def __init__(self, symbol, segments):
        if not segments or segments[0][0] != 0:
            raise ValueError(f"{symbol}: schedule must start at ts 0")
        if any(b[0] <= a[0] for a, b in zip(segments, segments[1:])):
            raise ValueError(f"{symbol}: segments must ascend")
        self.symbol = symbol
        self.segments = [(int(t), float(v)) for t, v in segments]

    def tick_at(self, ts):
        """Tick in force at bar-open timestamp `ts` (epoch ms)."""
        out = None
        for start, tick in self.segments:
            if ts >= start:
                out = tick
            else:
                break
        if out is None:
            raise ValueError(f"{self.symbol}: no tick for ts {ts}")
        return out

    def is_constant(self):
        return len(self.segments) == 1

    def to_json(self):
        return {"symbol": self.symbol,
                "segments": [[t, v] for t, v in self.segments]}


def probe_contracts(timeout=30):
    """Live probe. Returns {symbol: {"tick", "pricePlace", "priceEndStep"}}."""
    import requests
    r = requests.get(CONTRACTS_URL, params={"productType": PRODUCT_TYPE},
                     timeout=timeout)
    r.raise_for_status()
    body = r.json()
    if body.get("code") != "00000":
        raise RuntimeError(f"contracts probe failed: {body.get('msg')}")
    out = {}
    for c in body["data"]:
        place = int(c["pricePlace"])
        step = int(c["priceEndStep"])
        out[c["symbol"]] = {
            "tick": step * (10 ** -place),
            "pricePlace": place,
            "priceEndStep": step,
        }
    return out


def load_cache(path=CACHE_PATH):
    """Load the frozen tick schedules. The engine runs offline from here."""
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"contracts cache missing at {path}; run contracts.py to build it")
    raw = json.load(open(path))
    return {s: TickSchedule(s, v["segments"])
            for s, v in raw["symbols"].items()}


# Two SOLUSDT 15m prices carry 4 decimals after the 2024-08-14 move to a 0.001
# grid. Both are isolated venue prints, not evidence of a later tick segment
# (the ~200k bars around them are all on 0.001). They are frozen here by exact
# (ts, field, value) so the grid check stays strict: a NEW off-grid price is
# still a failure rather than being absorbed by a loosened tolerance.
KNOWN_OFFGRID = {
    ("SOLUSDT", 1724517000000, "high", 162.1107),
    ("SOLUSDT", 1725230700000, "low", 127.8382),
}


def verify_against_data(schedules, derived_dir, symbols):
    """Every historical price must lie on the tick grid in force at its bar.

    This is the check that catches a tick taken on faith from a precision
    field. Returns {symbol: [unexpected off-grid entries]}; all empty means the
    schedule holds.
    """
    import numpy as np
    import pyarrow.parquet as pq

    out = {}
    for sym in symbols:
        df = pq.read_table(
            os.path.join(derived_dir, "ohlcv_15m", f"{sym}.parquet")).to_pandas()
        ts = df["ts"].to_numpy()
        ticks = np.array([schedules[sym].tick_at(t) for t in ts])
        unexpected = []
        for col in ("high", "low", "close"):
            v = df[col].to_numpy()
            scaled = np.round(v / ticks)
            bad = np.nonzero(np.abs(scaled * ticks - v)
                             > 1e-9 * np.maximum(1.0, np.abs(v)))[0]
            for i in bad:
                entry = (sym, int(ts[i]), col, float(v[i]))
                if entry not in KNOWN_OFFGRID:
                    unexpected.append(entry)
        out[sym] = unexpected
    return out


if __name__ == "__main__":
    # Rebuild the cache: probe the live endpoint for the current segment, keep
    # the empirically-derived historical boundaries, then verify the whole
    # schedule against every price in the derived layer.
    root = os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))))
    live = probe_contracts()
    print("live probe:")
    for s in ("BTCUSDT", "ETHUSDT", "SOLUSDT"):
        print(f"  {s}: pricePlace={live[s]['pricePlace']} "
              f"priceEndStep={live[s]['priceEndStep']} -> tick {live[s]['tick']}")

    # SOL's grid changes at the first 1m bar that is fully on 0.001.
    SOL_TICK_CHANGE_TS = 1723608300000  # 2024-08-14T04:05:00Z
    schedules = {
        "BTCUSDT": TickSchedule("BTCUSDT", [(0, live["BTCUSDT"]["tick"])]),
        "ETHUSDT": TickSchedule("ETHUSDT", [(0, live["ETHUSDT"]["tick"])]),
        "SOLUSDT": TickSchedule("SOLUSDT",
                                [(0, 0.0001),
                                 (SOL_TICK_CHANGE_TS, live["SOLUSDT"]["tick"])]),
    }

    res = verify_against_data(schedules, os.path.join(root, "data", "derived"),
                              ["BTCUSDT", "ETHUSDT", "SOLUSDT"])
    print("unexpected off-grid prices per symbol (must be empty):",
          {k: len(v) for k, v in res.items()})
    print(f"known off-grid exceptions carried: {len(KNOWN_OFFGRID)}")
    if any(res.values()):
        for sym, rows in res.items():
            for r in rows[:10]:
                print("  UNEXPECTED", r)
        raise SystemExit("tick schedule does not match historical prices")

    os.makedirs(os.path.dirname(CACHE_PATH), exist_ok=True)
    with open(CACHE_PATH, "w") as fh:
        json.dump({
            "source": CONTRACTS_URL,
            "product_type": PRODUCT_TYPE,
            "note": "tick = priceEndStep * 10**-pricePlace; historical "
                    "segments derived empirically from derived layer",
            "symbols": {s: sch.to_json() for s, sch in schedules.items()},
        }, fh, indent=2, sort_keys=True)
        fh.write("\n")
    print(f"cache written: {CACHE_PATH}")
