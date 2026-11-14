# START
# Tests across the events' predictor implementations (no network needed).
# - test_baseline_plays_are_valid: thousands of synthetic plays with every baseline predictor pass the validator.
# - test_load_predictors_rejects_unknown_events.
# - test_baseline_timeouts_need_a_timeout: only a team with a timeout left calls one.
# END
import random

import pytest

from scenarios.play import load_predictors, run_play, validate_play
from scenarios.play.testing import synthetic_context


def test_baseline_plays_are_valid():
    predictors = load_predictors("baseline")
    for seed in range(3000):
        rng = random.Random(seed)
        result = run_play(synthetic_context(rng), predictors, rng)
        assert validate_play(result) == [], seed


def test_load_predictors_rejects_unknown_events():
    with pytest.raises(ValueError):
        load_predictors("baseline", handoff="baseline")


def test_baseline_timeouts_need_a_timeout():
    from scenarios.game import load_game_predictors
    timeout = load_game_predictors("baseline").timeout
    late = dict(kind="scrimmage", quarter=4, clock=100.0, clock_running=True, x=50.0, down=1, distance=10.0)
    rng = random.Random(0)
    ctx = synthetic_context(rng, **late, score={"HOME": 20, "AWAY": 17}, timeouts={"HOME": 0, "AWAY": 3},
                            offense="HOME", defense="AWAY")
    calls = [timeout(ctx, rng) for _ in range(500)]
    assert set(calls) == {"AWAY", None} and calls.count("AWAY") > 100  # the trailing defense stops the clock
    ctx = synthetic_context(rng, **late, score={"HOME": 20, "AWAY": 17}, timeouts={"HOME": 0, "AWAY": 0},
                            offense="HOME", defense="AWAY")
    assert {timeout(ctx, rng) for _ in range(200)} == {None}
