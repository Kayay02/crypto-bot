# POINT 4 — CLOSING RECORD AND HANDOFF

**Status:** CLOSED. Pre-committed kill conditions fired at step 3 of the
section 4.4 sequence. No candidate reached the holdout.

**Verdict:** The momentum/trend-continuation breakout strategy as specified
through Points 1, 1R, 2, 3, 3R does not have a demonstrable edge on 15m
BTCUSDT / ETHUSDT / SOLUSDT Bitget perpetuals at $2,000 with $20 fixed risk
after costs.

**The holdout is UNSPENT.** 2025-01-01 through 2026-07-26 has never been read.
Not one bar. This was the scarcest resource in the project and the entire
apparatus — the performance firewall, the frozen pre-registration, the thirteen
appendices, the two-layer seal — existed to protect it. A strategy killed at
step 3 leaves it fully available. A strategy passed by multiplicity would have
burned it on a false positive nobody could have detected.

---

## 1. WHAT KILLED IT

### 1.1 The terminal condition

**TWO-OF-THREE FAILED OUTRIGHT.**

Section 4.4: *"a symbol qualifies only if it passes on its own AND at least one
other symbol shows the same direction of edge"*, where "same direction of edge"
means gated expectancy exceeding ungated by at least 0.05R.

One symbol of three shows it. A rule requiring two cannot be satisfied by one.
No symbol qualifies. No candidate exists. The procedure terminates before the
holdout by its own pre-registered logic.

### 1.2 The full kill-condition table (report 15)

| Kill condition | BTC | ETH | SOL |
|---|---|---|---|
| (a) OOS expectancy <= 0 after costs | **FIRES** | **FIRES** | does not fire* |
| (b) gated vs ungated < 0.05R (gate decorative) | **FIRES** | **FIRES** | does not fire* |
| (c) ungated outperforms gated (thesis backwards) | clear | clear | clear |
| (d) two-of-three | **FAIL** | **FAIL** | **FAIL** |

\* SOL's two non-firing verdicts rest entirely on a single offset, m\*+0.50:
+0.0229R against a standard error of 0.0319, pooling 4 of 9 test folds, at an
offset no SOL fold selected. Under the stricter "selected offset" reading, kill
(a) fires for all three symbols. Two-of-three fails on either reading, so
nothing turns on the ambiguity — but see section 4.2, it nearly did.

### 1.3 The number that settles it

**160 of 198 A3-eligible grid points have NEGATIVE TRAINING expectancy.**

Only 38 of 198 pass Appendix K.2 acceptance, and clause (b) never binds — the
smallest gated_50 training fold holds 364 trades against a 200 minimum — so
acceptance is decided purely by expectancy > 0.

If training expectancy were centred at zero, roughly half the cells would pass.
19% passing means the distribution sits clearly below zero.

**The strategy loses money on the folds where its own parameters were chosen.**

This is not overfitting failing to generalise. It is failure to fit in the first
place, which is a cleaner and more informative result. Report 14's test-fold
tables could not distinguish the two; step 3 could, which is why step 3 was not
a formality.

ETH is the sharpest case: **zero of 70 A3-eligible grid points** has positive
training expectancy, across all nine folds.

### 1.4 Selections produced

6 of 27 fold-symbols produced a selection under the section 4.3 plateau rule:

| symbol | folds with a selection | selected offsets |
|---|---|---|
| BTCUSDT | 4 of 9 | m\*+1.75, m\*+1.50, m\*+1.50, m\*+1.50 |
| SOLUSDT | 2 of 9 | m\*+2.00, m\*+2.00 |
| ETHUSDT | **0 of 9** | none |

Section 4.4 already calls coverage below 7 of 9 a documented instability. At 4,
2 and 0 the collapse at step 4 had nothing stable to intersect — but that is
secondary. Two-of-three had already failed.

---

## 2. WHY IT FAILED — THE MECHANISM

Three findings, all pre-registered as questions before any number existed. These
are the substance of what Point 4 bought, and they should shape whatever comes
next.

