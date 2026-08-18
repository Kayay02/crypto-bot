# REPORT 44 — STEP REPORT-BACK: SUB-POINT 4.3a, THE METRIC VOCABULARY

## 0. GENRE

**A STEP REPORT-BACK, NOT AN ANALYSIS REPORT.** Declared here because
`docs/design/04_2e_housekeeping.md` §5.2 files both kinds in one numeric sequence
under `docs/handoff/` and requires the genre to be carried by the document.
Written to a file and committed with the step it reports; the chat channel carries
this file's path, its SHA-256, its line count, the commit hash and the test count,
and discussion, and no other account of the work.

**THE COMMIT HASH IS NOT IN THIS FILE AND CANNOT BE** — a file recording its own
commit's hash changes that hash.

**NOT A MEMBER OF THE FROZEN SPECIFICATION.** Evidence, per
`docs/design/04_0_divergence_disposition_amendment_2.md` §2.

**NO BANNED NAME APPEARS BELOW**, following the document it reports.
`docs/handoff/31_point_5_closing.md` §9(b) enumerates seven quantities and six of
the seven are on the enforced list; they are referred to as "the seven quantities
§9(b) enumerates" throughout.

**NOTHING WAS COMPUTED. NO CODE WAS CHANGED. NO ARTIFACT UNDER
`docs/design/04_2a_artifact_containment.md` §3's PROHIBITION, AS AMENDED AT
`docs/design/04_2e_housekeeping.md` §2.2, WAS OPENED.**

---

## 1. THE STEP

**ONE DOCUMENT, `docs/design/04_3a_metric_vocabulary.md`**, 1,070 lines,
committing definitions, levels, denominator handling and the two-tier
admissibility policy. **Three files in the commit:** the document,
`docs/prompts/MANIFEST.md` by that file's maintenance rule, and this report-back
under the third single-file exemption `docs/design/04_2e_housekeeping.md` §5.3
creates.

**NO THRESHOLD IS SET, NO KILL CONDITION IS COMMITTED, AND NO MEMBERSHIP IS
CLOSED.**

---

## 2. THE MANIFEST

**HASH ON ENTRY:**
`e7580fdd51670e5e1e9f455c5175be7e2c7a193a06016c254d73c0a7d11763fe`

**VERIFICATION: 64 hashed entries parsed, 64 match, 0 mismatches, 0 missing.**
Every hash recomputed from the working tree; none compared against a value quoted
in another document. **The four unhashed engine entries at §4 all exist.**

**`docs/prompts/STANDING_RULES.md` MATCHES THE SUPPLIED HASH:**
`da63e28104e41890dfea438b95f98ca67e4972034e4cbc8505e894c0a0077873`.

---

## 3. THE TWO TIERS, AND THE CHECKABLE PROPERTY

**A DECISION METRIC** is a quantity that a committed kill condition, threshold or
gate consumes as an input. **A DIAGNOSTIC METRIC** is a quantity that verifies the
run executed as specified.

**THE TWO ARE EXHAUSTIVE OF WHAT IS COMPUTED**, because §2.2 commits that a
quantity is computed if and only if a committed decision consumes it or it
verifies the specification. **The default is not to compute and the burden is on
the quantity**, which must name the decision or the clause. "It might be
interesting" is not a naming.

### 3.1 THE PROPERTY THAT DISTINGUISHES THEM

> ### **A DIAGNOSTIC METRIC APPEARS AS AN INPUT TO NO KILL CONDITION, NO
> ### THRESHOLD AND NO GATE OUTCOME, AND NO COMMITTED DECISION REFERENCES ONE.**

**"INADMISSIBLE FOR EVALUATING THE THESIS" WAS REJECTED AS THE FORM**, because it
is a rule about intent and intent is not checkable: a reader cannot verify what a
figure was meant for, and a step that used one otherwise would leave no trace.
**Under the committed form, whether a figure is diagnostic is a fact about the
decision graph** — the conditions are in 4.4, the gate in 4.6, and each names its
inputs, so the tier is read off the inputs.

