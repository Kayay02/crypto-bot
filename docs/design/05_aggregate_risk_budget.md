# AGGREGATE OPEN RISK BUDGET — PRE-REGISTERED

**Status: FROZEN at this commit.** This document is committed ALONE with the
constants module it specifies and the test that binds the two together. It
contains no measurement, reads no market data, touches no engine file, and
states no number about its own consequences. **The commit hash is the proof that
the rule preceded the cost of applying it.**

**Point 5, sub-point 5.2, step 2.**

**WHY THIS IS COMMITTED FIRST, AND ALONE.** Report 24 (`4e08e1b`) measured that
the uncapped book carries a median of nine concurrent positions. Report 25
(`e735295`) established that **the venue imposes no relevant limit** — tier 1
permits 150× / 150× / 100× and the entire measured book sits inside it, with the
nearest tier boundary 1.85× beyond the worst bar ever measured. **There is
therefore no exchange fact that decides this number.** It is a risk-appetite
choice.

**A risk-appetite choice made after seeing what it discards is not a choice.**
If the level were set after measuring the skip rate, it would be fitted to
preserve statistical power, and no later argument could distinguish "6% is the
right tolerance" from "6% is what left enough trades to measure". This follows
the precedent of `96c96cf`, where the timeframe admissibility rule was committed
alone before the measurement code that applied it existed; the closing record
§5.3 records that the discipline converted an outcome-deciding parameter into a
**disclosed sensitivity rather than a contamination**, and that is the whole
return on it.

**THE COST OF THIS RULE IS MEASURED IN STEP 3.** Nothing in this document
estimates the skip rate, the surviving signal count, or the concurrency
distribution under the cap. Report 24's occupancy tables were not consulted to
set the level, and the one figure from report 24 that does appear here (§2) is a
directional composition statistic, not a count of anything this rule would skip.

---

## 1. THE RULE

> **AGGREGATE OPEN NOMINAL RISK ACROSS THE WHOLE BOOK — ALL THREE SYMBOLS
> COMBINED, NOT PER SYMBOL — MAY NOT EXCEED $120.00, BEING 6.0% OF $2,000.00.**

**THE BOOK, NOT THE SYMBOL.** The constraint binds on the sum across BTCUSDT,
ETHUSDT and SOLUSDT. There is **no per-symbol sub-budget** and none is implied:
a per-symbol cap would permit three simultaneous one-symbol maxima and would
therefore be a weaker constraint wearing a stricter name. All three instruments
are correlated majors and the budget treats them as one exposure.

**NOMINAL RISK** is the risk unit the position-sizing rule solves for:
`RISK_PER_TRADE_USD` per open position. Amendment 1 (`703046a`) §3 establishes
that the engine sizes cost-inclusively so that a stop-out returns exactly
−1.0R — exactly `RISK_PER_TRADE_USD` — up to one tick of rounding, always away
from the position. **So $120 is the modelled loss if six open positions all stop
out**, and it is nominal in the precise sense that it is what the sizing rule
solves for, not a guarantee about fills in a fast market.

**THE CANONICAL VALUES.** This block is the specification; `src/risk/budget.py`
transcribes it and `tests/test_risk_budget.py` asserts the two agree
character-for-value. **A transcription drift must fail a test, not survive as a
discrepancy.**

```
MAX_AGGREGATE_OPEN_RISK_USD = 120.00
RISK_PER_TRADE_USD          = 20.00
ACCOUNT_CAPITAL_USD         = 2000.00
BUDGET_FRACTION_OF_CAPITAL  = 0.06
FULL_SIZE_POSITIONS         = 6
MARGIN_MODE                 = "cross"
POSITION_MODE               = "hedge"
```

In prose, so the numbers appear twice and must agree twice: the budget is
**$120.00**, risk per trade is **$20.00**, capital is **$2,000.00**, the budget
is **6.0%** of capital, and it funds **6** concurrent full-size positions.

