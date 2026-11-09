# START
# Field geometry and personnel/formation rules shared by the play modules.
# - rel(ctx, team, x) / to_x(ctx, team, r): convert between play coordinates and a team's yard line
#   (distance from its own goal line; < 0 is its own end zone, > 100 the opponent's).
# - other(ctx, team): the opponent.
# - clamp_x(x): keep a spot between the end lines.
# - line_of_scrimmage(ctx, rules, lineups): the snap spot (a kicked try moves it to the kick line).
# - eligible_receivers(ctx, formation): ends of the line and backs, minus a quarterback under center.
# - field_goal_distance(rules, los): kick distance from a line of scrimmage (end zone + holder depth added).
# - lineup_errors(ctx, lineups) / formation_errors(ctx, lineups, formation): legality problems.
# END
from scenarios.play.context import PlayContext


def rel(ctx: PlayContext, team: str, x: float) -> float:
    return x if team == ctx.situation.offense else 100 - x


def to_x(ctx: PlayContext, team: str, r: float) -> float:
    return r if team == ctx.situation.offense else 100 - r


def other(ctx: PlayContext, team: str) -> str:
    s = ctx.situation
    return s.defense if team == s.offense else s.offense


def clamp_x(x: float) -> float:
    return min(110.0, max(-10.0, x))


def line_of_scrimmage(ctx, rules, lineups) -> float:
    s = ctx.situation
    if s.kind == "try" and lineups.offense.unit == "field_goal":  # x is the two-point spot; kicks go from farther back
        return s.x - (rules.pat_line - rules.two_point_line)
    return s.x


def field_goal_distance(rules, los) -> int:
    return round(100 - los + rules.end_zone_depth + rules.field_goal_snap_depth)


def eligible_receivers(ctx, formation) -> tuple[str, ...]:
    ends = (formation.line[0], formation.line[-1])
    backs = tuple(p for p in formation.backfield if not (p == formation.qb and formation.under_center))
    return tuple(p for p in ends + backs if ctx.by_id[p].position not in ("OL",))


def lineup_errors(ctx, lineups) -> list[str]:
    s = ctx.situation
    errors = []
    for team, lineup in ((s.offense, lineups.offense), (s.defense, lineups.defense)):
        if len(lineup.players) != 11 or len(set(lineup.players)) != 11:
            errors.append(f"{team} {lineup.unit} has {len(set(lineup.players))} distinct players")
        for pid in lineup.players:
            p = ctx.by_id.get(pid)
            if p is None or p.team != team:
                errors.append(f"{pid} is not an active {team} player")
    return errors


def formation_errors(ctx, lineups, f) -> list[str]:
    errors = []
    if sorted(f.line + f.backfield) != sorted(lineups.offense.players):
        errors.append("formation players don't match the offensive lineup")
    if len(f.line) < 7 or len(f.backfield) > 4:
        errors.append(f"{len(f.line)} on the line, {len(f.backfield)} in the backfield")
    if f.qb not in f.backfield:
        errors.append("snap receiver must be in the backfield")
    if lineups.offense.unit in ("offense", "victory"):
        jerseys = [ctx.by_id[p].jersey for p in f.line]
        if None not in jerseys and sum(50 <= j <= 79 for j in jerseys) < 5:
            errors.append("fewer than 5 players numbered 50-79 on the line")
    return errors
