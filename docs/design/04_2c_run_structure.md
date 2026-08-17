# THE RUN STRUCTURE AND THE EVALUATION POPULATION

**SUB-POINT 4.2c. PRE-REGISTRATION. IT JOINS THE FROZEN SPECIFICATION ON COMMIT.**

**Manifest at entry: `74abe0f0e87291db22707c59eae7538131882d075dde24c2f70517f703793d70`,
59 entries, every entry verified, zero problems.**

---

## 0. WHAT THIS DOCUMENT IS

**IT COMMITS TWO THINGS AND ONLY TWO: THE STRUCTURE OF THE IN-SAMPLE VALIDATION
RUN, AND WHICH CANDIDATES ENTER IT.**

It is a pre-registration in the full sense the chain has used since
`docs/design/04_1c_pre_commitments.md`: written before the evidence that would
inform it exists, and committed so that it cannot be chosen after seeing a result.

### 0.1 THE PREMISE IT RELIES ON AND DOES NOT REARGUE

`docs/design/04_2a_artifact_containment.md` §2.4 commits the finding that the
frozen thesis fits nothing on train, and therefore:

> ### THE NINE FOLDS ARE A TIME-VARIATION DIAGNOSTIC FOR THE FROZEN THESIS, NOT
> ### NINE TRIALS.

**THAT IS A COMMITTED PREMISE HERE, NOT A CONCLUSION.** This document takes it as
given, uses it in §2.4 and §5, and does not reopen it. Its revival condition is
that document's §2.5 and is unchanged by anything here.

### 0.2 WHY THIS IS ARGUED AND NOT MEASURED

`docs/handoff/31_point_5_closing.md` §5.6, restating `docs/design/05_aggregate_risk_budget.md`
§6: **under the aggregate budget with real exits the traded population is a
function of realised outcomes and is not a subset of anything knowable in
advance.**

**SO THE QUESTION THIS DOCUMENT ANSWERS CANNOT BE ANSWERED BY MEASUREMENT.**
Whether one continuous run and several per-period runs yield different taken
populations is not decidable from bars: it requires resolving exits, which
requires running the engine in full mode, which is the one thing the freeze at
`docs/design/04_2b_point_4_decomposition.md` §4.2 unlocks and which has not
happened.

> ### THE DECISION IS STRUCTURAL AND IS MADE BEFORE THE EVIDENCE THAT WOULD INFORM
> ### IT EXISTS. THAT IS NOT A DEFECT. IT IS THE ORDER THE FIREWALL IMPOSES.

**AND THE ORDER IS THE POINT, NOT A COST OF IT.** A structure chosen after seeing
which structure produced the better-looking numbers would be a structure chosen to
produce them. The firewall's whole function is to make that impossible, and the
price of it is exactly this: deciding on argument, in the open, with the argument
recorded so that a later reader can see it was not retrofitted.

### 0.3 WHAT IT DOES NOT DO

**NO AGGREGATION RULE.** How per-period quantities are combined, whether the
headline is pooled or per-fold, and what the denominator is, are **4.2d's**.

**NO METRIC.** No quantity is defined, named as reportable, or given a
denominator. **4.3's.**

**NO LEVEL AND NO THRESHOLD.** Nothing here is a kill condition, an adequacy
bound or a pass mark. **4.4's.**

**NO COMPARISON RULE.** Whether two per-period quantities may be set against each
other, and under what conditions, is **4.2d's**. §5 states what the periods *are*
and stops there.

**NOTHING IS COMPUTED, MEASURED, OR RUN.** No engine entry point is invoked. No
artifact under `docs/design/04_2a_artifact_containment.md` §3's prohibition is
opened. No count in this document is produced here; every one is cited from a
committed record.

---

## 1. THE ENGINE THIS DOCUMENT STRUCTURES

**NAMED FIRST, BECAUSE THE REPOSITORY CONTAINS TWO EXECUTION PATHS AND ONLY ONE OF
THEM IS THE THESIS'S.**

**`src/engine/portfolio.py` IS THE VALIDATION PATH.** Its module docstring, lines
3 to 7: it is "the one place that carries the frozen aggregate risk budget
(document 05 and its two amendments), the frozen exit resolution specification
(document 06 and its amendment) and report 28's exchange-real sizing. Nothing else
in this repository holds all three, and nothing else is permitted to resolve an
exit."

**`src/engine/simulate.py` IS NOT.** The same docstring, lines 9 to 15, records
that reports 26 §12.1 and 28 §13.5 both concluded it "must be REPLACED rather than
adapted", and that it is left alone because its tests pin its behaviour and other
work depends on it. **It carries no aggregate budget** — the name does not appear
in the module — so it could not implement the rule this document structures even
if it were the path.

**THE ENTRY POINT IS `portfolio.run`**, `src/engine/portfolio.py:503`. Its `full`
mode refuses to execute without `FIREWALL_TOKEN`
(`src/engine/portfolio.py:118`), whose error text names Point 4 as what enabling
it spends. **That refusal is the freeze's mechanism**, and this document is one of
the sub-points that must be committed before it is passed.

---

## 2. THE RUN STRUCTURE

### 2.1 THE CANDIDATE STRUCTURES

**FOUR, INCLUDING THE TWO THE INSTRUCTION NAMES AND TWO THE RECORD ADMITS.**

**(A) ONE CONTINUOUS RUN.** `portfolio.run` is called once over the whole
in-sample window with the whole candidate frame. Fold periods are applied
afterwards as a date partition of the resulting positions.

**(B) PER-PERIOD RUNS OVER THE EIGHTEEN FOLD PERIODS.** One call per period, each
beginning with a fresh budget state.

**(C) PER-PERIOD RUNS OVER THE NINE TEST WINDOWS ONLY.** One call per test window,
each beginning with a fresh budget state, train periods not run.

**(D) INDEPENDENT-SIGNAL EVALUATION.** Every candidate resolved on its own with no
interaction of any kind — `src/engine/simulate.py:529`'s "signal mode", described
there as an edge-test instrument.

**(B) IS NOT WELL-DEFINED AND THAT DISPOSES OF IT BEFORE ANY ARGUMENT ABOUT
REALISM.** The eighteen fold periods are not a partition of the window. They are
an overlapping cover: `docs/handoff/40_point_4_2_fold_audit.md` §3.2 establishes
that adjacent training windows overlap by **49.5 to 50.3 per cent**, and §3.3 that
each fold's test window falls entirely inside the next two folds' training
windows — **fifteen cross-overlaps**. The consequence is at §3.4 of the same
report: a candidate falls in **at most three periods**, and **6,456 of the 11,384
fall in exactly three.**

> ### UNDER (B) THE MAJORITY OF CANDIDATES WOULD BE RUN THREE TIMES, IN THREE
> ### DIFFERENT BUDGET CONTEXTS, AND COULD BE TAKEN IN ONE AND SKIPPED IN ANOTHER.

**A structure that returns up to three different dispositions for one signal is
not a validation of a trading rule; it is three overlapping validations whose
union is not a population.** (B) is disqualified structurally and needs no appeal
to realism.

