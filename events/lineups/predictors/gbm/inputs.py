# START
# The fourth-down model's inputs: what the coach knows as he decides, as one row of numbers.
# - NAMES: the feature names, in the model's column order. WHO: the ones about the team, which the model
#   reads coarsely (shared.models).
# - UNITS: the model's classes, in order: offense (go for it), punt, field_goal.
# - features(ctx) -> list[float]: one play's values (nan where unknown): the situation and the game so far
#   (events.situation), and how often this team has gone for it on fourth down, this season and over earlier
#   ones. The same function reads a simulated play (predict) and a real one (train.py).
# END
from events import situation, strength

UNITS = ("offense", "punt", "field_goal")
WHO = ("team_goes", "team_goes_before")
NAMES = situation.NAMES + WHO


def features(ctx) -> list[float]:
    return situation.features(ctx) + strength.rates(ctx.game.form(ctx.situation.offense), "fourth_down_goes", "fourth_downs")
