# AMENDMENT 1 TO THE POINT 1 THESIS — WIN-RATE ARITHMETIC CORRECTED

## 1. HEADER

**This is Amendment 1 to `docs/handoff/22_point_1_thesis.md`, frozen at commit
`02e47a5406c75edb57ff846141c70d01d2d2a038` (`02e47a5`).**

**THE ORIGINAL DOCUMENT IS UNALTERED.** Not one character of
`22_point_1_thesis.md` has been edited. §10 of that document specifies its own
amendment procedure — *"An amendment is a new document with a new commit and an
explicit statement of what changed and why; a silent edit is a contamination
event."* — and this document follows it. Read together, the thesis as amended
is: `22_point_1_thesis.md` with §6's two win-rate figures replaced by §4 below.

**WHAT CHANGED, IN ONE SENTENCE.** The thesis's §6 computed the breakeven and
detectable-edge win rates from a cost model the engine does not implement,
producing **44.4%** and **58.0%**; the correct figures under the implemented
model are **40.0%** and **53.6%**.

**SCOPE.** This amendment changes **two numbers and the arithmetic that produces
them**. Every other frozen parameter is untouched and is listed explicitly in §6
so the scope cannot be misread as broader than it is.

**NO DATA WAS READ TO WRITE THIS DOCUMENT.** No parquet, no OHLCV, no bars, no
trade records, no backtest run, no simulation. The engine verification in §3 was
performed by **reading source code**. Every figure below is **arithmetic on
frozen design parameters** and none is a measurement.

---

## 2. WHAT WAS WRONG

Two sections of the thesis specify incompatible cost models. Both are quoted in
full.

**§5.2 TARGET — specifies net-solved placement and DISCLAIMS 1.39R BY NAME:**

> **TARGET = 1.5 × the stop distance, solved NET OF COSTS.**
>
> The reward-to-risk is 1:1.5 in **realised, after-cost** terms, not in gross
> price distance. The target price is solved so that a target exit returns 1.5
> risk units after the round-trip cost is deducted, rather than placed at 1.5×
> the gross stop distance and allowed to net out to less. Stating it this way
> matters because the cost budget is 0.11R (§6) — **a target placed gross would
> deliver ~1.39R net and the breakeven arithmetic in §6 would not describe the
> system being run.**

**§6 — then computes using exactly that disclaimed figure:**

> **The arithmetic, so it is checkable by hand.** With a round-trip cost of 0.11R
> charged against both outcomes, a winner returns `1.5 − 0.11 = 1.39R` and a
> loser costs `1.0 + 0.11 = 1.11R`:
>
>     breakeven:  p(1.39) = (1 − p)(1.11)   ->   p = 1.11 / 2.50 = 0.444
>     E = 0.34R:  p(1.39) − (1 − p)(1.11) = 0.34
>                 2.50p = 1.45              ->   p = 0.580

**§5.2 named 1.39R as the wrong answer, and §6 used 1.39R.** The two sections
were written from different mental models of where the cost lands, and the
contradiction sat one page apart in a document that was reviewed and committed.
The §6 table's entries of 44.4% and 58.0% both descend from it.

**BOTH CANNOT STAND.** The remainder of this amendment establishes which one is
wrong.

---

## 3. WHY §6 WAS THE ERROR

Two independent grounds. Either alone is sufficient; together they are decisive.

### 3.1 GROUND ONE — the 1.11R loser breaches the standing risk constraint

The project's standing constraint is **$20 fixed risk per trade AFTER fees and
estimated slippage**, on approximately **$2,000** of capital — **1% of equity,
enforced after costs.**

§6's model has a losing trade cost **1.11R**:

    1.11 x $20 = $22.20
    $22.20 / $2,000 = 1.11% of equity

**A 1.11R loser breaches the 1% after-costs constraint by construction, on every
losing trade, not occasionally.** A cost model whose ordinary loss violates the
project's defining risk parameter cannot be the model the project is running.
This ground is available from the thesis and the standing constraint alone, with
no reference to the code.

