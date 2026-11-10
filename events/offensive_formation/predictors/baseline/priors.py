# START
# Builds the baseline offensive formation priors from real plays.
# - observe(tally, sample): shotgun[down|distance bucket]: shotgun or under_center on runs and dropbacks.
# END
from shared.priors import dist_bucket


def observe(t, sample):
    s = sample.context.situation
    if s.kind == "scrimmage" and sample.actual["action"] in ("run", "scramble", "pass", "sack"):
        key = "shotgun" if sample.row.shotgun == 1 else "under_center"
        t.c[f"shotgun|{s.down}|{dist_bucket(s.distance)}"][key] += 1
