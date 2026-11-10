# START
# The pass rush event: what happens to the quarterback on a dropback (see README.md).
# - Predictor: predict(ctx, lineups, formation, defense, rng) -> PassRush.
# - PassRush: rushers, the result, time until it happened, and who hit or sacked the quarterback.
# - RESULTS: the legal results.
# END
from dataclasses import dataclass

RESULTS = ("throw", "sack", "scramble", "throwaway", "strip_sack")


@dataclass(frozen=True)
class PassRush:
    rushers: int
    result: str                    # one of RESULTS
    seconds: float
    hitters: tuple[str, ...] = ()  # defenders who hit the quarterback
    sackers: tuple[str, ...] = ()
    sack_yards: float = 0.0        # yards lost on a sack (>= 0)
