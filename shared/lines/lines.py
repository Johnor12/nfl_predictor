# START
# Betting lines: what the market expected, gathered as benchmarks for the evaluators.
# - game_lines(season) -> DataFrame, one row per game: game_id, week, home, away, spread (points the home
#   team is favored by) with home_spread_odds / away_spread_odds, total with over_odds / under_odds, and
#   home_moneyline / away_moneyline. Closing lines with American odds, from the nflverse schedule.
# - player_lines(season, weeks=None, games=None) -> DataFrame, one row per game, player, and stat (weeks and
#   games, a list of game ids, each narrow it down): game_id, week, player_id (gsis), player, stat (STATS'
#   names), line (latest, which is the closing line once the game is played), open, over_odds and under_odds
#   (American; nan where the book's price isn't published), and book. Every sportsbook's player props that
#   ESPN's public API has for the game; where several books have a line, the first of BOOKS with both prices
#   is kept, else the first of BOOKS.
# - STATS: the props we keep, ESPN's name -> our stat name: a play scenario stat, or one of COMBINED.
# - COMBINED: the props on a sum of stats: name -> {stat: weight} (tackles+assists, kick_pts, ...).
# - value(stat, line) -> float: a stat's or a combined stat's value in a stat line ({stat: value}).
# Internals: _props (one game's props, cached under .cache/lines/ once the game has been played, since the
#   lines of an upcoming game still move; a cached file in an earlier version's row format is fetched again), _books (the sportsbooks with pre-game props for a game), _fetch
#   (every page of one book's prop list), _parse (the list -> [ESPN athlete id, prop name, line, open, over
#   price, under price] rows: a book lists each side of a prop on its own, and often other lines of the same
#   prop without a price; the line kept is the priced one, or the one updated last, and never an unpriced
#   whole number, which is a rung of a "70 or more yards" ladder), _american.
# END
import json
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pandas as pd

from shared.nflverse import load

CACHE = Path(__file__).resolve().parents[2] / ".cache" / "lines"
ODDS = "https://sports.core.api.espn.com/v2/sports/football/leagues/nfl/events/{event}/competitions/{event}/odds"
BOOKS = ("DraftKings", "ESPN BET", "MGM", "Caesars", "PointsBet", "FanDuel", "SugarHouse")  # in order of preference
GAME_LINES = {  # nflverse schedule column -> ours
    "game_id": "game_id", "week": "week", "home_team": "home", "away_team": "away", "spread_line": "spread",
    "home_spread_odds": "home_spread_odds", "away_spread_odds": "away_spread_odds", "total_line": "total",
    "over_odds": "over_odds", "under_odds": "under_odds", "home_moneyline": "home_moneyline",
    "away_moneyline": "away_moneyline",
}
STATS = {
    "Total Passing Yards": "pass_yds", "Total Pass Completions": "pass_cmp", "Total Passing Attempts": "pass_att",
    "Total Passing Touchdowns": "pass_td", "Total Passing Interceptions": "int_thrown",
    "To throw an interception": "int_thrown", "Total Passing Plus Rushing Yards": "pass_yds+rush_yds",
    "Total Rushing Yards": "rush_yds", "Total Carries": "rush_att", "Total Receiving Yards": "rec_yds",
    "Total Receptions": "receptions", "Total Rushing Plus Receiving Yards": "rush_yds+rec_yds",
    "Total Tackles": "tackles", "Total Assists": "assists", "Total Tackles Plus Assists": "tackles+assists",
    "Total Sacks": "sacks", "Total Defensive Interceptions": "interceptions",
    "Total Field Goals Made": "fg_made", "Total Extra Points Made": "xp_made", "Total Kicking Points": "kick_pts",
}
COMBINED = {
    "pass_yds+rush_yds": {"pass_yds": 1, "rush_yds": 1}, "rush_yds+rec_yds": {"rush_yds": 1, "rec_yds": 1},
    "tackles+assists": {"tackles": 1, "assists": 1}, "kick_pts": {"fg_made": 3, "xp_made": 1},
}
WIDTH = 7  # a cached prop row: book, ESPN athlete id, prop name, line, open, over price, under price
COLUMNS = ["game_id", "week", "player_id", "player", "stat", "line", "open", "over_odds", "under_odds", "book"]


def value(stat, line) -> float:
    return float(sum(weight * line.get(part, 0.0) for part, weight in COMBINED.get(stat, {stat: 1}).items()))


