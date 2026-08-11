"""The aggregate open risk budget. PRE-REGISTERED CONSTANTS, NOTHING ELSE.

THE SPECIFICATION IS `docs/design/05_aggregate_risk_budget.md`, frozen in the
same commit as this file. This module transcribes its canonical block and adds
nothing: no allocation function, no viability check, no simulation, no data
access, no engine import. A test parses the document and requires every value
here to equal the value stated there, so a transcription drift fails rather than
surviving as a discrepancy.

THE RULE, IN ONE LINE. Aggregate open nominal risk across the whole book -- all
three symbols combined, not per symbol -- may not exceed 120.00 USDT, being 6.0%
of 2000.00 USDT of capital. Because the budget is an exact multiple of the risk
unit, that is a HARD CAP OF SIX CONCURRENT FULL-SIZE POSITIONS WITH
ARRIVAL-ORDER SKIP; the partial-allocation branch is specified in section 4 of
the document and is unreachable at these values.

THIS IS A JUDGEMENT, NOT A DERIVATION. Section 2 of the document states it in
full: a stated 30-50% tolerance for peak-to-trough decline, of which a single
maximally correlated adverse event may consume at most one fifth of the
conservative end. NO DERIVATION FROM ALREADY-FROZEN QUANTITIES PRODUCES THIS
NUMBER -- COST_TOLERANCE_R, the 1.50% stop floor, n = 3 settlements and the
1:1.5 reward-to-risk are all per-trade quantities and none of them constrains
book-level exposure. The number is a preference with an argued rationale and the
document says so at length rather than dressing it as arithmetic.

WHY THIS IS COMMITTED BEFORE THE MEASUREMENT. Report 25 established that the
venue imposes no relevant limit, so the level is a risk-appetite choice; a
choice made after seeing what it discards would be fitted to preserve
statistical power. The cost of the rule is measured in the NEXT step and nothing
here anticipates it: no skip rate, no surviving count, no concurrency figure.

NO MEASUREMENT AND NO WIRING. This module imports nothing at all -- not the data
layer, not the engine, not pandas -- and a test asserts the import list is
empty. No engine file imports it either; that is 5.3's work.
"""

# ---------------------------------------------------------------------------
# THE CANONICAL VALUES. Transcribed from section 1 of the design document.
# ---------------------------------------------------------------------------

MAX_AGGREGATE_OPEN_RISK_USD = 120.00
"""Maximum aggregate open nominal risk across the WHOLE BOOK, in USDT.

ACROSS THE BOOK, NOT PER SYMBOL. There is no per-symbol sub-budget and none is
implied: a per-symbol cap would permit three simultaneous one-symbol maxima and
would be a weaker constraint wearing a stricter name.
"""

RISK_PER_TRADE_USD = 20.00
"""Nominal risk per open position, in USDT. The project's standing risk unit.

Amendment 1 section 3 establishes that the engine sizes cost-inclusively so a
stop-out returns exactly -1.0R -- exactly this figure -- up to one tick of
rounding, always away from the position. Restated here rather than imported so
this module has no dependency; a test asserts the two agree.
"""

ACCOUNT_CAPITAL_USD = 2000.00
"""Account capital the budget is a fraction of, in USDT."""

MARGIN_MODE = "cross"
"""Section 8.1. Under isolated margin, at the leverage this book requires, the
liquidation price can sit INSIDE the stop on wide-stop trades -- and a stop that
cannot be reached is not a stop. The cost of cross is the loss of the
per-position firebreak, which is stated in the document rather than left
implicit.
"""

POSITION_MODE = "hedge"
"""Section 8.2. The strategy fires both directions on every symbol; under
one-way mode an opposite-direction signal would OFFSET an open position rather
than open a trade. Hedge mode does not restore parallel positions -- same-side
entries still net -- and it is an account-level setting per product type that
cannot be switched with any open position or pending order.
"""

# ---------------------------------------------------------------------------
# AMENDMENT 1. Transcribed from section 5 of
# docs/design/05a_aggregate_risk_budget_amendment_1.md. The LEVEL above is
# unchanged by it; these fill two specification gaps in the frozen document's
# section 3 and add nothing to its section 2.
# ---------------------------------------------------------------------------

