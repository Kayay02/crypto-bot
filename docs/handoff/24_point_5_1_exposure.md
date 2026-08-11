# REPORT 24 — MAXIMUM-HOLD EXPOSURE PROFILE OF THE FROZEN THESIS

**Point 5, sub-point 5.1.** The thesis is frozen
(`docs/handoff/22_point_1_thesis.md` at `02e47a5`, as amended by
`docs/handoff/22a_point_1_thesis_amendment_1.md` at `703046a`) and Point 1
(reopened) is closed (`docs/handoff/23_point_1_reopened_closing.md` at
`5e4d970`). **Nothing in this report changes any of them, and nothing here is a
fix.** This step measures; 5.2 sets portfolio construction rules and 5.3 fixes
position sizing.

**WHY THIS MEASUREMENT EXISTS.** The closing record §3.1 concluded that leverage
*"does not bind at present values"* on the basis of
`$20 / ($2,000 × 3) = 0.333%`. **That is a SINGLE-POSITION check.** It
establishes the tightest stop one trade could carry, and it is correct as far as
it goes. **It says nothing about aggregate exposure when several positions are
open at once.** The frozen time exit holds a position to the third funding
settlement after entry — 16 to 24 hours at 1h — across three symbols, so
overlapping positions are the expected case rather than the exceptional one.
Their frequency had never been measured. It is measured here.

**THE ANSWER, IN ONE LINE.** With every signal taken and no concurrency cap, the
book carries a **median of 9 positions** and **required leverage of 3.59×**,
with a maximum of **28 positions at 13.52×**. The account is occupied on
**99.84% of bars**. **Required leverage exceeds the engine's own configured
`max_leverage = 3.0` on 63.9% of all bars in the window.**

**The performance firewall is armed.** No expectancy, win rate, profit factor,
Sharpe, Sortino, equity curve, drawdown, `r_multiple`, `net_pnl` or `gross_pnl`
quantity is computed, inspected, estimated or referenced. **No stop or target is
evaluated.** **No bar after the entry bar is read for any purpose** — the
maximum-hold exit is located on the funding calendar, which is arithmetic on a
timestamp and reads no data at all. Every figure here is a count, a timestamp, a
notional or an occupancy: bar-level and signal-level quantities of the same
admissible class as report 21's signal counts. A test walks the module's AST and
refuses any performance name as an identifier or a string literal.

**Window read: 2022-01-01 to 2024-12-31 only. THE HOLDOUT IS SEALED** — the
window is inherited whole from `src/timeframe/resample.py` by way of
`sweep_population`, and this module defines no window constant of its own. The
planted mutation is reported in §9.4.

**Nothing here is swept.** Donchian-10, 1h, 2.25 × ATR(14) with a 1.50% floor,
n = 3 settlements. **One configuration, no free parameter, no grid.**

---

## 1. PROVENANCE

| item | value |
|---|---|
| `git rev-parse HEAD` at measurement | **`5e4d970b8ed4bc95b3b7262b6cb07e9f7a85f803`** |
| `--dirty` state at measurement | **dirty** — two untracked files, `src/analysis/exposure_profile.py` and `tests/test_exposure_profile.py`, which are the module and tests this report describes and which are committed together with it |
| module | **`src/analysis/exposure_profile.py`** |
| tests | **`tests/test_exposure_profile.py`** |
| signal detection | **`src/analysis/sweep_population.py`** (report 21, `aea6b5c`) — **REUSED UNMODIFIED. No refactor was required and no line of it was changed.** |
| sizing | **`src/engine/costs.py::position_size`**, called directly. Not modified. |
| fold boundaries | `data/derived/folds/folds.json`, nine in-sample folds; the `holdout` entry is never walked |

**No file was modified by this step.** `src/engine/costs.py`, `src/costs/`,
`src/timeframe/`, `src/analysis/sweep_population.py`,
`src/analysis/rsi_breakout_profile.py`, the engine, and every document numbered
22, 22a and 23 are untouched.

### 1.1 THE BAR TIMESTAMP CONVENTION — established, not assumed

> **BAR TIMESTAMPS ARE OPEN TIMES.** A 1h bar labelled `T` covers `[T, T + 1h)`
> and **CLOSES at `T + 1h`**.

**The fields read to establish it**, three independent statements of the same
convention plus the arithmetic consequence on the real series:

| source | field / line | what it says |
|---|---|---|
| `src/data/backfill_bitget.py` | module docstring, line 13 | *"Timestamps are the bar's OPEN time. Results ASCENDING."* — the venue fact, recorded at the point the data entered the project |
| `src/folds/schedule.py` | `LAST_BAR_OFFSET_MS = DAY_MS - BAR_15M_MS`, line 34 | *"Last 15m bar of a day opens at 23:45"* — an open time; a close-time series would end the day at 00:00 |
| `src/timeframe/resample.py` | `bucket = src["ts"] - (src["ts"] % period_ms)`, line 203 | the output `ts` is the bucket **START** |
| `src/engine/contracts.py` | `TickSchedule.tick_at`, line 45 | *"Tick in force at bar-open timestamp `ts`"* |

**The consequence on the data, checked:** the 1h series runs from
**2022-01-01T00:00:00Z** to **2024-12-31T23:00:00Z**. Under a close-time reading
the first bar would be 01:00 on the first day and the last would be
00:00:00Z of the day *after* the window — the latter being inside the seal. It
is neither. Asserted by test.

**Everything downstream depends on this.** Entry instant is `T + 1h`; the
settlement crossing is counted from `T + 1h`; the occupancy interval is
`(T + 1h, X + 1h]`. An open/close confusion would move every entry instant by an
hour, which would shift the settlement bucket for one entry hour in eight and
change the hold on 12.5% of positions by 8 hours.

---

## 2. THE CONFIG TABLE — every input `position_size` reads

**Taken from the engine, not restated.** `costs.CostConfig` with
`stop_atr_mult = 2.25` (the frozen thesis value) and three construction-only
parameters that `position_size` never reads.

| symbol | taker fee | entry slippage (bps) | stop haircut (bps) | `risk_usd` | `qty_step` | `min_trade_num` | `min_trade_usdt` |
|---|---:|---:|---:|---:|---:|---:|---:|
| BTCUSDT | **0.0006** | **0.0** | **5.0** | **$20.00** | **0.0001** | 0.0001 | 5.0 |
| ETHUSDT | **0.0006** | **0.0** | **5.0** | **$20.00** | **0.01** | 0.01 | 5.0 |
| SOLUSDT | **0.0006** | **0.0** | **10.0** | **$20.00** | **0.1** | 0.1 | 5.0 |

`qty_step` values come from `config/contracts_cache.json` via
`contracts.load_order_specs`. **Account capital: $2,000.00**, transcribed from
the engine's own `CostConfig` account constant and pinned against it by test.

**THE THREE CONSTRUCTION-ONLY PARAMETERS.** `stop_max_pct`, `rvol_threshold` and
`baseline_days` have no default after Point 3R and must be supplied to build the
object. **None of them is read.** A test varies all three (0.20 / 99.0 / 3
against 0.035 / 1.5 / 20) and asserts the resulting position table is
bit-identical, so a strategy parameter cannot reach an exposure figure through
the config object.

**`stop_geometry` IS DELIBERATELY NOT CALLED.** The engine's stop floor is
`cfg.stop_min_pct(symbol)` — a **derived** figure, 1.020% for BTC and ETH and
1.320% for SOL — while the thesis freezes **1.50%**. They are different numbers.
The thesis wins: the stop distance here is computed from the thesis rule and
handed to `position_size` as an argument. A test enumerates the engine surface
this module touches and asserts it is exactly `{position_size, CostConfig}`.

### 2.1 What the sizing call actually charges

