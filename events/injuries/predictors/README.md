# injuries predictors

Implementations of the [injuries event](../README.md)'s predictor, one package each. Every package exports `predict(ctx, lineups, record, rng)`; pick one by name with `play.load_predictors`.

- `baseline/`: at most one injury per play, at the real rate.
