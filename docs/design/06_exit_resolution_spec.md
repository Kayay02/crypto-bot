# EXIT RESOLUTION SPECIFICATION — PRE-REGISTERED

**Status: FROZEN at this commit.** Committed with the constants module it
specifies, its tests, and the raw venue snapshot §6 rests on — and nothing else.
**No backtest was run. No exit was evaluated against any real bar. No 1m bar was
read.** The commit hash is the proof that the conventions preceded any engine
capable of reporting what they do.

**Point 5, sub-point 5.3, step 2.** Steps 5.3.0 and 5.3.1 are closed.

---

## 1. WHAT THIS IS, AND WHY IT IS A BLINDER COMMITMENT THAN THE BUDGET WAS

**WHAT IS SPECIFIED, IN ONE BLOCK:**

| | rule |
|---|---|
| **E1** | stops, targets and time exits are evaluated on **1m** bars |
| **E2** | the stop is a conditional market order — a **touch** fills, inclusive |
| **E3** | the target is a resting maker limit order — a **trade-through by one tick** fills |
| **E4** | when one 1m bar satisfies both, the **stop** is taken, and it is counted |
| **E5** | on the max-hold bar, the **stop** is evaluated across the bar, the time exit only at its close |
| **E6** | the time exit is unchanged from the frozen thesis |
| **E7** | funding is charged **at entry, in the sizing denominator**, at the maximum settlements crossable |
| **E8** | missing 1m bars are **flagged and counted**, never silently absorbed |
| **E9** | what remains convention even at 1m is listed, not implied |

### 1.1 THIS CANNOT BE ADJUDICATED THE WAY DOCUMENT 05's RULES WERE

> **DOCUMENT 05's RULES WERE ADJUDICATED BY COUNTING.** Report 26 measured the
> skip rate, the rotation's neutrality across symbols and Rule C's 902-position
> gain **without touching a single outcome.** Every one of those is a count of
> signals, bars or allocations, and the performance firewall never had to move.
>
> **THESE CONVENTIONS CANNOT BE ADJUDICATED THAT WAY.** E2, E3 and E4 decide
> **which exit a trade takes**, and the quantity that would tell you whether a
> convention was well chosen is the **win rate** — which is firewalled until the
> validation design is separately pre-registered.
>
> **SO THIS IS A BLIND COMMITMENT IN A STRONGER SENSE THAN DOCUMENT 05 WAS, AND
> IT IS NOT ON EQUAL FOOTING WITH IT.**

**WHAT IS AND IS NOT AVAILABLE AS A CHECK.** 5.3.4 will be able to report **how
often** each convention decided something — E4's precedence count, E8's flagged
fraction, the target-fill count. **Those are frequencies, not verdicts.** A
convention that fires on 3% of trades might be harmless or might be the whole
result, and **nothing in Point 5 can distinguish those two cases.** Only the
validation design can, and it must be written before it is allowed to look.

**WHY THIS IS STILL WORTH DOING.** The alternative is not "adjudicate them
properly" — that option does not exist at this stage. The alternative is
**choosing them later, with an engine on the desk that can report outcomes**, at
which point the choice is contaminated whether or not anyone intends it. **A
blind commitment that is provably blind beats a sighted one that claims not to
be.**

**EACH RULE BELOW CARRIES ITS GROUND AND ITS COST.** Where a rule is
conservative, the direction is stated **in advance**, on the terms Amendment 2
§5 set for Rule C, so it cannot later be presented as a discovery.

---

## 2. E1 — RESOLUTION: 1m

**Stops, targets and time exits are evaluated on 1m bars. Signals, indicators
and entries remain on 1h and are unchanged.**

**THE GROUND** is report 27 (`60b66f5`), which measured the per-trade upper bound
on trades whose stop and target could **both** lie inside a single 1h bar at
**10.21%** hold-weighted and **11.94%** at maximum hold, against a criterion of
**2.0%** — exceeded by **5.1×**, independently on every symbol and in every one
of the eighteen fold periods.

**AND THE FIGURE IS AN UPPER BOUND ON AN UPPER BOUND.** Report 27 §7 stacks five
reasons the true fraction is lower — chiefly that a bar large enough to contain
both levels is usually not *positioned* to contain them. **The verdict does not
depend on how loose the bound is**: the stack would have to be wrong by more
than a factor of five, in the same direction, on every symbol and every fold.

