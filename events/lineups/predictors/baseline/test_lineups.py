# START
# Spot checks of the baseline lineups predictor on synthetic contexts (no network needed).
# - test_lineups_follow_the_depth_chart / test_kneel_rule / test_fourth_down_long_punts.
# - test_players_are_on_the_field_as_often_as_they_have_been: recent snaps decide who plays, and how often.
# END
import dataclasses
import random

from events.lineups.predictors.baseline import predict
from scenarios.play.testing import synthetic_context


def test_lineups_follow_the_depth_chart():
    ctx = synthetic_context(random.Random(1), kind="scrimmage", down=1, distance=10.0, x=30.0)
    lineups = predict(ctx, random.Random(0))
    offense = ctx.situation.offense
    assert f"{offense}-QB1" in lineups.offense.players
    assert all(f"{offense}-OL{i}" in lineups.offense.players for i in range(1, 6))


def test_kneel_rule():
    ctx = synthetic_context(random.Random(2), kind="scrimmage", offense="HOME", defense="AWAY", down=1, distance=10.0,
                            x=60.0, quarter=4, clock=90.0, clock_running=True, score={"HOME": 21, "AWAY": 14},
                            timeouts={"HOME": 3, "AWAY": 0})
    assert predict(ctx, random.Random(0)).offense.unit == "victory"


def test_fourth_down_long_punts():
    ctx = synthetic_context(random.Random(3), kind="scrimmage", down=4, distance=12.0, x=25.0, quarter=1)
    units = [predict(ctx, random.Random(i)).offense.unit for i in range(200)]
    assert units.count("punt") > 180


def test_players_are_on_the_field_as_often_as_they_have_been():
    ctx = synthetic_context(random.Random(1), kind="scrimmage", offense="HOME", defense="AWAY", down=1, distance=10.0,
                            x=30.0, quarter=1)
    snaps = {"HOME-RB1": (("offense", 100.0),), "HOME-RB2": (("offense", 300.0),), "HOME-QB2": (("offense", 400.0),),
             "HOME-OL8": (("offense", 400.0),), "AWAY-DB9": (("defense", 400.0),)}
    ctx = dataclasses.replace(ctx, players=tuple(dataclasses.replace(p, snaps=snaps.get(p.id, ())) for p in ctx.players))
    lineups = [predict(ctx, random.Random(i)) for i in range(400)]
    one_back = [l.offense.players for l in lineups if l.offense.personnel[0] == "1"]
    assert 0.75 < sum("HOME-RB2" in players for players in one_back) / len(one_back) < 0.92  # 300 of 400 snaps
    assert all(("HOME-RB1" in players) != ("HOME-RB2" in players) for players in one_back)
    assert all("HOME-QB1" in l.offense.players and "HOME-OL8" in l.offense.players for l in lineups)
    assert all("AWAY-DB9" in l.defense.players for l in lineups)  # the only defender with snaps always plays
