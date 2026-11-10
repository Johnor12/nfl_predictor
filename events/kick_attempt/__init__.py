# START
# The kick attempt event: a field goal or extra point (see README.md).
# - Predictor: predict(ctx, lineups, kicker, distance, rng) -> KickAttempt.
# - KickAttempt: the result, who blocked it (or None), and how long it took.
# - RESULTS: the legal results.
# END
from dataclasses import dataclass

RESULTS = ("good", "no_good", "blocked")


@dataclass(frozen=True)
class KickAttempt:
    result: str                    # one of RESULTS
    blocked_by: str | None = None
    seconds: float = 0.0
