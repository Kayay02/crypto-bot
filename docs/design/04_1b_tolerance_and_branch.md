# WHAT THE CONSTRAINT PROTECTS, AND THE BRANCH — PRE-REGISTERED

**Point 4, sub-point 4.1b.** The second of three sequentially committed
documents.

## 1. WHAT THIS DOCUMENT IS

**A PRE-REGISTRATION, FROZEN ON COMMIT.** Made **before any tolerance value is
selected**, **before any floor width is evaluated under the committed
denomination**, and **before any performance figure exists for this thesis.** It
joins the frozen specification on its commit, per
`docs/design/04_0_divergence_disposition_amendment_2.md` §2.

### 1.1 THE ORDER RULE THIS SATISFIES

**`docs/design/04_0_decision_rule.md` §4 requires the justification for the
tolerance to be stated and committed in its own commit BEFORE step 3's curve is
evaluated at any candidate value.** **This document is that justification.**

**The value itself is deferred to 4.1c**, so that the boundary between the
rationale and the number is **a further provable commit** rather than a claim
about which came first inside one document. The split is the same device 4.1a
used and for the same reason.

### 1.2 WHAT IS NOT CLAIMED, AND THIS MATTERS

> **THE ORDER RULE IS A COMMITMENT BARRIER, NOT AN INFORMATION BARRIER.**

**Report 28 §9 and report 32 §3.3 and §3.4 are committed and readable.** The
floor consequences of any tolerance in the region of the frozen value are
therefore **already public**, and this document is **not written as though its
author were ignorant of them.**

**Saying otherwise would be false against artifacts anyone can check.** The guard
is **the commit order** — that the rationale is fixed before a value is chosen —
**and not anyone's ignorance.** A pre-registration whose force depended on
ignorance would be worthless the moment the reader checked the repository; one
whose force depends on commit order survives the check.

**WHAT THIS DOCUMENT DID NOT DO IS CONSULT THE WIDTHS WHILE FORMING THE
ACCOUNT.** §4.3 records the considerations that were excluded, and no floor width
appears anywhere in this document.

---

## 2. WHAT THE CONSTRAINT WAS SUPPOSED TO PROTECT, AND WHY THAT FAILED

**THE ORIGINAL DERIVATION.** `COST_TOLERANCE_R = 0.11` was derived as **one third
of a minimum detectable edge in R**. `docs/handoff/31_point_5_closing.md` §5.1
records that this derivation **presumed costs subtract from the R multiples**.

**UNDER NET-SOLVED GEOMETRY THEY DO NOT.** The stop returns **exactly one risk
unit** and the target **exactly 1.5** by construction, because the target is
solved net of costs. Costs are **contained inside** the R multiples rather than
deducted from them.

### 2.1 THE CONSEQUENCE, STATED PRECISELY

> **COSTS DO NOT REDUCE THE R MULTIPLES. A POSITION'S STOP RETURNS EXACTLY MINUS
> ONE RISK UNIT AND ITS TARGET EXACTLY PLUS 1.5, WHATEVER THE COSTS ARE.**

**Therefore any account of the constraint that depends on costs eroding an edge
measured in R is UNAVAILABLE.** The quantity it would protect does not move.

**AND AN ACCOUNT THAT QUIETLY REINTRODUCES IT UNDER ANOTHER NAME IS THE SAME
ERROR RENAMED.** That is the failure mode §3 is written to avoid, and it is why
§3 interrogates the candidate account rather than adopting it.

---

## 3. INTERROGATING THE CANDIDATE ACCOUNT

**`docs/design/04_1a_denomination.md` §3.1 states that the constraint bounds the
friction share of the risk unit.**

> **THAT WAS FRAMING REQUIRED TO DENOMINATE THE CONSTRAINT. IT WAS NOT A
> RATIONALE DELIVERED.** 4.1a needed some account of what the constraint is for
> in order to choose which path's costs it should be denominated in. **It did not
> establish that the account is correct, and this section does not inherit it.**

### 3.1 IF A LARGE FRICTION SHARE DOES NOT REDUCE THE R MULTIPLES, WHAT DOES IT COST?

