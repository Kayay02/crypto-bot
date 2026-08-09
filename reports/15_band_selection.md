# REPORT 15 — BAND IDENTIFICATION AND PLATEAU SELECTION (step 3 of the §4.4 sequence)

Applies Appendix K.2's acceptance definition to every A3-eligible grid point, identifies contiguous passing bands per fold per symbol, selects the centre of the widest band per §4.3 and Appendix K.3, and evaluates the pre-committed kill conditions that step 3 makes decidable.

**THIS TASK STOPS AT STEP 3.** No collapse of the nine fold selections into a candidate (step 4), no A3 re-check (step 5, resolved at step 0), no D5 leave-one-out (step 7), no top-5% winner removal and no ±25% sensitivity probe (step 8).

**The holdout remains SEALED.** Nothing here opens a bar file. Every figure is derived from the step-2 cells and step-2 trade tables, so no re-simulation occurred and the report-13 seal was not exercised. No call in this module passes `authorised=True` — the flag is never set anywhere in the analysis code — and a test asserts it.

---

## 0. THE HEADLINE: THE PRE-COMMITTED KILL CONDITIONS FIRE

Stated first and without hedging, because that is what a pre-registration is for.

| kill condition | BTCUSDT | ETHUSDT | SOLUSDT |
|---|---|---|---|
| **(a)** OOS expectancy ≤ 0 after costs | **FIRES** | **FIRES** | does not fire |
| **(b)** gate contributes < 0.05R — decorative | **FIRES** | **FIRES** | does not fire |
| **(c)** ungated outperforms gated — thesis backwards | does not fire | does not fire | does not fire |
| **(d)** two-of-three qualification | **FAILS** | **FAILS** | **FAILS** |

**NO SYMBOL PRODUCES A CANDIDATE FOR STEP 4.** Two-of-three fails outright: exactly 1 of three symbols shows the §4.4 direction of edge, and the rule requires a symbol to show it **and** be corroborated by another. A rule needing two symbols cannot be satisfied by one.

Per §5 of the task specification and §4.3/§4.4 of the pre-registration, the procedure is exhausted and that is the finding. No variant is searched, no threshold relaxed, no range extended, no alternative configuration proposed.

---

## 1. Provenance

| item | value |
|---|---|
| HEAD at the start of step 3 | `bdde2a4188606162f08c9442e3aaa69e59d2a265` |
| Working tree at that point | **clean** (`git status --porcelain` empty) |
| Step-2 sweep commit | `c9220948221613b154cb6cd249d01d14789f452e` |
| Cells consumed | `data/derived/sweep/sweep_cells.jsonl` |
| Trade tables consumed | `data/derived/sweep/trades` |
| Re-simulation | **none** — see §1.1 |
| Artifact written | `data/derived/sweep/bands.json` |

### 1.1 No re-simulation was necessary

The task anticipated that Appendix K.2's TRAINING-fold figures might not exist in `sweep.json`. They do. Step 2 emitted every cell crossed with `train`/`test`, so the acceptance population — arm `full`, population `gated_50`, period `train`, direction `both` — is read directly from `sweep_cells.jsonl`. No engine call was made and no bar file was opened, so the question of proving bit-identical reproduction does not arise.

**This is a different population from the one report 14 §6 tabulates.** Report 14 pools TEST folds only, per Appendix M.4, because that is the correct population for ARM COMPARISON. Acceptance is a TRAINING-fold quantity, because selection is on train and evaluation is on test. No figure from report 14 §6 is reused for acceptance; §8(a) below records the guard that makes crossing them raise rather than compute.

## 2. The population contract

Every figure below names its population from the closed set (`ungated`, `breakout`, `gated_30`, `gated_50`, `gated_70`) crossed with (`train`, `test`) and (`long`, `short`, `both`). The step-2 validator `sweep.validate_records` is **reused, not reimplemented**, and runs over the cells before anything is read from them; a test re-plants the step-2 mutation of stripping a label through step 3's entry point.

| quantity | population | period | direction | arm |
|---|---|---|---|---|
| acceptance expectancy, SE, trade count (K.2a, K.2b) | `gated_50` | `train` | `both` | `full` |
| band identification and plateau selection | `gated_50` | `train` | `both` | `full` |
| kill (a) OOS expectancy | `gated_50` | `test` | `both` | `full` |
| kill (b)/(c)/(d) gated-vs-ungated | `gated_50` vs `ungated` | `test` | `both` | `full` vs `minus_rvol` |
| diagnostics (§7) | `gated_50` | `test` | `both` | `full`, `minus_time_stop` |

## 3. Acceptance per grid point (Appendix K.2)

**Population: `gated_50`, period `train`, direction `both`, arm `full`.** A grid point passes when all of:

- **(a)** training-fold expectancy per trade in R, net of costs, is **greater than zero**. No margin. No significance test. Zero is not greater than zero, and a test asserts that.
- **(b)** the training-fold trade count meets the 200-trade evidence minimum, applied per training fold.
- **(c)** the grid point survives A3, established at step 0.

**198** (fold, symbol, offset) cells evaluated; **38** pass. Clause (b) fails **0** times — every training fold clears 200 gated_50 trades comfortably (range 364–635), so acceptance is decided entirely by clause (a). Clause (c) is true by construction: offsets that fail A3 were never simulated.

Offsets are **offsets from m\***. The absolute multiplier is given alongside because m\* moves by a factor of 2.2 across folds and the two are not interchangeable.

### 3.1 BTCUSDT — train, `gated_50`, `both`

| fold | offset from m\* | multiplier | n (train) | expectancy R | SE | (a) E>0 | (b) n≥200 | (c) A3 | verdict |
|---|---|---|---|---|---|---|---|---|---|
| 1 | m\*+0.50 | 2.732 | 509 | -0.0008 | 0.0452 | ❌ | ✅ | ✅ | fail |
| 1 | m\*+0.75 | 2.982 | 509 | -0.0089 | 0.0437 | ❌ | ✅ | ✅ | fail |
| 1 | m\*+1.00 | 3.232 | 509 | -0.0152 | 0.0414 | ❌ | ✅ | ✅ | fail |
| 1 | m\*+1.25 | 3.482 | 509 | -0.0075 | 0.0394 | ❌ | ✅ | ✅ | fail |
| 1 | m\*+1.50 | 3.732 | 509 | -0.0110 | 0.0376 | ❌ | ✅ | ✅ | fail |
| 1 | m\*+1.75 | 3.982 | 509 | -0.0117 | 0.0363 | ❌ | ✅ | ✅ | fail |
| 1 | m\*+2.00 | 4.232 | 509 | -0.0016 | 0.0349 | ❌ | ✅ | ✅ | fail |
| 1 | m\*+2.25 | 4.482 | 509 | -0.0073 | 0.0332 | ❌ | ✅ | ✅ | fail |
| 2 | m\*+1.50 | 4.256 | 440 | -0.1036 | 0.0341 | ❌ | ✅ | ✅ | fail |
| 2 | m\*+1.75 | 4.506 | 440 | -0.0955 | 0.0332 | ❌ | ✅ | ✅ | fail |
| 2 | m\*+2.00 | 4.756 | 440 | -0.0929 | 0.0325 | ❌ | ✅ | ✅ | fail |
| 2 | m\*+2.25 | 5.006 | 440 | -0.0873 | 0.0314 | ❌ | ✅ | ✅ | fail |
| 3 | m\*+1.00 | 4.466 | 384 | +0.0232 | 0.0401 | ✅ | ✅ | ✅ | **PASS** |
| 3 | m\*+1.25 | 4.716 | 384 | +0.0253 | 0.0393 | ✅ | ✅ | ✅ | **PASS** |
| 3 | m\*+1.50 | 4.966 | 384 | +0.0279 | 0.0386 | ✅ | ✅ | ✅ | **PASS** |
| 3 | m\*+1.75 | 5.216 | 384 | +0.0255 | 0.0373 | ✅ | ✅ | ✅ | **PASS** |
| 3 | m\*+2.00 | 5.466 | 384 | +0.0229 | 0.0361 | ✅ | ✅ | ✅ | **PASS** |
| 3 | m\*+2.25 | 5.716 | 384 | +0.0220 | 0.0347 | ✅ | ✅ | ✅ | **PASS** |
| 4 | m\*+0.50 | 3.835 | 379 | +0.0528 | 0.0450 | ✅ | ✅ | ✅ | **PASS** |
| 4 | m\*+0.75 | 4.085 | 379 | +0.0571 | 0.0442 | ✅ | ✅ | ✅ | **PASS** |
| 4 | m\*+1.00 | 4.335 | 379 | +0.0523 | 0.0426 | ✅ | ✅ | ✅ | **PASS** |
| 4 | m\*+1.25 | 4.585 | 379 | +0.0523 | 0.0407 | ✅ | ✅ | ✅ | **PASS** |
| 4 | m\*+1.50 | 4.835 | 379 | +0.0594 | 0.0397 | ✅ | ✅ | ✅ | **PASS** |
| 4 | m\*+1.75 | 5.085 | 379 | +0.0629 | 0.0392 | ✅ | ✅ | ✅ | **PASS** |
| 4 | m\*+2.00 | 5.335 | 379 | +0.0586 | 0.0376 | ✅ | ✅ | ✅ | **PASS** |
| 4 | m\*+2.25 | 5.585 | 379 | +0.0575 | 0.0364 | ✅ | ✅ | ✅ | **PASS** |
| 5 | m\*+0.50 | 5.257 | 407 | -0.0632 | 0.0326 | ❌ | ✅ | ✅ | fail |
| 5 | m\*+0.75 | 5.507 | 407 | -0.0625 | 0.0314 | ❌ | ✅ | ✅ | fail |
| 5 | m\*+1.00 | 5.757 | 407 | -0.0529 | 0.0308 | ❌ | ✅ | ✅ | fail |
| 5 | m\*+1.25 | 6.007 | 407 | -0.0512 | 0.0304 | ❌ | ✅ | ✅ | fail |
| 5 | m\*+1.50 | 6.257 | 407 | -0.0507 | 0.0294 | ❌ | ✅ | ✅ | fail |
| 5 | m\*+1.75 | 6.507 | 407 | -0.0455 | 0.0285 | ❌ | ✅ | ✅ | fail |
| 5 | m\*+2.00 | 6.757 | 407 | -0.0391 | 0.0281 | ❌ | ✅ | ✅ | fail |
| 5 | m\*+2.25 | 7.007 | 407 | -0.0354 | 0.0273 | ❌ | ✅ | ✅ | fail |
| 6 | m\*+0.50 | 5.335 | 470 | -0.0470 | 0.0308 | ❌ | ✅ | ✅ | fail |
| 6 | m\*+0.75 | 5.585 | 470 | -0.0442 | 0.0301 | ❌ | ✅ | ✅ | fail |
| 6 | m\*+1.00 | 5.835 | 470 | -0.0391 | 0.0295 | ❌ | ✅ | ✅ | fail |
| 6 | m\*+1.25 | 6.085 | 470 | -0.0377 | 0.0288 | ❌ | ✅ | ✅ | fail |
| 6 | m\*+1.50 | 6.335 | 470 | -0.0318 | 0.0283 | ❌ | ✅ | ✅ | fail |
| 6 | m\*+1.75 | 6.585 | 470 | -0.0343 | 0.0274 | ❌ | ✅ | ✅ | fail |
| 6 | m\*+2.00 | 6.835 | 470 | -0.0257 | 0.0267 | ❌ | ✅ | ✅ | fail |
| 6 | m\*+2.25 | 7.085 | 470 | -0.0263 | 0.0261 | ❌ | ✅ | ✅ | fail |
| 7 | m\*+1.00 | 4.252 | 513 | +0.0092 | 0.0362 | ✅ | ✅ | ✅ | **PASS** |
| 7 | m\*+1.25 | 4.502 | 513 | +0.0107 | 0.0349 | ✅ | ✅ | ✅ | **PASS** |
| 7 | m\*+1.50 | 4.752 | 513 | +0.0049 | 0.0339 | ✅ | ✅ | ✅ | **PASS** |
| 7 | m\*+1.75 | 5.002 | 513 | +0.0065 | 0.0329 | ✅ | ✅ | ✅ | **PASS** |
| 7 | m\*+2.00 | 5.252 | 513 | -0.0019 | 0.0316 | ❌ | ✅ | ✅ | fail |
| 7 | m\*+2.25 | 5.502 | 513 | -0.0047 | 0.0309 | ❌ | ✅ | ✅ | fail |
| 8 | m\*+0.75 | 3.615 | 522 | +0.0126 | 0.0394 | ✅ | ✅ | ✅ | **PASS** |
| 8 | m\*+1.00 | 3.865 | 522 | +0.0103 | 0.0380 | ✅ | ✅ | ✅ | **PASS** |
| 8 | m\*+1.25 | 4.115 | 522 | +0.0161 | 0.0370 | ✅ | ✅ | ✅ | **PASS** |
| 8 | m\*+1.50 | 4.365 | 522 | +0.0206 | 0.0356 | ✅ | ✅ | ✅ | **PASS** |
| 8 | m\*+1.75 | 4.615 | 522 | +0.0144 | 0.0341 | ✅ | ✅ | ✅ | **PASS** |
| 8 | m\*+2.00 | 4.865 | 522 | +0.0095 | 0.0329 | ✅ | ✅ | ✅ | **PASS** |
| 8 | m\*+2.25 | 5.115 | 522 | +0.0128 | 0.0318 | ✅ | ✅ | ✅ | **PASS** |
| 9 | m\*+0.75 | 3.621 | 517 | -0.0297 | 0.0356 | ❌ | ✅ | ✅ | fail |
| 9 | m\*+1.00 | 3.871 | 517 | -0.0275 | 0.0338 | ❌ | ✅ | ✅ | fail |
| 9 | m\*+1.25 | 4.121 | 517 | -0.0184 | 0.0330 | ❌ | ✅ | ✅ | fail |
| 9 | m\*+1.50 | 4.371 | 517 | -0.0151 | 0.0318 | ❌ | ✅ | ✅ | fail |
| 9 | m\*+1.75 | 4.621 | 517 | -0.0244 | 0.0301 | ❌ | ✅ | ✅ | fail |
| 9 | m\*+2.00 | 4.871 | 517 | -0.0185 | 0.0293 | ❌ | ✅ | ✅ | fail |
| 9 | m\*+2.25 | 5.121 | 517 | -0.0138 | 0.0279 | ❌ | ✅ | ✅ | fail |

