# Report 34 — the non-uniformity check, re-run under the revised denomination

**Sub-point 4.1a. Status: the re-run is complete and its result is CASE (a) — the
trigger does not fire AND the cross-symbol ratio is no longer invariant.**

The original check (`docs/design/04_1c_non_uniformity_check.md`) returned a
non-firing verdict that was worth nothing, because the structure underneath it
showed the parameter had **zero** authority over the quantity the criterion was
watching: SOLUSDT's unvalidated share was a constant multiple of BTCUSDT's —
1.5455 — at every point of a fifteen-fold parameter sweep. A criterion cannot
clear a non-uniformity that no setting of its own parameter can move.

The denomination has since changed (`docs/design/04_1a_denomination_amendment_1.md`)
and the floor has been re-derived on the new one (report 33). This report re-runs
the same check, with the same criterion, at the new floor.

**The headline: the invariance is broken.** The cross-symbol ratio now runs from
1.0338 to 1.1139 across the grid and rises monotonically with the tolerance. The
parameter has authority over it. The non-firing verdict therefore now means
something, and what it means is stated in §3.5.

---

## 1. The membership axiom, and its reach

### 1.1 The axiom

> **A cost term is UNVALIDATED if its magnitude is not fixed by contract or by
> the venue's published fee schedule, but is instead estimated, assumed or
> carried over from another source.**

Applied to the terms `sizing.per_unit_denominator` actually carries:

| Term | Fixed by | Status |
|---|---|---|
| `taker_fee` | Bitget's published schedule | validated |
| `stop_haircut_bps` | estimated per symbol | **UNVALIDATED** |
| `entry_slippage_bps` | estimated | **UNVALIDATED** |

This is the same membership the derivation used. Nothing about it is new here.

### 1.2 THE REQUIRED CHECK ON `entry_slippage_bps` — AND ITS RESULT

The prompt requires this to be verified rather than assumed, and requires the
report to stop if it fails.

**`src/engine/costs.py:71` — `entry_slippage_bps: float = 0.0`. The frozen value
is ZERO.** Verified by reading the field's default off the dataclass and by
evaluating `ep.cost_config().entry_slippage_bps`, both giving `0.0`.

**IT DOES NOT FAIL. The membership is correct AND the term is inert.** Both
things are true at once and it matters that they are separated:

- The term **is** a member of the unvalidated set by the axiom. It is estimated,
  not published. If it were ever given a non-zero value it would enter every
  figure in this report through `hfc.unvalidated_rates`, which reads it.
- At its frozen value it contributes exactly nothing. Every number below is
  therefore carried by `stop_haircut_bps` alone.

**The consequence for reading this report:** the cross-symbol structure measured
in §3 is entirely the haircut's structure. A future decision to give entry
slippage a non-zero value **does not invalidate this report's method but does
invalidate its numbers**, and — because entry slippage is currently a single
symbol-independent scalar while the haircut is per-symbol — it would move the
cross-symbol ratio **toward** unity. That direction is asserted from the
algebra's shape, not measured, and is flagged for whoever sets that value.

### 1.3 What the axiom implies for the funding rate — AND THAT IT WAS NOT ACTED ON

**By the axiom, the funding rate IS unvalidated.** `FUNDING_RATE_PER_SETTLEMENT
= 0.0001` at `src/risk/exit_spec.py:115`, and document 06 line 358 records it in
terms that decide the question:

> "AN ASSUMPTION, NOT A MEASUREMENT."

It is not fixed by contract — Bitget's funding rate floats — and it is not on a
published fee schedule. It is an assumed constant. It satisfies the axiom.

**IT IS NOT IN THIS REPORT'S FIGURES, AND THAT IS A GAP, NOT A JUDGEMENT THAT IT
DOES NOT BELONG.** The reason is mechanical: `costs.position_size` carries no
funding term at all. The constrained ratio is built by difference against that
denominator, so a term the denominator does not contain cannot appear in the
difference. Funding is unvalidated *and* outside the cost model the constraint
ranges over.

