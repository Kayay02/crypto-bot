# THE STANDING PRACTICES, COMMITTED

**Point 4, sub-point 4.1d. Four rules committed, three conventions recorded, one
erratum logged, one ledger instance logged. Nothing is computed or derived.**

## 0. WHAT THIS DOCUMENT IS

**A PRE-REGISTRATION, FROZEN ON COMMIT.** It joins the frozen specification on its
commit, per `docs/design/04_0_divergence_disposition_amendment_2.md` §2's
open-forward clause.

**IT ACTS ON `docs/prompts/STANDING_RULES.md` §12**, which listed seven practices
every recent step has followed and that no committed document stated. That section
recorded them **so they could be committed properly later or dropped.** This is
that step.

### 0.1 IT DOES NOT REPRODUCE THE BANNED NAMES

**THIS DOCUMENT CONTAINS NONE OF THE BANNED TOKENS**, including in §3's erratum,
which is about that list. It does not need to: **the canonical list now lives in
code, at `src/firewall.py`**, and the prose being corrected is at
`docs/handoff/31_point_5_closing.md` §11. §3 points at both and characterises the
divergence rather than reproducing either.

**A NARROWER CONSTRUCTION THAN AN ERRATUM STRICTLY PERMITS**, and it is stated as
one so a reader can go and compare the two sources rather than assume this
document has summarised them fully.

---

## 1. THE FOUR RULES

**Each is transcribed from `docs/prompts/STANDING_RULES.md` §12 with its section
cited. Three are transcriptions of practice. The fourth, §1.3, is a rule this
document CREATES, and §1.3 says so.**

### 1.1 THE STANDARD VERIFICATION SEQUENCE

**Transcribed from `docs/prompts/STANDING_RULES.md` §12.6.**

> ### A STEP PERFORMS, AND REPORTS: the pre-existence check on target paths; hash
> ### recomputation of named documents; the test count before and after; the `git
> ### status` and `git diff --stat` confirmation; the banned-token grep; the
> ### non-ASCII inventory; committing alone; and reporting SHA-256, line count and
> ### commit hash.

**ONE ELEMENT WAS ALREADY COMMITTED** and is not newly created here:
`docs/handoff/31_point_5_closing.md` §13's *"target paths are checked before
writing"*. **The remaining elements are committed by this document.**

**WHY IT BINDS.** Each element is the evidence for a claim the step makes about
itself. A step that omits the pre-existence check may have overwritten an artifact
and not know; one that omits hash recomputation may have built on a document that
changed under it. **The sequence is not a formality; it is where the claims come
from.**

### 1.2 THE REPORT-BACK FORMAT

**Transcribed from `docs/prompts/STANDING_RULES.md` §12.5.**

> ### PLAIN PROSE LINES, ONE FACT PER LINE, NO TABLES, NO ALIGNED COLUMNS.

> ### AND THE TWO STANDING CLOSING ITEMS, WHICH ARE REPORTED EVERY TIME AND NOT
> ### ONLY WHEN THEY HAVE CONTENT:
>
> - **ANY PLACE WHERE A REQUIREMENT CONTRADICTED A CONSTRAINT, STATED RATHER THAN
>   RESOLVED.**
> - **ANYTHING READABLE AS NARROWER OR BROADER THAN INTENDED.**

**PARTLY COVERED BEFORE THIS DOCUMENT.** `docs/handoff/23_point_1_reopened_closing.md`
§5.1 commits *what* the report-back carries — hash, line count, commit hash, test
count. **It says nothing about the prose format or the two closing items**, which
this document commits.

**WHY THE TWO CLOSING ITEMS BIND.** The first is the mechanism by which every
instance of the sub-class at `docs/design/04_1b_tolerance_and_branch.md` §7 came to
be logged rather than silently resolved. The second is how a step's own scope
judgements reach the record instead of staying with whoever made them. **Both are
substantive disclosures, not formatting.**

