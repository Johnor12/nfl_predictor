# baseline timeout predictor

The real rate at which the offense or the defense calls a timeout before a play.

API (`from events.timeout.predictors.baseline import predict`, or `game.load_game_predictors("baseline")`):

- `predict(ctx, rng) -> str | None`
- `situation_key(situation) -> str`: the bucket the rates are counted by.

From data: who called a timeout before each real play (offense, defense, or nobody), by half, time left in the half (more than 5:00, 5:00, 2:00, 1:00), whether the clock is running, and, late in the second half, whether the offense is ahead, behind, or tied (`timeout`). Plays that aren't scrimmage downs share one bucket.

A team with no timeouts left can't call one; its share goes to nobody.

The priors come from the `priors_<season>.json` files next to the code: a game is predicted from the counts of the seasons before its own, older seasons counting less (see `shared/priors/README.md`). Rebuild every event's with `python -m events.baseline_priors` (`2026` for one season).
