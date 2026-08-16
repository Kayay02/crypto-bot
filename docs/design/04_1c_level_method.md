# THE LEVEL-SETTING METHOD — ONE ATTEMPT

**Point 4, sub-point 4.1c. One method proposed, tested, and reported. One
obligation disposed of. No level is stated.**

## 0. THE SCOPE LIMIT, STATED FIRST

> ### THIS DOCUMENT STATES NO TOLERANCE VALUE, NAMES NO SUB-INTERVAL AS PREFERRED,
> ### AND STATES NO FLOOR WIDTH AS GOVERNING.

**IF A METHOD IS FOUND, IT IS COMMITTED HERE AND APPLIED IN A LATER COMMIT.** That
separation is required by `docs/design/04_1c_pre_commitments.md` §4.3(e), and it
is the reason this document exists separately from `docs/design/04_1c_proper.md`.

**No requirement given to this document was read as asking for a level.** None
appeared to.

---

## 1. WHAT THIS DOCUMENT IS, AND WHAT SUCCESS WOULD LOOK LIKE

**A PRE-REGISTRATION, FROZEN ON COMMIT.** Made before any tolerance value is
stated and before any performance figure exists for this thesis. It joins the
frozen specification on its commit.

### 1.1 THE SUCCESS CONDITION, STATED BEFORE THE ATTEMPT

> ### A METHOD SUCCEEDS IF AND ONLY IF IT SURVIVES ALL FIVE DISQUALIFYING
> ### PROPERTIES AT `docs/design/04_1c_pre_commitments.md` §4.3, TESTED ONE AT A
> ### TIME AND IN WRITING.

It is stated here, ahead of §2, so that the attempt is not graded after the fact.
A success condition written after the result is a description of the result.

**SURVIVING FOUR IS NOT SUCCESS.** §4.3(d) is named in that document as the
property distinguishing a method from an argument for a conclusion already
reached, and a method failing any one property is disqualified.

### 1.2 THE SINGLE-ATTEMPT RULE, AND ITS REASON

> ### ONE METHOD IS PROPOSED AND TESTED. IF IT FAILS, THE FAILURE IS REPORTED AND
> ### THIS DOCUMENT PROCEEDS TO §4. IT IS NOT REVISED UNTIL IT PASSES.

**THE REASON, STATED PLAINLY.** Iterating a method against the standard until
something clears it is fitting the method to the wish for a method. What emerges
from that process has one demonstrated property — that it survived the test — and
no demonstrated connection to the question it claims to answer.

**IT IS THE SAME DEFECT AS ADJUSTING A STRATEGY UNTIL A BACKTEST LOOKS GOOD**, and
it is the defect this entire sub-point's commit-order discipline exists to
prevent. A standard that the candidate is edited against until it passes is not a
standard; it is a filter that reports only its own last iteration.

**SO THE METHOD BELOW IS THE ONE THE RATIONALE MOST NATURALLY SUGGESTS**, proposed
before it was tested, and it is reported as it stood when the test began.

---

## 2. THE ATTEMPT

### 2.1 THE QUESTION A METHOD MUST ANSWER

> ### WHAT SHARE OF THE RISK UNIT MAY REST ON AN ESTIMATE RATHER THAN ON
> ### OBSERVABLE PRICE GEOMETRY, AND WHY THAT SHARE RATHER THAN ANOTHER?

**IT IS NOT NARROWED.** It is not "what share is customary", not "what share
yields a workable floor", and not "what share is close to what was used before".
The second half of the question -- why that share rather than another -- carries
the whole weight, and a method answering only the first half has answered
nothing.

### 2.2 THE PRINCIPLE

The principle is taken from `docs/design/04_1b_tolerance_and_branch.md` §3.2,
which does not merely name the protected quantity but says what it is for:

> **AND IT IS THE AMPLIFICATION FACTOR ON ERROR IN THAT ESTIMATE. The larger the
> cost share, the more a proportional error in the cost model displaces the risk
> unit the standing rule fixes at $20.**

**THE PRINCIPLE THAT FOLLOWS:**

> ### THE TOLERANCE IS A BUDGET ON HOW FAR AN ERROR IN THE UNVALIDATED ESTIMATE
> ### MAY DISPLACE THE RISK UNIT THE STANDING RULE FIXES.

The constraint is not there to make costs small. `docs/design/04_1b_tolerance_and_branch.md`
§3.1 rejected that reading. It is there so that being wrong about the estimate
does not move the quantity the standing rule pins. **A bound on the share is a
bound on the amplification; a bound on the amplification is what a bound on the
displacement requires.**