So the axiom implies the constrained ratio is **under-inclusive**: it constrains
a proper subset of the unvalidated cost. **This report states that and stops.**
It does not act on it, because acting on it would mean re-deriving the closed
form over a different cost model — the portfolio path's, which per
`docs/design/06a_exit_resolution_spec_amendment_1.md` E7.2 does carry funding —
and that would change every figure below while answering a question this step
was not given. **Routed to 4.1c as an open item (§5.3).** Applying it selectively
here, to some cells or as a footnote adjustment, would be worse than not applying
it at all.

---

## 2. The threshold — restated, NOT retuned

### 2.1 The criterion, as committed

Committed at **`af7866d`**, "4.1c: the non-uniformity threshold, committed before
the derivation exists", in its own commit, before the solver that produced any
number it would judge:

- `S(tau)` — the spread of the protected quantity across symbols and directions
  at one tolerance. `S_max` is its maximum over the grid.
- `R(cell)` — the range of the protected quantity for one symbol-direction cell
  across the whole grid. `R_min` is its minimum over the six cells.

> ### THE TRIGGER FIRES IF AND ONLY IF `S_max >= R_min`.

Reported as the ratio `S_max / R_min`, firing at 1.0 or above.

The protected quantity is unchanged: the share of the **risk unit** determined by
estimate rather than by contract (`docs/design/04_1b_tolerance_and_branch.md`
§3.2).

### 2.2 It is REUSED, not re-implemented

`haircut_share_rerun.verdict` calls `haircut_share.threshold_verdict` — the same
function object the original run called. `tests/test_haircut_share_rerun.py`
asserts over the module's AST that no second copy of it exists here, and that
`PROTECTED` is the same object. **A restated criterion could drift; a reused one
cannot.** This is what makes the two verdicts comparable.

**No parameter of the criterion has been changed.** Not the statistic, not the
direction of the comparison, not the firing level.

### 2.3 WHAT WOULD MAKE THE VERDICT MEANINGFUL — decided in advance of reading it

The original run established that a non-firing verdict is not by itself evidence
of anything. Two cases were distinguished:

- **(a) The trigger does not fire AND the cross-symbol ratio is no longer
  invariant.** The parameter has authority; the criterion is measuring something
  it can affect; verdict and structure agree.
- **(b) The trigger does not fire BUT the ratio is still invariant.** The
  criterion is still blind and the problem has been moved, not fixed — the
  re-denomination shrank the number without changing the structure.

**THE RESULT IS CASE (a).** Stated here, before the figures, so it cannot be read
as chosen after them.

---

## 3. The measurement

### 3.1 Method

For each of 37 tolerances on report 33's committed grid (0.030 to 0.120, step
0.0025), each of three symbols and both directions — 222 cells:

1. The required floor width from `hfc.required_floor_fraction`, report 33's
   verified closed form.
2. The risk unit from `sizing.per_unit_denominator` at that width.
3. The unvalidated part **by difference**: that denominator, less the same
   denominator computed with the unvalidated set zeroed.
4. The protected quantity: the unvalidated part over the risk unit.

**Verification carried in the table itself.** Every row records the ratio of its
unvalidated sum to its stop distance, which must equal its own tolerance:

- **Solve residual: 3.761e-15.** The widths solve the constraint they were solved
  for; the shares are measured at the right floor.
- **Decomposition residual: 0.000e+00, exactly.** Validated plus unvalidated
  equals total at every cell.

### 3.2 The protected quantity, as a percentage of a risk unit

BTCUSDT and ETHUSDT are identical at every cell to within 1e-15 — they share
every rate the constraint touches — and are reported together.

