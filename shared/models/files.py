# START
# Model files: model_<season>.txt (LightGBM's text format), stored next to the predictor that uses them. A
# season's model is the one for that season's games, trained on the seasons before it.
# - models_of(file) -> load(season) -> probability | None: a cached loader for the model files in `file`'s
#   folder. `probability(row) -> float` is the model's probability of yes for one row of features. A season
#   later than every model gets the latest one; a season earlier than every model gets None.
# - save_model(model, file, season) -> Path: writes model_<season>.txt in `file`'s folder.
# Internals: _probability (a model file, read once; it remembers its recent rows' answers).
# END
from functools import lru_cache
from pathlib import Path

import lightgbm
import numpy as np


def models_of(file):
    folder = Path(file).resolve().parent

    @lru_cache(maxsize=None)
    def load(season: int):
        seasons = [int(path.stem.split("_")[1]) for path in folder.glob("model_*.txt")]
        trained = [s for s in seasons if s <= season]
        if not trained:
            return None
        return _probability(folder / f"model_{max(trained)}.txt")

    return load


@lru_cache(maxsize=None)
def _probability(path):
    model = lightgbm.Booster(model_file=path)
    predict = lru_cache(maxsize=4096)(lambda row: float(model.predict(np.array([row], dtype=float), num_threads=1)[0]))
    return lambda row: predict(tuple(row))  # an evaluator asks about the same play many times over


def save_model(model, file, season: int) -> Path:
    path = Path(file).resolve().parent / f"model_{season}.txt"
    model.save_model(path)
    return path