**THE COST.** Closing the 1m holdout seal gap becomes a precondition for 5.3.4.
That is 5.3.3's work and it is the largest single piece of work in Point 5.3.
**This specification does not touch the 1m loader** — the seal gap is open and
this step reads no bar at any resolution.

---

## 3. E2 — STOP FILL: A TOUCH FILLS

**The stop is a conditional MARKET order.** It fills when the 1m bar reaches the
stop price:

    long    low  <= stop_price          short   high >= stop_price

**The comparison is INCLUSIVE.** A market order triggered at the level fires at
the level; there is no queue to be behind, because a market order does not rest.

**FILL PRICE is the stop price adjusted by the pre-registered stop haircut** from
`CostConfig` — **5 bps on BTCUSDT and ETHUSDT, 10 bps on SOLUSDT** — applied
through the level, which `costs.stop_fill_price` already implements and report
28's sizing already charges inside the risk denominator.

### 3.1 THE INHERITED WEAKNESS, STATED PLAINLY

> **THE STOP HAIRCUT IS AN UNMEASURED PLACEHOLDER, AND IT *IS* THE ENTIRE
> SLIPPAGE-AND-GAP MODEL.**

`src/engine/costs.py` says so in its own source — *"Stop-market haircut, bps of
the stop price. Placeholders, per spec."* — and report 25 §2 confirmed it is not
a venue-published figure.

**IT IS NOT A SMALL TERM.** Report 28 §9 measured that **3,507 of 11,384
positions (30.81%) charge more than the frozen `COST_TOLERANCE_R = 0.11`**, and
that **SOLUSDT contributes 540 of those, of which 419 — 77.6% — are NOT
floor-bound.** Those 419 are above the tolerance *because of the 10 bps
haircut*, not because of the stop floor: SOL's haircut pushes `c/s` past 0.11 at
any stop tighter than about 2%.

*(A FIGURE FROM THE BRIEF THAT COULD NOT BE REPRODUCED, recorded rather than
repeated: the brief for this step put SOLUSDT's haircut-driven share of its
cost-tolerance breach at "35%". No such figure appears in report 28 §9 and none
of its ratios produces it. **The sourced figures are the ones above — 540 SOL
positions above the tolerance, 419 of them (77.6%) not floor-bound** — and they
are used instead. The frozen report wins over the brief.)*

**SO THE ONE NUMBER STANDING BETWEEN THIS MODEL AND REALITY ON THE STOP LEG HAS
NEVER BEEN MEASURED**, and it is the number that decides what a stop-out
actually costs. Report 18 closed the *slippage* question above 1.00% stops on a
tick-size lower bound, and explicitly noted that *"a tick-size floor therefore
UNDERSTATES stop-leg slippage, by an unknown amount"* — because the stop leg is
always taker and fires precisely when spreads widen.

**NOTHING HERE MEASURES IT AND NOTHING HERE CHANGES IT.** It is recorded as an
inherited weakness of the specification, and it is the largest one.

---

## 4. E3 — TARGET FILL: A TRADE-THROUGH BY ONE TICK

**The target is a resting MAKER LIMIT order.** It fills when price trades
through it:

    long    high >= target_price + tick     short   low <= target_price - tick

**THE GROUND.** A resting order does not fill because price *touched* it; it
fills because someone crossed the spread and traded *through* it. Price printing
exactly at a resting limit is evidence that the level was reached, **not that
our order was filled** — it may have been filled against the queue ahead of us.

**`tick` IS THE SYMBOL'S PRICE TICK AT THAT TIMESTAMP, NOT PER SYMBOL.** Report
28 §10 records that SOLUSDT's tick changed from 0.0001 to 0.001 on
**2024-08-14**, inside the measurement window, and that report 28's own sizing
resolves it per bar timestamp through `contracts.TickSchedule.tick_at`. **The
same resolution applies here.**

**WHY ONE TICK AND NOT A FREE PARAMETER.** The tick is the **smallest price
increment that exists**. It is therefore the only trade-through margin that is
not an arbitrary choice: two ticks, or a basis point, or half a spread would all
be **tunable parameters entering a pre-registration**, and this project's record
is unambiguous about what those become.

**FILL PRICE IS THE TARGET PRICE.** No haircut and no improvement: a resting
limit order that fills, fills at its own price.

### 4.1 THE COST, STATED IN ADVANCE

