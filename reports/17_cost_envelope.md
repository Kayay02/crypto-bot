# REPORT 17 — THE COST ENVELOPE AND THE ADMISSIBILITY LINE

**Point 1, reopened.** Point 4's hypothesis is closed
(`docs/handoff/16_point_4_closing.md`). Before an indicator or a thesis is
chosen for the next one, this step fixes the line every candidate will be
priced against.

**What this step touched:** a published fee schedule and closed-form
arithmetic. No parquet, no OHLCV, no trade record, no engine invocation, no
holdout. **The performance firewall is re-armed:** no expectancy, win rate,
profit factor, equity curve or `r_multiple` aggregate is computed, referenced
or estimated anywhere in this report or in `src/costs/`.

**The pre-committed budget** `COST_TOLERANCE_R = 0.11` was fixed **before** the
fee rates were retrieved and **before** any surface was inspected. It is not
modified here.

---

## 1. THE RETRIEVED FEE SCHEDULE

| field | value |
|---|---|
| `maker_rate` | `0.0002` — **0.02% per side** |
| `taker_rate` | `0.0006` — **0.06% per side** |
| `tier` | base tier (regular user, VIP 0 — no volume, balance or BGB tier applied) |
| `product` | USDT-M perpetual futures |
| `source_url` | `https://api.bitget.com/api/v2/mix/market/contracts?productType=USDT-FUTURES` |
| `retrieved_at` | `2026-08-09T17:03:41+00:00` |
| `retrieval_method` | **`automated`** |

**Manual entry was NOT required.** The automated path succeeded on the first
source attempted.

**Which source, and why that one.** `https://www.bitget.com/fee` is the
canonical human fee schedule. It is JS-rendered: an automated fetch returns a
page shell with no fee table in it, so it could not be parsed and was **not**
used as the source of the recorded rates. The Bitget v2 public API endpoint
`mix/market/contracts` is the machine-readable form of the same base-tier
schedule — it carries `makerFeeRate` and `takerFeeRate` per contract, and it
carries the lot-granularity fields section 6 needs, from the same response at
the same timestamp.

**Corroboration.** All **741** USDT-M perpetual contracts the endpoint returned
carry the identical `(0.0002, 0.0006)` pair, so this is a product-level
schedule and not a per-symbol one. `build_fee_artifact.py` treats disagreement
between contracts as a refusal rather than a majority vote. Two Bitget-owned
prose pages independently state the same figures:

- `https://www.bitget.com/support/articles/12560603817155` — "0.02% (for
  providing liquidity as market makers)… 0.06% (for consuming liquidity by
  placing market orders)… actual fee varies by account level."
- `https://www.bitget.com/academy/Fee-Structure-and-Fee-Calculations-on-Bitget`
  — "each trade will carry a transaction fee of 0.02% for Makers and 0.06% for
  Takers."

The artifact is committed at `data/reference/bitget_fees.json` with a
`.gitignore` exception following the existing `grid.json` / `sweep.json`
pattern. `src/costs/envelope.py` contains **no fee literal** — a test greps the
module for one — and raises `FeeArtifactError` if the artifact is absent,
unparseable, missing a required field, or carries a non-finite or non-positive
rate.

---

## 2. WHAT IS CONDITIONAL IN THE SCHEDULE

Four conditionals were looked for. None of them applies at base tier.

**(1) VIP tiers — do NOT apply at base tier.** Bitget publishes a VIP ladder on
which futures maker fees fall toward 0% and taker fees toward 0.02–0.03% at the
top levels. Qualification is on 30-day volume, account balance or BGB holdings.
**The exact per-level thresholds could not be retrieved:** both the VIP page
(`/vip/vipIntroduce`) and the human fee schedule are JS-rendered and return no
table to an automated fetch. This is recorded as a limitation, not resolved by
substituting a third-party summary.

