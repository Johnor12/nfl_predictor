# START
# Tests of the trained lineups predictor (no network needed; they use the committed model files).
# - test_the_model_reads_the_situation: a punt from deep in its own half, a kick in range, and going for it
#   more on fourth and one than on fourth and ten.
# - test_the_model_reads_the_team: a team that has gone for it often goes for it more.
# - test_other_downs_are_the_baseline_s.
# - test_plays_are_valid: synthetic plays with the trained lineups predictor pass the validator.
# - test_a_season_before_the_first_model_gets_the_baseline.
# END
import dataclasses
import random

from events.lineups.predictors import baseline, gbm
from scenarios.play import load_predictors, run_play, validate_play
from scenarios.play.testing import synthetic_context, with_history

PREDICTORS = load_predictors("baseline", lineups="gbm")
FOURTH = dict(kind="scrimmage", offense="HOME", defense="AWAY", quarter=2, clock=600.0,
              score={"HOME": 10, "AWAY": 10}, down=4)


def _ctx(**situation):
    return synthetic_context(random.Random(0), **{**FOURTH, **situation})


def test_the_model_reads_the_situation():
    assert gbm.units(_ctx(x=30.0, distance=8.0))["punt"] > 0.9
    assert gbm.units(_ctx(x=80.0, distance=8.0))["field_goal"] > 0.8
    assert gbm.units(_ctx(x=60.0, distance=1.0))["offense"] > gbm.units(_ctx(x=60.0, distance=10.0))["offense"] + 0.2


def test_the_model_reads_the_team():
    ctx = _ctx(x=58.0, distance=2.0)
    bold, careful = (with_history(ctx, "HOME", {"fourth_downs": 100.0, "fourth_down_goes": goes}) for goes in (32.0, 8.0))
    assert gbm.units(bold)["offense"] > gbm.units(careful)["offense"] + 0.03


def test_other_downs_are_the_baseline_s():
    ctx = _ctx(x=50.0, distance=5.0, down=2)
    assert gbm.units(ctx) == baseline.units(ctx)


def test_plays_are_valid():
    for seed in range(500):
        rng = random.Random(seed)
        assert validate_play(run_play(synthetic_context(rng), PREDICTORS, rng)) == [], seed


def test_a_season_before_the_first_model_gets_the_baseline():
    ctx = _ctx(x=58.0, distance=2.0)
    ctx = dataclasses.replace(ctx, game=dataclasses.replace(ctx.game, season=2011))
    assert gbm.units(ctx) == baseline.units(ctx)
