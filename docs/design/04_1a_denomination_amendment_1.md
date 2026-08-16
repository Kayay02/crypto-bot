# AMENDMENT 1 TO THE DENOMINATION DECISION

**Point 4, sub-point 4.1a, amendment 1.** The denomination is re-decided. Nothing
is derived.

## 0. THE SCOPE LIMIT, STATED FIRST

> ### THIS DOCUMENT DECIDES A DENOMINATION. IT DERIVES NO FLOOR WIDTH, STATES NO
> ### CLOSED FORM FOR THE REVISED FLOOR, AND EVALUATES NOTHING.

`docs/design/04_0_decision_rule.md` §8 requires the denomination decision to be
committed **before** the corresponding widths are evaluated, and
`docs/design/04_1a_denomination.md` §8 states that document's value rests
entirely on that order.

**A REVISED DENOMINATION DERIVED AND COMMITTED IN ONE DOCUMENT WOULD DESTROY THE
PROPERTY THE 4.1 SPLIT WAS CREATED TO PRODUCE** — and it would do so on the one
denomination change where **the direction of convenience is already known** (§5).
The derivation is a separate step with its own commit, exactly as report 32 was
separate from 4.1a.

**No requirement below is read as asking for the revised closed form.** None
appeared to.

---

## 1. WHAT THIS DOCUMENT IS

**AN AMENDMENT TO `docs/design/04_1a_denomination.md` (commit `b8077449`), MADE
UNDER THAT DOCUMENT'S §8.** That document is **not edited.**

**FROZEN ON COMMIT.** Made **before any floor width under the revised
denomination has been derived or evaluated**, and **before any performance figure
exists for this thesis.**

### 1.1 PRECEDENCE

- **On the denomination, this document governs.**
- **4.1a governs on everything else it decided**, and its grounds (3), (4) and
  (5) are **examined in §4 below rather than assumed to survive.**

### 1.2 WHAT IS NOT REOPENED

**`docs/design/04_1b_tolerance_and_branch.md`'s RATIONALE AND ITS BRANCH B CHOICE
STAND UNCHANGED.** The constraint still exists, and what it protects is still the
share of the risk unit determined by estimate rather than by observable price
geometry.

> **THIS AMENDMENT CHANGES THE RATIO THE CONSTRAINT IS EXPRESSED IN. IT DOES NOT
> CHANGE WHAT THE CONSTRAINT IS FOR.**

---

## 2. WHAT CHANGED, AND WHY IT IS A CHANGE OF FACT RATHER THAN OF MIND

### 2.1 WHAT WAS DECIDED

**4.1a decided the constraint binds the cost of the stop path** — entry taker
fee, stop-leg taker fee, entry slippage and stop haircut.

**4.1b §5 considered re-denominating onto the haircut alone and declined**, on
the ground that **the haircut sits inside the stop-path cost, so constraining the
whole constrains the part.**

### 2.2 THE FINDING

`docs/design/04_1c_non_uniformity_check.md` §5.3 established that **SOLUSDT's
unvalidated share is a constant multiple of BTCUSDT's and ETHUSDT's — 1.5455 —
invariant across the entire committed grid to within 1e-12.**

> **THE TOLERANCE ENTERS EVERY SYMBOL IDENTICALLY. MOVING IT MOVES EVERY SYMBOL'S
> UNVALIDATED SHARE IN LOCKSTEP AND CANNOT ALTER THEIR RATIO AT ANY POINT IN ITS
> RANGE.**

**THE CONSTRAINT'S PARAMETER THEREFORE HAS ZERO AUTHORITY OVER THE CROSS-SYMBOL
DISTRIBUTION OF THE QUANTITY 4.1b's RATIONALE SAYS IT PROTECTS.** That is a
**categorical** finding, not a magnitude one: there is no setting of the parameter
at which the distribution is different.

### 2.3 THE DISTINCTION THAT MATTERS

**4.1b §5's GROUND IS TRUE AND REMAINS TRUE.** The whole does bound the part; a
bound on the stop-path cost is a valid bound on the haircut's share of it, and
nothing here contradicts that.

> **WHAT IT DID NOT ESTABLISH IS THAT THE WHOLE BOUNDS THE PART UNIFORMLY.**

**THE AMENDMENT IS MADE ON EVIDENCE THAT DID NOT EXIST WHEN THE DECISION WAS
MADE, NOT ON A RE-READING OF EVIDENCE THAT DID.** 4.1b §5 named the condition
under which it would be reopened and routed the question forward; 4.1c produced
the measurement; this document acts on it. **That is the sequence working, not a
change of mind.**