### 2.3 THE METHOD THAT FOLLOWS FROM IT

**Two inputs, neither of them a width:**

- **A DISPLACEMENT BUDGET.** The maximum fraction by which the realised risk unit
  may depart from the nominal one on account of error in the unvalidated estimate.
- **A PLAUSIBLE PROPORTIONAL ERROR IN THAT ESTIMATE.** How wrong the unvalidated
  terms might be, as a fraction of themselves.

**THE METHOD:** the tolerance is set so that the plausible error, amplified by the
share, does not exceed the displacement budget. The share is the amplification
factor; the displacement is the error multiplied by the share; so the admitted
share is the budget divided by the plausible error.

**WHAT LEVEL-DETERMINING INPUT THE PRINCIPLE SUPPLIES.** It supplies the *form* of
the answer and the *identity* of the two quantities that determine it. It supplies
neither quantity. **That is stated here, before the test, rather than discovered
during it.**

**NO PROPERTY OF ANY FLOOR WIDTH ENTERS.** No width was consulted in constructing
this method, and report 36's curve was not opened while writing §2.

---

## 3. THE TEST, PROPERTY BY PROPERTY

### 3.1 PROPERTY (a) — selection by reference to the implied floor widths

**VERDICT: SURVIVES.**

The method's two inputs are a displacement budget and an error bound. **Neither is
a width, neither is computed from a width, and neither becomes available by
looking at one.** The method would return the same answer if report 36 did not
exist.

**AND IT DOES NOT SMUGGLE A WIDTH IN THROUGH FAMILIARITY.** It makes no reference
to the retired 1.50% floor, to any stratum count, or to whether the implied widths
are comfortable.

### 3.2 PROPERTY (b) — selection by reference to a quantity not computable before the level is chosen

**VERDICT: DISQUALIFIED.**

**THE ERROR BOUND CANNOT BE COMPUTED.** `docs/handoff/31_point_5_closing.md` §5.2
records that the stop haircut IS the entire slippage-and-gap model, is a
placeholder rather than a venue-published figure, and **cannot be validated
against this data layer**, because `open` is synthesised and no bar's first
observed price exists at any resolution -- so a bar that opens beyond the stop is
invisible. Document 06 §9 lists it as the largest remaining unknown in the exit
model and routes it to Point 6's paper trading or to a data source this project
does not have.

> ### THE METHOD REQUIRES A BOUND ON HOW WRONG THE ESTIMATE MIGHT BE, AND THE
> ### PROJECT HAS COMMITTED THAT IT DOES NOT KNOW AND CANNOT PRESENTLY FIND OUT.

**TWO READINGS OF (b) EXIST AND THE VERDICT DOES NOT TURN ON WHICH IS TAKEN.**

- **THE LETTER OF (b)** disqualifies selection by reference to "any quantity that
  cannot be computed before the level is chosen". A quantity that cannot be
  computed at all cannot be computed before the level is chosen. **The error bound
  falls within it.**
- **THE ILLUSTRATION ATTACHED TO (b)** in that document is about circularity: "A
  method that needs the level in order to produce the input that justifies the
  level selects nothing." **This method is not circular.** The error bound does not
  depend on the level.

**THE LETTER IS APPLIED, BECAUSE THE LETTER IS WHAT WAS COMMITTED** and the
illustration was an illustration. **But the disposition is the same under either
reading**: a method whose input does not exist produces no level, whether it is
disqualified or merely inapplicable. **The interpretive question is recorded rather
than resolved in whichever direction would be convenient.**

**AND THE OBVIOUS REPAIR IS NAMED AND REFUSED.** The method could be rescued by
assuming an error bound -- picking a factor and proceeding. **That is precisely the
recurring defect this project's ledger tracks**: a numerical input written from a
mental model of a quantity rather than from its implementation or achievable
range. §1.2 forbids the revision independently. **Both reasons are stated so that
neither carries the refusal alone.**

### 3.3 PROPERTY (c) — not evaluable without access to the person who chose it

**VERDICT: SURVIVES, CONDITIONALLY, AND THE CONDITION IS STATED.**

**IF BOTH INPUTS ARE WRITTEN DOWN, A READER CAN EVALUATE THE METHOD.** The
arithmetic is inspectable, the principle is cited to a committed document, and a
reader who disagrees can say which input they would set differently and what
follows. **Judgement exposed in writing is not judgement exercised privately.**

