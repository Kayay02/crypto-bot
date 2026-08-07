# Report 09a — Regime Artifact Rerun Under a Clean Hash

Addendum to `reports/09_regime_measurement.md`. Regenerates the Point 4.1 artifacts now that the pre-registration is committed, places the frozen tercile file under version control, and corrects two errors in report 09.

**No `src/regime/` logic was changed.** The artifacts are reproducible from the same code that produced them at `d9d8f97`.

**Firewall intact.** No trade outcome read or computed; `simulate` not imported; holdout sealed at 2025-01-01 and enforced by a passing test.

---

## 1. The clean commit hash

Pre-registration commit: **`7a326106f37da843ea982239b371b7e9f65e0fa2`**

Tree was verified clean before the rerun — `git status --porcelain` empty, and `git_revision()` returned the hash with **no `-dirty` suffix**. Both artifacts now record it:

| artifact | before | after |
|---|---|---|
| `terciles.json` | `d9d8f97…-dirty` | **`7a32610…`** (clean) |
| `_manifest.json` | `d9d8f97…-dirty` | **`7a32610…`** (clean) |

**How regeneration was handled.** `freeze_terciles` returns the existing payload unchanged when the fit window matches, which is correct — but it means a rerun on an identical window keeps the stale `-dirty` hash. So `terciles.json` was **deleted deliberately** before the rerun, which is exactly the path the refusal message itself prescribes ("Delete the file deliberately if a refit is genuinely intended"). **The refusal logic was not weakened**: it still raises on any fit-window mismatch, and the tests covering that (`test_frozen_cuts_file_raises_rather_than_overwriting`) still pass. The fit window is unchanged at 2022-01-01 → 2025-01-01 exclusive, per Appendix B, and was not moved to 2022-04-01.

---

## 2. Determinism check — IDENTICAL

All six cut values reproduce exactly. No discrepancy, so no stop condition.

| symbol | axis | regenerated (low / high) | report 09 §3 | match |
|---|---|---|---|---|
| BTCUSDT | m_star | 2.84405 / 3.66869 | 2.84405 / 3.66869 | ✓ |
| ETHUSDT | m_star | 2.26727 / 3.01855 | 2.26727 / 3.01855 | ✓ |
| SOLUSDT | m_star | 1.81192 / 2.24182 | 1.81192 / 2.24182 | ✓ |
| BTCUSDT | efficiency_ratio | 0.01305 / 0.03020 | 0.01305 / 0.03020 | ✓ |
| ETHUSDT | efficiency_ratio | 0.01200 / 0.02880 | 0.01200 / 0.02880 | ✓ |
| SOLUSDT | efficiency_ratio | 0.01376 / 0.02706 | 0.01376 / 0.02706 | ✓ |

Stronger than the required check: the `cuts` object compares **equal to the previous run's**, and all three parquet files are **byte-identical** to the pre-rerun copies (`cmp` clean). The only bytes that changed anywhere are the two `git_commit` strings.

Row and NaN counts match §6 exactly:

| symbol | rows | valid | NaN |
|---|---|---|---|
| BTCUSDT | 105,216 | 102,242 | 2,974 |
| ETHUSDT | 105,216 | 102,242 | 2,974 |
| SOLUSDT | 105,216 | 102,242 | 2,974 |

Holdout seal reconfirmed: `max(ts) < 2025-01-01` on all three.

---

## 3. Tracking the tercile artifact

`.gitignore` gained a scoped negation. Git cannot re-include a file inside an ignored *directory*, so the parent directories are unignored and their contents re-ignored, one level at a time, before the single file is negated:

```
!/data/
/data/*
!/data/derived/
/data/derived/*
!/data/derived/regime/
/data/derived/regime/*
!/data/derived/regime/terciles.json
```

Verified by `git add --dry-run`, which refuses an ignored path — a more reliable test than `git check-ignore -v`, whose exit code is 0 for a *negation* match as well as an ignore match and will mislead you here:

| path | result |
|---|---|
| `data/derived/regime/terciles.json` | **addable → tracked** |
| `data/derived/regime/BTCUSDT.parquet` | ignored |
| `data/derived/regime/ETHUSDT.parquet` | ignored |
| `data/derived/regime/SOLUSDT.parquet` | ignored |
| `data/derived/regime/_manifest.json` | ignored |
| `data/derived/ohlcv_15m/BTCUSDT.parquet` | ignored |
| `data/derived/_manifest.json` | ignored |
| `data/raw` | ignored |

Exactly one file under `/data/` is now tracked. Everything else is unchanged.

---

## 4. The random-walk floor was wrong — corrected

Report 09 gave the floor for the Kaufman efficiency ratio as `√(2/πN)`. That is wrong. The mean-absolute-deviation factor `√(2/π)` appears in **both** numerator and denominator and cancels:

```
denominator:  N · E|Δ|   = N · σ · √(2/π)
numerator:    E|S_N|     = σ · √N · √(2/π)
ratio                    = 1/√N
```

| window | N | old (wrong) | **corrected** |
|---|---|---|---|
| 14d | 1,344 | 0.02176 | **0.02728** |
| 30d | 2,880 | 0.01487 | **0.01863** |
| 60d | 5,760 | 0.01051 | **0.01318** |

The corrected floor is **higher**, so the observed excess over it is **smaller**. The direction of the original finding is unchanged; its magnitude was overstated.

### Diff summary — what changed in report 09

| location | change |
|---|---|
| §3 efficiency paragraph | floor `√(2/πN)` ≈ 0.0149 → **1/√N ≈ 0.01863**; "about 1.3× that floor" → **"about 1.03–1.12×"**; inline correction note added |
| §7 sensitivity table prose | floor series `0.0218 → 0.0149 → 0.0105` → **`0.02728 → 0.01863 → 0.01318`** |
| §8.1 | rewritten: derivation shown, observed/floor table added, the three findings below added, tercile-cut reading replaces "top third of a distribution" |
| §3 (new subsection) | covariate ranges added — see §5 below |
| §8.3 + §1 file tree | corrected: terciles.json is now tracked (was recorded as untracked with a recommendation) |

Nothing else in report 09 was touched. The body of the pre-registration was not touched at all.

### The three findings the correction requires

**BTC at 14 days sits marginally BELOW the floor.** Observed median 0.0267 against a floor of 0.02728 — a ratio of **0.98**. SOL is below at 14 days (0.95) and at 60 days (0.92). A sub-floor reading is not anomalous: the floor is an asymptotic expectation, individual windows scatter around it, and short-horizon mean reversion pushes below it. But it does mean that at 14 days these series are not distinguishable from chance on this measure.

**Observed median ÷ corrected floor:**

| symbol | 14d | 30d | 60d |
|---|---|---|---|
| BTCUSDT | **0.98** | 1.12 | 1.29 |
| ETHUSDT | 1.08 | 1.03 | 1.19 |
| SOLUSDT | 0.95 | 1.05 | 0.92 |

**The monotone rise with window length holds for BTC only** (0.98 → 1.12 → 1.29). ETH dips at 30 days and SOL peaks at 30 then falls below the floor at 60, so this is a BTC observation, not a market-wide one — a caveat beyond the one asked for, but stating it as a general pattern would overclaim on the evidence.

**Description only, and it says nothing about the strategy.** Three points is not a trend. And decisively: the strategy holds **21–41 bars, i.e. 5–8 hours**, one to two orders of magnitude shorter than any of these windows. Nothing about the edge follows from how efficiency behaves at 14 versus 60 days. It is recorded because it bears on how a regime *label* should be read.

**The corrected reading of the tercile cuts**, which replaces "the top third of a distribution":

| symbol | low cut | × floor | high cut | × floor |
|---|---|---|---|---|
| BTCUSDT | 0.01305 | **0.70×** | 0.03020 | **1.62×** |
| ETHUSDT | 0.01200 | 0.64× | 0.02880 | 1.55× |
| SOLUSDT | 0.01376 | 0.74× | 0.02706 | 1.45× |

For BTC the low cut sits at 0.70× the floor and the high cut at 1.62×. So a `low` label means **demonstrably choppier than chance** and a `high` label means **meaningfully directional** — about 60% more net displacement per unit of path than a random walk. Those are interpretable conditions, not merely distributional thirds. The same holds for ETH and SOL.

