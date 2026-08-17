# ARTIFACT CONTAINMENT AND THE DEAD APPARATUS

**Point 4, sub-point 4.2a.** One declaration, one containment regime, one
carve-out, one testimony, one ledger instance. **Nothing is computed and no
aggregation rule is committed.**

## 0. TWO SCOPE NOTES

### 0.1 NO BANNED NAME APPEARS IN THIS DOCUMENT

**IT CONTAINS NONE OF THEM.** Where a field or column must be referred to, it is
referred to **by citation** to `docs/handoff/41_point_4_2_artifact_audit.md`,
which lists them under its own declared exception. **That was available and it is
taken**, so no exception is needed here.

### 0.2 NO ARTIFACT WAS OPENED

**NOT ONE FILE NAMED IN §3 WAS OPENED BY THIS DOCUMENT, INCLUDING TO VERIFY ITS
CONTENTS.** Every fact about them is taken from
`docs/handoff/40_point_4_2_fold_audit.md` and
`docs/handoff/41_point_4_2_artifact_audit.md`.

---

## 1. WHAT THIS DOCUMENT IS

**A PRE-REGISTRATION, FROZEN ON COMMIT**, joining the frozen specification per
`docs/design/04_0_divergence_disposition_amendment_2.md` §2. Committed alone with
the manifest.

**IT RESTS ON THE TWO AUDITS AND REINTERPRETS NEITHER.** Where a fact is theirs it
is cited to them.

### 1.1 WHAT IT DOES NOT DO

**IT COMMITS NO AGGREGATION RULE.** How results are combined across folds is
4.2's and is open.

**IT DECIDES NOTHING ABOUT WHICH CANDIDATES ARE EVALUATED.**

**IT TAKES NO POSITION ON THE 2,817 CANDIDATES FALLING OUTSIDE ANY TEST WINDOW.**
`docs/handoff/40_point_4_2_fold_audit.md` §3.4 counts them and §6.4 states what
they bear on. **Open, and 4.2's.**

**IT CHANGES NO CODE, DELETES NOTHING AND MOVES NOTHING.** §3.5 and §7 name the
execution as owed to its own step.

---

## 2. THE SWEEP APPARATUS IS DEAD RELATIVE TO THE FROZEN THESIS

### 2.1 THE DECLARATION

> ### `src/sweep/` SELECTS A PER-FOLD ATR MULTIPLIER ON TRAINING DATA. IT DOES
> ### NOT PARTICIPATE IN EVALUATING THE FROZEN THESIS, AND THE FROZEN THESIS FITS
> ### NOTHING.

### 2.2 THE GROUND, AND IT IS ONE GROUND

> ### BOTH CHANNELS BY WHICH A FITTED QUANTITY COULD REACH THE EVALUATION PATH
> ### ARE CLOSED, AND THAT IS THE WHOLE OF THE ARGUMENT.

- **THE IMPORT CHANNEL.** `docs/handoff/40_point_4_2_fold_audit.md` §4.1
  establishes that no module under `src/engine/` imports `src.folds` or
  `src.sweep`, over AST import nodes across all eight engine modules.
- **THE FILE-READ CHANNEL.** `docs/handoff/41_point_4_2_artifact_audit.md` §4.1
  establishes that `src/engine/` reads none of the sweep's artifacts by path
  either — every `open`, `load`, `read_csv`, `read_json`, `read_parquet`,
  `read_table` and `glob` call in those modules was enumerated, and the only
  reads are the contract cache and parquet bars.

**AN ARTIFACT OPENED BY PATH WOULD NOT APPEAR AS AN IMPORT**, which is why the
second channel had to be checked separately and why the first alone would not have
established this.

### 2.3 WHAT IS NOT A GROUND, AND WHY EACH IS REJECTED

**THREE FACTS ARE TRUE, ARE RECORDED IN THE AUDITS, AND ARE NOT USED HERE:**

- **THE SWEEP SELECTED UNDER A STOP CAP `docs/design/04_1g_cap_adoption.md` HAS
  RETIRED.**
