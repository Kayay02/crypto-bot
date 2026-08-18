# THE METRIC VOCABULARY, THE LEVELS, AND THE TWO-TIER ADMISSIBILITY POLICY

**Point 4, sub-point 4.3, first part.** Definitions, levels, denominators and
admissibility. **Nothing is computed and no membership is closed.**

## 0. THREE SCOPE NOTES

### 0.1 NO BANNED NAME APPEARS IN THIS DOCUMENT

**Following `docs/design/04_2a_artifact_containment.md` §0.1.**
`docs/handoff/31_point_5_closing.md` §9(b) enumerates seven quantities by name and
six of the seven are on the enforced list. **They are referred to throughout as
"the seven quantities §9(b) enumerates" and are never written out.** Where an
item's committed identifier contains a banned token — the placeholder pair at
`docs/design/04_2b_point_4_decomposition.md` §5.3 — it is referred to by citation.

### 0.2 NOTHING IS COMPUTED AND NO ARTIFACT WAS OPENED

**No figure is produced here.** Every number below is quoted from a committed
document and is cited to it. **No file named at
`docs/design/04_2a_artifact_containment.md` §3.1, as amended at
`docs/design/04_2e_housekeeping.md` §2.2, was opened.**

### 0.3 WHAT IT RELIES ON AND DOES NOT REARGUE

**`docs/design/04_2c_run_structure.md`'s committed structure** — one continuous
run over the whole in-sample window, the budget carried across every fold
boundary, positions assigned to a period by entry-bar close, and the evaluation
population as a rule.

**`docs/design/04_2d_aggregation.md`'s committed aggregation and comparison
rules** — the inversion at §2.1, the prohibition on weighting schemes across
periods at §2.2, the defect test at §2.3, the partition at §3.2, and what a
comparison supports at §6.

**Neither is reargued.** Where this document appears to restate one it is because
a rule here is a consequence of it, and the consequence is marked as such.

---

## 1. WHAT THIS DOCUMENT IS

**A PRE-REGISTRATION, FROZEN ON COMMIT**, joining the frozen specification per
`docs/design/04_0_divergence_disposition_amendment_2.md` §2's open-forward clause.
**Committed alone with the manifest and this step's report-back.**

### 1.1 THE SCOPE, STATED PRECISELY

**IT COMMITS FOUR THINGS:**

1. **WHAT A METRIC IS** — the two-tier policy at §3, and the checkable property
   that distinguishes the tiers.
2. **AT WHAT LEVEL A METRIC IS COMPUTED** — §4, with the run level as the
   default and the reconstruction requirement stated.
3. **HOW A DENOMINATOR IS HANDLED** — §5, discharging the metric half of
   `docs/handoff/31_point_5_closing.md` §5.5 and the two questions
   `docs/design/04_2d_aggregation.md` §5.4 hands here.
4. **THE ADMISSIBILITY POLICY** — the default at §2.2, and the promotion route
   at §3.4.

**IT ALSO DISCHARGES §5.7's SUBSTANCE** (§6) and **DISPOSES OF THE GEOMETRY
HETEROGENEITY** `docs/design/04_1g_cap_adoption.md` created (§7).

### 1.2 WHAT IT DOES NOT DO

> ### **IT DOES NOT CLOSE THE DECISION TIER'S MEMBERSHIP.**

**IT SETS NO THRESHOLD.** A threshold is a kill condition's, and every kill
condition is 4.4's. `docs/design/04_1c_consequences_and_thresholds.md` §3.5
records the same separation for condition (d): the level was that document's, the
threshold was not.

**IT COMMITS NO KILL CONDITION AND NO GATE.**

**IT NAMES NO METRIC.** The drafting test is
`docs/design/04_2d_aggregation.md` §1.2's, applied one level up: **if a rule here
cannot be made concrete without naming a specific quantity, the line is being
crossed, and the remedy is to name the shape.** A rule about denominators binds
on every quantity that has one, which is strictly more than a rule about any named
quantity would bind on.

### 1.3 WHY MEMBERSHIP IS LEFT OPEN

> ### **A METRIC SET FIXED BEFORE THE CONDITIONS THAT CONSUME IT IS FIXED EITHER
> ### TOO WIDE OR TOO NARROW. A CONDITION WRITTEN BEFORE THE VOCABULARY EXISTS
> ### REFERS TO UNDEFINED QUANTITIES. THE VOCABULARY COMES FIRST; THE MEMBERSHIP
> ### FOLLOWS THE CONSUMERS.**

**TOO WIDE IS THE DANGEROUS DIRECTION AND IS WHY THE ORDER IS THIS WAY ROUND.** A
set fixed too narrow is discovered immediately — a condition is written and the
quantity it needs is absent, which is loud and is repaired by §9.3's amendment
route. **A set fixed too wide is never discovered**, because every surplus
quantity is computed, reported, read, and consumed by nobody — which is precisely
the hazard §2 exists to control.

**AND THE ASYMMETRY IS THE ARGUMENT.** Under the other order — membership first,
conditions second — a condition that wanted a quantity outside the set would face
a standing temptation to bend itself to what was available. **Under this order the
condition states what it needs and the vocabulary is amended to supply it, which
is a commit rather than a compromise.**

### 1.4 A ROUTING DIVERGENCE, RECORDED AND NOT RESOLVED

**`docs/design/04_2b_point_4_decomposition.md` §3.3 ASSIGNS §9(b) TO 4.3**, and
requires of 4.3 "each of the seven quantities §9(b) enumerates, specified as per
symbol, per fold, or pooled — and each specified exactly once."

**THE INSTRUCTION COMMISSIONING THIS DOCUMENT ASSIGNS THE COMPLETION OF THE
DECISION TIER'S MEMBERSHIP TO 4.4.** That is a re-routing of a committed
register, and it is recorded here as such rather than adopted silently or treated
as an error.

> ### **THE REGISTER SAYS 4.3. THE DIRECTION SAYS 4.4. THIS DOCUMENT DOES NOT
> ### CHOOSE, AND IT DOES NOT NEED TO** — the deliverable is owed either way and
> ### is not discharged here.

**WHAT IS DISCHARGED, AND IT IS MORE OF §9(b) THAN IT LOOKS.** §9(b)'s operative
requirement is that **each metric be specified at exactly one level**, on the
stated ground that "a metric whose level is left open is a metric that will be
computed at whichever level first looks informative." **§4.2 below satisfies that
requirement generically**: every metric is at the run level unless a committed
decision requires otherwise, so no metric's level can be left open and none can be
chosen after the fact. **What remains of §9(b) is which quantities are admitted at
all**, which is membership.

**THE REGISTER SHOULD BE UPDATED BY WHOEVER SETTLES THE ROUTING.** It is recorded
at §10.2 as an open item.

---

## 2. THE HAZARD THIS DOCUMENT EXISTS TO CONTROL

### 2.1 STATED PLAINLY, AND FIRST

**THE FIREWALL HAS HELD BECAUSE NO OUTCOME QUANTITY EXISTS.**
`docs/handoff/31_point_5_closing.md` §11 states it in those terms, and every
document in this chain has been able to rely on it.

**IT LIFTS AT THE FREEZE.** From that moment every computed figure is visible to
whoever reads the run.

> ### **A FIGURE THAT NO COMMITTED DECISION CONSUMES IS A FIGURE SOMEONE FORMS AN
> ### IMPRESSION FROM.**

**AND AN IMPRESSION IS THE ONE CHANNEL NO AUDIT CLOSES.**
`docs/handoff/41_point_4_2_artifact_audit.md` §5 records it in its own words:

