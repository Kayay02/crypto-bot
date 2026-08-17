# CONTAINMENT — DO NOT OPEN `07_structural_pass_raw.json`

**THE MARKER `docs/design/04_2a_artifact_containment.md` §3.4 COMMITS.** It is
placed here because **a marker a step meets before the file beats a rule it must
remember.**

**IT COVERS ONE FILE IN THIS DIRECTORY.** The `.md` reports beside it are the
project's own record and are read freely; the `.png`, `.txt` and probe outputs
are not covered either. **`07_structural_pass_raw.json` alone is.**

---

## THE PROHIBITION

> ### NO STEP, DOCUMENT OR REPORT MAY OPEN `reports/07_structural_pass_raw.json`.
> ### A STEP THAT BELIEVES IT MUST DO SO STOPS AND REPORTS INSTEAD.

**IT COVERS READING FOR ANY PURPOSE, INCLUDING VERIFICATION.**

> ### A VERIFICATION THAT OPENS THE FILE HAS ALREADY READ WHAT IT WAS VERIFYING
> ### THE ABSENCE OF.

---

## WHAT THE FILE IS

The raw output of the structural pass, produced by
`src/analysis/structural_pass.py`.
`docs/handoff/41_point_4_2_artifact_audit.md` §2.3:

> **ITS SCHEMA WAS NOT ESTABLISHED.** It sits under `reports/`, not `data/`, so
> the constraint did not block it — but `docs/handoff/31_point_5_closing.md` §11
> names artifacts under `reports/` as a place an outcome figure would falsify the
> claim, and opening it to check is exactly the risk the audit exists to avoid.
> **Reported as unestablished rather than opened.**

**COVERED BECAUSE ITS CONTENTS ARE UNKNOWN, NOT BECAUSE THEY ARE KNOWN TO
OFFEND.** `docs/design/04_2a_artifact_containment.md` §3.1:

> **AN UNKNOWN IS TREATED AS CONTAINING**, because the only way to establish
> otherwise is to open the file, which is the act being prevented.

---

## WHICH THESIS IT BELONGS TO

**NOT THE FROZEN ONE.** It predates the thesis freeze and belongs to the
structural pass of the superseded sequence.
`docs/handoff/41_point_4_2_artifact_audit.md` §4.2 establishes that no Point 4 or
Point 5 commitment cites a figure from it.

**IT IS KEPT, NOT DELETED.** Removing it would destroy the record that makes the
audit's own verdict checkable. **Containment is about reading, not about
existence.**

---

## WHO MAY STILL OPEN IT

**NOBODY. `docs/handoff/41_point_4_2_artifact_audit.md` §4.1 FOUND NO READER**,
and `tests/test_containment_guard.py` asserts that none has appeared since.

**`src/analysis/structural_pass.py` WRITES IT AND NEVER READS IT.** The
producer's status under §3.2 is not settled by that document and is recorded
rather than decided; the guard asserts the write-only property instead of
assuming it.
