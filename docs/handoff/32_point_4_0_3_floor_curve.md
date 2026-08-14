# REPORT 32 — THE PARAMETRIC STOP FLOOR

**Point 4, sub-point 4.0, step 3.** A DERIVATION and a MEASUREMENT. No exit is
resolved, no engine is invoked, and no outcome quantity is computed, inspected or
estimated.

**GOVERNED BY `docs/design/04_0_decision_rule.md`**, committed at `77a226bc`
before this step ran. That document is not restated here and is not softened.

> ### NO TOLERANCE VALUE IS SELECTED. NO BRANCH IS PREFERRED. NO FLOOR IS
> ### RECOMMENDED.
>
> This step produces curves. Which point on one governs, or whether any does, is
> sub-point 4.1's decision under step 2B §3's two-way fork, and step 2B §4
> requires the justification to be committed before any candidate value is
> evaluated.

**THE HEADLINE, IN ONE LINE.** The required stop floor has a **closed form** in
the tolerance, **it differs by direction as well as by symbol**, and evaluating it
at the frozen tolerance reproduces **exactly** the four figures
`docs/handoff/31_point_5_closing.md` §5.1 recorded as **supplied but unsourced** —
which are now derived, and whose pairing is now explained.

---

## 1. PROVENANCE

- `git rev-parse HEAD` at build: `12e32a6b` — the tolerance grid, committed alone
  and before the solver existed.
- Derivation module: `src/analysis/floor_curve.py`.
- Tests: `tests/test_floor_curve.py` — path chosen after checking that no file of
  that name existed; §9 records the check.
- Cost algebra: `src/engine/costs.py` and `src/engine/sizing.py`, **read and
  called, never reimplemented**.
- Population: the 11,384 candidate positions, built through report 24's own
  `exposure_profile.positions` on report 21's signal frame.
- Window: 2022-01-05 through 2024-12-31, the window reports 24, 26 and 28 used.

**NOT MODIFIED:** `src/engine/costs.py` · `src/engine/sizing.py` ·
`src/engine/portfolio.py` · `src/risk/` · `src/timeframe/` · every document under
`docs/design/` and `docs/handoff/`.

---

## 2. THE DENOMINATION QUESTION, RESOLVED FROM THE IMPLEMENTATION

**Step 2B §8 anticipated that `c/s <= tolerance` might be under-specified as to
which cost term `c` denominates**, since the stop leg fills taker and the target
leg fills maker, and it required this step to **report and stop** if so.

**IT IS NOT UNDER-SPECIFIED FOR THE RATIO REPORT 28 §9 MEASURED.** The chain is
three links and each was read:

- `src/analysis/sizing_drag.py:177` builds the column as
  `"cost_over_stop": (sized.denominator - stop_span) / stop_span`.
- `src/engine/sizing.py:264` obtains that denominator by dividing the config's
  risk unit by `costs.position_size`.
- `src/engine/costs.py:336` defines it as
  `denom = move + entry * cfg.taker_fee + stop * cfg.taker_fee + s_entry + s_stop`.

**So `c = denom - move` is the entry taker fee, plus the stop-leg taker fee, plus
the entry slippage, plus the stop haircut.**

> **THE MAKER FEE DOES NOT APPEAR IN IT. THE MEASURED RATIO IS THE COST OF THE
> STOP PATH, UNAMBIGUOUSLY.**

**DERIVATION A THEREFORE PROCEEDS**, on that denomination, per step 2B §8's first
limb.

### 2.1 WHAT THAT DOES AND DOES NOT SETTLE

**It settles what was MEASURED. It does not settle what the constraint SHOULD be
denominated in.** Those are different questions and step 2B §8 assigns the second
to 4.1.

**This step derives the floor that enforces a tolerance on the ratio as
measured**, and says so. **It does not decide that the stop path is the right
thing to constrain.** A constraint denominated on the target path, or on the
worse of the two, or one per path, would produce a different curve, and choosing
between them is a specification decision that step 2B §8 places in 4.1's own
commit **before the corresponding widths are evaluated.**

