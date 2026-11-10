# lineups predictors

Implementations of the [lineups event](../README.md)'s predictor, one package each. Every package exports `predict(ctx, rng)`; pick one by name with `play.load_predictors`.

- `baseline/`: the unit from hand-set rules and 4th-down priors, then 11 players filled from the depth chart.
