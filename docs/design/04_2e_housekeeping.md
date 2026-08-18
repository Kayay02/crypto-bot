# HOUSEKEEPING: TWO ERRATA, ONE AMENDMENT, ONE OBJECTIVE, ONE PROTOCOL

## 0. TWO SCOPE NOTES, AND THE CHECK THIS DOCUMENT RESTS ON

### 0.1 NO BANNED NAME APPEARS IN THIS DOCUMENT

**Following `docs/design/04_2a_artifact_containment.md` §0.1.** Where an item must
be referred to whose committed name contains one, it is referred to **by
citation** — the placeholder pair at `docs/design/04_2b_point_4_decomposition.md`
§5.3 is named that way and not by its two identifiers.

### 0.2 NO ARTIFACT WAS OPENED

**EVERY FINDING BELOW COMES FROM PARSING PYTHON SOURCE, FROM `git log`, OR FROM
CALENDAR ARITHMETIC ON A TIMESTAMP.** No file named at
`docs/design/04_2a_artifact_containment.md` §3.1 was opened, for any purpose,
including to verify the checks this document reports. §3.2 is explicit that the
confirming read and the offending read are the same read.

**NO OUTCOME QUANTITY IS COMPUTED OR INSPECTED.** The only numbers here are
counts of candidates, counts of tests, counts of call sites and two timestamps.

### 0.3 THE CHECK: WHO OPENS `bands.json`

**THE CLAIM UNDER TEST.** The consolidated code step reported that
`tests/test_sweep_bands.py` opens `data/derived/sweep/bands.json` on every suite
invocation, contradicting `docs/handoff/41_point_4_2_artifact_audit.md` §4.1's
record that the file has **no reader found.**

**IT WAS VERIFIED INDEPENDENTLY AND NOT TAKEN FROM THAT REPORT.** The chat
channel is the thing §5 below regulates, and a document that regulated it while
resting on it would have no standing to.

**THE METHOD, OVER AST NODES AND NEVER OVER RAW TEXT**, per
`docs/design/04_1a_denomination_amendment_1.md` §7:

1. Parse `src/sweep/bands.py` and read its module-level assignments. **`ARTIFACT_PATH`
   is the only constant naming `bands.json`.**
2. Parse every `.py` file under `src/` and `tests/`, build each module's import
   alias table from its `Import` and `ImportFrom` nodes, and collect every `Call`
   node whose function is a read — `open`, `load`, `loads`, `read_json`,
   `read_csv`, `read_parquet`, `read_table`, `glob` — that has, among its
   descendants, an `Attribute` resolving to `src.sweep.bands.ARTIFACT_PATH`.
3. For each hit, find the enclosing function and inspect its decorator list and
   its body for any skip.

**THE RESULT — THE CLAIM IS CONFIRMED, AND UNDERSTATED.**

> ### **SIX CALL SITES, NOT ONE.** `tests/test_sweep_bands.py` LINES 132, 315,
> ### 374, 379, 399 AND 409, EACH `json.load(open(bd.ARTIFACT_PATH))`, WHERE `bd`
> ### RESOLVES TO `src.sweep.bands` BY ITS OWN IMPORT.

**AND EVERY ONE RUNS UNCONDITIONALLY.** The six enclosing functions carry **no
decorator, no `skip`, no `importorskip` and no `xfail`**; the module defines no
`pytestmark` and calls `skip` nowhere. The step's report named only line 132.

**THE MODULE READS THREE PROHIBITED ARTIFACTS, NOT ONE.** Established by the same
method:

- **`bands.json`** — the six sites above.
- **`data/derived/sweep/sweep_cells.jsonl`** — through the module-scoped `cells`
  fixture at `tests/test_sweep_bands.py:25`, which calls `sw.load_cells()`.
  `src/sweep/sweep.py:524-528` raises `FileNotFoundError` rather than skipping
  when the file is absent.
- **the sweep trade tables** under `data/derived/sweep/trades/`, through
  `src/sweep/bands.py:539`'s `srep.load_trades`, reached from the test at `:91`.

**THE MODULE'S OWN COMMENT AT `:21` DESCRIBES ITS FIXTURES AS "the real step-2
artifact, read once."** The reading was never concealed. It was never enumerated.

**AND IT PREDATES BOTH DOCUMENTS THAT MISSED IT.** `git log` over the path returns
**exactly one commit**: `68e5b16`, **2026-08-09**, which introduced the file and
the read of `bd.ARTIFACT_PATH` together. `docs/handoff/41_point_4_2_artifact_audit.md`
was committed at `c5ae538` and `docs/design/04_2a_artifact_containment.md` at
`3fa9d06`, both on **2026-08-17**. The file has not been modified since it was
created.

> ### **THE READER EXISTED, UNCHANGED, FOR EIGHT DAYS BEFORE THE AUDIT THAT
> ### FAILED TO FIND IT. THE ENUMERATION WAS WRONG WHEN IT WAS WRITTEN, NOT
> ### OVERTAKEN BY A LATER CHANGE.**

**WAS THE REPORT-BACK WRONG? IT WAS INCOMPLETE, IN THE DIRECTION THAT UNDERSTATES
THE FINDING.** It named one call site where there are six, and one artifact where
there are three. **Its substantive claim — that the module reads `bands.json` on
every suite invocation and that §4.1 records no reader — is correct.** The
understatement is recorded rather than passed over, because the point of §5's
protocol is that a chat account is not evidence, and this is an instance of a chat
account being checkable-and-checked rather than trusted.

---

## 1. WHAT THIS DOCUMENT IS

**A PRE-REGISTRATION, JOINING THE FROZEN SPECIFICATION ON ITS COMMIT**, per
`docs/design/04_0_divergence_disposition_amendment_2.md` §2's open-forward clause.

**IT CLOSES FIVE ITEMS LEFT OPEN BY THE CONSOLIDATED CODE STEP:**

1. **§2** — an amendment to the grandfathered reader set at
   `docs/design/04_2a_artifact_containment.md` §3.3.
2. **§3** — an erratum against `docs/handoff/41_point_4_2_artifact_audit.md` §4.1.
3. **§4** — an erratum against `docs/design/04_2c_run_structure.md` §4.4, and the
   ratification of the implementation's reading.
4. **§5** — the report-back protocol.
5. **§6** — the clean-clone objective, restated so it can be evaluated.

**IT CREATES ONE NEW RULE AND ONLY ONE: THE PROTOCOL AT §5.** Everything else is
an amendment to a committed rule, a correction to a committed statement, or a
restatement of a committed objective.

