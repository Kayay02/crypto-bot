# Report 05 — Point 1R Handoff

Documentation-only task. Three files created, nothing else touched.

## Files created

```
docs/handoff/05_point_1r.md            360 lines
docs/prompts/05_point_1r_handoff.md    199 lines
reports/05_point_1r_handoff.md          66 lines
```

## Commit

`0da9d11c4d48e8c53b361f9c0a364bc01ce92610`

Message: `docs: Point 1R handoff — strategy amendment pass (1R.1-1R.5)`

## git status after commit

`git status --short` returns no output; `git status --porcelain | wc -l` returns 0. Working tree clean — the three new files were the only changes, and no existing tracked file was modified.

Commit contents:

```
docs/handoff/05_point_1r.md         | 360 ++++
docs/prompts/05_point_1r_handoff.md | 199 ++++
reports/05_point_1r_handoff.md      |  66 ++
3 files changed, 625 insertions(+)
```

A commit cannot contain its own hash, so this report was written with placeholders, committed as `0da9d11` above, and the hash/status then filled in by a follow-up commit touching only this report file. `0da9d11` is the handoff commit.

## Section headings in docs/handoff/05_point_1r.md

1. Status
2. The Four Mechanical Findings That Caused 1R
3. 1R.1 — Stop Geometry
4. 1R.2 — Volume Gate
5. 1R.3 — Time Stop
6. 1R.4 — The Edge Claim
7. 1R.5 — RSI
8. Baseline Strategy After 1R
9. Labelled Variants
10. What Must Not Change
11. Open Questions Carried Into Point 4 and Beyond
12. Next Open Point

All twelve sections present, in order.

## Flagged — noticed while writing, NOT resolved

1. **Sub-point amendment counts do not match the headings supplied.** 1R.1 was labelled "six amendments" but enumerates A1–A7 (seven) plus the Guard Rail Principle. 1R.2 was labelled "six amendments" and enumerates B0–B5 (six, if B0 counts as an amendment rather than a ledger update). 1R.4 was labelled "six amendments" but enumerates E1–E6 plus a separate defect/reconciliation/decomposition/structural-prediction preamble. Recorded as written; counts not corrected.

2. **A2 formula symbols are partly undefined in the source text.** `R / (E * L_max)` is evaluated as `$20 / ($2,000 * 3.0)`, so R = risk per trade, E = equity, L_max = max leverage — but the symbols themselves are never declared, and `R` here means dollar risk while `R` everywhere else in the document means the risk multiple (as in "+2R", "0.05R"). The same letter carries two meanings. Left as given.

3. **"$20 risk per trade" vs "1% risk after costs"** appear as two statements of the same constraint (Section 8 and Section 10). They agree at exactly $2,000 equity but diverge as equity moves. The document does not say which is authoritative.

4. **D4 arithmetic vs D3.** D4 states that with D3's derived counts (20 / 40) and phi = 1.0 the checkpoint threshold "solves to +1R". Using the given formula with target_R = 2 that yields threshold_R = 1.0 — consistent. Noting only that the formula's `checkpoint_bars` and D3's `time_stop_bars` are the same quantity under two names; the document never states this identity explicitly.

5. **B4 sample-size arithmetic is approximate and unsourced.** The "~66% x ~50% = ~33%" uses ~66% from the measured RVOL pass rate but ~50% for vwap_position, which has no threshold set yet and therefore no measured pass rate. Recorded as given.

6. **A3's floor-binding acceptance threshold (>20%) and F2's "rejects almost nothing" criterion** are stated at different levels of precision — one numeric, one qualitative. F2's decision rule has no numeric cut.

7. **Section 3 heading says "six amendments" while the Guard Rail Principle is introduced inside it** and is then applied in 1R.5. It is stated as a principle, not numbered as an amendment, so its status (binding rule vs rationale) is ambiguous.

8. **Prior handoff `docs/handoff/04_*.md` does not exist in the repo** — `docs/handoff/` contained only `.gitkeep` before this commit. The prompt's context assumed handoff #04 was already committed. Not created or reconstructed here.

## Firewall compliance

No profit, loss, expectancy, win-rate, Sharpe, profit-factor or equity figure was computed, displayed or estimated. The only numerics carried into the handoff are: binding/pass rates and exit-type frequencies from the four mechanical findings (rates, not performance), the retired "36%" framing explicitly labelled as retired and conditional, the 0.05R pre-committed drop threshold, and the E5 standard-error estimates.

## Scope confirmation

No file under `src/`, `tests/`, `config/` or `data/` was created, modified or deleted. No backtest, sweep, data pull or analysis script was run. No parameter value anywhere in the repo was changed.
