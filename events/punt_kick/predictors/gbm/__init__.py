# START
# Trained punt kick predictor: how far the punt goes, from a gradient-boosted model of the situation, the
# weather, and the punter's own history. Blocks and the hang time are the baseline's.
# - predict(ctx, lineups, punter, rng) -> PuntKick.
# - distance(ctx, punter, rng) -> float: one draw from the model's distribution on a scrimmage down (the
#   baseline's on a safety kick, and in a season before the first model). The model says which of its CUTS
#   the punt falls between, and the baseline's histogram where between them; between two cuts with the goal
#   line in between, that is a touchback as often as the histogram has a punt that long or longer.
# inputs.py reads the model's features; train.py trains a model per season from the seasons before it.
# END
from events.punt_kick.predictors import baseline
from events.punt_kick.predictors.gbm.inputs import CUTS, LIMIT, NAMES, features
from shared.models import draw, models_of
from shared.priors import hist

load_model = models_of(__file__, CUTS, limit=NAMES.index(LIMIT))  # season -> probability(row), or None


def distance(ctx, punter, rng) -> float:
    model = load_model(ctx.game.season)
    if model is None or ctx.situation.kind != "scrimmage":
        return baseline.distance(ctx, punter, rng)
    low, high = draw(model(features(ctx, ctx.by_id[punter])), CUTS, rng)
    if high is not None and high > 100 - ctx.situation.x:
        high = None  # a punt into the end zone is recorded at the goal line: every longer punt is in there too
    return hist(baseline.histogram(ctx), rng, low, high)


def predict(ctx, lineups, punter, rng):
    return baseline.predict(ctx, lineups, punter, rng, distance)
