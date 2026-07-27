# Backtesting engine (Point 3)

Volume-gated Donchian breakouts on 15m Bitget USDT-M perpetuals, with 1m
intrabar resolution. This directory contains the engine only — no validation
design, no parameter sweep, no performance reporting.

## Layout

| file | role |
|---|---|
| `signals.py` | Layer A — vectorized 15m signal generation. Never touches 1m. |
| `simulate.py` | Layer B — trade lifecycle loop + portfolio constraints + loaders. |
| `costs.py` | Fees, slippage, sizing, target solve, tick rounding. Closed form. |
| `contracts.py` | Tick-size probe and local cache. |
| `run.py` | Entry point: load → signals → simulate → provenance counters. |

The A/B split is what makes the later parameter sweep cheap: Layer A is pure
and vectorized over all bars, Layer B runs only over signal bars.

## Running

```bash
source .venv/bin/activate

# rebuild the tick cache (needs network; only when contracts change)
python src/engine/contracts.py

# a slice, with provenance counters (never performance figures)
python src/engine/run.py --symbols BTCUSDT \
    --start 1672531200000 --end 1675209600000 --summary

# full hand-checkable trace for one trade
python src/engine/run.py --symbols BTCUSDT \
    --start 1672531200000 --end 1675209600000 \
    --trace-signal-ts 1673881200000
```

## Tests

```bash
python -m pytest tests/ -q            # full suite; look-ahead demos deselected
python -m pytest -m lookahead -q --override-ini="addopts="   # planted bugs
python tests/make_golden.py           # re-freeze the golden file, deliberately
```

The `lookahead` marker holds two deliberately planted look-ahead bugs. They are
skipped by default and assert that the causality guard *catches* them. Run them
after touching `signals.py`.

## Non-obvious semantics

These look wrong at a glance and are not.

**`open_synth` is never read.** Bitget's bar `open` is a carried-forward
previous close, not a traded price. The loaders drop the column, so any
accidental use raises `KeyError` rather than silently computing on a fiction.
A static test enforces this over the whole engine source.

**Entry fills on the first 1m close of bar T+1, with zero added slippage.**
The one-minute convention already absorbs latency (~200 ms measured round trip,
so it over-covers by roughly 300×). Adding a second haircut double-counts.
`entry_slippage_bps` exists and defaults to 0 purely so it can be
sensitivity-tested.

**Position size is closed-form, including the stop haircut.** The denominator
is the all-in cost of one unit on a losing trade. Sizing on `(P − S)` alone
risks $20 *plus* costs — about 7% oversized. The haircut belongs in the
denominator because the engine fills stops through the level, so omitting it
would make realised losses exceed 1R.

**The target is solved, not doubled.** `T = (2R/q + P(1+f_taker)) / (1 − f_maker)`.
A naive "2 × stop distance" target makes winners land short of 2R while losers
still pay a full 1R, quietly degrading the true reward:risk. A unit test asserts
the naive target underdelivers.

**Take-profit needs trade-through, not touch.** A resting limit at `T` fills
only when a 1m high reaches `T + 1 tick`. Touching `T` exactly is recorded as
`tp_touched_not_filled` and the trade continues.

**Stops fill through the level.** A stop-market executes in milliseconds, not
60 seconds, so the fill is `stop − haircut` (longs), never the breach minute's
close.

**Exit detection starts the minute *after* entry.** The entry minute's own
high/low happened before the fill; testing them would exit on price action the
position was never exposed to.

**Both levels in one minute → stop first, flagged `assumed`.** 1m OHLC cannot
order two touches inside a minute. Conservative by construction, and counted
separately from `observed` so the assumption's weight is always visible.

**Tick size is a step function of time.** SOLUSDT traded on a 0.0001 grid until
2024-08-14T04:05Z and 0.001 after. Bitget's endpoint reports current state only,
so the historical boundary was derived empirically from the derived layer and
frozen in `config/contracts_cache.json`. Two isolated SOL prints carry 4 decimals
after the change; they are frozen as named exceptions so the grid check stays
strict rather than being absorbed by a loosened tolerance.

**Cooldown is direction-specific.** A stopped long blocks new longs until a new
20-bar high; shorts stay available.

**Time stop measures +1R by intrabar touch on 1m.** Consistent with how stop and
target are detected. Decision on the close of the 16th bar, execution on the
first 1m bar of T+17 — mirroring entry, so every decision rests on closed-bar
information.

**Divergence flags are reported, never filtered.** `flagged_bar_overlap` is a
column, not a filter. A test asserts the attach function contains no row-dropping.

**Funding is absent entirely.** Not an input to any decision — the rate is
unknowable at entry. It is a separate sensitivity run later.
