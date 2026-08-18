# THE RECORD RECONCILED, AND THE BRIEFING DISCIPLINE

## 0. THREE SCOPE NOTES, AND THE CHECKS THIS DOCUMENT RESTS ON

### 0.1 NO BANNED NAME APPEARS IN THIS DOCUMENT

**Following `docs/design/04_2a_artifact_containment.md` §0.1 and
`docs/design/04_3a_metric_vocabulary.md` §0.1.** §5 of this document adjudicates
six committed documents for the presence of outcome quantities, which is a task
that could not be performed without naming the quantities if it were performed by
quotation. **It is not.** Every quantity is referred to by citation to the
document and section that carries it, and no value from any of them appears here.

> ### **THAT ROUTE WAS AVAILABLE AND IT IS TAKEN. A CHECK OVER THIS DOCUMENT
> ### SHOULD FIND NOTHING, AND IF IT FINDS SOMETHING THE CHECK HAS FOUND A
> ### DEFECT IN THIS DOCUMENT.**

**ONE SUBSTRING COLLISION WAS HIT IN DRAFTING AND IS RECORDED RATHER THAN PASSED
OVER IN SILENCE.** An ordinary English superlative built on the verb
`docs/design/04_1d_standing_practices.md` §2.3 names contains an enforced token,
and the check above fired on it. **It was reworded.** That section records the
same collision being found and reworded in
`docs/design/04_1c_denominator_choice.md` **without the file noting it**, which
made the convention invisible to the next drafter. **It is noted here so the next
one meets it as a known hazard rather than as a surprise.**

### 0.2 NOTHING IS COMPUTED AND NO ARTIFACT WAS OPENED

**No file under `data/` was opened.** No prohibited artifact was opened, including
to adjudicate §5 -- that adjudication is over `docs/`, which is not prohibited,
and the artifacts under `data/` remained closed throughout.

**No quantity is computed.** Every figure in this document is a count of files, of
lines, of commits or of index entries, or a SHA-256.
`docs/design/04_2d_aggregation.md`
§7.1's distinction governs: no exit is resolved and no level is evaluated to
obtain any of them.

### 0.3 THE VERIFICATION THIS DOCUMENT RESTS ON

**EVERY FACTUAL CLAIM IN THE COMMISSIONING INSTRUCTION WAS CHECKED AGAINST THE
TREE BEFORE BEING ACTED ON, AND FIVE WERE FOUND WRONG.** They are recorded at
§1.3. **None is propagated.**

`docs/design/04_2b_point_4_decomposition.md` §7.2 states the rule this follows:
**an instruction's factual claims about the repository are not evidence about the
repository.** Instances (50), (51) and (52) were logged for its violation in three
consecutive steps. This document logs three more, at §9, and two of the three are
in documents committed after (52) was logged.

**THE MANIFEST WAS VERIFIED IN FULL ON ENTRY.**
`docs/prompts/MANIFEST.md` at `ef67cc5` carried SHA-256
`151a3634b3f8432cd80e5e235a7c2760a93e45e4d1267e01c3de750858d6be3d`, 693 lines,
**66 hashed entries, of which 66 match the working tree exactly, zero mismatch,
and zero listed path absent.** That hash is superseded by this commit, which is
expected and is not a defect, per that file's §0.1.

---

## 1. WHAT THIS DOCUMENT IS

**SUB-POINT 4.3b. A RECONCILIATION OF THE COMMITTED RECORD WITH THE TREE, AND ONE
DISCIPLINE COMMITTED.**

**IT JOINS THE FROZEN SPECIFICATION ON ITS COMMIT**, per
`docs/design/04_0_divergence_disposition_amendment_2.md` §2's open-forward clause,
because §2.3 below commits a rule.

### 1.1 THE SCOPE, STATED PRECISELY

**IT DOES SIX THINGS AND ONLY SIX:**

1. **DECIDES THE DISCIPLINE FOR BRIEFING DOCUMENTS** -- §2.3 -- and corrects
   `docs/prompts/STANDING_RULES.md` from the tree.
2. **LOGS TWO BREACHES AT COMMIT `2a04e37`** and disposes of
   `docs/prompts/ORIENTATION.md`.
3. **CORRECTS THREE COUNTS AND FINDS TWO MORE.**
4. **ADJUDICATES THE SIX PRE-THESIS DOCUMENTS UNDER `docs/handoff/`** on report
   41's own criteria.
5. **DECIDES WHETHER THE ENGINE MODULES ARE HASHED.**
6. **UPDATES THE OPEN-ITEMS REGISTER** and answers the ownership question.

### 1.2 WHAT IT DOES NOT DO

> ### **IT DECIDES NOTHING ABOUT 4.3's REMAINDER, 4.4, OR ANY METRIC.**

**IT SETS NO THRESHOLD AND COMMITS NO KILL CONDITION.** It closes no membership.
It computes nothing.

**IT DOES NOT EDIT `docs/prompts/ORIENTATION.md`'s CONTENT**, nor
`docs/prompts/STANDING_RULES.md`'s. §2.6 and §3.2 name what is owed and to which
step.

**IT DOES NOT REGENERATE EITHER BRIEFING.** §2.3 commits the discipline; applying
it is a separate step, because a document that both creates a rule and exercises
it leaves no commit at which the rule existed and the exercise did not.

### 1.3 THE COMMISSIONING INSTRUCTION'S CLAIMS THAT ARE WRONG

**RECORDED FIRST, BEFORE ANYTHING RESTS ON THEM, AND NOT PROPAGATED.**

**(i) "Six committed handoff documents carry outcome figures."** **TWO DO.**
`docs/handoff/16_point_4_closing.md` carries them in quantity, and
`docs/handoff/08_point_4_pre_registration.md` carries them in its post-lift
appendix M.1 alone. **The other four carry none**, and §5.2 establishes each
separately. `docs/handoff/06_structural_outcome.md` contains **not one occurrence
of any banned name at all**, and `docs/handoff/19_timeframe_rule.md`'s two
occurrences are a declaration that no such quantity is computed anywhere in the
step it reports.

**(ii) "The six unindexed documents and the six outcome-bearing documents are the
same six."** **THEY ARE NOT THE SAME SET AND THERE IS NO COINCIDENCE TO EXPLAIN.**
The six unindexed documents are exactly the six committed before the thesis
freeze; the outcome-bearing set has two members. §5.6 gives the real relation,
which is causal and is about the manifest's creation date.

**(iii) "Two were modified at `3e35ba5` and one at `1064028`", of the four modules
`docs/prompts/MANIFEST.md` §4 lists.** **ONE OF THE FOUR WAS MODIFIED AT
`3e35ba5`** -- `src/engine/costs.py`. The second file that commit touched,
`src/engine/simulate.py`, **is not in §4's list at all**, which is a separate
finding and is recorded at §7.2. `src/engine/portfolio.py` at `1064028` is right.

**(iv) "The register at `docs/design/04_2b_point_4_decomposition.md` §5.5 carries
[the amendment] with no owner."** That section's words are **"Unattached; owed."**
The substance is the same and the quotation is not. Recorded because a
transcription that improves on its source is still a transcription that differs
from it.

**(v) "The register has grown to roughly sixteen items."** **IT STANDS AT ELEVEN
IN THE FORM `docs/design/04_2e_housekeeping.md` §7.4 MAINTAINS IT, PLUS THE TWO
HOUSEKEEPING ITEMS**, which that section carries separately -- thirteen in total
before this document moves any. §8 gives the enumeration. The figure sixteen
appears in no committed document.

> ### **FIVE WRONG CLAIMS IN ONE INSTRUCTION, ABOUT A REPOSITORY THE INSTRUCTION
> ### HAD JUST BEEN AUDITED AGAINST. THAT IS THE POINT §0.3 MAKES, AND IT IS WHY
> ### THE RULE IS TO CHECK RATHER THAN TO ADOPT.**

**ONE OF THE FIVE ORIGINATES IN THE AUDIT AND NOT IN THE INSTRUCTION.** Claim (i)
restates a finding the read-only audit made from raw token counts without
classifying the occurrences. **The audit's finding was too coarse and this
document supersedes it**; the instruction carried it faithfully. Recorded so the
error is attributed where it belongs.

---

## 2. PART A -- THE BRIEFING DISCIPLINE

### 2.1 THE FORM QUESTION IS DECIDED FIRST, AND IT IS NOT DECIDED BY WHAT THE FILE PRESCRIBES

`docs/prompts/STANDING_RULES.md` §0 states:

> **IT IS AMENDED BY A NEW FILE, NEVER SILENTLY EDITED.** It would be
> `docs/prompts/STANDING_RULES_amendment_1.md`.

**THAT FILE DOES NOT EXIST**, verified over the working tree and over
`git log --all --diff-filter=A` on the path. The obligation has sat unattached at
`docs/design/04_2b_point_4_decomposition.md` §5.5 since `eb696f5`.

> ### **THE QUESTION IS NOT WHETHER TO WRITE THAT FILE. IT IS WHETHER THE
> ### MECHANISM THAT NAMES IT IS THE RIGHT MECHANISM FOR THIS KIND OF FILE.**

**A DOCUMENT PRESCRIBING ITS OWN AMENDMENT ROUTE IS NOT AUTHORITY FOR THE ROUTE
BEING CORRECT.** `docs/prompts/STANDING_RULES.md` §0 also states, of itself,
**"THIS FILE CREATES NO RULE"** and §13 states **"IT BINDS NOTHING ON ITS OWN
AUTHORITY."** By its own terms its amendment clause binds nothing either, and the
question is open for this document to decide.

### 2.2 WHY THE AMENDMENT MECHANISM IS WRONG FOR A BRIEFING

**THE MECHANISM EXISTS TO PROTECT A PRE-REGISTRATION, AND IT PROTECTS IT BY
PRESERVING THE THING THAT MAKES IT EVIDENCE.**

`docs/design/04_0_decision_rule.md` §4: **"the commit hash is the evidence, and it
is evidence that survives everyone's account of what they were thinking."** A
pre-registration's whole value is that it was written before the result. **Editing
it destroys exactly what it is for.** That is why errata are logged and not
patched, and why every amendment in this project is a new file: the frozen text is
the evidence.

> ### **A BRIEFING IS THE OPPOSITE KIND OF ARTIFACT. ITS ONLY VALUE IS BEING
> ### CURRENT, AND NOTHING WHATEVER DEPENDS ON WHAT IT SAID AT A PAST MOMENT.**

