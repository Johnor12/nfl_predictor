# coin toss predictors

Implementations of the [coin toss event](../README.md)'s predictor, one package each. Every package exports `predict(ctx, rng)`; pick one by name with `coin_toss.load_toss_predictors` or `game.load_game_predictors`.

- `baseline/`: a fair coin.
