# REPORT 21 — THE WICK-AND-REJECT SWEEP POPULATION AT 1h

**Point 1, continued.** The prior hypothesis was killed
(`docs/handoff/16_point_4_closing.md`); report 20 (`02acbcf`) closed 1R.5's
operationalisation. The thesis now under development is a **failed breakout /
liquidity sweep**, triggered by a bar whose **extreme breaks a Donchian-10
channel intrabar** while its **close returns inside** the channel.

**This step exists to answer one question.** A wick-and-reject bar is by
construction a large-range bar — it has to travel beyond the channel and come
back inside within one bar. If the distance from its close to its own sweep
extreme exceeds **2.25 × ATR**, then the frozen stop sits **inside** that
extreme, and a mere retest of the level the thesis claims was rejected would
take the stop out. **The stop would contradict the mechanism it is meant to
protect.** That is decidable from indicator distributions on bars.

**The performance firewall is re-armed.** No expectancy, win rate, profit
factor, Sharpe, equity curve, `r_multiple` or `net_pnl` aggregate is computed,
referenced or estimated. Signal counts, pass rates and indicator distributions
are permitted pre-firewall quantities. **No trade is simulated** — no entry, no
exit, no sizing, no outcome. **Nothing here reads a bar later than the one it
describes:** every quantity is a function of the signal bar and its own prior
channel, so there is no forward return to compute even by accident. A test
asserts no negative shift appears anywhere in the module.

**Window read: 2022-01-01 to 2024-12-31 only. THE HOLDOUT IS SEALED** — the
window is inherited whole from `src/timeframe/resample.py` and this module
defines no window constant of its own. Fold boundaries come from the tracked
`folds.json`; **the holdout entry in that file is never walked**, and every
window returned is asserted to end before the seal. §7.1 reports the planted
mutation.

**Nothing here is swept or selected.** N = 10 is frozen as a one-time structural
choice. m = 2.25, the 1.50% floor, ATR(14) and 1h are all frozen and
transcribed. The Donchian-20 column is **a single fixed comparison for the
record**, so the effect of N = 10 is visible rather than assumed. **This report
computes arithmetic; it proposes no multiplier and recommends no change.**

**No open price is used anywhere.** `open_synth` is dropped at the load
boundary. The trigger needs high, low and close.

---

## 1. THE TRIGGER, STATED PRECISELY

**THE EXCLUSION CONVENTION.** The channel is the engine's own
`signals.donchian_prior`, reused not reimplemented — `rolling(N).max().shift(1)`
— so the current bar's own high and low are **not** in its own lookback window:

    upper[T] = max( high[T−10] … high[T−1] )
    lower[T] = min( low[T−10]  … low[T−1]  )

**THE TRIGGER:**

| | condition 1 — the sweep | condition 2 — the rejection |
|---|---|---|
| **LONG** (downside sweep, rejected) | `low[T] < lower[T]` | `close[T] > lower[T]` |
| **SHORT** (upside sweep, rejected) | `high[T] > upper[T]` | `close[T] < upper[T]` |

**CHANNEL BREAK** is condition 1 alone — the channel was broken intrabar,
whatever the close then did. Wick-and-reject is a strict subset of it, and the
ratio between them is the **rejection rate**, previously unmeasured.

**AN OFF-BY-ONE HERE IS WORSE THAN FOR A CLOSE-BASED BREAKOUT.** If the bar's
own low were inside the window that produced the minimum, then
`lower[T] ≤ low[T]` always and `low[T] < lower[T]` becomes **strictly
unsatisfiable** — the population is empty, not merely distorted. Shifted the
other way it becomes trivial. Neither raises. §7.3 reports the guard, which
asserts the window contents directly and additionally asserts the
unsatisfiability as a property.

**STRICTNESS: all four comparisons are strict.** A low exactly *on* the prior
minimum has not broken the channel; a close landing exactly *on* the level has
not returned inside it. **Ties are counted, not argued about:**

| Donchian | symbol | `low == lower` | `high == upper` | `close == lower` | `close == upper` |
|---|---|---:|---:|---:|---:|
| 10 | BTCUSDT | 16 | 8 | 7 | 7 |
| 10 | ETHUSDT | 9 | 6 | 0 | 1 |
| 10 | SOLUSDT | 16 | 13 | 0 | 2 |
| 20 | BTCUSDT | 5 | 9 | 2 | 3 |
| 20 | ETHUSDT | 5 | 1 | 2 | 1 |
| 20 | SOLUSDT | 4 | 8 | 0 | 0 |

Out of 26,304 bars per symbol, at most 16 sit exactly on a boundary in any
cell — **at most 0.06%.** The convention is stated for completeness; it cannot
move a figure in this report.

