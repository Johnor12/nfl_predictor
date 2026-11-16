# START
# The shotgun model's inputs: what the offense knows as it lines up, as one row of numbers.
# - NAMES: the feature names, in the model's column order.
# - features(ctx, group) -> list[float]: one play's values (nan where unknown): the situation and the game
#   so far (events.situation), and the offense's personnel group (`Lineup.personnel`, None where the data
#   doesn't say). The same function reads a simulated play (predict) and a real one (train.py).
# END
from events import situation

NAMES = situation.NAMES + situation.PERSONNEL


def features(ctx, group) -> list[float]:
    return situation.features(ctx) + situation.personnel(group)
