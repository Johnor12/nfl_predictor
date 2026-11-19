# START
# Tests of the trained snap predictor (no network needed; they use the committed model files).
# - test_the_model_reads_the_situation: it passes more on third and long than on second and short, and more
#   when it trails late than when it leads.
# - test_the_model_reads_the_formation: it passes more from the shotgun than from under center.
# - test_the_model_reads_the_team: an offense that has passed more than its situations called for passes more.
# - test_plays_are_valid: synthetic plays with the trained snap predictor pass the validator.
# - test_a_season_before_the_first_model_gets_the_baseline.
# - test_features_read_the_game_so_far: the offense's dropbacks, runs, drive, and last play, from the history.
# - test_features_read_the_personnel: a group's backs, tight ends, and extra linemen; nan without one.
# END
import dataclasses
import math
import random

from events.situation import NAMES, features, personnel
from events.snap.predictors import baseline, gbm
from scenarios.play import PlaySummary, load_predictors, run_play, validate_play
from scenarios.play.testing import synthetic_context, with_history

PREDICTORS = load_predictors("baseline", snap="gbm")
MIDFIELD = dict(kind="scrimmage", offense="HOME", defense="AWAY", x=50.0, quarter=2, clock=600.0,
                score={"HOME": 10, "AWAY": 10})


def _lined_up(ctx):
    rng = random.Random(0)
    lineups = PREDICTORS.lineups(ctx, rng)
    formation = PREDICTORS.offensive_formation(ctx, lineups, rng)
    return lineups, formation, PREDICTORS.defensive_formation(ctx, lineups, formation, rng)


def _rate(**situation):
    ctx = synthetic_context(random.Random(0), **{**MIDFIELD, **situation})
    return gbm.pass_rate(ctx, *_lined_up(ctx))


def test_the_model_reads_the_situation():
    assert _rate(down=3, distance=12.0) > 0.8 > 0.5 > _rate(down=2, distance=1.0)
    late = dict(down=1, distance=10.0, quarter=4, clock=240.0)
    assert _rate(**late, score={"HOME": 10, "AWAY": 20}) > _rate(**late, score={"HOME": 20, "AWAY": 10}) + 0.4


def test_the_model_reads_the_formation():
    ctx = synthetic_context(random.Random(0), **MIDFIELD, down=1, distance=10.0)
    lineups, formation, defense = _lined_up(ctx)
    shotgun, under_center = (dataclasses.replace(formation, under_center=under) for under in (False, True))
    assert gbm.pass_rate(ctx, lineups, shotgun, defense) > gbm.pass_rate(ctx, lineups, under_center, defense) + 0.15


def test_the_model_reads_the_team():
    ctx = synthetic_context(random.Random(0), **MIDFIELD, down=1, distance=10.0)
    rate = lambda over: gbm.pass_rate(with_history(ctx, "HOME", {"plays": 600.0, "dropbacks_over": over}), *_lined_up(ctx))  # noqa: E731
    assert rate(45.0) > rate(-45.0) + 0.03


def test_plays_are_valid():
    for seed in range(500):
        rng = random.Random(seed)
        assert validate_play(run_play(synthetic_context(rng), PREDICTORS, rng)) == [], seed


def test_a_season_before_the_first_model_gets_the_baseline():
    ctx = synthetic_context(random.Random(0), **MIDFIELD, down=1, distance=10.0)
    ctx = dataclasses.replace(ctx, game=dataclasses.replace(ctx.game, season=2011))
    lined_up = _lined_up(ctx)
    assert gbm.pass_rate(ctx, *lined_up) == baseline.pass_rate(ctx, *lined_up)


def test_features_read_the_game_so_far():
    plays = [("HOME", "pass", 12.0), ("AWAY", "run", 3.0), ("AWAY", "punt", 0.0), ("HOME", "run", 4.0),
             ("HOME", "sack", -6.0), ("HOME", "no_play", 0.0)]
    ctx = synthetic_context(random.Random(0), **MIDFIELD, down=3, distance=12.0)
    ctx = dataclasses.replace(ctx, history=tuple(PlaySummary(team, kind, yards, "") for team, kind, yards in plays))
    row = dict(zip(NAMES, features(ctx)))
    assert (row["game_passes"], row["game_runs"], row["drive_plays"]) == (2, 1, 2)
    assert (row["last_pass"], row["last_yards"]) == (True, -6.0)  # the sack, not the penalty after it



def test_features_read_the_personnel():
    assert personnel("12+") == [1, 2, 1]
    assert all(math.isnan(value) for value in personnel(None))