- **IT RAN THROUGH `simulate.run_backtest` WHILE THE GOVERNING RISK UNIT IS
  `portfolio.size_position`'s**, which
  `docs/handoff/35_point_4_1c_denominator_audit.md` established are two different
  cost paths.
- **ITS PARAMETERISATION DIFFERS FROM THE THESIS'S IN THE MULTIPLE, THE CAP AND
  THE FLOOR**, per `docs/handoff/41_point_4_2_artifact_audit.md` §3.4.

> ### EACH OF THOSE SAYS THE SELECTION WAS MADE BADLY, NOT THAT THE APPARATUS IS
> ### DEAD. A LIVE APPARATUS THAT SELECTED UNDER WRONG ASSUMPTIONS WOULD NEED
> ### REDOING, NOT DECLARING DEAD.

**THE DISTINCTION IS THE POINT OF THIS SECTION.** A reader who takes any of the
three as the reason would conclude that fixing the assumptions revives the
question. **It does not, because the apparatus is disconnected rather than
mistaken** — and if it were connected, all three would be reasons to redo it
rather than reasons to ignore it.

### 2.4 THE CONSEQUENCE FOR THE FOLDS

**WITH NOTHING FITTED ON TRAIN IN THE FROZEN THESIS'S PATH, THE TRAIN/TEST SPLIT
CARRIES NO PROTECTION FOR IT.** There is no selection to protect the test windows
from.

> ### THE NINE FOLDS ARE A TIME-VARIATION DIAGNOSTIC FOR THE FROZEN THESIS, NOT
> ### NINE TRIALS.

**AND THIS VALIDATES A GROUND THAT UNTIL NOW RESTED ON A SOURCE-CODE DOCSTRING.**
`docs/design/04_1c_consequences_and_thresholds.md` §3.3 chose the pooled level for
kill condition (d) partly because `src/folds/schedule.py`'s docstring calls the
nine folds *"a STABILITY PROBE, NOT NINE INDEPENDENT TRIALS."*

**THAT WAS A DOCSTRING AND A FROZEN PRE-REGISTRATION RESTED ON IT.** The two
audits establish the same conclusion from the code's structure rather than from
its prose, and this document commits it.

> ### §3.3's CONCLUSION NOW STANDS ON A COMMITTED PREMISE.

**ITS SECOND GROUND IS UNAFFECTED AND STILL NARROWER THAN IT WAS USED FOR.**
`docs/handoff/40_point_4_2_fold_audit.md` §6.3 records that the docstring's
warning is about **training-window** overlap while the test windows are disjoint.
**That narrowing stands**, and §3.3's conclusion is not widened by this section.

### 2.5 WHAT WOULD REVIVE IT

> ### IF ANY FUTURE STEP INTRODUCES A CHAIN FROM `src/sweep/` TO THE EVALUATION
> ### PATH — BY IMPORT, BY FILE READ, OR BY ANY OTHER MEANS — THIS DECLARATION
> ### LAPSES AND THE FOLD INTERPRETATION AT §2.4 MUST BE REARGUED.

**THE DECLARATION IS CONDITIONAL AND IS NOT PERMANENT.** It describes a property
of the code as it stands, and a property of the code can change. **A step that
creates such a chain must say so and reopen §2.4**, not rely on this document
having once been true.

### 2.6 `src/sweep/` IS NOT DELETED AND IS NOT DEPRECATED

**IT BUILDS ITS OWN GRID AND REMAINS WHATEVER IT IS.** This document governs its
relationship to the frozen thesis and nothing else. **Nothing here says the
apparatus is worthless, wrong, or to be removed** — only that it is not in the
evaluation path.

---

## 3. CONTAINMENT

### 3.1 THE ARTIFACTS THIS SECTION COVERS

**FROM `docs/handoff/41_point_4_2_artifact_audit.md` §2 AND §6.1**, the files whose
schema indicates outcome quantities, or whose schema is unestablished and is
therefore treated as though it did:

1. **`data/derived/sweep/sweep.json`** — outcome quantities established.
2. **`data/derived/sweep/bands.json`** — built from them.
3. **`data/derived/sweep/sweep_cells.jsonl`** — untracked; §3.5.
4. **`data/derived/analysis/e6_dispersion.json`** — schema indicates dispersion
   only, **but its contents were not confirmed and its own commit message
   announces a partial firewall lift.** Covered by precaution.
