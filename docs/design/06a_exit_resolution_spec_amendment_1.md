# AMENDMENT 1 TO THE EXIT RESOLUTION SPECIFICATION

## 1. HEADER — WHAT CHANGED, AND WHAT IS NOT REVERSED

**This is Amendment 1 to `docs/design/06_exit_resolution_spec.md`, frozen at
commit `6def4cb`.**

**THE FROZEN DOCUMENT IS NOT ALTERED. Not one character.** Document 06 §8 sets
its own procedure and carries document 05b §4.5's escalation clause: *"an
amendment is a new document with a new commit and an explicit statement of what
changed and why; a silent edit is a contamination event."* **The SHA-256 of
document 06 is asserted by test** (§7), so an edit to it fails the suite rather
than passing unnoticed.

> ### NO RULE IN DOCUMENT 06 IS REVERSED.
>
> **E1 through E6 and E9 are untouched.** The resolution is 1m, the stop fills
> on an inclusive touch, the target fills on a trade-through by one tick, the
> stop takes precedence inside a bar, the stop is evaluated across the max-hold
> bar while the time exit is evaluated only at its close, the time exit is
> unchanged from the frozen thesis, and E9's list of what remains convention
> stands exactly as frozen.
>
> **E7 AND E8 ARE MADE DETERMINATE, NOT ALTERED.** Every sentence in document 06
> §5.4, §6 and §8 remains true after this amendment. What changes is that three
> questions those sections leave open — questions on which the text admits more
> than one reading, or none at all — are answered.

**WHAT CHANGED, IN ONE BLOCK.** Three specification gaps, found in review.
**They are gaps, not corrections**: nothing in document 06 is wrong.

| | gap | resolution |
|---|---|---|
| **1** | **E7 does not state whether realised P&L reconciles to the settlements ACTUALLY crossed.** Two readings survive the text: *provisioned only*, under which a stop-out returns exactly −1.0R; and *provisioned then reconciled*, under which sizing reserves three settlements, P&L charges the two typically crossed, and a stop-out returns about −0.993R. §5.4's closing line — *"making losses look slightly worse than they were"* — **entails** the first, and the first is the reading consistent with report 28's exact identity. **But that is an implication inside a cost-disclosure paragraph, not a statement of the rule.** | **E7.1**, §2: **funding is charged at the provisioned count in BOTH sizing and realised P&L. There is no reconciliation.** |
| **2** | **E7 does not state whether funding appears in the TARGET SOLVE.** Report 28 §3.1 solves the target from `(T − entry) − [entry×f + T×m + entry×e] = RR × d`. Funding is a new per-unit cost. If it enters `d` on the right but not the cost bracket on the left, **the stop identity still holds exactly while the target identity silently drifts.** | **E7.2**, §3: **funding appears on BOTH sides — in `d` and in the cost bracket.** |
| **3** | **E8's flag will fire zero times in-sample, and its first real exercise may be out-of-sample.** Report 19 establishes the 1m layer is exactly full for 2022–2024. The holdout window's 1m completeness is **unknown and cannot be checked without opening the seal.** | **E8.1**, §5: **the inertness is stated, reachable-value tests are required, and the flagged fraction must be reported even when it is zero.** |

**A FOURTH ITEM, SMALLER, IS FOLDED IN RATHER THAN SPLIT OUT** (§4): document 06
§6.1's `0.0200R` is a **comparison figure against the frozen budget** and is
**not** the rule for computing the funding term. Both numbers in that
neighbourhood — `0.0200R` and `0.0180R` — are right for their own purpose and
**neither is the way to construct the term.**

**THIS IS THE ONE AMENDMENT DOCUMENT 06 §8 PERMITS**, and every item above is
folded into it for exactly that reason. §8 restates the clause and makes it
binding.

**SCOPE.** This amendment adds to document 06 **§5.4**, **§6** and **§8**. It
supersedes nothing. **NO MEASUREMENT WAS RUN TO WRITE IT** — no market data at
any resolution, no 1m bar, no parquet, no folds, no counts. The 1m seal gap is
5.3.3's work and remains open.