**REPORTED EVEN WHEN EMPTY.** A closing item that appears only when it has content
tells a reader nothing when it is absent — they cannot distinguish "none" from
"not looked for". This follows the treatment
`docs/design/06a_exit_resolution_spec_amendment_1.md` §6.2 gives a zero-valued
branch: **reported as zero rather than omitted.**

### 1.3 THE SINGLE-FILE RULE AND ITS TWO EXEMPTIONS

> ### THIS RULE HAS NEVER BEEN COMMITTED ANYWHERE. THIS DOCUMENT CREATES IT. IT IS
> ### NOT A TRANSCRIPTION.

`docs/prompts/STANDING_RULES.md` §12.7 records the search that establishes this:
**"single-file", "exactly one file" and "one file per" over `docs/design/` and
`docs/handoff/` returned nothing.** That section states the consequence plainly —
the exemptions could not be transcribed as standing, **because the rule they except
from did not exist as a committed rule.**

**THE RULE, STATED IN THE FORM RECENT STEPS HAVE FOLLOWED:**

> **A STEP CREATES THE FILES ITS INSTRUCTION NAMES AND MODIFIES NOTHING ELSE. A
> DECISION IS COMMITTED ALONE. A DERIVATION AND ITS TESTS ARE COMMITTED TOGETHER
> AND WITH NOTHING ELSE.**

**AND THE TWO EXEMPTIONS:**

> **`docs/prompts/MANIFEST.md` AND THE CONSOLIDATED ERRATA INDEX MAY BE UPDATED BY
> ANY STEP IN THAT STEP'S OWN COMMIT, AND SUCH AN UPDATE IS NOT A MODIFICATION OF
> A FROZEN ARTIFACT.**

> ### THESE ARE EXEMPTIONS FROM A RULE THIS DOCUMENT IS ESTABLISHING, NOT FROM ONE
> ### THAT PRE-EXISTED. A READER SHOULD NOT TAKE THEM AS CARVE-OUTS FROM SOMETHING
> ### OLDER.

**THE ERRATA-INDEX EXEMPTION HAS ONE REAL PRECEDENT**, and it is an obligation
rather than an exemption: `docs/design/04_1c_pre_commitments.md` §5.4 requires any
document correcting a frozen artifact to add its entry **in the same commit.** That
requirement is unsatisfiable under a single-file rule without this exemption, which
is why the exemption is stated rather than left implied.

**WHY THE RULE BINDS.** The commit order is this project's only durable evidence
about what was known when — `docs/design/04_0_decision_rule.md` §4 rests the entire
firewall on it. **A commit mixing a decision with the measurement it governs
destroys the property the separation exists to produce**, and does so invisibly,
because the mixed commit looks exactly like a tidy one afterwards.

**THE RULE AS STATED IS LOOSER THAN "EXACTLY ONE FILE"**, and deliberately: recent
steps have committed a derivation module together with its tests, and a report
together with the module it describes. **Stating it as "exactly one file" would
make every one of those commits a breach retrospectively.** The looseness is
preserved rather than tightened, per the discipline
`docs/prompts/STANDING_RULES.md` §0 records.

### 1.4 THE VERBATIM-TRANSCRIPTION CONTENT PROHIBITION

**Transcribed from `docs/prompts/STANDING_RULES.md` §12.1.**

> ### AN INSTRUCTION REQUIRING VERBATIM TRANSCRIPTION OF A SOURCE TEXT MAY NOT
> ### ALSO CONSTRAIN THE CONTENT OF THE TRANSCRIBED TEXT.

**WHY IT NEEDED COMMITTING SEPARATELY.**
`docs/design/04_0_divergence_disposition_amendment_2.md` §6 logs it as **instance
(33)**, and `docs/design/04_1b_tolerance_and_branch.md` §7 groups it with the
drafting rule against pre-stating a delegated value. **But that rule's wording does
not reach it** — a verbatim requirement pre-states nothing; it forbids the
implementing session from altering anything, which a content constraint then
requires. **The two requirements are unsatisfiable together and no committed rule
said so.**

