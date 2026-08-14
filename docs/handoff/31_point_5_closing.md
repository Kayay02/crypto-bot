# POINT 5 — CLOSING RECORD AND HANDOFF

## 1. STATUS AND VERDICT

**POINT 5 (RISK AND POSITION SIZING) IS CLOSED.** It produced two frozen
pre-registrations with three amendments between them, seven measurement reports,
an exchange-real sizing layer, a sealed 1m loader and a portfolio execution path
that carries all three frozen rule-sets in one place.

**NO PERFORMANCE FIGURE WAS COMPUTED AT ANY STAGE OF THIS POINT.** Not one
expectancy, win rate, profit factor, Sharpe, Sortino, equity curve, drawdown,
`r_multiple`, `net_pnl` or `gross_pnl`. Everything decided was decided from:

- **occupancy and concurrency counts** on positions whose exits are calendar
  arithmetic (report 24),
- **venue schedules** retrieved and hash-snapshotted (reports 25, and document
  06 §7),
- **allocation counts** under the frozen budget (report 26),
- **bar-geometry distributions** — span against stop-to-target distance (report
  27),
- **quantities, notionals and price levels** (report 28),
- **path arithmetic over a partition tree** (report 29),
- **synthetic fixtures on hand-written prices** (report 30).

Every one is a permitted pre-firewall quantity, and fifteen AST guards across
fourteen test modules refuse the twelve names.

> ### POINT 4 IS NOW BLOCKING.
>
> **The execution path exists and cannot be run in `full` mode until the
> validation design is pre-registered.** Report 30 §2.1 puts that behind an
> explicit token rather than a boolean, so spending the firewall is a deliberate
> and greppable act.

**1,124 tests pass** at the closing commit `1e66c17`. **The holdout window
2025-01-01 through 2026-07-26 remains SEALED — with one disclosed breach of the
partition files, which §6 states in full and does not summarise away.**

---

## 2. THE ARTIFACT CHAIN

**EVERY SHA-256 BELOW WAS RECOMPUTED FROM THE FILE ON DISK AT COMMIT `1e66c17`,
not copied from any report.** A hash copied from a document that copied it from
another document is not provenance. **Every commit hash was verified to resolve
in `git log`.**

### 2.1 FROZEN DESIGN DOCUMENTS

| document | commit | SHA-256 |
|---|---|---|
| `docs/design/05_aggregate_risk_budget.md` | `a323237` | `d5ac7bd61323d04e75a854baf14086932470175408f5e2db4ca6f4d3afad268f` |
| `docs/design/05a_aggregate_risk_budget_amendment_1.md` | `62c2d2b` | `50da5aed3fabb86c3c7b54b41642444e50c7a7790de8dc93ab401ab53071522c` |
| `docs/design/05b_aggregate_risk_budget_amendment_2.md` | `46099a2` | `1d115df2272a4e231da41afbbd0b7c82020d0092ec2b3b483062d57c0e95f7bd` |
| `docs/design/06_exit_resolution_spec.md` | `6def4cb` | `773bbafe94ba136c9bddbdc443284af96c021eb4e0894677438e0cb7622f71a0` |
| `docs/design/06a_exit_resolution_spec_amendment_1.md` | `0f79311` | `6599b154806f0f34bf5d2f687af2f2e38d7d6179a04da0af40d6dc803edf65fb` |

### 2.2 MEASUREMENT AND BUILD REPORTS

| report | commit | SHA-256 |
|---|---|---|
| `docs/handoff/24_point_5_1_exposure.md` | `4e08e1b` | `e647e345ceaaec3a6c4fed16e8b4488a38ac9e48fa5a4d734f70231e4feeb045` |
| `docs/handoff/25_point_5_2_venue_constraints.md` | `e735295` | `6b8f525caac69317a4ce9e33e45e37f8314f058d7d0e01944b42729aec0adf66` |
| `docs/handoff/26_point_5_2_budget_cost.md` | `ef1f4f6` | `2b408bea1fbca457669ec3665aa6e7506ff74e23e21c859c8f5b3a286cbfb7f1` |
| `docs/handoff/27_point_5_3_0_intrabar_span.md` | `60b66f5` | `5806fac830480ccac3c93426598bfa2cdc51979e33255545fa5304fb45674aa9` |
| `docs/handoff/28_point_5_3_1_sizing.md` | `df14a68` | `be06acb5de72b7e6e2a253737317881e442715c4e7138290cf8ead71bc6d99ef` |
| `docs/handoff/29_point_5_3_3_1m_seal.md` | `7f46b1a` | `55e9546aee9b4a59035a4a769c2b1a9b7a41ad08fdb5dbcf7a48803df66e6e75` |
| `docs/handoff/30_point_5_3_4_portfolio.md` | `1e66c17` | `654b66e053c5dbcc672dbed0940efe555ce035b552640483a13e5c416eb34fa5` |

### 2.3 CODE ARTIFACTS, as at `1e66c17`

| module | introduced | SHA-256 |
|---|---|---|
| `src/risk/budget.py` | `a323237`, extended `62c2d2b` / `46099a2` | `088f0e1f2f0fa8ca2de0e720ccf442408a6d321232f475371b1221ca47b4a917` |
| `src/risk/exit_spec.py` | `6def4cb`, extended `0f79311` | `33f2f713740fbc47a5f1caeb1e97b474be7839a1b9077753e7243f901b18091b` |
| `src/engine/sizing.py` | `df14a68` | `db4d3beba29a7f66bbf1367273c75bf091dda6fcadeda78e4f3d3fe01d7ed81d` |
| `src/timeframe/sealed_1m.py` | `7f46b1a` | `00b539061b5c90519eed9524d9ea0a8d0c255bfc1726b809c2d2b53a588570cb` |
| `src/engine/portfolio.py` | `1e66c17` | `4251492d7bc9597873f1d0c5b91819fe9cce44c9df207bd6bb5181af1aef566e` |

### 2.4 THE THESIS THIS POINT SIZES

| document | commit | SHA-256 |
|---|---|---|
| `docs/handoff/22_point_1_thesis.md` | `02e47a5` | `5d716f7dfc2c7b0186082f23f1f4a8f121a44e67fd8eee7fdf8be922ef78da55` |
| `docs/handoff/22a_point_1_thesis_amendment_1.md` | `703046a` | `7d902da785e8cff3588ec1bb1680d9f5a44ffcf0a690e9b0fdb9c0954a518a66` |
| `docs/handoff/23_point_1_reopened_closing.md` | — | `d567177146828315dfabdbc1bb5d2c3ad5eed63b5ad966ea049feaca0d639818` |

---

## 3. WHAT WAS DECIDED, AND ON WHAT GROUND

