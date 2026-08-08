# REPORT 13 — THE 1m HOLDOUT SEAL AND THE BOUNDARY-CROSSING EXCLUSION

Implements Appendix M.2 (seal the engine's 1m path) and M.3 (exclude
boundary-crossing trades). Both land before the sweep, as M.2 requires.

The holdout remains SEALED. Nothing in this change reads a bar at or after
2025-01-01, and an AST scan across `src/` and `tests/` asserts that no call site
passes a literal `authorised=True`.

## 0. Headline

1. **The seal is closed and proven.** The mutation test fires in both
   directions: with the exclusion disabled the seal raises; with it restored
   the seal is silent and the excluded count is positive.
2. **Every E6 figure reproduces byte-identically.** All sigmas, all trade
   counts, min/max, the trigger verdict, the power table, the shortfall list
   and the 425-bar overlap are unchanged to full float precision.
3. **BUT report 12's "zero boundary crossings" claim was too strong, and
   Appendix M.2/M.3 restate it wrongly.** Five trades did cross. They were in
   the ungated universe only, never reached the 50% arm, and so influenced no
   reported figure — but they were simulated using 2025 1m bars. §4 sets this
   out; §7.1 records it as a specification error.

## 1. What was built

| Layer | Mechanism | Fires when |
|---|---|---|
| **Exclusion (M.3)** | `simulate.crosses_holdout` in `run_backtest`, before any 1m access | a signal's maximum walk reaches the boundary — counted, never raised |
| **Backstop A (M.2)** | `simulate.require_in_sample_window`, per trade, at point of use | the exclusion did not run — **raises** |
| **Backstop B (M.2)** | `simulate.load_1m(..., authorised=False)` | a sealed partition is requested — **raises** |
| **Clamp** | `simulate.in_sample_years` in `run.py` and `dispersion.py` | always — removes 2025+ from the `max(year)+1` convention |

`HoldoutSealError` subclasses `PermissionError`, matching `src/folds/`. It
raises and never degrades: falling back to partial data would turn a bug into a
silently wrong number.

### 1.1 Why the ordering is the point

Exclusion is decided by arithmetic on `entry_ts` alone and needs no data, so it
runs strictly before any 1m bar is requested. That is what makes the seal
*provable*: because exclusion runs first, a refusal is unambiguous evidence of a
bug. Had exclusion run only after the loader complained, refusals would be
routine and would carry no information.

### 1.2 Why the loader check alone is NOT sufficient

M.2 asks for a refusal in the 1m loader. That is necessary but does not close
the gap on its own, and this is the one place the specification is incomplete.

Once the sealed years are simply not loaded, a boundary-crossing trade triggers
no refusal at all. It runs off the end of the available records and exits
`insufficient_data` — a fabricated outcome, silently included in the population.
The loader is never asked for anything, so it never objects.

Only a check on the **requirement**, evaluated per trade, converts that into a
raise. Hence Backstop A. The mutation test in §3 exercises exactly this path,
with the sealed years already absent.

## 2. Excluded count per fold per symbol

Computed from signal-bar arithmetic across all 54 fold-symbol-period cells.
**Every cell not listed is zero.**

| symbol | fold | period | ungated signals | excluded (ungated) | gated 50% signals | excluded (50% arm) |
|---|---|---|---|---|---|---|
| SOLUSDT | 9 | test | 678 | **5** | 322 | **0** |
| all other 53 cells | — | — | — | 0 | — | 0 |
| **total** | | | | **5** | | **0** |

Only fold 9's test period ends on 2024-12-31, so it is the only cell that can
touch the boundary. The engine's own counter agrees: `refused.holdout_boundary`
totalled 5 across the full re-run.

## 3. The mutation test, both directions

M.2 requires a mutation test proving the seal refuses. A backstop never shown to
fire proves nothing.

| Direction | Configuration | Expected | Result |
|---|---|---|---|
| **1 — mutated** | `exclude_holdout_crossing=False` | seal RAISES | ✅ `HoldoutSealError` raised |
| **2 — restored** | `exclude_holdout_crossing=True` | seal SILENT, count > 0 | ✅ no raise, `holdout_boundary == 1` |

Run three ways, in `tests/test_holdout_seal.py`:

- `test_MUTATION_disabling_exclusion_makes_the_backstop_FIRE`
- `test_MUTATION_restoring_exclusion_makes_the_backstop_SILENT`
- `test_MUTATION_on_real_fold_9_data_both_directions` — the same pair against
  fold 9's real test signals plus a constructed crossing bar, so the mutation is
  provable whether or not that fold happens to signal in the final hours. The
  restored direction additionally asserts `max(signal_bar_ts) < 2025-01-01`.

Two further ordering guards:

- `test_excluded_trades_never_reach_the_1m_path` passes an **empty** 1m record
  array. If exclusion ran after the walk was sliced, the trade would land in
  `no_1m_coverage`; it lands in `holdout_boundary`, which proves the ordering.
- `test_the_authorisation_scanner_has_teeth` plants `authorised=True` and
  `authorised_1m=True` and requires the AST scan to catch both, while allowing
  `authorised=authorised` — the forwarding pattern `src/folds/warmup.py` already
  uses to propagate its own `False` default.

## 4. E6 reproduction — figure by figure

E6 was re-run under the new seal and diffed against the committed artifact from
the lift run. **`reports/12_e6_dispersion.md` was deliberately NOT overwritten:**
it is the record of the lift taken at hash `a30b97b`, and rewriting it would make
it claim a hash at which the firewall had already been lifted.

| Figure | Report 12 | Re-run | Verdict |
|---|---|---|---|
| BTCUSDT sigma / n / min / max | 0.7241551747 / 6318 / -1.0004656052 / 2.0004132229 | identical | ✅ |
| ETHUSDT sigma / n / min / max | 0.7666345581 / 6236 / -1.0006398611 / 2.0006516210 | identical | ✅ |
| SOLUSDT sigma / n / min / max | 0.8467221332 / 7456 / -1.0005235154 / 2.0004255900 | identical | ✅ |
| Pooled all symbols, n / sigma | 20010 / 0.7849904450 | identical | ✅ |
| Trigger fires / firing cells | False / 0 of 27 | identical | ✅ |
| Evidence-minimum shortfalls | 0 | identical | ✅ |
| Per-fold, per-direction, per-period sigma and n (all cells) | — | identical | ✅ |
| Power table, every row | — | identical | ✅ |
| Configuration, all 27 fold-symbols | — | identical | ✅ |
| Bounds check / Appendix L excursion | — | identical | ✅ |
| 425-bar overlap, all counts | — | identical | ✅ |
| **`n_ungated` SOLUSDT fold 9 test** | **678** | **673** | ⚠️ **MOVED by 5** |

A recursive diff over the whole statistics tree found 56 differences: 55 are the
intended new counter keys, and **one is a moved figure** — the line above.

### 4.1 What the moved counter means

`n_ungated` is the size of the ungated universe simulated before the 50% RVOL
filter is applied. It is a provenance counter in the artifact and in the run
log; **it is not printed anywhere in report 12**, so no figure in that report
changed. But it is in the committed `e6_dispersion.json`, so the record does
change, and it is recorded here rather than quietly regenerated.

Five SOL fold-9 signals crossed the boundary. In the lift run they were
simulated using 2025 1m bars, produced trades, and were then discarded by the
RVOL gate. Under the new seal they are excluded before any 1m access.

**Every E6 conclusion is untouched**, because every E6 figure is computed on the
gated 50% arm, which those five never entered.

## 5. The conservatism note (step 1)

The exclusion tests the **maximum possible** walk, not the actual exit.

| Quantity | Value |
|---|---|
| `max_hold_bars` | 40 |
| Realised hold | 41 bars (decide on close of 40, execute on first minute of 41) |
| `max_walk_minutes` | 617 |
| Walk span from entry | 36,960,000 ms = 10.2667 h |
| Earliest excluded entry bar | 2024-12-31 13:44:00Z |
| Earliest excluded signal bar | 2024-12-31 13:30:00Z |
| 15m signal bars excluded on 2024-12-31 | 42 per symbol per direction |

So roughly the final ten and a quarter hours of the in-sample window are
excluded, and most of those trades would in fact have exited well before
midnight. That over-exclusion is deliberate and is the whole point: deciding on
the ACTUAL exit bar would require resolving the trade, which needs the data the
seal forbids. Excluding on the maximum uses no future information; the
alternative uses exactly the information being protected.

The bound is anchored on `max_walk_minutes` (617), the buffer actually sliced,
rather than on the max-hold execution bar (615 minutes). Two minutes wider, so
the figure is the true data requirement rather than the expected exit.

