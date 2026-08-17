# MANIFEST — THE FROZEN ARTIFACT INDEX

## 0. WHAT THIS IS, AND THE MAINTENANCE RULE

**A LIVING INDEX OF EVERY ARTIFACT A SUBSEQUENT STEP MIGHT NEED TO VERIFY.** One
entry per artifact: path, SHA-256, the commit that introduced it, and one line on
what it governs or measures.

> ### ANY STEP CREATING A FROZEN ARTIFACT APPENDS ITS ENTRY IN THE SAME COMMIT.

**UPDATING THIS FILE IS ONE OF THE TWO EXEMPTIONS TO THE SINGLE-FILE RULE**,
committed at `docs/design/04_1d_standing_practices.md` §1.3. That document creates
the rule rather than transcribing it, and says so; the exemptions are exemptions
from a rule established there, not from one that pre-existed. **This paragraph
previously recorded the practice as uncommitted, which was true until
`docs/design/04_1d_standing_practices.md` was committed.**

> ### THIS MANIFEST IS A CONVENIENCE INDEX. THE GIT HISTORY IS AUTHORITATIVE WHERE
> ### THEY DISAGREE.

A hash here that does not match the file is a defect in this file, not evidence
about the file. **Recompute rather than trust.**

### 0.1 HOW THESE HASHES WERE PRODUCED

**EVERY HASH BELOW WAS COMPUTED FRESH FROM THE WORKING TREE AT THIS COMMIT.** None
was copied from any document.

**THE CROSS-CHECK, AND ITS RESULT.** Every 64-character hexadecimal string
appearing in any document under `docs/` alongside a file path was extracted and
compared against that file's current hash: **29 path-and-hash pairs found, 29
matching, zero mismatches, and no named file absent.** No silent-edit event is
detected at this commit.

---

## 1. THE FROZEN SPECIFICATION

`docs/design/04_0_divergence_disposition_amendment_2.md` §2 defines membership by
extension and states that the list is **open forward**: any document subsequently
committed as a pre-registration joins on its commit. The entries below carry a
membership note where the source is explicit.

### 1.1 THE THESIS

**`docs/handoff/22_point_1_thesis.md`**
`5d716f7dfc2c7b0186082f23f1f4a8f121a44e67fd8eee7fdf8be922ef78da55` — commit
`02e47a5`. The strategy thesis. Named member.

**`docs/handoff/22a_point_1_thesis_amendment_1.md`**
`7d902da785e8cff3588ec1bb1680d9f5a44ffcf0a690e9b0fdb9c0954a518a66` — commit
`703046a`. Amendment to the thesis. Named member.

### 1.2 THE STANDING BRIEF

**`docs/design/00_standing_brief.md`**
`04656b7565c03621e6067aa32d174bd62403ff46876d08bbb04d4b75ec14e175` — commit
`b8f4844`. Verbatim transcription of the standing project premises: capital, the
risk rule, the asset set, the venue, drawdown tolerance. Named member, as amended
by `04_0_divergence_disposition.md` §3.

### 1.3 THE AGGREGATE RISK BUDGET

**`docs/design/05_aggregate_risk_budget.md`**
`d5ac7bd61323d04e75a854baf14086932470175408f5e2db4ca6f4d3afad268f` — commit
`a323237`. The concurrency and allocation rules; refusal is a skip. Named member.

**`docs/design/05a_aggregate_risk_budget_amendment_1.md`**
`50da5aed3fabb86c3c7b54b41642444e50c7a7790de8dc93ab401ab53071522c` — commit
`62c2d2b`. Rules A and B: the rotation, and nominal charging before flooring.
Named member.

**`docs/design/05b_aggregate_risk_budget_amendment_2.md`**
`1d115df2272a4e231da41afbbd0b7c82020d0092ec2b3b483062d57c0e95f7bd` — commit
`46099a2`. Further amendment to the budget. Named member.

### 1.4 THE EXIT RESOLUTION SPECIFICATION

**`docs/design/06_exit_resolution_spec.md`**
`773bbafe94ba136c9bddbdc443284af96c021eb4e0894677438e0cb7622f71a0` — commit
`6def4cb`. E1 to E9: fill conventions, the time exit, funding, missing bars, the
trigger basis. Named member.

