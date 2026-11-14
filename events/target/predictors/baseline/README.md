# baseline target predictor

The receiver by how often each eligible player is thrown to when he is on the field; air yards and direction from the priors.

API (`from events.target.predictors.baseline import predict`, or `play.load_predictors("baseline")`):

- `predict(ctx, lineups, formation, eligible, rng) -> Target`

From data: how often a back, receiver, or tight end on the field is the target, by depth chart role (`target_rate`, from seasons whose data records who was on the field), air yards (`air_yards`, and `air_yards_goal` inside the 10), and direction (`direction`).

Hand-set: nothing.

The priors come from the `priors_<season>.json` files next to the code: each key from the latest season that has it and isn't after the game's (see `shared/priors/README.md`). Rebuild every event's with `python -m events.baseline_priors 2026`.
