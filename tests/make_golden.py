"""Regenerate the G5 golden file. Run deliberately, never automatically.

    python tests/make_golden.py

Prints only row count and hash -- no performance figures.
"""

import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src", "engine"))

import run as engine_run  # noqa: E402

GOLDEN_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "golden")
SLICE = dict(symbols=["BTCUSDT"], start_ts=1672531200000,
             end_ts=1675209600000)

if __name__ == "__main__":
    os.makedirs(GOLDEN_DIR, exist_ok=True)
    trades, refused, _ = engine_run.run(variant="gated", **SLICE)
    csv = os.path.join(GOLDEN_DIR, "btc_2023_01_gated.csv")
    trades.to_csv(csv, index=False)
    h = engine_run.output_hash(trades)
    with open(os.path.join(GOLDEN_DIR, "btc_2023_01_gated.sha256"), "w") as fh:
        fh.write(h + "\n")
    print(f"golden frozen: {len(trades)} rows")
    print(f"sha256: {h}")
