# snap predictors

Implementations of the [snap event](../README.md)'s predictor, one package each. Every package exports `predict(ctx, lineups, formation, defense, allowed_actions, rng)`; pick one by name with `play.load_predictors`. The default (`DEFAULT` in `__init__.py`) is `gbm`.

- `baseline/`: run or pass by game script, down, and distance; the ball carrier by depth chart role and his own carries this season.
- `gbm/`: run or pass from a trained model (gradient-boosted trees) of the situation and the offense's game so far; the rest is the baseline's.
