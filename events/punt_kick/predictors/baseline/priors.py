# START
# Builds the baseline punt kick priors from real plays.
# - observe(tally, sample): punt_blocked: yes or no; punt_distance[field bucket]: histogram of gross yards.
# END
from shared.priors import field_bucket


def observe(t, sample):
    s, row = sample.context.situation, sample.row
    if s.kind == "try" or sample.actual["action"] != "punt":
        return
    blocked = row.punt_blocked == 1
    t.c["punt_blocked"]["yes" if blocked else "no"] += 1
    if not blocked:
        t.hist[f"punt_distance|{field_bucket(s.x)}"].append(row.kick_distance)
