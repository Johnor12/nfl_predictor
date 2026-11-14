# coin toss scenario

The coin toss before a game, and before overtime: who wins it, what they choose, and who kicks off.

API (`from scenarios.coin_toss import ...`):

- `run_coin_toss(ctx, predictors, rng) -> Toss`: runs one toss from a `TossContext` with a `random.Random`. Raises the play scenario's `IllegalChoice` if a predictor names a team that isn't playing or a choice that isn't allowed.
- `TossContext(game, players, overtime=False)`: the game, both teams' active players, and whether this is the overtime toss.
- `Toss(winner, choice, kicking, receiving, second_half_kicking, overtime)`: `second_half_kicking` is None for an overtime toss.
- `allowed_choices(ctx)`: `receive`, `kick`, and, except in overtime, `defer`.
- `TossPredictors(coin_toss, toss_choice)`: one function per event. `load_toss_predictors("baseline", toss_choice="other")` builds it from each event's implementation of that name (`events/<event>/predictors/<name>/`).

## the event chain

```
coin toss -> toss choice -> who kicks off now, and at the second half
```

Both events are packages under `events/`: `coin_toss` (which team wins) and `toss_choice` (what the winner does with it).

## hardcoded rules

- The team that doesn't choose first chooses at the second half, and takes the ball.
- So a winner that defers kicks off the game and receives the second half; a winner that receives kicks off the second half; a winner that chooses to kick does it in both halves.
- There is no deferring in overtime.

Not modeled: the choice of which goal to defend (wind and sun aren't modeled yet either).
