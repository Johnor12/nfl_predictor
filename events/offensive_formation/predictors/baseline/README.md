# baseline offensive formation predictor

A legal alignment for the unit, shotgun or under center by the priors.

API (`from events.offensive_formation.predictors.baseline import predict`, or `play.load_predictors("baseline")`):

- `predict(ctx, lineups, rng) -> Formation`

From data: the shotgun rate by down and distance (`shotgun`).

Hand-set: the templates: punt, field goal, and an offense with the linemen in the middle, tight ends and receivers filling the line to 7, and the rest in the backfield.

The priors come from the `priors_<season>.json` for the game's season (the latest earlier one if it has none). Rebuild every event's with `python -m events.baseline_priors 2026`.