**IT IS A PROHIBITION ON THE DRAFTING SIDE**, following §7's reason: by the time
the implementing session meets it, both readings are already unsatisfiable and all
it can do is report.

---

## 2. THE THREE CONVENTIONS

**RECORDED, NOT COMMITTED AS RULES. FOLLOWING THEM IS EXPECTED; DEPARTING FROM
THEM IS UNTIDY AND IS NOT A DEFECT.**

### 2.1 THE PERMITTED NON-ASCII SET

**From `docs/prompts/STANDING_RULES.md` §12.3.** A document contains no non-ASCII
character other than the section sign and the em dash.

**Related but not the same**, per that section: instance (37) at
`docs/design/04_0_decision_rule.md` §9 concerns a check that matched em dashes when
it meant box-drawing characters, **which is a fact about a check rather than a
formatting rule.**

### 2.2 THE OUTPUT FORMATTING PRACTICE

**From `docs/prompts/STANDING_RULES.md` §12.4.** Markdown only; no box-drawing
characters, no pipe tables, no aligned-column ASCII.

### 2.3 THE SUBSTRING-COLLISION PRACTICE

**From `docs/prompts/STANDING_RULES.md` §12.2.** Prose documents have no AST, so
§6.1's verification rule cannot apply to them. Ordinary English words colliding
with a banned token by substring are therefore **avoided in drafting rather than by
reinterpreting the check.**

> ### THE KNOWN COLLISION: WORDS BUILT ON THE VERB MEANING "TO MAKE SHARP" CONTAIN
> ### A BANNED TOKEN AS A SUBSTRING.

**It is named here without being written**, per §0.1. `docs/prompts/STANDING_RULES.md`
§12.2 writes it out, and a reader who needs the exact string will find it there.

---

## 3. WHY THE PARTITION FALLS WHERE IT DOES

### 3.1 THE TEST

> ### A RULE BINDS AND ITS BREACH IS A DEFECT — LOGGABLE TO THE LEDGER. A
> ### CONVENTION IS FOLLOWED AND ITS BREACH IS UNTIDY.

**THE DISCRIMINATOR IS WHETHER A BREACH DAMAGES THE RECORD.** The verification
sequence, the two closing items, the single-file rule and the
verbatim prohibition each protect something a later reader depends on: that a claim
was checked, that a scope judgement was disclosed, that commit order means what it
appears to mean, that an instruction was satisfiable. **A breach of any of them
leaves the record saying something untrue about itself.**

**A STRAY EM DASH, A PIPE TABLE OR A COLLIDING WORD DOES NOT.** The document still
says what it says. Nothing a reader relies on becomes false.

### 3.2 TWO ITEMS ARE ARGUABLY ON THE OTHER SIDE, AND ARE NAMED

**THE PROSE FORMAT HALF OF §1.2 IS ARGUABLY A CONVENTION.** "Plain prose lines, one
fact per line, no tables, no aligned columns" is a presentation rule, and breaching
it damages nothing. **It is committed as a rule because it is inseparable in
practice from the two closing items**, which are not presentational — a report-back
that abandons the format tends to abandon the closing items with it. **A reader who
holds that only the two closing items should bind is not obviously wrong**, and
under that reading §1.2 splits into one rule and one convention.

**THE SUBSTRING-COLLISION PRACTICE AT §2.3 IS THE STRONGEST CANDIDATE FOR
RULE-HOOD.** A collision causes a verification check to fire falsely against a
clean document, and `docs/design/04_1a_denomination.md` §6's standing inclusion
criterion **logs exactly that as a ledger instance** when the remediation on offer
would degrade an otherwise correct artifact. **So a collision can already produce a
ledger instance without this document making it a rule.**

**IT IS LEFT AS A CONVENTION** on the ground that the defect in such a case is **the
check's**, not the document's — which is what instance (37) decided when a check
matched em dashes and the document was correct. **Making avoidance a rule would put
the obligation on the wrong side.** The alternative reading is available and is
stated here rather than left to be discovered.

---

## 4. ERRATUM AGAINST `docs/handoff/31_point_5_closing.md` §11

