# WHAT A STOP CAP MUST DO — THE REQUIREMENT

**Point 4, sub-point 4.1f.** The requirement, committed **before any candidate
rule is evaluated against it**. **Nothing is computed and no cap value is
stated.**

## 0. THE ORDER, AND WHY IT IS THIS WAY

`docs/design/04_1e_stop_cap.md` recorded the frozen cap as **wrong** and refused
to choose a replacement. Its §8 named the clause most exposed to pressure:

> **"It will first be inconvenient at the moment a step needs a cap in order to
> proceed, and the tempting move will be to adopt whichever value is nearest to
> hand."**

> ### COMMITTING WHAT A CAP MUST DO BEFORE MEASURING WHAT ANY CANDIDATE DELIVERS
> ### IS WHAT PREVENTS THE REQUIREMENT BEING WRITTEN TO FIT THE CANDIDATE.

**THIS DOCUMENT COMPUTES NOTHING.** Figures from
`docs/handoff/38_point_4_stop_cap_audit.md` are quoted as established facts where
an argument needs them. **No candidate rule is evaluated here** — that is
`docs/handoff/39_point_4_cap_candidates.md`, and the adoption is
`docs/design/04_1g_cap_adoption.md`.

**A PRE-REGISTRATION, FROZEN ON COMMIT**, joining the frozen specification per
`docs/design/04_0_divergence_disposition_amendment_2.md` §2. Committed alone.

---

## 1. WHAT THE AUDIT REMOVED

**THE REQUIREMENT IS BUILT FROM WHAT SURVIVED, NOT FROM THE PURPOSES THAT
FAILED.** Two purposes were credited to the cap and report 38 disposed of both.

### 1.1 THE GRANULARITY PURPOSE — DROPPED

Report 38 §3.3: the venue's minimum lot binds at between **49.03 and 538.61 per
cent** of entry depending on symbol and price — **14.0 to 153.9 times** the frozen
cap.

> ### A CONSTRAINT THAT BINDS ONE TO TWO ORDERS OF MAGNITUDE AWAY DOES NOT
> ### CONSTRAIN A CAP IN ANY PLAUSIBLE REGION. IT IS DROPPED AS A GROUND.

**It returns in a different role at §3.3** — not as a reason to have a cap, but as
a condition any rule including removal must satisfy. **Those are different jobs
and the distinction is the point.**

### 1.2 THE REACHABILITY PURPOSE — DROPPED

Report 38 §4.2: risk is fixed and the stop distance divides it, so a narrower stop
buys a **larger** position. On the candidates the frozen cap clips, notional at the
cap exceeds notional at the ATR-implied width on **100.00 per cent** of them,
median 1.2304 times and maximum 13.3210 times.

> ### A CAP CANNOT BE JUSTIFIED AS LIMITING EXPOSURE TO A VIOLENT MOVE. IT
> ### INCREASES THAT EXPOSURE ON EVERY CANDIDATE IT FIRES ON.

**AND THE SAME MECHANISM CUTS A SECOND TIME.** `costs.CostConfig.leverage_term`
bounds the risk unit from **below** at `risk_usd / (equity x max_leverage)`,
because a narrow stop means a large notional. **A cap pushes every candidate it
clips toward that bound rather than away from it.** The floor is the instrument
that protects against leverage; the cap works against it.

**DROPPED AS A GROUND.** Report 38 §4.3 adds that the stop haircut prices a
width-independent adverse fill and so does not price what the cap was credited
with limiting, and that nothing remains which the cap addresses in the protective
direction.

---

## 2. WHETHER A CAP IS NEEDED AT ALL

> ### THIS SECTION IS NOT A FORMALITY. REMOVAL IS A LIVE CANDIDATE AND IS NOT
> ### DISMISSED BECAUSE A CAP CURRENTLY EXISTS.

### 2.1 THE ARGUMENT FOR REMOVAL

