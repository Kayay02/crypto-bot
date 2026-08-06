# Report 09 — Point 4.1 Regime Characterisation

Causal, per-symbol, rolling regime measurement over 15m OHLCV, with a causality guard tested against its own target mutation.

Commit: **`d9d8f97109b1eeec2bab73c40e563f1f309a1fa5`** (`d9d8f97`).

**Firewall intact.** This module reads OHLCV and writes regime labels. It does not import `simulate`, and a tokenising test bans `net_pnl`, `r_multiple`, `trade_pnl`, `expectancy`, `pnl` and `win_rate` from executable code in every file. No trade outcome was read, computed or printed.

**Holdout sealed.** Nothing at or after 2025-01-01 was loaded. Truncation happens in the loader before any indicator runs, and a test asserts `max(ts) < 2025-01-01` for all three symbols.

---

## 1. File tree

```
src/regime/
  __init__.py     22 lines   purpose, firewall statement, the three things labels feed
  measure.py     395 lines   axes, covariates, causality guard, parquet output
  labels.py      305 lines   tercile fit/freeze/apply, concordance, build driver
tests/
  test_regime_measure.py     502 lines   37 tests — fixtures with known answers
  test_regime_causality.py   284 lines   13 tests — mutation tests, truncation, firewall

data/derived/regime/          (gitignored, per repo convention — see §8.3)
  BTCUSDT.parquet   105,216 rows   3,220,624 bytes   zstd:3
  ETHUSDT.parquet   105,216 rows   3,270,194 bytes   zstd:3
  SOLUSDT.parquet   105,216 rows   3,344,057 bytes   zstd:3
  terciles.json     frozen cuts + fit window + git commit
  _manifest.json    git commit, config, row counts, per-column NaN counts
```

Nothing outside `src/regime/` and `tests/` was modified.

---

## 2. Test results

**50 new tests, all passing. Full repo suite: 207 passing** (204 default selection + 3 look-ahead-marked run explicitly), up from 157.

| file | tests |
|---|---|
| `test_regime_measure.py` | 37 |
| `test_regime_causality.py` | 13 |

### The mutation test — confirmed to fail as intended

The requirement was to prove the guard can detect the bug it exists to catch, rather than assume it. `_ROLL` and `_LAG` — the two places window alignment lives — are indirected through module-level hooks so a test can rebind exactly that and nothing else.

**Three distinct mutations are planted. Each must be caught, so a guard that catches one by luck cannot pass the file.**

| mutation | what it does | guard |
|---|---|---|
| `_roll_ahead_one` | rolling window right edge slips from T to **T+1** | **RAISES** ✓ |
| `_lag_ahead_one` | lag reaches **forward** one bar, reading `close[T+1]` | **RAISES** ✓ |
| refit terciles on all data | full-sample quantile instead of the frozen window | **RAISES** ✓ (different cuts; and the unbounded call is rejected outright) |

Demonstrated directly, outside pytest:

```
unmutated guard  : PASSES (checked 6 bars)
MUTATED guard    : RAISED  -> look-ahead: m_star at bar index 450 (ts 1641400200000)
                              is 1.0735110183550427 on full history but nan when
                              truncated at that bar
```

The unmutated case is asserted to pass *inside the same test* before the mutation is applied. Without that, a guard broken in some other way would make the mutation test pass for the wrong reason.

### Non-vacuity, addressed directly

The brief warned that a generic `assert_causal` passes vacuously here — the RVOL slot baseline is indexed by `(day, slot)`, so truncating at bar T leaves bar T's own cell intact and a dropped day-shift recomputes identically. Four things defend against repeating that:

