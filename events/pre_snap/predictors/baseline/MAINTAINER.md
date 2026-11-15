# MAINTAINER

- __init__.py: `predict` and `_play_clock_used`.
- priors.py: `observe(tally, sample)`, which counts one real play into this predictor's priors.
- priors_<season>.json: the built priors (raw counts and histograms), one file per season (2011 on).

Notes:
- Delay of game comes from the foul rate, not from the clock usage.
- The hand-set clock usage is too fast: simulated games run about 10 plays long (`game: plays` in `evaluators/game`, where nearly half the real games fall below every simulated one). Stopping the clock after late penalties, as the rules say, added about one more. This is the place to fix it.