**THE THESIS SPECIFIES AN ATR-DERIVED STOP.** A cap replaces it, on the fraction
it clips, with a flat percentage of entry that does not vary with volatility at
all. `docs/design/04_1e_stop_cap.md` §5.1 records the consequence: on more than a
third of SOLUSDT's candidates the strategy was not running the stop rule the
thesis specifies.

**REMOVAL MAKES THAT GAP ZERO BY CONSTRUCTION.** No fraction is clipped, so no
fraction runs a different rule.

**AND BOTH SURVIVING OBJECTIONS TO A CAP POINT THE SAME WAY.** §1.2 establishes
that a cap increases gap exposure and consumes leverage headroom. **Removing it
removes both effects rather than tuning them.**

### 2.2 THE ARGUMENT AGAINST REMOVAL, STATED AT ITS STRONGEST

**A STOP WITHOUT AN UPPER BOUND MAKES THE QUANTITY ARBITRARILY SMALL.** Quantity is
the risk unit divided into the allocation, and the risk unit grows without bound
with the stop width. `sizing.viability` refuses a position whose quantity falls
below the venue's minimum lot, or whose notional falls below the venue's minimum
notional, and **a refused position is a SKIP** — it leaves the population silently.

> ### THAT IS THE ONE MECHANISM BY WHICH REMOVING THE CAP COULD DO HARM, AND IT
> ### IS A REAL ONE.

`sizing.viability`'s docstring records both conditions as **unreachable at the
frozen values** — and the frozen values include the cap. **Removing the cap is
exactly the change that could make them reachable.**

### 2.3 THE QUESTIONS THIS RAISES, LEFT AS QUESTIONS

**FOR `docs/handoff/39_point_4_cap_candidates.md` TO ANSWER, NOT THIS DOCUMENT:**

- **What is the widest ATR-implied stop in the candidate population, per symbol?**
- **What quantity does it produce, and how does that compare to the venue's
  minimum lot and minimum notional?**
- **Does the venue minimum bind anywhere in the population under removal, and on
  how many candidates?**

**THE QUESTION IS LIVE RATHER THAN ACADEMIC.** Report 38 §3.3 gives ETHUSDT's
tightest minimum-lot binding width, at its highest observed price, as **49.03 per
cent**, and §4.2 gives the widest ATR-implied width among clipped candidates as
**49.709 per cent**. **Those two numbers are close enough that the answer cannot be
assumed in either direction.**

> ### THIS DOCUMENT DOES NOT ANSWER THEM AND DOES NOT GUESS. IT MAKES THE ANSWER
> ### DECISIVE BY PUTTING IT IN LIMB 3.

---

## 3. THE REQUIREMENT

**FOUR LIMBS. A CANDIDATE RULE IS ADMISSIBLE ONLY IF IT SATISFIES ALL FOUR.**
Each is stated with what would show it failed, so the requirement discriminates
rather than ratifies.

### 3.1 LIMB 1 — DERIVATION

> ### IF A CAP EXISTS, IT IS DERIVED FROM A STATED QUANTITY, AND ITS VALUE
> ### FOLLOWS FROM THAT DERIVATION RATHER THAN BEING SUPPLIED ALONGSIDE IT.

**THIS IS THE LIMB 0.035 FAILED.** `docs/design/04_1e_stop_cap.md` §2.4 found its
provenance to be scaffolding in all nine places it appears.

**IT IS SATISFIED VACUOUSLY BY REMOVAL**, which has no value to derive. **That is a
vacuous pass and is recorded as one**, not as a positive merit.

**FAILS IF:** the value cannot be reproduced from the stated derivation and its
inputs; or the derivation is stated but a different value is used.

### 3.2 LIMB 2 — INTENT DELIVERY

> ### THE RULE STATES WHAT FRACTION OF THE CANDIDATE POPULATION IT CLIPS, AND
> ### DELIVERS IT.

**THE CLIPPED FRACTION IS THE THESIS GAP.** It is the fraction on which the
strategy runs a flat rule rather than the thesis's ATR rule, and it is therefore
not a side effect of the cap but the cap's principal cost. **A rule that does not
state what it costs cannot be weighed against one that does.**

