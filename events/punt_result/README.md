# punt result event

What happens when the punt comes down: a fair catch, a return (a carry), downed by the kicking team, out of bounds, a touchback, or a muff (a loose ball).

Predictor: `predict(ctx, lineups, landing_x, allowed, rng) -> PuntResult`

Inputs (besides the [common ones](../README.md)):

- `landing_x`: where the punt comes down.
- `allowed`: the legal results (only `touchback` when the punt reaches the end zone; otherwise `fair_catch`, `return`, `downed`, `out_of_bounds`, `muff`).

Output (`from events.punt_result import ...`):

- `PuntResult(result, player)`: the result, and the returner, fair catcher, or muffer.

The play scenario raises `IllegalChoice` unless the result is one of `allowed`; a fair catch, return, or muff names a player on the field for the receiving team.

Implementations are in [predictors/](predictors/README.md).
