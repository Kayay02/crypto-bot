# Report 08 — Point 3R: Engine Amendment

The engine now implements the Point 1R design as the structural pass resolved it. Two amendments died on measurement, one stood, one specification error was corrected.

---

## 1. File tree, commit, test counts

```
src/engine/
  costs.py            390 lines  MODIFIED  required params, derived floor/geometry, min-qty
  signals.py          325 lines  MODIFIED  session RVOL, RSI removed from entry
  simulate.py         610 lines  MODIFIED  state check, provenance counters, cooldown
  run.py              166 lines  MODIFIED  cfg required, order specs, CLI flags
  contracts.py        238 lines  MODIFIED  OrderSpec probe + cache
  README.md           320 lines  MODIFIED  entry rule, semantics, running
src/analysis/
  structural_pass.py           MODIFIED  re-exports the moved baseline (see §9.1)
config/
  contracts_cache.json         MODIFIED  minimum-order constraints added
docs/handoff/
  06_structural_outcome.md  148 lines  CREATED
docs/prompts/
  08_point_3r.md            269 lines  CREATED
reports/
  08_point_3r.md               this file  CREATED
tests/                                   10 files MODIFIED, 2 golden files added
```

Commit: **`c0cf37e4ba88f70306fce29dd1cd07bd871ba53b`** (`c0cf37e`) — 26 files, +2,261 / −486.

**Tests: 149 passing, 0 failing.** 146 under the default selection, plus 3 look-ahead-marked tests run explicitly (up from 2 — one was added, see §3).

| file | tests |
|---|---|
| `test_signals.py` | 18 (+3 look-ahead) |
| `test_holding_rules.py` | 26 |
| `test_costs.py` | 18 |
| `test_structural_pass.py` | 25 |
| `test_modes.py` | 12 |
| `test_determinism_golden.py` | 11 |
| `test_fixtures_lifecycle.py` | 11 |
| `test_trace_and_prohibitions.py` | 9 |
| `test_portfolio.py` | 6 |
| `test_regression_pinned_trade.py` | 6 |
| `test_manifest_integrity.py` | 4 |

`data/` was not touched. Confirmed by `git status`.

---

## 2. What changed

### Part 2 — Layer A

RVOL's denominator is now the **median of the same 15-minute UTC slot (96 slots/day) over the trailing `baseline_days` completed prior days**, quote-denominated on both sides. The implementation was **moved** from `src/analysis/structural_pass.py` into `src/engine/signals.py` rather than reimplemented, and analysis now re-exports it from the engine — dependency direction analysis → engine, never the reverse, so there is exactly one implementation. Causality is structural: the day/slot matrix is rolled over the day axis then shifted by one **whole day**, so day D reads days [D−N, D−1] only. `min_periods == baseline_days`, so a slot with a gap yields NaN rather than a baseline quietly computed from fewer days. Warm-up is now measured in **days**, not 20 bars, and `signals.warmup_bars()` counts it.

**RSI left the entry logic entirely.** `rsi_wilder` still runs and `rsi` is still recorded on signal rows, but it is not in the entry conjunction and — deliberately — not in the `finite` mask either, so its warm-up NaNs cannot suppress signals. The **cooldown's 20-bar-extreme condition was deleted**; `cooldown_bars` survives as a pure bar count, inert at 0. The entry rule is now exactly: `EMA20 > EMA50 AND close > Donchian-20 upper AND session_rvol >= rvol_threshold`.

### Part 3 — Stop geometry

`stop_atr_mult`, `stop_max_pct`, `rvol_threshold` and `baseline_days` have **no defaults**. They are represented by a `REQUIRED` sentinel that `__post_init__` converts into a `ValueError` naming every missing parameter; `run()` raises if handed no config at all; and the CLI marks all four `required=True`. `stop_min_pct` is now a **method**, not a field — `max(N_cost * c_roundtrip(symbol), risk_usd/(E*L_max))` — so it cannot be set. `stop_geometry()` returns the stop **and** which of `atr`/`floor`/`cap` set it, decided on the raw distance before tick rounding so a rounding artifact cannot mislabel it. Minimum-order rejection is a separate mechanism in separate units (`check_min_qty`, quantity and notional) per the Guard Rail Principle.