**§8.1's warning survives and is strengthened.** At the primary 30-day window the medians sit at only 1.03–1.12× the floor, and the middle tercile straddles it. These markets are only modestly distinguishable from a random walk on this measure, and a post-lift stratification reading "the strategy works in efficient markets" should be understood as "the efficient third means ER > ~0.030" — a mild directional tilt, not a strong trend.

---

## 5. The two reported covariates

30-day window, 2022-2024, per symbol. Uncut and unlabelled by design.

**drift_log_return** — signed log return over the window:

| symbol | min | median | max |
|---|---|---|---|
| BTCUSDT | −0.5313 | +0.0193 | +0.4801 |
| ETHUSDT | −0.8032 | +0.0008 | +0.6119 |
| SOLUSDT | −1.2335 | −0.0042 | +1.0857 |

**ema_fraction** — fraction of window bars with EMA20 > EMA50:

| symbol | min | median | max |
|---|---|---|---|
| BTCUSDT | 0.3625 | 0.5132 | 0.6826 |
| ETHUSDT | 0.3625 | 0.5010 | 0.7222 |
| SOLUSDT | 0.3424 | 0.4854 | 0.7024 |

**median_daily_quote_volume** — USDT:

| symbol | min | median | max |
|---|---|---|---|
| BTCUSDT | 1,873,007,933 | 5,236,398,318 | 17,541,391,350 |
| ETHUSDT | 411,734,654 | 1,797,435,227 | 8,364,225,347 |
| SOLUSDT | 18,669,136 | 44,038,683 | 605,927,106 |

Drift medians are near zero on all three, so the fit window is not dominated by one directional era — SOL's is slightly negative despite having the widest range. `ema_fraction` medians sit near 0.50, floored around 0.34 and capped around 0.72, so the strategy's own trend filter is roughly balanced over the window and never collapses to always-on or always-off. Liquidity spans an order of magnitude within each symbol and about two orders between BTC and SOL; per §4.1 that bears on slippage realism, not on the RVOL gate, which is session-normalised over trailing days and self-normalises to level.

---

## 6. The volume warm-up boundary — n+94 is correct

**No off-by-one. Nothing changed.**

The premise in the brief was that a 24-hour sum spans 96 bars so the boundary "should be n+95 under a 0-indexed convention". The 96-bar span is right; the conclusion is not, because two 0-indexed offsets compose and each contributes `length − 1`, not `length`:

```
trailing 24h sum:  rolling(96, min_periods=96)   first valid INDEX = 95      ( = 96 − 1 )
median of that:    rolling(n,  min_periods=n)    first valid INDEX = 95 + (n − 1) = n + 94
```

Verified empirically at n = 288: the 24h sum first becomes valid at index 95 and the median of it at index **382 = n + 94**, not 383.

**Convention, stated explicitly:** `warmup_bars(window_days)` returns a **count of leading masked bars**, and the **first valid 0-indexed position equals that count**. At the primary 30-day window both are **2,974** — indices 0–2,973 are NaN, index 2,974 is the first complete regime observation. The two coincide only because indexing is 0-based; they are conceptually different quantities and the report should not be read as conflating them.

Confirmed that all five measured columns share that single boundary after masking.

---

## 7. The three excluded tests

`pytest.ini` carries `addopts = -m "not lookahead"`, deselecting three tests, all in `tests/test_signals.py`:

- `test_planted_lookahead_bug_is_caught` — Donchian channel shifted `-1`
- `test_planted_rvol_lookahead_is_caught` — RVOL slot baseline reading future days
- `test_same_day_self_reference_is_invisible_to_truncation_but_caught_elsewhere` — documents the guard's blind spot

**Why they were excluded:** they were framed as *demonstrations* rather than regression tests — each deliberately breaks the code to prove a guard has teeth. The original reasoning was that a test which monkeypatches a bug into production code is a different category from one that asserts correct behaviour, and running it by default might confuse a reader watching the suite.

**How long they take: 0.14 seconds combined** (0.11 + 0.02 + 0.01). The whole suite with them included runs in **1.98s**; the default selection runs in **2.38s**. They are free — the difference is measurement noise.

