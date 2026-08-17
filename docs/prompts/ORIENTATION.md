# ORIENTATION — THE WHOLE PROJECT, FOR A READER WHO HAS NONE OF IT

## 0. WHAT THIS FILE IS

**A SUMMARY WRITTEN FOR A PARTICIPANT WHO DOES NOT HAVE THE REPOSITORY IN
CONTEXT.** It gathers what has happened, what is frozen, what is open, and what
the arguing rules are, so that a second reader can engage with the substance
instead of reconstructing the state.

> ### THIS FILE CREATES NO RULE, DECIDES NOTHING, AND HAS NO AUTHORITY.

**WHERE THIS FILE AND A SOURCE DOCUMENT DIFFER, THE SOURCE GOVERNS**, and the
difference is a defect in this file. It is the same construction
`docs/prompts/STANDING_RULES.md` §0 uses for itself, on the same grounds.

**IT IS A SUMMARY, WHICH MEANS IT IS LOSSY BY CONSTRUCTION.** Every section below
names the documents it is summarising. **A step that turns on a rule's exact
wording must read the source**, because this file has compressed arguments that
were written at length precisely because they are not compressible.

**IT IS NOT A WORK ORDER.** `docs/README.md` states the distinction that matters
here: a document recording what was decided reads like a specification and is not
one. **Nothing below instructs anybody to build anything.**

### 0.1 THE PERMITTED BANNED-TOKEN OCCURRENCES

**THIS FILE CONTAINS THE FIREWALL'S BANNED TOKENS**, which is unavoidable in a
file whose purpose includes keeping a new reader from tripping the firewall.
`docs/design/04_1d_standing_practices.md` §0.1 took the narrower route of naming
its sources without reproducing either; **this file takes the wider one and says
so.** The canonical list is `src/firewall.py`, from which membership should be
taken.

**THEY OCCUR IN SIX PLACES, EACH SEPARATELY REQUIRED BY WHAT THIS FILE MUST
CARRY:**

- **§4**, stating the figure that killed the FIRST Point 4 hypothesis, which is
  the substance of that verdict;
- **§5.5**, quoting kill conditions (a), (b), (c) and (f) in the frozen thesis's
  own words;
- **§6.1 and §12.2**, transcribing the standing brief's peak-to-trough
  loss-tolerance premise, from which the aggregate budget is derived;
- **§7.1**, quoting `docs/handoff/31_point_5_closing.md` §11's prose statement of
  what the firewall forbids;
- **§7.2**, listing the enforced twelve-name set and the three names the retired
  nine-name variant omitted, without which the divergence is not statable;
- **§8.1**, stating the premise the tolerance's original justification rested on.

> **A CHECK FINDING THOSE TOKENS IN THOSE SIX PLACES HAS FOUND THE LIST, THE
> QUOTED RULES AND THE PREMISES — NOT A VIOLATION. NO OTHER OCCURRENCE IN THIS
> FILE IS PERMITTED.**

**AND THE DISTINCTION THAT MAKES THIS ADMISSIBLE AT ALL: the firewall forbids such
a figure EXISTING FOR THIS THESIS.** §4's figure belongs to **the killed
momentum/breakout hypothesis**, is already published in committed reports, and is
not a quantity for the thesis at §5. **Every other occurrence above is a name, a
frozen rule's own wording, or a premise — none is a figure.**

---

## 1. THE PROJECT IN ONE PARAGRAPH

**A single-operator crypto trading bot on Bitget USDT-M perpetual futures —
BTCUSDT, ETHUSDT, SOLUSDT — at approximately $2,000 of capital with $20 of risk
per trade enforced after fees and estimated slippage, on 1h bars.** The strategy
under test is a **liquidity-sweep reversal**: a bar that reaches beyond a recent
Donchian extreme and closes back inside it is traded against the sweep. **The
project has built a complete backtesting and execution apparatus and has
deliberately not run it.** No outcome figure exists. The current and only blocking
work is the **validation design**, which must be written and committed before the
first result is permitted to exist.

**THE PROJECT'S DISTINGUISHING FEATURE IS NOT THE STRATEGY. IT IS THE
EPISTEMIC DISCIPLINE.** Roughly two thirds of the committed artifacts exist to
make it impossible to choose a parameter, a criterion or a justification after
seeing what it would produce. **A reader who engages with the strategy and
ignores the discipline will be arguing about the less important half.**

---

## 2. THE TWO HOLDOUT DISCLOSURES, CARRIED IN FULL

**THIS SECTION IS MANDATORY AND IS NOT A FORMALITY.**
`docs/design/04_0_divergence_disposition_amendment_1.md` §3, as extended by
`docs/design/04_0_divergence_disposition_amendment_2.md` §3, defines a writeup as
**any communication, in any medium, that states, characterises, or declines to
state a result computed on the holdout window, and any communication asserting
that no such result exists, that the holdout has not been opened, or that the seal
is intact.** This file asserts exactly that, in §7 and §11. **The obligation
therefore attaches, both disclosures are carried here in full rather than by
reference, and a communication too short to carry them is to be made longer rather
than abbreviated.**

### 2.1 THE FIRST DISCLOSURE — THE SUB-POINT 5.3.3 BREACH

**Source: `docs/handoff/31_point_5_closing.md` §6, whose primary account is
`docs/handoff/29_point_5_3_3_1m_seal.md` §9.**

**WHAT WAS OPENED.** Six sealed 1m partitions — `year=2025` and `year=2026`, all
three symbols — were **opened and decoded** during sub-point 5.3.3's mutation
battery. The battery ran against the real data directory behind a filesystem
barrier (`chmod 000` on the six files) which was **verified as armed at the start
and silently reverted to `0400` mid-run**; the process owns the files. Confirmed
under mutation M3b: a loader call opened both partitions for SOLUSDT, decoded the
timestamp, high, low and close columns, and returned a filtered frame.
**Near-certain under M2 and M3a, and deliberately not re-tested, because
re-testing would repeat the read.** Mutations M1, M4a, M4b and M5 cannot reach a
sealed path by construction and were unaffected.

**THAT NO SEALED VALUE REACHED ANYONE.** No sealed value was printed, aggregated,
stored, or used in any computation, and none reached a human, a document or an
artifact. The bytes were decoded into a transient process and discarded when it
exited. A persistent-disk check afterwards found nothing — no sealed value in the
pytest cache, in any log, or in captured output.

**THE ADJUDICATION AND ITS REASONING.** **The holdout remains valid.** An
out-of-sample test's validity rests on the data not having influenced the design
of what it tests. No sealed value reached anyone, so no design decision could have
been conditioned on one. Every Point 5 decision is committed with a hash predating
the breach — documents 05 (`a323237`), 05a (`62c2d2b`), 05b (`46099a2`), 06
(`6def4cb`) and 06a (`0f79311`) all precede `7f46b1a` — and the chain is verifiable
from `git log` independently of anyone's account of what happened. That
independence is the point: the adjudication does not rest on trusting the report.
The alternative was considered and rejected on its costs: declaring the window
burned would cost the entire out-of-sample test, with no second window available,
in exchange for no epistemic gain, since the contamination mechanism an
out-of-sample test guards against is design influence and there was none. **This
is an adjudication, not an exoneration.** The window's value rested on never
having been opened, and six of its files were opened by code written for this
project, in runs chosen by it.

### 2.2 THE SECOND DISCLOSURE — THE MANIFEST ROW-COUNT CHANNEL

**Source: `docs/design/04_0_divergence_disposition.md` §7**, which added it
because §6.4 above did not cover it.

- **WHAT WAS ACCESSED: ROW COUNTS ONLY.** `structural_pass.check_manifest` and
  `tests/test_manifest_integrity.py` called `pq.read_metadata` on all 26 manifest
  outputs, six of which are sealed 1m partitions, and accessed `.num_rows`. **Not
  the parquet footer's per-column minimum and maximum statistics, which would
  carry price information.**
- **ROW COUNTS OF A COMPLETE MINUTE LAYER ARE CALENDAR ARITHMETIC AND CARRY NO
  PRICE INFORMATION.**
- **THE COUNTS ARE RECORDED IN `data/derived/_manifest.json`.**
- **THE CHANNEL WAS CLOSED AT SUB-POINT 5.3.3.**

**THE ASYMMETRY THAT MOTIVATED THE EXTENSION, IN THE SOURCE'S OWN TERMS:** the
5.3.3 breach left nothing persistent on disk, while this channel left an artifact
on disk and ran on every test invocation over a longer period — **and the channel
that persisted was the one not attached to the permanent disclosure requirement.**
The principle: a reader of a holdout result is entitled to assess the seal, and
that entitlement does not permit the project to pre-select which touches of the
sealed files the reader is told about.

### 2.3 THE SEAL AND THE BUDGET

**THE HOLDOUT IS 2025-01-01 THROUGH 2026-07-26 AND REMAINS SEALED AND UNSPENT.**
The `year=2025` and `year=2026` partitions are the sealed ones; six sealed files
exist on disk and **the seal is not maintained by the absence of the data.**

> **HOLDOUT BUDGET: ONE CANDIDATE, ONE LOOK, WHOLE WINDOW, NO CANDIDATE TWO.**

