# Report 06 — 1R Errata and Handoff Backfill

Documentation-only pass. Eight review flags raised in `reports/05_point_1r_handoff.md` are now resolved and recorded; session handoff #04 is backfilled.

---

## 1. Files

```
docs/
  handoff/
    04_point_1r_opening.md    CREATED    104 lines
    05_point_1r.md            MODIFIED   494 lines  (was 360; +145 / −11)
  prompts/
    06_1r_errata.md           CREATED    192 lines
reports/
  06_1r_errata.md             CREATED    this file
```

## 2. Commit

Documentation commit: `72ecd8b6fe45b84d37d87bd2f56c2d1682cad150` (`72ecd8b`).

`git diff --stat` for that commit:

```
 docs/handoff/04_point_1r_opening.md | 104 +++++++++++++++++++
 docs/handoff/05_point_1r.md         | 156 ++++++++++++++++++++++++++---
 docs/prompts/06_1r_errata.md        | 192 ++++++++++++++++++++++++++++++++++++
 3 files changed, 441 insertions(+), 11 deletions(-)
```

`git status` after that commit:

```
?? reports/06_1r_errata.md
```

**Deviation from the prompt, flagged:** the prompt asked for a single commit covering all four files, but this report must quote the commit hash of the work it describes, and a file cannot contain the hash of the commit that creates it. This report is therefore committed in an immediately following commit, matching the precedent already set in this repo by `a46ce53` ("fill commit hash and status into Point 1R handoff report"). No other deviation.

## 3. Edits to `05_point_1r.md`, section by section

| Section | Edit | Kind |
|---|---|---|
| 3 (1R.1 heading) | Heading now reads "(seven amendments, A1–A7, plus the Guard Rail Principle as a separately stated binding rule)" | Label only (A7) |
| 3 / A2 | `R / (E * L_max)` → `risk_usd / (E * L_max)`; added symbol declarations for `risk_usd`, `E`, `L_max`; leverage term restated as `risk_usd / (E * L_max)` = $20 / ($2,000 × 3.0) = 0.333% | Notation only (A4) |
| 3 / A5 | "with fixed $20 risk" → "with `risk_usd` fixed at $20" | Notation only (A4) |
| 4 (1R.2 heading) | Heading now reads "(B0 contamination ledger update, plus five amendments, B1–B5)" | Label only (A7) |
| 5 / D4 | Added a naming-identity line: `checkpoint_bars` and `time_stop_bars` are the same quantity; `time_stop_bars` is canonical. Formula updated to `phi = (threshold_R / target_R) / (time_stop_bars / max_hold_bars)` | Naming only (A6) |
| 6 (1R.4 heading) | Heading now reads "(defect statement, reconciliation, decomposition and structural prediction, plus six amendments, E1–E6)" | Label only (A7) |
| 8 | Capital/risk row: `risk_usd` = $20 (FIXED), percent-of-equity deferred to Point 7. `stop_min_pct` row: `R` → `risk_usd`. Narrative paragraph: same risk phrasing | Risk denomination + notation (A3, A4) |
| 10 | "$2,000, 1% risk after costs" → "$2,000 account, `risk_usd` = $20 (FIXED) per trade after costs", with the Point 7 deferral and a pointer to Section 13 A3 | Risk denomination (A3) |
| 13 | New section: Errata and Numeric Kill Thresholds, A1–A7 | New content |

**No decision content changed beyond the eight resolved flags.** Sections 1, 2, 7, 9, 11 and 12 are byte-identical. Section 10's pre-committed kill conditions are unchanged and unweakened — the only edit in Section 10 is in the "Also unchanged" list, resolving the `$20` vs `1%` ambiguity, and it neither loosens nor reinterprets any kill condition.

Sections 1–13 are present and in order.

## 4. A1 threshold groups — numeric cuts confirmed

All six carry explicit numeric cuts; no qualitative language survives in any decision rule.

