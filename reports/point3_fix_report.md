# Point 3 — Fix Pass Report

Commit `106cb42` (previous pass: `d04ba47`).
Generated from the committed tree; all figures reproduced from actual runs.

---

## 1. FILE TREE + COMMIT + TEST COUNTS

```
src/engine/contracts.py
src/engine/costs.py
src/engine/diagnostics.py
src/engine/README.md
src/engine/run.py
src/engine/signals.py
src/engine/simulate.py
tests/conftest.py
tests/golden/btc_2023_01_gated.csv
tests/golden/btc_2023_01_gated.sha256
tests/make_golden.py
tests/test_costs.py
tests/test_determinism_golden.py
tests/test_fixtures_lifecycle.py
tests/test_holding_rules.py
tests/test_manifest_integrity.py
tests/test_modes.py
tests/test_portfolio.py
tests/test_regression_pinned_trade.py
tests/test_signals.py
tests/test_trace_and_prohibitions.py
```

New this pass: `src/engine/diagnostics.py`, `tests/test_holding_rules.py`,
`tests/test_modes.py`, `tests/test_regression_pinned_trade.py`.

**Commit:** `106cb42` — "Point 3 fix pass: separate time-stop from max-hold,
net +1R, signal mode"

**Tests:** `88 passed, 0 failed, 2 deselected` (default run).
The 2 deselected are the planted look-ahead demos; run explicitly with
`-m lookahead --override-ini="addopts="` they are `2 passed`.
Previous pass was 59 passed; +29 tests this pass.

---

## 2. MANIFEST CHECK

**PASS.** All 26 outputs in `_manifest.json` present; every Parquet row count
matches; every raw source SHA256 matches. Enforced continuously by
`tests/test_manifest_integrity.py` (4 tests, all passing), so the engine cannot
run against altered data. Raw layer untouched by this pass.

---

## 3. BLOCKING FIXES

### B1 — the time stop was unconditional

The walk buffer was `TIME_STOP_BARS * 15 + 1`, i.e. the 1m array handed to each
trade was sized from the *time stop*. Any trade that survived to the end of that
array was force-closed with `exit_reason = "walk_end"`, regardless of whether it
had reached +1R and earned the right to continue. That was 10 of 44 trades on
the golden slice — 23% of the universe silently capped at 16 bars, not an edge
case.

`time_stop_bars` (16) and `max_hold_bars` (48) are now separate config values
with an assertion that `max_hold_bars > time_stop_bars`, raised at config
construction. The time stop fires only when net +1R has *not* been reached;
`max_hold` is the cap for trades that did reach it. `max_walk_minutes(cfg)` is
now *derived* as `max_hold_bars * 15 + 2` and is documented as not a parameter.
`walk_end` is gone: exhausting the buffer now means the *data* ran out, which is
`exit_reason = "insufficient_data"` and is counted separately from every
trading decision. `test_walk_buffer_is_derived_and_outlasts_max_hold` fails if
the buffer could ever terminate a trade before `max_hold_bars`, at three
different `max_hold_bars` settings.

### B2 — +1R was gross, not net

The target was already solved so that 2R means 2R after fees, but the +1R
threshold governing the time stop was a naive `entry ± stop_distance`. That
level is reached while the trade has *not* made 1R after costs, so trades that
were still losing net survived the time stop.

`solve_price_for_net(entry, qty, direction, cfg, tick, net_pnl, exit_fee_rate)`
is now the single closed form; `solve_target` and the new `solve_r_level` are
both thin callers of it, so the two levels cannot drift apart. The +1R level
uses the **taker** fee on the exit side, because a trade continuing past the
time stop will exit by stop, target or max-hold and taker is the conservative
choice of those. Rounded away from the position, consistent with all other
rounding. Detection remains an intrabar 1m touch. On the standard fixture trade
the net level sits above the gross level, and
`test_gross_1r_touch_without_net_1r_is_still_time_stopped` pins the boundary: a
touch between the two levels does **not** count as reaching 1R.

**The cost arithmetic, sizing, target solve and slippage placement were not
touched.** Section 6 is the proof.

---

## 4. ACCEPTANCE GATES

### G1 — synthetic fixtures (all 17 originals still pass; 29 new)

Original 17, unchanged and passing:

| fixture | result |
|---|---|
| stop hit first | PASS |
| target hit first | PASS |
| both levels same minute -> stop-first, `assumed` | PASS |
| target touched, not traded through -> no fill | PASS |
| target + 1 tick -> does fill | PASS |
| far beyond stop -> `unresolved` | PASS |
| shallow breach -> `normal` | PASS |
| time stop, +1R never reached | PASS |
| +1R reached -> time stop suppressed | PASS |
| short direction symmetric | PASS |
| 1m open/volume absent from fixture dtype | PASS |
| cooldown blocks re-entry | PASS |
| new 20-bar extreme clears cooldown | PASS |
| cooldown direction-specific | PASS |
| unfundable trade refused | PASS |
| leverage cap binds on 3rd position | PASS |
| one position per symbol | PASS |

New fixtures required by this pass:

| fixture | result |
|---|---|
| +1R reached, continues past bar 16, exits target before max_hold | PASS |
| +1R reached, continues, hits max_hold cap -> `max_hold` | PASS |
| +1R reached, continues, later hits stop | PASS |
| net +1R vs gross +1R boundary -> still time-stopped | PASS |
| `max_hold_bars <= time_stop_bars` raises at config load | PASS |
| walk buffer exhaustion -> `insufficient_data`, never `walk_end` | PASS |
| signal mode allows two overlapping trades on one symbol | PASS |
| portfolio mode refuses the second | PASS |
| single isolated trade byte-identical across both modes | PASS |
| `cooldown_bars=3` blocks for exactly 3 bars | PASS |
| `cooldown_bars=0` blocks nothing | PASS |
| regression: BTCUSDT 1673881200000 -> -1.0001R | PASS |

Supporting tests also added: walk buffer outlasts max_hold at 3 settings; net
+1R actually delivers 1R; net +1R uses taker not maker; short-side net +1R
symmetry; signal mode ignores cooldown; signal mode ignores margin cap; unknown
mode raises; gated arm is a partition of the ungated table; rvol recorded on
every trade; negative `cooldown_bars` rejected; `insufficient_data` in the
exit-reason enum and `walk_end` absent from it.

### G2 — planted look-ahead: PASS
Both planted leaks (Donchian shifted -1, RVOL baseline shifted -1) still
caught by `assert_causal` / `assert_causal_indicators`. Unchanged this pass and
still deselected by default.

### G3 — trace mode: PASS
Extended to show both holding deadlines and both the net and gross +1R levels,
so the B2 change is visible in the trace rather than only in code. 4 tests.

### G4 — determinism: PASS
Two runs byte-identical; hash also invariant under row-order shuffle.

### G5 — golden file: PASS, regenerated deliberately. See section 7.

---

## 5. FULL TRACE — a trade that reaches +1R and continues past bar 16

BTCUSDT **long**, `signal_bar_ts=1674226800000`. This trade touches net +1R,
survives the bar-16 time stop under the new rule (which the old engine would
have force-closed as `walk_end`), and exits on target at bar 19 for +2.0004R.
Untruncated — all 290 walked minutes.

