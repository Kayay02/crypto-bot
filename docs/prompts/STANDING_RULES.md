# STANDING RULES — A TRANSCRIPTION

## 0. WHAT THIS FILE IS

**A TRANSCRIPTION OF RULES ALREADY COMMITTED ELSEWHERE**, gathered so that
instructions can reference them rather than restate them. Restatement in every
instruction has been the direct cause of four logged defects in which an
instruction contradicted its own constraints.

> ### THIS FILE CREATES NO RULE.

**WHERE THIS FILE AND A SOURCE DOCUMENT DIFFER, THE SOURCE GOVERNS**, and the
difference is a defect in this file to be reported.

**IT IS AMENDED BY A NEW FILE, NEVER SILENTLY EDITED.** It would be
`docs/prompts/STANDING_RULES_amendment_1.md`.

**NOTHING HERE IS TIGHTENED, EXTENDED, CLARIFIED OR COMPLETED.** Where a source's
wording is loose or ambiguous, the looseness is preserved and noted, because every
frozen document was written against the loose version. This is the discipline
`docs/design/00_standing_brief.md` §1 records for itself.

**§12 LISTS THINGS THAT LOOK LIKE RULES BUT ARE COMMITTED NOWHERE.** They are not
binding.

### 0.1 THE PERMITTED BANNED-TOKEN OCCURRENCES

**THIS FILE CONTAINS THE BANNED NAMES, WHICH IS UNAVOIDABLE IN A FILE WHOSE
PURPOSE IS TO STATE WHAT THEY ARE.** They occur in exactly four places, all of them
required by what this file must transcribe:

- **§1.1**, quoting `docs/handoff/31_point_5_closing.md` §11's statement of what
  the firewall forbids, in that record's own words;
- **§1.2**, listing the enforced twelve-name set;
- **§1.2 again**, naming the three names the nine-name variant omits, which is what
  makes the divergence statable;
- **§12.2**, naming the known substring collision, which cannot be named without
  writing the colliding word.

> **A CHECK FINDING THOSE TOKENS IN THOSE FOUR PLACES HAS FOUND THE LIST, NOT A
> VIOLATION. NO OTHER OCCURRENCE IN THIS FILE IS PERMITTED.**

**THE INSTRUCTION THAT PRODUCED THIS FILE PERMITTED ONE OCCURRENCE AND REQUIRED
FOUR.** The tension is recorded here rather than resolved by dropping any of the
four, since each is separately required. `docs/prompts/MANIFEST.md` contains none
of the tokens.

---

## 1. THE PERFORMANCE FIREWALL

### 1.1 WHAT IT FORBIDS

**Source: `docs/handoff/31_point_5_closing.md` §11.**

> **NO WIN RATE, EXPECTANCY, PROFIT FACTOR, SHARPE, SORTINO, EQUITY CURVE,
> DRAWDOWN, `r_multiple`, `net_pnl` OR `gross_pnl` FIGURE EXISTS ANYWHERE IN THIS
> REPOSITORY FOR THIS THESIS.**

No such quantity may be computed, inspected or estimated. That record adds, at
§10: it must not be computed **to check the engine works; not on one symbol; not
on one fold; not on one day.**

### 1.2 THE BANNED NAMES — AND THE TWO LISTS DIVERGE

**THE ENFORCED LIST**, from the AST guards, described at `tests/test_budget_cost.py`
as *"Report 25's twelve-name list. It only ever grows"*:

`expectancy`, `win_rate`, `winrate`, `profit_factor`, `sharpe`, `sortino`,
`net_pnl`, `gross_pnl`, `drawdown`, `r_multiple`, `equity`, `pnl`.

> ### DIVERGENCE, REPORTED AND NOT RECONCILED.

**FOUR TEST MODULES CARRY A NINE-NAME VARIANT** omitting `sortino`, `gross_pnl`
and `drawdown`: `test_exposure_profile.py`, `test_rsi_breakout_profile.py`,
`test_sweep_population.py`, `test_timeframe_resample.py`. **Fourteen modules carry
the twelve-name list.** Both are transcribed; neither is corrected here.