It is evaluated exactly once, on a single candidate selected entirely without
reference to it, over the whole window. There is no second candidate, no second
look, and no partial evaluation. If the candidate fails, the holdout is spent and
the answer is the answer.

---

## 3. HOW THE REPOSITORY IS ORGANISED, AND WHICH DOCUMENT WINS

### 3.1 THE THREE DIRECTORIES AND THEIR DIFFERENT AUTHORITY

**Source: `docs/README.md`.**

- **`docs/design/`** — pre-registrations. **A document committed here as a
  pre-registration joins the FROZEN SPECIFICATION on its commit and binds.**
- **`docs/handoff/`** — the decision and measurement record carried between chat
  sessions. **EVIDENCE, NOT SPECIFICATION.** Cited, relied on, corrected by
  erratum; does not bind.
- **`docs/prompts/`** — the literal specs sent to the build sessions, kept
  verbatim including anything later found wrong. Also holds
  `STANDING_RULES.md`, `MANIFEST.md` and this file.
- **`reports/`** — what came back from build sessions, plus raw diagnostics and
  figures from the early data layer.

**THE FILING RULE THAT KEEPS BITING:** design documents join the specification on
commit and **a measurement does not**, so a derivation is filed under
`docs/handoff/` even when it reads like a rule. Filing a measurement under
`docs/design/` would enrol it in the specification.
`docs/handoff/36_point_4_1c_risk_unit_derivation.md`'s preamble states the ground.

**SOURCE CODE UNDER `src/` IS AN IMPLEMENTATION OF THE SPECIFICATION AND IS NOT A
MEMBER OF IT.**

### 3.2 THE AUTHORITY LADDER, HIGHEST FIRST

1. **The git history.** `docs/prompts/MANIFEST.md` §0 says so explicitly: the
   manifest is a convenience index and **the git history is authoritative where
   they disagree.** A hash that does not match the file is a defect in the index,
   not evidence about the file. **Recompute rather than trust.**
2. **The frozen specification** — the documents at §6 below.
3. **The evidence reports** under `docs/handoff/`.
4. **The code**, which implements but does not define.
5. **`docs/prompts/STANDING_RULES.md`, `MANIFEST.md` and this file**, none of
   which bind on their own authority.

### 3.3 THE ARTIFACT INDEX

`docs/prompts/MANIFEST.md` carries one entry per artifact — path, SHA-256,
introducing commit, and one line on what it governs. **At its last revision: 22
frozen specification entries, 16 evidence reports, 10 implementation modules, 4
unhashed engine dependencies, 48 total hashed entries, and zero hash mismatches
against values recorded in committed documents.** Its §0.1 records the cross-check
that produced that: every 64-character hexadecimal string appearing alongside a
file path anywhere under `docs/` was extracted and compared against the file's
current hash — **29 pairs found, 29 matching, none absent.**

---

## 4. THE HISTORY, IN ORDER

**The project numbers its work as "Points". The numbering is not chronological,
because points were reopened.** The actual order of events:

**POINT 1 (original) and POINT 2.** Strategy premises and the data layer. Point 2
delivered acquisition, validation and a derived layer over Bitget and a Binance
cross-reference, with the git commit hash recorded in the derived manifest.

**POINT 3 and POINT 3R.** The backtesting engine — signals, simulation, costs,
contracts — then an amendment pass: session RVOL, a derived stop floor, a derived
time stop, and RSI removed.

**POINT 4 (first attempt) — A MOMENTUM/TREND-CONTINUATION BREAKOUT STRATEGY ON
15m. VALIDATED AND KILLED.** `docs/handoff/16_point_4_closing.md` is the record.
It ran a regime characterisation, a nine-fold walk-forward architecture, a 7,128
cell parameter sweep, a band selection and a kill-condition verdict.

> **WHAT KILLED IT: the pre-committed two-of-three rule. One symbol of three
> showed the required direction of edge; a rule requiring two cannot be satisfied
> by one. The procedure terminated before the holdout, by its own pre-registered
> logic.**

**The number that settles it: 160 of 198 eligible grid points had NEGATIVE
TRAINING expectancy** — ETHUSDT was zero of 70 — so the strategy lost money on the
folds its own parameters were chosen on. **That is failure to fit, not failure to
generalise**, and it is the cleaner result. Three mechanism findings came out of
it and shape everything after: the bar-21 time-stop **created** the holding-time
mode rather than catching one and removing it improved the result; the RVOL gate
did **volatility selection, not edge detection**; and the kill conditions carried
no aggregation rule over one axis, so a verdict was nearly decided by accident.

**POINT 1 (REOPENED) — THE CURRENT THESIS.** A new hypothesis, deliberately the
**opposite claim** to the dead one rather than a repair of it. §5 below.

**POINT 5 — RISK AND POSITION SIZING. CLOSED.**
`docs/handoff/31_point_5_closing.md`. Two frozen pre-registrations with three
amendments, seven measurement reports, an exchange-real sizing layer, a sealed 1m
loader, and a portfolio execution path carrying all three frozen rule-sets in one
place. **It produced a rule, an engine and no result, which is what it was opened
to do.**

**POINT 4 (REOPENED) — THE VALIDATION DESIGN. OPEN, AND BLOCKING EVERYTHING.**
This is where the project sits now. §8 below.

**POINT 6 — PAPER TRADING.** Not started. Carries a queue of four obligations,
§10.2.

---

## 5. THE STRATEGY UNDER TEST

**Source: `docs/handoff/22_point_1_thesis.md`, frozen at `02e47a5`, as amended by
`docs/handoff/22a_point_1_thesis_amendment_1.md` at `703046a`.**

### 5.1 THE CLAIM

Stop-loss orders cluster just beyond recent visible extremes, because that is
where they can be reasoned about. When price reaches the cluster the stops
trigger, each triggered stop is a market order in the direction of the move, and
the result is a **self-reinforcing cascade**. **At the moment of the break, a
cascade is indistinguishable from a genuine breakout.** They separate **at the bar
close**: a genuine breakout is sustained by continuing demand and tends to close
beyond the level, while a cascade is sustained only by the stops it consumes and
returns inside the level within the bar.

> **THE CLAIM: a bar that reaches beyond a recent extreme and closes back inside
> it is more likely to be followed by movement AWAY from that extreme than by
> continuation through it.**

**FOUR ARGUMENTS FOR WHY AN EDGE SHOULD EXIST, recorded as arguments and not
findings:** the absorbing counterparty is structurally identifiable and positioned
against the sweep; the order flow that caused the move is spent, because
stopped-out traders are flat; **the edge should survive being known, because stops
are not discretionary** — they are placed for risk management, not prediction, and
the alternative is worse for the trader placing them; and it is the opposite claim
to the dead hypothesis rather than a patch of it.

**PRE-REGISTERED FAILURE EXPECTATION.** The edge, if it exists, should
**concentrate in ranging and mean-reverting conditions and be weak or absent in
trending ones**, because trending regimes pollute the reversal population with
genuine breakouts. **Uniformity across regimes is to be treated as MORE suspicious
than concentration**, and that paragraph exists so uniformity cannot later be
reinterpreted as confirmation.

### 5.2 THE FROZEN PARAMETERS

- **Instruments:** Bitget USDT-M perpetual futures, BTCUSDT, ETHUSDT, SOLUSDT.
- **Timeframe:** **1h**, selected by a rule frozen before the selection at
  `96c96cf` and applied in report 19.
- **Indicators: two, and only two.** **Donchian-10**, excluding the current bar,
  used as a **structural marker and not a trend signal** — it locates where stops
  would have been placed. **ATR(14) Wilder**, used only for distance.
- **Long signal at bar T:** `low[T] < lower[T]` and `close[T] > lower[T]`, where
  `lower[T] = min(low[T-10] .. low[T-1])`. **Short is the exact mirror.** All four
  comparisons **strict**.
- **Two-sided bars are skipped**, chosen for determinism over any side-selection
  rule. Measured cost: 86 BTCUSDT, 59 ETHUSDT, 32 SOLUSDT across all nine training
  periods, at most 19 in a single fold.
- **Entry: the close of the signal bar, as a TAKER. Frozen**, because the entire
  excursion geometry in report 21 is conditional on that reference and changing it
  silently invalidates a committed result.
- **Stop: `max(2.25 x ATR(14), floor)`.** The floor was **1.50%** and **that
  number is now retired** — see §8.
- **Target: 1.5 x the stop distance, SOLVED NET OF COSTS**, so a target exit
  returns 1.5 risk units after the round trip rather than netting out to less.
- **Time exit: the close of the bar preceding the THIRD funding settlement after
  entry.** Denominated in settlements, not bars, so elapsed hold is **16 to 24
  hours** depending on where entry falls in the 8-hour cycle. Derived from a
  0.022R funding budget — 20% of the cost tolerance — at an assumed 0.01% per 8h,
  **rounded down** from 3.3.
- **`COST_TOLERANCE_R` = 0.11.** Frozen. Its justification is not.

### 5.3 TWO DELIBERATE DEPARTURES FROM THE OWNER'S ORIGINAL BRIEF

**NO OSCILLATOR.** Report 20 established that **RSI is entailed by channel
position and carries no independent information at the trigger**: the minimum RSI
on a long breakout bar was 50.85 / 52.98 / 49.48 across the three symbols and the
first percentile never reached 50, against an unconditional distribution centred
on 50 with a fifth percentile near 30. A gate would reject nothing.

