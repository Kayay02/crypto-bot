# THE LEVEL, STEP 1 — THE CALIBRATION

**Point 4, sub-point 4.1c. Four things are committed. No level and no width are
stated.**

## 0. THE SCOPE LIMIT, STATED FIRST, AND IT IS THE ONE MOST AT RISK HERE

> ### NO VALUE FOR THE TOLERANCE APPEARS ANYWHERE IN THIS DOCUMENT, IN ANY FORM.
> ### NOT AS A RESULT, NOT ILLUSTRATIVELY, NOT PARENTHETICALLY, AND NOT IN ORDER
> ### TO DISCLAIM IT. NO FLOOR WIDTH APPEARS.

**THE ALGEBRA COMMITTED HERE DETERMINES A LEVEL.** That is the point of it. **The
level is step 2's output**, and stating it here would collapse the commit
separation that `docs/design/04_1c_pre_commitments.md` §4.3(e) requires and that
§1 of this document relies on for its entire claim to honesty.

**NO BOUND OF THE ADMITTED DOMAIN IS QUOTED EITHER**, though those are committed
facts, because a domain bound is a tolerance value and the limit above admits no
exceptions.

**No requirement given to this document was read as asking for a level.** None
appeared to.

---

## 1. WHAT THIS DOCUMENT IS

**A PRE-REGISTRATION, FROZEN ON COMMIT.** Made **before the level it governs has
been computed or stated**, and before any performance figure exists for this
thesis. It joins the frozen specification on its commit.

### 1.1 THE ROUTE, AND WHY

**THE DERIVATION ROUTE WAS ATTEMPTED ONCE AND FAILED.**
`docs/design/04_1c_level_method.md` §3 proposed one method, tested it against the
five disqualifying properties one at a time, and reported it **disqualified on
property (b)**: the method needed a bound on how wrong the unvalidated estimates
might be, and `docs/handoff/31_point_5_closing.md` §5.2 records that the stop
haircut cannot be validated against this data layer, because no bar's first
observed price exists at any resolution.

**THAT DOCUMENT DID NOT CHOOSE BETWEEN THE TWO FALLBACKS**, and said so.
`docs/design/04_1c_pre_commitments.md` §4.4 named them and preferred neither.

> ### THE PROJECT OWNER HAS CHOSEN THE JUDGEMENT ROUTE. THE LEVEL IS SELECTED ON
> ### STATED JUDGEMENT, RECORDED AS JUDGEMENT, AND IS NOT PRESENTED AS DERIVED.

**THIS DOCUMENT IS THAT JUDGEMENT'S SPECIFICATION.** It commits the inputs the
judgement consists of, so that the level following from them is a mechanical
consequence of a judgement made in the open rather than a number chosen and then
explained.

### 1.2 THE THREE-STEP SEPARATION

**REQUIRED BY `docs/design/04_1c_pre_commitments.md` §4.3(e).**

- **STEP 1 — THIS DOCUMENT.** The risk-displacement budget, the uncertainty
  parameter and its scope, the reconciliation rule for the stress comparator, and
  an honest account of what the calibration is. **No level, no widths.**
- **STEP 2 — A REPORT UNDER `docs/handoff/`.** The mechanical mapping to the level
  and the floor widths, the stress comparator, the non-floor-bound stratum
  thickness, and the first count of the ATR-above-cap rejection population. §6
  states it in full.
- **STEP 3 — A FURTHER DESIGN DOCUMENT.** Kill condition (d)'s disposition, the
  magnitude threshold, and the Point 6 audit's terms.

**THE SEPARATION IS THE WHOLE DEFENCE AND IT IS CHEAP.** It costs two extra
commits and buys one thing: that the inputs were fixed before the output existed
is a fact in `git log` rather than a claim about what was known when.

---

## 2. THE RISK-DISPLACEMENT BUDGET

### 2.1 THE COMMITMENT

> ### THE MAXIMUM TOLERABLE DISPLACEMENT OF THE RISK UNIT CAUSED BY ERROR IN THE
> ### UNVALIDATED COST ESTIMATES IS TEN PER CENT OF ONE RISK UNIT.

**STATED IN BOTH UNITS.** `docs/design/00_standing_brief.md` §2 fixes the standing
rule, quoted here as the committed premise it is:

> **Risk per trade: never more than 1% (that is, $20), enforced after fees and
> estimated slippage.**

**Against that figure, the budget is two dollars of the twenty.** That is the same
commitment restated, not a second one.

