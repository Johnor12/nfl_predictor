# MAINTAINER

- __init__.py: `predict` and `_pass_rate`.
- priors.py: `observe(tally, sample)`, which counts one real play into this predictor's priors.
- priors_<season>.json: the built priors (raw counts and histograms), one file per season (2011 on), counted week by week.

Notes:
- A hurry or bleed script's pass rate is blended with the normal script's for the same down and distance.
- `carry_rate` is a rate per designed run he is on the field for, not a count of carries: the lineups predictor already decides how often each back is out there, so a count by role would charge a backup for his playing time twice (and hand his carries to the quarterback). It needs who was on the field, so it comes from 2025 until 2026's participation data is published.
- `carries_per_snap` counts the same players over every offensive snap (runs and dropbacks). It only exists to put a role's rate in the units a player's own season comes in: the data says how many snaps he played, not how many designed runs he was out there for.
- The player's own carries are `Player.stats["carries"]` (designed runs), not `rush_att`, which counts a quarterback's scrambles and kneels.
- Run or pass doesn't look at the personnel group on the field yet.