**NO DECISION IN THIS PROJECT RESTS ON A BRIEFING.** Not one committed document
cites `docs/prompts/STANDING_RULES.md` as the source of a rule; every rule it
carries is cited to its own source, which is the discipline §0 of that file sets
for itself. **Freezing it therefore protects nothing.**

**AND THE COST IS PAID BY EVERY READER.** An amendment chain on a briefing means a
reader must read two files to learn one fact, and three after the next drift, and
the failure mode is not that they read them in the wrong order -- **it is that
they read only the first, because a briefing is the file people read when they do
not yet know there is a second one.** A briefing that must be read alongside a
correction is a briefing that has stopped doing the one job it has.

**THE PROJECT ALREADY LEARNED THIS ABOUT A DIFFERENT COPIED THING.** Commit
`47a26de`'s message:

> **A GUARD COPIED EIGHTEEN TIMES IS EIGHTEEN GUARDS, AND THEY DIVERGE SILENTLY.**

The fix was not to log the divergence more carefully. **It was to stop copying and
start importing.** `docs/prompts/STANDING_RULES.md` is a copy of facts that live
elsewhere, and it has diverged from every one of them that moves.

### 2.3 THE DISCIPLINE, COMMITTED

> ### **A BRIEFING DOCUMENT IS REGENERATED WHOLESALE FROM THE TREE. IT IS NEVER
> ### AMENDED AND NEVER PATCHED, AND ITS SUPERSEDED TEXT IS NOT PRESERVED.**

**A BRIEFING DOCUMENT, DEFINED BY EXTENSION AND BY A STATED PRINCIPLE**, per
`docs/design/04_0_divergence_disposition_amendment_2.md` §7's drafting rule:

**BY EXTENSION, AS AT THIS COMMIT:** `docs/prompts/STANDING_RULES.md` and
`docs/prompts/ORIENTATION.md`.

**BY PRINCIPLE:** a document that **creates no rule and records no measurement**,
and whose stated purpose is to restate, for a reader who lacks context, what other
documents already establish. **INCLUDING WITHOUT LIMITATION** a transcription of
standing rules; an orientation or onboarding document; a summary of project
status; and any document that describes itself as binding nothing and as yielding
to its sources where they differ.

**THE THREE LIMBS:**

**LIMB ONE -- REGENERATION, NOT AMENDMENT.** The file is rewritten in full at the
commit that updates it. **No amendment file is created and no superseded text is
carried forward.** Nothing is lost: `git log -p` over the path is the complete
history, and unlike a pre-registration, a briefing's past text is of no evidential
value to anybody.

**LIMB TWO -- A BRIEFING CARRIES NO MOVING FIGURE. IT CITES ONE.**

> ### **THIS IS THE LIMB THAT ACTUALLY FIXES THE PROBLEM, AND THE OTHER TWO ARE
> ### HOUSEKEEPING BESIDE IT.**

A briefing may transcribe a **rule**, which changes only by a commit that can be
cited. It may **not** state a **moving figure** -- the defect-ledger total, the
errata index count, the test count, the commit count, the current sub-point, the
open-items list, or any count of documents or entries. **Where a briefing needs
one, it names the document and section that holds it and stops there.**

The reason is mechanical rather than moral: **a rule and its source move together,
so a transcription of a rule is stale only when the rule is superseded, which is a
loud event. A figure and its source move apart silently.** Every one of the six
divergences at §2.4 is a moving figure, and not one is a rule.

**LIMB THREE -- THE CURRENCY MARKER.** A briefing states, in its own text, the
commit at which it was last regenerated, and `docs/prompts/MANIFEST.md` records
the same commit in its entry. **A reader comparing the two against `HEAD` can
establish staleness without reading the body.**

### 2.4 THE CORRECTIONS, TAKEN FROM THE TREE

**EACH WAS RECOMPUTED OR RE-READ FROM THE WORKING TREE AND THE GIT HISTORY. NONE
IS TAKEN FROM THE COMMISSIONING INSTRUCTION.**

**CORRECTION 1 -- THE DEFECT-LEDGER TOTAL.** §7.2 states **"THE TOTAL IS 43."**
**The total read from the chain is 52**, stated at
`docs/design/04_2e_housekeeping.md` §7.3 as "51 + 1 = 52" and read unchanged at
`docs/design/04_3a_metric_vocabulary.md` §10.1. §9 of this document takes it
further. The chain was walked in full and is contiguous from (1) to (52) with no
number used twice and none skipped.

**CORRECTION 2 -- THE ERRATA INDEX.** §8 states the consolidated index is **"at
nine entries."** **It is at nine in its own text and at twelve in fact.** The
three outside it are entry 10 at `docs/design/04_1d_standing_practices.md` §4.1,
entry 11 at `docs/design/04_2e_housekeeping.md` §3.1 and entry 12 at that
document's §4.2. §8 of this document takes it to fifteen.

**CORRECTION 3 -- THE BANNED-NAME DIVERGENCE.** §1.2 states the divergence is
**"REPORTED AND NOT RECONCILED"** and that four modules carry a nine-name variant.
**It was reconciled at `47a26de`, fifteen minutes after `c6b71c5` committed
§1.2.** That commit defines the list once at `src/firewall.py`, aligns all
eighteen sites, and adds `tests/test_firewall_names.py`, which asserts over the
AST that no module defines its own copy. Its message states in terms:
**"STANDING_RULES section 1.2 recorded the divergence; this commit closes it."**
**THE THIRD LIMB OF THE DIVERGENCE IS ALSO ALREADY CLOSED, AND §1.2 DOES NOT
KNOW IT.** The prose divergence §1.2 records -- between
`docs/handoff/31_point_5_closing.md` §11's ten-item wording and the enforced list
-- **was logged as errata entry 10 at `docs/design/04_1d_standing_practices.md`
§4.1, in the same commit `fc8933f` that §12's practices were committed in.** So
§1.2's "REPORTED AND NOT RECONCILED" is wrong about both limbs it names, and both
were settled within twenty minutes of it being written.

**CORRECTION 4 -- THE PRACTICES §12 CALLS UNCOMMITTED.** §12 describes seven
practices as having no source. **All seven were dispositioned at `fc8933f`, twenty
minutes after §12 was written.** `docs/design/04_1d_standing_practices.md` §1
commits **four as rules** -- the standard verification sequence (§1.1), the
report-back format including the two standing closing items (§1.2), the
single-file rule and its two exemptions (§1.3), and the verbatim-transcription
content prohibition (§1.4) -- and its §2 records **three as conventions**, being
the permitted non-ASCII set, the output formatting practice and the
substring-collision practice. **A third exemption to the single-file rule was
added at `docs/design/04_2e_housekeeping.md` §5.3.**

> ### **§12.7 IS THE STARKEST CASE. IT STATES "NEITHER THE RULE NOR THE
> ### EXEMPTIONS IS COMMITTED ANYWHERE." `04_1d` §1.3 CREATES BOTH, AND SAYS SO
> ### IN THOSE WORDS.**

**CORRECTION 5 -- §11.2's "STILL OWED INSIDE POINT 4".** Both items are delivered.
**Step 2** is `docs/handoff/37_point_4_1c_level_and_consequences.md` at `eebe986`;
**step 3** is `docs/design/04_1c_consequences_and_thresholds.md` at `2a04e37`.

**CORRECTION 6 -- §0.1's CLAIM ABOUT THE MANIFEST.** §0.1 states
**"`docs/prompts/MANIFEST.md` contains none of the tokens."**

> ### **IT CONTAINS ONE, AT LINE 90, AND IT CONTAINED IT AT `c6b71c5` -- THE SAME
> ### COMMIT THAT INTRODUCED BOTH FILES. THE CLAIM WAS FALSE WHEN WRITTEN.**

Verified by extracting `docs/prompts/MANIFEST.md` at every commit that has touched
it: the token is present at all twenty revisions, from the first. It occurs in the
prose describing what `docs/design/00_standing_brief.md` transcribes, which is a
name and not a figure, so **nothing operative changes** -- but §0.1's closing
sentence **"NO OTHER OCCURRENCE IN THIS FILE IS PERMITTED"** is drafted against a
survey that was wrong about a second file. **Logged as errata entry 13.**

**AND ONE THAT IS NOT A CORRECTION, WHICH IS THE POINT OF §2.5.** Corrections 1,
2, 4 and 5 record claims that were **true when written and became false**.
Correction 3 records one that was true for fifteen minutes. **Only correction 6 is
an erratum in this project's sense, because only correction 6 was wrong at its own
commit.**

### 2.5 THE GENERAL PROBLEM, STATED AS A PROBLEM AND NOT AS AN INSTANCE

> ### **A BRIEFING THAT TRANSCRIBES A MOVING STATE IS STALE FROM THE MOMENT IT IS
> ### COMMITTED, AND NOTHING IN THIS PROJECT'S DISCIPLINE MAKES ANYONE UPDATE
> ### IT.**

**THE ERRATA MECHANISM CANNOT REACH IT.** An erratum corrects a claim that was
wrong when made. **Five of the six divergences at §2.4 were right when made.**
There is no defect to log, no correction of record to write, and no document to
name as the correction's holder. **The discipline this project uses for wrong
statements has no analogue for statements that expire.**

**THE LEDGER CANNOT REACH IT EITHER.** The recurring class is a criterion written
from a mental model rather than from an implementation. **A figure that was
measured correctly and then moved is not that**, and logging it would dilute a
count whose value is that it means one thing.

**AND THE HARM IS NOT HYPOTHETICAL. IT IS ALREADY IN THE COMMITTED RECORD ONCE.**
`docs/design/04_2e_housekeeping.md` §5.4 commits the two standing closing items
for report-backs, on the stated ground that they are **"practice that
`docs/prompts/STANDING_RULES.md` §12.5 records as committed nowhere."** That
sentence is true about §12.5 and false about the tree: **`04_1d` §1.2 had
committed them two days earlier, as one of its four rules, in the same words.**
A step read the briefing instead of the tree and re-created a rule that already
bound. **Logged as ledger instance (55) and as errata entry 14.**

> ### **THAT IS WHAT A STALE BRIEFING COSTS: NOT A READER MISLED IN THE ABSTRACT,
> ### BUT A COMMITTED DOCUMENT THAT CREATES SOMETHING TWICE AND ARGUES FOR IT FROM
> ### A REASON THAT HAD EXPIRED.**

**WHAT WOULD FIX IT, AND WHAT WOULD NOT.**

