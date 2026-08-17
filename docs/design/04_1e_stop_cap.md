# THE STOP CAP — DISPOSITION

**Point 4, sub-point 4.1e.** The frozen `stop_max_pct` is recorded. **No
replacement is chosen and no cap value is stated.**

## 0. THE DISPOSITION, STATED FIRST

> ### THE CAP IS WRONG.
>
> ### 0.035 IS NOT SUPPORTED BY EITHER PURPOSE GIVEN FOR IT, AND A COMMITTED
> ### DERIVATION FOR THIS EXACT PARAMETER PUTS IT ABOVE 0.035 IN EVERY ONE OF
> ### TWENTY-SEVEN SYMBOL-FOLD CELLS.

**THIS DOCUMENT THEREFORE STOPS.** It records the finding and does not choose a
replacement. A replacement changes which candidates are clipped and must be
decided on its own, in its own commit, against its own argument.

---

## 1. WHAT THIS DOCUMENT IS

**A PRE-REGISTRATION, FROZEN ON COMMIT**, joining the frozen specification per
`docs/design/04_0_divergence_disposition_amendment_2.md` §2. **Written after
`docs/handoff/38_point_4_stop_cap_audit.md` and citing it throughout.** Committed
alone.

**IT CHANGES NO CODE.** `src/engine/costs.py` is untouched and the value every
caller supplies is unchanged by this document. **A finding that a value is
unsupported is not a change to the value**, and changing it here would be the
replacement §0 defers.

---

## 2. THE GROUNDS

### 2.1 A COMMITTED DERIVATION EXISTS AND 0.035 IS NOT ITS OUTPUT

`src/sweep/grid.py`'s `derived_cap` computes this parameter as
`(m* + 2.5) x P95(ATR%)` over each training fold, per symbol, citing **Appendix H
and Amendment 6**. It is not an incidental helper: it is the rule the sweep
supplies to `CostConfig` for every fold cell.

Report 38 §5.1 evaluates it over nine folds and three symbols: **3.5043 to 7.4709
per cent**, with medians of 4.1128, 4.4556 and 6.6416.

> ### THE FROZEN VALUE OF 3.5000 PER CENT LIES BELOW ALL TWENTY-SEVEN CELLS.

**A parameter with a committed derivation, supplied instead as a constant that
the derivation never produces, is not a derived parameter.**

### 2.2 THE DERIVATION'S OWN STATED INTENT IS MISSED

`derived_cap`'s docstring states what the cap is for: at the top grid point it
binds when ATR% exceeds P95 — **five per cent of bars by construction** — and it
distinguishes that from the superseded form, which *"binds on 50% at the same
point, which is a second stop rule rather than a guard rail."*

Report 38 §5.2, over the 11,384 candidates:

- **At each symbol's median derived cap: 1.66, 3.36 and 4.27 per cent clipped.**
  The intent is met.
- **At the frozen 0.035: 3.13, 9.42 and 38.13 per cent clipped.** On SOLUSDT the
  frozen cap misses the stated intent by **7.6 times**.

> ### AT 38.13 PER CENT ON SOLUSDT THE FROZEN CAP IS DOING WHAT THE DERIVATION'S
> ### OWN DOCSTRING NAMES AS THE THING A CAP MUST NOT DO: ACTING AS A SECOND STOP
> ### RULE RATHER THAN A GUARD RAIL.

### 2.3 NEITHER STATED PURPOSE SUPPORTS IT

**THE GRANULARITY PURPOSE BINDS ONE TO TWO ORDERS OF MAGNITUDE AWAY.** Report 38
§3.3: the minimum lot binds between **49.03 and 538.61 per cent** depending on
symbol and price — **14.0 to 153.9 times the frozen cap.** Nothing about lot
granularity picks out 3.5 per cent.

**THE REACHABILITY PURPOSE RUNS BACKWARDS.** Report 38 §4.2: risk is fixed and the
stop distance divides it, so a narrower stop buys a larger position. On the 1,967
candidates the cap clips, notional at the cap exceeds notional at the ATR-implied
width on **100.00 per cent** of them, median **1.2304 times**, maximum **13.3210
times**.

> ### THE CAP INCREASES NOTIONAL EXPOSURE ON EVERY CANDIDATE IT FIRES ON. IT DOES
> ### NOT LIMIT EXPOSURE TO AN EXTREME MOVE.

Report 38 §4.3 adds that the stop haircut prices a **width-independent** adverse
fill and therefore does not price what the cap is credited with limiting, and that
nothing remains which the cap addresses in the protective direction.

### 2.4 ITS PROVENANCE IS SCAFFOLDING

Report 38 §2.4: 0.035 appears as a literal in nine places and **every one is
scaffolding** — `_UNUSED_SIZING_PARAMS`, `_UNUSED_SWEEP_PARAMS`, `FIXTURE_PARAMS`
commented *"Explicitly-arbitrary values ... not chosen values"*, placeholder dicts
and two README command lines.

