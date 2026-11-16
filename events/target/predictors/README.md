# target predictors

Implementations of the [target event](../README.md)'s predictor, one package each. Every package exports `predict(ctx, lineups, formation, eligible, rng)`; pick one by name with `play.load_predictors`. The default (`DEFAULT` in `__init__.py`) is `gbm`.

- `baseline/`: the receiver by depth chart role and his own targets this season; air yards by his position group; direction from the priors.
- `gbm/`: the air yards from a trained model (gradient-boosted trees) of the situation, the formation, and how deep the receiver has been thrown to; the rest is the baseline's.
- `gbm_receiver/`: who is thrown to from a trained model as well, asked about each eligible player (his own targets, next to the others'), on top of `gbm`. It scores no better than the baseline's choice in whole games, so it isn't the default.
