# timeout predictors

Implementations of the [timeout event](../README.md)'s predictor, one package each. Every package exports `predict(ctx, rng)`; pick one by name with `game.load_game_predictors`.

- `baseline/`: the real rate at which the offense or the defense calls a timeout, by how late in the half it is, whether the clock is running, and who is ahead.
