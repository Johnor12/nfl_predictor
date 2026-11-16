# MAINTAINER

- __init__.py: `predict`, `play_key`, and `challengeable`.
- priors.py: `observe(tally, sample)`, which counts one real play into this predictor's priors.
- priors_<season>.json: the built priors (raw counts), one file per season (2011 on), counted week by week.

Notes:
- The play-by-play names the challenging team by its city in the play's description (`shared/nflverse/contexts.py`, `_challenge`). A lost challenge without one is the team charged the timeout on the play's row.
- The replay official's own reviews aren't counted or predicted: they cost nobody anything.
- Nothing about the score, the clock, or the spot is used, and a team's timeouts only decide whether it may challenge. About one play in 300 is challenged, so the buckets are kept few.
