# AMENDMENT 2 TO THE DIVERGENCE DISPOSITION — AND THE CLOSE OF STEP 2A

**Sub-point 4.0, step 2A, final document.** Preconditions for the validation
design.

## 1. WHAT THIS DOCUMENT IS, AND THAT IT CLOSES STEP 2A

**This amends both `docs/design/04_0_divergence_disposition.md` (commit
`1ff72634`) and `docs/design/04_0_divergence_disposition_amendment_1.md` (commit
`814608d2`), under their respective change-discipline sections.** Both require
that a change to any disposition be a new document with its own commit and an
explicit statement of what changed and why, never a silent edit. **This is that
document. Neither prior document is edited.**

**IT IS MADE BEFORE THE 4.0 PARAMETRIC DERIVATION IS RUN AND BEFORE ANY
PERFORMANCE FIGURE EXISTS FOR THIS THESIS.** The commit hash is the proof of the
order.

### 1.1 THE STOPPING RULE — A PRE-COMMITMENT

> **STEP 2A CLOSES ON THIS DOCUMENT'S COMMIT, REGARDLESS OF WHAT THIS DOCUMENT'S
> OWN VERIFICATION SURFACES.**

**Residual ambiguities found afterwards are carried into step 2B's opening as
logged context. They do not generate a further amendment.**

**THE RULE WAS AGREED BEFORE THIS DOCUMENT WAS WRITTEN**, by the project owner,
and is recorded here as part of the document it binds.

**THE REASON, PLAINLY:** three rounds on one governance document already exceeds
what its content warrants. **The marginal ambiguity a fourth round would catch is
smaller than the cost of the loop** — and the loop has its own cost, in attention
that step 2B and step 3 need.

> **A STOPPING RULE CHOSEN AFTER SEEING WHAT IT WOULD FORGIVE IS NOT A STOPPING
> RULE.** It is a decision to stop looking, made once the looking became
> uncomfortable. **That is why this one is recorded as having preceded the
> verification**, and why this section says so before any of the findings below
> appear.

### 1.2 PRECEDENCE, FOR A READER

- **On any point this document amends, this document governs.**
- **Otherwise, amendment 1 governs on the four points it amends.**
- **Otherwise, the base document governs.**

---

## 2. "THE FROZEN SPECIFICATION", DEFINED BY EXTENSION

### THE DEFECT

Amendment 1 §2's amended clause binds **"any change to the frozen
specification"** and **does not say which documents constitute it.** A reader
could take it as the thesis only, or as the thesis plus the design documents.
**A scope term inside a binding clause, left to the reader, is read as narrowly
as the reader needs it to be.**

### THE DEFINITION

**The frozen specification comprises, as at this commit, these documents in
full:**

- `docs/handoff/22_point_1_thesis.md`
- `docs/handoff/22a_point_1_thesis_amendment_1.md`
- `docs/design/05_aggregate_risk_budget.md`
- `docs/design/05a_aggregate_risk_budget_amendment_1.md`
- `docs/design/05b_aggregate_risk_budget_amendment_2.md`
- `docs/design/06_exit_resolution_spec.md`
- `docs/design/06a_exit_resolution_spec_amendment_1.md`
- `docs/design/00_standing_brief.md`, as amended by
  `docs/design/04_0_divergence_disposition.md` §3
- `docs/design/04_0_divergence_disposition.md`
- `docs/design/04_0_divergence_disposition_amendment_1.md`
- **this document**

### THE LIST IS OPEN FORWARD

> **ANY DOCUMENT SUBSEQUENTLY COMMITTED AS A PRE-REGISTRATION UNDER THIS
> PROJECT'S DISCIPLINE JOINS THE FROZEN SPECIFICATION ON ITS COMMIT.**

The list above is **the membership as at this commit, not a closed set.** The
documents committed in **step 2B** and **step 3** will join it. **A reader who
finds a pre-registration committed after this document must treat it as a member
without waiting for this list to be reissued** — and this document is not
reissued, because §10 forbids it.

### WHAT IS NOT IN IT

