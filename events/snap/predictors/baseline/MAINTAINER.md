# MAINTAINER

- __init__.py: `predict` and `_pass_rate`.
- priors.py: `observe(tally, sample)`, which counts one real play into this predictor's priors.
- priors_<season>.json: the built priors (raw counts and histograms), one file per season (2011 on).

Notes:
- A hurry or bleed script's pass rate is blended with the normal script's for the same down and distance.
- `carry_rate` is a rate per snap on the field, not a count of carries: the lineups predictor already decides how often each back is out there, so a count by role would charge a backup for his playing time twice (and hand his carries to the quarterback). It needs who was on the field, so it comes from 2025 until 2026's participation data is published.
- Run or pass doesn't look at the personnel group on the field yet.
