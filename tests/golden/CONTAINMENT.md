# THE FIXTURE CARVE-OUT — READ THIS BEFORE TOUCHING THESE FILES

**THE TWO GOLDEN FILES CARRY OUTCOME QUANTITIES.**
`docs/handoff/41_point_4_2_artifact_audit.md` §2.5 established it from the header
row alone: both carry the same 34 columns, among them **four canonical banned
names and two outcome-adjacent ones**. Only the header was read; the rows beneath
were not.

> ### THEY ARE THE ONLY OUTCOME-BEARING ARTIFACTS THE CURRENT TEST SUITE READS,
> ### ON EVERY INVOCATION.

**THEY ARE THEREFORE GOVERNED BY A CARVE-OUT, NOT BY THE BLANKET PROHIBITION.**
`docs/design/04_2a_artifact_containment.md` §3.1(6) places them under §4 rather
than under §3.2, and §4.4 requires the carve-out's conditions be recorded where a
developer touching these fixtures will see them. **This file is that record**,
alongside the docstrings of the two readers themselves. The conditions below are
transcribed from §4.2 and §4.3 and are not restated from memory.

---

## THE CARVE-OUT

> ### THE TWO GOLDEN FILES AND THE PINNED-TRADE REGRESSION MAY READ
> ### OUTCOME-NAMED VALUES, PERMITTED ONLY UNDER FOUR CONDITIONS.

**(a) DETERMINISM AND SINGLE-POSITION IDENTITY ONLY.** They may assert that
identical inputs produce identical outputs, and that one hand-derived arithmetic
identity holds on one named position. **They may not compare populations, compare
two configurations, or aggregate over rows.**

**(b) EVERY EXPECTED VALUE IS HAND-DERIVED AND ITS DERIVATION IS WRITTEN DOWN.**
`tests/test_regression_pinned_trade.py`'s docstring already meets this — *"Every
value below is re-derived by hand from the formula, not copied from a run."*
**A value copied from a run is not permitted**, because a fixture that records
what the system did is a measurement wearing a fixture's name.

**(c) EXACTLY THESE ARTIFACTS AND EXACTLY THESE READERS.** The two files named at
§3.1(6) — `btc_2023_01_gated.csv` and `btc_2023_01_signal_ungated.csv` — and
`tests/test_regression_pinned_trade.py` and `tests/test_determinism_golden.py`.
**No further fixture and no further reader joins without amending that
document.**

**(d) THE BLANKET NAME BAN OTHERWISE INTACT.** The twelve-name guard is not
relaxed for these files, for these tests, or for anything else — mirroring the
third condition of the existing carve-out at `src/engine/sizing.py`.

---

## WHAT VOIDS IT

**ANY OF THE FOLLOWING EXCEEDS THE CARVE-OUT AND REOPENS IT:**

- **USING A FIXTURE TO COMPARE TWO CONFIGURATIONS**, which converts a determinism
  check into a comparison.
- **ADDING A SECOND PINNED TRADE**, because a count over two is a population of
  two and condition (a) then fails by arithmetic rather than by intent.
- **REGENERATING A GOLDEN FILE AND TAKING EXPECTED VALUES FROM THE RUN** rather
  than re-deriving them, which voids condition (b).
- **ANY ASSERTION OVER AN AGGREGATE OF THE ROWS** — a sum, a mean, a count
  conditioned on an outcome column.

> ### THE FIRST AND THE LAST ARE THE ONES THAT WOULD LOOK INNOCENT AT THE TIME,
> ### AND THEY ARE NAMED FOR THAT REASON.

---

## WHERE IT IS ENFORCED

**`tests/test_containment_guard.py` §2 ASSERTS ALL FOUR CONDITIONS AND ALL FOUR
VOIDING CASES OVER THE AST OF THE TWO READERS.** A rule enforced only by
intention is the shape of every defect in the ledger.

**`tests/make_golden.py` REGENERATES THESE FILES AND IS NOT A READER.** Running
it does not by itself void the carve-out; **taking a new expected value out of
what it produced does**, which is condition (b) and the third voiding case.

---

## WHY THEY EXIST AT ALL

They are determinism and arithmetic-identity fixtures, they predate the thesis
freeze, and **no decision cites them** —
`docs/handoff/41_point_4_2_artifact_audit.md` §4.3, which records that
`tests/test_determinism_golden.py` compares an output hash, the column list and
the row count and inspects no value, and that
`tests/test_regression_pinned_trade.py` is an arithmetic identity check on a
single position and not a measurement over a population.

> ### NONE OF THEM IS A CHAIN TO A COMMITMENT: NO POINT 4 OR POINT 5 DECISION
> ### CITES ANY OF THEM, AND NONE FEEDS A PARAMETER.
