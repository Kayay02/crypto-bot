"""The cost envelope: the minimum stop width a pre-committed cost budget allows.

WHAT THIS MODULE IS FOR. Point 4's hypothesis is closed. Before an indicator or
a thesis is chosen for the next one, this module fixes the line every candidate
will be priced against: given a budget for what round-trip costs may consume,
what is the narrowest stop that stays inside it? A candidate whose natural stop
sits below that line is not a candidate, and knowing this before the thesis is
chosen is what stops the line being negotiated afterwards.

THE ARITHMETIC, AND THE ONE THING IT MAKES LEGIBLE
==================================================

    f_eff     = maker_frac * f_maker + (1 - maker_frac) * f_taker
    notional  = R$ / s
    cost_in_R = [ 2*f_eff
                + 2*(1 - maker_frac)*slip
                + 2*maker_frac*MAKER_NONFILL_SLIP ] / s
    leverage  = notional / equity

EVERY COST TERM IS A PRICE FRACTION AND THE DIVISION BY `s` HAPPENS ONCE. Fees,
slippage and the maker chase distance are all distances between a price you
wanted and a price you got; dividing their sum by the stop width converts the
lot into R in one step. Nothing is added to that result afterwards.

`s` is stop distance as a fraction of entry price. The factor of 2 is the round
trip: entry and exit are each charged a fee.

ONLY TAKER LEGS PAY SLIPPAGE. This is the correction made in report 17's second
pass. A leg filled as maker rested at its own price and got that price -- it
does not pay slippage by construction. Charging slippage on both legs
regardless of `maker_frac`, as the first pass did, overstated maker execution
and made the slippage sensitivity of `s*` look identical at every maker
fraction. It is not: the sensitivity now shrinks as `maker_frac` rises and is
exactly zero at maker_frac = 1.0.

THE FLAT ALL-MAKER COLUMN IS OPTIMISTIC, AND DELIBERATELY SO. At
maker_frac = 1.0 the slippage term vanishes and `s*` is flat at
2*f_maker/tolerance. That is mechanically right and economically incomplete --
see MAKER_NONFILL_SLIP below, which is the term that would fill the gap and is
not measured.

EQUITY CANCELS. Under fixed-dollar risk the position is sized as notional = R$/s,
so every dollar cost above carries a factor R$/s and dividing by R$ to express
it in R removes R$ as well as equity. Cost as a fraction of R depends ONLY on stop
width, fee rate and slippage. It does not depend on account size, and it does
not depend on how large the fixed risk is. A $2,000 account and a $200,000
account running the same stop pay the same fraction of R in costs.

This is the finding the module exists to make unmissable, so `cost_in_r` does
not accept an equity argument at all -- the signature refuses the mistake rather
than documenting it. Capital enters only through `implied_leverage` (can the
position be held at all) and through lot granularity (can it be expressed in
whole contract steps). Those are the only two channels, and both are checked in
report 17.

THE FIREWALL IS RE-ARMED. Nothing here computes, reads or estimates a
performance quantity. `COST_TOLERANCE_R` is built from a dispersion figure and a
minimum-detectable-effect figure -- both permitted -- and no expectancy, win
rate, profit factor or r_multiple aggregate appears anywhere in this package.

NO FEE CONSTANT LIVES HERE. Every rate comes from data/reference/bitget_fees.json
via `load_fees`. There is no default, no fallback and no module-level fee
literal. A missing or malformed artifact raises. Deriving an admissibility line
against a fee rate nobody can date is the failure this design exists to prevent.

UNITS. Rates, `s` and `slip` are decimal fractions everywhere inside this
module: a rate of 0.001 means one tenth of one percent. Percentages are a
presentation concern and appear only where a column header names them. No
example here uses a real Bitget rate -- a test greps this file for one, because
a literal that happens to agree with the artifact is exactly the constant that
would make the artifact decorative.
"""

import json
import math
import os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FEES_PATH = os.path.join(ROOT, "data", "reference", "bitget_fees.json")

