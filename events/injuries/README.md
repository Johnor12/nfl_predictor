# injuries event

Which players were injured on the play, and for how long. The play reports them; the game scenario applies them.

Predictor: `predict(ctx, lineups, record, rng) -> tuple[Injury, ...]`

Inputs (besides the [common ones](../README.md)):

- `record`: the play's facts (read them with `play.facts`).

Output (`from events.injuries import ...`):

- `Injury(player, plays_out)`: plays missed; 999 is the rest of the game.

The play scenario raises `IllegalChoice` unless an injured player was on the field.

Implementations are in [predictors/](predictors/README.md).