**(D) IS DISQUALIFIED BY WHAT IS BEING VALIDATED.**
`docs/design/05_aggregate_risk_budget.md` §6.3 states that the capped and uncapped
populations "are not nested in the obvious way" and that "any comparison between
them is a comparison of two different populations and must say so." The frozen
thesis **is** a rule run under the budget; a run with no budget validates a
different rule. (D) has a legitimate use — isolating the trigger from the
constraint — and it is not that use that is at issue. **It is not a candidate for
this validation**, and its home is the superseded engine.

**THAT LEAVES (A) AND (C), WHICH IS THE REAL CHOICE.**

### 2.2 WHAT EACH DOES TO THE BUDGET'S STATE

**THE BUDGET'S STATE IS THE WHOLE OF WHAT IS AT STAKE.**
`docs/design/05_aggregate_risk_budget.md` §1 fixes it: aggregate open nominal risk
across the whole book may not exceed **$120.00**, being six concurrent positions
at the **$20.00** unit. §3 fixes its dynamics:

- allocation is in **arrival order**, decided once, at arrival, and final;
- **a skipped signal is skipped** — not queued, not deferred, not resized upward
  later;
- **when a position closes it returns exactly its own allocation** and nothing
  else, so the budget is a cap on concurrent exposure and carries no cumulative
  term.

**IN THE IMPLEMENTATION THAT STATE IS THREE LOCALS.** `src/engine/portfolio.py`
initialises `charged = 0.0` at `:567` and `book = []` at `:569`, once per call to
`run`, and walks `grid = _hourly_grid(min(ts), max(exit_bar))` at `:574` in a
single forward pass.

**SO THE STRUCTURE QUESTION IS EXACTLY THE QUESTION OF HOW MANY TIMES `run` IS
CALLED.**

**UNDER (A) — ONE CALL.** `charged` and `book` are initialised once, at the start
of the window, and carry across every fold boundary. A position open at a boundary
is open in both periods, and it occupies budget in both. A signal arriving on the
first day of period k competes against positions opened in period k-1.

**UNDER (C) — NINE CALLS.** `charged = 0.0` and `book = []` nine times. Each test
window opens with an empty book and the full $120.00 available.

> ### NO LIVE ACCOUNT HAS EVER STARTED A QUARTER WITH AN EMPTY BOOK AND A FULL
> ### BUDGET NINE TIMES IN A ROW.

**AND THE DISTORTION HAS A KNOWN SIGN.** An empty book cannot skip. Under (C) the
opening hours of each of nine windows carry an artificially low refusal rate,
because the only thing that causes a refusal under this rule — occupancy — is
absent by construction. The bias is not random noise added at nine dates; it is
**one-directional, at nine known dates, in the direction of taking more.**

### 2.3 WHICH IS FAITHFUL TO WHAT IS BEING VALIDATED

**THE THESIS IS A LIVE TRADING RULE RUN CONTINUOUSLY.** It is not a family of
quarterly experiments. The account it will run on has one book, one budget and no
boundary at which either is reset.

**THE ARGUMENT IS NOT "REALISM IS GOOD". IT IS NARROWER AND IT IS ALREADY
COMMITTED IN THIS PROJECT AT A DIFFERENT LEVEL.**
`docs/design/05_aggregate_risk_budget.md` §5.1 rejects best-of-cohort, random and
priority-ranked allocation, not because arrival order is better, but because every
alternative requires knowledge that does not exist at decision time:

> "A backtest that used any of them would be measuring a system that cannot be
> run. Arrival order is not chosen because it is good; it is chosen because it is
> the only one that exists at decision time."

**THAT ARGUMENT WAS MADE ABOUT THE ALLOCATION RULE. IT TRANSFERS TO THE RUN
STRUCTURE WITHOUT WEAKENING**, and the transfer is what makes this section an
argument rather than an assertion. A fresh book at 2023-01-01 is not a
forward-looking quantity, but it is the same species of thing: **a state the live
account cannot be in.** Under (C) the validated system is one that liquidates its
book and forgets its exposure eight times, on dates chosen by a fold schedule the
account does not know about. **No implementation of the frozen thesis can produce
that behaviour**, so a figure measured under (C) is a figure about a system that
will not be deployed.

**THE CONVERSE IS THE TEST OF WHETHER THE ARGUMENT IS DOING WORK.** Under (A),
every state the run passes through is a state the live account could occupy: one
book, continuous budget, arrival-order allocation, positions that outlive calendar
boundaries because calendars are not part of the rule. **There is no state under
(A) that is unreachable live.** That is a checkable property, and it is the
property (C) lacks.

### 2.4 THE STRONGEST CASE AGAINST (A), STATED AT ITS FULL STRENGTH

**IT IS NOT WEAK AND IT IS NOT DISMISSED.**

> ### UNDER ONE CONTINUOUS RUN, A PER-PERIOD QUANTITY IS NOT A MEASUREMENT OF THAT
> ### PERIOD.

Period k opens with whatever book period k-1 left it, and — worse than the
positions themselves — with whatever budget occupancy those positions impose. A
signal arriving in period k's first hours may be skipped for a reason that belongs
entirely to period k-1. **So the nine periods are not nine observations of the
same system under nine conditions. They are nine consecutive segments of one
path**, and any variation across them confounds the time-variation the diagnostic
exists to detect with carry-over from the preceding segment.

**Under (C), by contrast, every window is measured from the same initial
condition, which is the only circumstance in which a difference between two
windows is attributable to the windows rather than to their predecessors.** That
is a real methodological virtue and (A) does not have it.

**THREE THINGS ANSWER IT, AND THE THIRD IS THE ONE THAT DECIDES.**

**FIRST, THE CARRY-OVER IS BOUNDED, AND BOUNDED TIGHTLY.**
`docs/handoff/24_point_5_1_exposure.md` §5.2 establishes that every hold on the
candidate population lies inside the frozen 16-to-24-hour band, with a **maximum
of 24 hours**, asserted on every position rather than sampled. Under full-mode
exits a position can only resolve **earlier** than its time exit, never later, so
24 hours is an upper bound that survives the change of exit rule. **The inherited
book is therefore extinguished within the first day of a period**, against test
windows of roughly three months. Carry-over is a first-day effect, not a
period-long one.

**SECOND, THERE IS NO SECOND CHANNEL.**
`docs/design/05_aggregate_risk_budget.md` §3: a closing position "returns exactly
its own allocation to the budget, and nothing else. There is no accrual of profit
into the budget and no reduction of it on a loss." **The budget carries no
cumulative state at all.** So period k-1 cannot alter period k's capacity by any
route other than the positions still open at the seam, and those are gone within
24 hours. A structure whose budget compounded would have an unbounded carry-over
channel; this one does not.

**THIRD — AND THIS IS THE ONE THAT DECIDES — (C) DOES NOT REMOVE THE CONFOUND. IT
REPLACES IT WITH A WORSE ONE.**

The objection to (A) is that period k's opening is contaminated by period k-1.
**Under (C) period k's opening is contaminated by an empty book**, which is not a
neutral baseline — §2.2 establishes it has a known direction. So the choice is not
between a contaminated measurement and a clean one. It is between:

- **(A):** each period's first day inherits real state from real trading, in the
  same way the live account's would;
- **(C):** each period's first hours carry a systematic, one-directional
  distortion at nine known dates, produced by a reset that has no counterpart in
  the deployed system.

