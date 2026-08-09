# REPORT 20 — THE 1R.5 REVERSAL-BREAKOUT POPULATION AT 1h

**Point 1, continued.** Point 4's hypothesis was killed
(`docs/handoff/16_point_4_closing.md`) and Point 1 reopened. The timeframe was
selected as **1h** by the rule frozen at `96c96cf` (report 19, `74e3ca9`). This
step asks whether the 1R.5 "reversal breakout" population — a Donchian breakout
firing while RSI is depressed — exists at that timeframe, and whether its
absence at 15m was a property of the indicators or a property of 15m.

**The performance firewall is re-armed.** No expectancy, win rate, profit
factor, Sharpe, equity curve, `r_multiple` or `net_pnl` aggregate is computed,
referenced or estimated anywhere in this step. Signal counts, pass rates and
indicator distributions are explicitly permitted pre-firewall quantities. **No
trade is simulated** — no entry is taken, no exit is computed, no position is
sized. `src/engine/simulate` is not imported and a test asserts it.

**Window read: 2022-01-01 to 2024-12-31 only. THE HOLDOUT IS SEALED** —
2025-01-01 onward has never been read, not one bar. The window is **inherited
whole** from `src/timeframe/resample.py`; this step defines no window constant
of its own, and a test asserts that it defines none. Section 7.1 reports the
planted mutation that proves the seal holds through the new code path.

**No open price is used anywhere.** `open_synth` is dropped at the load
boundary; RSI needs close, Donchian needs high and low.

**Nothing was tuned.** Donchian 20 and RSI 14 are Point 4's periods,
transcribed because this is a test **of that operationalisation**. They are not
swept. The negligibility threshold was fixed before the measurement — §5.

---

## 1. WHAT WAS ASKED, AND WHAT WAS AT STAKE

Point 1R.5 removed `rsi_upper` on guard-rail grounds and left `rsi_lower` as a
filter intended to reject breakouts firing without momentum confirmation. Point
3's structural pass (report 07 §5.7) found **zero rejections in 11,711 breakout
bars** at 15m over 2022–23, with a **minimum RSI of 54.18** on long breakout
bars. The filter was inert because the population it targeted was empty, and the
closing record therefore classified the reversal-breakout hypothesis as
**UNEXERCISED, NOT REFUTED**.

The claim under test is that this emptiness is **structural**, not a fact about
15m:

> A Donchian-N breakout means price just made an N-bar high. RSI(14) measures
> recent gains against recent losses. Making an N-bar high entails recent gains
> having dominated. Both indicators are defined in **bar units**, so the
> relationship should be scale-invariant and the population equally empty at 1h.

If the claim holds, 1R.5's operationalisation is closed for the record. If it
fails — if a meaningful low-RSI breakout population exists at 1h — the
hypothesis is genuinely exercisable and that is a live finding.

---

## 2. CONSTRUCTION

### 2.1 Bars

Built through `src/timeframe/resample.py`, unchanged, the same path report 19
used. 15m is the existing 15m layer used directly; 1h is four 15m buckets.
**Incomplete buckets are dropped** by that module's existing logic, not
reimplemented here.

**Nothing was dropped.** `buckets_dropped == 0` for every symbol at both
timeframes — 26,304 1h bars and 105,216 15m bars per symbol over 1,096 days,
exactly `1096 × 86,400,000 / period_ms`. No measurement here rests on a thinned
sample. This reproduces report 19 §2.1.

### 2.2 RSI(14), Wilder's smoothing, on close

Seeded with the **simple mean of the first 14 gains and the first 14 losses**,
then

    avg_gain_i = (avg_gain_{i-1} × 13 + gain_i) / 14
    avg_loss_i = (avg_loss_{i-1} × 13 + loss_i) / 14
    RSI_i      = 100 − 100 / (1 + avg_gain_i / avg_loss_i)

Implemented directly rather than as an EWM `alpha = 1/14`, which seeds
differently and would not reproduce a hand-computed value — the same
construction and the same reason as report 19's ATR. `avg_loss == 0` returns
**RSI 100** by definition, which is the branch the engine's `rsi_wilder` takes;
followed rather than improved on, because a different convention on a boundary
case is how two implementations of one indicator stop being comparable. **That
branch is never reached: zero bars in the window carry RSI exactly 100.**

**Warm-up discarded: 114 bars**, the same arithmetic as report 19's ATR warm-up
— **1** (the first bar has no previous close, so no delta at all) + **13**
(deltas before the 14-delta seed window completes) + **100** (RSI values after
the seed, discarded for stabilisation). The seed's residual weight after 100
further bars is `(13/14)^100 = 6.0 × 10⁻⁴`. Donchian's own 20-bar warm-up is
strictly inside this and never binds.

The resulting bar counts — **26,190 at 1h and 105,102 at 15m** — are identical
to report 19's post-ATR-warm-up counts, so the two reports describe the same
bars. A test pins this.