**NO VOLUME TERM.** The brief asked for volume to be **central**. The thesis
excludes it, arguing that **the wick-and-reject shape IS an absorption statement
expressed in price** — a volume gate would measure the same event a second time,
in a second unit, at the cost of discarding signals that failed the second
measurement while passing the first. The departure is recorded explicitly so that
"we did not gate on volume" remains a **checkable** explanation rather than a
convenient one if the thesis fails.

> **AND THE CONSEQUENCE IS PRE-STATED:** any future addition of a volume term, an
> oscillator or any further indicator is **a new parameter entering a frozen
> specification**. It is not a return to the brief, and **"the original brief
> wanted volume" is explicitly not available as a justification.**

### 5.4 THE ARITHMETIC, AND THE CORRECTION THAT MATTERS

The thesis originally computed a **44.4% breakeven** and **58.0% detectable-edge**
win rate from a cost model **the engine does not implement**. Amendment 1
corrected them to **40.0%** and **53.6%** by deriving them from
`costs.position_size` and `costs.solve_target` as written.

**THE REFRAMING IS THE SUBSTANTIVE PART, AND IT IS EASY TO GET BACKWARDS:**

> **COSTS DO NOT RAISE THE REQUIRED WIN RATE. THEY LOWER THE ACHIEVABLE ONE BY
> PLACING THE TARGET FURTHER AWAY.**

Breakeven at 1:1.5 is `1/(1+1.5) = 40.0%` and depends **only** on the
reward-to-risk ratio; nothing about fees, slippage or funding can move it. What
costs do is inflate the gross target distance to `1.5s + 2.5c`, which at the
frozen tolerance is **+18.33%** further to travel, while shrinking notional by
**9.91%**. **The lever acts on the achievable side, not the required side**, so
any argument that a cost improvement lowers a threshold is wrong on this system.

**The error survived review because it was CONSERVATIVE** — it made the thesis
look harder than it is — and the amendment records the general lesson: **errors in
the conservative direction are the ones that survive review, precisely because
they are conservative. A pessimistic number is not a validated number.**

### 5.5 THE SIX PRE-COMMITTED KILL CONDITIONS

**Goalposts. Fixed at `02e47a5` and not movable, softenable or reinterpretable in
light of any result.**

- **(a) OUT-OF-SAMPLE EXPECTANCY.** At or below zero after costs on a symbol, that
  symbol fails.
- **(b) TWO-OF-THREE.** A symbol qualifies only if it passes on its own **and** at
  least one other symbol shows the same direction of edge, defined as expectancy
  exceeding zero by at least 0.05R.
- **(c) THESIS-BACKWARDS.** If continuation outperforms reversal on the same
  trigger population, the mechanism is refuted **regardless of absolute
  expectancy**. A profitable strategy whose stated mechanism runs backwards is not
  this thesis.
- **(d) FLOOR-STRATUM DECOMPOSITION.** If the advantage does not survive among
  non-floor-bound trades at 0.05R or better, **the thesis is about percentage stop
  width rather than about sweeps.** Flagged in the thesis itself as the condition
  most likely to bite.
- **(e) TIME-EXIT DOMINANCE.** If time exits exceed 40% of trades, the design is
  **refuted, not repaired** — no adjustment of the settlement count, target or
  horizon is permitted as a response. This exists because the dead hypothesis's
  time stop reached 45 to 83% of exits and that was the wrong shape, not a
  patchable bug.
- **(f) TRAINING-FOLD COHERENCE.** If more than half of admissible grid points
  have negative **training** expectancy, the strategy fails to fit before it fails
  to generalise.

**AGGREGATION: every condition is evaluated at the fold level and aggregated by
MAJORITY across the nine folds — at least five of nine — with per-fold figures
reported in every case.** No condition is evaluated on pooled data alone or on a
single fold. **The nine folds overlap by 50% in their training windows and are a
STABILITY PROBE, NOT NINE INDEPENDENT TRIALS**; majority across them is a
consistency requirement and must not be reported as a significance test.

**AND THE RULE'S COST IS PRE-ACCEPTED:** if the edge is real but concentrated in
ranging conditions and fewer than five folds are predominantly ranging, **the rule
kills a real edge.** That is recorded as the correct conservative failure and as a
known cost, and it is explicitly **not grounds for re-running with a different
rule.**

---

## 6. WHAT IS FROZEN

**Membership is defined by extension at
`docs/design/04_0_divergence_disposition_amendment_2.md` §2 and the list is OPEN
FORWARD: any document subsequently committed as a pre-registration joins on its
commit, and a reader finding one must treat it as a member without waiting for the
list to be reissued.**

**The thesis:** `22_point_1_thesis.md`, `22a_..._amendment_1.md`.

**The standing brief:** `00_standing_brief.md`, as amended by
`04_0_divergence_disposition.md` §3.

**The aggregate risk budget:** `05_aggregate_risk_budget.md` and amendments 1 and
2.

**The exit resolution specification:** `06_exit_resolution_spec.md` and amendment
1.

**The divergence disposition chain:** `04_0_divergence_disposition.md` and
amendments 1 and 2.

**The Point 4 decision chain:** `04_0_decision_rule.md`, `04_1a_denomination.md`
and its amendment 1, `04_1b_tolerance_and_branch.md`,
`04_1c_non_uniformity_check.md`, `04_1c_path_and_scope.md`,
`04_1c_denominator_choice.md`, `04_1c_pre_commitments.md`,
`04_1c_level_method.md`, `04_1c_proper.md`, `04_1d_standing_practices.md`,
`04_1c_consequences_and_thresholds.md`.

**A KNOWN HOLE IN THE MEMBERSHIP CRITERION, LOGGED AND OPEN.**
`docs/design/04_0_decision_rule.md` §9(i) records that the criterion admits future
documents as those "committed as a pre-registration under this project's
discipline" **without stating what marks a document as one** — the phrase defines
membership by the property whose definition is at issue, **in a document that
adopts a standing rule against scope terms defined by neither extension nor
principle. An operational marker is owed and none has been invented.**

### 6.1 THE STANDING BRIEF, AND WHY IT EXISTS

`docs/design/00_standing_brief.md` is a **verbatim transcription of the project
owner's premises as given in conversation**: capital of approximately $2,000; risk
per trade never more than 1%, that is $20, enforced after fees and estimated
slippage; crypto only, BTC/ETH/SOL; Bitget by default; intraday style with 5m, 15m
and 1h named as timeframe candidates; **a 30 to 50% peak-to-trough drawdown
tolerance**; three to four indicators with volume central; fee honesty before any
strategy is treated as promising; regime-aware validation with walk-forward and a
strict holdout; **a backtest is a hypothesis, never proof**; and not financial
advice.

**IT WAS WRITTEN BECAUSE THE PREMISES EXISTED NOWHERE IN THE REPOSITORY.**
`docs/handoff/31_point_5_closing.md` §12.1 recorded that **the most consequential
number in Point 5 — the entire $120 budget — is derived from a drawdown tolerance
that no reader of the repository could check.** The transcription is deliberately
**non-normative** and preserves the source's looseness, hedging and open questions
**because every frozen document was written against the loose version.**

---

## 7. THE PERFORMANCE FIREWALL

### 7.1 WHAT IT FORBIDS AND WHY IT IS THE CENTRAL MECHANISM

> **NO WIN RATE, EXPECTANCY, PROFIT FACTOR, SHARPE, SORTINO, EQUITY CURVE,
> DRAWDOWN, `r_multiple`, `net_pnl` OR `gross_pnl` FIGURE EXISTS ANYWHERE IN THIS
> REPOSITORY FOR THIS THESIS.**

**No such quantity may be computed, inspected or estimated — not to check the
engine works, not on one symbol, not on one fold, not on one day.**

**IT LIFTS WHEN THE VALIDATION DESIGN IS SEPARATELY WRITTEN, AGREED AND
COMMITTED**, and that design must not run the engine in `full` mode and must not
open the holdout. **The validation design is committed before the first
performance figure exists.**

**IT IS ENFORCED BY COMMIT ORDER, NOT BY INFORMATION BARRIERS.** The guard is
**order**; the commit hash is the evidence, **and it is evidence that survives
everyone's account of what they were thinking.** What would falsify the claim: a
commit at or before the stated hash containing an outcome figure for this thesis,
in a report, a document, a stored artifact under `reports/`, or a committed data
file.

### 7.2 THE ENFORCED LIST, AND A THREE-WAY DIVERGENCE

**The canonical list is `src/firewall.py`, defined once**, and
`tests/test_firewall_names.py` asserts over the AST that no module defines its own
copy. **The twelve names:** `expectancy`, `win_rate`, `winrate`, `profit_factor`,
`sharpe`, `sortino`, `net_pnl`, `gross_pnl`, `drawdown`, `r_multiple`, `equity`,
`pnl`. **The list only ever grows; a name is never removed.**

**IT WAS PREVIOUSLY WRITTEN OUT IN EIGHTEEN TEST MODULES AND HAD DRIFTED:**
fourteen carried twelve names and **four carried a nine-name variant missing
`sortino`, `gross_pnl` and `drawdown`** — a guard with three holes in it, passing
silently. Commit `47a26de` consolidated them; **aligning all eighteen sites caused
no test to fail**, which establishes nothing had fallen through the holes. **The
prose statement at `docs/handoff/31_point_5_closing.md` §11 diverges from both
lists** in membership and spelling, and is logged as **erratum entry 10** rather
than patched.

