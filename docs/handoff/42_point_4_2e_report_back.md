# REPORT 42 — STEP REPORT-BACK: SUB-POINT 4.2e

## 0. GENRE, AND WHY THIS FILE EXISTS

**THIS IS A STEP REPORT-BACK, NOT AN ANALYSIS REPORT.** The genre is declared here
because `docs/design/04_2e_housekeeping.md` §5.2 files both kinds in one numeric
sequence under `docs/handoff/` and requires the distinction to be carried by the
document rather than by a directory.

**IT IS THE FIRST DOCUMENT WRITTEN UNDER THAT PROTOCOL, AND IT REPORTS THE STEP
THAT COMMITTED IT.** The protocol requires a step's report-back to be written to a
file and committed in the same commit as the step; the chat channel carries this
file's path, its SHA-256, its line count, the commit hash and the test count, and
discussion, and no other account of the work.

**THE COMMIT HASH IS NOT IN THIS FILE AND CANNOT BE.** A file recording its own
commit's hash changes that hash — the case `docs/prompts/MANIFEST.md` §1.6 records
for `docs/design/04_1d_standing_practices.md`. §5.2 assigns the commit hash to the
chat channel for that reason.

**NOT A MEMBER OF THE FROZEN SPECIFICATION.**
`docs/design/04_0_divergence_disposition_amendment_2.md` §2: a record of what
happened is evidence, cited and corrected by erratum, and does not bind.

**NO OUTCOME QUANTITY APPEARS BELOW**, and no artifact named at
`docs/design/04_2a_artifact_containment.md` §3.1 was opened for any purpose.

---

## 1. THE STEP

**ONE DOCUMENT, `docs/design/04_2e_housekeeping.md`, CLOSING FIVE ITEMS LEFT OPEN
BY THE CONSOLIDATED CODE STEP.** No code was changed. Nothing was computed.

**FILES IN THE COMMIT: THREE.** The document; `docs/prompts/MANIFEST.md`, by that
file's own maintenance rule; and this report-back, under the third single-file
exemption `docs/design/04_2e_housekeeping.md` §5.3 creates.

---

## 2. THE MANIFEST

**HASH ON ENTRY:**
`5e85c273b2f0fbe513a3fad057f33452143bb8bb757de93ea859734e14a5f3f9`

**VERIFICATION: 61 hashed entries parsed, 61 match, 0 mismatches, 0 missing.**
Every hash was recomputed from the working tree; none was compared against a
value quoted in another document.

**THE FOUR UNHASHED ENTRIES AT §4 ALL EXIST** — `src/engine/costs.py`,
`src/engine/sizing.py`, `src/engine/portfolio.py`, `src/risk/exit_spec.py`.

**THE SECTION COUNTS RECONCILE:** 29 frozen-specification entries plus 20 evidence
reports plus 12 implementation modules is 61, which is the total §5 states.

**`docs/prompts/STANDING_RULES.md` MATCHES THE HASH THE INSTRUCTION SUPPLIED:**
`da63e28104e41890dfea438b95f98ca67e4972034e4cbc8505e894c0a0077873`.

---

## 3. §0's FINDING — WHO OPENS `bands.json`

**THE CLAIM WAS VERIFIED INDEPENDENTLY, OVER AST NODES, AND NOT TAKEN FROM THE
CONSOLIDATED CODE STEP'S REPORT-BACK.** That channel is what the protocol at §5
regulates, and a document resting on it while regulating it would have no standing.

**THE METHOD.** `src/sweep/bands.py` was parsed and its module-level assignments
read: `ARTIFACT_PATH` is the only constant naming `bands.json`. Every `.py` file
under `src/` and `tests/` was then parsed, each module's import alias table built
from its `Import` and `ImportFrom` nodes, and every `Call` node whose function is a
read collected where an `Attribute` among its descendants resolves to
`src.sweep.bands.ARTIFACT_PATH`. Enclosing functions were then inspected for
decorators and for skips.

### 3.1 CONFIRMED, AND THE REPORT-BACK WAS INCOMPLETE

