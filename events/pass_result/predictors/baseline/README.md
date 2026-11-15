# baseline pass result predictor

Complete, incomplete, or intercepted by pass depth.

API (`from events.pass_result.predictors.baseline import predict`, or `play.load_predictors("baseline")`):

- `predict(ctx, lineups, target, rng) -> PassResult`

From data: results by pass depth (`pass_result`: behind, short, medium, deep; `pass_result_goal` inside the 10) and how often an incompletion is defended (`defended`).

Hand-set: which position groups intercept and defend passes.

The priors come from the `priors_<season>.json` files next to the code: a game is predicted from the counts of what was played before it (the earlier seasons and its own season's earlier weeks), older seasons counting less (see `shared/priors/README.md`). Rebuild every event's with `python -m events.baseline_priors` (`2026` for one season).
