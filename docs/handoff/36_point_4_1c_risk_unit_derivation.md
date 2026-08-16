# REPORT 36 — THE STOP FLOOR UNDER THE RISK-UNIT DENOMINATOR

**Point 4, sub-point 4.1c, the derivation.** A DERIVATION and a VERIFICATION. **No
tolerance is selected, no floor is recommended, and no non-uniformity verdict is
returned.**

**WHY THIS SITS UNDER `docs/handoff/`.** It is a derivation and a measurement, not
a decision. Design documents join the frozen specification on commit per
`docs/design/04_0_divergence_disposition_amendment_2.md` §2; a derivation does
not, and filing it under `docs/design/` would enrol a measurement in the
specification. Report 33's preamble states this and it is followed here.

**THE DENOMINATOR IT SOLVES UNDER** was committed at `a9083b0`:
`docs/design/04_1c_denominator_choice.md` §2.1 binds the constraint to the
unvalidated sum over the **risk unit** — path two's denominator, funding on both
sides — at most the tolerance.

**NOTHING IS INHERITED FROM REPORT 33.** Its closed form was solved over the stop
distance as denominator and over path one. Its grid bounds, its pole, its
direction split and its grid-selection reasoning are properties of that form.
Every one of those questions is re-opened here and answered from this algebra. The
module imports nothing from it, and a test asserts that over the module's imports.

---

## 1. PROVENANCE

- **Grid commit, alone and first: `de05a18`.** The solver is absent from that tree;
  §2.4 gives the proof.
- **Derivation module:** `src/analysis/risk_unit_floor_curve.py`.
- **Tests:** `tests/test_risk_unit_floor_curve.py` — path chosen after listing
  `tests/` in full and probing three candidates; all three were free and the first
  was taken.
- **Cost algebra:** `src/engine/costs.py`, `src/engine/sizing.py` and
  `src/engine/portfolio.py`, **read and called, never reimplemented.**

**NOT MODIFIED:** everything under `src/engine/`, `src/risk/`, `src/timeframe/`;
`src/analysis/floor_curve.py`, `haircut_share.py`, `haircut_floor_curve.py`,
`haircut_share_rerun.py`; every document under `docs/`.

### 1.1 The terms, and where each comes from

The risk unit is assembled exactly as `portfolio.size_position` assembles it at
`src/engine/portfolio.py:298-299` — `sizing.per_unit_denominator` plus
`portfolio.funding_per_unit` — composed from those two functions rather than
retyped, and **without invoking `size_position` itself**, which would floor a
quantity and solve a target this derivation has no use for.

- **The price move**, `src/engine/costs.py:332`. The stop distance.
- **The entry taker fee**, `src/engine/costs.py:336`, on the entry price.
- **The stop-leg taker fee**, `src/engine/costs.py:336`, on the stop price.
- **The entry slippage**, `src/engine/costs.py:330`, on the entry price. Frozen at
  zero; §5.1 exercises it at a value where it is reachable.
- **The stop haircut**, `src/engine/costs.py:331`, on the stop price. The only
  per-symbol rate.
- **The funding term**, `src/engine/portfolio.py:187`, on the entry price,
  independent of the width.

**THE UNVALIDATED SET IS A SET WITH ATTACHMENT POINTS** — the haircut on the stop
price, entry slippage and funding on the entry price — not a list of hardcoded
terms. **An unknown attachment point raises**; §5.2 exercises that.

**THE NUMERATOR IS RECOVERED BY DIFFERENCE**, never restated: the risk unit less
the same assembly with the config-borne unvalidated rates zeroed and the funding
term omitted.

---

## 2. PART A — THE ACHIEVABLE RANGE, ESTABLISHED BEFORE THE GRID EXISTED

Writing everything as a fraction of the entry price, with `w` the fractional
width, `sigma` equal to −1 for a long and +1 for a short so the stop is
`entry (1 + sigma w)`, `f` the taker rate, `h` the haircut rate, and `A` the total
of the unvalidated rates:

    unvalidated  U = A + sigma * w * h
    risk unit    d = A + 2f + w * (1 + sigma * (f + h))

### 2.1 The limit as the width vanishes, and what sets it

**AT ZERO WIDTH THE STOP PRICE IS THE ENTRY PRICE**, every term collapses onto one
price, and the direction drops out:

    limit = A / (A + 2f)