**AND THE PROPERTY IS DIRECTIONAL, WHICH IS THE PART WORTH FLAGGING.** It
constrains the **decision** side — no condition may reference a diagnostic — rather
than the diagnostic's own definition. **A rule written the other way round would
be satisfiable by relabelling**, since nothing stops a step calling a quantity
diagnostic while a condition quietly consumes it. Written this way, the condition
is what would have to change.

### 3.2 THE BOUND ON THE DIAGNOSTIC TIER

**WITHOUT ONE THE TIER SWALLOWS THE DEFAULT**, because any quantity can be
described as verifying something.

> ### **EACH DIAGNOSTIC NAMES THE SPECIFICATION CLAUSE IT CHECKS, BY DOCUMENT AND
> ### SECTION. A DIAGNOSTIC THAT CHECKS NOTHING COMMITTED IS NOT A DIAGNOSTIC.**

**THE CITATION IS THE BOUND and is not a formality**: a clause is a statement that
can be false, so naming one commits the diagnostic to a falsifiable claim. The
tier is therefore bounded by the specification's own size, which is finite and
readable, rather than by anyone's judgement about usefulness.

### 3.3 PROMOTION

A diagnostic needed as a gate's input **is promoted by an amendment with its own
commit, made before the figure is inspected.** It is not reclassified in the
moment, and **a decision resting on an unpromoted diagnostic is a contamination
event.** The ground is `docs/design/04_0_decision_rule.md` §4's: the guard is
order, the commit hash is the evidence, and it survives everyone's account of what
they were thinking.

---

## 4. WHETHER A DIAGNOSTIC MAY BE AN OUTCOME QUANTITY

> ### **YES, AND UNDER FOUR CONSTRAINTS.**

The question could not be avoided: verifying that costs were charged as the model
says means checking an identity whose terms are outcome-denominated. Report 28
§7's identity — a stop returns exactly -1.0R in that trade's own realised risk
unit — is the paradigm case and is already relied on by
`docs/design/04_2d_aggregation.md` §8.2.

**(a) THE CLAUSE IT VERIFIES IS ITSELF ABOUT AN OUTCOME QUANTITY.** A diagnostic
does not acquire a licence by being a diagnostic; it acquires one where the clause
is stated in outcome terms and cannot be checked otherwise.

**(b) IT IS REPORTED AS A VERIFICATION STATISTIC, NOT AS THE QUANTITY'S OWN
DISTRIBUTION.** The admissible forms are **a count of violations** and **a maximum
absolute deviation from the identity**. The inadmissible form is the outcome's
distribution, mean, or any figure from which one could be reconstructed.

> **A RESIDUAL AGAINST AN IDENTITY IS NOT THE QUANTITY THE IDENTITY IS ABOUT.**
> `|realised R + 1.0|` over a stop-exited position says whether the arithmetic
> holds and says nothing whatever about how the strategy performed.

**(c) THE §3.1 PROPERTY HOLDS UNCONDITIONALLY** — not relaxed for outcome-bearing
diagnostics, which is where the relaxation would do the damage.

**(d) IT NAMES ITS CLAUSE.**

**THE MODEL IS ALREADY IN THE REPOSITORY AND WAS FOLLOWED RATHER THAN INVENTED:**
`src/engine/sizing.py`'s recorded carve-out permits one function to compute
proceeds at a price under three conditions, and
`docs/design/04_2a_artifact_containment.md` §4.2 permits the fixture readers under
four. **Both narrow the permitted use to the shape the verification takes**, which
is what (b) does.

**AND THE FIREWALL'S LIFT DOES NOT MAKE THIS MOOT.** After the freeze an outcome
quantity may lawfully exist; the hazard is not that it exists but that it is seen
without being consumed. **Constraint (b) is what keeps a verification from
becoming a viewing.**

---

## 5. THE DEFAULT LEVEL, AND THE METRIC THAT CANNOT DECOMPOSE

### 5.1 FIVE LEVELS, ONE DEFAULT

**DEFINED:** the run level; the period level over
`docs/design/04_2d_aggregation.md` §3.2's partition — the nine test windows plus
the unassigned row; the symbol level; the direction level; and **exactly one
stratum**, the non-floor-bound stratum
`docs/design/04_1c_consequences_and_thresholds.md` §3.2 commits. **No other
stratum is committed anywhere and this document commits none.**

