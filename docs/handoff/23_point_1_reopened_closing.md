# POINT 1 (REOPENED) — CLOSING RECORD AND HANDOFF

## 1. STATUS AND VERDICT

**POINT 1 (REOPENED) IS CLOSED.** It was opened after the Point 4 hypothesis was
validated and killed (`docs/handoff/16_point_4_closing.md`), and it has produced
what it was reopened to produce: **a complete, frozen, pre-registered thesis.**

**THE THESIS:** a **Donchian-10 wick-and-reject liquidity-sweep reversal on 1h**
— a bar whose extreme reaches beyond the prior 10-bar channel intrabar while its
close returns inside it, traded against the direction of the sweep. Frozen at
`02e47a5` (`docs/handoff/22_point_1_thesis.md`), as amended by `703046a`
(`docs/handoff/22a_point_1_thesis_amendment_1.md`).

**NO PERFORMANCE FIGURE WAS COMPUTED AT ANY STAGE OF THIS POINT.** Not one
expectancy, win rate, profit factor, Sharpe, equity curve, `r_multiple` or
`net_pnl` aggregate. Everything decided was decided from:

- **fee schedules** retrieved from the venue (reports 17, 18),
- **indicator distributions** on bars — ATR%, RSI, excursion, bar range
  (reports 19, 20, 21),
- **signal counts and pass rates** per symbol per fold (reports 20, 21),
- **arithmetic on frozen parameters** (thesis §6, amendment 1 §4),
- **source-code verification** of the engine's sizing and target solving
  (amendment 1 §3).

Every one of those is a permitted pre-firewall quantity, and the firewall was
re-armed and AST-guarded in each measurement module.

**THE HOLDOUT IS UNSPENT.** **2025-01-01 through 2026-07-26 has never been
read — not one bar — by any code path in this project.** The seal was
re-verified by planted mutation in reports 19, 20 and 21, and in every case the
mutation was confirmed to fail the guard before being reverted.

**698 tests pass** at the closing commit.

---

## 2. THE FROZEN SPECIFICATION

**This section is an INDEX, not a restatement.** The authoritative documents are
`docs/handoff/22_point_1_thesis.md` (frozen at `02e47a5`) and
`docs/handoff/22a_point_1_thesis_amendment_1.md` (frozen at `703046a`). Where
this table and those documents disagree, **they win.**

| parameter | value | fixed by |
|---|---|---|
| **Timeframe** | **1h** | rule `96c96cf`, report 19 at `74e3ca9` |
| **Trigger** | **Donchian-10 wick-and-reject**, current bar excluded from its own window, all four comparisons strict | thesis §4; geometry `aea6b5c` |
| **Two-sided bars** | **SKIPPED** — no trade taken | thesis §4.1 |
| **Entry** | **close of the signal bar, taker** — **FROZEN** | thesis §4.2 |
| **Stop** | **2.25 × ATR(14)**, floored at **1.50%** | thesis §5.1; floor from `d850ac4` |
| **Target** | **1 : 1.5, solved NET of costs** | thesis §5.2; engine verified at `703046a` |
| **Time exit** | **n = 3 funding settlements** (elapsed 16–24h), funding-cost justification only | thesis §5.3 |
| **Oscillator** | **NONE** — RSI carries no independent information at a channel event | report 20 at `02acbcf` |
| **Volume term** | **NONE** — deliberate departure from the original brief | thesis §3.2 |
| **Session filter** | **NONE — ruled OUT** | thesis (not specified; not added) |
| **`COST_TOLERANCE_R`** | **0.11** — frozen, not revisited | reports 17 / 18 |
| **Breakeven win rate** | **40.0%** | amendment 1 at `703046a` |
| **Detectable-edge win rate (E = 0.34R)** | **53.6%** | amendment 1 at `703046a` |

**Kill conditions (a)–(f) and the majority-of-nine aggregation rule** are frozen
in thesis §7 and §7.1 and are not reproduced here.

---

## 3. WHAT THIS POINT ESTABLISHED — findings that outlive it

**These are the transferable results.** Each survives the death of this thesis
and should be carried into any successor hypothesis.

### 3.1 EQUITY CANCELS FROM COST-IN-R

    cost_in_R = 2 * (f_eff + slip) / s

