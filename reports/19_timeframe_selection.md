# REPORT 19 — TIMEFRAME SELECTION

**Point 1, continued.** The cost work is complete (reports 17 and 18). This step
applies a pre-registered rule to ATR% distributions and selects the timeframe
the new hypothesis will be built on.

**THE RULE WAS FROZEN BEFORE THE NUMBERS EXISTED.**
`docs/handoff/19_timeframe_rule.md`, committed **alone** at **`96c96cf`** —
one file, 88 insertions, nothing else in the commit — before any measurement
code was written and before any bar was read. `src/timeframe/atr_profile.py`
transcribes its constants and a test pins each one. The rule is not modified
here, and it may not be modified in light of what it selected.

**Window read: 2022-01-01 to 2024-12-31 only.** **THE HOLDOUT IS SEALED** —
2025-01-01 through 2026-07-26 has never been read, not one bar. Resampling is a
new code path onto sealed data; section 6 reports the planted mutation that
proves the seal holds through it.

**The performance firewall is re-armed.** No expectancy, win rate, profit
factor, Sharpe, equity curve, `r_multiple` or `net_pnl` aggregate is computed,
referenced or estimated anywhere in this step. ATR percentiles are an explicitly
permitted pre-firewall quantity. No trade is simulated, no signal is generated,
and no entry rule exists yet.

**No open price is used anywhere.** `open_synth` is dropped at every load
boundary; ATR needs only high, low and close.

---

## 1. WHAT WAS ASKED

Point 4 used 1.5 × ATR(14) floored at 1%, and the floor bound **65–81% of
breakout bars**. That implies 15m ATR% sits mostly below ~0.67%, so a stop
placed at the report 18 cost floor would never be reached by the ATR term — the
multiplier would be decorative and the rule would be a fixed-percentage stop
wearing an ATR costume.

This step tests that directly. The inherited cost constraints are:

| constraint | floor **(% of entry)** | source |
|---|---:|---|
| fees alone, all-taker | 1.0909 | report 17 §3.2 |
| **slippage headroom, all-taker** | **1.50** | **report 18 §4 — the rule's floor** |
| half-maker | 1.00 | report 18 §4 |

The timeframe is **not inherited**. 15m came from the original Point 1, and
section 8.3 of the Point 4 closing record states that no Point 4 choice carries
forward by default.

---

## 2. RESAMPLING

**Sources — existing data only.** No download, no API call, no Point 2 work.

| timeframe | source layer | constituents per bucket |
|---|---|---:|
| 5m | 1m layer | 5 |
| 15m | 15m layer, used directly | 1 (passthrough) |
| 1h | 15m layer | 4 |
| 4h | 15m layer | 16 |
| 1d | 15m layer | 96 |

**Aggregation:** `high` = max of constituent highs, `low` = min of constituent
lows, `close` = last constituent close (by timestamp, after a stable sort),
`volume` = sum. **No open is constructed or read.**

**Bucket alignment.** Buckets are epoch-floored: `bucket_start = ts − ts %
period_ms`. The Unix epoch begins at 1970-01-01T00:00:00Z and every candidate
period divides an 86,400,000 ms day exactly, so epoch flooring puts **1d buckets
on UTC midnight** and intraday buckets on natural clock boundaries — :00/:05/:10
for 5m, :00/:15/:30/:45 for 15m, the top of the hour for 1h, and
00/04/08/12/16/20 UTC for 4h. No origin or offset argument exists, so alignment
cannot drift between callers. A test asserts the divisibility that makes this
sufficient.

**Incomplete buckets are DROPPED.** A partial bucket's high and low are taken
over a partial window and **understate** the true range — which biases ATR
downward, the direction that would make a timeframe look admissible when it is
not. Constituents are counted explicitly and any short bucket is discarded. No
forward-fill, no interpolation, no padding.

### 2.1 Dropped-bucket accounting

**Cells are buckets dropped for being short, and the percentage of buckets
formed.**

