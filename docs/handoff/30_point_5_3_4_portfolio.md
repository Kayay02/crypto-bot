# REPORT 30 — THE PORTFOLIO EXECUTION PATH, BUILT AND PROVEN AND NOT RUN

**Point 5, sub-point 5.3, step 4 — the last step in Point 5.** A BUILD and a
PROOF. The engine that resolves exits exists at this commit and **has never been
run against a real 1m bar.**

**WHAT THIS IS.** `src/engine/portfolio.py` is the one place that carries the
frozen aggregate risk budget (document 05 and its two amendments), the frozen
exit resolution specification (document 06 and its amendment) and report 28's
exchange-real sizing. Nothing else in the repository holds all three, and nothing
else is permitted to resolve an exit.

> ### THE ENGINE IS BUILT HERE. IT RUNS FOR THE FIRST TIME AFTER POINT 4.
>
> The moment this resolves a level against a real 1m bar, `exit_reason` exists,
> and **counting one value of it IS the win rate.** The performance firewall
> holds until the validation design is pre-registered, because a validation
> design chosen after seeing results is a design chosen to fit them.
>
> **`full` MODE WAS NEVER RUN ON REAL DATA IN THIS STEP.** Not once, not on one
> symbol, not on one fold, not on one day. Section 9 states how that is
> asserted rather than merely promised.

**THE ONE REAL-DATA EXECUTION IS THE `max_hold` REGRESSION**, which evaluates no
level and reads no 1m bar, and which reproduces report 26 **exactly on the first
run**: 6,021 taken, 5,363 skipped, 1,973 / 1,963 / 2,085 per symbol.

---

## 1. PROVENANCE

| item | value |
|---|---|
| `git rev-parse HEAD` at build | **`7f46b1a`** — report 29, the sealed 1m loader |
| module | **`src/engine/portfolio.py`** |
| tests | **`tests/test_portfolio_path.py`** — see §11.1 on the name |
| budget, rotation, charging, intra-bar order | `src/risk/budget.py` |
| fill rules, funding rate, settlement count | `src/risk/exit_spec.py` |
| geometry, flooring, viability, denominator | `src/engine/sizing.py`, unmodified |
| cost algebra, tick rounding, haircut | `src/engine/costs.py`, unmodified |
| lot steps and price ticks | `config/contracts_cache.json` via `contracts.py` |
| 1m bars | `src/timeframe/sealed_1m.py`, report 29's loader, and nothing else |
| candidate population | report 26's own `budget_cost.candidates`, supplied by the caller |

**NOT MODIFIED:** `src/engine/simulate.py` · `src/engine/costs.py` ·
`src/engine/sizing.py` · `src/risk/budget.py` · `src/risk/exit_spec.py` ·
`src/timeframe/sealed_1m.py` · `config/contracts_cache.json` · every frozen
document numbered 22, 22a, 23, 24, 25, 26, 27, 28, 29, 05, 05a, 05b, 06, 06a ·
**`tests/test_portfolio.py`**, which already existed (§11.1).

**MODIFIED, AND ONLY THE THREE WIRING ASSERTIONS §4 JUSTIFIES:**
`tests/test_risk_budget.py` · `tests/test_exit_spec.py` ·
`tests/test_sealed_1m.py`.

**WHY `simulate.py` IS NOT PATCHED.** It carries its own "one open position per
symbol, no pyramiding" rule, its own margin refusal at a placeholder ceiling
report 26 §12.1 measured as binding on **16.14%** of bars, and dollar-solved
targets report 28 §3 showed move when the quantity is floored. **Report 26 §12.1
and report 28 §13.5 both record that it must be REPLACED rather than adapted.**
It is left alone: its tests pin its behaviour and other work depends on it.

---

## 2. THE TWO MODES, AND THE GUARD ON THE SECOND

| mode | what it does | reads 1m? |
|---|---|---|
| **`max_hold`** | every position runs to its time exit; **no level is evaluated** | **no** |
| **`full`** | stops and targets resolved on 1m per document 06 | yes |

`max_hold` is the **default** and is the regression path.

