# REPORT 45 -- STEP REPORT-BACK: SUB-POINT 4.3b AND THE GUARD

## 0. THE GENRE, AND THE FORMAT

**A STEP REPORT-BACK, NOT AN ANALYSIS REPORT.** Declared here because
`docs/design/04_2e_housekeeping.md` §5.2 files both kinds in one numeric sequence
under `docs/handoff/` and requires the genre to be carried by the document.

**Written in the format `docs/design/04_1d_standing_practices.md` §1.2 commits:
plain prose lines, one fact per line, no tables, no aligned columns.**

**No banned name appears in this document.** Where a quantity must be referred to
it is referred to by citation, per `docs/design/04_2a_artifact_containment.md`
§0.1.

**Nothing was computed. No file under `data/` was opened. No prohibited artifact
was opened.**

---

## 1. THE STEP, AND A REQUIREMENT THAT CONTRADICTED A CONSTRAINT

The step was commissioned as two commits: a reconciliation document, then a code
fix to the containment guard.

Commit one is `48d60f3`, carrying `docs/design/04_3b_record_reconciliation.md` and
`docs/prompts/MANIFEST.md`.

Commit two is the commit carrying this file, `tests/test_containment_guard.py` and
`docs/prompts/MANIFEST.md`.

**THE CONTRADICTION, STATED AND NOT RESOLVED.** The instruction constrains commit
one to `docs/design/04_3b_record_reconciliation.md` "committed alone with the
manifest", constrains commit two to "code only", and requires a report-back "to a
committed file per the protocol" covering both commits.

`docs/design/04_2e_housekeeping.md` §5.2 requires a report-back to be committed in
the same commit as the step it reports.

A report-back covering commit two cannot be in commit one, because commit two has
not happened and because commit one is constrained to two named files.

A report-back is a document, so on the letter of "commit two changes code only" it
cannot be in commit two either.

The three requirements are not satisfiable together and the implementing session
reports rather than resolves, per `docs/design/04_1b_tolerance_and_branch.md` §7.

**The reading taken: this file is in commit two, with the manifest entry its
maintenance rule requires.** The ground is that §5.2 is committed specification
and "code only" is an instruction constraint, and that commit `3e35ba5` is the
standing precedent -- a code step whose commit carried its own report-back
document, its manifest entry, and the code.

---

## 2. THE MANIFEST

The manifest hash on entry was
`151a3634b3f8432cd80e5e235a7c2760a93e45e4d1267e01c3de750858d6be3d`, at 693 lines,
carrying 66 hashed entries.

**All 66 were recomputed against the working tree. 66 matched exactly. Zero
mismatches. Zero listed paths absent.**

The manifest now carries 80 hashed entries and all 80 were recomputed and matched
after the edit.

Every file under `docs/design/` and `docs/handoff/` is now indexed. The only
unindexed paths in those directories are `.gitkeep` and an ignored `.DS_Store`.

---

## 3. THE CLAIMS IN THE INSTRUCTION THAT WERE WRONG

**Five, each verified against the tree before being acted on, and none
propagated.** They are recorded in full at
`docs/design/04_3b_record_reconciliation.md` §1.3.

Two of the six named handoff documents carry outcome quantities, not six.

`docs/handoff/06_structural_outcome.md` contains no occurrence of any enforced
name anywhere in the file.

`docs/handoff/19_timeframe_rule.md`'s two occurrences are a declaration that no
such quantity is computed anywhere in the step it reports.

The six unindexed documents and the outcome-bearing documents are not the same
set, so the coincidence the instruction asks to be explained does not exist.

One of the four modules the manifest's §4 listed was modified at `3e35ba5`, not
two; the second file that commit touched was not in §4's list.

The register stood at thirteen on entry, not roughly sixteen, and the figure
sixteen appears in no committed document.

The register item's wording at `docs/design/04_2b_point_4_decomposition.md` §5.5
is "Unattached; owed", not "no owner".

