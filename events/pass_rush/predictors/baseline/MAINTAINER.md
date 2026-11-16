# MAINTAINER

- __init__.py: `predict` and `dropback` (the result mix, which another implementation can replace).
- test_pass_rush.py: a quarterback's season moves his dropback rates.
- priors.py: `observe(tally, sample)`, which counts one real play into this predictor's priors.
- priors_<season>.json: the built priors (raw counts and histograms), one file per season (2011 on), counted week by week.

Notes:
- The quarterback's own sack and scramble rates were measured with the carriers' and targets' usage (`shared/priors/MAINTAINER.md`): together they took 18% off the quarterback rushing yards score. `DROPBACKS` at 40, 75, and 150 are within noise of each other; 300 was worse on quarterback rushing yards (+5.6%, 1.9 standard errors).
- Only the quarterback is read. The pass rushers and the line in front of him aren't.
