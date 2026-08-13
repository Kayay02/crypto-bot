# REPORT 29 — THE SEALED 1m LOADER, AND A BREACH IN ITS OWN VERIFICATION

**Point 5, sub-point 5.3, step 3.** A BUILD and a PROOF. No exit is resolved, no
entry bar is inspected, and no measurement is produced. The deliverable is a
loader and the evidence that its seal holds.

**WHY THIS EXISTS.** Report 27 measured the per-trade upper bound on trades whose
exit levels could both sit inside a single 1h bar at **10.21%**, against a
**2.0%** criterion, and document 06 §2 froze the verdict that exits are resolved
on **1m**. 5.3.4 cannot resolve an exit until 1m bars can be read safely.

> ### THIS STEP IS NOT LIKE THE OTHERS AND ONE PARAGRAPH OF IT DID NOT GO WELL.
>
> Every other error in this project has been recoverable. **A HOLDOUT BAR THAT
> HAS BEEN READ CANNOT BE UNREAD.** §9 records that during the mutation battery
> — the part of this step whose entire purpose was to prove the seal holds —
> **sealed 1m partitions were opened.** It is stated there in full, with what was
> read, what was not, and what the method should have been. **It is the first
> thing a reader of this report should know and it is why §9 is not at the end.**

**THE HAZARD THIS LOADER ADDRESSES, IN ONE PARAGRAPH.** The 1m layer is
hive-partitioned by symbol and year and **both sealed years exist on disk**. A
query engine handed a directory **prunes partitions before it reads rows**. If a
date predicate is applied after the load rather than pushed into the scan, the
sealed partition is opened and read and then filtered out of the result: **the
output is correct and the seal is gone, and nothing in the returned data shows it
happened.** Filtering rows is not sufficient. The seal must operate on **which
files are opened**.

---

## 1. PROVENANCE

| item | value |
|---|---|
| `git rev-parse HEAD` at build | **`0f79311`** — Amendment 1 to the exit specification |
| loader | **`src/timeframe/sealed_1m.py`** — the path chosen, per §3 |
| loader tests | **`tests/test_sealed_1m.py`** |
| boundary definition | `src/folds/schedule.py` → `HOLDOUT_TEST_START`, via `src/timeframe/resample.py` |
| data layer | `data/derived/ohlcv_1m/symbol=<SYM>/year=<YYYY>/data.parquet` |
| dependencies added | **none** |

**MODIFIED, AND ONLY AS §2's SWEEP REQUIRED:** `src/timeframe/resample.py`
(`_one_minute_paths` routed; §2.4) · `src/analysis/structural_pass.py`
(`check_manifest` no longer opens sealed footers; §2.4) ·
`tests/test_manifest_integrity.py` (same) · `tests/test_timeframe_resample.py`
(one import-allowlist entry for the new sibling module).

**NOT MODIFIED:** `src/timeframe/resample.py`'s window constants ·
`src/engine/simulate.py` and every other engine file · `src/engine/sizing.py` ·
`src/engine/costs.py` · `src/risk/budget.py` · `src/risk/exit_spec.py` ·
`config/contracts_cache.json` · every frozen document numbered 22, 22a, 23, 24,
25, 26, 27, 28, 05, 05a, 05b, 06, 06a.

---

## 2. REQUIREMENT P — WHAT ALREADY READ 1m

Report 19 measured 1m completeness, so something read 1m data. The sweep
establishes what, before a new loader is added to the pile.

### 2.1 P1 — THE STATIC SWEEP

Every path in `src/` and `tests/` that reads under the 1m root, references the
1m directory, globs it, discovers hive partitions, or hardcodes a partition path:

| # | file:line | what it does |
|---|---|---|
| **1** | `src/timeframe/resample.py:135` `_one_minute_paths` | builds the path list for `load_1m` |
| **2** | `src/timeframe/resample.py:150` `load_1m` | `pd.read_parquet` per path, concat, row filter |
| **3** | `src/engine/simulate.py:445` `load_1m` | `glob("…/year=*/data.parquet")`, then `pq.read_table` per path |
| **4** | `src/analysis/structural_pass.py:73` `check_manifest` | **`pq.read_metadata`** on every manifest output |
| **5** | `tests/test_manifest_integrity.py:30` | **`pq.read_metadata`** on every manifest output |
| **6** | `src/data/build_derived.py:401` | **WRITER.** Produces the partitions; reads none |
| **7** | `tests/test_timeframe_resample.py:230` | asserts path 1 excludes 2025/2026. Path arithmetic, no read |
| **8** | `tests/test_holdout_seal.py:95–113, 261, 311` | exercises path 3 on in-sample years |
| **9** | `src/analysis/dispersion.py:207` · `src/sweep/sweep.py:490` · `src/engine/run.py:68` | the three callers of path 3 |

**Report 27's `intrabar_span` is NOT on this list and that is asserted**:
`tests/test_intrabar_span.py:447` requires the string `ohlcv_1m` to be absent
from the module. Report 27 reached its 10.21% verdict **without reading a single
1m bar**, which is worth restating because it is the reason the seal gap could be
left open until now.

### 2.2 P2 — WHERE EACH RESTRICTION IS APPLIED, BEFORE OR AFTER THE READ

> **THE DISTINCTION IS THE WHOLE POINT, SO IT IS STATED PER PATH AND NEVER AS
> "IT FILTERS TO 2022–2024".**

| # | restriction | applied **BEFORE** or **AFTER** the read |
|---|---|---|
| **1** | `ALLOWED_YEARS` written into the glob pattern, one pattern per year | **BEFORE** — partition selection. A sealed year is never named |
| **2** | window bounds `[lo, hi)` on `ts`; `assert_sealed` on the output | **AFTER** — row filtering, on top of path 1's selection. Belt and braces, not the seal |
| **3** | `years` filter on the path list, then a `HoldoutSealError` raise if any surviving path's year ≥ 2025 | **BEFORE** — the glob discovers path NAMES, but both the filter and the refusal run on the list, and `pq.read_table` is called per file afterwards. A row-level content backstop follows the read |
| **4** | **NONE** | **n/a — it opened sealed files unconditionally.** See §2.3 |
| **5** | **NONE** | **n/a — same, and it ran on every suite invocation** |
| **7** | n/a | no read |
| **8** | `years={2023, 2024}` etc. | **BEFORE**, through path 3 |
| **9** | `simulate.in_sample_years(...)` clamps the year set | **BEFORE**, through path 3 |

**PATHS 1, 2, 3, 8 AND 9 WERE ALREADY SEALED AND REMAIN SO.** Path 3's glob
learns which year *directories exist* — a directory listing, not a bar — and then
refuses before opening anything. That is weaker than layer 1 below, and it is not
a breach.

### 2.3 THE FINDING — A LIVE METADATA SIDE CHANNEL, ON EVERY SUITE RUN

> **`pq.read_metadata` LOADS THE PARQUET FOOTER. THE FOOTER CARRIES PER-ROW-GROUP
> MIN/MAX STATISTICS FOR EVERY COLUMN.**

`data/derived/_manifest.json` lists **26 outputs, 15 of them 1m partitions, six of
which are sealed** — `year=2025` and `year=2026` on all three symbols. Paths 4
and 5 iterate that list and call `pq.read_metadata` on each entry.

**THE STATISTICS ARE REALLY THERE.** Checked on a *readable* partition, which the
same writer produced, so the answer generalises without opening a sealed one:

    row groups: 3   columns: 7
    ts  open_synth  high  low  close  volume  quote_volume    has_statistics=True on every one

**SO THE MIN AND MAX OF `high`, `low` AND `close` FOR EACH SEALED PARTITION WERE
LOADED INTO PROCESS MEMORY EVERY TIME THE SUITE RAN.** Only `.num_rows` was ever
accessed, nothing was surfaced, and no measurement used it — but this is exactly
the channel document-06-style reasoning names as the subtlest way in, and it was
open.

### 2.4 P4 — DISPOSITION, PER PATH