| tolerance | BTC/ETH long | BTC/ETH short | SOL long | SOL short |
|---|---|---|---|---|
| 0.0300 | 2.721 | 2.724 | 2.813 | 2.816 |
| 0.0400 | 3.519 | 3.523 | 3.674 | 3.678 |
| 0.0500 | 4.271 | 4.276 | 4.502 | 4.507 |
| 0.0675 | 5.487 | 5.493 | 5.874 | 5.880 |
| 0.0800 | 6.286 | 6.292 | 6.799 | 6.806 |
| 0.1000 | 7.459 | 7.466 | 8.193 | 8.201 |
| 0.1200 | 8.519 | 8.526 | 9.489 | 9.498 |

The long/short split is small — a few thousandths of a percentage point — and has
the sign report 33 derived.

### 3.3 THE CENTRAL RESULT — the cross-symbol ratio

SOLUSDT's protected share over BTCUSDT's, at every grid point:

| tolerance | ratio (long) |
|---|---|
| 0.0300 | 1.033752 |
| 0.0500 | 1.054025 |
| 0.0675 | 1.070490 |
| 0.0900 | 1.090105 |
| 0.1200 | 1.113870 |

- **Long: 1.033752 → 1.113870. Span 0.080118. Rising monotonically.**
- **Short: 1.033790 → 1.113978. Span 0.080188. Rising monotonically.**
- **Flatness test at 1e-12: FALSE, in both directions.**

Against the original run's finding of **1.5455, flat to within 1e-12**.

Two things changed, and they are separate findings:

1. **The magnitude fell.** The cross-symbol non-uniformity went from a fixed 55%
   to between 3.4% and 11.4%.
2. **The invariance broke.** This is the one that matters. The tolerance now
   moves the ratio, so the criterion is watching a quantity its own parameter can
   affect.

**And the direction is informative:** the ratio is *nearer* to unity at *tighter*
tolerance. Loosening the tolerance does not merely cost more, it costs SOLUSDT
disproportionately more. That is a live trade-off for whoever sets the value at
4.1c, and it did not exist under the old denomination.

### 3.4 THE FLATNESS TEST IS SHOWN TO DISCRIMINATE

A flatness predicate that answered "not flat" to everything would report success
here whatever had happened. `test_the_flatness_test_TELLS_THE_TWO_DENOMINATIONS_APART`
hands the **same predicate at the same 1e-12 precision** both tables and requires
opposite answers:

- old denomination's table → **True** (it really is flat)
- revised table → **False**

**The instrument can tell case (a) from case (b). That is why §3.3 is admissible
as evidence and not merely as a number.**

### 3.5 The verdict, and what it now means

Committed criterion, applied unchanged:

- **`S_max` = 0.9791 percentage points**, at tolerance 0.1200.
- **`R_min` = 5.7983 percentage points**, at the BTCUSDT long cell.
- **Ratio `S_max / R_min` = 0.1689, against a firing threshold of 1.0.**

> **THE TRIGGER DOES NOT FIRE. And per §2.3 this is CASE (a) — the ratio is not
> invariant, so the parameter has authority over the quantity the criterion
> watches, so the non-firing verdict is evidence and not an artefact.**

The most adverse cross-symbol spread anywhere on the grid is about one sixth of
the least generous single-cell sensitivity. It is not a marginal call: 0.1689 is
not near 1.0, and it moved in the right direction from 0.6020 for a structural
reason rather than by rescaling.

**The re-denomination worked.** The original run's diagnosis — that the criterion
was blind because the parameter could not move the thing it measured — no longer
holds.

---

## 4. The cap-clipped stratum

### 4.1 Where the floor meets the cap

The frozen cap is `stop_max_pct = 0.035`. Solved from report 33's closed form
rather than searched — with `a` the stop-attached unvalidated rate and `b` the
entry-attached one, the width equals the cap at

`long: tau = (a+b)/cap − a` `short: tau = (a+b)/cap + a`

| cell | crossing tolerance |
|---|---|
| BTC/ETH long | 0.013786 |
| BTC/ETH short | 0.014786 |
| SOL long | 0.027571 |
| SOL short | 0.029571 |

Hand-computed and asserted in the tests, together with the check that the
required floor really does equal the cap at each crossing and exceeds it just
below.