`position_size` divides `risk_usd` by the **all-in cost of one unit on a losing
trade** — the price move plus both fee legs plus both slippage legs:

    denom = (entry − stop) + entry × f + stop × f + entry × slip_in + stop × h

**This is why the engine is called rather than a formula being written.** Two
plausible hand forms both give the wrong answer:

| form | quantity, against the engine's | why it is wrong |
|---|---:|---|
| naive `risk / (entry − stop)` | **+7.4%** | omits both fee legs and the haircut |
| tolerance form `risk / (s × 1.11)` | **−3.2%** | **`COST_TOLERANCE_R = 0.11` is a BUDGET CEILING, not a cost** |

The worked example is BTCUSDT long, entry 30,000, ATR 300, stop distance 675:
`denom = 675 + 18 + 17.595 + 0 + 14.6625 = 725.2575`, pinned by hand arithmetic
in the tests.

### 2.2 NOTIONAL IS AN UPPER BOUND — the engine performs no lot rounding

**`position_size` returns an UNQUANTISED quantity.** The closing record §6.1
records that `qty_step` is *"parsed, stored, serialised and printed, and never
read by sizing or execution"*. **Flooring to `qty_step` in 5.3 will reduce every
quantity**, so every notional in this report is at or above what an exchange
would have accepted. Measured, for scale:

| symbol | notional lost to flooring, pooled | worst single position |
|---|---:|---:|
| BTCUSDT | **0.2063%** | 1.4747% |
| ETHUSDT | **1.2639%** | **9.2126%** |
| SOLUSDT | **0.6668%** | 6.9954% |

**ETH is the granularity-binding symbol**, consistent with the closing record
§6.1. The pooled correction is under 1.3% on every symbol, so **flooring will
not materially reduce any figure in §7** — it moves 13.52× to roughly 13.4×, not
to 3×.

---

## 3. SIGNAL COUNTS — and the 570 / 281 ambiguity, RESOLVED

**THREE POPULATIONS ARE NAMED, and every count below says which one it is.**

| name | definition |
|---|---|
| **signal bars** | bars carrying either mask, **two-sided bars INCLUDED**. This is report 21's `n_signals`. |
| **two-sided bars** | bars carrying BOTH masks. **Skipped by rule** (thesis §4.1). |
| **positions** | signal bars − two-sided bars. **THE TRADED POPULATION**, and the one every occupancy figure rests on. |

### 3.1 SIGNAL BARS, per symbol per fold — TRAIN (minimum 200)

| symbol | F1 | F2 | F3 | F4 | F5 | F6 | F7 | F8 | F9 | **min** |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| BTCUSDT | 617 | 613 | 617 | 594 | 600 | 626 | 645 | 655 | 688 | **594** |
| ETHUSDT | 616 | 605 | 596 | 586 | **570** | 611 | 653 | 642 | 664 | **570** |
| SOLUSDT | 710 | 659 | 597 | 584 | 599 | 657 | 669 | 675 | 713 | **584** |
| **POOLED** | 1,943 | 1,877 | 1,810 | **1,764** | 1,769 | 1,894 | 1,967 | 1,972 | 2,065 | **1,764** |

### 3.2 SIGNAL BARS, per symbol per fold — TEST (minimum 50)

| symbol | F1 | F2 | F3 | F4 | F5 | F6 | F7 | F8 | F9 | **min** |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| BTCUSDT | 306 | 311 | 283 | 317 | 309 | 336 | 319 | 369 | 326 | **283** |
| ETHUSDT | 299 | 297 | 289 | **281** | 330 | 323 | 319 | 345 | 337 | **281** |
| SOLUSDT | 296 | 301 | 283 | 316 | 341 | 328 | 347 | 366 | 378 | **283** |
| **POOLED** | 901 | 909 | **855** | 914 | 980 | 987 | 985 | 1,080 | 1,041 | **855** |

### 3.3 THE AMBIGUITY IS RESOLVED — 570 and 281 are PER SYMBOL PER FOLD

> **Report 21's "worst of nine training folds: 570 signals against a 200
> minimum" and "worst of nine test folds: 281 against 50" are PER SYMBOL PER
> FOLD counts of SIGNAL BARS (two-sided bars included). They are ETHUSDT fold 5
> train and ETHUSDT fold 4 test, reproduced exactly.**

**The pooled reading cannot produce either number.** Pooled across the three
symbols the worst training fold is **1,764** (fold 4) and the worst test fold is
**855** (fold 3) — 3.1× and 3.0× the quoted figures. Both readings are
reproduced above and the test asserts the per-symbol one hits 570 and 281 on the
nose while the pooled one hits neither.

**This matters beyond bookkeeping.** Under the per-symbol reading the margin
over the minimum is 2.85× and 5.62×, as report 21 stated. Under the pooled
reading it would have looked like 8.8× and 17.1×, and a future step choosing
whether a per-symbol population is large enough to stratify would have been
reading a number three times too large.

### 3.4 THE TRADED POPULATION — positions, per symbol per fold

| symbol | period | F1 | F2 | F3 | F4 | F5 | F6 | F7 | F8 | F9 | **min** |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| BTCUSDT | train | 607 | 601 | 598 | 577 | 590 | 619 | 641 | 651 | 685 | **577** |
| ETHUSDT | train | 614 | 596 | 579 | 572 | **563** | 609 | 651 | 639 | 661 | **563** |
| SOLUSDT | train | 707 | 654 | 592 | 579 | 596 | 655 | 666 | 672 | 710 | **579** |
| BTCUSDT | test | 299 | 299 | **278** | 312 | 307 | 334 | 317 | 368 | 325 | **278** |
| ETHUSDT | test | 291 | 288 | 284 | 279 | 330 | 321 | 318 | 343 | 335 | **279** |
| SOLUSDT | test | 294 | 298 | 281 | 315 | 340 | 326 | 346 | 364 | 375 | **281** |

**Whole window: 3,735 (BTC) + 3,715 (ETH) + 3,934 (SOL) = 11,384 positions**
from 11,485 signal bars. Direction split: **5,572 long / 5,812 short** — a
2.1-point short tilt, present on all three symbols.

**Dropping two-sided bars costs at most 19 signals in any fold**, and the worst
traded fold is **563 train** against a 200 minimum (2.82×) and **278 test**
against 50 (5.56×). **Signal count remains not a constraint on the traded
population either.**

---

## 4. TWO-SIDED BARS AND THE FLOOR BINDING CROSS-CHECK

### 4.1 Two-sided bars — the frozen figures reproduced exactly

Thesis §4.1 records report 21's count as **86 / 59 / 32** (BTC / ETH / SOL)
*"at Donchian-10 across all nine training periods"*, at most 19 in any single
fold.

| symbol | sum over the nine TRAIN periods | sum over the nine TEST periods | **distinct bars, whole window** |
|---|---:|---:|---:|
| BTCUSDT | **86** ✓ | 37 | **48** |
| ETHUSDT | **59** ✓ | 31 | **33** |
| SOLUSDT | **32** ✓ | 17 | **20** |

Per-fold maximum over train periods: **19** (BTC, fold 3) ✓.

**NAME THE POPULATION.** The frozen 86 / 59 / 32 is a **sum over nine
OVERLAPPING training windows** — adjacent training windows overlap by 50%
(`src/folds/schedule.py`), so a bar in an overlap is counted twice. The count of
**distinct** two-sided bars in the whole window is **48 / 33 / 20**, roughly 55%
of the quoted figure. Both are correct; they answer different questions. This is
recorded because the closing record §4.1's transferable lesson is exactly this
one, and the 86/59/32 figure is the kind that reads as a bar count.

### 4.2 FLOOR BINDING — the frozen §5.1 rates reproduced to four decimal places