> **THIS IS STRICTLY MORE CONSERVATIVE THAN FILL-ON-TOUCH, ON THE LEG THAT
> PRODUCES EVERY WINNER.** It will report **fewer target fills** than a touch
> rule would. Every trade whose 1m high reaches the target exactly and goes no
> further is, under this rule, **not a winner**.

**The direction is stated here, before any count exists**, on the same terms
Amendment 2 §5 set for Rule C — *"so it cannot later be presented as a
discovery"*. If 5.3.4 reports a low target-fill rate, **part of that is this
rule**, and this paragraph is what makes that checkable rather than arguable.

**THE ASYMMETRY IS DELIBERATE AND IT IS WORTH NAMING.** E2 fills the stop on a
touch; E3 requires a trade-through for the target. **The pessimistic choice is
made on both legs** — the losing leg fills easily, the winning leg fills hard.
That is the correct direction for a rule chosen blind, and it is not free: if
the true fill behaviour is more generous, this specification understates the
strategy, and nothing here can say by how much.

### 4.2 WHAT IT DOES NOT FIX

> **`MAKER_NONFILL_SLIP` REMAINS 0.0 AND IS NOT CHANGED HERE.**

**A trade-through is evidence that a resting order COULD have filled. It is not
evidence about queue position.** If price trades one tick through our limit and
there were a thousand contracts ahead of us, we did not fill. The trade-through
rule addresses **whether the market reached us**; the non-fill constant
addresses **whether we were reached first**. They are different questions and
the first does not answer the second.

The closing record §5.2 records that this constant was invisible to **all 545
tests then in the suite, because every one of them multiplied it by zero**, and
§6.3 routes it to Point 6 as the term that blocks any maker-entry variant.
**Changing it is not this step's business.** Recording that E3 does not
substitute for it is.

---

## 5. E4–E7 — PRECEDENCE, TIME EXIT, AND FUNDING

### 5.1 E4 — INTRABAR PRECEDENCE: STOP FIRST, AND COUNTED

**When one 1m bar's range satisfies BOTH fill conditions, the STOP is taken.**

**THE GROUND is pessimism, and the reason it needs stating at all is that the
alternative is silence.** At 1m the geometry that produced report 27's 10.21% at
1h makes this far rarer — a 1m bar must span the whole stop-to-target distance —
**but "far rarer" is not "specified"**, and an unspecified case is decided by
**whichever comparison the implementer happened to write first**, which is the
worst possible way to decide it.

> **EVERY TRADE RESOLVED BY THIS RULE IS FLAGGED AND THE COUNT REPORTED BY
> 5.3.4.** The convention is not assumed negligible; its frequency is made a
> reported quantity, so §1.1's "frequencies, not verdicts" limit is at least
> supplied with its frequency.

### 5.2 E5 — STOP versus TIME EXIT ON THE SAME BAR: STOP FIRST

**Within the 1m bar that carries the max-hold exit, the stop is evaluated across
the whole bar and the time exit only at its close.**

**THIS IS NOT A PREFERENCE. IT IS WHAT THE TWO ORDER TYPES ARE.** The stop is a
resting conditional order that fires the instant price touches it, at any moment
of the bar. The time exit is an **action taken at a bar close** — a market order
we send. A stop touched at second 3 of the minute has already fired before the
close exists.

### 5.3 E6 — THE TIME EXIT, UNCHANGED FROM THE FROZEN THESIS

**Close of the 1h bar preceding the THIRD funding settlement strictly after
entry**; settlements at 00:00 / 08:00 / 16:00 UTC; **n = 3**; elapsed hold in
[16h, 24h]. Report 24 §5.2 measured the attainable set as **{17, …, 24} hours**,
with 16 unattainable on an hourly grid.

**Execution is a taker market order at that 1h bar's close.** Not a limit, not a
maker order: a time exit that does not execute is not a time exit.

**Nothing in this document changes any part of it.** It is restated so the
specification is complete in one place.

### 5.4 E7 — FUNDING: CHARGED AT ENTRY, IN THE SIZING DENOMINATOR

> **DECISION: funding is charged AT ENTRY, inside the per-unit risk
> denominator, at the MAXIMUM number of settlements the position could cross.**

**THE GROUND.** The project's standing risk rule is **$20 fixed risk per trade
after fees and estimated slippage** — 1% of equity, enforced after costs.
**Funding is a cost of holding.** A trade whose geometric loss is exactly $20.00
*and* which also paid funding has **breached the rule**. Charging funding at
entry, inside the denominator, keeps the worst-case stop-out at or below 1.0R —
which is what the rule requires and what report 28's stop identity asserts.

