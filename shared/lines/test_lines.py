# START
# Tests for the betting lines.
# - test_parse: ESPN's prop list becomes one row per player and prop (no network).
# - test_game_lines / test_player_lines: the cached 2026 lines have the expected shape. Skipped unless the
#   files are already in .cache (no downloads in tests).
# END
import pytest

from shared.lines.lines import CACHE, STATS, _parse
from shared.nflverse.download import CACHE as NFLVERSE

ATHLETE = {"$ref": "http://sports.core.api.espn.com/v2/sports/football/leagues/nfl/seasons/2026/athletes/123?lang=en"}


def _item(name, line=None, opened=None, athlete=ATHLETE, updated="2026-11-09T04:17Z"):
    target = lambda value: {} if value is None else {"target": {"value": value}}
    return {"athlete": athlete, "type": {"name": name}, "current": target(line), "open": target(opened),
            "lastUpdated": updated}


def test_parse():
    items = [_item("Total Passing Yards (incl. overtime)", 208.5, 202.5)] * 2  # listed twice: over and under
    items += [_item("Total Carries", 14.5, 15.5), _item("Total Carries", 15.5, 15.5, updated="2026-11-09T05:00Z")]
    items += [_item("Anytime Touchdown Scorer"), _item("Team Total Points", 27.5, 27.5, athlete="")]
    assert _parse(items) == [["123", "Total Carries", 15.5, 15.5], ["123", "Total Passing Yards", 208.5, 202.5]]
    assert {"Total Passing Yards", "Total Carries"} <= set(STATS)


@pytest.mark.skipif(not (NFLVERSE / "games.csv").exists(), reason="nflverse cache missing")
def test_game_lines():
    from shared.lines import game_lines
    lines = game_lines(2026)
    assert len(lines) > 100 and lines.game_id.is_unique
    favored = lines[lines.spread >= 3]
    assert (favored.home_moneyline < favored.away_moneyline).all()  # a positive spread favors the home team


@pytest.mark.skipif(not any(CACHE.glob("props_*.json")) or not (NFLVERSE / "roster_weekly_2026.parquet").exists(),
                    reason="lines cache missing")
def test_player_lines():
    from shared.lines import player_lines
    from shared.nflverse import load
    played = load("games", 2026).dropna(subset=["result"])
    week = int(played.week.min())
    if not all((CACHE / f"props_{int(event)}.json").exists() for event in played[played.week == week].espn):
        pytest.skip("lines cache incomplete")
    lines = player_lines(2026, weeks=[week])
    assert len(lines) > 300 and set(lines.stat) <= set(STATS.values())
    assert lines.player_id.str.match(r"\d\d-\d{7}").all() and (lines.line >= 0).all()
    assert not lines.duplicated(["game_id", "player_id", "stat"]).any()
