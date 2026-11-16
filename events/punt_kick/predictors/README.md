# punt kick predictors

Implementations of the [punt kick event](../README.md)'s predictor, one package each. Every package exports `predict(ctx, lineups, punter, rng)`; pick one by name with `play.load_predictors`.

- `baseline/`: block rate and punt distance by field position, from the priors.
- `gbm/`: the punt's distance from a trained model (gradient-boosted trees) of the situation, the weather, and the punter's own average; the rest is the baseline's. Better punt by punt, not the default: whole games scored no better with it (its MAINTAINER.md).