**LIMB TWO OF §2.3 FIXES IT, AND IT IS THE ONLY LIMB THAT DOES.** A briefing
carrying no moving figure cannot go stale in the way that matters. It can be
superseded, which is loud, but it cannot quietly disagree with a count. **Every
one of the six divergences would have been impossible under limb two.**

**AN UPDATE OBLIGATION WOULD NOT FIX IT, AND IS REJECTED.** Requiring every step
to refresh the briefings is the discipline that already failed: nothing enforced
it, twenty commits passed, and the obligation sat on a register with no owner. **A
convention nobody is checked against is what produced this section.**

**A TEST WOULD FIX THE RESIDUE, AND IT IS NAMED AS OWED RATHER THAN WRITTEN
HERE.** A check asserting that a briefing's currency marker names a commit, and
that the briefing contains no numeral in a figure position, would convert limbs
two and three into a guard. **This project has found repeatedly that a guard holds
where a convention does not** -- `docs/handoff/31_point_5_closing.md` §12.2 states
it as a general observation about verified and unverified channels. **It is not
written here because this document changes no code**, and §2.6 routes it.

### 2.6 WHAT IS OWED, AND TO WHICH STEP

- **THE REGENERATION OF `docs/prompts/STANDING_RULES.md`** under §2.3, carrying
  §2.4's six corrections, with every moving figure removed and replaced by a
  citation, and a currency marker added. **A document step. No owner at this
  commit.**
- **THE REGENERATION OF `docs/prompts/ORIENTATION.md`** on the same terms, per
  §3.2. **A document step. No owner at this commit.**
- **THE BRIEFING CURRENCY CHECK.** A test asserting limbs two and three. **A code
  step. No owner at this commit.**

> ### **`docs/prompts/STANDING_RULES_amendment_1.md` IS NOT WRITTEN AND MUST NOT
> ### BE. THE OBLIGATION AT `docs/design/04_2b_point_4_decomposition.md` §5.5 IS
> ### DISCHARGED BY DECIDING THE FORM, NOT BY SATISFYING THE FORM IT ASSUMED.**

---

## 3. PART B -- `docs/prompts/ORIENTATION.md`

### 3.1 TWO BREACHES AT COMMIT `2a04e37`, VERIFIED AGAINST GIT AND LOGGED

**THE FILE.** `docs/prompts/ORIENTATION.md`, tracked, 1,345 lines, SHA-256
`7d0e5503f6461ca5eba426465653f1a92dc5b7eeb30a7ec716e1c15913db194e`, working tree
identical to `HEAD`. Introduced at `2a04e37` at 1,147 lines; modified at `7ce7f9e`
to 1,169; modified at `eee1e18` to its present length. **Three commits, and no
others.**

**BREACH ONE -- THE SINGLE-FILE RULE.**
`docs/design/04_1d_standing_practices.md` §1.3 creates the rule and its two
exemptions at `fc8933f`, on 2026-08-16 at 20:02. **`2a04e37` is 2026-08-17 at
11:01, fifteen hours later, and it created two new files:**
`docs/design/04_1c_consequences_and_thresholds.md` and
`docs/prompts/ORIENTATION.md`, alongside a `docs/prompts/MANIFEST.md` edit.

**THE MANIFEST EDIT IS EXEMPT. `ORIENTATION.md` IS NOT.** The errata-index
exemption does not reach it, and the report-back exemption at
`docs/design/04_2e_housekeeping.md` §5.3 **did not exist until `8077238`**, two
days later, and would not reach it in any case -- that exemption covers "exactly
one file per step, at the path §5.2 prescribes, containing the report-back and
nothing else", and `docs/prompts/` is not that path.

> ### **THE FILE SET OF EVERY COMMIT FROM `fc8933f` TO `HEAD` WAS ENUMERATED.
> ### `2a04e37` IS THE ONLY SINGLE-FILE-RULE BREACH IN THE WHOLE OF THAT HISTORY.**

**BREACH TWO -- THE PRE-EXISTENCE CHECK.**
`docs/handoff/31_point_5_closing.md` §13 commits **"target paths are checked
before writing"**, and `docs/design/04_1d_standing_practices.md` §1.1 makes it the
first element of the standard verification sequence.

**THE CHECK WAS ESTABLISHED BY A PROPERTY OF THE COMMIT RATHER THAN BY
TESTIMONY.**
Every path introduced by any of the 118 commits on `main` was compared against its
commit message, by full path, basename, stem, sub-point rendering, report number
and every significant word of the stem. **Seventy paths fail that test.
Sixty-eight
are in bulk commits predating any such rule. One is a false positive of the method
-- `docs/handoff/44_point_4_3a_report_back.md`, whose commit message names 4.3a.**

> ### **`docs/prompts/ORIENTATION.md` AT `2a04e37` IS THE ONLY PATH IN THE ENTIRE
> ### POST-RULE HISTORY THAT ITS OWN COMMIT MESSAGE DOES NOT NAME, IDENTIFY, OR
> ### SHARE A SIGNIFICANT WORD WITH.**

**THE CONSEQUENCE IS NOT THE BREACH ITSELF.** It is that the manifest's
maintenance rule -- "ANY STEP CREATING A FROZEN ARTIFACT APPENDS ITS ENTRY IN THE
SAME COMMIT" -- was not applied, **in a commit that edited the manifest**, and has
not been applied in any of the eighteen commits since. **A 1,345-line tracked
document has been outside the index for eighteen commits.**

**WHAT IS NOT CLAIMED.** A session's account of this commit reported a concurrent
committer. **The reflog carries 122 entries: 117 `commit`, 4 `commit (amend)`, one
`commit (initial)`, and no checkout, reset, rebase, merge or force operation
anywhere.** A concurrent committer leaves a checkout or a divergent tip.
**There is
none, and the account is not adopted.** What the record supports is that one
session's file was staged into a commit another activity was assembling in the
same working directory. **That is what is logged; the intent behind it is not
established and is not guessed at.**

### 3.2 THE DISPOSITION

**THREE OPTIONS WERE ON OFFER: INDEXED AND MAINTAINED, INDEXED AND MARKED STALE,
OR REMOVED.**

**REMOVAL IS REFUSED, AND THE REASON IS NOT SENTIMENT.** §2 of that file carries
**both holdout disclosures in full**, which
`docs/design/04_0_divergence_disposition_amendment_1.md` §3 requires of any
communication characterising a holdout result and which
`docs/design/04_0_divergence_disposition_amendment_2.md` §3 extends to any
communication asserting the seal is intact. **`ORIENTATION.md` §15 asserts the
seal is intact and carries the disclosures attached to that assertion, in full and
not by reference, which is what those clauses require.** Deleting it would remove
one of the few places in the repository where that obligation is discharged
properly.

**"INDEXED AND MAINTAINED" IS REFUSED**, because it is the option §2.5 rejects. It
imposes an update obligation that nothing enforces, and the eighteen commits of
drift are the evidence for what that is worth.

> ### **THE DISPOSITION: INDEXED, AND GOVERNED BY §2.3's BRIEFING DISCIPLINE ON
> ### THE SAME TERMS AS `docs/prompts/STANDING_RULES.md`.**

**INDEXING IS NOT OPTIONAL AND IS DONE IN THIS COMMIT.**
`docs/handoff/41_point_4_2_artifact_audit.md`'s finding against the sweep
artifacts was that they were **an unmanaged surface**, and the remedy it names is
**disclosure and containment**. A 1,345-line tracked document that no index
mentions is the same kind of object. **Its entry in `docs/prompts/MANIFEST.md`
records its hash, its introducing commit, and the commit at which it was last
current**, which is limb three of §2.3.

**"MARKED STALE" IS SUBSUMED RATHER THAN CHOSEN.** The currency marker makes
staleness computable from the index rather than asserted in the body, which is
strictly better than a label someone must remember to attach. **The file's own
§15 already carries the right disclaimer** -- "Where it and a source document
differ, the source governs and the difference is a defect here" -- and that
sentence is not the problem. The problem is the six moving figures in the same
section, which limb two removes at regeneration.

**THE ANSWER IS THE SAME FOR BOTH BRIEFINGS, AND THAT IS THE POINT.** §2.3 was
decided without reference to `ORIENTATION.md`, on the nature of the artifact
rather than on the instance, and it lands on this file without adjustment.

> ### **THIS DOCUMENT EDITS NOTHING IN `docs/prompts/ORIENTATION.md`.** Its
> ### regeneration is owed at §2.6.

---

## 4. PART C -- THE COUNTS

### 4.1 `docs/design/04_2b_point_4_decomposition.md` -- THE 4.1c COUNTS

**THE DOCUMENT MAKES THE CLAIM TWICE, IN TWO SECTIONS, AND BOTH ARE WRONG.**

- **§2.2** states 4.1c is **"six design documents and four reports"** -- and then
  lists **seven design documents and three reports in the same bullet.**
- **§2.3** states **"4.1c WAS SPLIT INTO SIX DESIGN DOCUMENTS MID-COURSE."**

**THE COUNT FROM THE TREE.** Seven files match `docs/design/04_1c_*.md`:
`non_uniformity_check`, `path_and_scope`, `denominator_choice`, `pre_commitments`,
`level_method`, `proper`, `consequences_and_thresholds`. **Three files match
`docs/handoff/*4_1c*.md`: reports 35, 36 and 37.**

> ### **SEVEN AND THREE, NOT SIX AND FOUR. ALL TEN EXISTED AT `eb696f5`, WHICH IS
> ### WHERE THE CLAIM WAS WRITTEN, AND §2.2 ENUMERATES ALL TEN CORRECTLY IN THE
> ### SENTENCE THAT MISCOUNTS THEM.**

**THAT LAST FACT IS WHAT MAKES IT AN INSTANCE RATHER THAN A TYPOGRAPHICAL SLIP.**
The enumeration and the count are in the same bullet, and the count was not taken
from the enumeration beside it. **It was taken from a mental model of how many
documents 4.1c ought to have had** -- which is the recurring class exactly, and
which §2.3 of that same document independently records as a thing that surprised
its author. **Logged as errata entry 15 and ledger instance (53).**

### 4.2 `docs/prompts/MANIFEST.md` §5 -- THE OMITTED-MODULE COUNT

**§5 states the implementation modules are "12 -- `src/firewall.py` plus eleven
under `src/analysis/`, with 3 more analysis modules present and omitted as unused
by the current chain."**

**§3 OF THE SAME FILE NAMES THE OMITTED SET EXPLICITLY:** `budget_cost.py`,
`dispersion.py`, `intrabar_span.py`, `rsi_breakout_profile.py`,
`sweep_population.py`, `__init__.py`. **That is six.**

