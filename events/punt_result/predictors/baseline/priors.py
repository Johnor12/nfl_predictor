# START
# Builds the baseline punt result priors from real plays.
# - observe(tally, sample): punt_result[inside_10|inside_20|open]: fair_catch, return, downed, out_of_bounds,
#   or muff, for unblocked punts that came down in the field of play.
# END
from shared.priors import present


def observe(t, sample):
    s, row = sample.context.situation, sample.row
    if s.kind == "try" or sample.actual["action"] != "punt" or row.punt_blocked == 1 or not present(row.kick_distance):
        return
    land = s.x + row.kick_distance
    if land >= 100:
        return
    bucket = "inside_10" if land >= 90 else "inside_20" if land >= 80 else "open"
    result = ("fair_catch" if row.punt_fair_catch == 1 else "downed" if row.punt_downed == 1
              else "out_of_bounds" if row.punt_out_of_bounds == 1 else "touchback" if row.touchback == 1
              else "muff" if row.fumble == 1 and row.return_yards == 0 else "return")
    if result != "touchback":
        t.c[f"punt_result|{bucket}"][result] += 1
