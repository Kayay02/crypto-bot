# CONSEQUENCES AND THRESHOLDS — 4.1c's CLOSE

**Point 4, sub-point 4.1c, step 3.** One rule narrowed, one kill condition
disposed of, one threshold committed, two ledger instances logged, and 4.1c
closed. **Nothing is computed and no new width or level is stated.**

## 0. THE SCOPE LIMIT

> ### NO THRESHOLD IN AN OUTCOME QUANTITY IS SET ANYWHERE IN THIS DOCUMENT.

The performance firewall forbids it and §3 is explicit about what it therefore
does and does not dispose of. Report 37's figures are quoted as established facts
about the form they were measured under; **no new width, level or share is
stated.**

**QUOTATIONS ARE RENDERED IN ASCII.** Where a source writes a minus sign or a
not-less-than sign as a typographic character, it appears here as its ASCII
equivalent. The wording is verbatim; only the glyphs are transliterated.

---

## 1. WHAT THIS DOCUMENT IS

**A PRE-REGISTRATION, FROZEN ON COMMIT.** It joins the frozen specification on its
commit, per `docs/design/04_0_divergence_disposition_amendment_2.md` §2's
open-forward clause. Committed alone.

**IT AMENDS `docs/design/04_1c_pre_commitments.md` §3** under that document's §7
change discipline. **That document is not edited.**

---

## 2. PART 1 — THE REJECTION RULE, NARROWED TO POPULATION A

### 2.1 THE DECISION

> ### REJECT APPLIES TO POPULATION A ALONE — THE REQUIRED COST FLOOR EXCEEDING
> ### THE FROZEN CAP. POPULATION B — THE RAW ATR-DERIVED STOP EXCEEDING THE CAP —
> ### IS CLIPPED TO THE CAP.

Clipping population B is what `src/engine/costs.py`'s `stop_geometry` already
does: it takes the ATR distance, floors it at the derived floor, caps it at
`stop_max_pct`, and returns the mechanism that bound. **This decision does not
change the implementation; it narrows a rule that had been committed over a
population its own argument did not reach.**

### 2.2 THE GROUND, AND IT IS THE COST GROUND ALONE

`docs/design/04_1c_pre_commitments.md` §3.2 argued reject-over-clip like this: a
clipped position is taken with a stop **narrower than the constraint requires**,
therefore carries **a larger unvalidated share of its risk unit than the tolerance
permits**, and **is indistinguishable in the data from a compliant position.**

**THAT ARGUMENT IS ABOUT COST PROTECTION AND IT REACHES POPULATION A EXACTLY.**
For A the required floor is above the cap, so a clipped position sits below the
floor the constraint demands and its unvalidated share exceeds the tolerance.
**The argument works.**

**IT DOES NOT REACH POPULATION B.** A population-B position clipped to the cap
carries a stop **at the cap**, and the cap is `stop_max_pct = 0.035`. Report 37
§3.1 gives the required floors at the committed level as 0.597669 and 0.602349
per cent for BTCUSDT and ETHUSDT and 1.041253 and 1.058895 per cent for SOLUSDT.

> ### THE CAP EXCEEDS EVERY REQUIRED FLOOR BY BETWEEN 3.31 AND 5.86 TIMES — THE
> ### SMALLEST MULTIPLE BEING SOLUSDT SHORT AT 3.31, THE LARGEST BTCUSDT AND
> ### ETHUSDT LONG AT 5.86.

That is a ratio of two already-committed facts and not a new derivation.

**A STOP AT THE CAP IS THEREFORE FAR WIDER THAN THE CONSTRAINT REQUIRES, SO ITS
UNVALIDATED SHARE SITS FAR BELOW THE TOLERANCE.** There is nothing for the
cost-protection argument to protect against. **The argument that justified
rejection for A has no purchase on B**, and a rule justified by that argument
cannot be extended to B by the argument that justified it.

### 2.3 THE MECHANISM, STATED IN THE RIGHT DIRECTION

**A RAW ATR STOP ABOVE THE CAP IS CLIPPED TO SOMETHING NARROWER THAN THE BAR'S
VOLATILITY IMPLIES, NOT WIDER.** The position ends up with a tighter stop than its
own volatility called for.