**One of the five originates in the read-only audit rather than in the
instruction, and is attributed there:** the audit reported six documents as
carrying outcome quantities from raw token counts without classifying the
occurrences, and that finding is superseded.

---

## 4. PART A -- THE FORM DECIDED FOR BRIEFINGS

`docs/prompts/STANDING_RULES_amendment_1.md` was verified not to exist, in the
working tree and over `git log --all --diff-filter=A`.

**The amendment mechanism is refused for briefing documents, and the file is not
written.**

The ground is that the mechanism protects a pre-registration by preserving what
makes it evidence, and a briefing is evidence of nothing.

No committed document cites `docs/prompts/STANDING_RULES.md` as the source of a
rule; that file states of itself that it creates no rule and binds nothing.

The cost of an amendment chain on a briefing is paid by a reader who reads only
the first file, which is the reader a briefing exists for.

**The discipline committed at `docs/design/04_3b_record_reconciliation.md` §2.3
has three limbs: regeneration wholesale rather than amendment; no moving figure in
a briefing, only a citation to the document that holds it; and a currency marker
naming the commit at which it was last regenerated.**

Limb two is the one that fixes the problem, because a rule and its source move
together while a figure and its source move apart silently.

All six divergences found in `docs/prompts/STANDING_RULES.md` are moving figures
and none is a rule.

**The corrections made, all taken from the tree:**

The defect-ledger total it states as 43 is 52 as read from the chain, and 56 after
this step.

The errata index it describes as at nine entries is at nine in its own text and at
fifteen in fact after this step.

The banned-name divergence it reports as unreconciled was closed at `47a26de`,
fifteen minutes after `c6b71c5` committed the claim, and that commit's message
says so in terms.

The prose limb of the same divergence was logged as errata entry 10 at
`docs/design/04_1d_standing_practices.md` §4.1, in the commit `fc8933f`.

The seven practices its §12 calls uncommitted were all dispositioned at `fc8933f`:
four committed as rules at `docs/design/04_1d_standing_practices.md` §1 and three
recorded as conventions at its §2.

Its §12.7 states the single-file rule and its exemptions are committed nowhere;
`04_1d` §1.3 creates both and says it is creating them.

The two items its §11.2 calls still owed inside Point 4 were delivered at
`eebe986` and `2a04e37`.

Its §0.1 claims `docs/prompts/MANIFEST.md` contains none of the tokens; the
manifest contains one, at line 90, and contained it at `c6b71c5`, the commit that
introduced both files.

**That last one is the only correction of the six that was wrong when written, and
it is the only one logged as an erratum.** The other five were true at their
commit and expired.

The general problem is stated at `04_3b` §2.5: a briefing that transcribes a
moving state is stale from the moment it is committed, the errata mechanism cannot
reach it because nothing was wrong when written, and the ledger cannot reach it
because a figure that moved is not the recurring class.

The harm is already in the committed record once, at
`docs/design/04_2e_housekeeping.md` §5.4, which created a rule that already bound
because it read the briefing rather than the tree.

The regeneration of both briefings, and a test enforcing limbs two and three, are
open register items with no owner.

---

## 5. PART B -- THE TWO BREACHES AND THE DISPOSITION

`docs/prompts/ORIENTATION.md` is tracked, 1,345 lines, SHA-256
`7d0e5503f6461ca5eba426465653f1a92dc5b7eeb30a7ec716e1c15913db194e`, and the
working tree copy is identical to `HEAD`.

It was introduced at `2a04e37` at 1,147 lines, modified at `7ce7f9e` to 1,169, and
modified at `eee1e18` to its present length. Three commits and no others.

**BREACH ONE, VERIFIED: `2a04e37` created two new files.** The single-file rule
was committed at `docs/design/04_1d_standing_practices.md` §1.3 at `fc8933f`,
fifteen hours earlier.

The manifest edit in that commit is exempt; `docs/prompts/ORIENTATION.md` is
covered by no exemption.

