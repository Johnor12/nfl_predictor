# START
# The air yards model's inputs: what is known as the quarterback throws to a receiver, as one row of numbers.
# - NAMES: the feature names, in the model's column order.
# - CUTS: the air yards the model tells apart: every yard from 6 behind the line to 20 past it, then wider.
# - features(ctx, receiver, shotgun) -> list[float]: one play's values (nan where unknown): the situation and
#   the game so far (events.situation), whether the offense is in the shotgun, and the receiver (a `Player`):
#   his position, how deep he has been thrown to (air yards per target, this season and over earlier ones),
#   and his targets this season. The same function reads a simulated play (predict) and a real one (train.py).
# END
from events import situation, strength

CUTS = tuple(range(-6, 21)) + (22, 24, 26, 28, 30, 33, 36, 40, 45, 50)
NAMES = situation.NAMES + ("shotgun", "receiver_position", "receiver_depth", "receiver_depth_before", "receiver_targets")
LIMIT = "to_goal"  # passes pile up at the goal line and in the end zone behind it (shared.models.fit_number's `limit`)


def features(ctx, receiver, shotgun) -> list[float]:
    return (situation.features(ctx) + [shotgun, strength.position(receiver)]
            + strength.rates(receiver, "target_air_yds", "targets") + [strength.total(receiver, "targets")])