> ### THE COST CASE IS SAFE BECAUSE THE CAP STILL FAR EXCEEDS THE COST FLOOR, NOT
> ### BECAUSE CLIPPING HELPS.

Clipping is a narrowing, and narrowing is the direction the cost argument worries
about. It is tolerable here only because the narrowing stops at a level three to
six times the floor. **If the cap were ever lowered toward the floors, or the
floors raised toward the cap, this decision would have to be remade** — and §2.5
names the condition.

### 2.4 WHAT IS NOT DECIDED

> ### WHETHER A STOP CLIPPED NARROWER THAN VOLATILITY IMPLIES IS ITSELF
> ### UNDESIRABLE IS A SEPARATE QUESTION, ON SEPARATE GROUNDS, AND IS NOT SETTLED
> ### HERE.

It is a question about whether the geometry the strategy was designed around
survives being truncated — whether a position whose stop sits well inside its own
volatility is still the position the thesis describes. **That question is argued
nowhere in this repository.** No committed document takes a position on it, and
this one does not either.

**IT IS NAMED AS OPEN AND IT IS NOT CHARACTERISED AS UNIMPORTANT.** It bears on a
population the frozen cap already truncates today, under a mechanism that predates
this sub-point, and nothing here should be read as having considered and dismissed
it. **Routed at §6.3.**

### 2.5 WHAT THIS DECISION DOES NOT REST ON

**THE DECISION RESTS ON §2.2's COST ARGUMENT AND ON NOTHING ELSE.**

`docs/design/04_0_decision_rule.md` §8 commits the standing principle:
**execution reality over measurement convenience.** It bars a class of
considerations from entering a decision of this kind, and records that a finding
with awkward consequences for existing work **is a finding about the work and not
an argument against the finding.**

**NO CONSIDERATION FROM THAT BARRED CLASS APPEARS ANYWHERE ABOVE**, and none is
offered. A decision resting on one would be reversible by that same rule, which is
reason enough not to build on it.

**THE CONDITION UNDER WHICH THIS IS REMADE:** the cap moving toward the required
floors, or the floors toward the cap, such that the multiple at §2.2 ceases to be
large. That is a statement about the cost ground, which is the only ground here.

### 2.6 THE CONSEQUENCE FOR THE ADMISSIBLE POPULATION

**The admissible population is the candidate population less population A.**
Report 37 §6.1 counts population A at **zero**, so the admissible population is
**unchanged at 11,384**, and every prior measurement over that population
continues to describe the same set.

> ### THIS IS A CONSEQUENCE OF THE DECISION AND WAS NOT A REASON FOR IT.

It is stated because a reader needs to know which population the later steps
range over. **It is recorded after the argument rather than inside it**, and §2.5
records why it could not have been part of the argument.

---

## 3. PART 2 — KILL CONDITION (d), DISPOSED OF

### 3.1 WHAT (d) SAYS, AND THE PROBLEM ITS WORDING NOW HAS

The thesis §7(d): **"FLOOR-STRATUM DECOMPOSITION. Stratify trades by whether the
1.50% floor bound. If the advantage does not survive among NON-floor-bound trades
at >= 0.05R, the thesis is about percentage stop width rather than about sweeps."**

> **(d) NAMES A FLOOR THAT NO LONGER EXISTS.** The 1.50 per cent constant is
> retired; the governing floor is per symbol and per direction, at report 37 §3.1.

**THAT IS NOT AN ERRATUM.** The thesis was correct when written and the floor has
since been superseded by the 4.1 chain. **But (d)'s stratifying predicate is not
executable as written**, and restating it is part of disposing of it.

### 3.2 THE STRATUM

> ### (d) IS EVALUATED ON THE NON-FLOOR-BOUND STRATUM UNDER THE COMMITTED
> ### PER-SYMBOL, PER-DIRECTION FLOOR — NOT UNDER THE RETIRED CONSTANT.

The predicate is unchanged in kind: did the cost floor, rather than the
volatility, set the stop? Only the floor it refers to has moved.

