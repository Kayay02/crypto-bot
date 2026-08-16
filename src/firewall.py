"""THE PERFORMANCE FIREWALL'S BANNED-NAME LIST, DEFINED ONCE.

WHY THIS MODULE EXISTS. The list was previously written out in full in EIGHTEEN
separate test modules, and it had drifted: fourteen carried twelve names and four
carried a nine-name variant missing `sortino`, `gross_pnl` and `drawdown`. The
project's central safety mechanism was enforced by eighteen copies of a list that
no longer agreed with itself, and four modules enforced a guard with three holes
in it. `docs/prompts/STANDING_RULES.md` §1.2 recorded the divergence.

    A GUARD COPIED EIGHTEEN TIMES IS EIGHTEEN GUARDS, AND THEY DIVERGE SILENTLY.

`tests/test_firewall_names.py` asserts over the AST that no module defines its own
copy, which is the property this module exists to make enforceable rather than
merely true today.

WHY IT SITS AT THE TOP OF `src/` RATHER THAN INSIDE A SUBPACKAGE. Every existing
subpackage names a domain -- analysis, engine, risk, timeframe, venue, folds,
sweep, costs, data, regime -- and the firewall crosses all of them. It is not a
measurement, so `src/analysis/` is wrong by that package's own scope; it is not
cost algebra, a risk specification or a data path either. A top-level module keeps
one import path, identical from `tests/` and from any `src/` subpackage.

THIS MODULE IMPORTS NOTHING AND COMPUTES NOTHING. It is a list and two helpers
over it.
"""

#: The twelve banned names, in the order report 25 fixed them.
#:
#: PROVENANCE. Reports 19 to 21 carried nine. Report 24 section 9.5 recorded that
#: `drawdown`, `sortino` and `gross_pnl` were absent from that list, and report 25
#: added them. `tests/test_budget_cost.py` described the result as "Report 25's
#: twelve-name list. It only ever grows."
#:
#: THE LIST ONLY EVER GROWS. A name is never removed. `test_firewall_names.py`
#: pins the membership so that a removal fails rather than passing quietly.
PERFORMANCE_NAMES = ("expectancy", "win_rate", "winrate", "profit_factor",
                     "sharpe", "sortino", "net_pnl", "gross_pnl", "drawdown",
                     "r_multiple", "equity", "pnl")

#: The three names report 24 section 9.5 flagged as missing and report 25 added.
#: Named separately so the widening is assertable rather than merely present.
WIDENED_IN_REPORT_25 = ("drawdown", "sortino", "gross_pnl")

#: The nine-name list reports 19 to 21 and 24 carried. RETAINED AS HISTORY, NOT AS
#: AN ALTERNATIVE. Two test modules assert the twelve-name list is a superset of
#: it, which is how the widening is pinned; this constant gives them one source
#: for it instead of two hand-written copies.
INHERITED_FROM_REPORT_24 = ("expectancy", "win_rate", "winrate", "profit_factor",
                            "sharpe", "net_pnl", "r_multiple", "equity", "pnl")


def is_banned(name):
    """Does `name` contain a banned name as a substring, case-insensitively?

    SUBSTRING, NOT EQUALITY, because the guards search identifiers and string
    literals in which a banned name may appear as part of a longer token --
    `net_pnl_total` is as much a violation as `net_pnl`.
    """
    lowered = str(name).lower()
    return any(banned in lowered for banned in PERFORMANCE_NAMES)


def banned_in(text):
    """Every banned name appearing in `text`, in list order.

    THE CALLER SUPPLIES THE TEXT AND IS RESPONSIBLE FOR HAVING BUILT IT FROM
    EXECUTABLE TOKENS OR AST NODES rather than from raw source, per the standing
    verification rule at `docs/design/04_1a_denomination_amendment_1.md` section
    7. This function does not read files and cannot enforce that.
    """
    lowered = str(text).lower()
    return tuple(banned for banned in PERFORMANCE_NAMES if banned in lowered)