**`docs/design/06a_exit_resolution_spec_amendment_1.md`**
`6599b154806f0f34bf5d2f687af2f2e38d7d6179a04da0af40d6dc803edf65fb` — commit
`0f79311`. E7.1 funding provisioned not reconciled; E7.2 funding on both sides of
the target solve; E8.1 the missing-bar rule's out-of-sample status. Named member.

### 1.5 THE DIVERGENCE DISPOSITION CHAIN

**`docs/design/04_0_divergence_disposition.md`**
`50ffd5024dda4a84d812ef73983d68bf6289d6d18ed7f29903918898441babe2` — commit
`1ff7263`. Five divergences disposed of; §3 amends the standing brief; §7 extends
the holdout disclosure requirement to the second channel. Named member.

**`docs/design/04_0_divergence_disposition_amendment_1.md`**
`48bccb35b2d980b276fc38d58b63f03f4367e449c63904d9da94a6a0adf88022` — commit
`814608d`. §3 defines "writeup" broadly; §5 corrects the 0.0067R pairing. Named
member.

**`docs/design/04_0_divergence_disposition_amendment_2.md`**
`1a01f14f9a72c30a714a93ab2bf2749b3a62083d0638f90b6d6b6669b2058e4c` — commit
`fd45afd`. §2 defines the frozen specification by extension; §3 extends "writeup"
to absence and refusal; §7 adopts the scope drafting rule. Named member and the
document that defines the list.

### 1.6 THE POINT 4 DECISION CHAIN

**Each of these was committed as a pre-registration and therefore joins the frozen
specification on its commit**, per §2's open-forward clause.

**`docs/design/04_0_decision_rule.md`**
`f10ca4e5a1ab740309cb33e691989913f432635a75b3ea9dc8a9a7a0a15c3a72` — commit
`77a226b`. The Branch B/C fork; §4 the order and direction rules; §8 the failure
branch and the execution-reality-over-measurement-convenience principle; §9 the
ledger at 37.

**`docs/design/04_1a_denomination.md`**
`e0d641376ffd0e3205f2fa286d7207133b91039a7e876654789d9dfb309ee61b` — commit
`b807744`. The stop-path denomination and its five grounds; §4.1 the dominance
check named as owed; §5 an erratum; §6 the standing inclusion criterion; ledger 38.

**`docs/design/04_1a_denomination_amendment_1.md`**
`70ac4556c62c4d203eec42cf1112bf9454f65f9833fead7b2d0981d593f17bab` — commit
`02992c7`. Re-denominates the numerator onto the unvalidated term; §7 adopts the
standing verification rule and takes the ledger to 41.

**`docs/design/04_1b_tolerance_and_branch.md`**
`d28602331e63bd9e8bd54d3910b7a33f70a84c89edeb9cbf9baf82ce644f923c` — commit
`56a11f6`. Branch B chosen; §3.2 defines the protected quantity; §3.5 schedules the
expiry re-argument; §4.2 records that the rationale does not discriminate between
values; §7 the drafting rule and ledger 39.

**`docs/design/04_1c_non_uniformity_check.md`**
`eb4f647b2176af3719c2ba481e31672060487f4eb9a0298b5222bf6049c7baf1` — commit
`af7866d`. §4 commits the non-uniformity threshold, alone and before the
derivation existed. **Rendered inapplicable by `04_1c_denominator_choice.md` §3.3;
not falsified.**

**`docs/design/04_1c_path_and_scope.md`**
`802cb35ce9f86ce4d8e8ccc81532393649c5ce5ea63cf64b95cf8bb5ec2751d0` — commit
`506977b`. Path two committed as the risk unit; funding committed into the
unvalidated set; ledger 42.

**`docs/design/04_1c_denominator_choice.md`**
`d601e04ab27c546149d97329ed097be383f69c89e1cd6c0a9cca8d9da1523aa4` — commit
`a9083b0`. The constraint denominated in the risk unit itself; §3 the apparatus
inapplicable rather than satisfied; §5.5 the ledger at 43, the current total.

**`docs/design/04_1c_pre_commitments.md`**
`23b511a288b338930510670a64c4ff8f2362ee87c5d4201962c248335f8d6673` — commit
`5ec36c0`. §2 the admitted domain and the exclusion above it; §3 reject-over-clip
and the two rejection populations; §4.3 the five disqualifying properties; **§5 the
consolidated errata index, at nine entries.**