**Bars and warm-up.** 1h bars via `src/timeframe/resample.py`, unchanged; **zero
buckets dropped** for any symbol. **114 bars discarded** — report 19's ATR
convention exactly: 1 (no previous close, so no true range) + 13 (before the
seed completes) + 100 (stabilisation). **26,190 bars analysed per symbol**,
identical to reports 19 and 20, so all three describe the same bars. The
discard ends at **2022-01-05T18:00Z**, nearly three months before fold 1's
`train_start` of 2022-04-01, **so every fold below is fully warmed** — asserted
by test.

---

## 2. PART A/B — POPULATION SIZE AND THE REJECTION RATE

All percentages are of the 26,190 analysed bars.

| Donchian | symbol | dir | channel-break | **(%)** | **wick-and-reject** | **(%)** | **rejection rate** |
|---|---|---|---:|---:|---:|---:|---:|
| **D10** | BTCUSDT | long | 3,303 | 12.6117 | **1,899** | **7.2509** | **0.5749** |
| **D10** | BTCUSDT | short | 3,550 | 13.5548 | **1,932** | **7.3769** | **0.5442** |
| **D10** | ETHUSDT | long | 3,267 | 12.4742 | **1,809** | **6.9072** | **0.5537** |
| **D10** | ETHUSDT | short | 3,613 | 13.7953 | **1,972** | **7.5296** | **0.5458** |
| **D10** | SOLUSDT | long | 3,609 | 13.7801 | **1,965** | **7.5029** | **0.5445** |
| **D10** | SOLUSDT | short | 3,821 | 14.5895 | **2,009** | **7.6709** | **0.5258** |
| **D20** | BTCUSDT | long | 2,097 | 8.0069 | **1,202** | **4.5895** | **0.5732** |
| **D20** | BTCUSDT | short | 2,303 | 8.7934 | **1,261** | **4.8148** | **0.5475** |
| **D20** | ETHUSDT | long | 2,084 | 7.9572 | **1,146** | **4.3757** | **0.5499** |
| **D20** | ETHUSDT | short | 2,372 | 9.0569 | **1,288** | **4.9179** | **0.5430** |
| **D20** | SOLUSDT | long | 2,357 | 8.9996 | **1,282** | **4.8950** | **0.5439** |
| **D20** | SOLUSDT | short | 2,513 | 9.5953 | **1,307** | **4.9905** | **0.5201** |

### 2.1 The rejection rate is ~54% and it barely moves

**The rejection rate sits in 0.5258–0.5749 across all twelve cells.** It is
almost identical at D10 and D20 — BTC long 0.5749 vs 0.5732, SOL short 0.5258
vs 0.5201 — and it is consistently a point or two higher on the long side than
the short side on every symbol at both lengths.

This is the first measurement of a quantity the project had only guessed at.
**Slightly more than half of all intrabar channel breaks are rejected by the
close.** It is not a rare event, and it is not close to universal either. That
the figure is invariant to doubling the channel length is a structural
regularity worth recording: whatever produces rejections is not a property of
how far back the channel looks.

### 2.2 What N = 10 buys, as a comparison for the record

**D10 produces about 1.55× the signals of D20** (11,586 vs 7,486 pooled across
symbols and directions). Channel breaks scale similarly (12.47–14.59% of bars at
D10 against 7.96–9.60% at D20), which is what a nearer channel should do.

**N is frozen at 10 and this report does not select it.** The comparison is
recorded because "a shorter channel gives more signals" was previously an
assumption; it is now a number. §3 shows the choice also has a geometry
consequence, in the same direction.

---

## 3. PART B — PER-FOLD SIGNAL COUNTS

**Fold boundaries are read from the tracked `data/derived/folds/folds.json`**
(nine in-sample folds, committed at `af9d314`), **not** from the approximate
4,320 / 2,160 bar arithmetic. Actual bars per period: **train 4,344–4,416, test
2,160–2,208**.

**Boundary convention across timeframes.** `folds.json` states ends in 15m terms
(`train_end_ms` is 23:45:00Z of the end day). Bars are assigned by
`lo ≤ ts ≤ hi` on the bucket start. At 1h the last bucket of a day starts at
23:00 and none starts between 23:00 and midnight, so the 15m end admits exactly
the 1h bars of the end day and nothing beyond — the inclusive form is exact at
1h and needs no adjustment.

**Counts are both directions combined.** A bar carrying both masks — an outside
bar sweeping and rejecting both channels — is **one** signal bar, counted once;
the overlap is reported separately rather than double-counted or dropped. It
occurs but is rare: at D10, summed across all nine train periods, **86** bars
(BTC), **59** (ETH) and **32** (SOL) — at most 19 in any single fold.

### 3.1 Donchian-10 — TRAIN (minimum required: 200)