### 3.3 THE LEVEL

> ### (d) IS EVALUATED POOLED OVER THE WHOLE EVALUATION WINDOW. THE PER-FOLD
> ### DECOMPOSITION IS REPORTED AS A STABILITY PROBE AND IS NOT AGGREGATED BY
> ### MAJORITY FOR THIS CONDITION.

**THE FIRST REASON IS THAT THE MAJORITY RULE MISDESCRIBES THE FOLDS.**
`src/folds/schedule.py`'s own docstring states it: adjacent training windows
overlap by fifty per cent, **"the nine folds are a STABILITY PROBE, NOT NINE
INDEPENDENT TRIALS, and if they are ever counted as trials the arithmetic is
wrong."** A majority-of-nine rule counts them as trials. **Applying it to (d)
would be the error that docstring exists to prevent.**

**THE SECOND REASON IS THE ONE §5.9 RAISED, AND IT IS STATED AS A REASON RATHER
THAN LEFT AS A CONVENIENCE.** `docs/handoff/31_point_5_closing.md` §5.9 records
that under the majority rule the condition's verdict turns on the folds where the
stratum is thinnest — which are exactly the folds where it is least measurable.
**Pooling avoids that, and the fact that pooling is also the more forgiving level
is stated here rather than discovered later.** A reader who holds that the more
forgiving level should not be chosen by the party it forgives is entitled to that
objection; the answer offered is the first reason, which does not depend on
thinness at all.

**THE PER-FOLD DECOMPOSITION IS STILL REPORTED.** A pooled verdict that conceals a
fold in which the advantage inverts is a verdict that hides its own weakest
evidence. It is reported and read; it does not aggregate into the condition.

### 3.4 WHETHER §5.9's CONCERN IS ANSWERED

**§5.9's concern was that a small threshold is not detectable on a thin stratum.**

**IT IS ANSWERED ON THE CANDIDATE POPULATION AND NOT ON THE TAKEN POPULATION.**

Report 37 §5.2 measures the non-floor-bound candidate stratum at **11,163 of
11,384, 98.06 per cent**, with the thinnest fold cell at **238** and fold 4 test
still the bottleneck. Against §5.9's figure of roughly **52 per symbol** among
taken trades, the candidate stratum is ample.

> ### BUT (d) IS EVALUATED ON TRADES, NOT ON CANDIDATES, AND THE TWO ARE NOT THE
> ### SAME POPULATION.

`docs/handoff/31_point_5_closing.md` §5.6 establishes that **under the budget with
real exits the traded population is a function of realised outcomes and is not a
subset of anything knowable in advance.** Report 37 §5.1 restates it and declines
to estimate the taken population.

**SO: (d) IS EVALUATED ON THE TAKEN POPULATION, AND THE SIZE OF ITS NON-FLOOR-BOUND
STRATUM IS NOT KNOWABLE AT THIS COMMIT.** The candidate measurement bounds it from
above and establishes that the floor binds rarely under the committed level; it
does not establish how many trades survive the budget. **§5.9's concern is
therefore reduced and not eliminated**, and saying it is eliminated would put a
knowable number where an unknowable one belongs.

### 3.5 THE THRESHOLD IS NOT SET HERE, AND WAS NEVER OWED HERE

**(d)'s THRESHOLD IS ALREADY COMMITTED IN THE THESIS AT 0.05R.** It is an outcome
quantity. **This document does not set it, does not revise it, and does not
evaluate it.** What §5.9 left open was the **level**, which §3.3 disposes of.

> ### WHAT REMAINS OPEN IS NOT THE THRESHOLD BUT WHETHER 0.05R IS DETECTABLE ON
> ### THE STRATUM THAT ACTUALLY MATERIALISES.

That is a question about statistical power on a population whose size is
unknowable before the run, **and it cannot be answered without outcome data.**
**ROUTED to the first-run diagnostic gate** `docs/handoff/31_point_5_closing.md`
§9(f) requires, which must be pre-registered and outcome-independent: the taken
non-floor-bound stratum's **size** is a count, not an outcome quantity, and can be
reported by that gate before any advantage is computed. **If it proves too thin,
that is a finding about the condition's evaluability and must be recorded as one
rather than resolved by moving the threshold.**

