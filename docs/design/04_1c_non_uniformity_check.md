# THE NON-UNIFORMITY CHECK — THRESHOLD PRE-REGISTERED

**Point 4, sub-point 4.1c, the non-uniformity check.** A gap in 4.1b's own
argument, tested against a threshold committed before the quantity it judges
exists.

## 1. WHAT THIS DOCUMENT IS

**A PRE-REGISTRATION WHOSE THRESHOLD IS COMMITTED BEFORE THE QUANTITY IT JUDGES
HAS BEEN COMPUTED.**

### 1.1 THE TWO-COMMIT STRUCTURE

**THIS DOCUMENT IS COMMITTED TWICE, AND THE ORDER IS THE POINT.**

- **COMMIT ONE: §1 to §4** — the question, the decomposition stated
  algebraically, and **the threshold**. Committed **alone**, before
  `src/analysis/haircut_share.py` exists.
- **COMMIT TWO: §5 to §7** — the derivation module, its results, and the finding
  evaluated against §4's threshold as written.

**A READER CAN CHECK THE ORDER RATHER THAN TAKE IT ON TRUST.** Both hashes are
given at §6, and `git log` shows the threshold commit preceding the module's
first appearance.

**EXTENDING A DOCUMENT ITS OWN AUTHOR COMMITTED IS NOT AN AMENDMENT TO A FROZEN
ARTIFACT.** §1 to §4 are not edited in commit two — they are extended by §5 to
§7. If any word of §1 to §4 changes between the two commits, that is a
contamination event and the diff will show it.

### 1.2 WHAT THIS STEP DECIDES, AND WHAT IT DOES NOT

**IT DETERMINES WHETHER 4.1b §5's TRIGGER FIRES. IT DOES NOT SET A TOLERANCE
VALUE AND IT DOES NOT REOPEN 4.1a.** If the trigger fires, reopening 4.1a is a
separate document under that file's §8, **not written here**.

---

## 2. THE QUESTION

**DOES A SINGLE TOLERANCE, APPLIED TO THE COMMITTED STOP-PATH RATIO, BOUND THE
UNVALIDATED TERM'S SHARE OF THE RISK UNIT EQUALLY ACROSS SYMBOLS AND
DIRECTIONS?**

### 2.1 WHY IT IS OPEN

`docs/design/04_1b_tolerance_and_branch.md` §5 declined to re-denominate the
constraint onto the haircut alone, on the ground that **the haircut sits inside
the stop-path cost, so constraining the whole constrains the part.**

> **THAT GROUND IS TRUE AND INCOMPLETE.** It establishes that the whole bounds
> the part. **It does not establish that the whole bounds the part UNIFORMLY
> ACROSS SYMBOLS.**

### 2.2 THE MECHANISM

**The haircut's contribution to the ratio scales with the haircut rate over the
stop width, and both terms differ by symbol.** `docs/handoff/31_point_5_closing.md`
§5.2 records the rate as **5 bps on BTCUSDT and ETHUSDT and 10 bps on SOLUSDT**,
and report 32 §3.4 shows SOLUSDT requiring a wider floor at every tolerance.

**THE DIRECTION OF CONCERN, STATED: the symbol carrying the larger unvalidated
term is also the symbol requiring the wider floor, and these do not obviously
cancel.** A larger haircut raises the numerator; the wider floor it forces raises
the denominator. **Whether the ratio of the two is stable across symbols is the
question, and it is not answerable by inspection.**

### 2.3 WHY IT MATTERS

**If a single tolerance delivers materially different bounds on the unvalidated
share per symbol, the parameter is not controlling the quantity 4.1b's rationale
says it controls**, and 4.1b §5's trigger for reopening 4.1a fires.

---

## 3. WHAT IS MEASURED

### 3.1 THE COST TERMS, READ FROM THE IMPLEMENTATION