**THE TREE HOLDS SEVENTEEN files matching `src/analysis/*.py`. Seventeen less the
eleven listed is six.**

> ### **§5 SAYS THREE. §3 SAYS SIX. THE TREE SAYS SIX. A FILE DISAGREES WITH
> ### ITSELF ABOUT A SET IT ENUMERATES ELSEWHERE IN ITS OWN TEXT.**

**IT IS CORRECTED IN PLACE AND NOT BY ERRATUM, AND THE GROUND IS THAT FILE'S OWN
§0.** `docs/prompts/MANIFEST.md` describes itself as **"A LIVING INDEX"** and
states **"THIS MANIFEST IS A CONVENIENCE INDEX. THE GIT HISTORY IS AUTHORITATIVE
WHERE THEY DISAGREE"** and **"A hash here that does not match the file is a defect
in this file, not evidence about the file."** **It is not a frozen artifact and
the errata-not-patched discipline does not attach to it.** It is edited by every
step under its own maintenance rule, and this step edits it.

**THE DEFECT STILL HAPPENED AND IS STILL COUNTED.** The class does not depend on
whether the target is frozen. **Logged as ledger instance (54), with no erratum.**

### 4.3 `docs/design/04_1f_cap_requirement.md` -- THE HOLE IN THE CHAIN

**CONFIRMED: THE FILE CONTAINS NO OCCURRENCE OF THE WORD "LEDGER" AT ALL**, and
its eight sections run from §0 to §7 with no ledger section among them. Every
other Point 4 design document either logs an instance or states the total as
unchanged with a reason. **`04_1g` §7.1 therefore reads back past it, to
`04_1e` §6.3.**

**IT IS RECORDED AS A HOLE AND NOT LOGGED AS AN INSTANCE, AND THE ARGUMENT IS ON
THE COUNTING METHOD.**

`docs/handoff/31_point_5_closing.md` §7.1 counts **"every defect that a committed
document explicitly identifies as an instance of this class"**, the class being a
numerical or directional criterion written from a mental model of a quantity
rather than from its implementation. **A document that says nothing has written no
criterion from anything.** There is no wrong figure, no wrong direction and no
mental model to have been substituted for a measurement.

**AND NO COMMITTED RULE IS BREACHED.** The practice, as
`docs/prompts/STANDING_RULES.md` §7.2 transcribes it, binds **"EACH DOCUMENT
ADDING AN INSTANCE"**. `04_1f` adds none, so the practice does not reach it. **The
convention that a document reading no instance still states the total is followed
by nine documents and stated by none of them.**

> ### **IT IS A HOLE IN A CHAIN THAT IS OTHERWISE UNBROKEN FROM (1) TO (52), AND
> ### THE CHAIN'S ARITHMETIC IS UNAFFECTED BECAUSE `04_1f` CHANGED NOTHING TO
> ### CARRY FORWARD. RECORDED SO THAT A READER WALKING THE CHAIN AND FINDING A
> ### DOCUMENT WITH NO LEDGER SECTION KNOWS IT WAS LOOKED AT.**

### 4.4 A FOURTH, FOUND HERE AND NOT COMMISSIONED

**`docs/design/04_2e_housekeeping.md` §5.4 RE-COMMITS A RULE THAT ALREADY BOUND**,
on a ground taken from the stale briefing. The finding is stated in full at §2.5,
because it is the evidence that section rests on rather than a separate item.
**Logged as errata entry 14 and ledger instance (55).**

### 4.5 ONE INSTANCE OR TWO -- THE ARGUMENT

**§4.1 AND §4.2 ARE TWO INSTANCES, NOT ONE.**

**THE METHOD DECIDES IT.** `docs/handoff/31_point_5_closing.md` §7.1 counts
**"one per distinct defect -- not per symptom and not per document."** That clause
guards in two directions: it forbids splitting one defect into its symptoms, and
it forbids counting one defect once per document that repeats it. **Neither
applies here.**

- **They are not two symptoms of one defect.** One is a miscount of design
  documents belonging to a sub-point; the other is a miscount of modules omitted
  from an index. Different documents, different authors' acts, different subject
  matter, different commits -- `eb696f5` and, for the surviving wording, every
  manifest revision since.
- **They are not one defect repeated across documents.** Neither document restates
  the other's figure. There is no common origin to attribute a single miscount to.

**THE PRECEDENT IS DIRECTLY ON POINT AND RUNS THE SAME WAY.** Instances (50), (51)
and (52) are all the citation class, logged in three consecutive steps, **counted
as three.** `docs/design/04_2e_housekeeping.md` §7.2 calls (52) "the third
citation-class instance in as many steps" -- **naming the shared class while
keeping the separate count.** A shared class has never merged instances in this
ledger and does not here.

**THE ARGUMENT FOR ONE, STATED SO IT CAN BE WEIGHED.** A reader could hold that
"the chain miscounts its own artifacts" is a single systemic defect with two
appearances, and that counting appearances inflates a total whose value is that it
counts causes. **That reading is coherent and it is not adopted**, because the
method's words are "distinct defect" and not "distinct cause", and because under
it instances (50) to (52) would collapse to one and the ledger would have to be
recounted -- which
`docs/prompts/STANDING_RULES.md` §7.1 and every document that has added to the
ledger forbid in the same words: **instances are never renumbered or recounted.**

**§4.4's INSTANCE IS A THIRD ON THE SAME TEST.** Its defect is a re-commitment
induced by reading a briefing rather than the tree; its document is
`04_2e_housekeeping.md`; its subject is neither of the other two.

**AND §4.6's IS A FOURTH, WHICH IS THE HARDEST CALL OF THE SET BECAUSE IT SHARES A
FILE WITH §4.2's.** Both are miscounts in `docs/prompts/MANIFEST.md`. **They are
still two distinct defects**: one is a count of modules omitted from an index,
stated in §5 against an enumeration in §3; the other is the reported result of a
cross-check over hexadecimal strings, stated in §0.1. **Different sections,
different subject matter, different methods, and neither figure is derived from
the other.** The "not per document" clause forbids counting one defect once per
document that carries it; **it does not merge two defects because one document
carries both.** A reader who reads it the other way reaches 54 rather than 56, and
the argument is here rather than the conclusion.

> ### **FOUR DISTINCT DEFECTS, FOUR INSTANCES.**

### 4.6 A FIFTH, FOUND BY RUNNING A CHECK THE INDEX SAYS IT RAN

**`docs/prompts/MANIFEST.md` §0.1 STATES A CROSS-CHECK AND ITS RESULT:**

> **THE CROSS-CHECK, RE-RUN AT THIS REVISION.** Every 64-character hexadecimal
> string appearing in any document under `docs/` other than this manifest was
> extracted and compared against the working tree: **44 occurrences, of which 40
> resolve to a file in the tree and match it exactly, and 4 do not.**

It then enumerates **"THE FOUR THAT DO NOT RESOLVE, EACH ACCOUNTED FOR"** -- three
manifest-at-entry citations and one recorded module hash -- and concludes **"ZERO
MISMATCHES... No silent-edit event is detected at this commit."**

**THE CHECK WAS RE-RUN HERE, AGAINST THE `ef67cc5` TREE, BY THE STATED METHOD.**

> ### **THE RESULT IS 49 OCCURRENCES, 43 RESOLVING AND SIX NOT. THE UNRESOLVED
> ### COUNT IS SIX UNDER EVERY READING OF THE STATED METHOD THAT WAS TRIED, AND
> ### NEVER FOUR.**

Four variants were run to give the figure every chance: all of `docs/` less the
manifest; `docs/design/` and `docs/handoff/` only; and each of those counting
distinct strings rather than occurrences. **They give 49/43/6, 49/43/6, 36/30/6
and 36/30/6.** The occurrence total varies with the counting rule; **the
unresolved count does not vary at all.**

**THE TWO IT MISSED ARE EXACTLY THE KIND ITS OWN LIST ENUMERATES.**
`docs/handoff/43_point_4_stop_cap_implementation.md` records the manifest's hash
as it stood at `8077238`, and `docs/handoff/44_point_4_3a_report_back.md` records
it as it stood at `3e35ba5`. **Both were orphaned by the very revision that
counted them**, which is the mechanism §0.1 describes in its own closing
paragraph: *"EACH DOCUMENT THAT RECORDS A HASH IT VERIFIED ON ENTRY ADDS AN ORPHAN
THE MOMENT THE TARGET IS NEXT REVISED."*

**WHAT IS AND IS NOT DAMAGED.** The **conclusion survives**: no string naming a
file as it stands now fails to match it, and the two missed strings are accounted
for by the same explanation as the three the list gives. **No silent-edit event is
detected, and that claim is re-verified here rather than inherited.** What is
damaged is the count, the completeness of the enumeration, and -- the part that
matters -- **the standing of a section that describes itself as having re-run a
check.**

> ### **THIS IS THE RECURRING CLASS APPLIED TO A VERIFICATION, WHICH IS INSTANCE
> ### (37)'s SHAPE: A CHECK REPORTED FROM A MENTAL MODEL OF WHAT IT WOULD RETURN
> ### RATHER THAN FROM WHAT IT RETURNED.** A wrong figure in a document is one
> ### thing; a wrong figure attributed to a check that was run is another, because
> ### a reader has no way to discount it. **Logged as ledger instance (56).**

**CORRECTED IN PLACE, NOT BY ERRATUM**, on §4.2's ground. §0.1 is rewritten at
this commit with the figures for this revision, computed by the same script, and
the four variants recorded so the next reader can reproduce the number rather than
trust it.

---

## 5. PART D -- THE SIX PRE-THESIS DOCUMENTS, ADJUDICATED

### 5.1 THE CRITERIA, TRANSCRIBED VERBATIM BEFORE ANY FINDING IS STATED

**FROM `docs/handoff/41_point_4_2_artifact_audit.md` §1**, which itself
transcribed
them from its commissioning instruction before establishing any fact. **They are
reproduced here in that document's own words and are not adapted, narrowed or
extended for the different surface.**

> **THE FIREWALL CLAIM AT ISSUE is that no outcome quantity has been computed or
> inspected in the course of the decisions committed in Points 4 and 5. It is NOT
> the claim that no outcome quantity has ever been computed anywhere in the
> repository's history. Those are different claims and the distinction governs
> this audit.**