REQUIRED_FIELDS = (
    "maker_rate",
    "taker_rate",
    "tier",
    "product",
    "source_url",
    "retrieved_at",
    "retrieval_method",
    "notes",
)

# ---------------------------------------------------------------------------
# The account's fixed terms. Both are stated in the project brief and neither
# is a choice made here. RISK_DOLLARS and EQUITY appear in `implied_leverage`
# and nowhere in the cost arithmetic -- see the equity-cancellation note above.
# ---------------------------------------------------------------------------
RISK_DOLLARS = 20.0
EQUITY = 2000.0

COST_TOLERANCE_R = 0.11
"""The pre-committed cost budget, in units of R. PRE-REGISTERED -- DO NOT TUNE.

DERIVATION. Per-trade dispersion was measured at sigma = 0.72-0.85R (report 12,
the E6 step). At the trade counts this fold architecture produces, the minimum
detectable edge is approximately 0.34R. An edge that costs consume a large
share of is an edge the architecture cannot resolve from noise, so costs are
permitted no more than ONE THIRD of that minimum detectable effect:

    0.34 / 3 = 0.1133...  ->  0.11

ONE THIRD is the judgement in this number, and it is the only one. It is not
derived from anything; it is a stated tolerance for how much of the smallest
edge we could detect we are willing to spend on getting in and out.

WHEN IT WAS FIXED. Before the fee rates were retrieved and before any surface
was inspected. It is a budget, not a fitted quantity: had it been chosen after
seeing the admissibility table it would encode the answer it is supposed to
test. It is not modified in this step, and a later step that wants a different
budget must say so as an amendment with its own reasoning, not edit this line.
"""

MAKER_NONFILL_SLIP = 0.0
"""Chase distance for ONE maker leg that fails to fill, AS A FRACTION OF PRICE.
UNMODELLED. A placeholder, NOT a measurement.

WHAT IT STANDS FOR. A resting limit order fails to fill precisely when price is
moving away from the rest. The leg then has to be chased at a worse price, or
the trade is missed. That is adverse selection, and it is correlated with
exactly the conditions in which the entry mattered -- it is not a symmetric
noise term that averages out.

UNITS: A PRICE FRACTION, AND THE NAME SAYS SO. Dimensionally identical to
`slip`, and for the same reason: both are a distance between the price you
wanted and the price you got. It therefore sits in the `price_cost_rate`
numerator alongside `slip` and is divided by `s` exactly once, with everything
else.

WHY NOT R. It was originally named MAKER_NONFILL_COST_R and placed outside the
division, which is a consistent R denomination -- but the wrong one. Chasing a
leg twenty basis points is the same twenty basis points whether the stop behind
it is 0.5% or 5%. Denominating the chase in R asserts the opposite: it would
make an identical chase cost a FIXED FRACTION OF RISK, so a strategy could
shrink the cost of its own missed fills by widening its stop. That inverts the
causality -- the stop does not reach back and change what the order book did.
Under the correct denomination a wider stop does reduce the chase's cost in R,
but as a consequence of dividing a fixed price distance by a larger `s`, which
is exactly how `slip` and the fees already behave.

The two placements differ by a factor of 1/s -- 20x at s = 5% to 200x at
s = 0.5% -- so this is not a presentational choice. At the current value of
zero they are numerically indistinguishable, which is precisely why the
placement is pinned by a unit-consistency test and a planted mutation rather
than by a comment.

SETTING IT TO ZERO IS A KNOWN UNDERSTATEMENT OF MAKER-EXECUTION COST. It is
zero here because no measurement of it exists, and inventing a number would be
worse than carrying an explicit hole. The consequence, stated so it cannot be
read past:

    THE FLAT ALL-MAKER COLUMN OF REPORT 17'S ADMISSIBILITY TABLE IS OPTIMISTIC,
    AND SO IS THE ENTIRE `UNCON` COLUMN OF ITS BREAK-EVEN TABLE. NEITHER MAY BE
    DESIGNED AROUND.

At maker_frac = 1.0 the model says execution is free of everything except two
maker fees, and the whole true cost of all-maker execution sits in this term,
which is zero. Any conclusion of the form "just use maker execution" is reading
a number the model does not have.

WHY IT IS IN THE EXPRESSION RATHER THAN THE PROSE. `price_cost_rate` carries it
structurally, so no cost figure can be produced without the term being present
in the computation that produced it. Set it non-zero and every table in report
17 moves; a test asserts that propagation, so the term cannot rot into a
decorative constant that nothing reads.

SCALING. Per MAKER LEG. A round trip has 2*maker_frac maker legs, so the
contribution is 2*maker_frac*MAKER_NONFILL_SLIP and it vanishes at
maker_frac = 0, where there are no maker legs to fail to fill. That the cost is
linear in the number of maker legs is unverified -- it is the least-wrong shape
for a term whose magnitude is unknown, not a finding.

DO NOT estimate a value for this in the cost-envelope step. It needs fill data.
"""