### 7.3 HOW WORK PROCEEDS UNDER IT

Every decision so far has been made from **permitted pre-firewall quantities**:
occupancy and concurrency counts on positions whose exits are calendar arithmetic;
venue schedules retrieved and hash-snapshotted; allocation counts under the frozen
budget; bar-geometry distributions; quantities, notionals and price levels; path
arithmetic over a partition tree; and synthetic fixtures on hand-written prices.
**`src/engine/simulate.py` CAN compute the forbidden quantities and has not been
run on this thesis.** `full` mode sits behind an explicit token rather than a
boolean, **so spending the firewall is a deliberate and greppable act.**

---

## 8. WHERE THE PROJECT ACTUALLY IS — POINT 4, SUB-POINT 4.1c

**This is the live work, and it is the thing a second reader most needs to hold.**

### 8.1 THE PROBLEM THAT OPENED IT

**The 1.50% stop floor and `COST_TOLERANCE_R = 0.11` are not a consistent pair,
and that is falsified by measurement rather than argued.** Report 28 §9 measured
the floor-bound stratum's minimum cost-over-stop ratio at **0.1122 against the
tolerance's 0.11**, across 2,927 floor-bound positions of 11,384 candidates, and
found **no overlap at all**.

> **THE 1.500% FLOOR DOES NOT ENFORCE A TOLERANCE OF 0.11 AND CANNOT. Every
> position the floor governs breaches the tolerance the floor exists to enforce.**

**And the tolerance's own justification had already collapsed.** It was derived as
"one third of the ~0.34R minimum detectable edge", which **presumes costs subtract
from expectancy in R** — which, under net-solved geometry, they do not. **The
number is frozen; the argument for it is owed**, and it must be settled **before**
any performance figure is seen, because settling it afterwards would be selecting
a justification to fit a result.

### 8.2 THE DECISION CHAIN, IN COMMIT ORDER

**Each link is committed alone, before the quantity it governs exists. That
separation is the entire defence and it is checkable from `git log`.**

- **`77a226b` — the decision rule.** One option falsified by measurement, one
  closed by prior commitment, and **a two-way fork left open**: Branch B, a
  tolerance exists and the floor is derived algebraically to enforce it; Branch C,
  the tolerance is retired and the floor is governed by the tick grid, lot-size
  granularity and venue leverage. **Neither branch is cheaper** — B owes an
  argument that has already failed once, C owes the restructuring of a frozen kill
  condition, since **under Branch C the floor-bound stratum ceases to exist as a
  category and kill condition (d) has no definition.**
- **`b807744` — 4.1a.** The constraint is denominated in the stop path.
- **`5c55776` — report 32.** The parametric floor under that denomination.
  Superseded, not falsified.
- **`02992c7` — amendment 1 to 4.1a.** Re-denominates the numerator onto the
  unvalidated term.
- **`af7866d`, `7a08069` — the non-uniformity threshold**, committed before the
  derivation existed; the trigger did not fire. Later rendered **inapplicable**,
  not falsified.
- **`56a11f6` — 4.1b. BRANCH B CHOSEN**, with an honest limitation reported: **the
  account of what the tolerance protects does not discriminate between candidate
  values.**
- **`22e323a`, `3007dbd` — reports 33 and 34.** Revised closed form and re-run.
  Superseded.
- **`2983cac` — report 35.** Establishes there are **two cost paths, not one.**
- **`506977b` — 4.1c path and scope.** Path two committed as the risk unit;
  funding committed into the unvalidated set.
- **`a9083b0` — 4.1c denominator choice.** **The constraint is denominated in the
  risk unit itself**, on the ground that the constraint and its rationale become
  the same object.
- **`de05a18`, `e4122b6` — report 36, THE GOVERNING CLOSED FORM.** Grid committed
  first and alone; solver added after.
- **`5ec36c0` — pre-commitments.** The admitted domain, reject-over-clip, the two
  rejection populations, **five disqualifying properties a level-setting method
  must not have**, and the consolidated errata index.
- **`1a0aa24` — the level method.** One method proposed, tested against the five
  properties one at a time, **and reported DISQUALIFIED on property (b)**, because
  it needed a bound on how wrong the unvalidated estimates might be and the stop
  haircut cannot be validated against this data layer at all.
- **`db3a6de` — 4.1c step 1, the calibration.** Budget and uncertainty parameter
  committed, **with no level and no width stated anywhere in the document, not
  even to disclaim one.**
- **`c6b71c5`, `47a26de`, `fc8933f` — the standing rules, the firewall
  consolidation, and the standing practices.**
- **`eebe986` — report 37, step 2. THE LEVEL.**
- **`2a04e37` — step 3, `04_1c_consequences_and_thresholds.md`. THE CLOSE.** The
  rejection rule narrowed, kill condition (d) disposed of, the magnitude threshold
  committed, two ledger instances logged. **Sub-point 4.1c and sub-point 4.1 are
  both CLOSED.** §8.5.

### 8.3 THE CALIBRATION, AND ITS HONESTY

**The derivation route failed, so the project owner chose the JUDGEMENT route**,
and it is recorded as judgement rather than presented as derived.

- **THE RISK-DISPLACEMENT BUDGET: ten per cent of one risk unit** — two dollars of
  the twenty. **What it means to accept it:** a stop-out may return worse than one
  risk unit by up to that fraction if the estimates are wrong adversely. **That is
  a weakening of the standing 1% rule and is stated as one, not argued away.**
- **THE UNCERTAINTY PARAMETER: one hundred per cent proportional error** — the
  true value may be up to twice the modelled value.
- **ITS SCOPE: the ENTIRE unvalidated sum** — stop haircut plus provisioned
  funding — argued from **symmetry of ignorance**, since both are estimates and
  neither is better founded, and because the constraint binds the same bundle.
- **WHAT WOULD HAVE MADE A DIFFERENT BUDGET CORRECT** is stated in two forms,
  because **a judgement that cannot say what would have changed it is
  indistinguishable from a preference.**

> **THE CALIBRATION DOES NOT DERIVE THE TOLERANCE. IT RE-DESCRIBES IT IN UNITS A
> PERSON CAN HOLD AN OPINION ABOUT.** The divisor is one; the mapping is an
> identity, not a calculation, and it is not presented as one.

**AND THE ROUND-NUMBER PROBLEM WAS DISCLOSED BEFORE THE NUMBER EXISTED.** Step 1
stated in advance that the relation was simple enough that the result might be
round, that a round number emerging from a judgement calibration is exactly the
appearance the sub-point had guarded against throughout, and that **the document
could not answer the suspicion by argument, because any argument would be equally
available to someone who had chosen the number first.**

> ### THE DEFENCE IS THE COMMIT ORDER AND NOT THE ARITHMETIC.

### 8.4 WHAT STEP 2 RETURNED

> ### THE LEVEL IS 0.10.

- **It lies inside the admitted domain**, which report 36 gives as the interval
  common to all six cells: **0.03554692 to 0.40**, bounded below by SOLUSDT short
  at the frozen cap and above by the BTCUSDT and ETHUSDT zero-width ceiling.
  Checked, not assumed.
- **THE FLOOR WIDTHS**, as a percentage of entry price: **BTCUSDT and ETHUSDT
  0.597669 long and 0.602349 short; SOLUSDT 1.041253 long and 1.058895 short.**
  **Shorts require the wider floor at every symbol**, because the haircut and the
  stop-leg fee are charged on a stop price above entry.
- **Every width was fed back through the engine's own functions**, with a maximum
  absolute residual of **8.049e-16**.
- **Against the retired 1.50% constant, every width is narrower** — BTC and ETH by
  about 0.90 percentage points, SOL by about 0.45. **That comparison is
  ORIENTATION AND NOT JUSTIFICATION**, and selecting a level by reference to the
  widths it implies, **including because they are close to the retired figure, is
  a DISQUALIFYING property** of a level-setting method. A test asserts over the
  module's AST that the retired constant enters no computation.
- **THE STRESS COMPARATOR: 0.12977480, binding from SOLUSDT short.** The
  comparator is **looser** than the committed level, so committed scoping buys its
  symmetry of ignorance at the price of roughly a third more width. **It does not
  govern, and its result is barred in advance from reopening the scope
  decision** — revising a scope once its cost is visible is selecting the scope by
  its consequence.
- **FLOOR BINDING COLLAPSES.** At the new level, pooled binding is **221 of 11,384
  = 1.9413%** — BTCUSDT 154 (4.12%), ETHUSDT 51 (1.37%), SOLUSDT 16 (0.41%) —
  against **25.71% pooled at the retired 1.500% constant. The symbol ordering has
  also inverted**: under a constant floor the binding symbol was the least
  volatile relative to price; under a per-symbol floor SOLUSDT carries the widest
  floor and binds least.
- **FOLD 4 TEST REMAINS THE BOTTLENECK at every granularity measured** — 793
  non-floor-bound pooled and 12.47% bound, with the two thinnest cells anywhere
  being fold 4 test ETHUSDT at 238 and BTCUSDT at 244.
