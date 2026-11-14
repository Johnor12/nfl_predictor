# START
# Simulating the play scenario many times.
# - simulate_plays(contexts, predictors, sims=1, seed=0, examples=30) -> PlaySimulation: runs every context
#   `sims` times (each run has its own seed, so any play can be rerun), validates every play, and summarizes it.
# - simulate_play(ctx, predictors, sims=1, seed=0, index=0) -> (results, failures): one context's runs as
#   PlayResults, for callers that work through a season one play at a time. `index` is the context's
#   position in the simulation (it is part of each run's seed).
# - Each outcome is summarized with scenarios.play.summarize (the same keys as a real play's outcome).
# - PlaySimulation: outcomes (context, summary) for every play that ran; failures (context index, message,
#   narration or traceback) for plays that raised or broke an invariant; examples (context index, PlayResult),
#   the first run of about `examples` evenly spaced contexts.
# END
import random
import traceback
from dataclasses import dataclass, field

from scenarios.play import describe_play, run_play, summarize, validate_play


@dataclass
class PlaySimulation:
    outcomes: list = field(default_factory=list)
    failures: list = field(default_factory=list)
    examples: list = field(default_factory=list)


def simulate_play(ctx, predictors, sims: int = 1, seed: int = 0, index: int = 0) -> tuple[list, list]:
    results, failures = [], []
    for k in range(sims):
        rng = random.Random(seed * 1_000_003 + index * 101 + k)
        try:
            result = run_play(ctx, predictors, rng)
        except Exception as e:
            failures.append((index, f"{type(e).__name__}: {e}", traceback.format_exc()))
            continue
        errors = validate_play(result)
        if errors:
            failures.append((index, "; ".join(errors), describe_play(result)))
        results.append(result)
    return results, failures


def simulate_plays(contexts, predictors, sims: int = 1, seed: int = 0, examples: int = 30) -> PlaySimulation:
    sim = PlaySimulation()
    kept = set(range(0, len(contexts), max(1, len(contexts) // examples))) if examples else set()
    for i, ctx in enumerate(contexts):
        results, failures = simulate_play(ctx, predictors, sims, seed, i)
        sim.failures += failures
        sim.outcomes += [(ctx, summarize(result)) for result in results]
        if results and i in kept:
            sim.examples.append((i, results[0]))
    return sim
