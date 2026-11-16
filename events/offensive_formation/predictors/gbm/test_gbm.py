# START
# Tests of the trained offensive formation predictor (no network needed; they use the committed model files).
# - test_the_model_reads_the_situation_and_the_personnel: more shotgun on third and long than on first and
#   ten, and less with two backs and two tight ends on the field than with one back and one tight end.
# - test_the_model_reads_the_team: more shotgun for a team that has lived in it than for one that hasn't.
# - test_plays_are_valid: synthetic plays with the trained formation predictor pass the validator.
# - test_a_season_before_the_first_model_gets_the_baseline.
# - test_other_units_get_the_baseline: a punt unit's rate isn't the model's.
# END
import dataclasses
import random

from events.lineups import Lineup, Lineups
from events.offensive_formation.predictors import baseline, gbm
from scenarios.play import load_predictors, run_play, validate_play
from scenarios.play.testing import synthetic_context, with_history

PREDICTORS = load_predictors("baseline", offensive_formation="gbm")
MIDFIELD = dict(kind="scrimmage", offense="HOME", defense="AWAY", x=50.0, quarter=2, clock=600.0,
                score={"HOME": 10, "AWAY": 10})


def _lineups(group="11", unit="offense"):
    return Lineups(Lineup(unit, group, ()), Lineup("defense", "nickel", ()))


def _rate(group="11", **situation):
    ctx = synthetic_context(random.Random(0), **{**MIDFIELD, **situation})
    return gbm.shotgun_rate(ctx, _lineups(group))


def test_the_model_reads_the_situation_and_the_personnel():
    assert _rate(down=3, distance=12.0) > 0.9 > _rate(down=1, distance=10.0)
    assert _rate(down=1, distance=10.0) > _rate("22", down=1, distance=10.0) + 0.3


def test_the_model_reads_the_team():
    ctx = synthetic_context(random.Random(0), **MIDFIELD, down=1, distance=10.0)
    often, seldom = (with_history(ctx, "HOME", {"plays": 600.0, "shotgun": shotgun}) for shotgun in (510.0, 240.0))
    assert gbm.shotgun_rate(often, _lineups()) > gbm.shotgun_rate(seldom, _lineups()) + 0.2


def test_plays_are_valid():
    for seed in range(500):
        rng = random.Random(seed)
        assert validate_play(run_play(synthetic_context(rng), PREDICTORS, rng)) == [], seed


def test_a_season_before_the_first_model_gets_the_baseline():
    ctx = synthetic_context(random.Random(0), **MIDFIELD, down=1, distance=10.0)
    ctx = dataclasses.replace(ctx, game=dataclasses.replace(ctx.game, season=2011))
    assert gbm.shotgun_rate(ctx, _lineups()) == baseline.shotgun_rate(ctx, _lineups())


def test_other_units_get_the_baseline():
    ctx = synthetic_context(random.Random(0), **MIDFIELD, down=4, distance=10.0)
    punt = _lineups(None, "punt")
    assert gbm.shotgun_rate(ctx, punt) == baseline.shotgun_rate(ctx, punt)