---

## 4. PART 3 — THE MAGNITUDE THRESHOLD

### 4.1 THE QUESTION

`docs/handoff/31_point_5_closing.md` §5.3 poses it: **at what magnitude does a
breach of the after-costs risk rule stop being tolerable?** It records that until
it is stated, two decisions running in opposite directions on the same principle
**rest on intuition rather than on a criterion.**

### 4.2 THE THREE CASES THE THRESHOLD MUST MAKE CONSISTENT

- **THE FILL-PRICE TERM**, `docs/handoff/30_point_5_3_4_portfolio.md` §7.3. The
  exit fee is charged on the stop level while the fill sits a haircut away.
  Direction-dependent in sign and **beyond one risk unit for shorts**. At most
  **0.0033 USDT, under 0.017 per cent of a risk unit. ACCEPTED.**
- **THE TREATMENT `docs/design/06_exit_resolution_spec.md` §5.4 REJECTED** —
  charging funding as a realised cash flow per settlement actually crossed, which
  **"lets a stop-out return worse than -1.0R"**. Its magnitude is **1.16 to 1.80
  per cent of a risk unit**, derived at `docs/handoff/32_point_4_0_3_floor_curve.md`
  §4.3 on report 30's reference cells, at the then-governing 1.500 per cent floor.
  **REJECTED.**
- **THE DISPLACEMENT BUDGET**, `docs/design/04_1c_proper.md` §2.1. **Ten per cent
  of one risk unit. ACCEPTED as a contingent envelope.**

**A CORRECTION, MADE RATHER THAN PROPAGATED.** The instruction commissioning this
document attributed the 1.16 to 1.80 per cent figure to report 33. **It is report
32 §4.3.** Report 33 derives a floor curve and carries no such figure.

### 4.3 WHY A MAGNITUDE-ONLY THRESHOLD IS IMPOSSIBLE

> ### THE REJECTED CASE IS SMALLER THAN THE ACCEPTED ONE.

1.16 per cent was rejected; ten per cent was accepted. **Any threshold of the form
"tolerable below X" that rejects 1.16 must reject ten**, and would therefore
reject the displacement budget the same sub-point committed. **No ordering by
magnitude alone can separate these three cases.** That is not a difficulty to be
worked around; it is what tells us the separating property is not magnitude.

### 4.4 THE DISTINCTION THAT DOES SEPARATE THEM

> ### A BREACH THAT OCCURS WITH PROBABILITY ONE UNDER BASELINE MODEL ASSUMPTIONS
> ### IS A DIFFERENT OBJECT FROM A CONTINGENT DISPLACEMENT UNDER AN ADVERSE
> ### ASSUMPTION ABOUT AN UNVALIDATED ESTIMATE.

**A CERTAIN BREACH MISSTATES THE RISK UNIT ON EVERY POSITION IT TOUCHES**, in the
model as specified, with nothing needing to go wrong. It is a defect in the
statement of the rule.

**A CONTINGENT DISPLACEMENT LEAVES THE RULE EXACT IN THE MODEL AS SPECIFIED** and
bounds how far reality may move it if an estimate proves wrong. It is a statement
about how much the rule's authority may rest on modelling — which is precisely
what `docs/design/04_1b_tolerance_and_branch.md` §3.2 identifies the constraint as
protecting.

**WHERE EACH CASE FALLS:**

- **The fill-price term: CERTAIN.** For shorts it lands beyond one risk unit on
  every stop-out, by construction of the fee base. No adverse assumption is
  required.
- **The rejected funding treatment: CERTAIN.** Every stop-out that crossed a
  settlement loses the risk unit plus the funding. §5.4's own words: it *"lets a
  stop-out return worse than -1.0R"*, unconditionally.
- **The displacement budget: CONTINGENT.** It binds only if the unvalidated
  estimates are wrong in the adverse direction.

### 4.5 THE THRESHOLD, COMMITTED