### 2.1 The time-stop checkpoint DESTROYS value, and D6 is answered against it

Section 4.5 asked whether the bar-21 checkpoint CREATES a holding-time mode or
CATCHES one, answerable only on stop and target exits with 21 and 41 as
reference lines.

**It creates the mode.** Stop and target holding times run smoothly through bar
21 with no build-up against it. Bar 21 accounts for 0.5–2.2% of those exits.

Meanwhile `time_stop` is the DOMINANT exit at **45–83% of trades, rising with
offset**. And `minus_time_stop` beats the full model in essentially every cell
(BTC offset 2.25: -0.0090 vs -0.0258; SOL offset 2.0: +0.0030 vs -0.0148).

Removing a component improves expectancy. That is worse than the tie section 4.4
already resolves toward removal.

**The mechanism:** wider stops make the 1:2 structure take longer to resolve, so
more trades hit the horizon before either level is reached. The stop width and
the holding horizon are structurally mismatched, and A3 forced the sweep toward
exactly the wide offsets where the mismatch is worst.

This is NOT an exit-structure bug to patch. It is evidence that a 1:2 target on
a 15m breakout under a ~10-hour cap is the wrong SHAPE. Either the target is too
far for the horizon or the horizon is too short for the target, and changing one
addresses half of a relationship that may be wrong on both sides.

### 2.2 The RVOL gate does VOLATILITY SELECTION, not edge detection

Appendix I.1 pre-registered the test: stratify gated-vs-ungated by floor
binding. If the advantage survives among non-floor-bound trades, mechanism (a)
edge detection is supported. If it vanishes, mechanism (b) volatility selection
is the explanation.

**It vanishes.** The advantage lives in the floor-bound stratum, frequently
exceeding 0.05R there, and collapses among non-floor-bound trades to about
+0.02R on BTC and SOL, and NEGATIVE at five of nine offsets on ETH.

Against the 0.05R standard used everywhere else in this design, +0.02R has
vanished.

Two things worth keeping:

- The gate DOES show **monotonic improvement in the pre-registered direction**
  on all three symbols. At offset 1.5, gated_30 / gated_50 / gated_70:
  BTC -0.0249 / -0.0330 / -0.0462; ETH -0.0532 / -0.0595 / -0.0696;
  SOL -0.0200 / -0.0238 / -0.0420. Tighter gate, better expectancy, every time.
  The direction is real. The magnitude is not enough.
- **A direct ATR% filter would do the same job.** The session-normalised,
  quote-denominated slot-baseline apparatus that Point 1R's structural pass
  spent its effort validating is not earning its complexity. That is a design
  lesson, not a defect.

### 2.3 The EMA trend filter WORKS

`minus_ema` is worse than the full model in most cells. The thesis-critical
component does its job. Whatever comes next should keep a trend filter.

### 2.4 Costs dominate

The derived floor is 1.020% (BTC/ETH) and 1.320% (SOL). Expectancy sits at
-0.03R to -0.08R. The round trip consumes whatever small directional signal
exists. At $2,000 with taker entry and taker stop, the cost structure is the
binding economic constraint, not a detail.

---

## 3. WHAT POINT 4 PROVED ABOUT THE PROCESS

Recorded because it is the transferable part.

### 3.1 The firewall did its job

No performance figure was seen until 4.1–4.5 were written, agreed and committed
to git with a hash. Every threshold, every acceptance rule, every kill condition
was written blind. When the numbers arrived they could only confirm or refute —
they could not reshape the test.

The proof is that the verdict is uncomfortable and stands anyway.

### 3.2 A3 before the sweep was the right call

Appendix F.2 moved the A3 floor-binding check ahead of the lift on the grounds
that binding rates require no trade outcome. That bought the tradability verdict
— all three symbols tradable, 9/9 folds — with the firewall still intact, and it
refuted the pre-registered "weakest link" expectation without spending anything.