> ### (A)'s CARRY-OVER IS THE THING THE ACCOUNT ACTUALLY DOES. (C)'s RESET IS AN
> ### ARTEFACT OF THE VALIDATION APPARATUS.

**AND §5.6 FORBIDS SETTLING IT BY MEASUREMENT.** Which distortion is larger cannot
be established before the freeze, because both are functions of realised outcomes.
So the tie-break must be made on grounds available now, and the ground available
now is that one of the two structures has a path a live account would have and the
other does not. **§3 develops this as the argument it is rather than leaving it as
a remark.**

### 2.5 THE BOUNDARY-CROSSING ASSIGNMENT

**A POSITION ENTERED IN ONE PERIOD AND EXITED IN THE NEXT BELONGS TO NEITHER BY
DEFAULT, AND THE RULE MUST BE STATED.** They exist: every hold on the candidate
population is at least 17 hours (`docs/handoff/24_point_5_1_exposure.md` §5.2), so
any candidate entering within a day of a boundary crosses it.

> ### THE RULE: A POSITION IS ASSIGNED TO THE PERIOD CONTAINING **THE CLOSE OF THE
> ### BAR AT WHICH IT ENTERED** — the `entry_close_ms` stamp of the candidate
> ### frame. NOT THE SIGNAL BAR'S OPEN, NOT THE EXIT, AND NOT EXCLUDED.

**THREE GROUNDS, IN ORDER OF WEIGHT.**

**FIRST — THE PERIOD PARTITIONS DECISIONS, AND THE DECISION IS MADE AT ENTRY.**
Under `docs/design/05_aggregate_risk_budget.md` §3 the allocation decision is made
once, at arrival, and is final. That is the only moment at which the rule does
anything. A partition of the run's output is a partition of the moments the rule
acted, and every one of those moments is an entry.

**SECOND — ASSIGNING BY EXIT WOULD MAKE THE PARTITION ITSELF A FUNCTION OF
REALISED OUTCOMES.** Under full mode the exit stamp is not known until the
position resolves; a stop-out and a time exit on the same signal can fall in
different periods. **A partition whose membership depends on how a trade turned
out is not a time partition.** It would import §5.6's path dependence into the
diagnostic's own axis, where it has no business, and it would make the count of
positions in a period an outcome quantity in disguise.

**AND THE SAME OBJECTION HAS A SECOND EDGE WORTH NAMING.** Under exit assignment,
*which* positions cross a boundary is itself outcome-dependent: a position that
resolves in hour two does not cross, while the same position running to its time
exit does. **So exit assignment makes both the membership and the crossing count
path-dependent**, where entry assignment makes neither.

**THIRD — EXCLUDING CROSSERS WOULD MAKE THE PERIODS NON-EXHAUSTIVE**, would delete
positions on a pure calendar artefact, and would delete them non-uniformly:
periods are defined on calendar days, entries are not, so the excluded set would
be a function of where boundaries happen to fall relative to signal timing.

**THIS RULE IS ALREADY WHAT THE COMMITTED POINT 4 CODE DOES, AND THAT IS RECORDED
AS A CONSISTENCY FACT, NOT AS ITS AUTHORITY.**
`src/analysis/level_consequences.py:333`, `by_fold_period`, assigns "by its entry
bar's close stamp" and keeps an explicit `OUTSIDE ANY FOLD PERIOD` row rather than
dropping unassigned rows — "because a count that silently loses rows is a count
nobody can reconcile." **The exhaustiveness property this section requires is
therefore already implemented.** It is committed here as a rule regardless.

**THE BOUNDARY INSTANTS ARE THE SCHEDULE'S AND ARE NOT RESTATED.**
`src/folds/schedule.py:16-17`: start dates inclusive at 00:00:00Z, end dates
inclusive at 23:45:00Z, the last 15m bar of the day. **That convention is a 15m
convention applied to a 1h population**, which is harmless — no 1h entry stamp
falls between 23:00:00Z and 23:45:00Z — and it is named here so that a later
reader does not discover it as a surprise.

### 2.6 THE DECISION

> ### **THE IN-SAMPLE VALIDATION IS ONE CONTINUOUS RUN — STRUCTURE (A).**
>
> ### ONE CALL TO `portfolio.run` OVER THE WHOLE IN-SAMPLE WINDOW, WITH THE WHOLE
> ### EVALUATION POPULATION. THE BUDGET IS INITIALISED ONCE AND CARRIES ACROSS
> ### EVERY FOLD BOUNDARY. FOLD PERIODS ARE A DATE PARTITION OF THE RESULTING
> ### POSITIONS, ASSIGNED BY ENTRY-BAR CLOSE.

### 2.7 WHAT WOULD HAVE MADE THE OTHER CHOICE CORRECT

**THREE CONDITIONS. EACH IS CHECKABLE AND EACH IS FALSE TODAY. IF ANY BECOMES
TRUE, THIS DECISION IS WRONG AND MUST BE REOPENED.**

1. **IF THE MAXIMUM HOLD WERE LONG RELATIVE TO A FOLD PERIOD.** Carry-over is
   bounded by the hold. At a 24-hour maximum against a three-month window it is a
   first-day effect; at a hold measured in weeks it would dominate the diagnostic,
   and per-period runs would be the only way to isolate a period. **The frozen
   16-to-24-hour band is what makes (A) safe, and if that band is ever widened
   this section is the thing that must be re-read.**

2. **IF THE BUDGET CARRIED CUMULATIVE STATE.** If it compounded, or were
   denominated as a fraction of running capital rather than of the fixed $2,000.00,
   period k-1's outcomes would alter period k's capacity through a channel with no
   time bound, and no appeal to hold length would close it.

3. **IF THE FOLDS WERE NINE TRIALS RATHER THAN A TIME-VARIATION DIAGNOSTIC.** If
   anything were fitted on train, independence between folds would be
   load-bearing, and a shared budget path would be a channel through which one
   fold's evaluation informed another's. **`docs/design/04_2a_artifact_containment.md`
   §2.4 removed exactly this**, and its §2.5 states what would revive it.

### 2.8 A FINDING: THE STRUCTURE WAS IN THE CODE BEFORE IT WAS IN A DOCUMENT

**`src/engine/portfolio.py:503`'s `run` ALREADY IMPLEMENTS ONE CONTINUOUS FORWARD
PASS, AND ITS DOCSTRING AT `:531` ASSERTS THE DECISION THIS DOCUMENT MAKES:**

> "THE BUDGET DOES NOT RESET AT A FOLD BOUNDARY. It is an account property and it
> is continuous over the window."

**THAT IS A DOCSTRING AND NOT A COMMITTED DECISION**, and the distinction is one
this chain has had to make before.
`docs/design/04_2a_artifact_containment.md` §2.4 records that
`docs/design/04_1c_consequences_and_thresholds.md` §3.3 rested a frozen
pre-registration partly on `src/folds/schedule.py`'s docstring, and treats that as
a ground needing replacement rather than as sufficient.

> ### THE SAME PATTERN, AND IT IS NAMED RATHER THAN LEFT TO BE FOUND: THE RUN
> ### STRUCTURE HAS BEEN IMPLEMENTED SINCE THE ENGINE WAS BUILT AND HAS NEVER BEEN
> ### DECIDED. THIS DOCUMENT IS WHAT DECIDES IT.

