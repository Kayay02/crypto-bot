# REPORT 17 — THE COST ENVELOPE AND THE ADMISSIBILITY LINE

**Second pass.** This supersedes the version committed at `bbf1d2f`. Two defects
were found on review and are corrected here:

- **The slippage-leg model was wrong.** Slippage was charged on both round-trip
  legs regardless of maker fraction. A maker leg rested at its own price and
  does not pay slippage. Section 3 carries the corrected model and states what
  moved.
- **The slippage verdict was invalid.** It was derived from a sweep over an
  assumed 0–10 bps interval and therefore measured the interval, not the
  strategy. Section 4 retracts it and replaces it with an axis-independent
  break-even formulation.

The fee artifact, the fee arithmetic, the equity-cancellation result, the
leverage check and the first planted mutation verified correct on review and are
carried forward.

**Point 1, reopened.** Point 4's hypothesis is closed
(`docs/handoff/16_point_4_closing.md`). Before an indicator or a thesis is
chosen for the next one, this step fixes the line every candidate is priced
against.

**What this step touched:** a published fee schedule and closed-form arithmetic.
No parquet, no OHLCV, no trade record, no order book, no engine invocation, no
holdout. **The performance firewall is re-armed:** no expectancy, win rate,
profit factor, equity curve or `r_multiple` aggregate is computed, referenced or
estimated anywhere in this report or in `src/costs/`.

**The pre-committed budget** `COST_TOLERANCE_R = 0.11` was fixed **before** the
fee rates were retrieved and **before** any surface was inspected. It is not
modified here, including in light of anything found here.

---

## 1. THE RETRIEVED FEE SCHEDULE

Carried forward from the first pass unchanged — it verified correct.

| field | value |
|---|---|
| `maker_rate` | `0.0002` — **0.02% per side** |
| `taker_rate` | `0.0006` — **0.06% per side** |
| `tier` | base tier (regular user, VIP 0 — no volume, balance or BGB tier applied) |
| `product` | USDT-M perpetual futures |
| `source_url` | `https://api.bitget.com/api/v2/mix/market/contracts?productType=USDT-FUTURES` |
| `retrieved_at` | `2026-08-09T17:03:41+00:00` |
| `retrieval_method` | **`automated`** |

**Manual entry was not required.** The automated path succeeded on the first
source attempted.

**Which source, and why that one.** `https://www.bitget.com/fee` is the canonical
human fee schedule. It is JS-rendered: an automated fetch returns a page shell
with no fee table in it, so it could not be parsed and was **not** used as the
source of the recorded rates. The Bitget v2 public API endpoint
`mix/market/contracts` is the machine-readable form of the same base-tier
schedule — it carries `makerFeeRate` and `takerFeeRate` per contract, and the
lot-granularity fields section 6 needs, from the same response at the same
timestamp.

**Corroboration.** All **741** USDT-M perpetual contracts the endpoint returned
carry the identical `(0.0002, 0.0006)` pair, so this is a product-level schedule
and not a per-symbol one. `build_fee_artifact.py` treats disagreement between
contracts as a refusal rather than a majority vote. Two Bitget-owned prose pages
independently state the same figures:

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

Four conditionals were looked for. **None applies to this account today.** Two of
the three items that needed credentials have now been confirmed by the operator
and are recorded here.

**(1) VIP tiers — do not apply. CONFIRMED BY OPERATOR: the account is VIP 0.**
Bitget publishes a VIP ladder on which futures maker fees fall toward 0% and
taker fees toward 0.02–0.03% at the top levels, qualifying on 30-day volume,
account balance or BGB holdings. The operator has confirmed the account sits at
**VIP 0**, so the recorded base-tier rates are the account's actual rates, not
merely the published schedule's. The per-level thresholds still could not be
retrieved — both the VIP page (`/vip/vipIntroduce`) and the human fee schedule
are JS-rendered — but that no longer matters for pricing, only for knowing what
a future volume increase would buy.

**(2) BGB discount — available but NOT ACTIVE. OPERATOR: "we can activate to pay
fees in BGB."** The option exists on the account and has not been switched on.
While it is off, the recorded rates stand exactly as priced. Two things remain
unresolved and are deliberately not resolved by assumption: whether the
deduction would cover **futures** at all (Bitget's own academy and support pages
describe the 20% reduction as spot-and-margin; several third-party summaries
claim futures too, and they contradict each other), and what it would be worth
here. If it were activated **and** it covered futures, every fee figure in this
report would fall by 20% — `f_taker` to 0.00048, `f_maker` to 0.00016 — and
every `s*` would fall with it. That is a live, cheap option worth resolving
before the next step, and it is the only unresolved item in the checklist.

