# baseline injuries predictor

At most one injury per play, at the real rate.

API (`from events.injuries.predictors.baseline import predict`, or `play.load_predictors("baseline")`):

- `predict(ctx, lineups, record, rng) -> tuple[Injury, ...]`

From data: the share of plays whose description mentions an injured player (`injury`).

Hand-set: ball carriers and tacklers are hurt more often than everyone else, and how long the player is out.

The priors come from the `priors_<season>.json` for the game's season (the latest earlier one if it has none). Rebuild every event's with `python -m events.baseline_priors 2026`.