**A SHAPE NOTE IS RECORDED** because the five are not alike: symbol, direction and
stratum partition the run directly, while the eighteen periods are an overlapping
cover in which a position may appear in up to three rows — which is why only the
settled partition supports the reconstruction identity.

> ### **A METRIC IS DEFINED AT THE RUN LEVEL UNLESS A COMMITTED DECISION REQUIRES
> ### OTHERWISE. A DECOMPOSITION IS REPORTED ALONGSIDE, NEVER INSTEAD.**

**THE GROUND IS `docs/design/04_2d_aggregation.md` §2.1's INVERSION.** A
vocabulary whose default were the period level would put the derived thing first
and reintroduce the combining picture §2.2 forecloses. **"Alongside, never
instead" is the operative half**: parts reported without the whole have nothing to
check them against, which disables §2.3's defect test.

**AND IT DISCHARGES §9(b)'s "EACH SPECIFIED EXACTLY ONCE" GENERICALLY.** §9(b)'s
stated worry is a metric computed at whichever level first looks informative;
under this default no metric's level is open, and any departure is a committed
decision with a commit hash. **One committed decision already departs** —
condition (d)'s pooled evaluation on the non-floor-bound stratum — and it is
unaffected.

### 5.2 WHAT IS REQUIRED OF A METRIC THAT CANNOT DECOMPOSE

**WHICH CLASSES SATISFY THE REQUIREMENT.** A sum decomposes, and a count is its
cleanest case. A mean decomposes **but only with its denominator**, which is the
second reason the denominator must travel. An extremum decomposes.

**WHICH CANNOT.** A **ratio of sums does not decompose as a mean of ratios** —
for `A / B` the run figure is `(sum A) / (sum B)`, which is not any average of the
cells' `A_i / B_i` except by coincidence, and the failure is silent. An **order
statistic** does not decompose at all. Neither does any **path-dependent**
quantity, since a cell is a date-selected subset whose internal sequence is not
the run's.

> ### **A METRIC THAT CANNOT DECOMPOSE IS DEFINED AT THE RUN LEVEL AND ITS
> ### PER-CELL VALUES ARE NOT REPORTED AS A DECOMPOSITION.** They may be reported,
> ### labelled as separate computations over subsets, with the reconstruction
> ### identity explicitly stated as inapplicable and the reason given.

**THE REASON IS THAT §2.3's DEFECT TEST MUST NOT BE ARMED WHERE IT CANNOT FIRE
CORRECTLY.** Presenting non-decomposing parts as a decomposition would make a
correct run look defective — and worse, would train a reader to discount the test
on the occasion it is right. **The label removes the quantity from the test's
domain instead**, because a fifth cause of disagreement would give every real
failure an innocent explanation.

---

## 6. THE DENOMINATOR RULE

### 6.1 THE RULE, IN TWO LIMBS

> ### **EVERY FIGURE IS REPORTED WITH THE DENOMINATOR IT WAS COMPUTED OVER. A
> ### FIGURE WITHOUT ITS DENOMINATOR IS NOT REPORTED.**
>
> ### **AND WHERE THE DENOMINATOR VARIES FOR A REASON UNRELATED TO THE STRATEGY,
> ### THE FIGURE CARRIES A STATEMENT OF WHAT THE VARIATION IS A FUNCTION OF.**

**THE FIRST LIMB EXTENDS `docs/design/04_2d_aggregation.md` §5.3 TO EVERY LEVEL
AND BOTH TIERS** — to the symbol, direction and stratum levels and to diagnostics
— on the two grounds §5.3 gives, **neither of which is a fact about periods.**

**THE SECOND LIMB IS NEW AND IS WHAT §5.5 ACTUALLY DEMANDS.** The denominator's
value does not tell a reader what it is a function of; the statement does — that
the taken count is a function of the budget's spare capacity over the preceding
path, and that a period in which the book ran full is skewed away from high-ATR
entries relative to its own signal supply. **A denominator reported without that
statement invites the inference §5.5 forbids: reading a stable count as a stable
opportunity set.**

**IT IS A PROPERTY OF THE FIGURE, NOT OF THE REPORT**, so it travels wherever the
figure travels — following
`docs/design/04_0_divergence_disposition_amendment_1.md` §3's treatment of a
figure quoted in passing.

