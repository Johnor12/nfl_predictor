# offensive formation predictors

Implementations of the [offensive formation event](../README.md)'s predictor, one package each. Every package exports `predict(ctx, lineups, rng)`; pick one by name with `play.load_predictors`. The default (`DEFAULT` in `__init__.py`) is `gbm`.

- `baseline/`: a legal alignment for the unit, shotgun or under center by the priors.
- `gbm/`: shotgun or under center from a trained model (gradient-boosted trees) of the situation, the offense's game so far, and its personnel group; the alignment is the baseline's.
