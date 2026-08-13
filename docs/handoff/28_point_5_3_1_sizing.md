# REPORT 28 — EXCHANGE-REAL POSITION SIZING, AND WHAT FLOORING COSTS

**Point 5, sub-point 5.3, step 1.** A BUILD and a MEASUREMENT. No exit is
evaluated, no trade outcome is computed, and no bar after a signal bar is read.

**WHY THIS EXISTS.** The closing record §6.1 established that `qty_step` is
*"parsed, stored, serialised and printed, and never read by sizing or
execution"* — every backtest to date sized in fractional quantities no exchange
would accept. **This step makes sizing exchange-real.**

**THE SECOND DEFECT IS THE MORE CONSEQUENTIAL ONE AND IT IS WHY THE MODULE
EXISTS AT ALL.** Once quantity is floored, realised risk falls below the $20.00
nominal. `costs.solve_target` solves for a **dollar** amount — `net = RR × risk_usd`
— so its answer **depends on the quantity**, and a floored quantity moves the
target. A stop-out then no longer returns exactly −1.0R and a target no longer
returns exactly +1.5R, and **the thesis's 40.0% breakeven and 53.6%
detectable-edge arithmetic stops describing the system.**

**THE FIX, IN ONE LINE.** The target is solved **per unit, in price space**, so
quantity cancels exactly and the target price is **invariant to the quantity**.
That invariance is the central test of this step (§4.2).

**THE COST, IN ONE LINE.** Flooring costs **0.80% of nominal risk** across the
11,384 candidates — **$1,826.85 of $227,680** — and **0.78%** across the 6,021
taken. **No position fails either viability condition, on either population.**

**`src/engine/costs.py` IS NOT MODIFIED.** Reports 24, 26 and 27 all call
`position_size` and changing it would silently invalidate three closed reports.
The new module **imports** its cost algebra and reuses it verbatim.

---

## 1. PROVENANCE

| item | value |
|---|---|
| `git rev-parse HEAD` at build | **`60b66f5`** — report 27 |
| sizing module | **`src/engine/sizing.py`** — pure functions, no data access |
| sizing tests | **`tests/test_sizing.py`** |
| measurement module | **`src/analysis/sizing_drag.py`** |
| measurement tests | **`tests/test_sizing_drag.py`** |
| population | `exposure_profile` + `budget_cost`, **both unmodified** |
| symbol specs | `config/contracts_cache.json`, **read, never retyped** |
| window | 2022-01-05T18:00Z – 2024-12-31T23:00Z |

**NOT MODIFIED:** `src/engine/costs.py` · `costs.CostConfig.max_leverage` (still
3.0) · `src/risk/budget.py` · `src/engine/simulate.py` ·
`src/analysis/sweep_population.py` · `src/analysis/exposure_profile.py` ·
`src/analysis/budget_cost.py` · `src/analysis/intrabar_span.py` ·
`config/contracts_cache.json` · every frozen document numbered 22, 22a, 23, 24,
25, 26, 27, 05, 05a and 05b.

### 1.1 What the sizing module is not allowed to be

| constraint | how it is enforced |
|---|---|
| **no risk-package import** | `src/engine` stays unwired. The risk unit is a **parameter**. Asserted over the import graph — and see §11.1, where this bit. |
| **no leverage refusal** | report 26 §12.1 established `max_leverage = 3.0` is an unmeasured placeholder that would bind on 16.14% of bars and censor the population the budget already governs. Asserted: no identifier, attribute or non-docstring string names it. |
| **no data access** | no `pandas`, no `numpy`, no data layer, no parquet, no 1m path. The only I/O is the contract cache. |
| **specs read, not retyped** | a test asserts **no numeric literal in the module equals any `qty_step`, `min_trade_num`, `min_trade_usdt` or price tick.** |

---

## 2. THE ORDER OF OPERATIONS, AS IMPLEMENTED

**THE STEPS ARE NOT COMMUTATIVE AND THE ORDER IS THE SPECIFICATION.**

    1. stop_distance   = max(2.25 x ATR(14, Wilder), 0.0150 x entry)
    2. stop_price      = entry -/+ stop_distance, ROUNDED TO THE PRICE TICK
    3. effective       = RECOMPUTED from the ROUNDED stop price
    4. denominator d   = the engine's own cost algebra, not the naive move
    5. qty_unfloored   = risk_usd / d
    6. qty             = FLOOR(qty_unfloored / qty_step) x qty_step
    7. realised_risk   = qty x d
    8. target_price    = solved PER UNIT, rounded to the tick
    9. viability       = two conditions; refusal is a SKIP