### 3.3 The pre-registered expectation was WRONG, and that is recorded

Section 4.3's weakest-link section predicted a BTC tradability finding as "the
most likely single outcome of Point 4". It did not occur in any fold. Two
compounding errors: the 65–81% binding figure was measured at a void multiplier
(~1.5, far below m\*), and A3 evaluates the gated population where floor binding
runs 6–28pp below breakout bars.

A failed prediction recorded as failed is worth more than one quietly dropped.

### 3.4 The recurring error class — SEVEN instances

Every significant defect in Point 4 was the same error: **a numerical criterion
written from a mental model of a quantity rather than from its implementation or
its achievable range.**

| # | Defect | Appendix |
|---|---|---|
| 1 | m\* cut points written in offset units, not levels | A |
| 2 | `ema_fraction` "full precision" trigger on a discrete quantity | — |
| 3 | `stop_max_pct` anchored on the median, binding 50% at the top grid point | H |
| 4 | m\* population unspecified (all bars vs breakout bars) | F.1 |
| 5 | r_multiple bounded at [-1.1, +2.0] against an engine that rounds away | M.1 |
| 6 | boundary crossings counted on the gated table, not the ungated universe | M.2 |
| 7 | kill conditions carrying no aggregation rule over the offset axis | — |

**The mitigation that works:** derive every bound and threshold from the
variable's actual construction and measured range, never from its name or its
description. Where a quantity has a population, name the population in the same
sentence as the number.

### 3.5 Guards must be tested against the mutation they exist to catch

Seven vacuous guards were found or prevented across this project. The ones that
held were the ones with planted mutations: the regime causality shift, the
empty-1m-array ordering test, the report-12 numeric scanner that re-derives all
384 forbidden quantities, the population-label validator with six planted
mutations, and the step-3 period guard that hard-codes "train" rather than
reading its own selector.

**A guard that cannot detect its own target mutation proves nothing.**

### 3.6 Terminal heredocs corrupt long text

Appendices L and M were destroyed by paste races between the terminal echo and
the input buffer. All prose longer than a few lines must be written by Claude
Code directly to disk, never echoed through a shell heredoc, never pasted into
an open editor buffer.

---

## 4. OPEN ITEMS AND SPECIFICATION GAPS

### 4.1 `minus_max_hold` is unconstructible

Section 4.5 specifies it as one of five decomposition arms. `max_hold_bars` is
derived as 2 x donchian_period and explicitly not independently sweepable.
Removing the cap requires either changing the breakout rule — not a leave-one-out
— or inventing a replacement horizon post-lift. Section 4.4 never drops max-hold
anyway (guard rail, "measured and reported, NEVER dropped"), so nothing depended
on it. A specified arm that could not exist and fed no decision.

### 4.2 Kill conditions carry no aggregation rule over the OFFSET axis

Section 4.4 requires every pre-committed threshold to carry its aggregation rule
and records that "ER1's omission of one nearly decided B3 by accident". The
offset dimension was written without one. SOL's entire result turns on which
reading applies. Two-of-three failed on both, so nothing turned on it — but it
nearly did, in the same way and for the same reason as the earlier near-miss.

### 4.3 Section 4.5's "identical trade universe by construction" is false

True for the RVOL arms, which are cuts of one ungated simulation.
`minus_time_stop` is set-equal despite re-simulation. `minus_ema` is a strict
SUPERSET — removing a signal-generation filter necessarily admits more trades.
Inherent to a leave-one-out on a filter, not a defect, but the claim as written
would mislead.

### 4.4 Carried forward, unresolved

- Funding costs across a 40-bar hold, UNMODELLED. Point 6.
- Bitget kline taker-buy volume: documentation check only. Would give true
  aggressor-flow imbalance, stronger than anything derivable from OHLCV.
  Re-pulling reopens Point 2.
- Day-of-week separation in the RVOL slot baseline. Default: ignore.
- Percent-of-equity sizing. Point 7.

---

