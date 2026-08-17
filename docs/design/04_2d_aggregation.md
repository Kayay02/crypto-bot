# AGGREGATION, AND WHAT A COMPARISON BETWEEN PERIODS SUPPORTS

**SUB-POINT 4.2d. PRE-REGISTRATION. IT JOINS THE FROZEN SPECIFICATION ON COMMIT.**

**Manifest at entry: `8fe346881a56881c833d853539c5594ff38f6521e2902e254b5d5fc878c50ce6`,
60 entries, every entry verified, zero problems.**

---

## 1. WHAT THIS DOCUMENT IS

**IT DECIDES AT WHAT LEVEL A QUANTITY MAY BE COMPUTED, WHAT A PER-PERIOD FIGURE
IS, AND WHAT A COMPARISON BETWEEN PERIODS MAY AND MAY NOT SUPPORT.**

### 1.1 WHAT IT RELIES ON AND DOES NOT REARGUE

**`docs/design/04_2c_run_structure.md`'s COMMITTED STRUCTURE.** One continuous run
over the whole in-sample window; the budget initialised once and carried across
every boundary; fold periods applied afterwards to the run's output; positions
assigned by entry-bar close; the evaluation population committed as a rule.

**`docs/design/04_2a_artifact_containment.md` §2.4's COMMITTED FINDING.** Nothing is
fitted on train in the frozen thesis's path, so the nine folds are a
time-variation diagnostic and not nine trials.

**BOTH ARE PREMISES HERE.** Neither is reopened, and neither the run structure, the
evaluation population nor the fold interpretation is reargued.

### 1.2 THE LINE AGAINST 4.3, DRAWN BEFORE ANYTHING IS DECIDED

> ### THIS DOCUMENT DECIDES **AT WHAT LEVEL** A QUANTITY MAY BE COMPUTED AND **WHAT
> ### A COMPARISON MEANS.** IT DOES NOT DECIDE **WHICH QUANTITIES.**

**THE DRAFTING TEST, STATED SO THAT THE LINE IS CHECKABLE RATHER THAN ASSERTED.**
If a rule here cannot be made concrete without naming a specific metric, **that is
the signal the line is being crossed**, and the remedy is to name the **shape** of
the quantity instead — "a quantity computed over trades", "a quantity with a count
denominator", "an aggregate whose per-trade contributions may or may not be
size-weighted" — never the quantity itself.

**THE SHAPE VOCABULARY IS USED THROUGHOUT AND IS NOT AN EVASION.** A rule about
denominators binds on every quantity that has one, which is strictly more than a
rule about any named quantity would bind on, and it binds before 4.3 exists to be
constrained.

### 1.3 WHAT IT DOES NOT DO

**NO METRIC.** No quantity is defined, named as reportable, or selected.

**NO LEVEL AND NO THRESHOLD.** Nothing here is a kill condition, a pass mark, an
adequacy bound or a magnitude. **4.4's.**

**IT DOES NOT TOUCH KILL CONDITION (d).** §6.4 states what this document's rule
does to the **ground** on which `docs/design/04_1c_consequences_and_thresholds.md`
§3.3 chose (d)'s level. **It does not restate the condition and does not touch its
threshold**, which that document's §3.5 records as already committed in the thesis
and not this chain's to set.

**NOTHING IS COMPUTED, MEASURED, OR RUN.** No count in this document is produced
here. No artifact under `docs/design/04_2a_artifact_containment.md` §3's prohibition
is opened.

---

## 2. POOLING IS NOT AN AGGREGATION

**STATED FIRST, BECAUSE THE VOCABULARY OF WALK-FORWARD VALIDATION PULLS THE OTHER
WAY AND WILL KEEP PULLING.**

### 2.1 THE INVERSION

In the standard walk-forward picture there are k independent evaluations and the
question is how to combine them. Every word in that sentence — fold, out-of-sample
result, pooled estimate, aggregation — carries the assumption that the parts come
first and the whole is assembled from them.

> ### **UNDER ONE CONTINUOUS RUN THAT DEPENDENCY IS BACKWARDS. THE RUN-LEVEL
> ### QUANTITY IS PRIMARY. A PER-PERIOD FIGURE IS A DECOMPOSITION OF IT.**

**THERE IS NOTHING TO COMBINE.** The run produced one sequence of positions under
one budget path. A run-level quantity is that quantity computed over that
sequence. A per-period figure is **the same quantity computed over a subset of the
same sequence**, selected by entry date. The subset is carved out of the whole; the
whole is not built up from the subsets.

**SO "POOLED" IS THE WRONG WORD FOR THE RUN-LEVEL FIGURE, AND IT IS USED IN THE
RECORD.** `docs/design/04_1c_consequences_and_thresholds.md` §3.3 says (d) "IS
EVALUATED POOLED OVER THE WHOLE EVALUATION WINDOW" and calls the per-fold view a
**decomposition** in the same breath. **The second word is the accurate one.**
Nothing is pooled, because nothing was ever apart.

**THE WORD IS NOT BANNED AND NOTHING IS RENAMED.** §3.3 is committed and this
document does not amend it. **What is committed here is the relation the word must
be read as naming**, so that a later reader does not infer a combining step from
the vocabulary and then look for the rule that governs it.

### 2.2 WHAT FOLLOWS: NO WEIGHTING SCHEME ACROSS PERIODS

> ### **NO WEIGHTING SCHEME ACROSS PERIODS IS NEEDED OR ADMISSIBLE.**

