# THE PATH AND SCOPE DECISION

**Point 4, sub-point 4.1c, preparatory. Two decisions are made. Nothing is
derived.**

## 0. THE SCOPE LIMIT, STATED FIRST

> ### THIS DOCUMENT DECIDES. IT DERIVES NO CLOSED FORM, RECOMPUTES NO SHARE, AND
> ### STATES NO WIDTH OR TOLERANCE VALUE.

`docs/design/04_0_decision_rule.md` §8 requires that **which `c` the constraint is
denominated in is a specification decision**, made *"in its own commit, on stated
grounds, BEFORE the corresponding floor widths are evaluated"*, and states that
selecting the cost term after the candidate widths are visible is **specifically
forbidden**.

**THE EXPOSURE IS LARGER HERE THAN AT EITHER PRIOR DENOMINATION DECISION.** This
one supersedes the governing status of four committed derivations at once (§5).
A decision of that reach, made after its widths existed, would be
indistinguishable from a decision made to reach them.

**No requirement given to this document was read as asking for the revised closed
form.** None appeared to. §6 records where it is owed.

---

## 1. WHAT THIS DOCUMENT IS

**A PRE-REGISTRATION, FROZEN ON COMMIT.** Made **before any quantity under the
revised risk unit has been derived**, and **before any performance figure exists
for this thesis**. It joins the frozen specification on its commit, per
`docs/design/04_0_divergence_disposition_amendment_2.md` §2.

**IT AMENDS THE DENOMINATION COMMITTED AT `docs/design/04_1a_denomination.md`, AS
AMENDED AT `docs/design/04_1a_denomination_amendment_1.md`**, under those
documents' change discipline. **Neither is edited.** Amendment 1 §8 names
`04_1a_denomination_amendment_2.md` as the form a further change to *that* chain
would take; this document is filed at 4.1c instead because it is the first of the
three documents 4.1c owes (§6.3) and because it decides a question — which risk
unit — that 4.1a never reached.

### 1.1 PRECEDENCE

- **On which risk unit the constraint's protected quantity is a share of, and on
  funding's membership in the unvalidated set, this document governs.**
- **4.1a as amended governs on everything else it decided**, including that the
  constrained numerator is the unvalidated terms' contribution and that the
  constrained ratio is taken over the stop distance.

### 1.2 WHAT IS NOT REOPENED

**`docs/design/04_1b_tolerance_and_branch.md`'s RATIONALE AND ITS BRANCH B CHOICE
STAND UNCHANGED.** The constraint still exists, and what it protects is still
*"how much of the risk unit rests on an unvalidated estimate"* (4.1b §3.5).

> **THIS CHANGES WHICH RISK UNIT THE CONSTRAINT IS A SHARE OF. IT DOES NOT CHANGE
> WHAT THE CONSTRAINT IS FOR.**

### 1.3 ONE DENOMINATOR CHANGES AND ONE DOES NOT, AND THE DIFFERENCE IS STATED HERE RATHER THAN LEFT TO BE INFERRED

**Two distinct denominators are in play in the frozen chain and this document
touches only one of them.**

- **THE RISK UNIT** — the per-unit all-in loss at the stop. 4.1b §3.2 defines the
  protected quantity as a share of it and names it *"the stop distance plus the
  stop-path cost"*. **This is what §2 re-decides.**
- **THE CONSTRAINED RATIO'S DENOMINATOR** — the stop distance `s`, per amendment
  1 §3.1. **This is unchanged, and not by omission.** Funding is a cost term and
  not a geometry term: the distance from entry to stop is the same number on both
  paths. There is nothing about `s` for this decision to move.

**§3's decision nonetheless reaches the constrained ratio**, because it adds a
term to that ratio's **numerator**. The two effects are separate and §6's
re-derivation owes both.

---

## 2. THE DECISION ON THE PATH

### 2.1 THE DECISION

> ### THE CONSTRAINT IS DENOMINATED AGAINST PATH TWO's RISK UNIT: THE DENOMINATOR
> ### `portfolio.size_position` ASSEMBLES — PATH ONE's FIVE TERMS PLUS THE
> ### PER-UNIT FUNDING TERM.

Stated precisely, and **not solved for a width**:

    risk unit = the denominator at `src/engine/portfolio.py:298-299`, being
                `sizing.per_unit_denominator(...)` plus `funding_pu`, where
                `funding_pu` is `portfolio.funding_per_unit` at
                `src/engine/portfolio.py:187` -- the entry price multiplied by
                the funding rate and by the settlement count

