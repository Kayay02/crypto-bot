# Handoff 04 — Opening Point 1R (Strategy Amendment Pass)

> **RECONSTRUCTED AFTER THE FACT from the Point 1R record.** This document was never filed contemporaneously — `docs/handoff/` contained only `.gitkeep` before commit `0da9d11`. It is reconstructed from `docs/handoff/05_point_1r.md` and the Point 1R report so the record is complete. It is **not** a contemporaneous artifact and must not be cited as one.

---

## 1. Status at the Time

- **Point 1 (strategy)** — closed.
- **Point 2 (data)** — closed.
- **Point 3 (backtesting engine)** — closed. Two-layer custom design at commit `106cb42`, 88 tests passing.
- **Point 1R** — opened here as an **amendment pass on the strategy design**, not a new point of work. Point 3's structural diagnostics surfaced four mechanical facts about the Point 1 strategy that could not be left standing.

---

## 2. The Performance Firewall (standing rule)

No performance figure is to be computed, displayed or estimated while the firewall is in force.

**Allowed:**

- Exit-reason counts.
- Filter pass rates.
- Binding rates of floors and caps.
- Holding-time distributions.
- Trade counts.
- Provenance counters.
- Logical entailments between rules.

**Not allowed:**

- Expectancy.
- Win rate as a P&L claim.
- Profit factor.
- Sharpe.
- Equity curves.
- Total return.
- Any aggregate of the `net_pnl` or `r_multiple` columns.

The engine **already writes per-trade P&L to disk**. It is not to be aggregated. The firewall is a discipline about what is looked at, not about what exists on disk.

**It lifts only by deliberate decision at the start of Point 4, after the validation design is pre-registered.**

*Noted limitation:* exit-reason counts are performance-**adjacent** — a target:stop ratio implies a win rate. This is accepted as the price of having engine diagnostics at all. It is **not** to be extended further.

---

## 3. The Four Mechanical Findings That Caused 1R

**Finding 1 — Cooldown is a logical no-op.**
A long entry requires close above the Donchian-20 upper band, which IS a new 20-bar high. The condition that clears the cooldown is entailed by the entry condition that triggers it. It can never bind.

**Finding 2 — The ATR stop is overridden by its own 1.0% floor.**
The floor binds on 64.8% of 2022 trades and 81.1% of 2023 trades; BTC 2023 = 99.3%. The 3.5% cap essentially never binds. **Knock-on effect:** BTC and ETH effectively run a fixed-percent stop while SOL (floor binds 40–59%) runs a volatility-scaled one. They are not running the same strategy, which weakens both the shared-parameter justification and the two-of-three rule.

**Finding 3 — The volume gate is weak.**
RVOL >= 1.5 admits 65.9% (2022) and 68.8% (2023) of breakout bars. Its effect on the target-vs-stop ratio was +0.6pp in 2022 and −0.9pp in 2023 — the sign flips.

**Finding 4 — The most common outcome is neither target nor stop.**
Time-stop exits were 26.5% (2022) and 43.3% (2023); target exits 21.3% / 14.9%. The original "36% win rate at 1:2 to break even" framing assumed binary resolution and does not describe this population.

---

## 4. The Contamination Ledger

2022 and 2023 have been used for **structural diagnostics**. Reshaping the strategy using them spends some of their independence.

This is a much weaker form of contamination than fitting to returns — structural facts (binding rates, pass rates, exit-reason mixes) do not reveal which direction the money went — but it is **not zero**. Point 4 should treat 2022–23 as **partially used** and lean on 2024 and the 2025–26 holdout for real evidence.

**The 2025–26 holdout remains entirely untouched.**

---

## 5. The Governing Rule for 1R

> Every amendment must be justified by a **mechanical fact** — a binding rate, a pass rate, a logical entailment — **never** by "this improves the numbers", because the numbers have not been seen.

This is what makes an amendment pass under a firewall coherent rather than blind tinkering.

---

## 6. The 1R Agenda As Opened

- **1R.1 — Stop geometry.** The floor is overriding the mechanism it was meant to guard.
- **1R.2 — Volume gate selectivity.** RVOL >= 1.5 admits roughly two-thirds of breakout bars.
- **1R.3 — Time stop.** The most common exit was never given a declared purpose.
- **1R.4 — Restate the edge claim in expectancy terms.** The win-rate framing describes a minority subpopulation.

**1R.5 (RSI) was added during the pass.** Reason: the D5 single-pass drop rule means any component not registered as an attribution arm **before the firewall lifts** can never be examined later without becoming the iterative search that D5 bans. RSI was still in the baseline and unregistered, so it had to be opened now or never.

---

## 7. Working Rules

- **One point at a time.** No jumping ahead.
- **Decisions before code.** A point closes on a written decision record, not on a passing test.
- **No code is written in chat.** Claude Code receives self-contained prompts.
- **Handoffs, prompts and reports are versioned in the repo** — `docs/handoff/`, `docs/prompts/`, `reports/`.

---

## 8. Next

Point 1R proceeds through 1R.1 – 1R.5. Its output is `docs/handoff/05_point_1r.md`. The next open point after 1R closes is **Point 4 — validation design pre-registration**, at whose start the performance firewall lifts.
