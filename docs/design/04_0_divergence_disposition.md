# DIVERGENCE DISPOSITION — PRE-REGISTERED

**Sub-point 4.0, step 2A.** Preconditions for the validation design.

## 1. WHAT THIS DOCUMENT IS

**THIS IS A PRE-REGISTRATION AND IT IS FROZEN ON COMMIT.** It is made **before**
the 4.0 parametric derivation is run and **before any performance figure exists
for this thesis.** The commit hash is the proof of the order.

**IT DOES THREE THINGS AND NOTHING ELSE:**

1. **It disposes of five divergences** between the standing project brief
   (`docs/design/00_standing_brief.md`, committed at `b8f4844f`) and the frozen
   thesis and design documents. Transcribing the brief surfaced them; until now
   they were recorded nowhere.
2. **It amends one premise of the standing brief** — the holding horizon, §3 —
   under that brief's own §4, which requires that a change to any premise be a
   new document with its own commit and an explicit statement of what changed
   and why, **never a silent edit** to the brief itself. **This document is that
   new document.**
3. **It extends a standing disclosure requirement** to cover a second channel
   into the sealed window (§7).

> **WHERE THIS DOCUMENT AND ANY FROZEN DOCUMENT DISAGREE ON A MATTER OF FACT,
> THE FROZEN DOCUMENT WINS.** This document's authority extends **only to the
> dispositions it makes** — which divergence is settled, which is routed, which
> is logged, and the one premise amended. It restates facts from frozen
> documents for the reader's convenience and every such restatement is cited; a
> restatement is not an authority.

**WHY IT EXISTS NOW RATHER THAN LATER.** The 4.0 derivation and everything after
it must run against **a stated thesis**, not against two committed documents that
disagree with each other. A divergence that is still open when a number arrives
becomes a choice made in the presence of that number.

**NOTHING HERE IS COMPUTED, MEASURED OR DERIVED.** Every figure below is already
committed in a document named in this section or in the section citing it, and
carries that citation. **No new numeric criterion, threshold or penalty is
created by this document**, and two are explicitly withheld and routed (§2, §4).

---

## 2. DIVERGENCE 1 — INDICATORS. **DISPOSED.**

### THE PREMISE

`docs/design/00_standing_brief.md` §2 asks for **3 to 4 indicators**, proposed
with justification — *"ideally a trend or momentum indicator, an oscillator, and
at least one volume indicator"* — and records the project owner's stated position
that **volume analysis is underrated and should be central rather than
decorative**, and that the indicators must combine into one coherent thesis
rather than a stack.

### THE CONFLICT — THREE AGAINST ONE PREMISE

`docs/handoff/22_point_1_thesis.md` specifies:

- **§3.1: no oscillator.** *"No RSI, no stochastic, no oscillator of any kind is
  in this specification."*
- **§3.2: no volume term.** *"No RVOL, no volume gate, no volume confirmation
  term."* The section is titled a **deliberate departure from the original
  brief** and argues the case at length.
- **A single Donchian wick-and-reject construct**, not a combination of three or
  four indicators.

### DISPOSITION

> **THE FROZEN THESIS GOVERNS UNCONDITIONALLY.**

The brief's indicator wording is recorded as **the project owner's stated
preference at the outset**. The thesis's parsimony is **an argued and committed
design decision, made later**, and it stands. **The brief is non-normative by its
own §1** — it says so of itself — and it **does not reopen the thesis.**

### THE CONSEQUENCE, STATED SO IT CANNOT BE CLAIMED LATER

> **ANY FUTURE ADDITION OF A VOLUME TERM, AN OSCILLATOR, OR ANY FURTHER
> INDICATOR IS A NEW PARAMETER ENTERING A FROZEN SPECIFICATION.**

- **It is not a return to the brief.**
- **It is not exempt from pre-registration on the ground that the brief asked for
  it.** "The original brief wanted volume" is **not** a justification, and this
  paragraph exists so that it cannot be offered as one.
- **It must be justified on its own terms**, under the same discipline as any
  other parameter addition.