### 2.1 `full` MODE CANNOT BE ENTERED BY A BOOLEAN FLIP

    pf.run(..., mode=MODE_FULL)                      -> FirewallError
    pf.run(..., mode=MODE_FULL, firewall_token=True) -> FirewallError
    pf.run(..., mode=MODE_FULL,
           firewall_token="FIREWALL_ACKNOWLEDGED_POINT_4_COMMITTED")  -> runs

> **A BOOLEAN WOULD BE THE WRONG SHAPE.** Someone flipping `evaluate_exits=True`
> has not necessarily registered that they are spending the firewall. Someone
> typing `FIREWALL_ACKNOWLEDGED_POINT_4_COMMITTED` has — **and the string is
> greppable across the whole repository afterwards**, so every place the
> firewall was spent is findable by one search, for ever.

The refusal is asserted against the absent token and against six near-misses
including `True`, the empty string, and the token in lower case. **The exception
is never caught inside the module**: degrading to `max_hold` would silently
return a different population than the caller asked for.

---

## 3. WHERE EVERY FROZEN VALUE IS READ FROM

**IDENTITY, NOT EQUALITY.** A test asserts each of these is the frozen module's
own object, so a copy that happens to match today cannot stop matching tomorrow.

| value | read from |
|---|---|
| `BUDGET_USD`, `UNIT_USD`, `MAX_SLOTS` | `budget.MAX_AGGREGATE_OPEN_RISK_USD` / `RISK_PER_TRADE_USD` / `FULL_SIZE_POSITIONS` |
| rotation table, period, modulus | `budget.SYMBOL_ROTATION` / `ROTATION_PERIOD_MS` / `ROTATION_MODULUS` |
| charging basis, intra-bar order | `budget.BUDGET_CHARGES` / `INTRA_BAR_ORDER` |
| the 1h bar period | `budget.ROTATION_PERIOD_MS` — **the same object**, because Rule A's period IS the bar period and its docstring says so |
| the 1m bar period | `sealed_1m.BAR_MS` |
| funding rate and settlement count | `exit_spec.FUNDING_RATE_PER_SETTLEMENT` / `FUNDING_SETTLEMENTS_CHARGED` |
| reward-to-risk, ATR multiple, stop floor | `sizing.REWARD_TO_RISK` and `sizing`'s own functions |
| lot step, minimum quantity, minimum notional, price tick | `contracts.py`, from the cache |

**AND NO NUMERIC LITERAL IN THE MODULE EQUALS ANY OF THEM.** The test builds the
forbidden set from the frozen modules *and* the contract cache — every
`qty_step`, `min_trade_num`, `min_trade_usdt` and every price-tick segment — and
then asserts the module's entire literal set is `{0, 1, 10000.0}`. **A restated
constant is a constant that can drift**, and the only literals this module needs
are a zero, a one, and the basis-point divisor.

### 3.1 THE TIME EXIT IS SUPPLIED, NOT RE-DERIVED, AND THAT IS THE POINT

> **DOCUMENT 06 §6.1 RECORDS THAT `n = 3` IS TWO DIFFERENT QUANTITIES.** Thesis
> §5.3 uses it as a settlement **INDEX** in the exit rule and as a **COUNT** of
> settlements crossed in the funding budget. The enumeration shows they coincide
> on only **3 of 24 entry hours**.

`FUNDING_SETTLEMENTS_CHARGED` is the **COUNT**. Re-deriving the time exit from it
would conflate the two — **and the conflation would be numerically invisible,
because both are 3.** So the max-hold bar arrives per candidate from the frozen
calendar function that owns the index, and this module never computes it.

---

## 4. THE IMPORT ASSERTION, WIDENED ONCE, BY ONE FILE

> **`src/engine` IMPORTING `src/risk` REVERSES AN ASSERTION REPORTS 26 §12.2 AND
> 28 §11.1 BOTH ENFORCED.**

**THAT ASSERTION WAS ALWAYS SCOPED, AND ITS OWN TEXT SAYS SO.** Its docstring
reads *"NOTHING IS WIRED IN. No engine file imports src/risk. That wiring is
5.3's work"*; document 05 §10 requires the budget be wired at 5.3; report 28
§13.5 records that `simulate.py` must be replaced. **This module is that
replacement and this commit is that wiring.**

**IT IS SPENT ON ONE FILE, NOT RETIRED.** Three guards were changed and each
keeps its teeth:

| guard | before | after |
|---|---|---|
| `test_risk_budget.py::test_nothing_is_wired_in_yet` | no engine file may import `src.risk` | **only `src/engine/portfolio.py` may**; every other engine file still refused unconditionally, and the allowlist is explicit so a second importer anywhere still fails |
| `test_exit_spec.py::test_nothing_is_wired_in_yet` | no engine file may name `exit_spec` | same, one file exempt — **plus a new test asserting the exempt file reads the spec's own objects** |
| `test_sealed_1m.py` | no engine file may name `sealed_1m` | same, one file exempt — **plus a new test asserting that file reaches 1m by no other route**: no `glob`, no `pyarrow`, no `simulate`, no `ohlcv_1m` path, no `year=` token |

**RECORDED ON REPORT 28 §11.1's TERMS**, which is where this project decided that
a guard that fires is answered by changing the module and not the guard. **This
is the one case where the module is what the guard was waiting for** — and the
widening is written as an allowlist rather than a deletion precisely so that the
next unpermitted importer still fails.

---

## 5. THE BAR LOOP, AS IMPLEMENTED

One continuous forward pass over the hourly grid. Per bar:

    1. EXITS   every position whose exit falls at or before this bar closes,
               each returning the NOMINAL unit to the budget. In `full` mode
               resolution happens HERE, one hour at a time, against the 1m bars
               of THIS hour only.
    2. ENTRIES this bar's signals, against the remaining budget, in the priority
               order Rule A gives for THIS bar:
                   rotation = (bar_open_ms // 3_600_000) mod 3

**EXITS BEFORE ENTRIES, AND THE SAME UNIT MAY FUND BOTH AT ONE CLOSE.** Under
report 24 §5.3's half-open convention the closing position's last open bar is X
and the opening position's first is X+1, so the two never overlap on the
occupancy timeline. Evaluating entries first would model a sequence that cannot
occur live and would inflate the skip rate by an artefact of loop order.

**A SIGNAL ALLOCATED LESS THAN A VIABLE AMOUNT IS SKIPPED**, with a reason code —
`BUDGET_FULL`, `PARTIAL_ALLOCATION`, `BELOW_MIN_QTY` or `BELOW_MIN_NOTIONAL`.
**Not queued, not deferred, not resized later**, exactly as document 05 §3
specifies. A fixture asserts the seventh of seven overlapping signals is the one
skipped — **arrival order, not price and not symbol.**

### 5.1 PATH DEPENDENCE IS STRUCTURAL, NOT INCIDENTAL

> **THERE IS NO PRE-COMPUTED EXIT SCHEDULE, NO TWO-PASS DESIGN AND NO
> LOOKAHEAD.**

In `full` mode whether a signal is taken depends on when earlier positions
exited, which depends on how they resolved — **a stop frees its slot hours before
a time exit would.** Document 05 §6 pre-registered exactly this. A design that
resolved exits across the whole window before evaluating entries would be
**wrong, not merely slower.**

**ASSERTED THREE WAYS.** Exactly one `for` loop over the grid, over the AST. No
`reversed(`, `[::-1]`, `shift(-` or `iloc[i + 1]` among the module's executable
tokens. And, on a synthetic run, **every 1m window the loop requested is exactly
one bar wide, the sequence of window starts never goes backwards, and no hour is
revisited.**

### 5.2 THE CACHE, AND WHY ITS GRANULARITY IS AN HOUR

Up to six concurrent positions each needing up to 24 hours of 1m bars would
otherwise re-read the same minutes once per position per hour.

> **A DAY-CHUNKED CACHE WOULD READ 1m BARS FROM AFTER THE BAR THE LOOP IS
> STANDING ON.** That is lookahead in the only sense that matters — data crossing
> the boundary before the decision does — even though nothing would consult it.
> **Keying on the hour makes the cache incapable of it rather than merely not
> doing it**, and mutation H1 (§10) is what proves the distinction is enforced.

**CACHE CORRECTNESS, RUN FOR REAL ON AN IN-SAMPLE HOUR:** a miss and a hit are
both asserted **frame-identical to a fresh `sealed_1m.load`, on all three
symbols**; a hit is asserted to be the same object, so it cannot re-read; the key
is asserted to carry both the symbol and the hour, with two symbols' frames
required to differ; and a released hour is asserted to be re-read rather than
served stale. **No price is inspected — only frame equality.**

---

## 6. THE REGRESSION AGAINST REPORT 26

**`max_hold` mode, 2022-01-01 to 2024-12-31, one continuous pass.**

| | this module | report 26 | |
|---|---:|---:|---|
| taken | **6,021** | 6,021 | **exact** |
| skipped | **5,363** | 5,363 | **exact** |
| total | **11,384** | 11,384 | **exact** |
| BTCUSDT taken | **1,973** | 1,973 | **exact** |
| ETHUSDT taken | **1,963** | 1,963 | **exact** |
| SOLUSDT taken | **2,085** | 2,085 | **exact** |

**IT REPRODUCED ON THE FIRST RUN, WITH NO ADJUSTMENT.** That is the result this
step needed: the budget, the rotation and the intra-bar order in the execution
path are the same machinery report 26 verified, so every figure that report
states describes the rule that ships.

**Per symbol skipped: 1,762 / 1,752 / 1,849.**

**THE ONLY SKIP REASON IS `BUDGET_FULL`.** Zero viability failures, which
confirms report 28 §6.2's measurement of zero on both populations at the frozen
values — now confirmed through a different code path.

**EVERY POSITION EXITS `time`, and both flags are zero**, because the mode
evaluates no level. `exit_price` is `NaN` on every row: **`max_hold` mode reads
no bar, so it has no exit price to report**, and inventing one would be inventing
a fill.

### 6.1 THE BUDGET INVARIANTS, ON THE REGRESSION

| invariant | result |
|---|---|
| concurrency never exceeds 6 | **holds** — and the peak **is exactly 6**, so the cap actually binds |
| concurrency never negative | **holds** |
| open nominal risk never exceeds $120.00 | **holds** — the maximum is exactly **$120.00** |
| remaining budget never negative | **holds** |
| remaining budget always an exact multiple of $20.00 | **holds**, to 1e-9 |
| partial-allocation branch counter | **0** |
| the book closes | **holds** — concurrency returns to zero |

**THE PEAK IS ASSERTED TO EQUAL THE CAP, NOT MERELY TO RESPECT IT.** A regression
in which the budget never binds would prove nothing about the budget.

**DUAL RISK RECORDING** (report 28 §7): every row carries both figures. Nominal
is $20.00 on all 6,021; realised ranges **18.3392 – 20.0000** with a median of
**19.9237**. Funding per unit is asserted to equal `entry x rate x count` on
**every row**, to 1e-12.

---

## 7. THE SYNTHETIC FIXTURES

**HAND-COMPUTED, ASSERTED ELEMENT BY ELEMENT, NEVER ON REAL DATA.** Every level,
fill, flag and identity below is exercised on a 1m series written by the test.

| # | fixture | expectation | result |
|---|---|---|---|
| 1 | 1m bar reaching the stop **exactly** | **fills** — E2 is inclusive: a conditional market order does not rest, so there is no queue to be behind | **holds**, long and short |
| 2 | 1m bar reaching the target **exactly** | **does NOT fill** — E3 requires a trade-through; a print at a resting limit says the level was reached, not that we were filled | **holds**, long and short |
| 3 | one tick **through** the target | **fills, at the target price**, no haircut and no improvement | **holds**, long and short |
| 4 | one 1m bar spanning **both** levels | the **stop** is taken, `both_levels_one_bar` set, count **1** | **holds** |
| 5 | a bar reaching only one level | flag **clear**, count **0** — so the flag means what it says | **holds** |
| 6 | a stop at minute 3 **of the max-hold bar** | the **stop** wins; exit at minute 3, before the close exists | **holds** — the control times out at the last minute of that same bar |
| 7 | 5 deliberate holes in the 1m series | flagged, count **exactly 5**, **resolved on the bars that exist** | **holds** |
| 8 | a complete series | flag clear, count **0**, **reported rather than omitted** | **holds** |
| 9 | a hole **at the level itself** | resolves on what is there, count **1** — no convention can know what happened in an absent minute | **holds** |

**FIXTURES 7 TO 9 ARE BINDING, NOT OPTIONAL.** Document 06a §5.3 requires E8 carry
reachable-value tests **because the flag fires zero times in sample** — report 19
measured the 1m layer as exactly full over 2022–2024. Without them the branch is
invisible to the entire suite, which is `MAKER_NONFILL_COST_R` again: a term
invisible to 545 tests because every one multiplied it by zero.

**THE TICK IS RESOLVED PER TIMESTAMP, AND THE FIXTURES FOUND IT.** The first
version of the test helper took the *latest* tick segment; the module disagreed
on SOLUSDT, because the synthetic bar sits in 2023 and SOL's tick changed on
2024-08-14 (report 28 §10). **The module was right and the helper was wrong**,
and it now resolves the tick at the timestamp exactly as the module does.

### 7.1 THE R IDENTITIES, END TO END, AT A FLOORED QUANTITY, WITH FUNDING

**Six cells — three symbols x two directions — every one floored.** The prices are
the ones the module **emitted**, not values recomputed for the test.

| identity | result |
|---|---|
| net proceeds at the emitted **stop price**, haircut as a fraction, funding charged = **−1.0 x realised risk** | **exact**, to 1e-12 relative, on all six |
| net proceeds at the emitted **target price**, funding charged = **+1.5 x realised risk** | **exact up to one tick, always favourable**, on all six |
| the emitted target fill price equals the target price | **holds** |
| the emitted stop fill price equals `costs.stop_fill_price` | **holds** |

**Document 06a E7.1 is what makes this exact rather than approximate**: funding
enters the denominator and is then paid out of it, so it cancels, and R stays a
fixed unit decided at entry.

### 7.2 THE FUNDING-IN-`d`-ONLY VARIANT MISSES, AND BY THE STATED AMOUNT

| cell | defective form | specified form |
|---|---:|---:|
| BTCUSDT long / short | 1.482502R / 1.482400R | 1.500000R |
| ETHUSDT long / short | 1.482600R / 1.482400R | 1.500000R |
| SOLUSDT long / short | 1.482868R / 1.482904R | 1.500000R |

**Range 1.4824R – 1.4829R**, against document 06a §3.2's stated *"about 1.482R"*.
**The stop identity still passes under the defective form**, which is exactly why
the defect is invisible: the identity an implementer checks first is unaffected.

**AND THE SOLVE IS PINNED AGAINST THE ENGINE'S.** With `funding_pu` zeroed, this
module's target solve is asserted **identical** to `sizing.target_price_on_tick`
on every cell and both directions, so the added term cannot become a second copy
of the engine's algebra that drifts.

**FUNDING IS CONSTRUCTED, NOT BACK-SOLVED.** On an ATR-bound reference,
`funding_pu = 9.00` while `0.0200 x s = 13.50` — **50% wrong** — and neither
`0.0200` nor `0.0180` appears among the module's literals. Document 06a §4 records
that the two coincide **exactly** at the floor stop, which is why they are
confusable.

### 7.3 A SECOND-ORDER TERM THE ENGINE'S DENOMINATOR DOES NOT MODEL

> **THE IDENTITY IS EXACT AT THE STOP PRICE. AT THE ACTUAL FILL PRICE IT IS NOT,
> AND THE DIFFERENCE IS NOT ZERO.**

`costs.position_size` charges the exit fee on the **stop level**, while the fill
sits a haircut away from it. Per unit:

    diff = (fill - stop)(1 -/+ f) + stop x haircut

**The sign is direction-dependent** — inside one unit for longs, beyond it for
shorts — and the magnitude is at most **0.0033 USDT** across the six cells,
**under 0.017% of a risk unit**. A test bounds it by
`qty x (stop x haircut x taker_fee + tick)` and asserts it stays under a
thousandth of the risk unit.

**IT IS RECORDED, NOT CORRECTED.** Correcting it means editing `costs.py`, which
reports 24, 26, 27 and 28 all rest on. **It is routed to the validation design**,
alongside the stop haircut itself, which document 06 §3.1 already records as an
unmeasured placeholder that *is* the entire slippage-and-gap model.

---

## 8. WHAT THE MODULE MAY NOT DO

| prohibition | how it is enforced |
|---|---|
| **no aggregate over `exit_reason`** | no `value_counts`, `groupby`, `Counter` or `nunique` among executable tokens; **no comparison anywhere whose operand is an exit-reason constant**, over the AST; exactly three `.sum()` calls and all three count FLAGS |
| **twelve-name firewall** | armed over identifiers, attributes and non-docstring literals |
| **no margin refusal** | `leverage` absent from every executable token; report 26 §12.1's placeholder is not reimplemented |
| **`costs.solve_target` unreachable** | absent from the code text and from every attribute access; `per_unit_denominator` **is** reached, and it is the engine's own |
| **`simulate.py` unreachable** | absent from every executable token — the docstring names it only to record that it is not patched |
| **1m only through the sealed loader** | `src.timeframe.sealed_1m` imported; `glob`, `pyarrow`, `simulate`, `src.analysis`, `src.sweep` all refused; no `ohlcv_1m` path and no `year=` token |
| **one carve-out for proceeds** | `proceeds` appears nowhere in the module; the identity helper lives in the test file and is asserted to be the only one there |

**THE TWO COUNTERS THAT DO EXIST ARE OVER FLAGS.** Document 06 §5.1 requires the
intrabar-precedence count be reported and document 06a §5.3 requires the
missing-bar fraction be reported **even when it is zero**. **Neither is a function
of which exit a trade took**, which is the line this firewall draws.

**IT EMITS ROWS AND NOTHING ELSE** — sixteen per-position fields and four per-skip
fields, asserted column by column. **Something else will summarise them, after
Point 4.**

---

## 9. `full` MODE WAS NEVER RUN ON REAL DATA — AND IT IS ASSERTED, NOT PROMISED

**A test walks the test module's own AST.** Every call to `run` with
`mode=MODE_FULL` must be handed a `cache=` built from the synthetic series
generator. **Two functions are exempt and both are named in the assertion**: the
token-refusal test, which never gets past the guard, and the holdout-refusal test
below.

**THE HOLDOUT-REFUSAL TEST FACES THE REAL LOADER DELIBERATELY**, and its own
request log is asserted:

    cache.requests == [(BTCUSDT, 2025-01-01T00:00Z, +1h)]      one request
    cache.misses == 1,  cache.hits == 0                        it was REFUSED

**The single request was the sealed one, and it raised before a file was
opened.** No readable hour was touched either — the position's first window is
the boundary hour itself.

**AND THE TOKEN IS TYPED IN ONE PLACE.** A test asserts the only functions whose
source contains `FIREWALL_TOKEN` are that one helper and the two named
exemptions, so the set of callers that spend the firewall is bounded and
greppable.

---

## 10. THE HOLDOUT MUTATIONS

**Two planted, both caught, both reverted, `git diff --stat` empty after each.**

### H1 — THE CACHE REACHES INTO 2025. Guard intact, so it may face the real tree.

`Bars1mCache.hour` widened from one hour to a **24-hour chunk** — report 29's
rejected design, and the one that would read past the bar the loop is on.

| | |
|---|---|
| caught by | **four assertions**: the forward-only request check, both cache tests, **and the no-restated-constant test**, which fired on the hardcoded `24` |
| the 2025 request | **`SealBreach`, raised before any file was opened** |
| requests made | one, `[1735686000000, 1735772400000)` — refused |

**THE PRE-READ GUARD WAS INTACT**, so per report 29 §9.3 this mutation was
permitted to face the real directory. It was, and nothing was opened.

### H2 — THE CACHE BYPASSES THE SEALED LOADER. Guard DISABLED → SYNTHETIC TREE ONLY.

The default loader replaced with a raw `glob` over `year=*`.

> **REPORT 29 §9.3 IS BINDING AND IT WAS OBEYED.** *"Any mutation that disables a
> pre-read guard runs against a synthetic tree, never the real directory."* That
> rule exists because it was violated at 5.3.3. **Only static assertions were run
> against the real repository, and they read nothing.**

| | |
|---|---|
| caught by | `test_1m_access_is_only_through_the_sealed_loader` and `test_the_execution_path_reaches_1m_ONLY_through_the_sealed_loader` — **both fire without opening anything** |
| demonstrated on | a **synthetic tree of empty files**, years 2022–2026 |
| what the bypass selected | **5 files, 2 of them sealed** — `year=2025` and `year=2026` |
| what the sealed loader allows on the same tree | **3 files, 0 sealed** |

---

## 11. WHAT CONTRADICTS A FROZEN DOCUMENT

**Nothing contradicts a frozen document.** Three departures from this step's own
brief are recorded instead.

### 11.1 THE TEST FILE NAME — `tests/test_portfolio.py` ALREADY EXISTED

The brief said to create it. **A file of that name has existed since `d04ba47`**
(Point 3): it is G1 fixtures 7 and 8, six tests pinning `simulate.py`'s cooldown
and margin refusal.

> **IT WAS OVERWRITTEN IN ERROR DURING THIS BUILD AND RESTORED FROM GIT
> IMMEDIATELY, BEFORE ANYTHING WAS COMMITTED.** `git diff` against it is empty
> and all six of its tests pass. The new suite went to
> **`tests/test_portfolio_path.py`**.

**Recorded rather than smoothed over.** Merging the two would have put tests
asserting `simulate` is unreachable into a module whose first line imports it,
and would have retitled a Point 3 file. **The brief could not have known the name
was taken; the existing file wins.**

### 11.2 THE MODULE TAKES ITS CANDIDATE POPULATION AS A PARAMETER

The signal population and the max-hold calendar arrive from the caller rather
than being built inside the execution path. **Two reasons, both structural**:
`src/engine` importing `src/analysis` would be a second reversal of the import
direction §4 spent once and deliberately; and §3.1's index-versus-count hazard is
avoided outright by never computing the time exit here. **The regression feeds it
report 26's own `candidates()`**, which is what makes the reproduction an
identity rather than a re-derivation.

### 11.3 THE FILL-PRICE TERM OF §7.3

Not a contradiction — an inherited approximation in `costs.position_size`, now
measured at under 0.017% of a risk unit and routed to the validation design.

---

## 12. VERIFICATION SUMMARY

| | tests |
|---|---:|
| baseline at `7f46b1a` | **1,070 passing** |
| new in `tests/test_portfolio_path.py` | **+52** |
| new in `tests/test_exit_spec.py` and `tests/test_sealed_1m.py` | **+2** |
| **total** | **1,124 passing / 1,124** |

| check | result |
|---|---|
| regression reproduces report 26 exactly | **passes**, first run, no adjustment |
| budget invariants, cap binds at exactly 6 | **passes** |
| `full` mode refused without the token | **passes**, six near-misses |
| every frozen value read by identity | **passes** |
| no literal equals a frozen value; literal set is `{0, 1, 10000.0}` | **passes** |
| nine fill and flag fixtures | **passes** |
| R identities end to end, six cells, floored | **passes**, exact to 1e-12 |
| funding-in-`d`-only misses, 1.4824R–1.4829R | **passes** |
| target solve identical to the engine's at zero funding | **passes** |
| single-pass, forward-only, one-hour windows | **passes** |
| cache identical to a fresh load, all symbols | **passes** |
| no aggregate over `exit_reason`; twelve names; no margin refusal | **passes** |
| `full` mode never run on real data | **passes**, asserted over the test AST |
| two holdout mutations planted, caught, reverted | **passes**, `git diff --stat` empty |

---

## 13. WHAT THIS HANDS FORWARD

1. **The execution path exists and is proven.** Budget, exits and sizing in one
   module, every frozen value read rather than restated.
2. **It has never resolved an exit against a real bar.** The firewall is intact
   and spending it requires typing a string that says so.
3. **Point 4 is now the blocking step.** The validation design must be
   pre-registered before `full` mode runs — and when it does, the first thing it
   will report is the two flag counts, which are zero in sample by construction
   and unknown out of it.
4. **`simulate.py` is superseded but not removed.** Retiring it, and its callers
   in `run.py`, `sweep.py` and `dispersion.py`, is later work.
5. **Two items are routed to the validation design**: the fill-price term of
   §7.3, and the stop haircut that document 06 §3.1 already records as the
   largest inherited weakness in the exit model.

---

**Files.** `src/engine/portfolio.py` · `tests/test_portfolio_path.py` · this
report, with the three wiring-assertion changes of §4.
**Firewall:** armed, twelve names, no aggregate over `exit_reason`, one recorded
carve-out in the test module.
**Holdout:** sealed and unspent. `full` mode was never run on real data; the one
real-data run is the `max_hold` regression, which reads no 1m bar.
