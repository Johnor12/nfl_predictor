# START
# Trained snap predictor: run or pass from a gradient-boosted model of the situation, the offense's game so
# far, its personnel group, whether it is in the shotgun, and the box. Everything else is the baseline's.
# - predict(ctx, lineups, formation, defense, allowed, rng) -> Snap.
# - pass_rate(ctx, lineups, formation, defense) -> float: the model's probability of a dropback on a
#   scrimmage down (the baseline's on a try, and in a season before the first model).
# inputs.py reads the model's features; train.py trains a model per season from the seasons before it.
# END
from events.snap.predictors import baseline
from events.snap.predictors.gbm.inputs import features
from shared.models import models_of

load_model = models_of(__file__)  # season -> probability(row), or None


def pass_rate(ctx, lineups, formation, defense) -> float:
    model = load_model(ctx.game.season)
    if model is None or ctx.situation.kind != "scrimmage":
        return baseline.pass_rate(ctx, lineups, formation, defense)
    return model(features(ctx, lineups.offense.personnel, not formation.under_center, defense.box))


def predict(ctx, lineups, formation, defense, allowed, rng):
    return baseline.predict(ctx, lineups, formation, defense, allowed, rng, pass_rate)
