# START
# Baseline timeout predictor: the real rate at which the offense or the defense calls a timeout before a
# play, by how late in the half it is, whether the clock is running, and who is ahead; and how long a
# running clock ran before the call, by how late it is and who called it. After a timeout, the real rate at
# which the other team calls one too, by how late it is.
# - predict(ctx, called, rng) -> Timeout | None.
# - situation_key(s) -> str: the bucket the rates are counted and sampled by (shared with priors.py).
# - late(s) -> str: how late in the half it is (early, 5:00, 2:00, 1:00).
# A team with no timeouts left can't call one; its share goes to nobody.
# END
from events.timeout import Timeout
from shared.priors import choice, priors_of, rate, wait

load_priors = priors_of(__file__)  # (season, week) -> priors dict


def late(s) -> str:
    left = s.clock + (900 if s.quarter in (1, 3) else 0)  # seconds left in the half (or the overtime period)
    return "early" if left > 300 else "5:00" if left > 120 else "2:00" if left > 60 else "1:00"


def situation_key(s) -> str:
    if s.kind != "scrimmage":
        return "other"
    lead = s.score[s.offense] - s.score[s.defense]
    if s.quarter <= 2:
        half, score = "first", "any"
    else:
        half, score = "second", "any" if late(s) == "early" else "ahead" if lead > 0 else "behind" if lead < 0 else "tied"
    return f"{half}|{late(s)}|{score}|{'running' if s.clock_running else 'stopped'}"


def predict(ctx, called, rng):
    s = ctx.situation
    p = load_priors(ctx.game.season, ctx.game.week)
    if called:
        other = s.defense if called == s.offense else s.offense
        again = p.get("second", {}).get(late(s))
        return Timeout(other) if again and s.timeouts[other] and rng.random() < rate(again, "called") else None
    counts = dict(p["timeout"].get(situation_key(s), {}))
    for side, team in (("offense", s.offense), ("defense", s.defense)):
        if s.timeouts[team] == 0:
            counts["none"] = counts.get("none", 0) + counts.pop(side, 0)
    side = choice(counts, rng) if sum(counts.values()) else "none"
    if side == "none":
        return None
    gaps = p["snap_gap"].get(f"{late(s)}|{side}") if s.clock_running else None
    return Timeout(s.offense if side == "offense" else s.defense, wait(gaps, rng) if gaps else 0.0)
