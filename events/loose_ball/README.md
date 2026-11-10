# loose ball event

Fumbles, muffs, bad snaps, and blocked kicks: who recovers the ball (team and player) and where, or that it goes out of bounds. The rules decide whether the recovering player may advance it and who gets the ball. A shared building block, reachable from anywhere the ball is live.

Predictor: `predict(ctx, lineups, cause, x, last_team, rng) -> Recovery`

Inputs (besides the [common ones](../README.md)):

- `cause`: `fumble`, `bad_snap`, `muff`, or `blocked_kick`.
- `x`: where the ball came loose.
- `last_team`: the team that last had (or, on a muff, touched) the ball.

Output (`from events.loose_ball import ...`):

- `Recovery(team, player, x, seconds)`: the recovering team and player (both None if the ball went out of bounds) and where.

The play scenario raises `IllegalChoice` unless a recovering player is on the field for the recovering team. The scenario clamps the spot to the field.

Implementations are in [predictors/](predictors/README.md).