> - **NO BREACH: the artifacts contain outcome quantities, but no document,
>   decision or parameter committed in Points 4 or 5 consumed them, and no chain
>   exists from an artifact to such a decision. The finding is an unmanaged
>   surface, not a contamination event. The remedy is disclosure and
>   containment.**
> - **BREACH: a chain exists from an outcome quantity in an artifact to a
>   decision, parameter or threshold committed in Points 4 or 5. The remedy is to
>   identify every affected commitment and reopen it.**
> - **INDETERMINATE: the question cannot be settled without reading values, or
>   the provenance of an artifact cannot be established. STOP and report; do not
>   resolve it by reading.**

> **A CHAIN MEANS A TRACEABLE PATH, not a possibility. Establish chains over
> executable tokens, AST nodes and file reads; do not infer from proximity or
> from the fact that a file was present.**

**THE SURFACE IS DIFFERENT AND THE ADAPTATION IS STATED RATHER THAN ASSUMED.**
Report 41's surface was serialised artifacts under `data/` and the modules that
read them, so "executable tokens, AST nodes and file reads" was the whole of the
available evidence. **The surface here is prose, which has no AST and which no
module reads.** The analogue of a file read is a **citation**: a Point 4 or
Point 5
document naming one of these six and taking something from it. **That is the
substitution, it is the only one made, and every other limb is applied
unchanged.**

### 5.2 WHAT IS ACTUALLY THERE, DOCUMENT BY DOCUMENT

**THE COMMISSIONING INSTRUCTION ASSERTS THAT ALL SIX CARRY OUTCOME FIGURES. FOUR
DO NOT.** Each was examined in full and every occurrence of every enforced name
was classified by what it does in its sentence.

**`docs/handoff/06_structural_outcome.md` -- NOTHING.** **Not one occurrence of
any name on the enforced list, anywhere in the file.** There is nothing to
adjudicate.

**`docs/handoff/19_timeframe_rule.md` -- A DECLARATION THAT NONE EXISTS.** Two
occurrences, both on adjacent lines of a single sentence, and that sentence states
that **no such quantity is computed, referenced or estimated anywhere in the step
the document reports.** It is a firewall declaration of the same form as §0.1 of
this document. **It is the opposite of carrying a figure.**

**`docs/handoff/04_point_1r_opening.md` -- A PROHIBITION LIST AND A TASK NAME.**
Five occurrences. Four are a bulleted list of what the step is forbidden to
compute. The fifth names a task -- restating an edge claim in a given denomination
-- and states a structural fact about the population that claim describes. **No
value.**

**`docs/handoff/05_point_1r.md` -- DESIGN PARAMETERS AND PRE-COMMITTED
THRESHOLDS.** Nineteen lines carry an occurrence. Every one is a kill-condition
threshold fixed by design, an account variable named in a sizing formula, or
arithmetic on a **dispersion estimate that the document itself labels an
estimate**: its own §E6 states in terms that the dispersion figure **"is an
ESTIMATE from the bounds, not a measurement"**, and a separate line records that
the column required to measure it **was firewall-blocked at the time of writing.**
The standard-error and detectable-edge figures are arithmetic on that estimate.
**No measured outcome.**

> ### **`docs/handoff/08_point_4_pre_registration.md` -- A PRE-REGISTRATION IN ITS
> ### BODY, AND MEASURED OUTCOME QUANTITIES IN ITS POST-LIFT APPENDIX M.1.**

Its preamble states, at its own §0, that **the performance firewall was intact
when
it was written** and that no such quantity had been inspected. **That is true of
the body**: every occurrence in §1 to §12 and appendices A to L is a metric
name, a
pre-committed threshold, a reporting requirement or a mechanically derived bound.
**Appendix M is different and says so** -- it is labelled a post-lift addition and
records measurements taken after the firewall was deliberately relaxed for the
killed hypothesis. **M.1 carries realised distributional statistics over a
resolved
trade population.** Those are outcome quantities and the document does not pretend
otherwise.

> ### **`docs/handoff/16_point_4_closing.md` -- OUTCOME QUANTITIES IN QUANTITY, AND
> ### IT IS THE ONLY DOCUMENT OF THE SIX FOR WHICH THAT IS THE PRINCIPAL CONTENT.**

It is the closing record of the killed Point 4 hypothesis. It carries per-symbol
per-arm realised figures, a pooled figure with its standard error, acceptance
counts over the grid, and the verdict of each kill condition. **That is what a
closing record is for**, and the firewall had lifted for that hypothesis before it
was written.

### 5.3 THE CHAIN SEARCH

**RUN IN BOTH DIRECTIONS, OVER `docs/design/` AND `docs/handoff/` IN FULL.**

**FORWARD -- EVERY CITATION OF EACH OF THE SIX.** Four of the six are cited by no
Point 4 or Point 5 document at all: `04_point_1r_opening.md`, `05_point_1r.md`,
`06_structural_outcome.md` and `19_timeframe_rule.md`. **The two that carry
outcome quantities are the two that are cited**, and every citation was read in
context:

- **`08_point_4_pre_registration.md` is cited five times.** Once at
  `docs/design/04_1c_pre_commitments.md` §5.2, as an example of a correction
  **excluded** from the errata index. Once at
  `docs/design/04_2c_run_structure.md` §4.4 and twice at
  `docs/design/04_2d_aggregation.md` §5.3 and §7.2, in every case for **the text
  of a rule in appendix M.3 or M.4** -- an exclusion rule and two reporting
  requirements. Once at `docs/handoff/41_point_4_2_artifact_audit.md` §3, for
  provenance.
- **`16_point_4_closing.md` is cited eight times.** Once at
  `docs/design/04_1c_pre_commitments.md` §5.2 as a second **excluded** correction.
  Once at `docs/design/04_2e_housekeeping.md` §3.3 and once in
  `docs/handoff/42_point_4_2e_report_back.md` restating it, **expressly as a
  filename and not as a figure.** Once at
  `docs/handoff/31_point_5_closing.md` §7.1, taking **the number of rows in a
  numbered table of defect-ledger instances.** Four times for provenance, in
  reports 41 and 23 and in the thesis at
  `docs/handoff/22_point_1_thesis.md` §1 and §9.

**AND EVERY ONE OF THE THREE RULE CITATIONS DISCLAIMS THE SOURCE'S AUTHORITY IN
ITS OWN TEXT, UNPROMPTED.** `04_2c` §4.4: *"THAT DOCUMENT IS THE SUPERSEDED POINT
4's PRE-REGISTRATION, and this document does not treat it as binding... The rule
above is committed here afresh, on the grounds given here."* `04_2d` §5.3: *"A
CONCURRENCE, NOT AN AUTHORITY."* `04_2d` §7.2: *"REPORT 8 IS THE SUPERSEDED POINT
4's PRE-REGISTRATION AND IS NOT BINDING. This is an adoption afresh."*

**BACKWARD -- EVERY FIGURE, SEARCHED FOR ELSEWHERE.** Nineteen distinct numeric
strings were lifted from `16_point_4_closing.md` §1.2 to §2.4 and from appendix
M.1 of `08_point_4_pre_registration.md`, and searched over every other document
under `docs/design/` and `docs/handoff/`. **Sixteen return nothing at all.** Three
return matches and all three were opened and disambiguated:

- Two strings resolve to the **derived stop floor** in reports 24 and 25 and in
  `06_structural_outcome.md`. That quantity is `stop_min_pct`, computed by the
  cost algebra from the round-trip cost and the leverage term. **It is a cost
  fact, not an outcome quantity** -- no exit is resolved to obtain it -- and it
  **originates** in `06_structural_outcome.md`, which predates `16` and is one of
  the six. The direction of travel is into `16`, not out of it.
- One string resolves to a **funding-in-R comparison figure at the floor stop** in
  `docs/design/06a_exit_resolution_spec_amendment_1.md` §4.2 and
  `docs/handoff/30_point_5_3_4_portfolio.md` §7.3, where it is the subject of an
  express instruction not to use it. **A different quantity that shares four
  digits with one of `16`'s figures.**

> ### **NO FIGURE FROM EITHER DOCUMENT APPEARS IN ANY POINT 4 OR POINT 5 DOCUMENT.
> ### THE THREE APPARENT MATCHES ARE SUBSTRING COLLISIONS BETWEEN UNRELATED
> ### QUANTITIES, AND EACH IS NAMED ABOVE SO A READER CAN CHECK THE CALL.**

**ONE POSSIBILITY IS NAMED AND REFUSED, BECAUSE THE CRITERIA REQUIRE IT TO BE.**
Appendix M contains both M.1's figures and M.3's rule, and two Point 4 documents
cite M.3. **Citing a rule that shares a document with a figure is proximity.** The
criteria say in terms: *"do not infer from proximity or from the fact that a file
was present."* **The rule text is what was taken, both documents say so, and both
re-derive it.**

### 5.4 THE VERDICT, LIMB BY LIMB

- **BREACH requires a chain from an outcome quantity to a decision, parameter or
  threshold committed in Points 4 or 5.** No such chain exists. The forward search
  finds citations of rules, of filenames, of a table row count and of provenance,
  and no citation of a figure. The backward search finds no figure anywhere else.
  **The limb is not met.**
- **INDETERMINATE requires that the question cannot be settled without reading
  values, or that provenance cannot be established.** Neither holds. **These are
  prose documents under `docs/`, which nothing prohibits opening**, so the
  evidential problem that made report 41's task hard does not arise here at all;
  and every one of the six has a single introducing commit with a date. **The limb
  is not met.**
- **NO BREACH requires that the documents contain outcome quantities, that no
  Point 4 or Point 5 commitment consumed them, and that no chain exists.** Two of
  the six contain them; no commitment consumed them; no chain exists.

> ### **THE VERDICT IS NO BREACH.**

**THE GROUND, STATED SO IT CAN BE ATTACKED.** Every figure in the two documents
belongs to the **killed momentum and breakout hypothesis**, which
`docs/handoff/16_point_4_closing.md` records as killed and which
`docs/handoff/22_point_1_thesis.md` §1 supersedes. That thesis states, of itself,
that **no Point 4 choice carries forward by default and that every number in it is
a design parameter, a transcription from an artifact cited by hash, or arithmetic
on those two.** **The firewall claim at issue concerns this thesis, and the
figures concern a different one.**

**AND THE DATES ARE INDEPENDENT OF THE ARGUMENT.** All six were committed between
2026-08-04 and 2026-08-09 20:20. The thesis was frozen at `02e47a5` on 2026-08-11
at 12:26. **Every one of the six predates it, by between two and seven days.**
That is corroboration and not the ground; **a chain would be a breach whatever the
dates said**, which is why §5.3 was run rather than inferred from the calendar.

