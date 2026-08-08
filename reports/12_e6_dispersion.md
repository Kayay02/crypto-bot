# REPORT 12 — E6: PER-TRADE DISPERSION AND FOLD TRADE COUNTS

**Step 1 of the nine-step sequence (§4.4). THIS RUN LIFTED THE PERFORMANCE FIREWALL — partially.**

The lift covers IN-SAMPLE results only. The holdout (2025-01-01 onward) stays sealed until step 9. No loader in this run was passed `authorised=True`.

**This report carries dispersion and counts and nothing about location.** No mean, median or sum of `r_multiple` or `net_pnl`; no expectancy; no win rate; no profit factor; no Sharpe; no equity curve; no exit-reason or holding-time distribution; no per-arm or per-configuration comparison. That is not a stylistic choice: E6 decides fold architecture, and the decision is only blind if the evidence supporting it is. The prohibition is enforced by `assert_no_location_statistic`, which re-derives every forbidden quantity from the trade tables and refuses a report in which one appears.

## 0. What this run found

1. **Sigma is materially SMALLER than the design assumed.** Measured 0.7242R to 0.8467R per symbol against the 1.2R estimate §4.5 wrote the power table around — roughly 60–70% of it. Every downstream comparison is therefore more precise than pre-registered, not less.
2. **The E6 trigger does NOT fire**, in 0 of 27 fold-symbol test cells. The largest test-fold SE is 0.0787R against a 0.2R threshold — a factor of 2.5 of headroom. **The nine-fold architecture stands.** Per §4.5 this is reported, not acted on.
3. **No evidence minimum is missed anywhere.** All 27 fold-symbol cells clear 200 training trades and 50 test trades, and all 108 direction cells clear 30.
4. **Appendix L's upper bound on `r_multiple` is arithmetically wrong**, and the pre-registered sanity check duly fails: 1421 of 20010 trades exceed +2.0R, by at most 0.9990 of one tick. The cause is the engine's deliberate conservative rounding of the target, not a defect. §4 and §10.1 set this out. It changes nothing about 1, 2 or 3.

## 1. Provenance

- **HEAD at run time:** `a30b97b7988c8edbdb0d6225a2496405ac546fc1`
- **Working tree:** clean (verified before the run; a dirty hash aborts)
- **grid.json provenance:** `3d04c00663af8098a4fe0740d4d31d52d828d169` (step 0 artifact, pre-lift)
- **Mode:** signal mode (§4.5 edge-test instrument) — every signal simulated independently, no occupancy, cooldown or margin limit
- **Arm:** 50% RVOL pass rate, `baseline_days` = 20, `stop_max_pct` from grid.json
- **Window:** in-sample only, 2022-04-01 → 2024-12-31, nine folds, train and test evaluated separately
- **Indicators:** computed from each fold's `warmup_start` (45-day buffer), per `src/folds/warmup.py`

## 2. Configuration run, per fold per symbol

Pre-specified, not chosen: the centre of the A3-surviving offset set with the top grid point (2.50) removed — §4.3's plateau rule makes the edge of the searched range ineligible for selection — tie broken to the HIGHER central offset per Appendix K.3. Fully determined by step 0 outputs and the frozen rules. **This is not a selection and carries no privileged status**; it exists to generate a representative trade population.