**THE ALTERNATIVE THAT WAS REJECTED**: charging funding as a **realised cash flow
per settlement actually crossed**. It is *exact* — it charges what was paid, when
it was paid — and it is rejected because **it lets a stop-out return worse than
−1.0R**. A trade that crossed two settlements and then stopped out would lose
the risk unit plus the funding, and the standing rule would be breached on
exactly the trades where breaching it matters most.

**THE COST OF THE CHOICE, STATED HONESTLY.** Every position that exits before its
maximum hold **has been charged for settlements it never crossed**. That is a
**systematic overcharge concentrated on FAST EXITS**, and fast exits are
disproportionately **stop-outs** — so the overcharge falls hardest on the losing
side, making losses look slightly worse than they were. **The choice is made on
risk-rule compliance grounds and it is not free.**

---

## 6. THE FUNDING SETTLEMENT COUNT — DERIVED, NOT ASSUMED

**The count is derived from the frozen time-exit definition and the funding
calendar, enumerated over all 24 possible entry hours.**

**THE DERIVATION.** Bar timestamps are OPEN times (report 24 §1.1), so entry at
the close of 1h bar `T` is the instant `T + 1h`. The time exit is the close of
the bar preceding the third settlement strictly after that instant — call it
`s3` — which at 1h alignment is the instant `s3` itself. **The position is
therefore held across the interval `[entry, s3)`**, and the settlements it
crosses are those falling in that half-open interval.

| bar open | entry instant | s1 | s2 | s3 = exit | hold | **settlements crossed** |
|---|---|---|---|---|---:|---:|
| 00:00 | 01:00 | 08:00 | 16:00 | 00:00 | 23h | **2** |
| 01:00 | 02:00 | 08:00 | 16:00 | 00:00 | 22h | **2** |
| 02:00 | 03:00 | 08:00 | 16:00 | 00:00 | 21h | **2** |
| 03:00 | 04:00 | 08:00 | 16:00 | 00:00 | 20h | **2** |
| 04:00 | 05:00 | 08:00 | 16:00 | 00:00 | 19h | **2** |
| 05:00 | 06:00 | 08:00 | 16:00 | 00:00 | 18h | **2** |
| 06:00 | 07:00 | 08:00 | 16:00 | 00:00 | 17h | **2** |
| **07:00** | **08:00** | 16:00 | 00:00 | 08:00 | **24h** | **3** |
| 08:00 | 09:00 | 16:00 | 00:00 | 08:00 | 23h | **2** |
| 09:00 | 10:00 | 16:00 | 00:00 | 08:00 | 22h | **2** |
| 10:00 | 11:00 | 16:00 | 00:00 | 08:00 | 21h | **2** |
| 11:00 | 12:00 | 16:00 | 00:00 | 08:00 | 20h | **2** |
| 12:00 | 13:00 | 16:00 | 00:00 | 08:00 | 19h | **2** |
| 13:00 | 14:00 | 16:00 | 00:00 | 08:00 | 18h | **2** |
| 14:00 | 15:00 | 16:00 | 00:00 | 08:00 | 17h | **2** |
| **15:00** | **16:00** | 00:00 | 08:00 | 16:00 | **24h** | **3** |
| 16:00 | 17:00 | 00:00 | 08:00 | 16:00 | 23h | **2** |
| 17:00 | 18:00 | 00:00 | 08:00 | 16:00 | 22h | **2** |
| 18:00 | 19:00 | 00:00 | 08:00 | 16:00 | 21h | **2** |
| 19:00 | 20:00 | 00:00 | 08:00 | 16:00 | 20h | **2** |
| 20:00 | 21:00 | 00:00 | 08:00 | 16:00 | 19h | **2** |
| 21:00 | 22:00 | 00:00 | 08:00 | 16:00 | 18h | **2** |
| 22:00 | 23:00 | 00:00 | 08:00 | 16:00 | 17h | **2** |
| **23:00** | **00:00** | 08:00 | 16:00 | 00:00 | **24h** | **3** |

