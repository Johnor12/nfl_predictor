# START
# Builds the baseline target priors from real plays.
# - observe(tally, sample): target[role]: who was thrown to; air_yards: histogram outside the 10;
#   air_yards_goal[goal bucket]: histograms inside the 10; direction: left, middle, or right.
# END
from shared.priors import goal_bucket, present, role


def observe(t, sample):
    s, row, action = sample.context.situation, sample.row, sample.actual["action"]
    if s.kind == "try" or action != "pass" or not present(row.receiver_player_id):
        return
    receiver = sample.context.by_id.get(row.receiver_player_id)
    if receiver:
        t.c["target"][role(receiver)] += 1
    if present(row.air_yards):
        if row.yardline_100 <= 10:
            t.hist[f"air_yards_goal|{goal_bucket(row.yardline_100)}"].append(row.air_yards)
        else:
            t.hist["air_yards"].append(row.air_yards)
    if present(row.pass_location):
        t.c["direction"][row.pass_location] += 1
