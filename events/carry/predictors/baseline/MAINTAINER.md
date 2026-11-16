# MAINTAINER

- __init__.py: `predict` and `_yards` (which histogram a carry draws from).
- priors.py: `observe(tally, sample)`, which counts one real play into this predictor's priors (`_tackle`: who the box score credited), and `observe_totals(tally, totals)`, which counts a week's charted totals.
- priors_<season>.json: the built priors (raw counts and histograms), one file per season (2011 on), counted week by week.

Notes:
- Run, scramble, and catch histograms only use carries that started 50+ yards from the goal line, so long gains aren't cut short by touchdowns; goal-to-go histograms are keyed by 1-2, 3-5, and 6-10 yards to go.
- A position without a histogram of its own (a lineman) runs like a back and, at that pass depth, catches like a receiver.
- The durations were measured on plays that stop the clock, where the time to the next snap is the play alone (2023 to 2025): a run out of bounds late in a half 6.6 seconds, a completion 6.2, a scramble 8.3. A catch's carry starts counting at the catch: the time to throw and the ball's flight are the pass rush's and the pass result's.
- The tackle credit used to be hand-set: always on a tackle, half the time out of bounds, one rate of shared tackles, one set of position weights. Real carries that go out of bounds credit a tackler 88% (catches) to 100% (runs) of the time, which was most of the 6.8 solo tackles a team that simulated games were short of (33.9 against a real 40.7); the rest was the sack, which a box score also counts as a tackle (`scenarios/play/stats.py`).
- A tackle with an assist (one tackle and one assist, an eighth of runs) can't be said with `CarryEnd.tacklers` (one is a tackle, two are two assists), so `shared` counts it half as each: the tackles and the assists both come out right in total.
- The charting only comes per player and game, so `observe_totals` turns a week's totals into rates: a broken tackle per carry, a missed tackle per carry without one (the charters count about twice the misses they count broken tackles, so every broken tackle is somebody's miss and the rest are misses alone), and a run's yards after contact as a share of its yards. The yards before contact of one run are that share with a uniform spread around it: the league's average is right and nothing more is known per carry.
- Laterals happen at the season-wide rate, whatever the situation; most real ones are hook-and-laterals or last-play desperation. Returns never end in one (a handful a season).
