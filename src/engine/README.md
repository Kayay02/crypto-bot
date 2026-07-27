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

**Cooldown is direction-specific, and the extreme rule is provably inert.**
A stopped long blocks new longs until a new 20-bar high; shorts stay available.
The 20-bar-extreme condition is non-binding for *this* strategy by construction:
a long entry requires a close above the Donchian-20 upper band, which *is* a new
20-bar high, so the condition that clears the cooldown is entailed by the entry
condition it gates. It is retained deliberately — it is a locked decision and an
inert rule costs nothing. `cooldown_bars` (default **0**, preserving prior
behaviour exactly) adds an independent bar-count block that *can* bind: set it
positive to block re-entry for N bars after a stop-out.

**Two separate holding rules — the time stop is NOT unconditional.**
`time_stop_bars` (16) applies only when net +1R has *not* been reached: decision
on that bar's close, execution on the first 1m bar of the next, taker.
`max_hold_bars` (48) is the cap for trades that *did* reach +1R and are running
toward target. They are different rules and must never be conflated: sizing the
1m walk buffer from the time stop is what previously made the buffer act as an
unconditional exit, silently capping every trade at 16 bars.
`max_walk_minutes` is *derived* from `max_hold_bars` and is not a parameter; if
it is ever exhausted that is `exit_reason = "insufficient_data"`, a data
condition counted separately from any trading decision. `exit_reason
= "walk_end"` no longer exists.

**Why 48 bars.** The mandate is an intraday bot, so an unbounded hold is out of
scope. 48 bars is 12 hours, crossing one to two 8h funding settlements rather
than three. Longer holds also inflate portfolio occupancy, which starves the
strategy of trades — measured: raising the cap from 16 to 48 pushed
`refused_open_position` up and cost 2 of 44 trades on the golden slice alone.
It is a default to be swept later, not a discovered value.

**+1R is measured NET of costs.** The time stop tests a price solved so that
net P&L equals exactly +$20 after the entry taker fee and a taker exit — the
same closed form as the target, for the same reason. A naive
`entry ± stop_distance` level is reached while the trade has *not* actually made
1R, so a trade that is still losing after costs would survive the time stop.
Taker is used for the exit side because a trade continuing past the time stop
exits by stop, target or max-hold, and taker is the conservative assumption.
Detection remains an intrabar 1m touch.

**Divergence flags are reported, never filtered.** `flagged_bar_overlap` is a
column, not a filter. A test asserts the attach function contains no row-dropping.

**Funding is absent entirely.** Not an input to any decision — the rate is
unknowable at entry. It is a separate sensitivity run later. Note the margin
refusal counter is named `insufficient_margin`, deliberately *not* `funding`,
so it cannot be confused with a funding rate once real funding code lands.

**`max_leverage` (3.0) is an unmeasured placeholder**, not a probed exchange
constraint. Bitget's tiered initial margin was never queried. It has never bound
on real data at this setting, so it is untested beyond its fixtures.

**`stop_unresolved_frac` (0.5) is an admitted arbitrary constant**, now config
rather than hardcoded: the fraction of stop distance price must travel beyond
the level within the trigger minute before the fill is flagged `unresolved`.

## Evaluation modes

**Signal mode** is the edge-test instrument. Every signal is simulated
independently — no position limit, no cooldown, no margin cap, no interaction.
Trades may overlap. Run it ONCE over the full ungated universe; the gated arm is
obtained by *filtering* that trade table on `rvol >= threshold`
(`run.gated_arm`), never by a second simulation. This guarantees both arms are
the identical universe by construction, and lets the threshold be swept at zero
simulation cost.

This matters because portfolio mode cannot test the edge claim: ~30% of signals
never become trades because the symbol is occupied, the ungated universe is
larger so it would be censored harder, and *which* signals survive is decided by
arrival order rather than by the gate. That is two differently-censored samples,
and any difference between them is uninterpretable.

**Portfolio mode** is the realism instrument — equity curve, drawdown,
occupancy. Both modes share the same Layer B lifecycle code; only the active
constraint set differs, and a test asserts a single isolated trade is
byte-identical across the two.