The report-back exemption at `docs/design/04_2e_housekeeping.md` §5.3 did not
exist until `8077238`, two days later, and covers only one file at the path §5.2
prescribes.

The file set of every commit from `fc8933f` to `HEAD` was enumerated. `2a04e37` is
the only single-file-rule breach in that history.

**BREACH TWO, VERIFIED BY A PROPERTY OF THE COMMIT RATHER THAN BY TESTIMONY.**
Every path introduced by any of the 118 commits on `main` was compared against its
own commit message by full path, basename, stem, sub-point rendering, report
number and every significant word of the stem.

Seventy paths fail that comparison. Sixty-eight are in bulk commits predating any
such rule. One is a false positive of the method.

`docs/prompts/ORIENTATION.md` at `2a04e37` is the only path in the whole post-rule
history whose own commit message does not name, identify or share a significant
word with it.

The consequence is that the manifest entry that commit owed was never written, in
a commit that edited the manifest, and was not written in any of the eighteen
commits since.

**The reported concurrent committer is not adopted.** The reflog carries 122
entries: 117 commits, four amends, one initial commit, and no checkout, reset,
rebase, merge or force operation anywhere. A concurrent committer leaves a
checkout or a divergent tip and there is none.

**THE DISPOSITION: indexed, and governed by the briefing discipline at `04_3b`
§2.3 on the same terms as `docs/prompts/STANDING_RULES.md`.**

Removal is refused because its §2 carries both holdout disclosures in full and not
by reference, attached to its §15 assertion that the seal is intact, which is what
`docs/design/04_0_divergence_disposition_amendment_1.md` §3 and
`docs/design/04_0_divergence_disposition_amendment_2.md` §3 require of exactly
that assertion.

Indexed and maintained is refused because it imposes an obligation nothing
enforces, which is what produced the eighteen commits of drift.

Its manifest entry records the commit at which it was last current, which makes
staleness computable from the index rather than asserted in the body.

Its content was not edited.

---

## 6. PART C -- THE COUNTS AS FOUND

`docs/design/04_2b_point_4_decomposition.md` §2.2 states 4.1c is six design
documents and four reports, and §2.3 repeats the six.

The tree holds seven files matching `docs/design/04_1c_*.md` and three matching
`docs/handoff/*4_1c*.md`.

All ten existed at `eb696f5`, and §2.2 enumerates all ten correctly in the same
bullet that miscounts them.

`docs/prompts/MANIFEST.md` §5 stated three analysis modules omitted; its own §3
names six; the tree holds seventeen files under `src/analysis/` against eleven
listed, which is six.

`docs/design/04_1f_cap_requirement.md` contains no occurrence of the word "ledger"
and has no ledger section among its eight.

**The 4.1f silence is recorded as a hole and not logged as an instance.** The
counting method counts a defect a document identifies of the recurring class; a
document that says nothing has written no criterion from a mental model, and no
committed rule requires a document adding no instance to state the total.

**A fourth was found: `docs/design/04_2e_housekeeping.md` §5.4 re-commits a rule
already committed at `docs/design/04_1d_standing_practices.md` §1.2.**

**A fifth was found by re-running a check the manifest states it ran.**
`docs/prompts/MANIFEST.md` §0.1 reported the hexadecimal cross-check as 44
occurrences, 40 resolving and 4 not.

Re-run against the `ef67cc5` tree in four variants -- two file sets by two
counting rules -- it returns 49/43/6, 49/43/6, 36/30/6 and 36/30/6.

The occurrence total moves with the counting rule and the unresolved count does
not; it is six in every variant and four in none.

The two the prior list missed are manifest-at-entry citations in reports 43 and
44, which is exactly the kind its own list enumerates, and both were orphaned by
the very revision that counted them.

The conclusion was not damaged and was re-established rather than inherited: no
string naming a file as it stands now fails to match it, and no named file is
absent.

**ONE INSTANCE OR TWO: TWO, AND FOUR IN TOTAL.** The method counts one per
distinct defect, not per symptom and not per document.

