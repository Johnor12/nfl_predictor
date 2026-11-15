# baseline timeout predictor

The real rate at which the offense or the defense calls a timeout before a play, and how long a running clock ran before the call.

API (`from events.timeout.predictors.baseline import predict`, or `game.load_game_predictors("baseline")`):

- `predict(ctx, rng) -> Timeout | None`
- `situation_key(situation) -> str`: the bucket the rates are counted by; `late(situation) -> str`: how late in the half it is.

From data: who called a timeout before each real play (offense, defense, or nobody), by half, time left in the half (more than 5:00, 5:00, 2:00, 1:00), whether the clock is running, and, late in the second half, whether the offense is ahead, behind, or tied (`timeout`). Plays that aren't scrimmage downs share one bucket.

Also from data, for a timeout on a running clock: how long the clock ran first, by how late in the half it is and who called it (`snap_gap`, the real time between the two snaps around such a timeout, less what the first play took: `shared.priors.wait`). Early in a half the offense calls its timeouts with the play clock nearly out, so about 35 seconds run off; a defense in the last two minutes calls it at once.

A team with no timeouts left can't call one; its share goes to nobody.

The priors come from the `priors_<season>.json` files next to the code: a game is predicted from the counts of what was played before it (the earlier seasons and its own season's earlier weeks), older seasons counting less (see `shared/priors/README.md`). Rebuild every event's with `python -m events.baseline_priors` (`2026` for one season).
