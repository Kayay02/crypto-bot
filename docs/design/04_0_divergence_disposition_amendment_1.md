# AMENDMENT 1 TO THE DIVERGENCE DISPOSITION

**Sub-point 4.0, step 2A.** Preconditions for the validation design.

## 1. WHAT THIS DOCUMENT IS

**This amends `docs/design/04_0_divergence_disposition.md`, committed at
`1ff72634`, under that document's §8**, which requires that a change to any
disposition in it be a new document with its own commit and an explicit
statement of what changed and why, **never a silent edit.** **This is that new
document, and the base document is not edited.**

**IT IS MADE BEFORE THE 4.0 PARAMETRIC DERIVATION IS RUN AND BEFORE ANY
PERFORMANCE FIGURE EXISTS FOR THIS THESIS.** The commit hash is the proof of the
order.

**IT MAKES FOUR AMENDMENTS, EACH STATING WHAT CHANGED AND WHY:**

1. **§2's consequence, restated as a principle** rather than an enumeration.
2. **§7's "writeup", defined** — the broad reading, made explicit.
3. **§3's two true statements, reconciled** by a clarification.
4. **Two citations, verified** — one correct, one carrying a defect the check
   found and the instruction did not anticipate.

> **WHERE THIS DOCUMENT AND THE BASE DOCUMENT DIFFER, THIS DOCUMENT GOVERNS ON
> THE FOUR POINTS IT AMENDS, AND THE BASE DOCUMENT GOVERNS ON EVERYTHING ELSE.**

**NOTHING HERE IS COMPUTED, MEASURED OR DERIVED.** Every figure is already
committed and carries a citation verified against the file, with one exception
that is named as such in §5.4.

---

## 2. AMENDMENT 1 — §2's CONSEQUENCE, RESTATED AS A PRINCIPLE

### WHAT THE BASE DOCUMENT SAYS

§2's consequence reads: **"any future addition of a volume term, an oscillator,
or any further indicator is a NEW parameter entering a frozen specification"**,
and it forecloses **"the original brief wanted volume"** as a justification.

### THE DEFECT

**THE CLAUSE IS AN ENUMERATION.** Its force is a commitment against a future
argument, but **as written it covers only additions of the three kinds named.**

**A CHANGE TO AN EXISTING ELEMENT OF THE FROZEN SPECIFICATION FALLS OUTSIDE THE
ENUMERATION WHILE FALLING SQUARELY INSIDE THE PRINCIPLE.** The Donchian lookback
of **10** (`docs/handoff/22_point_1_thesis.md` §4); the wick-and-reject construct
itself (§4); the **2.25** ATR multiplier and the **1.50%** stop floor (§5.1); the
**1:1.5** reward-to-risk (§5.2); the **n = 3** settlement time exit (§5.3); or
the addition of a session filter, a regime filter or any other gating term —
**none of these is "an indicator", and every one of them is a change to a frozen
specification.**

> **A FORECLOSURE WITH A GAP IS ROUTED AROUND WITHOUT ANYONE NEEDING TO ACT IN
> BAD FAITH, BECAUSE THE READER FOLLOWS WHAT IS WRITTEN.** The failure mode is
> not deception; it is a reader correctly observing that the clause does not
> reach the case in front of them.

### THE AMENDED CLAUSE

**This replaces the enumerated one:**

> **ANY CHANGE TO THE FROZEN SPECIFICATION IS AN UNREGISTERED MODIFICATION UNTIL
> IT IS PRE-REGISTERED.** This covers, **without being limited to**: adding an
> indicator, filter, gate or term of any kind; removing one; changing the value
> of any parameter; changing the definition of any rule; and changing the
> conditions under which any rule applies. **It applies whether the change is
> presented as an addition, a correction, a simplification, a clarification or a
> return to an earlier intention.**
>
> **No such change is exempt on the ground that the standing brief asked for it.
> No such change is exempt on the ground that it makes the specification
> simpler.**
>
> **Every such change requires pre-registration on its own terms, in its own
> committed document, before any figure bearing on it is inspected.**

### WHAT IS UNCHANGED, AND MUST NOT BE READ AS CREATED HERE

> **THE CRITERION BY WHICH SUCH A CHANGE IS JUDGED — WHAT CONSTITUTES
> UNJUSTIFIED COMPLEXITY — STILL DOES NOT EXIST.** It is **still owed to
> sub-point 4.5**, and it is **still deliberately not named.**

