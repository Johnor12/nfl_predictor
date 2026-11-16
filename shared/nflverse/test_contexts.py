# START
# Tests for real play and game contexts. Skipped unless the 2026 files are already in .cache/nflverse (no
# downloads in tests).
# - test_week_one_contexts_are_valid: every real input passes validate_context.
# - test_conventions: kickoffs are from the kicking team's side; tries use the two-point spot; clock inference.
# - test_timeouts_before_plays: who called a timeout before a play, and the state before it.
# - test_week_one_games: every game's inputs are valid and match its plays'; its real outcome and stat lines.
# - test_recent_snaps: players carry their recent snaps: per kicking unit where the season records who was on
#   the field (2025), otherwise from the per-game snap counts (2026); nobody has any before week 1.
# - test_usage_and_snap_gaps: a starter's season stats say how he has been used (snaps, carries, dropbacks),
#   and a play knows the game time since the snap before it.
# - test_weather_comes_from_the_report_where_the_schedule_has_none: outdoors only.
# - test_old_seasons: a season in nflverse's older formats (2014: weekly depth charts, detailed positions,
#   teams that have since moved, no charting or participation) gives valid inputs. Skipped unless cached.
# END
import pytest

from shared.nflverse.download import CACHE
from scenarios.play import validate_context

pytestmark = pytest.mark.skipif(not (CACHE / "play_by_play_2026.parquet").exists(), reason="nflverse cache missing")


@pytest.fixture(scope="module")
def plays():
    from shared.nflverse import real_plays
    return real_plays(2026, weeks=[1])


def test_week_one_contexts_are_valid(plays):
    assert len(plays) > 2000
    assert [(p.context.game.game_id, e) for p in plays for e in validate_context(p.context)] == []


def test_conventions(plays):
    opening = plays[0].context.situation
    assert opening.kind == "kickoff" and opening.x == 35 and opening.quarter == 1 and opening.clock == 900
    assert not opening.clock_running
    tries = [p.context.situation for p in plays if p.context.situation.kind == "try"]
    assert all(80 <= s.x <= 99 and s.down is None for s in tries)  # behind the 2 after a penalty on the try
    assert sum(s.x == 98 for s in tries) > 0.9 * len(tries)
    after_kickoff = plays[1].context.situation
    assert after_kickoff.kind == "scrimmage" and not after_kickoff.clock_running
    assert all(len(p.context.history) == i for i, p in enumerate(plays[:50]))


def test_timeouts_before_plays(plays):
    from shared.priors import Sample, timeout_case
    called = [p for p in plays if p.actual["timeout"]]
    assert 80 < len(called) < 200 and all(p.actual["timeout"] in p.context.situation.timeouts for p in called)
    assert all(p.actual["timeout_clock_running"] is None for p in plays if not p.actual["timeout"])
    play = called[0]
    before, caller = timeout_case(Sample(play.context, play.actual, None, None))
    s, team = play.context.situation, play.actual["timeout"]
    assert caller == ("offense" if team == s.offense else "defense") and not s.clock_running
    assert before.situation.timeouts[team] == s.timeouts[team] + 1


def test_week_one_games(plays):
    from scenarios.game import validate_game_context
    from shared.nflverse import STAT_COLUMNS, real_games
    games = real_games(2026, weeks=[1])
    assert len(games) == 16 and all(game.actual and validate_game_context(game.context) == [] for game in games)
    game = games[0]
    first = next(p for p in plays if p.context.game.game_id == game.context.game.game_id)
    assert game.context.players == first.context.players and game.context.game == first.context.game
    actual, teams = game.actual, (game.context.game.home, game.context.game.away)
    assert actual["margin"] == actual["points"][teams[0]] - actual["points"][teams[1]]
    assert actual["plays"] == sum(p.context.game.game_id == game.context.game.game_id for p in plays)
    assert set(actual["teams"]) == set(teams) and all(set(line) <= set(STAT_COLUMNS) for line in actual["players"].values())
    assert all(100 < actual["teams"][team]["pass_yds"] + actual["teams"][team]["rush_yds"] < 700 for team in teams)
    assert all(actual["teams"][team]["penalties"] < 20 for team in teams)
    by_id = {p.id: p for p in game.context.players}
    passers = [pid for pid, line in actual["players"].items() if line.get("pass_att", 0) > 10]
    assert passers and all(by_id[pid].position == "QB" for pid in passers)