`src/engine/costs.py:336` defines the per-unit denominator as

    denom = move + entry * taker_fee + stop * taker_fee + s_entry + s_stop

with `s_entry = entry * entry_slippage_bps / 10_000` and
`s_stop = stop * haircut_bps(symbol) / 10_000`. The cost term is
`c = denom - move`.

### 3.2 THE SPLIT INTO VALIDATED AND UNVALIDATED

**The split is by epistemic status, per `docs/design/04_1b_tolerance_and_branch.md`
§3.2**, not by leg:

- **VALIDATED:** `entry * f + stop * f + entry * e` — the taker fee on both legs
  and the entry slippage. These are venue-published rates, and
  `docs/handoff/31_point_5_closing.md` §5.2 singles out the haircut as the
  placeholder without so identifying them.
- **UNVALIDATED:** `stop * h` — the stop haircut, which §5.2 records **IS the
  entire slippage-and-gap model** and **cannot be validated against this data
  layer**.

### 3.3 THE DECOMPOSITION, STATED ALGEBRAICALLY BEFORE ANY VALUE IS COMPUTED

Writing the stop width as a fraction `w` of entry price `P`, so the stop price is
`P(1-w)` on a long and `P(1+w)` on a short and the stop distance is `s = wP`:

    validated share of the ratio, long    = [(2f + e) - w*f] / w
    unvalidated share of the ratio, long  = h(1 - w) / w

    validated share of the ratio, short   = [(2f + e) + w*f] / w
    unvalidated share of the ratio, short = h(1 + w) / w

**The two sum to the committed ratio `c/s`**, whose closed form report 32 §3.1
gives, and the sum is verified numerically in commit two rather than assumed.

### 3.4 THE PROTECTED QUANTITY IS A SHARE OF THE RISK UNIT, NOT OF THE STOP

**4.1b §3.2 defines what the constraint protects as the share of the RISK UNIT
determined by estimate.** The risk unit per unit of quantity is `d = s + c`, so
the protected quantity is

    u = (unvalidated cost) / d

**AND THAT REFRAMES THE QUESTION IN A WAY WORTH STATING BEFORE ANY NUMBER
EXISTS.** At the required floor the ratio equals the tolerance by construction, so
the TOTAL cost share of the risk unit is `tau / (1 + tau)` — **identical for every
symbol and every direction.** The constraint therefore already delivers a
perfectly uniform bound on the total cost share.

> **SO THE ENTIRE NON-UNIFORMITY, IF THERE IS ANY, LIVES IN ONE PLACE: THE
> UNVALIDATED TERM'S FRACTION OF THE TOTAL COST.** `u` factors as that fraction
> multiplied by `tau / (1 + tau)`.

**This is a structural consequence of the closed form, not a measurement**, and
it is stated here so that §5 reports the quantity that actually carries the
question rather than one that cannot vary.

---

## 4. THE THRESHOLD, COMMITTED HERE

### 4.1 THE TWO QUANTITIES COMPARED

**(a) THE CROSS-SYMBOL SPREAD.** At a tolerance `tau`, let

    S(tau) = max u  -  min u

taken over the **six symbol-direction cells** — three symbols by two directions.
**Computed at every point of the committed grid** at
`src/analysis/floor_curve.py` — 0.02 to 0.30 inclusive, step 0.005, fifty-seven
points. **The criterion uses `S_max`, the maximum of `S(tau)` over that grid.**

**(b) THE TOLERANCE SENSITIVITY.** For each symbol-direction cell, let

    R(cell) = max u over the grid  -  min u over the grid

**The criterion uses `R_min`, the minimum of `R(cell)` over the six cells.**

### 4.2 THE CRITERION

> ### THE TRIGGER FIRES IF AND ONLY IF `S_max >= R_min`.

**REPORTED AS THE RATIO `S_max / R_min`, firing at 1 or above.**