> **SELECTION BY AVAILABILITY IS THE SAME DEFECT AS SELECTION AFTER SIGHT.** This
> report computes one curve because one is what the implemented ratio determines,
> and that fact must not become an argument that the stop-path denomination is
> therefore the correct one.

---

## 3. DERIVATION A — THE PARAMETRIC STOP FLOOR

### 3.1 THE CLOSED FORM

Write the stop width as a fraction `w` of the entry price `P`. The stop price is
`P(1-w)` on a long and `P(1+w)` on a short, and the move is `wP`. Substituting
into `c = denom - move`, with `f` the taker fee, `e` the entry slippage fraction
and `h` the stop haircut fraction:

    long   c = P[(2f + e + h) - w(f + h)]
    short  c = P[(2f + e + h) + w(f + h)]

and `s = wP`, so **`P` cancels exactly** and `c/s` is a function of `w` alone.
Setting `c/s = tau` and solving:

    long   w(tau) = (2f + e + h) / (tau + f + h)
    short  w(tau) = (2f + e + h) / (tau - f - h)

**A CLOSED FORM EXISTS, SO NO NUMERICAL SOLUTION WAS NEEDED.** The committed grid
is used to report and verify the curve, not to solve it.

### 3.2 THE DIRECTION SPLIT, WHICH IS GEOMETRIC AND WAS NOT PREVIOUSLY STATED

> **THE TWO DIRECTIONS DIFFER, AND NOT BY CONVENTION.**

The stop sits **below** entry on a long and **above** it on a short. The taker fee
and the haircut are both charged **on the stop price**, so at the same width they
are **smaller on a long and larger on a short**. **A short needs a wider floor to
meet the same tolerance.**

**THIS EXPLAINS SOMETHING THE PROJECT HAD RECORDED WITHOUT EXPLANATION.**
`docs/handoff/31_point_5_closing.md` §5.1 carries four required-floor figures
supplied to it — two per symbol group — and records them as **unsourced**, with no
account of why there were two. **They are the long and the short leg.**

### 3.3 THE UNSOURCED FIGURES ARE NOW DERIVED

At the frozen tolerance of 0.11, from the closed form and confirmed against
`costs.position_size`:

- **BTCUSDT and ETHUSDT: 1.5302% long, 1.5611% short.**
- **SOLUSDT: 1.9713% long, 2.0295% short.**

**`docs/handoff/31_point_5_closing.md` §5.1's supplied figures were 1.530% /
1.561% and 1.971% / 2.030%.** They agree to every digit those figures carried.

> **THE §5.1 DISPOSITION IS DISCHARGED.** That record required Point 4 to derive
> them from the implementation before relying on them. They are derived, and the
> derivation is verified against the implementation rather than against itself.

**AND THE QUALITATIVE CLAIM §5.1 CITED IS REPRODUCED.** Report 28 §9 states that
SOLUSDT's 10 bps haircut pushes `c/s` above 0.11 at any stop tighter than about
2%. The curve gives SOLUSDT's requirement at 0.11 as **1.9713% long and 2.0295%
short** — which is that statement, in exact form.

### 3.4 THE CURVE ACROSS THE COMMITTED GRID

Required floor width, as a percentage of entry, at selected grid points. BTCUSDT
and ETHUSDT share a curve because they share a haircut; SOLUSDT differs through
that term and through nothing else. Long value first, short second.

