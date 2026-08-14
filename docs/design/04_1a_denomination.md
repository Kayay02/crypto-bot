# THE DENOMINATION DECISION — PRE-REGISTERED

**Point 4, sub-point 4.1a.** The first of three sequentially committed documents.

## 1. WHAT THIS DOCUMENT IS, AND WHAT IT IS CONDITIONAL ON

**A PRE-REGISTRATION, FROZEN ON COMMIT.** Made **before any floor-width curve
under an alternative denomination has been computed**, and **before any
performance figure exists for this thesis.** It joins the frozen specification on
its commit, per `docs/design/04_0_divergence_disposition_amendment_2.md` §2.

### 1.1 THE CONDITIONALITY, STATED FIRST BECAUSE IT GOVERNS HOW THE DOCUMENT IS READ

> **A DENOMINATION DECISION IS ONLY OPERATIVE UNDER BRANCH B, WHERE A
> COST-TOLERANCE CONSTRAINT EXISTS. UNDER BRANCH C, WHERE THE TOLERANCE IS
> RETIRED, THERE IS NOTHING TO DENOMINATE.**

**THIS DOCUMENT DECIDES THE DENOMINATION THAT GOVERNS IF A TOLERANCE EXISTS.**

- **It does not decide that one does.**
- **It does not prefer Branch B over Branch C**, and expresses no view between
  them.
- **It must not be read as doing either.** That choice belongs to **4.1b**.

A reader who takes this document as evidence that the project has settled on
Branch B has read it wrongly, and this paragraph is what makes that checkable.

### 1.2 WHY IT IS COMMITTED FIRST

**Two reasons, and the first is a rule rather than a preference.**

**`docs/design/04_0_decision_rule.md` §8 requires the denomination decision to be
committed BEFORE the corresponding floor widths are evaluated.** Report 32
computed widths under one denomination only — the stop path — because that is
what the implemented ratio determines. **Report 32 §2.1 warns explicitly that
this must not become an argument that the stop path is the correct thing to
constrain, and that selection by availability is the same defect as selection
after sight.**

**And 4.1b's argument may reasonably refer to what the constraint would bind**,
which cannot be discussed until the denomination is settled. Deciding both in one
document would make the order between them unprovable — **the split exists so
that the order is a fact about commit hashes rather than a claim about
intentions.**

### 1.3 WHAT IT DOES NOT COMMIT

**No tolerance value. No floor width, beyond quoting the four already committed
at report 32 §3.3 as established facts. No branch. Nothing is computed and no
code is added.**

---

## 2. THE QUESTION, STATED PRECISELY

The constraint has the form **`c / s` at most `tau`**, where **`s` is the stop
distance in price terms** and `tau` is the tolerance.

**THE EXIT LEGS DIFFER IN FEE TREATMENT.** Per document 06: the stop fills
**taker**, through a conditional market order (E2); the target fills **maker**,
through a resting limit (E3); and the time exit is *"a taker market order at that
1h bar's close"* (§5.3). **So `c` is not a single quantity, and the constraint is
under-specified until it names one.**

### 2.1 THE CANDIDATES

**THE STOP PATH.** Entry taker fee, stop-leg taker fee, entry slippage, and the
**stop haircut**. This is what the implemented ratio measures — report 32 §2
establishes it from `src/analysis/sizing_drag.py:177`, `src/engine/sizing.py:264`
and `src/engine/costs.py:336`.

**THE TARGET PATH.** Entry taker fee, target-leg **maker** fee, entry slippage,
and **no stop haircut** — a position exiting at the target never touches the stop,
so the haircut is not charged on it.

**THE WORSE OF THE TWO**, evaluated per position.

**ONE CONSTRAINT PER PATH**, both of which must hold.

### 2.2 A THIRD PATH THE CANDIDATE LIST OMITS

> **THERE ARE THREE EXIT PATHS, NOT TWO.**

**The time exit is a taker market order and carries no haircut** (document 06
§5.3). Its cost composition is therefore **entry taker fee, exit taker fee, entry
slippage** — the same shape as the stop path **minus the haircut**, and strictly
more expensive on the exit leg than the target path's maker fee.

