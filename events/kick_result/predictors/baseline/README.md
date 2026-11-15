# baseline kick result predictor

Return, touchback, fair catch, or muff by where the kickoff comes down.

API (`from events.kick_result.predictors.baseline import predict`, or `play.load_predictors("baseline")`):

- `predict(ctx, lineups, landing_x, allowed, rng) -> KickResult`

From data: results in the landing zone and the end zone (`kickoff_result`).

Hand-set: the onside recovery rate, the muff rate, and the fair catch rate on safety kicks (kickoffs' own, where the rules allow one, is in the data: about 3% in 2023, next to none before). The returner is the top kick returner on the field by depth chart.

The priors come from the `priors_<season>.json` files next to the code: a game is predicted from the counts of the seasons before its own, older seasons counting less (see `shared/priors/README.md`). `kickoff_result` only pools the seasons played under the game's kickoff rules (`shared.rulebook.KICKOFF`). Rebuild every event's with `python -m events.baseline_priors` (`2026` for one season).