### 3.2 ETHUSDT — train, `gated_50`, `both`

| fold | offset from m\* | multiplier | n (train) | expectancy R | SE | (a) E>0 | (b) n≥200 | (c) A3 | verdict |
|---|---|---|---|---|---|---|---|---|---|
| 1 | m\*+0.50 | 2.122 | 538 | -0.0503 | 0.0467 | ❌ | ✅ | ✅ | fail |
| 1 | m\*+0.75 | 2.372 | 538 | -0.0401 | 0.0445 | ❌ | ✅ | ✅ | fail |
| 1 | m\*+1.00 | 2.622 | 538 | -0.0345 | 0.0427 | ❌ | ✅ | ✅ | fail |
| 1 | m\*+1.25 | 2.872 | 538 | -0.0406 | 0.0407 | ❌ | ✅ | ✅ | fail |
| 1 | m\*+1.50 | 3.122 | 538 | -0.0455 | 0.0383 | ❌ | ✅ | ✅ | fail |
| 1 | m\*+1.75 | 3.372 | 538 | -0.0442 | 0.0364 | ❌ | ✅ | ✅ | fail |
| 1 | m\*+2.00 | 3.622 | 538 | -0.0432 | 0.0341 | ❌ | ✅ | ✅ | fail |
| 1 | m\*+2.25 | 3.872 | 538 | -0.0387 | 0.0327 | ❌ | ✅ | ✅ | fail |
| 2 | m\*+0.75 | 2.545 | 454 | -0.1013 | 0.0443 | ❌ | ✅ | ✅ | fail |
| 2 | m\*+1.00 | 2.795 | 454 | -0.1109 | 0.0422 | ❌ | ✅ | ✅ | fail |
| 2 | m\*+1.25 | 3.045 | 454 | -0.0951 | 0.0405 | ❌ | ✅ | ✅ | fail |
| 2 | m\*+1.50 | 3.295 | 454 | -0.0868 | 0.0390 | ❌ | ✅ | ✅ | fail |
| 2 | m\*+1.75 | 3.545 | 454 | -0.0807 | 0.0374 | ❌ | ✅ | ✅ | fail |
| 2 | m\*+2.00 | 3.795 | 454 | -0.0682 | 0.0360 | ❌ | ✅ | ✅ | fail |
| 2 | m\*+2.25 | 4.045 | 454 | -0.0594 | 0.0345 | ❌ | ✅ | ✅ | fail |
| 3 | m\*+0.50 | 3.123 | 382 | -0.0494 | 0.0469 | ❌ | ✅ | ✅ | fail |
| 3 | m\*+0.75 | 3.373 | 382 | -0.0408 | 0.0456 | ❌ | ✅ | ✅ | fail |
| 3 | m\*+1.00 | 3.623 | 382 | -0.0305 | 0.0448 | ❌ | ✅ | ✅ | fail |
| 3 | m\*+1.25 | 3.873 | 382 | -0.0152 | 0.0434 | ❌ | ✅ | ✅ | fail |
| 3 | m\*+1.50 | 4.123 | 382 | -0.0184 | 0.0413 | ❌ | ✅ | ✅ | fail |
| 3 | m\*+1.75 | 4.373 | 382 | -0.0239 | 0.0399 | ❌ | ✅ | ✅ | fail |
| 3 | m\*+2.00 | 4.623 | 382 | -0.0166 | 0.0393 | ❌ | ✅ | ✅ | fail |
| 3 | m\*+2.25 | 4.873 | 382 | -0.0233 | 0.0375 | ❌ | ✅ | ✅ | fail |
| 4 | m\*+0.50 | 3.491 | 364 | -0.0270 | 0.0454 | ❌ | ✅ | ✅ | fail |
| 4 | m\*+0.75 | 3.741 | 364 | -0.0304 | 0.0438 | ❌ | ✅ | ✅ | fail |
| 4 | m\*+1.00 | 3.991 | 364 | -0.0213 | 0.0427 | ❌ | ✅ | ✅ | fail |
| 4 | m\*+1.25 | 4.241 | 364 | -0.0283 | 0.0414 | ❌ | ✅ | ✅ | fail |
| 4 | m\*+1.50 | 4.491 | 364 | -0.0192 | 0.0403 | ❌ | ✅ | ✅ | fail |
| 4 | m\*+1.75 | 4.741 | 364 | -0.0081 | 0.0394 | ❌ | ✅ | ✅ | fail |
| 4 | m\*+2.00 | 4.991 | 364 | -0.0054 | 0.0382 | ❌ | ✅ | ✅ | fail |
| 4 | m\*+2.25 | 5.241 | 364 | -0.0137 | 0.0363 | ❌ | ✅ | ✅ | fail |
| 5 | m\*+0.25 | 4.632 | 385 | -0.0980 | 0.0357 | ❌ | ✅ | ✅ | fail |
| 5 | m\*+0.50 | 4.882 | 385 | -0.0949 | 0.0346 | ❌ | ✅ | ✅ | fail |
| 5 | m\*+0.75 | 5.132 | 385 | -0.0937 | 0.0336 | ❌ | ✅ | ✅ | fail |
| 5 | m\*+1.00 | 5.382 | 385 | -0.0857 | 0.0332 | ❌ | ✅ | ✅ | fail |
| 5 | m\*+1.25 | 5.632 | 385 | -0.0854 | 0.0324 | ❌ | ✅ | ✅ | fail |
| 5 | m\*+1.50 | 5.882 | 385 | -0.0812 | 0.0313 | ❌ | ✅ | ✅ | fail |
| 5 | m\*+1.75 | 6.132 | 385 | -0.0794 | 0.0306 | ❌ | ✅ | ✅ | fail |
| 5 | m\*+2.00 | 6.382 | 385 | -0.0754 | 0.0295 | ❌ | ✅ | ✅ | fail |
| 5 | m\*+2.25 | 6.632 | 385 | -0.0700 | 0.0289 | ❌ | ✅ | ✅ | fail |
| 6 | m\*+0.50 | 4.273 | 465 | -0.0851 | 0.0338 | ❌ | ✅ | ✅ | fail |
| 6 | m\*+0.75 | 4.523 | 465 | -0.0817 | 0.0325 | ❌ | ✅ | ✅ | fail |
| 6 | m\*+1.00 | 4.773 | 465 | -0.0808 | 0.0314 | ❌ | ✅ | ✅ | fail |
| 6 | m\*+1.25 | 5.023 | 465 | -0.0741 | 0.0310 | ❌ | ✅ | ✅ | fail |
| 6 | m\*+1.50 | 5.273 | 465 | -0.0669 | 0.0305 | ❌ | ✅ | ✅ | fail |
| 6 | m\*+1.75 | 5.523 | 465 | -0.0640 | 0.0297 | ❌ | ✅ | ✅ | fail |
| 6 | m\*+2.00 | 5.773 | 465 | -0.0638 | 0.0289 | ❌ | ✅ | ✅ | fail |
| 6 | m\*+2.25 | 6.023 | 465 | -0.0630 | 0.0281 | ❌ | ✅ | ✅ | fail |
| 7 | m\*+0.75 | 3.452 | 537 | -0.1148 | 0.0346 | ❌ | ✅ | ✅ | fail |
| 7 | m\*+1.00 | 3.702 | 537 | -0.1143 | 0.0333 | ❌ | ✅ | ✅ | fail |
| 7 | m\*+1.25 | 3.952 | 537 | -0.1054 | 0.0325 | ❌ | ✅ | ✅ | fail |
| 7 | m\*+1.50 | 4.202 | 537 | -0.1017 | 0.0314 | ❌ | ✅ | ✅ | fail |
| 7 | m\*+1.75 | 4.452 | 537 | -0.0939 | 0.0304 | ❌ | ✅ | ✅ | fail |
| 7 | m\*+2.00 | 4.702 | 537 | -0.0912 | 0.0293 | ❌ | ✅ | ✅ | fail |
| 7 | m\*+2.25 | 4.952 | 537 | -0.0843 | 0.0284 | ❌ | ✅ | ✅ | fail |
| 8 | m\*+0.50 | 2.958 | 519 | -0.1274 | 0.0386 | ❌ | ✅ | ✅ | fail |
| 8 | m\*+0.75 | 3.208 | 519 | -0.1147 | 0.0373 | ❌ | ✅ | ✅ | fail |
| 8 | m\*+1.00 | 3.458 | 519 | -0.1199 | 0.0354 | ❌ | ✅ | ✅ | fail |
| 8 | m\*+1.25 | 3.708 | 519 | -0.1197 | 0.0338 | ❌ | ✅ | ✅ | fail |
| 8 | m\*+1.50 | 3.958 | 519 | -0.1192 | 0.0327 | ❌ | ✅ | ✅ | fail |
| 8 | m\*+1.75 | 4.208 | 519 | -0.1068 | 0.0321 | ❌ | ✅ | ✅ | fail |
| 8 | m\*+2.00 | 4.458 | 519 | -0.1110 | 0.0308 | ❌ | ✅ | ✅ | fail |
| 8 | m\*+2.25 | 4.708 | 519 | -0.1107 | 0.0289 | ❌ | ✅ | ✅ | fail |
| 9 | m\*+0.75 | 3.248 | 491 | -0.0575 | 0.0389 | ❌ | ✅ | ✅ | fail |
| 9 | m\*+1.00 | 3.498 | 491 | -0.0540 | 0.0378 | ❌ | ✅ | ✅ | fail |
| 9 | m\*+1.25 | 3.748 | 491 | -0.0447 | 0.0363 | ❌ | ✅ | ✅ | fail |
| 9 | m\*+1.50 | 3.998 | 491 | -0.0391 | 0.0345 | ❌ | ✅ | ✅ | fail |
| 9 | m\*+1.75 | 4.248 | 491 | -0.0320 | 0.0337 | ❌ | ✅ | ✅ | fail |
| 9 | m\*+2.00 | 4.498 | 491 | -0.0329 | 0.0323 | ❌ | ✅ | ✅ | fail |
| 9 | m\*+2.25 | 4.748 | 491 | -0.0427 | 0.0303 | ❌ | ✅ | ✅ | fail |

