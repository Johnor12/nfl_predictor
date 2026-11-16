# START
# Trains the pass result models from real plays.
# - train(season) -> Path: the model for `season`'s games, fitted to every earlier season's real plays and
#   written as model_<season>.txt next to this file.
# - example(sample) -> row | None: a real pass thrown to a receiver on a scrimmage down as the model's
#   features (inputs.py) and its result's place in RESULTS.
# - TABLES: the training table: its name -> (example, the row's names: the features, then "result").
# - CLI: `python -m events.pass_result.predictors.gbm.train 2026`, or `2021-2026` for a range (the default:
#   the six most recent seasons).
# The model's settings are shared.models' defaults but for the rounds (ROUNDS: more of them scored worse on
# the seasons before the evaluated ones), with the quarterback's and the defense's inputs read coarsely.
# END
from events.pass_result.predictors.gbm.inputs import NAMES, RESULTS, WHO, features
from events.training import table, train_cli
from shared.models import fit, save_model
from shared.nflverse import SEASONS
from shared.priors import present

TABLE = "pass_result_gbm"
ROUNDS = 40  # chosen on 2019 and 2020, with models trained on 2011 to 2018
COLUMNS = NAMES + ("result",)


def example(sample):
    row, ctx = sample.row, sample.context
    if (ctx.situation.kind != "scrimmage" or sample.actual["action"] != "pass" or not present(row.receiver_player_id)
            or not present(row.air_yards)):
        return None
    result = "intercepted" if row.interception == 1 else "complete" if row.complete_pass == 1 else "incomplete"
    qb, receiver = ctx.by_id.get(row.passer_player_id), ctx.by_id.get(row.receiver_player_id)
    return features(ctx, qb, receiver, row.air_yards) + [RESULTS.index(result)]


def train(season: int):
    examples = table(TABLE, [s for s in SEASONS if s < season], example, COLUMNS)
    return save_model(fit(examples, NAMES, "result", classes=len(RESULTS), coarse=WHO, rounds=ROUNDS), __file__, season)


TABLES = {TABLE: (example, COLUMNS)}

if __name__ == "__main__":
    train_cli(TABLES, train)
