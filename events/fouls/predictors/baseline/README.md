# baseline fouls predictor

At most one foul per play, at the real rate for the kind of play.

API (`from events.fouls.predictors.baseline import predict`, or `play.load_predictors("baseline")`):

- `predict(ctx, lineups, record, allowed_fouls, rng) -> tuple[Foul, ...]`

From data: flags per play by kind of play (`fouls` over `snaps`, for run, pass, punt, field_goal, kickoff).

Hand-set: the foul's timing when several are possible, its spot, and which positions commit it (`shared.priors.fouler`).

The priors come from the `priors_<season>.json` for the game's season (the latest earlier one if it has none). Rebuild every event's with `python -m events.baseline_priors 2026`.
