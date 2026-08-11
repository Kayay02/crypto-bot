# AMENDMENT 2 TO THE AGGREGATE OPEN RISK BUDGET

## 1. HEADER — WHAT CHANGED

**This is Amendment 2 to `docs/design/05_aggregate_risk_budget.md`, frozen at
commit `a323237`, as already amended by
`docs/design/05a_aggregate_risk_budget_amendment_1.md`, frozen at commit
`62c2d2b`.**

**NEITHER FROZEN DOCUMENT IS ALTERED.** Not one character of either. Document 05
§11 specifies the procedure — *"an amendment is a new document with a new commit
and an explicit statement of what changed and why; a silent edit is a
contamination event"* — and Amendment 1 §6.1 restates it for itself. **Both
SHA-256 values are asserted by test** (§3), so an edit to either fails the suite
rather than passing unnoticed.

**WHAT CHANGED, IN ONE BLOCK.** One specification gap, found in review. **It is
a gap, not a correction**: nothing in either document is wrong.

| | gap | resolution |
|---|---|---|
| **C** | Document 05 §3 allocates in **arrival order**; Amendment 1 **Rule A** orders simultaneous SIGNALS against each other. **Neither orders a signal against an EXIT occurring at the same instant.** Report 24 §5.3's convention makes that instant real and common: a position closes at the close of bar `X`, and a signal on bar `X` also enters at the close of bar `X`. At that one instant a position releases its allocation and another signal wants it. | **RULE C**, §2: **exits are processed before entries.** |

> ### THE LEVEL DID NOT CHANGE.
>
> **`MAX_AGGREGATE_OPEN_RISK_USD` REMAINS `120.00`.** `RISK_PER_TRADE_USD`
> remains `20.00`, `ACCOUNT_CAPITAL_USD` remains `2000.00`,
> `BUDGET_FRACTION_OF_CAPITAL` remains `0.06`, `FULL_SIZE_POSITIONS` remains
> `6`, `MARGIN_MODE` remains `"cross"`, `POSITION_MODE` remains `"hedge"`,
> `TIE_BREAK_RULE` remains `"cyclic_rotation_by_bar_timestamp"` and
> `BUDGET_CHARGES` remains `"nominal"`.
>
> **DOCUMENT 05 §2's DERIVATION IS UNTOUCHED AND IS NOT REVISITED.** The 30–50%
> tolerance, the one-fifth judgement, the choice of the conservative end, and
> the disclosure that the tolerance is **not recorded in any committed
> artifact** all stand exactly as frozen. **This amendment specifies mechanism,
> not appetite.** Nothing below could be used to argue for a different level,
> and no measurement of the level's cost exists at this commit (§5).

**SCOPE.** This amendment adds to document 05 **§3** and composes with
Amendment 1 **Rule A**. It supersedes nothing. **NO MEASUREMENT WAS RUN TO WRITE
IT** — no market data, no parquet, no bars, no folds, no counts, no occupancy.

---

## 2. RULE C — EXITS BEFORE ENTRIES

### 2.1 THE RULE

> **WITHIN A SINGLE BAR CLOSE, THE PROCESSING ORDER IS:**
>
> **1. ALL POSITIONS WHOSE EXIT FALLS AT THIS BAR'S CLOSE ARE CLOSED**, and each
> returns `RISK_PER_TRADE_USD` to the budget.
>
> **2. ONLY THEN ARE THAT BAR'S SIGNALS EVALUATED** against the remaining
> budget, in the priority order Amendment 1 Rule A gives for that bar.

**ACROSS BARS NOTHING CHANGES.** An earlier bar is fully processed — its exits
and then its entries — before a later bar begins. Document 05 §3's arrival-order
rule is intact and Amendment 1's statement that *"an earlier bar's signals are
always allocated before a later bar's"* is unaffected.

**WHY, AND IT IS THE SAME GROUND AS BEFORE.** Document 05 §5.1 selected arrival
order because *"live, the decision is made when the signal arrives, with no
knowledge of later signals"* — operational faithfulness, not convenience. **The
same ground selects this.** Live, at the 1h close, the time-exit market order
fills and releases its margin and its budget **before** the new entry order is
evaluated and placed; the two are not simultaneous in the account, they are
sequential in the account, and this order is the sequence that occurs.

