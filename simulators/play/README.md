# play simulator

Runs the play scenario over many inputs, checks every play, and summarizes each outcome so they can be aggregated and compared with real plays.

API (`from simulators.play import ...`):

- `simulate_plays(contexts, predictors, sims=1, seed=0, examples=30) -> PlaySimulation`: runs each `PlayContext` `sims` times with the given `Predictors`. A play that raises or breaks an invariant is recorded as a failure instead of stopping the run.
- `simulate_play(ctx, predictors, sims=1, seed=0, index=0) -> (results, failures)`: one context's runs as `PlayResult`s, for a caller that works through many plays one at a time (`evaluators/play`). `index` is the context's position in the simulation; with `seed` it fixes every run's seed.
- `PlaySimulation`:
  - `outcomes`: `(context, summary)` for every play that ran.
  - `failures`: `(context index, message, narration or traceback)`.
  - `examples`: `(context index, PlayResult)`: the first run of about `examples` evenly spaced contexts.
- `summarize(result) -> dict`: one play's outcome: `action`, `yards`, `points` by team, `touchdown`, `turnover`, `penalty`, `first_down`, `complete`, `field_goal_result`, `extra_point_result`, `kick_distance`, `touchback`, `return_yards`, `seconds`. Same keys and values as `shared.nflverse`'s `RealPlay.actual`, so real and simulated plays can be measured the same way (a touchdown counts as a first down, as in nflverse).

Every run has its own seed (from `seed`, the context's index, and the run number), so any play can be reproduced.
