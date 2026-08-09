# REPORT 14 — THE SWEEP (step 2 of the §4.4 sequence)

Simulates every A3-surviving grid point across all folds, symbols and arms, and produces the per-cell statistics steps 3 through 8 consume.

**THIS TASK PRODUCES INPUTS AND STOPS.** No band identification, no plateau selection, no collapse, no two-of-three, no D5 drop decision, no top-5% removal, no ±25% sensitivity probe. Appendix K.2's acceptance definition is deliberately NOT applied: expectancy and counts are reported, and whether a grid point passes is decided at step 3.

**The holdout remains SEALED.** The report-13 seal was active throughout; the 1m span is clamped by `in_sample_years`, no call site authorises a holdout read, and a test fails if the sweep ever overrides `exclude_holdout_crossing`.

## 0. The population contract

Five significant Point 4 defects have been the same error: a quantity measured on one population and applied to another, invisible because both had the same name (Appendices F.1, H, M.1, M.2, and report 12's `n_ungated`). Every figure below therefore names its population, drawn from a closed set:

| population | definition |
|---|---|
| `ungated` | every simulated signal, before any RVOL filter |
| `breakout` | bars passing Donchian-20 + EMA20/EMA50, pre-RVOL — a BAR population, so it carries counts and binding rates and no expectancy |
| `gated_30` / `gated_50` / `gated_70` | `ungated` filtered at the 30/50/70% pass-rate threshold |

crossed with exactly one of `train`/`test` and one of `long`/`short`/`both`. `sweep.record()` is the only constructor for an artifact row and requires all four labels; `validate_records` refuses a row missing a label, carrying one outside its set, or an empty list. Six planted mutations prove the guard bites — one per label stripped, one relabelled to `gated_60`, one empty list.

## 1. Provenance

- **HEAD the SWEEP ran at:** `c9220948221613b154cb6cd249d01d14789f452e`
- **Working tree at that point:** clean. `src/sweep/sweep.py` refuses to start on a dirty tree, so this hash is clean by construction and the figures below are reproducible from it.
- **HEAD the REPORT was generated at:** `c9220948221613b154cb6cd249d01d14789f452e-dirty` (later; formatting only, no simulation re-run)
- **grid.json provenance:** `3d04c00663af8098a4fe0740d4d31d52d828d169` (step 0, pre-lift)
- **Mode:** signal mode (§4.5 edge-test instrument) — every signal simulated independently, no occupancy, cooldown or margin limit
- **`baseline_days`:** 20 (§4.3, fixed not swept); **`stop_max_pct`** from grid.json per Appendix H (P95 form)
- **Window:** in-sample only, 2022-04-01 → 2024-12-31, nine folds, train and test computed separately

## 2. Cell count

A cell is (fold, symbol, offset, arm, population, period, direction).

| quantity | value |
|---|---|
| folds × symbols | 9 × 3 = 27 |
| A3-eligible (fold, symbol, offset) combinations | **198** (BTC 62, ETH 70, SOL 66) |
| arm × population pairs emitted | 6 |
| periods × directions | 2 × 3 = 6 |
| **labelled records** | **7128** |
| backtests executed | 198 × 2 periods × 3 simulations = 1188 |

Offset 2.50 is excluded everywhere: §4.3's plateau rule requires passing neighbours on BOTH sides, which the edge of the searched range can never have, so it is ineligible for selection and is not simulated.

## 3. Artifact structure

The per-cell table is far too large to inline. It is written as one JSON object per line:

```
data/derived/sweep/sweep_cells.jsonl          7128 records
  {fold_id, symbol, offset, multiplier,
   arm, population, period, direction,      <- the four mandatory labels
   metrics: {n, expectancy_r, sigma_r, se_r, expectancy_per_bar_r,
             floor_binding_rate, cap_binding_rate, atr_binding_rate,
             exit_reasons{...}, holding_stop{...}, holding_target{...},
             min_r, max_r},
   floor_strata: {floor_bound{...}, not_floor_bound{...}}}   <- App. J
```

- `data/derived/sweep/trades` — full trade tables, one parquet per (symbol, fold), every row labelled with `arm`, `population`-defining RVOL thresholds, `offset` and `period`.
- `data/derived/sweep/sweep.json` — the aggregates below, tracked in git alongside `grid.json` and `folds.json`.

## 4. How each decomposition arm was produced

§4.5 runs signal mode so gated arms are FILTERS of one ungated simulation and share an identical trade universe by construction. **That holds for the RVOL arms and for exactly one of the decomposition arms.** The rest required re-simulation, and saying which is the point of this table.

| arm | population(s) | produced by | universe vs the full model |
|---|---|---|---|
| `full` | `gated_30`, `gated_50`, `gated_70` | **filter** of the base simulation | identical by construction |
| `minus_rvol` | `ungated` | **filter** of the base simulation | identical by construction (it is the unfiltered set) |
| `minus_ema` | `gated_50` | **RE-SIMULATED** | strict **SUPERSET** — dropping the trend filter admits bars the baseline never generated |
| `minus_time_stop` | `gated_50` | **RE-SIMULATED** | **identical** — the checkpoint changes when a trade exits, not whether it exists |
| `minus_max_hold` | — | **BLOCKED, NOT RUN** | see §4.1 |

Universe identity is asserted **by trade id**, not by count: the gated arms are proper subsets of `ungated` and nest across 70 → 50 → 30; `minus_time_stop` is set-equal to `full`; `minus_ema` is a proper superset, which is precisely why it cannot be a filter of anything.

`generate_signals` gained `apply_ema_filter=True`, mirroring the existing `apply_rvol_gate`, so the minus-EMA universe is produced by the engine rather than reimplemented in the sweep. A test asserts the default is bit-identical to the baseline rule, so engine semantics do not move.

### 4.1 `minus_max_hold` is BLOCKED, and why it was not faked

`costs.CostConfig.max_hold_bars` is a **read-only property** fixed at `2 × donchian_period` and documented *"NOT independently sweepable"*. Removing the cap requires either:

- changing `donchian_period`, which changes the breakout rule itself, so the result would not be a leave-one-out of the same strategy; or
- introducing a replacement holding horizon — **a free parameter that is nowhere pre-registered.**

Inventing that horizon post-lift is exactly the move this design exists to prevent, so the arm is reported as blocked rather than run against a fabricated number. A test asserts the property is genuinely read-only, so the blocker cannot decay into an excuse.

**Nothing downstream is gated on it.** §4.4 classifies max-hold as a GUARD RAIL — *"measured and reported, NEVER dropped"* — so the arm is descriptive and no D5 decision depends on it. Recorded in §9 as a specification gap.

## 5. Boundary-crossing exclusions (Appendix M.3)

Population: `ungated` — signal mode simulates the ungated universe, and that is the population report 12 measured on the wrong side of, per Appendix M.2.

**The raw counter accumulates across offset runs.** Exclusion is decided on the signal bar by `crosses_holdout`, which depends only on the entry timestamp and `max_hold_bars` — **not on the stop geometry** — so the same signals are excluded once per offset simulated. The per-offset count is the meaningful figure and is the one to read.

| symbol | fold | eligible offsets | train (per offset) | test (per offset) | test (raw, summed over offsets) |
|---|---|---|---|---|---|
| SOLUSDT | 9 | 7 | 0 | **5** | 35 |

All other 26 of 27 fold-symbols excluded zero in every period at every offset.

**This reproduces E6 exactly.** Report 13 measured five excluded ungated SOLUSDT fold-9 test trades; the sweep excludes the same five at every one of the seven eligible offsets. Fold 9 is the only fold whose test period ends 2024-12-31, so it is the only cell that can touch the boundary. Zero trades on the `gated_50` arm are affected, also matching report 13.

## 6. Appendix J — arm comparisons, stratified by floor binding

Appendix J requires that **every** arm comparison carry (a) each arm's floor-binding rate and (b) the comparison stratified into floor-bound and non-floor-bound trades, wherever both strata clear the evidence minimums. Where a stratum falls short it is stated and the stratified figure is withheld. **The minimums do not move.**

**Pooling, named:** every row pools **TEST FOLDS ONLY**, per Appendix M.4 — training folds overlap by 50%, so pooling them double-counts mid-span trades and understates the standard error. Rows are **not** pooled across offsets; each offset is reported separately, with the number of folds in which that offset is A3-eligible.

This is DESCRIPTION. §4.3's 30/50/70 monotonicity reading and the 0.05R marginal-contribution comparison happen at later steps.

### 6.1 BTCUSDT — test folds only

| offset | arm | population | folds | n | E[R] | SE | floor % | E[R] floor-bound | E[R] non-floor-bound |
|---|---|---|---|---|---|---|---|---|---|
| 0.5 | `full` | `gated_30` | 4 | 427 | -0.0771 | 0.0354 | 27.9 | -0.0846 (n=119) | -0.0742 (n=308) |
| 0.5 | `full` | `gated_50` | 4 | 784 | -0.0378 | 0.0269 | 29.7 | -0.0763 (n=233) | -0.0215 (n=551) |
| 0.5 | `full` | `gated_70` | 4 | 1189 | -0.0529 | 0.0215 | 33.1 | -0.0899 (n=394) | -0.0346 (n=795) |
| 0.5 | `minus_rvol` | `ungated` | 4 | 1849 | -0.0677 | 0.0162 | 45.0 | -0.0830 (n=832) | -0.0552 (n=1017) |
| 0.5 | `minus_ema` | `gated_50` | 4 | 1013 | -0.0641 | 0.0226 | 30.1 | -0.1012 (n=305) | -0.0481 (n=708) |
| 0.5 | `minus_time_stop` | `gated_50` | 4 | 784 | 0.0052 | 0.0332 | 29.7 | -0.1000 (n=233) | 0.0497 (n=551) |
| 0.75 | `full` | `gated_30` | 6 | 1023 | -0.0750 | 0.0240 | 19.4 | -0.0674 (n=198) | -0.0768 (n=825) |
| 0.75 | `full` | `gated_50` | 6 | 1581 | -0.0613 | 0.0192 | 24.2 | -0.0638 (n=382) | -0.0605 (n=1199) |
| 0.75 | `full` | `gated_70` | 6 | 2132 | -0.0749 | 0.0163 | 28.4 | -0.0810 (n=606) | -0.0724 (n=1526) |
| 0.75 | `minus_rvol` | `ungated` | 6 | 3025 | -0.0855 | 0.0130 | 37.9 | -0.0851 (n=1146) | -0.0858 (n=1879) |
| 0.75 | `minus_ema` | `gated_50` | 6 | 2096 | -0.0889 | 0.0161 | 24.4 | -0.1218 (n=512) | -0.0782 (n=1584) |
| 0.75 | `minus_time_stop` | `gated_50` | 6 | 1581 | -0.0459 | 0.0234 | 24.2 | -0.0748 (n=382) | -0.0367 (n=1199) |
| 1 | `full` | `gated_30` | 8 | 1204 | -0.0569 | 0.0213 | 15.0 | -0.0276 (n=180) | -0.0620 (n=1024) |
| 1 | `full` | `gated_50` | 8 | 1923 | -0.0494 | 0.0169 | 18.8 | -0.0377 (n=361) | -0.0522 (n=1562) |
| 1 | `full` | `gated_70` | 8 | 2663 | -0.0576 | 0.0143 | 22.7 | -0.0696 (n=604) | -0.0540 (n=2059) |
| 1 | `minus_rvol` | `ungated` | 8 | 3887 | -0.0762 | 0.0114 | 31.8 | -0.0806 (n=1236) | -0.0742 (n=2651) |
| 1 | `minus_ema` | `gated_50` | 8 | 2515 | -0.0723 | 0.0144 | 19.0 | -0.0908 (n=477) | -0.0680 (n=2038) |
| 1 | `minus_time_stop` | `gated_50` | 8 | 1923 | -0.0368 | 0.0206 | 18.8 | -0.0357 (n=361) | -0.0371 (n=1562) |
| 1.25 | `full` | `gated_30` | 8 | 1204 | -0.0510 | 0.0208 | 12.7 | 0.0152 (n=153) | -0.0606 (n=1051) |
| 1.25 | `full` | `gated_50` | 8 | 1923 | -0.0457 | 0.0164 | 16.1 | 0.0050 (n=309) | -0.0554 (n=1614) |
| 1.25 | `full` | `gated_70` | 8 | 2663 | -0.0531 | 0.0139 | 19.7 | -0.0465 (n=525) | -0.0548 (n=2138) |
| 1.25 | `minus_rvol` | `ungated` | 8 | 3887 | -0.0716 | 0.0111 | 28.6 | -0.0708 (n=1112) | -0.0720 (n=2775) |
| 1.25 | `minus_ema` | `gated_50` | 8 | 2515 | -0.0703 | 0.0140 | 16.1 | -0.0648 (n=405) | -0.0714 (n=2110) |
| 1.25 | `minus_time_stop` | `gated_50` | 8 | 1923 | -0.0328 | 0.0201 | 16.1 | 0.0171 (n=309) | -0.0423 (n=1614) |
| 1.5 | `full` | `gated_30` | 9 | 1403 | -0.0249 | 0.0195 | 10.6 | 0.0247 (n=149) | -0.0307 (n=1254) |
| 1.5 | `full` | `gated_50` | 9 | 2177 | -0.0330 | 0.0154 | 13.6 | -0.0215 (n=297) | -0.0348 (n=1880) |
| 1.5 | `full` | `gated_70` | 9 | 2980 | -0.0462 | 0.0131 | 17.2 | -0.0517 (n=512) | -0.0451 (n=2468) |
| 1.5 | `minus_rvol` | `ungated` | 9 | 4285 | -0.0653 | 0.0105 | 26.0 | -0.0841 (n=1114) | -0.0586 (n=3171) |
| 1.5 | `minus_ema` | `gated_50` | 9 | 2852 | -0.0593 | 0.0130 | 13.7 | -0.0665 (n=391) | -0.0581 (n=2461) |
| 1.5 | `minus_time_stop` | `gated_50` | 9 | 2177 | -0.0195 | 0.0187 | 13.6 | -0.0087 (n=297) | -0.0212 (n=1880) |
| 1.75 | `full` | `gated_30` | 9 | 1403 | -0.0250 | 0.0188 | 8.9 | -0.0233 (n=125) | -0.0251 (n=1278) |
| 1.75 | `full` | `gated_50` | 9 | 2177 | -0.0305 | 0.0149 | 11.4 | -0.0324 (n=248) | -0.0303 (n=1929) |
| 1.75 | `full` | `gated_70` | 9 | 2980 | -0.0436 | 0.0127 | 14.7 | -0.0588 (n=438) | -0.0410 (n=2542) |
| 1.75 | `minus_rvol` | `ungated` | 9 | 4285 | -0.0624 | 0.0102 | 23.5 | -0.0920 (n=1006) | -0.0533 (n=3279) |
| 1.75 | `minus_ema` | `gated_50` | 9 | 2852 | -0.0551 | 0.0127 | 11.5 | -0.0766 (n=328) | -0.0523 (n=2524) |
| 1.75 | `minus_time_stop` | `gated_50` | 9 | 2177 | -0.0158 | 0.0183 | 11.4 | -0.0147 (n=248) | -0.0160 (n=1929) |
| 2 | `full` | `gated_30` | 9 | 1403 | -0.0194 | 0.0183 | 7.3 | -0.0629 (n=102) | -0.0159 (n=1301) |
| 2 | `full` | `gated_50` | 9 | 2177 | -0.0275 | 0.0145 | 9.3 | -0.0747 (n=202) | -0.0227 (n=1975) |
| 2 | `full` | `gated_70` | 9 | 2980 | -0.0413 | 0.0123 | 12.3 | -0.0868 (n=367) | -0.0349 (n=2613) |
| 2 | `minus_rvol` | `ungated` | 9 | 4285 | -0.0601 | 0.0099 | 21.0 | -0.1064 (n=901) | -0.0478 (n=3384) |
| 2 | `minus_ema` | `gated_50` | 9 | 2852 | -0.0517 | 0.0123 | 9.4 | -0.1092 (n=269) | -0.0457 (n=2583) |
| 2 | `minus_time_stop` | `gated_50` | 9 | 2177 | -0.0132 | 0.0178 | 9.3 | -0.0933 (n=202) | -0.0050 (n=1975) |
| 2.25 | `full` | `gated_30` | 9 | 1403 | -0.0174 | 0.0177 | 6.4 | -0.0610 (n=90) | -0.0144 (n=1313) |
| 2.25 | `full` | `gated_50` | 9 | 2177 | -0.0258 | 0.0140 | 8.1 | -0.0857 (n=176) | -0.0205 (n=2001) |
| 2.25 | `full` | `gated_70` | 9 | 2980 | -0.0386 | 0.0119 | 10.8 | -0.0978 (n=321) | -0.0314 (n=2659) |
| 2.25 | `minus_rvol` | `ungated` | 9 | 4285 | -0.0581 | 0.0096 | 19.2 | -0.1104 (n=821) | -0.0457 (n=3464) |
| 2.25 | `minus_ema` | `gated_50` | 9 | 2852 | -0.0497 | 0.0119 | 7.9 | -0.0908 (n=225) | -0.0461 (n=2627) |
| 2.25 | `minus_time_stop` | `gated_50` | 9 | 2177 | -0.0090 | 0.0173 | 8.1 | -0.1021 (n=176) | -0.0008 (n=2001) |

### 6.2 ETHUSDT — test folds only

| offset | arm | population | folds | n | E[R] | SE | floor % | E[R] floor-bound | E[R] non-floor-bound |
|---|---|---|---|---|---|---|---|---|---|
| 0.25 | `full` | `gated_30` | 1 | 181 | -0.1074 | 0.0458 | 5.0 | n=9 <50 **withheld** | -0.1161 (n=172) |
| 0.25 | `full` | `gated_50` | 1 | 307 | -0.0376 | 0.0391 | 5.9 | n=18 <50 **withheld** | -0.0390 (n=289) |
| 0.25 | `full` | `gated_70` | 1 | 408 | -0.0369 | 0.0354 | 9.1 | n=37 <50 **withheld** | -0.0377 (n=371) |
| 0.25 | `minus_rvol` | `ungated` | 1 | 510 | -0.0508 | 0.0311 | 17.1 | -0.0295 (n=87) | -0.0552 (n=423) |
| 0.25 | `minus_ema` | `gated_50` | 1 | 384 | -0.0602 | 0.0346 | 5.7 | n=22 <50 **withheld** | -0.0628 (n=362) |
| 0.25 | `minus_time_stop` | `gated_50` | 1 | 307 | -0.0115 | 0.0507 | 5.9 | n=18 <50 **withheld** | -0.0233 (n=289) |
| 0.5 | `full` | `gated_30` | 6 | 898 | -0.0834 | 0.0281 | 22.6 | -0.0250 (n=203) | -0.1005 (n=695) |
| 0.5 | `full` | `gated_50` | 6 | 1357 | -0.0693 | 0.0230 | 24.9 | -0.0236 (n=338) | -0.0844 (n=1019) |
| 0.5 | `full` | `gated_70` | 6 | 1875 | -0.0768 | 0.0192 | 27.9 | -0.0822 (n=523) | -0.0747 (n=1352) |
| 0.5 | `minus_rvol` | `ungated` | 6 | 2736 | -0.0824 | 0.0151 | 38.7 | -0.0818 (n=1058) | -0.0828 (n=1678) |
| 0.5 | `minus_ema` | `gated_50` | 6 | 1762 | -0.0626 | 0.0201 | 24.7 | -0.0347 (n=435) | -0.0717 (n=1327) |
| 0.5 | `minus_time_stop` | `gated_50` | 6 | 1357 | -0.0835 | 0.0272 | 24.9 | -0.0658 (n=338) | -0.0893 (n=1019) |
| 0.75 | `full` | `gated_30` | 9 | 1394 | -0.0710 | 0.0229 | 16.4 | -0.0383 (n=228) | -0.0774 (n=1166) |
| 0.75 | `full` | `gated_50` | 9 | 2101 | -0.0760 | 0.0186 | 18.5 | -0.0208 (n=389) | -0.0885 (n=1712) |
| 0.75 | `full` | `gated_70` | 9 | 2877 | -0.0874 | 0.0156 | 21.5 | -0.0873 (n=618) | -0.0875 (n=2259) |
| 0.75 | `minus_rvol` | `ungated` | 9 | 4159 | -0.0887 | 0.0126 | 31.8 | -0.0957 (n=1322) | -0.0855 (n=2837) |
| 0.75 | `minus_ema` | `gated_50` | 9 | 2734 | -0.0757 | 0.0160 | 18.3 | -0.0306 (n=501) | -0.0859 (n=2233) |
| 0.75 | `minus_time_stop` | `gated_50` | 9 | 2101 | -0.0807 | 0.0221 | 18.5 | -0.0431 (n=389) | -0.0893 (n=1712) |
| 1 | `full` | `gated_30` | 9 | 1394 | -0.0661 | 0.0223 | 12.2 | -0.0624 (n=170) | -0.0667 (n=1224) |
| 1 | `full` | `gated_50` | 9 | 2101 | -0.0692 | 0.0181 | 14.9 | -0.0169 (n=313) | -0.0783 (n=1788) |
| 1 | `full` | `gated_70` | 9 | 2877 | -0.0799 | 0.0151 | 17.6 | -0.0831 (n=506) | -0.0792 (n=2371) |
| 1 | `minus_rvol` | `ungated` | 9 | 4159 | -0.0831 | 0.0123 | 27.9 | -0.1015 (n=1161) | -0.0759 (n=2998) |
| 1 | `minus_ema` | `gated_50` | 9 | 2734 | -0.0685 | 0.0156 | 14.6 | -0.0291 (n=399) | -0.0752 (n=2335) |
| 1 | `minus_time_stop` | `gated_50` | 9 | 2101 | -0.0715 | 0.0216 | 14.9 | -0.0449 (n=313) | -0.0761 (n=1788) |
| 1.25 | `full` | `gated_30` | 9 | 1394 | -0.0589 | 0.0213 | 8.8 | 0.0406 (n=122) | -0.0685 (n=1272) |
| 1.25 | `full` | `gated_50` | 9 | 2101 | -0.0649 | 0.0173 | 11.6 | 0.0523 (n=244) | -0.0803 (n=1857) |
| 1.25 | `full` | `gated_70` | 9 | 2877 | -0.0758 | 0.0145 | 14.1 | -0.0564 (n=407) | -0.0790 (n=2470) |
| 1.25 | `minus_rvol` | `ungated` | 9 | 4159 | -0.0775 | 0.0118 | 23.8 | -0.0928 (n=989) | -0.0727 (n=3170) |
| 1.25 | `minus_ema` | `gated_50` | 9 | 2734 | -0.0645 | 0.0149 | 11.3 | 0.0302 (n=310) | -0.0766 (n=2424) |
| 1.25 | `minus_time_stop` | `gated_50` | 9 | 2101 | -0.0625 | 0.0208 | 11.6 | 0.0340 (n=244) | -0.0751 (n=1857) |
| 1.5 | `full` | `gated_30` | 9 | 1394 | -0.0532 | 0.0205 | 6.0 | 0.0679 (n=84) | -0.0610 (n=1310) |
| 1.5 | `full` | `gated_50` | 9 | 2101 | -0.0595 | 0.0168 | 8.5 | 0.0646 (n=178) | -0.0710 (n=1923) |
| 1.5 | `full` | `gated_70` | 9 | 2877 | -0.0696 | 0.0141 | 10.9 | -0.0654 (n=315) | -0.0702 (n=2562) |
| 1.5 | `minus_rvol` | `ungated` | 9 | 4159 | -0.0727 | 0.0115 | 20.4 | -0.0932 (n=847) | -0.0675 (n=3312) |
| 1.5 | `minus_ema` | `gated_50` | 9 | 2734 | -0.0594 | 0.0144 | 8.3 | 0.0431 (n=228) | -0.0687 (n=2506) |
| 1.5 | `minus_time_stop` | `gated_50` | 9 | 2101 | -0.0594 | 0.0202 | 8.5 | 0.0361 (n=178) | -0.0682 (n=1923) |
| 1.75 | `full` | `gated_30` | 9 | 1394 | -0.0522 | 0.0198 | 4.6 | -0.0032 (n=64) | -0.0545 (n=1330) |
| 1.75 | `full` | `gated_50` | 9 | 2101 | -0.0581 | 0.0161 | 6.6 | -0.0045 (n=138) | -0.0619 (n=1963) |
| 1.75 | `full` | `gated_70` | 9 | 2877 | -0.0674 | 0.0136 | 8.8 | -0.1042 (n=252) | -0.0639 (n=2625) |
| 1.75 | `minus_rvol` | `ungated` | 9 | 4159 | -0.0702 | 0.0111 | 17.9 | -0.0975 (n=743) | -0.0643 (n=3416) |
| 1.75 | `minus_ema` | `gated_50` | 9 | 2734 | -0.0599 | 0.0138 | 6.5 | -0.0331 (n=178) | -0.0618 (n=2556) |
| 1.75 | `minus_time_stop` | `gated_50` | 9 | 2101 | -0.0586 | 0.0196 | 6.6 | -0.0228 (n=138) | -0.0611 (n=1963) |
| 2 | `full` | `gated_30` | 9 | 1394 | -0.0455 | 0.0192 | 3.7 | 0.0340 (n=51) | -0.0486 (n=1343) |
| 2 | `full` | `gated_50` | 9 | 2101 | -0.0552 | 0.0156 | 5.2 | -0.0216 (n=109) | -0.0570 (n=1992) |
| 2 | `full` | `gated_70` | 9 | 2877 | -0.0653 | 0.0131 | 7.0 | -0.0949 (n=200) | -0.0631 (n=2677) |
| 2 | `minus_rvol` | `ungated` | 9 | 4159 | -0.0681 | 0.0108 | 15.7 | -0.0837 (n=653) | -0.0652 (n=3506) |
| 2 | `minus_ema` | `gated_50` | 9 | 2734 | -0.0570 | 0.0133 | 5.2 | -0.0457 (n=143) | -0.0577 (n=2591) |
| 2 | `minus_time_stop` | `gated_50` | 9 | 2101 | -0.0567 | 0.0190 | 5.2 | -0.0403 (n=109) | -0.0576 (n=1992) |
| 2.25 | `full` | `gated_30` | 9 | 1394 | -0.0431 | 0.0184 | 2.9 | n=40 <50 **withheld** | -0.0484 (n=1354) |
| 2.25 | `full` | `gated_50` | 9 | 2101 | -0.0521 | 0.0150 | 3.9 | 0.0207 (n=81) | -0.0550 (n=2020) |
| 2.25 | `full` | `gated_70` | 9 | 2877 | -0.0607 | 0.0127 | 5.0 | -0.0933 (n=143) | -0.0590 (n=2734) |
| 2.25 | `minus_rvol` | `ungated` | 9 | 4159 | -0.0655 | 0.0104 | 13.1 | -0.0701 (n=544) | -0.0648 (n=3615) |
| 2.25 | `minus_ema` | `gated_50` | 9 | 2734 | -0.0555 | 0.0128 | 4.0 | -0.0408 (n=110) | -0.0561 (n=2624) |
| 2.25 | `minus_time_stop` | `gated_50` | 9 | 2101 | -0.0519 | 0.0184 | 3.9 | -0.0012 (n=81) | -0.0539 (n=2020) |

### 6.3 SOLUSDT — test folds only

| offset | arm | population | folds | n | E[R] | SE | floor % | E[R] floor-bound | E[R] non-floor-bound |
|---|---|---|---|---|---|---|---|---|---|
| 0.5 | `full` | `gated_30` | 4 | 744 | 0.0334 | 0.0404 | 38.0 | 0.0246 (n=283) | 0.0389 (n=461) |
| 0.5 | `full` | `gated_50` | 4 | 1124 | 0.0229 | 0.0319 | 41.6 | 0.0197 (n=468) | 0.0252 (n=656) |
| 0.5 | `full` | `gated_70` | 4 | 1554 | -0.0137 | 0.0265 | 44.0 | -0.0352 (n=683) | 0.0032 (n=871) |
| 0.5 | `minus_rvol` | `ungated` | 4 | 2178 | -0.0522 | 0.0218 | 49.4 | -0.0951 (n=1077) | -0.0103 (n=1101) |
| 0.5 | `minus_ema` | `gated_50` | 4 | 1450 | -0.0097 | 0.0272 | 41.9 | 0.0037 (n=608) | -0.0194 (n=842) |
| 0.5 | `minus_time_stop` | `gated_50` | 4 | 1124 | 0.0350 | 0.0364 | 41.6 | 0.0366 (n=468) | 0.0339 (n=656) |
| 0.75 | `full` | `gated_30` | 8 | 1402 | -0.0116 | 0.0266 | 18.5 | 0.1273 (n=260) | -0.0432 (n=1142) |
| 0.75 | `full` | `gated_50` | 8 | 2206 | -0.0192 | 0.0208 | 22.0 | 0.0869 (n=486) | -0.0492 (n=1720) |
| 0.75 | `full` | `gated_70` | 8 | 3057 | -0.0432 | 0.0173 | 25.1 | 0.0066 (n=767) | -0.0599 (n=2290) |
| 0.75 | `minus_rvol` | `ungated` | 8 | 4367 | -0.0583 | 0.0142 | 32.2 | -0.0433 (n=1404) | -0.0654 (n=2963) |
| 0.75 | `minus_ema` | `gated_50` | 8 | 2835 | -0.0465 | 0.0178 | 22.7 | 0.0500 (n=643) | -0.0749 (n=2192) |
| 0.75 | `minus_time_stop` | `gated_50` | 8 | 2206 | -0.0157 | 0.0242 | 22.0 | 0.1483 (n=486) | -0.0620 (n=1720) |
| 1 | `full` | `gated_30` | 9 | 1583 | -0.0290 | 0.0235 | 12.4 | 0.0779 (n=197) | -0.0442 (n=1386) |
| 1 | `full` | `gated_50` | 9 | 2522 | -0.0315 | 0.0183 | 14.8 | 0.0835 (n=373) | -0.0515 (n=2149) |
| 1 | `full` | `gated_70` | 9 | 3474 | -0.0502 | 0.0154 | 16.8 | 0.0333 (n=583) | -0.0671 (n=2891) |
| 1 | `minus_rvol` | `ungated` | 9 | 4954 | -0.0600 | 0.0127 | 22.0 | -0.0258 (n=1091) | -0.0697 (n=3863) |
| 1 | `minus_ema` | `gated_50` | 9 | 3229 | -0.0516 | 0.0157 | 15.0 | 0.0413 (n=485) | -0.0680 (n=2744) |
| 1 | `minus_time_stop` | `gated_50` | 9 | 2522 | -0.0246 | 0.0216 | 14.8 | 0.1467 (n=373) | -0.0544 (n=2149) |
| 1.25 | `full` | `gated_30` | 9 | 1583 | -0.0273 | 0.0227 | 8.9 | 0.0775 (n=141) | -0.0375 (n=1442) |
| 1.25 | `full` | `gated_50` | 9 | 2522 | -0.0286 | 0.0176 | 11.5 | 0.0890 (n=289) | -0.0438 (n=2233) |
| 1.25 | `full` | `gated_70` | 9 | 3474 | -0.0473 | 0.0148 | 13.0 | 0.0383 (n=451) | -0.0600 (n=3023) |
| 1.25 | `minus_rvol` | `ungated` | 9 | 4954 | -0.0574 | 0.0122 | 17.3 | -0.0144 (n=855) | -0.0663 (n=4099) |
| 1.25 | `minus_ema` | `gated_50` | 9 | 3229 | -0.0497 | 0.0150 | 11.4 | 0.0610 (n=368) | -0.0639 (n=2861) |
| 1.25 | `minus_time_stop` | `gated_50` | 9 | 2522 | -0.0163 | 0.0209 | 11.5 | 0.1652 (n=289) | -0.0398 (n=2233) |
| 1.5 | `full` | `gated_30` | 9 | 1583 | -0.0200 | 0.0218 | 6.0 | 0.0975 (n=95) | -0.0275 (n=1488) |
| 1.5 | `full` | `gated_50` | 9 | 2522 | -0.0238 | 0.0169 | 8.2 | 0.0881 (n=206) | -0.0338 (n=2316) |
| 1.5 | `full` | `gated_70` | 9 | 3474 | -0.0420 | 0.0142 | 9.6 | 0.0278 (n=335) | -0.0494 (n=3139) |
| 1.5 | `minus_rvol` | `ungated` | 9 | 4954 | -0.0522 | 0.0118 | 13.2 | -0.0107 (n=654) | -0.0585 (n=4300) |
| 1.5 | `minus_ema` | `gated_50` | 9 | 3229 | -0.0441 | 0.0144 | 8.1 | 0.0772 (n=261) | -0.0548 (n=2968) |
| 1.5 | `minus_time_stop` | `gated_50` | 9 | 2522 | -0.0095 | 0.0202 | 8.2 | 0.1456 (n=206) | -0.0233 (n=2316) |
| 1.75 | `full` | `gated_30` | 9 | 1583 | -0.0220 | 0.0209 | 4.3 | 0.0910 (n=68) | -0.0271 (n=1515) |
| 1.75 | `full` | `gated_50` | 9 | 2522 | -0.0201 | 0.0162 | 5.6 | 0.0725 (n=141) | -0.0256 (n=2381) |
| 1.75 | `full` | `gated_70` | 9 | 3474 | -0.0379 | 0.0137 | 6.8 | 0.0263 (n=236) | -0.0426 (n=3238) |
| 1.75 | `minus_rvol` | `ungated` | 9 | 4954 | -0.0469 | 0.0113 | 9.9 | -0.0034 (n=491) | -0.0517 (n=4463) |
| 1.75 | `minus_ema` | `gated_50` | 9 | 3229 | -0.0401 | 0.0138 | 5.5 | 0.0732 (n=179) | -0.0468 (n=3050) |
| 1.75 | `minus_time_stop` | `gated_50` | 9 | 2522 | -0.0068 | 0.0196 | 5.6 | 0.1260 (n=141) | -0.0146 (n=2381) |
| 2 | `full` | `gated_30` | 9 | 1583 | -0.0182 | 0.0199 | 2.9 | n=46 <50 **withheld** | -0.0249 (n=1537) |
| 2 | `full` | `gated_50` | 9 | 2522 | -0.0148 | 0.0155 | 4.1 | 0.1449 (n=104) | -0.0217 (n=2418) |
| 2 | `full` | `gated_70` | 9 | 3474 | -0.0344 | 0.0131 | 5.2 | 0.0337 (n=180) | -0.0381 (n=3294) |
| 2 | `minus_rvol` | `ungated` | 9 | 4954 | -0.0432 | 0.0108 | 7.7 | 0.0081 (n=379) | -0.0474 (n=4575) |
| 2 | `minus_ema` | `gated_50` | 9 | 3229 | -0.0327 | 0.0132 | 4.0 | 0.1001 (n=129) | -0.0382 (n=3100) |
| 2 | `minus_time_stop` | `gated_50` | 9 | 2522 | 0.0030 | 0.0188 | 4.1 | 0.1963 (n=104) | -0.0053 (n=2418) |
| 2.25 | `full` | `gated_30` | 9 | 1583 | -0.0191 | 0.0190 | 2.1 | n=33 <50 **withheld** | -0.0206 (n=1550) |
| 2.25 | `full` | `gated_50` | 9 | 2522 | -0.0152 | 0.0149 | 2.8 | 0.1654 (n=71) | -0.0205 (n=2451) |
| 2.25 | `full` | `gated_70` | 9 | 3474 | -0.0324 | 0.0125 | 3.5 | 0.0591 (n=121) | -0.0357 (n=3353) |
| 2.25 | `minus_rvol` | `ungated` | 9 | 4954 | -0.0417 | 0.0104 | 5.6 | -0.0048 (n=275) | -0.0439 (n=4679) |
| 2.25 | `minus_ema` | `gated_50` | 9 | 3229 | -0.0319 | 0.0127 | 2.8 | 0.1097 (n=89) | -0.0359 (n=3140) |
| 2.25 | `minus_time_stop` | `gated_50` | 9 | 2522 | 0.0038 | 0.0182 | 2.8 | 0.2380 (n=71) | -0.0030 (n=2451) |

## 7. Cells below an evidence minimum

Minimums, per symbol, **which do not move**: 200 per training fold, 50 per test fold, 30 per direction. Reported, never adjusted.

**64 of 7128 records fall short.** Rolled up by (symbol, arm, population, period, direction), since the raw list runs to thousands of rows:

| symbol | arm | population | period | direction | short cells | minimum | worst n | folds |
|---|---|---|---|---|---|---|---|---|
| BTCUSDT | `full` | `gated_30` | test | both | 8 | 50 | 45 | 4 |
| BTCUSDT | `full` | `gated_30` | test | long | 8 | 30 | 22 | 4 |
| BTCUSDT | `full` | `gated_30` | test | short | 16 | 30 | 21 | 4,6 |
| ETHUSDT | `full` | `gated_30` | test | both | 8 | 50 | 43 | 4 |
| ETHUSDT | `full` | `gated_30` | test | long | 8 | 30 | 18 | 4 |
| ETHUSDT | `full` | `gated_30` | test | short | 16 | 30 | 19 | 4,6 |

**Every shortfall sits on `gated_30`**, in `test` folds 4, 6, on BTCUSDT and ETHUSDT, arm `full`. Of these, **16 are `both` cells** (against the 50-trade test minimum) and 48 are direction cells (against 30).

That the 30% arm is where the counts run out is structural, not surprising: it is the most selective arm by construction, admitting roughly 30% of breakout bars, and folds 4 and 6 are the thinnest test periods. **No `gated_50` or `gated_70` cell falls short anywhere**, so the arm the full model runs on clears its minimum at every offset in every fold on every symbol.

Reported, not relaxed. §4.3's monotonicity test reads 70 → 50 → 30, so the thin end of that comparison carries less evidence than the other two arms and must be read that way at step 3. The minimums do not move to admit these cells.

## 8. Verification

| # | check | result |
|---|---|---|
| a | every figure carries a population label; a stripped label fails the guard | PASS — 6 planted mutations caught |
| b | gated arms are strict subsets of ungated, **by trade id** | PASS — and nested 70 ⊇ 50 ⊇ 30 |
| c | holdout seal and boundary exclusion active; report-13 mutation still passes | PASS |
| d | no trade originates before `train_start` in any fold | PASS |
| e | rerunning a cell reproduces bit-identical `r_multiple` | PASS |
| f | no `r_multiple` outside [-1.2, +2R + one tick] | PASS across all 1,188 backtests |
| g | full suite | PASS |

Check (f) runs inside the sweep itself, on every simulation, and raises rather than reporting — so a violation would have aborted the run rather than reaching this report.

## 9. Judgment calls

**1. Arm-to-population mapping.** `full` is reported at all three RVOL populations, because §4.3's 30/50/70 monotonicity test needs them. `minus_ema` and `minus_time_stop` are reported at `gated_50` only: D5 is a leave-one-out **against the full model**, and the full model is the 50% arm. Emitting them at 30 and 70 as well would multiply cells without feeding any pre-registered decision.

**2. Signals are generated once per (fold, symbol, period, EMA-variant) and reused at every offset.** A pure saving, not an approximation: signals depend on neither `stop_atr_mult` nor `stop_max_pct`, and a test asserts the signal set is invariant to both.

**3. `expectancy_per_bar_r` is total R over total bars held**, not the mean of per-trade R-per-bar. The two differ, and §4.5 does not say which. Total-over-total weights each bar of exposure equally, which is what "per bar" means when the metric exists to stop holding time silently inflating the per-trade figure.

**4. Appendix J stratification is applied at `direction=both` only.** Splitting each direction cell again by floor binding puts nearly every resulting cell below the minimums, so the stratified figure would be withheld almost everywhere and the table would carry no information. Per-direction figures are reported unstratified; the stratification is on the comparison Appendix J is about.

**5. A stratum is tested against its PERIOD minimum** (200 train / 50 test). Appendix J says "wherever both strata clear the evidence minimums" without naming which minimum applies to a stratum rather than a cell. The period minimum is the stricter available reading.

**6. The `breakout` population carries no expectancy here.** It is a BAR population, so a per-trade metric is undefined on it. Its counts and floor/cap binding rates are step 0 outputs and already live in `grid.json`; they are not restated. It remains in the closed label set so that any figure computed on it in a later step must say so.

**7. The exclusion counter accumulates across offset runs**, so the raw 35 for SOL fold 9 is 5 signals × 7 offsets. §5 reports the per-offset figure, which is the one that means anything.

## 10. Where I believe the specification is wrong or incomplete

**10.1 §4.5's arm-decomposition claim is false for two of its own five arms.** It states the five arms are "run in SIGNAL MODE (gated arms are filters of one ungated simulation, so all arms share an identical trade universe by construction)". That holds for the RVOL arms. It cannot hold for `minus_ema`, which is a strict superset — dropping the trend filter admits bars the baseline never generated — nor is it a filter for `minus_time_stop`, which needs re-simulation even though its universe is identical. The parenthetical over-claims. No decision depends on it, but a reader would reasonably infer that all five arms are cuts of one table, and they are not.

**10.2 The `minus_max_hold` arm is specified but not constructible.** §4.5 lists it as arm 5 and §4.4 requires max-hold be "measured and reported". Neither says how, and `max_hold_bars` is a read-only property with no registered alternative horizon. **This arm cannot be produced without a new free parameter**, and I have not invented one. Closing it requires a pre-committed holding horizon for the counterfactual — which, being post-lift, would have to be recorded as a decision made with results visible, exactly the status Appendix M carries.

**10.3 Appendix J does not say which minimum a STRATUM must clear.** See judgment call 5. The stricter reading was taken; the looser one (30, the per-direction minimum) would admit more stratified figures.

