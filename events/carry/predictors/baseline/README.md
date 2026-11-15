# baseline carry predictor

Yards from a histogram for the kind of carry, how it ended, and tacklers by position group.

API (`from events.carry.predictors.baseline import predict`, or `play.load_predictors("baseline")`):

- `predict(ctx, lineups, kind, carrier, yard_line, rng) -> CarryEnd`

From data: yardage histograms by kind (`run`, `scramble`, `catch`, `interception`, `punt_return`, `kick_return`; `run_goal` and `catch_goal` inside the 10), how carries end (`carry_end`), how often a run or a catch ends in a lateral (`lateral`), tacklers by position group (`tackler`), and the assisted tackle rate (`assisted`).

Hand-set: kneels, fumble recovery returns, how returns without data end, slides on scrambles, forced fumble credit, who takes a lateral (a back, receiver, or tight end on the field), and the carry's duration.

The priors come from the `priors_<season>.json` files next to the code: a game is predicted from the counts of the seasons before its own, older seasons counting less (see `shared/priors/README.md`). `kick_return` only pools the seasons played under the game's kickoff rules (`shared.rulebook.KICKOFF`). Rebuild every event's with `python -m events.baseline_priors` (`2026` for one season).