**WHY A DIRECT COMPARISON AND NOT A SCALED ONE.** Both quantities are **ranges of
the same quantity in the same units** — a share of one risk unit — so a ratio is
meaningful without normalisation and a difference would be meaningful too. **The
ratio is reported because it makes the margin legible in one number.**

### 4.3 THE REASONING THE CRITERION ENCODES

**If changing the tolerance moves the protected quantity less than choosing a
different symbol does, then the tolerance is not the thing governing the
protected quantity.**

> **A CONSTRAINT WHOSE PARAMETER IS DOMINATED BY AN AXIS IT DOES NOT RANGE OVER
> IS NOT CONTROLLING WHAT ITS RATIONALE SAYS IT CONTROLS.**

That is the whole content of the test, and it is denominated in what 4.1b's
rationale supplies — the unvalidated share of the risk unit — rather than in a
number that feels large.

### 4.4 WHY MAXIMUM AGAINST MINIMUM

**`S_max` is the most adverse cross-symbol spread anywhere on the grid.
`R_min` is the least generous single-cell sensitivity.** The comparison is
therefore **deliberately biased toward firing.**

**A NON-FIRING VERDICT UNDER THIS FORM IS THE STRONGER VERDICT.** A firing verdict
would be the weaker one and would have to be read with that in mind — which is
stated now, before the direction of the answer is known to any reader.

### 4.5 THIS THRESHOLD IS NOT REVISED IN COMMIT TWO

**Whatever the derivation returns, §4 stands as committed.** Revising it after
seeing the numbers would be the precise failure the whole 4.1 split exists to
prevent, and the diff between the two commits is where anyone can check that it
was not.

**IF THE NUMBERS LAND NEAR THE THRESHOLD, THE THRESHOLD IS APPLIED ANYWAY.** A
threshold applied only when it is comfortable is not a threshold.

### 4.6 A PROCESS DISCLOSURE, MADE BEFORE THE THRESHOLD IS RELIED ON

> **THE AUTHOR OF THIS THRESHOLD IS NOT IGNORANT OF INDICATIVE MAGNITUDES.**

§3.3 required the decomposition to be stated algebraically before any value was
computed, and it was. **In the course of establishing that the decomposition is
well-formed and that §3.4's factorisation holds, the expressions were evaluated
at sample tolerances.** So this threshold was written by an author who had seen
roughly where the two quantities sit.

**THIS IS DISCLOSED RATHER THAN CONCEALED, AND IT IS DISCLOSED HERE RATHER THAN
IN COMMIT TWO**, so that it is part of the artifact a reader checks the threshold
against.

**IT DOES NOT WEAKEN THE COMMIT-ORDER GUARD, AND IT DOES WEAKEN ANY CLAIM OF
IGNORANCE** — exactly the distinction `docs/design/04_1b_tolerance_and_branch.md`
§1.2 drew and for the same reason: the guard is that the threshold is fixed
before the derivation is committed and is applied as written, not that anyone was
in the dark.

**WHAT MAKES IT CHECKABLE ANYWAY:** §4.4's max-against-min construction is the
**strictest defensible reading** of §4.3's reasoning and is biased toward firing.
**An author tuning a threshold to avoid a firing verdict would not choose the
most adverse spread and the least generous sensitivity.** The construction is
therefore evidence against its own tuning, which is the best a disclosed
non-ignorance can offer.

**A LESS EXPOSED ALTERNATIVE WAS AVAILABLE AND WAS NOT TAKEN:** measuring the
spread at a single nominated tolerance rather than at its maximum over the grid
would have produced a smaller numerator and a more comfortable margin.

---

## 5. THE DERIVATION AND ITS RESULTS

**Module: `src/analysis/haircut_share.py`.** The haircut's contribution is taken
from the implementation **by difference** — `costs.position_size` is called once
with the frozen configuration and once with a configuration whose haircut rates
are zeroed, and the difference is the term. **No cost term is restated anywhere**,
and the width comes from report 32's committed closed form, imported unchanged.