**Account size never enters.** The cost of a trade as a fraction of its own risk
unit is a function of fee rates, slippage and stop width — nothing else. Capital
affects only **leverage** and **lot granularity**, and neither binds at present
values (leverage term $20/($2,000 × 3) = 0.333%, far inside the 1.50% floor).

**Consequence: "this would work with more capital" is UNAVAILABLE as a cost
argument.** The question that was asked when this point opened — *"is $2,000 on
15m too small?"* — mislocated the binding variable. More capital does not move
the admissibility line.

*Source: report 17 (`a9a4c76`), §3.1.*

### 3.2 THE SLIPPAGE QUESTION IS CLOSED ABOVE 1.00% STOPS

A **tick-size lower bound** on the spread — the book cannot be tighter than one
tick — gives **34.7× to 1,369× headroom** at stops ≥ 1.00% of entry, on all
three symbols. The minimum anywhere in that region is 34.7× (SOL, all-taker,
1.50% stop): the book would have to widen thirty-five-fold from its own
granularity floor before costs breached 0.11R.

**Sub-1% stops still require measurement.** That is a **forward trigger, not a
threshold** — if a future design proposes a stop under 1.00%, slippage must be
measured before it can be admitted.

*Source: report 18 (`d850ac4`), §3–4.*

### 3.3 THE DONCHIAN/RSI ENTAILMENT IS STRUCTURAL AND SCALE-INVARIANT

A channel breakout **entails** elevated RSI, and the mechanism is exact: the
breakout bar's own gain enters Wilder's `avg_gain` at weight **1/14** on the very
bar the condition fires. For RSI to stay below 50 the prior losses would have to
outweigh that gain by a factor of 13.

**Measured at 1h over 2022–2024: ZERO sub-50 long-breakout bars on BTC and ETH;
ONE on SOL** (0.0829% of 1,206). The unconditional RSI distribution is centred
on 50 with a P5 near 30 — **so this is CONDITIONING, not scarcity.** There is no
shortage of low-RSI bars; the channel condition simply never selects one.
Confirmed at 15m as a control, where the 2022–23 figures reproduce Point 3's
minimum of 54.18 / 54.56 / 55.73 exactly.

**1R.5 is CLOSED.** The reversal-breakout hypothesis cannot be exercised with an
RSI bound on a Donchian trigger at any timeframe under consideration.

*Source: report 20 (`02acbcf`), §4–6.*

### 3.4 15m WAS INOPERATIVE FOR AN ATR-SCALED STOP — and this EXPLAINS a Point 4 finding

At 15m, `1.5 × median ATR` places the stop at **0.48% / 0.59% / 0.99%** of entry
(BTC / ETH / SOL) — **below even the 1.0909% fee-only floor on all three
symbols.**

**This is the mechanism behind the Point 4 observation that its 1% floor bound
65–81% of breakout bars.** The multiplier was never setting the stop; the floor
was, essentially always. Point 4's stop rule was a fixed-percentage stop wearing
an ATR costume, and the reason is arithmetic rather than incidental.

**This is a mechanism, not a correlation.** It was derived from ATR%
distributions before the connection to Point 4 was drawn, and it retrodicts the
earlier finding rather than being fitted to it.

*Source: report 19 (`74e3ca9`), §3.*

### 3.5 THE SWEEP REJECTION RATE IS ~0.53–0.57 AND INVARIANT TO CHANNEL LENGTH

Of all bars that break the Donchian channel intrabar, **52.6%–57.5% close back
inside it.** The figure is **nearly identical at Donchian-10 and Donchian-20**
(0.5258–0.5749 against 0.5201–0.5732) and is consistently one to two points
higher on the long side than the short side, on every symbol at both lengths.

**Whatever produces rejections is not a property of how far back the channel
looks.** This is the first measurement of a quantity the project had only
guessed at. **Unexplained. Recorded as a structural regularity, not pursued.**

*Source: report 21 (`aea6b5c`), §2.1.*

### 3.6 WICK-AND-REJECT BARS ARE NOT A HIGH-ATR SUBSET

The prediction was that these bars, being large, would sit clear of a percentage
floor. **They do not.** BTC floor binding is **46.15% on signals against 46.21%
on all bars** — a difference of 0.05 percentage points. ETH differs by 0.33,
SOL by 0.06.

**Why.** The trigger selects on **RELATIVE range** — the bar's size against its
own ATR, where these bars run 1.23–1.54× typical. **That criterion is
scale-free, and therefore nearly orthogonal to the ATR LEVEL**, which is what a
percentage floor compares against. Selecting for `range / ATR` says almost
nothing about `ATR / close`.