| Group | Numeric cut |
|---|---|
| B3 validity | >= 99.99% of bars inside `[low − 1 tick, high + 1 tick]`, per symbol per year |
| B3 non-redundancy | `|rho| >= 0.90` KILL / `0.70 <= |rho| < 0.90` AMBER / `< 0.70` PASS |
| B3 dispersion | IQR of `vwap_position` >= 0.15 AND a threshold exists rejecting 25%–75% of breakout bars |
| F2 `rsi_lower` | rejects < 5% → drop; >= 5% → retained as a live arm |
| B5 selectivity ratio | >= 2.0 pre-spent / <= 1.3 never selective / 1.3–2.0 inconclusive |
| B2 denomination | more stable denomination must win in >= 2 of 3 symbols across both years; else default `quote_volume` |

The qualitative phrases "very high", "clusters tightly" and "rejects almost nothing" remain in the original B3/F2 prose in Sections 4 and 7, where they are the historical statement of the check being resolved. Section 13 supplies the operative cuts. Nothing in the decision rules is qualitative.

## 5. Flagged, NOT resolved

1. **A2 was not applied in place.** Part A2 says the `~66% x ~50% = ~33%` figure should be "replaced"; Part B lists only A3, A4 and A6 as in-place edits, and the verification checklist restricts the diff to Sections 8, 10, the headings, the notation, the canonicalisation and Section 13. The B4 paragraph in Section 4 therefore still carries the `~33%` figure, superseded by Section 13 A2. Following the verification checklist over the looser wording in A2; flagging rather than resolving.

2. **A7 assumes headings that do not exist.** The prompt says the 1R.1 / 1R.2 / 1R.4 headings "state amendment counts that do not match their contents". They stated no counts at all — they read simply "1R.1 — Stop Geometry", etc. Correct counts were added rather than corrected. The enumerated contents were verified to match: A1–A7 (seven) plus the Guard Rail Principle; B0 plus B1–B5 (five); defect/reconciliation/decomposition/prediction plus E1–E6 (six).

3. **`checkpoint_bars` appeared only once.** The collision was narrower than A6 implies — the D4 formula was the sole occurrence. Section 8 already used "Checkpoint threshold" as prose (not as a parameter name) and was left alone.

4. **"one tick" is not defined in the repo.** The B3 validity tolerance is stated in ticks, but no per-symbol tick size is recorded in any handoff. Point 4 will need the Bitget contract tick sizes for BTC/ETH/SOL before this check can be executed. Not resolved here.

5. **Point 7 is referenced but not scoped.** A3 defers percent-of-equity sizing to Point 7; the point list in the handoffs does not describe Point 7's contents. Recorded as-is.

6. **Section 13's A-labels collide with Section 3's A-labels.** Section 13 uses A1–A7 for errata items while Section 3 (1R.1) uses A1–A7 for stop-geometry amendments. Both are as the prompt specified. Cross-references in Section 13 disambiguate by naming the section, but the collision exists.

## 6. Constraint compliance

- **No code, test, config or data file was created, modified or deleted.** The commit touches three files, all under `docs/`; this report is the only file under `reports/`. Nothing under `src/`, `tests/`, `config/` or `data/` appears in `git status` or the diff.
- **No parameter value changed.** `risk_usd = $20` is a disambiguation of two phrasings that already agreed at $2,000 equity, not a new value.
- **No backtest, sweep, data pull or analysis script was run.**
- **The performance firewall was not breached.** No profit, loss, expectancy, win-rate, Sharpe, profit-factor or equity figure was computed, displayed or estimated. Figures reproduced in the handoff backfill are binding rates, pass rates and exit-reason counts — all on the allowed list — carried verbatim from Section 2 of `05_point_1r.md`.
- **No pre-committed kill condition was weakened, softened or reinterpreted.**
- **The A1 thresholds were not adjusted for plausibility**, and no commentary suggesting post-hoc revision was added.