**THIS AMENDMENT BROADENS THE SCOPE OF WHAT MUST BE PRE-REGISTERED. IT CREATES
NO THRESHOLD, NO PENALTY AND NO METRIC, AND IT MUST NOT BE READ AS CREATING
ONE.** The base document's §2 withheld that criterion deliberately and **this
amendment withholds it on the same grounds**: naming one here would be choosing
it in the absence of the analysis 4.5 exists to perform.

**The amended clause says what must be registered. It says nothing whatever about
what would be approved.**

### THE LEDGER ENTRY

**The enumeration originated in the instruction that specified the base
document's §2, not in its implementation.**

**LOGGED AS INSTANCE (34)**, as a **distinct sub-class** of the project's
recurring defect class: **a scope stated by enumeration where the commitment's
force requires a principle.** The enumeration was written from a mental model of
**which future changes are foreseeable** — the recurring class applied to **a set**
rather than to a numeric range.

**No earlier ledger instance is renumbered, restated or recounted here.**

**ON THE PRIOR RUNNING TOTAL, AND THIS IS RECORDED RATHER THAN RESOLVED.** The
instruction that ordered this document gives the prior running total as **33**.
**The last running total stated in any committed document is 32**
(`docs/handoff/31_point_5_closing.md` §7.1), and **no instance (33) appears in
any committed document as at this commit.** The figure 33 is therefore **supplied
but unsourced** in the repository — the same disposition
`docs/handoff/31_point_5_closing.md` §5.1 applies to the required stop floors.
**Both figures are recorded here with their provenance and neither is adopted
over the other.** Reconciling the ledger is not a disposition this document
makes, and it is not made silently by numbering this instance (34).

---

## 3. AMENDMENT 2 — §7's "WRITEUP", DEFINED

### WHAT THE BASE DOCUMENT SAYS

§7 binds **"any writeup of holdout results"** to carry both disclosures in full,
and **does not define what counts as a writeup.**

### THE DEFECT

> **THE NARROW READING — A FINAL HOLDOUT REPORT ONLY — IS AVAILABLE PRECISELY
> WHEN THE DISCLOSURE IS MOST INCONVENIENT TO MAKE, WHICH IS THE CIRCUMSTANCE
> THE REQUIREMENT EXISTS FOR.**

A single figure mentioned in passing, in a message that would be awkward to
interrupt with two full disclosures, is exactly the case the narrow reading
excuses and the broad reading catches.

### THE DEFINITION, AND IT IS THE BROAD ONE

> **A WRITEUP IS ANY COMMUNICATION, IN ANY MEDIUM, THAT STATES OR CHARACTERISES A
> RESULT COMPUTED ON THE HOLDOUT WINDOW.** This includes a final report; an
> interim or partial report; a summary; **a single figure quoted in passing**; a
> commit message; a chat message or report-back; a verbal account; and **any
> artifact committed to this repository that contains such a figure.**
>
> **THE OBLIGATION ATTACHES TO THE FIRST SUCH COMMUNICATION AND TO EVERY ONE
> AFTER IT. IT IS NOT DISCHARGED BY HAVING DISCLOSED ONCE.**
>
> **WHERE A COMMUNICATION IS TOO SHORT TO CARRY BOTH DISCLOSURES IN FULL, THE
> CORRECT RESPONSE IS TO MAKE IT LONGER** — not to omit them, and not to
> substitute a reference.

---

## 4. AMENDMENT 3 — §3's CLARIFICATION

### THE TENSION

§3 states that **the multi-settlement exposure is load-bearing**, being the reason
funding is provisioned at three settlements and the reason a funding term appears
in the sizing denominator and in the target cost bracket. **Two paragraphs later
it states that no frozen derivation depends on the word "intraday".**

**Both are true.** A reader may take the second to mean **the holding horizon
itself is not load-bearing**, which is the opposite of what the first says.

### THE CLARIFICATION, ADDED TO §3

> **THE TWO CLAIMS CONCERN DIFFERENT THINGS.**
>
> **THE HOLDING HORIZON IS LOAD-BEARING**, and several frozen derivations depend
> on it.
>
> **THE WORD "intraday", AS A LABEL IN THE STANDING BRIEF, IS NOT.** The only
> downstream use of the style premise was **the timeframe candidate set**, and
> **1h satisfies both the original and the amended wording.**
>
> **AMENDING THE LABEL THEREFORE REQUIRES NO RE-DERIVATION. AMENDING THE HORIZON
> WOULD REQUIRE A GREAT DEAL, AND IS NOT DONE HERE.**