**This is the cross-check that had to pass before any exposure figure could be
reported.** Computed with report 21's own `floor_binding_fraction` on report
21's own signal-bar population, so it is an identity rather than a
re-derivation.

| symbol | **thesis §5.1 (frozen)** | **measured here** | difference |
|---|---:|---:|---:|
| BTCUSDT | **46.15%** | **46.1538%** | **0.0000 pp** |
| ETHUSDT | **29.43%** | **29.4290%** | **0.0000 pp** |
| SOLUSDT | **3.09%** | **3.0855%** | **0.0045 pp** |

**NO STOP CONDITION.** The signal population reproduces the already-frozen
result exactly.

On the **traded** population (two-sided bars removed) the rates are
**45.9438% / 29.3405% / 3.0757%** — within 0.22 points of the signal-bar figures
on every symbol, so removing two-sided bars does not select a different
volatility population.

### 4.3 Floor binding per fold — a pre-registered monitored quantity

Thesis §5.1 requires this reported per fold, per symbol, as a fraction of trades
taken. On the **traded population**:

| symbol | period | F1 | F2 | F3 | F4 | F5 | F6 | F7 | F8 | F9 |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| BTCUSDT | train | 13.2% | 40.1% | 59.5% | 60.7% | 83.4% | 80.9% | 52.1% | 42.1% | 41.3% |
| BTCUSDT | test | 68.6% | 50.5% | 71.6% | **93.9%** | 67.8% | 37.7% | 46.7% | 36.7% | 44.9% |
| ETHUSDT | train | **1.3%** | 17.8% | 35.2% | 48.4% | 77.1% | 68.0% | 38.3% | 27.4% | 22.1% |
| ETHUSDT | test | 36.4% | 34.0% | 63.0% | **91.4%** | 48.2% | 28.0% | 26.7% | 17.8% | 13.4% |
| SOLUSDT | train | **0.0%** | 3.5% | 3.9% | 5.7% | 13.1% | 7.5% | 0.6% | 0.9% | 1.6% |
| SOLUSDT | test | 7.8% | **0.0%** | 11.7% | 14.3% | 1.2% | 0.0% | 1.7% | 1.4% | 1.3% |

**THE POOLED BINDING RATE HIDES AN ENORMOUS FOLD-TO-FOLD SWING.** BTCUSDT ranges
from **13.2% to 93.9%** and ETHUSDT from **1.3% to 91.4%**. Fold 4 test — the
low-volatility second half of 2023 — has the floor setting the stop on **more
than nine trades in ten** on both BTC and ETH. **In that fold "2.25 × ATR" does
not describe the stop rule at all; a fixed 1.50% does.** Kill condition (d)
stratifies on exactly this, and the stratification is not remotely balanced
within folds.

**Reported, not adjudicated.** No parameter is proposed and none is changed.

---

## 5. THE MAX-HOLD RULE AND THE ELAPSED HOLD DISTRIBUTION

### 5.1 The rule as implemented

> A position opened at the close of bar `T` is held until the close of the bar
> **preceding the third funding settlement strictly after the entry instant**.
> Settlements are at **00:00, 08:00 and 16:00 UTC**, `n = 3`.

**Denominated in settlements, not bars.** The settlement grid is the multiples of
8 hours from the epoch — the Unix epoch begins at 00:00:00Z and 8h divides a day
exactly, so no offset term is needed and none is accepted.

**STRICTLY AFTER.** An entry instant landing exactly on a settlement does not
count that settlement, so an entry at exactly 16:00Z looks forward to 00:00,
08:00 and 16:00 of the following day.

**"THE BAR PRECEDING THE SETTLEMENT"** is the bar whose **open** is the last bar
open before it — at 1h, `settlement − 1h` — and that bar **closes at the
settlement instant**. Bars are labelled by open time, so the bar preceding 16:00
is the bar labelled 15:00, not the bar labelled 14:00. **This is the reading
that makes the thesis's own stated 24-hour upper bound attainable:** an entry at
exactly a settlement instant holds for exactly 24 hours. Under the other reading
the maximum would be 23 and the frozen band's top edge could never be reached.

### 5.2 The elapsed hold distribution — the settlement-logic check

**At 1h every entry instant lands on an hour boundary, so the hold takes exactly
eight values.** `hold = 24 − (entry_hour mod 8)` hours, taking 24 when that is 0.

| hold (hours) | 16 | 17 | 18 | 19 | 20 | 21 | 22 | 23 | 24 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **positions** | 0 | 1,493 | 1,431 | 1,451 | 1,226 | 1,391 | 1,368 | 1,592 | 1,432 |

**Min 17h, max 24h, mean 20.51h, median 21h, over all 11,384 positions.** Every
hold is inside the frozen 16–24 hour band, asserted on every position rather
than sampled.

**16 IS THE BAND'S EDGE, NOT AN ATTAINABLE VALUE ON AN HOURLY GRID.** The last
entry instant before a settlement is one hour before it, which reaches its third
settlement 17 hours later. The frozen band is stated as a band and is satisfied
as a band; nothing here needs it to be tight.

**THE DISTRIBUTION IS NOT UNIFORM AND THAT IS NOT A BUG.** It is the
entry-**hour** distribution pushed through a deterministic map, and signal
arrival is not uniform across the UTC day — Point 4 measured diurnal swings of
32–51 percentage points in pass rates by hour. The 20-hour bucket (1,226) and
the 23-hour bucket (1,592) differ by 30%, which is the diurnal structure showing
through. **No claim is made about it and it is not pursued.**

### 5.3 The occupancy convention

> A position opened at the close of bar `T` and closed at the close of bar `X`
> is open on bars **`T+1` … `X` inclusive** — the half-open instant interval
> `(close of T, close of X]`.

**It is NOT open on its own signal bar**, because at every moment of that bar it
did not yet exist, and **it IS open on its exit bar**, because it is carried
through that bar and closed at its end. **The occupied bar count is then exactly
the hold in hours**, which is what makes the hand-computed control in §9.1
checkable. The two neighbouring conventions each differ by one bar per position,
which on 11,384 positions moves every mean and every histogram while breaking no
invariant and raising nothing.

**THE TIMELINE IS CLIPPED AT THE WINDOW EDGE AND THE CLIPPING IS COUNTED.** Exit
timestamps are calendar values; a position entered in the last hours of the
window exits past it. **10 positions** (2 BTC, 4 ETH, 4 SOL) have their tails
truncated at the last measured bar. No bar is read to produce those exits and
none is read past them.

---

## 6. PER-SYMBOL OCCUPANCY

**26,190 bars per symbol** (26,304 raw 1h bars less the 114-bar warm-up),
2022-01-05T18:00:00Z to 2024-12-31T23:00:00Z. **Zero buckets dropped**, so the
hourly calendar grid and the bar series coincide exactly — asserted by test,
because every per-bar fraction below is denominated in grid bars.

### 6.1 Concurrent position count, whole window

| symbol | **max** | P99 | P95 | P90 | median | mean | bars occupied |
|---|---:|---:|---:|---:|---:|---:|---:|
| BTCUSDT | **12** | 7 | 6 | 5 | **3** | **2.92** | 95.09% |
| ETHUSDT | **11** | 7 | 6 | 5 | **3** | **2.90** | 95.17% |
| SOLUSDT | **10** | 8 | 6 | 5 | **3** | **3.09** | 96.97% |

### 6.2 Open notional, whole window (USDT, over ALL bars including empty ones)

| symbol | **max** | P99 | P95 | P90 | median | mean |
|---|---:|---:|---:|---:|---:|---:|
| BTCUSDT | **14,219.70** | 8,382.09 | 5,993.94 | 5,646.55 | 2,651.24 | 3,010.53 |
| ETHUSDT | **11,985.49** | 7,668.49 | 5,984.48 | 4,792.83 | 2,395.16 | 2,673.79 |
| SOLUSDT | **10,151.50** | 5,912.24 | 4,437.24 | 3,650.68 | 1,699.51 | 1,939.71 |