**WEIGHTING PRESUPPOSES SEPARATE ESTIMATES BEING MERGED.** A weight answers "how
much should this estimate count towards the combined one", and there is no
combined one to count towards. Assigning weights to the nine periods and
combining them would produce a number that is **not** the run-level figure and has
no referent in the run.

**AND THE RECONSTRUCTION IDENTITY IS NOT A WEIGHTING SCHEME.** For a quantity that
decomposes over a partition, the run-level figure will equal some determinate
combination of the period figures — a count-weighted one for a per-trade mean, a
risk-weighted one for a size-weighted aggregate, and so on. **That combination is
an arithmetic consequence of the operator, not a choice**, and it is available as a
**check** rather than as a method.

**THE CHECK ONLY CLOSES IF THE UNASSIGNED ROW IS INCLUDED**, which is one of the
two reasons §3.3 commits it.

### 2.3 A DISAGREEMENT IS A DEFECT, NOT A MODELLING CHOICE

> ### **IF A PER-PERIOD FIGURE AND THE RUN-LEVEL FIGURE DISAGREE ARITHMETICALLY,
> ### THAT IS A DEFECT.**

It is not a finding about the folds, not evidence of instability, and not a
modelling decision to be resolved by choosing a convention. **The two are the same
operator over a set and over its parts**, so a disagreement means one of: the
partition is not exhaustive, a position was assigned twice, the operator differs
between levels, or the arithmetic is wrong. **All four are bugs and each is
findable.**

**THIS IS THE PRACTICAL PAYOFF OF THE INVERSION.** Under the combining picture a
mismatch between a pooled figure and its parts is ambiguous, because the pooling
rule is itself a choice that could be different. **Here it is unambiguous**, and
that is worth more than any weighting scheme would have been.

---

## 3. WHICH PERIODS FORM THE PARTITION

### 3.1 THE EIGHTEEN PERIODS ARE NOT A PARTITION

`docs/handoff/40_point_4_2_fold_audit.md` §3.2: adjacent training windows overlap
by **49.5 to 50.3 per cent**, eight overlapping pairs, one per adjacent pair.
§3.3: **fifteen cross-overlaps**, each fold's test window falling entirely inside
the next two folds' training windows.

**SO A POSITION CAN LAND IN UP TO THREE OF THE EIGHTEEN PERIODS.** Rows built over
the eighteen do not sum to the whole: they double- and triple-count.

**ONLY THE NINE TEST WINDOWS ARE DISJOINT.** The same report §3.1: no two test
windows overlap by one day, and their union runs **2022-10-01 to 2024-12-31 with
no gaps**, each beginning the day after the previous one ends.

### 3.2 THE SETTLEMENT

> ### **THE PARTITION IS THE NINE TEST WINDOWS PLUS THE UNASSIGNED ROW.**
>
> ### THAT IS THE DECOMPOSITION WHOSE PARTS SUM TO THE WHOLE, AND IT IS THE ONLY
> ### ONE ON WHICH §2's IDENTITY AND §2.3's DEFECT TEST CAN OPERATE.

**IT IS EXHAUSTIVE AND DISJOINT.** Disjoint by §3.1. Exhaustive because assignment
is by entry-bar close (`docs/design/04_2c_run_structure.md` §2.5) and every entry
stamp either falls inside exactly one test window or falls outside all nine, in
which case it lands in the unassigned row and nowhere else.

**AND THERE IS NO TRAILING RESIDUE.** The union runs to 2024-12-31, which is the
in-sample window's own end, so the unassigned row is entirely a **leading**
residue.

### 3.3 THE UNASSIGNED ROW

> ### **DEFINITION: THE POSITIONS OF THE RUN WHOSE ENTRY-BAR CLOSE FALLS BEFORE
> ### 2022-10-01, THE FIRST TEST WINDOW'S START.**

**IT SPANS ROUGHLY NINE MONTHS.** The in-sample window's candidates begin
2022-01-05 — which `docs/design/04_2c_run_structure.md` §4.3 establishes is where
the 114-bar warm-up discard ends rather than a chosen date — and the first test
window opens 2022-10-01.

**IT IS NOT SMALL AND IT IS NOT INCIDENTAL.**
`docs/handoff/40_point_4_2_fold_audit.md` §3.4 puts **2,817 of 11,384 candidates**
outside every test window, and §6.4 records that they are not a random ninth of
the data. **How many of them the run takes is unknowable before the run**, per
`docs/handoff/31_point_5_closing.md` §5.6, so no count is stated here and none is
implied.

> ### **IT IS REPORTED. ALWAYS, AND EVEN WHEN A READER WOULD RATHER SEE A CLEAN
> ### PARTITION.**

**TWO REASONS, AND THE SECOND IS THE ONE THAT MAKES IT NON-NEGOTIABLE.**

**FIRST, `docs/design/04_2c_run_structure.md` §4.5 REQUIRES IT** — candidates in no
fold period are run and reported under an explicit unassigned row rather than
dropped, on `src/analysis/level_consequences.py:333`'s stated ground that a count
which silently loses rows is a count nobody can reconcile.

**SECOND, §2.2's RECONSTRUCTION IDENTITY DOES NOT CLOSE WITHOUT IT.** Drop the
unassigned row and the nine test-window figures no longer account for the run, so
§2.3's defect test stops working — a real disagreement between the parts and the
whole would be indistinguishable from the row that was suppressed. **Suppressing
it does not tidy the partition; it disables the only check the partition provides.**