### Part 4 — Time stop

`time_stop_bars`, `max_hold_bars` and `threshold_r` are read-only properties derived from `donchian_period`, `tau` and `phi`; passing them raises `TypeError`. The time stop became a **state check**: at the close of the 15m bar `time_stop_bars` after entry, the trade must *be* at or above `threshold_r` net of costs. The intrabar latch is gone. `touched_threshold_intrabar` is recorded so the affected population stays measurable, but no rule reads it. `time_stop_enabled=False` gives the NO_TIME_STOP arm.

---

## 3. Test results — every new fixture

**Session baseline (7 new, `test_signals.py`)**

- `test_rvol_baseline_reads_only_strictly_prior_completed_days` — mutate every bar of day 8; that day's own baseline must not move. **The load-bearing causality test.**
- `test_rvol_baseline_is_not_inert` — mirror: changing prior days *must* move it, so the test above cannot pass trivially.
- `test_rvol_baseline_uses_the_matching_slot_only` — slot 7 reads slot 7 of prior days, nothing else.
- `test_rvol_baseline_uses_median_not_mean` — one 1,000,000× event bar does not move the slot baseline.
- `test_rvol_warmup_produces_no_signals_and_is_counted` — warm-up bars are NaN, produce no signal, and `warmup_bars()` counts them.
- `test_rvol_numerator_and_denominator_use_the_same_field` — matches `session_rvol` on `quote_volume`, and does *not* match the base-volume computation.
- `test_missing_quote_volume_column_raises`.

**RSI removal (4 new)**

- `test_changing_rsi_does_not_change_which_bars_signal` — RSI forced to 5.0 on every bar (which the old 50–75 band rejected outright); the signal set is identical. **The ruling, pinned.**
- `test_rsi_is_still_recorded_as_an_informational_column`.
- `test_rsi_warmup_nans_do_not_suppress_signals`.
- `test_no_entry_condition_references_vwap_position` — tokenises `signals.py` and `simulate.py`, strips comments and docstrings, asserts no `vwap` in executable code.

**Look-ahead (1 new, 2 retargeted)**

- `test_planted_rvol_lookahead_is_caught` — retargeted from the flat mean to a `shift(-1)` day axis.
- `test_same_day_self_reference_is_invisible_to_truncation_but_caught_elsewhere` — **new, and it documents a real limitation.** See §9.4.
- `test_planted_lookahead_bug_is_caught` — unchanged, still catches the Donchian leak.

**Required parameters and derived floor (4 new, `test_costs.py`)**

- `test_derived_floor_matches_hand_arithmetic_for_both_cost_structures` — 1.020% BTC/ETH, 1.320% SOL; cost term > leverage term in all three.
- `test_leverage_term_stays_in_the_formula_even_though_it_never_binds` — at `n_cost=0.5` the leverage term takes over, proving it is live.
- `test_stop_binding_mechanism_is_reported` — atr / floor / cap, both directions.
- Required-parameter raising is verified in `test_holding_rules.py` and directly (§5).

**Derived geometry and the state check (14 new, `test_holding_rules.py`)**

- `test_time_stop_and_max_hold_derive_from_donchian_period` — 20 / 40, and asserts they are *not* 16 / 48.
- `test_tau_scales_the_time_stop_only` — `max_hold` unmoved.
- `test_max_hold_and_time_stop_are_not_independently_settable` — both raise `TypeError`.
- `test_threshold_r_is_derived_from_phi` — solves to exactly 1.0.
- `test_phi_of_1_5_reproduces_the_old_geometry` — `(1/2)/(16/48) = 1.5`, and a `donchian_period=16, phi=1.5` config reproduces threshold 1.5R at bar 16.
- `test_front_loading_is_a_choice_not_a_default`.
- `test_config_rejects_max_hold_not_greater_than_time_stop` — now via `tau >= 2.0`.
- **`test_touch_then_retrace_IS_time_stopped`** — the behavioural change, pinned.
- `test_at_threshold_at_the_checkpoint_close_continues`.
- `test_exactly_at_threshold_at_the_checkpoint_continues` — the `>=` boundary.
- `test_one_tick_below_threshold_at_the_checkpoint_is_time_stopped`.
- `test_checkpoint_decides_on_a_close_and_executes_on_the_next_bar`.
- `test_short_side_state_check_is_symmetric`.
- `test_no_time_stop_arm_disables_the_checkpoint` and `test_no_time_stop_arm_changes_nothing_else` — the latter compares eight fields between arms on a trade that stops out early.

