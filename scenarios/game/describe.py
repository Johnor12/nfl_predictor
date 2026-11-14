# START
# Human-readable narration of a game, for audits and debugging.
# - describe_game(result, plays=False) -> str: the final score, points by period, each team's totals, and its
#   leading passer, rusher, and receiver. With plays=True, the whole timeline follows: every coin toss, play
#   (the play scenario's narration), and stoppage.
# END
from scenarios.coin_toss import Toss
from scenarios.game.record import Stoppage
from scenarios.play import describe_play

TEAM_LINE = (("pass yds", "pass_yds"), ("rush yds", "rush_yds"), ("sacked", "sacked"), ("int", "int_thrown"),
             ("fumbles lost", "fumbles_lost"), ("penalties", "penalties"), ("punts", "punts"))
LEADERS = (("passing", "pass_yds"), ("rushing", "rush_yds"), ("receiving", "rec_yds"))


def _by_period(result, team) -> list[int]:
    points = [0] * result.quarters
    for play in result.plays:
        points[play.context.situation.quarter - 1] += sum(p for scorer, p, _ in play.scores if scorer == team)
    return points


def _stoppage(entry) -> str:
    clock = f"{int(entry.clock // 60)}:{int(entry.clock % 60):02d}"
    who = f" {entry.team}" if entry.team else ""
    return f"-- {entry.kind.replace('_', ' ')}{who} (Q{entry.quarter} {clock})"


def describe_game(result, plays: bool = False) -> str:
    game = result.context.game
    names = {p.id: p.name for p in result.context.players}
    ending = "" if result.quarters == 4 else " (OT)"
    lines = [f"{game.away} {result.score[game.away]} @ {game.home} {result.score[game.home]}{ending}, "
             f"{len(result.plays)} plays"]
    for team in (game.away, game.home):
        totals = result.team_stats[team]
        lines.append(f"{team}: " + " ".join(map(str, _by_period(result, team))) + " | "
                     + ", ".join(f"{label} {totals.get(stat, 0):.0f}" for label, stat in TEAM_LINE))
        roster = [p.id for p in result.context.players if p.team == team]
        for label, stat in LEADERS:
            leader = max(roster, key=lambda pid: result.stats.get(pid, {}).get(stat, 0.0))
            lines.append(f"  {label}: {names[leader]} {result.stats.get(leader, {}).get(stat, 0.0):.0f}")
    if plays:
        for entry in result.record:
            if isinstance(entry, Toss):
                lines.append(f"-- coin toss: {entry.winner} wins and chooses to {entry.choice}; {entry.kicking} kicks off")
            elif isinstance(entry, Stoppage):
                lines.append(_stoppage(entry))
            else:
                lines.append(describe_play(entry))
    return "\n".join(lines)
