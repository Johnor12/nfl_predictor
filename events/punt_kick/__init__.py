# START
# The punt kick event: blocked or not, and how far the punt goes (see README.md).
# - Predictor: predict(ctx, lineups, punter, rng) -> PuntKick.
# - PuntKick: distance, who blocked it (or None), and hang time.
# END
from dataclasses import dataclass


@dataclass(frozen=True)
class PuntKick:
    distance: float                # from the line of scrimmage to where the ball is caught, downed, or goes out
    blocked_by: str | None = None
    seconds: float = 0.0