> "**CODE TRACING CANNOT ESTABLISH WHETHER A PERSON OPENED AN ARTIFACT AND LET
> WHAT THEY SAW INFORM A JUDGEMENT.** ... **THE RESIDUAL THIS AUDIT CANNOT
> CLOSE**: whether a person read [an artifact] at some point and carried an
> impression forward into a judgement that no document records. **Nothing in the
> repository can settle that.**"

**THAT RESIDUAL WAS TOLERABLE WHILE THE ARTIFACTS BELONGED TO A SUPERSEDED
THESIS.** After the freeze the figures belong to **this** thesis, and the same
unclosable channel runs from them to every judgement 4.4 through 4.7 make.

> ### **THE DEFENCE CANNOT BE AN AUDIT, BECAUSE THE AUDIT IS THE THING THAT DOES
> ### NOT REACH. IT HAS TO BE THAT THE FIGURE WAS NEVER PRODUCED.**

### 2.2 THE CONSEQUENCE: THE DEFAULT IS NOT TO COMPUTE

> ### **A QUANTITY IS COMPUTED IF AND ONLY IF EITHER (i) A COMMITTED DECISION
> ### CONSUMES IT AS AN INPUT, OR (ii) IT VERIFIES THAT THE RUN EXECUTED AS
> ### SPECIFIED. ANYTHING ELSE IS NOT COMPUTED.**

**THE BURDEN IS ON THE QUANTITY.** It is not on anyone to argue a quantity out;
it is on the quantity to name the decision that consumes it or the clause it
verifies. **A quantity that can name neither is not admitted, and "it might be
interesting" is not a naming.**

**THIS IS THE SAME SHAPE AS THE READ PROHIBITION AND IS ADOPTED FOR THE SAME
REASON.** `docs/design/04_2a_artifact_containment.md` §3.2 refuses a read *for
any purpose, including verification*, because the confirming read and the
offending read are the same read. **Here: the exploratory computation and the
committed computation produce the same visible number.**

**AND IT IS NOT A COUNSEL OF CAUTION.** A default that says "compute little"
would be advice. **This one is a rule with a checkable predicate**: for every
figure a run produces, a reader can ask which committed decision consumes it or
which clause it verifies, and the answer is in a document or the figure should not
be there.

### 2.3 THIS IS THE FIRST DOCUMENT IN THE CHAIN TO FACE THIS

**UNTIL THE FREEZE THERE WAS NOTHING TO LOOK AT.** Every prior document in Point 4
and Point 5 operated in a regime where the hazard was structurally absent: the
firewall's guarantee was that the figures did not exist, so no discipline about
which of them to produce was required, and none was written.

> ### **THAT IS WHY NO COMMITTED DOCUMENT STATES A COMPUTE-BY-DEFAULT RULE TO
> ### AMEND. §2.2 IS NEW, AND IT IS NEW BECAUSE THE CONDITION IT ADDRESSES IS
> ### NEW.**

**THE NEAREST PRECEDENT IS NOT A PRECEDENT AND IS NAMED SO.**
`docs/design/04_2d_aggregation.md` §7.4 declines to commit the refusal count and
routes it to 4.6's gate, which is a decision about **one** quantity taken on the
merits. **It is not a general rule and does not purport to be.**

---

## 3. THE TWO TIERS

### 3.1 THE DEFINITIONS

> ### **A DECISION METRIC IS A QUANTITY THAT A COMMITTED KILL CONDITION,
> ### THRESHOLD OR GATE CONSUMES AS AN INPUT.**

**ITS MEMBERSHIP IS NOT CLOSED HERE.** §1.2 and §1.4.

> ### **A DIAGNOSTIC METRIC IS A QUANTITY THAT VERIFIES THE RUN EXECUTED AS
> ### SPECIFIED.**

**WITHOUT LIMITATION**, per
`docs/design/04_0_divergence_disposition_amendment_2.md` §7's drafting rule: that
costs were charged as the cost model says; that the seal was not touched; that the
budget behaved as `docs/design/05_aggregate_risk_budget.md` and its two amendments
govern; that counts reconcile across the partition.

**THE TWO TIERS ARE EXHAUSTIVE OF WHAT IS COMPUTED**, by §2.2: a quantity that is
in neither tier is a quantity that is not produced.

### 3.2 THE MECHANICAL PROPERTY, WHICH IS THE POINT OF THE SECTION

**"INADMISSIBLE FOR EVALUATING THE THESIS" IS A RULE ABOUT INTENT, AND INTENT IS
NOT CHECKABLE.** A reader cannot verify what a figure was meant for, and a step
that used one for something else would leave no trace in the form of the rule.

> ### **THE CHECKABLE FORM: A DIAGNOSTIC METRIC APPEARS AS AN INPUT TO NO KILL
> ### CONDITION, NO THRESHOLD AND NO GATE OUTCOME, AND NO COMMITTED DECISION
> ### REFERENCES ONE.**

**SO WHETHER A FIGURE IS DIAGNOSTIC IS A FACT ABOUT THE DECISION GRAPH RATHER
THAN ABOUT WHAT ANYONE MEANT.** The graph is written down: the conditions are in
4.4, the gate is in 4.6, and each names its inputs. **A reader checks the tier by
reading the inputs, not by reading an intention.**

**AND THE PROPERTY IS DIRECTIONAL, WHICH MATTERS.** It is stated as a constraint
on the **decision** side — no condition may reference a diagnostic — rather than
as a constraint on the diagnostic's own definition. **A rule written the other way
round would be satisfiable by relabelling**, since nothing stops a step calling a
quantity diagnostic while a condition quietly consumes it. **Written this way, the
condition is the thing that would have to change.**

### 3.3 THE BOUNDING RULE FOR THE DIAGNOSTIC TIER

**WITHOUT A BOUND THE DIAGNOSTIC TIER SWALLOWS §2.2.** Any quantity can be
described as verifying something, and a tier admitted on a description is a tier
with no edge.

> ### **EACH DIAGNOSTIC METRIC NAMES THE SPECIFICATION CLAUSE IT CHECKS, BY
> ### DOCUMENT AND SECTION. A DIAGNOSTIC THAT CHECKS NOTHING COMMITTED IS NOT A
> ### DIAGNOSTIC.**

**THE CITATION IS THE BOUND.** It is not a formality: a clause is a statement that
can be false, so naming one commits the diagnostic to a falsifiable claim about
the run. **A quantity that cannot name a clause is a quantity nobody can say what
would count as passing.**

**THE TIER IS THEREFORE BOUNDED BY THE SPECIFICATION'S OWN SIZE**, which is
finite, committed and readable — rather than by anyone's judgement about
usefulness.

### 3.4 PROMOTION, AND WHAT AN UNPROMOTED DIAGNOSTIC COSTS

**A DIAGNOSTIC FIGURE MAY TURN OUT TO BE NEEDED AS A GATE'S INPUT.** That is not
forbidden and it is not unexpected.

> ### **IT IS PROMOTED TO THE DECISION TIER BY AN AMENDMENT WITH ITS OWN COMMIT,
> ### MADE BEFORE THE FIGURE IS INSPECTED.**

**IT IS NOT RECLASSIFIED IN THE MOMENT.**

> ### **A DECISION RESTING ON AN UNPROMOTED DIAGNOSTIC IS A CONTAMINATION EVENT.**

**WHY THE ORDER IS THE WHOLE OF IT.** Promotion after inspection is
indistinguishable, from the outside and often from the inside, from choosing the
input because of what it turned out to say. `docs/design/04_0_decision_rule.md`
§4 states the general form: **the guard is ORDER, not a threshold, and the commit
hash is the evidence, and it is evidence that survives everyone's account of what
they were thinking.**