# ---------------------------------------------------------------------------
# The surface axes. `s` spans the stop widths this project can actually run:
# the derived floor sits near 1.0% and the cap at 3.5%, and the axis is
# extended either side so the admissible boundary is visible rather than
# clipped. `slip` spans zero to 10bps per side.
# ---------------------------------------------------------------------------
S_MIN, S_MAX, S_STEP = 0.005, 0.050, 0.0005
SLIP_MIN, SLIP_MAX, SLIP_STEP = 0.0000, 0.0010, 0.0001
MAKER_FRAC_AXIS = (0.0, 0.25, 0.50, 0.75, 1.0)


def _axis(lo, hi, step, decimals):
    """Inclusive float axis, rounded so the values are exact at the step.

    Accumulating `lo + i*step` leaves values like 0.030000000000000002, which
    then key dictionaries and print tables badly. Rounding at construction
    makes the axis exact and comparable.
    """
    n = int(round((hi - lo) / step))
    return tuple(round(lo + i * step, decimals) for i in range(n + 1))


S_AXIS = _axis(S_MIN, S_MAX, S_STEP, 6)
SLIP_AXIS = _axis(SLIP_MIN, SLIP_MAX, SLIP_STEP, 6)


class FeeArtifactError(Exception):
    """The fee artifact is absent, unreadable, or does not meet its contract."""


class Fees:
    """Base-tier maker and taker rates, as decimal fractions, with provenance.

    Constructed only by `load_fees` or by a test supplying explicit rates. There
    is no default constructor: a Fees object with no rates in it is the thing
    this module refuses to let exist.
    """

    __slots__ = ("maker_rate", "taker_rate", "tier", "product", "source_url",
                 "retrieved_at", "retrieval_method", "notes", "contract_specs")

    def __init__(self, maker_rate, taker_rate, tier, product, source_url,
                 retrieved_at, retrieval_method, notes, contract_specs=None):
        self.maker_rate = maker_rate
        self.taker_rate = taker_rate
        self.tier = tier
        self.product = product
        self.source_url = source_url
        self.retrieved_at = retrieved_at
        self.retrieval_method = retrieval_method
        self.notes = notes
        self.contract_specs = contract_specs or {}

    def __repr__(self):
        return ("Fees(maker_rate=%r, taker_rate=%r, tier=%r, retrieved_at=%r)"
                % (self.maker_rate, self.taker_rate, self.tier, self.retrieved_at))


def _validated_rate(value, field):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise FeeArtifactError(
            "fee artifact field %r must be a number, got %r (%s)"
            % (field, value, type(value).__name__)
        )
    v = float(value)
    if not math.isfinite(v):
        raise FeeArtifactError("fee artifact field %r is not finite: %r" % (field, v))
    if v <= 0.0:
        raise FeeArtifactError(
            "fee artifact field %r must be positive, got %r" % (field, v)
        )
    return v


