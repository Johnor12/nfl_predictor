# START
# Tests of the models toolkit (no network needed).
# - test_a_fitted_model_predicts: fit learns a simple rule, and predicts it for one row.
# - test_models_of_picks_the_season: a season gets the latest model trained for it or for an earlier season,
#   None before the first, and a file is only read once.
# END
import math
import random

import pandas as pd

from shared.models import fit, models_of, save_model


def _model():
    rng = random.Random(0)
    rows = [(x, math.nan if rng.random() < 0.1 else rng.random(), x > 0.5) for x in (rng.random() for _ in range(4000))]
    return fit(pd.DataFrame(rows, columns=["x", "noise", "yes"]), ["x", "noise"], "yes", rounds=20, min_data_in_leaf=20)


def test_a_fitted_model_predicts(tmp_path):
    save_model(_model(), tmp_path / "predictor.py", 2024)
    probability = models_of(tmp_path / "predictor.py")(2024)
    assert probability([0.9, 0.5]) > 0.9 > 0.1 > probability([0.1, math.nan])


def test_models_of_picks_the_season(tmp_path):
    model = _model()
    for season in (2022, 2024):
        save_model(model, tmp_path / "predictor.py", season)
    load = models_of(tmp_path / "predictor.py")
    assert load(2021) is None
    assert load(2022) is load(2023) is not load(2024)
    assert load(2024) is load(2030)
