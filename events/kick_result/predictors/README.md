# kick result predictors

Implementations of the [kick result event](../README.md)'s predictor, one package each. Every package exports `predict(ctx, lineups, landing_x, allowed, rng)`; pick one by name with `play.load_predictors`.

- `baseline/`: return, touchback, or muff by where the kickoff comes down.