**(3) Maker rebate — does not apply. CONFIRMED BY OPERATOR: none found.** No
negative maker fee or rebate programme is offered to this account. Rebate-grade
maker pricing appears only at high VIP / designated market-maker levels. Note
that `load_fees` would refuse an artifact carrying a negative maker rate
outright — it validates rates as strictly positive — so a rebate would require
the model to be revisited, not just the number.

**(4) Promotional rates — none applying.** The fee promotions Bitget was
publishing at retrieval time concern stock, metal, commodity and index futures.
This project trades none of them.

**Not covered by these rates: funding.** Funding is a periodic transfer between
longs and shorts (`fundInterval = 8` hours), not a trading fee. It is a real cost
of carry and it is outside this envelope — see section 8, item 3.

---

## 3. THE CORRECTED ADMISSIBILITY LINE

### 3.1 The model correction

**Previous (first pass, wrong):**

    cost_in_R = 2 * (f_eff + slip) / s

**Corrected:**

    f_eff     = maker_frac * f_maker + (1 - maker_frac) * f_taker      [unchanged]
    cost_in_R = [ 2*f_eff
                + 2*(1 - maker_frac)*slip
                + 2*maker_frac*MAKER_NONFILL_SLIP ] / s                [term = 0, see 3.4]
    s*        = [ 2*f_eff
                + 2*(1 - maker_frac)*slip
                + 2*maker_frac*MAKER_NONFILL_SLIP ] / tolerance_r

Both legs are charged a fee. **Only the taker legs pay slippage** — a leg filled
as maker rested at its own price and got that price. Charging slippage on maker
legs, as the first pass did, systematically overstated the cost of maker
execution.

### 3.2 Minimum admissible stop at `COST_TOLERANCE_R = 0.11`

**Every cell is `s*` expressed as PERCENT OF ENTRY PRICE.** A stop at or above
the cell value keeps round-trip costs within 0.11R; anything narrower does not.

| slippage, **bps per side** | `maker_frac`=0.00 **(% of entry)** | 0.25 **(%)** | 0.50 **(%)** | 0.75 **(%)** | 1.00 **(%)** |
|---:|---:|---:|---:|---:|---:|
| 0.0 | 1.0909 | 0.9091 | 0.7273 | 0.5455 | **0.3636** |
| 1.0 | 1.2727 | 1.0455 | 0.8182 | 0.5909 | **0.3636** |
| 2.0 | 1.4545 | 1.1818 | 0.9091 | 0.6364 | **0.3636** |
| 3.0 | 1.6364 | 1.3182 | 1.0000 | 0.6818 | **0.3636** |
| 4.0 | 1.8182 | 1.4545 | 1.0909 | 0.7273 | **0.3636** |
| 5.0 | 2.0000 | 1.5909 | 1.1818 | 0.7727 | **0.3636** |
| 6.0 | 2.1818 | 1.7273 | 1.2727 | 0.8182 | **0.3636** |
| 7.0 | 2.3636 | 1.8636 | 1.3636 | 0.8636 | **0.3636** |
| 8.0 | 2.5455 | 2.0000 | 1.4545 | 0.9091 | **0.3636** |
| 9.0 | 2.7273 | 2.1364 | 1.5455 | 0.9545 | **0.3636** |
| 10.0 | 2.9091 | 2.2727 | 1.6364 | 1.0000 | **0.3636** |

### 3.3 What changed, and what did not

**The all-taker column did not move at all.** At `maker_frac = 0` the factor
`(1 - maker_frac)` equals 1 and the two models are algebraically identical. This
is why the error survived the first pass's review: the column most likely to be
spot-checked is exactly the one that cannot detect it. A test now asserts the
all-taker column against the *prior* model's formula written out longhand, as a
genuine cross-check rather than a restatement.

**Everything else moved down.** Reduction in `s*` at 10 bps per side:

| `maker_frac` | first pass `s*` **(% of entry)** | corrected `s*` **(%)** | corrected is lower by **(pp)** |
|---:|---:|---:|---:|
| 0.00 | 2.9091 | 2.9091 | **0.0000** |
| 0.25 | 2.7273 | 2.2727 | 0.4545 |
| 0.50 | 2.5455 | 1.6364 | 0.9091 |
| 0.75 | 2.3636 | 1.0000 | 1.3636 |
| 1.00 | 2.1818 | **0.3636** | **1.8182** |

**The all-maker column is now FLAT across the entire slippage axis** at
`s* = 2 * f_maker / tolerance_r = 0.3636%`. With no taker leg there is nothing
for slippage to be charged on, so the slippage axis has no purchase at all.

**The first pass's headline structural claim is retracted.** It reported the
slippage spread in `s*` as *identically 1.8182 pp at every maker fraction*, and
argued that the constancy was "the arithmetic being correct, not a degenerate
table". It was neither — it was an artifact of charging slippage on maker legs.
The spread carries a `(1 - maker_frac)` factor and shrinks linearly:

| `maker_frac` | spread in `s*` across 0→10 bps **(percentage points)** |
|---:|---:|
| 0.00 | 1.8182 |
| 0.25 | 1.3636 |
| 0.50 | 0.9091 |
| 0.75 | 0.4545 |
| 1.00 | **0.0000** |

A test previously asserted the invariance and passed. It passed against the
wrong model. It has been replaced with one asserting the `(1 - maker_frac)`
shrinkage and the exact zero at all-maker.

### 3.4 The counterweight: maker legs are slippage-free but NOT costless

`MAKER_NONFILL_SLIP = 0.0` in `src/costs/envelope.py`. **Unmodelled. A
placeholder, not a measurement.** A chase distance, denominated as a **fraction
of price** — dimensionally identical to `slip`, and divided by `s` alongside it.
The unit was ambiguous when this term was introduced and was resolved in a third
pass; see section 8, item 12.

A resting limit order fails to fill precisely when price is moving away from the
rest. The leg is then chased at a worse price, or the trade is missed
altogether. That is adverse selection, correlated with exactly the conditions in
which the entry mattered — not a symmetric noise term that averages out. **This
cost is real and it is not in the envelope.**

**Setting it to zero is a known understatement of maker-execution cost, and the
flat all-maker column above is therefore optimistic.** At `maker_frac = 1.0` the
model says slippage is free, and the entire true cost of all-maker execution
sits in a term set to zero. Any conclusion of the form "just run everything as
maker" is reading a number the model does not have.

It appears in the cost computation as an additive term rather than only in
prose, so no cost figure can be produced without it being structurally present.
A test raises the constant and requires every downstream figure to move by
exactly `2 * maker_frac * MAKER_NONFILL_SLIP / s`, so it cannot decay into a
decorative constant nothing reads. **No value is estimated for it here.** It
needs fill data this step may not read.

*One deviation from the specification, stated rather than made silently:* the
term was specified as a flat additive constant. It is implemented as
`2 * maker_frac * MAKER_NONFILL_SLIP` — scaled by the number of maker legs —
because a flat term would charge a non-fill cost at `maker_frac = 0`, where
there are no maker legs to fail to fill. That scaling is an unverified shape for
a term of unknown magnitude, not a finding. At the current value of zero it
changes no published number.

*Superseded in the third pass:* this paragraph originally also claimed the term
does **not** divide by `s`, on the reasoning that "a missed fill is a missed
opportunity, not a price-proportional charge". That was wrong, and it is
corrected in section 8, item 12. A chase distance is exactly a price-proportional
quantity — it is `slip` under another name — and it now divides by `s` with
every other cost term.

### 3.5 The equity cancellation — unchanged and unaffected by the correction

Under fixed-dollar risk the position is sized `notional = R$ / s`, so every
price-proportional dollar cost carries a factor `R$ / s`. Dividing by `R$` to
express it in R removes `R$` — and equity never entered in the first place.

**Cost as a fraction of R depends only on stop width, fee rate and slippage.** It
does not depend on account size, and it does not depend on how large the fixed
risk is. A $2,000 account and a $200,000 account running the same stop pay the
same fraction of R in costs. The table in 3.2 is not a $2,000-specific table; it
is the schedule's table.

`cost_in_r()` takes **no equity argument and no risk-dollars argument** — the
signature refuses the mistake rather than documenting it. Capital enters through
exactly two channels: leverage (section 5) and lot granularity (section 6).

---

## 4. THE BREAK-EVEN SLIPPAGE TABLE

### 4.1 Retraction of the first pass's verdict

The first pass concluded that **slippage is load-bearing**, on this reasoning:
`s*` moves 1.8182 pp across a 0–10 bps slippage axis versus 0.7273 pp across the
fee axis, a ratio of **2.5×**, and 1.8182 pp is 73% of the working stop range.

**That conclusion is retracted. The reasoning was invalid.**

The 0–10 bps axis was written down, not measured. It was not derived from any
observed or bounded range of realised slippage for these symbols at these
notionals. Every number in that argument is therefore proportional to a width
somebody chose:

- The 1.8182 pp spread **is** `2 × (axis width) / tolerance`. It restates the
  axis.
- The 2.5× ratio **is** `(axis width) / (f_taker − f_maker)`. It restates the
  axis divided by a constant.
- Had the axis been specified as 0–4 bps, the same procedure would have produced
  a spread of 0.7273 pp and a ratio of **1.0×**, and would have concluded that
  slippage and fees matter equally. Had it been 0–2 bps, it would have concluded
  that slippage matters *less* than fees.

The procedure cannot distinguish a fact about slippage from the width of the
interval it was handed. It produced a confident directional verdict anyway, and
that verdict then propagated into the report's closing section as a
recommendation to spend on a measurement step.

