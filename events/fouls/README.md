# fouls event

Fouls during the play (holding, pass interference, roughing the passer, a face mask...) and dead-ball fouls after it, each with the offending player and the spot. Predicted once, after the ball is dead, conditioned on the whole play. The play scenario decides accept/decline and enforces the penalty.

Predictor: `predict(ctx, lineups, record, allowed_fouls, rng) -> tuple[Foul, ...]`

Inputs (besides the [common ones](../README.md)):

- `record`: the play's facts so far (read them with `play.facts`).
- `allowed_fouls`: the `(type, team, timing)` triples possible on this play (no pass interference on a run, no roughing the passer without a dropback...).

Output (`from events.fouls import ...`):

- `Foul(type, team, player, x, timing)`: `type` is a key of `play.CATALOG`; `timing` is `live`, `return`, or `after` here, and `presnap` or `snap` when the foul comes from the [pre-snap event](../pre_snap/README.md).

The play scenario raises `IllegalChoice` unless each foul is one of `allowed_fouls`, by a player on the field for that team, at a spot on the field.

Implementations are in [predictors/](predictors/README.md).