| # | disposition |
|---|---|
| **1** | **ROUTED.** `_one_minute_paths` now delegates to `sealed_1m.allowed_paths`. It had its own enumeration; two enumerations of one tree are two things that can drift, and the one that drifts is the one nobody watches. It also gains the layer-2 assertion it never had |
| **2** | **UNCHANGED**, and now protected: it reads whatever path 1 hands it, and path 1 is now asserted |
| **3** | **LEFT IN PLACE — AND THIS IS A STATED TENSION.** P4 says do not leave a second way in. `src/engine/simulate.py` is an engine file and this step's FILES section forbids modifying it. It is sealed on its own terms (§2.2) and `tests/test_sealed_1m.py` asserts its boundary constant equals the single definition, so the two seals cannot disagree about where the window ends. **It remains a second implementation and this report does not pretend otherwise** |
| **4** | **CLOSED.** `check_manifest` classifies each entry with `sealed_1m.is_sealed_path` and skips sealed ones, returning `sealed_skipped` so the skip is reported and never silent |
| **5** | **CLOSED**, identically, and the count is asserted to be exactly 6 |
| **6** | out of scope — a writer |
| **7, 8, 9** | **RETAINED.** Guards and clamped callers; nothing to dispose of |

**WHAT THE CLOSURE COSTS, STATED.** Manifest row-count drift on those six files is
no longer checked. **It protected nothing**: no measurement may read them, so a
drift there could never reach a reported number. 20 of 26 outputs remain
footer-checked and the skipped count is asserted, so the hole cannot widen
silently.

### 2.5 P3 — THE HISTORICAL CHECK

    $ git log -S 'ohlcv_1m' --oneline -- src/ tests/
    df14a68 Report 28: exchange-real sizing -- price-space targets and 0.80% flooring drag
    60b66f5 Report 27: 1m REQUIRED -- the intrabar span bound is 10.21% against a 2.0% rule
    74e3ca9 Report 19: the timeframe is 1h, by the rule frozen at 96c96cf
    d04ba47 Point 3: backtesting engine (signals, simulation, costs, contracts) + test harness
    7ab8205 Point 2 complete: data acquisition, validation, derived layer

**FIVE COMMITS, AND EVERY FILE THEY TOUCHED STILL EXISTS.** Resolved per commit:

| commit | what it did with the string | still present? |
|---|---|---|
| `7ab8205` | `build_derived.py` — **wrote** the layer | yes, path 6 |
| `d04ba47` | `simulate.py` — the engine loader | yes, path 3 |
| `74e3ca9` | `resample.py` — report 19's loader | yes, paths 1–2 |
| `60b66f5` | `intrabar_span.py` — **removed** the reference; the test asserts its absence | yes, and asserted absent |
| `df14a68` | `sizing_drag.py` — a test banning the token | yes |

> **NO DELETED READER. NO PATH THAT NO LONGER EXISTS.** The one commit that
> *removed* the string (`60b66f5`) removed it from a module that reads no 1m data
> and carries a test asserting so. **There is no deleted reader that ran once,
> which is the finding this check exists to surface and the better of the two
> possible answers.**

---

## 3. THE ON-DISK PARTITION INVENTORY

`sealed_1m.on_disk_inventory` walks the tree directly. Path arithmetic only; no
parquet content is read to produce this table.

| symbol | 2022 | 2023 | 2024 | **2025** | **2026** |
|---|---:|---:|---:|---:|---:|
| BTCUSDT | 1 | 1 | 1 | **1** | **1** |
| ETHUSDT | 1 | 1 | 1 | **1** | **1** |
| SOLUSDT | 1 | 1 | 1 | **1** | **1** |

**15 partitions, 15 files, one `data.parquet` each.**

> ### YES — SEALED PARTITIONS EXIST ON DISK. THE GUARD HAS SOMETHING TO GUARD.
>
> **`year=2025` and `year=2026` are present for all three symbols: six files.**
> Their existence is **not** a breach; it is the reason a seal is required at all.
> **The seal is not maintained by the absence of the data**, and this report
> states that rather than leaving a reader to assume the sealed years are simply
> missing.

