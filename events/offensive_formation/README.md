# offensive formation event

How the offense lines up: who is on the line, who is in the backfield, and who takes the snap (under center or not). The formation fixes who the eligible receivers are for the rest of the play. Formations are legal by construction; an illegal formation only happens as a pre-snap foul.

Predictor: `predict(ctx, lineups, rng) -> Formation`

Output (`from events.offensive_formation import ...`):

- `Formation(name, line, backfield, qb, under_center)`: the players on the line (left to right), the players in the backfield, and the player receiving the snap (quarterback, punter, or holder).

The play scenario raises `IllegalChoice` unless the line and backfield together are exactly the offensive lineup, with at least 7 on the line and at most 4 in the backfield; the snap receiver is in the backfield; an offense or victory unit has at least 5 players numbered 50-79 on the line (when jerseys are known).

Implementations are in [predictors/](predictors/README.md).
