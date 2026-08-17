# REPORT 41 — THE COMMITTED ARTIFACTS, ADJUDICATED

**Point 4.** An AUDIT. **No outcome value was read, printed, summarised or
aggregated.**

---

## 1. THE ADJUDICATION CRITERIA

**COMMITTED IN THE INSTRUCTION THAT PRODUCED THIS REPORT, BEFORE ANY FACT WAS
ESTABLISHED, AND TRANSCRIBED HERE VERBATIM BEFORE ANY FINDING IS STATED.**

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

### 1.1 THE PERMITTED BANNED-TOKEN OCCURRENCES

**THIS REPORT CONTAINS SOME OF THE BANNED NAMES, AND THAT IS UNAVOIDABLE IN A
REPORT WHOSE TASK IS TO SAY WHICH FIELDS AN ARTIFACT HAS.** The instruction that
produced it states the distinction: **field names are not outcome quantities; the
numbers under them are.** They occur in exactly these places, all of them required:

- **§2.1**, naming the field `bands.py` reads out of `sweep.json`;
- **§2.2**, listing the terms `dispersion.py`'s own guard bans;
- **§2.5** and **§6.1**, listing the golden files' columns;
- **§4.3**, naming the two columns the pinned-trade regression asserts over;
- **§5**, describing what the artifacts hold.

> **A CHECK FINDING THOSE TOKENS HERE HAS FOUND A SCHEMA, NOT A VIOLATION. NO
> VALUE FROM ANY OF THOSE FIELDS APPEARS ANYWHERE IN THIS REPORT.**

### 1.2 A REQUIREMENT AND A CONSTRAINT CONFLICT, STATED AND NOT RESOLVED

**PART 1 REQUIRES REPORTING EACH ARTIFACT'S SCHEMA. THE CONSTRAINTS FORBID
READING ANYTHING UNDER `data/`. THE ARTIFACTS LIVE UNDER `data/`.**

Those two cannot both be satisfied by opening the files, and the standing rule is
to report such a conflict rather than resolve it in either direction.

> ### WHAT WAS DONE INSTEAD: NOT ONE ARTIFACT UNDER `data/` WAS OPENED. EVERY
> ### SCHEMA BELOW IS ESTABLISHED FROM THE CODE THAT WRITES OR READS IT.

That is a genuine substitute rather than an evasion — the writing code is the
authority on what fields exist — and where it leaves a gap, §2 says so. **The two
files outside `data/` were treated differently and §2.5 records how.**

---

## 2. PART 1 — WHAT EXISTS

**ENUMERATED FROM THE GIT INDEX, NOT BY LISTING `data/`.** Sizes are blob sizes
at `HEAD`.

### 2.1 THE SWEEP ARTIFACTS

**`data/derived/sweep/grid.json`** — 124,622 bytes. Introduced `7f93257`
(2026-08-07), last modified `0aa27ef` (2026-08-07).
**Schema, from `grid.grid_payload`:** `a3`, `design`, `firewall`, `git_commit`,
`grid`, `m_star`, `population`, `rvol_thresholds`, `script`, `stop_max_pct`,
`symbols`.
> **NO FIELD NAME MATCHES ANY OF THE TWELVE CANONICAL NAMES OR AN OBVIOUS
> VARIANT.** Every field is a derivation input or a provenance record: the
> multiplier grid, `m*`, the derived cap, the RVOL thresholds, the A3 prescreen
> and population counts. **Schema does not indicate outcome quantities.**

**`data/derived/sweep/sweep.json`** — 236,539 bytes. Introduced and last modified
`bdde2a4` (2026-08-09), message *"Sweep run (step 2): 7,128 labelled cells."*
**Schema, from `sweep.record`:** each record carries `arm`, `direction`,
`fold_id`, `metrics`, `multiplier`, `offset`, `period`, `population`, `symbol`.
> **`metrics` IS A NESTED FIELD AND IT CARRIES OUTCOME QUANTITIES.** Established
> without opening the file: `bands._acceptance_metrics` reads
> `m["n"], m["expectancy_r"], m["se_r"]`. **`expectancy_r` matches a canonical
> banned name.** Schema indicates outcome quantities.