5. **`reports/07_structural_pass_raw.json`** — **schema unestablished.** Covered
   by precaution.
6. **`tests/golden/btc_2023_01_gated.csv`** and
   **`tests/golden/btc_2023_01_signal_ungated.csv`** — outcome quantities
   established. **Governed by §4's carve-out rather than by §3.2's prohibition.**

> **ITEMS 4 AND 5 ARE COVERED BECAUSE THEIR CONTENTS ARE UNKNOWN, NOT BECAUSE
> THEY ARE KNOWN TO OFFEND. AN UNKNOWN IS TREATED AS CONTAINING**, because the
> only way to establish otherwise is to open the file, which is the act being
> prevented.

### 3.2 THE READ PROHIBITION

> ### NO STEP, DOCUMENT OR REPORT MAY OPEN AN OUTCOME-BEARING ARTIFACT NAMED IN
> ### §3.1. A STEP THAT BELIEVES IT MUST DO SO STOPS AND REPORTS INSTEAD.

**THE PROHIBITION COVERS READING FOR ANY PURPOSE, INCLUDING VERIFICATION.**

> ### A VERIFICATION THAT OPENS THE FILE HAS ALREADY READ WHAT IT WAS VERIFYING
> ### THE ABSENCE OF.

**THAT IS NOT A TECHNICALITY.** The most plausible future breach is not someone
wanting a figure; it is someone wanting to confirm there is no figure. **The
confirming read and the offending read are the same read.**

**STOPPING AND REPORTING IS THE PERMITTED RESPONSE**, on the pattern
`docs/design/04_0_decision_rule.md` §8 uses for an under-specified constraint:
report it, do not resolve it by acting.

### 3.3 THE EXISTING READERS, ENUMERATED AND NOT RETROSPECTIVELY BROKEN

**THE PROHIBITION BINDS FUTURE READS. IT DOES NOT SILENTLY BREAK THE SUITE.**
`docs/handoff/41_point_4_2_artifact_audit.md` §4.1 enumerates every existing
reader, and they fall into two classes:

- **THE SWEEP'S OWN MODULES** — `grid.py`, `bands.py`, `sweep.py`,
  `sweep_report.py` — reading their own outputs. **Permitted: the apparatus may
  read its own artifacts.** It is dead relative to the frozen thesis (§2), which
  is a statement about what it feeds, not a prohibition on it functioning.
- **THREE TEST MODULES** — `tests/test_sweep_prescreen.py`,
  `tests/test_sweep_run.py`, `tests/test_dispersion.py` — which read these
  artifacts on every suite invocation, two of them failing rather than skipping
  when absent.

> ### THE THREE TEST MODULES ARE A CLOSED SET, RECORDED HERE, AND WHETHER THEY
> ### SHOULD CONTINUE TO READ THESE FILES IS OWED. §7.

**NO NEW READER JOINS EITHER CLASS WITHOUT AMENDING THIS DOCUMENT.**

### 3.4 WHAT HAPPENS TO THE ARTIFACTS

**`docs/handoff/41_point_4_2_artifact_audit.md` §7's RECOMMENDATIONS ARE INPUT.
THE CHOICES ARE MADE HERE.**

**THEY ARE NOT DELETED AND NOT UNTRACKED.** The audit's ground is adopted: they
are the evidence for the superseded point and for the audit's own verdict, and
removing them would destroy the record that makes the verdict checkable.
**Containment is about reading, not about existence.**

**THEY ARE MARKED AT THE DIRECTORY LEVEL.** A marker file in each directory
holding one, stating what the files are, which thesis they belong to, that they
carry or may carry outcome quantities, and that §3.2 prohibits opening them.
**A marker a step meets before the file beats a rule it must remember.**

**THE MARKER'S WRITING IS OWED TO ITS OWN STEP** — this document changes no file
other than itself and the manifest.

### 3.5 `sweep_cells.jsonl`, ADDRESSED SEPARATELY

