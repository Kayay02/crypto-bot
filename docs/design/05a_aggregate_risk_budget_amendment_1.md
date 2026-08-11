# AMENDMENT 1 TO THE AGGREGATE OPEN RISK BUDGET

## 1. HEADER — WHAT CHANGED

**This is Amendment 1 to `docs/design/05_aggregate_risk_budget.md`, frozen at
commit `a323237`.**

**THE ORIGINAL DOCUMENT IS UNALTERED.** Not one character of
`05_aggregate_risk_budget.md` has been edited. Its §11 specifies its own
amendment procedure — *"an amendment is a new document with a new commit and an
explicit statement of what changed and why; a silent edit is a contamination
event"* — and this document follows it. **Its SHA-256 is
`d5ac7bd61323d04e75a854baf14086932470175408f5e2db4ca6f4d3afad268f` and a test
asserts that value, so an edit to the frozen document fails the suite rather
than passing unnoticed.**

**WHAT CHANGED, IN ONE BLOCK.** Two specification gaps found in review. **Both
are gaps, not corrections**: nothing in document 05 is wrong, and nothing in it
is superseded.

| | gap | resolution |
|---|---|---|
| **A** | §3 allocates *"in arrival order"* and §5.1 defends arrival order as the only causally implementable rule. **Neither defines what happens when signals arrive SIMULTANEOUSLY.** On 1h bars all three symbols close at the same instant, so simultaneity is the ordinary case, not an edge case. | **RULE A**, §2: a priority order that rotates cyclically by bar, derived from the bar's own open timestamp. |
| **B** | §3 says a closing position *"returns exactly its own allocation"*. **It does not say whether the allocation charged is the NOMINAL $20.00 or the REALISED risk after `qty_step` flooring.** Once 5.3 implements flooring the two differ. | **RULE B**, §3: the budget is charged the **nominal** allocation. |

> ### THE LEVEL DID NOT CHANGE.
>
> **`MAX_AGGREGATE_OPEN_RISK_USD` REMAINS `120.00`.** `RISK_PER_TRADE_USD`
> remains `20.00`, `ACCOUNT_CAPITAL_USD` remains `2000.00`,
> `BUDGET_FRACTION_OF_CAPITAL` remains `0.06`, `FULL_SIZE_POSITIONS` remains
> `6`, `MARGIN_MODE` remains `"cross"` and `POSITION_MODE` remains `"hedge"`.
>
> **§2's DERIVATION IS UNTOUCHED AND IS NOT REVISITED.** The 30–50% tolerance,
> the one-fifth judgement, the choice of the conservative end, and the
> disclosure that the tolerance is **not recorded in any committed artifact**
> all stand exactly as frozen. **This amendment specifies mechanism, not
> appetite.** Nothing below could be used to argue for a different level, and no
> measurement of the level's cost exists at this commit (§6).

**SCOPE.** This amendment adds to **§3** (the allocation rule) and to **§4** (the
inert partial branch). It supersedes nothing. Read together, the rule as amended
is document 05 with §3 extended by Rules A and B and §4's inertness claim placed
on the explicit footing Rule B gives it.

**NO MEASUREMENT WAS RUN TO WRITE THIS.** No market data, no parquet, no bars,
no folds, no counts, no occupancy. The figures cited from reports 24 and 25 are
transcribed from frozen documents.

---

## 2. RULE A — THE INTRA-BAR TIE-BREAK

### 2.1 THE RULE