- tau 0.020: BTC/ETH 8.0569 and 8.9947; SOL 10.1852 and 11.9565
- tau 0.040: BTC/ETH 4.1363 and 4.3702; SOL 5.2885 and 5.7292
- tau 0.060: BTC/ETH 2.7823 and 2.8862; SOL 3.5714 and 3.7671
- tau 0.080: BTC/ETH 2.0962 and 2.1546; SOL 2.6961 and 2.8061
- tau 0.110: BTC/ETH 1.5302 and 1.5611; SOL 1.9713 and 2.0295
- tau 0.140: BTC/ETH 1.2048 and 1.2239; SOL 1.5537 and 1.5896
- tau 0.200: BTC/ETH 0.8454 and 0.8547; SOL 1.0913 and 1.1089
- tau 0.260: BTC/ETH 0.6511 and 0.6566; SOL 0.8410 and 0.8514
- tau 0.300: BTC/ETH 0.5646 and 0.5688; SOL 0.7294 and 0.7373

**The full 342-row curve — 57 tolerances by three symbols by two directions — is
produced by `floor_curve.floor_curve`.**

### 3.5 VERIFICATION, MONOTONICITY AND THE POLE

**EVERY WIDTH IS FED BACK THROUGH `costs.position_size`** and the resulting `c/s`
required to equal the tolerance it was solved for. **Maximum absolute residual
across all 342 points: 5.662e-15.** The closed form is not trusted; it is checked.

**MONOTONICITY IS VERIFIED, NOT ASSUMED.** All six curves are **strictly
decreasing** in the tolerance across the whole grid, checked by numerical
difference rather than by inspection of the algebra.

**PRICE INVARIANCE IS VERIFIED**, at 30,000, 2,000 and 100 — two orders of
magnitude — with the ratio equal to the tolerance at each.

**THE SHORT FORM HAS A POLE AT `tau = f + h`.** Below it no finite width meets the
tolerance, because widening the stop raises the cost as fast as it raises the
move. The pole sits at **0.0011** on BTCUSDT and ETHUSDT and **0.0016** on
SOLUSDT, both far below the grid's minimum of 0.02, so **no grid point is
affected.** The function returns infinity there rather than a negative width,
which would be a silently wrong answer with the sign flipped.

---

## 4. DERIVATION B — THE MAGNITUDE DOCUMENT 06 §5.4 REJECTED

### 4.1 WHAT §5.4 SAYS

It rejects *"charging funding as a realised cash flow per settlement actually
crossed"*, on the ground that *"it lets a stop-out return worse than −1.0R"*, and
states that such a trade *"would lose the risk unit plus the funding"*. **It
states no numeral.**

### 4.2 WHAT IS DETERMINATE, AND WHAT IS NOT

**THE ABSOLUTE EXCESS IS DETERMINATE FROM THAT SENTENCE.** The loss is the risk
unit **plus the funding actually paid**, so the excess over one risk unit is the
funding actually paid:

    excess_per_unit = entry_price x funding_rate x settlements_crossed

**THE NORMALISATION IS NOT FULLY DETERMINATE, AND THIS REPORT DOES NOT RESOLVE
IT.** Expressing that excess as a fraction of a risk unit needs a denominator, and
**§5.4 does not say whether the rejected treatment also removes the funding term
from the sizing denominator.** Both candidates are reported:

- against the denominator **without** a funding term — the reading §5.4's own
  words support, since the rejected treatment charges funding as a cash flow
  *instead of* inside the denominator;
- against the **adopted** denominator, which includes the provisioned three
  settlements, for the reader who takes the other reading.

> **NEITHER READING IS ADOPTED HERE.** The two differ by **under 2% of each
> other**, so no conclusion that turns on order of magnitude depends on the
> choice — which is why the item proceeds rather than stopping.

### 4.3 THE VALUES, ON REPORT 30 §7.2's REFERENCE CELLS

At the 1.500% floor, funding rate 0.0001, as a percentage of one risk unit. First
figure excludes funding from the denominator, second includes it.

- Two settlements crossed, BTCUSDT: 1.1988% and 1.1776%. Excess 6.0000 per unit.
- Two settlements crossed, ETHUSDT: 1.1988% and 1.1776%. Excess 0.4000 per unit.
- Two settlements crossed, SOLUSDT: 1.1644% and 1.1444%. Excess 0.0200 per unit.
- Three settlements crossed, BTCUSDT: 1.7982% and 1.7664%.
- Three settlements crossed, ETHUSDT: 1.7982% and 1.7664%.
- Three settlements crossed, SOLUSDT: 1.7466% and 1.7166%.