**PATH ONE IS RETIRED FROM THE DENOMINATION.** It remains in the code, remains
what `sizing.size` computes, and remains what reports 28, 32, 33 and 34 measured.
It no longer defines the risk unit the constraint's protected quantity is a share
of.

### 2.2 THE GROUND: EXECUTION FIDELITY, NOT PREFERENCE

**PATH TWO IS THE DENOMINATOR THE EXECUTING POSITION SIZES ON.**
`docs/handoff/35_point_4_1c_denominator_audit.md` §2.2 establishes which path is
used where: path one by the sizing layer and by the measurement chain, path two by
`portfolio.size_position` — the execution path, and *"by nothing else"*. §2.5 of
the same report states the consequence: path one *"is not the denominator the
executing position sizes on"*, and report 34 §3 *"reports shares of a risk unit
`portfolio.size_position` does not use"*.

> **A CONSTRAINT BOUNDING A SHARE OF PATH ONE BOUNDS A SHARE OF A QUANTITY THE
> EXCHANGE-FACING SIZING DOES NOT USE.**

That is the whole ground and it is not a preference between two defensible
objects. The standing rule at `docs/design/00_standing_brief.md` §2 fixes risk per
trade *"enforced after fees and estimated slippage"*, and it is enforced by
whatever denominator actually sizes the order. **The constraint protects the
reliability of the risk unit (4.1b §3.5); the risk unit it must protect is the one
the order is sized by.**

**THE RE-MEASUREMENT BILL IS NOT A CONSIDERATION, AND THAT WAS PRE-COMMITTED.**
`docs/design/04_0_decision_rule.md` §8 states the standing principle —
*"EXECUTION REALITY OVER MEASUREMENT CONVENIENCE"* — and that *"THE COST OF
RE-MEASURING IS NOT A CONSIDERATION IN THE BRANCH CHOICE"*, adding that a finding
implying a large re-measurement bill *"is a finding about the reports and not an
argument against the derivation"*. **That principle was committed before this bill
was known. It is invoked here, not invented here.**

### 2.3 WHAT THIS DOES NOT CLAIM

**IT DOES NOT CLAIM PATH ONE IS WRONG AS AN OBJECT.** It is the correct all-in
per-unit loss at the stop for a position sized without a funding provision, and
`src/engine/costs.py:336` computes it correctly.

**IT DOES NOT CLAIM REPORTS 28, 32, 33 OR 34 WERE INCORRECTLY PERFORMED.** Each
measured what it said it measured, against the denominator it named, with the
verification it reported. Report 32's residual of 5.662e-15 against
`costs.position_size` stands; report 33's revised closed form stands as a relation
over path one; report 34's solve residual of 3.761e-15 and its exactly-zero
decomposition residual stand.

> **WHAT CHANGES IS WHICH MEASUREMENT GOVERNS, NOT WHETHER ANY OF THEM WAS
> CORRECT.**

### 2.4 THE COST OF THIS DECISION, UNSOFTENED

**THE CONSTRAINT'S DENOMINATOR NOW CONTAINS A TERM THAT CANNOT BE VALIDATED OVER
THE MEASUREMENT WINDOW.** `src/risk/exit_spec.py:118` records the funding rate as
*"AN ASSUMPTION, NOT A MEASUREMENT"* on the ground that available funding history
covers roughly 90 days against a three-year window. Amendment 1 §5.1 already
recorded that the constrained numerator rests on a single placeholder; this
decision puts a second unmeasured quantity into the denominator as well.

**THAT IS A REAL COST AND IT IS NOT ARGUED AWAY.** The reply is that the term is
charged on every executing position whether or not the constraint counts it, so
excluding it does not remove the exposure — it removes only the constraint's
sight of it. **That is a reason to accept the cost, not a reason to deny it is
one.**

---

## 3. THE DECISION ON FUNDING's MEMBERSHIP IN THE NUMERATOR

### 3.1 THE DECISION

> ### FUNDING IS A MEMBER OF THE UNVALIDATED SET. IT ENTERS THE CONSTRAINED
> ### NUMERATOR AS WELL AS THE DENOMINATOR.

### 3.2 THE GROUND, FROM THE AXIOM

`docs/handoff/34_point_4_1a_non_uniformity_rerun.md` §1 states the membership
axiom: **a cost term is unvalidated if its magnitude is not fixed by contract or
by the venue's published fee schedule, but is instead estimated, assumed or
carried over from another source.**

**FUNDING SATISFIES IT.** The rate floats at the venue and is not on a published
fee schedule; the model holds it at an assumed constant, `0.0001` at
`src/risk/exit_spec.py:115`, which document 06 records as **an assumption, not a
measurement**. The settlement count is derived from the frozen time-exit rule
rather than assumed, but **a term whose rate is assumed is an assumed term.**