> ### THE ANSWER IS NOT THREE FOR MOST ENTRIES.
>
> **21 of the 24 entry hours cross TWO settlements. Three cross THREE.**
> The three are exactly the hours where **the entry instant coincides with a
> settlement** — the position is open at that settlement and pays it — and those
> are also exactly the 24-hour holds.
>
> **THE MAXIMUM IS 3, AND 3 IS WHAT IS CHARGED.**
> `FUNDING_SETTLEMENTS_CHARGED = 3`.

### 6.1 THE CONSEQUENCE FOR THESIS §5.3's 0.022R — a finding, not a repair

**The number matches. The meaning does not.**

Thesis §5.3 derives `n` from a funding budget:

> `n = 0.022 × 0.0150 / 0.0001 = 3.3` → ROUNDED DOWN to **n = 3**

with `n` defined **in that derivation** as *"the number of settlements
crossed"*. It then uses the same `n = 3` as a **settlement INDEX** in the exit
rule — *"the third funding settlement after entry"*.

> **THOSE ARE TWO DIFFERENT QUANTITIES AND THE ENUMERATION SHOWS THEY DO NOT
> COINCIDE.** Used as an index, `n = 3` produces a rule under which the typical
> position crosses **two** settlements, not three. The count-crossed and the
> index agree only on the 3 boundary hours in 24.

**THE FROZEN BUDGET IS NOT BREACHED — IT IS UNDERSPENT.** At the maximum of 3
settlements and the floor stop `s = 1.50%`:

    funding_in_R = rate x n / s = 0.0001 x 3 / 0.0150 = 0.0200R   <=  0.022R

and at the typical count of 2, **0.0133R** — about **60% of the budget**. **The
rule as written is more conservative than its own derivation assumed**, which is
the safe direction.

**IT IS RECORDED AS A FINDING AND ROUTED, NOT REPAIRED.** Thesis §5.3 is frozen;
nothing here edits it. This is the **third** instance of the closing record §4's
recurring defect class — *"a numerical criterion written from a mental model of
a quantity rather than from its implementation"* — and it is a mild one, because
it errs conservatively and changes no threshold. **It is carried to the
validation design**, which owes an account of `COST_TOLERANCE_R`'s justification
anyway (amendment 1 §7), and the funding budget is part of that account.

### 6.2 The rate, and the sign

**`FUNDING_RATE_PER_SETTLEMENT = 0.0001` — 0.01% per 8h — IS AN ASSUMPTION, NOT
A MEASUREMENT**, in the same terms thesis §5.3 uses: *"Bitget funding history
available to this project covers roughly 90 days against a three-year test
window. The rate cannot be verified over the period being tested."* The derived
layer confirms it — the Bitget funding series runs from 2026-04-27, **270
records**, against a 2022–2024 window.

**FUNDING IS DIRECTIONAL IN REALITY.** Longs pay shorts when the rate is
positive and the reverse when it is negative; a position can *receive* funding.
**This model charges it as an UNSIGNED COST TO BOTH SIDES.** That is the
conservative treatment — it never credits a position with funding it might not
receive — and it is stated as such rather than left to be discovered as an
asymmetry.

---

## 7. THE VENUE RETRIEVAL — TRIGGER PRICE BASIS

**RETRIEVED. The question was: does Bitget trigger conditional stop and
take-profit orders on LAST price or MARK price, and is that a default or a
per-order parameter?**

**WHY IT MATTERS.** This project's OHLCV is **LAST** price. If the venue
triggered on **mark**, every stop in the backtest would fire at a different
instant than it would live, and mark price is smoother than last, so the
backtest would misstate stop-outs in a direction that cannot be signed without
knowing the answer.

### 7.1 The answer

| question | answer |
|---|---|
| **is it a per-order parameter?** | **YES** — `triggerType` |
| **allowed values** | **`fill_price`** (fill / LAST price) and **`market_price`** (mark price; the v2 pages spell it `mark_price`) |
| **default on the stop-profit / stop-loss endpoint** | **`fill_price`** — the parameter is optional there and the documentation declares the default explicitly |
| **on the plain trigger-order endpoints** | **REQUIRED** — no default applies |
| **does it differ between stop and take-profit?** | **NO** — one `triggerType` governs both legs of a TP/SL order; no page documents a per-leg basis |

**The retrieved parameter table, verbatim after tag-stripping:**

    triggerType   String   No    Trigger Type default 'fill_price'      (TPSL)
    triggerType   String   Yes   Trigger type                           (plan order)

and the value glossary:

    triggerType   Words          Description
                  fill_price     fill price
                  market_price   mark price

