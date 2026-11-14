# baseline punt kick predictor

Block rate and punt distance by field position, from the priors.

API (`from events.punt_kick.predictors.baseline import predict`, or `play.load_predictors("baseline")`):

- `predict(ctx, lineups, punter, rng) -> PuntKick`

From data: the block rate (`punt_blocked`) and gross distance by field position (`punt_distance`).

Hand-set: who blocks punts, and hang time.

The priors come from the `priors_<season>.json` files next to the code: each key from the latest season that has it and isn't after the game's (see `shared/priors/README.md`). Rebuild every event's with `python -m events.baseline_priors 2026`.
