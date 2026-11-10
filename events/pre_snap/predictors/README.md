# pre snap predictors

Implementations of the [pre snap event](../README.md)'s predictor, one package each. Every package exports `predict(ctx, lineups, formation, allowed_fouls, rng)`; pick one by name with `play.load_predictors`.

- `baseline/`: play clock used by game script, and pre-snap fouls at the real rate.
