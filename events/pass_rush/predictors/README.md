# pass rush predictors

Implementations of the [pass rush event](../README.md)'s predictor, one package each. Every package exports `predict(ctx, lineups, formation, defense, rng)`; pick one by name with `play.load_predictors`. The default (`DEFAULT` in `__init__.py`) is `gbm`.

- `baseline/`: the dropback's result (the league's rates, moved toward the quarterback's own sacks and scrambles this season), rushers, sack yardage, and quarterback hits from the priors.
- `gbm/`: throw, sack, or scramble from a trained model (gradient-boosted trees) of the situation, the formation, and the quarterback's own history; the rest is the baseline's.
