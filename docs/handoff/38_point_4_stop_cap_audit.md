# REPORT 38 — THE FROZEN STOP CAP, AUDITED

**Point 4.** A MEASUREMENT. **Nothing is decided, no cap value is recommended and
none is selected.**

**WHY THIS SITS UNDER `docs/handoff/`.** It is a measurement, not a decision.
Design documents join the frozen specification on commit; a measurement does not.

> ### THE HEADLINE: A COMMITTED DERIVATION FOR THIS PARAMETER ALREADY EXISTS,
> ### AND 0.035 IS NOT ITS OUTPUT FOR ANY SYMBOL OR ANY FOLD.

`src/sweep/grid.py`'s `derived_cap` computes the cap as `(m* + 2.5) x P95(ATR%)`
over each training fold, citing Appendix H and Amendment 6. Evaluated over the
nine folds and three symbols it yields **3.5043 per cent to 7.4709 per cent**.
**The frozen 0.035 lies below all twenty-seven of those values.**

---

## 1. PROVENANCE

- **Module:** `src/analysis/stop_cap_audit.py`.
- **Grid commit, alone and first: `0a1ae11`.** The counting functions
  `clipped_at` and `sensitivity_table` are absent from that tree; §7.1 gives the
  proof.
- **Tests:** `tests/test_stop_cap_audit.py` — path chosen after listing `tests/`
  in full and probing three candidates; all three were free and the first taken.
- **NOT MODIFIED:** `src/engine/`, `src/risk/`, `src/sweep/`, `src/folds/`, every
  other module under `src/analysis/`, every document under `docs/design/`.

**THE SEAL.** The barrier is asserted **once per symbol-fold immediately before
each read** inside `derived_cap_table`, and a test asserts the call sits inside
the loop rather than at the function's entry. Runtime tracing over the whole
derived-cap build recorded **zero** opens of any sealed partition. Bar data is
limited to training windows, which lie wholly inside 2022-01-05 to 2024-12-31.
The barrier is probed in the firing direction on both sealed years, with an
unsealed path required to pass.

---

## 2. PART 1 — WHAT THE CAP DOES, FROM THE CODE

### 2.1 WHERE THE VALUE IS DEFINED

**`src/engine/costs.py:63`: `stop_max_pct: float = REQUIRED`.** It is one of the
four parameters Point 3R stripped of defaults. The module docstring gives the
reason for that, and it is worth quoting because it is about this class of
parameter exactly:

> **"Four parameters have NO DEFAULT and raise if not supplied (stop_atr_mult,
> stop_max_pct, rvol_threshold, baseline_days). Each was a placeholder that
> silently acted as a chosen value; a stale default is exactly the failure 3R
> exists to correct."**

**SO THE PARAMETER HAS NO DEFAULT ANYWHERE. EVERY CALLER SUPPLIES IT**, and what
each supplies is §2.3's subject.

### 2.2 EVERY READ SITE

**58 sites name `stop_max_pct`**, over AST nodes and never raw text: **14
attribute reads**, 22 keyword arguments, 1 name binding, 21 string literals. The
string literals are dictionary keys and sweep-dimension names; the keyword
arguments are construction sites.

**THE FOURTEEN ATTRIBUTE READS ARE THE LIVE CONSUMPTIONS**, and only two are in
the engine:

- **`src/engine/costs.py:247`** — `hi = cfg.stop_max_pct * entry` inside
  `stop_geometry`. **This is the clamp.** The raw ATR distance is compared to a
  derived per-symbol floor and to this cap, and the mechanism that bound is
  returned as one of `atr`, `floor`, `cap`.
- **`src/engine/simulate.py:186`** — a trace line only. It formats the cap into a
  diagnostic string and changes nothing.

The remaining twelve are in `src/analysis/` and in tests: three in
`risk_unit_floor_curve.py`, two in `haircut_share_rerun.py`, one in
`level_consequences.py`, and six in test modules.

