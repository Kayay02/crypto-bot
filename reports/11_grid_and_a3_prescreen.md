# Report 11 — Point 4.3 Grid Definition and A3 Pre-Screen (Step 0, Pre-Lift)

The full sweep grid and the A3 floor-binding pre-screen, computed entirely before the firewall lifts.

**The firewall has not lifted.** Every quantity here is an entry-time structural property — binding rates, pass rates, signal counts, ATR percentiles. Layer B was never run; `simulate` and `src.regime` are never imported (AST *and* runtime checks); no trade outcome was read. Per Appendix F.2 this is step 0 and is not a partial lift: it inspects no performance figure at all.

**Holdout sealed.** Nothing at or after 2025-01-01 was loaded. `src/folds/` enforces this with `authorised=False` defaults and nothing here overrides them.

**Pre-registration frozen at `65dc3d7`** (Appendices F, G, H committed before any code was written against them). Grid artifact at `7f93257`.

---

## 1. File tree and tests

```
src/sweep/
  __init__.py      19 lines   purpose, firewall statement, holdout seal
  grid.py         283 lines   m*, the 11 multipliers, derived cap, RVOL thresholds
  prescreen.py    204 lines   floor/cap binding, A3 verdict, survival summary
tests/
  test_sweep_grid.py       37 tests
  test_sweep_prescreen.py  28 tests

data/derived/sweep/
  grid.json       TRACKED — per fold per symbol, plus the A3 verdict
```

**65 new tests. Full suite: 329 passing**, up from 264. Runtime 14.4s. Nothing outside `src/sweep/`, `tests/` and one `.gitignore` negation was modified; no existing artifact was regenerated.

Verification coverage: population invariance (a), the 50% identity at m\* (b), the 5% cap identity and its monotonicity (c), grid shape (d), RVOL target pass rates (e), floor-binding monotonicity (f), training-only causality (g), firewall AST/runtime (h), holdout refusal (i).

---

## 2. The grid, per fold per symbol

`m* = stop_min_pct / median(ATR%)` over training-fold breakout bars; cap `= (m*+2.5) × P95(ATR%)`; RVOL thresholds at 30/50/70% pass rates on the same population.

### BTCUSDT — floor 1.020%

| fold | med ATR% | P95 ATR% | m\* | range (absolute) | cap % | rv30 | rv50 | rv70 |
|---|---|---|---|---|---|---|---|---|
| 1 | 0.4570 | 1.1653 | 2.232 | 2.23 – 4.73 | 5.514 | 3.365 | 2.416 | 1.780 |
| 2 | 0.3701 | 0.8093 | 2.756 | 2.76 – 5.26 | 4.254 | 3.454 | 2.484 | 1.783 |
| 3 | 0.2943 | 0.7607 | 3.466 | 3.47 – 5.97 | 4.538 | 5.056 | 3.184 | 2.081 |
| 4 | 0.3058 | 0.6575 | 3.335 | 3.34 – 5.84 | 3.837 | 4.883 | 3.162 | 2.081 |
| 5 | 0.2144 | 0.4937 | 4.757 | 4.76 – 7.26 | 3.583 | 3.455 | 2.186 | 1.405 |
| 6 | 0.2109 | 0.5007 | 4.835 | 4.84 – 7.34 | 3.673 | 3.264 | 2.149 | 1.415 |
| 7 | 0.3136 | 0.7451 | 3.252 | 3.25 – 5.75 | 4.286 | 2.764 | 1.878 | 1.399 |
| 8 | 0.3560 | 0.7665 | 2.865 | 2.87 – 5.37 | 4.113 | 2.117 | 1.554 | 1.206 |
| 9 | 0.3552 | 0.6954 | 2.871 | 2.87 – 5.37 | 3.735 | 3.345 | 2.073 | 1.431 |

### ETHUSDT — floor 1.020%

