# Backtesting engine (Point 3, amended at Point 3R)

Volume-gated Donchian breakouts on 15m Bitget USDT-M perpetuals, with 1m
intrabar resolution. This directory contains the engine only — no validation
design, no parameter sweep, no performance reporting.

## Layout

| file | role |
|---|---|
| `signals.py` | Layer A — vectorized 15m signal generation. Never touches 1m. |
| `simulate.py` | Layer B — trade lifecycle loop + portfolio constraints + loaders. |
| `costs.py` | Fees, slippage, sizing, target solve, tick rounding. Closed form. |
| `contracts.py` | Tick-size and minimum-order probe, and local cache. |
| `run.py` | Entry point: load → signals → simulate → provenance counters. |

The A/B split is what makes the later parameter sweep cheap: Layer A is pure
and vectorized over all bars, Layer B runs only over signal bars.

## Running

```bash
source .venv/bin/activate

# rebuild the tick cache (needs network; only when contracts change)
python src/engine/contracts.py

# a slice, with provenance counters (never performance figures).
# The four parameters below have NO DEFAULTS and are required -- see
# "Four parameters have no default" under Non-obvious semantics.
python src/engine/run.py --symbols BTCUSDT \
    --start 1672531200000 --end 1675209600000 --summary \
    --stop-atr-mult 2.5 --stop-max-pct 0.035 \
    --rvol-threshold 1.5 --baseline-days 20

# full hand-checkable trace for one trade
python src/engine/run.py --symbols BTCUSDT \
    --start 1672531200000 --end 1675209600000 \
    --stop-atr-mult 2.5 --stop-max-pct 0.035 \
    --rvol-threshold 1.5 --baseline-days 20 \
    --trace-signal-ts 1673881200000

# NO_TIME_STOP counterfactual arm (D1). Not baseline.
python src/engine/run.py ... --no-time-stop
```

There is no runnable default configuration, deliberately. Choosing these values
is a Point 4 sweep decision, and every value used in the test suite is
explicitly labelled as arbitrary fixture scaffolding.

## Tests

```bash
python -m pytest tests/ -q            # full suite; look-ahead demos deselected
python -m pytest -m lookahead -q --override-ini="addopts="   # planted bugs
python tests/make_golden.py           # re-freeze BOTH golden files, deliberately
```

The `lookahead` marker holds two deliberately planted look-ahead bugs. They are
skipped by default and assert that the causality guard *catches* them. Run them
after touching `signals.py`.

## Entry rule after Point 3R

Long, on a closed 15m bar:

    EMA20 > EMA50
    AND close > Donchian-20 upper (channel of the 20 bars ending at T-1)
    AND session-normalised RVOL >= rvol_threshold

Short is the symmetric inverse. **That is the whole entry rule.** No RSI, no
`vwap_position`, no cooldown condition.

Two components were removed on measurement, not on taste:

* **RSI is gone entirely.** `rsi_lower` rejected **zero** of 11,711 breakout
  bars over 2022-23 — the minimum RSI on a long breakout bar was 54.18, more
  than four points clear of the 50 threshold. `rsi_upper` had already been
  removed for violating the Guard Rail Principle (a momentum bound guarding a
  momentum mechanism). The original brief asked for an oscillator; evidence
  removed it. `rsi_wilder` still runs and `rsi` is recorded on every signal row,
  but **no entry condition reads it**, and a test asserts that changing RSI does
  not change which bars signal.
* **`vwap_position` was proposed and killed before it was ever built.** Three
  independent mechanical grounds: measured per direction (which is how the gate
  would be applied) its IQR was 0.089–0.126 against a pre-committed 0.15 cut,
  failing 6 of 6 symbol-years; its median sat at 0.55–0.58 on essentially every
  breakout bar, making it a constant rather than a discriminator; and at that
  dispersion any usable threshold lands in the densest part of the distribution,
  so classification would be noise-dominated. It is **not** a labelled variant
  and must not be revived — doing so post-hoc is the iterative search D5 bans.

