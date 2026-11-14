# baseline pre snap predictor

Play clock used by game script, and pre-snap fouls at the real rate.

API (`from events.pre_snap.predictors.baseline import predict`, or `play.load_predictors("baseline")`):

- `predict(ctx, lineups, formation, allowed_fouls, rng) -> PreSnap`

From data: pre-snap foul rates per snap (`fouls` over `snaps`).

Hand-set: play clock usage (hurry, bleed, or normal pace) and which positions commit each foul (`shared.priors.fouler`).

The priors come from the `priors_<season>.json` files next to the code: each key from the latest season that has it and isn't after the game's (see `shared/priors/README.md`). Rebuild every event's with `python -m events.baseline_priors 2026`.
