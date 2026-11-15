# MAINTAINER

- __init__.py: `predict` and `_yards` (which histogram a carry draws from).
- priors.py: `observe(tally, sample)`, which counts one real play into this predictor's priors.
- priors_<season>.json: the built priors (raw counts and histograms), one file per season (2011 on), counted week by week.

Notes:
- Run, scramble, and catch histograms only use carries that started 50+ yards from the goal line, so long gains aren't cut short by touchdowns; goal-to-go histograms are keyed by 1-2, 3-5, and 6-10 yards to go.
- A position without a histogram of its own (a lineman) runs like a back and, at that pass depth, catches like a receiver.
- The durations were measured on plays that stop the clock, where the time to the next snap is the play alone (2023 to 2025): a run out of bounds late in a half 6.6 seconds, a completion 6.2, a scramble 8.3. A catch's carry starts counting at the catch: the time to throw and the ball's flight are the pass rush's and the pass result's.
- Laterals happen at the season-wide rate, whatever the situation; most real ones are hook-and-laterals or last-play desperation. Returns never end in one (a handful a season).