| symbol | F1 | F2 | F3 | F4 | F5 | F6 | F7 | F8 | F9 | **MIN** |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| BTCUSDT | 617 | 613 | 617 | 594 | 600 | 626 | 645 | 655 | 688 | **594** |
| ETHUSDT | 616 | 605 | 596 | 586 | 570 | 611 | 653 | 642 | 664 | **570** |
| SOLUSDT | 710 | 659 | 597 | 584 | 599 | 657 | 669 | 675 | 713 | **584** |

### 3.2 Donchian-10 — TEST (minimum required: 50)

| symbol | F1 | F2 | F3 | F4 | F5 | F6 | F7 | F8 | F9 | **MIN** |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| BTCUSDT | 306 | 311 | 283 | 317 | 309 | 336 | 319 | 369 | 326 | **283** |
| ETHUSDT | 299 | 297 | 289 | 281 | 330 | 323 | 319 | 345 | 337 | **281** |
| SOLUSDT | 296 | 301 | 283 | 316 | 341 | 328 | 347 | 366 | 378 | **283** |

### 3.3 Donchian-20 — the same figures, for the record

| period | symbol | F1 | F2 | F3 | F4 | F5 | F6 | F7 | F8 | F9 | **MIN** |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| train | BTCUSDT | 403 | 405 | 392 | 384 | 367 | 369 | 414 | 447 | 485 | **367** |
| train | ETHUSDT | 415 | 390 | 350 | 342 | 339 | 354 | 428 | 461 | 461 | **339** |
| train | SOLUSDT | 458 | 427 | 370 | 363 | 381 | 424 | 422 | 434 | 499 | **363** |
| test | BTCUSDT | 199 | 193 | 191 | 176 | 193 | 221 | 226 | 259 | 210 | **176** |
| test | ETHUSDT | 186 | 164 | 178 | 161 | 193 | 235 | 226 | 235 | 218 | **161** |
| test | SOLUSDT | 187 | 183 | 180 | 201 | 223 | 199 | 235 | 264 | 274 | **180** |

### 3.4 The binding numbers

**The MINIMUM across folds is the binding figure, not the mean** — the design
has to survive its worst fold, not its average one. A test asserts
`fold_minimum` returns the minimum and not the mean.

| | requirement | **D10 worst fold** | margin | **D20 worst fold** | margin |
|---|---:|---:|---:|---:|---:|
| **TRAIN** | 200 | **570** (ETH, F5) | **2.85×** | **339** (ETH, F5) | 1.70× |
| **TEST** | 50 | **281** (ETH, F4) | **5.62×** | **161** (ETH, F4) | 3.22× |

**Every fold clears both minimums on every symbol, at both channel lengths.**
The tightest cell in the entire table is ETH fold 5 train at D10 — 570 against a
requirement of 200. **Signal count is not a constraint on this design.** Folds
3–5 are the sparse stretch on every symbol — train minima fall in folds 4–5 and
test minima in folds 3–4, together covering roughly 2023-04 to 2023-09. That is
a calendar fact about that market period, not a fold-design artefact; even there
the margin is nearly 3×.

Note that the nine folds **overlap by 50% in their training windows** and are a
stability probe, not nine independent trials (`src/folds/schedule.py`). The
counts above are per-fold populations, not independent samples.

---

## 4. PART C — THE GEOMETRY CHECK

For each wick-and-reject bar:

    LONG :  excursion = close − low       (entry to the swept extreme)
    SHORT:  excursion = high − close
            excursion_atr = excursion / ATR(14) at that bar

ATR is `src/timeframe/atr_profile.py`'s Wilder ATR, **reused not
reimplemented**, so this report's ATR is report 19's ATR — a test asserts
element-wise equality and that the 1h ETH median reproduces report 19's 0.8440%.
Both excursions are non-negative by construction since `low ≤ close ≤ high`.

### 4.1 The excursion_atr distribution