**STEP 3 IS NOT COSMETIC.** Everything downstream uses the **effective**
distance implied by the rounded stop, never the pre-rounding one. **A stop price
that is not on a tick is not a stop price**, so the distance that matters is the
one the exchange would honour. This is what makes the stop identity in §4.3
*exact* rather than off by the rounding residue.

**STEP 4 REUSES THE ENGINE RATHER THAN REIMPLEMENTING IT.** `d` is obtained by
**dividing the config's own risk unit by `costs.position_size`** — which returns
`risk_usd / d` — so the cost algebra cannot drift from the engine's even in
principle: there is one copy of it and it is `costs.py`'s. Sizing on the price
move alone is the naive form report 24 §2.1 measured as **7.4% wrong**, and a
test pins that the denominator is 1.074× the move on the reference case.

**STEP 6 FLOORS, NEVER ROUNDS, NEVER CEILS.** The closing record §6.1: *"Floor
is the only rounding direction that cannot breach the 1% rule; round-to-nearest
and ceil both can."* A test plants a round-to-nearest implementation and asserts
it **breaches the risk unit** on a real fixture while flooring does not.

---

## 3. THE PRICE-SPACE TARGET, AND THE QUANTITY-INVARIANCE RESULT

### 3.1 The derivation

**The condition is written per unit of quantity**, with `f` the entry taker fee,
`m` the **exit maker** fee, `e` the entry slippage and `d` the per-unit
denominator:

    long    (T - entry) - [ entry x f + T x m + entry x e ]  =  RR x d
    short   (entry - T) - [ entry x f + T x m + entry x e ]  =  RR x d

solving to

    long    T = ( RR d + entry (1 + f + e) ) / (1 - m)
    short   T = ( entry (1 - f - e) - RR d ) / (1 + m)

> **QUANTITY APPEARS ON NEITHER SIDE. IT CANCELS EXACTLY.**

**THE EXIT LEG IS MAKER, NOT TAKER.** Report 27 §3.3 established this from the
engine's own algebra; using the taker fee would place the target further out and
quietly change the reward the strategy aims at.

**`RR` IS 1.5 AND IS SUPPLIED EXPLICITLY.** `CostConfig.target_r_multiple`
**defaults to 2.0** — Point 4's 1:2 — while the thesis freezes 1.5. Amendment 1
§3 records the divergence and report 27 §3.2 is where it first became
load-bearing. **The module never reads the config field at all**; a test asserts
the string does not appear in its source, and separately that the value used is
1.5 and differs from the engine default.

**ENTRY SLIPPAGE APPEARS ON BOTH SIDES.** `d` includes it via `position_size`,
so the target cost includes it too. At the frozen configuration
`entry_slippage_bps` is **0**, so the term moves no number today — it is written
for consistency, not for effect, and `costs.solve_price_for_net` omits it for the
same reason it never mattered.

### 3.2 The result

**A test named `test_CENTRAL_the_target_price_is_invariant_to_quantity` sizes the
same position at a tenfold different risk unit** — quantity 10× apart — **and
requires the target price to be identical.** It is.

**The contrast is pinned too**: `costs.solve_target(entry, 0.0275, …)` and
`costs.solve_target(entry, 0.0276, …)` are asserted to **differ**, so the defect
and the fix are distinguishable by test rather than only by prose. **`costs.py`
is documented by that test, not changed by it.**

---

## 4. THE R IDENTITIES

### 4.1 The recorded firewall carve-out