---

## 2. E7.1 — FUNDING IS NOT RECONCILED

### 2.1 THE RULE

> **FUNDING IS CHARGED AT THE PROVISIONED COUNT —
> `FUNDING_SETTLEMENTS_CHARGED = 3` — IN BOTH THE SIZING DENOMINATOR AND
> REALISED P&L. NO RECONCILIATION TO THE SETTLEMENTS ACTUALLY CROSSED IS
> PERFORMED AT ANY POINT.**

Per unit of quantity, `funding_pu = entry_price × FUNDING_RATE_PER_SETTLEMENT ×
FUNDING_SETTLEMENTS_CHARGED`. **The same term appears in the denominator that
sizes the position and in the proceeds that close it.** A position that crosses
two settlements is charged three; a position that crosses three is charged
three; **the charge does not depend on what happened.**

**THIS IS THE READING DOCUMENT 06 §5.4 ENTAILS**, and the amendment states it
rather than leaving it to be inferred. §5.4's closing line — *"a systematic
overcharge concentrated on FAST EXITS … making losses look slightly worse than
they were"* — is only true if the overcharge **survives into the realised
figure**. Under reconciliation it would not: the overcharge would be refunded at
exit and losses would look exactly as bad as they were. **The paragraph is
therefore evidence for the rule, but it is a disclosure of a cost, not a
statement of a convention, and a specification should not have to be
reverse-engineered from its own cost paragraph.**

### 2.2 THE CONSEQUENCE — THE IDENTITIES ARE EXACT, NOT APPROXIMATE

**A STOP EXIT RETURNS EXACTLY −1.0R AND A TARGET EXIT EXACTLY +1.5R.**

The per-unit denominator is `d = s + c + funding_pu`, where `s` is the effective
stop distance and `c` the fee and slippage legs. At the stop, per-unit net
proceeds are `−(s + c + funding_pu) = −d`, which is **exactly** one realised
risk unit. Report 28 §4.2's identity is preserved term for term: **funding
enters `d` and is then paid out of `d`, so it cancels.**

| what is preserved | figure | source |
|---|---|---|
| stop exit | **−1.0R exactly** | report 28 §4.2 |
| target exit | **+1.5R exactly**, up to the tick rounding report 28 already documents as favourable | report 28 §4.2 |
| breakeven win rate | **40.0%** | thesis §5.2 — `1 / (1 + 1.5)` |
| detectable-edge threshold | **53.6%** | thesis §5.2 |

**R REMAINS A FIXED UNIT.** One R is the same quantity for every trade in the
population, decided at entry and never revised.

### 2.3 THE COST, STATED

> **THE TYPICAL POSITION IS OVERCHARGED BY ONE SETTLEMENT.**

Document 06 §6 enumerates the settlement count over all 24 entry hours: **21 of
the 24 cross TWO settlements, and three cross THREE.** Three are charged on all
24. **So on 21 of 24 entry hours the position pays for one settlement it never
crossed** — about **0.0067R** at the 1.50% floor stop (`rate / s`), inside its
own risk unit.

**THAT OVERCHARGE IS ALREADY DISCLOSED IN DOCUMENT 06 §5.4 AND THIS AMENDMENT
DOES NOT CHANGE IT.** The overcharge exists because of E7's charge-at-entry rule,
which is frozen. What this section does is state **which of two readings of §5.4
is operative** — and under the operative reading the overcharge is **never
refunded.**

**THE DIRECTION IS CONSERVATIVE AND IT IS CONCENTRATED.** Fast exits are
disproportionately stop-outs, so the overcharge falls hardest on the losing side.
**Stated here in advance**, on the terms document 05b §5 set for Rule C, so it
cannot later be presented as a discovery.

### 2.4 WHY (i) AND NOT (ii) — THE CHOICE, RECORDED