- **Reports under `docs/handoff/` that record measurements rather than
  pre-register rules are EVIDENCE, NOT SPECIFICATION**, and are not members. They
  are cited, relied on, and corrected by erratum; they do not bind.
- **Source code under `src/` is an IMPLEMENTATION of the specification and is not
  itself the specification.** Where code and specification disagree, **that is a
  defect to be reported, not a change to the specification.** Code cannot amend a
  pre-registration by diverging from it.

---

## 3. "WRITEUP", EXTENDED TO COVER ABSENCE AND REFUSAL

### THE DEFECT

Amendment 1 §3 defines a writeup as a communication that **states or
characterises a result computed on the holdout window.** As written, that does
not obviously reach:

- a statement that **no result was computed**;
- a statement that **the holdout has not been opened**;
- a **refusal** to state a result.

> **THOSE ARE AMONG THE CASES WHERE A READER MOST NEEDS THE DISCLOSURE, BECAUSE
> EACH IS A CLAIM ABOUT THE SEAL.**

### THE EXTENSION

> **THE DISCLOSURE OBLIGATION ATTACHES EQUALLY TO ANY COMMUNICATION THAT STATES,
> CHARACTERISES, OR DECLINES TO STATE A RESULT COMPUTED ON THE HOLDOUT WINDOW,
> AND TO ANY COMMUNICATION ASSERTING THAT NO SUCH RESULT EXISTS, THAT THE HOLDOUT
> HAS NOT BEEN OPENED, OR THAT THE SEAL IS INTACT.**

**THE REASON:** each of those is **itself a claim about the seal**, and **a reader
cannot assess a claim about the seal without knowing what has touched it.** An
assurance that the seal is intact, offered without the disclosure of what has
touched the sealed files, is precisely the assurance a reader has no way to
check.

**AMENDMENT 1 §3's PROVISIONS ON MEDIUM AND LENGTH CONTINUE TO APPLY IN FULL.**
This extension is not narrowed to written communications and does not exempt
short ones.

---

## 4. THE SELF-REFERENCE CLAUSE

### THE PROBLEM

Amendment 1 §2's amended clause makes **any change to the frozen specification an
unregistered modification until pre-registered**, including **changing the
conditions under which any rule applies.**

`docs/handoff/31_point_5_closing.md` §9(c) requires Point 4 to **restate the
thesis's kill conditions for the capped, path-dependent population.** **Read
literally, the clause makes Point 4's own required deliverable an unregistered
modification.**

### THE CLAUSE

> **A DOCUMENT WHOSE FUNCTION IS TO PRE-REGISTER A CHANGE IS NOT A VIOLATION OF
> THE REQUIREMENT TO PRE-REGISTER THAT CHANGE, PROVIDED THE PRE-REGISTRATION IS
> COMMITTED BEFORE THE THING IT REGISTERS IS MEASURED, INSPECTED OR RELIED
> UPON.**

### AND IT IS NARROW

**THE CLAUSE COVERS THE ORDER OF COMMITMENT AND NOTHING ELSE.** A
pre-registration that precedes what it registers is valid; **one written after is
not, whatever document it appears in.**

**IT DOES NOT EXEMPT POINT 4's DOCUMENTS FROM PRE-REGISTRATION DISCIPLINE
GENERALLY**, and it creates **no exemption for metric calibration, threshold
selection, or any other act performed inside a pre-registration document.**
Performing such an act inside a document labelled a pre-registration does not
make it pre-registered; **only committing it before the thing it governs is
looked at does that.**

> **THE CLAUSE CANNOT BE READ AS BLESSING WHATEVER A POINT 4 DOCUMENT HAPPENS TO
> CONTAIN.** It says when a pre-registration counts. It says nothing about what
> may be put inside one.

---

## 5. THE DEFECT LEDGER, RECONCILED

### WHAT THE COMMITTED DOCUMENTS SAY — READ BEFORE THIS SECTION WAS WRITTEN