**THE 4.1 CHAIN TAKES ITS CAP FROM A DICT WHOSE DOCSTRING SAYS THE VALUE IS NEVER
READ.** It is nonetheless load-bearing: report 38 §2.4 shows that moving it to
0.050 moves the admitted domain's lower bound — committed at
`docs/design/04_1c_pre_commitments.md` §2.1 — from 0.03554692 to 0.02567516.

### 2.5 WHY THIS IS "WRONG" AND NOT "A JUDGEMENT"

**A JUDGEMENT WOULD REQUIRE SOMEONE TO HAVE MADE ONE.** Recording 0.035 as a
judgement would need what
`docs/design/04_1c_proper.md` §2.4 requires of one: what was weighed, what would
have made a different value correct, and who decided. **No committed document
contains any of that**, and this document will not manufacture it retrospectively.
**A value supplied as scaffolding is not a judgement that happens to be
unrecorded; it is not a judgement.**

**AND IT IS NOT MERELY UNDERIVED.** An underived parameter sitting where no
derivation exists would be a gap. **Here a derivation exists, is committed, is
cited to an appendix and an amendment, and produces values that exclude the one in
use.**

---

## 3. THE UNCOMPUTABLE SIDE, STATED EXPLICITLY

> ### WHETHER A STOP CLIPPED NARROWER THAN VOLATILITY IMPLIES IS ITSELF
> ### UNDESIRABLE IS AN OUTCOME QUESTION. IT IS UNASSESSABLE BEFORE THE HOLDOUT
> ### AND IT IS NOT ASSESSED HERE.

`docs/design/04_1c_consequences_and_thresholds.md` §2.4 left it open, argued
nowhere, and expressly declined to characterise it as unimportant. Report 38 §4.4
names it as the uncomputable half of the reachability question.

**EVERY GROUND IN §2 IS COMPUTABLE AND NONE OF THEM TOUCHES IT.** §2.1 and §2.2
compare a constant against a committed rule; §2.3 measures notional and lot
geometry; §2.4 reads provenance.

> ### THE FINDING IS THEREFORE MADE WITHOUT THE OUTCOME SIDE, AND SAYS SO.

**IT IS CONCEIVABLE THAT THE OUTCOME SIDE RESCUES 0.035** — that clipping to a
tight cap turns out to serve the strategy for a reason none of §2's grounds can
see. **Nothing here rules that out**, and §4 is what would establish it.

---

## 4. THE POINT 6 FALSIFIER

> ### WHAT PAPER TRADING WOULD HAVE TO SHOW.

**FOR THE FINDING TO BE OVERTURNED — that is, for 0.035 to be right after all —
paper trading must show BOTH:**

1. **THAT CLIPPED POSITIONS DO NOT SUFFER FROM THEIR LARGER NOTIONAL.** §2.3
   establishes that a clipped position carries up to 13.32 times the notional its
   own volatility implied. If realised adverse excursions on clipped positions are
   no worse per risk unit than on unclipped ones, the exposure argument against
   the cap loses its force.
2. **THAT THE TIGHTER STOP IS NOT PAID FOR IN PREMATURE EXITS AT A RATE THAT
   COSTS MORE THAN THE CAP SAVES.** This is the §3 question and it is the one only
   the holdout or paper trading can answer.

**FOR THE FINDING TO BE CONFIRMED, EITHER LIMB FAILING IS ENOUGH.**

**AND ONE MEASUREMENT WOULD SETTLE §2.1 WITHOUT ANY OUTCOME QUANTITY AT ALL:**
recomputing `derived_cap` on the paper-trading window. **If it again returns values
above 0.035 on every symbol, the constant is excluded by the project's own rule on
fresh data**, and that is a count over ATR percentiles rather than an outcome
figure.

---

## 5. THE CONSEQUENCE FOR THE THESIS

### 5.1 THE GAP

**The thesis specifies an ATR-derived stop** — 2.25 times ATR(14), floored. On the
clipped fraction the effective rule is **a flat percentage of entry**, which is not
an ATR rule and does not vary with volatility at all.

Report 38 §6 counts that fraction at the frozen cap: **17.28 per cent pooled and
38.13 per cent of SOLUSDT**, with worse cells inside the folds.

> ### ON MORE THAN A THIRD OF SOLUSDT's CANDIDATES THE STRATEGY IS NOT RUNNING
> ### THE STOP RULE THE THESIS SPECIFIES.

### 5.2 IT IS RECORDED AND NOT RESOLVED

**RESOLVING IT REQUIRES CHOOSING A CAP**, which §0 defers, or amending the thesis's
stop rule, which is not this document's to do.

**WHAT OWES IT:**

- **THE REPLACEMENT DECISION** — a document choosing a cap value, which must state
  the resulting clipped fraction and therefore the size of this gap under its own
  choice. **It has no owner at this commit.**
- **POINT 4's REMAINING AGENDA ITEM (c)** at
  `docs/handoff/31_point_5_closing.md` §9 — the kill conditions restated for the
  capped population. **A condition stratifying on floor binding while a larger
  fraction is cap-bound is stratifying on the wrong mechanism**, and (c) is where
  that must be faced.

### 5.3 WHAT DOES NOT FOLLOW