**THE CRITERION BY WHICH SUCH AN ADDITION WOULD BE JUDGED DOES NOT EXIST YET.**
What constitutes unjustified complexity is **owed to sub-point 4.5** — parameter
sensitivity and the curve-fitting criterion — and is **deliberately not named
here.** No penalty, no threshold and no metric for it is invented in this
document, because inventing one here would be choosing it in the absence of the
analysis 4.5 exists to perform.

---

## 3. DIVERGENCE 2 — HOLDING HORIZON. **PREMISE AMENDED.**

> **THIS SECTION IS AN AMENDMENT TO `docs/design/00_standing_brief.md` §2, MADE
> UNDER THAT FILE'S §4.** That section requires a change to any premise to be a
> new document with its own commit and an explicit statement of what changed and
> why, never a silent edit to the brief. **This is that document and this is that
> statement.** The brief itself is not touched.

### WHAT THE PREMISE SAID

*"**Style:** intraday. The timeframe is to be chosen jointly; 5m, 15m and 1h are
named as candidates, with tradeoffs to be weighed."* — brief §2.

### WHAT IS ACTUALLY THE CASE

The frozen time exit (`docs/handoff/22_point_1_thesis.md` §5.3) closes a position
at **the third funding settlement after entry**.
`docs/handoff/24_point_5_1_exposure.md` §5 measured hold duration across **all
11,384 candidate positions** at **minimum 17h, maximum 24h, mean 20.51h, median
21h**.

> **EFFECTIVELY EVERY POSITION IS HELD OVERNIGHT, AND EVERY POSITION CROSSES
> MULTIPLE FUNDING SETTLEMENTS.**

### THE AMENDED PREMISE

**The strategy is a multi-settlement short-swing strategy on 1h bars, with holds
in the 16 to 24 hour band (`22_point_1_thesis.md` §5.3), not a strict
single-session intraday strategy.**

**THE 1h BAR TIMEFRAME IS UNCHANGED** and remains inside the original candidate
set. Only the description of the holding horizon changes.

### WHY AN AMENDMENT RATHER THAN A RECORDED DEPARTURE

**THE MULTI-SETTLEMENT EXPOSURE IS NOT INCIDENTAL TO THE DESIGN. IT IS
LOAD-BEARING.** It is:

- the reason **funding is provisioned at three settlements**
  (`docs/design/06_exit_resolution_spec.md` §6, and
  `docs/design/06a_exit_resolution_spec_amendment_1.md` E7.1);
- the reason **a funding term appears in the sizing denominator and in the target
  cost bracket** (`06a` E7.2);
- and therefore the reason **a substantial part of the cost structure exists at
  all.**

**A premise that describes the strategy as intraday misdescribes the mechanism
the cost model is built around.** A departure logged against the brief would
leave the misdescription standing as the project's stated premise; an amendment
replaces it. **That is the difference, and it is why this one is amended and the
other four are not.**

### WHAT DOES NOT CHANGE

> **NO FROZEN DERIVATION DEPENDS ON THE WORD "INTRADAY".**

The only downstream use of the style premise was **the timeframe candidate set**,
and the selected **1h** timeframe satisfies **both the original and the amended
wording**. **This amendment therefore changes no frozen document's premises and
requires no re-derivation.**

**CONTRAST THIS WITH THE DRAWDOWN TOLERANCE.** That premise **is** derived from —
`docs/design/05_aggregate_risk_budget.md` §2 reasons from it to the book-level
open risk limit — and it is **NOT amended here, or anywhere in this document.**
The distinction between an amendable premise and a load-bearing one is exactly
whether a frozen derivation stands on it.

---

## 4. DIVERGENCE 3 — THE 1% RISK RULE AGAINST A KNOWN SYSTEMATIC TERM. **ROUTED TO 4.1.**

### THE PREMISE

*"**Risk per trade:** never more than 1% (that is, $20), enforced after fees and
estimated slippage."* — brief §2.

### THE FACT

`docs/handoff/30_point_5_3_4_portfolio.md` §7.3 and
`docs/handoff/31_point_5_closing.md` §5.3 record that `costs.position_size`
charges the exit fee **on the stop level** while the actual fill sits **a haircut
away from it**, and that **for short positions this places the realised loss
beyond one risk unit** — at most **0.0033 USDT** across the **six cells** measured,
**under 0.017% of a risk unit** (`30_point_5_3_4_portfolio.md` §7.3).

