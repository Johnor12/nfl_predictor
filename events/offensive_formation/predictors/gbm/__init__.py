# START
# Trained offensive formation predictor: shotgun or under center from a gradient-boosted model of the
# situation, the offense's game so far, and the personnel group on the field. The alignment is the baseline's.
# - predict(ctx, lineups, rng) -> Formation.
# - shotgun_rate(ctx, lineups) -> float: the model's probability of the shotgun when the offense is out on a
#   scrimmage down (the baseline's for any other unit, on a try, and in a season before the first model).
# inputs.py reads the model's features; train.py trains a model per season from the seasons before it.
# END
from events.offensive_formation.predictors import baseline
from events.offensive_formation.predictors.gbm.inputs import features
from shared.models import models_of

load_model = models_of(__file__)  # season -> probability(row), or None


def shotgun_rate(ctx, lineups) -> float:
    model = load_model(ctx.game.season)
    if model is None or ctx.situation.kind != "scrimmage" or lineups.offense.unit != "offense":
        return baseline.shotgun_rate(ctx, lineups)
    return model(features(ctx, lineups.offense.personnel))


def predict(ctx, lineups, rng):
    return baseline.predict(ctx, lineups, rng, shotgun_rate)
