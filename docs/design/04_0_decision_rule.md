# THE DECISION RULE — PRE-REGISTERED

**Sub-point 4.0, step 2B.** Preconditions for the validation design.

## 1. WHAT THIS DOCUMENT IS

**A PRE-REGISTRATION, FROZEN ON COMMIT.** Made **before step 3's derivation
runs** and **before any performance figure exists for this thesis.** The commit
hash is the proof of the order.

**IT JOINS THE FROZEN SPECIFICATION ON ITS COMMIT**, per
`docs/design/04_0_divergence_disposition_amendment_2.md` §2, whose membership
list is open forward for exactly this case.

> **IT COMMITS NO NUMERIC THRESHOLD. IT SETS NO VALUE FOR THE COST TOLERANCE. IT
> SELECTS NO BRANCH.**
>
> **It commits the RULES under which sub-point 4.1 will select one.**

**Nothing here is computed, measured or derived.** Every figure carries a
citation verified against the file it came from.

---

## 2. WHAT IS ALREADY SETTLED, AND WHAT IS NOT

### THE FALSIFIED OPTION

> **RETAINING BOTH `COST_TOLERANCE_R = 0.11` AND THE 1.500% STOP FLOOR AS A
> MUTUALLY CONSISTENT PAIR IS FALSIFIED BY COMMITTED MEASUREMENT, NOT BY
> ARGUMENT.**

`docs/handoff/28_point_5_3_1_sizing.md` §9 measured the floor-bound stratum's
minimum `c/s` at **0.1122** against the tolerance's **0.11**, across 2,927
floor-bound positions of 11,384 candidates, and states that **there is no overlap
at all.**

**THE 1.500% FLOOR DOES NOT ENFORCE A TOLERANCE OF 0.11 AND CANNOT.** Every
position the floor governs breaches the tolerance the floor exists to enforce.

**THIS WAS KNOWN BEFORE STEP 3 WAS SCOPED.** Step 3 will describe **the shape of
the relationship** between the tolerance and the required floor width. **It will
not adjudicate this pair**, because the pair is already adjudicated and the
verdict is in a committed report.

### THE OPTION CLOSED BY A PRIOR COMMITMENT

**Holding the floor at a constant and moving the tolerance to fit it is CLOSED**
by the floor-shape commitment recorded in §4 below.

Two reasons, both structural:

- **It reinstates the free parameter that commitment removes.** A floor stated as
  a constant, with a tolerance chosen to match, is a tunable number with a
  constraint's name on it.
- **It moves the primitive to accommodate the derived quantity.** The tolerance
  is what the floor is for; deriving the tolerance from the floor inverts the
  dependency and makes the constraint an artifact of the mechanism meant to
  enforce it.

**IT IS NOT A LIVE BRANCH.**

### WHAT REMAINS

**A two-way fork, set out in §3.**

---

## 3. THE TWO-WAY FORK

### BRANCH B — A COST-TOLERANCE CONSTRAINT EXISTS

**A tolerance parameter is retained, justified on grounds stated and committed in
sub-point 4.1, and the stop floor is DERIVED ALGEBRAICALLY to enforce it.**

### BRANCH C — NO COST-TOLERANCE CONSTRAINT EXISTS

**The tolerance is retired.** The stop floor is governed by **whatever else
genuinely binds**: the tick grid, lot-size granularity, and the leverage the
venue permits.

### THE BRANCHES ARE EXHAUSTIVE AND MUTUALLY EXCLUSIVE GIVEN §2

Either a cost-tolerance constraint exists or it does not. §2 removes the two
options that are neither. **NEITHER BRANCH IS SELECTED HERE.**

### WHY STEP 3 DOES NOT NEED THE BRANCH RESOLVED FIRST

**Step 3 produces the required floor width AS A FUNCTION OF the tolerance
parameter — a curve, not a point.**

- **Under Branch B**, the curve is evaluated at whatever value 4.1 commits.
- **Under Branch C**, the curve documents **what was given up and at what width**
   — the record of the constraint that was retired, in the units it would have
  bound in.

> **THE PARAMETRIC FORM IS WHAT MAKES THE BRANCH CHOICE SEPARABLE FROM THE
> MEASUREMENT**, and that separation is the reason step 3 can run before 4.1
> concludes.

### AND THE BRANCH CHOICE IS NOT DECIDABLE FROM STEP 3's OUTPUT

> **WHETHER THE CONSTRAINT SHOULD EXIST IS A QUESTION ABOUT WHAT IT PROTECTS. NO
> POINT ON THE CURVE ANSWERS IT.**

It is **owned by 4.1 and decided on rationale.**