**`BUDGET_FRACTION_OF_CAPITAL` AND `FULL_SIZE_POSITIONS` ARE DERIVED, NOT
CHOSEN.** They are `120.00 / 2000.00` and `120.00 / 20.00`. Both divisions are
exact, and the module refuses to import if either stops being exact.

---

## 2. THE DERIVATION — A JUDGEMENT, NOT A RESULT

**THE ARGUMENT, STATED IN FULL SO IT CAN BE ATTACKED:**

1. The project's stated tolerance for peak-to-trough decline is **30–50%**.
2. A **single maximally correlated adverse event** — one in which every open
   position stops out together — is permitted to consume **at most one fifth of
   the conservative end** of that tolerance.
3. `30% / 5 = 6%`, and `6% × $2,000 = $120`.

**WHY THE ALL-STOP-TOGETHER CASE IS TREATED AS REACHABLE RATHER THAN
HYPOTHETICAL.** Report 24 §7.4 measured that **20.51% of occupied bars carry a
book that is entirely one-sided** — every open position in the same direction —
across three correlated majors, at a median concurrency of nine. One occupied
bar in five is already the shape the event requires. **The correlated case is
not a tail assumption about this strategy; it is a fifth of its ordinary
operation.** No correlation, covariance or joint-move quantity has been computed
anywhere in this project, and none is computed here — the 20.51% is a
directional composition count, and it is used as a reason to take the case
seriously rather than as an estimate of its probability.

### 2.1 THIS IS A PREFERENCE WITH AN ARGUED RATIONALE. IT IS NOT DERIVED.

**NO DERIVATION FROM ALREADY-FROZEN QUANTITIES PRODUCES THIS NUMBER, AND NONE IS
CLAIMED.** `COST_TOLERANCE_R = 0.11`, the 1.50% stop floor, `n = 3` settlements,
the 1:1.5 reward-to-risk and the $20 risk unit are all frozen upstream, and
**not one of them constrains aggregate concurrent exposure.** They are per-trade
quantities; this is a book-level one, and the two are formally independent.

**Three of the three inputs above are judgements:**

| input | status |
|---|---|
| the 30–50% tolerance | **operator preference. NOT RECORDED IN ANY COMMITTED ARTIFACT.** It comes from the design discussion; a search of `docs/` and `reports/` finds no prior statement of it. It is written down here for the first time, which is itself part of what this commit does. |
| "at most one fifth" | **a judgement, and the only free parameter in the derivation.** Nothing derives the fifth. At one quarter the budget would be $150 and seven and a half positions; at one sixth, $100 and five. |
| taking 30% rather than 50% | **a judgement in the conservative direction**, chosen so the rule is set against the tolerance the operator would actually be uncomfortable exceeding rather than the one they would tolerate at the limit. |

**THE SENSITIVITY IS RECORDED NOW, BEFORE IT MATTERS.** The closing record §4.1's
transferable lesson is to derive every criterion from its implementation or its
measured range and never from a quantity's name — and this criterion **cannot**
be so derived, because no measured range for it exists. **The honest position is
that $120 is a stated preference, defensible but not unique, and that a
different operator could defend $100 or $150 on the same reasoning.** Writing
that here, before the skip rate is known, is what makes it a disclosed
judgement rather than a rationalisation.

**THE THIRTY-PER-CENT FIGURE IS NOT A MEASUREMENT AND MUST NOT BECOME ONE.** It
is a tolerance the operator states in advance. **It is not a prediction about
this strategy**, no decline of any size has been computed for this or any
hypothesis, and the performance firewall forbids computing one until the
validation design is committed.

---

## 3. THE ALLOCATION RULE

**SIGNALS ARE ALLOCATED IN ARRIVAL ORDER.**

    for each signal, in the order it arrives:
        remaining = MAX_AGGREGATE_OPEN_RISK_USD - (open nominal risk)
        allocation = min(RISK_PER_TRADE_USD, remaining)
        if the resulting order is NOT VIABLE:  SKIP the signal
        otherwise:                             OPEN at `allocation`

