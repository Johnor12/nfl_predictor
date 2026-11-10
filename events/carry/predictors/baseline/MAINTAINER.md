# MAINTAINER

- __init__.py: `predict`.
- priors.py: `observe(tally, sample)`, which counts one real play into this predictor's priors.
- priors_2026.json: the built priors (raw counts and histograms).

Notes:
- Run, scramble, and catch histograms only use carries that started 50+ yards from the goal line, so long gains aren't cut short by touchdowns; goal-to-go histograms are keyed by 1-2, 3-5, and 6-10 yards to go.
- Laterals aren't modeled: a carry can't end in one.
