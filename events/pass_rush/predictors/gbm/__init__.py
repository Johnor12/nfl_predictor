# START
# Trained pass rush predictor: throw, sack, or scramble from a gradient-boosted model of the situation, the
# formation, and the quarterback's own history. Everything else about the dropback is the baseline's.
# - predict(ctx, lineups, formation, defense, rng) -> PassRush.
# - dropback(ctx, formation, league) -> {"throw": p, "sack": p, "scramble": p}: the model's probabilities on a
#   scrimmage down (the baseline's on a try, and in a season before the first model).
# inputs.py reads the model's features; train.py trains a model per season from the seasons before it.
# END
from events.pass_rush.predictors import baseline
from events.pass_rush.predictors.gbm.inputs import RESULTS, features
from shared.models import models_of

load_model = models_of(__file__)  # season -> probability(row), or None


def dropback(ctx, formation, league) -> dict:
    model = load_model(ctx.game.season)
    if model is None or ctx.situation.kind != "scrimmage":
        return baseline.dropback(ctx, formation, league)
    return dict(zip(RESULTS, model(features(ctx, ctx.by_id.get(formation.qb), not formation.under_center))))


def predict(ctx, lineups, formation, defense, rng):
    return baseline.predict(ctx, lineups, formation, defense, rng, dropback)