### 2.2 THE CONSEQUENCE THAT LOOKS LIKE A BUG AND IS NOT

> **UNDER THIS RULE THE SAME $20.00 OF BUDGET CAN FUND A CLOSING POSITION AND AN
> OPENING POSITION AT THE SAME BAR CLOSE. THIS IS CORRECT. IT IS NOT DOUBLE
> COUNTING.**

**THE REASON IS REPORT 24 §5.3's HALF-OPEN CONVENTION**, which is frozen:

> *"A position opened at the close of bar `T` and closed at the close of bar `X`
> is open on bars `T+1` … `X` inclusive — the half-open instant interval
> `(close of T, close of X]`."*

So for a position closing at the close of bar `X` and a position opening at the
close of bar `X`:

| position | last / first bar open | 
|---|---|
| the one **closing** at the close of `X` | its **last** open bar is **`X`** |
| the one **opening** at the close of `X` | its **first** open bar is **`X+1`** |

**THEY DO NOT OVERLAP ON ANY BAR.** There is no instant at which both are open,
so there is no instant at which the budget carries both. The $20.00 is held by
one, then by the other, and never by two at once. **On every bar of the
occupancy timeline the sum of open allocations is at or below $120.00** — which
is what the budget constrains, and the only thing it constrains.

**THIS IS WRITTEN OUT AT LENGTH BECAUSE THE FAILURE MODE IS AN IMPLEMENTER
"FIXING" IT.** Someone reading the same $20 funding two positions at one
timestamp will reasonably suspect double counting, and the natural repair —
evaluate entries before exits — **silently reverts this rule** while looking
like a bug fix and leaving every aggregate still plausible. **A test pins the
behaviour so that the reversal fails**: a synthetic book at the cap, with one
exit and one signal at the same bar close, is asserted to TAKE the signal, and
the entries-first ordering is asserted to produce the opposite answer on the
same input. **The two orderings are therefore distinguishable by test, not only
by prose.**

### 2.3 WHY NOT ENTRIES BEFORE EXITS

**IT MODELS A SEQUENCE THAT CANNOT OCCUR LIVE.** There is no account in which a
new entry is evaluated against a budget still encumbered by a position that has
already closed at that same instant. The encumbrance would be an artefact of the
backtester's loop, not a property of the account.

**AND IT IS STRICTLY MORE RESTRICTIVE, NOT MERELY DIFFERENT.** Every signal that
entries-first admits, exits-first also admits — the budget available under
exits-first is greater or equal at every evaluation, since exits only ever add
to it. **The two orderings are ordered, not merely distinct:**

> **ENTRIES-FIRST WOULD SKIP SIGNALS THE LIVE ACCOUNT WOULD HAVE TAKEN, AND
> WOULD BIAS THE MEASURED SKIP RATE UPWARD FOR A REASON THAT IS AN ARTEFACT OF
> PROCESSING ORDER.**

**THAT IS WHY THE CHOICE CANNOT BE DEFERRED TO THE IMPLEMENTATION.** A neutral
choice could be left to whoever writes 5.3; a choice that moves a headline
metric in a known direction cannot. Document 05 §7 commits to reporting the skip
tail *"as an explicit metric rather than suppressed"*, and a skip rate inflated
by loop order would be reporting the backtester rather than the strategy.

### 2.4 INTERACTION WITH RULE A — the two compose without ambiguity

**WHEN EXITS FREE FEWER SLOTS THAN THERE ARE CONTENDING SIGNALS ON THAT BAR,
AMENDMENT 1 RULE A's ROTATION DECIDES WHICH SIGNALS TAKE THEM.**

> **RULE C SETS HOW MUCH BUDGET EXISTS AT THE MOMENT OF EVALUATION.
> RULE A SETS WHO GETS IT.**

They act on different questions and in a fixed sequence, so there is no ordering
between the rules to specify and no case in which both must be consulted about
the same decision. Worked through:

1. Bar `X` closes.
2. **Rule C**: every position whose exit falls here closes; the budget rises by
   `RISK_PER_TRADE_USD` per closure. The remaining budget is now fixed for this
   bar.
3. **Rule A**: bar `X`'s signals are ordered by
   `(bar_open_epoch_ms // 3_600_000) mod 3`.