**The claim about the absence of downstream dependence is limited to the
timeframe candidate set**, which is the only downstream use identified. **It is
not a claim that no frozen derivation depends on the holding horizon** — §3 of
the base document says the opposite, and the base document governs there.

---

## 5. AMENDMENT 4 — TWO CITATIONS, VERIFIED

**The checks were performed against the files before this section was written.**

### 5.1 CHECK A — THE FUNDING REJECTION AND THE MAGNITUDE FIGURE

**WHAT `docs/design/06_exit_resolution_spec.md` §5.4 CONTAINS.** The rejection,
and its ground: *"THE ALTERNATIVE THAT WAS REJECTED: charging funding as a
realised cash flow per settlement actually crossed … it is rejected because it
lets a stop-out return worse than −1.0R."* **It states no numeral for the
magnitude of that breach.** A search of that section for the numeral returns
nothing.

**WHAT `docs/design/06a_exit_resolution_spec_amendment_1.md` §2.3 CONTAINS.** The
numeral: *"the position pays for one settlement it never crossed — about
**0.0067R** at the 1.50% floor stop."*

> ### AND THAT NUMERAL DENOMINATES A DIFFERENT QUANTITY THAN THE BASE DOCUMENT
> ### ATTACHES IT TO.
>
> **0.0067R is the one-settlement OVERCHARGE under the ADOPTED reading** — the
> cost of the choice that **was** made. It is not the magnitude of the treatment
> that was **rejected**.

**AND THE TWO DOCUMENTS REJECT TWO DIFFERENT TREATMENTS.** Document 06 §5.4
rejects charging funding as a realised cash flow, on the ground that it returns
**worse** than −1.0R. Document 06a §2.4 rejects a different reading — provisioned
then reconciled — whose stop exit it gives as **≈ −0.993R**, which is **inside**
one risk unit, not beyond it. **Neither rejection carries the 0.0067R numeral.**

**DISPOSITION.** Both citations point at the right file and the right section for
the text they name: **06 §5.4 does state the rejection, and 06a §2.3 does state
the numeral.** Neither citation is wrong as to location. **What is wrong is the
pairing.** The base document's §4 sentence — *"The magnitude at stake there is
stated as roughly 0.0067R in … §2.3"* — **attaches a figure denominating the
adopted reading's overcharge to a claim about the rejected treatment's breach**,
and **that sentence does not govern.**

**THE CORRECTED STATEMENT, WHICH GOVERNS:** document 06 §5.4 rejected the
realised-cash-flow treatment **categorically, on the ground that it breaches
−1.0R at all, and stated no magnitude.**

**THE MAGNITUDE OF THAT REJECTED BREACH IS UNSOURCED IN THE SECTIONS EXAMINED** —
06 §5.4, 06a §2.3 and 06a §2.4. **No search was made for a section that would
make the original citation work.** It is recorded as supplied but unsourced,
pending derivation, on the disposition `docs/handoff/31_point_5_closing.md` §5.1
applies to the required stop floors.

**A RELATED FACT, RECORDED AND NOT AMENDED.**
`docs/handoff/31_point_5_closing.md` §5.3 attributes **both** the rejection and
the numeral to document 06 §5.4. **The numeral is not in that section.** That
document is frozen, this amendment does not reach it, and the fact is recorded
here so that a reader comparing the two is not left to reconcile them alone.

**The corrected figure `0.00589R`** logged at `docs/handoff/31_point_5_closing.md`
§8, erratum 1, **is a correction to the same overcharge quantity** and inherits
the same limitation: it denominates the adopted reading, not the rejected one.

### 5.2 CHECK B — THE REALISED-RISK RANGE

**WHAT `docs/handoff/30_point_5_3_4_portfolio.md` §6.1 CONTAINS.** *"Nominal is
$20.00 on all **6,021**; realised ranges **18.3392 – 20.0000**."* The section runs
from its heading to the rule preceding §7, and the range sits inside it.

**DISPOSITION: THE BASE DOCUMENT'S CITATION IS CORRECT. NO CORRECTION IS
NEEDED.**