### 6.2 THE TWO TRAVELLING QUESTIONS, DISCHARGED

**MAY A QUANTITY BE DENOMINATED IN TRADE COUNT AT ALL? YES, UNDER DISCLOSURE
RATHER THAN BY BEING HARMLESS.** The prohibition case was put at full strength —
counts of **976 to 1,025** against widely varying supply, so the denominator
carries no information about the period. **It fails because the alternatives do not
escape**: total risk deployed is the count times a constant under Rule B's nominal
charging; time in market is shaped by the budget in a direction §5.4 names; and
calendar time answers a different question. **There is no neutral denominator to
prefer, and prohibiting the count would displace the problem into one whose
dependence is less obvious.** §5.5's own instruction is a constraint on inference,
not on arithmetic.

**DO COUNT- AND TIME-DENOMINATED FIGURES ANSWER THE SAME QUESTION? NO, AND
NEITHER ESCAPES THE BUDGET.** Three shapes are distinguished — per taken position,
per unit of exposure, per unit of calendar — and only the third is not a budget
artefact. **No shape is preferred; the choice for any metric belongs to the
decision that consumes it.** What is committed is that the three are different
quantities, that a metric names which it uses, and that a figure in one is never
compared with a figure in another.

### 6.3 WHAT PATH DEPENDENCE PERMITS AND FORBIDS

**PERMITTED:** a per-trade figure may be defined, computed and reported. **Path
dependence makes the denominator uninformative about opportunity; it does not make
the numerator wrong.**

**FORBIDDEN, three definitions:**

1. **No metric defined as a function of the taken count's relation to the
   candidate count** — a take rate, a skip rate, a capture fraction. That
   describes the budget's capacity and its variation would be read as the
   strategy's. **The counts themselves are reportable; the ratio as a metric is
   not.**
2. **No metric whose definition presumes the population is fixed**, and none
   defined relative to a population size established on the candidate population.
   §5.6 records the concrete instance: report 21's adequacy thresholds "were
   established on the uncapped population and do not describe what is traded."
3. **No metric defined over a counterfactual population** — what would have been
   taken under a different budget or order. That population does not exist and its
   figures would be model output presented as measurement.

**AND ONE THING NOT FORBIDDEN, STATED SO THE OMISSION IS NOT READ AS AN
OVERSIGHT:** comparing figures at different levels of the same run is governed by
`docs/design/04_2d_aggregation.md` §6 and is untouched. This constrains what a
metric may be, not what a comparison supports.

---

## 7. §5.7's DISCHARGE PER §8.2's SPLIT

**§8.2 ASSIGNED THE WHOLE SUBSTANCE HERE** — "THE SUBSTANCE — WHICH OPERATOR — IS
WHOLLY 4.3's, AND IS HANDED ON UNDECIDED" — together with a second separable
piece it named as a definition rather than an aggregation rule: which of
`nominal_risk_usd` and `realised_risk_usd` sits in a per-trade R's denominator.
**Both are discharged.**

### 7.1 THE UNIT

> ### **A PER-TRADE R IS DENOMINATED IN `realised_risk_usd` — THAT TRADE'S OWN
> ### REALISED RISK.**

**THE GROUND IS REPORT 28 §7's, WHICH §8.2 ALREADY VERIFIED**: it is "the true
1.0R denominator **for that trade**", and it is what makes a stop return exactly
-1.0R in that trade's own unit.

**THE ALTERNATIVE IS NOT A UNIT AT ALL.** `nominal_risk_usd` is a constant by
`docs/design/05a_aggregate_risk_budget_amendment_1.md` Rule B, which commits that
the budget is charged the nominal allocation and that flooring is not reflected in
it. **A per-trade quantity divided by a constant is the dollar quantity rescaled,
not a normalised one**, and a stop would return -1.0R only where the flooring drag
happened to be zero.

**THE DUAL RECORDING IS UNTOUCHED.** Both fields remain stored and neither is
derived from the other at read time; what is committed is which denominates an R.

### 7.2 THE OPERATOR

> ### **AN AGGREGATE OVER R-DENOMINATED PER-TRADE QUANTITIES IS EQUAL-WEIGHTED.**