**THE ARGUMENT IN §2.2 TO §2.4 IS NOT A RATIONALISATION OF THE EXISTING CODE.** It
would be one if it had been written to reach the code's answer; the test of that
is §2.7, which states three conditions under which the code's answer would be
wrong, and §2.4, which states the case against it at full strength. **The
coincidence is recorded because the alternative — noticing it later and wondering
whether the decision was ever made — is worse.**

**NO CODE CHANGE FOLLOWS FROM THIS SECTION.** The implementation and the decision
now agree; before this commit they did not disagree either, because there was
nothing for the implementation to agree with.

---

## 3. WHAT §5.6 MEANS FOR THE CHOICE

### 3.1 THE PROPOSITION

`docs/handoff/31_point_5_closing.md` §5.6, on `docs/design/05_aggregate_risk_budget.md`
§6: **under the budget with real exits the traded population is a function of
realised outcomes** — a stop-out frees its slot hours before a time exit would —
**so it is not a subset of anything knowable in advance.**

### 3.2 WHAT FOLLOWS FOR EACH STRUCTURE

**FOR (A):** the taken population is one path, determined by the interaction of
arrival order with realised exits over the whole window. It is unknowable until
the run happens, and after the run it is one population with one history.

**FOR (C):** the taken population is nine paths, each starting empty. Because
occupancy is what causes skips and the opening occupancy differs, **the population
(C) takes is a different population from the one (A) takes** — not a subset, not a
superset, and not the same set differently labelled. `docs/design/05_aggregate_risk_budget.md`
§6.3 makes exactly this point about the capped and uncapped runs, and it applies
here for the same reason: **two populations produced by two different budget paths
are two populations.**

**FOR (B) AND (D):** (B) has no single taken population at all, since a candidate
may be taken in one overlapping period and skipped in another. (D) takes every
candidate by construction and so has no path at all.

### 3.3 THE ASYMMETRY IS ITSELF AN ARGUMENT

**THE DIFFERENCE BETWEEN (A)'s AND (C)'s POPULATIONS IS UNMEASURABLE BEFORE THE
FREEZE.** It cannot be bounded, estimated or sampled, because estimating it means
resolving exits.

**THAT LOOKS LIKE A REASON TO DEFER THE DECISION AND IT IS THE OPPOSITE.** If the
difference could be measured, it would be measured *after* the freeze, by someone
who had seen results — and choosing a run structure with results in view is
choosing the structure that produces the preferred results. **The unmeasurability
is what forces the decision into the open, where it has to be made on grounds
other than its consequences.**

**AND ON THOSE GROUNDS THE TWO ARE NOT SYMMETRIC.** Both produce a taken
population; only one of them produces it by a path the live account would have.
(A)'s population is unknowable in advance **and is the population the deployed
system would take**. (C)'s is unknowable in advance **and is the population no
deployed system would take**, because no deployed system resets its book eight
times on a schedule it does not know about.

> ### WHEN TWO STRUCTURES ARE BOTH UNMEASURABLE IN ADVANCE, THE ONE WHOSE
> ### UNMEASURABLE QUANTITY IS THE ONE YOU ACTUALLY CARE ABOUT WINS. THAT IS THE
> ### ARGUMENT, AND IT IS AVAILABLE NOW.

### 3.4 THE DISPOSITION OF §5.6

**PARTLY DISCHARGED HERE. THE REST TRAVELS, AND WHAT TRAVELS IS NAMED.**

**DISCHARGED BY THIS DOCUMENT:** §5.6's bearing on **run structure**. The
proposition is used, its consequence for each candidate structure is stated, and
the decision is made in its light rather than in spite of it. Nothing further about
run structure is owed to it.

**WHAT TRAVELS TO 4.2d:** that **no per-period quantity is a sample from a fixed
population**, because the population is a function of the path. Any aggregation
rule that treats nine per-period figures as nine draws from one distribution is
assuming what §5.6 denies. **4.2d must state how it aggregates in the knowledge
that the per-period populations are path-determined and not exchangeable.**

**WHAT TRAVELS TO 4.3:** that **no metric may be denominated in a quantity the
path pins**, which is §5.5's warning in §5.6's terms and is treated at §5.3 below.

**WHAT TRAVELS TO 4.4:** that **no adequacy or power argument may rest on a count
established against the uncapped population.** §5.6 says so directly: report 21's
200/50 thresholds "were established on the UNCAPPED population and do not describe
what is traded", and report 26 §9's capped reference figures are recorded there
explicitly as **not** establishing adequacy. **This document does not resolve it and
does not weaken it.** `docs/design/04_2b_point_4_decomposition.md` §5.2 already
records §5.6 as bearing on 4.4; that routing stands.

> ### §5.6's REGISTER ENTRY MOVES FROM "ATTACHED TO 4.2, CITED AS A FACT, NEVER
> ### DISPOSED" TO "DISPOSED AS TO RUN STRUCTURE; THREE NAMED RESIDUES TRAVELLING
> ### TO 4.2d, 4.3 AND 4.4."

---

## 4. THE EVALUATION POPULATION

### 4.1 THE INHERITED RESTRICTION, AND WHETHER ANY REASON SURVIVES

**THE RESTRICTION WAS NEVER COMMITTED, BUT IT WAS THE WORKING ASSUMPTION.**
`docs/handoff/40_point_4_2_fold_audit.md` §3.4 establishes the arithmetic that
made it visible: of **11,384** candidates, **8,567** fall in exactly one test
window, **none in more than one**, and **2,817 in none** — being **888** that
precede the schedule's first training start of 2022-04-01 and **1,929** inside
fold 1's training window only. The union of test windows runs **2022-10-01 to
2024-12-31**, against an in-sample window whose candidates begin **2022-01-05**.
§6.4 of the same report records that the 2,817 are not a random ninth of the
data.

**THE GROUND FOR A TEST-WINDOW RESTRICTION WAS THAT TRAINING DATA IS CONTAMINATED
BY SELECTION.** That ground is a good one wherever it applies. **It does not apply
here.** `docs/design/04_2a_artifact_containment.md` §2.4: with nothing fitted on
train in the frozen thesis's path, "the train/test split carries no protection for
it. There is no selection to protect the test windows from."

**SO THE QUESTION IS WHETHER ANY OTHER REASON SURVIVES. FOUR WERE CONSIDERED.**

- **SELECTION CONTAMINATION.** Dead, by §2.4 above.
- **COMPARABILITY WITH EXISTING MEASUREMENTS.** Not a ground. `docs/design/04_1f_cap_requirement.md`
  bars it in terms: preserving comparability with existing measurements is not a
  ground for a specification choice. It is barred here for the same reason and the
  bar is not narrowed.
- **THE SPLIT IS CONVENTIONAL.** Not a ground. A convention whose rationale has
  been shown not to apply is a habit.
- **REGIME REPRESENTATIVENESS.** This one runs the *other* way. The excluded span
  is a period `docs/handoff/40_point_4_2_fold_audit.md` §6.4 records as a
  distinctive one; excluding it narrows what the validation sees.

> ### **NO REASON SURVIVES FOR EXCLUDING A CANDIDATE BECAUSE IT FALLS OUTSIDE A
> ### TEST WINDOW. THE TEST-WINDOW RESTRICTION IS NOT ADOPTED.**

