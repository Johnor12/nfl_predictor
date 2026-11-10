# pre snap event

How much of the play clock is used before the snap (it comes off the game clock if the clock is running) and any pre-snap foul. A dead-ball foul (false start, encroachment, delay of game...) ends the play without a snap. A foul at the snap (defensive offside, illegal formation...) leaves the ball live: a free play for the offense.

Predictor: `predict(ctx, lineups, formation, allowed_fouls, rng) -> PreSnap`

Inputs (besides the [common ones](../README.md)):

- `formation`: the offense's `Formation`.
- `allowed_fouls`: the `(type, team, timing)` triples the rules allow before the snap.

Output (`from events.pre_snap import ...`):

- `PreSnap(seconds, foul)`: play clock used, and a `Foul` (see [fouls](../fouls/README.md)) with timing `presnap` or `snap`, or None.

The play scenario raises `IllegalChoice` unless `seconds` isn't negative; a foul is one of `allowed_fouls`, by a player on the field, at a spot on the field.

Implementations are in [predictors/](predictors/README.md).
