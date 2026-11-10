# MAINTAINER

- __init__.py: `predict`.
- priors.py: `observe(tally, sample)`, which counts one real play into this predictor's priors.
- priors_2026.json: the built priors (raw counts and histograms).

Notes:
- Inside the 10 the air yards are resampled (up to 20 times) to stay inside the end line.