**AND THE COST OF THE RULE IS SMALL AND THE COST OF ITS ABSENCE IS TOTAL.** A
promotion commit is minutes. A decision resting on a figure promoted after it was
seen cannot be repaired by anything, because the population it was chosen against
has already been seen.

### 3.5 WHETHER A DIAGNOSTIC METRIC MAY BE AN OUTCOME QUANTITY

**THE QUESTION IS REAL AND CANNOT BE AVOIDED.** Some of what §3.1 lists as
diagnostic touches quantities the firewall names: **verifying that costs were
charged as the model says means checking an identity whose terms are
outcome-denominated.** Report 28 §7's identity — that a stop returns exactly
-1.0R in that trade's own realised risk unit — is the paradigm case, and it is
already relied on by `docs/design/04_2d_aggregation.md` §8.2.

> ### **YES, AND UNDER FOUR CONSTRAINTS, ALL FOUR CHECKABLE.**

**(a) THE CLAUSE IT VERIFIES IS ITSELF ABOUT AN OUTCOME QUANTITY.** A diagnostic
does not acquire a licence to touch outcome quantities merely by being a
diagnostic; it acquires one where the specification clause it checks is stated in
outcome terms and cannot be checked otherwise.

**(b) IT IS REPORTED AS A VERIFICATION STATISTIC, NOT AS THE QUANTITY'S OWN
DISTRIBUTION.** The admissible forms are **a count of violations** and **a maximum
absolute deviation from the identity**. **The inadmissible form is the outcome's
distribution, mean, or any figure from which one could be reconstructed.**

> ### **A RESIDUAL AGAINST AN IDENTITY IS NOT THE QUANTITY THE IDENTITY IS
> ### ABOUT.** `|realised R + 1.0|` over a stop-exited position tells a reader
> ### whether the arithmetic holds and tells them nothing whatever about how the
> ### strategy performed.

**(c) THE §3.2 PROPERTY HOLDS UNCONDITIONALLY.** It appears as an input to no
condition, threshold or gate, and no committed decision references it. **This is
not relaxed for outcome-bearing diagnostics; it is where the relaxation would do
the damage.**

**(d) IT NAMES ITS CLAUSE, PER §3.3.**

**THE MODEL IS ALREADY IN THE REPOSITORY AND IS FOLLOWED RATHER THAN INVENTED.**
`src/engine/sizing.py`'s recorded carve-out permits one function to compute
proceeds at a price **only under three conditions, all asserted by test**, and
`docs/design/04_2a_artifact_containment.md` §4.2 permits the fixture readers
**only under four**. **Both work by narrowing the permitted use to the shape the
verification takes, which is what (b) does here.**

**AND THE FIREWALL'S LIFT DOES NOT MAKE THIS MOOT.** After the freeze an outcome
quantity may lawfully exist; §2.1's hazard is not that it exists but that it is
**seen without being consumed**. **Constraint (b) is what keeps a verification
from becoming a viewing.**

---

## 4. THE LEVEL

### 4.1 THE LEVELS A QUANTITY MAY BE COMPUTED AT

**THE RUN LEVEL.** The quantity computed over every position of the one continuous
run `docs/design/04_2c_run_structure.md` §2.6 commits. **It means: what the
strategy did over the in-sample window, under one budget path, with nothing
partitioned.**

**THE PERIOD LEVEL.** The quantity computed over the subset of the run's positions
whose entry-bar close falls in one cell of `docs/design/04_2d_aggregation.md`
§3.2's partition — **the nine test windows plus the unassigned row.** It means
exactly what `docs/design/04_2c_run_structure.md` §5.2 says and no more: a
quantity over a date-selected subset, **under a budget whose state at the period's
opening was inherited and was not reset.**

**THE SYMBOL LEVEL.** The quantity computed over the run's positions in one
symbol. **It means: what the strategy did on that instrument**, and it is a
partition of the run — every position has exactly one symbol.

**THE DIRECTION LEVEL.** Likewise for long and short. **Also a partition** — thesis
4.1 skips two-sided bars, so every position has exactly one direction.

**THE STRATUM LEVEL, AND EXACTLY ONE STRATUM IS COMMITTED.**
`docs/design/04_1c_consequences_and_thresholds.md` §3.2 commits **the
non-floor-bound stratum under the committed per-symbol, per-direction floor** —
the predicate being whether the cost floor, rather than the volatility, set the
stop. **It is a partition of the run into two parts, and only the non-floor-bound
part is named by that document.**

> ### **NO OTHER STRATUM IS COMMITTED ANYWHERE, AND THIS DOCUMENT COMMITS NONE.**
> ### A stratum introduced later is an amendment, per §9.3.

**A NOTE ON SHAPE, BECAUSE THE FIVE ARE NOT ALIKE.** Symbol, direction and stratum
partition the run directly. **The period level does not partition it in the same
sense** — `docs/design/04_2c_run_structure.md` §5.1 records that the eighteen
periods are an overlapping cover and a position may appear in up to three period
rows, which is why §3.2 settles the partition on the nine **test** windows plus
the unassigned row rather than on the periods at large. **Only that settled
partition supports §2.2's identity.**

### 4.2 THE DEFAULT

> ### **A METRIC IS DEFINED AT THE RUN LEVEL UNLESS A COMMITTED DECISION REQUIRES
> ### OTHERWISE. A DECOMPOSITION IS REPORTED ALONGSIDE, NEVER INSTEAD.**

**THE GROUND IS `docs/design/04_2d_aggregation.md` §2.1's INVERSION, AND THE
DEFAULT IS ITS DIRECT CONSEQUENCE.** The run-level quantity is primary and a
per-period figure is a decomposition of it. **A vocabulary whose default were the
period level would put the derived thing first and would reintroduce, through the
back door, the combining picture §2.2 forecloses.**

**"ALONGSIDE, NEVER INSTEAD" IS THE OPERATIVE HALF.** A decomposition reported
instead of the whole is a set of parts with nothing to check them against, which
disables §2.3's defect test — the same failure
`docs/design/04_2d_aggregation.md` §3.3 records for suppressing the unassigned
row.

**AND THE DEFAULT SATISFIES §9(b)'s "EACH SPECIFIED EXACTLY ONCE" GENERICALLY.**
§9(b)'s stated worry is that "a metric whose level is left open is a metric that
will be computed at whichever level first looks informative." **Under this default
no metric's level is open**: it is the run level, and any departure is a committed
decision with a commit hash, which is the order guarantee §3.4 relies on.

**ONE COMMITTED DECISION ALREADY DEPARTS, AND IT IS UNAFFECTED.**
`docs/design/04_1c_consequences_and_thresholds.md` §3.3 evaluates condition (d)
pooled over the whole window on the non-floor-bound stratum, with the per-fold
decomposition reported as a stability probe and not aggregated. **That is a
committed decision requiring a stratum, and it is exactly the "unless" clause
above.** This document does not disturb it.

### 4.3 THE RECONSTRUCTION REQUIREMENT

> ### **A DECOMPOSITION MUST RECONSTRUCT THE RUN-LEVEL FIGURE. A DISAGREEMENT IS A
> ### DEFECT, NOT A MODELLING CHOICE.**

**THAT IS `docs/design/04_2d_aggregation.md` §2.3, restated here because it binds
on a metric's definition and not only on a report's arithmetic.**

**WHICH CLASSES SATISFY IT.**

