import os
import sys

import numpy as np
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src", "engine"))

DERIVED = os.path.join(ROOT, "data", "derived")

import costs  # noqa: E402

# Explicitly-arbitrary values for the four parameters that have NO DEFAULT
# after Point 3R. They are fixture scaffolding, not chosen values: the whole
# point of removing the defaults is that a number must be stated where it is
# used. stop_atr_mult=1.5 here reproduces the pre-3R fixture arithmetic so the
# hand-computed fixtures stay hand-checkable; it carries no other status.
FIXTURE_PARAMS = dict(stop_atr_mult=1.5, stop_max_pct=0.035,
                      rvol_threshold=1.5, baseline_days=20)


def make_cfg(**kw):
    """A CostConfig with the four required parameters filled in."""
    p = dict(FIXTURE_PARAMS)
    p.update(kw)
    return costs.CostConfig(**p)


@pytest.fixture
def cfg():
    return make_cfg()


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


# ---------------------------------------------------------------------------
# The frozen slice used by the golden-file and pinned-trade regressions.
#
# baseline_days=5 (not the fixture default 20) so that a one-month slice still
# contains signals after the session baseline warms up. Every value here is
# EXPLICITLY ARBITRARY fixture scaffolding: the golden file is a determinism
# anchor, not a claim that these are the right parameters. Choosing them is a
# Point 4 sweep decision.
# ---------------------------------------------------------------------------

GOLDEN_CFG_KW = dict(stop_atr_mult=1.5, stop_max_pct=0.035,
                     rvol_threshold=1.5, baseline_days=5)


def golden_cfg():
    return costs.CostConfig(**GOLDEN_CFG_KW)
