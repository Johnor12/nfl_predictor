# punt kick predictors

Implementations of the [punt kick event](../README.md)'s predictor, one package each. Every package exports `predict(ctx, lineups, punter, rng)`; pick one by name with `play.load_predictors`.

- `baseline/`: block rate and punt distance by field position, from the priors.