**IT SAT OUTSIDE THE AUDIT'S FRAME.**
`docs/handoff/41_point_4_2_artifact_audit.md` enumerated **tracked** artifacts, and
this file is untracked. It is present in the working tree, holds sweep cells, and
`tests/test_sweep_run.py` reads it and **fails rather than skips** when it is
absent.

**TWO CONSEQUENCES, BOTH REAL:**

1. **THE SUITE IS NOT REPRODUCIBLE FROM THE REPOSITORY ALONE.** A clean clone
   cannot pass, because a required file is not in it. **That is a defect in the
   suite's own terms**, independent of anything about firewalls.
2. **AN OUTCOME-BEARING FILE SITS OUTSIDE VERSION CONTROL AND INSIDE THE WORKING
   TREE.** It is subject to no history, no review and no hash.

> ### THE DECISION: IT STAYS WHERE IT IS. IT IS NEITHER TRACKED NOR DELETED.

**THE GROUND FOR NOT TRACKING IT:** doing so would add a further outcome-bearing
file to version control, which runs directly against §3.2.

**THE GROUND FOR NOT DELETING IT:** a test currently requires it and fails without
it, and deleting it here would break the suite from a document that commits to
changing no code.

**THE COST IS STATED RATHER THAN ABSORBED:** consequence 1 stands unrepaired.
**Repairing it means either making that test skip, or regenerating the file from
source in a clean clone — both code changes, and both owed.** §7.

### 3.6 THE MECHANICAL GUARD

**`tests/test_artifact_containment.py`, COMMITTED WITH REPORT 41, ALREADY ASSERTS
THAT NO ENGINE MODULE AND NO POINT 4 ANALYSIS MODULE OPENS THESE PATHS.** It does
not yet cover the whole tree.

> ### A TEST ASSERTING THAT NOTHING OUTSIDE THE SWEEP'S OWN MODULES AND §3.3's
> ### CLOSED SET OPENS THESE PATHS IS OWED TO ITS OWN STEP.

**WHY A GUARD AND NOT THE PROHIBITION ALONE:**

> ### A RULE ENFORCED ONLY BY INTENTION IS THE SHAPE OF EVERY DEFECT IN THE
> ### LEDGER.

The ledger's recurring class is a criterion written from a mental model rather
than from what the code does. **A prohibition nobody can check is exactly that**:
a belief about the repository's behaviour, held in place by care. **The guard is
what converts it into a property.**

---

## 4. THE FIXTURE CARVE-OUTS

### 4.1 WHAT IS BEING CARVED OUT

The two golden files under `tests/golden/` and
`tests/test_regression_pinned_trade.py` read outcome-named values on **every suite
invocation**. They are determinism and arithmetic-identity fixtures, they predate
the thesis freeze, and no decision cites them —
`docs/handoff/41_point_4_2_artifact_audit.md` §4.3.

**THEY NEED A CARVE-OUT BECAUSE THEY ARE OTHERWISE A STANDING VIOLATION OF THE
BLANKET BAN**, and because `src/engine/sizing.py` already demonstrates the form: a
recorded carve-out permitted **only under three conditions, all asserted by test.**

### 4.2 THE CARVE-OUT, WITH ITS CONDITIONS

> ### THE TWO GOLDEN FILES AND THE PINNED-TRADE REGRESSION MAY READ
> ### OUTCOME-NAMED VALUES, PERMITTED ONLY UNDER FOUR CONDITIONS.

**(a) DETERMINISM AND SINGLE-POSITION IDENTITY ONLY.** They may assert that
identical inputs produce identical outputs, and that one hand-derived arithmetic
identity holds on one named position. **They may not compare populations, compare
two configurations, or aggregate over rows.**

**(b) EVERY EXPECTED VALUE IS HAND-DERIVED AND ITS DERIVATION IS WRITTEN DOWN.**
`tests/test_regression_pinned_trade.py`'s docstring already meets this — *"Every
value below is re-derived by hand from the formula, not copied from a run."*
**A value copied from a run is not permitted**, because a fixture that records what
the system did is a measurement wearing a fixture's name.