**Convention reconciliation.** The engine's `rsi_wilder` is the EWM form. After
the 114-bar discard the largest disagreement between the two seedings anywhere
in the window is **4.3 × 10⁻³ RSI points** (BTC 1h; ETH 1h is 7.6 × 10⁻⁴, all
six cells ≤ 4.3 × 10⁻³). Every comparison in this report against Point 3's
figures is therefore sound at the resolution reported.

### 2.3 Donchian-20 breakouts — THE EXCLUSION CONVENTION

    upper[T] = max( high[T−20] … high[T−1] )      the current bar's own high
    lower[T] = min( low[T−20]  … low[T−1]  )      and low are NOT in its window

    LONG  breakout at T :  close[T] >  upper[T]
    SHORT breakout at T :  close[T] <  lower[T]

The channel is `src/engine/signals.py::donchian_prior`, **reused, not
reimplemented** — this is a test of Point 4's operationalisation, so it must use
the channel Point 4 used. It is `rolling(20).max().shift(1)`, so the first
defined value is at index 20, not 19.

**An off-by-one here does not raise, it redefines the population.** Admitting
the current bar makes `close > max(high)` satisfiable only on a bar closing
exactly at its high — the population all but vanishes, and *a vanishing
population is this report's headline result*. The two failure modes are
indistinguishable in the output table. Section 7.3 reports the guard.

### 2.4 The population is DELIBERATELY BROADER than Point 3's

Point 3 measured the engine's **trend AND Donchian** conditions together
(EMA20 > EMA50 *and* close above the channel). This measures the **Donchian
condition alone**. No trend, RVOL, vwap or RSI term enters the population
definition; conditioning the population on RSI would be assuming the answer.

Dropping the trend filter can only **admit** bars, never remove them — and the
bars it admits are exactly the ones most likely to carry a depressed RSI:
breakouts against the prevailing trend. **The broader population is the
conservative choice for a search that expects to find nothing.** §6.2 narrows it
back to Point 3's own definition so the two can be compared directly.

---

## 3. PART A — BREAKOUT COUNTS

Per symbol, per timeframe, per direction, over 2022-01-01 → 2024-12-31, on bars
surviving the 114-bar warm-up.

| timeframe | symbol | bars analysed | **LONG breakouts** | **SHORT breakouts** | long **(% of bars)** | short **(% of bars)** |
|---|---|---:|---:|---:|---:|---:|
| 1h | BTCUSDT | 26,190 | 1,039 | 893 | 3.9672 | 3.4097 |
| 1h | ETHUSDT | 26,190 | 1,083 | 936 | 4.1352 | 3.5739 |
| 1h | SOLUSDT | 26,190 | 1,206 | 1,075 | 4.6048 | 4.1046 |
| 15m | BTCUSDT | 105,102 | 4,496 | 3,960 | 4.2777 | 3.7678 |
| 15m | ETHUSDT | 105,102 | 4,518 | 4,073 | 4.2987 | 3.8753 |
| 15m | SOLUSDT | 105,102 | 5,166 | 4,727 | 4.9152 | 4.4975 |

**The breakout RATE is nearly scale-invariant** — 3.97–4.60% of bars at 1h
against 4.28–4.92% at 15m, long; 3.41–4.10% against 3.77–4.50%, short. That is
the first evidence for the bar-units argument and it is independent of RSI: a
20-bar channel breaks at roughly the same per-bar frequency regardless of how
long a bar is. Coarsening the timeframe by 4× cuts the bar count by 4× and the
breakout count by very nearly the same factor.

**The population is not vacuous** — 893 to 5,166 bars per cell. A test asserts
breakouts exist and that they are a few percent of bars, not a few tenths and
not a third.

---

## 4. PART B — THE RSI DISTRIBUTION ON BREAKOUT BARS

### 4.1 LONG breakout bars — how far RSI descends

**The question for longs is the LEFT tail.** All cells are RSI points.

| timeframe | symbol | **MIN** | P1 | P5 | P10 | P25 | MEDIAN | P75 | P90 | MAX | bars |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1h | BTCUSDT | **50.85** | 54.90 | 58.03 | 60.33 | 64.03 | 69.65 | 76.11 | 81.15 | 91.51 | 1,039 |
| 1h | ETHUSDT | **52.98** | 55.67 | 58.98 | 60.66 | 64.01 | 69.38 | 74.21 | 78.76 | 92.64 | 1,083 |
| 1h | SOLUSDT | **49.48** | 55.31 | 58.38 | 60.28 | 63.70 | 68.17 | 72.86 | 77.67 | 91.53 | 1,206 |
| 15m | BTCUSDT | **44.42** | 54.07 | 57.57 | 59.12 | 62.51 | 67.13 | 73.24 | 79.35 | 94.67 | 4,496 |
| 15m | ETHUSDT | **39.80** | 53.36 | 57.35 | 59.18 | 62.52 | 67.20 | 72.90 | 78.47 | 95.54 | 4,518 |
| 15m | SOLUSDT | **46.79** | 54.44 | 57.52 | 59.31 | 62.57 | 66.82 | 71.88 | 76.90 | 96.08 | 5,166 |