> **SIX CALL SITES, NOT ONE.** `tests/test_sweep_bands.py` lines 132, 315, 374,
> 379, 399 and 409, each `json.load(open(bd.ARTIFACT_PATH))`.

**ALL SIX RUN UNCONDITIONALLY.** The six enclosing functions carry no decorator, no
`skip`, no `importorskip` and no `xfail`; the module defines no `pytestmark` and
calls `skip` nowhere.

**AND THE MODULE READS THREE PROHIBITED ARTIFACTS, NOT ONE:** `bands.json` at the
six sites; `data/derived/sweep/sweep_cells.jsonl` through the module-scoped `cells`
fixture at `:25`, which calls `sw.load_cells()` — a function that raises
`FileNotFoundError` rather than skipping; and the sweep trade tables through
`src/sweep/bands.py:539`'s `srep.load_trades`, reached from the test at `:91`.

> ### **THE CONSOLIDATED STEP'S REPORT-BACK NAMED ONE CALL SITE AND ONE ARTIFACT.
> ### ITS SUBSTANTIVE CLAIM WAS CORRECT AND ITS ACCOUNT WAS INCOMPLETE, IN THE
> ### DIRECTION THAT UNDERSTATES THE FINDING.**

**RECORDED RATHER THAN PASSED OVER**, because it is an instance of a chat account
being checked rather than trusted, which is the whole argument for §5.

### 3.2 THE READER PREDATES BOTH DOCUMENTS THAT MISSED IT

`git log` over `tests/test_sweep_bands.py` returns **exactly one commit**:
`68e5b16`, **2026-08-09**, which introduced the file and the read together. The
file has not been modified since.

`docs/handoff/41_point_4_2_artifact_audit.md` was committed at `c5ae538` and
`docs/design/04_2a_artifact_containment.md` at `3fa9d06`, both **2026-08-17**.

> **EIGHT DAYS. THE ENUMERATION WAS WRONG WHEN IT WAS WRITTEN, NOT OVERTAKEN BY A
> LATER CHANGE.**

---

## 4. THE AMENDMENT, AND WHETHER THE FOURTH READER IS GRANDFATHERED

**`docs/design/04_2a_artifact_containment.md` §3.3's CLASS TWO IS AMENDED FROM
THREE TEST MODULES TO FOUR**, adding `tests/test_sweep_bands.py`. That document is
not edited; §2 of `docs/design/04_2e_housekeeping.md` is the amendment.

**THE DEPARTURE FROM THE NAMING CONVENTION IS DISCLOSED.** §8 of the amended
document names its successor as
`docs/design/04_2a_artifact_containment_amendment_1.md`. This amendment travels
inside a document carrying four unrelated closures instead, and §2.1 says so in
terms so a reader looking for that filename knows where it went.

**THE CONSEQUENCE, STATED PLAINLY AND NOT SOFTENED:**

> ### THE READ PROHIBITION AT §3.2 HAS BEEN IN BREACH ON EVERY SUITE INVOCATION
> ### SINCE IT WAS COMMITTED. A BREACH OF A RULE THIS PROJECT WROTE, FOUND BY THE
> ### GUARD THE SAME PROJECT BUILT.

**WHETHER IT REACHED ANYTHING: NO.** Every write-capable call in the module was
enumerated over `Call` nodes — the only ones are two `json.dumps` at `:317` and
`:319`, comparing two in-memory structures. **No `open` in a write mode, no `dump`,
no `to_csv`, no `to_json`, no `to_parquet`, no `write`.** 38 test functions and no
file produced. A search over `docs/` returns the module in
`docs/prompts/MANIFEST.md` alone, written by the step reporting the finding, and
returns the report rendered from `bands.json` in no file at all.

**A RULE BROKEN WITHOUT CONSEQUENCE IS STILL A RULE BROKEN.**

### 4.1 THE DECISION: GRANDFATHERED, AND WHY THAT IS NOT THE CHEAP ANSWER