| timeframe | BTCUSDT dropped **(count)** | **(%)** | ETHUSDT **(count)** | **(%)** | SOLUSDT **(count)** | **(%)** |
|---|---:|---:|---:|---:|---:|---:|
| 5m | 0 | 0.0000 | 0 | 0.0000 | 0 | 0.0000 |
| 15m | 0 | 0.0000 | 0 | 0.0000 | 0 | 0.0000 |
| 1h | 0 | 0.0000 | 0 | 0.0000 | 0 | 0.0000 |
| 4h | 0 | 0.0000 | 0 | 0.0000 | 0 | 0.0000 |
| 1d | 0 | 0.0000 | 0 | 0.0000 | 0 | 0.0000 |

**Nothing was dropped anywhere. The 2% flag does not trigger for any
symbol-timeframe.** No measurement here rests on a thinned sample.

**That result was verified rather than assumed**, because zero drops across a
three-year window is the kind of clean number that usually means a counting bug.
Both source layers are exactly full over 2022-01-01 to 2024-12-31 (1,096 days):

| layer | bars per symbol | expected | |
|---|---:|---:|---|
| 1m | 1,578,240 | 1096 × 1440 = 1,578,240 | exact |
| 15m | 105,216 | 1096 × 96 = 105,216 | exact |

and every bucket count equals `1096 × 86,400,000 / period_ms` exactly:
**5m 315,648 · 15m 105,216 · 1h 26,304 · 4h 6,576 · 1d 1,096**, identically for
all three symbols. The drop path is not vacuous — a test feeds it a deliberate
gap and asserts the short bucket is dropped rather than emitted with an
understated range.

---

## 3. ATR% DISTRIBUTIONS

**ATR(14), Wilder's smoothing**, on resampled bars.
`TR = max(H − L, |H − C_prev|, |L − C_prev|)`. The first bar has no previous
close and therefore no true range at all; it is dropped rather than given the
`H − L` fallback, which is a different statistic sharing a name. ATR is seeded
with the simple mean of the first 14 true ranges, then
`ATR_i = (ATR_{i−1} × 13 + TR_i) / 14`. Implemented directly rather than as an
EWM, which seeds differently and would not reproduce a hand-computed value.

**DENOMINATOR: the close of the same bar the ATR is stated at.** `ATR% = 100 ×
ATR / close`. Stated once and used identically in every table below. Close
rather than an average or midpoint because it is the price a next-bar entry
would reference, and because it is the only price in the frame not already
inside the high/low the ATR is built from.

**Warm-up discarded: 114 bars.** 1 (no previous close) + 13 (true ranges before
the seed window completes) + 100 (ATR values after the seed, discarded for
stabilisation). The seed's residual weight after 100 further bars is
`(13/14)^100 = 6.0 × 10⁻⁴`, so it contributes under 0.06% of the reported ATR —
far below the resolution of any figure here.

**All cells are ATR% — PERCENT OF CLOSE.**

| timeframe | symbol | P10 **(%)** | P25 **(%)** | **MEDIAN (%)** | P75 **(%)** | P90 **(%)** | bars |
|---|---|---:|---:|---:|---:|---:|---:|
| 5m | BTCUSDT | 0.0683 | 0.1083 | **0.1654** | 0.2464 | 0.3485 | 315,534 |
| 5m | ETHUSDT | 0.0919 | 0.1374 | **0.2061** | 0.3039 | 0.4293 | 315,534 |
| 5m | SOLUSDT | 0.1912 | 0.2552 | **0.3543** | 0.4924 | 0.6831 | 315,534 |
| 15m | BTCUSDT | 0.1459 | 0.2195 | **0.3188** | 0.4456 | 0.6062 | 105,102 |
| 15m | ETHUSDT | 0.1894 | 0.2734 | **0.3916** | 0.5512 | 0.7589 | 105,102 |
| 15m | SOLUSDT | 0.3700 | 0.4837 | **0.6576** | 0.8837 | 1.1985 | 105,102 |
| 1h | BTCUSDT | 0.3576 | 0.5136 | **0.6947** | 0.9022 | 1.2044 | 26,190 |
| 1h | ETHUSDT | 0.4574 | 0.6229 | **0.8440** | 1.1435 | 1.5220 | 26,190 |
| 1h | SOLUSDT | 0.8359 | 1.0537 | **1.3824** | 1.7961 | 2.3831 | 26,190 |
| 4h | BTCUSDT | 0.9044 | 1.1494 | **1.4648** | 1.8526 | 2.4224 | 6,462 |
| 4h | ETHUSDT | 1.0835 | 1.4025 | **1.7813** | 2.3463 | 3.1075 | 6,462 |
| 4h | SOLUSDT | 1.8859 | 2.3088 | **2.8338** | 3.7348 | 4.7079 | 6,462 |
| 1d | BTCUSDT | 2.8127 | 3.1644 | **3.7166** | 4.6459 | 5.6433 | 982 |
| 1d | ETHUSDT | 3.0945 | 3.7221 | **4.6003** | 5.8567 | 7.7855 | 982 |
| 1d | SOLUSDT | 5.3535 | 6.0720 | **7.3777** | 8.8947 | 11.2505 | 982 |