### 4.1 THE ENTRY, IN THE CONSOLIDATED INDEX'S FORM

**ENTRY 10. Point 5 closing record §11 — the prose statement of what the firewall
forbids.** *Target: evidence.* **SAID:** a prose sentence naming ten items as the
quantities that may not exist. **CORRECT:** the enforced guard carries **twelve**
names, and it differs from the prose in **spelling** as well as membership — the
prose uses spaced two-word forms and a following noun where the guards use single
underscored tokens, so **two prose items correspond to three enforced names and one
prose item corresponds to a shorter enforced token.** The canonical list is now at
`src/firewall.py`, which is where a reader should take the membership from.
**CORRECTION LIVES AT:** this document, §4. **Not operative** — the record's §11
claim, that no such figure exists in the repository, is unaffected; what is
corrected is its enumeration of the set.

### 4.2 THE INDEX'S NEXT HOLDER MUST CARRY IT

**`docs/design/04_1c_pre_commitments.md` §5 IS FROZEN AND IS NOT EDITED.** Its §5.4
maintenance rule requires the entry to be added in the same commit as the
correction; **this document is that entry, recorded here because the index cannot
be edited.**

> **THE INDEX STANDS AT NINE ENTRIES IN ITS OWN TEXT AND AT TEN IN FACT. THE NEXT
> DOCUMENT TO HOLD THE INDEX MUST CARRY ENTRY 10 FORWARD.**

**A GAP THE MAINTENANCE RULE DID NOT ANTICIPATE**, recorded rather than worked
around: the rule requires same-commit entry into a document that its own change
discipline forbids editing. **Every correction after the index's own commit is in
the same position.**

### 4.3 WHY IT MATTERED

**The divergence was not cosmetic.** `docs/prompts/STANDING_RULES.md` §1.2 found the
list in three forms, and the survey behind commit `47a26de` found **four test
modules enforcing a nine-name variant** — a guard with three holes in it, passing
silently. **The prose statement was one of the three forms and the one a reader
would most naturally take as authoritative**, being in the closing record's firewall
section.

**ALIGNING ALL EIGHTEEN ENFORCEMENT SITES CAUSED NO TEST TO FAIL**, which
establishes that nothing in those four modules had fallen through the holes.

---

## 5. THE LEDGER

### 5.1 THE TOTAL, READ

**`docs/design/04_1c_denominator_choice.md` §5.5 states "42 + 1 = 43". The total
read is 43**, so the instance below takes **(44)**.

### 5.2 INSTANCE (44)

**AN INSTRUCTION STATED THAT A FILE'S LISTING OF THE BANNED SET WAS "THE ONE
PERMITTED OCCURRENCE" OF THOSE TOKENS, WHILE ITS OWN REQUIREMENTS DEMANDED FOUR
SEPARATE OCCURRENCES.**

It arose in the instruction that produced `docs/prompts/STANDING_RULES.md`. The
requirements demanded the tokens appear in four places: quoting the closing
record's statement of what the firewall forbids; listing the enforced set; naming
the three the variant omits, without which the divergence is not statable; and
naming the known substring collision. **The constraint permitted one.**

> **IT PRE-STATED A COUNT ITS OWN REQUIREMENTS DETERMINED.**

**SUB-CLASS: internal contradiction between an instruction's constraints and its
requirements** — the sub-class `docs/handoff/31_point_5_closing.md` §7.2 records as
instances **(23) to (26)**, and which `docs/design/04_1b_tolerance_and_branch.md` §7
records continuing at **(33)**, **(35)** and **(39)**. **This is its fourth
occurrence in Point 4.**

**THE IMPLEMENTING SESSION REPORTED THE CONTRADICTION RATHER THAN RESOLVING IT**,
and **corrected the file's own self-description rather than dropping required
content** — `docs/prompts/STANDING_RULES.md` §0.1 now enumerates all four
occurrences and states that the instruction permitted one and required four.

