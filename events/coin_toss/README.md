# coin toss event

Which team wins the coin toss, before the game and before overtime.

Predictor: `predict(ctx, rng) -> str`

Inputs:

- `ctx`: the coin toss scenario's `TossContext` (the game, both teams' active players, and whether this is the overtime toss).
- `rng`: a seeded `random.Random`.

Output: the winning team's name.

The coin toss scenario raises `IllegalChoice` unless the team is one of the two playing.

Implementations are in [predictors/](predictors/README.md).