### THE CHARACTERISATION, STATED PRECISELY, BECAUSE IT GOVERNS WHAT 4.1 MUST JUSTIFY

**(1) THE TERM IS SYSTEMATIC AND DIRECTION-DEPENDENT. IT IS NOT NOISE.** It is
**signed**; it **breaches in the same direction on every short stop-out**; and it
**does not average out across trades**.

> **A TOLERANCE JUSTIFIED ON THE GROUND THAT A QUANTITY IS ZERO-MEAN DOES NOT
> APPLY TO IT.** Any argument of that shape must be refused here on inspection,
> because the premise it rests on is false of this term.

**(2) IT MUST NOT BE CONFLATED WITH QUANTITY-GRANULARITY FLOORING, WHICH RUNS THE
OPPOSITE WAY.** Flooring places realised risk **BELOW** nominal:
`docs/handoff/30_point_5_3_4_portfolio.md` §6.1 measured realised risk across the
**6,021 taken positions** ranging **18.3392 to 20.0000**, **never above
20.0000**.

> **FLOORING CAN NEVER BREACH THE PREMISE. THE FILL-PRICE TERM IS THE ONLY
> MECHANISM IDENTIFIED THAT CAN.** The two are frequently discussed together
> because both concern the gap between nominal and realised risk. **They have
> opposite signs and only one of them is a breach.**

### DISPOSITION — NOT DISPOSED HERE

**NO EPSILON IS SET IN THIS DOCUMENT.** No magnitude threshold is stated, implied
or bounded here.

**SUB-POINT 4.1 OWES A STATED MAGNITUDE THRESHOLD**, answering:

> **AT WHAT MAGNITUDE DOES A BREACH OF THE AFTER-COSTS RISK RULE STOP BEING
> TOLERABLE?**

**IT MUST BE STATED AGAINST A SYSTEMATIC ONE-DIRECTIONAL TERM**, per (1) above.

**AND IT MUST RECONCILE WITH A DECISION THAT ALREADY RAN THE OTHER WAY.**
`docs/design/06_exit_resolution_spec.md` §5.4 **REJECTED** a different funding
treatment — charging funding as a realised cash flow per settlement actually
crossed — **specifically because "it lets a stop-out return worse than −1.0R"**.
The magnitude at stake there is stated as **roughly 0.0067R** in
`docs/design/06a_exit_resolution_spec_amendment_1.md` §2.3, and
`docs/handoff/31_point_5_closing.md` §8, erratum 1, logs the corrected figure as
**0.00589R** as a share of a realised risk unit. **Either figure is larger than
the term accepted in §7.3.**

> **TWO DECISIONS CURRENTLY RUN IN OPPOSITE DIRECTIONS ON THE SAME PRINCIPLE,
> WITH NO STATED CRITERION BETWEEN THEM.** One breach was rejected as
> intolerable; a smaller one was accepted on magnitude grounds. **That may well
> be correct — a threshold between them would make both decisions consistent —
> but no such threshold has been stated, so at present the two rest on intuition
> rather than on a criterion. 4.1 owes the criterion.**

---

## 5. DIVERGENCE 4 — THE TIMEFRAME CANDIDATE SET. **LOGGED, NO ACTION.**

The premise names **5m, 15m and 1h** as candidates (brief §2). The frozen
selection rule evaluated **5m, 15m, 1h, 4h and 1d** (`src/timeframe/resample.py`,
`TIMEFRAME_ORDER`) — **two candidates outside the premise's set**, of which **1d
is not intraday on any reading**.

**THE SELECTED TIMEFRAME, 1h, IS INSIDE THE PREMISE'S SET.** No selection was
contaminated by the widening and **nothing requires re-derivation.**

**Logged for completeness. No action follows.**

---

## 6. DIVERGENCE 5 — REGIME-AWARE VALIDATION. **NOT A DIVERGENCE.**

The premise requires regime characterisation in measurable terms, testing across
multiple historical windows resembling the current regime, testing across
different regimes to find where the strategy breaks, walk-forward analysis, a
strict out-of-sample holdout, and parameter-sensitivity checks (brief §2).