| fold | med ATR% | P95 ATR% | m\* | range (absolute) | cap % | rv30 | rv50 | rv70 |
|---|---|---|---|---|---|---|---|---|
| 1 | 0.6290 | 1.3363 | 1.622 | 1.62 – 4.12 | 5.508 | 3.951 | 2.825 | 2.023 |
| 2 | 0.5682 | 1.1488 | 1.795 | 1.80 – 4.30 | 4.934 | 4.396 | 2.977 | 2.054 |
| 3 | 0.3889 | 0.9474 | 2.623 | 2.62 – 5.12 | 4.853 | 5.219 | 3.195 | 2.055 |
| 4 | 0.3410 | 0.6965 | 2.991 | 2.99 – 5.49 | 3.824 | 4.440 | 2.730 | 1.779 |
| 5 | 0.2328 | 0.5243 | 4.382 | 4.38 – 6.88 | 3.608 | 2.932 | 1.931 | 1.288 |
| 6 | 0.2703 | 0.5586 | 3.773 | 3.77 – 6.27 | 3.504 | 2.813 | 1.943 | 1.320 |
| 7 | 0.3775 | 0.8712 | 2.702 | 2.70 – 5.20 | 4.532 | 2.426 | 1.777 | 1.285 |
| 8 | 0.4150 | 0.8987 | 2.458 | 2.46 – 4.96 | 4.456 | 1.932 | 1.454 | 1.133 |
| 9 | 0.4084 | 0.8031 | 2.498 | 2.50 – 5.00 | 4.014 | 3.755 | 2.208 | 1.413 |

### SOLUSDT — floor 1.320%

| fold | med ATR% | P95 ATR% | m\* | range (absolute) | cap % | rv30 | rv50 | rv70 |
|---|---|---|---|---|---|---|---|---|
| 1 | 0.8160 | 1.7037 | 1.618 | 1.62 – 4.12 | 7.015 | 2.470 | 1.745 | 1.258 |
| 2 | 0.6786 | 1.4315 | 1.945 | 1.95 – 4.45 | 6.363 | 3.789 | 2.325 | 1.582 |
| 3 | 0.6766 | 1.6785 | 1.951 | 1.95 – 4.45 | 7.471 | 4.810 | 2.802 | 1.689 |
| 4 | 0.6110 | 1.3688 | 2.160 | 2.16 – 4.66 | 6.379 | 4.480 | 2.729 | 1.683 |
| 5 | 0.4682 | 0.9893 | 2.819 | 2.82 – 5.32 | 5.262 | 4.592 | 2.722 | 1.638 |
| 6 | 0.6411 | 1.4775 | 2.059 | 2.06 – 4.56 | 6.736 | 4.341 | 2.555 | 1.631 |
| 7 | 0.8177 | 1.6143 | 1.614 | 1.61 – 4.11 | 6.642 | 4.340 | 2.700 | 1.668 |
| 8 | 0.7085 | 1.5351 | 1.863 | 1.86 – 4.36 | 6.698 | 4.417 | 2.895 | 1.798 |
| 9 | 0.6272 | 1.3558 | 2.104 | 2.10 – 4.60 | 6.243 | 3.788 | 2.485 | 1.654 |

**m\* moves substantially between folds** — BTC ranges 2.23 to 4.84, more than a factor of two. This is exactly why §4.4 collapses fold selections as *offsets from m\**, not as absolute multipliers: an absolute value of 3.5 is near the bottom of fold 3's range and below the bottom of fold 5's.

RVOL thresholds hit their targets to within 1pp on all 81 cells (27 fold-symbols × 3 arms); measured deviation is under 0.4pp everywhere.

---

## 3. Sanity checks — both construction identities hold

### m\* identity: floor binds ~50% of breakout bars at multiplier = m\*

| fold | BTC | ETH | SOL |
|---|---|---|---|
| 1 | 50.0% | 50.0% | 50.0% |
| 2 | 49.9% | 49.9% | 50.0% |
| 3 | 49.9% | 50.0% | 50.0% |
| 4 | 49.9% | 50.0% | 50.1% |
| 5 | 49.9% | 49.9% | 50.0% |
| 6 | 49.9% | 50.0% | 50.0% |
| 7 | 50.0% | 50.0% | 50.0% |
| 8 | 50.0% | 50.0% | 50.0% |
| 9 | 50.0% | 50.0% | 50.0% |

**Range 49.93% – 50.05%; maximum deviation from 50% is 0.066pp.** The identity holds exactly as Appendix F.1 requires. (It is an identity, not an empirical result: the floor equals `m* × median`, so at multiplier `m*` it binds precisely when `ATR% < median`. Its value is that it would break loudly if the population or the binding computation were wrong.)

### Cap identity: cap binds ~5% of breakout bars at m\*+2.5