### 3.2 GROUND TWO — the engine implements the other model, and tests pin it

**VERIFIED BY READING THE IMPLEMENTATION**, not by inference from documentation,
from the closing record, or from surrounding code.

**POSITION SIZING — cost-inclusive. `src/engine/costs.py:319–339`:**

```
def position_size(entry, stop, direction, cfg, symbol):
    """Closed-form qty giving exactly risk_usd loss if the stop is hit.

    Denominator is the all-in cost of one unit on a losing trade: the price
    move plus both fee legs plus both slippage legs. Sizing on (P - S) alone
    risks risk_usd PLUS costs -- about 7% oversized.
    ...
    """
    s_entry = entry * cfg.entry_slippage_bps / 10_000.0
    s_stop = stop * cfg.haircut_bps(symbol) / 10_000.0
    move = (entry - stop) if direction == LONG else (stop - entry)
    ...
    denom = move + entry * cfg.taker_fee + stop * cfg.taker_fee + s_entry + s_stop
    ...
    return cfg.risk_usd / denom
```

The denominator is the price move **plus** both fee legs **plus** both slippage
legs — that is `s + c` in price units. **This is form (b): `N = R$ / (s + c)`.**
The docstring names the alternative and rejects it: *"Sizing on (P − S) alone
risks risk_usd PLUS costs — about 7% oversized."*

**TARGET SOLVING — net-solved. `src/engine/costs.py:285–295`:**

```
def solve_target(entry, qty, direction, cfg, tick):
    """Take-profit price: net +target_r_multiple * R, exiting maker.

    "2 x stop distance" is NOT equivalent: it ignores that the winner pays two
    fee legs on a larger notional, so realised winners land short of 2R while
    losers still pay a full 1R.
    """
    return solve_price_for_net(
        entry, qty, direction, cfg, tick,
        net_pnl=cfg.target_r_multiple * cfg.risk_usd,
        exit_fee_rate=cfg.maker_fee)
```

delegating to `src/engine/costs.py:264–282`:

```
def solve_price_for_net(entry, qty, direction, cfg, tick, net_pnl,
                        exit_fee_rate):
    """Price at which net P&L equals `net_pnl` after entry taker + exit fee.

    Long, with X the exit price and P the entry fill:
        net = q*(X - P) - q*P*f_in - q*X*f_out
    Solving for X:
        X = ( net/q + P*(1 + f_in) ) / (1 - f_out)

    Always rounds AWAY from the position, so a level is never claimed at a
    price that would deliver less than `net_pnl`.
    """
```

**This is form (b): the target distance is solved so that a target exit returns
exactly `target_r_multiple × R$` AFTER the round trip is deducted.** The
docstring names the gross alternative and rejects it in the same terms §5.2
does.

**REALISED OUTCOMES FROM THE CODE AS WRITTEN** — not as intended:

| exit | net P&L by construction | R, via `r_multiple(net, cfg) = net / risk_usd` |
|---|---|---|
| **stop** | `−risk_usd` (sizing solves for it) | **exactly −1.0R** |
| **target** | `+target_r_multiple × risk_usd` (target solves for it) | **exactly +RR** |

with the only departure being **one tick of rounding, always AWAY from the
position** — so a loss may exceed 1R by a tick's worth and a win may exceed RR
by a tick's worth, never the reverse.

**TESTS DO PIN THESE VALUES.** Four of them, and their existence is itself part
of the finding:

- **`tests/test_costs.py:115` `test_losing_trade_costs_exactly_one_R`** —
  *"The whole point of the closed form: a stop-out loses risk_usd, not more."*
  Asserts `net <= -risk_usd + 1e-9` and `net == approx(-risk_usd, abs=2*q*tick)`
  across three symbol/direction cases including the stop-fill haircut.
- **`tests/test_costs.py:139` `test_target_delivers_exactly_two_R`** — asserts
  `net >= 2*risk_usd - 1e-9` and `net == approx(2*risk_usd, abs=0.05)`, both
  directions.
