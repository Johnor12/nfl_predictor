# START
# The injuries event: who was hurt on the play, and for how long (see README.md).
# - Predictor: predict(ctx, lineups, record, rng) -> tuple[Injury, ...].
# - Injury: the player and the number of plays missed.
# END
from dataclasses import dataclass


@dataclass(frozen=True)
class Injury:
    player: str
    plays_out: int                 # plays missed; 999 = rest of the game