| Donchian | symbol | dir | MIN | P10 | P25 | **MEDIAN** | P75 | P90 | P95 | P99 | MAX | n |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| D10 | BTCUSDT | long | 0.015 | 0.336 | 0.519 | **0.768** | 1.135 | 1.526 | 1.813 | 2.792 | 4.698 | 1,899 |
| D10 | BTCUSDT | short | 0.005 | 0.302 | 0.468 | **0.721** | 1.060 | 1.551 | 1.960 | 2.816 | 4.756 | 1,932 |
| D10 | ETHUSDT | long | 0.042 | 0.341 | 0.495 | **0.755** | 1.073 | 1.435 | 1.734 | 2.713 | 3.962 | 1,809 |
| D10 | ETHUSDT | short | 0.019 | 0.259 | 0.426 | **0.656** | 0.971 | 1.351 | 1.637 | 2.476 | 5.251 | 1,972 |
| D10 | SOLUSDT | long | 0.039 | 0.292 | 0.444 | **0.682** | 0.966 | 1.324 | 1.621 | 2.400 | 3.954 | 1,965 |
| D10 | SOLUSDT | short | 0.009 | 0.257 | 0.417 | **0.630** | 0.919 | 1.270 | 1.516 | 2.156 | 4.974 | 2,009 |
| D20 | BTCUSDT | long | 0.015 | 0.398 | 0.592 | **0.869** | 1.233 | 1.642 | 2.046 | 3.007 | 4.698 | 1,202 |
| D20 | BTCUSDT | short | 0.036 | 0.359 | 0.540 | **0.807** | 1.165 | 1.654 | 2.106 | 3.013 | 4.756 | 1,261 |
| D20 | ETHUSDT | long | 0.042 | 0.383 | 0.568 | **0.829** | 1.135 | 1.521 | 1.796 | 2.806 | 3.962 | 1,146 |
| D20 | ETHUSDT | short | 0.047 | 0.317 | 0.489 | **0.729** | 1.050 | 1.458 | 1.783 | 2.649 | 5.251 | 1,288 |
| D20 | SOLUSDT | long | 0.039 | 0.325 | 0.506 | **0.740** | 1.049 | 1.386 | 1.694 | 2.484 | 3.954 | 1,282 |
| D20 | SOLUSDT | short | 0.028 | 0.286 | 0.458 | **0.684** | 1.003 | 1.342 | 1.625 | 2.256 | 4.974 | 1,307 |

**The median excursion is 0.63–0.77 ATR at D10.** The typical sweep bar's close
sits well under one ATR from the extreme it just swept. Even the **P95 is
1.52–1.96 ATR** — below the 2.25 stop on every symbol and both directions. The
distribution only reaches the stop at the **P99** (2.16–2.82 ATR), and crosses
it there on five of the six cells — all but SOL short, at 2.156.

### 4.2 THE DIRECT ANSWER — the fraction where the stop sits inside the extreme

`excursion_atr > m` means the swept extreme is **further from the close than the
stop is**, so a stop at `m × ATR` sits **inside** the extreme and a retest of
the swept level would take it out. **That is the failure direction and this is
its frequency, in percent of signals:**

| Donchian | symbol | dir | m = 2.0 | **m = 2.25** | m = 2.5 | m = 3.0 | m = 3.5 | m@90% | m@95% |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| D10 | BTCUSDT | long | 4.0021 | **2.3170** | 1.6324 | 0.7899 | 0.3686 | 1.526 | 1.813 |
| D10 | BTCUSDT | short | 4.6584 | **2.8986** | 2.0704 | 0.7764 | 0.3623 | 1.551 | 1.960 |
| D10 | ETHUSDT | long | 2.8192 | **2.1559** | 1.3820 | 0.4975 | 0.1658 | 1.435 | 1.734 |
| D10 | ETHUSDT | short | 2.5862 | **1.2677** | 0.9635 | 0.4564 | 0.3550 | 1.351 | 1.637 |
| D10 | SOLUSDT | long | 2.2392 | **1.3740** | 0.7634 | 0.2545 | 0.0509 | 1.324 | 1.621 |
| D10 | SOLUSDT | short | 1.5431 | **0.8462** | 0.5973 | 0.2987 | 0.1493 | 1.270 | 1.516 |
| D20 | BTCUSDT | long | 5.3245 | **3.1614** | 2.2463 | 1.1647 | 0.5824 | 1.642 | 2.046 |
| D20 | BTCUSDT | short | 6.3442 | **3.8065** | 2.7756 | 1.1102 | 0.5551 | 1.654 | 2.106 |
| D20 | ETHUSDT | long | 3.4031 | **2.4433** | 1.5707 | 0.4363 | 0.1745 | 1.521 | 1.796 |
| D20 | ETHUSDT | short | 3.3385 | **1.7081** | 1.3199 | 0.6211 | 0.5435 | 1.458 | 1.783 |
| D20 | SOLUSDT | long | 2.8861 | **1.7161** | 0.9360 | 0.3120 | 0.0780 | 1.386 | 1.694 |
| D20 | SOLUSDT | short | 1.9893 | **1.0712** | 0.6886 | 0.3060 | 0.1530 | 1.342 | 1.625 |

`m@90%` and `m@95%` are the multipliers that would place the stop **beyond** the
extreme on 90% and 95% of signals — that is, the 90th and 95th percentiles of
the excursion distribution. **They are arithmetic, not proposals.**

### 4.3 What the geometry check says

> **At the frozen m = 2.25, the stop sits inside the sweep extreme on
> 0.85%–2.90% of signals at Donchian-10.** Equivalently, **the frozen stop
> clears the swept extreme on 97.10%–99.15% of signals**, on every symbol and
> both directions.

