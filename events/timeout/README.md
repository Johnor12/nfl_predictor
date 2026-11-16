# timeout event

Whether a team calls a timeout before the next play, and how far into the play clock. The game scenario asks before every play, and once more after a timeout: the other team may call one in the same dead ball.

Predictor: `predict(ctx, called, rng) -> Timeout | None`

Inputs:

- `ctx`: the next play's `PlayContext` as it stands before the snap: the situation (clock, whether it's running, timeouts left, score, down and distance), the active players, and the game's history.
- `called`: the team that has already called a timeout in this dead ball, or None. `ctx` is then the state after its timeout: charged, the clock stopped.
- `rng`: a seeded `random.Random`.

Output (`from events.timeout import ...`):

- `Timeout(team, seconds)`, or None: the team calling it, and how much of the play clock had gone by when it did (a team saving a delay of game calls it late, a defense stopping the clock at once).

The game scenario raises `IllegalChoice` unless the team has a timeout left, isn't the one that just called one, and `seconds` isn't negative. If the game clock is running, it runs for those seconds first (never into the two-minute warning or past the end of the period). Then the timeout is charged and the clock stops until the snap.

Implementations are in [predictors/](predictors/README.md).
