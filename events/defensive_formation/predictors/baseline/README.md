# baseline defensive formation predictor

Box count from the priors; deep safeties hand-set.

API (`from events.defensive_formation.predictors.baseline import predict`, or `play.load_predictors("baseline")`):

- `predict(ctx, lineups, formation, rng) -> DefensiveFormation`

From data: box count by down and distance, from FTN charting (`box`).

Hand-set: deep safeties (two more often on long yardage).

The priors come from the `priors_<season>.json` for the game's season (the latest earlier one if it has none). Rebuild every event's with `python -m events.baseline_priors 2026`.
