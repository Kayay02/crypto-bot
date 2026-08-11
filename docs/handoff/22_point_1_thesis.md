# POINT 1 (REOPENED) — THESIS SPECIFICATION, PRE-REGISTERED

**Status: FROZEN at this commit.** This document is committed ALONE, containing
nothing else. No code accompanies it, no data was read to write it, and no
quantity in it was computed from a trade outcome. **The commit hash is the proof
that the thesis preceded any result it will be judged by.**

**Context.** The Point 4 hypothesis was validated and killed
(`docs/handoff/16_point_4_closing.md`). Point 1 was reopened and has now
produced a new thesis. Section 8.3 of the closing record states that no Point 4
choice carries forward by default; every parameter below is either newly
specified here or inherited from an artifact named in §9 with its hash.

**Every number in this document is either (a) a design parameter fixed here,
(b) transcribed from a frozen artifact cited by hash, or (c) arithmetic on those
two.** Nothing is a measured performance figure, because none exists.

**Instruments.** Bitget USDT-M perpetual futures — BTCUSDT, ETHUSDT, SOLUSDT.
~$2,000 capital, $20 fixed risk per trade after costs. Timeframe 1h.

---

## 1. THE CLAIM

**In plain English.**

Traders place stop-loss orders where they can be reasoned about — just beyond
the most recent visible high or low. Because that reasoning is common, the
orders accumulate in the same place. A **cluster of resting stop orders forms
beyond a recent visible extreme.**

When price reaches that cluster, the stops trigger. Each triggered stop is a
market order in the direction of the move, which pushes price further, which
triggers more stops. The result is a **self-reinforcing cascade**: a fast,
convincing move through the level on real volume.

**At the moment of the break, that cascade is indistinguishable from a genuine
breakout.** Both look identical — the level gives way, price accelerates
through it, and the move is real. Nothing available at the instant of the break
separates the two.

**They become distinguishable at the bar close.** A genuine breakout is
sustained by continuing demand and tends to close beyond the level. A cascade is
sustained only by the stops it is consuming; when they are exhausted there is
nothing left to carry price, and it returns inside the level within the bar.

**THE CLAIM:** *a bar that reaches beyond a recent extreme and closes back
inside it is more likely to be followed by movement AWAY from that extreme than
by continuation through it.*

The bar close is doing the work. It is the first moment at which the two
explanations for the same move separate, and the trigger in §4 is nothing more
than a statement of that separation in indicator terms.

---

## 2. WHY AN EDGE SHOULD EXIST

**These are ARGUMENTS, not findings.** Nothing below has been measured. They are
recorded here so that the reasoning which motivated the thesis is fixed in
advance and can be judged against the outcome rather than reconstructed after
it. An argument that survives a failed result is a rationalisation.

**2.1 The absorbing counterparty is structurally identifiable and positioned
against the sweep.** For the cascade to stop, someone must have absorbed the
stop orders. That is not a diffuse "the market"; it is whoever took the other
side of a burst of market orders at a price they were willing to hold. Their
position is by construction opposite to the direction of the sweep, and it was
established at a price they chose. Unlike most counterparty reasoning, this one
identifies both the side and the level, which is why the shape is worth trading
rather than merely observing.

**2.2 The order flow that caused the move is spent.** Stopped-out traders are
flat. They are not holding a position that must later be exited in the same
direction, so the flow that produced the move cannot produce it again. A genuine
breakout leaves behind participants who may add; a stop cascade leaves behind
participants who have nothing left to do. The move consumed its own fuel.

**2.3 The edge should survive being known.** Most patterns decay once
identified, because the behaviour producing them is discretionary and can be
withdrawn. **Stops are not discretionary.** They are placed for risk management,
not prediction — the trader placing one is not forecasting that the level will
hold, they are bounding a loss if it does not. Risk management does not stop
being necessary because the resulting liquidity is known to be harvestable, and
the alternative — not placing a stop — is worse for the trader placing it. The
supply of clustered stops is therefore structural rather than fashionable.