**A SUM DECOMPOSES.** A total over the run equals the sum of the cell totals,
exactly, over an exhaustive disjoint partition. **A count is the special case and
is the cleanest of all.**

**A MEAN DECOMPOSES, BUT ONLY WITH ITS DENOMINATOR.** The run-level mean is the
count-weighted combination of the cell means, and the combination is **an
arithmetic consequence of the operator, not a choice** — §2.2's own words.
**Without the cell counts the reconstruction is unavailable**, which is the second
reason §5.3 requires the denominator to travel.

**A RATIO OF SUMS DOES NOT DECOMPOSE AS A MEAN OF RATIOS.** This is the class the
requirement bites on, and it is worth stating flatly because the failure is
silent: for a quantity of the form `A / B` computed over a set, the run-level
figure is `(sum A) / (sum B)` and it is **not** the mean, weighted or unweighted,
of the cells' `A_i / B_i` except by coincidence. **A step that reports cell ratios
and an unweighted average of them has reported a figure with no referent in the
run.**

**A MINIMUM, A MAXIMUM AND ANY EXTREMUM DECOMPOSE**, being the extremum of the
cell extrema.

**AN ORDER STATISTIC DOES NOT DECOMPOSE AT ALL.** A quantile over the run is not
any combination of the cells' quantiles. **Nor does any path-dependent
quantity** — one whose value depends on the sequence rather than the multiset of
positions — because the cells are date-selected subsets and a subset's internal
sequence is not the run's.

**WHAT IS REQUIRED OF A METRIC THAT CANNOT DECOMPOSE:**

> ### **IT IS DEFINED AT THE RUN LEVEL AND ITS PER-CELL VALUES ARE NOT REPORTED
> ### AS A DECOMPOSITION.** They may be reported, and if they are they are
> ### labelled as **separate computations over subsets**, with the reconstruction
> ### identity explicitly stated as inapplicable and the reason given.

**THE POINT IS THAT §2.3's DEFECT TEST MUST NOT BE ARMED WHERE IT CANNOT FIRE
CORRECTLY.** A non-decomposing metric whose parts are presented as a decomposition
would make a correct run look defective — and, worse, would train a reader to
discount the test on the occasion it is right.

**AND THE LABEL IS NOT A COURTESY.** Under §2.3 a disagreement between parts and
whole is a **bug**, and the four causes it enumerates are all findable. **A fifth
cause — "the metric does not decompose" — would make the test useless by giving
every failure an innocent explanation.** The label removes that quantity from the
test's domain instead.

---

## 5. DENOMINATORS

### 5.1 WHAT TRAVELS HERE, TAKEN AND NOT RESTATED

**`docs/design/04_2d_aggregation.md` §5 DISCHARGED THE AGGREGATION HALF OF
`docs/handoff/31_point_5_closing.md` §5.5** and named two questions as travelling
to 4.3. **They are taken below.** The reasoning behind them — that the taken count
varies for a capacity reason (§5.2), and that the samples differ in **composition**
with a known direction because a full book preferentially skips high-ATR entries
(§5.2, on `docs/design/05_aggregate_risk_budget.md` §5.2) — **is relied on and is
not restated.**

**AND §5.5's ADEQUACY HALF IS NOT TOUCHED HERE EITHER.**
`docs/design/04_2b_point_4_decomposition.md` §5.2 records it as bearing on 4.4's
adequacy reasoning. **Unmoved.**

### 5.2 THE FIRST TRAVELLING QUESTION: MAY A QUANTITY BE DENOMINATED IN TRADE COUNT AT ALL

> ### **YES. A TRADE-COUNT DENOMINATOR IS ADMISSIBLE, AND IT IS ADMISSIBLE UNDER
> ### THE DISCLOSURE RULE AT §5.4 RATHER THAN BY BEING HARMLESS.**

**THE ARGUMENT FOR PROHIBITION, PUT AT FULL STRENGTH FIRST.**
`docs/handoff/31_point_5_closing.md` §5.5 records taken counts per training period
at **976 to 1,025** against widely varying signal supply, and concludes that
**trade count per fold measures capital, not market conditions.** A denominator
the budget pins nearly flat is a denominator that carries no information about the
period it describes, and a per-trade figure built on it inherits that.

**WHY PROHIBITION IS NEVERTHELESS THE WRONG ANSWER, AND THE REASON IS THAT THE
ALTERNATIVES DO NOT ESCAPE.**

**EVERY AVAILABLE DENOMINATOR IS A BUDGET ARTEFACT.** Trade count is pinned by
capacity. **Total risk deployed** is the count times a constant, by
`docs/design/05a_aggregate_risk_budget_amendment_1.md` Rule B's nominal charging,
so it is the same quantity rescaled. **Time in market** is shaped by the budget
too, and §8 below establishes that it is shaped in a *specific known direction*.
**Calendar time** is the one denominator the budget does not touch — and a figure
denominated in calendar time answers a different question, which is §5.3.

> ### **THERE IS NO NEUTRAL DENOMINATOR TO PREFER. PROHIBITING THE COUNT WOULD
> ### DISPLACE THE PROBLEM INTO A DENOMINATOR WHOSE DEPENDENCE IS LESS OBVIOUS,
> ### WHICH IS WORSE THAN A KNOWN ONE THAT IS DISCLOSED.**

**AND §5.5's OWN INSTRUCTION IS A DISCLOSURE INSTRUCTION, NOT A PROHIBITION.** Its
operative sentence is that **Point 4 must not read a stable trade count as
evidence of a stable opportunity set** — a constraint on inference, which §5.4
implements, rather than a constraint on arithmetic.

### 5.3 THE SECOND TRAVELLING QUESTION: COUNT-DENOMINATED AGAINST TIME-DENOMINATED

> ### **THEY ANSWER DIFFERENT QUESTIONS, AND NEITHER ESCAPES THE BUDGET.**

**A COUNT-DENOMINATED FIGURE ANSWERS: what did a position do, on average, given
that a position was taken.** Its denominator is pinned by capacity, so it says
nothing about how many opportunities there were.

**A TIME-DENOMINATED FIGURE ANSWERS ONE OF TWO DIFFERENT THINGS depending on which
time it uses**, and the two must not be conflated. **Denominated in time in
market** it answers what the deployed capital did per unit of exposure — and §8
establishes that exposure duration is itself shaped by the budget rule. **Denominated
in calendar time** it answers what the account did per unit of the window, which
folds the idle periods in and is the only shape that is not a budget artefact.

> ### **NO SHAPE IS PREFERRED HERE, AND THE CHOICE FOR ANY GIVEN METRIC BELONGS
> ### TO THE DECISION THAT CONSUMES IT.** What is committed is that the three are
> ### **different quantities**, that a metric names which it uses, and that a
> ### figure denominated in one is never compared with a figure denominated in
> ### another.

### 5.4 THE RULE, COMMITTED

> ### **EVERY FIGURE IS REPORTED WITH THE DENOMINATOR IT WAS COMPUTED OVER. A
> ### FIGURE WITHOUT ITS DENOMINATOR IS NOT REPORTED.**
>
> ### **AND WHERE THE DENOMINATOR VARIES FOR A REASON UNRELATED TO THE STRATEGY,
> ### THE FIGURE CARRIES A STATEMENT OF WHAT THE VARIATION IS A FUNCTION OF.**

