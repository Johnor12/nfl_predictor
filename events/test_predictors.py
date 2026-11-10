# START
# Tests across the events' predictor implementations (no network needed).
# - test_baseline_plays_are_valid: thousands of synthetic plays with every baseline predictor pass the validator.
# - test_load_predictors_rejects_unknown_events.
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