### 2.4 THE COMMITTED THRESHOLD DID NOT FIRE, AND IS NOT OVERRIDDEN

**`docs/design/04_1c_non_uniformity_check.md` §6.1 reports `S_max / R_min` of
0.6020 against a firing level of 1.0. THE TRIGGER DID NOT FIRE.**

**THE CHECK APPLIED ITS THRESHOLD CORRECTLY**, and §4.5 of that document forbade
revising it after the numbers were visible. It did not revise it. **It recorded
the limitation instead, which was the right conduct.**

> **THIS AMENDMENT DOES NOT REST ON THE THRESHOLD HAVING FIRED. IT RESTS ON THE
> STRUCTURAL FINDING THE THRESHOLD WAS INCAPABLE OF TESTING.**

The threshold compared **additive** ranges. The effect is **multiplicatively
constant**. A criterion of that construction cannot register a constant ratio as
decisive, however large the ratio is — §7 logs that as a ledger instance.
**Presenting the threshold as having fired would be false**, and the amendment
does not need it to have.

---

## 3. THE REVISED DENOMINATION

### 3.1 THE DECISION

> ### THE CONSTRAINT IS DENOMINATED IN THE UNVALIDATED TERM'S SHARE: THE STOP
> ### HAIRCUT'S CONTRIBUTION, MEASURED AGAINST THE SAME DENOMINATOR THE PRIOR
> ### RATIO USED.

**THE CHANGE IS TO THE NUMERATOR AND NOT TO WHAT THE RATIO IS TAKEN OVER.**

Stated precisely, and **not solved for a width**:

    numerator    = the stop haircut's per-unit contribution -- the term
                   `src/engine/costs.py:336` adds as `s_stop`, being the stop
                   price multiplied by that symbol's haircut rate

    denominator  = the stop distance, the same `s` the prior ratio was taken
                   over -- the absolute price move from entry to the stop

**THE RELATIONSHIP BETWEEN THE CONSTRAINED RATIO AND THE PROTECTED QUANTITY IS
THEREFORE UNCHANGED IN FORM.** 4.1b §3.2 names the protected quantity as a share
of the risk unit; the constrained ratio is taken over the stop distance, exactly
as the prior ratio was. **Only the numerator narrows.**

### 3.2 WHAT THE FEE TERMS DO NOW

**THEY LEAVE THE CONSTRAINED RATIO. THEY REMAIN IN THE SIZING DENOMINATOR AND IN
THE COST MODEL.**

`src/engine/costs.py:336` is untouched by this amendment. Every position is still
sized against the full stop-path cost; every fee is still charged; the risk unit
is still the stop distance plus **all** of the cost.

> **THIS IS A CHANGE TO WHAT IS CONSTRAINED, NOT TO WHAT IS CHARGED. NO COST IS
> REMOVED FROM THE MODEL BY THIS AMENDMENT.**

**The constraint stops ranging over the fee terms. The position sizing does
not.**

### 3.3 THE FROZEN TOLERANCE DOES NOT CARRY OVER

**`COST_TOLERANCE_R = 0.11` IS A TOLERANCE ON A DIFFERENT RATIO.**

> **A TOLERANCE ON A DIFFERENT RATIO IS A DIFFERENT QUANTITY, AND REUSING THE
> NUMBER WOULD BE A CATEGORY ERROR.**

The figure is named here only as the existing committed parameter under the
**old** denomination. **It is not carried forward, not endorsed, and not
replaced.** No value under the revised denomination is stated anywhere in this
document.

---

## 4. WHETHER 4.1a's GROUNDS SURVIVE

**Several of 4.1a §3.3's grounds were arguments for the stop PATH over the target
path. That is a different question from which TERM within the stop path the
constraint binds**, and they are examined here rather than carried over.

### GROUND (1) — THE RATE ORDERING. **UNAFFECTED, AND NOT LOAD-BEARING HERE.**

It establishes that the stop leg carries the largest exit-leg rate of the three,
and therefore that the **stop path** is the right path. **The revised
denomination is still a stop-path term**, so the ground still holds and still
supports the path.

**IT SAYS NOTHING ABOUT WHICH TERM WITHIN THAT PATH THE CONSTRAINT BINDS**, which
is this amendment's question. **It survives and is silent.**

### GROUND (2) — THE DOMINANCE ARGUMENT. **UNAFFECTED AS TO PATH, AND STRENGTHENED AS TO THIS QUESTION.**

As written it disposed of "one constraint per path" and "the worse of the two" by
showing the stop path bounds the others. **That reasoning is untouched.**

