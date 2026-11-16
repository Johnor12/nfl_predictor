# START
# Trains the punt distance models from real plays.
# - train(season) -> Path: the model for `season`'s games, fitted to every earlier season's real punts and
#   written as model_<season>.txt next to this file.
# - example(sample) -> row | None: a real punt that wasn't blocked, on a scrimmage down, as the model's
#   features (inputs.py) and its distance.
# - TABLES: the training table: its name -> (example, the row's names: the features, then "punt_yards").
# - CLI: `python -m events.punt_kick.predictors.gbm.train 2026`, or `2021-2026` for a range (the default: the
#   six most recent seasons).
# The model's settings are shared.models' defaults, with the weather and the punter's inputs read coarsely.
# END
from events.punt_kick.predictors.gbm.inputs import CUTS, LIMIT, NAMES, WHO, features
from events.training import table, train_cli
from shared.models import fit_number, save_model
from shared.nflverse import SEASONS
from shared.priors import present

TABLE = "punt_kick_gbm"
COLUMNS = NAMES + ("punt_yards",)


def example(sample):
    row, ctx = sample.row, sample.context
    punter = ctx.by_id.get(row.punter_player_id)
    if (ctx.situation.kind != "scrimmage" or sample.actual["action"] != "punt" or row.punt_blocked == 1 or not punter
            or not present(row.kick_distance)):
        return None
    return features(ctx, punter) + [row.kick_distance]


def train(season: int):
    examples = table(TABLE, [s for s in SEASONS if s < season], example, COLUMNS)
    return save_model(fit_number(examples, NAMES, "punt_yards", CUTS, coarse=WHO, limit=LIMIT), __file__, season)


TABLES = {TABLE: (example, COLUMNS)}

if __name__ == "__main__":
    train_cli(TABLES, train)