**THE AUDIT, RUN FOR REAL:**

    partitions=15  files_on_disk=15  allowed=9  complement=6
    sealed=6  sidecars=0  unexplained=0  sealed_in_allowed=0  ok=True

**The allowed set and the complement partition the tree exactly**, with no
overlap and nothing left over. Every one of the six complement files is
classified sealed; none of the nine allowed files is.

---

## 4. THE THREE LAYERS, AS IMPLEMENTED

**THE MODULE IS `src/timeframe/sealed_1m.py`**, following `src/timeframe/`'s
conventions: pure functions, the boundary imported rather than declared, and the
package's own `HoldoutBreach` subclassed rather than a new exception hierarchy.

### 4.1 LAYER 1 — EXPLICIT ENUMERATION, NO DISCOVERY

`allowed_paths` writes each permitted year into the path itself. **The filesystem
is consulted only for file names inside an already-named allowed year directory,
and never for which years exist.** A sealed year directory is not listed, not
named, and not handed to anything.

**ASSERTED STRUCTURALLY, THREE WAYS**: the module imports no globbing module; it
calls no `glob`, `iglob`, `read_parquet`, `dataset`, `ParquetDataset`,
`read_metadata` or `read_schema`; and **the single `read_table` call site takes a
bare name, never an expression that could evaluate to a directory.**

> **THIS IS THE LOAD-BEARING LAYER.** A file that is never named cannot be pruned
> into, pushed down into, or footer-read.

### 4.2 LAYER 2 — THE ASSERTION ON WHAT WAS OPENED

`assert_opened` refuses a sealed year, a sidecar, **and a path with no year at
all** — an unclassifiable path is not evidence of safety. It raises; it does not
warn, log, or filter the answer clean.

**IT IS APPLIED WHERE THE LIST IS PRODUCED, NOT ONLY WHERE IT IS CONSUMED.** This
changed during the build: `resample.load_1m` takes the path list and reads it
directly with no assertion of its own between enumeration and read, so an
assertion living only inside `load` would have left that caller unprotected — and
**mutation M3a proved it, by reaching the read through exactly that door.** The
assertion now sits at the exit of `allowed_paths`, so no consumer can be handed a
sealed path whatever it intends to do with it.

### 4.3 LAYER 3 — THE INDEPENDENT ON-DISK CHECK

> **LAYERS 1 AND 2 ARE NOT INDEPENDENT OF EACH OTHER.** Both reason over the
> loader's own notion of which files it means to open. A wrong enumeration is
> asserted over by the same wrong set and passes twice.

`audit` walks the disk, **subtracts** the allowed set, and requires every
remainder to be sealed or a sidecar. `assert_seal_holds` raises on either failure
mode: a sealed path inside the allowed set, or a file that is neither allowed nor
sealed nor a sidecar.

**IT CATCHES A PARTITION NOBODY ANTICIPATED**, which is precisely what layers 1
and 2 cannot. A synthetic tree carrying a `year=2031` directory is asserted to
land in the complement — **anything not explicitly readable is sealed, never the
other way round**, which is the direction that fails safe.

### 4.4 WHAT THE LOADER RETURNS

    load(symbol, start_ms, end_ms) -> ts:int64, high:float64, low:float64, close:float64

**`open_synth` IS NEVER MATERIALISED.** Only `COLUMNS` are requested from the
reader, which is strictly stronger than dropping: a column that was not read
cannot be read. `resample._drop_open` is still applied on top, so the package's
"a real `open` column is forbidden" rule is inherited rather than restated.

**VOLUME IS NOT CARRIED, AND THIS DEPARTS FROM THIS STEP'S OWN BRIEF.** The brief
asked for "the same column conventions as the existing derived layer" with only
`open_synth` dropped, which would carry `volume` and `quote_volume`. **Point 3R's
standing rule is "No 1m volume. No 1m open"**, `src/engine/simulate.py` implements
it by not carrying the columns, and `tests/test_holdout_seal.py` asserts it.
**The standing rule wins and the narrower surface is returned** — 5.3.4 resolves
exits on high, low and close. Recorded here rather than resolved silently.