**THE FIRST LIMB EXTENDS `docs/design/04_2d_aggregation.md` §5.3 TO EVERY LEVEL
AND BOTH TIERS.** That section committed it for per-period figures and added that
it applies to the run-level figure too. **It is extended here to the symbol level,
the direction level, the stratum level and to diagnostic metrics**, on the two
grounds §5.3 gives — that a figure without its denominator is displayed rather
than reported, and that the denominators are what make the reconstruction check
performable — **neither of which is a fact about periods.**

**THE SECOND LIMB IS NEW AND IS WHAT §5.5 ACTUALLY DEMANDS.** The denominator's
**value** does not tell a reader what the value is a function of. **The statement
does**: that the taken count is a function of the budget's spare capacity over
the preceding path, and that a period in which the book ran full is a period
skewed away from high-ATR entries relative to its own signal supply.

> ### **A DENOMINATOR REPORTED WITHOUT THAT STATEMENT INVITES EXACTLY THE
> ### INFERENCE §5.5 FORBIDS — READING A STABLE COUNT AS A STABLE OPPORTUNITY
> ### SET.**

**IT IS A PROPERTY OF THE FIGURE, NOT OF THE REPORT.** The statement travels
wherever the figure travels, which follows from
`docs/design/04_0_divergence_disposition_amendment_1.md` §3's treatment of a
figure quoted in passing: an obligation attached to a figure is not discharged by
having stated it once elsewhere.

### 5.5 THE PATH-DEPENDENCE CONSEQUENCE FOR A METRIC'S DEFINITION

**`docs/handoff/31_point_5_closing.md` §5.6: under the budget with real exits the
traded population is a function of realised outcomes and is not a subset of
anything knowable in advance.**

> ### **SO ANY PER-TRADE DENOMINATOR IS A QUANTITY THE STRATEGY DID NOT CHOOSE.**

**WHAT THAT PERMITS.** A per-trade figure may be defined, computed and reported.
The population is the run's actual output and is the right object to describe.
**Path dependence makes the denominator uninformative about opportunity; it does
not make the numerator wrong.**

**WHAT IT FORBIDS, AND THESE ARE THE OPERATIVE CLAUSES:**

1. **NO METRIC IS DEFINED AS A FUNCTION OF THE TAKEN COUNT'S RELATION TO THE
   CANDIDATE COUNT** — a take rate, a skip rate, a capture fraction. Such a
   quantity is a description of the budget's capacity, not of the strategy, and
   its variation would be read as the strategy's. **The counts themselves are
   reportable; the ratio as a metric is not.**
2. **NO METRIC IS DEFINED IN A WAY THAT PRESUMES THE POPULATION IS FIXED** — no
   quantity whose definition requires a stable denominator, and none defined
   relative to a population size established on the candidate population.
   `docs/handoff/31_point_5_closing.md` §5.6 records the concrete instance:
   report 21's adequacy thresholds "were established on the uncapped population
   and do not describe what is traded."
3. **NO METRIC IS DEFINED OVER A COUNTERFACTUAL POPULATION** — what would have
   been taken under a different budget, a different order, or no budget. That
   population does not exist and its figures would be model output presented as
   measurement.

**AND ONE THING IT DOES NOT FORBID, STATED BECAUSE THE OMISSION WOULD BE READ AS
AN OVERSIGHT.** Comparing two per-trade figures **at different levels of the same
run** — a symbol against another symbol, a period against another period — is
governed by `docs/design/04_2d_aggregation.md` §6 and is not touched here. **This
section constrains what a metric may be, not what a comparison supports.**

---

## 6. §5.7 — DISCHARGED PER §8.2's SPLIT

### 6.1 WHAT §8.2 ASSIGNED HERE

**`docs/design/04_2d_aggregation.md` §8.2 DISCHARGED THE AGGREGATION HALF BY
CONSTRAINING RATHER THAN CHOOSING**, and stated the assignment in terms:

> "**THE SUBSTANCE — WHICH OPERATOR — IS WHOLLY 4.3's, AND IS HANDED ON
> UNDECIDED.**"

**THREE CONSTRAINTS BIND ON WHATEVER IS CHOSEN**, and are taken as binding: the
same operator at every level; the run-level figure computed directly over the
run's positions and never reconstructed from cell figures; and the denominator
travelling — the count for an equal-weighted operator, the total risk deployed for
a size-weighted one.

**§8.2 ALSO NAMED A SECOND, SEPARABLE PIECE AS A DEFINITION RATHER THAN AN
AGGREGATION RULE:** "which of `nominal_risk_usd` and `realised_risk_usd` sits in a
per-trade R's denominator is a **definition of the metric**."

**IT ASSIGNED THE WHOLE. THE WHOLE IS DISCHARGED BELOW.**

### 6.2 THE UNIT: WHAT SITS IN A PER-TRADE R's DENOMINATOR

> ### **`realised_risk_usd`. A PER-TRADE R IS DENOMINATED IN THAT TRADE'S OWN
> ### REALISED RISK.**

**THE GROUND IS REPORT 28 §7's, WHICH §8.2 ALREADY READ AND VERIFIED:**
`realised_risk_usd` is "`qty x d`, the true 1.0R denominator **for that trade**",
and it is what makes a stop return exactly -1.0R in that trade's own unit.

**THE ALTERNATIVE IS NOT A UNIT AT ALL.** `nominal_risk_usd` is what the budget
charges — a constant by
`docs/design/05a_aggregate_risk_budget_amendment_1.md` Rule B, which commits that
the budget is charged the nominal allocation and that flooring is not reflected in
it. **A per-trade quantity divided by a constant is the dollar quantity rescaled,
not a normalised one**, and a stop would return -1.0R only on the trades where the
flooring drag happened to be zero.

**THE TWO REMAIN STORED SEPARATELY AND NEITHER IS DERIVED FROM THE OTHER AT READ
TIME**, which is report 28 §7's dual recording and is untouched. **What is
committed is which of them denominates an R, not that the other is discarded** —
the budget's own arithmetic continues to use the nominal figure, and the diagnostic
tier may compare them, since the wedge between them verifies Rule B.

### 6.3 THE OPERATOR

> ### **AN AGGREGATE OVER R-DENOMINATED PER-TRADE QUANTITIES IS EQUAL-WEIGHTED.**

**THREE GROUNDS, AND THE FIRST IS ARITHMETIC RATHER THAN JUDGEMENT.**

**FIRST — SIZE-WEIGHTING BY THE NOMINAL FIGURE IS NOT A DISTINCT OPERATOR.** By
Rule B every taken position is charged the same nominal allocation, so weights
proportional to it are all equal and the operator **is** equal weighting. **The
apparent two-way choice has only one non-degenerate alternative**, which is
weighting by `realised_risk_usd`.

**SECOND — WEIGHTING BY REALISED RISK UNDOES THE DENOMINATION §6.2 JUST
COMMITTED.** If each trade's R is that trade's outcome divided by its own realised
risk, weighting the aggregate by that same realised risk multiplies the divisor
back in. **The result is a dollar-denominated aggregate wearing an R's name** — and
a reader told it is in R units would be told something false about it.

**THIRD — THE WEDGE IS A VENUE ARTEFACT, NOT A STRATEGY PROPERTY.** §5.7 gives its
size as flooring drag of **0.80%**. Flooring drag is `qty_step` granularity: it is
a function of which symbol was traded and at what price level, and report 28 §10
records SOLUSDT's tick changing inside the measurement window. **A weight
proportional to it would make the aggregate depend on lot geometry**, which is
precisely the "quantity the strategy did not choose" hazard §5.5 addresses one
level up.

### 6.4 THE SCOPE OF §6.3, AND WHY §8.2's PREMISE IS ANSWERED RATHER THAN DENIED

