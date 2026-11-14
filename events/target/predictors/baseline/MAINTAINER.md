# MAINTAINER

- __init__.py: `predict`.
- priors.py: `observe(tally, sample)`, which counts one real play into this predictor's priors.
- priors_<season>.json: the built priors (raw counts and histograms), one file per season.

Notes:
- Inside the 10 the air yards are resampled (up to 20 times) to stay inside the end line.
- `target_rate` is a rate per snap on the field, not a count of targets, for the same reason as the snap predictor's `carry_rate`: the lineups predictor already decides how often each receiver is out there.