**The P1 does not reach 50 in any cell, at either timeframe.** The lowest first
percentile anywhere in the table is 53.36 (ETH 15m); at 1h the range is
54.90–55.67. The P5 range is 57.35–58.98 across all six cells. **The bottom five
percent of long breakouts sit above 57 RSI everywhere.**

The minimum is a single bar and behaves like one — it is the only column where
1h and 15m visibly differ, and it differs in the direction 4× more bars would
predict: 15m has four times the sample and therefore four times the opportunity
for an outlier.

### 4.2 SHORT breakout bars — how far RSI ascends

**For shorts the mirrored quantity is the relevant one.** A short breakout
firing "without momentum confirmation" is one with an *elevated* RSI, so the
question is the **RIGHT tail** and the operative statistics are the **MAX** and
the upper percentiles, not the minimum. Both tails are reported.

| timeframe | symbol | MIN | P1 | P5 | P10 | P25 | MEDIAN | P75 | P90 | **MAX** | bars |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1h | BTCUSDT | 5.63 | 14.61 | 17.87 | 21.03 | 25.75 | 31.04 | 36.13 | 39.88 | **48.70** | 893 |
| 1h | ETHUSDT | 5.31 | 12.14 | 18.31 | 20.83 | 25.83 | 31.28 | 35.86 | 39.61 | **48.53** | 936 |
| 1h | SOLUSDT | 10.51 | 15.20 | 20.66 | 23.42 | 27.86 | 32.36 | 36.25 | 39.61 | **46.20** | 1,075 |
| 15m | BTCUSDT | 4.33 | 12.58 | 18.74 | 22.22 | 27.55 | 32.98 | 37.33 | 40.75 | **51.22** | 3,960 |
| 15m | ETHUSDT | 3.55 | 12.97 | 18.85 | 21.94 | 27.31 | 32.71 | 37.15 | 40.42 | **55.51** | 4,073 |
| 15m | SOLUSDT | 6.30 | 14.31 | 20.46 | 23.22 | 28.02 | 32.96 | 37.01 | 40.14 | **50.31** | 4,727 |

**At 1h the MAXIMUM RSI on any short breakout bar in three years is 48.70.** Not
one short breakout on any symbol reached 50. The mirror of the long result is
exact: P90 is 39.61–40.75 across all six cells, so the top ten percent of short
breakouts sit below 41.

### 4.3 The all-bars control — the conditioning effect

RSI over **all** analysed bars, breakout and non-breakout alike, same symbols
and timeframes. This is what the breakout condition is doing to the
distribution.

| timeframe | symbol | MIN | P1 | P5 | P10 | P25 | MEDIAN | P75 | P90 | MAX | bars |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1h | BTCUSDT | 5.63 | 22.03 | 29.97 | 34.84 | 42.69 | 50.39 | 57.92 | 66.12 | 91.95 | 26,190 |
| 1h | ETHUSDT | 5.31 | 21.49 | 29.54 | 34.54 | 42.43 | 50.27 | 58.08 | 66.08 | 92.64 | 26,190 |
| 1h | SOLUSDT | 9.80 | 23.61 | 30.86 | 34.85 | 41.92 | 49.72 | 57.77 | 65.40 | 91.53 | 26,190 |
| 15m | BTCUSDT | 4.14 | 22.59 | 31.96 | 36.65 | 43.41 | 50.31 | 57.03 | 64.21 | 94.67 | 105,102 |
| 15m | ETHUSDT | 3.55 | 22.74 | 31.37 | 36.07 | 43.04 | 50.27 | 57.36 | 64.39 | 95.54 | 105,102 |
| 15m | SOLUSDT | 6.30 | 23.74 | 31.79 | 36.02 | 42.74 | 49.97 | 57.29 | 64.17 | 96.08 | 105,102 |

**The unconditional distribution is centred on 50 and symmetric** — medians
49.72 to 50.39 across all six cells, P1 around 22, P90 around 65. Roughly half
of all bars carry RSI below 50, and the low-RSI region is heavily populated: the
P5 of all bars is ~30, against a P5 on long breakout bars of ~58.

**So the emptiness is entirely a conditioning effect, not a scarcity of
low-RSI bars.** There is no shortage of bars below RSI 50 to break out from —
they are about half the sample. The Donchian condition simply never selects one.
That is the shape of an entailment, and it is what distinguishes this result
from "the data did not happen to contain any."

---

## 5. PART C — THE REJECTION-RATE TABLE

**This is a pass-rate measurement and nothing more.** Whether a rejected bar
would have been a good trade is not asked, not computed, and not estimable from
anything in this section. No rejected bar is simulated.

**Strictness convention.** `rsi_lower` passes a bar when `rsi >= threshold` and
therefore **rejects `rsi < threshold`**. The mirrored `rsi_upper` passes
`rsi <= threshold` and **rejects `rsi > threshold`**. The boundary cannot matter
at this resolution — exact equality with an integer threshold on a smoothed
continuous quantity is measure-zero, and **the number of exact ties across all
sixty cells of this table is zero.**

