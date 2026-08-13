"""The exit resolution specification. PRE-REGISTERED CONSTANTS, NOTHING ELSE.

THE SPECIFICATION IS `docs/design/06_exit_resolution_spec.md`, frozen in the
same commit as this file. This module transcribes its canonical block and adds
nothing: no fill logic, no comparison against any bar, no simulation, no data
access. A test parses the document and requires every value here to equal the
value stated there, so a transcription drift fails rather than surviving.

WHY THIS IS COMMITTED BEFORE THE ENGINE. Report 27 measured that up to 10.21% of
trades could carry both their stop and their target inside one 1h bar, against a
2.0% criterion, and returned the verdict that exits are evaluated on 1m. EVERY
CONVENTION BELOW DECIDES TRADE OUTCOMES. If any were chosen while an engine
capable of reporting outcomes existed, it would be chosen -- knowingly or not --
for its effect on those outcomes.

AND THIS IS A BLINDER COMMITMENT THAN THE BUDGET WAS. Document 05's rules could
be adjudicated by COUNTING: report 26 measured the skip rate, the rotation's
neutrality and Rule C's gain without touching an outcome. THESE CONVENTIONS
CANNOT BE ADJUDICATED THAT WAY -- their effect is on win rate, which is
firewalled until the validation design is pre-registered. Section 1 of the
document says so at length; it is not equal footing and it is not presented as
such.

NO BACKTEST, NO BAR, NO 1m ACCESS. The 1m holdout seal gap is 5.3.3's work and
is NOT closed, so this step must not touch the 1m loader at all. This module
imports nothing -- asserted by test -- so it could not reach a bar if it tried.

NOTHING IS WIRED IN. No engine file imports this package. 5.3.4 does the wiring.
"""

# ---------------------------------------------------------------------------
# THE CANONICAL VALUES. Transcribed from section 10 of the design document.
# ---------------------------------------------------------------------------

EXIT_RESOLUTION = "1m"
"""E1. Stops, targets and time exits are evaluated on 1m bars. Signals,
indicators and entries remain on 1h and are unchanged.

Report 27's verdict: the per-trade upper bound on trades whose stop and target
could both sit inside one 1h bar is 10.21%, against a 2.0% criterion. That
figure is an UPPER BOUND ON AN UPPER BOUND (report 27 section 7) and the verdict
does not depend on how loose it is -- the margin is 5.1x."""

STOP_FILL_RULE = "touch_inclusive"
"""E2. The stop is a conditional MARKET order: a TOUCH fills it.

    long   low  <= stop      short   high >= stop        INCLUSIVE

Fill price is the stop price adjusted by the pre-registered stop haircut --
5 bps BTC/ETH, 10 bps SOL. THAT HAIRCUT IS AN UNMEASURED PLACEHOLDER and it IS
the entire slippage-and-gap model; report 28 section 9 measured that on SOLUSDT
it is the whole reason that symbol breaches the cost tolerance."""

TARGET_FILL_RULE = "trade_through_one_tick"
"""E3. The target is a resting MAKER LIMIT order: a TRADE-THROUGH fills it.

    long   high >= target + tick     short   low <= target - tick

A resting order does not fill because price touched it; it fills because price
traded through it. ONE TICK because the tick is the smallest price increment
that exists, so it is the only trade-through margin that is not an arbitrary
choice -- any other would be a tunable parameter entering a pre-registration.

THE TICK IS RESOLVED PER TIMESTAMP, NOT PER SYMBOL. SOLUSDT's tick changed on
2024-08-14 (report 28 section 10).

STRICTLY MORE CONSERVATIVE THAN TOUCH, ON THE LEG THAT PRODUCES EVERY WINNER.
It will report fewer target fills than a touch rule would. Stated in advance."""

INTRABAR_PRECEDENCE = "stop_first"
"""E4. When one 1m bar satisfies BOTH fill conditions, the STOP is taken.

The pessimistic convention. At 1m the geometry makes this far rarer than report
27's 1h figure, but "far rarer" is not "specified", and an unspecified case is
decided by whichever comparison the implementer wrote first. EVERY TRADE
RESOLVED THIS WAY IS FLAGGED AND COUNTED, so 5.3.4 can state how often the
convention decided an outcome instead of assuming it was negligible."""

