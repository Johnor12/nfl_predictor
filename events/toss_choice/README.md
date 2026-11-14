# toss choice event

What the team that won the coin toss does with it: take the ball, kick, or defer the choice to the second half.

Predictor: `predict(ctx, winner, allowed, rng) -> str`

Inputs:

- `ctx`: the coin toss scenario's `TossContext` (the game, both teams' active players, and whether this is the overtime toss).
- `winner`: the team that won the toss.
- `allowed`: the choices the rules allow (`receive`, `kick`, and, except in overtime, `defer`).
- `rng`: a seeded `random.Random`.

Output (`from events.toss_choice import CHOICES`): one of `allowed`.

The coin toss scenario raises `IllegalChoice` unless the choice is one of `allowed`. What a choice means (who kicks off each half) is the scenario's rules, not the predictor's.

Implementations are in [predictors/](predictors/README.md).