### 3.3 SOLUSDT — train, `gated_50`, `both`

| fold | offset from m\* | multiplier | n (train) | expectancy R | SE | (a) E>0 | (b) n≥200 | (c) A3 | verdict |
|---|---|---|---|---|---|---|---|---|---|
| 1 | m\*+0.50 | 2.118 | 635 | -0.0690 | 0.0433 | ❌ | ✅ | ✅ | fail |
| 1 | m\*+0.75 | 2.368 | 635 | -0.0785 | 0.0410 | ❌ | ✅ | ✅ | fail |
| 1 | m\*+1.00 | 2.618 | 635 | -0.0528 | 0.0390 | ❌ | ✅ | ✅ | fail |
| 1 | m\*+1.25 | 2.868 | 635 | -0.0449 | 0.0370 | ❌ | ✅ | ✅ | fail |
| 1 | m\*+1.50 | 3.118 | 635 | -0.0482 | 0.0350 | ❌ | ✅ | ✅ | fail |
| 1 | m\*+1.75 | 3.368 | 635 | -0.0402 | 0.0334 | ❌ | ✅ | ✅ | fail |
| 1 | m\*+2.00 | 3.618 | 635 | -0.0365 | 0.0320 | ❌ | ✅ | ✅ | fail |
| 1 | m\*+2.25 | 3.868 | 635 | -0.0431 | 0.0301 | ❌ | ✅ | ✅ | fail |
| 2 | m\*+0.75 | 2.695 | 566 | -0.0202 | 0.0424 | ❌ | ✅ | ✅ | fail |
| 2 | m\*+1.00 | 2.945 | 566 | -0.0107 | 0.0409 | ❌ | ✅ | ✅ | fail |
| 2 | m\*+1.25 | 3.195 | 566 | +0.0023 | 0.0390 | ✅ | ✅ | ✅ | **PASS** |
| 2 | m\*+1.50 | 3.445 | 566 | -0.0063 | 0.0370 | ❌ | ✅ | ✅ | fail |
| 2 | m\*+1.75 | 3.695 | 566 | -0.0034 | 0.0356 | ❌ | ✅ | ✅ | fail |
| 2 | m\*+2.00 | 3.945 | 566 | -0.0140 | 0.0337 | ❌ | ✅ | ✅ | fail |
| 2 | m\*+2.25 | 4.195 | 566 | -0.0112 | 0.0324 | ❌ | ✅ | ✅ | fail |
| 3 | m\*+0.50 | 2.451 | 489 | -0.0183 | 0.0490 | ❌ | ✅ | ✅ | fail |
| 3 | m\*+0.75 | 2.701 | 489 | -0.0029 | 0.0478 | ❌ | ✅ | ✅ | fail |
| 3 | m\*+1.00 | 2.951 | 489 | +0.0010 | 0.0461 | ✅ | ✅ | ✅ | **PASS** |
| 3 | m\*+1.25 | 3.201 | 489 | +0.0070 | 0.0440 | ✅ | ✅ | ✅ | **PASS** |
| 3 | m\*+1.50 | 3.451 | 489 | -0.0035 | 0.0421 | ❌ | ✅ | ✅ | fail |
| 3 | m\*+1.75 | 3.701 | 489 | -0.0020 | 0.0403 | ❌ | ✅ | ✅ | fail |
| 3 | m\*+2.00 | 3.951 | 489 | -0.0073 | 0.0387 | ❌ | ✅ | ✅ | fail |
| 3 | m\*+2.25 | 4.201 | 489 | +0.0017 | 0.0372 | ✅ | ✅ | ✅ | **PASS** |
| 4 | m\*+0.75 | 2.910 | 482 | -0.0155 | 0.0426 | ❌ | ✅ | ✅ | fail |
| 4 | m\*+1.00 | 3.160 | 482 | -0.0208 | 0.0405 | ❌ | ✅ | ✅ | fail |
| 4 | m\*+1.25 | 3.410 | 482 | -0.0070 | 0.0394 | ❌ | ✅ | ✅ | fail |
| 4 | m\*+1.50 | 3.660 | 482 | -0.0087 | 0.0379 | ❌ | ✅ | ✅ | fail |
| 4 | m\*+1.75 | 3.910 | 482 | +0.0039 | 0.0371 | ✅ | ✅ | ✅ | **PASS** |
| 4 | m\*+2.00 | 4.160 | 482 | +0.0119 | 0.0358 | ✅ | ✅ | ✅ | **PASS** |
| 4 | m\*+2.25 | 4.410 | 482 | +0.0253 | 0.0349 | ✅ | ✅ | ✅ | **PASS** |
| 5 | m\*+0.75 | 3.569 | 491 | -0.0167 | 0.0379 | ❌ | ✅ | ✅ | fail |
| 5 | m\*+1.00 | 3.819 | 491 | -0.0095 | 0.0367 | ❌ | ✅ | ✅ | fail |
| 5 | m\*+1.25 | 4.069 | 491 | -0.0013 | 0.0355 | ❌ | ✅ | ✅ | fail |
| 5 | m\*+1.50 | 4.319 | 491 | +0.0127 | 0.0342 | ✅ | ✅ | ✅ | **PASS** |
| 5 | m\*+1.75 | 4.569 | 491 | +0.0227 | 0.0334 | ✅ | ✅ | ✅ | **PASS** |
| 5 | m\*+2.00 | 4.819 | 491 | +0.0266 | 0.0323 | ✅ | ✅ | ✅ | **PASS** |
| 5 | m\*+2.25 | 5.069 | 491 | +0.0302 | 0.0314 | ✅ | ✅ | ✅ | **PASS** |
| 6 | m\*+1.00 | 3.059 | 521 | -0.0344 | 0.0411 | ❌ | ✅ | ✅ | fail |
| 6 | m\*+1.25 | 3.309 | 521 | -0.0311 | 0.0395 | ❌ | ✅ | ✅ | fail |
| 6 | m\*+1.50 | 3.559 | 521 | -0.0117 | 0.0381 | ❌ | ✅ | ✅ | fail |
| 6 | m\*+1.75 | 3.809 | 521 | -0.0086 | 0.0361 | ❌ | ✅ | ✅ | fail |
| 6 | m\*+2.00 | 4.059 | 521 | +0.0017 | 0.0343 | ✅ | ✅ | ✅ | **PASS** |
| 6 | m\*+2.25 | 4.309 | 521 | +0.0106 | 0.0329 | ✅ | ✅ | ✅ | **PASS** |
| 7 | m\*+0.50 | 2.114 | 568 | -0.0701 | 0.0465 | ❌ | ✅ | ✅ | fail |
| 7 | m\*+0.75 | 2.364 | 568 | -0.0928 | 0.0435 | ❌ | ✅ | ✅ | fail |
| 7 | m\*+1.00 | 2.614 | 568 | -0.0765 | 0.0419 | ❌ | ✅ | ✅ | fail |
| 7 | m\*+1.25 | 2.864 | 568 | -0.0775 | 0.0396 | ❌ | ✅ | ✅ | fail |
| 7 | m\*+1.50 | 3.114 | 568 | -0.0708 | 0.0376 | ❌ | ✅ | ✅ | fail |
| 7 | m\*+1.75 | 3.364 | 568 | -0.0640 | 0.0361 | ❌ | ✅ | ✅ | fail |
| 7 | m\*+2.00 | 3.614 | 568 | -0.0478 | 0.0344 | ❌ | ✅ | ✅ | fail |
| 7 | m\*+2.25 | 3.864 | 568 | -0.0427 | 0.0325 | ❌ | ✅ | ✅ | fail |
| 8 | m\*+0.50 | 2.363 | 589 | -0.0871 | 0.0414 | ❌ | ✅ | ✅ | fail |
| 8 | m\*+0.75 | 2.613 | 589 | -0.0751 | 0.0396 | ❌ | ✅ | ✅ | fail |
| 8 | m\*+1.00 | 2.863 | 589 | -0.0812 | 0.0372 | ❌ | ✅ | ✅ | fail |
| 8 | m\*+1.25 | 3.113 | 589 | -0.0872 | 0.0349 | ❌ | ✅ | ✅ | fail |
| 8 | m\*+1.50 | 3.363 | 589 | -0.0832 | 0.0333 | ❌ | ✅ | ✅ | fail |
| 8 | m\*+1.75 | 3.613 | 589 | -0.0708 | 0.0319 | ❌ | ✅ | ✅ | fail |
| 8 | m\*+2.00 | 3.863 | 589 | -0.0693 | 0.0302 | ❌ | ✅ | ✅ | fail |
| 8 | m\*+2.25 | 4.113 | 589 | -0.0663 | 0.0288 | ❌ | ✅ | ✅ | fail |
| 9 | m\*+0.75 | 2.854 | 593 | -0.0106 | 0.0382 | ❌ | ✅ | ✅ | fail |
| 9 | m\*+1.00 | 3.104 | 593 | -0.0145 | 0.0364 | ❌ | ✅ | ✅ | fail |
| 9 | m\*+1.25 | 3.354 | 593 | -0.0050 | 0.0351 | ❌ | ✅ | ✅ | fail |
| 9 | m\*+1.50 | 3.604 | 593 | -0.0118 | 0.0330 | ❌ | ✅ | ✅ | fail |
| 9 | m\*+1.75 | 3.854 | 593 | -0.0104 | 0.0316 | ❌ | ✅ | ✅ | fail |
| 9 | m\*+2.00 | 4.104 | 593 | -0.0155 | 0.0304 | ❌ | ✅ | ✅ | fail |
| 9 | m\*+2.25 | 4.354 | 593 | -0.0138 | 0.0290 | ❌ | ✅ | ✅ | fail |