**Signal-mode golden (5 new, `test_determinism_golden.py`)** — hash, shape, gated-arm-is-a-filter, no portfolio constraints applied, and new provenance columns present and typed.

**Deliberately updated existing tests** (reason recorded in each docstring):

| test | why |
|---|---|
| `test_fixture_6_time_stop_when_1R_never_reached` | `reached_1r` → `at_threshold_at_checkpoint`; `bars_held` is now `time_stop_bars + 1` (§9.3) |
| `test_fixture_6b_no_time_stop_once_1R_reached` | renamed `..._when_held_above_threshold`; fixture must now *hold* above threshold, not touch once |
| `test_above_threshold_then_{target,max_hold,stop}` | same latch → state-check reason |
| `test_fixture_7_cooldown_blocks_reentry_until_new_extreme` | extreme rule removed; now asserts it does *not* block, plus a new bar-count test |
| `test_fixture_8_unfundable_trade_is_refused` | a single trade can no longer be unfundable — **a result, not a weakened test** (§9.2) |
| `test_signal_mode_ignores_cooldown` | relied on the extreme rule; now uses `cooldown_bars=100` |
| `test_signal_mode_ignores_margin_cap` | now uses two concurrent symbols |
| `test_stop_distance_floor_and_cap` | floor is derived per symbol, not a flat 1.0% |
| `test_breakout_definition_excludes_rvol_and_rsi` | `rvol_min`/`rsi_long_lo` no longer exist on `SignalParams` |
| `test_pinned_trade_*` | re-pinned; see §6 |

---

## 4. Full trace — the state-check path

A trade that **touches +1R intrabar at minute 1**, drifts back to 100.00, and is **time-stopped at the checkpoint**. Fixture arithmetic: entry 100.00, ATR 2.00, `stop_atr_mult` 1.5, ETHUSDT tick 0.01. Walk minutes 2–313 and 316+ are flat at 100.00 and elided; every decision line is shown.

```
  ENTRY   1m bar ts=1600000900000 close=100 -> fill 100  (entry_slippage_bps=0.0)
  STOP    atr=2 x1.5 = 3  floor 1.0200% (DERIVED: max(6.0 x c_roundtrip 0.1700%, lev 0.3333%)) cap 3.500% of 100 -> stop 97 (3.0000% of entry) [stop_binding_mechanism=atr]
  SIZE    denom = |P-S| 3 + P*f_taker 0.06 + S*f_taker 0.0582 + P*s_entry 0 + S*s_stop 0.0485 = 3.1667
          qty = risk 20.0 / 3.1667 = 6.31572299
  TARGET  solve: (2.0R/q + P*(1+f_taker)) / (1-f_maker) -> 106.42   notional 631.5723
  LEVELS  stop 97 | target 106.42 | tp needs trade-through >= 106.43
          threshold_R = phi 1.0 x target_R 2.0 x 20/40 = 1R
          +1R net 103.29 (gross 1R would be 103) -- the STATE CHECK tests the NET level
  WALK    601 1m bars after the entry minute
          checkpoint CLOSE   1600019740000 (close of 15m bar 20 after entry) -- STATE CHECK
          time-stop execution 1600019800000 (only if BELOW threshold at that close)
          max-hold execution  1600036900000 (bar 40 after entry)
    [  1] ts=1600000960000 h=103.34 l=103.24
    ... minutes 2-313 flat at 100.00, elided ...
    [314] ts=1600019740000 CHECKPOINT close=100 vs threshold 103.29 -> BELOW -> time stop   (touched intrabar earlier: True -- informational, NOT the test)
    [315] ts=1600019800000 TIME STOP: below threshold at the checkpoint close -> exit at 1m close 100
  PNL     gross = q 6.31572299 x (100 - 100) = 0
          fees  = q*P*0.0006 0.378943 + q*X*0.0006 0.378943 = 0.757887
          net   = 0 - 0.757887 = -0.757887   R = -0.0379
```