### 5.5 WHAT CONTAINMENT IS REQUIRED

**THE REMEDY THE CRITERIA NAME FOR NO BREACH IS "DISCLOSURE AND CONTAINMENT". THE
TWO ARE NOT THE SAME AND ONLY ONE IS OWED HERE.**

**DISCLOSURE IS OWED AND IS DISCHARGED IN THIS COMMIT**, by indexing all six at
§5.7 with their status recorded.

> ### **CONTAINMENT IN THE SENSE `docs/design/04_2a_artifact_containment.md` §3.2
> ### USES -- A PROHIBITION ON OPENING -- IS NOT OWED, AND COMMITTING ONE WOULD BE
> ### A DEFECT.**

**THREE REASONS, AND THE FIRST IS DECISIVE ON ITS OWN:**

1. **THESE ARE DOCUMENTS A READER LEGITIMATELY NEEDS.**
   `docs/handoff/08_point_4_pre_registration.md` is the killed hypothesis's
   pre-registration and `docs/handoff/16_point_4_closing.md` is its closing
   record. **Both are cited in the current chain** -- `04_2c` §4.4 and `04_2d`
   §5.3 and §7.2 rest on rules read out of the first, and each says so. **A
   prohibition on opening a document the chain reads is unsatisfiable.**
2. **THE HAZARD CONTAINMENT ADDRESSES IS ABSENT.**
   `04_2a` §3.2 prohibits opening artifacts whose **schema alone** does not tell a
   reader what is inside, so that a check requires a read and a read is the
   contamination. **A prose document states its own status in its own text.**
   `08`'s preamble declares the firewall's state at writing and its appendix M
   labels itself post-lift; `16`'s title and first section declare it a closing
   record for a killed hypothesis. **A reader cannot open either by accident and
   be surprised.**
3. **THE READ CHANNEL IS ALREADY GOVERNED.** The prohibition that matters is the
   one against **carrying a figure forward**, and that is
   `docs/handoff/31_point_5_closing.md` §11's firewall, which binds independently
   of where the figure is read. **A second prohibition attached to the file rather
   than to the act would add nothing and would make three committed documents
   unreadable to satisfy it.**

**WHAT IS OWED INSTEAD, AND IS DONE HERE:** each of the six carries, in its
manifest entry, **what it is, which thesis it belongs to, and whether it carries
outcome quantities.** That is the disclosure, and it is the thing whose absence
made the surface unmanaged.

**ONE THING IS NAMED AND NOT DECIDED.** Whether a future step citing `08` or `16`
must declare that it did so, in the manner `04_2a` §0.1 requires for banned names,
**is a firewall question of the same genus as item 5 at
`docs/design/04_2b_point_4_decomposition.md` §5.1** and is not settled by any
committed document. **It is added to the register at §8. No owner at this
commit.**

### 5.6 THE COINCIDENCE -- IT DOES NOT EXIST AS STATED, AND THE REAL RELATION IS CAUSAL

**THE COMMISSIONING INSTRUCTION ASSERTS THAT THE SIX UNINDEXED DOCUMENTS AND THE
SIX OUTCOME-BEARING DOCUMENTS ARE THE SAME SIX.** §5.2 establishes that **the
outcome-bearing set has two members**, so the two sets are not the same and there
is no coincidence of that shape to explain.

**THERE IS A REAL AND EXACT RELATION, AND IT IS NOT ABOUT FIGURES.**

> ### **THE SIX UNINDEXED DOCUMENTS ARE EXACTLY THE SIX `docs/handoff/` DOCUMENTS
> ### COMMITTED BEFORE THE THESIS FREEZE AT `02e47a5`. NOT ONE MORE AND NOT ONE
> ### FEWER.**

Verified by introducing-commit date against the thesis commit: the six run from
2026-08-04 10:37 to 2026-08-09 20:20, and the next document in the directory,
`22_point_1_thesis.md`, is the thesis itself.

**THE CAUSE IS THE MANIFEST'S CREATION DATE AND ITS STATED SCOPE.**
`docs/prompts/MANIFEST.md` was created at `c6b71c5` on 2026-08-16, five days after
the freeze, and its §0 defines itself as **"A LIVING INDEX OF EVERY ARTIFACT A
SUBSEQUENT STEP MIGHT NEED TO VERIFY."** It was built by walking the chain the
current thesis rests on, which begins at the thesis. **Everything before that
commit was outside the horizon of the walk, and the boundary of the index is the
boundary of the walk.**

> ### **CAUSAL, AND THE CAUSE IS MUNDANE. THE INDEX STOPS WHERE THE CHAIN THE
> ### INDEXER WAS FOLLOWING STARTS. THE PRESENCE OF OUTCOME QUANTITIES HAS
> ### NOTHING TO DO WITH IT, WHICH IS EXACTLY WHY FOUR OF THE SIX HAVE NONE.**

**AND THE MECHANISM GENERALISES, WHICH IS THE PART WORTH KEEPING.** An index built
by walking a chain is complete with respect to the chain and silent about
everything else, **and its silence is indistinguishable from an assertion that
nothing else exists.** `docs/design/04_2a_artifact_containment.md` §3.3 built a
closed set on report 41's forward enumeration and inherited its one omission,
which is the same failure at a different scale. **An enumeration is evidence about
what the enumerator looked at.**

### 5.7 MEMBERSHIP AND INDEXING

**ARE ANY OF THE SIX MEMBERS OF THE FROZEN SPECIFICATION? NO, AND THE CLAUSE THAT
WOULD ADMIT THEM DOES NOT REACH BACKWARD.**

`docs/design/04_0_divergence_disposition_amendment_2.md` §2:

> **THE LIST IS OPEN FORWARD. ANY DOCUMENT SUBSEQUENTLY COMMITTED AS A
> PRE-REGISTRATION UNDER THIS PROJECT'S DISCIPLINE JOINS THE FROZEN SPECIFICATION
> ON ITS COMMIT.**

**THE WORD IS "SUBSEQUENTLY", AND ITS REFERENCE POINT IS THAT DOCUMENT'S OWN
COMMIT**, `fd45afd`, on 2026-08-14. **`08_point_4_pre_registration.md` is
2026-08-07 and `19_timeframe_rule.md` is 2026-08-09. Both precede it.** The clause
is forward-only by its own word, and §2's list-by-extension names neither.

> ### **TWO SELF-DESCRIBED FROZEN PRE-REGISTRATIONS ARE NOT MEMBERS OF THE FROZEN
> ### SPECIFICATION, AND THE REASON IS A DATE RATHER THAN A JUDGEMENT ABOUT THEIR
> ### CONTENT.**

**THE CONTRARY READING IS AVAILABLE AND IS REFUSED.** A reader could hold that a
clause defining membership by a property -- being a pre-registration under this
project's discipline -- describes a class rather than a period, and that
"subsequently" merely disclaims exhaustiveness. **That reading is refused because
§2 defines membership by extension and states the list "as at that commit", and
because admitting a document into the frozen specification nine days after it was
written, by a clause it could not have been drafted against, is the opposite of
what a freeze is for.** `08` also contains a post-lift appendix, which no
member of
the frozen specification does. **A reader who disagrees can find the whole
argument here rather than a conclusion.**

**THEY ARE NONETHELESS INDEXED, AND THAT IS A DIFFERENT QUESTION.**

`docs/prompts/MANIFEST.md` §0 scopes itself to **"EVERY ARTIFACT A SUBSEQUENT STEP
MIGHT NEED TO VERIFY"**, not to members of the frozen specification -- its §2
indexes twenty-three documents that are expressly **not** members. **Three of the
six are cited by the live chain and a subsequent step may need to verify any of
them.**

> ### **ALL SIX ARE INDEXED IN THIS COMMIT, IN A SECTION OF THEIR OWN, EACH WITH
> ### ITS HASH, ITS INTRODUCING COMMIT, ITS STATUS AND WHETHER IT CARRIES OUTCOME
> ### QUANTITIES.**

**THE SECTION IS SEPARATE FROM §1 AND §2 DELIBERATELY.** Filing them among the
evidence reports would imply they belong to the current thesis's chain, which is
the confusion the index exists to prevent. **They are the record of a superseded
thesis, and the index says so.**

---

## 6. PART E -- THE ENGINE MODULES

### 6.1 THE GROUND FOR OMITTING THEM NO LONGER HOLDS

`docs/prompts/MANIFEST.md` §4 lists four modules **without hashes**, on a stated
ground:

> **LISTED WITHOUT HASHES, BECAUSE THEY ARE READ-ONLY DEPENDENCIES RATHER THAN
> ARTIFACTS THIS CHAIN PRODUCES**, and because every recent step asserts they are
> unmodified via `git status` rather than by hash.

**BOTH HALVES OF THE GROUND ARE NOW FALSE, AND THE SECOND HALF WAS ALWAYS THE
LOAD-BEARING ONE.**

- **`src/engine/costs.py` was modified at `3e35ba5`**, implementing
  `docs/design/04_1g_cap_adoption.md` §0.
- **`src/engine/portfolio.py` was modified at `1064028`**, implementing
  `docs/design/04_2c_run_structure.md` §4.4 and §4.5.
- `src/engine/sizing.py` last changed at `df14a68` and `src/risk/exit_spec.py` at
  `0f79311`, both on 2026-08-13.

**THE COMMISSIONING INSTRUCTION SAYS TWO OF THE FOUR MOVED AT `3e35ba5`. ONE
DID.**
That commit touched two engine files, but the second, `src/engine/simulate.py`,
**is not among the four §4 lists** -- which is §6.2's finding and a separate one.

> ### **AND `git status` IS NOT A SUBSTITUTE FOR A HASH. IT ASSERTS THAT A FILE
> ### MATCHES `HEAD`. IT SAYS NOTHING WHATEVER ABOUT WHETHER `HEAD` IS WHAT A
> ### DOCUMENT RELIED ON**, which is the only question an index answers. A clean
> ### tree at a modified `HEAD` is exactly the state that produced the stale line
> ### references §4 has had to correct twice in prose.

### 6.2 `src/engine/simulate.py` IS ABSENT FROM §4 ENTIRELY

**§4's TITLE IS "THE ENGINE FILES THE DERIVATIONS CALL", AND ON THAT SCOPE THE
OMISSION IS CORRECT** -- no derivation module under `src/analysis/` calls it.