**THE CONDITION:** the document applying the method must state both inputs
explicitly. A method applied with either input left implicit would fail (c), and
the failure would be invisible.

**A WEAKNESS IS RECORDED HERE THAT IS NOT (c)'s.** The method converts "choose a
tolerance" into "choose a displacement budget". That is one undetermined choice
replaced by another, one step removed from the constraint. **It is progress only if
the second choice is easier to argue than the first**, and this document does not
claim that it is. **It is recorded as a weakness rather than presented as a
solution**, and it is not the ground of any verdict above.

### 3.4 PROPERTY (d) — failing to state what would have made a different level correct

**VERDICT: SURVIVES.**

**THIS IS THE PROPERTY `docs/design/04_1c_pre_commitments.md` §4.3(d) NAMES AS
DECISIVE, AND THE METHOD ANSWERS IT DIRECTLY.**

A different level would have been correct if either input were different, and the
method says exactly how:

- **A LARGER DISPLACEMENT BUDGET ADMITS A LARGER SHARE.** If the project were
  willing to let the realised risk unit depart further from the nominal one on
  account of estimate error, more of the risk unit could rest on the estimate.
- **A LARGER PLAUSIBLE ERROR DEMANDS A SMALLER SHARE.** If the haircut might be
  wrong by more, less of the risk unit may depend on it at the same displacement
  budget.

**THAT IS A DISCRIMINATING ANSWER AND NOT A RATIONALISATION.** It names the
conditions under which the answer changes, before the answer exists, and it makes
the method falsifiable in the only sense available to a specification: a reader can
say the budget or the error bound is wrong, and the level moves.

**IT IS WORTH STATING THAT THE METHOD SURVIVES ITS HARDEST TEST**, because that is
what makes the failure at (b) informative rather than merely another dead end.

### 3.5 PROPERTY (e) — not committed in its own commit before the level it selects

**VERDICT: SURVIVES, BY CONSTRUCTION.**

The method is committed in this document, alone, and no level is stated here. Any
application is a later commit. **This document exists in order to satisfy (e), and
it would satisfy it whether or not the method had survived the other four.**

### 3.6 THE OVERALL VERDICT

> ### DISQUALIFIED, ON PROPERTY (b) ALONE.

**IT SURVIVES (a), (c), (d) AND (e). IT FAILS (b).**

**THE FAILURE IS NOT A DEFECT OF THE METHOD'S CONSTRUCTION.** The method answers
(d), the property named as decisive, and it is derived from a principle stated in a
committed document rather than assembled to pass a test. **It fails because one of
its two inputs is a quantity this project has recorded as unavailable.**

**WHAT THIS DOES AND DOES NOT ESTABLISH.** It establishes that this method does not
succeed now. **It does not establish that no method can succeed**, and §1.2's
single-attempt rule means this document is not entitled to that conclusion -- one
attempt is one attempt. **But the reason for the failure is a property of the
project's evidence rather than of the method's construction**, and any method that
bounds how much error can be tolerated will need to know how much error there might
be. **That is offered as an observation about the shape of the difficulty, not as a
proof, and a later document is free to find a method that does not need it.**

**ONE POSSIBILITY IS NAMED WITHOUT BEING PURSUED:** the input becomes available if
the haircut is ever measured, which `docs/handoff/31_point_5_closing.md` §5.2 routes
to Point 6's paper trading. **This method is therefore blocked rather than dead**,
and a later document may revive it on measured inputs. **Reviving it would not be a
revision of a failed method** under §1.2, because nothing about the method would
change -- only the availability of an input it already names.

---

## 4. THE METHOD IS DISQUALIFIED — BOTH ROUTES PREPARED, NEITHER CHOSEN

**§3.6's verdict is disqualified, so this section applies.**

> ### THIS DOCUMENT DOES NOT CHOOSE BETWEEN THE TWO ROUTES AT
> ### `docs/design/04_1c_pre_commitments.md` §4.4. THAT CHOICE BELONGS TO THE
> ### PROJECT OWNER AND THIS DOCUMENT SURFACES IT.

Both are prepared so that the choice is made against what each actually requires,
rather than against whichever is described first.

### 4.1 THE JUDGEMENT ROUTE — what a judgement record would have to contain

**FOUR THINGS, AND A RECORD MISSING ANY OF THEM IS NOT HONEST:**

