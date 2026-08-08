# POINT 4 — PRE-REGISTRATION (FROZEN DESIGN)

**Status:** COMPLETE. Sub-points 4.1 through 4.5 all closed.
**Written:** before any performance figure from this strategy was seen.
**Purpose:** this document is the frozen validation design. It must be committed
to git BEFORE any analysis runs on real data. The commit hash is what makes this
a pre-registration rather than a claim of one.

**THE PERFORMANCE FIREWALL WAS INTACT WHEN THIS WAS WRITTEN.** No expectancy,
win rate, profit factor, Sharpe, equity curve, or any aggregate of net_pnl or
r_multiple had been inspected. Every criterion below is a pass rate, a binding
rate, a structural property of the data, or a logical entailment.

**AMENDMENTS ARE PERMITTED PRE-LIFT ONLY**, recorded as numbered appendices with
their justification and provenance. Nothing may be amended after the lift. If a
defect is found once results are seen, the honest response is to record the
defect and label everything downstream exploratory — not to fix the design and
continue as if it had been pre-registered.

---

## 4.1 — REGIME CHARACTERISATION

### Purpose — exhaustive list

Regime labels feed exactly three things:

1. Interpretation of post-lift results (distinguishing "no edge" from "no edge *here*")
2. The cross-symbol concordance check on the two-of-three rule
3. Point 8 decay detection

They feed **nothing else**. Specifically they must never touch: fold boundary
selection, parameter ranges, sweep design, acceptance thresholds, or drop
decisions. If a regime label reaches any of those, it has become a channel for
fitting.

### Admissibility rule

A regime axis must be computable from a data file that has never seen the
strategy's parameters.

