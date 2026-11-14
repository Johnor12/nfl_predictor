# baseline loose ball predictor

Who recovers, near the spot of the ball.

API (`from events.loose_ball.predictors.baseline import predict`, or `play.load_predictors("baseline")`):

- `predict(ctx, lineups, cause, x, last_team, rng) -> Recovery`

From data: how often a fumble is lost (`fumble_recovery`).

Hand-set: recovery odds for bad snaps, muffs, and blocked kicks, fumbles out of bounds, the recovering player (anyone on the field), and where and how long the recovery takes.

The priors come from the `priors_<season>.json` files next to the code: each key from the latest season that has it and isn't after the game's (see `shared/priors/README.md`). Rebuild every event's with `python -m events.baseline_priors 2026`.
