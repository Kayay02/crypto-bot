# THE 4.1c PRE-COMMITMENTS

**Point 4, sub-point 4.1c, preparatory. Four things are committed. Nothing is
computed, derived or selected.**

## 0. THE SCOPE LIMIT, STATED FIRST

> ### THIS DOCUMENT SELECTS NO TOLERANCE VALUE, STATES NO FLOOR WIDTH AS
> ### GOVERNING, AND SETS NO MAGNITUDE THRESHOLD.

Figures from `docs/handoff/36_point_4_1c_risk_unit_derivation.md` are quoted where
an argument requires them, as established facts about the ratio's structure and
never as candidate levels.

**No requirement given to this document was read as asking for a level.** None
appeared to.

---

## 1. WHAT THIS DOCUMENT IS

**A PRE-REGISTRATION, FROZEN ON COMMIT.** Made **before any tolerance value is
selected** and **before any performance figure exists for this thesis**. It joins
the frozen specification on its commit, per
`docs/design/04_0_divergence_disposition_amendment_2.md` §2, whose membership list
is open forward.

**IT COMMITS FOUR THINGS:**

1. **The admitted parameter domain**, and the exclusion of the regime above it
   (§2).
2. **The reject-over-clip precedence**, and the partition of the two rejection
   populations (§3).
3. **The standard any level-setting method must meet** — not a method (§4).
4. **The consolidated errata index**, initialised and given a maintenance rule
   (§5).

**`docs/design/04_1c_proper.md` FOLLOWS AND OWES:** the level, the widths, the
dominance check named at `docs/design/04_1a_denomination.md` §4.1, kill condition
(d)'s disposition, and the magnitude threshold
`docs/handoff/31_point_5_closing.md` §5.3 records as outstanding.

---

## 2. THE ADMITTED PARAMETER DOMAIN, AND THE EXCLUSION ABOVE IT

### 2.1 THE DOMAIN

> ### THE TOLERANCE IS ADMITTED ONLY WITHIN THE INTERVAL COMMON TO ALL SYMBOLS
> ### AND DIRECTIONS.

**BOUNDED BELOW** by the largest per-cell value of the ratio at the frozen stop
cap. Report 36 §2.2 establishes that as **SOLUSDT short, at 0.03554692.** Below it
that cell requires a width the cap forbids.

**BOUNDED ABOVE BY THE SMALLEST CEILING ACROSS SYMBOLS, WHICH IS BTCUSDT's AND
ETHUSDT's, AT 0.40.**

> **"THE CEILING" IN THIS DOCUMENT ALWAYS MEANS 0.40, NEVER SOLUSDT's 0.52.**

That is stated because the two exist and a reader reaching for "the ceiling" would
naturally find the larger one. **SOLUSDT's ceiling of 0.52 is not a bound on the
admitted domain and never governs it.** The binding ceiling is the lowest one,
because the domain is the intersection across cells and not the union.

### 2.2 THE EXCLUSION, ARGUED

**A TOLERANCE ABOVE 0.40 IS ONE THAT BTCUSDT's AND ETHUSDT's CONSTRAINT CANNOT
BIND AT ANY ADMISSIBLE WIDTH.**

Report 36 §2.1 establishes that the ratio's supremum over positive widths is the
zero-width limit. Above it, **the ratio is already below the tolerance at every
width**, so every width satisfies the constraint and **no width is required.**

> ### THE CONSTRAINT IS VACUOUS FOR THOSE SYMBOLS, NOT MERELY LOOSE. NO WIDTH IS
> ### UNATTAINABLE.

**THE PHRASING MATTERS AND THE WRONG ONE IS NAMED SO IT CANNOT BE WRITTEN LATER.**
A reader might say that above the ceiling "the required width cannot be reached".
**That is wrong.** Nothing is out of reach. The required width has fallen to
nothing: the constraint asks for no width at all, and every position satisfies it
however tight its stop. **The failure is that the constraint stops asking, not
that the answer becomes unreachable.**

### 2.3 WHY VACUITY DISQUALIFIES THE REGIME

