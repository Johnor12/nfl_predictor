# START
# The carry event: one player running with the ball (see README.md).
# - Predictor: predict(ctx, lineups, kind, carrier, yard_line, rng) -> CarryEnd.
# - CarryEnd: signed yards, how the carry ended, tacklers, who forced a fumble, who took a lateral, how long
#   it took, and what a charter adds: who missed a tackle, the tackles the carrier broke, and the yards
#   before first contact.
# - ENDS: the legal ways a carry ends.
# END
from dataclasses import dataclass

ENDS = ("tackled", "out_of_bounds", "fumble", "down", "lateral")


@dataclass(frozen=True)
class CarryEnd:
    yards: float                   # signed, in the carrier's direction of travel
    how: str                       # one of ENDS; down is a slide, kneel, or no contact
    tacklers: tuple[str, ...] = ()
    forced_by: str | None = None   # who forced a fumble
    seconds: float = 0.0
    lateral_to: str | None = None  # the teammate who caught a lateral (a dropped one is a fumble)
    missed: tuple[str, ...] = ()   # defenders who missed a tackle on the way
    broken: int = 0                # the tackles the carrier is credited with breaking
    contact: float | None = None   # yards gained before first contact (None: not charted)
