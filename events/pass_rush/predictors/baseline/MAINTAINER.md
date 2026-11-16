# MAINTAINER

- __init__.py: `predict` and `dropback` (the result mix, which another implementation can replace).
- test_pass_rush.py: a quarterback's season moves his dropback rates.
- priors.py: `observe(tally, sample)`, which counts one real play into this predictor's priors, and `observe_totals(tally, totals)`, which counts a week's charted totals.
- priors_<season>.json: the built priors (raw counts and histograms), one file per season (2011 on), counted week by week.

Notes:
- The quarterback's own sack and scramble rates were measured with the carriers' and targets' usage (`shared/priors/MAINTAINER.md`): together they took 18% off the quarterback rushing yards score. `DROPBACKS` at 40, 75, and 150 are within noise of each other; 300 was worse on quarterback rushing yards (+5.6%, 1.9 standard errors).
- Whether there is a sack only reads the quarterback: the pass rushers and the line in front of him aren't read. Who gets it reads the rushers' own sacks and hits.
- A blitz isn't tied to `rushers`: the count of rushers comes from one charting (FTN, 2022 on) and the blitzes from another (PFR), which calls a quarter of dropbacks blitzed where FTN counts an eighth with a blitzer.
- PFR's "times hit" is a hit without a sack (about half the official quarterback hits, which count sacks), and its pressures are hurries, hits, and sacks: that is how `scenarios/play/stats.py` adds them up, and the passer's side comes out exactly (pressured = hurried + hit + sacked in the data).