```
TRACE BTCUSDT long signal_bar_ts=1674226800000
  SIGNAL  close            = 21169.5
  SIGNAL  ema_fast         = 21063.39668795
  SIGNAL  ema_slow         = 21026.1511735
  SIGNAL  donchian_upper   = 21166
  SIGNAL  donchian_lower   = 20918.5
  SIGNAL  rvol             = 2.07947109
  SIGNAL  rsi              = 72.26529738
  SIGNAL  atr              = 55.34207734
  ENTRY   1m bar ts=1674227700000 close=21159.5 -> fill 21159.5  (entry_slippage_bps=0.0)
  STOP    atr=55.34207734 x1.5 = 83.01311601  floor 1.000% cap 3.500% of 21159.5 -> stop 20947.9 (1.0000% of entry)
  SIZE    denom = |P-S| 211.6 + P*f_taker 12.6957 + S*f_taker 12.56874 + P*s_entry 0 + S*s_stop 10.47395 = 247.33839
          qty = risk 20.0 / 247.33839 = 0.08086088
  TARGET  solve: (2.0R/q + P*(1+f_taker)) / (1-f_maker) -> 21671.3   notional 1710.9758
  LEVELS  stop 20947.9 | target 21671.3 | tp needs trade-through >= 21671.4
          +1R net 21432.4 (gross would be 21371.1) -- time stop tests the NET level
  WALK    721 1m bars after the entry minute
          time-stop execution 1674242100000 (bar 16+1, only if +1R net NOT reached)
          max-hold execution  1674270900000 (bar 48+1, cap once +1R net IS reached)
    [  1] ts=1674227760000 h=21160 l=21143
    [  2] ts=1674227820000 h=21152 l=21140
    [  3] ts=1674227880000 h=21147.5 l=21138
    [  4] ts=1674227940000 h=21163 l=21145
    [  5] ts=1674228000000 h=21182.5 l=21161.5
    [  6] ts=1674228060000 h=21215 l=21181
    [  7] ts=1674228120000 h=21245 l=21196.5
    [  8] ts=1674228180000 h=21206.5 l=21186.5
    [  9] ts=1674228240000 h=21202 l=21180
    [ 10] ts=1674228300000 h=21195 l=21154
    [ 11] ts=1674228360000 h=21157 l=21126.5
    [ 12] ts=1674228420000 h=21151.5 l=21131
    [ 13] ts=1674228480000 h=21160.5 l=21146.5
    [ 14] ts=1674228540000 h=21173.5 l=21157
    [ 15] ts=1674228600000 h=21172.5 l=21147
    [ 16] ts=1674228660000 h=21149 l=21132
    [ 17] ts=1674228720000 h=21158 l=21139.5
    [ 18] ts=1674228780000 h=21160.5 l=21144
    [ 19] ts=1674228840000 h=21149.5 l=21136
    [ 20] ts=1674228900000 h=21147 l=21135.5
    [ 21] ts=1674228960000 h=21148 l=21132
    [ 22] ts=1674229020000 h=21146 l=21134.5
    [ 23] ts=1674229080000 h=21149 l=21133
    [ 24] ts=1674229140000 h=21139.5 l=21126.5
    [ 25] ts=1674229200000 h=21137.5 l=21132.5
    [ 26] ts=1674229260000 h=21142.5 l=21133
    [ 27] ts=1674229320000 h=21145.5 l=21133.5
    [ 28] ts=1674229380000 h=21152.5 l=21130
    [ 29] ts=1674229440000 h=21133 l=21120.5
    [ 30] ts=1674229500000 h=21131 l=21119.5
    [ 31] ts=1674229560000 h=21135.5 l=21128
    [ 32] ts=1674229620000 h=21129 l=21107.5
    [ 33] ts=1674229680000 h=21127 l=21117
    [ 34] ts=1674229740000 h=21122.5 l=21120.5
    [ 35] ts=1674229800000 h=21128 l=21113.5
    [ 36] ts=1674229860000 h=21120 l=21115
    [ 37] ts=1674229920000 h=21124 l=21116
    [ 38] ts=1674229980000 h=21126 l=21118.5
    [ 39] ts=1674230040000 h=21137 l=21126
    [ 40] ts=1674230100000 h=21144 l=21136.5
    [ 41] ts=1674230160000 h=21147 l=21135
    [ 42] ts=1674230220000 h=21147 l=21135
    [ 43] ts=1674230280000 h=21139.5 l=21135
    [ 44] ts=1674230340000 h=21146 l=21138.5
    [ 45] ts=1674230400000 h=21147 l=21143.5
    [ 46] ts=1674230460000 h=21151 l=21144.5
    [ 47] ts=1674230520000 h=21166 l=21151
    [ 48] ts=1674230580000 h=21166 l=21156
    [ 49] ts=1674230640000 h=21165 l=21156
    [ 50] ts=1674230700000 h=21162.5 l=21161
    [ 51] ts=1674230760000 h=21163 l=21151
    [ 52] ts=1674230820000 h=21160.5 l=21150.5
    [ 53] ts=1674230880000 h=21162 l=21153.5
    [ 54] ts=1674230940000 h=21154 l=21152
    [ 55] ts=1674231000000 h=21155 l=21148.5
    [ 56] ts=1674231060000 h=21155.5 l=21148.5
    [ 57] ts=1674231120000 h=21159.5 l=21153.5
    [ 58] ts=1674231180000 h=21163 l=21154
    [ 59] ts=1674231240000 h=21170 l=21158
    [ 60] ts=1674231300000 h=21182 l=21169.5
    [ 61] ts=1674231360000 h=21198.5 l=21178.5
    [ 62] ts=1674231420000 h=21215 l=21184.5
    [ 63] ts=1674231480000 h=21207 l=21188
    [ 64] ts=1674231540000 h=21197 l=21188
    [ 65] ts=1674231600000 h=21199 l=21189
    [ 66] ts=1674231660000 h=21191 l=21180.5
    [ 67] ts=1674231720000 h=21187 l=21180.5
    [ 68] ts=1674231780000 h=21200 l=21186.5
    [ 69] ts=1674231840000 h=21207.5 l=21187.5
    [ 70] ts=1674231900000 h=21189 l=21180.5
    [ 71] ts=1674231960000 h=21191.5 l=21175
    [ 72] ts=1674232020000 h=21203 l=21190.5
    [ 73] ts=1674232080000 h=21217 l=21201
    [ 74] ts=1674232140000 h=21223 l=21209.5
    [ 75] ts=1674232200000 h=21234 l=21215.5
    [ 76] ts=1674232260000 h=21283 l=21226
    [ 77] ts=1674232320000 h=21264.5 l=21237
    [ 78] ts=1674232380000 h=21259.5 l=21235.5
    [ 79] ts=1674232440000 h=21238 l=21225
    [ 80] ts=1674232500000 h=21295 l=21235
    [ 81] ts=1674232560000 h=21304 l=21261.5
    [ 82] ts=1674232620000 h=21291 l=21262.5
    [ 83] ts=1674232680000 h=21290 l=21264.5
    [ 84] ts=1674232740000 h=21284 l=21262.5
    [ 85] ts=1674232800000 h=21294.5 l=21265.5
    [ 86] ts=1674232860000 h=21279.5 l=21265.5
    [ 87] ts=1674232920000 h=21301 l=21279
    [ 88] ts=1674232980000 h=21300 l=21290.5
    [ 89] ts=1674233040000 h=21324.5 l=21292.5
    [ 90] ts=1674233100000 h=21330 l=21297.5
    [ 91] ts=1674233160000 h=21308 l=21280
    [ 92] ts=1674233220000 h=21360 l=21306.5
    [ 93] ts=1674233280000 h=21373 l=21334
    [ 94] ts=1674233340000 h=21370 l=21342.5
    [ 95] ts=1674233400000 h=21355.5 l=21338
    [ 96] ts=1674233460000 h=21388 l=21339
    [ 97] ts=1674233520000 h=21391.5 l=21367
    [ 98] ts=1674233580000 h=21410.5 l=21374
    [ 99] ts=1674233640000 h=21410 l=21374.5
    [100] ts=1674233700000 h=21386.5 l=21362
    [101] ts=1674233760000 h=21369.5 l=21335.5
    [102] ts=1674233820000 h=21359.5 l=21333
    [103] ts=1674233880000 h=21341 l=21294.5
    [104] ts=1674233940000 h=21319.5 l=21289
    [105] ts=1674234000000 h=21353 l=21316.5
    [106] ts=1674234060000 h=21354.5 l=21339.5
    [107] ts=1674234120000 h=21351.5 l=21339.5
    [108] ts=1674234180000 h=21364 l=21346.5
    [109] ts=1674234240000 h=21377 l=21360.5
    [110] ts=1674234300000 h=21396 l=21355.5
    [111] ts=1674234360000 h=21415.5 l=21384
    [112] ts=1674234420000 h=21398 l=21376
    [113] ts=1674234480000 h=21394.5 l=21369.5
    [114] ts=1674234540000 h=21402.5 l=21371.5
    [115] ts=1674234600000 h=21383.5 l=21362.5
    [116] ts=1674234660000 h=21395.5 l=21380.5
    [117] ts=1674234720000 h=21399.5 l=21384
    [118] ts=1674234780000 h=21396.5 l=21368
    [119] ts=1674234840000 h=21373.5 l=21348.5
    [120] ts=1674234900000 h=21377 l=21358.5
    [121] ts=1674234960000 h=21396.5 l=21376.5
    [122] ts=1674235020000 h=21394 l=21382.5
    [123] ts=1674235080000 h=21393.5 l=21374.5
    [124] ts=1674235140000 h=21384 l=21372
    [125] ts=1674235200000 h=21396 l=21372
    [126] ts=1674235260000 h=21386 l=21375
    [127] ts=1674235320000 h=21382 l=21371.5
    [128] ts=1674235380000 h=21378.5 l=21363
    [129] ts=1674235440000 h=21368.5 l=21350
    [130] ts=1674235500000 h=21359.5 l=21346.5
    [131] ts=1674235560000 h=21353 l=21335
    [132] ts=1674235620000 h=21362.5 l=21335
    [133] ts=1674235680000 h=21361 l=21351
    [134] ts=1674235740000 h=21354 l=21320
    [135] ts=1674235800000 h=21341 l=21323.5
    [136] ts=1674235860000 h=21354.5 l=21335.5
    [137] ts=1674235920000 h=21354 l=21345
    [138] ts=1674235980000 h=21353 l=21340.5
    [139] ts=1674236040000 h=21351 l=21342.5
    [140] ts=1674236100000 h=21349 l=21331.5
    [141] ts=1674236160000 h=21331.5 l=21309
    [142] ts=1674236220000 h=21313 l=21285.5
    [143] ts=1674236280000 h=21314 l=21291.5
    [144] ts=1674236340000 h=21330 l=21311.5
    [145] ts=1674236400000 h=21360.5 l=21329.5
    [146] ts=1674236460000 h=21371 l=21350
    [147] ts=1674236520000 h=21362.5 l=21353.5
    [148] ts=1674236580000 h=21367 l=21356.5
    [149] ts=1674236640000 h=21356.5 l=21343
    [150] ts=1674236700000 h=21348 l=21339.5
    [151] ts=1674236760000 h=21344 l=21327.5
    [152] ts=1674236820000 h=21336 l=21304.5
    [153] ts=1674236880000 h=21324 l=21312.5
    [154] ts=1674236940000 h=21327.5 l=21312
    [155] ts=1674237000000 h=21337.5 l=21320
    [156] ts=1674237060000 h=21364.5 l=21337
    [157] ts=1674237120000 h=21360.5 l=21350.5
    [158] ts=1674237180000 h=21361.5 l=21352
    [159] ts=1674237240000 h=21382.5 l=21359.5
    [160] ts=1674237300000 h=21383 l=21365
    [161] ts=1674237360000 h=21371 l=21354.5
    [162] ts=1674237420000 h=21367.5 l=21357.5
    [163] ts=1674237480000 h=21373.5 l=21356.5
    [164] ts=1674237540000 h=21362.5 l=21354
    [165] ts=1674237600000 h=21377.5 l=21347.5
    [166] ts=1674237660000 h=21391.5 l=21367.5
    [167] ts=1674237720000 h=21407.5 l=21380.5
    [168] ts=1674237780000 h=21406 l=21381
    [169] ts=1674237840000 h=21396 l=21380
    [170] ts=1674237900000 h=21387.5 l=21371.5
    [171] ts=1674237960000 h=21376.5 l=21360.5
    [172] ts=1674238020000 h=21365 l=21353.5
    [173] ts=1674238080000 h=21354.5 l=21336.5
    [174] ts=1674238140000 h=21353 l=21340.5
    [175] ts=1674238200000 h=21352.5 l=21336
    [176] ts=1674238260000 h=21338 l=21319.5
    [177] ts=1674238320000 h=21339.5 l=21326
    [178] ts=1674238380000 h=21363 l=21338.5
    [179] ts=1674238440000 h=21387 l=21361.5
    [180] ts=1674238500000 h=21392.5 l=21384.5
    [181] ts=1674238560000 h=21437 l=21392
    [182] ts=1674238620000 h=21417.5 l=21365
    [183] ts=1674238680000 h=21375 l=21354.5
    [184] ts=1674238740000 h=21354.5 l=21323.5
    [185] ts=1674238800000 h=21347 l=21316.5
    [186] ts=1674238860000 h=21348 l=21323
    [187] ts=1674238920000 h=21323 l=21293.5
    [188] ts=1674238980000 h=21331 l=21313
    [189] ts=1674239040000 h=21322.5 l=21305.5
    [190] ts=1674239100000 h=21317 l=21306
    [191] ts=1674239160000 h=21345 l=21316.5
    [192] ts=1674239220000 h=21339.5 l=21323.5
    [193] ts=1674239280000 h=21327.5 l=21310
    [194] ts=1674239340000 h=21330 l=21322
    [195] ts=1674239400000 h=21328.5 l=21309.5
    [196] ts=1674239460000 h=21340 l=21324
    [197] ts=1674239520000 h=21342.5 l=21332
    [198] ts=1674239580000 h=21346 l=21332
    [199] ts=1674239640000 h=21343 l=21335.5
    [200] ts=1674239700000 h=21359 l=21340.5
    [201] ts=1674239760000 h=21369 l=21354.5
    [202] ts=1674239820000 h=21377 l=21360
    [203] ts=1674239880000 h=21381 l=21362
    [204] ts=1674239940000 h=21376 l=21356
    [205] ts=1674240000000 h=21376.5 l=21364
    [206] ts=1674240060000 h=21375.5 l=21366
    [207] ts=1674240120000 h=21378.5 l=21371
    [208] ts=1674240180000 h=21393.5 l=21373.5
    [209] ts=1674240240000 h=21393 l=21385
    [210] ts=1674240300000 h=21389 l=21375.5
    [211] ts=1674240360000 h=21380 l=21374.5
    [212] ts=1674240420000 h=21388.5 l=21378
    [213] ts=1674240480000 h=21394 l=21377.5
    [214] ts=1674240540000 h=21401.5 l=21392
    [215] ts=1674240600000 h=21395 l=21383.5
    [216] ts=1674240660000 h=21392 l=21365
    [217] ts=1674240720000 h=21379.5 l=21359
    [218] ts=1674240780000 h=21385.5 l=21375.5
    [219] ts=1674240840000 h=21386 l=21375
    [220] ts=1674240900000 h=21382.5 l=21372.5
    [221] ts=1674240960000 h=21376 l=21364.5
    [222] ts=1674241020000 h=21377.5 l=21365
    [223] ts=1674241080000 h=21383.5 l=21376.5
    [224] ts=1674241140000 h=21382 l=21376
    [225] ts=1674241200000 h=21386.5 l=21380
    [226] ts=1674241260000 h=21380.5 l=21366
    [227] ts=1674241320000 h=21367 l=21357
    [228] ts=1674241380000 h=21368 l=21357
    [229] ts=1674241440000 h=21374 l=21367
    [230] ts=1674241500000 h=21382 l=21371.5
    [231] ts=1674241560000 h=21396 l=21381.5
    [232] ts=1674241620000 h=21397 l=21381
    [233] ts=1674241680000 h=21389.5 l=21380.5
    [234] ts=1674241740000 h=21386 l=21381.5
    [235] ts=1674241800000 h=21389 l=21383
    [236] ts=1674241860000 h=21396 l=21388.5
    [237] ts=1674241920000 h=21396 l=21390.5
    [238] ts=1674241980000 h=21393.5 l=21386
    [239] ts=1674242040000 h=21389.5 l=21386
    [240] ts=1674242100000 h=21389 l=21386
    [241] ts=1674242160000 h=21389.5 l=21387.5
    [242] ts=1674242220000 h=21389 l=21381.5
    [243] ts=1674242280000 h=21381.5 l=21360.5
    [244] ts=1674242340000 h=21364 l=21357.5
    [245] ts=1674242400000 h=21371 l=21358
    [246] ts=1674242460000 h=21379.5 l=21370
    [247] ts=1674242520000 h=21388 l=21377
    [248] ts=1674242580000 h=21394 l=21384.5
    [249] ts=1674242640000 h=21423.5 l=21394
    [250] ts=1674242700000 h=21414 l=21395.5
    [251] ts=1674242760000 h=21405 l=21387.5
    [252] ts=1674242820000 h=21388.5 l=21366.5
    [253] ts=1674242880000 h=21383 l=21366
    [254] ts=1674242940000 h=21387 l=21381
    [255] ts=1674243000000 h=21386 l=21382.5
    [256] ts=1674243060000 h=21383.5 l=21371
    [257] ts=1674243120000 h=21381 l=21371
    [258] ts=1674243180000 h=21384 l=21377.5
    [259] ts=1674243240000 h=21377.5 l=21371
    [260] ts=1674243300000 h=21371.5 l=21365
    [261] ts=1674243360000 h=21391.5 l=21366.5
    [262] ts=1674243420000 h=21399.5 l=21390
    [263] ts=1674243480000 h=21399 l=21393
    [264] ts=1674243540000 h=21412.5 l=21396.5
    [265] ts=1674243600000 h=21413 l=21395
    [266] ts=1674243660000 h=21405.5 l=21394.5
    [267] ts=1674243720000 h=21403.5 l=21396
    [268] ts=1674243780000 h=21413 l=21398.5
    [269] ts=1674243840000 h=21500 l=21394.5
    [270] ts=1674243900000 h=21406.5 l=21369
    [271] ts=1674243960000 h=21389.5 l=21375.5
    [272] ts=1674244020000 h=21397 l=21376
    [273] ts=1674244080000 h=21436.5 l=21397
    [274] ts=1674244140000 h=21417 l=21394.5
    [275] ts=1674244200000 h=21427.5 l=21409.5
    [276] ts=1674244260000 h=21440 l=21425
    [277] ts=1674244320000 h=21443.5 l=21415.5
    [278] ts=1674244380000 h=21486.5 l=21440
    [279] ts=1674244440000 h=21495 l=21466
    [280] ts=1674244500000 h=21478 l=21455
    [281] ts=1674244560000 h=21482 l=21450
    [282] ts=1674244620000 h=21495 l=21474.5
    [283] ts=1674244680000 h=21498 l=21478
    [284] ts=1674244740000 h=21528 l=21475.5
    [285] ts=1674244800000 h=21546 l=21498
    [286] ts=1674244860000 h=21596.5 l=21513
    [287] ts=1674244920000 h=21615 l=21560
    [288] ts=1674244980000 h=21640 l=21578.5
    [289] ts=1674245040000 h=21649 l=21586
    [290] ts=1674245100000 h=22043.5 l=21633  TARGET (observed) traded through 21671.4, fill 21671.3 maker
  PNL     gross = q 0.08086088 x (21671.3 - 21159.5) = 41.384599
          fees  = q*P*0.0006 1.026585 + q*X*0.0002 0.350472 = 1.377058
          net   = 41.384599 - 1.377058 = 40.007541   R = 2.0004
```

