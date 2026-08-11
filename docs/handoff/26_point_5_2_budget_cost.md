# REPORT 26 — WHAT THE FROZEN RISK BUDGET COSTS

**Point 5, sub-point 5.2, step 3.** A MEASUREMENT. No rule is changed, no engine
file is touched, no parameter is chosen, and no alternative budget is reported —
that last would be the sweep the pre-registration exists to prevent.

**THE ORDER OF EVENTS MATTERS AND IS THE POINT.** Report 24 (`4e08e1b`) measured
the uncapped book: a median of **9** concurrent positions, a maximum of **28**,
**11,384** positions over the window. The budget was then frozen at **$120.00**
in three commits — `a323237`, `62c2d2b`, `46099a2` — **before this measurement
existed**, so the level could not be fitted to preserve statistical power. This
step applies the frozen rule and reports what it costs.

**THE ANSWER, IN ONE LINE.** The budget takes **6,021 of 11,384 positions and
skips 5,363 — a 47.11% skip rate** — leaving a book that sits at its six-position
cap on **49.14% of bars**, with median required leverage of **2.15×** against the
uncapped **3.59×**. **The skip rate is within 0.18 points of identical on all
three symbols.** Document 05 §5.2's pre-registered prediction that the surviving
population would be enriched in floor-bound trades **HELD, in direction, on all
three symbols and on 14 of 18 fold periods — but the magnitude is small: 2.78
percentage points pooled.**

> **EVERY SKIP FIGURE IN THIS REPORT IS AN UPPER BOUND.** Exits here are
> maximum-hold exits only. Under real exits, positions that stop out or reach
> target close **earlier**, free budget **earlier**, and admit signals this
> measurement skips. **The magnitude of that correction is unknowable until the
> validation design exists**, and no figure here estimates it. §9.

**The performance firewall is armed.** No expectancy, win rate, profit factor,
Sharpe, Sortino, equity curve, drawdown, `r_multiple`, `net_pnl` or `gross_pnl`
is computed, inspected, estimated or referenced. **No stop or target is
evaluated anywhere.** No bar after the entry bar is read except to locate the
max-hold exit on the funding calendar. **`src/engine/simulate.py` is not
imported and a test asserts it is unreachable** — §11.4 records why that
mattered.

**The holdout is sealed.** 2025-01-01 to 2026-07-26 has never been read. §11.5
reports the planted mutation.

---

## 1. PROVENANCE

| item | value |
|---|---|
| `git rev-parse HEAD` at measurement | **`46099a2`** — Amendment 2 to the budget pre-registration |
| module | **`src/analysis/budget_cost.py`** — alongside `sweep_population.py` (report 21) and `exposure_profile.py` (report 24) |
| tests | **`tests/test_budget_cost.py`** |
| signal population | **`src/analysis/sweep_population.py`**, report 21 at `aea6b5c` — **REUSED UNMODIFIED** |
| position table | **`src/analysis/exposure_profile.py`**, report 24 at `4e08e1b` — **REUSED UNMODIFIED** |
| sizing | `src/engine/costs.py::position_size`, called through report 24's own config |

**NO REFACTOR WAS REQUIRED AND NO LINE OF EITHER REUSED MODULE WAS CHANGED.**
`sweep_population.analysis_frame` and `exposure_profile.positions` were both
importable as-is, so this report's candidate population is byte-identical to
report 24's — which §5 asserts as a STOP condition rather than assuming.

### 1.1 The three design documents, unchanged

The rule this measurement applies must still be the rule that was frozen. All
three hashes are **asserted by test**:

| document | commit | SHA-256 |
|---|---|---|
| `docs/design/05_aggregate_risk_budget.md` | `a323237` | `d5ac7bd61323d04e75a854baf14086932470175408f5e2db4ca6f4d3afad268f` |
| `docs/design/05a_aggregate_risk_budget_amendment_1.md` | `62c2d2b` | `50da5aed3fabb86c3c7b54b41642444e50c7a7790de8dc93ab401ab53071522c` |
| `docs/design/05b_aggregate_risk_budget_amendment_2.md` | `46099a2` | `1d115df2272a4e231da41afbbd0b7c82020d0092ec2b3b483062d57c0e95f7bd` |

### 1.2 WHERE THE REFERENCE ALLOCATION LOGIC LIVES — asked, and answered plainly

> **`src/risk/budget.py` HOLDS VALUES ONLY.** Its sole function is
> `_refuse_inexact_transcription`, an import-time integrity check on the
> constants. **It gained no allocation logic, no viability check and no
> simulation** — exactly as its three prompts required. **There is nothing to
> report as a contradiction here.**

**Amendment 2's behavioural pin needed an allocation implementation, and it sits
in the TEST file**: `tests/test_risk_budget.py::_process_bar`, a per-bar counter
model of the two candidate loop orders. It has no notion of individual
positions, of exit scheduling, or of the rotation — it exists to make
exits-first and entries-first distinguishable on one bar and nothing more.

**THIS STEP WRITES ITS OWN.** `budget_cost.allocate` is the first full
implementation: a single continuous pass with a min-heap of open positions' exit
bars. **Every rule value it uses is the frozen module's object, not a copy** —
a test asserts identity (`is`, not `==`) for all eight, and separately asserts
that no numeric literal in the module equals `120.0` or `20.0`, so a
transcription cannot hide there.

---

## 2. THE RUN CONVENTION

### 2.1 One continuous pass; the budget does not reset at a fold boundary

**ONE PASS over 2022-01-05T18:00:00Z to 2024-12-31T23:00:00Z** — 26,190 bars on
a common UTC hourly grid, all three symbols, **starting from an empty book.**

