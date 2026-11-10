# defensive formation predictors

Implementations of the [defensive formation event](../README.md)'s predictor, one package each. Every package exports `predict(ctx, lineups, formation, rng)`; pick one by name with `play.load_predictors`.

- `baseline/`: box count from the priors; deep safeties hand-set.