**FIRST, AND IT IS ARITHMETIC RATHER THAN JUDGEMENT — SIZE-WEIGHTING BY THE
NOMINAL FIGURE IS NOT A DISTINCT OPERATOR.** Rule B charges every taken position
the same nominal allocation, so weights proportional to it are all equal and the
operator **is** equal weighting. **The apparent two-way choice has only one
non-degenerate alternative.**

**SECOND — WEIGHTING BY REALISED RISK UNDOES THE DENOMINATION §7.1 COMMITS.** If
each trade's R is its outcome divided by its own realised risk, weighting by that
same realised risk multiplies the divisor back in. **The result is a
dollar-denominated aggregate wearing an R's name.**

**THIRD — THE WEDGE IS A VENUE ARTEFACT.** §5.7 gives its size as flooring drag of
**0.80%**, which is `qty_step` granularity: a function of which symbol traded and
at what price, with report 28 §10 recording SOLUSDT's tick changing inside the
window. **A weight proportional to it would make the aggregate depend on lot
geometry.**

### 7.3 §8.2's PREMISE IS ANSWERED, NOT DENIED

**§8.2 HELD THAT THE CHOICE "CANNOT BE SETTLED WITHOUT NAMING THE QUANTITY, AND
NAMING IT IS THE LINE." THAT IS CORRECT AS STATED AND IS NOT CONTRADICTED.**

> ### **WHAT IS SETTLED IS THE OPERATOR FOR A SHAPE, AND THE SHAPE CARRIES ENOUGH
> ### MEANING TO SETTLE IT, BECAUSE THE DENOMINATION IS ITSELF THE STATEMENT OF
> ### WHAT THE QUANTITY MEANS.**

A quantity denominated in its own trade's risk unit has already answered §8.2's
question — whether a contribution should scale with the capital at risk on it. **It
should not; that is what the denomination did.**

**NOT REACHED, AND ROUTED:** an aggregate over a quantity that is **not**
R-denominated — a count, a duration, a rate — and a dollar-denominated aggregate
under its own name. **Both are amendments under §9.3.** §8.2's three constraints
are satisfied: same operator at every level, run-level figure computed directly,
denominator travels.

---

## 8. THE GEOMETRY DECISION, AND WHAT SURVIVES R-NORMALISATION

### 8.1 WHAT NORMALISATION REMOVES

**THE PAYOFF SCALE, COMPLETELY.** Under §7.1 a stop returns exactly -1.0R and the
frozen reward-to-risk puts the target at a fixed multiple of the same unit, **for
every position at every width.**

> ### **SO THE HETEROGENEITY IN SIZE OF OUTCOME IS NOT A RESIDUE. IT IS REMOVED BY
> ### CONSTRUCTION, AND ANY ARGUMENT FOR STRATIFICATION RESTING ON IT IS ANSWERED
> ### BEFORE IT STARTS.**

### 8.2 WHAT SURVIVES — TWO THINGS, BOTH STRUCTURAL

1. **THE RELATION BETWEEN THE GEOMETRY AND THE FIXED CLOCK.** R-denomination
   rescales the price axis and leaves the time axis alone. Two positions with
   identical R geometry and stop widths differing by a factor of fifty face the
   same 17-to-24-hour window to traverse distances differing by that factor.
   **This is a fact about the specification — an unbounded width rule combined
   with a calendar time exit — not an assertion about what wide-stop positions
   do.**
2. **THE COST SHARE OF THE RISK UNIT.** The derived floor is `n_cost` times the
   round-trip cost, so at a floor-bound stop the cost terms are a fixed and
   substantial fraction of the risk unit by construction and at a
   forty-nine-per-cent stop a small one. **The risk unit's composition varies with
   width** — which is the predicate
   `docs/design/04_1c_consequences_and_thresholds.md` §3.2 already stratifies
   condition (d) on.

### 8.3 THE DECISION

> ### **NO METRIC IS STRATIFIED BY STOP WIDTH BY DEFAULT. THE DISTRIBUTION OF STOP
> ### WIDTH IS REPORTED ALONGSIDE EVERY RUN-LEVEL AND PER-CELL FIGURE COMPUTED
> ### OVER POSITIONS, AS A DIAGNOSTIC UNDER §3.**

