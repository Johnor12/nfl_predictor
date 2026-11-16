# pass result predictors

Implementations of the [pass result event](../README.md)'s predictor, one package each. Every package exports `predict(ctx, lineups, target, rng)`; pick one by name with `play.load_predictors`. The default (`DEFAULT` in `__init__.py`) is `gbm`.

- `baseline/`: complete, incomplete, or intercepted by pass depth.
- `gbm/`: complete, incomplete, or intercepted from a trained model (gradient-boosted trees) of the situation, the throw, the quarterback's history, and the defense's; the rest is the baseline's.
