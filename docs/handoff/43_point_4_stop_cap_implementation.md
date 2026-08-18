# REPORT 43 — STEP REPORT-BACK: THE STOP CAP'S REMOVAL FROM THE ENGINE

## 0. GENRE

**A STEP REPORT-BACK, NOT AN ANALYSIS REPORT.** Declared here because
`docs/design/04_2e_housekeeping.md` §5.2 files both kinds in one numeric
sequence under `docs/handoff/` and requires the genre to be carried by the
document. Written to a file and committed with the step it reports; the chat
channel carries this file's path, its SHA-256, its line count, the commit hash
and the test count, and discussion, and no other account of the work.

**THE COMMIT HASH IS NOT IN THIS FILE AND CANNOT BE** — a file recording its own
commit's hash changes that hash.

**NOT A MEMBER OF THE FROZEN SPECIFICATION.** Evidence, per
`docs/design/04_0_divergence_disposition_amendment_2.md` §2.

**NO OUTCOME QUANTITY IS COMPUTED OR INSPECTED**; nothing under `data/` for
`year=2025` or `year=2026` was opened; no artifact under
`docs/design/04_2a_artifact_containment.md` §3's prohibition, as amended at
`docs/design/04_2e_housekeeping.md` §2.2, was opened. **The engine was not run
in full evaluation mode over the real population.**

---

## 1. THE MANIFEST

**HASH ON ENTRY:**
`e1c1edfed66b9c774650e7811cbff684b4b2291fcd9e4a8aedf4eb79664107ed`

**VERIFICATION: 63 hashed entries parsed, 63 match, 0 mismatches, 0 missing.**
Every hash recomputed from the working tree; none compared against a value
quoted in another document. **The four unhashed entries at §4 all exist.**

**`docs/prompts/STANDING_RULES.md` MATCHES THE SUPPLIED HASH:**
`da63e28104e41890dfea438b95f98ca67e4972034e4cbc8505e894c0a0077873`.

---

## 2. PART 0 — EVERY READER, ENUMERATED AND CLASSIFIED

**METHOD: AST NODES, NEVER RAW TEXT.** Every `.py` file under `src/` and
`tests/` was parsed and every `Attribute`, `Name`, `arg` and `keyword` node
named `stop_max_pct` or `stop_geometry` collected with its enclosing function.
**40 references to `stop_max_pct` and 6 to `stop_geometry`.**

### 2.1 `stop_geometry` — SIX REFERENCES, AND THE CALLER SET IS SMALLER THAN THE ADOPTION STATES

- **`src/engine/costs.py:238`** — the definition. **THE ONLY FUNCTION IN THE
  REPOSITORY THAT EVER APPLIED A CAP.**
- **`src/engine/costs.py:261`** — `costs.stop_price` calls it and returns the
  price. **`stop_price` IS CALLED FROM NOWHERE IN `src/`** — only from
  `tests/test_costs.py`. That is narrower than
  `docs/design/04_1g_cap_adoption.md` §4.1 states, and is recorded because it
  means the cap had exactly **one** production reach.
- **`src/engine/simulate.py:179`** — `simulate_trade`. **THE ONE PRODUCTION
  APPLICATION.**
- **`tests/test_costs.py:55-59`** — four assertions, one of which pinned the cap.

> ### **CLASSIFICATION: ONE DEFINITION, ONE PRODUCTION CALLER, ONE TEST-ONLY
> ### CALLER, ONE TEST. §4.1's "AND FROM NOWHERE ELSE" IS CONFIRMED.**

### 2.2 `stop_max_pct` — FORTY REFERENCES IN FIVE CLASSES

**CLASS 1 — ON THE STOP RULE, SO THE CAP MUST GO. Two sites.**

- **`src/engine/costs.py:247`**, inside `stop_geometry`: `hi = cfg.stop_max_pct
  * entry`, then `elif raw > hi: dist, mech = hi, CAP`. **This is the
  divergence.** Reachable from the frozen thesis's evaluation path? **Not
  through `portfolio.size_position`** — §4.1 is right that the governing path
  calls `sizing.stop_distance`, which applies no upper bound — **but reachable
  through `simulate.py`, which the sweep and `src/engine/run.py` and the golden
  fixtures all run.** **REMOVED.**