**READING (ii) IS MORE FAITHFUL TO CASH FLOW.** It charges what was paid, when it
was paid. That is a real virtue and it is why the reading survives the text at
all. **It is rejected on two grounds, both stated.**

| | reading (i) — **adopted** | reading (ii) — rejected |
|---|---|---|
| stop exit | **−1.0R exactly** | **≈ −0.993R**, and the exact value depends on the entry hour |
| target exit | **+1.5R exactly** | **≈ +1.507R**, likewise entry-hour dependent |
| breakeven | **40.0%**, the frozen figure | **≈ 39.7%** — `0.9933 / 2.5` |
| is R a fixed unit? | **yes** | **no** — every R multiple depends on when the trade opened |

**THE SECOND ROW OF THAT TABLE IS THE ONE THAT DECIDES IT.** Under (ii) the risk
unit is no longer a property of the position; it is a property of the position
**and the hour it was opened**. Two identical trades entered at 07:00 and 09:00
would report different R multiples for the same price path. **A unit that varies
with the clock is not a unit**, and every aggregate computed over it — the
breakeven comparison, the detectable-edge arithmetic, the whole of thesis §5.2 —
would be an average over a quantity whose denominator moved.

**AND THE FROZEN ARITHMETIC WOULD MOVE.** 40.0% becomes about 39.7%. That is a
small shift and it is in the *favourable* direction, which is precisely why it
deserves suspicion: **a specification choice that quietly makes a frozen
threshold easier to clear is the kind of change that must be made deliberately
and in the open, or not at all.** Made here, in the open, the answer is not at
all.

> **THE CHOICE IS FOR DETERMINACY OF THE RISK UNIT, AND THE FAITHFULNESS IT
> GIVES UP IS NAMED RATHER THAN HIDDEN.** Reading (i) charges money that was
> never paid, on 21 of 24 entry hours. That is a real inaccuracy in the cash
> account, it is stated in §2.3, and it is accepted so that R stays fixed.

---

## 3. E7.2 — FUNDING APPEARS ON BOTH SIDES OF THE TARGET SOLVE

### 3.1 THE RULE

> **`funding_pu` APPEARS IN THE TARGET COST BRACKET AND IN THE DENOMINATOR
> `d`. BOTH. NOT ONE.**

Writing `funding_pu = entry_price × FUNDING_RATE_PER_SETTLEMENT ×
FUNDING_SETTLEMENTS_CHARGED`, the target condition is

    long    (T − entry) − [ entry × f + T × m + entry × e + funding_pu ]  =  RR × d
    short   (entry − T) − [ entry × f + T × m + entry × e + funding_pu ]  =  RR × d

with `f` the entry taker fee, `m` the **exit maker** fee, `e` the entry
slippage, `RR = 1.5`, and **`d` — the per-unit risk denominator — ALSO including
`funding_pu`**. Solving:

    long    T = ( RR × d + funding_pu + entry × (1 + f + e) ) / (1 − m)
    short   T = ( entry × (1 − f − e) − RR × d − funding_pu ) / (1 + m)

**This is report 28 §3.1's solve with one term added in two places.** Nothing
else about it changes: the exit leg is still maker, `RR` is still supplied
explicitly and never read from `CostConfig`, and the target is still rounded away
from entry onto the price tick.

### 3.2 THE FAILURE THIS PREVENTS

> **FUNDING IN `d` ALONE LEAVES THE STOP IDENTITY EXACT AND SILENTLY BREAKS THE
> TARGET IDENTITY.**

The stop identity survives because `d` is both what sizes the position and what
is lost at the stop — adding a term to `d` adds it to both sides at once. **The
target identity does not have that property.** If `funding_pu` is in `d` but not
in the cost bracket, the solve returns a `T` at which realised net proceeds are
`RR × d − funding_pu`, so the trade returns

    1.5R − funding_pu / d   ≈   1.5R − 0.018R   ≈   1.482R

