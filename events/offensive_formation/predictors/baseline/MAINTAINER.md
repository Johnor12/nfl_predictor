# MAINTAINER

- __init__.py: `predict` and the templates (`_formation`).
- priors.py: `observe(tally, sample)`, which counts one real play into this predictor's priors.
- priors_<season>.json: the built priors (raw counts and histograms), one file per season.

Notes:
- Receiver splits, motion, and shifts aren't modeled.