**THIS DOCUMENT EXISTS BECAUSE A QUESTION DECIDED ON RATIONALE AFTER A
MEASUREMENT IS VISIBLE IS A QUESTION DECIDED BY THE MEASUREMENT.** The rationale
arrives second and takes the shape of the number it is written to accommodate,
and nobody involved need intend it.

---

## 4. THE TWO RULES WITH TEETH

### THE ORDER RULE

> **THE JUSTIFICATION FOR THE TOLERANCE MUST BE STATED AND COMMITTED IN ITS OWN
> COMMIT BEFORE STEP 3's CURVE IS EVALUATED AT ANY CANDIDATE VALUE OF THE
> TOLERANCE.**

Under **Branch B** that justification is **an account of what the tolerance
protects**. Under **Branch C** it is **the account of why it is retired and what
governs the floor instead.** Either way it is committed first.

**THE REASON:** choosing the tolerance by reading off which value yields a
comfortable floor is the failure mode this rule exists to prevent. **The guard
against it is ORDER, not a threshold.** It is the same mechanism as the
performance firewall: **the commit hash is the evidence**, and it is evidence
that survives everyone's account of what they were thinking.

**PRODUCING THE CURVE IS NOT EVALUATING IT.** Step 3 **may run and commit the
parametric result before 4.1 concludes.** What the order rule forbids is
**selecting a tolerance value after seeing the floor widths the candidate values
imply.**

### THE DIRECTION RULE

> **THE TOLERANCE IS THE PRIMITIVE AND THE FLOOR IS DERIVED FROM IT. THE
> DERIVATION RUNS TOLERANCE TO FLOOR AND NEVER FLOOR TO TOLERANCE.**

**THIS FOLLOWS FROM THE FLOOR-SHAPE COMMITMENT, WHICH IS BINDING:** the stop
floor is **derived from the cost algebra with no free parameter**, on the ground
that **a floor stated as a constant is a tunable parameter wearing a
constraint's name.**

**THE DIRECTION RULE IS WHAT STOPS THE CLOSED OPTION IN §2 FROM REAPPEARING
UNDER ANOTHER NAME.** Without it, "we retained the floor and re-derived the
tolerance to match" is available as a description of the same move.

---

## 5. WHAT EACH BRANCH OWES

### BRANCH B OWES

**An account of what the tolerance protects that SURVIVES NET-SOLVED GEOMETRY.**

Under net-solved geometry the stop is **exactly one risk unit** and the target
**exactly 1.5 risk units** by construction, so **costs do not erode the R
multiples — they are contained within them.**

**THE ORIGINAL DERIVATION DOES NOT SURVIVE.**
`docs/handoff/31_point_5_closing.md` §5.1 records that the *"one third of the
~0.34R minimum detectable edge"* derivation rested on a premise net-solved
geometry does not supply, and that **the tolerance must be re-argued before any
performance figure is seen.**

> **A REPLACEMENT ACCOUNT MUST BE ARGUED RATHER THAN ASSUMED.**

**NO CANDIDATE REPLACEMENT ACCOUNT IS STATED, ENDORSED OR SKETCHED IN THIS
DOCUMENT.** 4.1 owes the argument, and pre-empting it here would be choosing it —
which is the thing §4's order rule exists to prevent, applied to the rationale
rather than to the number.

### BRANCH C OWES

**A statement of what governs the stop floor instead** — the tick grid, lot-size
granularity, the leverage the venue permits, or some combination, stated
explicitly rather than left as a residual.

**AND AN EXPLICIT DISPOSITION FOR A CONSEQUENCE THE BRANCH CARRIES:**

> **UNDER BRANCH C THE FLOOR-BOUND STRATUM CEASES TO EXIST AS A CATEGORY.**

The thesis's **kill condition (d)** is written against exactly that stratum: it
requires the advantage to survive **among non-floor-bound trades**. With no
floor-derived-from-a-tolerance, the stratification the condition is built on has
no definition.

**KILL CONDITION (d) MUST THEREFORE BE RESTRUCTURED OR REPLACED UNDER BRANCH C.
THIS IS AN OBLIGATION AND NOT AN OPTION.**

**AND `docs/handoff/31_point_5_closing.md` §5.9's OPEN QUESTION IS SUBSUMED INTO
IT** — whether (d) is evaluated per fold under the majority rule or pooled. Under
Branch C that question is not answered separately; it is answered by whatever
replaces (d).

### NEITHER BRANCH IS CHEAPER

**Branch B owes an argument that has already failed once. Branch C owes the
restructuring of a frozen kill condition.** **THIS DOCUMENT EXPRESSES NO
PREFERENCE BETWEEN THEM.**