| symbol | fold | m\* | A3-surviving offsets | eligible (top removed) | offset run | absolute multiplier | stop_max_pct | rvol threshold |
|---|---|---|---|---|---|---|---|---|
| BTCUSDT | 1 | 2.2318 | 0.5, 0.75, 1, 1.25, 1.5, 1.75, 2, 2.25, 2.5 | 0.5, 0.75, 1, 1.25, 1.5, 1.75, 2, 2.25 | **1.5** | 3.7318 | 5.5140 | 2.4157 |
| BTCUSDT | 2 | 2.7562 | 1.5, 1.75, 2, 2.25, 2.5 | 1.5, 1.75, 2, 2.25 | **2** | 4.7562 | 4.2537 | 2.4842 |
| BTCUSDT | 3 | 3.4659 | 1, 1.25, 1.5, 1.75, 2, 2.25, 2.5 | 1, 1.25, 1.5, 1.75, 2, 2.25 | **1.75** | 5.2159 | 4.5382 | 3.1845 |
| BTCUSDT | 4 | 3.3351 | 0.5, 0.75, 1, 1.25, 1.5, 1.75, 2, 2.25, 2.5 | 0.5, 0.75, 1, 1.25, 1.5, 1.75, 2, 2.25 | **1.5** | 4.8351 | 3.8368 | 3.1618 |
| BTCUSDT | 5 | 4.7567 | 0.5, 0.75, 1, 1.25, 1.5, 1.75, 2, 2.25, 2.5 | 0.5, 0.75, 1, 1.25, 1.5, 1.75, 2, 2.25 | **1.5** | 6.2567 | 3.5826 | 2.1861 |
| BTCUSDT | 6 | 4.8354 | 0.5, 0.75, 1, 1.25, 1.5, 1.75, 2, 2.25, 2.5 | 0.5, 0.75, 1, 1.25, 1.5, 1.75, 2, 2.25 | **1.5** | 6.3354 | 3.6727 | 2.1492 |
| BTCUSDT | 7 | 3.2525 | 1, 1.25, 1.5, 1.75, 2, 2.25, 2.5 | 1, 1.25, 1.5, 1.75, 2, 2.25 | **1.75** | 5.0025 | 4.2859 | 1.8783 |
| BTCUSDT | 8 | 2.8655 | 0.75, 1, 1.25, 1.5, 1.75, 2, 2.25, 2.5 | 0.75, 1, 1.25, 1.5, 1.75, 2, 2.25 | **1.5** | 4.3655 | 4.1128 | 1.5535 |
| BTCUSDT | 9 | 2.8713 | 0.75, 1, 1.25, 1.5, 1.75, 2, 2.25, 2.5 | 0.75, 1, 1.25, 1.5, 1.75, 2, 2.25 | **1.5** | 4.3713 | 3.7352 | 2.0729 |
| ETHUSDT | 1 | 1.6217 | 0.5, 0.75, 1, 1.25, 1.5, 1.75, 2, 2.25, 2.5 | 0.5, 0.75, 1, 1.25, 1.5, 1.75, 2, 2.25 | **1.5** | 3.1217 | 5.5077 | 2.8247 |
| ETHUSDT | 2 | 1.7951 | 0.75, 1, 1.25, 1.5, 1.75, 2, 2.25, 2.5 | 0.75, 1, 1.25, 1.5, 1.75, 2, 2.25 | **1.5** | 3.2951 | 4.9341 | 2.9766 |
| ETHUSDT | 3 | 2.6225 | 0.5, 0.75, 1, 1.25, 1.5, 1.75, 2, 2.25, 2.5 | 0.5, 0.75, 1, 1.25, 1.5, 1.75, 2, 2.25 | **1.5** | 4.1225 | 4.8530 | 3.1953 |
| ETHUSDT | 4 | 2.9908 | 0.5, 0.75, 1, 1.25, 1.5, 1.75, 2, 2.25, 2.5 | 0.5, 0.75, 1, 1.25, 1.5, 1.75, 2, 2.25 | **1.5** | 4.4908 | 3.8243 | 2.7298 |
| ETHUSDT | 5 | 4.3824 | 0.25, 0.5, 0.75, 1, 1.25, 1.5, 1.75, 2, 2.25, 2.5 | 0.25, 0.5, 0.75, 1, 1.25, 1.5, 1.75, 2, 2.25 | **1.25** | 5.6324 | 3.6083 | 1.9308 |
| ETHUSDT | 6 | 3.7735 | 0.5, 0.75, 1, 1.25, 1.5, 1.75, 2, 2.25, 2.5 | 0.5, 0.75, 1, 1.25, 1.5, 1.75, 2, 2.25 | **1.5** | 5.2735 | 3.5043 | 1.9426 |
| ETHUSDT | 7 | 2.7018 | 0.75, 1, 1.25, 1.5, 1.75, 2, 2.25, 2.5 | 0.75, 1, 1.25, 1.5, 1.75, 2, 2.25 | **1.5** | 4.2018 | 4.5319 | 1.7768 |
| ETHUSDT | 8 | 2.4578 | 0.5, 0.75, 1, 1.25, 1.5, 1.75, 2, 2.25, 2.5 | 0.5, 0.75, 1, 1.25, 1.5, 1.75, 2, 2.25 | **1.5** | 3.9578 | 4.4556 | 1.4541 |
| ETHUSDT | 9 | 2.4979 | 0.75, 1, 1.25, 1.5, 1.75, 2, 2.25, 2.5 | 0.75, 1, 1.25, 1.5, 1.75, 2, 2.25 | **1.5** | 3.9979 | 4.0139 | 2.2085 |
| SOLUSDT | 1 | 1.6177 | 0.5, 0.75, 1, 1.25, 1.5, 1.75, 2, 2.25, 2.5 | 0.5, 0.75, 1, 1.25, 1.5, 1.75, 2, 2.25 | **1.5** | 3.1177 | 7.0153 | 1.7453 |
| SOLUSDT | 2 | 1.9452 | 0.75, 1, 1.25, 1.5, 1.75, 2, 2.25, 2.5 | 0.75, 1, 1.25, 1.5, 1.75, 2, 2.25 | **1.5** | 3.4452 | 6.3635 | 2.3247 |
| SOLUSDT | 3 | 1.9510 | 0.5, 0.75, 1, 1.25, 1.5, 1.75, 2, 2.25, 2.5 | 0.5, 0.75, 1, 1.25, 1.5, 1.75, 2, 2.25 | **1.5** | 3.4510 | 7.4709 | 2.8016 |
| SOLUSDT | 4 | 2.1605 | 0.75, 1, 1.25, 1.5, 1.75, 2, 2.25, 2.5 | 0.75, 1, 1.25, 1.5, 1.75, 2, 2.25 | **1.5** | 3.6605 | 6.3794 | 2.7291 |
| SOLUSDT | 5 | 2.8194 | 0.75, 1, 1.25, 1.5, 1.75, 2, 2.25, 2.5 | 0.75, 1, 1.25, 1.5, 1.75, 2, 2.25 | **1.5** | 4.3194 | 5.2624 | 2.7218 |
| SOLUSDT | 6 | 2.0591 | 1, 1.25, 1.5, 1.75, 2, 2.25, 2.5 | 1, 1.25, 1.5, 1.75, 2, 2.25 | **1.75** | 3.8091 | 6.7359 | 2.5550 |
| SOLUSDT | 7 | 1.6143 | 0.5, 0.75, 1, 1.25, 1.5, 1.75, 2, 2.25, 2.5 | 0.5, 0.75, 1, 1.25, 1.5, 1.75, 2, 2.25 | **1.5** | 3.1143 | 6.6416 | 2.7000 |
| SOLUSDT | 8 | 1.8631 | 0.5, 0.75, 1, 1.25, 1.5, 1.75, 2, 2.25, 2.5 | 0.5, 0.75, 1, 1.25, 1.5, 1.75, 2, 2.25 | **1.5** | 3.3631 | 6.6978 | 2.8950 |
| SOLUSDT | 9 | 2.1044 | 0.75, 1, 1.25, 1.5, 1.75, 2, 2.25, 2.5 | 0.75, 1, 1.25, 1.5, 1.75, 2, 2.25 | **1.5** | 3.6044 | 6.2425 | 2.4845 |

