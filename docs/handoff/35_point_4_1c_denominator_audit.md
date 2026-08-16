# Report 35 — the sizing denominator, audited against the code

**Sub-point 4.1c, preparatory. This report settles a composition and decides
nothing.**

It exists because sub-point 4.1c will pre-commit a decision criterion and then
set the cost tolerance's value, and the protected quantity is defined as a share
**of the risk unit**. A criterion pre-committed against a risk unit whose
composition is unsettled is pre-committed against a definition that may move, and
the pre-commitment is then worth nothing.

**THE HEADLINE: THERE ARE TWO DISTINCT PER-UNIT DENOMINATORS AND BOTH DISPUTED
STATEMENTS ARE TRUE, EACH OF A DIFFERENT ONE.** No erratum is owed against either.
What is owed is the consequence: the constraint is denominated in the one that
**does not** contain funding, while the position that actually executes sizes on
the one that **does**.

---

## 1. The denominator, term by term, from the code

The function is `costs.position_size`, `src/engine/costs.py:319`. Its answer is a
quantity; the denominator it divides by is the per-unit all-in loss if the stop is
hit, assembled at `src/engine/costs.py:330-336`:

`denom = move + entry * cfg.taker_fee + stop * cfg.taker_fee + s_entry + s_stop`

### 1.1 The five terms

**TERM 1 — THE PRICE MOVE.** `src/engine/costs.py:332`, `move = (entry - stop) if
direction == LONG else (stop - entry)`. This is the stop distance itself, not a
cost: it is the quantity the other four are measured against. Supplied by the
caller as the gap between two prices. Charged against neither price — it **is**
the difference between them.

**TERM 2 — THE ENTRY TAKER FEE.** `src/engine/costs.py:336`, `entry *
cfg.taker_fee`. The rate is `taker_fee = 0.0006` at `src/engine/costs.py:68`.
**Charged against the ENTRY price.**

**TERM 3 — THE EXIT TAKER FEE ON THE STOP LEG.** `src/engine/costs.py:336`, `stop
* cfg.taker_fee`. Same rate, same line, second occurrence. **Charged against the
STOP price** — that is, against the stop *level*, not against the price the stop
actually fills at. That distinction is the fill-price term of closing record §5.3
and it returns in §3.3 below.

**TERM 4 — THE ENTRY SLIPPAGE.** `src/engine/costs.py:330`, `s_entry = entry *
cfg.entry_slippage_bps / 10_000.0`. The rate is `entry_slippage_bps = 0.0` at
`src/engine/costs.py:71`. **Charged against the ENTRY price.** Frozen at zero, so
it contributes nothing at present values; the field exists so it can be
sensitivity-tested, and `CostConfig`'s own docstring warns against raising it "to
be safe" because the 1m fill convention already absorbs latency.

**TERM 5 — THE STOP-MARKET HAIRCUT.** `src/engine/costs.py:331`, `s_stop = stop *
cfg.haircut_bps(symbol) / 10_000.0`. The rates are `stop_haircut_bps` at
`src/engine/costs.py:73-75` — 5 bps on BTCUSDT, 5 bps on ETHUSDT, 10 bps on
SOLUSDT — reached through `haircut_bps` at `src/engine/costs.py:171`. **Charged
against the STOP price.** It is the only per-symbol term in the denominator.

### 1.2 `sizing.per_unit_denominator` adds nothing

`src/engine/sizing.py:252-267` obtains the same denominator by dividing
`cfg.risk_usd` by `costs.position_size`'s answer, at `src/engine/sizing.py:264`.
Its docstring states the reason: *"REUSED FROM THE ENGINE RATHER THAN
REIMPLEMENTED ... The cost algebra therefore cannot drift from the engine's —
there is only one copy of it and it is `costs.py`'s."* The two therefore carry
term-for-term identical composition, asserted by test.

### 1.3 FUNDING IS NOT AMONG THEM

**The identifying phrase is the denominator line itself**, `src/engine/costs.py:336`
— five addends and no sixth — together with the fact that **no name containing
"funding" is bound anywhere in `src/engine/costs.py`, nor reachable within
`position_size`**. Asserted over the module's AST rather than over its text, per
the standing rule at `docs/design/04_1a_denomination_amendment_1.md` §7.

The maker fee is likewise absent, and is asserted absent by perturbation: raising
`maker_fee` tenfold moves this denominator by exactly nothing. The stop leg is
taker, which is what the denomination decided at `docs/design/04_1a_denomination.md`
§5 requires it to be.

---

## 2. The reconciliation

### 2.1 What each document claims

