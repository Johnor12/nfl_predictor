# kick attempt predictors

Implementations of the [kick attempt event](../README.md)'s predictor, one package each. Every package exports `predict(ctx, lineups, kicker, distance, rng)`; pick one by name with `play.load_predictors`.

- `baseline/`: field goals by distance bin and extra points, from the priors.