**This section is an INDEX with arguments, not a restatement.** The authoritative
documents are those in §2.1. Where this section and they disagree, **they win.**

### 3.1 MARGIN AND POSITION MODE

**CROSS MARGIN.** Under isolated margin, at the leverage this book requires, **the
liquidation price can sit INSIDE the stop on wide-stop trades** — and a stop that
cannot be reached is not a stop. The cost of cross is the loss of the
per-position firebreak, and document 05 §8.1 states it rather than leaving it
implicit.

**HEDGE POSITION MODE, AND IT IS LOAD-BEARING RATHER THAN PRECAUTIONARY.** Report
25 §5.1 established that under one-way mode an opposite-direction signal
**offsets** an open position rather than opening a trade. Report 26 §7 measured
the exposure: **on 24.5–26.5% of bars — one bar in four — this strategy holds a
long and a short on the same symbol simultaneously, under the cap.** Uncapped the
figure is 46–48%; the cap roughly halves it and does not come close to
eliminating it. **Had the figure been zero, hedge mode would have been a harmless
precaution. At a quarter of all bars it is doing real work.**

### 3.2 THE AGGREGATE OPEN RISK BUDGET

**$120.00 of aggregate open NOMINAL risk across the whole book — 6.0% of $2,000.**
Derived in document 05 §2 from a stated **30–50% peak-to-trough drawdown
tolerance**, by allowing **one maximally correlated adverse event to consume at
most one fifth of the conservative end** (20% of 30% = 6%).

> **THIS IS A JUDGEMENT, NOT A DERIVATION, AND DOCUMENT 05 §2 SAYS SO AT LENGTH.**
> `COST_TOLERANCE_R`, the 1.50% stop floor, `n = 3` settlements and the 1:1.5
> reward-to-risk are all **per-trade** quantities and none of them constrains
> book-level exposure. The number is a preference with an argued rationale.

**ACROSS THE BOOK, NOT PER SYMBOL.** A per-symbol sub-budget would permit three
simultaneous one-symbol maxima and would be a weaker constraint wearing a
stricter name.

**THE RULE IS A HARD CAP OF SIX FULL-SIZE POSITIONS WITH ARRIVAL-ORDER SKIP.**
Because the budget is an exact multiple of the risk unit and Rule B charges the
nominal figure, an allocation is **one unit or zero, and zero is never viable**.
**The partial-allocation branch of document 05 §3 is therefore INERT**, is
documented as such in §4, and is implemented anyway with a counter that asserts
it is never taken — report 26 §11.3 and report 30 §6.1 both measure it at **0**.

**A SKIPPED SIGNAL IS SKIPPED.** Not queued, not deferred, not resized later
(document 05 §3).

### 3.3 THE THREE ORDERING RULES

| rule | decision | ground |
|---|---|---|
| **A** — intra-bar ties | **cyclic rotation by bar timestamp**: `(bar_open_ms // 3_600_000) mod 3` | Amendment 1 §2. Each symbol holds **each priority RANK exactly once in three**, not merely first place once — a scheme rotating first place while leaving third fixed would be biased on the rank that decides who loses the last slot. **Derived from the TIMESTAMP, not a bar index**, because an index is a property of the slice and the timestamp is a property of the bar |
| **B** — charging basis | **NOMINAL, never realised** | Amendment 1 §3. Under realised charging the six flooring shortfalls would accumulate as remaining budget, a seventh signal would be allocated the remainder, and **the inert partial branch would become reachable — silently** |
| **C** — intra-bar order | **exits before entries** | Amendment 2 §2. The same unit may fund a closing and an opening position at one bar close, and that is correct rather than double counting: under report 24 §5.3's half-open convention the closing position's last open bar is X and the opening position's first is X+1. Entries-first models a sequence that **cannot occur live** and is strictly more restrictive |

**RULE C IS NOT COSMETIC.** Report 26 §6 measured **902 positions — 14.98% of all
6,021 taken — that Rule C admits and entries-first would have skipped**, moving
the skip rate by **7.9 percentage points** on loop order alone.

### 3.4 EXIT RESOLUTION

**EXITS ARE EVALUATED ON 1m** (document 06 §2). Report 27 §6 measured the per-trade
upper bound on positions whose stop and target could both sit inside a single 1h
bar at **10.21% hold-weighted and 11.94% at maximum hold, against a 2.0%
criterion** — exceeded by **5.1×**, independently on every symbol and in every one
of the eighteen fold periods.

| rule | decision | ground |
|---|---|---|
| **E2** stop fill | **inclusive TOUCH** | a conditional market order does not rest, so there is no queue to be behind: triggered at the level, it fires at the level |
| **E3** target fill | **TRADE-THROUGH by one tick** | a resting maker limit fills because someone crossed the spread through it, not because price touched it. **One tick because the tick is the smallest increment that exists** — any other margin is a tunable parameter entering a pre-registration |
| **E4** intrabar precedence | **STOP first, and FLAGGED** | pessimism, and the alternative is silence: an unspecified case is decided by whichever comparison the implementer wrote first |
| **E5** stop vs time exit | **STOP first** | not a preference — **it is what the two order types are.** A stop touched at second 3 of the minute has already fired before the close exists |

**THE ASYMMETRY IS DELIBERATE**: the losing leg fills easily, the winning leg
fills hard. Document 06 §4.1 states the direction **in advance** so a low
target-fill rate cannot later be presented as a discovery.

### 3.5 FUNDING

**PROVISIONED AT THREE SETTLEMENTS IN BOTH SIZING AND REALISED P&L, WITH NO
RECONCILIATION** (document 06a E7.1). `funding_pu = entry × rate × count`, and
the same term appears in the sizing denominator **and** in the target cost
bracket (E7.2).

**WHY THE PROVISIONED READING.** It keeps a stop at exactly **−1.0R** and a target
at exactly **+1.5R**, so report 28's identities and the thesis's **40.0%**
breakeven and **53.6%** detectable-edge arithmetic hold exactly. The rejected
reading is more faithful to cash flow and **makes every R multiple depend on the
entry hour** — a unit that varies with the clock is not a unit.

**THE COST IS STATED, NOT HIDDEN.** Document 06 §6's enumeration: **21 of 24 entry
hours cross TWO settlements while three are charged, and three cross THREE.** The
typical position is overcharged by one settlement, **never refunded**, and the
overcharge falls hardest on fast exits, which are disproportionately stop-outs.

**FUNDING ON BOTH SIDES OF THE TARGET SOLVE IS NOT OPTIONAL.** In the denominator
alone, the stop identity stays exact while the target identity drifts to about
**1.482R** — report 30 §7.2 measured **1.4824R–1.4829R** on six floor-bound cells.
**The stop identity — the one an implementer checks first — keeps passing.**