def load_fees(path=FEES_PATH):
    """Read and validate the fee artifact. Raises FeeArtifactError, never defaults.

    Every failure mode here -- absent file, unparseable JSON, missing field,
    non-finite or non-positive rate -- is a refusal. There is deliberately no
    branch that produces a Fees object without having read one from disk.
    """
    if not os.path.exists(path):
        raise FeeArtifactError(
            "fee artifact not found at %s. Build it with "
            "`python src/costs/build_fee_artifact.py`. This module has no "
            "default fee rate and will not proceed without one." % path
        )
    try:
        with open(path) as fh:
            raw = json.load(fh)
    except json.JSONDecodeError as exc:
        raise FeeArtifactError("fee artifact at %s is not valid JSON: %s" % (path, exc))

    if not isinstance(raw, dict):
        raise FeeArtifactError(
            "fee artifact at %s must be a JSON object, got %s"
            % (path, type(raw).__name__)
        )

    missing = [f for f in REQUIRED_FIELDS if f not in raw]
    if missing:
        raise FeeArtifactError(
            "fee artifact at %s is missing required field(s): %s"
            % (path, ", ".join(missing))
        )

    maker = _validated_rate(raw["maker_rate"], "maker_rate")
    taker = _validated_rate(raw["taker_rate"], "taker_rate")
    if maker > taker:
        raise FeeArtifactError(
            "fee artifact has maker_rate %r > taker_rate %r. The envelope's "
            "monotonicity in maker_frac assumes maker <= taker; a schedule "
            "that inverts them needs the surface re-read, not a silent pass."
            % (maker, taker)
        )
    if raw["retrieval_method"] not in ("automated", "manual_operator_entry"):
        raise FeeArtifactError(
            "fee artifact retrieval_method must be 'automated' or "
            "'manual_operator_entry', got %r" % (raw["retrieval_method"],)
        )

    return Fees(
        maker_rate=maker,
        taker_rate=taker,
        tier=raw["tier"],
        product=raw["product"],
        source_url=raw["source_url"],
        retrieved_at=raw["retrieved_at"],
        retrieval_method=raw["retrieval_method"],
        notes=raw["notes"],
        contract_specs=raw.get("contract_specs"),
    )


def _check_maker_frac(maker_frac):
    if not math.isfinite(maker_frac) or not (0.0 <= maker_frac <= 1.0):
        raise ValueError("maker_frac must lie in [0, 1], got %r" % (maker_frac,))


def effective_fee_rate(maker_frac, fees):
    """Blended per-side fee rate, as a decimal fraction.

    `maker_frac` is the fraction of the TWO round-trip legs filled as maker. It
    is a fraction of legs, not a probability per leg: 0.5 means one of the two
    legs rests and one crosses, which for a stop-managed strategy is the
    realistic case -- a limit entry and a market exit.
    """
    _check_maker_frac(maker_frac)
    return maker_frac * fees.maker_rate + (1.0 - maker_frac) * fees.taker_rate


def _check_s_and_slip(s, slip):
    if not math.isfinite(s) or s <= 0.0:
        raise ValueError("stop fraction s must be positive and finite, got %r" % (s,))
    if not math.isfinite(slip) or slip < 0.0:
        raise ValueError("slip must be non-negative and finite, got %r" % (slip,))


def price_cost_rate(maker_frac, slip, fees):
    """Round-trip price-proportional cost, as a fraction of PRICE.

        2*f_eff + 2*(1 - maker_frac)*slip + 2*maker_frac*MAKER_NONFILL_SLIP

    Every term here is a price fraction, which is what makes it legitimate to
    divide the whole thing by `s` exactly once. Both legs pay a fee; the TAKER
    legs pay slippage; the MAKER legs pay a chase distance. Factored out so the
    forward function and both inverses share ONE expression -- separate copies
    would be separate places for a factor to be dropped, or for a term to drift
    to the wrong side of the division.
    """
    f_eff = effective_fee_rate(maker_frac, fees)
    return (2.0 * f_eff
            + 2.0 * (1.0 - maker_frac) * slip
            + 2.0 * maker_frac * MAKER_NONFILL_SLIP)