## 6. Verification

| Item | Result |
|---|---|
| a) Mutation test, both directions | ✅ §3 — raises when disabled, silent with count 5 when restored |
| b) E6 reproduction | ⚠️ all figures identical; one provenance counter moved — §4 |
| c) Default 1m path refuses 2025+; no test authorises | ✅ `years=None` and any sealed year both raise; AST scan clean over 30+ files |
| d) Full suite | ✅ **411 passed** (was 392; 19 new) |

Engine semantics are otherwise unchanged: away from the boundary the exclusion
is inert, asserted by `test_exclusion_is_inert_away_from_the_boundary`, which
runs the same signal with the flag on and off and requires an identical
`r_multiple`.

The boundary constant is duplicated into the engine, because the engine
deliberately has no dependency on `src/`. `test_engine_holdout_constant_matches_the_folds_definition`
asserts it equals `src.folds.schedule.HOLDOUT_TEST_START`, so the duplication
cannot drift.

## 7. Where I believe the specification is wrong

### 7.1 "ZERO trades crossed the boundary" is false as written

Appendix M.2 states: *"ZERO trades crossed the boundary, so no holdout bar
influenced any figure in report 12."* M.3 states: *"It affected zero trades in
E6."* Report 12 §10.2 item 5 says *"0 trades cross the boundary."*

**Five trades crossed.** The error is mine, and it came from the counter I used:
report 12's `exit_after_is_end` was computed on the **gated** trade table, which
is the only table E6 retains. The ungated universe — which signal mode actually
simulates — contained five crossing SOL fold-9 trades, and those were resolved
using 2025 1m bars.

The narrower claim survives intact: **no holdout bar influenced any reported
figure**, because every E6 figure comes from the gated arm and none of the five
reached it. No conclusion moves. But "zero trades crossed" and "no holdout bar
was read" are different statements, and only the first was ever checked.

This strengthens rather than weakens M.2's case for the seal: the gap was not
merely structural, it was already being exercised.

**Recommended, not done here:** M.2 and M.3 should be corrected to say that five
ungated trades crossed and that no gated trade did. I have not edited the frozen
document without being asked. Appendix M is itself a post-lift record, so
correcting a factual error in it is not an amendment of anything pre-registered.

### 7.2 The loader-level refusal is necessary but not sufficient

M.2 asks only for `authorised=False` on the 1m loader. As argued in §1.2, that
alone leaves boundary-crossing trades exiting `insufficient_data` in silence. I
added the per-trade point-of-use backstop as well. Both are implemented; the
mutation test exercises the second, because the first cannot fire once the
sealed years are simply never requested.

## 8. Judgment calls

**1. The exclusion runs on the UNGATED universe.** Signal mode simulates ungated
and filters to the arm afterwards, so exclusion sits in `run_backtest` and
removes crossing signals before simulation. This keeps §4.5's guarantee that
every arm is the identical trade universe by construction — excluding after
gating would give the arms different universes at the boundary. It is also why
the excluded count is 5 on the ungated universe and 0 on the 50% arm; §2 reports
both rather than only the arm figure, which is what misled report 12.

**2. The `max(year) + 1` convention is clamped, not removed.** It is correct at
every year boundary except the sealed one. `in_sample_years` removes only the
sealed years, so trades crossing 2022/23 and 2023/24 still resolve normally.

**3. The exclusion defaults to ON** (`exclude_holdout_crossing=True`) rather than
being required at every call site. A seal that must be remembered is not a seal.
The parameter exists so the mutation test can turn it off.

**4. `load_1m(years=None)` now refuses.** Previously it loaded every partition on
disk, which includes 2025 and 2026. The lazy call must not be the unsealed one,
so the default path refuses rather than quietly loading the holdout. No
production caller passes `years=None`.

**5. Report 12 and its artifact were left unmodified.** They record the lift as
it happened. The one moved counter is documented here instead. Regenerating them
would erase the evidence for §7.1.

## 9. Provenance

- **Commit:** `fc4cfc96f91700f9101a2713c7cd8294bd3ad5fa`
- **Parent:** `3ac9f0f` (Appendix M rebuilt)
- **Working tree at commit:** clean
- **Test suite:** 411 passed
- **E6 reproduction baseline:** `data/derived/analysis/e6_dispersion.json` from the lift run at `a30b97b`