**THE GROUND IS `docs/design/04_1b_tolerance_and_branch.md` §4.1's, AND IT IS THE
GROUND ON WHICH BRANCH C WAS REFUSED.** That section chose Branch B — a constraint
exists — and refused Branch C because retiring the constraint *"would leave the
fraction of the risk unit resting on an unvalidated estimate unbounded, at exactly
the point in the design where `docs/handoff/31_point_5_closing.md` §5.2 records
that the estimate is the largest remaining unknown in the exit model."*

**A TOLERANCE ABOVE 0.40 IS BRANCH C FOR TWO OF THREE SYMBOLS.** BTCUSDT and
ETHUSDT would carry no bound on the share of their risk unit resting on an
unvalidated estimate, while SOLUSDT would carry one. That is not a loose
constraint; it is the retired branch, reintroduced for part of the population by a
choice of level.

**AND IT REINSTATES THE DEFECT THE FIRST RE-DENOMINATION WAS MADE TO REMOVE.**
`docs/design/04_1a_denomination_amendment_1.md` §2.2 re-denominated on the finding
that the parameter had **zero authority over the cross-symbol distribution of the
protected quantity**. A tolerance above the smallest ceiling produces a
cross-symbol asymmetry in that same quantity — bounded on one symbol, unbounded on
two — **and does so under a setting rather than under a denomination.**

> **THE DEFECT WOULD RETURN THROUGH THE PARAMETER RATHER THAN THROUGH THE
> DEFINITION, WHICH MAKES IT HARDER TO SEE AND NOT LESS REAL.**

### 2.4 THE GRID ALREADY EXCLUDES IT, AND THAT IS NOT WHY IT IS EXCLUDED

**Report 36's committed grid runs 0.036 to 0.396, stopping inside the smallest
ceiling.** So no cell of that grid lies in the excluded regime.

> ### THAT IS A PROPERTY OF HOW THE GRID WAS BUILT. IT IS NOT AN ARGUMENT, AND IT
> ### IS NOT WHAT EXCLUDES THE REGIME.

Report 36 §2.5 records that the grid's upper end was fixed by taking the last
multiple of the step strictly below the smallest ceiling. **A domain that rested on
that fact would be a domain resting on a step size.** If the grid were ever
rebuilt, respaced, or extended, the exclusion would silently follow it.

**THE EXCLUSION IS THEREFORE COMMITTED HERE AS A DECISION, ON §2.3's GROUND, AND
STANDS INDEPENDENTLY OF ANY GRID.**

**THIS FOLLOWS THE PRECEDENT AT
`docs/handoff/34_point_4_1a_non_uniformity_rerun.md` §4.2**, which reported an
empty cap-clipped stratum and stated in the same breath that the emptiness was **an
artefact of grid construction rather than a finding** — that the stratum was empty
because the grid had been built to avoid it, and that reporting the zero without
that sentence would have been misleading. **The same discipline is applied here to
a bound rather than to a count.**

---

## 3. PRECEDENCE: REJECT, NOT CLIP

### 3.1 THE RULE

> ### WHERE THE WIDTH REQUIRED TO SATISFY THE CONSTRAINT EXCEEDS THE FROZEN STOP
> ### CAP, THE POSITION IS REJECTED AND DOES NOT ENTER THE POPULATION. IT IS NOT
> ### CLIPPED TO THE CAP.

A rejected position is a **skip**, on the treatment `docs/design/05_aggregate_risk_budget.md`
§3 gives to a refused position: not sized down, not retried, not deferred.

### 3.2 THE ARGUMENT

**THE MECHANISM, STATED IN THE RIGHT DIRECTION.** A required floor above the cap
means the position needs a **WIDER** stop than the cap allows. Clipping it to the
cap therefore makes the stop **NARROWER than the constraint requires** — not wider.

**A NARROWER STOP MEANS A SMALLER RISK UNIT AGAINST AN ALMOST UNCHANGED
UNVALIDATED SUM**, so the clipped position carries **a larger unvalidated share of
its risk unit than the tolerance permits.** It is precisely the position the
constraint exists to exclude, admitted in violation of the constraint.

