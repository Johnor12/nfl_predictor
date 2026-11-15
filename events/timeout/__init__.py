# START
# The timeout event: whether a team calls a timeout before the next play (see README.md).
# - Predictor: predict(ctx, rng) -> Timeout | None. ctx is the next play's PlayContext as it stands before
#   the snap.
# - Timeout: the team calling it, and how long the play clock had been going when it did.
# END
from dataclasses import dataclass


@dataclass(frozen=True)
class Timeout:
    team: str
    seconds: float = 0.0           # play clock used before the call (it comes off a running game clock)
