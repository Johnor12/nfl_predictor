# free kick predictors

Implementations of the [free kick event](../README.md)'s predictor, one package each. Every package exports `predict(ctx, lineups, onside, rng)`; pick one by name with `play.load_predictors`.

- `baseline/`: kickoff distance and out-of-bounds rate from the priors.
