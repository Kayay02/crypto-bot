# Prompt 05 — Point 1R Handoff (saved verbatim)

Goal
Write the Point 1R handoff document into the repo as a versioned artifact, capturing every amendment agreed during the Point 1R design pass. This is a documentation-only task: no code is written, no config values are changed, no backtests are run.

Context
This is a systematic algorithmic trading bot for Bitget USDT-M perpetual futures, trading BTC, ETH and SOL on 15-minute candles. Account ~$2,000, risk $20/trade enforced after fees and slippage.

Points 1 (strategy), 2 (data) and 3 (backtesting engine) are closed. Engine is a two-layer custom design at commit 106cb42 with 88 tests passing.

Point 1R was a structured amendment pass on the strategy design, opened after engine diagnostics revealed four mechanical defects. It is now closed across five sub-points (1R.1 through 1R.5). NO PROFIT OR LOSS FIGURES WERE INSPECTED AT ANY POINT — a standing "performance firewall" rule forbids it until the start of Point 4, and every amendment below was justified from binding rates, pass rates, parameter arithmetic or logical entailments only.

Repo conventions already in use:
- Handoff documents -> docs/handoff/NN_name.md
- Claude Code prompts -> docs/prompts/NN_name.md
- Claude Code reports -> reports/NN_name.md
The previous handoff is docs/handoff/04_*.md (session handoff #04).

Files
Create:
- docs/handoff/05_point_1r.md   (the handoff document — main deliverable)
- docs/prompts/05_point_1r_handoff.md   (this prompt, saved verbatim)
- reports/05_point_1r_handoff.md   (short completion report)

Do not create or modify anything else. In particular do not touch any file under src/, tests/, config/ or data/.

Requirements
Write docs/handoff/05_point_1r.md with the following sections and content. Reproduce the substance faithfully; you may improve formatting and clarity but do not add, remove or reinterpret any decision.

SECTION 1 — STATUS
Points 1, 2, 3 closed. Point 1R closed (all five sub-points). Next open point: Point 4 (validation design pre-registration). The performance firewall lifts at the start of Point 4, and only after the validation design is written down and pre-registered.

SECTION 2 — THE FOUR MECHANICAL FINDINGS THAT CAUSED 1R
1. Cooldown is a logical no-op. A long entry requires close above the Donchian-20 upper band, which IS a new 20-bar high — the condition that clears the cooldown is entailed by the entry condition that triggers it. It can never bind.
2. The ATR stop is overridden by its own floor. The 1.0% floor binds on 64.8% of 2022 trades and 81.1% of 2023 trades; BTC 2023 = 99.3%. The 3.5% cap essentially never binds. Knock-on: BTC/ETH effectively run a fixed-percent stop while SOL (floor binds 40-59%) runs a volatility-scaled one — they are not running the same strategy, which weakens both the shared-parameter justification and the two-of-three rule.
3. The volume gate is weak. RVOL >= 1.5 admits 65.9% (2022) and 68.8% (2023) of breakout bars. Effect on the target-vs-stop ratio was +0.6pp in 2022 and -0.9pp in 2023 — the sign flips.
4. The most common outcome is neither target nor stop. Time-stop exits were 26.5% (2022) and 43.3% (2023); target exits 21.3% / 14.9%. The original "36% win rate at 1:2 to break even" framing assumed binary resolution and does not describe this population.

SECTION 3 — 1R.1 STOP GEOMETRY (six amendments)
A1. The stop's job is declared as NOISE SURVIVAL, volatility-scaled. stop_atr_mult is a first-class parameter to be calibrated at 15m, not inherited. The value 1.5 is void as a default — it is an unset placeholder with no privileged status in any sweep. The stop does not measure invalidation, cost or leverage.
A2. stop_min_pct becomes DERIVED, not chosen:
    stop_min_pct = max( N_cost * c_roundtrip , R / (E * L_max) )
    where c_roundtrip is the round-trip cost on the stop path (taker in, taker out = 0.12% before slippage, plus the engine's slippage haircut both sides); N_cost is the cost-dominance ratio, proposed at 6 (costs may consume at most ~1/6 of the risk distance) and is the one chosen number remaining; and the leverage term is $20 / ($2,000 * 3.0) = 0.333%.
    The cost term dominates the leverage term by roughly 3x, so the floor is fundamentally a cost guard rail. The leverage term stays in the formula so that any downward revision of N_cost does not silently make it load-bearing.
A3. Shared parameters across symbols are RETAINED. No per-symbol parameters. The BTC-vs-SOL divergence is an artifact of the floor binding at different rates, not a genuine mechanism difference; recalibrating stop_atr_mult upward so the ATR term clears the floor dissolves it at source without tripling the fitting surface.
    Pre-registered acceptance check for Point 4: report floor binding rate per symbol per year. If the floor binds on more than 20% of trades for any symbol, recalibration has failed — reopen 1R.1 rather than proceed.
    Pre-registered interpretation, committed before results are visible: if BTC's floor binding rate cannot be brought under 20% at any multiplier that still produces a plausible 2R target, the honest reading is that BTC 15m breakout noise is structurally narrower than our cost floor — i.e. BTC at this timeframe is not tradable at $2,000 with these fees. That is a finding about tradability, not a kill condition, and it does not modify the pre-committed kill conditions.
A4. STRUCTURE_STOP registered as a LABELLED VARIANT: stop anchored to breakout structure (breakout-bar low, or the crossed Donchian level, minus a buffer), variable-width, sized accordingly. Not baseline. Must not be silently promoted.
A5. The cap is re-derived as a target-plausibility and exchange-minimum guard rail. It is NOT loss limitation — with fixed $20 risk a wider stop means a smaller position, so dollar risk is constant by construction. Its jobs are (i) target plausibility, since at some stop width a 2R target stops being a thing that happens within the hold horizon, and (ii) rejecting positions that fall below Bitget's minimum order quantity, explicitly rather than by silent rounding. Cap binding rate joins the reported provenance counters.
A6. The sweep is defined PROCEDURALLY. Point 4 sweeps stop_atr_mult and N_cost on a 2D grid. The multiplier range is anchored at m*, the multiplier at which median ATR% crosses the derived floor for that symbol, and swept from 0.4 * m* to 3.0 * m*. CRITICAL: m* is computed PER WALK-FORWARD TRAINING FOLD, never globally and never over the full window — a globally computed anchor would read the 2025-26 holdout and leak it.
A7. New provenance counters. Per trade: stop_binding_mechanism in {atr, floor, cap}. Per trade in portfolio mode: size_binding_mechanism in {risk_rule, leverage_cap, min_qty}. The second closes a Point 3 known gap (max_leverage=3.0 was unmeasured) and detects divergence between signal mode and portfolio mode.

GUARD RAIL PRINCIPLE (established here, applied throughout): a guard rail must be denominated in a DIFFERENT UNIT from the mechanism it guards. Percent-of-price guarding an ATR-scaled stop is coherent. ATR guarding ATR is a logical no-op — it is either always inert or always binding, never conditionally binding. This principle killed a proposed volatility-relative floor in 1R.1 and killed rsi_upper in 1R.5.

SECTION 4 — 1R.2 VOLUME GATE (six amendments)
B0. Contamination ledger updated. Add: "Diurnal volume profile (volume levels by time-of-day, not returns) was observed across the full 2022-2026 window during Point 2. All 1R.2 design justification is restricted to 2022-23. The holdout's diurnal profile is confirming evidence at Point 4, never motivating evidence in 1R." The phrase "structural in every year" is struck from the 1R reasoning chain.
B1. Session-normalised RVOL baseline replaces the flat 20-bar trailing mean. Justification: 20 bars at 15m is a 5-hour window, short enough to sit inside one phase of the diurnal cycle, so the denominator tracks the SLOPE of that cycle — inflating RVOL during session ramp-up and suppressing it during ramp-down. The gate partly measures what time it is.
    - Slot = position within the UTC day; 96 slots at 15m.
    - Baseline(T) = MEDIAN of the same slot over the trailing baseline_days COMPLETED PRIOR days. Strictly prior; bar T's own day contributes nothing. Causality-guarded in Layer A.
    - Median not mean: a single event bar in the baseline would inflate a mean and suppress RVOL for that slot every day for the whole window.
    - baseline_days is a new unset parameter. Warm-up of baseline_days before the first valid signal.
    - Day-of-week separation: registered OPEN QUESTION. Default is to IGNORE it (separating weekday/weekend fragments the baseline into thin cells). Recorded as a choice, revisitable at Point 4 with evidence.
B2. Denomination: quote_volume by default for both numerator and denominator (they must always use the same field). Justification is bias from price drift across the baseline window, not cross-regime comparability — RVOL is always computed locally, so no cross-regime comparison occurs. Base and quote denominations are biased in OPPOSITE directions and the bias acts hardest during trends, which is where this strategy takes most of its trades.
    Pre-registered test at Point 4: compare trailing-window stability of quote_volume vs volume per symbol per year. Whichever is more stable is the correct denominator. If base wins, switch.
B3. vwap_position added as an orthogonal volume LOCATION condition:
        bar_vwap      = quote_volume / volume
        vwap_position = (bar_vwap - low) / (high - low)     in [0, 1]
        long:  require vwap_position >= threshold
        short: require (1 - vwap_position) >= threshold
    Justification: any MAGNITUDE measure of volume is near-entailed by the entry condition, because breakout bars are intrinsically high-volume — selectivity is spent before the gate applies. Location is orthogonal to the breakout condition, so its selectivity is real. Uses only stored fields (quote_volume, volume, high, low); no open_synth, no 1m data, no new source.
    Degenerate bars (high == low): gate FAILS. Must be an explicit branch, not a division-by-zero producing NaN.
    Threshold unset, calibrated at Point 4.
    TWO MANDATORY PRE-CHECKS, either of which kills this amendment:
      (1) Validity — bar_vwap must land inside [low, high] on every bar, every symbol. If not, Bitget's quote_volume is unreliable and both B3 and B2 die.
      (2) Non-redundancy — correlation between vwap_position and close_position = (close - low)/(high - low) on breakout bars. If |rho| is very high, vwap_position is a re-labelled price-action term and fails its purpose. Also check dispersion: if breakout-bar vwap_position clusters tightly there is nothing to discriminate with.
B4. The gate is CONJUNCTIVE: RVOL_pass AND vwap_pass. Both binary — a continuous score is rejected because the kill condition "gated vs ungated expectancy differ by <0.05R" requires a clean A/B and a continuous score has no ungated arm.
    Four arms, all filters of the same signal-mode trade table (identical universe by construction): ungated / RVOL only / vwap only / both.
    Sample-size risk: two conjunctive conditions multiply rejection (~66% x ~50% = ~33% of breakout bars), colliding with the evidence minimum of 200 IS / 50 OOS / 30 per direction per symbol. PRE-COMMITTED RESOLUTION ORDER if minimums cannot be met: loosen thresholds -> extend the in-sample window -> drop to a single condition. THE EVIDENCE MINIMUM IS NOT ON THAT LIST and does not move. Trade counts per arm per symbol are reported BEFORE thresholds are fixed.
B5. Pre-registered diagnostics for Point 4:
    - Gate pass rate on breakout bars vs on ALL bars, per symbol per year. This ratio is the definition of selectivity and the all-bars denominator has never been measured. It distinguishes "RVOL is genuinely selective but pre-spent by conditioning" from "RVOL >= 1.5 was never selective".
    - Pass rate by hour of day, flat baseline vs session-normalised.
    - Gate effect measured on TIME-STOP RATE and holding-time distribution, not only target:stop. A participation gate's claimed failure mode is "price goes nowhere", so the time-stop rate has the most power to detect it. The +0.6pp / -0.9pp figure was measured on a minority subset of the population.
    - vwap_position distribution, validity check, and correlation with close_position.
    - Quote-vs-base stability comparison.

SECTION 5 — 1R.3 TIME STOP (eight amendments)
D1. Purpose declared: INVALIDATION BY ABSENCE (thesis decay), not capital recycling. Justification: signal mode has no position limits, so opportunity cost there is identically zero; an opportunity-cost rule sitting in the edge-measurement instrument would contaminate it. Thesis decay is a property of the trade population and belongs in both modes. NO_TIME_STOP registered as a counterfactual arm under the drop rule.
D2. Ambiguity resolved: STATE CHECK at the checkpoint bar's close ("is the trade at +threshold now"), NOT a latch ("did it ever touch"). Reasons: a wick to +1R that immediately retraces is the same liquidity-vacuum failure mode vwap_position was added to catch; keeps the rule in Layer A's 15m world with no 1m dependency; carries no latch state. Accepted cost: a trade that ran to +1.8R and retraced to +0.9R gets cut, in profit.
D3. Both bar counts DERIVED from the Donchian period:
        time_stop_bars = tau * donchian_period      tau default 1.0  -> 20 bars
        max_hold_bars  = 2 * donchian_period                         -> 40 bars
    Justification: at bar 20 post-entry, every bar in the Donchian lookback is post-breakout — the 20-bar high that was broken has rolled out of the window, so the reference frame that generated the signal no longer exists. The previous values 16 and 48 are VOID. Only tau remains sweepable, over a narrow band around 1.0.
D4. The pace factor phi is made explicit:
        phi = (threshold_R / target_R) / (checkpoint_bars / max_hold_bars)
    The original geometry gave phi = (1/2) / (16/48) = 1.5 — demanding 50% of the price journey in 33% of the time budget. Nobody chose this; it fell out of two unrelated placeholders. Default is now phi = 1.0 (linear pace). With D3's derived counts and phi = 1.0 the checkpoint threshold solves to +1R — the original value, now for a reason, and now an OUTPUT rather than an input. Front-loading (phi > 1) is a real momentum-decay claim and must be discovered by the sweep, not assumed.
    Net effect: three free parameters (time_stop_bars, threshold R, max_hold_bars) become two derived quantities and one dimensionless parameter.
D5. DROP RULES CONSTRAINED TO A SINGLE PASS. The "0.05R or it's decorative" rule now applies to four components (RVOL, vwap_position, the combined gate, the time stop). Individually sound; together they form a stepwise model-selection procedure, which is overfitting. Noise estimate: at ~1.2R per-trade dispersion and a ~68-trade complement out of 200, the standard error of the paired difference is roughly 0.05R — so the threshold is about a ONE-STANDARD-ERROR test.
    The kill condition itself is pre-committed and does NOT change. The PROCEDURE is constrained:
    - Leave-one-out against the full model, SINGLE PASS. Every component measured against the same full specification.
    - Drop all failures SIMULTANEOUSLY. No iterative re-testing after each removal.
    - ONE confirmation run of the reduced model. If it fails the kill conditions, the strategy dies. No second round.
    - Drop decisions POOLED across symbols and folds, not per-symbol-per-fold.
    - TIES GO TO REMOVAL. Where a result sits inside the noise band, drop the component.
D6. Pre-registered diagnostics:
    - Time-stop rate split by stop_binding_mechanism (floor vs ATR) within the same period — the discriminator for whether the 26.5% -> 43.3% swing was an ARTIFACT of the fixed-percent stop or a GENUINE regime effect.
    - Year-over-year dispersion of the time-stop rate, before vs after ATR-scaling is restored. PREDICTION: it narrows. If it does not, the swing was genuine and the rule needs regime-awareness.
    - Full holding-time distribution per exit reason. If holding times bunch against the checkpoint, the checkpoint is creating the mode rather than catching one.
    - COUPLING PREDICTION (falsifiable, registered before results): the vwap gate and the time stop target the same failure mode, so the time-stop rate should FALL in the gated arm relative to ungated. If the gate passes its own test but the time-stop rate does not move, one of the two is not doing what we claimed.
D7. Sequencing constraint for Point 4: time-stop parameters cannot be calibrated before stop geometry is settled PER FOLD. They are coupled through R.
D8. Known gap, not modeled: a 40-bar hold is ~10 hours and crosses at least one funding settlement. Point 2 forbids funding as a backtest input, so this cannot be modeled and must NOT be used to justify shortening the hold. Logged for Point 6.

SECTION 6 — 1R.4 THE EDGE CLAIM (six amendments)
The defect: "break-even at a clean 1:2 after costs ~36% win rate" is true only conditional on every trade resolving at target or stop. That condition holds for 36.2% (2022) and 29.8% (2023) of the population. The framing described a minority subpopulation.
Reconciliation: the pre-committed kill conditions ALREADY speak expectancy. Only the prose was wrong; no kill condition changes.
Decomposition:
        E[R] = p_tgt*(+2) + p_stop*(-1) + p_chk*m_chk + p_hold*m_hold
    all net of costs. The first two terms are fixed by construction; the last two are distributions with unknown means covering the majority of trades.
STRUCTURAL PREDICTION, falsifiable: checkpoint exits survive by being below +1R at the checkpoint close, which truncates the population from ABOVE but not below (trades near -1R survive to be time-stopped; trades near +1R do not), so m_chk should be structurally NEGATIVE. Max-hold exits survive by being AT OR ABOVE +1R at the checkpoint, which selects from above, so m_hold should be structurally POSITIVE. They are opposite-signed by construction and MUST BE REPORTED SEPARATELY — a blended "time stop" mean would average out the one mechanism the exit rules create. If the signs do not come out this way, the state check is not doing what D2 says.
E1. The win-rate framing is RETIRED as a description of the strategy. It survives only as an explicitly labelled conditional: "among trades that resolve at target or stop, 36% must be targets." Never quoted without the qualifier.
E2. Primary edge claim, formally: "Over the out-of-sample holdout, per symbol, with the gate active, expectancy per trade net of all modeled costs is positive; and expectancy with the gate active exceeds expectancy without it by >= 0.05R on an identical trade universe."
E3. Point 4 reports the FOUR-ARM DECOMPOSITION (p and m per arm), never a single expectancy figure alone, with the two time arms separated.
E4. Expectancy per BAR added as a SECONDARY metric (0.1R over 6 bars and 0.1R over 40 bars are not the same strategy). Secondary only — kill conditions remain denominated per-trade.
E5. Power analysis pre-registered. At an estimated per-trade dispersion sigma ~ 1.2R:
        n = 200 (IS min)  -> SE 0.085R -> smallest edge detectable at 2 SE: 0.17R
        n = 50  (OOS min) -> SE 0.170R -> 0.34R
        n = 30  (per direction) -> SE 0.219R -> 0.44R
    Consequences, all pre-registered:
    - The evidence minimums are FLOORS FOR A GO DECISION, not sample sizes that can confirm a modest edge. If OOS expectancy lands near zero at n=50, the honest reading is "UNDERPOWERED, NO CONCLUSION", not "no edge".
    - The 0.05R drop threshold is well under one SE at any of these sample sizes — independent confirmation that D5's single-pass constraint is load-bearing.
    - Point 4 fold design should optimise for OOS TRADE COUNT, since statistical power is the binding constraint.
E6. sigma = 1.2R is an ESTIMATE from the bounds, not a measurement — measuring it requires the r_multiple column, which is firewall-blocked. FIRST ACT AFTER THE FIREWALL LIFTS AT POINT 4: measure sigma and recompute the power table before looking at anything else. If sigma is materially larger, the minimums are worse than shown and the fold design must respond.

SECTION 7 — 1R.5 RSI (four amendments)
Rationale for opening this point: D5 forbids adding attribution arms after the firewall lifts, so any component not registered now either stays unexamined or gets tested post-hoc, which is the iterative search that was banned.
Finding 1: the lower bound is redundant with two other conditions. RSI >= 50 means gains dominate losses over the window; a long entry already requires close above the Donchian-20 upper band (price above everything for 20 bars) and EMA20 > EMA50. Not strict entailment — Wilder smoothing has memory beyond 14 bars — but narrow. The population it rejects is qualitatively distinct: RSI < 50 at a 20-bar high is a REVERSAL breakout, the first break after a sustained decline, which may be a different animal from trend continuation.
Finding 2: the upper bound VIOLATES THE GUARD RAIL PRINCIPLE. The entry mechanism is momentum; RSI <= 75 is a momentum measure. Same unit. The consequence is exactly what the principle predicts: it does not bind conditionally, it truncates the top of the distribution the strategy is built to capture. A trend-continuation strategy that systematically declines the strongest continuations has an unargued contradiction at its centre. The intent behind it is real but is properly a TARGET-PLAUSIBILITY concern and should be denominated in PRICE EXTENSION, not momentum.
F1. Band split into rsi_lower and rsi_upper as SEPARATE registered arms under the D5 single-pass drop rule. Never swept as a unit.
F2. Lower bound RETAINED pending measurement of its pass rate on breakout bars per symbol per year. Both readings pre-registered now: if it rejects almost nothing it is decorative and drops on the single pass; if it rejects a small coherent reversal-breakout population it is a real regime filter and stays.
F3. rsi_upper REMOVED FROM BASELINE. EXTENSION_GUARD registered as a labelled variant in its place, denominated in ATR units of distance from EMA20 (or extension beyond the broken Donchian level). Not baseline; must earn entry on evidence. Registered alongside STRUCTURE_STOP and the partial-runner.
F4. rsi_period FIXED AT 14, not swept, with the inherited-convention limitation stated explicitly. Justification: with the upper bound gone, RSI's remaining job is a near-redundant lower bound that may not survive the drop pass; spending sweep dimensions and statistical power on it is a bad trade against 0.085R of in-sample standard error.

SECTION 8 — BASELINE STRATEGY AFTER 1R
State the current baseline in one place, with every parameter marked DERIVED, FIXED, or UNSET-TO-BE-CALIBRATED. Note explicitly that all values previously described as placeholders remain placeholders unless derived.
- Timeframe 15m, Bitget USDT-M perps, BTC/ETH/SOL, ~$2,000 capital, $20 risk per trade after costs.
- Trend filter: EMA20 / EMA50.
- Trigger: Donchian-20 breakout on a closed 15m bar, market order next bar (fill = 1m close of first minute of bar T+1).
- Gate: session-normalised RVOL (quote-denominated, median slot baseline over baseline_days trailing completed days) AND vwap_position, both binary, conjunctive.
- Momentum condition: rsi_lower only (rsi_period fixed 14). rsi_upper removed.
- Stop: stop_atr_mult * ATR(14), floored at derived stop_min_pct, capped at stop_max_pct.
- Target: +2R, solved net of costs.
- Time stop: state check at bar tau * donchian_period; exit if below the phi-derived threshold. Hard exit at 2 * donchian_period.
- Cooldown: REMOVED (logical no-op).
- One position per symbol, no pyramiding (portfolio mode only).
Also state the parameter surface count: reduced from roughly 15 to roughly 13, with rsi_lower as a live drop candidate.

SECTION 9 — LABELLED VARIANTS (not baseline, must not be silently promoted)
STRUCTURE_STOP (A4), EXTENSION_GUARD (F3), NO_TIME_STOP counterfactual arm (D1), partial-runner exit (from Point 1).

SECTION 10 — WHAT MUST NOT CHANGE
- The pre-committed kill conditions, reproduced in full: gated vs ungated expectancy differ by <0.05R -> gate is decorative; ungated outperforms gated -> thesis backwards (test inverse before discarding); OOS expectancy <= 0 after costs; edge vanishes at +/-25% parameter moves (need a plateau, not a peak); removing the top 5% of winners flips expectancy negative; minimum evidence 200 IS trades, 50 OOS, 30 per direction, PER SYMBOL; short side dropped if OOS expectancy < 0 over 30+ short trades; two-of-three rule (a symbol qualifies only if it passes on its own AND at least one other symbol shows the same direction of edge).
- The performance firewall until it is deliberately lifted at the start of Point 4, after the validation design is pre-registered.
- Every Point 2 data decision and every Point 3 engine semantic.
- 15m timeframe, Bitget, BTC/ETH/SOL, $2,000, 1% risk after costs.
- 2025-26 remains an untouched out-of-sample holdout.

SECTION 11 — OPEN QUESTIONS CARRIED INTO POINT 4 AND BEYOND
1. Bitget kline endpoint: does it expose taker-buy volume? DOCUMENTATION CHECK ONLY — reading the API docs costs nothing and reopens nothing. Only a decision to re-pull data would reopen Point 2. Taker-buy volume would give a true aggressor-flow imbalance, a stronger participation measure than anything derivable from OHLCV.
2. Day-of-week separation in the RVOL slot baseline (B1). Default is to ignore it.
3. Funding cost across multi-bar holds (D8) — logged for Point 6.
4. Point 3 known gaps still open: no signal-mode golden file; Layer B unoptimised; insufficient_data path fixture-tested only.
5. Deferred measurement of overlap between the 425 flagged reconstruction-divergence bars and actual signal bars.

SECTION 12 — NEXT OPEN POINT
Point 4 — validation design. Regime labelling from empirical measurement (never narrative memory), walk-forward folds, out-of-sample holdout, parameter-sensitivity plateaus. The performance firewall lifts at the START of Point 4, only after the validation design is written down and pre-registered. First act after lifting: measure sigma per E6 and recompute the power table.

Constraints
- DOCUMENTATION ONLY. Do not write, modify or delete any code, test, config or data file.
- Do not change any parameter value anywhere in the repo. This document RECORDS decisions; implementing them is a later point.
- Do not run any backtest, sweep, data pull or analysis script.
- Do not compute, display or estimate any profit, loss, expectancy, win rate, Sharpe, profit factor or equity figure. The performance firewall is in force.
- Do not soften, reinterpret or "improve" any decision recorded above. If something reads as internally inconsistent, flag it in the report rather than resolving it yourself.
- Plain markdown. No code blocks except for the formulas already given.

Verification
- Confirm all three files exist at the stated paths.
- Confirm docs/handoff/05_point_1r.md contains all twelve sections in order.
- Confirm `git status` shows ONLY the three new files as changes — no modifications to any existing tracked file.
- Confirm the document contains no numeric profit, loss, expectancy or win-rate figure other than: (a) the retired "36%" framing explicitly labelled as retired and conditional, (b) the 0.05R drop threshold, which is a pre-committed kill condition, and (c) the E5 power-analysis figures, which are standard-error estimates and not results.
- Confirm the pre-committed kill conditions in Section 10 are reproduced verbatim and unweakened.
- Commit all three files in a single commit with the message: "docs: Point 1R handoff — strategy amendment pass (1R.1-1R.5)".

Report back
Write reports/05_point_1r_handoff.md containing:
- File tree of the three created files with line counts.
- The commit hash from `git rev-parse HEAD`.
- Output of `git status` after the commit.
- Section headings extracted from docs/handoff/05_point_1r.md, to confirm structure.
- Any internal inconsistency, ambiguity or missing information you noticed while writing, flagged but NOT resolved.
- Confirmation that no code, test, config or data file was touched.