`docs/handoff/31_point_5_closing.md` §7.1 states the running total as **32**, and
gives its composition as **7** instances tabulated in the Point 4 closing record
§3.4, **9** numbered in the Point 1 reopened closing record §4 — a subtotal of
**16** before Point 5 — and **16** enumerated in that record's own §7.2.

**§7.2 WAS READ AND ITS ENUMERATION CONFIRMED: sixteen instances, numbered (17)
through (32) contiguously.** The committed total matches its stated composition,
and **no discrepancy was found.**

### THE PROBLEM

Amendment 1 §2 logged instance **(34)** while recording that the prior running
total of **33** supplied to it **was unsourced in the repository**, and that the
last committed total was **32**. **The committed ledger therefore reads 32, then
a gap at (33), then (34).**

**Amendment 1 correctly declined to reconcile this**, because reconciling it was
outside what that document was authorised to do. **This section reconciles it.**

### THE THREE MISSING INSTANCES

**(33) A PROMPT REQUIRING VERBATIM TRANSCRIPTION OF A SOURCE TEXT WHILE
SEPARATELY REQUIRING THAT A PHRASE CONTAINED IN THAT TEXT BE ABSENT FROM THE
OUTPUT.** The two requirements are **unsatisfiable together**. It arose in the
instruction that produced `docs/design/00_standing_brief.md`; **the implementing
session reported the contradiction rather than resolving it, and chose fidelity
to the source.** Sub-class: **internal contradiction between a prompt's own
constraints and its requirements**, the sub-class
`docs/handoff/31_point_5_closing.md` §7.2 records as instances **(23) to (26)**.

**(35) A PROMPT REQUIRING A RUNNING TOTAL TO BE STATED AS 33 WHILE SEPARATELY
REQUIRING EVERY FIGURE TO CARRY A VERIFIED CITATION TO A COMMITTED DOCUMENT, WHEN
NO COMMITTED DOCUMENT STATES 33.** It arose in the instruction that produced
`docs/design/04_0_divergence_disposition_amendment_1.md`; **the implementing
session reported the contradiction rather than resolving it.** **Same sub-class
as (33).**

**(36) THE CONFLATION OF TWO DISTINCT QUANTITIES:** the one-settlement funding
overcharge under the adopted reading, and the magnitude of the breach for which
`docs/design/06_exit_resolution_spec.md` §5.4 rejected the realised-cash-flow
treatment. **Amendment 1 §5.1 establishes that document 06 §5.4 states no
numeral**, and that the **0.0067R** figure in
`docs/design/06a_exit_resolution_spec_amendment_1.md` §2.3 **denominates the
adopted reading's overcharge.** The conflation appears in
`docs/handoff/31_point_5_closing.md` §5.3, was carried forward into the
instruction that produced the base document, and thence into that document's §4.

> **(36) IS ONE INSTANCE, NOT THREE.** The counting method
> `docs/handoff/31_point_5_closing.md` §7.1 states is **one per distinct defect,
> not one per document carrying it.** The conflation is one defect that
> propagated through three documents.

### THE RECONCILED TOTAL

**32 + 4 = 36.**

That is the committed total established by the read above, plus instances **(33)
through (36)** — three logged here and **(34)** already logged in amendment 1 §2.

**No earlier instance is renumbered or recounted.**

**THIS RECONCILIATION SUPERSEDES AMENDMENT 1 §5.4's RECORDING OF 33 AS SUPPLIED
BUT UNSOURCED.** **33 is now a committed instance number with a stated defect
behind it**, and the ledger is contiguous from (1) to (36).

---

## 6. ERRATUM AGAINST `docs/handoff/31_point_5_closing.md` §5.3

### THE ERRATUM

**That section attributes BOTH the rejection of the realised-cash-flow funding
treatment AND the numeral "roughly 0.0067R" to
`docs/design/06_exit_resolution_spec.md` §5.4.**

**Amendment 1 §5.1 established that the numeral is not in that section**, and
that where it does appear —
`docs/design/06a_exit_resolution_spec_amendment_1.md` §2.3 — **it denominates a
different quantity**, the one-settlement overcharge under the adopted reading.

### ERRATA ARE LOGGED, NOT PATCHED

