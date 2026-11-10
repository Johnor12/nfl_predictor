# carry predictors

Implementations of the [carry event](../README.md)'s predictor, one package each. Every package exports `predict(ctx, lineups, kind, carrier, yard_line, rng)`; pick one by name with `play.load_predictors`.

- `baseline/`: yards from a histogram for the kind of carry, how it ended, and tacklers by position group.