## 4. Band identification (§4.3)

Contiguity is a **grid** relation, not a list relation: two passing offsets 0.50 apart are not contiguous, because the 0.25 point between them failed. A fold produces a selection only where a contiguous run of **three or more** passing points exists.

Offset 2.50 is excluded from eligibility by the plateau rule and was not simulated, so no band can reach it.

| symbol | fold | offsets evaluated | passing | runs found (offsets from m\*) | longest run | selection? |
|---|---|---|---|---|---|---|
| BTCUSDT | 1 | 8 | 0 | *none* | 0 | NO SELECTION |
| BTCUSDT | 2 | 4 | 0 | *none* | 0 | NO SELECTION |
| BTCUSDT | 3 | 6 | 6 | [m\*+1.00 … m\*+2.25] w=6 | 6 | **yes** |
| BTCUSDT | 4 | 8 | 8 | [m\*+0.50 … m\*+2.25] w=8 | 8 | **yes** |
| BTCUSDT | 5 | 8 | 0 | *none* | 0 | NO SELECTION |
| BTCUSDT | 6 | 8 | 0 | *none* | 0 | NO SELECTION |
| BTCUSDT | 7 | 6 | 4 | [m\*+1.00 … m\*+1.75] w=4 | 4 | **yes** |
| BTCUSDT | 8 | 7 | 7 | [m\*+0.75 … m\*+2.25] w=7 | 7 | **yes** |
| BTCUSDT | 9 | 7 | 0 | *none* | 0 | NO SELECTION |
| ETHUSDT | 1 | 8 | 0 | *none* | 0 | NO SELECTION |
| ETHUSDT | 2 | 7 | 0 | *none* | 0 | NO SELECTION |
| ETHUSDT | 3 | 8 | 0 | *none* | 0 | NO SELECTION |
| ETHUSDT | 4 | 8 | 0 | *none* | 0 | NO SELECTION |
| ETHUSDT | 5 | 9 | 0 | *none* | 0 | NO SELECTION |
| ETHUSDT | 6 | 8 | 0 | *none* | 0 | NO SELECTION |
| ETHUSDT | 7 | 7 | 0 | *none* | 0 | NO SELECTION |
| ETHUSDT | 8 | 8 | 0 | *none* | 0 | NO SELECTION |
| ETHUSDT | 9 | 7 | 0 | *none* | 0 | NO SELECTION |
| SOLUSDT | 1 | 8 | 0 | *none* | 0 | NO SELECTION |
| SOLUSDT | 2 | 7 | 1 | [m\*+1.25 … m\*+1.25] w=1 | 1 | NO SELECTION |
| SOLUSDT | 3 | 8 | 3 | [m\*+1.00 … m\*+1.25] w=2; [m\*+2.25 … m\*+2.25] w=1 | 2 | NO SELECTION |
| SOLUSDT | 4 | 7 | 3 | [m\*+1.75 … m\*+2.25] w=3 | 3 | **yes** |
| SOLUSDT | 5 | 7 | 4 | [m\*+1.50 … m\*+2.25] w=4 | 4 | **yes** |
| SOLUSDT | 6 | 6 | 2 | [m\*+2.00 … m\*+2.25] w=2 | 2 | NO SELECTION |
| SOLUSDT | 7 | 8 | 0 | *none* | 0 | NO SELECTION |
| SOLUSDT | 8 | 8 | 0 | *none* | 0 | NO SELECTION |
| SOLUSDT | 9 | 7 | 0 | *none* | 0 | NO SELECTION |

**Folds producing a selection:** BTCUSDT 4/9, ETHUSDT 0/9, SOLUSDT 2/9 — 6 of 27 fold-symbols in total.

ETHUSDT produces **no selection in any fold**: not one of its 70 A3-eligible grid points has positive training expectancy. That is not a marginal miss — every ETH training cell is negative, at every offset, in all nine folds.

## 5. Plateau selection (§4.3, Appendix K.3)

The selected value is the **centre of the widest contiguous passing band, NOT the argmax**. Where the band has an even number of points the **higher** of the two central offsets is taken, per Appendix K.3. The selection function receives offsets only and never sees an expectancy, so it cannot express an argmax pull even by accident.

| symbol | fold | band (offsets from m\*) | width | even? | **selected offset** | selected multiplier |
|---|---|---|---|---|---|---|
| BTCUSDT | 1 | — | — | — | *NO SELECTION* | — |
| BTCUSDT | 2 | — | — | — | *NO SELECTION* | — |
| BTCUSDT | 3 | [m\*+1.00 … m\*+2.25] | 6 | yes | **m\*+1.75** | 5.216 |
| BTCUSDT | 4 | [m\*+0.50 … m\*+2.25] | 8 | yes | **m\*+1.50** | 4.835 |
| BTCUSDT | 5 | — | — | — | *NO SELECTION* | — |
| BTCUSDT | 6 | — | — | — | *NO SELECTION* | — |
| BTCUSDT | 7 | [m\*+1.00 … m\*+1.75] | 4 | yes | **m\*+1.50** | 4.752 |
| BTCUSDT | 8 | [m\*+0.75 … m\*+2.25] | 7 | no | **m\*+1.50** | 4.365 |
| BTCUSDT | 9 | — | — | — | *NO SELECTION* | — |
| ETHUSDT | 1 | — | — | — | *NO SELECTION* | — |
| ETHUSDT | 2 | — | — | — | *NO SELECTION* | — |
| ETHUSDT | 3 | — | — | — | *NO SELECTION* | — |
| ETHUSDT | 4 | — | — | — | *NO SELECTION* | — |
| ETHUSDT | 5 | — | — | — | *NO SELECTION* | — |
| ETHUSDT | 6 | — | — | — | *NO SELECTION* | — |
| ETHUSDT | 7 | — | — | — | *NO SELECTION* | — |
| ETHUSDT | 8 | — | — | — | *NO SELECTION* | — |
| ETHUSDT | 9 | — | — | — | *NO SELECTION* | — |
| SOLUSDT | 1 | — | — | — | *NO SELECTION* | — |
| SOLUSDT | 2 | — | — | — | *NO SELECTION* | — |
| SOLUSDT | 3 | — | — | — | *NO SELECTION* | — |
| SOLUSDT | 4 | [m\*+1.75 … m\*+2.25] | 3 | no | **m\*+2.00** | 4.160 |
| SOLUSDT | 5 | [m\*+1.50 … m\*+2.25] | 4 | yes | **m\*+2.00** | 4.819 |
| SOLUSDT | 6 | — | — | — | *NO SELECTION* | — |
| SOLUSDT | 7 | — | — | — | *NO SELECTION* | — |
| SOLUSDT | 8 | — | — | — | *NO SELECTION* | — |
| SOLUSDT | 9 | — | — | — | *NO SELECTION* | — |

Absolute multipliers are shown for completeness only. **They are not comparable across folds** — m\* moves by a factor of 2.2 — which is why §4.4 requires bands to be expressed as offsets.

**These nine-fold selections are NOT collapsed into a candidate.** That is step 4 and a separate task, and §4.4 forbids a step revisiting an earlier one.

**Where the centre rule actually bit** (centre ≠ argmax): BTCUSDT fold 3: centre m\*+1.75, argmax m\*+1.50; BTCUSDT fold 4: centre m\*+1.50, argmax m\*+1.75; BTCUSDT fold 7: centre m\*+1.50, argmax m\*+1.25; SOLUSDT fold 4: centre m\*+2.00, argmax m\*+2.25; SOLUSDT fold 5: centre m\*+2.00, argmax m\*+2.25.

## 6. The pre-committed kill conditions

### 6.1 (a) OOS EXPECTANCY ≤ 0 AFTER COSTS

**Population: `gated_50`, period `test`, direction `both`, arm `full`, pooled across TEST FOLDS ONLY per Appendix M.4.** Training folds overlap by 50% and pooling them would double-count mid-span trades; test folds do not overlap.

Fold coverage varies by offset because A3 eligibility varies by fold. The `folds` column states it on every row, and a figure pooling four folds is not the same statement as one pooling nine.

**BTCUSDT**

| offset from m\* | folds pooled | n | expectancy R | SE | positive? | exceeds own SE? |
|---|---|---|---|---|---|---|
| m\*+0.50 | 4 | 784 | -0.0378 | 0.0269 | no | no |
| m\*+0.75 | 6 | 1581 | -0.0613 | 0.0192 | no | no |
| m\*+1.00 | 8 | 1923 | -0.0494 | 0.0169 | no | no |
| m\*+1.25 | 8 | 1923 | -0.0457 | 0.0164 | no | no |
| m\*+1.50 | 9 | 2177 | -0.0330 | 0.0154 | no | no |
| m\*+1.75 | 9 | 2177 | -0.0305 | 0.0149 | no | no |
| m\*+2.00 | 9 | 2177 | -0.0275 | 0.0145 | no | no |
| m\*+2.25 | 9 | 2177 | -0.0258 | 0.0140 | no | no |

- Any offset positive: **NO** · any offset exceeding its own standard error: **NO**
- Best offset: m\*+2.25 at -0.0258
- **VERDICT: kill condition (a) FIRES for BTCUSDT.**

**ETHUSDT**

| offset from m\* | folds pooled | n | expectancy R | SE | positive? | exceeds own SE? |
|---|---|---|---|---|---|---|
| m\*+0.25 | 1 | 307 | -0.0376 | 0.0391 | no | no |
| m\*+0.50 | 6 | 1357 | -0.0693 | 0.0230 | no | no |
| m\*+0.75 | 9 | 2101 | -0.0760 | 0.0186 | no | no |
| m\*+1.00 | 9 | 2101 | -0.0692 | 0.0181 | no | no |
| m\*+1.25 | 9 | 2101 | -0.0649 | 0.0173 | no | no |
| m\*+1.50 | 9 | 2101 | -0.0595 | 0.0168 | no | no |
| m\*+1.75 | 9 | 2101 | -0.0581 | 0.0161 | no | no |
| m\*+2.00 | 9 | 2101 | -0.0552 | 0.0156 | no | no |
| m\*+2.25 | 9 | 2101 | -0.0521 | 0.0150 | no | no |

- Any offset positive: **NO** · any offset exceeding its own standard error: **NO**
- Best offset: m\*+0.25 at -0.0376
- **VERDICT: kill condition (a) FIRES for ETHUSDT.**

**SOLUSDT**

| offset from m\* | folds pooled | n | expectancy R | SE | positive? | exceeds own SE? |
|---|---|---|---|---|---|---|
| m\*+0.50 | 4 | 1124 | +0.0229 | 0.0319 | yes | no |
| m\*+0.75 | 8 | 2206 | -0.0192 | 0.0208 | no | no |
| m\*+1.00 | 9 | 2522 | -0.0315 | 0.0183 | no | no |
| m\*+1.25 | 9 | 2522 | -0.0286 | 0.0176 | no | no |
| m\*+1.50 | 9 | 2522 | -0.0238 | 0.0169 | no | no |
| m\*+1.75 | 9 | 2522 | -0.0201 | 0.0162 | no | no |
| m\*+2.00 | 9 | 2522 | -0.0148 | 0.0155 | no | no |
| m\*+2.25 | 9 | 2522 | -0.0152 | 0.0149 | no | no |

