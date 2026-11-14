# baseline toss choice predictor

Hand-set rates, the same for every team.

API (`from events.toss_choice.predictors.baseline import predict`, or `game.load_game_predictors("baseline")`):

- `predict(ctx, winner, allowed, rng) -> str`

Hand-set: the opening toss is deferred 90% of the time and received otherwise. In overtime the winner takes the ball 97% of the time when a touchdown on the first possession wins the game, and half the time when both teams are guaranteed a possession (the season's format comes from `shared.rulebook`).