**The Point 4 suspicion is confirmed.** 15m median ATR% is 0.3188% (BTC),
0.3916% (ETH) and 0.6576% (SOL) — all at or below the ~0.67% the closing
record's floor-binding rate implied. At 1.5 × ATR the 15m stop would sit at
0.48% / 0.59% / 0.99% of entry, **below even the 1.0909% fee-only floor on all
three symbols.** The Point 4 stop rule could not have placed a cost-admissible
stop through its ATR term at any point; the floor was doing the work, exactly as
the 65–81% binding rate said.

---

## 4. THE FROZEN RULE APPLIED

    m_required = 1.50 / median(ATR%)

    ADMISSIBLE   m_required in [1.0, 3.0]
    TOO FINE     m_required > 3.0   -- the multiplier would be doing the work
    TOO COARSE   m_required < 1.0   -- typical volatility already exceeds the
                                       floor; the floor is not binding

A timeframe is admissible only if **ALL THREE** symbols are ADMISSIBLE.

| timeframe | BTCUSDT `m_required` | mark | ETHUSDT `m_required` | mark | SOLUSDT `m_required` | mark | timeframe |
|---|---:|---|---:|---|---:|---|---|
| 5m | 9.068 | TOO FINE | 7.277 | TOO FINE | 4.234 | TOO FINE | ✗ |
| 15m | 4.705 | TOO FINE | 3.830 | TOO FINE | 2.281 | ADMISSIBLE | ✗ |
| **1h** | **2.159** | **ADMISSIBLE** | **1.777** | **ADMISSIBLE** | **1.085** | **ADMISSIBLE** | **✓** |
| 4h | 1.024 | ADMISSIBLE | 0.842 | TOO COARSE | 0.529 | TOO COARSE | ✗ |
| 1d | 0.404 | TOO COARSE | 0.326 | TOO COARSE | 0.203 | TOO COARSE | ✗ |

### 4.1 THE SELECTION: **1h**

**1h is admissible. It is also the ONLY admissible timeframe, so "finest
admissible" and "the admissible one" coincide** — the selection rule's
tie-breaking preference for finer was not exercised and did not need to be.

The candidate set brackets the answer cleanly on both sides. 5m fails on all
three symbols; 15m fails on two of three; 4h fails on two of three in the
opposite direction; 1d fails on all three. The transition from TOO FINE to TOO
COARSE happens **within one step either side of 1h** for every symbol, and no
symbol is marginal at 1h — the widest is BTC at 2.159 against a ceiling of 3.0,
and the narrowest is SOL at 1.085 against a floor of 1.0.

SOL at 1h (1.085) is the one cell near a boundary. It is 8.5% above the lower
edge; a 7.8% higher SOL median ATR% would have made 1h TOO COARSE for SOL and
left **nothing admissible at all**.

### 4.2 `m_required` at P25 and P75 — INFORMATION ONLY

**These do NOT enter the admissibility test.** The frozen rule anchors on the
median. They are reported because a stop clearing the floor at the median but
not at P25 behaves differently in calm regimes.