**Recommendation: bring them into the default run.** There is no cost argument, and the framing argument is weak: these assert that a guard raises on a specific mutation, which is exactly what a regression test does. The project's own history is the strongest case — **three vacuous guards have been found here**, and §4.1 of the pre-registration calls that "a pattern, not bad luck". A test that proves a guard has teeth is precisely the test you cannot afford to let decay, and a suite that never runs it will not notice when it stops working.

Concretely: delete the `addopts` line from `pytest.ini` and keep the `lookahead` marker registered for selective runs. **I did not make this change** — `pytest.ini` is outside the files this task authorises me to modify, and altering test selection during a pre-registration rerun is not something to slip in unannounced.

**Worth noting:** the newer regime mutation tests are **not** marked `lookahead` and already run by default — all 13 of `test_regime_causality.py`, including the three planted mutations. Only the three older engine ones are excluded, so the gap is narrower than it looks, but it is still the older guards that are unwatched.

---

## 8. Verification summary

| check | result |
|---|---|
| tree clean before rerun | ✓ `git status --porcelain` empty |
| HEAD hash has no `-dirty` | ✓ `7a32610…` |
| both artifacts record the clean hash | ✓ |
| tercile cuts identical to report 09 §2 list | ✓ all six, plus `cuts` object equal |
| parquet byte-identical to previous run | ✓ all three |
| row / NaN counts match §6 | ✓ 105,216 / 102,242 / 2,974 |
| `terciles.json` tracked, parquet ignored | ✓ |
| holdout sealed | ✓ `max(ts) < 2025-01-01`, test passes |
| firewall | ✓ no `simulate` import, tokenising test passes |
| full suite | ✓ **207 passing** (204 + 3) |

---

## 9. What I still believe is wrong

**9.1 — `freeze_terciles` cannot distinguish a legitimate rerun from a silent refit, and the delete-first workaround is the weak point.** The guard raises on a mismatched fit window, which is the important case. But an *identical*-window rerun returns the stale payload rather than refreshing provenance, so the only way to update a `-dirty` hash is to delete the file — the one operation the artifact exists to make difficult. Now that `terciles.json` is tracked, git provides the real protection (a deletion shows in `git status`), so this is much less serious than it was an hour ago. Still, a cleaner design would let the file be rewritten when the *cuts are identical* and refuse otherwise, making the deletion path unnecessary. Not changed here: modifying `src/regime/` is out of scope for this task, and the artifacts must stay reproducible from the code that produced them.

**9.2 — `_manifest.json` is still untracked, so the row/NaN counts and config it records are not provable.** The brief scoped tracking to `terciles.json` only, and I followed that. But the manifest is the artifact that records *what was produced* (row counts, per-column NaN counts, the config, the same git hash) and it is ~1.7 KB. If the argument for tracking the cuts is provability, the same argument covers the manifest. The parquet files are genuinely large (9.8 MB total) and belong in `.gitignore`; the manifest does not. Flagged, not changed.

**9.3 — report 09's header still records `d9d8f97`, which is no longer the hash in the artifacts.** I left it deliberately: it is the commit at which report 09 was *written*, and rewriting it would misrepresent when that analysis happened. The artifacts now carry `7a32610` and this addendum records the relationship. Worth knowing that the two documents cite different hashes for good reason.

**9.4 — the 2022-01-01 fit-window start is now formally pre-registered (Appendix B), which closes report 09 §8.6.** No action needed; recording that the flag is discharged. Appendix B's rationale — that regime labels describe market conditions rather than the traded population — is the right argument, and the ~5.6% of the fit set that falls outside the trading window is Feb–Mar 2022 as report 09 estimated.

**9.5 — a caveat on Appendix E worth restating.** Appendix E now records that regime m\* (rolling 30-day, range 1.16–8.58) is a different quantity from sweep-anchor m\* (per 6-month training fold). That is correct and important. The one thing it does not say: the sweep-anchor values have **not yet been computed**, so nobody knows their range yet. The 6-month fold medians will sit well inside 1.16–8.58 — a longer window averages more — but by how much is unmeasured. Nothing should be inferred about the sweep range until those folds exist.