**AND THE TEMPTATION IS REAL, WHICH IS WHY THE RULE IS WRITTEN DOWN NOW.** A table
of nine quarters plus a ragged ten-month remainder looks worse than a table of
nine quarters. **It is not worse. It is the same information with nothing hidden**,
and the version that looks tidier is the version that has lost a fifth of its
window.

### 3.4 TRAIN WINDOWS ARE INERT HERE, STATED PLAINLY

> ### **THE TRAIN WINDOWS PLAY NO ROLE IN ANYTHING THIS DOCUMENT DECIDES.**

**NOTHING IS FITTED ON THEM** — `docs/design/04_2a_artifact_containment.md` §2.4 —
so they mark no boundary the strategy is aware of and confer no status on the
positions inside them. **They also cannot form a partition**, by §3.1. **They are
not the basis of any figure, denominator, comparison or check committed here.**

**THEY ARE NOT DELETED FROM THE RECORD.** `docs/design/04_2c_run_structure.md` §5.1
commits the eighteen-period **decomposition** as a reporting form and this document
does not withdraw it; §4.2 states the one constraint the overlaps place on it.
**What is refused is carrying them forward as though they bit.**

### 3.5 A VOCABULARY CLARIFICATION, NOT AN ERRATUM

**`docs/design/04_2c_run_structure.md` §5.1 CALLS A FOLD PERIOD "A DATE PARTITION
OF ONE RUN'S OUTPUT" AND, TWO PARAGRAPHS LATER, STATES THAT THE PERIODS ARE AN
OVERLAPPING COVER AND NOT A PARTITION OF TIME.** Both statements are in the
committed text and the second is correct.

**THE DOCUMENT IS NOT WRONG — IT IS LOOSE**, and it discloses its own looseness in
the adjacent paragraph, which is why this is recorded as a clarification and not
logged as an erratum. **The vocabulary is fixed here for everything downstream:**

- **DECOMPOSITION** — any grouping of the run's positions for reporting, including
  the eighteen-period one, which may overlap.
- **PARTITION** — the disjoint, exhaustive grouping of §3.2, on which alone
  arithmetic across cells is defined.

---

## 4. WHAT THE OVERLAPS DO AND DO NOT CONSTRAIN

### 4.1 THEY DO NOT BIND ON THE PARTITION

**THE PARTITION IS BY TEST WINDOW, AND TEST WINDOWS ARE DISJOINT BY CONSTRUCTION**
(`docs/handoff/40_point_4_2_fold_audit.md` §3.1).

> ### **THE FIFTEEN CROSS-OVERLAPS AND THE 49.5 TO 50.3 PER CENT TRAIN OVERLAP
> ### TOUCH NOTHING COMPUTED OVER THE PARTITION.**

**NO CONSTRAINT IS MANUFACTURED TO JUSTIFY HAVING INHERITED THEM.** They were
inherited by `docs/design/04_2c_run_structure.md` §5.3 as things 4.2d could not
begin without, and the honest result of examining them is that they do not reach
the partition. **Saying so is the discharge.**

### 4.2 THE ONE THING THEY DO BIND ON

**THEY BIND ON THE EIGHTEEN-PERIOD DECOMPOSITION, WHICH IS STILL REPORTED.**

> ### **NO ARITHMETIC IS DEFINED ACROSS THE EIGHTEEN-PERIOD DECOMPOSITION'S ROWS.**
> ### THEY MAY NOT BE SUMMED, AVERAGED, OR COUNTED, BECAUSE A POSITION APPEARS IN
> ### UP TO THREE OF THEM.

**THIS IS NOT A CONSTRAINT ON A COMPARISON; IT IS A CONSTRAINT ON A TOTAL.** A
reader adding eighteen row counts and comparing the sum to the run's position count
will get a number roughly two to three times too large, and the error is silent
because every row is individually correct.

### 4.3 WHAT THEY ARE RETIRED AGAINST

> ### **THE OVERLAP FACTS ARE RETIRED HERE. THEY BIND ON ONE THING AND ONE ONLY:
> ### ANY FUTURE ATTEMPT TO TREAT THE PERIODS AS INDEPENDENT TRIALS.**

That attempt is foreclosed at §6.2 on grounds that do not need the overlaps at all
— **so the overlaps are now a second, redundant reason for a conclusion already
reached.** They are recorded as such rather than carried forward as live
constraints on aggregation, which they are not and never were.

**AND THE FIFTEEN CROSS-OVERLAPS' CONTENT IS WORTH NAMING PRECISELY BEFORE IT IS
RETIRED**, because it is easy to misremember as being about the test windows. It
says each fold's test window is later used as **training data**. That matters if
and only if something is fitted on train. **Nothing is.**

---

## 5. §5.5 AND WHAT A DENOMINATOR MEANS

### 5.1 THE PROPOSITION

`docs/handoff/31_point_5_closing.md` §5.5, on report 26 §3.3: taken counts per
training period are **976 to 1,025** while signal supply varies widely over the
same periods.

> "**TRADE COUNT PER FOLD MEASURES CAPITAL, NOT MARKET CONDITIONS.** A fold with
> more signals does not produce more trades; it produces more skips."

**`docs/design/04_2b_point_4_decomposition.md` §5.2 ATTACHES §5.5 TO 4.3;
`docs/design/04_2c_run_structure.md` §5.3 STATES ITS AGGREGATION HALF IS THIS
DOCUMENT'S.** That half is discharged below.