- **POPULATION A — the required floor above the cap — COUNTED AT ZERO**, across
  all 11,384 candidates and all six cells, because **a count of zero reported is
  evidence and a count of zero assumed is a restatement of the definition.**
- **POPULATION B — the ATR-derived stop above the cap — COUNTED FOR THE FIRST
  TIME: 1,967 of 11,384, 17.28% pooled**, being BTCUSDT 117 (3.13%), ETHUSDT 350
  (9.42%) and **SOLUSDT 1,500 (38.13%)**. It is bar geometry and **independent of
  the level entirely.** It is **disjoint** from the floor-bound set, necessarily,
  because population A is empty.

### 8.5 STEP 3, WHICH CLOSED 4.1c

**`docs/design/04_1c_consequences_and_thresholds.md`, commit `2a04e37`.** It
decided three things.

**FIRST — THE REJECTION RULE, NARROWED.**

> **REJECT APPLIES TO POPULATION A ALONE. POPULATION B — the raw ATR-derived stop
> above the cap — IS CLIPPED TO THE CAP**, which is what
> `costs.stop_geometry` already does. The decision changes no implementation; it
> narrows a rule that had been committed over a population its own argument did
> not reach.

**The ground is the cost ground alone.** Reject-over-clip was argued from cost
protection: a clipped position carries a stop narrower than the constraint
requires, so a larger unvalidated share than the tolerance permits. **That reaches
population A exactly and has no purchase on B**, because a B position clipped to
the cap carries a stop **at** the cap, and **the cap exceeds every required floor
by between 3.31 and 5.86 times** — smallest at SOLUSDT short, largest at BTCUSDT
and ETHUSDT long. Its unvalidated share therefore sits far below the tolerance.

**The mechanism is stated in the right direction, which matters:** clipping makes
the stop **NARROWER** than the bar's volatility implies, not wider, **and
narrowing is the direction the cost argument worries about. The case is safe
because the cap still far exceeds the floor, not because clipping helps.** If the
cap were ever lowered toward the floors, or the floors raised toward the cap, the
decision would have to be remade.

**The admissible population is unchanged at 11,384**, because population A counts
zero — **recorded as a consequence after the argument and expressly not a reason
for it.**

**SECOND — KILL CONDITION (d), DISPOSED OF.**

**(d) named a floor that no longer exists**; the 1.50% constant is retired and the
governing floor is per symbol and per direction. **That is a supersession, not an
erratum** — the thesis was correct when written — but the stratifying predicate
was not executable as written.

> **STRATUM: the non-floor-bound stratum under the COMMITTED per-symbol,
> per-direction floor.** The predicate is unchanged in kind — did the cost floor,
> rather than the volatility, set the stop? — and only the floor it refers to has
> moved.

> **LEVEL: POOLED over the whole evaluation window. The per-fold decomposition is
> reported as a stability probe and is NOT aggregated by majority for this
> condition.**

**The first reason does not depend on stratum thinness at all:** the fold
schedule's own docstring states that the nine folds are **a stability probe, not
nine independent trials, and that if they are ever counted as trials the
arithmetic is wrong.** A majority-of-nine rule counts them as trials. The second
reason is the thinness problem. **That pooling is also the more forgiving level is
stated as a reason rather than left to be noticed**, and the document concedes
that a reader who holds the more forgiving level should not be chosen by the party
it forgives is entitled to the objection — answering it with the first reason.

**AND THE CONCERN IS REDUCED, NOT ELIMINATED.** The non-floor-bound **candidate**
stratum is ample at 11,163 of 11,384, or 98.06%. **But (d) is evaluated on TRADES,
and the taken population is a function of realised outcomes, so its stratum size
is not knowable at this commit.** Saying the concern is eliminated would put a
knowable number where an unknowable one belongs. **Whether 0.05R is DETECTABLE on
the stratum that materialises is routed to the first-run diagnostic gate**, where
the stratum's size is a count rather than an outcome quantity. **If it proves too
thin, that is a finding about the condition's evaluability and must be recorded as
one rather than resolved by moving the threshold.**

**THIRD — THE MAGNITUDE THRESHOLD, COMMITTED.**

**The question was: at what magnitude does a breach of the after-costs risk rule
stop being tolerable? The answer begins by establishing that magnitude alone
cannot answer it.**

> ### THE REJECTED CASE IS SMALLER THAN THE ACCEPTED ONE.

The funding treatment rejected at **1.16 to 1.80 per cent of a risk unit** is
smaller than the displacement budget accepted at **ten per cent**. **Any threshold
of the form "tolerable below X" that rejects the first must reject the second.**
That is not a difficulty to work around; **it is what tells us the separating
property is not magnitude.**

> ### THE SEPARATING PROPERTY IS MODALITY. A BREACH THAT OCCURS WITH PROBABILITY
> ### ONE UNDER BASELINE MODEL ASSUMPTIONS IS A DIFFERENT OBJECT FROM A CONTINGENT
> ### DISPLACEMENT UNDER AN ADVERSE ASSUMPTION ABOUT AN UNVALIDATED ESTIMATE.

A certain breach **misstates the risk unit on every position it touches, with
nothing needing to go wrong — a defect in the statement of the rule.** A
contingent displacement **leaves the rule exact in the model as specified** and
bounds how far reality may move it.

**THE THRESHOLD, AS COMMITTED — FIRST MODALITY, THEN MAGNITUDE:**

- **(i)** A **contingent** displacement is governed by the displacement budget and
  by nothing in that section. Its tolerable magnitude is that budget.
- **(ii)** A **certain** breach is tolerable **only if its magnitude is below the
  imprecision with which the risk unit can already be delivered. The anchor is the
  LOT-GRANULARITY DRAG: 0.80 per cent of nominal risk, pooled.**
- **(iii)** A certain breach at or above that anchor **is not tolerable** unless
  argued on its own grounds elsewhere.

**The reasoning for the anchor:** flooring quantity to the venue's lot step
already means the risk unit delivered is not the one nominated, by 0.80% pooled.
**A certain breach smaller than that is below the precision at which the rule can
be enforced at all; a larger one becomes the binding imprecision**, and the rule's
stated figure stops describing what the mechanism delivers.

**IT PASSES THE TEST IT HAD TO PASS.** The fill-price term at 0.017% is below the
anchor and was accepted; the funding treatment at 1.16% is above it and was
rejected. **Both prior decisions are reproduced, by a criterion neither of them was
chosen against.**

**AND THE DOCUMENT SEPARATES WHAT IS DERIVED FROM WHAT IS JUDGED. The ORDERING is
derived** — forced by the three cases, since no magnitude-only rule can separate
them. **The ANCHOR is a judgement**, recorded as one, with two alternatives named:
anchoring on the tick grid gives a tighter bar, and anchoring on the worst single
position's 9.21% granularity drag gives a far looser one. **The pooled figure was
chosen because the threshold governs terms that apply systematically rather than
to one position.**

### 8.6 WHAT REMAINS OWED AFTER 4.1

> ### SUB-POINT 4.1c IS CLOSED. SUB-POINT 4.1 IS CLOSED.

**What 4.1 produced:** a constraint denominated in the risk unit, a closed form for
the floor it implies, a level reached by a judgement recorded as judgement, the
widths that follow, a stratification, the first count of a population that had been
defined but never counted, and a magnitude threshold that makes three prior
decisions consistent. **And no performance figure.**

**INSIDE POINT 4:**

1. **(d)'s DETECTABILITY**, routed to the first-run diagnostic gate.
2. **THE VOLATILITY QUESTION — whether a stop clipped narrower than volatility
   implies is itself undesirable.** It is a question about whether the geometry the
   strategy was designed around survives being truncated. **It is argued nowhere in
   this repository, no committed document takes a position on it, and it is named
   as open and expressly not characterised as unimportant. It has NO OWNER at this
   commit.**
3. **Point 4's remaining agenda** — §9(a) through (g) below, **less what 4.1
   discharged.** No committed document fixes a sub-point numbering beyond 4.1, so
   the next step's label is for whoever opens it.

**HOUSEKEEPING, both routed and neither done:**

4. **The errata index should become a standalone artifact.** It lives inside a
   frozen document that cannot be edited, so every entry after its own commit sits
   somewhere else. **An index whose entries are scattered across the documents that
   made them is the failure it was created to solve.**
5. **`docs/prompts/STANDING_RULES.md` §12 is out of date** — it describes seven
   practices as uncommitted and four were since committed. That file is amended by
   a new file and never edited, **so an amendment is owed.**

**AND BEYOND 4.1, THE VALIDATION DESIGN ITSELF IS STILL OWED IN FULL.** §9.

---

## 9. WHAT THE VALIDATION DESIGN MUST CONTAIN

**Source: `docs/handoff/31_point_5_closing.md` §9. Requirements, not
suggestions.**

- **(a) Fold structure and the walk-forward procedure**, on the existing nine
  folds, **with the aggregation rule stated against the fact that they overlap by
  50% and are not independent trials.**
- **(b) The metrics, and the level each is computed at** — per symbol, per fold,
  or pooled, **each specified once**. A metric whose level is left open is a metric
  that will be computed at whichever level first looks informative.
