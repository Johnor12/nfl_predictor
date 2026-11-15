# START
# Builds the baseline target priors from real plays.
# - observe(tally, sample): air_yards[position group of the receiver]: histograms outside the 10;
#   air_yards_goal[goal bucket]: histograms inside the 10; direction: left, middle, or right;
#   target_rate[role]: targeted or other, for each back, receiver, and tight end on the field for a targeted
#   pass (who is thrown to, given who is out there), in seasons whose data records who was on the field;
#   targets_per_snap[role]: the same over every offensive snap he is on the field for (the units a player's
#   own season comes in: Player.stats' targets and offense_snaps).
# END
from shared.priors import goal_bucket, group, played, present, role

RECEIVERS = ("RB", "FB", "WR", "TE")
SNAPS = ("run", "scramble", "pass", "sack")


def observe(t, sample):
    s, row, action = sample.context.situation, sample.row, sample.actual["action"]
    if s.kind == "try" or action not in SNAPS:
        return
    receiver = row.receiver_player_id if action == "pass" and present(row.receiver_player_id) else None
    on_field = played(sample)
    if on_field and (not receiver or receiver in on_field[0]):
        for player in map(sample.context.by_id.get, on_field[0]):
            if player.position in RECEIVERS:
                targeted = "targeted" if player.id == receiver else "other"
                t.c[f"targets_per_snap|{role(player)}"][targeted] += 1
                if receiver:
                    t.c[f"target_rate|{role(player)}"][targeted] += 1
    if not receiver:
        return
    if present(row.air_yards):
        player = sample.context.by_id.get(receiver)
        if row.yardline_100 <= 10:
            t.hist[f"air_yards_goal|{goal_bucket(row.yardline_100)}"].append(row.air_yards)
        elif player and player.position in RECEIVERS:
            t.hist[f"air_yards|{group(player)}"].append(row.air_yards)
    if present(row.pass_location):
        t.c["direction"][row.pass_location] += 1
