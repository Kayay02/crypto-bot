# REPORT 37 — THE LEVEL AND ITS CONSEQUENCES

**Point 4, sub-point 4.1c, step 2.** A MEASUREMENT. **Nothing is decided and
nothing is disposed of.**

**WHY THIS SITS UNDER `docs/handoff/`.** It is a measurement, not a decision.
Design documents join the frozen specification on commit per
`docs/design/04_0_divergence_disposition_amendment_2.md` §2; **a measurement does
not.** `docs/design/04_1c_proper.md` §6.1 required this step to be filed here on
that ground.

**EVERY INPUT WAS COMMITTED BEFORE THIS STEP RAN.** The budget and the
uncertainty parameter at `docs/design/04_1c_proper.md` §2 and §3, commit
`db3a6de`; the admitted domain and the rejection populations at
`docs/design/04_1c_pre_commitments.md` §2 and §3, commit `5ec36c0`; the closed
form and the grid at `docs/handoff/36_point_4_1c_risk_unit_derivation.md`, commit
`e4122b6`.

---

## 1. PROVENANCE

- **Derivation module:** `src/analysis/level_consequences.py`. It is a
  measurement over the candidate population, which is what `src/analysis/` is
  for.
- **Report 36's closed form is IMPORTED, never reimplemented.**
  `src/analysis/risk_unit_floor_curve.py` is not modified; a test asserts this
  module defines no `required_floor_fraction` and no `ratio_at_width` of its own.
- **Tests:** `tests/test_level_consequences.py` — path chosen after listing
  `tests/` in full and probing three candidates; all three were free and the
  first was taken.

**NOT MODIFIED:** everything under `src/engine/`, `src/risk/`, `src/timeframe/`,
`src/folds/`; `src/analysis/risk_unit_floor_curve.py`, `floor_curve.py`,
`haircut_floor_curve.py`, `haircut_share.py`, `haircut_share_rerun.py`; every
document under `docs/design/`.

### 1.1 THE SEAL

**NOTHING UNDER A SEALED PARTITION WAS OPENED.** The barrier is asserted **once
per symbol in this module immediately before delegating**, and again **once per
symbol inside `floor_curve.candidate_population` immediately before each read** —
two assertions rather than one, because a barrier verified in one module and
relied on from another is a barrier assumed at the call site. That is report 29
§9.1's finding applied.

**VERIFIED AT RUNTIME.** Every file open during the population build was traced
for a sealed year partition: **zero.** The bars read are the 15m and resampled 1h
layers over 2022-01-05 to 2024-12-31.

**THE BARRIER IS PROBED IN THE FIRING DIRECTION** by test, on both sealed years,
with an unsealed path required to pass — so the assertion is shown to
discriminate rather than merely to raise.

---

## 2. PART 1 — THE LEVEL

### 2.1 THE VALUE

> ### THE LEVEL IS 0.10.

`docs/design/04_1c_proper.md` §2.1 commits the displacement budget at **ten per
cent of one risk unit**. §3.1 commits the uncertainty parameter at **one hundred
per cent proportional error**. §4.1 commits the relation: the admitted share is
the budget divided by the error.

### 2.2 ITS EPISTEMIC STATUS, STATED EXACTLY

> ### THE DIVISOR IS ONE. THIS IS AN IDENTITY, NOT A CALCULATION, AND IT IS NOT
> ### PRESENTED AS ONE.

`docs/design/04_1c_proper.md` §4.2 commits that the calibration **re-describes**
the tolerance rather than deriving it. Nothing was learned about the world
between that document and this number. The judgement was made once, in the units
where it could be made, and the conversion to the constrained ratio's units is
division by one.

**THE LEVEL IS A ROUND FIGURE, AND THAT WAS DISCLOSED IN ADVANCE.** §4.3 of that
document stated, before any level existed, that the relation is simple enough
that the result might be round; that a round number emerging from a judgement
calibration is exactly the appearance this sub-point has guarded against
throughout; and that the document could not answer the suspicion by argument,
because any argument would be equally available to someone who had chosen the
number first.

> ### THE DEFENCE IS THE COMMIT ORDER AND NOT THE ARITHMETIC.

**THE SEQUENCE A READER CAN CHECK IN `git log`:**

- **`5ec36c0`** — the standard a level-setting method must meet, committed before
  any method was proposed.
- **`1a0aa24`** — one method proposed, tested and reported disqualified on
  property (b), with no level stated.