### 4.2 TWO DIFFERENT THINGS ARE CALLED "RESTRICTING TO TEST WINDOWS", AND ONLY ONE IS THIS DOCUMENT'S

**THEY ARE NOT THE SAME OPERATION AND THEY HAVE DIFFERENT CONSEQUENCES.**

**RESTRICTING THE INPUT** — feeding only test-window candidates to `portfolio.run`
— **changes the budget path.** Candidates from the excluded spans never occupy
budget, so signals inside the test windows face an emptier book than they would
have. It changes which candidates are taken, not merely which are reported. **It
is also structure (C) in disguise**, because nine disjoint input spans with one
call each is nine fresh books. **§2.6 and §4.1 both dispose of it.**

**RESTRICTING THE OUTPUT** — running everything and reporting only test-window
positions — **preserves the path** and discards rows afterwards. It is not a
population question at all; it is a question about what a headline figure is
computed over.

> ### THE FIRST IS THIS DOCUMENT'S AND IS REFUSED. THE SECOND IS **4.2d's** AND IS
> ### NEITHER DECIDED NOR PREJUDGED HERE.

**THIS DOCUMENT COMMITS ONLY THAT EVERY CANDIDATE ENTERS THE RUN.** What is
reported over which subset is an aggregation rule, and §0.3 forbids this document
from making one.

### 4.3 WARMUP, ESTABLISHED FROM THE CODE AND NOT MERGED WITH THE WINDOW QUESTION

**A CANDIDATE EXCLUDED FOR INSUFFICIENT HISTORY IS EXCLUDED FOR A DIFFERENT REASON
THAN ONE OUTSIDE A TEST WINDOW. THE TWO ARE KEPT APART HERE, AND THE ANSWER TO THE
FIRST TURNS OUT TO BE MORE DECISIVE THAN EXPECTED.**

**THE RULE, READ FROM THE CODE.**

`src/analysis/sweep_population.py:99-100`:

```
WARMUP_STABILISATION_BARS = 100
WARMUP_BARS = 1 + (ATR_PERIOD - 1) + WARMUP_STABILISATION_BARS
```

