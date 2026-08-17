# REPORT 40 — THE FOLD SCHEDULE, AUDITED

**Point 4, sub-point 4.2's input.** A MEASUREMENT. **Nothing is decided.**

**WHY THIS SITS UNDER `docs/handoff/`.** It is a measurement, not a decision.

> ### THE HEADLINE, IN ONE SENTENCE: THE FROZEN THESIS FITS NOTHING ON TRAIN, AND
> ### THE PRE-REGISTERED PROCEDURE THAT SELECTS WHICH VARIANT OF IT TO RUN FITS
> ### ITS PRINCIPAL PARAMETER ON TRAIN AND EVALUATES IT ON TEST.

Those are two different objects and the audit's whole result is keeping them
apart. §5 gives the trace for each candidate quantity.

---

## 1. PROVENANCE

- **Tests:** `tests/test_fold_audit.py` — path chosen after listing `tests/` in
  full and probing two candidates; both free, the first taken. 11 added.
- **NO CODE WAS CHANGED.**
- **NO BAR WAS READ FOR THE GEOMETRY.** `build_schedule` is a pure function of
  calendar constants, asserted by test to call no reader. The candidate counts
  reuse the population already built at report 37, over the in-sample window
  only.
- **REACHABILITY IS ESTABLISHED OVER AST NODES**, never raw text.

---

## 2. PART 1 — THE SCHEDULE AS IMPLEMENTED

### 2.1 THE CONSTRUCTION

`src/folds/schedule.py` generates folds from a calendar rule: **train 6 months,
test 3 months, step 3 months**, starting at **2022-04-01** and stopping when a
fold's test window would pass **2024-12-31**. A **45-day warmup** precedes each
train start, for indicator continuity only.

**IT RAISES RATHER THAN ADJUSTING** if the rule does not produce exactly nine
folds ending exactly on the in-sample end, or if fold 1's warmup would precede
the first available bar. Its own words: *"A schedule quietly reshaped to make a
count come out right is not the pre-registered schedule."*

**THE EIGHTEEN PERIODS ARE THE NINE FOLDS' TRAIN AND TEST WINDOWS.** There is no
eighteen-element structure in the code; the count is nine folds times two named
periods, and `fold_periods` additionally names the warmup span.

### 2.2 THE NINE FOLDS

- **Fold 1:** train 2022-04-01 to 2022-09-30, test 2022-10-01 to 2022-12-31.
- **Fold 2:** train 2022-07-01 to 2022-12-31, test 2023-01-01 to 2023-03-31.
- **Fold 3:** train 2022-10-01 to 2023-03-31, test 2023-04-01 to 2023-06-30.
- **Fold 4:** train 2023-01-01 to 2023-06-30, test 2023-07-01 to 2023-09-30.
- **Fold 5:** train 2023-04-01 to 2023-09-30, test 2023-10-01 to 2023-12-31.
- **Fold 6:** train 2023-07-01 to 2023-12-31, test 2024-01-01 to 2024-03-31.
- **Fold 7:** train 2023-10-01 to 2024-03-31, test 2024-04-01 to 2024-06-30.
- **Fold 8:** train 2024-01-01 to 2024-06-30, test 2024-07-01 to 2024-09-30.
- **Fold 9:** train 2024-04-01 to 2024-09-30, test 2024-10-01 to 2024-12-31.

Start dates are inclusive at 00:00:00Z and end dates inclusive at 23:45:00Z, the
last 15m bar of the day.

### 2.3 THE DOCSTRING DOES STATE A PURPOSE

**IT DOES, AND IT IS THE SENTENCE
`docs/design/04_1c_consequences_and_thresholds.md` §3.3 RELIED ON:**

> **"Adjacent training windows overlap by 50%: the nine folds are a STABILITY
> PROBE, NOT NINE INDEPENDENT TRIALS, and if they are ever counted as trials the
> arithmetic is wrong."**

**AND A SECOND SENTENCE THAT BEARS ON PART 3 AND HAS NOT BEEN CITED BEFORE:**

> **"Rolling rather than anchored so that constant training length makes
> fold-to-fold PARAMETER VARIATION attributable to the market rather than to
> estimation noise shrinking as the window grows."**

> ### THAT SENTENCE PRESUPPOSES THAT PARAMETERS VARY FROM FOLD TO FOLD — WHICH IS
> ### TO SAY, THAT SOMETHING IS ESTIMATED PER FOLD.

