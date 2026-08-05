"""Regenerate the G5 golden file. Run deliberately, never automatically.

    python tests/make_golden.py

Prints only row count and hash -- no performance figures.
"""

import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src", "engine"))

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import run as engine_run  # noqa: E402
from conftest import golden_cfg  # noqa: E402

GOLDEN_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "golden")
SLICE = dict(symbols=["BTCUSDT"], start_ts=1672531200000,
             end_ts=1675209600000)

def freeze(name, **kw):
    trades, _, _ = engine_run.run(cfg=golden_cfg(), **SLICE, **kw)
    trades.to_csv(os.path.join(GOLDEN_DIR, f"{name}.csv"), index=False)
    h = engine_run.output_hash(trades)
    with open(os.path.join(GOLDEN_DIR, f"{name}.sha256"), "w") as fh:
        fh.write(h + "\n")
    print(f"{name}: {len(trades)} rows  sha256 {h}")
    return h


if __name__ == "__main__":
    os.makedirs(GOLDEN_DIR, exist_ok=True)
    # Portfolio mode, gated -- the original G5 anchor.
    freeze("btc_2023_01_gated", variant="gated", mode="portfolio")
    # Signal mode, UNGATED -- the Point 3 known gap, closed here. Signal mode
    # is the edge-test instrument, and the gated arm is obtained by FILTERING
    # this table, so this is the anchor that actually needs pinning.
    freeze("btc_2023_01_signal_ungated", variant="ungated", mode="signal")
