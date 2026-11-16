# START
# Baseline pass result predictor: complete, incomplete, or intercepted by pass depth (goal-to-go inside the 10).
# - predict(ctx, lineups, target, rng, results=results) -> PassResult. Another implementation can hand in its
#   own `results` and keep the rest (events/pass_result/predictors/gbm).
# - results(ctx, lineups, target) -> {"complete": weight, "incomplete": weight, "intercepted": weight}.
# Who defends or intercepts it: by position group, and each defender's own passes defended per snap
# (shared.priors.COVERAGE). What a charter adds, at the charted rates: the defender in coverage (the one who
# defended it, else by position group and how often he has been thrown at), and whether an incompletion
# was a drop (if nobody defended it) or a bad throw.
# Hand-set: how long the ball is in the air (with the time to throw it, an incompletion takes the 5 seconds
# a real one does).
# END
from events.pass_result import PassResult
from shared.priors import COVERAGE, TARGETED, air_bucket, choice, goal_bucket, pick, priors_of, rate, some

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
    defender = None
    if result == "intercepted" or (result == "incomplete" and rng.random() < rate(p["defended"], "yes")):
        defender = pick(ctx, defenders, p["defender"][result], rng, own=COVERAGE)
    coverage = (defender,) if defender else some(ctx, defenders, rng, p.get("covered"), None, p.get("coverage"), TARGETED)
    drop = bad = False
    if result == "incomplete" and "drop" in p:  # the priors count both per incompletion; a defended pass isn't a drop
        drop = not defender and rng.random() < rate(p["drop"], "yes") / (1 - rate(p["defended"], "yes"))
        bad = not drop and rng.random() < rate(p["bad_throw"], "yes")
    return PassResult(result, defender, seconds, coverage[0] if coverage else None, drop, bad)