> **WHEN TWO OR MORE SIGNALS ARRIVE ON THE SAME BAR, THEY ARE ALLOCATED IN A
> PRIORITY ORDER THAT ROTATES CYCLICALLY BY BAR, DERIVED FROM THE BAR'S OWN OPEN
> TIMESTAMP.**

    rotation = (bar_open_epoch_ms // 3_600_000) mod 3

    rotation 0  ->  BTCUSDT, ETHUSDT, SOLUSDT
    rotation 1  ->  ETHUSDT, SOLUSDT, BTCUSDT
    rotation 2  ->  SOLUSDT, BTCUSDT, ETHUSDT

**ACROSS BARS, ARRIVAL ORDER IS UNCHANGED.** An earlier bar's signals are always
allocated before a later bar's, without exception. **Rotation orders only WITHIN
a bar**, and it is invoked only when a bar carries more than one signal. Document
05 §3's arrival-order rule is intact; this fills the hole underneath it.

**THE ROTATION IS A TOTAL ORDER ON THE TIED SET.** A bar yields at most one
signal per symbol — thesis §4.1 skips two-sided bars, so a bar that fires both
the long and the short trigger on a symbol opens nothing — so the tied set is a
subset of the three symbols and the rotation orders it completely. **There is no
second tie to break.**

### 2.2 WHY THE TIMESTAMP AND NOT A BAR INDEX

**THIS IS THE LOAD-BEARING DESIGN CHOICE IN RULE A AND IT IS NOT COSMETIC.**

**A BAR INDEX DEPENDS ON WHERE THE SERIES STARTS.** Different scopes trim
different amounts: report 24 discards a **114-bar** indicator warm-up before its
pooled scope begins, and each of its eighteen fold periods begins at its own
`folds.json` boundary. **Under an index-derived rotation the same UTC bar can
draw a different priority in the pooled run than in the fold run that contains
it, and two correct measurements of the same period would disagree about which
symbol was allocated first.**

> **THE TIMESTAMP IS A PROPERTY OF THE BAR ITSELF. THE INDEX IS A PROPERTY OF
> THE SLICE THE BAR HAPPENS TO BE IN.** The rule must depend only on the former.

### 2.2.1 THE HAZARD IS LATENT, NOT ACTIVE — CHECKED, AND THE CHECK CORRECTED A CLAIM

**AN INDEX-DERIVED ROTATION WOULD AGREE WITH THIS RULE ON EVERY SCOPE REPORT 24
CURRENTLY RUNS. THAT AGREEMENT IS AN ARITHMETIC COINCIDENCE AND IT IS RECORDED
RATHER THAN RELIED ON.**

The index rotation for a bar is `(index_of_bar) mod 3`, which differs from
`(bar_hours) mod 3` by `(start_hours) mod 3` — a constant per scope. **The two
rules therefore agree across two scopes exactly when the two scope starts differ
by a whole multiple of three hours.** For every scope this project currently
defines they do:

| scope start | offset from another scope start | ≡ 0 (mod 3)? |
|---|---|:---:|
| `folds.json` boundaries | whole days — **24 h**, and 24 = 3 × 8 | **yes** |
| the pooled scope's warm-up trim | **114 bars**, and 114 = 3 × 38 | **yes** |

**So the index rule is correct today BY ACCIDENT**, and it was verified to be so:
for report 24 §7.5's worst bar, the index computed from the pooled scope, from
the whole-window start, from fold 9's train start and from fold 8's test start
are **all congruent mod 3**, and all agree with the timestamp rule.

**IT WOULD DIVERGE SILENTLY ON ANY SCOPE STARTING AT A NON-MULTIPLE OF THREE
HOURS** — a warm-up of 113 or 115 bars, an intraday fold boundary, a resumed
run, a different indicator period. **None of those changes is one anyone would
think to check against a tie-break rule**, and the failure would appear as two
correct-looking measurements disagreeing about which symbol was allocated first.

**THIS IS PRECISELY THE DEFECT CLASS THIS PROJECT KEEPS FINDING.** The closing
record §3.4 records Point 4's stop rule as *"a fixed-percentage stop wearing an
ATR costume"* — a rule whose stated mechanism could never bind, correct-looking
because of an arithmetic relationship nobody had checked. **A tie-break that is
scope-invariant only because 114 and 24 happen to be divisible by 3 is the same
shape.** The timestamp rule is invariant by construction, and needs no such
coincidence to hold.

**BOTH FACTS ARE PINNED BY TEST**, so neither can decay: the timestamp rotation
is required to be identical for a given UTC bar computed from any series start;
an index implementation is required to **DISAGREE** on a scope offset by one
hour; and the present coincidence — that today's day-aligned scopes and the
114-bar trim make the two agree — is asserted explicitly, so that changing the
warm-up to a non-multiple of three fails a test and re-opens the question
deliberately rather than silently.

**A NOTE ON WHAT THIS CORRECTS.** The brief for this step stated the
scope-dependence as *"a live hazard, not a hypothetical one"*. **On checking, it
is neither: it is a latent one.** The underlying argument for reading the
timestamp is unaffected and is if anything stronger — a rule that is correct only
by coincidence is worse than one that is correct by construction, because it
provides no warning when the coincidence ends. **Recorded here because a claim
checked and found qualified is worth more than a claim repeated.**

### 2.3 BAR TIMESTAMPS ARE OPEN TIMES

**RESTATED HERE BECAUSE THE RULE IS ARITHMETIC ON THAT TIMESTAMP.** A close-time
reading would shift every rotation by exactly one bar and would therefore
produce a different priority on every bar in the window, silently and without
error.

Report 24 §1.1 establishes the convention from four independent sources:

| source | what it says |
|---|---|
| `src/data/backfill_bitget.py`, module docstring | *"Timestamps are the bar's OPEN time."* — the venue fact, recorded where the data entered the project |
| `src/folds/schedule.py`, `LAST_BAR_OFFSET_MS` | the last 15m bar of a day opens at **23:45**, which is an open time |
| `src/timeframe/resample.py` | each bucket is labelled `ts - ts % period_ms`, its **START** |
| `src/engine/contracts.py`, `TickSchedule.tick_at` | *"Tick in force at bar-open timestamp `ts`"* |

with the empirical confirmation that the 1h series runs from
**2022-01-01T00:00:00Z** to **2024-12-31T23:00:00Z** — a close-time series would
begin at 01:00 and end at 00:00 of the following day.

**So `bar_open_epoch_ms` is the value already carried in the `ts` column** of
every frame in this project, unmodified. No conversion is applied and none is
permitted: a rotation computed on a converted timestamp is a different rule.

### 2.4 EXACT NEUTRALITY — three rotations, not six permutations

**Cyclic rotation gives each symbol first priority on exactly one bar in three,
second priority on exactly one bar in three, and third priority on exactly one
bar in three.**

| rotation | 1st | 2nd | 3rd |
|---:|---|---|---|
| 0 | **BTCUSDT** | ETHUSDT | SOLUSDT |
| 1 | **ETHUSDT** | SOLUSDT | BTCUSDT |
| 2 | **SOLUSDT** | BTCUSDT | ETHUSDT |

Read down any column: each symbol appears exactly once. **THAT IS NEUTRALITY
ACROSS ALL THREE PRIORITY RANKS, NOT MERELY ACROSS FIRST PLACE**, and it is what
distinguishes the three cyclic rotations from an arbitrary subset of the six
permutations. A scheme that rotated first place while leaving second and third
fixed would be neutral in the headline and biased underneath it, and the bias
would fall on whichever symbol was permanently third — the position that matters
most, because it is the one that loses the last free slot.

**Over any three consecutive hourly bars the allocation order is a complete
Latin square over the three symbols.** Asserted by test over consecutive triples
and, separately, over a 3,000-bar synthetic span where each symbol must hold
first priority exactly **1,000** times.

**Because the modulus is 3 and the bar period is 1h, the rotation advances by
exactly one on every bar and the cycle closes every three hours.** It never
aligns with the 8-hour funding cycle in a way that could couple the tie-break to
settlement timing: 3 and 8 are coprime, so the joint cycle is 24 hours and every
rotation meets every settlement phase equally often. Recorded because the frozen
time exit is denominated in settlements (thesis §5.3), and a tie-break that
correlated with settlement phase would be a coupling nobody chose.

### 2.5 WHY ROTATION AND NOT THE ALTERNATIVES

**FIXED PRIORITY (BTC > ETH > SOL) — REJECTED.** Deterministic, stateless and
trivially implementable, and it **systematically starves the lower-priority
symbols of slots.** Whenever the budget is short of free slots on a contested
bar, SOLUSDT loses every time and ETHUSDT loses whenever BTC and ETH both fire.
**This acts directly on a pre-committed kill condition.** Thesis §7's condition
(b) — the two-of-three rule — requires that *"a symbol qualifies only if it
passes on its own AND at least one other symbol shows the same direction of edge,
defined as expectancy exceeding zero by at least 0.05R"*, and that requires each
symbol to carry an adequate population. **A rule that depletes two symbols of
three to feed the first is a rule that decides a confirmation test by
allocation.** Rejected on that ground alone.

**SKIP ALL TIED SIGNALS — REJECTED.** Perfectly neutral and perfectly wasteful.
It discards more than the budget requires: on a bar with three signals and two
free slots it takes none, **leaving capacity unused for no risk benefit
whatever.** The budget's purpose is to bound aggregate exposure, not to bound
it further on the specific bars where signals cluster. It would also interact
with §5.2's known bias in the same direction and make it worse, since ties are
most common exactly when signals cluster.

**RANDOM SELECTION — REJECTED, on two separate grounds.** It is **not
reproducible**: two runs of the same backtest over the same bars would produce
different traded populations, which destroys the determinism the golden-file and
pinned-trade regressions rest on. And **live it is arbitrary without being
neutral in any useful sense** — neutrality in expectation over an infinite run
is not neutrality over the finite window that will actually be traded, and a
seeded generator merely relocates the arbitrariness into the seed.

**ROTATION — ADOPTED.** Four properties, all required:

1. **DETERMINISTIC** — the same bars produce the same allocation, every run.
2. **EXACTLY NEUTRAL IN AGGREGATE** — §2.4, across all three ranks, not
   asymptotically but exactly, on every complete triple of bars.
3. **STATELESS** — the timestamp is the state. Nothing is carried between bars,
   nothing needs initialising, and no run-order dependence can creep in.
4. **DECIDABLE AT THE MOMENT OF ARRIVAL** — which is document 05 §5.1's
   requirement, and the reason arrival order was adopted there: *"live, the
   decision is made when the signal arrives, with no knowledge of later
   signals."* The rotation is a function of the bar the signal arrives on and of
   nothing else, so it is available at that instant.

**WHAT ROTATION DOES NOT CLAIM.** It does not make the tie-break costless. On any
individual contested bar some symbol is allocated last and may be skipped, and
over a finite window the symbols will not have been contested equally often —
neutrality is over bars, not over ties. **This is a fair rule, not a free one**,
and step 3 will report per-symbol skip counts rather than assuming the rotation
equalised them.

---

## 3. RULE B — THE BUDGET IS CHARGED THE NOMINAL ALLOCATION

### 3.1 THE RULE

> **THE BUDGET IS CHARGED THE NOMINAL ALLOCATION, BEING
> `RISK_PER_TRADE_USD = 20.00` BEFORE `qty_step` FLOORING, AND A CLOSING
> POSITION RETURNS THAT SAME NOMINAL FIGURE. REALISED RISK AFTER FLOORING DOES
> NOT ENTER BUDGET ACCOUNTING.**

**THE GAP THIS FILLS.** Document 05 §3 says a closing position *"returns exactly
its own allocation"* and §3.1 requires the quantity to be **floored** to the
symbol's `qty_step`. Today those two sentences do not conflict, because report
24 §2.2 records that **the engine performs no quantisation at all**. Once 5.3
implements flooring they would, and *"its own allocation"* would have two
readings with different consequences.

**WHY THE NOMINAL READING.** Flooring only ever reduces quantity, so realised
risk per trade sits slightly **below** $20.00 and varies per trade with the
price and the step. Charging realised risk would make the budget's remaining
balance a running sum of six different fractional shortfalls — **a quantity that
depends on prices, and therefore on the path.** Charging the nominal figure
keeps the budget's arithmetic in units of the risk unit itself, which is what
document 05 §3 means by *"the budget is denominated in the nominal risk unit,
which is fixed per trade by construction."*

### 3.2 CONSEQUENCE 1 — THE PARTIAL BRANCH STAYS INERT, BY CONSTRUCTION

**THIS IS THE REASON THE RULE EXISTS.**

Under realised-risk charging, six open positions would leave a remainder — the
sum of six flooring shortfalls, cents rather than dollars. `min($20, remaining)`
would then return **that remainder** rather than `$0`, a seventh signal would be
allocated it, and **the partial-allocation branch that document 05 §4 declares
INERT would become reachable.**

**IT WOULD BECOME REACHABLE SILENTLY.** Nothing raises. The seventh position
would simply be a few cents of nominal risk, would floor to a quantity of zero or
to a notional under the $5 minimum, and would be refused by §3.1's viability
test — so the *observable* behaviour would often be identical while the rule
being executed was a different one. **And it would be invisible to any test
written at these values**, because a viability refusal and a budget refusal look
the same from outside.

**This is the `MAKER_NONFILL_COST_R` hazard again**, which closing record §5.2
documents: a term in the wrong denomination, invisible to all 545 tests then in
the suite, **because every one of them multiplied it by zero.** Document 05 §4
already names the inert branch as exactly this class of hazard. Rule B is what
keeps it inert **by construction rather than by arithmetic coincidence**: with
nominal charging the remaining budget is always an exact multiple of $20.00,
`min($20, remaining)` is always exactly $20.00 or exactly $0.00, and §4's
description — **a hard cap of six concurrent full-size positions with
arrival-order skip** — remains the operative one.

### 3.3 CONSEQUENCE 2 — CHARGED EXPOSURE SLIGHTLY EXCEEDS TRUE EXPOSURE, AND THE ERROR IS CONSERVATIVE

**Flooring only reduces quantity, so realised risk is at or below nominal risk,
always.** The budget therefore charges slightly more than the book truly carries,
and **the error runs in the safe direction**: the account holds marginally less
risk than the budget believes, never more.

**THE MAGNITUDE, FROM A FROZEN MEASUREMENT.** Report 24 §2.2 measured the pooled
notional lost to flooring at

| symbol | pooled notional lost to flooring | worst single position |
|---|---:|---:|
| BTCUSDT | **0.21%** | 1.47% |
| ETHUSDT | **1.26%** | **9.21%** |
| SOLUSDT | **0.67%** | 7.00% |

**Those percentages transfer directly to risk.** Realised risk is
`quantity × stop distance` and notional is `quantity × entry price`; both are
linear in quantity, so flooring reduces the two by the *same* fraction. **A
notional measurement therefore bounds the risk overstatement exactly.**

**So the book-level overstatement is under 1.3% — well under 2% of the
budget — or under $1.60 of $120.00.** ETHUSDT is the binding symbol, consistent
with the closing record §6.1's finding that ETH is the granularity-binding
instrument.

**The worst SINGLE position is overstated by up to 9.21%**, and that figure is
recorded rather than averaged away. It changes nothing about the rule — the
budget charges $20.00 regardless — but a reader should not infer from the pooled
1.3% that no individual trade is far from nominal.

### 3.4 CONSEQUENCE 3 — 5.3 MUST WIRE THE BUDGET TO THE NOMINAL FIGURE

> **WIRING THE BUDGET TO REALISED RISK WOULD BE A SILENT RULE CHANGE, AND THIS
> PARAGRAPH IS WHAT MAKES IT A DETECTABLE ERROR RATHER THAN A DEFENSIBLE
> READING.**

`BUDGET_CHARGES = "nominal"` is committed as a constant in `src/risk/budget.py`
for exactly this reason: **the implementation must read the decision rather than
re-derive it**, and a reviewer of 5.3 can check one identifier instead of
reasoning about which of two plausible quantities was intended.

**The implementation must charge `RISK_PER_TRADE_USD` on open and credit
`RISK_PER_TRADE_USD` on close**, taking neither figure from the position's
realised size. Realised risk remains worth **recording per trade** — the closing
record §6.1 asks for a *"realised-vs-intended risk provenance counter"* so the
gap is visible rather than assumed away — but it is a reported quantity, **not a
budget input**, and the two must not be confused in the same code path.

---

## 4. DOCUMENT 05 IS UNMODIFIED, AND NOTHING IN IT IS SUPERSEDED

**`docs/design/05_aggregate_risk_budget.md` stands exactly as frozen at
`a323237`.** Every section, every number, every judgement.

**THIS AMENDMENT SUPERSEDES NOTHING.** It **adds** to two sections:

| section of document 05 | what this amendment adds |
|---|---|
| **§3, the allocation rule** | Rule A, defining the order within a bar, which §3 left undefined; and Rule B, defining which figure *"its own allocation"* names, which §3 left ambiguous once flooring exists. |
| **§4, the inert partial branch** | Rule B places §4's inertness on an explicit footing. §4's arithmetic — *"$120.00 is an exact multiple of $20.00"* — was always correct; Rule B is what guarantees the premise it rests on, that the amounts entering that arithmetic are the nominal ones. |

**No other section is touched, and in particular §2 is not.** Nothing here bears
on the derivation of the level, on the 30–50% tolerance, on the one-fifth
judgement, or on §9's honest assessment of the guard-rail principle as
borderline. **§5.1's requirement that the rule be decidable at the moment of
arrival is not weakened by Rule A — it is what selects rotation over the
alternatives** (§2.5), and §5.2's recorded arrival-order bias is unchanged in
both direction and magnitude, since rotation reorders within a bar and does not
change which bars are contested.

**Read together, the rule as amended is:** document 05 at `a323237`, with §3
extended by Rules A and B of this document.

---

## 5. THE CONSTANTS

Added to `src/risk/budget.py`. **Values only — no logic, no allocation function,
no data access.** A test parses them out of this document and requires equality
with the module, so a transcription drift fails rather than surviving.

```
TIE_BREAK_RULE     = "cyclic_rotation_by_bar_timestamp"
ROTATION_PERIOD_MS = 3600000
ROTATION_MODULUS   = 3
BUDGET_CHARGES     = "nominal"
SYMBOL_ROTATION    = (("BTCUSDT", "ETHUSDT", "SOLUSDT"),
                      ("ETHUSDT", "SOLUSDT", "BTCUSDT"),
                      ("SOLUSDT", "BTCUSDT", "ETHUSDT"))
```

**`SYMBOL_ROTATION` IS INDEXED BY THE ROTATION VALUE** — `SYMBOL_ROTATION[r]` is
the priority order for a bar whose rotation is `r` — and each entry is ordered
**highest priority first**.

**KNOWN-VALUE PINS, computed by hand and asserted by test:**

| bar (open, UTC) | epoch ms | `// 3_600_000` | `mod 3` | priority order |
|---|---:|---:|---:|---|
| **2022-01-01T00:00:00Z** — the first bar of the window | 1,640,995,200,000 | 455,832 | **0** | **BTCUSDT, ETHUSDT, SOLUSDT** |
| **2024-07-15T22:00:00Z** — report 24 §7.5's worst bar | 1,721,080,800,000 | 478,078 | **1** | **ETHUSDT, SOLUSDT, BTCUSDT** |

Two further pins are asserted for the window's own boundaries: the first
measured bar after warm-up, **2022-01-05T18:00:00Z**, is rotation **0**, and the
last bar of the window, **2024-12-31T23:00:00Z**, is rotation **2**.

**`ROTATION_PERIOD_MS = 3600000` IS THE BAR PERIOD, NOT A FREE PARAMETER.** It
is 1h because the timeframe is frozen at 1h by the rule at `96c96cf` and report
19. If the timeframe ever changed, this constant would change with it and the
rotation would still advance exactly once per bar.

---

## 6. PRE-REGISTRATION STATEMENT

**THIS AMENDMENT IS COMMITTED BEFORE ANY MEASUREMENT OF THE RULE'S COST
EXISTS.**

**NO SKIP-RATE, SURVIVING-COUNT OR CAPPED-CONCURRENCY FIGURE EXISTS ANYWHERE IN
THIS REPOSITORY AT THIS COMMIT.** Not for the budget as originally frozen, and
not for the budget as amended. Step 3 is the step that measures it and it has
not been run.

**Neither rule in this document was chosen with reference to its effect on
signal counts.** Rule A follows from §2.5's four required properties — the same
properties document 05 §5.1 already committed to — and Rule B follows from
keeping §4's inert branch inert. **Report 24's occupancy tables were not
consulted for either.** The report 24 figures that do appear here are §1.1's bar
timestamp convention (§2.3), §2.2's flooring percentages (§3.3), §7.5's worst-bar
timestamp used as an arithmetic pin (§5), and §7.1/§7.6's existence as two
scopes (§2.2) — **none of which is a count of anything either rule would skip.**

**THE STATE OF THE REPOSITORY AT THE TIME OF WRITING** is document 05 frozen at
**`a323237`**, report 25 at `e735295`, report 24 at `4e08e1b`, the thesis at
`02e47a5` and thesis amendment 1 at `703046a`.

**WHAT WOULD FALSIFY THE CLAIM THAT THIS IS A PRE-REGISTRATION.** A commit
between `a323237` and this one containing a skip-rate, surviving-count or capped
concurrency figure. **There is none, and `git log` is the check.**

### 6.1 THIS AMENDMENT MAY NOT BE EDITED IN LIGHT OF STEP 3'S RESULT

**On the same terms document 05 §11 sets for itself.**

**A further correction is Amendment 2, with its own commit and its own statement
of what changed and why. A silent edit is a contamination event.**

**If step 3 shows the tie-break costs more than expected — that one symbol is
skipped more often than another, or that contested bars are more common than
anticipated — that is a finding about the strategy at this capital, and it is
NOT grounds for changing the rotation.** Changing it afterwards would be
selecting a tie-break to fit a per-symbol population, which is precisely the
failure the two-of-three condition in thesis §7(b) exists to prevent, and
§2.5's rejection of fixed priority is the argument against doing it deliberately.

**THE PERFORMANCE FIREWALL IS ARMED.** No expectancy, win rate, profit factor,
Sharpe, Sortino, equity curve, drawdown, `r_multiple`, `net_pnl` or `gross_pnl`
quantity is computed, inspected, estimated or referenced in this document or in
the module it extends, and an AST guard over the module refuses all twelve
names.

**THE HOLDOUT REMAINS SEALED AND UNSPENT.** 2025-01-01 through 2026-07-26 has
never been read by any code path in this project, and no code path was executed
to write this document.

**NOTHING IS WIRED IN.** No engine file imports `src/risk`, asserted by walking
every module under `src/`. That remains 5.3's work.

---

**Committed with the module change and the tests, and nothing else. Document 05
stands unaltered at `a323237`; its SHA-256 is asserted by test. The level is
unchanged at $120.00.**