**`docs/design/04_1c_level_method.md`**
`4d7e4c80d495c51f4cc68335559a8b4984a558e429fc5f973f942442251a9069` — commit
`1a0aa24`. One level-setting method attempted and disqualified on property (b); the
dominance obligation discharged as moot.

**`docs/design/04_1c_proper.md`**
`548489044aa0cad5d3ec28d8dbc5ce534865376df63374f6326a9af36ec42dbc` — commit
`db3a6de`. The judgement route's specification: the displacement budget, the
uncertainty parameter and its scope, the stress comparator's reconciliation rule,
and §7.3 the Point 6 queue at four.

**`docs/design/04_1c_consequences_and_thresholds.md`**
`07e6a74a34387a1c0f45f070b1046bc2d090361206ef6e380d6bbed17f44cb85` — **introduced by the same commit as this
manifest revision**; `git log --diff-filter=A` over the path is authoritative.
4.1c's close: §2 narrows reject-over-clip to population A and commits clipping for
population B; §3 disposes of kill condition (d) as to stratum and level; §4 commits
the magnitude threshold, ordered modality-then-magnitude; §5 the ledger at 46 and
the errata index's true standing; §6 4.1c's closing position.

**`docs/design/04_1e_stop_cap.md`**
`6acab4f554f6fc638a15302d4e3223e264b1a580437181c812e28fbb134d3812` — **introduced by the same commit as this
manifest revision**. Records the frozen `stop_max_pct` of 0.035 as **WRONG** on
four computable grounds and STOPS: no replacement is chosen. §3 states the
uncomputable side, §4 commits a Point 6 falsifier, §5 records the thesis gap on
the clipped fraction, §6 the ledger at 47.

**`docs/design/04_1d_standing_practices.md`**
`e4959d4cfc25489c2d016efbfe7c95e04ada360df8546f8bf907314c034e9f3b` — commit
**introduced by the same commit as this manifest revision** — its hash cannot
appear here, because a file recording its own commit's hash changes that hash. Every
other entry was added in a later commit than the artifact it names, so the case had
not arisen before; `git log --diff-filter=A` over the path is authoritative. §1
commits four standing practices as rules, one of which — the
single-file rule and its two exemptions at §1.3 — this document creates rather
than transcribes; §2 records three as conventions; §4 logs **erratum entry 10**;
§5 logs **ledger instance (44)**, taking the total to 44.

**`docs/design/04_1f_cap_requirement.md`**
`fe895646df98a9071446a5d86df5687c3251206ab2f976da9718e7ad3c3a6eb6` — **introduced by the same commit as this
manifest revision**. What a stop cap must do, committed BEFORE any candidate is
evaluated: two failed purposes dropped, removal kept live, four limbs each with
its failure test, constants not excluded, and comparability barred as a ground.

**`docs/design/04_1g_cap_adoption.md`**
`337c6049431f06f653f981117914e84a862966b2f6e4e38a49a94e158003d0d0` — **introduced by the same commit as this
manifest revision**. Adopts candidate B: **there is no stop cap.** The clipped
fraction is zero and 04_1e's thesis gap is closed; the admitted domain's lower
bound moves to 0.00359143 with the level still inside; no fold-dependence arises;
two code changes named as owed; ledger 48.

**`docs/design/04_2a_artifact_containment.md`**
`ddd8938612f0086dc63d35fffbf1536114ef60e4a383cf64f084a1274638d3f6` — **introduced by the same commit as this
manifest revision**. Declares `src/sweep/` dead relative to the frozen thesis on
one ground -- both the import and file-read channels closed -- and commits
containment for the outcome-bearing artifacts, a four-condition fixture carve-out,
the human-channel testimony, and ledger instance (49). Commits no aggregation
rule.

**`docs/design/04_2b_point_4_decomposition.md`**
`90cd89063a6f96c8bbeb88c46cc71606e0d4ebe187290789de1192ef7ebfa840` — **introduced by the same commit as this
manifest revision**. Point 4's sub-point structure: 4.0 and 4.1 TRANSCRIBED with
their label drift recorded, 4.2 to 4.7 PRE-REGISTERED with deliverables, the §9
mapping verified and §9(g) corrected from sub-point to completeness obligation,
the freeze defined with six preconditions, and the open-items register placing all
nine closing-record items -- four of which had never been cited. Ledger 50.