**`data/derived/sweep/bands.json`** — 304,205 bytes. Introduced and last modified
`68e5b16` (2026-08-09), message *"Point 4 step 3: band selection and
kill-condition verdict."*
**Built by `bands.py` from `sweep.json`'s acceptance metrics**, which §2.1 above
establishes are outcome quantities. **Schema indicates outcome quantities.**

**`data/derived/sweep/sweep_cells.jsonl` IS NOT TRACKED.** It exists in the
working tree and is absent from the git index. Recorded because §4.2 finds a test
that reads it.

### 2.2 THE DISPERSION ARTIFACT

**`data/derived/analysis/e6_dispersion.json`** — 105,476 bytes. Introduced and
last modified `f9eaa48` (2026-08-08), message *"E6 run:
reports/12_e6_dispersion.md. THE FIREWALL IS LIFTED, PARTIALLY."*

**Its writer, `src/analysis/dispersion.py`, carries two guards** that establish
the schema without opening the file: `FORBIDDEN_TERMS`, which bans `expectancy`,
`win rate`, `profit factor`, `sharpe`, `sortino`, `mean r`, `median r` and
others; and `PERMITTED_STAT_KEYS`, an allowlist whose statistical members are
`n`, `sigma`, `min`, `max`, `iqr`, `p10_p90_spread` and `se`.

> ### THE SCHEMA INDICATES DISPERSION STATISTICS AND EXPLICITLY EXCLUDES LOCATION
> ### STATISTICS. Whether the guards held in the run that produced this file
> ### cannot be confirmed without opening it, **and it was not opened.**

**The commit message is nonetheless the plainest statement in the repository that
a firewall was deliberately relaxed**, and §3 places it in time.

### 2.3 THE STRUCTURAL AND CONFIGURATION ARTIFACTS

**`data/derived/folds/folds.json`** — 4,606 bytes, `af9d314` to `6d482fb`
(2026-08-07). The serialised schedule, from `schedule.schedule_payload`: fold
identifiers and dates. **No outcome quantities.**

**`data/derived/regime/terciles.json`** — 1,573 bytes, `6f5ca72` (2026-08-07),
and **`_manifest.json`** — 1,687 bytes, `20a6226` (2026-08-07). The regime axis,
built by `regime/measure.py` from ATR per cent, an efficiency ratio, drift and
median quote volume. **No outcome quantities.**

**`reports/07_structural_pass_raw.json`** — 184,731 bytes, `de4b8d0`
(2026-08-05). Produced by the structural pass.
> **ITS SCHEMA WAS NOT ESTABLISHED.** It sits under `reports/`, not `data/`, so
> the constraint did not block it — but `docs/handoff/31_point_5_closing.md` §11
> names artifacts under `reports/` as a place an outcome figure would falsify the
> claim, and opening it to check is exactly the risk the audit exists to avoid.
> **Reported as unestablished rather than opened.** §6 records that this does not
> move the verdict, and why.

### 2.4 `config/contracts_cache.json`

Venue lot steps, price ticks and order minimums, cross-checked against the live
venue at report 25. **Inputs. No outcome quantities.** Listed because §4.1 finds
it is the one file the engine reads besides bars.

### 2.5 THE GOLDEN FILES — AND THESE ARE NOT UNDER `data/`

**`tests/golden/btc_2023_01_gated.csv`** — 20,256 bytes, introduced `d04ba47`
(2026-07-27), last modified `c0cf37e` (2026-08-05).
**`tests/golden/btc_2023_01_signal_ungated.csv`** — 44,023 bytes, introduced
`c0cf37e` (2026-08-05), last modified `b6182b6` (2026-08-05).

**THE CONSTRAINT DID NOT BLOCK THESE AND ONLY THE HEADER ROW WAS READ.** Column
names are schema; the rows beneath were not read. Both carry the same 34 columns,
among them:

> ### `gross_pnl`, `net_pnl`, `r_multiple`, `mfe`, `mae`, `exit_reason`.

