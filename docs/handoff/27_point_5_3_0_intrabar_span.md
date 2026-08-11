# REPORT 27 — CAN ONE 1h BAR CONTAIN BOTH THE STOP AND THE TARGET?

**Point 5, sub-point 5.3, step 0.** A MEASUREMENT. No rule is set, no engine file
is touched, no trade is constructed, no outcome is evaluated.

---

## 0. THE DECISION RULE, STATED BEFORE THE MEASUREMENT WAS RUN

**Recorded here verbatim, before any result appears in this document:**

> "The intrabar convention flips a trade between -1.0R and +1.5R, a 2.5R swing.
> If a fraction q of trades is resolved by convention, the maximum expectancy
> distortion is 2.5 x q in R. Thesis section 7 condition (d) uses 0.05R as the
> threshold for a material advantage. Therefore q_max = 0.05 / 2.5 = 2.0% of
> trades. If the upper bound on ambiguous trades exceeds 2.0%, exits are
> evaluated on 1m. At or below 2.0%, 1h is admissible."

### 0.1 THIS IS A WEAKER FORM OF PRE-REGISTRATION THAN THE PROJECT'S OTHERS

> **THE CRITERION WAS STATED IN CONVERSATION AND WAS NOT COMMITTED TO GIT AHEAD
> OF THE MEASUREMENT.** It is **not** equivalent to the timeframe rule at
> `96c96cf` or the risk budget at `a323237`, both of which were committed
> **alone, in their own commits, before the measurement code existed**, so that
> the hash itself proves the rule preceded the number.

**Nothing here can prove this criterion preceded this result.** The closing
record §5.3 is explicit about what that discipline buys — it *"converted a
potential contamination into a disclosed limitation, which is the whole return
on it"* — and that return is not available here. **What is available is a
statement of the weakness, which is this paragraph.**

**Two things reduce the exposure without removing it**, and both are stated as
mitigations rather than as substitutes:

- **the criterion is arithmetic on two already-frozen numbers** — the 2.5R swing
  is `1.0 + 1.5` from the frozen reward-to-risk (thesis §5.2), and 0.05R is kill
  condition (d)'s own threshold (thesis §7). It is not a free parameter that
  could have been dialled to a convenient value; changing it would require
  changing a frozen document.
- **the result is not near the line.** §6's answer exceeds the criterion by more
  than **five times**, and by more than **three times** on the least exposed
  symbol. A criterion chosen to fit this result would have had to be chosen very
  badly to land here.

**Neither observation is a substitute for a commit, and this section is not an
argument that it was.** The correct reading is: *this decision rests on a
criterion whose priority is asserted rather than proven.*

---

## 1. THE QUESTION, AND WHY IT DECIDES A LARGE PIECE OF WORK

The frozen strategy exits at a stop or at a 1:1.5 target. **If both levels lie
inside one 1h bar, no 1h data can say which was reached first**, and the trade is
decided by a convention — pessimistic, optimistic, or coin-flip — rather than by
evidence.

Evaluating exits on **1m** would nearly eliminate the ambiguity. It also requires
**closing the 1m holdout seal gap first**, which is the largest single piece of
work in Point 5.3. **This step measures the exposure so that choice rests on a
number rather than on a preference.**

**THE ANSWER, IN ONE LINE.** The per-trade upper bound on ambiguous trades is
**10.21%** (hold-weighted) or **11.94%** (maximum hold), against a criterion of
**2.0%**. **VERDICT: 1m REQUIRED.**

---

## 2. PROVENANCE

| item | value |
|---|---|
| `git rev-parse HEAD` at measurement | **`ef1f4f6`** — report 26 |
| module | **`src/analysis/intrabar_span.py`**, alongside reports 21, 24 and 26's modules |
| tests | **`tests/test_intrabar_span.py`** |
| ATR | `src/timeframe/atr_profile.py` via `sweep_population.atr_series` — **REUSED, asserted byte-identical** |
| data | `src/timeframe/resample.py`, 1h only |
| cost model | `src/engine/costs.py`, called **only on synthetic reference inputs** |
| window | 2022-01-05T18:00:00Z – 2024-12-31T23:00:00Z, **26,190 bars per symbol** after the 114-bar warm-up |

