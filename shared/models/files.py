# START
# Model files: model_<season>.txt (LightGBM's text format), stored next to the predictor that uses them. A
# season's model is the one for that season's games, trained on the seasons before it. A predictor with
# several models names each one (`name`: run_<season>.txt, catch_<season>.txt).
# - models_of(file, cuts=None, name="model", limit=None, several=False) -> load(season) -> probability |
#   None: a cached loader for the model files in `file`'s folder. `probability(row)` is the model's answer
#   for one row of features: the probability of yes (a float), each class's probability (a tuple, for a
#   model fitted with classes), or with `cuts` (a model from fit_number) the probability that the number
#   reaches each cut (a tuple that never rises; `limit` is the place in the row of the feature it was
#   fitted with as its limit). With `several`, `probability(rows)` answers a list of rows in one call (a
#   tuple of floats): the candidates of a choice, each a row. A season later than every model gets the
#   latest one; a season earlier than every model gets None.
# - choose(probabilities, rng) -> int: which candidate, drawn in proportion to a `several` model's answers.
# - save_model(model, file, season, name="model") -> Path: writes <name>_<season>.txt in `file`'s folder.
# - draw(reaches, cuts, rng) -> (low, high): a number drawn from a fit_number model's answer, as the cuts it
#   falls between: low <= number < high (None for no bound: below the first cut, or at or above the last).
# Internals: _probability (a model file, read once; it remembers its recent rows' answers).
# END
from functools import lru_cache
from pathlib import Path

import lightgbm
import numpy as np


def models_of(file, cuts=None, name="model", limit=None, several=False):
    folder = Path(file).resolve().parent

    @lru_cache(maxsize=None)
    def load(season: int):
        seasons = [int(path.stem.rsplit("_", 1)[1]) for path in folder.glob(f"{name}_*.txt")]
        trained = [s for s in seasons if s <= season]
        if not trained:
            return None
        return _probability(folder / f"{name}_{max(trained)}.txt", cuts and tuple(cuts), limit, several)

    return load


@lru_cache(maxsize=None)
def _probability(path, cuts=None, limit=None, several=False):
    # read as text, so a file checked out with Windows line endings still loads (LightGBM only takes \n)
    model = lightgbm.Booster(model_str=Path(path).read_text())

    @lru_cache(maxsize=4096)
    def predict_several(rows):
        return tuple(model.predict(np.array(rows, dtype=float), num_threads=1).tolist())

    if several:
        return lambda rows: predict_several(tuple(map(tuple, rows)))

    @lru_cache(maxsize=4096)  # an evaluator asks about the same play many times over
    def predict(row):
        if cuts:  # one row per cut; the answers are made to fall, whatever the trees' rounding does
            room = (lambda cut: ()) if limit is None else (lambda cut: (row[limit] - cut,))
            out = model.predict(np.array([row + (cut,) + room(cut) for cut in cuts], dtype=float), num_threads=1)
            return tuple(np.minimum.accumulate(out).tolist())
        out = model.predict(np.array([row], dtype=float), num_threads=1)[0]
        return float(out) if np.ndim(out) == 0 else tuple(out.tolist())

    return lambda row: predict(tuple(row))


def choose(probabilities, rng) -> int:
    return rng.choices(range(len(probabilities)), probabilities)[0]


def draw(reaches, cuts, rng) -> tuple:
    u = rng.random()
    reached = sum(p > u for p in reaches)
    return cuts[reached - 1] if reached else None, cuts[reached] if reached < len(cuts) else None


def save_model(model, file, season: int, name="model") -> Path:
    path = Path(file).resolve().parent / f"{name}_{season}.txt"
    model.save_model(path)
    return path