**FOUR CANONICAL BANNED NAMES AND TWO OUTCOME-ADJACENT ONES. SCHEMA INDICATES
OUTCOME QUANTITIES, AND THESE ARE THE ONLY SUCH ARTIFACTS THAT ARE READ BY THE
CURRENT TEST SUITE.** §4.3 traces what reads them.

---

## 3. PART 2 — PROVENANCE

### 3.1 THE TWO DATES THAT GOVERN

- **THE THESIS FREEZE: 2026-08-11.** `02e47a5`, *"Pre-register the Point 1
  (reopened) thesis"*, and `703046a`, its amendment 1.
- **POINT 4 OPENED: 2026-08-14.** `77a226b`, *"The 4.0 decision rule."*

### 3.2 EVERY ARTIFACT PREDATES BOTH

- grid.json: **2026-08-07** — four days before the freeze, seven before Point 4.
- e6_dispersion.json: **2026-08-08**.
- sweep.json and bands.json: **2026-08-09** — two days before the freeze.
- folds.json, terciles.json, regime manifest: **2026-08-07**.
- structural_pass_raw.json: **2026-08-05**.
- The golden files: **2026-07-27**, last touched **2026-08-05**.

> ### NO ARTIFACT BEARING OUTCOME QUANTITIES WAS PRODUCED OR MODIFIED AFTER THE
> ### THESIS FREEZE. THE LATEST IS TWO DAYS BEFORE IT AND FIVE DAYS BEFORE POINT
> ### 4 OPENED.

**THE ONLY TRACKED FILES UNDER `data/` OR `reports/` TOUCHED AT OR AFTER THE
FREEZE** are `data/reference/bitget_venue/*` — retrieved venue documentation and
its manifest, gathered for document 06's trigger-basis question. **Venue inputs,
not outcomes.**

### 3.3 WHAT THE COMMIT MESSAGES SAY

`68e5b16` is labelled *"Point 4 step 3"* and `bdde2a4` *"Sweep run (step 2)"*.
**Those refer to a PRIOR Point 4** — the one whose pre-registration is
`docs/handoff/08_point_4_pre_registration.md` and whose closing is
`docs/handoff/16_point_4_closing.md`. **Point 1 was subsequently reopened**
(`docs/handoff/23_point_1_reopened_closing.md`), a new thesis was frozen on
2026-08-11, and the current Point 4 opened on 2026-08-14.

> ### THE ARTIFACTS BELONG TO A SUPERSEDED THESIS AND A SUPERSEDED POINT 4. THAT
> ### IS THE DISTINCTION §1's CRITERIA MAKE GOVERNING.

`f9eaa48`'s *"THE FIREWALL IS LIFTED, PARTIALLY"* was **an announcement, not a
leak** — made three days before the current thesis existed, for a run under the
prior one.

### 3.4 THE PARAMETERISATION, AND HOW IT DIFFERS FROM THE FROZEN THESIS

**ESTABLISHED FROM THE PRODUCING CODE AND FROM REPORT 39's INDEPENDENT
RECOMPUTATION ON BARS, NOT FROM THE ARTIFACTS.**

`grid.json` carries, per symbol and per training fold: `m_star` = the derived
cost floor over the median breakout ATR per cent; `grid` = eleven multipliers
from `m*` to `m* + 2.5` in steps of 0.25; `stop_max_pct` = `(m* + 2.5) x
P95(ATR%)`; and `rvol_thresholds` at pass rates 0.30, 0.50 and 0.70.

**THREE DIFFERENCES FROM THE FROZEN THESIS, EACH MATERIAL:**

1. **THE ATR MULTIPLE.** The thesis freezes **2.25**. The grid searches `m*` to
   `m* + 2.5`, and report 39 §3.1 recomputed `m*` across the folds at **1.6143 to
   4.8354**. **The swept range is not centred on the frozen value and on some
   folds does not contain it.**
2. **THE STOP CAP.** The grid supplies a per-fold cap of **3.5043 to 7.4709 per
   cent**. `docs/design/04_1g_cap_adoption.md` adopted **no cap at all**.
