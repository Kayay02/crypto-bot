# REPORT 39 — CANDIDATE STOP-CAP RULES, MEASURED

**Point 4, sub-point 4.1f's measurement.** **Nothing is selected and nothing is
recommended.** Per-limb verdicts are reported and
`docs/design/04_1g_cap_adoption.md` decides.

**THE REQUIREMENT IS `docs/design/04_1f_cap_requirement.md`, COMMITTED AT
`ff4b226` BEFORE THIS REPORT EXISTED.** Its four limbs are cited here and are
neither restated nor reinterpreted.

**WHY THIS SITS UNDER `docs/handoff/`.** It is a measurement, not a decision.

---

## 1. PROVENANCE

- **Module:** `src/analysis/cap_candidates.py`. It imports
  `src/sweep/grid.py`'s rule and `src/analysis/risk_unit_floor_curve.py`'s domain
  machinery; a test asserts it reimplements neither.
- **Tests:** `tests/test_cap_candidates.py` — path chosen after listing `tests/`
  in full and probing two candidates; both free, the first taken. 15 added.
- **NOT MODIFIED:** `src/engine/`, `src/risk/`, `src/sweep/`, `src/folds/`,
  `src/analysis/stop_cap_audit.py` and every other analysis module, every document
  under `docs/design/`.

**THE SEAL.** The barrier is asserted once per symbol-fold immediately before each
read, asserted by test to sit inside the loop, and probed in the firing direction
on both sealed years. Bar data is limited to training windows inside 2022-01-05 to
2024-12-31.

---

## 2. THE CANDIDATES

- **A — `grid.derived_cap`**, the committed rule, per symbol and per training
  fold.
- **B — NO CAP AT ALL.**
- **C — `grid.derived_cap` EVALUATED OVER THE WHOLE IN-SAMPLE WINDOW**, giving one
  constant per symbol. **The requirement admits it**: §4.2 of that document
  records that constants are not excluded in advance and that a derived constant
  is admissible. It is included because it is the natural variant that keeps
  limb 1 and removes limb 4's difficulty, and leaving it unmeasured would have
  left the comparison between A and B looking like the only one available.

---

## 3. CANDIDATE A — `grid.derived_cap`, PER SYMBOL AND PER FOLD

### 3.1 THE VALUES

As a percentage of entry, across nine training folds:

- **BTCUSDT: 3.5826 to 5.5140, median 4.1128.**
- **ETHUSDT: 3.5043 to 5.5077, median 4.4556.**
- **SOLUSDT: 5.2624 to 7.4709, median 6.6416.**

### 3.2 THE CLIPPED FRACTION

**Judged by the cap of the fold period each candidate falls in**, which is the
operative reading of a per-fold rule: the sweep derives the cap on a training fold
and applies it to that fold's period.

- **POOLED: 232 clipped of 8,567 assigned, 2.71 per cent.**
- **BTCUSDT: 32 of 2,839, 1.13 per cent.**
- **ETHUSDT: 61 of 2,789, 2.19 per cent.**
- **SOLUSDT: 139 of 2,939, 4.73 per cent.**

**2,817 CANDIDATES FALL IN NO TEST FOLD PERIOD AND HAVE NO CAP UNDER THIS RULE.**
They are reported rather than assigned one, because assigning a cap the rule does
not supply would be inventing the rule's behaviour outside its own domain.

Per test fold period, clipped of assigned: fold 1, 38 of 884 (4.30 per cent);
fold 2, 14 of 885 (1.58); fold 3, 1 of 843 (0.12); fold 4, 3 of 906 (0.33); fold 5,
69 of 975 (7.08); fold 6, 66 of 982 (6.72); fold 7, 11 of 981 (1.12); fold 8, 18 of
1,075 (1.67); fold 9, 12 of 1,036 (1.16).

### 3.3 THE FOLD-DEPENDENCE

**Each candidate evaluated against all nine of its symbol's fold caps:**

- **BTCUSDT: 28 clipped under every fold cap, 80 under some and not others, 3,627
  under none.**
- **ETHUSDT: 56 always, 294 sometimes, 3,365 never.**
- **SOLUSDT: 108 always, 305 sometimes, 3,521 never.**
- **POOLED: 192 always, 679 SOMETIMES, 10,513 never.**

> ### 679 CANDIDATES ARE CLIPPED UNDER SOME FOLDS AND NOT OTHERS — THREE AND A
> ### HALF TIMES THE 192 THAT ARE CLIPPED UNDER ALL OF THEM.

**THE CLIPPED POPULATION UNDER THIS RULE IS NOT A PROPERTY OF A CANDIDATE. IT IS A
PROPERTY OF A CANDIDATE AND A FOLD.**

### 3.4 THE VERDICTS, LIMB BY LIMB

- **LIMB 1, DERIVATION: PASSES.** The value follows from `m*` and the 95th
  percentile of breakout ATR per cent over the training fold, both computed by
  `src/sweep/grid.py`, and the derivation is cited to Appendix H and Amendment 6.
