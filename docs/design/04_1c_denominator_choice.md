# THE DENOMINATOR CHOICE

**Point 4, sub-point 4.1c, preparatory. One denominator is decided. Nothing is
derived.**

## 0. THE SCOPE LIMIT, STATED FIRST

> ### THIS DOCUMENT DECIDES A DENOMINATOR. IT DERIVES NO CLOSED FORM, STATES NO
> ### WIDTH, NO SHARE AND NO TOLERANCE VALUE, AND RECOMPUTES NOTHING.

`docs/design/04_0_decision_rule.md` §8 requires that which quantity the constraint
is denominated in is a specification decision made *"in its own commit, on stated
grounds, BEFORE the corresponding floor widths are evaluated"*, and states that
selecting it after the candidate widths are visible is **specifically forbidden**.

**No requirement given to this document was read as asking for a derivation.**
None appeared to. §4.3 names one question this decision opens that only a
derivation can answer, and routes it to §6 rather than attempting it.

---

## 1. WHAT THIS DOCUMENT IS

**A PRE-REGISTRATION, FROZEN ON COMMIT.** Made **before any width has been derived
under path two's risk unit**, and **before any performance figure exists for this
thesis**. It joins the frozen specification on its commit, per
`docs/design/04_0_divergence_disposition_amendment_2.md` §2.

**IT AMENDS THE CONSTRAINED RATIO'S DENOMINATOR AS SET AT
`docs/design/04_1a_denomination_amendment_1.md` §3.1**, under that document's §8
change discipline. **Neither that document nor any other frozen document is
edited.**

It is filed at 4.1c, alongside `docs/design/04_1c_path_and_scope.md`, for the
reason that document's §1 gives: these are the documents 4.1c owes before its
level-setting can proceed, and they decide questions the 4.1a chain did not
reach.

### 1.1 PRECEDENCE

- **On what the constrained numerator is divided by, this document governs.**
- **Amendment 1 governs on everything else it decided**, including the numerator's
  narrowing to the unvalidated terms' contribution.
- **`docs/design/04_1c_path_and_scope.md` governs on which risk unit** — path two's
  — **and on funding's membership.**

### 1.2 WHAT IS NOT REOPENED

**`docs/design/04_1b_tolerance_and_branch.md`'s RATIONALE AND ITS BRANCH B CHOICE
STAND.** What the constraint protects is still *"how much of the risk unit rests
on an unvalidated estimate"* (4.1b §3.5).

**THE NUMERATOR'S MEMBERSHIP STANDS** — the unvalidated terms' contribution as
narrowed at amendment 1 §3.1, extended to funding at path-and-scope §3.

**PATH TWO AS THE RISK UNIT STANDS**, as committed at path-and-scope §2.1.

> **THIS CHANGES ONLY WHAT THE NUMERATOR IS DIVIDED BY.**

---

## 2. THE DECISION

### 2.1 THE DECISION

> ### THE CONSTRAINT IS THE UNVALIDATED SUM OVER THE RISK UNIT — PATH TWO's
> ### DENOMINATOR, FUNDING INCLUDED ON BOTH SIDES — AT MOST THE TOLERANCE.
> ### THE STOP-DISTANCE DENOMINATOR IS RETIRED.

Stated precisely, and **not solved for a width**:

    numerator    = the unvalidated terms' per-unit contribution: the stop
                   haircut, the entry slippage, and the funding term

    denominator  = the risk unit -- the denominator `portfolio.size_position`
                   assembles at `src/engine/portfolio.py:298-299`, being path
                   one's five terms plus `funding_pu`

**THE RETIRED FORM DIVIDED BY THE STOP DISTANCE**, the absolute price move from
entry to the stop. That quantity remains what it was, remains observable, and
remains the geometry the floor sets. **It is no longer what the constraint is a
share of.**

### 2.2 THE GROUND: THE CONSTRAINT AND THE PROTECTED QUANTITY BECOME ONE OBJECT

`docs/design/04_1b_tolerance_and_branch.md` §3.2 names the protected quantity:

> **THE FRICTION SHARE IS THE FRACTION OF THE RISK UNIT DETERMINED BY ESTIMATE
> RATHER THAN BY OBSERVABLE PRICE GEOMETRY.**

**THE RETIRED FORM DID NOT BIND THAT QUANTITY. IT BOUND A PROXY FOR IT.** The
constraint bound the unvalidated sum over the stop distance; the rationale
protects the unvalidated sum over the risk unit. The two differ by the ratio of
stop distance to risk unit, which varies by symbol and by width.

> **BINDING THE PROTECTED QUANTITY DIRECTLY DOES NOT MAKE THE MAPPING SMALLER. IT
> REMOVES THE MAPPING.**

That distinction is the whole ground. A proxy can be made tighter, and a tighter
proxy is still a proxy — the constraint would still be one quantity and the
rationale another, and every question about the gap between them would still
arise. **Under this decision there is no gap, because there are not two
quantities.**

### 2.3 THE ALGEBRAIC RELATION, STATED AND NOT SOLVED

Writing `tau` for the tolerance, `U` for the unvalidated sum, `s` for the stop
distance and `d` for the risk unit:

- **UNDER THE RETIRED FORM**, the constraint was `U / s` at most `tau`, so the
  protected quantity `U / d` equalled **`tau` multiplied by `s / d`** at the
  binding width.
- **UNDER THIS FORM**, the constraint is `U / d` at most `tau`, so the protected
  quantity **equals `tau`** at the binding width.

**NO WIDTH IS DERIVED FROM EITHER FORM HERE, AND NO VALUE OF `s / d` IS STATED.**
The factor is named to identify what is removed, not to be evaluated. That
`s / d` varies by symbol and by width is a structural statement about the two
expressions and is not a measurement.

---

## 3. WHAT THIS DOES NOT MAKE UNIFORM

**THIS SECTION FORECLOSES A READING THE DECISION INVITES.**

### 3.1 WHAT IS TRUE

**EQUAL TOLERANCE NOW DELIVERS EQUAL PROTECTED QUANTITY ACROSS SYMBOLS AND
DIRECTIONS, BY CONSTRUCTION RATHER THAN BY MEASUREMENT.** At the binding width the
protected quantity is the tolerance, and the tolerance is one number.

> **THAT IS A FACT ABOUT THE CONSTRAINT. IT IS NOT A FACT ABOUT THE SYMBOLS.**

Nothing has been discovered about BTCUSDT, ETHUSDT or SOLUSDT. A definition was
changed.

### 3.2 WHAT IS NOT TRUE

**THE SYMBOL-DEPENDENT STRUCTURE IS NOT REMOVED. IT MOVES.**

It moves into the **required floor widths**, which will differ across symbols by
more than they do under the retired form — because a symbol carrying twice the
unvalidated rate must buy the same protected share with **more geometry**. The
variation that was visible in the protected quantity becomes variation in the
width required to achieve it.

**NO FIGURE FOR THAT DIFFERENCE IS STATED HERE.** Its magnitude, its direction
across the tolerance range, and whether it is larger or smaller than the
stratum-thinning pressure report 32 §5.4 recorded are **the derivation's to
produce** (§6.1). This document asserts only that the structure does not vanish,
which follows from the rates differing.

### 3.3 THE NON-UNIFORMITY APPARATUS BECOMES INAPPLICABLE, NOT SATISFIED

**THE THRESHOLD AT `docs/design/04_1c_non_uniformity_check.md` §4, ITS VERDICT,
AND REPORT 34's RE-RUN ALL BECOME INAPPLICABLE.**

The criterion compares `S_max`, the maximum cross-symbol spread of the protected
quantity over the grid, against `R_min`, the smallest within-cell range of that
quantity over the grid. §4.3 of that document states what it encodes: *"If
changing the tolerance moves the protected quantity less than choosing a
different symbol does, then the tolerance is not the thing governing the
protected quantity."*

