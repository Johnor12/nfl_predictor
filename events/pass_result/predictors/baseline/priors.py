# START
# Builds the baseline pass result priors from real plays.
# - observe(tally, sample): pass_result[air bucket] and pass_result_goal[goal bucket] (inside the 10):
#   complete, incomplete, or intercepted; defended: yes or no on incompletions.
# END
from shared.priors import air_bucket, goal_bucket, present


def observe(t, sample):
    s, row, action = sample.context.situation, sample.row, sample.actual["action"]
    if s.kind == "try" or action != "pass" or not present(row.receiver_player_id):
        return
    if present(row.air_yards):
        result = "intercepted" if row.interception == 1 else "complete" if row.complete_pass == 1 else "incomplete"
        if row.yardline_100 <= 10:
            t.c[f"pass_result_goal|{goal_bucket(row.yardline_100)}"][result] += 1
        else:
            t.c[f"pass_result|{air_bucket(row.air_yards)}"][result] += 1
    if row.incomplete_pass == 1:
        t.c["defended"]["yes" if present(row.pass_defense_1_player_id) else "no"] += 1