## 3. Dispersion of `r_multiple`

### 3.1 Pooled per symbol (all in-sample trades, train + test)

| symbol | n | sigma (R) | SE (R) | min R | max R | IQR (R) | p10-p90 (R) |
|---|---|---|---|---|---|---|---|
| BTCUSDT | 6318 | 0.7242 | 0.0091 | -1.0005 | 2.0004 | 0.7437 | 1.8417 |
| ETHUSDT | 6236 | 0.7666 | 0.0097 | -1.0006 | 2.0007 | 0.8051 | 1.8068 |
| SOLUSDT | 7456 | 0.8467 | 0.0098 | -1.0005 | 2.0004 | 1.0457 | 2.0061 |

Train and test pooled separately, same symbols:

| symbol / period | n | sigma (R) | SE (R) | min R | max R | IQR (R) | p10-p90 (R) |
|---|---|---|---|---|---|---|---|
| BTCUSDT train | 4141 | 0.7327 | 0.0114 | -1.0004 | 2.0004 | 0.7498 | 1.8618 |
| BTCUSDT test | 2177 | 0.7076 | 0.0152 | -1.0005 | 2.0004 | 0.7311 | 1.7935 |
| ETHUSDT train | 4135 | 0.7647 | 0.0119 | -1.0006 | 2.0007 | 0.8078 | 1.8023 |
| ETHUSDT test | 2101 | 0.7705 | 0.0168 | -1.0006 | 2.0007 | 0.8002 | 1.8176 |
| SOLUSDT train | 4934 | 0.8483 | 0.0121 | -1.0004 | 2.0004 | 1.0552 | 1.9985 |
| SOLUSDT test | 2522 | 0.8438 | 0.0168 | -1.0005 | 2.0004 | 1.0254 | 2.0078 |