### 4.4 THE COMPARISON 4.1 OWES A CRITERION FOR

**The accepted fill-price term of `docs/handoff/30_point_5_3_4_portfolio.md` §7.3
is at most 0.0033 USDT and under 0.017% of a risk unit.**

**The rejected treatment's excess is between 1.16% and 1.80% of a risk unit** on
the same cells — **roughly seventy times larger at two settlements crossed and
about a hundred times at three.**

> **BOTH BREACH THE SAME RULE IN THE SAME DIRECTION. ONE WAS REFUSED OUTRIGHT AND
> THE OTHER ACCEPTED.**

**AND THE ASYMMETRY IS NOW QUANTIFIED ON BOTH SIDES**, which is what
`docs/design/04_0_divergence_disposition_amendment_2.md` §8 routed here for: a
criterion written against one known magnitude and one unknown one is fitted to
the half of the evidence that happens to be visible. **Both halves are now
visible. The criterion itself is still 4.1's and is not stated here.**

---

## 5. DERIVATION C — STRUCTURAL STRATIFICATION

### 5.1 THE RE-STRATIFICATION, STATED BEFORE ANY FIGURE

> **"FLOOR-BOUND" IS A DIFFERENT PREDICATE HERE THAN IN EVERY PRIOR REPORT.**

Reports 26 and 28 stratified against a **single constant floor of 1.500%**,
identical across symbols and directions. This step stratifies against
**`w(tau)`, which varies by tolerance, by symbol and by direction.**

**THE STEP 2B §6 REFERENCE VALUES AND THE CURVES BELOW ARE NOT DIRECTLY
COMPARABLE AND ARE NOT PRESENTED AS A CONTINUATION OF ONE SERIES.** Where a prior
figure is quoted it is labelled as measured at the constant floor and used for
contrast only.

**THE DEFINITION USED HERE:** a position is floor-bound at tolerance `tau` when
`2.25 x ATR(14) < w(tau) x entry_price`, with `w(tau)` taken for that position's
own symbol and direction. That is `sizing.floor_binds` called with a parametric
floor fraction — the implementation's own predicate, not a second copy.

### 5.2 POOLED, ACROSS THE COMMITTED GRID

Floor-bound percentage, non-floor-bound count of 11,384, and mean granularity
drag as a percentage of nominal risk.

- tau 0.020: 99.67% bound, 37 not bound, drag 2.7172%
- tau 0.040: 94.94% bound, 576 not bound, drag 1.4158%
- tau 0.060: 79.10% bound, 2,379 not bound, drag 1.0228%
- tau 0.080: 57.99% bound, 4,782 not bound, drag 0.8722%
- tau 0.110: 30.83% bound, 7,874 not bound, drag 0.8114%
- tau 0.140: 15.97% bound, 9,566 not bound, drag 0.7890%
- tau 0.200: 5.92% bound, 10,710 not bound, drag 0.7811%
- tau 0.260: 2.57% bound, 11,091 not bound, drag 0.7796%
- tau 0.300: 1.41% bound, 11,223 not bound, drag 0.7796%

**FOR CONTRAST ONLY, AT THE CONSTANT 1.500% FLOOR:** report 26 §4.1 measured
floor binding at **25.71% pooled** and report 28 §8.2 measured drag at **0.8024%
pooled**. The curve's neighbouring values are close because the derived floor at
the frozen tolerance is close to 1.500%, **and the two are still different
predicates.**

### 5.3 PER SYMBOL

Non-floor-bound counts, with the bound percentage in brackets.

- tau 0.060: BTCUSDT 301 (91.94% bound), ETHUSDT 750 (79.81%), SOLUSDT 1,328
  (66.24%)
