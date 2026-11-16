# START
# The pass rush event: what happens to the quarterback on a dropback (see README.md).
# - Predictor: predict(ctx, lineups, formation, defense, rng) -> PassRush.
# - PassRush: rushers, the result, time until it happened, who hit or sacked the quarterback, and what a
#   charter adds: who hurried his throw, and who came on a blitz.
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
    hurriers: tuple[str, ...] = ()  # defenders who hurried the throw without hitting him
    blitzers: tuple[str, ...] = ()  # defenders who came on a blitz