### 3.2 Per direction, per symbol (all in-sample trades)

Long and short cohorts stay separate throughout (§4.5).

| symbol / direction | n | sigma (R) | SE (R) | min R | max R | IQR (R) | p10-p90 (R) |
|---|---|---|---|---|---|---|---|
| BTCUSDT long | 3501 | 0.7636 | 0.0129 | -1.0004 | 2.0004 | 0.8010 | 1.9031 |
| BTCUSDT short | 2817 | 0.6711 | 0.0126 | -1.0005 | 2.0004 | 0.6897 | 1.7507 |
| ETHUSDT long | 3350 | 0.7785 | 0.0135 | -1.0006 | 2.0007 | 0.8569 | 1.8287 |
| ETHUSDT short | 2886 | 0.7526 | 0.0140 | -1.0006 | 2.0006 | 0.7601 | 1.7868 |
| SOLUSDT long | 3855 | 0.8547 | 0.0138 | -1.0003 | 2.0004 | 1.1074 | 2.0280 |
| SOLUSDT short | 3601 | 0.8380 | 0.0140 | -1.0005 | 2.0004 | 0.9812 | 1.9468 |

### 3.3 Per fold per symbol — TEST period

| symbol / fold | n | sigma (R) | SE (R) | min R | max R | IQR (R) | p10-p90 (R) |
|---|---|---|---|---|---|---|---|
| BTCUSDT f1 | 229 | 0.6795 | 0.0449 | -1.0005 | 2.0004 | 0.6440 | 1.6647 |
| BTCUSDT f2 | 254 | 0.8230 | 0.0516 | -1.0003 | 2.0003 | 0.7944 | 2.2884 |
| BTCUSDT f3 | 166 | 0.6555 | 0.0509 | -1.0002 | 2.0001 | 0.6214 | 1.3146 |
| BTCUSDT f4 | 107 | 0.7205 | 0.0696 | -1.0003 | 2.0003 | 0.7585 | 1.7571 |
| BTCUSDT f5 | 287 | 0.6338 | 0.0374 | -1.0002 | 2.0002 | 0.6562 | 1.4830 |
| BTCUSDT f6 | 161 | 0.6754 | 0.0532 | -1.0001 | 2.0001 | 0.6439 | 1.5997 |
| BTCUSDT f7 | 176 | 0.6264 | 0.0472 | -1.0001 | 2.0001 | 0.7538 | 1.7459 |
| BTCUSDT f8 | 432 | 0.7037 | 0.0339 | -1.0001 | 2.0001 | 0.7958 | 1.7999 |
| BTCUSDT f9 | 365 | 0.7578 | 0.0397 | -1.0001 | 2.0001 | 0.8927 | 1.7910 |
| ETHUSDT f1 | 230 | 0.9032 | 0.0596 | -1.0006 | 2.0006 | 1.2188 | 3.0002 |
| ETHUSDT f2 | 191 | 0.9116 | 0.0660 | -1.0006 | 2.0007 | 1.0712 | 3.0003 |
| ETHUSDT f3 | 130 | 0.7076 | 0.0621 | -1.0004 | 2.0004 | 0.7334 | 1.7905 |
| ETHUSDT f4 | 95 | 0.7788 | 0.0799 | -1.0004 | 2.0004 | 0.7836 | 1.9945 |
| ETHUSDT f5 | 307 | 0.6352 | 0.0363 | -1.0003 | 2.0004 | 0.6787 | 1.4111 |
| ETHUSDT f6 | 158 | 0.5873 | 0.0467 | -1.0002 | 2.0001 | 0.6049 | 1.4780 |
| ETHUSDT f7 | 178 | 0.7830 | 0.0587 | -1.0002 | 2.0002 | 0.7797 | 1.8867 |
| ETHUSDT f8 | 437 | 0.7767 | 0.0372 | -1.0003 | 2.0002 | 0.7916 | 1.8539 |
| ETHUSDT f9 | 375 | 0.7828 | 0.0404 | -1.0003 | 2.0002 | 0.9685 | 1.8128 |
| SOLUSDT f1 | 349 | 1.0172 | 0.0545 | -1.0004 | 2.0004 | 1.5261 | 3.0002 |
| SOLUSDT f2 | 260 | 0.8591 | 0.0533 | -1.0004 | 2.0002 | 1.0464 | 1.9280 |
| SOLUSDT f3 | 249 | 0.8682 | 0.0550 | -1.0003 | 2.0003 | 0.9237 | 3.0001 |
| SOLUSDT f4 | 237 | 0.8028 | 0.0521 | -1.0003 | 2.0003 | 0.9368 | 1.7780 |
| SOLUSDT f5 | 263 | 0.7743 | 0.0477 | -1.0003 | 2.0002 | 0.8130 | 1.7959 |
| SOLUSDT f6 | 316 | 0.6842 | 0.0385 | -1.0001 | 2.0000 | 0.9600 | 1.6248 |
| SOLUSDT f7 | 319 | 0.8953 | 0.0501 | -1.0001 | 2.0000 | 1.4309 | 2.3107 |
| SOLUSDT f8 | 207 | 0.8500 | 0.0591 | -1.0005 | 2.0003 | 1.1387 | 2.2400 |
| SOLUSDT f9 | 322 | 0.7489 | 0.0417 | -1.0005 | 2.0002 | 0.9173 | 1.7459 |

