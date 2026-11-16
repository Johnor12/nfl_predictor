# START
# Trains the fourth-down models from real plays.
# - train(season) -> Path: the model for `season`'s games, fitted to every earlier season's real plays and
#   written as model_<season>.txt next to this file.
# - example(sample) -> row | None: a real fourth down as the model's features (inputs.py) and the unit the
#   offense sent out, as its place in UNITS. Kneels, and plays a penalty wiped out, are left out.
# - TABLES: the training table: its name -> (example, the row's names: the features, then "unit").
# - CLI: `python -m events.lineups.predictors.gbm.train 2026`, or `2021-2026` for a range (the default: the
#   six most recent seasons).
# The model's settings are shared.models' defaults but for the rounds (ROUNDS: more of them scored worse on
# the seasons before the evaluated ones), with the team's inputs read coarsely.
# END
from events.lineups.predictors.gbm.inputs import NAMES, UNITS, WHO, features
from events.training import table, train_cli
from shared.models import fit, save_model
from shared.nflverse import SEASONS

TABLE = "lineups_gbm"
ROUNDS = 100  # chosen on 2019 and 2020, with models trained on 2011 to 2018
COLUMNS = NAMES + ("unit",)
SENT_OUT = {"punt": "punt", "field_goal": "field_goal", "run": "offense", "pass": "offense", "sack": "offense",
            "scramble": "offense", "spike": "offense"}  # a real play's action -> the unit behind it


def example(sample):
    s, unit = sample.context.situation, SENT_OUT.get(sample.actual["action"])
    if s.kind != "scrimmage" or s.down != 4 or not unit:
        return None
    return features(sample.context) + [UNITS.index(unit)]


def train(season: int):
    examples = table(TABLE, [s for s in SEASONS if s < season], example, COLUMNS)
    return save_model(fit(examples, NAMES, "unit", classes=len(UNITS), coarse=WHO, rounds=ROUNDS), __file__, season)


TABLES = {TABLE: (example, COLUMNS)}

if __name__ == "__main__":
    train_cli(TABLES, train)