**AND THE PROSE STATEMENT DIVERGES FROM BOTH.** `docs/handoff/31_point_5_closing.md`
§11 names ten items and includes *"equity curve"* rather than `equity`, and *"win
rate"* rather than `win_rate` and `winrate`. **The prose and the guards are not the
same list.** Reported, not reconciled.

### 1.3 WHEN IT LIFTS

**Source: `docs/handoff/31_point_5_closing.md` §11 and §10.**

**When the validation design — Point 4 — is separately written, agreed and
committed.** That record states the design **must not run the engine in `full`
mode** and **must not open the holdout**, and that **the validation design is
committed before the first performance figure exists.**

### 1.4 IT IS ENFORCED BY COMMIT ORDER, NOT BY INFORMATION BARRIERS

**Source: `docs/design/04_0_decision_rule.md` §4.**

> **The guard against it is ORDER, not a threshold. It is the same mechanism as
> the performance firewall: the commit hash is the evidence, and it is evidence
> that survives everyone's account of what they were thinking.**

**WHAT WOULD FALSIFY THE CLAIM**, per §11: a commit at or before the stated hash
containing an outcome figure for this thesis, in a report, a document, a stored
artifact under `reports/`, or a committed data file.

---

## 2. THE HOLDOUT SEAL

### 2.1 THE SEALED WINDOW

**Source: `docs/design/05_aggregate_risk_budget.md` §, and identically in both its
amendments.**

> **THE HOLDOUT REMAINS SEALED AND UNSPENT. 2025-01-01 through 2026-07-26.**

The `year=2025` and `year=2026` partitions are the sealed ones.

**HOLDOUT BUDGET, per `docs/handoff/31_point_5_closing.md` §14: ONE CANDIDATE, ONE
LOOK, WHOLE WINDOW, NO CANDIDATE TWO.**

### 2.2 THE BARRIER IS ASSERTED IMMEDIATELY BEFORE EACH READ

**Source: `docs/handoff/29_point_5_3_3_1m_seal.md` §, the 5.3.3 breach account.**

That report records the failure that produced the rule: a filesystem barrier
*"was verified as armed at the start and was not re-verified before each mutation,
which is the procedural failure."* The barrier silently reverted mid-battery and a
mutated loader reached sealed partitions.

**THE REASON, IN THAT REPORT'S TERMS:** a barrier verified once per run is a claim
about the past, and the state it asserts can change without anything failing.

**AND THE RULE ADDED BY POINT 5**, per `docs/handoff/31_point_5_closing.md` §13:

> **A mutation that disables a pre-read guard never faces the real data
> directory.**

### 2.3 THE TWO DISCLOSURE OBLIGATIONS

**Source: `docs/design/04_0_divergence_disposition.md` §7.**

> **ANY WRITEUP OF HOLDOUT RESULTS MUST CARRY BOTH DISCLOSURES IN FULL**, and not
> by reference.

**THE FIRST**, from `docs/handoff/31_point_5_closing.md` §6.4: the 5.3.3 breach —
**what was opened, that no sealed value reached anyone, the adjudication and its
reasoning.**

**THE SECOND**, added by §7 because the first did not cover it, must state:

- **what was accessed: row counts only** — not the parquet footer's per-column
  minimum and maximum statistics, which would carry price information;
- **that row counts of a complete minute layer are calendar arithmetic and carry
  no price information**;
- **that the counts are recorded in `data/derived/_manifest.json`**;
- **that the channel was closed at sub-point 5.3.3.**

### 2.4 WHAT COUNTS AS A WRITEUP

**Source: `docs/design/04_0_divergence_disposition_amendment_1.md` §3, as extended
by `docs/design/04_0_divergence_disposition_amendment_2.md` §3.**

> **A WRITEUP IS ANY COMMUNICATION, IN ANY MEDIUM, THAT STATES OR CHARACTERISES A
> RESULT COMPUTED ON THE HOLDOUT WINDOW.** This includes a final report; an
> interim or partial report; a summary; **a single figure quoted in passing**; a
> commit message; a chat message or report-back; a verbal account; and **any
> artifact committed to this repository that contains such a figure.**

