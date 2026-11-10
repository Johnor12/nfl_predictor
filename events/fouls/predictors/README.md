# fouls predictors

Implementations of the [fouls event](../README.md)'s predictor, one package each. Every package exports `predict(ctx, lineups, record, allowed_fouls, rng)`; pick one by name with `play.load_predictors`.

- `baseline/`: at most one foul per play, at the real rate for the kind of play.
