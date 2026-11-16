# START
# The challenge event: whether a head coach challenges the play just run, and whether he wins (see README.md).
# - Predictor: predict(ctx, outcome, allowed, rng) -> Challenge | None. ctx is the PlayContext of the play
#   just run, outcome its summary (scenarios.play.summarize), allowed the teams that may challenge it.
# - Challenge: the team that challenged, and whether the ruling was reversed.
# END
from dataclasses import dataclass


@dataclass(frozen=True)
class Challenge:
    team: str
    won: bool                      # the ruling on the field was reversed