**AND UNDER THE REVISED DENOMINATION IT BECOMES STRONGER, FOR A REASON WORTH
STATING.** 4.1a §2.1 records that the target path carries **no stop haircut**, and
§2.2 records that the time path **carries no haircut** either.

> **THE HAIRCUT IS THE ONLY UNVALIDATED TERM ON ANY OF THE THREE PATHS.**

So a constraint on the haircut's share **bounds the model-error exposure of every
path**, not merely of the one it is charged on — because the other two carry none.
**The bounding property ground (2) relied on survives the narrowing intact.**

### GROUND (3) — THE TIE TO THE RISK UNIT. **SURVIVES IN PART, AND THE PART THAT FAILS WAS ALREADY SUPERSEDED.**

**WHAT SURVIVES:** the denominator is unchanged, and the haircut is a term **in**
the quantity the risk rule is denominated in. `costs.py:336`'s denominator is
still what sizes every position, and the constrained numerator is still one of
its components. **The tie to the risk unit is preserved by constraining a
component of that quantity measured against it.**

**WHAT DOES NOT SURVIVE:** ground (3) as written concluded that constraining the
ratio *"constrains the friction share of the quantity the risk rule is
denominated in"* — **the WHOLE friction share.** Under the revised denomination
the constraint bounds only part of it.

**THAT CLAIM WAS ALREADY SUPERSEDED BEFORE THIS AMENDMENT.**
`docs/design/04_1b_tolerance_and_branch.md` §3.5 narrowed the account: the
friction share is **the mechanism**, and what is protected is **how much of the
risk unit rests on an unvalidated estimate.** Ground (3)'s whole-share phrasing
belonged to the framing 4.1b replaced.

> **THIS IS THE ONE GROUND THAT DOES NOT COME THROUGH WHOLE, AND IT IS RECORDED
> AS SUCH RATHER THAN REPORTED AS SURVIVING.**

### GROUND (4) — BLINDNESS TO THE LEAST-KNOWN TERM. **SURVIVES, AND ITS OWN LOGIC NOW ARGUES FOR THE AMENDMENT.**

Ground (4) argued that **excluding** the haircut would leave the constraint blind
to the largest and least-known term, and that *"a constraint that is precise about
the costs we know and silent about the one we do not is precise in the wrong
place."*

**THE MIRROR CASE IS A CONSTRAINT THAT SEES ONLY THAT TERM. WHAT IS LOST BY
CEASING TO RANGE OVER THE FEE TERMS?**

**Nothing the constraint was protecting.** The fee terms are venue-published
rates; `docs/handoff/31_point_5_closing.md` §5.2 singles out the haircut as the
placeholder and does not so identify them. **They carry no model error, so
ranging over them adds no protection against model error** — which 4.1b §3.2
established is what the constraint is for.

**AND WHAT IS NOT LOST:** the fee terms remain in the sizing denominator (§3.2),
so a change in them still moves the risk unit and is still charged. **A fee
schedule change is an observable event, discoverable by re-reading a published
schedule — not a model error the constraint exists to bound.**

> **GROUND (4)'s PRINCIPLE — BIND WHAT YOU CANNOT VALIDATE — IS THE STRONGEST
> ARGUMENT FOR THE PRIOR DENOMINATION AND, APPLIED SYMMETRICALLY, THE STRONGEST
> ARGUMENT FOR THIS ONE.**

**AND ITS SUPPORTING MEASUREMENT POINTS THE SAME WAY.** Report 28 §9's finding
that **419 of SOLUSDT's 540 tolerance breaches are not floor-bound** — they breach
because of the haircut — is evidence that the haircut is where the constraint's
work already is.

### GROUND (5) — THE FLOOR AS INSTRUMENT. **SURVIVES, AND TIGHTENS.**

The floor sets `s`, which is the denominator of the constrained ratio **and also
the price level at which the stop haircut is charged.** Both remain true under
the revised denomination.

**IT TIGHTENS BECAUSE THE INSTRUMENT AND THE CONSTRAINED TERM NOW MEET
DIRECTLY:** the floor sets the price the haircut is charged on and the distance
it is measured against, with no intervening terms the floor does not control.

### 4.1 THE VERDICT ON THE GROUNDS

**Four survive — (1) silently, (2) strengthened, (4) inverted in this
amendment's favour, (5) tightened. One, (3), comes through in part**, its
whole-share claim having been superseded by 4.1b before this document was
written.

**THE DECISION RESTS ON §2.2's STRUCTURAL FINDING AND ON GROUND (4)'s PRINCIPLE
APPLIED SYMMETRICALLY.** Ground (3)'s partial failure does not undo it, and is
recorded so that a reader can weigh it rather than discover it.