**THE AXIOM WAS COMMITTED BEFORE THIS APPLICATION OF IT.** Report 34 §1.3 applied
it to funding, reached the same membership, and declined to act on it because
acting would have required a cost model that report did not govern. **The
membership is not newly asserted here; the authority to act on it is what this
document supplies.**

### 3.3 THE CONSISTENCY ARGUMENT

**A TERM CANNOT BE UNVALIDATED IN THE DENOMINATOR AND NOT IN THE NUMERATOR.**

Excluding funding from the numerator while including it in the denominator would
bound the share of unvalidated cost using a denominator that **contains
unvalidated cost it does not count**. The resulting quantity is a share of
nothing: its numerator and its denominator would disagree about what the
unvalidated set is.

> **THE TWO DECISIONS IN THIS DOCUMENT ARE ONE DECISION. TAKING §2 WITHOUT §3
> WOULD PRODUCE AN INCOHERENT RATIO, AND TAKING §3 WITHOUT §2 WOULD PUT A TERM IN
> THE NUMERATOR THAT THE DENOMINATOR DOES NOT CONTAIN.**

---

## 4. THE DIRECTION THE FIGURES MOVE, AND THE LEDGER INSTANCE BEHIND IT

### 4.1 THE ALGEBRA, STATED AND NOT COMPUTED

Writing `U` for the unvalidated sum, `D` for path one's denominator and `F` for
the per-unit funding term, following
`docs/handoff/35_point_4_1c_denominator_audit.md` §2.5:

- **Funding in the denominator alone:** the share becomes `U / (D + F)`, which is
  **strictly less** than `U / D`.
- **Funding in both:** the share becomes `(U + F) / (D + F)`, which **exceeds**
  `U / D` whenever `D` exceeds `U`. **`U` is a proper part of `D` and the price
  move is strictly positive, so `D` exceeds `U` always.**

### 4.2 THE CONSEQUENCE OF §3's DECISION

**THE SECOND BRANCH IS THE ONE TAKEN.**

> ### REPORT 34 §3's SHARES ARE UNDERSTATED RELATIVE TO THE GOVERNING DEFINITION.

**THE MAGNITUDE IS NOT COMPUTED HERE**, is not estimated, and is not bounded. It
is owed to the re-derivation named at §6.1. **The direction follows from the
inequality above and from nothing else.**

### 4.3 THE LEDGER

#### THE TOTAL, READ

**`docs/design/04_1a_denomination_amendment_1.md` §7 states "39 + 2 = 41".** **The
total read is 41**, so the instance below takes **(42)**.

#### INSTANCE (42)

**A DIRECTIONAL CLAIM ABOUT WHERE FOLDING FUNDING IN WOULD MOVE THE CROSS-SYMBOL
RATIO — TOWARD UNITY — ASSERTED FROM A MENTAL MODEL OF THE ALGEBRA RATHER THAN
FROM THE ALGEBRA.**

It was made in the collaboration channel. **The direction is not determinate
without the numerator decision**, which
`docs/handoff/35_point_4_1c_denominator_audit.md` §2.5 established by showing the
two membership branches move the share in **opposite** directions. A claim that
does not depend on the branch cannot have been read off an algebra in which the
branch is decisive.

**IT IS THE RECURRING CLASS:** a numerical or directional criterion written from a
mental model of a quantity rather than from its implementation or achievable
range.

> **ONE INSTANCE, NOT TWO.** `docs/handoff/34_point_4_1a_non_uniformity_rerun.md`
> §1.2 carries the same shape of claim in committed text about a different term —
> that a non-zero entry slippage, being symbol-independent where the haircut is
> per-symbol, *"would move the cross-symbol ratio toward unity"*. **That is the
> same reasoning applied to a different scalar and is equally undetermined by the
> algebra alone.** It is logged as a symptom of this instance rather than counted
> separately, following the precedent by which amendment 1 §7 logged two symptoms
> as instance (41).
>
> **REPORT 34 §1.2 LABELLED ITS CLAIM AS ASSERTED FROM THE ALGEBRA's SHAPE RATHER
> THAN MEASURED.** That labelling is why it is a recorded limitation rather than a
> concealed one, and it does not make the claim determinate. **It is not corrected
> by edit** — report 34 is not amended — **and any future step relying on that
> sentence must derive the direction instead.**

#### THE TOTAL

**41 + 1 = 42.**

**No earlier instance is renumbered or recounted**, and the ledger remains
contiguous from (1) to (42).