**NOTHING ELSE BOUNDS THE SAME QUANTITY FROM ABOVE.** From below,
`cfg.stop_min_pct(symbol)` is a DERIVED per-symbol cost floor, read at the same
line of `stop_geometry`, at 1.020 per cent for BTCUSDT and ETHUSDT and 1.320 per
cent for SOLUSDT. **The floor is derived and the cap is supplied**, which is the
asymmetry this report exists to examine.

### 2.3 IS A REASON RECORDED ANYWHERE? YES — AND NOT WHERE THE VALUE COMES FROM

**`stop_geometry`'s DOCSTRING STATES NO REASON.** It explains only that the
mechanism is decided on the raw distance before rounding, so a tick-level artefact
cannot relabel an ATR stop as a floor stop. **Nothing there says what the cap is
for or why it takes any particular value.**

> ### BUT A REASON, A RULE AND A DESIGN INTENT ARE ALL RECORDED — IN
> ### `src/sweep/grid.py`.

`derived_cap`'s docstring, quoted in full:

> **"stop_max_pct = (m* + 2.5) x P95(ATR%) over training-fold breakout bars.
> Appendix H. At the top grid point the cap binds when (m*+2.5) x ATR% > (m*+2.5)
> x P95, i.e. when ATR% > P95 -- 5% of bars by construction, and strictly less at
> every lower multiplier. The superseded median form binds on 50% at the same
> point, which is a second stop rule rather than a guard rail."**

**THAT IS THE PURPOSE, STATED IN THE PROJECT'S OWN WORDS: A GUARD RAIL BINDING
ABOUT FIVE PER CENT OF BARS, AND EXPLICITLY NOT A SECOND STOP RULE.** The rule is
per symbol and per fold and is computed from the training population.

### 2.4 WHERE 0.035 ACTUALLY COMES FROM

**IT IS NOT `derived_cap`'s OUTPUT.** It appears as a literal in nine places, and
every one of them is scaffolding:

- **`src/analysis/exposure_profile.py:150`**, in a dict named
  **`_UNUSED_SIZING_PARAMS`**, whose docstring says of its three members: *"They
  are supplied purely to construct the object and are NEVER read; a test varies
  all three and asserts every quantity produced here is unchanged, so this cannot
  become a channel through which a strategy parameter reaches the exposure
  figures."*
- **`src/regime/measure.py:132`**, in `_UNUSED_SWEEP_PARAMS`, with the same
  disclaimer.
- **`tests/conftest.py:19`**, in `FIXTURE_PARAMS`, commented *"Explicitly-arbitrary
  values ... They are fixture scaffolding, not chosen values."*
- Placeholder dicts in `src/sweep/grid.py:73`, `src/folds/warmup.py:69`,
  `src/analysis/structural_pass.py:536`; two README command lines; and test
  configs.

> ### THE 4.1 CHAIN SUPPLIES ITS CAP FROM `_UNUSED_SIZING_PARAMS`, A DICT WHOSE
> ### DOCSTRING SAYS THE VALUE IS NEVER READ.

**THAT CLAIM WAS TRUE WHEN WRITTEN AND IS NO LONGER TRUE.** The guard behind it,
`test_the_three_construction_only_parameters_are_never_read`, varies the three
parameters and asserts `ep.positions`'s output is unchanged. **Its scope is
`ep.positions` alone.** Modules added later — `risk_unit_floor_curve`,
`haircut_share_rerun`, `level_consequences` — take their config from the same
`ep.cost_config()` and **do** read `stop_max_pct`.

**IT IS LOAD-BEARING TODAY.** Moving the value from 0.035 to 0.050 moves the
admitted domain's lower bound from 0.03554692 to 0.02567516 — a bound report 36
derived and `docs/design/04_1c_pre_commitments.md` §2.1 committed. **The guard is
correct and narrow; the docstring's blanket wording has been read as general.**

---

## 3. PART 2 — THE GRANULARITY CONSTRAINT

