# MAINTAINER

- __init__.py: `predict`.
- priors.py: `observe(tally, sample)`, which counts one real play into this predictor's priors.
- priors_<season>.json: the built priors (raw counts and histograms), one file per season (2011 on), counted week by week.

Notes:
- Safety kicks use the kickoff priors.