**The frozen geometry is internally consistent with the trigger.** The concern
that motivated this step — that a 2.25 × ATR stop would sit inside the wick and
be taken out by a retest of the rejected level — **is not borne out.** The
required coverage arrives well below 2.25: `m@95%` is **1.52–1.96** across all
six D10 cells and `m@90%` is 1.27–1.55, so **2.25 buys more than 95% coverage
everywhere**, and on SOL more than 99%.

The sensitivity is smooth and shallow around the frozen value. Dropping to
m = 2.0 roughly doubles the exposed fraction (to 1.54–4.66%); raising to
m = 2.5 roughly halves it (to 0.60–2.07%). **Nothing turns on the third decimal
of the multiplier** — there is no cliff near 2.25, which is the reassuring shape
for a frozen parameter to have.

**BTC is the binding symbol** (2.32% long, 2.90% short) and SOL the least
exposed (1.37% / 0.85%). The ordering is consistent across every multiplier and
both channel lengths.

**D20 would be worse, not better, on this axis** — 1.07–3.81% exposed against
D10's 0.85–2.90%. The longer channel is broken less often but from further away,
so its sweeps are geometrically larger. **N = 10 is frozen and this is not a
reason for it**, but it is worth recording that the frozen choice happens to sit
on the favourable side of this trade-off rather than against it.

### 4.4 Bar range in ATR units — the mechanism behind the numbers

| symbol | dir | **range/ATR, w&r median** | w&r P90 | all-bars median | all-bars P90 | ratio of medians |
|---|---|---:|---:|---:|---:|---:|
| BTCUSDT | long | **1.267** | 2.158 | 0.823 | 1.691 | 1.54× |
| BTCUSDT | short | **1.174** | 2.094 | 0.823 | 1.691 | 1.43× |
| ETHUSDT | long | **1.231** | 2.042 | 0.838 | 1.655 | 1.47× |
| ETHUSDT | short | **1.108** | 1.939 | 0.838 | 1.655 | 1.32× |
| SOLUSDT | long | **1.135** | 1.850 | 0.870 | 1.563 | 1.31× |
| SOLUSDT | short | **1.066** | 1.717 | 0.870 | 1.563 | 1.23× |

**Wick-and-reject bars are 1.23–1.54× the typical bar's range in ATR units — a
real premium, but a modest one.** The premise that made this check necessary
("by construction a large-range bar") is confirmed in direction and quantified:
these bars are larger than typical, but they are not outliers. A median range of
1.07–1.27 ATR against 2.25 ATR of stop leaves the whole bar comfortably inside
the stop, and **the excursion is only part of that range** — the close sits
somewhere within it, so the close-to-extreme distance (median 0.63–0.77 ATR) is
roughly **59–61%** of the bar's range.

**That is the mechanism.** The stop clears the extreme not because the bars are
small but because 2.25 ATR is roughly twice a typical sweep bar's entire range,
and the excursion is only part of that range.

---

## 5. PART D — STOP DISTANCE IN PERCENT, AGAINST THE COST FLOOR

`2.25 × ATR` as a **percentage of the bar's close**, against the **1.50% floor**.
The floor **binds** when the ATR term falls **below** it — the guard rail, not
the volatility, then sets the stop.

| symbol | population | P10 | P25 | **MEDIAN** | P75 | **floor binds (%)** | n |
|---|---|---:|---:|---:|---:|---:|---:|
| BTCUSDT | wick-and-reject | 0.778 | 1.142 | **1.578** | 2.045 | **46.1538** | 3,783 |
| BTCUSDT | ALL bars | 0.805 | 1.156 | **1.563** | 2.030 | **46.2085** | 26,190 |
| ETHUSDT | wick-and-reject | 1.034 | 1.413 | **1.913** | 2.616 | **29.4290** | 3,748 |
| ETHUSDT | ALL bars | 1.029 | 1.402 | **1.899** | 2.573 | **29.7556** | 26,190 |
| SOLUSDT | wick-and-reject | 1.875 | 2.373 | **3.122** | 4.040 | **3.0855** | 3,954 |
| SOLUSDT | ALL bars | 1.881 | 2.371 | **3.110** | 4.041 | **3.1424** | 26,190 |

Per direction on wick-and-reject bars: BTC long 46.87% / short 45.86%; ETH long
29.57% / short 29.46%; SOL long 3.26% / short 2.94%.

**Cross-check against report 19.** The all-bars median of `2.25 × ATR%` is
1.5632% / 1.8991% / 3.1103%, which is exactly 2.25 × report 19's 1h median ATR%
of 0.6947 / 0.8440 / 1.3824. The two reports agree to four decimal places.

### 5.1 The prediction in the brief is REFUTED — twice over

The brief predicted: *"Wick-and-reject bars are a high-volatility subset, so the
floor should bind even less often."*

