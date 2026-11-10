# START
# Builds the baseline defensive formation priors from real plays.
# - observe(tally, sample): box[down|distance bucket]: histogram of charted defenders in the box.
# END
from shared.priors import dist_bucket


def observe(t, sample):
    s, f = sample.context.situation, sample.charting
    if s.kind == "scrimmage" and sample.actual["action"] in ("run", "scramble", "pass", "sack"):
        if f is not None and f.n_defense_box > 0:
            t.hist[f"box|{s.down}|{dist_bucket(s.distance)}"].append(f.n_defense_box)