- **`db3a6de`** — the budget and the uncertainty parameter, with no level and no
  width stated anywhere in the document.
- **this commit** — the level, following mechanically.

**THE INPUTS PRECEDE THE OUTPUT IN SEPARATE COMMITS.** That is the whole of the
defence and it was named as such before the output existed.

### 2.3 IT LIES INSIDE THE ADMITTED DOMAIN

`docs/design/04_1c_pre_commitments.md` §2.1 admits the tolerance only within the
interval common to all cells. Report 36 §2.4 gives that interval as
**0.03554692 to 0.40**, bounded below by SOLUSDT short's value at the frozen cap
and above by BTCUSDT and ETHUSDT's zero-width ceiling.

**0.10 IS INSIDE IT**, and inside every individual cell's range: BTCUSDT and
ETHUSDT long from 0.02117068, short from 0.02207163, both to 0.40; SOLUSDT long
from 0.03378378, short from 0.03554692, both to 0.52. **Checked, not assumed.**

---

## 3. PART 2 — THE FLOOR WIDTHS

### 3.1 THE WIDTHS

Report 36's closed form evaluated at the level, as a percentage of the entry
price, per symbol and per direction.

- **BTCUSDT long: 0.597669 per cent.** Short: **0.602349 per cent.**
- **ETHUSDT: identical to BTCUSDT at both directions**, sharing every rate the
  constraint touches.
- **SOLUSDT long: 1.041253 per cent.** Short: **1.058895 per cent.**

**Shorts require the wider floor at every symbol**, which is report 36 §3.4's
derived direction split — the haircut and the stop-leg fee are charged on a stop
price that sits above entry on a short.

### 3.2 THE FEEDBACK CHECK

Every width was fed back through the path-two denominator, the unvalidated sum
and the risk unit recomputed **from the engine's own functions**, and the ratio
required to equal the level it was solved for.

> **MAXIMUM ABSOLUTE FEEDBACK RESIDUAL ACROSS ALL SIX CELLS: 8.049e-16.**

**No cell exceeds the frozen cap**, which §6.1 counts rather than assumes.

### 3.3 AGAINST THE RETIRED CONSTANT FLOOR — ORIENTATION ONLY

The retired constant floor was 1.50 per cent. Against it, every width at this
level is narrower: BTCUSDT and ETHUSDT by about 0.90 percentage points, SOLUSDT
by about 0.45.

> ### THIS COMPARISON IS ORIENTATION AND NOT JUSTIFICATION.

`docs/design/04_1c_pre_commitments.md` §4.3(a) makes selection of a level **by
reference to the floor widths it implies — including because they are close to
the retired 1.50 per cent floor — a DISQUALIFYING property** of a level-setting
method. The comparison is given so a reader who has carried the old number in
their head can locate these, **and it is evidence for nothing.** A test asserts
over the module's AST that the retired constant is read by the reporting function
alone and enters no computation.

---

## 4. PART 3 — THE STRESS COMPARATOR

### 4.1 THE WORST CELL, NAMED

`docs/design/04_1c_proper.md` §5.3 committed the reconciliation rule and
**deliberately did not name the symbol**, leaving the identification to this step
because it is a comparison of rates.

The haircut's share of the unvalidated sum, at zero width:

- **BTCUSDT and ETHUSDT: 0.625** — five bps of eight.
- **SOLUSDT: 0.769231** — ten bps of thirteen.

> ### THE WORST CELL IS SOLUSDT, AND IT IS SOLUSDT SHORT THAT BINDS.

### 4.2 THE COMPARATOR'S LEVEL

Under haircut-only scoping the budget is spent on the haircut alone, so the
binding condition is that the haircut's share of the risk unit reaches the
budget. Solving it per cell gives implied levels of **0.16017984** and
**0.15981984** for BTCUSDT and ETHUSDT long and short, and **0.13022480** and
**0.12977480** for SOLUSDT.

> ### APPLYING §5.3's RULE, THE BINDING COMPARATOR LEVEL IS 0.12977480, FROM
> ### SOLUSDT SHORT.

At that level the other symbols are protected **more tightly than the budget
requires**, which is what §5.3 says happens and which a test asserts by computing
their haircut share of the risk unit and requiring it below the budget, while
requiring SOLUSDT short to meet it exactly.

### 4.3 THE COMPARATOR'S WIDTHS