**MEASURED ON SYNTHETIC REFERENCE INPUTS**, three symbols × two directions at a
floored quantity and a floor-bound stop, the defective form lands at **1.4823R
to 1.4829R** while the specified form returns **1.5R to 1e-12 relative.**

**THE ERROR IS INVISIBLE WITHOUT LOOKING FOR IT.** It is 1.2% of the reward,
below the noise of anything an implementer would eyeball, it produces no
exception, it moves no price by a visible amount, **and the stop identity — the
one an implementer would check first, because it is the one the risk rule turns
on — keeps passing.** A suite that asserted only the stop identity would report
green.

**THAT IS WHY IT IS SPECIFIED RATHER THAN LEFT TO IMPLEMENTATION**, and why the
two forms are made **distinguishable by test**: the defective solve is
constructed deliberately in `tests/test_exit_spec.py` and asserted to **miss**
1.5R, so a future implementation that omits the term fails loudly instead of
returning a slightly smaller number forever.

### 3.3 QUANTITY INVARIANCE IS PRESERVED — ASSERTED, NOT ASSUMED

**`funding_pu` DEPENDS ON ENTRY PRICE, RATE AND COUNT. IT DOES NOT DEPEND ON
QUANTITY.** It is therefore a per-unit price-space term exactly like the fee and
slippage legs, it cancels from both sides of the solve exactly as they do, and
**report 28 §3.2's central result stands unchanged: the target price is invariant
to the quantity.**

> **THIS IS ASSERTED, NOT ASSUMED.** Report 28's central test is re-run with
> funding present: the same position sized at a **tenfold different risk unit**
> — quantities 10× apart, both floored — is required to produce an **identical
> target price.** It does, on all three symbols and both directions.

**The reason this needs its own assertion** is that `funding_pu` is the first
cost term added to the solve since the invariance was established, and a term
introduced as a *dollar* charge rather than a *per-unit price* charge would
break the invariance while looking correct in every other respect — reinstating
the exact defect report 28 exists to fix.

---

## 4. E7.3 — FUNDING ENTERS THE DENOMINATOR BY CONSTRUCTION

### 4.1 THE RULE

> **`funding_pu` IS COMPUTED FROM ENTRY PRICE, RATE AND COUNT:**
>
>     funding_pu = entry_price × FUNDING_RATE_PER_SETTLEMENT × FUNDING_SETTLEMENTS_CHARGED
>
> **IT IS NOT DERIVED FROM, BACK-SOLVED FROM, OR CROSS-CHECKED AGAINST ANY
> R-SHARE FIGURE.**

Three inputs, one multiplication, no reference to the stop distance and no
reference to the risk unit. **The term is a price, per unit, like every other
term in `d`.**

### 4.2 IN PARTICULAR, DO NOT USE 0.0200R

**Document 06 §6.1 computes**

    funding_in_R = rate × n / s = 0.0001 × 3 / 0.0150 = 0.0200R   ≤   0.022R

**and that computation is correct for what it does**: it reproduces thesis §5.3's
own derivation form so the charge can be compared against the frozen funding
budget on the budget's own terms. **It is a comparison, and §6.1 says so.**

**IT IS NOT A CONSTRUCTION RULE, FOR TWO REASONS.**

1. **IT IS THE SHARE OF THE STOP TERM, NOT OF THE RISK UNIT.** The realised share
   of the risk unit is `rate × n / (s + c)` — about **0.0180R** — **because the
   risk unit includes costs.** The two differ by the cost ratio `c/s`, which
   report 28 §9 measured across the population with a median of 0.0878 and a
   maximum of 0.1483.
2. **IT IS PINNED TO THE FLOOR STOP.** `0.0200R` is `rate × n / s` evaluated at
   `s = 1.50% of entry`. **At any other stop it is simply the wrong number**, and
   the stop is floor-bound on only 2,927 of 11,384 candidate positions (report 28
   §9).

