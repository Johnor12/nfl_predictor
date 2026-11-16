# START
# Tests for the betting lines.
# - test_parse / test_parse_prices: ESPN's prop list becomes one row per player and prop, with the prices of
#   a book that publishes them and without its ladder of other lines (no network).
# - test_value: a combined prop is a weighted sum of a stat line's stats.
# - test_game_lines / test_player_lines: the cached 2026 lines have the expected shape. Skipped unless the
#   files are already in .cache (no downloads in tests).
# END
import pytest

from shared.lines.lines import CACHE, COMBINED, STATS, _parse, value
from shared.nflverse.download import CACHE as NFLVERSE

ATHLETE = {"$ref": "http://sports.core.api.espn.com/v2/sports/football/leagues/nfl/seasons/2026/athletes/123?lang=en"}


def _item(name, line=None, opened=None, athlete=ATHLETE, updated="2026-11-09T04:17Z", **prices):
    target = lambda value: {} if value is None else {"target": {"value": value}}
    current = {**target(line), **{side: {"american": odds} for side, odds in prices.items()}}
    return {"athlete": athlete, "type": {"name": name}, "current": current, "open": target(opened), "lastUpdated": updated}


def test_parse():
    items = [_item("Total Passing Yards (incl. overtime)", 208.5, 202.5)] * 2  # listed twice: over and under
    items += [_item("Total Carries", 14.5, 15.5), _item("Total Carries", 15.5, 15.5, updated="2026-11-09T05:00Z")]
    items += [_item("Anytime Touchdown Scorer"), _item("Team Total Points", 27.5, 27.5, athlete="")]
    assert _parse(items) == [["123", "Total Carries", 15.5, 15.5, None, None],
                             ["123", "Total Passing Yards", 208.5, 202.5, None, None]]
    assert {"Total Passing Yards", "Total Carries"} <= set(STATS)


def test_parse_prices():
    # a book that prices its line: each side on its own, among the rungs of a "70 or more" ladder
    items = [_item("Total Receiving Yards", 49.5, 52.5, over="-120"), _item("Total Receiving Yards", 60.0, 60.0),
             _item("Total Receiving Yards", 49.5, 52.5, under="Even"),
             _item("Total Receiving Yards", 40.0, 40.0, updated="2026-11-09T05:00Z"),
             _item("Total Receptions", 4.0, 4.0), _item("Total Sacks", 0.5, 0.5, under="-170")]
    assert _parse(items) == [["123", "Total Receiving Yards", 49.5, 52.5, -120.0, 100.0],
                             ["123", "Total Sacks", 0.5, 0.5, None, -170.0]]


def test_value():
    line = {"tackles": 4.0, "assists": 3.0, "fg_made": 2.0, "xp_made": 3.0}
    assert value("tackles", line) == 4 and value("tackles+assists", line) == 7 and value("kick_pts", line) == 9
    assert value("rush_yds+rec_yds", line) == 0 and set(COMBINED) <= set(STATS.values())


@pytest.mark.skipif(not (NFLVERSE / "games.csv").exists(), reason="nflverse cache missing")
def test_game_lines():
    from shared.lines import game_lines
    lines = game_lines(2026)
    assert len(lines) > 100 and lines.game_id.is_unique
    favored = lines[lines.spread >= 3]
    assert (favored.home_moneyline < favored.away_moneyline).all()  # a positive spread favors the home team


@pytest.mark.skipif(not any(CACHE.glob("props_*.json")) or not (NFLVERSE / "players.parquet").exists(),
                    reason="lines cache missing")
def test_player_lines():
    from shared.lines import player_lines
    from shared.nflverse import load
    played = load("games", 2026).dropna(subset=["result"])
    week = int(played.week.min())
    if not all((CACHE / f"props_{int(event)}.json").exists() for event in played[played.week == week].espn):
        pytest.skip("lines cache incomplete")
    lines = player_lines(2026, weeks=[week])
    assert len(lines) > 300 and set(lines.stat) <= set(STATS.values()) and {"tackles", "sacks", "kick_pts"} <= set(lines.stat)
    assert lines.player_id.str.match(r"\d\d-\d{7}").all() and (lines.line >= 0).all()
    assert not lines.duplicated(["game_id", "player_id", "stat"]).any()
