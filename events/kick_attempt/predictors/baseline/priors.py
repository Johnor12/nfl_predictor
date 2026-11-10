# START
# Builds the baseline kick attempt priors from real plays.
# - observe(tally, sample): pat: nflverse extra point results (good, failed, blocked);
#   fg[distance bin]: nflverse field goal results (made, missed, blocked).
# END
from shared.priors import fg_bin, present


def observe(t, sample):
    row, action = sample.row, sample.actual["action"]
    if sample.context.situation.kind == "try":
        if action == "extra_point":
            t.c["pat"][str(row.extra_point_result)] += 1
    elif action == "field_goal" and present(row.kick_distance):
        t.c[f"fg|{fg_bin(row.kick_distance)}"][str(row.field_goal_result)] += 1
