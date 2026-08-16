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

*(Written in commit two. §1 to §4 above are unchanged from commit one.)*

---

## 6. THE FINDING

*(Written in commit two.)*

---

## 7. WHAT THIS DOCUMENT DOES NOT DO

*(Written in commit two.)*
