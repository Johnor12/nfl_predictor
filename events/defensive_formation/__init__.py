# START
# The defensive formation event: the defense's front and look (see README.md).
# - Predictor: predict(ctx, lineups, formation, rng) -> DefensiveFormation.
# - DefensiveFormation: box count and deep safeties.
# END
from dataclasses import dataclass


@dataclass(frozen=True)
class DefensiveFormation:
    box: int                       # defenders in the box
    deep_safeties: int
