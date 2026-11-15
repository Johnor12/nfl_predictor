# pass rush predictors

Implementations of the [pass rush event](../README.md)'s predictor, one package each. Every package exports `predict(ctx, lineups, formation, defense, rng)`; pick one by name with `play.load_predictors`.

- `baseline/`: the dropback's result (the league's rates, moved toward the quarterback's own sacks and scrambles this season), rushers, sack yardage, and quarterback hits from the priors.