**(c) EXACTLY THESE ARTIFACTS AND EXACTLY THESE READERS.** The two files named at
§3.1(6), and `tests/test_regression_pinned_trade.py` and
`tests/test_determinism_golden.py`. **No further fixture and no further reader
joins without amending this document.**

**(d) THE BLANKET NAME BAN OTHERWISE INTACT.** The twelve-name guard is not
relaxed for these files, for these tests, or for anything else — mirroring the
third condition of the existing carve-out.

### 4.3 WHAT VOIDS IT

**ANY OF THE FOLLOWING EXCEEDS THE CARVE-OUT AND REOPENS IT:**

- **USING A FIXTURE TO COMPARE TWO CONFIGURATIONS**, which converts a determinism
  check into a comparison.
- **ADDING A SECOND PINNED TRADE**, because a count over two is a population of
  two and condition (a) then fails by arithmetic rather than by intent.
- **REGENERATING A GOLDEN FILE AND TAKING EXPECTED VALUES FROM THE RUN** rather
  than re-deriving them, which voids condition (b).
- **ANY ASSERTION OVER AN AGGREGATE OF THE ROWS** — a sum, a mean, a count
  conditioned on an outcome column.

> ### THE FIRST AND THE LAST ARE THE ONES THAT WOULD LOOK INNOCENT AT THE TIME,
> ### AND THEY ARE NAMED FOR THAT REASON.

### 4.4 THE EXECUTION IS OWED

**THE CARVE-OUT IS COMMITTED HERE. WHATEVER CODE OR COMMENT RECORDS IT IS WRITTEN
ELSEWHERE**, on the model of `sizing.py`'s, whose conditions are stated in the
source and asserted by test. §7.

---

## 5. THE HUMAN CHANNEL

### 5.1 THE RESIDUAL

`docs/handoff/41_point_4_2_artifact_audit.md` §5 records that code tracing cannot
establish whether a person opened an artifact and let what they saw inform a
judgement, and names that as the residual it cannot close.

### 5.2 THE PROJECT OWNER'S ANSWER, RECORDED

> ### THE PROJECT OWNER STATES THAT HE HAS NOT LOOKED AT THE SWEEP ARTIFACTS, THE
> ### BANDS RESULTS, OR THE PRIOR POINT 4's REPORTS SINCE BEFORE THE POINT 1
> ### REOPEN.

### 5.3 WHAT THAT DOES AND DOES NOT ESTABLISH

> ### IT IS TESTIMONY, NOT EVIDENCE A READER CAN CHECK, AND IT IS RECORDED AS
> ### TESTIMONY.

**No artifact in this repository corroborates it and none could.** A reader who
declines to accept it is not thereby in conflict with anything the repository
records.

**TWO INDEPENDENT REASONS THE EXPOSURE IS LOW EVEN IF THE RECOLLECTION IS
IMPERFECT:**

1. **THE ARTIFACTS DESCRIBE A DIFFERENT CONFIGURATION.**
   `docs/handoff/41_point_4_2_artifact_audit.md` §3.4 establishes that they differ
   from the frozen thesis in **the multiple, the cap and the floor**. A figure
   carried forward from them would be a figure about a system that is not the one
   being validated.
2. **EVERY ARTIFACT PREDATES THE FREEZE.** That report's §3 dates the freeze at
   **2026-08-11** against a latest artifact of **2026-08-09**. **Anything seen was
   seen before the thesis it would have to contaminate existed.**

> ### THE FIREWALL CLAIM SURVIVES ON THE CODE AND DOCUMENT EVIDENCE AT
> ### `docs/handoff/41_point_4_2_artifact_audit.md` §6, NOT ON THIS TESTIMONY.
> ### WHAT THIS SECTION DOES IS CLOSE A RESIDUAL BY TESTIMONY, AND SAY SO.

---

## 6. THE LEDGER

### 6.1 THE TOTAL, READ

**`docs/design/04_1g_cap_adoption.md` §7.3 states "47 + 1 = 48". The total read is
48**, so the instance below takes **(49)**.

### 6.2 INSTANCE (49)