**This is a recurrence of the project's standing error class: a numerical bound
written from a mental model of a quantity rather than from its achievable
range.** It is the same shape as the pre-3R flat 1.0% stop floor and the
pre-Amendment-6 median-form cap — a number that looked like a measurement
because it was expressed to four decimal places, and was in fact an assumption
propagated through arithmetic. Four decimal places on the output of an assumed
input is the tell, and this report's first pass printed 1.8182 pp without
flagging it. Recording it here so the pattern is on file a third time.

Note that the correction in section 3 does **not** rescue the old verdict. Under
the corrected model the same procedure yields spreads of 1.8182 / 1.3636 /
0.9091 / 0.4545 / 0.0000 pp — different numbers, same defect. Every one of them
is still linear in a chosen axis width.

### 4.2 The replacement: invert the question

Instead of asking *how much does `s*` move if slippage is X*, ask *how much
slippage can this stop absorb*. Solving the corrected cost relation for `slip`:

    slip_max = [ tolerance_r * s - 2*f_eff ] / [ 2 * (1 - maker_frac) ]

There is no assumed interval anywhere in that expression. Implemented as
`max_tolerable_slip(s, maker_frac, tolerance_r, fees)`, with three deliberately
distinguishable outcomes:

| return | meaning |
|---|---|
| a float ≥ 0 | the break-even per-side slippage, as a decimal fraction |
| `SLIP_UNCONSTRAINED` (`math.inf`) | `maker_frac = 1.0` and fees alone fit — there are no taker legs, so slippage is not a constraint at all |
| `None` | the stop is **inadmissible on fees alone**; no slippage figure, not even zero, brings it inside the budget |

`None` rather than a negative float on the last case, deliberately. A negative
break-even is arithmetically meaningful but is exactly the value that gets
formatted into a table, compared with `<`, or minimised over, and reads as a
real bound while being a category error. `None` fails at the point of use. A
test asserts it is not returned as a float.

### 4.3 The break-even table

**Cells are the maximum tolerable slippage in BASIS POINTS PER SIDE** at
`COST_TOLERANCE_R = 0.11`, base-tier rates.

- **`INADM`** = inadmissible on fees alone. The stop breaches 0.11R at *zero*
  slippage. No execution quality can save it.
- **`UNCON`** = unconstrained. All legs are maker, so no slippage is paid at all
  and the constraint does not exist. **Read this column against section 3.4 —
  it is the column the unmodelled non-fill term would bite.**

| stop `s` **(% of entry)** | `maker_frac`=0.00 **(bps/side)** | 0.25 **(bps/side)** | 0.50 **(bps/side)** | 0.75 **(bps/side)** | 1.00 **(bps/side)** |
|---:|---:|---:|---:|---:|---:|
| 0.50 | `INADM` | `INADM` | `INADM` | `INADM` | `UNCON` |
| 0.75 | `INADM` | `INADM` | 0.25 | 4.50 | `UNCON` |
| 1.00 | `INADM` | 0.67 | 3.00 | 10.00 | `UNCON` |
| 1.50 | 2.25 | 4.33 | 8.50 | 21.00 | `UNCON` |
| 2.00 | 5.00 | 8.00 | 14.00 | 32.00 | `UNCON` |
| 2.50 | 7.75 | 11.67 | 19.50 | 43.00 | `UNCON` |
| 3.00 | 10.50 | 15.33 | 25.00 | 54.00 | `UNCON` |
| 4.00 | 16.00 | 22.67 | 36.00 | 76.00 | `UNCON` |
| 5.00 | 21.50 | 30.00 | 47.00 | 98.00 | `UNCON` |

The `INADM` cells are precisely the region below the fee-only floor
`2 * f_eff / tolerance_r`, which is the `slip = 0` row of section 3.2:
**1.0909% / 0.9091% / 0.7273% / 0.5455% / 0.3636%** by maker fraction. Those
five numbers are the hardest line in this report — they depend only on the fee
schedule and the pre-committed budget, and no execution assumption of any kind
enters them.

### 4.4 What this table converts the question into

The slippage question is no longer *"what interval should we sweep?"*. It is now
a **single comparison against one measurable market quantity**: realised
per-side slippage for these three symbols at notionals in the **$400 to $5,500**
range, which is the full span the admissible region produces (section 5).

Pick a candidate stop width and an intended execution mix, read one cell, and
compare it to a measured number. Above the cell, the candidate breaches the
pre-committed budget. Below it, it does not. There is no sweep, no assumed
interval, and no ratio whose magnitude depends on how wide somebody drew an
axis.