At the binding comparator level, as a percentage of entry: **BTCUSDT and ETHUSDT
0.415309 long and 0.417602 short; SOLUSDT 0.747173 long and 0.756353 short.**
Feedback residual 1.055e-15.

### 4.4 WHAT IT COSTS, AND NOTHING MORE

**THE COMPARATOR IS LOOSER THAN THE COMMITTED LEVEL — 0.1298 against 0.10 — SO IT
WOULD DEMAND NARROWER FLOORS.**

That is the direction that makes it informative: **stressing the whole
unvalidated bundle is more conservative than stressing the haircut alone**, and
the committed scoping therefore buys its symmetry of ignorance at the price of
roughly a third more width. The widths above make that price visible in the units
the floor is stated in.

> ### IT DOES NOT GOVERN, AND §5.4 FORBIDS ITS RESULT FROM REOPENING THE SCOPE
> ### DECISION.

That section committed in advance that a comparator showing the committed scoping
materially looser **is information for the Point 6 audit, not grounds to revise
the scope after seeing what it costs**, because revising a scope once its cost is
visible is selecting the scope by its consequence. **This report reports it and
stops.** A test asserts the comparator cannot move the level.

---

## 5. PART 4 — THE STRATUM

### 5.1 THE POPULATION

**11,384 candidates**, the same population every prior report used: BTCUSDT
3,735, ETHUSDT 3,715, SOLUSDT 3,934. Every signal, before any allocation.

**THIS IS THE CANDIDATE POPULATION AND NOT THE TAKEN POPULATION.**
`docs/handoff/31_point_5_closing.md` §5.6 establishes that under the budget with
real exits **the traded population is a function of realised outcomes** — a
stop-out frees its slot hours before a time exit would — **and is not a subset of
anything knowable in advance.**

> **THE TAKEN POPULATION IS NOT COMPUTED HERE, AND REPORT 26's MAXIMUM-HOLD
> COUNTS ARE NOT REUSED AS A PROXY FOR IT.** They describe a different rule's
> population. Substituting them would put a knowable number where an unknowable
> one belongs, which is the error §5.6 exists to prevent.

### 5.2 FLOOR BINDING, PER SYMBOL AND POOLED

Floor binding is pure bar geometry: the floor binds when the ATR-derived stop
falls below the required floor width. It is decidable on candidates with no
exits, no allocation and no path dependence.

- **BTCUSDT: 154 of 3,735 floor-bound, 4.12 per cent. Non-floor-bound 3,581.**
- **ETHUSDT: 51 of 3,715 floor-bound, 1.37 per cent. Non-floor-bound 3,664.**
- **SOLUSDT: 16 of 3,934 floor-bound, 0.41 per cent. Non-floor-bound 3,918.**
- **POOLED: 221 of 11,384 floor-bound, 1.9413 per cent. Non-floor-bound 11,163.**

**FOR ORIENTATION AND NOT AS A COMPARISON OF LIKE WITH LIKE:**
`docs/design/04_0_decision_rule.md` §4 records the floor-binding fraction at the
retired 1.500 per cent constant floor as **25.71 per cent pooled** across the same
11,384 candidates. **The widths at this level are narrower, so the floor binds far
less often.** The ordering of symbols has also inverted: under a constant floor
the binding symbol was whichever was least volatile relative to price; under a
per-symbol floor SOLUSDT carries the widest floor and binds least, because its
volatility is larger still.

### 5.3 PER FOLD PERIOD

The eighteen fold periods are `src/folds/schedule.py`'s nine folds in train and
test. **Adjacent training windows overlap by 50 per cent, so a candidate can fall
in more than one period and the period counts do not sum to the population.**
Reported as counts per period, not as a partition.

- **Fold 1 train:** 1,929 candidates, 0 floor-bound, 0.00 per cent,
  non-floor-bound 1,929. **Fold 1 test:** 884, 39 bound, 4.41 per cent, 845.
- **Fold 2 train:** 1,851, 39 bound, 2.11 per cent, 1,812. **Fold 2 test:** 885,
  38 bound, 4.29 per cent, 847.
- **Fold 3 train:** 1,769, 77 bound, 4.35 per cent, 1,692. **Fold 3 test:** 843,
  12 bound, 1.42 per cent, 831.
- **Fold 4 train:** 1,728, 50 bound, 2.89 per cent, 1,678. **Fold 4 test:** 906,
  113 bound, 12.47 per cent, **793.**
