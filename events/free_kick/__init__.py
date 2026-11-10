# START
# The free kick event: a kickoff or safety kick leaving the tee (see README.md).
# - Predictor: predict(ctx, lineups, onside, rng) -> FreeKick.
# - FreeKick: the kicker, distance, whether it went out of bounds, and hang time.
# END
from dataclasses import dataclass


@dataclass(frozen=True)
class FreeKick:
    kicker: str
    distance: float                # from the kick spot to where it lands
    out_of_bounds: bool = False
    seconds: float = 0.0           # hang time (doesn't run the game clock)