> ### **THE FOURTH READER IS GRANDFATHERED, ON THE SAME GROUND AND WITH THE SAME
> ### RESERVATION AS THE OTHER THREE.**

**THE ARGUMENT FOR REQUIRING A STOP WAS PUT FIRST AND AT FULL STRENGTH:** §3.3's
justification is about not breaking what the drafter **considered**, and the fourth
was never considered, so extending the permission grants something the document
never granted. **And there is a real channel** — a failed assertion prints its
operands, so a test that loads an artifact renders artifact-derived content into a
human-readable surface at the moment it fails.

**THE ARGUMENT THAT HOLDS IS EQUAL TREATMENT.** On every criterion §3.3 could have
applied, the fourth reader is indistinguishable from the three the document names:
it predates the prohibition, reads on every invocation, fails rather than skips,
emits nothing, and feeds no commitment.

> **THE ONLY DIFFERENCE IS THAT AN AUDITOR SAW THREE AND MISSED ONE. TO
> GRANDFATHER THREE AND FORBID THE FOURTH IS TO PROMOTE THE RECORD OF AN ERROR
> INTO A RULE.**

**AND THE EMISSION CHANNEL DOES NOT DISCRIMINATE** — it is a property of the whole
class, so it is an argument for item 5 and not for singling out one member.

**THE COST IS EXPLICITLY NOT THE GROUND.** Requiring a stop would disable 38 tests
pinning the band-selection machinery. That is real and it is not why. **If the
three had been forbidden, the fourth would be forbidden here at whatever cost.**

**AND THE GRANDFATHERING IS PROVISIONAL, EXACTLY AS THEIRS IS.** §7 item 5 —
whether any of them should continue — now ranges over **four** modules, bears on
**freeze precondition 5**, and the arguments for requiring a stop travel to it
intact.

---

## 5. WHETHER THE OMISSION DISTURBS REPORT 41's VERDICT

**IT DOES NOT, AND THE REASON IS STRUCTURAL RATHER THAN ARITHMETIC.**

**THE VERDICT DOES NOT REST ON §4.1.** §4.1 is the **forward** trace, from each
artifact to whatever opens it. §4.2 is the **backward** trace, from every Point 4
and Point 5 commitment. **The NO BREACH verdict is the backward trace's.** A
forward trace that misses a consumer weakens the claim that it lists all consumers;
it cannot create a consumer of a commitment, because the backward trace starts from
the commitments.

**AND THE OMITTED READER CANNOT APPEAR IN THE BACKWARD TRACE FOR A REASON
INDEPENDENT OF ANYONE HAVING LOOKED:** it writes no file, so it cannot be a link in
a chain from an artifact to a commitment. **The backward trace returns the same
answer had §4.1 named it.**

**IT WAS ALSO INDEPENDENTLY RE-RUN AND IT HOLDS.** One further file names
`bands.json` — `docs/handoff/16_point_4_closing.md`, the **superseded** Point 4's
closing record — in a commit table and a step instruction, **as a filename and not
as a figure.** §4.2's claim is about citing a figure, and it survives.

**WHAT IS DAMAGED IS NARROWER AND IS STATED:** §4.1's completeness claim is false,
and every downstream use of it as a **closed enumeration** — which is exactly what
`docs/design/04_2a_artifact_containment.md` §3.3 made of it — is unsound. That is
the whole of the damage.

**ERRATUM ENTRY 11 LOGGED**, in the consolidated index's form, target *evidence*,
**operative**.

---

## 6. §4's VERIFICATION, THE ERRATUM, AND WHICH READING THE RULE REQUIRES

**VERIFIED FROM THE CODE, NOT FROM THE CONSOLIDATED STEP'S REPORT.** The AST of
`src/analysis/exposure_profile.py` gives `max_hold_exit`'s body as
`exit_close = settlement` and `exit_bar = exit_close - BAR_MS`, and `positions`
unpacking at `:385` into `row['exit_bar_ts']` and `row['exit_close_ms']`.