- Any offset positive: **YES** · any offset exceeding its own standard error: **NO**
- Best offset: m\*+0.50 at +0.0229
- **VERDICT: kill condition (a) does not fire for SOLUSDT.**

**SOLUSDT needs stating precisely.** The condition as pre-committed asks whether OOS expectancy is ≤ 0, and SOL has 1 offset where it is not: m\*+0.50 at +0.0229 (SE 0.0319, 4 folds pooled). So the condition does not fire on the letter of the rule. Three things about that single point are recorded rather than argued away:

- it is smaller than its own standard error (+0.0229 against 0.0319);
- it pools **4 of 9** test folds, because m\*+0.50 is A3-eligible in only those folds;
- **no SOLUSDT fold selected m\*+0.50.** Both SOL selections landed at m\*+2.00, where pooled test expectancy is -0.0148.

Every offset any SOL fold actually selected is negative out of sample. That is recorded as an observation, not used to redefine the condition.

### 6.2 (b) GATED VS UNGATED DIFFER BY < 0.05R — THE GATE IS DECORATIVE

**Populations: `gated_50` against `ungated`, period `test`, direction `both`, arms `full` and `minus_rvol`, pooled across test folds only.** Appendix J's requirement is met on every row: each arm's floor-binding rate, and the comparison stratified into floor-bound and non-floor-bound trades, with any stratum below the evidence minimum stated and withheld rather than reported.

**BTCUSDT**

| offset | n gated / ungated | E gated_50 | E ungated | **diff** | ≥0.05R? | floor-bind g / u | gap |
|---|---|---|---|---|---|---|---|
| m\*+0.50 | 784 / 1849 | -0.0378 | -0.0677 | **+0.0299** | no | 29.7% / 45.0% | -15.3pp |
| m\*+0.75 | 1581 / 3025 | -0.0613 | -0.0855 | **+0.0243** | no | 24.2% / 37.9% | -13.7pp |
| m\*+1.00 | 1923 / 3887 | -0.0494 | -0.0762 | **+0.0268** | no | 18.8% / 31.8% | -13.0pp |
| m\*+1.25 | 1923 / 3887 | -0.0457 | -0.0716 | **+0.0259** | no | 16.1% / 28.6% | -12.5pp |
| m\*+1.50 | 2177 / 4285 | -0.0330 | -0.0653 | **+0.0323** | no | 13.6% / 26.0% | -12.4pp |
| m\*+1.75 | 2177 / 4285 | -0.0305 | -0.0624 | **+0.0318** | no | 11.4% / 23.5% | -12.1pp |
| m\*+2.00 | 2177 / 4285 | -0.0275 | -0.0601 | **+0.0326** | no | 9.3% / 21.0% | -11.7pp |
| m\*+2.25 | 2177 / 4285 | -0.0258 | -0.0581 | **+0.0324** | no | 8.1% / 19.2% | -11.1pp |

Appendix J stratification, same populations:

| offset | floor-bound Δ | non-floor-bound Δ |
|---|---|---|
| m\*+0.50 | +0.0067 (g -0.0763 / u -0.0830, n_g=233, n_u=832) | +0.0337 (g -0.0215 / u -0.0552, n_g=551, n_u=1017) |
| m\*+0.75 | +0.0213 (g -0.0638 / u -0.0851, n_g=382, n_u=1146) | +0.0253 (g -0.0605 / u -0.0858, n_g=1199, n_u=1879) |
| m\*+1.00 | +0.0429 (g -0.0377 / u -0.0806, n_g=361, n_u=1236) | +0.0221 (g -0.0522 / u -0.0742, n_g=1562, n_u=2651) |
| m\*+1.25 | +0.0758 (g +0.0050 / u -0.0708, n_g=309, n_u=1112) | +0.0165 (g -0.0554 / u -0.0720, n_g=1614, n_u=2775) |
| m\*+1.50 | +0.0626 (g -0.0215 / u -0.0841, n_g=297, n_u=1114) | +0.0238 (g -0.0348 / u -0.0586, n_g=1880, n_u=3171) |
| m\*+1.75 | +0.0596 (g -0.0324 / u -0.0920, n_g=248, n_u=1006) | +0.0230 (g -0.0303 / u -0.0533, n_g=1929, n_u=3279) |
| m\*+2.00 | +0.0317 (g -0.0747 / u -0.1064, n_g=202, n_u=901) | +0.0251 (g -0.0227 / u -0.0478, n_g=1975, n_u=3384) |
| m\*+2.25 | +0.0247 (g -0.0857 / u -0.1104, n_g=176, n_u=821) | +0.0252 (g -0.0205 / u -0.0457, n_g=2001, n_u=3464) |

- Maximum difference at any offset: **+0.0326**.
- **VERDICT: kill condition (b) FIRES for BTCUSDT.**

**ETHUSDT**

| offset | n gated / ungated | E gated_50 | E ungated | **diff** | ≥0.05R? | floor-bind g / u | gap |
|---|---|---|---|---|---|---|---|
| m\*+0.25 | 307 / 510 | -0.0376 | -0.0508 | **+0.0132** | no | 5.9% / 17.1% | -11.2pp |
| m\*+0.50 | 1357 / 2736 | -0.0693 | -0.0824 | **+0.0132** | no | 24.9% / 38.7% | -13.8pp |
| m\*+0.75 | 2101 / 4159 | -0.0760 | -0.0887 | **+0.0128** | no | 18.5% / 31.8% | -13.3pp |
| m\*+1.00 | 2101 / 4159 | -0.0692 | -0.0831 | **+0.0139** | no | 14.9% / 27.9% | -13.0pp |
| m\*+1.25 | 2101 / 4159 | -0.0649 | -0.0775 | **+0.0126** | no | 11.6% / 23.8% | -12.2pp |
| m\*+1.50 | 2101 / 4159 | -0.0595 | -0.0727 | **+0.0132** | no | 8.5% / 20.4% | -11.9pp |
| m\*+1.75 | 2101 / 4159 | -0.0581 | -0.0702 | **+0.0121** | no | 6.6% / 17.9% | -11.3pp |
| m\*+2.00 | 2101 / 4159 | -0.0552 | -0.0681 | **+0.0129** | no | 5.2% / 15.7% | -10.5pp |
| m\*+2.25 | 2101 / 4159 | -0.0521 | -0.0655 | **+0.0134** | no | 3.9% / 13.1% | -9.2pp |

Appendix J stratification, same populations:

| offset | floor-bound Δ | non-floor-bound Δ |
|---|---|---|
| m\*+0.25 | n_g=18 / n_u=87 < 50 **withheld** | +0.0163 (g -0.0390 / u -0.0552, n_g=289, n_u=423) |
| m\*+0.50 | +0.0583 (g -0.0236 / u -0.0818, n_g=338, n_u=1058) | -0.0016 (g -0.0844 / u -0.0828, n_g=1019, n_u=1678) |
| m\*+0.75 | +0.0749 (g -0.0208 / u -0.0957, n_g=389, n_u=1322) | -0.0030 (g -0.0885 / u -0.0855, n_g=1712, n_u=2837) |
| m\*+1.00 | +0.0846 (g -0.0169 / u -0.1015, n_g=313, n_u=1161) | -0.0024 (g -0.0783 / u -0.0759, n_g=1788, n_u=2998) |
| m\*+1.25 | +0.1451 (g +0.0523 / u -0.0928, n_g=244, n_u=989) | -0.0075 (g -0.0803 / u -0.0727, n_g=1857, n_u=3170) |
| m\*+1.50 | +0.1577 (g +0.0646 / u -0.0932, n_g=178, n_u=847) | -0.0035 (g -0.0710 / u -0.0675, n_g=1923, n_u=3312) |
| m\*+1.75 | +0.0930 (g -0.0045 / u -0.0975, n_g=138, n_u=743) | +0.0024 (g -0.0619 / u -0.0643, n_g=1963, n_u=3416) |
| m\*+2.00 | +0.0621 (g -0.0216 / u -0.0837, n_g=109, n_u=653) | +0.0082 (g -0.0570 / u -0.0652, n_g=1992, n_u=3506) |
| m\*+2.25 | +0.0908 (g +0.0207 / u -0.0701, n_g=81, n_u=544) | +0.0098 (g -0.0550 / u -0.0648, n_g=2020, n_u=3615) |

- Maximum difference at any offset: **+0.0139**.
- **VERDICT: kill condition (b) FIRES for ETHUSDT.**

**SOLUSDT**

| offset | n gated / ungated | E gated_50 | E ungated | **diff** | ≥0.05R? | floor-bind g / u | gap |
|---|---|---|---|---|---|---|---|
| m\*+0.50 | 1124 / 2178 | +0.0229 | -0.0522 | **+0.0751** | **yes** | 41.6% / 49.4% | -7.8pp |
| m\*+0.75 | 2206 / 4367 | -0.0192 | -0.0583 | **+0.0391** | no | 22.0% / 32.2% | -10.1pp |
| m\*+1.00 | 2522 / 4954 | -0.0315 | -0.0600 | **+0.0285** | no | 14.8% / 22.0% | -7.2pp |
| m\*+1.25 | 2522 / 4954 | -0.0286 | -0.0574 | **+0.0288** | no | 11.5% / 17.3% | -5.8pp |
| m\*+1.50 | 2522 / 4954 | -0.0238 | -0.0522 | **+0.0284** | no | 8.2% / 13.2% | -5.0pp |
| m\*+1.75 | 2522 / 4954 | -0.0201 | -0.0469 | **+0.0269** | no | 5.6% / 9.9% | -4.3pp |
| m\*+2.00 | 2522 / 4954 | -0.0148 | -0.0432 | **+0.0283** | no | 4.1% / 7.7% | -3.5pp |
| m\*+2.25 | 2522 / 4954 | -0.0152 | -0.0417 | **+0.0265** | no | 2.8% / 5.6% | -2.7pp |

Appendix J stratification, same populations:

| offset | floor-bound Δ | non-floor-bound Δ |
|---|---|---|
| m\*+0.50 | +0.1147 (g +0.0197 / u -0.0951, n_g=468, n_u=1077) | +0.0355 (g +0.0252 / u -0.0103, n_g=656, n_u=1101) |
| m\*+0.75 | +0.1301 (g +0.0869 / u -0.0433, n_g=486, n_u=1404) | +0.0162 (g -0.0492 / u -0.0654, n_g=1720, n_u=2963) |
| m\*+1.00 | +0.1094 (g +0.0835 / u -0.0258, n_g=373, n_u=1091) | +0.0182 (g -0.0515 / u -0.0697, n_g=2149, n_u=3863) |
| m\*+1.25 | +0.1033 (g +0.0890 / u -0.0144, n_g=289, n_u=855) | +0.0225 (g -0.0438 / u -0.0663, n_g=2233, n_u=4099) |
| m\*+1.50 | +0.0988 (g +0.0881 / u -0.0107, n_g=206, n_u=654) | +0.0247 (g -0.0338 / u -0.0585, n_g=2316, n_u=4300) |
| m\*+1.75 | +0.0759 (g +0.0725 / u -0.0034, n_g=141, n_u=491) | +0.0262 (g -0.0256 / u -0.0517, n_g=2381, n_u=4463) |
| m\*+2.00 | +0.1369 (g +0.1449 / u +0.0081, n_g=104, n_u=379) | +0.0257 (g -0.0217 / u -0.0474, n_g=2418, n_u=4575) |
| m\*+2.25 | +0.1701 (g +0.1654 / u -0.0048, n_g=71, n_u=275) | +0.0235 (g -0.0205 / u -0.0439, n_g=2451, n_u=4679) |

