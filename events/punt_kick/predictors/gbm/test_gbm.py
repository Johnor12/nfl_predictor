# START
# Tests of the trained punt kick predictor (no network needed; they use the committed model files).
# - test_the_model_reads_the_punter_and_the_weather: a punter who has kicked far is likelier to kick 48 yards,
#   and a windy day makes it less likely.
# - test_the_model_knows_the_goal_line: nobody punts 50 yards from the opponent's 40.
# - test_plays_are_valid: synthetic plays with the trained punt kick predictor pass the validator.
# - test_a_season_before_the_first_model_gets_the_baseline.
# END
import dataclasses
import random

from events.punt_kick.predictors import baseline, gbm
from events.punt_kick.predictors.gbm.inputs import CUTS, features
from scenarios.play import load_predictors, run_play, validate_play
from scenarios.play.testing import synthetic_context, with_history

PREDICTORS = load_predictors("baseline", punt_kick="gbm")
OWN_30 = dict(kind="scrimmage", offense="HOME", defense="AWAY", x=30.0, quarter=2, clock=600.0,
              score={"HOME": 10, "AWAY": 10}, down=4, distance=8.0)


def _reaches(yards, history=None, wind=None, **situation):
    """The model's probability that the punt goes `yards` or more."""
    ctx = synthetic_context(random.Random(0), **{**OWN_30, **situation})
    ctx = with_history(ctx, "HOME-P1", history) if history else ctx
    if wind is not None:
        ctx = dataclasses.replace(ctx, game=dataclasses.replace(ctx.game, roof="outdoors", temperature=50, wind=wind))
    return gbm.load_model(2026)(features(ctx, ctx.by_id["HOME-P1"]))[CUTS.index(yards)]


def test_the_model_reads_the_punter_and_the_weather():
    assert _reaches(48, {"punts": 60.0, "punt_yds": 2940.0}) > _reaches(48, {"punts": 60.0, "punt_yds": 2580.0}) + 0.03
    assert _reaches(48, wind=3) > _reaches(48, wind=22) + 0.03


def test_the_model_knows_the_goal_line():
    assert _reaches(50, x=60.0) < 0.01 < _reaches(50)


def test_plays_are_valid():
    for seed in range(500):
        rng = random.Random(seed)
        assert validate_play(run_play(synthetic_context(rng), PREDICTORS, rng)) == [], seed


def test_a_season_before_the_first_model_gets_the_baseline():
    ctx = synthetic_context(random.Random(0), **OWN_30)
    ctx = dataclasses.replace(ctx, game=dataclasses.replace(ctx.game, season=2011))
    draws = [module.distance(ctx, "HOME-P1", random.Random(1)) for module in (gbm, baseline)]
    assert draws[0] == draws[1]
