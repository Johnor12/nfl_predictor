# pass result predictors

Implementations of the [pass result event](../README.md)'s predictor, one package each. Every package exports `predict(ctx, lineups, target, rng)`; pick one by name with `play.load_predictors`.

- `baseline/`: complete, incomplete, or intercepted by pass depth.