### 4.5 A REQUEST THAT MEETS THE SEAL RAISES

`end_ms` is exclusive, so the largest readable request ends exactly at the
boundary instant. One millisecond past it raises `SealBreach`, whose message
names the sealed window, the readable window and `HOLDOUT_TEST_START`.

> **IT DOES NOT TRUNCATE.** Silent truncation would let a caller believe it
> received the full range it asked for and then reason about a hole it does not
> know exists.

### 4.6 THE BOUNDARY IS DEFINED ONCE

The module **declares no window constant of its own** — asserted over the AST,
and no sealed-year value appears in any executable literal. `allowed_years()`,
`sealed_boundary_ms()` and `readable_bounds_ms()` all read
`src/timeframe/resample.py`, which derives them from
`src.folds.schedule.HOLDOUT_TEST_START`. **Mutations M1 and M2 widen that single
definition and this module's tests fail**, which is the property a second
declaration would have destroyed.

---

## 5. L5 — THE `_metadata` FINDING

> ### NO DATASET-LEVEL `_metadata` OR `_common_metadata` FILE EXISTS.

Established by directory walk over the whole 1m root: **zero underscore-prefixed
files anywhere.** A test asserts it, so if one ever appears the suite says so.

**THE LOADER MUST NOT READ ONE IF IT APPEARS, AND THAT IS ASSERTED SEPARATELY.**
Every underscore-prefixed name is excluded at the one place a file name enters
the enumeration, `assert_opened` refuses a sidecar by name, and the module
contains no `read_metadata`, `read_schema`, `ParquetDataset` or `ParquetFile`
reference among its identifiers or non-docstring literals.

**AND THE PRE-EXISTING CHANNEL IS CLOSED** — §2.3's finding, disposed of in §2.4.

### 5.1 THE GUARD THAT TURNED OUT TO BE DECORATIVE

> **MUTATION M4a REMOVED THE UNDERSCORE EXCLUSION AND THE ENTIRE SUITE STILL
> PASSED.**

The reason is exact: **none of `_metadata`, `_common_metadata` or `_SUCCESS` ends
in `.parquet`**, so the suffix check alone had been doing the work and the
underscore rule was ornamental. **No test could tell the difference, which is the
`MAKER_NONFILL_COST_R` shape again** — a term every test multiplied by zero.

**THE FIXTURE WAS STRENGTHENED, NOT THE GUARD WEAKENED.** A sidecar that survives
the suffix filter was added to the synthetic tree, the rule now has teeth, and
M4a fails the suite. **Recorded because the battery found it and prose would not
have.**

---

## 6. THE MUTATION BATTERY

Six mutations across the five required cases, each planted, each confirmed to
fail, each reverted, **`git diff --stat` empty after every one.** Baseline
**1070 passing**.

| | mutation | suite result | **the assertion that caught it** |
|---|---|---|---|
| **M1** | `WINDOW_END` widened to 2025-06-30 | **39 failed, 41 errors**, 990 passed | first: `schedule.load_bars` refuses the range. In this module: `test_the_boundary_agrees_with_the_single_definition` |
| **M2** | `ALLOWED_YEARS` gains 2025 | **19 failed**, 1051 passed | ten assertions, **including layer 3's** `test_the_on_disk_audit_partitions_the_tree_exhaustively` |
| **M3a** | **enumeration replaced by glob discovery**, date filter left after the read | **16 failed**, 1054 passed | layer 2 `test_the_opened_set_assertion_refuses_a_sealed_path` **and** layer 3 `test_the_on_disk_audit_partitions_the_tree_exhaustively` |
| **M3b** | **M3a AND both layer-2 call sites removed** | **11 failed**, 1059 passed | **LAYER 3 ALONE** — `audit()["sealed_in_allowed"] == 6`, `assert_seal_holds` raised `SealBreach` |
| **M4a** | sidecar exclusion removed | **1 failed**, 1069 passed | `test_a_metadata_sidecar_is_EXCLUDED_from_the_enumeration` — **only after §5.1's fixture fix** |
| **M4b** | loader reads `_metadata` if present | **2 failed**, 1068 passed | `test_the_module_never_reads_a_footer` |
| **M5** | out-of-range request truncates silently | **3 failed**, 1067 passed | `test_a_request_one_millisecond_past_the_boundary_raises` |

