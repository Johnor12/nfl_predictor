# punt kick event

Whether the punt is blocked (a loose ball) and how far it goes.

Predictor: `predict(ctx, lineups, punter, rng) -> PuntKick`

Inputs (besides the [common ones](../README.md)):

- `punter`: the punter's id.

Output (`from events.punt_kick import ...`):

- `PuntKick(distance, blocked_by, seconds)`: yards from the line of scrimmage to where the ball is caught, downed, or goes out; who blocked it, or None; hang time.

The play scenario raises `IllegalChoice` unless a blocker is on the field for the defense. The scenario floors the distance at 0 and stops the punt at the end line.

Implementations are in [predictors/](predictors/README.md).