Range **5.01% – 5.10%** across all 27 fold-symbols. Amendment 6 works as designed. The superseded median form is separately measured in-test at 49.9–50.0%, confirming the defect Appendix H corrects.

### Monotonicity

Floor binding is **monotonically decreasing in the multiplier: zero violations** across all 297 cells (27 fold-symbols × 11 points) on every population — breakout, gated-30, gated-50, gated-70. Cap binding is monotonically increasing everywhere.

### Gated vs breakout

**Gated floor binding is below breakout floor binding in 297 of 297 cells (100%).** The hypothesis holds: the RVOL gate selects higher-volume bars, which are higher-ATR. The gap is large — at multiplier m\*, breakout binding is 50% by construction while gated binding is 21.8–43.6%:

| fold | BTC brk/gat | ETH brk/gat | SOL brk/gat |
|---|---|---|---|
| 1 | 50.0 / 38.9 | 50.0 / 38.1 | 50.0 / 43.6 |
| 2 | 49.9 / 41.6 | 49.9 / 38.5 | 50.0 / 41.9 |
| 3 | 49.9 / 32.3 | 50.0 / 31.7 | 50.0 / 35.4 |
| 4 | 49.9 / 28.8 | 50.0 / 28.6 | 50.1 / 35.1 |
| 5 | 49.9 / 24.3 | 49.9 / 21.8 | 50.0 / 33.8 |
| 6 | 49.9 / 25.3 | 50.0 / 26.0 | 50.0 / 41.5 |
| 7 | 50.0 / 37.8 | 50.0 / 37.2 | 50.0 / 38.0 |
| 8 | 50.0 / 33.3 | 50.0 / 37.4 | 50.0 / 38.9 |
| 9 | 50.0 / 38.9 | 50.0 / 40.1 | 50.0 / 42.5 |

This 6–28pp gap is the single most consequential number in the pre-screen: it is why A3 passes as widely as it does. See §7.1.

---

## 4. The A3 table

Floor binding on the **gated population at the 50% RVOL arm**, per §4.4. `*` marks a grid point passing A3 (< 20%). Columns are offsets from m\*.

### BTCUSDT

| fold | 0.0 | 0.25 | 0.5 | 0.75 | 1.0 | 1.25 | 1.5 | 1.75 | 2.0 | 2.25 | 2.5 | surv | run |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 38.9 | 28.1 | 17.9\* | 12.8\* | 9.6\* | 5.1\* | 3.3\* | 1.8\* | 0.8\* | 0.8\* | 0.6\* | 9 | 9 |
| 2 | 41.6 | 36.4 | 30.9 | 26.6 | 23.9 | 20.5 | 17.7\* | 15.5\* | 13.6\* | 12.3\* | 11.1\* | **5** | 5 |
| 3 | 32.3 | 29.7 | 24.5 | 21.6 | 18.5\* | 17.2\* | 16.4\* | 14.3\* | 11.7\* | 10.4\* | 9.4\* | 7 | 7 |
| 4 | 28.8 | 23.7 | 19.8\* | 15.3\* | 13.2\* | 11.3\* | 9.8\* | 8.7\* | 7.1\* | 5.5\* | 4.5\* | 9 | 9 |
| 5 | 24.3 | 20.9 | 17.9\* | 13.8\* | 11.8\* | 9.3\* | 6.9\* | 6.4\* | 5.7\* | 5.4\* | 4.7\* | 9 | 9 |
| 6 | 25.3 | 22.8 | 18.5\* | 15.7\* | 14.3\* | 10.6\* | 9.4\* | 7.0\* | 6.8\* | 6.2\* | 5.5\* | 9 | 9 |
| 7 | 37.8 | 31.4 | 27.1 | 22.6 | 18.5\* | 16.2\* | 13.3\* | 11.3\* | 10.5\* | 9.2\* | 8.2\* | 7 | 7 |
| 8 | 33.3 | 25.7 | 21.3 | 16.5\* | 13.4\* | 11.1\* | 9.2\* | 6.9\* | 5.2\* | 3.6\* | 3.1\* | 8 | 8 |
| 9 | 38.9 | 31.5 | 25.7 | 19.5\* | 14.9\* | 12.2\* | 9.7\* | 8.7\* | 5.8\* | 4.1\* | 3.7\* | 8 | 8 |

### ETHUSDT