> ### UNDER THIS DECISION, CHOOSING A DIFFERENT SYMBOL MOVES THE PROTECTED
> ### QUANTITY BY NOTHING, BECAUSE THE TOLERANCE IS THAT QUANTITY. THE CRITERION's
> ### CROSS-SYMBOL SPREAD IS IDENTICALLY ZERO BY CONSTRUCTION.

**A CRITERION WHOSE TEST STATISTIC IS ZERO BY CONSTRUCTION TESTS NOTHING.** It
cannot fire, and its not firing carries no information, because there is no state
of the world in which it would have fired. **That is the definition of
inapplicable and it is not the same as satisfied.**

**THE QUESTION THE APPARATUS ASKED DOES NOT ARISE.** It asked whether the
tolerance has authority over the cross-symbol distribution of the protected
quantity. When the tolerance **is** that quantity, the question has no content.

### 3.4 THE FALSE SUMMARY, NAMED SO IT CANNOT BE WRITTEN LATER

> **A SUMMARY REPORTING "UNIFORMITY ACHIEVED" WOULD BE FALSE IN A WAY THAT
> MATTERS.**

It would suggest **a source of variation was removed**. What happened is that
**the instrument that measured it no longer applies**, and the variation moved to
the widths where no instrument is currently pointed. A reader who takes
"uniformity achieved" at face value would conclude the cross-symbol problem is
solved, when in fact it has been relocated to a quantity nothing has yet measured
and to which §6.1 owes a derivation.

**THE SAME PROHIBITION APPLIES TO REPORTING THE CRITERION'S RATIO AS FAVOURABLE.**
A ratio of zero against a firing level of one is not a wide margin; it is a
degenerate statistic. **Reporting it as a margin would be the false summary in
numerical dress.**

### 3.5 WHAT THE APPARATUS IS STILL GOOD FOR

**ITS VERDICT AND ITS MEASUREMENTS: NOTHING GOING FORWARD.** They answer a
question that no longer arises. §5 records their status.

**ITS CONSTRUCTION: AVAILABLE, AND POINTED AT A DIFFERENT QUANTITY.** Two things
built for the retired question are methods rather than results, and the symbol
question has moved to the widths where a method is now needed:

- **The commit-order discipline** — a criterion committed in its own commit before
  any number it would judge exists.
- **The discrimination requirement** — report 34 §3.4's demonstration that a
  flatness test must be shown to return the opposite answer on a case that really
  is flat, or its answer is worthless.

**THEY ARE OFFERED TO `docs/design/04_1c_pre_commitments.md` AND NEITHER IS
ADOPTED HERE.** Whether the width distribution warrants a criterion at all, and
what that criterion would be, are that document's questions. **This document
adopts no criterion** (§7).

---

## 4. THE COUNTER-ARGUMENT, STATED AND ANSWERED

### 4.1 THE ARGUMENT AGAINST

**UNDER THE RETIRED FORM THE CONSTRAINT CONTAINED NO VALIDATED TERM AT ALL.** Its
numerator was unvalidated cost and its denominator was pure price geometry. **A
change in the taker fee could not move the required floor by any amount.**

**UNDER THIS FORM THE RISK UNIT CONTAINS THE VALIDATED FEES.** A published fee
schedule change moves the risk unit, therefore moves the ratio, therefore moves
the required floor — **even though nothing unvalidated has changed.**

This is a serious objection. `docs/design/04_1a_denomination_amendment_1.md` §4,
ground (4), rests on exactly the distinction it draws: *"A fee schedule change is
an observable event, discoverable by re-reading a published schedule — not a
model error the constraint exists to bound."*

### 4.2 THE ANSWER, ON THE MERITS

**THE QUESTION IS NOT WHETHER THE FLOOR MOVES. IT IS WHETHER THE PROTECTED
QUANTITY MOVES.** If it does, the floor moving is the constraint working.

**IT DOES.** 4.1b §3.2 defines the protected quantity as the fraction of the risk
unit determined by estimate, and adds what that fraction is for:

> **AND IT IS THE AMPLIFICATION FACTOR ON ERROR IN THAT ESTIMATE. The larger the
> cost share, the more a proportional error in the cost model displaces the risk
> unit the standing rule fixes at $20.**

**AMPLIFICATION IS A RATIO, AND A RATIO MOVES WHEN EITHER SIDE MOVES.** If the
taker fee rises, the risk unit grows while the unvalidated sum does not. The same
proportional error in the haircut then displaces a **smaller fraction** of the
risk unit. **The exposure the constraint exists to bound is genuinely lower, and
it is lower for a reason that has nothing to do with the haircut.**

> ### THIS DOCUMENT ADOPTS THAT ANSWER: THE FLOOR MOVING ON A VALIDATED FEE
> ### CHANGE IS THE CONSTRAINT WORKING, NOT THE CONSTRAINT BEING CONTAMINATED.

**AND IT FOLLOWS FROM THE RATIONALE ALREADY COMMITTED RATHER THAN FROM A NEW
ONE.** 4.1b §3.1 explicitly **rejected** the exposure reading — that the
constraint bounds how much cost is paid — in favour of the reliability reading.
Under the exposure reading a fee change would be a contamination, because fees are
cost. Under the reliability reading it is a genuine change in reliability. **The
answer is entailed by a choice made at 4.1b, not made here.**

### 4.3 THE OPPOSITE VIEW IS AVAILABLE, AND THIS IS WHAT IT IMPLIES

**A READER MAY HOLD THAT THE CONSTRAINED QUANTITY SHOULD DEPEND ONLY ON
UNVALIDATED INPUTS** — that a constraint on model error should be invariant to
anything the venue publishes. That view is coherent and it is not dismissed here.

**WHAT IT IMPLIES, STATED PLAINLY:**

- **The geometric denominator would be retained**, and with it the proxy: the
  constraint would bind one quantity while the rationale protects another, with
  the gap varying by symbol and by width.
- **4.1b §3.2 would have to be rewritten**, because it defines the protected
  quantity as a share of the risk unit. The rationale and the constraint cannot
  both stand as written under the opposite view.
- **The entire non-uniformity apparatus would remain necessary**, because the gap
  it exists to police would remain.

**THE CHOICE IS THEREFORE BETWEEN A CONSTRAINT INVARIANT TO PUBLISHED RATES AND A
CONSTRAINT IDENTICAL TO ITS RATIONALE. THIS DOCUMENT TAKES THE SECOND.**

### 4.4 A COST OF THE ADOPTED VIEW, NOT ARGUED AWAY

**THE REQUIRED FLOOR IS NOW A FUNCTION OF A PUBLISHED FEE SCHEDULE.** If Bitget
changes its taker or maker rates, the floor must be re-derived. Under the retired
form it need not have been. **That is a standing maintenance obligation created by
this decision**, it is recorded here rather than discovered at the moment it
binds, and it is routed to §6.1 to state as a condition of its result.

### 4.5 THE SELF-REFERENTIAL DENOMINATOR — NAMED AS OWED, NOT ATTEMPTED

> ### THE RISK UNIT DEPENDS ON THE STOP WIDTH, AND THE STOP WIDTH IS WHAT THE
> ### FLOOR SETS. THE CONSTRAINT's DENOMINATOR IS NOW A FUNCTION OF THE QUANTITY
> ### BEING SOLVED FOR.

Under the retired form the denominator was the stop distance, which is the
solved-for quantity directly. Under this form it is the stop distance **plus
cost terms**, some of which themselves depend on the stop price.

**WHETHER THAT YIELDS A CLOSED FORM, A FIXED POINT REQUIRING ITERATION, OR NO
SOLUTION IN SOME REGION OF THE TOLERANCE RANGE IS THE DERIVATION's QUESTION.**

**IT IS NOT ATTEMPTED HERE AND IT IS NOT ASSUMED TO RESOLVE CLEANLY.** No claim is
made that a closed form exists. `docs/design/04_0_decision_rule.md` §8 already
provides for the case where one does not: *"a numerical solution over a stated
grid of tolerance values is acceptable, provided the grid is committed before it
is solved and the solution method is reported"*, and states that
**non-linearity is not a failure but a solver choice.** That provision is invoked
in advance so that its use later is not a concession made under pressure.

