# START
# The pre-snap event: play clock used before the snap, and any pre-snap foul (see README.md).
# - Predictor: predict(ctx, lineups, formation, allowed_fouls, rng) -> PreSnap.
# - PreSnap: seconds of play clock used, and a Foul (events/fouls) or None.
# END
from dataclasses import dataclass

from events.fouls import Foul


@dataclass(frozen=True)
class PreSnap:
    seconds: float                 # play clock used before the snap
    foul: Foul | None = None