**AND IT WOULD BE INDISTINGUISHABLE IN THE DATA FROM A COMPLIANT POSITION.** It has
a stop, a quantity and a risk unit like any other. Nothing about it records that
its floor was refused.

> ### A CONSTRAINT THAT SILENTLY DEGRADES EXACTLY WHERE IT BINDS HARDEST IS NOT
> ### PERFORMING THE FUNCTION `docs/design/04_1b_tolerance_and_branch.md` §4.1
> ### CLAIMS FOR IT.

That section keeps the constraint in order to bound the share of the risk unit
resting on an unvalidated estimate. **Clipping bounds it everywhere except where it
was in danger of exceeding the bound**, which is the only place the bound was doing
work.

### 3.3 THE TWO REJECTION POPULATIONS, PARTITIONED

**THEY ARE DIFFERENT REJECTIONS FOR DIFFERENT REASONS AND MUST NOT BE POOLED.**
A pooled count would attribute volatility rejections to cost protection and make
the constraint look as though it were removing positions it never touched.

#### POPULATION A — THE REQUIRED FLOOR EXCEEDS THE CAP

**A COST-PROTECTION REJECTION.** The constraint asks for a width the frozen cap
forbids.

**IT IS EMPTY ACROSS THE ADMITTED DOMAIN, BY CONSTRUCTION.** §2.1 sets the domain's
lower bound at the largest per-cell value of the ratio **at the cap**. At or above
that bound, every cell's required width is at or inside the cap. There is no
tolerance in the admitted domain at which this population can be non-empty.

> **THE RULE IS THEREFORE PRECAUTIONARY RATHER THAN OPERATIVE — AND IT IS WHAT
> MAKES THE DOMAIN's LOWER BOUND MEANINGFUL RATHER THAN ARBITRARY.**

The lower bound is not a taste about how tight a tolerance should be. It is the
point below which this rejection rule would start removing positions, and stating
the rule is what gives that point its content.

**IT BECOMES OPERATIVE ONLY IF THE DOMAIN IS EVER WIDENED DOWNWARD, OR IF THE
FROZEN CAP IS EVER LOWERED.** Either change makes it live, and either change must
therefore come with a count.

#### POPULATION B — THE RAW ATR-DERIVED STOP EXCEEDS THE CAP

**A VOLATILITY REJECTION.** The stop the bar geometry asks for is wider than the
cap, before any cost accounting occurs.

**IT IS INDEPENDENT OF THE TOLERANCE AND OF COST ACCOUNTING ENTIRELY.** It is a
property of the relationship between realised volatility and the frozen cap. No
value of the tolerance changes its membership by one position.

**IT IS NOT EMPTY.** Its size is a function of the data.

**IT IS NOT COUNTED HERE**, and counting it is not this document's business. **This
document commits no figure for it and no expectation about its size.**

### 3.4 THE RESULTING STRATIFICATION

**For kill condition (d)'s benefit, positions fall into exactly these strata:**

- **FLOOR-BOUND** — the constraint's floor, not the volatility, set the stop.
- **NOT FLOOR-BOUND** — the volatility set the stop, inside the cap and at or
  beyond the floor.
- **REJECTED (A)** — the required floor exceeded the cap. Empty across the admitted
  domain.
- **REJECTED (B)** — the raw stop exceeded the cap. Not empty.

> ### NO CLIPPED STRATUM EXISTS UNDER THIS RULE.

**THAT IS THE REASON THE RULE WAS CHOSEN AND NOT A CONSEQUENCE TO BE DISCOVERED.**
A clipped stratum would be a population of positions that violate the constraint
and look compliant, and no later stratification could separate them from positions
that were never at risk of violating it.

---

## 4. THE STANDARD A LEVEL-SETTING METHOD MUST MEET

### 4.1 THE SITUATION, STATED HONESTLY FIRST