---

## 6. THE CONSEQUENCES LEDGER

### THE PRINCIPLE

> **ANY CHANGE TO THE STOP FLOOR IS ASSESSED IN THESE QUANTITIES AND NOT IN
> ADJECTIVES.**

A criterion phrased as **viability, absurdity, collapse or unnaturalness is not
evaluable**, and is decided in practice by whoever reads it **after the numbers
arrive.**

**THIS IS THE PROJECT'S RECURRING DEFECT CLASS APPLIED TO A DECISION RULE** — a
criterion written from a mental model of a quantity rather than from its
implementation or its achievable range. **This ledger exists to keep the
assessment denominated in quantities that have implementations and known
achievable ranges.**

### THE FOUR QUANTITIES, WITH THEIR REFERENCE POINTS AT THE 1.500% FLOOR

**1. THE FLOOR-BINDING FRACTION.** Currently **25.71% pooled** across the 11,384
candidates, **27.02% among taken** and **24.24% among skipped**
(`docs/handoff/26_point_5_2_budget_cost.md` §4.1, restated at
`docs/handoff/31_point_5_closing.md` §4.2). Binding among taken positions ranges
from **5.37% to 68.28%** across the eighteen fold periods
(`docs/handoff/31_point_5_closing.md` §5.9). **A wider floor raises this.**

**2. LOT-GRANULARITY DRAG.** Currently **0.80% of nominal risk** across the
11,384 candidates — **$1,826.85 of $227,680** — and **0.78%** across the 6,021
taken (`docs/handoff/28_point_5_3_1_sizing.md` §8.2). **ETHUSDT is the
granularity-binding symbol and the worst single position is 9.21%**
(`docs/handoff/28_point_5_3_1_sizing.md` §8.3). **A wider floor means smaller
notional per position, fewer contract units, and a larger granularity share.**

**3. ABSOLUTE TARGET DISTANCE IN PRICE SPACE.** The target sits at **1.5 times
the stop distance** in price terms (thesis §5.2), so **it scales directly with
the floor.** A wider floor puts the target further away in absolute terms, and
the reward has to be travelled before it is collected.

**4. THE THICKNESS OF THE NON-FLOOR-BOUND STRATUM, per fold and pooled.**

> **THIS ONE MATTERS MOST, AND THE REASON IS STRUCTURAL: KILL CONDITION (d) IS
> EVALUATED ON THAT STRATUM.**

`docs/handoff/31_point_5_closing.md` §5.9 records that at **fold 4 test** it is
already about **157 pooled across three symbols — roughly 52 per symbol** — from
**495 taken** at **68.28% floor-bound.**

**A WIDER FLOOR THINS THE EXACT STRATUM A KILL CONDITION DEPENDS ON.**

**A NUMERIC COINCIDENCE, RECORDED SO IT IS NOT CONFLATED.** The figure **157**
also appears in `docs/handoff/26_point_5_2_budget_cost.md` §9 as **SOLUSDT's own
worst test-fold taken count, also at fold 4**. **These are two different
quantities that coincide numerically**, and §5.9 flags the coincidence for the
same reason it is repeated here.

### A DIRECTIONAL CORRECTION, BECAUSE THE INTUITION RUNS THE WRONG WAY

> **WIDENING THE FLOOR DOES NOT RAISE THE LEVERAGE REQUIREMENT. IT LOWERS IT.**

Risk per position is fixed, so **notional is inversely proportional to stop
width**: a wider stop buys a smaller position.
`docs/handoff/26_point_5_2_budget_cost.md` §5.5's maximum of **3.5964× under the
cap** would **fall, not rise.**

**LEVERAGE IS THEREFORE NOT A CONSTRAINT THAT BINDS AGAINST WIDENING, AND MUST
NOT BE OFFERED AS ONE.** It is recorded here because it is the argument most
likely to be reached for, and it points the wrong way.

### NO THRESHOLD IS SET ON ANY OF THE FOUR

**This ledger states what is measured and where the current values sit. What
value of any of them would be unacceptable is NOT DECIDED HERE.**

---

## 7. STEP 3's DERIVATION AGENDA

### ITEM 1 — THE PARAMETRIC STOP FLOOR

**Required floor width as a function of the tolerance parameter, per symbol and
per fee treatment**, solved from **the same cost algebra
`docs/handoff/28_point_5_3_1_sizing.md` §9 measured `c/s` against.**

**OUTPUT IS A CURVE OR A CLOSED FORM IN THE TOLERANCE — not a set of point values
at one tolerance.** A point set at one tolerance would make §4's order rule
unenforceable, because it would embed a chosen tolerance in the measurement.