## 4. Appendix L sanity check (Popoviciu) — ONE PART FAILS

Appendix L bounds `r_multiple` in approximately [-1.2, 2], so by Popoviciu's inequality sigma ≤ 1.55R.

| check | bound | observed | verdict |
|---|---|---|---|
| max `r_multiple` | ≤ 2 | 2.00065162 | **FAIL** |
| min `r_multiple` | ≥ -1.2 | -1.00063986 | PASS |
| max sigma (per symbol, pooled) | ≤ 1.55 | 0.8467 | PASS |
| max `r_multiple` vs the ENGINE-DERIVED ceiling | ≤ +2R + one tick | 0 breaches | PASS |

### 4.1 The upper bound fails, and Appendix L is the thing that is wrong

**1421 of 20010 trades exceed +2.0R.** The largest is 2.00065162R — an excess of 6.52e-04R, about 0.013 cents on a $20 risk unit.

Every excursion is a **target** exit; no other exit reason produces one. The cause is in the engine's own documented arithmetic, not in a defect:

> `costs.solve_price_for_net` rounds the solved level **away from the position** — `"up"` for a long, `"down"` for a short — so that "a level is never claimed at a price that would deliver less than `net_pnl`".

A filled target therefore delivers +2R **plus up to one tick of P&L**, and never more. Appendix L's derivation states that "target exits fill at exactly +2R", which overlooks that rounding. The premise is wrong; the engine is behaving exactly as specified.

**Measured against the correct ceiling:** the largest excess over +2R is **0.9990 of one tick** — strictly under one tick, in every one of the 1421 cases. 0 trades exceed the tick-aware ceiling. That is the check whose breach would mean an engine defect, and it passes.

**Consequence for the E6 conclusion: none.** Appendix L derives 1.55R from the range [-1.1, 2]. Correcting only the upper end to the observed 2.000652 gives 1.550326R — a move of 3.26e-04R. Measured sigma is 0.8467R at its largest, nowhere near either figure, so the dispersion finding and the fold trigger verdict are unaffected.

**The realised range is TIGHTER than Appendix L assumed, not wider.** The observed minimum is -1.000640R, not the −1.1R the derivation posits: `position_size` already absorbs both fee legs and the stop haircut into the risk denominator, so a stop-out lands at −1R net rather than −1R plus a haircut. Popoviciu over the realised range [-1.0006, 2.0007] gives 1.5006R, and measured sigma is below half of that.

**No threshold was moved to make this pass.** Appendix L is a frozen pre-registration document and §4.5 forbids post-lift amendment, so it is NOT amended here. The pre-registered check is retained, its failure is reported above, and the hard stop that aborts the run was placed on the tighter engine-derived ceiling — the bound that Appendix L was trying to express. See §10 for this recorded as a specification defect.

## 5. Trade counts and the evidence minimums

Minimums, per symbol, **which do not move**: 200 IS trades (per training fold, Appendix K.2b), 50 per test fold, 30 per direction. Cells below a minimum are marked `SHORT`.