- **WHAT WAS WEIGHED.** The considerations actually in play, including the ones
  that did not decide it. A record listing only the deciding consideration is a
  conclusion with a reason attached.
- **WHAT WOULD HAVE CHANGED IT.** Named specifically enough that a reader can
  check later whether that thing happened. This is §4.3(d)'s requirement carried
  over to judgement: **judgement that cannot say what would have changed it is
  indistinguishable from preference.**
- **WHO DECIDED.** By name or role, so the record has an author rather than a
  passive voice.
- **AN EXPLICIT STATEMENT THAT THE LEVEL IS NOT DERIVED.** In those words, in the
  document that states the level, and not in a footnote. A level presented as
  derived when it was chosen is the contamination this sub-point's entire
  commit-order discipline exists to prevent.

**AND TWO THINGS THIS DOCUMENT ADDS:**

- **IT MUST RECORD THAT §2's METHOD WAS ATTEMPTED AND FAILED AT (b)**, so the
  judgement is visibly a fallback rather than a first resort.
- **IT SHOULD RECORD THE DISPLACEMENT BUDGET THE CHOSEN LEVEL IMPLIES**, even
  though the level was not derived from one. That makes the judgement checkable
  against a measured haircut if Point 6 ever supplies one, converting an
  unfalsifiable choice into a deferred test.

**THE JUDGEMENT IS NOT EXERCISED HERE AND NO LEVEL IS NAMED.**

### 4.2 THE BRANCH C ROUTE — what reopening would require

**AN AMENDMENT TO `docs/design/04_1b_tolerance_and_branch.md` UNDER THAT
DOCUMENT'S OWN CHANGE DISCIPLINE**, as a new document with its own commit. **Not a
reinterpretation here**, and not a decision this document is entitled to make on
4.1b's behalf.

**WHAT THAT AMENDMENT WOULD HAVE TO ARGUE:**

- **THAT A CONSTRAINT WHOSE LEVEL CANNOT BE JUSTIFIED IS WORSE THAN NO
  CONSTRAINT** -- because it presents an unjustified number as a bound and confers
  the appearance of protection. **This is the substantive claim and it is not
  obvious.**
- **AGAINST 4.1b §4.1's STANDING GROUND**, which refused Branch C because retiring
  the constraint leaves the fraction of the risk unit resting on an unvalidated
  estimate **unbounded**, at exactly the point where
  `docs/handoff/31_point_5_closing.md` §5.2 records that estimate as the largest
  remaining unknown. **That ground does not weaken merely because a level is hard
  to justify**, and the amendment must engage it rather than note it.
- **WHAT THE STOP FLOOR RESTS ON INSTEAD.** With no tolerance there is no
  cost-derived floor, and the amendment must supply the floor an independent
  basis or state that the floor is set by the remaining mechanisms alone. **This
  document does not derive either and states no floor.**

### 4.3 WHICH ARTIFACTS EACH ROUTE MAKES UNNECESSARY

**STATED SO THE COST OF EACH IS VISIBLE RATHER THAN ASSUMED EQUAL.**

**UNDER THE JUDGEMENT ROUTE: NOTHING BECOMES UNNECESSARY.** Every committed
artifact in the 4.1 chain remains operative -- the denomination decisions, report
36's closed form, the admitted domain, the reject-over-clip precedence. The chain
carries a level whose provenance is judgement, and the rest stands as built.

**UNDER THE BRANCH C ROUTE, THE FOLLOWING BECOME UNNECESSARY AS GOVERNING**,
though none is falsified:

- **`docs/design/04_1a_denomination.md` and its amendment 1**, whose entire
  subject is which quantity a tolerance is denominated in. With no tolerance,
  there is nothing to denominate.
- **`docs/design/04_1c_path_and_scope.md` and `docs/design/04_1c_denominator_choice.md`**,
  for the same reason.
- **`docs/handoff/36_point_4_1c_risk_unit_derivation.md`'s closed form**, which
  maps a tolerance to a width. With no tolerance it maps nothing, though its
  achievable-range analysis remains a correct description of the ratio.
- **`docs/design/04_1c_pre_commitments.md` §2's admitted domain**, which is an
  interval of tolerances.
- **`docs/design/04_1c_pre_commitments.md` §3's population A**, the cost-protection
  rejection, which becomes vacuous. **Population B survives untouched**, being a
  volatility rejection independent of the tolerance and of cost accounting
  entirely.

> **THAT IS SIX ARTIFACTS AGAINST NONE, AND THE ASYMMETRY IS STATED RATHER THAN
> LEFT TO BE FELT.**