- **(c) The kill conditions, restated for the capped, path-dependent
  population.** The thesis's conditions were written against the uncapped
  population; they now govern one that is **47.11% smaller at maximum hold, is a
  function of realised outcomes, and is non-uniform in hold duration by
  construction.**
- **(d) Parameter-sensitivity checks, and what constitutes curve-fitting**, stated
  as a criterion rather than as a caution.
- **(e) The order of inspection**, and what the response is to each kind of
  failure, **written before the first figure exists. An order chosen after a
  result is an order chosen to reach it.**
- **(f) A first-run diagnostic gate — REQUIRED, pre-registered, and
  outcome-independent.** Its necessity is a consequence of Point 5's own correct
  decision: **every `full`-mode verification so far is synthetic**, so when the
  engine first meets real data, **a defect in level evaluation would surface at
  the same moment as the first performance figures, and separating them would
  require inspecting outcomes — which is how a validation design gets fitted.**
  Candidate checks, all computable without touching `exit_reason`: taken and
  skipped counts and the budget invariants; the intrabar-precedence flag count,
  which **should be near zero at 1m, so a large value means the fill logic is
  wrong rather than that the market was volatile**; the missing-bar flag count,
  which **must be exactly zero in sample**; every emitted stop and target price on
  the tick grid; and every realised risk at or below nominal. **The gate is only
  available if it is specified before the run** — afterwards every check is still
  computable and none is still evidence.
- **(g) The disposition of every open item — all nine — each with a decision or an
  explicit deferral naming what it is deferred to.**

---

## 10. THE OPEN ITEMS

### 10.1 THE NINE FROM POINT 5

1. **`COST_TOLERANCE_R`'s justification, together with the 1.50% stop floor.**
   One item, not two. **DISCHARGED by Point 4 sub-point 4.1**, which retired the
   constant floor, re-denominated the constraint on the risk unit, and derived a
   per-symbol per-direction floor from a level set by recorded judgement — §8.
2. **The stop haircut itself.** 5 bps on BTC and ETH, 10 bps on SOL, and **it IS
   the entire slippage-and-gap model**, described in the engine's own source as a
   placeholder and confirmed not to be a venue-published figure. **It cannot be
   validated against this data layer**, because `open` is **synthesised** from the
   carried-forward previous close and dropped by every loader, so **no bar's first
   observed price exists at any resolution. A bar that opens beyond the stop is
   invisible.**
3. **The fill-price term.** The exit fee is charged on the **stop level** while
   the actual fill sits a haircut away. **At most 0.0033 USDT, under 0.017% of a
   risk unit — and it makes a SHORT stop-out breach 1.0R**, in the direction the
   standing rule exists to prevent. **The criterion it was missing is now
   committed** — §8.5, third part — **and it reproduces the original acceptance.**
4. **The Rule C hold-duration selection effect.** Exits free budget at settlement
   instants, and those are exactly the entry hours that draw 24-hour holds, so
   **the traded population is non-uniform in hold duration BY CONSTRUCTION — and
   the non-uniformity is produced by the budget rule rather than by the market.**
   Its size was never measured.
5. **The capital-supply flatline.** Taken counts per training period are almost
   flat at 976 to 1,025 while signal supply varies widely. **Trade count per fold
   measures CAPITAL, not market conditions.** A fold with more signals produces
   more skips, not more trades. **Any threshold or power calculation denominated
   in trade count is denominated in a quantity the budget pins nearly flat.**
6. **Path dependence.** Under the budget with real exits the traded population is
   a function of realised outcomes — a stop-out frees its slot hours before a time
   exit would — **so it is not a subset of anything knowable in advance.** Report
   21's 200/50 adequacy thresholds were established on the uncapped population and
   **do not describe what is traded.**
7. **R-multiple weighting.** Equal-weighted or dollar-weighted is undecided. Both
   `nominal_risk_usd` and `realised_risk_usd` are stored per position and neither
   is derived from the other at read time, precisely to keep the choice open.
8. **The operational leverage setting**, and the disposition of
   `costs.CostConfig.max_leverage`, which is **still 3.0** in legacy paths whose
   tests pin it while the new execution path implements **no leverage refusal at
   all. Two different answers coexist in the repository.**
9. **At what level kill condition (d) is evaluated. DISPOSED at 4.1c step 3:
   the stratum is defined under the committed per-symbol per-direction floor and
   the level is POOLED**, with the per-fold decomposition reported but not
   aggregated. **Detectability on the taken stratum remains routed forward.** §8.5.

### 10.2 THE POINT 6 QUEUE, AT FOUR

1. **The expiry re-argument.** If the haircut is measured, the estimate becomes an
   observation and the constraint's rationale weakens, so its justification must be
   re-argued. **Enlarged once the numerator narrowed onto the haircut**: the
   constraint's sole input is replaced at that moment rather than merely improved
   upon.
2. **Folding measured slippage into the unvalidated set.** Entry slippage is a
   committed member of that set, **frozen at zero, carrying no magnitude today.**
3. **Re-evaluating the achievable domain**, because the zero-width limit rises
   with the unvalidated total, so a non-zero slippage moves the domain's upper
   bound and the grid built inside it. **The admitted domain itself changes — this
   is not a re-run on new inputs.**
4. **The empirical audit of the displacement budget.** When paper trading supplies
   observed fills, the realised displacement is measured against the budget, and
   the budget, the uncertainty parameter and the level are re-argued.

> **ITEMS 2 AND 3 ARE ONE EVENT WITH TWO CONSEQUENCES**, listed separately because
> a step doing the first without the second would leave a domain that no longer
> bounds what it claims to.

**AND THE AUDIT IS WHAT MAKES THE JUDGEMENT CHECKABLE:** a judgement with a stated
falsifier is a hypothesis; one without is a preference. **It is not a promise that
the judgement is right. It is a commitment that it will be found out if it is
wrong, on a schedule fixed before the answer is known.**

---

## 11. THE RULES THAT CONSTRAIN AN ARGUMENT

**A second reader who wants to argue well in this project needs these more than
they need the strategy. An argument that violates one of them is not a strong
argument that loses; it is inadmissible.**

### 11.1 THE TWO RULES WITH TEETH

> **THE ORDER RULE. The justification for the tolerance must be stated and
> committed IN ITS OWN COMMIT before the curve is evaluated at any candidate
> value.** Producing the curve is not evaluating it; what is forbidden is
> **selecting a value after seeing the floor widths the candidate values imply.**

> **THE DIRECTION RULE. The tolerance is the primitive and the floor is derived
> from it. The derivation runs tolerance to floor and NEVER floor to tolerance**,
> because **a floor stated as a constant is a tunable parameter wearing a
> constraint's name.**

**The direction rule exists specifically to stop a closed option from reappearing
under another name** — without it, "we retained the floor and re-derived the
tolerance to match" is available as a description of the same move.

### 11.2 THE PRINCIPLES THAT DECIDE TIES

- **EXECUTION REALITY OVER MEASUREMENT CONVENIENCE. The cost of re-measuring is
  not a consideration in the branch choice.** If a derivation implies that closed
  reports rest on a floor that does not enforce what it was meant to, **that is a
  finding about the reports and not an argument against the derivation.**
- **A CRITERION PHRASED AS VIABILITY, ABSURDITY, COLLAPSE OR UNNATURALNESS IS NOT
  EVALUABLE**, and is decided in practice by whoever reads it after the numbers
  arrive. **Consequences are denominated in named quantities with implementations
  and known achievable ranges**, of which four are fixed for the stop floor: the
  floor-binding fraction, lot-granularity drag, absolute target distance in price
  space, and **the thickness of the non-floor-bound stratum, which matters most
  because kill condition (d) is evaluated on it.**
- **ONE DIRECTIONAL CORRECTION, BECAUSE THE INTUITION RUNS THE WRONG WAY:**
  **widening the floor does not raise the leverage requirement, it LOWERS it**,
  since risk per position is fixed and notional is inversely proportional to stop
  width. **Leverage is therefore not a constraint that binds against widening and
  must not be offered as one.** It is recorded because it is the argument most
  likely to be reached for.
- **A JUDGEMENT MUST SAY WHAT WOULD HAVE MADE A DIFFERENT ANSWER CORRECT**, or it
  is indistinguishable from a preference.
- **AN ARGUMENT THAT SURVIVES A FAILED RESULT IS A RATIONALISATION**, which is why
  motivating arguments are pre-registered.

### 11.3 THE DRAFTING RULES

- **A SCOPE TERM INSIDE A BINDING CLAUSE IS DEFINED EITHER BY EXTENSION — an
  explicit list of documents, paths or cases — OR BY A STATED PRINCIPLE FOLLOWED
  BY AN EXPLICIT "INCLUDING WITHOUT LIMITATION" ILLUSTRATION. IT IS NEVER DEFINED
  BY EXAMPLE ALONE.** The reason: **a clause written to be inconvenient later is
  read later by someone for whom it is inconvenient, and a scope stated by example
  is read as narrowly as the examples permit.**
- **A PROMPT MUST NEVER PRE-STATE THE EXPECTED VALUE OF A QUANTITY WHOSE
  DETERMINATION THAT SAME PROMPT DELEGATES.** Stated as a prohibition on the
  drafting side, because by the time the implementing session meets it both
  readings are already unsatisfiable and all it can do is report.