**A single symbol's open notional exceeds the whole $2,000 account on the median
bar, on all three symbols.**

### 6.3 Fraction of bars at each concurrency level

| level | BTCUSDT | ETHUSDT | SOLUSDT |
|---:|---:|---:|---:|
| 0 | 4.906% | 4.834% | 3.032% |
| 1 | 14.464% | 15.449% | 13.559% |
| 2 | 24.086% | 22.784% | 23.158% |
| 3 | 23.860% | 24.196% | 24.223% |
| 4 | 16.464% | 16.930% | 17.258% |
| 5 | 9.397% | 9.443% | 10.344% |
| 6 | 4.269% | 3.971% | 5.055% |
| 7 | 1.577% | 1.420% | 2.287% |
| 8 | 0.649% | 0.676% | 0.821% |
| 9 | 0.214% | 0.214% | 0.229% |
| 10 | 0.038% | 0.069% | 0.034% |
| 11 | 0.050% | 0.015% | — |
| 12 | 0.027% | — | — |

Every level from 0 to the maximum is listed, including levels that never occur,
so a missing row cannot read as a level never reached.

### 6.4 SIGNALS ARRIVING INTO AN ALREADY-OPEN SYMBOL

| symbol | positions | opened while ≥1 already open on that symbol | **fraction** |
|---|---:|---:|---:|
| BTCUSDT | 3,735 | 3,577 | **95.77%** |
| ETHUSDT | 3,715 | 3,542 | **95.34%** |
| SOLUSDT | 3,934 | 3,793 | **96.42%** |

> **OVERLAP IS NOT AN EDGE CASE. IT IS ESSENTIALLY THE ONLY CASE.** Fewer than
> one signal in twenty arrives at a flat book on its own symbol. Any
> concurrency rule 5.2 writes will therefore act on ~95% of signals, not on a
> tail of them, and a "one position per symbol" cap would discard roughly
> nineteen signals in twenty rather than trimming an occasional pile-up.

### 6.5 Notional per position — bounded above, and the bound binds often

| symbol | mean | median | min | **max** |
|---|---:|---:|---:|---:|
| BTCUSDT | 1,030.92 | 1,141.91 | 230.13 | **1,198.79** |
| ETHUSDT | 920.83 | 957.99 | 166.97 | **1,198.79** |
| SOLUSDT | 629.48 | 598.59 | 40.13 | **1,164.41** |

**The maximum is structural, not empirical.** Under cost-inclusive sizing
`notional = risk_usd / (s + c)`, and `s` is bounded below by the 1.50% floor, so

    max notional = 20 / (0.0150 + c)

which is **$1,198.79** at the BTC/ETH round-trip cost and **$1,164.41** at SOL's.
**One floor-bound position is 0.599× the account.** The BTC median sits at 95%
of that ceiling because the floor binds on 46% of its signals.

**The arithmetic that follows from it:** `3.0 / 0.599 = 5.008`, so **six
simultaneous floor-bound positions breach 3× leverage**. The median book carries
nine.

---

## 7. BOOK-LEVEL OCCUPANCY — the number this step exists to produce

All three symbols aligned on the common UTC hourly grid, **26,190 bars**.

### 7.1 The headline table

| quantity | **max** | P99 | P95 | P90 | median | mean |
|---|---:|---:|---:|---:|---:|---:|
| **positions open** | **28** | 19 | 15 | 14 | **9** | **8.91** |
| **notional open (USDT)** | **27,045.20** | 17,826.90 | 14,257.18 | 12,641.37 | **7,182.00** | **7,624.06** |
| **required leverage (× $2,000)** | **13.52×** | 8.91× | 7.13× | 6.32× | **3.59×** | **3.81×** |
| **nominal risk open (USDT)** | **560.00** | 380.00 | 300.00 | 280.00 | **180.00** | **178.24** |

**Nominal risk open is `positions × $20`.** At the median the book has **$180 of
nominal risk against $2,000 of capital — 9.0% of the account**. At the maximum
it is **$560, or 28.0%.** *(This is nominal risk as the position-sizing rule
defines it. It is not a loss, not an expected loss, and not a drawdown — no
outcome is evaluated anywhere in this report.)*

### 7.2 REQUIRED LEVERAGE AGAINST THE ENGINE'S OWN CAP

`costs.CostConfig.max_leverage = 3.0`, described in the source as *"NOT a probed
exchange constraint — an unmeasured placeholder"*, and the engine refuses trades
whose notional could not have been carried.

| required leverage | bars | **fraction of the window** |
|---|---:|---:|
| > 1× | 25,350 | **96.79%** |
| > 2× | 22,064 | **84.25%** |
| **> 3× — the configured cap** | **16,742** | **63.93%** |
| > 4× | 10,793 | 41.21% |
| > 5× | 6,128 | 23.40% |
| > 6× | 3,196 | 12.20% |
| > 8× | 567 | 2.17% |
| > 10× | 88 | 0.34% |
| > 12× | 16 | 0.06% |

> **THE SINGLE-POSITION CHECK AND THE AGGREGATE ANSWER POINT IN OPPOSITE
> DIRECTIONS.** One position at the floor requires **0.599×**, comfortably
> inside 3×, which is what the closing record §3.1's leverage term was
> measuring and it was right. **The uncapped book requires more than 3× on
> 63.93% of bars and more than 8× on 2.17%.** Leverage does not bind per trade
> and binds heavily in aggregate. **Nothing is decided here** — whether the cap
> is real, whether the margin mode is cross or isolated, and what the
> concurrency limit should be are all 5.2's decisions.

### 7.3 Fraction of bars at each book concurrency level

| level | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **bars** | 43 | 88 | 348 | 780 | 1,207 | 2,008 | 2,400 | 2,825 | 3,010 | 3,013 |
| **fraction** | 0.164% | 0.336% | 1.329% | 2.978% | 4.609% | 7.667% | 9.164% | 10.787% | 11.493% | 11.504% |

| level | 10 | 11 | 12 | 13 | 14 | 15 | 16 | 17 | 18 | 19 |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **bars** | 2,583 | 2,129 | 1,735 | 1,238 | 951 | 662 | 423 | 273 | 191 | 110 |
| **fraction** | 9.863% | 8.129% | 6.625% | 4.727% | 3.631% | 2.528% | 1.615% | 1.042% | 0.729% | 0.420% |

| level | 20 | 21 | 22 | 23 | 24 | 25 | 26 | 27 | 28 |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **bars** | 74 | 36 | 32 | 9 | 15 | 3 | 1 | 1 | 2 |
| **fraction** | 0.283% | 0.137% | 0.122% | 0.034% | 0.057% | 0.011% | 0.004% | 0.004% | 0.008% |

**The book is empty on 43 bars out of 26,190 — 0.164%.** It carries at least six
positions on 82.9% of bars.

### 7.4 DIRECTIONAL COMPOSITION

| quantity | value |
|---|---:|
| mean long positions open | 4.364 |
| mean short positions open | 4.548 |
| occupied bars | 26,147 |
| **bars where ALL open positions share one direction** | **5,362** |
| **fraction of occupied bars, single-direction** | **20.51%** |
| — of which all long | 2,624 |
| — of which all short | 2,738 |

**One occupied bar in five carries a book that is entirely one-sided.** At the
median concurrency of nine positions that is nine simultaneous same-direction
positions across three correlated majors. **This is a correlation-risk input for
5.2 and it is not evaluated here** — no covariance, no beta, no joint-move
estimate is computed, and nothing in this report says what a one-sided book
would do.

