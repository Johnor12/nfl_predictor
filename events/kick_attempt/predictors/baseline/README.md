# baseline kick attempt predictor

Field goals by distance bin and extra points, from the priors.

API (`from events.kick_attempt.predictors.baseline import predict`, or `play.load_predictors("baseline")`):

- `predict(ctx, lineups, kicker, distance, rng) -> KickAttempt`

From data: field goal results by distance bin (`fg`) and extra point results (`pat`).

Hand-set: no makes beyond 66 yards, who blocks kicks, and the kick's duration.

The priors come from the `priors_<season>.json` for the game's season (the latest earlier one if it has none). Rebuild every event's with `python -m events.baseline_priors 2026`.
