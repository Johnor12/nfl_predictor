# START
# The carry event: one player running with the ball (see README.md).
# - Predictor: predict(ctx, lineups, kind, carrier, yard_line, rng) -> CarryEnd.
# - CarryEnd: signed yards, how the carry ended, tacklers, who forced a fumble, and how long it took.
# - ENDS: the legal ways a carry ends.
# END
from dataclasses import dataclass

ENDS = ("tackled", "out_of_bounds", "fumble", "down")


@dataclass(frozen=True)
class CarryEnd:
    yards: float                   # signed, in the carrier's direction of travel
    how: str                       # one of ENDS; down is a slide, kneel, or no contact
    tacklers: tuple[str, ...] = ()
    forced_by: str | None = None   # who forced a fumble
    seconds: float = 0.0