### 1.1 WHAT IT DOES NOT DO

**IT DECIDES NOTHING ABOUT METRICS, LEVELS OR KILL CONDITIONS.** Those are 4.3's,
4.4's and 4.5's.

**IT DOES NOT DISPOSE OF THE `simulate.py` CAP DIVERGENCE.** §7 records that it is
open and why; it does not settle it.

**IT CHANGES NO CODE.** Every consequence for the code is named as owed to a code
step.

**IT COMPUTES NOTHING.** §0.2.

---

## 2. AMENDMENT: THE GRANDFATHERED READER SET

### 2.1 WHAT IS AMENDED, AND UNDER WHICH DISCIPLINE

`docs/design/04_2a_artifact_containment.md` §3.3 enumerates the existing readers
of the artifacts §3.1 covers, in two classes, and closes the set:

> **NO NEW READER JOINS EITHER CLASS WITHOUT AMENDING THIS DOCUMENT.**

**§8 OF THAT DOCUMENT STATES ITS CHANGE DISCIPLINE: a change to any commitment is
a new document with its own commit, never a silent edit.** It names its successor
as `docs/design/04_2a_artifact_containment_amendment_1.md`.

> ### **THIS DOCUMENT IS THAT AMENDMENT IN SUBSTANCE AND IS NOT NAMED AS ONE, AND
> ### THE DEPARTURE IS DISCLOSED RATHER THAN GLOSSED.** It carries four other
> ### closures that have nothing to do with containment, and splitting it would
> ### produce a one-line document. **A reader looking for
> ### `04_2a_artifact_containment_amendment_1.md` will not find it; §2 of this
> ### document is where it went.**

**`docs/design/04_2a_artifact_containment.md` IS NOT EDITED.** Its §3.3 stands as
written and as wrong.

### 2.2 THE AMENDED SET

> ### **CLASS TWO OF §3.3 IS FOUR TEST MODULES, NOT THREE:**
> ### `tests/test_sweep_prescreen.py`, `tests/test_sweep_run.py`,
> ### `tests/test_dispersion.py`, **AND `tests/test_sweep_bands.py`.**

**CLASS ONE IS UNCHANGED** — the sweep's own modules, reading their own outputs.

**THE SET REMAINS CLOSED ON THE SAME TERMS.** No fifth module joins without
amending this document.

### 2.3 THE CONSEQUENCE, STATED PLAINLY

**AN UNENUMERATED READER IS NOT A GRANDFATHERED READER.** §3.3's grandfathering
operates by extension — it names three modules — and
`docs/design/04_0_divergence_disposition_amendment_2.md` §7's drafting rule is
that a scope term inside a binding clause defined by extension is defined by the
list and by nothing else. **A module absent from the list was never inside it.**

> ### **THE READ PROHIBITION AT §3.2 HAS THEREFORE BEEN IN BREACH ON EVERY SUITE
> ### INVOCATION SINCE IT WAS COMMITTED.** From `3fa9d06` on 2026-08-17 until
> ### this commit, `tests/test_sweep_bands.py` opened three prohibited artifacts
> ### every time the suite ran, and no clause permitted it.

**THAT IS A BREACH OF A RULE THIS PROJECT WROTE, FOUND BY THE GUARD THE SAME
PROJECT BUILT.** It is stated in those words because the alternatives available —
that the set was "incomplete", that the reader was "not yet enumerated", that the
prohibition "had not been applied" — all describe the same facts while removing
the word that makes them assessable.

**AND THE GUARD IS THE REASON IT IS KNOWN.** `docs/design/04_2a_artifact_containment.md`
§3.6 committed the guard on the ground that **a rule enforced only by intention is
the shape of every defect in the ledger.** The guard was built, it ran, and the
first thing it found was that the document commissioning it was wrong about the
repository. **That is the guard working, not the guard failing**, and it is the
strongest available evidence for §3.6's own argument.

### 2.4 WHETHER THE BREACH REACHED ANYTHING

**ESTABLISHED FROM SOURCE, BY THE SAME METHOD AS §0.3.**

**THE READER EMITS NOTHING.** Every call in `tests/test_sweep_bands.py` that could
write was enumerated over `Call` nodes: **the only ones are two `json.dumps` at
`:317` and `:319`**, inside `test_the_written_artifact_matches_a_fresh_build`,
which serialise two in-memory structures so they can be compared to each other.
**There is no `open` in a write mode, no `dump`, no `to_csv`, no `to_json`, no
`to_parquet` and no `write`.** The module has 38 test functions and produces no
file.

**NO DOCUMENT CITES IT.** A search over `docs/` for `test_sweep_bands` returns
matches in **`docs/prompts/MANIFEST.md` only**, all written by the consolidated
code step reporting this finding. **No design document and no report names it.**

**AND NO DOCUMENT CITES THE REPORT IT UNDERPINS.** A search over `docs/` for
`15_band_selection` returns **no file at all.**

> ### **NOTHING REACHED ANYTHING. NO FIGURE FROM `bands.json` ENTERS A DOCUMENT,
> ### A DECISION OR A REPORT BY WAY OF THIS READER, AND THE READER IS STRUCTURALLY
> ### INCAPABLE OF CARRYING ONE, BECAUSE IT WRITES NOTHING.**

**A RULE BROKEN WITHOUT CONSEQUENCE IS STILL A RULE BROKEN.** The absence of a
consequence is a fact about this instance and not a property of the rule. The
prohibition exists because the consequence of the read that does matter is
irreversible, and a discipline that only registers breaches which happened to land
is a discipline that will register the one that lands too late.

### 2.5 WHAT THE GUARD SHOULD DO ABOUT IT

**TWO ANSWERS ARE AVAILABLE: GRANDFATHER THE FOURTH READER AS THE OTHER THREE
WERE, OR REQUIRE IT TO STOP READING.**

**THE ARGUMENT FOR REQUIRING IT TO STOP, STATED FIRST AND AT ITS FULL STRENGTH.**
§3.3's grandfathering is justified in one sentence: *"THE PROHIBITION BINDS FUTURE
READS. IT DOES NOT SILENTLY BREAK THE SUITE."* That justification is about not
retroactively breaking something the drafter **considered and chose to preserve**.
The fourth reader was never considered, so extending the permission to it is not
declining to break something — it is granting a permission the document never
granted. **And there is a channel: a failed assertion prints what it compared, so
a test that loads an artifact renders artifact-derived content into a human-readable
surface at the moment it fails.** That is not nothing; the run recorded at §6.3
produced several hundred lines of such output.

