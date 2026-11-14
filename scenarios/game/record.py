# START
# The game record (the timeline) and the game result.
# - Stoppage(kind, quarter, clock, team): something between plays: timeout (called by team, or taken instead
#   of a 10-second runoff), runoff, two_minute_warning, or period_end.
# - GameResult: the record (in order: the Toss of each coin toss, every PlayResult, and the Stoppages), the
#   final score, winner (None for a tie), periods played, player and team stats (the sum of the plays'), and
#   absences (player, index of the first play missed, plays missed; 999 is the rest of the game).
#   result.plays is the PlayResults alone.
# END
from dataclasses import dataclass
from functools import cached_property

from scenarios.game.context import GameContext
from scenarios.play import PlayResult


@dataclass(frozen=True)
class Stoppage:
    kind: str                      # timeout, runoff, two_minute_warning, period_end
    quarter: int
    clock: float                   # seconds left in the period
    team: str | None = None        # who was charged a timeout


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
