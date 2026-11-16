# START
# Trains the shotgun models from real plays.
# - train(season) -> Path: the model for `season`'s games, fitted to every earlier season's real plays and
#   written as model_<season>.txt next to this file.
# - example(sample) -> row | None: a real run or dropback on a scrimmage down as the model's features
#   (inputs.py) and whether the offense was in the shotgun.
# - TABLES: the training table: its name -> (example, the row's names: the features, then "shotgun").
# - CLI: `python -m events.offensive_formation.predictors.gbm.train 2026`, or `2021-2026` for a range (the
#   default: the six most recent seasons).
# The model's settings are shared.models' defaults, with the team's inputs read coarsely.
# END
from events.offensive_formation.predictors.gbm.inputs import NAMES, WHO, features
from events.situation import SNAPS
from events.training import table, train_cli
from shared.models import fit, save_model
from shared.nflverse import SEASONS
from shared.priors import personnel

TABLE = "offensive_formation_gbm"
COLUMNS = NAMES + ("shotgun",)


def example(sample):
    if sample.context.situation.kind != "scrimmage" or sample.actual["action"] not in SNAPS:
        return None
    return features(sample.context, personnel(sample)) + [sample.row.shotgun == 1]


def train(season: int):
    examples = table(TABLE, [s for s in SEASONS if s < season], example, COLUMNS)
    return save_model(fit(examples, NAMES, "shotgun", coarse=WHO), __file__, season)


TABLES = {TABLE: (example, COLUMNS)}

if __name__ == "__main__":
    train_cli(TABLES, train)