> ### FIRST MODALITY, THEN MAGNITUDE.
>
> ### **(i)** A CONTINGENT DISPLACEMENT IS GOVERNED BY THE DISPLACEMENT BUDGET AT
> ### `docs/design/04_1c_proper.md` §2 AND BY NOTHING IN THIS SECTION. Its
> ### tolerable magnitude is that budget.
>
> ### **(ii)** A CERTAIN BREACH — one occurring with probability one under
> ### baseline model assumptions — IS TOLERABLE ONLY IF ITS MAGNITUDE IS BELOW
> ### THE IMPRECISION WITH WHICH THE RISK UNIT CAN ALREADY BE DELIVERED. THE
> ### ANCHOR IS THE LOT-GRANULARITY DRAG: **0.80 per cent of nominal risk pooled
> ### across the 11,384 candidates**, `docs/handoff/28_point_5_3_1_sizing.md` §8.2.
>
> ### **(iii)** A CERTAIN BREACH AT OR ABOVE THAT ANCHOR IS NOT TOLERABLE, AND IS
> ### REJECTED UNLESS SOME OTHER DOCUMENT ARGUES IT ON ITS OWN GROUNDS.

**WHY THAT ANCHOR.** Flooring quantity to the venue's lot step already means the
risk unit delivered is not the risk unit nominated, by 0.80 per cent pooled. **A
certain breach smaller than that is below the precision at which the rule can be
enforced at all** — it is not the binding imprecision and nothing a reader could
act on turns on it. **A certain breach larger than it becomes the binding
imprecision**, and the rule's stated figure stops describing what the mechanism
delivers.

**IT SEPARATES THE TWO CERTAIN CASES**, which is the test it had to pass: 0.017
per cent is below the anchor and was accepted; 1.16 per cent is above it and was
rejected. **Both prior decisions are reproduced, in the order modality then
magnitude, by a criterion neither of them was chosen against.**

**THE PER-POSITION TAIL IS NOT THE ANCHOR AND THAT IS A CHOICE.** The same report
gives the worst single position's granularity drag as 9.21 per cent. **The anchor
is the pooled figure**, because the threshold governs terms that apply
systematically rather than to one position. **A reader who holds that a worst-case
anchor is the right one would set a far looser threshold**, and §4.6 records that.

### 4.6 WHAT WOULD HAVE MADE A DIFFERENT THRESHOLD CORRECT

Per `docs/design/04_1c_pre_commitments.md` §4.3(d), which requires this and names
it as what distinguishes a criterion from a rationalisation.

- **A DIFFERENT VIEW OF WHAT THE BINDING IMPRECISION IS.** The anchor is
  lot-granularity drag. On a venue with finer lot steps that drag falls and the
  anchor tightens with it; **the threshold is not a constant and is not intended
  to be.** Anchoring instead on the tick grid, or on the worst-position tail,
  gives a different bar — tighter in the first case, far looser in the second.
- **A VIEW THAT MODALITY SHOULD NOT ORDER THE TEST.** A reader holding that a
  breach is a breach regardless of whether it is certain must then either reject
  the displacement budget at ten per cent or accept the funding treatment at 1.16
  per cent. **Naming which is how that reader argues a different threshold**, and
  §4.3 shows there is no third option.

### 4.7 DERIVATION OR JUDGEMENT

**THE ORDERING IS DERIVED.** §4.3 shows that no magnitude-only threshold can
separate the three committed cases, so modality must come first. That is forced by
the cases, not chosen.

**THE ANCHOR IS A JUDGEMENT**, and is recorded as one on the terms
`docs/design/04_1c_proper.md` §2.4 used: **it is selected in this document, on the
argument at §4.5, and it is not the output of any calculation.** No measurement
implies that granularity drag is the right reference rather than another; §4.6
names two alternatives and where they lead. **A reader who disagrees is
disagreeing with a stated judgement, which is the correct thing to be disagreeing
with, and is not being contradicted by evidence.**

---

## 5. PART 4 — THE LEDGER AND THE ERRATA INDEX

### 5.1 THE TOTAL, READ