> **THE OBLIGATION ATTACHES TO THE FIRST SUCH COMMUNICATION AND TO EVERY ONE AFTER
> IT. IT IS NOT DISCHARGED BY HAVING DISCLOSED ONCE.**

> **WHERE A COMMUNICATION IS TOO SHORT TO CARRY BOTH DISCLOSURES IN FULL, THE
> CORRECT RESPONSE IS TO MAKE IT LONGER** — not to omit them, and not to
> substitute a reference.

**THE EXTENSION**, amendment 2 §3:

> **THE DISCLOSURE OBLIGATION ATTACHES EQUALLY TO ANY COMMUNICATION THAT STATES,
> CHARACTERISES, OR DECLINES TO STATE A RESULT COMPUTED ON THE HOLDOUT WINDOW, AND
> TO ANY COMMUNICATION ASSERTING THAT NO SUCH RESULT EXISTS, THAT THE HOLDOUT HAS
> NOT BEEN OPENED, OR THAT THE SEAL IS INTACT.**

---

## 3. THE FILING CONVENTIONS

### 3.1 DESIGN VERSUS HANDOFF

**Source: `docs/handoff/33_point_4_1a_revised_derivation.md`, preamble, and
`docs/design/04_0_divergence_disposition_amendment_2.md` §2.**

> **Design documents join the frozen specification on commit; a derivation does
> not, and filing it under `docs/design/` would enrol a measurement in the
> specification.**

Amendment 2 §2 states it from the other side: **reports under `docs/handoff/` that
record measurements rather than pre-register rules are EVIDENCE, NOT
SPECIFICATION.** They are cited, relied on, and corrected by erratum; they do not
bind. **Source code under `src/` is an IMPLEMENTATION of the specification and is
not a member.**

### 3.2 THE NAMING CONVENTION

**Source: `docs/design/04_1a_denomination.md` §8, and each subsequent document's
change-discipline section.**

**Amendments append `_amendment_N`, not a letter.** 4.1a §8 names its own successor
as `docs/design/04_1a_denomination_amendment_1.md`.

**NOTED AS AN INCONSISTENCY IN THE SOURCES, PRESERVED AND NOT CORRECTED:** the
Point 5 design documents use the letter form — `05a`, `05b`, `06a`. The
`_amendment_N` form is the Point 4 convention only.

### 3.3 THE FROZEN SPECIFICATION, BY EXTENSION

**Source: `docs/design/04_0_divergence_disposition_amendment_2.md` §2**, which
states the membership **as at that commit, not a closed set**:

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
- that document itself

> **THE LIST IS OPEN FORWARD. ANY DOCUMENT SUBSEQUENTLY COMMITTED AS A
> PRE-REGISTRATION UNDER THIS PROJECT'S DISCIPLINE JOINS THE FROZEN SPECIFICATION
> ON ITS COMMIT.** A reader who finds a pre-registration committed after that
> document must treat it as a member without waiting for the list to be reissued.

`docs/prompts/MANIFEST.md` records every subsequent member with its hash and
introducing commit.

---

## 4. THE ORDER AND DIRECTION RULES

**Source: `docs/design/04_0_decision_rule.md` §4.**

### 4.1 THE ORDER RULE

> **THE JUSTIFICATION FOR THE TOLERANCE MUST BE STATED AND COMMITTED IN ITS OWN
> COMMIT BEFORE STEP 3's CURVE IS EVALUATED AT ANY CANDIDATE VALUE OF THE
> TOLERANCE.**

**PRODUCING THE CURVE IS NOT EVALUATING IT.** What the order rule forbids is
**selecting a tolerance value after seeing the floor widths the candidate values
imply.**

### 4.2 THE DIRECTION RULE

> **THE TOLERANCE IS THE PRIMITIVE AND THE FLOOR IS DERIVED FROM IT. THE
> DERIVATION RUNS TOLERANCE TO FLOOR AND NEVER FLOOR TO TOLERANCE.**

It follows from the floor-shape commitment: the stop floor is **derived from the
cost algebra with no free parameter**, on the ground that **a floor stated as a
constant is a tunable parameter wearing a constraint's name.**