> ### THE TRAP IS REAL, AND IT IS WORTH SHOWING RATHER THAN ASSERTING.
>
> **AT THE FLOOR STOP, `0.0200 × s` EQUALS `funding_pu` EXACTLY.** On the BTCUSDT
> synthetic reference at entry 30,000 with a floor-bound stop: `0.0200 × 450.00 =
> 9.00` and `30,000 × 0.0001 × 3 = 9.00`. **The back-solve and the construction
> agree, so an implementation that used the back-solve would pass any test
> written at the floor.**
>
> **AWAY FROM THE FLOOR THEY DIVERGE IMMEDIATELY.** The same entry with an
> ATR-bound stop of 675.00 gives `0.0200 × 675.00 = 13.50` against a true
> `funding_pu` of **9.00** — **50% too large**, on the 74% of positions that are
> not floor-bound.

**BOTH NUMBERS ARE RIGHT FOR THEIR OWN PURPOSE AND NEITHER IS THE WAY TO COMPUTE
THE TERM.** `0.0200R` answers *"does the charge fit inside thesis §5.3's
budget?"*; `0.0180R` answers *"what fraction of a realised risk unit is
funding?"* — and it is the figure §3.2's drift is expressed in. **Neither answers
*"what is the per-unit funding cost of this position?"*, which has only one
correct answer and it is `entry × rate × count`.**

**A TEST ASSERTS THE DISTINCTION**: `funding_pu` is required to equal
`entry × rate × count`, and required **not** to equal `0.0200 × s` or
`0.0180 × d` on a non-floor-bound reference position, **so the construction rule
and the comparison figures cannot be confused by a future implementation.**

---

## 5. E8.1 — THE MISSING-BAR RULE IS INERT IN-SAMPLE

### 5.1 THE FLAG WILL FIRE ZERO TIMES DURING VALIDATION

**Report 19 (`74e3ca9`) established this directly on the derived layer**, and
document 06 §8.1 already cites it: the 1m layer is **exactly full** over
2022-01-01 to 2024-12-31.

| | figure |
|---|---|
| 1m rows, pooled | **1,578,240** — exactly `1,096 × 1,440` |
| per symbol, per year | **525,600 / 525,600 / 527,040** on BTCUSDT, ETHUSDT and SOLUSDT |
| buckets dropped | **zero, anywhere** |
| 1m completeness | **100.000% on all three symbols** |

> **THERE ARE NO MISSING 1m BARS IN THE MEASUREMENT WINDOW, SO E8's FLAG WILL
> FIRE ZERO TIMES DURING VALIDATION.** The flagged fraction 5.3.4 reports will be
> **0.0000%**, and that is a fact about the data, not about the rule.

**NOTHING HERE RE-MEASURES IT. The figures are cited from report 19, and no 1m
bar is read to write this amendment.**

### 5.2 AND THE HOLDOUT'S 1m COMPLETENESS IS UNKNOWN

> **THE HOLDOUT WINDOW HAS NEVER BEEN EXAMINED FOR 1m COMPLETENESS, AND IT
> CANNOT BE EXAMINED WITHOUT OPENING THE SEAL. EXAMINING IT IS OPENING IT.**

**E8 IS THEREFORE THE ONE CONVENTION IN DOCUMENT 06 WHOSE FIRST REAL EXERCISE MAY
OCCUR OUT OF SAMPLE.** Every other rule in the specification will have decided
thousands of in-sample positions before the holdout is touched, and their
frequencies will be known quantities by then. **E8's will be a number nobody has
ever seen, arriving in the one window where a surprise cannot be absorbed by
revising anything**, because revising a convention after the holdout is open is
choosing it with the holdout in view.

**THIS IS NOT A REASON TO CHOOSE A DIFFERENT CONVENTION NOW.** Document 06 §8's
argument for flagging over any fill convention is unchanged and this amendment
does not touch it. **It is a reason to make the branch impossible to overlook**,
which is what §5.3 requires.