4. Document 05 §3: each signal in that order takes `min(RISK_PER_TRADE_USD,
   remaining)`, subject to §3.1's viability test. With Amendment 1 Rule B's
   nominal charging the allocation is always exactly `$20.00` or exactly `$0.00`.

**Rule A's neutrality is unaffected by Rule C.** The rotation is a function of
the bar's timestamp alone; how many slots exist on that bar does not enter it,
so each symbol still holds each priority rank on exactly one bar in three.

---

## 3. DOCUMENTS 05 AND 05a ARE UNMODIFIED, AND NOTHING IS SUPERSEDED

**Both stand exactly as frozen.**

| document | commit | SHA-256 |
|---|---|---|
| `docs/design/05_aggregate_risk_budget.md` | **`a323237`** | `d5ac7bd61323d04e75a854baf14086932470175408f5e2db4ca6f4d3afad268f` |
| `docs/design/05a_aggregate_risk_budget_amendment_1.md` | **`62c2d2b`** | `50da5aed3fabb86c3c7b54b41642444e50c7a7790de8dc93ab401ab53071522c` |

**Both values are asserted by test, and both tests must fail if either file ever
differs.**

**THIS AMENDMENT SUPERSEDES NOTHING.** It **adds** to document 05 §3 and
**composes** with Amendment 1 Rule A (§2.4). In particular it does not touch
document 05 §2's derivation, §4's inert partial branch — Rule C moves budget in
whole units of `RISK_PER_TRADE_USD`, so the multiple-of-$20 property Amendment 1
Rule B guarantees is preserved exactly — §5.2's recorded arrival-order bias, or
§9's assessment of the guard-rail principle as borderline.

**Read together, the rule as amended is:** document 05 at `a323237`, with §3
extended by Amendment 1's Rules A and B and by Rule C of this document.

---

## 4. THE ORDERING SURFACE, NOW WALKED DELIBERATELY

**THIS IS THE THIRD SPECIFICATION GAP FOUND IN THIS RULE.** Amendment 1 closed
two — the intra-bar tie-break between signals, and nominal versus realised
charging — and this closes a third. **Three gaps found reactively, one at a
time, is a pattern and not a coincidence**, and continuing to find them one at a
time would be the failure rather than the process.

**SO THE ORDERING SURFACE HAS NOW BEEN ENUMERATED DELIBERATELY**, rather than
waited upon. Every case in which two budget events could contend at one instant:

**4.1 EXITS AMONG THEMSELVES — NO CONTENTION, AND THIS IS PROVABLE.** Every exit
*releases* budget and none consumes it, so the remaining budget after processing
a set of exits is the same whatever order they are processed in. **There is
nothing to specify**, and the absence of a rule here is a conclusion rather than
an omission.

**4.2 SAME-SYMBOL SAME-BAR ENTRY AND EXIT — COVERED BY RULE C UNCHANGED.** Under
report 25 §5.1's netting finding these are two distinct *strategy* positions
sitting on one netted *venue* position. **Budget accounting is at the strategy
level** — that is what document 05 §3 means by an allocation being returned by
"a closing position" — so Rule C applies with no special case. **The venue-side
consequence is an execution concern for 5.3, not a budget one**: at the exchange
the pair is a partial close and a partial open of one netted position, and if
they are same-direction the two orders may net down or cancel entirely. That
changes what is *sent*, not what is *charged*.

**4.3 TWO SIGNALS ON ONE SYMBOL IN ONE BAR — IMPOSSIBLE BY CONSTRUCTION.**
Thesis §4.1 skips two-sided bars: a bar that fires both the long and the short
trigger on a symbol opens nothing. So a bar yields **at most one signal per
symbol**, the tied set is a subset of the three symbols, and Amendment 1 Rule A
is a total order on it. **No sub-tie exists to break.**

**4.4 WINDOW-EDGE TRUNCATION — POSITIONS HOLD BUDGET TO THE BOUNDARY.** Report
24 §5.3 records **10 positions** (2 BTC, 4 ETH, 4 SOL) whose calendar exits fall
past the end of the measured window and whose occupancy is clipped there. **Those
positions hold their allocation to the boundary and never release it inside the
window.** That is the correct treatment: the exit is a calendar fact outside the
measured period, and releasing the budget at the boundary would credit the book
with capacity it did not have. The last bars of a scope may therefore carry a
permanently reduced budget, **and that is a property of measuring a finite
window, not a defect to be repaired.**

