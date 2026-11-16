# START
# Builds the baseline challenge priors from real plays.
# - observe(tally, sample): counts one real play a coach could challenge (see shared/priors/building.py).
#   challenge[play key]: offense_won, offense_lost, defense_won, defense_lost, or none, by who challenged
#   the play and whether the ruling was reversed (sample.actual["challenge"]).
# END
from events.challenge.predictors.baseline import challengeable, play_key


def observe(t, sample):
    s, challenge = sample.context.situation, sample.actual["challenge"]
    if not challengeable(s):
        return
    who = "none"
    if challenge:
        team, won = challenge
        who = f"{'offense' if team == s.offense else 'defense'}_{'won' if won else 'lost'}"
    t.c[f"challenge|{play_key(sample.actual)}"][who] += 1