**§8.2 HELD THAT THE CHOICE "CANNOT BE SETTLED WITHOUT NAMING THE QUANTITY, AND
NAMING IT IS THE LINE."** That is correct as stated and is not contradicted here.

> ### **WHAT §6.3 SETTLES IS THE OPERATOR FOR A **SHAPE** — AN R-DENOMINATED
> ### PER-TRADE QUANTITY — AND THE SHAPE CARRIES ENOUGH MEANING TO SETTLE IT,
> ### BECAUSE THE DENOMINATION IS ITSELF THE STATEMENT OF WHAT THE QUANTITY
> ### MEANS.**

**A QUANTITY DENOMINATED IN ITS OWN TRADE'S RISK UNIT HAS ALREADY ANSWERED §8.2's
QUESTION** — whether a position's contribution should scale with the capital at
risk on it. **It should not; that is what the denomination did.** The residual
choice is then not open, and §6.3's second ground is the demonstration.

**WHAT IS THEREFORE NOT SETTLED, AND IS ROUTED:**

- **AN AGGREGATE OVER A QUANTITY THAT IS NOT R-DENOMINATED** — a count, a
  duration, a rate. §6.3 does not reach it. **If 4.4 admits such a metric and its
  aggregation is not obvious from its shape, that is an amendment under §9.3.**
- **A DOLLAR-DENOMINATED AGGREGATE**, if one were ever wanted. **§6.3 forecloses
  presenting one as an R aggregate; it does not forbid one existing under its own
  name**, and admitting one would be a membership question and an amendment.

**AND THE THREE CONSTRAINTS AT §8.2 ARE SATISFIED BY §6.3.** The operator is the
same at every level, being a property of the quantity; the run-level figure is
computed directly over the run's positions; and the denominator travels, being the
count, per §5.4.

---

## 7. THE GEOMETRY HETEROGENEITY

### 7.1 THE FACT

**`docs/design/04_1g_cap_adoption.md` §0 REMOVED THE UPPER BOUND ON STOP WIDTH.**

**`docs/handoff/39_point_4_cap_candidates.md` §4.1 RECORDS THE WIDEST ATR-IMPLIED
STOP AT 49.7087 PER CENT ON SOLUSDT**, against derived cost floors that
`docs/design/04_1c_consequences_and_thresholds.md`'s chain places near one per
cent — 1.020 per cent for BTCUSDT and ETHUSDT, 1.320 per cent for SOLUSDT.

> ### **STOP WIDTHS, AND THEREFORE TARGET DISTANCES, SPAN NEARLY TWO ORDERS OF
> ### MAGNITUDE — AND EVERY ONE OF THEM IS HELD TO THE SAME TIME EXIT.**

**THE TIME EXIT IS THE THIRD FUNDING SETTLEMENT AFTER THE ENTRY CLOSE**, a
calendar function of the entry alone, giving a hold of 17 to 24 hours regardless
of geometry.

### 7.2 WHAT THAT DOES TO A POOLED FIGURE

**POSITIONS WITH RADICALLY DIFFERENT GEOMETRY ARE NOT THE SAME TRADE.** A position
whose stop sits one per cent away and one whose stop sits fifty per cent away are
different instruments held under the same clock. **A single run-level figure over
both mixes them**, and the mixture proportions are a property of the population
rather than of the strategy's rule.

### 7.3 WHAT R-DENOMINATION NORMALISES, AND WHAT IT DOES NOT

**THIS IS THE PART THAT DECIDES THE SECTION, SO IT IS SEPARATED FROM THE
DECISION.**

**WHAT NORMALISATION REMOVES — THE PAYOFF SCALE, COMPLETELY.** Under §6.2 a stop
returns exactly -1.0R and the frozen reward-to-risk puts the target at a fixed
multiple of the same unit, **for every position, at every width.** A wide-stop
position and a narrow-stop one have identical payoff magnitudes in R.

> ### **SO THE HETEROGENEITY IN **SIZE OF OUTCOME** IS NOT A RESIDUE. IT IS
> ### REMOVED BY CONSTRUCTION, AND ANY ARGUMENT FOR STRATIFICATION THAT RESTS ON
> ### IT IS ANSWERED BEFORE IT STARTS.**

**WHAT NORMALISATION DOES NOT REMOVE — TWO THINGS, BOTH STRUCTURAL AND BOTH
STATABLE WITHOUT ANY OUTCOME:**

1. **THE RELATION BETWEEN THE GEOMETRY AND THE FIXED CLOCK.** R-denomination
   rescales the price axis and leaves the time axis alone. Two positions with the
   same R geometry and stop widths differing by a factor of fifty face the same
   17-to-24-hour window to traverse distances differing by that factor. **This is
   a fact about the specification — an unbounded width rule combined with a
   calendar time exit — and it is not an assertion about what wide-stop positions
   do.**
2. **THE COST SHARE OF THE RISK UNIT.** The derived floor is `n_cost` times the
   round-trip cost, so at a floor-bound stop the cost terms are a fixed and
   substantial fraction of the risk unit by construction, while at a
   forty-nine-per-cent stop they are a small one. **The risk unit's composition
   varies with width**, and this is exactly the predicate
   `docs/design/04_1c_consequences_and_thresholds.md` §3.2 already stratifies
   condition (d) on.

### 7.4 THE DECISION

> ### **NO METRIC IS STRATIFIED BY STOP WIDTH BY DEFAULT. THE DISTRIBUTION OF
> ### STOP WIDTH IS REPORTED ALONGSIDE EVERY RUN-LEVEL AND PER-CELL FIGURE
> ### COMPUTED OVER POSITIONS, AS A DIAGNOSTIC METRIC UNDER §3.**

**THE ARGUMENT FOR MANDATORY STRATIFICATION, PUT FIRST.** §7.2 is true: a pooled
figure over a two-order-of-magnitude geometry range mixes populations. A rule
requiring every metric to be reported by width band would make the mixture
visible everywhere it occurs.

**WHY IT IS NOT ADOPTED. THREE REASONS, AND THE FIRST IS DECISIVE.**

**FIRST — MANDATORY STRATIFICATION IS A DECISION-TIER COMMITMENT AND THIS
DOCUMENT MAY NOT MAKE ONE.** Requiring a metric to be evaluated per band means
its condition is evaluated per band, which is a rule about kill conditions.
`docs/design/04_1c_consequences_and_thresholds.md` §3.3 shows the shape of that
decision and shows it being taken **for a named condition, with reasons specific
to it.** **A blanket rule taken here would pre-empt every such decision 4.4 has
not yet made**, and would do it without knowing a single condition.

**SECOND — §7.3 ESTABLISHES THAT THE STRONGEST GROUND IS ALREADY ANSWERED.** The
payoff-scale heterogeneity is normalised away. What survives is real but is not
the thing a naive reading of §7.2 has in mind, and a rule adopted against the
answered ground would be a rule adopted for the wrong reason.

**THIRD — A STRATIFICATION ALREADY EXISTS WHERE A COMMITTED DECISION NEEDED
ONE.** §3.2's non-floor-bound stratum is a stop-width predicate in all but name:
it asks whether the floor or the volatility set the stop, which is a question
about where in the width range the position sits. **The specification's existing
answer to "must a condition acknowledge width" is yes, for the condition that
needed it** — which is evidence that the case-by-case route works, not that a
blanket rule is missing.

**WHY THE DISTRIBUTION IS REPORTED RATHER THAN NOTHING BEING DONE.**