### 5.3 WHAT IS REQUIRED — THE DOCUMENT 05 §4 TREATMENT, IN FULL

**E8 IS AN INERT BRANCH AND IT GETS THE TREATMENT THIS PROJECT GIVES INERT
BRANCHES:** specified, documented as unreachable at present values, **and
carrying tests that exercise it at values where it IS reachable.** Document 05 §4
set it for the partial-allocation branch and report 28 §6.3 followed it for the
viability predicate.

**THE PRECEDENT THAT MAKES THIS NON-NEGOTIABLE IS `MAKER_NONFILL_COST_R`** — the
closing record §5.2's term in the wrong denomination, **invisible to all 545
tests then in the suite because every one of them multiplied it by zero.** A
branch that no test reaches is a branch nobody can tell was ever checked, and a
constant multiplied by zero in every test is a constant with no test at all.

**THREE REQUIREMENTS, BINDING ON 5.3.4:**

1. **REACHABLE-VALUE TESTS.** E8 must carry tests that exercise it on a
   **synthetic 1m series with deliberate holes** inside a position's open
   interval — asserting that the flag is **set** and that the **missing-bar count
   is correct** — and a complete synthetic series asserting the flag is **clear**.
   The series are hand-built integer timestamps. **No market data of any
   resolution is involved, and the 1m seal is not touched to satisfy this.**
2. **5.3.4 MUST REPORT THE FLAGGED FRACTION EVEN WHEN IT IS ZERO.** Report 28
   §6.2's rule applies verbatim: *"REPORTED AS ZERO RATHER THAN OMITTED. A branch
   that is never reported is a branch nobody can tell was checked."*
3. **ANY OUT-OF-SAMPLE RUN MUST REPORT IT SEPARATELY.** The holdout's flagged
   fraction is reported **as its own figure**, never pooled with the in-sample
   zero. **A non-zero figure in the holdout must be visible immediately rather
   than inferred later** from a pooled average that a zero denominator of missing
   bars would otherwise hide.

**WHAT IS NOT DECIDED HERE.** Document 06 §8's deferral stands: **if the holdout's
flagged fraction turns out to be material, the convention is reconsidered THEN**,
against a known frequency — and, per §8 of this amendment, by re-specification
rather than by a second amendment.

---

## 6. THE CONSTANTS

Added to `src/risk/exit_spec.py`. **Values only — no logic.** A test parses them
out of this document and requires equality with the module.

```
FUNDING_REALISED_TREATMENT  = "provisioned_not_reconciled"
FUNDING_IN_TARGET_SOLVE     = True
MISSING_BAR_INERT_IN_SAMPLE = True
```

**NO EXISTING CONSTANT CHANGES VALUE.** `FUNDING_CHARGED` remains
`"in_sizing_denominator_at_entry"`, `FUNDING_SETTLEMENTS_CHARGED` remains `3`,
`FUNDING_RATE_PER_SETTLEMENT` remains `0.0001`, `MISSING_BAR_RULE` remains
`"flag_and_count"`, and document 06 §10's canonical block is untouched — **a test
asserts that block still carries exactly its eleven original names.**

### 6.1 A GUARD FIRED WHILE THIS WAS BEING WRITTEN, AND IT FIRED CORRECTLY

**The first constant was to be named `FUNDING_PNL_TREATMENT`.** The twelve-name
performance firewall is an **AST guard over identifiers**, and its list includes
the bare token `pnl` — a deliberate broadening of the documents' `net_pnl` and
`gross_pnl`. **The name tripped it.**

> **THE NAME WAS CHANGED, NOT THE GUARD.** `FUNDING_REALISED_TREATMENT` carries
> the same meaning — how funding is treated in realised P&L — and contains none
> of the twelve, so the firewall remains **unconditional and allowlist-free.**

**Recorded because the alternative was available and tempting**, and because
report 28 §11.1 recorded the identical event for the identical reason: adding the
identifier to an exemption would have passed the suite and quietly turned an
unconditional assertion into one with a carve-out. **The constant names no
performance quantity; the guard is lexical by design; and a lexical guard that
starts accepting arguments about intent is no longer a guard.**

