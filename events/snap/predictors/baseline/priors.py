# START
# Builds the baseline snap priors from real plays.
# - observe(tally, sample): pass_rate[script|down|distance bucket]: pass (dropbacks) or run;
#   two_point_play: pass or run on two-point tries;
#   carry_rate[role]: carried or other, for each quarterback, back, receiver, and tight end on the field for a
#   designed run (who carries, given who is out there), in seasons whose data records who was on the field.
# END
from shared.priors import dist_bucket, played, role, script

CARRIERS = ("QB", "RB", "FB", "WR", "TE")


def observe(t, sample):
    s, row, action = sample.context.situation, sample.row, sample.actual["action"]
    if action == "no_play":
        return
    if s.kind == "scrimmage" and action in ("run", "scramble", "pass", "sack"):
        t.c[f"pass_rate|{script(s)}|{s.down}|{dist_bucket(s.distance)}"]["pass" if action != "run" else "run"] += 1
    if s.kind == "try":
        if row.two_point_attempt == 1:
            t.c["two_point_play"]["pass" if action in ("pass", "sack") else "run"] += 1
        return
    on_field = played(sample)
    if action == "run" and on_field and row.rusher_player_id in on_field[0]:
        for player in map(sample.context.by_id.get, on_field[0]):
            if player.position in CARRIERS:
                t.c[f"carry_rate|{role(player)}"]["carried" if player.id == row.rusher_player_id else "other"] += 1