**BUT IT IS THE MODULE THE ONLY OPEN SPECIFICATION DIVERGENCE LIVED IN.**
`docs/design/04_1g_cap_adoption.md` §5 named it, freeze precondition 3 at
`docs/design/04_2b_point_4_decomposition.md` §4.3 rested on it, and `3e35ba5`
closed it there. **A module that a freeze precondition turned on, and that the
full evaluation run executes, is an artifact a subsequent step might need to
verify** -- which is `docs/prompts/MANIFEST.md` §0's own scope and is wider than
§4's title.

### 6.3 THE DECISION

> ### **ALL FIVE ARE HASHED, IN THIS COMMIT. §4 IS RESTATED AS A HASHED SECTION
> ### AND `src/engine/simulate.py` IS ADDED TO IT.**

**THE REASON IS THE MOMENT RATHER THAN THE PRINCIPLE.**

`docs/design/04_2b_point_4_decomposition.md` §4.2 states what the freeze unlocks:

> **AFTER THE FREEZE THE ENGINE MAY BE RUN IN FULL EVALUATION MODE ON THE
> IN-SAMPLE WINDOW. THAT RUN COMPUTES OUTCOME QUANTITIES FOR THE FIRST TIME IN
> THIS THESIS'S LIFE.**

and that **lifting the firewall is irreversible.**

> ### **THESE ARE THE MODULES THAT RUN, AND UNTIL THIS COMMIT THEY WERE THE LEAST
> ### INDEXED FILES IN THE REPOSITORY. TWELVE ANALYSIS MODULES THAT PRODUCE
> ### REPORTS NOBODY WILL RE-RUN CARRIED HASHES; THE FOUR THAT PRODUCE THE
> ### IRREVERSIBLE RESULT DID NOT.**

**AND A HASH IS THE ONLY EVIDENCE THAT SURVIVES THE EVENT.** After the run, the
question "was the engine that produced this figure the engine the specification
describes" cannot be answered by `git status`, because `git status` is a statement
about the working tree at the moment it is run and the moment that matters has
passed. **It is the same argument `docs/design/04_0_decision_rule.md` §4 makes for
commit order: the evidence must survive everyone's account of what they were
thinking.**

**THE COST IS STATED.** Five more entries must be refreshed whenever those files
change, and a stale hash in the index is a defect in the index. **That is the
trade the manifest's §0 already accepts for sixty-six other entries**, and it is
cheaper than the alternative, which is having no answer at the only moment the
question is asked.

---

## 7. PART F -- THE OPEN-ITEMS REGISTER

**RECORDED IN THE FORM `docs/design/04_2b_point_4_decomposition.md` §5 USES. THAT
DOCUMENT IS NOT EDITED.**

### 7.1 THE COUNT ON ENTRY, ESTABLISHED RATHER THAN QUOTED

**`docs/design/04_2e_housekeeping.md` §7.4 LISTS TEN OPEN ITEMS** and carries the
two housekeeping items at `04_2b` §5.5 separately, as unchanged. **Its own closing
summary says "Ten items open, none with an owner", which counts the ten and not
the two.**

**`docs/design/04_3a_metric_vocabulary.md` §10.2 CLOSES ONE OF THE TEN** -- the
`simulate.py` cap divergence, by `3e35ba5` -- **and adds two.** Eleven, plus the
two housekeeping items. **Thirteen on entry to this document.**

> ### **THE COMMISSIONING INSTRUCTION SAYS "ROUGHLY SIXTEEN". THAT FIGURE APPEARS
> ### IN NO COMMITTED DOCUMENT AND THE ENUMERATION DOES NOT SUPPORT IT.**

### 7.2 WHAT THIS DOCUMENT MOVES

**CLOSED HERE -- TWO:**

- **THE `docs/prompts/STANDING_RULES.md` AMENDMENT**, at `04_2b` §5.5. **Closed by
  §2.3 deciding the form and §2.4 making the corrections.** The amendment file is
  not written and must not be. **The regeneration it is replaced by is a new item
  below.**
- **THE GUARD'S REGISTER UPDATE**, `04_2e` §2.6. **Closed by the second commit of
  this step**, which moves `tests/test_sweep_bands.py` into the grandfathered set,
  cites §2.2 as the amendment that admitted it, and keeps the exactness assertion.

**ADDED HERE -- FOUR:**

- **THE REGENERATION OF `docs/prompts/STANDING_RULES.md`** under §2.3. **A
  document step. No owner at this commit.**
- **THE REGENERATION OF `docs/prompts/ORIENTATION.md`** under §2.3 and §3.2. **A
  document step. No owner at this commit.**
- **THE BRIEFING CURRENCY CHECK**, §2.5. A test asserting limbs two and three of
  §2.3. **A code step. No owner at this commit.**
- **WHETHER A STEP CITING A SUPERSEDED-THESIS DOCUMENT MUST DECLARE IT**, §5.5.
  **A firewall question of item 5's genus, unattached to a sub-point. No owner at
  this commit.**

**CARRIED UNCHANGED -- ELEVEN.**

**TEN ARE EVERY REMAINING ITEM AT `04_2e` §7.4 AND `04_3a` §10.2:** item 5 and
item 7 from `04_2a` §7; the reconciliation of report 26; the pre-existing
aggregate under the fixture carve-out; the absolute path recorded in the band
artifact; the skip repair in `tests/test_sweep_bands.py`; the test runner's
absence from `requirements.txt`; the post-freeze report-back question; the
geometry disposition's hand-forward; and the register update for `04_3a` §1.4's
routing divergence. **None is moved and none acquires an owner.**

**THE ELEVENTH IS THE STANDALONE ERRATA INDEX**, at `04_2b` §5.5, routed by
`docs/design/04_1c_consequences_and_thresholds.md` §6.3 item 8. **It is NOT closed
here.** §8 below adds three entries and restates the true standing, which is what
every document since `04_1d` has done and is exactly the accumulation the item
exists to end. **The index still lives inside a frozen document and still says
nine in its own text.** **Owed before Point 4's closing record. No owner at this
commit.**

**THE FOUR POINT 6 OBLIGATIONS AT `04_2b` §5.4 ARE UNMOVED AND NONE IS A FREEZE
PRECONDITION.**

### 7.3 THE COUNT

**Thirteen on entry. Two closed -- the `STANDING_RULES` amendment and the guard's
register update. Four added. Eleven carried unchanged.**

**THE ARITHMETIC: 13 - 2 + 4 = 15, AND 11 + 4 = 15 FROM THE OTHER SIDE.** Both are
shown because a register whose parts and whose total are stated by the same act is
a register nobody has checked.

> ### **FIFTEEN OPEN ITEMS. NOT ONE HAS AN OWNER.**

### 7.4 IS THAT A PROBLEM THE REGISTER CAN SOLVE

> ### **NO. THE REGISTER IS AN INSTRUMENT FOR RECORDING WHAT IS OWED, AND
> ### OWNERSHIP IS NOT A PROPERTY OF THE THING OWED. IT IS A PROPERTY OF WHO IS
> ### DIRECTED TO DO IT, AND THE REGISTER IS NOT THE DIRECTOR.**

**THE EVIDENCE THAT THE REGISTER IS WORKING IS THE SAME EVIDENCE THAT IT CANNOT
SOLVE THIS.** `docs/design/04_2b_point_4_decomposition.md` §5.3 found that **four
of the nine items the closing record required disposed of had never been cited by
any Point 4 document** -- and it found that by being written. The register is the
only reason those four are visible. **Fifteen items with no owner is a register
doing its job against a process that has no assignment step.**

**WHAT WOULD ACTUALLY CHANGE IT, STATED AND NOT COMMITTED.** Every item on this
register was created by a step that could not do it, and assigned by nobody
because **the only actor who assigns work in this project is the project owner,
and no committed document says so or gives the register a route to them.** The
gap is not in the register's form. **It is that the register has no reader who is
obliged to read it**, and a document cannot commit an obligation on a person
outside the document's own discipline.

**ONE THING IS WITHIN REACH AND IS OFFERED RATHER THAN COMMITTED.** The freeze
preconditions at `04_2b` §4.3 **are** a forcing function -- items 5 and 7 bear on
preconditions 4 and 5, and those preconditions must be evaluated before 4.7.
**Marking, for each register item, whether it blocks the freeze would convert part
of the register from a list into a checklist with a deadline.** Nine of the
fifteen do not block it, which is why it is not proposed as a general answer.
**Not committed here: it is a change to `04_2b` §5's form, and that document is
frozen.**

---

## 8. THE ERRATA

**THREE ENTRIES, IN THE CONSOLIDATED INDEX'S FORM**, per
`docs/design/04_1c_pre_commitments.md` §5.4's maintenance rule, which requires
that any document making a correction to a frozen artifact adds its entry in the
same commit. **The index itself cannot be edited, being inside a frozen document,
so they are added here in its form and their standing is restated at §8.4.**

### 8.1 ENTRY 13

> **ENTRY 13. `docs/prompts/STANDING_RULES.md` §0.1 -- the claim about the
> manifest's token content.** *Target: a transcription that binds nothing, which
> is a third category §8.4 addresses.* **SAID:** "`docs/prompts/MANIFEST.md`
> contains none of the tokens." **CORRECT:** it contains one, in the prose
> describing what `docs/design/00_standing_brief.md` transcribes, and it contained
> it at `c6b71c5` -- the commit that introduced both files. **The claim was false
> when written**, verified by extracting the manifest at all twenty revisions that
> have touched it. **CORRECTION LIVES AT:** this document, §2.4 correction 6.
> **Not operative** -- the occurrence is a name and not a figure, and §0.1's
> enumeration of its own four permitted places is correct and complete, verified
> line by line.

### 8.2 ENTRY 14

> **ENTRY 14. `docs/design/04_2e_housekeeping.md` §5.4 -- the two standing closing
> items, committed twice.** *Target: specification.* **SAID:** the two closing
> items are "practice that `docs/prompts/STANDING_RULES.md` §12.5 records as
> committed nowhere", and "THEY ARE COMMITTED HERE, for report-backs."
> **CORRECT:** they were committed at `docs/design/04_1d_standing_practices.md`
> §1.2, at commit `fc8933f`, two days earlier, as one of that document's four
> rules and in the same words. The statement about §12.5 is true; the inference
> from it to the tree is not. **CORRECTION LIVES AT:** this document, §2.5.
> **Partly operative** -- the rule binds either way and no report-back obligation
> changes; what is corrected is §5.4's account of what it was doing, and its
> ground, which had expired.

### 8.3 ENTRY 15