> **VERIFYING THE IDENTITIES REQUIRES COMPUTING NET PROCEEDS AT A PRICE, WHICH
> IS OUTCOME-ADJACENT GROUND.** It is permitted here under three conditions,
> **all asserted by test**:
>
> - **synthetic reference inputs only.** `net_proceeds_per_unit` is never called
>   on a real signal, a real bar or a real position — a test asserts **no
>   function inside either module calls it**; only the tests do, on hand-chosen
>   values.
> - **exactly one named function**, asserted over the AST: the only function in
>   the module whose name contains `proceeds` is `net_proceeds_per_unit`.
> - **the blanket twelve-name ban otherwise intact.** It was not relaxed. The
>   function's name contains none of the twelve, so the carve-out is
>   **conceptual, not lexical** — which is why it is documented here rather than
>   exempted in code.
>
> **IT DOES NOT ASK WHETHER A PRICE WAS REACHED.** The exit price is supplied by
> the caller. It is arithmetic on two prices.

**A FIREWALL WITH AN UNDOCUMENTED EXCEPTION IS A FIREWALL NOBODY CAN AUDIT**,
which is why this section exists and why report 27 §9.4 set the precedent.

### 4.2 What holds

Asserted on six cells — three symbols × two directions — **at a floored
quantity**, with the fixtures chosen so `qty < qty_unfloored` on every one:

| identity | result |
|---|---|
| net proceeds at the stop price = **−1.0 × realised_risk_usd** | **exact**, to 1e-12 relative |
| net proceeds at the target price = **+1.5 × realised_risk_usd** | **exact up to one tick**, always favourable |
| both, LONG and SHORT | **hold** |
| both, at a floored quantity | **hold** — this is the case the fix exists for |

**THE STOP IDENTITY IS EXACT** because the denominator is recomputed from the
rounded stop (§2 step 3). **THE TARGET IDENTITY IS EXACT UP TO ONE TICK**, always
in the favourable direction, because the target rounds **away** from entry and
can therefore only deliver more than the reward, never less.

### 4.3 And what fails, so the two are distinguishable

**Solving the target for `1.5 × NOMINAL` over a floored quantity** — the old
behaviour — is asserted to **miss** the identity: the target lands further out
and the realised reward overshoots +1.5 realised units by exactly the flooring
residue, landing instead on `1.5 × nominal`. **A test asserts the miss**, so a
future regression to dollar-denominated solving fails rather than passes.

---

## 5. TICK ROUNDING — direction, argument, and measured magnitude

### 5.1 The convention already exists in the repository

`costs.stop_geometry` rounds the stop **away from entry** — *"Round the stop AWAY
from entry so rounding never tightens the risk"* — and
`costs.solve_price_for_net` rounds targets away too, so *"a level is never
claimed at a price that would deliver less"*. **The convention is present and
coherent, so it is followed rather than replaced**, on both legs.

| leg | direction | argument |
|---|---|---|
| **STOP** | long **down**, short **up** — **wider** | A wider stop is **not a larger loss**: the quantity is solved from the rounded stop, so the position simply gets smaller and the loss still caps at one risk unit. Rounding the other way would move the stop **inside** the structure report 21's excursion check exists to protect. |
| **TARGET** | long **up**, short **down** — **harder to reach** | Rounding a target away from entry can only **cost reward, never add it**, so the level never claims more than it delivers. |

> **THE TWO LEGS ARE NOT SYMMETRIC AND THE REPORT SAYS SO.** Rounding a target
> away costs reward outright. Rounding a stop away costs nothing, because
> quantity compensates. The same word — "away" — has different consequences on
> the two legs, and it is only the stop's compensation mechanism that makes the
> convention harmless there.

### 5.2 The measured magnitude — and it is negligible

Tick shift as a fraction of the effective stop distance, across all 11,384
candidates:

| leg | mean | median | P95 | P99 | **max** |
|---|---:|---:|---:|---:|---:|
| stop | 0.0089% | 0.0063% | 0.0264% | 0.0377% | **0.0549%** |
| target | 0.0089% | 0.0062% | 0.0267% | 0.0369% | **0.0548%** |

> **THE WORST CASE IS FIVE HUNDREDTHS OF ONE PERCENT OF THE STOP DISTANCE.**
> Against a 2.5R stop-to-target span this is roughly **one part in five
> thousand**.
>
> **THE DIRECTION THEREFORE DOES NOT DESERVE PRE-REGISTRATION.** A7 asked the
> question and the answer is that this is an implementation detail, not a
> design choice with an outcome attached: choosing the opposite direction on
> both legs would move no reported figure at the second decimal place. **Had it
> been material, this paragraph would say the opposite** — the magnitude was
> measured before the conclusion was drawn.

