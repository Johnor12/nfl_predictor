# START
# Baseline target predictor: the receiver by how often each eligible player is thrown to when he is on the
# field (by depth chart role, and his own targets this season), air yards by his position group, and the
# direction from the priors.
# - predict(ctx, lineups, formation, eligible, rng, air_yards=air_yards, receiver=receiver) -> Target. Another
#   implementation can hand in its own `air_yards` or `receiver` and keep the rest
#   (events/target/predictors/gbm).
# - receiver(ctx, formation, eligible, rng) -> str: who is thrown to.
# - air_yards(ctx, formation, receiver, rng) -> float: one draw of how far downfield the pass is thrown.
# - histogram(ctx, receiver) -> {"yards": count}: the air yards of passes to the receiver's position group
#   (goal-to-go histograms inside the 10).
# The air yards are drawn again (up to 20 times) until the pass stays inside the end line.
# END
from events.target import Target
from shared.priors import choice, goal_bucket, group, hist, priors_of, usage

load_priors = priors_of(__file__)  # (season, week) -> priors dict


def histogram(ctx, receiver) -> dict:
    p, los = load_priors(ctx.game.season, ctx.game.week), ctx.situation.x
    by_group = p["air_yards"]
    return (p["air_yards_goal"][goal_bucket(100 - los)] if los >= 90
            else by_group.get(group(ctx.by_id[receiver])) or by_group["WR"])


def air_yards(ctx, formation, receiver, rng) -> float:
    return hist(histogram(ctx, receiver), rng)


def receiver(ctx, formation, eligible, rng) -> str:
    p = load_priors(ctx.game.season, ctx.game.week)
    weights = [usage(ctx.by_id[pid], "targets", "targeted", p["target_rate"], p["targets_per_snap"]) or 0.001
               for pid in eligible]
    return rng.choices(eligible, weights)[0]


def predict(ctx, lineups, formation, eligible, rng, air_yards=air_yards, receiver=receiver):
    p = load_priors(ctx.game.season, ctx.game.week)
    receiver = receiver(ctx, formation, eligible, rng)
    los = ctx.situation.x
    for _ in range(20):  # keep the pass inside the end line, since the field compresses near the goal
        air = air_yards(ctx, formation, receiver, rng)
        if los + air <= 108:
            break
    return Target(receiver, min(air, 108 - los), choice(p["direction"], rng))
