# Claude Code Prompt — 1R Errata and Handoff Backfill

> Paste everything below the line into Claude Code in VS Code.

---

## Goal

Amend the Point 1R handoff to close eight review flags, and backfill the missing session handoff #04. Documentation only.

## Context

Systematic algorithmic trading bot, Bitget USDT-M perpetual futures, BTC/ETH/SOL, 15-minute candles, ~$2,000 account.

Points 1 (strategy), 2 (data) and 3 (engine, commit `106cb42`, 88 tests passing) are closed. Point 1R — a strategy amendment pass — was filed at commit `0da9d11` in `docs/handoff/05_point_1r.md`, together with `reports/05_point_1r_handoff.md`.

That report flagged eight internal inconsistencies without resolving them, per its instructions. All eight have now been reviewed and resolved. This task records the resolutions.

A **performance firewall** is in force: no profit, loss, expectancy, win-rate, Sharpe, profit-factor or equity figure may be computed, displayed or estimated. It lifts only at the start of Point 4, after the validation design is pre-registered. Nothing in this task goes near it.

## Files

Create:
- `docs/handoff/04_point_1r_opening.md` — backfill of session handoff #04
- `docs/prompts/06_1r_errata.md` — this prompt, verbatim

Modify:
- `docs/handoff/05_point_1r.md` — apply the amendments below

Create:
- `reports/06_1r_errata.md` — completion report

Touch nothing else. In particular, do not modify any file under `src/`, `tests/`, `config/` or `data/`.

---

## Requirements

### Part A — New section in `docs/handoff/05_point_1r.md`

Insert a new section **"Section 13 — Errata and Numeric Kill Thresholds (resolved review flags)"** at the end of the document, before nothing. Do not renumber or rewrite existing sections except where Part B explicitly requires it.

State at the top of the section: these thresholds were fixed **before** the structural measurement pass was run, so that a measurement cannot be interpreted against a threshold chosen after seeing it.

#### A1 — Numeric kill thresholds for the structural checks

The 1R.2 and 1R.5 pre-checks were specified qualitatively ("very high", "clusters tightly", "rejects almost nothing"). Deciding those cuts after seeing the measurements would be threshold-shopping. The cuts are therefore fixed now:

**B3 validity check** — `bar_vwap = quote_volume / volume` must land within `[low − 1 tick, high + 1 tick]` on **at least 99.99% of bars**, per symbol per year. The one-tick tolerance allows floating-point and tick-rounding noise and nothing else. FAIL ⇒ Bitget's `quote_volume` is unreliable ⇒ **both B3 (vwap_position) and B2 (quote denomination) die.**

**B3 non-redundancy check** — Pearson correlation between `vwap_position` and `close_position = (close − low) / (high − low)`, measured on breakout bars only, per symbol per year:
- `|rho| >= 0.90` → **KILL.** 81% shared variance; vwap_position is a relabelled price-action term.
- `0.70 <= |rho| < 0.90` → **AMBER.** Proceed, but the redundancy is recorded and reported in every result that uses the gate.
- `|rho| < 0.70` → **PASS.**

**B3 dispersion check** — on breakout bars, both must hold:
- interquartile range of `vwap_position` **>= 0.15**, and
- there must exist a threshold rejecting between **25% and 75%** of breakout bars.

FAIL ⇒ nothing to discriminate with ⇒ B3 dies.

**F2 `rsi_lower` check** — rejection rate on breakout bars, per symbol per year:
- rejects **< 5%** → decorative; drops now, before the build, without consuming an attribution arm.
- rejects **>= 5%** → retained as a live arm under the D5 single-pass drop rule.

Rationale: 5% of the 200-trade in-sample minimum is 10 trades, below any power to detect anything.

**B5 selectivity ratio** — (pass rate on breakout bars) ÷ (pass rate on all bars), per symbol per year:
- ratio **>= 2.0** → RVOL is genuinely selective, but its selectivity was **pre-spent by conditioning** on the breakout.
- ratio **<= 1.3** → RVOL >= 1.5 was **never selective**; the gate as originally specified was decoration.
- between 1.3 and 2.0 → inconclusive; the gate stays pending the B4 four-arm attribution.

**B2 denomination decision rule** — the more stable denomination must win in **at least 2 of 3 symbols across both years**. Otherwise default to `quote_volume`. This mirrors the pre-committed two-of-three rule rather than inventing new arbitration.

#### A2 — B4 sample-size arithmetic corrected

The recorded figure `~66% x ~50% = ~33%` used an invented 50% pass rate for `vwap_position`, which has no threshold set and therefore no measured pass rate. Replace with the design range: RVOL ~66% × vwap_position 25–75% ⇒ **joint survival band of 16%–50% of breakout bars**.

