"""Venue constraints, retrieved from the exchange and stamped.

WHY THIS IS ITS OWN PACKAGE. It is not a data-layer module: it reads no bar, no
parquet and no derived series, and it must be able to say so structurally rather
than by assertion. It is not a cost module either -- fees live in
`src/costs/` because they enter the admissibility arithmetic, whereas what is
retrieved here (leverage tiers, maintenance margin rates, lot sizes, order
limits) constrains what the exchange will ACCEPT, which is a different question
from what a trade costs.

NOTHING HERE CHOOSES A PARAMETER. These modules retrieve and parse. Whether a
constraint binds, and what to do about it, is decided elsewhere and later.
"""
