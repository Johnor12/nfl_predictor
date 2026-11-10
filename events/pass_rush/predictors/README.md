# pass rush predictors

Implementations of the [pass rush event](../README.md)'s predictor, one package each. Every package exports `predict(ctx, lineups, formation, defense, rng)`; pick one by name with `play.load_predictors`.

- `baseline/`: the dropback's result, rushers, sack yardage, and quarterback hits from the priors.