**This report does not assert what that realised value is, and does not estimate
it.** No half-spread figure is computed or quoted here. Doing so requires order
book or fill data that this step may not read, and producing a number from a
mental model of what slippage "should" be at these sizes would reproduce
verbatim the error retracted in 4.1. That measurement is the next step's job.

What *can* be said without any data, because it is a property of the table
rather than of the market: the cells span more than two orders of magnitude
(0.25 to 98 bps), so the comparison is unlikely to be marginal in most of the
grid. The decision-relevant band — where a plausible measurement could plausibly
fall on either side — is the top-left region, roughly `s` ≤ 1.5% at
`maker_frac` ≤ 0.50. That is where the measurement will actually be doing work,
and it is where it should be aimed.

---

## 5. IMPLIED LEVERAGE, AND WHETHER ANY CAP BINDS

Carried forward from the first pass — verified correct, and unaffected by the
model correction (leverage does not involve slippage).

`leverage = notional / equity = R$ / (s * equity)`, at R$ = 20 and equity =
$2,000.

| `s` **(% of entry)** | notional **(USDT)** | implied leverage **(×)** |
|---:|---:|---:|
| 0.3636 (narrowest `s*` on the grid) | 5,500.00 | **2.75×** |
| 0.50 (axis minimum) | 4,000.00 | 2.00× |
| 1.00 | 2,000.00 | 1.00× |
| 2.00 | 1,000.00 | 0.50× |
| 3.50 | 571.43 | 0.29× |
| 5.00 (axis maximum) | 400.00 | **0.20×** |

Exchange maximums from the same retrieval: **BTCUSDT 150×, ETHUSDT 150×,
SOLUSDT 100×**.

**No leverage cap binds anywhere in the admissible region — not close.** The
worst case anywhere on the grid is 2.75×, against a cap of 100× on the most
restricted symbol: **36× of headroom**. Leverage is not a constraint on this
design at $2,000 with $20 fixed risk, and no candidate should be rejected or
reshaped on leverage grounds.

Worth noting for its own sake: at any stop wider than 1.00%, implied leverage is
**below 1×** — the position is smaller than the account. Fixed-dollar risk at
$20 on $2,000 is a 1%-of-equity risk, so leverage appears at all only when the
stop is tighter than the risk fraction.

---

## 6. MINIMUM NOTIONAL AND LOT GRANULARITY

Retrieved from the same API response at the same timestamp — retrieval
succeeded, no estimation involved.

| symbol | min order qty **(base coin)** | qty step **(base coin)** | min notional **(USDT)** | max leverage **(×)** |
|---|---:|---:|---:|---:|
| BTCUSDT | 0.0001 | 0.0001 | 5 | 150 |
| ETHUSDT | 0.01 | 0.01 | 5 | 150 |
| **SOLUSDT** | **0.1** | **0.1** | **5** | **100** |

### 6.1 Minimum notional does not bind — decided, no price needed

Notional is smallest at the widest stop: at the axis maximum `s` = 5.00% it is
**$400.00**. Bitget's `minTradeUSDT` is **$5** on all three symbols. Even the
smallest position on the axis clears it by **80×**. Nothing in the admissible
region approaches the minimum-notional floor.

### 6.2 Quantity-step thresholds — all three symbols

The first pass omitted the SOLUSDT row from this table. It is completed here on
exactly the same basis as BTC and ETH.

Rounding an order quantity down to a whole step discards up to one step of
notional, which is up to one step of *risk*. The thresholds below are the prices
at which one step reaches the stated fraction of the position.

**At the SMALLEST notional in play — $400.00, at `s` = 5.00%:**

| symbol | step **(base coin)** | 1 step = 1% of notional at price **(USDT)** | = 5% of notional at price **(USDT)** | min qty exceeds notional at price **(USDT)** |
|---|---:|---:|---:|---:|
| BTCUSDT | 0.0001 | 40,000 | 200,000 | 4,000,000 |
| ETHUSDT | 0.01 | 400 | 2,000 | 40,000 |
| **SOLUSDT** | **0.1** | **40** | **200** | **4,000** |

**At the LARGEST notional in play — $5,500.00, at `s` = 0.3636%:**

| symbol | step **(base coin)** | 1 step = 1% of notional at price **(USDT)** | = 5% of notional at price **(USDT)** | min qty exceeds notional at price **(USDT)** |
|---|---:|---:|---:|---:|
| BTCUSDT | 0.0001 | 550,000 | 2,750,000 | 55,000,000 |
| ETHUSDT | 0.01 | 5,500 | 27,500 | 550,000 |
| **SOLUSDT** | **0.1** | **550** | **2,750** | **55,000** |

### 6.3 Is quantisation material for SOL specifically?

**SOL is unambiguously the binding case, by a wide margin: its thresholds sit
10× below ETH's and 1,000× below BTC's.** Bitget quotes SOL quantity to one
decimal place, so a SOL position is expressible only in tenths of a coin, while
BTC is expressible in ten-thousandths. That is the whole difference, and it is
structural rather than incidental.