| fold | 0.0 | 0.25 | 0.5 | 0.75 | 1.0 | 1.25 | 1.5 | 1.75 | 2.0 | 2.25 | 2.5 | surv | run |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 38.1 | 24.5 | 14.1\* | 7.6\* | 4.6\* | 2.4\* | 1.5\* | 0.6\* | 0.2\* | 0.0\* | 0.0\* | 9 | 9 |
| 2 | 38.5 | 30.6 | 24.2 | 19.6\* | 15.2\* | 12.3\* | 9.5\* | 8.4\* | 5.7\* | 4.8\* | 4.0\* | 8 | 8 |
| 3 | 31.7 | 24.9 | 19.6\* | 15.2\* | 12.6\* | 9.4\* | 8.1\* | 6.3\* | 5.2\* | 4.7\* | 3.9\* | 9 | 9 |
| 4 | 28.6 | 23.4 | 16.5\* | 13.2\* | 9.3\* | 7.1\* | 6.3\* | 4.4\* | 4.1\* | 3.6\* | 2.7\* | 9 | 9 |
| 5 | 21.8 | 17.9\* | 14.5\* | 13.0\* | 9.9\* | 7.8\* | 6.2\* | 3.9\* | 3.1\* | 2.1\* | 1.6\* | **10** | 10 |
| 6 | 26.0 | 21.9 | 19.1\* | 16.8\* | 13.3\* | 11.4\* | 9.5\* | 8.0\* | 7.1\* | 5.2\* | 3.2\* | 9 | 9 |
| 7 | 37.2 | 29.1 | 20.3 | 13.8\* | 9.1\* | 7.1\* | 5.4\* | 4.3\* | 3.5\* | 3.0\* | 2.8\* | 8 | 8 |
| 8 | 37.4 | 26.6 | 17.7\* | 12.5\* | 9.1\* | 6.2\* | 5.0\* | 4.0\* | 2.5\* | 2.1\* | 1.5\* | 9 | 9 |
| 9 | 40.1 | 30.3 | 21.6 | 16.1\* | 11.2\* | 7.1\* | 5.1\* | 3.7\* | 2.6\* | 2.0\* | 1.2\* | 8 | 8 |

### SOLUSDT

| fold | 0.0 | 0.25 | 0.5 | 0.75 | 1.0 | 1.25 | 1.5 | 1.75 | 2.0 | 2.25 | 2.5 | surv | run |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 43.6 | 26.3 | 14.3\* | 7.2\* | 4.1\* | 2.7\* | 1.9\* | 1.6\* | 1.1\* | 0.6\* | 0.2\* | 9 | 9 |
| 2 | 41.9 | 28.3 | 20.7 | 16.8\* | 13.1\* | 9.4\* | 6.7\* | 4.4\* | 2.3\* | 1.6\* | 1.6\* | 8 | 8 |
| 3 | 35.4 | 25.4 | 18.6\* | 14.1\* | 9.6\* | 7.2\* | 4.7\* | 3.3\* | 2.2\* | 1.2\* | 1.2\* | 9 | 9 |
| 4 | 35.1 | 29.3 | 22.8 | 17.4\* | 13.7\* | 11.2\* | 8.1\* | 6.8\* | 4.4\* | 3.5\* | 3.1\* | 8 | 8 |
| 5 | 33.8 | 26.1 | 20.4 | 14.3\* | 10.4\* | 7.7\* | 5.7\* | 4.5\* | 4.1\* | 2.4\* | 2.0\* | 8 | 8 |
| 6 | 41.5 | 33.2 | 26.3 | 20.2 | 15.2\* | 10.7\* | 7.3\* | 5.0\* | 3.1\* | 2.3\* | 1.5\* | 7 | 7 |
| 7 | 38.0 | 26.8 | 16.5\* | 9.7\* | 6.3\* | 4.2\* | 3.5\* | 2.3\* | 1.8\* | 0.9\* | 0.4\* | 9 | 9 |
| 8 | 38.9 | 26.1 | 17.0\* | 12.7\* | 9.0\* | 5.8\* | 3.9\* | 3.2\* | 2.5\* | 1.9\* | 1.0\* | 9 | 9 |
| 9 | 42.5 | 31.2 | 24.5 | 16.7\* | 12.0\* | 8.3\* | 5.7\* | 3.7\* | 2.4\* | 1.2\* | 0.8\* | 8 | 8 |