**A skipped signal is skipped, not queued, not deferred and not resized upward
later.** It does not become eligible when the budget frees; the decision is made
once, at arrival, and it is final. A queue would be a second mechanism with its
own parameters and would make the traded population depend on how long a signal
is allowed to wait.

**When a position closes it returns exactly its own allocation to the budget**,
and nothing else. There is no accrual of profit into the budget and no reduction
of it on a loss: the budget is denominated in the nominal risk unit, which is
fixed per trade by construction, so a closing position releases what it took.
**This is what makes the budget a cap on concurrent exposure rather than on
cumulative exposure.**

### 3.1 VIABILITY — both conditions, on the venue's own figures

An allocation produces a viable order only if **BOTH** hold:

1. **the quantity floored to the symbol's `qty_step` is STRICTLY GREATER THAN
   ZERO**, and
2. **the resulting notional is at least the $5.00 minimum.**

**FLOORED, NOT ROUNDED.** The closing record §6.1 states it: *"Floor is the only
rounding direction that cannot breach the 1% rule; round-to-nearest and ceil
both can."* Report 24 §2.2 records that the engine currently applies no
quantisation at all and that fixing it is 5.3's work. **This rule is written
against the floored quantity, which is the quantity 5.3 will produce.**

**The two conditions are the venue's, retrieved and confirmed.** Report 25 §2
records `qty_step` of **0.0001 / 0.01 / 0.1** (BTC / ETH / SOL) and a
`minTradeUSDT` of **$5.00** on all three, cross-checked field-by-field against
`config/contracts_cache.json` with **twelve of twelve agreeing**. The engine
already encodes both as one predicate in `costs.check_min_qty`, which returns
`(ok, reason)` against `min_trade_num` and `min_trade_usdt`. **Nothing here
imports it** — this document specifies; 5.3 wires.

**A NON-VIABLE ORDER IS REFUSED LOUDLY, NEVER SILENTLY ROUNDED TO ZERO.** A
quantity that floors to zero is not a very small trade; it is no trade, and a
system that recorded it as one would be reporting a fill it could not have got.

---

## 4. THE PARTIAL-ALLOCATION BRANCH IS INERT AT THIS BUDGET

**$120.00 is an exact multiple of $20.00, and a closing position returns exactly
its own allocation.** Therefore, starting from an empty book, **the remaining
budget is always a multiple of $20.00** — it only ever decreases by $20 on an
open and increases by $20 on a close. `min($20, remaining)` is consequently
always either $20 or $0, and $0 is never viable.

> **THE RULE IS THEREFORE A HARD CAP OF SIX CONCURRENT FULL-SIZE POSITIONS WITH
> ARRIVAL-ORDER SKIP.**

That sentence is the operative description of this rule and is the one to
implement against. Every signal either takes a full **$20.00** position or is
skipped; **no partially-sized position can arise from an all-full-size book.**

**THE PARTIAL BRANCH IS RETAINED IN THE SPECIFICATION ANYWAY, AND THE REASON IS
STATED SO IT IS NOT LATER DELETED AS DEAD CODE.** It becomes reachable the
moment `RISK_PER_TRADE_USD` or `MAX_AGGREGATE_OPEN_RISK_USD` changes such that
the ratio is not an integer — and it would then be reachable **silently**,
because nothing in the arithmetic announces the transition. **A rule with an
undocumented dead branch is worse than one without it**: the branch is where an
implementation puts behaviour nobody has thought about, and the project's own
record contains the precedent. Process finding §5.2 of the closing record
documents `MAKER_NONFILL_COST_R` sitting in the wrong denomination, invisible to
all 545 tests then in the suite, **because every one of them multiplied it by
zero.** An inert branch is the same hazard in a different shape.

**Consequently: the partial branch is specified, is documented as unreachable at
these values, and must carry a test that exercises it at values where it IS
reachable.** That test belongs to 5.3, with the implementation; this step
commits no logic to test.

---

## 5. WHY ARRIVAL ORDER, AND WHAT IT COSTS

### 5.1 Arrival order is the only causally implementable rule