**2.4 It is the OPPOSITE claim to Point 4's, not a repair of it.** Point 4
traded continuation through a Donchian breakout and was killed. This thesis
trades reversal against the same class of event. **This is deliberate and it is
the point.** Section 4 of the closing record forbids patching the dead strategy;
a thesis that inverted one parameter of it would be a patch. Inverting the
*claim* is not. If Point 4's population was systematically resolving against its
own direction, the failure of that hypothesis is evidence for this one — but
that inference is stated as motivation, **not as support**, because Point 4's
trigger, timeframe and stop rule all differ from what is specified below, and
its result cannot be transferred.

### 2.5 WHERE THIS SHOULD FAIL — pre-registered

**In strongly trending regimes.** When a market is genuinely trending, breaks of
recent extremes are more often real continuation than liquidity events. Those
genuine breakouts will still sometimes close back inside the channel — from
volatility, from a single large seller, from noise — and will enter the trigger
population indistinguishably. **The reversal population is polluted by genuine
breakouts in exactly the conditions where genuine breakouts are common.**

The expectation is therefore that the edge, if it exists, is **concentrated in
ranging and mean-reverting conditions and weak or absent in trending ones.**

**UNIFORMITY ACROSS REGIMES SHOULD BE TREATED AS MORE SUSPICIOUS THAN
CONCENTRATION.** A mechanism that works identically everywhere is not behaving
like the mechanism described in §1, which is explicitly about which of two
explanations generated a move — and the mix of those two explanations is exactly
what a regime is. A flat result across regimes is more likely to indicate that
something other than the stated mechanism is producing it.

This is recorded now because the Point 4 closing record §3.3 notes that its
pre-registered expectation was wrong and that recording it was what made the
error legible. The same applies here: **if the result comes back uniform, this
paragraph is the evidence that uniformity was not what was expected**, and it
must not be reinterpreted as confirmation.

---

## 3. INDICATORS

Two. Both are frozen.

**DONCHIAN-10 — locates the liquidity pool.** The channel over the prior 10
bars, excluding the current bar. **It is a STRUCTURAL MARKER, NOT A TREND
SIGNAL.** Its job is to identify where market participants can see a recent
extreme and would therefore have placed stops beyond it. It is not used to
establish direction, momentum, or trend state, and nothing in §4 reads it as
such. N = 10 was fixed as a one-time structural choice — sweeps target recent
local liquidity, not multi-day boundaries — and is frozen.

**ATR(14), Wilder — sets stop and target.** Price-unit volatility, used only for
distance. It plays no part in signal generation.

### 3.1 NO OSCILLATOR

**No RSI, no stochastic, no oscillator of any kind is in this specification.**

Report 20 (`02acbcf`) established that **RSI is entailed by channel position and
carries no independent information at the trigger.** Measured over 2022–2024 at
1h, the minimum RSI on a long Donchian breakout bar was 50.85 / 52.98 / 49.48
across the three symbols and the first percentile never reached 50, while the
unconditional distribution over all bars is centred on 50 with a fifth
percentile near 30. The channel condition alone determines the oscillator's
value. **A gate on RSI would reject nothing and would cost a term in the
specification for no information.**

That result is about a close-based breakout rather than this trigger, and the
entailment is not claimed to transfer term for term. **The transferable finding
is the one that matters here:** oscillator readings at a channel event are
largely a restatement of the channel event. Adding one would risk measuring the
same thing twice under a second name.

### 3.2 NO VOLUME INDICATOR — A DELIBERATE DEPARTURE FROM THE ORIGINAL BRIEF

**No RVOL, no volume gate, no volume confirmation term.**

**The reasoning.** The wick-and-reject shape **is itself an absorption statement,
expressed in price.** For price to travel beyond the extreme and return inside
within one bar, something must have absorbed the flow that carried it out —
that is what §2.1 identifies as the counterparty. The shape does not merely
correlate with absorption; it is what absorption looks like when written in
OHLC. **A volume gate would measure the same event a second time, in a second
unit, at the cost of discarding signals that failed the second measurement while
passing the first.**

**THIS IS A DEPARTURE FROM THE ORIGINAL PROJECT BRIEF, WHICH ASKED FOR VOLUME TO
BE CENTRAL. THE DEPARTURE IS DELIBERATE AND IS RECORDED HERE RATHER THAN LEFT
IMPLICIT.**

Two things support it, and both are stated as reasons rather than proofs:

- Point 4's RVOL gate was measured to do **volatility selection, not edge
  detection** (closing record §2.2). It selected for larger bars, which is a
  property the trigger here already has by construction — so the same gate would
  be even more redundant against this trigger than it was against that one.