**THE CASE FOR MANDATORY STRATIFICATION WAS PUT FIRST AND FAILS ON THREE GROUNDS,
THE FIRST DECISIVE.** Requiring a metric to be reported per band means its
condition is evaluated per band, **which is a decision-tier commitment this
document may not make** — and would pre-empt every such decision 4.4 has not yet
taken, without knowing a single condition. Second, §8.1 answers the strongest
ground. Third, a stratification already exists where a committed decision needed
one, which is evidence the case-by-case route works.

**WHY THE DISTRIBUTION IS REPORTED RATHER THAN NOTHING DONE.** A stop width is a
function of entry price and ATR at signal time, **computable before any exit
resolves and not an outcome quantity in any regime**, so reporting it neither
spends nor depends on the lift. **And it names its clause**: it verifies
`docs/design/04_1g_cap_adoption.md` §0 — that the run executed with no upper bound
— and it is what makes §6 of that document's falsifier readable. A refusal for
quantity happens when the risk unit divided by a wide stop falls below the venue
minimum, **so the width distribution is what says whether a small refusal count
means the rule is safe or that no wide stop arose.**

**HANDED TO 4.4:** whether any particular condition must be evaluated per width
band, with §8.2's two residues as its material.

**AND NO POSITION IS TAKEN ON WHETHER WIDE-STOP POSITIONS BEHAVE DIFFERENTLY.**
That is an outcome quantity and it does not exist. **The answer given is that a
metric's reporting must acknowledge the heterogeneity while its definition need
not.**

---

## 9. §5.4's DISPOSITION

> ### **ONE NARROW PART IS VOCABULARY AND IS TAKEN. THE REST IS 4.4's AND IS LEFT
> ### THERE.**

**TAKEN:** §5.4 establishes that a time-in-market denominator is a budget
artefact, which **settles the second question `docs/design/04_2d_aggregation.md`
§5.4 handed here.**

**WHY IT IS THIS DOCUMENT'S.** §6.2 above had to say whether a count-denominated
and a time-denominated figure answer the same question, and the honest answer
depends on whether the time denominator escapes the capacity problem. **Without
§5.4 a step could reasonably have concluded that denominating in exposure time
sidesteps §5.5's warning.** It does not: exits free budget at settlement instants,
those are exactly the entry hours drawing 24-hour holds, so the taken population
is enriched in long holds by the budget's own release schedule. **§6.2's
commitment rests on that, and the disclosure obligation reaches a time denominator
for the same reason it reaches a count.**

**LEFT WITH 4.4:** the stratify-or-state choice, which is the same species as the
geometry decision and fails the same first test; and the effect's size, unmeasured
per §5.4's own record.

**NO HOLD-DURATION STRATUM IS COMMITTED.** §4.1's enumeration of levels is closed
and hold duration is not in it; one is available to 4.4 through the amendment
route.

---

## 10. WHAT 4.4 INHERITS

**TEN COMMITTED ITEMS**, listed at §9.1 of the document: the two tiers and the
checkable property; the default not to compute; the diagnostic bound; the
outcome-quantity constraint; the five levels and the run-level default; the
reconstruction requirement with its classes; the two-limb denominator rule; the
three forbidden path-dependence definitions; the unit and the operator; and the
geometry disposition.

**FOUR OPEN:** the decision tier's membership, including which of the seven
quantities §9(b) enumerates are admitted; whether any condition is evaluated per
width band; whether to stratify on hold duration or state the confound; and the
denominator shape for any given metric.

### 10.1 THE AMENDMENT ROUTE

> ### **4.4 MAY REQUIRE A QUANTITY THIS DOCUMENT DOES NOT DEFINE. DOING SO IS AN
> ### AMENDMENT TO IT, WITH ITS OWN COMMIT, MADE BEFORE THE QUANTITY IS
> ### COMPUTED.**

**IT IS PREFERABLE TO BOTH ALTERNATIVES, AND BOTH ARE NAMED SO THEY CAN BE
RECOGNISED.**

**BENDING A CONDITION TO FIT AN AVAILABLE QUANTITY** produces a condition whose
content was chosen by the vocabulary rather than by the thesis, **and the bend is
invisible afterwards** because the committed condition reads as though it had
always been about that quantity.