The schedule's own design rationale therefore assumes the second of the two
readings this audit was asked to decide between. **It is a docstring and not a
committed premise**, which is exactly why §5 traces the code rather than resting
on it.

### 2.4 THE SPAN AND THE HOLDOUT

**Total span: 2022-04-01 to 2024-12-31**, with indicators computed from
2022-02-15.

**The derived layer begins 2022-01-05**, so **the schedule starts nearly three
months after the data does.** Nothing in the rule reaches back to 2022-01-05, and
§4.4 counts what falls in the gap.

**The holdout is DEFINED and carries no train window** — `train_start` and
`train_end` are both `None`. Its docstring: *"the holdout is evaluated once,
whole-window, against a candidate selected entirely elsewhere by the 4.3/4.4
procedure."* **That sentence names a selection procedure and is the second place
the code assumes something is chosen on the in-sample data.**

---

## 3. PART 2 — WINDOW GEOMETRY

### 3.1 TEST WINDOWS ARE DISJOINT AND CONTIGUOUS

> ### NO TWO TEST WINDOWS OVERLAP BY ONE DAY.

Their union runs **2022-10-01 to 2024-12-31 with no gaps** — each test window
begins the day after the previous one ends.

### 3.2 TRAIN WINDOWS OVERLAP ADJACENT FOLDS BY HALF

**VERIFIED AGAINST THE SCHEDULE RATHER THAN REPEATED FROM
`docs/handoff/31_point_5_closing.md`.** Adjacent pairs overlap by 90 to 92 days
of a 181 to 184 day window: **49.5 to 50.3 per cent**, the variation being month
lengths.

**NON-ADJACENT TRAINING WINDOWS DO NOT OVERLAP AT ALL.** There are exactly
**eight** overlapping train pairs, one per adjacent pair, and no others. **The
50 per cent figure is correct and is narrower than it sounds**: it describes
neighbours, not the set.

### 3.3 EVERY TEST WINDOW IS LATER USED AS TRAINING DATA

> ### FIFTEEN CROSS-OVERLAPS. EACH FOLD'S TEST WINDOW FALLS ENTIRELY INSIDE THE
> ### NEXT TWO FOLDS' TRAINING WINDOWS.

Fold 1's test window is training data for folds 2 and 3; fold 2's for folds 3 and
4; and so on to fold 7's, which is training data for folds 8 and 9. Folds 8 and 9
have one and zero later consumers respectively, which is why the count is fifteen
rather than eighteen.

**EVERY ONE RUNS FORWARD.** No fold trains on a later fold's test window, so
there is **no lookahead**. Asserted by test in that direction specifically.

> ### THIS IS THE FACT THAT BEARS MOST DIRECTLY ON WHETHER THE NINE TEST WINDOWS
> ### ARE INDEPENDENT EVALUATIONS. THEY ARE DISJOINT IN TIME AND THEY ARE NOT
> ### INDEPENDENT OF THE SELECTION PROCESS, BECAUSE SEVEN OF THE NINE ARE INPUTS
> ### TO A LATER FOLD'S SELECTION.

### 3.4 THE CANDIDATE COUNTS

Over the 11,384 candidates, by period:

- **Train:** fold 1, 1,929; fold 2, 1,851; fold 3, 1,769; fold 4, 1,728; fold 5,
  1,749; fold 6, 1,881; fold 7, 1,957; fold 8, 1,963; fold 9, 2,056.
- **Test:** fold 1, 884; fold 2, 885; fold 3, 843; fold 4, 906; fold 5, 975;
  fold 6, 982; fold 7, 981; fold 8, 1,075; fold 9, 1,036.

**IN NO PERIOD AT ALL: 888.** Report 37 §5.3's figure is **verified**. They
precede 2022-04-01, the schedule's first training start.

**IN NO TEST WINDOW: 2,817.** This is the number that matters for evaluation and
**it is not the 888.** It decomposes as **888 in no period at all** plus **1,929
in fold 1's training window only**, that window preceding every test window. The
2,817 span 2022-01-05 to 2022-09-30 and are 896 BTCUSDT, 926 ETHUSDT and 995
SOLUSDT.

> ### THE TWO FIGURES ANSWER DIFFERENT QUESTIONS AND ARE EASILY CONFLATED. 888 IS
> ### "OUTSIDE THE SCHEDULE ENTIRELY"; 2,817 IS "NEVER EVALUATED ON TEST".