**First: the effect is real in direction but negligible in size.** The floor
binds on 46.15% of BTC wick-and-reject bars against 46.21% of all bars — a
difference of **0.05 percentage points**. ETH: 29.43% vs 29.76%, a difference of
0.33. SOL: 3.09% vs 3.14%, a difference of 0.06. **Directionally the prediction
holds on all three symbols; materially it is nothing.** Any design reasoning
that assumed the sweep population would sit meaningfully clear of the floor is
wrong.

**Why.** The premise contains a conflation. Wick-and-reject bars are **not** a
high-ATR subset; they are a high-**relative-range** subset — §4.4 shows they are
selected for being ~1.3× the typical bar *relative to their own ATR*. That
selection criterion is **scale-free**, so it is nearly orthogonal to the ATR
*level*, and the ATR level is what the percentage floor compares against.
Selecting for `range/ATR` tells you almost nothing about `ATR/close`. The
observed 0.05–0.33 point shift is the small residual correlation between the
two, and nothing more.

**Second, and larger: the floor binds far more often than "should not bind in
median conditions" suggests.** Report 19 established that at 1h the floor does
not bind at the median, and that remains true — the BTC median of 1.578% is
above 1.50%. **But it is above by 5%, so the floor binds on 46% of BTC signals
and 29% of ETH signals.** Both statements are true simultaneously; the second is
the operationally relevant one and it does not follow from the first.

**On BTC the guard rail is not a guard rail — it is close to being the stop
rule.** On nearly half of BTC signals the stop is set by the 1.50% floor rather
than by 2.25 × ATR. On SOL it is a genuine rail, binding 3% of the time. **ETH
sits between at 29%.** This is reported, not adjudicated: no parameter is
changed here. It is carried to §8 as the principal open question.

---

## 6. VERIFICATION

`tests/test_sweep_population.py`, **29 tests**. Full suite **698 tests, all
passing** (669 pre-existing + 29 new).

### 6.1 PLANTED MUTATION — the holdout seal

**The mutation.** In `src/timeframe/resample.py`:

```
WINDOW_END    = dt.date(2024, 12, 31)  ->  dt.date(2025, 6, 30)
ALLOWED_YEARS = (2022, 2023, 2024)     ->  (2022, 2023, 2024, 2025)
```

**Why it would otherwise pass unnoticed.** The 1m layer physically holds
`year=2025` and `year=2026`; the seal is not maintained by absence. A widened
filter raises nothing and every figure here would simply become better-sampled
while the holdout was spent without anyone deciding to spend it.

**The failing assertion:**

```
        assert rs.WINDOW_START == dt.date(2022, 1, 1)
>       assert rs.WINDOW_END == dt.date(2024, 12, 31)
E       AssertionError: assert datetime.date(2025, 6, 30) == datetime.date(2024, 12, 31)
E        +  where datetime.date(2025, 6, 30) = rs.WINDOW_END
E        +  and   datetime.date(2024, 12, 31) = <class 'datetime.date'>(2024, 12, 31)
E        +    where <class 'datetime.date'> = dt.date
```

**9 tests in this file failed** (the constant guard, the end-to-end bar check,
the fold-window check, the fold-count check, the non-vacuity check, the channel
comparison, the ATR reuse check, the excursion-sign check and the open-price
check); **26 failed suite-wide.** `schedule.load_bars` also raised
`PermissionError` on the widened range before any assertion was reached, and
`assert_sealed` stands behind it. This module defines **no window constant of
its own** — a test asserts it defines none — so nothing here can drift from the
one seal. Reverted from a pre-mutation copy;
`git diff --exit-code -- src/timeframe/resample.py` is clean.

### 6.2 PLANTED MUTATION — the geometry comparison inverted

**The mutation.** In `sweep_population.fraction_inside`:

```
return float(np.sum(x > mult) / len(x))  ->  np.sum(x < mult)
```

**THIS MUTATION CHANGES ONLY A FRACTION — NO DISTRIBUTIONAL FIGURE.** Every
percentile of `excursion_atr`, every channel-break and wick-and-reject count,
every rejection rate, every ATR table and every fold row in this report stays
**byte-identical** under it. The mutated function still returns a number in
[0, 1] that still moves with `m` in a plausible-looking direction. The only
thing that changes is **the answer to the question this step exists to
answer** — §4.3's "2.32% of signals" becoming "97.68% of signals" — and with it
the verdict on whether the frozen stop contradicts the trigger. **It is
invisible to every other test in the file**, which is why the guard asserts an
asymmetric fixture, a monotonicity property and a quantile cross-check rather
than a single value.

**The failing assertions:**

```
        # Asymmetric about 2.25, so the two readings cannot coincide.
>       assert sp.fraction_inside(x, 2.25) == pytest.approx(0.4)
E       assert 0.6 == 0.4 ± 4.0e-07
E         comparison failed
E         Obtained: 0.6
E         Expected: 0.4 ± 4.0e-07
```

