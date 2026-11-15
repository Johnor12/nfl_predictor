# baseline injuries predictor

At most one injury per play, at the real rate.

API (`from events.injuries.predictors.baseline import predict`, or `play.load_predictors("baseline")`):

- `predict(ctx, lineups, record, rng) -> tuple[Injury, ...]`

From data: the share of plays whose description mentions an injured player (`injury`).

Hand-set: ball carriers and tacklers are hurt more often than everyone else, and how long the player is out.

The priors come from the `priors_<season>.json` files next to the code: a game is predicted from the counts of what was played before it (the earlier seasons and its own season's earlier weeks), older seasons counting less (see `shared/priors/README.md`). Rebuild every event's with `python -m events.baseline_priors` (`2026` for one season).