> ### NO CANDIDATE FALLS IN MORE THAN ONE TEST WINDOW. 8,567 FALL IN EXACTLY ONE.

A candidate falls in **at most three** periods — one test and two trains, or three
trains. The distribution is 888 in none, 1,998 in one, 2,042 in two and 6,456 in
three.

---

## 4. PART 3 — WHAT IS ESTIMATED ON TRAIN

### 4.1 THE REACHABILITY TEST

**THE EVALUATION PATH IS `portfolio.size_position` AND WHAT THE ENGINE CALLS WHEN
RUNNING THE THESIS AS SPECIFIED.**

> ### NO MODULE UNDER `src/engine/` IMPORTS `src.folds` OR `src.sweep`.

Verified over AST import nodes across all eight engine modules and pinned by
test. `portfolio.py` imports `contracts`, `costs`, `sizing`, `src.risk` and
`src.timeframe`; `simulate.py` imports `costs`, `glob` and `pyarrow.parquet`.

**THE DEPENDENCY EXISTS AND RUNS ONE WAY: `src/sweep/sweep.py` IMPORTS
`simulate` AND `costs`.** A test asserts that too, so the absence above is not the
absence of any relationship at all.

> ### THEREFORE NO TRAIN-ESTIMATED QUANTITY CAN REACH A POSITION BY IMPORT. THE
> ### ONLY CHANNEL IS A CONFIG OBJECT CONSTRUCTED BY THE SWEEP AND HANDED TO THE
> ### ENGINE.

### 4.2 THE QUANTITIES, TRACED

**`grid.m_star`.** Computed from the **median** of breakout ATR per cent over the
training fold. Consumed by `grid.multiplier_grid`, which produces eleven
multipliers from `m*` to `m* + 2.5`. Chain: `fold_symbol_grid` -> `build_grid` ->
`grid.json` -> `sweep.cfg_for` -> `CostConfig.stop_atr_mult` ->
`simulate.run_backtest`. **LIVE for the sweep. DEAD for `portfolio.size_position`**
— that function receives `atr` and a `cfg`, and the thesis's own multiplier is
`sizing.STOP_ATR_MULT = 2.25`, a stated constant.

**`grid.derived_cap`.** Computed from the **95th percentile** of the same
population. Same chain to `CostConfig.stop_max_pct`. **LIVE for the sweep, whose
simulations go through `simulate.run_backtest` and therefore through
`costs.stop_geometry`, which applies the cap. DEAD for the governing path**, per
`docs/design/04_1g_cap_adoption.md` §4.1, which established that
`portfolio.size_position` calls `sizing.stop_distance` and applies no cap.

**`grid.rvol_threshold_for_pass_rate`.** Computed per fold and per target pass
rate. Chain to `CostConfig.rvol_threshold` and to the sweep's arm cuts.
**LIVE for the sweep. DEAD for the analysis chain** — §6.3's read-site sweep finds
no attribute read of `rvol_threshold` anywhere under `src/analysis/`.

**`src/sweep/prescreen.py`.** The A3 floor-binding check, per fold and symbol,
against a pre-committed 20 per cent limit. Consumed by the sweep's own
eligibility. **DEAD for the evaluation path.**

**`src/sweep/bands.py`.** §4.3 below.

**`src/regime/measure.py`.** Computes ATR per cent, an efficiency ratio, drift and
median daily quote volume over **rolling windows**, not per fold. It builds a
regime axis. **No chain reaches the engine**; `_UNUSED_SWEEP_PARAMS` in that module
exists only to construct a config object. **DEAD.**

**`src/folds/warmup.py`.** Establishes that a 45-day buffer suffices for indicator
convergence. It produces a sufficiency verdict, not a parameter. **DEAD.**

**`src/analysis/dispersion.py`.** Reads `grid.json` and re-runs periods to measure
dispersion. A measurement module. **DEAD for the evaluation path.**

**ATR, the Donchian channel and RVOL themselves** are computed on **rolling**
lookbacks that cross period boundaries; they are not per-fold estimates and no
fold enters them.

### 4.3 THE ONE THAT IS LIVE, AND IT IS LIVE BY DESIGN

`src/sweep/bands.py` states it in its own docstring, quoting Appendix K.2:

> **"ACCEPTANCE IS A TRAINING-FOLD QUANTITY. Appendix K.2 defines acceptance on
> TRAINING folds: 'Selection is on TRAIN, evaluation is on TEST. That is what
> makes the procedure walk-forward.'"**