```
        exc = sp.excursion_of(f, sp.LONG)
        assert len(exc) == 1 and exc[0] == pytest.approx(2.40625, rel=1e-15)
>       assert sp.fraction_inside(exc, 2.25) == pytest.approx(1.0)
E       assert 0.0 == 1.0 ± 1.0e-06
E         comparison failed
E         Obtained: 0.0
E         Expected: 1.0 ± 1.0e-06
```

**2 tests failed** — the targeted guard and the hand-computed arithmetic test,
whose synthetic bar was deliberately built at `excursion_atr = 2.40625`, just
above the frozen multiplier, so that it also exercises this branch. Reverted
from a pre-mutation copy.

### 6.3 The Donchian exclusion convention

Guarded three ways, each failing under an off-by-one: the **window contents**
asserted element-wise on a 200-bar pseudo-random series (with an explicit
assertion that the series *contains* bars where including the current bar would
change the window minimum, or the test would prove nothing); the **first defined
index** at `period`, not `period − 1`; and the **unsatisfiability property** —
on any series, no bar's low is below the minimum of a window containing it, so
the off-by-one yields an empty population, while the correct convention finds
breaks on the same series.

### 6.4 Trigger correctness and the NEGATIVE CONTROL

Built on 200 flat bars whose true range is exactly 2.0, so ATR is exactly 2.0
and the prior-10 low is exactly 99.0, followed by one hand-specified bar:

| the bar | expected | asserted |
|---|---|---|
| low 95, close 100.5 | break **and** sweep | ✓ exactly one sweep, not a run |
| low 95, close 96 | **break, NOT sweep** | ✓ **the negative control** |
| low 99.5, close 100.2 | neither | ✓ |
| low 99.0 (tie), close 100.5 | **not** a break | ✓ strictness |
| low 95, close 99.0 (tie) | break, **not** sweep | ✓ strictness |

**The negative control is not a formality.** Dropping the second condition
converts the population from wick-and-reject into plain channel-break — roughly
doubling it, per §2 — while leaving every column plausible.

### 6.5 excursion_atr arithmetic, hand-computed

On the same fixture, with the sweep bar high 101, low 95, close 100.5, previous
close 100:

    TR            = max(101−95, |101−100|, |95−100|) = max(6, 1, 5) = 6
    ATR           = (2.0 × 13 + 6) / 14 = 32/14 = 2.285714…
    excursion     = 100.5 − 95 = 5.5
    excursion_atr = 5.5 / (32/14) = 77/32 = 2.40625      EXACTLY
    range_atr     = 6 / (32/14)   = 84/32 = 2.625        EXACTLY

All four asserted to `rel=1e-15`. Nothing is checked against another library.

### 6.6 Direction symmetry

The price axis is reflected (`p → K − p`), which swaps the roles of high and
low. Long sweeps on the original must be short sweeps on the mirror. Asserted on
a 2,000-bar random series (containing 101 sweeps) as **equality of counts in
both directions and element-wise equality of the excursion arrays and the ATR
series** — an aggregate-only match would survive a mirrored-but-misaligned
implementation.

### 6.7 The remaining tests

- **Frozen inputs pinned**: N = 10, comparison N = 20, ATR 14, m = 2.25, floor
  1.50%, timeframe 1h, minimums 200/50.
- **Warm-up is exactly 114 bars** at three lengths, no NaN ATR survives it, and
  the surviving ATR equals 2.0 exactly on the flat fixture.
- **ATR is report 19's ATR**: element-wise identical to
  `atr_profile.wilder_atr`, and the 1h ETH median reproduces report 19's
  0.8440%.
- **`fold_minimum` returns the minimum, not the mean** — asserted against a
  fixture where the two differ by an order of magnitude.
- **Fold windows**: eighteen periods, ids 1–9, none touching the seal, the
  holdout entry present in the artifact but not walked, and the warm-up ending
  before the first fold begins.
- **No double counting**: `n_signals == n_long + n_short − n_both_directions`
  on every fold row, with an assertion that two-sided bars actually occur.
- **Non-vacuity and containment** on real data: every wick-and-reject bar is
  also a channel break, and the rejection rate lies strictly in (0.3, 0.8).
- **A shorter channel admits more bars** than a longer one — a sanity property,
  not a selection.
- **Floor-binding direction**: the mirrored trap in Part D, asserted on a
  fixture straddling 1.50.
- **The firewall**, over the module's AST: no performance name as an identifier
  or non-docstring string literal; `simulate`, `src.sweep` and `src.folds.run`
  not importable; `signals` deliberately imported; **and no negative shift
  anywhere in the source**, since that is how a future bar leaks in.
- **No open price** is read, bound, or present in any loaded frame.

---

## 7. ASSUMPTIONS AND LIMITATIONS