---

## 6. THE VIABILITY PREDICATE

### 6.1 The two conditions

    qty > 0  and  qty >= min_trade_num      flooring did not zero the position
    qty x entry_price >= min_trade_usdt     the $5.00 minimum notional

**Both are read from `config/contracts_cache.json`**, which report 25 §2
cross-checked field-by-field against the live venue with twelve of twelve
agreeing.

**`min_trade_num` COINCIDES WITH `qty_step` ON ALL THREE SYMBOLS** — 0.0001 /
0.01 / 0.1 — so the two quantity conditions are **one condition here**. They are
implemented separately because they are separate constraints at the venue and a
future symbol could separate them. **A test asserts the coincidence**, so if it
ever ends, that is visible rather than silent.

**A REFUSED POSITION IS A SKIP.** It is not sized down and not retried,
degrading into the skip tail exactly as document 05 §3 specifies. Reason codes
are `BELOW_MIN_QTY` and `BELOW_MIN_NOTIONAL`.

### 6.2 BOTH BRANCHES ARE UNREACHABLE AT THE FROZEN VALUES

Under the frozen budget the allocation is always exactly **$20.00** (Amendment 1
Rule B, confirmed on the real population by report 26 §6.1), so the notional is
`$20 / (s + c)` and report 24 §6.5 gives the smallest per-position notional over
the whole window as **$230 / $167 / $40** — **the smallest is eight times the
$5.00 threshold.**

**MEASURED, ON BOTH POPULATIONS:**

| population | positions | `BELOW_MIN_QTY` | `BELOW_MIN_NOTIONAL` |
|---|---:|---:|---:|
| all candidates | 11,384 | **0** | **0** |
| taken under the budget | 6,021 | **0** | **0** |

**REPORTED AS ZERO RATHER THAN OMITTED.** A branch that is never reported is a
branch nobody can tell was checked.

### 6.3 They are implemented and tested anyway

**TREATED EXACTLY AS DOCUMENT 05 §4 TREATED THE INERT PARTIAL BRANCH:**
specified, documented as unreachable at present values, and **carrying tests
that exercise them at values where they ARE reachable.**

| test | how it reaches the branch |
|---|---|
| `test_BELOW_MIN_QTY_is_reached_at_a_tiny_risk_unit` | `risk_usd = 0.01` on BTCUSDT: `qty_unfloored > 0` but floors to **0** |
| `test_BELOW_MIN_NOTIONAL_is_reached_at_a_coarse_step_and_high_price` | a spec with a **$5,000** minimum notional: the quantity condition **passes** and the notional condition fails, so the second reason code is separately reachable |
| `test_the_two_reason_codes_are_distinct_and_a_viable_position_says_so` | both codes and `ok` asserted distinct, and the predicate exercised directly |

**A DEAD BRANCH WITH NO TEST IS `MAKER_NONFILL_COST_R` AGAIN** — closing record
§5.2, a term in the wrong denomination invisible to all 545 tests then in the
suite **because every one of them multiplied it by zero.**

---

## 7. DUAL RISK RECORDING

**EVERY SIZED POSITION CARRIES BOTH FIGURES, AND NEITHER IS DERIVED AT READ
TIME:**

| field | what it is | who uses it |
|---|---|---|
| `nominal_risk_usd` | **$20.00**, the figure the budget charges | the aggregate budget, per Amendment 1 Rule B, which charges the nominal figure **before** flooring |
| `realised_risk_usd` | `qty × d`, the true 1.0R denominator **for that trade** | R multiples: a stop returns exactly −1.0 and a target exactly +1.5 in that trade's own risk unit |

**THE TWO ANSWER DIFFERENT QUESTIONS AND BOTH ARE STORED.** A reader with only
one of them cannot recover the other without knowing the flooring residue, and
the residue is exactly what this report measures. **The budget continues to
charge nominal** — which is what keeps the partial-allocation branch inert
(Amendment 1 §3.2) — **while R multiples are computed against realised**, which
is what keeps the thesis's 40.0% / 53.6% arithmetic describing the system.

---

## 8. THE DRAG — what flooring costs

### 8.1 The three loss fractions are one number