**Live, the decision is made at the instant the signal arrives, with no
knowledge of any later signal.** Every alternative selection rule requires the
future:

- **best-of-cohort** — take the six best signals of some window — requires
  knowing what the window contains, which at the moment of the first signal is
  unknown;
- **random selection among competing signals** requires the same window;
- **priority by symbol, by direction or by expected quality** requires either a
  ranking the strategy does not produce or a forward-looking quantity the
  firewall forbids.

**A backtest that used any of them would be measuring a system that cannot be
run.** Arrival order is not chosen because it is good; it is chosen because it
is the only one that exists at decision time.

### 5.2 THE KNOWN BIAS, RECORDED IN ADVANCE

**SIGNALS CLUSTER IN HIGH-VOLATILITY PERIODS.** A book that is full is a book
that has recently filled, so **the cap preferentially skips signals arriving
during clusters — which is to say, preferentially skips high-ATR trades.**

**THAT IS EXACTLY THE STRATUM IN WHICH THE 1.50% FLOOR DOES NOT BIND.** Thesis
§5.1 measures the floor binding on **46.15% / 29.43% / 3.09%** of signals
(BTC / ETH / SOL); when ATR is high, `2.25 × ATR` clears the floor and the ATR
term sets the stop. **So the surviving population is expected to be ENRICHED IN
FLOOR-BOUND TRADES relative to the uncapped population, and the skipped
population depleted of them.**

**WHY THAT MATTERS SPECIFICALLY.** Kill condition (d) — thesis §7 — stratifies
on exactly this: *"If the advantage does not survive among NON-floor-bound
trades at ≥ 0.05R, the thesis is about percentage stop width rather than about
sweeps."* Report 24 §4.3 measured that stratum swinging from **0.0% to 93.9%
across folds** on the uncapped population. **A rule that systematically shifts
the mix between the two strata acts directly on the condition most likely to
decide the thesis.**

**THIS INTERACTION IS EXPECTED, IT IS NOT CORRECTABLE, AND IT IS NOT A DEFECT.**
It is not correctable because the only corrections available are the
future-requiring selection rules ruled out in §5.1, and because a rule that
skipped preferentially by floor-binding stratum would be selecting trades on a
property of the stop rule — which is a strategy parameter entering through the
risk rail. **Recording the direction in advance is what makes the eventual
measurement interpretable**: if the composition shifts as predicted, that is the
mechanism; if it does not, this paragraph is the evidence that it was not what
was expected.

**STEP 3 WILL MEASURE THE FLOOR-BINDING COMPOSITION OF THE SURVIVING AND THE
SKIPPED POPULATIONS, PER FOLD.** It is named here as a required output of the
next step so that it is not discovered later as an omission.

---

## 6. PATH DEPENDENCE, ACCEPTED EXPLICITLY

**Under this rule, whether a signal is traded depends on what is already open.**
What is already open depends on when earlier positions exited. **When they
exited depends on their outcomes** — a stop-out at bar 4 frees its allocation
sixteen hours before a max-hold exit would.

> **THE TRADED POPULATION IS THEREFORE A FUNCTION OF REALISED OUTCOMES.**

Three consequences, all accepted:

**6.1 THE POPULATION IS NOT KNOWABLE BEFORE THE BACKTEST RUNS.** It cannot be
enumerated from bars alone, as report 21's population was. Anything measured on
it is conditional on the exit logic being the one that will be run.

**6.2 REPORT 21'S SIGNAL-COUNT ADEQUACY DOES NOT DESCRIBE THIS POPULATION.** The
frozen figures — worst train fold **570** against a 200 minimum, worst test fold
**281** against 50, resolved by report 24 §3.3 as **per symbol per fold on
signal bars** — were established on the **UNCAPPED** population. **They are
statements about signals, not about trades taken under this rule**, and they
must not be cited as evidence that the capped population is adequate. Whether it
is adequate is a step 3 measurement and this document makes no claim about it.

