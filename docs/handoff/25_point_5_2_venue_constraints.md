# REPORT 25 — BITGET VENUE CONSTRAINTS, RETRIEVED

**Point 5, sub-point 5.2, step 1.** A RETRIEVAL. No strategy parameter is
chosen, no concurrency cap is set, no leverage setting or margin mode is
decided, no engine file is touched, and no market data is read.

**WHY THIS EXISTS.** Report 24 (`4e08e1b`) measured that the uncapped book
carries a median of 9 positions and **$7,182** of notional, with a maximum of 28
positions and **$27,045**, against $2,000 of capital. It reported that against
`costs.CostConfig.max_leverage = 3.0` — a number whose own source line reads
*"NOT a probed exchange constraint — an unmeasured placeholder"* (`costs.py:113`).
**Every statement about whether that book is carryable therefore rested on a
figure nobody had retrieved.** This step retrieves the venue's actual
constraints.

**THE HEADLINE, IN ONE LINE.** The venue permits the entire measured book with
room to spare: all three book states sit in **tier 1 on every symbol**, where
Bitget's maximum leverage is **150× (BTC, ETH) and 100× (SOL)** and the
maintenance margin rate is **0.40% / 0.40% / 0.50%**. `max_leverage = 3.0` is
**thirty-three to fifty times more restrictive than the venue.** At report 24's
worst bar the venue's maintenance requirement is **$114.40 against $2,000 —
a maintenance margin ratio of 5.72%**, where liquidation triggers at 100%.
**The binding constraint on this book is not the exchange. It is risk appetite,
and 5.2 must set it on those grounds rather than against a placeholder.**

**A SECOND FINDING, LOAD-BEARING FOR 5.3.** Bitget **nets** same-symbol
same-direction entries into a **single position with an averaged entry price**,
in one-way mode and within each side in hedge mode. **Report 24's "11 concurrent
ETH positions" is not eleven positions at the venue — it is one netted position
carrying eleven reduce-only conditional orders at eleven distinct trigger
prices.** §5.

**No market data is read.** This module imports nothing from `src/timeframe`,
`src/folds`, `src/analysis` or the engine — asserted over the import graph, not
by convention — so the holdout is untouched by construction and no seal test
applies. **The performance firewall is armed and WIDENED**: report 24 §9.5 noted
that `drawdown`, `sortino` and `gross_pnl` were absent from the guard's name
list; they are added here (§9.5).

---

## 1. PROVENANCE

| item | value |
|---|---|
| `git rev-parse HEAD` at retrieval | **`4e08e1ba442887742370686593928c187d911b6d`** |
| `--dirty` state at retrieval | **dirty** — untracked `src/venue/` and `tests/test_venue_constraints.py`, the module and tests this report describes, committed together with it |
| **UTC retrieval timestamp** | **`2026-08-11T13:01:35+00:00`** |
| retrieval script | **`src/venue/bitget_constraints.py`** |
| raw snapshot | **`data/reference/bitget_venue/`** — six response bodies plus `manifest.json`, committed |
| tests | **`tests/test_venue_constraints.py`** |
| credentials used | **none.** Both endpoints are public: no key, no signing |

**WHY `src/venue/` AND NOT `src/data/`.** The retrieval follows
`src/data/backfill_bitget.py`'s conventions — the same base URL and product type
from `config/settings.py`, the same 5 req/s throttle, the same four-attempt
exponential backoff with jitter, the same retryable set (HTTP 429, 5xx, Bitget
codes 45001 / 40725 / 40808), the same fail-loud on 400-class errors. It does
**not** belong in the data layer: it reads no bar and must be able to say so
structurally. A test asserts it cannot import `src/timeframe`, `src/folds`,
`src/analysis`, the engine, pandas or pyarrow.

### 1.1 Endpoints called

