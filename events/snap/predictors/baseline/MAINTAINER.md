# MAINTAINER

- __init__.py: `predict` and `_pass_rate`.
- priors.py: `observe(tally, sample)`, which counts one real play into this predictor's priors.
- priors_2026.json: the built priors (raw counts and histograms).

Notes:
- A hurry or bleed script's pass rate is blended with the normal script's for the same down and distance.
