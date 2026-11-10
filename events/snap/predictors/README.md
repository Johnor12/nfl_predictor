# snap predictors

Implementations of the [snap event](../README.md)'s predictor, one package each. Every package exports `predict(ctx, lineups, formation, defense, allowed_actions, rng)`; pick one by name with `play.load_predictors`.

- `baseline/`: run or pass by game script, down, and distance; the ball carrier by depth chart role.