1. **The guard checks arbitrary bars, not only bars carrying values.** Checking only non-NaN rows is the vacuity mode: a leak that turns rows into NaN leaves nothing to compare. `test_guard_is_not_vacuous_because_it_checks_arbitrary_bars` asserts NaN rows are genuinely in the sampled range.
2. **The guard refuses a history too short to test** rather than passing on zero comparisons.
3. **Truncation invariance is checked over every bar of a prefix**, at three window lengths, not just at sampled points.
4. **The guard's blind spot is documented and pinned, not assumed away.** `test_guard_catches_a_shortened_lag` plants a lag that is off by one *backward*. That reads no future bar, so truncation cannot see it — and the test asserts the guard does **not** fire, then asserts the values genuinely move. What stands between that bug and the output is the exact-value fixture set (ramp = 1.0, zigzag = 0.0), not the causality guard. Recording where the guard stops working seemed more useful than implying it covers everything.

---

## 3. Observed ranges, 2022-01-01 → 2024-12-31

### m\* per symbol (30-day window)

| symbol | min | median | max |
|---|---|---|---|
| BTCUSDT | 1.759 | 3.236 | 8.576 |
| ETHUSDT | 1.250 | 2.713 | 7.325 |
| SOLUSDT | 1.163 | 2.019 | 3.738 |

The ordering matches expectation from the derived floors and each symbol's volatility: BTC is most squeezed against its cost floor, SOL least. M8 measured m\* at 1.71–4.08 on per-symbol-year medians; the rolling 30-day view is wider (1.16–8.58) because a 30-day median tracks volatility regimes that a yearly median averages away. That is the axis having real variance, which is what it is for.

### Efficiency ratio per symbol (30-day window)

| symbol | min | median | max |
|---|---|---|---|
| BTCUSDT | 0.0000 | 0.0209 | 0.1123 |
| ETHUSDT | 0.0000 | 0.0193 | 0.0938 |
| SOLUSDT | 0.0000 | 0.0196 | 0.0967 |

**These values are much smaller than an efficiency ratio usually looks, and the reason is structural rather than a bug — see §8.1.** Over a 2,880-bar window a random walk accumulates net displacement of order √N against N total movement, so the ratio floors near `√(2/πN)` ≈ 0.0149. The observed medians (0.019–0.021) sit about 1.3× that floor, i.e. these markets are modestly more directional than a random walk. The axis still discriminates — the max is 5× the median — but "high efficiency" here means 0.03, not 0.6.

### Fitted tercile cuts (frozen, fit window 2022-01-01 → 2025-01-01 exclusive)

| symbol | axis | low ≤ | high > | n fitted |
|---|---|---|---|---|
| BTCUSDT | m\_star | 2.84405 | 3.66869 | 102,242 |
| ETHUSDT | m\_star | 2.26727 | 3.01855 | 102,242 |
| SOLUSDT | m\_star | 1.81192 | 2.24182 | 102,242 |
| BTCUSDT | efficiency\_ratio | 0.01305 | 0.03020 | 102,242 |
| ETHUSDT | efficiency\_ratio | 0.01200 | 0.02880 | 102,242 |
| SOLUSDT | efficiency\_ratio | 0.01376 | 0.02706 | 102,242 |

Cuts are per symbol, never pooled. Applied to the fit window they split 0.333/0.333/0.333 on every symbol-axis, confirming the fit is correct — that balance is trivially expected here and is **not** evidence about later data (§8.2).

---

## 4. m\* < 1.0 structural marker

**Zero windows, all three symbols, at the primary 30-day window** — 0 of 102,242 per symbol. This is the expected result: m\* = 1.0 is where median volatility would exactly reach the cost floor, and M8 predicted it is never crossed.

**But it is crossed at the 14-day sensitivity window, and that is a finding.**

| symbol | 14d | 30d | 60d |
|---|---|---|---|
| BTCUSDT | 0 | 0 | 0 |
| ETHUSDT | **737** | 0 | 0 |
| SOLUSDT | **2,131** | 0 | 0 |

ETH's crossings fall in a single week (2022-06-20 → 2022-06-27, min m\* 0.898); SOL's span 2022-05-17 → 2022-11-22 (min 0.908). Both are the high-volatility stretch of the 2022 drawdown, where a 14-day median ATR% briefly exceeds the cost floor.

The marker is therefore **window-dependent**, and "expected to be false everywhere" holds at 30 and 60 days but not at 14. Worth recording because the spec describes a crossing in the holdout as "notable in itself" — if a future crossing is reported, the window it was measured at has to be stated alongside it, or the claim is ambiguous.