### 5.2 WHAT A VARYING DENOMINATOR DOES TO A COMPARISON

**ANY PER-PERIOD QUANTITY COMPUTED OVER TRADES HAS THE PERIOD'S TRADE COUNT AS ITS
DENOMINATOR, AND THAT COUNT VARIES FOR A REASON THAT IS NOT THE STRATEGY'S** — the
budget's spare capacity at that time, which by `docs/handoff/31_point_5_closing.md`
§5.6 is a function of realised outcomes over the preceding path.

**SO TWO PERIODS' PER-TRADE FIGURES ARE MEANS OVER SAMPLES WHOSE SIZES DIFFER FOR A
CAPACITY REASON.** A difference between them is not, on its face, a difference in
how the strategy behaved.

**AND THE SECOND EFFECT IS THE ONE THAT IS EASY TO MISS, BECAUSE IT IS NOT ABOUT
SIZE AT ALL.** `docs/design/05_aggregate_risk_budget.md` §5.2 records it as a known
bias, in advance:

> "**SIGNALS CLUSTER IN HIGH-VOLATILITY PERIODS.** A book that is full is a book
> that has recently filled, so **the cap preferentially skips signals arriving
> during clusters — which is to say, preferentially skips high-ATR trades.**"

> ### **THE SAMPLES DO NOT MERELY DIFFER IN SIZE. THEY DIFFER IN COMPOSITION, AND
> ### THE COMPOSITION SHIFT HAS A KNOWN DIRECTION.**

A period in which the book ran full is a period whose taken population is skewed
away from high-ATR entries relative to its own signal supply. **A comparison of two
per-trade figures is therefore a comparison across two differently-composed
populations**, which is the same species of thing
`docs/design/05_aggregate_risk_budget.md` §6.3 says must be declared when it
occurs, applied here between two periods of one run rather than between two runs.

**THIS IS NOT A REASON NOT TO COMPARE.** §6 sets out what a comparison does
support. **It is the reason a bare pair of numbers cannot carry the comparison**,
which is §5.3.

### 5.3 A PER-PERIOD QUANTITY MUST CARRY ITS DENOMINATOR

> ### **EVERY PER-PERIOD FIGURE IS REPORTED WITH THE DENOMINATOR IT WAS COMPUTED
> ### OVER. A FIGURE WITHOUT ITS DENOMINATOR IS NOT REPORTED.**

**FIRST REASON — WITHOUT IT THE FIGURE IS UNINTERPRETABLE.** By §5.2 the
denominator varies for a path reason and the composition varies with it. A reader
given two figures and no denominators cannot tell whether a difference reflects the
strategy, the book's state, or a thin cell. **A number that cannot be interpreted
by the reader it is reported to has not been reported; it has been displayed.**

**SECOND REASON — THE DENOMINATORS ARE WHAT MAKE §2.2's CHECK PERFORMABLE.** The
reconstruction identity needs the cell counts. Without them a reader cannot verify
that the parts account for the whole, and §2.3's defect test — the one thing that
distinguishes a bug from a finding — is unavailable.

**THE RULE IS ABOUT SHAPE, NOT ABOUT ANY QUANTITY.** It binds on every per-period
figure that has a denominator, whatever 4.3 decides those figures are, and it binds
before 4.3 exists.

**AND IT APPLIES TO THE RUN-LEVEL FIGURE TOO.** The run-level denominator is
reported for the same two reasons, and because a partition whose parts carry
denominators and whose whole does not cannot be checked in the direction that
matters.

**A CONCURRENCE, NOT AN AUTHORITY.**
`docs/handoff/08_point_4_pre_registration.md` Appendix M.4 reached the first
reason from a different direction — n inflation under train overlap — and required
that "the sweep report must state which population every pooled figure is computed
over". **That document is the superseded Point 4's pre-registration and is not
binding**; the rule above is committed on the grounds given above. The agreement is
recorded because two derivations reaching one rule is a check on both.

### 5.4 WHAT TRAVELS TO 4.3

**NAMED AND NOT DECIDED:**

- **WHETHER ANY REPORTABLE QUANTITY MAY BE DENOMINATED IN TRADE COUNT AT ALL.**
  §5.2 establishes what the denominator is a function of; whether a metric should
  therefore avoid it, and what it should use instead, is a question about what the
  metric means. **4.3's.**
- **WHETHER A COUNT-DENOMINATED FIGURE AND A TIME-DENOMINATED ONE ANSWER THE SAME
  QUESTION.** The shapes differ and this document does not choose between them.
  **4.3's.**

**AND §5.5's ADEQUACY HALF IS UNMOVED.** `docs/design/04_2b_point_4_decomposition.md`
§5.2 records it as bearing on 4.4's adequacy reasoning. **This document does not
touch it.**

---

## 6. WHAT A COMPARISON BETWEEN PERIODS SUPPORTS

### 6.1 WHAT IT CAN INDICATE

**THE FOLDS ARE A TIME-VARIATION DIAGNOSTIC** — `docs/design/04_2a_artifact_containment.md`
§2.4 — **and a comparison between two periods' figures is evidence about variation
over time.** That is what the diagnostic is for and this document does not narrow
it.

**THE FORM THE EVIDENCE TAKES IS DESCRIPTIVE.** A difference between two cells
says the run behaved differently across those two calendar spans, under whatever
conditions each span contained, including the state of the book. **That is a real
and useful thing to know**, and a decomposition that shows a figure inverting in
one cell is showing something a run-level figure conceals.

