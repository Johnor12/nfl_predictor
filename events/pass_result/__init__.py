# START
# The pass result event: complete, incomplete, or intercepted (see README.md).
# - Predictor: predict(ctx, lineups, target, rng) -> PassResult.
# - PassResult: the result and who defended or intercepted the pass.
# - RESULTS: the legal results.
# END
from dataclasses import dataclass

RESULTS = ("complete", "incomplete", "intercepted")


@dataclass(frozen=True)
class PassResult:
    result: str                    # one of RESULTS
    defender: str | None = None    # who defended or intercepted it