**THE FIRST CANDIDATE ANSWER — EXPOSURE TO THE HYPOTHESIS — DOES NOT SURVIVE.**

The argument would run: a larger friction share means a smaller share of the risk
unit is the market move being bet on, so the trade is less an expression of the
hypothesis and more a payment to the venue.

**IT FAILS ON THE SPECIFICATION'S OWN TERMS.** The thesis freezes the
reward-to-risk at **1:1.5 solved NET of costs**. **The specification is already
the net one.** A higher friction share does not distort the executed trade away
from what the thesis specifies — **it is what the thesis specifies, evaluated at
a higher cost.** There is no divergence between the specified and the executed
geometry to protect.

**WHAT DOES GROW IS THE GROSS PRICE MOVE THE TARGET REQUIRES.** Whether a larger
gross move is achieved less often **is an outcome quantity**, and it is
firewalled. **`docs/design/04_0_decision_rule.md` §6 item 3 already ruled that
intuition out of bounds**, and report 32 §5.7 restated it: target distance is on
the ledger as a descriptive scaling identity only.

> **SO THE EXPOSURE ANSWER EITHER DISSOLVES INTO THE SPECIFICATION OR REDUCES TO
> AN OUTCOME CLAIM. EITHER WAY IT IS UNAVAILABLE**, and reaching for it would be
> §2.1's error renamed.

### 3.2 THE ANSWER THAT SURVIVES: HOW MUCH OF THE RISK UNIT RESTS ON AN ESTIMATE

**THE RISK UNIT IS ASSERTED, NOT OBSERVED.** The standing rule is **$20 of risk
after fees and estimated slippage** (`docs/design/00_standing_brief.md` §2), and
the per-unit denominator that delivers it is **the stop distance plus the
stop-path cost.**

**THOSE TWO COMPONENTS HAVE DIFFERENT EPISTEMIC STATUS, AND THAT IS THE WHOLE
POINT:**

- **The stop distance is observable.** It is a price level the exchange will
  honour, on a tick the venue publishes.
- **The stop-path cost is not observed. It is computed from rates**, and
  `docs/handoff/31_point_5_closing.md` §5.2 records that **one of them — the
  haircut, 5 bps on BTCUSDT and ETHUSDT and 10 bps on SOLUSDT — IS the entire
  slippage-and-gap model**, is **a placeholder rather than a venue-published
  figure**, and **cannot be validated against this data layer**, because no bar's
  first observed price exists at any resolution.

> ### THE FRICTION SHARE IS THE FRACTION OF THE RISK UNIT DETERMINED BY ESTIMATE
> ### RATHER THAN BY OBSERVABLE PRICE GEOMETRY.
>
> **AND IT IS THE AMPLIFICATION FACTOR ON ERROR IN THAT ESTIMATE.** The larger
> the cost share, the more a proportional error in the cost model displaces the
> risk unit the standing rule fixes at $20.

### 3.3 THIS IS A DIFFERENT CLAIM FROM THE EXPOSURE ONE, AND IT IS NOT HYPOTHETICAL

**THE TWO CLAIMS ARE ABOUT DIFFERENT THINGS.** The exposure claim is about **what
the trade bets on**. This one is about **how well the project knows what it has
bet** — the reliability of the risk unit, which is the standing brief's own rule
rather than a property of the hypothesis.

**AND THE MECHANISM IS ALREADY INSTANTIATED IN THIS REPOSITORY, MEASURED.**
`docs/handoff/31_point_5_closing.md` §5.3 records the fill-price term: the exit
fee is charged on the stop level while the fill sits a haircut away, and **for
shorts the realised loss lands beyond one risk unit** — *"in the direction the
rule exists to prevent"* — at **at most 0.0033 USDT, under 0.017% of a risk
unit.**

> **THAT IS EXACTLY THIS MECHANISM: A COST-MODEL IMPRECISION DISPLACING THE RISK
> UNIT AND BREACHING THE STANDING RULE.** It is small because the friction share
> is small. **The constraint bounds how large that class of displacement can
> become.**

### 3.4 WHAT THE 419-OF-540 MEASUREMENT IMPLIES

