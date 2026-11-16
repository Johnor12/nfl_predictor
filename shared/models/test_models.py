# START
# Tests of the models toolkit (no network needed).
# - test_a_fitted_model_predicts: fit learns a simple rule, and predicts it for one row.
# - test_several_rows_at_once: a model asked about several candidates answers each as it would alone, and
#   choose draws one in proportion.
# - test_models_of_picks_the_season: a season gets the latest model trained for it or for an earlier season,
#   None before the first, and a file is only read once.
# - test_a_model_of_classes_predicts_each: fit with classes gives each class's probability.
# - test_a_model_of_a_number_predicts_its_distribution: fit_number's answer falls with the cut, and draw
#   samples from it.
# - test_a_number_s_model_knows_its_limit: with a limit, the model puts everything that would go past it on it.
# - test_a_coarse_feature_is_read_in_steps: a feature named in `coarse` only splits at a few values.
# END
import math
import random

import pandas as pd

from shared.models import choose, draw, fit, fit_number, models_of, save_model


def _model():
    rng = random.Random(0)
    rows = [(x, math.nan if rng.random() < 0.1 else rng.random(), x > 0.5) for x in (rng.random() for _ in range(4000))]
    return fit(pd.DataFrame(rows, columns=["x", "noise", "yes"]), ["x", "noise"], "yes", rounds=20, min_data_in_leaf=20)


def test_a_fitted_model_predicts(tmp_path):
    save_model(_model(), tmp_path / "predictor.py", 2024)
    probability = models_of(tmp_path / "predictor.py")(2024)
    assert probability([0.9, 0.5]) > 0.9 > 0.1 > probability([0.1, math.nan])


def test_several_rows_at_once(tmp_path):
    save_model(_model(), tmp_path / "predictor.py", 2024)
    one, several = models_of(tmp_path / "predictor.py")(2024), models_of(tmp_path / "predictor.py", several=True)(2024)
    rows = [[0.9, 0.5], [0.1, math.nan], [0.6, 0.2]]
    assert several(rows) == tuple(one(row) for row in rows)
    rng = random.Random(0)
    chosen = [choose(several(rows), rng) for _ in range(500)]
    assert chosen.count(0) > 5 * chosen.count(1) and set(chosen) <= {0, 1, 2}


def test_models_of_picks_the_season(tmp_path):
    model = _model()
    for season in (2022, 2024):
        save_model(model, tmp_path / "predictor.py", season)
    load = models_of(tmp_path / "predictor.py")
    assert load(2021) is None
    assert load(2022) is load(2023) is not load(2024)
    assert load(2024) is load(2030)


def test_a_model_of_classes_predicts_each(tmp_path):
    rng = random.Random(0)
    rows = [(x, int(3 * x)) for x in (rng.random() for _ in range(4000))]
    model = fit(pd.DataFrame(rows, columns=["x", "third"]), ["x"], "third", rounds=20, min_data_in_leaf=20, classes=3)
    save_model(model, tmp_path / "predictor.py", 2024)
    low, middle, high = models_of(tmp_path / "predictor.py")(2024)([0.5])
    assert middle > 0.9 and abs(low + middle + high - 1) < 1e-6


def test_a_model_of_a_number_predicts_its_distribution(tmp_path):
    rng = random.Random(0)
    rows = [(x, 10 * x + rng.gauss(0, 1)) for x in (rng.random() for _ in range(4000))]
    cuts = [2, 4, 6, 8]
    model = fit_number(pd.DataFrame(rows, columns=["x", "y"]), ["x"], "y", cuts, rounds=40, min_data_in_leaf=20)
    save_model(model, tmp_path / "predictor.py", 2024)
    reaches = models_of(tmp_path / "predictor.py", cuts)(2024)([0.5])  # y is about 5 here
    assert reaches[0] > 0.95 and reaches[1] > 0.7 and reaches[2] < 0.3 and reaches[3] < 0.05
    assert list(reaches) == sorted(reaches, reverse=True)
    draws = [draw(reaches, cuts, random.Random(seed)) for seed in range(200)]
    assert 0.5 < sum(d == (4, 6) for d in draws) / 200 < 0.8  # between 4 and 6 about 65% of the time
    assert draw((0.0,) * 4, cuts, random.Random(0)) == (None, 2) and draw((1.0,) * 4, cuts, random.Random(0)) == (8, None)


def test_a_number_s_model_knows_its_limit(tmp_path):
    rng = random.Random(0)
    rows = [(limit, min(limit, rng.randint(0, 9))) for limit in (rng.randint(1, 9) for _ in range(6000))]
    cuts = list(range(1, 10))
    model = fit_number(pd.DataFrame(rows, columns=["limit", "y"]), ["limit"], "y", cuts, rounds=60, min_data_in_leaf=20,
                       limit="limit")
    save_model(model, tmp_path / "predictor.py", 2024)
    reaches = models_of(tmp_path / "predictor.py", cuts, limit=0)(2024)([4])  # y stops at 4
    assert abs(reaches[3] - 0.6) < 0.06 and reaches[4] < 0.03  # it gets to 4 six times in ten, and never past


def test_a_coarse_feature_is_read_in_steps(tmp_path):
    rng = random.Random(0)
    rows = [(x, x > 0.5) for x in (rng.random() for _ in range(4000))]
    table = pd.DataFrame(rows, columns=["x", "yes"])
    exact = fit(table, ["x"], "yes", rounds=20, min_data_in_leaf=20)
    coarse = fit(table, ["x"], "yes", rounds=20, min_data_in_leaf=20, coarse=["x"])
    thresholds = lambda model: set(model.trees_to_dataframe().threshold.dropna().round(6))  # noqa: E731
    assert len(thresholds(coarse)) <= 7 < len(thresholds(exact))
