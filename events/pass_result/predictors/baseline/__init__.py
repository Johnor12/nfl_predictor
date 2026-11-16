# START
# Baseline pass result predictor: complete, incomplete, or intercepted by pass depth (goal-to-go inside the 10).
# - predict(ctx, lineups, target, rng, results=results) -> PassResult. Another implementation can hand in its
#   own `results` and keep the rest (events/pass_result/predictors/gbm).
# - results(ctx, lineups, target) -> {"complete": weight, "incomplete": weight, "intercepted": weight}.
# Hand-set: which position groups intercept and defend passes, and how long the ball is in the air (with the
# time to throw it, an incompletion takes the 5 seconds a real one does).
# END
from events.pass_result import PassResult
from shared.priors import air_bucket, choice, goal_bucket, pick, priors_of, rate

load_priors = priors_of(__file__)  # (season, week) -> priors dict


def results(ctx, lineups, target) -> dict:
    p = load_priors(ctx.game.season, ctx.game.week)
    los = ctx.situation.x
    return p["pass_result_goal"][goal_bucket(100 - los)] if los >= 90 else p["pass_result"][air_bucket(target.air_yards)]


def predict(ctx, lineups, target, rng, results=results):
    p = load_priors(ctx.game.season, ctx.game.week)
    result = choice(results(ctx, lineups, target), rng)
    defenders = lineups.defense.players
    seconds = 1.2 + abs(target.air_yards) / 20 + rng.uniform(0, 1)
    if result == "intercepted":
        return PassResult(result, pick(ctx, defenders, {"DB": 80, "LB": 18, "DL": 2}, rng), seconds)
    if result == "incomplete" and rng.random() < rate(p["defended"], "yes"):
        return PassResult(result, pick(ctx, defenders, {"DB": 85, "LB": 13, "DL": 2}, rng), seconds)
    return PassResult(result, seconds=seconds)