The module finds contiguous passing bands per fold per symbol and **selects the
centre of the widest band**, per §4.3 and Appendix K.3. `SELECT_PERIOD = "train"`,
and the literal `"train"` is **hard-coded separately** inside `_acceptance_metrics`
so that flipping the selector raises rather than silently reading the wrong
population — a structure this report asserts by test rather than merely notes.

> ### THE ATR MULTIPLIER IS SELECTED ON TRAIN, PER FOLD, AND THE SELECTION IS
> ### EVALUATED ON TEST. THAT IS A LIVE TRAIN-TO-TEST DEPENDENCY AND IT IS THE
> ### PRE-REGISTERED PROCEDURE RATHER THAN A LEAK.

**THE CHAIN, END TO END:** training-fold breakout ATR per cent -> `m_star` and
`derived_cap` -> the eleven-point multiplier grid and the per-fold cap ->
`sweep.cfg_for` -> `simulate.run_backtest` on train and test -> `sweep.json` ->
`bands.acceptance_table`, filtered to `period == "train"` -> `identify_bands` ->
`select_plateau` -> the per-fold selected multiplier -> **the candidate the holdout
would be run against.**

### 4.4 THE ANSWER, STATED WITHOUT SOFTENING

> ### RUNNING THE THESIS AS FROZEN, NOTHING IS ESTIMATED ON TRAIN. EVERY
> ### PARAMETER IS A STATED CONSTANT AND NO CHAIN REACHES
> ### `portfolio.size_position` FROM ANY TRAINING WINDOW.

> ### RUNNING THE PRE-REGISTERED 4.3/4.4 PROCEDURE, THE ATR MULTIPLIER IS FITTED
> ### ON TRAIN AND CONSUMED ON TEST, AND THE TRAIN/TEST SPLIT IS LOAD-BEARING FOR
> ### EXACTLY THAT.

**THE TWO ARE NOT THE SAME SYSTEM.** The thesis freezes `2.25 x ATR`; the
procedure searches `m*` to `m* + 2.5`, where `m*` ranged from 1.6143 to 4.8354
across the folds this report evaluated. **Whether 2.25 is even inside the searched
grid varies by fold and symbol**, and this report does not check it because that is
a question about which system is being validated, which is 4.2's.

### 4.5 THREE FACTS THIS AUDIT SURFACED AND DOES NOT RESOLVE

**FIRST: THE SWEEP SELECTED UNDER A CAPPED STOP RULE THAT NO LONGER GOVERNS.**
Its simulations run through `simulate.run_backtest`, which applies
`costs.stop_geometry` and therefore the cap. `docs/design/04_1g_cap_adoption.md`
adopted **no cap**, and `portfolio.size_position` never applied one. **Any existing
per-fold selection was made on a stop rule the specification has since retired.**

**SECOND: THE SWEEP HAS RUN, AND ITS ARTIFACTS ARE COMMITTED.**
`data/derived/sweep/grid.json`, `sweep.json` and `bands.json` are **tracked in
git**.

> **THIS REPORT DID NOT OPEN THEM.** `docs/handoff/31_point_5_closing.md` §11
> names, as what would falsify the firewall claim, *"a commit at or before
> `1e66c17` containing an outcome figure for this thesis — in a report, a
> document, a stored artifact under `reports/`, or a committed data file."*
> **`sweep.json` and `bands.json` are committed data files produced by a
> procedure whose acceptance metrics are outcome quantities.**

**WHETHER THEY PERTAIN TO THE CURRENT FROZEN THESIS OR TO A SUPERSEDED ONE CANNOT
BE ESTABLISHED WITHOUT OPENING THEM, AND OPENING THEM IS THE THING TO AVOID.**
**Routed to whoever holds the firewall. This report does not resolve it and does
not assert that the claim is either intact or breached.** Every figure in this
report was recomputed from bars through `src/sweep/grid.py`'s functions, never
read from those files.

**THIRD: `simulate.run_backtest` AND `portfolio.size_position` ARE TWO ENGINES.**
The sweep drives the first; `docs/design/04_1c_path_and_scope.md` §2.1 committed
the second as the risk unit. **A selection made on one and evaluated through the
other is comparing across a boundary
`docs/handoff/35_point_4_1c_denominator_audit.md` established is real.**

