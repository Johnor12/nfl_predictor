# target event

Who the pass goes to and where: air yards from the line of scrimmage and the side of the field. Only eligible receivers can be targeted.

Predictor: `predict(ctx, lineups, formation, eligible, rng) -> Target`

Inputs (besides the [common ones](../README.md)):

- `formation`: the offense's `Formation`.
- `eligible`: the eligible receivers' ids.

Output (`from events.target import ...`):

- `Target(receiver, air_yards, direction)`: `direction` is left, middle, or right.

The play scenario raises `IllegalChoice` unless the receiver is one of `eligible`. The scenario clamps the target spot to half a yard inside the end lines (a pass caught beyond the end line is incomplete).

Implementations are in [predictors/](predictors/README.md).