### 2.2 WHAT IT MEANS TO ACCEPT IT

**A STOP-OUT MAY RETURN WORSE THAN ONE RISK UNIT BY UP TO THIS FRACTION IF THE
ESTIMATES ARE WRONG IN THE ADVERSE DIRECTION.** The position was sized against a
risk unit built partly from numbers nobody has measured. If those numbers are too
low, the loss at the stop exceeds what the standing rule fixes, by the amount of
the error carried through the sizing.

**THE BUDGET SAYS HOW MUCH OF THAT THE PROJECT WILL ACCEPT.** It is judged
tolerable against the standing rule. **It is not argued to be optimal, and it is
not the output of any calculation.**

**IT IS A REAL COST AND IT IS NOT ARGUED AWAY.** The standing rule says never more
than 1%. This budget admits that the rule may be breached, by up to a tenth of the
unit, whenever the estimates are wrong adversely. **That is a weakening of the
standing rule and it is stated as one**, in the same terms
`docs/handoff/31_point_5_closing.md` §5.3 uses for the fill-price term it accepted
on magnitude grounds.

### 2.3 WHAT WOULD HAVE MADE A DIFFERENT BUDGET CORRECT

**`docs/design/04_1c_pre_commitments.md` §4.3(d) REQUIRES THIS, AND IT IS WHAT
DISTINGUISHES A JUDGEMENT FROM A RATIONALISATION.** A judgement that cannot say
what would have changed it is indistinguishable from a preference.

**TWO THINGS WOULD HAVE MADE A DIFFERENT BUDGET CORRECT:**

- **A DIFFERENT TOLERANCE FOR BREACHING THE STANDING RULE.** The rule is stated as
  a hard cap -- never more than 1%. A reader who takes that literally admits no
  budget at all and would set it at zero, which forces the unvalidated share to
  zero and the floor to infinity; a reader who treats the rule as nominal rather
  than realised would admit a larger one. **The budget encodes a position between
  those, and naming a different position is how a different budget is argued.**
- **A DIFFERENT VIEW OF HOW MUCH OF THE RULE'S AUTHORITY A MODELLED TERM MAY
  CONSUME.** The standing rule's force comes from being a number the operator can
  rely on. Every fraction of it that rests on an unmeasured estimate is a fraction
  that is asserted rather than enforced. **A reader who holds that a larger share
  of the rule's authority may rest on modelling would set a larger budget, and one
  who holds that the rule should be almost entirely enforceable would set a
  smaller one.**

**NEITHER OF THOSE IS SETTLED BY ANYTHING IN THIS REPOSITORY**, which is why the
budget is a judgement.

### 2.4 WHO DECIDED

**THE PROJECT OWNER, in the collaboration channel, on the date of this commit.**

**NAMED AS THE PROJECT OWNER'S JUDGEMENT AND NOT AS A CONSENSUS OR A FINDING.** No
measurement produced it, no document implied it, and no analysis in this
repository constrains it. **A reader who disagrees with it is disagreeing with a
person's stated judgement, which is the correct thing to be disagreeing with, and
is not being contradicted by evidence.**

---

## 3. THE UNCERTAINTY PARAMETER AND ITS SCOPE

### 3.1 THE PARAMETER

> ### THE ASSUMED PROPORTIONAL ERROR IN THE UNVALIDATED ESTIMATES IS ONE HUNDRED
> ### PER CENT: THE TRUE VALUE MAY BE UP TO TWICE THE MODELLED VALUE.

### 3.2 THE SCOPE

> ### IT RANGES OVER THE ENTIRE UNVALIDATED SUM -- THE STOP HAIRCUT AND THE
> ### PROVISIONED FUNDING TERM TOGETHER -- AS THAT SET WAS FIXED AT
> ### `docs/design/04_1c_path_and_scope.md` §3.

Entry slippage is a member of that set and is frozen at zero, so it carries no
magnitude at this commit. §7 records what changes if it is ever given one.

### 3.3 THE SCOPE IS THE LOAD-BEARING CHOICE, AND IT IS ARGUED

**BOTH TERMS ARE ESTIMATES AND NEITHER IS BETTER FOUNDED THAN THE OTHER.**

**FUNDING** is provisioned at a fixed count of settlements, at an assumed constant
rate, on a quantity that floats at the venue.
`docs/design/04_1c_path_and_scope.md` §3.2 records document 06's own terms for it:
an assumption, not a measurement, because the funding history available to this
project covers a fraction of the window being tested.