**Report 28 §9 measured 419 of SOLUSDT's 540 tolerance breaches as driven by the
haircut rather than by the floor.**

> **SO THE CONSTRAINT IS, IN PRACTICE, ALREADY ABOUT THE UNVALIDATED TERM.** The
> ratio is denominated in the whole stop-path cost, but **the breaches it flags
> are concentrated in the single term that carries the model error.**

**THAT IS CONFIRMATION FROM COMMITTED MEASUREMENT RATHER THAN FROM ARGUMENT**, and
it is the strongest evidence in this section: the account was reached by asking
what survives net-solved geometry, and the measurement independently points at
the same term.

### 3.5 WHERE THE INTERROGATION LANDS

**IT LANDS NEAR 4.1a's FRAMING BUT NARROWER, AND THE NARROWING IS THE
SUBSTANCE.**

- **4.1a said:** the constraint bounds the friction share of the risk unit.
- **This document says:** the friction share is **the mechanism**; what is
  bounded through it is **how much of the risk unit rests on an unvalidated
  estimate.** The purpose is **the reliability of the risk unit**, not the
  magnitude of the friction as such.

**IT SURVIVED THE INTERROGATION RATHER THAN BEING RESTATED**, and it survived in
a changed form: 4.1a's wording is compatible with the exposure reading, which
§3.1 rejects.

**AND THE ACCOUNT CARRIES AN EXPIRY CONDITION, WHICH IS STATED HERE RATHER THAN
DISCOVERED LATER.** If the haircut were ever measured — Point 6's paper trading is
the route `docs/handoff/31_point_5_closing.md` §5.2 names — **the estimate would
become an observation and this rationale would weaken accordingly.** It does not
follow that the constraint should then be retired; it follows that its
justification would have to be re-argued at that point, and this paragraph is
what makes that a scheduled question rather than an omission.

---

## 4. THE BRANCH CHOICE

### 4.1 THE CHOICE

> ### BRANCH B. A COST-TOLERANCE CONSTRAINT EXISTS.

**THE GROUND.** §3 identifies something the constraint genuinely protects, and it
is not the thing whose loss §2 established: it is **the reliability of the risk
unit against error in the one cost term this project cannot validate.** That is
**the standing brief's own rule**, not a property of the hypothesis, and it does
not reduce to any outcome quantity.

**Branch C is not chosen because the constraint is not vacuous.** Retiring it
would leave the fraction of the risk unit resting on an unvalidated estimate
**unbounded**, at exactly the point in the design where
`docs/handoff/31_point_5_closing.md` §5.2 records that the estimate is the
largest remaining unknown in the exit model.

### 4.2 WHAT BRANCH B DELIVERS, AND WHAT IT DOES NOT

**THE STANDING RATIONALE, as stated at §3.2 to §3.5:** the constraint bounds the
share of the risk unit determined by estimate rather than by observable price
geometry, and thereby bounds how far an error in the unvalidated cost term can
displace the risk unit the standing rule fixes.

> ### AND THE RATIONALE DOES NOT DISCRIMINATE BETWEEN CANDIDATE VALUES STATED IN
> ### THIS RATIO. THIS IS REPORTED AS A RESULT, NOT WORKED AROUND.

**WHY IT DOES NOT.** The account is about **the unvalidated term's** share of the
risk unit. The committed ratio is denominated in **the whole stop-path cost**,
whose numerator carries **the taker fee twice and the haircut once** — report 32
§3.1's form is `2f + e + h`. **The majority of the ratio's magnitude therefore
comes from terms that carry no model error at all.**

**So the ratio bounds the right quantity — conservatively, since the unvalidated
term's share is a component of it — but a particular value of the ratio cannot be
argued FROM the account without converting through that term's share
separately.**

**4.1c THEREFORE OWES A STATED METHOD FOR SETTING THE LEVEL THAT DOES NOT READ IT
OFF THE CURVE.** Naming a value because it yields a comfortable floor is the
failure `docs/design/04_0_decision_rule.md` §4 exists to prevent, and it is not
made permissible by the rationale being unable to name one directly.