**NO 1m DATA WAS READ. NOT ONE BAR.** A test asserts no 1m path is reachable
from this module: no `load_1m`, no `ohlcv_1m`, no `BAR_1M_MS`, and the timeframe
constant is pinned to `"1h"`.

**THIS IS A DISTRIBUTION OVER BARS AND IT NEVER PAIRS A BAR WITH A TRADE.** No
position, entry, exit or trade object is constructed; nothing asks whether a
level was reached. A test asserts the module contains no identifier or string
containing `hit`, `touch`, `reached`, `crossed`, `exit_reason` or `was_hit`, and
that `simulate` and `budget_cost` are unreachable.

---

## 3. THE SPAN MULTIPLIER, DERIVED FROM THE ENGINE

### 3.1 What is being derived

A bar could contain both levels only if its range exceeds the **price distance
between the stop and the target**. That distance is **not** 2.5 × the stop
distance: cost-inclusive sizing solves the target **net of costs** and places it
further out than 1.5 × the stop distance (amendment 1 §5.1).

Writing `k` for the span as a multiple of the stop distance:

    criterion:  bar_range  >  k x stop_distance
    naive:      k = 1 + 1.5 = 2.5          -> ATR threshold 2.5 x 2.25 = 5.625
    derived:    k from the cost model      -> below

### 3.2 A FROZEN PARAMETER THAT WOULD HAVE BEEN INHERITED WRONG

> **`CostConfig.target_r_multiple` DEFAULTS TO 2.0. THE THESIS FREEZES 1.5.**

