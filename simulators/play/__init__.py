# START
# The play simulator: runs the play scenario over many inputs and collects outcome summaries.
# - simulate_plays(contexts, predictors, sims=1, seed=0, examples=30) -> PlaySimulation.
# - simulate_play(ctx, predictors, sims=1, seed=0, index=0) -> (results, failures): one context's PlayResults.
# - summarize(result) -> dict: one simulated play, with the same keys nflverse uses for a real one.
# - PlaySimulation: outcomes, failures, and example results.
# END
from simulators.play.simulator import PlaySimulation, simulate_play, simulate_plays, summarize

__all__ = ["simulate_plays", "simulate_play", "summarize", "PlaySimulation"]
