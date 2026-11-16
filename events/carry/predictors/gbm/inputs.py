# START
# The yards models' inputs: what is known as a ball carrier sets off, as one row of numbers. There are two
# models: designed runs, and the yards after a catch.
# - RUN / CATCH: each model's feature names, in its column order. RUN_WHO / CATCH_WHO: the ones about the
#   carrier and his team, which the models read coarsely (shared.models).
# - RUN_CUTS / CATCH_CUTS: the yards each model tells apart: every yard up to 15, then wider.
# - RUN_LIMIT / CATCH_LIMIT: the feature each carry runs up against: the yards to the goal line from where it
#   starts (shared.models.fit_number's `limit`).
# - run(ctx, carrier) -> list[float]: the situation and the game so far (events.situation), the carrier's
#   position, his yards per rush this season and over earlier ones, and his team's yards per designed run.
# - catch(ctx, receiver, yard_line) -> list[float]: the situation and the game so far, how far downfield the
#   ball was caught, how far that is from the goal line, the receiver's position, and his yards after the
#   catch per reception, this season and over earlier ones.
# `carrier` and `receiver` are `Player`s. The same functions read a simulated play (predict) and a real one
# (train.py).
# END
from events import situation, strength

LONG = (17, 19, 21, 24, 27, 30, 35, 40, 50, 60, 75)
RUN_CUTS = tuple(range(-5, 16)) + LONG
CATCH_CUTS = tuple(range(-2, 16)) + LONG
RUN_WHO = ("carrier_yards", "carrier_yards_before", "team_yards", "team_yards_before")
CATCH_WHO = ("receiver_yac", "receiver_yac_before")
RUN = situation.NAMES + ("carrier_position",) + RUN_WHO
CATCH = situation.NAMES + ("air_yards", "catch_to_goal", "receiver_position") + CATCH_WHO
RUN_LIMIT, CATCH_LIMIT = "to_goal", "catch_to_goal"


def run(ctx, carrier) -> list[float]:
    team = ctx.game.form(carrier.team)
    return (situation.features(ctx) + [strength.position(carrier)] + strength.rates(carrier, "rush_yds", "rush_att")
            + strength.rates(team, "rush_yds", "runs"))


def catch(ctx, receiver, yard_line) -> list[float]:
    return (situation.features(ctx) + [yard_line - ctx.situation.x, 100 - yard_line, strength.position(receiver)]
            + strength.rates(receiver, "rec_yac", "receptions"))
