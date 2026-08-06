"""Point 4.1 -- regime characterisation.

Reads 15m OHLCV and writes regime labels. NOTHING ELSE. The performance
firewall is in force: no module here reads, computes, aggregates or prints
`net_pnl`, `r_multiple`, expectancy, win rate, or any other quantity derived
from a trade outcome. `src/engine/simulate.py` is deliberately not imported,
and a test enforces that.

Regime labels feed exactly three things (docs/handoff 4.1):
  1. interpretation of post-lift results,
  2. the cross-symbol concordance check behind the two-of-three rule,
  3. Point 8 decay detection.

They feed NOTHING else -- never fold boundaries, parameter ranges, sweep
design, acceptance thresholds or drop decisions. A regime label reaching any of
those has become a channel for fitting.

Every value at bar T is computable from bars at or before T. This is not a
bonus property: a descriptive statement conditioning on something unobservable
at the time is useless, and decay detection is impossible for a condition only
identifiable in retrospect.
"""
