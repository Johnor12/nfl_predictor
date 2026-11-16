# START
# Trained target predictor: how far downfield the pass is thrown, from a gradient-boosted model of the
# situation, the formation, and the receiver's own history. Who is thrown to and the direction are the
# baseline's.
# - predict(ctx, lineups, formation, eligible, rng) -> Target.
# - air_yards(ctx, formation, receiver, rng) -> float: one draw from the model's distribution on a scrimmage
#   down (the baseline's on a try, and in a season before the first model). The model says which of its
#   CUTS the pass falls between; where they are more than a yard apart, the baseline's histogram says where.
# inputs.py reads the model's features; train.py trains a model per season from the seasons before it.
# END
from events.target.predictors import baseline
from events.target.predictors.gbm.inputs import CUTS, LIMIT, NAMES, features
from shared.models import draw, models_of
from shared.priors import hist

load_model = models_of(__file__, CUTS, limit=NAMES.index(LIMIT))  # season -> probability(row), or None


def air_yards(ctx, formation, receiver, rng) -> float:
    model = load_model(ctx.game.season)
    if model is None or ctx.situation.kind != "scrimmage":
        return baseline.air_yards(ctx, formation, receiver, rng)
    reaches = model(features(ctx, ctx.by_id[receiver], not formation.under_center))
    return hist(baseline.histogram(ctx, receiver), rng, *draw(reaches, CUTS, rng))


def predict(ctx, lineups, formation, eligible, rng):
    return baseline.predict(ctx, lineups, formation, eligible, rng, air_yards)
