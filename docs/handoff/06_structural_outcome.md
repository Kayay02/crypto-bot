# Handoff 06 — Structural Outcome and Point 3R Engine Amendment

Decision record for what the structural measurement pass settled and what the engine now implements.

**This document APPENDS to `docs/handoff/05_point_1r.md`; it does not revise it.** Section 4 of that handoff still specifies `vwap_position` (B3) as a live amendment, and Section 13 still carries the thresholds it was measured against. That is deliberate. The record should show what was proposed, what was measured, and what survived — a design record that quietly deletes its dead branches cannot be audited, and the fact that B3 was once alive is part of why the thresholds were pre-committed in the first place.

Measurements: `reports/07_structural_pass.md`, commit `de4b8d0`. Implementation: `reports/08_point_3r.md`.

The performance firewall was in force throughout. Every justification below is a pass rate, a rejection rate, a dispersion statistic or a logical entailment.

---

## 1. Status

- **Points 1, 2, 3, 1R** — closed.
- **Structural measurement pass** — closed at commit `de4b8d0`.
- **Point 3R (engine amendment)** — closed by this document.
- **Next open point: Point 4 — validation design pre-registration.**

The firewall lifts at the **start of Point 4**, only after the validation design is written down and pre-registered.

---

## 2. The Four Rulings

### Ruling 1 — `vwap_position` (B3) is DEAD. Permanently, and not as a labelled variant.

Killed on three independent mechanical grounds:

1. **Dispersion, measured on the population a threshold actually sees.** The gate is applied directionally — longs test `vwap_position`, shorts test `1 − vwap_position` — so the relevant dispersion is per direction. Measured that way the IQR is **0.089–0.126** against the pre-committed cut of **0.15**, failing **6 of 6 symbol-years**. (Pooled across directions it is 0.124–0.157 and splits 3–3, but the pooled figure is inflated by direction-mixing: the same artifact inflated the B3 redundancy correlation five-fold, from ~0.06 within direction to ~0.35–0.61 pooled.)
2. **It is a constant, not a discriminator.** The median of the gated term sits at **0.55–0.58** in every symbol-year, for both directions. On a breakout bar the volume-weighted average price sits slightly toward the breakout direction — consistently, on essentially every bar, rather than distinguishing between them.
3. **Any usable threshold lands in the densest part of the distribution.** With IQR ≈ 0.10 around a median of ≈ 0.56, a threshold anywhere near the median classifies bars that differ by less than measurement noise. Signal counts confirm the cliff: at `vp >= 0.6` a conjunctive gate leaves 119–297 signals per symbol-year-direction, and at `vp >= 0.7` it leaves **2–41**, below the 30-per-direction evidence minimum almost everywhere.

**Note what did NOT kill it.** B3 passed its validity check outright (100.0000% of 210,240 bars, zero violations) and passed non-redundancy decisively (within-direction |rho| ≤ 0.18). `vwap_position` genuinely carries information that `close_position` does not. It carries almost none of it. Orthogonal and nearly constant.

**Do not revive it.** Reintroducing a component after seeing it fail its pre-committed check is exactly the iterative search the D5 single-pass rule bans. It is not registered as a labelled variant, and no diagnostic column records it.

### Ruling 2 — `rsi_lower` (F2) DROPS. RSI leaves the strategy entirely.

**Zero rejections in 11,711 breakout bars**, across 3 symbols × 2 years. The minimum RSI on any long breakout bar over two years was **54.18** — more than four points clear of the 50 threshold, never close to binding. F2's pre-committed cut was "rejects < 5% → decorative, drops now".

1R.5 argued this was "not strict entailment — Wilder smoothing has memory beyond 14 bars — but narrow". Over 2022–23 it is entailment in practice: a bar closing above a 20-bar high with EMA20 > EMA50 has, without exception, had gains dominate losses over the prior 14 bars.

`rsi_upper` was already removed by F3 for violating the Guard Rail Principle. With the lower bound now gone, **RSI leaves the strategy entirely.** The original brief asked for an oscillator; evidence removed it. Do not reintroduce one.

`rsi_wilder` is retained and `rsi` is recorded on signal rows as an informational column. No entry condition reads it, and a test asserts that changing RSI does not change which bars signal.

### Ruling 3 — Session-normalised RVOL (B1) STANDS.

B1's registered rationale is confirmed. Under the flat 20-bar baseline the gate's pass rate on breakout bars swings **32–51 percentage points** by hour of the UTC day — the gate substantially measures what time it is, exactly as B1 argued. Session-normalisation compresses that spread in **5 of 6 symbol-years** (SOL 2022 is the exception and widens).