**It is named here because a candidate list that omits it is a list that cannot
be exhaustive**, and because §3 must argue against all the alternatives rather
than the two that were tabulated.

**AND ONE COST IS COMMON TO ALL THREE.** Funding is charged at the provisioned
count in the denominator and in the target cost bracket, on every position
regardless of how it exits (`docs/design/06a_exit_resolution_spec_amendment_1.md`
E7.1 and E7.2). **The entry leg and funding are paid on every path; the paths
differ only in the exit leg.**

### 2.3 THE CONDITION UNDER WHICH THIS DECISION IS MADE, DELIBERATELY

**Report 32 computed widths under the stop-path denomination only.** The other
three — and the time path — **have no widths computed at this commit.**

> **THAT IS A FACT ABOUT WHAT THE IMPLEMENTATION DETERMINES. IT IS NOT EVIDENCE
> ABOUT WHICH DENOMINATION IS CORRECT.**

**This decision is made in that condition on purpose.** Computing widths under
all four and then choosing would be choosing after sight; computing widths under
one and then choosing it would be choosing by availability. **The decision is
therefore made from what the constraint is for, before any further width
exists.**

---

## 3. THE DECISION, ARGUED FROM WHAT THE CONSTRAINT IS FOR

### 3.1 WHAT A COST-TOLERANCE CONSTRAINT SERVES IN THIS DESIGN

**Under net-solved geometry the stop returns exactly one risk unit and the target
exactly 1.5 risk units by construction.** Costs **do not erode the R multiples**;
they are **contained within them**. That is the fact that broke the tolerance's
original derivation, per `docs/handoff/31_point_5_closing.md` §5.1.

**SO WHAT IS LEFT FOR THE CONSTRAINT TO DO?** The risk unit is fixed. What varies
is **how much of it is spent on frictions rather than on the market move being
bet on.** A position whose costs consume a large share of its risk unit is one
whose exposure to the hypothesis is correspondingly small: the same dollars are
at stake, but a larger part of them is paid to the venue regardless of what the
market does.

> **THE CONSTRAINT BOUNDS THE FRICTION SHARE OF THE RISK UNIT.** That is the
> reading that survives net-solved geometry, and the denomination question is
> then: **friction on which path?**

**THIS SECTION DOES NOT ARGUE THAT SUCH A CONSTRAINT SHOULD EXIST.** Whether
bounding the friction share is worth doing at all is Branch B versus Branch C and
belongs to 4.1b.

### 3.2 THE DECISION

> ### THE CONSTRAINT IS DENOMINATED IN THE COST OF THE STOP PATH.

### 3.3 THE GROUNDS

**(1) THE STOP LEG CARRIES THE LARGEST EXIT-LEG RATE OF THE THREE, AND IT IS NOT
CLOSE.** The stop leg is charged **taker plus haircut**; the time leg **taker**;
the target leg **maker**. The rate ordering is therefore
**stop > time > target**, and it holds by construction rather than by
measurement, since the haircut is strictly positive and the taker fee exceeds the
maker fee.

**(2) A CONSTRAINT ON THE MOST EXPENSIVE PATH BOUNDS THE OTHERS. ONE CONSTRAINT
PER PATH IS THEREFORE NOT STRICTER — IT IS THE SAME CONSTRAINT UNDER MORE
NAMES.** This disposes of the fourth candidate directly: two constraints of which
one is always the binding one are one constraint and a redundancy. **And it
disposes of "the worse of the two" as a distinct option** — the worse of the paths
IS the stop path, so that candidate names the same rule.

**A QUALIFICATION, STATED RATHER THAN GLOSSED.** The rate ordering is certain; the
ordering of `rate x price` is not established here, because the three legs are
charged at different price levels — the stop below entry on a long, the target
above it. **Establishing that the stop path dominates at every width the design
contemplates is a derivation this document does not perform**, and §4 records it
as owed. **The decision does not rest on it**: grounds (3) and (4) stand
independently, and this ground would merely become "the stop path is the most
expensive at the widths that matter" rather than "at all widths".

