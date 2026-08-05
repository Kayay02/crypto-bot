# Claude Code Prompt — Point 3R: Engine Amendment

> Paste everything below the line into Claude Code in VS Code.

---

## Goal

Bring the backtesting engine into line with the Point 1R strategy design and the structural pass outcomes. Two 1R amendments died on measurement, one stood, and one specification error was corrected — this pass implements what survived and removes what did not.

## Context

Systematic algorithmic trading bot. Bitget USDT-M perpetual futures, BTC/ETH/SOL, 15-minute candles, ~$2,000 account, `risk_usd` fixed at $20 per trade net of costs.

The engine is at commit `106cb42` and **still implements the pre-1R design**. The structural measurement pass (`reports/07_structural_pass.md`, commit `de4b8d0`) has since resolved four open questions. This pass implements them.

Decision record: `docs/handoff/05_point_1r.md` (Sections 1–13, ER1–ER7 in Section 13).

**The performance firewall remains in force.** It lifts only at the start of Point 4, after the validation design is pre-registered. This pass writes code and runs fixtures; it does **not** compute, display or estimate any profit, loss, expectancy, win rate, profit factor, Sharpe, return or equity figure, and takes no aggregate of the `net_pnl` or `r_multiple` columns. Fixture P&L is permitted because fixture answers are known by construction.

**Do not run a parameter sweep, a full backtest, or any real-data run beyond the single smoke test specified below.**

### The four rulings being implemented

1. **`vwap_position` (B3) is DEAD — permanently, not as a labelled variant.** Killed on three independent mechanical grounds: the gate is applied directionally so the population a threshold sees is per-direction (directional IQR 0.089–0.126 against a 0.15 cut, 6/6 fail); the median sits at 0.55–0.58 on essentially every breakout bar, making it a constant rather than a discriminator; and with IQR ~0.10 any usable threshold sits in the densest part of the distribution, so classification would be noise-dominated. **Do not implement it. Do not add it as a diagnostic column.** Reviving it later would be the iterative search that D5 bans.
2. **`rsi_lower` (F2) DROPS.** Zero rejections in 11,711 breakout bars; minimum RSI on any long breakout bar over two years was 54.18. `rsi_upper` was already removed by F3. **RSI leaves the strategy entirely.** The original brief asked for an oscillator; evidence removed it. Do not reintroduce one.
3. **Session-normalised RVOL (B1) STANDS.** Its registered rationale is confirmed: under the flat baseline the gate's pass rate on breakout bars swings 32–51 percentage points by hour of UTC day, and session-normalisation compresses that in 5 of 6 cells.
4. **`c_roundtrip` uses the engine's actual cost structure**, not "haircut on both sides". Entry slippage is deliberately zero (the 1m-close fill convention absorbs latency); the stop-market haircut applies on the stop leg only.

---

## Files

Create:
- `docs/handoff/06_structural_outcome.md` — the decision record for this pass
- `docs/prompts/08_point_3r.md` — this prompt, verbatim
- `reports/08_point_3r.md` — the report

Modify:
- `src/engine/signals.py`, `src/engine/simulate.py`, `src/engine/costs.py`, `src/engine/run.py` as required
- `src/engine/README.md`
- `tests/` as required

Do not modify `data/`. Do not modify `src/analysis/`.

---

## Part 1 — Decision record

Write `docs/handoff/06_structural_outcome.md`. **Do not rewrite `05_point_1r.md` to hide that B3 was once alive** — the record should show what was proposed, what was measured, and what survived. Append; do not revise history.

It must contain: the four rulings above with their mechanical justification; the resulting baseline strategy with every parameter marked DERIVED, FIXED or UNSET; the note that Finding 3's recorded pass rates (65.9% / 68.8%) do not reproduce (this pass measured ~70.6% / ~74.0%) and that the discrepancy is most likely a denominator difference — Finding 3's provenance is unrecorded, so **its specific numbers must not be quoted forward**, though its conclusion (the gate is weak) is unaffected; the note that removing `rsi_upper` returns roughly 27% of breakout bars to the population, and specifically the highest-momentum ones; the note that the 1R.5 reversal-breakout hypothesis is **unexercised, not refuted**; and a new standing rule: **every pre-committed threshold must carry its aggregation rule**, defaulting to the Section 10 two-of-three pattern unless stated otherwise. ER1's omission of one nearly decided B3 by accident.

---

## Part 2 — Layer A changes

### 2.1 RVOL baseline — session-normalised

Replace the flat 20-bar trailing mean.