Hand-check: 1.5xATR = 83.01 is 0.392% of entry, below the 1.0% floor, so the
stop is floored to 21159.5 x 0.99 = 20947.905, rounded away to 20947.9. The
trade reaches net +1R early, so the bar-16 time stop does not apply; it then
runs to the target at minute 290 (bar 19 after entry), well inside the 48-bar
max-hold cap. Net +40.0075 on a $20 R = +2.0004R, delivered with a maker exit.

---

## 6. REGRESSION TRACE — the pinned trade is undisturbed

BTCUSDT **short**, `signal_bar_ts=1673881200000`, the trade verified by hand in
the previous pass. Reproduced from the current tree:

```
TRACE BTCUSDT short signal_bar_ts=1673881200000
  SIGNAL  close            = 20673
  SIGNAL  ema_fast         = 20842.41225689
  SIGNAL  ema_slow         = 20901.4163895
  SIGNAL  donchian_upper   = 20916
  SIGNAL  donchian_lower   = 20766
  SIGNAL  rvol             = 5.65998418
  SIGNAL  rsi              = 31.99087948
  SIGNAL  atr              = 76.71784866
  ENTRY   1m bar ts=1673882100000 close=20741.5 -> fill 20741.5  (entry_slippage_bps=0.0)
  STOP    atr=76.71784866 x1.5 = 115.076773  floor 1.000% cap 3.500% of 20741.5 -> stop 20949 (1.0004% of entry)
  SIZE    denom = |P-S| 207.5 + P*f_taker 12.4449 + S*f_taker 12.5694 + P*s_entry 0 + S*s_stop 10.4745 = 242.9888
          qty = risk 20.0 / 242.9888 = 0.08230832
  TARGET  solve: (2.0R/q + P*(1+f_taker)) / (1-f_maker) -> 20239   notional 1707.198
  LEVELS  stop 20949 | target 20239 | tp needs trade-through >= 20238.9
          +1R net 20473.7 (gross would be 20534) -- time stop tests the NET level
  WALK    721 1m bars after the entry minute
          time-stop execution 1673896500000 (bar 16+1, only if +1R net NOT reached)
          max-hold execution  1673925300000 (bar 48+1, cap once +1R net IS reached)
    [  1] ts=1673882160000 h=20757.5 l=20727.5
    [  2] ts=1673882220000 h=20806 l=20755.5
    [  3] ts=1673882280000 h=20812.5 l=20775
    [  4] ts=1673882340000 h=20800 l=20776.5
    [  5] ts=1673882400000 h=20811 l=20794
    [  6] ts=1673882460000 h=20808 l=20790.5
    [  7] ts=1673882520000 h=20796.5 l=20770.5
    [  8] ts=1673882580000 h=20880 l=20795.5
    [  9] ts=1673882640000 h=20970 l=20863  STOP (observed) fill 20959.5 quality=normal
  PNL     gross = q 0.08230832 x (20959.5 - 20741.5) = -17.943214
          fees  = q*P*0.0006 1.024319 + q*X*0.0006 1.035085 = 2.059404
          net   = -17.943214 - 2.059404 = -20.002617   R = -1.0001
```

