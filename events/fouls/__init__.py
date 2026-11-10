# START
# The fouls event: fouls during and after the play (see README.md).
# - Predictor: predict(ctx, lineups, record, allowed_fouls, rng) -> tuple[Foul, ...].
# - Foul: type, team, player, spot, and timing. Also the type of a pre-snap foul (events/pre_snap).
# END
from dataclasses import dataclass


@dataclass(frozen=True)
class Foul:
    type: str                      # a key of the play scenario's foul catalog (play.CATALOG)
    team: str
    player: str
    x: float                       # spot of the foul
    timing: str                    # presnap, snap, live, return, after (see scenarios/play/penalties.py)
