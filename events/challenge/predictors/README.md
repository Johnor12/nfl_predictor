# challenge predictors

Implementations of the [challenge event](../README.md)'s predictor, one package each. Every package exports `predict(ctx, outcome, allowed, rng)`; pick one by name with `game.load_game_predictors`.

- `baseline/`: the real rate at which the offense or the defense challenges a play and wins or loses, by the kind of play and how it came out.