def nonfill_rate(maker_frac):
    """Contribution of the UNMODELLED maker non-fill term, as a PRICE FRACTION.

    2*maker_frac maker legs, each carrying MAKER_NONFILL_SLIP. Zero today,
    because the constant is zero. Read its docstring before using any all-maker
    figure this module produces.

    Named `nonfill_rate`, not `nonfill_cost_r`. The old name asserted R
    denomination and the old placement honoured it; both were wrong, and a name
    that keeps asserting the wrong unit is how the error would come back.
    """
    _check_maker_frac(maker_frac)
    return 2.0 * maker_frac * MAKER_NONFILL_SLIP


def cost_in_r(s, maker_frac, slip, fees):
    """Round-trip cost as a fraction of R.

    NO EQUITY ARGUMENT, BY DESIGN. Under fixed-dollar risk both equity and the
    risk amount cancel out of this quantity; accepting either would imply they
    move the answer. See the module docstring.

    TWO GUARDS ARE PLANTED AGAINST THIS EXPRESSION, both in
    `tests/test_costs_envelope.py`, because both mutations are silent:

      - dropping the factor of 2 halves every cost and doubles every admissible
        stop, and every RATIO in the output survives unchanged;
      - dropping (1 - maker_frac) from the slippage term restores the first
        pass's error, which is invisible at maker_frac = 0 -- the all-taker
        column is identical under both models -- and only shows up in columns
        the eye is least likely to check;
      - moving MAKER_NONFILL_SLIP outside the division by `s` re-denominates it
        from a price fraction into R, which is wrong by a factor of 1/s -- 20x
        to 200x across the s axis -- and is undetectable at its current value
        of zero.

    ONE DIVISION BY `s`, APPLIED ONCE, TO EVERYTHING. Every term in
    `price_cost_rate` is a price fraction; dividing their sum by `s` converts
    the lot into R in a single step. Nothing may be added to this result
    afterwards without being denominated in R first, and nothing currently is.
    """
    _check_s_and_slip(s, slip)
    return price_cost_rate(maker_frac, slip, fees) / s


def notional(s, risk_dollars=RISK_DOLLARS):
    """Position notional under fixed-dollar risk: R$ / s."""
    if not math.isfinite(s) or s <= 0.0:
        raise ValueError("stop fraction s must be positive and finite, got %r" % (s,))
    return risk_dollars / s


def implied_leverage(s, risk_dollars=RISK_DOLLARS, equity=EQUITY):
    """Notional divided by equity. THIS is where account size enters.

    Identity, asserted by test: implied_leverage(s) * s * equity == risk_dollars.
    """
    if not math.isfinite(equity) or equity <= 0.0:
        raise ValueError("equity must be positive and finite, got %r" % (equity,))
    return notional(s, risk_dollars) / equity


def _check_tolerance(tolerance_r):
    """Validate the budget.

    REPLACES `_net_tolerance`, which subtracted the non-fill term from the
    budget before solving. That was the R-denominated treatment's bookkeeping:
    a cost that did not scale with `s` had to be taken off the top because it
    could not appear inside a numerator that gets divided by `s`. Under
    price-fraction denomination the term sits in the numerator with the others
    and the budget is untouched, so the subtraction -- and the "consumes the
    entire budget" failure mode it needed -- both disappear.
    """
    if not math.isfinite(tolerance_r) or tolerance_r <= 0.0:
        raise ValueError(
            "tolerance_r must be positive and finite, got %r" % (tolerance_r,)
        )
    return tolerance_r


