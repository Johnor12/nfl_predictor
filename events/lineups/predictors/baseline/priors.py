# START
# Builds the baseline lineups priors from real plays.
# - observe(tally, sample): counts one real play (see shared/priors/building.py).
#   unit[down|distance bucket|field bucket]: offense, punt, or field_goal on scrimmage downs (kneels excluded;
#   a fake is the kicking unit's);
#   two_point: attempt or kick on tries.
#   From who was on the field, in seasons whose data records it:
#   personnel[script|down|distance bucket] and personnel[try]: the offense's personnel group on runs and dropbacks;
#   package[personnel group]: the defense's package against it.
# END
from shared.priors import dist_bucket, field_bucket, package, personnel, script, sent_out


def observe(t, sample):
    s, action = sample.context.situation, sample.actual["action"]
    if action == "no_play":
        return
    unit = sent_out(sample) if s.kind == "scrimmage" else "offense"
    if s.kind == "scrimmage" and unit != "victory":
        t.c[f"unit|{s.down}|{dist_bucket(s.distance)}|{field_bucket(s.x)}"][unit] += 1
    if s.kind == "try":
        t.c["two_point"]["attempt" if sample.row.two_point_attempt == 1 else "kick"] += 1
    group = personnel(sample) if action in ("run", "scramble", "pass", "sack") and unit == "offense" else None
    if group:
        key = "try" if s.kind == "try" else f"{script(s)}|{s.down}|{dist_bucket(s.distance)}"
        t.c[f"personnel|{key}"][group] += 1
        if package(sample):
            t.c[f"package|{group}"][package(sample)] += 1
