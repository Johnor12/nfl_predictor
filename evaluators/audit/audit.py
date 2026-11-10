# START
# Running real inputs through the play simulator.
# - run_audit(season=2026, weeks=None, sims=1, seed=0, predictors=None) -> Audit: validates every real
#   context, simulates each one `sims` times (baseline predictors unless given), and pairs the outcomes.
# - Audit: plays (RealPlay), input_errors (RealPlay, message), failures (RealPlay, message, narration or
#   traceback), actual / simulated (context, outcome) pairs, examples (RealPlay, PlayResult).
# END
from dataclasses import dataclass

from shared.nflverse import real_plays
from scenarios.play import load_predictors, validate_context
from simulators.play import simulate_plays


@dataclass
class Audit:
    season: int
    plays: list
    input_errors: list
    failures: list
    actual: list
    simulated: list
    examples: list


def run_audit(season: int = 2026, weeks=None, sims: int = 1, seed: int = 0, predictors=None) -> Audit:
    plays = real_plays(season, weeks)
    sim = simulate_plays([rp.context for rp in plays], predictors or load_predictors("baseline"), sims, seed)
    return Audit(
        season, plays,
        input_errors=[(rp, error) for rp in plays for error in validate_context(rp.context)],
        failures=[(plays[i], message, detail) for i, message, detail in sim.failures],
        actual=[(rp.context, rp.actual) for rp in plays],
        simulated=sim.outcomes,
        examples=[(plays[i], result) for i, result in sim.examples],
    )
