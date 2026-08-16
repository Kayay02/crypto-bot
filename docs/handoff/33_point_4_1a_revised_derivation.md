# REPORT 33 — THE REVISED STOP FLOOR

**Point 4, sub-point 4.1a, the revised derivation.** A DERIVATION and a
VERIFICATION. No tolerance is selected, no floor is recommended, and **no
non-uniformity verdict is returned.**

**WHY THIS SITS UNDER `docs/handoff/`.** It is a derivation and a measurement,
not a decision. Design documents join the frozen specification on commit per
`docs/design/04_0_divergence_disposition_amendment_2.md` §2; **a derivation does
not**, and filing it under `docs/design/` would enrol a measurement in the
specification.

**THE DENOMINATION IT SOLVES UNDER** was committed at `02992c7a`:
`docs/design/04_1a_denomination_amendment_1.md` §3.1 binds the constraint to the
unvalidated term's contribution over the stop distance — **numerator narrowed,
denominator unchanged.**

---

## 1. PROVENANCE

- Grid commit, alone and first: **`532e9334`**. The solver is absent from that
  tree.
- Derivation module: **`src/analysis/haircut_floor_curve.py`**.
- Tests: **`tests/test_haircut_floor_curve.py`** — path chosen after listing
  `tests/` in full and probing two candidates; §8 records the check.
- Cost algebra: `src/engine/costs.py` and `src/engine/sizing.py`, **read and
  called, never reimplemented**.

**NOT MODIFIED:** `src/engine/costs.py` · `src/engine/sizing.py` ·
`src/engine/portfolio.py` · `src/risk/` · `src/timeframe/` ·
`src/analysis/floor_curve.py` · `src/analysis/haircut_share.py` · every document
under `docs/design/` and `docs/handoff/`.

---

## 2. THE NUMERATOR, DEFINED BY PRINCIPLE

> **THE NUMERATOR IS THE SUM OF THE COST MODEL'S UNVALIDATED FRICTION TERMS.**

**AT THIS COMMIT THAT SUM HAS EXACTLY ONE NON-ZERO MEMBER — THE STOP HAIRCUT.**
Both facts were confirmed in `src/engine/costs.py` before this report was
written:

- **The haircut is present.** `stop_haircut_bps: dict = field(` at line 73, read
  through `def haircut_bps(self, symbol)` at line 171, and charged at line 331 as
  `s_stop = stop * cfg.haircut_bps(symbol) / 10_000.0`.
- **Entry slippage is zero.** `entry_slippage_bps: float = 0.0` at line 71, and
  charged at line 330 on the **entry** price.

**AND THE COST MODEL ITSELF ANTICIPATES THAT CHANGING.** The `CostConfig`
docstring records that *"entry_slippage_bps is 0 by design"* and that *"it exists
as a config value purely so it can be sensitivity-tested later"*.

### 2.1 IMPLEMENTED AS A SET, NOT AS THE ONE TERM THAT IS CURRENTLY NON-ZERO

`docs/design/04_0_divergence_disposition_amendment_2.md` §7 adopts a standing
rule against scopes stated by enumeration. **A numerator naming only the haircut
would let entry slippage escape the constraint at exactly the moment it started
to matter** — and the cost model says that moment is anticipated.

**THE SET CARRIES EACH TERM'S ATTACHMENT POINT**, because a term charged on the
**stop** price and one charged on the **entry** price enter the closed form
differently: the stop price moves with the width and the entry price does not.
**An unknown attachment point raises rather than being dropped**, since a
silently omitted term is what the set exists to prevent.

**A SET WITH ONE MEMBER IS INDISTINGUISHABLE FROM A HARDCODED TERM UNTIL A SECOND
MEMBER EXISTS**, so §8 adds one and requires the numerator, the ratio and the
solved width all to move.

### 2.2 A CLASSIFICATION TENSION, RECORDED AND NOT RESOLVED