- Maximum difference at any offset: **+0.0751**, reached at m\*+0.50.
- **VERDICT: kill condition (b) does not fire for SOLUSDT.**

**What the stratification says — Appendix I.1's question, answered.**

I.1 named two possible sources of a gated-minus-ungated gap: **(a) EDGE DETECTION**, the registered thesis, or **(b) VOLATILITY SELECTION**, the gate merely removing trades whose volatility is too low relative to the cost floor. The stratified figures separate them, and they point at (b):

- The gate cuts floor binding by 3–15pp at every offset on every symbol — it is selecting higher-ATR bars exactly as report 11 predicted.
- Among **floor-bound** trades the gate's advantage is large and frequently clears 0.05R on its own.
- Among **non-floor-bound** trades it collapses to roughly +0.02R on BTC and SOL, and on ETH it is **negative at five of nine offsets** — the gated arm is slightly worse than ungated once floor-bound trades are removed.

Per I.1 this is DESCRIPTION and changes no verdict: the 0.05R threshold operates on the unstratified figure, and it is not reached. But it says what the gate is doing. Under mechanism (b) a direct ATR% filter would do the same job more simply, and the session-normalised RVOL apparatus is unnecessary machinery.

### 6.3 (c) UNGATED OUTPERFORMS GATED — THESIS BACKWARDS

**Populations: `gated_50` against `ungated`, period `test`, direction `both`, per symbol per offset.**

| symbol | offsets where ungated outperforms | of | verdict |
|---|---|---|---|
| BTCUSDT | 0 | 8 | **does not fire** |
| ETHUSDT | 0 | 9 | **does not fire** |
| SOLUSDT | 0 | 8 | **does not fire** |

**VERDICT: kill condition (c) does not fire anywhere.** The gated arm beats the ungated arm at every A3-eligible offset on all three symbols. The thesis is not backwards — the gate points the right way. It simply does not point far enough: the sign is right everywhere and the magnitude clears 0.05R at one offset on one symbol.

### 6.4 (d) TWO-OF-THREE

§4.4 defines a corroborating symbol as one whose **gated expectancy exceeds its ungated expectancy by ≥ 0.05R** — explicitly NOT "is profitable", because profitability is a different claim from "the gate works". A symbol qualifies only if it shows that itself AND at least one other symbol shows it too.

| symbol | shows direction of edge? | corroborating symbols | qualifies? |
|---|---|---|---|
| BTCUSDT | no | SOLUSDT | **no** |
| ETHUSDT | no | SOLUSDT | **no** |
| SOLUSDT | **yes** | — | **no** |

**VERDICT: two-of-three FAILS. No symbol qualifies.** 1 of three symbols shows the direction of edge. SOLUSDT shows it, at one offset, but nothing corroborates it; BTCUSDT and ETHUSDT do not show it at all, so SOL cannot corroborate them into qualification either. A rule requiring two symbols is not satisfiable by one.

**Interpretation caveat, per §4.4.** 4.1's concordance measurement may show all three symbols sitting in the same regime cell most of the time, which would make two-of-three weaker evidence than it looks. That caveat cuts toward leniency and the rule still fails, so it changes nothing here.

**On the reading of "passes on its own".** §4.4 defines the corroboration test but not the self-test. Both available readings give the same verdict — under the 0.05R reading only SOL passes and has no corroborator; under the stricter reading (own edge AND a step-3 selection AND positive OOS expectancy) no symbol passes at all. Recorded in §9 as a judgment call whose resolution does not matter.

## 7. Supporting diagnostics — DESCRIPTION ONLY, no thresholds

**Population: `gated_50`, period `test`, direction `both`, arm `full`, pooled per symbol across test folds only.** These exist to inform the next hypothesis, not to rescue this one. No threshold is attached to any figure in this section.

### 7.1 Exit-reason distribution, as a fraction of trades

**BTCUSDT**

| offset | n | stop | target | time_stop | max_hold | insufficient_data |
|---|---|---|---|---|---|---|
| m\*+0.50 | 784 | 0.171 | 0.060 | 0.742 | 0.027 | 0.000 |
| m\*+0.75 | 1581 | 0.189 | 0.060 | 0.723 | 0.028 | 0.000 |
| m\*+1.00 | 1923 | 0.164 | 0.056 | 0.758 | 0.023 | 0.000 |
| m\*+1.25 | 1923 | 0.151 | 0.051 | 0.775 | 0.022 | 0.000 |
| m\*+1.50 | 2177 | 0.142 | 0.054 | 0.781 | 0.023 | 0.000 |
| m\*+1.75 | 2177 | 0.129 | 0.048 | 0.800 | 0.023 | 0.000 |
| m\*+2.00 | 2177 | 0.119 | 0.046 | 0.814 | 0.022 | 0.000 |
| m\*+2.25 | 2177 | 0.106 | 0.041 | 0.831 | 0.022 | 0.000 |

**ETHUSDT**

| offset | n | stop | target | time_stop | max_hold | insufficient_data |
|---|---|---|---|---|---|---|
| m\*+0.25 | 307 | 0.117 | 0.049 | 0.814 | 0.020 | 0.000 |
| m\*+0.50 | 1357 | 0.225 | 0.091 | 0.670 | 0.015 | 0.000 |
| m\*+0.75 | 2101 | 0.237 | 0.089 | 0.656 | 0.018 | 0.000 |
| m\*+1.00 | 2101 | 0.214 | 0.084 | 0.684 | 0.017 | 0.000 |
| m\*+1.25 | 2101 | 0.191 | 0.074 | 0.714 | 0.021 | 0.000 |
| m\*+1.50 | 2101 | 0.171 | 0.068 | 0.741 | 0.020 | 0.000 |
| m\*+1.75 | 2101 | 0.152 | 0.061 | 0.766 | 0.020 | 0.000 |
| m\*+2.00 | 2101 | 0.138 | 0.055 | 0.785 | 0.022 | 0.000 |
| m\*+2.25 | 2101 | 0.119 | 0.049 | 0.810 | 0.021 | 0.000 |

**SOLUSDT**

| offset | n | stop | target | time_stop | max_hold | insufficient_data |
|---|---|---|---|---|---|---|
| m\*+0.50 | 1124 | 0.357 | 0.167 | 0.452 | 0.024 | 0.000 |
| m\*+0.75 | 2206 | 0.303 | 0.130 | 0.549 | 0.019 | 0.000 |
| m\*+1.00 | 2522 | 0.269 | 0.107 | 0.600 | 0.024 | 0.000 |
| m\*+1.25 | 2522 | 0.241 | 0.098 | 0.638 | 0.023 | 0.000 |
| m\*+1.50 | 2522 | 0.211 | 0.088 | 0.679 | 0.021 | 0.000 |
| m\*+1.75 | 2522 | 0.188 | 0.080 | 0.711 | 0.021 | 0.000 |
| m\*+2.00 | 2522 | 0.163 | 0.072 | 0.742 | 0.023 | 0.000 |
| m\*+2.25 | 2522 | 0.146 | 0.064 | 0.765 | 0.025 | 0.000 |

**The time-stop checkpoint is the dominant exit and grows with the stop width.** On BTC it takes 74–83% of trades and rises monotonically with offset; ETH 66–81%; SOL 45–77%. Target exits are rare and shrink as stops widen (BTC 6.0% → 4.1%), which is the mechanical consequence of a wider stop implying a wider +2R target at the same ATR. Max-hold takes 1.5–2.8% throughout, and `insufficient_data` is zero everywhere — the report-13 boundary exclusion means no trade was resolved off the end of the available records.

### 7.2 Holding-time distribution on STOP and TARGET exits only (D6)

§4.5: holding time is degenerate by construction for the time-stop (always 21) and max-hold (always 41) exits, so D6 is answerable only on stop and target exits. Bars **21** and **41** are the reference lines. §4.5's reading: stop/target exits clustering just before 21 means the checkpoint is **catching** an existing mode; smooth through it means the checkpoint is **creating** one.

**BTCUSDT** — fraction of stop+target exits by holding time

| offset | n | 0–5 | 6–10 | 11–15 | 16–20 | **21** | 22–25 | 26–30 | 31–35 | 36–40 | **41** | median |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| m\*+0.50 | 181 | 0.320 | 0.254 | 0.149 | 0.188 | 0.017 | 0.028 | 0.039 | 0.006 | 0.000 | 0.000 | 8 |
| m\*+0.75 | 394 | 0.259 | 0.251 | 0.193 | 0.213 | 0.018 | 0.030 | 0.025 | 0.003 | 0.008 | 0.000 | 10 |
| m\*+1.00 | 422 | 0.273 | 0.258 | 0.192 | 0.194 | 0.014 | 0.021 | 0.028 | 0.014 | 0.005 | 0.000 | 10 |
| m\*+1.25 | 390 | 0.246 | 0.262 | 0.185 | 0.210 | 0.018 | 0.023 | 0.031 | 0.018 | 0.008 | 0.000 | 10 |
| m\*+1.50 | 426 | 0.242 | 0.265 | 0.192 | 0.204 | 0.012 | 0.026 | 0.033 | 0.019 | 0.007 | 0.000 | 10 |
| m\*+1.75 | 386 | 0.246 | 0.269 | 0.197 | 0.197 | 0.013 | 0.026 | 0.026 | 0.018 | 0.008 | 0.000 | 10 |
| m\*+2.00 | 359 | 0.240 | 0.248 | 0.209 | 0.203 | 0.017 | 0.028 | 0.028 | 0.017 | 0.011 | 0.000 | 11 |
| m\*+2.25 | 319 | 0.219 | 0.260 | 0.207 | 0.210 | 0.022 | 0.022 | 0.028 | 0.016 | 0.016 | 0.000 | 11 |

**ETHUSDT** — fraction of stop+target exits by holding time

| offset | n | 0–5 | 6–10 | 11–15 | 16–20 | **21** | 22–25 | 26–30 | 31–35 | 36–40 | **41** | median |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| m\*+0.25 | 51 | 0.176 | 0.235 | 0.216 | 0.294 | 0.020 | 0.039 | 0.000 | 0.020 | 0.000 | 0.000 | 12 |
| m\*+0.50 | 428 | 0.280 | 0.262 | 0.210 | 0.185 | 0.014 | 0.021 | 0.021 | 0.005 | 0.002 | 0.000 | 10 |
| m\*+0.75 | 685 | 0.285 | 0.250 | 0.219 | 0.191 | 0.015 | 0.016 | 0.010 | 0.006 | 0.009 | 0.000 | 10 |
| m\*+1.00 | 627 | 0.281 | 0.257 | 0.207 | 0.198 | 0.013 | 0.021 | 0.010 | 0.005 | 0.010 | 0.000 | 10 |
| m\*+1.25 | 556 | 0.281 | 0.250 | 0.189 | 0.203 | 0.018 | 0.025 | 0.016 | 0.009 | 0.009 | 0.000 | 10 |
| m\*+1.50 | 502 | 0.271 | 0.255 | 0.167 | 0.231 | 0.012 | 0.028 | 0.020 | 0.008 | 0.008 | 0.000 | 10 |
| m\*+1.75 | 449 | 0.263 | 0.258 | 0.167 | 0.236 | 0.011 | 0.027 | 0.020 | 0.009 | 0.009 | 0.000 | 10 |
| m\*+2.00 | 405 | 0.242 | 0.272 | 0.190 | 0.222 | 0.010 | 0.022 | 0.022 | 0.007 | 0.012 | 0.000 | 10 |
| m\*+2.25 | 354 | 0.237 | 0.282 | 0.195 | 0.212 | 0.014 | 0.017 | 0.028 | 0.011 | 0.003 | 0.000 | 10 |

