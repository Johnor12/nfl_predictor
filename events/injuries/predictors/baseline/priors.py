# START
# Builds the baseline injuries priors from real plays.
# - observe(tally, sample): injury: plays, and how many of them mention an injured player.
# END


def observe(t, sample):
    if sample.actual["action"] == "no_play":
        return
    if "injured" in str(sample.row.desc):
        t.c["injury"]["injured"] += 1
    t.c["injury"]["plays"] += 1