1. **This step measures BARS, not trades.** Nothing here says a wick-and-reject
   signal is worth taking, and nothing here could. The geometry check
   establishes only that the frozen stop does not sit inside the structure the
   trigger identifies — an **internal-consistency** result, not evidence of
   any edge.

2. **The excursion is measured to the SIGNAL BAR'S OWN extreme, not to any
   subsequent low.** That is the question that was asked and it is the right
   one for consistency — the mechanism claims the wick extreme is the level
   being defended. **It is NOT a claim about how far price travels against the
   position after entry**, which would be a forward-looking quantity and is
   firewalled. A stop clearing the signal bar's extreme can still be hit on any
   later bar.

3. **Entry price is taken as the signal bar's CLOSE.** No entry mechanism has
   been specified yet; if entry is ever on the next bar, or on a retracement,
   every excursion figure shifts and this check has to be redone against the
   actual entry reference.

4. **ATR at the signal bar includes that bar's own true range**, with weight
   1/14 under Wilder smoothing. Since sweep bars are ~1.3× typical range, the
   ATR they are divided by is itself slightly inflated by the bar being
   measured. **This makes `excursion_atr` slightly conservative — it understates
   the ratio** by roughly the same small factor — so the ~2% exposure figure is
   if anything an over-estimate of the risk. Stated rather than corrected: using
   a prior-bar ATR would be a different convention and would have to be applied
   consistently everywhere.

5. **The nine folds overlap by 50%** and are a stability probe, not nine
   independent trials. The per-fold counts are population sizes, not sample
   sizes for any inference.

6. **The Donchian-20 column is one fixed comparison, not a sweep.** N = 10 is
   frozen. Nothing in this report selects between them, and the D20 figures
   should not be read as an evaluation of an alternative.

7. **`m@90%` and `m@95%` are quantiles, not proposals.** They are the arithmetic
   the brief asked for. No multiplier is recommended and m = 2.25 is unchanged.

---

## 8. WHAT THIS SETTLES, AND WHAT IT OPENS

**SETTLED.** The frozen stop geometry is **internally consistent** with the
wick-and-reject trigger at Donchian-10. A 2.25 × ATR stop clears the sweep
extreme on **97.1%–99.2%** of signals; 95% coverage arrives at
1.52–1.96 ATR, well inside the frozen value; and the sensitivity around 2.25 is
smooth with no cliff. **The concern that motivated this step does not
materialise.**

**SETTLED.** Signal count is not a constraint. The worst of eighteen fold
periods per symbol carries **570 train signals against a requirement of 200**
and **281 test signals against 50** — margins of 2.85× and 5.62×.

**MEASURED FOR THE FIRST TIME.** The rejection rate is **0.526–0.575** and is
invariant to doubling the channel length.

**OPEN QUESTIONS**, carried forward:

1. **The 1.50% floor binds on 46% of BTC signals and 29% of ETH signals.**
   This is the largest finding in the report and it was not what the step set
   out to look for. The rail was justified as a guard rail; on BTC it is closer
   to being the stop rule itself. Report 19's "does not bind in median
   conditions" is still true and still not sufficient — the BTC median clears
   the floor by only 5%. **Whether a guard rail that binds on nearly half of one
   symbol's signals is still a guard rail is a design question, not a
   measurement one**, and it is not decided here. Note that when the floor binds
   the stop is *wider* than 2.25 × ATR, so §4's coverage figures are a **lower
   bound** on realised coverage — the floor makes the geometry safer, not
   riskier.

2. **"Wick-and-reject bars are a high-volatility subset" is false as stated**
   and should not be reused as a premise. They are a high-*relative*-range
   subset (1.23–1.54× typical `range/ATR`), which is scale-free and therefore
   nearly orthogonal to the ATR level. Any argument of the form "these bars are
   volatile, therefore X about a percentage threshold" needs rechecking.

3. **Entry reference is unspecified.** §7.3: every figure in Part C assumes
   entry at the signal bar's close. The entry mechanism is the next thing that
   has to be frozen, and this check has to be rerun against it.

4. **The rejection rate's invariance to channel length is unexplained.** 0.52–0.57
   at both N = 10 and N = 20 is a stronger regularity than the step needed and
   is not accounted for by anything measured here. Noted, not pursued.

5. **Two-sided bars are counted once and not characterised.** At D10 they total
   86 / 59 / 32 per symbol across all nine train periods, at most 19 in one
   fold. A bar that sweeps and rejects both channels is
   ambiguous as a directional signal, and no rule yet says which side it takes.
   Small enough not to move any figure here; large enough to need a rule before
   signals are generated.

---

**Files.** `src/analysis/sweep_population.py` ·
`tests/test_sweep_population.py` · this report.
**Not modified:** `src/costs/`, `src/timeframe/`,
`src/analysis/rsi_breakout_profile.py`, the engine, the regime module, any
existing report.