---

## 2. EVIDENCE — REPORTS UNDER `docs/handoff/`

**NOT MEMBERS OF THE FROZEN SPECIFICATION.**
`docs/design/04_0_divergence_disposition_amendment_2.md` §2: reports that record
measurements rather than pre-register rules are **evidence, not specification** —
cited, relied on, and corrected by erratum; they do not bind.

**`docs/handoff/23_point_1_reopened_closing.md`**
`d567177146828315dfabdbc1bb5d2c3ad5eed63b5ad966ea049feaca0d639818` — commit
`5e4d970`. §5.1 the read-back protocol.

**`docs/handoff/24_point_5_1_exposure.md`**
`e647e345ceaaec3a6c4fed16e8b4488a38ac9e48fa5a4d734f70231e4feeb045` — commit
`4e08e1b`. Exposure profile over the candidate population.

**`docs/handoff/25_point_5_2_venue_constraints.md`**
`6b8f525caac69317a4ce9e33e45e37f8314f058d7d0e01944b42729aec0adf66` — commit
`e735295`. §2 cross-checks the contract cache against the live venue.

**`docs/handoff/26_point_5_2_budget_cost.md`**
`2b408bea1fbca457669ec3665aa6e7506ff74e23e21c859c8f5b3a286cbfb7f1` — commit
`ef1f4f6`. The frozen budget skips 47.11% of signals at max hold.

**`docs/handoff/27_point_5_3_0_intrabar_span.md`**
`5806fac830480ccac3c93426598bfa2cdc51979e33255545fa5304fb45674aa9` — commit
`60b66f5`. 1m required; §8 establishes that `open` is synthesised.

**`docs/handoff/28_point_5_3_1_sizing.md`**
`be06acb5de72b7e6e2a253737317881e442715c4e7138290cf8ead71bc6d99ef` — commit
`df14a68`. Exchange-real sizing; §9 the floor-bound tolerance breaches.

**`docs/handoff/29_point_5_3_3_1m_seal.md`**
`55e9546aee9b4a59035a4a769c2b1a9b7a41ad08fdb5dbcf7a48803df66e6e75` — commit
`7f46b1a`. The sealed 1m loader; §9 discloses the 5.3.3 breach.

**`docs/handoff/30_point_5_3_4_portfolio.md`**
`654b66e053c5dbcc672dbed0940efe555ce035b552640483a13e5c416eb34fa5` — commit
`1e66c17`. The portfolio execution path; §7.3 the fill-price term.

**`docs/handoff/31_point_5_closing.md`**
`8e6c74426f95336e624fc836f9fe3f262cb783b3eadbf2c3b6865a91b3a82050` — commit
`78ba335`. **The Point 5 closing record.** §5.2 the haircut's unvalidatable status;
§5.3 the fill-price term and the missing magnitude threshold; §7 the ledger method;
§8 errata 1 to 5; §11 the firewall status; §13 the standing working rules.

**`docs/handoff/32_point_4_0_3_floor_curve.md`**
`b95ed49db87f27945df2fae01986a6f8f3882c8dfd112290494aadb5584aadc5` — commit
`5c55776`. The parametric floor under the original denomination. **Superseded as
governing, not falsified.**

**`docs/handoff/33_point_4_1a_revised_derivation.md`**
`45bad5b710096ba0abe5336c3e0d710a3da391a8f9b80e717f4a646397d10538` — commit
`22e323a`. The revised closed form over the stop distance; its preamble states the
design-versus-handoff filing ground. **Superseded as governing, not falsified.**

**`docs/handoff/34_point_4_1a_non_uniformity_rerun.md`**
`a2af6e199450ef4c12aa156cdd10006d55b4d511e2e365d36f8061acd853e0ab` — commit
`3007dbd`. The non-uniformity re-run; §4.2 the empty-stratum-as-artefact
precedent. **Superseded as governing, not falsified.**

**`docs/handoff/35_point_4_1c_denominator_audit.md`**
`aacdd676fa11ddb98501adebf624fe935b1f2a34f5a96cc6036d81edfeedbd5c` — commit
`2983cac`. §2.2 establishes the two cost paths. **Unaffected by later decisions.**

