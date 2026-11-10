# START
# Builds the baseline free kick priors from real plays.
# - observe(tally, sample): kickoff_oob: yes or no; kickoff_distance: histogram for kickoffs kept in bounds.
# END


def observe(t, sample):
    row = sample.row
    if sample.actual["action"] != "kickoff" or sample.context.situation.kind != "kickoff":
        return
    out_of_bounds = row.kickoff_out_of_bounds == 1 or row.penalty_type == "Kickoff Out of Bounds"
    t.c["kickoff_oob"]["yes" if out_of_bounds else "no"] += 1
    if not out_of_bounds:
        t.hist["kickoff_distance"].append(row.kick_distance)