**AND IT IS EXACTLY WHAT `docs/design/04_1c_consequences_and_thresholds.md` §3.3
ALREADY REQUIRES BE REPORTED**: "A pooled verdict that conceals a fold in which the
advantage inverts is a verdict that hides its own weakest evidence. It is reported
and read; it does not aggregate into the condition." **Reported and read is exactly
the status this section confirms.**

### 6.2 WHAT IT CANNOT SUPPORT

> ### **NO INFERENTIAL PROCEDURE THAT TREATS THE PERIODS AS INDEPENDENT
> ### OBSERVATIONS IS ADMISSIBLE.**

**THREE INDEPENDENT GROUNDS, ANY ONE OF WHICH IS SUFFICIENT.**

**FIRST — ONE BUDGET PATH AND ONE POSITION SEQUENCE.** The periods are consecutive
segments of a single continuous run (`docs/design/04_2c_run_structure.md` §2.6).
Each period's taken population depends on what the preceding calendar time left
open, and by §5.6 that depends on realised outcomes. **Segments of one path are not
draws from a population.**

**SECOND — THE DENOMINATORS ARE NOT EXCHANGEABLE.** §5.2: the cell sizes vary with
capacity and the cell compositions shift with a known direction. **Observations
whose selection probability depends on the state of the system are not independent
observations of it.**

**THIRD — THE SEGMENTS ARE CONSECUTIVE IN TIME.** Whatever serial structure the
market itself carries is uncontrolled across adjacent cells. **This ground holds
even if the first two were somehow answered**, and it is stated so that a later
reader does not suppose that removing the budget would restore independence.

**WHAT THIS FORECLOSES, NAMED SO THAT THE FORECLOSURE IS CHECKABLE:**

- **MAJORITY-OF-NINE RULES** and any variant — best-of, worst-of, k-of-nine.
- **PER-PERIOD SIGNIFICANCE TESTS**, and any procedure whose validity rests on
  independence between cells.
- **ANY COUNT OF HOW MANY PERIODS CLEAR A THRESHOLD**, used as evidence of
  anything. The count is arithmetic on nine numbers; **what it is not is a tally of
  successes.**
- **ANY DISPERSION FIGURE COMPUTED ACROSS THE NINE CELLS AND READ AS SAMPLING
  ERROR.** Reading it as a description of how much the cells differ is §6.1 and is
  permitted; reading it as an estimate of uncertainty about the run-level figure is
  this ground and is not.

**THE FORECLOSURE IS ABOUT INFERENCE AND NOT ABOUT REPORTING.** Nothing here
prevents a per-period figure being computed, tabulated, read or discussed. **What is
foreclosed is a procedure that converts nine numbers into a verdict by counting
them.**

### 6.3 THE UNASSIGNED ROW IS NOT A TENTH PERIOD

**IT IS PART OF THE PARTITION AND IT IS NOT A CELL OF THE DIAGNOSTIC.** It spans
roughly nine months against test windows of roughly three, it is a leading residue
rather than a scheduled span, and treating it as a tenth observation would be a
counting procedure of exactly the kind §6.2 forecloses.

**IT IS REPORTED, READ, AND INCLUDED IN THE RECONSTRUCTION IDENTITY.** That is its
whole role.

### 6.4 THE CONSEQUENCE FOR KILL CONDITIONS, WHICH 4.4 OWES

**`docs/design/04_1c_consequences_and_thresholds.md` §3.3 CHOSE THE POOLED LEVEL
FOR CONDITION (d) AND GAVE TWO REASONS.** The first was that a majority rule
misdescribes the folds, resting on `src/folds/schedule.py`'s docstring. The second
was §5.9's — that under a majority rule the verdict turns on the folds where the
stratum is thinnest.

> ### **§6.2 REACHES §3.3's CONCLUSION FROM A DIRECTION THAT KNOWS NOTHING ABOUT
> ### (d).**

**THIS DOCUMENT DOES NOT KNOW WHAT (d) IS, DOES NOT KNOW ITS THRESHOLD, DOES NOT
KNOW ITS STRATUM AND DOES NOT EVALUATE IT.** §6.2 forecloses majority-of-nine for
**every** condition and **every** quantity, on three structural grounds none of
which mentions thinness, forgivingness, or any measured population. **A rule that
reaches the same place while blind to the case cannot have been chosen for what it
does to the case.**

**AND §3.3's FIRST GROUND HAS NOW BEEN REPLACED TWICE.** It rested on a docstring;
`docs/design/04_2a_artifact_containment.md` §2.4 replaced that with a committed
premise; §6.2 adds a third ground from the run structure. **The conclusion stands
on three grounds, two of which postdate it.**

**THE OBJECTION AS ACTUALLY RECORDED, AND A CORRECTION.** §3.3 does not record an
**ordering** objection. What it records is a **forgivingness** objection: "A reader
who holds that the more forgiving level should not be chosen by the party it
forgives is entitled to that objection." **The ordering fact behind it is real** —
report 37 (`eebe986`) measured the candidate stratum before
`04_1c_consequences_and_thresholds.md` (`2a04e37`) chose the level, and §3.4 cites
that measurement — **and it is what gives the recorded objection its force.** The
two are stated separately here because merging them would attribute to §3.3 an
objection it does not make.

> ### **WHAT §6.2 RETIRES IS THE OBJECTION AS DIRECTED AT THE LEVEL.** POOLING IS
> ### NOW FORCED, NOT CHOSEN, SO IT CANNOT HAVE BEEN CHOSEN FOR BEING FORGIVING.

