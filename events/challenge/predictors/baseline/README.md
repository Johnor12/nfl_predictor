# baseline challenge predictor

The real rate at which the offense or the defense challenges a play, and wins or loses.

API (`from events.challenge.predictors.baseline import predict`, or `game.load_game_predictors("baseline")`):

- `predict(ctx, outcome, allowed, rng) -> Challenge | None`
- `play_key(outcome) -> str`: the bucket the rates are counted by; `challengeable(situation) -> bool`: a coach may challenge a play from here.

From data: who challenged each real play and how the review came out (the offense or the defense, won or lost, or nobody), by the kind of play (a completion, an incompletion, a run, a sack, a kick, anything else) and how it ended (a touchdown, a turnover, a first down, or none of them). The play is the one in the data, which is the ruling after the review: a completion the defense challenged and lost, or an incompletion the defense challenged and won.

Only plays a coach could challenge are counted: not after the two-minute warning of a half or in overtime, where the replay official starts every review.

A team that may not challenge (no timeout or no challenge left) can't; its share goes to nobody.

The priors come from the `priors_<season>.json` files next to the code: a game is predicted from the counts of what was played before it (the earlier seasons and its own season's earlier weeks), older seasons counting less (see `shared/priors/README.md`). Rebuild every event's with `python -m events.baseline_priors` (`2026` for one season).
