# START
# Trained pass result predictor: complete, incomplete, or intercepted from a gradient-boosted model of the
# situation, the throw, the quarterback's history, and the defense's. Who defends or intercepts the pass and
# how long it is in the air are the baseline's.
# - predict(ctx, lineups, target, rng) -> PassResult.
# - results(ctx, lineups, target) -> {"complete": p, "incomplete": p, "intercepted": p}: the model's
#   probabilities on a scrimmage down (the baseline's on a try, and in a season before the first model).
# inputs.py reads the model's features; train.py trains a model per season from the seasons before it.
# END
from events import strength
from events.pass_result.predictors import baseline
from events.pass_result.predictors.gbm.inputs import RESULTS, features
from shared.models import models_of

load_model = models_of(__file__)  # season -> probability(row), or None


def results(ctx, lineups, target) -> dict:
    model = load_model(ctx.game.season)
    if model is None or ctx.situation.kind != "scrimmage":
        return baseline.results(ctx, lineups, target)
    qb, receiver = strength.quarterback(ctx, lineups), ctx.by_id.get(target.receiver)
    return dict(zip(RESULTS, model(features(ctx, qb, receiver, target.air_yards))))


def predict(ctx, lineups, target, rng):
    return baseline.predict(ctx, lineups, target, rng, results)