### 3.1 THE RELATION

Quantity is the risk unit divided into the allocation, and the risk unit grows
with the stop width, so **quantity falls as the stop widens** — asserted by test
across five widths at every symbol and direction. Flooring to the venue's lot
step then consumes a share of nominal risk that grows as quantity shrinks.

**THE MINIMUM LOT BINDS WHERE THE SOLVED QUANTITY REACHES ONE LOT STEP.** Because
the risk unit is affine in the width, that is solved rather than searched:

    w* = ( risk_usd / (min_trade_num x entry) - A - 2f ) / ( 1 + sigma (f + h) )

A test confirms the solve against what it claims: at `w*` the unfloored quantity
equals one minimum lot exactly, above it falls below, below it exceeds.

**THE OBSERVED PRICE RANGES** over the 11,384 candidates, which the next section
needs: BTCUSDT 15,639.00 to 107,284.00; ETHUSDT 990.20 to 4,066.84; SOLUSDT 9.14
to 259.90.

### 3.2 THE MINIMUM-LOT BINDING WIDTH, AT THREE ENTRY PRICES

Long leg, as a percentage of entry. Lot steps are 0.0001, 0.01 and 0.1.

- **At 120.5:** BTCUSDT 166,157.68; ETHUSDT 1,661.38; SOLUSDT 165.99.
- **At 3,000:** BTCUSDT 6,673.81; ETHUSDT 66.54; SOLUSDT 6.43.
- **At 95,000:** BTCUSDT 210.56; ETHUSDT 1.91; SOLUSDT **negative**.

**THE WIDTH DEPENDS STRONGLY ON PRICE, AND THAT ANSWERS THE QUESTION THE THREE
PRICES WERE FOR.** Quantity scales as the reciprocal of price, so a fixed lot step
binds at a narrower width the higher the price.

**THE NEGATIVE ENTRY IS AN ARTEFACT OF THE CROSS-PRODUCT AND IS NOT A FINDING.**
One SOLUSDT lot of 0.1 at 95,000 is 9,500 of notional, which no positive stop
width fits inside a 20.00 risk unit; the solve returns the correct answer to an
impossible question. **SOLUSDT never trades near that price.** A test pins both
the negative result and its meaning.

### 3.3 AT EACH SYMBOL'S OWN PRICES

Long leg, at each symbol's median observed entry price:

- **BTCUSDT at 37,159.90: 538.61 per cent** — 153.9 times the frozen cap.
- **ETHUSDT at 2,192.02: 91.14 per cent** — 26.0 times.
- **SOLUSDT at 60.78: 329.33 per cent** — 94.1 times.

At each symbol's **maximum** observed price, the tightest case available:
BTCUSDT 186.43 per cent, ETHUSDT 49.03 per cent, SOLUSDT 76.82 per cent — **14.0
to 53.3 times the frozen cap.**

### 3.4 DRAG AGAINST THE STATED REFERENCE LEVELS

**THIS REPORT INVENTS NO ACCEPTABILITY LEVEL.** The references are the ones
`docs/handoff/28_point_5_3_1_sizing.md` §8.2 already measured: **0.80 per cent of
nominal risk pooled**, and **9.21 per cent on the worst single position**. A test
asserts the module declares no constant naming an acceptable drag.

**THE CURVE IS A SAWTOOTH, NOT A MONOTONE FUNCTION.** Flooring drops the quantity
to the lot below, so drag falls discontinuously at each lot boundary and climbs
between them. What follows is therefore a **first crossing** and not a level the
curve stays above; a test asserts the non-monotonicity so the distinction is not
decorative.

First crossing of each reference, long leg at each symbol's median price:

- **BTCUSDT:** 0.80 per cent first reached at a width of **4.700 per cent**; 9.21
  per cent not reached below 30 per cent.
- **ETHUSDT:** 0.80 per cent at **0.850 per cent**; 9.21 per cent at **8.950 per
  cent**.