- **AN INSTRUCTION REQUIRING VERBATIM TRANSCRIPTION MAY NOT ALSO CONSTRAIN THE
  CONTENT OF THE TRANSCRIBED TEXT.** The two requirements are unsatisfiable
  together.
- **THE IMPLEMENTING SESSION REPORTS A CONTRADICTION RATHER THAN RESOLVING IT.**
  This is the single most frequently exercised rule in the project.

### 11.4 THE VERIFICATION RULES

- **ANY CHECK THAT SEARCHES SOURCE TEXT RUNS OVER EXECUTABLE TOKENS OR AST NODES,
  NEVER OVER RAW TEXT** — because this project's modules are written to state the
  prohibitions they obey, and **a check that cannot distinguish a citation from a
  violation will demand the removal of the citation.**
- **A CHECK CAN BE WRONG ABOUT WHAT IT MATCHES.** Instance (37) is a check that
  asserted a formatting defect against a clean document using a character class
  that matched em dashes rather than box-drawing characters. **The document was
  correct and the check was wrong.**
- **A FALSELY FIRING CHECK IS LOGGED AS A LEDGER INSTANCE IF AND ONLY IF THE
  IMMEDIATE REMEDIATION ON OFFER WOULD HAVE DEGRADED AN OTHERWISE CORRECT
  ARTIFACT.** Routine test iteration is excluded. The criterion exists **so the
  next such check is classified by someone who does not yet know which way it will
  come out.**

### 11.5 THE WORKING RULES

- **One point at a time.**
- **Decisions before code.**
- **No code in chat.**
- **Claude Code prompts for anything built.**
- **FRICTION OVER COMPLIANCE — an objection raised is worth more than an
  instruction followed.**
- **THE READ-BACK PROTOCOL: artifacts are transferred by FILE UPLOAD, not by
  pasting. The chat report-back carries only SHA-256, line count, commit hash and
  test count.** A hash that matches proves the file on disk is correct and
  **proves nothing whatever about a paste that accompanies it**, and the two were
  repeatedly observed to disagree.
- **A mutation that disables a pre-read guard never faces the real data
  directory.**
- **Prompts do not name new test files, and target paths are checked before
  writing.**
- **A step creates the files its instruction names and modifies nothing else.** A
  decision is committed alone; a derivation and its tests are committed together
  and with nothing else. **`MANIFEST.md` and the consolidated errata index are the
  two exemptions.**
- **Errata are LOGGED, NOT PATCHED. No frozen text is edited**, and the correction
  lives in a document other than the one it corrects.
- **A silent edit is a contamination event**, repeated at the end of every frozen
  document.

### 11.6 THE DEFECT LEDGER

**THE TOTAL IS 46**, contiguous from (1), and **instances are never renumbered or
recounted.** Each document adding one reads the total from the most recent
document stating one and shows the arithmetic in a line. **The two most recent:
(45)**, a rule argued on cost protection — which reaches only the population whose
required floor exceeds the cap — committed over both rejection populations, so
**the partition and the rule's scope disagreed inside one section**; and **(46)**,
a verification check asserting an exact count of eighteen modules importing the
canonical banned-name list, which fired against a legitimate nineteenth.

> **THE RECURRING CLASS: a numerical or directional criterion written from a
> mental model of a quantity rather than from its implementation or its achievable
> range.**

**The most common sub-class is internal contradiction between an instruction's own
constraints and its requirements**, at instances (23) to (26), then (33), (35),
(39) and (44) — **in each case a requirement and a constraint referred to the same
quantity and disagreed about who determined it.**

**ALTERNATIVE READINGS OF THE TOTAL ARE ON RECORD RATHER THAN SUPPRESSED.** A
reader holding a committed clause whose letter and illustration diverge to be
itself an instance would have reached a different total at one point; and a reader
holding instance (46) to be routine test iteration — on the ground that the
obvious remediation was to fix the check rather than the module — **would stand at
45 rather than 46.** The call was made on the ground that the inclusion criterion
asks what remediation was **on offer**, not which one a careful implementer would
have taken.

**THE ERRATA INDEX stands at nine entries in its own frozen text and at ten in
fact**, because the maintenance rule requires same-commit entry into a document
its own change discipline forbids editing. **The gap is recorded rather than
worked around, and the index's next holder must carry entry 10 forward.**
Sub-point 4.1c's closing document restates the true standing and **routes the
index to become a standalone artifact**, on the ground that **an index whose
entries are scattered across the documents that made them is the failure it was
created to solve.**

---

## 12. THE MEASURED FACTS THAT EXIST

**Every figure here is a count, a price distance, a rate or a cost. None is an
outcome quantity.**

### 12.1 THE POPULATION

- **11,384 candidate positions** over 2022-01-05T18:00Z to 2024-12-31T23:00Z:
  **BTCUSDT 3,735, ETHUSDT 3,715, SOLUSDT 3,934.**
- **888 candidates fall in no fold period**, preceding the in-sample window's
  2022-04-01 opening. Reported rather than dropped.
- **Nine folds, rolling 6-month train and 3-month test, overlapping 50%.**
- Uncapped signal counts: **worst train fold 570 against a 200 minimum; worst test
  fold 281 against 50.** These describe the **uncapped** population.

### 12.2 THE BOOK

- **Aggregate open nominal risk budget: $120.00**, being 6.0% of $2,000, derived
  by allowing one maximally correlated adverse event to consume at most one fifth
  of the conservative end of the 30 to 50% drawdown tolerance. **A judgement, and
  the source says so at length.**
- **Uncapped**, the book carries a **median of 9 concurrent positions**, requires
  **3.59x median leverage** with a maximum of **13.52x**, and **63.93% of bars
  require more than 3x.**
- **Capped: 6,021 taken, 5,363 skipped, a 47.11% skip rate**, with per-symbol skip
  rates within **0.18 percentage points** of identical. **Every one of the 5,363
  skips arrived at an exactly full budget; partial allocations: zero.**
- **THE 47.11% IS AN UPPER BOUND**, measured at maximum hold; under real exits
  positions close early and admit signals this measurement skips. **How far below
  is unknowable at this commit.**
- **Peak concurrency exactly 6; peak open nominal risk exactly $120.00.** Realised
  risk across the 6,021 taken ranges **18.3392 to 20.0000**, median **19.9237** —
  **never above nominal.**
- **Margin: CROSS**, because under isolated margin at this leverage **the
  liquidation price can sit INSIDE the stop on wide-stop trades, and a stop that
  cannot be reached is not a stop.**
- **Position mode: HEDGE, and it is load-bearing.** Under one-way mode an
  opposite-direction signal **offsets** an open position. **On 24.5 to 26.5% of
  bars — one bar in four — this strategy holds a long and a short on the same
  symbol simultaneously under the cap**, and 46 to 48% uncapped.
- **Ordering rules: A**, cyclic rotation by bar timestamp so each symbol holds
  each priority RANK exactly once in three; **B**, budget charged on **nominal,
  never realised**; **C**, **exits before entries**, which admitted **902
  positions — 14.98% of all taken — that entries-first would have skipped**,
  moving the skip rate by 7.9 percentage points on loop order alone.

### 12.3 COSTS, VENUE AND EXECUTION

- **Fees:** taker on entry, taker on the stop leg via a conditional market order,
  **maker on the target leg**. Base tier throughout; **"fee treatment" means the
  maker/taker composition of the three legs and NOT VIP volume tiers.**
- **Stop haircut: 5 bps BTC and ETH, 10 bps SOL.** Unvalidatable.
- **Funding: provisioned at three settlements in both sizing and realised P&L,
  with NO reconciliation**, at an assumed 0.01% per 8h. **21 of 24 entry hours
  cross two settlements while three are charged**, so the typical position is
  overcharged by one settlement and **never refunded**, and the overcharge falls
  hardest on fast exits, which are disproportionately stop-outs. The provisioned
  reading was chosen because the alternative **makes every R multiple depend on
  the entry hour, and a unit that varies with the clock is not a unit.**
- **Exit conventions: stop fills on inclusive TOUCH; target fills on TRADE-THROUGH
  by one tick; stop takes precedence intrabar and the case is FLAGGED; stop takes
  precedence over the time exit.** **The asymmetry is deliberate — the losing leg
  fills easily, the winning leg fills hard — and it is stated in advance so a low
  target-fill rate cannot later be presented as a discovery.**
- **Exits are evaluated on 1m, and that is REQUIRED rather than preferred.** The
  per-trade upper bound on positions whose stop and target could both sit inside a
  single 1h bar is **10.21% hold-weighted and 11.94% at maximum hold against a
  2.0% criterion — exceeded by 5.1x, independently on every symbol and in every
  one of the eighteen fold periods.**
- **Missing 1m bars are flagged and counted, NEVER filled.** **A missing bar is not
  a price gap: a gap is something the market did, a hole is something the data does
  not know.**
- **Venue limits measured live: 150x, 150x, 100x in tier 1** with maintenance
  margin **0.40%, 0.40%, 0.50%**. Maintenance requirement at the worst bar was
  **$114.40 against $2,000, a 5.72% margin ratio where liquidation triggers at
  100%.** The engine's `max_leverage = 3.0` is **an unmeasured placeholder that
  would bind on 16.14% of bars.**
