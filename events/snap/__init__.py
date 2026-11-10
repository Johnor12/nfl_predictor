# START
# The snap event: the snap itself and what the offense does with it (see README.md).
# - Predictor: predict(ctx, lineups, formation, defense, allowed_actions, rng) -> Snap.
# - Snap: the action, the ball carrier on a run, and whether the snap was bad.
# END
from dataclasses import dataclass


@dataclass(frozen=True)
class Snap:
    action: str                    # run, pass, kneel, spike, punt, field_goal
    ball_to: str | None = None     # ball carrier on a run
    bad_snap: bool = False
