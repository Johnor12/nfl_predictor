# START
# The punt result event: what the receiving team does with a punt (see README.md).
# - Predictor: predict(ctx, lineups, landing_x, allowed, rng) -> PuntResult.
# - PuntResult: the result and the returner, fair catcher, or muffer.
# END
from dataclasses import dataclass


@dataclass(frozen=True)
class PuntResult:
    result: str                    # fair_catch, return, downed, out_of_bounds, touchback, muff
    player: str | None = None      # returner / fair catcher / muffer
