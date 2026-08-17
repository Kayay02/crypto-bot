# THE STOP CAP — ADOPTION

**Point 4, sub-point 4.1g.** One candidate adopted, on
`docs/design/04_1f_cap_requirement.md`'s limbs and
`docs/handoff/39_point_4_cap_candidates.md`'s measurements. **Nothing is
computed.**

## 0. THE ADOPTION

> ### CANDIDATE B IS ADOPTED. THERE IS NO STOP CAP.
>
> ### THE STOP IS THE ATR RULE FLOORED AT THE COST FLOOR, WITH NO UPPER BOUND.

---

## 1. WHAT THIS DOCUMENT IS

**A PRE-REGISTRATION, FROZEN ON COMMIT**, joining the frozen specification per
`docs/design/04_0_divergence_disposition_amendment_2.md` §2. Committed alone.

**IT CHANGES NO CODE.** §5 records what code change the adoption implies and names
it as owed to its own step.

**IT CITES BOTH PRIOR DOCUMENTS AND REINTERPRETS NEITHER.** The requirement is
`ff4b226`; the measurements are `a613f09`.

---

## 2. THE GROUNDS

### 2.1 THE REQUIREMENT'S OWN CONDITIONAL IS MET

`docs/design/04_1f_cap_requirement.md` §3.5 stated it in advance, before any
candidate was measured:

> **"IF NO CANDIDATE IN THE POPULATION IS REFUSED UNDER REMOVAL, THEN NO LIMB OF
> THIS REQUIREMENT REQUIRES A CAP TO EXIST."**

**REPORT 39 §4.3 MEASURES ZERO REFUSALS ACROSS ALL 11,384 CANDIDATES.** Not one
is refused for quantity or for notional. The tightest case is SOLUSDT at twelve
lots and 40.04 of notional, eight times the venue's minimum.

> ### THE ANTECEDENT HOLDS, SO THE CONSEQUENT DOES: NO LIMB REQUIRES A CAP.

**THE CONDITIONAL WAS COMMITTED BEFORE THE MEASUREMENT AND THE MEASUREMENT
SATISFIED IT.** That order is the whole of why this ground is available.

### 2.2 THE LIMB VERDICTS

Report 39 §7:

- **CANDIDATE B: all four limbs pass**, limb 1 vacuously and recorded as such.
- **CANDIDATE C: all four limbs pass.**
- **CANDIDATE A: limb 4 fails on its face**, on 679 candidates clipped under some
  of a symbol's fold caps and not others, against 192 clipped under all of them.

**A AND B ARE THEREFORE NOT ON A LEVEL**, and the choice that needs argument is
between B and C.

### 2.3 WHY B RATHER THAN C

**BOTH SATISFY THE REQUIREMENT. THE REQUIREMENT DOES NOT SETTLE IT**, and this is
where the audit's findings do.

`docs/design/04_1f_cap_requirement.md` §1 dropped both purposes ever offered for a
cap, and it dropped them for reasons that do not merely leave a cap unsupported
but count against one:

- **A CAP INCREASES EXPOSURE TO A VIOLENT MOVE.** Risk is fixed and the stop
  divides it, so clipping buys a larger position — on 100.00 per cent of what it
  clips, median 1.2304 times and maximum 13.3210 times.
- **A CAP CONSUMES LEVERAGE HEADROOM**, pushing every candidate it clips toward
  the bound `leverage_term` exists to protect rather than away from it.
- **A CAP REPLACES THE THESIS'S STOP RULE** on the fraction it clips, which
  `docs/design/04_1e_stop_cap.md` §5.1 recorded as the gap.

> ### C WOULD BUY NOTHING THAT ANY COMMITTED DOCUMENT ASKS FOR, AND WOULD PAY FOR
> ### IT IN ALL THREE OF THOSE COINS ON 2.43 PER CENT OF CANDIDATES.

**THE STRONGEST ARGUMENT FOR C IS STATED AND ANSWERED.** C is a guard rail against
a regime whose volatility exceeds anything in sample — report 39 §4.3's zero
refusals were measured **in sample only**, and out of sample the ATR could be
wider.

