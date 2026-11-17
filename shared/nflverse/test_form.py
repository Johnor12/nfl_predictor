# START
# Tests for form: what teams, coaches, referees, and players did before a game. Skipped unless the 2025 and
# 2026 files are already in .cache/nflverse (no downloads in tests).
# - test_a_team_s_season_builds_up_game_by_game: nothing before week 1; before a later game, exactly the
#   team's earlier games; what one team's offense did is what its opponent's defense allowed.
# - test_earlier_seasons_are_discounted: a team's career totals are last season's plus half of what came
#   before it, and a player's career is the same sum of his season stats.
# - test_coaches_and_referees: a coach's form is what the units he ran did: the head coach's games and fourth
#   downs, the offense under its play caller, the defense under its; a referee's counts each of his games once.
# - test_a_coach_s_form_follows_him: a play caller's career is with him at a new team, in a new job.
# - test_a_game_not_played_yet_gets_the_season_so_far.
# END
import pytest

from shared.nflverse.download import CACHE

pytestmark = pytest.mark.skipif(not all((CACHE / f"play_by_play_{season}.parquet").exists() for season in (2025, 2026)),
                                reason="nflverse cache missing")


@pytest.fixture(scope="module")
def games():
    from shared.nflverse import real_games
    return {g.context.game.game_id: g for g in real_games(2026)}


def _team_games(games, team, before_week):
    return [g for g in games.values() if team in (g.context.game.home, g.context.game.away)
            and g.context.game.week < before_week and g.actual]


def test_a_team_s_season_builds_up_game_by_game(games):
    opener = next(g.context.game for g in games.values() if g.context.game.week == 1)
    assert opener.form(opener.home).stats == {}
    assert opener.form(opener.home).career["games"] > 16
    later = next(g.context.game for g in games.values() if g.context.game.week == 6)
    team, form = later.home, later.form(later.home)
    earlier = _team_games(games, team, 6)
    assert form.stats["games"] == len(earlier)
    assert form.stats["points"] == sum(g.actual["points"][team] for g in earlier)
    assert form.stats["allowed_points"] == sum(sum(g.actual["points"].values()) - g.actual["points"][team] for g in earlier)
    assert 0.3 < form.stats["dropbacks"] / form.stats["plays"] < 0.8 and form.stats["pass_cmp"] <= form.stats["pass_att"]
    first = next(g.context.game for g in games.values() if g.context.game.week == 1)
    home, away = (next(g.context.game for g in _team_games(games, team, 3)[1:]).form(team).stats
                  for team in (first.home, first.away))  # each team's second game
    assert home["plays"] == away["allowed_plays"] and away["sacked"] == home.get("allowed_sacked", 0)


def test_earlier_seasons_are_discounted(games):
    from shared.nflverse import real_games
    from shared.nflverse.form import DECAY
    game = next(iter(games.values())).context
    team = game.game.home
    last_season = next(g.context.game for g in real_games(2025, weeks=[1]) if team in (g.context.game.home, g.context.game.away))
    older, last_year = last_season.form(team).career, _team_games({g.context.game.game_id: g for g in real_games(2025)}, team, 99)
    career = game.game.form(team).career
    assert career["games"] == pytest.approx(len(last_year) + DECAY * older["games"])
    passer = max(game.players, key=lambda p: p.career.get("pass_att", 0))
    assert passer.career["pass_att"] > 300 and passer.career["pass_cmp"] < passer.career["pass_att"]


def test_coaches_and_referees(games):
    game = next(g.context.game for g in games.values() if g.context.game.week == 3 and g.context.game.referee)
    team, staff, referee = game.form(game.home).stats, game.staff(game.home), game.form(game.referee)
    head, offense, defense = (game.form(coach).stats for coach in (staff.head_coach, staff.offensive_play_caller,
                                                                   staff.defensive_play_caller))
    # two games in, each has had his job in both of them
    assert all(head[stat] == team[stat] for stat in ("games", "points", "fourth_downs"))
    assert all(offense[stat] == team[stat] for stat in ("plays", "shotgun", "rush_yds"))
    assert all(defense[stat] == team[stat] for stat in ("allowed_plays", "allowed_pass_att"))
    if staff.head_coach != staff.offensive_play_caller:
        assert "plays" not in head and "games" not in offense
    worked = [g for g in games.values() if g.context.game.referee == game.referee and g.context.game.week < 3]
    assert referee.stats["games"] == len(worked)
    assert 0.02 < (referee.stats["flags"] + referee.stats["defense_flags"]) / referee.stats["snaps"] < 0.15


def test_a_coach_s_form_follows_him():
    from shared.nflverse import real_games
    game = next(g.context.game for g in real_games(2025, weeks=[1]) if "CHI" in (g.context.game.home, g.context.game.away))
    johnson = game.staff("CHI")  # Ben Johnson: the Lions' play caller through 2024, the Bears' head coach from 2025
    assert johnson.head_coach == johnson.offensive_play_caller == "Ben Johnson"
    career = game.form("Ben Johnson").career
    assert career["plays"] > 1000 and "games" not in career and "allowed_plays" not in career
    assert career["plays"] != game.form("CHI").career["plays"]


def test_a_game_not_played_yet_gets_the_season_so_far(games):
    unplayed = [g.context.game for g in games.values() if g.actual is None]
    if not unplayed:
        pytest.skip("every game has been played")
    game = unplayed[0]
    assert game.form(game.home).stats["games"] == len(_team_games(games, game.home, 99))
