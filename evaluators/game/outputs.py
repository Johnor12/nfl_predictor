# START
# What the game evaluator scores: every stat of every team and every player.
# - game_outputs(ctx, outcome) -> {(name, subject): value}: the scored outputs, read the same way from a real
#   outcome (RealGame.actual) and a simulated one (simulators.game.summarize). subject is None, a team, or a
#   player id. Names: "game: margin", "team: pass_yds", "player: tackles (LB starter)".
# - FAMILIES: the stats, grouped by what a player does (passing, rushing, ..., flags, and the charted ones:
#   CHARTED). STATS: all of them; every one is scored for each team. A charted stat is only scored in a
#   season that was charted (shared.nflverse.CHARTED_SINCE).
# - POSITION_STATS: position -> the stats scored for each of its players (the families his position has a
#   part in). A stat outside them (a receiver's pass) is still in his team's row.
# - ROLES: every role, in report order. role_of(player): a quarterback's, back's, receiver's, or tight end's
#   depth chart rank (a 3 means third or lower), a lineman's or defender's "starter" (first at a depth chart
#   slot) or "backup", else the position.
# - fantasy(stats) -> float: a stat line's fantasy points (FANTASY: a point per reception), scored with a
#   touchdown (rushing or receiving, yes or no) for the positions that carry the ball (SCORERS).
# - parse(name) -> (level, stat, role): a row's name taken apart ("player", "tackles", "LB starter").
# END
from shared.nflverse import CHARTED_SINCE
from shared.priors import role

FAMILIES = {
    "passing": ("pass_att", "pass_cmp", "pass_yds", "pass_td", "int_thrown", "sacked", "sack_yards", "pass_air_yds",
                "pass_yac", "pass_first_downs"),
    "rushing": ("rush_att", "rush_yds", "rush_td", "rush_first_downs"),
    "receiving": ("targets", "receptions", "rec_yds", "rec_td", "target_air_yds", "rec_yac", "rec_first_downs"),
    "ball": ("fumbles", "fumbles_lost", "two_pt"),
    "defense": ("tackles", "assists", "tfl", "sacks", "qb_hits", "interceptions", "int_ret_yds", "passes_defended",
                "forced_fumbles", "fumble_recoveries", "fumble_ret_yds", "fumble_ret_td", "safeties", "def_td",
                "kicks_blocked"),
    "returns": ("punt_returns", "punt_ret_yds", "kick_returns", "kick_ret_yds", "special_teams_td"),
    "kicking": ("fg_att", "fg_made", "fg_made_yds", "xp_att", "xp_made"),
    "punting": ("punts", "punt_yds"),
    "flags": ("penalties", "penalty_yards"),
    "pressure": ("pressured", "hurried", "hit", "blitzed", "bad_throws", "pass_drops"),
    "contact": ("rush_yds_before_contact", "rush_yds_after_contact", "rush_broken_tackles"),
    "hands": ("drops", "rec_broken_tackles"),
    "rush and coverage": ("pressures", "hurries", "blitzes", "missed_tackles", "coverage_targets", "coverage_cmp",
                          "coverage_yds", "coverage_td"),
}
CHARTED = frozenset(stat for family in ("pressure", "contact", "hands", "rush and coverage")
                    for stat in FAMILIES[family])
STATS = tuple(stat for family in FAMILIES.values() for stat in family)
_POSITIONS = {
    "QB": ("passing", "pressure", "rushing", "contact", "ball", "flags"),
    "RB": ("rushing", "contact", "receiving", "hands", "ball", "returns", "flags"),
    "FB": ("rushing", "contact", "receiving", "hands", "ball", "flags"),
    "WR": ("receiving", "hands", "rushing", "contact", "ball", "returns", "flags"),
    "TE": ("receiving", "hands", "ball", "flags"),
    "OL": ("flags",),
    "DL": ("defense", "rush and coverage", "flags"),
    "LB": ("defense", "rush and coverage", "flags"),
    "DB": ("defense", "rush and coverage", "returns", "flags"),
    "K": ("kicking",),
    "P": ("punting",),
    "LS": ("flags",),
}
POSITION_STATS = {position: tuple(stat for family in families for stat in FAMILIES[family])
                  for position, families in _POSITIONS.items()}
SCORERS = ("QB", "RB", "FB", "WR", "TE")  # the positions scored on a touchdown and on fantasy points
FANTASY = {"pass_yds": 0.04, "pass_td": 4, "int_thrown": -2, "rush_yds": 0.1, "rush_td": 6, "receptions": 1,
           "rec_yds": 0.1, "rec_td": 6, "two_pt": 2, "fumbles_lost": -2, "special_teams_td": 6, "fumble_ret_td": 6}
RANKED = ("QB", "RB", "WR", "TE")
DEPTH = ("OL", "DL", "LB", "DB")
RETURN_SLOTS = ("KR", "PR", "H")
ROLES = tuple([f"{position}{rank}" for position in RANKED for rank in (1, 2, 3)] + ["FB"]
              + [f"{position} {depth}" for position in DEPTH for depth in ("starter", "backup")] + ["K", "P", "LS"])


def role_of(player) -> str:
    if player.position in DEPTH:
        first = any(rank == 1 for slot, rank in player.depth if slot not in RETURN_SLOTS)
        return f"{player.position} {'starter' if first else 'backup'}"
    return role(player)


def fantasy(stats) -> float:
    return float(sum(points * stats.get(stat, 0) for stat, points in FANTASY.items()))


def parse(name) -> tuple:
    level, _, rest = name.partition(": ")
    stat, _, position = rest.partition(" (")
    return level, stat, position.rstrip(")")


def game_outputs(ctx, outcome) -> dict:
    game, charted = ctx.game, ctx.game.season >= CHARTED_SINCE
    out = {("game: margin", None): float(outcome["margin"]), ("game: total", None): float(outcome["total"]),
           ("game: home win", None): outcome["margin"] > 0, ("game: overtime", None): bool(outcome["overtime"]),
           ("game: plays", None): float(outcome["plays"])}
    for team in (game.home, game.away):
        stats = outcome["teams"][team]
        out["team: points", team] = float(outcome["points"][team])
        out["team: turnovers", team] = float(stats.get("int_thrown", 0) + stats.get("fumbles_lost", 0))
        for stat in STATS:
            if charted or stat not in CHARTED:
                out[f"team: {stat}", team] = float(stats.get(stat, 0))
    for player in ctx.players:
        position, stats = role_of(player), outcome["players"].get(player.id, {})
        for stat in POSITION_STATS[player.position]:
            if charted or stat not in CHARTED:
                out[f"player: {stat} ({position})", player.id] = float(stats.get(stat, 0))
        if player.position in SCORERS:
            out[f"player: touchdown ({position})", player.id] = stats.get("rush_td", 0) + stats.get("rec_td", 0) > 0
            out[f"player: fantasy ({position})", player.id] = fantasy(stats)
    return out