**Still -1.0001R**, byte-identical to the previous pass. Entry 20741.5, stop
20949.0, qty 0.08230832, exit 20959.5, net -20.002617. Pinned by
`tests/test_regression_pinned_trade.py` (5 tests): entry and levels, sizing,
exit, the -1.0001R headline to four decimals, and a from-scratch recomputation
of gross/fees/net from the row's own fields rather than trusting the stored
total. This trade never reaches +1R, so B2 does not touch it; it stops at bar 0,
so B1 does not touch it. That is why it is a good pin.

---

## 7. GOLDEN FILE

| | |
|---|---|
| **Old hash** | `b7b5272da8d43922f697dba35cbb88f14f25386e9c8d1ed926ed47b53ccf735b` |
| **New hash** | `d91622dee0b64ca6118858c0899a37466b59f2d8eab7f0017cad08ac8b2a6049` |
| **Rows** | 44 -> 42 |

Slice unchanged: BTCUSDT, 2023-01-01..2023-02-01, default parameters.

**What accounts for the delta.** Every one of the 10 old `walk_end` trades was
an artefact of B1 and has been reclassified:

| old | new | count |
|---|---|---|
| `walk_end` @16 bars | `time_stop` @16 | 4 |
| `walk_end` @16 bars | `max_hold` @48 | 3 |
| `walk_end` @16 bars | `target` @19 | 1 |
| `walk_end` @16 bars | `stop` @28 | 1 |
| `walk_end` @16 bars | (no longer a trade) | 1 |