**`docs/design/04_1d_standing_practices.md` §5.3 states "43 + 1 = 44". The total
read is 44**, so the instances below take **(45)** and **(46)**.

### 5.2 INSTANCE (45)

**A RULE ARGUED ON COST PROTECTION — WHICH REACHES ONLY THE POPULATION WHOSE
REQUIRED FLOOR EXCEEDS THE CAP — WAS COMMITTED OVER BOTH REJECTION POPULATIONS.**

It originated in the instruction that specified
`docs/design/04_1c_pre_commitments.md` §3. That section partitioned A and B
correctly and stated of B that it is **"a volatility rejection, a property of bar
geometry, independent of the tolerance and of cost accounting entirely"** — and
then applied to it a rule whose entire justification is cost accounting. **The
partition and the rule's scope disagree inside one section.**

**SUB-CLASS: the recurring class applied to a specification rather than to a
numerical threshold or a decision criterion** — the sub-class
`docs/design/04_1c_denominator_choice.md` §5.5 assigns to instance **(43)**,
alongside instance **(40)**. **This instance's particular shape is a scope wider
than the argument that justified it.**

**NOT CORRECTED BY EDIT.** §3 stands as written; §2 of this document narrows it.

### 5.3 INSTANCE (46)

**A VERIFICATION CHECK ASSERTED AN EXACT COUNT OF EIGHTEEN MODULES IMPORTING THE
CANONICAL BANNED-NAME LIST, AND FIRED AGAINST A LEGITIMATE NINETEENTH.**

`tests/test_firewall_names.py`, added at commit `47a26de`. Report 37 §7.1 repaired
it as a superset relation over the eighteen named enforcing modules and
**deliberately routed the classification forward** rather than making it, following
`docs/handoff/32_point_4_0_3_floor_curve.md` §8's precedent. **This document makes
it.**

**THE STANDING INCLUSION CRITERION, APPLIED.**
`docs/design/04_1a_denomination.md` §6: a falsely firing check is logged **if and
only if the immediate remediation on offer would have degraded an otherwise
correct artifact.**

> ### IT QUALIFIES. LOGGED.

**THE GROUNDS.** The check fired against `tests/test_level_consequences.py`, which
was correct: it imports the list in order to assert that report 37's derivation
module names no banned quantity. **One immediate remediation on offer was to drop
that import — which would have removed the new module's firewall guard.** That is
the same shape as instance (38), where the remediation on offer was stripping a
required and accurate citation from a module to satisfy an over-broad match.

**THE ALTERNATIVE READING IS NAMED.** A reader may hold that the obvious
remediation was to fix the check rather than the module, that no correct artifact
was ever really at risk, and that this is therefore routine test iteration, which
§6 excludes. **Under that reading the total is 45 rather than 46.** The call made
here is the one above, on the ground that the criterion asks what remediation was
**on offer** and not which one a careful implementer would have taken.

**IT IS ALSO THE RECURRING CLASS APPLIED TO A TEST:** a criterion written from a
snapshot of how many modules happened to enforce the guard, rather than from what
the guard requires.

### 5.4 THE TOTAL

**44 + 2 = 46.**

**No earlier instance is renumbered or recounted**, and the ledger remains
contiguous from (1) to (46).

### 5.5 THE ERRATA INDEX

> ### THIS DOCUMENT CREATES NO ERRATUM. NO ENTRY IS ADDED.

Three candidates were considered and each is something else:

- **§2's narrowing** is an amendment to a rule, not a correction of a statement.
  Nothing in `docs/design/04_1c_pre_commitments.md` §3 is false.
- **§3.1's observation** that kill condition (d) names a retired floor is a
  supersession, not an error. The thesis was correct when written.
- **§4.2's correction** of the 1.16 to 1.80 per cent attribution corrects the
  **instruction** that commissioned this document. Instructions are not frozen
  artifacts and the index does not range over them.