**THAT ARGUMENT IS REAL AND IT DOES NOT CARRY**, for a reason about what happens
when it bites: **under B an unviably wide stop produces a REFUSAL, which is a
defined outcome with a reason code, counted and visible.** `sizing.viability`
returns `BELOW_MIN_QTY` or `BELOW_MIN_NOTIONAL` and the position becomes a skip.
**Under C the same candidate is silently clipped instead, and takes a position with
up to thirteen times the notional its volatility implied.** §6 routes the
monitoring obligation that keeps B's failure mode visible.

### 2.4 WHAT IS NOT A GROUND

**THAT THE GOVERNING EXECUTION PATH ALREADY IMPLEMENTS B IS NOT A GROUND FOR
ADOPTING IT.** §4.1 records that it does. `docs/design/04_1f_cap_requirement.md`
§5 bars adopting a candidate because it is already what the code does, in the same
way it bars retaining 0.035 because it is what everything was measured at.

> ### THE FACT IS RECORDED AT §4.1 AS A CONSEQUENCE AND IS NOT USED HERE AS A
> ### REASON. THE GROUNDS ARE §2.1, §2.2 AND §2.3, EVERY ONE OF WHICH WOULD STAND
> ### IF THE CODE CAPPED EVERYWHERE.

---

## 3. THE CLIPPED FRACTION AND THE THESIS GAP

> ### THE CLIPPED FRACTION UNDER THE ADOPTED RULE IS ZERO.

**THE THESIS GAP `docs/design/04_1e_stop_cap.md` §5.1 RECORDED IS CLOSED.** That
section recorded that on 17.28 per cent of candidates pooled, and 38.13 per cent of
SOLUSDT's, the strategy was not running the stop rule the thesis specifies.

**UNDER THIS ADOPTION EVERY CANDIDATE RUNS THE THESIS'S RULE**: the ATR multiple,
floored at the cost floor. **No candidate runs a flat percentage of entry.**

**THE FLOOR IS NOT AFFECTED AND IS NOT A GAP OF THE SAME KIND.** It is derived from
the cost algebra with no free parameter, per
`docs/design/04_0_decision_rule.md` §4's floor-shape commitment, and the thesis
specifies a floor. **What is removed is the upper bound, which the thesis does not
specify.**

---

## 4. THE CONSEQUENCES

### 4.1 THE GOVERNING PATH ALREADY BEHAVES THIS WAY

**`portfolio.size_position` — the execution path
`docs/design/04_1c_path_and_scope.md` §2.1 committed as the risk unit — calls
`sizing.stop_distance`, which is `max(ATR multiple, floor fraction)` and applies NO
UPPER BOUND.** `costs.stop_geometry`, the only function that applies the cap, is
called from `costs.stop_price` and from `src/engine/simulate.py` and from nowhere
else.

**THE 4.1 ANALYSIS CHAIN IS ALSO UNCAPPED**, taking its stop distances from
`sizing.stop_distance` and `exposure_profile.stop_distance`.

> ### SO THE SPECIFICATION HAS BEEN COMMITTING A CAP THAT THE GOVERNING PATH DOES
> ### NOT APPLY. §7 LOGS THAT.

**IT IS RECORDED HERE AS A CONSEQUENCE AND NOT USED AS A GROUND** (§2.4).

### 4.2 THE ADMITTED DOMAIN MOVES AND THE LEVEL REMAINS INSIDE

Report 39 §6: the domain's lower bound moves from **0.03554692** under the frozen
cap to **0.00359143** under removal, taking the widest ATR width the rule reaches
as the binding width. The upper bound is unchanged at 0.40.

> ### THE COMMITTED LEVEL OF 0.10 REMAINS INSIDE THE ADMITTED DOMAIN, AND WITH A
> ### WIDER MARGIN THAN BEFORE.

**THIS IS A CHECK ON THE LEVEL'S POSITION AND NOT A RE-ARGUMENT OF IT.** The
level's ground is the displacement budget at `docs/design/04_1c_proper.md` §2 and
the uncertainty parameter at §3, and neither is touched by any cap.

### 4.3 NO FOLD-DEPENDENCE ARISES

**THE ADOPTED RULE IS NOT FOLD-DEPENDENT.** No fold enters it, so no candidate's
status depends on which fold is asked, and limb 4 passes without disclosure.

> ### 4.2's AGGREGATION RULE THEREFORE INHERITS NO CAP-INDUCED FOLD-DEPENDENCE
> ### FROM THIS DECISION.

