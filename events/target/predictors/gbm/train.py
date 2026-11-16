# START
# Trains the air yards models from real plays.
# - train(season) -> Path: the model for `season`'s games, fitted to every earlier season's real plays and
#   written as model_<season>.txt next to this file.
# - example(sample) -> row | None: a real pass thrown to a receiver on a scrimmage down as the model's
#   features (inputs.py) and its air yards.
# - TABLES: the training table: its name -> (example, the row's names: the features, then "air_yards").
# - CLI: `python -m events.target.predictors.gbm.train 2026`, or `2021-2026` for a range (the default: the six
#   most recent seasons).
# The model's settings are shared.models' defaults.
# END
from events.target.predictors.gbm.inputs import CUTS, LIMIT, NAMES, features
from events.training import table, train_cli
from shared.models import fit_number, save_model
from shared.nflverse import SEASONS
from shared.priors import present

TABLE = "target_gbm"
COLUMNS = NAMES + ("air_yards",)


def example(sample):
    row, ctx = sample.row, sample.context
    receiver = ctx.by_id.get(row.receiver_player_id)
    if ctx.situation.kind != "scrimmage" or sample.actual["action"] != "pass" or not receiver or not present(row.air_yards):
        return None
    return features(ctx, receiver, row.shotgun == 1) + [row.air_yards]


def train(season: int):
    examples = table(TABLE, [s for s in SEASONS if s < season], example, COLUMNS)
    return save_model(fit_number(examples, NAMES, "air_yards", CUTS, limit=LIMIT), __file__, season)


TABLES = {TABLE: (example, COLUMNS)}

if __name__ == "__main__":
    train_cli(TABLES, train)
