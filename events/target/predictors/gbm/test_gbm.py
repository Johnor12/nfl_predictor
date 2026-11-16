# START
# Tests of the trained target predictor (no network needed; they use the committed model files).
# - test_the_model_reads_the_receiver: a receiver who has been thrown to deep is thrown to deeper than one
#   who catches short passes, and a back shorter than a receiver.
# - test_air_yards_stay_on_the_field: near the goal line a pass doesn't go past the end line.
# - test_plays_are_valid: synthetic plays with the trained target predictor pass the validator.
# - test_a_season_before_the_first_model_gets_the_baseline.
# END
import dataclasses
import random

from events.target.predictors import baseline, gbm
from events.target.predictors.gbm.inputs import CUTS, features
from scenarios.play import eligible_receivers, load_predictors, run_play, validate_play
from scenarios.play.testing import synthetic_context, with_history

PREDICTORS = load_predictors("baseline", target="gbm")
MIDFIELD = dict(kind="scrimmage", offense="HOME", defense="AWAY", x=50.0, quarter=2, clock=600.0,
                score={"HOME": 10, "AWAY": 10}, down=1, distance=10.0)


def _past_ten(receiver, history=None):
    """The model's probability that a pass to the receiver travels 10 yards or more."""
    ctx = synthetic_context(random.Random(0), **MIDFIELD)
    ctx = with_history(ctx, receiver, history) if history else ctx
    return gbm.load_model(2026)(features(ctx, ctx.by_id[receiver], True))[CUTS.index(10)]


def test_the_model_reads_the_receiver():
    deep = _past_ten("HOME-WR1", {"targets": 100.0, "target_air_yds": 1600.0})
    short = _past_ten("HOME-WR1", {"targets": 100.0, "target_air_yds": 500.0})
    assert deep > short + 0.15
    assert _past_ten("HOME-WR1") > _past_ten("HOME-RB1") + 0.15


def test_air_yards_stay_on_the_field():
    for seed in range(200):
        rng = random.Random(seed)
        ctx = synthetic_context(rng, **{**MIDFIELD, "x": 97.0, "distance": 3.0})
        lineups = PREDICTORS.lineups(ctx, rng)
        formation = PREDICTORS.offensive_formation(ctx, lineups, rng)
        target = gbm.predict(ctx, lineups, formation, eligible_receivers(ctx, formation), rng)
        assert 97 + target.air_yards <= 108


def test_plays_are_valid():
    for seed in range(500):
        rng = random.Random(seed)
        assert validate_play(run_play(synthetic_context(rng), PREDICTORS, rng)) == [], seed


def test_a_season_before_the_first_model_gets_the_baseline():
    ctx = synthetic_context(random.Random(0), **MIDFIELD)
    ctx = dataclasses.replace(ctx, game=dataclasses.replace(ctx.game, season=2011))
    lineups = PREDICTORS.lineups(ctx, random.Random(0))
    formation = PREDICTORS.offensive_formation(ctx, lineups, random.Random(0))
    draws = [module.air_yards(ctx, formation, "HOME-WR1", random.Random(1)) for module in (gbm, baseline)]
    assert draws[0] == draws[1]