---

## 5. WHAT THIS CHANGE COSTS

### 5.1 THE CONSTRAINT NOW RESTS ON A SINGLE PLACEHOLDER

**`docs/handoff/31_point_5_closing.md` §5.2 records the haircut as a placeholder
rather than a venue-published figure**, which **IS the entire slippage-and-gap
model**, and which **cannot be validated against this data layer** because no
bar's first observed price exists at any resolution.

> **UNDER THE PRIOR DENOMINATION THE PLACEHOLDER WAS A COMPONENT OF THE
> CONSTRAINED QUANTITY. UNDER THIS ONE IT IS THE WHOLE OF IT.**

**THAT IS A REAL COST AND IT IS NOT ARGUED AWAY.** The constraint's numerator is
now a number nobody has measured. The reply that §4's ground (4) supplies — that
the uncertainty is in the world rather than in the choice, and that a constraint
which ranges over exactly-known terms adds no protection — is a reason to accept
the cost, **not a reason to deny it is one.**

### 5.2 THE EXPIRY CONDITION GROWS

`docs/design/04_1b_tolerance_and_branch.md` §3.5 scheduled a re-argument for the
point at which the haircut is measured, noting the rationale would weaken as the
estimate became an observation.

> **UNDER THIS DENOMINATION THE CONSTRAINT'S SOLE INPUT IS REPLACED AT THAT
> MOMENT, NOT MERELY IMPROVED UPON.** The re-argument §3.5 schedules is
> correspondingly larger here than it was under the prior denomination.

**RECORDED AS OWED TO POINT 6**, whose paper trading is the route §5.2 names for
measuring the haircut. **It is not discharged here and no part of it is
anticipated here.**

### 5.3 THE DIRECTION OF CONVENIENCE, UNSOFTENED

> **AT EQUAL PROTECTION THIS DENOMINATION IMPLIES NARROWER FLOORS FOR BTCUSDT AND
> ETHUSDT THAN THE PRIOR ONE.**

The fee terms leave the numerator, and those two symbols carry half SOLUSDT's
haircut rate, so at equal protection on the term that remains they need less
width than the prior ratio demanded of them.

**THAT RELIEVES THE STRATUM-THINNING PRESSURE RECORDED AT REPORT 32 §5.4 FOR TWO
OF THREE SYMBOLS** — the pressure that report identified as the structural fact
its derivation existed to surface.

**THAT IS THE CONVENIENT DIRECTION, AND IT IS STATED HERE RATHER THAN LEFT TO BE
NOTICED.**

- **The decision was made on §2.2's structural finding**, which is categorical and
  concerns the parameter's authority over a distribution, not any width.
- **No width was computed or consulted in reaching it.** None appears in this
  document, and the revised closed form does not exist at this commit.
- **A finding that points toward convenience warrants more scrutiny, not less.**
  §4's examination of the grounds is where that scrutiny was applied, and ground
  (3) is reported as failing in part rather than smoothed over precisely because
  the conclusion is comfortable.

---

## 6. WHAT IS OWED NEXT, AND TO WHOM

### 6.1 THE REVISED CLOSED FORM — A SEPARATE DERIVATION STEP

**NOT THIS DOCUMENT, AND NOT 4.1c-PROPER'S LEVEL-SETTING.** A separate step with
its own commit, as report 32 was separate from 4.1a.

**WHAT IT MUST PRODUCE:**

- **The required floor width as a function of the revised tolerance, per symbol
  and per direction.**
- **Derived from the implementation and not from the algebra in prose**, on the
  method report 32 used and verified.
- **The direction split re-established or shown not to arise.** **IT MUST NOT BE
  ASSUMED TO CARRY OVER.** Report 32 §3.2's split arose because the taker fee and
  the haircut are both charged on the stop price; **the fee terms leaving the
  constrained ratio changes which terms are charged against which price**, and
  whether the split survives that is a question to be answered rather than
  inherited.

### 6.2 WHAT REPORT 32 STILL GOVERNS

> **REPORT 32's CLOSED FORM NO LONGER GOVERNS THE CONSTRAINT. IT IS SUPERSEDED AS
> THE GOVERNING RELATION — IT IS NOT FALSIFIED.**

**It remains the correct relation between the OLD ratio and width**, and **its
verification against `costs.position_size` — a maximum residual of 5.662e-15
across 342 points, report 32 §3.5 — stands.** Its four widths at the frozen
tolerance remain correct facts about that relation, and its derivation of the
figures `docs/handoff/31_point_5_closing.md` §5.1 recorded as unsourced is
unaffected.

**Nothing in report 32 is withdrawn. It answers a question that is no longer the
governing one.**