**THE ARGUMENT FOR GRANDFATHERING, AND IT IS THE ONE THAT HOLDS.**

**THE FOURTH READER IS IN THE IDENTICAL FACTUAL POSITION TO THE OTHER THREE.** It
predates the prohibition — 2026-08-09 against 2026-08-17. It reads on every
invocation. It fails rather than skips when its inputs are absent. It emits
nothing. No commitment consumes it. **On every criterion §3.3 could have applied,
it is indistinguishable from the three the document names.**

> ### **THE ONLY DIFFERENCE BETWEEN THE FOURTH READER AND THE OTHER THREE IS THAT
> ### AN AUDITOR SAW THREE AND MISSED ONE.** To grandfather three and forbid the
> ### fourth is to make the same conduct permitted or prohibited according to
> ### whether it was noticed. **That is not a distinction; it is the record of an
> ### error, promoted to a rule.**

**AND THE EMISSION CHANNEL DOES NOT DISCRIMINATE.** A failed assertion prints its
operands in `tests/test_dispersion.py` and `tests/test_sweep_run.py` exactly as it
does here. **The channel is a property of the whole class, not of the fourth
member**, so it is an argument about §7 item 5's question and not an argument for
treating this module differently from its three siblings.

> ### **DECIDED: THE FOURTH READER IS GRANDFATHERED, ON THE SAME GROUND AND WITH
> ### THE SAME RESERVATION AS THE OTHER THREE.**

**THE GROUND IS EQUAL TREATMENT, AND THE COST IS EXPLICITLY NOT THE GROUND.** It
is true that requiring this module to stop would disable 38 tests that pin the
band-selection machinery, and that is a real cost. **It is not why.** If the three
had been forbidden, the fourth would be forbidden here at whatever cost; the
question is what distinguishes it from them, and the answer is nothing.

**AND THE GRANDFATHERING IS PROVISIONAL, EXACTLY AS THEIRS IS.** §3.3 records that
whether the enumerated modules should continue to read these artifacts is **owed**,
at §7 item 5, and `docs/design/04_2b_point_4_decomposition.md` §5.1 records that
item 5 **must be settled before freeze precondition 5 at §4.3 can be evaluated.**

> ### **ITEM 5 NOW RANGES OVER FOUR MODULES, AND THE THREE ARGUMENTS ABOVE FOR
> ### REQUIRING A STOP TRAVEL TO IT INTACT.** They are arguments about the class.
> ### They are not spent by being rejected here as grounds for singling out one
> ### member of it.

### 2.6 WHAT THE CODE MUST DO, NAMED AS OWED

**`tests/test_containment_guard.py` CURRENTLY PINS THE FOURTH READER IN A LIST
NAMED `UNDECLARED_READERS`, ASSERTED AS EXACT**, precisely so that the gap stayed
visible until a document closed it. **This document closes it.**

**OWED TO A CODE STEP: move `tests/test_sweep_bands.py` from that list into the
grandfathered set, and cite this section as the amendment that admitted it.** The
exactness assertion is kept, so a fifth undeclared reader still fails the guard.
**No owner at this commit.**

---

## 3. ERRATUM: `docs/handoff/41_point_4_2_artifact_audit.md` §4.1

### 3.1 THE ENTRY, IN THE CONSOLIDATED INDEX'S FORM

**ENTRY 11. Report 41 §4.1 — the forward enumeration of readers.**
*Target: evidence.* **SAID:** `bands.json` is *"written by `src/sweep/bands.py`;
**no reader found**"*, and `sweep.json` and `sweep_cells.jsonl` are read by
`src/sweep/bands.py`, `src/sweep/sweep_report.py` and `tests/test_sweep_run.py`.
**CORRECT:** `tests/test_sweep_bands.py` reads `bands.json` at six call sites,
reads `sweep_cells.jsonl` through its `cells` fixture, and reads the sweep trade
tables through `src/sweep/bands.py`'s diagnostics — all on every suite invocation,
none of it skippable, and all of it committed at `68e5b16` on 2026-08-09, eight
days before the audit. **The module is absent from §4.1 entirely, not merely from
one of its lines.** **CORRECTION LIVES AT:** this document, §3. **Operative** —
`docs/design/04_2a_artifact_containment.md` §3.3 built its closed set from this
enumeration and is wrong in consequence; §2 above amends the set.

### 3.2 THE MAINTENANCE RULE IS OBEYED AND THE GAP IT LEAVES IS RESTATED

**`docs/design/04_1c_pre_commitments.md` §5.4 REQUIRES THE ENTRY IN THE SAME
COMMIT AS THE CORRECTION.** It is here.

**THE INDEX ITSELF IS FROZEN AND CANNOT BE EDITED**, which
`docs/design/04_1d_standing_practices.md` §4.2 records as a gap the maintenance
rule did not anticipate, and `docs/design/04_1c_consequences_and_thresholds.md`
§5.5 restates.

> ### **THE INDEX STANDS AT NINE ENTRIES IN ITS OWN TEXT AND AT TWELVE IN FACT** —
> ### nine at `docs/design/04_1c_pre_commitments.md` §5, entry 10 at
> ### `docs/design/04_1d_standing_practices.md` §4.1, and **entries 11 and 12 at
> ### §3 and §4 of this document.** THE NEXT DOCUMENT TO HOLD THE INDEX CARRIES
> ### TWELVE FORWARD.

### 3.3 WHAT DOES NOT FOLLOW: THE VERDICT IS UNDISTURBED

**REPORT 41 §6 RETURNED **NO BREACH**, AND THE QUESTION IS WHETHER AN OMITTED
READER DISTURBS IT. IT DOES NOT, AND THE REASON IS STRUCTURAL RATHER THAN
ARITHMETIC.**

**THE VERDICT DOES NOT REST ON §4.1.** §4.1 is a **forward** trace — from each
artifact to whatever opens it. §4.2 is a **backward** trace — from every Point 4
and Point 5 commitment, asking whether any of them consumes a figure from any of
these artifacts. **The verdict is the backward trace's.** A forward trace that
misses a consumer weakens the claim "these are all the consumers"; it cannot by
itself create a consumer of a commitment, because the backward trace starts from
the commitments and not from the files.

