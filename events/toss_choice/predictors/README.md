# toss choice predictors

Implementations of the [toss choice event](../README.md)'s predictor, one package each. Every package exports `predict(ctx, winner, allowed, rng)`; pick one by name with `coin_toss.load_toss_predictors` or `game.load_game_predictors`.

- `baseline/`: hand-set rates: defer the opening toss, and in overtime take the ball unless both teams are guaranteed a possession.