**(3) THE STOP PATH IS THE PATH THE RISK UNIT IS BUILT FROM.** The project's
standing rule is **$20 of risk after fees and estimated slippage**
(`docs/design/00_standing_brief.md` §2), enforced **on the loss**. The
denominator `d` that sizes every position **is the stop path's all-in per-unit
cost** — that is precisely what `src/engine/costs.py:336` computes. **The target
path's cost does not enter the risk unit at all**; it enters the target solve.

> **CONSTRAINING `c / s` ON THE STOP PATH CONSTRAINS THE FRICTION SHARE OF THE
> QUANTITY THE RISK RULE IS DENOMINATED IN.** Constraining it on the target path
> would bound the friction share of a quantity the risk rule never mentions.

**(4) EXCLUDING THE HAIRCUT WOULD MAKE THE CONSTRAINT BLIND TO THE LARGEST AND
LEAST-KNOWN TERM, AND THAT IS THE WRONG DIRECTION FOR A RISK CONSTRAINT.**

`docs/handoff/31_point_5_closing.md` §5.2 records that the haircut — 5 bps on
BTCUSDT and ETHUSDT, 10 bps on SOLUSDT — **is the entire slippage-and-gap model**,
is **a placeholder rather than a venue-published figure**, and **cannot be
validated against this data layer** because no bar's first observed price exists
at any resolution.

**THE PLACEHOLDER STATUS ARGUES FOR INCLUDING IT, NOT AGAINST.** The argument
against would be that a denomination depending on a placeholder inherits its
uncertainty. **It does — and the uncertainty is in the world, not in the choice.**
If the haircut is real, excluding it from the constraint does not make the cost
smaller; it makes the constraint unable to see it. **A constraint that is precise
about the costs we know and silent about the one we do not is precise in the
wrong place.**

**AND THE HAIRCUT IS WHERE THE ACTION ALREADY IS.** Report 28 §9 measured that
**419 of SOLUSDT's 540 tolerance breaches are not floor-bound** — they breach
because of the 10 bps haircut rather than because of the floor. **A denomination
excluding the haircut would report that symbol as compliant on the very positions
that are not.**

**(5) THE FLOOR CAN CONTROL THE STOP PATH AND CONTROLS THE OTHERS ONLY
INDIRECTLY.** The floor sets `s`, which is the denominator of every candidate and
**also the price level at which the stop leg's own fee and haircut are charged**.
The target and time legs are charged at prices the floor does not set directly.
**The floor is the instrument; the stop path is what it acts on.**

### 3.4 WHAT WAS NOT A REASON

> **REPORT 32's SINGLE CURVE WAS NOT A REASON, AND IS RECORDED HERE AS NOT
> HAVING BEEN ONE.**

Every ground above is available without knowing any width under any
denomination. Grounds (1) and (2) are rate comparisons; (3) is a statement about
which quantity the risk rule is denominated in; (4) is about what a constraint
can and cannot see; (5) is about what the floor acts on. **None of them mentions
a number report 32 produced.**

**NOR WAS CONVENIENCE A REASON. No floor width is stated anywhere in this
document** other than the four quoted at §5 as already-committed facts, and the
decision was not checked against what floor it implies.

**AND THE DECISION RUNS AGAINST CONVENIENCE ON ITS FACE**, which is worth stating
because it is the direction that attracts less scrutiny: the stop path is the
**most expensive** of the three, so denominating in it demands the **widest**
floor of any candidate at the same tolerance. **A denomination chosen for comfort
would have been the target path.**

---

## 4. WHAT FOLLOWS FOR THE DERIVATION

> **NO NEW DERIVATION IS REQUIRED. REPORT 32's CLOSED FORM GOVERNS UNCHANGED.**

The decision is the stop path, which is the denomination report 32 derived
against, so:

    long   w(tau) = (2f + e + h) / (tau + f + h)
    short  w(tau) = (2f + e + h) / (tau - f - h)

stands as the governing relation, with `f` the taker fee, `e` the entry slippage
fraction and `h` the stop haircut fraction (report 32 §3.1). **4.1c may evaluate
widths from it without waiting on anything.**

### 4.1 WHAT IS OWED ANYWAY

**THE DOMINANCE CHECK OF §3.3's QUALIFICATION.** If 4.1c relies on the claim that
constraining the stop path bounds the other two — rather than merely on the stop
path being the right thing to constrain in its own terms — **that dominance must
be verified across the widths in play, because it compares `rate x price` at
three different price levels.** Named as owed. **Not derived here.**