**AND THE OMITTED READER CANNOT APPEAR IN THE BACKWARD TRACE, FOR A REASON THAT
DOES NOT DEPEND ON ANYONE HAVING LOOKED.** §2.4 establishes over the AST that the
module **writes no file at all.** A module that emits nothing cannot be a link in a
chain from an artifact to a commitment. **The backward trace would return the same
answer had §4.1 named it.**

**THE BACKWARD TRACE WAS ALSO INDEPENDENTLY RE-RUN HERE, AND IT HOLDS.** A search
over `docs/` for the module returns `docs/prompts/MANIFEST.md` alone; a search for
the report rendered from `bands.json` returns nothing. **One further file names
`bands.json`** — `docs/handoff/16_point_4_closing.md`, the **superseded** Point 4's
closing record — and it names it in a commit table and in a step instruction, **as
a filename and not as a figure.** §4.2's claim is that no Point 4 or Point 5
document **cites a figure from** these artifacts, and that claim survives.

> ### **THE VERDICT IS ROBUST TO THE OMISSION BECAUSE THE OMISSION IS IN THE TRACE
> ### THE VERDICT DOES NOT REST ON, AND BECAUSE THE OMITTED ITEM IS OF A KIND THAT
> ### THE TRACE IT DOES REST ON CANNOT REACH.**

**WHAT IS DAMAGED IS NARROWER AND IS STATED.** §4.1's completeness claim is false,
and every downstream use of it as a **closed enumeration** — which is exactly what
`docs/design/04_2a_artifact_containment.md` §3.3 made of it — is unsound. **That
is the whole of the damage, and §2 repairs it.**

---

## 4. ERRATUM: `docs/design/04_2c_run_structure.md` §4.4

### 4.1 THE CLAIM, VERIFIED AGAINST THE CODE

**§4.4 STATES:** *"`exposure_profile.max_hold_exit` (`src/analysis/exposure_profile.py:234`)
returns the third funding settlement after the entry close **unconditionally**. It
applies no clamp to the end of the bar frame. `positions` writes that stamp to
`exit_bar_ts` (`:352`, column list at `:346-349`)."*

**THE FIRST TWO SENTENCES ARE CORRECT. THE THIRD IS NOT.** Read from the AST of
`src/analysis/exposure_profile.py`, the body of `max_hold_exit` is:

```
entry_close = bar_close_ms(signal_bar_ts)
settlement  = nth_settlement_after(entry_close, n)
exit_close  = settlement
exit_bar    = exit_close - BAR_MS
return (exit_bar, exit_close, exit_close - entry_close)
```

and `positions` unpacks it at `:385` as `exit_bar, exit_close, hold`, writing
`row['exit_bar_ts'] = int(exit_bar)` and `row['exit_close_ms'] = int(exit_close)`.

**AND ON A STAMP, WITH NO DATA READ:** for a signal bar at 2024-12-31T22:00Z,
`max_hold_exit` returns `exit_bar_ts` = 2025-01-01T15:00Z and `exit_close_ms` =
2025-01-01T16:00Z. **`nth_settlement_after(bar_close_ms(ts))` equals `exit_close_ms`
and does not equal `exit_bar_ts`; the two differ by 3,600,000 ms, exactly one
hour.**

> ### **THE THIRD FUNDING SETTLEMENT IS WRITTEN TO `exit_close_ms`. `exit_bar_ts`
> ### IS THAT SETTLEMENT MINUS ONE BAR — THE OPEN OF THE BAR THE EXIT HAPPENS ON,
> ### NOT THE INSTANT OF THE EXIT.**

**THE CITED LINE NUMBER IS ALSO OFF.** §4.4 cites `:352` for the write; the unpack
is at `:385` and the column tuple `POSITION_COLUMNS` is at `:346-349`, which is the
part of the citation that is right.

### 4.2 THE ENTRY, IN THE CONSOLIDATED INDEX'S FORM

**ENTRY 12. `docs/design/04_2c_run_structure.md` §4.4 — which column carries the
scheduled exit.** *Target: specification.* **SAID:** `positions` writes the third
funding settlement to `exit_bar_ts`, at `:352`. **CORRECT:** it writes it to
`exit_close_ms`; `exit_bar_ts` carries that settlement minus one bar period, and
the unpack is at `:385`. **CORRECTION LIVES AT:** this document, §4. **Not
operative as to the rule, operative as to the implementation instruction** — see
§4.3 and §4.4.

### 4.3 THE COMMITTED RULE IS UNAFFECTED

**THE RULE AT §4.4 AND §4.5 IS STATED IN TERMS OF THE SCHEDULED MAX-HOLD EXIT, NOT
IN TERMS OF A COLUMN NAME:**

> **A CANDIDATE IS EVALUATED ONLY IF ITS SCHEDULED MAX-HOLD EXIT FALLS STRICTLY
> BEFORE THE HOLDOUT SEAL. ONE WHOSE SCHEDULED EXIT FALLS AT OR AFTER IT IS
> EXCLUDED, AND EXCLUDED BEFORE ANY 1m BAR IS REQUESTED ON ITS BEHALF.**

**AND §4.4 IDENTIFIES THE SCHEDULED MAX-HOLD EXIT TWICE, INDEPENDENTLY OF THE
COLUMN CLAIM:** once as *"the third funding settlement after the entry close"*, and
once in *"an entry at the last in-sample bar's close has its third settlement in
2025."*

> ### **THE RULE NAMES AN EVENT. THE ERRATUM CORRECTS A CLAIM ABOUT WHICH COLUMN
> ### CARRIES THAT EVENT'S TIMESTAMP. THE EVENT IS THE SAME EVENT BEFORE AND
> ### AFTER THE CORRECTION.**

**NOTHING IN §4.5's SIX-POINT STATEMENT OF THE POPULATION MOVES**, and nothing in
`docs/design/04_2d_aggregation.md` §7.2's adoption of the count moves either.

### 4.4 THE IMPLEMENTATION'S READING, RATIFIED

**WHAT WAS IMPLEMENTED.** `src/engine/portfolio.py` tests `exit_close_ms >= seal`.
Over the candidate population that excludes **11** candidates where a test on
`exit_bar_ts` would exclude **10**; the difference is the single candidate whose
scheduled exit falls **exactly on** the boundary instant.

**WHICH READING DOES THE RULE REQUIRE? `exit_close_ms`.** The rule's subject is the
scheduled max-hold exit, §4.4 identifies that with the third funding settlement,
and §4.1 above establishes from the code that the third funding settlement is
`exit_close_ms`. **The column claim was the only thing pointing the other way, and
it is the thing that is wrong.**

