# START
# Baseline target predictor: the receiver by depth chart role, air yards and direction from the priors.
# - predict(ctx, lineups, formation, eligible, rng) -> Target.
# Inside the 10 the air yards come from goal-to-go histograms, resampled to stay inside the end line.
# END
from events.target import Target
from shared.priors import choice, goal_bucket, hist, priors_of, role

load_priors = priors_of(__file__)  # season -> priors dict


def predict(ctx, lineups, formation, eligible, rng):
    p = load_priors(ctx.game.season)
    weights = [p["target"].get(role(ctx.by_id[pid]), 5) for pid in eligible]
    receiver = rng.choices(eligible, weights)[0]
    los = ctx.situation.x
    air_yards = p["air_yards_goal"][goal_bucket(100 - los)] if los >= 90 else p["air_yards"]
    for _ in range(20):  # keep the pass inside the end line, since the field compresses near the goal
        air = hist(air_yards, rng)
        if los + air <= 108:
            break
    return Target(receiver, min(air, 108 - los), choice(p["direction"], rng))
