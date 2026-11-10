# START
# Builds the baseline pre-snap priors from real plays.
# - observe(tally, sample): snaps[n]: scrimmage downs and tries; fouls[type|side]: pre-snap fouls.
# END
from shared.priors import PRESNAP, flag


def observe(t, sample):
    if sample.context.situation.kind in ("scrimmage", "try"):
        t.c["snaps"]["n"] += 1
    foul = flag(sample)
    if foul and foul[0] in PRESNAP:
        t.c["fouls"]["|".join(foul)] += 1
