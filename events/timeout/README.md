# timeout event

Whether a team calls a timeout before the next play. The game scenario asks before every play.

Predictor: `predict(ctx, rng) -> str | None`

Inputs:

- `ctx`: the next play's `PlayContext` as it stands before the snap: the situation (clock, whether it's running, timeouts left, score, down and distance), the active players, and the game's history.
- `rng`: a seeded `random.Random`.

Output: the team calling a timeout, or None.

The game scenario raises `IllegalChoice` unless the team has a timeout left. It then charges the timeout and stops the clock until the snap.

Implementations are in [predictors/](predictors/README.md).