**AND THE POSSIBILITY OF NO SOLUTION IN SOME REGION IS NOT TREATED AS A DEFECT OF
THIS DECISION.** If some tolerances turn out to be unachievable at any width, that
is a fact about the constraint that this form makes visible and the retired form
concealed behind a proxy. **A finding of that kind would be information, and §6.1
must report it rather than restrict the grid until it disappears.**

---

## 5. THE BLAST RADIUS

**EVERY ARTIFACT BELOW IS SUPERSEDED AS GOVERNING AND NONE IS FALSIFIED. EACH
REMAINS THE CORRECT ANSWER TO THE QUESTION IT WAS ASKED.**

### 5.1 REPORT 33's CLOSED FORM

**STILL:** the correct required-floor relation under the unvalidated numerator over
the **stop distance**, with its derived direction split, its pole, its committed
grid, and its verification against the engine's own denominator.

**NO LONGER:** the relation any width is read from. Its denominator is the retired
one. **Superseded as governing, not falsified.**

**AND ITS DIRECTION SPLIT AND POLE DO NOT CARRY OVER.** They were properties of a
particular denominator. §6.1 requires both to be re-established.

### 5.2 REPORT 34's SHARES, RATIOS AND VERDICT

**STILL:** the correct shares of path one's risk unit at report 33's floor, with an
exactly-zero decomposition residual, and a flatness test demonstrated to
discriminate. The cross-symbol figures it reported — running from 1.033752 to
1.113870 across its grid, against 1.5455 flat under the prior denomination — remain
correct **facts about the forms they were measured under**, and are quoted here as
such.

**NO LONGER:** measurements of the governing quantity. Path-and-scope §5.4 already
recorded them as understated relative to the governing definition; this decision
additionally makes the quantity they measure one the constraint no longer binds.
**Superseded as governing, not falsified.**

### 5.3 THE NON-UNIFORMITY THRESHOLD AND CHECK

**STILL:** a correctly constructed criterion, committed in its own commit before its
numbers existed, correctly applied, and correctly reported as not firing under the
form it was built for. `docs/design/04_1a_denomination_amendment_1.md` §7 already
recorded its one construction defect as instance (40), and that record stands.

**NO LONGER:** applicable at all. §3.3 gives the reason: its test statistic is zero
by construction under this decision. **This is the one item whose retirement is
not a relabelling** — the others answer a superseded question, while this one
answers a question that no longer exists. **Superseded as governing, not
falsified.**

### 5.4 THIS IS THE SECOND DENOMINATION CHANGE IN SUB-POINT 4.1, AND THE HONEST ANSWER ON BOTH

**THE FIRST**, at `docs/design/04_1a_denomination_amendment_1.md`, narrowed the
numerator. **It was made on a measured structural finding**: that the parameter had
zero authority over the cross-symbol distribution of the protected quantity, the
ratio being constant across the whole committed grid.

**THIS ONE** changes the denominator. **It was made on a distinction between two
denominators that the chain had conflated** — the risk unit and the stop distance —
surfaced at `docs/design/04_1c_path_and_scope.md` §1.3.

> ### COULD EITHER HAVE BEEN MADE EARLIER ON INFORMATION AVAILABLE AT THE TIME?

**THE FIRST: PARTLY, AND MORE THAN AMENDMENT 1 ALLOWED.** That document's §2.3
states the amendment was *"made on evidence that did not exist when the decision
was made"*. **The measurement did not exist. The structural fact did.** The
invariance of the cross-symbol ratio is a property of report 32's closed form, and
that closed form was committed before 4.1a was written. **It could have been read
off the algebra rather than waiting to be measured.** Measuring it was not wrong —
it produced certainty and a demonstrated instrument — but the claim that the
evidence did not exist is too strong, and it is corrected here rather than left
standing.

