# START
# The play record (facts) and the play result (everything computed from them).
# - Sack, Pass, Carry, LooseBall, Kick: facts the chain records alongside the event outputs it keeps as-is
#   (Lineups, Formation, DefensiveFormation, PreSnap, Snap, PassRush, Foul, Injury from events/).
# - Dead: how and where the ball became dead and who is entitled to it (also used for penalty-adjusted results).
# - PlayResult: the record plus enforcement, scores, stats, clock, the next situation, and disqualifications.
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
    seconds: float = 0.0           # in the air
    coverage: str | None = None    # charted: the defender in coverage, a drop, a bad throw
    drop: bool = False
    bad_throw: bool = False


@dataclass(frozen=True)
class Carry:
    player: str
    team: str
    kind: str                      # run, scramble, kneel, catch, interception, punt_return, kick_return, recovery
    start: float
    end: float                     # spot where the carry ended (spot of a fumble; goal line on a touchdown)
    how: str                       # tackled, out_of_bounds, fumble, down, lateral, touchdown
    tacklers: tuple[str, ...] = ()
    forced_by: str | None = None
    seconds: float = 0.0
    lateral: bool = False          # the ball came by a lateral: same kind as the carry before it, from where it ended
    missed: tuple[str, ...] = ()   # charted: who missed a tackle, the tackles broken, the yards before contact
    broken: int = 0
    contact: float | None = None


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
    kind: str                      # punt, field_goal, pat, fair_catch_kick, kickoff, safety_kick, onside_kickoff
    kicker: str
    x: float                       # spot of the kick (line of scrimmage, or free kick line)
    land: float | None             # where it was caught, downed, landed, or went out (None for place kicks)
    result: str                    # punt/free kick: the PuntResult / KickResult result, or out_of_bounds, short, blocked,
                                   # illegal_touch (the kicking team recovered a free kick short of 10 yards);
                                   # place kick: good, no_good, blocked (a fair-catch kick: good or no_good)
    player: str | None = None      # returner / blocker / recovering player
    seconds: float = 0.0


@dataclass(frozen=True)
class Dead:
    team: str                      # team entitled to the ball
    x: float                       # where the next play starts
    how: str                       # tackled, out_of_bounds, down, incomplete, touchdown, safety, touchback, kick_good,
                                   # kick_missed, fair_catch, downed, recovered, kick_out_of_bounds, kick_short,
                                   # illegal_touch, penalty, offsetting
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
    disqualified: tuple[str, ...] = ()      # players ejected on this play, out for the rest of the game
    warned: frozenset[str] = frozenset()    # the next play's PlayContext.warned

    @property
    def no_play(self) -> bool:
        return self.final.no_play


def facts(record, kind) -> list:
    return [f for f in record if isinstance(f, kind)]