**Flooring scales quantity, notional and realised risk by the same factor**, so
`drag_fraction`, `qty_lost_fraction` and `notional_lost_fraction` are
**identical per position** — asserted to within 1e-12 across all 11,384 rows.
They are reported as one distribution rather than three.

**THE POOLED FORMS DO DIFFER, AND THE REASON IS WEIGHTING**: risk is equally
weighted because every position carries the same $20.00 unit; notional is not.
Both are reported, because report 24 §2.2 measured the **notional-weighted** one
and comparing against the other would be comparing two different quantities.

### 8.2 Realised risk, and the drag

**ALL 11,384 CANDIDATES:**

| quantity | min | P1 | P5 | P25 | median | P75 | P95 | P99 | max | mean |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `realised_risk_usd` | **18.158** | 19.082 | 19.426 | 19.774 | **19.920** | 19.971 | 19.994 | 19.999 | 20.000 | **19.840** |
| drag (%) | 0.0001 | 0.0055 | 0.0285 | 0.1432 | **0.3987** | 1.1307 | 2.8702 | 4.5884 | **9.2117** | **0.8024** |

**THE 6,021 TAKEN UNDER THE BUDGET:** realised risk min **18.293**, median
**19.923**, mean **19.845**; drag median **0.383%**, mean **0.777%**, max
**8.533%**.

**POOLED TOTALS:**

| population | nominal | realised | **drag** | **as % of nominal** |
|---|---:|---:|---:|---:|
| all candidates | $227,680.00 | $225,853.15 | **$1,826.85** | **0.8024%** |
| taken | $120,420.00 | $119,484.24 | **$935.76** | **0.7771%** |

### 8.3 Per symbol, and the cross-check against report 24

| population | symbol | n | drag mean | **notional-weighted loss** | report 24 §2.2 |
|---|---|---:|---:|---:|---:|
| candidates | BTCUSDT | 3,735 | 0.2216% | **0.2069%** | 0.2063% |
| candidates | ETHUSDT | 3,715 | 1.4255% | **1.2662%** | 1.2639% |
| candidates | SOLUSDT | 3,934 | 0.7654% | **0.6674%** | 0.6668% |
| taken | BTCUSDT | 1,973 | 0.2154% | 0.2024% | — |
| taken | ETHUSDT | 1,963 | 1.3773% | 1.2319% | — |
| taken | SOLUSDT | 2,085 | 0.7434% | 0.6454% | — |

> **THE CROSS-CHECK PASSES AND THE RESIDUAL IS EXPLAINED.** Every symbol
> reproduces report 24 §2.2 to within **0.0024 percentage points**, and every
> one is **slightly larger** — which is the correct direction and a test asserts
> it: report 24 applied **no tick rounding**, while this step rounds the stop
> away from entry, widening it, which enlarges the denominator, shrinks the
> quantity and slightly increases the flooring loss.

**ETH's worst single position is 9.21%**, reproducing report 24 §2.2's worst
case exactly. **ETH is the granularity-binding symbol** throughout, consistent
with the closing record §6.1.

### 8.4 Per fold — taken population

| fold | period | n | drag | | fold | period | n | drag |
|---:|---|---:|---:|---|---:|---|---:|---:|
| 1 | train | 1,025 | 0.706% | | 5 | test | 519 | 0.608% |
| 1 | test | 500 | 0.330% | | 6 | train | 1,014 | 0.462% |
| 2 | train | 1,018 | 0.430% | | 6 | test | 501 | 1.116% |
| 2 | test | 485 | 0.374% | | 7 | train | 1,020 | 0.857% |
| 3 | train | 985 | 0.352% | | 7 | test | 503 | 1.188% |
| 3 | test | 491 | 0.403% | | 8 | train | 1,004 | 1.152% |
| 4 | train | 976 | 0.388% | | 8 | test | 517 | 1.081% |
| 4 | test | 495 | 0.310% | | 9 | train | 1,020 | 1.133% |
| 5 | train | 986 | 0.356% | | 9 | test | 516 | 1.283% |

**The drag rises across the window, from 0.31% to 1.28%.** Prices rose over
2022–2024 while the quantity step did not, so the same $20.00 risk unit buys
fewer steps and the flooring residue is a larger share of a smaller quantity.
**That mechanism is arithmetic, not a market effect**, and it means the drag is
a function of price level — which §10 makes into a stated limitation running the
other way.

