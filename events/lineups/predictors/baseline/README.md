# baseline lineups predictor

The unit from hand-set rules and 4th-down priors, then 11 players filled from the depth chart.

API (`from events.lineups.predictors.baseline import predict`, or `play.load_predictors("baseline")`):

- `predict(ctx, rng) -> Lineups`

From data: unit choice by down, distance, and field position (`unit`; this is the 4th-down decision), and the two-point attempt rate (`two_point`).

Hand-set: the kneel rule, the field goal at the end of a half, the late-game two-point chart, onside kicks, the personnel mix, and the depth-chart fill for every unit (nflverse has no 2026 on-field personnel yet).

The priors come from the `priors_<season>.json` for the game's season (the latest earlier one if it has none). Rebuild every event's with `python -m events.baseline_priors 2026`.