**SOLUSDT** — fraction of stop+target exits by holding time

| offset | n | 0–5 | 6–10 | 11–15 | 16–20 | **21** | 22–25 | 26–30 | 31–35 | 36–40 | **41** | median |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| m\*+0.50 | 589 | 0.341 | 0.272 | 0.188 | 0.153 | 0.005 | 0.020 | 0.010 | 0.005 | 0.003 | 0.002 | 8 |
| m\*+0.75 | 955 | 0.276 | 0.275 | 0.219 | 0.173 | 0.009 | 0.022 | 0.013 | 0.008 | 0.003 | 0.001 | 10 |
| m\*+1.00 | 949 | 0.255 | 0.292 | 0.228 | 0.174 | 0.008 | 0.021 | 0.013 | 0.006 | 0.003 | 0.000 | 10 |
| m\*+1.25 | 856 | 0.239 | 0.292 | 0.216 | 0.195 | 0.009 | 0.019 | 0.014 | 0.008 | 0.007 | 0.000 | 10 |
| m\*+1.50 | 756 | 0.235 | 0.279 | 0.216 | 0.204 | 0.017 | 0.020 | 0.008 | 0.012 | 0.009 | 0.000 | 10 |
| m\*+1.75 | 674 | 0.218 | 0.279 | 0.220 | 0.211 | 0.018 | 0.025 | 0.013 | 0.013 | 0.003 | 0.000 | 11 |
| m\*+2.00 | 593 | 0.187 | 0.287 | 0.228 | 0.226 | 0.012 | 0.029 | 0.012 | 0.010 | 0.010 | 0.000 | 11 |
| m\*+2.25 | 531 | 0.160 | 0.290 | 0.226 | 0.239 | 0.015 | 0.028 | 0.019 | 0.011 | 0.011 | 0.000 | 12 |

**Reading: the checkpoint CREATES the mode, it does not catch one.** The distribution runs smoothly through bar 21 on all three symbols at every offset. The 16–20 bucket holds roughly the same mass as 11–15 with no build-up against the line; bar 21 itself takes 0.5–2.2% of stop/target exits, which is what a single bar out of a smooth distribution should take; and 22–30 continues at a comparable rate rather than falling off a cliff. Roughly 90–95% of stop and target exits happen before bar 21 simply because most trades that are going to resolve resolve early — the median is 8–12 bars — not because anything clusters at the checkpoint.

Bar 41 is empty on stop/target exits almost everywhere, which is expected: a trade still alive at 41 exits `max_hold` by definition.

### 7.3 Expectancy per bar alongside per trade, wherever a time arm appears

§4.5 requires the secondary metric wherever a time arm is compared, because per-trade expectancy silently rewards holding longer. It never overrides the primary metric in a decision, and it does not here.

`minus_max_hold` is **BLOCKED**, not omitted: `CostConfig.max_hold_bars` is a read-only property and no replacement horizon is pre-registered. §4.4 never drops max-hold in any case — it is a GUARD RAIL, *measured and reported, NEVER dropped*.

**BTCUSDT** — `gated_50`, test folds

| offset | full: E/trade | full: E/bar | minus_time_stop: E/trade | minus_time_stop: E/bar | n |
|---|---|---|---|---|---|
| m\*+0.50 | -0.0378 | -0.00199 | +0.0052 | +0.00016 | 784 |
| m\*+0.75 | -0.0613 | -0.00321 | -0.0459 | -0.00144 | 1581 |
| m\*+1.00 | -0.0494 | -0.00257 | -0.0368 | -0.00112 | 1923 |
| m\*+1.25 | -0.0457 | -0.00234 | -0.0328 | -0.00098 | 1923 |
| m\*+1.50 | -0.0330 | -0.00168 | -0.0195 | -0.00058 | 2177 |
| m\*+1.75 | -0.0305 | -0.00155 | -0.0158 | -0.00046 | 2177 |
| m\*+2.00 | -0.0275 | -0.00138 | -0.0132 | -0.00038 | 2177 |
| m\*+2.25 | -0.0258 | -0.00128 | -0.0090 | -0.00025 | 2177 |

**ETHUSDT** — `gated_50`, test folds

| offset | full: E/trade | full: E/bar | minus_time_stop: E/trade | minus_time_stop: E/bar | n |
|---|---|---|---|---|---|
| m\*+0.25 | -0.0376 | -0.00189 | -0.0115 | -0.00034 | 307 |
| m\*+0.50 | -0.0693 | -0.00385 | -0.0835 | -0.00286 | 1357 |
| m\*+0.75 | -0.0760 | -0.00424 | -0.0807 | -0.00279 | 2101 |
| m\*+1.00 | -0.0692 | -0.00379 | -0.0715 | -0.00239 | 2101 |
| m\*+1.25 | -0.0649 | -0.00346 | -0.0625 | -0.00200 | 2101 |
| m\*+1.50 | -0.0595 | -0.00312 | -0.0594 | -0.00185 | 2101 |
| m\*+1.75 | -0.0581 | -0.00301 | -0.0586 | -0.00178 | 2101 |
| m\*+2.00 | -0.0552 | -0.00282 | -0.0567 | -0.00169 | 2101 |
| m\*+2.25 | -0.0521 | -0.00264 | -0.0519 | -0.00151 | 2101 |

**SOLUSDT** — `gated_50`, test folds

| offset | full: E/trade | full: E/bar | minus_time_stop: E/trade | minus_time_stop: E/bar | n |
|---|---|---|---|---|---|
| m\*+0.50 | +0.0229 | +0.00148 | +0.0350 | +0.00156 | 1124 |
| m\*+0.75 | -0.0192 | -0.00114 | -0.0157 | -0.00061 | 2206 |
| m\*+1.00 | -0.0315 | -0.00180 | -0.0246 | -0.00090 | 2522 |
| m\*+1.25 | -0.0286 | -0.00159 | -0.0163 | -0.00057 | 2522 |
| m\*+1.50 | -0.0238 | -0.00129 | -0.0095 | -0.00032 | 2522 |
| m\*+1.75 | -0.0201 | -0.00107 | -0.0068 | -0.00022 | 2522 |
| m\*+2.00 | -0.0148 | -0.00077 | +0.0030 | +0.00009 | 2522 |
| m\*+2.25 | -0.0152 | -0.00078 | +0.0038 | +0.00011 | 2522 |

The two arms share an identical trade universe by construction — the checkpoint changes when a trade exits, not whether it exists — so the `n` column is common to both. Removing the checkpoint improves per-trade expectancy on BTC and SOL at every offset and is roughly neutral on ETH. **This is not a D5 decision and must not be read as one**: D5 is step 7, pools across symbols and folds, and is not run here.

### 7.4 Supplementary: the 30/50/70 pass-rate ladder

Not a step-3 requirement. Included because §4.3 makes the 70%→50%→30% ordering the sharpest falsification test of the RVOL gate — the same question kill condition (b) asks — and the figures were already computed. **No threshold is attached and no decision is gated on it.** Appendix J's floor-binding rates accompany each arm because the arms differ in composition.

**BTCUSDT** — expectancy per trade, test folds, direction `both`

| offset | `gated_70` | `gated_50` | `gated_30` | `ungated` | monotone 70→50→30? | floor-bind 70/50/30/un |
|---|---|---|---|---|---|---|
| m\*+0.50 | -0.0529 | -0.0378 | -0.0771 | -0.0677 | no | 33%/30%/28%/45% |
| m\*+0.75 | -0.0749 | -0.0613 | -0.0750 | -0.0855 | no | 28%/24%/19%/38% |
| m\*+1.00 | -0.0576 | -0.0494 | -0.0569 | -0.0762 | no | 23%/19%/15%/32% |
| m\*+1.25 | -0.0531 | -0.0457 | -0.0510 | -0.0716 | no | 20%/16%/13%/29% |
| m\*+1.50 | -0.0462 | -0.0330 | -0.0249 | -0.0653 | yes | 17%/14%/11%/26% |
| m\*+1.75 | -0.0436 | -0.0305 | -0.0250 | -0.0624 | yes | 15%/11%/9%/23% |
| m\*+2.00 | -0.0413 | -0.0275 | -0.0194 | -0.0601 | yes | 12%/9%/7%/21% |
| m\*+2.25 | -0.0386 | -0.0258 | -0.0174 | -0.0581 | yes | 11%/8%/6%/19% |

**ETHUSDT** — expectancy per trade, test folds, direction `both`

| offset | `gated_70` | `gated_50` | `gated_30` | `ungated` | monotone 70→50→30? | floor-bind 70/50/30/un |
|---|---|---|---|---|---|---|
| m\*+0.25 | -0.0369 | -0.0376 | -0.1074 | -0.0508 | no | 9%/6%/5%/17% |
| m\*+0.50 | -0.0768 | -0.0693 | -0.0834 | -0.0824 | no | 28%/25%/23%/39% |
| m\*+0.75 | -0.0874 | -0.0760 | -0.0710 | -0.0887 | yes | 21%/19%/16%/32% |
| m\*+1.00 | -0.0799 | -0.0692 | -0.0661 | -0.0831 | yes | 18%/15%/12%/28% |
| m\*+1.25 | -0.0758 | -0.0649 | -0.0589 | -0.0775 | yes | 14%/12%/9%/24% |
| m\*+1.50 | -0.0696 | -0.0595 | -0.0532 | -0.0727 | yes | 11%/8%/6%/20% |
| m\*+1.75 | -0.0674 | -0.0581 | -0.0522 | -0.0702 | yes | 9%/7%/5%/18% |
| m\*+2.00 | -0.0653 | -0.0552 | -0.0455 | -0.0681 | yes | 7%/5%/4%/16% |
| m\*+2.25 | -0.0607 | -0.0521 | -0.0431 | -0.0655 | yes | 5%/4%/3%/13% |

**SOLUSDT** — expectancy per trade, test folds, direction `both`