3. **THE STOP FLOOR.** The sweep runs through `simulate.run_backtest`, whose
   floor is the derived **1.020 / 1.320 per cent**; the thesis freezes **1.50 per
   cent**, which is what `sizing.stop_distance` and the governing path implement.

> ### THE ARTIFACTS DESCRIBE A SYSTEM PARAMETERISED DIFFERENTLY FROM THE ONE THE
> ### FROZEN THESIS SPECIFIES, IN THE MULTIPLE, THE CAP AND THE FLOOR.

---

## 4. PART 3 — CONSUMERS

### 4.1 FORWARD: EVERY READER, TRACED OVER AST NODES AND PATH CONSTANTS

- **`grid.json`** — read by `src/sweep/grid.py` (`load_grid`),
  `src/sweep/sweep_report.py`, `src/analysis/dispersion.py`, and
  `tests/test_sweep_prescreen.py`.
- **`sweep.json` and `sweep_cells.jsonl`** — read by `src/sweep/bands.py`,
  `src/sweep/sweep_report.py`, and `tests/test_sweep_run.py`.
- **`bands.json`** — written by `src/sweep/bands.py`; **no reader found.**
- **`e6_dispersion.json`** — read by `tests/test_dispersion.py`.
- **`terciles.json`** — read by `src/regime/labels.py` and
  `tests/test_regime_measure.py`.

> ### `src/engine/` READS NONE OF THEM.

**CHECKED ON THE FILE-READ CHANNEL DIRECTLY**, not only on imports, because an
artifact opened by path would not appear as an import. Every `open`, `load`,
`read_csv`, `read_json`, `read_parquet`, `read_table` and `glob` call in all eight
engine modules was enumerated: **`contracts.py` opens
`config/contracts_cache.json`; `simulate.py` reads parquet bars and globs bar
files. There is nothing else.** Pinned by test over every engine module's string
constants and call names.

### 4.2 BACKWARD: FROM EVERY POINT 4 AND POINT 5 COMMITMENT

**NO DESIGN DOCUMENT AND NO REPORT COMMITTED IN POINTS 4 OR 5 CITES A FIGURE FROM
ANY OF THESE ARTIFACTS.** A search across `docs/design/` and the Point 4 and 5
reports for `grid.json`, `sweep.json`, `bands.json`, `e6_dispersion`,
`reports/12` and `reports/14` returns **matches in exactly one document —
`docs/handoff/40_point_4_2_fold_audit.md`** — which names them as an open question
and states that it did not open them.

**TWO POINT 4 MODULES IMPORT `src.sweep.grid`:** `stop_cap_audit.py` and
`cap_candidates.py`. **Neither loads the committed artifact.** Both call
`breakout_frame`, `m_star` and `derived_cap` **on bars**, recomputing the rule
from data; neither calls `load_grid`, `load_cells` or `build_grid`, and neither
names a JSON path. **Pinned by test, in both directions** — the absence of the
loaders, and the presence of the recomputation, so the check cannot pass on a
module that simply never touched the sweep.

**THE POINT 4 CHAIN'S OWN INPUTS ARE BARS, RATES AND STATED CONSTANTS.** Report 40
§4 established the same conclusion from imports; this report establishes it from
file reads, which is the channel that report named as unchecked.

### 4.3 THE ONE LIVE SURFACE, AND IT IS NOT A CHAIN

**THE GOLDEN FILES AND THE PINNED-TRADE REGRESSION RUN ON EVERY SUITE
INVOCATION.**

- **`tests/test_determinism_golden.py`** compares an output **hash**, the column
  list and the row count. Its own docstring: it *"asserts anything about
  performance -- only that the SAME inputs keep producing"* the same output.
  **No value is inspected.**
- **`tests/test_regression_pinned_trade.py`** runs the engine on real in-sample
  data for **one hand-selected trade** and asserts `r_multiple` and `net_pnl`
  against values its docstring states are *"re-derived by hand from the formula,
  not copied from a run."* **It is an arithmetic identity check on a single
  position** — that a stop-out returns -1.0R by construction — and not a
  measurement over a population.