Reading the three things that matter:

**The `threshold_R` solve.** `phi` 1.0 × `target_R` 2.0 × (20/40) = **1R** — derived, not supplied. The price is then solved net of costs: `X = (net/q + P(1+f_taker)) / (1 − f_taker)` = `(20/6.31572299 + 100×1.0006) / 0.9994` = 103.2836…, rounded **up** to tick → **103.29**. Gross 1R would have been 103.00; the 0.29 gap is the two fee legs, and a trade sitting between 103.00 and 103.29 has not made 1R after costs.

**The checkpoint.** At minute 1 the bar's high was **103.34 ≥ 103.29**, so `touched_threshold_intrabar` is `True` — under the old latch this trade would have survived to `max_hold`. At the checkpoint close (minute 314, the last minute of the 15m bar 20 bars after entry) the price is **100.00 < 103.29**, so the state check fails and the trade is cut. Execution is minute 315, the first minute of the next 15m bar.

**The fee math.** Exit at 100.00 = entry, so gross is exactly 0. Both legs are taker at 6 bps: `6.31572299 × 100 × 0.0006` = 0.378943 each, 0.757887 total. Net −0.757887, i.e. −0.0379R — a trade that made nothing and paid the round trip. This is fixture P&L, known by construction.

---

## 5. Derived values

**`stop_min_pct`, both terms shown.** `c_roundtrip` = entry taker 0.06% + stop taker 0.06% + entry slippage 0.00% + stop-market haircut. Leverage term = `risk_usd / (E × L_max)` = 20 / (2000 × 3.0) = **0.3333%** for every symbol.

| Symbol | haircut | `c_roundtrip` | cost term (×6) | leverage term | **`stop_min_pct`** | binds | ratio |
|---|---|---|---|---|---|---|---|
| BTCUSDT | 5 bps | 0.1700% | **1.0200%** | 0.3333% | **1.0200%** | cost | 3.06× |
| ETHUSDT | 5 bps | 0.1700% | **1.0200%** | 0.3333% | **1.0200%** | cost | 3.06× |
| SOLUSDT | 10 bps | 0.2200% | **1.3200%** | 0.3333% | **1.3200%** | cost | 3.96× |

Computed from config at load time; the literals 1.020 and 1.320 appear nowhere in `src/`. Verified against hand arithmetic by `test_derived_floor_matches_hand_arithmetic_for_both_cost_structures`, and the leverage term is shown to be live by dropping `n_cost` to 0.5.

**Holding geometry**, with `donchian_period` = 20, `tau` = 1.0, `phi` = 1.0, `target_R` = 2:

```
time_stop_bars = tau * donchian_period      = 1.0 * 20  = 20 bars   (was 16, void)
max_hold_bars  = 2 * donchian_period        = 2 * 20    = 40 bars   (was 48, void)
threshold_R    = phi * target_R * (time_stop_bars / max_hold_bars)
               = 1.0 * 2 * (20/40)          = 1.0 R                 (was an input)
max_walk_minutes = max_hold_bars * 15 + 2   = 602 minutes           (derived, not a rule)
```

**Required-parameter enforcement**, verified directly:

```
stop_atr_mult    omitted -> ValueError   OK
stop_max_pct     omitted -> ValueError   OK
rvol_threshold   omitted -> ValueError   OK
baseline_days    omitted -> ValueError   OK
CostConfig()     bare    -> ValueError   OK
run() with cfg=None      -> ValueError   OK
```

---

## 6. Golden files

**Portfolio-mode gated golden — `tests/golden/btc_2023_01_gated.csv`**

