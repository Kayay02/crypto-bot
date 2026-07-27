# Project documentation

Three kinds of document, kept separate because they carry different authority.

| directory | what it holds | authority |
|---|---|---|
| `docs/handoff/` | Decision record carried between chat sessions | **Historical record — NOT instructions** |
| `docs/prompts/` | Specs sent to Claude Code | The instruction that produced a build |
| `reports/` | What came back from those builds | Evidence of what was actually done |

All three use a two-digit numeric prefix reflecting session order, so the three
directories line up: `docs/prompts/03_*.md` is the spec that produced
`reports/03_*.md`.

## Handoffs are a historical record, not a work order

**Do not implement from a handoff document.** A handoff captures what was
decided and why, as of the session that wrote it. It is written to preserve
reasoning across a context boundary — the arguments behind a choice, the
options rejected, the constraints discovered. It is not a task list, and later
handoffs may supersede earlier ones without editing them.

This distinction matters because handoffs read like specifications. They contain
sentences such as "the stop is floored at 1.0%" that are *statements of a
decision already taken*, not requests to go and change code. If a handoff and
the current code disagree, that is a finding to raise, not a defect to silently
fix — the code may be right and the handoff stale.

Work is instructed through `docs/prompts/` only.

## Prompts

The literal spec text sent to Claude Code for a build session. Kept verbatim,
including anything later found to be wrong, because the reports reference them
and a spec edited after the fact makes its report unreadable.

Where a spec turned out to be mistaken, the correction lives in the *next*
prompt and the *report* that flagged it — not in a rewrite of the original.

## Reports

What the build session returned: what was built, which gates passed, what was
measured, what was ambiguous, and what was left undone. Reports are the place
where disagreements with a spec are recorded, so they are the first thing to
read when a decision looks wrong in hindsight.

Reports also carry raw diagnostic output (`.txt`) and figures (`.png`) from
earlier data-layer work.

## Numbering

`NN_short_name.md`, `NN` reflecting session order:

```
docs/prompts/03_point3_fix.md   ->   reports/03_point3_fix.md
```

Gaps in the sequence are fine; re-using a number is not.