- **`tests/test_dispersion.py`** and **`tests/test_sweep_run.py`** read
  `e6_dispersion.json` and the untracked cells file, and **fail rather than skip**
  when absent. What they assert is record labelling, coverage and structure.

> ### THESE ARE AN UNMANAGED SURFACE. NONE OF THEM IS A CHAIN TO A COMMITMENT: NO
> ### POINT 4 OR POINT 5 DECISION CITES ANY OF THEM, AND NONE FEEDS A PARAMETER.

**IT IS NONETHELESS THE PLACE WHERE OUTCOME-NAMED VALUES ARE READ IN THIS
REPOSITORY TODAY**, and §7 recommends accordingly.

---

## 5. PART 4 — THE HUMAN CHANNEL, STATED HONESTLY

> ### CODE TRACING CANNOT ESTABLISH WHETHER A PERSON OPENED AN ARTIFACT AND LET
> ### WHAT THEY SAW INFORM A JUDGEMENT. NOTHING IN §4 REACHES THAT, AND THIS
> ### AUDIT IS NOT EXHAUSTIVE OF IT.

**WHAT CAN BE ESTABLISHED, AND IS:**

- **No committed document cites a figure from any artifact** — §4.2.
- **No decision's stated grounds reference one.** Every Point 4 and Point 5
  decision's grounds were checked against their own §-level statements: the
  denomination chain rests on the cost algebra and rate comparisons; the level on
  the displacement budget and the uncertainty parameter; the cap chain on lot
  geometry, notional arithmetic and `grid.derived_cap` **recomputed from bars**;
  the aggregation groundwork on schedule geometry. **None names a swept figure.**
- **WHETHER THE VALUES WOULD HAVE BEEN USEFUL, ANSWERABLE FROM SCHEMA AND
  PARAMETERISATION ALONE:** the artifacts hold per-fold, per-multiplier
  expectancy for a system whose multiple, cap and floor all differ from the frozen
  thesis (§3.4). **They would be useful to a choice of ATR multiplier.** No Point
  4 or Point 5 decision chose one — the decisions were about cost denomination,
  the risk unit, a tolerance level, a stop cap and an evaluation stratum.
  **The one place they would have bitten is the cap**, and
  `docs/design/04_1g_cap_adoption.md` retired the cap entirely on grounds that
  count against any cap.

> ### THE RESIDUAL THIS AUDIT CANNOT CLOSE: whether a person read
> ### `sweep.json`, `bands.json` or `reports/12` and `reports/14` at some point
> ### and carried an impression forward into a judgement that no document
> ### records. **Nothing in the repository can settle that**, and it is named here
> ### rather than left as an unstated assumption behind §6's verdict.

---

## 6. PART 5 — THE VERDICT

### 6.1 LIMB BY LIMB

**LIMB 1 — "the artifacts contain outcome quantities": SATISFIED.**
`sweep.json` carries `expectancy_r` and `se_r` under `metrics`; `bands.json` is
built from them; the golden files carry `gross_pnl`, `net_pnl`, `r_multiple`,
`mfe` and `mae`. Established from schema, without opening any file under `data/`.

**LIMB 2 — "no document, decision or parameter committed in Points 4 or 5
consumed them": SATISFIED.** §4.2. The only document mentioning them is report 40,
which named the question and did not open them.

**LIMB 3 — "no chain exists from an artifact to such a decision": SATISFIED.**
§4.1 and §4.2, in both directions. `src/engine/` reads none of them on the
file-read channel; the two Point 4 modules importing the sweep recompute from
bars; no reader of any artifact is reachable from a Point 4 or Point 5
commitment.

**AND THE PROVENANCE LIMB OF "INDETERMINATE" IS NOT ENGAGED.** §3 establishes
every artifact's provenance from git: **all predate the thesis freeze, and the
outcome-bearing ones by two to fifteen days.**

