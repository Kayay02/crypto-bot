"""Read-only analysis code.

Nothing here simulates a trade, and nothing here reads `net_pnl` or
`r_multiple`. Every quantity produced is a bar-level statistic, a count or a
correlation -- the performance firewall (see docs/handoff/05_point_1r.md) is in
force until the start of Point 4.

Indicator definitions are IMPORTED from src/engine, never reimplemented, so
"breakout bar" means exactly the same thing here as it does in the engine.
"""