**THIS IS THE DISTINCTION `src/sweep/grid.py`'s `derived_cap` DOCSTRING ALREADY
DRAWS**, between a guard rail binding a small tail and a rule that *"binds on 50%
at the same point, which is a second stop rule rather than a guard rail."*

**FAILS IF:** the rule states no intended fraction; or its realised fraction over
the candidate population departs from its stated intent.

**WHAT THIS LIMB DOES NOT SETTLE.** It does not say what intended fraction is
acceptable. **A rule intending a large fraction and delivering it passes this
limb**, and whether that fraction is tolerable is a judgement
`docs/design/04_1g_cap_adoption.md` must make and record as one. **The limb is
stated this way deliberately: setting an acceptable fraction here, before any
candidate's fraction is known, would be inventing a number with nothing to derive
it from — and setting it after would be fitting it.**

### 3.3 LIMB 3 — EXECUTABILITY

> ### EVERY POSITION THE RULE ADMITS MUST BE EXECUTABLE AT THE VENUE: QUANTITY AT
> ### OR ABOVE THE MINIMUM LOT, AND NOTIONAL AT OR ABOVE THE MINIMUM NOTIONAL.

**THIS IS THE ONLY LIMB THAT COULD REQUIRE AN UPPER BOUND ON STOP WIDTH.** §1.1
dropped granularity as a *reason to have a cap*; it returns here as a *condition
every rule must meet*, removal included.

**THE FAILURE IT GUARDS IS SILENT.** A position the venue would refuse becomes a
skip, and the population shrinks without anything raising an error.

**FAILS IF:** any candidate in the population is refused for quantity or notional
under the rule. **The count is the evidence, and a count of zero must be reported
rather than assumed** — `docs/design/04_1c_proper.md` §6.3's treatment of
population A, applied here.

### 3.4 LIMB 4 — POPULATION DETERMINACY

> ### THE RULE MUST YIELD A DETERMINATE CLIPPED POPULATION. IF IT DOES NOT, THE
> ### INDETERMINACY MUST BE STATED, COUNTED, AND ROUTED TO WHATEVER DEPENDS ON IT.

**A RULE COMPUTED PER FOLD MAKES THE POPULATION A FUNCTION OF WHICH FOLD IS
ASKED.** The same candidate may be clipped under one fold's rule and not another's.
That is not automatically disqualifying — it may be the honest consequence of a
rule that adapts to the regime — **but a fold-dependent population lands on
whatever aggregates across folds**, and discovering that later is the failure this
limb exists to prevent.

**FAILS IF:** the population is fold-dependent and the dependence is neither
counted nor routed.

### 3.5 WHAT FOLLOWS IF LIMB 3 DOES NOT BIND

> ### IF NO CANDIDATE IN THE POPULATION IS REFUSED UNDER REMOVAL, THEN NO LIMB OF
> ### THIS REQUIREMENT REQUIRES A CAP TO EXIST.

Limb 1 is vacuous under removal, limb 2 gives it a clipped fraction of zero, and
limb 4 gives it a determinate population. **That is stated here, before the
measurement, so that the measurement decides it rather than the adoption
document's preferences.**

**IT IS A CONDITIONAL AND NOT A CONCLUSION.** `docs/design/04_1g_cap_adoption.md`
chooses, on `docs/handoff/39_point_4_cap_candidates.md`'s measurements.

---

## 4. THE ADMISSIBILITY STANDARD

### 4.1 DERIVED, NOT SUPPLIED

**A cap value that appears in the repository without a derivation producing it is
not admissible**, whatever its magnitude and however long it has been in use. That
is limb 1 and it is the standard `docs/design/04_1e_stop_cap.md` applied.

### 4.2 A CONSTANT IS ADMISSIBLE IF IT IS DERIVED

> ### CONSTANTS ARE NOT EXCLUDED IN ADVANCE. RULING OUT A FORM BEFORE THE ARGUMENT
> ### IS THE SAME DEFECT AS RULING ONE IN.

