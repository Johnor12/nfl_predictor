# baseline free kick predictor

Kickoff distance and out-of-bounds rate from the priors.

API (`from events.free_kick.predictors.baseline import predict`, or `play.load_predictors("baseline")`):

- `predict(ctx, lineups, onside, rng) -> FreeKick`

From data: kickoff distance (`kickoff_distance`) and the out-of-bounds rate (`kickoff_oob`).

Hand-set: onside kicks travel 10-15 yards, and hang time. The kicker is the K (else the P) on the field.

The priors come from the `priors_<season>.json` for the game's season (the latest earlier one if it has none). Rebuild every event's with `python -m events.baseline_priors 2026`.