**IT COSTS NOTHING AGAINST THE FIREWALL.** A stop width is a function of the entry
price and the ATR at signal time. **It is computable before any exit resolves and
is not an outcome quantity in any regime**, so reporting it neither spends nor
depends on the lift.

**AND IT QUALIFIES UNDER §2.2(ii) AND NAMES ITS CLAUSE UNDER §3.3.** It verifies
`docs/design/04_1g_cap_adoption.md` §0 — that the run was executed with no upper
bound on width — and it is what makes §6 of that document's falsifier
interpretable. **That section commits the count of positions refused for quantity
or for notional as the adoption's own falsifier, reported wherever the engine runs
under this rule including when zero.** A refusal for quantity happens when the
risk unit divided by a wide stop distance falls below the venue minimum, **so the
width distribution is the quantity that says whether a refusal count is small
because the rule is safe or small because no wide stop arose.**

> ### **WITHOUT THE DISTRIBUTION, §6's FALSIFIER CANNOT BE READ. THAT IS THE
> ### CLAUSE, AND IT IS WHY THE DIAGNOSTIC IS ADMITTED RATHER THAN TOLERATED.**

**WHAT IS HANDED TO 4.4.** **Whether any particular kill condition must be
evaluated per width band is 4.4's**, to be taken condition by condition on
`docs/design/04_1c_consequences_and_thresholds.md` §3.3's model. **§7.3's two
surviving residues are the material for that decision** and are recorded here so
4.4 does not have to rediscover them.

**AND WHAT THIS SECTION DOES NOT DO.** It takes no position on whether wide-stop
positions behave differently. **That is an outcome quantity and it does not exist.**
The question answered here is whether a metric's definition must acknowledge the
heterogeneity — and the answer is that its **reporting** must, while its
**definition** need not.

---

## 8. §5.4 — THE RULE C HOLD-DURATION SELECTION EFFECT

### 8.1 WHAT IT SAYS, READ

**`docs/handoff/31_point_5_closing.md` §5.4:** exits free budget **at settlement
instants**, because the time exit is defined on the funding calendar; document 06
§6's enumeration shows those are exactly the entry hours that draw 24-hour holds;
so **the traded population is non-uniform in hold duration by construction, and
the non-uniformity is produced by the budget rule rather than by the market.** It
adds that any statistic sensitive to hold duration inherits it, and that Point 4
must decide whether to stratify on hold duration or to state the confound.

**`docs/design/04_2b_point_4_decomposition.md` §5.2 ATTACHES §5.4 TO 4.4.**

### 8.2 ONE NARROW PART IS VOCABULARY AND IS TAKEN; THE REST IS 4.4's

> ### **THE PART THAT IS VOCABULARY: §5.4 ESTABLISHES THAT A TIME-IN-MARKET
> ### DENOMINATOR IS A BUDGET ARTEFACT, WHICH SETTLES THE SECOND QUESTION
> ### `docs/design/04_2d_aggregation.md` §5.4 HANDED HERE.**

**WHY IT IS THIS DOCUMENT'S.** §5.3 above had to say whether a count-denominated
figure and a time-denominated one answer the same question. **The honest answer
depends on whether the time denominator escapes the capacity problem the count
has** — and §5.4 is the document that shows it does not. Without it, a step could
reasonably have concluded that denominating in exposure time sidesteps §5.5's
warning. **It does not: the exposure duration of the taken population is enriched
in long holds by the budget's own release schedule.**

**SO §5.3's COMMITMENT ABOVE RESTS ON §5.4**, and §5.4's contribution to it is
discharged here. **The disclosure obligation at §5.4's second limb reaches a
time-in-market denominator for the same reason it reaches a count.**

**WHAT REMAINS IS NOT VOCABULARY AND IS LEFT WITH 4.4.**

- **WHETHER TO STRATIFY ON HOLD DURATION OR TO STATE THE CONFOUND.** That is the
  choice §5.4 poses, and it is the same species as §7.4's: it is a decision about
  how a **condition** is evaluated, and §7.4's first reason applies unchanged.
- **THE SIZE OF THE EFFECT.** Unmeasured, per §5.4's own record, and not
  measurable here.

> ### **NO STRATUM ON HOLD DURATION IS COMMITTED BY THIS DOCUMENT.** §4.1's
> ### enumeration is closed and hold duration is not in it. **A hold-duration
> ### stratum is available to 4.4 through §9.3's amendment route.**

---

## 9. WHAT 4.4 INHERITS

### 9.1 THE VOCABULARY, COMMITTED

1. **THE TWO TIERS** and §3.2's checkable property: a diagnostic appears as an
   input to no condition, threshold or gate, and no committed decision references
   one.
2. **THE DEFAULT NOT TO COMPUTE** at §2.2, with its two admission grounds and the
   burden on the quantity.
3. **THE DIAGNOSTIC TIER'S BOUND** at §3.3: each diagnostic names the clause it
   checks, by document and section.
4. **THE OUTCOME-QUANTITY CONSTRAINT** at §3.5: admissible only where the clause
   is itself about an outcome quantity, and only as a count of violations or a
   maximum absolute deviation.
5. **THE FIVE LEVELS** at §4.1, with the run level as the default at §4.2 and a
   decomposition reported alongside rather than instead.
6. **THE RECONSTRUCTION REQUIREMENT** at §4.3, with the classes that satisfy it,
   the classes that cannot, and what is required of a metric that cannot.
7. **THE DENOMINATOR RULE** at §5.4, both limbs, at every level and in both tiers.
8. **THE PATH-DEPENDENCE CLAUSES** at §5.5: three definitions forbidden, and what
   is permitted.
9. **THE UNIT AND THE OPERATOR** at §6.2 and §6.3: a per-trade R is denominated in
   `realised_risk_usd`, and an aggregate over R-denominated per-trade quantities
   is equal-weighted.
10. **THE GEOMETRY DISPOSITION** at §7.4: no default stratification, the width
    distribution reported as a diagnostic, and §7.3's two surviving residues
    recorded as the material for any per-condition decision.

### 9.2 WHAT IS OPEN

- **THE DECISION TIER'S MEMBERSHIP**, per §1.2, including which of the seven
  quantities §9(b) enumerates are admitted. **And the routing divergence at §1.4:
  the register says 4.3, the direction says 4.4.**
- **WHETHER ANY CONDITION IS EVALUATED PER WIDTH BAND** — §7.4.
- **WHETHER TO STRATIFY ON HOLD DURATION OR TO STATE THE CONFOUND** — §8.2.
- **THE CHOICE OF DENOMINATOR SHAPE FOR ANY GIVEN METRIC** — §5.3 commits that
  the three shapes are different quantities and prefers none.

### 9.3 THE AMENDMENT ROUTE, COMMITTED EXPLICITLY

**4.4 MAY REQUIRE A QUANTITY THIS DOCUMENT DOES NOT DEFINE.** That is expected,
not a failure of either document — it is what §1.3's ordering makes likely.

> ### **DOING SO IS AN AMENDMENT TO THIS DOCUMENT, WITH ITS OWN COMMIT, MADE
> ### BEFORE THE QUANTITY IS COMPUTED.**

**IT WOULD BE `docs/design/04_3a_metric_vocabulary_amendment_1.md`**, per §11.

**AND IT IS PREFERABLE TO BOTH ALTERNATIVES, WHICH ARE NAMED SO THEY CAN BE
RECOGNISED.**

**THE FIRST ALTERNATIVE IS BENDING A CONDITION TO FIT AN AVAILABLE QUANTITY.** A
condition written to consume what happens to be defined is a condition whose
content was chosen by the vocabulary rather than by the thesis. **The bend is
invisible afterwards**, because the committed condition reads as though it had
always been about that quantity.

