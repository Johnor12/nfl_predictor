# START
# Builds the baseline target priors from real plays.
# - observe(tally, sample): air_yards: histogram outside the 10; air_yards_goal[goal bucket]: histograms
#   inside the 10; direction: left, middle, or right;
#   target_rate[role]: targeted or other, for each back, receiver, and tight end on the field for a targeted
#   pass (who is thrown to, given who is out there), in seasons whose data records who was on the field.
# END
from shared.priors import goal_bucket, played, present, role

RECEIVERS = ("RB", "FB", "WR", "TE")


def observe(t, sample):
    s, row, action = sample.context.situation, sample.row, sample.actual["action"]
    if s.kind == "try" or action != "pass" or not present(row.receiver_player_id):
        return
    on_field = played(sample)
    if on_field and row.receiver_player_id in on_field[0]:
        for player in map(sample.context.by_id.get, on_field[0]):
            if player.position in RECEIVERS:
                t.c[f"target_rate|{role(player)}"]["targeted" if player.id == row.receiver_player_id else "other"] += 1
    if present(row.air_yards):
        if row.yardline_100 <= 10:
            t.hist[f"air_yards_goal|{goal_bucket(row.yardline_100)}"].append(row.air_yards)
        else:
            t.hist["air_yards"].append(row.air_yards)
    if present(row.pass_location):
        t.c["direction"][row.pass_location] += 1
