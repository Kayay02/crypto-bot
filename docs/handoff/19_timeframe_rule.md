# TIMEFRAME SELECTION RULE — PRE-REGISTERED

**Status:** FROZEN at this commit. This document is committed ALONE, containing
nothing else, before any measurement code is written and before any bar is read.
The commit hash is the proof that the rule preceded the numbers it selects on.

**Context.** Point 1 is reopened after the Point 4 hypothesis was validated and
killed (`docs/handoff/16_point_4_closing.md`). The timeframe is NOT inherited:
15m came from the original Point 1, and section 8.3 of the closing record states
that no Point 4 choice carries forward by default.

**What this rule is for.** Reports 17 and 18 established a cost floor the new
hypothesis inherits. Point 4 used 1.5 × ATR(14) floored at 1%, and the floor
bound 65–81% of breakout bars — which implies 15m ATR% sits mostly below ~0.67%,
so a stop placed at the cost floor would never be reached by the ATR term. The
multiplier would be decorative and the rule would be a fixed-percentage stop
wearing an ATR costume. This rule decides, in advance of looking, on which
timeframes an ATR-proportional stop at the cost floor is actually operative.

---

## THE RULE

**ADMISSIBILITY.** A timeframe is admissible if, for ALL THREE symbols, there
exists a multiplier m in [1.0, 3.0] such that

    m × median(ATR%) >= 1.50%

**SELECTION.** Choose the FINEST admissible timeframe. Finer is preferred
because more bars means more trades means more power against the ~0.34R minimum
detectable edge, and because it stays closer to the project's intraday intent.
The cost floor pushes coarser; power pushes finer; the rule takes the finest
point that satisfies the constraint.

**FLOOR PROVENANCE.** 1.50% is the all-taker slippage-headroom floor from report
18, itself derived from COST_TOLERANCE_R = 0.11. It is not a new number and is
not adjustable in this step.

**MULTIPLIER RANGE.** [1.0, 3.0] is a JUDGEMENT and the only free parameter in
this rule. Below 1.0 the stop sits inside typical bar range and is hit by noise.
Above 3.0 the multiplier rather than the volatility is setting the stop, which
is the section 2.2 failure mode. Recorded as a judgement, not a derivation.

**ANCHOR.** The median is the selection anchor. P25 and P75 are reported for
information — a stop clearing the floor at the median but not at P25 behaves
differently in calm regimes — but do NOT enter the admissibility test.

**REGIME.** Admissibility is assessed on the AGGREGATE distribution over
2022-01-01 to 2024-12-31. Per-tercile figures are reported for information only
and do NOT enter the test.

**IF NOTHING IS ADMISSIBLE.** That is a FINDING, not grounds to relax the
multiplier range, the floor, or the candidate set. It would mean the cost
structure rules out this instrument set at every timeframe under consideration,
which directly answers section 8.4's second question.

**THIS RULE IS FROZEN** once committed. It may not be modified in light of the
measurement it selects on.

---

## SCOPE OF THE MEASUREMENT THIS RULE WILL BE APPLIED TO

Fixed here so the measurement cannot be shaped after the fact:

- **Candidate timeframes:** 5m, 15m, 1h, 4h, 1d. The candidate set is closed.
- **Window:** 2022-01-01 to 2024-12-31 only. **The holdout is sealed** —
  2025-01-01 through 2026-07-26 has never been read, not one bar, and
  resampling is a new code path onto sealed data through which the seal must
  hold.
- **Symbols:** BTCUSDT, ETHUSDT, SOLUSDT. All three must pass; there is no
  partial admissibility.
- **ATR:** ATR(14), Wilder's smoothing, on resampled bars. True range =
  max(H − L, |H − C_prev|, |L − C_prev|).
- **No open price.** The Bitget `open` field is synthesised (carried-forward
  previous close) and is renamed `open_synth` in the derived layer so that any
  reference fails loudly. ATR needs only high, low and close.
- **Incomplete buckets are DROPPED**, never forward-filled, interpolated or
  padded. A partial bucket's high and low are computed over a partial window and
  understate the true range.

## THE FIREWALL IS RE-ARMED

No expectancy, win rate, profit factor, Sharpe, equity curve, `r_multiple` or
`net_pnl` aggregate is computed, referenced or estimated anywhere in the step
this rule governs. ATR percentiles are an explicitly permitted pre-firewall
quantity. No trade is simulated, no signal is generated, and no entry rule
exists yet. This is a distributional measurement on price ranges.
