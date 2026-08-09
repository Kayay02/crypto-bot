# REPORT 18 — THE SLIPPAGE LOWER BOUND, FROM TICK SIZE ALONE

Report 17 closed by converting the slippage question into a single comparison:
measure realised per-side slippage, read one cell of the break-even table. This
step tries the cheap side of that comparison first, and it turns out to be
enough.

**The argument.** At $400 to $5,500 of notional, a market order on BTC/ETH/SOL
perpetuals does not come close to exhausting top-of-book depth. A taker that
does not exhaust the touch pays half the bid-ask spread and nothing else, so
book depth drops out and slippage is half the spread. The spread has a hard
floor of one tick. Tick size is published; a price is one HTTP call. That gives
a **lower bound** on slippage — the useful direction, because if the break-even
tolerance is many multiples of the floor, no measurement can move the verdict.

**What this step read:** two public instrument endpoints and one point-in-time
price per symbol, used solely to convert a tick into basis points. **No
historical market data.** No parquet, no OHLCV, no candle endpoint, no trade
records, no engine, no holdout. **The performance firewall is re-armed:** no
expectancy, win rate, profit factor, equity curve or `r_multiple` aggregate is
computed, referenced or estimated.

**`COST_TOLERANCE_R` remains 0.11.** It is pre-committed and is not revisited
here regardless of what this step found. Every break-even figure below is
imported from `src/costs/envelope.py`; none is copied from report 17. A test
greps this step's module for report-17 constants and fails if one appears.

---

## 1. RETRIEVED INSTRUMENT SPECIFICATIONS

**Source:** `https://api.bitget.com/api/v2/mix/market/contracts?productType=USDT-FUTURES`
(specifications) and
`https://api.bitget.com/api/v2/mix/market/tickers?productType=USDT-FUTURES`
(price).
**Retrieved at:** `2026-08-09T17:48:59+00:00`. **Method:** `automated`.
Committed at `data/reference/bitget_instruments.json`.

| symbol | tick size **(USDT)** | qty step **(base coin)** | min order qty **(base coin)** | price used **(USDT)** | price field |
|---|---:|---:|---:|---:|---|
| BTCUSDT | 0.1 | 0.0001 | 0.0001 | 65,172.60 | `lastPr` |
| ETHUSDT | 0.01 | 0.01 | 0.01 | 1,922.38 | `lastPr` |
| SOLUSDT | 0.001 | 0.1 | 0.1 | 77.126 | `lastPr` |

**Tick size is derived, not read off one field.** Bitget publishes the price
increment as a pair: `pricePlace` decimal places and `priceEndStep` steps of the
last place, so `tick = priceEndStep * 10^-pricePlace`. All three symbols
currently have `priceEndStep = 1`, so the tick equals one unit of the last
decimal — but reading `pricePlace` alone would silently understate the tick on
any instrument that ticks in coarser steps, and a test pins the two-field
derivation.

### 1.1 What the price is, and what it is not

**A single point-in-time reading per symbol**, taken at the timestamp above and
used for exactly one purpose: converting a tick size into basis points. It is
not a bar, not a series, not an input to any strategy or parameter. No
historical window was queried and the holdout was not touched. The artifact
records it as a reference value with its own millisecond timestamp so it can
never be mistaken for a data series.

**The verdict below is therefore price-conditional**, and section 5.3 states
exactly how far each price would have to move to change it.

### 1.2 Corroboration: observed top of book at the same instant

Recorded alongside the price, from the same response:

| symbol | observed bid **(USDT)** | observed ask **(USDT)** | spread **(ticks)** |
|---|---:|---:|---:|
| BTCUSDT | 65,172.60 | 65,172.70 | **1.0** |
| ETHUSDT | 1,922.38 | 1,922.39 | **1.0** |
| SOLUSDT | 77.125 | 77.126 | **1.0** |

All three were quoting at **exactly one tick** at that instant — the structural
floor is also what the book was actually doing.

**This is one reading and it proves almost nothing on its own.** It cannot
establish a typical spread, a distribution, or anything about adverse
conditions. It is recorded because it is consistent with the floor being the
binding constraint rather than a distant theoretical limit, and because a
reading of, say, 40 ticks would have been a reason to stop and reconsider the
whole method. It was not.