### 5.1 LONG breakouts against candidate `rsi_lower`

| timeframe | symbol | bars | **≥ 40** | **≥ 45** | **≥ 50** | **≥ 55** | **≥ 60** |
|---|---|---:|---:|---:|---:|---:|---:|
| 1h | BTCUSDT | 1,039 | 0 (0.0000%) | 0 (0.0000%) | **0 (0.0000%)** | 12 (1.1550%) | 97 (9.3359%) |
| 1h | ETHUSDT | 1,083 | 0 (0.0000%) | 0 (0.0000%) | **0 (0.0000%)** | 7 (0.6464%) | 86 (7.9409%) |
| 1h | SOLUSDT | 1,206 | 0 (0.0000%) | 0 (0.0000%) | **1 (0.0829%)** | 12 (0.9950%) | 108 (8.9552%) |
| 15m | BTCUSDT | 4,496 | 0 (0.0000%) | 1 (0.0222%) | **11 (0.2447%)** | 71 (1.5792%) | 613 (13.6343%) |
| 15m | ETHUSDT | 4,518 | 1 (0.0221%) | 1 (0.0221%) | **4 (0.0885%)** | 87 (1.9256%) | 601 (13.3023%) |
| 15m | SOLUSDT | 5,166 | 0 (0.0000%) | 0 (0.0000%) | **8 (0.1549%)** | 73 (1.4131%) | 673 (13.0275%) |

Cells are the count of breakout bars the filter **would reject**, and that count
as a percentage of the breakout population.

### 5.2 SHORT breakouts against the mirrored `rsi_upper`

| timeframe | symbol | bars | **≤ 60** | **≤ 55** | **≤ 50** | **≤ 45** | **≤ 40** |
|---|---|---:|---:|---:|---:|---:|---:|
| 1h | BTCUSDT | 893 | 0 (0.0000%) | 0 (0.0000%) | **0 (0.0000%)** | 7 (0.7839%) | 84 (9.4065%) |
| 1h | ETHUSDT | 936 | 0 (0.0000%) | 0 (0.0000%) | **0 (0.0000%)** | 6 (0.6410%) | 80 (8.5470%) |
| 1h | SOLUSDT | 1,075 | 0 (0.0000%) | 0 (0.0000%) | **0 (0.0000%)** | 4 (0.3721%) | 100 (9.3023%) |
| 15m | BTCUSDT | 3,960 | 0 (0.0000%) | 0 (0.0000%) | **2 (0.0505%)** | 53 (1.3384%) | 508 (12.8283%) |
| 15m | ETHUSDT | 4,073 | 0 (0.0000%) | 1 (0.0246%) | **5 (0.1228%)** | 60 (1.4731%) | 472 (11.5885%) |
| 15m | SOLUSDT | 4,727 | 0 (0.0000%) | 0 (0.0000%) | **1 (0.0212%)** | 48 (1.0154%) | 493 (10.4294%) |

### 5.3 What the table says

**At the threshold that matters — 50, the value 1R.5 actually proposed — the
1h rejection rate is 0.0000%, 0.0000% and 0.0829%: one bar in 3,328.** The
short side rejects **nothing at all** at 1h: zero bars in 2,904.

`rsi_lower` only starts doing measurable work at **60**, where it rejects
7.9–9.3% of 1h long breakouts. But a filter at 60 is not the 1R.5 filter. 1R.5's
`rsi_lower` was specified to reject *breakouts firing without momentum
confirmation*; a bound at 60 rejects breakouts that have momentum but not
much of it, which is a different instrument answering a different question, and
adopting it would be choosing the threshold to make the filter non-inert rather
than because 60 was ever the hypothesis. **It is recorded here as a measurement
and is not proposed.**

---

## 6. PART D — THE SCALE-INVARIANCE VERDICT

### 6.1 The negligibility threshold — FIXED BEFORE THE MEASUREMENT

> **NEGLIGIBLE means: fewer than 1% of long breakout bars below RSI 50, on all
> three symbols.**

Written into `src/analysis/rsi_breakout_profile.py` as the named constants
`NEGLIGIBLE_MAX_PCT = 1.0` and `NEGLIGIBLE_RSI_LEVEL = 50.0`, and **fixed before
any figure below was computed**. Read strictly: exactly 1.00% is *not*
negligible. A test pins both constants and §7.2 reports the planted mutation on
the comparison's direction.

### 6.2 The evidence, per symbol

| timeframe | symbol | MIN RSI (long) | **P1** | **P5** | **count < 50** | of | **% < 50** |
|---|---|---:|---:|---:|---:|---:|---:|
| 1h | BTCUSDT | 50.85 | 54.90 | 58.03 | **0** | 1,039 | **0.0000%** |
| 1h | ETHUSDT | 52.98 | 55.67 | 58.98 | **0** | 1,083 | **0.0000%** |
| 1h | SOLUSDT | 49.48 | 55.31 | 58.38 | **1** | 1,206 | **0.0829%** |
| 15m | BTCUSDT | 44.42 | 54.07 | 57.57 | **11** | 4,496 | **0.2447%** |
| 15m | ETHUSDT | 39.80 | 53.36 | 57.35 | **4** | 4,518 | **0.0885%** |
| 15m | SOLUSDT | 46.79 | 54.44 | 57.52 | **8** | 5,166 | **0.1549%** |

