# START
# The lineups event: which 11 players each team puts on the field (see README.md).
# - Predictor: predict(ctx, rng) -> Lineups.
# - Lineup: one team's unit, personnel label, and 11 player ids.
# - Lineups: the offense's and the defense's Lineup.
# Offense units: offense, punt, field_goal, victory, kickoff, onside_kickoff.
# Defense units: defense, punt_return, field_goal_block, kick_return.
# END
from dataclasses import dataclass


@dataclass(frozen=True)
class Lineup:
    unit: str
    personnel: str | None          # e.g. "11" (1 RB, 1 TE) for the offense, "nickel" for the defense
    players: tuple[str, ...]


@dataclass(frozen=True)
class Lineups:
    offense: Lineup
    defense: Lineup