**THE INDEX'S STANDING IS RESTATED BECAUSE IT IS MISLEADING AS IT SITS.**
`docs/design/04_1c_pre_commitments.md` §5 says nine entries in its own text.
**Entry 10 was added by `docs/design/04_1d_standing_practices.md` §4.1**, against
the Point 5 closing record §11's prose statement of the banned set. **The index
therefore stands at TEN IN FACT AGAINST NINE IN ITS OWN TEXT**, and the index is
frozen and cannot be edited. **Its next holder carries ten forward.**

---

## 6. PART 5 — 4.1c's CLOSING POSITION

### 6.1 THE 4.1 CHAIN, WITH COMMITS

**DECISIONS, under `docs/design/`, each a member of the frozen specification:**

- **`04_0_decision_rule.md`**, `77a226b` — the Branch B/C fork, the order and
  direction rules, and the execution-reality principle.
- **`04_1a_denomination.md`**, `b807744` — the stop path denominated, five
  grounds, the dominance check named as owed.
- **`04_1a_denomination_amendment_1.md`**, `02992c7` — the numerator narrowed to
  the unvalidated term; the standing verification rule adopted.
- **`04_1b_tolerance_and_branch.md`**, `56a11f6` — Branch B chosen; the protected
  quantity defined; the rationale reported as not discriminating between values.
- **`04_1c_non_uniformity_check.md`**, `af7866d` — the non-uniformity threshold,
  committed before its numbers existed. **Now inapplicable, not falsified.**
- **`04_1c_path_and_scope.md`**, `506977b` — path two committed as the risk unit;
  funding committed into the unvalidated set.
- **`04_1c_denominator_choice.md`**, `a9083b0` — the constraint denominated in the
  risk unit itself; the prior apparatus declared inapplicable.
- **`04_1c_pre_commitments.md`**, `5ec36c0` — the admitted domain; reject-over-clip
  and the two populations; the five disqualifying properties; the errata index.
- **`04_1c_level_method.md`**, `1a0aa24` — one method attempted and disqualified;
  the dominance obligation discharged as moot.
- **`04_1c_proper.md`**, `db3a6de` — the displacement budget, the uncertainty
  parameter and its scope, the comparator's reconciliation rule.
- **`04_1d_standing_practices.md`**, `fc8933f` — four practices committed as
  rules, three recorded as conventions, erratum entry 10.
- **this document** — the rejection rule narrowed, (d) disposed, the magnitude
  threshold committed, 4.1c closed.

**MEASUREMENTS, under `docs/handoff/`, which bind nothing:**

- **`32_point_4_0_3_floor_curve.md`**, `5c55776` — the original parametric floor
  and the rejected treatment's magnitude. Superseded as governing.
- **`33_point_4_1a_revised_derivation.md`**, `22e323a` — the closed form over the
  stop distance. Superseded as governing.
- **`34_point_4_1a_non_uniformity_rerun.md`**, `3007dbd` — the re-run. Superseded
  as governing.
- **`35_point_4_1c_denominator_audit.md`**, `2983cac` — the two cost paths
  established. Unaffected.
- **`36_point_4_1c_risk_unit_derivation.md`**, `e4122b6` — **the governing closed
  form**, the achievable range, the committed grid.
- **`37_point_4_1c_level_and_consequences.md`**, `eebe986` — **the governing level
  and widths**, the comparator, the stratum, population B's first count.

### 6.2 THE LEVEL AND THE WIDTHS

**THE LEVEL IS 0.10**, from `docs/design/04_1c_proper.md` §2 and §3, reported at
`docs/handoff/37_point_4_1c_level_and_consequences.md` §2, which states its status:
**the budget divided by one, a re-description and not a derivation**, disclosed in
advance as possibly round, defended by commit order alone.

**THE WIDTHS**, report 37 §3.1, as a percentage of entry: **BTCUSDT and ETHUSDT
0.597669 long and 0.602349 short; SOLUSDT 1.041253 long and 1.058895 short.**
Feedback residual 8.049e-16.

### 6.3 WHAT REMAINS OWED, AND TO WHOM

**INSIDE POINT 4:**

1. **(d)'s DETECTABILITY** — whether 0.05R is detectable on the taken
   non-floor-bound stratum. §3.5. **Owed to the first-run diagnostic gate** at
   `docs/handoff/31_point_5_closing.md` §9(f).