**`docs/handoff/31_point_5_closing.md` IS FROZEN AND IS NOT EDITED.** **This entry
is the correction of record.**

### WHETHER ANYTHING OPERATIVE CHANGES

**THE CLOSING RECORD §5.3's ARGUMENT SURVIVES.** That argument is that two
decisions run in opposite directions on the same principle and that **sub-point
4.1 owes a criterion reconciling them.** Nothing in the correction touches it.

**WHAT CHANGES IS HOW THE ARGUMENT IS CORRECTLY STATED**, following amendment 1
§5.3:

- **Document 06 §5.4's rejection is CATEGORICAL.** It refuses the treatment on the
  ground that it breaches the risk unit at all, and **states no magnitude.**
- **The fill-price term of `docs/handoff/30_point_5_3_4_portfolio.md` §7.3 was
  accepted on MAGNITUDE grounds** — at most **0.0033 USDT** across the six cells
  measured, **under 0.017% of a risk unit**.

> **THE TWO DECISIONS DIFFER IN KIND, NOT IN THRESHOLD.** One breach was refused
> outright with no magnitude named; a second was accepted because its magnitude
> is small. **There is no stated criterion reconciling a categorical refusal with
> a magnitude-based acceptance, and 4.1 owes exactly that.**

**NO THRESHOLD IS SET HERE AND NO MAGNITUDE IS STATED FOR THE REJECTED BREACH.**

---

## 7. THE STANDING DRAFTING RULE

> **A SCOPE TERM INSIDE A BINDING CLAUSE IS DEFINED EITHER BY EXTENSION — AN
> EXPLICIT LIST OF DOCUMENTS, PATHS OR CASES — OR BY A STATED PRINCIPLE FOLLOWED
> BY AN EXPLICIT "INCLUDING WITHOUT LIMITATION" ILLUSTRATION. IT IS NEVER DEFINED
> BY EXAMPLE ALONE.**

**Adopted as standing for every subsequent document in this project.**

### THE EVIDENCE, FROM THIS SUB-POINT'S OWN RECORD

- **Instance (34)** was **an enumeration standing in for a principle** — three
  named kinds of addition, where the commitment needed to reach every change.
- **The undefined "frozen specification"**, corrected in §2 above, was **a scope
  term left to the reader.**
- **The undefined "writeup"**, corrected by amendment 1 §3, was **the same.**

**THREE INSTANCES OF ONE FAILURE MODE IN THREE CONSECUTIVE DOCUMENTS.** That is
not a run of bad luck; it is a drafting habit, and it is named here so that it
stops being one.

### WHY IT MATTERS SPECIFICALLY FOR PRE-COMMITMENTS

> **A CLAUSE WRITTEN TO BE INCONVENIENT LATER IS READ LATER BY SOMEONE FOR WHOM
> IT IS INCONVENIENT. A SCOPE STATED BY EXAMPLE IS READ AS NARROWLY AS THE
> EXAMPLES PERMIT.**

**The rule exists so that the reading does not depend on the reader's
incentives.** Every other guard in this project — the firewall, the seal, the
commit-before-measurement discipline — is built on the same principle: **make the
constraint independent of the good faith of whoever meets it.**

---

## 8. ROUTING THE UNSOURCED MAGNITUDE TO STEP 3

### THE ITEM

**Amendment 1 §5.1 records the magnitude of `docs/design/06_exit_resolution_spec.md`
§5.4's rejected breach as UNSOURCED in the sections examined**, under the
disposition `docs/handoff/31_point_5_closing.md` §5.1 applies to the required
stop floors.

### THE ROUTING

> **THAT DISPOSITION IS A HOLDING POSITION, NOT A RESTING PLACE.**

The quantity is **a determinate function of the funding rate, the settlement
count and the stop width** — computable from **the same cost algebra step 3 works
in.**

**IT IS ADDED TO STEP 3's DERIVATION AGENDA**, to be **derived from the
implementation alongside the parametric stop-floor derivation**, and **is not to
remain an open unknown through Point 4.**

### IT IS NOT DERIVED HERE

