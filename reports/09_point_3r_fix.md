# Report 09 — Point 3R Fix Pass

Two corrections closing Point 3R: exit timing made symmetric, and the threshold-solve discrepancy resolved.

---

## 1. Commit and test counts

Commit: **`b6182b656d61ace01259c38fe448f0c4f2971757`** (`b6182b6`) — 6 files, +205 / −23.

```
src/engine/simulate.py                          MODIFIED  max-hold timing, walk buffer
src/engine/README.md                            MODIFIED  exit convention + pace footnote
tests/test_holding_rules.py                     MODIFIED  2 updated, 9 added
tests/golden/btc_2023_01_signal_ungated.{csv,sha256}  REGENERATED
reports/08_point_3r.md                          MODIFIED  §4 arithmetic correction
```

**Tests: 157 passing, 0 failing** — 154 under the default selection (up from 146: 9 added, 1 net from restructuring) plus 3 look-ahead-marked run explicitly.

`data/` untouched. No parameter was chosen; the engine still refuses to run without all four.

---

## 2. Fix 1 — symmetric exit timing

**What changed.** Max hold now decides on the **close of bar `max_hold_bars`** and executes at the **first 1m close of bar `max_hold_bars + 1`**, matching the time stop and matching entry. Previously it fired at the *start* of bar `max_hold_bars`, so a trade held only `max_hold_bars − 1` complete bars and `max_hold_bars = 40` did not mean 40 bars.

Three edits: `max_hold_deadline` became `max_hold_close_ts` / `max_hold_exec_ts` at `entry + (max_hold_bars+1)·BAR`; `max_walk_minutes` went from `max_hold_bars*15 + 2` to `(max_hold_bars+1)*15 + 2` (602 → 617 at 40 bars) so the buffer still outlasts the last minute any rule can fire; and the trace now prints both the decision close and the execution minute for both exits.

`threshold_R` is unchanged — `phi` is defined on parameters, not realised holds.

**Full trace of a max-hold exit.** Fixture: entry 100.00, ATR 2.00, `stop_atr_mult` 1.5, ETHUSDT tick 0.01, price held at 103.79 (above the 103.29 threshold) for the whole walk. Walk minutes are flat and elided; every decision line is shown.

```
  ENTRY   1m bar ts=1600000900000 close=100 -> fill 100  (entry_slippage_bps=0.0)
  STOP    atr=2 x1.5 = 3  floor 1.0200% (DERIVED: max(6.0 x c_roundtrip 0.1700%, lev 0.3333%)) cap 3.500% of 100 -> stop 97 (3.0000% of entry) [stop_binding_mechanism=atr]
  SIZE    denom = |P-S| 3 + P*f_taker 0.06 + S*f_taker 0.0582 + P*s_entry 0 + S*s_stop 0.0485 = 3.1667
          qty = risk 20.0 / 3.1667 = 6.31572299
  TARGET  solve: (2.0R/q + P*(1+f_taker)) / (1-f_maker) -> 106.42   notional 631.5723
  LEVELS  stop 97 | target 106.42 | tp needs trade-through >= 106.43
          threshold_R = phi 1.0 x target_R 2.0 x 20/40 = 1R
          +1R net 103.29 (gross 1R would be 103) -- the STATE CHECK tests the NET level
  WALK    616 1m bars after the entry minute
          checkpoint CLOSE   1600019740000 (close of 15m bar 20 after entry) -- STATE CHECK
          time-stop execution 1600019800000 (first 1m close of bar 21; only if BELOW threshold at that close)
          max-hold CLOSE     1600037740000 (close of 15m bar 40 after entry)
          max-hold execution  1600037800000 (first 1m close of bar 41)
    ... walk minutes elided ...
    [314] ts=1600019740000 CHECKPOINT close=103.79 vs threshold 103.29 -> AT/ABOVE -> continue   (touched intrabar earlier: True -- informational, NOT the test)
    ... walk minutes elided ...
    [615] ts=1600037800000 MAX HOLD (open at the close of bar 40) -> exit at 1m close 103.79
  PNL     gross = q 6.31572299 x (103.79 - 100) = 23.93659
          fees  = q*P*0.0006 0.378943 + q*X*0.0006 0.393305 = 0.772249
          net   = 23.93659 - 0.772249 = 23.164341   R = 1.1582
```

**The timing, checked against the clock.** `entry_ts` = 1600000900000. Bar `k` after entry spans `[entry_ts + k·900000, entry_ts + (k+1)·900000)`.

- Checkpoint close = `entry_ts + 20·900000 + 900000 − 60000` = **1600019740000** — the last minute of bar 20. Price 103.79 ≥ 103.29, so the trade continues.
- Max-hold close = `entry_ts + 40·900000 + 900000 − 60000` = **1600037740000** — the last minute of bar 40. The trade is still open.
- Max-hold execution = `entry_ts + 41·900000` = **1600037800000**, exactly one minute after that close, and the first minute of bar 41.
- `bars_held = (1600037800000 − 1600000900000) / 900000` = **41 = `max_hold_bars` + 1**. ✓