---

## 9. THE REALISED COST RATIO AGAINST `COST_TOLERANCE_R`

**`c/s` — the cost term as a fraction of the stop term — measured per position,
stratified by whether the 1.50% floor bound.** The thesis freezes
`COST_TOLERANCE_R = 0.11`.

**ALL 11,384 CANDIDATES:**

| stratum | n | min | P25 | median | P75 | P95 | **max** | mean |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| **all** | 11,384 | 0.0028 | 0.0639 | 0.0878 | 0.1122 | 0.1144 | **0.1483** | 0.0856 |
| **floor-bound** | 2,927 | **0.1122** | 0.1122 | 0.1144 | 0.1144 | 0.1144 | **0.1483** | 0.1147 |
| **not floor-bound** | 8,457 | 0.0028 | 0.0577 | 0.0756 | 0.0934 | 0.1123 | 0.1481 | 0.0755 |

> ### 3,507 OF 11,384 POSITIONS — 30.81% — EXCEED THE FROZEN 0.11 TOLERANCE.
>
> **Of those, 2,927 are floor-bound and 580 are not.** The floor-bound stratum's
> **minimum is 0.1122**, so **every single floor-bound position exceeds the
> tolerance** — there is no overlap at all.

**On the 6,021 taken: 1,932 exceed — 32.09%** — of which 1,627 are floor-bound
and 305 are not.

**Per symbol, candidates exceeding 0.11:** BTCUSDT **1,804** (of which 1,716
floor-bound), ETHUSDT **1,163** (1,090), SOLUSDT **540** (121). **SOLUSDT's
excess is mostly NOT floor-bound** — 419 of its 540 — because its 10 bps stop
haircut pushes `c/s` above 0.11 at any stop tighter than about 2%, well above
its 1.50% floor.

**THIS CONFIRMS AND QUANTIFIES THE CLOSING RECORD §10.2 FINDING.** That section
derived, from the config alone, that a floor-bound stop charges 0.112–0.114 on
BTC/ETH and 0.145–0.148 on SOL. **The measured maximum is 0.1483**, matching the
derivation. **What was an inference is now a distribution and a count.**

> **REPORTED, NOT RESOLVED.** Amendment 1 §7 already carries the open item that
> `COST_TOLERANCE_R`'s *justification* is owed and must be settled **before any
> performance figure is inspected**. Nothing here changes the value, and the
> disposition of a tolerance that nearly a third of positions exceed belongs to
> the validation design. **This step's contribution is to make it a measured
> quantity instead of an inference.**

---

## 10. THE HISTORICAL `qty_step` ASSUMPTION — a named limitation

> **EVERY FIGURE IN §8 APPLIES TODAY'S QUANTITY STEPS TO 2022–2024 BARS.**

Report 25 §8 established that **no Bitget endpoint publishes lot-size history**
and that it cannot be recovered: the contracts endpoint reports the current
contract state only, and unlike the price tick — which `contracts.py`
reconstructed empirically by grid-validating historical prices — **the derived
layer holds no order sizes, so the same reconstruction is not available.**

**IF THE 2022 STEPS WERE COARSER, THE TRUE DRAG WAS LARGER, AND NOTHING IN THIS
PROJECT CAN SAY BY HOW MUCH.**

**Stated in the terms thesis §5.3 uses for the funding rate** — *"0.01% per 8h is
the venue's baseline and is used as a stated assumption"* — **so here: today's
quantity steps are the venue's current state and are used as a stated assumption
about the backtest window.** Not smoothed over, and not presented as measured.

**THE DIRECTION OF THE RISK, AND IT RUNS AGAINST §8.4's TREND.** Exchanges
generally refine lot granularity over time rather than coarsen it, so 2022 steps
were more likely coarser than today's — which would make the early-window drag
*larger* than measured, partly offsetting the rising trend §8.4 attributes to
price level. **That is an industry tendency, not a measurement**, and it is
recorded as a reason the trend in §8.4 should not be read as a clean price-level
effect.

