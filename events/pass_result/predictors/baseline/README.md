# baseline pass result predictor

Complete, incomplete, or intercepted by pass depth.

API (`from events.pass_result.predictors.baseline import predict`, or `play.load_predictors("baseline")`):

- `predict(ctx, lineups, target, rng) -> PassResult`

From data: results by pass depth (`pass_result`: behind, short, medium, deep; `pass_result_goal` inside the 10), how often an incompletion is defended (`defended`), and the position groups that defend and intercept passes (`defender`: a lineman bats down one defended pass in eight).

From each defender's own past: a position group's passes defended and interceptions go to its players on the field by their own passes defended per snap on defense (`shared.priors.COVERAGE`).

From Pro Football Reference's charting (2018 on, counted per game, so these are league rates): the defender in coverage (`covered`: nearly every target has one; `coverage`: his position group; picked by how often he has been thrown at; the defender who broke the pass up when there is one), and whether an incompletion was a drop (`drop`; never one a defender got to) or a bad throw (`bad_throw`).

Hand-set: how long the ball is in the air (by its air yards; with the time to throw, an incompletion takes the 5 seconds a real one does).

The priors come from the `priors_<season>.json` files next to the code: a game is predicted from the counts of what was played before it (the earlier seasons and its own season's earlier weeks), older seasons counting less (see `shared/priors/README.md`). Rebuild every event's with `python -m events.baseline_priors` (`2026` for one season).