**NO PRIOR MEASUREMENT IS WITHDRAWN.** Reports 24, 26, 28, 30, 32, 34, 36 and 37
each measured what they said they measured at the cap they named. **A finding that
a parameter is unsupported is not a finding that measurements taken at it were
performed wrongly.**

---

## 6. THE LEDGER

### 6.1 THE TOTAL, READ

**`docs/design/04_1c_consequences_and_thresholds.md` §5.4 states "44 + 2 = 46".
The total read is 46**, so the instance below takes **(47)**.

### 6.2 INSTANCE (47)

**A PARAMETER STRIPPED OF ITS DEFAULT SO THAT A NUMBER WOULD HAVE TO BE STATED
WHERE IT IS USED WAS THEN SUPPLIED FROM SCAFFOLDING AT EVERY CALL SITE, AND NEVER
STATED AS A CHOSEN VALUE ANYWHERE.**

`src/engine/costs.py`'s module docstring gives Point 3R's reason for removing the
defaults: *"Each was a placeholder that silently acted as a chosen value; a stale
default is exactly the failure 3R exists to correct."*

> **REMOVING THE DEFAULT MOVED THE PLACEHOLDER FROM THE DATACLASS TO THE CALL
> SITES. IT DID NOT ELIMINATE IT.** Every caller now states a number, and every
> number stated is scaffolding.

**ONE INSTANCE, TWO SYMPTOMS**, following the precedent by which
`docs/design/04_1a_denomination_amendment_1.md` §7 logged instance (41):

- **THE PROVENANCE SYMPTOM**, §2.4 above: nine literals, all scaffolding.
- **THE SCOPE SYMPTOM**: `exposure_profile._UNUSED_SIZING_PARAMS`'s docstring
  states the value is **NEVER read**, and its guard —
  `test_the_three_construction_only_parameters_are_never_read` — is scoped to
  `ep.positions` alone. Modules added since take the same config and do read it.
  **The guard is correct and narrow; the claim above it is general and is now
  false.**

**SUB-CLASS: the recurring class applied to a guard's scope** — a claim about a
quantity's reach written from a snapshot of the callers that existed when it was
written, rather than from what the guard actually covers.

**NOT CORRECTED BY EDIT HERE.** This document changes no code. **Narrowing that
docstring to what its guard supports is owed to whoever next touches
`exposure_profile.py`**, and is recorded here so it is not lost.

### 6.3 THE TOTAL

**46 + 1 = 47.**

**No earlier instance is renumbered or recounted**, and the ledger remains
contiguous from (1) to (47).

### 6.4 THE ERRATA INDEX

> ### THIS DOCUMENT CREATES NO ERRATUM.

The `_UNUSED_SIZING_PARAMS` docstring is **source code**, which
`docs/design/04_0_divergence_disposition_amendment_2.md` §2 records as an
implementation of the specification and not a member of it. **The index does not
range over it.**

**THE INDEX STANDS AT TEN IN FACT AGAINST NINE IN ITS OWN TEXT**, per
`docs/design/04_1c_consequences_and_thresholds.md` §5.5, and its next holder
carries ten forward.

---

## 7. WHAT THIS DOCUMENT DOES NOT DO

**IT CHOOSES NO REPLACEMENT CAP AND STATES NO CAP VALUE.** §0.

**IT CHANGES NO CODE.** The engine still clamps at whatever each caller supplies.

**IT WITHDRAWS NO MEASUREMENT.** §5.3.

**IT DOES NOT ASSESS THE OUTCOME SIDE.** §3.

**IT DOES NOT AMEND THE THESIS'S STOP RULE**, and names what owes the gap at §5.2.

---

## 8. CHANGE DISCIPLINE

**A CHANGE TO THIS FINDING IS A NEW DOCUMENT WITH ITS OWN COMMIT AND AN EXPLICIT
STATEMENT OF WHAT CHANGED AND WHY — NEVER A SILENT EDIT.** It would be
`docs/design/04_1e_stop_cap_amendment_1.md`.

**A SILENT EDIT IS A CONTAMINATION EVENT.**

**THE CLAUSE MOST EXPOSED IS §0's REFUSAL TO CHOOSE A REPLACEMENT.** It will first
be inconvenient at the moment a step needs a cap in order to proceed, and the
tempting move will be to adopt whichever value is nearest to hand — most likely
0.035 itself, on the ground that it is what everything was measured at. **That
ground is the one `docs/design/04_0_decision_rule.md` §8 bars**, and an amendment
adopting a cap on it must say so in those words.

---

**Committed alone, changing no code. The frozen stop cap is recorded as WRONG on
four computable grounds: a committed derivation for this parameter exists and
places it above 0.035 in every one of twenty-seven cells; that derivation's stated
intent of a five per cent guard rail is missed by up to 7.6 times; the granularity
purpose binds fourteen to a hundred and fifty-four times further out; and the
reachability purpose runs backwards, the cap increasing notional exposure on every
candidate it clips. Its provenance is scaffolding in every one of nine places. No
replacement is chosen, no cap value is stated, and the outcome side is named as
unassessable with a Point 6 falsifier committed for it. One ledger instance logged
at 46 + 1 = 47; no erratum created. The thesis gap on the clipped fraction is
recorded and routed.**