def min_admissible_stop(tolerance_r, maker_frac, slip, fees):
    """Narrowest stop whose round-trip cost stays within `tolerance_r`.

    Closed form, by solving cost_in_R = tolerance_r for s:

        s* = [ 2*f_eff
             + 2*(1 - maker_frac)*slip
             + 2*maker_frac*MAKER_NONFILL_SLIP ] / tolerance_r

    Any s >= s* is admissible; cost_in_r is strictly decreasing in s, so the
    admissible set is the half-line above s*. Solved rather than searched --
    a bisection here would introduce tolerance where none is needed and would
    hide that the relationship is exactly linear in the price-cost rate.

    THE SLIPPAGE SENSITIVITY OF s* IS NOT CONSTANT. It is 2*(1-maker_frac)/tol
    per unit of slip, so it shrinks as maker_frac rises and is exactly zero at
    maker_frac = 1.0. The first pass of this module reported it as identically
    2/tol at every maker fraction; that was an artifact of charging slippage on
    maker legs, not a property of the cost structure.
    """
    tol = _check_tolerance(tolerance_r)
    if not math.isfinite(slip) or slip < 0.0:
        raise ValueError("slip must be non-negative and finite, got %r" % (slip,))
    return price_cost_rate(maker_frac, slip, fees) / tol


#: Returned by `max_tolerable_slip` when no amount of slippage can breach the
#: budget, because the taker-leg slippage term has vanished at maker_frac = 1.0
#: and the fees alone already fit. Distinct from a large finite answer: it means
#: the constraint does not exist, not that it is generous.
SLIP_UNCONSTRAINED = math.inf


def max_tolerable_slip(s, maker_frac, tolerance_r, fees):
    """Largest per-side slippage a given stop can absorb. THE BREAK-EVEN INVERSE.

    Solving cost_in_R = tolerance_r for slip:

        slip_max = [ tolerance_r * s
                   - 2*f_eff
                   - 2*maker_frac*MAKER_NONFILL_SLIP ] / [ 2 * (1 - maker_frac) ]

    The fixed component is read back out of `price_cost_rate` at slip = 0
    rather than being rewritten here, so the non-fill term cannot be present in
    the forward function and quietly absent from its inverse.

    WHY THIS AND NOT A SENSITIVITY SWEEP. Sweeping `s*` across an assumed
    slippage interval measures the interval, not the strategy: pick a wider
    interval and the same procedure declares slippage more important. This
    direction has no assumed interval in it. It converts the slippage question
    into a single number per cell that a measurement can be compared against.

    THREE RETURN CASES, DELIBERATELY DISTINGUISHABLE:

      float >= 0          the break-even slippage, a decimal fraction per side.
      SLIP_UNCONSTRAINED  maker_frac == 1.0 and fees alone fit: there are no
                          taker legs, so no slippage is paid and the constraint
                          does not exist. `math.inf`, which poisons arithmetic
                          rather than passing as a plausible bound.
      None                the stop is INADMISSIBLE ON FEES ALONE. No slippage,
                          not even zero, brings it inside the budget.

    `None` rather than a negative float on the last case, on purpose. A
    negative break-even is arithmetically meaningful but is exactly the kind of
    value that gets formatted into a table, compared with `<`, or minimised
    over, and reads as a real bound while being a category error. `None` fails
    at the point of use.
    """
    tol = _check_tolerance(tolerance_r)
    if not math.isfinite(s) or s <= 0.0:
        raise ValueError("stop fraction s must be positive and finite, got %r" % (s,))
    _check_maker_frac(maker_frac)

    # Everything that does not depend on slip, taken from the one expression
    # that defines the model rather than restated here.
    fixed_component = price_cost_rate(maker_frac, 0.0, fees)
    budget = tol * s - fixed_component

    if maker_frac == 1.0:
        # No taker legs: slip has no coefficient to divide by.
        return SLIP_UNCONSTRAINED if budget >= 0.0 else None
    if budget < 0.0:
        return None
    return budget / (2.0 * (1.0 - maker_frac))


