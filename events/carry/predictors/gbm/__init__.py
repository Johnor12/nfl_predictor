# START
# Trained carry predictor: the yards of a designed run and the yards after a catch, each from a
# gradient-boosted model of the situation and the carrier's own history. Every other kind of carry, how a
# carry ends, and the tacklers are the baseline's.
# - predict(ctx, lineups, kind, carrier, yard_line, rng) -> CarryEnd.
# - yards(ctx, kind, carrier, yard_line, rng) -> float: one draw from the kind's model on a scrimmage down
#   (the baseline's for another kind, on a try, and in a season before the first model). The model says
#   which of its cuts the carry falls between; where they are more than a yard apart, the baseline's
#   histogram says where. Between two cuts with the goal line in between, that is a touchdown as often as
#   the histogram has a gain that long or longer.
# inputs.py reads the models' features; train.py trains both per season from the seasons before it.
# END
from events.carry.predictors import baseline
from events.carry.predictors.gbm.inputs import CATCH, CATCH_CUTS, CATCH_LIMIT, RUN, RUN_CUTS, RUN_LIMIT, catch, run
from shared.models import draw, models_of
from shared.priors import hist

load_run = models_of(__file__, RUN_CUTS, "run", RUN.index(RUN_LIMIT))  # season -> probability(row), or None
load_catch = models_of(__file__, CATCH_CUTS, "catch", CATCH.index(CATCH_LIMIT))


def yards(ctx, kind, carrier, yard_line, rng) -> float:
    load = {"run": load_run, "catch": load_catch}.get(kind) if ctx.situation.kind == "scrimmage" else None
    model = load and load(ctx.game.season)
    if not model:
        return baseline.yards(ctx, kind, carrier, yard_line, rng)
    player = ctx.by_id[carrier]
    row, cuts = (run(ctx, player), RUN_CUTS) if kind == "run" else (catch(ctx, player, yard_line), CATCH_CUTS)
    low, high = draw(model(row), cuts, rng)
    if high is not None and high > 100 - yard_line:
        high = None  # real carries stop at the goal line: the cuts that hold it hold every longer gain too
    return hist(baseline.histogram(ctx, kind, carrier, yard_line), rng, low, high)


def predict(ctx, lineups, kind, carrier, yard_line, rng):
    return baseline.predict(ctx, lineups, kind, carrier, yard_line, rng, yards)