Exit-reason totals moved `time_stop` 20->23, `stop` 11->12, `target` 3->4,
`max_hold` 0->3, `walk_end` 10->0.

The 4 reclassified to `time_stop` are the **B2** effect: they had touched gross
+1R but not net +1R, so under the corrected definition they never reached 1R and
the time stop correctly applies. The other 6 are the **B1** effect: they had
genuinely reached +1R and are now allowed to run, three of them all the way to
the 48-bar cap.

**Row count fell 44 -> 42** because trades now last longer (mean bars_held
13.39 -> 15.90, max 16 -> 48), so portfolio occupancy rose and two signals
(`1674640800000`, `1674984600000`) were refused for `open_position` that
previously became trades. This is the occupancy cost of `max_hold_bars=48`
predicted in the spec rationale, showing up immediately and measurably.

---

## 8. COUNTERS — per year, per symbol, both modes

Full machine output follows. Headline points first.

**`decided_by_assumption` is 0 in 2022 as well as 2023** — 0 of 2064 portfolio
trades and 0 of 4646 signal-mode trades in the LUNA/FTX year. The previous
"near-inert" conclusion survives the volatility test. For both levels to fall in
one minute, a single 1m bar must span from the stop (>=1% of entry) to the
target (~2R beyond entry); that does not happen even in 2022.

**`tp_touched_not_filled` is 0 in 2022** (and 1 in 2023, portfolio). Also
survives the volatility test.

**`stop_fill_unresolved` did NOT bind harder in 2022** in the way the spec
anticipated: 29 occurrences in 2022 portfolio vs 24 in 2023 — 1.41% vs 1.27% of
trades. Higher, but marginally. In signal mode: 57 of 4646 (1.23%) in 2022.
This is worth flagging as a partial refutation of the expectation, not a
confirmation.

**`refused_cooldown` is now non-zero** — 6 in 2022 (was 0 everywhere last pass).
Not because the extreme rule started binding, but because longer holds changed
which signals arrive while a symbol is blocked.