**A RATIONALE THAT JUSTIFIES A CONSTRAINT'S EXISTENCE BUT NOT ITS LEVEL IS A REAL
OUTCOME**, and reporting it is preferable to manufacturing a level-discriminating
argument that the interrogation did not produce.

### 4.3 WHAT DID NOT ENTER THE CHOICE

**THE COST OF RE-MEASURING REPORTS 26, 28 AND 30 WAS NOT A CONSIDERATION**, per
`docs/design/04_0_decision_rule.md` §8, which records execution reality over
measurement convenience.

**THE FLOOR WIDTH A BRANCH IMPLIES WAS NOT A CONSIDERATION.** Report 32's widths
are committed and readable, and **no width appears anywhere in this document**.
The choice rests on §3's account, every step of which is available without
knowing any width.

**AND THE DIRECTION OF CONVENIENCE IS RECORDED**, since it runs the same way it
did at 4.1a: **Branch B is the branch that keeps a constraint and therefore
keeps a floor wider than none**, and Branch C would have discharged 4.1c of the
level question entirely.

---

## 5. THE THIRD RESULT — CONSIDERED, AND NOT REACHED

**The fork permits two answers. A third is available**: that the constraint is
worth having, **but that the ratio on the stop path is not the right one to
express it in.** If §3's account is specifically about sensitivity to the
unvalidated haircut, the natural quantity would be **that term's share of the
risk unit** rather than the whole stop-path cost's share — a different ratio,
which would reopen 4.1a under its §8.

**IT WAS CONSIDERED. IT IS NOT REACHED, AND THE REASON IS SPECIFIC.**

**THE UNVALIDATED TERM'S SHARE IS A COMPONENT OF THE COMMITTED RATIO, NOT A
DIFFERENT QUANTITY.** The haircut sits inside the stop-path cost, and both are
charged against the same denominator. **Constraining the whole therefore
constrains the part.** The committed ratio is **a valid and conservative bound on
exactly the quantity §3 identifies** — it is not a bound on something else.

**WHAT IS REACHED IS WEAKER AND IS ALREADY RECORDED AT §4.2:** the committed
ratio is an **indirect parametrisation** of the account. It bounds the right
thing while being dominated in magnitude by terms that carry no model error, so
**the tolerance number cannot be argued from the account directly.**

> **THAT IS A CALIBRATION PROBLEM, NOT A DENOMINATION ERROR**, and it is routed to
> 4.1c as §4.2's obligation rather than reopened against 4.1a.

**THE CONDITION UNDER WHICH IT WOULD BECOME THE THIRD RESULT IS STATED HERE SO
THAT 4.1c CAN RECOGNISE IT:** if 4.1c finds it cannot state a method for setting
the level in this ratio's units **without first computing the unvalidated term's
share and converting through it**, that is evidence the ratio is the wrong
parametrisation, and **`docs/design/04_1a_denomination.md` §8's change discipline
is the route** — a new document, not an edit.

**THE BRANCH IS NOT LEFT OPEN**, because the third result was not reached. Had it
been, this section would say so and §4 would state no choice.

---

## 6. WHAT THIS DOCUMENT DOES NOT DO

- **It commits no value for the tolerance.** The frozen 0.11 is named only as the
  existing committed parameter and as the value whose justification failed; it is
  neither endorsed nor replaced, and no range is stated. **Owed to 4.1c.**
- **It evaluates no floor width.** **Owed to 4.1c.**
- **It does not perform the dominance check named as owed at
  `docs/design/04_1a_denomination.md` §4.1.** **Owed to 4.1c.**
- **It does not dispose of kill condition (d)**, whose per-fold-versus-pooled
  question `docs/handoff/31_point_5_closing.md` §5.9 leaves open. **Owed to
  4.1c.** *(Branch B keeps the floor-bound stratum in existence, so the
  restructuring Branch C would have compelled does not arise; the level question
  remains.)*
- **It sets no magnitude threshold** for the after-costs risk rule. **Owed to
  4.1c.**

---

## 7. THE LEDGER

### THE CURRENT TOTAL, READ

**`docs/design/04_1a_denomination.md` §6 states "37 + 1 = 38".** **The total read
is 38**, so the instance logged below takes **(39)**.