**REPORT 34 §1.3** states that *"`costs.position_size` carries no funding term at
all"*, and builds the under-inclusiveness finding on it.

**CLOSING RECORD §3.5** states that *"`funding_pu = entry × rate × count`, and the
same term appears in the sizing denominator **and** in the target cost bracket"*.

**DOCUMENT 06a E7.1** states that funding is charged at the provisioned count of
three settlements *"in BOTH sizing and realised"*, with no reconciliation to
settlements actually crossed.

**DOCUMENT 06a E7.2** states that the per-unit funding term appears *"on BOTH
sides of the target solve: in the cost bracket AND in the denominator"*.

### 2.2 THERE ARE TWO COST PATHS, AND EACH STATEMENT IS TRUE OF ONE

**PATH ONE — THE SIZING PATH.** Computed by `costs.position_size`
(`src/engine/costs.py:319`) and reached by `sizing.per_unit_denominator`
(`src/engine/sizing.py:252`). It carries the five terms of §1.1 and **no funding
term**. It is used by `sizing.size`, the exchange-real sizing layer of report 28;
by `src/analysis/sizing_drag.py:177`, which forms `cost_over_stop` from
`sized.denominator`; and by the whole 4.1a / report 33 / report 34 chain.

**PATH TWO — THE PORTFOLIO EXECUTION PATH.** Computed by `portfolio.size_position`
(`src/engine/portfolio.py:269`), whose denominator is assembled at
`src/engine/portfolio.py:298-299` as `sizing.per_unit_denominator(...) +
funding_pu` — **path one plus one term**. The funding term is
`portfolio.funding_per_unit` (`src/engine/portfolio.py:187`), `entry_price *
FUNDING_RATE * FUNDING_COUNT`, with the rate and count read from
`src/risk/exit_spec.py:115` and `:101`. Its matching target solve is
`portfolio.target_with_funding` (`src/engine/portfolio.py:204`), which places the
same term in the cost bracket as well. It is used by the execution path of report
30 and by nothing else.

**SO: REPORT 34 §1.3 IS TRUE OF PATH ONE. CLOSING RECORD §3.5 AND 06a E7.1 AND
E7.2 ARE TRUE OF PATH TWO. ALL FOUR STATEMENTS ARE CORRECT.** The apparent
contradiction was an equivocation on the phrase "the sizing denominator", which
names a different object in the two contexts.

### 2.3 Which path the cost-tolerance constraint is measured against

**PATH ONE — AND THIS IS CITED, NOT INFERRED.**
`docs/design/04_1a_denomination.md` §2.1 defines the stop-path candidate and says
of it: *"This is what the implemented ratio measures — report 32 §2 establishes
it from `src/analysis/sizing_drag.py:177`, `src/engine/sizing.py:264` and
`src/engine/costs.py:336`."* §5 of the same document decides that candidate.
Amendment 1 re-denominated the numerator onto the unvalidated terms' contribution
over the stop distance and left the cost model untouched.

It is also true of the code as it stands: `haircut_floor_curve.py`,
`haircut_share.py` and `haircut_share_rerun.py` each reach the denominator
through `per_unit_denominator` and call neither `size_position` nor
`funding_per_unit`. Asserted over the three modules' ASTs.

### 2.4 NO ERRATUM IS LOGGED, AND THAT IS A FINDING RATHER THAN A COURTESY

No statement in any of the four is false, so none is corrected. **Report 34 §1.3
in particular already named path two explicitly** — it routed the item forward on
the ground that acting on it *"would mean re-deriving the closed form over a
different cost model — the portfolio path's, which per ... E7.2 does carry
funding"*. It identified the two paths correctly and did not conflate them.

**ONE UNRECONCILED TENSION IS LOGGED INSTEAD, AND IT IS NOT AN ERRATUM.**
`docs/design/04_1a_denomination.md` §2.2 states that *"Funding is charged at the
provisioned count in the denominator and in the target cost bracket, on every
position regardless of how it exits"* and that *"The entry leg and funding are
paid on every path"*. §5 of that same document then decides a denomination whose
implemented computation, `src/engine/costs.py:336`, excludes funding. **Both
statements are true and the document does not reconcile them.** The consequence is
live, and it is the under-inclusiveness of §4.3. Recorded here; the document is
not edited.

### 2.5 REPORT 34's §3 FIGURES DO NOT NEED RECOMPUTING AS THINGS STAND

They are measured against path one, which is the denominator the committed
denomination names. **Against the denomination as committed they are correct.**

**WHAT IS TRUE INSTEAD, AND IT IS NOT SMALLER:** path one is not the denominator
the executing position sizes on. Report 34 §3 reports shares of a risk unit that
`portfolio.size_position` does not use.