> **ENTRY 15. `docs/design/04_2b_point_4_decomposition.md` §2.2 and §2.3 -- the
> 4.1c document counts.** *Target: specification.* **SAID:** 4.1c is "six design
> documents and four reports" (§2.2), and "4.1c WAS SPLIT INTO SIX DESIGN
> DOCUMENTS MID-COURSE" (§2.3). **CORRECT:** **seven design documents and three
> reports**, all ten of which existed at that document's own commit `eb696f5`, and
> all ten of which §2.2 enumerates correctly in the bullet that miscounts them.
> **CORRECTION LIVES AT:** this document, §4.1. **Not operative** -- §2.3's
> substantive finding, that the decomposition followed the findings rather than
> preceding them, is unaffected and is if anything strengthened by the seventh
> document.

### 8.4 THE INDEX'S STANDING, AND A CATEGORY IT DOES NOT HAVE

> ### **THE INDEX STANDS AT NINE ENTRIES IN ITS OWN TEXT AND AT FIFTEEN IN FACT** --
> ### nine at `docs/design/04_1c_pre_commitments.md` §5, entry 10 at
> ### `docs/design/04_1d_standing_practices.md` §4.1, entries 11 and 12 at
> ### `docs/design/04_2e_housekeeping.md` §3.1 and §4.2, and entries 13, 14 and 15
> ### here.

**ENTRY 13's TARGET IS A CATEGORY THE INDEX'S SCOPE DOES NOT NAME.**
`docs/design/04_1c_pre_commitments.md` §5.2 admits two targets, **specification**
and **evidence**, and `docs/prompts/STANDING_RULES.md` is neither: it creates no
rule and records no measurement. **`docs/design/04_2a_artifact_containment.md`
§6.3 met the same boundary from the other side and declined to add its entry**,
its target being a chat report-back, while writing the entry in the index's form
so a future holder could adopt it.

**THIS DOCUMENT TAKES THE OTHER ROUTE AND ADDS ENTRY 13, AND THE GROUND IS
NARROW.** A briefing is a **committed, frozen artifact in the tree** that a reader
can be misled by, which a chat message is not. §2.3 now governs it as a class with
a stated discipline, which no committed document had done before this one. **The
distinction from `04_2a` §6.3 is the file's presence in the repository, not a
judgement that the earlier call was wrong.** A reader who holds that the index
should carry only the two named targets will read fourteen and not fifteen, and
the entry is written so that reading is available.

---

## 9. THE LEDGER

### 9.1 THE TOTAL, READ

**`docs/design/04_3a_metric_vocabulary.md` §10.1 states the total is 52** and adds
no instance, reading it from `docs/design/04_2e_housekeeping.md` §7.3's
"51 + 1 = 52". **The total read is 52**, so the instances below take **(53)**,
**(54)**, **(55)** and **(56)**.

**THE CHAIN WAS WALKED IN FULL RATHER THAN TAKEN ON TRUST**, from
`docs/design/04_0_divergence_disposition_amendment_2.md` §5's "32 + 4 = 36" to
`04_3a` §10.1. **It is contiguous from (1) to (52), no number is used twice and
none is skipped, and every figure a document reads matches the file it cites.**
**Two documents read past their immediate predecessor** -- `04_1c_level_method.md`
§8 and `04_1d_standing_practices.md` §5.1 both read
`04_1c_denominator_choice.md`, skipping one and three documents respectively --
and in both cases the figure is 43 either way, so the arithmetic is unaffected.
**Recorded, not logged: no committed rule requires reading the immediate
predecessor, only the most recent document stating a total, and 43 was the most
recent figure by either route.**

### 9.2 INSTANCE (53)

**A DESIGN DOCUMENT STATED THE SIZE OF A SET IN THE SAME SENTENCE IN WHICH IT
ENUMERATED THE SET, AND THE TWO DISAGREED.**
`docs/design/04_2b_point_4_decomposition.md` §2.2 says "six design documents and
four reports" and lists seven and three; §2.3 repeats the six.

**SUB-CLASS: instance (50)'s, (51)'s and (52)'s** -- a statement about the
repository written from a mental model of it rather than from the repository.
**IT IS THE PUREST FORM OF IT YET LOGGED**, because the correct answer was not
merely available, it was **in the same bullet**, and the count was still taken
from somewhere else. **The chain is (23) to (26), then (33), (35), (39), (44),
(50), (51), (52) and now (53).**

### 9.3 INSTANCE (54)

**AN INDEX STATED THE SIZE OF ITS OWN OMITTED SET AS THREE, HAVING ENUMERATED SIX
OF THEM IN AN EARLIER SECTION OF THE SAME FILE.**
`docs/prompts/MANIFEST.md` §5 against its own §3.

**LOGGED SEPARATELY FROM (53) ON THE COUNTING METHOD**, argued at §4.5. **The
target's frozen status is irrelevant to the class**: a defect is counted where it
occurs, and `docs/handoff/31_point_5_closing.md` §7.1 counts defects a committed
artifact records, not defects a frozen artifact records. **No erratum is
created**,
because `docs/prompts/MANIFEST.md` is a living index by its own §0 and is
corrected
in place in this commit.

### 9.4 INSTANCE (55)

**A DESIGN DOCUMENT CREATED A RULE THAT ALREADY BOUND, ON THE GROUND THAT A
BRIEFING RECORDED IT AS UNCOMMITTED.** `docs/design/04_2e_housekeeping.md` §5.4
against `docs/design/04_1d_standing_practices.md` §1.2.

**IT IS THE SUB-CLASS WITH ONE FEATURE THE OTHERS DO NOT HAVE**, and the feature
is why §2 of this document exists: **the document that erred read a source, cited
it accurately, and was still wrong about the tree, because the source it read was
a transcription that had expired.** (50), (51), (52) and (53) each record someone
not checking. **(55) records someone checking the wrong thing** -- and the wrong
thing was the file the project puts in front of every step first.

**A CLOSE CALL, ARGUED BOTH WAYS.** The re-commitment is harmless in operation:
the rule binds, its scope in `04_2e` is a subset of `04_1d`'s, and no report-back
obligation is different under either. **A reader could hold that a redundant
commitment with a stale justification is untidy rather than defective, and reach
52 + 2 = 54.** It is logged because the defect is not the redundancy but **the
reasoning** -- a committed document asserting it is creating something it is not,
from a premise about the repository that was false -- which is the sub-class
exactly, and because leaving it unlogged would remove the only committed evidence
that the briefing's staleness has cost anything. **A reader who disagrees can
follow the argument here rather than the conclusion.**

### 9.5 INSTANCE (56)

**AN INDEX REPORTED THE RESULT OF A CHECK IT STATED IT HAD RE-RUN, AND THE
REPORTED RESULT IS NOT WHAT THE CHECK RETURNS.**
`docs/prompts/MANIFEST.md` §0.1's cross-check figures, established at §4.6.

**SUB-CLASS: instance (37)'s** -- the recurring class applied to a verification
criterion rather than to a decision threshold. **(37) was a check wrong about what
it matched; this is a check whose result was wrong about what it returned.** The
family is one where the verification apparatus itself carries the defect, which is
the worst place for it because a reader has no independent way to discount a
figure attributed to a run.

**LOGGED SEPARATELY FROM (54) ON THE ARGUMENT AT §4.5.** Same file, different
section, different quantity, different method, neither derived from the other.

### 9.6 THE TOTAL

**52 + 4 = 56.**

**No earlier instance is renumbered or recounted**, and the ledger remains
contiguous from (1) to (56).

---

## 10. WHAT THIS DOCUMENT DOES NOT DO

**IT DECIDES NOTHING ABOUT 4.3's REMAINDER.** The decision tier's membership, the
routing divergence at `docs/design/04_3a_metric_vocabulary.md` §1.4, the
denominator shape for any metric and the geometry hand-forward are all untouched.

**IT COMMITS NO METRIC, NO THRESHOLD, NO KILL CONDITION AND NO GATE.**

**IT DOES NOT REGENERATE EITHER BRIEFING**, and it edits neither.

**IT DOES NOT CLOSE THE STANDALONE ERRATA INDEX ITEM**, and adding three entries
outside a frozen index makes that item more urgent rather than less.

**IT SETTLES NO FREEZE PRECONDITION.** §6.3's hashing bears on none of the six at
`docs/design/04_2b_point_4_decomposition.md` §4.3, and §7.2's two closures bear on
precondition 5 only in the sense that the guard now states the rule it enforces --
**item 5 remains open and precondition 5 remains unevaluable until it is
settled**, per `04_2b` §5.1.

**IT REOPENS NOTHING.** §5.4's verdict of NO BREACH leaves every Point 4 and Point
5 commitment standing.

**AND IT DOES NOT ESTABLISH THAT NO OTHER SURFACE IS UNMANAGED.** §5's
adjudication is over `docs/design/` and `docs/handoff/`. **`reports/` was not
adjudicated here and is not claimed to be clean**; report 41's §2.5 reached two
files outside `data/` and no document has swept that directory as a whole.
**Recorded as a limit of this document, not as a finding about that directory.**

---

## 11. CHANGE DISCIPLINE

**THIS DOCUMENT IS FROZEN ON COMMIT AND JOINS THE FROZEN SPECIFICATION**, per
`docs/design/04_0_divergence_disposition_amendment_2.md` §2.

**A CHANGE TO ANY DECISION IN IT IS A NEW DOCUMENT WITH ITS OWN COMMIT AND AN
EXPLICIT STATEMENT OF WHAT IS AMENDED AND WHY**, named
`docs/design/04_3b_record_reconciliation_amendment_1.md`, per the naming
convention `docs/design/04_1a_denomination.md` §8 sets.

> ### **THE ONE ASYMMETRY, STATED SO IT IS NOT MISTAKEN FOR AN INCONSISTENCY:
> ### THIS DOCUMENT IS AMENDED AND NEVER REGENERATED, WHILE THE FILES §2.3
> ### GOVERNS ARE REGENERATED AND NEVER AMENDED.**

**THAT IS THE WHOLE CONTENT OF §2.2.** This document decides things, so its text
at this commit is evidence of what was decided before what came next. **A briefing
decides nothing, so its text at any past commit is evidence of nothing.** The two
disciplines differ because the artifacts differ, and a project that applied one
rule to both would be protecting a file that needs no protection at the cost of a
reader who needs a current one.

**SECTIONS §2.3, §5.4, §5.5, §5.7 AND §6.3 ARE THE COMMITMENTS.** Everything else
is finding, argument or record.