> **THE BUDGET IS AN ACCOUNT PROPERTY AND IT IS CONTINUOUS.** It does not reset
> at a fold boundary, because the account does not.

**FOLDS ARE AN ATTRIBUTION OF RESULTS, NOT SEPARATE RUNS.** A position or a skip
belongs to the fold period containing its **SIGNAL BAR**, matching report 24's
convention. **A fold-independent run — one restarting with an empty book at each
boundary — would differ at fold edges**, admitting signals in the first hours of
each period that the continuous run skips, and it would also not be a thing the
account could do.

**THE FOLD PERIODS OVERLAP, SO THE PER-FOLD COUNTS SUM TO MORE THAN THE
POPULATION.** Training windows are 6 months on a 3-month step, so a bar in fold
*k*'s test period also sits in fold *k+1*'s and fold *k+2*'s training windows.
Measured membership: **6,457 positions belong to three fold periods, 2,042 to
two, 1,996 to one, and 889 to none** (they precede fold 1's train start). The
per-fold rows below therefore sum to **25,451**, not 11,384, and that identity
is asserted.

### 2.2 Maximum-hold exits only — and the two caveats that are NOT the same caveat

Exits are located on the funding calendar exactly as report 24 §5.1 does: the
close of the bar preceding the **third funding settlement strictly after entry**,
settlements at 00:00 / 08:00 / 16:00 UTC, `n = 3`, elapsed hold in [16h, 24h].
**No stop, target or outcome is evaluated anywhere.**

**CAVEAT ONE — THIS MEASUREMENT IS DETERMINISTIC, AND THE CAPPED POPULATION IS A
STRICT SUBSET OF THE UNCAPPED ONE.** Exit timestamps depend only on entry
timestamps, so the allocation walk is a pure function of the signal population.
Two runs are byte-identical, asserted by test.

**CAVEAT TWO — THE REAL BACKTEST WILL HAVE NEITHER PROPERTY.** Document 05 §6
accepts path dependence explicitly: under real exits a stop-out frees its slot
hours before a max-hold exit would, so **the traded population becomes a
function of realised outcomes** and is not a subset of anything knowable in
advance.

> **THESE ARE TWO DIFFERENT CAVEATS AND THEY MUST NOT BE MERGED.** The first is
> a property of this measurement that makes it reproducible. The second is a
> property of the system that makes this measurement an upper bound. A reader
> who collapses them concludes that the capped population is knowable in
> advance, which is exactly what document 05 §6.1 says it is not.

### 2.3 The rule as implemented

Read from `src/risk/budget.py`; nothing retyped:

| | value | source |
|---|---|---|
| aggregate budget | **$120.00** | `MAX_AGGREGATE_OPEN_RISK_USD` |
| risk unit | **$20.00** | `RISK_PER_TRADE_USD` |
| slots | **6** | `FULL_SIZE_POSITIONS` |
| charging basis | **nominal** | `BUDGET_CHARGES` (Amendment 1 Rule B) |
| intra-bar order | **exits before entries** | `INTRA_BAR_ORDER` (Amendment 2 Rule C) |
| tie-break | **cyclic rotation by bar timestamp** | `TIE_BREAK_RULE`, `SYMBOL_ROTATION` (Amendment 1 Rule A) |

**A HARD CAP OF SIX CONCURRENT FULL-SIZE POSITIONS WITH ARRIVAL-ORDER SKIP**,
implemented as that. **The partial-allocation branch was taken 0 times** — a
counter, asserted zero, not an argument.

---

## 3. SIGNALS, TAKEN, SKIPPED — the headline

**THE POPULATION IS NAMED IN EVERY COUNT BELOW.** "Signals" means the **traded
candidate population**: bars carrying exactly one directional wick-and-reject
trigger, two-sided bars already excluded by thesis §4.1. It is report 24's
11,384-position population, identical row for row.

### 3.1 Pooled and per symbol, whole window

| population | signals | **taken** | **skipped** | **skip rate** |
|---|---:|---:|---:|---:|
| BTCUSDT | 3,735 | **1,973** | **1,762** | **47.18%** |
| ETHUSDT | 3,715 | **1,963** | **1,752** | **47.16%** |
| SOLUSDT | 3,934 | **2,085** | **1,849** | **47.00%** |
| **POOLED** | **11,384** | **6,021** | **5,363** | **47.11%** |

**AGAINST REPORT 24'S UNCAPPED FIGURES, SIDE BY SIDE:** the uncapped run took all
11,384. **The budget removes 5,363 positions — 47.11% of the population — and
that is the cost of the rule at this capital.**

**`taken + skipped` equals report 24's count exactly, per symbol and pooled.**
Asserted as a **STOP condition**: a discrepancy would mean the two populations
diverged and every skip rate here would be a ratio of two different things while
still looking entirely reasonable. **No discrepancy.**

### 3.2 SKIP RATE BY SYMBOL — the rotation's neutrality, measured not assumed

**Amendment 1 Rule A is neutral by construction over bars** — each symbol holds
each of the three priority ranks on exactly one bar in three, asserted here on
the real grid to within 0.1% at every rank. **Whether that produced equal skip
rates over this finite window is a different question, and it is empirical.**

> **IT DID. The three skip rates span 0.18 percentage points: 47.18% / 47.16% /
> 47.00%.** The spread is smaller than the difference in the symbols' own signal
> counts (SOL carries 199 more signals than ETH), and no symbol is
> systematically starved.

**This is the outcome document 05 §2.5 required of the tie-break and could not
guarantee**, since neutrality over bars does not imply neutrality over
contested bars. The measurement says the two coincided here. **It is not a
guarantee for another window.**

### 3.3 Per fold — pooled

| fold | period | signals | taken | skipped | **skip rate** |
|---:|---|---:|---:|---:|---:|
| 1 | train | 1,928 | 1,025 | 903 | 46.84% |
| 1 | test | 884 | 500 | 384 | **43.44%** |
| 2 | train | 1,851 | 1,018 | 833 | 45.00% |
| 2 | test | 885 | 485 | 400 | 45.20% |
| 3 | train | 1,769 | 985 | 784 | 44.32% |
| 3 | test | 843 | 491 | 352 | **41.76%** |
| 4 | train | 1,728 | 976 | 752 | 43.52% |
| 4 | test | 906 | 495 | 411 | 45.36% |
| 5 | train | 1,749 | 986 | 763 | 43.62% |
| 5 | test | 977 | 519 | 458 | 46.88% |
| 6 | train | 1,883 | 1,014 | 869 | 46.15% |
| 6 | test | 981 | 501 | 480 | 48.93% |
| 7 | train | 1,958 | 1,020 | 938 | 47.91% |
| 7 | test | 981 | 503 | 478 | 48.73% |
| 8 | train | 1,962 | 1,004 | 958 | 48.83% |
| 8 | test | 1,075 | 517 | 558 | **51.91%** |
| 9 | train | 2,056 | 1,020 | 1,036 | **50.39%** |
| 9 | test | 1,035 | 516 | 519 | 50.14% |

**THE SKIP RATE RISES ACROSS THE WINDOW — 41.76% at its lowest (fold 3 test) to
51.91% at its highest (fold 8 test)** — and the reason is visible in the same
table: **the taken count is almost flat** (976–1,025 per training period) **while
the signal count rises** (1,728 → 2,056). **The budget delivers a roughly
constant number of trades per unit time and the skip rate is whatever the signal
supply makes it.** That is what a hard concurrency cap does, and it is worth
stating plainly: the cap converts a variable signal supply into a near-constant
trade rate.

### 3.4 Per symbol per fold — taken and skipped

| symbol | period | F1 | F2 | F3 | F4 | F5 | F6 | F7 | F8 | F9 |
|---|---|---|---|---|---|---|---|---|---|---|
| BTCUSDT | train, taken / skipped | 316 / 291 | 335 / 266 | 332 / 266 | 323 / 254 | 339 / 251 | 333 / 286 | 332 / 309 | 330 / 321 | 339 / 346 |
| ETHUSDT | train, taken / skipped | 328 / 286 | 324 / 272 | 323 / 256 | 331 / 241 | 331 / 232 | 347 / 262 | 340 / 311 | 315 / 324 | 323 / 338 |
| SOLUSDT | train, taken / skipped | 381 / 326 | 359 / 295 | 330 / 262 | 322 / 257 | 316 / 280 | 334 / 321 | 348 / 318 | 359 / 313 | 358 / 352 |
| BTCUSDT | test, taken / skipped | 171 / 128 | 161 / 138 | 162 / 116 | 177 / 135 | 156 / 151 | 176 / 158 | 154 / 163 | 185 / 183 | 165 / 160 |
| ETHUSDT | test, taken / skipped | 162 / 129 | 161 / 127 | 170 / 114 | 161 / 118 | 186 / 144 | 154 / 167 | 161 / 157 | 162 / 181 | 155 / 180 |
| SOLUSDT | test, taken / skipped | 167 / 127 | 163 / 135 | 159 / 122 | 157 / 158 | 177 / 163 | 171 / 155 | 188 / 158 | 170 / 194 | 196 / 179 |

Per-symbol per-fold skip rates run **40.14%** (ETH, fold 3 test) to **53.73%**
(ETH, fold 9 test). **No symbol holds the extreme in more than one fold**, which
is the per-cell form of §3.2's finding.

---

## 4. FLOOR-BINDING COMPOSITION — the pre-registered prediction, adjudicated

**Document 05 §5.2 named this as a required output of this step and predicted a
direction in advance:**

> *"Signals cluster in high-volatility periods, so a full book preferentially
> skips high-ATR trades — precisely the trades where the 1.50% stop floor does
> not bind. The surviving population is therefore expected to be ENRICHED in
> floor-bound trades relative to the uncapped population."*

Measured with **report 21's own `floor_binding_fraction`** on both
sub-populations, so the figure is an identity rather than a re-derivation.

### 4.1 The answer

| population | floor binds on ALL | on **TAKEN** | on **SKIPPED** | **taken − skipped** |
|---|---:|---:|---:|---:|
| BTCUSDT | 45.94% | **47.64%** | 44.04% | **+3.60 pp** |
| ETHUSDT | 29.34% | **31.64%** | 26.77% | **+4.87 pp** |
| SOLUSDT | 3.08% | **3.17%** | 2.97% | **+0.19 pp** |
| **POOLED** | 25.71% | **27.02%** | 24.24% | **+2.78 pp** |

> ### THE PREDICTION HELD — IN DIRECTION, ON EVERY SYMBOL. THE MAGNITUDE IS
> ### SMALL.
>
> **Direction: correct on all three symbols, on 14 of 18 pooled fold periods,
> and on 35 of 54 per-symbol per-fold cells.** The surviving population is
> enriched in floor-bound trades exactly as pre-registered.
>
> **Magnitude: 2.78 percentage points pooled**, against a floor-binding rate
> that swings from **0.0% to 93.9% across folds** (report 24 §4.3). **The
> selection effect is an order of magnitude smaller than the fold-to-fold
> variation it sits inside.**

**WHY THE EFFECT IS WEAKER THAN THE ARGUMENT SUGGESTED, stated as an
observation and not as a rescue.** The mechanism predicted is real — clustered
signals are preferentially skipped, and clustering correlates with volatility —
but report 21 §5.1 established that **wick-and-reject bars are a high-RELATIVE-
range subset, not a high-ATR-LEVEL subset**, and that the trigger's selection
criterion is *"scale-free, and therefore nearly orthogonal to the ATR LEVEL,
which is what a percentage floor compares against."* **The same orthogonality
that made the floor bind equally on signals and on all bars also weakens the
link between "arrives in a cluster" and "clears the floor".** The closing record
§3.6's transferable rule — *"any argument of the form 'these bars are volatile,
therefore X about a percentage threshold' is UNSOUND"* — applies to document 05
§5.2's own argument, and the measurement is the check.

**SOLUSDT is nearly unaffected (+0.19 pp)** because its floor binds on 3% of
signals: there is almost no floor-bound stratum for the cap to enrich.

### 4.2 Per fold — pooled floor binding on both sub-populations

| fold | period | all | **taken** | **skipped** | delta (pp) |
|---:|---|---:|---:|---:|---:|
| 1 | train | 4.56% | 5.37% | 3.65% | +1.72 |
| 1 | test | 37.78% | 39.00% | 36.20% | +2.80 |
| 2 | train | 19.99% | 21.32% | 18.37% | +2.95 |
| 2 | test | 28.14% | 27.22% | 29.25% | **−2.03** |
| 3 | train | 32.96% | 33.20% | 32.65% | +0.55 |
| 3 | test | 48.75% | 50.10% | 46.88% | +3.22 |
| 4 | train | 38.19% | 38.73% | 37.50% | +1.23 |
| 4 | test | 65.45% | 68.28% | 62.04% | +6.24 |
| 5 | train | 57.40% | 59.23% | 55.05% | +4.18 |
| 5 | test | 37.97% | 39.11% | 36.68% | +2.43 |
| 6 | train | 51.19% | 53.35% | 48.68% | +4.67 |
| 6 | test | 22.02% | 21.56% | 22.50% | **−0.94** |
| 7 | train | 29.98% | 30.49% | 29.42% | +1.07 |
| 7 | test | 24.36% | 23.06% | 25.73% | **−2.67** |
| 8 | train | 23.19% | 22.31% | 24.11% | **−1.80** |
| 8 | test | 18.70% | 21.86% | 15.77% | +6.09 |
| 9 | train | 21.40% | 22.45% | 20.37% | +2.08 |
| 9 | test | 18.94% | 19.96% | 17.92% | +2.04 |

**Fourteen of eighteen periods are positive; four are negative** (fold 2 test,
fold 6 test, fold 7 test, fold 8 train), by 0.94 to 2.67 points. **The
prediction is directional and it is not universal**, and the four exceptions are
reported rather than averaged away.

**WHAT THIS MEANS FOR KILL CONDITION (d)**, stated and not resolved: thesis §7's
condition (d) stratifies on floor-binding and requires the advantage to survive
among **non**-floor-bound trades. **The cap shifts the mix toward floor-bound
trades by ~2.8 points, which thins the non-floor-bound stratum the condition is
evaluated on.** Whether that thinning matters is a question for the validation
design; this report measures the shift and makes no claim about it.

---

## 5. CONCURRENCY AND EXPOSURE UNDER THE CAP

All figures on the same 26,190-bar grid as report 24, so every row is directly
comparable.

### 5.1 The book, capped against uncapped

| quantity | | **max** | P99 | P95 | P90 | median | mean |
|---|---|---:|---:|---:|---:|---:|---:|
| **positions open** | **capped** | **6** | 6 | 6 | 6 | **5** | **4.90** |
| | uncapped (report 24) | 28 | 19 | 15 | 14 | 9 | 8.91 |
| **notional open (USDT)** | **capped** | **7,192.74** | 7,148.90 | 6,800.86 | 6,441.71 | **4,290.73** | **4,233.61** |
| | uncapped | 27,045.20 | 17,826.90 | 14,257.18 | 12,641.37 | 7,182.00 | 7,624.06 |
| **required leverage** | **capped** | **3.596×** | 3.574× | 3.400× | 3.221× | **2.145×** | **2.117×** |
| | uncapped | 13.523× | 8.913× | 7.129× | 6.321× | 3.591× | 3.812× |
| **nominal risk open (USDT)** | **capped** | **120.00** | 120.00 | 120.00 | 120.00 | **100.00** | **98.04** |
| | uncapped | 560.00 | 380.00 | 300.00 | 280.00 | 180.00 | 178.24 |

**The maximum is the cap, exactly**: 6 positions, $120.00 of nominal risk. **The
median book carries 5 positions and $100.00 of nominal risk — 5.0% of the
account** — against the uncapped median of 9 and $180.00.

### 5.2 Fraction of bars at each concurrency level

| level | 0 | 1 | 2 | 3 | 4 | 5 | **6 (at the cap)** |
|---:|---:|---:|---:|---:|---:|---:|---:|
| **bars** | 129 | 394 | 1,199 | 2,768 | 4,079 | 4,752 | **12,869** |
| **fraction** | 0.49% | 1.50% | 4.58% | 10.57% | 15.57% | 18.14% | **49.14%** |

> **THE BOOK IS AT ITS CAP ON 49.14% OF ALL BARS IN THE WINDOW.** Just under
> half the time, the next signal on any symbol is skipped. That is the same fact
> as the 47.11% skip rate, seen from the timeline rather than from the
> population.

Bars occupied: **99.51%** (uncapped 99.84%). Empty on 129 bars against 43.

### 5.3 Per-symbol concurrency under the cap

| symbol | **max** | P99 | P95 | P90 | median | mean | bars occupied |
|---|---:|---:|---:|---:|---:|---:|---:|
| BTCUSDT | 5 | 4 | 3 | 3 | 2 | **1.61** | 86.73% |
| ETHUSDT | 5 | 4 | 3 | 3 | 2 | **1.60** | 86.03% |
| SOLUSDT | 6 | 4 | 3 | 3 | 2 | **1.70** | 88.59% |

Uncapped these were maxima of 12 / 11 / 10 and means of 2.92 / 2.90 / 3.09
(report 24 §6.1). **No per-symbol cap exists and none is implied** — SOLUSDT
reaches 6, meaning the whole book was SOL on at least one bar.

### 5.4 DIRECTIONAL COMPOSITION — the cap made one-sidedness MORE common

| | capped | uncapped (report 24 §7.4) |
|---|---:|---:|
| occupied bars | 26,061 | 26,147 |
| **bars where ALL open positions share one direction** | **8,441** | 5,362 |
| **fraction of occupied bars** | **32.39%** | **20.51%** |

> **THE CAP RAISED THE ONE-SIDED FRACTION BY 11.9 POINTS.** This is arithmetic
> rather than a change in the market: with fewer positions open, the chance that
> all of them happen to share a direction is mechanically higher — six coins
> land the same way far more often than nine do.

**IT IS REPORTED BECAUSE IT RUNS AGAINST THE INTUITION THAT A SMALLER BOOK IS A
SAFER ONE.** The book is smaller in every exposure measure and **more
concentrated in direction**. Correlation risk is a 5.2 input and no correlation
quantity has been computed anywhere in this project; this is a composition count
and nothing more.

### 5.5 The single worst bar under the cap

| field | value |
|---|---|
| **timestamp (bar open, UTC)** | **2023-07-31T20:00:00Z** |
| **positions open** | **6** — the cap |
| — BTCUSDT | **5** positions, $5,993.95 |
| — ETHUSDT | **1** position, $1,198.79 |
| — SOLUSDT | 0 |
| **total notional** | **$7,192.74** |
| **required leverage** | **3.5964×** |
| direction | **6 long, 0 short — entirely one-sided** |
| nominal risk open | $120.00 |

Report 24's uncapped worst bar was 2024-07-15T22:00Z at 28 positions and
13.52×. **Five of the six positions are BTCUSDT, at the per-position notional
ceiling of $1,198.79** — the floor-bound maximum established in report 24 §6.5.

---

## 6. HOW OFTEN EACH RULE ACTUALLY DECIDED SOMETHING

**The diagnostics that make the rules auditable rather than assumed.** Without
these, a rule that never fired and a rule that fired constantly look identical
in the output.

| diagnostic | count | as a fraction |
|---|---:|---|
| bars carrying at least one signal | **7,871** | 30.05% of 26,190 bars |
| **bars carrying 2+ simultaneous signals (contested)** | **2,746** | **34.89% of signal bars** |
| signals arriving on a contested bar | 6,259 | 54.98% of all signals |
| **contested bars with fewer free slots than contenders — RULE A CHANGED AN OUTCOME** | **1,739** | **63.33% of contested bars; 22.09% of signal bars** |
| signals on bars where Rule A decided | 4,068 | 35.73% of all signals |
| **bars carrying both an exit and a signal** | **861** | **10.94% of signal bars** |
| **positions TAKEN under Rule C that entries-first would have SKIPPED** | **902** | **14.98% of all 6,021 taken positions** |
| bars on which Rule C changed at least one outcome | 710 | 9.02% of signal bars |
| signals arriving at an exactly full budget | **5,363** | = every skip |
| **partial allocations** | **0** | Amendment 1 Rule B, asserted |

### 6.1 What each number says

**RULE A IS NOT DECORATIVE.** It decided the outcome on **1,739 bars** — nearly
two thirds of contested bars. Had it been fixed priority (BTC > ETH > SOL),
those are the bars on which SOLUSDT would have lost, systematically, and
document 05's two-of-three confirmation requirement would have been decided by
allocation. **This is the measurement that retires "the tie-break probably does
not matter".**

**RULE C BOUGHT 902 POSITIONS — 14.98% OF EVERYTHING TAKEN.** Had those 902 been
skipped and nothing else changed, the skip rate would read **55.03%** instead of
47.11% — **a 7.9-point difference produced entirely by loop order.** *(That
one-line arithmetic is illustrative: it applies the local per-bar figure
globally, which a real entries-first run would not do — see below.)* Amendment 2
§2.3 predicted the direction and refused to defer the choice to the
implementation on exactly this ground; the magnitude is now measured.

**THE RULE C FIGURE IS A LOCAL COUNTERFACTUAL AND IS LABELLED AS ONE.** It counts,
at each bar, the takes beyond what was free **before** that bar's exits were
released, holding the rest of the run fixed. **A full entries-first run would
diverge globally** — every earlier difference changes what is open later — and it
is not run, because producing a complete second set of figures for a rejected
rule is not this report's job. The local figure is exact for what it measures:
the immediate cost of the ordering, bar by bar.

**EVERY SKIP HAPPENED AT AN EXACTLY FULL BUDGET.** 5,363 skips, 5,363 signals
arriving at zero remaining, and **zero partial allocations.** This is Amendment 1
Rule B's inertness claim, confirmed on the real population: the allocation was
always exactly $20.00 or exactly $0.00, and the remaining budget was a whole
multiple of $20.00 at every bar.

---

## 7. SAME-SYMBOL OPPOSITE-DIRECTION OVERLAP — the hedge-mode evidence

**On how many bars does one symbol carry BOTH an open long and an open short?**

| symbol | | bars both open | **fraction of bars** | bars long open | bars short open |
|---|---|---:|---:|---:|---:|
| BTCUSDT | **capped** | **6,424** | **24.53%** | 14,385 | 14,754 |
| | uncapped | 12,152 | 46.40% | 18,429 | 18,628 |
| ETHUSDT | **capped** | **6,483** | **24.75%** | 13,906 | 15,109 |
| | uncapped | 11,828 | 45.16% | 18,254 | 18,498 |
| SOLUSDT | **capped** | **6,930** | **26.46%** | 15,023 | 15,110 |
| | uncapped | 12,633 | 48.24% | 18,938 | 19,091 |

> ### THE FIGURE IS NOT ZERO. IT IS ROUGHLY A QUARTER OF ALL BARS, ON EVERY
> ### SYMBOL, EVEN UNDER THE CAP.
>
> **THE HEDGE-MODE DECISION WAS NECESSARY, NOT MERELY PRUDENT.**

Report 25 §5.1 established that under **one-way mode** an opposite-direction
signal **offsets** an open position rather than opening a trade. **On 24.5–26.5%
of bars — one bar in four — this strategy holds a long and a short on the same
symbol simultaneously.** Under one-way mode those positions could not coexist:
each opposing entry would have partially or wholly closed the other, converting
a signal into an unrelated exit.

**The cap roughly halves the overlap** (46–48% uncapped → 24.5–26.5% capped),
because a smaller book is less likely to hold both sides at once. **It does not
come close to eliminating it.** Had the figure been zero, hedge mode would have
been a harmless precaution; at a quarter of all bars it is load-bearing, and
`POSITION_MODE = "hedge"` is doing real work rather than reserving an option.

---

## 8. PROJECTED OUT-OF-SAMPLE TRADE COUNTS

**AN EXTRAPOLATION, NOT A MEASUREMENT. NO SEALED DATA WAS READ.** The figure is
the in-sample taken-position rate multiplied by a count of hours between two
dates already published in `folds.json` and `schedule.py`. **The seal forbids
reading the holdout's content, not knowing how long it is.**

The holdout spans **2025-01-01 to 2026-07-26 inclusive = 572 days = 13,728
hourly bars**, against 26,190 in-sample bars.

| symbol | taken in sample | rate per bar | **projected over the holdout** |
|---|---:|---:|---:|
| BTCUSDT | 1,973 | 0.07533 | **≈ 1,034** |
| ETHUSDT | 1,963 | 0.07495 | **≈ 1,029** |
| SOLUSDT | 2,085 | 0.07961 | **≈ 1,093** |
| **total** | **6,021** | — | **≈ 3,156** |

**Against the 50-trade out-of-sample minimum: roughly 20× on every symbol.**

**THE ASSUMPTION, STATED.** This rests on **signal density being stationary**
between the two periods. **Nothing in this project supports that assumption and
nothing here tests it** — the holdout is sealed, which is precisely why the
figure must be projected rather than counted. §3.3 measured signal supply rising
across the in-sample window (1,728 → 2,056 per training period), so stationarity
is already doubtful *within* the window. **If density rises further, the taken
count barely moves** — §3.3's finding is that the cap delivers a near-constant
trade rate — **so the projection is more robust than the assumption it rests on**,
which is a property of the cap rather than a defence of the assumption.

---

## 9. THE 200 / 50 ADEQUACY THRESHOLDS — reported with their caveat

> **DOCUMENT 05 §6.2 STATES THAT THESE THRESHOLDS WERE ESTABLISHED ON THE
> UNCAPPED POPULATION AND DO NOT DESCRIBE THE TRADED POPULATION UNDER THIS
> RULE.** They are reported here **as a reference point only.**

| population | minimum | worst cell, **capped taken** | ratio |
|---|---:|---:|---:|
| BTCUSDT train | 200 | **316** (fold 1) | 1.58× |
| ETHUSDT train | 200 | **315** (fold 8) | 1.57× |
| SOLUSDT train | 200 | **316** (fold 5) | 1.58× |
| BTCUSDT test | 50 | **154** (fold 7) | 3.08× |
| ETHUSDT test | 50 | **154** (fold 6) | 3.08× |
| SOLUSDT test | 50 | **157** (fold 4) | 3.14× |

**Uncapped, report 24 §3.4's worst cells were 563 train and 278 test.** The cap
roughly halves both, and the margin over the thresholds falls from 2.82× / 5.56×
to **1.57× / 3.08×**.

> **NO CLAIM IS MADE THAT CLEARING THESE ESTABLISHES ADEQUACY.** The thresholds
> were derived against a population that does not exist under this rule, and
> under real exits the traded population is path-dependent (§2.2) so it is not
> even fixed. **Whether 315 trades per training fold is adequate is a validation
> design question**, and this table is a reference point, not an answer.

---

## 10. EVERY SKIP FIGURE IS AN UPPER BOUND

> **THE 47.11% SKIP RATE IS AN UPPER BOUND, AND SO IS EVERY PER-FOLD AND
> PER-SYMBOL FIGURE DERIVED FROM IT.**

**THE REASON, IN ONE SENTENCE.** Every position here runs its full maximum hold
of 17–24 hours, because no stop and no target is evaluated; **a real position
that stops out at hour 3 frees its $20.00 fourteen to twenty-one hours earlier
and admits a signal this measurement skips.**

**THE DIRECTION IS CERTAIN AND THE MAGNITUDE IS NOT.** Real exits can only occur
at or before the max hold, never after it, so the real skip rate is **at or
below** 47.11%. **How far below is unknowable at this commit**: it depends on
stop and target hit rates, which are firewalled until the validation design is
committed, and no figure in this report estimates them.

**WHAT THAT DOES AND DOES NOT LICENCE.** It licenses reading 47.11% as a
worst-case. **It does not license assuming the real figure is much lower** — the
holding-time distribution under real exits is exactly the quantity Point 4's
§2.1 failure warns about being manufactured by the rule that measures it, and
nothing here is entitled to guess it.

**A SECOND, SMALLER UPPER-BOUND EFFECT, carried from report 24 §2.2:** notional
figures remain unquantised, so open-notional and required-leverage figures in §5
are at or above what an exchange would accept, by 0.21% / 1.26% / 0.67%
(BTC / ETH / SOL). **The skip counts are unaffected** — Amendment 1 Rule B
charges the nominal $20.00, so flooring cannot change who is taken.

---

## 11. VERIFICATION

### 11.1 SYNTHETIC POSITIVE CONTROL — the take/skip sequence, hand-computed

**THE CONSTRUCTION**, on bars 0–10 from 2022-01-01T00:00:00Z. Exit bars are
hand-chosen to place the two cases the rules exist for; they are not max-hold
exits, because this control tests the **allocation** and not the funding
calendar.

| bar | construction | hand-computed result |
|---:|---|---|
| 0–5 | one signal each; the book fills to exactly SIX | **TAKEN × 6** |
| 6 | one signal, book full, no exit | **SKIPPED** |
| 7 | one signal **and** one exit at the same close | **TAKEN** — Rule C releases before evaluating; entries-first would skip it |
| 10 | **THREE** signals, **ONE** freed slot; rotation 1 → ETH, SOL, BTC | **ETH TAKEN, SOL and BTC SKIPPED** — Rule A decided |

**Asserted element by element** against
`[T, T, T, T, T, T, F, T, T, F, F]` — not as counts — plus the per-bar
diagnostics at each of bars 5, 6, 7 and 10. **PASSES.**

Three further controls: a seventh concurrent signal is asserted **skipped and
never partially allocated**; the rotation is asserted to pick the correct
winner at each of the three rotation values; and the Rule C gain is asserted to
be exactly one position on a fixture built to contain exactly one.

### 11.2 SYNTHETIC NEGATIVE CONTROL

An empty candidate frame yields **zero taken, zero skipped, zero bars, an
all-zero occupancy timeline** in both count and notional. Separately, a
300-bar flat series — where `low == lower` and `high == upper` on every bar and
all four comparisons are strict — is asserted to produce **zero signals and zero
candidate positions**, so the emptiness is reachable from real code and not only
from an empty frame. **PASSES.**

### 11.3 INVARIANTS ON THE REAL RUN — asserted at every bar

| invariant | result |
|---|---|
| concurrency never exceeds **6** | **holds**; the maximum is exactly 6 |
| open nominal risk never exceeds **$120.00**, never negative | **holds**; the maximum is exactly $120.00 |
| remaining budget is always an exact multiple of **$20.00** | **holds** at every bar |
| **the partial-allocation branch is never taken** | **holds — the counter is 0** |
| `taken + skipped` == report 24's uncapped count, per symbol and pooled | **holds exactly**: 3,735 / 3,715 / 3,934 and 11,384 |
| every skip occurred at an exactly full budget | **holds**: 5,363 skips, 5,363 full-budget arrivals |

The guard is asserted to be able to **refuse**: a planted partial-allocation
count and a planted seven-position book each raise.

### 11.4 RULE A NEUTRALITY, DETERMINISM, AND THE FORBIDDEN IMPORT

**RULE A NEUTRALITY ON REAL DATA.** On any three consecutive real bars each
symbol holds each of the three priority ranks exactly once (checked across the
window); across all 26,190 bars each symbol holds each rank on **within 0.1% of
one bar in three**.

**DETERMINISM.** Two full runs produce identical position tables, identical
diagnostics, identical per-symbol figures, identical worst bar and identical
projection. Asserted by frame comparison.

**`src/engine/simulate.py` IS NOT REACHABLE**, asserted over the import graph
and over the module's identifiers, and transitively over every module this one
imports. **This mattered concretely rather than theoretically:** simulate's
portfolio mode carries *"one open position per symbol, no pyramiding"* — which
would have capped each symbol at 1 against the 5, 5 and 6 measured in §5.3 — and
a margin refusal at `max_leverage = 3.0`, which **would have bound**: §5.1's
maximum required leverage under the budget is **3.5964×**, and §11.6 measures
that 16.14% of bars exceed 3.0×. Either would have silently changed the traded
population.

### 11.5 PLANTED MUTATION — the holdout seal

**THE MUTATION.** In `src/timeframe/resample.py`, both halves of the filter
widened at once: `WINDOW_END` to 2025-06-30 and `ALLOWED_YEARS` to include 2025.

**RESULT: planted, confirmed failing, reverted.**

| scope | outcome under the mutation |
|---|---|
| `tests/test_budget_cost.py` | **11 tests fail** (1 failure + 10 errors) |
| whole suite | **56 fail** (35 failures + 21 errors) |
| first assertion to fire | `assert rs.WINDOW_END == dt.date(2024, 12, 31)` → `datetime.date(2025, 6, 30) == datetime.date(2024, 12, 31)` |

`git diff --stat src/timeframe/resample.py` is **empty** after the revert. The
module defines no window constant of its own — asserted over its AST — and
inherits the seal through `sweep_population` and `exposure_profile`. The
out-of-sample projection in §8 reads two **dates** and no bar.

### 11.6 The firewall, and the remaining tests

**THE TWELVE-NAME AST GUARD** from report 25 — the nine from reports 19–21 plus
`drawdown`, `sortino` and `gross_pnl` — is carried over this module's
identifiers and non-docstring string literals. **No forward shift** (`.shift(-`)
appears; `solve_target`, `stop_geometry`, `was_hit`, `exit_reason`, `trade_pnl`,
`summarize` and `target_price` appear nowhere; the engine surface touched is
asserted to be within `{position_size, CostConfig}`.

**CONSTANTS PROVENANCE.** All eight rule values are asserted to be the frozen
module's **objects** (`is`, not `==`), and no numeric literal in the module
equals 120.0 or 20.0. The three design-document hashes are asserted.

**FULL SUITE.**

| | tests |
|---|---:|
| baseline at `46099a2` | **839 passing** |
| new in `tests/test_budget_cost.py` | **+29** |
| **total** | **868 passing / 868** |

---

## 12. WHAT CONTRADICTS A FROZEN DOCUMENT

**One item, and it contradicts nothing frozen — it confirms a report-25 finding
in a place that had not been checked.**

### 12.1 `max_leverage = 3.0` WOULD STILL BIND UNDER THE BUDGET

Report 25 §10.1 established that `costs.CostConfig.max_leverage = 3.0` is *"NOT
a probed exchange constraint — an unmeasured placeholder"*, 33–50× more
restrictive than the venue's tier-1 cap. **It might reasonably have been assumed
that a $120 budget would bring the book inside it. It does not.**

| | value |
|---|---:|
| maximum required leverage under the cap | **3.5964×** |
| bars above 3.0× | **4,228 — 16.14% of the window** |
| bars above 3.5× | 826 — 3.15% |
| bars above 2.0× | 14,649 — 55.93% |

**Six floor-bound positions at the $1,198.79 per-position ceiling are $7,192.74
of notional, which is 3.596× on $2,000** — the arithmetic report 25 §6.3 gives,
now confirmed as reachable and reached. **So the two constraints are not
redundant and the budget does not subsume the leverage cap:** the budget caps
**nominal risk**, `max_leverage` caps **notional**, and the two relate only
through the stop width, which varies per trade.

**NOTHING IS CHANGED AND NOTHING IS PROPOSED.** `costs.py` is untouched and
`max_leverage` still reads 3.0. Its disposition remains explicitly out of scope,
as report 25 §10.2 recorded. **What this adds is that the question cannot be
closed by pointing at the budget** — a system running this rule would still trip
the engine's own margin refusal on one bar in six.

### 12.2 A TEST FROM STEP 2 WAS NARROWED, DELIBERATELY AND ON THE RECORD

`tests/test_risk_budget.py::test_nothing_is_wired_in_yet` was written at the
step-2 pre-registration to enforce *"NOTHING IS WIRED IN. No engine file imports
`src/risk`. That wiring is 5.3's work"*, and it enforced it by refusing **every**
importer anywhere under `src/`.

**THIS REPORT'S MODULE IMPORTS `src/risk/budget.py`, AND WAS REQUIRED TO** — its
brief says *"Read the values from `src/risk/budget.py`. DO NOT re-derive or
re-type them"*, which is what stops a second copy of a frozen number existing
(§1.2). **A measurement module reading the constants is the opposite of wiring:
it changes no execution path and no engine behaviour.**

**THE ASSERTION WAS THEREFORE NARROWED TO WHAT IT WAS WRITTEN TO MEAN** — no
engine file, no `src/sweep`, no `src/folds` — **and kept with teeth**: the
permitted set is an explicit allowlist naming exactly one module and its reason,
so any other importer appearing anywhere still fails. **`src/engine` remains
entirely unwired and the engine assertion is separate and unconditional.**

**IT IS RECORDED HERE RATHER THAN LOOSENED SILENTLY**, because a test narrowed
to let one's own new code pass is the failure mode that makes a suite
decorative, and the only defence is stating which assertion changed and why.

### 12.3 Nothing else disagrees

- The candidate population is report 24's, exactly: 3,735 / 3,715 / 3,934.
- Floor-binding on the full population reproduces report 24 §4.2's rates.
- Document 05 §5.2's prediction held in direction (§4.1) — a frozen prediction
  confirmed, not contradicted.
- Amendment 1 Rule B's inertness claim and Amendment 2 Rule C's
  more-restrictive claim both hold on the real population (§6.1).
- The thesis, its amendment, the closing record and reports 24 and 25 are
  otherwise untouched.

---

## 13. WHAT THIS HANDS FORWARD — no decision is made here

1. **The budget costs 47.11% of signals at max hold, and that is an upper
   bound.** 6,021 positions survive.
2. **The skip rate is symbol-neutral to within 0.18 points**, so the rotation
   did in practice what it guarantees in principle.
3. **The floor-binding enrichment is real and small: +2.78 points pooled**,
   inside a stratum that swings 0–94% across folds. Kill condition (d) is
   evaluated on a slightly thinner non-floor-bound stratum than the uncapped
   population would have given it.
4. **Rule A decided 1,739 bars and Rule C bought 902 positions.** Neither rule
   is decorative, and the pre-registration of both was worth its cost.
5. **Hedge mode is load-bearing**: one bar in four carries a long and a short on
   the same symbol.
6. **The engine's `max_leverage = 3.0` still binds on 16.14% of bars**, so the
   budget did not close that question.
7. **~3,156 projected out-of-sample positions** against a 50-trade minimum,
   under a stated stationarity assumption the window itself already strains.

---

**Files.** `src/analysis/budget_cost.py` · `tests/test_budget_cost.py` · this
report.
**Not modified:** `src/risk/budget.py` · every engine file — `max_leverage`
still reads 3.0 · `src/analysis/exposure_profile.py` ·
`src/analysis/sweep_population.py` · `config/contracts_cache.json` · every
frozen document numbered 22, 22a, 23, 24, 25, 05, 05a and 05b.
**Holdout:** sealed, unspent, re-verified by planted mutation.
**Firewall:** armed, AST-guarded, twelve names, no trade simulated, no outcome
evaluated, `simulate` unreachable.