### 4.2 THE DIRECTION SPLIT

**Report 32 §3.2's direction split applies under any denomination in which a cost
term is charged on the stop price**, because the stop sits below entry on a long
and above it on a short.

- **The stop path: yes.** Both its taker fee and its haircut are charged there.
- **The worse-of-paths candidate: yes**, being the stop path.
- **The target path: it has an analogous split of its own, with the opposite
  sign**, since the target sits above entry on a long and below it on a short.
  **It is not the same split and no form for it is derived here.**
- **The time path: not in the same way.** Its exit price is a bar close, which is
  not a fixed function of entry, so no closed-form direction split follows.

**The governing relation is therefore per symbol AND per direction**, as report
32 §3.2 established and as no frozen document had previously recorded.

---

## 5. ERRATUM AGAINST `docs/handoff/31_point_5_closing.md` §5.1

### THE ERRATUM

That section supplies *"required floors of **1.530% / 1.561% (BTC, ETH)** and
**1.971% / 2.030% (SOL)**"*. **The parenthetical labels the first pair as two
symbols, BTCUSDT and ETHUSDT.**

### THE CORRECTION

**BTCUSDT AND ETHUSDT SHARE A CURVE EXACTLY.** They share a haircut — 5 bps each —
and differ in nothing else the cost algebra uses, so their required floors are
identical at every tolerance (report 32 §3.4).

> **THE TWO FIGURES ARE THE LONG AND THE SHORT LEGS OF A SINGLE SHARED CURVE, NOT
> TWO SYMBOLS.** The same holds for the SOLUSDT pair.

Report 32 §3.3 derives them as **1.5302% long and 1.5611% short** on BTCUSDT and
ETHUSDT, and **1.9713% long and 2.0295% short** on SOLUSDT.

**THE FIGURES ARE CORRECT. THE POPULATION LABELS ARE WRONG.**

### THE CLASS, AND IT IS THE THIRD OCCURRENCE

**This is the same shape as `docs/handoff/31_point_5_closing.md` §8's erratum 3**
— right numbers, wrong population attached to them — **which that record itself
calls the purest instance of the project's recurring defect class.** Erratum 3 is
logged in that record's §7.2 as instance (29).

**THIS IS THE THIRD OCCURRENCE OF THAT SHAPE**: document 06a §5.1's three years
labelled as three symbols; this pair of directions labelled as two symbols; and
the numeric coincidence at `docs/handoff/31_point_5_closing.md` §5.9, where two
different quantities both equal 157 and the record had to say so explicitly to
stop them being conflated.

### WHETHER ANYTHING OPERATIVE CHANGES

**NOTHING.** §5.1 recorded the figures as **supplied but UNSOURCED**, stated that
they *"appear nowhere in `docs/` or `reports/`"*, and required that **Point 4
derive them from the implementation before relying on them.** Report 32 did
exactly that, independently, and **did not carry the label forward.**

### THE CLASSIFICATION, MADE EXPLICITLY

> **LOGGED AS AN ERRATUM ONLY. NOT A FURTHER LEDGER INSTANCE.**

**THE GROUNDS.** The closing record **quarantined these figures at the moment they
entered** — marked them unsourced, forbade reliance on them, and routed them for
derivation — **and the quarantine held.** The label was never operative because
the figures were never operative, and the mechanism designed to catch exactly
this caught it.

**THE TEST THAT MAKES THIS A DISTINCTION RATHER THAN AN EXCUSE:** had §5.1 stated
the figures as established rather than quarantined, the mislabel would have
propagated a wrong population into the frozen chain and **would be a ledger
instance.** The quarantine is doing the work, not the outcome.

**IT IS A CLOSE CALL AND THE ALTERNATIVE IS NAMED.** Instance (29) is the same
shape and was logged, and a reader who holds that the ledger should count the
defect regardless of whether the record fenced it off would reach 39 rather than
38. **That reading is available and is not obviously wrong.** The call made here
is the one stated above.

**ERRATA ARE LOGGED, NOT PATCHED.** `docs/handoff/31_point_5_closing.md` is frozen
and is not edited.

---

