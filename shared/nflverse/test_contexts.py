# START
# Tests for real play and game contexts. Skipped unless the 2026 files are already in .cache/nflverse (no
# downloads in tests).
# - test_week_one_contexts_are_valid: every real input passes validate_context.
# - test_conventions: kickoffs are from the kicking team's side; tries use the two-point spot; clock inference.
# - test_timeouts_before_plays: who called a timeout before a play, and the state before it.
# - test_week_one_games: every game's inputs are valid and match its plays'; its real outcome and stat lines.
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