**WHAT IT DOES NOT RETIRE, STATED SO THE DISCHARGE IS NOT READ WIDER THAN IT IS:**

- **§3.4's CONCERN**, which that document records as **reduced and not eliminated**
  — the taken stratum's size is unknowable before the run. **Untouched.**
- **(d)'s THRESHOLD**, which §3.5 records as already committed in the thesis and
  not this chain's to set. **Untouched.**
- **WHETHER (d) IS EVALUABLE AT ALL**, routed by §3.5 to the first-run diagnostic
  gate. **Untouched, and 4.6's.**

---

## 7. REPORTING OBLIGATIONS THIS DOCUMENT COMMITS

### 7.1 THESE ARE COUNTS, NOT OUTCOME QUANTITIES

**STATED FIRST SO THE SECTION IS NOT READ AS REACHING PAST THE FIREWALL.**

> ### EVERY OBLIGATION BELOW IS A **COUNT OF POSITIONS OR OF EXCLUSIONS.** NOT ONE
> ### OF THEM REQUIRES AN EXIT TO BE RESOLVED, A LEVEL TO BE EVALUATED OR AN
> ### OUTCOME TO BE READ.

**THE PRECEDENT IS ALREADY IN THE CHAIN.**
`docs/design/04_1c_consequences_and_thresholds.md` §3.5 routes a population size to
the first-run diagnostic gate on exactly this ground: "the taken non-floor-bound
stratum's **size** is a count, not an outcome quantity, and can be reported by that
gate before any advantage is computed."

**COUNTS UNDER THE BUDGET ARE PATH-DEPENDENT WITHOUT BEING OUTCOME QUANTITIES.**
By §5.6 the taken population depends on realised outcomes, so these counts cannot
be known before the run. **That makes them unknowable in advance; it does not make
them outcomes.** The distinction is the one the firewall draws and this section
stays on the permitted side of it.

### 7.2 M.3's SECOND LIMB — ADOPTED, AFRESH

`docs/handoff/08_point_4_pre_registration.md` Appendix M.3 requires that the
holdout-boundary-excluded count be **reported per fold per symbol**.
`docs/design/04_2c_run_structure.md` §4.4 adopted M.3's first limb — the exclusion
itself — on its own grounds and passed the second here, named as travelling.

> ### **ADOPTED.** THE SEAL-CROSSING EXCLUSION COUNT IS REPORTED, **PER PARTITION
> ### CELL AND PER SYMBOL.**

**REPORT 8 IS THE SUPERSEDED POINT 4's PRE-REGISTRATION AND IS NOT BINDING.** This
is an adoption afresh, on the ground below, and M.3's agreement is a concurrence.

**THE GROUND.** `docs/design/04_2c_run_structure.md` §4.5 commits the evaluation
population as a rule and states that a count computed later which disagrees with
the rule is a finding. **A rule that excludes some candidates and reports nothing
about the exclusion cannot be checked against the run**, and the exclusion sits at
the one place where a silent loss is most plausible — the window's far edge, where
`portfolio.py` currently has no boundary test at all. **The count is what makes
§4.4's rule falsifiable.**

**RESHAPED TO THE COMMITTED PARTITION AND THE RESHAPING IS DISCLOSED.** M.3 says
"per fold". §3.2 commits the partition as nine test windows plus the unassigned
row, and the eighteen-period decomposition does not sum (§4.2), so **"per fold"
becomes "per partition cell"**. **Per symbol is carried unchanged**, and is the
right grain because the exclusion depends on entry timing, which differs by symbol.

### 7.3 WHICH COUNTS ARE REPORTED EVEN WHEN ZERO

**THE RULE THIS FOLLOWS IS REPORT 28 §6.2's**, quoted verbatim and adopted as a
requirement by `docs/design/06a_exit_resolution_spec_amendment_1.md` §5.3
requirement 2:

> "**REPORTED AS ZERO RATHER THAN OMITTED.** A branch that is never reported is a
> branch nobody can tell was checked."

> ### **THE FOLLOWING ARE REPORTED FOR EVERY CELL OF THE PARTITION AND EVERY
> ### SYMBOL, INCLUDING CELLS WHERE THE VALUE IS ZERO:**
>
> 1. **THE POSITION COUNT** — the denominator §5.3 requires, which is also the
>    cell's entry in the reconstruction identity.
> 2. **THE SEAL-CROSSING EXCLUSION COUNT** — §7.2.

**AND THE UNASSIGNED ROW IS REPORTED WHETHER OR NOT IT IS EMPTY**, per §3.3. It is
not expected to be empty; the rule is written so that its being reported does not
depend on anyone's expectation.

**WHY ZERO MUST APPEAR.** A count that appears only when non-zero tells a reader
nothing when absent: absence is ambiguous between "zero" and "not checked", and the
reader cannot distinguish them. **The seal-crossing count is the case where this
bites hardest**, because it is expected to be zero or near-zero in most cells, so
omission-when-zero would produce a report in which the exclusion is invisible
almost everywhere and indistinguishable from an exclusion that was never
implemented — which, in `portfolio.py`, it currently is not.

### 7.4 WHAT IS NOT COMMITTED HERE

**THE REFUSAL COUNT** — signals skipped for want of budget — is a count and not an
outcome, and it is the quantity that would make §5.2's capacity story directly
visible. **It is not committed here.** It belongs with the first-run diagnostic
gate, on the model `docs/design/04_1c_consequences_and_thresholds.md` §3.5 sets,
and this document names it as bearing on **4.6** rather than claiming it.