TIME_EXIT_VS_STOP = "stop_first"
"""E5. On the bar carrying the max-hold exit, the stop is evaluated across the
WHOLE bar and the time exit only at its CLOSE.

The stop is a resting conditional order that fires the instant price touches it;
the time exit is an action taken at a bar close. This is not a preference, it is
what the two order types are."""

FUNDING_CHARGED = "in_sizing_denominator_at_entry"
"""E7. Funding is charged at ENTRY, inside the per-unit risk denominator, at the
MAXIMUM number of settlements the position could cross.

THE GROUND: the standing risk rule is "never more than 1%, enforced after fees
and estimated slippage". Funding is a cost of holding. A trade whose geometric
loss is exactly the risk unit AND which also paid funding has breached the rule.
Charging at entry keeps the worst-case stop-out at or below 1.0R, which is what
the rule requires and what report 28's identity asserts.

THE COST, STATED: every position that exits before its maximum hold has been
charged for settlements it never crossed -- a systematic overcharge concentrated
on FAST EXITS, which are disproportionately stop-outs."""

FUNDING_SETTLEMENTS_CHARGED = 3
"""E7. DERIVED FROM THE FROZEN TIME-EXIT RULE, NOT ASSUMED.

Enumerated over all 24 entry hours in section 5 of the document: a position
crosses TWO settlements on 21 of the 24, and THREE on the 3 hours where the
entry instant coincides with a settlement. THE MAXIMUM IS 3 and that is what is
charged.

IT MATCHES THESIS SECTION 5.3's n = 3 NUMERICALLY BUT NOT IN MEANING. The thesis
derived 3 as the count of settlements crossed by a typical position; the
enumeration shows the typical count is 2 and 3 is the boundary case. The
consequence for the frozen 0.022R figure is recorded in the document and routed
to the validation design, NOT repaired here."""

FUNDING_RATE_PER_SETTLEMENT = 0.0001
"""E7. Thesis section 5.3's stated assumption: 0.01% per 8h settlement.

AN ASSUMPTION, NOT A MEASUREMENT, in the same terms section 5.3 uses: Bitget
funding history available to this project covers roughly 90 days against a
three-year window, so the rate cannot be verified over the period being tested.

FUNDING IS DIRECTIONAL IN REALITY -- longs pay shorts or the reverse, depending
on the sign -- while this model charges it as an UNSIGNED COST TO BOTH SIDES.
That is the conservative treatment and it is stated as such."""

MISSING_BAR_RULE = "flag_and_count"
"""E8. A position whose open interval contains missing 1m bars is FLAGGED with
the count. It is resolved on the bars that exist. The flagged fraction is
reported by 5.3.4.

WHY FLAGGING RATHER THAN A FILL CONVENTION: a missing bar is not a price gap. A
gap is something the market did; a hole is something the data does not know. Any
fill convention over an absent minute records an event that may not have
happened, at a price nobody observed, and does so INVISIBLY.

THE CONVENTION IS DELIBERATELY DEFERRED. If 5.3.4 reports the flagged fraction
as material it is reconsidered THEN, as an amendment with its own commit, rather
than chosen now against an unknown frequency."""

TRIGGER_PRICE_BASIS = "fill_price"
"""R. RETRIEVED. Bitget's conditional-order trigger basis is a per-order
parameter, `triggerType`, taking `fill_price` (fill / LAST price) or
`market_price` (mark price). On the stop-profit / stop-loss endpoint it is
OPTIONAL and its documented default is `fill_price`.

THIS PROJECT'S OHLCV IS LAST PRICE, so the specification and the venue agree by
default -- and the operator must nonetheless set the parameter EXPLICITLY rather
than rely on a default, which is this project's own Point 3R lesson about
parameters nobody chose.

Retrieved from Bitget's static v1 documentation mirror and snapshotted with its
SHA-256; the v2 pages are JS-rendered and returned no endpoint content, so the
v2 default is not independently corroborated. Section 6 of the document states
both boundaries."""

TRIGGER_PRICE_PARAMETER = "triggerType"
"""The venue's own name for it, so the operator checklist names the right field."""
