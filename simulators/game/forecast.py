# START
# Presenting a game simulation: the distributions of its outcomes.
# - distribution(values) -> dict: mean and the 10th, 25th, 50th, 75th, and 90th percentiles.
# - forecast(sim, players=4) -> str: win probabilities; the distributions of each team's points, the margin,
#   the total, and the number of plays; and stat lines for each team's quarterback, kicker, and leading
#   rushers and receivers (by simulated mean).
# END
from statistics import fmean

PERCENTILES = (10, 25, 50, 75, 90)
LINES = (("passing", ("pass_yds", "pass_att", "pass_cmp", "pass_td", "int_thrown"), 1),
         ("rushing", ("rush_yds", "rush_att", "rush_td"), None),
         ("receiving", ("rec_yds", "receptions", "rec_td"), None),
         ("kicking", ("fg_made", "xp_made"), 1))


def distribution(values) -> dict:
    ordered = sorted(values)
    out = {"mean": fmean(ordered)}
    for p in PERCENTILES:
        out[p] = ordered[min(len(ordered) - 1, int(p / 100 * len(ordered)))]
    return out


def _row(label, values) -> str:
    d = distribution(values)
    return f"{label:28s} {d['mean']:7.1f} " + " ".join(f"{d[p]:6.0f}" for p in PERCENTILES)


def forecast(sim, players: int = 4) -> str:
    game, n = sim.context.game, len(sim.outcomes)
    winners = sim.values("winner")
    lines = [f"{game.away} @ {game.home} ({game.game_id}): {n} simulated games, {len(sim.failures)} failed",
             f"{game.home} wins {100 * winners.count(game.home) / n:.1f}%, {game.away} wins "
             f"{100 * winners.count(game.away) / n:.1f}%, tie {100 * winners.count(None) / n:.1f}%, "
             f"overtime {100 * fmean(sim.values('overtime')):.1f}%", "",
             f"{'':28s} {'mean':>7s} " + " ".join(f"{p:5d}%" for p in PERCENTILES)]
    points = sim.values("points")
    lines += [_row(f"{team} points", [p[team] for p in points]) for team in (game.away, game.home)]
    lines += [_row(f"margin ({game.home} - {game.away})", sim.values("margin")), _row("total", sim.values("total")),
              _row("plays", sim.values("plays"))]
    for team in (game.away, game.home):
        roster = [p for p in sim.context.players if p.team == team]
        for label, stats, count in LINES:
            ranked = sorted(roster, key=lambda p: -fmean(sim.player(p.id, stats[0])))[:count or players]
            for player in ranked:
                if fmean(sim.player(player.id, stats[0])) > 0:
                    lines += ["", f"{team} {player.name} ({label})"]
                    lines += [_row(f"  {stat}", sim.player(player.id, stat)) for stat in stats]
    return "\n".join(lines)
