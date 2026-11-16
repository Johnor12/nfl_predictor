# START
# Builds the baseline snap priors from real plays.
# - observe(tally, sample): pass_rate[script|down|distance bucket]: pass (dropbacks) or run;
#   two_point_play: pass or run on two-point tries;
#   fake[punt or field_goal]: kick, run, or pass, by what the kicking unit did on a scrimmage down (a snap it
#   never got hold of counts as a kick: the bad snap is predicted on its own). Its plays count nowhere else;
#   carry_rate[role]: carried or other, for each quarterback, back, receiver, and tight end on the field for a
#   designed run (who carries, given who is out there), in seasons whose data records who was on the field;
#   carries_per_snap[role]: the same over every offensive snap he is on the field for (the units a player's
#   own season comes in: Player.stats' carries and offense_snaps).
# END
from shared.priors import dist_bucket, played, role, script, sent_out

CARRIERS = ("QB", "RB", "FB", "WR", "TE")
SNAPS = ("run", "scramble", "pass", "sack")


def observe(t, sample):
    s, row, action = sample.context.situation, sample.row, sample.actual["action"]
    if action == "no_play":
        return
    unit = sent_out(sample) if s.kind == "scrimmage" else None
    if unit in ("punt", "field_goal"):
        kicked = action == unit or row.aborted_play == 1
        t.c[f"fake|{unit}"]["kick" if kicked else "run" if action == "run" else "pass"] += 1
        return
    if s.kind == "scrimmage" and action in ("run", "scramble", "pass", "sack"):
        t.c[f"pass_rate|{script(s)}|{s.down}|{dist_bucket(s.distance)}"]["pass" if action != "run" else "run"] += 1
    if s.kind == "try":
        if row.two_point_attempt == 1:
            t.c["two_point_play"]["pass" if action in ("pass", "sack") else "run"] += 1
        return
    on_field = played(sample)
    carrier = row.rusher_player_id if action == "run" else None
    if not on_field or action not in SNAPS or (carrier and carrier not in on_field[0]):
        return
    for player in map(sample.context.by_id.get, on_field[0]):
        if player.position in CARRIERS:
            carried = "carried" if player.id == carrier else "other"
            t.c[f"carries_per_snap|{role(player)}"][carried] += 1
            if carrier:
                t.c[f"carry_rate|{role(player)}"][carried] += 1