### 3.6 MISSING 1m BARS, AND NO LEVERAGE REFUSAL

**MISSING 1m BARS ARE FLAGGED AND COUNTED, NEVER FILLED** (document 06 §8). **A
missing bar is not a price gap: a gap is something the market did, a hole is
something the data does not know.** Any fill convention over an absent minute
records an event that may not have happened, at a price nobody observed, and does
so invisibly.

**NO LEVERAGE REFUSAL IN THE NEW EXECUTION PATH** (report 30 §8). Report 26 §12.1
established `costs.CostConfig.max_leverage = 3.0` as an unmeasured placeholder
that **would bind on 16.14% of bars** and censor the population the budget already
governs. Report 25 §3 measured the venue's actual limit at **150× (BTC, ETH) and
100× (SOL)** in tier 1, with maintenance margin **0.40% / 0.40% / 0.50%**.

### 3.7 WHAT WAS RULED OUT OF SCOPE

**DAILY LOSS LIMITS AND KILL SWITCHES BELONG TO THE LIVE LAYER AND STAY OUT OF
THE BACKTEST.** They are operational risk controls, not properties of the
hypothesis; putting them in the backtest would make the measured population a
function of an operational policy that has not been designed, and would confound
the thesis with its deployment.

---

## 4. WHAT WAS MEASURED

**EVERY FIGURE CARRIES ITS POPULATION IN THE SAME SENTENCE**, which is report 23
§4.1's own transferable rule and the one that would have caught several of §7's
instances.

### 4.1 THE UNCAPPED BOOK — report 24 (`4e08e1b`)

- **11,384 candidate positions** over 2022-01-05T18:00Z – 2024-12-31T23:00Z:
  **3,735 BTCUSDT + 3,715 ETHUSDT + 3,934 SOLUSDT** (§3).
- The uncapped book carries a **median of 9 concurrent positions** and requires
  **3.59× median leverage on $2,000**, with a maximum of **13.52×**; **63.93% of
  bars require more than 3×** (§7, §10.1).
- Hold duration over all 11,384: **min 17h, max 24h, mean 20.51h, median 21h** —
  every one inside the frozen [16h, 24h] band (§5).

### 4.2 THE CAPPED BOOK — report 26 (`ef1f4f6`)

| population | figure |
|---|---|
| taken under the budget | **6,021** |
| skipped | **5,363** |
| skip rate | **47.11%** |
| per symbol taken / skipped | BTC **1,973** / 1,762 · ETH **1,963** / 1,752 · SOL **2,085** / 1,849 |
| per-symbol skip rate spread | within **0.18 points** of identical |
| positions Rule C admitted that entries-first would skip | **902** — 14.98% of taken |
| skips arriving at an exactly full budget | **5,363 — every one** |
| partial allocations | **0** |
| maximum required leverage under the cap (§5.5) | **3.5964×** |

> **THE 47.11% SKIP RATE IS AN UPPER BOUND** (§10). It was measured at maximum
> hold; under real exits positions close early, free budget early, and admit
> signals this measurement skips. **How far below is unknowable at this commit.**

**FLOOR BINDING, pooled across the 11,384 candidates: 25.71%** — **27.02% among
taken, 24.24% among skipped**, a **+2.78 pp** difference (§4.1).

**THE CAPITAL FLATLINE** (§3.3): the taken count per training period is **almost
flat at 976–1,025** while signal supply varies widely across the same periods.

### 4.3 SIZING AND COSTS — report 28 (`df14a68`)

- **Flooring costs 0.80% of nominal risk** across the 11,384 candidates —
  **$1,826.85 of $227,680** — and **0.78%** across the 6,021 taken (§8.2).
  **ETH is the granularity-binding symbol**; worst single position **9.21%**.
- **`c/s` against `COST_TOLERANCE_R = 0.11`** (§9), on the 11,384 candidates:
  median **0.0878**, maximum **0.1483**. **3,507 of 11,384 — 30.81% — exceed the
  frozen tolerance.** Of those, **2,927 are floor-bound and 580 are not**, and the
  floor-bound stratum's **minimum is 0.1122**, so **every single floor-bound
  position exceeds the tolerance — there is no overlap at all.**
- **SOLUSDT's excess is mostly NOT floor-bound**: **419 of its 540**, because its
  10 bps stop haircut pushes `c/s` above 0.11 at any stop tighter than ~2%.
- **No position fails either viability condition on either population** (§6.2).

### 4.4 THE 1m LAYER — report 19 (`74e3ca9`), cited by reports 29 and 30

**The 1m layer is exactly full over 2022-01-01 to 2024-12-31: 1,578,240 rows PER
SYMBOL** — `1,096 × 1,440` — **with zero buckets dropped anywhere**, and per-year
**525,600 / 525,600 / 527,040** for 2022 / 2023 / 2024. **Three-symbol total
4,734,720.** Completeness **100.000% on all three symbols**.

*(Report 19's own table header reads "bars per symbol". Document 06a §5.1
mislabels the same figures — see §8, erratum 3.)*

**ON-DISK PARTITIONS** (report 29 §3): **15 partitions, 15 files** — three symbols
× five years. **`year=2025` and `year=2026` EXIST for all three symbols: six
sealed files.** The seal is not maintained by the absence of the data.

### 4.5 THE EXECUTION PATH — report 30 (`1e66c17`)

**The `max_hold` regression reproduced report 26 exactly, on the first run, with
no adjustment**: 6,021 / 5,363 / 11,384 and 1,973 / 1,963 / 2,085. **Peak
concurrency exactly 6; peak open nominal risk exactly $120.00** — the cap is
asserted to bind, not merely to be respected. Realised risk across the 6,021
taken ranges **18.3392 – 20.0000** with a median of **19.9237**.

---

## 5. THE OPEN ITEMS, ROUTED TO THE VALIDATION DESIGN

**Each of these is owed to Point 4 and none can be settled without it.**

### 5.1 `COST_TOLERANCE_R`'s JUSTIFICATION — TOGETHER WITH THE 1.50% STOP FLOOR

> **THESE ARE ONE ITEM AND MUST BE SETTLED TOGETHER.** The floor is the mechanism
> that enforces the tolerance, and report 28 §9 measured that **it fails on 100%
> of the cases it governs**: every floor-bound position's `c/s` exceeds 0.11, the
> stratum minimum being 0.1122 against the tolerance's 0.11.