| | old | new |
|---|---|---|
| sha256 | `d91622dee0b64ca6118858c0899a37466b59f2d8eab7f0017cad08ac8b2a6049` | `6b79f3a72346c3712b11b9ffdc8a451727a1ee45f33d6c9796d5fd51396e0817` |
| rows | 42 | 54 |
| columns | 28 | 34 |

**What accounts for the delta**, in order of size:

1. **RSI removal (+rows).** `rsi_upper <= 75` was rejecting ~27% of long breakout bars; removing the band admits them. This is the dominant contributor to 42 → 54.
2. **Session-normalised RVOL (± rows).** A different denominator admits and rejects a different set of bars. It also imposes a `baseline_days` warm-up, which *removes* signals from the start of the slice — the golden config uses `baseline_days=5`, so the first 5 days of January produce nothing.
3. **Derived stop floor (all rows).** Every floor-bound trade has a wider stop (1.000% → 1.020% for BTC), hence a smaller `qty`, a different stop-fill price and different P&L. The pinned trade below is one of these.
4. **State-check time stop (some rows).** Trades that touched +1R intrabar and retraced now exit `time_stop` instead of running on; exit timestamps, prices and reasons change.
5. **+6 columns.** `stop_binding_mechanism`, `size_binding_mechanism`, `threshold_r`, `threshold_price`, `at_threshold_at_checkpoint`, `checkpoint_price`, `touched_threshold_intrabar`, minus `reached_1r` which was removed.

The delta is not attributable to a single change and no attempt is made here to decompose it further — doing so would require running per-change variants over real data, which is beyond the smoke test this pass is permitted.

**Signal-mode ungated golden — `tests/golden/btc_2023_01_signal_ungated.csv` (NEW)**

Closes the Point 3 known gap. sha256 `6e17ffd880233dd94b0a3445c77c036f52d873d518e75682de371ccfd50e6b54`, **118 rows**, 34 columns. This is the arm that actually matters: signal mode is the edge-test instrument, and the gated arm is obtained by *filtering* this table, so pinning it pins both arms at once. Four tests guard it (hash, shape, filter-consistency, no portfolio constraints applied).

Both files are regenerated by `python tests/make_golden.py`, which now freezes both.

---

## 7. Minimum order quantity

Probed live from `https://api.bitget.com/api/v2/mix/market/contracts` (`productType=USDT-FUTURES`) and cached in `config/contracts_cache.json` alongside the tick schedule.

| Symbol | `minTradeNum` (min qty) | `minTradeUSDT` (min notional) | `sizeMultiplier` (qty step) |
|---|---|---|---|
| BTCUSDT | 0.0001 | 5 | 0.0001 |
| ETHUSDT | 0.01 | 5 | 0.01 |
| SOLUSDT | 0.1 | 5 | 0.1 |

**Two constraints, not one** — a minimum quantity *and* a minimum notional. `check_min_qty` tests both and returns the specific reason; the trade is refused loudly and counted in `refused_min_qty`.

**How it was verified.** The probe ran through the existing `contracts.py` probe-and-verify path, so rebuilding the cache re-ran the historical tick-grid validation as a side effect: **0 unexpected off-grid prices** across all three symbols, with the 2 known SOL exceptions carried. The tick schedule is byte-identical to before (BTC 0.1, ETH 0.01, SOL 0.0001 → 0.001 at 2024-08-14T04:05:00Z), so the additive change did not disturb it.

**Recorded limitation, and it is the same one the tick has.** Bitget reports the **current** contract state only. Unlike the tick, these values **cannot** be reconstructed for history by grid-validating the derived layer — it holds prices, not order sizes. They are therefore cached as current-state facts, explicitly **not** as a schedule over time, and the cache note says so.

**Practical note:** at ~$2,000 equity with `risk_usd` $20 and stop widths near 1%, position notionals land near $600, far above a $5 minimum. This guard rail is expected never to bind at current account size. It is implemented because A5 requires the rejection to be explicit rather than a silent rounding to zero, and because it must be in place before any smaller-account or wider-stop configuration is tested.

---

## 8. Smoke test

