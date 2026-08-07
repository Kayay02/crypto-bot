"""Point 4.3 -- sweep grid definition and the A3 pre-screen (step 0, PRE-LIFT).

Everything here is determined AT ENTRY: the stop level follows from ATR at the
signal bar, the derived floor and the derived cap. No lifecycle resolution is
needed, so Layer B is never run and `simulate` is never imported.

FIREWALL. This package computes binding rates, pass rates, signal counts and
ATR percentiles -- all on the allowed list. It reads no trade outcome. Per
Appendix F.2 this is step 0 of the revised sequence and is explicitly NOT a
partial lift: it inspects no performance figure at all. The firewall lifts at
step 1 (E6) and not before.

HOLDOUT SEALED. Nothing at or after 2025-01-01 is loaded. `src/folds/` enforces
this with `authorised=False` defaults and nothing here overrides them.

NO REGIME LABELS. §4.1 forbids labels from touching parameter ranges. This
package does not import `src.regime`.
"""
