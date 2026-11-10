# offensive formation predictors

Implementations of the [offensive formation event](../README.md)'s predictor, one package each. Every package exports `predict(ctx, lineups, rng)`; pick one by name with `play.load_predictors`.

- `baseline/`: a legal alignment for the unit, shotgun or under center by the priors.
