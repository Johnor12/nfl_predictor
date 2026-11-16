# MAINTAINER

- __init__.py: `predict`, `shotgun_rate` (the part of it another implementation replaces), and the templates (`_formation`).
- priors.py: `observe(tally, sample)`, which counts one real play into this predictor's priors.
- priors_<season>.json: the built priors (raw counts and histograms), one file per season (2011 on), counted week by week.

Notes:
- Receiver splits, motion, and shifts aren't modeled.
- A lineup with four backs (`40` personnel) puts the fourth on the line: with all four behind the quarterback only six are on the line, which is illegal.
