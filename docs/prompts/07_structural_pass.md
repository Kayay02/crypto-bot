# Claude Code Prompt — Structural Measurement Pass

> Paste everything below the line into Claude Code in VS Code.

---

## Goal

Run the pre-registered structural checks from Point 1R and report the measurements. These checks decide whether several 1R amendments live or die **before** any of them are implemented. Also fold in three small documentation corrections carried over from the previous report.

## Context

Systematic algorithmic trading bot. Bitget USDT-M perpetual futures, BTC/ETH/SOL, 15-minute candles, ~$2,000 account, `risk_usd` fixed at $20 per trade after costs.

Points 1, 2, 3 and 1R are closed. The engine is at commit `106cb42` and **still implements the pre-1R design** — it has not yet been amended. That is deliberate: this pass measures whether the 1R amendments are worth building.

Decision record: `docs/handoff/05_point_1r.md`, especially **Section 13** which fixes the numeric kill thresholds. Those thresholds were committed before this measurement was run, precisely so that a measurement cannot be interpreted against a threshold chosen after seeing it. **Do not adjust, reinterpret or soften any of them.**

A **performance firewall** is in force. It lifts only at the start of Point 4. Nothing in this task goes near it — every quantity below is a bar-level statistic, a count or a correlation. **No trade is simulated. No P&L, expectancy, win rate, return or equity figure is computed, displayed or estimated, and no aggregate is taken of the `net_pnl` or `r_multiple` columns.**

## Window restriction

**All measurements are restricted to 2022-01-01 → 2023-12-31**, per the 1R.2 contamination ledger (B0). Do not read, load, aggregate or reason about 2024, 2025 or 2026 data anywhere in this task. The 2025–26 holdout must remain untouched.

If a trailing-window calculation needs warm-up data, it may reach back before 2022-01-01 only if such data exists; otherwise start measurements after the warm-up period inside 2022 and say so.

---

## Files

Create:
- `src/analysis/__init__.py`
- `src/analysis/structural_pass.py` — the measurement script
- `tests/test_structural_pass.py` — tests for the new code
- `docs/prompts/07_structural_pass.md` — this prompt, verbatim
- `reports/07_structural_pass.md` — the report

Modify (documentation corrections only):
- `docs/handoff/05_point_1r.md`

**Do not modify anything under `src/engine/`, `config/` or `data/`.** You may import from `src/engine/` — reusing the existing, tested indicator functions is required where they exist, so that "breakout bar" means exactly the same thing here as in the engine.

---

## Part 1 — Documentation corrections

Three flags from `reports/06_1r_errata.md` are now resolved. Apply them to `docs/handoff/05_point_1r.md`:

**C1 — Renumber Section 13's items from `A1–A7` to `ER1–ER7`.** They currently collide with Section 3's `A1–A7` (stop-geometry amendments). Update every cross-reference to Section 13 items throughout the document. Section 3's labels do not change.

**C2 — Supersede the stale B4 figure.** The B4 paragraph in Section 4 still carries `~66% x ~50% = ~33%`. Replace the `~50%` and `~33%` with the corrected design range from Section 13 (`vwap_position` 25–75% ⇒ joint survival band 16%–50% of breakout bars), and add a pointer to the Section 13 item. Leave the `~66%` RVOL figure, which was measured.

**C3 — Record the tick schedule in the handoff.** Report 06 flagged that "one tick" is used in the B3 validity tolerance but no tick size appears in any handoff document. The values exist in `config/contracts_cache.json` and were probed and verified during Point 3. Add them to Section 8 (or a clearly labelled subsection) as a recorded fact:

- BTCUSDT — 0.1
- ETHUSDT — 0.01
- SOLUSDT — 0.0001 before 2024-08-14T04:05:00Z; 0.001 from that timestamp

State that the tick is `priceEndStep × 10^-pricePlace`, not `10^-pricePlace`, and that the SOL change was discovered by grid-validating historical prices. Read the values from `config/contracts_cache.json` rather than transcribing them from this prompt, and flag any disagreement.

---

## Part 2 — Definitions

These must be implemented exactly, because every measurement below is conditioned on them.

**Breakout bar (long):** on a closed 15m bar, `EMA20 > EMA50` **and** `close >` the Donchian-20 upper level. Short is the symmetric inverse. **The RVOL gate, `vwap_position` and RSI are all excluded from this definition** — they are the things being measured against it.

