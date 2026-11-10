# START
# The offensive formation event: how the offense lines up (see README.md).
# - Predictor: predict(ctx, lineups, rng) -> Formation.
# - Formation: who is on the line, who is in the backfield, and who takes the snap.
# END
from dataclasses import dataclass


@dataclass(frozen=True)
class Formation:
    name: str
    line: tuple[str, ...]          # players on the line of scrimmage, left to right
    backfield: tuple[str, ...]
    qb: str                        # player receiving the snap (quarterback, punter, or holder)
    under_center: bool