### 7.5 THE SINGLE WORST BAR IN THE WINDOW

| field | value |
|---|---|
| **timestamp (bar open, UTC)** | **2024-07-15T22:00:00Z** |
| bar interval | 2024-07-15T22:00:00Z → 2024-07-15T23:00:00Z |
| **total positions open** | **28** |
| — BTCUSDT | **9** positions, **$9,261.34** |
| — ETHUSDT | **11** positions, **$11,561.97** |
| — SOLUSDT | **8** positions, **$6,221.89** |
| **total notional open** | **$27,045.20** |
| **required leverage** | **13.5226×** |
| **direction** | **28 short, 0 long — the book is entirely one-sided** |
| nominal risk open | $560.00 |

**The worst bar by position count is the same bar.** It falls in fold 8 test and
fold 9 train, which overlap there.

Ranked on notional rather than count deliberately: required leverage is what a
margin call is denominated in, and two small positions are not worse than one
large one. The count at that bar is reported alongside so both readings are
visible.

### 7.6 Book-level occupancy per fold

| fold | period | bars | positions | conc max | P99 | P95 | P90 | median | mean | **lev max** | lev P95 | **lev median** | occupied | one-sided |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | train | 4,392 | 1,928 | 22 | 19 | 16 | 14 | 9 | 8.98 | **8.36×** | 5.70× | **2.92×** | 99.80% | 23.02% |
| 1 | test | 2,208 | 884 | 21 | 16 | 14 | 12 | 8 | 8.13 | **10.54×** | 7.31× | **3.58×** | 99.14% | 25.17% |
| 2 | train | 4,416 | 1,851 | 22 | 18 | 15 | 13 | 8 | 8.55 | **10.54×** | 6.50× | **3.27×** | 99.77% | 23.08% |
| 2 | test | 2,160 | 885 | 23 | 19 | 16 | 13 | 8 | 8.40 | **12.84×** | 7.61× | **3.37×** | 99.35% | 23.49% |
| 3 | train | 4,368 | 1,769 | 23 | 18 | 15 | 13 | 8 | 8.27 | **12.84×** | 7.41× | **3.47×** | 99.27% | 24.17% |
| 3 | test | 2,184 | 843 | 18 | 16 | 13 | 12 | 8 | 7.89 | **10.34×** | 6.96× | **4.02×** | 99.73% | 20.02% |
| 4 | train | 4,344 | 1,728 | 23 | 18 | 14 | 12 | 8 | 8.15 | **12.84×** | 7.22× | **3.62×** | 99.61% | 21.63% |
| 4 | test | 2,208 | 906 | 20 | 17 | 15 | 13 | 8 | 8.39 | **11.06×** | 7.94× | **4.14×** | 99.28% | 20.26% |
| 5 | train | 4,392 | 1,749 | 20 | 17 | 14 | 12 | 8 | 8.14 | **11.06×** | 7.52× | **4.08×** | 99.61% | 20.07% |
| 5 | test | 2,208 | 977 | 20 | 18 | 15 | 14 | 9 | 9.11 | **10.74×** | 7.47× | **4.02×** | 99.73% | 15.49% |
| 6 | train | 4,416 | 1,883 | 20 | 17 | 15 | 14 | 9 | 8.78 | **11.06×** | 7.76× | **4.09×** | 99.57% | 17.74% |
| 6 | test | 2,184 | 981 | 25 | 20 | 16 | 14 | 9 | 9.20 | **10.10×** | 6.64× | **3.54×** | 99.91% | 20.26% |
| 7 | train | 4,392 | 1,958 | 25 | 18 | 15 | 14 | 9 | 9.18 | **10.74×** | 7.10× | **3.80×** | 99.86% | 17.35% |
| 7 | test | 2,184 | 981 | 20 | 18 | 15 | 14 | 9 | 9.23 | **10.93×** | 7.10× | **3.92×** | 99.68% | 18.79% |
| 8 | train | 4,368 | 1,962 | 25 | 19 | 15 | 14 | 9 | 9.24 | **10.93×** | 6.79× | **3.78×** | 99.84% | 19.56% |
| 8 | test | 2,208 | 1,075 | **28** | 22 | 17 | 15 | 9 | 9.92 | **13.52×** | 8.04× | **4.08×** | 99.86% | 18.87% |
| 9 | train | 4,392 | 2,056 | **28** | 20 | 16 | 15 | 9 | 9.60 | **13.52×** | 7.63× | **4.01×** | 99.84% | 18.88% |
| 9 | test | 2,208 | 1,035 | 22 | 19 | 16 | 14 | 9 | 9.52 | **11.23×** | 7.50× | **3.80×** | 99.95% | 16.99% |

**Book notional per fold**, for the record:

| fold | period | max | P99 | P95 | P90 | median | mean | risk max |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| 1 | train | 16,715 | 14,074 | 11,394 | 9,952 | 5,841 | 6,085 | 440 |
| 1 | test | 21,082 | 17,367 | 14,628 | 12,571 | 7,149 | 7,558 | 420 |
| 2 | train | 21,082 | 16,257 | 12,997 | 11,119 | 6,542 | 6,907 | 440 |
| 2 | test | 25,677 | 18,614 | 15,226 | 12,759 | 6,731 | 7,368 | 460 |
| 3 | train | 25,677 | 18,407 | 14,822 | 12,699 | 6,943 | 7,474 | 460 |
| 3 | test | 20,675 | 16,538 | 13,911 | 12,792 | 8,038 | 8,178 | 360 |
| 4 | train | 25,677 | 18,459 | 14,431 | 12,792 | 7,247 | 7,786 | 460 |
| 4 | test | 22,125 | 18,950 | 15,871 | 14,260 | 8,283 | 8,912 | 400 |
| 5 | train | 22,125 | 18,861 | 15,040 | 13,598 | 8,168 | 8,550 | 400 |
| 5 | test | 21,481 | 17,639 | 14,942 | 13,293 | 8,034 | 8,241 | 400 |
| 6 | train | 22,125 | 18,861 | 15,513 | 13,882 | 8,187 | 8,612 | 400 |
| 6 | test | 20,202 | 15,323 | 13,287 | 12,353 | 7,074 | 7,501 | 500 |
| 7 | train | 21,481 | 17,265 | 14,197 | 12,747 | 7,604 | 7,895 | 500 |
| 7 | test | 21,865 | 16,907 | 14,199 | 12,678 | 7,837 | 8,083 | 400 |
| 8 | train | 21,865 | 16,670 | 13,577 | 12,571 | 7,568 | 7,815 | 500 |
| 8 | test | **27,045** | 21,054 | 16,086 | 14,506 | 8,155 | 8,720 | **560** |
| 9 | train | **27,045** | 19,138 | 15,261 | 13,489 | 8,024 | 8,428 | **560** |
| 9 | test | 22,455 | 18,864 | 15,003 | 13,214 | 7,607 | 8,191 | 440 |

**THE RESULT IS STABLE ACROSS FOLDS AND IT IS NOT A LATE-WINDOW ARTEFACT.**
Median required leverage is between **2.92× and 4.14×** in all eighteen fold
periods; the maximum is between **8.36× and 13.52×**; occupancy is above 99.1%
everywhere. **There is no fold in which the uncapped book is comfortable.** The
worst fold periods are the two that share 2024-07-15, and the mildest is fold 1
train — the earliest — so the trend across the window is mildly upward and
entirely secondary to the level.

### 7.7 Per-symbol occupancy per fold

Concurrency and the signal-into-open-book fraction, per symbol per fold period:

