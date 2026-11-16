# challenge event

Whether a head coach challenges the play that was just run, and whether he wins. The game scenario asks after every play that a coach may challenge.

Predictor: `predict(ctx, outcome, allowed, rng) -> Challenge | None`

Inputs:

- `ctx`: the `PlayContext` of the play just run (the situation it started from, the game, the active players, the history before it).
- `outcome`: what happened on it, as `scenarios.play.summarize` gives it (`action`, `complete`, `touchdown`, `turnover`, `first_down`, ...): the same keys a real play's `actual` has.
- `allowed`: the teams that may challenge it. The game scenario doesn't ask when nobody may.
- `rng`: a seeded `random.Random`.

Output (`from events.challenge import ...`):

- `Challenge(team, won)`, or None: the team that challenged, and whether the ruling was reversed.

A simulated play is the ruling after any review, as a real play is in the data. So a challenge that was won means the play was first ruled differently on the field; the play itself doesn't change. What a challenge costs is the game scenario's: one of the team's challenges, and a timeout if it was lost.

The game scenario raises `IllegalChoice` unless the team is one of `allowed`.

Implementations are in [predictors/](predictors/README.md).