**THE HAIRCUT** is a placeholder standing in for the entire slippage-and-gap
model. `docs/handoff/31_point_5_closing.md` §5.2 records that it IS that whole
model, that it is not a venue-published figure, and that it cannot be validated
against this data layer at all.

> ### ASSUMING FULL ERROR ON ONE AND NONE ON THE OTHER IS AN ASYMMETRY WITH NO
> ### GROUND BEHIND IT.

**AND THE CONSTRAINT WAS DENOMINATED OVER THE WHOLE UNVALIDATED BUNDLE FOR THE
SAME REASON.** `docs/design/04_1c_path_and_scope.md` §3.3 committed funding into
the constrained numerator on the ground that excluding a term from the numerator
while including it in the denominator would bound the share of unvalidated cost
using a denominator containing unvalidated cost it does not count.

**SO SCOPING THE UNCERTAINTY PARAMETER OVER ANYTHING NARROWER WOULD MAKE THE
STRESS ASSUMPTION AND THE CONSTRAINT DISAGREE ABOUT WHAT IS UNVALIDATED.** The
constraint would bound a bundle the stress assumption treats as partly certain,
and the budget would then be a budget on a different quantity from the one the
constraint binds. **The two must range over the same set or the calibration
connects nothing to nothing.**

### 3.4 WHAT WOULD HAVE MADE A DIFFERENT SCOPE CORRECT

**EVIDENCE THAT ONE TERM'S ESTIMATE IS MATERIALLY BETTER FOUNDED THAN THE
OTHER'S.** Not an intuition that one feels more solid -- evidence, of the kind
that would let a reader say how much better founded.

**NO SUCH EVIDENCE EXISTS AT THIS COMMIT.** Both terms are recorded in committed
documents as assumptions in almost identical language, and neither has been
measured.

**WHERE IT WOULD COME FROM.** For the haircut, Point 6's paper trading or a data
source carrying first observed prices, which
`docs/handoff/31_point_5_closing.md` §5.2 names as the two routes and records that
this project has neither. For funding, a longer funding-rate history covering the
measurement window, against which the assumed constant rate and the provisioned
settlement count could both be checked.

---

## 4. WHAT THIS CALIBRATION IS, STATED WITHOUT FLATTERY

### 4.1 THE RELATION

**Under the scope committed at §3, a proportional error in the unvalidated
estimates displaces the risk unit by that error multiplied by the unvalidated
share of the risk unit.** The whole bundle is stressed together, so the whole
bundle's share is what the error acts on.

**AND THE CONSTRAINT BINDS THAT SHARE DIRECTLY.**
`docs/design/04_1c_denominator_choice.md` §2.1 committed the constraint as the
unvalidated sum over the risk unit, at most the tolerance.

> ### THE BUDGET AND THE TOLERANCE ARE THEREFORE THE SAME PARAMETER IN DIFFERENT
> ### UNITS, RELATED BY THE UNCERTAINTY PARAMETER ALONE.

**No value is stated on either side of that relation.**

### 4.2 THE CONSEQUENCE, STATED HONESTLY

> ### THIS CALIBRATION DOES NOT DERIVE THE TOLERANCE. IT RE-DESCRIBES IT IN UNITS
> ### A PERSON CAN HOLD AN OPINION ABOUT.

**THAT IS REAL WORK AND IT IS WORTH SAYING WHY.** A displacement of the risk unit
is a thing the standing rule speaks to: the rule fixes a number and the
displacement says by how much that number may fail to hold. A person can have a
view about that. **A bare share of a denominator is not such a thing** -- nothing
in the standing brief, the thesis or any frozen document gives a reader any
purchase on whether a given share is acceptable, which is precisely what
`docs/design/04_1b_tolerance_and_branch.md` §4.2 reported when it found the
rationale unable to discriminate between candidate values.

**BUT IT IS RE-DESCRIPTION AND NOT DERIVATION.** Nothing new is learned about the
world between §2 and the level. The judgement is made once, in the units where it
can be made, and then converted.

**PRESENTING IT AS DERIVATION WOULD BE THE MANUFACTURED LEVEL-DISCRIMINATING
ARGUMENT `docs/design/04_1b_tolerance_and_branch.md` §4.2 WARNED AGAINST**, and
the warning is quoted rather than paraphrased: reporting that the rationale does
not discriminate *"is preferable to manufacturing a level-discriminating argument
that the interrogation did not produce."*