```
COUNTERS AND DIAGNOSTICS — report only, no performance figures
config: time_stop_bars=16 max_hold_bars=48 cooldown_bars=0 max_leverage=3.0 stop_unresolved_frac=0.5

==========================================================================
YEAR 2022
==========================================================================

PORTFOLIO MODE (gated) — all symbols
  counters
    trades                         2064
    resolved_by_observation        2064
    decided_by_assumption          0
    tp_touched_not_filled          0
    stop_fill_unresolved           29
    flagged_bar_overlap            8
    refused_open_position          991
    refused_cooldown               6
    refused_insufficient_margin    0
    refused_no_1m_coverage         0
  diagnostics  (n=2064)
    exit-reason distribution:
      target                  428   20.74%
      stop                   1002   48.55%
      time_stop               547   26.50%
      max_hold                 87    4.22%
      insufficient_data         0    0.00%
    stop-band binding:
      1.0% floor             1338   64.83%
      3.5% cap                 17    0.82%
      1.5xATR (neither)       709   34.35%
    holding time (bars_held) by exit reason:
      ALL                  n= 2064  min=  0 med=  11.0 mean= 12.67 p90=  24.0 max= 48
      target               n=  428  min=  0 med=  10.0 mean= 12.59 p90=  29.0 max= 46
      stop                 n= 1002  min=  0 med=   5.0 mean=  7.83 p90=  16.0 max= 46
      time_stop            n=  547  min= 16 med=  16.0 mean= 16.00 p90=  16.0 max= 16
      max_hold             n=   87  min= 48 med=  48.0 mean= 48.00 p90=  48.0 max= 48
      insufficient_data    -

PORTFOLIO MODE (gated) — per symbol
  BTCUSDT  (n=671)
    exit-reason distribution:
      target                   96   14.31%
      stop                    254   37.85%
      time_stop               288   42.92%
      max_hold                 33    4.92%
      insufficient_data         0    0.00%
    stop-band binding:
      1.0% floor              587   87.48%
      3.5% cap                  0    0.00%
      1.5xATR (neither)        84   12.52%
    holding time (bars_held) by exit reason:
      ALL                  n=  671  min=  0 med=  16.0 mean= 14.60 p90=  25.0 max= 48
      target               n=   96  min=  0 med=  11.0 mean= 15.34 p90=  34.0 max= 46
      stop                 n=  254  min=  0 med=   6.0 mean=  8.38 p90=  16.0 max= 41
      time_stop            n=  288  min= 16 med=  16.0 mean= 16.00 p90=  16.0 max= 16
      max_hold             n=   33  min= 48 med=  48.0 mean= 48.00 p90=  48.0 max= 48
      insufficient_data    -
      assumed=0 tp_touch_no_fill=0 stop_unresolved=12 flagged=3
  ETHUSDT  (n=675)
    exit-reason distribution:
      target                  146   21.63%
      stop                    316   46.81%
      time_stop               178   26.37%
      max_hold                 35    5.19%
      insufficient_data         0    0.00%
    stop-band binding:
      1.0% floor              463   68.59%
      3.5% cap                  2    0.30%
      1.5xATR (neither)       210   31.11%
    holding time (bars_held) by exit reason:
      ALL                  n=  675  min=  0 med=  11.0 mean= 12.77 p90=  23.0 max= 48
      target               n=  146  min=  0 med=   9.0 mean= 11.09 p90=  24.5 max= 43
      stop                 n=  316  min=  0 med=   5.0 mean=  7.83 p90=  15.0 max= 46
      time_stop            n=  178  min= 16 med=  16.0 mean= 16.00 p90=  16.0 max= 16
      max_hold             n=   35  min= 48 med=  48.0 mean= 48.00 p90=  48.0 max= 48
      insufficient_data    -
      assumed=0 tp_touch_no_fill=0 stop_unresolved=11 flagged=5
  SOLUSDT  (n=718)
    exit-reason distribution:
      target                  186   25.91%
      stop                    432   60.17%
      time_stop                81   11.28%
      max_hold                 19    2.65%
      insufficient_data         0    0.00%
    stop-band binding:
      1.0% floor              288   40.11%
      3.5% cap                 15    2.09%
      1.5xATR (neither)       415   57.80%
    holding time (bars_held) by exit reason:
      ALL                  n=  718  min=  0 med=   7.0 mean= 10.79 p90=  24.0 max= 48
      target               n=  186  min=  0 med=  10.0 mean= 12.35 p90=  27.0 max= 45
      stop                 n=  432  min=  0 med=   4.0 mean=  7.50 p90=  18.9 max= 44
      time_stop            n=   81  min= 16 med=  16.0 mean= 16.00 p90=  16.0 max= 16
      max_hold             n=   19  min= 48 med=  48.0 mean= 48.00 p90=  48.0 max= 48
      insufficient_data    -
      assumed=0 tp_touch_no_fill=0 stop_unresolved=6 flagged=0

SIGNAL MODE — one ungated simulation; gated arm is a FILTER of the same table
  counters (ungated universe)
    trades                         4646
    resolved_by_observation        4646
    decided_by_assumption          0
    tp_touched_not_filled          0
    stop_fill_unresolved           57
    flagged_bar_overlap            16
    refused_open_position          0
    refused_cooldown               0
    refused_insufficient_margin    0
    refused_no_1m_coverage         0
  diagnostics (ungated universe)  (n=4646)
    exit-reason distribution:
      target                  988   21.27%
      stop                   2310   49.72%
      time_stop              1131   24.34%
      max_hold                217    4.67%
      insufficient_data         0    0.00%
    stop-band binding:
      1.0% floor             2856   61.47%
      3.5% cap                 46    0.99%
      1.5xATR (neither)      1744   37.54%
    holding time (bars_held) by exit reason:
      ALL                  n= 4646  min=  0 med=  11.0 mean= 12.92 p90=  26.0 max= 48
      target               n=  988  min=  0 med=  10.0 mean= 12.89 p90=  30.0 max= 47
      stop                 n= 2310  min=  0 med=   6.0 mean=  8.14 p90=  17.0 max= 47
      time_stop            n= 1131  min= 16 med=  16.0 mean= 16.00 p90=  16.0 max= 16
      max_hold             n=  217  min= 48 med=  48.0 mean= 48.00 p90=  48.0 max= 48
      insufficient_data    -

  gated arm (rvol >= 1.5): 3061 of 4646 rows (65.9%)
  diagnostics (gated arm)  (n=3061)
    exit-reason distribution:
      target                  649   21.20%
      stop                   1473   48.12%
      time_stop               788   25.74%
      max_hold                151    4.93%
      insufficient_data         0    0.00%
    stop-band binding:
      1.0% floor             1982   64.75%
      3.5% cap                 24    0.78%
      1.5xATR (neither)      1055   34.47%
    holding time (bars_held) by exit reason:
      ALL                  n= 3061  min=  0 med=  12.0 mean= 12.97 p90=  26.0 max= 48
      target               n=  649  min=  0 med=  10.0 mean= 12.77 p90=  30.0 max= 46
      stop                 n= 1473  min=  0 med=   5.0 mean=  7.84 p90=  16.0 max= 47
      time_stop            n=  788  min= 16 med=  16.0 mean= 16.00 p90=  16.0 max= 16
      max_hold             n=  151  min= 48 med=  48.0 mean= 48.00 p90=  48.0 max= 48
      insufficient_data    -

SIGNAL MODE — per symbol (ungated universe)
  BTCUSDT  (n=1319)
    exit-reason distribution:
      target                  202   15.31%
      stop                    528   40.03%
      time_stop               516   39.12%
      max_hold                 73    5.53%
      insufficient_data         0    0.00%
    stop-band binding:
      1.0% floor             1128   85.52%
      3.5% cap                  0    0.00%
      1.5xATR (neither)       191   14.48%
    holding time (bars_held) by exit reason:
      ALL                  n= 1319  min=  0 med=  16.0 mean= 14.53 p90=  27.0 max= 48
      target               n=  202  min=  0 med=  11.0 mean= 14.91 p90=  35.9 max= 47
      stop                 n=  528  min=  0 med=   7.0 mean=  8.31 p90=  15.0 max= 44
      time_stop            n=  516  min= 16 med=  16.0 mean= 16.00 p90=  16.0 max= 16
      max_hold             n=   73  min= 48 med=  48.0 mean= 48.00 p90=  48.0 max= 48
      insufficient_data    -
      assumed=0 tp_touch_no_fill=0 stop_unresolved=17 flagged=8
  ETHUSDT  (n=1451)
    exit-reason distribution:
      target                  313   21.57%
      stop                    696   47.97%
      time_stop               356   24.53%
      max_hold                 86    5.93%
      insufficient_data         0    0.00%
    stop-band binding:
      1.0% floor              959   66.09%
      3.5% cap                  6    0.41%
      1.5xATR (neither)       486   33.49%
    holding time (bars_held) by exit reason:
      ALL                  n= 1451  min=  0 med=  11.0 mean= 13.37 p90=  30.0 max= 48
      target               n=  313  min=  0 med=  10.0 mean= 11.85 p90=  26.8 max= 43
      stop                 n=  696  min=  0 med=   6.0 mean=  8.43 p90=  17.0 max= 47
      time_stop            n=  356  min= 16 med=  16.0 mean= 16.00 p90=  16.0 max= 16
      max_hold             n=   86  min= 48 med=  48.0 mean= 48.00 p90=  48.0 max= 48
      insufficient_data    -
      assumed=0 tp_touch_no_fill=0 stop_unresolved=21 flagged=8
  SOLUSDT  (n=1876)
    exit-reason distribution:
      target                  473   25.21%
      stop                   1086   57.89%
      time_stop               259   13.81%
      max_hold                 58    3.09%
      insufficient_data         0    0.00%
    stop-band binding:
      1.0% floor              769   40.99%
      3.5% cap                 40    2.13%
      1.5xATR (neither)      1067   56.88%
    holding time (bars_held) by exit reason:
      ALL                  n= 1876  min=  0 med=   8.0 mean= 11.45 p90=  25.0 max= 48
      target               n=  473  min=  0 med=  10.0 mean= 12.71 p90=  28.8 max= 47
      stop                 n= 1086  min=  0 med=   5.0 mean=  7.87 p90=  18.0 max= 47
      time_stop            n=  259  min= 16 med=  16.0 mean= 16.00 p90=  16.0 max= 16
      max_hold             n=   58  min= 48 med=  48.0 mean= 48.00 p90=  48.0 max= 48
      insufficient_data    -
      assumed=0 tp_touch_no_fill=0 stop_unresolved=19 flagged=0

==========================================================================
YEAR 2023
==========================================================================

PORTFOLIO MODE (gated) — all symbols
  counters
    trades                         1897
    resolved_by_observation        1897
    decided_by_assumption          0
    tp_touched_not_filled          1
    stop_fill_unresolved           24
    flagged_bar_overlap            1
    refused_open_position          872
    refused_cooldown               0
    refused_insufficient_margin    0
    refused_no_1m_coverage         0
  diagnostics  (n=1897)
    exit-reason distribution:
      target                  273   14.39%
      stop                    670   35.32%
      time_stop               846   44.60%
      max_hold                108    5.69%
      insufficient_data         0    0.00%
    stop-band binding:
      1.0% floor             1538   81.08%
      3.5% cap                  0    0.00%
      1.5xATR (neither)       359   18.92%
    holding time (bars_held) by exit reason:
      ALL                  n= 1897  min=  0 med=  16.0 mean= 14.76 p90=  24.4 max= 48
      target               n=  273  min=  0 med=   9.0 mean= 12.45 p90=  29.0 max= 47
      stop                 n=  670  min=  0 med=   6.5 mean=  8.79 p90=  18.0 max= 47
      time_stop            n=  846  min= 16 med=  16.0 mean= 16.00 p90=  16.0 max= 16
      max_hold             n=  108  min= 48 med=  48.0 mean= 48.00 p90=  48.0 max= 48
      insufficient_data    -

PORTFOLIO MODE (gated) — per symbol
  BTCUSDT  (n=567)
    exit-reason distribution:
      target                   59   10.41%
      stop                    103   18.17%
      time_stop               358   63.14%
      max_hold                 47    8.29%
      insufficient_data         0    0.00%
    stop-band binding:
      1.0% floor              563   99.29%
      3.5% cap                  0    0.00%
      1.5xATR (neither)         4    0.71%
    holding time (bars_held) by exit reason:
      ALL                  n=  567  min=  0 med=  16.0 mean= 17.13 p90=  25.4 max= 48
      target               n=   59  min=  0 med=   8.0 mean= 12.03 p90=  23.0 max= 47
      stop                 n=  103  min=  0 med=   9.0 mean=  9.86 p90=  15.0 max= 47
      time_stop            n=  358  min= 16 med=  16.0 mean= 16.00 p90=  16.0 max= 16
      max_hold             n=   47  min= 48 med=  48.0 mean= 48.00 p90=  48.0 max= 48
      insufficient_data    -
      assumed=0 tp_touch_no_fill=0 stop_unresolved=5 flagged=0
  ETHUSDT  (n=540)
    exit-reason distribution:
      target                   60   11.11%
      stop                    147   27.22%
      time_stop               295   54.63%
      max_hold                 38    7.04%
      insufficient_data         0    0.00%
    stop-band binding:
      1.0% floor              527   97.59%
      3.5% cap                  0    0.00%
      1.5xATR (neither)        13    2.41%
    holding time (bars_held) by exit reason:
      ALL                  n=  540  min=  0 med=  16.0 mean= 16.20 p90=  29.1 max= 48
      target               n=   60  min=  0 med=   9.5 mean= 14.57 p90=  40.2 max= 45
      stop                 n=  147  min=  0 med=   7.0 mean=  9.05 p90=  16.2 max= 37
      time_stop            n=  295  min= 16 med=  16.0 mean= 16.00 p90=  16.0 max= 16
      max_hold             n=   38  min= 48 med=  48.0 mean= 48.00 p90=  48.0 max= 48
      insufficient_data    -
      assumed=0 tp_touch_no_fill=1 stop_unresolved=7 flagged=0
  SOLUSDT  (n=790)
    exit-reason distribution:
      target                  154   19.49%
      stop                    420   53.16%
      time_stop               193   24.43%
      max_hold                 23    2.91%
      insufficient_data         0    0.00%
    stop-band binding:
      1.0% floor              448   56.71%
      3.5% cap                  0    0.00%
      1.5xATR (neither)       342   43.29%
    holding time (bars_held) by exit reason:
      ALL                  n=  790  min=  0 med=  10.5 mean= 12.09 p90=  23.0 max= 48
      target               n=  154  min=  0 med=   9.0 mean= 11.78 p90=  28.7 max= 45
      stop                 n=  420  min=  0 med=   5.5 mean=  8.43 p90=  19.0 max= 47
      time_stop            n=  193  min= 16 med=  16.0 mean= 16.00 p90=  16.0 max= 16
      max_hold             n=   23  min= 48 med=  48.0 mean= 48.00 p90=  48.0 max= 48
      insufficient_data    -
      assumed=0 tp_touch_no_fill=0 stop_unresolved=12 flagged=1

SIGNAL MODE — one ungated simulation; gated arm is a FILTER of the same table
  counters (ungated universe)
    trades                         4025
    resolved_by_observation        4025
    decided_by_assumption          0
    tp_touched_not_filled          4
    stop_fill_unresolved           43
    flagged_bar_overlap            3
    refused_open_position          0
    refused_cooldown               0
    refused_insufficient_margin    0
    refused_no_1m_coverage         0
  diagnostics (ungated universe)  (n=4025)
    exit-reason distribution:
      target                  569   14.14%
      stop                   1308   32.50%
      time_stop              1921   47.73%
      max_hold                227    5.64%
      insufficient_data         0    0.00%
    stop-band binding:
      1.0% floor             3349   83.20%
      3.5% cap                  0    0.00%
      1.5xATR (neither)       676   16.80%
    holding time (bars_held) by exit reason:
      ALL                  n= 4025  min=  0 med=  16.0 mean= 15.21 p90=  25.0 max= 48
      target               n=  569  min=  0 med=  10.0 mean= 13.55 p90=  32.0 max= 47
      stop                 n= 1308  min=  0 med=   7.0 mean=  9.10 p90=  18.0 max= 47
      time_stop            n= 1921  min= 16 med=  16.0 mean= 16.00 p90=  16.0 max= 16
      max_hold             n=  227  min= 48 med=  48.0 mean= 48.00 p90=  48.0 max= 48
      insufficient_data    -

  gated arm (rvol >= 1.5): 2769 of 4025 rows (68.8%)
  diagnostics (gated arm)  (n=2769)
    exit-reason distribution:
      target                  412   14.88%
      stop                    991   35.79%
      time_stop              1199   43.30%
      max_hold                167    6.03%
      insufficient_data         0    0.00%
    stop-band binding:
      1.0% floor             2257   81.51%
      3.5% cap                  0    0.00%
      1.5xATR (neither)       512   18.49%
    holding time (bars_held) by exit reason:
      ALL                  n= 2769  min=  0 med=  16.0 mean= 14.80 p90=  25.0 max= 48
      target               n=  412  min=  0 med=   9.0 mean= 12.75 p90=  30.0 max= 47
      stop                 n=  991  min=  0 med=   6.0 mean=  8.59 p90=  17.0 max= 47
      time_stop            n= 1199  min= 16 med=  16.0 mean= 16.00 p90=  16.0 max= 16
      max_hold             n=  167  min= 48 med=  48.0 mean= 48.00 p90=  48.0 max= 48
      insufficient_data    -

SIGNAL MODE — per symbol (ungated universe)
  BTCUSDT  (n=1233)
    exit-reason distribution:
      target                  120    9.73%
      stop                    224   18.17%
      time_stop               799   64.80%
      max_hold                 90    7.30%
      insufficient_data         0    0.00%
    stop-band binding:
      1.0% floor             1227   99.51%
      3.5% cap                  0    0.00%
      1.5xATR (neither)         6    0.49%
    holding time (bars_held) by exit reason:
      ALL                  n= 1233  min=  0 med=  16.0 mean= 17.01 p90=  22.8 max= 48
      target               n=  120  min=  0 med=  11.0 mean= 13.36 p90=  23.2 max= 47
      stop                 n=  224  min=  0 med=   8.0 mean= 10.14 p90=  18.0 max= 47
      time_stop            n=  799  min= 16 med=  16.0 mean= 16.00 p90=  16.0 max= 16
      max_hold             n=   90  min= 48 med=  48.0 mean= 48.00 p90=  48.0 max= 48
      insufficient_data    -
      assumed=0 tp_touch_no_fill=0 stop_unresolved=6 flagged=2
  ETHUSDT  (n=1209)
    exit-reason distribution:
      target                  127   10.50%
      stop                    294   24.32%
      time_stop               706   58.40%
      max_hold                 82    6.78%
      insufficient_data         0    0.00%
    stop-band binding:
      1.0% floor             1187   98.18%
      3.5% cap                  0    0.00%
      1.5xATR (neither)        22    1.82%
    holding time (bars_held) by exit reason:
      ALL                  n= 1209  min=  0 med=  16.0 mean= 16.58 p90=  26.2 max= 48
      target               n=  127  min=  0 med=  11.0 mean= 14.77 p90=  34.0 max= 47
      stop                 n=  294  min=  0 med=   8.0 mean= 10.00 p90=  18.7 max= 46
      time_stop            n=  706  min= 16 med=  16.0 mean= 16.00 p90=  16.0 max= 16
      max_hold             n=   82  min= 48 med=  48.0 mean= 48.00 p90=  48.0 max= 48
      insufficient_data    -
      assumed=0 tp_touch_no_fill=1 stop_unresolved=15 flagged=0
  SOLUSDT  (n=1583)
    exit-reason distribution:
      target                  322   20.34%
      stop                    790   49.91%
      time_stop               416   26.28%
      max_hold                 55    3.47%
      insufficient_data         0    0.00%
    stop-band binding:
      1.0% floor              935   59.07%
      3.5% cap                  0    0.00%
      1.5xATR (neither)       648   40.93%
    holding time (bars_held) by exit reason:
      ALL                  n= 1583  min=  0 med=  12.0 mean= 12.77 p90=  25.0 max= 48
      target               n=  322  min=  0 med=  10.0 mean= 13.13 p90=  32.0 max= 45
      stop                 n=  790  min=  0 med=   6.0 mean=  8.46 p90=  18.0 max= 47
      time_stop            n=  416  min= 16 med=  16.0 mean= 16.00 p90=  16.0 max= 16
      max_hold             n=   55  min= 48 med=  48.0 mean= 48.00 p90=  48.0 max= 48
      insufficient_data    -
      assumed=0 tp_touch_no_fill=3 stop_unresolved=22 flagged=1
```

