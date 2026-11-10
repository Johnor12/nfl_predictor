# baseline carry predictor

Yards from a histogram for the kind of carry, how it ended, and tacklers by position group.

API (`from events.carry.predictors.baseline import predict`, or `play.load_predictors("baseline")`):

- `predict(ctx, lineups, kind, carrier, yard_line, rng) -> CarryEnd`

From data: yardage histograms by kind (`run`, `scramble`, `catch`, `interception`, `punt_return`, `kick_return`; `run_goal` and `catch_goal` inside the 10), how carries end (`carry_end`), tacklers by position group (`tackler`), and the assisted tackle rate (`assisted`).

Hand-set: kneels, fumble recovery returns, how returns without data end, slides on scrambles, forced fumble credit, and the carry's duration.

The priors come from the `priors_<season>.json` for the game's season (the latest earlier one if it has none). Rebuild every event's with `python -m events.baseline_priors 2026`.