- **LIMB 2, INTENT DELIVERY: PASSES.** The rule states its intent in its own
  docstring — the cap binds when ATR per cent exceeds the 95th percentile, *"5% of
  bars by construction, and strictly less at every lower multiplier."* It delivers
  2.71 per cent pooled and no symbol above 4.73 per cent, which is consistent with
  that intent rather than departing from it.
- **LIMB 3, EXECUTABILITY: PASSES.** §4.3 measures zero refusals with the stop
  uncapped; a cap only narrows stops and therefore only raises quantities, so no
  cap can refuse more than removal does, and removal refuses none.
- **LIMB 4, POPULATION DETERMINACY: FAILS ON ITS FACE AND IS DISCHARGEABLE BY
  DISCLOSURE.** The population is fold-dependent, on 679 candidates. The limb
  fails *"if the population is fold-dependent and the dependence is neither counted
  nor routed"* — §3.3 counts it, and routing it is the adoption document's to do.

---

## 4. CANDIDATE B — NO CAP AT ALL

### 4.1 THE WIDEST STOP THE RULE PRODUCES

Under removal the ATR rule is unbounded above, so the widest stop it reaches in
the population is where limb 3 is tested:

- **BTCUSDT: 8.5315 per cent**, at an entry of 28,062.00 with ATR 1,064.0431.
- **ETHUSDT: 11.8216 per cent**, at 1,908.89 with ATR 100.2939.
- **SOLUSDT: 49.7087 per cent**, at 10.0108 with ATR 2.2117.

### 4.2 THE RESULTING QUANTITIES

Smallest quantity and smallest notional in the population, sized at each
candidate's own ATR width, floored to the venue's lot step, against the venue's
minimums:

- **BTCUSDT: smallest quantity 0.0055 against a lot step of 0.0001 — 55 lots.
  Smallest notional 227.30 against a 5.00 minimum.**
- **ETHUSDT: smallest quantity 0.08 against 0.01 — 8 lots. Smallest notional
  152.71.**
- **SOLUSDT: smallest quantity 1.2 against 0.1 — 12 lots. Smallest notional
  40.04.**

### 4.3 DOES THE VENUE MINIMUM BIND ANYWHERE?

> ### NO. ZERO REFUSALS ACROSS ALL 11,384 CANDIDATES. NOT ONE IS REFUSED FOR
> ### QUANTITY OR FOR NOTIONAL.

**COUNTED, NOT ASSUMED**, per `docs/design/04_1c_proper.md` §6.3's treatment of a
population expected empty. `sizing.viability` is called and not reimplemented, and
a test exercises it at a width where it **does** refuse — a SOLUSDT candidate at a
750 per cent ATR width — so a pass here means the condition was capable of failing.

**THE MARGIN IS NOT NARROW.** The tightest case is SOLUSDT at 12 lots and 40.04 of
notional, eight times the venue's minimum notional.

**REPORT 38 §3.3's NEAR-MISS DOES NOT MATERIALISE.** That report gave ETHUSDT's
tightest minimum-lot binding width as 49.03 per cent at its highest observed
price, against a widest observed ATR width of 49.709 per cent — close enough that
`docs/design/04_1f_cap_requirement.md` §2.3 declined to guess. **The two do not
meet, because they occur on different symbols and at different prices:** the 49.709
per cent width is SOLUSDT's, at an entry of 10.01, where one lot is 0.1 and the
quantity is 12 lots.

### 4.4 THE VERDICTS, LIMB BY LIMB

- **LIMB 1, DERIVATION: PASSES VACUOUSLY.** There is no value to derive. **This is
  recorded as a vacuous pass and not as a positive merit**, per §3.1 of the
  requirement.
- **LIMB 2, INTENT DELIVERY: PASSES.** It states a clipped fraction of zero and
  delivers zero.
- **LIMB 3, EXECUTABILITY: PASSES.** §4.3, on a measured count of zero refusals.
- **LIMB 4, POPULATION DETERMINACY: PASSES.** No fold enters the rule, so no
  candidate's status depends on which fold is asked.

---

## 5. CANDIDATE C — THE SAME RULE OVER THE WHOLE IN-SAMPLE WINDOW

### 5.1 THE VALUES

`grid.derived_cap` applied to the breakout population over the full in-sample
window rather than per fold, giving one constant per symbol:

- **BTCUSDT: 4.4687 per cent**, from `m*` 3.0563 and a 95th percentile of
  0.804255.
- **ETHUSDT: 4.9141 per cent**, from 2.4761 and 0.987539.
- **SOLUSDT: 6.7982 per cent**, from 1.9290 and 1.534938.

### 5.2 THE CLIPPED FRACTION

- **POOLED: 277 of 11,384, 2.43 per cent.**
- **BTCUSDT: 50 of 3,735, 1.34 per cent.**
- **ETHUSDT: 83 of 3,715, 2.23 per cent.**
- **SOLUSDT: 144 of 3,934, 3.66 per cent.**