**TRANSFERABLE RULE: any argument of the form "these bars are volatile,
therefore X about a percentage threshold" is UNSOUND** and must be checked
rather than asserted.

*Source: report 21 (`aea6b5c`), §5.1.*

### 3.7 THE ENGINE SIZES COST-INCLUSIVE AND SOLVES TARGETS NET

Verified **in source** at `703046a`, not inferred from documentation:

- `src/engine/costs.py:319` `position_size` — `N = R$ / (s + c)`, where the
  denominator is the price move plus both fee legs plus both slippage legs. A
  stop-out loses **exactly −1.0R**.
- `src/engine/costs.py:285` `solve_target` — solves for net `+RR × R$` after the
  round trip. A target exit returns **exactly +RR**.
- Pinned by **four tests**, including `test_losing_trade_costs_exactly_one_R` and
  a regression pin at `r_multiple = -1.0001204`.

**COSTS ARE PAID IN REACHABILITY, NOT AS A PER-TRADE R HAIRCUT.** The target
sits **~18% further away** (2.6625% against a naive 2.25% at the 1.50% floor);
the R multiple of any completed trade is untouched by costs. This is the finding
that corrected the thesis's win rates.

*Source: amendment 1 (`703046a`), §3 and §5.*

### 3.8 SIGNAL COUNTS ARE NOT A CONSTRAINT

Worst of nine training folds: **570 signals against a 200 minimum** (2.85×).
Worst of nine test folds: **281 against 50** (5.62×). Every fold clears on every
symbol. **Donchian-20 would also have cleared** (367 / 161), so the N = 10 choice
was not required by power.

*Source: report 21 (`aea6b5c`), §3.*

---

## 4. ERRORS MADE AND RECORDED

The Point 4 closing record §3.4 documents a recurring defect class:

> **a numerical criterion written from a mental model of a quantity rather than
> from its implementation or its achievable range.**

**IT RECURRED REPEATEDLY IN THIS POINT.** Nine instances are recorded below,
because **a failure recorded as failure is worth more than one quietly
dropped** — and because the class is evidently not yet extinguished by being
named.

**(1) COST TOLERANCE FRAMED AS AN ACCOUNT-SIZE QUESTION.** The point opened by
asking whether $2,000 on 15m was too small. Equity cancels from `cost_in_R`
entirely (§3.1). The binding variable was the stop width relative to the fee
rate, and the question as posed could not have found it.

**(2) THE SLIPPAGE AXIS WAS ARBITRARY.** A 0–10 bps range was specified with no
derivation, and the first pass's verdict — *"slippage is 2.5× the fee axis"* —
was a **restatement of the chosen axis width**, not a finding about slippage.
Retracted in report 17's second pass (`a9a4c76`, §4.1).

**(3) SLIPPAGE CHARGED ON MAKER LEGS.** The first pass charged slippage on all
legs. A leg filled as maker rested at its own price and got that price.
Corrected to `2 × (1 − maker_frac) × slip`, which systematically lowered the cost
of maker execution.

**(4) THE NON-FILL TERM'S UNIT.** Introduced as `MAKER_NONFILL_COST_R` — the
`_R` suffix declaring R denomination — and placed **outside** the division by
`s`, with a docstring defending the non-scaling. **A chase is a price
displacement**, dimensionally identical to `slip`, and therefore a fraction of
price. Corrected to `MAKER_NONFILL_SLIP` **inside** the division (`b066901`).
The two placements differ by `1/s` — 20× at a 5% stop, 200× at 0.5%.

**(5) GRANULARITY-BINDING SYMBOL.** SOL was named as the binding symbol on the
basis of **where each threshold sits** rather than **where each instrument sits
relative to its own threshold**. **ETH is binding:** one quantity step is worth
**$19.22 on ETH against $7.71 on SOL and $6.52 on BTC.** Corrected in `01281d3`.

**(6) THE ENGINE'S ROUNDING BEHAVIOUR WAS ASSERTED, NOT VERIFIED.** Report 17
claimed quantity *"rounds down"*. **The engine performs no quantity quantisation
at all** — `qty_step` is parsed, stored, serialised and printed, and never read
by sizing or execution. Routed to Point 5 (§6).