**Whether it is material in dollars cannot be decided in this step, and I am not
estimating it.** Converting a step into dollars requires a price, and this step
reads no price series. What is established: the check reduces to **one
substitution** into the tables above, and SOL is the only symbol where the
answer is in any doubt. For BTC the thresholds are absurd at every anchor; for
ETH they are comfortable at the large-notional anchor and only questionable at
the small one; **for SOL, one step reaches 1% of a $400 position at a price of
$40 and 5% at $200.**

Three things that *can* be stated without a price:

1. **Minimum order quantity does not bind for SOL** unless SOL trades above
   $4,000 — the right-hand column. That is decided.
2. **The exposure is worst exactly where the envelope is loosest.** Notional is
   smallest at the widest stops, so if SOL quantisation proves material it will
   bite in the wide-stop region that section 4's table treats as most
   comfortable. The two effects push in opposite directions, and a candidate
   choosing a wide stop for cost headroom buys granularity error with it.
3. **If it proves material, the fix is not in this envelope.** It is a
   per-symbol notional floor or a per-symbol minimum stop — a sizing rule, not a
   cost model change. Quantisation makes realised risk *lower* than intended
   (quantity rounds down), so it degrades statistical power rather than
   breaching the risk budget. It is a precision problem, not a safety one.

**Verdict: retrievable, retrieved, and decidable with one number this step may
not read. SOL is the symbol to check first, and the substitution belongs in the
next step alongside the slippage measurement — both need the same data access.**

---

## 7. PLANTED-MUTATION RESULTS

A guard that cannot detect its own target mutation proves nothing. Three vacuous
guards have already been found in this project. Both guards below were verified
by planting the mutation each defends against, observing the failure, and
reverting.

### 7.1 Mutation 1 — the factor of 2 (carried forward, re-verified)

**The mutation.** In the round-trip cost expression:

```
2.0 * f_eff + 2.0 * (1.0 - maker_frac) * slip
    ->  1.0 * f_eff + 1.0 * (1.0 - maker_frac) * slip
```

— charging one side of the round trip instead of both. It halves every cost
figure and roughly doubles every admissible stop, and every **ratio** in the
output survives unchanged, so a ratio-only test cannot see it.

**The failing assertion:**

```
>       assert ev.cost_in_r(0.01, 0.0, 0.0001, f) == pytest.approx(0.14, rel=1e-12)
E       assert 0.06999999999999999 == 0.14 ± 1.0e-12
E         Obtained: 0.06999999999999999
E         Expected: 0.14 ± 1.0e-12
```

Re-verified against the **rewritten** expression, not merely carried over from
the first pass — the refactor into `price_cost_rate` moved the code the guard
targets, so the guard was re-planted rather than assumed to still apply.

### 7.2 Mutation 2 — the `(1 - maker_frac)` factor (new)

**The mutation.** In `price_cost_rate`:

```
return 2.0 * f_eff + 2.0 * (1.0 - maker_frac) * slip
    ->  return 2.0 * f_eff + 2.0 * slip
```

— charging slippage on maker legs, which restores exactly the defect this pass
exists to correct.

**Why it needed its own guard.** It is **invisible at `maker_frac = 0`**, where
`(1 - maker_frac) = 1` and both models agree to the last bit. The all-taker
column is the one most likely to be spot-checked and it cannot detect this
mutation — which is precisely how the error survived the first pass. The guard
is therefore anchored at `maker_frac = 1.0`, where the effect is largest, and at
0.5, where it is half.

**The failing assertion:**

```
>       assert ev.cost_in_r(0.02, 1.0, 0.0010, f) == pytest.approx(0.0200, rel=1e-12)
E       assert 0.12000000000000001 == 0.02 ± 1.0e-12
E         Obtained: 0.12000000000000001
E         Expected: 0.02 ± 1.0e-12
```

A 6× error at all-maker, against zero error at all-taker.

**Result: both guards have teeth.** Under mutation 2, **10** tests in the file
fail, not one — the correction is load-bearing across the round-trip check, the
all-maker invariance test, the sensitivity-shrinkage test, both inverses and the
non-fill propagation test. Under mutation 1, the targeted guard fails on its
absolute-value assertion. Both files were restored from pre-mutation copies and
the full suite re-run green after each.

---

## 8. ASSUMPTIONS AND AMBIGUITIES

All ten from the first pass are carried forward, with items 2 and 4 rewritten to
reflect what changed. Three new items follow. Item 12 was added in a third pass
that resolved a unit ambiguity in the item-11 placeholder; it changes no
published number.