- **`src/engine/simulate.py:186`**, a trace line printing `cap
  {cfg.stop_max_pct:.3%}`. Applies nothing, but **states a cap in the
  human-readable channel**, which is the same divergence in a different
  medium. **CHANGED.**

**CLASS 2 — ON THE SWEEP'S OWN PATH, WHICH §5 LEAVES ALIVE. Two sites, both
untouched.**

- **`src/sweep/sweep.py:153`**, `cfg_for`: `stop_max_pct=float(cell["stop_max_pct"])`
  — the per-fold `derived_cap` supplied into `CostConfig`. **`sweep.py:399`
  calls `simulate.run_backtest`, so this value was applied through
  `stop_geometry`.** After this step it is still supplied and no longer applied.
- **`src/sweep/grid.py:73`**, `base_cfg` — explicitly-arbitrary scaffolding whose
  invariance the sweep's own tests assert.

**CLASS 3 — ANALYSIS MODULES USING THE CAP AS A STRUCTURAL BOUND. Nine sites,
all untouched.**

- **`src/analysis/risk_unit_floor_curve.py:206, 225, 440`** — `ratio_at_cap`
  evaluates the ratio at the cap as "THE OTHER END" of an interval;
  `monotonicity` sweeps `(0, cap]`; `solve_and_feed_back` records
  `exceeds_cap`. **This is the module `docs/prompts/MANIFEST.md` names as the
  governing derivation module**, and it is the use
  `docs/handoff/36_point_4_1c_risk_unit_derivation.md` made of the cap.
- **`src/analysis/level_consequences.py:291`** — report 37's stratification.
- **`src/analysis/haircut_share_rerun.py:100, 187`** — report 34's re-run,
  superseded as governing.
- **`src/analysis/cap_candidates.py:246, 275`** — report 39's own module, whose
  whole subject is domains under candidate caps.
- **`src/analysis/structural_pass.py:536`** — `m8_floor`, config construction.

> ### **NONE OF THESE APPLIES A CAP TO A STOP. EACH USES THE VALUE AS THE UPPER
> ### END OF AN INTERVAL A CURVE IS SWEPT OVER, OR AS A FLAG ON A WIDTH.** They
> ### are derivation apparatus, not stop geometry, and
> ### `docs/design/04_1g_cap_adoption.md` §5 item 2 names them as the reason the
> ### parameter survives.

**CLASS 4 — CONFIG CONSTRUCTION ELSEWHERE, NOT THE STOP RULE. Four sites,
untouched.** `src/analysis/dispersion.py:182`,
`src/analysis/exposure_profile.py:150`, `src/folds/warmup.py:69`,
`src/regime/measure.py:132`, and `src/engine/run.py:146` (the CLI argument).

**CLASS 5 — TESTS. Twenty-three sites** across fourteen modules, all supplying
the parameter as required scaffolding. **Exactly two asserted the cap's effect**
— `tests/test_costs.py`'s two — and both are handled at §5.

### 2.3 ONE FURTHER SITE, FOUND AND NOT TOUCHED

**`src/engine/diagnostics.py:48` LABELS THE CAP BUCKET `"3.5% cap"`**, hard-coding
the retired constant in a display string.

> **IT IS IMPORTED BY NOTHING.** An AST scan of every `Import` and `ImportFrom`
> node under `src/` and `tests/` returns no importer. **It applies nothing, is
> on no path, and was left alone** as outside the minimum change. Recorded so it
> is not discovered later as a surprise.

---

## 3. WHETHER A LIVE CONSUMER STILL REQUIRES THE PARAMETER

> ### **YES, AND THE STOP CONDITION WAS THEREFORE NOT TRIGGERED.**

