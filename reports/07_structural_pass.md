# Report 07 — Structural Measurement Pass (1R Pre-Checks)

Measurements only. Nothing here decides anything: each result is reported against the numeric threshold fixed in Section 13 of `docs/handoff/05_point_1r.md` **before** this pass was run, and the verdict is whatever that pre-committed threshold implies.

---

## 1. Files, commit, tests

```
src/analysis/
  __init__.py                     10 lines   CREATED
  structural_pass.py             670 lines   CREATED
tests/
  test_structural_pass.py        386 lines   CREATED   25 tests
docs/prompts/
  07_structural_pass.md          198 lines   CREATED
docs/handoff/
  05_point_1r.md                 512 lines   MODIFIED  (C1-C3 only, +28/-10)
reports/
  07_structural_pass.md          426 lines   CREATED   this file
  07_structural_pass_raw.json  5,790 lines   CREATED   machine-readable results
```

Commit hash is recorded in §9.

**Tests: 115 passed, 0 failed.** 113 under the default selection (88 pre-existing + 25 new), plus 2 look-ahead-marked tests that `pytest.ini` deselects by default (`addopts = -m "not lookahead"`) and which were run explicitly. No pre-existing test was modified.

Nothing under `src/engine/`, `config/` or `data/` was touched. The engine still implements the pre-1R design, deliberately.

## 2. Manifest integrity

Checked before any bar was read, same contract as `tests/test_manifest_integrity.py`.

```
ok:            True
git_commit:    1648707990665...  (recorded at derived-layer build)
outputs:       26 files, all row counts match
raw_sources:   13 files, all sha256 match
row_drift:     []
hash_drift:    []
```

## 3. Window and warm-up

All measurements are restricted to **2022-01-01T00:00:00Z → 2023-12-31T23:45:00Z**. Truncation happens in `load_window()` at the parquet boundary, before any indicator is computed, so no rolling window and no session baseline can reach a bar outside it. 70,080 bars per symbol — a complete 15m grid for two years with no gaps.

**The derived layer starts exactly at 2022-01-01, so no pre-window warm-up data exists.** Warm-up is therefore consumed inside 2022:

- Engine indicators (EMA50 / Donchian-20 / RSI-14 / ATR-14) — first ~50 bars of 2022 yield NaN and produce no breakout bar.
- M5 session baseline — the first `baseline_days` days of 2022 yield NaN. At `baseline_days = 30` that is the whole of January 2022. **2022 M5 figures are computed on a slightly shorter year than 2023 figures.** 2023 is unaffected: it warms up from 2022.

No bar from 2024, 2025 or 2026 was read, loaded or aggregated. Verified by test (`test_load_window_reads_no_bar_outside_2022_2023`).

---

## 4. DECISION TABLE

This is the deliverable. Verdicts are mechanical consequences of the Section 13 thresholds, not judgements.

### M1 — B3 validity (`bar_vwap` inside `[low − 1 tick, high + 1 tick]`) — threshold ≥ 99.99%

| Symbol | Year | Fraction inside | Violations | Verdict |
|---|---|---|---|---|
| BTCUSDT | 2022 | **100.0000%** | 0 / 35,040 | **PASS** |
| BTCUSDT | 2023 | **100.0000%** | 0 / 35,040 | **PASS** |
| ETHUSDT | 2022 | **100.0000%** | 0 / 35,040 | **PASS** |
| ETHUSDT | 2023 | **100.0000%** | 0 / 35,040 | **PASS** |
| SOLUSDT | 2022 | **100.0000%** | 0 / 35,040 | **PASS** |
| SOLUSDT | 2023 | **100.0000%** | 0 / 35,040 | **PASS** |

Not one violation in 210,240 bars, and not one bar with zero volume or a missing vwap. Bitget's `quote_volume` is internally consistent with its own OHLC. **B3 and B2 both survive this check outright.**

### M2 — B3 non-redundancy (`rho(vwap_position, close_position)` on breakout bars) — KILL ≥ 0.90 / AMBER 0.70–0.90 / PASS < 0.70

| Symbol | Year | rho (pooled) | rho (long) | rho (short) | n | Verdict |
|---|---|---|---|---|---|---|
| BTCUSDT | 2022 | 0.578 | 0.073 | 0.101 | 1,867 | **PASS** |
| BTCUSDT | 2023 | 0.465 | 0.040 | 0.171 | 1,696 | **PASS** |
| ETHUSDT | 2022 | 0.531 | 0.001 | 0.052 | 2,037 | **PASS** |
| ETHUSDT | 2023 | 0.347 | 0.072 | 0.031 | 1,658 | **PASS** |
| SOLUSDT | 2022 | 0.434 | 0.052 | −0.093 | 2,448 | **PASS** |
| SOLUSDT | 2023 | 0.614 | 0.076 | 0.182 | 2,005 | **PASS** |

PASS on the pooled figure, and **PASS decisively on the directional one**. See §5.2 — the pooled correlation is almost entirely a direction artifact.

### M3 — B3 dispersion (IQR of `vwap_position` on breakout bars) — threshold IQR ≥ 0.15

