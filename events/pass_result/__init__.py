# START
# The pass result event: complete, incomplete, or intercepted (see README.md).
# - Predictor: predict(ctx, lineups, target, rng) -> PassResult.
# - PassResult: the result, who defended or intercepted the pass, and how long the ball was in the air.
# - RESULTS: the legal results.
# END
from dataclasses import dataclass

RESULTS = ("complete", "incomplete", "intercepted")


@dataclass(frozen=True)
class PassResult:
    result: str                    # one of RESULTS
    defender: str | None = None    # who defended or intercepted it
    seconds: float = 0.0           # from the throw until the pass is caught, intercepted, or dead
