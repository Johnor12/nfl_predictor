# START
# The punt distance model's inputs: what is known as the punter kicks, as one row of numbers.
# - NAMES: the feature names, in the model's column order. WHO: the ones about the weather and the punter,
#   which the model reads coarsely (shared.models).
# - CUTS: the distances the model tells apart: every 2 yards from 24 to 64, wider outside.
# - LIMIT: the feature a punt runs up against: the yards to the goal line (a touchback is recorded there).
# - features(ctx, punter) -> list[float]: one play's values (nan where unknown): the situation and the game
#   so far (events.situation), the weather (temperature, wind, outdoors), and the punter (a `Player`): his
#   yards per punt this season and over earlier ones. The same function reads a simulated play (predict) and
#   a real one (train.py).
# END
from events import situation, strength

CUTS = (10, 18) + tuple(range(24, 66, 2)) + (68, 72)
WHO = ("temperature", "wind", "outdoors", "punter_yards", "punter_yards_before")
NAMES = situation.NAMES + WHO
LIMIT = "to_goal"


def features(ctx, punter) -> list[float]:
    return situation.features(ctx) + strength.weather(ctx.game) + strength.rates(punter, "punt_yds", "punts")