- tau 0.110: BTCUSDT 1,930 (48.33% bound), ETHUSDT 2,550 (31.36%), SOLUSDT 3,394
  (13.73%)
- tau 0.200: BTCUSDT 3,267 (12.53% bound), ETHUSDT 3,530 (4.98%), SOLUSDT 3,913
  (0.53%)

**THE ORDERING IS STABLE AND IT INVERTS THE HAIRCUT ORDERING.** SOLUSDT needs the
widest floor and yet has the fewest floor-bound positions, because its ATR is
large relative to its price. **The symbol that the cost model penalises most is
the one whose bar geometry is least often at the floor.**

### 5.4 PER FOLD — THE STRATUM A KILL CONDITION DEPENDS ON

Non-floor-bound candidate counts in the thinnest of the eighteen fold periods,
and in fold 4 test specifically, which
`docs/handoff/31_point_5_closing.md` §5.9 identifies as the binding cell.

- tau 0.060: thinnest is fold 3 test at 27 of 843; fold 4 test 36 of 906
- tau 0.110: thinnest is fold 4 test at 216 of 906
- tau 0.200: thinnest is fold 4 test at 623 of 906
- tau 0.300: thinnest is fold 4 test at 809 of 906

> **A TIGHTER TOLERANCE THINS THE STRATUM SEVERELY AND NON-LINEARLY.** At tau
> 0.060 the thinnest fold period retains **27 candidate positions across three
> symbols**. At tau 0.020 the pooled non-floor-bound count over the entire window
> is **37**.

**THAT IS THE STRUCTURAL FACT THIS DERIVATION EXISTS TO SURFACE**, and it is
stated in candidate counts, which are computable, rather than in trade counts,
which are not.

### 5.5 GRANULARITY DRAG IS NOT MONOTONE, AND THE CLAIM IS NOT MADE

**Drag falls from 2.7172% at tau 0.020 to 0.7796% at tau 0.300** — a fall of about
1.94 percentage points — **but it is not monotone.** Twelve of the fifty-six grid
steps show a local rise. **The largest rise is 9.979 parts per million**, and all
twelve lie in the flat tail above tau 0.140 where the ATR binds for most positions
and the floor barely moves.

**THE CAUSE IS LOT QUANTISATION.** Flooring to the lot step is a step function, so
a slightly narrower floor can leave a slightly larger residual for some positions
even as the aggregate falls.

> **MONOTONICITY WAS CHECKED AND FOUND FALSE, SO IT IS NOT CLAIMED.** The floor
> width curve is strictly monotone and is asserted so; the drag curve is not, and
> asserting it would have been a claim the numbers contradict.

### 5.6 WHAT IS NOT COMPUTABLE, AND IS NOT WORKED AROUND

> **THE SAME QUANTITIES ON THE TAKEN POPULATION ARE UNAVAILABLE AT THIS COMMIT.**

`docs/handoff/31_point_5_closing.md` §5.6 establishes that **under the budget with
real exits the traded population is a function of realised outcomes and is not
knowable in advance.** Producing it would require resolving exits, which is an
outcome computation and is firewalled.

**THEREFORE, AND EXPLICITLY:**

- **No stratum thickness is computed on a taken population.**
- **The portfolio engine is not run.**
- **Report 26's per-fold taken counts are not reused as if they described the
  traded population.** Its **495 taken at fold 4 test** was measured under
  **max-hold assumptions** and is **an upper-bound proxy**; it is cited here only
  to locate the candidate figures relative to it, and carries that label wherever
  it appears.

**Every count in §5.2 to §5.4 is a CANDIDATE count** — every signal, before the
budget allocates anything.

### 5.7 TARGET DISTANCE — THE IDENTITY, STATED ONCE

**The target sits at 1.5 times the stop distance in price terms** (thesis §5.2),
so absolute target distance **scales linearly with the floor.**