The tolerance is frozen and is not in question. Its *"one third of the ~0.34R
minimum detectable edge"* derivation **presumed costs subtract from expectancy in
R**, which under net-solved geometry they do not (amendment 1 §7, carried by
report 23 §6.2). **It must be re-argued before any performance figure is seen** —
re-arguing it afterwards would be selecting a justification to fit a result.

**WHAT IS OWED ARITHMETICALLY:** the stop widths at which `c/s ≤ 0.11` actually
holds, per symbol and per fee treatment, solved from the same cost algebra report
28 §9 measured against.

> **A FIGURE THIS RECORD CANNOT SOURCE.** The brief for this closing record
> supplies required floors of **1.530% / 1.561% (BTC, ETH)** and **1.971% /
> 2.030% (SOL)** against the frozen 1.500%, with the SOL gap attributed entirely
> to the unmeasured 10 bps haircut. **Those four figures appear nowhere in
> `docs/` or `reports/`** — grep over both trees returns nothing. They are
> recorded here as **supplied but UNSOURCED**, and **Point 4 must derive them
> from the implementation before relying on them.** The qualitative claim they
> support is independently sourced: report 28 §9 states that SOLUSDT's 10 bps
> haircut pushes `c/s` above 0.11 at any stop tighter than about 2%, and that
> 419 of SOL's 540 breaches are not floor-bound.

### 5.2 THE STOP HAIRCUT ITSELF

**5 bps on BTC/ETH and 10 bps on SOL, and it IS the entire slippage-and-gap
model.** `src/engine/costs.py` says so in its own source — *"Placeholders, per
spec"* — and report 25 §2 confirmed it is not a venue-published figure.

**IT CANNOT BE VALIDATED AGAINST THIS DATA LAYER.** Report 27 §8 established that
`open` is **synthesised** from the carried-forward previous close and is dropped
by every loader, so **no bar's first observed price exists at any resolution.** A
bar that opens beyond the stop is invisible. Document 06 §9 lists this as the
largest remaining unknown in the exit model and routes it to Point 6's paper
trading or a data source this project does not have.

### 5.3 THE FILL-PRICE TERM — report 30 §7.3

`costs.position_size` charges the exit fee on the **stop level** while the actual
fill sits a haircut away from it. Per unit, `diff = (fill − stop)(1 ∓ f) + stop ×
haircut`. **Direction-dependent in sign**, at most **0.0033 USDT** across report
30's six cells, **under 0.017% of a risk unit**.

> **IT MAKES A SHORT STOP-OUT BREACH 1.0R.** For shorts the fee is charged on a
> higher fill price, so the realised loss lands **beyond** one risk unit. The
> project's standing rule is $20 fixed risk **after** fees and slippage, and this
> term breaches it — by a negligible amount, in the direction the rule exists to
> prevent.

**IT IS ACCEPTED ON MAGNITUDE GROUNDS, AND FUNDING AT 0.0067R WAS NOT.** Document
06 §5.4 rejected charging funding as a realised cash flow **precisely because it
lets a stop-out return worse than −1.0R** — at roughly 0.0067R, over twice this
term's worst case. **The two decisions run in opposite directions on the same
principle, and the only thing distinguishing them is a threshold nobody has
stated.** Point 4 owes that threshold: **at what magnitude does a breach of the
risk rule stop being tolerable?** Until it is stated, both decisions rest on
intuition rather than on a criterion.

### 5.4 THE RULE C HOLD-DURATION SELECTION EFFECT

Exits free budget **at settlement instants**, because the time exit is defined on
the funding calendar. A signal arriving on a bar where budget is freed is
therefore a signal arriving at a settlement boundary — **and document 06 §6's
enumeration shows those are exactly the entry hours that draw 24-hour holds.**

> **THE TRADED POPULATION IS NON-UNIFORM IN HOLD DURATION BY CONSTRUCTION**, and
> the non-uniformity is produced by the budget rule rather than by the market.

Nothing in Point 5 measured the size of this effect. **Any per-fold or pooled
statistic that is sensitive to hold duration inherits it**, and Point 4 must
decide whether to stratify on hold duration or to state the confound.

### 5.5 THE CAPITAL-SUPPLY FLATLINE

Report 26 §3.3: taken counts per training period are **976–1,025** while signal
supply varies widely over the same periods.

> **TRADE COUNT PER FOLD MEASURES CAPITAL, NOT MARKET CONDITIONS.** A fold with
> more signals does not produce more trades; it produces more skips.

**Any kill condition, adequacy threshold or power calculation denominated in
trade count is denominated in a quantity the budget pins nearly flat.** Point 4
must not read a stable trade count as evidence of a stable opportunity set.

### 5.6 PATH DEPENDENCE

Document 05 §6 pre-registered it and report 26 §2.2 restates it: **under the
budget with real exits, the traded population is a function of realised
outcomes** — a stop-out frees its slot hours before a time exit would — **so it is
not a subset of anything knowable in advance.**

**REPORT 21's 200 / 50 ADEQUACY THRESHOLDS WERE ESTABLISHED ON THE UNCAPPED
POPULATION AND DO NOT DESCRIBE WHAT IS TRADED.** Report 26 §9 reports the capped
worst cells as a reference point only — **316 / 315 / 316 train and 154 / 154 /
157 test**, margins falling from 2.82× / 5.56× uncapped to **1.57× / 3.08×** — and
states explicitly that **no claim is made that clearing them establishes
adequacy**, because the thresholds were derived against a population that does
not exist under this rule and which is not even fixed.

### 5.7 R-MULTIPLE WEIGHTING

**Whether R multiples are equal-weighted or dollar-weighted is undecided.** Report
28 §7 stores both `nominal_risk_usd` and `realised_risk_usd` per position and
neither is derived from the other at read time, precisely so that this choice
remains open. **It is a validation-design choice with a direct effect on every
aggregate**, and flooring drag of 0.80% is the size of the wedge between them.

### 5.8 THE OPERATIONAL LEVERAGE SETTING

**Constrained only to exceed 3.596×** — report 26 §5.5's maximum required
leverage under the cap — **with margin.** Report 25 §3 measured the venue permits 150× / 150×
/ 100× in tier 1 at 0.40% / 0.40% / 0.50% maintenance margin, and §4 gives the
maintenance requirement at report 24's worst bar as **$114.40 against $2,000 — a
5.72% margin ratio, where liquidation triggers at 100%.**

**AND THE DISPOSITION OF `costs.CostConfig.max_leverage` IS OWED.** It is **still
3.0** for the legacy paths whose tests pin it. The new execution path implements
no leverage refusal at all. **Two different answers coexist in the repository**,
and Point 4 must state which governs a live deployment.

### 5.9 AT WHAT LEVEL KILL CONDITION (d) IS EVALUATED

