# MAINTAINER

- __init__.py: `predict` and `_play_clock_used`.
- priors.py: `observe(tally, sample)`, which counts one real play into this predictor's priors.
- priors_2026.json: the built priors (raw counts and histograms).

Notes:
- Delay of game comes from the foul rate, not from the clock usage.
