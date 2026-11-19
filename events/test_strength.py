# START
# Tests of the inputs about who is playing (no network needed).
# - test_rates_come_from_both_windows: this season's rate and the earlier seasons', nan with nothing to
#   divide by, for a team's form and for a player.
# - test_a_rating_is_shrunk: both windows together, the earlier seasons counting less; 0 with no past.
# - test_conditions: the weather as numbers, nan where the game doesn't say.
# - test_the_quarterback_is_the_one_on_the_field.
# END
import dataclasses
import math
import random

from events import strength
from scenarios.play import load_predictors
from scenarios.play.testing import synthetic_context, with_history

CTX = synthetic_context(random.Random(0), kind="scrimmage", offense="HOME", defense="AWAY", down=1, distance=10.0, x=50.0)


def test_rates_come_from_both_windows():
    ctx = with_history(CTX, "HOME", {"plays": 200.0, "shotgun": 150.0}, {"plays": 1000.0, "shotgun": 500.0})
    team = ctx.game.form("HOME")
    assert strength.rates(team, "shotgun", "plays") == [0.75, 0.5] and strength.total(team, "plays") == 200
    assert strength.rates(team, "fourth_down_goes", "plays") == [0.0, 0.0]  # it has played, and never went for it
    assert all(math.isnan(rate) for rate in strength.rates(ctx.game.form("AWAY"), "shotgun", "plays"))
    passer = with_history(CTX, "HOME-QB1", {"pass_att": 100.0, "pass_cmp": 64.0}, {}).by_id["HOME-QB1"]
    season, career = strength.rates(passer, "pass_cmp", "pass_att")
    assert season == 0.64 and math.isnan(career) and strength.total(passer, "pass_att") == 100


def test_a_rating_is_shrunk():
    passer = with_history(CTX, "HOME-QB1", {"pass_att": 100.0, "pass_cmp_over": 6.0},
                          {"pass_att": 400.0, "pass_cmp_over": -8.0}).by_id["HOME-QB1"]
    assert strength.rating(passer, "pass_cmp_over", "pass_att", 150) == (6.0 - 4.0) / (100 + 200 + 150)
    assert strength.rating(CTX.by_id["HOME-QB2"], "pass_cmp_over", "pass_att", 150) == 0.0
    assert strength.rating(CTX.game.form("AWAY"), "allowed_pass_cmp_over", "allowed_pass_att", 300) == 0.0


def test_conditions():
    game = dataclasses.replace(CTX.game, roof="outdoors", temperature=40, wind=12)
    assert strength.weather(game) == [40, 12, True]
    dome = dataclasses.replace(CTX.game, roof="dome")
    assert math.isnan(strength.weather(dome)[0]) and strength.weather(dome)[2] is False
    assert all(math.isnan(value) for value in strength.weather(CTX.game))


def test_the_quarterback_is_the_one_on_the_field():
    lineups = load_predictors("baseline").lineups(CTX, random.Random(0))
    assert strength.quarterback(CTX, lineups).id == "HOME-QB1"
    assert strength.position(CTX.by_id["HOME-WR2"]) < strength.position(CTX.by_id["HOME-RB1"]) < strength.position(CTX.by_id["HOME-OL1"])
    assert math.isnan(strength.experience(CTX.by_id["HOME-QB1"]))