**Does a low-RSI long-breakout population exist at 1h?**

- **BTCUSDT — NO.** P1 = 54.90, P5 = 58.03. **Zero** bars below RSI 50 in 1,039
  long breakouts. The minimum, 50.85, is above the threshold.
- **ETHUSDT — NO.** P1 = 55.67, P5 = 58.98. **Zero** bars below RSI 50 in 1,083
  long breakouts. The minimum, 52.98, is nearly three points clear.
- **SOLUSDT — NO.** P1 = 55.31, P5 = 58.38. **One** bar below RSI 50 in 1,206
  long breakouts (0.0829%). That single bar is 2023-06-06T17:00Z, RSI 49.4788,
  clearing its channel by 0.196%. It is the entire sub-50 population at 1h
  across all three symbols.

Every 1h cell is below the 1% threshold by two to four orders of magnitude.

### 6.3 Does the 15m control reproduce Point 3?

Point 3 measured **trend + Donchian over 2022–23**; this report measures
**Donchian alone over 2022–24**. Three figures are therefore reported, and which
is which is stated:

**(a) Full period, Donchian-only, 2022–2024** — the table in §6.2. Minimum long
RSI 44.42 / 39.80 / 46.79; 11 / 4 / 8 bars below 50.

**(b) Overlapping period, Donchian-only, 2022–2023** — Point 3's window, this
report's population definition:

| symbol | LONG bars | MIN | P1 | count < 50 | % < 50 |
|---|---:|---:|---:|---:|---:|
| BTCUSDT | 2,725 | 44.42 | 53.36 | 9 | 0.3303% |
| ETHUSDT | 2,845 | 39.80 | 52.85 | 4 | 0.1406% |
| SOLUSDT | 3,312 | 46.79 | 54.50 | 7 | 0.2114% |

**(c) Overlapping period, Point 3's OWN population (EMA20 > EMA50 AND
Donchian), 2022–2023** — narrowed all the way back to what report 07 measured:

| symbol | LONG bars | **MIN RSI (long)** | report 07 §5.7 | P1 | report 07 | SHORT bars | **MAX RSI (short)** | report 07 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| BTCUSDT | 1,860 | **54.18** | 54.18 | 58.14 | 58.15 | 1,698 | **45.75** | 45.75 |
| ETHUSDT | 1,910 | **54.56** | 54.56 | 58.68 | 58.68 | 1,784 | **44.81** | 44.81 |
| SOLUSDT | 2,254 | **55.73** | 55.73 | 58.87 | 58.88 | 2,192 | **44.41** | 44.41 |

Total breakout bars **11,698** against Point 3's **11,711** — a difference of
**13 bars in 11,711 (0.11%)**, and **the minimum RSI reproduces to the reported
two decimal places on all three symbols**. Rejections at `rsi_lower = 50` on
this population: **0, 0, 0** — Point 3's "zero rejections in 11,711 breakout
bars", reproduced.

The 13-bar residual is accounted for and not left open: this report discards
**114** warm-up bars where Point 3 discarded about **50**, so roughly 64 bars at
the very start of 2022 are absent here. That is a difference in warm-up
convention, not in measurement. The 0.01 disagreements on the P1 column
(58.14 vs 58.15, 58.87 vs 58.88) are the same 64 bars moving a percentile by one
rank.

**The control reproduces Point 3.** The code that reports emptiness at 1h is the
same code that reproduces the 15m figure it is being compared against.

### 6.4 Is the 1h result materially different from 15m?

**No — and where it differs, it differs in the direction that makes the
population MORE empty at 1h, not less.**

| quantity | 1h range | 15m range | direction |
|---|---|---|---|
| long breakout rate | 3.97–4.60% of bars | 4.28–4.92% of bars | near-identical |
| P1 of long-breakout RSI | 54.90–55.67 | 53.36–54.44 | **higher at 1h** |
| P5 of long-breakout RSI | 58.03–58.98 | 57.35–57.57 | **higher at 1h** |
| count below RSI 50 | 0, 0, 1 | 11, 4, 8 | fewer at 1h |
| % below RSI 50 | 0.0000–0.0829% | 0.0885–0.2447% | **lower at 1h** |
| rejections at `rsi_lower = 50` | 0, 0, 1 | 11, 4, 8 | fewer at 1h |
| max RSI on short breakouts | 46.20–48.70 | 50.31–55.51 | **lower at 1h** |

The hypothesis being tested predicted equal emptiness at both scales. What was
found is emptiness at both, slightly **deeper** at 1h. The direction is
explainable and does not require a new mechanism: 15m has four times the sample
and therefore four times the opportunity for a tail bar, and its tail bars come
in clusters — of BTC's 11 sub-50 bars at 15m, three fall inside 45 minutes of
each other on 2023-07-15, and of SOL's 8, three fall inside 45 minutes on
2022-09-27. **The 15m "population" is 23 bars in 14,180, and it is not 23
independent events.**