**THE PRICE TICK IS NOT SUBJECT TO THIS LIMITATION.** It **is** a schedule in
the cache — SOLUSDT moved from a 0.0001 to a 0.001 grid on 2024-08-14 — and the
measurement resolves it **per bar timestamp**, not per symbol. A test asserts
the same synthetic position sizes differently on either side of that boundary.

---

## 11. VERIFICATION

### 11.1 A GUARD FIRED DURING THE BUILD, AND IT FIRED CORRECTLY

**The first version of `src/engine/sizing.py` mentioned the risk package's
DOTTED module path in a docstring**, in a sentence recording that it is
deliberately not imported. **Report 26's `test_nothing_is_wired_in_yet` is a TEXT
search over every file under `src/`, and it flagged the engine module as an
unpermitted importer — correctly, by its own rule.**

> **THE MODULE WAS CHANGED, NOT THE GUARD.** The docstring now says `src/risk`
> with a slash and never the dotted path, so the engine file contains no such
> token at all — **which is the stronger property**, and the assertion that
> engine files are unwired remains unconditional and untouched.

**Recorded because the alternative was available and tempting**: adding
`src/engine/sizing.py` to that test's allowlist would have passed the suite and
quietly weakened the one assertion that keeps the engine unwired from the risk
package.

### 11.2 The central test and the identities

| check | result |
|---|---|
| **`test_CENTRAL_the_target_price_is_invariant_to_quantity`** | **passes** — identical target at a 10× quantity |
| `costs.solve_target` asserted **not** quantity-invariant | **passes** — the defect is pinned, not fixed in place |
| stop = −1.0 × realised, 3 symbols × 2 directions, floored qty | **passes**, exact to 1e-12 |
| target = +1.5 × realised, same cells | **passes**, exact to one tick, always favourable |
| the identity **fails** against nominal risk | **passes** — the two forms are distinguishable |
| carve-out is exactly one function, called by no module code | **passes**, over the AST |

### 11.3 Flooring, viability, ticks

| check | result |
|---|---|
| `qty` is a whole multiple of `qty_step`, all 11,384 | **passes** |
| `qty <= qty_unfloored` and `realised <= nominal`, all positions | **passes** |
| equality exactly when the quantity is an exact multiple | **passes** |
| a planted **round-to-nearest** breaches the risk unit | **passes** — flooring does not |
| `BELOW_MIN_QTY` reached at `risk_usd = 0.01` | **passes** |
| `BELOW_MIN_NOTIONAL` reached with the quantity condition passing | **passes** |
| every stop and target lands on the price tick, all symbols | **passes** |
| both legs round **away** from entry | **passes**, asserted per leg |
| the effective stop distance is recomputed from the rounded price | **passes** |

### 11.4 Regression, and what may not be reached

| check | result |
|---|---|
| **`costs.position_size` byte-identical** to reports 24/26/27's values | **passes** — pinned to hand arithmetic on the documented denominator |
| the new denominator is that same number, reused not copied | **passes** |
| **no leverage check** anywhere — identifiers, attributes, string literals | **passes** |
| the risk package is unreachable; `risk_usd` is a parameter | **passes** |
| **no numeric literal equals any `qty_step`, minimum or tick** | **passes** |
| no data layer, no `pandas`/`numpy`, no 1m path, no `simulate` | **passes** |
| **twelve-name firewall**, both modules, not relaxed | **passes** |
| no bar after a signal bar; no `hit`/`touch`/`reached`/`crossed` | **passes** |
| the carve-out is not called from the measurement module | **passes** |

### 11.5 Controls

**SYNTHETIC POSITIVE CONTROL.** Two positions whose flooring is computed by
hand and asserted **element by element**:

- **SOLUSDT long**, entry 100.0, ATR 1.0, after the 2024 tick change:
  `d = 2.25 + 0.06 + 0.05865 + 0.09775 = 2.46640`, unfloored `20/2.46640 =
  8.108985…`, **floored 8.1**, realised **19.977840**, drag **0.11080%**.
- **BTCUSDT long**, entry 30,000, ATR 300: `d = 675 + 18 + 17.595 + 14.6625 =
  725.2575`, unfloored `0.02757617…`, **floored 0.0275**, realised
  **19.94458125**, drag **0.27709375%**.

Every one of those figures is asserted, not just the aggregate. **PASSES.**