> ### **THE IMPLEMENTATION MATCHES THE RULE. IT IS RATIFIED.**

**IS THE BOUNDARY INSTANT ITSELF AMBIGUOUS? NO, AND THE ANSWER IS IN THE RULE'S OWN
WORDS.** *"Strictly before"* on the admitting side and *"at or after"* on the
excluding side is an explicit disposition of the boundary instant: **an exit landing
exactly on the seal is excluded.** The apparent ambiguity was never about the
comparison; it was about which of two stamps the comparison ranges over, and §4.1
settles that.

**THE CONSEQUENCE IS RECORDED RATHER THAN LEFT TO BE REDISCOVERED.** The seal falls
on a funding settlement instant, so a scheduled exit lands exactly on it and the
case is reachable — it is reached by exactly one candidate. **That candidate needs
no sealed minute**: its 1m walk ends one minute before the seal. **The rule
excludes it anyway, and that is the rule working as written rather than a defect.**
§4.4 states in terms that the scheduled exit is *"the conservative bound"* and that
a position resolving earlier *"would not have needed the sealed hours, but that is
not knowable at the decision"*. **Over-exclusion at the boundary instant uses no
future information; the alternative requires knowing an outcome.**

---

## 5. THE REPORT-BACK PROTOCOL

### 5.1 WHY

**`docs/handoff/23_point_1_reopened_closing.md` §5.1 RECORDS FIVE TRANSFER DEFECTS
IN SIX RETURNS** — content duplication, section misordering, silent truncation,
and **an entirely different report delivered under a correct commit hash.** It
committed the read-back protocol: artifacts under review move by **file upload**,
and the chat carries **SHA-256, line count, commit hash and test count** only.
`docs/handoff/31_point_5_closing.md` §13 carried it over unchanged, and §12.2 adds
the observation that **the verified path held and the unverified path broke,
repeatedly, in the same point.**

**THE PROTOCOL COVERED THE ARTIFACT UNDER REVIEW. IT DID NOT COVER THE ACCOUNT OF
THE WORK.** A report-back has been a paste, every time, and §0.3 above records the
most recent instance of a paste being incomplete in a way only an independent check
would find.

> ### **A HASHED COMMITTED FILE IS VERIFIABLE. A PASTED ACCOUNT IS NOT.** THE
> ### REPORT-BACK IS AN ARTIFACT AND IS TREATED AS ONE.

### 5.2 THE RULE, COMMITTED

> ### **A STEP'S REPORT-BACK IS WRITTEN TO A FILE AND COMMITTED IN THE SAME COMMIT
> ### AS THE STEP IT REPORTS. THE CHAT CHANNEL CARRIES THE FILE'S PATH, ITS
> ### SHA-256, ITS LINE COUNT, THE COMMIT HASH AND THE TEST COUNT — AND
> ### DISCUSSION. IT CARRIES NO OTHER ACCOUNT OF THE WORK.**

**WHERE THEY LIVE: `docs/handoff/`.** A report-back records what a step did. Under
`docs/design/04_0_divergence_disposition_amendment_2.md` §2 and the filing ground
at `docs/handoff/33_point_4_1a_revised_derivation.md`'s preamble, **a record of
what happened is evidence and not specification**, and filing it under
`docs/design/` would enrol an execution record in the frozen specification.

**HOW THEY ARE NAMED: `docs/handoff/NN_<slug>.md`, in the existing numeric
sequence, `NN` being the next unused integer.** One sequence and not two, because
`docs/prompts/MANIFEST.md` already indexes every report under one numbering and a
second sequence would produce two documents entitled to be called "report 42".

**THE GENRE IS DECLARED IN THE DOCUMENT'S FIRST SECTION** — a step report-back, or
an analysis report. That is what keeps the shared sequence readable: the
distinction is carried by the document rather than by a directory.

**THE MANIFEST ENTRY IS APPENDED IN THE SAME COMMIT**, by that file's own
maintenance rule.

### 5.3 THE THIRD EXEMPTION TO THE SINGLE-FILE RULE

**`docs/design/04_1d_standing_practices.md` §1.3 CREATES THE SINGLE-FILE RULE AND
TWO EXEMPTIONS — `docs/prompts/MANIFEST.md` and the consolidated errata index.**

> ### **A THIRD IS CREATED HERE: THE STEP'S OWN REPORT-BACK FILE.**

**WITHOUT IT THE PROTOCOL IS UNSATISFIABLE.** §5.2 requires the report-back in the
same commit as the step; the single-file rule permits one file per step. **A rule
that cannot be obeyed alongside a rule already committed is a defect in the newer
rule**, and the exemption is the minimum that removes it.

**IT IS NARROW.** The exemption covers exactly one file per step, at the path §5.2
prescribes, containing the report-back and nothing else.

### 5.4 THE PRE-FREEZE RULE, COMMITTED IN FULL

**BEFORE THE FREEZE, NO OUTCOME QUANTITY EXISTS**, per
`docs/handoff/31_point_5_closing.md` §11. **A committed report-back therefore
cannot contain one**, and the rule at §5.2 is committed **without qualification**
for every step up to and including the freeze.

**WHAT A PRE-FREEZE REPORT-BACK MAY CONTAIN**, stated by a principle followed by an
explicit illustration, per
`docs/design/04_0_divergence_disposition_amendment_2.md` §7: **anything the
firewall already permits a committed document to contain.** Including without
limitation: counts of candidates, of exclusions, of positions, of skips and of
tests; hashes, line counts, commit hashes and paths; timestamps and calendar
arithmetic; statements of what was verified and how; contradictions found, stated
and unresolved; and items left open.

**AND ONE OBLIGATION THAT IS NEW ONLY IN ITS PLACEMENT.** A report-back states
**any place where a requirement contradicted a constraint, stated rather than
resolved**, and **anything readable as narrower or broader than intended.** Those
two closing items are practice that `docs/prompts/STANDING_RULES.md` §12.5 records
as committed nowhere. **They are committed here, for report-backs.**

### 5.5 THE POST-FREEZE QUESTION, ROUTED AND NOT SETTLED

**AFTER THE FREEZE A REPORT-BACK CAN CONTAIN AN OUTCOME FIGURE**, and a committed
report-back that does is **a committed artifact containing outcome quantities** —
which is the precise object `docs/handoff/41_point_4_2_artifact_audit.md` was
written to adjudicate, and the precise object
`docs/design/04_2a_artifact_containment.md` §3.2 prohibits opening.

