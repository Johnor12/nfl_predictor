# START
# Builds the baseline loose ball priors from real plays.
# - observe(tally, sample): fumble_recovery: lost or kept, for fumbles on runs and dropbacks.
# END


def observe(t, sample):
    row = sample.row
    if sample.context.situation.kind == "try":
        return
    if row.fumble == 1 and sample.actual["action"] in ("run", "scramble", "pass", "sack"):
        t.c["fumble_recovery"]["lost" if row.fumble_lost == 1 else "kept"] += 1