- **Lot-granularity flooring costs 0.80% of nominal risk** — **$1,826.85 of
  $227,680** across the 11,384 candidates, 0.78% across the 6,021 taken.
  **ETHUSDT is the granularity-binding symbol**; worst single position 9.21%.
  **Flooring places realised risk BELOW nominal and can never breach the 1%
  rule** — it must not be conflated with the fill-price term, which runs the
  opposite way.

### 12.4 THE DATA LAYER

- **In-sample 1m layer is exactly full over 2022-01-01 to 2024-12-31: 1,578,240
  rows per symbol**, being 1,096 x 1,440, **zero buckets dropped anywhere**,
  three-symbol total **4,734,720**, completeness **100.000%** on all three.
- **15 on-disk partitions, 15 files** — three symbols by five years — of which six
  are the sealed 2025 and 2026 files.
- **`open` is SYNTHESISED** from the carried-forward previous close and is dropped
  by every loader. This is why the haircut cannot be validated.
- Funding history available covers roughly **90 days against a three-year test
  window**, which is why the rate is an assumption.

### 12.5 THE REPOSITORY

- **101 commits**, 49 test modules, **1,280 tests passing.**
- `src/` carries `engine/` (signals, simulate, costs, sizing, portfolio,
  contracts, run, diagnostics), `risk/` (budget, exit_spec), `analysis/`,
  `timeframe/`, `folds/`, `sweep/`, `venue/`, `costs/`, `data/`, and
  **`firewall.py` at the top level, because the firewall crosses every
  subpackage.**
- **`README.md` at the repository root is STALE.** It describes the project as at
  the data-acquisition design stage with no strategy code, and names a 15-minute
  timeframe. **Both statements are long superseded** and the file has simply not
  been revised.

---

## 13. HOW TO ARGUE WELL HERE — THE TRAPS

**These are the misreadings the committed record explicitly anticipates. A second
reader who walks into one will be corrected by a document rather than by a
person.**

**1. DO NOT TREAT ADMISSIBILITY AS EVIDENCE OF EDGE.** Everything measured to date
establishes that the design **can be tested** — that it clears the cost floor,
produces enough signals, and is internally consistent between trigger and stop.
**It has shown nothing whatsoever about whether it works.** Every figure so far is
a statement about **bars**.

**2. DO NOT READ THE 97 TO 99% EXTREME-CLEARANCE RESULT AS SAFETY.** It
establishes that the stop clears the signal bar's **own** extreme. **It says
nothing about price revisiting that extreme on a LATER bar.** The thesis names
this misreading as one it exists partly to prevent.

**3. DO NOT ARGUE THAT LOWER COSTS LOWER THE REQUIRED WIN RATE.** They do not.
Breakeven is geometric in the reward-to-risk ratio alone. Costs act on the
**achievable** side by moving the target further away. §5.4.

**4. DO NOT OFFER "THESE ARE BIG BARS, THEREFORE X ABOUT A PERCENTAGE
THRESHOLD".** Report 21 refuted the premise: the trigger selects on **relative**
range, which is **scale-free and therefore nearly orthogonal to the ATR level** a
percentage floor compares against. BTC floor binding was 46.15% on signals against
46.21% on all bars — **a difference of 0.05 percentage points.** The thesis states
that any argument of that shape is unsound.

**5. DO NOT OFFER LEVERAGE AS A REASON NOT TO WIDEN THE FLOOR.** It points the
other way. §11.2.

**6. DO NOT READ A STABLE TRADE COUNT AS A STABLE OPPORTUNITY SET.** The budget
pins trade count nearly flat regardless of signal supply. §10.1 item 5.

**7. DO NOT COMPARE CANDIDATE COUNTS WITH TAKEN COUNTS.** They are different
populations and the record flags the confusion each time it could arise. **The
taken population under the current level cannot be computed at all**, because it
is a function of realised outcomes.

**8. DO NOT PROPOSE PATCHING A DEAD OR DYING DESIGN.** Kill condition (e) says in
advance that a time-exit dominance result is **refuted, not repaired**. The prior
hypothesis's closing record forbids patching it, and the current thesis is an
**inversion of the claim** rather than a parameter flip precisely to stay outside
that prohibition.

**9. DO NOT REACH FOR THE ORIGINAL BRIEF AS AUTHORITY.** It is non-normative by
its own §1, the frozen thesis governs unconditionally where they conflict, and the
consequence has been pre-stated so it cannot be claimed later. §5.3.

**10. DO NOT RESOLVE A CONTRADICTION YOU FIND. REPORT IT.** That is the rule, it
is the most-exercised rule in the project, and every logged instance records the
session as having done exactly that.

**11. DO NOT ASSUME A DOCUMENT'S FIGURE IS SOURCED.** At least one set of
figures — required floors of **1.530% and 1.561% for BTC and ETH and 1.971% and
2.030% for SOL** — is recorded in the Point 5 closing record as **supplied but
UNSOURCED**, appearing nowhere in `docs/` or `reports/`, with the instruction that
they must be derived from the implementation before being relied on.

**12. AND THE HIGHEST-VALUE MOVE: CHECK THE COMMIT ORDER.** Every claim this
project makes about what was known when is checkable in `git log`, and **the
project has repeatedly chosen to spend extra commits to make it so.** An argument
that a decision was reached backwards is answerable — or not — from the history,
and that is the intended way to attack any of it.

---

## 14. WHERE AN ARGUMENT IS ACTUALLY LIVE

**Closed questions are closed by commitment, and reopening one requires an
amendment that says it is doing so. These are the places where a second reader can
contribute something rather than relitigate.**

- **THE MAGNITUDE THRESHOLD IS NOW COMMITTED AND IS NO LONGER OPEN AS A
  QUESTION** — §8.5. **What remains arguable is its ANCHOR**, which the document
  records as a judgement rather than a derivation. It names the two alternatives
  and where each leads: the tick grid gives a tighter bar, the worst single
  position's 9.21% granularity drag gives a far looser one. **A reader who holds
  that modality should not order the test at all must then either reject the
  displacement budget at ten per cent or accept the funding treatment at 1.16 per
  cent, and naming which is how that reader argues a different threshold.** There
  is no third option.
- **THE VOLATILITY QUESTION — the freshest genuinely open item, and it has no
  owner.** Population B is now clipped rather than rejected, so **1,967
  candidates — 17.28% pooled and 38.13% of SOLUSDT — take a stop NARROWER than
  their own volatility implies.** Whether that is undesirable is a question about
  whether the geometry the thesis describes survives being truncated. **It is
  argued nowhere, no committed document takes a position, and the closing document
  explicitly declines to characterise it as unimportant.**
- **Kill condition (d)'s evaluation level. DISPOSED — pooled** — but the reasoning
  invites a stated objection and answers it: **pooling is also the more forgiving
  level, and a reader who holds the more forgiving level should not be chosen by
  the party it forgives is entitled to that objection.** The answer offered is the
  fold-schedule argument, which does not depend on thinness. **Whether that answer
  is sufficient is arguable.**
- **The risk-displacement budget of ten per cent.** It is **the project owner's
  stated judgement**, not a finding, and the source says so: **a reader who
  disagrees is disagreeing with a person's stated judgement, which is the correct
  thing to be disagreeing with, and is not being contradicted by evidence.** The
  document names two axes on which a different budget would be argued.
- **The uncertainty parameter's scope.** Argued from symmetry of ignorance. **What
  would overturn it is evidence that one term's estimate is materially better
  founded than the other's** — evidence of the kind that would let a reader say
  **how much** better founded — and no such evidence exists.
- **Whether the 53.6% detectable-edge bar is reachable at all** on a 1h intraday
  trigger. The thesis itself records that **nothing measured supports it, that the
  bar is high, and that archetype plausibility is not evidence.**
- **The aggregation rule's known false-negative cost.** Pre-accepted, and
  explicitly not grounds for re-running — but the reasoning is stated in the open
  and is arguable on its merits **before** a result exists.
- **The frozen-specification admission criterion's circularity.** An operational
  marker is owed and none has been invented. §6.
- **The population B result.** **More than a third of SOLUSDT's candidates ask for
  a stop the frozen cap forbids.** Report 37 drew no conclusion from it, being the
  first measurement of a quantity that was defined but never counted. **Step 3 then
  decided its disposition — clip, not reject — on the cost ground alone, and
  explicitly left the volatility question above unanswered.**

---

## 15. STATUS AT THE TIME OF WRITING

- **SUB-POINT 4.1c AND SUB-POINT 4.1 ARE CLOSED**, at commit `2a04e37`. **The next
  open item is Point 4's remaining agenda at §9(a) through (g), less what 4.1
  discharged**, and no committed document fixes a sub-point label beyond 4.1.
- **Defect ledger: 46.** **Errata index: 10 entries in fact against 9 in the frozen
  index's own text**, with the index routed to become a standalone artifact.
- **Test suite: 1,280 passing.** 101 commits on `main`.
- **Performance firewall: ARMED.** No outcome quantity exists in this repository
  for this thesis.
- **Holdout: SEALED AND UNSPENT, with the two disclosures at §2 attached to that
  statement permanently, in full, and not by reference.**

---

**This file summarises and binds nothing. Where it and a source document differ,
the source governs and the difference is a defect here.**
