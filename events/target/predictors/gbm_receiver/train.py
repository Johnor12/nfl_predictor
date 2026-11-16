# START
# Trains the receiver models from real plays.
# - train(season) -> Path | None: the model for `season`'s games, fitted to every earlier season's real
#   plays and written as model_<season>.txt next to this file (None if no earlier season records who was
#   on the field).
# - example(sample) -> rows | None: a real pass thrown to a receiver on a scrimmage down, as a row per back,
#   receiver, and tight end on the field for it: the model's features (inputs.py) and whether he was the one
#   thrown to. Only in a season that records who was on the field (2016 on).
# - TABLES: the training table: its name -> (example, the row's names: the features, then "targeted").
# - CLI: `python -m events.target.predictors.gbm_receiver.train 2026`, or `2021-2026` for a range (the
#   default: the six most recent seasons).
# The model's leaves are larger than shared.models' default (LEAF): a player's rates are the same in every
# row of his game.
# END
from events.target.predictors.gbm_receiver.inputs import NAMES, RECEIVERS, candidates
from events.training import table, train_cli
from shared.models import fit, save_model
from shared.nflverse import SEASONS
from shared.priors import played

TABLE = "target_gbm_receiver"
COLUMNS = NAMES + ("targeted",)
LEAF = 1000


def example(sample):
    row, ctx, on_field = sample.row, sample.context, played(sample)
    if ctx.situation.kind != "scrimmage" or sample.actual["action"] != "pass" or not on_field:
        return None
    players = [ctx.by_id[pid] for pid in on_field[0] if pid in ctx.by_id and ctx.by_id[pid].position in RECEIVERS]
    if row.receiver_player_id not in [player.id for player in players]:
        return None
    rows = candidates(ctx, players, row.shotgun == 1)
    return [features + [player.id == row.receiver_player_id] for player, features in zip(players, rows)]


def train(season: int):
    examples = table(TABLE, [s for s in SEASONS if s < season], example, COLUMNS)
    if not len(examples):
        return None
    return save_model(fit(examples, NAMES, "targeted", min_data_in_leaf=LEAF), __file__, season)


TABLES = {TABLE: (example, COLUMNS)}

if __name__ == "__main__":
    train_cli(TABLES, train)