| timeframe | symbol | `m` at P25 **(calm)** | `m` at MEDIAN | `m` at P75 **(active)** |
|---|---|---:|---:|---:|
| 1h | BTCUSDT | 2.921 | 2.159 | 1.663 |
| 1h | ETHUSDT | 2.408 | 1.777 | 1.312 |
| 1h | SOLUSDT | 1.423 | 1.085 | 0.835 |
| 15m | BTCUSDT | 6.834 | 4.705 | 3.366 |
| 15m | ETHUSDT | 5.486 | 3.830 | 2.721 |
| 15m | SOLUSDT | 3.101 | 2.281 | 1.697 |
| 4h | BTCUSDT | 1.305 | 1.024 | 0.810 |
| 4h | ETHUSDT | 1.070 | 0.842 | 0.639 |
| 4h | SOLUSDT | 0.650 | 0.529 | 0.402 |
| 5m | BTCUSDT | 13.844 | 9.068 | 6.087 |
| 5m | ETHUSDT | 10.913 | 7.277 | 4.936 |
| 5m | SOLUSDT | 5.878 | 4.234 | 3.046 |
| 1d | BTCUSDT | 0.474 | 0.404 | 0.323 |
| 1d | ETHUSDT | 0.403 | 0.326 | 0.256 |
| 1d | SOLUSDT | 0.247 | 0.203 | 0.169 |

At 1h, **every P25 value stays inside [1.0, 3.0]** — 2.921, 2.408, 1.423 — so
the requirement remains satisfiable in the calm quartile without leaving the
band. **At P75 SOL falls to 0.835, below 1.0**: in active conditions SOL's
typical hourly range already exceeds the 1.50% floor unaided. That is not a
failure of the selection (the rule anchors on the median) but it does mean a
fixed multiplier would place SOL's stop above the cost floor in active regimes,
which is a sizing consequence for whoever writes the stop rule.

### 4.3 Per-tercile medians — INFORMATION ONLY

**Can the frozen tercile artifact be applied to resampled bars without
modification? Partly — and the part that cannot is stated rather than worked
around.**

The cuts in `data/derived/regime/terciles.json` are quantiles of the 30-day
rolling `m_star` and `efficiency_ratio` computed **on 15m bars**. Labelling a 1h
bar directly would require those axes computed on 1h bars, whose distribution is
different, so the cuts would no longer be its quantiles — applying them anyway
would be adapting the artifact, which this step will not do.

What can be done without modification is to attach the **already-labelled 15m
series** (`data/derived/regime/{symbol}.parquet`, produced by the frozen
artifact, spanning exactly 2022-01-01 to 2024-12-31) to 1h bars **by
timestamp**. **Attribution convention: each 1h bar takes the `m_star_label` of
the 15m bar at its bucket start.** A 1h bucket can span a label change; this
takes the label prevailing at entry to the bucket and does not attempt to
reconcile the rest.

**1h median ATR% by `m_star` tercile.** Note the direction: `m_star` is itself a
required-multiplier quantity, so the **low** `m_star` tercile is the **high**
volatility regime.

| symbol | low `m_star` **(median ATR%)** | `m_req` | mid **(median ATR%)** | `m_req` | high `m_star` **(median ATR%)** | `m_req` | unlabelled |
|---|---:|---:|---:|---:|---:|---:|---:|
| BTCUSDT | 0.8702 | 1.724 | 0.6786 | 2.210 | 0.5127 | 2.926 | 2.41% |
| ETHUSDT | 1.1435 | 1.312 | 0.8294 | 1.809 | 0.5904 | 2.541 | 2.41% |
| SOLUSDT | 1.6843 | 0.891 | 1.3422 | 1.118 | 1.0761 | 1.394 | 2.41% |

Of the nine cells, **eight remain inside [1.0, 3.0]**. Two sit near an edge:
BTC's high-`m_star` (calm) tercile at 2.926 approaches the 3.0 ceiling, and
**SOL's low-`m_star` (volatile) tercile at 0.891 falls below 1.0**. The 2.41%
unlabelled share is the 30-day warm-up of the regime window, which carries no
label by construction.

**This does not affect the selection.** The frozen rule assesses admissibility
on the aggregate distribution and says so explicitly; per-tercile figures are
reported for information and do not enter the test.

---

## 5. WHAT THE SELECTION IMPLIES

For 1h only. Plain arithmetic; no strategy conclusions are drawn.