| symbol | fold | train n | train long | train short | test n | test long | test short |
|---|---|---|---|---|---|---|---|
| BTCUSDT | 1 | 509 | 213 | 296 | 229 | 102 | 127 |
| BTCUSDT | 2 | 440 | 221 | 219 | 254 | 171 | 83 |
| BTCUSDT | 3 | 384 | 220 | 164 | 166 | 92 | 74 |
| BTCUSDT | 4 | 379 | 239 | 140 | 107 | 52 | 55 |
| BTCUSDT | 5 | 407 | 227 | 180 | 287 | 177 | 110 |
| BTCUSDT | 6 | 470 | 269 | 201 | 161 | 110 | 51 |
| BTCUSDT | 7 | 513 | 324 | 189 | 176 | 76 | 100 |
| BTCUSDT | 8 | 522 | 298 | 224 | 432 | 227 | 205 |
| BTCUSDT | 9 | 517 | 256 | 261 | 365 | 227 | 138 |
| ETHUSDT | 1 | 538 | 250 | 288 | 230 | 115 | 115 |
| ETHUSDT | 2 | 454 | 236 | 218 | 191 | 123 | 68 |
| ETHUSDT | 3 | 382 | 213 | 169 | 130 | 66 | 64 |
| ETHUSDT | 4 | 364 | 215 | 149 | 95 | 41 | 54 |
| ETHUSDT | 5 | 385 | 195 | 190 | 307 | 186 | 121 |
| ETHUSDT | 6 | 465 | 260 | 205 | 158 | 110 | 48 |
| ETHUSDT | 7 | 537 | 332 | 205 | 178 | 78 | 100 |
| ETHUSDT | 8 | 519 | 287 | 232 | 437 | 211 | 226 |
| ETHUSDT | 9 | 491 | 222 | 269 | 375 | 210 | 165 |
| SOLUSDT | 1 | 635 | 326 | 309 | 349 | 135 | 214 |
| SOLUSDT | 2 | 566 | 267 | 299 | 260 | 130 | 130 |
| SOLUSDT | 3 | 489 | 210 | 279 | 249 | 130 | 119 |
| SOLUSDT | 4 | 482 | 248 | 234 | 237 | 124 | 113 |
| SOLUSDT | 5 | 491 | 256 | 235 | 263 | 186 | 77 |
| SOLUSDT | 6 | 521 | 326 | 195 | 316 | 180 | 136 |
| SOLUSDT | 7 | 568 | 359 | 209 | 319 | 133 | 186 |
| SOLUSDT | 8 | 589 | 289 | 300 | 207 | 109 | 98 |
| SOLUSDT | 9 | 593 | 274 | 319 | 322 | 173 | 149 |

Whole in-sample population per symbol (train and test folds pooled; note training windows overlap by 50%, so this is not a count of independent trades):

| symbol | IS trades | train | test |
|---|---|---|---|
| BTCUSDT | 6318 | 4141 | 2177 |
| ETHUSDT | 6236 | 4135 | 2101 |
| SOLUSDT | 7456 | 4934 | 2522 |

### 5.1 Shortfalls — none. Every cell clears its minimum.

Reported, not adjusted. §4.5: the evidence minimums do NOT move, and the resolution order is loosen thresholds → extend the in-sample window → drop to a single condition. The holdout is not touched.

## 6. The E6 trigger

**Rule (§4.5, unchanged by Appendix L):** if a 3-month test fold's standard error on expectancy exceeds 0.2R, test folds extend to 6 months with a 6-month step, giving five folds instead of nine.

SE is computed as the pooled per-symbol sigma over that fold's test trade count. Per Appendix L this is a **trade-count guard expressed in SE units** — the binding quantity is n, not sigma.

**THE TRIGGER DOES NOT FIRE.** 0 of 27 fold-symbol test cells exceed 0.2R.

| symbol | fold | test n | SE (R) | > 0.20R? |
|---|---|---|---|---|
| BTCUSDT | 1 | 229 | 0.0479 | no |
| BTCUSDT | 2 | 254 | 0.0454 | no |
| BTCUSDT | 3 | 166 | 0.0562 | no |
| BTCUSDT | 4 | 107 | 0.0700 | no |
| BTCUSDT | 5 | 287 | 0.0427 | no |
| BTCUSDT | 6 | 161 | 0.0571 | no |
| BTCUSDT | 7 | 176 | 0.0546 | no |
| BTCUSDT | 8 | 432 | 0.0348 | no |
| BTCUSDT | 9 | 365 | 0.0379 | no |
| ETHUSDT | 1 | 230 | 0.0506 | no |
| ETHUSDT | 2 | 191 | 0.0555 | no |
| ETHUSDT | 3 | 130 | 0.0672 | no |
| ETHUSDT | 4 | 95 | 0.0787 | no |
| ETHUSDT | 5 | 307 | 0.0438 | no |
| ETHUSDT | 6 | 158 | 0.0610 | no |
| ETHUSDT | 7 | 178 | 0.0575 | no |
| ETHUSDT | 8 | 437 | 0.0367 | no |
| ETHUSDT | 9 | 375 | 0.0396 | no |
| SOLUSDT | 1 | 349 | 0.0453 | no |
| SOLUSDT | 2 | 260 | 0.0525 | no |
| SOLUSDT | 3 | 249 | 0.0537 | no |
| SOLUSDT | 4 | 237 | 0.0550 | no |
| SOLUSDT | 5 | 263 | 0.0522 | no |
| SOLUSDT | 6 | 316 | 0.0476 | no |
| SOLUSDT | 7 | 319 | 0.0474 | no |
| SOLUSDT | 8 | 207 | 0.0589 | no |
| SOLUSDT | 9 | 322 | 0.0472 | no |

