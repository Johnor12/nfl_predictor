# START
# Baseline timeout predictor: the real rate at which the offense or the defense calls a timeout before a
# play, by how late in the half it is, whether the clock is running, and who is ahead.
# - predict(ctx, rng) -> str | None.
# - situation_key(s) -> str: the bucket the priors are counted and sampled by (shared with priors.py).
# A team with no timeouts left can't call one; its share goes to nobody.
# END
from shared.priors import choice, priors_of

load_priors = priors_of(__file__)  # (season, week) -> priors dict


def situation_key(s) -> str:
    if s.kind != "scrimmage":
        return "other"
    left = s.clock + (900 if s.quarter in (1, 3) else 0)  # seconds left in the half (or the overtime period)
    late = "early" if left > 300 else "5:00" if left > 120 else "2:00" if left > 60 else "1:00"
    lead = s.score[s.offense] - s.score[s.defense]
    if s.quarter <= 2:
        half, score = "first", "any"
    else:
        half, score = "second", "any" if late == "early" else "ahead" if lead > 0 else "behind" if lead < 0 else "tied"
    return f"{half}|{late}|{score}|{'running' if s.clock_running else 'stopped'}"


def predict(ctx, rng):
    s = ctx.situation
    counts = dict(load_priors(ctx.game.season, ctx.game.week)["timeout"].get(situation_key(s), {}))
    for side, team in (("offense", s.offense), ("defense", s.defense)):
        if s.timeouts[team] == 0:
            counts["none"] = counts.get("none", 0) + counts.pop(side, 0)
    if not sum(counts.values()):
        return None
    return {"offense": s.offense, "defense": s.defense, "none": None}[choice(counts, rng)]