**IT IS DIRECTION-INDEPENDENT, AND IT IS SET BY THE UNVALIDATED TOTAL AGAINST TWO
TAKER LEGS AND NOTHING ELSE.** With entry slippage frozen at zero, `A` is the
haircut plus funding: 0.0005 + 0.0003 for BTCUSDT and ETHUSDT, 0.0010 + 0.0003 for
SOLUSDT, against a taker rate of 0.0006.

- **BTCUSDT and ETHUSDT: 0.40.**
- **SOLUSDT: 0.52.**

Verified as a limit rather than asserted: the gap to it falls by a factor of ten
for each decade of width, first order, over six decades, and the test asserts that
**order of convergence** rather than closeness at one point.

### 2.2 The behaviour at the frozen cap

At `cfg.stop_max_pct = 0.035` the ratio takes its lowest admissible value:

- **BTCUSDT and ETHUSDT long: 0.02117068. Short: 0.02207163.**
- **SOLUSDT long: 0.03378378. Short: 0.03554692.**

### 2.3 Monotonicity, measured

**ALL SIX CELLS ARE STRICTLY DECREASING IN THE WIDTH**, over a sweep of 20,001
points from just above zero to the cap. **No curve claimed monotone was found
otherwise.** The sign of the derivative is in fact independent of the width — it is
`sigma h (A + 2f) − A (1 + sigma (f + h))`, a constant — but that is a consequence
of the algebra and the result reported here is the measurement.

### 2.4 THE ACHIEVABLE RANGE, AND IT DIFFERS BY SYMBOL

Given monotonicity, the tolerances a width in the open interval up to the cap can
deliver are the open interval from the value at the cap to the zero-width limit:

- **BTCUSDT long: 0.02117068 to 0.40.** Short: 0.02207163 to 0.40.
- **ETHUSDT: identical to BTCUSDT at every cell.**
- **SOLUSDT long: 0.03378378 to 0.52.** Short: 0.03554692 to 0.52.

> ### THE ACHIEVABLE RANGE DIFFERS BY SYMBOL, AT BOTH ENDS.

**ABOVE A SYMBOL'S CEILING ITS CONSTRAINT CANNOT BIND AT ANY WIDTH.** The ratio is
already below such a tolerance at every width, so no floor is required and none is
imposed. **For BTCUSDT and ETHUSDT that happens above 0.40. For SOLUSDT it happens
above 0.52.**

**A TOLERANCE BETWEEN 0.40 AND 0.52 THEREFORE BINDS SOLUSDT AND LEAVES BTCUSDT AND
ETHUSDT ENTIRELY UNCONSTRAINED.** That is a structural fact about the constraint
under this denominator and 4.1c will need it. It is stated without softening and
**no value is recommended.**

**BELOW A CELL'S VALUE AT THE CAP the required width exceeds the frozen cap.** The
binding cell there is SOLUSDT short at 0.03554692.

The solver **refuses** rather than returning a number outside these bounds, and
tests exercise the refusal on the symbol whose ceiling is lower while requiring the
other symbol still to solve.

### 2.5 The grid, and the proof of order

**COMMITTED AT `de05a18`, ALONE, BEFORE THE SOLVER EXISTED.**

    0.036 to 0.396 inclusive, step 0.004, ninety-one points

**THE SELECTION RULE:** every multiple of the step lying **strictly inside the
common achievable interval** — the highest floor across cells to the lowest ceiling
across cells, which is 0.03554692 to 0.40.

- **THE LOWER END IS FIXED BY SOLUSDT SHORT's VALUE AT THE CAP, 0.03554692.**
  0.036 is the first multiple of the step above it. Below that, that cell would
  need a width the frozen cap forbids.
- **THE UPPER END IS FIXED BY BTCUSDT's AND ETHUSDT's ZERO-WIDTH LIMIT, 0.40.**
  0.396 is the last multiple strictly below it. At or above it those two cells
  impose no floor at all.
- **THE STEP IS A RESOLUTION CHOICE AND IS STATED AS CHOSEN, NOT DERIVED.** It
  divides both bounds exactly. No result depends on it.

**A TEST RE-DERIVES THE GRID FROM THE ACHIEVABLE RANGE** and asserts equality, so
the grid satisfies its stated rule rather than merely recording numbers.

**NOTHING IS CARRIED FROM REPORT 33**, whose grid ran 0.030 to 0.120 at step
0.0025 and was chosen so every cell was satisfiable within the cap under a
different denominator. Both bounds, the step and the count differ, and a test
asserts the two grids are not equal and that this module imports nothing from
that one.