### 1.3 Cross-check against report 17 section 6

Quantity step and minimum order quantity were compared against
`data/reference/bitget_fees.json` — the artifact report 17 section 6 was
rendered from, rather than the markdown, which is a presentation of it.

**RESULT: CLEAN.** All three symbols agree on both fields. The retrieval script
treats a mismatch as a refusal — it writes nothing and exits non-zero rather
than overwriting — and a test plants a disagreement to confirm the check can
actually refuse.

| symbol | qty step here | qty step, report 17 | min qty here | min qty, report 17 | |
|---|---:|---:|---:|---:|---|
| BTCUSDT | 0.0001 | 0.0001 | 0.0001 | 0.0001 | match |
| ETHUSDT | 0.01 | 0.01 | 0.01 | 0.01 | match |
| SOLUSDT | 0.1 | 0.1 | 0.1 | 0.1 | match |

---

## 2. THE SPREAD FLOOR

    one_tick_bps    = 1e4 * tick_size / price
    slip_bps(n)     = 1e4 * n_ticks * tick_size / (2 * price)

The factor of 2 is the half-spread: a taker crossing an `n`-tick spread pays
half of it relative to the mid. The other half is what the resting side gave up.

### 2.1 Implied per-side slippage by spread width

**All cells are BASIS POINTS PER SIDE.**

| symbol | 1 tick **(bps/side)** | 2 ticks **(bps/side)** | 3 ticks **(bps/side)** | 5 ticks **(bps/side)** | 10 ticks **(bps/side)** |
|---|---:|---:|---:|---:|---:|
| BTCUSDT | **0.00767** | 0.01534 | 0.02302 | 0.03836 | 0.07672 |
| ETHUSDT | **0.02601** | 0.05202 | 0.07803 | 0.13005 | 0.26009 |
| SOLUSDT | **0.06483** | 0.12966 | 0.19449 | 0.32414 | 0.64829 |

The 1-tick column is the **structural floor**: per-side slippage on a taker fill
cannot be lower than this, because the spread cannot be narrower than one tick.

### 2.2 Which symbol is widest, in the only sense that matters

**SOLUSDT is the widest in relative terms, by a factor of 8.45 over BTCUSDT.**

| symbol | one tick **(bps of price)** | floor = half spread **(bps/side)** | relative to BTC **(×)** |
|---|---:|---:|---:|
| BTCUSDT | 0.015344 | 0.007672 | 1.00× |
| ETHUSDT | 0.052019 | 0.026009 | 3.39× |
| SOLUSDT | 0.129658 | 0.064829 | **8.45×** |