### 6.5 THE VERDICT

Applying the threshold fixed in §6.1 — fewer than 1% of long breakout bars below
RSI 50, on all three symbols — to all six cells:

| | BTCUSDT | ETHUSDT | SOLUSDT | |
|---|---|---|---|---|
| **1h** | 0.0000% ✓ | 0.0000% ✓ | 0.0829% ✓ | negligible |
| **15m** | 0.2447% ✓ | 0.0885% ✓ | 0.1549% ✓ | negligible |

> # (A) STRUCTURAL
>
> **The population is empty or negligible at both timeframes. The
> Donchian/RSI entailment is scale-invariant. 1R.5's operationalisation is
> CLOSED FOR THE RECORD: it cannot be exercised with this trigger at any
> timeframe under consideration.**

Per symbol: **BTCUSDT STRUCTURAL · ETHUSDT STRUCTURAL · SOLUSDT STRUCTURAL.**
Overall: **STRUCTURAL.**

### 6.6 Why the entailment holds — the mechanism, stated

The measurement supports a mechanism, and stating it is what makes the result
transferable rather than a table of six numbers. **The breakout bar's own gain
enters the RSI it is measured at.** A bar that closes above a 20-bar high has,
by construction, produced a gain large enough to clear that high, and that gain
enters `avg_gain` with weight 1/14 on the very bar the condition fires. For RSI
to remain below 50 the prior losses would have to outweigh it by a factor of 13.

That is not impossible — §7.4's positive control constructs it — but it requires
a specific shape: a sharp fall, then a **flat** consolidation long enough for the
20-bar channel to collapse onto current price, so that the break can be *small*.
A large break from a fallen market lifts its own RSI above 50 in the act of
breaking. **Real 1h and 15m crypto bars do not consolidate flat enough for
twenty bars.** The mechanism is expressed entirely in bar counts — 20 for the
channel, 14 for the RSI — which is why it does not care how long a bar is, and
that is precisely the scale-invariance claim.

---

## 7. VERIFICATION

`tests/test_rsi_breakout_profile.py`, **30 tests**. Full suite **669 tests, all
passing** (639 pre-existing + 30 new).

**The result this step reports is a NEGATIVE one**, which makes the guards
load-bearing in a way they are not when a measurement finds something. An empty
population is also what a broken detector produces. Three tests exist purely so
that "we found nothing" is distinguishable from "we could not have found
anything": §7.3, §7.4, and a non-vacuity check on the real data.

### 7.1 PLANTED MUTATION — the holdout seal

**The mutation.** In `src/timeframe/resample.py`, widen the date filter to admit
2025:

```
WINDOW_END    = dt.date(2024, 12, 31)  ->  dt.date(2025, 6, 30)
ALLOWED_YEARS = (2022, 2023, 2024)     ->  (2022, 2023, 2024, 2025)
```

**Why it would otherwise pass unnoticed.** The 1m layer physically holds
`year=2025` and `year=2026`; the seal is not maintained by absence. A widened
filter raises nothing at import and nothing in any RSI figure — the numbers
simply become better-sampled and the holdout is spent without anyone deciding to
spend it. This report's population definition and warm-up path are a **new code
path onto sealed data**, so the seal is re-proved through it rather than assumed
from report 19.

**The failing assertion:**

```
>       assert rs.WINDOW_END == dt.date(2024, 12, 31)
E       AssertionError: assert datetime.date(2025, 6, 30) == datetime.date(2024, 12, 31)
E        +  where datetime.date(2025, 6, 30) = rs.WINDOW_END
E        +  and   datetime.date(2024, 12, 31) = <class 'datetime.date'>(2024, 12, 31)
E        +    where <class 'datetime.date'> = dt.date
```

**7 of this file's tests failed** under the mutation, not one — the constant
guard, the end-to-end bar check at both timeframes, the bar-count check, the
non-vacuity check, the Point 3 reconciliation and the open-price check. **17
tests failed across the whole suite.** Two independent runtime guards also fired
before any test assertion was reached: `schedule.load_bars` raised
`PermissionError` on the widened range, and `resample.assert_sealed` stands
behind it on the way out. Defence in depth — this module deliberately defines
**no window constant of its own**, and a test asserts that it defines none, so
there is nothing here that could drift from the one seal.

Reverted from a pre-mutation copy; `git diff --exit-code -- src/timeframe/resample.py` is clean.

### 7.2 PLANTED MUTATION — the negligibility comparison inverted

**The mutation.** In `rsi_breakout_profile.is_negligible`:

```
return bool(pct_below < max_pct)  ->  return bool(pct_below > max_pct)
```

**Why it is easy to get wrong and hard to spot.** Every number in every table
above stays byte-identical. The only thing that changes is the single word at
the end of this report — STRUCTURAL becomes SCALE-DEPENDENT — and the report
then states the opposite conclusion over a correct set of figures. There is no
arithmetic anywhere that would look wrong. A **small** percentage is the empty
population and the hypothesis stays unexercised; a **large** percentage is the
live finding.