The clause forbids splitting one defect into symptoms and forbids counting one
defect once per document that repeats it, and neither applies.

The two manifest defects share a file and are still distinct: different sections,
different subject matter, different methods, and neither figure derived from the
other.

The precedent runs the same way. Instances (50), (51) and (52) are all the
citation class in three consecutive steps and were counted as three, with
`docs/design/04_2e_housekeeping.md` §7.2 naming the shared class while keeping the
separate count.

The contrary reading is recorded at `04_3b` §4.5 with the totals it would give.

---

## 7. PART D -- THE VERDICT

**NO BREACH.**

Report 41's criteria were transcribed verbatim at `04_3b` §5.1 before any finding
was stated, from that document's own §1.

One substitution was made and is stated: prose has no AST and no module reads it,
so the analogue of a file read is a citation. Every other limb was applied
unchanged.

**The BREACH limb requires a chain from an outcome quantity to a decision,
parameter or threshold committed in Points 4 or 5. It is not met.**

The forward search found the four documents carrying no outcome quantity are cited
by no Point 4 or Point 5 document at all.

The two that carry them are cited thirteen times between them, and every citation
was read in context.

Three citations take rule text from appendix M, and all three disclaim the
source's authority in their own words, unprompted, and re-derive the rule.

Two citations are of an excluded correction, two are of a filename expressly not a
figure, one takes a count of rows in a table, and five are provenance.

The backward search took nineteen numeric strings from the two documents and
searched every other document under `docs/design/` and `docs/handoff/`.

Sixteen return nothing. Three return matches and all three were opened: two
resolve to the derived stop floor, which is a cost quantity that originates in one
of the six and travels into the closing record rather than out of it, and one
resolves to a funding comparison figure that shares four digits with an unrelated
quantity.

Proximity was considered and refused: appendix M holds both a figure and a rule,
and the criteria say in terms not to infer from proximity.

**The INDETERMINATE limb is not met.** These are prose documents under `docs/`,
which nothing prohibits opening, and each has a single introducing commit with a
date.

**The NO BREACH limb is met on all three of its conditions.**

**CONTAINMENT IN THE SENSE `docs/design/04_2a_artifact_containment.md` §3.2 USES
IS NOT OWED, AND COMMITTING IT WOULD BE A DEFECT.**

Three of these documents are read by the live chain, so a prohibition on opening
them is unsatisfiable.

A prose document states its own status in its own text where a serialised artifact
does not, so the hazard the prohibition addresses is absent.

The prohibition that matters is the firewall itself, which binds on the act rather
than on the file.

**Disclosure is owed and is discharged in commit one**, by indexing all six with
their status and whether each carries outcome quantities.

**THE COINCIDENCE IS NOT ONE AS STATED, AND THE REAL RELATION IS CAUSAL.**

The six unindexed documents are exactly the six `docs/handoff/` documents
committed before the thesis freeze at `02e47a5`, not one more and not one fewer.

The manifest was created at `c6b71c5`, five days after that freeze, by walking the
chain the current thesis rests on, and the chain begins at the thesis.

The presence of outcome quantities has nothing to do with it, which is why four of
the six have none.

**THEY ARE INDEXED AND THEY ARE NOT MEMBERS OF THE FROZEN SPECIFICATION.**

The open-forward clause at `docs/design/04_0_divergence_disposition_amendment_2.md`
§2 reads "subsequently" and its reference point is its own commit `fd45afd` on
2026-08-14; the two self-described pre-registrations are dated 2026-08-07 and
2026-08-09 and both precede it.

They are indexed anyway because the manifest's §0 scopes itself to every artifact
a subsequent step might need to verify, not to members.

The contrary reading is stated at `04_3b` §5.7 rather than only the conclusion.

**No chain was found, so the instruction's stop condition was not triggered.**

---

## 8. PART E -- THE ENGINE MODULES

**All five are hashed, and `src/engine/simulate.py` is added to the section.**

The stated ground for omitting them was that they are read-only dependencies and
that recent steps assert them unmodified via `git status`.