Thesis §7(d) stratifies trades by whether the 1.50% floor bound and requires the
advantage to survive among **non-floor-bound trades at ≥ 0.05R**. §7.1 aggregates
every condition by **majority across the nine folds**.

> **IN A HIGH-BINDING FOLD THE NON-FLOOR-BOUND STRATUM IS THIN.** Report 26 §3.3
> gives fold 4 test as **495 taken**; §4.2 gives **68.28% floor-bound among
> taken** in that cell. The non-floor-bound remainder is therefore about **157
> pooled across three symbols — roughly 52 per symbol.** A 0.05R threshold is not
> detectable on 52 trades.

*(Report 26 §9 separately reports **157** as SOLUSDT's own worst test-fold taken
count, also at fold 4. **These are two different quantities that coincide
numerically** and must not be conflated.)*

**POOLED AND OUT-OF-SAMPLE THE STRATUM IS AMPLE**, and floor binding among taken
positions ranges from **5.37% to 68.28%** across the eighteen fold periods
(§4.2), so most cells are comfortable and only the high-binding ones bite. **Point
4 must decide whether (d) is evaluated per fold under the majority rule — where
it is undetectable in the folds most likely to bite — or pooled, and must state
the choice before any figure exists.**

---

## 6. THE 5.3.3 BREACH — PERMANENTLY DISCLOSED

**Report 29 §9 is the primary account. This section does not soften it.**

### 6.1 WHAT HAPPENED

**Six sealed 1m partitions — `year=2025` and `year=2026`, all three symbols — were
OPENED AND DECODED during 5.3.3's mutation battery.** The battery was run against
the real data directory behind a filesystem barrier (`chmod 000` on the six
files) which was verified as armed at the start and **silently reverted to `0400`
mid-run**; the process owns the files.

- **CONFIRMED under mutation M3b**: `load("SOLUSDT", …)` opened
  `year=2025/data.parquet` and `year=2026/data.parquet`, decoded `ts`, `high`,
  `low` and `close`, and returned a filtered frame.
- **NEAR-CERTAIN under M2 and M3a**, and **not re-tested, because re-testing
  would repeat it.**
- **NOT AFFECTED: M1, M4a, M4b and M5**, which cannot reach a sealed path by
  construction.

**NO SEALED VALUE WAS PRINTED, AGGREGATED, STORED, OR USED IN ANY COMPUTATION,
AND NONE REACHED A HUMAN, A DOCUMENT OR AN ARTIFACT.** The bytes were decoded
into a transient process and discarded when it exited. **A persistent-disk check
afterwards found nothing** — no sealed value in `.pytest_cache`, in any log, or in
captured output.

### 6.2 THE ADJUDICATION, AND ITS REASONING

> **THE HOLDOUT REMAINS VALID.**

**An out-of-sample test's validity rests on the data not having influenced the
design of what it tests.** No sealed value reached anyone, so no design decision
could have been conditioned on one. **Every Point 5 decision is committed with a
hash predating the breach** — documents 05 (`a323237`), 05a (`62c2d2b`), 05b
(`46099a2`), 06 (`6def4cb`) and 06a (`0f79311`) all precede `7f46b1a` — **and the
chain is verifiable from `git log` independently of anyone's account of what
happened.** That independence is the point: the adjudication does not rest on
trusting the report.

**THE ALTERNATIVE WAS CONSIDERED AND REJECTED ON ITS COSTS.** Declaring the window
burned would cost **the entire out-of-sample test, with no second window
available**, in exchange for **no epistemic gain** — the contamination mechanism
an out-of-sample test guards against is design influence, and there was none.

**THIS IS AN ADJUDICATION, NOT AN EXONERATION.** The window's value rested on
never having been opened, and six of its files were opened by code written for
this project, in runs chosen by it.

### 6.3 THE RULE IT PRODUCED, NOW BINDING

> **A MUTATION THAT DISABLES A PRE-READ GUARD NEVER FACES THE REAL DATA
> DIRECTORY.** There is no safe way to run one there: the mutation's entire
> purpose is to remove the thing that would have stopped the read. It runs
> against a synthetic tree, and only mutations provably incapable of reaching a
> read may face the real directory.

**IT WAS OBEYED AT 5.3.4.** Report 30 §10 records two holdout mutations: **H1**,
whose pre-read guard was intact, faced the real tree and was refused before any
file was opened; **H2**, which disabled a guard, **ran against a synthetic tree of
empty files only**, with just the static assertions run against the repository.

### 6.4 THE DISCLOSURE REQUIREMENT

> **ANY WRITEUP OF HOLDOUT RESULTS MUST CARRY THIS DISCLOSURE.** Not a reference
> to it — the disclosure itself: what was opened, that no value reached anyone,
> the adjudication and its reasoning. A reader of a holdout result is entitled to
> assess the seal for themselves.

---

## 7. THE DEFECT LEDGER

**The recurring class is the Point 4 closing record §3.4's:**

> **a numerical criterion written from a mental model of a quantity rather than
> from its implementation or its achievable range.**

### 7.1 THE COUNT WAS CONTESTED. THIS RECORD SETTLES IT.

**Report 24 §10.1 calls its own leverage fallacy *"the eighth instance"*.** That
is a **miscount**, and it is itself an instance of the class.

**THE METHOD.** Count every defect that a committed document **explicitly
identifies as an instance of this class**, **one per distinct defect** — not per
symptom and not per document — **cumulatively across points**, from the documents
themselves rather than from any running total quoted in them.

| source | instances | how they are enumerated there |
|---|---:|---|
| Point 4 closing record §3.4 (`docs/handoff/16_point_4_closing.md`) | **7** | a numbered table, rows 1–7 |
| Point 1 (reopened) closing record §4 (`docs/handoff/23_…`) | **9** | numbered (1)–(9) in prose |
| **subtotal before Point 5** | **16** | |
| this record §7.2 | **16** | enumerated below |
| **RUNNING TOTAL** | **32** | |

**WHERE REPORT 24 WENT WRONG:** it cites *"the closing record §4"* — the Point 1
(reopened) record, whose §4 **states "Nine instances are recorded below" and
numbers them (1) to (9)** — and then calls itself **the eighth**. **The count is
inconsistent with its own citation**, before Point 4's seven are considered at
all. **No mechanism for the miscount is asserted here**, because none is
recoverable from the documents; only the discrepancy is. **Report 24 §10.1's
instance is the 17th, not the 8th.** The correction is logged here and **report
24 is not edited** — errata are logged, not patched.

### 7.2 THE POINT 5 INSTANCES — SIXTEEN

**FROM THE ASSISTANT SIDE OF THE COLLABORATION (6):**

