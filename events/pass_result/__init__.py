# START
# The pass result event: complete, incomplete, or intercepted (see README.md).
# - Predictor: predict(ctx, lineups, target, rng) -> PassResult.
# - PassResult: the result, who defended or intercepted the pass, how long the ball was in the air, and what
#   a charter adds: the defender in coverage, and whether an incompletion was a drop or a bad throw.
# - RESULTS: the legal results.
# END
from dataclasses import dataclass

RESULTS = ("complete", "incomplete", "intercepted")


@dataclass(frozen=True)
class PassResult:
    result: str                    # one of RESULTS
    defender: str | None = None    # who defended or intercepted it
    seconds: float = 0.0           # from the throw until the pass is caught, intercepted, or dead
    coverage: str | None = None    # the defender in coverage on the receiver
    drop: bool = False             # an incompletion the receiver dropped
    bad_throw: bool = False        # an incompletion the passer missed