### 4.3 THE DISCLOSURE ABOUT THE RESULTING NUMBER

**BECAUSE THE RELATION IS SIMPLE, THE LEVEL THAT STEP 2 COMPUTES MAY TURN OUT TO
BE A ROUND FIGURE.**

> ### A ROUND NUMBER EMERGING FROM A JUDGEMENT CALIBRATION IS EXACTLY THE
> ### APPEARANCE THIS SUB-POINT HAS SPENT ITS WHOLE LENGTH GUARDING AGAINST.

It looks like a number chosen first and reached backwards. **The document cannot
answer that by argument**, because any argument it could make would be available
equally to someone who had in fact chosen the number first.

> ### THE DEFENCE IS THE COMMIT ORDER AND NOT THE ARITHMETIC.

**THE BUDGET AND THE UNCERTAINTY PARAMETER ARE FIXED IN THIS COMMIT, BEFORE ANY
LEVEL HAS BEEN COMPUTED**, and a reader can verify that from `git log` rather than
taking it on trust. **The sequence that establishes it:**

- **`5ec36c0`** -- the standard a level-setting method must meet, committed before
  any method was proposed.
- **`1a0aa24`** -- one method proposed, tested and reported disqualified, with no
  level stated.
- **this commit** -- the budget and the uncertainty parameter, with no level
  stated and no width stated.
- **step 2's commit** -- the level, following mechanically.

**A READER WHO SUSPECTS THE NUMBER CAME FIRST CAN CHECK THE ORDER AND FIND THAT
THE INPUTS PRECEDE THE OUTPUT IN SEPARATE COMMITS.** That is the only defence
available and it is the reason the three-step separation was imposed.

**AND THE NUMBER IS NOT STATED HERE IN ORDER TO DISCLAIM IT.** Naming it while
protesting that it was not chosen first would put the very thing at issue into the
document that exists to establish it was not there.

---

## 5. THE STRESS COMPARATOR AND ITS RECONCILIATION RULE

### 5.1 THE COMMITMENT

> ### STEP 2 ALSO COMPUTES A COMPARATOR: THE LEVEL THAT WOULD FOLLOW IF THE
> ### UNCERTAINTY PARAMETER RANGED OVER THE HAIRCUT ALONE RATHER THAN THE WHOLE
> ### UNVALIDATED BUNDLE.

### 5.2 WHY

**THE SCOPE DECISION AT §3 IS A JUDGEMENT, AND A JUDGEMENT THAT CHANGES THE
REQUIRED TIGHTNESS SHOULD HAVE ITS COST VISIBLE RATHER THAN ASSUMED.** §3.3 argues
the scope from symmetry of ignorance, which is a good argument and not a
measurement. The comparator shows what accepting it costs, in the units the
decision is made in.

**THE COMPARATOR IS NOT ADOPTED AND DOES NOT GOVERN.** It is computed, reported,
and left standing beside the committed scoping.

### 5.3 THE RECONCILIATION RULE, COMMITTED

**UNDER HAIRCUT-ONLY SCOPING THE HAIRCUT'S SHARE OF THE UNVALIDATED SUM DIFFERS BY
SYMBOL**, because the haircut rate is per-symbol while the funding term is a
single scalar for all three. **So one budget maps to different levels per symbol.**

> ### WHERE THAT HAPPENS, THE BINDING LEVEL IS THE ONE SATISFYING THE BUDGET ON
> ### THE WORST CELL -- THE SYMBOL WHOSE HAIRCUT IS THE LARGEST FRACTION OF ITS
> ### UNVALIDATED SUM -- AND THE OTHER SYMBOLS ARE PROTECTED MORE TIGHTLY THAN THE
> ### BUDGET REQUIRES.

**WHICH SYMBOL THAT IS, IS NOT IDENTIFIED HERE.** Identifying it is a comparison of
rates and therefore a computation, which step 2 owns. **The rule is committed
before its subject is known**, which is the same discipline every other criterion
in this sub-point was committed under.

**THIS RULE GOVERNS THE COMPARATOR ONLY.** Under §3's committed scoping the
uncertainty parameter ranges over the whole unvalidated sum, which is the same
bundle the constraint binds, so the two coincide exactly and **no symbol multiplier
arises**. One budget maps to one level for every symbol and direction.

### 5.4 THE COMPARATOR'S RESULT DOES NOT REOPEN §3