**The failing assertions:**

```
>       assert rbp.is_negligible(0.0) is True
E       assert False is True
E        +  where False = <function is_negligible at 0x1075807c0>(0.0)
E        +    where <function is_negligible at 0x1075807c0> = rbp.is_negligible
```

```
>       assert rbp.verdict(ok) == rbp.STRUCTURAL
E       AssertionError: assert 'SCALE-DEPENDENT' == 'STRUCTURAL'
E         - STRUCTURAL
E         + SCALE-DEPENDENT
```

**3 tests failed.** The guard asserts the full ordering across rising
percentages — `True, True, True, False, False, False` — so an inversion reverses
a sequence rather than flipping one label, and a second test shows the flip
propagating all the way to the verdict string.

Reverted from a pre-mutation copy.

### 7.3 The Donchian exclusion convention

Guarded three ways, each of which fails under an off-by-one:

1. **The window contents, directly.** For every valid index on a 200-bar
   pseudo-random series, `upper[i] == max(high[i−20 : i])` and
   `lower[i] == min(low[i−20 : i])`. The test additionally **asserts that the
   series contains bars where including the current bar would change the window
   max** — without that, the test could pass on a series where the off-by-one
   makes no difference and would be proving nothing.
2. **The first defined index.** `upper[:20]` is all NaN and `upper[20]` is
   finite. A dropped `.shift(1)` makes index 19 finite.
3. **The behavioural consequence.** Twenty bars with high 10, then a bar with
   high 100, low 9, close 11. Under correct exclusion the channel is 10 and the
   close of 11 clears it — a breakout. Under the off-by-one the channel becomes
   100, the close does not clear it, and **the population is silently emptied**.
   The mirror is asserted too: a wick below the channel is not a close below it.

### 7.4 SYNTHETIC POSITIVE CONTROL

**Without this the empty result is uninterpretable.** A series that *does*
contain a low-RSI breakout is constructed and the detector must find it, through
the full pipeline — bar frame in, warm-up discarded, verdict machinery out — not
through the indicator functions in isolation.

**The construction is itself the argument for §6.6's mechanism.** A single large
up-bar clearing a 20-bar high from a falling market does **not** produce a low
RSI; the breakout bar's own gain drags RSI up with it. A Donchian break can only
coincide with a depressed RSI if the break is *small*, which requires the 20-bar
high to sit on top of current price, which requires a flat base:

```
bars   0-149 : alternating 100 / 101   -- establishes avg_gain ~ avg_loss
bars 150-169 : twenty bars of -3%      -- drives avg_gain to ~0
bars 170-189 : twenty bars perfectly flat -- both averages decay by the same
                                          (13/14) factor per bar, so RSI holds
                                          near 0 while the 20-bar channel
                                          collapses onto current price
bar      190 : +0.5%                   -- clears the flat channel by 0.5%, a
                                          gain far too small to lift RSI to 50
```

**RESULT: exactly one long breakout detected, at RSI 10.68**, close 55.198
against a channel of 54.923. The verdict machinery carries it through: the
sub-50 share is 100%, `is_negligible(100.0)` is `False`, and `verdict` returns
`SCALE-DEPENDENT`. **The measurement can find the population if it exists.**

A **negative** control sits beside it: the same pipeline on a steadily rising
random series finds more than 20 breakouts and **zero** below RSI 50. A detector
that flagged everything would pass the positive control and fail this one.

### 7.5 The remaining tests

- **Wilder RSI against hand-computed arithmetic**, not against another library —
  a second implementation agreeing with the first proves they share an author's
  assumptions. Four cases: the simple-mean seed; the zero-loss branch; a
  non-uniform seed (`mean(1..14) = 7.5`, then `7.5 × 13/14` against `105/14`);
  and `48.148148…` reached two independent ways. Plus a guard that Wilder is
  **not** a rolling mean — a shock 15 bars back has left a 14-bar window
  entirely but still holds RSI below 20 under Wilder.
- **A balanced series does not sit at 50, it oscillates about it** — the seed is
  exactly 50, the next bar is exactly `100 × 7.5/14 = 53.5714…`. Recorded
  because reading a single bar's RSI as "balanced = 50" is reading a phase.
- **The convention gap** against the engine's EWM-seeded `rsi_wilder` is
  asserted below 0.05 RSI points after warm-up.
- **Warm-up is exactly 114 bars** at three lengths, no NaN survives it, and the
  resulting counts match report 19's (26,190 / 105,102) on all three symbols.
- **Non-vacuity on real data**: more than 500 breakouts per direction per cell,
  between 1% and 15% of bars.
- **The Point 3 reconciliation** is asserted, not just reported — minimum long
  RSI within 0.02 of report 07's figures on all three symbols, total within 50
  bars of 11,711.
- **Rejection-table semantics**: long rejects below, short rejects above, they
  are not interchangeable, and counts are monotone in the threshold.