**AND ON A STAMP, WITH NO DATA READ:** for a signal bar at 2024-12-31T22:00Z,
`exit_bar_ts` is 2025-01-01T15:00Z and `exit_close_ms` is 2025-01-01T16:00Z;
`nth_settlement_after(bar_close_ms(ts))` equals `exit_close_ms` and does not equal
`exit_bar_ts`. **They differ by exactly 3,600,000 ms.**

> ### **CONFIRMED. THE THIRD FUNDING SETTLEMENT IS WRITTEN TO `exit_close_ms`;
> ### `exit_bar_ts` IS THAT SETTLEMENT MINUS ONE BAR PERIOD.**

**THE CITED LINE NUMBER IS ALSO OFF** — §4.4 cites `:352` for the write, and the
unpack is at `:385`. The column-tuple citation at `:346-349` is correct.

**ERRATUM ENTRY 12 LOGGED**, target *specification*.

**THE COMMITTED RULE IS UNAFFECTED.** §4.4 and §4.5 state the rule in terms of the
**scheduled max-hold exit**, and §4.4 identifies that twice, independently of the
column claim, with the third funding settlement. **The rule names an event; the
erratum corrects a claim about which column carries that event's timestamp.**

**WHICH READING THE RULE REQUIRES: `exit_close_ms`.** The column claim was the only
thing pointing the other way and it is the thing that is wrong.

> ### **THE IMPLEMENTATION TESTS `exit_close_ms >= seal`. IT MATCHES THE RULE AND
> ### IS RATIFIED.**

**IS THE BOUNDARY INSTANT AMBIGUOUS? NO.** *"Strictly before"* on the admitting side
and *"at or after"* on the excluding side is an explicit disposition: an exit
landing exactly on the seal is **excluded**. The apparent ambiguity was never about
the comparison but about which stamp it ranges over.

**THE CONSEQUENCE IS RECORDED.** The seal falls on a settlement instant, so the case
is reachable and is reached by exactly one candidate — the eleventh, where the
narrower reading would exclude ten. **That candidate needs no sealed minute.** The
rule excludes it anyway, and §4.4 calls the scheduled exit *"the conservative
bound"* for precisely this reason: **over-exclusion at the boundary uses no future
information; the alternative requires knowing an outcome.**

---

## 7. THE PROTOCOL AS COMMITTED, AND WHERE THE POST-FREEZE QUESTION IS ROUTED

**THE RULE:** a step's report-back is written to a file and committed in the same
commit as the step. **The chat carries the path, the SHA-256, the line count, the
commit hash and the test count — and discussion — and no other account of the
work.**

**WHERE THEY LIVE: `docs/handoff/`**, because a record of what happened is evidence
and not specification, and filing it under `docs/design/` would enrol an execution
record in the frozen specification.

**HOW THEY ARE NAMED: `docs/handoff/NN_<slug>.md`, in the existing numeric
sequence**, `NN` the next unused integer. One sequence and not two, so that no two
documents are entitled to be called "report 42". **The genre is declared in the
document's first section**, which is what keeps the shared sequence readable.

**A THIRD SINGLE-FILE EXEMPTION IS CREATED**, alongside `docs/prompts/MANIFEST.md`
and the consolidated errata index at
`docs/design/04_1d_standing_practices.md` §1.3. **Without it the protocol is
unsatisfiable**: §5.2 requires the report-back in the step's own commit and the
single-file rule permits one file. The exemption covers exactly one file per step,
at the prescribed path, containing the report-back and nothing else.

**AND ONE CONTRADICTION IN THE COMMISSIONING INSTRUCTION, STATED AND NOT
RESOLVED.** It directs that the document be *"committed alone with the manifest"*
and separately directs that the report-back be written to a committed file. **Those
are two files and three.** The exemption at §5.3 is the minimum that makes both
satisfiable; committing the report-back separately would break *"committed with
that step"*.

**THE PRE-FREEZE RULE IS COMMITTED IN FULL**, with what a report-back may contain
stated as a principle plus an explicit illustration per
`docs/design/04_0_divergence_disposition_amendment_2.md` §7, and with the two
standing closing items — a requirement that contradicted a constraint, stated
rather than resolved, and anything readable as narrower or broader than intended —
**committed for report-backs**, having previously been practice that
`docs/prompts/STANDING_RULES.md` §12.5 records as committed nowhere.