**THE INSTRUCTION'S STOP CONDITION** was: stop if removing the cap from the
governing path would require **removing the parameter** from a consumer the
adoption left alive.

**IT DOES NOT.** `stop_max_pct` remains a required `CostConfig` field, still in
`NO_DEFAULT_PARAMS`, still supplied at every construction site, still read by
Classes 2, 3 and 4. **What was removed is its application on the stop rule, not
the parameter.** `docs/design/04_1g_cap_adoption.md` §5 item 2 keeps it
expressly, and §4.1 of this step's own guard pins that it is still required.

**AND THE ADOPTION ANTICIPATED EXACTLY THIS OUTCOME, IN ITS OWN WORDS.** §5's
closing paragraph asks

> "**Whether the sweep should still derive a cap it no longer supplies to the
> engine** is a question for whoever next touches the sweep."

**"A CAP IT NO LONGER SUPPLIES TO THE ENGINE" PRESUPPOSES THE STATE THIS STEP
CREATES.** The sweep still derives `derived_cap`, still writes it into its grid,
and still passes it into `CostConfig`; it is simply no longer applied. **The open
question — whether deriving it remains worthwhile — is untouched and undecided.**

**WHAT FOLLOWS.** Nothing in the sweep changed. A test at §4 below pins
structurally that `sweep.cfg_for` still supplies the value, so a later step
cannot withdraw it quietly through this path.

---

## 4. PART 1 — WHAT CHANGED, AND WHY IT IS THE MINIMUM

**THREE EDITS, IN TWO SOURCE FILES.**

**1. `src/engine/costs.py`, `stop_geometry` — THE CAP BRANCH REMOVED.** Two
lines of logic: `hi = cfg.stop_max_pct * entry` and the `elif raw > hi` arm. The
function is now `max(ATR multiple, floor)` and returns `atr` or `floor`.

**WHY `stop_geometry` AND NOT ITS CALLER.**
`docs/design/04_1g_cap_adoption.md` §5 offers both — "changing `stop_geometry` or
its caller". Changing the caller was rejected: `stop_geometry` is also reached
from `costs.stop_price`, so a caller-side fix would leave a capping function
inside `costs.py` that the specification says does not exist, and the divergence
would persist in the module rather than being closed. **One function, one branch,
and the divergence has nowhere left to live.**

**2. `src/engine/costs.py`, the `ATR, FLOOR, CAP` constants — KEPT, WITH A NOTE.**
`CAP` is now unreachable and is not deleted, on two committed grounds: §4.4 of
the adoption records that the reject-over-clip rule is **inoperative rather than
repealed** and "would govern again the moment one did", recorded so a later step
reintroducing a cap does not re-derive it; and the counters at `simulate.py:700`
and `:736` report the cap branch as **zero rather than omitting it**, which is
the treatment `docs/design/06a_exit_resolution_spec_amendment_1.md` §5.3 requires
of a zero-valued branch.

**3. `src/engine/simulate.py` — THE TRACE LINE AND ONE COMMENT.** The trace no
longer prints a cap. The comment justifying the minimum-order guard rail by
"`stop_max_pct` already guards width in percent" now records that **nothing
guards width at all**, and that this guard rail is consequently the only refusal
a wide stop can meet — which is why §6 of the adoption makes the count of
refusals for quantity or notional **the adoption's own falsifier**.

**WHY THIS IS THE MINIMUM.** Nothing else in `src/` applies a cap: the caller set
at §2.1 is closed and was re-verified after the change by a test that fails if a
third caller appears. The floor is untouched. The sweep is untouched. The
admitted domain's derivation is untouched. `stop_max_pct` survives. **No file
outside `src/engine/` was modified.**

---

## 5. PART 2 — THE NEGATIVE CONTROL

**THE GUARD: `tests/test_no_stop_cap.py`, 16 tests.** Its fixture is
`docs/handoff/39_point_4_cap_candidates.md` §4.1's widest measured cell —
**SOLUSDT, entry 10.0108, ATR 2.2117, width 49.7087 per cent** — used verbatim,
with the two narrower cells beside it. **The width exceeds the retired 0.035 by
more than fourteen times**, so any cap near the retired level clips it by a
margin no rounding accounts for.