| offset | `gated_70` | `gated_50` | `gated_30` | `ungated` | monotone 70→50→30? | floor-bind 70/50/30/un |
|---|---|---|---|---|---|---|
| m\*+0.50 | -0.0137 | +0.0229 | +0.0334 | -0.0522 | yes | 44%/42%/38%/49% |
| m\*+0.75 | -0.0432 | -0.0192 | -0.0116 | -0.0583 | yes | 25%/22%/19%/32% |
| m\*+1.00 | -0.0502 | -0.0315 | -0.0290 | -0.0600 | yes | 17%/15%/12%/22% |
| m\*+1.25 | -0.0473 | -0.0286 | -0.0273 | -0.0574 | yes | 13%/11%/9%/17% |
| m\*+1.50 | -0.0420 | -0.0238 | -0.0200 | -0.0522 | yes | 10%/8%/6%/13% |
| m\*+1.75 | -0.0379 | -0.0201 | -0.0220 | -0.0469 | no | 7%/6%/4%/10% |
| m\*+2.00 | -0.0344 | -0.0148 | -0.0182 | -0.0432 | no | 5%/4%/3%/8% |
| m\*+2.25 | -0.0324 | -0.0152 | -0.0191 | -0.0417 | no | 3%/3%/2%/6% |

The ordering holds at most offsets — the gate does rank trades, and the sign is consistently right. What it does not do is move the number far: the whole span from `ungated` to `gated_30` is about 0.04R on BTC, 0.02R on ETH and 0.03R on SOL away from the single four-fold point at m\*+0.50, and every figure in the ladder is negative except at that offset. Floor binding falls monotonically across the same ladder, which is the composition effect §6.2 already identified.

## 8. Verification

482 tests pass (444 before this step, 38 added). Every item the task specified:

| # | requirement | how it is enforced |
|---|---|---|
| a | acceptance computed on train, never test | `_acceptance_metrics` raises `TestPeriodLeak` on any record not labelled `train`. The literal `"train"` there is deliberately NOT `SELECT_PERIOD`: a test monkeypatches the selector to `"test"` and requires the pipeline to raise. A guard reading the same constant as the thing it guards is vacuous. A further test recomputes the acceptance trade count straight off the parquet tables, tying the `train` label to the stored data rather than to itself. |
| b | population labels on every figure; step-2 validator reused; planted mutations still pass | `sweep.validate_records` is called on the cells before anything is read; the step-2 label-stripping mutation is re-planted through step 3's entry point; kill-condition rows are asserted to carry `period="test"`, and `_require_test` raises on a train row. |
| c | plateau returns the band centre, not the argmax | a constructed five-point band with monotonically rising expectancy — so its argmax is its LAST point — asserts the centre is returned and that centre ≠ argmax. `band_centre` takes offsets only and never receives an expectancy. |
| d | even-count tie-break returns the HIGHER central offset | tested on Appendix K.3's own worked case (a four-point band, offsets 1.50 to 2.25 → 2.00) and at widths 4 and 6, with an explicit assertion that the LOWER central offset is never returned. |
| e | a two-point run produces NO SELECTION | tested directly, plus a zero-run case, plus two separate two-point runs which must not combine, plus `band_centre` refusing a sub-three run outright. |
| f | determinism | `acceptance_table` and the selection pipeline are asserted equal across two runs; the written artifact is asserted equal to a fresh build; rebuilding the JSON reproduces a byte-identical file. |
| g | holdout seal active, no 2025+ data read | nothing here opens a bar file. A test asserts `authorised` appears nowhere in the module, and another asserts every `signal_bar_ts`, `entry_ts` and `exit_ts` in every trade table step 3 reads falls strictly before `HOLDOUT_TEST_START`. |
| h | full suite passes | 482 passed in 30.4s. |

One further guard: a test greps the module for the names of later steps (`top_5`, `leave_one_out`, `sensitivity_probe`, `collapse`, `intersect_bands`) and fails if step 3 has quietly grown into step 4, 7 or 8.

## 9. Where the specification was ambiguous, and what I decided

### 9.1 K.2(b): whose trade count?

K.2(b) says "the training-fold trade count **for that symbol**" without naming a population. It could mean the `gated_50` count or the `ungated` count. I used **`gated_50`**, because K.2(a) measures expectancy on that arm and the minimum exists to guarantee that expectancy has evidence behind it; a 200-trade minimum satisfied by trades the arm does not contain would be exactly the measured-on-one-population, applied-to-another defect Appendix M.3 catalogues. **The choice is immaterial here:** the smallest `gated_50` training fold holds 364 trades, so clause (b) passes under either reading at every one of the 198 cells. The `ungated` count is carried in the artifact as `n_ungated_train` regardless.

### 9.2 K.2: which direction cohort?

§4.5 keeps long and short cohorts separate throughout, but K.2 states a single expectancy per grid point. I read acceptance on direction `both`, and treated the 30-trade per-direction minimum as a separate commitment that does not gate acceptance. Reading K.2 as requiring both cohorts to pass independently would be a stricter rule than the one written, and it would only remove passing points — it cannot create a candidate that the reported reading does not.

### 9.3 A tie on band WIDTH

K.3 legislates the tie between two central offsets within one band. Neither §4.3 nor K.3 says what to do when two *separate* runs are equally wide. I applied K.3's own stated rationale — a wider stop strictly reduces floor binding, the only structural criterion in this design carrying a threshold — and take the higher band. **The case does not arise in the data:** no fold-symbol has two runs tied at the maximum width. The rule is implemented and tested so that the resolution is on record rather than invented later.

### 9.4 Kill (d): what "passes on its own" means

§4.4 defines the corroboration test (gated − ungated ≥ 0.05R) but never defines the self-test. I applied the same 0.05R definition to the symbol itself, since it is the only definition §4.4 supplies and since §4.4 is explicit that two-of-three is not about profitability. The stricter reading is reported alongside in §6.4. Both give the same verdict, so the ambiguity does not affect the outcome.

### 9.5 Contiguity across an A3-ineligible offset

A3-ineligible offsets were never simulated, so they cannot pass. I treated them as breaking contiguity, consistent with K.2(c) making A3 survival a clause of acceptance and with §4.3 requiring the neighbours themselves to pass. In this data every fold-symbol's A3-eligible set is already contiguous — A3 always cuts a prefix, never a hole — so the rule never has to fire.

## 10. Where I believe the specification is wrong or incomplete

### 10.1 The plateau rule is weak in exactly the way K.2 predicted, and the data shows it

K.2 already records that band edges are noisy because a grid point near zero expectancy passes or fails partly by chance, and that contiguity does not suppress that noise the way it would for independent points, since adjacent offsets share most of their trades. The acceptance table makes this concrete and worse than the prose suggests: **adjacent offsets within a fold are not merely correlated, they are computed on an identical trade universe** — the `n` column is constant across every offset within a fold-symbol (BTC fold 1: 509 at all eight offsets). Only the stop geometry differs. A fold's eight grid points are therefore closer to one observation viewed eight ways than to eight observations, and a run of six passing points is very nearly the single statement "this fold's training expectancy is positive".

The evidence for that: of the 27 fold-symbols, **21 are unanimous** — either every eligible offset passes or none does. Only 6 folds split at all. A selection rule whose output is that close to a per-fold coin-flip on the sign of one number is doing less filtering than "three contiguous points" implies. This is not a request to change the rule — it is frozen and was applied as written. It is a note that the plateau requirement should not be credited with more robustness than it delivers, and that step 4's coverage statistic is the place the instability will actually show.

### 10.2 The kill conditions are not given an aggregation rule over offsets

§4.4 states every threshold with an aggregation rule, and "Every pre-committed threshold carries its aggregation rule" is listed among the unchanged commitments. Kill conditions (a), (b) and (c) do not carry one over the **offset** axis. "OOS expectancy ≤ 0" is a single number in the prose but the sweep produces eight or nine of them per symbol, and "any offset" and "the selected offset" are materially different tests.

This is not hypothetical: it is the whole of SOLUSDT's result. Under "any offset", kill (a) does not fire for SOL and kill (b) does not fire for SOL, both on the strength of the single point m\*+0.50 — which pools four of nine test folds and which no SOL fold selected. Under "the offset the fold actually selected", both fire for all three symbols. I evaluated the **most lenient** reading, "any offset", because it is the one the task specified verbatim ("State for each symbol whether ANY offset gives positive test expectancy") and because a reading chosen after seeing which way it cuts is not a pre-registration. The stricter reading is reported so the difference is visible rather than buried. **The overall outcome is unchanged either way, because two-of-three fails under both.**

### 10.3 Two-of-three cannot distinguish "the gate is weak" from "the strategy is unprofitable"

§4.4 is deliberate that two-of-three tests "the gate works" and not "is profitable", and gives good reasons. The consequence in this data is that the rule's verdict is driven by a quantity — the gated-minus-ungated difference — that is positive on all three symbols at all 25 offsets, while the thing anyone would want to trade is negative almost everywhere. A world in which the gate reliably added 0.06R to a strategy losing 0.30R per trade would pass two-of-three. That is a real gap in the qualification logic, though it does not bite here: the rule fails anyway, and the additional failure of kill (a) on two symbols means nothing reaches step 4 regardless. Recorded because it is a design observation the next iteration should carry, not because it changes this result.

### 10.4 Nothing measures the checkpoint at the selected offset, and the checkpoint is where most trades end

Not a defect in a rule, an absence. 74–83% of BTC trades exit at the checkpoint, and §7.2 shows the checkpoint is creating that mode rather than catching one. The registered thesis is trend continuation, and a strategy that resolves three-quarters of its trades on a fixed clock at bar 21 is not primarily testing trend continuation. Nothing in 4.1–4.5 measures what the trade would have done without the checkpoint at the *selected* offset specifically — the `minus_time_stop` arm exists, but D5 pools it across symbols and folds at step 7 and never at a per-fold selected value. Flagged as informing the next hypothesis, per the task's framing of §6, not as a proposal.

## 11. Outcome

| symbol | folds with a selection | kill (a) | kill (b) | kill (c) | two-of-three | **candidate for step 4?** |
|---|---|---|---|---|---|---|
| BTCUSDT | 4/9 | **FIRES** | **FIRES** | clear | **FAIL** | **NO** |
| ETHUSDT | 0/9 | **FIRES** | **FIRES** | clear | **FAIL** | **NO** |
| SOLUSDT | 2/9 | clear | clear | clear | **FAIL** | **NO** |

**NO SYMBOL PRODUCES A CANDIDATE FOR STEP 4.**

ETHUSDT fails at the first hurdle — no fold produces a selection, because no ETH training cell anywhere in the grid has positive expectancy. BTCUSDT produces selections in four folds but its OOS expectancy is negative at every offset and its gate contributes at most 0.033R. SOLUSDT produces selections in two folds and is the only symbol to show the §4.4 direction of edge, at one offset, which no fold selected and which nothing corroborates.

Per §5 of the task and §4.3/§4.4 of the pre-registration: **the procedure is exhausted and that is the finding.** No variant has been searched, no threshold relaxed, no range extended, no alternative configuration proposed. The nine-step sequence does not continue to step 4.

This is the protocol working as designed. The pre-registered expectation recorded before any number arrived was that the second most likely outcome of Point 4 was that *"the RVOL gate proves decorative"*, on the grounds that the structural pass had already found its selectivity largely pre-spent by conditioning on the breakout. That is close to what happened, with one refinement the stratification supplies: the gate is not inert — it orders trades correctly at every offset on every symbol — but §6.2 locates its contribution almost entirely in the removal of floor-bound trades rather than in edge detection. **The validation protocol does not create edge. It prevents belief in edge that is not there.**

---

*Report generated from `data/derived/sweep/bands.json` by `src/sweep/bands.py`. Every figure above is rendered from the artifact; none is transcribed by hand.*