## 5. THE CONTAMINATION LEDGER, UPDATED

| Window | Status after Point 4 |
|---|---|
| 2022-01 to 2022-03 | Warm-up only. Never traded. Used for tercile fit (Appendix B). |
| 2022-04 to 2024-12 | **SUBSTANTIALLY SPENT.** Structural diagnostics (Points 1R, 2, 3R), the four structural rulings, the full nine-fold walk-forward, the 198-point sweep, and every finding in section 2 above. |
| 2025-01 to 2026-07 | **ENTIRELY UNTOUCHED.** Not one bar read. Sealed at the loader and at the per-trade requirement check, both mutation-tested. |

**Consequence for the next hypothesis:** in-sample evidence from 2022–24 is now
weak evidence. A new design justified by section 2's findings is partly fitted to
that window even though no parameter was tuned on returns. The holdout carries
correspondingly more weight, and Point 6 paper trading on genuinely forward data
matters more than it did here.

---

## 6. ARTIFACTS AND PROVENANCE

| Item | Location | Commit |
|---|---|---|
| Pre-registration, Appendices A–M | `docs/handoff/08_point_4_pre_registration.md` | `cd1fed8` |
| Regime measurement | `src/regime/`, reports 09, 09a | `20a6226` |
| Fold architecture | `src/folds/`, report 10, `folds.json` | `af9d314`, `6d482fb` |
| Grid and A3 pre-screen | `src/sweep/grid.py`, `prescreen.py`, report 11, `grid.json` | `45d4bcb`, `7f93257` |
| E6 dispersion (THE LIFT) | `src/analysis/`, report 12 | `a30b97b` |
| 1m seal and boundary exclusion | report 13 | `fc4cfc9` |
| The sweep | `src/sweep/sweep.py`, report 14, `sweep.json` | `bdde2a4` |
| Band selection and kill verdict | `src/sweep/bands.py`, report 15, `bands.json` | pending |

Test suite: 482 passing.

E6 findings, which stand: sigma 0.7242R (BTC), 0.7666R (ETH), 0.8467R (SOL)
against a 1.2R design assumption. The fold-extension trigger did NOT fire —
0 of 27 cells, largest test-fold SE 0.0787R against 0.20R. The nine-fold
architecture stood. No evidence-minimum shortfall in any of 27 fold-symbol or
108 direction cells.

---

## 7. NEXT STEPS — IN ORDER

### Step 1. Commit the step 3 work

Including `bands.json`. Step 4 may not revisit step 3, so a committed copy
proves which numbers the verdict rested on. The `.gitignore` exception follows
the existing `grid.json` / `sweep.json` pattern.

### Step 2. Commit this document

To `docs/handoff/16_point_4_closing.md`.

### Step 3. DO NOT run steps 4 through 8

Two-of-three has failed. No candidate can reach the holdout regardless of what
the collapse, D5, or the robustness gates produce. Continuing would be motions
on a procedure whose terminal condition is met, and it would look like searching
for a configuration that passes after the kill fired.

**The kill conditions are the goalposts.**

### Step 4. DO NOT patch this strategy

Specifically: do not drop the time stop and re-run, do not widen the target, do
not swap RVOL for an ATR filter and re-test.

Every one of those is a configuration chosen AFTER seeing which direction the
money went. Section 4.4 is explicit: no component may be added as an attribution
arm after the firewall lifts, and D5 is single-pass. A variant selected from
report 14's tables carries no evidential weight, and it would look exactly like
a discovery.

Anything run on this strategy from here is EXPLORATORY and cannot be presented
as validation.

### Step 5. Open Point 1 again — a NEW hypothesis

Not a repair. See section 8.

---

## 8. HOW TO OPEN POINT 1 AGAIN

### 8.1 Where

**A fresh chat.** Upload this document as the handoff. Open with:

> "Let's start with Point 1 again — a new strategy hypothesis, informed by the
> Point 4 closing record."