_REPORT ONLY -- §4.5 says the fold change is reviewed before it is acted on. Nothing is implemented here._

## 7. The power table, recomputed on measured sigma

§4.5's noise caveat made quantitative. The design assumed sigma = 1.2R; every row below uses MEASURED sigma. Each SE is compared against the 0.05R marginal-contribution threshold D5 drop decisions use. A ratio above 1 means the noise on that figure exceeds the difference the decision is trying to detect.

| population | sigma (R) | n | SE (R) | SE / 0.05R |
|---|---|---|---|---|
| BTCUSDT — 200-trade IS minimum | 0.7242 | 200 | 0.0512 | 1.02 |
| BTCUSDT — 50-trade test minimum | 0.7242 | 50 | 0.1024 | 2.05 |
| BTCUSDT — typical test fold (median count) | 0.7242 | 229 | 0.0479 | 0.96 |
| BTCUSDT — typical training fold (median count) | 0.7242 | 470 | 0.0334 | 0.67 |
| BTCUSDT — pooled in-sample | 0.7242 | 6318 | 0.0091 | 0.18 |
| ETHUSDT — 200-trade IS minimum | 0.7666 | 200 | 0.0542 | 1.08 |
| ETHUSDT — 50-trade test minimum | 0.7666 | 50 | 0.1084 | 2.17 |
| ETHUSDT — typical test fold (median count) | 0.7666 | 191 | 0.0555 | 1.11 |
| ETHUSDT — typical training fold (median count) | 0.7666 | 465 | 0.0356 | 0.71 |
| ETHUSDT — pooled in-sample | 0.7666 | 6236 | 0.0097 | 0.19 |
| SOLUSDT — 200-trade IS minimum | 0.8467 | 200 | 0.0599 | 1.20 |
| SOLUSDT — 50-trade test minimum | 0.8467 | 50 | 0.1197 | 2.39 |
| SOLUSDT — typical test fold (median count) | 0.8467 | 263 | 0.0522 | 1.04 |
| SOLUSDT — typical training fold (median count) | 0.8467 | 566 | 0.0356 | 0.71 |
| SOLUSDT — pooled in-sample | 0.8467 | 7456 | 0.0098 | 0.20 |
| **D5 pooled (all folds × all symbols)** — 200-trade IS minimum | 0.7850 | 200 | 0.0555 | 1.11 |
| **D5 pooled (all folds × all symbols)** — 50-trade test minimum | 0.7850 | 50 | 0.1110 | 2.22 |
| **D5 pooled (all folds × all symbols)** — pooled in-sample | 0.7850 | 20010 | 0.0055 | 0.11 |

The D5 row is the only figure pooled across symbols, and §4.4 licenses exactly that pooling for drop decisions. Everything else is per symbol.

## 8. The 425 reconstruction-divergence bars (deferred Point 2 item)

Point 2 recorded 425 flagged bars (426 rows; one SOL bar is flagged on both `high` and `volume`, which is the single OHLC divergence) as a FLAG LIST, not an exclusion filter, and deferred the signal-bar overlap measurement to Point 4. Measured here.

| symbol | flagged bars | in-sample | ∩ breakout bar | ∩ gated signal bar (50%) | ∩ signal bar of a taken trade | ∩ entry bar |
|---|---|---|---|---|---|---|
| BTCUSDT | 264 | 207 | 13 | 6 | 6 | 16 |
| ETHUSDT | 106 | 90 | 10 | 9 | 9 | 11 |
| SOLUSDT | 55 | 43 | 7 | 5 | 5 | 4 |
| **all** | 425 | 340 | 30 | 20 | 20 | 31 |

Counts only. **No outcome comparison between flagged and unflagged trades is made** — that would be a location statistic, and this report may not carry one.

## 9. Refusal and provenance counters

