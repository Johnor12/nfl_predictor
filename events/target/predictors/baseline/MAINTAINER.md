# MAINTAINER

- __init__.py: `predict`.
- priors.py: `observe(tally, sample)`, which counts one real play into this predictor's priors.
- priors_<season>.json: the built priors (raw counts and histograms), one file per season (2011 on), counted week by week.

Notes:
- Inside the 10 the air yards are resampled (up to 20 times) to stay inside the end line.
- `target_rate` is a rate per targeted pass he is on the field for, not a count of targets, for the same reason as the snap predictor's `carry_rate`: the lineups predictor already decides how often each receiver is out there. `targets_per_snap` is the same over every offensive snap, the units a player's own season comes in (see the snap predictor's notes).
- A position without air yards of its own (a quarterback or a lineman catching a pass) gets a receiver's.