> ### IF IT SHOWS THE COMMITTED SCOPING IS MATERIALLY LOOSER, THAT IS INFORMATION
> ### FOR THE POINT 6 AUDIT, NOT GROUNDS TO REVISE THE SCOPE AFTER SEEING WHAT IT
> ### COSTS.

**REVISING A SCOPE ONCE ITS COST IS VISIBLE IS SELECTING THE SCOPE BY ITS
CONSEQUENCE**, which is the failure the commit-order discipline exists to prevent
and which `docs/design/04_0_decision_rule.md` §8 forbids in the branch-choice case
in the same terms. **A revision is possible only through §9's amendment route, and
such an amendment would have to state that it was made after the comparator was
seen.**

---

## 6. WHAT STEP 2 MUST PRODUCE, AND WHAT IT MUST NOT

### 6.1 IT IS A REPORT UNDER `docs/handoff/`

**NOT A DESIGN DOCUMENT.** It is a measurement, and
`docs/handoff/36_point_4_1c_risk_unit_derivation.md`'s preamble states the ground:
design documents join the frozen specification on commit and a derivation does
not, so filing a measurement under `docs/design/` would enrol it in the
specification.

### 6.2 IT MUST PRODUCE

- **THE LEVEL**, following mechanically from §2 and §3, with the mapping shown.
- **THE PER-SYMBOL, PER-DIRECTION FLOOR WIDTHS AT THAT LEVEL**, from report 36's
  closed form, **verified against the implementation** rather than against the
  algebra in prose.
- **THE STRESS COMPARATOR OF §5**, with §5.3's reconciliation rule applied and the
  worst cell identified.
- **THE NON-FLOOR-BOUND STRATUM THICKNESS** over the 11,384 candidates, **per
  symbol and per fold period.** A pooled figure alone would hide whether the
  stratum thins unevenly across the window.
- **THE FIRST COUNT OF THE ATR-DERIVED-STOP-ABOVE-CAP REJECTION POPULATION**, which
  `docs/design/04_1c_pre_commitments.md` §3 defines as population B and which
  **nothing in this repository has yet counted.**

### 6.3 POPULATION A MUST BE COUNTED, NOT ASSUMED

**`docs/design/04_1c_pre_commitments.md` §3 STATES THAT POPULATION A -- THE
REQUIRED FLOOR ABOVE THE CAP -- IS EMPTY AT ANY LEVEL INSIDE THE ADMITTED DOMAIN,
BY CONSTRUCTION.**

> ### STEP 2 MUST REPORT THE COUNT RATHER THAN ASSUME IT.

An expectation derived from a domain definition is exactly the kind of claim that
survives unexamined until it is wrong. **A count of zero reported is evidence; a
count of zero assumed is a restatement of the definition.**

### 6.4 IT MUST NOT

**IT MUST NOT DISPOSE OF KILL CONDITION (d), SET THE MAGNITUDE THRESHOLD, OR
REVISE ANYTHING COMMITTED HERE.** All three belong to step 3.

---

## 7. THE POINT 6 AUDIT OBLIGATION

### 7.1 THE COMMITMENT

> ### WHEN PAPER TRADING SUPPLIES OBSERVED FILLS, THE REALISED DISPLACEMENT OF THE
> ### RISK UNIT IS MEASURED AGAINST THE BUDGET COMMITTED AT §2, AND THE BUDGET,
> ### THE UNCERTAINTY PARAMETER AND THE LEVEL ARE RE-ARGUED IN LIGHT OF IT.

### 7.2 THIS IS WHAT MAKES THE JUDGEMENT CHECKABLE

> ### A JUDGEMENT WITH A STATED FALSIFIER IS A HYPOTHESIS. ONE WITHOUT IS A
> ### PREFERENCE.

The budget asserts that the displacement will stay within a bound under an assumed
error. **Observed fills make both testable**: the realised haircut can be compared
against the modelled one, giving the error the uncertainty parameter guessed at,
and the realised displacement can be compared against the budget directly.

**IT IS NOT A PROMISE THAT THE JUDGEMENT IS RIGHT. IT IS A COMMITMENT THAT IT WILL
BE FOUND OUT IF IT IS WRONG**, on a schedule fixed before the answer is known.

### 7.3 THE POINT 6 QUEUE, NOW AT FOUR

**THREE OBLIGATIONS WERE ALREADY QUEUED FOR POINT 6, AND THIS IS THE FOURTH:**