## 6. THE LEDGER

### WHAT THE COMMITTED DOCUMENTS SAY, READ BEFORE THIS SECTION WAS WRITTEN

- `docs/design/04_0_divergence_disposition_amendment_2.md` §5 states
  **"32 + 4 = 36"**.
- `docs/design/04_0_decision_rule.md` §9 states **"THE TOTAL IS NOW 37. 36 + 1 =
  37"**.

**Both confirmed against the files.**

### INSTANCE (38)

**A VERIFICATION CHECK IN REPORT 32's STEP SEARCHED A MODULE'S RAW TEXT FOR A
COST-ALGEBRA EXPRESSION AND FAILED AGAINST A CLEAN MODULE**, because the module
**quotes that expression in its docstring in order to cite it**, which the step
required it to do. The check was corrected to run over **executable tokens only**
and **the module was not changed.** Recorded at
`docs/handoff/32_point_4_0_3_floor_curve.md` §8, which deliberately left the
classification to whoever next touched the ledger. **This document makes it.**

### THE STANDING INCLUSION CRITERION, NOW ADOPTED

> **A VERIFICATION CHECK THAT FIRES FALSELY IS LOGGED AS A LEDGER INSTANCE IF AND
> ONLY IF THE IMMEDIATE REMEDIATION ON OFFER WOULD HAVE DEGRADED AN OTHERWISE
> CORRECT ARTIFACT.**

- **Instance (37) qualifies**: the remediation on offer was **a false defect
  report against a clean document.**
- **Instance (38) qualifies**: the remediation on offer was **stripping a required
  and accurate citation from a module** to satisfy an over-broad text match.
- **Routine test iteration, in which no correct artifact was at risk, is
  excluded.**

**THE CRITERION EXISTS SO THAT THIS IS DECIDED BY A STATED RULE RATHER THAN CASE
BY CASE**, and so that the next such check is classified by someone who does not
yet know which way it will come out.

### THE TOTAL

**37 + 1 = 38.**

**No earlier instance is renumbered or recounted**, and the ledger remains
contiguous from (1) to (38).

---

## 7. WHAT THIS DOCUMENT DOES NOT DO

- **It does not choose a branch**, and expresses no preference between Branch B
  and Branch C. **Owed to 4.1b.**
- **It does not argue for or against a tolerance existing.** **Owed to 4.1b.**
- **It states no tolerance value.** The frozen 0.11 is referred to only as an
  existing committed parameter. **Owed to 4.1b.**
- **It states no floor width**, beyond quoting the four already committed at
  report 32 §3.3. **Owed to 4.1c.**
- **It does not dispose of kill condition (d).** **Owed to 4.1c.**
- **It sets no magnitude threshold** for the after-costs risk rule. **Owed to
  4.1c.**

---

## 8. CHANGE DISCIPLINE

**A CHANGE TO THIS DECISION IS A NEW DOCUMENT WITH ITS OWN COMMIT AND AN EXPLICIT
STATEMENT OF WHAT CHANGED AND WHY — NEVER A SILENT EDIT.** Under the naming
convention for Point 4 documents it would be
`docs/design/04_1a_denomination_amendment_1.md`.

**A SILENT EDIT IS A CONTAMINATION EVENT.**

> **THIS DOCUMENT'S VALUE RESTS ENTIRELY ON ITS COMMIT PRECEDING THE COMPUTATION
> OF WIDTHS UNDER THE ALTERNATIVE DENOMINATIONS.** Editing it afterwards would
> destroy exactly the property it was split out to create.

The split cost an extra document and an extra commit, and bought one thing: **the
order between the denomination and the widths is a fact anyone can check from
`git log`, rather than a claim about what was known when.** An edit after the
widths exist would convert that fact back into a claim, and there would be no way
to tell from the repository that it had.

---

**Committed alone, before any floor-width curve under an alternative denomination
exists and before any performance figure exists for this thesis. One denomination
decided and argued from what the constraint is for; one third exit path added to
a candidate list that omitted it; one derivation confirmed as governing unchanged
and one dominance check named as owed; one erratum logged and classified; one
standing inclusion criterion adopted; the ledger at 38. No branch is chosen, no
tolerance is named, and no floor is recommended.**