**THE POST-FREEZE QUESTION IS ROUTED TO ITS OWN DOCUMENT, AND THE CHOICE IS
ARGUED:**

- **not `docs/design/04_2d_aggregation.md` §7**, whose §7.1 states that every
  obligation in it is a count and not an outcome quantity — it disclaims the
  subject matter;
- **not 4.6's first-run diagnostic gate**, which owes what is looked at and in what
  order, a different genus from what may be written down and committed;
- **its own document**, on the precedent
  `docs/design/04_2b_point_4_decomposition.md` §5.1 sets for item 5, detached from
  every sub-point as **a firewall question, not a validation-design one.**

**ITS DEADLINE IS NOT THE FREEZE** but the first post-freeze report-back, which is
the moment the question first bites. **No owner at this commit.**

---

## 8. THE RESTATED OBJECTIVE, WHETHER IT IS MET, AND WHAT REMAINS

**THE ORIGINAL WAS UNACHIEVABLE AS WRITTEN.** The suite requires a derived
market-data layer of roughly 985 MB, built from an immutable raw layer fetched from
the venue; neither is tracked and neither sensibly could be. **That is a defect in
the objective, not a failure of the step.**

**AND `docs/design/04_2a_artifact_containment.md` §3.5 MISATTRIBUTES THE CAUSE** to
`sweep_cells.jsonl`, which is one absent input among several and by a wide margin
the smallest. Recorded as a correction of emphasis; **no erratum entry is added for
an implication.**

**THE RESTATEMENT, IN FOUR EVALUABLE PARTS:** what must be **present** — the clone
plus the derived data layer, an environment precondition whose absence is never a
finding about the commit; what must **build** — the recorded dependencies plus the
test runner, with no step absent from a file in the repository; what must **pass** —
every test whose inputs are tracked or derivable from the data layer; what may
legitimately **skip** — every test whose subject is an outcome-bearing artifact the
repository is forbidden to carry and which is absent, skipping loudly and naming
the artifact, the document forbidding it and how to regenerate it. **What may
legitimately fail: nothing.**

**WHICH MEASURED RESULT WOULD CONSTITUTE MEETING IT.**

- **Clone alone — 1,133 passed, 70 failed, 99 errors:** the environment
  precondition is unmet, so the run does not evaluate the objective at all.
- **Clone plus the full data layer — 1,377 passed, 1 failed:** fails on *what may
  legitimately fail: nothing*. **It is also not the target** — an environment
  holding artifacts a build does not produce is not the environment the objective
  is about.
- **Clone plus the data layer without the sweep's untracked outputs — 1,362 passed,
  3 skipped, 2 failed, 11 errors:** **this is the run that would constitute meeting
  it**, and it meets it only when its failures and errors reach zero. Its three
  skips are exactly the legitimate category.

> ### **THE RESTATED OBJECTIVE IS NOT MET. EVERY FAILURE AND EVERY ERROR IS ONE
> ### MODULE: `tests/test_sweep_bands.py`.**

**IT CARRIES TWO DISTINCT DEFECTS NEEDING DIFFERENT REPAIRS.**

**(a) IT FAILS RATHER THAN SKIPS WHEN ITS UNTRACKED INPUTS ARE ABSENT** — 11 errors
and 1 failure. The same defect §3.5 identifies and §7 item 4 routes, in a module
§3.5 did not know was a reader. Its repair is the one already applied to
`tests/test_sweep_run.py`. **Mechanical. No owner at this commit.**

**(b) THE ABSOLUTE PATH RECORDED IN `bands.json`** — 1 failure, present with every
input present. Established from source with no artifact opened:
`src/sweep/bands.py:708` records an absolute path into its payload and `:840`
renders it relative to `ROOT`, so the committed report matches a fresh render only
where `ROOT` is what it was when the payload was written.