**THE PROOF THAT THE SOLVER IS ABSENT FROM THE GRID COMMIT'S TREE** is at §7.3:
`git ls-tree` shows the module present at `de05a18`, and parsing that blob's AST
shows the function list contains no inversion — only the forward ratio, its
limits, the monotonicity sweep and the range.

---

## 3. PART B — THE CLOSED FORM

### 3.1 THE SELF-REFERENTIAL DENOMINATOR RESOLVES, AND THE REASON IS NOT AN ASSUMPTION

**The risk unit contains the stop distance, which is the quantity being solved
for.** The equation is genuinely self-referential.

> ### IT YIELDS A CLOSED FORM, BECAUSE BOTH SIDES ARE AFFINE IN THE WIDTH.

The width enters the numerator once, through the haircut on a stop price that
moves linearly with it, and the denominator once, through the move and the
stop-attached rates. `U = tau d` is therefore a **linear** equation in the width.

**NO FIXED POINT AND NO ITERATION IS REQUIRED.** That is a derived result and not
a convenience: it would fail the moment any unvalidated rate were charged on a
quantity that is not affine in the width. **It is asserted by test** — a
three-point second difference of both the numerator and the risk unit is zero at
every cell — and a further test asserts the module contains no solver loop and
calls no root-finder.

### 3.2 The form

    w = [ A (1 - tau) - 2 f tau ] / [ tau (1 + sigma (f + h)) - sigma h ]

Hand-computed positive controls, checked against the module to within 1e-14:

- **BTCUSDT long at tolerance 0.100.** Numerator 0.0008 × 0.9 − 0.0012 × 0.1 =
  0.00060. Denominator 0.1 × (1 − 0.0011) + 0.0005 = 0.10039.
- **SOLUSDT short at tolerance 0.100.** Numerator 0.0013 × 0.9 − 0.0012 × 0.1 =
  0.00105. Denominator 0.1 × (1 + 0.0016) − 0.0010 = 0.09916.

### 3.3 The widths, per symbol and per direction

Required width as a percentage of the entry price, long then short.

- **Tolerance 0.036.** BTCUSDT and ETHUSDT 1.9967 and 2.0484. SOLUSDT 3.2754 and
  3.4515.
- **Tolerance 0.048.** BTCUSDT and ETHUSDT 1.4531 and 1.4805. SOLUSDT 2.4119 and
  2.5065.
- **Tolerance 0.060.** BTCUSDT and ETHUSDT 1.1252 and 1.1416. SOLUSDT 1.8882 and
  1.9460.
- **Tolerance 0.080.** BTCUSDT and ETHUSDT 0.7959 and 0.8041. SOLUSDT 1.3602 and
  1.3902.
- **Tolerance 0.100.** BTCUSDT and ETHUSDT 0.5977 and 0.6023. SOLUSDT 1.0413 and
  1.0589.
- **Tolerance 0.140.** BTCUSDT and ETHUSDT 0.3705 and 0.3723. SOLUSDT 0.6748 and
  0.6824.
- **Tolerance 0.200.** BTCUSDT and ETHUSDT 0.1997 and 0.2003. SOLUSDT 0.3986 and
  0.4014.
- **Tolerance 0.280.** BTCUSDT and ETHUSDT 0.0857 and 0.0858. SOLUSDT 0.2139 and
  0.2147.
- **Tolerance 0.396.** BTCUSDT and ETHUSDT 0.0020 and 0.0020. SOLUSDT 0.0782 and
  0.0784.

**BTCUSDT AND ETHUSDT ARE IDENTICAL AT EVERY CELL**, sharing every rate the
constraint touches.

**NO VALUE IS RECOMMENDED AND NO ROW IS PREFERRED.** The table is the curve.

### 3.4 THE DIRECTION SPLIT — DERIVED, AND ITS NEGATIVE CONDITION EXERCISED

**A SPLIT ARISES, AND SHORTS REQUIRE THE WIDER FLOOR AT EVERY TOLERANCE.**

**ITS FORM:** `sigma` enters through the rates charged on the **stop price**, whose
distance from entry moves with the width in a direction-dependent way. On a short
the stop price rises above entry, so both the haircut and the stop-leg taker fee
are charged on a larger number; on a long they are charged on a smaller one.
**Funding does not contribute to the split at all** — it is charged on the entry
price and is independent of the width — and neither does the entry-leg fee.

