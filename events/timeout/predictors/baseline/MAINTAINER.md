# MAINTAINER

- __init__.py: `predict`, `situation_key`, and `late`.
- priors.py: `observe(tally, sample)`, which counts one real play into this predictor's priors.
- priors_<season>.json: the built priors (raw counts), one file per season (2011 on), counted week by week.

Notes:
- The situation is read as it stood before the timeout: `shared.priors.timeout_case` gives the caller its timeout back and restores the clock.
- A lost challenge isn't a timeout here: the challenge event predicts it, and the game scenario charges it.
- A team can't call two timeouts in a row, so the second one between two plays is the other team's (`second`), whatever the situation: it is counted by how late it is alone.
- Nothing about the down, the spot, or the play clock is used, so timeouts that set up a kick or avoid a delay of game are only captured on average.
- A timeout on a stopped clock costs no game time, so `snap_gap` is only counted, and only sampled, on a running one. A key with no timeouts yet (a thin week 1) calls it at once.
- Before the call had a time, every timeout was called the moment the last play ended: about a minute of running clock a game that real teams use up and simulated ones didn't.