**(2) BGB holding discount — recorded as NOT applying to futures. Ambiguous.**
Bitget's own academy page states the 20% fee reduction for paying fees in BGB
applies to **spot** trading ("Spot trading transaction fee will be reduced by
20% when paying with BGB"), and a Bitget support article extends it to spot and
margin. No Bitget page found offers it on futures. Several third-party
summaries claim it applies across spot *and* futures, and they contradict each
other. The artifact records it as **not applying to USDT-M futures at base
tier**, which is the conservative reading (it prices costs no lower than they
are), and flags it for operator confirmation. **See section 8, item 2.**

**(3) Maker rebate — does NOT apply at base tier.** No negative maker fee or
rebate programme is offered to a base-tier account. Rebate-grade maker pricing
appears only at high VIP / designated market-maker levels.

**(4) Promotional rates — none applying.** The fee promotions Bitget was
publishing at retrieval time concern stock, metal, commodity and index futures.
This project trades none of them.

**Not covered by these rates: funding.** Funding is a periodic transfer between
longs and shorts (`fundInterval = 8` hours), not a trading fee. It is a real
cost of carry and it is **outside this envelope** — see section 8, item 3.

---

## 3. THE ADMISSIBILITY LINE

    f_eff     = maker_frac * f_maker + (1 - maker_frac) * f_taker
    cost_in_R = 2 * (f_eff + slip) / s
    s*        = 2 * (f_eff + slip) / tolerance_r        [solved, not searched]

`s` is stop distance as a fraction of entry price. The factor of 2 is the round
trip: both legs are charged a fee and both pay slippage.

**Blended fee rate by maker fraction** (fraction of the two round-trip legs
filled as maker):

| `maker_frac` | `f_eff`, **percent per side** |
|---|---|
| 0.00 (all taker) | **0.0600%** |
| 0.25 | **0.0500%** |
| 0.50 | **0.0400%** |
| 0.75 | **0.0300%** |
| 1.00 (all maker) | **0.0200%** |

### Minimum admissible stop at `COST_TOLERANCE_R = 0.11`

**Every cell is `s*` expressed as PERCENT OF ENTRY PRICE.** A stop at or above
the cell value keeps round-trip costs within 0.11R; anything narrower does not.

| slippage, **bps per side** | `maker_frac`=0.00 **(% of entry)** | 0.25 **(%)** | 0.50 **(%)** | 0.75 **(%)** | 1.00 **(%)** |
|---:|---:|---:|---:|---:|---:|
| 0.0 | 1.0909 | 0.9091 | 0.7273 | 0.5455 | 0.3636 |
| 1.0 | 1.2727 | 1.0909 | 0.9091 | 0.7273 | 0.5455 |
| 2.0 | 1.4545 | 1.2727 | 1.0909 | 0.9091 | 0.7273 |
| 3.0 | 1.6364 | 1.4545 | 1.2727 | 1.0909 | 0.9091 |
| 4.0 | 1.8182 | 1.6364 | 1.4545 | 1.2727 | 1.0909 |
| 5.0 | 2.0000 | 1.8182 | 1.6364 | 1.4545 | 1.2727 |
| 6.0 | 2.1818 | 2.0000 | 1.8182 | 1.6364 | 1.4545 |
| 7.0 | 2.3636 | 2.1818 | 2.0000 | 1.8182 | 1.6364 |
| 8.0 | 2.5455 | 2.3636 | 2.1818 | 2.0000 | 1.8182 |
| 9.0 | 2.7273 | 2.5455 | 2.3636 | 2.1818 | 2.0000 |
| 10.0 | 2.9091 | 2.7273 | 2.5455 | 2.3636 | 2.1818 |

The full surface is 91 × 5 × 11 = **5,005 cells**; 3,728 of them (74.5%) are
admissible, and the admissible set is exactly the half-line `s >= s*` in each
`(maker_frac, slip)` column.

### The equity cancellation

Under fixed-dollar risk the position is sized `notional = R$ / s`, so the dollar
cost of a round trip is `2 * (f_eff + slip) * R$ / s`. Dividing by `R$` to
express it in R removes `R$` — and equity never entered in the first place.

**Cost as a fraction of R depends only on stop width, fee rate and slippage.**
It does not depend on account size, and it does not depend on how large the
fixed risk is. A $2,000 account and a $200,000 account running the same stop
pay the same fraction of R in costs. The table above is therefore not a
$2,000-specific table; it is the schedule's table.

`cost_in_r()` takes **no equity argument and no risk-dollars argument** — the
signature refuses the mistake rather than documenting it. Capital enters through
exactly two channels, both checked below: leverage (section 5) and lot
granularity (section 6).

---

## 4. THE SLIPPAGE SENSITIVITY VERDICT

How far `s*` travels across the full 0 → 10 bps-per-side slippage axis:

| `maker_frac` | `s*` at 0 bps **(% of entry)** | `s*` at 10 bps **(% of entry)** | spread **(percentage points)** | ratio |
|---:|---:|---:|---:|---:|
| 0.00 | 1.0909 | 2.9091 | **1.8182 pp** | 2.67× |
| 0.25 | 0.9091 | 2.7273 | **1.8182 pp** | 3.00× |
| 0.50 | 0.7273 | 2.5455 | **1.8182 pp** | 3.50× |
| 0.75 | 0.5455 | 2.3636 | **1.8182 pp** | 4.33× |
| 1.00 | 0.3636 | 2.1818 | **1.8182 pp** | 6.00× |

The spread is **identical at every maker fraction — 1.8182 percentage points**.
That is not a degenerate table. `f_eff` enters `s*` additively with `slip`, so
it cancels out of any difference taken along the slip axis: the spread is
`2 * Δslip / tolerance_r` and nothing else. A test asserts this, so an edit that
made `f_eff` multiplicative could not pass silently.

### The verdict: SLIPPAGE IS LOAD-BEARING.

Three comparisons, all pointing the same way.

**Against the fee axis.** Moving from all-taker to all-maker execution — the
largest execution improvement available on this schedule, and a hard one to
achieve — moves `s*` by **0.7273 pp**. The slippage axis moves it by **1.8182
pp**. Slippage is worth **2.5× more than the entire fee axis**. Choosing the
slippage number matters more than choosing how the orders are placed.

**Against the stop widths in play.** The reference stop range this project has
been working in is roughly **1.02% to 3.5%** (the derived floor and the cap from
the previous hypothesis's engine config — a reference range, not a commitment;
see section 8, item 8). That range is **2.48 pp wide**. The slippage spread of
**1.8182 pp is 73% of it**. The slippage assumption alone traverses nearly the
whole usable stop band.

**At the decision boundary.** At `maker_frac = 0.50` — a limit entry and a
market stop-out, the realistic case — `s*` is **0.7273%** at zero slippage and
**1.6364%** at 5 bps per side. A ~1% stop is comfortably admissible under the
first assumption and **inadmissible** under the second. The slippage number does
not shade the answer; it flips it.

**Conclusion, stated plainly: the prior slippage assumption cannot be carried
forward with a documented sensitivity. Slippage is a first-class design input
and needs its own measurement step.** The spread is not small relative to the
stop widths in play — it is comparable to them. Re-deriving slippage
empirically **is** worth the spend, and it should happen before a stop rule is
chosen for the new hypothesis, not after.

---

## 5. IMPLIED LEVERAGE, AND WHETHER ANY CAP BINDS

`leverage = notional / equity = R$ / (s * equity)`, at R$ = 20 and equity =
$2,000.

| `s` **(% of entry)** | notional **(USDT)** | implied leverage **(×)** |
|---:|---:|---:|
| 0.50 (axis minimum) | 4,000.00 | **2.00×** |
| 1.00 | 2,000.00 | 1.00× |
| 2.00 | 1,000.00 | 0.50× |
| 3.50 | 571.43 | 0.29× |
| 5.00 (axis maximum) | 400.00 | **0.20×** |
| 0.3636 (narrowest `s*` on the grid) | 5,500.00 | **2.75×** |
| 2.9091 (widest `s*` on the grid) | 687.50 | 0.34× |

Exchange maximums from the same retrieval: **BTCUSDT 150×, ETHUSDT 150×,
SOLUSDT 100×**.

**No leverage cap binds anywhere in the admissible region — not close.** The
worst case anywhere on the grid is 2.75×, against a cap of 100× on the most
restricted symbol. That is **36× of headroom**. Leverage is not a constraint on
this design at $2,000 with $20 fixed risk, and no candidate should be rejected
or reshaped on leverage grounds.

Worth noting for its own sake: at any stop wider than 1.00%, implied leverage is
**below 1×** — the position is smaller than the account. Fixed-dollar risk at
$20 on $2,000 is a 1%-of-equity risk, so leverage only appears at all when the
stop is tighter than the risk fraction.

---

## 6. MINIMUM NOTIONAL AND LOT GRANULARITY

Retrieved from the same API response, same timestamp — **retrieval succeeded**:

| symbol | min order qty **(base coin)** | qty step **(base coin)** | min notional **(USDT)** | max leverage **(×)** |
|---|---:|---:|---:|---:|
| BTCUSDT | 0.0001 | 0.0001 | 5 | 150 |
| ETHUSDT | 0.01 | 0.01 | 5 | 150 |
| SOLUSDT | 0.1 | 0.1 | 5 | 100 |

**Minimum notional does not bind. Decided, no price needed.** Notional is
smallest at the widest stop: at the axis maximum `s` = 5.00% it is **$400.00**,
and at the widest `s*` on the grid (2.9091%) it is **$687.50**. Bitget's
`minTradeUSDT` is **$5** on all three symbols. Even the smallest position on the
axis clears it by **80×**. Nothing in the admissible region approaches the
minimum-notional floor.

**Lot granularity cannot be decided in this step, and I am not estimating it.**
Quantity is quoted in base coin, so converting a step into dollars requires a
price — and this step reads no price series. What *can* be stated without one is
the arithmetic threshold. At the smallest notional on the axis ($400), one
quantity step is worth:

| symbol | step | 1 step = 1% of notional when price ≥ | = 5% of notional when price ≥ | min qty exceeds notional when price ≥ |
|---|---:|---:|---:|---:|
| BTCUSDT | 0.0001 | $40,000 | $200,000 | $4,000,000 |
| ETHUSDT | 0.01 | $400 | $2,000 | $40,000 |
| SOLUSDT | 0.1 | $40 | $200 | $4,000 |

Read this as: rounding the order quantity down to a whole step throws away up to
one step of notional, which is up to one step of *risk*. The middle column is
the price at which that discarded slice reaches 5% of the intended position —
i.e. where $20 of intended risk becomes $19 or less purely from quantisation.
**The right-hand column shows the minimum-order-quantity constraint is nowhere
near binding on any of the three symbols.**

Applying a price to the middle column is a one-line check and belongs in the
next step, which is permitted to read prices. It is listed as an open item in
section 8. What is settled here: **minimum notional does not bind, minimum
order quantity does not bind, and granularity is a rounding-precision question
rather than a feasibility one.**

---

## 7. THE PLANTED-MUTATION RESULT

A guard that cannot detect its own target mutation proves nothing. Three vacuous
guards have already been found in this project, so this one was verified by
planting the mutation it defends against.

**The mutation.** In `src/costs/envelope.py::cost_in_r`:

```
return 2.0 * (f_eff + slip) / s     ->     return (f_eff + slip) / s
```

— charging one side of the round trip instead of both. This is the most
consequential silent error available in the module: it halves every cost figure
and roughly doubles every admissible stop, and the resulting surface looks
entirely plausible. A ratio-only test would not catch it, since halving every
value leaves every ratio intact.

**Procedure.** Planted the mutation, ran
`tests/test_costs_envelope.py::test_round_trip_charges_both_legs`, observed the
failure, restored the file from a pre-mutation copy, and re-ran the full file.

**The failing assertion:**

```
>       assert ev.cost_in_r(0.01, 0.0, 0.0001, f) == pytest.approx(0.14, rel=1e-12)
E       assert 0.06999999999999999 == 0.14 ± 1.0e-12
E         Obtained: 0.06999999999999999
E         Expected: 0.14 ± 1.0e-12
```

**Result: the guard has teeth.** `1 failed` under the mutation; `50 passed`
after reverting. The test asserts the **absolute** value (0.14R at `f_eff` =
0.0006, `slip` = 0.0001, `s` = 0.01), asserts directly that the two-leg cost is
exactly twice the one-leg cost built from the same parts, and carries the same
guard on `min_admissible_stop`, which holds its own independent factor of 2.

---

## 8. ASSUMPTIONS AND AMBIGUITIES

Listed rather than resolved silently.

**1. `maker_frac` is a deterministic fraction of legs, not a fill probability.**
The surface is over an assumed average execution mix. Real fills are stochastic:
a resting limit order sometimes does not fill and has to be chased, which
converts a maker leg into a taker leg exactly when the market is moving. The
realised `maker_frac` will be worse than the intended one, and correlated with
adverse conditions. The surface does not model that correlation.

**2. Slippage is applied to BOTH legs regardless of `maker_frac`. This is
internally inconsistent and it is deliberately conservative.** A leg that fills
as maker has, by construction, roughly zero slippage — it filled at the price it
rested at. The model charges `slip` on both legs even at `maker_frac = 1.0`, so
the all-maker column of the admissibility table is **pessimistic**. The correct
treatment is `slip` on taker legs only, which would make the model
`2 * f_eff + 2 * (1 - maker_frac) * slip`. That change would tilt the surface,
not merely shift it — and it would *strengthen* the case for maker execution.
It was not made here because it is a modelling decision that should be made
against measured fill data, which is the same measurement step section 4 calls
for. **Flagged as the largest single modelling assumption in this report.**

**3. Funding is excluded.** Funding is a transfer, not a fee, and it scales with
holding time rather than stop width, so it does not belong in an
`s`-parameterised envelope. But it is a real per-trade cost and total trade cost
is fee + slippage + funding. This envelope prices two of the three. A
holding-time-parameterised funding cost is a separate piece of work.

**4. The BGB futures question is genuinely ambiguous.** Bitget's own pages put
the 20% BGB fee deduction on spot and margin; multiple third-party summaries
claim it covers futures too, and they contradict each other. Recorded as **not
applying** — the conservative reading. If it does apply, costs are 20% lower
than this report prices them and every `s*` in section 3 falls by 20% of its
fee component. **Operator confirmation required.**

**5. VIP tier thresholds could not be retrieved.** Both relevant Bitget pages
are JS-rendered. What is recorded is that base tier is 0.02%/0.06% and that
better pricing exists above it; the ladder itself is not in the artifact.

**6. These are the SCHEDULE's base-tier rates, not the ACCOUNT's rates.** The
API publishes the product schedule and cannot see an account. If the account
sits at any VIP level, or has a BGB deduction switched on, its real rates are
lower and every figure here is conservative. This needs credentials and is in
the operator checklist.

**7. σ = 0.72–0.85R and MDE ≈ 0.34R are carried in as given.** Both come from
report 12 (the E6 dispersion step). Neither is recomputed here and neither could
be — recomputing them would require reading trade records. `COST_TOLERANCE_R`
inherits whatever error those figures carry. The "one third" in the derivation
is a stated tolerance, not a derived quantity; it is the only judgement in the
threshold.

**8. The 1.02%–3.5% reference stop range belongs to the CLOSED hypothesis.**
Those are the derived floor and cap from the Point 4 engine configuration. The
new hypothesis has no stop rule yet. The range is used in section 4 only as a
scale against which to judge whether 1.8182 pp is "large", and it should be
re-examined once a stop rule exists. The verdict does not hang on it: the
comparison against the fee axis (2.5×) is independent of any stop range.

**9. Lot granularity in dollars is deferred to a price-reading step.** Stated in
section 6. The thresholds are computed; only the price substitution is missing.

**10. `s` is treated as a fraction of ENTRY price on both legs.** Fees are
charged on the notional at each leg's own price, and the exit price differs from
the entry price by roughly `s`. Charging both legs at the entry price
understates the loss-side exit fee by a factor of about `(1 - s)` and overstates
the win-side one. At `s` ≤ 5% this is a sub-5% error on the fee component —
around 0.05 pp on `s*` at the widest cells, an order of magnitude below the
slippage spread. Noted for completeness; it does not affect the verdict.

---

## 9. WHAT THIS STEP FIXES FOR EVERYTHING THAT FOLLOWS

- **The admissibility line is section 3's table.** Any candidate whose natural
  stop falls below its cell is not admissible at `COST_TOLERANCE_R = 0.11`. That
  line was fixed before the fee rates were known and must be applied, not
  renegotiated, when a candidate turns out to fail it.
- **Account size is not a lever on cost.** It never was. Arguments of the form
  "this would work with more capital" are unavailable for cost reasons
  specifically — capital moves leverage and lot granularity, and neither binds.
- **Slippage is now a measurement obligation, not an assumption.** It outweighs
  the entire fee axis by 2.5× and spans 73% of the working stop range. It gets
  its own step.
- **Fees are cheap relative to slippage, and maker execution is worth less than
  it looks.** Going from all-taker to all-maker buys 0.7273 pp of stop width.
  Worth having, not worth designing the strategy around.