### 5.1 THE DECOMPOSITION HOLDS

**Maximum residual of validated plus unvalidated against the total, across all
342 cells: 5.551e-17.** The split partitions the cost term exactly.

**AND §3.4's STRUCTURAL CLAIM IS CONFIRMED.** The total cost share of the risk
unit equals `tau / (1 + tau)` **to within 3.525e-15 at every one of the 342
cells** — identical for every symbol and every direction. **The constraint does
deliver a perfectly uniform bound on the total share**, so the whole question is
the unvalidated term's fraction of it, exactly as §3.4 said before any value
existed.

### 5.2 THE UNVALIDATED SHARE OF THE RISK UNIT

Percent of one risk unit, at selected grid points. BTCUSDT and ETHUSDT share a
value; SOLUSDT is given separately. Long first, short second.

- tolerance 0.020: BTC/ETH 0.559 and 0.594; SOL 0.865 and 0.918; spread 0.359
- tolerance 0.050: BTC/ETH 1.384 and 1.417; SOL 2.139 and 2.190; spread 0.807
- tolerance 0.110: BTC/ETH 2.899 and 2.931; SOL 4.480 and 4.529; spread 1.630
- tolerance 0.200: BTC/ETH 4.887 and 4.917; SOL 7.553 and 7.598; spread 2.711
- tolerance 0.300: BTC/ETH 6.774 and 6.801; SOL 10.469 and 10.510; spread 3.737

**AND THE UNVALIDATED FRACTION OF THE COST TERM IS NEARLY FLAT IN THE
TOLERANCE**: BTCUSDT and ETHUSDT move from 28.53 to 29.35 percent across the
entire grid, SOLUSDT from 44.09 to 45.36.

### 5.3 THE FACT THAT CARRIES THE FINDING

> **SOLUSDT's UNVALIDATED SHARE IS A CONSTANT MULTIPLE OF BTCUSDT's — 1.5455 —
> AT EVERY POINT OF THE GRID.** The maximum and the minimum of that ratio agree
> to within 1e-12.

The tolerance enters both symbols identically; only the haircut rate differs. **So
the symbol effect is exactly MULTIPLICATIVE and exactly INVARIANT to the
parameter**, while the tolerance's effect on the same quantity is a range that
grows with the level of the quantity itself.

### 5.4 THE TWO QUANTITIES §4 COMPARES

- **`S_max` = 3.7367 percentage points**, at tolerance 0.300.
- **`R_min` = 6.2069 percentage points**, at the BTCUSDT short cell.
- **Ratio `S_max / R_min` = 0.6020.**

---

## 6. THE FINDING

### 6.1 THE VERDICT, APPLYING §4 AS WRITTEN

> ### THE TRIGGER DOES NOT FIRE.
>
> **`S_max / R_min` = 0.6020, against a firing threshold of 1.0.** The most
> adverse cross-symbol spread anywhere on the grid is **about three fifths** of
> the least generous single-cell sensitivity.

**IT IS NOT A MARGINAL CALL ON ITS OWN UNITS** — 0.6020 is not near 1.0 — **and
§4.4 recorded before the answer was known that this construction is biased
toward firing**, so a non-firing verdict under it is the stronger of the two
verdicts it could return.

### 6.2 WHAT FOLLOWS, AND ONLY THIS

**THE TOTAL-COST DENOMINATION COMMITTED AT 4.1a STANDS AS A UNIFORM PROXY, AND
4.1c-PROPER PROCEEDS.** 4.1b §5's trigger for reopening 4.1a **has not fired**,
and 4.1a is not reopened.

**NO FOLLOW-ON DOCUMENT IS WRITTEN HERE.**

### 6.3 A LIMITATION OF THE TEST, RECORDED WITHOUT REVISING IT

**§4.5 forbids revising the threshold after seeing the numbers, and it is not
revised. The verdict above stands as the instrument returned it.** What follows
is recorded so that whoever writes 4.1c-proper has it in view.