| Symbol | Year | IQR (pooled) | Verdict (pooled) | IQR long (`vp`) | IQR short (`1−vp`) | Verdict (directional) |
|---|---|---|---|---|---|---|
| BTCUSDT | 2022 | 0.1329 | **FAIL** | 0.0900 | 0.0888 | **FAIL** |
| BTCUSDT | 2023 | 0.1239 | **FAIL** | 0.0913 | 0.0979 | **FAIL** |
| ETHUSDT | 2022 | 0.1517 | PASS | 0.1112 | 0.1080 | **FAIL** |
| ETHUSDT | 2023 | 0.1341 | **FAIL** | 0.1070 | 0.1083 | **FAIL** |
| SOLUSDT | 2022 | 0.1530 | PASS | 0.1260 | 0.1118 | **FAIL** |
| SOLUSDT | 2023 | 0.1572 | PASS | 0.1082 | 0.1084 | **FAIL** |

**Pooled: 3 PASS / 3 FAIL. Directional: 6 FAIL / 6.** The two readings disagree about whether B3 lives, and Section 13 does not say which population it meant. **Flagged in §7.1, not resolved here.**

The second dispersion condition — "a threshold exists rejecting 25–75% of breakout bars" — is satisfied in all six cells, as anticipated. It is near-vacuous: for any continuous distribution the median rejects ~50% by construction. **The IQR is the operative test.** The distribution is *not* atomic — 1,651–2,439 distinct values per cell out of 1,658–2,448 bars, i.e. essentially every bar has its own value. So the low IQR is genuine concentration, not discretisation.

### M4 — B5 selectivity ratio (flat RVOL ≥ 1.5) — ≥ 2.0 pre-spent / ≤ 1.3 never selective

| Symbol | Year | Pass, all bars | Pass, breakout bars | Ratio | Verdict |
|---|---|---|---|---|---|
| BTCUSDT | 2022 | 15.93% | 78.95% | **4.95** | **SELECTIVE BUT PRE-SPENT** |
| BTCUSDT | 2023 | 13.33% | 75.41% | **5.66** | **SELECTIVE BUT PRE-SPENT** |
| ETHUSDT | 2022 | 16.88% | 73.54% | **4.36** | **SELECTIVE BUT PRE-SPENT** |
| ETHUSDT | 2023 | 11.36% | 67.79% | **5.97** | **SELECTIVE BUT PRE-SPENT** |
| SOLUSDT | 2022 | 16.71% | 60.17% | **3.60** | **SELECTIVE BUT PRE-SPENT** |
| SOLUSDT | 2023 | 17.78% | 78.35% | **4.41** | **SELECTIVE BUT PRE-SPENT** |

Unanimous, and not close to the boundary. The all-bars denominator — never measured before this pass — settles it: RVOL ≥ 1.5 is a strong discriminator in the population at large (it admits ~11–18% of all bars), and admits ~60–79% of breakout bars. **Its selectivity is real and was spent before the gate ran**, exactly the reading B5 pre-registered as one of its two alternatives. The "RVOL was never selective" branch is refuted.

### M6 — B2 denomination stability — more stable must win ≥ 2 of 3 symbols across both years

| Symbol | Year | Within-window CV, base | Within-window CV, quote | Global CV, base | Global CV, quote | Winner |
|---|---|---|---|---|---|---|
| BTCUSDT | 2022 | 0.513975 | **0.513600** | 0.5512 | **0.5441** | quote |
| BTCUSDT | 2023 | 0.478914 | **0.478798** | 0.6093 | **0.5687** | quote |
| ETHUSDT | 2022 | 0.615590 | **0.615234** | 1.0125 | **0.8318** | quote |
| ETHUSDT | 2023 | 0.414391 | **0.414280** | 0.5145 | **0.4913** | quote |
| SOLUSDT | 2022 | 0.524271 | **0.523328** | 3.7335 | **1.4925** | quote |
| SOLUSDT | 2023 | **0.650427** | 0.650510 | 1.2522 | **1.0157** | quote (global) / base (within, by 8e-5) |

**Verdict: `quote_volume` wins 3 of 3 symbols across both years. B2's default stands.**

Both statistics agree, but they are not equally informative:

- **Within-window CV** (median of `rolling_std(20)/rolling_mean(20)`, the local statistic — the one that matters, since RVOL is always computed locally) shows the two denominations as **effectively identical**, differing in the fourth-to-fifth decimal. Over 20 bars the price barely moves, so `quote ≈ price × base` and the CV is nearly invariant to the scaling. SOL 2023 flips to base by 0.00008, which is noise, not a result.
- **Global CV** (std/mean of the baseline series across the year) separates them clearly, and always in quote's favour — most dramatically SOL 2022, where base CV is 3.73 against quote's 1.49. This is the drift statistic B2's justification appeals to.

Honest reading: **the decision rule is satisfied, but the margin it is satisfied by is almost entirely the global statistic, and the local statistic — the one describing what the gate actually computes — shows near-indifference.** B2 is upheld on the rule as written; it is not upheld by a large local effect.

### M7 — F2 `rsi_lower` rejection rate on breakout bars — < 5% drops now / ≥ 5% retained