**(17) THE SINGLE-POSITION LEVERAGE CHECK TREATED AS A BOOK-LEVEL CONSTRAINT.**
`leverage_term` is a per-position quantity and was read as an account-level one.
One floor-bound position requires 0.599×; the median book requires 3.59×. **The
same shape as Point 1's error (7): the population was mis-named.** *(report 24
§10.1.)*

**(18) A 0.5% MAINTENANCE MARGIN RATE ASSERTED AS SOURCED WHEN IT WAS ASSUMED.**
The venue's tier-1 rates are **0.40% / 0.40% / 0.50%** (report 25 §3, and §4
is the section that checked the assumed figure against them). The figure
was stated with the confidence of a retrieval before the retrieval existed.

**(19) BAR-INDEX SCOPE-DEPENDENCE ASSERTED AS A LIVE HAZARD WHEN IT IS LATENT.**
Amendment 1 §2.2.1 checked it and **corrected the claim**: every scope this
project currently defines starts at a whole multiple of three hours — fold
boundaries at 24h, the pooled warm-up trim at 114 bars = 3 × 38 — so an
index-derived rotation agrees with the timestamp rule **today, by arithmetic
coincidence.** The hazard is real and dormant, and the argument for the timestamp
rule is that it cannot wake up, not that it is currently binding.

**(20) A COUNT CAP AND A DOWNSIZING MECHANISM PROPOSED TOGETHER IN ONE MESSAGE.**
They are **mutually exclusive**: a hard count cap means an allocation is one unit
or nothing, which is precisely the condition under which downsizing never fires.

**(21) THE DOWNSIZING MECHANISM SPECIFIED WITHOUT CHECKING ITS REACHABLE STATES.**
At $120 with $20 units the partial branch is **unreachable**, so the rule
degenerates to the hard cap it was proposed to avoid. **The defect is not that
the mechanism is wrong — it is that its reachable state space was never
enumerated**, which is the class exactly.

**(22) "35%" TRANSCRIBED FROM A FLOOR-WIDTH RATIO INTO A POPULATION FRACTION.**
The brief for the exit specification put SOLUSDT's haircut-driven share of its
cost-tolerance breach at 35%. **No such figure appears in report 28 §9 and none
of its ratios produces it**; the sourced figures are 540 SOL positions above the
tolerance, **419 of them (77.6%) not floor-bound.** *(document 06 §3.1, which
records the correction rather than repeating the figure.)*

**FROM THE PROMPT-CONSTRUCTION SIDE — a distinct sub-class, INTERNAL
CONTRADICTION BETWEEN A PROMPT'S OWN CONSTRAINTS AND ITS REQUIREMENTS (4):**

**(23) `src/risk` REQUIRED UNIMPORTED BY ANYTHING UNDER `src/` IN ONE STEP AND
REQUIRED TO BE READ IN THE NEXT.** Resolved at 5.3.4 by spending the assertion on
one file with the allowlist kept explicit (report 30 §4) — but the two
requirements were live simultaneously.

**(24) A CONSTANT NAMED `FUNDING_PNL_TREATMENT` SPECIFIED IN A PROMPT THAT
REQUIRED THE GUARD BANNING THAT TOKEN.** The twelve-name AST firewall refuses the
bare token `pnl` over identifiers. Resolved by renaming the constant to
`FUNDING_REALISED_TREATMENT` and leaving the guard unconditional — **the module
changed, not the guard**, on report 28 §11.1's terms *(document 06a §6.1).*

**(25) A MUTATION BATTERY SPECIFIED WITHOUT SPECIFYING ITS ENVIRONMENT.** The
prompt required mutations planted, run, confirmed failing and reverted, and said
nothing about **where** they run. **That omission produced the 5.3.3 breach**
(§6). The rule that closes it is now §6.3's and is stated in report 29 §9.3.

**(26) `tests/test_portfolio.py` SPECIFIED AS A FILE TO CREATE WHEN IT HAD
EXISTED SINCE `d04ba47`.** It holds Point 3's G1 fixtures 7 and 8. **It was
overwritten in error and restored from git before anything was committed**
(report 30 §11.1); the new suite went to `tests/test_portfolio_path.py`.

**FROM THE IMPLEMENTATION SIDE, ON THE SAME TERMS (6):**

**(27) REPORT 24 §10.1's INSTANCE MISCOUNT** — §7.1 above. **A count of one's own
errors, written from a mental model of the ledger rather than from the ledger.**

**(28) DOCUMENT 06a §2.3 AND §2.4 — THE WRONG DENOMINATOR, TWICE.** §8, errata 1
and 2. One defect with two symptoms.

**(29) DOCUMENT 06a §5.1's POPULATION LABEL.** §8, erratum 3.

**(30) DOCUMENT 06a §5.2's CLAIM, WHICH WAS FALSE WHEN WRITTEN.** §8, erratum 4.

**(31) REPORT 29's DECORATIVE SIDECAR EXCLUSION.** The underscore-prefix rule
could not fire, because **no real sidecar name ends in `.parquet`** and the suffix
check alone was doing the work. **No test could tell** — `MAKER_NONFILL_COST_R`'s
shape again. Found by the mutation battery, fixture strengthened rather than
guard weakened *(report 29 §5.1).*

**(32) THE CHMOD BARRIER METHOD.** A safety mechanism adopted without verifying
it would hold, and **not re-verified before each mutation.** It reverted silently
and the battery continued against the real directory *(report 29 §9.1).*

### 7.3 THE MITIGATION ADOPTED

**PROMPTS NO LONGER NAME NEW TEST FILES**, and **every prompt requires target
paths to be checked before writing.** Instance (26) is what produced both.

**AND A SECOND ONE, FROM (25) AND (32):** a verification procedure that relies on
an environmental precondition must **assert the precondition immediately before
each use**, not once at the start. A barrier verified once is a barrier assumed
thereafter.

### 7.4 WHAT THE LEDGER IS FOR

**A project that counts its own errors as evidence about its process cannot
afford a miscount** — which is why (27) is logged as an instance rather than
quietly corrected. **Sixteen instances in one point, against nine in Point 1
reopened and seven in Point 4, is not evidence of a worsening process**: Point 5
produced more artifacts under more explicit guards, and **most of these were
caught by the guards rather than by review.** Instances (31) and (32) were both
found by a mutation battery whose purpose is exactly that.

**The class is not extinguished by being named.** It has now been named in three
consecutive closing records.

---

## 8. THE ERRATA LOG

**ERRATA ARE LOGGED, NOT PATCHED. NO FROZEN TEXT IS EDITED.** Each entry gives the
correct value and states whether anything operative changes.

### ERRATUM 1 — document 06a §2.3, the overcharge figure

