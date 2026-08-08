"""Read-only analysis code.

`structural_pass.py` predates the lift: it simulates no trade and reads neither
`net_pnl` nor `r_multiple`. Every quantity it produces is a bar-level
statistic, a count or a correlation.

`dispersion.py` is E6 -- step 1 of the §4.4 sequence, and the module whose run
LIFTED the performance firewall. It reads `r_multiple` to measure DISPERSION
and COUNTS only: standard deviations, trade counts, standard errors, quantile
spreads, min and max. It emits no mean, median or sum of `r_multiple` or
`net_pnl`, and enforces that with a guard tested against its own target
mutation. The lift is partial -- the holdout stays sealed until step 9, and no
loader here is passed authorised=True.

Indicator definitions are IMPORTED from src/engine, never reimplemented, so
"breakout bar" means exactly the same thing here as it does in the engine.
"""