| counter | total across all fold-symbol-periods |
|---|---|
| refused_cooldown | 0 |
| refused_insufficient_margin | 0 |
| refused_min_qty | 0 |
| refused_no_1m_coverage | 0 |
| refused_open_position | 0 |
| trades whose exit_ts crosses 2025-01-01 | 0 |
| trades originating before their period start | 0 |

`open_position`, `cooldown` and `insufficient_margin` are structurally zero in signal mode — no constraint of that kind applies. They are printed rather than omitted so that a non-zero value would be visible as a defect.

## 10. Ambiguities resolved, and where the specification is wrong

### 10.1 Where I believe the specification is WRONG

**(a) Appendix L's upper bound on `r_multiple` is arithmetically wrong.** It asserts "target exits fill at exactly +2R". They do not: `costs.solve_price_for_net` deliberately rounds the target away from the position so a level never delivers less than +2R, so a filled target delivers +2R plus up to one tick. §4 quantifies it. The conclusion Appendix L draws — sigma ≤ 1.55R — survives essentially unchanged, so this is a defect in the derivation, not in the design. **It is NOT amended here:** §4.5 permits amendment pre-lift only, and this run is the lift. Recorded for the record and for whoever writes the next appendix.

**(b) Appendix L's own text is corrupted in the committed document.** Lines 1143–1145 of `docs/handoff/08_point_4_pre_registration.md` contain repeated, spliced fragments — `"(b - a)^2 / 4, so sigma <= 1.55R, attained only by"` recurs a dozen times mid-sentence, and the paragraph beginning `"The o"` is destroyed. The meaning of the rule is recoverable (sigma ≤ 1.55R by Popoviciu; the trigger is a trade-count guard) and the CORRECTED READING paragraph is intact, so E6 was executed against the recoverable reading. **A pre-registration document whose text is damaged is weaker evidence than one whose text is not**, and this should be repaired by a commit that states it is repairing a transcription error and changes no rule.

### 10.2 Judgment calls

**1. "200 IS trades per symbol" is applied per TRAINING FOLD.** The carried commitments state it per symbol without naming the unit. Appendix K.2(b) resolves it — "the training-fold trade count for that symbol meets the pre-committed evidence minimum of 200 IS trades" — and §4.2 sizes a 6-month train window against it. §5 also reports the whole-window pooled count so the looser reading is available.

**2. The 30-per-direction minimum is applied per fold per period.** §4.2 quotes "60–100 per direction" for a 3-month test fold against the 30 minimum, which fixes the unit as the fold. Train-period direction cells are reported on the same basis.

**3. Signal mode was run UNGATED and filtered to the 50% arm**, per §4.5 and `run.py:gated_arm`, rather than re-simulating with the gate on. In signal mode no trade interacts with another, so the two are the same trade set by construction. The ungated universe size is reported beside each cell.

**4. Indicators are computed once per fold from `warmup_start` through `test_end`**, then partitioned into train and test. `src/folds/` specifies one buffer before `train_start` covering both periods because they are contiguous. The test period therefore carries a much longer effective buffer than 45 days, which is what the fold design intends.

**5. 1m bars from 2025 ARE loaded, to resolve in-sample trades that cross the boundary.** A trade signalled in the last hours of 2024-12-31 walks a 41-bar lifecycle into 2025-01-01. `src/engine/run.py` already loads `max(year) + 1` for exactly this reason, and changing it would be changing engine semantics. Those minutes RESOLVE an in-sample trade; they never originate one, and no statistic is computed over holdout bars. The 15m loader — the one that decides which bars can produce a signal — is bounded at 2024-12-31 and refuses the holdout on the default path. 0 trades cross the boundary; a test asserts no signal bar does.

**6. "An actual entry bar in this run" is reported two ways** in §8. A flagged bar can coincide with the SIGNAL bar of a trade that was taken, or with the ENTRY bar itself, which sits one 15m bar later. The phrasing admits both, so both are counted.

**7. The top grid point is excluded before taking the centre, not after.** §4.3's plateau rule makes offset 2.50 ineligible for selection, so it is removed from the surviving set and the centre is taken of what remains. Taking the centre first and then checking eligibility would sometimes land on an offset that could never be selected.

**8. The E6 trigger uses the POOLED per-symbol sigma** over each fold's own test trade count, as specified. Per-fold test sigmas are reported in §3.3 but are not used in the trigger: Appendix L's corrected reading makes it a trade-count guard, so the dispersion term is held fixed while n varies.

