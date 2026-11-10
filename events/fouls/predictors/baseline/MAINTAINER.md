# MAINTAINER

- __init__.py: `predict`, `_category` (the kind of play, from the record), and `_foul_spot`.
- priors.py: `observe(tally, sample)`, which counts one real play into this predictor's priors.
- priors_2026.json: the built priors (raw counts and histograms).

Notes:
- Pre-snap fouls are counted by the pre-snap event's priors, not here.
- nflverse labels a play wiped out by a penalty `no_play`; `priors.py` reads the kind of play from its description (`shared.priors.nullified`).
