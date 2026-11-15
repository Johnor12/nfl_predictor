# START
# Baseline target predictor: the receiver by how often each eligible player is thrown to when he is on the
# field (by depth chart role, and his own targets this season), air yards by his position group, and the
# direction from the priors.
# - predict(ctx, lineups, formation, eligible, rng) -> Target.
# Inside the 10 the air yards come from goal-to-go histograms, resampled to stay inside the end line.
# END
from events.target import Target
from shared.priors import choice, goal_bucket, group, hist, priors_of, usage

load_priors = priors_of(__file__)  # (season, week) -> priors dict


def predict(ctx, lineups, formation, eligible, rng):
    p = load_priors(ctx.game.season, ctx.game.week)
    weights = [usage(ctx.by_id[pid], "targets", "targeted", p["target_rate"], p["targets_per_snap"]) or 0.001
               for pid in eligible]
    receiver = rng.choices(eligible, weights)[0]
    los = ctx.situation.x
    by_group = p["air_yards"]
    air_yards = (p["air_yards_goal"][goal_bucket(100 - los)] if los >= 90
                 else by_group.get(group(ctx.by_id[receiver])) or by_group["WR"])
    for _ in range(20):  # keep the pass inside the end line, since the field compresses near the goal
        air = hist(air_yards, rng)
        if los + air <= 108:
            break
    return Target(receiver, min(air, 108 - los), choice(p["direction"], rng))