**THE SECOND IS DEFINING ONE SILENTLY** — introducing a quantity in 4.4's own text
without amending here. **That produces two definitions of the vocabulary in two
documents**, which is the drift `src/firewall.py`'s consolidation was created to
end: eighteen copies of one list, four of them three names behind, every test
passing.

> ### **AN AMENDMENT COSTS A COMMIT. THE ALTERNATIVES COST THE PROPERTY THAT
> ### MAKES THE ORDER GUARANTEE WORTH ANYTHING.**

**THE ORDER REQUIREMENT IS THE OPERATIVE HALF.** "Before the quantity is
computed" is the same guard as §3.4's promotion rule and rests on the same ground
at `docs/design/04_0_decision_rule.md` §4: **the commit hash is the evidence, and
it is evidence that survives everyone's account of what they were thinking.**

---

## 10. THE LEDGER AND THE OPEN ITEMS

### 10.1 THE LEDGER

**THE TOTAL, READ:** `docs/design/04_2e_housekeeping.md` §7.3 states **52**.

> ### **THIS DOCUMENT ADDS NO INSTANCE. THE TOTAL IS UNCHANGED AT 52**, and the
> ### ledger remains contiguous from (1) to (52).

**ONE CANDIDATE WAS CONSIDERED AND IS NOT LOGGED, AND THE REASON IS GIVEN SO THE
CALL CAN BE CHECKED.** §1.4's routing divergence — the commissioning instruction
assigning to 4.4 what `docs/design/04_2b_point_4_decomposition.md` §3.3 assigns to
4.3 — resembles instances (50), (51) and (52), each a statement about a document
written from a mental model of it.

**IT IS NOT ONE, ON TWO GROUNDS.**

**FIRST, IT MAKES NO FALSE CLAIM ABOUT ANY DOCUMENT.** (50) attributed a count to
a document that declares none; (51) cited a section that does not exist; (52)
transcribed four of five register members. **This instruction cites nothing and
misdescribes nothing** — it issues a direction that the register does not yet
reflect, which is a thing a project owner may do and which
`docs/design/04_2b_point_4_decomposition.md` §5.1 has precedent for recording as
the owner's direction.

**SECOND, `docs/design/04_1a_denomination.md` §6's CRITERION IS NOT MET.** The
remediation on offer — recording both, routing explicitly, and naming the register
update as owed — **degrades no otherwise correct artifact.** Nothing false enters a
frozen document.

### 10.2 THE OPEN ITEMS REGISTER — THIS DOCUMENT'S ENTRIES

**RECORDED IN THE FORM `docs/design/04_2b_point_4_decomposition.md` §5 USES. THAT
DOCUMENT IS NOT EDITED.**

**DISCHARGED:**

- **`docs/handoff/31_point_5_closing.md` §5.5's METRIC HALF**, routed here by
  `docs/design/04_2d_aggregation.md` §5.4. **Discharged at §5.2, §5.3 and §5.4**:
  a trade-count denominator is admissible under disclosure rather than by being
  harmless; the count and time shapes answer different questions and neither
  escapes the budget; and the disclosure rule is committed in two limbs at every
  level and in both tiers. **Its adequacy half is unmoved and remains 4.4's.**
- **`docs/handoff/31_point_5_closing.md` §5.7**, whose substance
  `docs/design/04_2d_aggregation.md` §8.2 handed here whole. **Discharged at §6.2
  and §6.3**: the unit is `realised_risk_usd`; the operator is equal weighting;
  §8.2's three constraints are satisfied. **§6.4 records what the discharge does
  not reach.**
- **`docs/design/04_2d_aggregation.md` §5.4's TWO QUESTIONS.** **Discharged at
  §5.2 and §5.3.**

**PARTLY DISCHARGED, WITH THE REMAINDER NAMED:**

- **`docs/handoff/31_point_5_closing.md` §5.4.** **Its vocabulary part is
  discharged at §8.2** — a time-in-market denominator is a budget artefact, which
  is what §5.3's commitment rests on. **The stratify-or-state choice and the
  effect's unmeasured size remain 4.4's, unmoved.**
- **§9(b).** **Its "each specified exactly once" requirement is discharged
  generically at §4.2.** **Which quantities are admitted remains open**, per §1.2
  and §1.4.

**NEW, AND CREATED BY THIS DOCUMENT:**

- **THE GEOMETRY DISPOSITION'S HAND-FORWARD** — whether any kill condition must be
  evaluated per width band, with §7.3's two residues as its material. **4.4's. No
  owner at this commit.**
- **THE REGISTER UPDATE FOR §1.4's ROUTING.** Whoever settles whether §9(b)'s
  membership is 4.3's or 4.4's should record it against
  `docs/design/04_2b_point_4_decomposition.md` §3.3. **No owner at this commit.**

**CARRIED UNCHANGED:** every item at `docs/design/04_2e_housekeeping.md` §7.4.
**The `simulate.py` cap divergence there is closed** by commit `3e35ba5` and
`docs/handoff/43_point_4_stop_cap_implementation.md`; the remaining nine stand as
recorded. **The four Point 6 obligations are unmoved and none is a freeze
precondition.**

**NOTHING ELSE IN THE REGISTER MOVES.**

---

## 11. CHANGE DISCIPLINE

**A CHANGE TO ANY COMMITMENT HERE IS A NEW DOCUMENT WITH ITS OWN COMMIT AND AN
EXPLICIT STATEMENT OF WHAT CHANGED AND WHY — NEVER A SILENT EDIT.** It would be
`docs/design/04_3a_metric_vocabulary_amendment_1.md`.

**THE CLAUSE MOST EXPOSED IS §2.2's DEFAULT NOT TO COMPUTE.** It will first be
inconvenient when the run produces a table and someone wants one more column that
would take a line of code and answers an obvious question. **The rule's whole
content is that the obvious question is the dangerous one**, because a quantity
nobody committed to consuming is a quantity whose only consumer is an impression.

**THE SECOND MOST EXPOSED IS §3.4's PROMOTION ORDER.** It will be inconvenient at
exactly the moment a diagnostic turns out to be informative, which is the moment
its promotion is least defensible. **An amendment permitting a promotion after
inspection must say that it permits choosing a decision's input in light of what
the input says**, in those words.

**AND §6.3's OPERATOR IS COMMITTED FOR A SHAPE, NOT FOR A LIST.** A later document
admitting a metric outside that shape does not thereby reopen §6.3; it needs an
operator of its own, by §6.4.

---

**Committed alone with the manifest and this step's report-back. The vocabulary
committed: two tiers with a checkable property that makes the tier a fact about
the decision graph rather than about intent; a default not to compute, stated
against the one channel report 41 §5 records as unclosable, and the first such
rule in the chain because until the freeze there was nothing to look at; five
levels with the run level as the default and the reconstruction requirement
sorted by metric class; a two-limb denominator rule extended to every level and
both tiers, with three metric definitions forbidden on path dependence; §5.7
discharged whole — the unit is the trade's own realised risk and the operator is
equal weighting, on the ground that weighting by realised risk undoes the
denomination; the geometry heterogeneity disposed of by reporting the width
distribution as a diagnostic whose clause is 04_1g §6's falsifier, with mandatory
stratification refused because it would be a decision-tier commitment; §5.4's
vocabulary part taken and its choice left with 4.4; and the amendment route
committed with its order guarantee. Ledger unchanged at 52. Membership is not
closed, no threshold is set, no kill condition is committed, and no figure is
computed.**