**AN INSTRUCTION REQUIRED CONTENT IT SEPARATELY FORBADE THE MEANS OF PRODUCING.**

**ONE INSTANCE, TWO SYMPTOMS**, following the precedent by which
`docs/design/04_1a_denomination_amendment_1.md` §7 logged instance (41) as one
defect with two symptoms:

- **THE FIRST SYMPTOM.** It required reporting the schemas of files under `data/`
  while separately forbidding anything under `data/` to be opened. Recorded at
  `docs/handoff/41_point_4_2_artifact_audit.md` §1.2.
- **THE SECOND SYMPTOM.** It banned a set of tokens from a report whose required
  content was a list of field names drawn from that same set. Recorded at that
  report's §1.1.

**SUB-CLASS: internal contradiction between an instruction's constraints and its
requirements** — the sub-class `docs/handoff/31_point_5_closing.md` §7.2 records
as instances **(23) to (26)**, continuing at **(33)**, **(35)**, **(39)** and
**(44)**.

> ### THIS IS THE SIXTH OCCURRENCE OF THAT SUB-CLASS IN POINT 4.

**THE MECHANISM COMMON TO ALL SIX:** a requirement and a constraint refer to the
same object and disagree about what may be done to it. In (33) it was a text that
had to be transcribed verbatim and to omit a phrase it contained; in (35) and (39)
a total that had to be stated and was delegated; in (44) a count of token
occurrences that the requirements determined; here a file that had to be described
and not opened, and a vocabulary that had to be listed and not used.

**IN EVERY CASE THE IMPLEMENTING SESSION REPORTED THE CONTRADICTION RATHER THAN
RESOLVING IT**, and in every case the contradiction was visible on the face of the
instruction before any work began.

### 6.3 A CORRECTION, RECORDED AS A CORRECTION AND NOT AS AN INSTANCE

**THE PREMISE HANDED TO THIS DOCUMENT IS THAT
`docs/handoff/41_point_4_2_artifact_audit.md` §1.1 "declares eight occurrences" of
banned names in its own text. IT DECLARES NO NUMBER AT ALL.**

That section enumerates **six sections** in five bullets and says the tokens
*"occur in exactly these places."* **It makes a location claim, not a count.**

**THE LOCATION CLAIM IS CORRECT AND COMPLETE.** A recount over the committed file
finds the tokens in §2.1, §2.2, §2.5, §4.3, §5 and §6.1 — **exactly the six
declared, with none declared-but-absent and none present-but-undeclared.**

**THE ACTUAL FIGURES, ESTABLISHED BY RECOUNT:**

- **16 occurrences** in total.
- **7 distinct names.**
- **8 lines** carrying one or more.
- **6 sections.**

> ### THE FIGURE "EIGHT" WAS NEVER IN THE DOCUMENT. IT APPEARED IN THE
> ### REPORT-BACK THAT ACCOMPANIED IT, AND IT REFERRED TO THE EIGHT **LINES** A
> ### GREP MATCHED — NOT TO OCCURRENCES, AND NOT TO DISTINCT NAMES.

**SO §1.1 COUNTED NEITHER DISTINCT NAMES NOR OCCURRENCES. IT COUNTED NOTHING**,
and the imprecision is the report-back's.

**THE ENTRY, IN THE CONSOLIDATED INDEX'S FORM:**

> **Point 4 artifact audit's report-back — the banned-name occurrence count.**
> *Target: a report-back, not a committed artifact.* **SAID:** "All eight
> occurrences are field names." **CORRECT:** there are **16 occurrences** across
> **8 lines**, of **7 distinct names**, in **6 sections**; the figure eight
> counted matched lines. **CORRECTION LIVES AT:**
> `docs/design/04_2a_artifact_containment.md` §6.3. **Not operative** — the
> report's own §1.1 makes no count, its location claim is correct and complete,
> and no decision rests on the figure.

> ### IT IS NOT ADDED TO THE INDEX. Its target is a chat report-back, and
> `docs/design/04_0_divergence_disposition_amendment_2.md` §2's membership does
> not reach communications. **The entry is written in the index's form so that a
> future holder can adopt it if they judge the index should range wider**, and
> that judgement is not made here.