**DEFINING ONE SILENTLY IN 4.4's OWN TEXT** produces two definitions of the
vocabulary in two documents — the drift `src/firewall.py`'s consolidation was
created to end: eighteen copies of one list, four of them three names behind,
every test passing.

**THE ORDER REQUIREMENT IS THE OPERATIVE HALF**, resting on the same ground as the
promotion rule.

---

## 11. THE LEDGER

**THE TOTAL, READ:** `docs/design/04_2e_housekeeping.md` §7.3 states **52**.

> ### **THIS DOCUMENT ADDS NO INSTANCE. THE TOTAL IS UNCHANGED AT 52**, contiguous
> ### from (1) to (52).

**THE ARITHMETIC IS THEREFORE 52, WITH NO ADDITION.**

**ONE CANDIDATE WAS CONSIDERED AND IS NOT LOGGED**, with the reason given at
§10.1 of the document so the call can be checked: the routing divergence at §1.4
resembles instances (50) to (52) but **makes no false claim about any document** —
it issues a direction the register does not yet reflect, which a project owner may
do and which `docs/design/04_2b_point_4_decomposition.md` §5.1 has precedent for
recording as the owner's direction. **And `docs/design/04_1a_denomination.md` §6's
criterion is not met**: recording both and routing explicitly degrades no
otherwise correct artifact.

---

## 12. THE TWO STANDING CLOSING ITEMS

### 12.1 WHERE A REQUIREMENT CONTRADICTED A CONSTRAINT

**ONE, STATED AND NOT RESOLVED.**

**`docs/design/04_2b_point_4_decomposition.md` §3.3 ASSIGNS §9(b) TO 4.3** and
requires of 4.3 "each of the seven quantities §9(b) enumerates, specified as per
symbol, per fold, or pooled — and each specified exactly once."
**THE COMMISSIONING INSTRUCTION ASSIGNS THE COMPLETION OF MEMBERSHIP TO 4.4** and
separately forbids this document from closing it.

> ### **THE REGISTER SAYS 4.3. THE DIRECTION SAYS 4.4. THE DOCUMENT RECORDS BOTH
> ### AT §1.4 AND CHOOSES NEITHER**, because the deliverable is owed either way
> ### and is not discharged here.

**WHAT IS DISCHARGED IS MORE OF §9(b) THAN IT LOOKS**, and this is recorded so a
later reader does not treat §9(b) as wholly outstanding: its operative
requirement is that each metric be specified at exactly one level, and §4.2's
default satisfies that **generically**, for every metric that is ever admitted.
**What remains is membership.**

**THE REGISTER UPDATE IS NAMED AS AN OPEN ITEM** at §10.2 of the document, with no
owner.

### 12.2 ANYTHING READABLE AS NARROWER OR BROADER THAN INTENDED

**§2.2's DEFAULT COULD BE READ AS BANNING EXPLORATORY WORK GENERALLY.** It does
not reach anything outside the run's own output; it governs which quantities the
run produces.

**§3.5's PERMISSION COULD BE READ AS ADMITTING OUTCOME QUANTITIES TO THE
DIAGNOSTIC TIER BROADLY.** Constraint (b) is the narrow one and is the whole of
the permission's content: **a count of violations or a maximum absolute deviation,
never the distribution.**

**§6.3's OPERATOR IS COMMITTED FOR A SHAPE, NOT FOR A LIST.** A later document
admitting a metric outside the R-denominated per-trade shape does not reopen it;
that metric needs an operator of its own.

**§7.4's "REPORTED ALONGSIDE EVERY RUN-LEVEL AND PER-CELL FIGURE COMPUTED OVER
POSITIONS" IS DELIBERATELY SCOPED TO FIGURES OVER POSITIONS.** It does not attach
to a diagnostic that is not computed over positions, and it should not be read as
a universal reporting obligation.

**AND §4.1's LEVEL ENUMERATION IS CLOSED, WHICH IS THE BROADEST-LOOKING CLAUSE IN
THE DOCUMENT AND IS THE NARROWEST.** Five levels and one stratum. **Anything else
— a hold-duration band, a width band, a volatility regime — is an amendment**, and
§8 and §9 above each name a candidate that would need one.

---

**Nothing was computed. No code was changed. Suite unchanged at 1394 passing.**