### 4.2 THE COUNT IS ZERO — AND WHY THAT IS NOT AN INTERESTING ZERO

**Cap-clipped cells on the grid: 0 of 222.**

**This is by construction of the grid, not by any property of the cap.** Report
33 §4 chose the grid's lower bound of 0.030 precisely so that every cell is
satisfiable within the cap — the largest crossing, SOLUSDT short at 0.029571,
sits just below it. **The stratum is empty because the grid was built to avoid
it, and reporting the zero without that sentence would be misleading.**

Below the grid it is not empty, and the tests assert this rather than leave it as
a claim: at tolerance 0.020, cells do exceed the cap.

### 4.3 The precedence question — asked, and answered as moot HERE ONLY

Whether the floor binds first or the cap does is a real ordering question and it
is not settled by this report.

**On this grid the two orderings give identical counts, both zero**, because no
cell reaches the cap at all. The question has no purchase on any figure above.

**IT IS NOT SETTLED IN GENERAL.** Any future tolerance below 0.0296 on a SOLUSDT
short, or below 0.0138 on a BTC/ETH long, makes the ordering load-bearing, and
nothing here decides it. Routed to 4.1c (§5.3).

---

## 5. What this report does not do

### 5.1 It selects no tolerance

**No value of the tolerance is chosen, recommended, or implied.** The grid is
report 33's, reused whole. §3.3's observation that tighter tolerances give more
uniform cross-symbol protection is a property of the curve, **not** an argument
for a tight tolerance — the countervailing considerations are 4.1c's to weigh.
The tests assert over the module's AST that no constant naming a selected
tolerance exists.

### 5.2 It computes no outcome quantity

No performance measure of any kind is computed, inspected or estimated. The
twelve-name firewall is asserted over this module's AST, over executable tokens
and non-docstring string constants, per the standing rule at
`docs/design/04_1a_denomination_amendment_1.md` §7. **Nothing under `data/` is
opened, listed or read** — this report is over rates and algebra only — and no
engine entry point is invoked, both asserted structurally.

### 5.3 Open items routed to 4.1c

1. **The constrained ratio is under-inclusive** (§1.3). Funding satisfies the
   membership axiom but is absent from the cost model the constraint ranges over.
   Deciding whether the constraint should range over the portfolio path's
   denominator instead is 4.1c's, and it would change every figure here.
2. **The floor/cap precedence is unsettled** (§4.3). Moot on this grid, live
   below 0.0296.
3. **Entry slippage is inert but live** (§1.2). A non-zero value re-opens §3's
   numbers and would move the ratio toward unity.

### 5.4 A better criterion exists — STATED, NOT APPLIED

The committed criterion compares an **additive** spread against an **additive**
range. The original run's failure was that a purely multiplicative symbol effect
is invisible to it. That weakness has not been repaired; it has been dodged,
because this denomination happens not to produce a purely multiplicative effect.

**The construction that would be robust to both** is to compare the cross-symbol
**ratio's** departure from unity against the parameter's authority over that
ratio — both quantities §3.3 already reports, and both dimensionless.

**ITS VERDICT IS NOT COMPUTED AND NOT REPORTED HERE.** Adopting a criterion after
seeing the data it would judge is exactly the failure the commit-order discipline
exists to prevent. It is offered to 4.1c as a recommendation, to be committed in
its own commit before any number it would judge exists, or rejected.

---

## Artifacts

| Artifact | Path |
|---|---|
| Measurement module | `src/analysis/haircut_share_rerun.py` |
| Tests (16) | `tests/test_haircut_share_rerun.py` |
| This report | `docs/handoff/34_point_4_1a_non_uniformity_rerun.md` |
| Criterion reused from | `src/analysis/haircut_share.py` (`af7866d`) |
| Floor reused from | `src/analysis/haircut_floor_curve.py` (`22e323a`) |

**Full suite: 1197 passed** — 1181 baseline, plus the 16 above.