| symbol | period | F1 | F2 | F3 | F4 | F5 | F6 | F7 | F8 | F9 |
|---|---|---|---|---|---|---|---|---|---|---|
| BTCUSDT | train max / mean | 9 / 2.82 | 9 / 2.76 | 11 / 2.79 | 11 / 2.72 | 10 / 2.75 | 10 / 2.90 | 12 / 3.01 | 12 / 3.06 | 12 / 3.18 |
| BTCUSDT | test max / mean | 9 / 2.75 | 11 / 2.84 | 9 / 2.61 | 10 / 2.90 | 9 / 2.87 | 12 / 3.14 | 9 / 2.97 | 12 / 3.37 | 9 / 2.99 |
| ETHUSDT | train max / mean | 9 / 2.87 | 9 / 2.75 | 10 / 2.70 | 10 / 2.69 | 10 / 2.62 | 10 / 2.83 | 10 / 3.03 | 9 / 3.00 | 11 / 3.09 |
| ETHUSDT | test max / mean | 9 / 2.68 | 10 / 2.71 | 10 / 2.66 | 7 / 2.58 | 10 / 3.06 | 9 / 2.99 | 9 / 3.00 | 11 / 3.16 | 9 / 3.07 |
| SOLUSDT | train max / mean | 10 / 3.30 | 10 / 3.03 | 9 / 2.78 | 10 / 2.74 | 10 / 2.77 | 9 / 3.05 | 9 / 3.14 | 9 / 3.17 | 9 / 3.33 |
| SOLUSDT | test max / mean | 8 / 2.70 | 9 / 2.85 | 10 / 2.62 | 9 / 2.91 | 9 / 3.18 | 9 / 3.08 | 9 / 3.26 | 9 / 3.38 | 9 / 3.46 |

| symbol | period | F1 | F2 | F3 | F4 | F5 | F6 | F7 | F8 | F9 |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| BTCUSDT | train, into open | 96.4% | 95.2% | 95.0% | 94.8% | 94.6% | 95.6% | 95.9% | 96.3% | 96.2% |
| BTCUSDT | test, into open | 94.0% | 96.0% | 93.2% | 95.8% | 95.1% | 96.4% | 95.9% | 96.2% | 96.0% |
| ETHUSDT | train, into open | 95.6% | 93.6% | 93.3% | 93.4% | 93.4% | 95.2% | 95.7% | 95.8% | 96.2% |
| ETHUSDT | test, into open | 92.4% | 93.8% | 92.6% | 93.9% | 96.1% | 95.0% | 96.2% | 95.9% | 95.8% |
| SOLUSDT | train, into open | 97.6% | 96.0% | 95.4% | 96.2% | 95.3% | 95.7% | 96.6% | 96.0% | 96.2% |
| SOLUSDT | test, into open | 94.2% | 96.3% | 96.1% | 94.3% | 96.8% | 96.0% | 95.7% | 96.7% | 97.9% |

**The into-open fraction never falls below 92.4% in any of the fifty-four
cells.** It is the most stable figure in the report.

**Fold-scope convention:** a fold's figures use the positions whose **signal
bar** falls inside that fold period, measured on that period's own grid. A
position opened in the last hours of a period has its tail truncated at the
period boundary — at most 24 bars of a ~4,300-bar training period.

---

## 8. EVERY FIGURE ABOVE IS AN UPPER BOUND — all three reasons

> **THE OCCUPANCY, NOTIONAL AND LEVERAGE FIGURES IN THIS REPORT ARE UPPER
> BOUNDS.** Three independent reasons, none of which cancels the others, and all
> three point the same way.

**1. THE MAX-HOLD ASSUMPTION.** No stop, target or exit of any kind is
evaluated. Every position runs the full 17–24 hours. A real position that stops
out or reaches its target frees its slot **sooner, never later**, so realised
concurrency is at most what is measured here. **How much sooner is unknown and
is unknowable at this stage** — it is a function of stop and target hit rates,
which are firewalled until the validation design is committed. This is the
largest of the three effects and it is not quantified.

**2. UNQUANTISED SIZING.** `position_size` returns a raw fractional quantity and
the engine applies no lot rounding (closing record §6.1). **Flooring to
`qty_step` reduces every quantity**, so every notional is at or above what an
exchange would accept. Measured at **0.21% / 1.26% / 0.67%** of pooled notional
(BTC / ETH / SOL) in §2.2 — real, but small enough that it changes no conclusion
here.

**3. UNCAPPED CONCURRENCY.** Every signal opens an additional position,
including on a symbol that already carries one. **No cap of any kind is
applied.** This is the assumption the step was asked to measure under, and it is
the one 5.2 exists to replace.

**The direction is the correct one for a risk measurement.** A bound that can
only be loosened by later work is usable now; one that could move either way is
not.

**One effect points the other way and is recorded for completeness.** The
engine's charged round-trip cost slightly exceeds `0.11 × s` at a floor-bound
stop (§10.2), which makes the sizing denominator larger and every quantity
marginally **smaller**. Against a notional sized at exactly `0.11 × s` it is
worth **0.2% on BTC/ETH and 3.2% on SOL**, and it does not offset the three
effects above.

---

## 9. VERIFICATION

### 9.1 SYNTHETIC POSITIVE CONTROL — the occupancy timeline, hand-computed

**"We found nothing" is indistinguishable from "the detector is broken" without
one** (closing record §5.4), and an all-zero occupancy timeline is exactly what
both a correct empty book and a broken interval calculation look like.

**THE CONSTRUCTION.** 200 flat bars starting at 2022-01-01T00:00:00Z, with long
sweep bars planted at bar indices **120, 124 and 128**. Lows descend
**95 / 94 / 93** because each sweep enters the next ten bars' channel, so a
later sweep must break a channel the earlier one already lowered. Highs stay at
the flat 101.0, which is not *strictly* above the prior-10 maximum of 101.0, so
**no short signal exists anywhere in the series** and the population is exactly
the three placed sweeps.

**THE HAND ARITHMETIC.** Bar index `i` opens at hour `i mod 24`, entry is at its
close, and `hold = 24 − (entry_hour mod 8)`:

| index | opens | entry | hold | open on bars |
|---:|---|---|---:|---|
| 120 | 00:00 | 01:00 | **23h** | 121 … 143 |
| 124 | 04:00 | 05:00 | **19h** | 125 … 143 |
| 128 | 08:00 | 09:00 | **23h** | 129 … 151 |

giving the concurrency timeline

    bars 114..120 -> 0     121..124 -> 1     125..128 -> 2
    bars 129..143 -> 3     144..151 -> 1     152..199 -> 0

**FIFTEEN BARS CARRY THREE SIMULTANEOUS POSITIONS ON ONE SYMBOL**, which is the
overlap case the control was required to contain. **Asserted element by element
against that array, twice** — once built from the three intervals and once
written out as literal runs — and the occupied-bar total is asserted to equal
`23 + 19 + 23 = 65`. The notional timeline is asserted against the same
intervals weighted by each position's notional.

**PASSES.**

A further test walks all 24 entry hours and asserts, for each, that the occupied
bar count equals the hold in hours, that the position is **not** open on its own
signal bar, and that it **is** open on its exit bar and not after it.

### 9.2 SYNTHETIC NEGATIVE CONTROL

A 300-bar flat series has `low == lower` and `high == upper` on every bar, and
all four comparisons are strict, so **nothing can fire**. Asserted: zero long
sweeps, zero short sweeps, zero positions, and an **all-zero occupancy timeline
over all 186 analysed bars** — count and notional both. The histogram is
asserted to be the single row `{level: 0, bars: 186, fraction: 1.0}`.

**If the strictness ever loosened, this series would fire on every bar rather
than none**, which is why the flat series is the right negative control here.

**PASSES.**

### 9.3 FUNDING SETTLEMENT LOGIC