def game_lines(season: int) -> pd.DataFrame:
    return load("games", season)[list(GAME_LINES)].rename(columns=GAME_LINES).dropna(subset=["spread"]).reset_index(drop=True)


def _get(url) -> dict:
    try:
        with urllib.request.urlopen(url, timeout=60) as response:
            return json.load(response)
    except urllib.error.HTTPError as error:
        if error.code != 404:  # 404: nothing published for this game (yet)
            raise
        return {}


def _books(event) -> list:
    """[(ESPN's id of the book, its name)]: the books with props for the game, without their in-game lines."""
    listed = [(item["provider"]["id"], item["provider"]["name"]) for item in _get(ODDS.format(event=event) + "?limit=100")
              .get("items", []) if "propBets" in item]
    return [(book, name.replace("Draft Kings", "DraftKings").replace("Bet 365", "bet365").split(" Sportsbook")[0])
            for book, name in listed if "Live" not in name]


def _fetch(event, book) -> list:
    items, page, pages = [], 1, 1
    while page <= pages:
        data = _get(ODDS.format(event=event) + f"/{book}/propBets?limit=1000&page={page}")
        items += data.get("items", [])
        pages, page = data.get("pageCount", 1), page + 1
    return items


def _american(side) -> float | None:
    odds = (side or {}).get("american")
    return None if odds is None else 100.0 if odds.upper() in ("EVEN", "EV") else float(odds)


def _parse(items) -> list:
    props = {}
    for item in items:
        athlete, current = item.get("athlete") or {}, item.get("current", {})
        line = current.get("target", {}).get("value")
        if "$ref" in athlete and line is not None:
            key = (athlete["$ref"].split("/athletes/")[1].split("?")[0], item["type"]["name"].replace(" (incl. overtime)", ""))
            prices = _american(current.get("over")), _american(current.get("under"))
            if prices == (None, None) and float(line).is_integer():
                continue  # "70 or more yards", one of a ladder of them, not an over/under
            props.setdefault(key, []).append((any(p is not None for p in prices), item.get("lastUpdated", ""), line,
                                              item.get("open", {}).get("target", {}).get("value"), *prices))
    rows = []
    for key, listed in sorted(props.items()):
        listed.sort(key=lambda entry: entry[:2])  # a priced line last, and of those the one updated last
        line, opened = listed[-1][2:4]
        sides = [entry for entry in reversed(listed) if entry[2] == line]
        over, under = (next((entry[i] for entry in sides if entry[i] is not None), None) for i in (4, 5))
        rows.append([*key, line, opened, over, under])
    return rows


def _props(event, played) -> list:
    path = CACHE / f"props_{event}.json"
    if path.exists():
        rows = json.loads(path.read_text())
        if all(len(row) == WIDTH for row in rows):  # else it was cached by an earlier version of _parse
            return rows
    rows = [[name, *row] for book, name in _books(event) for row in _parse(_fetch(event, book))]
    if played:
        CACHE.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(rows))
    return rows


def player_lines(season: int, weeks=None, games=None) -> pd.DataFrame:
    schedule = load("games", season)
    keep = schedule.espn.notna()
    if weeks is not None:
        keep &= schedule.week.isin(list(weeks))
    if games is not None:
        keep &= schedule.game_id.isin(list(games))
    games = schedule[keep]
    known = load("players").dropna(subset=["espn_id", "gsis_id"]).drop_duplicates("espn_id")
    players = {str(int(float(espn))): (gsis, name) for espn, gsis, name in zip(known.espn_id, known.gsis_id, known.display_name)}
    with ThreadPoolExecutor(8) as pool:
        props = list(pool.map(_props, games.espn.astype(int), games.result.notna()))
    rows = []
    for game, listed in zip(games.itertuples(), props):
        for book, espn_id, name, line, opened, over, under in listed:
            if name in STATS and espn_id in players:
                rows.append((game.game_id, game.week, *players[espn_id], STATS[name], line, opened, over, under, book))
    lines = pd.DataFrame(rows, columns=COLUMNS).astype({"over_odds": float, "under_odds": float})
    rank = lines.book.map({book: i for i, book in enumerate(BOOKS)}).fillna(len(BOOKS))
    unpriced = lines.over_odds.isna() | lines.under_odds.isna()
    order = lines.assign(unpriced=unpriced, rank=rank).sort_values(["unpriced", "rank"], kind="stable").index
    return lines.loc[order].drop_duplicates(["game_id", "player_id", "stat"]).sort_index().reset_index(drop=True)
