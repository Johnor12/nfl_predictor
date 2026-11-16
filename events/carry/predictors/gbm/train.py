# START
# Trains the yards models from real plays.
# - train(season) -> [Path, Path]: the models for `season`'s games, fitted to every earlier season's real
#   plays and written as run_<season>.txt and catch_<season>.txt next to this file.
# - run_example(sample) / catch_example(sample) -> row | None: a real designed run, or a real completion, on
#   a scrimmage down as its model's features (inputs.py) and the yards gained (after the catch).
# - TABLES: the training tables: name -> (example, the row's names: the features, then "yards").
# - CLI: `python -m events.carry.predictors.gbm.train 2026`, or `2021-2026` for a range (the default: the six
#   most recent seasons).
# The models' settings are shared.models' defaults, with the carrier's and the team's inputs read coarsely.
# END
from events.carry.predictors.gbm.inputs import (CATCH, CATCH_CUTS, CATCH_LIMIT, CATCH_WHO, RUN, RUN_CUTS, RUN_LIMIT,
                                                RUN_WHO, catch, run)
from events.training import table, train_cli
from shared.models import fit_number, save_model
from shared.nflverse import SEASONS
from shared.priors import present


def run_example(sample):
    row, ctx = sample.row, sample.context
    carrier = ctx.by_id.get(row.rusher_player_id)
    if ctx.situation.kind != "scrimmage" or sample.actual["action"] != "run" or not carrier or not present(row.yards_gained):
        return None
    return run(ctx, carrier) + [row.yards_gained]


def catch_example(sample):
    row, ctx = sample.row, sample.context
    receiver = ctx.by_id.get(row.receiver_player_id)
    if (ctx.situation.kind != "scrimmage" or sample.actual["action"] != "pass" or row.complete_pass != 1 or not receiver
            or not present(row.air_yards) or not present(row.yards_after_catch)):
        return None
    yard_line = ctx.situation.x + row.air_yards
    return catch(ctx, receiver, yard_line) + [row.yards_after_catch] if 0 < yard_line < 100 else None


TABLES = {"carry_run_gbm": (run_example, RUN + ("yards",)), "carry_catch_gbm": (catch_example, CATCH + ("yards",))}
MODELS = {"run": ("carry_run_gbm", RUN, RUN_CUTS, RUN_WHO, RUN_LIMIT),
          "catch": ("carry_catch_gbm", CATCH, CATCH_CUTS, CATCH_WHO, CATCH_LIMIT)}


def train(season: int):
    paths = []
    for name, (name_of_table, names, cuts, who, limit) in MODELS.items():
        examples = table(name_of_table, [s for s in SEASONS if s < season], *TABLES[name_of_table])
        model = fit_number(examples, names, "yards", cuts, coarse=who, limit=limit)
        paths.append(save_model(model, __file__, season, name))
    return paths


if __name__ == "__main__":
    train_cli(TABLES, train)
