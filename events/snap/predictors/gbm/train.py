# START
# Trains the run-or-pass models from real plays.
# - train(season) -> Path: the model for `season`'s games, fitted to every earlier season's real plays and
#   written as model_<season>.txt next to this file.
# - example(sample) -> row | None: a real run or dropback on a scrimmage down as the model's features
#   (inputs.py) and whether the offense dropped back.
# - COLUMNS: the row's names: the features, then "pass".
# - CLI: `python -m events.snap.predictors.gbm.train 2026`, or `2021-2026` for a range (the default: the six
#   most recent seasons).
# The model's settings are shared.models' defaults: on 2019 and 2020, with models trained on 2011 to 2018,
# nothing tried beat them by more than 0.2%.
# END
import sys

from events.snap.predictors.gbm.inputs import DROPBACKS, NAMES, SNAPS, features
from events.training import table
from shared.models import fit, save_model
from shared.nflverse import SEASONS

COLUMNS = NAMES + ("pass",)


def example(sample):
    action = sample.actual["action"]
    if sample.context.situation.kind != "scrimmage" or action not in SNAPS:
        return None
    return features(sample.context) + [action in DROPBACKS]


def train(season: int):
    examples = table("snap_gbm", [s for s in SEASONS if s < season], example, COLUMNS)
    return save_model(fit(examples, NAMES, "pass"), __file__, season)


if __name__ == "__main__":
    first, _, last = (sys.argv[1] if len(sys.argv) > 1 else f"{SEASONS[-6]}-{SEASONS[-1]}").partition("-")
    seasons = range(int(first), int(last or first) + 1)
    table("snap_gbm", [s for s in SEASONS if s < seasons[-1]], example, COLUMNS)  # every season's rows, built together
    for season in seasons:
        print(train(season).name)