---

## 9. DIAGNOSTICS — the finding that matters

**The stop is not volatility-adaptive. It is a fixed 1% stop most of the time.**

The single trade inspected last pass was not an outlier. The 1.0% floor binds:

| | 2022 | 2023 |
|---|---|---|
| all symbols, portfolio | **64.83%** | **81.08%** |
| BTCUSDT | **87.48%** | **99.29%** |
| all symbols, signal mode (ungated) | 61.47% | see block above |

The 3.5% cap binds almost never (0.82% in 2022, 0.00% in 2023). So for BTC in
2023, 1.5xATR(14) on 15m bars was below 1% of price on 563 of 567 trades — the
"volatility-adaptive" stop was a fixed 1% stop in all but four cases, and the
ATR multiplier had no effect on those trades at all.

This changes what the strategy is. Sweeping `stop_atr_mult` will do nothing for
BTC until the floor is lowered or made volatility-relative, because the
parameter is not reaching the output. I have not changed the floor — it is a
locked spec value — but the sweep design in Point 4 should treat
`stop_min_pct` as a first-class parameter rather than a guard rail, or the ATR
multiplier sweep will read as a flat line and be misinterpreted as "ATR does not
matter".

**Exit-reason distribution** shifted materially between the two years:
`time_stop` 26.5% (2022) -> 44.6% (2023), `target` 20.7% -> 14.4%, `stop`
48.6% -> 35.3%. Consistent with 2023 being the chop-dominated year: fewer
resolutions either way, more trades timing out.