**`docs/design/04_1c_non_uniformity_check.md` §3.2 places entry slippage in the
VALIDATED bucket**, alongside the taker fee, on the ground that
`docs/handoff/31_point_5_closing.md` §5.2 singles out the haircut as the
placeholder without so identifying it.

**THIS DERIVATION PLACES IT IN THE UNVALIDATED SET**, on the ground that it is a
slippage model held at zero by a stated modelling argument rather than a
venue-published rate, and that `costs.py` itself describes it as awaiting
sensitivity testing.

> **THE TWO CLASSIFICATIONS PRODUCE THE SAME NUMERATOR AT THIS COMMIT**, because
> the term is zero either way. **The divergence is operationally moot now and
> would not be if the term were switched on.**

**It is recorded rather than resolved.** Resolving it is not this step's
business, and neither reading changes a figure below.

---

## 3. THE REVISED CLOSED FORM

### 3.1 THE DERIVATION

Write the width as a fraction `w` of entry price `P`, so the stop price is
`P(1-w)` on a long and `P(1+w)` on a short and the stop distance is `s = wP`.
Let **`a`** be the unvalidated rate charged on the **stop** price and **`b`** the
unvalidated rate charged on the **entry** price. The numerator is

    long   U = P(1-w)a + Pb          short  U = P(1+w)a + Pb

so **`P` cancels** from `U / s` and

    long   U/s = [a + b - wa] / w    short  U/s = [a + b + wa] / w

Setting each equal to the tolerance and solving:

    long   w(tau) = (a + b) / (tau + a)
    short  w(tau) = (a + b) / (tau - a)

**A CLOSED FORM EXISTS**, so no numerical solution was required. The committed
grid is used to **report and verify** the curve, not to solve it.

### 3.2 IT WAS DERIVED, NOT CARRIED OVER

**Report 32 §3.1's form was `(2f + e + h) / (tau ± (f + h))`.** The revised form
is **not that form with substitutions** — the fee terms leaving the numerator
changes both the numerator and **the quantity subtracted in the short-leg
denominator**, and the second is what moves the pole.

**Carrying the old form over by analogy would have produced a pole in the wrong
place**, which is the failure §3.4 makes checkable.

### 3.3 THE DIRECTION SPLIT — IT STILL ARISES, AND ITS DRIVER HAS CHANGED

> **A SPLIT STILL ARISES. THE SHORT LEG REQUIRES THE WIDER FLOOR AT EVERY
> TOLERANCE, ON EVERY SYMBOL.**

**Under report 32 §3.2 the split was fed by the taker fee AND the haircut**, both
charged on the stop price. **Under the revised numerator only the stop-attached
unvalidated rate feeds it** — `a` alone.

### 3.4 WHAT WOULD HAVE CONSTITUTED SHOWING NO SPLIT

**Stated so the negative result is checkable had it occurred:** the two forms
coincide exactly when **`a = 0`** — when **no unvalidated term is charged on the
stop price at all.** The split would then collapse and the pole would vanish.

**IT IS NOT ZERO**, so the split stands. **The condition is exercised by test
rather than argued**: a configuration with the whole unvalidated rate moved onto
the entry price is asserted to make the two directions coincide and the pole go
to zero.

### 3.5 THE POLE, AND IT HAS MOVED

**The short form is undefined at `tau = a`.** The function returns **infinity**
there rather than a negative width, which would be a wrong answer with the sign
flipped.

- **BTCUSDT and ETHUSDT: 0.0005.** Report 32's sat at **0.0011**.
- **SOLUSDT: 0.0010.** Report 32's sat at **0.0016**.

**Both have moved, and both moved down**, because the fee terms left the
subtracted quantity. **Both sit far below the committed grid's lower bound**, so
no grid point approaches one.

**The long leg has no pole** at or above zero.

---

## 4. THE GRID, AND HOW ITS RANGE WAS CHOSEN

**COMMITTED ALONE AT `532e9334`, BEFORE THE SOLVER EXISTED.**

