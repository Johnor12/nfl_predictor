# START
# The predictor interface: one function per event, bundled in Predictors, plus each event's output type.
# - Predictors: dataclass of event functions; swap one with dataclasses.replace(predictors, carry=my_carry).
# - Output dataclasses: Lineup, Lineups, Formation, DefensiveFormation, PreSnap, Snap, PassRush, Target,
#   PassResult, CarryEnd, Recovery, PuntKick, KickOutcome, KickAttempt, FreeKick, Foul, Injury.
# Every predictor takes the play context first and a seeded random.Random last, and returns a sample.
# Spots ("x") are in play coordinates: yards from the play's offense's own goal line (kicking team on free kicks).
# Predictors are handed the legal options where the rules restrict them (allowed actions, eligible receivers,
# allowed fouls); the play scenario rejects anything outside them.
# END
from dataclasses import dataclass
from typing import Callable

# offense units: "offense", "punt", "field_goal", "victory", "kickoff", "onside_kickoff"
# defense units: "defense", "punt_return", "field_goal_block", "kick_return"


@dataclass(frozen=True)
class Lineup:
    unit: str
    personnel: str | None          # e.g. "11" (1 RB, 1 TE) for the offense, "nickel" for the defense
    players: tuple[str, ...]


@dataclass(frozen=True)
class Lineups:
    offense: Lineup
    defense: Lineup


@dataclass(frozen=True)
class Formation:
    name: str
    line: tuple[str, ...]          # players on the line of scrimmage, left to right
    backfield: tuple[str, ...]
    qb: str                        # player receiving the snap (quarterback, punter, or holder)
    under_center: bool


@dataclass(frozen=True)
class DefensiveFormation:
    box: int                       # defenders in the box
    deep_safeties: int


@dataclass(frozen=True)
class PreSnap:
    seconds: float                 # play clock used before the snap
    foul: "Foul | None" = None


@dataclass(frozen=True)
class Snap:
    action: str                    # run, pass, kneel, spike, punt, field_goal
    ball_to: str | None = None     # ball carrier on a run
    bad_snap: bool = False


@dataclass(frozen=True)
class PassRush:
    rushers: int
    result: str                    # throw, sack, scramble, throwaway, strip_sack
    seconds: float
    hitters: tuple[str, ...] = ()  # defenders who hit the quarterback
    sackers: tuple[str, ...] = ()
    sack_yards: float = 0.0        # yards lost on a sack (>= 0)


@dataclass(frozen=True)
class Target:
    receiver: str
    air_yards: float
    direction: str                 # left, middle, right


@dataclass(frozen=True)
class PassResult:
    result: str                    # complete, incomplete, intercepted
    defender: str | None = None    # who defended or intercepted it


@dataclass(frozen=True)
class CarryEnd:
    yards: float                   # signed, in the carrier's direction of travel
    how: str                       # tackled, out_of_bounds, fumble, down (slide, kneel, or no contact)
    tacklers: tuple[str, ...] = ()
    forced_by: str | None = None   # who forced a fumble
    seconds: float = 0.0


@dataclass(frozen=True)
class Recovery:
    team: str | None               # None if the ball went out of bounds
    player: str | None
    x: float                       # where it was recovered or went out of bounds
    seconds: float = 0.0


@dataclass(frozen=True)
class PuntKick:
    distance: float                # from the line of scrimmage to where the ball is caught, downed, or goes out
    blocked_by: str | None = None
    seconds: float = 0.0


@dataclass(frozen=True)
class KickOutcome:
    result: str                    # punts: fair_catch, return, downed, out_of_bounds, touchback, muff;
                                   # free kicks: return, touchback, fair_catch, muff, kicking_recovery
    player: str | None = None      # returner / fair catcher / muffer / recovering kicking player


@dataclass(frozen=True)
class KickAttempt:
    result: str                    # good, no_good, blocked
    blocked_by: str | None = None
    seconds: float = 0.0


@dataclass(frozen=True)
class FreeKick:
    kicker: str
    distance: float                # from the kick spot to where it lands
    out_of_bounds: bool = False
    seconds: float = 0.0           # hang time (doesn't run the game clock)


@dataclass(frozen=True)
class Foul:
    type: str                      # key of fouls.CATALOG
    team: str
    player: str
    x: float                       # spot of the foul
    timing: str                    # presnap, snap, live, return, after (see fouls.py)


@dataclass(frozen=True)
class Injury:
    player: str
    plays_out: int                 # plays missed; 999 = rest of the game


@dataclass(frozen=True)
class Predictors:
    lineups: Callable              # (ctx, rng) -> Lineups
    offensive_formation: Callable  # (ctx, lineups, rng) -> Formation
    defensive_formation: Callable  # (ctx, lineups, formation, rng) -> DefensiveFormation
    pre_snap: Callable             # (ctx, lineups, formation, allowed_fouls, rng) -> PreSnap
    snap: Callable                 # (ctx, lineups, formation, defense, allowed_actions, rng) -> Snap
    pass_rush: Callable            # (ctx, lineups, formation, defense, rng) -> PassRush
    target: Callable               # (ctx, lineups, formation, eligible, rng) -> Target
    pass_result: Callable          # (ctx, lineups, target, rng) -> PassResult
    carry: Callable                # (ctx, lineups, kind, carrier, yard_line, rng) -> CarryEnd
    loose_ball: Callable           # (ctx, lineups, cause, x, last_team, rng) -> Recovery
    punt_kick: Callable            # (ctx, lineups, punter, rng) -> PuntKick
    punt_result: Callable          # (ctx, lineups, landing_x, allowed, rng) -> KickOutcome
    kick_attempt: Callable         # (ctx, lineups, kicker, distance, rng) -> KickAttempt
    free_kick: Callable            # (ctx, lineups, onside, rng) -> FreeKick
    kick_result: Callable          # (ctx, lineups, landing_x, allowed, rng) -> KickOutcome
    fouls: Callable                # (ctx, lineups, record, allowed_fouls, rng) -> tuple[Foul, ...]
    injuries: Callable             # (ctx, lineups, record, rng) -> tuple[Injury, ...]
