# START
# Tests for the baseline predictors (no network needed: synthetic contexts and the committed priors file).
# - test_baseline_plays_are_valid: thousands of synthetic situations; every play passes the validator.
# - test_lineups_follow_the_depth_chart / test_kneel_rule / test_fourth_down_long_punts: spot checks.
# END
import random

from predictors.baseline import baseline_predictors, load_priors
from predictors.baseline.predictors import Baseline
from scenarios.play import run_play, validate_play
from scenarios.play.testing import synthetic_context


def test_baseline_plays_are_valid():
    predictors = baseline_predictors(2026)
    for seed in range(3000):
        rng = random.Random(seed)
        result = run_play(synthetic_context(rng), predictors, rng)
        assert validate_play(result) == [], seed


def test_lineups_follow_the_depth_chart():
    baseline = Baseline(load_priors(2026))
    ctx = synthetic_context(random.Random(1), kind="scrimmage", down=1, distance=10.0, x=30.0)
    lineups = baseline.lineups(ctx, random.Random(0))
    offense = ctx.situation.offense
    assert f"{offense}-QB1" in lineups.offense.players
    assert all(f"{offense}-OL{i}" in lineups.offense.players for i in range(1, 6))


def test_kneel_rule():
    baseline = Baseline(load_priors(2026))
    ctx = synthetic_context(random.Random(2), kind="scrimmage", down=1, distance=10.0, x=60.0, quarter=4,
                            clock=90.0, clock_running=True)
    s = ctx.situation
    ctx = synthetic_context(random.Random(2), kind="scrimmage", down=1, distance=10.0, x=60.0, quarter=4, clock=90.0,
                            clock_running=True, score={s.offense: 21, s.defense: 14}, timeouts={s.offense: 3, s.defense: 0})
    assert baseline.lineups(ctx, random.Random(0)).offense.unit == "victory"


def test_fourth_down_long_punts():
    baseline = Baseline(load_priors(2026))
    ctx = synthetic_context(random.Random(3), kind="scrimmage", down=4, distance=12.0, x=25.0, quarter=1)
    units = [baseline.lineups(ctx, random.Random(i)).offense.unit for i in range(200)]
    assert units.count("punt") > 180
