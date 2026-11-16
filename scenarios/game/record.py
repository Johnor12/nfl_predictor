# START
# The game record (the timeline) and the game result.
# - Stoppage(kind, quarter, clock, team): something between plays: timeout (called by team, or taken instead
#   of a 10-second runoff), challenge_won, challenge_lost (a coach's challenge; lost, it cost the team a
#   timeout), injury_timeout (a timeout charged for an injury after the two-minute warning), excess_timeout
#   (the same for a team with none left), runoff, two_minute_warning, or period_end.
# - CHARGED: the kinds that cost the team a timeout.
# - GameResult: the record (in order: the Toss of each coin toss, every PlayResult, and the Stoppages), the
#   final score, winner (None for a tie), periods played, player and team stats (the sum of the plays'), and
#   absences (player, index of the first play missed, plays missed; 999 is the rest of the game).
#   result.plays is the PlayResults alone.
# END
from dataclasses import dataclass
from functools import cached_property

from scenarios.game.context import GameContext
from scenarios.play import PlayResult


CHARGED = ("timeout", "challenge_lost", "injury_timeout")


@dataclass(frozen=True)
class Stoppage:
    kind: str                      # timeout, challenge_won, challenge_lost, injury_timeout, excess_timeout, runoff,
                                   # two_minute_warning, period_end
    quarter: int
    clock: float                   # seconds left in the period
    team: str | None = None        # who called the timeout, challenged, or had the injured player


@dataclass(frozen=True)
class GameResult:
    context: GameContext
    record: tuple
    score: dict[str, int]
    winner: str | None
    quarters: int                  # 4, or more with overtime
    stats: dict[str, dict[str, float]]
    team_stats: dict[str, dict[str, float]]
    absences: tuple[tuple[str, int, int], ...]

    @cached_property
    def plays(self) -> tuple[PlayResult, ...]:
        return tuple(entry for entry in self.record if isinstance(entry, PlayResult))