- A gate that costs signals must earn them back in selectivity. The pre-fold
  counts in report 21 (`aea6b5c`) are healthy (§6), but they are not so large
  that a term with no argued-for independent content should be spending them.

**The cost of being wrong about this is stated plainly:** if the thesis fails,
"we did not gate on volume" is an available explanation, and this section is
what makes that explanation checkable rather than convenient. **Volume is not
forbidden forever; it is excluded from THIS specification.** Reintroducing it
would be a new hypothesis requiring its own pre-registration, not an amendment
to this one.

---

## 4. SIGNAL SPECIFICATION

**Evaluated at BAR CLOSE. The Donchian window EXCLUDES the current bar.**

    upper[T] = max( high[T-10] ... high[T-1] )
    lower[T] = min( low[T-10]  ... low[T-1]  )

**LONG SIGNAL at bar T:**

    low[T]   <  lower[T]        the extreme reaches beyond the channel intrabar
    close[T] >  lower[T]        the close returns INSIDE the channel

**SHORT SIGNAL at bar T — the exact mirror:**

    high[T]  >  upper[T]
    close[T] <  upper[T]

**Strictness: all four comparisons are STRICT.** A low exactly on the prior
minimum has not reached beyond the channel; a close exactly on the level has not
returned inside it.

**The exclusion convention is load-bearing.** If the current bar were inside its
own lookback window, `low[T] < lower[T]` would be strictly unsatisfiable and the
population would be empty rather than merely distorted. Report 21 (`aea6b5c`)
carries the guard.

### 4.1 TWO-SIDED BARS ARE SKIPPED

**If both the long and the short conditions fire on the same bar, NO TRADE IS
TAKEN.** Such a bar sweeps and rejects both channels — an outside bar that
reached beyond the prior high and the prior low and closed between them.

**This is chosen for DETERMINISM over any side-selection rule.** Any rule for
picking a side — larger excursion, closer close, direction of the prior bar —
would be a new discretionary parameter introduced at the moment it is least
justifiable, and it would be fitted on a handful of bars. Skipping is
unambiguous, requires no parameter, and cannot be tuned.

**The cost of skipping is small and is quantified in advance.** Report 21
measured these bars at Donchian-10 across all nine training periods: **86
(BTCUSDT), 59 (ETHUSDT), 32 (SOLUSDT)**, at most 19 in any single fold, against
per-fold signal counts in the high hundreds. **They are not characterised
further and no claim is made about them.**

### 4.2 ENTRY — FROZEN

**ENTRY IS AT THE CLOSE OF THE SIGNAL BAR, AS A TAKER.** No next-bar entry, no
limit order, no retracement entry, no confirmation bar.

**RECORD THIS EXPLICITLY: the entire excursion geometry in report 21
(`aea6b5c`) is CONDITIONAL ON THIS REFERENCE.** Every figure in that report's
Part C measures the distance from the signal bar's close to the swept extreme.
If the entry reference is ever changed — to the next bar's price, to a
retracement, to anything other than the signal bar's close — **the geometry
check does not carry over and must be rerun before the stop rule can be
considered consistent.** This is the reason entry is frozen here rather than
left open: an unfrozen entry reference silently invalidates an already-committed
result.

All-taker is also the cost assumption the floor in §5 rests on (report 18,
`d850ac4`). Entry style and cost model are the same decision.

---

## 5. STOP, TARGET, EXITS

### 5.1 STOP

**STOP = 2.25 × ATR(14) from entry, with a 1.50% floor.** The stop distance is
`max(2.25 × ATR, 1.50% of entry)`.

**THE FLOOR'S STATUS, STATED HONESTLY.**

**It is a COST-ADMISSIBILITY CONSTRAINT, NOT A RARELY-FIRING RAIL.** The 1.50%
figure is the all-taker slippage-headroom floor from report 18 (`d850ac4`,
`01281d3`), derived from `COST_TOLERANCE_R = 0.11`. A stop tighter than it
cannot carry the cost budget. It is not a safety net for outliers; it is the
line below which the trade is not worth taking at all.

**MEASURED BINDING RATES on the wick-and-reject population** (report 21,
`aea6b5c`, 1h, 2022-01-01 to 2024-12-31):