**RVOL is session-normalised and quote-denominated.** The baseline is the
**median** of the same 15-minute UTC slot (96 slots/day) over the trailing
`baseline_days` **completed prior days**. Bar T's own day contributes nothing —
not even earlier slots of it.

Why: the old flat 20-bar mean is a 5-hour window, short enough to sit inside one
phase of the diurnal cycle, so the denominator tracked the *slope* of that cycle
and the gate partly measured what time it was. Measured, the flat gate's pass
rate on breakout bars swung **32–51 percentage points** by hour of UTC day;
session-normalisation compresses that in 5 of 6 symbol-years.

Median rather than mean because a single event bar in the baseline would inflate
a mean and suppress RVOL for that slot every day for the rest of the window.
Quote rather than base denomination because `quote_volume` was the more stable
trailing baseline in 3 of 3 symbols across both years. Numerator and denominator
always use the same field, and a test asserts it — mixing them divides a
quantity by a value in different units.

Cost: the warm-up is now `baseline_days` **days**, not 20 bars. Warm-up bars
produce no signal and are counted by `signals.warmup_bars`.

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

**Four parameters have no default.** `stop_atr_mult`, `stop_max_pct`,
`rvol_threshold` and `baseline_days` must be supplied explicitly; `CostConfig`
raises `ValueError` if any is missing, and `run()` raises if given no config at
all. Each was previously a placeholder that silently acted as a chosen value —
`stop_atr_mult = 1.5` in particular was never chosen by anyone and was measured
to sit below `m*` (the multiplier at which median ATR% clears the derived floor)
in every symbol-year, which is why the floor was binding on 65–81% of trades. A
stale default that looks like a decision is the specific failure this removal
prevents.

**`stop_min_pct` is DERIVED per symbol, never chosen.**

    stop_min_pct = max( N_cost * c_roundtrip , risk_usd / (E * L_max) )

with `N_cost` = 6, and `c_roundtrip` = entry taker + stop taker + entry slippage
+ stop-market haircut = 0.06% + 0.06% + 0% + haircut. That gives **1.020% for
BTC/ETH** (5 bps haircut) and **1.320% for SOL** (10 bps). The cost term
dominates the leverage term by 3.06–3.96×.

It is per-symbol because its *inputs* are per-symbol, not because it was tuned
per symbol — `N_cost` is the shared parameter, and there are still no per-symbol
knobs. The haircut applies on the stop leg only; entry slippage is deliberately
0 because the 1m-close fill convention already absorbs latency, so charging a
haircut on both legs would double-count.

The leverage term stays in the formula even though it is nowhere near binding,
so that a future downward revision of `N_cost` cannot silently make it
load-bearing without anyone noticing. It also has a useful consequence: when it
*does* bind, notional is guaranteed below `E * L_max`, so a single trade can
never be refused for margin. Margin refusal survives only for concurrent
positions.

**`stop_max_pct` and the exchange minimum are two different guard rails.** A5
re-derived the cap as target-plausibility *and* exchange-minimum protection —
explicitly not loss limitation, since with fixed `risk_usd` a wider stop means a
smaller position and dollar risk is constant by construction. Per the Guard Rail
Principle these are implemented separately and in different units:
`stop_max_pct` caps stop width in **percent of price**; `check_min_qty` rejects
orders below Bitget's `minTradeNum` / `minTradeUSDT` in **quantity and
notional**. The second refuses loudly rather than letting a sub-minimum order
round silently to nothing.

**Provenance counters added at 3R (A7).** `stop_binding_mechanism` ∈
{`atr`, `floor`, `cap`} per trade, decided on the *raw* distance before tick
rounding so a rounding artifact cannot relabel an ATR stop as a floor stop; and
`size_binding_mechanism` ∈ {`risk_rule`, `leverage_cap`, `min_qty`}, which
closes the Point 3 gap where `max_leverage = 3.0` was never measured. Taken
trades always record `risk_rule` because the other two *refuse* rather than
resize — the refusal counts carry that information instead.

