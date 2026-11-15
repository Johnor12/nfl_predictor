# MAINTAINER

- __init__.py: `predict`, `_category` (the kind of play, from the record), and `_foul_spot`.
- priors.py: `observe(tally, sample)`, which counts one real play into this predictor's priors.
- priors_<season>.json: the built priors (raw counts and histograms), one file per season (2011 on).

Notes:
- Pre-snap fouls are counted by the pre-snap event's priors, not here.
- nflverse names more fouls than the play scenario has. `shared.priors.flag` counts one under the scenario's foul that is enforced the same way (illegal use of hands as holding, a disqualification as unnecessary roughness), and drops the rest.
- nflverse labels a play wiped out by a penalty `no_play`; `priors.py` reads the kind of play from its description (`shared.priors.nullified`).