### 4.3 THE COST OF RE-MEASURING IS NOT A CONSIDERATION

**Source: `docs/design/04_0_decision_rule.md` §8.**

> **THE STANDING PRINCIPLE: EXECUTION REALITY OVER MEASUREMENT CONVENIENCE.**
>
> **THE COST OF RE-MEASURING IS NOT A CONSIDERATION IN THE BRANCH CHOICE.**

If a derivation implies that closed reports rest on a floor that does not enforce
what it was meant to, **that is a finding about the reports and not an argument
against the derivation.**

**NOTED, PRESERVED, NOT WIDENED:** §8 states this **of the branch choice.**
`docs/design/04_1c_level_method.md` §4.3 applied the same principle to a
specification bill, stating that it did so. **The source wording is narrower than
the use.**

---

## 5. THE DRAFTING RULES

### 5.1 SCOPE TERMS

**Source: `docs/design/04_0_divergence_disposition_amendment_2.md` §7.**

> **A SCOPE TERM INSIDE A BINDING CLAUSE IS DEFINED EITHER BY EXTENSION — AN
> EXPLICIT LIST OF DOCUMENTS, PATHS OR CASES — OR BY A STATED PRINCIPLE FOLLOWED BY
> AN EXPLICIT "INCLUDING WITHOUT LIMITATION" ILLUSTRATION. IT IS NEVER DEFINED BY
> EXAMPLE ALONE.**

**Adopted as standing for every subsequent document in this project.** The reason
given: **a clause written to be inconvenient later is read later by someone for
whom it is inconvenient, and a scope stated by example is read as narrowly as the
examples permit.**

### 5.2 PRE-STATING A DELEGATED VALUE

**Source: `docs/design/04_1b_tolerance_and_branch.md` §7.**

> **A PROMPT'S VERIFICATION OR STRUCTURAL CONSTRAINTS MUST NEVER PRE-STATE THE
> EXPECTED VALUE OF A QUANTITY WHOSE DETERMINATION THAT SAME PROMPT EXPLICITLY
> DELEGATES.**

**Stated as a prohibition on the drafting side rather than as a resolution
procedure on the implementing side**, because by the time the implementing session
meets it, both readings are already unsatisfiable and all it can do is report.

### 5.3 VERBATIM TRANSCRIPTION AND CONTENT CONSTRAINTS

> ### THIS IS NOT COMMITTED AS A STANDING RULE. SEE §12.1.

`docs/design/04_0_divergence_disposition_amendment_2.md` §6 logs **instance (33)**:
*"A PROMPT REQUIRING VERBATIM TRANSCRIPTION OF A SOURCE TEXT WHILE SEPARATELY
REQUIRING THAT A PHRASE CONTAINED IN THAT TEXT BE ABSENT FROM THE OUTPUT. The two
requirements are unsatisfiable together."*

`docs/design/04_1b_tolerance_and_branch.md` §7 groups it with §5.2's rule as
sharing one mechanism. **But §5.2's wording — pre-stating a delegated value — does
not reach it**, and no committed document states the verbatim case as a rule in its
own right. **Transcribed as a logged instance, not as a rule.**

### 5.4 THE COMMON SUB-CLASS

**Source: `docs/design/04_1b_tolerance_and_branch.md` §7**, citing
`docs/handoff/31_point_5_closing.md` §7.2:

**Internal contradiction between a prompt's own constraints and its
requirements** — instances (23) to (26), then (33), (35) and (39). **In each case a
requirement and a constraint referred to the same quantity and disagreed about who
determined it.**

**THE IMPLEMENTING SESSION REPORTS THE CONTRADICTION RATHER THAN RESOLVING IT.**
That is what every logged instance records the session as having done.

---

## 6. THE VERIFICATION RULES

### 6.1 SOURCE-TEXT CHECKS RUN OVER TOKENS OR AST NODES

**Source: `docs/design/04_1a_denomination_amendment_1.md` §7.**

> **ANY VERIFICATION CHECK THAT SEARCHES SOURCE TEXT RUNS OVER EXECUTABLE TOKENS OR
> AST NODES, NEVER OVER RAW TEXT.**