The standing project description and working rules carry over unchanged: one
point at a time, decisions before code, no code in chat, Claude Code prompts for
anything built, friction over compliance.

### 8.2 What carries forward

**The infrastructure, all of it.** This is the largest asset the project has and
it cost most of the work:

- Two-layer engine, 482 tests, verified cost-inclusive sizing, targets solved
  net of costs, trade-through fill semantics, provenance counters
- Clean 15m and 1m Bitget data, 2022-01 to 2026-07, quality-verified
- Nine-fold walk-forward architecture with proven 45-day warm-up sufficiency
- The regime characterisation module and its frozen tercile artifact
- The holdout seal, two-layer and mutation-tested
- The population-label contract and its validator
- The whole pre-registration discipline: firewall, frozen design, git hash as
  proof, amendments as numbered appendices

A new hypothesis on the same instruments and timeframe reuses nearly all of it.

**The evidence in section 2.** Time-based exits dominate. The bar-21 checkpoint
creates a mode rather than catching one. RVOL contributes volatility selection
reproducible by a simpler filter. The EMA trend filter works. Costs dominate at
this size.

### 8.3 What must NOT carry forward

- The 1:2 fixed target with a 21-bar checkpoint and 41-bar cap. This exact shape
  is what failed.
- The assumption that session-normalised RVOL is worth its complexity.
- Any parameter value from Point 4. `stop_atr_mult` selections, rvol thresholds
  and cap values were selected under a design now closed.
- The belief that a trend-continuation breakout on 15m crypto is the obvious
  candidate. It was tested. It did not work.

### 8.4 The three questions Point 1 must answer first

Before any indicator discussion.

**(1) Is the target-to-horizon relationship the thesis, or a parameter?**

Point 4's central finding is that 45–83% of trades exit on time rather than at a
level. The 1:2 target and the ~10-hour cap were chosen separately and turned out
to be mismatched. A new hypothesis should derive one from the other — a target
reachable within the horizon the edge actually persists over — rather than
picking both and hoping.

**(2) Can the cost structure be improved, or is $2,000 on 15m simply too small?**

The floor at 1.020%/1.320% exists because entry and stop are both taker. Maker
entry, a longer timeframe with proportionally larger moves, or a different exit
mechanism would each change the arithmetic. This should be settled with fee math
BEFORE any indicator is chosen. If the honest answer is that the edge required to
clear costs at this size is implausibly large, that is worth knowing in week one
rather than at step 3 of Point 4.

**(3) What is the actual thesis?**

Point 1 originally asserted trend continuation after a volume-confirmed
breakout. That has now been tested and did not hold at this timeframe and cost
structure. The next thesis must be genuinely different — mean reversion,
liquidity provision, a different horizon, a different instrument class — not the
same claim with adjusted parameters.

The 1R.5 "reversal breakout" hypothesis remains UNEXERCISED, NOT REFUTED, and is
a legitimate candidate.

### 8.5 The discipline that must be re-established

**The firewall is re-armed from the first message of the new Point 1.** No
performance figure from the new hypothesis is inspected until its own
pre-registration is written, agreed and committed with a hash.

The old firewall's lift applies only to the closed strategy. A new hypothesis
gets a new firewall, and the holdout stays sealed until that hypothesis has its
own step 9.

**The holdout budget is unchanged: one candidate, one look, whole window, no
candidate two.**

---

## 9. THE HONEST SUMMARY

The strategy does not work. It loses money on 160 of 198 grid points in the
training folds where its own parameters were chosen, on two of three symbols it
fails the out-of-sample expectancy condition outright, and the volume gate that
was central to the thesis turns out to be doing volatility selection that a
one-line ATR filter would reproduce.

The process worked exactly as designed. The kill conditions were written before
any number existed, they fired, and the holdout was never spent.

**A validation protocol does not create edge. It prevents belief in edge that is
not there.** That was written into section 4.3 before the firewall lifted,
precisely so it would be on the record when this moment arrived.

Point 4 returned no edge. That is the protocol working correctly.