---

## 8. §5.7 — R-MULTIPLE WEIGHTING

### 8.1 WHAT §5.7 SAYS, READ

`docs/handoff/31_point_5_closing.md` §5.7: "**Whether R multiples are
equal-weighted or dollar-weighted is undecided.** Report 28 §7 stores both
`nominal_risk_usd` and `realised_risk_usd` per position and neither is derived
from the other at read time, precisely so that this choice remains open. **It is a
validation-design choice with a direct effect on every aggregate**, and flooring
drag of 0.80% is the size of the wedge between them."

**VERIFIED AGAINST REPORT 28 §7 RATHER THAN TAKEN ON THE SUMMARY.** That section,
"DUAL RISK RECORDING", stores `nominal_risk_usd` as "$20.00, the figure the budget
charges" and `realised_risk_usd` as "`qty x d`, the true 1.0R denominator **for
that trade**". **The two fields and their stated purposes are as §5.7 describes.**

### 8.2 THE SPLIT

**THE AGGREGATION HALF IS REAL BUT IT IS THIN, AND ITS THINNESS IS THE FINDING.**

**IT IS THIS: WHATEVER OPERATOR 4.3 CHOOSES, THREE CONSTRAINTS BIND ON IT.**

1. **THE SAME OPERATOR AT EVERY LEVEL.** Equal-weighted at the run level and
   size-weighted per period, or the reverse, would make §2.3's defect test fire on
   a correct run. **The operator is a property of the quantity, not of the level.**
2. **THE RUN-LEVEL FIGURE IS COMPUTED DIRECTLY OVER THE RUN'S POSITIONS**, never
   reconstructed from cell figures. **This is §2.1 and it is what makes the choice
   safe at all**: neither operator is associative across a partition — an
   equal-weighted mean over the run is not the unweighted mean of nine
   equal-weighted cell means unless the cells are equal in size, and §5.5 says they
   are pinned by capacity rather than equal. **A combining design would have made
   the equal-versus-size choice interact with the partition. Under §2 it does not
   interact with it at all.**
3. **THE DENOMINATOR TRAVELS**, per §5.3 — the count for an equal-weighted
   operator, the total risk deployed for a size-weighted one. **They are different
   denominators and a reader must be told which.**

> ### **THE SUBSTANCE — WHICH OPERATOR — IS WHOLLY 4.3's, AND IS HANDED ON
> ### UNDECIDED.**

**THE REASON IS THE §1.2 TEST, APPLIED TO ITSELF.** Choosing between the two
requires knowing what the aggregate is supposed to answer: whether a position's
contribution should scale with the capital at risk on it depends on what the
quantity means. **That cannot be settled without naming the quantity, and naming it
is the line.** Further, which of `nominal_risk_usd` and `realised_risk_usd` sits in
a per-trade R's denominator is a **definition of the metric**, not an aggregation
rule — report 28 §7 records that `realised_risk_usd` is what makes a stop return
exactly -1.0R in that trade's own unit.

**WHAT THE AGGREGATION HALF DOES NOT DO IS NARROW 4.3's CHOICE.** Both operators
satisfy all three constraints. **The half is discharged by constraining the choice
rather than by making it**, and if that reads as a small return on the item, that
is the accurate report: under §2's inversion most of §5.7's difficulty evaporated,
and the residue is a metric question that was always a metric question.

---

## 9. THE LEDGER AND THE OPEN ITEMS

### 9.1 THE LEDGER

**THE TOTAL, READ:** `docs/design/04_2c_run_structure.md` §7.1 states the total read
is **50** and logs no instance, leaving it unchanged. **The total read is 50**, so
the instance below takes **(51)**.

### 9.2 INSTANCE (51)

**A CITATION TO A SECTION THAT DOES NOT EXIST IN THE DOCUMENT CITED.**

The instruction that produced this document directed that the zero-reporting rule
be followed on the model of **`docs/design/06a_exit_resolution_spec_amendment_1.md`
§6.2's treatment of a zero-valued branch.**

**THAT DOCUMENT HAS NO §6.2.** Its §6 is "THE CONSTANTS" and its only sub-section
is §6.1. **The rule is report 28 §6.2's**, quoted verbatim and adopted as a
requirement by that amendment at **§5.3, requirement 2**. A reader following the
citation as given would find nothing, and following it into document 06 instead
would find §6.2 "The rate, and the sign", which is unrelated.

**THE CONTENT CLAIM WAS CORRECT.** A zero-valued-branch rule of exactly the
described character exists and is adopted at §7.3 above. **Only the location was
written from a mental model rather than from the document.**

**SUB-CLASS: instance (50)'s** — a statement about what a document says, written
from a mental model of it — **which is itself the recurring class applied to a
citation**, per `docs/design/04_1c_denominator_choice.md` §5.5 on instance (43).

**WHY THIS IS LOGGED WHEN LAST STEP'S SLIP WAS NOT, AND THE TEST IS STATED SO THE
TWO CAN BE CHECKED FOR CONSISTENCY.** `docs/design/04_2c_run_structure.md` §7.1
recorded a section-number slip and declined to log it: there the cited section
existed and held one of the two facts correctly, the other being one heading later
in the same document. **Here the cited section does not exist**, and under
`docs/design/04_1a_denomination.md` §6's criterion the remediation on offer —
adopting the citation as given — **would have degraded an otherwise correct
artifact**, by planting a citation to a non-existent section in a document joining
the frozen specification.