### INSTANCE (39)

**The instruction that produced `docs/design/04_1a_denomination.md` stated in its
verification requirements that the ledger total "stands at 38", while separately
delegating to that document the erratum classification which determines whether
the total is 38 or 39.** **The two requirements are unsatisfiable together**: the
delegated call could not be made freely if its answer was already fixed by the
verification section. **The implementing session reported the tension rather than
resolving it silently**, and 4.1a §5 names the alternative reading and where it
leads.

**SUB-CLASS: internal contradiction between a prompt's own constraints and its
requirements** — the sub-class `docs/handoff/31_point_5_closing.md` §7.2 records
as instances **(23) to (26)**. **This is its third occurrence in Point 4**, after
instances **(33)** and **(35)**.

### THE STANDING DRAFTING RULE, NOW ADOPTED

> **A PROMPT'S VERIFICATION OR STRUCTURAL CONSTRAINTS MUST NEVER PRE-STATE THE
> EXPECTED VALUE OF A QUANTITY WHOSE DETERMINATION THAT SAME PROMPT EXPLICITLY
> DELEGATES.**

**ALL THREE POINT 4 OCCURRENCES SHARE THAT MECHANISM.** Instance (33) required a
verbatim transcription while requiring a phrase inside it to be absent; instance
(35) required a total to be stated as a figure no committed document carried;
instance (39) fixed a total whose value the same prompt delegated. **In each case
a requirement and a constraint referred to the same quantity and disagreed about
who determined it.**

**The rule is stated as a prohibition on the drafting side rather than as a
resolution procedure on the implementing side**, because by the time the
implementing session meets it, both readings are already unsatisfiable and all it
can do is report.

### A REFINEMENT, NOT A NEW INSTANCE

**The quarantine test stated at `docs/design/04_1a_denomination.md` §5 is
corrected to read "was the DEFECTIVE ELEMENT fenced off", not "was the containing
document fenced off".**

**A quarantine covering a figure's PROVENANCE does not automatically cover a
STRUCTURAL CLAIM attached to it.** §5.1 fenced off the four figures as unsourced;
it did not thereby fence off the population label attached to them, which is a
different kind of assertion and was not what the quarantine addressed.

**THE CLASSIFICATION MADE AT 4.1a §5 STANDS** — erratum only — **and only the
criterion's wording is refined.** The label was in fact never relied on, which is
what the classification turned on; the refinement makes the criterion say that
rather than something broader that happens to give the same answer here.

### THE TOTAL

**38 + 1 = 39.**

**No earlier instance is renumbered or recounted**, and the ledger remains
contiguous from (1) to (39).

---

## 8. CHANGE DISCIPLINE

**A CHANGE TO THIS DOCUMENT'S ACCOUNT OR BRANCH CHOICE IS A NEW DOCUMENT WITH ITS
OWN COMMIT AND AN EXPLICIT STATEMENT OF WHAT CHANGED AND WHY — NEVER A SILENT
EDIT.** It would be `docs/design/04_1b_tolerance_and_branch_amendment_1.md`.

**A SILENT EDIT IS A CONTAMINATION EVENT.**

> **THIS DOCUMENT'S VALUE RESTS ON ITS COMMIT PRECEDING THE SELECTION OF ANY
> TOLERANCE VALUE.** The account it states is the thing 4.1c must select from. An
> account revised after a value is on the desk is an account fitted to that
> value, and no reader could distinguish it from one that was not.

**THE ACCOUNT IS THE PART MOST EXPOSED TO LATER PRESSURE**, because §4.2 concedes
that it does not name a level. The temptation at 4.1c will be to widen the
account until it does. **Widening it is a change to this document and requires a
commit that says so.**

---

**Committed alone, before any tolerance value is selected and before any floor
width is evaluated under the committed denomination. One candidate account
rejected, one reached and narrowed, one branch chosen, one honest limitation
reported rather than papered over, one third result considered and declined with
its trigger condition stated, one ledger instance logged and one standing
drafting rule adopted. No value is named, no width is evaluated, and no floor is
recommended.**