Walk index 615 = minute 615 = `41 × 15`, and `max_walk_minutes` is 617, so the buffer covers it with two minutes of slack. Fixture P&L only; entry and exit prices are set by construction.

---

## 3. Fix 2 — the threshold solve

**The code was correct. The report prose was wrong.**

Evaluating the documented formula at full precision:

```
q                       = 6.315722992389554
threshold_R * risk_usd  = 1.0 * 20 = 20
net/q                   = 3.1667                (exactly the sizing denominator)
P * (1 + f_taker)       = 100 * 1.0006 = 100.05999999999999
sum                     = 103.2267
/ (1 - f_taker)         = 103.2267 / 0.9994
                        = 103.28867320392236
```

`costs.solve_r_level(100.0, q, "long", cfg, 0.01)` returns **103.29**, and the unrounded intermediate inside `solve_price_for_net` is **103.28867320392236** — identical to the formula, bit for bit. There is no code path that differs from the documentation.

So: **`103.2836` in `reports/08_point_3r.md` §4 was a transcription error in the prose.** The digits `86` and `67` were transposed and a digit dropped. Nothing operational differed — at ETHUSDT's 0.01 tick both values round up to 103.29, which is why no fixture, test or golden file caught it. I have corrected §4 in report 08 and marked the correction inline rather than silently rewriting it.

**A note on the prompt's working:** the prompt gives `103.28887`. That is also slightly off — `103.2267 / 0.9994 = 103.288673…`, not `103.28887`. The prompt's conclusion (that `103.2836` is wrong) is right; its replacement value is not the exact one. The engine's value stands.

**The new test.** `test_threshold_solve_matches_hand_arithmetic_at_a_coarse_tick` pins the solve where rounding cannot conceal an error of this class.

The error was `(103.288673 − 103.2836) / 103.288673` ≈ **4.7 × 10⁻⁵** relative. At a ~100 price with a 0.01 tick that is half a tick, invisible after rounding. The test therefore uses **BTCUSDT scale: entry 20000.0, tick 0.1**, where the same relative error is ~0.95 in absolute terms — about **10 ticks**, and impossible to hide. The test asserts three things: the engine matches hand arithmetic exactly; a value perturbed by 4.7 × 10⁻⁵ would land more than 5 ticks away (so the fixture is provably sensitive enough to catch the error class it exists for); and the returned level really does deliver `threshold_R` net of both taker legs. A companion test covers the short side at the same tick.

---

## 4. Regression — the pinned trade

**Unaffected, as required.**

| field | value |
|---|---|
| `exit_reason` | `stop` |
| `stop_binding_mechanism` | `floor` |
| `stop_price` | 20953.1 |
| `qty` | 0.08094108 |
| `exit_price` | 20963.6 |
| **`r_multiple`** | **−1.0001204** |

All six `test_regression_pinned_trade.py` tests pass unchanged. It still reconciles to **−1.0001R**.

**One correction to the prompt's description:** the prompt says the pinned trade "exits by stop at bar 9". It exits **9 minutes** after entry — `entry_ts` 1673882100000, `exit_ts` 1673882640000, a 540,000 ms gap — which is **within the entry 15m bar**, so `bars_held = 0`, not 9. The substantive point is unchanged and stronger than stated: the trade exits inside its first bar, twenty bars before the checkpoint could fire, so no exit-timing change can reach it.

---

## 5. Golden files

| file | old sha256 | new sha256 | rows |
|---|---|---|---|
| `btc_2023_01_gated.csv` | `6b79f3a72346c37…396e0817` | **`6b79f3a72346c37…396e0817`** (unchanged) | 54 → 54 |
| `btc_2023_01_signal_ungated.csv` | `6e17ffd880233dd…cfd50e6b54` | **`75a6c6a6ae6cfab…e590d8665adc`** | 118 → 118 |

**The portfolio-mode gated golden did not move at all** — byte-identical files, confirmed by `diff`. No trade in that slice exits by max hold, so the change could not reach it. That is itself a useful check: a timing fix that touched trades exiting by stop or target would have been a bug.

**Delta attribution for the signal-mode golden: exactly 2 rows of 118, both attributable to the bar-count change alone.** Every other row is identical across all 34 columns.

| signal bar | dir | old | new | what happened |
|---|---|---|---|---|
| 1673604000000 | long | `max_hold`, bars_held 40 | **`target`**, bars_held 40 | Previously cut at the *start* of bar 40. Now it lives through bar 40 and trades through its target 2 minutes later. |
| 1674247500000 | long | `max_hold`, bars_held 40 | `max_hold`, **bars_held 41** | Exit moved exactly one 15m bar later (`exit_ts` +900,000 ms). |

The second row is the direct mechanical effect. The first is the expected knock-on: giving a trade one more bar lets it resolve, and this one resolved at target. Both rows had `at_threshold_at_checkpoint = True` before and after, so the checkpoint decision was untouched — only what happens after it. No row changed entry, stop, target, `qty`, `stop_binding_mechanism` or the checkpoint fields.

I did not aggregate anything over the changed rows.

---

## 6. Tests changed

**Updated (2), each with the reason in its docstring:**