`src/engine/costs.py` was modified at `3e35ba5` and `src/engine/portfolio.py` at
`1064028`, so the second half of the ground is falsified twice.

`git status` asserts that a file matches `HEAD`, which is a different claim from
the one an index makes, and a clean tree at a modified `HEAD` is the state that
produced the stale line references that section has corrected in prose twice.

`src/engine/simulate.py` falls outside the section's former title because no
derivation calls it, and it is the module freeze precondition 3 turned on and the
module the full evaluation run executes.

The chain is about to run these modules in full evaluation mode for the first
time, and until this commit they were the least-indexed files in the repository:
twelve analysis modules producing reports nobody will re-run carried hashes, and
the four producing the irreversible result did not.

A hash is the only evidence that survives the run, because `git status` is a
statement about the moment it is run and that moment will have passed.

---

## 9. PART F -- THE REGISTER

Thirteen items on entry: eleven in the form `docs/design/04_2e_housekeeping.md`
§7.4 maintains, plus the two housekeeping items it carries separately.

Two closed: the `docs/prompts/STANDING_RULES.md` amendment, closed by deciding the
form rather than by satisfying the form it assumed; and the guard's register
update, closed by commit two.

Four added: the regeneration of each briefing, the briefing currency check, and
whether a step citing a superseded-thesis document must declare it.

Eleven carried unchanged, including the standalone errata index, which this step
makes more urgent by adding three entries outside it.

**Fifteen open items. Not one has an owner.**

**That is not a problem the register can solve.** Ownership is a property of who
is directed to do the work, and the register is not the director.

The register is why four items the closing record required disposed of were found
never to have been cited, so it is working as an instrument.

Every item was created by a step that could not do it and assigned by nobody,
because the only actor who assigns work is outside the discipline the documents
can bind.

One thing within reach is offered and not committed: marking each item for whether
it blocks the freeze would convert part of the register into a checklist with a
deadline. Nine of the fifteen do not block it, which is why it is not offered as a
general answer, and it would edit a frozen document.

---

## 10. COMMIT TWO -- THE GUARD

`tests/test_containment_guard.py` held `tests/test_sweep_bands.py` in
`UNDECLARED_READERS` while `docs/design/04_2e_housekeeping.md` §2.2 had amended
the closed set to four modules.

The module is moved into `GRANDFATHERED_TESTS`, and §2.2 is cited in the source as
the amendment that admitted it, with §2.6 cited as the section directing the move.

`UNDECLARED_READERS` is left in place as an empty tuple rather than deleted,
because the assertion over it is what §2.6 requires be kept.

An empty tuple asserted as exact says no undeclared reader exists at all, so a
fifth reader anywhere under `src/` or `tests/` still fails the guard.

The test name `test_the_UNDECLARED_readers_are_exactly_the_ones_the_audit_missed`
is deliberately unchanged, being the identity under which the finding was pinned.

**THE NEGATIVE CONTROL WAS RUN TWICE, AND THE GUARD FAILED BOTH TIMES.**

A byte-copy of the fixed module was taken before breaking it, and its SHA-256 is
`6b06bfce6dba5ece7490c3538debebdef56c00287e8b7999280c9b0aef4bdc97`.

**CONTROL A: `tests/test_sweep_bands.py` removed from the grandfathered set. Two
tests failed and seventeen passed.**

`test_NOTHING_outside_the_closed_set_names_a_prohibited_artifact` failed with:
"these modules name a prohibited artifact and are not in
docs/design/04_2a_artifact_containment.md section 3.3's closed set:
{'tests/test_sweep_bands.py': ['ARTIFACT_PATH']}. A new reader joins by AMENDING
THAT DOCUMENT, not by editing this tuple."

`test_the_UNDECLARED_readers_are_exactly_the_ones_the_audit_missed` failed with:
"AssertionError: ['tests/test_sweep_bands.py']" against an expected empty set.