### 4.5 IF A FOURTH ORDERING GAP EMERGES

> **IF A FURTHER ORDERING GAP EMERGES DURING 5.3, THE CORRECT CONCLUSION IS THAT
> THIS PRE-REGISTRATION WAS WRITTEN AT THE WRONG GRANULARITY — NOT THAT A FOURTH
> AMENDMENT SHOULD BE WRITTEN.**

**A rule that needs an amendment per implementation detail is a rule specified
above the level at which it operates.** The response would then be to re-write
the specification at the granularity of the event loop — a full statement of what
happens at a bar close, in order, once — as a **new pre-registration with its own
commit**, superseding this chain in one piece, rather than to accumulate a fourth
patch onto a document whose §3 is by then four documents long.

**This is recorded now, before the fourth gap, so that the decision is a
pre-commitment rather than a judgement made under the pressure of wanting to get
on with 5.3.** The amendment procedure exists to prevent silent edits; it is not
a licence to specify by accretion, and this paragraph is where that limit is
placed.

---

## 5. PRE-REGISTRATION STATEMENT

**THIS AMENDMENT IS COMMITTED BEFORE ANY MEASUREMENT OF THE RULE'S COST
EXISTS.**

**NO SKIP-RATE, SURVIVING-COUNT OR CAPPED-CONCURRENCY FIGURE EXISTS ANYWHERE IN
THIS REPOSITORY AT THIS COMMIT.** Not for the budget as originally frozen, not
as amended by Amendment 1, and not as amended here. Step 3 is the step that
measures it and it has not been run.

**RULE C WAS NOT CHOSEN WITH REFERENCE TO ITS EFFECT ON SIGNAL COUNTS.** It
follows from document 05 §5.1's operational-faithfulness ground — the same ground
that selected arrival order before any count existed — and from report 24 §5.3's
frozen occupancy convention. **Report 24's occupancy tables were not consulted.**
The report 24 figures appearing here are §5.3's convention (§2.2) and §5.3's
count of 10 window-clipped positions (§4.4), **neither of which is a count of
anything this rule would skip.**

**IT IS ACKNOWLEDGED THAT RULE C IS THE LESS RESTRICTIVE OF THE TWO ORDERINGS**
(§2.3) and therefore that it will produce a lower skip rate than the
alternative. **That is not why it was chosen** — it was chosen because it is the
sequence that occurs live — and the direction is stated here, in advance,
precisely so that it cannot later be presented as a discovery.

**THE STATE OF THE REPOSITORY AT THE TIME OF WRITING** is document 05 at
`a323237`, Amendment 1 at `62c2d2b`, report 25 at `e735295`, report 24 at
`4e08e1b`, the thesis at `02e47a5` and thesis amendment 1 at `703046a`.

**WHAT WOULD FALSIFY THE CLAIM THAT THIS IS A PRE-REGISTRATION.** A commit
between `62c2d2b` and this one containing a skip-rate, surviving-count or capped
concurrency figure. **There is none, and `git log` is the check.**

---

## 6. THIS AMENDMENT MAY NOT BE EDITED IN LIGHT OF STEP 3'S RESULT

**On the same terms document 05 §11 sets for itself and Amendment 1 §6.1 repeats.**

**A further correction is Amendment 3 — subject to §4.5, which says that a fourth
ordering gap calls for a re-specification rather than a third patch — with its
own commit and its own statement of what changed and why. A silent edit is a
contamination event.**

**If step 3 shows the skip rate is uncomfortable, that is a finding about the
strategy at this capital** (document 05 §7) **and it is NOT grounds for changing
Rule C.** Reverting to entries-first to move a skip rate would be selecting a
loop order to fit a metric, and §2.3 is the argument against doing it
deliberately.

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

## 7. THE CONSTANT

Added to `src/risk/budget.py`. **Value only — no logic.** A test parses it out of
this document and requires equality with the module.

```
INTRA_BAR_ORDER = "exits_before_entries"
```

---

**Committed with the module change and the tests, and nothing else. Documents 05
and 05a stand unaltered at `a323237` and `62c2d2b`; both SHA-256 values are
asserted by test. The level is unchanged at $120.00.**
