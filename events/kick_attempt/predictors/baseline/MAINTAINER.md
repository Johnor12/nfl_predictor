# MAINTAINER

- __init__.py: `predict`.
- priors.py: `observe(tally, sample)`, which counts one real play into this predictor's priors.
- priors_2026.json: the built priors (raw counts and histograms).

Notes:
- The priors keep nflverse's result names (made/missed/blocked, good/failed/blocked); `predict` maps them to `RESULTS`.