- **SOLUSDT:** 0.80 per cent at **2.950 per cent**; 9.21 per cent not reached
  below 30 per cent.

### 3.5 WHERE 0.035 SITS ON THAT CURVE

Drag at the frozen cap, long leg, at each symbol's median price: BTCUSDT and
ETHUSDT below a tenth of one per cent; SOLUSDT a few tenths. **The frozen cap sits
in the flat part of the curve for every symbol**, far below the width at which the
minimum lot binds and, for two symbols of three, below the width at which drag
first reaches the pooled reference.

> ### THE GRANULARITY CONSTRAINT DOES NOT EXPLAIN 0.035. IT BINDS BETWEEN 14 AND
> ### 154 TIMES FURTHER OUT.

---

## 4. PART 3 — THE REACHABILITY CONSTRAINT, TESTED

### 4.1 THE PROBLEM WITH THE PURPOSE AS STATED

The second purpose credited to the cap is keeping the stop inside a reachable,
liquid band so an extreme move does not blow through it.

**EVERY CLIPPED CANDIDATE ALREADY HAS AN ATR-IMPLIED STOP ABOVE THE CAP.**
Clipping does not reduce the market's volatility. It means the stop sits closer to
entry than the bar's own volatility asked for, so it is **reached sooner**.

> ### THE CAP IS NOT CONTROLLING WHETHER A VIOLENT MOVE OCCURS. IT IS CONTROLLING
> ### HOW MUCH IS EXPOSED WHEN ONE DOES.

**SO THE PURPOSE IS TESTABLE**, and the test is what direction the exposure moves.

### 4.2 THE TEST, AND IT RUNS AGAINST THE PURPOSE

Risk is held fixed at one unit, and the stop distance is what divides it. Quantity
is the risk unit divided into the allocation, so **notional is approximately the
risk unit divided by the width**: a narrower stop buys a LARGER position.

Measured on the 1,967 candidates the frozen cap clips, comparing notional at the
cap against notional at the width their own ATR asked for:

- **BTCUSDT, 117 clipped: median 1.1728 times, maximum 2.3598 times.**
- **ETHUSDT, 350 clipped: median 1.1718 times, maximum 3.2489 times.**
- **SOLUSDT, 1,500 clipped: median 1.2472 times, maximum 13.3210 times.**
- **POOLED: median 1.2304 times. The ratio exceeds one on 100.00 per cent of
  clipped candidates.**

> ### CLIPPING INCREASES NOTIONAL EXPOSURE ON EVERY CANDIDATE IT FIRES ON. IT
> ### DOES NOT REDUCE EXPOSURE TO AN EXTREME MOVE; IT INCREASES IT.

That is not a measurement artefact and could not have come out otherwise: with
risk fixed, narrowing the stop necessarily raises the quantity, and a gap of any
given size is then multiplied by more units.

### 4.3 WHAT THE HAIRCUT ALREADY PRICES, AND WHAT REMAINS

`docs/design/06_exit_resolution_spec.md` and `src/risk/exit_spec.py` charge a
**stop-market haircut** — 5 bps on BTCUSDT and ETHUSDT, 10 bps on SOLUSDT —
applied to the stop price on the stop leg, so the model already assumes the stop
fills **through** its level and charges for it. `docs/handoff/31_point_5_closing.md`
§5.2 records that this haircut **is the entire slippage-and-gap model**, is a
placeholder rather than a venue-published figure, and cannot be validated against
this data layer because no bar's first observed price exists at any resolution.

**THE HAIRCUT IS A FIXED RATE. IT DOES NOT VARY WITH THE STOP'S WIDTH AND DOES NOT
VARY WITH VOLATILITY.** So it prices an adverse fill of constant proportion,
whatever the geometry.

> ### THE HAIRCUT DOES NOT PRICE WHAT THE CAP IS CREDITED WITH LIMITING, AND
> ### NOTHING REMAINS THAT THE CAP ADDRESSES IN THE PROTECTIVE DIRECTION.