> **IT IS NOT REPORT 32'S GRID.** The revised ratio is a different quantity with
> a different achievable range and a pole in a different place. **Reusing
> 0.02 to 0.30 because it is the grid that exists would be a range carried over
> by analogy** — the recurring defect class applied to a measurement's own
> instrument.

**THE RANGE IS FIXED BY TWO STRUCTURAL BOUNDS, BOTH READ FROM COMMITTED
ARTIFACTS:**

**LOWER, 0.030.** `costs.stop_geometry` caps the stop distance at
`cfg.stop_max_pct * entry`, frozen at **0.035**, clamping any wider raw distance
to that cap. **A required floor above it collides with the cap and cannot be
honoured.** The most demanding cell — SOLUSDT short — reaches the cap just below
**0.0296**, so **0.030 is the first clean grid point at which every cell is
satisfiable within the frozen cap.**

**UPPER, 0.120.** Running the other way the required width falls, and the most
demanding cell drops below the thesis's frozen **1.50%** floor just below
**0.0677**. **0.120 carries the grid comfortably past that for every cell**, so
the grid **brackets both structural boundaries** rather than stopping at one.

**STEP, 0.0025 — thirty-seven points.** The range is about a third the width of
report 32's, so the resolution in the reported quantity is comparable.

**A NOTE ON ORDER.** The bounds are derived **from** the closed form's structure,
which is the method this step specifies, so knowing the algebra before fixing the
grid is required rather than a leak. **What the commit order protects is that the
grid was fixed before the curve was reported over it.**

---

## 5. THE CURVE

Required floor width as a percentage of entry, long first and short second.
**BTCUSDT and ETHUSDT share a curve exactly** — they share a haircut and the
revised numerator contains nothing else that differs between them, which is
asserted by test rather than assumed.

- tolerance 0.0300: BTC/ETH 1.6393 and 1.6949; SOL 3.2258 and 3.4483
- tolerance 0.0400: BTC/ETH 1.2346 and 1.2658; SOL 2.4390 and 2.5641
- tolerance 0.0500: BTC/ETH 0.9901 and 1.0101; SOL 1.9608 and 2.0408
- tolerance 0.0675: BTC/ETH 0.7353 and 0.7463; SOL 1.4599 and 1.5038
- tolerance 0.0800: BTC/ETH 0.6211 and 0.6289; SOL 1.2346 and 1.2658
- tolerance 0.1000: BTC/ETH 0.4975 and 0.5025; SOL 0.9901 and 1.0101
- tolerance 0.1200: BTC/ETH 0.4149 and 0.4184; SOL 0.8264 and 0.8403

**The full 222-row curve — 37 tolerances by three symbols by two directions — is
produced by `haircut_floor_curve.floor_curve`.**

### 5.1 MONOTONICITY, VERIFIED

**All six curves are strictly DECREASING in the tolerance across the whole
grid**, checked by numerical difference rather than by inspection of the algebra.
**No curve claimed monotone was found otherwise.**

**No non-finite width appears at any grid point**, the poles being far below the
lower bound.

---

## 6. VERIFICATION AGAINST THE IMPLEMENTATION

> **THE CLOSED FORM IS NOT TRUSTED. IT IS CHECKED.**

**Every solved width is fed back through `costs.position_size`**, the unvalidated
sum is recovered **by difference** — the engine's denominator less the engine's
denominator with the unvalidated set zeroed — and the resulting ratio is required
to equal the tolerance it was solved for.

**MAXIMUM ABSOLUTE RESIDUAL ACROSS ALL 222 CELLS: 3.761e-15.**

**PRICE INVARIANCE VERIFIED** at **30,000, 1,000 and 100** — two and a half
orders of magnitude — with the recovered ratio equal to the tolerance at each, as
report 32 §3.5 did for the old relation.

**NOTHING IS OBTAINED BY RESTATING A COST TERM.** The numerator comes from the
engine by difference; the denominator is the engine's own. A test asserts the
module contains no second copy of the rate arithmetic among its executable
tokens.