**AND IT IS EXPLICITLY NOT AN ARGUMENT FOR THE JUDGEMENT ROUTE.**
`docs/design/04_0_decision_rule.md` §8 commits that the cost of re-measuring is not
a consideration in a branch choice, and that a finding implying a large
re-measurement bill is a finding about the reports rather than an argument against
the finding. **The same principle applies to a specification bill.** The count is
given so the choice is informed, not so it is weighted.

---

## 5. THE DOMINANCE OBLIGATION, DISPOSED OF

### 5.1 WHAT WAS OWED, AND ON WHAT CONDITION

`docs/design/04_1a_denomination.md` §4.1 named it: **if 4.1c relies on the claim
that constraining the stop path bounds the other two** -- rather than merely on the
stop path being the right thing to constrain in its own terms -- **that dominance
must be verified across the widths in play, because it compares a rate multiplied
by a price at three different price levels.**

**THE OBLIGATION IS CONDITIONAL ON ITS ANTECEDENT.** So the question to settle is
whether 4.1c relies on that claim.

### 5.2 THE ARGUMENT

**FIRST, THE DENOMINATION HAS MOVED TWICE SINCE THAT OBLIGATION WAS WRITTEN.**
`docs/design/04_1c_path_and_scope.md` §2.1 moved the risk unit to path two's
denominator, and `docs/design/04_1c_denominator_choice.md` §2.1 made that
denominator the constraint's own. **The constraint now binds the unvalidated share
of the risk unit.**

**THE RISK UNIT IS A SIZING QUANTITY: ONE PER POSITION, NOT ONE PER EXIT PATH.** It
is computed at entry, from the entry price and the stop price, and it is what
divides the allocation into a quantity. **Every position has exactly one, decided
before any exit occurs and independent of which exit occurs.**

**SECOND, THE GROUND THE OBLIGATION QUALIFIED HAS BEEN SUPERSEDED.**
`docs/design/04_1a_denomination.md` §3.3 ground (2) argued that a constraint on the
most expensive path bounds the others, and thereby disposed of the candidates "one
constraint per path" and "the worse of the two". **It was an argument about which
PATH to denominate in.** The later denomination changes did not choose a different
path among the three; **they moved the denomination off the path question
entirely**, onto a quantity that exists once per position.

> ### 4.1c DOES NOT RELY ON THE DOMINANCE CLAIM, BECAUSE THERE ARE NO LONGER THREE
> ### CANDIDATE QUANTITIES FOR ONE TO DOMINATE. THE ANTECEDENT IS FALSE.

**THE OBLIGATION IS DISCHARGED AS MOOT.**

### 5.3 THE OBSERVATION THAT SURVIVES THE ARGUMENT, RECORDED SO IT IS NOT LOST

**THE THIRD FACT WEIGHED DOES NOT DISAPPEAR WITH THE OBLIGATION.** The stop
haircut is charged **only on a stop exit**. A position exiting at the target or at
the time exit was sized against a risk unit containing a term it never pays.

**THAT IS TRUE, AND IT IS NOT THE DOMINANCE QUESTION.** Dominance asked which of
three cost paths is largest. This asks whether a term provisioned at sizing time
should be provisioned when the exit that triggers it may not occur. **They are
different questions and answering the second was never owed by §4.1.**

**IT IS STRUCTURALLY IDENTICAL TO A PATTERN THE SPECIFICATION HAS ALREADY
ADOPTED.** `docs/design/06a_exit_resolution_spec_amendment_1.md` E7.1 charges
funding at the provisioned count in the sizing denominator with **no reconciliation
to the settlements actually crossed**, and states the cost openly: positions
exiting early are charged for something they did not incur. The ground was that the
risk unit must be decided at entry, because a unit that is revised after the fact is
not a unit.

**THE HAIRCUT FOLLOWS THE SAME PATTERN FOR THE SAME REASON.**

> **AND E7.1 DOES NOT DISPOSE OF IT AUTOMATICALLY. E7.1 GOVERNS FUNDING.** No
> committed document extends it to the haircut, and this document does not extend
> it either -- extending a rule by analogy is not the same as the rule applying.

**IT IS RECORDED HERE AND NOT MADE AN OBLIGATION**, because no committed document
owes it and this document is not entitled to create one on its own authority. **A
reader who holds that it should be an obligation now has it written down to point
at**, which is the whole reason for recording it.

---