**THE VERDICT IS SENSITIVE TO WHICH QUANTITY THE TEST IS DENOMINATED IN, AND THE
SENSITIVITY IS LARGE.** Evaluating the identical criterion on the unvalidated
term's **fraction of the cost** rather than its **share of the risk unit** gives
`S_max` = 18.2888 points, `R_min` = 0.8235 points, and a ratio of **22.2078** —
**it would fire, by a factor of more than twenty.**

**§3.4 CHOSE THE SHARE OF THE RISK UNIT, AND CHOSE IT BEFORE ANY VALUE EXISTED**,
on the ground that `04_1b_tolerance_and_branch.md` §3.2 defines the protected
quantity as a share of the risk unit. **That reasoning is unchanged by the
numbers and the choice is not revisited here.**

**BUT THE STRUCTURE §5.3 EXPOSES IS NOT CAPTURED BY EITHER FORM.** The symbol
effect is a **constant multiplicative factor of 1.5455** that no choice of
tolerance can alter. §4's criterion compares **additive ranges**, and an additive
comparison is dominated by the scale of the quantity at the loose end of the
grid — which is why the same structure reads as 0.6020 in one denomination and
22.2078 in another.

> **THE HONEST STATEMENT: A CONSTANT MULTIPLICATIVE NON-UNIFORMITY OF ABOUT 55%
> EXISTS AND IS OUTSIDE THE PARAMETER'S CONTROL, AND §4's ADDITIVE TEST DOES NOT
> SEE IT AS DECISIVE.**

**WHAT THAT DOES AND DOES NOT LICENSE.** It does not license overturning §6.1 —
the threshold was committed first precisely so that it would not be reinterpreted
once its answer was visible, and reinterpreting it here would be the failure the
4.1 split exists to prevent. **It does mean the question 4.1c-proper inherits is
not fully settled by this test**, and that a multiplicative formulation of the
same question is available to it and was not the one committed.

**IT IS RECORDED AS A LIMITATION OF THE INSTRUMENT, NOT AS A SECOND VERDICT.**

### 6.4 THE ORDER, CHECKABLE

- **Threshold commit, §1 to §4 alone: `af7866d7`.** `src/analysis/haircut_share.py`
  is **absent from that commit's tree** — verifiable with `git ls-tree`.
- **Derivation commit, §5 to §7 and the module: the commit carrying this text.**

**§1 to §4 ARE BYTE-IDENTICAL BETWEEN THE TWO COMMITS.** The diff shows additions
below the §4 boundary and no change above it.

---

## 7. WHAT THIS DOCUMENT DOES NOT DO

- **It sets no tolerance value**, and proposes none. Every quantity is reported
  across the committed grid; no point on it is selected. **Owed to 4.1c-proper.**
- **It evaluates no floor width beyond what the decomposition requires.** The
  widths used are report 32's committed closed form, imported unchanged, and no
  new width is stated. **Owed to 4.1c-proper.**
- **It does not reopen 4.1a**, whose §8 is the only route and which is not
  triggered by §6.1's verdict.
- **It does not perform the dominance check** named as owed at
  `docs/design/04_1a_denomination.md` §4.1. **Owed to 4.1c-proper.**
- **It does not dispose of kill condition (d)**, whose level question
  `docs/handoff/31_point_5_closing.md` §5.9 leaves open. **Owed to
  4.1c-proper.**
- **It sets no magnitude threshold** for the after-costs risk rule. **Owed to
  4.1c-proper.**

---

**The threshold was committed alone, before the module existed. The derivation
was run against it and the verdict applied as written: the trigger does not fire
at 0.6020 of the firing level. One limitation of the instrument is recorded
without revising it, and one structural fact — a constant multiplicative
non-uniformity of about 55%, invariant to the parameter — is handed forward. No
tolerance is selected, no width is recommended, and 4.1a is not reopened.**