---

## 7. DOCUMENTS 06, 05, 05a AND 05b ARE UNMODIFIED

**NOT ONE CHARACTER OF ANY OF THE FOUR.**

| document | commit | SHA-256 |
|---|---|---|
| `docs/design/06_exit_resolution_spec.md` | **`6def4cb`** | `773bbafe94ba136c9bddbdc443284af96c021eb4e0894677438e0cb7622f71a0` |
| `docs/design/05_aggregate_risk_budget.md` | **`a323237`** | `d5ac7bd61323d04e75a854baf14086932470175408f5e2db4ca6f4d3afad268f` |
| `docs/design/05a_aggregate_risk_budget_amendment_1.md` | **`62c2d2b`** | `50da5aed3fabb86c3c7b54b41642444e50c7a7790de8dc93ab401ab53071522c` |
| `docs/design/05b_aggregate_risk_budget_amendment_2.md` | **`46099a2`** | `1d115df2272a4e231da41afbbd0b7c82020d0092ec2b3b483062d57c0e95f7bd` |

**ALL FOUR VALUES ARE ASSERTED BY TEST, AND EACH TEST MUST FAIL IF THE FILE EVER
DIFFERS.**

**THIS AMENDMENT SUPERSEDES NOTHING.** It does not touch document 06 §2's
resolution verdict, §3's stop fill rule or its inherited-weakness disclosure,
§4's trade-through rule or its stated conservatism, §5.1–§5.3's precedence and
time-exit rules, §6's settlement enumeration, §7's venue retrieval, §9's
convention list, or §10's canonical constants block. **Nor does it touch document
05's budget derivation, Amendment 1's Rules A and B, or Amendment 2's Rule C** —
no rule in the budget chain is read differently because of anything here.

**Read together, the exit specification as amended is:** document 06 at
`6def4cb`, with **§5.4** extended by E7.1, E7.2 and E7.3 and **§8** extended by
E8.1.

---

## 8. THE ESCALATION CLAUSE, RESTATED AND NOW BINDING

Document 06 §8 carries document 05b §4.5's clause. **It is restated here in the
first person of the document it now binds:**

> **THIS IS THE ONE AMENDMENT DOCUMENT 06 §8 PERMITS.**
>
> **IF A FURTHER GAP EMERGES IN THE EXIT SPECIFICATION, THE CORRECT RESPONSE IS
> TO RE-SPECIFY THE WHOLE DOCUMENT IN ONE PIECE — NOT TO WRITE AMENDMENT 2.**

**The re-specification would be written at the granularity of the exit-evaluation
loop** — a full statement of what happens as each 1m bar is examined, in order,
once — as a **new pre-registration with its own commit**, superseding document 06
and this amendment together, rather than accumulating a third document onto a
chain whose §5.4 would by then be spread across three.

**THREE GAPS IN ONE REVIEW IS ITSELF THE EVIDENCE FOR THE CLAUSE**, and the fact
that all three fell in E7 and E8 — the two rules document 06 states in prose
rather than as predicates — locates where the granularity is wrong. **That is
recorded now, before the second gap, so the decision is a pre-commitment rather
than a judgement made under the pressure of wanting to get on with 5.3.4.**

**THE CLAUSE IS NOT A LICENCE TO SPECIFY BY ACCRETION.** The amendment procedure
exists to prevent silent edits; document 05b §4.5 placed the limit and this
paragraph is where it binds the exit chain.

---

## 9. PRE-REGISTRATION STATEMENT

**THIS AMENDMENT IS COMMITTED BEFORE ANY ENGINE CAPABLE OF EVALUATING AN EXIT
EXISTS.**