| symbol | floor binds on signals | floor binds on ALL bars | median 2.25 × ATR |
|---|---:|---:|---:|
| BTCUSDT | **46.15%** | 46.21% | 1.578% |
| ETHUSDT | **29.43%** | 29.76% | 1.913% |
| SOLUSDT | **3.09%** | 3.14% | 3.122% |

**On BTCUSDT the floor sets the stop on nearly half of all signals.** It is not
an edge case there; it is close to being the stop rule. On SOLUSDT it is a
genuine rail at 3%. ETHUSDT sits between.

**REPORT 21 REFUTED THE PREMISE THAT WICK-AND-REJECT BARS ARE A HIGH-ATR
SUBSET.** The prediction had been that these bars, being large, would sit clear
of a percentage floor. They do not: BTC binding is **46.15% on signals against
46.21% on all bars — a difference of 0.05 percentage points.** ETH differs by
0.33 points and SOL by 0.06.

**Why the premise was wrong.** The trigger selects on **RELATIVE range** — the
bar's size measured against its own ATR, where wick-and-reject bars run
1.23–1.54× typical. **That criterion is scale-free, and is therefore nearly
orthogonal to the ATR LEVEL**, which is what a percentage floor compares
against. Selecting for `range / ATR` says almost nothing about `ATR / close`.
**Any future argument of the form "these bars are volatile, therefore X about a
percentage threshold" is unsound and this paragraph is the reason.**

**WHEN THE FLOOR BINDS, THE STOP IS WIDER THAN THE ATR RULE WOULD SET.** Two
consequences follow, both favourable, and both are stated so that the high
binding rate is not misread as a defect:

- **Cost-in-R falls.** A wider stop means a given round-trip cost is a smaller
  fraction of the risk unit.
- **Extreme coverage rises.** Report 21's finding that a 2.25 × ATR stop clears
  the swept extreme on 97.1–99.2% of signals is therefore a **LOWER BOUND** on
  realised coverage; the floor makes the geometry safer, not riskier.

**FLOOR BINDING RATE IS A PRE-REGISTERED MONITORED QUANTITY.** It is reported
**per fold**, per symbol, as a fraction of trades taken. It is monitored because
a design in which one symbol's stop is set by a constant nearly half the time is
a design where "2.25 × ATR" describes BTCUSDT only partially, and that has to be
visible in the record rather than discovered later. Kill condition (d) in §7
turns on the same stratification.

### 5.2 TARGET

**TARGET = 1.5 × the stop distance, solved NET OF COSTS.**

The reward-to-risk is 1:1.5 in **realised, after-cost** terms, not in gross
price distance. The target price is solved so that a target exit returns 1.5
risk units after the round-trip cost is deducted, rather than placed at 1.5×
the gross stop distance and allowed to net out to less. Stating it this way
matters because the cost budget is 0.11R (§6) — a target placed gross would
deliver ~1.39R net and the breakeven arithmetic in §6 would not describe the
system being run.

### 5.3 TIME EXIT — A FUNDING GUARD RAIL

**DENOMINATED IN FUNDING SETTLEMENTS, NOT BARS.**

**THE RULE: the position is closed at the CLOSE OF THE BAR PRECEDING THE THIRD
FUNDING SETTLEMENT AFTER ENTRY.** n = 3.

**THE DERIVATION.** Funding paid, expressed in risk units:

    funding_in_R = (rate × n) / s

with `rate` the per-settlement funding rate, `n` the number of settlements
crossed, and `s` the stop distance as a fraction of entry. Setting a budget of
**0.022R — 20% of `COST_TOLERANCE_R` = 0.11** — at an assumed rate of **0.01%
per 8h** and **s = 1.50%**:

    n = 0.022 × 0.0150 / 0.0001 = 3.3   ->   ROUNDED DOWN to n = 3

**Rounded DOWN, not to nearest.** Rounding up would exceed the budget the rule
was derived from.

**s = 1.50% IS THE FLOOR, NOT THE TYPICAL STOP.** The median 2.25 × ATR is
**1.578% / 1.913% / 3.122%** (BTC / ETH / SOL, report 21), which would give
**n = 3.5 / 4.2 / 6.9** respectively. **The floor is used deliberately, because
it is the BINDING case and yields the tightest n across all three symbols.** A
rule derived from the median would be too loose for exactly the trades where
funding is most expensive in R terms — the tight-stop ones — and would differ
per symbol, which a guard rail must not.