| Symbol | Year | Breakout bars | Rejected | Rejection rate | Verdict |
|---|---|---|---|---|---|
| BTCUSDT | 2022 | 1,867 | **0** | **0.00%** | **DECORATIVE — DROPS NOW** |
| BTCUSDT | 2023 | 1,696 | **0** | **0.00%** | **DECORATIVE — DROPS NOW** |
| ETHUSDT | 2022 | 2,037 | **0** | **0.00%** | **DECORATIVE — DROPS NOW** |
| ETHUSDT | 2023 | 1,658 | **0** | **0.00%** | **DECORATIVE — DROPS NOW** |
| SOLUSDT | 2022 | 2,448 | **0** | **0.00%** | **DECORATIVE — DROPS NOW** |
| SOLUSDT | 2023 | 2,005 | **0** | **0.00%** | **DECORATIVE — DROPS NOW** |

**Zero rejections in 11,711 breakout bars.** Unanimous and unambiguous — `rsi_lower` drops now, before the build, without consuming an attribution arm.

### Summary

| Check | Verdict | Unanimous? |
|---|---|---|
| M1 B3 validity | **PASS** | yes, 6/6, zero violations |
| M2 B3 non-redundancy | **PASS** | yes, 6/6, both poolings |
| M3 B3 dispersion | **FAIL directionally (6/6); pooled 3/3 split** | **no — see §7.1** |
| M4 B5 selectivity | **Selective but pre-spent** | yes, 6/6 |
| M6 B2 denomination | **quote_volume retained** | yes, 3/3 symbols |
| M7 F2 `rsi_lower` | **Drops now — decorative** | yes, 6/6, exactly zero |

---

## 5. Full detail

### 5.1 M1 — validity