**THIS ONE: YES, PLAINLY, AND THE PLACE IS IDENTIFIABLE.**
`docs/design/04_1a_denomination_amendment_1.md` §3.1 states, in a single sentence:
*"4.1b §3.2 names the protected quantity as a share of the risk unit; the
constrained ratio is taken over the stop distance, exactly as the prior ratio
was."* **Both facts are written down, adjacent, and the difference between them is
not noticed.** The same sentence concludes that the relationship between the two
*"is therefore unchanged in form"* — which is true and irrelevant, because the
relationship was already a gap.

**NO MEASUREMENT WAS NEEDED. NO LATER ARTIFACT SUPPLIED ANYTHING THAT THE
DOCUMENT DID NOT ALREADY CONTAIN.** Reports 33, 34 and 35 clarified the picture and
none of them was necessary to see this. **The decision is nine steps later than the
information was.**

**THAT IS STATED WITHOUT MITIGATION.** The commit-order discipline is intact — this
change is being made before its widths exist, as the first was — and that is the
property the discipline guarantees. **It does not guarantee that a decision is made
as early as it could have been, and here it was not.**

### 5.5 THE LEDGER

#### THE TOTAL, READ

**`docs/design/04_1c_path_and_scope.md` §4.3 states "41 + 1 = 42".** **The total
read is 42**, so the instance below takes **(43)**.

#### INSTANCE (43)

**A SPECIFICATION DOCUMENT SET A CONSTRAINT's DENOMINATOR TO ONE QUANTITY AND
CITED, IN THE SAME SENTENCE, A RATIONALE DENOMINATED IN A DIFFERENT ONE — AND
CONCLUDED THAT THE RELATIONSHIP BETWEEN THEM WAS UNCHANGED.**

`docs/design/04_1a_denomination_amendment_1.md` §3.1. **The conclusion is true of
the form of the relationship and silent about its content**, and it was read as
establishing that binding the one bound the other. **It did not, and the gap
between them is what the entire non-uniformity apparatus was subsequently built to
police.**

**IT IS THE RECURRING CLASS:** a criterion — here a constraint's own definition —
written from a mental model of a quantity rather than from what the quantity is.
**SUB-CLASS: the class applied to a specification rather than to a numerical
threshold or a decision criterion**, alongside instance (40), which applied it to a
decision criterion.

**THE DEFECT IS NOT CORRECTED BY EDIT.** Amendment 1 is not amended and §3.1's
sentence stands as written; this document supersedes the denominator it set.

#### THE TOTAL

**42 + 1 = 43.**

**No earlier instance is renumbered or recounted**, and the ledger remains
contiguous from (1) to (43).

---

## 6. WHAT IS OWED NEXT, AND TO WHOM

### 6.1 THE DERIVATION — REPORT 36, FILED UNDER `docs/handoff/`

**A SEPARATE STEP WITH ITS OWN COMMIT, BEFORE ANY WIDTH OR LEVEL IS EVALUATED.**

**IT IS FILED UNDER `docs/handoff/` AND NOT UNDER `docs/design/`**, on report 33's
own stated ground: *"It is a derivation and a measurement, not a decision. Design
documents join the frozen specification on commit ... a derivation does not, and
filing it under `docs/design/` would enrol a measurement in the specification."*

**WHAT IT MUST PRODUCE:**

- **The required floor width as a function of the tolerance under the risk-unit
  denominator**, with funding on both sides, **per symbol and per direction.**
- **Derived from the implementation and verified against
  `portfolio.size_position`**, which path-and-scope §6.1 already establishes as the
  object to verify against. Verifying against the algebra in this document's prose
  would verify nothing.
- **THE DIRECTION SPLIT AND ANY POLE ESTABLISHED RATHER THAN CARRIED OVER.**
  Report 33's split and pole were properties of the stop-distance denominator.
  Whether either arises here is a question to be answered. **Neither is inherited.**
