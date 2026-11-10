# START
# Spot checks of the baseline lineups predictor on synthetic contexts (no network needed).
# - test_lineups_follow_the_depth_chart / test_kneel_rule / test_fourth_down_long_punts.
# END
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
