# START
# Training a model from a table of examples.
# - fit(table, features, label, weight=None, rounds=ROUNDS, classes=None, coarse=(), favor=(), **params) -> model:
#   gradient-boosted trees (LightGBM) for a yes/no label, or with `classes` for a label that is one of that
#   many classes (0, 1, ...). `table` is a DataFrame with a column per feature (nan where unknown) and the
#   label; `weight` an optional weight per row. PARAMS are the defaults; a predictor passes its own.
# - fit_number(table, features, label, cuts, rounds=ROUNDS, coarse=(), limit=None, favor=(), **params) -> model: the
#   distribution of a number (yards), as one yes/no model of "the label reaches this cut": the table
#   repeated once per cut, with the cut as one more feature (CUT) that the model can only fall with. `limit`
#   names a feature the number runs up against (the yards to the goal line): how far the cut is from it is
#   then a feature too (ROOM), so the model can tell a cut at the goal line from one short of it. Read with
#   models_of(file, cuts, limit=the feature's place in the row).
# - `coarse`: the features the model may only read in COARSE steps: the ones that say who is playing (a
#   team's or a player's past rate). Read exactly, such a number picks out one team's season among the
#   training plays, and the model learns that season instead of what the rate says (MAINTAINER.md).
# - `favor`: the features whose splits count FAVOR times when a tree chooses one. An input that is the same on
#   every play of a team's game (who is at home) moves one play by too little for a tree to split on it, and
#   over a game it adds up: without this the models gave the home team a third of its real edge (MAINTAINER.md).
# Internals: _settings (LightGBM's bins and split weight per feature).
# END
import lightgbm
import numpy as np

PARAMS = {"objective": "binary", "learning_rate": 0.1, "num_leaves": 31, "min_data_in_leaf": 200,
          "verbose": -1, "seed": 0, "deterministic": True, "force_row_wise": True}
ROUNDS = 150
CUT, ROOM = "cut", "room"  # the last features of a number's model: the cut, and the limit minus the cut
COARSE = 8   # the steps a coarse feature is read in, each holding an equal share of the training plays
FAVOR = 3.0  # what a favored feature's splits count for


def _settings(features, coarse, favor) -> dict:
    steps = {"max_bin_by_feature": [COARSE if name in coarse else 255 for name in features]} if coarse else {}
    weight = {"feature_contri": [FAVOR if name in favor else 1.0 for name in features]} if favor else {}
    return {**steps, **weight}


def fit(table, features, label, weight=None, rounds=ROUNDS, classes=None, coarse=(), favor=(), **params):
    if classes:
        params = {"objective": "multiclass", "num_class": classes, **params}
    data = lightgbm.Dataset(table[list(features)], table[label], weight=weight)
    return lightgbm.train({**PARAMS, **_settings(features, coarse, favor), **params}, data, rounds)


def fit_number(table, features, label, cuts, rounds=ROUNDS, coarse=(), limit=None, favor=(), **params):
    rows, cuts = len(table), np.asarray(cuts, dtype=np.float32)
    inputs = np.repeat(table[list(features)].to_numpy(np.float32), len(cuts), axis=0)
    cut = np.tile(cuts, rows)
    reached = np.repeat(table[label].to_numpy(), len(cuts)) >= cut
    columns, names = [inputs, cut], list(features) + [CUT]
    falling = [0] * len(features) + [-1]  # reaching a higher cut is never more likely
    if limit:
        columns, names, falling = columns + [inputs[:, names.index(limit)] - cut], names + [ROOM], falling + [0]
    data = lightgbm.Dataset(np.column_stack(columns), reached, feature_name=names)
    settings = {**PARAMS, "monotone_constraints": falling, **_settings(names, coarse, favor), **params}
    return lightgbm.train(settings, data, rounds)