**6.3 THE UNCAPPED AND CAPPED RUNS ARE NOT NESTED IN THE OBVIOUS WAY.** The
capped traded population is a subset of the uncapped signal population, but
which subset depends on outcomes, so the two runs cannot be compared as though
one were the other with rows deleted at random. Any comparison between them is a
comparison of two different populations and must say so.

**This is the price of a portfolio constraint and it is paid knowingly.** The
alternative — validating with no cap — measures a system that cannot be run at
this capital, which is §7's argument in a different setting.

---

## 7. THE ONE-BUDGET DECISION, AND THE ALTERNATIVE REJECTED

**A DUAL-BUDGET SCHEME WAS CONSIDERED AND IS REJECTED.** It would have used a
loose budget during validation — enough to suppress the skip tail and keep the
traded population close to the uncapped one — and the real budget for
deployment.

**IT IS REJECTED ON ONE GROUND, AND THE GROUND IS SUFFICIENT:**

> **VALIDATING UNDER A BUDGET THE LIVE ACCOUNT WILL NEVER USE MEASURES A SYSTEM
> THAT WILL NEVER EXIST.**

Every figure such a validation produced would describe a strategy with a
different traded population, a different concurrency profile and — per §5.2 — a
different floor-binding composition from the one actually deployed. The gap
between them would be unmeasured by construction, and the temptation to treat
the loose-budget result as the real one would be at its strongest precisely when
the tight-budget result was worse.

**THE SKIP TAIL IS ACCEPTED AS A REAL PROPERTY OF THIS STRATEGY AT THIS
CAPITAL.** It is not noise, not an artefact of the cap, and not something to be
tuned away: at $2,000 with a $20 risk unit, a strategy that fires nine
overlapping signals cannot take all nine, and that is a fact about the strategy
and the account together.

**IT WILL BE REPORTED AS AN EXPLICIT METRIC, NOT SUPPRESSED.** Step 3 reports
the skip rate as a headline quantity. **A strategy whose skip rate is
uncomfortable is a finding, not a problem with the measurement**, and the number
that would make the level look better is exactly the number that must not be
allowed to change it.

---

## 8. MARGIN MODE AND POSITION MODE

### 8.1 `MARGIN_MODE = "cross"`

**DECIDED.** At the leverage this book requires, **isolated margin can place the
liquidation price inside the stop on wide-stop trades.** Under isolated, report
25 §6.2 records the trigger as *"the sum of the isolated margin and the
unrealized PnL is less than the maintenance margin"* — margin scoped to the
single position — so a position sized for a wide stop and margined in isolation
can be liquidated before its own stop is reached. **A stop that cannot be
reached is not a stop, and the entire risk model rests on the stop being the
binding exit.**

Under cross, the same report records the trigger as cross-account value falling
below **the sum of the maintenance margins of all trading pairs**, with the
whole USDT-M balance standing behind every position. Report 25 §4.1 computes
that requirement at report 24's most exposed bar as **$114.40 against $2,000 —
a 5.72% margin ratio where liquidation triggers at 100%.**

**THE COST OF CROSS IS STATED RATHER THAN LEFT IMPLICIT:** it removes the
per-position firebreak. A catastrophic move on one symbol draws on the margin
supporting the other two. **That is the trade being made** — accepting shared
exposure to keep every stop reachable — and it is the reason the aggregate
budget in §1 binds on the book rather than per symbol. The two decisions are the
same decision seen twice.

### 8.2 `POSITION_MODE = "hedge"`

**DECIDED.** Report 25 §5.1 establishes that **the venue nets same-symbol
same-direction entries into a single position with an averaged entry price**,
and that one-way mode holds positions in only one direction per pair, where *"new
positions in the same direction are merged"* and an opposite-direction entry
**offsets or closes** the existing one.

**The strategy fires both directions on every symbol** — thesis §4 specifies a
long and a short trigger, and report 24 §3.4 counts **5,572 long against 5,812
short** over the window, on all three symbols. **Under one-way mode an
opposite-direction signal would offset an open position rather than open a
trade**, silently converting an entry into a partial or full exit of an
unrelated trade. That is not the strategy.

