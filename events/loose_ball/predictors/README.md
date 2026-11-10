# loose ball predictors

Implementations of the [loose ball event](../README.md)'s predictor, one package each. Every package exports `predict(ctx, lineups, cause, x, last_team, rng)`; pick one by name with `play.load_predictors`.

- `baseline/`: who recovers, near the spot of the ball.