---

## 5. PART 4 — THE FROZEN PARAMETER INVENTORY

### 5.1 THE INVENTORY

**STATED CONSTANTS, cited where set:**

- **Donchian lookback: 20**, `costs.CostConfig.donchian_period`, also
  `sweep_population.DONCHIAN_PERIOD`.
- **ATR period: 14**, `sweep_population.ATR_PERIOD`, thesis §5.1.
- **ATR multiple: 2.25**, `sizing.STOP_ATR_MULT`, thesis §5.1.
- **Thesis stop floor: 1.50 per cent**, `sizing.STOP_FLOOR_FRACTION`.
- **Reward-to-risk: 1.5**, `sizing.REWARD_TO_RISK`, thesis §5.2.
- **Taker fee 0.0006 and maker fee 0.0002**, `costs.CostConfig`, venue-published
  and cross-checked at report 25.
- **Stop haircut 5 / 5 / 10 bps**, `costs.CostConfig.stop_haircut_bps`, and the
  source calls them *"Placeholders, per spec."*
- **`n_cost = 6.0`**, `costs.CostConfig`, described there as *"the one chosen
  number in the floor."*
- **Funding rate 0.0001 and settlement count 3**, `src/risk/exit_spec.py`.
- **Risk budget: 20.00 per trade, 120.00 aggregate, 2,000.00 capital**,
  `src/risk/budget.py`.
- **`baseline_days = 20`**, fixed and not swept per §4.3.

**DERIVED FROM OTHER CONSTANTS:**

- **The engine stop floor**, `costs.stop_min_pct` = `max(n_cost x c_roundtrip,
  leverage_term)` — 1.020 per cent BTC/ETH, 1.320 per cent SOL.
- **`time_stop_bars`, `max_hold_bars`, `threshold_r`**, all properties of
  `CostConfig` derived from `donchian_period`, `tau` and `phi`.
- **`FULL_SIZE_POSITIONS = 6`**, from the aggregate over the per-trade risk.
- **The cost tolerance level, 0.10**, from the displacement budget and the
  uncertainty parameter at `docs/design/04_1c_proper.md` §2 and §3.

**ESTIMATED FROM DATA: none in the frozen thesis's evaluation path**, per §4.4.

### 5.2 THE 3R SWEEP — SCAFFOLDING PROVENANCE ACROSS ALL FOUR

`docs/design/04_1e_stop_cap.md` §2.4 found `stop_max_pct` supplied from
placeholder dicts. **The same check, never run for the other three, is run here.**
Attribute reads of each of the four no-default parameters:

- **`stop_atr_mult`: 5 reads, none under `src/analysis/`** — `sweep.py`,
  `costs.py:245`, `run.py`, and two in `simulate.py`.
- **`stop_max_pct`: 9 reads in `src/`, SIX of them under `src/analysis/`** —
  three in `risk_unit_floor_curve.py`, two in `haircut_share_rerun.py`, one in
  `level_consequences.py`.
- **`rvol_threshold`: 2 reads, none under `src/analysis/`** — `run.py` and
  `signals.py`.
- **`baseline_days`: 7 reads, none under `src/analysis/`** — `costs.py:141`
  validation, `run.py`, and five in `signals.py`.

> ### THE SCAFFOLDING FINDING DOES NOT GENERALISE. OF THE FOUR, ONLY
> ### `stop_max_pct` IS READ BY THE ANALYSIS CHAIN FROM A STRUCTURE WHOSE
> ### DOCSTRING SAYS IT IS UNUSED.

**`exposure_profile._UNUSED_SIZING_PARAMS` MAKES THREE CLAIMS AND TWO OF THEM
HOLD.** `rvol_threshold` and `baseline_days` really are never read there.
Ledger instance (47) at `docs/design/04_1e_stop_cap.md` §6.2 already records the
one that does not, and **this report narrows it rather than widening it.**

### 5.3 ONE FURTHER PLACEHOLDER, INERT BUT NAMED

**`equity_usd = 2000.0` AND `max_leverage = 3.0`** carry a comment in
`costs.py` that is explicit: *"NOT a probed exchange constraint -- an unmeasured
placeholder."*

They feed `leverage_term`, which feeds `stop_min_pct` — **the derived floor.** At
present values the cost term binds and the leverage term does not, and `costs.py`
says why the term is kept anyway: *"so that a future downward revision of n_cost
cannot silently make it load-bearing without anyone noticing."*