**STATED:** the one-settlement overcharge is *"about **0.0067R** at the 1.50%
floor stop (`rate / s`)"*.

**CORRECT:** as a share of a **realised risk unit** the figure is
`rate / (s + c + funding)` = **0.00589R** at the floor stop, using report 28 §9's
floor-bound minimum `c/s = 0.1122`.

**WHY IT IS WRONG:** **§4.2 of the same document forbids that denominator.** It
states that `rate × n / s` is a comparison figure pinned to the floor stop and
*"incorrect as a construction rule"*, because the risk unit includes costs — and
then §2.3 uses `rate / s` to denominate a share of the risk unit.

**OPERATIVE?** **NO.** The figure appears in a cost-disclosure paragraph and
constructs nothing. **The stated figure is larger than the true one, so the
disclosure is conservative.**

### ERRATUM 2 — document 06a §2.4, the rejected reading's breakeven

**STATED:** under the rejected reconciled reading the breakeven is
*"≈ **39.7%** — `0.9933 / 2.5`"*.

**CORRECT:** **39.8%.** With the corrected share of erratum 1, `x = 0.00589`, the
breakeven is `(1 − x) / 2.5` = **0.39765**.

**OPERATIVE?** **NO.** It is a figure in a **rejected** branch, quoted to show what
the rejected reading would have cost. The adopted reading's breakeven is the
frozen **40.0%** and is unaffected.

### ERRATUM 3 — document 06a §5.1, the completeness table's labels

**STATED:** *"1m rows, **pooled** — 1,578,240"* and *"per symbol, per year —
525,600 / 525,600 / 527,040 **on BTCUSDT, ETHUSDT and SOLUSDT**"*.

**CORRECT:** **1,578,240 is PER SYMBOL** — report 19's own table header reads
*"bars per symbol"* — and the **three-symbol total is 4,734,720.** The three
figures labelled as three symbols are **three YEARS for one symbol**: 2022, 2023
and 2024, at 365 × 1,440, 365 × 1,440 and 366 × 1,440. They sum to 1,578,240,
which is the arithmetic identity that makes the mislabelling detectable.

**OPERATIVE?** **NO — the figures are correct and the labels name the wrong
population.** It is nonetheless the purest instance of §7's class in this point:
**the numbers are right and the populations attached to them are not.**

### ERRATUM 4 — document 06a §5.2, a claim that was false when written

**STATED:** *"THE HOLDOUT WINDOW HAS NEVER BEEN EXAMINED FOR 1m COMPLETENESS, AND
IT CANNOT BE EXAMINED WITHOUT OPENING THE SEAL."*

**CORRECT:** **it had been, and by a path that ran on every test invocation.**
Report 29 §2.3 established that `structural_pass.check_manifest` and
`tests/test_manifest_integrity.py` called `pq.read_metadata` on **all 26 manifest
outputs, six of which are sealed 1m partitions**, and accessed `.num_rows` —
**which is a completeness figure.** `data/derived/_manifest.json` records those
counts in a file on disk.

**PRICE INTEGRITY IS INTACT.** Row counts of a full minute layer are **calendar
arithmetic** and carry no price information. The parquet footer also carries
per-column min/max statistics, which **would** be price information — but the code
accessed only `.num_rows`, and the channel was closed at 5.3.3 (report 29 §2.4).

**OPERATIVE? PARTLY, AND POINT 4 MUST ACT ON IT.** E8.1's reasoning — that the
missing-bar rule's *"first real exercise may occur out of sample"* — was built on
the premise that the holdout's completeness is unknown. **The premise is false in
its narrow form**: the row counts exist. **E8.1's requirements are unchanged and
remain binding** — reachable-value tests, the flagged fraction reported even when
zero, and reported separately out of sample — **but the argument for them must be
restated in Point 4 on the corrected footing.**

### ERRATUM 5 — report 24 §10.1, the instance count

**STATED:** *"the eighth instance"*. **CORRECT: the seventeenth.** §7.1 gives the
method and the arithmetic. **OPERATIVE? NO** — it changes no measurement in report
24, only the ledger.

---

## 9. WHAT POINT 4 MUST CONTAIN

**These are requirements, not suggestions.**

**(a) FOLD STRUCTURE AND THE WALK-FORWARD PROCEDURE**, on the existing nine folds
in `src/folds/schedule.py`. Adjacent training windows overlap by 50% and the nine
folds are **a stability probe, not nine independent trials** — the aggregation
rule must be stated against that fact, not against an assumption of independence.

**(b) THE METRICS, AND THE LEVEL EACH IS COMPUTED AT.** Expectancy per trade, win
rate, profit factor, Sharpe, Sortino, maximum drawdown and trade count — **each
specified as per symbol, per fold, or pooled**, and each specified once. A metric
whose level is left open is a metric that will be computed at whichever level
first looks informative.

**(c) THE KILL CONDITIONS, RESTATED FOR THE CAPPED, PATH-DEPENDENT POPULATION.**
Thesis §7's conditions (a)–(f) were written against the uncapped population.
**They now govern a population that is 47.11% smaller at maximum hold, is a
function of realised outcomes, and is non-uniform in hold duration by
construction (§5.4).** Condition (d) additionally needs §5.9's level decision, and
condition (e)'s 40% time-exit threshold now applies to a population whose
hold-duration mix the budget rule shapes.

**(d) PARAMETER-SENSITIVITY CHECKS, AND WHAT CONSTITUTES CURVE-FITTING**, stated
as a criterion rather than as a caution.

**(e) THE ORDER OF INSPECTION** — what is looked at first, and **what the response
is to each kind of failure**, written before the first figure exists. An order
chosen after a result is an order chosen to reach it.

**(f) A FIRST-RUN DIAGNOSTIC GATE — REQUIRED, AND REQUIRED BECAUSE OF POINT 5's
OWN DECISION.**

> **EVERY `full`-MODE VERIFICATION IN REPORT 30 IS SYNTHETIC.** That was the right
> call — it is what kept the firewall intact through Point 5 — and it has a
> price. **When the engine first runs on real data, a defect in level evaluation
> would surface at the same moment as the first performance figures**, and the
> two could not be separated without inspecting outcomes. **Inspecting outcomes
> to decide whether the engine works is how a validation design gets fitted.**

**THE GATE MUST BE PRE-REGISTERED AND MUST BE OUTCOME-INDEPENDENT.** Candidate
checks, all computable without touching `exit_reason`:

- **taken and skipped counts, and the budget invariants** — concurrency ≤ 6, open
  nominal ≤ $120.00, never negative, remaining an exact multiple of $20.00,
  partial-allocation counter zero;