Per fold period, clipped of the candidates in that period: fold 1 train 135 of
1,929 (7.00 per cent) and test 40 of 884 (4.52); fold 2, 47 of 1,851 (2.54) and 10
of 885 (1.13); fold 3, 50 of 1,769 (2.83) and 1 of 843 (0.12); fold 4, 11 of 1,728
(0.64) and 3 of 906 (0.33); fold 5, 4 of 1,749 (0.23) and 12 of 975 (1.23); fold 6,
15 of 1,881 (0.80) and 20 of 982 (2.04); fold 7, 32 of 1,957 (1.64) and 7 of 981
(0.71); fold 8, 27 of 1,963 (1.38) and 16 of 1,075 (1.49); fold 9, 23 of 2,056
(1.12) and 2 of 1,036 (0.19).

**Fold periods overlap, so these do not sum to the pooled count.**

### 5.3 THE VERDICTS, LIMB BY LIMB

- **LIMB 1, DERIVATION: PASSES.** Same rule, same inputs, one window instead of
  nine. The value follows from the derivation.
- **LIMB 2, INTENT DELIVERY: PASSES.** Same stated intent; 2.43 per cent pooled
  and no symbol above 3.66.
- **LIMB 3, EXECUTABILITY: PASSES**, for §3.4's reason.
- **LIMB 4, POPULATION DETERMINACY: PASSES.** One cap per symbol for the whole
  window, so a candidate's status does not depend on which fold is asked.

**ONE PROPERTY IS RECORDED WITHOUT BEING A LIMB.** The window it is computed over
is the in-sample window, so applying it out of sample uses a cap fitted to a
different period. **That is true of any rule fitted in sample**, including
candidate A, and no limb of the requirement ranges over it.

---

## 6. THE ADMITTED DOMAIN AND THE LEVEL'S POSITION

**RECOMPUTED AS `docs/handoff/36_point_4_1c_risk_unit_derivation.md` DERIVED IT**,
through `risk_unit_floor_curve.common_achievable_range`, imported and not
restated. **Where a candidate carries per-symbol caps the bound is the largest of
each cell's ratio at its own cap** — the domain is an intersection, and applying
one symbol's cap to all of them would understate it. A test pins that.

- **CANDIDATE A**, per fold: the lower bound runs **0.01777751 to 0.02450051**
  across the nine folds, upper bound 0.40 throughout.
- **CANDIDATE B**, with the widest ATR width as the binding width: lower bound
  **0.00359143**, upper bound 0.40.
- **CANDIDATE C**: lower bound **0.01937905**, upper bound 0.40.
- **The frozen 0.035 for reference:** lower bound 0.03554692.

> ### THE COMMITTED LEVEL OF 0.10 LIES INSIDE THE ADMITTED DOMAIN UNDER EVERY
> ### CANDIDATE, INCLUDING UNDER EVERY ONE OF CANDIDATE A's NINE FOLDS.

**EVERY CANDIDATE WIDENS THE DOMAIN**, because every one caps at a wider width than
0.035 does, and a wider cap lowers the ratio at the cap.

> ### THIS IS A CHECK ON THE LEVEL'S POSITION AND NOT A RE-ARGUMENT OF THE LEVEL.

The level's ground is the displacement budget at `docs/design/04_1c_proper.md` §2
and the uncertainty parameter at §3. **Neither is touched by any cap**, and nothing
here bears on whether 0.10 is the right level — only on whether it remains
attainable.

---

## 7. SUMMARY OF VERDICTS

- **Candidate A:** limb 1 passes, limb 2 passes, limb 3 passes, **limb 4 fails on
  its face and is dischargeable by disclosure**, on 679 fold-dependent candidates.
- **Candidate B:** limb 1 passes vacuously, limbs 2, 3 and 4 pass.
- **Candidate C:** all four limbs pass.

**NO CANDIDATE IS SELECTED, PREFERRED OR RECOMMENDED HERE.** A test asserts the
module declares no constant naming an adopted, chosen or preferred rule.

---

## 8. WHAT THIS REPORT DOES NOT DO

**IT SELECTS NOTHING.** Owed to `docs/design/04_1g_cap_adoption.md`.

**IT COMPUTES NO OUTCOME QUANTITY**, resolves no exit and does not invoke the
execution loop; asserted over the module's AST together with the twelve-name
firewall.

**IT DOES NOT RE-ARGUE THE LEVEL.** §6.

**IT DOES NOT WEIGH THE LIMBS AGAINST EACH OTHER.** Limb 4's failure for candidate
A is reported as a failure of that limb; whether disclosure discharges it, and what
that costs, is the adoption document's judgement.

---

## 9. ARTIFACTS

- **Report:** `docs/handoff/39_point_4_cap_candidates.md`
- **Module:** `src/analysis/cap_candidates.py`
- **Tests, 15 added:** `tests/test_cap_candidates.py`
- **Requirement:** `docs/design/04_1f_cap_requirement.md`, commit `ff4b226`

**Full suite: 1311 passed** — 1296 before this step, plus the 15 above.