- **`tests/test_costs.py:151` `test_naive_2x_stop_target_falls_short_of_2R`** —
  *"Documents WHY the solve exists: the naive target underdelivers."* Asserts
  the gross-placed target nets **less** than the nominal R multiple and that the
  solved target sits further out.
- **`tests/test_regression_pinned_trade.py:87`
  `test_pinned_trade_still_reconciles_to_minus_one_R`** — a real pinned
  stop-out reconciling to **`r_multiple = -1.0001204`**, *"the headline number:
  −1.0001R, to four decimal places."* The 0.0001 excess is the tick rounding.

**So the answer is unambiguous: the engine implements (1b) + (2b).** §5.2
described what is implemented; **§6 described a model that exists nowhere in the
codebase.** This is a documentation error confined to §6 of the thesis — **not**
the more serious finding the brief anticipated, in which §5.2 would have
described an intention never implemented. **No code change is required and none
is made.**

**One note for exactness, which changes nothing.** The engine's default
`target_r_multiple` is **2.0** (Point 4's 1:2), which is why the tests above
assert against 2R. The thesis sets **1.5**. That is a configuration value, not a
code path: the solve mechanism, the sizing formula and the realised-R properties
are identical at any RR. The corrected arithmetic in §4 uses RR = 1.5 as the
thesis specifies.

---

## 4. THE CORRECTED FIGURES

Under cost-inclusive sizing with net-solved targets — the implemented model —
the round-trip cost is absorbed **into the position size and into the target
distance**, not deducted from the R multiple at exit. Therefore:

    N        = R$ / (s + c)
    loser    = exactly  -1.0R
    winner   = exactly  +1.5R

**THE ARITHMETIC, written out so it is checkable by hand:**

    breakeven:  1.5p = 1.0(1 - p)
                1.5p + 1.0p = 1.0
                2.5p = 1.0                 ->  p = 1.0 / 2.5  = 0.400  = 40.0%

    E = 0.34R:  1.5p - 1.0(1 - p) = 0.34
                1.5p + 1.0p - 1.0 = 0.34
                2.5p = 1.34                ->  p = 1.34 / 2.5 = 0.536  = 53.6%

**THESE SUPERSEDE 44.4% AND 58.0% WHEREVER THOSE FIGURES APPEAR IN THE THESIS**
— specifically in the **§6 table** (rows *"breakeven win rate at 1:1.5"* and
*"win rate required for E = 0.34R"*), in the **§6 hand-checkable arithmetic
block**, and in **§6.1** (*"58.0% is the number this thesis must earn"*) and
**§8.2** (*"The required 58.0% win rate is high for any intraday trigger"*).

**Corrected: 53.6% is the number this thesis must earn.**

**These remain DESIGN TARGETS derived from frozen parameters. They are not
measurements. No trade was simulated to produce them and no performance quantity
was computed from data.**

**The substantive claim of §6.1 is UNAFFECTED and is restated here so the
correction is not mistaken for encouragement:** nothing measured so far supports
53.6% any more than it supported 58.0%. Reports 17 through 21 established
admissibility — cost clearance, signal counts, trigger/stop consistency — and
**nothing whatever about edge.** 53.6% is lower than 58.0%; it is not low.

---

## 5. WHERE THE COST ACTUALLY GOES

The cost has not vanished. It moved from the exit arithmetic into **the position
size and the target distance**, where the engine actually puts it.

### 5.1 The target-distance expression, derived from first principles

Let `P` be the entry price, `s` the stop distance **as a fraction of P**, `c` the
round-trip cost **as a fraction of P**, `N` the quantity, `R$` the risk unit,
and `RR` the reward-to-risk multiple.

**Step 1 — sizing.** A stop-out must lose exactly `R$`. The all-in loss per unit
is the price move plus the round-trip cost:

    N x (sP + cP) = R$        ->        N = R$ / (P(s + c))

so the notional is

    N x P = R$ / (s + c)

**Step 2 — the target.** Let `d` be the **gross** target distance in price
units. Gross P&L at the target is `N x d`; the round trip costs `N x P x c`.
Requiring the net to equal `RR x R$`:

    N x d  -  N x P x c  =  RR x R$
    N x d  =  RR x R$  +  N x P x c
        d  =  RR x (R$ / N)  +  P x c

**Step 3 — substitute `R$ / N = P(s + c)` from step 1:**

    d = RR x P(s + c) + P x c
      = P x ( RR x s  +  RR x c  +  c )
      = P x ( RR x s  +  (RR + 1) x c )

**Step 4 — at RR = 1.5:**

    d / P  =  1.5s + 2.5c

**That is the expression, derived rather than asserted.** The `(RR + 1)` on the
cost term is the whole content of the correction: the target must cover the cost
of the round trip **and** the cost already built into the enlarged risk unit.

### 5.2 The figures at s = 1.50% and COST_TOLERANCE_R = 0.11

With `c = 0.11 x s = 0.1650%`:

| quantity | value |
|---|---:|
| naive gross target distance, `1.5 x s` | **2.2500%** |
| **net-solved gross target distance, `1.5s + 2.5c`** | **2.6625%** |
| **increase** | **+18.33%** |
| notional under `N = R$/s` | `R$ / 0.0150` |
| **notional under `N = R$/(s+c)`** | `R$ / 0.01665` |
| **notional reduction** | **−9.91%** |

Both figures have closed forms independent of `s`, because `c` is defined as a
fixed fraction of `s`:

    target increase   = (RR + 1)/RR x 0.11 = (2.5/1.5) x 0.11 = 18.33%
    notional reduction = 0.11 / 1.11                          =  9.91%

### 5.3 THE REFRAMING, STATED EXPLICITLY

> **COSTS DO NOT RAISE THE REQUIRED WIN RATE. THEY LOWER THE ACHIEVABLE WIN RATE
> BY PLACING THE TARGET FURTHER AWAY.**

**The required win rate is geometric.** At a 1:1.5 reward-to-risk with a −1.0R
loser and a +1.5R winner, breakeven is `1/(1+1.5) = 40.0%` and nothing about
fees, slippage or funding can change that. It depends **only** on the
reward-to-risk ratio.

**What costs do is make the target harder to reach.** The price must travel
**2.66% instead of 2.25%** — 18.33% further — for the same +1.5R. Fewer trades
will get there. The win rate the market delivers falls; the win rate the
arithmetic demands does not move.

**This distinction is not cosmetic — it changes what a cost improvement buys.**
Under the erroneous §6 model, cutting costs would have appeared to lower a
required threshold. Under the implemented model it does nothing of the kind: it
pulls the target closer, which raises the achievable win rate against an
unchanged 40.0% breakeven. **The lever acts on the achievable side, not the
required side**, and any future reasoning about maker rebates, venue choice or
execution improvements has to be framed that way.

---

## 6. WHAT DOES NOT CHANGE

**Everything else in the thesis stands exactly as frozen at `02e47a5`.** Listed
explicitly so the scope of this amendment is unambiguous:

| frozen item | value | thesis § |
|---|---|---|
| Timeframe | **1h** | header, §3 |
| Trigger | **Donchian-10 wick-and-reject**, current bar excluded from its own window | §4 |
| Strictness | all four comparisons **strict** | §4 |
| Two-sided bars | **skipped**, for determinism | §4.1 |
| Entry | **close of the signal bar, taker**, FROZEN | §4.2 |
| Stop multiplier | **m = 2.25 × ATR(14)** | §5.1 |
| Stop floor | **1.50%**, a cost-admissibility constraint | §5.1 |
| Floor binding rates | 46.15% / 29.43% / 3.09% (BTC/ETH/SOL) | §5.1 |
| Binding rate monitored per fold | **yes** | §5.1 |
| Reward-to-risk | **1 : 1.5**, net-solved | §5.2 |
| Time exit | **n = 3 funding settlements**, elapsed 16–24h | §5.3 |
| Time-exit justification | **funding cost only**; thesis-decay rejected | §5.3 |
| Funding rate assumption | **0.01% / 8h**, monitored per fold | §5.3 |
| **`COST_TOLERANCE_R`** | **0.11 — UNCHANGED** | §6 |
| Slippage closed for stops | ≥ 1.00% | §6 |
| Signal counts | worst train 570 vs 200; worst test 281 vs 50 | §6 |
| No oscillator | **no RSI, no oscillator of any kind** | §3.1 |
| No volume term | **no RVOL, no volume gate** — deliberate departure | §3.2 |
| No session filter | none specified, none added | — |
| Kill conditions | **all six, (a) through (f), verbatim** | §7 |
| Aggregation rule | **majority across the nine folds**, per-fold figures reported | §7.1 |
| Pre-registered failure expectation | edge concentrates in ranging regimes; uniformity is suspicious | §2.5 |
| Known risks | one-sided excursion result; high bar; regime dependence | §8 |
| Holdout budget | one candidate, one look, whole window, no candidate two | §10 |

**`COST_TOLERANCE_R = 0.11` IS NOT CHANGED BY THIS AMENDMENT.** It is frozen,
and every admissibility figure in reports 17, 18 and 21 rests on it — including
the 1.50% stop floor that this document's own §5.2 figures use as an input.
**This step corrects a justification, not a threshold.** §7 records what is now
open about that justification.

**No module, no test and no report is modified by this amendment.** The engine
was found to be correct as written; there is nothing in the code to fix.

---

## 7. OPEN ITEM — THE COST_TOLERANCE_R JUSTIFICATION NO LONGER DESCRIBES THE MECHANISM

**THE VALUE STAYS AT 0.11. ITS STATED JUSTIFICATION DOES NOT SURVIVE THIS
CORRECTION, AND THAT IS RECORDED HERE AS AN OPEN ITEM RATHER THAN REPAIRED.**

**The original justification** was that *costs may consume no more than one
third of the ~0.34R minimum detectable edge*: `0.34 / 3 ≈ 0.11`. That reasoning
**presumes costs subtract from expectancy in R** — that a 0.11R cost turns a
0.34R gross edge into a 0.23R net one.

**Under net-solved geometry they do not do so directly.** A stop exit returns
−1.0R and a target exit returns +1.5R, with costs already inside the risk unit
and inside the target distance. **Costs never appear as a subtraction from the R
multiple of any completed trade.** They subtract from expectancy only
indirectly, by making the target 18.33% further away and therefore less often
reached. The arithmetic `0.34 / 3 = 0.11` no longer corresponds to any quantity
in the system.

**WHAT THE TOLERANCE STILL CONSTRAINS.** It remains meaningful, under a
different reading:

- **The fraction of the risk unit consumed by costs.** `c = 0.11 x s` says the
  round-trip cost may not exceed 11% of the stop distance. That is what
  generates the **1.50% stop floor** — a stop tighter than `c / 0.11` would let
  costs take a larger share of the risk unit than the budget permits.
- **Equivalently, how much further the target must travel.** By §5.1, a
  tolerance of `t` makes the gross target distance `(RR + 1)/RR x t` longer than
  the naive `RR x s`. At `t = 0.11` and `RR = 1.5` that is **+18.33%**. The
  tolerance is a **bound on how far the cost pushes the target out**, and that
  reading is exact under the implemented model.

**A SECOND-ORDER OBSERVATION, RECORDED AND NOT ACTED ON.** Under cost-inclusive
sizing the cost's realised share of the risk unit is `c / (s + c)`, not `c / s`.
At `c = 0.11 x s` that is **0.0991R, not 0.11R** — the budget is conservative by
about 10% relative to its own nominal figure. **This is noted for completeness
and is NOT a reason to change the value**; a threshold loosened after the fact
because a re-derivation found slack is exactly the move this project's amendment
procedure exists to prevent.

**WHAT IS OPEN.** Whether `0.11` is the right bound **under the reading that
actually applies** — a bound on target-distance inflation and on the cost's
share of the risk unit — has not been re-argued. It was argued under a reading
that turns out not to describe the system. **The number is frozen; the argument
for it is owed.** This is carried to the validation design document as an
explicit item, and it must be settled **before** any performance figure is
inspected, because settling it afterward would be selecting a justification to
fit a result.

---

## 8. ERROR CLASSIFICATION

**This is an instance of the recurring defect class documented in the Point 4
closing record §3.4**, which found seven instances of one error and stated it as:

> **a numerical criterion written from a mental model of a quantity rather than
> from its implementation or its achievable range.**

**This is the eighth instance.** The win-rate figures in thesis §6 were derived
from an **assumed cost model** — costs deducted from the R multiple at exit —
rather than from **how the engine actually sizes positions and solves targets**.
The implementation was available, unambiguous, documented in its own docstrings,
and pinned by four tests. It was not consulted.

**The mitigation §3.4 prescribes applies exactly:** *"derive every bound and
threshold from the variable's actual construction and measured range, never from
its name or its description."* Had the §6 arithmetic been derived from
`position_size` and `solve_target` rather than from the phrase "cost budget of
0.11R", the contradiction with §5.2 could not have been written.

### 8.1 WHY IT SURVIVED REVIEW — THE ERROR WAS IN THE CONSERVATIVE DIRECTION

**The error made the thesis appear HARDER than it is.** It overstated the
breakeven win rate by 4.4 percentage points (44.4% against 40.0%) and the
detectable-edge win rate by 4.4 points (58.0% against 53.6%). Every figure it
produced was a **higher bar** than the true one.

**A conservative-looking number attracts less scrutiny.** A review that finds a
strategy needs 58% rather than 53.6% has no incentive to check the arithmetic —
the number is uncomfortable, the discomfort reads as rigour, and a figure that
makes one's own hypothesis look worse is the last place anyone goes looking for
a flattering mistake. The document even flagged the higher number as a risk
(§8.2, *"58% is a high bar"*), which made it **more** credible rather than less.

**The general lesson, recorded for the next document:** *errors in the
conservative direction are the ones that survive review, precisely because they
are conservative.* The check that catches them is not scepticism about whether a
number is too good — it is deriving every number from its implementation
regardless of which direction it points. **A pessimistic number is not a
validated number.**

**One thing this episode does show working:** §5.2 stated the correct model
plainly enough that the contradiction was detectable from the document alone,
without reading the code. Writing the disclaimed alternative out by name — *"a
target placed gross would deliver ~1.39R net"* — is what made the error findable.

---

## 9. STATUS

**THE THESIS AS AMENDED IS FROZEN.** `22_point_1_thesis.md` at `02e47a5`, with
§6's win-rate figures superseded by §4 of this document. Both documents stand
together; neither may be edited. A further correction is Amendment 2, with its
own commit and its own statement of what changed and why.

**THE PERFORMANCE FIREWALL REMAINS ARMED.** No expectancy, win rate, profit
factor, Sharpe, equity curve, `r_multiple` or `net_pnl` quantity has been
computed from data at any point in producing this document, and none may be
until the **validation design** is separately written, agreed and committed. The
win rates in §4 are arithmetic on frozen design parameters; no trade was
simulated to produce them.

**THE HOLDOUT REMAINS SEALED AND UNSPENT.** 2025-01-01 to 2026-07-26 has never
been read — not one bar — by any code path in this project. No code path was
executed to write this document.

**HOLDOUT BUDGET, UNCHANGED: ONE CANDIDATE, ONE LOOK, WHOLE WINDOW, NO CANDIDATE
TWO.**

**NEXT.** The validation design document, carrying the §7 open item as an
explicit agenda entry to be settled before any performance figure is inspected.

---

**Committed alone. One file. No code changes, no test changes, no data access,
no simulation. The original thesis stands unaltered at `02e47a5`.**
