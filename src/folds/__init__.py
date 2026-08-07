"""Point 4.2 -- walk-forward fold architecture.

Folds come from a FIXED CALENDAR RULE decided in advance. They are never
derived from data and never from regime labels: §4.1 forbids labels from
touching fold boundaries, because a boundary chosen to sit on a regime seam is
a channel for fitting. This package does not import `src.regime` for schedule
generation at all -- the only regime use anywhere here is reading already-frozen
labels to REPORT per-fold concordance, which is a description of folds that
already exist.

FIREWALL. This package produces date ranges, bar counts and signal counts.
Signal COUNTS are permitted; signal OUTCOMES are not. `simulate` is never
imported and no trade outcome is read.

HOLDOUT SEAL. The holdout is DEFINED here and never LOADED. Every loader takes
`authorised: bool = False` and raises on the default path.
"""
