# MAINTAINER

- __init__.py: `predict`, `_category` (the kind of play, from the record), and `_foul_spot`.
- priors.py: `observe(tally, sample)`, which counts one real play into this predictor's priors.
- priors_<season>.json: the built priors (raw counts and histograms), one file per season (2011 on), counted week by week.

Notes:
- Pre-snap fouls are counted by the pre-snap event's priors, not here.
- nflverse names more fouls than the play scenario has. `shared.priors.flag` counts one under the scenario's foul that is enforced the same way (illegal use of hands as holding, a disqualification as unnecessary roughness), and drops the rest.
- nflverse labels a play wiped out by a penalty `no_play`; `priors.py` reads the kind of play from its description (`shared.priors.nullified`).
- Simulated games have about 2.5 fewer accepted penalties than real ones (10 a game against 12.5; `team: penalties` in `evaluators/game`). It was hidden while simulated games ran long. Two causes, measured on 24 games:
  - The priors count accepted penalties (nflverse's `penalty` is 1 only for those), but the predictor's flags then go through the play scenario's accept/decline rule, which declines about 1.2 a game. The real declined flags (about 1.6 a game) are only in the play descriptions ("Penalty on ..., declined"); counting them would make the priors flags thrown, which is what the event predicts.
  - A sampled foul the rules don't allow on the play is dropped, about 0.85 a game: pass interference on a sack or a scramble (0.27; the rate is per pass play, thrown or not), the return team's fouls on a punt or kickoff that isn't returned, and intentional grounding (never placed).