**IT COVERS FIVE LIMBS:** the geometry that used to clip, on both sides; a sweep
across 200 widths from 0.005 to 1.000 of entry asserting the cap mechanism is
unreachable at every one; the floor still binding below it, so the guard cannot
pass on a geometry that lost the floor too; **the governing path end to end**,
asserting the unclipped distance is what the sizing denominator was built from;
and the structural limbs — that `stop_geometry` does not read the parameter, that
`CAP` is assigned nowhere in it, and that the caller set is still exactly the two
the adoption names.

### 5.1 VERIFIED BY BREAKING IT

**WHAT WAS REINTRODUCED.** The two removed lines, restored verbatim into
`stop_geometry`:

```
    hi = cfg.stop_max_pct * entry
    ...
    elif raw > hi:
        dist, mech = hi, CAP
```

**WHAT FAILED: 10 OF 16 TESTS.** The messages, quoted from the run with
`pytest`'s plus-minus character rendered as `+/-` to keep this document
inside the non-ASCII set every recent step has held to:

- `test_the_widest_measured_width_SURVIVES_on_the_short_side[SOLUSDT]` —
  **`assert 0.03500219762656336 == 0.497087 +/- 1.0e-04`**. The width was clipped
  from 49.7 per cent to 3.5.
- the same, ETHUSDT — `assert 0.03500002619323265 == 0.118216 +/- 1.0e-04`;
  BTCUSDT — `assert 0.035000000000000066 == 0.085315 +/- 1.0e-04`.
- `test_the_widest_cell_of_all_is_more_than_fourteen_TIMES_the_retired_cap` —
  **`AssertionError: assert 'cap' == 'atr'`**.
- `test_the_widest_measured_width_SURVIVES_stop_geometry[BTCUSDT|ETHUSDT|SOLUSDT]`
  — **"the fixture no longer reproduces report 39 section 4.1's width"**.
- `test_the_CAP_MECHANISM_IS_UNREACHABLE_at_every_width` — **"a cap was applied
  somewhere in the sweep"**.
- `test_stop_geometry_does_not_READ_the_cap_parameter` — **"stop_geometry reads
  the cap parameter again"**.
- `test_the_cap_label_survives_and_is_assigned_nowhere_in_the_geometry` —
  **"stop_geometry can still return CAP"**.

**WHAT DID NOT FAIL, AND IT IS THE RIGHT ANSWER.**
`test_the_widest_width_SURVIVES_TO_SIZING_on_the_governing_path` **passed with
the cap reintroduced**, because `portfolio.size_position` reaches
`sizing.stop_distance` and never `stop_geometry`. **That is
`docs/design/04_1g_cap_adoption.md` §4.1's claim, confirmed by a control rather
than assumed:** the governing path was already uncapped, and the divergence lived
entirely on `simulate.py`'s side.

**RESTORED FROM A BYTE-COPY**, `shasum -a 256` identical before and after —
`b81dd4b76c3bda2de1adf8523ca235c3ca4c28717746681e5603df82b062e89f` — and the
16 tests re-verified green.

---

## 6. PART 3 — WHAT ELSE MOVED

**BASELINE 1378 PASSING. AFTER THE CHANGE, BEFORE ANY TEST WAS TOUCHED: 1392
PASSED, 2 FAILED.** With the guard's 16 added, the arithmetic is
1378 + 16 - 2 = 1392.

> ### **EXACTLY TWO TESTS CHANGED RESULT, BOTH IN `tests/test_costs.py`, AND
> ### BOTH ASSERTED THE RETIRED CAP DIRECTLY.**

- **`test_stop_distance_floor_and_cap`** — `assert 25.0 == 96.5 +/- 9.7e-05`. It
  asserted that ATR=50 on a 100.0 entry produces a stop at **96.5**, three and a
  half per cent wide. Under the adoption it produces **25.0**, the full
  `1.5 x 50` distance.