One run, ETHUSDT, June 2023 (`1685577600000` → `1688169600000`), signal mode, ungated, with an **explicitly arbitrary** `stop_atr_mult = 2.5` — labelled as arbitrary in the command and here, and chosen by nothing.

- **Pipeline executed end to end**: load → indicators → signals → simulate → provenance counters → output hash.
- **Bars in slice: 2,881. Warm-up bars: 1,920** (`baseline_days=20`).
- **Signals: 51.**
- **Trades: 51.**
- **Every provenance counter populated**, including all five added or extended at 3R (`refused_min_qty`, `stop_binding_atr`/`_floor`/`_cap`, `size_binding_risk_rule`/`_leverage_cap`/`_min_qty`).

Nothing else is reported from this run and no conclusion is drawn from it. Its only purpose is to prove the pipeline runs.

---

## 9. Ambiguities, deviations and disagreements

**9.1 — DEVIATION: `src/analysis/structural_pass.py` was modified, which the Files section forbade.** The constraint "Do not modify `src/analysis/`" is contradicted by Part 2.1, which instructs moving the session baseline into the engine and states "If you move it, `src/analysis` must import from `src/engine`, never the reverse" — a move necessarily edits both sides. I followed Part 2.1 because it is the more specific instruction and the single-implementation argument is correct. Changes to `structural_pass.py` are confined to: re-exporting `session_baseline`/`session_rvol` from the engine, adding a local `rvol_prior` (the engine no longer implements the *flat* RVOL that M4 measures, and that measurement must stay reproducible), and threading the changed `compute_indicators` signature. **The M1–M9 results are unchanged** — `test_structural_pass.py`'s 25 tests still pass.

**9.2 — RESULT, not a weakened test: a single trade can no longer be refused for margin.** The derived floor's leverage term is `risk_usd/(E·L_max)`, so when it binds, `notional = risk_usd·P/(P·stop_pct + costs) < risk_usd/stop_pct = E·L_max`, strictly. Lowering `max_leverage` now *widens* the floor and *shrinks* the position in exactly the proportion that keeps notional under the cap. Verified at 3.0×, 0.65×, 0.1× and 0.02×: never refused, notional always ≤ cap. The old fixture (a 0.1× cap refusing one ~$630 trade) is unreachable. Margin refusal survives only for **concurrent** positions, which is still tested. This is what A2 said the leverage term was for, now demonstrated rather than asserted.

**9.3 — DEVIATION worth checking: the time stop now exits one bar later than before.** Part 4.3 says the decision is at "the close of 15m bar `time_stop_bars` after entry" with execution "at the close of the first 1m bar of the next 15m bar", which puts the exit at `entry + time_stop_bars + 1` bars and gives `bars_held == time_stop_bars + 1`. The pre-3R code executed at `entry + time_stop_bars` (`bars_held == time_stop_bars`). I implemented the specification as written. Note the resulting asymmetry: the time stop executes at bar `time_stop_bars + 1` while max-hold executes at bar `max_hold_bars` exactly, because 4.1 specifies a hard cap with no decide-then-execute step. Both are defensible — the time stop *is* a decision on a closed bar, the max hold is not — but the asymmetry was not stated in the prompt and is flagged rather than resolved.

**9.4 — FINDING: the truncation-based causality guard structurally cannot catch a same-day self-reference in the slot baseline.** If the day-axis `.shift(1)` were dropped, day D's baseline would include day D itself. `assert_causal` truncates history at bar T and requires an identical answer — but the baseline is indexed by `(day, slot)`, and truncating at bar T leaves bar T's own `(day, slot)` cell intact; the later bars of day T that truncation removes occupy *different slots*. The recomputed answer matches and the guard passes. **`assert_causal` is necessary but not sufficient for a slot baseline.** The dedicated mutation test — rewrite every bar of one day, require that day's own baseline not to move — is what actually catches it. Both are kept, and `test_same_day_self_reference_is_invisible_to_truncation_but_caught_elsewhere` pins the limitation so it cannot be forgotten. This is not a defect in the shipped code (the shift is present and correct); it is a limitation of one guard, now documented.

