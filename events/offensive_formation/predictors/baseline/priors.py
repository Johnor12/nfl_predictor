# START
# Builds the baseline offensive formation priors from real plays.
# - observe(tally, sample): shotgun[down|distance bucket]: shotgun or under_center on runs and dropbacks;
#   personnel_shotgun[personnel group|down|distance bucket]: the same by the personnel group on the field, in
#   seasons whose data records it.
# END
from shared.priors import dist_bucket, personnel


def observe(t, sample):
    s = sample.context.situation
    if s.kind == "scrimmage" and sample.actual["action"] in ("run", "scramble", "pass", "sack"):
        key = "shotgun" if sample.row.shotgun == 1 else "under_center"
        t.c[f"shotgun|{s.down}|{dist_bucket(s.distance)}"][key] += 1
        if personnel(sample):
            t.c[f"personnel_shotgun|{personnel(sample)}|{s.down}|{dist_bucket(s.distance)}"][key] += 1