| endpoint | method | auth | documentation page that identified it |
|---|---|---|---|
| `https://api.bitget.com/api/v2/mix/market/contracts` | GET | **public** | [Get Contract Config](https://www.bitget.com/api-doc/contract/market/Get-All-Symbols-Contracts) |
| `https://api.bitget.com/api/v2/mix/market/query-position-lever` | GET | **public** | [Get Position Tier](https://www.bitget.com/api-doc/contract/position/Get-Query-Position-Lever) |

Both called once per symbol with `productType=USDT-FUTURES&symbol=<SYMBOL>`;
**all six calls returned HTTP 200 with Bitget code `00000`.**

**THE DOCUMENTATION PAGES ARE JS-RENDERED AND WERE NOT PARSED.** An automated
fetch of either `api-doc` URL returns an application shell containing the
Unified Trading Account overview and no endpoint content — **the same finding
`src/costs/build_fee_artifact.py` recorded for `www.bitget.com/fee`**. The paths
were identified from those pages' indexed content and then **confirmed against
the live API**, which is the primary source in any case. The URLs are recorded
for human verification. Paths were not taken from memory: two candidate paths
tried alongside them (`/api/v2/uta/public/instruments`,
`/api/v2/mix/market/contracts-oi`) returned **404**, and are reported as such
rather than quietly dropped.

### 1.2 Raw snapshot — SHA-256 of every file

Bodies are written **verbatim**, as the bytes the server sent: no
re-serialisation, no indentation, no appended newline. A test asserts each file
still hashes to the manifest's value, and that each begins `{"code":` and
contains no newline — which a pretty-printed rewrite would not satisfy.

| file | bytes | SHA-256 |
|---|---:|---|
| `contracts__BTCUSDT.json` | 832 | `b102d41600110d07a1cf7d4f6426ba4669b1e308042b31c104325c80db36e646` |
| `contracts__ETHUSDT.json` | 829 | `edbdac63ad9d60d0558230b0eb2e6f7b59ed63850dcd7438a1d8d7cf1b2fa5ff` |
| `contracts__SOLUSDT.json` | 829 | `115601119ee76d1a7ed96fb961999ac9843acb78fa946f9058fcb88245391349` |
| `query-position-lever__BTCUSDT.json` | 1,496 | `a6ce67dc3eefe2f4cdb68b4d1ebe0832dbcde43ce65354a3272b46b07d063615` |
| `query-position-lever__ETHUSDT.json` | 1,857 | `7096dbab9e4b4923f10d9938b0d96895bd9c4633e3191c3455a45ce7a13f35f9` |
| `query-position-lever__SOLUSDT.json` | 1,239 | `95ff694673c3df056b10a9f1cad46139a5e6a076fed5797b5bd16a56b61ff7c3` |

**RAW BEFORE PARSED, AND THE PARSER READS FROM DISK.** Every table below is
produced by reading those files back, not from an in-memory response. A test
re-derives both tables from the file bytes independently of the module's own
loader and requires equality, so this report cannot describe something the
snapshot does not contain.

---

## 2. CONTRACT SPECIFICATIONS

| field | BTCUSDT | ETHUSDT | SOLUSDT | source field |
|---|---:|---:|---:|---|
| quantity step | **0.0001** | **0.01** | **0.1** | `sizeMultiplier` |
| minimum order quantity | **0.0001** | **0.01** | **0.1** | `minTradeNum` |
| minimum order notional | **5 USDT** | **5 USDT** | **5 USDT** | `minTradeUSDT` |
| price tick | **0.1** | **0.01** | **0.001** | `priceEndStep × 10^−pricePlace` |
| quantity decimals | 4 | 2 | 1 | `volumePlace` |
| price decimals | 1 | 2 | 3 | `pricePlace` |
| **maximum order quantity** | **1,200 BTC** | **9,900 ETH** | **62,000 SOL** | `maxOrderQty` |
| **maximum MARKET order quantity** | **220 BTC** | **1,900 ETH** | **7,800 SOL** | `maxMarketOrderQty` |
| minimum leverage | 1× | 1× | 1× | `minLever` |
| **maximum leverage** | **150×** | **150×** | **100×** | `maxLever` |
| max orders per symbol | **200** | **200** | **200** | `maxSymbolOrderNum` |
| max orders per product | **1,000** | **1,000** | **1,000** | `maxProductOrderNum` |
| max positions | **200** | **200** | **200** | `maxPositionNum` |
| funding interval | 8h | 8h | 8h | `fundInterval` |
| margin coins | USDT | USDT | USDT | `supportMarginCoins` |
| status | normal | normal | normal | `symbolStatus` |

**THE TICK IS DERIVED, NOT READ.** `tick = priceEndStep × 10^−pricePlace`, **not**
`10^−pricePlace`, which coincides today only because `priceEndStep` is 1 on all
three. `src/engine/contracts.py` states the same rule; the two derivations are
asserted equal by test.

**THERE IS NO CONTRACT-SIZE / MULTIPLIER FIELD.** Quantity is denominated in the
base coin and `sizeMultiplier` is the step it must be a multiple of. The
response carries no contract multiplier, so **one unit of quantity is one base
coin**. Recorded because "contract size" is a real field on other venues and its
absence here is a fact rather than an omission.

**`posLimit`** (0.2 / 0.1 / 0.15) is present in every response and is **not
interpreted**: no documentation reachable by automated fetch defines it. It is
carried verbatim in the parsed output so the snapshot's content is fully
represented. §9.

**THE MAXIMUM ORDER QUANTITY IS NOWHERE NEAR BINDING.** Report 24's largest
single position is ~$1,199 of notional — about **0.018 BTC**, against a 220 BTC
market-order cap. Four orders of magnitude of headroom.

### 2.1 CACHE CROSS-CHECK — live against `config/contracts_cache.json`

**The cache is READ and never written.** A disagreement would be reported, not
resolved in either direction.

| symbol | field | live (venue) | cached | agrees | cache source |
|---|---|---:|---:|:---:|---|
| BTCUSDT | qty_step | 0.0001 | 0.0001 | **yes** | `symbols.BTCUSDT.order.qty_step` |
| BTCUSDT | min_trade_qty | 0.0001 | 0.0001 | **yes** | `symbols.BTCUSDT.order.min_trade_num` |
| BTCUSDT | min_trade_usdt | 5.0 | 5.0 | **yes** | `symbols.BTCUSDT.order.min_trade_usdt` |
| BTCUSDT | tick_size | 0.1 | 0.1 | **yes** | `symbols.BTCUSDT.segments[-1]` (1 segment) |
| ETHUSDT | qty_step | 0.01 | 0.01 | **yes** | `symbols.ETHUSDT.order.qty_step` |
| ETHUSDT | min_trade_qty | 0.01 | 0.01 | **yes** | `symbols.ETHUSDT.order.min_trade_num` |
| ETHUSDT | min_trade_usdt | 5.0 | 5.0 | **yes** | `symbols.ETHUSDT.order.min_trade_usdt` |
| ETHUSDT | tick_size | 0.01 | 0.01 | **yes** | `symbols.ETHUSDT.segments[-1]` (1 segment) |
| SOLUSDT | qty_step | 0.1 | 0.1 | **yes** | `symbols.SOLUSDT.order.qty_step` |
| SOLUSDT | min_trade_qty | 0.1 | 0.1 | **yes** | `symbols.SOLUSDT.order.min_trade_num` |
| SOLUSDT | min_trade_usdt | 5.0 | 5.0 | **yes** | `symbols.SOLUSDT.order.min_trade_usdt` |
| SOLUSDT | tick_size | 0.001 | 0.001 | **yes** | `symbols.SOLUSDT.segments[-1]` (current of 2) |

> **TWELVE OF TWELVE AGREE. NO DISAGREEMENT.** Report 24 §2 used
> `qty_step` 0.0001 / 0.01 / 0.1 and a $5 minimum notional from this cache; both
> are confirmed against the venue at today's retrieval. **5.3's quantisation fix
> can be built against these values.**

**SOL's tick is a schedule, not a scalar** — 0.0001 before 2024-08-14T04:05Z and
0.001 after — so the live tick is compared against the cache's **current**
segment. Comparing against the first segment would report a disagreement that is
really a history. Asserted by test, and a planted disagreement is asserted to be
detected rather than absorbed.

---

## 3. LEVERAGE AND MAINTENANCE MARGIN TIERS

Retrieved from `query-position-lever`. `startUnit` / `endUnit` bound the
**position value in USDT**; `leverage` is the maximum permitted while the
position sits in that band; **`keepMarginRate` is the maintenance margin rate**
as a decimal fraction (0.0040 = 0.40%).

### 3.1 BTCUSDT — 12 tiers

| tier | position value (USDT) | max leverage | **MMR** |
|---:|---|---:|---:|
| **1** | **0 – 200,000** | **150×** | **0.40%** |
| 2 | 200,000 – 1,000,000 | 100× | 0.50% |
| 3 | 1,000,000 – 5,000,000 | 75× | 0.70% |
| 4 | 5,000,000 – 15,000,000 | 50× | 1.00% |
| 5 | 15,000,000 – 50,000,000 | 25× | 2.00% |
| 6 | 50,000,000 – 100,000,000 | 20× | 3.00% |
| 7 | 100,000,000 – 150,000,000 | 10× | 6.00% |
| 8 | 150,000,000 – 300,000,000 | 5× | 12.00% |
| 9 | 300,000,000 – 500,000,000 | 4× | 15.00% |
| 10 | 500,000,000 – 700,000,000 | 3× | 20.00% |
| 11 | 700,000,000 – 900,000,000 | 2× | 30.00% |
| 12 | 900,000,000 – 1,200,000,000 | 1× | 60.00% |

### 3.2 ETHUSDT — 15 tiers

| tier | position value (USDT) | max leverage | **MMR** |
|---:|---|---:|---:|
| **1** | **0 – 200,000** | **150×** | **0.40%** |
| 2 | 200,000 – 1,000,000 | 100× | 0.50% |
| 3 | 1,000,000 – 3,000,000 | 75× | 1.00% |
| 4 | 3,000,000 – 12,000,000 | 50× | 1.50% |
| 5 | 12,000,000 – 40,000,000 | 25× | 2.00% |
| 6 | 40,000,000 – 70,000,000 | 20× | 3.00% |
| 7 | 70,000,000 – 100,000,000 | 10× | 5.00% |
| 8 | 100,000,000 – 150,000,000 | 8× | 7.00% |
| 9 | 150,000,000 – 200,000,000 | 7× | 8.00% |
| 10 | 200,000,000 – 250,000,000 | 6× | 9.00% |
| 11 | 250,000,000 – 300,000,000 | 5× | 12.00% |
| 12 | 300,000,000 – 400,000,000 | 4× | 15.00% |
| 13 | 400,000,000 – 500,000,000 | 3× | 20.00% |
| 14 | 500,000,000 – 800,000,000 | 2× | 30.00% |
| 15 | 800,000,000 – 1,200,000,000 | 1× | 60.00% |

### 3.3 SOLUSDT — 10 tiers

| tier | position value (USDT) | max leverage | **MMR** |
|---:|---|---:|---:|
| **1** | **0 – 50,000** | **100×** | **0.50%** |
| 2 | 50,000 – 100,000 | 75× | 0.80% |
| 3 | 100,000 – 1,000,000 | 50× | 1.00% |
| 4 | 1,000,000 – 5,000,000 | 25× | 2.00% |
| 5 | 5,000,000 – 10,000,000 | 20× | 3.00% |
| 6 | 10,000,000 – 30,000,000 | 10× | 5.00% |
| 7 | 30,000,000 – 60,000,000 | 5× | 12.00% |
| 8 | 60,000,000 – 80,000,000 | 4× | 15.00% |
| 9 | 80,000,000 – 150,000,000 | 2× | 30.00% |
| 10 | 150,000,000 – 300,000,000 | 1× | 60.00% |

**Every table is asserted contiguous** — tier 1 starts at 0, each band's start
equals the previous band's end, rates rise monotonically and leverage falls
monotonically — **and asserted to cover 0 to at least $30,000 with no gap.** A
planted gap, a falling rate, a rising leverage cap, a missing level and an empty
table are each asserted to raise.

### 3.4 CROSS VERSUS ISOLATED — one table, and that is itself the finding

> **BITGET PUBLISHES ONE POSITION-TIER TABLE PER SYMBOL. THE ENDPOINT TAKES NO
> MARGIN-MODE PARAMETER AND RETURNS IDENTICAL ROWS REGARDLESS.**

Verified by probing the same endpoint three ways —
`productType=USDT-FUTURES`, `productType=usdt-futures`, and with
`marginCoin=USDT` added — all three returned the **same 12 rows** for BTCUSDT.
There is no cross tier table and no isolated tier table; there is **the** tier
table, and the margin mode changes what the maintenance margin is measured
*against*, not the rate itself (§6).

**This is a negative result and it is reported as one.** The brief asked for
both figures "where they differ". On the retrievable evidence **they do not
differ**, and the decision to run cross margin is therefore documented against
tier rates that are identical under either mode, with the difference lying
entirely in the margin pool and the liquidation trigger.

### 3.5 THE THREE BOOK STATES FROM REPORT 24 §7.1, MAPPED

| book state (report 24) | notional | BTCUSDT tier | ETHUSDT tier | SOLUSDT tier |
|---|---:|:---:|:---:|:---:|
| **median** | $7,182.00 | **1** (150×, 0.40%) | **1** (150×, 0.40%) | **1** (100×, 0.50%) |
| **P99** | $17,826.90 | **1** (150×, 0.40%) | **1** (150×, 0.40%) | **1** (100×, 0.50%) |
| **maximum** | $27,045.20 | **1** (150×, 0.40%) | **1** (150×, 0.40%) | **1** (100×, 0.50%) |

**ALL THREE SIT IN TIER 1 ON EVERY SYMBOL, AND EACH MAPS TO EXACTLY ONE TIER** —
asserted, not asserted-by-eye. The nearest boundary is **SOL's tier-1 ceiling at
$50,000**, which is 1.85× the worst bar ever measured. The book would have to
**double** before any tier change touched it, and even then only on SOL.

**Consequence: the tier system does not constrain this project at any measured
size.** Every leverage and maintenance figure below is a tier-1 figure.

### 3.6 The maintenance margin formula, and a recent change to it

Bitget's classic-account futures maintenance margin moved on **2025-11-10
08:00 UTC** from a whole-position form to a **progressive tiered** one, for new
positions ([support article
12560603841952](https://www.bitget.com/support/articles/12560603841952)):

    superseded:   maintenance margin = position value × MMR(tier)
    current:      maintenance margin = position value × MMR(tier) − offset(tier)

where each slice of the position value is effectively charged its own tier's
rate. **The endpoint publishes the bands and the rates but NOT the offset**, so
the module reconstructs it from the table:

    offset(k) = Σ over j < k of (end_j − start_j) × (rate_k − rate_j)

**This derivation is checked, not asserted:** a test requires
`value × rate_k − offset_k` to equal the slice-by-slice sum at every band edge
and at a point inside every band, on all three symbols.

**OFFSET(TIER 1) IS ZERO BY CONSTRUCTION** — there is no lower tier to discount —
**so the change moves no figure in this report.** Inside tier 1 the two forms are
identical and both reduce to `position value × MMR`. Derived tier-2 offsets are
$200 (BTC), $200 (ETH) and $150 (SOL), recorded only so a reader checking
against an older Bitget page can tell which formula they are looking at.

---

## 4. THE ASSUMED 0.5% MAINTENANCE RATE — CHECKED

**The design discussion used "about 0.5%" to argue that liquidation sits far
outside the stop. THAT FIGURE WAS ASSUMED, NOT RETRIEVED.** The retrieved rates:

| symbol | assumed | **retrieved (tier 1)** | assumption is |
|---|---:|---:|---|
| BTCUSDT | ~0.5% | **0.40%** | **conservative by 25%** |
| ETHUSDT | ~0.5% | **0.40%** | **conservative by 25%** |
| SOLUSDT | ~0.5% | **0.50%** | **exact** |

> **VERDICT: THE ARGUMENT BUILT ON IT IS SUPPORTED, AND ON TWO SYMBOLS IT IS
> STRONGER THAN THE ARGUMENT CLAIMED.** A lower maintenance margin rate places
> liquidation further away, so an assumption that overstated the rate
> understated the distance. The assumed value is an **upper bound** on the true
> tier-1 rate for all three symbols — asserted by test, so a future retrieval
> that moved a rate above 0.50% would fail here rather than silently invalidate
> the argument.

**THIS IS LUCK, NOT METHOD, AND IT IS RECORDED AS SUCH.** The closing record §4's
recurring defect class is *"a numerical criterion written from a mental model of
a quantity rather than from its implementation or its achievable range"*, and
amendment 1 §8.1 adds that **errors in the conservative direction are the ones
that survive review**. This was exactly such an error: unsourced, conservative,
and therefore unexamined. It happened to hold. **The next one need not**, and
the check that catches them is retrieval regardless of which way the number
points.

### 4.1 What the retrieved rate actually implies at the worst bar

Arithmetic on §3's rates and report 24 §7.5's per-symbol notional. **Nothing
here is a performance quantity**: it is the venue's stated requirement against a
stated account size.

| symbol | notional at the worst bar | tier | MMR | **maintenance margin** |
|---|---:|:---:|---:|---:|
| BTCUSDT | $9,261.34 | 1 | 0.40% | **$37.05** |
| ETHUSDT | $11,561.97 | 1 | 0.40% | **$46.25** |
| SOLUSDT | $6,221.89 | 1 | 0.50% | **$31.11** |
| **total** | **$27,045.20** | — | — | **$114.40** |

**Against $2,000 of account value that is a maintenance margin ratio of 5.72%.**
Liquidation triggers at **100%** (§6). **On the most exposed bar in three years,
the account would have to lose $1,885.60 — 94.3% of itself — before the venue's
maintenance requirement bound.**

**WHAT THIS DOES AND DOES NOT SAY.** It says the *maintenance* requirement is
remote. It says nothing about whether losing 94% of the account is an acceptable
path to that point, nothing about the initial margin needed to open the book
(§6.3), and nothing about what a one-sided 28-position book does in a fast
move — report 24 §7.4 measured that 20.51% of occupied bars are entirely
one-sided, and no correlation quantity has been computed anywhere in this
project.

---

## 5. POSITION NETTING SEMANTICS — the finding 5.3 turns on

### 5.1 The venue nets. It does not carry parallel positions.

From [Bitget's hedge/one-way mode
guide](https://www.bitget.com/support/articles/12560603817602) and the
[trading-modes overview](https://www.bitget.com/academy/futures-trading-modes):

- **ONE-WAY MODE:** *"you can only hold positions in one direction for the same
  futures trading pair"*. **New entries in the same direction are MERGED** into
  the existing position; an entry in the opposite direction offsets or closes it.
- **HEDGE MODE:** *"you can hold positions in both long and short directions
  simultaneously"* — **one long and one short per pair, not many.** Same-side
  entries still merge into that side's position.

> **THEREFORE, UNDER EITHER MODE, REPORT 24'S "ELEVEN CONCURRENT ETH POSITIONS"
> IS ONE POSITION AT THE VENUE** — a single netted ETH long (or short) with a
> volume-weighted average entry price, carrying eleven reduce-only conditional
> orders at eleven distinct stop prices and eleven distinct targets.

**WHAT THAT CHANGES, STATED PLAINLY AND NOT ACTED ON:**

- **Report 24's occupancy numbers remain correct as measured.** They count
  *strategy positions* — signal-to-exit intervals — and that is the right unit
  for an exposure measurement. Notional, nominal risk and required leverage all
  sum identically whether the venue nets or not.
- **`maxPositionNum = 200` is not the relevant limit.** With netting the account
  holds at most 3 positions (one-way) or 6 (hedge), never 28. The limit that
  matters is the **conditional-order** count, §5.3.
- **The engine models something else.** `simulate.py` carries per-trade stop and
  target prices on independent positions and enforces *"one open position per
  symbol, no pyramiding"* in portfolio mode (`simulate.py:517`). Neither matches
  a netted position with N attached partial closes. **5.3 is building a
  different structure from the one currently modelled**, and this report is
  where that is recorded — it is not resolved here.
- **A netted position has ONE liquidation price**, computed on the averaged
  entry and the aggregate size, not eleven. Under cross margin it is not even
  per-symbol (§6).

### 5.2 Partial reduce-only TP/SL at multiple distinct trigger prices — YES

[Notice on the futures partial position TP/SL feature
upgrade](https://www.bitget.com/support/articles/12560603846567) documents
multiple take-profit and stop-loss orders attached to **one** position at
**different trigger prices**, with a worked example of two TP orders at two
prices on a single 1 BTC position. Post-upgrade, *"the sum of TP orders may
exceed the total position volume"*, where previously both had to stay within the
position size. Applies to **classic account mode**. Dedicated API endpoints
exist (`/api/v2/mix/order/place-tpsl-order`, `/api/v2/mix/order/place-plan-order`
and their modify/cancel siblings).

**So the structure 5.3 would need is supported by the venue.** Whether it is
what we should build is not decided here.

### 5.3 Order and position limits

| limit | value | source |
|---|---:|---|
| orders per symbol | **200** | `maxSymbolOrderNum`, retrieved |
| orders per product (USDT-M) | **1,000** | `maxProductOrderNum`, retrieved |
| positions | **200** | `maxPositionNum`, retrieved |
| **conditional / trigger orders per symbol** | **NOT DOCUMENTED** | §5.4 |

**Against report 24's measured worst case** — 11 concurrent strategy positions on
one symbol, 28 across the book — a netted implementation would need at most
**~22 conditional orders on the busiest symbol** (one stop and one target each)
and **~56 across the book**. Both sit far inside 200 and 1,000 **if** conditional
orders count against those limits.

### 5.4 AMBIGUITIES I COULD NOT RESOLVE FROM THE DOCUMENTATION

Recorded rather than guessed. **An ambiguity recorded is worth more than a
confident reading of a page that does not quite say it.**

1. **Whether trigger / plan orders count against `maxSymbolOrderNum`.** The
   field is documented as "the maximum number of orders for a specific symbol"
   with no statement about conditional orders, and no Bitget page reachable by
   automated fetch states a separate limit for pending trigger orders. **The
   only figure this project's design depends on is therefore undocumented.**
   It can be settled by an authenticated probe against the live account, which
   this step did not perform.
2. **The documented example value disagrees with the live value.** The Get
   Contract Config page's example shows `maxSymbolOrderNum: "999999"`; the live
   response for all three of our symbols is **200**. The live value is
   authoritative and is what is reported; the discrepancy is noted so a reader
   consulting the doc page is not surprised.
3. **`posLimit`** (0.2 / 0.1 / 0.15) is undefined by any reachable
   documentation. Carried verbatim, not interpreted.
4. **Whether the partial-TP/SL upgrade applies identically under a Unified
   Trading Account.** The notice names *"classic account mode"* specifically.
5. **Whether a netted position's attached conditional orders survive a partial
   fill of another conditional order in every case.** The upgrade notice
   describes one behaviour (remaining TP/SL orders stay active after a partial
   close; a limit-order path may auto-cancel the rest) but the two sentences do
   not obviously compose into a single rule.

**Position mode scope, which IS unambiguous:** the setting *"will apply to all
the trading pairs under the respective futures type"* — so it is
**account-level per product type (USDT-M), not per-symbol** — and *"you cannot
switch modes if you have open positions on any pair… if there is an existing
position or pending order, you will not be able to switch"*.

---

## 6. CROSS MARGIN MECHANICS AND THE LIQUIDATION TRIGGER

### 6.1 What is shared

From [How Margin Works in Bitget
Futures](https://www.bitget.com/support/articles/12560603817029): under cross
mode *"all available funds in your account are shared across positions"*; under
isolated mode *"margin is calculated separately for each position and does not
affect others"*.

### 6.2 The liquidation trigger

From Bitget's [liquidation
overview](https://www.bitget.com/futures/introduction/liquidation-summarize):

| mode | trigger condition |
|---|---|
| **cross** | *"Cross-account equity (excluding isolated margin and isolated unrealized gains/losses) < the sum of the maintenance margins of all trading pairs"* |
| **isolated** | *"When the sum of the isolated margin and the unrealized PnL is less than the maintenance margin"* |

Both are the same statement in different scopes: **the maintenance margin ratio
reaches 100%**, where the ratio is maintenance margin ÷ margin balance. Above
100%, partial liquidation begins; at **160%** the remainder is closed at the
bankruptcy price; the platform de-leverages gradually — cancelling orders,
netting positions, reducing leverage tiers — before liquidating what is left.
Auto-deleveraging activates only when the insurance fund is depleted or falls
30% from its peak.

**THE SCOPE IS THE WHOLE USDT-M BOOK.** Under cross the requirement is the
**sum over all pairs**, which is exactly the $114.40 computed in §4.1 — and it
is why the decision to run cross margin matters: under isolated, each position's
margin stands alone and a wide-stop trade's liquidation price can sit inside its
own stop, which is the reason recorded for the decision. **That decision was
taken before this retrieval and nothing here was filtered by it.**

### 6.3 What the leverage setting does — and the constraint that actually binds

**The leverage setting does not change the maintenance margin rate.** The MMR
comes from the tier, and the tier is selected by **position value**, per Bitget's
[position tier
article](https://www.bitget.com/support/articles/12560603819706): *"As position
value increases, the maximum supported leverage is reduced and the required
maintenance margin rate increases"*. Leverage enters **initial margin** —
*"Initial margin = position size × mark price ÷ leverage"* — and through it the
liquidation price.

**So the venue constraint that binds this book is INITIAL margin, not
maintenance margin.** At report 24's worst bar of $27,045.20 of notional:

| leverage setting | initial margin required | fits in $2,000? |
|---:|---:|:---:|
| 3× | $9,015.07 | **no** |
| 5× | $5,409.04 | **no** |
| 10× | $2,704.52 | **no** |
| **14×** | **$1,931.80** | **yes** |
| 20× | $1,352.26 | yes |
| 50× | $540.90 | yes |
| **150× / 100× (venue tier-1 maximum)** | **$201.04** | yes |

**To open $27,045 on $2,000 the account needs a leverage setting of at least
13.53× — which is exactly report 24 §7.1's "required leverage" figure, and the
venue permits up to 150×/100× in tier 1.** The venue is not the binding
constraint anywhere in the measured range.

### 6.4 Account types

Bitget distinguishes **classic accounts** from the **Unified Trading Account
(UTA)**, and the distinction changes the margin pool:

- **Classic:** futures margin is USDT; balances are separate per product with
  manual transfers between them.
- **UTA:** one shared balance across spot, margin and futures. In **Advanced
  Mode** other assets serve as collateral at a per-asset collateral ratio,
  converted to USD equivalent, and PnL offsets across products. UTA also offers
  an isolated-margin mode and a basic mode in which spot and futures margin stay
  relatively separate. Main accounts can revert to classic; **sub-accounts
  cannot be reverted once upgraded.**

**Everything in §3 and §6 above is the CLASSIC-account reading**, which is what
the maintenance-margin change notice and the tier documentation address by name.
**Which account type this project will run on is not decided here**, and the
figures would need re-checking under UTA Advanced Mode, where the collateral
ratio changes what "account value" means in the liquidation condition.

---

## 7. STATIC CODE CHECK — where `max_leverage` is read

**READ ONLY. NOTHING WAS CHANGED.** `src/engine/costs.py` is untouched and
`max_leverage` still reads 3.0.

| location | what it does |
|---|---|
| `src/engine/costs.py:114` | **the declaration**, `max_leverage: float = 3.0`, directly under the comment *"NOT a probed exchange constraint — an unmeasured placeholder"* |
| `src/engine/costs.py:195` | `leverage_term()` → `risk_usd / (equity_usd × max_leverage)` = **0.333%**. Feeds `stop_min_pct` as `max(n_cost × c_roundtrip, leverage_term)`. **Never binds**: the cost term is 1.020%–1.320%, three to four times larger. |
| `src/engine/simulate.py:623` | **the refusal.** `cap = cfg.equity_usd * cfg.max_leverage`; if `concurrent + t["notional"] > cap` the trade is **dropped**, counted as `refused["insufficient_margin"]`, and the walk continues. |
| `src/engine/simulate.py:527` | docstring stating that rule (portfolio-mode constraint 3) |
| `src/engine/diagnostics.py:71` | prints the value in a config line; no behaviour |
| `src/analysis/structural_pass.py:533` | recomputes the leverage term independently for report 07's floor table; reporting only |
| `src/regime/measure.py:128` | comment only — names it among the inputs to `stop_min_pct` |
| `tests/test_portfolio.py:156,165,171,176,187` · `tests/test_modes.py:75` | tests that pin the cap's behaviour by setting it to 0.35 / 0.65 and asserting notional stays under `equity × max_leverage` |

### 7.1 Report 24 §7.2's claim, verified

Report 24 §7.2 states the engine *"refuses trades whose notional could not have
been carried"*. **The claim is accurate but narrower than the phrasing
suggests**, and the three qualifications matter:

1. **PORTFOLIO MODE ONLY.** The check is inside `if mode == "portfolio"`. In
   SIGNAL mode — *"no position limit, no cooldown, no margin cap, no interaction
   of any kind"* — it does not run at all.
2. **THE REFUSAL DROPS THE SIGNAL SILENTLY.** It increments a counter and
   `continue`s. It does not resize the position, does not queue it, and does not
   raise. Signals are therefore censored **by arrival order**, which the
   engine's own docstring already flags as dropping *"~30% of signals by arrival
   order rather than by the gate"*.
3. **IT NEVER ACTED ON REPORT 24'S FIGURES.** `src/analysis/exposure_profile.py`
   computes its own occupancy timeline with `CONCURRENCY_CAP = None` and does not
   import `simulate`. Report 24's numbers were measured **with no cap applied**,
   which is what it says, and the engine's refusal is a separate mechanism that
   was not in that path.

**No change is proposed to any of it.** Whether `max_leverage` should hold the
venue's number, a chosen risk number, or nothing at all is 5.2's decision.

---

## 8. THE TEMPORAL LIMITATION — a named limitation

> **THESE ARE TODAY'S VENUE PARAMETERS. THE BACKTEST WINDOW IS 2022-01-01 TO
> 2024-12-31, AND THIS RETRIEVAL CANNOT ESTABLISH WHAT THE VENUE'S PARAMETERS
> WERE OVER THAT WINDOW.**

Retrieved on **2026-08-11**, roughly **nineteen months after the window's end**.
Neither endpoint publishes history: `contracts` and `query-position-lever` both
report the **current** contract state only, exactly as
`src/engine/contracts.py` already records for tick size (*"Bitget's
/api/v2/mix/market/contracts reports the CURRENT contract state only"*).

**What may have differed over 2022–2024 and cannot be recovered:**

- **tier bands, leverage caps and maintenance margin rates.** Bitget's maximum
  leverage on major pairs has been raised over time across the industry; a
  125× cap appears in Bitget's own tier article against the 150× retrieved here.
- **minimum order quantity and minimum notional.**
- **the maintenance margin formula itself** — the progressive form dates from
  **2025-11-10**, so **for the whole of the backtest window the whole-position
  form applied.** Inside tier 1 the two are identical, so this changes nothing
  for us, but it is a formula change inside the period between the window and
  this retrieval.
- **`qty_step`.** The one parameter with partial history is the **price tick**,
  which `config/contracts_cache.json` carries as an empirically derived schedule
  (SOL moved from 0.0001 to 0.001 on 2024-08-14). **No such history exists for
  the quantity step, the tier table or the order limits.**

**This is stated in the same terms the thesis §5.3 uses for funding:** *"0.01%
per 8h is the venue's baseline and is used as a stated assumption."* So here —
**today's tier table is the venue's current state and is used as a stated
assumption about the backtest window.** It is not smoothed over, and any
conclusion that depends on the window's actual tiers rather than today's is not
supported by this retrieval.

**The direction of the risk is favourable but not zero.** Leverage caps have
generally risen and maintenance rates generally fallen over the period, so
today's tier 1 is if anything *more* permissive than 2022's. That is an
industry-wide tendency, **not a measurement**, and it is recorded as a reason to
be relaxed about the limitation rather than as evidence against it.

---

## 9. WHAT COULD NOT BE RETRIEVED, AND WHY

| item | status | what it would have provided |
|---|---|---|
| **the account's current leverage setting, position mode and margin mode** | **REQUIRES AUTHENTICATION** (`/api/v2/mix/account/*`) | what the account is actually configured to do today. **Not worked around and not approximated.** |
| **the account's type (classic vs UTA) and VIP tier** | **REQUIRES AUTHENTICATION** | which of §6.4's readings applies |
| **whether conditional orders count against `maxSymbolOrderNum`** | **NOT DOCUMENTED** | the only order-limit figure the design depends on (§5.4) |
| **a separate limit for pending trigger orders** | **NOT DOCUMENTED** | as above |
| **cross- vs isolated-specific tier tables** | **DOES NOT EXIST** | the endpoint takes no margin-mode parameter and returns identical rows (§3.4) |
| **historical tier tables, leverage caps, lot sizes** | **NO ENDPOINT PUBLISHES HISTORY** | the window's actual constraints (§8) |
| **`posLimit`'s meaning** | **NOT DOCUMENTED** | unknown; carried verbatim, not interpreted |
| **the API documentation pages themselves** | **JS-RENDERED, RETURNED NO ENDPOINT CONTENT** | field-by-field descriptions. Paths were confirmed against the live API instead. |
| `/api/v2/uta/public/instruments` | **HTTP 404** | a UTA-side instrument list, had one existed at that path |
| `/api/v2/mix/market/contracts-oi` | **HTTP 404** (`40404 Request URL NOT FOUND`) | open-interest limits |

**No unauthenticated approximation was substituted for anything on this list.**

---

## 10. WHAT CONTRADICTS A FROZEN DOCUMENT OR REPORT 24

**Three items. One contradicts report 24's framing, one contradicts an
assumption behind report 24's structural model, and one does not contradict
anything but corrects a number's status.**

### 10.1 `max_leverage = 3.0` IS NOT A VENUE CONSTRAINT, AND REPORT 24 §7.2 READ IT AS ONE

Report 24 §7.2 tabulated required leverage against *"the engine's own configured
`max_leverage = 3.0`"* and reported that it is exceeded on **63.93% of bars**.
It flagged the source's own placeholder disclaimer, so it did not claim the
number was the venue's — but the table's framing invites that reading, and the
retrieved answer is unambiguous:

| | value |
|---|---|
| engine placeholder | **3×** |
| **venue tier-1 maximum, BTC / ETH** | **150×** |
| **venue tier-1 maximum, SOL** | **100×** |
| ratio | **the placeholder is 33–50× more restrictive** |

**The venue permits the entire measured book, including the 13.52× worst bar,
with no tier change and no special approval.** The "63.93% of bars exceed the
cap" figure is therefore a statement about **an unmeasured placeholder**, not
about carryability. **Report 24's numbers are unchanged and correct; what
changes is what they are measured against.** 5.2 must choose a cap on risk
grounds, and this report supplies the venue's ceiling rather than the answer.

### 10.2 THE ENGINE AND REPORT 24 BOTH MODEL PARALLEL POSITIONS; THE VENUE NETS

Report 24 measured up to **11 concurrent positions on one symbol** and 28 across
the book. **The venue would hold one position per symbol per side** (§5.1).

**This does not invalidate report 24.** Its unit — signal-to-exit intervals — is
the right one for an exposure measurement, and every aggregate it reports
(notional, nominal risk, required leverage, one-sidedness) is identical under
netting. **It does mean the engine's per-trade independent-position model, and
its portfolio-mode "one open position per symbol, no pyramiding" rule, describe
neither the venue nor the strategy as measured.** 5.3 will be building a netted
position with N attached partial reduce-only orders, which is a **structurally
different object** from what `simulate.py` currently constructs. Recorded here;
not resolved here.

### 10.3 THE 0.5% MAINTENANCE RATE WAS AN ASSUMPTION AND IS NOW A RETRIEVED FIGURE

No frozen document states it — it lives in design discussion — so nothing is
contradicted. **Its status changes**: 0.40% / 0.40% / 0.50% retrieved, the
assumption confirmed as an upper bound, and the argument built on it supported
(§4). Recorded because the closing record §4.1's rule is to derive every
criterion from its implementation or measured range, and this one had not been.

### 10.4 Nothing else disagrees

- `config/contracts_cache.json` agrees with the venue on **12 of 12** fields
  (§2.1). Report 24 §2's `qty_step` and minimum-notional values stand.
- `data/reference/bitget_fees.json` records `max_leverage` 150 / 150 / 100 from
  the same `maxLever` field, retrieved earlier and **unchanged**.
- `fundInterval = 8` confirms the 8-hour settlement cadence the thesis §5.3's
  time exit is denominated in.
- The thesis, amendment 1, the closing record and report 24 are otherwise
  untouched by anything retrieved here.

---

## 11. VERIFICATION

| check | result |
|---|---|
| **schema assertions** — every field the report depends on is required and typed at parse time | **pass.** Deleting any of the 18 required contract fields or any of the 6 tier fields raises `SchemaError`; non-numeric, non-finite and zero values raise |
| **negative control — truncation** | **pass.** Both response types cut to 60% of their length raise *"not valid JSON"* |
| **negative control — renamed field** | **pass.** `keepMarginRate` → `maintMarginRate` and `sizeMultiplier` → `lotSize` both raise, naming the missing field |
| **negative control — empty tier table** | **pass.** `data: []`, `null` and `{}` all raise; an empty contract table raises *"EMPTY"* |
| **structural refusals** | **pass.** Planted band gap, falling MMR, rising leverage cap and missing level each raise; out-of-order rows are sorted rather than refused |
| **coverage** — 0 to ≥ $30,000, no gap | **pass** on all three symbols; a table truncated below the range raises |
| **each book state maps to exactly one tier** | **pass** — and to **tier 1** on every symbol |
| **offset derivation** | **pass.** `value × rate − offset` equals the slice-by-slice sum at every band edge and mid-band, on all three symbols; tier-1 offset is 0; the progressive form is never harsher than the flat form |
| **cache cross-check** | **pass** — 12 of 12 agree; a **planted** cache disagreement is detected and does not leak into other fields |
| **round trip** | **pass.** Both tables re-derived from the file bytes independently of the module's loader and required equal; recorded SHA-256 matches every file; bodies asserted verbatim (no newline, single line, `{"code":` prefix) |
| **no market data / no engine** | **pass**, over the import graph: `src.timeframe`, `src.folds`, `src.analysis`, `src.engine`, `src.sweep`, `src.regime`, `simulate`, pandas, numpy and pyarrow are all refused |
| **firewall guard, WIDENED** | **pass.** Twelve banned names — the nine from reports 19–21 and 24 plus **`drawdown`, `sortino`, `gross_pnl`** — checked over identifiers and non-docstring string literals. A test asserts the new list is a superset of the old one, so the widening cannot be quietly dropped |
| **nothing is written to config or the engine** | **pass.** The only write targets are the snapshot directory and its manifest; `contracts_cache.json` is opened read-only |
| **full suite** | **782 passing / 782** (745 baseline at `4e08e1b` + **37** new) |

**No holdout seal test applies and none is present.** This module cannot reach
the data layer, so there is no path on which a seal could be breached and a
planted mutation would have nothing to catch. That is stated rather than
silently omitted.

---

## 12. WHAT THIS HANDS TO 5.2 — no decision is made here

1. **The venue's ceiling is 150× / 150× / 100× in tier 1, and tier 1 extends to
   $200,000 / $200,000 / $50,000.** The whole measured book — median $7,182,
   worst $27,045 — sits inside it with the nearest boundary 1.85× away.
   **The cap is ours to choose, not the venue's to impose.**
2. **Maintenance margin at the worst bar is $114.40 against $2,000: a 5.72%
   margin ratio where liquidation is 100%.** The retrieved rates are at or below
   the 0.5% the design argument assumed.
3. **The venue nets.** Whatever cap 5.2 sets, the thing being capped is
   conditional orders against a netted position, not parallel positions — and
   5.3's sizing fix lands on that structure.
4. **200 orders per symbol, 1,000 per product, 200 positions**, with the
   conditional-order question open (§5.4). A netted implementation of report
   24's worst bar needs ~22 conditional orders on one symbol and ~56 across the
   book.
5. **Position mode is account-level per product type and cannot be switched with
   any open position or pending order.** It is a setup-time decision, not a
   runtime one.
6. **Everything here is today's state** (§8) and the account-level settings are
   unretrieved (§9). An authenticated probe is the natural next retrieval and it
   is not this step.

---

**Files.** `src/venue/__init__.py` · `src/venue/bitget_constraints.py` ·
`data/reference/bitget_venue/` (6 raw bodies + manifest) · `.gitignore` (one negation, with its justification) ·
`tests/test_venue_constraints.py` · this report.
**Not modified:** `src/engine/costs.py` and every other engine file —
`max_leverage` still reads 3.0 · `config/contracts_cache.json` (read only) ·
`src/analysis/exposure_profile.py` · `src/analysis/sweep_population.py` · every
frozen document numbered 22, 22a, 23 and 24.
**No strategy parameter was chosen.** No cap, no leverage setting, no margin
mode, nothing written to config.
**Holdout:** untouched by construction — this module cannot reach the data layer.
**Firewall:** armed, AST-guarded, widened by three names.
