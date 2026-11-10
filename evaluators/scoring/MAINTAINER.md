# MAINTAINER

- __init__.py: the public API (re-exports).
- scores.py: the score functions (`fair_crps`, `fair_brier`, `score`, `kind_of`, `climatology`, `brier`, `log_loss`, `probability`) and diagnostics (`pit`, `histogram`, `reliability`). Pure functions of plain values.
- scorecard.py: `Scorecard`, which keeps each output's per-case scores, half-ensemble differences, outcomes, PIT values, and forecasts, and summarizes them in `rows()`.
- report.py: markdown for a scorecard (`OUT`, `GUIDE`, `score_table`, `pit_table`, `reliability_table`).
- test_scoring.py: the scores' properties (fairness, the binary and multiclass identities, the reference), calibrated forecasts looking calibrated, and the scorecard.

Notes:
- This package imports nothing from the rest of the project.
- One implementation scores numbers and yes/no outcomes: fair CRPS on True/False samples is the fair Brier score. `fair_brier` is that, summed over the classes.
- Outcomes must be a plain `bool`, `str`, `int`, or `float` (`kind_of` raises otherwise). A numpy bool from a pandas row would be scored as a number, so convert when reading data (`bool(row.shotgun == 1)`).
- The reference is computed from the outcomes alone (`climatology`): half the mean absolute difference between two different cases' outcomes, which is the mean fair score of forecasting each case with all the others.
- A half-ensemble difference has 4 times the sim variance of the full ensemble's score (two halves, each with twice the variance). That's the 2 in `sim_se`.
- A categorical output's reliability uses every class the output ever took (in any forecast or outcome), so a class given 0% in a case still counts.
- The scorecard keeps per-case values rather than sums, so they can be merged across processes and, later, compared case by case between two predictor versions.
