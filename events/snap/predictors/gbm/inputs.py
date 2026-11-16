# START
# The run-or-pass model's inputs: what the offense knows at the snap, as one row of numbers.
# - NAMES: the feature names, in the model's column order.
# - features(ctx, group, shotgun, box) -> list[float]: one play's values (nan where unknown): the situation
#   and the game so far (events.situation), the offense's personnel group (`Lineup.personnel`), whether it
#   is in the shotgun, and the defenders in the box. The same function reads a simulated play (predict) and
#   a real one (train.py), so the two can't drift apart.
# END
from events import situation

NAMES = situation.NAMES + situation.PERSONNEL + ("shotgun", "box")


def features(ctx, group, shotgun, box) -> list[float]:
    return situation.features(ctx) + situation.personnel(group) + [shotgun, box]