**THE REASON, IN THE SOURCE'S TERMS:** comments, docstrings and cited paths are
content the modules are **required** to carry — this project's modules are written
to state the prohibitions they obey — **and a check that cannot distinguish a
citation from a violation will demand the removal of the citation.**

`tests/test_structural_pass.py` already uses this method, stripping comments and
docstrings by tokenising before searching.

### 6.2 THE STANDING INCLUSION CRITERION

**Source: `docs/design/04_1a_denomination.md` §6.**

> **A VERIFICATION CHECK THAT FIRES FALSELY IS LOGGED AS A LEDGER INSTANCE IF AND
> ONLY IF THE IMMEDIATE REMEDIATION ON OFFER WOULD HAVE DEGRADED AN OTHERWISE
> CORRECT ARTIFACT.**

**Routine test iteration, in which no correct artifact was at risk, is excluded.**
The criterion exists **so that the next such check is classified by someone who
does not yet know which way it will come out.**

### 6.3 A CHECK CAN BE WRONG ABOUT WHAT IT MATCHES

**Source: `docs/design/04_0_decision_rule.md` §9, instance (37).** A check
asserted a formatting defect against a clean document **using a character class
that matched em dashes rather than box-drawing characters. The document was
correct and the check was wrong.**

> **IT IS THE RECURRING DEFECT CLASS APPLIED TO A VERIFICATION CRITERION — a check
> written from a mental model of what it matches rather than from what it
> matches.**

### 6.4 PROSE DOCUMENTS, SUBSTRING COLLISIONS AND THE NON-ASCII SET

> ### NOT COMMITTED. SEE §12.2 AND §12.3.

---

## 7. THE DEFECT LEDGER

### 7.1 THE COUNTING METHOD

**Source: `docs/handoff/31_point_5_closing.md` §7.1**, cited by
`docs/design/04_0_decision_rule.md` §9 as counting **every defect a committed
artifact records.**

**INSTANCES ARE NEVER RENUMBERED OR RECOUNTED.** Every document that has added to
the ledger states this in the same words, and states that the ledger **remains
contiguous** from (1) to the current total.

**THE RECURRING CLASS**, as the documents state it: **a numerical or directional
criterion written from a mental model of a quantity rather than from its
implementation or achievable range.**

### 7.2 THE CURRENT TOTAL AND WHERE IT IS STATED

**THE TOTAL IS 43.** Stated at `docs/design/04_1c_denominator_choice.md` §5.5 as
**"42 + 1 = 43"**.

**Carried forward unchanged** by `docs/design/04_1c_pre_commitments.md` §8,
`docs/design/04_1c_level_method.md` §8 and `docs/design/04_1c_proper.md` §10, each
of which reads the total, states that it adds no instance, and gives its reason.

**EACH DOCUMENT ADDING AN INSTANCE READS THE TOTAL FROM THE MOST RECENT DOCUMENT
STATING ONE, AND SHOWS THE ARITHMETIC IN ONE LINE.**

**AN ALTERNATIVE READING IS ON RECORD.** `docs/design/04_1c_level_method.md` §8
records that a reader holding a committed clause whose letter and illustration
diverge to be itself an instance **would reach 44 rather than 43**, following the
precedent at `docs/design/04_1a_denomination.md` §5, which named its own close call
and the total the alternative reading would give.

---

## 8. ERRATA DISCIPLINE

**Source: `docs/handoff/31_point_5_closing.md` §8 and
`docs/design/04_0_divergence_disposition_amendment_2.md` §6.**

> **ERRATA ARE LOGGED, NOT PATCHED. NO FROZEN TEXT IS EDITED.**

Each entry gives the correct value and **states whether anything operative
changes.** The correction lives in a document other than the one it corrects, and
that document is **the correction of record.**

**THE CONSOLIDATED INDEX LIVES AT `docs/design/04_1c_pre_commitments.md` §5**, at
nine entries, with its scope, its search method and its exclusions stated there.

**THE MAINTENANCE RULE**, from §5.4 of that document:

> **ANY DOCUMENT MAKING A CORRECTION TO A FROZEN ARTIFACT ADDS ITS ENTRY TO THIS
> INDEX IN THE SAME COMMIT.**

Not afterwards and not in a later consolidation pass. **Point 4's closing record
carries the final index.**

---

## 9. THE READ-BACK PROTOCOL

**Source: `docs/handoff/23_point_1_reopened_closing.md` §5.1**, carried over
unchanged by `docs/handoff/31_point_5_closing.md` §13.

> **THE RULE: artifacts under review are transferred by FILE UPLOAD, not by
> pasting. The chat report-back carries only SHA-256, line count, commit hash and
> test count.**

**A hash that matches proves the file on disk is correct. It proves nothing
whatever about a paste that accompanies it**, and the two were repeatedly observed
to disagree.

**AND POINT 5's OBSERVATION**, `docs/handoff/31_point_5_closing.md` §12.2: **the
verified path held and the unverified path broke, repeatedly, in the same point** —
the defect rate is a property of whether the channel is checkable, not of what is
being carried.

---

## 10. THE STANDING WORKING RULES

**Source: `docs/handoff/31_point_5_closing.md` §13**, transcribed in full:

- **One point at a time.**
- **Decisions before code.**
- **No code in chat.**
- **Claude Code prompts for anything built.**
- **Friction over compliance** — an objection raised is worth more than an
  instruction followed.
- **The read-back protocol** — artifacts by file upload; the chat carries hash,
  line count, commit and test count only.

**AND TWO ADDED BY POINT 5:**

- **A mutation that disables a pre-read guard never faces the real data
  directory** (§6.3).
- **Prompts do not name new test files, and target paths are checked before
  writing** (§7.3).

---

## 11. OPEN OBLIGATIONS QUEUED FOR LATER POINTS

### 11.1 THE POINT 6 QUEUE, AT FOUR

**Source: `docs/design/04_1c_proper.md` §7.3**, which gathers them.

1. **THE EXPIRY RE-ARGUMENT.** Committed at
   `docs/design/04_1b_tolerance_and_branch.md` §3.5: if the haircut is measured,
   the estimate becomes an observation and the constraint's rationale weakens, so
   its justification must be re-argued. **Enlarged by
   `docs/design/04_1a_denomination_amendment_1.md` §5.2**, which records that under
   the narrowed numerator the constraint's sole input is replaced at that moment
   rather than merely improved upon.
2. **FOLDING MEASURED SLIPPAGE INTO THE UNVALIDATED SET.** Committed at
   `docs/design/04_1c_proper.md` §7.3. Entry slippage is a member of that set,
   frozen at zero, carrying no magnitude today.
3. **RE-EVALUATING THE ACHIEVABLE DOMAIN.** Committed at
   `docs/design/04_1c_proper.md` §7.3, resting on
   `docs/handoff/36_point_4_1c_risk_unit_derivation.md` §5.1: the zero-width limit
   rises with the unvalidated total, so a non-zero slippage moves the domain's
   upper bound and the grid built inside it. **The admitted domain itself changes.**
4. **THE EMPIRICAL AUDIT OF THE DISPLACEMENT BUDGET.** Committed at
   `docs/design/04_1c_proper.md` §7.1: when paper trading supplies observed fills,
   the realised displacement of the risk unit is measured against the budget, and
   the budget, the uncertainty parameter and the level are re-argued in light of it.

**ITEMS 2 AND 3 ARE ONE EVENT WITH TWO CONSEQUENCES**, listed separately in the
source because a step doing the first without the second would leave a domain that
no longer bounds what it claims to.

### 11.2 STILL OWED INSIDE POINT 4

**Source: `docs/design/04_1c_proper.md` §1.2 and §8.**

- **STEP 2**, a report under `docs/handoff/`: the level, the per-symbol
  per-direction floor widths, the stress comparator, the non-floor-bound stratum
  thickness, and the first count of population B.
- **STEP 3**, a design document: kill condition (d)'s disposition, the magnitude
  threshold, and the Point 6 audit's terms.

---

## 12. NOT COMMITTED — PRACTICES WITH NO SOURCE