If the requirement's limbs are satisfied by a rule whose output happens not to vary
by symbol or by fold, **that constant is derived and is admissible.** The objection
to 0.035 was never that it was a constant; it was that nothing produced it.

**AND A CONSTANT HAS AN ADVANTAGE LIMB 4 RECOGNISES**, being determinate by
construction. That is a merit under limb 4 and not a thumb on the scale elsewhere.

### 4.3 NO FORM IS PREFERRED

Per-symbol, per-fold, per-symbol-per-fold, constant, or no cap at all — **the
requirement admits any of them and prefers none.** A candidate is judged limb by
limb.

---

## 5. WHAT IS BARRED AS A GROUND

> ### PRESERVING COMPARABILITY WITH EXISTING MEASUREMENTS IS NOT A GROUND FOR
> ### ADOPTING ANY CANDIDATE, AND AN ARGUMENT FOR RETAINING 0.035 ON THAT BASIS IS
> ### BARRED HOWEVER IT IS PHRASED.

`docs/design/04_0_decision_rule.md` §8 commits the standing principle —
**execution reality over measurement convenience** — and records that a finding
with awkward consequences for existing work **is a finding about the work and not
an argument against the finding.**

**THE PHRASINGS THE BAR REACHES, NAMED SO THEY CANNOT BE OFFERED AS SOMETHING
ELSE:** that reports 24, 26, 28, 30, 32, 34, 36, 37 and 38 measured at 0.035; that
changing it invalidates a body of work; that a re-measurement would be large; that
the value is what everything is calibrated against; and that continuity is itself
a virtue here.

> ### NONE OF THOSE IS AN ARGUMENT ABOUT WHAT A STOP CAP SHOULD DO.

**0.035 IS NOT EXCLUDED FROM CANDIDACY BY THIS SECTION.** If some derivation
produces it, limb 1 is satisfied and it competes on the other three like anything
else. **What is barred is adopting it because it is already there.**

---

## 6. WHAT THIS DOCUMENT DOES NOT DO

**IT EVALUATES NO CANDIDATE AND COMPUTES NOTHING.** Owed to
`docs/handoff/39_point_4_cap_candidates.md`.

**IT ADOPTS NOTHING AND PREFERS NOTHING.** Owed to
`docs/design/04_1g_cap_adoption.md`.

**IT STATES NO CAP VALUE AND NO ACCEPTABLE CLIPPED FRACTION.** §3.2 records why the
second is deliberately absent.

**IT DOES NOT RE-ARGUE THE COST TOLERANCE.** The level of 0.10 rests on the
displacement budget at `docs/design/04_1c_proper.md` §2 and is untouched by any
cap. A cap moves the admitted domain's lower bound, which is a question about
whether the level still lies inside it — **a check on position, not a
re-argument.**

---

## 7. CHANGE DISCIPLINE

**A CHANGE TO THIS REQUIREMENT IS A NEW DOCUMENT WITH ITS OWN COMMIT AND AN
EXPLICIT STATEMENT OF WHAT CHANGED AND WHY — NEVER A SILENT EDIT.** It would be
`docs/design/04_1f_cap_requirement_amendment_1.md`.

**A SILENT EDIT IS A CONTAMINATION EVENT.**

> ### AN AMENDMENT MADE AFTER `docs/handoff/39_point_4_cap_candidates.md` EXISTS
> ### MUST SAY SO IN THOSE WORDS.

**THAT IS THE WHOLE VALUE OF THIS DOCUMENT'S COMMIT PRECEDING THE MEASUREMENT.**
A requirement relaxed once a favoured candidate is known to fail it is not a
requirement, and only the commit order distinguishes the two.

---

**Committed alone, before any candidate is evaluated. Two purposes dropped on the
audit's findings and one of them returned in a different role; removal considered
seriously and left standing as a live candidate with the questions that would
settle it named and unanswered; four limbs committed, each with what would show it
failed; the standard stated as derived-not-supplied with constants explicitly not
excluded and no form preferred; and comparability barred as a ground in every
phrasing it could take. No candidate is evaluated, no value is stated, and no
acceptable clipped fraction is set.**