**"FEE TREATMENT" IS DEFINED EXPLICITLY, BECAUSE IT HAS BEEN CONFUSED WITH VENUE
VOLUME TIERS.** It means **the maker/taker composition of the three legs**:

- **taker entry** at the signal-bar close (thesis §4.2);
- **taker stop**, via a conditional market order (document 06 E2);
- **maker limit target** (document 06 E3).

**Confirmed in the implementation:** `costs.position_size` charges the taker fee
on both the entry and the stop leg, and `costs.solve_target` solves the exit at
the maker fee.

> **IT DOES NOT MEAN VIP VOLUME TIERS.** This account sits at the base tier and
> **the derivation is at that tier throughout.**

### ITEM 2 — THE §5.4 MAGNITUDE

**Carried from `docs/design/04_0_divergence_disposition_amendment_2.md` §8:** the
magnitude of the breach for which `docs/design/06_exit_resolution_spec.md` §5.4
rejected the realised-cash-flow funding treatment. **That section states no
numeral.**

The quantity is **a function of the funding rate, the settlement count and the
stop width.** **IT IS DERIVED FROM THE IMPLEMENTATION, NOT ASSERTED FROM THE
ALGEBRA IN PROSE.**

**WHY IT IS OWED:** sub-point 4.1 owes a criterion reconciling **a categorical
refusal with a magnitude-based acceptance**. **That criterion is fitted to
whichever half of the evidence is visible if only one magnitude is known.**

### THE FIREWALL POSITION OF STEP 3

**Every quantity above is a cost, a price distance or a count. NONE IS AN OUTCOME
QUANTITY.** **Step 3 does not run the engine and does not touch `exit_reason`.**

---

## 8. STEP 3's FAILURE BRANCH

### THE FAILURE THAT IS ACTUALLY LIKELY, AND IT IS NOT A SOLVER PROBLEM

> **THE COST TERM IS NOT A SINGLE FUNCTION OF STOP WIDTH, BECAUSE THE EXIT LEGS
> DIFFER IN FEE TREATMENT: THE STOP LEG FILLS TAKER AND THE TARGET LEG FILLS
> MAKER.**

A constraint of the form *`c/s` at most tolerance* is therefore **under-specified
until it says WHICH `c`**:

- the cost of the **stop path**;
- the cost of the **target path**;
- **the worse of the two**;
- or **one constraint per path**.

**Step 3 may find there is no single closed form in the tolerance for this
reason.**

### THE RULE, AND IT IS AN ORDER RULE RATHER THAN A THRESHOLD

> **IF STEP 3 FINDS THE CONSTRAINT UNDER-SPECIFIED IN THIS WAY, IT REPORTS THE
> UNDER-SPECIFICATION AND STOPS. IT DOES NOT CHOOSE WHICH COST TERM TO USE.**

**Which `c` the constraint is denominated in is a SPECIFICATION DECISION.** It is
made **in 4.1, in its own commit, on stated grounds, BEFORE the corresponding
floor widths are evaluated.**

> **IT IS SPECIFICALLY FORBIDDEN TO SELECT THE COST TERM AFTER BOTH CANDIDATE
> FLOOR WIDTHS ARE VISIBLE.**

**That is the direction rule and the order rule failing together**, and **it is
the most likely way this decision gets made badly** — not by anyone deciding to
cheat, but by the choice presenting itself as obvious once one of the two numbers
is uncomfortable.

### THE SECONDARY FAILURE

**If a closed form does not exist for any other reason, a numerical solution over
a stated grid of tolerance values is acceptable**, provided **the grid is
committed before it is solved** and **the solution method is reported.**

**NON-LINEARITY IS NOT A FAILURE. IT IS A SOLVER CHOICE.**

### WHAT IS NOT A FAILURE BRANCH

**A result that is inconvenient. A result that implies a wide floor. A result
that implies a large re-measurement bill for reports 26, 28 and 30.**

> **THE STANDING PRINCIPLE: EXECUTION REALITY OVER MEASUREMENT CONVENIENCE.**
>
> **THE COST OF RE-MEASURING IS NOT A CONSIDERATION IN THE BRANCH CHOICE.**

If the derivation implies that three closed reports rest on a floor that does not
enforce what it was meant to, **that is a finding about the reports and not an
argument against the derivation.**

---

## 9. RESIDUAL ITEMS CARRIED FROM STEP 2A

**These are LOGGED CONTEXT under step 2A's stopping rule
(`docs/design/04_0_divergence_disposition_amendment_2.md` §1.1). THEY ARE NOT
AMENDMENTS TO STEP 2A, WHICH IS CLOSED.**

