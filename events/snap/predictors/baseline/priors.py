# START
# Builds the baseline snap priors from real plays.
# - observe(tally, sample): pass_rate[script|down|distance bucket]: pass (dropbacks) or run;
#   two_point_play: pass or run on two-point tries; run_carrier[role]: who carried on designed runs.
# END
from shared.priors import dist_bucket, role, script


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
    if action == "run":
        rusher = sample.context.by_id.get(row.rusher_player_id)
        if rusher:
            t.c["run_carrier"][role(rusher)] += 1