**`docs/design/04_1b_tolerance_and_branch.md` §4.2 RECORDED THAT THE RATIONALE
JUSTIFIES THE CONSTRAINT'S EXISTENCE AND DOES NOT DISCRIMINATE BETWEEN CANDIDATE
VALUES.** It states this as a result rather than working around it, and routes to
4.1c *"a stated method for setting the level that does not read it off the
curve"*.

> ### THAT OBLIGATION IS STILL OPEN. THIS DOCUMENT DOES NOT DISCHARGE IT.

It commits the standard such a method must meet. **A standard is not a method**,
and calling it one would be the manufactured level-discriminating argument §4.2
warns against.

### 4.2 WHY NO DECISION CRITERION IS COMMITTED, STATED RATHER THAN DROPPED

`docs/handoff/34_point_4_1a_non_uniformity_rerun.md` §5.4 recommended a
ratio-based criterion, robust to multiplicative effects, to 4.1c. **It is not
committed, and the reason is that the question it tested no longer arises.**

That criterion tested whether the tolerance had **authority over the cross-symbol
distribution of the protected quantity**. Under the risk-unit denominator the
constraint and the protected quantity are **one object**, so the cross-symbol
spread of the protected quantity is **zero by construction**.

`docs/design/04_1c_denominator_choice.md` §3.3 commits that the prior apparatus is
**INAPPLICABLE rather than satisfied**, and §3.4 forbids reporting the resulting
figure as a favourable margin. **A criterion whose statistic is identically zero
cannot fire, and carries no information in not firing, because there is no state
of the world in which it would have fired.**

**IT IS THEREFORE NOT COMMITTED, AND THAT IS RECORDED HERE RATHER THAN THE
RECOMMENDATION BEING QUIETLY ALLOWED TO LAPSE.** A recommendation that disappears
without a stated reason is indistinguishable from one that was found inconvenient.

### 4.3 THE STANDARD, COMMITTED AS DISQUALIFYING PROPERTIES

> ### A PROPOSED LEVEL-SETTING METHOD IS DISQUALIFIED IF IT HAS ANY OF THESE
> ### PROPERTIES.

**(a) IT SELECTS THE LEVEL BY REFERENCE TO THE FLOOR WIDTHS THE CANDIDATE LEVELS
IMPLY, IN ANY FORM.** Including: because the implied widths are convenient; because
they are familiar; because they are close to the retired 1.50% floor; or because
they are comfortable against any stratum count. **Proximity to a previously used
number is not evidence about a level, and it is the most available substitute for
evidence.**

**(b) IT SELECTS THE LEVEL BY REFERENCE TO ANY QUANTITY THAT CANNOT BE COMPUTED
BEFORE THE LEVEL IS CHOSEN.** A method that needs the level in order to produce the
input that justifies the level selects nothing.

**(c) IT IS NOT EVALUABLE BY A READER WHO HAS THE COMMITTED DOCUMENTS AND NO
ACCESS TO THE PERSON WHO CHOSE IT.** A method that reduces to judgement exercised
privately is not a method. It may still be the honest thing to do — §4.4 says so —
but it must then be labelled as judgement rather than presented as a method.

**(d) IT DOES NOT STATE WHAT WOULD HAVE MADE A DIFFERENT LEVEL CORRECT.** A method
that returns one answer and cannot say what would have produced another is
rationalising rather than discriminating. **This is the property that distinguishes
a method from an argument for a conclusion already reached.**

**(e) IT IS NOT COMMITTED IN ITS OWN COMMIT BEFORE THE LEVEL IT SELECTS IS
STATED.** The order rule of `docs/design/04_0_decision_rule.md` §8, applied to the
method as it has been applied to every denomination in this sub-point.

### 4.4 A METHOD MEETING ALL OF THE ABOVE MAY NOT EXIST

> ### THAT IS A POSSIBLE OUTCOME, NOT A FAILURE.

`docs/design/04_1b_tolerance_and_branch.md` §4.2 already established that the
rationale does not discriminate between values. **Nothing since has supplied a
discriminating account**, and this document does not pretend one is forthcoming.

**IF `docs/design/04_1c_proper.md` CANNOT STATE A METHOD MEETING §4.3, THE HONEST
OPTIONS ARE THESE TWO:**

