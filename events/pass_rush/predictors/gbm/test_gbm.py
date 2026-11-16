# START
# Tests of the trained pass rush predictor (no network needed; they use the committed model files).
# - test_the_model_reads_the_situation: more sacks and scrambles on third and long than on first and ten.
# - test_the_model_reads_the_quarterback: one who has been sacked a lot is sacked more, and one who runs
#   scrambles more.
# - test_plays_are_valid: synthetic plays with the trained pass rush predictor pass the validator.
# - test_a_season_before_the_first_model_gets_the_baseline.
# END
import dataclasses
import random

from events.pass_rush.predictors import baseline, gbm
from scenarios.play import load_predictors, run_play, validate_play
from scenarios.play.testing import synthetic_context, with_history

PREDICTORS = load_predictors("baseline", pass_rush="gbm")
MIDFIELD = dict(kind="scrimmage", offense="HOME", defense="AWAY", x=50.0, quarter=2, clock=600.0,
                score={"HOME": 10, "AWAY": 10})
LEAGUE = {"throw": 90, "sack": 6, "scramble": 4}


def _rates(qb=None, **situation):
    ctx = synthetic_context(random.Random(0), **{**MIDFIELD, **situation})
    rng = random.Random(0)
    formation = PREDICTORS.offensive_formation(ctx, PREDICTORS.lineups(ctx, rng), rng)
    if qb:
        ctx = with_history(ctx, formation.qb, qb)
    return gbm.dropback(ctx, formation, LEAGUE)


def test_the_model_reads_the_situation():
    long, early = _rates(down=3, distance=12.0), _rates(down=1, distance=10.0)
    assert long["sack"] > early["sack"] and long["scramble"] > early["scramble"]
    assert abs(sum(long.values()) - 1) < 1e-6


def test_the_model_reads_the_quarterback():
    statue = _rates({"dropbacks": 400.0, "times_sacked": 44.0, "scrambles": 4.0}, down=2, distance=8.0)
    runner = _rates({"dropbacks": 400.0, "times_sacked": 16.0, "scrambles": 40.0}, down=2, distance=8.0)
    assert statue["sack"] > runner["sack"] + 0.005 and runner["scramble"] > statue["scramble"] + 0.01


def test_plays_are_valid():
    for seed in range(500):
        rng = random.Random(seed)
        assert validate_play(run_play(synthetic_context(rng), PREDICTORS, rng)) == [], seed


def test_a_season_before_the_first_model_gets_the_baseline():
    ctx = synthetic_context(random.Random(0), **MIDFIELD, down=1, distance=10.0)
    ctx = dataclasses.replace(ctx, game=dataclasses.replace(ctx.game, season=2011))
    rng = random.Random(0)
    formation = PREDICTORS.offensive_formation(ctx, PREDICTORS.lineups(ctx, rng), rng)
    assert gbm.dropback(ctx, formation, LEAGUE) == baseline.dropback(ctx, formation, LEAGUE)