> ### **THE PROTOCOL AT §5.2 WOULD, UNMODIFIED, MANUFACTURE THE ARTIFACTS THIS
> ### CHAIN HAS SPENT TWO DOCUMENTS CONTAINING.**

**IT IS NOT SETTLED HERE.** A rule committed now for a regime whose contents are
unknown would be written from a mental model of them, which is the ledger's
recurring class.

**ROUTED TO ITS OWN DOCUMENT**, and the choice among the three candidates is
argued rather than asserted:

- **NOT `docs/design/04_2d_aggregation.md` §7.** That section commits **what must
  be reported**, and §7.1 states in terms that **every obligation in it is a count
  and not an outcome quantity.** It disclaims the subject matter.
- **NOT 4.6's FIRST-RUN DIAGNOSTIC GATE.** 4.6 owes the gate, the order of
  inspection and the response to each kind of failure —
  `docs/design/04_2b_point_4_decomposition.md` §3.3. Those are questions about
  **what is looked at and in what order.** This is a question about **what may be
  written down and committed**, which is a different genus.
- **ITS OWN DOCUMENT**, on the precedent
  `docs/design/04_2b_point_4_decomposition.md` §5.1 sets for item 5: that item was
  detached from every sub-point on the ground that it is **a firewall question, not
  a validation-design one.** This is the same genus and takes the same route.

**ITS DEADLINE IS NOT THE FREEZE.** It must be settled **before the first
post-freeze report-back is written**, which is later and is the moment the question
first bites. **No owner at this commit.**

---

## 6. THE RESTATED CLEAN-CLONE OBJECTIVE

### 6.1 THE OBJECTIVE WAS UNACHIEVABLE AS WRITTEN

**`docs/design/04_2b_point_4_decomposition.md` §5.1 REQUIRES OF THE CONSOLIDATED
CODE STEP:**

> **THAT STEP MUST ACHIEVE: A CLEAN CLONE BUILDS AND THE SUITE PASSES.**

**NO CLEAN CLONE CAN PASS, AND NOT BECAUSE OF ANYTHING THE STEP DID OR OMITTED.**
The suite requires a derived market-data layer of roughly **985 MB**, built by
`src/data/build_derived.py` from an immutable raw layer that is itself fetched from
the venue's API. **Neither is tracked, and `.gitignore` records the deliberate
reasoning for tracking a handful of provability artifacts and nothing else.**
Tracking a bar layer is not a thing anyone proposes; the objective simply did not
notice that it required one.

> ### **THAT IS A DEFECT IN THE OBJECTIVE, NOT A FAILURE OF THE STEP.** An
> ### objective no execution can satisfy cannot be used to judge an execution.

**AND `docs/design/04_2a_artifact_containment.md` §3.5 MISATTRIBUTES THE CAUSE.**
Its consequence 1 states that the suite is not reproducible from the repository
alone **because `sweep_cells.jsonl` is not in it.** That file is one of several
absent inputs and by a wide margin the smallest. **The bar layer is the binding
constraint and always was.** Recorded as a correction of emphasis rather than as an
erratum: §3.5's statement is true, its implied sufficiency is not, and no entry is
added for an implication.

### 6.2 THE OBJECTIVE, RESTATED SO IT CAN BE EVALUATED

> ### **WHAT MUST BE PRESENT.** A clone of the repository at the commit under
> ### test, **plus** the derived market-data layer produced by
> ### `src/data/build_derived.py`. The data layer is an **environment
> ### precondition**, not a repository property, and its absence is never a
> ### finding about the commit.
>
> ### **WHAT MUST BUILD.** The dependencies at `requirements.txt`, plus the test
> ### runner, into a fresh interpreter environment, with no step that is not
> ### recorded in a file in the repository.
>
> ### **WHAT MUST PASS.** Every test whose inputs are either tracked or derivable
> ### from the data layer.
>
> ### **WHAT MAY LEGITIMATELY SKIP.** Every test whose subject is an
> ### **outcome-bearing artifact the repository is forbidden to carry** and which
> ### is absent from the environment — and it must skip **loudly**, naming the
> ### artifact, the document that forbids tracking it, and how to regenerate it.
>
> ### **WHAT MAY LEGITIMATELY FAIL. NOTHING.** A failure is never legitimate. The
> ### skip category exists precisely so that absence has an expression that is not
> ### failure.

**THE ASYMMETRY BETWEEN SKIP AND FAIL IS THE WHOLE OF THE RESTATEMENT.** The
original objective had one category and so was satisfiable only by an environment
nobody can construct. **Two categories make it evaluable**, and the second is
bounded by a rule — an artifact the repository is *forbidden* to carry, not merely
one that is *absent* — so it cannot be widened by anyone who finds a failing test
inconvenient.

### 6.3 THE MEASURED RESULTS, AND WHICH ONE WOULD MEET IT

**THREE RUNS ARE ON RECORD AT `docs/prompts/MANIFEST.md` §5.3**, on a clone of
`e844cf7` at a fresh path:

1. **CLONE ALONE: 1,133 passed, 70 failed, 99 errors.** Fails §6.2 on **what must
   be present** — the environment precondition is unmet, so the run does not
   evaluate the objective at all.
2. **CLONE PLUS THE FULL DATA LAYER: 1,377 passed, 1 failed.** Fails §6.2 on **what
   may legitimately fail: nothing.**
3. **CLONE PLUS THE DATA LAYER WITHOUT THE SWEEP'S UNTRACKED OUTPUTS — the state a
   build actually produces: 1,362 passed, 3 skipped, 2 failed, 11 errors.** The
   three skips are `tests/test_sweep_run.py` and are exactly the legitimate
   category. **Fails on the 2 failures and 11 errors.**

> ### **RUN 3 IS THE ONE THAT WOULD CONSTITUTE MEETING THE RESTATED OBJECTIVE,
> ### AND IT MEETS IT ONLY WHEN ITS FAILURES AND ERRORS REACH ZERO.** Run 2 is not
> ### the target: an environment that happens to hold artifacts a build does not
> ### produce is not the environment the objective is about.

### 6.4 THE UNRECORDED STEP

**`requirements.txt` LISTS `requests`, `pandas` AND `pyarrow`. IT DOES NOT LIST THE
TEST RUNNER.** "Build, then run the suite" therefore has a step that no file in the
repository records, and the clone runs above required it to be supplied from
outside.

