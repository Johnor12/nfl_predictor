# START
# The play record (facts) and the play result (everything computed from them).
# - Sack, Pass, Carry, LooseBall, Kick: facts the chain records alongside the event outputs it keeps as-is
#   (Lineups, Formation, DefensiveFormation, PreSnap, Snap, PassRush, Foul, Injury from events/).
# - Dead: how and where the ball became dead and who is entitled to it (also used for penalty-adjusted results).
# - PlayResult: the record plus enforcement, scores, stats, clock, and the next situation.
# - facts(record, type): the record's facts of one type, in order.
# All spots are play coordinates (yards from the play's offense's own goal line).
# END
from dataclasses import dataclass, field

from events.fouls import Foul
from events.injuries import Injury
from scenarios.play.context import PlayContext, Situation


@dataclass(frozen=True)
class Sack:
    passer: str
    sackers: tuple[str, ...]
    x: float


@dataclass(frozen=True)
class Pass:
    passer: str
    receiver: str | None           # None on throwaways and spikes
    x: float                       # target spot (where it was caught or would have been)
    direction: str | None
    result: str                    # complete, incomplete, intercepted, throwaway, spike
    defender: str | None = None


@dataclass(frozen=True)
class Carry:
    player: str
    team: str
    kind: str                      # run, scramble, kneel, catch, interception, punt_return, kick_return, recovery
    start: float
    end: float                     # spot where the carry ended (spot of a fumble; goal line on a touchdown)
    how: str                       # tackled, out_of_bounds, fumble, down, touchdown
    tacklers: tuple[str, ...] = ()
    forced_by: str | None = None
    seconds: float = 0.0


@dataclass(frozen=True)
class LooseBall:
    cause: str                     # fumble, bad_snap, muff, blocked_kick
    x: float
    last_team: str                 # team that last possessed (or touched, for a muff) the ball
    fumbler: str | None
    forced_by: str | None
    team: str | None               # recovering team, None if out of bounds
    player: str | None
    recovery_x: float
    seconds: float = 0.0


@dataclass(frozen=True)
class Kick:
    kind: str                      # punt, field_goal, pat, kickoff, safety_kick, onside_kickoff
    kicker: str
    x: float                       # spot of the kick (line of scrimmage, or free kick line)
    land: float | None             # where it was caught, downed, landed, or went out (None for place kicks)
    result: str                    # punt/free kick: the PuntResult / KickResult result, or out_of_bounds, short, blocked;
                                   # place kick: good, no_good, blocked
    player: str | None = None      # returner / blocker / recovering player
    seconds: float = 0.0


@dataclass(frozen=True)
class Dead:
    team: str                      # team entitled to the ball
    x: float                       # where the next play starts
    how: str                       # tackled, out_of_bounds, down, incomplete, touchdown, safety, touchback, kick_good,
                                   # kick_missed, fair_catch, downed, recovered, kick_out_of_bounds, kick_short, penalty
    kick: bool = False             # the ball was kicked to the receiving side: whoever has it starts a new series
    series: str = "normal"         # normal (next down), replay (same down), loss (loss of down), first (automatic first down)
    no_play: bool = False
    succeeding: float = 0.0        # yards to move the next play's spot after a score (for the next offense, signed)


@dataclass(frozen=True)
class PlayResult:
    context: PlayContext
    record: tuple
    live: Dead | None              # how the live ball ended, before penalties (None if there was no snap)
    final: Dead                    # after penalty enforcement
    accepted: tuple[Foul, ...]
    declined: tuple[Foul, ...]
    penalty_yards: dict[str, float]  # yards assessed against each team
    scores: tuple[tuple[str, int, str], ...]  # (team, points, how)
    next: Situation
    stats: dict[str, dict[str, float]]
    team_stats: dict[str, dict[str, float]]
    elapsed: float                 # game seconds used (pre-snap runoff plus the play)
    clock_after: str               # running, ready (restarts on ready-for-play), snap (stopped until the snap)
    untimed_down: bool
    runoff_option: bool            # 10-second runoff option for the defense
    injuries: tuple[Injury, ...] = field(default=())

    @property
    def no_play(self) -> bool:
        return self.final.no_play


def facts(record, kind) -> list:
    return [f for f in record if isinstance(f, kind)]