Breakout-population binding is 50% at offset 0 in every cell by construction and falls monotonically; the full breakout series is in `grid.json` under `breakout_floor_binding_by_offset`.

**A3 never passes at offset 0** in any of the 27 fold-symbols. The range correctly begins where it does: searching below m\* would search a region already known to be floor-dominated, exactly as §4.3 argues.

**Because binding is monotonically decreasing, every surviving set is a contiguous suffix** running to the top of the grid. So `surviving = longest run` in all 27 cells, and the "contiguous run of three" test reduces to "at least three survivors".

The 30% and 70% arms are in `grid.json`; they shift the whole curve as expected (the 30% arm admits only the highest-volume, highest-ATR bars, so binding is lower still) and do not change any A3 verdict, which is decided on the 50% arm alone.

---

## 5. Cap binding — a finding, reported prominently as Appendix H requires

**On breakout bars the derivation works exactly:** 5.01% – 5.10% at the top grid point, monotonically lower below.

**On the gated population it does not.** At m\*+2.5:

| fold | BTC brk/gat | ETH brk/gat | SOL brk/gat |
|---|---|---|---|
| 1 | 5.0 / 7.9 | 5.0 / 7.8 | 5.0 / 5.0 |
| 2 | 5.0 / 8.9 | 5.1 / 9.0 | 5.0 / 8.8 |
| 3 | 5.1 / 9.1 | 5.1 / 8.4 | 5.0 / 9.4 |
| 4 | 5.0 / 9.8 | 5.1 / 9.3 | 5.1 / 9.3 |
| 5 | 5.0 / 9.8 | 5.1 / 9.6 | 5.1 / **10.2** |
| 6 | 5.0 / **10.0** | 5.1 / 8.8 | 5.1 / 7.7 |
| 7 | 5.1 / 6.8 | 5.0 / 6.9 | 5.0 / 8.8 |
| 8 | 5.1 / 7.3 | 5.0 / 8.1 | 5.0 / 8.1 |
| 9 | 5.0 / 8.3 | 5.1 / 7.9 | 5.1 / 5.7 |

**Gated cap binding runs 5.04% – 10.18%, mean 8.40% — 1.66× the breakout figure, and double the 5% target in the worst cells.** Appendix H states: *"a cap binding materially above 5% at any grid point is a finding about this derivation and must be reported."* This is that finding.

**The cause is structural, not a bug.** Appendix F.1 fixes the cap's population to breakout bars — the same population as m\*, deliberately, so the two anchors are consistent. But the cap is *applied* to the traded (gated) population, and gated bars are higher-ATR. Measured at fold 5: gated P95 exceeds breakout P95 by 9–16% (BTC 0.4937 → 0.5393; ETH 0.5243 → 0.5710; SOL 0.9893 → 1.1443). A threshold set at the breakout P95 therefore sits below the gated P95 and catches roughly twice as many gated bars.

This is the *same* effect that makes A3 pass more easily — the gate shifts the ATR distribution upward — acting in the opposite direction on the cap. It is internally consistent and was foreseeable from F.1, but its magnitude was not stated anywhere.

**I have not changed anything in response.** The derivation is frozen at Appendix H, this is step 0, and §4.3 forbids adjusting a criterion to make a result come out right. What it means practically: at the top of the grid the cap is roughly twice as active on real trades as the 5% design intent, which is still an order of magnitude short of the 50% defect Amendment 6 fixed. Whether that warrants an Amendment 7 (anchoring the cap on the gated P95, at the cost of making the cap depend on `rvol_threshold` — precisely what F.1 rejected for m\*) is a decision for you, pre-lift, and I flag rather than propose it.

---

## 6. Surviving grid and the tradability verdict

| symbol | folds with a viable band (≥3 contiguous survivors) | min survivors in any fold | verdict |
|---|---|---|---|
| **BTCUSDT** | **9 / 9** | 5 (fold 2, offsets 1.50–2.50) | **TRADABLE** |
| **ETHUSDT** | **9 / 9** | 8 (folds 2, 7, 9) | **TRADABLE** |
| **SOLUSDT** | **9 / 9** | 7 (fold 6, offsets 1.00–2.50) | **TRADABLE** |

**All three symbols clear A3 in every fold.** Stated plainly: on the floor-binding criterion, **BTC, ETH and SOL are all tradable at $2,000 with these fees**, and the pre-registered tradability finding did **not** materialise.

