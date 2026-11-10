# START
# The kick result event: what happens to a free kick that comes down in play (see README.md).
# - Predictor: predict(ctx, lineups, landing_x, allowed, rng) -> KickResult.
# - KickResult: the result and the returner, fair catcher, muffer, or recovering kicking-team player.
# END
from dataclasses import dataclass


@dataclass(frozen=True)
class KickResult:
    result: str                    # return, touchback, fair_catch, muff, kicking_recovery
    player: str | None = None      # returner / fair catcher / muffer / recovering kicking player