- **the intrabar-precedence flag count**, which should be **near zero at 1m** — a
  1m bar must span the whole stop-to-target distance — so **a large value means
  the fill logic is wrong**, not that the market was volatile;
- **the missing-bar flag count, which MUST be exactly zero in sample**, because
  report 19 establishes the 1m layer is full; **anything else means the loader or
  the interval arithmetic is broken**;
- **every emitted stop and target price on the tick grid**, and **every realised
  risk at or below nominal.**

> **THE GATE IS ONLY AVAILABLE IF IT IS SPECIFIED BEFORE THE RUN.** Afterwards,
> every one of these checks is still computable and none of them is still
> evidence: a threshold chosen once the numbers are visible is a threshold chosen
> to pass.

**(g) THE DISPOSITION OF EVERY §5 OPEN ITEM** — all nine, each with a decision or
an explicit deferral naming what it is deferred to.

---

## 10. WHAT POINT 4 MUST NOT DO

- **IT MUST NOT RUN THE ENGINE IN `full` MODE.** The validation design is
  committed **before** the first performance figure exists.
- **IT MUST NOT COMPUTE, INSPECT OR ESTIMATE ANY OUTCOME QUANTITY.** Not to check
  the engine works; not on one symbol; not on one fold; not on one day.
- **IT MUST NOT OPEN THE HOLDOUT.**

**On the terms document 05 §11 sets for itself:** the design is committed in its
own commit, and a correction is a new document with its own commit. **A silent
edit is a contamination event.**

---

## 11. FIREWALL STATUS

**NO WIN RATE, EXPECTANCY, PROFIT FACTOR, SHARPE, SORTINO, EQUITY CURVE,
DRAWDOWN, `r_multiple`, `net_pnl` OR `gross_pnl` FIGURE EXISTS ANYWHERE IN THIS
REPOSITORY FOR THIS THESIS, AT COMMIT `1e66c17`.**

**`full` MODE HAS NEVER RUN ON REAL DATA.** Report 30 §9 asserts it over the test
module's own AST: every `full`-mode invocation must be handed a synthetic cache,
with two named exemptions, and the one that faces the real loader is refused
before a file is opened.

**THE CHECK.** `git log`, plus **fifteen AST firewall guards across fourteen test
modules**, all passing at this commit. `src/engine/simulate.py` **can** compute
such quantities and **has not been run on this thesis**.

**WHAT WOULD FALSIFY THE CLAIM:** a commit at or before `1e66c17` containing an
outcome figure for this thesis — in a report, a document, a stored artifact under
`reports/`, or a committed data file. **There is none.**

---

## 12. TWO PROCESS ITEMS

### 12.1 THE STANDING PROJECT BRIEF IS NOT IN THE REPOSITORY

**Capital ($2,000), the 1% risk rule, the asset set, the exchange and the 30–50%
drawdown tolerance exist only in conversation.** No committed artifact states
them.

**THIS HAS ALREADY COST SOMETHING.** Report 25's session had to reconstruct the
drawdown tolerance from context and **correctly flagged it as unsourced** — and
**document 05 §2's derivation of the entire $120 budget rests on that
tolerance.** The most consequential number in Point 5 is derived from a premise
that no reader of this repository can check.

> **RECOMMENDATION: commit the standing brief as a repository artifact before
> Point 4 opens.** It is not a rule change; it is writing down what every frozen
> document already assumes. **A frozen derivation resting on an uncommitted
> premise is only as durable as the conversation that carried it**, and this
> handoff exists precisely because that conversation ends.

### 12.2 THE TRANSFER PROTOCOL HELD ON ARTIFACTS AND FAILED ON DECISIONS

**Every hash-verified file transfer in Point 5 succeeded.** The read-back
protocol from report 23 §5.1 — artifacts by file upload, the chat carrying only
hash, line count, commit and test count — **did not fail once.**

**THE UNVERIFIED CHANNEL FAILED REPEATEDLY.** Chat-to-chat decision transfer,
which carries no hash and has no check: a message echoed back twice in place of a
decision; a paste-back replaced by tool output; a wrong file uploaded.

> **THE VERIFIED PATH HELD AND THE UNVERIFIED PATH BROKE, REPEATEDLY, IN THE SAME
> POINT.** That is as clean a controlled comparison as this project is going to
> get, and it points at one conclusion: **the defect rate is a property of
> whether the channel is checkable, not of what is being carried.**

**THIS BEARS DIRECTLY ON ANY FUTURE AUTOMATION HARNESS.** A harness that passes
artifacts by reference and hash inherits the reliable path. **A harness that
passes decisions as unverified text inherits the one that broke** — and decisions
are exactly what cannot be recovered from the repository afterwards.

---

## 13. HOW TO OPEN POINT 4

**A FRESH CHAT**, with **this document**, **the thesis** (`22` and `22a`) and
**the five frozen design documents** (§2.1) uploaded as handoff. **Not pasted** —
report 23 §5.1.

**THE STANDING WORKING RULES CARRY OVER UNCHANGED:**

- **One point at a time.**
- **Decisions before code.**
- **No code in chat.**
- **Claude Code prompts for anything built.**
- **Friction over compliance** — an objection raised is worth more than an
  instruction followed.
- **The read-back protocol** — artifacts by file upload; the chat carries hash,
  line count, commit and test count only.

**AND TWO ADDED BY THIS POINT:**

- **A mutation that disables a pre-read guard never faces the real data
  directory** (§6.3).
- **Prompts do not name new test files, and target paths are checked before
  writing** (§7.3).

---

## 14. STATUS

**POINT 5 IS CLOSED.** Two pre-registrations, three amendments, seven reports, an
exchange-real sizing layer, a sealed 1m loader and an execution path — **and no
result.**

**THE FROZEN DOCUMENTS ARE FROZEN.** Documents 05, 05a, 05b, 06 and 06a may not be
edited. Document 06 §8.1's escalation clause is now binding on the exit chain: **a
further gap calls for re-specification in one piece, not Amendment 2.**

**THE PERFORMANCE FIREWALL IS ARMED.** No outcome quantity may be computed,
inspected or estimated **until the validation design is separately written,
agreed and committed.** The kill conditions are goalposts; the procedure that
applies them does not yet exist.

**THE HOLDOUT REMAINS SEALED**, with §6's disclosure attached to it permanently.

**HOLDOUT BUDGET, UNCHANGED: ONE CANDIDATE, ONE LOOK, WHOLE WINDOW, NO CANDIDATE
TWO.**

---

**Point 5 produced a rule, an engine and no number, which is what it was opened
to do. Point 4 is now the only thing standing between this project and its first
result — and that is the correct order.**
