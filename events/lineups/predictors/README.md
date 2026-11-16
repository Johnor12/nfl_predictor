# lineups predictors

Implementations of the [lineups event](../README.md)'s predictor, one package each. Every package exports `predict(ctx, rng)`; pick one by name with `play.load_predictors`. The default (`DEFAULT` in `__init__.py`) is `gbm`.

- `baseline/`: the unit from hand-set rules and 4th-down priors, the personnel group and the defense's package from the priors, then 11 players who have been playing in the unit (by depth chart where there are no snaps to go on).
- `gbm/`: the fourth-down decision from a trained model (gradient-boosted trees) of the situation and how often the team has gone for it; the rest is the baseline's.