**close_position** = `(close − low) / (high − low)`

**bar_vwap** = `quote_volume / volume`

**vwap_position** = `(bar_vwap − low) / (high − low)`, clipped to `[0, 1]` for reporting but with pre-clip violations counted separately (see B3 validity).

**Degenerate bars** where `high == low`: an explicit branch. These bars fail any position-based gate and must be counted and reported, never allowed to produce NaN or a division by zero.

**Flat RVOL (current engine):** bar volume ÷ mean volume of the prior 20 bars.

**Session-normalised RVOL (B1 proposal):** bar volume ÷ median volume of the **same 15-minute slot of the UTC day** over the trailing `baseline_days` **completed prior days**. 96 slots per day. Bar `T`'s own day contributes nothing. Median, not mean. Warm-up of `baseline_days` before the first valid value.

**Causality is mandatory** and must be enforced structurally, not by convention: the slot baseline may only read strictly prior completed days. Write a test that fails if it can see the current day.

---

## Part 3 — Measurements

Report every result **per symbol and per year (2022, 2023) separately**, never pooled, unless a pooled figure is explicitly also requested.

### M1 — B3 validity check
Fraction of bars where `bar_vwap` lands inside `[low − 1 tick, high + 1 tick]`, using the tick in force at that bar's timestamp.

Report the fraction, the count and magnitude of violations, and the worst violations by absolute distance outside the band.

**Threshold (Section 13):** ≥ 99.99% required. Below that, `quote_volume` is unreliable and **both `vwap_position` and the quote denomination die.**

### M2 — B3 non-redundancy check
Pearson correlation between `vwap_position` and `close_position`, **on breakout bars only**.

Also report the same correlation on all bars, for context.

**Threshold:** `|rho| >= 0.90` KILL / `0.70 <= |rho| < 0.90` AMBER / `< 0.70` PASS.

### M3 — B3 dispersion check
On breakout bars: the full distribution of `vwap_position` — deciles, IQR, mean, median, and the fraction of bars at the extremes (`<= 0.05` and `>= 0.95`).

**Threshold:** IQR ≥ 0.15, and a threshold must exist rejecting 25–75% of breakout bars.

Note for the report: the second condition is near-vacuous for any continuous distribution, since the median always rejects ~50%. Report both, but state plainly that **the IQR is the operative test** and report whether the distribution is atomic (mass concentrated on few values) rather than continuous.

### M4 — B5 selectivity ratio
For flat RVOL at threshold 1.5:
- pass rate on **all bars**
- pass rate on **breakout bars**
- the ratio (breakout ÷ all)

**Threshold:** ratio ≥ 2.0 → selective but pre-spent by conditioning; ≤ 1.3 → never selective; between → inconclusive.

### M5 — Session-normalised RVOL characterisation
This is the measurement that decides what the B1 amendment is actually worth.

For `baseline_days` ∈ {5, 10, 20, 30}:
- the full distribution of session-normalised RVOL on breakout bars (deciles)
- **the threshold that reproduces the same pass rate as flat RVOL ≥ 1.5**, per symbol per year
- the selectivity ratio (breakout ÷ all bars) at that equivalent threshold, directly comparable to M4
- pass rate **by hour of UTC day**, flat baseline vs session-normalised, side by side

**Report these as characterisation, not as a choice.** Do not recommend a `baseline_days` value and do not pick a threshold — those are Point 4 sweep decisions. The purpose here is to establish what the parameter surface looks like.

Rationale to state in the report: the RVOL threshold 1.5 was calibrated against a flat 20-bar mean. Changing the denominator changes the distribution, so 1.5 no longer denotes the same selectivity. The equivalent-pass-rate threshold makes the two baselines comparable at matched selectivity, which is the only way to see whether session-normalisation buys anything beyond relabelling.

### M6 — B2 denomination stability
Compare trailing-window stability of `quote_volume` versus `volume` as the RVOL denominator. Use the coefficient of variation of the trailing baseline across the window as the stability statistic; state the definition used and why.

**Decision rule:** the more stable denomination must win in ≥ 2 of 3 symbols across both years, else default to `quote_volume`.

### M7 — F2 `rsi_lower` rejection rate
Fraction of breakout bars rejected by the RSI condition alone (`RSI(14) < 50` for longs, `> 50` for shorts).