The two do different things: the haircut prices a typical adverse fill and is
width-independent; the cap changes the width, and §4.2 establishes that the change
it makes moves exposure the **wrong** way. **There is no residual exposure that the
cap reduces and the haircut misses.** What is genuinely unpriced — a tail gap far
beyond the stop — is unpriced by both, and made worse rather than better by the
cap.

### 4.4 THE UNCOMPUTABLE SIDE, NAMED

> ### WHETHER A STOP CLIPPED NARROWER THAN VOLATILITY IMPLIES IS MORE OFTEN HIT
> ### IS AN OUTCOME QUANTITY, AND THE FIREWALL FORBIDS COMPUTING IT.

It is the other half of this question and this report does not touch it. A stop
reached sooner may cost the strategy its thesis or may cost it nothing; **nothing
in §4 bears on that**, and §4.2's finding is about exposure per event, not about
event frequency.

---

## 5. PART 4 — WHERE THE CONSTRAINTS BIND, AGAINST 0.035

### 5.1 THE COMMITTED DERIVATION, EVALUATED

`grid.derived_cap` over nine folds and three symbols, as a percentage of entry:

- **BTCUSDT: 3.5826 to 5.5140, median 4.1128.**
- **ETHUSDT: 3.5043 to 5.5077, median 4.4556.**
- **SOLUSDT: 5.2624 to 7.4709, median 6.6416.**

> ### ACROSS ALL TWENTY-SEVEN SYMBOL-FOLD CELLS THE MINIMUM IS 3.5043 PER CENT.
> ### THE FROZEN VALUE IS 3.5000. **ZERO OF TWENTY-SEVEN FALL BELOW IT.**

### 5.2 WHETHER THE DERIVATION'S STATED INTENT IS MET

`derived_cap`'s docstring states the intent: the cap should bind on **about five
per cent** of the population, and a cap binding on half is *"a second stop rule
rather than a guard rail."*

Clip rate at each symbol's **median derived cap**, against the clip rate at the
frozen 0.035, over the 11,384 candidates:

- **BTCUSDT: 1.66 per cent at 4.1128, against 3.13 per cent at 3.5000.**
- **ETHUSDT: 3.36 per cent at 4.4556, against 9.42 per cent at 3.5000.**
- **SOLUSDT: 4.27 per cent at 6.6416, against 38.13 per cent at 3.5000.**

> ### THE DERIVED CAP MEETS ITS STATED INTENT ON ALL THREE SYMBOLS. THE FROZEN
> ### CONSTANT MISSES IT BY UP TO 7.6 TIMES.

### 5.3 THE DISTANCE FROM 0.035 TO EACH COMPUTABLE CONSTRAINT

- **THE COMMITTED DERIVED CAP:** nearest cell 3.5043 per cent, **0.0043
  percentage points above 0.035** — and that is ETHUSDT's single tightest fold.
  The median cells sit 0.61, 0.96 and 3.14 percentage points above it, and the
  furthest cell 3.97 above. **0.035 is at the extreme low edge of the derived
  range and below every member of it.**
- **THE MINIMUM-LOT CONSTRAINT:** nearest case 49.03 per cent, **14.0 times
  0.035**, and up to 154 times at median prices. **Far.**
- **THE GRANULARITY REFERENCE LEVELS:** the pooled 0.80 per cent reference is
  first crossed at 0.850 per cent on ETHUSDT — below 0.035 — and at 2.950 and
  4.700 per cent on SOLUSDT and BTCUSDT. **0.035 lies among them with no
  particular relation to any.**

### 5.4 THE FINDING

> ### 0.035 IS NOT EXPLAINED BY EITHER PURPOSE GIVEN FOR IT.

**THE GRANULARITY PURPOSE BINDS ONE TO TWO ORDERS OF MAGNITUDE AWAY.** Nothing
about lot granularity picks out 3.5 per cent.