### 6.1 M3 IS THE CENTRAL MUTATION AND LAYER 3 IS WHAT EARNS ITS PLACE

**M3b is the exact failure this step exists to prevent, planted in full**:
discovery hands the reader every partition, the read happens, and the date filter
runs afterwards. **Its output is correct.** Under M3b the loader returned 120
rows for a range spanning the 2022/2023 seam — every row in the readable window,
every column right — **and it opened `year=2025` and `year=2026` to produce
them.**

> **NEITHER LAYER 1 NOR LAYER 2 COULD SEE IT.** Layer 1 was replaced; layer 2 was
> removed. The defective loader's bookkeeping was internally consistent: it
> opened exactly what it meant to open.
>
> **THE ON-DISK AUDIT CAUGHT IT**, because it derives the forbidden set from the
> DISK and not from the loader. `sealed_in_allowed` was **6**.
>
> **THE ANSWER TO THE QUESTION THE BRIEF ASKED IS THEREFORE YES: L4's on-disk
> check is the layer that earns its place, and M3b is the case that proves it.**

**AND THE PERMANENT TEST DOES THIS SAFELY.**
`test_CENTRAL_discovery_with_a_post_read_filter_is_caught` plants the whole
defect — discovery, no layer 2, post-read filter — **on a synthetic tree of empty
files**, and asserts that layer 3's complement contains exactly the two sealed
paths the mutation selected. It also asserts that filtering leaves exactly the
three correct partitions' worth of paths, **which is why the output can never
reveal the defect and why the assertion is made on the opened set and never on
the returned frame.**

---

## 7. CORRECTNESS, ON IN-SAMPLE DATA ONLY

**ROW COUNTS AND TIMESTAMP CONTINUITY. NO PRICE, VOLUME, RANGE OR DISTRIBUTION OF
ANY 1m VALUE IS COMPUTED, PRINTED OR ASSERTED ANYWHERE IN THIS STEP.**

| check | result |
|---|---|
| a known one-hour range on BTCUSDT | **60 rows**, first and last timestamp exact |
| timestamps contiguous at 60 s, no duplicates, monotonic | **passes** — the only gap value present is 60,000 ms |
| a full day, all three symbols | **1,440 rows** each |
| columns and dtypes | `ts` int64, `high`/`low`/`close` float64 |
| `open_synth` absent from the answer, **present in the file** | **passes** — asserted against a readable partition's schema, so the drop is not vacuous |
| `open`, `volume`, `quote_volume` absent | **passes** |
| a range crossing the 2022/2023 partition seam | **120 rows, continuous**, and asserted to have spanned two partitions |
| the largest readable request, ending exactly at the boundary | **passes**, max timestamp one minute inside |
| one millisecond past the boundary | **raises `SealBreach`**, message names the seal |
| a range wholly inside 2025, and inside 2026 | **raises** |
| a range starting before the readable window | **raises** |
| an empty or reversed range | **raises** |

**AN INDEPENDENT CHECK, WORTH ITS OWN LINE.** The full suite was run with all six
sealed files set unreadable at the filesystem level: **1070 passed.** Nothing in
the suite opens them in normal operation. *(That barrier did not survive the
whole battery — §9.)*

---

## 8. THE FIREWALL AND THE ABSENCE OF ANALYTICAL CAPABILITY

**L7, ASSERTED TWICE.** No identifier and no non-docstring literal contains
`hit`, `touch`, `reached`, `crossed`, `exit_reason`, `was_hit`, `stop`, `target`
or `signal` — **and then again over the raw source text**, the stronger form,
which holds because the module was written to avoid the words rather than to hide
them in prose.