This contradicts the pre-registration's own stated expectation. §4.3's "weakest link" section says: *"The most likely single outcome of Point 4 is a TRADABILITY FINDING ON BTC, not a strategy verdict… There is a real chance the m\*+2.5 range is exhausted without reaching 20%."* That did not happen — BTC clears at offset 0.5 in five of nine folds and at worst needs offset 1.5.

BTC is nonetheless the tightest symbol, as predicted: it has the narrowest surviving band (fold 2, five points), the two highest m\* values (4.76, 4.84), and the highest floor-binding at every offset. The direction of the prediction was right; the magnitude was not.

**§4.3's plateau rule excludes the range edges from selection** ("a value at the edge of the searched range… fails the plateau requirement"). Removing offsets 0.0 and 2.5 from the eligible set, **every fold-symbol still retains ≥3 contiguous eligible points** (worst case BTC fold 2: four points, 1.50–2.25). So the plateau rule is satisfiable everywhere on A3 grounds. Whether an *acceptance* plateau exists is a post-lift question this pre-screen cannot answer.

---

## 7. Judgment calls and ambiguities

**7.1 — the gated-vs-breakout gap is what makes A3 pass, and it deserves stating explicitly.** A3 is evaluated on the gated population per §4.4, and that population's floor binding is 6–28pp below the breakout population's at m\*. Had A3 been evaluated on breakout bars instead, it would fail at offsets 0–0.5 almost everywhere and the surviving bands would be materially narrower. The choice of population is therefore not a detail — it is the single largest driver of the verdict. §4.4 is unambiguous that A3 is about the traded population, so the choice is right, but the result is much more sensitive to it than the text suggests.

**7.2 — long and short ATR distributions differ, and I pooled anyway as instructed.** Median ATR% is 5–6% higher on short breakouts than long (BTC 0.3116 vs 0.3276; ETH 0.3936 vs 0.4171; SOL 0.6524 vs 0.6912), consistent across all three symbols. Worst single fold-symbol median deviation is **20.1%**. P95 diverges more: **16–22% higher on shorts** in every symbol.

In m\* terms the pooling cost is small — direction-specific m\* would differ by ~0.16 (BTC 3.274 long-only vs 3.114 short-only), which is under one grid step of 0.25. But the cap inherits the larger P95 divergence, so a pooled cap is ~10% loose for shorts and ~10% tight for longs. **Pooled per instruction and flagged.** Nothing in §4.3 or Appendix F.1 addresses direction, so this is genuinely unspecified rather than a departure.

**7.3 — "approximately 50%" and "approximately 5%" were given a 1pp tolerance.** Measured deviations are far smaller (0.066pp and 0.10pp), so the tolerance never binds. Both are identities rather than estimates, so a tight tolerance is appropriate; a loose one would let a real population error pass.

**7.4 — RVOL thresholds use `quantile(1 − target)` with `>=` comparison.** On a continuous distribution this hits the target exactly; ties would make it approximate. Realised pass rates are within 0.4pp everywhere, so ties are not material at these sample sizes.

**7.5 — test-period binding is computed and stored but never read by any criterion.** §4.4 makes A3 a training-fold quantity. I compute the test-period figures as description (they are in `grid.json`) and a test asserts the A3 verdict reads only the training gated arm. They are not in this report's tables to avoid implying they carry weight.

**7.6 — `grid.json` stores the A3 and cap binding series by offset, not the full per-population detail.** The full breakdown (all four populations × 11 offsets × 27 cells) would be ~3,500 numbers. The artifact stores what a later step needs — m\*, multipliers, cap, RVOL thresholds, A3 binding, cap binding, breakout binding, survival — and the rest is reproducible from the committed code.

---

## 8. Where I think the specification is worth questioning