**`docs/handoff/36_point_4_1c_risk_unit_derivation.md`**
`959858189ba78d783e28a21e8d961d52b141be1f79f666efe600ff7937b0fe67` — commit
`e4122b6`. **The governing closed form.** §2 the achievable range and the
per-symbol ceilings; §2.5 the committed grid; §3.5 the short-only pole; §5.1 the
set probe.

**`docs/handoff/37_point_4_1c_level_and_consequences.md`**
`b236ce325fb6af3bc2d820e6505e0479a55035469fcb5eaef8e635c026e7ebbe` — **introduced by the same commit as this
manifest revision**; `git log --diff-filter=A` over the path is authoritative.
Sub-point 4.1c step 2: the level and its epistemic status, the floor widths, the
stress comparator with the worst cell named, the stratum over the 11,384
candidates, and the FIRST COUNT of the ATR-above-cap rejection population.

**`docs/handoff/38_point_4_stop_cap_audit.md`**
`529b3a28c88bf2197fa3e20511abe1257e572a6dac92f7876e603e8d21bf4df9` — **introduced by the same commit as this
manifest revision**. The frozen stop cap audited: every read site, the granularity
constraint, the reachability purpose tested and found to run backwards, the
committed `grid.derived_cap` rule evaluated against 0.035, and the clipped count
across a committed range.

**`docs/handoff/39_point_4_cap_candidates.md`**
`fc3878bc3d26486a4230bce5b3f9e9c297a1d61a65963504305dee68fb6ca0d3` — **introduced by the same commit as this
manifest revision**. Three candidate cap rules measured against
`04_1f_cap_requirement.md`'s four limbs, with per-limb verdicts and no
selection: `grid.derived_cap` per fold, no cap at all, and the same rule over the
whole in-sample window.

**`docs/handoff/40_point_4_2_fold_audit.md`**
`9d0866d6624b8ff666289b284c580e82a2335999e74dda514e494e27a256b4ac` — **introduced by the same commit as this
manifest revision**. The fold schedule audited for 4.2: nine folds with disjoint
contiguous test windows, adjacent train windows overlapping ~50 per cent, fifteen
test-into-train cross-overlaps, and a reachability trace establishing that the
frozen thesis fits nothing on train while the 4.3/4.4 selection procedure fits the
ATR multiple on train and evaluates it on test.

**`docs/handoff/41_point_4_2_artifact_audit.md`**
`e13a9122941edc4e9c5597b550b563802220b5a5292fe1ceb5660809e764a768` — **introduced by the same commit as this
manifest revision**. Adjudicates the committed sweep artifacts against criteria
transcribed before any finding: **NO BREACH.** They carry outcome quantities,
belong to a superseded thesis, all predate the 2026-08-11 freeze, and no chain
reaches any Point 4 or Point 5 commitment. No file under `data/` was opened.

---

## 3. IMPLEMENTATION — MODULES LATER STEPS BUILD ON

**Source code is an implementation of the specification and is not a member of
it**, per amendment 2 §2.

**`src/analysis/cap_candidates.py`**
`55458809d3dab0cf192f20727b27970dbd1df56e959494a5e69e7196e1819bc0` — **introduced by the same commit as this
manifest revision**. Report 39's module; imports `grid.derived_cap` and report
36's domain machinery rather than reimplementing either.

**`src/analysis/stop_cap_audit.py`**
`57160bbeac676dff639a23a45cac8a34bf6f843f45dd721affb6f46d910fb545` — **introduced by the same commit as this
manifest revision**; range committed alone first at `0a1ae11`. Report 38's module.

**`src/analysis/level_consequences.py`**
`f558673aadddf1df27816c050d4445332302108571d384a4e01cf0764bfc789a` — **introduced by the same commit as this
manifest revision**. Report 37's derivation module: the level from the committed
budget and uncertainty parameter, the comparator, and the stratification. Imports
`risk_unit_floor_curve` rather than reimplementing the closed form.

**`src/firewall.py`**
`529f7eaec40c1624d9af0b7eadee995719a341aa77630af6c5aa48df20b52809` — commit
`47a26de`. **THE BANNED-NAME LIST, DEFINED ONCE.** Previously written out in
eighteen test modules, four of which had drifted three names behind.
`tests/test_firewall_names.py` asserts over the AST that no module defines its own
copy. It sits at the top of `src/` because the firewall crosses every subpackage
and is not a measurement.