- **The firewall**, over the module's AST: no performance name may appear as an
  identifier or a non-docstring string literal. Docstrings are excluded because
  they *state* the prohibition.
- **The import graph**: `simulate`, `src.sweep` and `src.folds.run` may not be
  imported; the engine's `signals` **must** be, so the Donchian channel is
  reused rather than reimplemented.
- **No open price** is read, bound or present in any loaded frame.

---

## 8. ASSUMPTIONS AND LIMITATIONS

1. **The negligibility threshold is a judgement.** 1% below RSI 50 on all three
   symbols was fixed before the measurement, which is the only protection
   available against having chosen it to produce this answer. It did not turn
   out to be close: the largest observed value is 0.2447% and the 1h maximum is
   0.0829%. **The verdict would be unchanged for any threshold from about
   0.25% up to 100%**, so the specific number carries no weight here. It would
   have mattered only if the population had been marginal, and it is not.

2. **Two timeframes were measured, not five.** The claim tested is
   scale-invariance and the evidence is a 4× ratio, not a sweep. 5m, 4h and 1d
   were not measured, because the frozen rule already excluded them as
   timeframes and measuring them would be answering a question nobody asked.
   **The verdict's scope is stated accordingly: "at any timeframe under
   consideration," which is 15m and 1h.** A reader who wants the claim over the
   full candidate set does not have it from this report.

3. **The population is Donchian-only and deliberately broader than the
   engine's actual entry condition**, which also requires EMA20 > EMA50. The
   engine's population is a strict subset of the one measured here (§6.3b/c
   confirm it on matched windows: of BTC's 2,725 Donchian-only long breakouts
   at 15m over 2022–23, **1,860 survive the trend filter — 68%**). Emptiness on
   the superset entails emptiness on the subset, so this
   direction of the argument is safe. **The reverse does not hold** and is not
   claimed.

4. **RSI is Wilder-seeded here and EWM-seeded in the engine.** The gap after
   warm-up is at most 4.3 × 10⁻³ RSI points, four orders of magnitude below any
   figure reported. If an entry rule is ever built on `rsi_lower`, it should use
   one implementation, not two.

5. **One bar in 3,328 is not zero.** SOL's 2023-06-06T17:00Z breakout at RSI
   49.4788 is a real bar and is reported as such. The verdict is "negligible,"
   not "empty," and the distinction is kept because the sub-50 population at 1h
   is a single event, which is a statement about one bar rather than about a
   regime.

6. **Nothing here says whether reversal breakouts are profitable, or whether
   they exist under some other trigger.** The firewall forbids the first
   question and this step does not ask the second. **The finding is narrow and
   deliberately so: `rsi_lower` on a Donchian-20 breakout cannot select a
   distinct population, because there is no distinct population for it to
   select.** If reversal breakouts exist, an RSI bound on this trigger is not
   what separates them — which is what report 07 §7.3 flagged, now established
   at both scales rather than one.

---

## 9. WHAT THIS CLOSES, AND WHAT IT DOES NOT

**CLOSED.** 1R.5's operationalisation. The reversal-breakout hypothesis is no
longer "unexercised pending a different timeframe" — the timeframe was changed,
by a rule frozen before the numbers existed, and the population is still empty.
It is closed **for the record on this trigger**, which is a stronger statement
than report 07 could make and a weaker one than "refuted."

**NOT CLOSED.** Whether a reversal-breakout hypothesis is worth pursuing under a
**different trigger**. The entailment demonstrated here is between *Donchian-N*
and *RSI(14)*, and §6.6 explains why it is tight: the breakout bar's own gain
enters the RSI on the bar the condition fires. A trigger that does not embed its
own confirmation in the indicator it is filtered by — a level break, a range
exit, a volatility expansion — would not inherit this entailment. **That is a
new hypothesis and it is not proposed here**, only noted so the closing of 1R.5
is not read as closing more than it does.

**OPEN QUESTIONS**, carried forward:

1. **`rsi_lower` at 60 is the only non-inert setting measured** (7.9–9.3% of 1h
   long breakouts rejected). It is not 1R.5's filter and was not proposed. If a
   future step wants a momentum bound, it needs a justification for the level
   that is not "it is the first one that rejects anything."
2. **Whether the entailment survives a different Donchian period is untested.**
   20 and 14 are Point 4's numbers and were not swept — correctly, since this
   was a test of that operationalisation. A shorter channel against a longer RSI
   (say Donchian-10 with RSI-21) weakens the arithmetic in §6.6 and is the
   cheapest place to look if anyone wants to reopen this.
3. **The 15m tail bars cluster.** 23 sub-50 bars across three symbols, with at
   least two clusters of three inside 45 minutes. Not characterised further,
   because characterising a 23-bar population would invite reading structure
   into it that 23 bars cannot support.

---

**Files.** `src/analysis/rsi_breakout_profile.py` ·
`tests/test_rsi_breakout_profile.py` · this report.
**Not modified:** `src/costs/`, `src/timeframe/`, the engine, the regime module,
any existing report.
