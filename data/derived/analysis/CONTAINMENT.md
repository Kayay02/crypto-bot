# CONTAINMENT — DO NOT OPEN `e6_dispersion.json` OR `trades/`

**THE MARKER `docs/design/04_2a_artifact_containment.md` §3.4 COMMITS.** It is
placed here because **a marker a step meets before the file beats a rule it must
remember.**

---

## THE PROHIBITION

> ### NO STEP, DOCUMENT OR REPORT MAY OPEN AN OUTCOME-BEARING ARTIFACT NAMED
> ### BELOW. A STEP THAT BELIEVES IT MUST DO SO STOPS AND REPORTS INSTEAD.

**IT COVERS READING FOR ANY PURPOSE, INCLUDING VERIFICATION.**

> ### A VERIFICATION THAT OPENS THE FILE HAS ALREADY READ WHAT IT WAS VERIFYING
> ### THE ABSENCE OF.

---

## WHAT THESE FILES ARE

- **`e6_dispersion.json`** — the E6 dispersion run's artifact: the measured
  sigma, the per-fold trade counts and the E6 trigger verdict.
- **`trades/`** — the 54 trade tables the run produced. Untracked.

**COVERED BY PRECAUTION RATHER THAN BY ESTABLISHED CONTENT**, and the difference
is stated rather than smoothed over.
`docs/handoff/41_point_4_2_artifact_audit.md` §2.2 records that the writer,
`src/analysis/dispersion.py`, carries two guards — a forbidden-term list and a
permitted-statistic allowlist whose statistical members are dispersion measures
and explicitly not location measures — so **the schema indicates dispersion
statistics and excludes location statistics.**

> ### WHETHER THOSE GUARDS HELD IN THE RUN THAT PRODUCED THIS FILE CANNOT BE
> ### CONFIRMED WITHOUT OPENING IT, AND IT WAS NOT OPENED.

**AND THE COMMIT THAT INTRODUCED IT ANNOUNCES A PARTIAL FIREWALL LIFT IN ITS OWN
MESSAGE**, which is the plainest statement in this repository that a firewall was
deliberately relaxed. `docs/design/04_2a_artifact_containment.md` §3.1 covers it
for that reason:

> **AN UNKNOWN IS TREATED AS CONTAINING**, because the only way to establish
> otherwise is to open the file, which is the act being prevented.

---

## WHICH THESIS IT BELONGS TO

**NOT THE FROZEN ONE.** It belongs to the superseded Point 4 sequence's fold
architecture decision and predates the thesis freeze.
`docs/handoff/41_point_4_2_artifact_audit.md` §4.2 establishes that **no design
document and no report committed in Points 4 or 5 cites a figure from it.**

**IT IS KEPT, NOT DELETED.** It is the evidence for the decision it fed, and
removing it would destroy the record that makes that decision checkable.
**Containment is about reading, not about existence.**

---

## WHO MAY STILL OPEN IT

**A CLOSED SET, ENUMERATED AT `docs/design/04_2a_artifact_containment.md` §3.3
AND ASSERTED BY `tests/test_containment_guard.py`:**

- **`tests/test_dispersion.py`.**
- **`src/analysis/dispersion.py` WRITES IT AND NEVER READS IT.** The producer's
  status under §3.2 is not settled by that document and is recorded rather than
  decided; the guard asserts the write-only property instead of assuming it.

> ### NO NEW READER JOINS WITHOUT AMENDING THAT DOCUMENT.
