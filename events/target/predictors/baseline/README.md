# baseline target predictor

The receiver by depth chart role; air yards and direction from the priors.

API (`from events.target.predictors.baseline import predict`, or `play.load_predictors("baseline")`):

- `predict(ctx, lineups, formation, eligible, rng) -> Target`

From data: target share by role (`target`), air yards (`air_yards`, and `air_yards_goal` inside the 10), and direction (`direction`).

Hand-set: nothing.

The priors come from the `priors_<season>.json` for the game's season (the latest earlier one if it has none). Rebuild every event's with `python -m events.baseline_priors 2026`.
