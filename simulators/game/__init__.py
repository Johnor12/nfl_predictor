# START
# The game simulator: plays the game scenario many times and presents the distributions.
# - simulate_game(ctx, predictors, sims=1000, seed=0, workers=1) -> GameSimulation.
# - summarize(result) -> dict: one simulated game, with the same keys as a real one (shared.nflverse.RealGame).
# - GameSimulation: outcomes, failures, an example game; values(key), team(team, stat), player(id, stat).
# - replay(ctx, predictors, seed, run) -> GameResult: one of a simulation's runs again, in full.
# - distribution(values) -> dict / forecast(sim) -> str: means and percentiles, and a readable summary.
# - CLI: `python -m simulators.game 2026_10_NE_DET [--sims 1000]` forecasts a real game.
# END
from simulators.game.forecast import distribution, forecast
from simulators.game.simulator import GameSimulation, replay, simulate_game, summarize

__all__ = ["simulate_game", "summarize", "GameSimulation", "replay", "distribution", "forecast"]