**ELAPSED HOLD IS 16–24 HOURS, NOT 24.** Funding settles at fixed UTC times
every 8 hours. The elapsed time to the third settlement therefore **depends on
where entry falls within the 8-hour cycle**: entering just after a settlement
gives close to 24 hours, entering just before one gives close to 16. **The rule
is defined in settlements and the elapsed time is a consequence, not a
parameter.** Quoting a single figure would misdescribe the rule and would invite
someone to reimplement it in bars.

**THE JUSTIFICATION IS FUNDING COST ONLY.**

**A THESIS-DECAY JUSTIFICATION WAS CONSIDERED AND IS EXPLICITLY REJECTED.** It
would have said: the sweep's information content decays, so exit when it is
spent. It is rejected for two reasons, both structural:

- **It would violate the guard-rail principle.** A time exit justified by edge
  decay is denominated in the same unit as the mechanism it is supposed to
  guard. A guard rail must be independent of what it guards, or it stops being a
  rail and becomes a component of the strategy — and then it must be swept,
  justified, and defended on performance, which is precisely what a rail exists
  to avoid.
- **It would MANUFACTURE the holding-time distribution it is measured against —
  the Point 4 §2.1 failure.** Point 4's bar-21 checkpoint was found to CREATE
  the holding-time mode rather than catch one, and `time_stop` became the
  dominant exit at 45–83% of trades while removing it improved expectancy. A
  horizon chosen because the edge "should" be gone by then guarantees that
  trades end when the horizon says so, and the resulting distribution then
  appears to confirm the choice. **Funding cost is measurable independently of
  the trade's outcome; edge decay is not.** That is the whole distinction.

Kill condition (e) in §7 exists because this rail can still fail even when
correctly justified.

**THE 0.01% RATE IS AN ASSUMPTION, NOT A MEASUREMENT.** Bitget funding history
available to this project covers roughly **90 days** against a **three-year**
test window. The rate cannot be verified over the period being tested. **0.01%
per 8h is the venue's baseline and is used as a stated assumption.**

**REALISED FUNDING IS A PRE-REGISTERED MONITORED QUANTITY**, reported per fold
alongside the binding rate. If realised funding materially exceeds the 0.022R
budget, n = 3 was derived from a wrong input and the derivation — not the
result — is what must be revisited.

---

## 6. COST AND DETECTABILITY POSITION

| quantity | value | source |
|---|---:|---|
| cost budget `COST_TOLERANCE_R` | **0.11R** | report 17 / 18 (`a9a4c76`, `b066901`) |
| stop floor, all-taker | **≥ 1.50%** | report 18 (`d850ac4`, `01281d3`) |
| slippage question closed for stops | **≥ 1.00%** | report 18 (`d850ac4`) |
| reward-to-risk | **1 : 1.5** net | §5.2 |
| **breakeven win rate at 1:1.5** | **44.4%** | arithmetic, below |
| **win rate required for E = 0.34R** | **58.0%** | arithmetic, below |
| worst TRAIN fold signal count | **570** vs 200 minimum | report 21 (`aea6b5c`) |
| worst TEST fold signal count | **281** vs 50 minimum | report 21 (`aea6b5c`) |

**The arithmetic, so it is checkable by hand.** With a round-trip cost of 0.11R
charged against both outcomes, a winner returns `1.5 − 0.11 = 1.39R` and a loser
costs `1.0 + 0.11 = 1.11R`:

    breakeven:  p(1.39) = (1 − p)(1.11)   ->   p = 1.11 / 2.50 = 0.444
    E = 0.34R:  p(1.39) − (1 − p)(1.11) = 0.34
                2.50p = 1.45              ->   p = 0.580

**These are DESIGN TARGETS derived from frozen cost parameters. They are not
measurements and no performance quantity has been computed.**

### 6.1 WHAT THIS SECTION DOES AND DOES NOT ESTABLISH

**58.0% is the number this thesis must earn.**