**CONTROL B: `tests/test_dispersion.py` removed from the grandfathered set, to
demonstrate the fifth-reader property without creating a file. The same two tests
failed**, naming `tests/test_dispersion.py` and the two path constants it reaches.

**Restored from the byte-copy after each control.** The restored file is
byte-identical to the copy, verified by `cmp` and by SHA-256.

The guard passes 19 of 19 after the restore.

---

## 11. THE FIGURES

Commit one: `48d60f3`.

`docs/design/04_3b_record_reconciliation.md`, SHA-256
`27a91ef4c6f888eba9e2cf308b7283abe2426929b3c8524aa95f32da8ca502aa`, 1,441 lines.

`tests/test_containment_guard.py`, SHA-256
`6b06bfce6dba5ece7490c3538debebdef56c00287e8b7999280c9b0aef4bdc97`, 695 lines,
previously 678.

**Test suite: 1394 passing before this step, 1394 passing after commit one, and
1394 passing after commit two.**

**No test's result changed. No test was added, removed or renamed.**

Ledger: 52 read from `docs/design/04_3a_metric_vocabulary.md` §10.1, plus four,
**56**.

Errata index: twelve in fact on entry, plus three, **fifteen in fact against nine
in its own text**.

Manifest: 66 hashed entries on entry, **80 after**, all 80 recomputed and matched.

Open items register: **fifteen, none with an owner.**

Performance firewall: armed. Holdout: sealed and unspent.

---

## 12. THE TWO STANDING CLOSING ITEMS

**Reported every time and not only when they have content**, per
`docs/design/04_1d_standing_practices.md` §1.2.

### 12.1 WHERE A REQUIREMENT CONTRADICTED A CONSTRAINT

**ONE, STATED AT §1 AND NOT RESOLVED.** The instruction constrains commit one to
two named files, constrains commit two to code only, and requires a committed
report-back covering both. `docs/design/04_2e_housekeeping.md` §5.2 requires the
report-back in the same commit as the step it reports. The three cannot hold
together. The reading taken and its ground are recorded at §1.

**A SECOND, NARROWER ONE.** The instruction says "Verify every manifest entry and
report the result" and separately "CHANGE NOTHING ELSE" of commit two. The
manifest's own maintenance rule requires this file's entry to be appended in this
commit, which is a change beyond the guard. The entry is made, on the ground that
the maintenance rule is committed specification and predates the instruction.

### 12.2 ANYTHING READABLE AS NARROWER OR BROADER THAN INTENDED

**THE BRIEFING DEFINITION AT `04_3b` §2.3 IS BROADER THAN THE TWO FILES IT NAMES.**
It is defined by extension and by a stated principle with an explicit "including
without limitation" illustration, per
`docs/design/04_0_divergence_disposition_amendment_2.md` §7, so a future document
that creates no rule and records no measurement falls under it whether or not
anyone intended that. **That breadth is deliberate and is stated so it is not
discovered later.**

**"REGENERATED WHOLESALE" COULD BE READ AS LICENSING AN EDIT TO A BRIEFING.** It
does not: limb one governs the file's own revision by a step whose purpose is to
revise it, and it says nothing about editing a briefing in passing. **A reader who
wanted that latitude would not find it in the words, and this sentence is here so
they do not try.**

**THE PART D VERDICT IS NARROWER THAN "NOTHING IN `docs/` IS UNMANAGED".** It
covers `docs/design/` and `docs/handoff/`. **`reports/` was not adjudicated and is
not claimed to be clean**, and `04_3b` §10 records that as a limit rather than a
finding.

**THE PART E DECISION IS NARROWER THAN "EVERY MODULE THE RUN TOUCHES IS HASHED".**
Five are. The engine has more modules than five, and no claim is made about the
rest.

**INSTANCE (55) AND INSTANCE (56) ARE BOTH CLOSE CALLS AND BOTH ARE ARGUED BOTH
WAYS IN THE DOCUMENT**, with the total the contrary reading would give stated in
each case, following the precedent at `docs/design/04_1a_denomination.md` §5.
