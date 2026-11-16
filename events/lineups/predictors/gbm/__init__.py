# START
# Trained lineups predictor: the fourth-down decision (go for it, punt, or kick) from a gradient-boosted model
# of the situation and the team's own history. Everything else about the lineups (the hand-set rules, the
# personnel, the players) is the baseline's.
# - predict(ctx, rng) -> Lineups.
# - units(ctx) -> {"offense": p, "punt": p, "field_goal": p}: the model's probabilities on fourth down (the
#   baseline's on any other down, and in a season before the first model).
# inputs.py reads the model's features; train.py trains a model per season from the seasons before it.
# END
from events.lineups.predictors import baseline
from events.lineups.predictors.gbm.inputs import UNITS, features
from shared.models import models_of

load_model = models_of(__file__)  # season -> probability(row), or None


def units(ctx) -> dict:
    model = load_model(ctx.game.season)
    if model is None or ctx.situation.down != 4:
        return baseline.units(ctx)
    return dict(zip(UNITS, model(features(ctx))))


def predict(ctx, rng):
    return baseline.predict(ctx, rng, units)