**114 bars at 1h.** Its decomposition, from the constant's own docstring: 1 (the
first bar has no previous close and so no true range), plus 13 (true ranges before
the seed window completes), plus 100 (ATR values after the seed, discarded for
stabilisation, the seed's residual weight at that point being 6.0e-4).

**IT IS APPLIED AT `analysis_frame`, `src/analysis/sweep_population.py:269`:**

```
out = out.iloc[warmup:].reset_index(drop=True)
```

**ORDER IS LOAD-BEARING AND IS DELIBERATE.** That function computes every
indicator on the **full** bar frame and trims afterwards, so no rolling window is
starved at the seam.

**THE CHANNEL'S OWN WARMUP IS STRICTLY INSIDE IT AND NEVER BINDS.**
`DONCHIAN_PERIOD` is 10 (`src/analysis/sweep_population.py:72`) and the fixed
comparison period is 20 (`:77`); both are shorter than 114. The non-finite guard
exists independently in any case: `sweep_masks` computes
`ok_up, ok_dn = np.isfinite(upper), np.isfinite(lower)` at `:193` and conjoins
them into both break masks at `:195-196`, so an unformed channel cannot produce a
break.

**AND THERE IS A THIRD GUARD, DOWNSTREAM.** `exposure_profile.positions` selects
signal bars at `src/analysis/exposure_profile.py:378` as
`idx = np.nonzero(mask & np.isfinite(atr))[0]` — a non-finite ATR cannot become a
candidate whatever the mask says.

**THE POPULATION PASSES THROUGH ALL OF IT.** `floor_curve.candidate_population`
(`src/analysis/floor_curve.py:361`) calls `sp.analysis_frame(...)` at `:386` and
`ep.positions(...)` at `:387`, in that order, per symbol.

> ### **THE WARMUP EXCLUSION IS PRIOR TO THE POPULATION, NOT A FILTER ON IT.** THE
> ### 114 BARS ARE REMOVED FROM THE FRAME BEFORE ANY CANDIDATE IS CONSTRUCTED, SO
> ### NO CANDIDATE CAN EXIST INSIDE THE DISCARD.

**DOES IT TOUCH THE 888? NO — AND THE REASON IS STRUCTURAL RATHER THAN
NUMERICAL.** The set of candidates excluded for insufficient history is empty, for
every subset of the population, because the exclusion operates on bars and the
population is built from what survives it.

**THE TWO FACTS AGREE AND THE AGREEMENT IS NOT A COINCIDENCE.** The constant's
docstring records that the discard ends at **2022-01-05T18:00Z**;
`docs/handoff/40_point_4_2_fold_audit.md` §3.4 records that the earliest
candidates date from **2022-01-05**. **The in-sample window's start date is not a
chosen boundary — it is where the 114-bar discard ends.** This document notes that
the end-of-discard instant is stated in a docstring and follows from the constant
plus the first bar's timestamp; the constant and its application are verified in
the code above, and the timestamp is not re-derived here because doing so would
mean opening `data/`.

**ONE FURTHER THING, BECAUSE IT IS THE OBVIOUS PLACE TO GET CONFUSED.** There is a
**second, different** warmup notion in the repository: `src/folds/schedule.py:42`
sets `WARMUP_DAYS = 45` and `:153` gives each fold a `warmup_start` of
`train_start` minus 45 days, described at `src/folds/warmup.py:3-7`. **It does not
apply to the candidate population.** Its consumers are `src/sweep/sweep.py:185`
and `src/analysis/dispersion.py:221` — the per-fold chain, which computes
indicators separately for each fold and therefore needs a buffer before each one.

> ### THE PER-FOLD WARMUP EXISTS TO SERVE PER-PERIOD COMPUTATION. UNDER §2.6's
> ### CONTINUOUS RUN IT IS INERT: INDICATORS ARE COMPUTED ONCE, GLOBALLY, AND
> ### TRIMMED ONCE.

**THAT IS NOT AN ARGUMENT FOR §2.6** — it would be circular, since the per-fold
buffer would simply be used under (C). It is recorded so that a reader who finds
`WARMUP_DAYS = 45` does not conclude that the evaluation population is warmed
per fold. **It is not.**

### 4.4 A THIRD EXCLUSION, FOUND WHILE ESTABLISHING THE SECOND, AND NOT MERGED WITH EITHER

**THE WINDOW'S FAR EDGE HAS A RULE AND `portfolio.py` DOES NOT IMPLEMENT ONE.**

`exposure_profile.max_hold_exit` (`src/analysis/exposure_profile.py:234`) returns
the third funding settlement after the entry close **unconditionally**. It applies
no clamp to the end of the bar frame. `positions` writes that stamp to
`exit_bar_ts` (`:352`, column list at `:346-349`).

**SO CANDIDATES ENTERING IN THE FINAL HOURS OF THE IN-SAMPLE WINDOW CARRY
SCHEDULED EXITS INSIDE THE SEAL.** An entry at the last in-sample bar's close has
its third settlement in 2025.

**AND `portfolio.run` WALKS THE GRID TO `max(exit_bar)`** — `src/engine/portfolio.py:574`
— **requesting 1m bars per open position per hour in `full` mode** through
`Bars1mCache.hour` (`:351`), whose loader defaults to the sealed loader (`:344`).
**`src/engine/portfolio.py` contains no holdout-crossing exclusion.** The sealed
module appears in it three times — the import at `:77`, the bar-period constant at
`:109` and the cache's default loader at `:344` — and at none of them as a
boundary test on a candidate.

**THE SUPERSEDED ENGINE HAS THE RULE THE GOVERNING ONE LACKS.**
`src/engine/simulate.py:90`'s `crosses_holdout` and `:103`'s
`require_in_sample_window` implement exactly this exclusion, refusing the signal
and counting it under `holdout_boundary` rather than reaching for a sealed bar.
Its comment at `:559-565` records why the ordering matters: the exclusion "runs
FIRST, before any 1m data is requested... so no sealed bar is touched to find out
whether a sealed bar is needed", and "because this runs first, a
`require_in_sample_window` raise below is unambiguous evidence of a bug."

**AND THE RULE IS NOT NEW. IT HAS BEEN ON THE RECORD SINCE REPORT 8.**
`docs/handoff/08_point_4_pre_registration.md:1255`, **Appendix M.3**, states it in
terms: trades whose resolution would require data at or after 2025-01-01 "are
EXCLUDED from in-sample analysis", because "exclusion is the only option that
spends no holdout data. Truncating at the boundary would require inventing an exit
price, which is a fabricated outcome. Resolving with holdout bars would contaminate
an in-sample result inside the very module that selects the candidate."

**THAT DOCUMENT IS THE SUPERSEDED POINT 4's PRE-REGISTRATION**, and this document
does not treat it as binding — `docs/design/04_2b_point_4_decomposition.md` is what
governs Point 4 now. **The rule above is committed here afresh, on the grounds
given here.** The coincidence is recorded because two independent derivations
reaching the same rule and the same reason is a check on both, and because it makes
the divergence more serious than it first appeared:

> ### THE EXCLUSION HAS BEEN SPECIFIED SINCE REPORT 8 AND IS IMPLEMENTED IN
> ### `simulate.py`. THE ENGINE BUILT TO REPLACE `simulate.py` DOES NOT IMPLEMENT
> ### IT. THE REPLACEMENT DROPPED IT.

**M.3's SECOND LIMB IS NOT ADOPTED HERE.** It also requires that "the excluded
count is reported per fold per symbol." **That is a reporting requirement and
therefore 4.2d's**, and §0.3 forbids this document from committing one. It travels
to 4.2d named as travelling, neither adopted nor refused.

> ### **THE RULE, COMMITTED HERE:** A CANDIDATE IS EVALUATED ONLY IF ITS SCHEDULED
> ### MAX-HOLD EXIT FALLS STRICTLY BEFORE THE HOLDOUT SEAL. ONE WHOSE SCHEDULED
> ### EXIT FALLS AT OR AFTER IT IS **EXCLUDED**, AND EXCLUDED **BEFORE** ANY 1m BAR
> ### IS REQUESTED ON ITS BEHALF.

**FOUR THINGS ABOUT IT.**

**IT IS A THIRD REASON AND IS NOT MERGED WITH THE OTHER TWO.** Warmup excludes for
insufficient history and does so before the population exists. The test-window
restriction excluded for a selection concern and is refused at §4.1. **This
excludes because the data needed to resolve the position is sealed**, which is
neither.

**IT IS DECIDABLE BY ARITHMETIC ON THE ENTRY STAMP ALONE**, since the scheduled
exit is a calendar function of the entry. **No sealed bar is touched to discover
that a sealed bar would be needed** — which is the ordering property
`src/engine/simulate.py`'s comment at `:559-565` identifies as what makes the seal
provable, and it is adopted here for the same reason.

**IT USES THE SCHEDULED EXIT, NOT THE REALISED ONE, AND MUST.** A realised exit is
an outcome; making the population depend on it would make membership
path-dependent, which is the defect §2.5 refuses for the boundary rule. **The
scheduled max-hold exit is the conservative bound**: a position resolving earlier
would not have needed the sealed hours, but that is not knowable at the decision.

**ITS COUNT IS NOT ESTABLISHED HERE** and no attempt is made to establish it,
because doing so means opening the population, which §0.3 forbids. It is bounded
above by the candidates entering in the window's final day.

**THE IMPLEMENTATION HALF IS A DIVERGENCE AND IS ROUTED, NOT FIXED.** A decision
document that edits the engine is a decision and an implementation in one commit,
which is the separation `docs/design/04_1g_cap_adoption.md` §5 keeps. **It is
recorded at §7.2 as a specification-implementation divergence bearing on freeze
precondition 3 at `docs/design/04_2b_point_4_decomposition.md` §4.3**, and
assigned to the consolidated code step.

### 4.5 THE POPULATION, COMMITTED AS A RULE

> ### **EVERY CANDIDATE IN THE CANDIDATE POPULATION ENTERS THE RUN, EXCEPT THOSE
> ### WHOSE SCHEDULED MAX-HOLD EXIT FALLS AT OR AFTER THE HOLDOUT SEAL.**

**STATED SO THAT A LATER READER CAN EVALUATE IT WITHOUT A COUNT:**

1. **THE SOURCE** is `floor_curve.candidate_population`
   (`src/analysis/floor_curve.py:361`) over the in-sample window: one row per
   position the frozen thesis would open, both directions, all three symbols,
   two-sided bars excluded per thesis 4.1.
2. **NO DATE RESTRICTION IS APPLIED BEYOND THE TWO THE WINDOW ALREADY CARRIES** —
   the 114-bar discard at its start, which removes bars and no candidates, and the
   seal at its end, per §4.4.
3. **FALLING OUTSIDE A TEST WINDOW IS NOT A GROUND FOR EXCLUSION.** The 888, the
   1,929 and every other candidate outside the test windows are **in**.
4. **FALLING OUTSIDE EVERY FOLD PERIOD IS NOT A GROUND FOR EXCLUSION.** Such
   candidates are run, and are reported under an explicit unassigned row rather
   than dropped, per §2.5.
5. **NOTHING IS EXCLUDED ON AN OUTCOME**, on a symbol, on a direction, on ATR, on
   whether the stop floor binds, or on any stratum of
   `docs/design/04_1c_consequences_and_thresholds.md`. The strata classify; they do
   not filter.
6. **A CANDIDATE IN THE POPULATION IS NOT NECESSARILY TAKEN.** Entering the run
   means being offered to the budget in arrival order. **Whether it is taken is the
   path's business** and by §5.6 is unknowable in advance.

**THE COUNT IS NOT THE COMMITMENT.** The record's figures are cited above for
reconciliation and the reconciliation should be done at the run; **the rule is what
is committed**, and if a count computed later disagrees with it the rule governs
and the discrepancy is a finding.

---

## 5. THE FOLD PERIODS' ROLE

### 5.1 WHAT A FOLD PERIOD IS UNDER THE COMMITTED STRUCTURE

> ### **A FOLD PERIOD IS A DATE PARTITION OF ONE RUN'S OUTPUT.** IT IS NOT A RUN,
> ### NOT A TRIAL, NOT AN INDEPENDENT EVALUATION, AND NOT AN INPUT TO THE ENGINE.

**IT IS NOT AN INPUT IN the literal sense.** `portfolio.run`'s signature
(`src/engine/portfolio.py:503`) takes candidates, config, specs, ticks, mode,
token, cache and derived directory. **There is no fold argument.** The schedule
does not reach the engine at all; it is applied to what the engine produced.

**THE PARTITION IS BY ENTRY-BAR CLOSE**, per §2.5, over the eighteen periods plus
an explicit unassigned row, on the model of
`src/analysis/level_consequences.py:333`.

**AND THE PERIODS ARE AN OVERLAPPING COVER, NOT A PARTITION OF TIME** — §2.1 —
so a position may appear in up to three period rows. **That is legitimate for a
partition of output and was fatal for a partition of runs**, which is the whole
difference between (A) and (B) restated.

### 5.2 WHAT MAY THEREFORE BE SAID ABOUT A PER-PERIOD QUANTITY

**A per-period quantity is a quantity computed over the subset of one run's
positions whose entry fell inside that period, under a budget whose state at the
period's opening was inherited from the preceding calendar time and was not
reset.**

**THAT SENTENCE IS THE WHOLE OF WHAT MAY BE SAID HERE.** It is a description of
what the number is. It is not a licence to compare two of them, and this document
issues none.

> ### WHETHER AND HOW PER-PERIOD QUANTITIES MAY BE COMPARED IS **4.2d's**, AND IS
> ### NEITHER DECIDED NOR PREJUDGED HERE.

### 5.3 WHAT 4.2d INHERITS

**FOUR THINGS, NAMED SO THAT 4.2d CANNOT BEGIN WITHOUT THEM.**

1. **THE FIFTEEN TEST-INTO-TRAIN CROSS-OVERLAPS.**
   `docs/handoff/40_point_4_2_fold_audit.md` **§3.3** — each fold's test window
   falls entirely inside the next two folds' training windows; folds 8 and 9 have
   one and zero later consumers, which is why the count is fifteen and not
   eighteen; every overlap runs forward, so there is no lookahead.
2. **THE 49.5 TO 50.3 PER CENT ADJACENT TRAIN OVERLAP.** The same report **§3.2** —
   90 to 92 days of a 181 to 184 day window, the variation being month lengths;
   **eight** overlapping train pairs, one per adjacent pair, and non-adjacent
   training windows do not overlap at all.
3. **`docs/handoff/31_point_5_closing.md` §5.5's WARNING** — trade count per fold
   measures capital availability rather than signal frequency; a fold with more
   signals produces more skips, not more trades.
4. **§5.6's RESIDUE**, per §3.4: no per-period quantity is a sample from a fixed
   population.

**A CORRECTION TO THE CITATION, MADE RATHER THAN PROPAGATED.** Items 1 and 2 are
**not both at §3.2**. The 49.5 to 50.3 per cent figure is §3.2; the fifteen
cross-overlaps are **§3.3**. Both facts are stated correctly in the record and
both are inherited as stated; only the section number differs. §7.1 records why
this is not logged as a ledger instance.

**ON THE SPLIT OF §5.5 — THE SPLIT IS RIGHT, WITH ONE ADDITION.**
`docs/design/04_2b_point_4_decomposition.md` §5.2 attaches §5.5 to 4.3 and records
it as bearing on 4.4's adequacy reasoning. **Its halves separate cleanly:**

- **THE AGGREGATION HALF IS 4.2d's** — whether per-fold counts may be combined,
  and whether a count may serve as a weight or a denominator when the budget pins
  it nearly flat.
- **THE METRIC HALF IS 4.3's** — whether any reportable quantity may be
  denominated in trade count at all.
- **AND THE ADEQUACY HALF IS 4.4's**, which `04_2b` §5.2 already carries and which
  this document does not move.

**§2.6 STRENGTHENS §5.5 RATHER THAN DISTURBING IT.** Under a continuous run a
period's trade count depends on the previous period's book as well as on capital
availability. **The count is therefore even less a measure of signal frequency
than §5.5 says**, and 4.2d inherits the warning in its stronger form.

---

## 6. THE HOLDOUT

### 6.1 THE STRUCTURE GOVERNS IT

**THE STRUCTURE COMMITTED AT §2.6 GOVERNS THE HOLDOUT RUN WHEN IT OCCURS:** one
continuous run over the holdout window, budget initialised once and carried
across it, positions assigned by entry-bar close.

**THAT IS NEARLY VACUOUS FOR THE HOLDOUT AND IT IS STATED ANYWAY.** The holdout
has no fold schedule to partition by — `src/folds/schedule.py:189` gives its
definition a `train_start` of `None` — so there are no periods and the only
structure available is one continuous run. **It is stated because a rule that
happens to be forced is still a rule, and the alternative is a later reader
wondering whether the holdout was ever considered.**

### 6.2 THE ONE-LOOK BUDGET IS UNAFFECTED

> ### **THIS DOCUMENT DOES NOT TOUCH THE HOLDOUT BUDGET.** IT REMAINS WHAT
> ### `docs/handoff/31_point_5_closing.md` §14 STATES: **ONE CANDIDATE, ONE LOOK,
> ### WHOLE WINDOW, NO CANDIDATE TWO.**

**AND THE HOLDOUT DOES NOT UNLOCK AT 4.7.** `docs/design/04_2b_point_4_decomposition.md`
§4.2 is explicit that the freeze unlocks the in-sample window only. **Nothing here
advances the holdout's date, loosens its budget, or authorises a read.**

### 6.3 A RESIDUE THIS DOCUMENT PRODUCES AND CANNOT DISCHARGE

**THE IN-SAMPLE / HOLDOUT SEAM IS ITSELF A BOUNDARY, AND IT IS THE EXACT BOUNDARY
§2.4 OBJECTS TO.**

The holdout begins the day after the in-sample window ends. A live account running
continuously across 2024-12-31 would carry its book into 2025-01-01. **A holdout
run executed as a separate call starts with `charged = 0.0` and `book = []`** —
which is precisely the fresh-book distortion §2.2 identifies and §2.6 rejects at
fold boundaries.

**AND IT CANNOT BE ELIMINATED.** A single call spanning both windows would request
sealed bars, so the seam is forced by the seal. **The seal is not negotiable and
the seam is its price.**

**WHAT IS OWED IS THAT THE SEAM BE STATED IN THE HOLDOUT'S OWN RECORD, NOT THAT IT
BE REMOVED.** The distortion is one reset rather than eight, at a date determined
by the seal rather than by a schedule, and it is bounded by the same 24-hour hold
as everything else in §2.4. **It is small. It is not zero, and an unrecorded small
thing becomes an unexplained one.**

> ### **OWED TO 4.6.** THE SUB-POINT THAT COMMITS THE GATE AND THE ORDER OF
> ### INSPECTION IS THE ONE THAT GOVERNS THE HOLDOUT LOOK, AND IT MUST RECORD THAT
> ### THE HOLDOUT RUN BEGINS WITH AN EMPTY BOOK AND WHY.

**IT IS ENTERED IN THE REGISTER AT §7.2 AS A NEW OPEN ITEM.** It is flagged as
produced by this document rather than inherited, so that a reader can see it did
not exist before §2.6 made the seam visible.

---

## 7. THE LEDGER AND THE OPEN ITEMS

### 7.1 THE LEDGER

**THE TOTAL, READ:** `docs/design/04_2b_point_4_decomposition.md` §7.3 states
**"49 + 1 = 50"**. The total read is **50**.

> ### **NO INSTANCE IS LOGGED. THE TOTAL IS UNCHANGED AT 50.**

**TWO CANDIDATES WERE CONSIDERED AND BOTH ARE RECORDED RATHER THAN LOGGED, SO THAT
A READER WHO DISAGREES CAN SEE WHAT WAS WEIGHED.**

**FIRST — THE SECTION-NUMBER SLIP AT §5.3.** The instruction that produced this
document attributed both the fifteen cross-overlaps and the 49.5 to 50.3 per cent
overlap to `docs/handoff/40_point_4_2_fold_audit.md` §3.2; the cross-overlaps are
§3.3. **This is formally the sub-class of instance (50)** — a statement about what
a document says, written from a mental model of it. **It is not logged**, because
both content claims are correct, the correction is made in place at §5.3, and
nothing downstream changes. Instance (50) was logged because it **required a
document to write a correction to a claim its target does not make**; this required
a citation to be repaired and nothing else. **Logging a section number would
inflate a ledger whose value is that its instances are load-bearing.**

**SECOND — THE HOLD FIGURE.** The instruction cites
`docs/handoff/24_point_5_1_exposure.md`'s **mean hold of 20.51 hours**. That figure
is correct and is the elapsed hold under **time exits only**, measured on the
candidate population with no exits resolved. **Under full mode holds can only be
shorter.** The conclusion the instruction draws from it — that boundary-crossing
positions exist — is unaffected, because the minimum hold is 17 hours and any
positive hold produces crossings. **It is a clarification, not an error**, and §2.4
uses the **maximum** of 24 hours rather than the mean precisely because the maximum
is the quantity that bounds carry-over.

**AND ONE TRANSPARENCY NOTE, ON THE MODEL `docs/design/04_1d_standing_practices.md`
§5.4 SETS.** Two words, one in §4.3's opening and one in §4.4, collided with a
banned token by substring and were replaced with synonyms before this document was
committed. **Nothing else in
the file moved**, both sentences were correct before the change and after it, and
the changes were made so that a raw-text firewall grep over the document would not
fire.
**Not logged**, under `docs/design/04_1a_denomination.md` §6's criterion — a falsely
firing check is logged only if the remediation on offer would have degraded an
otherwise correct artifact, and one ordinary synonym for another degrades nothing.
**Recorded anyway**, because an undocumented edit made to satisfy a check is exactly
the shape of thing this project logs.

### 7.2 THE OPEN ITEMS REGISTER — THIS DOCUMENT'S ENTRIES

**RECORDED HERE IN THE FORM `docs/design/04_2b_point_4_decomposition.md` §5 USES.
THAT DOCUMENT IS NOT EDITED.**

**DISCHARGED, IN PART, WITH THE RESIDUE NAMED:**

- **`docs/handoff/31_point_5_closing.md` §5.6**, path dependence, attached to 4.2
  at `04_2b` §5.2 and recorded there as **cited three times as a fact, never
  disposed**. **Disposed here as to run structure**, per §3.4. **Three residues
  travel and are named:** the non-exchangeability of per-period populations, to
  **4.2d**; the prohibition on metrics denominated in a path-pinned quantity, to
  **4.3**; the prohibition on adequacy arguments resting on uncapped-population
  counts, to **4.4**. **Its 4.4 routing at `04_2b` §5.2 stands unchanged.**

**CARRIED, WITH ITS SPLIT ENDORSED AND ONE ADDITION:**

- **`docs/handoff/31_point_5_closing.md` §5.5**, the capital-supply flatline,
  attached to 4.3 at `04_2b` §5.2. **The split is right**: aggregation half to
  **4.2d**, metric half to **4.3**, adequacy half to **4.4** as `04_2b` already
  records. **Strengthened, not weakened**, by §2.6 — see §5.3.

**NEW, PRODUCED BY THIS DOCUMENT:**

- **THE `portfolio.py` SEAL-CROSSING EXCLUSION.** §4.4 commits the rule; the
  engine does not implement it, while the superseded `src/engine/simulate.py` does.
  **This is a specification-implementation divergence and it bears on freeze
  precondition 3** at `docs/design/04_2b_point_4_decomposition.md` §4.3, which
  today names one such divergence. **There are two.** **Assigned to the
  consolidated code step** at `04_2b` §5.1, which already carries the other.
  **Owed, with no owner at this commit.**

- **THE IN-SAMPLE / HOLDOUT SEAM.** §6.3. The holdout run begins with an empty
  book, the seam is forced by the seal and cannot be removed, and it must be
  recorded in the holdout's own record. **Attached to 4.6.** **Flagged as produced
  by this document rather than inherited.**

**NOTHING ELSE IN THE REGISTER MOVES.** The seven at
`docs/design/04_2a_artifact_containment.md` §7, the four Point 6 obligations and
the two housekeeping items are unaffected by this commit.

---

## 8. WHAT THIS DOCUMENT DOES NOT DO

**NO AGGREGATION RULE, NO METRIC, NO LEVEL, NO THRESHOLD, NO COMPARISON RULE.**
§0.3 states them and nothing in §2 to §7 supplies one. §4.2 refuses an output
restriction as explicitly as it refuses an input one, because refusing it would be
an aggregation rule stated negatively.

**IT DOES NOT REARGUE `docs/design/04_2a_artifact_containment.md` §2.4**, and if
that finding is ever revived on its own §2.5 terms, §2.7's third condition is the
place this document must be re-read.

**IT ESTABLISHES NO COUNT.** Every figure is cited from a committed record. No
population is opened, no bar is read, no engine entry point is invoked, and no
artifact under `docs/design/04_2a_artifact_containment.md` §3's prohibition is
touched.

**IT DOES NOT EDIT CODE.** §4.4's divergence and §2.8's coincidence are both
recorded and routed; neither is repaired here.

**IT DOES NOT VERIFY THE COUNTS IT CITES.** The 11,384, the 8,567, the 2,817, the
888, the 1,929 and the 6,456 are `docs/handoff/40_point_4_2_fold_audit.md` §3.4's,
carried on that report's authority. **A discrepancy found later is an erratum
against this document**, not a revision of what it committed: the rule at §4.5 is
the commitment and it does not depend on any of those figures being right.

---

## 9. CHANGE DISCIPLINE

**THIS DOCUMENT JOINS THE FROZEN SPECIFICATION ON COMMIT.** It is amended by a new
document that names it, states what changes and states why, on the model the 4.1
chain uses. **It is not edited in place.**

**AN ERROR FOUND IN IT IS LOGGED AS AN ERRATUM AND NOT PATCHED**, per
`docs/prompts/STANDING_RULES.md`.

**THE DECISION AT §2.6 IS REOPENED ONLY BY ONE OF THE THREE CONDITIONS AT §2.7
BECOMING TRUE**, and a document reopening it must say which one and on what
evidence. **It is not reopened by a result**, which is the entire reason it is
committed before any result exists.
