# punt result predictors

Implementations of the [punt result event](../README.md)'s predictor, one package each. Every package exports `predict(ctx, lineups, landing_x, allowed, rng)`; pick one by name with `play.load_predictors`.

- `baseline/`: fair catch, return, downed, out of bounds, or muff by where the punt lands.
