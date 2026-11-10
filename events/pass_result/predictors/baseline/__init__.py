# START
# Baseline pass result predictor: complete, incomplete, or intercepted by pass depth (goal-to-go inside the 10).
# - predict(ctx, lineups, target, rng) -> PassResult.
# Hand-set: which position groups intercept and defend passes.
# END
from events.pass_result import PassResult
from shared.priors import air_bucket, choice, goal_bucket, pick, priors_of, rate

load_priors = priors_of(__file__)  # season -> priors dict


def predict(ctx, lineups, target, rng):
    p = load_priors(ctx.game.season)
    los = ctx.situation.x
    counts = p["pass_result_goal"][goal_bucket(100 - los)] if los >= 90 else p["pass_result"][air_bucket(target.air_yards)]
    result = choice(counts, rng)
    defenders = lineups.defense.players
    if result == "intercepted":
        return PassResult(result, pick(ctx, defenders, {"DB": 80, "LB": 18, "DL": 2}, rng))
    if result == "incomplete" and rng.random() < rate(p["defended"], "yes"):
        return PassResult(result, pick(ctx, defenders, {"DB": 85, "LB": 13, "DL": 2}, rng))
    return PassResult(result)