This excludes breakout-follow-through proxies (e.g. "fraction of Donchian
breakouts followed by a new extreme within k bars") — these are strategy success
in price clothing, and they are where the temptation lives.

### Labelled axes (two)

**Axis 1 — volatility relative to the cost floor: m\***

`m* = stop_min_pct / median(ATR%)` over the window.

Low m\* = volatility comfortably above the cost structure. High m\* = the floor
dominates and the strategy is structurally squeezed. M8 measured m\* at 1.71–4.08
across symbol-years, implying median 15m ATR% of roughly 0.25%–0.60% — a 2.4x
spread, so the axis has real variance. It is also the axis on which the strategy
mechanically breaks.

Preferred over raw ATR% because it is an already-committed derived quantity
(derived-over-free) and because it is dimensionless in a way that makes BTC and
SOL comparable despite different floors.

**Cut points [AMENDED — see Appendix A]:** frozen 2022–2024 terciles, fitted on
in-sample data only and applied unchanged forward.

**m\* = 1.0 is a REPORTED STRUCTURAL MARKER, NOT A CUT.** It is the level at
which median volatility would exactly reach the cost floor. M8 measured m\* at
1.71–4.08, so it is expected never to be crossed. The count of windows below it
is reported; a crossing in the holdout would be notable in itself.

The original cut points were defective — see Appendix A. This axis no longer
carries an external anchor and therefore no longer has the zero-leak property
that motivated preferring it over raw ATR%. It remains a committed derived
quantity rather than a free one, and remains dimensionless across symbols with
differing floors.

**Known non-independence:** m\* and the A3 floor-binding check share a unit.
"The floor binds in high-m\* regimes" is near-tautological. A3 and the regime
label are NOT two confirmations of one thing.

**Axis 2 — directional efficiency: Kaufman efficiency ratio**

Net displacement over the window divided by the sum of absolute bar-to-bar moves.
Bounded 0–1, direction-agnostic, contains no strategy parameters.

Rationale: a trend-continuation thesis claims edge when price moves *efficiently*,
not merely a lot. High-volatility chop and low-volatility drift are different
worlds and volatility alone cannot separate them. This is the axis where the
thesis lives, and therefore the most informative stratification after the lift.

**Cut points:** 2022–2024 terciles, frozen and applied unchanged forward. There
is no external anchor available for this axis. Holdout cells will be unbalanced;
that imbalance is a finding, not a defect to be corrected.

### Reported covariates (two, uncut)

- **Drift:** signed log return over the window, plus fraction of bars with
  EMA20 > EMA50 (free — it is the strategy's own filter). Not labelled because
  long/short cohorts are already reported separately, which absorbs most of what
  a drift label would carry.
- **Liquidity level:** median daily quote volume. Does not affect the RVOL gate
  (session-normalised over trailing days, so self-normalising to level) but does
  affect slippage realism. OOS sits in a market 40–50% quieter, market-wide.

Four axes at three levels would be 81 cells against 4.5 years — every fold
becomes its own unique regime and "test across multiple windows that resemble it"
becomes impossible. Hence two labelled, two continuous.

### Measurement

- **Per symbol**, not market-wide. Floors differ by symbol (1.020% vs 1.320%), so
  m\* is per-symbol by construction; two-of-three also operates per symbol.
- **Per bar**, on a rolling trailing window, aggregated upward to whatever
  reporting unit is needed. One label per fold would discard within-fold
  heterogeneity — exactly the thing that makes a fold's result hard to read.
- **Window: 30 days**, with sensitivity reported at 14 and 60.

Window rationale: must be slower than the trade horizon (max hold 40 bars ~10h)
or it measures noise, and long enough to contain a meaningful number of the
strategy's own opportunities. M9's counts imply ~1.5–2.3 signals per
symbol-day-direction, so 30 days spans ~50–70 signals per direction, comfortably
above the 30-trade minimum. Below ~15 days the label describes a sample too thin
to be a regime.

### Causality — BOTH leak defences binding

The regime-label leak was resolved with **both** defences mandatory, not one
primary and one bonus:

**(b) Post-hoc reporting only.** Fold boundaries are cut by a fixed calendar rule
decided in advance (see 4.2). Labels are never used for fold selection. A fixed
calendar rule is harder to game and easier to verify than any argument about
clean regime boundaries.

**(a) Causally computable labels.** Trailing windows only. No centring, no
full-sample normalisation, no full-window quantiles. This is NOT a bonus: a
descriptive statement conditioning on something unobservable at the time is
useless, and Point 8 decay detection is impossible for a condition that can only
be identified in retrospect. You cannot monitor for what you can only see
afterwards.

**Guard requirement:** enforced by a mutation test that specifically catches a
dropped shift in the regime computation. A generic `assert_causal` is known to
pass vacuously here — truncating at bar T leaves bar T's own cell intact. Three
vacuous guards have been found in this project; this is a pattern, not bad luck.

### Required output

**Cross-symbol label concordance, per fold.** The two-of-three rule assumes BTC,
ETH and SOL are partially independent observations. If all three sit in the same
regime cell 90% of the time, "three symbols agree" is closer to one observation
repeated three times, and two-of-three is weaker evidence than it appears. This
puts a number on an assumption currently taken on faith.

---

## 4.2 — FOLD ARCHITECTURE

### IS/OOS boundary

- **In-sample: 2022-04-01 → 2024-12-31**
- **Holdout: 2025-01-01 → 2026-07-26**

The boundary is 31 December 2024 — a calendar rule decided before any label or
return was inspected, landing on the contamination ledger's own seam (2022–23
partially spent, 2024 comparatively clean, 2025–26 untouched).

Contamination does not argue against using 2022–23 for training. Structural facts
derived from it make *fitting* to it partly circular, but the circularity damages
the test, not the train — and 24 months of a 55-month dataset cannot be discarded.
Consequence: walk-forward test folds inside 2022–23 are weaker pseudo-OOS
evidence than those inside 2024. This weights interpretation, not structure.

Start is 2022-04-01 because Q1 2022 is consumed as warm-up and is never traded.

### Warm-up

**45-day buffer, drawn from data PRECEDING each fold, never consumed from within
it.**

The 3R smoke test found a one-month slice spending 1,920 of 2,881 bars on
warm-up. Warm-up drawn from prior bars leaks nothing because the slot baseline is
strictly backward-looking.

Binding component ~30 days: `baseline_days` at sweep maximum, the 30-day regime
window, ATR(14), Donchian-20, and EMA50 (which needs ~200 bars to converge to
within rounding, not 50). The 45-day buffer gives headroom so the number does not
move if a sweep range widens slightly.

**Required test:** no trade may originate from a bar inside the buffer. If the
engine emits a signal from a warm-up bar, the buffer is not doing its job. This
is a test, not a hope.

Cost accepted: Q1 2022 is never traded.

### Fold structure

**Rolling 6-month train / 3-month test, 3-month step. Nine folds across
2022-04-01 → 2024-12-31.**

Rolling rather than anchored/expanding for one specific reason: with an anchored
window, later folds train on more data than earlier ones, so fold-to-fold
differences in selected parameters confound *market change* with *estimation
noise shrinking*. Since one of the two things wanted from walk-forward is a
stability read — do the parameters wander? — that confound is fatal to the
exercise. Constant training length makes fold-to-fold variation attributable to
the market.

Sizing, from M9 (512–829 signals per symbol-year-direction, RVOL-only):
- 6-month train ~250–400 trades per symbol-direction, 500–800 per symbol
  (vs 200 IS minimum — comfortable)
- 3-month test ~125–200 per symbol, 60–100 per direction
  (vs 50 OOS and 30 per direction — adequate, not lavish)

**Adjacent training windows overlap by 50%. The nine folds are a STABILITY PROBE,
NOT NINE INDEPENDENT TRIALS.** If they are ever counted as trials, the arithmetic
is wrong.

12/3 was considered — more regimes per training window, more stable parameters,
at the cost of adaptivity and fold count. 6/3 chosen because the free-parameter
count is genuinely small (see 4.3: effectively about two and a half), and low
parameter count is what makes short training windows affordable. A 6-month window
also gives a stable median ATR% for per-fold m\*; 3 months would not.

### Holdout budget — ONE CANDIDATE, ONE LOOK, WHOLE WINDOW

- **One candidate configuration** reaches the holdout, selected by the
  pre-registered 4.3/4.4 procedure — not by judgment at selection time.
- **One evaluation, whole window**, 2025-01-01 → 2026-07-26.
- **Stratified reporting afterwards** by regime label — descriptive only, no
  thresholds attached.
- **If it fails, there is no candidate two.** The holdout is marked spent.
  Anything subsequent is explicitly labelled exploratory and cannot be presented
  as validation.

Why this replaced the 9-candidate proposal: the worry behind 9 (that a single
number hides where the strategy worked and where it failed) is correct, but
splitting into three periods with three candidates each runs nine pass/fail
decisions — roughly a 37% chance at least one passes by chance. 4.1's regime
labels solve the actual problem at zero multiplicity cost: **breaking one result
into strata is description; running three tests with three verdicts is
multiplicity.** They look similar on the page and are completely different
statistically.

The power argument against 6-month slices was WITHDRAWN — M9's counts showed it
was wrong. The false-positive argument stands; it is arithmetic, not data.

Why one shot is acceptable despite unlucky-regime risk:
1. The nine walk-forward test folds already provide the multi-window evidence.
   The holdout's job is different — it is the single unbiased read.
2. **The holdout is not the last data we will ever see.** Point 6 is paper
   trading on live data. A strategy killed unluckily is recoverable at cost of
   time; a strategy passed by multiplicity is NOT recoverable, because we would
   never know.

The same reasoning rejects reserving part of 2025–26 as a deeper reserve. Forward
time generates fresh data for free; hoarding historical holdout while the
calendar produces more is the wrong conservation.

### Sigma measured in-sample only

E6's post-lift dispersion measurement draws from IS folds only. Measuring sigma
on the holdout is a look at the holdout — and worse, a look taken specifically to
decide whether fold design must change, which is holdout information feeding
design.

### Holdout regime composition NOT inspected before the lift

Option 3 from 4.1 (one frozen summary table) is WITHDRAWN as unnecessary — the
stricter holdout budget removed the decision it was meant to feed. There is no
candidate-per-period allocation to size. Holdout regime composition is computed
after the lift as part of the stratified report. **2025–26 remains fully
untouched until the single evaluation.**

---

## 4.3 — SWEEP DESIGN

### Structural principle: the sweep is three things, not one grid

The four unset parameters are NOT peers. They differ in what they do, in what
evidence can select them, and in whether the firewall permits selecting them at
all. Structure: **one parameter searched, one derived, one selected on a
non-performance criterion, one fixed.**

Naive alternative rejected: 11 x 8 x 8 x 4 ~ 2,800 cells per symbol-fold. At that
size the best cell is best by chance.

### `stop_atr_mult` — the only genuine search

**Swept m\* → m\*+2.5 in steps of 0.25, per training fold per symbol.** Eleven
grid points.

m\* computed per training fold (A6) — a global anchor would read the holdout.

Range runs UPWARD from m\* because m\* is where the MEDIAN ATR% crosses the floor,
so at exactly m\* the floor binds on roughly half of trades. Clearing the 20%
binding threshold needs roughly the 20th percentile to clear, materially above
m\*. Searching below m\* searches a region already known to be floor-dominated.

**PRE-COMMITTED: the range is NOT extended upward to rescue a failing A3.**
Extending means accepting arbitrarily wide stops and correspondingly tiny
positions purely to satisfy a binding-rate check — converting a tradability
finding into a fitted parameter. If the range is exhausted, that is the finding.

The +/-25% kill condition operates on the SELECTED value in absolute multiplier
terms per fold, since m\* moves between folds.

### `stop_max_pct` — derived, not swept

**Cap = the percent value corresponding to m\*+2.5 at fold-median ATR%, per fold
per symbol.**

This makes the cap a proper guard rail: inert under normal conditions (it can
only bind when realised ATR% at trade time substantially exceeds the fold median)
and active only in genuine volatility spikes. Not tuned, no performance
criterion, moves with the same anchor as everything else.

Sweeping it is explicitly rejected: a swept cap finds the value that clips the
worst outcomes, which is fitting to returns through a component whose stated
purpose is target plausibility and exchange-minimum protection. A guard rail
optimised for performance stops being a guard rail.

Percentile anchoring (e.g. 90th percentile of fold ATR%) was considered and
rejected — arguably cleaner conceptually, but it introduces a new free number.

### `rvol_threshold` — selected on pass rate, not performance

**Set per training fold per symbol at the value producing a 50% PASS RATE ON
BREAKOUT BARS in that fold.**

Rationale: the edge claim is that the gate separates good breakouts from bad, and
4.4's attribution test asks exactly that. Selecting the threshold that performs
best in training and then running attribution measures a threshold chosen because
it performed — asking the data the same question twice. The structural pass
already warned that RVOL's selectivity is largely pre-spent by conditioning on
the breakout.

50% specifically: it maximises statistical power (equal-sized arms), it is a
round pre-committed number rather than a fitted one, and M9 confirms the gated
arm still clears evidence minimums at half strength (250–400 IS trades per
symbol, 60–100 per test fold).

**Pre-registered sensitivity at 30% and 70% pass rates, reported alongside.**
If the gate is real, expectancy per trade should improve MONOTONICALLY from 70%
→ 50% → 30%. If flat across all three, the gate is decorative regardless of the
0.05R comparison at any single point. This is a stronger and more falsifiable
test than picking one threshold.

Cost accepted: performance may be left on the table if the true optimal pass rate
is 15% or 85%. A gate whose value depends on hitting a narrow threshold band is
a gate not worth trusting, and the monotonicity test would reveal a strong edge
at an extreme.

### `baseline_days` — fixed at 20, not swept

Sensitivity <0.5 across 5→30, **non-monotonic**. Non-monotonic is the informative
part: the variation is noise, not signal, so any selected value would be selected
by noise. Zero grid resolution spent.

20 rather than 5 or 30 because it sits mid-range, gives a stable slot baseline
without an excessive trailing requirement, and fits within the 45-day warm-up.

### Total grid

**11 x 3 = 33 configurations per symbol per fold.** Nine folds, three symbols.
Small enough that the multiple-comparisons problem stays bounded.

### Plateau-not-peak

Per fold per symbol:

- The selected `stop_atr_mult` must sit where **the adjacent grid points on both
  sides also pass acceptance.** A value at the edge of the searched range, or
  with a failing neighbour, fails the plateau requirement.
- **SELECTION RULE: the centre of the widest contiguous passing band, NOT the
  argmax.** Pre-committed now because the pull toward argmax after the lift will
  be strong.
- If no contiguous band of three passing points exists, the fold produces no
  selection.

**Stated limit:** at 0.25 steps, three adjacent points span 0.5 in multiplier
terms — well under the +/-25% the kill condition demands. The plateau test is
NECESSARY BUT WEAKER than the kill condition. The +/-25% check remains a separate,
stricter test applied to the finally selected value. This gap is stated rather
than papered over.

---

## 4.4 — ACCEPTANCE AND DROP PROCEDURE

### Firewall clarification

**The firewall protects the DESIGN, not the EXECUTION.** Once 4.1–4.5 are frozen,
the sweep runs and selection happens by expectancy — legitimately, because the
selection rule was written blind. What would be illegitimate is seeing results and
then choosing the rule.

Consequence: **nothing in 4.3 or 4.4 executes until 4.5 is closed and committed.
There is no partial lift.**

### The nine-step sequence — NO STEP REVISITS AN EARLIER ONE

1. **E6** — measure sigma from `r_multiple`, IS folds only, recompute power table
2. **Sweep** — all 33 configurations, all folds, all symbols
3. **Per-fold band identification and plateau selection**
4. **Collapse** nine fold selections into one candidate
5. **A3 floor-binding check**
6. **Two-of-three qualification**
7. **D5 single-pass leave-one-out**
8. **One confirmation run** (+ robustness gates)
9. **Holdout — single evaluation**

If step 5 fails, we do NOT return to step 3 with a different band. Ordering can be
gamed once numbers are visible, which is why the sequence is pre-committed.

### Collapse: band intersection on m\*-offsets

Median of nine is rejected: adjacent folds share 50% of their training data, so
nine selections are not nine observations. A median of correlated values looks
stable while telling you little about stability.

- Express each fold's passing band as an **offset from m\*** ("m\*+0.5 to
  m\*+1.25"), not as an absolute multiplier — absolute values are not comparable
  across folds because m\* moves.
- **Primary:** intersect the nine bands. Non-empty → candidate is the centre of
  the intersection.
- **Fallback (pre-committed):** if empty, take the offset contained in the
  largest number of fold bands, and report the coverage count.
- **Coverage below 7 of 9 is a documented instability**, reported prominently.
  Not an automatic kill, but it means the parameter does not hold across time and
  the holdout result must be read in that light.

Intersection is stricter than median and produces a stability statistic for free.

### A3 floor-binding check

The handoff states A3 as <20% binding per symbol per year, but selection happens
per 6-month training fold. These units do not align, and the gap is where a check
quietly stops binding.

- **Measured per training fold** — that is where the parameter is chosen, so that
  is where the check must bite.
- **Reported per year** as the pre-committed reporting unit.
- **Evaluated PER SYMBOL, never pooled.** It is a statement about whether that
  symbol's noise is wider than that symbol's cost floor, and the floors differ
  (1.020% vs 1.320%). Pooling would let SOL rescue BTC on an intrinsically
  per-symbol question.
- A fold failing A3 produces no selection, exactly as a missing plateau does.

**Pre-registered reading if a symbol fails throughout:** that symbol is NOT
TRADABLE at $2,000 with these fees. A finding about tradability, NOT a kill
condition. Other symbols continue independently.

**EXPECT THIS TO BE TIGHT.** The derived floor (1.020%/1.320%) is higher than the
1.000% already binding on 65–81% of trades, and m\* is where the MEDIAN crosses.

### Two-of-three — "same direction of edge" defined

A corroborating symbol counts if its **gated expectancy exceeds its ungated
expectancy by >= 0.05R** — the same marginal-contribution threshold used
throughout.

NOT "is profitable." Profitability is a different claim from "the gate works,"
and two-of-three exists to test the latter.

Deliberately weaker than requiring the corroborating symbol to pass fully;
requiring full passage would make the rule effectively "all three must pass,"
which is a different and much harsher rule than the one committed to.

**Interpretation caveat:** 4.1's concordance measurement may show all three
symbols sit in the same regime cell most of the time, in which case two-of-three
is weaker evidence than it looks. Reported alongside; moderates interpretation
rather than changing the rule.

### D5 — THREE dispositions, not one

Applying one drop rule uniformly across four arms is a category error.

**DROPPABLE — RVOL gate, time-stop checkpoint.** Both are edge components. Both
claim to improve expectancy per trade. Both are properly subject to "prove it or
go."

**THESIS-CRITICAL — EMA trend filter.** If it fails to contribute 0.05R,
dropping it does not produce a better version of this strategy; it produces a
DIFFERENT strategy (an undirected Donchian breakout with no trend context). The
entire edge claim is trend continuation. **PRE-COMMITTED: EMA failing attribution
is REPORTED AS A THESIS FAILURE, NOT EXECUTED AS A DROP.**

**GUARD RAIL — max-hold cap.** Not an edge component; its job is bounding
exposure, and a 40-bar hold already crosses an unmodelled funding settlement.
Dropping it for failing to add 0.05R means unbounded holds justified by a
performance criterion — the same error rejected for `stop_max_pct`. **Measured
and reported, NEVER dropped.**

D5 mechanics otherwise unchanged: leave-one-out against the full model, ONE pass,
all failures dropped SIMULTANEOUSLY, ONE confirmation run, decisions POOLED
across symbols and folds, TIES GO TO REMOVAL. No component may be added as an
attribution arm after the firewall lifts.

### Robustness gates before the holdout (applied at step 8)

- **Top-5% winner removal.** Remove the top 5% of trades by `r_multiple` per
  symbol; if expectancy flips negative, the edge is a handful of trades and does
  not survive. Evaluated per symbol.
- **+/-25% parameter sensitivity** on the final `stop_atr_mult` in absolute
  multiplier terms. Needs a plateau, not a peak.

Failing either means the candidate does NOT reach the holdout. Given the one-shot
budget, sending a candidate already known to be fragile spends the holdout on a
question already answered.

### Partial-symbol holdout

If A3 excludes one symbol but the others qualify, the holdout evaluates the
reduced candidate. Two-of-three remains satisfiable and the exclusion is a stated
tradability finding, not a strategy failure. **Recorded explicitly as testing
something narrower than what was designed.**

---

## 4.5 — METRICS, REPORTING, AND THE LIFT PROTOCOL

### The lift protocol

The lift is irreversible, so it is a discrete event with a defined precondition,
not a gradual drift into looking at numbers.

**PRECONDITION: 4.1–4.5 written, agreed, and COMMITTED TO GIT.** Not "agreed in
chat" — committed, with a hash. A design frozen in a commit that provably
predates the results is the difference between pre-registration and a claim of
pre-registration.

**MECHANISM: the lift happens when the analysis script runs.** Therefore the
analysis script must be written and reviewed BEFORE it runs — reviewed against
the frozen design, not against its output. Writing it, running it, seeing the
output, then fixing a bug means the lift was already spent on a buggy version.

**Build ordering:**

1. Commit the frozen 4.1–4.5 design
2. Build regime measurement, sweep harness, reporting layer — tested on fixtures
   with answers known by construction
3. Verify against fixtures ONLY — no real-data aggregates
4. Run E6 on IS folds — **THIS IS THE LIFT MOMENT**
5. Everything else follows the nine-step sequence

Step 3 will feel like an unnecessary delay and is the step most worth keeping.
Three vacuous guards have been found in this project. A harness bug discovered
AFTER the lift cannot be fixed by rerunning, because the buggy output has already
been seen.

**TWO FIREWALLS.** The lift covers IN-SAMPLE results only. The holdout stays
sealed until step 9 of the 4.4 sequence. The second firewall outlives the first,
and it is crossed at the moment curiosity peaks.

### E6 — first act after the lift, and what it may change

Measure sigma from `r_multiple`, IS folds only, recompute the power table against
the 1.2R estimate.

**PRE-COMMITTED TRIGGER: if measured sigma is large enough that a 3-month test
fold's standard error on expectancy exceeds 0.20R, test folds extend to 6 months
with a 6-month step, giving five folds instead of nine.**

Anchored to the decision the folds must support rather than to a round number.
At assumed sigma = 1.2R over 50 trades, SE ~ 0.17R. Given typical fold counts of
125–200 trades per symbol, the trigger trips at roughly sigma > 2.2–2.8R.

A flat sigma threshold was considered; if used it would be 2.5R, not the 1.5R
originally proposed. The 1.5R version was rejected because it ignored actual
per-fold trade counts — 3-month folds carry 125–200 trades per symbol, not 50
(the 50 is a floor, not an expectation), so it would have fired a fold-design
change where folds were adequate.

**The evidence minimums do NOT move.** Not to be reduced, not pooled across
symbols. The resolution order remains: loosen thresholds → extend the in-sample
window → drop to a single condition. The holdout is not touched.

Setting the trigger before measuring is the point. A trigger chosen after seeing
sigma is not a trigger.

### Noise caveat — ON RECORD BEFORE ANY NUMBERS ARRIVE

If sigma is anywhere near 1.2R, the standard error on a single fold's expectancy
is several times the 0.05R threshold that D5 drop decisions use. Pooling across
symbols and folds is what D5 relies on to bring that error down, and 4.4 commits
to pooling — so the procedure is sound. **But individual per-fold attribution
numbers will be noisy, and reading them as if precise would be a mistake.**

### Metrics

**PRIMARY: expectancy per trade in R, net of costs.** Every kill condition and
threshold is denominated in it. It remains the single decision metric.

**SECONDARY: expectancy per bar.** The time-stop checkpoint exits at bar 21 and
max-hold at bar 41, so per-trade expectancy silently rewards holding longer.
Per-bar expectancy is the honest comparison for the two time arms and is reported
wherever a time arm is compared. **It never overrides the primary metric in a
decision** — it exists so that a per-trade result driven purely by holding time
is visible as such. If it ever starts driving decisions, that is drift.

**DIAGNOSTIC (no thresholds attached):** exit-reason distribution; floor/cap/ATR
binding mechanism counts; holding-time distribution on stop and target exits
only; all provenance counters; refusal counters; cross-symbol regime concordance.

**REPORTED BUT NON-DECISIONAL:** Sharpe, Sortino, max drawdown, profit factor,
win rate, equity curve. These come from portfolio mode, which is the realism
instrument, not the edge-test instrument. Worth having; not evidence about the
edge. Drawdown here is FIXED-BET drawdown, not compounding (fixed risk_usd).

### The arm decomposition

Five arms, run in SIGNAL MODE (gated arms are filters of one ungated simulation,
so all arms share an identical trade universe by construction):

1. Full model
2. Minus RVOL gate
3. Minus EMA trend filter
4. Minus time-stop checkpoint
5. Minus max-hold cap

**The two time arms stay SEPARATED.** A combined "time exits" arm would confound
a checkpoint firing on a decision rule with a cap firing on elapsed time alone.

**D6 — does the checkpoint CREATE the mode or CATCH one?** Holding time is
degenerate by construction for time-stop (always 21) and max-hold (always 41), so
the question is answerable ONLY on stop and target exits, with 21 and 41 drawn as
reference lines. Stop/target exits clustering just before 21 → the checkpoint is
catching an existing mode. Smooth through it → the checkpoint is creating one.

### Reporting structure

Everything reported **per symbol, never pooled** — except D5 drop decisions,
which 4.4 explicitly pools across symbols and folds.

**Layer 1 — per fold, per symbol:** selected offset, band width, A3 binding rate,
trade counts by direction, expectancy per trade and per bar, exit reasons.

**Layer 2 — aggregated across folds, per symbol:** band intersection and
coverage, attribution table, sensitivity results, top-5% removal.

**Layer 3 — holdout, per symbol:** primary metric, then regime-stratified
breakdown as DESCRIPTION ONLY. Plus the two-of-three verdict and the long/short
cohort split with its pre-committed short-side drop rule.

Long and short cohorts stay separate throughout.

---

## PRE-REGISTERED EXPECTATION — WEAKEST LINK

Recorded before results so it cannot be rationalised afterwards.

**The most likely single outcome of Point 4 is a TRADABILITY FINDING ON BTC, not
a strategy verdict.** The derived floor (1.020%) sits above a level already
binding on 65–81% of trades, and clearing 20% binding requires roughly the 20th
percentile to clear — well above m\*. There is a real chance the m\*+2.5 range is
exhausted without reaching 20%.

This is not a flaw in the design. It is the fee math arriving where it was always
going to arrive. If it happens, the pre-committed reading holds and **the range
is not widened.**

Second most likely: the RVOL gate proves decorative. The structural pass already
found its selectivity largely pre-spent by conditioning on the breakout. The
30/50/70 monotonicity test answers this cleanly.

**The validation protocol does not create edge. It prevents belief in edge that
is not there.** If Point 4 returns no edge, that is the protocol working
correctly, not failing.

---

## UNCHANGED COMMITMENTS CARRIED INTO POINT 4

- All pre-committed kill conditions. They are the goalposts.
- Evidence minimums: 200 IS trades, 50 OOS, 30 per direction — PER SYMBOL.
- Short side dropped if OOS expectancy < 0 over 30+ short trades.
- Guard rail principle: different unit from the mechanism guarded.
- D5 single-pass. Loud failures over silent corruption. Derived over free.
- A guard must be tested against the specific mutation it exists to catch.
- Every pre-committed threshold carries its aggregation rule.
- Every Point 2 data decision and every Point 3/3R engine semantic.
- 15m, Bitget, BTC/ETH/SOL, $2,000, risk_usd $20 fixed after costs.

## KNOWN GAPS LOGGED, NOT RESOLVED HERE

- Funding costs across a 40-bar hold (~10h, crosses >=1 settlement) — UNMODELLED,
  Point 6. Must NOT be used to justify shortening the hold.
- The 425 reconstruction-divergence bars / signal-bar overlap measurement.
- Bitget kline taker-buy volume — documentation check only; re-pulling reopens
  Point 2.
- Day-of-week separation in the RVOL slot baseline. Default: ignore.
- Percent-of-equity sizing — Point 7.
- Labelled variants (STRUCTURE_STOP, EXTENSION_GUARD, NO_TIME_STOP, partial
  runner) remain unimplemented and must not be silently promoted.

---

## APPENDIX A — AMENDMENT 1: m\* CUT POINTS

Made pre-lift. No performance figure seen at time of amendment.

**Defect.** The two m\* cut points originally specified in 4.1 do not partition
the axis.

  1. "The top of the multiplier range swept in 4.3" is m\*+2.5 — an OFFSET from
     m\*, not a LEVEL of m\*. Wrong units. It cannot cut the m\* axis at all.
     The error survived review because it sounded externally anchored.
  2. m\* = 1.0 lies entirely outside the observed range (M8: 1.71–4.08). Every
     window in the dataset falls on one side of it, so it yields one bucket,
     not three. A cut that never cuts.

**Correction.** m\* cut points become frozen 2022–2024 terciles, matching the
efficiency axis. m\* = 1.0 is retained as a reported structural marker only.

**Cost.** The m\* axis loses its external-anchor zero-leak property — the
specific reason m\* was preferred over raw ATR%. What remains: it is still a
committed derived quantity, and still dimensionless across symbols with
differing floors. Frozen in-sample terciles applied forward is the same
discipline already accepted for the efficiency axis, so this is a downgrade to
an existing standard, not below it.

**Provenance.** Justified solely from M8's measured m\* range, a structural
diagnostic from 2022–23 already logged as partially spent in the contamination
ledger. No holdout information involved. The original text is preserved in git
history at the prior commit.

---

## APPENDIX B — AMENDMENT 2: TERCILE FIT WINDOW

Made pre-lift. No performance figure seen.

The tercile fit window for both labelled axes is 2022-01-01 → 2024-12-31,
which is NOT the same as the trading in-sample window (2022-04-01 →
2024-12-31, §4.2).

Rationale. The 2022-04-01 boundary exists because Q1 2022 is consumed as
warm-up and never traded. Regime labels are not a statistic about the traded
population — they describe market conditions, which exist in Q1 2022 whether
or not the strategy trades them. A distribution fit benefits from all
available pre-holdout data. The regime measurement's own warm-up consumes to
roughly 2022-01-31 in any case, so the difference is February and March 2022:
about 5.6% of the fit set.

The holdout boundary is unchanged. Nothing at or after 2025-01-01 enters the
fit.

---

## APPENDIX C — AMENDMENT 3: m\* < 1.0 MARKER IS WINDOW-SPECIFIC

Made pre-lift. No performance figure seen.

§4.1 states m\* = 1.0 "is expected never to be crossed" without naming a
window. Measured 2022-2024: zero crossings at 30 and 60 days on all three
symbols, but 737 (ETH) and 2,131 (SOL) at 14 days, all inside the 2022
drawdown.

The marker is therefore defined AT THE 30-DAY PRIMARY WINDOW. Any reported
crossing must state the window it was measured at, or the claim is ambiguous.

---

## APPENDIX D — AMENDMENT 4: m\* AXIS JUSTIFICATION NARROWED

Made pre-lift. No performance figure seen.

Appendix A conceded that m\* loses its external-anchor property but retained
"already-committed derived quantity" and "dimensionless across symbols" as
justification. Under per-symbol tercile labelling, raw ATR% has both of those
properties equally — terciles wash out exactly the level information that
normalising by the cost floor provides.

What genuinely survives: m\* = 1.0 is an interpretable absolute marker (see
Appendix C), and the axis is denominated in units of the mechanism that
mechanically breaks the strategy, so a label maps directly onto the failure
mode. The axis is retained on those grounds. The earlier justification
overstated the case.

---

## APPENDIX E — REGIME m\* IS NOT SWEEP-ANCHOR m\*

Two distinct computations share the name.

REGIME m\*: rolling 30-day window, per bar, per symbol. Measured range
1.16-8.58 across 2022-2024. Used only for labelling.

SWEEP-ANCHOR m\*: per 6-month training fold, per symbol (§4.3, A6). Anchors
the stop_atr_mult grid.

The 30-day extremes are NOT where the sweep will run. Recorded so the report's
figures are not misread as the sweep range.

---

## APPENDIX F — AMENDMENT 5: m* POPULATION, AND A3 BEFORE THE SWEEP

Made pre-lift. No performance figure seen.

F.1 — SWEEP-ANCHOR m* POPULATION.
§4.3 specifies m* "computed per training fold (A6)" without naming the
population. It is hereby defined as: median ATR% over BREAKOUT BARS in the
training fold — bars passing Donchian-20 and the EMA20/EMA50 filter, BEFORE the
RVOL gate.

Rationale. The argument for searching upward from m* is that the floor binds on
half the population at m* by construction. That holds only if the population
defining the median is the population A3 measures binding over — which is the
traded population, not all bars. Breakout bars are intrinsically higher
volatility than the unconditional distribution, so an all-bars m* would sit
above the relevant one and the construction would not hold.

Gated signal bars were rejected: they depend on rvol_threshold, which is itself
selected per fold, so anchoring the grid to them would make the grid depend on a
quantity the grid exists to help select. Breakout bars depend only on fixed
components.

This also fixes the population for stop_max_pct, which §4.3 derives from
"fold-median ATR%" — the same median, same population.

F.2 — A3 IS COMPUTED BEFORE THE SWEEP.
The nine-step sequence in §4.4 places A3 at step 5. A3 requires no trade
outcome: floor binding is determined at entry from ATR at the signal bar, and
binding rates are on the firewall's allowed list.

A3 is therefore computed across the full grid — all folds, all symbols, all
eleven multipliers — BEFORE the firewall lifts, and grid points failing A3 are
excluded before any simulation runs.

The revised sequence:
  0. Grid definition and A3 pre-screen  [PRE-LIFT]
  1. E6 sigma measurement                [THE LIFT]
  2. Sweep, A3-surviving grid points only
  3-9. Unchanged.

The outcome is unchanged: a grid point failing A3 fails acceptance whenever it
is checked. What changes is that the tradability finding — the pre-registered
most likely outcome of Point 4 — is available without spending the firewall.
The non-revisitability rule still binds: step 0 is not rerun with a different
range if it eliminates a symbol. §4.3's "the range is NOT extended upward to
rescue a failing A3" applies with full force at step 0.

CLARIFICATION ON "NO PARTIAL LIFT". §4.4 states "nothing in 4.3 or 4.4 executes
until 4.5 is closed and committed. There is no partial lift." Both conditions
are satisfied: 4.5 is closed and committed, and step 0 is not a partial lift.
"No partial lift" forbids inspecting SOME performance figures while withholding
others. Step 0 inspects NONE — floor and cap binding are entry-time structural
properties on the firewall's allowed list, computed without running Layer B or
importing simulate. The firewall lifts at step 1 and not before.

---

## APPENDIX G — TWO FINDINGS FROM 4.2, RECORDED WITHOUT RULE CHANGE

G.1 — PER-FOLD CONCORDANCE IS UNSTABLE.
§4.4 says the concordance measurement "moderates interpretation rather than
changing the rule", written when only a whole-period figure existed. Per fold,
m* concordance ranges 0.159 to 0.661 against a whole-period 0.4544 — a spread
wider than the value itself. Efficiency ranges 0.189 to 0.530.

The degree of independence underpinning two-of-three therefore varies roughly
fourfold across folds. A verdict driven by high-concordance folds represents
materially less independent evidence than one driven by low-concordance folds,
and the aggregate cannot distinguish them. The two-of-three rule is UNCHANGED.
This is recorded so the per-fold figures are on the table when the verdict is
read. Full table in reports/10_fold_architecture.md.

G.2 — §4.2's "REQUIRED TEST" IS THE WEAKER OF TWO.
§4.2 states: "Required test: no trade may originate from a bar inside the
buffer. This is a test, not a hope." As implemented anywhere that slices signals
to the train window, that check CANNOT FAIL — it is a hope in the shape of a
test.

What establishes sufficiency is the pair: indicators computed with a 45-day
buffer must be BIT-IDENTICAL to those computed with a 90-day buffer from
train_start onward, AND a deliberately shortened buffer must be DETECTED as
differing. Both are implemented (report 10 §3). §4.2's requirement is satisfied
by the pair, not by the literal check alone.

Measured: 25 days suffices for every strategy indicator; the binding component
is the 20-day RVOL slot baseline, not EMA50. The 45-day buffer carries ~20 days
of measured headroom. No change — the buffer costs nothing.

---

## APPENDIX H — AMENDMENT 6: stop_max_pct DERIVATION CORRECTED

Made pre-lift. No performance figure seen.

DEFECT. §4.3 derives the cap as (m* + 2.5) x fold-median ATR%. The top grid
point is stop_atr_mult = m* + 2.5. At that point the cap binds whenever
ATR%(t) > median(ATR%) — exactly 50% of breakout bars by definition of the
median, made exact by Appendix F.1 fixing both quantities to the same
population.

A cap binding on half of all trades is not a guard rail; it is a second stop
rule. §4.3 requires it to be "inert under normal conditions... active only in
genuine volatility spikes". At high multipliers it would flatten the sweep
artificially, and the plateau test would read that flatness as stability. A3
measures FLOOR binding only, so nothing would catch it.

MEASURED, not argued. Cap binding at the top grid point, over training-fold
breakout bars, sampled across folds 1, 2, 3, 5, 9 and all three symbols:
  committed median form: 49.9% - 50.0%
  P95 form (this amendment): 5.0% - 5.1%
P95/median ratio runs 1.96 - 2.58.

CORRECTION. stop_max_pct = (m* + 2.5) x P95(ATR%) over breakout bars in the
training fold, per fold per symbol.

The cap then binds on 5% of breakout bars at the widest grid point and less at
every point below. This is a structural pass-rate criterion — the same pattern
already accepted for rvol_threshold: a round pre-committed number selected on
structure, never on performance.

§4.3's rejection of percentile anchoring ("introduces a new free number") is
WITHDRAWN. The alternative chosen in its place has a worse defect than the one
it avoided.

WHY THE ORIGINAL REJECTION WAS WRONG. §4.3 rejected percentile anchoring
because it "introduces a new free number". That reasoning does not survive: the
formula already contains m*+2.5, and 95 is no more free than 2.5 is. Both are
round pre-committed constants. The rejection traded an imagined cost for a real
defect — a cap that binds on half of all trades at the top of the searched
range, defeating its own stated purpose.

STATED TENSION. This is closer to ATR guarding ATR than the guard-rail
principle prefers. The principle's stated failure mode is "always inert or
always binding, never conditionally binding", and rsi_upper failed because
filter and signal moved together perfectly. Instantaneous ATR and a fold-level
ATR percentile do not move together, so the cap fires conditionally on genuine
within-fold spikes. The tension is recorded rather than argued away.

CAP BINDING RATE IS NOW A REPORTED DIAGNOSTIC at every grid point, alongside
floor binding. It carries no acceptance threshold — A3 remains a floor-binding
criterion only — but a cap binding materially above 5% at any grid point is a
finding about this derivation and must be reported.

---

## APPENDIX I — TWO CLARIFICATIONS BEFORE THE SWEEP

Made pre-lift. No performance figure seen. Neither part changes a rule,
threshold, or acceptance criterion. Both are reporting requirements.

I.1 — THE GATE'S MECHANISM MUST BE DISTINGUISHED FROM ITS EFFECT.

Report 11 establishes that the RVOL gate systematically selects higher-ATR
bars: gated floor binding runs 6-28pp below breakout floor binding in 297 of
297 cells. The trades the gate excludes are therefore disproportionately
floor-bound — wider stops relative to their own volatility, wider targets,
structurally less able to reach +2R inside the hold limit.

Consequently a gated-minus-ungated expectancy gap has two possible sources:
  (a) EDGE DETECTION — the gate distinguishes good breakouts from bad, which
      is the registered thesis; or
  (b) VOLATILITY SELECTION — the gate removes trades whose volatility is too
      low relative to the cost floor.

Both are real value. They have different implications: under (b) a direct
ATR% filter would do the same job more simply, and the session-normalised RVOL
apparatus is unnecessary machinery.

REQUIRED REPORTING: the gated-versus-ungated comparison is reported
STRATIFIED BY FLOOR BINDING — separately for trades where the floor bound and
trades where it did not. If the gate's advantage survives among non-floor-bound
trades, mechanism (a) is supported. If it vanishes, mechanism (b) is the
explanation.

This is DESCRIPTION. The 0.05R marginal-contribution threshold and the D5
drop rule are unchanged and continue to operate on the unstratified figure.
The stratification informs what is built next, not whether the gate passes.

I.2 — +/-25% SENSITIVITY PROBES MAY FALL OUTSIDE THE A3-ELIGIBLE SET.

§4.3 specifies the +/-25% kill condition "on the SELECTED value in absolute
multiplier terms per fold". Report 11 measures m* varying 2.2x across folds
(BTC 2.23 to 4.84), so a common offset maps to very different absolute
multipliers, and +/-25% spans very different offset ranges fold to fold.

Worked example: BTC fold 1, m* = 2.232. A selected offset of 1.0 is multiplier
3.232; -25% is 2.424, i.e. offset 0.19 — which FAILS A3 in that fold.

The probe would then evaluate a configuration that could never have been
selected, and a poor result there is not evidence about the strategy as
configured.

REQUIRED REPORTING: each +/-25% probe point is reported together with its A3
eligibility in that fold. Where a probe point is A3-ineligible, that is stated
explicitly and its expectancy is NOT read as evidence of fragility.

The kill condition itself is UNCHANGED: the edge must not vanish at +/-25%.
What is added is that an A3-ineligible probe point is labelled as such rather
than silently counted.

I.3 — RESIDUAL CAP BINDING ACCEPTED WITHOUT CHANGE.

Report 11 section 5 measures cap binding on the traded population at
5.04-10.18%, mean 8.40%, against Appendix H's 5% design intent on breakout
bars. Appendix H required this be reported prominently; it has been.

NO CHANGE IS MADE. Amendment 6's concern was a cap acting as a second stop
rule (50% binding) and flattening the sweep; 8.4% does not do that. The
plateau rule excludes the top grid point, so the figure at any selectable
multiplier is lower still. Correcting it would anchor the cap on the gated P95,
reintroducing the rvol_threshold dependency F.1 rejected for m*.

Recorded honestly: that dependency is a preference, not a proof. The residual
is accepted as the cheaper of two imperfect options.

---

## APPENDIX J — FLOOR-BINDING COMPOSITION APPLIES TO EVERY ARM COMPARISON

Made pre-lift. No performance figure seen. Reporting requirement only. No rule,
threshold, or acceptance criterion changes.

Appendix I.1 requires the gated-versus-ungated comparison to be stratified by
floor binding, because the RVOL gate systematically selects higher-ATR bars and
the excluded trades are disproportionately floor-bound.

That reasoning is not specific to the gated/ungated pair. It applies to ANY
expectancy comparison between arms whose floor-binding composition differs.

MEASURED (report 11a): at the first A3-passing offset, floor binding on the 70%
RVOL arm reaches or exceeds 20% in 17 of 27 fold-symbols (BTC 8/9, ETH 6/9,
SOL 3/9), and in 28 of 297 grid cells the 70% arm is at or above 20% while the
50% arm passes. The 30/50/70 monotonicity test of section 4.3 therefore compares
arms of differing floor-binding composition.

GENERAL REQUIREMENT. Any reported expectancy comparison between arms — gated
versus ungated, 30 versus 50 versus 70, or any D5 leave-one-out arm — must
carry:
  (a) the floor-binding rate of each arm, and
  (b) the comparison stratified into floor-bound and non-floor-bound trades,
      wherever both strata clear the evidence minimums.

Where a stratum falls below the evidence minimums, that is stated and the
stratified figure is not reported for it. The minimums do not move.

INTERPRETIVE CONSEQUENCE FOR THE MONOTONICITY TEST. Section 4.3 makes an
improvement from 70% to 50% to 30% the sharpest falsification test of the RVOL
gate. Where the arms differ materially in floor binding, an observed improvement
is consistent with EITHER the gate detecting edge OR the gate removing
structurally disadvantaged floor-bound trades. The stratified figures
distinguish them. The test itself is UNCHANGED: flat expectancy across all three
arms still means the gate is decorative.

Recorded before the number was inspected at the offsets where selection can
actually occur, so that the requirement is not conditioned on that measurement.

---

## APPENDIX K — AMENDMENT 7: "PASS ACCEPTANCE" DEFINED FOR A GRID POINT

Made pre-lift. No performance figure seen. This fills a gap; it does not change
a rule. No threshold is moved.

K.1 — THE GAP.
Section 4.3's plateau rule requires that "the adjacent grid points on both sides
also pass acceptance" and that a fold with no contiguous run of three passing
points produces no selection. "Pass acceptance" is never defined for a single
grid point.

It cannot mean A3: section 4.4 treats the two as separate ("a fold failing A3
produces no selection, exactly as a missing plateau does"), and A3 is fully
resolved at step 0. It must involve expectancy, since section 4.4 states
selection "happens by expectancy" and the kill condition frames the plateau as
being about where the edge survives.

Without a definition the sweep harness cannot identify a passing band. Supplying
one after expectancies are visible would be fitting the selection rule to the
results.

K.2 — THE DEFINITION.
A grid point PASSES ACCEPTANCE in a fold for a symbol when ALL of:

  (a) TRAINING-fold expectancy per trade, in R, net of costs, is GREATER THAN
      ZERO, measured on the gated arm at the 50% RVOL threshold;
  (b) the training-fold trade count for that symbol meets the pre-committed
      evidence minimum of 200 IS trades;
  (c) the grid point survives A3 (already established at step 0).

Selection is on TRAIN, evaluation is on TEST. That is what makes the procedure
walk-forward, and it is why (a) is a training-fold quantity.

Greater-than-zero is chosen because it is the only threshold that introduces no
free parameter. Any margin would be a number selected without justification.

ACKNOWLEDGED WEAKNESS. With sigma near 1.2R and roughly 250-400 training trades
per symbol-fold, the standard error on a fold's expectancy is about 0.07R. A
grid point whose true expectancy is near zero therefore passes or fails partly
by chance, so band EDGES are noisy. This is precisely why section 4.3 requires
three CONTIGUOUS passing points rather than accepting isolated ones. Note the
filtering is weaker than it looks: adjacent grid points share most of their
trades, so their expectancies are highly correlated and contiguity does not
suppress noise the way it would for independent points. Recorded rather than
argued away.

K.3 — EVEN-COUNT BAND TIE-BREAK.
Section 4.4 specifies "the centre of the widest contiguous passing band". A band
with an even number of points has no single centre. BTC's A3-eligible band is
four points wide (offsets 1.50 to 2.25), so this case is likely rather than
hypothetical.

RULE: where the band has an even number of points, take the HIGHER of the two
central offsets — the wider stop.

Justification: a wider stop strictly reduces floor binding, which is the only
structural criterion in this design carrying a threshold. The tie is therefore
broken on a pre-registered criterion rather than on taste. The cost is slightly
higher cap binding, which carries no threshold (Appendix I.3).

K.4 — SCOPE.
This appendix defines acceptance for a SINGLE GRID POINT during band
identification (step 3). It does not alter the 0.05R marginal-contribution
threshold, the D5 drop rule, the two-of-three rule, the top-5% removal, the
+/-25% sensitivity condition, or any kill condition. Those are unchanged and
operate as written.

---

## APPENDIX L — AMENDMENT 8: THE E6 TRIGGER GLOSS WAS WRONG

Made pre-lift. No performance figure seen. The RULE is unchanged. Its
explanatory gloss was arithmetically wrong and is corrected here.

THE RULE, UNCHANGED. If a 3-month test fold's standard error on expectancy
exceeds 0.20R, test folds extend to 6 months with a 6-month step, giving five
folds instead of nine.

THE DEFECT. Section 4.5 glosses this as tripping "at roughly sigma > 2.2-2.8R".
Sigma cannot reach 2.2R. r_multiple is mechanically bounded: target exits fill
at exactly +2R (maker limit at a target solved net of costs); time-stop and
max-hold exits are strictly below +2R, since a trade reaching the target would
have filled there; stop exits are -1R less the haircut, about -1.1R. The column
therefore lives in approximately [-1.1, +2.0].

NOTE ADDED POST-LIFT. The bound this appendix gave for r_multiple was itself
wrong, at both ends. It is recorded in Appendix M.1 and is not restated here.
The RULE below is unaffected: it was never derived from that bound, and no
threshold moves.

WHY THE RULE SURVIVES. SE = sigma / sqrt(n), so the trigger fires when
n < 25 * sigma^2 -- roughly 36 trades at sigma = 1.2R, and 49 at sigma = 1.4R.
The trigger is therefore reachable through a LOW TRADE COUNT rather than
through high dispersion, which is the risk actually worth guarding against, and
the count at which it fires sits just below the pre-committed 50-trade evidence
minimum per symbol per test fold.

The original gloss assumed n of 125-200 per symbol-fold, which is M9's estimate
for RVOL-only signals; the gated arm at a 50% pass rate roughly halves it, and
occupancy effects may reduce it further. Whether the counts hold is an empirical
question E6 answers.

CORRECTED READING. The E6 trigger is a TRADE-COUNT guard expressed in standard
error units, not a dispersion guard. Sigma is still measured and reported,
because it calibrates how precisely every downstream comparison can be read
(section 4.5's noise caveat), but it is the fold trade counts that determine
whether the trigger fires.

Evidence minimums do NOT move. This appendix moves no threshold.
---

## APPENDIX M — POST-LIFT RECORD: E6 FINDINGS AND THE HOLDOUT SEAL GAP

THIS APPENDIX IS POST-LIFT. The firewall lifted when E6 ran (report 12). Per
section 4.5 nothing pre-registered may be amended from here: once results are
seen, the honest response to a defect is to record it, not to repair the design
and carry on as though the repair had been pre-registered. This appendix
RECORDS defects and decisions. It alters no rule, no threshold, no acceptance
criterion and no kill condition. It is deliberately NOT numbered as an
amendment, and nothing in it may be read as one.

M.1 — APPENDIX L'S BOUND WAS WRONG. RECORDED, NOT FIXED.

Appendix L asserted that r_multiple lies in approximately [-1.1, +2.0]. Both
ends are wrong.

  UPPER END. Target exits do not fill at exactly +2R.
  costs.solve_price_for_net rounds the target AWAY from the position, so that a
  level is never claimed at a price which would deliver less than the solved
  net figure. A filled target therefore lands up to one tick above +2R.
  Measured in report 12: 1,421 of 20,010 trades exceed +2.0R, every one of them
  a target exit, the worst by 0.9990 of a tick.

  LOWER END. The realised minimum is -1.0006R, not -1.1R. position_size absorbs
  both fee legs and the stop haircut into the risk denominator, so a stop loses
  exactly the pre-committed risk_usd rather than that plus a haircut.

The engine behaves exactly as Points 1R and 3R specify. What was wrong is the
pre-registration's DESCRIPTION of the engine, not the engine.

check_r_bounds was NOT widened to make the check pass. It is retained verbatim
as the literal Appendix L check, and its failure stands as report 12's headline
finding. The hard stop that aborts a run was moved onto the bound the engine's
own arithmetic implies, +2R plus one tick of P&L per trade, and that bound
passes with zero breaches. Popoviciu's ceiling moves from 1.55R to 1.5503R.
Measured sigma is at most 0.8467R, so E6 findings 1 through 3 are untouched.

NOTHING DOWNSTREAM IS AFFECTED. Every rule that could plausibly have depended
on the range of r_multiple turns out not to:

  top-5% winner removal is a PERCENTILE, so it is invariant to the range;
  the +/-25% sensitivity condition operates on the MULTIPLIER, not on returns;
  the 0.05R marginal-contribution threshold is a DIFFERENCE between two
    expectancies, so a shift common to both cancels;
  the evidence minimums are COUNTS;
  the E6 trigger compares a measured sigma against a threshold that sigma
    never approached.

The defect lies in a diagnostic assertion, not in decision machinery. Nothing
is labelled exploratory.

M.2 — THE HOLDOUT SEAL HAS A GAP IN THE 1m PATH.

Report 12 section 10.2 records that 1m bars from 2025 were loaded, so that an
in-sample trade signalled in the closing hours of 2024-12-31 could resolve its
41-bar lifecycle instead of exiting on missing data. That matches
src/engine/run.py, which already loads max(year) + 1 for the same reason. ZERO
trades crossed the boundary, so no holdout bar influenced any figure in report
12. No contamination occurred.

The gap is structural rather than realised. Section 4.2's seal covers the
src/folds/ loaders and NOT the engine's 1m path, which predates it. E6 ran one
configuration per fold-symbol. The sweep runs eleven multipliers across three
RVOL arms, and wider stops imply longer holds, so boundary crossings become
materially more likely there than they were here.

REQUIRED BEFORE THE SWEEP. The 1m loading path must refuse 2025-01-01 and later
by default, on the same authorised=False pattern already used in src/folds/,
with a mutation test proving that it refuses. A seal never shown to refuse is
not a seal.

M.3 — BOUNDARY-CROSSING TRADES ARE EXCLUDED. POST-LIFT DECISION.

Section 4.2 does not say what happens to an in-sample trade whose resolution
would require data at or after 2025-01-01.

RULE. Such trades are EXCLUDED from in-sample analysis, and the excluded count
is reported per fold per symbol.

Reason. Exclusion is the only option that spends no holdout data. Truncating at
the boundary would require inventing an exit price, which is a fabricated
outcome. Resolving with holdout bars would contaminate an in-sample result
inside the very module that selects the candidate, which is the one place
contamination cannot be tolerated.

THIS DECISION IS POST-LIFT and is labelled as such. It affected zero trades in
E6. It moves no threshold and changes no acceptance criterion.

M.4 — THE D5 POOLED POPULATION MUST BE NAMED.

Report 12 gives a pooled D5 standard error of 0.0055R on n = 20,010. If that
population spans train and test across all nine folds, the figure is not a
count of independent trades: adjacent training windows overlap by 50%, so a
trade in the middle of the span is counted two or three times. That inflates n
and understates SE by roughly a factor of 1.6.

The conclusion survives. A corrected SE near 0.0087R against the 0.05R
threshold still gives a ratio near 0.17, so the pooled D5 figure remains
readable, which is what section 4.4's pooling commitment requires of it.

REQUIRED. The sweep report must state which population every pooled figure is
computed over, and D5 attribution runs on TEST folds only, which do not
overlap. This is a clarification of section 4.4's existing pooling rule, not a
change to it.