**(i) THE FROZEN-SPECIFICATION ADMISSION CRITERION IS CIRCULAR.**
`docs/design/04_0_divergence_disposition_amendment_2.md` §2 admits future
documents as those *"committed as a pre-registration under this project's
discipline"*, **without stating what marks a document as one.** The phrase
defines membership by the property whose definition is at issue — **in a document
that adopts a standing rule against scope terms defined by neither extension nor
principle.** **An operational marker is owed. None is invented here**; the
obligation is stated and left open.

**(ii) THE NUMBER (37) WAS NOT ALLOCATED BY ITS RHETORICAL USE.** That document's
§8 writes that answering the routed magnitude there *"would be instance (37)"*.
**THAT SENTENCE ALLOCATED NOTHING AND RESERVED NOTHING.** The next ledger
instance takes **the next free number in the ordinary way** — which, the total
standing at 36, is 37, **and it is assigned below in (iv) to an unrelated
defect.** This is recorded to prevent a later erratum against a frozen document.

**(iii) THE SELF-REFERENCE CLAUSE DOES NOT SAY BY WHOM.** That document's §4
requires a pre-registration to precede the thing it registers being *"measured,
inspected or relied upon"*, and **does not say by whom.** A document relied upon
by its own author while drafting, before commit, sits outside the plain reading.
**Logged. No disposition is made here.**

**(iv) A VERIFICATION CHECK ASSERTED A FALSE DEFECT AGAINST A CLEAN ARTIFACT.** A
check written in the collaboration channel asserted a formatting defect against
`docs/design/04_0_divergence_disposition_amendment_2.md` **using a character
class that matched em dashes rather than box-drawing characters.** **The document
was correct and the check was wrong.**

> **IT IS THE RECURRING DEFECT CLASS APPLIED TO A VERIFICATION CRITERION — a
> check written from a mental model of what it matches rather than from what it
> matches.**

**THE DECISION, MADE HERE AND RECORDED: IT IS LOGGED AS A LEDGER INSTANCE,
NUMBERED (37), NOT AS AN OPERATIONAL NOTE.**

**THE GROUNDS.** The ledger's method
(`docs/handoff/31_point_5_closing.md` §7.1) counts **every defect a committed
document explicitly identifies as an instance of the class, one per distinct
defect.** It **already counts defects caught before they reached an artifact** —
instance (19) is a claim corrected by the check that examined it, with no artifact
ever carrying the error. **Excluding a defect because it was caught would make
the ledger count only the failures that got through, which biases it downward
exactly as the process improves.** A verification criterion is a new surface for
the class, and that is the kind of thing the ledger exists to surface.

**(37) IS UNRELATED TO §8's RHETORICAL USE OF THE SAME NUMBER.** It is the next
free number, assigned by ordinary succession to this defect, and it has nothing
to do with the routed magnitude.

### THE LEDGER TOTAL

**Reconciled at `docs/design/04_0_divergence_disposition_amendment_2.md` §5 as
36.** **This document adds instance (37).**

> **THE TOTAL IS NOW 37.** 36 + 1 = 37. **No earlier instance is renumbered or
> recounted**, and the ledger remains contiguous from (1) to (37).

---

## 10. CHANGE DISCIPLINE

**A CHANGE TO ANY RULE IN THIS DOCUMENT IS A NEW DOCUMENT WITH ITS OWN COMMIT AND
AN EXPLICIT STATEMENT OF WHAT CHANGED AND WHY — NEVER A SILENT EDIT.** Under the
naming convention adopted for Point 4 documents it would be
`docs/design/04_0_decision_rule_amendment_1.md`.

**A SILENT EDIT IS A CONTAMINATION EVENT.**

> **THE ORDER RULE IN §4 IS THE CLAUSE MOST EXPOSED TO LATER PRESSURE**, because
> **it binds at exactly the moment the curve exists and the tolerance does
> not** — when the floor widths are on the desk, the justification is not
> written, and writing it first is the slowest available path.
>
> **IT IS WRITTEN TO BE INCONVENIENT THEN. THAT IS ITS ENTIRE FUNCTION**, and a
> clause of that kind is worth nothing if it can be revised by the person it is
> inconvenient for, at the moment it becomes inconvenient.

---

**Committed alone, before step 3's derivation and before any performance figure
exists for this thesis. One option falsified by measurement, one closed by prior
commitment, a two-way fork left open, two rules with teeth, four quantities in
which the consequences are denominated, one derivation agenda with its failure
branch, and four residual items logged. No branch is selected, no threshold is
set, and no tolerance value is named.**