---

## 5. Cross-symbol concordance, 2022-2024

Fraction of bars on which **all three** symbols carry the same label. 102,242 labelled bars; 2,974 warm-up bars excluded from both numerator and denominator (counting an unlabelled bar as a disagreement would understate concordance for a reason unrelated to the market).

| axis | concordance | agreeing bars |
|---|---|---|
| **m\_star** | **0.4544** | 46,459 / 102,242 |
| **efficiency\_ratio** | **0.3096** | 31,654 / 102,242 |

Most common cells:

- m\_star: `high|high|high` 19,322 · `low|low|low` 18,422 · `low|low|mid` 9,276 · `mid|mid|mid` 8,715
- efficiency: `high|high|high` 15,564 · `low|low|low` 10,835 · `low|mid|low` 6,916 · `low|low|mid` 6,177

**Reading this against the two-of-three rule.** Under independence, three symbols each uniformly split into terciles would agree by chance about 1/9 ≈ 11% of the time. Observed concordance is **4.1× chance on m\*** and **2.8× chance on efficiency**. So the three symbols are clearly *not* independent — but they are also not the degenerate case 4.4 warned about, where all three sit in the same cell 90% of the time and "three symbols agree" collapses to one observation repeated.

The honest summary: on roughly 45% of bars the three symbols are in the same volatility-vs-cost regime, and on roughly 31% the same efficiency regime. Two-of-three is therefore weaker evidence than three independent observations would be, and stronger than one. This is descriptive input to interpretation only; per 4.4 it moderates how the rule's result is read and does not change the rule.

Efficiency concordance being lower than m\* concordance is the more interesting half: volatility regimes are substantially market-wide, but *directional efficiency* is more symbol-specific. Since the trend-continuation thesis lives on the efficiency axis, the axis that matters most for the edge claim is also the one where the three symbols are most nearly independent.

---

## 6. Row and NaN counts

| symbol | rows | valid | NaN (all measured columns) |
|---|---|---|---|
| BTCUSDT | 105,216 | 102,242 | 2,974 |
| ETHUSDT | 105,216 | 102,242 | 2,974 |
| SOLUSDT | 105,216 | 102,242 | 2,974 |

All three cover 2022-01-01 00:00 → 2024-12-31 23:45 UTC on a complete 15m grid.

**Warm-up is 2,974 bars, not 2,880.** The five measured columns do not become computable at the same bar, so a single boundary is imposed at the largest requirement and every column is masked before it — a row is either a complete regime observation or entirely NaN. See §8.4.

Exact-zero efficiency values, which are legitimate (a window returning exactly to its start) rather than NaN in disguise: BTC 5, ETH 0, SOL 1. Smallest non-zero values are ~2–7 × 10⁻⁷, so the zeros are genuinely distinct from "very small".

---

## 7. Sensitivity — 14 and 60 day windows

| symbol | window | valid rows | m\* min / med / max | ER min / med / max |
|---|---|---|---|---|
| BTCUSDT | 14 | 103,778 | 1.206 / 3.224 / 10.263 | 0.0000 / 0.0267 / 0.2195 |
| BTCUSDT | 30 | 102,242 | 1.759 / 3.236 / 8.576 | 0.0000 / 0.0209 / 0.1123 |
| BTCUSDT | 60 | 99,362 | 1.936 / 3.264 / 6.754 | 0.0000 / 0.0170 / 0.0710 |
| ETHUSDT | 14 | 103,778 | 0.898 / 2.688 / 9.251 | 0.0000 / 0.0295 / 0.1832 |
| ETHUSDT | 30 | 102,242 | 1.250 / 2.713 / 7.325 | 0.0000 / 0.0193 / 0.0938 |
| ETHUSDT | 60 | 99,362 | 1.345 / 2.764 / 6.171 | 0.0000 / 0.0157 / 0.0555 |
| SOLUSDT | 14 | 103,778 | 0.908 / 2.023 / 4.234 | 0.0000 / 0.0259 / 0.1567 |
| SOLUSDT | 30 | 102,242 | 1.163 / 2.019 / 3.738 | 0.0000 / 0.0196 / 0.0967 |
| SOLUSDT | 60 | 99,362 | 1.226 / 2.048 / 3.327 | 0.0000 / 0.0121 / 0.0785 |