**8.1 — Appendix H's 5% guarantee holds on the wrong population.** See §5. Amendment 6 fixes the cap to the breakout P95 so that it shares m\*'s population (F.1's consistency argument), but the cap's *purpose* — "inert under normal conditions, active only in genuine volatility spikes" — is a statement about trades, and trades are the gated population. On that population it binds at 8.4% mean and 10.2% worst, not 5%.

Amendment 6 is still a large improvement (50% → 8.4%) and I would not undo it. But the appendix asserts "the cap then binds on 5% of breakout bars at the widest grid point" as though that settles the guard-rail question, and it does not: it settles it for a population the cap is never applied to. The honest statement is that the cap binds ~5% of *breakout* bars and ~8% of *traded* bars.

Fixing it would mean anchoring on the gated P95, which makes the cap depend on `rvol_threshold` — the exact dependency F.1 rejected for m\*. That is a real tension, not an oversight, and it is why I flag rather than recommend.

**8.2 — the pre-registered "weakest link" expectation was wrong, and that is worth recording explicitly.** §4.3 predicted a BTC tradability finding as the most likely single outcome of Point 4. On the A3 criterion it did not occur, in any fold. The prediction was made from M8's per-symbol-year m\* range (1.71–4.08) and the observation that the derived floor sits above a level already binding on 65–81% of trades.

The reason it was wrong looks to be the gated-population effect of §7.1: the earlier binding figures were measured on a different population than A3 evaluates. This does not vindicate or damage the strategy — A3 is a structural check, not an edge test — but a pre-registered expectation that failed should be recorded as failed rather than quietly passed over. §4.3's accompanying commitment ("if it happens, the range is not widened") was never tested because the range never needed widening.

**8.3 — §4.3's plateau rule and the A3 suffix structure interact in a way nothing anticipates.** Because floor binding decreases monotonically, A3 survivors always form a suffix running to the top of the grid. The plateau rule then excludes the top edge. So the A3-eligible, plateau-eligible set is always `[first survivor … m*+2.25]`. Nothing is broken — every cell retains ≥3 points — but it means A3 can only ever remove points from the *bottom* of the range, and the effective search space is bounded above by the plateau rule rather than by A3. Worth knowing before reading a selected offset near 2.25 as "comfortably inside the range".

**8.4 — the fold-to-fold variation in m\* is larger than §4.3's collapse procedure may have anticipated.** BTC's m\* ranges 2.23–4.84 across folds, a factor of 2.2. §4.4's band-intersection collapse expresses each fold's band as an offset from m\*, which handles this correctly. But it means the *absolute* multiplier implied by a common offset varies enormously — offset 1.0 is multiplier 3.23 in fold 1 and 5.76 in fold 6. The ±25% sensitivity kill condition operates "on the SELECTED value in absolute multiplier terms per fold", so it will be a very different test in different folds. Consistent with the design as written; just larger in practice than the text implies.

---

## 9. Artifact and verification

`data/derived/sweep/grid.json` is **tracked** and carries a **clean commit hash** (`7f93257910da0a74ddaab89a1f4c1fa361920304`, no `-dirty` suffix). Verified with `git add --dry-run`, which refuses ignored paths — `git check-ignore -v` exits 0 on a negation match and will mislead you:

| path | result |
|---|---|
| `data/derived/sweep/grid.json` | **ADDABLE (tracked)** |
| `data/derived/folds/folds.json` | ADDABLE (tracked) |
| `data/derived/regime/terciles.json` | ADDABLE (tracked) |
| `data/derived/regime/*.parquet` | ignored |
| `data/derived/ohlcv_15m/*.parquet` | ignored |

| check | result |
|---|---|
| breakout population invariant to the three swept parameters | ✓ bar-for-bar, incl. poisoned rvol/rsi |
| floor binds ~50% at m\* on breakout bars | ✓ 49.93–50.05%, all 27 cells |
| cap binds ~5% at m\*+2.5 on breakout bars | ✓ 5.01–5.10% |
| median cap form measured at 50% (the corrected defect) | ✓ in-test |
| grid exactly 11 points spanning exactly 2.5 | ✓ all cells |
| RVOL thresholds hit 30/50/70% targets | ✓ within 0.4pp |
| floor binding monotonically decreasing | ✓ 0 violations / 297 cells / 4 populations |
| gated binding ≤ breakout binding | ✓ 297 / 297 |
| training-only causality (test period truncated away) | ✓ identical m\*, cap, thresholds |
| no `simulate`, no `src.regime` (AST + runtime) | ✓ |
| no outcome-derived token in executable code | ✓ |
| holdout refuses by default | ✓ `PermissionError` |
| full suite | ✓ **329 passing** |

**The firewall has not lifted.** No number in this report is a performance figure: every one is a binding rate, a pass rate, an ATR percentile, a count, or a multiplier. The lift occurs at step 1 (E6) and has not been reached.