**A CORRECTION TO THE INSTRUCTION THAT COMMISSIONED THIS DOCUMENT, MADE RATHER
THAN PROPAGATED.** That instruction placed instance **(43)** in this sub-class.
**It is not in it.** `docs/design/04_1c_denominator_choice.md` §5.5 assigns (43) to
**"the class applied to a specification rather than to a numerical threshold or a
decision criterion", alongside instance (40).** The committed record governs; the
sub-class chain is (23) to (26), then (33), (35), (39) and now (44).

### 5.3 THE TOTAL

**43 + 1 = 44.**

**No earlier instance is renumbered or recounted**, and the ledger remains
contiguous from (1) to (44).

### 5.4 A TRANSPARENCY NOTE, NOT AN INSTANCE

**`docs/prompts/STANDING_RULES.md` §12.2 RECORDS THAT A WORD COLLIDING WITH A
BANNED TOKEN BY SUBSTRING WAS FOUND AND REWORDED IN
`docs/design/04_1c_denominator_choice.md` BEFORE THAT DOCUMENT WAS COMMITTED, AND
THAT THE FILE CARRIES NO NOTE OF IT.**

**IT IS STATED HERE SO THE ALTERATION IS ON THE RECORD.** The word was in a
sentence about earlier reports having clarified a picture; it was replaced with a
synonym and nothing else in the file moved. **The document was correct before the
change and correct after it**, and the change was made so a raw-text firewall grep
over the document would not fire.

**NOT LOGGED AS A LEDGER INSTANCE.** Under
`docs/design/04_1a_denomination.md` §6's standing inclusion criterion, a falsely
firing check is logged **if and only if the immediate remediation on offer would
have degraded an otherwise correct artifact.** Substituting one ordinary synonym
for another degraded nothing. **The criterion is applied rather than the case being
decided on its feel**, which is what that criterion exists for.

**IT IS RECORDED ANYWAY**, because the alternative — an undocumented edit made to
satisfy a check — is exactly the shape of thing this project logs, and a reader
comparing drafts should not have to discover it.

---

## 6. WHAT THIS DOCUMENT DOES NOT DO

**IT COMPUTES AND DERIVES NOTHING.** No tolerance value, floor width or level
appears.

**IT CHANGES NO CODE.** Commit `47a26de` changed code and tests; this commit
changes documents. Neither touches the other's files.

**IT CREATES NO RULE BEYOND §1.3**, which says so in its own text. §1.1, §1.2 and
§1.4 transcribe practice; §2 records conventions without binding them.

**IT DOES NOT AMEND `docs/prompts/STANDING_RULES.md`.** That file's §12 continues
to describe these seven items as uncommitted, which was true when it was written.
**A reader consulting it alone will find that section out of date as to §1's four
items**, and this sentence is the notice of that.

---

## 7. CHANGE DISCIPLINE

**A CHANGE TO ANY COMMITMENT HERE IS A NEW DOCUMENT WITH ITS OWN COMMIT AND AN
EXPLICIT STATEMENT OF WHAT CHANGED AND WHY — NEVER A SILENT EDIT.** It would be
`docs/design/04_1d_standing_practices_amendment_1.md`.

**A SILENT EDIT IS A CONTAMINATION EVENT.**

**THE CLAUSE MOST EXPOSED IS §1.3.** It is the only rule here that did not exist
before, it binds the mechanism the whole project's evidence rests on, and it will
first be inconvenient at the moment a step wants to fold one more file into a
commit. **The exemptions are stated in §1.3 exhaustively for that reason: a third
exemption is an amendment, not a judgement call.**

---

**Committed alone, changing no code. Four practices committed as rules, one of
which this document creates rather than transcribes and says so; three recorded as
conventions with the two arguable cases named and argued on both sides; one erratum
logged against a frozen record's enumeration of the banned set, with the index gap
that prevents its being filed in place recorded rather than worked around; one
ledger instance logged at (44) with a correction to the instruction that
commissioned it; one undocumented alteration put on the record and explicitly not
logged, under a criterion applied rather than felt.**