> **IT BLOCKS THE OBJECTIVE.** It fails with everything present, so no environment
> precondition explains it and no skip can express it.

**AND IT IS SEPARATELY ROUTED, BECAUSE ITS REPAIRS ARE DECISIONS.** The three
available — change what a module declared dead relative to the frozen thesis
writes; regenerate a tracked outcome-bearing artifact; or weaken a pin that exists
to prove a committed report matches its inputs — **are settled by no committed
document, and this step does not settle them.**

**THE UNRECORDED STEP.** `requirements.txt` lists `requests`, `pandas` and
`pyarrow` and **does not list the test runner**, so "build then run the suite" has a
step no file records. The clone runs supplied it from outside. **Stated, not fixed.
No owner at this commit.**

---

## 9. THE LEDGER ARITHMETIC

**THE TOTAL, READ:** `docs/design/04_2d_aggregation.md` §9.3 states **51**.

**INSTANCE (52).** An instruction transcribed a committed register incompletely,
dropping one of five assigned items, so a freeze precondition recorded as being
cleared was cleared in part. `docs/design/04_2b_point_4_decomposition.md` §5.1
directs **five** items to the consolidated code step; the instruction that produced
that step named **four**, omitting the `simulate.py` cap divergence.

**SUB-CLASS: instance (50)'s and instance (51)'s** — a statement about what a
document says, written from a mental model of it — **itself the recurring class
applied to a citation**, per `docs/design/04_1c_denominator_choice.md` §5.5 on
instance (43).

**WHAT DISTINGUISHES IT FROM ITS TWO PREDECESSORS.** (50) attributed a count to a
document that declares none; (51) cited a section that does not exist. **This one
cites the right document at the right section and transcribes four of five
members.**

> ### A PARTIAL TRANSCRIPTION IS THE HARDEST OF THE THREE TO CATCH, BECAUSE
> ### EVERYTHING PRESENT IS RIGHT. THE OTHER TWO FAIL ON INSPECTION OF THE CITED
> ### TEXT; THIS ONE PASSES INSPECTION OF EVERYTHING IT SAYS.

**IT MEETS `docs/design/04_1a_denomination.md` §6's INCLUSION CRITERION:** the
remediation on offer — executing four items and reporting the step complete —
would have degraded an otherwise correct artifact by recording a freeze
precondition as cleared when it was not. **The implementing session did not adopt
it**, naming item 6 as unaddressed at execution.

**THE ARITHMETIC: 51 + 1 = 52.** No earlier instance is renumbered or recounted,
and the ledger remains contiguous from (1) to (52).

**THIS IS THE FOURTH CITATION-OR-TRANSCRIPTION ERROR CARRIED BY AN INSTRUCTION INTO
THIS CHAIN, AND THREE OF THE FOUR FALL IN CONSECUTIVE STEPS.**

**THE ERRATA INDEX MOVES FROM TEN IN FACT TO TWELVE IN FACT**, against nine in its
own text. Entries 11 and 12 are at §3 and §4 of the document this step commits.

---

## 10. THE OPEN ITEMS, WITH OWNERS

**TEN, AND NONE HAS AN OWNER AT THIS COMMIT.**

1. **The `simulate.py` cap divergence** — `docs/design/04_2a_artifact_containment.md`
   §7 item 6, directed to the consolidated step and omitted from its instruction.
   **Bears on freeze precondition 3, which is closed as to the seal-crossing
   exclusion and open as to the cap.**
2. **Whether the grandfathered test modules should keep reading** — item 5, **now
   four modules**. Bears on freeze precondition 5.
3. **The placeholder pair** at `docs/design/04_2b_point_4_decomposition.md` §5.3 —
   item 7, unmoved.
4. **The reconciliation of `docs/handoff/26_point_5_2_budget_cost.md`.** Under the
   exclusion, the counts it rests on move: **6,021 taken becomes 6,015 and 5,363
   skipped becomes 5,358**, over an evaluated population of 11,373 rather than
   11,384. **Counts, not outcome quantities**, per
   `docs/design/04_2d_aggregation.md` §7.1. The report is not falsified — it
   describes a population the specification no longer admits — and
   `src/analysis/budget_cost.py` still reproduces it. **Whether it is re-measured
   or corrected by erratum is disposed by no committed document.**