**IF 4.1c MOVES THE DENOMINATION TO PATH TWO, THE FIGURES MUST BE RECOMPUTED, AND
THE DIRECTION OF THE ERROR IS NOT DETERMINATE WITHOUT 4.1c's OTHER DECISION.**
Writing `U` for the unvalidated sum, `D` for path one's denominator and `F` for
the funding term:

- **If funding enters the denominator only**, the share becomes `U / (D + F)`,
  which is strictly less than `U / D`. **Report 34 §3 would be OVERSTATED.**
- **If funding enters the numerator as well** — which the axiom of §4 says it
  does — the share becomes `(U + F) / (D + F)`, which exceeds `U / D` whenever
  `D > U`. `U` is a proper part of `D` and the move is strictly positive, so
  `D > U` always holds. **Report 34 §3 would be UNDERSTATED.**

**THE TWO BRANCHES POINT IN OPPOSITE DIRECTIONS AND THIS REPORT PICKS NEITHER**,
because the branch is selected by whether the constrained ratio ranges over
funding, and that is 4.1c's decision. No figure is recomputed here under either
branch.

---

## 3. What the risk unit actually is

### 3.1 The standing rule

`docs/design/00_standing_brief.md` §2: *"Risk per trade: never more than 1% (that
is, $20), enforced after fees and estimated slippage."*

### 3.2 What is implemented

**PATH ONE's risk unit** is the price move plus the entry taker fee plus the stop-leg
taker fee plus the entry slippage plus the stop haircut. **PATH TWO's** is all of
that plus provisioned funding.

### 3.3 COSTS PAID OUTSIDE THE RISK UNIT

**TWO, ON PATH ONE. ONE, ON PATH TWO. NEITHER IS A TECHNICALITY.**

**FIRST — FUNDING, ON PATH ONE ONLY.** A position sized on path one pays funding
and its risk unit does not contain it, so a stop-out loses the risk unit **plus
the funding**. **This is not this report's inference; it is the project's own
frozen reasoning.** `src/risk/exit_spec.py:88`, the `FUNDING_CHARGED` docstring,
states it directly: *"the standing risk rule is 'never more than 1%, enforced
after fees and estimated slippage'. Funding is a cost of holding. A trade whose
geometric loss is exactly the risk unit AND which also paid funding has breached
the rule."* That is precisely why path two adds the term. **The repository has
already decided funding belongs inside the risk unit, and path one is the path
that does not have it.**

**SECOND — THE FILL-PRICE FEE RESIDUAL, ON BOTH PATHS.** Term 3 charges the exit
fee against the stop **level** while the fill sits a haircut away from it. Closing
record §5.3 measured this at most 0.0033 USDT across six cells, under 0.017% of a
risk unit, direction-dependent in sign, and — for shorts — **beyond** one risk
unit. It is a known, disclosed, accepted breach of the standing rule.

**WHAT IS *NOT* A BREACH, STATED SO THE LIST IS EXHAUSTIVE.** The maker fee paid on
a target exit is absent from both denominators by design: the denominator is the
loss **if the stop is hit**, so a target-leg cost is not a cost of the risk unit.
Lot flooring moves realised risk **below** nominal and cannot breach the rule
upward. Tick rounding of the stop rounds **away** from entry, widening the stop
and shrinking the position.

### 3.4 The routing

**Both findings go to 4.1c**, and the second one arrives with a question already
open against it. Closing record §5.3 records that the fill-price term was accepted
on magnitude grounds while funding at roughly 0.0067R was rejected on the same
principle, and that *"the only thing distinguishing them is a threshold nobody has
stated."* **This report adds a third item to that list — funding sitting outside
path one's risk unit — and does not state the threshold either.** Adjudication is
not this report's business.

---

## 4. The membership consequence

### 4.1 The axiom

A cost term is **unvalidated** if its magnitude is not fixed by contract or by the
venue's published fee schedule, but is instead estimated, assumed or carried over
from another source.

### 4.2 Every term's membership, with the ground

**THE PRICE MOVE — NOT A COST TERM.** It is the stop distance the costs are
measured against. The axiom does not range over it.

**THE ENTRY TAKER FEE — VALIDATED.** `taker_fee = 0.0006` is Bitget's published
base-tier rate. `src/costs/build_fee_artifact.py:181` records it as retrieved from
the venue and product-level across all 741 USDT-M perpetuals.

**THE STOP-LEG TAKER FEE — VALIDATED AS A RATE, WITH ONE QUALIFICATION.** The same
published rate. The **base** it is charged against is the stop level rather than
the fill, which is the §3.3 residual; that is a defect in the base, not in the
rate's validation status.

