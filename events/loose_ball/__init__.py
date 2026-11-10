# START
# The loose ball event: who ends up with a fumble, muff, bad snap, or blocked kick (see README.md).
# - Predictor: predict(ctx, lineups, cause, x, last_team, rng) -> Recovery.
# - Recovery: the recovering team and player (None if out of bounds) and where.
# END
from dataclasses import dataclass


@dataclass(frozen=True)
class Recovery:
    team: str | None               # None if the ball went out of bounds
    player: str | None
    x: float                       # where it was recovered or went out of bounds
    seconds: float = 0.0
