# START
# Baseline carry predictor: yards from a histogram for the kind of carry, how it ended, and tacklers by group.
# - predict(ctx, lineups, kind, carrier, yard_line, rng) -> CarryEnd.
# Goal to go (inside the 10) uses separate, compressed histograms where the priors have them.
# A run or a catch ends in a lateral at the real rate, to a back, receiver, or tight end on the field.
# Hand-set: kneels, fumble recovery returns (RECOVERY_YARDS), how returns without data end (RETURN_ENDS),
# slides on scrambles, forced fumble credit, who takes a lateral, and the carry's duration.
# END
from events.carry import CarryEnd
from shared.priors import choice, goal_bucket, group, hist, on_field, pick, pick_many, priors_of, rate

load_priors = priors_of(__file__)  # season -> priors dict
RECOVERY_YARDS = {"0": 70, "2": 10, "5": 8, "10": 5, "20": 4, "40": 2, "70": 1}
RETURN_ENDS = {"tackled": 93, "out_of_bounds": 6, "fumble": 1}
LATERAL_TO = {"RB": 3, "WR": 2, "TE": 1}


def predict(ctx, lineups, kind, carrier, yard_line, rng):
    if kind == "kneel":
        return CarryEnd(-1.0 if yard_line > 2 else 0.0, "down", seconds=1.0)
    p = load_priors(ctx.game.season)
    goal = p.get(f"{kind}_goal", {}).get(goal_bucket(100 - yard_line)) if yard_line >= 90 else None
    yards = hist(RECOVERY_YARDS if kind == "recovery" else goal or p[kind], rng)
    how = choice(p["carry_end"].get(kind, RETURN_ENDS), rng)
    if kind == "scramble" and how == "tackled" and rng.random() < 0.3:
        how = "down"  # slide
    team = ctx.by_id[carrier].team
    seconds = 2.0 + abs(yards) / 7 + rng.uniform(0, 1.5)
    takers = [pid for pid in on_field(ctx, lineups, team) if pid != carrier and group(ctx.by_id[pid]) in LATERAL_TO]
    if how == "tackled" and takers and rng.random() < rate(p.get("lateral", {}).get(kind, {}), "yes"):
        return CarryEnd(yards, "lateral", seconds=seconds, lateral_to=pick(ctx, takers, LATERAL_TO, rng))
    opponents = lineups.defense.players if team == ctx.situation.offense else lineups.offense.players
    tacklers = ()
    if how in ("tackled", "fumble") or (how == "out_of_bounds" and rng.random() < 0.5):
        weights = p["tackler"]["kick" if kind in ("punt_return", "kick_return") else "scrimmage"]
        n = 2 if rng.random() < rate(p["assisted"], "yes") else 1
        tacklers = pick_many(ctx, opponents, weights, n, rng)
    forced = tacklers[0] if how == "fumble" and tacklers and rng.random() < 0.7 else None
    return CarryEnd(yards, how, tacklers, forced, seconds)
