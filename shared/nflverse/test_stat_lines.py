# START
# Tests for the real stat lines and for the history every player carries into a game. Skipped unless the
# files are already in .cache/nflverse (no downloads in tests).
# - test_stat_lines: one row per game and player; both sides of a play agree (sacks and sacks taken,
#   interceptions thrown and made); the charted stats are there from 2018 on and only then.
# - test_everyone_has_a_history: before a week 3 game, defenders, linemen, and kickers have season stats as
#   passers and receivers do, and their snaps on their side of the ball.
# - test_on_field: in a season that records who was on the field, a lineman's on-field totals are part of
#   his team's, and a defender's are what the offenses he faced did.
# END
import pytest

from shared.nflverse.download import CACHE

pytestmark = pytest.mark.skipif(
    not all((CACHE / name).exists() for name in ("play_by_play_2026.parquet", "players.parquet", "advstats_week_def_2026.parquet")),
    reason="nflverse cache missing")


def test_stat_lines():
    from shared.nflverse import CHARTED, STAT_COLUMNS, stat_lines
    lines = stat_lines(2026)
    assert not lines.duplicated(["game_id", "player_id"]).any() and lines.player_id.str.match(r"\d\d-\d{7}").all()
    charted = {stat for stats in CHARTED.values() for stat in stats}
    assert set(lines.columns) == {"game_id", "week", "player_id", "team"} | set(STAT_COLUMNS) | charted
    games = lines.groupby("game_id")[["sacks", "sacked", "interceptions", "int_thrown", "tackles", "pressures"]].sum()
    assert (games.sacks == games.sacked).mean() > 0.95 and (games.interceptions == games.int_thrown).all()
    assert games.tackles.between(40, 140).all() and games.pressures.between(5, 60).all()
    if (CACHE / "stats_player_week_2014.parquet").exists():
        assert set(stat_lines(2014).columns) == {"game_id", "week", "player_id", "team"} | set(STAT_COLUMNS)


def test_everyone_has_a_history():
    from shared.nflverse import real_plays
    assert not any(p.season_stats for p in real_plays(2026, weeks=[1])[0].context.players)  # nothing before week 1
    players = real_plays(2026, weeks=[3])[0].context.players
    for position, stats in (("LB", ("tackles", "defense_snaps")), ("DB", ("tackles", "defense_snaps", "coverage_targets")),
                            ("DL", ("tackles", "defense_snaps", "pressures")), ("OL", ("offense_snaps",)),
                            ("K", ("fg_att", "xp_att", "special_teams_snaps"))):
        group = [p for p in players if p.position == position]
        assert group and all(sum(p.stats.get(stat, 0) > 0 for p in group) >= 0.5 * len(group) for stat in stats), position
    assert all(p.stats.get("tackles", 0) <= p.stats.get("defense_snaps", 0) + p.stats.get("special_teams_snaps", 0)
               for p in players if p.position in ("DL", "LB", "DB") and p.snaps)
    veteran = max(players, key=lambda p: p.career.get("tackles", 0))
    assert veteran.position in ("LB", "DB") and veteran.career["tackles"] > 60 and veteran.career["defense_snaps"] > 500


@pytest.mark.skipif(not (CACHE / "pbp_participation_2025.parquet").exists(), reason="2025 participation missing")
def test_on_field():
    from shared.nflverse import ON_FIELD, real_plays
    ctx = real_plays(2025, weeks=[6])[0].context
    for team in (ctx.game.home, ctx.game.away):
        form = ctx.game.form(team).stats
        linemen = [p for p in ctx.players if p.team == team and p.position == "OL" and p.stats.get("offense_snaps", 0) > 100]
        assert linemen and all(0 < p.stats["on_dropbacks"] <= form["dropbacks"] for p in linemen)
        assert all(p.stats.get("on_sacked", 0) <= form.get("sacked", 0) for p in linemen)
        assert all(0 < p.stats["on_pressures"] < p.stats["on_dropbacks"] for p in linemen)
        defenders = [p for p in ctx.players if p.team == team and p.stats.get("defense_snaps", 0) > 100]
        assert defenders and all(0 < p.stats["on_allowed_plays"] <= form["allowed_plays"] for p in defenders)
        assert all(p.stats["on_allowed_plays"] <= p.stats["defense_snaps"] for p in defenders)
    assert {name.removeprefix("on_allowed_").removeprefix("on_") for p in ctx.players for name in p.stats
            if name.startswith("on_")} <= set(ON_FIELD)