**STATED, NOT FIXED.** Adding it is a code step and not this document's. **No owner
at this commit.**

### 6.5 IS THE RESTATED OBJECTIVE MET? NO, AND WHAT REMAINS IS ONE MODULE

**EVERY FAILURE AND EVERY ERROR IN RUN 3 IS `tests/test_sweep_bands.py`** — the
module §2 has just admitted to the grandfathered set. **It carries two distinct
defects and they need different repairs.**

**(a) IT FAILS RATHER THAN SKIPS WHEN ITS UNTRACKED INPUTS ARE ABSENT** — 11 errors
and 1 failure. **This is the same defect `docs/design/04_2a_artifact_containment.md`
§3.5 identifies and §7 item 4 routes, in a module §3.5 did not know was a reader.**
Its repair is the one already applied to `tests/test_sweep_run.py`: skip on absence,
loudly, naming the artifact. **Owed to a code step. No owner at this commit.**

**(b) `test_the_committed_report_matches_a_render_of_the_committed_artifact` FAILS
WHEREVER THE REPOSITORY IS NOT AT THE PATH THE ARTIFACT WAS WRITTEN AT** — 1
failure, present in run 2 as well as run 3. **Established from source and with no
artifact opened:** `src/sweep/bands.py:708` records an **absolute** path into its
payload, and `:840` renders it as `os.path.relpath(p['cells_path'], sch.ROOT)`. The
rendered value equals the committed report's only when `ROOT` is what it was when
the payload was written.

**DOES (b) BLOCK THE OBJECTIVE? YES.** It fails with every input present, so no
environment precondition explains it and no skip can express it. **It is a genuine
failure under §6.2 and the objective is not met while it stands.**

**AND IT IS SEPARATELY ROUTED, BECAUSE ITS REPAIRS ARE DECISIONS AND NOT
MECHANICS.** The three available are: change what a module declared dead relative
to the frozen thesis writes; regenerate a tracked outcome-bearing artifact;
or weaken a pin that exists to prove a committed report matches its inputs. **None
is settled by any committed document, and this document does not settle it.** It is
listed at §7.3. **No owner at this commit.**

---

## 7. WHAT REMAINS OPEN, AND THE INSTRUCTION DEFECT

### 7.1 THE DEFECT