> ### EVERYTHING IN THIS SECTION IS A PRACTICE EVERY RECENT STEP HAS FOLLOWED AND
> ### THAT NO COMMITTED DOCUMENT STATES. NONE OF IT IS BINDING.

It is listed so it can be committed properly later or dropped. **A search over
`docs/design/` and `docs/handoff/` found no source for any of it.**

### 12.1 THE VERBATIM-TRANSCRIPTION PROHIBITION

That an instruction requiring verbatim transcription cannot also constrain the
transcribed text's content. **Exists only as logged instance (33)** and as an
example grouped under §5.2's rule, whose wording does not reach it. **Not a rule.**

### 12.2 THE SUBSTRING-COLLISION PRACTICE

That prose documents have no AST, so §6.1's rule cannot apply to them, and ordinary
English words colliding with a banned token by substring are therefore avoided in
drafting rather than by reinterpreting the check.

**THE KNOWN COLLISION: words built on "sharpen" contain a banned token as a
substring.** One was found and reworded in
`docs/design/04_1c_denominator_choice.md` before commit; the file records no note
of it. **No committed document states the practice or names the collision.**

### 12.3 THE PERMITTED NON-ASCII SET

That a document may contain no non-ASCII character other than the section sign and
the em dash. **Recent instructions have imposed it; no document commits it.**
Related but not the same: instance (37) at
`docs/design/04_0_decision_rule.md` §9 concerns a check that matched em dashes when
it meant box-drawing characters, which is a fact about a check rather than a
formatting rule.

### 12.4 THE OUTPUT FORMATTING PRACTICE

Markdown only; no box-drawing characters, no pipe tables, no aligned-column ASCII.
**Followed since Point 4 opened; committed nowhere.**

### 12.5 THE REPORT-BACK FORMAT

Plain prose lines, one fact per line, no tables, no aligned columns; and the two
standing closing items — **any place where a requirement contradicted a constraint,
stated rather than resolved**, and **anything readable as narrower or broader than
intended.**

**PARTLY COVERED, AND ONLY PARTLY.** §9's read-back protocol commits *what* the
report-back carries — hash, line count, commit, test count. **It says nothing about
the prose format or the two closing items.**

### 12.6 THE STANDARD VERIFICATION SEQUENCE

The pre-existence check on target paths; hash recomputation of named documents; the
test count before and after; the `git status` and `git diff --stat` confirmation;
the banned-token grep; the non-ASCII inventory; committing alone; and reporting
SHA-256, line count and commit hash.

**ONE ELEMENT IS COMMITTED:** `docs/handoff/31_point_5_closing.md` §13's *"target
paths are checked before writing"*. **The rest is practice.**

### 12.7 THE SINGLE-FILE RULE AND ITS TWO EXEMPTIONS

That a step creates exactly one file and modifies nothing else; and that
`docs/prompts/MANIFEST.md` and the consolidated errata index are exempt, being
updatable by any step in that step's own commit without counting as a modification
of a frozen artifact.

> **NEITHER THE RULE NOR THE EXEMPTIONS IS COMMITTED ANYWHERE.** A search for
> "single-file", "exactly one file" and "one file per" over `docs/design/` and
> `docs/handoff/` returned nothing. **The exemptions cannot be transcribed as
> standing, because the rule they except from does not exist as a committed rule.**

**THE MAINTENANCE RULE AT §8 IS THE ONE REAL PRECEDENT** — the errata index's
same-commit update requirement is committed at
`docs/design/04_1c_pre_commitments.md` §5.4 — **but it is stated as an obligation to
update, not as an exemption from a single-file rule.**

---

## 13. WHAT THIS FILE DOES NOT DO

**IT BINDS NOTHING ON ITS OWN AUTHORITY.** Every rule above is binding because its
source is, and to the extent its source is.

**IT RESOLVES NO DIVERGENCE.** §1.2's three-way divergence in the banned-name list
and §3.2's naming inconsistency are transcribed and left standing.

**IT IS NOT A SUBSTITUTE FOR READING THE SOURCES** where a step turns on a rule's
exact wording. It is a table of contents with the text attached.