TIE_BREAK_RULE = "cyclic_rotation_by_bar_timestamp"
"""RULE A. When two or more signals arrive on the SAME BAR they are allocated in
a priority order that rotates cyclically by bar:

    rotation = (bar_open_epoch_ms // ROTATION_PERIOD_MS) mod ROTATION_MODULUS

ACROSS BARS, ARRIVAL ORDER IS UNCHANGED -- an earlier bar's signals are always
allocated before a later bar's. Rotation orders only WITHIN a bar, and a bar
yields at most one signal per symbol (two-sided bars are skipped by thesis 4.1),
so the rotation is a total order on the tied set.
"""

ROTATION_PERIOD_MS = 3_600_000
"""One 1h bar, in milliseconds. THE BAR PERIOD, NOT A FREE PARAMETER: the
timeframe is frozen at 1h by the rule at 96c96cf. If the timeframe changed this
would change with it and the rotation would still advance once per bar."""

ROTATION_MODULUS = 3
"""Three symbols, three cyclic rotations. Coprime with the 8-hour funding
interval, so the joint cycle is 24 hours and every rotation meets every
settlement phase equally often."""

SYMBOL_ROTATION = (
    ("BTCUSDT", "ETHUSDT", "SOLUSDT"),
    ("ETHUSDT", "SOLUSDT", "BTCUSDT"),
    ("SOLUSDT", "BTCUSDT", "ETHUSDT"),
)
"""Priority order per rotation value: SYMBOL_ROTATION[r], highest priority first.

CYCLIC ROTATIONS, NOT ARBITRARY PERMUTATIONS. Read down any column and each
symbol appears exactly once, so each holds each of the three priority RANKS on
exactly one bar in three -- neutrality across all three ranks, not merely across
first place. A scheme that rotated first place while leaving third fixed would
be biased on the rank that decides who loses the last free slot.

DERIVED FROM THE TIMESTAMP, NOT FROM A BAR INDEX. An index depends on where the
series starts, and pooled and fold-scoped runs trim different warm-ups, so the
same UTC bar would draw different priorities in different scopes. The timestamp
is a property of the bar; the index is a property of the slice.
"""

BUDGET_CHARGES = "nominal"
"""RULE B. The budget is charged RISK_PER_TRADE_USD BEFORE qty_step flooring,
and a closing position returns that same nominal figure. Realised risk after
flooring does NOT enter budget accounting.

WHY IT MATTERS: under realised-risk charging, six open positions would leave the
sum of six flooring shortfalls as remaining budget, a seventh signal would be
allocated that remainder, and the partial-allocation branch the frozen document
declares INERT would become reachable -- silently, and invisibly to any test
written at these values. The error runs conservative: charged exposure slightly
exceeds true exposure, by under 1.3% of the budget on report 24's measurement.

5.3 MUST WIRE THE BUDGET TO THIS FIGURE. Wiring it to realised risk would be a
silent rule change; this constant is what makes that a detectable error rather
than a defensible reading.
"""

# ---------------------------------------------------------------------------
# AMENDMENT 2. Transcribed from section 7 of
# docs/design/05b_aggregate_risk_budget_amendment_2.md. The LEVEL is unchanged
# by it, and so is every value above.
# ---------------------------------------------------------------------------

INTRA_BAR_ORDER = "exits_before_entries"
"""RULE C. Within a single bar close, ALL positions whose exit falls at this
bar's close are closed first -- each returning RISK_PER_TRADE_USD -- and only
then are that bar's signals evaluated against the remaining budget, in the
priority order Rule A gives for that bar. Across bars nothing changes.

THE SAME UNIT CAN FUND A CLOSING AND AN OPENING POSITION AT ONE BAR CLOSE, AND
THAT IS CORRECT RATHER THAN DOUBLE COUNTING. Under report 24 section 5.3's
half-open convention the closing position's last open bar is X and the opening
position's first is X+1, so the two never overlap and no bar of the occupancy
timeline carries both.

DO NOT "FIX" THIS BY EVALUATING ENTRIES FIRST. That models a sequence which
cannot occur live -- the exit order fills and releases before the entry order is
placed -- and it is strictly MORE RESTRICTIVE, so it would skip signals the live
account would have taken and inflate the measured skip rate by an artefact of
loop order. A test pins both orderings and requires them to disagree.
"""