**The m\* median is remarkably stable across windows** (BTC 3.224 → 3.236 → 3.264) while the range contracts as the window lengthens — exactly what averaging more data should do. The axis's central tendency is not a window artifact.

**The efficiency median moves with window length** (0.027 → 0.021 → 0.017 for BTC), tracking the √N random-walk floor (0.0218 → 0.0149 → 0.0105). This is the compression effect of §8.1 and is the reason the tercile cuts are not transferable between window lengths. Only 30-day cuts are frozen; measuring at 14 or 60 requires its own fit, and the artifact keys cuts by window length so the two cannot be confused.

---

## 8. Judgment calls where the specification was ambiguous

**8.1 — "Kaufman efficiency ratio" over 2,880 bars is dominated by the √N floor.** The formula was specified exactly and I implemented it exactly. But the resulting values live in 0.00–0.11 rather than the 0–1 range the "bounded 0-1" description suggests, because net displacement grows as √N while total path length grows as N. This is not a defect and I did not "fix" it — rescaling would break the exact fixture answers (ramp = 1.0, zigzag = 0.0) that make the implementation verifiable. It does mean **the axis is a relative discriminator, not an absolute one**: a "high efficiency" 30-day window means ER > 0.030, which is a mild trend, not a strong one. Anyone reading a post-lift stratification as "the strategy works in efficient markets" should know that "efficient" here means "the top third of a distribution whose median is 1.3× a random walk". Flagged, not resolved.

**8.2 — the fit window and the available data are currently identical, so the frozen-cuts machinery is untested against real drift.** The prompt specifies fitting on 2022-01-01 → 2024-12-31 and also forbids computing anything for 2025–26. Those two instructions together mean the fit set equals the application set: terciles split 0.333/0.333/0.333 by construction, and the "later data will be unbalanced" property has nothing to act on yet. The freeze/apply path is exercised only by fixtures (`test_frozen_cuts_on_a_shifted_distribution_produce_expected_imbalance`). This is correct and intended, but the balanced-thirds result in §3 should not be mistaken for evidence that the cuts generalise. It is arithmetic, not a finding.

**8.3 — the frozen tercile artifact is not under version control.** `/data/` is gitignored repo-wide, so `terciles.json` lives only on disk. A pre-registration artifact that can be deleted and silently refitted is weakly frozen: `freeze_terciles` refuses to overwrite a *different* fit window, but only while the file exists. The recorded git commit inside the JSON helps, and I did not change `.gitignore` because that is outside the permitted file scope. **Recommendation: force-add `data/derived/regime/terciles.json` to git.** It is ~1 KB and it is the artifact whose whole value is provability.

**8.4 — a single warm-up boundary was imposed rather than per-column boundaries.** The five columns become computable at different bars: `ema_fraction` at n−1, `efficiency` and `drift` at n, `m_star` at n+13 (ATR(14) warm-up nested inside the median window), `median_daily_quote_volume` at n+94 (the 24-hour sum nested inside the median window). Per-column NaN would satisfy the letter of "bars before a full window emit NaN" but would produce **partial rows**, and partial rows invite downstream code to filter on whichever column happens to be populated. I masked all columns at the largest boundary: **2,974 bars at 30 days, not 2,880.** The cost is ~94 bars of `ema_fraction` and ~1 day of other columns discarded per symbol. Flagged because it makes the reported warm-up larger than the window and that would otherwise look like a bug.

**8.5 — "median daily quote volume" implemented as a rolling 24-hour sum, not calendar-day totals.** The spec says "median daily quote volume over the window". Calendar-day totals would require either a day-boundary aggregation (introducing an artifact at UTC midnight and a partial current day) or excluding the current day (introducing a shift the other axes do not have). I compute the median over the window of the trailing 24-hour quote-volume sum, which is per-bar, causal, has no calendar artifact, and coincides with calendar-day totals when sampled at day boundaries. Flagged as a judgment call; the alternative is defensible and would give slightly different numbers.