**Hedge mode holds one long and one short per pair**, which is the minimum
structure this strategy needs. **It does not restore parallel positions**:
same-side entries still net within each side, so the netting finding of report
25 §5.1 stands in full and 5.3 still builds a netted position carrying multiple
reduce-only conditional orders.

**POSITION MODE IS A SETUP-TIME DECISION, NOT A RUNTIME ONE.** Report 25 §5.4
records that it is **account-level per product type** — *"the changes made will
apply to all the trading pairs under the respective futures type"* — and that
*"you cannot switch modes if you have open positions on any pair… if there is an
existing position or pending order, you will not be able to switch"*. It is
therefore committed here rather than left to the implementation.

---

## 9. THE GUARD-RAIL PRINCIPLE, HONESTLY ASSESSED

**The principle**, as this project states it: a guard rail must be denominated in
a **different unit** from the mechanism it guards, or it stops being a rail and
becomes a component of the strategy — at which point it must be swept, justified
and defended on performance, which is precisely what a rail exists to avoid.
Thesis §5.3 applies it to the time exit; `costs.check_min_qty` applies it to
order size.

**THE CASE FOR A PASS.** The budget is denominated in **dollars of aggregate
nominal risk**. The strategy mechanism is denominated in **price and ATR** — a
Donchian channel in price, a stop at `2.25 × ATR` floored at 1.50% of entry, a
target at 1:1.5. These are different units, and no quantity in the budget can be
adjusted to make a trigger fire more often or a stop sit differently.

### 9.1 THE TENSION, RECORDED RATHER THAN ARGUED AWAY

**RISK PER TRADE IS FIXED AT $20.00. AGGREGATE NOMINAL RISK IS THEREFORE EXACTLY
PROPORTIONAL TO POSITION COUNT** — `$120 / $20 = 6`, precisely — **and position
count is a signal-population quantity.**

**So the budget is, arithmetically, a cap on concurrent signals wearing a
dollar-denominated costume.** The unit differs; the *information content* does
not. §4 makes this unavoidable rather than incidental: the rule's own operative
description is "six concurrent full-size positions", which is stated in
positions, not in dollars.

**THIS IS A BORDERLINE CASE AND IT IS RECORDED AS ONE. IT IS NOT CLAIMED AS A
CLEAN PASS.** The project's own record contains exactly the failure this
resembles: closing record §3.4 found that Point 4's stop rule was *"a
fixed-percentage stop wearing an ATR costume"*, because the ATR term could never
bind. Report 21 §5.1 found the same shape again on BTCUSDT, where the floor sets
the stop on 46% of signals. **A rail whose unit is nominally distinct but whose
value is a fixed multiple of a strategy quantity is the same defect class**, and
naming it here is the only protection against it being discovered later as a
surprise.

**WHAT KEEPS IT ON THE ACCEPTABLE SIDE, stated as an argument and not as a
proof:** the budget is derived from a **tolerance for loss on the account**
(§2), which is a fact about the operator and not about the signal population,
and it would take the same value if the strategy produced a tenth as many
signals or ten times as many. **A count-denominated rail would not have that
property** — "at most six signals" would be a statement about the population and
would have to be re-argued if the population changed. The proportionality is a
consequence of the risk unit being fixed, not of the budget being chosen against
a count.

**IF THE RISK UNIT EVER STOPS BEING FIXED, THIS ASSESSMENT MUST BE REDONE.** The
proportionality that makes it borderline is the same proportionality that makes
it derivable, and both die together.

---

## 10. WHAT IS NOT DECIDED HERE

**Four items, named so they cannot be absorbed into this document later.**

**10.1 THE OPERATIONAL RAIL ON CONCURRENT CONDITIONAL ORDERS.** Report 25 §5.4
records that **whether trigger orders count against `maxSymbolOrderNum` = 200 is
undocumented** and could not be established without an authenticated probe. Six
netted positions carrying reduce-only stops and targets is a small number of
conditional orders against either reading, but the rail is not written here and
this budget does not imply one.