**NO WIN RATE, EXPECTANCY, PROFIT FACTOR, SHARPE, SORTINO, EQUITY CURVE,
DRAWDOWN, `r_multiple`, `net_pnl` OR `gross_pnl` FIGURE EXISTS ANYWHERE IN THIS
REPOSITORY AT THIS COMMIT.** Not for this hypothesis and not for any other.
`src/engine/simulate.py` can compute such quantities and **has not been run on
this thesis**; nothing in Points 5.1, 5.2 or 5.3 has produced one.

**NO BACKTEST WAS RUN TO WRITE THIS. NO EXIT WAS EVALUATED AGAINST ANY REAL BAR.
NO 1m BAR WAS READ** — the 1m seal gap is 5.3.3's work and is not yet closed, and
this step does not touch the 1m loader at any point.

**THE R IDENTITIES IN §3.2 WERE VERIFIED ON SYNTHETIC REFERENCE INPUTS ONLY**,
under report 28 §4.1's recorded carve-out and its three conditions — hand-chosen
prices, exactly one named function, and the twelve-name ban otherwise intact.
**No signal, no bar and no real position was involved**, and the arithmetic asks
whether a price *delivers* a given return, never whether it was *reached*.

**THE MODULE THIS AMENDS IMPORTS NOTHING AT ALL**, asserted by AST walk, and is
asserted to import nothing from `src/timeframe`, `src/folds`, `src/analysis`,
`src/engine`, `src/sweep`, `src/regime`, `pandas`, `numpy` or `pyarrow`. **A
module with no imports cannot reach a bar.**

**NOTHING IS WIRED IN.** No engine file imports `src/risk`. **5.3.4 does the
wiring.**

**THE STATE OF THE REPOSITORY AT THE TIME OF WRITING:**

| artifact | commit |
|---|---|
| thesis / amendment 1 | `02e47a5` / `703046a` |
| report 27 — intrabar span | `60b66f5` |
| report 28 — sizing | `df14a68` |
| documents 05 / 05a / 05b | `a323237` / `62c2d2b` / `46099a2` |
| document 06 — exit resolution | `6def4cb` |

**WHAT WOULD FALSIFY THE CLAIM.** A commit at or before this one containing an
outcome figure for this thesis. **There is none, and `git log` is the check.**

**THE THREE RESOLUTIONS WERE NOT CHOSEN WITH REFERENCE TO THEIR EFFECT ON
OUTCOMES**, because no such effect is computable at this commit. Where a choice
had a direction — E7.1's overcharge on 21 of 24 entry hours, and the fact that
the rejected reading would have made the frozen breakeven *easier* to clear —
**the direction is stated in the section that makes the choice**, in advance.

---

## 10. THIS AMENDMENT MAY NOT BE EDITED IN LIGHT OF 5.3.4's RESULTS

**On the terms document 06 §8 and document 05 §11 both set:** a correction is a
**new document with its own commit and an explicit statement of what changed and
why; a silent edit is a contamination event.** And per §8 of this document, a
correction to the exit specification is now a **re-specification**, not a second
amendment.

**IF 5.3.4 REPORTS THAT THE FUNDING OVERCHARGE IS LARGER IN AGGREGATE THAN
EXPECTED, OR THAT THE FLAGGED FRACTION IS NON-ZERO, THAT IS A FINDING — NOT
GROUNDS FOR CHANGING A RULE HERE.** Switching to reconciliation after seeing that
the overcharge cost something would be selecting a P&L convention to improve a
result, which is the precise failure the pre-registration exists to prevent.
**§2.3 states the overcharge's direction and §2.4 states what reconciliation
would do to the breakeven, both in advance, for exactly that reason.**

---

**Committed with `src/risk/exit_spec.py` and `tests/test_exit_spec.py`, and
nothing else. Document 06 stands unaltered at `6def4cb`, and documents 05, 05a
and 05b at `a323237`, `62c2d2b` and `46099a2`; all four SHA-256 values are
asserted by test. No engine file, no backtest, no bar at any resolution, no 1m
access. The commit hash is the proof that these resolutions preceded any engine
that could report what they do.**