**HAD CANDIDATE A BEEN ADOPTED IT WOULD HAVE**, on 679 candidates, and that
consequence is named here so that the absence of it is a recorded fact rather than
an assumption 4.2 would have to make. **The fold-dependence 4.2 must still handle
is the one the fold schedule itself creates** — overlapping training windows, per
that module's own docstring — and this decision adds nothing to it.

### 4.4 THE TWO REJECTION POPULATIONS BECOME INOPERATIVE

`docs/design/04_1c_pre_commitments.md` §3 defined population A as the required
floor exceeding the cap and population B as the raw ATR stop exceeding it, and
`docs/design/04_1c_consequences_and_thresholds.md` §2 narrowed rejection to A and
committed clipping for B.

**WITH NO CAP THERE IS NOTHING FOR EITHER TO EXCEED.** Both categories dissolve:
population A was already empty at every admitted level, and population B becomes
empty by construction.

**THE REJECT-OVER-CLIP RULE IS NOT REPEALED AND IS NOT WRONG.** It is inoperative
while no cap exists, and it would govern again the moment one did. **Recorded so
that a later step reintroducing a cap knows the rule is already committed and does
not re-derive it.**

---

## 5. WHAT CODE CHANGE IS REQUIRED

**THE GOVERNING PATH REQUIRES NONE.** §4.1.

**TWO THINGS REMAIN AND BOTH ARE OWED TO THEIR OWN STEP:**

1. **`src/engine/simulate.py` STILL APPLIES A CAP**, through
   `costs.stop_geometry`. Under this adoption that is a divergence from the
   specification. **Closing it means changing `stop_geometry` or its caller**, and
   `costs.py` is the module reports 24, 26, 27 and 28 all rest on.
2. **`stop_max_pct` REMAINS A REQUIRED `CostConfig` PARAMETER**, read by
   `stop_geometry` and by the analysis modules that compute the admitted domain.
   **Removing it is not a one-line change** and it interacts with the sweep, which
   derives a cap per fold for its own grid.

> ### NEITHER IS MADE HERE. A DECISION DOCUMENT THAT EDITS THE ENGINE IS A
> ### DECISION AND AN IMPLEMENTATION IN ONE COMMIT, WHICH IS THE SEPARATION THIS
> ### PROJECT KEEPS.

**OWED TO A SEPARATE STEP WITH ITS OWN COMMIT.** It has no owner at this commit.

**AND ONE THING THAT IS NOT A CODE CHANGE:** the sweep's `derived_cap` is not
withdrawn. It remains the rule the sweep uses to build its own grid, and this
adoption governs the stop rule rather than the sweep's construction. **Whether the
sweep should still derive a cap it no longer supplies to the engine is a question
for whoever next touches the sweep.**

---

## 6. THE MONITORING OBLIGATION

**§2.3's answer to candidate C rests on B's failure mode being visible**, so the
visibility must be committed rather than assumed.

> ### WHEREVER THE ENGINE RUNS UNDER THIS RULE, THE COUNT OF POSITIONS REFUSED FOR
> ### QUANTITY OR FOR NOTIONAL IS REPORTED, INCLUDING WHEN IT IS ZERO.

**REPORTED AS ZERO RATHER THAN OMITTED**, on
`docs/design/06a_exit_resolution_spec_amendment_1.md` §6.2's treatment of a
zero-valued branch: a count that appears only when non-zero tells a reader nothing
when it is absent.

**IT IS A COUNT AND NOT AN OUTCOME QUANTITY**, so the firewall does not reach it,
and `docs/handoff/31_point_5_closing.md` §9(f)'s first-run diagnostic gate is where
it belongs.

**AND IT IS THE FALSIFIER FOR THIS ADOPTION.** If refusals appear in numbers that
materially shrink the population, the argument at §2.3 has failed on its own terms
and the choice between B and C must be remade.

---

## 7. THE LEDGER

### 7.1 THE TOTAL, READ

**`docs/design/04_1e_stop_cap.md` §6.3 states "46 + 1 = 47". The total read is
47**, so the instance below takes **(48)**.

### 7.2 INSTANCE (48)

**A RULE WAS COMMITTED OVER A MECHANISM THE GOVERNING EXECUTION PATH DOES NOT
IMPLEMENT.**