| assertion | result |
|---|---|
| the first settlement after any instant is at 00:00, 08:00 or 16:00 UTC, and is **strictly** after | **passes**, all 24 hours × 3 days |
| an instant **exactly on** a settlement does not count that settlement | **passes** |
| entry immediately **after** a settlement (entry instant = the settlement itself) → **24h** exactly; one hour later → 23h | **passes** |
| entry immediately **before** a settlement (07:00, one hour before 08:00) → **17h** | **passes** |
| every hold on the hourly grid lies in **[16h, 24h]**, and the attainable set is exactly {17,…,24} | **passes** |
| the exit bar **closes on** the third settlement | **passes** |
| **n is a settlement index, not a bar count**: n = 2 → 12h, n = 3 → 20h, n = 4 → 28h at a fixed entry, and both n = 2 and n = 4 are **refused** by the band guard | **passes** |
| **every hold in the real measurement**, all 11,384 positions, lies in [16h, 24h] | **passes** |

`assert_hold_admissible` raises on any hold outside the band and is asserted to
raise in both directions. **A settlement off-by-one produces holds of 12 or 28
hours — plausible numbers that no occupancy figure would look wrong for — so
this is the check that makes them loud.**

### 9.4 PLANTED MUTATION — the holdout seal

**THE MUTATION.** In `src/timeframe/resample.py`, both halves of the filter
widened at once:

    WINDOW_END   = dt.date(2024, 12, 31)      ->  dt.date(2025, 6, 30)
    ALLOWED_YEARS = (2022, 2023, 2024)        ->  (2022, 2023, 2024, 2025)

**WHY IT WOULD OTHERWISE PASS UNNOTICED.** The 1m layer physically holds the
sealed years on disk; the seal is not maintained by absence. A widened filter
raises nothing, and every occupancy figure would simply become better-sampled
while the holdout was spent without anyone deciding to spend it.

**RESULT: the mutation was planted, confirmed failing, and reverted.**

| scope | outcome under the mutation |
|---|---|
| `tests/test_exposure_profile.py` | **19 tests fail** (8 failures + 11 errors) |
| whole suite | **33 failures + 11 errors** |
| first assertion to fire | `assert rs.WINDOW_END == dt.date(2024, 12, 31)` → `datetime.date(2025, 6, 30) == datetime.date(2024, 12, 31)` |

`git diff --stat src/timeframe/resample.py` is **empty** after the revert.

**The seal has three layers on this module's path**, each asserted
independently:

1. **The module defines no window constant of its own.** A test walks the AST
   and asserts `WINDOW_START`, `WINDOW_END` and `ALLOWED_YEARS` are not assigned
   anywhere in it, and that the sealed year does not appear in its source text.
2. **`positions()` passes its output through `resample.assert_sealed`.** A
   position is opened on its **signal bar**, so sealing the position table seals
   the entry. A test shifts a synthetic frame so the signal bar lands exactly on
   the seal and asserts `HoldoutBreach` is raised.
3. **Fold windows are checked against the seal.** All eighteen periods are
   asserted to end before it, and the `holdout` entry in `folds.json` is
   asserted never to be walked.

**Exit timestamps are calendar values and are deliberately outside the seal's
scope** — they read no data. A test asserts that late-window exits **do** fall
past the seal as timestamps (otherwise it would be asserting nothing) while the
occupancy timeline's last grid point is **2024-12-31T23:00:00Z**, strictly
before it.

### 9.5 THE FIREWALL GUARD

**Same form as reports 19, 20 and 21.** Those modules do not share a guard
helper — each test file carries its own copy of the same nine-name list — so the
form is reproduced rather than imported, and the list is identical:

    expectancy, win_rate, winrate, profit_factor, sharpe, net_pnl,
    r_multiple, equity, pnl

A test walks the module's AST and collects every `Name`, `Attribute`, `arg`,
function name, class name and **non-docstring string literal**, then refuses any
of those nine as a substring. Docstrings are excluded because they **state** the
prohibition, so a raw grep would fire on the rule rather than on a violation of
it.

**Additional guards on the same module:**

- **Import graph.** `simulate`, `src.engine.simulate`, `src.sweep`,
  `src.folds.run` and `src.engine.run` may not be imported. `costs` **is**
  imported, deliberately and narrowly.
- **The engine surface is enumerated.** A test collects every attribute accessed
  on `costs` and asserts the set is exactly `{position_size, CostConfig}`.
  **`solve_target`, `stop_geometry`, `stop_fill_price`, `solve_r_level`,
  `trade_pnl` and `summarize` appear nowhere in the module's identifiers.**
- **No forward shift.** `.shift(-` appears nowhere.
- **No open price.** `open_synth` is neither read nor bound, and the loaded
  frames are asserted to carry no `open` column.

**`equity` is on the banned list, and the account size is a legitimate input
here.** It is therefore transcribed as `CAPITAL_USD = 2000.0` and pinned against
the engine's own account constant by a test, so the module never spells the
banned name and the transcription cannot drift.

### 9.6 THE DONCHIAN EXCLUSION GUARD — reused, not reproduced

**Report 21's guard covers this module because this module computes no channel
of its own.** The signal frame comes from `sweep_population.analysis_frame`,
which calls the engine's `signals.donchian_prior`
(`rolling(N).max().shift(1)`). `test_sweep_population.py`'s
`test_donchian_window_excludes_the_current_bar` and
`test_including_the_current_bar_would_empty_the_population` are therefore guards
on this module's trigger too.

**Asserted here rather than assumed:** a test checks the module contains no
`.rolling(` call and no channel construction of its own, and separately asserts
the window contents on the frame this module actually consumes —
`lower[120] == min(low[110:120])` and **not** `min(low[111:121])`.

**No refactor was required. `src/analysis/sweep_population.py` is imported
as-is and no line of it was changed.**

### 9.7 TWO-SIDED BAR EXCLUSION

A constructed outside bar — high 105 against a prior-10 maximum of 101, low 95
against a prior-10 minimum of 99, closing at 100 between them — is asserted to
fire **both** masks, and then asserted to open **no position**: the position
table is empty and the occupancy timeline is zero everywhere. `signal_counts`
reports it as one signal bar, one two-sided bar and **zero positions**.

On the real population, `n_positions == n_signal_bars − n_two_sided` and
`n_positions == n_long + n_short` are asserted in all eighteen fold periods on
all three symbols.

### 9.8 The remaining tests

- **Frozen inputs** are asserted to be *the same objects* as report 21's, not
  copies with the same value — timeframe, Donchian period, ATR period, stop
  multiplier and floor.
- **`CONCURRENCY_CAP is None`** is asserted, and the property is asserted
  behaviourally: three positions on one symbol must be allowed to coexist.
- **The three construction-only config parameters** are varied and the position
  table asserted bit-identical.
- **`position_size` is called**: the quantity is asserted equal to a direct call
  and to hand arithmetic on the documented denominator, and asserted **not**
  equal to either the naive or the cost-tolerance form.
- **Floor binding** is asserted equal to `sweep_population.floor_binding_fraction`
  on the same input, exactly, on 5,000 random draws.
- **Leverage and nominal risk** are asserted to be `notional / 2000` and
  `positions × 20` in the pooled scope and all eighteen fold scopes.
- **Book occupancy** is asserted to be the sum of the three symbol timelines,
  and the worst bar's per-symbol breakdown asserted to reconcile to its totals.
- **Every histogram** is asserted to cover every level from 0 to the maximum,
  to sum to the bar count, and to have fractions summing to 1.
- **The grid** is asserted to equal the bar series exactly, and the window edge
  clipping asserted to be counted and bounded.
- **570 / 281** are asserted to be reproduced by the per-symbol reading and
  **not** by the pooled one; **86 / 59 / 32** asserted to be reproduced by the
  overlapping-train-window sum and **not** by the distinct-bar count.

