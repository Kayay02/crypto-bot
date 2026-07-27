import os
import sys

import numpy as np
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src", "engine"))

DERIVED = os.path.join(ROOT, "data", "derived")

import costs  # noqa: E402


@pytest.fixture
def cfg():
    return costs.CostConfig()


@pytest.fixture
def tick_eth():
    return 0.01


def make_1m(ts0, bars):
    """Build a 1m structured array from (high, low, close) triples.

    Deliberately has no `open` and no `volume` field: if any engine code ever
    reaches for them the test fails with a field error, which is the point.
    """
    n = len(bars)
    arr = np.zeros(n, dtype=[("ts", "i8"), ("high", "f8"), ("low", "f8"),
                             ("close", "f8")])
    for i, (h, l, c) in enumerate(bars):
        arr[i] = (ts0 + i * 60_000, h, l, c)
    return arr


def make_signal(symbol="ETHUSDT", direction="long", sig_ts=1_600_000_000_000,
                atr=2.0, **kw):
    """A minimal signal row. atr drives stop distance; the rest is provenance."""
    s = {
        "symbol": symbol,
        "direction": direction,
        "signal_bar_ts": sig_ts,
        "atr": atr,
        "close": 100.0,
        "ema_fast": 101.0,
        "ema_slow": 99.0,
        "donchian_upper": 99.5,
        "donchian_lower": 95.0,
        "rvol": 2.0,
        "rsi": 60.0,
        "variant": "gated",
    }
    s.update(kw)
    return s
