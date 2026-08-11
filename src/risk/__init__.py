"""Book-level risk rules. Constants only at this commit.

WHAT LIVES HERE. Rules that constrain the BOOK rather than the trade: how much
aggregate exposure may be open at once, in what margin and position mode. Trade
level sizing is `src/engine/costs.py` and stays there.

WHY IT IS A SEPARATE PACKAGE. The aggregate budget is a risk-appetite choice,
not a cost quantity and not a venue fact, and it is pre-registered before the
measurement of its cost exists. Keeping it out of the engine is what lets it be
committed alone: nothing imports it yet, so committing it changes no behaviour
and the commit is a statement of intent rather than a change of code.

NOTHING HERE IS WIRED IN. No engine file imports this package at this commit.
That wiring is sub-point 5.3's work.
"""
