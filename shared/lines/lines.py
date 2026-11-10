# START
# Betting lines: what the market expected, gathered as benchmarks for the evaluators.
# - game_lines(season) -> DataFrame, one row per game: game_id, week, home, away, spread (points the home
#   team is favored by) with home_spread_odds / away_spread_odds, total with over_odds / under_odds, and
#   home_moneyline / away_moneyline. Closing lines with American odds, from the nflverse schedule.
# - player_lines(season, weeks=None) -> DataFrame, one row per game, player, and stat: game_id, week,
#   player_id (gsis), player, stat (a play scenario stat name: pass_yds, rush_yds, receptions, ...), line
#   (latest, which is the closing line once the game is played) and open. DraftKings' player props as
#   published by ESPN's public API, which gives the lines but not their prices.
# - STATS: the props we keep, ESPN's name -> our stat name.
# Internals: _props (one game's props, cached under .cache/lines/ once the game has been played, since the
#   lines of an upcoming game still move), _fetch (every page of ESPN's prop list for a game; empty if none
#   is published), _parse (the list -> [ESPN athlete id, prop name, line, open] rows; a prop is listed twice,
#   over and under, and when the two disagree the one updated last is kept).
# END
import json
import urllib.error
import urllib.request
from pathlib import Path

import pandas as pd

from shared.nflverse import load

CACHE = Path(__file__).resolve().parents[2] / ".cache" / "lines"
PROPS = ("https://sports.core.api.espn.com/v2/sports/football/leagues/nfl/events/{event}/competitions/{event}"
         "/odds/100/propBets?limit=1000&page={page}")  # 100 is DraftKings
GAME_LINES = {  # nflverse schedule column -> ours
    "game_id": "game_id", "week": "week", "home_team": "home", "away_team": "away", "spread_line": "spread",
    "home_spread_odds": "home_spread_odds", "away_spread_odds": "away_spread_odds", "total_line": "total",
    "over_odds": "over_odds", "under_odds": "under_odds", "home_moneyline": "home_moneyline",
    "away_moneyline": "away_moneyline",
}
STATS = {
    "Total Passing Yards": "pass_yds", "Total Pass Completions": "pass_cmp", "Total Passing Attempts": "pass_att",
    "Total Passing Touchdowns": "pass_td", "Total Passing Interceptions": "int_thrown",
    "Total Rushing Yards": "rush_yds", "Total Carries": "rush_att", "Total Receiving Yards": "rec_yds",
    "Total Receptions": "receptions", "Total Field Goals Made": "fg_made", "Total Extra Points Made": "xp_made",
}


def game_lines(season: int) -> pd.DataFrame:
    return load("games", season)[list(GAME_LINES)].rename(columns=GAME_LINES).dropna(subset=["spread"]).reset_index(drop=True)


def _fetch(event) -> list:
    items, page, pages = [], 1, 1
    while page <= pages:
        try:
            with urllib.request.urlopen(PROPS.format(event=event, page=page), timeout=60) as response:
                data = json.load(response)
        except urllib.error.HTTPError as error:
            if error.code != 404:  # 404: no props published for this game (yet)
                raise
            break
        items += data.get("items", [])
        pages, page = data.get("pageCount", 1), page + 1
    return items


def _parse(items) -> list:
    latest = {}
    for item in items:
        athlete = item.get("athlete") or {}
        line = item.get("current", {}).get("target", {}).get("value")
        if "$ref" in athlete and line is not None:
            key = (athlete["$ref"].split("/athletes/")[1].split("?")[0], item["type"]["name"].replace(" (incl. overtime)", ""))
            updated = item.get("lastUpdated", "")
            if key not in latest or updated > latest[key][0]:
                latest[key] = (updated, line, item.get("open", {}).get("target", {}).get("value"))
    return [[*key, line, opened] for key, (_, line, opened) in sorted(latest.items())]


def _props(event, played) -> list:
    path = CACHE / f"props_{event}.json"
    if path.exists():
        return json.loads(path.read_text())
    rows = _parse(_fetch(event))
    if played:
        CACHE.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(rows))
    return rows


def player_lines(season: int, weeks=None) -> pd.DataFrame:
    games = load("games", season)
    games = games[games.espn.notna() & (games.week.isin(list(weeks)) if weeks is not None else True)]
    rosters = load("rosters", season).dropna(subset=["espn_id", "gsis_id"]).drop_duplicates("espn_id")
    players = {str(r.espn_id): (r.gsis_id, r.full_name) for r in rosters.itertuples()}
    rows = []
    for game in games.itertuples():
        for espn_id, name, line, opened in _props(int(game.espn), pd.notna(game.result)):
            if name in STATS and espn_id in players:
                rows.append((game.game_id, game.week, *players[espn_id], STATS[name], line, opened))
    return pd.DataFrame(rows, columns=["game_id", "week", "player_id", "player", "stat", "line", "open"])