- **SAY SO, AND SELECT ON STATED JUDGEMENT, WITH THE JUDGEMENT RECORDED AS
  JUDGEMENT** — naming what was weighed, by whom, and what would have changed it,
  and explicitly not presented as derived.
- **REOPEN WHETHER A LEVEL IS NEEDED AT ALL** — which reopens Branch C, decided at
  4.1b §4.1, and would require an amendment to that document under its own change
  discipline rather than a silent reinterpretation here.

**NEITHER IS PREFERRED AND THIS DOCUMENT DOES NOT CHOOSE BETWEEN THEM.** Both are
named so that neither can later be presented as the only available course, and so
that arriving at 4.1c-proper without a method is a foreseen outcome rather than an
emergency.

---

## 5. THE CONSOLIDATED ERRATA INDEX

### 5.1 WHY IT EXISTS

**ERRATA ARE LOGGED, NOT PATCHED.** The corrected document is never edited, so
every correction lives in a **different** document from the one it corrects. They
have accumulated across seven documents. **A reader of a corrected passage has no
way to discover that it was corrected**, which is the failure mode the
logged-not-patched discipline creates and does not itself solve.

### 5.2 SCOPE, AND HOW THE SOURCES WERE SEARCHED

**SCOPE: corrections logged under the errata-not-patched discipline** — where the
target document was committed and frozen, and a later document carries the
correction. Entries name whether the target is **specification** (a member of the
frozen specification per `docs/design/04_0_divergence_disposition_amendment_2.md`
§2) or **evidence** (a report under `docs/handoff/`, which that section records as
cited and corrected by erratum but not binding).

**HOW THE SEARCH WAS RUN**, over `docs/` in full:

- for headings and markers containing "erratum" or "errata";
- for the project's correction idiom, a **STATED** claim paired with a
  **CORRECT** one;
- for correction language generally — "is wrong", "is incorrect", "is false", "is
  too strong", "is corrected", "mislabel", "misstat".

**DELIBERATELY EXCLUDED, AND NAMED SO THE EXCLUSION IS VISIBLE:** amendments a
document makes to **itself** before or at its own freezing are not errata, because
no frozen text is being corrected from outside. Two were found and set aside on
that ground — an appendix amendment inside `docs/handoff/08_point_4_pre_registration.md`
correcting one of its own explanatory glosses, and `docs/handoff/16_point_4_closing.md`
§4.3 correcting a claim in an earlier section of the same closing record. **A
reader who disagrees with that boundary can find both from the search terms
above.**

**THE INDEX IS COMPLETE AS OF THIS COMMIT ONLY.**

### 5.3 THE INDEX

**ENTRY 1. Document 06a §2.3 — the one-settlement overcharge figure.**
*Target: specification.* **SAID:** the overcharge is about 0.0067R at the 1.50%
floor stop, as `rate / s`. **CORRECT:** as a share of a realised risk unit it is
`rate / (s + c + funding)` = 0.00589R at the floor stop. §4.2 of that same
document forbids the denominator §2.3 used. **CORRECTION LIVES AT:**
`docs/handoff/31_point_5_closing.md` §8, erratum 1. **Not operative** — the figure
constructs nothing and the stated value is the conservative direction.

**ENTRY 2. Document 06a §2.4 — the rejected reading's breakeven.**
*Target: specification.* **SAID:** approximately 39.7%. **CORRECT:** 39.8%,
following from entry 1's corrected share. **CORRECTION LIVES AT:**
`docs/handoff/31_point_5_closing.md` §8, erratum 2. **Not operative** — it is a
figure in a rejected branch, and the adopted reading's frozen 40.0% is unaffected.

**ENTRY 3. Document 06a §5.1 — the completeness table's population labels.**
*Target: specification.* **SAID:** 1,578,240 rows pooled, and three per-symbol
figures. **CORRECT:** 1,578,240 is per symbol, the three-symbol total is
4,734,720, and the three figures labelled as three symbols are three years for one
symbol. **CORRECTION LIVES AT:** `docs/handoff/31_point_5_closing.md` §8,
erratum 3. **Not operative** — the numbers are right and the populations attached
to them are not. Logged in that record's ledger as instance (29).

