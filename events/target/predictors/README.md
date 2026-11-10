# target predictors

Implementations of the [target event](../README.md)'s predictor, one package each. Every package exports `predict(ctx, lineups, formation, eligible, rng)`; pick one by name with `play.load_predictors`.

- `baseline/`: the receiver by depth chart role; air yards and direction from the priors.