**SYNTHETIC NEGATIVE CONTROL.** An empty population produces **zero rows** with
the full column set, zero viability failures, a zero drag total and `NaN`
distribution statistics — **not a silent success with an empty aggregate.**
**PASSES.**

### 11.6 PLANTED MUTATION — the holdout seal

**THE MUTATION.** In `src/timeframe/resample.py`, `WINDOW_END` widened to
2025-06-30 and `ALLOWED_YEARS` extended to include 2025.

**RESULT: planted, confirmed failing, reverted.** `git diff --stat` is empty
after the revert.

| scope | outcome under the mutation |
|---|---|
| `tests/test_sizing_drag.py` | **13 tests fail** (1 failure + 12 errors) |
| `tests/test_sizing.py` | **0 fail — all 47 still pass** |
| whole suite | **78 fail** (37 failures + 41 errors) |

> **THE SIZING MODULE IS UNAFFECTED BY THE MUTATION, AND THAT IS THE POINT.** It
> cannot reach the data layer at all, so there is no path on which a seal could
> be breached. The mutation bites only where data is read — the drag
> measurement — which is exactly the separation the module boundary was drawn
> for.

### 11.7 FULL SUITE

| | tests |
|---|---:|
| baseline at `60b66f5` | **898 passing** |
| new in `tests/test_sizing.py` | **+47** |
| new in `tests/test_sizing_drag.py` | **+22** |
| **total** | **967 passing / 967** |

---

## 12. WHAT CONTRADICTS A FROZEN DOCUMENT

**Nothing contradicts a frozen document. Three frozen findings are confirmed and
quantified.**

**12.1 THE CLOSING RECORD §6.1's UNQUANTISED-SIZING DEFECT IS FIXED AND
MEASURED.** *"Every backtest to date has sized in unachievable fractional
quantities."* The cost of that is **0.80% of nominal risk pooled**, ETH-binding,
worst single position 9.21%. **The realised-vs-intended risk provenance counter
§6.1 asked for is the `nominal_risk_usd` / `realised_risk_usd` pair of §7.**

**12.2 REPORT 24 §2.2's FLOORING FIGURES ARE REPRODUCED** to within 0.0024
percentage points on every symbol, with the residual explained and its direction
asserted (§8.3). **Report 24's own figures stand; they were computed without
tick rounding and are correct for what they measured.**

**12.3 THE CLOSING RECORD §10.2's `c/s` FINDING IS CONFIRMED AND TURNED INTO A
DISTRIBUTION.** It derived 0.112–0.114 and 0.145–0.148 from the config; the
measured maximum is **0.1483** and **30.81% of positions exceed the frozen
0.11**. **The value is unchanged and its disposition remains the validation
design's.**

**12.4 AMENDMENT 1 §3's `target_r_multiple` NOTE REMAINS LOAD-BEARING.** Report
27 §3.2 was the first place the 2.0-versus-1.5 divergence mattered; this is the
second. **The module does not read the config field at all**, which is a
stronger guarantee than supplying the right value.

---

## 13. WHAT THIS HANDS FORWARD

1. **Sizing is exchange-real.** Quantities are floored to the lot step, both
   levels land on the price tick, and the target is invariant to quantity.
2. **The R identities hold at a floored quantity**, so the thesis's 40.0% /
   53.6% arithmetic describes the system again.
3. **Flooring costs 0.80% of nominal risk**, ETH-binding, and the viability
   branches are unreachable at the frozen values — implemented, tested, and
   measured as zero.
4. **30.81% of positions charge more than `COST_TOLERANCE_R`.** Open, routed to
   the validation design, and now a number rather than an inference.
5. **Nothing is wired in.** `simulate.py` still constructs independent positions
   with dollar-solved targets; replacing that path is later work, and report 25
   §10.2's netted-execution finding lands on it too.
6. **The 1m seal gap remains 5.3.3's**, and report 27's verdict stands: exits are
   evaluated on 1m.

---

**Files.** `src/engine/sizing.py` · `tests/test_sizing.py` ·
`src/analysis/sizing_drag.py` · `tests/test_sizing_drag.py` · this report.
**Firewall:** armed, twelve names, one recorded conceptual carve-out (§4.1), no
exit evaluated and no bar after a signal bar read.
**Holdout:** sealed, unspent, re-verified by planted mutation.