**1. `maker_frac` is a deterministic fraction of legs, not a fill probability.**
The surface is over an assumed average execution mix. Real fills are stochastic:
a resting limit order sometimes does not fill and has to be chased, which
converts a maker leg into a taker leg exactly when the market is moving. The
realised `maker_frac` will be worse than the intended one, and correlated with
adverse conditions. The surface does not model that correlation. **This is now
partly represented** by item 11's placeholder, but only partly: item 11 covers
the cost of the failed fill, not the drift in `maker_frac` itself.

**2. Slippage is now charged on taker legs only — CORRECTED THIS PASS.** The
first pass listed the both-legs treatment as "the largest single modelling
assumption in this report" and declined to fix it, on the grounds that the
correct treatment should be decided against measured fill data. That was the
wrong call: the correction is a matter of mechanics, not measurement — a resting
order gets its resting price whether or not anyone has measured anything. It has
been made. What genuinely does need fill data is item 11, which is now separated
out rather than being used as a reason to leave a known-wrong model in place.

**3. Funding is excluded.** Funding is a transfer, not a fee, and it scales with
holding time rather than stop width, so it does not belong in an
`s`-parameterised envelope. But it is a real per-trade cost and total trade cost
is fee + slippage + funding + non-fill. This envelope prices two of the four
(and one of those two is a placeholder set to zero). A holding-time-parameterised
funding cost is separate work.

**4. The BGB question — narrowed, not closed.** The operator confirms the
deduction is **available but not activated**, so it does not affect any figure in
this report today. What remains unresolved is whether it would cover **futures**
if activated: Bitget's own pages describe it as spot-and-margin, third-party
summaries disagree with each other. If it applies to futures, activating it cuts
every fee figure here by 20%. **This is the one open item that is cheap to
resolve and has real value.**

**5. VIP tier thresholds could not be retrieved.** Both relevant Bitget pages are
JS-rendered. Now largely moot for pricing — the operator confirms VIP 0, so
base-tier rates are the account's actual rates — but it means we cannot say what
volume would be needed to reach the next tier.

**6. Rates now confirmed as the ACCOUNT's rates, not merely the schedule's.**
The first pass could only say these were published base-tier rates, because a
public endpoint cannot see an account. The operator has since confirmed VIP 0,
no BGB deduction active, and no maker rebate. **The three checklist items are
resolved** and the figures in this report are the account's real fee terms, not
a conservative stand-in.

**7. σ = 0.72–0.85R and MDE ≈ 0.34R are carried in as given.** Both come from
report 12 (the E6 dispersion step). Neither is recomputed here and neither could
be — recomputing them would require reading trade records. `COST_TOLERANCE_R`
inherits whatever error those figures carry. The "one third" in the derivation is
a stated tolerance, not a derived quantity; it is the only judgement in the
threshold.

**8. The 1.02%–3.5% reference stop range belongs to the CLOSED hypothesis.**
Those are the derived floor and cap from the Point 4 engine configuration. The
new hypothesis has no stop rule yet. **The first pass used this range as a
denominator in its slippage verdict; that use is retracted along with the
verdict** (section 4.1). Section 4's break-even table does not depend on any
stop range — it is read cell by cell.

**9. Lot granularity in dollars is deferred to a price-reading step.** Stated in
section 6.3. The thresholds are computed for all three symbols; only the price
substitution is missing. SOL is the case to check.

**10. `s` is treated as a fraction of ENTRY price on both legs.** Fees are
charged on the notional at each leg's own price, and the exit price differs from
the entry price by roughly `s`. Charging both legs at the entry price
understates the loss-side exit fee by about `(1 - s)` and overstates the win-side
one. At `s` ≤ 5% this is a sub-5% error on the fee component. Noted for
completeness; it does not affect any verdict here.

**11. NEW — the maker non-fill cost is a placeholder at zero.** `MAKER_NONFILL_SLIP
= 0.0`, unmodelled. Setting it to zero is a **known understatement of
maker-execution cost**, and the consequence is concrete: the flat all-maker
column in section 3.2 and the entire `UNCON` column in section 4.3 are
**optimistic** and must not be designed around. The model currently says
all-maker execution has no slippage-like cost at all, which is mechanically
true and economically false. **No value is estimated.** It needs fill data, and
it should be measured in the same step as slippage — the two come from the same
observations, and item 13 establishes that they are the same *kind* of quantity.

**12. NEW — the non-fill term's UNIT was ambiguous; resolved as a PRICE
FRACTION.** The constant was introduced as `MAKER_NONFILL_COST_R`, whose `_R`
suffix declares R denomination, and it was placed *outside* the division by `s`
— consistently R-denominated, so the two agreed, and the second pass shipped
without noticing that the agreement was on the wrong unit.