**9.5 — AGREEMENT, recorded because Part 2.3 invited disagreement: retaining `cooldown_bars` at 0 is right.** It was registered as a sweep dimension before the firewall; at 0 it is behaviourally inert so the baseline is unchanged; and deleting it would make it untestable later without violating D5's ban on adding arms after the firewall lifts. One caveat: `cooldown_bars` is now the *only* thing the cooldown does, so it should be described as a bar-count block rather than as "the cooldown", and the README says so.

**9.6 — AMBIGUITY: `size_binding_mechanism` cannot take all three of its specified values on a taken trade.** Part 3.4 specifies it per trade with values `{risk_rule, leverage_cap, min_qty}`, but `leverage_cap` and `min_qty` cause **refusal**, not resizing — resizing would break the fixed-`risk_usd` invariant, which is not negotiable. So every taken trade records `risk_rule` by construction. I did not resolve this by inventing a clamping path. Instead the refusal counts carry the other two values (`size_binding_leverage_cap`, `size_binding_min_qty` in `summarize()`), so no information is lost, and the column's degeneracy is documented in code and README. Flagged: if the intent was for the engine to *clamp* size at the leverage cap rather than refuse, that is a different design and would need its own decision.

**9.7 — Golden-file config uses `baseline_days=5`, not the fixture default 20.** A one-month golden slice cannot warm up a 20-day baseline and still contain trades. The value is labelled explicitly-arbitrary fixture scaffolding in `conftest.py`. It does mean the golden slice exercises a shorter baseline than a real run would; the determinism guarantee is unaffected.

**9.8 — The pinned regression trade moved, and the reason is fully accounted for.** Its stop is floor-bound, and the floor changed from a hardcoded 1.000% to the derived 1.020%. Same signal bar, same direction, same entry price, same exit reason. All new values were re-derived by hand from the formula (the derivation is in the test docstring) and independently reproduce the engine to 8 significant figures: stop 20949.0 → **20953.1**, qty 0.08230832 → **0.08094108**, stop fill 20959.5 → **20963.6**, and it still reconciles to **−1.0001R**. A new test asserts the floor comes from the formula and is *not* 0.010.

---

## 10. What is not done

- **No parameter was chosen.** `stop_atr_mult`, `stop_max_pct`, `rvol_threshold` and `baseline_days` remain unset by design, and the engine refuses to run without them. Choosing them is Point 4.
- **No sweep, no full backtest, no diagnostics.** Only the Part 7 smoke test ran. No binding rates, exit-reason mixes or holding-time distributions were computed from real data, and the smoke run's diagnostic counters were deliberately not reported.
- **`m*` was not recomputed.** The structural pass reported it for scale only; the operational anchor must be computed per walk-forward training fold at Point 4, never globally.
- **The A3 acceptance check is not run.** Whether recalibrating `stop_atr_mult` brings floor binding under 20% per symbol is a Point 4 measurement, and it is now a harder target: the derived floor (1.020% / 1.320%) is *higher* than the 1.000% that was already binding on 65–81% of trades.
- **The golden delta was not decomposed per rule change.** Attributing rows to individual changes would need per-change runs over real data, beyond what this pass permits.
- **`STRUCTURE_STOP`, `EXTENSION_GUARD` and the partial-runner** remain unimplemented labelled variants.
- **Funding is still not modelled** (D8, logged for Point 6), and a 40-bar hold crosses at least one settlement.
- **Point 3 gaps still open:** Layer B is unoptimised, and the `insufficient_data` path remains fixture-tested only. The signal-mode golden gap is now closed.

---

## 11. Firewall confirmation

No profit, loss, expectancy, win rate, profit factor, Sharpe, return or equity figure was computed, displayed or estimated, and no aggregate was taken of the `net_pnl` or `r_multiple` columns. The only P&L in this report is the §4 fixture trace, where entry and exit are both 100.00 by construction and the arithmetic is hand-checkable. The smoke test reported counts and counter population only.

`vwap_position` is absent from all executable code in `signals.py` and `simulate.py`, enforced by a tokenising test. No entry condition reads RSI, enforced by a behavioural test. `walk_end` does not appear anywhere in `src/engine/`.