Also characterise the rejected population: are those bars systematically different in ATR%, `close_position` or `vwap_position`? The 1R hypothesis is that they are **reversal breakouts** — the first break after a sustained decline — and therefore a qualitatively distinct animal from trend continuation.

**Threshold:** rejects < 5% → decorative, drops now; ≥ 5% → retained as a live arm.

### M8 — A2 derived stop floor, and ATR scale
Compute `stop_min_pct = max( N_cost × c_roundtrip , risk_usd / (E × L_max) )` with `N_cost = 6`, `c_roundtrip` = 0.12% plus the engine's configured slippage haircut on both sides, `risk_usd` = 20, `E` = 2000, `L_max` = 3.0. Show both terms and which dominates.

Then, per symbol per year, report the distribution of `ATR(14) as a percentage of close` on breakout bars — deciles, median.

From that, report **`m*` = the ATR multiplier at which median ATR% crosses the derived floor**, per symbol per year.

**Critical:** `m*` is reported here **for scale only**. Section 3 A6 requires that the operational `m*` be computed **per walk-forward training fold** at Point 4, never globally — a globally computed anchor would read the holdout. Say so explicitly in the report so this figure cannot later be mistaken for the operational anchor.

### M9 — Signal counts per gate arm
Count breakout bars, per symbol per year per direction, surviving each arm:
1. ungated
2. RVOL only (flat, ≥ 1.5)
3. `vwap_position` only — report as a curve across candidate thresholds rather than at one value
4. both conjunctively — again as a curve
5. with and without `rsi_lower`

**These are signal counts, not trades.** Do not simulate. State clearly that portfolio-mode occupancy would reduce these further, and that signal mode is the edge-test instrument.

Compare against the pre-committed evidence minimums — 200 in-sample, 50 out-of-sample, 30 per direction, **per symbol** — and state plainly where a conjunctive gate would fall short. **The evidence minimum does not move.**

---

## Constraints

- **Firewall.** No trade simulation. No P&L, expectancy, win rate, profit factor, Sharpe, return or equity figure. No aggregate of `net_pnl` or `r_multiple`. If a measurement cannot be produced without touching those, stop and report it as blocked.
- **Window.** 2022–2023 only. Do not load or reason about 2024–2026 anywhere.
- **Do not modify `src/engine/`, `config/` or `data/`.** New analysis code lives in `src/analysis/`.
- **Do not implement any 1R amendment.** This pass measures; Point 3R builds.
- **Do not adjust any Section 13 threshold**, and do not add commentary proposing they be revisited now that data has been seen.
- Reuse the engine's existing indicator implementations where they exist. If you must reimplement anything, say which and why, and test it against the engine's version.
- Report per symbol per year. Do not pool unless also asked for pooled.
- Manifest integrity check before reading any data, as elsewhere in this repo.
- If a result is ambiguous or a definition underspecified, **flag it in the report — do not resolve it yourself**.

## Verification

- Tests for the new analysis code, at minimum: slot-baseline causality (must fail if it can see the current day); degenerate-bar handling (`high == low`); `vwap_position` clipping and violation counting; agreement of the breakout-bar definition with the engine's own EMA/Donchian conditions.
- The full existing test suite still passes.
- Confirm no file under `src/engine/`, `config/` or `data/` appears in `git status`.
- Grep the report for forbidden terms (`expectancy`, `win rate`, `profit`, `Sharpe`, `equity curve`, `net_pnl`, `r_multiple`) and confirm no measured value of any of them appears.
- Commit in a single commit: `analysis: structural measurement pass (1R pre-checks)`

## Report back

Write `reports/07_structural_pass.md` containing:

1. File tree, commit hash, test counts.
2. Manifest check result.
3. **A decision table at the top**: for each of M1, M2, M3, M4, M6, M7 — the measured value, the pre-committed threshold, and the resulting verdict (PASS / AMBER / KILL / INCONCLUSIVE), per symbol per year. This table is the deliverable; everything else is supporting detail.
4. Full detail for M1–M9 in order.
5. The three documentation corrections (C1–C3), with confirmation of what changed.
6. Anything ambiguous, underspecified or surprising — flagged, NOT resolved.
7. Explicit confirmation that no trade was simulated, no forbidden figure computed, and no data outside 2022–2023 was read.

Write the report to the file. Do not print it in the chat — confirm the path and line count only.
