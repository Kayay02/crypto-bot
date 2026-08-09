"""Timeframe candidacy: resampling, ATR% distributions, and the frozen rule.

WHAT THIS PACKAGE IS FOR. Point 1 is reopened and the timeframe is NOT
inherited -- 15m came from the original Point 1, and section 8.3 of
`docs/handoff/16_point_4_closing.md` states that no Point 4 choice carries
forward by default. Reports 17 and 18 fixed a cost floor the new hypothesis
inherits; this package measures on which timeframes an ATR-proportional stop
placed at that floor is actually OPERATIVE rather than decorative.

THE RULE IS PRE-REGISTERED AND FROZEN. `docs/handoff/19_timeframe_rule.md`,
committed alone at 96c96cf before any measurement code existed and before any
bar was read. `atr_profile.py` implements it; it does not get to reinterpret it.

THE HOLDOUT IS SEALED, AND RESAMPLING IS A NEW CODE PATH ONTO SEALED DATA.
Nothing at or after 2025-01-01 may be read here. The 1m layer is physically
partitioned by year and DOES contain year=2025 and year=2026 directories on
disk, so the seal is not maintained by absence -- it is maintained by an
explicit year filter plus `assert_sealed` on every frame this package returns.
A planted mutation widens the filter and is required to be caught.

THE PERFORMANCE FIREWALL IS RE-ARMED. No expectancy, win rate, profit factor,
Sharpe, equity curve, r_multiple or net_pnl aggregate is computed, referenced
or estimated anywhere in this package. ATR percentiles are an explicitly
permitted pre-firewall quantity. No trade is simulated, no signal is generated,
and no entry rule exists yet. A test walks the AST of every module here and
refuses any of those names as an identifier or string literal.

NO OPEN PRICE. The Bitget `open` field is synthesised (carried-forward previous
close) and is renamed `open_synth` in the derived layer precisely so a
reference fails loudly. ATR needs only high, low and close, so nothing here has
any business touching it. A test greps the package for the name.
"""
