# carry predictors

Implementations of the [carry event](../README.md)'s predictor, one package each. Every package exports `predict(ctx, lineups, kind, carrier, yard_line, rng)`; pick one by name with `play.load_predictors`. The default (`DEFAULT` in `__init__.py`) is `gbm`.

- `baseline/`: yards from a histogram for the kind of carry (runs by the carrier's position group, catches by pass depth and the receiver's), how it ended, and tacklers by position group.
- `gbm/`: the yards of a designed run and the yards after a catch from trained models (gradient-boosted trees) of the situation and the carrier's own history; the rest is the baseline's.