**`src/analysis/risk_unit_floor_curve.py`**
`4a7b035e46860d24b9755439c209f148c939ff4e3443c29a47657f0a52640e18` — commit
`de05a18` introduced it with the grid and Part A only; commit `e4122b6` added the
solver. **The governing derivation module.**

**`src/analysis/haircut_floor_curve.py`**
`4b5aabaee811ba54397f1466fb8da6b47d8a1a9f3738ba494a909be754a7d7c2` — commit
`532e933`. Report 33's closed form. Superseded as governing.

**`src/analysis/haircut_share.py`**
`5ed9536d37424a0b0b9aace812d9730da7be3ba00a18d329c43f418ad6dd2125` — commit
`7a08069`. The non-uniformity threshold's implementation. Inapplicable under the
current denominator.

**`src/analysis/haircut_share_rerun.py`**
`1a6971627252293a4e538308c2963b0fc15e6ce065e54ee4416c42ab33f790e5` — commit
`3007dbd`. Report 34's re-run. Superseded as governing.

**`src/analysis/floor_curve.py`**
`237f84ffd4df3b7f0c1567cce1be25281927346908681fe5dbd11b4b2ff50f83` — commit
`12e32a6`. Report 32's curve. Superseded as governing.

**`src/analysis/exposure_profile.py`**
`71717a557eb8286ca5a41ceb3277d240ead43e71c2ad877149ff8d24e0398a43` — commit
`4e08e1b`. Supplies `cost_config()`, which every derivation above calls.

**`src/analysis/sizing_drag.py`**
`f1dbe96c4ebb5628d29cb5f8b73b44098c433c754415a7f6951f89ceb3ec61d3` — commit
`df14a68`. Report 28's drag measurement; line 177 forms the cost-over-stop ratio.

**`src/analysis/structural_pass.py`**
`0c31a7ca3c77c82f90266d1144f72e46f458c1ea061b2b710f54d6294b3b06a9` — commit
`4e08e1b` or earlier. Carries the tokenising method
`docs/design/04_1a_denomination_amendment_1.md` §7 adopts as standing.

**OTHER MODULES UNDER `src/analysis/` NOT LISTED ABOVE** —
`budget_cost.py`, `dispersion.py`, `intrabar_span.py`, `rsi_breakout_profile.py`,
`sweep_population.py`, `__init__.py` — **are committed and hashed in the working
tree but no current step builds on them.** They are omitted rather than
forgotten.

---

## 4. THE ENGINE FILES THE DERIVATIONS CALL

**LISTED WITHOUT HASHES, BECAUSE THEY ARE READ-ONLY DEPENDENCIES RATHER THAN
ARTIFACTS THIS CHAIN PRODUCES**, and because every recent step asserts they are
unmodified via `git status` rather than by hash.

- **`src/engine/costs.py`** — the cost algebra. Line 336 assembles path one's
  denominator; line 171 the haircut; line 71 the entry slippage, frozen at zero.
- **`src/engine/sizing.py`** — exchange-real sizing. Line 252
  `per_unit_denominator` recovers path one's denominator from the engine.
- **`src/engine/portfolio.py`** — the execution path. Lines 298 to 299 assemble
  path two's denominator; line 187 `funding_per_unit`.
- **`src/risk/exit_spec.py`** — the E-series constants. Line 101 the settlement
  count; line 115 the funding rate.

---

## 5. STATUS AT THIS COMMIT

- **Frozen specification entries listed: 27.**
- **Evidence reports listed: 20.**
- **Implementation modules listed: 12** — `src/firewall.py` plus eleven under
  `src/analysis/`, with 3 more analysis modules present and omitted as unused by
  the current chain.
- **Engine dependencies listed without hashes: 4.**
- **Total hashed entries: 59.**
- **Hash mismatches against values recorded in committed documents: zero.**
- **Defect ledger: 50**, stated at
  `docs/design/04_2b_point_4_decomposition.md` §7.3.
- **Errata index: 10 entries** — nine at `docs/design/04_1c_pre_commitments.md` §5
  and **entry 10 at `docs/design/04_1d_standing_practices.md` §4.1**. The index
  says nine in its own text and is frozen; `04_1c_consequences_and_thresholds.md`
  §5.5 restates the true standing and §6.3 item 8 routes it to become a standalone
  artifact.
- **Test suite: 1341 passing.**
- **Performance firewall: armed. Holdout: sealed and unspent.**
