# START
# Trains the dropback models from real plays.
# - train(season) -> Path: the model for `season`'s games, fitted to every earlier season's real plays and
#   written as model_<season>.txt next to this file.
# - example(sample) -> row | None: a real dropback on a scrimmage down as the model's features (inputs.py)
#   and its result's place in RESULTS (a throwaway is a throw: the data can't tell them apart before 2022).
# - TABLES: the training table: its name -> (example, the row's names: the features, then "result").
# - CLI: `python -m events.pass_rush.predictors.gbm.train 2026`, or `2021-2026` for a range (the default: the
#   six most recent seasons).
# The model's settings are shared.models' defaults but for the rounds (ROUNDS: more of them scored worse on
# the seasons before the evaluated ones), with the quarterback's inputs read coarsely and
# the home input favored (FAVOR, shared.models: who is at home moves every play of a game by a little).
# END
from events.pass_rush.predictors.gbm.inputs import NAMES, RESULTS, WHO, features
from events.situation import DROPBACKS
from events.training import table, train_cli
from shared.models import fit, save_model
from shared.nflverse import SEASONS
from shared.priors import present

TABLE = "pass_rush_gbm"
ROUNDS = 40  # chosen on 2019 and 2020, with models trained on 2011 to 2018
FAVOR = ("home",)
COLUMNS = NAMES + ("result",)


def example(sample):
    action, row, ctx = sample.actual["action"], sample.row, sample.context
    if ctx.situation.kind != "scrimmage" or action not in DROPBACKS:
        return None
    qb = row.passer_player_id if present(row.passer_player_id) else row.rusher_player_id  # a scrambler ran
    return features(ctx, ctx.by_id.get(qb), row.shotgun == 1) + [RESULTS.index("throw" if action == "pass" else action)]


def train(season: int):
    examples = table(TABLE, [s for s in SEASONS if s < season], example, COLUMNS)
    model = fit(examples, NAMES, "result", classes=len(RESULTS), coarse=WHO, favor=FAVOR, rounds=ROUNDS)
    return save_model(model, __file__, season)


TABLES = {TABLE: (example, COLUMNS)}

if __name__ == "__main__":
    train_cli(TABLES, train)