**THE INDEX STANDS AT TEN IN FACT AGAINST NINE IN ITS OWN TEXT**, unchanged.

### 6.4 THE TOTAL

**48 + 1 = 49.**

**No earlier instance is renumbered or recounted**, and the ledger remains
contiguous from (1) to (49).

---

## 7. WHAT IS OWED, AND TO WHOM

1. **THE CONTAINMENT EXECUTION** — writing the directory markers §3.4 commits.
   **No owner at this commit.**
2. **THE MECHANICAL GUARD** — the tree-wide read guard §3.6 commits. **No owner at
   this commit.**
3. **THE CARVE-OUT'S RECORDING** — writing §4.2's four conditions into the source
   and asserting them by test, on `sizing.py`'s model. **No owner at this
   commit.**
4. **`sweep_cells.jsonl`'s REPRODUCIBILITY** — §3.5 leaves the file in place and
   the suite non-reproducible from a clean clone. Repairing it means making
   `tests/test_sweep_run.py` skip, or regenerating the file from source. **No
   owner at this commit.**
5. **THE THREE TEST MODULES AT §3.3** — whether they should continue to read
   outcome-bearing artifacts on every invocation. **No owner at this commit.**
6. **THE `simulate.py` CAP DIVERGENCE** — `docs/design/04_1g_cap_adoption.md` §5
   records that `simulate.py` still applies a cap the specification has retired,
   and states it has no owner. **Still no owner at this commit.**

   > **A NOTE ON THE DEADLINE.** The instruction commissioning this document
   > requires that item to have an owner "before the freeze at 4.7". **No
   > committed document names a sub-point 4.7 or a freeze at one** — the only
   > "4.7" in the repository is a section number inside
   > `docs/design/04_1c_consequences_and_thresholds.md`. **The deadline is
   > recorded as stated and cannot be cited to a source**, and whoever fixes the
   > freeze point should attach this item to it.

7. **THE PLACEHOLDER PAIR** — `equity_usd` and `max_leverage`, which
   `docs/handoff/40_point_4_2_fold_audit.md` §5.3 names as unmeasured placeholders
   feeding `leverage_term` inside a derived floor that governs, inert at present
   values. **No owner at this commit.**

**SEVEN ITEMS, SEVEN WITHOUT OWNERS.** That is recorded as a fact about the
project's state rather than smoothed over: **the audits have produced more open
items than the chain has steps to absorb them.**

---

## 8. CHANGE DISCIPLINE

**A CHANGE TO ANY COMMITMENT HERE IS A NEW DOCUMENT WITH ITS OWN COMMIT AND AN
EXPLICIT STATEMENT OF WHAT CHANGED AND WHY — NEVER A SILENT EDIT.** It would be
`docs/design/04_2a_artifact_containment_amendment_1.md`.

**A SILENT EDIT IS A CONTAMINATION EVENT.**

**THE CLAUSE MOST EXPOSED IS §3.2's PROHIBITION ON VERIFYING READS.** It will
first be inconvenient when someone wants to confirm that an artifact is harmless,
and the confirming read is the offending read. **An amendment permitting such a
read must say that it permits reading an outcome-bearing artifact to check whether
it is one**, in those words.

---

**Committed alone. The sweep apparatus declared dead relative to the frozen thesis
on one ground — both channels closed — with three true facts named and rejected as
grounds because each says the selection was made badly rather than that the
apparatus is irrelevant. The fold interpretation §3.3 relied on now stands on a
committed premise rather than a docstring, without being widened. Containment
committed: the artifacts kept and marked, reading prohibited for any purpose
including verification, existing readers enumerated as a closed set, and
`sweep_cells.jsonl` left in place with its reproducibility cost stated rather than
absorbed. One carve-out committed under four conditions with four voiding uses
named. One residual closed by testimony and labelled as testimony. One ledger
instance at 48 + 1 = 49, the sixth of its sub-class, and one correction recorded
in the index's form without being added to it. Seven items owed, none with an
owner. No aggregation rule is committed and no position is taken on which
candidates are evaluated.**