- **`test_stop_binding_mechanism_is_reported`** — `assert 'atr' == 'cap'`. It
  asserted the cap mechanism on the same input.

**HANDLED ON THE CONSOLIDATED STEP'S MODEL, NOT BY EDITING LITERALS GREEN.** The
retired figure is kept in the file as a named comparison —
`STOP_UNDER_THE_RETIRED_CAP = 96.5` beside `STOP_UNDER_NO_CAP = 25.0` — the test
asserts the new value **and** asserts it is not the old one with the message "the
retired cap is being applied again", and both docstrings record that the test
asserted the cap until the adoption was implemented. The first test is renamed
`test_stop_distance_floor_and_NO_cap`, because a test named for a cap that does
not exist is a name that will mislead.

### 6.1 NO REGRESSION FIXTURE MOVED, AND THAT IS A FINDING

**REPORTS 24, 26, 27, 28, 30, 32, 34, 36 AND 37 REST ON THIS CODE. NOT ONE OF
THEIR REGRESSIONS CHANGED.**

- **`tests/test_determinism_golden.py` PASSED** — the golden hash, the column
  list and the row count are unchanged, so **no row of the frozen January 2023
  BTCUSDT slice was cap-bound**. Establishing that required no reading of the
  fixture: the hash comparison is the evidence.
- **`tests/test_regression_pinned_trade.py` PASSED** — the pinned trade is
  floor-bound and the floor is untouched.
- **`tests/test_portfolio_path.py`'s report-26 reconciliation PASSED** — that
  population is built by `exposure_profile.stop_distance` and sized by
  `portfolio.size_position`, neither of which ever saw a cap.
- **`tests/test_sizing_drag.py`, `tests/test_budget_cost.py`,
  `tests/test_intrabar_span.py`, `tests/test_level_consequences.py`,
  `tests/test_risk_unit_floor_curve.py`, `tests/test_stop_cap_audit.py`,
  `tests/test_cap_candidates.py` ALL PASSED UNCHANGED.**

> ### **THE CAP WAS APPLIED ON EXACTLY ONE PRODUCTION PATH AND THAT PATH FED NO
> ### CLOSED REPORT'S FIGURES.** The 4.1 analysis chain never reached it, which
> ### is what `docs/design/04_1g_cap_adoption.md` §4.1 asserts and what the
> ### suite now demonstrates.

**FINAL: 1394 PASSING**, 1378 + 16, no failures and no skips.

---

## 7. FREEZE PRECONDITION 3

**`docs/design/04_2b_point_4_decomposition.md` §4.3 PRECONDITION 3 REQUIRES:**
*"THE SPECIFICATION AND THE IMPLEMENTATION DO NOT DIVERGE IN ANY KNOWN
RESPECT"*, and names one open case — that `src/engine/simulate.py` still applies
a stop cap the specification has retired.

**THE TWO DIVERGENCES THAT HAVE EVER BEEN NAMED AGAINST IT ARE NOW BOTH
CLOSED:**

1. **The seal-crossing exclusion** — `docs/design/04_2c_run_structure.md` §4.4
   and §4.5 — implemented at commit `1064028` and ratified at
   `docs/design/04_2e_housekeeping.md` §4.4.
2. **The stop cap** — `docs/design/04_1g_cap_adoption.md` §0 — implemented by
   this step, with a guard verified by breaking it.

> ### **PRECONDITION 3 IS CLOSED AS TO EVERY DIVERGENCE ANY COMMITTED DOCUMENT
> ### HAS NAMED.**

**IT IS NOT THEREFORE SATISFIED, AND THE DISTINCTION MATTERS.** The precondition
is worded over **any known respect**, not over a list. **Closing every named
divergence discharges the list; it does not by itself establish that no unnamed
one exists**, and this step looked only where the cap was. **A reader evaluating
the precondition should treat it as met on the record and open to any divergence
a later step finds** — which is what the containment guard's first run
demonstrated is a live possibility.