**Tick size in dollars ranks the three exactly backwards.** SOL has the
*smallest* absolute tick (0.001 against BTC's 0.1) and the *largest* tick
relative to price. Only tick-over-price is comparable across instruments, and a
comparison made on the dollar tick would conclude that BTC is the coarsest
instrument, which is the reverse of the truth. A test asserts both orderings so
the inversion cannot be reintroduced.

Even so, the absolute magnitudes are tiny. The widest floor of the three is
**0.065 bps per side** — under seven thousandths of one percent.

---

## 3. THE BREAK-EVEN COMPARISON

Break-even figures are imported from
`src/costs/envelope.py::max_tolerable_slip` at `COST_TOLERANCE_R = 0.11`, using
the committed fee artifact. Tick counts are `tolerable_bps / floor_bps` — how
many ticks wide the spread would have to be before the budget is breached.

### 3.1 All-taker (`maker_frac = 0.00`) — the conservative case

| stop **(% of entry)** | tolerable slip **(bps/side)** | BTCUSDT **(ticks)** | ETHUSDT **(ticks)** | SOLUSDT **(ticks)** |
|---:|---:|---:|---:|---:|
| 0.75 | `INADM` | — | — | — |
| 1.00 | `INADM` | — | — | — |
| 1.50 | 2.25 | 293.3 | 86.5 | **34.7** |
| 2.00 | 5.00 | 651.7 | 192.2 | 77.1 |
| 2.50 | 7.75 | 1,010.2 | 298.0 | 119.5 |
| 3.00 | 10.50 | 1,368.6 | 403.7 | 162.0 |

`INADM` = inadmissible on fees alone. At all-taker the fee-only floor is 1.0909%
of entry, so a 0.75% or 1.00% stop breaches the budget at **zero** slippage.
Those cells are not slippage findings and no tick count applies to them — the
stop is already disqualified before the book is consulted.

### 3.2 Half-maker (`maker_frac = 0.50`) — a limit entry and a market stop-out

| stop **(% of entry)** | tolerable slip **(bps/side)** | BTCUSDT **(ticks)** | ETHUSDT **(ticks)** | SOLUSDT **(ticks)** |
|---:|---:|---:|---:|---:|
| 0.75 | 0.25 | 32.6 | 9.6 | **3.9** |
| 1.00 | 3.00 | 391.0 | 115.3 | 46.3 |
| 1.50 | 8.50 | 1,107.9 | 326.8 | 131.1 |
| 2.00 | 14.00 | 1,824.8 | 538.3 | 216.0 |
| 2.50 | 19.50 | 2,541.7 | 749.7 | 300.8 |
| 3.00 | 25.00 | 3,258.6 | 961.2 | 385.6 |

### 3.3 Is that tick count plausible for a liquid perpetual?

Read the tables as: *the book would have to be this many ticks wide before costs
breach 0.11R.*

- **Three-digit and four-digit tick counts are not plausible spreads.** A
  BTCUSDT perpetual quoting 1,368 ticks wide is a $137 spread on a $65,000
  instrument — a market in disorder, not a wide market. Nothing in the 1.50%+
  rows is reachable.
- **The 34.7-tick minimum in the all-taker table** (SOL at a 1.50% stop) is a
  ~35× widening from the observed touch. Plausible only in a genuine
  dislocation, not in ordinary trading.
- **One cell is genuinely tight: `maker_frac = 0.50` at a 0.75% stop.** SOL
  tolerates 3.9 ticks, ETH 9.6. A 4-tick SOL spread is entirely reachable in a
  fast market.

**Why that one cell is tight is a fee fact, not a slippage fact.** The fee-only
floor at `maker_frac = 0.50` is 0.7273% of entry. A 0.75% stop sits **3.1%
above** it, so fees have already consumed almost the whole budget and only
0.25 bps of the tolerance is left for anything else. The cell is tight because
the stop is nearly fee-disqualified, not because SOL's spread is large.

---

## 4. THE VERDICT

Stated per symbol, downstream of section 3's numbers.

**The decision rule, declared explicitly because it is a judgement.** A cell is
treated as closed when the tolerable spread is at least **one order of magnitude
(10×) above the one-tick floor** — the book would have to widen tenfold before
the budget is at risk. Between 2× and 10× is conditional; at or below 2× is
open. The rule is a judgement, not a derived quantity, and section 4.4 states
how sensitive the verdicts are to it.

### 4.1 BTCUSDT — **(A) CLOSED**

The minimum headroom anywhere in the grid, including the tightest cell, is
**32.6×**. Every other cell is 293× or more. No plausible spread breaches the
budget at any stop width of interest. **No further slippage measurement is
warranted for BTCUSDT.**

### 4.2 ETHUSDT — **(B) CONDITIONAL**, closed at stops **≥ 1.00%**

At a 0.75% stop with half-maker execution the tolerance is **9.6 ticks** — a
single-digit multiple, and fractionally under the 10× line. At 1.00% it is
115.3×, and it only rises from there. **Slippage is a constraint on stop width
only, and only just.**

This is a knife-edge call: 9.6× against a 10× threshold. A reader applying a 5×
threshold would classify ETHUSDT as CLOSED outright, and that reading is
defensible. The honest summary is that ETH's tightest cell has roughly an order
of magnitude of margin and every other cell has two or more.

### 4.3 SOLUSDT — **(B) CONDITIONAL**, closed at stops **≥ 1.00%**

At a 0.75% stop with half-maker execution the tolerance is **3.9 ticks**. A
4-tick SOL spread is reachable, so this cell is a real constraint rather than a
formality. At 1.00% the tolerance is 46.3× and the constraint disappears.
**Slippage is a constraint on stop width only, with the threshold at 1.00%.**

### 4.4 What the verdicts turn on

**No symbol is OPEN.** No cell anywhere in the grid is at the one-to-two-tick
scale that would require measuring realised spread before choosing a stop rule.

**The whole verdict rests on a single cell**, `maker_frac = 0.50` at a 0.75%
stop, which is 3.1% above the fee-only floor. Every stop at or above 1.00% has
at least **34.7×** of headroom on the worst symbol at the worst maker fraction.
The practical consequence is one line:

> **A stop rule at or above 1.00% of entry closes the slippage question for all
> three symbols. Below 1.00%, SOL and ETH need the spread checked before the
> stop rule is fixed.**

The verdicts are insensitive to the threshold rule for BTC (32.6× clears any
threshold under 32) and for the ≥1.00% region (34.7× minimum). They are
sensitive only where they are already marked conditional.

**This does not retire report 17's break-even table.** The table remains the
pre-committed line, and a candidate must still be priced against it. What has
changed is that the *slippage* input to that pricing now has a bound, so the
comparison can be made without a measurement step for any stop at or above 1.00%.

---

## 5. THE ASYMMETRY THIS METHOD CANNOT SEE

**This is a limitation, not a caveat to be waved through.**

### 5.1 The problem

This method bounds slippage under **normal spread conditions only**. It cannot
see the case that matters most.

A stop-loss exit is a market order that fires during a fast adverse move —
precisely when spreads widen and top-of-book depth thins. **The stop leg is
always taker.** It cannot be worked as a maker order, because the entire point
of it is that it must execute now. So the one leg guaranteed to cross the spread
is also the leg most likely to cross a *widened* spread, and the two are
positively correlated by construction: the conditions that trigger the stop are
the conditions that widen the book.

A tick-size floor therefore **understates stop-leg slippage, by an unknown
amount.** The one-tick observation in section 1.2 was taken in an ordinary
moment and says nothing about this.

**This report does not estimate how far spreads widen in fast markets.** That
needs data this step does not have, and producing a number for it from a mental
model of what a fast market "looks like" would repeat exactly the error report
17 section 4.1 retracted.

### 5.2 The headroom that absorbs it

What *can* be stated is how much margin exists before the widening matters. The
headroom multiple is the factor by which the spread would have to widen from its
floor before the budget breaks.

| stop **(% of entry)** | maker_frac | BTCUSDT **(× floor)** | ETHUSDT **(× floor)** | SOLUSDT **(× floor)** |
|---:|---:|---:|---:|---:|
| 0.75 | 0.50 | 33× | **10×** | **4×** |
| 1.00 | 0.50 | 391× | 115× | 46× |
| 1.50 | 0.00 | 293× | 87× | **35×** |
| 1.50 | 0.50 | 1,108× | 327× | 131× |
| 2.00 | 0.00 | 652× | 192× | 77× |
| 3.00 | 0.00 | 1,369× | 404× | 162× |

**Where the multiple is large, the asymmetry is immaterial.** At a 1.50%
all-taker stop, SOL — the worst symbol — absorbs a 35-fold spread widening
before the budget breaks, and BTC absorbs 293-fold. Fast-market widening of that
magnitude is not a spread; it is a broken market in which the stop's fill price
is the least of the problems.

**Where the multiple is small, say so plainly:** at a 0.75% stop with half-maker
execution, **SOL has 4× and ETH has 10×**. A four-fold spread widening during a
fast move is ordinary, not exceptional. **At that cell the asymmetry is material
and this method cannot resolve it.** That is precisely why both symbols are
marked CONDITIONAL rather than CLOSED, and why the 1.00% threshold is stated as
a threshold rather than a suggestion.

### 5.3 The other thing this method cannot see: the price moved

Headroom is proportional to price, because the floor is `tick / price`. The
retrieved prices are a single instant, so the verdicts carry a price condition.
The tightest cell (`maker_frac = 0.50`, 0.75% stop, 0.25 bps tolerable) falls to
two ticks at these prices:

| symbol | price at retrieval **(USDT)** | falls to 2 ticks at **(USDT)** | falls to 1 tick at **(USDT)** |
|---|---:|---:|---:|
| BTCUSDT | 65,172.60 | 4,000 | 2,000 |
| ETHUSDT | 1,922.38 | 400 | 200 |
| SOLUSDT | 77.126 | **40** | **20** |

**SOL is the live one.** At a SOL price below roughly $40, the tightest cell
would fall to two ticks and SOLUSDT would move from CONDITIONAL to OPEN. That is
a 48% decline from the retrieval price — not a remote scenario over the life of
a strategy.

For the region that matters, the condition is far weaker: the tightest cell at
stops ≥ 1.00% (all-taker, 1.50%, 2.25 bps tolerable) would need SOL below
**$4.44**, ETH below **$44.44** or BTC below **$444** to fall to two ticks.
**The "closed at ≥ 1.00%" conclusion is robust to any plausible price move; the
0.75% conditional verdicts are not.** Re-run
`python src/costs/tick_probe.py` to refresh the artifact if prices have moved
materially before this is relied on.

---

## 6. ASSUMPTIONS AND LIMITATIONS

1. **Depth is assumed not to bind.** The whole method rests on a market order at
   $400–$5,500 not exhausting the touch on these three perpetuals. That is
   asserted, not measured — this step read no order book. It is the assumption
   most likely to be wrong for SOL in a thin moment, and it fails in the same
   direction as section 5.1, compounding it.
2. **Slippage is taken as exactly half the spread.** Real taker fills can be
   worse (walking the book) or better (crossing into a hidden or improving
   quote). The half-spread is the standard first-order treatment, not an
   identity.
3. **One price per symbol, one instant.** Section 5.3 quantifies the exposure.
4. **The 10× closure threshold is a judgement**, declared in section 4 and not
   derived from anything. Section 4.4 states which verdicts survive a different
   choice.
5. **The one-tick observation is a single reading**, recorded as corroboration
   only. It is not evidence about the spread distribution.
6. **Maker legs are assumed to pay no spread**, consistent with
   `src/costs/envelope.py`. Their cost is the non-fill term, which is still an
   unmodelled placeholder at zero (report 17, section 8 items 11 and 12). **This
   step does not fill that hole**, and the `maker_frac = 0.50` column inherits
   it.
7. **`COST_TOLERANCE_R` was not revisited.** Two symbols came back CONDITIONAL;
   that is a finding about those symbols at those stop widths, not grounds to
   move a pre-committed budget, and no tolerance change is proposed.

---

## 7. WHAT THIS STEP SETTLES

- **The slippage measurement step report 17 called for is not needed for any
  stop at or above 1.00% of entry.** Minimum headroom there is 34.7× on the
  worst symbol at the worst maker fraction. The expensive option — book
  snapshots or live fills — is not warranted to answer this question.
- **BTCUSDT is closed outright** at every stop width of interest.
- **ETHUSDT and SOLUSDT are closed at stops ≥ 1.00%** and conditional below it.
  A candidate proposing a sub-1% stop on either symbol owes a spread check
  before its stop rule is fixed.
- **Fees, not spreads, are what disqualify tight stops.** Both `INADM` cells and
  the single tight cell come from the fee-only floor, not from the book. The
  binding constraint on this design at tight stops is the 0.06% taker fee.
- **The fast-market asymmetry is bounded but not eliminated.** It is immaterial
  wherever headroom is in the hundreds, and it is material at exactly one cell,
  which is why that cell is called conditional.
- **The unmodelled maker non-fill cost remains the largest open hole in the cost
  model.** This step did not touch it. It is now the only unquantified term left
  in the envelope, and it is the one that determines whether maker execution is
  worth pursuing at all.

---

## 8. QUANTITY GRANULARITY — CLOSING REPORT 17 SECTION 6

Report 17 section 6 deferred the dollar-denominated granularity check to "a
later step permitted to read prices" and named **SOLUSDT** as the binding
symbol. This step has those prices. **Closing the check reverses the symbol.**

**No new retrieval was performed.** The quantity steps and prices used here are
the values committed in `data/reference/bitget_instruments.json` at commit
`d850ac4`, retrieved at **`2026-08-09T17:48:59+00:00`**. The working copy is
byte-identical to that commit.

### 8.1 The granularity table

    step_value_usdt   = qty_step * price
    notional(s)       = 20.0 / s
    step_fraction(s)  = step_value_usdt / notional(s)
                      = qty_step * price * s / 20.0

**What one quantity step is worth:**

| symbol | qty step **(base coin)** | price **(USDT)** | step value **(USDT)** | vs BTC **(×)** |
|---|---:|---:|---:|---:|
| **ETHUSDT** | 0.01 | 1,922.38 | **$19.2238** | 2.95× |
| SOLUSDT | 0.1 | 77.126 | $7.7126 | 1.18× |
| BTCUSDT | 0.0001 | 65,172.60 | $6.5173 | 1.00× |

**One step as a fraction of position notional.** All cells are **percent of
notional**; `notional` is $2,000 at a 1% stop falling to $400 at a 5% stop.

| symbol | s=1.00% **(% of notional)** | s=1.50% **(%)** | s=2.00% **(%)** | s=3.00% **(%)** | s=5.00% **(%)** |
|---|---:|---:|---:|---:|---:|
| **ETHUSDT** | **0.9612** | **1.4418** | **1.9224** | **2.8836** | **4.8060** |
| SOLUSDT | 0.3856 | 0.5784 | 0.7713 | 1.1569 | 1.9282 |
| BTCUSDT | 0.3259 | 0.4888 | 0.6517 | 0.9776 | 1.6293 |

**The same figures in dollars of the $20 risk** — `20.0 × step_fraction`, the
most a single step of rounding can move realised risk:

| symbol | s=1.00% **(USDT of risk)** | s=1.50% **(USDT)** | s=2.00% **(USDT)** | s=3.00% **(USDT)** | s=5.00% **(USDT)** |
|---|---:|---:|---:|---:|---:|
| **ETHUSDT** | **$0.1922** | **$0.2884** | **$0.3845** | **$0.5767** | **$0.9612** |
| SOLUSDT | $0.0771 | $0.1157 | $0.1543 | $0.2314 | $0.3856 |
| BTCUSDT | $0.0652 | $0.0978 | $0.1303 | $0.1955 | $0.3259 |

**ETHUSDT is the largest at every stop width**, by **2.49× over SOLUSDT** and
**2.95× over BTCUSDT**. Those multiples are constant across `s`, because
`step_fraction` is the same ranking scaled by a common positive factor — the
ordering cannot cross over anywhere on the axis.

**Worst case: `20.0 × max(step_fraction)` = $0.9612 of the $20 risk — 4.81% —
on ETHUSDT at a 5.00% stop.** At a 1.00% stop the worst case is $0.1922, or
0.96%.

### 8.2 This reverses report 17 section 6, and why it got it wrong

Report 17 section 6.3 stated: *"SOL is unambiguously the binding case, by a wide
margin: its thresholds sit 10× below ETH's and 1,000× below BTC's."* **That is
wrong, and the reason is worth naming precisely.**

**The ranking was made on where each threshold sits, not on where each
instrument sits relative to its own threshold.** Report 17 computed, correctly,
the price at which one step reaches 1% of a $400 position: $40 for SOL, $400 for
ETH, $40,000 for BTC. It then ranked the symbols by those thresholds — SOL's is
lowest, so SOL "must" be most exposed. But a threshold says where the line is,
not which side of it the instrument is standing on, or how far past it:

| symbol | 1%-of-$400-notional threshold **(USDT)** | actual price **(USDT)** | trades past its threshold by **(×)** |
|---|---:|---:|---:|
| **ETHUSDT** | 400 | 1,922.38 | **4.81×** |
| SOLUSDT | 40 | 77.126 | 1.93× |
| BTCUSDT | 40,000 | 65,172.60 | 1.63× |

SOL's threshold is ten times lower than ETH's *and* SOL's price is twenty-five
times lower than ETH's. The second fact dominates, and report 17 used only the
first. The only quantity that is comparable across symbols is a **dollar
amount** — `qty_step × price` — because 0.1 SOL and 0.0001 BTC are not the same
kind of thing and cannot be ranked against each other directly. Report 17 said
as much about *tick* size and then did not apply the same discipline to *quantity*
step.

Report 17 section 6.3 is marked SUPERSEDED in place, with the original argument
left intact.

A test asserts the strict ordering ETH > SOL > BTC on `step_value_usdt`, and a
planted mutation reproduces the original error by ranking on `qty_step` alone.

### 8.3 The rounding-direction check — AND WHAT IT FOUND

Report 17 section 6.3 item 3 also asserted: *"Quantisation makes realised risk
lower than intended (quantity rounds down), so it degrades statistical power
rather than breaching the risk budget. It is a precision problem, not a safety
one."*

**That assertion was checked against the engine. It does not describe this
codebase, because THE ENGINE PERFORMS NO QUANTITY QUANTISATION AT ALL.**

**1. The exact operation.** Position quantity is computed in
`src/engine/costs.py:339`, the final line of `position_size`:

```python
    return cfg.risk_usd / denom
```

A raw float. It is consumed directly at `src/engine/simulate.py:190`
(`qty = position_size(entry, stop, direction, cfg, symbol)`) and used unmodified
for notional, target solving, P&L and MFE/MAE. **There is no rounding step
between the two.** A repository-wide search for any quantisation of `qty` —
`round`, `math.floor`, `math.ceil`, `int()`, or the engine's own
`round_to_tick` — returns nothing. `round_to_tick` exists and is applied to
**prices** only.

**2. Floors, rounds, or ceils?** **None of the three.** Orders are sized at full
float precision, on a quantity grid the exchange would not accept.

Note that `OrderSpec` in `src/engine/contracts.py:79-83` *does* parse and store
`qty_step`. It is written to JSON and printed in `__repr__`, and it is read by
no sizing or execution code anywhere. The field is carried, not used.

**3. Can a minimum-quantity clamp raise quantity above the fixed-risk target?**
**No.** `check_min_qty` (`src/engine/costs.py:349-365`) returns
`(False, reason)` and the caller *refuses the trade* at
`src/engine/simulate.py:196-199` rather than resizing it. The codebase states
this itself at `src/engine/simulate.py:702-704`: *"taken trades are always
risk_rule because leverage_cap and min_qty REFUSE rather than resize."* No
clamp path can inflate quantity.

**So the risk budget is not currently breached** — but not for the reason report
17 gave. It is not breached because the rounding that report 17 described as
safe does not happen. Report 17's claim is not true-or-false about this engine;
it is a statement about an unimplemented feature, and it should not be relied on
as a guarantee.

**THE LIVE CONSEQUENCE, FLAGGED FOR POINT 5 (RISK AND POSITION SIZING).** Any
order actually sent to Bitget must be a multiple of `qty_step`. When
quantisation is implemented, the direction is a design decision with a risk-rule
consequence attached, and the figures in section 8.1 are its magnitude:

- **Floor (round down).** Realised risk is at most `20.0 × step_fraction`
  *below* $20 — the section 8.1 dollar table read as a shortfall. Worst case
  $0.96 on ETH at a 5% stop. Never breaches the budget. This is what report 17
  assumed was already happening.
- **Round to nearest.** Realised risk can *exceed* $20 by up to **half** a step:
  $0.0961 on ETH at a 1% stop, rising to **$0.4806 at a 5% stop** (2.40% over
  budget). SOL and BTC top out at $0.1928 and $0.1629.
- **Ceil (round up).** Realised risk can exceed $20 by up to a **full** step:
  **$0.1922 to $0.9612 on ETH** across the 1%–5% range, i.e. **up to 4.81% over
  the $20 target**. SOL up to $0.3856, BTC up to $0.3259.

**Round-to-nearest and ceil both breach the project's standing rule that risk
per trade never exceeds 1% of equity after costs.** $20 *is* 1% of $2,000, so
any excess at all is a breach — it is available at every stop width and on every
symbol under either option, and only the magnitude varies. At the worst cell
(ETH, 5.00% stop, ceil) realised risk reaches **$20.96, or 1.048% of equity**.
Only **floor** is incapable of breaching.

**This is NOT fixed in this step.** Changing sizing behaviour is a design
decision, not a cleanup, and it belongs to Point 5. What this step establishes is
that the decision exists, that it has not been made, that a default of
round-to-nearest — the most natural thing to reach for — would breach the risk
rule, and by exactly how much.

### 8.4 What remains open

**One item: the engine has no quantity quantisation, so the rounding direction
is an unmade Point 5 design decision — and floor is the only one of the three
options that cannot breach the $20 risk rule.**