**ENTRY 4. Document 06a §5.2 — a claim that was false when written.**
*Target: specification.* **SAID:** the holdout window has never been examined for
1m completeness and cannot be without opening the seal. **CORRECT:** it had been,
by a path that ran on every test invocation, and the row counts exist on disk.
**CORRECTION LIVES AT:** `docs/handoff/31_point_5_closing.md` §8, erratum 4.
**Partly operative** — E8.1's requirements are unchanged and binding, but the
argument for them must be restated on the corrected footing.

**ENTRY 5. Report 24 §10.1 — the defect-ledger instance count.**
*Target: evidence.* **SAID:** "the eighth instance". **CORRECT:** the seventeenth.
**CORRECTION LIVES AT:** `docs/handoff/31_point_5_closing.md` §8, erratum 5.
**Not operative** — it changes no measurement, only the ledger.

**ENTRY 6. Point 5 closing record §5.1 — the required-floor figure labels.**
*Target: evidence.* **SAID:** required floors of 1.530% and 1.561% for "(BTC,
ETH)" and 1.971% and 2.030% for SOL, the parenthetical labelling the first pair as
two symbols. **CORRECT:** BTCUSDT and ETHUSDT share a curve exactly, so each pair
is the long and short legs of one shared curve, not two symbols. The figures are
correct and the population labels are wrong. **CORRECTION LIVES AT:**
`docs/design/04_1a_denomination.md` §5. **Not operative as to the figures.** That
section records it as the third occurrence of the right-numbers-wrong-population
shape.

**ENTRY 7. Point 5 closing record §5.3 — the 0.0067R attribution.**
*Target: evidence.* **SAID:** both the rejection of the realised-cash-flow funding
treatment and the numeral "roughly 0.0067R" are attributed to document 06 §5.4.
**CORRECT:** the numeral is not in that section; where it appears, at document 06a
§2.3, it denominates a different quantity — the adopted reading's overcharge, not
the rejected treatment's breach. Document 06 §5.4's rejection is categorical and
states no magnitude. **CORRECTION LIVES AT:**
`docs/design/04_0_divergence_disposition_amendment_2.md` §6, resting on
`docs/design/04_0_divergence_disposition_amendment_1.md` §5.1. **Partly
operative** — the numeric comparison is withdrawn; the structural claim that 4.1
owes a reconciling criterion survives and is stated more exactly.

**ENTRY 8. Divergence disposition §4 — the same pairing, in the base document.**
*Target: specification.* **SAID:** "The magnitude at stake there is stated as
roughly 0.0067R in … §2.3", attaching a figure that denominates the adopted
reading's overcharge to a claim about the rejected treatment's breach.
**CORRECT:** the pairing does not govern; the magnitude of the rejected breach is
unsourced in the sections examined and is recorded as supplied but unsourced,
pending derivation. **CORRECTION LIVES AT:**
`docs/design/04_0_divergence_disposition_amendment_1.md` §5.1 and §5.3.
**Partly operative** — one sentence does not survive as stated and the argument it
supported does.

**ENTRY 9. Denomination amendment 1 §2.3 — the claim about when the evidence
existed.** *Target: specification.* **SAID:** the amendment was *"made on evidence
that did not exist when the decision was made"*. **CORRECT:** the measurement did
not exist, but the structural fact did — the invariance of the cross-symbol ratio
is a property of report 32's closed form, which was committed before 4.1a was
written, and could have been read off the algebra. The claim is too strong.
**CORRECTION LIVES AT:** `docs/design/04_1c_denominator_choice.md` §5.4. **Not
operative** — the amendment's decision stands; what is corrected is its account of
its own timing.

### 5.4 THE MAINTENANCE RULE

> ### ANY DOCUMENT MAKING A CORRECTION TO A FROZEN ARTIFACT ADDS ITS ENTRY TO THIS
> ### INDEX IN THE SAME COMMIT.