**THE SUSPECTED INFERENCE LANDED ON THE RIGHT SECTION FOR A REASON.** §6.1 carries
**both** the realised-risk range **and** the partial-allocation branch counter, so
`docs/handoff/31_point_5_closing.md` §3.2's citation of §6.1 for the counter is
**also** correct. The two quantities share a section; the citation is not an
accident that happened to work.

**The range appears in that one place among the sections examined**, and
§6.1 is its primary and only source there.

### 5.3 WHETHER ANYTHING OPERATIVE CHANGES

**THE BASE DOCUMENT'S §4 ARGUMENT IS THAT 4.1 OWES A CRITERION. THAT ARGUMENT IS
INTACT.** But its **stated ground is corrected, and the correction cuts both
ways:**

- **THE SENTENCE "Either figure is larger than the term accepted in §7.3" DOES
  NOT SURVIVE AS STATED**, because neither figure denominates the rejected
  treatment's breach. **The numeric comparison is withdrawn.**
- **THE STRUCTURAL CLAIM SURVIVES, AND IS STATED MORE EXACTLY.** Document 06 §5.4's rejection is
  **categorical** — it states no magnitude at all — while the fill-price term of
  `docs/handoff/30_point_5_3_4_portfolio.md` §7.3 was **accepted on magnitude
  grounds**, at most **0.0033 USDT** across the six cells measured, **under
  0.017% of a risk unit**.

> **THE TWO DECISIONS DIFFER IN KIND, NOT MERELY IN THRESHOLD.** One breach of
> the after-costs risk rule was refused outright with no magnitude named; a
> second was accepted because its magnitude is small. **There is no stated
> criterion reconciling a categorical refusal with a magnitude-based
> acceptance**, and 4.1 owes exactly that.

**4.1's OBLIGATION IS UNCHANGED IN SUBSTANCE AND BETTER STATED.** No threshold,
epsilon or magnitude is set here, and none is implied.

### 5.4 THE ONE FIGURE IN THIS DOCUMENT THAT IS NOT COMMITTED

**The prior running total of 33 in §2's ledger entry.** It is supplied by the
instruction that ordered this document and appears in no committed document; the
last committed total is 32. **It is marked as such at the point of use and is not
adopted.** Every other figure here carries a citation verified against its file.

---

## 6. WHAT IS NOT AMENDED

**THE FIVE DISPOSITIONS THEMSELVES ARE UNCHANGED:**

- **The frozen thesis still governs the indicator question unconditionally.**
  Amendment 1 widens what must be pre-registered; it does not reopen the thesis
  and does not admit anything into it.
- **The holding-horizon premise amendment stands as made** — a multi-settlement
  short-swing strategy on 1h bars. Amendment 3 clarifies the reasoning around it
  and changes neither the amendment nor its scope.
- **The 1% question is still routed to 4.1, with no epsilon set here.**
  Amendment 4 corrects the citations supporting the routing; the routing is
  untouched.
- **The timeframe candidate set is still logged, with no action.**
- **Regime-aware validation is still recorded as unfinished work rather than a
  conflict between committed artifacts.**

> **THIS AMENDMENT CHANGES HOW TWO COMMITMENTS ARE SCOPED, RESOLVES ONE WORDING
> TENSION, AND CORRECTS CITATIONS. IT REVERSES NO DISPOSITION.**

---

## 7. CHANGE DISCIPLINE

**A CHANGE TO THIS AMENDMENT IS A FURTHER DOCUMENT WITH ITS OWN COMMIT AND AN
EXPLICIT STATEMENT OF WHAT CHANGED AND WHY — NEVER A SILENT EDIT.**

Under the naming convention adopted for Point 4 documents it would be
`docs/design/04_0_divergence_disposition_amendment_2.md`. **The single-letter
convention used by 05a, 05b and 06a is not used here**, because the `04_0` prefix
encodes a sub-point rather than a document number and a letter would be ambiguous
between the documents sharing that prefix.

**A SILENT EDIT IS A CONTAMINATION EVENT.** This applies with particular force to
§2's amended clause and §3's definition, because both were written to be
inconvenient later: one forecloses every route around a pre-registration
requirement, and the other forecloses every excuse for a shortened disclosure.
**A pre-commitment that can be edited when it becomes inconvenient is not a
pre-commitment.**

---

**Committed alone, before the 4.0 parametric derivation and before any
performance figure exists for this thesis. Two scopes widened, one tension
resolved, two citations verified — one correct, one carrying a conflation the
check found. No criterion is created, no threshold is set, and no disposition is
reversed.**