**THE REACHABILITY PURPOSE RUNS BACKWARDS.** §4.2 measures the cap increasing
notional exposure on 100 per cent of the candidates it fires on.

**AND THE ONE COMMITTED RULE THAT DOES ADDRESS THIS PARAMETER PUTS IT SOMEWHERE
ELSE** — above 0.035 in every one of twenty-seven cells, and roughly twice 0.035
on SOLUSDT.

**NO RATIONALE IS CONSTRUCTED HERE TO CLOSE THAT GAP.** The report was asked to
state the finding whatever it is, and this is it.

---

## 6. PART 5 — SENSITIVITY

Clipped candidates across the committed range, per symbol and pooled, over the
11,384 candidates. **This is a count of bar geometry**: `clipped_at` reads no
config at all, which a test asserts over its signature and its body.

- **3.00 per cent:** BTCUSDT 235 (6.29), ETHUSDT 636 (17.12), SOLUSDT 2,119
  (53.86), pooled 2,990 (26.26).
- **3.50 per cent:** 117 (3.13), 350 (9.42), 1,500 (38.13), pooled 1,967 (17.28).
- **4.00 per cent:** 68 (1.82), 203 (5.46), 1,016 (25.83), pooled 1,287 (11.31).
- **4.50 per cent:** 48 (1.29), 119 (3.20), 717 (18.23), pooled 884 (7.77).
- **5.00 per cent:** 40 (1.07), 79 (2.13), 497 (12.63), pooled 616 (5.41).
- **5.50 per cent:** 30 (0.80), 56 (1.51), 361 (9.18), pooled 447 (3.93).
- **6.00 per cent:** 15 (0.40), 44 (1.18), 263 (6.69), pooled 322 (2.83).
- **6.50 per cent:** 12 (0.32), 40 (1.08), 186 (4.73), pooled 238 (2.09).
- **7.00 per cent:** 10 (0.27), 35 (0.94), 127 (3.23), pooled 172 (1.51).
- **7.50 per cent:** 7 (0.19), 27 (0.73), 106 (2.69), pooled 140 (1.23).
- **8.00 per cent:** 3 (0.08), 21 (0.57), 81 (2.06), pooled 105 (0.92).

**The count falls monotonically as the cap widens**, asserted by test. **The 3.50
row reproduces report 37 §6.2 exactly**, which is the check that this module and
that one are counting the same thing.

**NO VALUE IN THIS RANGE IS RECOMMENDED OR PREFERRED.** The range was committed at
`0a1ae11` before the counting functions existed.

---

## 7. WHAT THIS REPORT DOES NOT DO

**IT RECOMMENDS NO CAP VALUE AND SELECTS NONE.** A test asserts the module
declares no constant naming a chosen or recommended cap.

**IT COMPUTES NO OUTCOME QUANTITY**, resolves no exit, and does not invoke the
execution loop; asserted over the module's AST, together with the twelve-name
firewall.

**IT DOES NOT DECIDE WHAT THE CAP SHOULD BE.** `docs/design/04_1e_stop_cap.md`
records the disposition.

### 7.1 THE PROOF OF COMMIT ORDER

At `0a1ae11`, `git ls-tree` lists `src/analysis/stop_cap_audit.py`, and parsing
that blob's AST gives nine functions — the read-site scan, the granularity
relation, the minimum-lot solve, the drag crossings and the derived-cap
evaluation — and **neither `clipped_at` nor `sensitivity_table`**. `CAP_GRID` is
already present. The counting functions first appear in this report's commit.

---

## 8. ARTIFACTS

- **Report:** `docs/handoff/38_point_4_stop_cap_audit.md`
- **Module:** `src/analysis/stop_cap_audit.py`
- **Tests, 16 added:** `tests/test_stop_cap_audit.py`
- **Range commit:** `0a1ae11`

**Full suite: 1296 passed** — 1280 before this step, plus the 16 above.
