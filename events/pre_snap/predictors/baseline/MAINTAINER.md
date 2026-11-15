# MAINTAINER

- __init__.py: `predict` and `_play_clock_used`.
- priors.py: `observe(tally, sample)`, which counts one real play into this predictor's priors.
- priors_<season>.json: the built priors (raw counts and histograms), one file per season (2011 on), counted week by week.

Notes:
- Delay of game comes from the foul rate, not from the clock usage.
- The data doesn't record the play clock at the snap (nflverse's `play_clock` is empty), only the game clock at each snap. So `snap_gap` is the time between two snaps, and the predictor takes off what the play in between took (`shared.priors.PLAY_SECONDS`, which the carry, pass rush, and pass result baselines' durations are set to match).
- `snap_gap` only counts snaps on a full play clock. After an administrative stoppage (a penalty, mostly) the previous "play" may not have been snapped at all, so the gap says little about the 25-second clock, which stays hand-set.
- The play clock used is capped a second short of the play clock: the gaps' long tail is long plays, not delays of game.
- With the hand-set clock usage this replaced, simulated games ran about 20 plays long (`game: plays` in `evaluators/game`: skill -129%); plays that were too short (a run took 3.4 seconds, an incompletion 2.7) were the other half of that. With the real gaps, real durations, and the time before a timeout, the skill is -2% on 160 games, and what is left is spread, not bias: every team snaps at the league's pace. Per quarter the simulated games are still about a second a play quick in the first quarter and slow inside the two-minute warning of the second.
