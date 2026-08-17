# CONTAINMENT — DO NOT OPEN THE FILES IN THIS DIRECTORY

**THE MARKER `docs/design/04_2a_artifact_containment.md` §3.4 COMMITS.** It is
placed here because **a marker a step meets before the file beats a rule it must
remember.**

---

## THE PROHIBITION

> ### NO STEP, DOCUMENT OR REPORT MAY OPEN AN OUTCOME-BEARING ARTIFACT NAMED
> ### BELOW. A STEP THAT BELIEVES IT MUST DO SO STOPS AND REPORTS INSTEAD.

**THE PROHIBITION COVERS READING FOR ANY PURPOSE, INCLUDING VERIFICATION.**

> ### A VERIFICATION THAT OPENS THE FILE HAS ALREADY READ WHAT IT WAS VERIFYING
> ### THE ABSENCE OF.

The most plausible future breach is not someone wanting a figure; it is someone
wanting to confirm there is no figure. **The confirming read and the offending
read are the same read.**

---

## WHAT THESE FILES ARE

- **`sweep.json`** — the step 2 deliverable of the superseded Point 4 sequence:
  per-offset, per-arm, per-population aggregates over the fold grid.
  **Outcome quantities established** — `docs/handoff/41_point_4_2_artifact_audit.md`
  §2.1.
- **`bands.json`** — the step 3 deliverable, built from `sweep.json`: acceptance
  verdicts, per-fold bands, plateau selections and kill-condition verdicts.
  **Built from outcome quantities.**
- **`sweep_cells.jsonl`** — the per-cell records behind `sweep.json`.
  **UNTRACKED, BY DECISION**, `docs/design/04_2a_artifact_containment.md` §3.5:
  tracking it would add a further outcome-bearing file to version control, which
  runs directly against §3.2.
- **`trades/`** — the per-cell trade tables. Untracked, and reachable only from
  the sweep's own modules.

**`grid.json` AND `sweep_checkpoint.json` ARE NOT COVERED.** `grid.json` is a
pre-registration artifact — the eleven multipliers, `m*`, the derived cap and the
A3 verdict per fold per symbol — and carries no outcome quantity. It is tracked
deliberately, so that a commit proves the range was not widened afterwards.

---

## WHICH THESIS THEY BELONG TO

**NOT THE FROZEN ONE.** `docs/design/04_2a_artifact_containment.md` §2.1
declares the apparatus that produced them **dead relative to the frozen thesis**:

> ### `src/sweep/` SELECTS A PER-FOLD ATR MULTIPLIER ON TRAINING DATA. IT DOES
> ### NOT PARTICIPATE IN EVALUATING THE FROZEN THESIS, AND THE FROZEN THESIS
> ### FITS NOTHING.

**AND THE PARAMETERISATION DIFFERS IN THREE MATERIAL RESPECTS**, per
`docs/handoff/41_point_4_2_artifact_audit.md` §3.4: the ATR multiple (a searched
range against the thesis's frozen 2.25), the stop cap (a per-fold cap against the
no-cap `docs/design/04_1g_cap_adoption.md` adopted), and the stop floor (the
derived floor of the superseded engine against the thesis's frozen one).

> ### THE ARTIFACTS DESCRIBE A SYSTEM PARAMETERISED DIFFERENTLY FROM THE ONE THE
> ### FROZEN THESIS SPECIFIES.

**THEY ARE KEPT, NOT DELETED**, because they are the evidence for the superseded
point and for report 41's own verdict, and removing them would destroy the record
that makes the verdict checkable. **Containment is about reading, not about
existence.**

---

## WHO MAY STILL OPEN THEM

**A CLOSED SET, ENUMERATED AT `docs/design/04_2a_artifact_containment.md` §3.3
AND ASSERTED BY `tests/test_containment_guard.py`:**

- **the sweep's own modules** — `src/sweep/grid.py`, `bands.py`, `sweep.py`,
  `sweep_report.py`. The apparatus may read its own artifacts; being dead
  relative to the frozen thesis is a statement about what it feeds, not a
  prohibition on it functioning.
- **`tests/test_sweep_run.py`** and **`tests/test_sweep_prescreen.py`**.

> ### NO NEW READER JOINS EITHER CLASS WITHOUT AMENDING THAT DOCUMENT.
