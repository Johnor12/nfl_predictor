# START
# The target event: who the pass goes to and where (see README.md).
# - Predictor: predict(ctx, lineups, formation, eligible, rng) -> Target.
# - Target: the receiver, air yards from the line of scrimmage, and the side of the field.
# END
from dataclasses import dataclass


@dataclass(frozen=True)
class Target:
    receiver: str
    air_yards: float
    direction: str                 # left, middle, right