**8.6 — fit window start.** The prompt says fit on 2022-01-01 → 2024-12-31; spec §4.2 says in-sample is 2022-04-01 → 2024-12-31 because Q1 2022 is warm-up and never traded. I followed the prompt. In practice the regime warm-up consumes to ~2022-01-31 anyway, so the difference is February and March 2022 — about 5,760 bars of a 102,242-bar fit, i.e. 5.6%. Flagged because if regime labels are ever compared against fold results, the label distribution includes two months the strategy never trades.

---

## 9. Where I believe the specification is wrong

**9.1 — the pre-registration is not committed, which is the one thing 4.5 says must be true.** The prompt states the spec is "frozen and committed at `docs/handoff/08_point_4_pre_registration.md`" and refers to "amendment 1 in the git log". Neither is true in this repo:

- The file is **untracked**, at the path `docs/handoff/08_point_4_pre_registration(3).md` — a `(3)` suffix suggesting a re-downloaded copy, with a `(2)` open in the editor.
- There is **no amendment commit** in `git log`. Appendix A exists inside the document, but as uncommitted text.

§4.5 is unambiguous: *"PRECONDITION: 4.1–4.5 written, agreed, and COMMITTED TO GIT. Not 'agreed in chat' — committed, with a hash. A design frozen in a commit that provably predates the results is the difference between pre-registration and a claim of pre-registration."* Build ordering step 1 is "Commit the frozen 4.1–4.5 design"; this task is step 2.

Step 2 has now been done before step 1. Nothing is contaminated — no performance figure was touched and regime labels are not results — but **there is currently no hash proving the design predates the regime output**, and the artifacts record it: both `terciles.json` and `_manifest.json` carry a `-dirty` commit hash, and the *only* thing making the tree dirty is the uncommitted pre-registration. I did not commit it myself: choosing which copy is the canonical pre-registration, and under what filename, is a provenance decision that belongs to you. **This should be resolved before Point 4.3/4.4 execute.**

**9.2 — Appendix A removed m\*'s external anchor but the axis keeps its "derived-over-free" justification, and that justification is now doing less work than it reads as doing.** Appendix A is candid that the axis "loses its external-anchor zero-leak property — the specific reason m\* was preferred over raw ATR%". What remains is that m\* is a committed derived quantity and is dimensionless across symbols. But with frozen in-sample terciles, **raw ATR% would have exactly the same two properties**: it is also already-committed, and per-symbol terciles are also dimensionless in the sense that matters. The genuine remaining advantage of m\* over ATR% is narrower than "derived over free" implies — it is that m\* is expressed in units of the thing that mechanically breaks the strategy, so a label maps directly onto the failure mode. That is a real advantage and I would keep the axis; I think the stated justification overstates it. Not a defect that changes anything here.

**9.3 — "expected to be false everywhere" for m\* < 1.0 is stated without its window.** As §4 shows, it is true at 30 and 60 days and false at 14. The spec treats the marker as window-independent. Minor, but a holdout crossing reported without its window would be uninterpretable.

---

## 10. What is not done

- **No labels for 2025–26.** The holdout is sealed and requires separate authorisation. `load_15m` defaults to truncating at 2025-01-01 and a test enforces it.
- **Only the 30-day window is persisted.** 14 and 60 day output is produced on demand by the same function for sensitivity reporting (§7); their terciles are not frozen, and the artifact keys cuts by window length so they cannot be silently mixed.
- **No fold-level concordance.** §4.1 asks for concordance "per fold"; folds are defined in 4.2 and are not implemented yet. `concordance()` takes an explicit date range, so per-fold aggregation is a caller-side loop once fold boundaries exist. The whole-period figures are in §5.
- **Nothing was computed that touches trade outcomes.** E6, the sweep, and everything else in the nine-step sequence remain untouched; the lift has not happened.