**THAT IS AN IDENTITY AND IT IS NOT COMPUTED PER TOLERANCE.** Step 2B §6's item 3
justified its place on the ledger with a claim about reward being travelled before
it is collected; **that is an outcome intuition and it is not assessed here.**
Target distance is on the ledger as a **descriptive scaling identity only**, and
nothing in this report says anything about whether a target at any distance is
reached.

---

## 6. FOUR CONTEXT ITEMS, RECORDED AND NOT ACTED ON

**(1) THE ORDER RULE IS A COMMITMENT BARRIER, NOT AN INFORMATION BARRIER.**
Report 28 §9 already establishes publicly that SOLUSDT's haircut pushes `c/s`
above 0.11 at any stop tighter than about 2%. **Nobody is ignorant of the rough
anchor**, and this report does not pretend otherwise. What step 2B §4 forbids is
**selecting a value after seeing the widths**, and the guard is the commit order,
not anyone's ignorance.

**(2) SELECTION BY AVAILABILITY IS THE SAME DEFECT AS SELECTION AFTER SIGHT.**
Step 2B §8's forbidden act is stated as choosing the cost term "after both
candidate floor widths are visible" and does not cover the case where only one is.
**§2.1 above states the point directly**: this report computes one curve because
one is what the implemented ratio determines, and that must not become an argument
that the stop-path denomination is correct.

**(3) THE STEP 2B §6 REFERENCE VALUES ARE NOT COMPARABLE TO THEIR SUCCESSORS.**
Handled in §5.1, before any figure was given.

**(4) TARGET DISTANCE'S JUSTIFICATION IN STEP 2B §6 WAS AN OUTCOME INTUITION.**
Handled in §5.7. The identity stands; the intuition is not repeated.

---

## 7. THE FIREWALL AND THE SEAL

**NO OUTCOME QUANTITY IS COMPUTED, INSPECTED OR ESTIMATED.** Every quantity in
this report is a cost rate, a price distance, a fraction of a risk unit, or a
count of candidate positions. **No exit is resolved. `exit_reason` is not read.
The portfolio engine is not invoked** — asserted over the module's imports and
over every call name in it.

**THE SEAL BARRIER IS ASSERTED IMMEDIATELY BEFORE EACH READ, NOT ONCE PER RUN.**
`candidate_population` calls `assert_paths_unsealed` twice inside its per-symbol
loop — once for the 15m path it opens and once for the 1m allowed set — and an
AST test asserts both calls sit inside the loop rather than before it.

> **REPORT 29 §9.1 RECORDS A BARRIER THAT WAS ARMED, SILENTLY REVERTED MID-RUN,
> AND WAS NEVER RE-CHECKED, AND SIX SEALED PARTITIONS WERE OPENED AS A RESULT.**
> That is why the assertion is per read and why a probe test hands it a sealed
> path and requires it to raise.

**Classification is delegated to `sealed_1m.is_sealed_path`**, the project's
single classifier, rather than to a second copy of the year arithmetic.

**This step reads the 15m layer only.** No 1m partition is opened at all.

---

## 8. A CHECK THAT FIRED FALSELY, RECORDED

**The first version of `test_the_cost_algebra_is_not_reimplemented` searched the
module's raw text for the denominator expression** and failed — **against a clean
module**, because the module **quotes that expression in its docstring in order to
cite it**, which is exactly what the step required.

> **THIS IS THE SHAPE THE DEFECT LEDGER RECORDS AT INSTANCE (37)** — a check
> written from a mental model of what it matches rather than from what it matches.
> It fired twice now in consecutive steps, on the same distinction between a
> citation and a violation.

**The check was corrected to run over executable tokens only**, comments and
docstrings stripped, following `tests/test_structural_pass.py`'s existing method.
**The module was not changed to satisfy it.**

**No ledger instance is added by this report.** The total stands as reconciled at
`docs/design/04_0_divergence_disposition_amendment_2.md` §5 and extended by
`docs/design/04_0_decision_rule.md` §9. **Whether a check that fires falsely
inside a step, is caught, and is corrected before commit constitutes a further
instance is a judgement this report does not make** — it is recorded here so that
whoever next touches the ledger can make it with the fact in view.

