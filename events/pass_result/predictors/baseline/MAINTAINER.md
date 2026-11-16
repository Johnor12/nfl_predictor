# MAINTAINER

- __init__.py: `predict`.
- priors.py: `observe(tally, sample)`, which counts one real play into this predictor's priors, and `observe_totals(tally, totals)`, which counts a week's charted totals.

Notes:
- The defender in coverage isn't tied to the receiver: nothing in the data says who covered whom, so a defender's coverage stats follow how often he is thrown at, not who he lines up against.
- priors_<season>.json: the built priors (raw counts and histograms), one file per season (2011 on), counted week by week.