5. **The pre-existing aggregate under the fixture carve-out** —
   `tests/test_determinism_golden.py`'s `nunique() == 1` on a config-derived
   column. Pinned exactly by the guard and unsettled; belongs with item 5.
6. **The absolute path recorded in `bands.json`** — §8(b). **Blocks the restated
   clean-clone objective.**
7. **`tests/test_sweep_bands.py`'s skip repair** — §8(a). Mechanical.
8. **The test runner's absence from `requirements.txt`** — §8. Mechanical.
9. **The guard's register update** — move the fourth reader out of the undeclared
   list into the grandfathered set, citing the amendment. Mechanical, and required
   for the guard to state the amended rule rather than the superseded one.
10. **The post-freeze report-back question** — routed to its own document, due
    before the first post-freeze report-back is written.

**CARRIED UNCHANGED:** the two housekeeping items at
`docs/design/04_2b_point_4_decomposition.md` §5.5 — the standalone errata index,
now **twelve in fact against nine in its own text**, and the
`docs/prompts/STANDING_RULES.md` amendment. **The four Point 6 obligations at §5.4
are unmoved and none is a freeze precondition.**

---

## 11. THE TWO STANDING CLOSING ITEMS

### 11.1 WHERE A REQUIREMENT CONTRADICTED A CONSTRAINT

**ONE, STATED AND NOT RESOLVED.** The commissioning instruction directs that
`docs/design/04_2e_housekeeping.md` be **"committed alone with the manifest"** —
two files — and separately directs that the report-back be **written to a committed
file** under the protocol that same instruction commissions — three files.

**THE TWO ARE UNSATISFIABLE TOGETHER UNDER THE SINGLE-FILE RULE.** The resolution
taken is the narrowest available: §5.3 creates a third exemption covering exactly
the report-back file, on the ground that a rule that cannot be obeyed alongside a
rule already committed is a defect in the newer rule. **Committing the report-back
in a separate commit was rejected because it would break "committed with that
step", which is the protocol's operative clause.**

**A SECOND, MINOR ONE.** The instruction directs that the amendment be made "under
that document's change discipline; do not edit it". That discipline names the
successor `docs/design/04_2a_artifact_containment_amendment_1.md`, and the
instruction also fixes the filename as `docs/design/04_2e_housekeeping.md`. **The
document is not edited, which is the operative half; the naming convention is
departed from and the departure is disclosed at §2.1 so the amendment can be
found.**

### 11.2 ANYTHING READABLE AS NARROWER OR BROADER THAN INTENDED

**§2.2's AMENDED SET COULD BE READ AS PERMITTING TESTS TO READ PROHIBITED
ARTIFACTS GENERALLY.** It does not. It names four modules by extension and closes
the set on the same terms. §9 of the document flags this as the second most exposed
clause for exactly this reason.

**§5.4's ILLUSTRATION OF WHAT A PRE-FREEZE REPORT-BACK MAY CONTAIN IS WRITTEN AS A
PRINCIPLE PLUS AN EXPLICIT "INCLUDING WITHOUT LIMITATION" LIST**, per
`docs/design/04_0_divergence_disposition_amendment_2.md` §7, so it should not be
read as narrowly as the list. **The principle is the operative half: anything the
firewall already permits a committed document to contain.**

**§6.2's SKIP CATEGORY IS DELIBERATELY NARROW.** It covers artifacts the repository
is **forbidden** to carry, not artifacts that merely happen to be absent. **A
reader who finds a failing test inconvenient cannot widen it without amending the
clause.**

**§2.5's GRANDFATHERING DECIDES ONE THING ONLY** — that the fourth reader is
treated as the three were. It decides nothing about whether any of the four may
continue, and §7.4 records that question as open and as bearing on a freeze
precondition.

---

**Suite: 1378 passing, unchanged — no code was changed.**
