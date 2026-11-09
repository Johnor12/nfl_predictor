# START
# Play scenario inputs ("the play context").
# - Game, Player, Situation, PlaySummary, PlayContext: frozen dataclasses describing the world before the play.
# - KINDS / FREE_KICKS: the kinds of play a situation can call for.
# - validate_context(ctx) -> list[str]: problems with an input (empty list if it's usable).
# Coordinates: Situation.x is the ball's yard line measured from the offense's own goal line (0-100).
#   For free kicks the kicking team is the offense. For a try, x is the two-point spot; the play scenario
#   moves the line of scrimmage to the kick spot if the offense sends out its kicking unit.
# END
from dataclasses import dataclass
from functools import cached_property

KINDS = ("scrimmage", "try", "kickoff", "safety_kick")
FREE_KICKS = ("kickoff", "safety_kick")
POSITIONS = ("QB", "RB", "FB", "WR", "TE", "OL", "DL", "LB", "DB", "K", "P", "LS")


@dataclass(frozen=True)
class Game:
    game_id: str
    season: int
    week: int
    home: str
    away: str
    neutral_site: bool = False
    roof: str | None = None
    surface: str | None = None
    temperature: float | None = None
    wind: float | None = None
    stadium: str | None = None
    start_time: str | None = None
    home_coach: str | None = None
    away_coach: str | None = None
    referee: str | None = None


@dataclass(frozen=True)
class Player:
    id: str
    name: str
    team: str
    position: str                              # one of POSITIONS
    jersey: int | None = None
    depth: tuple[tuple[str, int], ...] = ()    # depth chart (slot, rank) pairs, e.g. ("RB", 1), ("KR", 2)
    years_exp: int | None = None
    draft_pick: int | None = None              # overall pick; None if undrafted
    season_stats: tuple[tuple[str, float], ...] = ()  # this season's totals before this game

    def rank(self, slot: str) -> int | None:
        ranks = [r for s, r in self.depth if s == slot]
        return min(ranks) if ranks else None


@dataclass(frozen=True)
class Situation:
    kind: str
    offense: str
    defense: str
    x: float
    down: int | None
    distance: float | None
    score: dict[str, int]
    quarter: int
    clock: float               # seconds left in the quarter
    clock_running: bool
    play_clock: int
    timeouts: dict[str, int]


@dataclass(frozen=True)
class PlaySummary:
    offense: str
    kind: str      # run, pass, punt, field_goal, kickoff, ...
    yards: float
    result: str    # short description of what happened


@dataclass(frozen=True)
class PlayContext:
    game: Game
    situation: Situation
    players: tuple[Player, ...]          # active players on both teams
    history: tuple[PlaySummary, ...] = ()

    @cached_property
    def by_id(self) -> dict[str, Player]:
        return {p.id: p for p in self.players}

    def roster(self, team: str) -> tuple[Player, ...]:
        return tuple(p for p in self.players if p.team == team)


def validate_context(ctx: PlayContext) -> list[str]:
    s, g = ctx.situation, ctx.game
    errors = []
    if s.kind not in KINDS:
        errors.append(f"unknown kind {s.kind}")
    if {s.offense, s.defense} != {g.home, g.away}:
        errors.append(f"teams {s.offense}/{s.defense} don't match game {g.away}@{g.home}")
    if not 0 < s.x < 100:
        errors.append(f"ball at {s.x} is not in the field of play")
    if s.kind == "scrimmage":
        if s.down not in (1, 2, 3, 4):
            errors.append(f"down {s.down}")
        if s.distance is None or not 0 < s.distance <= 100 - s.x + 1e-9:
            errors.append(f"distance {s.distance} at x={s.x}")
    if set(s.score) != {s.offense, s.defense} or min(s.score.values()) < 0:
        errors.append(f"score {s.score}")
    if set(s.timeouts) != {s.offense, s.defense} or not all(0 <= t <= 3 for t in s.timeouts.values()):
        errors.append(f"timeouts {s.timeouts}")
    if s.quarter < 1 or not 0 <= s.clock <= 900:
        errors.append(f"clock q{s.quarter} {s.clock}")
    if len(ctx.by_id) != len(ctx.players):
        errors.append("duplicate player ids")
    for team in (s.offense, s.defense):
        roster = ctx.roster(team)
        if len(roster) < 22:
            errors.append(f"{team} has only {len(roster)} active players")
        for pos in ("QB", "OL", "K"):
            if not any(p.position == pos for p in roster):
                errors.append(f"{team} has no active {pos}")
    for p in ctx.players:
        if p.position not in POSITIONS:
            errors.append(f"{p.name} has unknown position {p.position}")
    return errors
