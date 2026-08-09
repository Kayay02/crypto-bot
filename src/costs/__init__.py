"""Cost admissibility -- the fee artifact and the closed-form cost envelope.

THIS PACKAGE TOUCHES NO MARKET DATA. It reads a published fee schedule and does
arithmetic on it. There is no parquet load, no OHLCV, no trade record, no
engine invocation, and no import of `src.folds`, `src.sweep`, `src.regime` or
`src/engine`. If a future edit needs any of those, it belongs in a different
package.

THE PERFORMANCE FIREWALL IS RE-ARMED. Point 4's hypothesis is closed
(docs/handoff/16_point_4_closing.md) and a new one has not been chosen. Nothing
here computes, references or estimates expectancy, win rate, profit factor, an
equity curve or any r_multiple aggregate. `COST_TOLERANCE_R` is derived from a
DISPERSION figure and a minimum-detectable-effect figure, both of which are on
the firewall's permitted list, and it was fixed before the fee rates were
retrieved.

NAME COLLISION, DELIBERATE. `src/engine/costs.py` is imported bare as `costs`
by the engine and by `tests/conftest.py`, which puts `src/engine` on sys.path.
This package is only ever reached as `src.costs`, so the two never resolve to
each other. Do not add `src/` to sys.path to shorten the import.
"""
