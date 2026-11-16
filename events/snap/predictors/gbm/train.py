# START
# Trains the run-or-pass models from real plays.
# - train(season) -> Path: the model for `season`'s games, fitted to every earlier season's real plays and
#   written as model_<season>.txt next to this file.
# - example(sample) -> row | None: a real run or dropback on a scrimmage down as the model's features
#   (inputs.py) and whether the offense dropped back. The personnel group and the box are nan in the
#   seasons whose data doesn't record them.
# - TABLES: the training table: its name -> (example, the row's names: the features, then "pass").
# - CLI: `python -m events.snap.predictors.gbm.train 2026`, or `2021-2026` for a range (the default: the six
#   most recent seasons).
# The model's settings are shared.models' defaults: on 2019 and 2020, with models trained on 2011 to 2018,
# nothing tried beat them by more than 0.2%.
# END
import math

from events.situation import DROPBACKS, SNAPS
from events.snap.predictors.gbm.inputs import NAMES, features
from events.training import table, train_cli
from shared.models import fit, save_model
from shared.nflverse import SEASONS
from shared.priors import personnel

TABLE = "snap_gbm"
COLUMNS = NAMES + ("pass",)


def example(sample):
    action, charting = sample.actual["action"], sample.charting
    if sample.context.situation.kind != "scrimmage" or action not in SNAPS:
        return None
    box = charting.n_defense_box if charting is not None and charting.n_defense_box > 0 else math.nan
    return features(sample.context, personnel(sample), sample.row.shotgun == 1, box) + [action in DROPBACKS]


def train(season: int):
    examples = table(TABLE, [s for s in SEASONS if s < season], example, COLUMNS)
    return save_model(fit(examples, NAMES, "pass"), __file__, season)


TABLES = {TABLE: (example, COLUMNS)}

if __name__ == "__main__":
    train_cli(TABLES, train)