**THE SPLIT NARROWS AS THE TOLERANCE RISES**, because the width itself shrinks and
the split is carried by the width-dependent part. It is 0.0517 percentage points
on BTCUSDT and 0.1761 on SOLUSDT at tolerance 0.036, and 0.0047 and 0.0176 at
tolerance 0.100.

> **WHAT WOULD HAVE CONSTITUTED SHOWING THAT NO SPLIT ARISES:** the solved widths
> coinciding for long and short at every tolerance, which happens if and only if
> `sigma` drops out of both expressions. **That needs BOTH stop-attached rates to
> vanish — the haircut and the taker fee.**

**THAT CONDITION IS EXERCISED BY TEST, SO A NEGATIVE RESULT WOULD HAVE BEEN
CHECKABLE:**

- **With the haircut zeroed alone, the split SURVIVES**, carried by the stop-leg
  taker fee. This is the case that would have been missed by assuming the haircut
  is the only stop-attached rate.
- **With the haircut and the taker fee both zeroed, the split VANISHES exactly**,
  long and short agreeing to within 1e-15.

### 3.5 THE POLE — DERIVED, AND DIRECTION-ASYMMETRIC

Setting the closed form's denominator to zero:

    tau_pole = sigma * h / (1 + sigma * (f + h))

- **FOR A LONG IT IS NEGATIVE**, `−h / (1 − f − h)`, and therefore not a tolerance.
  **There is no pole at any admissible tolerance on a long.**
- **FOR A SHORT IT IS POSITIVE**, `h / (1 + f + h)`. **BTCUSDT and ETHUSDT:
  0.00049945. SOLUSDT: 0.00099840.**

**WHAT IT MEANS.** It is the ratio's asymptote as the width grows without bound. A
short's unvalidated sum **grows** with the width, because the haircut is charged on
a stop price moving away from entry, so the ratio cannot be driven below that value
at any width. **A tolerance below it is unreachable on a short by geometry alone.**
Tested: the short ratio approaches it from above at widths of 1, 10, 100 and 1000
and never crosses it, and the solver refuses a tolerance at half the pole.

**BOTH POLES SIT FAR BELOW THE COMMITTED GRID** — more than an order of magnitude
below its lower bound — so no grid cell is near one, which is why the curve is well
behaved throughout. **This is not report 33's pole and was not derived by analogy
with it.**

---

## 4. PART C — VERIFICATION AGAINST THE IMPLEMENTATION

**546 cells: ninety-one tolerances by three symbols by two directions.**

### 4.1 The feedback check

Every solved width is fed back through the path-two denominator, the unvalidated
sum and the risk unit are recomputed **from the engine's own functions**, and the
ratio is required to equal the tolerance it was solved for. **The closed form is
never trusted to check itself.**

> **MAXIMUM ABSOLUTE FEEDBACK RESIDUAL ACROSS ALL 546 CELLS: 2.037e-14.**

### 4.2 The decomposition

Move plus validated cost plus unvalidated cost must equal the risk unit at every
cell.

> **MAXIMUM ABSOLUTE DECOMPOSITION RESIDUAL: 0.000e+00, exactly.**

### 4.3 Price invariance

Every solved width recomputed at entry prices of 120.5, 3,000.0 and 95,000.0 —
three widely separated scales.

> **MAXIMUM WIDTH SPREAD ACROSS PRICES: 0.000e+00, exactly.** The width is a
> fraction and every rate is charged proportionally to a price, so the price
> cancels — and that is now asserted rather than assumed.

---

## 5. THE SET PROBE

### 5.1 Switching entry slippage on

Entry slippage is frozen at zero. Raised to 5 bps, **all four required things
move**: the unvalidated sum rises, the ratio at a fixed width rises, the solved
width rises, and the zero-width ceiling rises with the unvalidated total. **The new
width still reproduces its tolerance to within 1e-12**, so the term entered both
the numerator and the denominator consistently.

This is the treatment document 05 §4 gave the inert partial branch: a term
unreachable at present values is exercised at values where it is reachable.

### 5.2 An unknown attachment point raises

Two probes, both required to raise rather than silently drop a term:

- **A term charged against a price the module does not know** — asking for an
  attachment point of `mark_price` raises `UnknownAttachmentPoint`.
