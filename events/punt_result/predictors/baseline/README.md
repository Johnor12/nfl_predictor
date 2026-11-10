# baseline punt result predictor

Fair catch, return, downed, out of bounds, or muff by where the punt lands.

API (`from events.punt_result.predictors.baseline import predict`, or `play.load_predictors("baseline")`):

- `predict(ctx, lineups, landing_x, allowed, rng) -> PuntResult`

From data: results by landing spot (`punt_result`: inside the 10, inside the 20, open field).

Hand-set: nothing; the returner is the top punt returner on the field by depth chart.

The priors come from the `priors_<season>.json` for the game's season (the latest earlier one if it has none). Rebuild every event's with `python -m events.baseline_priors 2026`.