- **Slot** = position within the UTC day; **96 slots** at 15m.
- **Baseline(T)** = **median** of the same slot over the trailing `baseline_days` **completed prior days**. Bar `T`'s own day contributes nothing.
- Median, not mean: a single event bar would inflate a mean and suppress RVOL for that slot every day for the rest of the window.
- **Denomination: `quote_volume`** for both numerator and denominator (M6 verdict, 3 of 3 symbols). They must always use the same field — assert it.
- Warm-up of `baseline_days` before the first valid signal; bars inside warm-up produce no signal and are counted.
- **Causality is structural, not conventional.** The baseline may only read strictly prior completed days. Write a test that fails if it can see the current day, and keep the existing `assert_causal` / `assert_causal_indicators` guards applied to it.

`src/analysis/structural_pass.py` already contains a working session-baseline implementation. **Import or move it rather than reimplementing** — two independent implementations that must agree is a defect waiting to happen. If you move it, `src/analysis` must import from `src/engine`, never the reverse.

Note for the report: `baseline_days` sensitivity is close to flat (the selectivity ratio moves by less than 0.5 across 5 → 30, non-monotonically), so a Point 4 sweep should not spend much resolution on it.

### 2.2 RSI removed from entry logic

RSI is no longer an entry condition. Keep `rsi_wilder` available and record `rsi` as an informational column on signal rows, but **no entry condition may read it**. Add a test asserting that changing the RSI value on a bar does not change whether that bar produces a signal.

### 2.3 Cooldown

Remove the new-20-bar-extreme rule entirely — it is a proven logical no-op (a long entry requires a close above the Donchian-20 upper, which *is* a new 20-bar high, so the clearing condition is entailed by the triggering condition).

**Retain `cooldown_bars`, default 0.** It was registered before the firewall as a sweep dimension; at 0 it is behaviourally inert, so the baseline is unchanged. Deleting it now would make it untestable later without violating D5. When positive it blocks re-entry in that symbol and direction for N bars after a stop-out. Flag in the report if you think this reasoning is wrong.

### 2.4 Entry conditions after 3R

Long, on a closed 15m bar: `EMA20 > EMA50` **and** `close >` Donchian-20 upper **and** session-normalised RVOL `>= rvol_threshold`. Short is the symmetric inverse. That is the whole entry rule. No RSI, no `vwap_position`, no cooldown condition.

---

## Part 3 — Stop geometry

### 3.1 `stop_atr_mult` is a first-class parameter with NO default

The value 1.5 is void. It carries no privileged status. **The parameter must have no default value at all** — if it is not explicitly supplied, config loading must raise. A silent fallback to a stale placeholder is exactly the failure this pass exists to correct.

Apply the same treatment to `stop_max_pct`, `rvol_threshold` and `baseline_days`: **no defaults, must be supplied, raise if absent.**

### 3.2 `stop_min_pct` is DERIVED, never chosen

```
stop_min_pct = max( N_cost * c_roundtrip , risk_usd / (E * L_max) )
```

- `N_cost` = 6 (the one chosen number; shared across symbols)
- `c_roundtrip` = entry taker + stop taker + stop-market haircut = 0.06% + 0.06% + `stop_haircut_bps`
  → **0.17% BTC/ETH** (5 bps), **0.22% SOL** (10 bps)
- `risk_usd` = 20, `E` = 2000, `L_max` = 3.0 → leverage term **0.3333%**

Resulting floors: **1.020% BTC/ETH, 1.320% SOL.** The cost term dominates by 3.06–3.96×.

The floor is therefore **per-symbol because its inputs are per-symbol**, not because it was tuned per symbol. `N_cost` is the shared parameter. Compute it from config at load time; do not hardcode 1.020 or 1.320.

Keep the leverage term in the formula even though it is nowhere near binding, so that any future downward revision of `N_cost` cannot silently make it load-bearing without anyone noticing.

### 3.3 `stop_max_pct` — two jobs, separated

A5 re-derived the cap as a **target-plausibility and exchange-minimum guard rail**, explicitly *not* loss limitation (with fixed `risk_usd`, a wider stop means a smaller position, so dollar risk is constant by construction).

Implement these as **two separate mechanisms**, per the Guard Rail Principle (a guard rail must be denominated in a different unit from the mechanism it guards):

1. **`stop_max_pct`** — a percent-of-price cap on stop distance. No default; must be supplied.
2. **Minimum order quantity rejection** — a separate, explicit check against Bitget's minimum order quantity for that symbol, rejecting the trade loudly rather than by silent rounding. Denominated in quantity, not percent.