Amendment 1 §3 records the difference by name: *"the engine's default
`target_r_multiple` is 2.0 (Point 4's 1:2) … The thesis sets 1.5. That is a
configuration value, not a code path."* Reports 24 and 26 called only
`position_size`, **which never reads that field**, so their figures are entirely
unaffected — **this is the first measurement in the project for which the field
is load-bearing.**

**Taking the default would have widened every span by about 20%, counted fewer
bars, and understated the exposure this step exists to bound — the unsafe
direction, and invisible in any output.** It is supplied explicitly here and a
test pins both that it is 1.5 and that it differs from the engine default.

*(For the record: under the 2.0 default the pooled per-trade bound would have
read 5.74% rather than 10.21%. The verdict would have been unchanged — both
exceed 2.0% — so this error would not have flipped the decision, but it would
have halved the reported magnitude.)*

### 3.3 The derivation, both ways

**ANALYTIC**, closed form from the `CostConfig` fields, following the engine's
own algebra. With `s` the stop distance as a fraction of entry, `f` taker, `m`
maker, `e` entry slippage, `h` the stop haircut, `RR` the reward multiple:

    sizing, as a fraction of entry (costs.position_size):
        LONG    d = s + f + (1-s) f + e + (1-s) h
        SHORT   d = s + f + (1+s) f + e + (1+s) h

    target, exiting MAKER (costs.solve_price_for_net):
        LONG    X_t = ( RR d + 1 + f ) / (1 - m)     x entry
        SHORT   X_t = ( 1 - f - RR d ) / (1 + m)     x entry

    span    = X_t - X_stop  (long)   or   X_stop - X_t  (short),
              with X_stop = (1 -/+ s) x entry

**THE MAKER EXIT MATTERS.** The target leg is solved against `maker_fee`, not
`taker_fee`. Using the wrong leg would widen the span and understate the
exposure.

**NUMERIC**, by calling the engine's own `position_size` and `solve_target` on
**six hand-chosen synthetic (entry, ATR) pairs** — `(30000, 200)`,
`(30000, 300)`, `(2000, 15)`, `(2000, 30)`, `(100, 1)`, `(100, 2.5)`.

> **THE ENGINE SOLVER IS NEVER CALLED ON A REAL BAR, A REAL SIGNAL OR A REAL
> LEVEL.** A test asserts structurally that `solve_target` and `position_size`
> are named inside exactly one function — the synthetic reference path — and that
> the per-bar sweep's own code calls nothing from `costs`.

**AGREEMENT: the worst absolute discrepancy across all 36 reference cells is
3.9 × 10⁻⁹**, at a reference tick of 1e-8 chosen so the solver's rounding — always
*away* from the position — cannot mask a formula disagreement. **NO STOP
CONDITION.**

### 3.4 The multiplier

**`k` IS NOT A CONSTANT.** To first order `k = 2.5 × (1 + c/s)`, so it **falls as
the stop widens**. A single quoted `k` is therefore a reading at a stated stop
width. **Quoted at the frozen 1.50% floor** — the binding case on nearly half of
BTCUSDT's signals:

| symbol | direction | **derived k** | ATR threshold (k × 2.25) | naive k | naive ATR threshold |
|---|---|---:|---:|---:|---:|
| BTCUSDT | long | **2.722028** | **6.1246** | 2.5 | 5.625 |
| BTCUSDT | short | **2.724638** | **6.1304** | 2.5 | 5.625 |
| ETHUSDT | long | **2.722028** | **6.1246** | 2.5 | 5.625 |
| ETHUSDT | short | **2.724638** | **6.1304** | 2.5 | 5.625 |
| SOLUSDT | long | **2.771288** | **6.2354** | 2.5 | 5.625 |
| SOLUSDT | short | **2.775378** | **6.2446** | 2.5 | 5.625 |

**THE DERIVED SPAN IS 8.9–11.0% WIDER THAN THE NAIVE ONE.** A wider span counts
**fewer** bars, so **the naive form is the looser bound and overstates the
exposure**; the derived figures below are the honest ones. Report 24 §2.1
measured a naive *sizing* form as 7.4% wrong; this is the same hazard on the
target leg, and it runs the same way.

**Long and short differ** because the fee and haircut legs sit on the stop price,
which is below entry for a long and above it for a short. **SOLUSDT's span is
wider** because its stop haircut is 10 bps against BTC/ETH's 5.

**THE PER-BAR SWEEP USES NO SINGLE `k`.** It evaluates the span in **price
units** at each candidate entry bar's own close and ATR, so it inherits none of
the error in quoting one. The table above is for the record.

---

## 4. THE CRITERION, AND WHICH ATR

### 4.1 Only the ATR term of the stop

The frozen stop is `max(2.25 × ATR, 1.50% of entry)`. **Only the ATR term is
used.** The floor can only **widen** the stop and therefore only widen the span,
so ignoring it counts **more** bars. **That is the conservative direction and it
is deliberate.**

### 4.2 Two ratios, and only one of them can decide

The stop is set from the ATR at the **entry** bar, which may be up to **24 bars**
before the bar being tested — report 24 §5.2 measured holds of 17–24 hours — and
ATR moves in between.

    (a)  range[t] / ATR[t]                        the own-bar ratio
    (b)  range[t] / min(ATR[t-24] .. ATR[t-1])    the worst case over every bar
                                                  that could have been the entry

> **(b) IS THE DECISION-RELEVANT ONE.** The smallest ATR in the window gives the
> tightest possible stop and therefore the **narrowest possible span**. **(a) IS
> NOT CONSERVATIVE IN RISING VOLATILITY** and must not drive the conclusion: a
> bar that is unremarkable against its own inflated ATR may be enormous against
> the ATR that actually set the stop of a position opened a few hours earlier.

**The lookback EXCLUDES the current bar** — bar `t` cannot have been its own
entry bar — asserted on the window contents directly, the same convention and the
same guard as report 21's Donchian channel.

### 4.3 THE TWO RATIOS GIVE OPPOSITE VERDICTS ON THIS DATA

**This is the single most consequential methodological fact in the report.**

| symbol | per-trade bound from **(a)**, max hold | per-trade bound from **(b)**, max hold |
|---|---:|---:|
| BTCUSDT | **0.82%** | **14.85%** |
| ETHUSDT | **1.10%** | **12.92%** |
| SOLUSDT | **0.64%** | **8.06%** |

> **RATIO (a) CLEARS THE 2.0% CRITERION ON EVERY SYMBOL. RATIO (b) EXCEEDS IT ON
> EVERY SYMBOL, BY BETWEEN FOUR AND SEVEN TIMES.** Choosing the wrong ratio does
> not shade this answer — **it reverses it.**

A test asserts both halves of this, so a future change that silently switched
ratios would fail rather than flip a verdict.

---

## 5. THE MEASUREMENT

### 5.1 Ratio distributions, pooled and per symbol — 26,190 bars each

**Ratio (a), range / own-bar ATR:**

| symbol | max | P99.9 | P99 | P95 | P90 | median | mean |
|---|---:|---:|---:|---:|---:|---:|---:|
| BTCUSDT | 8.862 | 5.166 | 3.306 | 2.102 | 1.691 | 0.823 | 0.985 |
| ETHUSDT | 8.343 | 5.154 | 3.132 | 2.068 | 1.656 | 0.838 | 0.986 |
| SOLUSDT | 8.464 | 5.138 | 2.804 | 1.895 | 1.563 | 0.870 | 0.989 |

**Ratio (b), range / minimum prior-24 ATR — THE DECISION-RELEVANT ONE:**

| symbol | **max** | **P99.9** | **P99** | P95 | P90 | median | mean |
|---|---:|---:|---:|---:|---:|---:|---:|
| BTCUSDT | **63.143** | **11.545** | **5.616** | 3.162 | 2.389 | 0.992 | 1.307 |
| ETHUSDT | **39.023** | **10.423** | **5.057** | 2.893 | 2.222 | 0.990 | 1.255 |
| SOLUSDT | **31.453** | **9.115** | **4.300** | 2.578 | 2.043 | 1.003 | 1.219 |

**THE MAXIMUM IS NOT BELOW THE THRESHOLD.** Ratio (b) reaches **63.1** on
BTCUSDT against a threshold near **6.12**. **Ambiguity is not impossible
in-sample; it is possible and it is not rare.** The P99 of ratio (b) is already
within 10% of the threshold on BTCUSDT.

### 5.2 Exceedance counts

**The criterion applied exactly, in price units, per bar: `range[t] >` the
narrowest span any position open on bar `t` could have carried**, minimised over
both directions and over all 24 candidate entry bars.

| symbol | bars | **derived: exceeding** | **fraction** | naive (5.625): exceeding | fraction |
|---|---:|---:|---:|---:|---:|
| BTCUSDT | 26,190 | **162** | **0.6186%** | 259 | 0.9889% |
| ETHUSDT | 26,190 | **141** | **0.5384%** | 185 | 0.7064% |
| SOLUSDT | 26,190 | **88** | **0.3360%** | 121 | 0.4620% |
| **POOLED** | **78,570** | **391** | **0.4976%** | **565** | **0.7191%** |

**More than fifty bars exceed on every symbol, so no timestamp listing is
emitted** — the module emits one only below that threshold, and a test asserts
the listing is absent for the right reason.

**The naive threshold counts 44% more bars**, as it must: a narrower span
catches more. Asserted by test, so the two thresholds cannot be silently
swapped.

### 5.3 Per fold — derived exceedance on ratio (b)

| fold | period | BTCUSDT | ETHUSDT | SOLUSDT |
|---:|---|---|---|---|
| 1 | train | 16 (0.364%) | 10 (0.228%) | 7 (0.159%) |
| 1 | test | 23 (1.042%) | 22 (0.996%) | 15 (0.679%) |
| 2 | train | 33 (0.747%) | 28 (0.634%) | 20 (0.453%) |
| 2 | test | 21 (0.972%) | 17 (0.787%) | 15 (0.694%) |
| 3 | train | 44 (1.007%) | 39 (0.893%) | 30 (0.687%) |
| 3 | test | 20 (0.916%) | 16 (0.733%) | 14 (0.641%) |
| 4 | train | 41 (0.944%) | 33 (0.760%) | 29 (0.668%) |
| 4 | test | 20 (0.906%) | 21 (0.951%) | 14 (0.634%) |
| 5 | train | 40 (0.911%) | 37 (0.842%) | 28 (0.638%) |
| 5 | test | 18 (0.815%) | 14 (0.634%) | 9 (0.408%) |
| 6 | train | 38 (0.861%) | 35 (0.793%) | 23 (0.521%) |
| 6 | test | 13 (0.595%) | 7 (0.321%) | 3 (0.137%) |
| 7 | train | 31 (0.706%) | 21 (0.478%) | 12 (0.273%) |
| 7 | test | 9 (0.412%) | 13 (0.595%) | 5 (0.229%) |
| 8 | train | 22 (0.504%) | 20 (0.458%) | 8 (0.183%) |
| 8 | test | 10 (0.453%) | 12 (0.543%) | 2 (0.091%) |
| 9 | train | 19 (0.433%) | 25 (0.569%) | 7 (0.159%) |
| 9 | test | 6 (0.272%) | 9 (0.408%) | 2 (0.091%) |

**EVERY ONE OF THE FIFTY-FOUR CELLS IS NON-ZERO.** The exposure is not
concentrated in one fold or one regime: it is present everywhere, peaking in
folds 3–6 (the 2023 window) and falling toward the end of the period. **The
lowest cell — SOL fold 8 test at 0.091% — still gives a per-trade bound of 2.2%
at maximum hold, above the criterion.**

---

## 6. PER-BAR TO PER-TRADE, AND THE VERDICT

**The decision rule is denominated in trades, not bars.** A trade open for `n`
bars is exposed on `n` bars, so the chance that at least one of them is large
enough is **at most `n × p`** — a union bound.

**Report 24 §5.2's measured hold histogram**, transcribed and not recomputed:

| hold (hours) | 17 | 18 | 19 | 20 | 21 | 22 | 23 | 24 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| positions | 1,493 | 1,431 | 1,451 | 1,226 | 1,391 | 1,368 | 1,592 | 1,432 |

**Mean hold 20.5129 bars** over all 11,384 positions.

| population | p (per bar) | **weighted (× 20.51)** | **max hold (× 24)** | criterion | verdict |
|---|---:|---:|---:|---:|---|
| BTCUSDT | 0.6186% | **12.69%** | **14.85%** | 2.0% | **exceeds** |
| ETHUSDT | 0.5384% | **11.04%** | **12.92%** | 2.0% | **exceeds** |
| SOLUSDT | 0.3360% | **6.89%** | **8.06%** | 2.0% | **exceeds** |
| **POOLED** | **0.4976%** | **10.21%** | **11.94%** | **2.0%** | **EXCEEDS** |
| pooled, naive threshold | 0.7191% | 14.75% | 17.26% | 2.0% | exceeds |

> # VERDICT: 1m REQUIRED.
>
> **The pooled per-trade upper bound is 10.21% hold-weighted and 11.94% at
> maximum hold, against a criterion of 2.0%. It exceeds the criterion by 5.1×.**
>
> **Every symbol exceeds it independently**, the least exposed by 3.4×. **Every
> one of the eighteen fold periods exceeds it on every symbol.** The naive
> threshold, the derived threshold, the weighted conversion and the maximum-hold
> conversion **all give the same answer**, and the answer does not depend on
> which of them is used.
>
> **Exits are evaluated on 1m.** Closing the 1m holdout seal gap is therefore on
> the critical path for Point 5.3.

---

## 7. THE CONSERVATISM STACK — the true figure is BELOW this bound

**EVERY LAYER RUNS THE SAME WAY. The bound is loose, and by an unquantified
margin.**

**7.1 A BAR LARGE ENOUGH IS USUALLY NOT POSITIONED TO CONTAIN BOTH LEVELS.** The
criterion asks only whether the bar's range **exceeds** the stop-to-target
distance. It does not ask whether the bar's high and low actually **straddle**
both levels — which requires the bar to sit in a particular place relative to an
entry made hours earlier. **This is the largest term in the stack and it is not
quantified here**, because quantifying it would mean pairing a bar with a trade's
levels, which is exactly what §2's firewall boundary forbids at this step.

**7.2 THE UNION BOUND ASSUMES INDEPENDENCE ACROSS A TRADE'S BARS.** It does not
hold: **large bars cluster**, so a trade that contains one large bar is more
likely than average to contain a second, and `n × p` over-counts. The direction
is certain even though the magnitude is not.

**7.3 THE FLOOR IS IGNORED.** Using only the ATR term of the stop counts bars
that a floored — and therefore wider — stop would have excluded. Thesis §5.1
measures the floor binding on **46.15% / 29.43% / 3.09%** of signals, so on
BTCUSDT this is nearly half of them.

**7.4 THE MINIMUM PRIOR ATR IS THE WORST CASE, NOT THE TYPICAL ONE.** Ratio (b)
divides every bar's range by the **smallest** ATR in the preceding 24 bars. A
real trade's stop was set by **one** of those bars, not the most favourable one.
The gap between ratio (a) and ratio (b) in §4.3 is the size of this term, and it
is large.

**7.5 EVERY LARGE BAR IS ASSUMED TO RESOLVE ITS TRADE AMBIGUOUSLY.** A bar can
exceed the span without the trade being open at that moment in a way that makes
both levels live.

> **CONCLUSION ON THE STACK: 10.21% IS AN UPPER BOUND ON AN UPPER BOUND. THE
> TRUE AMBIGUOUS FRACTION IS LOWER, AND NOTHING HERE SAYS BY HOW MUCH.**
>
> **THIS DOES NOT WEAKEN THE VERDICT AND IT WOULD BE A MISREADING TO TREAT IT AS
> IF IT DID.** The criterion is explicitly written against an *upper bound* — *"if
> the upper bound on ambiguous trades exceeds 2.0%"* — and the margin is 5.1×.
> **The stack would have to be wrong by more than a factor of five, in the same
> direction, on every symbol and every fold, for 1h to be admissible.** The
> honest use of §7 is in sizing the 1m work's benefit, not in reopening the
> decision.

---

## 8. GAP RISK — RECORDED AS A LIMITATION, NOT MEASURED

**THIS MEASUREMENT ASSUMES FILLS OCCUR AT THE STOP OR TARGET PRICE.** It does not
address a bar **OPENING beyond a level**, where the fill would be worse than the
level and the realised loss would exceed the risk unit.

> **GAPS ARE INVISIBLE IN THIS DATA BY CONSTRUCTION AND CANNOT BE MEASURED
> HERE.**

Bitget's `open` field is **synthesised from the carried-forward previous close**.
The derived layer renames it **`open_synth`** and every loader in the project
**drops it at the boundary** — `schedule.load_bars` and `resample._drop_open`
both refuse a real `open` column and discard the synthetic one, and reports 21,
24 and 26 each assert that no `open` reaches them. **A synthesised open equals
the previous close by definition, so the data contains no gap even where the
market had one.** No amount of care with this series can recover it.

**WHAT THIS MEANS FOR THE DECISION.** Gap risk is **strictly additive** to the
ambiguity measured here: it is a second way the 1h convention can misprice an
exit, and it also argues toward finer data. **It does not change the verdict,
which is already 1m REQUIRED**, and it is not used to support it.

**THIS LANDS ON 5.3.2's EXIT PRE-REGISTRATION.** That step must state what
happens when a bar's first observed price is already beyond a level, and it
cannot answer that from this data layer. **Recorded here so it is inherited as an
open item rather than discovered later.**

---

## 9. VERIFICATION

### 9.1 SYNTHETIC POSITIVE CONTROL — exceeding bars by INDEX, not by count

**THE CONSTRUCTION.** 400 flat bars with range exactly 2.0 and ATR exactly 2.0,
so no bar exceeds. Three bars widened to a range of **40.0** — far above any
threshold near 6.2 × ATR — at indices **150, 250 and 350**, spaced more than 24
bars apart so each is the only wide bar in its own lookback window.

**ASSERTED BY INDEX** against `[36, 136, 236]` (the warm-up trims 114), **not by
count**: a count alone would pass if the detector fired on the wrong bars.
**PASSES.**

The ratios at the first spike are asserted against hand arithmetic:
`range / ATR = 40 / ((13 × 2.0 + 40.0)/14) = 8.4848…` — **Wilder's ATR includes
the current bar's own true range**, so the own-bar ratio is *not* 40/2 — while
`range / min prior ATR = 40 / 2.0 = 20` exactly. **The gap between the two at the
same bar is precisely the effect that makes ratio (b) decision-relevant.**

**The later two spikes are asserted to within 0.1%, not exactly, and the reason
is recorded:** Wilder's smoothing decays a spike **geometrically** and never
returns exactly to its pre-spike value — 100 bars on, the residue is still
`(13/14)^100 = 6.0 × 10⁻⁴`. **Asserting exact equality there would be asserting
something false about the estimator.**

A second control sweeps a single bar's range across the threshold and asserts it
flips from non-exceeding to exceeding exactly once, at the arithmetic's own
value.

### 9.2 SYNTHETIC NEGATIVE CONTROL

A flat series with **one** bar placed deliberately **just below** the span:
**zero exceedances**. Widening that same bar past the span: **exactly one**, at
the asserted index. **PASSES.**

**A construction that did not work is recorded, because the reason is
instructive:** setting *every* bar's range near the span fails, because a series
whose every range is 12 has an ATR of 12, which puts the stop at 2.25 × 12 and
the span far above 12 again. **The span scales with the series' own volatility,
so "just below the threshold" is only meaningful for a bar that is large
relative to its own history.**

### 9.3 The remaining tests

| check | result |
|---|---|
| analytic and numeric `k` agree at all 36 reference cells | **passes**, worst error 3.9e-9 |
| derived `k` is **not** the naive 2.5, and the two are not confusable | **passes** |
| `k` falls as the stop widens; long ≠ short; SOL > BTC = ETH | **passes** |
| `target_r_multiple` is 1.5 and **differs from the engine default of 2.0** | **passes** |
| ATR is **byte-identical** to `sweep_population`'s and to `atr_profile`'s directly | **passes** |
| the prior-min lookback is 24 bars and **excludes the current bar** | **passes**, asserted on window contents |
| ratio (b) ≤ ratio (a) when ATR is non-increasing; equal when ATR is flat | **passes** |
| the two ratios give opposite verdicts on real data | **passes**, asserted both ways |
| the naive threshold counts **more** bars than the derived one | **passes** |
| the hold histogram sums to 11,384 with mean 20.5129 | **passes** |
| the engine solver is named in exactly one function, the synthetic path | **passes**, asserted over the AST |
| no 1m path, no `simulate`, no `budget_cost` reachable | **passes** |
| no `hit` / `touch` / `reached` / `crossed` / `exit_reason` / `was_hit` | **passes** |
| twelve-name performance firewall | **passes** — see §9.4 |

### 9.4 ONE CARVE-OUT IN THE FIREWALL, AND IT IS RECORDED

**`r_multiple` IS ON THE BANNED LIST AND `target_r_multiple` IS AN ENGINE CONFIG
FIELD THIS MODULE MUST NAME.** The blanket substring ban is **kept**, and the
single token `target_r_multiple` is stripped before the check, with a **separate
assertion** that it appears only as a config field: never as an assignment
target, never as a bare `r_multiple`. **A computed R multiple would still fail
the guard.**

**It is recorded rather than quietly excluded**, because a firewall with an
undocumented exception is a firewall nobody can audit.

### 9.5 PLANTED MUTATION — the holdout seal

**THE MUTATION.** In `src/timeframe/resample.py`, both halves of the filter
widened at once: `WINDOW_END` to 2025-06-30 and `ALLOWED_YEARS` to include 2025.

**RESULT: planted, confirmed failing, reverted.**

| scope | outcome under the mutation |
|---|---|
| `tests/test_intrabar_span.py` | **10 tests fail** (2 failures + 8 errors) |
| whole suite | **65 fail** (36 failures + 29 errors) |
| first assertion to fire | `assert rs.WINDOW_END == dt.date(2024, 12, 31)` → `datetime.date(2025, 6, 30) == datetime.date(2024, 12, 31)` |

`git diff --stat src/timeframe/resample.py` is **empty** after the revert. The
module defines no window constant of its own, asserted over its AST, and the
sealed year does not appear in its source.

### 9.6 FULL SUITE

| | tests |
|---|---:|
| baseline at `ef1f4f6` | **868 passing** |
| new in `tests/test_intrabar_span.py` | **+30** |
| **total** | **898 passing / 898** |

---

## 10. WHAT CONTRADICTS A FROZEN DOCUMENT

**Nothing contradicts a frozen document. One frozen note was found to be
load-bearing here for the first time, and one convention is confirmed.**

**10.1 AMENDMENT 1 §3's NOTE ABOUT `target_r_multiple` BECAME OPERATIVE.** It
recorded that the engine defaults to 2.0 while the thesis freezes 1.5, and
called it *"a configuration value, not a code path"* — correct, and until now
inconsequential, because no measurement had solved a target. **This one does, and
the note is what prevented the error.** §3.2 records both the correction and
what the wrong value would have produced. **Reports 24 and 26 are unaffected:
`position_size` never reads the field.**

**10.2 REPORT 24 §5.2's HOLD DISTRIBUTION IS USED AS THE CONVERSION WEIGHT** and
is transcribed unchanged. No position is constructed here to re-derive it.

**10.3 THE `open_synth` CONVENTION IS CONFIRMED, NOT CONTRADICTED.** The closing
record's account of it is exactly right, and §8 records the consequence for gap
risk as an open item for 5.3.2.

---

## 11. WHAT THIS HANDS TO 5.3

1. **EXITS ARE EVALUATED ON 1m.** The per-trade upper bound is 10.21% against a
   2.0% criterion, exceeded by every symbol and every fold period independently.
2. **CLOSING THE 1m HOLDOUT SEAL GAP IS ON THE CRITICAL PATH.** It is no longer
   optional work; it is a precondition for a defensible exit evaluation.
3. **THE BOUND IS LOOSE (§7)** and the true ambiguous fraction is lower by an
   unquantified margin. That matters for sizing the benefit of the 1m work, not
   for the decision.
4. **GAP RISK IS UNMEASURABLE IN THIS DATA LAYER (§8)** and lands on 5.3.2's exit
   pre-registration as an explicit open item.
5. **THE DECISION RULE'S PRE-REGISTRATION IS WEAKER THAN THE PROJECT'S OTHERS
   (§0.1).** If 5.3's later work wants to lean on this verdict, it should lean on
   the 5.1× margin rather than on the criterion's provenance.

---

**Files.** `src/analysis/intrabar_span.py` · `tests/test_intrabar_span.py` ·
this report.
**Not modified:** every engine file · `src/risk/budget.py` ·
`src/analysis/sweep_population.py` · `src/analysis/exposure_profile.py` ·
`src/analysis/budget_cost.py` · `config/contracts_cache.json` · every frozen
document numbered 22, 22a, 23, 24, 25, 26, 05, 05a and 05b.
**No 1m data was read.** **Holdout:** sealed, unspent, re-verified by planted
mutation. **Firewall:** armed, AST-guarded, one recorded carve-out, no trade
constructed and no bar ever paired with a level.