> **THE SPECIFICATION IS WRITTEN AGAINST LAST PRICE BECAUSE THAT IS THE DATA WE
> HAVE — AND THE VENUE AGREES BY DEFAULT ON THE ENDPOINT THAT MATTERS.**

**THE OPERATOR REQUIREMENT THAT FOLLOWS.** `triggerType` must be set
**EXPLICITLY to `fill_price` on every conditional order**, never left to a
default. This project's own Point 3R lesson is exactly this: four parameters had
their defaults *removed* because *"a stale placeholder acting as a chosen value
is the failure mode being corrected"*. A default that happens to be right is
still a value nobody chose.

### 7.2 Provenance, and the boundaries of the retrieval

Method per report 25: pages discovered rather than hardcoded, **raw bodies
written before any parsing**, SHA-256 recorded, nothing approximated.

| snapshot | bytes | SHA-256 |
|---|---:|---|
| `trigger_basis__v1_mix_doc.html` | 738,091 | `311ed34f82bf6defc6bf9f0489c47d036d3691ab3f37e46c475ffcb41bd07961` |
| `trigger_basis__v2_place_tpsl.html` | 23,627 | `fea1f4a67519e6d61b3e9d4db079d214e3006a0b1f3ebb88079eeada6f32eac4` |
| `trigger_basis__v2_place_plan.html` | 23,627 | `fea1f4a67519e6d61b3e9d4db079d214e3006a0b1f3ebb88079eeada6f32eac4` |
| `trigger_basis_manifest.json` | — | `6e7d1201dd2d09ceb23d89ad8c2fde24aadab7d1dfdd763f60974b0b0d49b7a0` |

Retrieved **2026-08-13**, under `data/reference/bitget_venue/`, the convention
report 25 established. Script: `src/venue/trigger_basis.py`.

**THREE BOUNDARIES, STATED RATHER THAN SMOOTHED:**

1. **THE v2 PAGES RETURNED AN APPLICATION SHELL.** Both hash **identically** —
   the same 23,627-byte shell — confirming report 25's finding that
   `www.bitget.com/api-doc/…` is JS-rendered and carries no endpoint content to
   an automated fetch. **The default is read from Bitget's own STATIC v1
   documentation mirror**, and the v2 default is **not independently
   corroborated.**
2. **NO LIVE ORDER WAS PLACED.** Placing one requires a signed request and this
   project holds no credentials in this path. The default is read from
   documentation, **not confirmed against venue behaviour.**
3. **THE v1 DOCUMENTATION IS THE DEPRECATED API.** It is Bitget's own published
   documentation and the parameter survives into v2 with a renamed mark-price
   token, but a default documented for v1 is evidence about v2, not proof.

**BECAUSE THE ANSWER IS LAST PRICE, NOTHING IS REDESIGNED.** Had it been mark
price, this section would have recorded it as a named limitation with its
direction of effect and routed it to the validation design; the specification
would have stood unchanged, because last price is the only data that exists.

---

## 8. E8 — MISSING 1m BARS: FLAGGED AND COUNTED

**THE RULE.** A position whose open interval contains one or more missing 1m
bars is **FLAGGED with the count of missing bars**. The position is resolved on
the bars that exist. **The flagged fraction is reported by 5.3.4.**

**WHY FLAGGING RATHER THAN A FILL CONVENTION.**

> **A MISSING BAR IS NOT A PRICE GAP. A gap is something the market did; a hole
> is something the data does not know.**

If a level was crossed inside an absent minute, **any** fill convention records
an event that may not have happened, at a price nobody observed — and does so
**invisibly**, producing a trade table in which the invented fills are
indistinguishable from the observed ones. **Flagging makes the exposure
countable.**

### 8.1 The completeness figures, cited not re-measured

**Report 19 (`74e3ca9`) measured this directly on the derived layer** and states
that both source layers are **exactly full** over 2022-01-01 to 2024-12-31
(1,096 days):

| layer | rows | expected | status |
|---|---:|---|---|
| **1m** | **1,578,240** | 1,096 × 1,440 = 1,578,240 | **exact** |
| 15m | 105,216 | 1,096 × 96 = 105,216 | exact |

with **zero buckets dropped anywhere** — a figure report 19 verified rather than
assumed, *"since that is the kind of clean number that usually means a counting
bug"*.

**Per symbol per year**, from the derived layer's build manifest:

| symbol | 2022 | 2023 | 2024 |
|---|---:|---:|---:|
| BTCUSDT | 525,600 | 525,600 | 527,040 |
| ETHUSDT | 525,600 | 525,600 | 527,040 |
| SOLUSDT | 525,600 | 525,600 | 527,040 |
| **expected** | 365 × 1,440 | 365 × 1,440 | **366** × 1,440 (leap) |

**Every cell is exact. 1m completeness over the measurement window is 100.000%
on all three symbols.**

*(The per-year table comes from `data/derived/_manifest.json`, which is **not a
tracked file** — `/data/` is ignored wholesale. The committed, citable source is
report 19, which states the same fact as a pooled total. The Point 2 artifacts
that are committed — `reports/integrity_report.txt`, `reports/probe_1m.txt` —
cover the 15m layer's integrity and the 1m endpoint's retention and shape
respectively, not 1m completeness.)*

### 8.2 SO THIS RULE IS INERT IN-SAMPLE, AND IT IS SPECIFIED ANYWAY

> **THE FLAGGED FRACTION OVER 2022–2024 WILL BE ZERO.** There are no missing 1m
> bars to flag.

**This is the third inert branch in this project's specification chain**, and it
gets the same treatment as the first two — document 05 §4's partial allocation
and report 28 §6's viability predicate: **specified, documented as unreachable at
present values, and carrying tests that exercise it at values where it IS
reachable.** The closing record §5.2's rule applies: *"any placeholder committed
at zero requires a PROBE-BASED test at construction time that sets it non-zero
and pins the structural consequence."*

**IT IS NOT INERT OUT OF SAMPLE, AND THAT IS WHY IT IS HERE.** The holdout
window has never been examined for completeness — examining it is examining it —
so **nothing is known about missing 1m bars in 2025–2026.** A rule that exists
only after the holdout is opened is a rule chosen with the holdout in view.

**THE CONVENTION IS DELIBERATELY DEFERRED.** If 5.3.4 reports the flagged
fraction as material — which in-sample it cannot be, so this means the holdout —
**the convention is reconsidered THEN, as an amendment with its own commit**,
rather than chosen now against an unknown frequency. If it is negligible, **the
flag is the whole treatment.**

---

## 9. E9 — WHAT REMAINS RESOLVED BY CONVENTION EVEN AT 1m

**Moving to 1m shrinks the convention-dependent fraction. IT DOES NOT REMOVE
IT.** What follows is still convention rather than evidence:

| # | what | why it is still convention |
|---|---|---|
| 1 | **intrabar precedence within a 1m bar** (E4) | when both conditions hold in one minute, no 1m data can say which came first. Counted, not resolved. |
| 2 | **the fill price on a gapped stop** | `open` is **synthesised** from the carried-forward previous close and is dropped by every loader (report 27 §8), so **no bar's first observed price exists at any resolution.** A bar that opens beyond the stop is invisible. |
| 3 | **the stop haircut** (E2) | it **is** the gap model in (2), and it has never been measured — §3.1. |
| 4 | **queue position on the maker target** (E3) | a trade-through says the market reached us, not that we were reached first — §4.2. |
| 5 | **the funding rate** (E7) | 0.01%/8h is an assumption; 90 days of history against a three-year window. |
| 6 | **missing-bar treatment** (E8) | deferred until 5.3.4 measures the frequency; zero in-sample, unknown out of sample. |

**ITEMS 2 AND 3 ARE THE SAME HOLE SEEN TWICE**, and together they are the
largest remaining unknown in the exit model: **there is no observed opening
price at any resolution, and the single constant that stands in for it is a
placeholder.** Finer data does not fix this. **Only a measurement of realised
stop fills can**, and that requires either Point 6's paper trading or a data
source this project does not have.

---

## 10. THE CONSTANTS

Transcribed into `src/risk/exit_spec.py`. A test parses this block and requires
equality with the module.

```
EXIT_RESOLUTION             = "1m"
STOP_FILL_RULE              = "touch_inclusive"
TARGET_FILL_RULE            = "trade_through_one_tick"
INTRABAR_PRECEDENCE         = "stop_first"
TIME_EXIT_VS_STOP           = "stop_first"
FUNDING_CHARGED             = "in_sizing_denominator_at_entry"
FUNDING_SETTLEMENTS_CHARGED = 3
FUNDING_RATE_PER_SETTLEMENT = 0.0001
MISSING_BAR_RULE            = "flag_and_count"
TRIGGER_PRICE_BASIS         = "fill_price"
TRIGGER_PRICE_PARAMETER     = "triggerType"
```