**NO VALUE FOR IT IS STATED, ESTIMATED OR BOUNDED IN THIS DOCUMENT**, and nothing
here states how the rejected treatment would have charged.

> **STATING A VALUE HERE FROM THE COST ALGEBRA, WITHOUT RUNNING IT AGAINST THE
> IMPLEMENTATION, IS THE PROJECT'S RECURRING DEFECT CLASS** — a number written
> from a mental model of a quantity rather than from its implementation. **This
> section exists to route the quantity, not to answer it**, and answering it here
> would be instance (37).

### WHY IT MATTERS

**Sub-point 4.1 owes a criterion reconciling a categorical refusal with a
magnitude-based acceptance (§6).** **That criterion is easier to state honestly
when both magnitudes are known, and at present only one of them is.** A criterion
written against one known magnitude and one unknown one is a criterion fitted to
the half of the evidence that happens to be visible.

---

## 9. WHAT IS NOT AMENDED, AND STEP 2A's CLOSING STATE

**THE FIVE DISPOSITIONS OF THE BASE DOCUMENT ARE UNCHANGED.** The frozen thesis
still governs the indicator question unconditionally; the holding-horizon premise
amendment stands as made; the 1% question is still routed to 4.1 with no epsilon
set; the timeframe candidate set is still logged with no action; regime-aware
validation is still recorded as unfinished work rather than a conflict.

**AMENDMENT 1's FOUR AMENDMENTS ARE UNCHANGED, EXCEPT** that §5 above supersedes
its §5.4 on the ledger total.

### STEP 2A's CLOSING STATE

**The three documents comprising step 2A, and what each governs:**

- **`docs/design/04_0_divergence_disposition.md`, commit `1ff72634`** — the five
  dispositions, the holding-horizon premise amendment, and the extension of the
  holdout disclosure requirement to the manifest-footer channel. **Governs
  wherever the two amendments are silent.**
- **`docs/design/04_0_divergence_disposition_amendment_1.md`, commit `814608d2`**
  — the pre-registration scope restated as a principle, the definition of
  "writeup", the load-bearing-horizon clarification, and the two verified
  citations. **Governs on those four points over the base document.**
- **This document** — the definition of "the frozen specification", the extension
  of "writeup" to absence and refusal, the self-reference clause, the ledger
  reconciliation, the §5.3 erratum, the standing drafting rule, and the routing of
  the unsourced magnitude. **Governs on those points over both.**

**THE TWO ITEMS STEP 2A ROUTES FORWARD, NEITHER OF WHICH IS SET ANYWHERE IN STEP
2A:**

- **The magnitude threshold owed to sub-point 4.1** — at what magnitude a breach
  of the after-costs risk rule stops being tolerable, stated against a systematic
  one-directional term, and reconciling a categorical refusal with a
  magnitude-based acceptance.
- **The complexity criterion owed to sub-point 4.5** — what constitutes
  unjustified complexity, against which any change to the frozen specification
  would be judged.

**And one item routed to step 3:** the magnitude of document 06 §5.4's rejected
breach (§8).

> ### STEP 2A IS CLOSED.

---

## 10. CHANGE DISCIPLINE

**A CHANGE TO ANY DISPOSITION IN STEP 2A AFTER THIS COMMIT IS NOT MADE BY
AMENDMENT.** It is **carried into step 2B's opening as logged context**, per the
stopping rule in §1.1.

**A SILENT EDIT TO ANY OF THE THREE STEP 2A DOCUMENTS IS A CONTAMINATION EVENT.**
The stopping rule ends the amendment chain; **it does not licence editing what
the chain produced.** The two are opposite: the chain stops precisely so that the
three documents can be relied on as they stand.

---

**Committed alone, before the 4.0 parametric derivation and before any
performance figure exists for this thesis. Two scope terms defined, one clause
added, the ledger reconciled to a contiguous count, one erratum logged, one
drafting rule adopted as standing, and one unsourced magnitude routed to step 3.
No criterion is created, no threshold is set, and no disposition is reversed.
Step 2A is closed.**