**NOTHING MEASURED SO FAR SUPPORTS IT.** Not one figure in reports 17 through 21
speaks to win rate, expectancy, or edge of any kind. Report 19 selected a
timeframe on ATR distributions. Report 20 closed an oscillator question on
indicator distributions. Report 21 established that the stop geometry does not
contradict the trigger, that signal counts are sufficient, and that the cost
floor binds more often than expected. **Every one of those is a statement about
BARS.**

**EVERYTHING TO THIS POINT ESTABLISHES ADMISSIBILITY, NOT EDGE.** The work so
far has shown that this design *can* be tested — that it clears the cost floor,
produces enough signals per fold to measure, and is internally consistent
between trigger and stop. **It has shown nothing whatsoever about whether it
works.** A 58% win rate on a 1h intraday trigger is a high bar, and the honest
position at this commit is that there is no evidence for it.

---

## 7. PRE-COMMITTED KILL CONDITIONS

**These are GOALPOSTS. They are fixed at this commit and may not be moved,
softened, or reinterpreted in light of any result.**

**(a) OUT-OF-SAMPLE EXPECTANCY.** Out-of-sample expectancy ≤ 0 after costs on a
symbol → **that symbol fails.**

**(b) TWO-OF-THREE.** A symbol qualifies only if it passes on its own **AND** at
least one other symbol shows the same direction of edge, defined as **expectancy
exceeding zero by at least 0.05R.**

**(c) THESIS-BACKWARDS.** If continuation — entering WITH the sweep direction —
outperforms reversal on the same trigger population, **the mechanism is refuted
regardless of absolute expectancy.** A profitable strategy whose stated
mechanism runs backwards is not this thesis; it is an unexplained result wearing
this thesis's name.

**(d) FLOOR-STRATUM DECOMPOSITION.** Stratify trades by whether the 1.50% floor
bound. **If the advantage does not survive among NON-floor-bound trades at
≥ 0.05R, the thesis is about percentage stop width rather than about sweeps.**
Given the binding rates in §5.1 — 46.15% on BTCUSDT — this is not a remote
possibility and is the condition most likely to bite.

**(e) TIME-EXIT DOMINANCE.** **If time exits exceed 40% of trades, the
target-to-horizon relationship is mismatched as in Point 4, and the design is
REFUTED, NOT REPAIRED.** Point 4's `time_stop` reached 45–83% of exits; that was
diagnosed as the wrong SHAPE rather than a patchable bug. The same diagnosis
applies here and no adjustment of n, target, or horizon is permitted as a
response.

**(f) TRAINING-FOLD COHERENCE.** **If more than half of admissible grid points
have negative TRAINING expectancy, the strategy fails to fit before it fails to
generalise.** A design that cannot produce a positive result on data it was
allowed to see is not a generalisation problem.

### 7.1 AGGREGATION RULE — APPLIES TO EVERY CONDITION ABOVE

**EACH CONDITION IS EVALUATED AT THE FOLD LEVEL AND AGGREGATED BY MAJORITY
ACROSS THE NINE FOLDS. PER-FOLD FIGURES ARE REPORTED IN EVERY CASE.**

A condition is met if it is met in **at least five of the nine folds**. No
condition is evaluated on pooled data alone, and no condition is evaluated on a
single fold.

**This is stated to avoid the Point 4 §4.2 omission.** There, the kill
conditions carried no aggregation rule over the offset axis, SOL's entire result
turned on which reading applied, and **a verdict was nearly decided by
accident** — the second such near-miss in that project. The rule is written here
before any fold exists in a result, so that no reading can be selected after the
fact.

**Note on the folds themselves:** the nine folds overlap by 50% in their
training windows and are a **stability probe, not nine independent trials**
(`src/folds/schedule.py`). Majority across them is a consistency requirement,
not a significance test, and must not be reported as one.

---

## 8. KNOWN RISKS, RECORDED BEFORE ANY DATA

**8.1 THE REPORT 21 EXCURSION RESULT IS ONE-SIDED.** It established that the
stop clears the signal bar's **OWN** extreme on 97–99% of signals. **It says
NOTHING about price revisiting that extreme on a LATER bar.** The check
established internal consistency between trigger and stop — that the stop is not
placed inside the structure the trigger identifies — and nothing more. A stop
clearing the signal bar's extreme can still be hit on any subsequent bar, and
how often that happens is a forward-looking quantity that has not been measured
and is firewalled until the validation design is committed. **Reading report 21
as evidence that the stop will survive is a misreading, and it is a misreading
this document exists partly to prevent.**