**ONE ITEM IS RECORDED AS OBSERVED AND NOT CLASSIFIED HERE:**
`src/engine/diagnostics.py:48`'s `"3.5% cap"` label, in a module imported by
nothing. **It applies nothing and is on no path**, so it is not a divergence in
behaviour; **it is a statement of a retired rule surviving in source.** Whether
the precondition's wording reaches a dead module's display string is not settled
by any committed document and is not settled here.

---

## 8. WHAT THE COMMITTED DOCUMENTS DID NOT SETTLE

**FOUR THINGS, STATED RATHER THAN DECIDED.**

1. **WHETHER THE ANALYSIS MODULES SHOULD STILL TAKE THEIR UPPER BOUND FROM
   `stop_max_pct`.** `src/analysis/risk_unit_floor_curve.py`'s `ratio_at_cap`
   and `monotonicity` sweep `(0, cap]` with `cap = cfg.stop_max_pct`, i.e. from
   the retired constant. **Under the adoption the binding width is the widest
   achievable ATR width**, and `docs/design/04_1g_cap_adoption.md` §4.2 already
   records the recomputed bound as **0.00359143** with the committed level of
   0.10 still inside. **The instruction expressly forbade recomputing the
   domain, and §5 item 2 anticipates these modules keep reading the parameter.**
   Whether their bound should be re-sourced is unsettled. **No owner.**
2. **WHETHER THE SWEEP SHOULD STILL DERIVE A CAP.** §5's own open question,
   untouched. It is now exactly the question §5 framed: a cap the sweep derives
   and no longer supplies to the engine. **Routed by §5 to whoever next touches
   the sweep. No owner.**
3. **`src/engine/diagnostics.py`'s RETIRED LABEL.** §7 above. **No owner.**
4. **WHETHER `costs.stop_price` SHOULD SURVIVE AT ALL.** It is called from no
   module under `src/` — only from `tests/test_costs.py`. That is narrower than
   `docs/design/04_1g_cap_adoption.md` §4.1 records and is a fact this step
   found rather than a decision it takes. **Not removed; no committed document
   asks for it. No owner.**

---

## 9. THE TWO STANDING CLOSING ITEMS

### 9.1 WHERE A REQUIREMENT CONTRADICTED A CONSTRAINT

**NONE.** The instruction's stop conditions were checked and neither fired:
removing the cap from the stop rule required removing no parameter from a live
consumer (§3), and the implementation matches the adoption as written (§4).

**ONE NEAR-MISS IS RECORDED.** Part 2 directs the guard at "the governing path",
and `docs/design/04_1g_cap_adoption.md` §4.1 establishes that the governing path
**never had a cap**. A guard written only against `portfolio.size_position`
would therefore have passed before the change and after it, proving nothing —
and the negative control at §5.1 shows exactly that, since the governing-path
limb was one of the six that did **not** fail. **The guard was written against
the path that actually clipped as well as the one that did not**, which is what
gives it teeth. Recorded because a reader checking the guard against the
instruction's wording will find it broader than the words.

### 9.2 ANYTHING READABLE AS NARROWER OR BROADER THAN INTENDED

**`CAP`'s SURVIVAL COULD BE READ AS THE CAP SURVIVING.** It does not: the label
is a name for a mechanism nothing produces, kept because §4.4 keeps the rule
that would classify with it. A test asserts it is assigned nowhere in the
geometry.

**THE GUARD'S WIDTH SWEEP RUNS TO 1.000 OF ENTRY**, which is far past anything
the population produces. That is deliberate breadth, so a cap reintroduced at an
implausible level is caught too; it should not be read as a claim that such
widths occur.

**§7's "CLOSED AS TO EVERY NAMED DIVERGENCE" IS DELIBERATELY NARROWER THAN
"PRECONDITION 3 IS MET."** The wording is chosen so that a freeze document
citing this report cites what was established and not more.

---

**Suite: 1394 passing. Baseline 1378, plus 16 in the new guard.**