**`FUNDING_SETTLEMENTS_CHARGED` IS THE VALUE §6's ENUMERATION PRODUCES**, not a
literal typed by hand: a test re-derives the count over all 24 entry hours from
the frozen time-exit definition and asserts the constant equals the maximum.

---

## 11. PRE-REGISTRATION STATEMENT

**THIS SPECIFICATION IS COMMITTED BEFORE ANY ENGINE CAPABLE OF EVALUATING AN
EXIT EXISTS.**

**NO WIN RATE, EXPECTANCY, PROFIT FACTOR, SHARPE, SORTINO, EQUITY CURVE,
DRAWDOWN, `r_multiple`, `net_pnl` OR `gross_pnl` FIGURE EXISTS ANYWHERE IN THIS
REPOSITORY AT THIS COMMIT.** Not for this hypothesis and not for any other.
`src/engine/simulate.py` can compute such quantities and **has not been run on
this thesis**; nothing in Points 5.1, 5.2 or 5.3 has produced one, and every
measurement module carries an AST guard refusing the twelve names.

**NO BACKTEST WAS RUN TO WRITE THIS. NO EXIT WAS EVALUATED AGAINST ANY REAL BAR.
NO 1m BAR WAS READ** — the 1m seal gap is open and this step does not touch the
1m loader.

**THE STATE OF THE REPOSITORY AT THE TIME OF WRITING:**

| artifact | commit |
|---|---|
| thesis / amendment 1 | `02e47a5` / `703046a` |
| report 24 — exposure | `4e08e1b` |
| report 25 — venue constraints | `e735295` |
| report 26 — budget cost | `ef1f4f6` |
| report 27 — intrabar span | `60b66f5` |
| report 28 — sizing | `df14a68` |
| documents 05 / 05a / 05b | `a323237` / `62c2d2b` / `46099a2` |

**WHAT WOULD FALSIFY THE CLAIM.** A commit at or before this one containing an
outcome figure for this thesis. **There is none, and `git log` is the check.**

**THE CONVENTIONS WERE NOT CHOSEN WITH REFERENCE TO THEIR EFFECT ON OUTCOMES**,
because no such effect is computable at this commit. Where a choice had a
direction — E3's conservatism, E7's overcharge on fast exits — **the direction is
stated in the section that makes the choice**, in advance.

---

## 12. THIS DOCUMENT MAY NOT BE EDITED IN LIGHT OF 5.3.4's RESULTS

**On the terms document 05 §11 sets for itself:** an amendment is a **new
document with a new commit and an explicit statement of what changed and why; a
silent edit is a contamination event.**

**If 5.3.4 reports that E4's precedence fired more often than expected, or that
the target-fill rate is low, THAT IS A FINDING ABOUT THE STRATEGY AND THE
CONVENTIONS TOGETHER — NOT GROUNDS FOR CHANGING A CONVENTION.** Changing E3 to
fill-on-touch after seeing a low target-fill rate would be selecting a fill rule
to raise a win rate, which is the precise failure this document exists to
prevent. §4.1 states E3's direction in advance for exactly that reason.

### 12.1 THE ESCALATION CLAUSE, carried from document 05b §4.5

> **IF THIS SPECIFICATION NEEDS MORE THAN ONE AMENDMENT, THE CORRECT CONCLUSION
> IS THAT IT WAS WRITTEN AT THE WRONG GRANULARITY — NOT THAT A SECOND PATCH
> SHOULD BE WRITTEN.**

The response would then be to re-specify **in one piece**, at the granularity of
the exit-evaluation loop — a full statement of what happens as each 1m bar is
examined, in order, once — as a **new pre-registration with its own commit**,
superseding this chain, rather than accumulating patches onto a document whose
§3–§8 is by then several documents long.

**Recorded now, before the second amendment**, so the decision is a
pre-commitment rather than a judgement made under the pressure of wanting to get
on with 5.3.4. Document 05b §4.5 set this rule after the third gap in the budget
specification; this document inherits it from the start.

---

**Committed with `src/risk/exit_spec.py`, `tests/test_exit_spec.py`,
`src/venue/trigger_basis.py` and the raw venue snapshot. No engine file, no
backtest, no bar at any resolution. The commit hash is the proof that these
conventions preceded any engine that could report what they do.**