**8.2 58% IS A HIGH BAR AND ARCHETYPE PLAUSIBILITY IS NOT EVIDENCE.** The
liquidity-sweep mechanism in §1 is a recognisable and widely described market
archetype. That is a reason to test it; **it is not a reason to expect it to
work.** Widely described patterns are widely traded, and §2.3's argument that
this one should survive being known is an argument, not a result. The required
58.0% win rate is high for any intraday trigger, and no measured quantity
currently points toward it.

**8.3 REGIME DEPENDENCE IS EXPECTED, AND THE AGGREGATION RULE COULD KILL A REAL
EDGE.** §2.5 pre-registers the expectation that the edge concentrates in ranging
conditions. The majority-across-folds rule in §7.1 requires the edge to appear in
five of nine folds. **If the edge is real but concentrated in ranging
conditions, and fewer than five folds are predominantly ranging, the rule kills
a real edge.**

**This is the CORRECT CONSERVATIVE FAILURE and it is recorded as a KNOWN COST OF
THE RULE.** The alternative — permitting a pass on a minority of folds — would
allow any result to be rescued by selecting the folds that agree with it, which
is the failure mode the rule exists to prevent. **Accepting a higher false-
negative rate to eliminate a class of false positives is a deliberate trade, and
if this thesis dies by it, that outcome was chosen in advance, here, and is not
grounds for re-running with a different rule.**

---

## 9. PROVENANCE

Every artifact this thesis rests on, frozen, with its commit hash.

| artifact | what it fixed | commit |
|---|---|---|
| Timeframe selection rule, pre-registered | admissibility rule; multiplier band [1.0, 3.0]; finest-admissible selection | **`96c96cf`** |
| Report 19 — timeframe selection | **1h selected**; ATR% distributions per symbol per timeframe | **`74e3ca9`** |
| Report 17 second pass — cost envelope | slippage-leg model corrected; admissibility line | **`a9a4c76`** |
| Non-fill term unit resolved | price fraction, structurally enforced | **`b066901`** |
| Report 18 — slippage lower bound | **1.50% all-taker floor**; slippage closed above 1.00% stops | **`d850ac4`** |
| Granularity — binding symbol | ETH is binding, not SOL; the engine does not round | **`01281d3`** |
| Report 20 — RSI / 1R.5 closure | **oscillator carries no independent information**; 1R.5 closed STRUCTURAL | **`02acbcf`** |
| Report 21 — sweep population and geometry | rejection rate; per-fold counts; **stop clears extreme on 97–99%**; floor binding rates | **`aea6b5c`** |
| Point 4 closing record | what killed it; §2.1 time-stop failure; §4.2 aggregation omission | `docs/handoff/16_point_4_closing.md` |
| Fold architecture | nine folds, rolling 6m train / 3m test; `folds.json` tracked | `data/derived/folds/folds.json` |

---

## 10. STATUS

**THIS THESIS IS FROZEN AT THIS COMMIT.** It may not be edited in light of any
subsequent measurement. An amendment is a new document with a new commit and an
explicit statement of what changed and why; a silent edit is a contamination
event.

**THE PERFORMANCE FIREWALL IS ARMED.** No expectancy, win rate, profit factor,
Sharpe, equity curve, `r_multiple` or `net_pnl` quantity may be computed,
inspected, estimated or referenced for this hypothesis **until the VALIDATION
DESIGN is separately written, agreed and committed.** That design is the next
document, not the next measurement. The kill conditions in §7 are goalposts; the
procedure that applies them does not yet exist and writing it after seeing a
number would defeat both.

**THE HOLDOUT REMAINS SEALED AND UNSPENT.** 2025-01-01 to 2026-07-26 has never
been read — not one bar — by any code path in this project.

**HOLDOUT BUDGET: ONE CANDIDATE, ONE LOOK, WHOLE WINDOW, NO CANDIDATE TWO.**
The holdout is evaluated exactly once, on a single candidate selected entirely
without reference to it, over the whole window. There is no second candidate, no
second look, and no partial evaluation. If the candidate fails, the holdout is
spent and the answer is the answer.

---

**Committed alone. No code, no measurement, no data access. The commit hash is
the proof that this thesis preceded any result it will be judged by.**
