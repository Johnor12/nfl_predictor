# START
# Trained receiver choice: who is thrown to, from a gradient-boosted model of each eligible back, receiver,
# and tight end (his own targets, next to the others'). How far downfield is the gbm predictor's model; the
# direction is the baseline's.
# - predict(ctx, lineups, formation, eligible, rng) -> Target.
# - receiver(ctx, formation, eligible, rng) -> str: one of the eligible players, in proportion to the model's
#   probability for each (the baseline's choice on a try, in a season before the first model, and when no
#   back, receiver, or tight end is eligible).
# inputs.py reads the model's features; train.py trains a model per season from the seasons before it.
# END
from events.target.predictors import baseline, gbm
from events.target.predictors.gbm_receiver.inputs import RECEIVERS, candidates
from shared.models import choose, models_of

load_model = models_of(__file__, several=True)  # season -> probability(rows), or None


def receiver(ctx, formation, eligible, rng) -> str:
    model = load_model(ctx.game.season)
    players = [ctx.by_id[pid] for pid in eligible if ctx.by_id[pid].position in RECEIVERS]
    if model is None or ctx.situation.kind != "scrimmage" or not players:
        return baseline.receiver(ctx, formation, eligible, rng)
    return players[choose(model(candidates(ctx, players, not formation.under_center)), rng)].id


def predict(ctx, lineups, formation, eligible, rng):
    return baseline.predict(ctx, lineups, formation, eligible, rng, gbm.air_yards, receiver)
