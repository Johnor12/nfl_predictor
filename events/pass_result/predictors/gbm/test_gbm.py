# START
# Tests of the trained pass result predictor (no network needed; they use the committed model files).
# - test_the_model_reads_the_throw: a deep pass is completed less often, and intercepted more, than a short one.
# - test_the_model_reads_the_quarterback: an accurate passer completes more than an erratic one.
# - test_plays_are_valid: synthetic plays with the trained pass result predictor pass the validator.
# - test_a_season_before_the_first_model_gets_the_baseline.
# END
import dataclasses
import random

from events.pass_result.predictors import baseline, gbm
from events.target import Target
from scenarios.play import load_predictors, run_play, validate_play
from scenarios.play.testing import synthetic_context, with_history

PREDICTORS = load_predictors("baseline", pass_result="gbm")
MIDFIELD = dict(kind="scrimmage", offense="HOME", defense="AWAY", x=50.0, quarter=2, clock=600.0,
                score={"HOME": 10, "AWAY": 10}, down=1, distance=10.0)


def _results(air_yards=6.0, qb=None, season=2026):
    ctx = synthetic_context(random.Random(0), **MIDFIELD)
    ctx = dataclasses.replace(ctx, game=dataclasses.replace(ctx.game, season=season))
    ctx = with_history(ctx, "HOME-QB1", qb) if qb else ctx
    lineups = PREDICTORS.lineups(ctx, random.Random(0))
    return ctx, lineups, Target("HOME-WR1", air_yards, "left")


def test_the_model_reads_the_throw():
    short, deep = gbm.results(*_results(4.0)), gbm.results(*_results(30.0))
    assert short["complete"] > deep["complete"] + 0.25 and deep["intercepted"] > short["intercepted"]
    assert abs(sum(short.values()) - 1) < 1e-6


def test_the_model_reads_the_quarterback():
    accurate = gbm.results(*_results(qb={"pass_att": 500.0, "pass_cmp": 350.0, "int_thrown": 6.0}))
    erratic = gbm.results(*_results(qb={"pass_att": 500.0, "pass_cmp": 280.0, "int_thrown": 18.0}))
    assert accurate["complete"] > erratic["complete"] + 0.01


def test_plays_are_valid():
    for seed in range(500):
        rng = random.Random(seed)
        assert validate_play(run_play(synthetic_context(rng), PREDICTORS, rng)) == [], seed


def test_a_season_before_the_first_model_gets_the_baseline():
    args = _results(season=2011)
    assert gbm.results(*args) == baseline.results(*args)