**NONE OF THIS IS SATISFIED BY ANY COMMITTED DOCUMENT, BECAUSE THE VALIDATION
DESIGN DOES NOT EXIST.** It is **Point 4**, which is **open and blocking**.

> **THIS IS UNFINISHED WORK, NOT A CONFLICT BETWEEN COMMITTED ARTIFACTS.** No
> frozen document contradicts the premise; the document that would satisfy it has
> not been written.

**It is recorded here so that all five divergences carry a disposition and none
is left implicit.** A divergence with no entry is indistinguishable from one
nobody noticed.

---

## 7. EXTENSION OF THE HOLDOUT DISCLOSURE REQUIREMENT

### THE EXISTING REQUIREMENT

`docs/handoff/31_point_5_closing.md` §6.4 requires that **any writeup of holdout
results carry, in full and not by reference**, the disclosure of the 5.3.3
breach: **what was opened, that no sealed value reached anyone, the adjudication
and its reasoning.**

### THE SECOND CHANNEL, NOT COVERED BY §6.4

The same closing record's **§8, erratum 4** records that
`structural_pass.check_manifest` and `tests/test_manifest_integrity.py` called
`pq.read_metadata` on **all 26 manifest outputs, six of which are sealed 1m
partitions**, and accessed **`.num_rows`, which is a completeness figure**; and
that **`data/derived/_manifest.json` records those counts in a file on disk.**

**§6.4 does not cover it.**

### THE ASYMMETRY, AND IT RUNS THE WRONG WAY

> **THE §6 BREACH LEFT NOTHING PERSISTENT ON DISK. THIS CHANNEL LEFT AN ARTIFACT
> ON DISK AND RAN ON EVERY TEST INVOCATION, OVER A LONGER PERIOD.**
>
> **THE CHANNEL THAT PERSISTED IS THE ONE NOT CURRENTLY ATTACHED TO THE
> PERMANENT DISCLOSURE REQUIREMENT.**

That is the wrong way round, and it is the reason this extension is made now
rather than left to whoever writes the holdout result.

### THE EXTENSION, NOW BINDING

**ANY WRITEUP OF HOLDOUT RESULTS MUST CARRY BOTH DISCLOSURES IN FULL.**

The second must state:

- **what was accessed: row counts only** — **not** the parquet footer's
  per-column minimum and maximum statistics, **which would carry price
  information**;
- **that row counts of a complete minute layer are calendar arithmetic and carry
  no price information**;
- **that the counts are recorded in `data/derived/_manifest.json`**;
- **that the channel was closed at sub-point 5.3.3.**

### THE PRINCIPLE

> **THE READER OF A HOLDOUT RESULT IS ENTITLED TO ASSESS THE SEAL, AND THAT
> ENTITLEMENT DOES NOT PERMIT THE PROJECT TO PRE-SELECT WHICH TOUCHES OF THE
> SEALED FILES THE READER IS TOLD ABOUT.**

A disclosure regime that discloses the touch someone happened to write a report
about, and omits the one that ran quietly on every test invocation, is a regime
that reports what was noticed rather than what happened. **Both are disclosed, in
full, or the seal cannot be assessed by anyone but the project itself.**

---

## 8. CHANGE DISCIPLINE

**A CHANGE TO ANY DISPOSITION IN THIS DOCUMENT IS A NEW DOCUMENT WITH ITS OWN
COMMIT AND AN EXPLICIT STATEMENT OF WHAT CHANGED AND WHY — NEVER A SILENT EDIT.**

**A SILENT EDIT IS A CONTAMINATION EVENT.**

This applies with particular force to §2's consequence and §4's routing, because
both are commitments **against** a future argument: §2 forecloses "the brief asked
for volume" as a justification, and §4 forecloses a zero-mean tolerance argument
and refuses to set the threshold early. **A pre-commitment that can be edited
when it becomes inconvenient is not a pre-commitment**, and both were written to
be inconvenient later.

---

**Committed alone, before the 4.0 parametric derivation and before any
performance figure exists for this thesis. Five divergences disposed: one
governed by the frozen thesis, one premise amended, one routed to 4.1, one
logged, one recorded as unfinished work. One disclosure requirement extended to a
second channel. No figure is computed, no criterion is created, and two are
deliberately withheld.**