Denomination is `quote_volume`, on the B2 decision rule: the more stable trailing baseline won in **3 of 3 symbols across both years**.

**Recorded against it, because it belongs in the record:** at *matched* selectivity, session-normalised RVOL is **less** selective than the flat baseline in all 24 cells measured (ratios 2.06–3.71 against flat's 3.60–5.97). B1 stands on the mechanism it was registered to fix, not on a selectivity improvement, and it did not deliver one. Whether that trade is worth making is a Point 4 question.

`baseline_days` sensitivity is close to flat — the selectivity ratio moves by less than 0.5 across 5 → 30, non-monotonically — so **a Point 4 sweep should not spend much resolution on it.**

### Ruling 4 — `c_roundtrip` uses the engine's actual cost structure.

Entry taker + stop taker + entry slippage + stop-market haircut **on the stop leg only** = 0.06% + 0.06% + 0% + haircut. Entry slippage is deliberately zero: the 1m-close fill convention already absorbs latency (~200 ms measured round trip, so the convention over-covers by roughly 300×), and charging a haircut on both legs would double-count.

This resolves the specification inconsistency flagged in report 07 §7.5, where the prompt and A2 both said "haircut on both sides" but the engine applies it once. The difference is material: 1.020% vs 1.320% for BTC/ETH, and it propagates into `m*` and hence the A6 sweep range.

---

## 3. Baseline Strategy After 3R

| Element | Specification | Status |
|---|---|---|
| Timeframe | 15m, Bitget USDT-M perps | FIXED |
| Universe | BTC / ETH / SOL | FIXED |
| Capital / risk | ~$2,000 capital; `risk_usd` = $20 per trade net of costs | FIXED |
| Trend filter | EMA20 / EMA50 | FIXED |
| Trigger | Donchian-20 breakout on a closed 15m bar; fill = 1m close of first minute of bar T+1 | FIXED |
| RVOL baseline | session-normalised, median of same UTC slot over trailing completed prior days | FIXED |
| RVOL denomination | `quote_volume`, numerator and denominator | FIXED |
| `baseline_days` | **no default; must be supplied** | UNSET — TO BE CALIBRATED |
| `rvol_threshold` | **no default; must be supplied** | UNSET — TO BE CALIBRATED |
| `vwap_position` | killed on measurement | **REMOVED** |
| RSI (`rsi_lower`, `rsi_upper`) | killed on measurement / Guard Rail Principle | **REMOVED** |
| `rsi_period` | informational column only | N/A |
| `stop_atr_mult` | multiplier on ATR(14); **no default; must be supplied** | UNSET — TO BE CALIBRATED |
| `stop_min_pct` | `max(N_cost * c_roundtrip, risk_usd / (E * L_max))` → 1.020% BTC/ETH, 1.320% SOL | **DERIVED** |
| `N_cost` | 6, shared across symbols | UNSET — TO BE CALIBRATED |
| `stop_max_pct` | percent-of-price cap; **no default; must be supplied** | UNSET — TO BE CALIBRATED |
| Minimum order size | `minTradeNum` / `minTradeUSDT`, explicit rejection | **FIXED (probed)** |
| Target | +2R, solved net of costs, maker exit | FIXED |
| `time_stop_bars` | `tau * donchian_period` → 20 | **DERIVED** |
| `max_hold_bars` | `2 * donchian_period` → 40 | **DERIVED** |
| `tau` | 1.0, narrow sweep band | UNSET — TO BE CALIBRATED |
| `threshold_R` | solved from `phi` → +1R | **DERIVED** |
| `phi` | 1.0 (linear pace) | UNSET — TO BE CALIBRATED |
| Time-stop semantics | **state check at the checkpoint close**, not an intrabar latch | FIXED |
| `time_stop_enabled` | NO_TIME_STOP counterfactual arm | FIXED (not baseline) |
| Cooldown (20-bar extreme) | logical no-op | **REMOVED** |
| `cooldown_bars` | 0 (inert); registered sweep dimension | UNSET — TO BE CALIBRATED |
| Position rule | one position per symbol, no pyramiding (portfolio mode only) | FIXED |

**Entry rule, in full.** Long, on a closed 15m bar: `EMA20 > EMA50` **and** `close >` Donchian-20 upper **and** session-normalised RVOL `>= rvol_threshold`. Short is the symmetric inverse. That is the whole rule.

**Parameter surface:** four parameters with no default (`stop_atr_mult`, `stop_max_pct`, `rvol_threshold`, `baseline_days`), plus `N_cost`, `tau`, `phi` and `cooldown_bars` as sweepable knobs with stated defaults. Three quantities that were previously free inputs (`stop_min_pct`, `max_hold_bars`, `threshold_R`) are now derived.

---

## 4. Corrections to the Record

### 4.1 Finding 3's specific numbers must not be quoted forward

Section 2 of `05_point_1r.md` records RVOL >= 1.5 admitting **65.9% (2022) and 68.8% (2023)** of breakout bars. The structural pass measured **~70.6% and ~74.0%** on the same window — same direction of year-over-year change, but roughly 5 points apart in level.

The most likely explanation is a denominator difference: the structural pass defines a breakout bar as trend + Donchian only, whereas Finding 3's figure may have been computed on a population that already had other conditions applied, or pooled across symbols with different weighting. **Finding 3's provenance is not recorded anywhere**, so this cannot be settled.

**Ruling: Finding 3's specific numbers must not be quoted forward.** Its *conclusion* — that the volume gate is weak, admitting roughly two-thirds of breakout bars — is unaffected and is confirmed by the reproducible measurement. Where a number is needed, use the structural pass figures, which have recorded provenance.

### 4.2 Removing `rsi_upper` returns ~27% of breakout bars — the highest-momentum ones

Measured: `rsi_upper <= 75` was rejecting **514–569 long breakout bars per symbol (~27%)** and **443–490 short (~26%)** over 2022–23.

F3 removed it on principle, before this was measured. The measurement quantifies what that removal returns to the population, and the composition matters more than the count: these are by construction **the strongest momentum bars in the sample** — precisely the continuations a trend-continuation strategy exists to capture. The trade population after 3R is therefore not merely ~27% larger; it is skewed toward stronger moves than any earlier population. Any Point 4 comparison against pre-1R diagnostics must account for this.

### 4.3 The reversal-breakout hypothesis is UNEXERCISED, not refuted

F2 pre-registered two readings for `rsi_lower`: decorative, or "a small coherent reversal-breakout population" making it a real regime filter. With **exactly zero** rejections there was no population to characterise, so the second reading was never given a chance to be tested.

The verdict (drops now) follows mechanically from the < 5% cut and is not in doubt. But the record must say the hypothesis was **unexercised**, not falsified. Whether reversal breakouts exist as a distinct population remains open; RSI >= 50 turned out not to be what separates them. If that question is ever reopened it needs a different instrument, and reopening it is a new registration, not a revival.

---

## 5. New Standing Rule — Every Threshold Carries Its Aggregation Rule

> **Every pre-committed threshold must state the population it is measured over and the rule for aggregating across symbols and years. Absent an explicit statement, the default is the Section 10 two-of-three pattern: the condition must hold in at least 2 of 3 symbols across both years.**

ER1's omission of one nearly decided B3 by accident. The dispersion check said only "IQR >= 0.15 on breakout bars". It did not say whether "breakout bars" meant pooled across directions or per direction — and the two readings disagreed about whether the amendment lived (3 pass / 3 fail pooled, versus 6 fail directionally). It also gave no rule for resolving a 3–3 split, unlike B2 in the same section, which carries an explicit two-of-three rule.

Had the pooled reading been adopted without noticing the ambiguity, B3 would have survived on a coin-flip and been built. The threshold was pre-committed correctly; what was missing was the specification of what it applied to.

This rule is binding on Point 4's validation design, where every kill condition will need the same treatment.

---

## 6. What Point 4 Inherits

1. **The engine implements this design and nothing is left to interpret**, but it cannot run without four explicitly-supplied parameters. Choosing them is Point 4's job.
2. **`m*` must be computed per walk-forward training fold**, never globally. The structural pass reported `m*` = 1.71–4.08 for scale only; a globally computed anchor would read the 2025–26 holdout and leak it.
3. **The derived floor is higher than the old hardcoded one** (1.020% / 1.320% vs 1.000%), so clearing it requires `stop_atr_mult` above `m*` in every symbol-year. The A3 acceptance check — floor binding under 20% per symbol — is a harder target than it was before this pass.
4. **The state check changes the trade population**, not just the exit labels. Trades that wick to +1R and retrace are now cut. `touched_threshold_intrabar` is recorded so the size of that population is measurable, and it should be reported at Point 4 as a diagnostic of how much the rule change moved.
5. **The evidence minimums do not move**: 200 IS, 50 OOS, 30 per direction, per symbol.
6. **2022–23 is partially spent.** Structural diagnostics have now been run on it twice. Lean on 2024 and the 2025–26 holdout for real evidence. The holdout remains entirely untouched.