1. **THE EXPIRY RE-ARGUMENT** at `docs/design/04_1b_tolerance_and_branch.md` §3.5.
   If the haircut is measured, the estimate becomes an observation and the
   constraint's rationale weakens accordingly, so its justification must be
   re-argued. `docs/design/04_1a_denomination_amendment_1.md` §5.2 records that
   this re-argument grew larger once the constraint's numerator narrowed onto the
   haircut.
2. **FOLDING MEASURED SLIPPAGE INTO THE UNVALIDATED SET.** Entry slippage is a
   committed member of that set and is frozen at zero, so it carries no magnitude
   today. A measured value gives it one.
3. **RE-EVALUATING THE ACHIEVABLE DOMAIN**, because a non-zero slippage moves the
   ceiling. `docs/handoff/36_point_4_1c_risk_unit_derivation.md` §5.1 established
   that the zero-width limit rises with the unvalidated total, so switching
   slippage on moves the domain's upper bound and therefore the grid built inside
   it. **This is not a re-run of the same analysis on new inputs; the admitted
   domain itself changes.**
4. **THIS AUDIT** -- the realised displacement against the budget.

**ITEMS 2 AND 3 ARE ONE EVENT WITH TWO CONSEQUENCES**, and they are listed
separately because a step that did the first without the second would leave a
domain that no longer bounds what it claims to.

---

## 8. WHAT THIS DOCUMENT DOES NOT DO

**IT STATES NO LEVEL AND NO FLOOR WIDTH.** Owed by step 2.

**IT COUNTS NO POPULATION.** Neither population A nor population B, and no stratum
thickness. Owed by step 2.

**IT DOES NOT DISPOSE OF KILL CONDITION (d).** Owed by step 3, which
`docs/handoff/31_point_5_closing.md` §9(c) records as additionally needing §5.9's
level decision.

**IT SETS NO MAGNITUDE THRESHOLD.** §2's budget is closely related and is **not**
a substitute: the threshold asks at what magnitude a breach of the standing risk
rule stops being tolerable in general, across the fill-price term and every other
disclosed breach, while §2's budget answers that question for one cause only --
error in the unvalidated estimates. Owed by step 3.

**IT IDENTIFIES NO WORST CELL.** Owed by step 2, per §5.3.

---

## 9. CHANGE DISCIPLINE AND THE ERRATA INDEX

**A CHANGE TO ANY COMMITMENT HERE IS A NEW DOCUMENT WITH ITS OWN COMMIT AND AN
EXPLICIT STATEMENT OF WHAT CHANGED AND WHY -- NEVER A SILENT EDIT.** It would be
`docs/design/04_1c_proper_amendment_1.md`.

**A SILENT EDIT IS A CONTAMINATION EVENT.**

**AND ONE FORM OF AMENDMENT IS NAMED IN ADVANCE.** An amendment revising §2's
budget or §3's scope **after step 2's level or the §5 comparator has been seen must
say so in those words.** §5.4 forbids the revision on the comparator's account;
this clause ensures that if it happens anyway, a reader can tell.

### 9.1 THE ERRATA INDEX

> ### THIS DOCUMENT CORRECTS NO FROZEN ARTIFACT. NO ENTRY IS ADDED TO THE
> ### CONSOLIDATED INDEX AT `docs/design/04_1c_pre_commitments.md` §5.

It commits new parameters and discharges no obligation by correcting anything. **The
index stands at nine entries, unchanged, and its next holder carries it forward as
it is.**

---

## 10. THE LEDGER

**`docs/design/04_1c_level_method.md` §8 states that the total read is 43 and
unchanged. The total read is 43.**

**THIS DOCUMENT ADDS NO INSTANCE AND THE TOTAL IS UNCHANGED AT 43.** It records no
defect: the budget and the uncertainty parameter are judgements openly made, not
criteria written from a mental model of a quantity, and §4.2 states what they are
rather than claiming more for them.

---

**Committed alone, before the level it governs has been computed or stated. One
risk-displacement budget committed as the project owner's judgement, with what
would have made a different budget correct stated in two forms; one uncertainty
parameter committed at full proportional error and scoped over the whole
unvalidated bundle, argued from symmetry of ignorance and from the constraint's own
membership; one calibration described as re-description rather than derivation,
with the round-number appearance disclosed in advance and the commit sequence named
as its only defence; one stress comparator commissioned with its reconciliation
rule committed before its subject is known, and its result barred from reopening
the scope; one audit obligation added to the Point 6 queue as the judgement's
falsifier. No level is stated, no floor width is stated, no population is counted,
and the ledger is unchanged at 43.**