**THE ENTRY SLIPPAGE — UNVALIDATED.** A config estimate, `entry_slippage_bps`,
with no venue source. Frozen at 0.0, so it is a member that contributes nothing.

**THE STOP HAIRCUT — UNVALIDATED.** `src/engine/costs.py:72` calls the values
*"Placeholders, per spec"* in the source itself, and closing record §5.2 confirms
they are not venue-published and adds that they cannot be validated against this
data layer at all, because no bar's first observed price exists at any resolution.

**FUNDING, ON PATH TWO — UNVALIDATED, VIA ITS RATE.** `src/risk/exit_spec.py:118`:
*"AN ASSUMPTION, NOT A MEASUREMENT"* — Bitget funding history available to this
project covers roughly 90 days against a three-year window. The **count** of three
settlements is derived rather than assumed, from the frozen time-exit rule, but a
term whose rate is assumed is an assumed term.

### 4.3 THE RESULTING SCOPE, AND THE UNDER-INCLUSIVENESS FINDING

**THE CONSTRAINED RATIO CURRENTLY RANGES OVER TWO UNVALIDATED TERMS: the entry
slippage and the stop haircut.** One of those two is frozen at zero, so the ratio
is in practice carried by the stop haircut alone — which is what report 34 §1.2
found and what makes its cross-symbol result the haircut's structure.

**IT DOES NOT RANGE OVER FUNDING.**

> **THE UNDER-INCLUSIVENESS FINDING, STATED AS ONE.** Funding is unvalidated under
> the axiom; it is inside path two's risk unit by the project's own decision at
> E7.1; and it is outside the constrained ratio. **An unvalidated cost sits inside
> the risk unit the position executes on and outside the constraint that exists to
> bound unvalidated cost.**

**THE MECHANISM IS NOW EXACT.** Report 34 §1.3 reached this from the numerator's
construction — a term absent from the denominator cannot appear in a difference
taken against it. This report locates the cause one level up: **the exclusion is a
property of which path the constraint was denominated in, not of the axiom and
not of the ratio's construction.** Denominating in path one excluded funding as a
side effect of a decision made on other grounds.

**THE CONSTRAINT IS NOT WIDENED HERE.** Whether the constrained ratio should range
over funding, and whether the denomination should move from path one to path two,
are 4.1c's decisions. **This report recommends no side and computes no figure under
either.** The widened ratio's value is not calculated, not estimated, and not
bounded.

---

## 5. What this report does not do

**IT SETS NO TOLERANCE VALUE.** Owed by 4.1c.

**IT DOES NOT SETTLE FLOOR-VERSUS-CAP PRECEDENCE.** Moot on report 33's grid and
live below a tolerance of 0.0296. Owed by 4.1c, per report 34 §5.3.

**IT ADOPTS AND EVALUATES NO DECISION CRITERION.** The criterion committed at
`af7866d` is neither applied nor retuned here, and the ratio-based alternative
report 34 §5.4 recommends is neither adopted nor evaluated. Owed by 4.1c.

**IT RECOMPUTES NO FIGURE FROM REPORTS 32, 33 OR 34.** Whether a recomputation is
needed is settled at §2.5 — not as things stand, and conditionally if the
denomination moves. Owed by whichever step moves it, if one does.

**IT DOES NOT DISPOSE OF KILL CONDITION (d).** Owed by Point 4 proper, per closing
record §9(c), which records that condition (d) additionally needs §5.9's level
decision.

**IT SETS NO MAGNITUDE THRESHOLD.** The question of at what magnitude a breach of
the standing risk rule stops being tolerable is closing record §5.3's, is owed by
Point 4, and now has three items waiting on it rather than two.

### 5.1 Two disclosures about method

**THE PORTFOLIO ENGINE WAS NOT INVOKED.** Path two's composition is established
over the AST of `src/engine/portfolio.py:298-299` rather than by calling
`size_position`. One pure helper, `portfolio.funding_per_unit`, is called in the
tests — three scalars and one multiplication, reading no bar and opening no file.
No exit was resolved, `exit_reason` was not read, and nothing under `data/` was
opened, listed or read.

**NO OUTCOME QUANTITY WAS COMPUTED, INSPECTED OR ESTIMATED**, and no file under
`src/` was modified.

---

## Artifacts

- This report: `docs/handoff/35_point_4_1c_denominator_audit.md`
- Tests, 16 added: `tests/test_denominator_composition.py`
- Audited: `src/engine/costs.py`, `src/engine/sizing.py`, `src/engine/portfolio.py`

**Full suite: 1213 passed** — 1197 before this step, plus the 16 above.