def envelope_surface(fees, s_axis=S_AXIS, maker_fracs=MAKER_FRAC_AXIS,
                     slips=SLIP_AXIS, tolerance_r=COST_TOLERANCE_R,
                     risk_dollars=RISK_DOLLARS, equity=EQUITY):
    """The full (s x maker_frac x slip) surface as a list of row dicts.

    One row per grid cell. `admissible` is the verdict against `tolerance_r`,
    and `min_stop` repeats the closed-form boundary for the row's
    (maker_frac, slip) so a row can be read without recomputing it.

    Returned as plain dicts rather than a DataFrame: this is a few thousand
    rows of closed-form arithmetic with no data-layer dependency, and keeping
    it dependency-free is part of the point of the package.
    """
    rows = []
    for mf in maker_fracs:
        f_eff = effective_fee_rate(mf, fees)
        for sl in slips:
            s_star = min_admissible_stop(tolerance_r, mf, sl, fees)
            for s in s_axis:
                c = cost_in_r(s, mf, sl, fees)
                rows.append({
                    "s": s,
                    "maker_frac": mf,
                    "slip": sl,
                    "f_eff": f_eff,
                    "cost_in_r": c,
                    "min_stop": s_star,
                    "admissible": c <= tolerance_r,
                    "notional_usdt": notional(s, risk_dollars),
                    "leverage_x": implied_leverage(s, risk_dollars, equity),
                })
    return rows


def admissibility_table(fees, maker_fracs=MAKER_FRAC_AXIS, slips=SLIP_AXIS,
                        tolerance_r=COST_TOLERANCE_R):
    """min_admissible_stop over (maker_frac x slip), as {maker_frac: {slip: s*}}."""
    return {
        mf: {sl: min_admissible_stop(tolerance_r, mf, sl, fees) for sl in slips}
        for mf in maker_fracs
    }


#: Candidate stop widths for the break-even table, as fractions of entry price.
#: Chosen to bracket the working range rather than to be swept: a break-even
#: table is read row by row against a measured slippage, not integrated over.
BREAKEVEN_S_AXIS = (0.005, 0.0075, 0.010, 0.015, 0.020, 0.025, 0.030, 0.040, 0.050)


def breakeven_table(fees, s_axis=BREAKEVEN_S_AXIS, maker_fracs=MAKER_FRAC_AXIS,
                    tolerance_r=COST_TOLERANCE_R):
    """max_tolerable_slip over (s x maker_frac), as {s: {maker_frac: result}}.

    Cell values are whatever `max_tolerable_slip` returns -- a decimal fraction
    per side, `SLIP_UNCONSTRAINED`, or `None`. The three are not collapsed into
    one numeric type here; distinguishing them is the point.
    """
    return {
        s: {mf: max_tolerable_slip(s, mf, tolerance_r, fees) for mf in maker_fracs}
        for s in s_axis
    }


def slippage_sensitivity(fees, maker_fracs=MAKER_FRAC_AXIS, slips=SLIP_AXIS,
                         tolerance_r=COST_TOLERANCE_R):
    """How far s* travels across the whole slip axis, per maker_frac.

    Returns {maker_frac: {"s_star_at_min_slip", "s_star_at_max_slip", "spread"}},
    all as decimal fractions of price. The caller converts to percentage points
    at the presentation layer.

    THE SPREAD IS 2*(1 - maker_frac)*(slip_hi - slip_lo)/tolerance_r. It shrinks
    linearly in maker_frac and is exactly ZERO at maker_frac = 1.0.

    RETAINED FOR DIAGNOSIS ONLY -- DO NOT DRAW A VERDICT FROM IT. The spread is
    proportional to (slip_hi - slip_lo), which is a property of whatever axis
    the caller passed in, not of the strategy. Report 17's first pass concluded
    slippage was load-bearing from a ratio of this spread to the fee-axis
    spread, computed over a slippage interval that had been written down rather
    than measured; the ratio restated the interval. `max_tolerable_slip` is the
    axis-independent form and is what the report now uses.
    """
    lo, hi = min(slips), max(slips)
    out = {}
    for mf in maker_fracs:
        s_lo = min_admissible_stop(tolerance_r, mf, lo, fees)
        s_hi = min_admissible_stop(tolerance_r, mf, hi, fees)
        out[mf] = {
            "slip_min": lo,
            "slip_max": hi,
            "s_star_at_min_slip": s_lo,
            "s_star_at_max_slip": s_hi,
            "spread": s_hi - s_lo,
        }
    return out