---

## 5. THE BLAST RADIUS, STATED IN FULL

**EVERY ARTIFACT BELOW IS SUPERSEDED AS GOVERNING AND NONE IS FALSIFIED. EACH
REMAINS THE CORRECT ANSWER TO THE QUESTION IT WAS ASKED.**

### 5.1 REPORT 28's `c/s` DISTRIBUTION

**STILL:** the correct distribution of the cost-over-stop ratio over path one's
denominator on the real candidate population, including its finding that 419 of
SOLUSDT's 540 tolerance breaches are not floor-bound.

**NO LONGER:** the distribution the tolerance is set against. **Superseded as
governing, not falsified.**

### 5.2 REPORT 32's CLOSED FORM AND ITS FOUR REQUIRED-FLOOR FIGURES

**STILL:** the correct relation between the **old** ratio and width, verified
against `costs.position_size` to a maximum residual of 5.662e-15 across 342
points, and still the derivation of the four figures
`docs/handoff/31_point_5_closing.md` §5.1 recorded as supplied but unsourced.

**NO LONGER:** governing on any width. It was already superseded as governing by
amendment 1 §6.2 on the numerator; it is now superseded on the denominator as
well. **Superseded as governing, not falsified.**

### 5.3 REPORT 33's REVISED CLOSED FORM

**STILL:** the correct required-floor relation under the revised **numerator**,
derived over path one's denominator, verified to 3.761e-15 by report 34's own
solve residual, together with its committed grid and its derived direction split.

**NO LONGER:** the relation the widths are read from. **Superseded as governing,
not falsified.**

### 5.4 REPORT 34's PROTECTED-QUANTITY SHARES, CROSS-SYMBOL RATIOS AND VERDICT

**STILL:** the correct shares of path one's risk unit at report 33's floor, with a
decomposition residual of exactly zero and a flatness test demonstrated to
discriminate between the old denomination's invariant ratio and the revised one.

**NO LONGER:** shares of the governing risk unit — and §4.2 records that they are
**understated** relative to it. **Superseded as governing, not falsified.**

### 5.5 REPORT 35's ENUMERATION

**UNAFFECTED. It remains a correct audit of both paths**, and it is the artifact
this decision rests on. Its enumeration of path one's five terms, its structural
finding that no funding name is reachable within `costs.position_size`, and its
identification of path two's composition are all unchanged by a decision about
which path governs.

### 5.6 THE ONE THAT IS MORE THAN A RELABELLING

> ### REPORT 34's VERDICT — CASE (a), THAT THE PARAMETER HAS AUTHORITY OVER THE
> ### CROSS-SYMBOL RATIO — WAS ESTABLISHED OVER PATH ONE's SHARES. WHETHER IT
> ### SURVIVES UNDER PATH TWO IS NOT KNOWN AND MUST NOT BE ASSUMED.

**THE REASON IS STRUCTURAL AND IS THE WHOLE OF WHY THIS ITEM IS DIFFERENT FROM
THE OTHER FOUR.** The funding term is unlike every term already in the ratio in
two ways at once:

- **ITS ATTACHMENT POINT DIFFERS.** It is charged on the **entry price** times a
  settlement count. The haircut is charged on the **stop price**; the fee legs are
  charged on the entry price and the stop price. A term attached to the entry
  price alone enters the width algebra differently from one attached to the stop
  price, because the stop price is where the width variable lives.
- **IT IS SYMBOL-INDEPENDENT WHERE THE HAIRCUT IS PER-SYMBOL.** The rate and the
  count are single scalars for all three symbols. The haircut is the only
  per-symbol term in the ratio, and it is what produced every cross-symbol result
  reported to date.

**THE NON-UNIFORMITY QUESTION IS THEREFORE REOPENED BY THIS DECISION.** Report 34
answered it under path one. **Its answer under path two is owed, not inherited**,
and it is owed to the re-run named at §6.2 under a criterion pre-committed before
the answer exists.

**NOTHING IS PREDICTED ABOUT THAT ANSWER HERE** — not its direction, not whether
the ratio remains non-invariant, not whether the trigger fires. §4.3 logs what
happens when the direction of a cross-symbol effect is asserted rather than
derived.

---

## 6. WHAT IS OWED NEXT, AND TO WHOM

### 6.1 THE RE-DERIVATION — A SEPARATE STEP WITH ITS OWN COMMIT

**IT COMES BEFORE ANY WIDTH OR LEVEL IS EVALUATED**, as report 32 was separate
from 4.1a and report 33 from amendment 1.

**WHAT IT MUST PRODUCE:**