- **A term injected into the set with an unknown attachment point** raises when the
  rates are read, rather than being skipped and leaving the numerator short.

A third probe requires a term with a **known** attachment point but **no rate
source** to raise as well: membership without a rate is a hole, not a zero.

---

## 6. ONE NUMERICAL BOUNDARY, FOUND AND HANDLED WITHOUT A TUNED CONSTANT

**AT EXACTLY A SYMBOL's CEILING THE CLOSED FORM's NUMERATOR IS AN EXACT ZERO.**
In floating point it is not: at tolerance 0.40 on BTCUSDT it evaluates to
5.42e-20, and dividing by the denominator yields a width of 1.36e-19 — positive,
and meaningless. **A guard testing the sign of the solved width therefore admitted
a tolerance it should have refused.**

**THE FIX WAS NOT AN EPSILON.** Adding a small threshold would have been a
numerical criterion written from a mental model of the quantity, which is the
defect class the ledger tracks. Instead the admissibility test was moved onto **the
structural bound itself** — the tolerance is compared against `A / (A + 2f)`,
computed from the same rates. That introduces no tuned constant and refuses
exactly where the algebra says no positive width exists.

**IT IS RECORDED HERE RATHER THAN CORRECTED SILENTLY**, and a test pins the
boundary from both sides: just below the ceiling a positive width exists and is
smaller than 1e-8, and at and above it the solver raises.

---

## 7. WHAT THIS STEP DOES NOT DO

### 7.1 It returns no non-uniformity verdict

**Under this denominator the constraint and the protected quantity are the same
object, so the cross-symbol spread of the protected quantity is zero by
construction.** `docs/design/04_1c_denominator_choice.md` §3.3 states that the
prior apparatus is **INAPPLICABLE rather than satisfied**, and §3.4 forbids
reporting the resulting ratio as a favourable margin.

> **NO SUCH RATIO IS COMPUTED AND NONE IS REPORTED HERE.** The symbol-dependent
> structure that section says moves into the widths is visible at §3.3 as the
> widths themselves, reported as a curve and not as a verdict.

### 7.2 It selects nothing and settles nothing else

**It selects no tolerance value and recommends no floor.** It does not settle
floor-versus-cap precedence, does not restratify any population, does not touch
kill condition (d), sets no magnitude threshold, and performs no dominance check.
`docs/design/04_1c_pre_commitments.md` and `docs/design/04_1c_proper.md` own those,
in that order.

**NO OUTCOME QUANTITY WAS COMPUTED, INSPECTED OR ESTIMATED.** No exit was resolved;
`exit_reason` was not read; the portfolio engine's execution loop was not invoked
and `size_position` is called nowhere, asserted over the module's AST. **Nothing
under `data/` was opened, listed or read** — verified at runtime by tracing every
file open while the whole curve was built: zero.

### 7.3 What the superseded artifacts still are

**REPORTS 32, 33 AND 34 REMAIN CORRECT ANSWERS TO THE QUESTIONS THEY WERE ASKED.
THEY ARE SUPERSEDED AS GOVERNING AND NONE IS FALSIFIED.** This report is not to be
read as impeaching them.

- **Report 32** remains the correct relation between the old ratio and width,
  verified to a maximum residual of 5.662e-15.
- **Report 33** remains the correct required-floor relation under the unvalidated
  numerator over the stop distance, with its own grid, split and pole.
- **Report 34** remains the correct measurement of path one's protected-quantity
  shares at report 33's floor.

Each answered the question its denomination posed. **The denomination changed; the
answers did not become wrong.**

**THE PROOF OF COMMIT ORDER.** At `de05a18`, `git ls-tree` lists
`src/analysis/risk_unit_floor_curve.py`, and parsing that blob's AST gives fifteen
functions — the forward ratio, its zero-width limit, its value at the cap, the
monotonicity sweep, the achievable range and the grid — and **no inversion of any
kind**. `required_floor_fraction`, `pole`, `form_constants`, `curve` and every
verification helper first appear in the derivation commit.

---

## 8. ARTIFACTS

- **Report:** `docs/handoff/36_point_4_1c_risk_unit_derivation.md`
- **Module:** `src/analysis/risk_unit_floor_curve.py`
- **Tests, 34 added:** `tests/test_risk_unit_floor_curve.py`
- **Grid commit:** `de05a18`

**Full suite: 1247 passed** — 1213 before this step, plus the 34 above.