**Not afterwards, and not in a later consolidation pass.** An index updated
separately from the corrections it indexes is an index that is wrong between
commits, and the gap is exactly where a correction gets lost.

**Adding an entry is an amendment to this document under §7** — a new document with
its own commit — because this one is frozen on commit like any other
pre-registration.

**POINT 4's CLOSING RECORD CARRIES THE FINAL INDEX**, consolidated from this one
and every amendment to it.

---

## 6. WHAT THIS DOCUMENT DOES NOT DO

**IT SELECTS NO TOLERANCE VALUE**, and names no sub-interval of the admitted domain
as attractive. Owed by `docs/design/04_1c_proper.md`.

**IT STATES NO FLOOR WIDTH AS GOVERNING.** Report 36's figures appear only as facts
about the ratio's structure. Owed by `docs/design/04_1c_proper.md`.

**IT PERFORMS NO DOMINANCE CHECK.** Owed by `docs/design/04_1c_proper.md`, per
`docs/design/04_1a_denomination.md` §4.1.

**IT DOES NOT DISPOSE OF KILL CONDITION (d).** §3.4 supplies the stratification
that disposition will need and does not make it. Owed by
`docs/design/04_1c_proper.md`.

**IT SETS NO MAGNITUDE THRESHOLD.** Owed by `docs/design/04_1c_proper.md`.

**IT COMMITS NO LEVEL-SETTING METHOD, ONLY THE STANDARD ONE MUST MEET.** Owed by
`docs/design/04_1c_proper.md`.

---

## 7. CHANGE DISCIPLINE

**A CHANGE TO ANY COMMITMENT HERE IS A NEW DOCUMENT WITH ITS OWN COMMIT AND AN
EXPLICIT STATEMENT OF WHAT CHANGED AND WHY — NEVER A SILENT EDIT.** It would be
`docs/design/04_1c_pre_commitments_amendment_1.md`.

**A SILENT EDIT IS A CONTAMINATION EVENT.**

### 7.1 THE CLAUSE MOST EXPOSED TO LATER PRESSURE

> ### §4's STANDARD IS THE CLAUSE MOST EXPOSED, AND IT IS WRITTEN TO BE
> ### INCONVENIENT AT THE MOMENT IT BINDS.

**IT BINDS EXACTLY WHEN A LEVEL MUST BE CHOSEN AND NO DISCRIMINATING METHOD HAS
BEEN FOUND.** At that moment property (a) forbids the most natural available move —
choosing a level because the widths it implies look reasonable — and property (d)
forbids the most natural available defence, an argument that supports the chosen
level without saying what would have supported another.

**THE PRESSURE WILL NOT PRESENT ITSELF AS PRESSURE.** It will present itself as a
sensible level that happens to be defensible, and the standard will look like
pedantry obstructing an obvious answer. **That is what it is for.** §4.4 exists so
that the way out is to name the judgement as judgement, not to weaken the
standard.

> **IF THIS DOCUMENT IS AMENDED TO RELAX §4.3 AFTER CANDIDATE WIDTHS HAVE BEEN
> SEEN, THE AMENDMENT MUST SAY SO IN THOSE WORDS**, and a reader is entitled to
> weigh it accordingly.

---

## 8. THE LEDGER

**`docs/design/04_1c_denominator_choice.md` §5.5 states "42 + 1 = 43". The total
read is 43.**

**THIS DOCUMENT ADDS NO INSTANCE AND THE TOTAL IS UNCHANGED AT 43.** It records no
new defect: §5's index consolidates corrections already logged and logs none of its
own, and the four commitments rest on findings already established elsewhere.

---

**Committed alone, before any tolerance value is selected. One domain admitted and
one regime excluded on the ground that vacuity is Branch C by another route; one
precedence committed with its two rejection populations partitioned and one of them
stated empty by construction; one standard committed in place of a method that does
not exist, with both honest outcomes named and neither preferred; one errata index
initialised at nine entries with its scope and its search stated, and a maintenance
rule attached. No tolerance value is selected, no floor width is stated as
governing, and no magnitude threshold is set.**