**Cooldown: the extreme rule was REMOVED at 3R.** It was a provable logical
no-op — a long entry requires a close above the Donchian-20 upper band, which
*is* a new 20-bar high, so the condition that cleared the cooldown was entailed
by the condition that triggered it. It could never bind, and an inert rule that
looks like a live one is worse than no rule. What survives is `cooldown_bars`
(default **0**, behaviourally inert there), a pure bar count that blocks
re-entry in that symbol *and direction* for N bars after a stop-out. It is
retained rather than deleted because it was registered as a sweep dimension
before the firewall, and deleting it would make it untestable later without
violating the D5 single-pass rule. Cooldown remains direction-specific: a
stopped long does not block shorts.

**Two separate holding rules, both DERIVED from the Donchian period.**

    time_stop_bars = tau * donchian_period      tau = 1.0  ->  20 bars
    max_hold_bars  = 2 * donchian_period                   ->  40 bars

The old values 16 and 48 are void. Only `tau` is sweepable, over a narrow band
around 1.0; `max_hold_bars` is *not* independently sweepable, and both are
read-only properties so passing them raises `TypeError`.

**Why the Donchian period.** At bar 20 post-entry every bar in the Donchian
lookback is post-breakout: the 20-bar high that was broken has rolled out of the
window, so the reference frame that generated the signal no longer exists. That
is a structural argument about when the thesis expires, replacing a pair of
unrelated placeholders.

`max_walk_minutes` is *derived* from `max_hold_bars` and is not a parameter; if
it is ever exhausted that is `exit_reason = "insufficient_data"`, a data
condition counted separately from any trading decision. `exit_reason
= "walk_end"` no longer exists.

**The time stop is a STATE CHECK, not a latch.** At the close of the 15m bar
`time_stop_bars` after entry, the trade must *be* at or above `threshold_R`, net
of costs. "Did it ever touch" is deliberately not the test.

This supersedes the Point 3 decision to measure +1R by intrabar 1m touch, and it
changes behaviour: a trade that wicks to +1R and immediately retraces is now cut
at the checkpoint. Three reasons. A wick to +1R that does not hold is a
liquidity-vacuum failure, not a healthy trade. The state check stays inside
Layer A's 15m world with no 1m dependency. And it carries no latch state, so
there is nothing to get wrong across a data gap.

Accepted cost, stated plainly: a trade that ran to +1.8R and retraced to +0.9R
gets cut while in profit. `touched_threshold_intrabar` is recorded on every
trade so the size of that population stays measurable, but **no rule reads it**.

Decision on the checkpoint close, execution on the first 1m bar of the next 15m
bar, taker — mirroring the entry convention. `time_stop_enabled=False` selects
the **NO_TIME_STOP** counterfactual arm (D1) for the D5 leave-one-out pass; it
disables the checkpoint and nothing else.

**`threshold_R` is an OUTPUT, not an input.**

    phi = (threshold_R / target_R) / (time_stop_bars / max_hold_bars)

`phi` = 1.0 is linear pace and is the only free parameter here. With
`target_R` = 2, 20 and 40 bars it solves to exactly **+1R** — the original
value, now for a reason. The old geometry implied `phi` = (1/2)/(16/48) = **1.5**,
demanding 50% of the price journey in 33% of the time budget. Nobody chose that;
it fell out of two unrelated placeholders. Front-loading (`phi` > 1) is a real
momentum-decay claim and must be discovered by a sweep, not assumed.

**`threshold_R` is measured NET of costs.** The state check tests a price solved
so that net P&L equals exactly `threshold_R * $20` after the entry taker fee and
a taker exit — the same closed form as the target, for the same reason. A naive
`entry ± stop_distance` level is reached while the trade has *not* actually made
1R, so a trade that is still losing after costs would survive the checkpoint.
Taker is used for the exit side because a trade continuing past the checkpoint
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
