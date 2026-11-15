# baseline kick attempt predictor

Field goals by distance bin and extra points, from the priors.

API (`from events.kick_attempt.predictors.baseline import predict`, or `play.load_predictors("baseline")`):

- `predict(ctx, lineups, kicker, distance, rng) -> KickAttempt`

From data: field goal results by distance bin (`fg`) and extra point results (`pat`).

Hand-set: no makes beyond 66 yards, who blocks kicks, and the kick's duration.

The priors come from the `priors_<season>.json` files next to the code: a game is predicted from the counts of what was played before it (the earlier seasons and its own season's earlier weeks), older seasons counting less (see `shared/priors/README.md`). `pat` only pools the seasons played under the game's try rules (`shared.rulebook.TRY`). Rebuild every event's with `python -m events.baseline_priors` (`2026` for one season).