The pre-committed resolution order if evidence minimums cannot be met is unchanged: loosen thresholds → extend the in-sample window → drop to a single condition. **The evidence minimum (200 IS / 50 OOS / 30 per direction, per symbol) is not on that list and does not move.**

#### A3 — Risk denomination: fixed dollar risk is authoritative

Sections 8 and 10 state "$20 risk per trade" and "1% risk after costs". These agree at exactly $2,000 equity and diverge as equity moves. Resolution:

**`risk_usd` is FIXED at $20 for all backtesting and validation. Percent-of-equity sizing is deferred to Point 7 as a live-deployment decision.**

Rationale — this is a measurement argument, not a risk-appetite one. If R floats with equity, an early winner enlarges every subsequent R, and a trade's contribution to expectancy depends on *when in the sequence it occurred*. Expectancy per trade would stop being a property of the strategy and become a property of the ordering, corrupting the metric 1R.4 was written to define. Fixed R keeps every trade commensurable. Compounding is a deployment question and belongs where it can be tested against a real equity curve.

#### A4 — Symbol collision: `R` resolved

`R` currently denotes both dollar risk (in A2's floor formula) and the risk multiple (in "+2R", "0.05R"). Fix the notation throughout the document:

- **`risk_usd`** — the fixed dollar risk per trade ($20).
- **`R`** — reserved exclusively for the risk multiple.

A2's derived floor formula is restated as:

```
stop_min_pct = max( N_cost * c_roundtrip , risk_usd / (E * L_max) )
```

with symbols declared explicitly: `c_roundtrip` = round-trip cost on the stop path (taker in, taker out = 0.12% before slippage, plus the engine's slippage haircut both sides); `N_cost` = cost-dominance ratio, proposed at 6; `E` = account equity; `L_max` = maximum leverage (3.0). The leverage term evaluates to `$20 / ($2,000 × 3.0)` = 0.333%.

#### A5 — The Guard Rail Principle is BINDING, not rationale

Record its status explicitly. It has already been applied to kill two proposals (a volatility-relative floor in 1R.1, and `rsi_upper` in 1R.5), so it functions as a rule regardless of how it was labelled. State it as:

> **Guard Rail Principle (binding).** A guard rail must be denominated in a different unit from the mechanism it guards. Percent-of-price guarding an ATR-scaled stop is coherent. ATR guarding ATR is a logical no-op — it is either always inert or always binding, never conditionally binding. Any future guard rail proposal must state its denomination and that of the mechanism it guards.

#### A6 — Naming identity stated

`checkpoint_bars` in the D4 pace-factor formula and `time_stop_bars` in D3 are the **same quantity under two names**. State the identity explicitly and use `time_stop_bars` as the canonical name.

#### A7 — Amendment counts corrected

Section headings state amendment counts that do not match their contents. Correct the headings to match what is enumerated:

- 1R.1 — **seven** amendments (A1–A7), plus the Guard Rail Principle stated separately as a binding rule.
- 1R.2 — B0 (contamination ledger update) plus **five** amendments (B1–B5).
- 1R.4 — a defect statement, reconciliation, decomposition and structural prediction, plus **six** amendments (E1–E6).

No decision content changes; labels only.

### Part B — Apply A3, A4 and A6 in place

Section 8 (Baseline Strategy After 1R) and Section 10 (What Must Not Change) currently carry the ambiguous risk phrasing. Update both to use `risk_usd = $20 (FIXED)` and note that percent-of-equity is deferred to Point 7. Apply the `R` / `risk_usd` notation fix wherever the collision occurs. Apply the `checkpoint_bars` → `time_stop_bars` canonicalisation.

**Do not change any other decision content anywhere in the document.** If applying these edits appears to require altering a decision, stop and flag it in the report instead.

### Part C — Backfill `docs/handoff/04_point_1r_opening.md`

`docs/handoff/` contained only `.gitkeep` before commit `0da9d11`, so handoff #04 — the document that opened Point 1R — was never filed. Reconstruct it from the material below. Mark it clearly at the top as **reconstructed after the fact from the Point 1R record**, so it is not mistaken for a contemporaneous artifact.

It must contain:

**Status at the time:** Points 1, 2 and 3 closed. Point 1R opened as an amendment pass on the strategy design.

**The performance firewall**, stated as a standing rule:
- Allowed: exit-reason counts, filter pass rates, binding rates of floors and caps, holding-time distributions, trade counts, provenance counters, logical entailments between rules.
- Not allowed: expectancy, win rate as a P&L claim, profit factor, Sharpe, equity curves, total return, any aggregate of the `net_pnl` or `r_multiple` columns.
- The engine already writes per-trade P&L to disk. It is not to be aggregated.
- Lifts only by deliberate decision at the start of Point 4, after the validation design is pre-registered.
- Note: exit-reason counts are performance-*adjacent* — a target:stop ratio implies a win rate. Accepted as the price of engine diagnostics; not to be extended further.

**The four mechanical findings that caused 1R** (already recorded in Section 2 of `05_point_1r.md` — reproduce them consistently):
1. Cooldown is a logical no-op — the condition clearing it is entailed by the entry condition triggering it.
2. The ATR stop is overridden by its own 1.0% floor (binds 64.8% of 2022 trades, 81.1% of 2023; BTC 2023 = 99.3%). Knock-on: BTC/ETH effectively run a fixed-percent stop while SOL (40–59%) runs a volatility-scaled one — they are not running the same strategy, weakening both the shared-parameter justification and the two-of-three rule.
3. The volume gate is weak — RVOL >= 1.5 admits 65.9% (2022) and 68.8% (2023) of breakout bars; effect on the target-vs-stop ratio was +0.6pp then −0.9pp, sign flipping.
4. The most common outcome is neither target nor stop — time-stop exits 26.5% (2022) and 43.3% (2023) versus target exits 21.3% / 14.9%.

**The contamination ledger:** 2022 and 2023 have been used for structural diagnostics. Reshaping the strategy using them spends some of their independence. This is a much weaker form of contamination than fitting to returns — structural facts do not reveal which direction the money went — but it is not zero. Point 4 should treat 2022–23 as partially used and lean on 2024 and the 2025–26 holdout for real evidence. The 2025–26 holdout remains entirely untouched.

**The governing rule for 1R:** every amendment must be justified by a mechanical fact — a binding rate, a pass rate, a logical entailment — never by "this improves the numbers", because the numbers have not been seen.

**The 1R agenda as opened:** 1R.1 stop geometry, 1R.2 volume gate selectivity, 1R.3 time stop, 1R.4 restate the edge claim in expectancy terms. Record that 1R.5 (RSI) was added during the pass, because the D5 single-pass drop rule means any component not registered as an attribution arm before the firewall lifts can never be examined later without becoming the iterative search that D5 bans.

**Working rules:** one point at a time; decisions before code; no code written in chat — Claude Code receives self-contained prompts; handoffs, prompts and reports are versioned in the repo.

---

## Constraints

- Documentation only. No code, test, config or data file may be created, modified or deleted.
- No parameter value anywhere in the repo changes. This records decisions; implementing them is Point 3R.
- Do not run any backtest, sweep, data pull or analysis script.
- The performance firewall is in force. Compute, display or estimate no profit, loss, expectancy, win-rate, Sharpe, profit-factor or equity figure.
- Do not weaken, soften or reinterpret any pre-committed kill condition. They are reproduced in Section 10 and must remain verbatim.
- The numeric thresholds in A1 are **fixed before measurement, deliberately**. Do not adjust them for plausibility, and do not add commentary suggesting they be revisited after data is seen.
- If anything above appears internally inconsistent, flag it in the report — do not resolve it yourself.

## Verification

- All four files exist at the stated paths.
- `docs/handoff/05_point_1r.md` contains Sections 1–13, in order, with 1–12 otherwise unchanged apart from the Part B edits.
- Every threshold in A1 appears with an explicit numeric cut — no qualitative language ("very high", "tightly", "almost nothing") survives in the decision rules.
- The pre-committed kill conditions in Section 10 are unchanged and unweakened.
- `git status` shows only the four intended files as added or modified.
- `git diff` on `05_point_1r.md` touches only Sections 8, 10, the amendment-count headings, the `R` / `risk_usd` notation, the `checkpoint_bars` canonicalisation, and the new Section 13.
- Commit all changes in a single commit: `docs: 1R errata — numeric kill thresholds, risk denomination, handoff 04 backfill`

## Report back

Write `reports/06_1r_errata.md` containing:

- File tree of created and modified files with line counts.
- Commit hash from `git rev-parse HEAD`.
- `git status` after the commit.
- The full `git diff --stat` for the commit.
- A list of every edit made to `05_point_1r.md`, section by section, confirming no decision content changed beyond the eight resolved flags.
- Confirmation that all six threshold groups in A1 carry numeric cuts.
- Any internal inconsistency, ambiguity or missing information noticed while writing — flagged, NOT resolved.
- Confirmation that no code, test, config or data file was touched, and that the performance firewall was not breached.