**`docs/design/04_2b_point_4_decomposition.md` §5.1 DIRECTS FIVE ITEMS TO THE
CONSOLIDATED CODE STEP:** the mechanical guard (item 2), the carve-out's recording
in source (item 3), `sweep_cells.jsonl`'s reproducibility repair (item 4), **the
`simulate.py` cap divergence (item 6)**, and the directory markers (item 1, which
§5.1 flags as its own addition rather than the owner's direction).

**THE INSTRUCTION THAT PRODUCED THAT STEP NAMED FOUR: items 2, 3, 4 and 1.** It
**dropped item 6.**

**THE CONSEQUENCE IS NOT COSMETIC.** Freeze precondition 3 at
`docs/design/04_2b_point_4_decomposition.md` §4.3 requires that **the specification
and the implementation do not diverge in any known respect**, and names the
`simulate.py` cap divergence as the one known open case, citing
`docs/design/04_1g_cap_adoption.md` §5.

> ### **FREEZE PRECONDITION 3 IS CLOSED AS TO THE SEAL-CROSSING EXCLUSION AND
> ### **OPEN** AS TO THE CAP.** A precondition recorded as being cleared was
> ### cleared in part.

### 7.2 INSTANCE (52)

**AN INSTRUCTION TRANSCRIBED A COMMITTED REGISTER INCOMPLETELY, DROPPING ONE OF
FIVE ASSIGNED ITEMS, SO A FREEZE PRECONDITION RECORDED AS BEING CLEARED WAS CLEARED
IN PART.**

**THE TOTAL, READ.** `docs/design/04_2d_aggregation.md` §9.3 states **51**. The
instance below takes **(52)**.

**SUB-CLASS: instance (50)'s and instance (51)'s** — a statement about what a
document says, written from a mental model of it rather than from the document —
**which is itself the recurring class applied to a citation**, per
`docs/design/04_1c_denominator_choice.md` §5.5 on instance (43).

**WHAT DISTINGUISHES IT FROM ITS TWO PREDECESSORS, STATED SO THE THREE CAN BE
CHECKED FOR CONSISTENCY.** (50) attributed a count to a document that declares
none. (51) cited a section that does not exist. **This one cites a register that
does exist, at the right document and the right section, and transcribes four of
its five members.** The citation is correct; the **enumeration under it** is short
by one.

> ### **A PARTIAL TRANSCRIPTION IS THE HARDEST OF THE THREE TO CATCH, BECAUSE
> ### EVERYTHING PRESENT IS RIGHT.** (50) and (51) both fail on inspection of the
> ### cited text. This one passes inspection of everything it says and fails only
> ### on what it does not say.

**IT MEETS `docs/design/04_1a_denomination.md` §6's INCLUSION CRITERION.** The
remediation on offer — executing the four named items and reporting the step
complete — **would have degraded an otherwise correct artifact**, by recording a
freeze precondition as cleared when it was not. **The implementing session did not
adopt it**: the code step's own report named item 6 as unaddressed and stated that
precondition 3 remained open as to the cap. **The error was caught at execution and
is logged at the document that closes the step.**

**AND THE RATE IS NOW WORTH RESTATING.** This is the fourth citation or
transcription error carried by an instruction into this chain, and **three of the
four fall in consecutive steps.** The pattern
`docs/design/04_2b_point_4_decomposition.md` §7.2 names holds without amendment:
**an instruction's factual claims about the repository are not evidence about the
repository.**

### 7.3 THE TOTAL

**51 + 1 = 52.**

**No earlier instance is renumbered or recounted**, and the ledger remains
contiguous from (1) to (52).

### 7.4 THE OPEN ITEMS

**RECORDED IN THE FORM `docs/design/04_2b_point_4_decomposition.md` §5 USES. THAT
DOCUMENT IS NOT EDITED.**

**CARRIED FROM `docs/design/04_2a_artifact_containment.md` §7:**

- **ITEM 6 — THE `simulate.py` CAP DIVERGENCE.** `docs/design/04_1g_cap_adoption.md`
  §5 records that the module still applies a cap the specification has retired.
  Directed to the consolidated code step by §5.1, **omitted from the instruction
  that produced it, and not executed.** It bears on **freeze precondition 3** and
  must be closed, or §4.4's third option invoked, before 4.7. **No owner at this
  commit.**
- **ITEM 5 — WHETHER THE GRANDFATHERED TEST MODULES SHOULD KEEP READING
  OUTCOME-BEARING ARTIFACTS ON EVERY INVOCATION.** **Now four modules**, per §2.2.
  §2.5's three arguments for requiring a stop travel to it intact. It bears on
  **freeze precondition 5**. **No owner at this commit.**
- **ITEM 7 — the placeholder pair at `docs/design/04_2b_point_4_decomposition.md`
  §5.3.** Unmoved. **No owner at this commit.**

**SURFACED BY THE CONSOLIDATED CODE STEP AND NOT YET DISPOSED:**

- **THE RECONCILIATION OF `docs/handoff/26_point_5_2_budget_cost.md`.** Under the
  exclusion now implemented, the counts that record rest on move: **6,021 taken
  becomes 6,015 and 5,363 skipped becomes 5,358**, over an evaluated population of
  11,373 rather than 11,384. **These are counts and not outcome quantities**, per
  `docs/design/04_2d_aggregation.md` §7.1. **The report is not falsified** — it
  describes a population the specification no longer admits, and
  `src/analysis/budget_cost.py`, which produced it, is untouched and still
  reproduces it. **Whether it is re-measured or corrected by erratum is disposed by
  no committed document and is not disposed here.** **No owner at this commit.**
- **THE PRE-EXISTING AGGREGATE UNDER THE FIXTURE CARVE-OUT.**
  `tests/test_determinism_golden.py` asserts `nunique() == 1` on a
  config-derived column of a live run. On the letter of
  `docs/design/04_2a_artifact_containment.md` §4.2(a) that is an aggregate over
  rows; in substance it reads no fixture row and no outcome column. **Pinned exactly
  by the guard — one module, one reduction, one column — and unsettled.** It belongs
  with item 5, being a question about the carve-out's scope rather than about the
  validation design. **No owner at this commit.**
- **THE ABSOLUTE PATH RECORDED IN `bands.json`.** §6.5(b). **Blocks the restated
  clean-clone objective.** **No owner at this commit.**
- **`tests/test_sweep_bands.py`'s SKIP REPAIR.** §6.5(a). Mechanical, and the same
  repair already applied to its sibling. **No owner at this commit.**
- **THE TEST RUNNER'S ABSENCE FROM `requirements.txt`.** §6.4. Mechanical. **No
  owner at this commit.**

**SURFACED BY THIS DOCUMENT:**

- **THE GUARD'S REGISTER UPDATE.** §2.6 — move the fourth reader out of the
  undeclared list and into the grandfathered set, citing §2.2. Mechanical, and
  required for the guard to state the amended rule rather than the superseded one.
  **No owner at this commit.**
- **THE POST-FREEZE REPORT-BACK QUESTION.** §5.5. **Routed to its own document**,
  due before the first post-freeze report-back is written. **No owner at this
  commit.**

**UNCHANGED AND CARRIED:** the two housekeeping items at
`docs/design/04_2b_point_4_decomposition.md` §5.5 — the standalone errata index,
**now at twelve entries in fact against nine in its own text**, and the
`docs/prompts/STANDING_RULES.md` amendment. **The four Point 6 obligations at §5.4
are unmoved and none is a freeze precondition.**

**NOTHING ELSE IN THE REGISTER MOVES.**

---

## 8. WHAT THIS DOCUMENT DOES NOT DO

**IT COMMITS NO METRIC, NO LEVEL AND NO KILL CONDITION.** 4.3's, 4.4's and 4.5's.

**IT DOES NOT DISPOSE OF THE CAP DIVERGENCE.** It records that the divergence is
open, that the instruction dropped it, and that a freeze precondition is open in
consequence. **It takes no position on what should be done about `simulate.py`.**

**IT DOES NOT DECIDE WHETHER THE FOUR GRANDFATHERED MODULES SHOULD CONTINUE TO
READ.** §2.5 decides only that the fourth is treated as the three are; item 5 is
where the class is decided.

**IT DOES NOT SETTLE THE POST-FREEZE REPORT-BACK REGIME.** §5.5 routes it and
states why settling it now would be the ledger's recurring class.

**IT RE-OPENS NO CLOSED FINDING.** `docs/handoff/41_point_4_2_artifact_audit.md`
§6's verdict stands, on the reasoning at §3.3 above.

**IT CHANGES NO CODE**, and every code consequence it names is listed at §7.4 with
no owner.

---

## 9. CHANGE DISCIPLINE

**A CHANGE TO ANY COMMITMENT HERE IS A NEW DOCUMENT WITH ITS OWN COMMIT AND AN
EXPLICIT STATEMENT OF WHAT CHANGED AND WHY — NEVER A SILENT EDIT.** It would be
`docs/design/04_2e_housekeeping_amendment_1.md`.

**THE CLAUSE MOST EXPOSED IS §5.2's.** It will first be inconvenient when a step is
small enough that writing a report-back file feels disproportionate to it, and the
temptation will be to paste "just this once". **The protocol exists because the
paste that broke things was also just this once, five times in six.**

**THE SECOND MOST EXPOSED IS §2.5's GRANDFATHERING.** It will be cited as
establishing that a test may read a prohibited artifact. **It establishes no such
thing.** It establishes that the fourth reader is treated as the three were, and it
records that whether any of the four may continue is open and must be settled
before the freeze.

---

**Committed alone with the manifest and this step's report-back. Five items
closed: the grandfathered reader set amended to four modules after an independent
AST check found six call sites and three artifacts where the report-back named one
of each; report 41 §4.1's enumeration corrected by erratum with its verdict shown
robust to the omission because the verdict rests on the backward trace and the
omitted item writes nothing; `docs/design/04_2c_run_structure.md` §4.4's column
claim corrected by erratum with the committed rule shown unaffected and the
implementation's reading ratified, the boundary instant found unambiguous and its
one over-excluded candidate recorded; the report-back protocol committed in full
for the pre-freeze regime with a third single-file exemption created to make it
satisfiable and the post-freeze question routed to its own document; and the
clean-clone objective restated in four evaluable parts after being found
unachievable as written, not met, and blocked by one module. Ledger 51 + 1 = 52,
the third citation-class instance in as many steps and the first that fails only on
what it omits. Errata index at twelve in fact against nine in its own text. Ten
items open, none with an owner. No metric, no level, no kill condition and no
disposition of the cap.**