- **Fold 5 train:** 1,749, 125 bound, 7.15 per cent, 1,624. **Fold 5 test:** 975,
  11 bound, 1.13 per cent, 964.
- **Fold 6 train:** 1,881, 124 bound, 6.59 per cent, 1,757. **Fold 6 test:** 982,
  0 bound, 0.00 per cent, 982.
- **Fold 7 train:** 1,957, 11 bound, 0.56 per cent, 1,946. **Fold 7 test:** 981,
  7 bound, 0.71 per cent, 974.
- **Fold 8 train:** 1,963, 7 bound, 0.36 per cent, 1,956. **Fold 8 test:** 1,075,
  0 bound, 0.00 per cent, 1,075.
- **Fold 9 train:** 2,056, 7 bound, 0.34 per cent, 2,049. **Fold 9 test:** 1,036,
  1 bound, 0.10 per cent, 1,035.

**888 CANDIDATES FALL IN NO FOLD PERIOD** — they precede the in-sample window's
2022-04-01 opening — **and are reported rather than dropped**, because a count
that silently loses rows is a count nobody can reconcile. None is floor-bound.

### 5.4 THE THINNEST CELL, AND WHETHER FOLD 4 TEST REMAINS THE BOTTLENECK

> ### YES. FOLD 4 TEST IS THE BOTTLENECK AT EVERY GRANULARITY MEASURED.

- **Pooled by period**, its 793 non-floor-bound is the smallest of the eighteen,
  and its 12.47 per cent binding fraction is the largest.
- **By symbol within period**, the two thinnest cells in the whole table are
  **fold 4 test ETHUSDT at 238 non-floor-bound (14.70 per cent bound)** and
  **fold 4 test BTCUSDT at 244 (21.79 per cent bound)** — the two highest binding
  fractions anywhere.

**THE COMPARISON WITH THE PRIOR RECORD IS NOT LIKE FOR LIKE AND THE DIFFERENCE
MATTERS.** `docs/handoff/31_point_5_closing.md` §5.9 gives the prior worst as fold
4 test with **495 taken** and **68.28 per cent floor-bound among taken**, leaving
about **157 non-floor-bound pooled across three symbols, roughly 52 per symbol**,
and observes that a 0.05R threshold is not detectable on 52 trades.

> **THOSE ARE TAKEN COUNTS. THESE ARE CANDIDATE COUNTS. THEY ARE NOT
> COMPARABLE**, and the taken counts under this level cannot be computed at all,
> for §5.6's reason.

**WHAT CAN BE SAID:** the same cell is the bottleneck under both, and on the
candidate population the stratum there is 793 pooled and 238 at the thinnest
symbol rather than 157 and 52. **Whether the taken stratum is correspondingly
thicker is not established here and this report does not estimate it.**
Kill condition (d)'s disposition is step 3's and **is not touched.**

---

## 6. PART 5 — THE REJECTION POPULATIONS

### 6.1 POPULATION A — THE REQUIRED FLOOR ABOVE THE CAP

`docs/design/04_1c_pre_commitments.md` §3 defines it and states it is empty
across the admitted domain by construction, the domain's lower bound being the
largest per-cell ratio at the cap.

> ### COUNTED, NOT ASSUMED: ZERO, ACROSS ALL 11,384 CANDIDATES AND ALL SIX CELLS.

**A count of zero reported is evidence; a count of zero assumed is a restatement
of the definition.** `docs/design/04_1c_proper.md` §6.3 required the count.

### 6.2 POPULATION B — THE ATR-DERIVED STOP ABOVE THE CAP

**THE FIRST COUNT. NOTHING IN THIS REPOSITORY HAD COUNTED IT.**

- **BTCUSDT: 117 of 3,735, 3.13 per cent.**
- **ETHUSDT: 350 of 3,715, 9.42 per cent.**
- **SOLUSDT: 1,500 of 3,934, 38.13 per cent.**
- **POOLED: 1,967 of 11,384, 17.28 per cent.**

Per fold period, in the same order as §5.3: 621 and 101; 342 and 160; 261 and 31;
191 and 44; 75 and 217; 261 and 203; 420 and 118; 321 and 109; 227 and 110. **253
fall outside every fold period.** Its worst cells are SOLUSDT in fold 1 train, 393
of 707 at 55.6 per cent, and SOLUSDT in fold 7 train, 363 of 666 at 54.5 per cent.