---

## 9. VERIFICATION

**THE TEST PATH CHECK, PERFORMED BEFORE ANY TEST FILE WAS WRITTEN.**
`ls -1 tests/` was listed in full and two candidate paths were probed for
existence. `tests/test_floor_curve.py` did not exist and was chosen.
**`tests/test_portfolio.py` — the file a prior step overwrote — was not touched.**

- baseline: **1,124 passing**
- new in `tests/test_floor_curve.py`: **+23**
- total: **1,147 passing / 1,147**

**WHAT THE NEW TESTS COVER:**

- **A synthetic positive control for each derivation, hand-computed.** Derivation
  A's four widths at the frozen tolerance, computed from the rates independently
  of the module. Derivation B's BTCUSDT cell, with the denominator built term by
  term in the docstring and asserted to 500.505. Derivation C's floor-binding
  predicate on a hand-built two-row population with a known answer, plus the
  boundary either side of 0.00675.
- **The probe that the sealed-partition assertion actually fires**, on a
  `year=2025` path, a `year=2026` path, and a mixed list containing one sealed
  member.
- **A monotonicity check on every curve claimed monotone**, by numerical
  difference across the whole grid.
- **The central verification**: every one of the 342 widths fed back through
  `costs.position_size` and required to reproduce its tolerance.
- **An import-time grid guard**, probed by narrowing the grid and requiring the
  refusal to fire.
- **The firewall**: no engine import, no engine call, no `exit_reason`, the
  twelve-name guard, and no selected tolerance among the module's assignments.

---

## 10. WHAT CONTRADICTS A FROZEN DOCUMENT

**Nothing contradicts a frozen document.** Three items are worth stating.

**10.1 `docs/handoff/31_point_5_closing.md` §5.1's UNSOURCED FIGURES ARE NOW
SOURCED**, and agree to every digit they carried. That record's disposition —
*"Point 4 must derive them from the implementation before relying on them"* — is
**discharged**, and the pairing it left unexplained is explained in §3.2.

**10.2 THE DIRECTION SPLIT WAS NOT PREVIOUSLY RECORDED ANYWHERE.** No frozen
document states that the required floor differs between a long and a short. **It
is not a contradiction — no document says otherwise — but it is new**, and any
floor stated as a single per-symbol number is under-specified by one dimension.

**10.3 THE STOP-PATH DENOMINATION WAS IMPLICIT AND IS NOW EXPLICIT.** Report 28
§9 reports `c/s` without stating which legs `c` covers. §2 above establishes it
from the implementation. **Report 28's figures are unaffected**; what changes is
that the ratio now has a stated definition.

---

## 11. WHAT THIS HANDS FORWARD

1. **The required floor is a closed form in the tolerance**, per symbol **and per
   direction**, verified against the implementation to 5.662e-15.
2. **The four previously unsourced required-floor figures are derived**, and the
   reason there were two per symbol is now on the record.
3. **The rejected treatment's magnitude is quantified** at 1.16% to 1.80% of a
   risk unit, against an accepted term under 0.017%. **Both halves of the
   comparison 4.1 owes a criterion for are now visible.**
4. **The stratification curve is available across the committed grid**, on the
   candidate population, with the taken-population equivalents stated as
   unavailable and why.
5. **The denomination decision remains 4.1's**, and this report's single curve
   must not be read as having made it.
6. **No tolerance is selected, no branch is preferred, and no floor is
   recommended.**

---

**Files.** `src/analysis/floor_curve.py` · `tests/test_floor_curve.py` · this
report. **Grid committed separately at `12e32a6b`, before the solver existed.**
**Firewall:** armed; no outcome quantity, no engine, no exit resolved.
**Holdout:** sealed; the barrier is asserted per read and probed by test; no 1m
partition was opened by this step.
