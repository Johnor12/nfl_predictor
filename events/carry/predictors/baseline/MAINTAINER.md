# MAINTAINER

- __init__.py: `predict`.
- priors.py: `observe(tally, sample)`, which counts one real play into this predictor's priors.
- priors_<season>.json: the built priors (raw counts and histograms), one file per season (2011 on).

Notes:
- Run, scramble, and catch histograms only use carries that started 50+ yards from the goal line, so long gains aren't cut short by touchdowns; goal-to-go histograms are keyed by 1-2, 3-5, and 6-10 yards to go.
- Laterals happen at the season-wide rate, whatever the situation; most real ones are hook-and-laterals or last-play desperation. Returns never end in one (a handful a season).
