# START
# Training a model from a table of examples.
# - fit(table, features, label, weight=None, rounds=ROUNDS, **params) -> model: gradient-boosted trees
#   (LightGBM) for a yes/no label. `table` is a DataFrame with a column per feature (nan where unknown) and
#   the label; `weight` an optional weight per row. PARAMS are the defaults; a predictor passes its own.
# END
import lightgbm

PARAMS = {"objective": "binary", "learning_rate": 0.1, "num_leaves": 31, "min_data_in_leaf": 200,
          "verbose": -1, "seed": 0, "deterministic": True, "force_row_wise": True}
ROUNDS = 150


def fit(table, features, label, weight=None, rounds=ROUNDS, **params):
    data = lightgbm.Dataset(table[list(features)], table[label], weight=weight)
    return lightgbm.train({**PARAMS, **params}, data, rounds)