**Holding time** is bimodal by construction — `time_stop` is always exactly 16
and `max_hold` always exactly 48, so the medians of those buckets carry no
information. The informative ones are `target` (median 10 bars in 2022, 9 in
2023) and `stop` (median 5 and 6.5), both well inside the time stop.

---

## 10. AMBIGUITIES, DEVIATIONS AND DISAGREEMENTS

1. **`max_walk_minutes = max_hold_bars * 15 + 2`.** The +2 covers the entry
   minute plus the execution minute of bar `max_hold_bars + 1`. The spec said
   "enough buffer to observe the execution minute" without a number.

2. **`insufficient_data` trades still produce a P&L row** (exit at the last
   available 1m close) rather than being dropped. They are counted separately
   and are 0 everywhere in 2022-2023, but if a future slice reaches the end of
   the dataset they will appear. Dropping them instead would silently shrink the
   universe, which seemed worse than a flagged row. Flagging for a decision.

3. **`cooldown_bars` composes with the extreme rule as AND, not OR** — both must
   clear. With the default of 0 this is exactly the old behaviour. The spec said
   "retain the existing rule" and "add cooldown_bars" without specifying how they
   combine; AND is the conservative reading.

4. **Signal mode still records `refused_no_1m_coverage`.** It is the one refusal
   that is a data condition rather than a portfolio constraint, so suppressing it
   in signal mode would hide missing data. It is 0 throughout.

5. **Disagreement — `stop_fill_unresolved` did not behave as the spec expected.**
   The instruction anticipated it binding "considerably harder than 22
   occurrences" in 2022. It bound 29 times (1.41%), versus 24 (1.27%) in 2023.
   That is not a meaningful increase. I did not tune `stop_unresolved_frac` to
   manufacture one. If the expectation was that violent 2022 minutes routinely
   blow through stops, the data does not support it at a 0.5 threshold — and the
   threshold is now config, so it can be swept to find where it starts to bite.

6. **Disagreement — the 1% stop floor is doing more work than the ATR term.**
   See section 9. I implemented the spec as written and am flagging rather than
   redesigning, per the standing instruction. But this is the largest single
   finding of the pass and I think it outranks the gate question for Point 4.

7. **On performance figures:** still none computed or inspected. My position has
   changed slightly — with signal mode in place, the gated-vs-ungated comparison
   is now *methodologically* sound, so the reviewer could reasonably ask for it.
   I would still hold, because the stop-floor finding (6) means the trade
   population is likely to change before it is worth measuring. Reviewer's call.

---

## 11. WHAT IS NOT DONE

- No full backtest; no performance figures of any kind. Real data touched only
  for G4/G5, counters and diagnostics.
- Counters were run over 2022 and 2023 as instructed. 2024, 2025 and 2026 were
  not run.
- The golden file still covers one symbol, one month, portfolio mode only. It
  does not cover signal mode, SOL's pre-2024 tick segment, or `max_hold` on a
  second symbol. Widening is cheap if wanted.
- `max_leverage=3.0` remains an unmeasured placeholder; Bitget's tiered margin
  was not probed. It has never bound on real data, so it is untested outside
  fixtures.
- `cooldown_bars` defaults to 0, so the new bar-count path is exercised only by
  fixtures, never on real data in this report.
- Funding remains entirely absent, per spec.
- Layer B is still an unoptimised Python loop. The 2022 signal-mode run over
  4646 trades is the slowest thing here; a full-history two-mode sweep will need
  attention.
- `insufficient_data` has never been observed on real data, so that path is
  fixture-tested only.
