# START
# Tests for the play simulator (no network needed: synthetic contexts).
# - test_simulation_is_valid_and_repeatable: every play runs and validates; the same seed gives the same outcomes.
# - test_failures_are_collected: a predictor that breaks the rules is reported, not raised.
# END
import random

from events.snap import Snap
from scenarios.play import load_predictors
from scenarios.play.testing import scripted, synthetic_context
from simulators.play import simulate_plays


def _contexts(n=200):
    return [synthetic_context(random.Random(i)) for i in range(n)]


def test_simulation_is_valid_and_repeatable():
    predictors = load_predictors("baseline")
    sim = simulate_plays(_contexts(), predictors, sims=2, seed=1, examples=10)
    assert sim.failures == [] and len(sim.outcomes) == 400 and len(sim.examples) == 10
    assert [o for _, o in sim.outcomes] == [o for _, o in simulate_plays(_contexts(), predictors, 2, 1).outcomes]
    assert [o for _, o in sim.outcomes] != [o for _, o in simulate_plays(_contexts(), predictors, 2, 2).outcomes]


def test_failures_are_collected():
    contexts = [synthetic_context(random.Random(i), kind="scrimmage") for i in range(20)]
    broken = scripted(load_predictors("baseline"), snap=Snap("lateral"))
    sim = simulate_plays(contexts, broken)
    assert len(sim.failures) + len(sim.outcomes) == 20
    assert sim.failures and all(message.startswith("IllegalChoice") for _, message, _ in sim.failures)