**What the ambiguity was.** The quantity is a chase distance: a resting order
did not fill, and the leg was taken at a worse price. That is a distance between
the price you wanted and the price you got, which is dimensionally identical to
`slip` and therefore a fraction of price — not a fraction of risk. Two
placements are available and they differ by a factor of `1/s`, which is **20×
at `s` = 5% and 200× at `s` = 0.5%**:

    price fraction :  ( 2*f_eff + 2*(1-mf)*slip + 2*mf*C ) / s
    R-denominated  :  ( 2*f_eff + 2*(1-mf)*slip ) / s  +  2*mf*C

**Which was adopted, and why.** Price fraction. The constant is renamed
`MAKER_NONFILL_SLIP` — the name now carries the unit, because the unit is the
thing that was ambiguous — and it sits in the numerator beside `slip`, divided
by `s` exactly once along with everything else. Chasing a leg twenty basis
points is the same twenty basis points whether the stop behind it is 0.5% or
5%. R denomination asserts the opposite: it would fix the chase at a constant
*fraction of risk*, so a strategy could shrink the cost of its own missed fills
merely by widening its stop. **That inverts the causality — the stop does not
reach back and change what the order book did.** Under price-fraction
denomination a wider stop does still reduce the chase's cost in R, but as a
consequence of dividing a fixed price distance by a larger `s`, which is exactly
how the fees and `slip` already behave.

**No published number in this report changes.** The constant is zero, and the
two placements are numerically identical at zero — which is precisely why the
error was invisible and why the resolution is enforced structurally rather than
documented. Every figure in sections 3.2, 4.3, 5 and 6 was recomputed after the
change and is byte-identical. The correction matters entirely for what happens
when the term is given a value.

**How it is now enforced.** A unit-consistency test raises the constant to a
non-zero probe and pins the result at **two** values of `s`, asserting that the
gap between the two candidate placements scales as `(1/s − 1)`. No single
R-denominated constant can reproduce the price-fraction answer at both, so the
test fails on the *placement* rather than on the value. A third planted mutation
moves the term back outside the division and is confirmed to fail it. The old
identifier is barred from the module by an AST check, so a name asserting the
wrong unit cannot return. Also removed: `_net_tolerance`, which subtracted the
term from the budget before solving the inverses. That subtraction was the R
treatment's bookkeeping — a cost that did not scale with `s` had to come off the
top — and with it goes the "consumes the entire budget" failure mode it needed.

**What remains unverified** is the *shape*, not the unit: that the cost is
linear in the number of maker legs (`2 * maker_frac`) is the least-wrong
placement for a term of unknown magnitude, not a finding.

**13. NEW — the first pass's slippage verdict is retracted.** Section 4.1. The
2.5× ratio and the "slippage is load-bearing" conclusion were artifacts of an
axis width that had been written down rather than measured. Anything downstream
that cited report 17 for "slippage is load-bearing" is citing a retracted claim
and must be re-derived from section 4.3. **The retraction does not assert the
opposite** — it asserts that the first pass had no basis for a direction, and
that the break-even table is how the question gets answered.

---

## 9. WHAT THIS STEP FIXES FOR EVERYTHING THAT FOLLOWS

- **The hardest line in the report is the fee-only floor.** `2 * f_eff /
  tolerance_r`: **1.0909% / 0.9091% / 0.7273% / 0.5455% / 0.3636%** of entry, by
  maker fraction from all-taker to all-maker. No execution assumption of any kind
  enters these. A candidate whose stop falls below its column is inadmissible at
  `COST_TOLERANCE_R = 0.11` before slippage is even discussed, and no measurement
  can change that.
- **The admissibility line is section 3.2's table.** It was fixed before the fee
  rates were known and must be applied, not renegotiated, when a candidate fails
  it.
- **The slippage question is now a single comparison, not a sweep.** Section
  4.3's table converts it into: measure realised per-side slippage for these
  three symbols at $400–$5,500 notional, then read one cell. Aim the measurement
  at `s` ≤ 1.5%, `maker_frac` ≤ 0.50 — that is where the answer is genuinely in
  doubt.
- **Account size is not a lever on cost.** It never was. Arguments of the form
  "this would work with more capital" are unavailable for cost reasons
  specifically — capital moves leverage and lot granularity, and neither binds.
- **Maker execution buys more than the first pass showed, and its true price is
  not yet known.** Correcting the slippage-leg model moved `s*` at all-maker from
  2.1818% to 0.3636% at 10 bps — a 6× improvement that the wrong model had hidden.
  But the offsetting non-fill cost is a placeholder at zero. **Do not design
  around maker execution on the strength of this table** until item 11 has a
  number.
- **A verdict derived from a swept axis is a statement about the axis.** Third
  occurrence of this error class in the project. When a bound is written rather
  than measured, invert the question and solve for the break-even instead — the
  inverse has no assumed interval in it and can be compared directly against a
  measurement.