def test_recent_snaps(plays):
    from shared.nflverse import load, real_plays, real_samples
    assert not any(p.snaps for p in plays[0].context.players)  # week 1: nothing to go on yet
    assert load("participation", 2026) is None
    ctx = real_plays(2026, weeks=[3])[0].context
    units = {unit for p in ctx.players for unit, _ in p.snaps}
    assert units == {"offense", "defense", "special_teams"}
    assert sum(bool(p.snaps) for p in ctx.players) > 0.8 * len(ctx.players)
    if not (CACHE / "pbp_participation_2025.parquet").exists():
        return
    sample = next(iter(real_samples(2025, weeks=[3])))
    units = {unit for p in sample.context.players for unit, _ in p.snaps}
    assert units == {"offense", "defense", "punt", "punt_return", "field_goal", "field_goal_block", "kickoff", "kick_return"}
    on_field = sample.participation.players_on_play.split(";")
    assert len(on_field) == 22 and set(on_field) <= set(sample.context.by_id)


def test_usage_and_snap_gaps(plays):
    from shared.nflverse import real_plays
    assert not any(p.season_stats for p in plays[0].context.players)  # week 1: nothing to go on yet
    later = real_plays(2026, weeks=[3])
    starters = [p for p in later[0].context.players if p.position == "QB" and p.stats.get("dropbacks", 0) > 40]
    assert starters and all(p.stats["offense_snaps"] >= p.stats["dropbacks"] >= p.stats["pass_att"] for p in starters)
    backs = [p for p in later[0].context.players if p.position == "RB" and p.stats.get("carries", 0) > 10]
    assert backs and all(p.stats["carries"] == p.stats["rush_att"] <= p.stats["offense_snaps"] for p in backs)
    assert later[0].actual["seconds_since_snap"] is None  # the opening kickoff
    gaps = [p.actual["seconds_since_snap"] for p in later
            if p.context.situation.clock_running and p.context.situation.play_clock == 40]
    assert 35 < sum(gaps) / len(gaps) < 40  # a play and most of a play clock


@pytest.mark.skipif(not (CACHE / "play_by_play_2014.parquet").exists(), reason="2014 nflverse cache missing")
def test_old_seasons():
    from scenarios.play.context import POSITIONS
    from shared.nflverse import real_games, real_samples
    samples = list(real_samples(2014, weeks=[2]))
    assert len(samples) > 2000 and all(s.charting is None and s.participation is None for s in samples)
    assert [e for s in samples[::50] for e in validate_context(s.context)] == []
    ctx = next(s.context for s in samples if s.context.game.game_id == "2014_02_KC_DEN")
    assert {p.position for p in ctx.players} <= set(POSITIONS)
    assert {slot for p in ctx.players for slot, _ in p.depth} >= {"QB", "RB", "WR", "LT", "PK", "KR", "LCB"}
    assert sum(bool(p.snaps) for p in ctx.players) > 0.8 * len(ctx.players)  # week 1's snap counts
    game = real_games(2014, games=["2014_02_STL_TB"])[0]  # the Rams have moved since: they are LA everywhere
    assert (game.context.game.home, game.context.game.away) == ("TB", "LA")
    assert set(game.actual["teams"]) == {"TB", "LA"} and {p.team for p in game.context.players} == {"TB", "LA"}


def test_weather_comes_from_the_report_where_the_schedule_has_none():
    from shared.nflverse.contexts import _weather
    report = "Sunny Temp: 73° F, Humidity: 79%, Wind: W 3 mph"
    assert _weather({"roof": "outdoors", "temp": float("nan"), "wind": float("nan")}, report) == [73.0, 3.0]
    assert _weather({"roof": "outdoors", "temp": 70.0, "wind": float("nan")}, "Temp: 73° F, Wind: 10 WSW mph") == [70.0, 10.0]
    assert _weather({"roof": "dome", "temp": float("nan"), "wind": float("nan")}, "Indoor Temp: 72° F, Wind: mph") == [None, None]
    assert _weather({"roof": "outdoors", "temp": float("nan"), "wind": float("nan")}, "Temp: ° F, Wind: mph") == [None, None]
    assert _weather({"roof": "outdoors", "temp": float("nan"), "wind": float("nan")}, None) == [None, None]