**(7) TRADE COUNTS UNDER CANDIDATE (a) ESTIMATED AT 80–150 PER FOLD. ACTUAL
MINIMUM 570.** Off by roughly 4–7×. The error came from applying a guessed
failure rate to a **close-based breakout base**, conflating **intrabar channel
breaks** (12.5–14.6% of bars) with **closes outside the channel** (~4%). Two
different populations under one name — the exact failure the §3.4 mitigation
warns about. **This estimate MOTIVATED the Donchian-10 timing decision, though
not its structural justification**, which stands independently: sweeps target
recent local liquidity, not multi-day boundaries.

**(8) EXCURSION GEOMETRY PREDICTED AT MEDIAN 0.8–1.4 ATR AND P90 ABOVE 2.25.**
**Actual median 0.63–0.77, P90 1.27–1.55.** The exposed tail at m = 2.25 is
**1–3%, not the ~10% anticipated.** The prediction was made from an intuition
about how large a sweep bar "must" be, rather than from the bar-range
distribution, which was already available.

**(9) THE WIN-RATE FIGURES.** **44.4% and 58.0%** were derived from an assumed
cost model — costs deducted from the R multiple at exit — while
`src/engine/costs.py` **explicitly rejected that model in its own docstrings**
(*"Sizing on (P − S) alone risks risk_usd PLUS costs"*; *"'2 × stop distance' is
NOT equivalent"*). The thesis's own §5.2 disclaimed the figure **by name** one
page before §6 used it. Corrected to **40.0% and 53.6%** by amendment 1
(`703046a`).

### 4.1 THE TRANSFERABLE LESSON

**Derive every criterion from the implementation or the measured range — never
from the quantity's name, its description, or an intuition about its size.**

**Where a quantity has a population, name the population in the same sentence as
the number.** Error (7) is the pure case: "breakout bars" meant two different
populations differing by 3×, and the ambiguity was invisible because both
readings were reasonable.

**And a new one, from error (9): a pessimistic number is not a validated
number.** All nine errors above but especially (9) ran in the **conservative**
direction — it overstated both win-rate bars by 4.4 percentage points. **A
conservative-looking figure attracts less scrutiny**, because the discomfort it
creates reads as rigour. The thesis even flagged 58% as a risk, which made it
*more* credible rather than less. **The check that catches these is not
scepticism about whether a number looks too good; it is deriving every number
from its implementation regardless of which direction it points.**

### 4.2 THE ONE PREDICTION THAT HELD

**The Donchian/RSI entailment was predicted to be STRUCTURAL AND SCALE-INVARIANT
BEFORE MEASUREMENT, and it was.** Report 20's brief stated the claim in advance —
both indicators are defined in bar units, so the relationship should not depend
on how long a bar is — and the measurement returned it: the population is
equally empty at 1h and 15m, and if anything **emptier at 1h**.

**It is recorded here for the same reason the nine failures are.** The Point 4
record §3.3 noted that its pre-registered expectation was wrong and that
recording it was what made the error legible. **The reverse case has to be
recorded on the same terms, or the record only ever documents failure and stops
being evidence about the process.**

---

## 5. PROCESS FINDINGS

### 5.1 THE READ-BACK PROTOCOL — five transfer defects in six returns

**Every on-disk file was clean. Every defect was introduced by REGENERATING
report contents in chat rather than READING THEM FROM DISK.** The observed
failures were: content duplication, section misordering, silent truncation, and
on one occasion **an entirely different report delivered under a correct commit
hash** — the hash matched, the content did not.

**The Point 4 record §3.6 covered the WRITE path only** ("terminal heredocs
corrupt long text"). The write path was fixed; the **read-back path was not**,
and it failed five times in six.

> **THE RULE: artifacts under review are transferred by FILE UPLOAD, not by
> pasting. The chat report-back carries only SHA-256, line count, commit hash
> and test count.**

A hash that matches proves the file on disk is correct. It proves nothing
whatever about a paste that accompanies it, and the two were repeatedly observed
to disagree.

### 5.2 ZERO-VALUED PLACEHOLDERS HAVE NO GUARD BY DEFAULT

`MAKER_NONFILL_COST_R` sat in **the wrong denomination**, invisible to **all 545
tests then in the suite**, because every one of them multiplied it by zero. A
constant at zero is numerically identical under any placement, so no test that
exercises it at its committed value can detect a structural error in where it
sits.

> **THE RULE: any placeholder committed at zero requires a PROBE-BASED test at
> construction time that sets it non-zero and pins the structural consequence.**

The fix that worked pins the term at **two** values of `s` and asserts the gap
between candidate placements scales as `(1/s − 1)` — a property no single
R-denominated constant can satisfy at both, so the test fails on the
**placement** rather than on the value.

### 5.3 PRE-COMMITTING THE RULE IN ITS OWN COMMIT WORKS

The timeframe rule was committed **alone** at `96c96cf` — one file, 88
insertions, nothing else — before any measurement code was written and before
any bar was read.

**It later emerged that the multiplier band's upper edge decided the outcome:**
15m would have been selected at any ceiling above 4.705, and the frozen ceiling
was 3.0. That is a judgement carrying the answer.

**Because the band was PROVABLY frozen first, that fact is a RECORDED
SENSITIVITY rather than a CONTAMINATION.** The same fact discovered about a
parameter chosen after the numbers were seen would have been fatal to the
selection. **The commit-alone discipline converted a potential contamination
into a disclosed limitation, which is the whole return on it.**

### 5.4 SYNTHETIC POSITIVE CONTROLS ARE REQUIRED FOR NULL RESULTS

**"We found nothing" is indistinguishable from "the detector is broken" without
one.** Report 20's headline was an empty population; report 21's trigger could
have been emptied silently by a single off-by-one in the Donchian shift.

Both reports therefore carry a **constructed instance of the thing being
searched for** — report 20 builds a crash, a flat 20-bar base and a small break
that fires at RSI 10.68; report 21 asserts a hand-specified bar that breaks and
closes back inside — plus a **negative control** that must NOT fire. Without the
positive control, an empty result is uninterpretable and an empty result was
exactly what both reports returned.

---

## 6. OPEN ITEMS, ROUTED

### 6.1 POINT 5 — risk and position sizing

- **THE ENGINE PERFORMS NO QUANTITY QUANTISATION.** `qty_step` is parsed,
  stored, serialised and printed, and **never read by sizing or execution**.
  Every backtest to date has sized in **unachievable fractional quantities**.
  **Floor is the only rounding direction that cannot breach the 1% rule;
  round-to-nearest and ceil both can.** Add a **realised-vs-intended risk
  provenance counter** so the gap is visible rather than assumed away.
- **ETH is the granularity-binding symbol.** Worst case **$0.96 of the $20 risk
  unit (4.81%)**, at a 5.00% stop.

### 6.2 VALIDATION DESIGN — the next document

- **`COST_TOLERANCE_R = 0.11`'s JUSTIFICATION IS OWED.** The value is frozen and
  is not in question; its *"one third of the ~0.34R minimum detectable edge"*
  derivation **presumed costs subtract from expectancy in R**, which under
  net-solved geometry they do not. **It must be re-argued BEFORE any performance
  figure is seen** — re-arguing it afterward would be selecting a justification
  to fit a result. *(amendment 1 §7.)*
- **The budget is ~10% conservative against its own headline.** Under
  cost-inclusive sizing the cost's realised share of the risk unit is
  `c/(s+c) = 0.0991R`, not `0.11R`. **RECORDED, NOT ACTED ON.** Loosening a
  frozen threshold because a re-derivation found slack is precisely what the
  amendment procedure exists to prevent.
- **Whether the majority-of-nine aggregation rule interacts badly with the
  pre-registered expectation** that the edge concentrates in ranging regimes
  (thesis §8.3). If fewer than five folds are predominantly ranging, the rule
  kills a real edge. That is the correct conservative failure and it is recorded
  as a known cost — but the interaction should be understood before it fires,
  not after.

### 6.3 POINT 6 — paper trading

- **`MAKER_NONFILL_SLIP` is zero and unmeasured.** It blocks any maker-entry
  variant, which would **drop the cost floor from 1.50% to 1.00%** — a material
  loosening of the admissibility line that cannot be claimed until the term has
  a value.
- **Realised funding against the 0.022R budget.** The 0.01%/8h rate is an
  **assumption, not a measurement**: Bitget history available to this project
  covers ~90 days against a three-year test window.

### 6.4 NOT PURSUED — recorded so they are not lost

- **The sweep rejection rate's invariance to channel length** (§3.5). A stronger
  regularity than the step needed, unexplained by anything measured.
- **Two-sided bar behaviour.** 86 / 59 / 32 bars per symbol at D10 across all
  nine training periods, at most 19 in one fold. **Skipped by rule** (thesis
  §4.1), not characterised, no claim made about them.
- **DIURNAL RVOL STRUCTURE.** Point 4 measured pass rates swinging **32–51
  percentage points by hour of the UTC day**. It was never used as a signal —
  only normalised away by the session baseline. **Available to a future
  hypothesis; explicitly OUT of this one.**

---

## 7. THE CONTAMINATION LEDGER, UPDATED

| period | status |
|---|---|
| **2022-01 → 2022-03** | **Warm-up only. Never traded.** Consumed by indicator warm-up in every measurement (114 bars at 1h ends 2022-01-05T18:00Z; fold 1 train begins 2022-04-01). |
| **2022-04 → 2024-12** | **SUBSTANTIALLY SPENT — and spent FURTHER by this point.** Reports 19, 20 and 21 all read it. |
| **2025-01 → 2026-07** | **ENTIRELY UNTOUCHED. Not one bar read.** |

**WHAT THIS POINT SPENT, SPECIFICALLY.** The **wick-and-reject population itself
has now been characterised on 2022–2024**: channel-break and signal counts, the
rejection rate, the full excursion-in-ATR distribution, bar range in ATR units,
per-fold signal counts, and floor-binding rates per symbol. Report 19 read ATR%
distributions across five timeframes; report 20 read RSI distributions on
breakout and all bars at two timeframes.

**No trade outcome was computed from any of it. But the trigger's structural
properties are now KNOWN from this window.**

> **CONSEQUENCE TO CARRY FORWARD: the thesis was designed with knowledge of this
> window's structural properties. No parameter was tuned on returns, and no
> return exists to have tuned on — but the design is NOT NAIVE to 2022–24.
> The holdout carries correspondingly more weight.**

This is stated plainly because it is the honest position, and because the
difference between "not tuned on returns" and "naive to the window" is exactly
the distinction that gets blurred when a result finally arrives.

---

## 8. HOW TO OPEN THE NEXT POINT

**A FRESH CHAT**, with **this document** and **the thesis** (`22` and `22a`)
uploaded as handoff. Not pasted — see §5.1.

**RECOMMENDED ORDER, with the reasoning stated:**

**FIRST — POINT 5, the quantity-rounding gap.** It is a **correctness fix on the
layer the validation will depend on**. Every backtest to date has sized in
fractional quantities the exchange would not accept, so every realised risk
figure the validation produces would inherit that gap. Fixing it after the
validation is designed means redoing the validation; fixing it first costs
nothing. **It is also small and well-specified**, which makes it a poor thing to
leave sitting behind a larger piece of work.

**THEN — POINT 4, the validation design for this thesis.** It carries the §6.2
open items as explicit agenda entries, and the `COST_TOLERANCE_R` justification
must be settled **inside it**, before any performance figure is inspected.

**THE STANDING WORKING RULES CARRY OVER UNCHANGED:**

- **One point at a time.**
- **Decisions before code.**
- **No code in chat.**
- **Claude Code prompts for anything built.**
- **Friction over compliance** — an objection raised is worth more than an
  instruction followed.
- **The §5.1 read-back protocol** — artifacts by file upload; the chat carries
  hash, line count, commit and test count only.

---

## 9. STATUS

**THE THESIS IS FROZEN** at `02e47a5`, as amended by amendment 1 at `703046a`.
Neither document may be edited. A further correction is Amendment 2, with its own
commit and its own statement of what changed and why.

**THE PERFORMANCE FIREWALL IS ARMED.** No expectancy, win rate, profit factor,
Sharpe, equity curve, `r_multiple` or `net_pnl` figure may be computed,
inspected or estimated **until the VALIDATION DESIGN is separately written,
agreed and committed.** The kill conditions are goalposts; the procedure that
applies them does not yet exist, and writing it after seeing a number would
defeat both.

**THE HOLDOUT REMAINS SEALED AND UNSPENT.** 2025-01-01 through 2026-07-26 has
never been read by any code path in this project.

**HOLDOUT BUDGET, UNCHANGED: ONE CANDIDATE, ONE LOOK, WHOLE WINDOW, NO CANDIDATE
TWO.**

---

**Point 1 (reopened) is closed. It produced a thesis and no result, which is
what it was reopened to do.**