## 6. WHAT THIS DOCUMENT DOES NOT DO

**IT STATES NO TOLERANCE VALUE, NO FLOOR WIDTH, AND NO SUB-INTERVAL.** Owed by
`docs/design/04_1c_proper.md`.

**IT DOES NOT DISPOSE OF KILL CONDITION (d).** Owed by
`docs/design/04_1c_proper.md`.

**IT SETS NO MAGNITUDE THRESHOLD.** Owed by `docs/design/04_1c_proper.md`. §2.3's
displacement budget is closely related to it and is **not** a substitute: the
threshold asks at what magnitude a breach of the standing risk rule stops being
tolerable, and this document sets no such magnitude.

**IT DOES NOT EXERCISE JUDGEMENT ON THE LEVEL.** §4.1 states what a judgement
record would need to contain and exercises none. Owed by
`docs/design/04_1c_proper.md`.

**IT DOES NOT CHOOSE BETWEEN §4's TWO ROUTES.** That choice belongs to the project
owner.

---

## 7. CHANGE DISCIPLINE, AND THE ERRATA INDEX

**A CHANGE TO THIS DOCUMENT IS A NEW DOCUMENT WITH ITS OWN COMMIT AND AN EXPLICIT
STATEMENT OF WHAT CHANGED AND WHY -- NEVER A SILENT EDIT.** It would be
`docs/design/04_1c_level_method_amendment_1.md`.

**A SILENT EDIT IS A CONTAMINATION EVENT.**

**AND ONE FORM OF CHANGE IS NAMED IN ADVANCE.** If a later document proposes a
second method, that is not an amendment to this one -- this document's result
stands as the record of one attempt and its outcome. **An amendment that revised
§2's method until it passed §3 would violate §1.2 and must say so if attempted.**

### 7.1 THE ERRATA INDEX

> ### THIS DOCUMENT MAKES NO CORRECTION TO ANY FROZEN ARTIFACT. NO ENTRY IS ADDED
> ### TO THE CONSOLIDATED INDEX AT `docs/design/04_1c_pre_commitments.md` §5.

**The two things that might be mistaken for corrections are neither:**

- **§3.2's reading of property (b)** is an interpretation applied to a committed
  clause whose letter and whose illustration differ in reach. **Nothing in that
  clause is stated to be wrong**, both readings are recorded, and the verdict does
  not turn on which is taken.
- **§5's disposition** discharges a conditional obligation by showing its
  antecedent false. **That is the obligation working as written**, not a correction
  to the document that wrote it.

**The index at `docs/design/04_1c_pre_commitments.md` §5 therefore stands at nine
entries, unchanged, and its next holder carries it forward as it is.**

---

## 8. THE LEDGER

**`docs/design/04_1c_denominator_choice.md` §5.5 states "42 + 1 = 43". The total
read is 43.**

**THIS DOCUMENT ADDS NO INSTANCE AND THE TOTAL IS UNCHANGED AT 43.**

**THE CANDIDATE WAS CONSIDERED AND DECLINED, AND THE REASONING IS GIVEN SO A
READER CAN DISAGREE.** Property (b)'s letter reaches further than its attached
illustration, which is a drafting looseness in a committed clause. **It is not
logged**, on the ground that the recurring class is a criterion written from a
mental model of a quantity's behaviour, and (b) is not a criterion about a
quantity -- it is a scope clause whose illustration is narrower than its rule.
**Applying the letter is the conservative reading and costs nothing here, since
§3.2 records that the verdict is identical either way.**

**A READER WHO HOLDS THAT A COMMITTED CLAUSE WHOSE LETTER AND ILLUSTRATION DIVERGE
IS ITSELF A LEDGER INSTANCE WOULD REACH 44 RATHER THAN 43.** That reading is
available and is not obviously wrong. The call made here is the one stated above,
following the precedent at `docs/design/04_1a_denomination.md` §5, which named its
own close call and the total the alternative reading would give.

---

**Committed alone, before any tolerance value is stated. One method proposed from
a principle in a committed document and tested against five properties one at a
time; it survives four including the one named as decisive, and is disqualified on
the fifth because an input it needs is a quantity this project has recorded as
unavailable. The obvious repair is named and refused on two independent grounds.
Both fallback routes are prepared with their costs stated and neither is chosen.
One dominance obligation is discharged as moot, with the observation that survived
the argument recorded without being converted into an obligation. No level is
stated, no width is stated, no sub-interval is preferred, and the ledger is
unchanged at 43.**