If Bitget's minimum order quantity is not already in `config/contracts_cache.json`, probe the contracts endpoint for it and cache it alongside the tick schedule, using the same probe-and-verify discipline. Report what you find.

### 3.4 New provenance counters

- **Per trade:** `stop_binding_mechanism` ∈ {`atr`, `floor`, `cap`}
- **Per trade, portfolio mode:** `size_binding_mechanism` ∈ {`risk_rule`, `leverage_cap`, `min_qty`}

The second closes a Point 3 known gap (`max_leverage` = 3.0 was never measured) and detects divergence between signal mode and portfolio mode.

---

## Part 4 — Time stop

### 4.1 Bar counts are DERIVED from the Donchian period

```
time_stop_bars = tau * donchian_period      tau = 1.0  ->  20 bars
max_hold_bars  = 2 * donchian_period                  ->  40 bars
```

**The previous values 16 and 48 are void.** Only `tau` remains sweepable, over a narrow band around 1.0. `max_hold_bars` is not independently sweepable.

Rationale for the README: at bar 20 post-entry every bar in the Donchian lookback is post-breakout — the 20-bar high that was broken has rolled out of the window, so the reference frame that generated the signal no longer exists.

Retain the existing assertion that `max_hold_bars > time_stop_bars`, and the guarantee that the 1m walk buffer can never itself terminate a trade (`walk_end` must remain unreachable; data exhaustion is `insufficient_data`).

### 4.2 The checkpoint threshold is an OUTPUT, not an input

```
phi = (threshold_R / target_R) / (time_stop_bars / max_hold_bars)
```

`phi` = 1.0 (linear pace) is the default and **the only free parameter here**. With `target_R` = 2, `time_stop_bars` = 20, `max_hold_bars` = 40, this solves to `threshold_R` = 1.0.

Implement `threshold_R` as **derived from `phi`**, not supplied. The old geometry implied `phi` = 1.5 — demanding 50% of the price journey in 33% of the time budget — which nobody chose; it fell out of two unrelated placeholders. Front-loading (`phi` > 1) is a real momentum-decay claim and must be discovered by a sweep, not assumed.

### 4.3 STATE CHECK, not latch — this changes existing behaviour

At the **close of 15m bar `time_stop_bars` after entry**, evaluate whether the trade **is currently at or above `threshold_R`, net of costs**. This is a state check ("is it at +threshold now"), **not** a latch ("did it ever touch +threshold").

**This supersedes the Point 3 decision to measure +1R by intrabar 1m touch.** Reasons, for the README: a wick to +1R that immediately retraces is a liquidity-vacuum failure, not a healthy trade; the rule stays in Layer A's 15m world with no 1m dependency; and it carries no latch state. Accepted cost: a trade that ran to +1.8R and retraced to +0.9R gets cut while in profit.

Below threshold at the checkpoint → exit, executed at the close of the first 1m bar of the next 15m bar, taker, `exit_reason = "time_stop"`.
At or above threshold → the trade continues to stop, target, or `max_hold_bars`.

`threshold_R` must be solved **net of costs**, using the taker fee on the exit side (conservative — a continuing trade exits by stop, target or max-hold). Round to tick, away from the position.

### 4.4 `NO_TIME_STOP` counterfactual arm

Register a configuration flag disabling the time stop entirely, so the D5 leave-one-out drop pass can measure it. Not baseline.

---

## Part 5 — Unchanged, do not relax

- `open_synth` is never read. No 1m volume. No 1m open. No indicator reads 1m data.
- Entry fill = 1m close of the first minute of bar `T+1`. Entry slippage 0.
- Take-profit requires trade-through at target + 1 tick (maker). Stop fills at level ∓ haircut (taker). All rounding away from the position.
- Target solved net of costs. Closed-form cost-inclusive sizing.
- Two modes: **signal mode** (no position/cooldown/margin limits; one ungated simulation, gated arm obtained by filtering the same trade table) and **portfolio mode**. Both share Layer B.
- Provenance counters: resolved-by-observation / decided-by-assumption / tp-touched-not-filled / stop-fill-quality-unresolved / flagged-bar-overlap.
- The 425 reconstruction-divergence bars are flagged, never excluded.
- Manifest SHA256 integrity check enforced.
- Funding is never an input to trade logic and no funding cost is applied.
- `risk_usd` = $20 FIXED. `R` denotes the risk multiple only.

---

## Part 6 — Tests

All existing tests must still pass or be deliberately updated with the reason recorded. New fixtures required:

- Session baseline reads only strictly prior completed days (fails if it can see the current day)
- Session baseline uses median, not mean — a single extreme bar in the window does not move it proportionally
- Warm-up produces no signals and is counted
- Numerator and denominator always use the same volume field
- Changing RSI on a bar does not change whether it signals
- `stop_atr_mult`, `stop_max_pct`, `rvol_threshold`, `baseline_days` each raise if not supplied
- Derived `stop_min_pct` matches hand arithmetic for both cost structures (1.020% / 1.320%)
- `stop_binding_mechanism` correctly identifies atr / floor / cap
- `size_binding_mechanism` correctly identifies risk_rule / leverage_cap / min_qty
- `threshold_R` derives correctly from `phi`; `phi` = 1.5 reproduces the old +1R-at-bar-16 geometry
- **State check vs latch:** a trade that touches +1R intrabar but closes below it at the checkpoint **is time-stopped** (this is the behavioural change — pin it)
- A trade at exactly `threshold_R` at the checkpoint continues (boundary)
- `time_stop_bars` = 20 and `max_hold_bars` = 40 derive from `donchian_period`
- `walk_end` remains unreachable
- `NO_TIME_STOP` disables the checkpoint and nothing else
- `cooldown_bars` = 0 is inert; = 3 blocks for exactly 3 bars
- Signal mode and portfolio mode remain byte-identical for a single isolated trade
- The planted look-ahead tests still catch both leaks

**Golden files.** Both will change — every rule changed. Regenerate deliberately and report **old hash, new hash, and which rule change accounts for the delta**. Also create the **signal-mode golden file** that Point 3 left as a known gap.

---

## Part 7 — Smoke test only, no real-data analysis

The engine cannot run without `stop_atr_mult`, and choosing it is a Point 4 sweep decision. So:

- Run **one** smoke test on a short slice (a single symbol, one month, 2023) with an **explicitly arbitrary** multiplier, labelled as such in both the code and the report.
- Report only: the pipeline executed end to end, the number of signals, the number of trades, and confirmation that every provenance counter populated.
- **Do not report distributions, binding rates, exit-reason mixes, holding times or any other diagnostic from this run**, and do not draw any conclusion from it. Its only purpose is to prove the pipeline runs.

---

## Constraints

- Performance firewall in force. No P&L, expectancy, win rate, profit factor, Sharpe, return or equity figure. No aggregate of `net_pnl` or `r_multiple`. Fixture P&L only.
- No parameter sweep, no full backtest, no run beyond the Part 7 smoke test.
- Do not touch `data/`. Do not read or reason about 2024–2026 data.
- Do not reintroduce `vwap_position`, RSI as a gate, or the 20-bar-extreme cooldown.
- Do not restore a default for any of the four no-default parameters.
- Do not rewrite `docs/handoff/05_point_1r.md` to hide superseded proposals.
- If anything above is ambiguous or appears internally inconsistent, **flag it in the report — do not resolve it yourself.**

## Verification

- Full test suite passes; report counts.
- Confirm no entry condition reads RSI, and no code path references `vwap_position`.
- Confirm each of the four parameters raises when absent.
- Confirm `walk_end` is unreachable.
- Grep the report for forbidden terms and confirm no measured value of any appears.
- Single commit: `engine: Point 3R amendment — session RVOL, derived stop floor, derived time stop, RSI removed`

## Report back

Write `reports/08_point_3r.md`. Do not print it in chat; confirm path and line count only.

```
1. FILE TREE + commit hash + test counts
2. WHAT CHANGED — one short paragraph per part (2 through 4)
3. TEST RESULTS — itemised, every new fixture listed individually
4. FULL TRACE — one trade exercising the STATE CHECK path: touches
   +1R intrabar, closes below threshold at the checkpoint, is time-stopped.
   Show the derived threshold_R solve, the checkpoint evaluation, and the
   fee math. Do not truncate.
5. DERIVED VALUES — stop_min_pct per symbol with both terms shown;
   time_stop_bars, max_hold_bars, threshold_R with their derivations
6. GOLDEN FILES — old hash, new hash, explanation of the delta, plus the
   new signal-mode golden file
7. MINIMUM ORDER QUANTITY — what was found, and how it was verified
8. SMOKE TEST — pipeline ran, signal count, trade count, counters populated.
   Nothing else.
9. AMBIGUITIES, DEVIATIONS AND DISAGREEMENTS — state disagreements, do not
   silently comply
10. WHAT IS NOT DONE
```
