# kick result event

What happens to a free kick that comes down in play: a return (a carry), a touchback, a fair catch (when the rules allow one), a muff (a loose ball), or a recovery by the kicking team.

Predictor: `predict(ctx, lineups, landing_x, allowed, rng) -> KickResult`

Inputs (besides the [common ones](../README.md)):

- `landing_x`: where the kick comes down.
- `allowed`: the legal results under the season's rules (`kicking_recovery` only on onside kicks; no fair catches under the dynamic kickoff).

Output (`from events.kick_result import ...`):

- `KickResult(result, player)`: the result, and the returner, fair catcher, muffer, or recovering kicking-team player.

The play scenario raises `IllegalChoice` unless the result is one of `allowed`; every result but a touchback names a player on the field for the right team.

Implementations are in [predictors/](predictors/README.md).
