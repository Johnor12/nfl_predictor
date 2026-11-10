# baseline kick result predictor

Return, touchback, or muff by where the kickoff comes down.

API (`from events.kick_result.predictors.baseline import predict`, or `play.load_predictors("baseline")`):

- `predict(ctx, lineups, landing_x, allowed, rng) -> KickResult`

From data: results in the landing zone and the end zone (`kickoff_result`).

Hand-set: the onside recovery rate, the muff rate, and the fair catch rate where fair catches are allowed. The returner is the top kick returner on the field by depth chart.

The priors come from the `priors_<season>.json` for the game's season (the latest earlier one if it has none). Rebuild every event's with `python -m events.baseline_priors 2026`.