`bar_vwap = quote_volume / volume`, tested against `[low − tick, high + tick]` with the tick looked up per bar timestamp from `config/contracts_cache.json` (BTC 0.1, ETH 0.01, SOL 0.0001 throughout the window — SOL's 0.001 segment begins in 2024 and is outside it).

No violations at any magnitude, so there is no "worst violation" table to print. There were also **0 degenerate bars** (`high == low`) and **0 zero-volume bars** across all 210,240 bars, so the explicit branches written for both are exercised only by the unit tests, not by the real data. They remain necessary: their absence over two years is not a guarantee about 2024–26, and the code must not produce a NaN if one appears.

This is the cleanest result in the pass. The tolerance did no work — zero bars landed in the one-tick margin either.

### 5.2 M2 — non-redundancy, and why the pooled figure misleads

The pooled correlation (0.35–0.61) and the within-direction correlation (−0.09 to 0.18) differ by a factor of roughly five. The pooled number is **an artifact of mixing directions**:

- On long breakout bars, price closes near the high, so `close_position` is high; the bar's volume-weighted average price also sits toward the high, so `vwap_position` is high.
- On short breakout bars, both are low.

Pooling the two populations produces a correlation that measures nothing but "which direction is this bar", not any shared information between the two terms. **Within a direction, `vwap_position` is essentially uncorrelated with `close_position`.**

That is a stronger result for B3 than the pre-check required. B3's stated purpose — that location of volume within the bar is orthogonal to price action within the bar — is confirmed, and by a wide margin. `vwap_position` is genuinely not a relabelled price-action term.

The tension with M3 is the interesting part: **`vwap_position` carries information that `close_position` does not, but it carries very little of it in absolute terms.** Orthogonal, and nearly constant.

### 5.3 M3 — dispersion

Distribution of `vwap_position` on breakout bars, pooled across directions:

| Symbol | Year | d1 | q1 | median | q3 | d9 | IQR | ≤ 0.05 | ≥ 0.95 | distinct values |
|---|---|---|---|---|---|---|---|---|---|---|
| BTCUSDT | 2022 | 0.402 | 0.442 | 0.490 | 0.575 | 0.618 | 0.133 | 0.0% | 0.0% | 1,861 / 1,867 |
| BTCUSDT | 2023 | 0.406 | 0.452 | 0.517 | 0.576 | 0.622 | 0.124 | 0.0% | 0.0% | 1,691 / 1,696 |
| ETHUSDT | 2022 | 0.391 | 0.433 | 0.494 | 0.585 | 0.629 | 0.152 | 0.0% | 0.0% | 2,034 / 2,037 |
| ETHUSDT | 2023 | 0.398 | 0.442 | 0.507 | 0.576 | 0.622 | 0.134 | 0.0% | 0.0% | 1,651 / 1,658 |
| SOLUSDT | 2022 | 0.383 | 0.430 | 0.490 | 0.583 | 0.633 | 0.153 | 0.0% | 0.0% | 2,439 / 2,448 |
| SOLUSDT | 2023 | 0.386 | 0.434 | 0.504 | 0.591 | 0.638 | 0.157 | 0.0% | 0.0% | 1,997 / 2,005 |

Directionally — the population a threshold actually sees, since longs test `vwap_position` and shorts test `1 − vwap_position`:

| Symbol | Year | median (long) | IQR (long) | median (short, `1−vp`) | IQR (short) |
|---|---|---|---|---|---|
| BTCUSDT | 2022 | 0.557 | 0.0900 | 0.566 | 0.0888 |
| BTCUSDT | 2023 | 0.554 | 0.0913 | 0.547 | 0.0979 |
| ETHUSDT | 2022 | 0.563 | 0.1112 | 0.570 | 0.1080 |
| ETHUSDT | 2023 | 0.545 | 0.1070 | 0.543 | 0.1083 |
| SOLUSDT | 2022 | 0.555 | 0.1260 | 0.563 | 0.1118 |
| SOLUSDT | 2023 | 0.571 | 0.1082 | 0.581 | 0.1084 |

Two observations, both structural:

1. **The gated term's median is ~0.55–0.58 in every cell, for both directions.** On a breakout bar, the volume-weighted average price sits slightly toward the breakout direction. That is a real and consistent asymmetry — but it is small, and it is present on essentially every breakout bar rather than distinguishing between them.
2. **Splitting by direction removes about a quarter of the pooled IQR** (0.124–0.157 → 0.089–0.126). The pooled dispersion was partly the same direction-mixing effect that inflated the M2 correlation.

The distribution is continuous, not atomic: >99.5% of bars carry a distinct value, and no bar in any cell sits at either extreme (`≤ 0.05` or `≥ 0.95` are both exactly 0.0% everywhere). So the concentration is a genuine property of the quantity, not an artifact of rounding or of a degenerate-bar pile-up.

### 5.4 M4 — flat RVOL selectivity

Detail in the decision table above. One reconciliation note: Finding 3 in Section 2 records RVOL ≥ 1.5 admitting **65.9% (2022) and 68.8% (2023)** of breakout bars. This pass measures 60.2–79.0% per symbol-year, which pools to roughly 70.6% (2022) and 74.0% (2023) — **close to, but not equal to, the recorded figures.** Flagged in §7.4.

### 5.5 M5 — session-normalised RVOL characterisation

Characterisation only. **No `baseline_days` value is recommended and no threshold is chosen** — both are Point 4 sweep decisions.

Why the equivalent-threshold construction is necessary: the threshold 1.5 was calibrated against a flat 20-bar mean. Changing the denominator changes the whole distribution, so 1.5 no longer denotes the same selectivity. Comparing "flat at 1.5" against "session at 1.5" would compare two different degrees of strictness and attribute the difference to the baseline. The equivalent-pass-rate threshold holds selectivity fixed so that any remaining difference is attributable to the baseline itself.

**Equivalent threshold and selectivity ratio at matched pass rate:**

| Symbol | Year | flat pass (breakout) | `bd`=5 thr / ratio | `bd`=10 | `bd`=20 | `bd`=30 | flat ratio (M4) |
|---|---|---|---|---|---|---|---|
| BTCUSDT | 2022 | 0.790 | 1.515 / 3.09 | 1.571 / 3.50 | 1.609 / 3.60 | 1.607 / 3.58 | **4.95** |
| BTCUSDT | 2023 | 0.754 | 1.426 / 2.86 | 1.420 / 2.94 | 1.448 / 2.98 | 1.431 / 2.90 | **5.66** |
| ETHUSDT | 2022 | 0.735 | 1.695 / 3.20 | 1.746 / 3.44 | 1.840 / 3.49 | 1.925 / 3.54 | **4.36** |
| ETHUSDT | 2023 | 0.678 | 1.515 / 3.35 | 1.541 / 3.71 | 1.519 / 3.54 | 1.502 / 3.47 | **5.97** |
| SOLUSDT | 2022 | 0.602 | 1.627 / 2.32 | 1.660 / 2.42 | 1.730 / 2.39 | 1.747 / 2.31 | **3.60** |
| SOLUSDT | 2023 | 0.784 | 1.299 / 2.20 | 1.302 / 2.27 | 1.247 / 2.16 | 1.212 / 2.06 | **4.41** |

Three things this establishes about the parameter surface:

1. **At matched selectivity, session-normalised RVOL is LESS selective than flat RVOL — in all 24 cells.** Ratios of 2.06–3.71 against flat's 3.60–5.97. This is the opposite of what B1's motivation would lead one to expect, and it is uniform: there is no symbol, year or `baseline_days` where session-normalisation buys more discrimination between breakout bars and the bar population at large.
2. **`baseline_days` barely matters.** Across 5 → 30 the ratio moves by less than 0.5 in every symbol-year, non-monotonically. The parameter surface is close to flat in this direction. That is useful to know before a sweep spends resolution on it.
3. **The equivalent thresholds cluster at 1.21–1.93**, i.e. near 1.5. Under the new denominator, the existing threshold value happens to denote roughly the same strictness. Coincidence, but it means a like-for-like comparison at Point 4 does not require a wildly different number.

**Pass rate by UTC hour, breakout bars, flat vs session (`bd`=20), spread across the 24 hours:**

| Symbol | Year | flat spread (min → max) | session spread (min → max) | compressed? |
|---|---|---|---|---|
| BTCUSDT | 2022 | 0.485 (0.47 → 0.95) | 0.255 (0.68 → 0.93) | yes |
| BTCUSDT | 2023 | 0.336 (0.53 → 0.86) | 0.282 (0.61 → 0.89) | yes |
| ETHUSDT | 2022 | 0.470 (0.44 → 0.91) | 0.349 (0.54 → 0.89) | yes |
| ETHUSDT | 2023 | 0.510 (0.34 → 0.85) | 0.343 (0.48 → 0.83) | yes |
| SOLUSDT | 2022 | 0.324 (0.43 → 0.76) | 0.403 (0.41 → 0.81) | **no** |
| SOLUSDT | 2023 | 0.368 (0.55 → 0.91) | 0.281 (0.64 → 0.92) | yes |

**B1's diagnosis is confirmed.** Under the flat baseline the gate's pass rate on breakout bars varies by 32–51 percentage points depending purely on the hour of the UTC day — the gate substantially measures what time it is, exactly as B1 argued. Session-normalisation compresses that spread in 5 of 6 cells, in one case by half. SOL 2022 is the exception and widens.

So the two M5 findings point in opposite directions, and both are real: **session-normalisation does what B1 said it would do to the time-of-day artifact, and it costs selectivity to do it.** Whether that trade is worth making is a Point 4 decision and is not made here.

### 5.6 M6 — denomination stability

Detail and the honest reading are in the decision table above. Statistic definitions, stated because the choice is load-bearing:

- **`within_window_cv`** = median over the year of `rolling_std(20).shift(1) / rolling_mean(20).shift(1)` — the coefficient of variation of the *same trailing 20 bars that form the RVOL denominator*, at the moment it is used. Chosen as the operative statistic because RVOL is computed locally: what matters is how noisy the denominator is where it is applied, not how it drifts over a year.
- **`global_cv`** = `std / mean` of the trailing-baseline series across the whole year. This captures drift across the window, which is the bias B2's justification actually appeals to, and for `quote_volume` it necessarily inherits the year's price trajectory.

Both are shifted by one bar, matching the engine's `rvol_prior`, so neither reads the bar it describes.

### 5.7 M7 — `rsi_lower`

Zero rejections. Independently verified rather than taken from the aggregate, because a rate of exactly 0.00% across six cells is the kind of result that is usually a bug:

| Symbol | min RSI on long breakout bars | 1st pctile | max RSI on short breakout bars | 99th pctile |
|---|---|---|---|---|
| BTCUSDT | 54.18 | 58.15 | 45.75 | 41.15 |
| ETHUSDT | 54.56 | 58.68 | 44.81 | 41.19 |
| SOLUSDT | 55.73 | 58.88 | 44.41 | 41.17 |

The **minimum** RSI on any long breakout bar in two years is 54.18 — more than four points clear of the 50 threshold, on the wrong side of it for rejection. The bound has never come close to binding.

Section 7 of the handoff argued this was "not strict entailment — Wilder smoothing has memory beyond 14 bars — but narrow." **Over 2022–23 it is entailment in practice.** A bar that closes above a 20-bar high with EMA20 > EMA50 has, without exception, had gains dominate losses over the prior 14 bars.

There is consequently **no rejected population to characterise** — the ATR% / `close_position` / `vwap_position` profile of rejected bars is empty, and the 1R.5 "reversal breakout" hypothesis is **untestable on this window** rather than confirmed or refuted. If reversal breakouts exist, the RSI lower bound is not what separates them. Flagged in §7.3.

Incidental, and it does not reopen a closed decision: the already-removed `rsi_upper` was rejecting **514–569 long breakout bars per symbol (~27%)** and 443–490 short (~26%). F3 removed it on principle, before this was measured; the measurement quantifies what that removal returns to the population.

### 5.8 M8 — derived stop floor and ATR scale

`stop_min_pct = max( N_cost × c_roundtrip , risk_usd / (E × L_max) )`, with `N_cost = 6`, `risk_usd = 20`, `E = 2000`, `L_max = 3.0`.

Leverage term = `20 / (2000 × 3.0)` = **0.3333%**, identical for all symbols.

Two cost variants are reported because the prompt and the engine disagree about where the haircut applies — see §7.5:

| Variant | Symbol | `c_roundtrip` | cost term (×6) | leverage term | **`stop_min_pct`** | dominant | cost ÷ leverage |
|---|---|---|---|---|---|---|---|
| engine as implemented | BTC / ETH | 0.170% | 1.020% | 0.333% | **1.020%** | cost | 3.06× |
| engine as implemented | SOL | 0.220% | 1.320% | 0.333% | **1.320%** | cost | 3.96× |
| haircut both sides | BTC / ETH | 0.220% | 1.320% | 0.333% | **1.320%** | cost | 3.96× |
| haircut both sides | SOL | 0.320% | 1.920% | 0.333% | **1.920%** | cost | 5.76× |

**The cost term dominates in every variant and every symbol**, by 3.06–5.76×. A2's claim that the floor is fundamentally a cost guard rail holds, and its "roughly 3x" estimate is right at the low end of the measured range. The leverage term is nowhere near load-bearing — consistent with A2's stated reason for keeping it in the formula anyway.

**ATR(14) as a percentage of close, on breakout bars:**

| Symbol | Year | d1 | median | d9 | `m*` (engine variant) | `m*` (both-sides variant) |
|---|---|---|---|---|---|---|
| BTCUSDT | 2022 | 0.212% | 0.426% | 0.823% | **2.39** | 3.10 |
| BTCUSDT | 2023 | 0.109% | 0.250% | 0.501% | **4.08** | 5.28 |
| ETHUSDT | 2022 | 0.314% | 0.579% | 1.024% | **1.76** | 2.28 |
| ETHUSDT | 2023 | 0.145% | 0.301% | 0.536% | **3.39** | 4.39 |
| SOLUSDT | 2022 | 0.452% | 0.773% | 1.381% | **1.71** | 2.48 |
| SOLUSDT | 2023 | 0.326% | 0.625% | 1.204% | **2.11** | 3.07 |

> **`m*` IS REPORTED HERE FOR SCALE ONLY.** Section 3 / A6 requires the operational `m*` to be computed **per walk-forward training fold** at Point 4, never globally and never over the full window, because a globally computed anchor would read the 2025–26 holdout and leak it. The figures above are computed over 2022–23 only and are a sense of magnitude for designing the sweep. **They must never be used as the operational anchor.**

This is the clearest corroboration in the pass of Finding 2. The current engine runs `stop_atr_mult = 1.5` against a 1.0% floor. **`m*` exceeds 1.5 in every single symbol-year** (1.71–4.08), meaning at the median breakout bar the ATR term sits below the floor and the floor binds — which is precisely the 64.8% / 81.1% binding rates Finding 2 recorded. The extremes line up too: BTC 2023 has the highest `m*` at 4.08 and was the cell with 99.3% floor binding; SOL has the lowest and was the cell that stayed volatility-scaled at 40–59%.

It also shows the recalibration is a larger move than it might have looked. The derived floor (1.02–1.32%) is **higher** than the current hard-coded 1.0%, so clearing it requires the multiplier to rise further still — and A6's sweep range of `0.4·m*` to `3.0·m*` spans roughly 0.68–12.2 across the six cells. Whether a multiplier that clears the floor still admits a plausible 2R target within the hold horizon is exactly the A3 acceptance question, and it is not answered here.

### 5.9 M9 — signal counts per gate arm

**These are signal-bar counts, not trades. No trade was simulated.** Portfolio-mode occupancy (one position per symbol, no pyramiding) would reduce every figure below; signal mode has no position limits and is the edge-test instrument, which is what the evidence minimums are denominated in.

Counts per symbol per year per direction:

| Symbol | Year | Dir | ungated | RVOL only | both @ vp 0.5 | @ 0.6 | @ 0.7 | @ 0.8 |
|---|---|---|---|---|---|---|---|---|
| BTCUSDT | 2022 | long | 872 | 689 | 567 | 185 | 7 | 0 |
| BTCUSDT | 2022 | short | 995 | 785 | 677 | 231 | 12 | 0 |
| BTCUSDT | 2023 | long | 993 | 753 | 611 | 182 | 6 | 0 |
| BTCUSDT | 2023 | short | 703 | 526 | 409 | 121 | 2 | 0 |
| ETHUSDT | 2022 | long | 998 | 719 | 578 | 253 | 24 | 0 |
| ETHUSDT | 2022 | short | 1,039 | 779 | 632 | 290 | 24 | 0 |
| ETHUSDT | 2023 | long | 914 | 612 | 468 | 154 | 6 | 0 |
| ETHUSDT | 2023 | short | 744 | 512 | 388 | 119 | 3 | 0 |
| SOLUSDT | 2022 | long | 1,159 | 702 | 529 | 248 | 34 | 3 |
| SOLUSDT | 2022 | short | 1,289 | 771 | 629 | 270 | 38 | 1 |
| SOLUSDT | 2023 | long | 1,103 | 829 | 680 | 295 | 31 | 2 |
| SOLUSDT | 2023 | short | 902 | 742 | 615 | 297 | 41 | 0 |

`rsi_lower` is omitted from the arm columns because it rejects nothing (M7): the "with `rsi_lower`" count equals the ungated count in all twelve rows.

**Against the pre-committed evidence minimums — 200 IS, 50 OOS, 30 per direction, per symbol. The minimums do not move.**

- **Ungated and RVOL-only: comfortable.** Every symbol-year-direction cell clears 200 on its own, with 512–1,289 signals. Two years of in-sample data yields 3,563–4,453 signals per symbol.
- **Conjunctive gate at `vwap_position` ≥ 0.5: still comfortable.** 388–680 per cell.
- **At ≥ 0.6: tight but viable.** 119–297 per cell. A single symbol-year-direction cell now sits near the 200 IS floor, and below it in several cells; pooling the two years clears it.
- **At ≥ 0.7: the population collapses.** 2–41 per cell. **Every cell falls below the 30-per-direction minimum except SOL, and none reaches 200 IS.**
- **At ≥ 0.8: essentially nothing.** 0–3.

The cliff between 0.6 and 0.7 is a direct consequence of M3: with the gated term concentrated at median ~0.56 and IQR ~0.10, a threshold at 0.7 sits roughly two interquartile ranges above the median and rejects nearly everything.

**Reconciliation with ER2's predicted joint survival band of 16–50% of breakout bars.** The measured joint survival is:

| threshold | joint survival, share of ungated |
|---|---|
| vp ≥ 0.5 | 58–65% — **above** the band |
| vp ≥ 0.6 | 17–28% — **inside** the band |
| vp ≥ 0.7 | 0.3–4% — **below** the band |

ER2's band was derived from RVOL ~66% × a design range of 25–75% for `vwap_position`. The measured RVOL term is 60–79%, near the assumed 66%. The `vwap_position` term is what moves: at a threshold of 0.5 it admits ~75–80% of the RVOL-passing set, just above the design range's ceiling, because the median sits at 0.56 rather than 0.50. **The band is reachable, but only in a narrow threshold window around 0.55–0.65.** ER2's arithmetic was sound; the operating point it implies is tighter than the round number 0.5 would suggest.

---

## 6. Documentation corrections (C1–C3)

All three applied to `docs/handoff/05_point_1r.md`. No decision content changed.

**C1 — Section 13 renumbered `A1–A7` → `ER1–ER7`.** Resolves the label collision with Section 3's stop-geometry amendments flagged in report 06 §5.6. Seven headings renamed. Two cross-references updated (`Section 13, A3` → `Section 13, ER3`, at line 48 in the A2 formula block and line 345 in Section 10). Section 3's own `A1–A7` labels are untouched, as required.

**C2 — stale B4 figure superseded.** The B4 sample-size paragraph in Section 4 previously read `~66% x ~50% = ~33% of breakout bars`. It now states the measured RVOL term (~66%) separately from the `vwap_position` term, gives the latter as the ER1 design range of 25–75% rather than an invented pass rate, states the resulting joint survival band of **16%–50%**, and points to Section 13, ER2 as the governing item. The `~66%` figure is retained, as instructed — it was measured. This closes the flag raised in report 06 §5.1, where A2/ER2 was recorded in Section 13 but not applied in place.

**C3 — tick schedule recorded.** New subsection **8.1 Tick Schedule (recorded fact)** in Section 8. Values were read from `config/contracts_cache.json` programmatically, not transcribed:

| Symbol | Cached segments | Prompt | Agreement |
|---|---|---|---|
| BTCUSDT | `[[0, 0.1]]` | 0.1 | **matches** |
| ETHUSDT | `[[0, 0.01]]` | 0.01 | **matches** |
| SOLUSDT | `[[0, 0.0001], [1723608300000, 0.001]]` | 0.0001 before 2024-08-14T04:05:00Z, then 0.001 | **matches** — ts 1723608300000 = 2024-08-14T04:05:00Z exactly |

**No disagreement between the cache and the prompt.** The subsection records that the tick is `priceEndStep × 10^-pricePlace` and not `10^-pricePlace` (they coincide today only because `priceEndStep == 1` for all three symbols), that a tick is a step function of time rather than a scalar, and that the SOL boundary was discovered by grid-validating historical prices against candidate grids because Bitget's contracts endpoint reports only the current state. It also notes that only SOL's 0.0001 segment is in force inside the 2022–23 measurement window.

---

## 7. Flagged — NOT resolved

**7.1 — M3's dispersion check does not specify which population it means, and the two readings disagree about whether B3 lives.** This is the most consequential ambiguity in the pass.

Section 13 / ER1 says the IQR is measured "on breakout bars" and stops there. But the gate is applied **directionally**: longs test `vwap_position ≥ t`, shorts test `(1 − vwap_position) ≥ t`. So there are two defensible populations:

- **Pooled** across directions: IQR 0.124–0.157 → **3 PASS, 3 FAIL**.
- **Per direction**, which is what a threshold actually sees: IQR 0.089–0.126 → **6 FAIL, 0 PASS**.

Under the directional reading B3 dies outright and unanimously. Under the pooled reading it survives in half the cells, and ER1 gives no aggregation rule across symbol-years to resolve a 3–3 split either (unlike B2, which carries an explicit two-of-three rule). Both readings are reported above; **neither is adopted here.**

Two further points bearing on whoever resolves it, neither of which is a resolution: the pooled IQR is inflated by direction-mixing — the same artifact that inflated the M2 correlation five-fold — which is an argument that the pooled figure is measuring something other than what the check intends. And the choice was not foreseeable when ER1 was written, so this is a genuine gap in the pre-commitment rather than a threshold that wants adjusting after seeing data.

**7.2 — ER1 fixes per-symbol-per-year thresholds but no aggregation rule for M1, M3 or M7.** M1 and M7 came out unanimous so it does not bite there. M3 splits 3–3 pooled and it does. B2 (ER1's last item) and the Section 10 two-of-three rule both show the project knows how to write such a rule; B3's dispersion check simply does not have one.

**7.3 — the 1R.5 "reversal breakout" hypothesis is untestable on this window, not refuted.** F2 pre-registered two readings: decorative, or "a small coherent reversal-breakout population" making it a real regime filter. With exactly zero rejections there is no population to characterise, so the second reading was never given a chance to be right. The verdict (drops now) follows mechanically from the < 5% cut and is not in doubt. But the record should say the hypothesis was **unexercised**, not falsified. Whether reversal breakouts exist as a distinct population remains an open question that RSI ≥ 50 turned out not to address.

**7.4 — M4's measured RVOL pass rates do not exactly reproduce Finding 3.** Section 2 records 65.9% (2022) / 68.8% (2023); this pass pools to ~70.6% / ~74.0%. The direction of the 2022→2023 change agrees (both rise) but the levels differ by ~5 points. Most likely explanation: a different breakout-bar denominator — this pass defines a breakout bar as trend + Donchian only, per the prompt, whereas Finding 3's figure may have been computed on a population that already had other conditions applied, or pooled across symbols with different weighting. Not investigated; the earlier figure's provenance is not in the handoff. Flagging because Finding 3 is one of the four findings that motivated 1R.

**7.5 — `c_roundtrip`'s slippage term is specified inconsistently between the prompt and the engine.** A2 and this prompt both say "plus the engine's slippage haircut on both sides". The engine applies **entry slippage on the entry leg** (`entry_slippage_bps`, deliberately 0 — the 1m fill convention already absorbs latency and raising it would double-count) and the **stop-market haircut on the stop leg** (`stop_haircut_bps`, 5 bps BTC/ETH, 10 bps SOL). It does not apply the haircut twice. Both variants are reported in §5.8; they differ materially (BTC floor 1.020% vs 1.320%, SOL 1.320% vs 1.920%), and the choice propagates into `m*` and hence the A6 sweep range. **Not resolved** — resolving it would mean choosing a parameter value, which is Point 3R's job.

**7.6 — M5 produced a result that runs against B1's motivation, and it is uniform.** At matched selectivity, session-normalised RVOL is less selective than flat RVOL in all 24 cells measured. B1's own justification is nonetheless confirmed on its own terms — the hour-of-day pass-rate spread is large under the flat baseline (32–51pp) and compresses under session normalisation in 5 of 6 cells. Both results are reported as characterisation. **No `baseline_days` and no threshold is recommended**, and no view is offered on whether B1 should survive; that is a Point 4 sweep decision.

**7.7 — degenerate bars and zero-volume bars do not occur in this window at all.** Zero of 210,240 bars. The explicit branches for both are exercised only by unit tests. This is worth recording because it means the real data has not tested them, and 2024–26 has not been looked at.

**7.8 — M5's 2022 figures rest on a slightly shorter year than 2023's.** No pre-2022 data exists, so the session baseline warms up inside 2022 — at `baseline_days = 30`, all of January 2022 is excluded. Cross-year comparisons of M5 for 2022 are very slightly biased by the missing month. The effect is small and is not corrected.

**7.9 — M6's two stability statistics disagree in emphasis.** The decision rule is met (`quote_volume`, 3 of 3 symbols), but almost entirely on the global statistic; the local statistic — the one describing what the gate actually computes — shows the two denominations differing in the fourth-to-fifth decimal, and flips sign in one cell. The rule as written was chosen before this was visible and is applied as written. Recording that the margin is thinner than the verdict looks.

---

## 8. Firewall and scope confirmation

- **No trade was simulated.** `src/engine/simulate.py` is not imported by any file added in this pass. Enforced by test (`test_analysis_module_never_imports_the_simulator`), which tokenises the module and strips comments and docstrings before checking, so the prose discussing the firewall cannot make the check pass or fail spuriously.
- **No P&L, expectancy, win rate, profit factor, Sharpe, return or equity figure was computed, displayed or estimated.** The `net_pnl` and `r_multiple` columns were never read; the same test bans those identifiers from executable tokens.
- **Every quantity in this report is a bar-level statistic, a count, a correlation or closed-form parameter arithmetic.** The percentages are pass rates, rejection rates and binding-adjacent scale figures — all on the allowed list in handoff 04 §2.
- **No data outside 2022–2023 was read.** Truncation happens at the parquet boundary before any computation, and is covered by a test. The 2025–26 holdout is untouched. SOL's 2024 tick segment is recorded in the handoff as a documentation fact from `config/contracts_cache.json`; no 2024 bar was loaded.
- **No file under `src/engine/`, `config/` or `data/` was created, modified or deleted.** Confirmed by `git status` — see §9.
- **No 1R amendment was implemented.** The engine remains at the pre-1R design. This pass measures; Point 3R builds.
- **No Section 13 threshold was adjusted, reinterpreted or softened**, and no commentary proposing that any be revisited now that data has been seen appears anywhere above.
- **Engine indicator implementations were reused, not reimplemented.** `ema`, `rsi_wilder`, `atr_wilder`, `donchian_prior`, `rvol_prior` and `compute_indicators` are imported from `src/engine/signals.py`. The only new computations are `close_position`, `bar_vwap`, `vwap_position`, the session slot baseline (which has no engine equivalent — it is the B1 proposal) and descriptive statistics. The breakout-bar definition is the engine's own trend and Donchian terms with RVOL and RSI removed, and a test asserts that every engine signal bar falls inside it and that changing the RVOL/RSI knobs does not move it.

## 9. Git state

Commit hash, `git status` and `git diff --stat` are recorded here after the commit is made — see the commit referenced in §1.
