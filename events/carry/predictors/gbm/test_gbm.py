# START
# Tests of the trained carry predictor (no network needed; they use the committed model files).
# - test_the_models_read_the_carrier: a back who has gained more per rush is likelier to gain four, and a
#   receiver who has run after his catches likelier to gain five after this one.
# - test_the_models_know_the_goal_line: nobody gains ten yards from the three.
# - test_other_carries_are_the_baseline_s: a punt return's yards are the baseline's draw.
# - test_plays_are_valid: synthetic plays with the trained carry predictor pass the validator.
# - test_a_season_before_the_first_model_gets_the_baseline.
# END
import dataclasses
import random

from events.carry.predictors import baseline, gbm
from events.carry.predictors.gbm.inputs import CATCH_CUTS, RUN_CUTS, catch, run
from scenarios.play import load_predictors, run_play, validate_play
from scenarios.play.testing import synthetic_context, with_history

PREDICTORS = load_predictors("baseline", carry="gbm")
MIDFIELD = dict(kind="scrimmage", offense="HOME", defense="AWAY", x=50.0, quarter=2, clock=600.0,
                score={"HOME": 10, "AWAY": 10}, down=1, distance=10.0)


def _run(yards, history=None, **situation):
    """The model's probability that a run by the first back gains `yards` or more."""
    ctx = synthetic_context(random.Random(0), **{**MIDFIELD, **situation})
    ctx = with_history(ctx, "HOME-RB1", history) if history else ctx
    return gbm.load_run(2026)(run(ctx, ctx.by_id["HOME-RB1"]))[RUN_CUTS.index(yards)]


def _catch(yards, history=None, yard_line=55.0, **situation):
    """The model's probability that the first receiver gains `yards` or more after a catch at the yard line."""
    ctx = synthetic_context(random.Random(0), **{**MIDFIELD, **situation})
    ctx = with_history(ctx, "HOME-WR1", history) if history else ctx
    return gbm.load_catch(2026)(catch(ctx, ctx.by_id["HOME-WR1"], yard_line))[CATCH_CUTS.index(yards)]


def test_the_models_read_the_carrier():
    assert _run(4, {"rush_att": 200.0, "rush_yds": 1100.0}) > _run(4, {"rush_att": 200.0, "rush_yds": 640.0}) + 0.01
    assert _catch(5, {"receptions": 80.0, "rec_yac": 560.0}) > _catch(5, {"receptions": 80.0, "rec_yac": 200.0}) + 0.02


def test_the_models_know_the_goal_line():
    assert _run(10, x=97.0, distance=3.0) < 0.01 < _run(10)
    assert _catch(10, yard_line=97.0, x=90.0) < 0.01 < _catch(10)


def test_other_carries_are_the_baseline_s():
    ctx = synthetic_context(random.Random(0), **MIDFIELD)
    draws = [module.yards(ctx, "punt_return", "AWAY-DB1", 30.0, random.Random(1)) for module in (gbm, baseline)]
    assert draws[0] == draws[1]


def test_plays_are_valid():
    for seed in range(500):
        rng = random.Random(seed)
        assert validate_play(run_play(synthetic_context(rng), PREDICTORS, rng)) == [], seed


def test_a_season_before_the_first_model_gets_the_baseline():
    ctx = synthetic_context(random.Random(0), **MIDFIELD)
    ctx = dataclasses.replace(ctx, game=dataclasses.replace(ctx.game, season=2011))
    draws = [module.yards(ctx, "run", "HOME-RB1", 50.0, random.Random(1)) for module in (gbm, baseline)]
    assert draws[0] == draws[1]