| test | old expectation | new | reason |
|---|---|---|---|
| `test_at_threshold_at_the_checkpoint_close_continues` | `bars_held == max_hold_bars` | `== max_hold_bars + 1` | Max hold now decides on a closed bar and fills on the next. |
| `test_above_threshold_then_max_hold_cap` | `bars_held == max_hold_bars`, `exit_ts == ENTRY + 40·BAR` | `+ 1`, `ENTRY + 41·BAR` | Same. |

**Tightened (1):** `test_walk_buffer_is_derived_and_outlasts_max_hold` asserted `max_walk_minutes > (max_hold_bars+1)*15 − 15`, which was slack enough to pass even if the buffer expired before max hold could fire. It now asserts `> (max_hold_bars+1)*15`.

**Added (9):**

- `test_time_stop_holds_time_stop_bars_plus_one`
- `test_max_hold_holds_max_hold_bars_plus_one`
- `test_both_exits_use_the_same_decide_then_execute_convention` — checks both exits land exactly one minute past the close of their decision bar, not at it
- `test_walk_buffer_still_covers_the_max_hold_execution_minute` — across `donchian_period` ∈ {10, 20, 48}
- `test_exhausting_the_buffer_is_still_insufficient_data_not_walk_end`
- `test_realised_pace_ratio_differs_from_the_parameter_ratio` — pins 20/40 = 0.500 against 21/41 ≈ 0.512 and asserts `threshold_R` does not move
- `test_threshold_solve_matches_hand_arithmetic_at_a_coarse_tick`
- `test_threshold_solve_short_side_at_a_coarse_tick`
- (plus the tightened buffer test above, counted once)

---

## 7. Ambiguities and disagreements

**7.1 — The prompt's replacement value for the threshold solve is itself slightly off.** It gives `103.28887`; the exact value is `103.288673…`. The prompt's *diagnosis* is correct — the report's `103.2836` was wrong — but I pinned the test to the engine's exact value, verified against the formula at full precision, rather than to the prompt's figure. Flagging rather than silently adopting either number.

**7.2 — The pinned trade does not exit "at bar 9".** It exits at *minute* 9, inside the entry bar, `bars_held = 0`. See §4. The verification requirement is satisfied either way; the description was inaccurate.

**7.3 — `bars_held` now counts the execution bar, which slightly overstates exposure.** `bars_held = (exit_ts − entry_ts) / 900000` = 41 for a max-hold trade, but the position is only *exposed* through bar 40's close plus one minute of bar 41. The name has meant "bars between entry and exit fills" since Point 3 and I have not redefined it, but at Point 4 the holding-time distribution (D6) will be denominated in this quantity, and it is worth deciding then whether the reported figure should be the exposure count (40) or the fill-to-fill count (41). Not resolved here — it is a reporting convention, not a rule.

**7.4 — The realised pace ratio is now 21/41, not 20/40, and `phi` no longer describes realised behaviour exactly.** The prompt instructed recording this as a footnote and stated that nothing derives from the realised ratio, which is true of the current code. Recorded in the README and pinned by a test. Stating the residual anyway: D4's argument for `phi` is about the *shape of the price journey against the time budget*, and the realised budget is now 41 bars while the realised checkpoint is at 21. The 2.4% discrepancy is far too small to matter against a sweep band, but `phi = 1.0` now means "linear pace in parameter space" rather than "linear pace in realised time". Flagged, not resolved.

**7.5 — The time-stop side needed no code change.** It already decided on the close of bar `time_stop_bars` and executed at the first minute of bar `time_stop_bars + 1`; §9.3 of report 08 flagged the *asymmetry*, and the fix was entirely on the max-hold side. Noting this because the prompt's framing ("make the timing symmetric") could suggest both moved.

---

## 8. What is not done

- **No parameter was chosen.** `stop_atr_mult`, `stop_max_pct`, `rvol_threshold` and `baseline_days` remain without defaults; `CostConfig()` and `run(cfg=None)` still raise.
- **No sweep, no backtest, no real-data run.** The golden files were regenerated (required, and they run over a frozen one-month slice) but no diagnostic was computed from them beyond the row-level delta attribution in §5.
- **`bars_held` semantics were not redefined** — see §7.3, deferred to Point 4's holding-time reporting.
- **The §9.6 `size_binding_mechanism` degeneracy is unchanged.** Taken trades still always record `risk_rule`; refusal counters carry the other two values. Clamping remains rejected because it would break `risk_usd` commensurability, per the constraint.
- Everything listed under §10 of report 08 remains open: `STRUCTURE_STOP`, `EXTENSION_GUARD` and the partial-runner are unimplemented; funding is unmodelled; `m*` is still to be computed per walk-forward fold at Point 4; the A3 floor-binding acceptance check has not been run.

---

## 9. Firewall confirmation

No profit, loss, expectancy, win rate, profit factor, Sharpe, return or equity figure was computed, displayed or estimated, and no aggregate was taken of the `net_pnl` or `r_multiple` columns. The P&L in §2 is a hand-checkable fixture whose prices are set by construction; §4 quotes the single pinned trade's `r_multiple` as a regression invariant, as it has been since Point 3; §5 reports which rows changed and how, not what they earned.
