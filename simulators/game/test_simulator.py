# START
# Tests for the game simulator (no network needed: a synthetic game).
# - test_simulation_is_valid_and_repeatable: every game runs and validates; the same seed gives the same
#   outcomes, in one process or several; a run can be replayed.
# - test_failures_are_collected: a predictor that breaks the rules is reported, not raised.
# - test_forecast: distributions and the readable summary.
# END
from events.snap import Snap
from scenarios.game import load_game_predictors
from scenarios.game.testing import synthetic_game, with_events
from simulators.game import distribution, forecast, replay, simulate_game, summarize


def test_simulation_is_valid_and_repeatable():
    ctx, predictors = synthetic_game(), load_game_predictors("baseline")
    sim = simulate_game(ctx, predictors, sims=6, seed=1)
    assert sim.failures == [] and len(sim.outcomes) == 6 and sim.example is not None
    assert sorted(sim.values("margin")) == sorted(simulate_game(ctx, predictors, 6, 1, workers=2).values("margin"))
    assert sim.values("margin") != simulate_game(ctx, predictors, 6, 2).values("margin")
    assert summarize(replay(ctx, predictors, 1, 4)) == sim.outcomes[4]
    assert all(m == p["HOME"] - p["AWAY"] for m, p in zip(sim.values("margin"), sim.values("points")))
    assert sum(sim.team("HOME", "pass_yds")) == sum(sim.player("HOME-QB1", "pass_yds")) + sum(sim.player("HOME-QB2", "pass_yds"))
    assert sim.player("HOME-K1", "pass_yds") == [0.0] * 6


def test_failures_are_collected():
    broken = with_events(load_game_predictors("baseline"), snap=lambda *args: Snap("lateral"))
    sim = simulate_game(synthetic_game(), broken, sims=3)
    assert sim.outcomes == [] and len(sim.failures) == 3
    assert all(message.startswith("IllegalChoice") for _, message, _ in sim.failures)


def test_forecast():
    assert distribution(range(100)) == {"mean": 49.5, 10: 10, 25: 25, 50: 50, 75: 75, 90: 90}
    text = forecast(simulate_game(synthetic_game(), load_game_predictors("baseline"), sims=6))
    assert "HOME wins" in text and "HOME QB1 (passing)" in text and "margin (HOME - AWAY)" in text
