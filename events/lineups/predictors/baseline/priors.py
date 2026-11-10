# START
# Builds the baseline lineups priors from real plays.
# - observe(tally, sample): counts one real play (see shared/priors/building.py).
#   unit[down|distance bucket|field bucket]: offense, punt, or field_goal on scrimmage downs (kneels excluded);
#   two_point: attempt or kick on tries.
# END
from shared.priors import dist_bucket, field_bucket


def observe(t, sample):
    s, action = sample.context.situation, sample.actual["action"]
    if action == "no_play":
        return
    if s.kind == "scrimmage" and action != "kneel":
        unit = {"punt": "punt", "field_goal": "field_goal"}.get(action, "offense")
        t.c[f"unit|{s.down}|{dist_bucket(s.distance)}|{field_bucket(s.x)}"][unit] += 1
    if s.kind == "try":
        t.c["two_point"]["attempt" if sample.row.two_point_attempt == 1 else "kick"] += 1