- **THE SELF-REFERENTIAL DENOMINATOR OF §4.5 RESOLVED OR REPORTED AS
  UNRESOLVABLE** — closed form, fixed point, or no solution in some region —
  **with the region reported rather than excluded from the grid.**
- **THE FEE-SCHEDULE DEPENDENCE OF §4.4 STATED AS A CONDITION OF ITS RESULT**, so
  that a future rate change is known to invalidate the widths rather than
  discovered to have done so.

### 6.2 `docs/design/04_1c_pre_commitments.md` — AFTER IT

**IT OWES:** the reject-over-clip precedence — what happens when a required floor
exceeds the frozen cap, which report 34 §5.3 routed forward and which no document
has settled; and the decision criterion, if §3.5's relocated question warrants one,
committed in its own commit before any quantity it would judge exists. **It also
owes the magnitude threshold** `docs/handoff/31_point_5_closing.md` §5.3 records as
outstanding.

### 6.3 `docs/design/04_1c_proper.md` — LAST

**IT OWES:** the tolerance's level, the widths, the dominance check named at
`docs/design/04_1a_denomination.md` §4.1, and kill condition (d)'s disposition.
**It cannot proceed until §6.1 and §6.2 exist**, because every one of those either
is a width or depends on one.

---

## 7. WHAT THIS DOCUMENT DOES NOT DO

**IT SETS NO TOLERANCE VALUE.** Owed by `docs/design/04_1c_proper.md`.

**IT DERIVES NO CLOSED FORM, RECOMPUTES NO SHARE AND STATES NO WIDTH.** Owed by
report 36, §6.1. No width, tolerance value or share is stated as governing anywhere
in this document.

**IT DOES NOT SETTLE FLOOR-VERSUS-CAP PRECEDENCE.** Owed by
`docs/design/04_1c_pre_commitments.md`.

**IT ADOPTS NO DECISION CRITERION.** Owed by
`docs/design/04_1c_pre_commitments.md`. §3.5 offers two methods to it and adopts
neither.

**IT DOES NOT DISPOSE OF KILL CONDITION (d).** Owed by
`docs/design/04_1c_proper.md`, which `docs/handoff/31_point_5_closing.md` §9(c)
records as additionally needing §5.9's level decision.

**IT SETS NO MAGNITUDE THRESHOLD.** Owed by
`docs/design/04_1c_pre_commitments.md`.

---

## 8. CHANGE DISCIPLINE

**A CHANGE TO THIS DECISION IS A NEW DOCUMENT WITH ITS OWN COMMIT AND AN EXPLICIT
STATEMENT OF WHAT CHANGED AND WHY — NEVER A SILENT EDIT.** It would be
`docs/design/04_1c_denominator_choice_amendment_1.md`.

**A SILENT EDIT IS A CONTAMINATION EVENT.**

> **THIS DOCUMENT'S VALUE RESTS ON ITS COMMIT PRECEDING THE DERIVATION OF ANY
> WIDTH UNDER THE DENOMINATOR IT COMMITS.**

**AND THE DIRECTION OF CONVENIENCE IS NOT KNOWN HERE, WHICH IS ITSELF WORTH
RECORDING.** Amendment 1 §5.3 and path-and-scope §8 both stated a known direction
in advance, so that a reader could weigh the decision against it. **This decision
has no such statement, because §3.2's relocation of the symbol structure into the
widths has no known sign at this commit** — the widths under this denominator do
not exist. **That is a reason the commit order matters more here, not less: there
is no advance disclosure to check the result against, so only the order
distinguishes a decision from a selection.**

---

**Committed alone, before any width under the risk-unit denominator has been
derived. One denominator retired and one committed, on the ground that the
constraint and its rationale become the same object; one seductive reading
foreclosed in the document rather than left to a later summary; one
counter-argument answered on the merits with the opposite view stated and its
implications named; one self-referential denominator named as owed and not assumed
to resolve; three artifacts superseded as governing and none falsified; one
ledger instance logged and one earlier claim about the availability of evidence
corrected. No width is stated, no closed form is derived, and no tolerance value is
committed.**