### 6.3 WHAT 4.1c-PROPER STILL OWES

**The level, the widths, the dominance check named at
`docs/design/04_1a_denomination.md` §4.1, kill condition (d)'s disposition, and
the magnitude threshold.**

> **AND IT CANNOT PROCEED UNTIL THE REVISED DERIVATION EXISTS**, because every one
> of those either is a width or depends on one.

---

## 7. THE LEDGER

### THE TOTAL, READ

**`docs/design/04_1b_tolerance_and_branch.md` §7 states "38 + 1 = 39".** **The
total read is 39**, so the instances below take **(40)** and **(41)**.

### INSTANCE (40)

**A DECISION THRESHOLD CONSTRUCTED AS AN ADDITIVE COMPARISON — A CROSS-SYMBOL
SPREAD AGAINST A WITHIN-CELL RANGE OVER THE PARAMETER GRID — WHEN THE EFFECT IT
WAS BUILT TO DETECT IS MULTIPLICATIVELY CONSTANT.**

**Because the quantity scales with the parameter, the within-cell range grows
with the level while a constant ratio does not.** So the criterion **could not
fire on the effect it existed to test**, at any magnitude of that effect.

**It originated in the instruction that specified the non-uniformity check's
threshold.** **SUB-CLASS: the recurring class applied to a decision criterion** —
written from a mental model of how a quantity behaves rather than from its
behaviour.

### INSTANCE (41)

**VERIFICATION CHECKS SEARCHING RAW SOURCE TEXT FIRED FALSELY AGAINST CLEAN
MODULES TWICE IN ONE STEP** — on a parameter name the module carries **in order to
zero it**, and on a path the module cites **in order to record that it opens
nothing there.** **Both were corrected to run over executable tokens and neither
module was changed.**

> **ONE INSTANCE, NOT TWO.** One defect with two symptoms, following the
> precedent by which errata 1 and 2 were logged as a single instance at
> `docs/handoff/31_point_5_closing.md` §7.2.

**IT IS THE THIRD CONSECUTIVE STEP IN WHICH THIS SHAPE OCCURRED. Instances (37)
and (38) are the first two.**

### THE STANDING VERIFICATION RULE, NOW ADOPTED

> **ANY VERIFICATION CHECK THAT SEARCHES SOURCE TEXT RUNS OVER EXECUTABLE TOKENS
> OR AST NODES, NEVER OVER RAW TEXT.**

**Comments, docstrings and cited paths are content the modules are REQUIRED to
carry** — this project's modules are written to state the prohibitions they obey —
**and a check that cannot distinguish a citation from a violation will demand the
removal of the citation.** That is the remediation the inclusion criterion at
`docs/design/04_1a_denomination.md` §6 names as degrading an otherwise correct
artifact.

**THIS IS ALREADY THE METHOD `tests/test_structural_pass.py` USES**, which strips
comments and docstrings by tokenising before searching. **Adopting it as standing
costs nothing** — the method exists, is committed, and is being re-derived
independently in step after step instead of being reused.

### THE TOTAL

**39 + 2 = 41.**

**No earlier instance is renumbered or recounted**, and the ledger remains
contiguous from (1) to (41).

---

## 8. CHANGE DISCIPLINE

**A CHANGE TO THIS AMENDMENT IS A FURTHER DOCUMENT WITH ITS OWN COMMIT AND AN
EXPLICIT STATEMENT OF WHAT CHANGED AND WHY — NEVER A SILENT EDIT.** It would be
`docs/design/04_1a_denomination_amendment_2.md`.

**A SILENT EDIT IS A CONTAMINATION EVENT.**

> **THIS DOCUMENT'S VALUE, LIKE THAT OF THE DOCUMENT IT AMENDS, RESTS ON ITS
> COMMIT PRECEDING THE DERIVATION OF ANY WIDTH UNDER THE DENOMINATION IT
> DECIDES.**

**AND THE EXPOSURE IS GREATER HERE THAN IT WAS AT 4.1a**, because §5.3 records
that the direction of convenience is known in advance. **A denomination decided
before its widths exist is a decision; the same denomination decided after them
would be a selection**, and only the commit order distinguishes the two.

---

**Committed alone, before any width under the revised denomination has been
derived or evaluated. One denomination re-decided on a categorical finding about
the parameter's authority; five grounds examined and one reported as failing in
part; one cost stated and not argued away; one expiry condition enlarged and
routed to Point 6; two ledger instances logged and one standing verification rule
adopted. No width is stated, no closed form is derived, no tolerance value is
committed, and report 32 is superseded rather than falsified.**