# ---------------------------------------------------------------------------
# DERIVED. Computed, never typed twice.
# ---------------------------------------------------------------------------

BUDGET_FRACTION_OF_CAPITAL = MAX_AGGREGATE_OPEN_RISK_USD / ACCOUNT_CAPITAL_USD
"""0.06. The budget as a fraction of capital -- 6.0%."""

FULL_SIZE_POSITIONS = round(MAX_AGGREGATE_OPEN_RISK_USD / RISK_PER_TRADE_USD)
"""6. Concurrent full-size positions the budget funds.

`round`, not `int`, so a float-representation residue cannot truncate a whole
position downward. The exactness is checked below rather than assumed: if the
ratio ever stops being integral, the partial-allocation branch of section 3
becomes reachable and section 4's "hard cap of six" description silently stops
being true.
"""


def _refuse_inexact_transcription():
    """Refuse to import on a value the document's arithmetic does not support.

    THE FAILURE THIS CATCHES. Editing one constant without the other leaves a
    module that still imports, still exports plausible numbers, and no longer
    describes the frozen rule. The document is the specification and these are
    the only two relations it asserts about these values, so they are checked
    where they cannot be skipped.
    """
    if ACCOUNT_CAPITAL_USD <= 0.0 or RISK_PER_TRADE_USD <= 0.0:
        raise ValueError("capital and risk per trade must be positive")

    # RECOMPUTED from the primitives, not read back from the derived names, so
    # a hand-edited derived constant is caught as well as a hand-edited
    # primitive one.
    fraction = MAX_AGGREGATE_OPEN_RISK_USD / ACCOUNT_CAPITAL_USD
    if abs(fraction - 0.06) > 1e-12:
        raise ValueError(
            "the budget is %r of capital, not the frozen 0.06; the document at "
            "docs/design/05_aggregate_risk_budget.md states 6.0%% and an "
            "amendment is a new document, not an edit" % (fraction,))
    if abs(fraction - BUDGET_FRACTION_OF_CAPITAL) > 1e-12:
        raise ValueError(
            "a derived constant disagrees with the primitives it is derived "
            "from: %r against %r" % (BUDGET_FRACTION_OF_CAPITAL, fraction))

    ratio = MAX_AGGREGATE_OPEN_RISK_USD / RISK_PER_TRADE_USD
    if abs(ratio - round(ratio)) > 1e-12:
        raise ValueError(
            "the budget funds %r positions, which is not an integer; the "
            "partial-allocation branch of section 3 is then REACHABLE and "
            "section 4's 'hard cap of six full-size positions' no longer "
            "describes the rule" % (ratio,))
    if round(ratio) != FULL_SIZE_POSITIONS:
        raise ValueError(
            "a derived constant disagrees with the primitives it is derived "
            "from: %r positions against %r" % (FULL_SIZE_POSITIONS, ratio))

    # AMENDMENT 1. The rotation table's neutrality is the whole content of
    # Rule A, and a malformed table would still index, still return three
    # symbols, and would silently favour one of them.
    if len(SYMBOL_ROTATION) != ROTATION_MODULUS:
        raise ValueError(
            "the rotation table has %d entries against a modulus of %d; every "
            "rotation value must index exactly one ordering"
            % (len(SYMBOL_ROTATION), ROTATION_MODULUS))
    for rank in range(ROTATION_MODULUS):
        at_rank = [order[rank] for order in SYMBOL_ROTATION]
        if len(set(at_rank)) != ROTATION_MODULUS:
            raise ValueError(
                "the rotation table is NOT neutral at priority rank %d: %r. "
                "Each symbol must hold each rank exactly once, not merely hold "
                "first place once" % (rank, at_rank))


_refuse_inexact_transcription()