- **The required floor width as a function of the revised tolerance under path
  two's denominator**, with funding in **both** the numerator and the denominator,
  **per symbol and per direction.**
- **Derived from the implementation and verified against
  `portfolio.size_position` rather than against the algebra in prose.** Report 33
  verified against `sizing.per_unit_denominator`; that is now the wrong object to
  verify against, and verifying against the prose of this document would verify
  nothing.
- **THE DIRECTION SPLIT RE-ESTABLISHED OR SHOWN NOT TO ARISE. IT MUST NOT BE
  CARRIED OVER FROM REPORT 33.** Report 33's split arose from terms charged on the
  stop price, whose sign relative to entry differs by direction. **A term charged
  on the entry price enters the width algebra differently and may produce no split
  at all.** Whether it does is a question to be answered rather than inherited.

### 6.2 THE NON-UNIFORMITY RE-RUN — AFTER IT

Under the criterion `docs/design/04_1c_pre_commitments.md` will pre-commit, and
**not** under the criterion committed at `af7866d`, which report 34 §5.4 recorded
as unable to register a purely multiplicative effect.

### 6.3 THE ORDER OF THE REMAINING 4.1c DOCUMENTS

**`docs/design/04_1c_pre_commitments.md` FOLLOWS, THEN `docs/design/04_1c_proper.md`.**

**`04_1c_pre_commitments.md` OWES:** the decision criterion for the re-run, in its
own commit **before** any quantity under path two exists; the magnitude threshold
`docs/handoff/31_point_5_closing.md` §5.3 records as owed, against which three
items now wait — the fill-price residual, funding's former position outside path
one's risk unit, and whatever the re-derivation surfaces; and the floor-versus-cap
precedence rule report 34 §5.3 routed forward.

**`04_1c_proper.md` OWES:** the tolerance's value, the widths, the dominance check
named at `docs/design/04_1a_denomination.md` §4.1, and kill condition (d)'s
disposition. **It cannot proceed until §6.1 and §6.2 exist**, because every one of
those either is a width or depends on one.

---

## 7. WHAT THIS DOCUMENT DOES NOT DO

**IT SETS NO TOLERANCE VALUE.** Owed by `04_1c_proper.md`.

**IT DERIVES NO CLOSED FORM AND RECOMPUTES NO SHARE.** Owed by the re-derivation
step at §6.1. No width, no tolerance value and no share under either path is
stated anywhere in this document.

**IT DOES NOT SETTLE FLOOR-VERSUS-CAP PRECEDENCE.** Owed by
`04_1c_pre_commitments.md`.

**IT ADOPTS NO DECISION CRITERION.** Owed by `04_1c_pre_commitments.md`.

**IT DOES NOT DISPOSE OF KILL CONDITION (d).** Owed by `04_1c_proper.md`, which
`docs/handoff/31_point_5_closing.md` §9(c) records as additionally needing §5.9's
level decision.

**IT SETS NO MAGNITUDE THRESHOLD.** Owed by `04_1c_pre_commitments.md`.

---

## 8. CHANGE DISCIPLINE

**A CHANGE TO THIS DECISION IS A NEW DOCUMENT WITH ITS OWN COMMIT AND AN EXPLICIT
STATEMENT OF WHAT CHANGED AND WHY — NEVER A SILENT EDIT.** It would be
`docs/design/04_1c_path_and_scope_amendment_1.md`.

**A SILENT EDIT IS A CONTAMINATION EVENT.**

> **THIS DOCUMENT'S VALUE RESTS ON ITS COMMIT PRECEDING THE DERIVATION OF ANY
> QUANTITY UNDER THE RISK UNIT IT COMMITS.**

**AND THE ORDER MATTERS MORE HERE THAN AT EITHER PRIOR DENOMINATION DECISION.**
Amendment 1 §8 recorded that its exposure was greater than 4.1a's because the
direction of convenience was known in advance. **Here the direction of the
figures is known in advance** — §4.2 states that report 34's shares are
understated relative to the governing definition — **and the re-measurement bill
is known to be large.** A risk unit chosen after the widths under it existed would
be a selection, and only the commit order distinguishes it from a decision.

---

**Committed alone, before any quantity under path two's risk unit has been
derived. One path retired and one committed on execution fidelity; one membership
committed on the axiom and on coherence; the direction of the consequence stated
and its magnitude left to the re-derivation; five artifacts superseded as
governing and none falsified; one non-uniformity verdict reopened rather than
inherited; one ledger instance logged with a committed symptom recorded alongside
it. No width is stated, no closed form is derived, and no tolerance value is
committed.**