**10.2 THE DISPOSITION OF `costs.CostConfig.max_leverage`.** It still reads
**3.0** and this step does not touch it. Report 25 §10.1 established that the
placeholder is 33–50× more restrictive than the venue's tier-1 cap; **whether it
should hold the venue's number, a chosen risk number, or be removed is a later
decision and is explicitly out of scope.** Note that it is not redundant with
this budget: `max_leverage` caps **notional**, this rule caps **nominal risk**,
and the two are related only through the stop width, which varies by trade.

**10.3 THE ENGINE'S NEW PORTFOLIO EXECUTION MODE.** `simulate.py` currently
enforces *"one open position per symbol, no pyramiding"* and models independent
positions with per-trade stops. Report 25 §10.2 records that this describes
neither the venue nor the strategy as measured. **Building the netted-position
execution path is 5.3's work.** Nothing in this step is wired in; no engine file
imports `src/risk`.

**10.4 WHETHER R-MULTIPLES ARE EQUAL-WEIGHTED OR DOLLAR-WEIGHTED.** With the
partial branch inert (§4) every trade carries the same risk unit and the two
weightings coincide **at these values** — but they do not coincide in general,
and the choice belongs to the **validation design**, not here. Recording it now
prevents it from being settled by whichever implementation is written first.

---

## 11. PRE-REGISTRATION STATEMENT

**THIS RULE IS COMMITTED BEFORE ANY MEASUREMENT OF ITS CONSEQUENCES EXISTS.**

**The state of the repository at the time of writing** is report 25 at
**`e735295`** (`docs/handoff/25_point_5_2_venue_constraints.md`), with report 24
at `4e08e1b`, the thesis frozen at `02e47a5` and amendment 1 at `703046a`. **No
step between `e735295` and this commit measured anything about a concurrency
cap, a skip rate, or a capped traded population**, and no such measurement
exists anywhere in this repository at this commit.

**THE LEVEL WAS CHOSEN WITHOUT REFERENCE TO ITS EFFECT ON SIGNAL COUNTS.**
$120.00 follows from §2's three judgements — a 30–50% tolerance, one fifth of
it, taken at the conservative end — and from nothing else. Report 24's
occupancy tables were not consulted to set it. The only report 24 figure in this
document is §7.4's 20.51% one-sided-book fraction, used in §2 to argue that the
correlated case is reachable; **it is a directional composition statistic and
says nothing about how many signals a cap would skip.**

**WHAT WOULD FALSIFY THE CLAIM THAT THIS IS A PRE-REGISTRATION.** A commit
between `e735295` and this one containing a skip-rate, surviving-count or capped
concurrency figure. There is none, and `git log` is the check.

**THIS DOCUMENT MAY NOT BE EDITED IN LIGHT OF STEP 3'S RESULT.** Following the
thesis's own §10 procedure: **an amendment is a new document with a new commit
and an explicit statement of what changed and why; a silent edit is a
contamination event.** If step 3 shows the skip rate is uncomfortable, that is a
finding about the strategy at this capital (§7) and **not grounds for moving
$120**. Moving it would require a new document arguing the tolerance was wrong —
on tolerance grounds, not on skip-rate grounds.

**THE PERFORMANCE FIREWALL IS ARMED.** No expectancy, win rate, profit factor,
Sharpe, Sortino, equity curve, drawdown, `r_multiple`, `net_pnl` or `gross_pnl`
quantity is computed, inspected, estimated or referenced in this document or in
the module it specifies, and an AST guard over the module refuses all twelve
names. **No market data was read to write this**: no parquet, no bars, no folds,
no occupancy, no counts.

**THE HOLDOUT REMAINS SEALED AND UNSPENT.** 2025-01-01 through 2026-07-26 has
never been read by any code path in this project, and no code path was executed
to write this document.

---

**Committed alone with `src/risk/budget.py` and `tests/test_risk_budget.py`. No
engine file, no config file, no frozen document, and no measurement. The commit
hash is the proof that the rule preceded the cost of applying it.**