> ### THE DISTINGUISHING TEST: WOULD ADOPTING THE CLAIM UNCHECKED HAVE PUT
> ### SOMETHING FALSE INTO A COMMITTED ARTIFACT? LAST STEP, NO — A READER WOULD
> ### HAVE FOUND THE FACT ONE HEADING AWAY. HERE, YES.

**AND THE RATE IS NOW WORTH NAMING.** This is the third citation error carried by
an instruction into this chain, after the report-33-for-32 attribution corrected at
`docs/design/04_1c_consequences_and_thresholds.md` §4.2 and the §3.2-for-§3.3 slip
recorded at `docs/design/04_2c_run_structure.md` §5.3. **Two of the three fell in
consecutive steps.** The pattern `docs/design/04_2b_point_4_decomposition.md` §7.2
names holds: an instruction's factual claims about the repository are not evidence
about the repository.

### 9.3 THE TOTAL

**50 + 1 = 51.**

**No earlier instance is renumbered or recounted**, and the ledger remains
contiguous from (1) to (51).

### 9.4 THE OPEN ITEMS REGISTER — THIS DOCUMENT'S ENTRIES

**RECORDED IN THE FORM `docs/design/04_2b_point_4_decomposition.md` §5 USES. THAT
DOCUMENT IS NOT EDITED.**

**DISCHARGED:**

- **`docs/handoff/31_point_5_closing.md` §5.5's AGGREGATION HALF**, routed here by
  `docs/design/04_2c_run_structure.md` §5.3. **Discharged at §5.2 and §5.3**: the
  effect of a capacity-driven denominator on a between-period comparison is stated,
  including the composition shift, and the denominator is required to travel with
  every figure. **Its metric half travels to 4.3 (§5.4); its adequacy half remains
  4.4's, unmoved.**
- **§5.6's 4.2d RESIDUE**, named at `docs/design/04_2c_run_structure.md` §3.4 —
  that no per-period quantity is a sample from a fixed population, so aggregation
  must proceed knowing the populations are path-determined and not exchangeable.
  **Discharged at §2 and §6.2**: there is no aggregation across periods to perform,
  and no procedure treating them as exchangeable is admissible.
- **`docs/handoff/31_point_5_closing.md` §5.7's AGGREGATION HALF.** **Discharged at
  §8.2** as three constraints binding on whatever operator is chosen.

**TRAVELLING, NAMED AND NOT DECIDED:**

- **§5.7's SUBSTANCE — equal- or size-weighted. Wholly 4.3's** (§8.2). Its register
  entry moves from "attached to 4.2 with a hand-off to 4.3" to "aggregation half
  discharged; substance handed to 4.3 undecided."
- **§5.5's METRIC HALF — whether any quantity may be denominated in trade count.
  4.3's** (§5.4).
- **THE REFUSAL COUNT — a count, not an outcome, not committed here. Bearing on
  4.6's first-run diagnostic gate** (§7.4).

**ADOPTED AFRESH:**

- **APPENDIX M.3's SECOND LIMB**, passed here by
  `docs/design/04_2c_run_structure.md` §4.4. **Adopted at §7.2** on this document's
  own ground, reshaped from "per fold" to "per partition cell" and disclosed as
  reshaped. **Report 8 remains non-binding.**

**RETIRED:**

- **THE FIFTEEN CROSS-OVERLAPS AND THE 49.5 TO 50.3 PER CENT TRAIN OVERLAP**,
  inherited at `docs/design/04_2c_run_structure.md` §5.3. **They bind on nothing
  computed over the partition** (§4.1); they bind only on forbidding arithmetic
  across the eighteen-period decomposition's rows (§4.2), and they are retired
  against any future attempt to treat periods as independent trials (§4.3).

**NOTHING ELSE IN THE REGISTER MOVES.**

---

## 10. WHAT THIS DOCUMENT DOES NOT DO

**NO METRIC, NO LEVEL, NO THRESHOLD.** §1.3 states them and no section supplies
one. §8.2 declines to choose between two operators for precisely this reason, and
says so rather than choosing quietly.

**IT DOES NOT TOUCH KILL CONDITION (d)** beyond §6.4's statement about the ground
for its level, and §6.4 names three things it explicitly does not retire.

**IT DOES NOT REARGUE** the run structure, the evaluation population or the fold
interpretation.

**IT ESTABLISHES NO COUNT.** Every figure is cited from a committed record. Nothing
is computed, no population is opened, no engine entry point is invoked, and no
artifact under `docs/design/04_2a_artifact_containment.md` §3's prohibition is
touched.

**IT DOES NOT EDIT CODE**, and it identifies no new divergence. The one open
divergence bearing on §7.2 — `portfolio.py`'s missing seal-crossing exclusion — is
`docs/design/04_2c_run_structure.md` §7.2's item and is not restated as new.

---

## 11. CHANGE DISCIPLINE

**THIS DOCUMENT JOINS THE FROZEN SPECIFICATION ON COMMIT.** It is amended by a new
document that names it, states what changes and states why. **It is not edited in
place**, and an error found in it is logged as an erratum rather than patched.

**§2's INVERSION IS THE LOAD-BEARING COMMITMENT.** §3, §4, §5.3, §6.2 and §8.2 all
depend on it. **A document reopening any of them must reopen §2 first**, and must
say what about the run structure changed to make the run-level quantity no longer
primary.