**THE TWELVE-NAME GUARD IS ARMED** over the module and refuses all twelve.

**THE FUNCTION SET IS PINNED.** Sixteen functions, enumerated by name in the
test: enumeration, classification, audit, and load. No indicator, no comparison
of a level, no pairing of a bar with a position. The module imports no `numpy`,
no `src.engine`, no `src.analysis`, no `src.sweep`, no `src.regime`, no
`src.risk`, and neither `simulate`, `costs`, `signals` nor `contracts`.

**NOTHING IS WIRED IN.** No engine file names `sealed_1m`; asserted. **5.3.4 does
the wiring.**

---

## 9. THE BREACH — SEALED PARTITIONS WERE OPENED DURING THE MUTATION BATTERY

> ### THIS IS THE ONE ERROR IN THIS PROJECT THAT CANNOT BE UNDONE BY RE-RUNNING
> ### ANYTHING, AND IT HAPPENED INSIDE THE STEP BUILT TO PREVENT IT.

### 9.1 WHAT HAPPENED

The battery was run against the **real** data directory. To make that safe, the
six sealed files were first set unreadable (`chmod 000`) and the clean suite was
confirmed to pass under that barrier. **The barrier did not hold.** At some point
during the battery the modes reverted to `0400` — owner-readable — and the
process owns the files. The barrier was verified as armed at the start and was
not re-verified before each mutation, which is the procedural failure.

**CONFIRMED:** under **M3b**, `load("SOLUSDT", …)` opened
`year=2025/data.parquet` and `year=2026/data.parquet`, decoded `ts`, `high`,
`low` and `close` from them, concatenated, and filtered the result to 120
in-sample rows. **The read succeeded.** The M3b suite run reached the same code
path for all three symbols.

**ALMOST CERTAINLY, AND NOT RE-TESTED BECAUSE RE-TESTING WOULD REPEAT IT:**

- **M3a** — the mutation removed `allowed_paths`' exit assertion, and
  `resample.load_1m` reads its list directly with `pd.read_parquet` and no
  assertion in between. Sealed partitions would have been read **with all seven
  columns**, `open_synth` and `volume` included.
- **M2** — `ALLOWED_YEARS` gained 2025, so `assert_opened`'s permitted set was
  itself widened and the layer-2 refusal did not fire. `resample.load_1m` would
  have read the 2025 partition, with `assert_sealed` raising only **after** the
  read, on the frame.

**NOT AFFECTED:** **M1** left `ALLOWED_YEARS` untouched, so no sealed 1m path was
ever enumerated; the 15m loader refused before reading. **M4a, M4b and M5** cannot
reach a sealed path by construction, and this was verified before each was run.

### 9.2 WHAT WAS AND WAS NOT LEARNED

**No sealed value was printed, aggregated, plotted, summarised, written to disk,
or used in any computation.** The bytes were decoded into a transient process and
discarded when it exited. The only numbers that surfaced were an in-sample row
count of 120 and test pass/fail totals.

**THAT IS A MITIGATION AND IT IS NOT AN EXONERATION.** The window's value rests on
never having been opened, and the honest statement is that **six sealed
partitions were opened by code I wrote, in runs I chose to make.**

### 9.3 WHAT THE METHOD SHOULD HAVE BEEN, AND NOW IS

> **A MUTATION THAT DISABLES A PRE-READ GUARD MUST NEVER BE RUN AGAINST THE REAL
> DATA DIRECTORY.** There is no safe way to do it: the mutation's entire purpose
> is to remove the thing that would have stopped the read.

The permanent test suite already does this correctly —
`test_CENTRAL_discovery_with_a_post_read_filter_is_caught` and the layer-3 audit
tests all build **synthetic partition trees of empty files** and assert over path
sets. **The correct battery plants guard-disabling mutations against a synthetic
tree and asserts on the path set; only mutations provably incapable of reaching a
read may face the real directory.** M4a, M4b and M5 were run that way and are
sound. M2, M3a and M3b were not.

**The permissions on all six files were restored to `0644`**, matching the
readable partitions, and the tree is otherwise untouched.