2. **THE VOLATILITY QUESTION** — whether a stop clipped narrower than volatility
   implies is itself undesirable. §2.4. **Argued nowhere. Owed to whichever step
   takes up the cap**, and it has no owner at this commit.
3. **POINT 4's REMAINING AGENDA**, `docs/handoff/31_point_5_closing.md` §9(a)
   through (g): the fold structure and aggregation rule, the metrics and the level
   each is computed at, the kill conditions restated for the capped population,
   the parameter-sensitivity criterion, the order of inspection, the first-run
   diagnostic gate, and the disposition of every §5 open item. **4.1 discharged
   the cost-tolerance constraint and (d)'s stratum and level. The rest stands.**

**QUEUED FOR POINT 6**, per `docs/design/04_1c_proper.md` §7.3:

4. **The expiry re-argument**, `docs/design/04_1b_tolerance_and_branch.md` §3.5,
   enlarged by `04_1a_denomination_amendment_1.md` §5.2.
5. **Folding measured slippage into the unvalidated set.**
6. **Re-evaluating the achievable domain**, since a non-zero slippage moves the
   ceiling and therefore the grid built inside it.
7. **The empirical audit of the displacement budget**, the judgement's falsifier.

**HOUSEKEEPING:**

8. **THE ERRATA INDEX SHOULD BECOME A STANDALONE ARTIFACT.** It lives inside a
   frozen document that cannot be edited, so every entry after its own commit sits
   somewhere else — §5.5 above, and §4.1 of the standing-practices document.
   **An index whose entries are scattered across the documents that made them is
   the failure it was created to solve.**
9. **`docs/prompts/STANDING_RULES.md` §12 IS OUT OF DATE.** It describes seven
   practices as uncommitted; four were committed at `fc8933f`. That file is
   amended by a new file and never edited, so an amendment is owed.

### 6.4 THE POSITION

> ### SUB-POINT 4.1c IS CLOSED. SUB-POINT 4.1 IS CLOSED.

**WHAT 4.1 PRODUCED:** a constraint denominated in the risk unit, a closed form
for the floor it implies, a level reached by a judgement recorded as judgement, the
widths that follow, a stratification, the first count of a population that had been
defined but never counted, and a magnitude threshold that makes three prior
decisions consistent. **And no performance figure.**

**THE NEXT OPEN ITEM IS POINT 4's REMAINING AGENDA AT
`docs/handoff/31_point_5_closing.md` §9.** **No committed document fixes a
sub-point numbering beyond 4.1**, so the next step's label is for whoever opens it;
its subject is §9(a) through (g) less what 4.1 discharged.

---

## 7. CHANGE DISCIPLINE

**A CHANGE TO ANY COMMITMENT HERE IS A NEW DOCUMENT WITH ITS OWN COMMIT AND AN
EXPLICIT STATEMENT OF WHAT CHANGED AND WHY — NEVER A SILENT EDIT.** It would be
`docs/design/04_1c_consequences_and_thresholds_amendment_1.md`.

**A SILENT EDIT IS A CONTAMINATION EVENT.**

**THE CLAUSE MOST EXPOSED IS §4.5's ANCHOR.** It is a judgement that will first be
inconvenient when a certain breach lands just above 0.80 per cent and the tempting
move is to re-anchor on the worst-position tail, which §4.5 records as giving a far
looser bar. **An amendment doing that after such a breach is known must say so in
those words.**

---

**Committed alone. One rejection rule narrowed to the population its argument
reaches, on the cost ground alone, with the multiple stated and the mechanism
stated in the right direction; one open question named and not dismissed; one kill
condition disposed of as to stratum and level, with its detectability routed and
the taken population's unknowability stated rather than estimated; one magnitude
threshold committed, ordered by modality because no ordering by magnitude can
separate the committed cases, with its anchor recorded as judgement and two
alternatives named; two ledger instances logged at 44 + 2 = 46 with the close call
on the second argued both ways; no erratum created and the index's true standing
restated; 4.1c and 4.1 closed. No threshold in an outcome quantity is set, and no
new width or level is stated.**
