# baseline offensive formation predictor

A legal alignment for the unit, shotgun or under center by the priors.

API (`from events.offensive_formation.predictors.baseline import predict`, or `play.load_predictors("baseline")`):

- `predict(ctx, lineups, rng) -> Formation`

From data: the shotgun rate by down and distance (`shotgun`), sharpened by the offense's personnel group (`personnel_shotgun`, from seasons whose data records who was on the field).

Hand-set: the templates: punt, field goal, and an offense with the linemen in the middle, tight ends and receivers filling the line to 7, and the rest in the backfield.

The priors come from the `priors_<season>.json` files next to the code: a game is predicted from the counts of what was played before it (the earlier seasons and its own season's earlier weeks), older seasons counting less (see `shared/priors/README.md`). Rebuild every event's with `python -m events.baseline_priors` (`2026` for one season).
