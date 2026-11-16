# START
# The dropback model's inputs: what is known as the quarterback drops back, as one row of numbers.
# - NAMES: the feature names, in the model's column order. WHO: the ones about the quarterback, which the
#   model reads coarsely (shared.models).
# - RESULTS: the model's classes, in order: throw, sack, scramble.
# - features(ctx, qb, shotgun) -> list[float]: one play's values (nan where unknown): the situation and the
#   game so far (events.situation), whether the offense is in the shotgun, and the quarterback (a `Player`,
#   or None): how often he has been sacked and has scrambled per dropback, this season and over earlier
#   ones, his dropbacks this season, and his years in the league. The same function reads a simulated play
#   (predict) and a real one (train.py).
# END
import math

from events import situation, strength

RESULTS = ("throw", "sack", "scramble")
WHO = ("qb_sacked", "qb_sacked_before", "qb_scrambles", "qb_scrambles_before", "qb_dropbacks", "qb_experience")
NAMES = situation.NAMES + ("shotgun",) + WHO


def features(ctx, qb, shotgun) -> list[float]:
    if qb is None:
        return situation.features(ctx) + [shotgun] + [math.nan] * len(WHO)
    return (situation.features(ctx) + [shotgun] + strength.rates(qb, "times_sacked", "dropbacks")
            + strength.rates(qb, "scrambles", "dropbacks") + [strength.total(qb, "dropbacks"), strength.experience(qb)])
