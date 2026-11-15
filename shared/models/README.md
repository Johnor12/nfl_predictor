# models

The toolkit behind the trained predictors: machine learning models fitted to real plays. Each trained predictor keeps its own model files next to its code; this package is what they share.

API (`from shared.models import ...`):

- `models_of(file) -> load(season) -> probability | None`: a cached loader for the `model_<season>.txt` files next to `file`. A season's model is the one for that season's games, trained on the seasons before it, so a game is always predicted by a model that has never seen its season. `probability(row) -> float` is the model's probability of yes for one row of features (a list of numbers in the order the model was trained with; `nan` where a value is unknown). A season later than every model gets the latest model; a season earlier than every model gets `None`, and the predictor falls back.
- `fit(table, features, label, weight=None, rounds=150, **params) -> model`: gradient-boosted trees (LightGBM) for a yes/no label. `table` is a DataFrame with a column per feature and the label; `weight` is an optional weight per row; `params` override LightGBM's settings (`shared.models.training.PARAMS`).
- `save_model(model, file, season) -> Path`: writes `model_<season>.txt` next to `file`.

A training table comes from `events.training.table`, which turns every real play into a row with a predictor's own `example` function.

Only yes/no outputs so far. A model with more classes, or a number, needs another objective in `fit` and another reader next to `probability`.