### 5.1 Bar counts

| symbol | 1h bars formed **(2022-2024)** | bars after ATR warm-up | bars per day |
|---|---:|---:|---:|
| BTCUSDT | 26,304 | 26,190 | 24.00 |
| ETHUSDT | 26,304 | 26,190 | 24.00 |
| SOLUSDT | 26,304 | 26,190 | 24.00 |

Window: **1,096 days**. Against 15m's 105,216 bars, 1h gives **one quarter the
bars** — the power cost of the coarser timeframe, stated as a number and not
adjudicated here.

### 5.2 Target distance at 1:2 reward-to-risk

At the 1.50% stop floor, a 1:2 target sits at **2 × 1.50% = 3.00% of entry**.
In multiples of the timeframe's own median ATR%:

| symbol | median ATR% **(1h, %)** | 3.00% target as multiples of median ATR **(×)** |
|---|---:|---:|
| BTCUSDT | 0.6947 | **4.318** |
| ETHUSDT | 0.8440 | **3.554** |
| SOLUSDT | 1.3824 | **2.170** |

This is the target-to-horizon question from section 8.4 arriving from the cost
side. **The numbers are stated; no conclusion is drawn from them here.**

### 5.3 Funding intervals crossed

`fundInterval = 8` hours (report 17's fee artifact). At 1h, one bar is one hour.
**Funding is UNMODELLED and deferred to Point 6; these are scoping figures, not
a cost estimate.**

| hold **(bars)** | hold **(hours)** | funding boundaries crossed |
|---:|---:|---|
| 10 | 10.0 | **1 or 2**, depending on entry phase in the 8h cycle |
| 20 | 20.0 | **2 or 3**, depending on entry phase |
| 40 | 40.0 | **exactly 5** |

A hold whose length is an exact multiple of 8 hours crosses the same number of
boundaries regardless of when it started, which is why 40 bars is exact and the
other two are not.

---

## 6. PLANTED-MUTATION RESULTS

A guard that cannot detect its own target mutation proves nothing. Both were
verified by planting the mutation, observing the failure, and reverting from a
pre-mutation copy.

### 6.1 Holdout seal — the new code path onto sealed data

**The mutation.** In `src/timeframe/resample.py`, widen the date filter:

```
WINDOW_END    = dt.date(2024, 12, 31)  ->  dt.date(2025, 6, 30)
ALLOWED_YEARS = (2022, 2023, 2024)     ->  (2022, 2023, 2024, 2025)
```

**Why it would otherwise pass unnoticed.** The 1m layer is partitioned by year
and `year=2025` / `year=2026` **exist on disk**. The seal is not maintained by
absence. Nothing about a widened filter fails at import, at load, or in any ATR
figure — the numbers simply get quietly better-sampled and the holdout is spent
without anyone deciding to spend it.

**The failing assertion:**

```
>       assert rs.WINDOW_END < sch.HOLDOUT_TEST_START
E       assert datetime.date(2025, 6, 30) < datetime.date(2025, 1, 1)
E        +  where datetime.date(2025, 6, 30) = rs.WINDOW_END
E        +  and   datetime.date(2025, 1, 1) = sch.HOLDOUT_TEST_START
```

**8 tests failed** under the mutation, not one: the constant check, the
partition-path check, the end-to-end bar check at all five timeframes, and the
loader window check. The `assert_sealed` runtime guard also fired independently,
raising `HoldoutBreach` on the loaded frames — defence in depth, since a widened
filter upstream still cannot get past a check applied on the way out.

### 6.2 Admissibility classification inverted

**The mutation.** In `src/timeframe/atr_profile.py::classify`, swap the returns:

```
if m > m_max: return TOO_FINE      ->  return TOO_COARSE
if m < m_min: return TOO_COARSE    ->  return TOO_FINE
```

**Why it is easy to get wrong and hard to spot.** The mapping runs opposite to
the intuition the words suggest. A **large** required multiplier means the median
bar range is **small** relative to the floor, and small bars are what **fine**
timeframes have — so large `m` is TOO FINE. "m is large, so we need a lot of
ATR, so the timeframe must be too coarse" is the natural misreading, and it
produces a table where every cell still carries a plausible-looking label. The
mutation does not change **which** cells pass — only which direction they fail
in, and therefore which end of the candidate set the rule points at.

**The failing assertion:**

```
>       assert ap.classify(ap.m_required(0.20)) == ap.TOO_FINE
E       AssertionError: assert 'TOO COARSE' == 'TOO FINE'
E         
E         - TOO FINE
E         + TOO COARSE
```

2 tests failed. The guard asserts the full monotone sequence across rising
median ATR% — `TOO FINE → ADMISSIBLE → TOO COARSE` — so an inversion reverses a
sequence, not just a single label.

---

## 7. ASSUMPTIONS AND LIMITATIONS

1. **The [1.0, 3.0] multiplier band is the only free parameter in the rule, and
   it is a judgement.** Recorded as such in the frozen document. It decides the
   answer, and the sensitivity is asymmetric — stated here rather than left for
   someone to discover:

   | band | admissible | selected |
   |---|---|---|
   | **[1.0, 3.0]** — the frozen rule | 1h | **1h** |
   | [0.5, 3.0] — lower edge relaxed | 1h, 4h | 1h |
   | [1.0, 4.70] | 1h | 1h |
   | [1.0, 4.71] | 15m, 1h | **15m** |
   | [1.0, 5.0] | 15m, 1h | **15m** |

   **Relaxing the lower edge does not change the selection** — it only admits
   coarser timeframes, and finest-first still picks 1h. **Relaxing the upper
   edge past 4.705 does change it**, because 4.705 is BTC's requirement at 15m
   and BTC is the binding symbol there; above that threshold 15m becomes
   admissible and, being finer, is selected instead.

   So the whole selection turns on the upper edge sitting below 4.705, and 3.0
   is comfortably below it — but this is a judgement carrying the answer, not a
   derivation. It was fixed before the numbers were computed, which is the only
   protection available against having chosen it to produce this result.
2. **`m_required` uses the median only.** By construction of the frozen rule.
   Section 4.2 shows where P25 and P75 would move it.
3. **Resampled bars inherit whatever the 15m and 1m layers contain.** No
   independent validation of the source data was performed here beyond the
   completeness check in section 2.1; the layers' own integrity work belongs to
   Point 2.
4. **The 5m series is aggregated from 1m and every other series from 15m.** 5m
   therefore rests on a different source layer than the rest, and a defect
   confined to one layer would not affect both. No such defect is known.
5. **Regime attribution is by bucket-start label** (section 4.3), and 2.41% of
   1h bars are unlabelled because of the regime window's own warm-up.
6. **Nothing in this step establishes that 1h has an edge.** It establishes only
   that on 1h an ATR-proportional stop at the cost floor is operative rather
   than decorative. That is a necessary condition, not evidence of anything.
7. **No stop rule has been chosen.** The multiplier that would be used is not
   selected here — only the range within which one exists.

---

## 8. WHAT THIS STEP FIXES FOR EVERYTHING THAT FOLLOWS

- **The timeframe is 1h.** Selected by a rule frozen at `96c96cf` before the
  numbers existed, and it was the only admissible candidate.
- **15m is ruled out, and the Point 4 stop rule is retrospectively explained.**
  At 15m, 1.5 × median ATR gives a stop of 0.48%–0.99% of entry, below even the
  fee-only floor of 1.0909% on all three symbols. The Point 4 floor bound
  65–81% of bars because it could not do otherwise.
- **A stop-rule multiplier in [1.085, 2.159] places the stop at the 1.50% floor
  at the median across the three symbols.** The exact multiplier is a later
  choice; this is the band it must live in.
- **The power cost is one quarter of the bars.** 26,304 per symbol at 1h against
  105,216 at 15m, over 2022–2024.
- **SOL is the constraint at both ends.** It is the only symbol admissible at
  15m and the closest to failing at 1h (1.085 against a floor of 1.0), and in
  its active quartile and its volatile tercile it falls below 1.0. Whatever stop
  rule is written will bind differently on SOL than on the other two.
- **The holdout is still unspent.** 2025-01-01 onward has never been read, and
  the seal now holds through a resampling path that did not exist before.
