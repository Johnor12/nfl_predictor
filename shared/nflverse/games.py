# START
# Real games from nflverse data: every game of a season as a game scenario input, with what happened.
# - real_games(season, weeks=None, games=None) -> list[RealGame]: in schedule order, played or not. weeks
#   and games (game ids) each narrow it down.
# - RealGame(context, actual): the GameContext (the same game info and active players as the game's real
#   plays), and the real outcome, or None if the game hasn't been played. actual has the keys of
#   simulators.game.summarize: points by team, margin (home minus away), total, winner (None for a tie),
#   overtime, plays, teams ({team: {stat: value}}), players ({player id: {stat: value}}).
# - STAT_COLUMNS: the play scenario's stat names -> nflverse's player stats columns. Team stats are the sum
#   of the team's players'.
# END
from dataclasses import dataclass

import pandas as pd

from scenarios.game import GameContext
from shared.nflverse.contexts import _game, _is_play, _num, _players, _Rosters
from shared.nflverse.download import load

STAT_COLUMNS = {
    "pass_att": "attempts", "pass_cmp": "completions", "pass_yds": "passing_yards", "pass_td": "passing_tds",
    "int_thrown": "passing_interceptions", "sacked": "sacks_suffered",
    "rush_att": "carries", "rush_yds": "rushing_yards", "rush_td": "rushing_tds",
    "targets": "targets", "receptions": "receptions", "rec_yds": "receiving_yards", "rec_td": "receiving_tds",
    "fumbles_lost": "fumbles_lost_total", "penalties": "penalties",
    "sacks": "def_sacks", "interceptions": "def_interceptions", "tackles": "def_tackles_solo",
    "fg_att": "fg_att", "fg_made": "fg_made", "xp_att": "pat_att", "xp_made": "pat_made",
    "punts": "pt_att", "punt_yds": "pt_yards",
}


@dataclass(frozen=True)
class RealGame:
    context: GameContext
    actual: dict | None


def _actual(game, schedule, plays, stats) -> dict:
    home, away = int(schedule["home_score"]), int(schedule["away_score"])
    players, teams = {}, {game.home: {}, game.away: {}}
    for row in stats:
        if pd.isna(row["player_id"]):  # a team's leftover row, not a player
            continue
        line = {stat: float(row[column]) for stat, column in STAT_COLUMNS.items() if _num(row[column], 0)}
        if line:
            players[row["player_id"]] = line
        for stat, value in line.items():
            teams[row["team"]][stat] = teams[row["team"]].get(stat, 0.0) + value
    return {"points": {game.home: home, game.away: away}, "margin": home - away, "total": home + away,
            "winner": None if home == away else game.home if home > away else game.away,
            "overtime": schedule["overtime"] == 1, "plays": plays, "teams": teams, "players": players}


def real_games(season: int, weeks=None, games=None) -> list[RealGame]:
    schedule = load("games", season)
    if weeks is not None:
        schedule = schedule[schedule.week.isin(list(weeks))]
    if games is not None:
        schedule = schedule[schedule.game_id.isin(list(games))]
    pbp = load("pbp", season)
    rosters = _Rosters(season, pbp)
    rows = dict(tuple(pbp[pbp.game_id.isin(schedule.game_id)].groupby("game_id", sort=False)))
    stats = load("player_stats", season)
    stats = dict(tuple(stats[stats.game_id.isin(schedule.game_id)].groupby("game_id")))  # only the games asked for
    games = []
    for sched in schedule.to_dict("records"):
        played = rows.get(sched["game_id"])
        game = _game(sched, sched, rosters.forms, None if played is None else played["weather"].iloc[0])
        context = GameContext(game, _players(rosters, game, str(sched["gameday"])[:10], played))
        actual = None
        if played is not None and pd.notna(sched["result"]):
            plays = sum(_is_play(row) for row in played[["posteam", "play_type", "penalty"]].to_dict("records"))
            lines = stats[game.game_id].to_dict("records") if game.game_id in stats else []
            actual = _actual(game, sched, plays, lines)
        games.append(RealGame(context, actual))
    return games