**IT IS BAR GEOMETRY AND IS INDEPENDENT OF THE LEVEL ENTIRELY.** No value of the
tolerance changes its membership by one candidate. A test asserts this by
recomputing at a different level and requiring the population unchanged, while
requiring floor binding to change — so the comparison has content.

**IT IS ALSO LARGE, AND UNEVEN.** More than a third of SOLUSDT's candidates ask
for a stop the frozen cap forbids. That is a fact about volatility against a
frozen cap and **this report draws no conclusion from it**; it is the first
measurement of a quantity that was defined but never counted.

### 6.3 HOW THE TWO INTERACT

> ### THEY DO NOT OVERLAP: ZERO CANDIDATES ARE BOTH FLOOR-BOUND AND ABOVE THE
> ### CAP. 1,967 are above the cap only, 221 are floor-bound only, 9,196 are
> ### neither.

**AND THIS IS NECESSARY RATHER THAN INCIDENTAL, WHILE POPULATION A IS EMPTY.**
Floor binding means the ATR stop falls **below** the required floor; population B
means it rises **above** the cap. Both can hold only if the floor exceeds the cap
— which is population A. **Population A being empty is exactly the condition that
makes the two disjoint**, and §6.1 counts it as empty.

**THE PROOF IS EXERCISED IN THE DIRECTION THAT WOULD BREAK IT.** A test forces
the cap below the required floor, confirms population A becomes non-empty, and
requires the two predicates to coincide — so the disjointness reported above is a
property of the configuration rather than an artefact of the measurement.

**A REJECTED CANDIDATE IS NOT FLOOR-BOUND, BECAUSE IT IS NOT A POSITION.** Under
`docs/design/04_1c_pre_commitments.md` §3's reject-over-clip rule a population-B
candidate never enters the population, so the 1,967 are removed before the
floor-binding question is asked of anything. **The stratification of §5 therefore
describes candidates of which 1,967 would be rejected**, and a later step needing
the admitted population must subtract them. **This report does not subtract them**,
because §5's counts answer the question §5.9 asked, which was about the candidate
population, and changing the denominator mid-report would make the two
incomparable.

---

## 7. WHAT THIS REPORT DOES NOT DO

**IT DISPOSES OF NOTHING.** Kill condition (d) is untouched, no magnitude
threshold is set, and nothing committed is revised. §5.4 supplies the
stratification (d)'s disposition will need and does not make it.

**IT COMPUTES NO OUTCOME QUANTITY.** No exit was resolved; `exit_reason` was not
read; the execution loop was not invoked and `portfolio.size_position` is called
nowhere, asserted over the module's AST.

**IT DOES NOT ESTIMATE THE TAKEN POPULATION** and does not reuse report 26's
counts as a proxy.

**THE COMPARATOR DOES NOT GOVERN** and its result does not reopen the scope.

### 7.1 ONE FINDING ABOUT A TEST, ROUTED AND NOT CLASSIFIED

**`tests/test_firewall_names.py`'s import check, added at commit `47a26de`,
asserted that exactly eighteen modules import the canonical banned-name list.**
This step's new test module legitimately imports it — to assert the derivation
module is clean — and the check fired against it.

**IT IS THE RECURRING CLASS APPLIED TO A TEST: a criterion written from a
snapshot of how many modules happened to enforce the guard, rather than from what
the guard requires.** The assertion has been restated as a superset relation over
the eighteen named modules, so that a module **dropping** its guard still fails
while a module **adding** one does not.

> **CLASSIFICATION IS LEFT TO WHOEVER NEXT TOUCHES THE LEDGER**, following the
> precedent at `docs/handoff/32_point_4_0_3_floor_curve.md` §8, which recorded a
> falsely firing check and deliberately left its classification to the next
> document. **This report disposes of nothing, including this.** The standing
> inclusion criterion at `docs/design/04_1a_denomination.md` §6 is the rule that
> applies, and the fact a reader needs in order to apply it is that one available
> remediation was to drop the import from an otherwise correct new module.

---

## 8. ARTIFACTS

- **Report:** `docs/handoff/37_point_4_1c_level_and_consequences.md`
- **Module:** `src/analysis/level_consequences.py`
- **Tests, 19 added:** `tests/test_level_consequences.py`

**Full suite: 1280 passed** — 1261 before this step, plus the 19 above.
