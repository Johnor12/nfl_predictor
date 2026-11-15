# timeout event

Whether a team calls a timeout before the next play, and how far into the play clock. The game scenario asks before every play.

Predictor: `predict(ctx, rng) -> Timeout | None`

Inputs:

- `ctx`: the next play's `PlayContext` as it stands before the snap: the situation (clock, whether it's running, timeouts left, score, down and distance), the active players, and the game's history.
- `rng`: a seeded `random.Random`.

Output (`from events.timeout import ...`):

- `Timeout(team, seconds)`, or None: the team calling it, and how much of the play clock had gone by when it did (a team saving a delay of game calls it late, a defense stopping the clock at once).

The game scenario raises `IllegalChoice` unless the team has a timeout left and `seconds` isn't negative. If the game clock is running, it runs for those seconds first (never into the two-minute warning or past the end of the period). Then the timeout is charged and the clock stops until the snap.

Implementations are in [predictors/](predictors/README.md).
