# MANIFEST — THE FROZEN ARTIFACT INDEX

## 0. WHAT THIS IS, AND THE MAINTENANCE RULE

**A LIVING INDEX OF EVERY ARTIFACT A SUBSEQUENT STEP MIGHT NEED TO VERIFY.** One
entry per artifact: path, SHA-256, the commit that introduced it, and one line on
what it governs or measures.

> ### ANY STEP CREATING A FROZEN ARTIFACT APPENDS ITS ENTRY IN THE SAME COMMIT.

**UPDATING THIS FILE IS ONE OF THE TWO PRACTICES `docs/prompts/STANDING_RULES.md`
§12.7 RECORDS AS UNCOMMITTED.** That section states the position honestly: the
single-file rule these updates would be an exemption from is committed nowhere, so
the exemption cannot be transcribed as standing. **The practice is followed; it is
not claimed as a rule.**

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

---

## 3. IMPLEMENTATION — ANALYSIS MODULES LATER STEPS BUILD ON

**Source code is an implementation of the specification and is not a member of
it**, per amendment 2 §2.

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

- **Frozen specification entries listed: 20.**
- **Evidence reports listed: 15.**
- **Analysis modules listed: 8**, with 6 more present and omitted as unused by the
  current chain.
- **Engine dependencies listed without hashes: 4.**
- **Total hashed entries: 43.**
- **Hash mismatches against values recorded in committed documents: zero, over 29
  path-and-hash pairs.**
- **Defect ledger: 43**, stated at `docs/design/04_1c_denominator_choice.md` §5.5.
- **Errata index: 9 entries**, at `docs/design/04_1c_pre_commitments.md` §5.
- **Test suite: 1247 passing.**
- **Performance firewall: armed. Holdout: sealed and unspent.**