### 9.9 FULL SUITE

| | tests |
|---|---:|
| baseline at the Point 1 closing commit `5e4d970` | **698 passing** |
| new in `tests/test_exposure_profile.py` | **+47** |
| **total** | **745 passing / 745** |

---

## 10. WHAT CONTRADICTS A FROZEN DOCUMENT

**Three items. None is a contradiction of a frozen parameter; two are
contradictions of a frozen CONCLUSION, and one is a cost fact that the frozen
documents do not state.**

### 10.1 THE CLOSING RECORD §3.1's LEVERAGE CONCLUSION DOES NOT SURVIVE

> *"Capital affects only leverage and lot granularity, and neither binds at
> present values (leverage term $20/($2,000 × 3) = 0.333%, far inside the 1.50%
> floor)."* — closing record §3.1

**The arithmetic is correct and the conclusion is not.** `leverage_term()` is
the minimum stop width at which **one** position fits inside 3× leverage, and at
0.333% it is indeed far inside the 1.50% floor. **But the quantity that binds is
not one position's stop width; it is the sum over positions open at the same
instant.** Under the frozen max hold, uncapped:

- one floor-bound position requires **0.599×**, comfortably inside the cap;
- **six** simultaneous floor-bound positions breach it;
- the median book carries **nine**, at **3.59×**;
- **63.93% of bars require more than 3×.**

**This is the eighth instance of the closing record §4's recurring defect class**
— *"a numerical criterion written from a mental model of a quantity rather than
from its implementation or its achievable range"* — and it is the same shape as
error (7): **the population was mis-named.** `leverage_term` is a per-position
quantity and it was read as an account-level one. The closing record's own
transferable lesson, *"name the population in the same sentence as the number"*,
is exactly what would have caught it.

**It is stated as a contradiction of a conclusion, not of a parameter.** No
frozen parameter said anything about aggregate leverage, because no frozen
document measured it. **Nothing is changed here.** Whether `max_leverage = 3.0`
is real — the source calls it *"NOT a probed exchange constraint — an unmeasured
placeholder"* — and what the concurrency cap should be are 5.2's decisions.

### 10.2 THE CHARGED ROUND-TRIP COST EXCEEDS `COST_TOLERANCE_R` AT THE FLOOR

Thesis §5.1 states the 1.50% floor is the level below which *"a stop tighter
than it cannot carry the cost budget"*, derived from `COST_TOLERANCE_R = 0.11`.
**At a stop exactly on the floor, the cost the engine actually charges is
already above 0.11 on the `c / s` reading, and above it on SOLUSDT under either
reading.**

Arithmetic on §2's config table, at `s = 1.50%`, per unit of entry price
(`c = entry × f + stop × f + stop × h`):

| symbol | direction | `c` | **`c / s`** | **`c / (s + c)`** |
|---|---|---:|---:|---:|
| BTCUSDT / ETHUSDT | long | 0.0016835 | **0.11223R** | 0.10091R |
| BTCUSDT / ETHUSDT | short | 0.0017165 | **0.11443R** | 0.10268R |
| SOLUSDT | long | 0.0021760 | **0.14507R** | **0.12669R** |
| SOLUSDT | short | 0.0022240 | **0.14827R** | **0.12912R** |

**Amendment 1 §7 establishes that under cost-inclusive sizing the realised share
of the risk unit is `c / (s + c)`, not `c / s`.** On that reading BTCUSDT and
ETHUSDT sit at **0.101R**, inside the budget. **SOLUSDT sits at 0.127–0.129R,
outside it by 15–17%**, on every floor-bound trade.

**The source is the stop haircut**, which report 18's derivation of the 1.50%
floor did not carry: at `s = 1.50%` and all-taker, report 18's own table gives
tolerable slippage of **2.25 bps per side**, or 4.5 bps for the round trip.
The engine charges **5 bps** on the stop leg for BTC and ETH and **10 bps** for
SOL, with entry slippage at 0. `costs.py` calls those figures *"Placeholders,
per spec"* — **they are not measurements**, and the engine's own derived floor
`stop_min_pct` uses `n_cost = 6.0` (a 1/6 = 0.1667 budget), not 0.11, which is
why the engine never noticed the gap.

**FLAGGED, NOT RESOLVED, AND NOT ACTED ON.** It changes no figure in this
report except in the conservative direction (a larger denominator means a
smaller quantity and a smaller notional). It belongs with the `COST_TOLERANCE_R`
justification item that amendment 1 §7 and closing record §6.2 already route to
the validation design, and it should be settled there — **before any performance
figure is inspected**, for the same reason that item is.

### 10.3 A BOUNDARY QUESTION IN THE TIME-EXIT RULE, RECORDED

Thesis §5.3 derives `n = 3` from a funding budget in which `n` is *"the number
of settlements crossed"*, and states the rule as closing *"at the close of the
bar preceding the third funding settlement after entry"*.

**Under the implementation here the exit bar closes AT the third settlement**
(§5.1), so whether the position is present for that settlement is a
venue-boundary question: the bar's closing trade occurs strictly before the
boundary instant, so the position crosses **two** settlements, not three. Under
the alternative reading — exiting one bar earlier — it also crosses two.

**Either way the position crosses at most the three settlements the budget
allows, so the funding derivation is respected and no kill condition is
affected.** The ambiguity is recorded because a future implementation could
resolve it the other way and would then differ from this report's occupancy by
one bar per position — about 4.5% of total occupancy. **No change is proposed.**

---

## 11. WHAT THIS HANDS TO 5.2 AND 5.3 — no decision is made here

**Five numbers, and what each one constrains.**

1. **The uncapped book requires a median of 3.59× and a maximum of 13.52×
   leverage, and exceeds 3× on 63.93% of bars.** A concurrency cap is not an
   optimisation; without one the strategy as frozen is not carryable at $2,000
   under the engine's own configured cap. **The cap is 5.2's to set.**

2. **95.3–96.4% of signals arrive while that symbol already has a position
   open.** Any per-symbol cap acts on essentially every signal, not on a tail.
   A "one position per symbol" rule would discard nineteen signals in twenty and
   would change the traded population from ~11,384 to a few hundred — which
   would also invalidate report 21's per-fold count adequacy, since 570 signals
   per symbol per fold is not 570 *positions* under a cap.

3. **20.51% of occupied bars carry a one-sided book**, at a median concurrency
   of nine across three correlated majors. Whether that is acceptable is a
   correlation question this report does not touch.

4. **Per-position notional is bounded above by `20 / (0.0150 + c)` ≈ $1,199**,
   and the BTC median sits at 95% of that ceiling because the floor binds on
   46% of its signals. **The floor and the leverage question are the same
   question**: the floor makes the stop wider, which makes the position larger,
   which is what fills the account.

5. **Floor binding per fold ranges from 0.0% to 93.9%.** 5.3's sizing fix and
   kill condition (d)'s stratification both land on a population whose
   composition swings by more than 90 points between folds.

**Everything here is an upper bound (§8), and the largest of the three
loosening effects — that positions do not in fact all run the full max hold — is
firewalled and cannot be quantified until the validation design exists.** A cap
chosen against these numbers will be conservative by an unknown margin, and
choosing it is 5.2's decision, taken with that stated.

---

**Files.** `src/analysis/exposure_profile.py` · `tests/test_exposure_profile.py`
· this report.
**Not modified:** `src/engine/costs.py`, the rest of the engine,
`src/analysis/sweep_population.py`, `src/costs/`, `src/timeframe/`,
`src/folds/`, and every frozen document numbered 22, 22a and 23.
**Holdout:** sealed, unspent, re-verified by planted mutation.
**Firewall:** armed, AST-guarded, no trade simulated, no outcome computed.
