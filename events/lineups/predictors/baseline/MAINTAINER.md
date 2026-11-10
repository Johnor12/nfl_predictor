# MAINTAINER

- __init__.py: `predict`, the unit choice (`_unit`, `_kneel`, `_two_point_rate`, `_onside`).
- depth_chart.py: the personnel mix, the defense's matching package, and 11 players for any unit by depth chart rank (base/nickel/dime, 4-3 or 3-4 aware) with position fallbacks.
- test_lineups.py: spot checks (depth chart, kneel rule, 4th-and-long punts).
- priors.py: `observe(tally, sample)`, which counts one real play into this predictor's priors.
- priors_2026.json: the built priors (raw counts and histograms).

Notes:
- Priors are keyed `down|distance bucket|field bucket`; a cell with fewer than 20 samples is blended with the down and field bucket's total.
