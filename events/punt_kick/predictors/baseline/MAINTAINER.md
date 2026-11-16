# MAINTAINER

- __init__.py: `predict`, `distance`, and `histogram` (the distance is the part another implementation can replace).
- priors.py: `observe(tally, sample)`, which counts one real play into this predictor's priors.
- priors_<season>.json: the built priors (raw counts and histograms), one file per season (2011 on), counted week by week.