---

## 7. WHAT REPORT 32 STILL GOVERNS

> **REPORT 32 IS SUPERSEDED AS THE GOVERNING RELATION. IT IS NOT FALSIFIED, AND
> NOTHING HERE IMPEACHES IT.**

- **Its closed form remains the correct relation between the OLD ratio and
  width.** It answers a question that is no longer the governing one.
- **Its verification stands** — a maximum residual of 5.662e-15 across 342
  points, report 32 §3.5.
- **Its derivation of the four figures `docs/handoff/31_point_5_closing.md` §5.1
  recorded as supplied but unsourced is unaffected**, as is its explanation of
  why there were two per symbol.
- **Its structural findings about the old relation stand**, including the
  direction split it established, which this report re-derived rather than
  inherited.

**A reader should not take this report as correcting report 32.** It solves a
different constraint.

---

## 8. VERIFICATION SUMMARY

**THE TEST PATH CHECK.** `tests/` was listed in full and two candidate paths were
probed. `tests/test_haircut_floor_curve.py` did not exist and was chosen.

- baseline: **1,162 passing**
- new in `tests/test_haircut_floor_curve.py`: **+19**
- total: **1,181 passing / 1,181**

**WHAT THE NEW TESTS COVER:**

- **A synthetic positive control for the closed form**, hand-computed from the
  rates independently of the module, on all three symbols and both directions.
- **The feedback check against `costs.position_size` at every one of the 222
  cells**, plus price invariance at three prices.
- **THE SET PROBE** — the one test that distinguishes a set from a hardcoded
  term. Entry slippage is switched on and the numerator, the measured ratio and
  the solved width are all required to move, with the solved width still
  reproducing its tolerance with the second term live.
- **An unknown attachment point** asserted to raise rather than be dropped.
- **Monotonicity**, by numerical difference across the whole grid.
- **The pole probe**: infinity at and below the pole, finite above it, no pole on
  the long leg, the pole below report 32's, and the pole below the grid.
- **The no-split condition of §3.4**, exercised on a configuration with the
  unvalidated rate moved onto the entry price.
- **The grid guards**: the committed endpoints and step, the import-time refusal
  of a narrowed grid, that it is not report 32's grid, and that its two bounds
  are the structural ones claimed.
- **The firewall**: no engine import, no engine call, no `exit_reason`, nothing
  under `data/`, the twelve-name guard, and no verdict machinery.

**ALL SOURCE-TEXT CHECKS RUN OVER EXECUTABLE TOKENS**, per the standing rule at
`docs/design/04_1a_denomination_amendment_1.md` §7. **None fired falsely in this
step**, which is the first step in four in which none did.

---

## 9. WHAT THIS REPORT DOES NOT DO

- **It selects no tolerance value and recommends no floor.** The frozen 0.11 does
  not carry over — it is a tolerance on a different ratio, per amendment 1 §3.3 —
  and no value under the revised denomination is stated anywhere.
- **IT RETURNS NO NON-UNIFORMITY VERDICT.** Whether the revised tolerance has
  authority over the cross-symbol distribution of the protected quantity is **the
  next step's question**, evaluated against **its own committed threshold
  construction, in its own commit.** Nothing here states, implies or foreshadows
  whether that trigger would fire, and **no comparison between the revised
  spread and the old one appears.**
- **It does not restratify the candidate population**, computes no floor-binding
  fraction, and does not touch kill condition (d).
- **It does not perform the dominance check** named at
  `docs/design/04_1a_denomination.md` §4.1.
- **It sets no magnitude threshold.**

---

**Files.** `src/analysis/haircut_floor_curve.py` · `tests/test_haircut_floor_curve.py`
· this report. **Grid committed separately and first at `532e9334`.**
**Firewall:** armed; no outcome quantity, no engine, no exit resolved, no bar
data of any kind. **Holdout:** untouched — this derivation is over rates and
algebra and opens no file under `data/`.