**ONE SCHEMA WAS NOT ESTABLISHED** — `reports/07_structural_pass_raw.json`, §2.3.
**It does not move the verdict**, because limbs 2 and 3 are established by tracing
consumers rather than contents: whatever that file holds, **nothing committed in
Points 4 or 5 reads it.**

### 6.2 THE VERDICT

> ### NO BREACH.
>
> ### THE ARTIFACTS CONTAIN OUTCOME QUANTITIES. THEY BELONG TO A SUPERSEDED
> ### THESIS AND A SUPERSEDED POINT 4, EVERY ONE PREDATES THE CURRENT THESIS
> ### FREEZE, AND NO CHAIN RUNS FROM ANY OF THEM TO ANYTHING COMMITTED IN POINTS
> ### 4 OR 5.

**THE FINDING IS AN UNMANAGED SURFACE, NOT A CONTAMINATION EVENT**, in the
criteria's own words. **The remedy is disclosure and containment.**

**THE FIREWALL CLAIM AT `docs/handoff/31_point_5_closing.md` §11 SURVIVES AS
STATED.** That section claims no outcome figure exists *"for this thesis"*, and
names committed data files as a place one would falsify it. **The committed data
files hold figures for a different thesis**, and §11's own wording is what
distinguishes them.

---

## 7. CONTAINMENT — RECOMMENDED, NOT DECIDED

**THIS REPORT RECOMMENDS. IT DELETES NOTHING, MOVES NOTHING AND CHANGES NO
CODE.**

1. **DO NOT UNTRACK OR DELETE THE ARTIFACTS.** They are the evidence for a
   superseded point and for this audit; removing them would destroy the record
   that makes this verdict checkable. **Containment is about reading, not about
   existence.**
2. **MARK THEM AT THE DIRECTORY LEVEL.** A `README` in `data/derived/sweep/` and
   `data/derived/analysis/` stating what the files are, which thesis they belong
   to, that they carry outcome quantities, and that no step under the current
   Point 4 may read them. **A marker a future step meets before the file, rather
   than a rule it must remember.**
3. **THE MACHINE-CHECKABLE HALF IS COMMITTED WITH THIS REPORT.**
   `tests/test_artifact_containment.py` fails if any engine module or Point 4
   analysis module acquires a reader. **That is what prevents inadvertent reading
   by code**; it cannot prevent inadvertent reading by a person.
4. **THE GOLDEN FILES AND THE PINNED TRADE NEED A DECISION THIS REPORT DOES NOT
   MAKE.** They are the only outcome-named values read by the current suite. They
   are determinism and arithmetic-identity fixtures, hand-derived, and predate
   everything — **but they are read on every invocation and no committed document
   records them as a permitted exception.**
   `src/engine/sizing.py`'s `net_proceeds_per_unit` carries exactly such a
   recorded carve-out, with three stated conditions. **The golden files and the
   pinned trade have none.** Recommended: an explicit carve-out on the same terms,
   or a statement of why one is not needed. **Owed to its own step.**
5. **DISCLOSE IN THE POINT 4 CLOSING RECORD.** §11's successor should carry this
   audit's finding, so a later reader meets the artifacts with the adjudication
   attached rather than discovering them.

---

## 8. WHAT THIS REPORT DOES NOT DO

**IT READ NO OUTCOME VALUE.** No file under `data/` was opened. Only the header
row of the two golden files under `tests/` was read, and column names are schema.

**IT ESTABLISHED NO SCHEMA BY OPENING.** Every schema comes from the code that
writes or reads the artifact.

**IT DELETED, MOVED AND CHANGED NOTHING**, and §7 recommends rather than decides.

**IT DOES NOT CLOSE THE HUMAN CHANNEL** and §5 names that as the residual.

**IT COMMITS NO NEW RULE.** The carve-out at §7.4 is a recommendation.

---

## 9. ARTIFACTS

- **Report:** `docs/handoff/41_point_4_2_artifact_audit.md`
- **Tests, 19 added:** `tests/test_artifact_containment.py`

**Full suite: 1341 passed** — 1322 before this step, plus the 19 above.