**IT IS INERT TODAY AND IT IS INSIDE A DERIVED FLOOR THAT DOES GOVERN.** Recorded
here because §5.2's sweep would otherwise have looked exhaustive and this is a
placeholder in the same class one level down.

---

## 6. PART 5 — WHAT THESE FINDINGS BEAR ON

**STATED WITHOUT DECIDING ANY OF THEM. 4.2's DECISION DOCUMENT DECIDES.**

### 6.1 WHETHER TEST WINDOWS ARE INDEPENDENT EVALUATIONS

§3.1 and §3.3 bear on it and pull in opposite directions: **the test windows are
disjoint in time and no candidate appears in two of them**, but **seven of the nine
are subsequently training data for later folds.** Whether that makes them
overlapping views depends on what the aggregation is aggregating.

### 6.2 WHETHER POOLING IS ARITHMETICALLY DISTINCT FROM THE WHOLE WINDOW

§3.1 and §3.4 bear on it directly: the test windows are **disjoint and
contiguous**, their union is 2022-10-01 to 2024-12-31, and **no candidate falls in
two**. So pooling across the nine test windows and running that union as one
window range over **the same 8,567 candidates, each exactly once.**

**WHAT DIFFERS IS NOT THE POPULATION.** It is whether a per-fold parameter varies
across it — which under §4.4's first reading it does not, and under the second it
does.

### 6.3 WHETHER §3.3's GROUND SURVIVES

`docs/design/04_1c_consequences_and_thresholds.md` §3.3 chose the pooled level for
kill condition (d) on the ground that the schedule's docstring calls the nine folds
a stability probe rather than nine independent trials.

**AS A FINDING AND NOT A DECISION:**

- **THE DOCSTRING SAYS WHAT §3.3 SAID IT SAYS**, verbatim, and §2.3 quotes it.
- **THE GEOMETRY CORROBORATES IT.** Adjacent training windows overlap by 49.5 to
  50.3 per cent, and fifteen cross-overlaps make each test window an input to
  later folds' selection. **Nine trials drawn from overlapping data are not nine
  independent trials**, and the arithmetic warning is well founded.
- **BUT THE GROUND IS NARROWER THAN §3.3 USED IT FOR.** The docstring's warning is
  about **training-window overlap**. §3.1 establishes the **test** windows are
  disjoint — which is the population a per-fold verdict on (d) would actually be
  computed over. **The non-independence is in the selection, not in the test
  population.**
- **AND THE STATUS OF THE PREMISE IS UNCHANGED.** It remains a source-code
  docstring. A frozen pre-registration still rests on it, and this report
  establishes the facts without committing them.

> ### THE GROUND SURVIVES ON THE EVIDENCE AND IT SUPPORTS SOMETHING NARROWER THAN
> ### IT WAS USED FOR. WHETHER THAT NARROWING CHANGES §3.3's CONCLUSION IS 4.2's.

### 6.4 WHETHER THE PRE-WINDOW CANDIDATES ARE INSIDE THE EVALUATION POPULATION

**THE NUMBER IS 2,817, NOT 888**, and §3.4 gives the decomposition. **888 fall in
no period at all and a further 1,929 fall only in fold 1's training window.** Both
groups are outside every test window, and any pooled test-window evaluation
excludes all 2,817 whether or not that is intended.

**AND ONE MORE THING BEARS ON IT:** the 2,817 span 2022-01-05 to 2022-09-30, which
includes the deepest part of the 2022 drawdown. **Excluding them is not excluding a
random ninth of the data.**

---

## 7. WHAT THIS REPORT DOES NOT DO

**IT DECIDES NOTHING**, recommends nothing, and commits nothing.

**IT DID NOT OPEN THE SWEEP ARTIFACTS**, for §4.5's reason, and every figure here
was recomputed from bars.

**IT COMPUTED NO OUTCOME QUANTITY**, resolved no exit and did not invoke the
execution loop.

**IT OPENED NOTHING SEALED.** The schedule's holdout dates were read as dates, not
data.

**IT CHANGED NO CODE**, and the three unresolved items at §4.5 are reported rather
than fixed.

---

## 8. ARTIFACTS

- **Report:** `docs/handoff/40_point_4_2_fold_audit.md`
- **Tests, 11 added:** `tests/test_fold_audit.py`

**Full suite: 1322 passed** — 1311 before this step, plus the 11 above.