`docs/design/04_1c_pre_commitments.md` §3 partitioned two rejection populations by
reference to the cap, and
`docs/design/04_1c_consequences_and_thresholds.md` §2 committed that population B
is clipped to it. **The governing path applies no cap** — §4.1 — so neither
population exists there and the clipping rule describes behaviour that path never
performs.

**IT IS THE RECURRING CLASS APPLIED TO A SPECIFICATION:** a rule written from a
mental model of what the implementation does, rather than from which function the
governing path actually calls. **SUB-CLASS: as assigned to instance (43) by
`docs/design/04_1c_denominator_choice.md` §5.5** — the class applied to a
specification rather than to a numerical threshold or a decision criterion.

**IT IS THE SECOND TIME THE SAME TWO-PATH STRUCTURE HAS PRODUCED AN INSTANCE.**
`docs/handoff/35_point_4_1c_denominator_audit.md` established that the repository
carries two cost paths and that statements true of one are false of the other.
**The cap is a third quantity with the same shape, and it was not checked against
the path split when the rule was written.**

**NOT CORRECTED BY EDIT.** Both documents stand; §4.4 records the rule as
inoperative rather than wrong.

### 7.3 THE TOTAL

**47 + 1 = 48.**

**No earlier instance is renumbered or recounted**, and the ledger remains
contiguous from (1) to (48).

### 7.4 THE ERRATA INDEX

> ### THIS DOCUMENT CREATES NO ERRATUM.

`docs/design/04_1c_consequences_and_thresholds.md` §2.1 says clipping is *"what
`src/engine/costs.py` `stop_geometry` already does"*, **which is true of that
function.** It makes no claim about which path calls it. **Nothing in either
document is false**, and §7.2 logs the gap as a defect of scope rather than a
misstatement.

**THE INDEX STANDS AT TEN IN FACT AGAINST NINE IN ITS OWN TEXT**, and its next
holder carries ten forward.

---

## 8. WHAT THIS DOCUMENT DOES NOT DO

**IT CHANGES NO CODE.** §5.

**IT DOES NOT RE-ARGUE THE LEVEL.** §4.2.

**IT DOES NOT WITHDRAW THE SWEEP'S `derived_cap`.** §5.

**IT DOES NOT REPEAL THE REJECT-OVER-CLIP RULE**, which is inoperative rather than
wrong. §4.4.

**IT SETTLES NOTHING ABOUT THE OUTCOME SIDE.** Whether an uncapped stop serves the
strategy is unassessable before the holdout, exactly as
`docs/design/04_1e_stop_cap.md` §3 recorded for the capped case. **The adoption is
made without it, and §6 is what would show it wrong.**

---

## 9. CHANGE DISCIPLINE

**A CHANGE TO THIS ADOPTION IS A NEW DOCUMENT WITH ITS OWN COMMIT AND AN EXPLICIT
STATEMENT OF WHAT CHANGED AND WHY — NEVER A SILENT EDIT.** It would be
`docs/design/04_1g_cap_adoption_amendment_1.md`.

**A SILENT EDIT IS A CONTAMINATION EVENT.**

**THE CLAUSE MOST EXPOSED IS §2.3.** It chooses B over C on an argument about which
failure mode is visible, and it will first be inconvenient if refusals appear out
of sample. **The honest response then is §6's falsifier, not a quiet reintroduction
of a cap**, and an amendment reintroducing one must state that §6 fired and what it
showed.

---

**Committed alone, changing no code. Candidate B adopted: there is no stop cap.
The requirement's own conditional, committed before the measurement, is satisfied
by a measured zero refusals across all 11,384 candidates, so no limb requires a cap
to exist; B passes all four limbs where A fails limb 4 on 679 fold-dependent
candidates; and C is refused on the audit's findings, which count against a cap
rather than merely failing to support one, with its strongest argument stated and
answered on which failure mode stays visible. The clipped fraction is zero and the
thesis gap is closed. The admitted domain's lower bound moves to 0.00359143 and the
committed level remains inside. No fold-dependence arises, so 4.2 inherits none.
That the governing path already behaves this way is recorded as a consequence and
expressly not used as a ground. Two code changes are named as owed to their own
step. One monitoring obligation committed as the adoption's falsifier, and one
ledger instance logged at 47 + 1 = 48.**