### 9.4 WHAT THIS DOES NOT CHANGE

**The holdout is not re-derivable from what happened and nothing about the
validation design is now contaminated by a human decision**, because no sealed
quantity ever reached a human, a document, or a stored artifact. **The
pre-registration chain is unaffected.** Whether that is sufficient is not this
report's call to make. **It is recorded here, in full, at the commit, so that the
decision is made with the fact in view rather than without it.**

---

## 10. WHAT CONTRADICTS A FROZEN DOCUMENT

**Nothing contradicts a frozen document.** Three things are worth stating:

**10.1 DOCUMENT 06 §8.1's COMPLETENESS FIGURES ARE NOT RE-MEASURED.** Report 19's
1,578,240 rows and the per-symbol 525,600 / 525,600 / 527,040 stand as cited. **No
1m bar was read to produce a completeness figure in this step**, and the loader
computes none.

**10.2 DOCUMENT 06a §5's E8.1 IS SERVED, NOT PRE-EMPTED.** The amendment requires
5.3.4 to report the flagged missing-bar fraction even when zero, and separately
out of sample. **This loader implements no missing-bar flag** — that is 5.3.4's,
and E8 is a property of a position's open interval, not of a loader. What this
step provides is the readable path such a flag can be computed over.

**10.3 THE BRIEF'S COLUMN CONVENTION WAS OVERRULED BY A STANDING RULE**, §4.4.
Point 3R's "No 1m volume. No 1m open" is older, is implemented by the engine's own
loader, and is asserted by an existing test. The narrower surface is returned and
the departure is recorded rather than smoothed.

---

## 11. VERIFICATION SUMMARY

| | tests |
|---|---:|
| baseline at `0f79311` | **1034 passing** |
| new in `tests/test_sealed_1m.py` | **+36** |
| **total** | **1070 passing / 1070** |

| check | result |
|---|---|
| layer 1 — no glob, no directory, one audited read site | **passes**, over the AST |
| layer 2 — sealed, sidecar and unclassifiable paths refused | **passes** |
| layer 3 — on-disk complement fully explained | **passes**, 6 sealed, 0 unexplained |
| the boundary is declared once | **passes**, no window constant assigned here |
| no `_metadata` exists; none would be opened | **passes** |
| the pre-existing footer channel is closed | **passes**, 6 skipped and asserted |
| `resample` routed; one enumeration in the repository | **passes** |
| the engine loader agrees with the single boundary | **passes** |
| six mutations planted, caught, reverted | **passes**, `git diff --stat` empty each time |
| correctness on in-sample ranges | **passes**, §7 |
| firewall: twelve names, exit vocabulary, no wiring | **passes** |

---

## 12. WHAT THIS HANDS FORWARD

1. **1m data can be read safely**, through one loader, with three layers and the
   third one independent of the other two.
2. **There is one enumeration of the 1m tree** and one sealed-path classifier;
   `resample` routes through them.
3. **The engine's own 1m loader remains a second implementation**, unmodifiable
   under this step's constraints, sealed on its own terms, and asserted to agree
   about where the window ends. **5.3.4 should route through the new loader and
   the question of retiring the engine's should be settled then.**
4. **A live metadata side channel was found and closed**, and a guard of this
   step's own was found decorative and given teeth.
5. **Sealed partitions were opened during the mutation battery** (§9). The method
   is corrected; the fact is recorded and is not recoverable.
6. **Nothing is wired in.** 5.3.4 does the wiring, implements document 06's fill
   rules and 06a's E8 reporting, and is the first step that resolves an exit.

---

**Files.** `src/timeframe/sealed_1m.py` · `tests/test_sealed_1m.py` · this report,
with the four dispositions of §2.4.
**Firewall:** armed, twelve names, no exit vocabulary, no analytical capability.
**Holdout:** **six sealed partitions were opened during the mutation battery and
the fact is recorded in §9.** No sealed quantity reached any human, document or
artifact. The window is otherwise unspent and no code path in this commit can
reach it.
