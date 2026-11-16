# START
# Tests for the game evaluator.
# - test_the_scenario_scores_against_itself: synthetic games whose "real" outcome is one more simulated run
#   get every output scored (every stat of every team and player), the lines' samples kept, and a full
#   report (no data needed).
# - test_outputs: which stats a position is scored on, roles, fantasy points, and no charted stat before the
#   charting started.
# - test_week_one_evaluation: a real week scores games, teams, players, and the timeout and challenge
#   predictors. Skipped unless the 2026 files are already in .cache/nflverse.
# END
import random
from types import SimpleNamespace

import pytest

from evaluators.game import Evaluation, evaluate, evaluate_games, game_outputs, write_report
from evaluators.game.outputs import POSITION_STATS, STATS, fantasy, parse, role_of
from evaluators.game.report import pooled
from evaluators.lines import Line
from scenarios.game import load_game_predictors, run_game
from scenarios.game.testing import synthetic_game
from shared.nflverse.download import CACHE
from simulators.game import summarize


def test_the_scenario_scores_against_itself(tmp_path):
    ctx, predictors = synthetic_game(), load_game_predictors("baseline")
    games = [SimpleNamespace(context=ctx, actual=summarize(run_game(ctx, predictors, random.Random(-i - 1))))
             for i in range(3)]
    assert set(game_outputs(ctx, games[0].actual)) == set(game_outputs(ctx, summarize(run_game(ctx, predictors, random.Random(9)))))
    lines = [Line("spread", ("margin", "test"), 2.5, 0.5, 3.0), Line("total", ("total", "test"), 44.5, 0.5, 40.0),
             Line("pass_yds", ("pass_yds", "test", "HOME-QB1"), 220.5, 0.5, 250.0),
             Line("total", ("total", "another game"), 44.5, 0.5, 40.0)]
    card, samples, failures = evaluate_games(games, sims=4, seed=0, predictors=predictors, workers=1, lines=lines)
    rows = {row["name"]: row for row in card.rows()}
    assert failures == 0 and set(samples) == {line.key for line in lines[:3]}
    assert all(len(values) == 4 for values in samples.values())
    assert rows["game: margin"]["n"] == 3 and rows["team: pass_yds"]["n"] == 6 and rows["game: margin"]["sims"] == 4
    assert rows["player: pass_yds (QB1)"]["n"] == 6 and rows["player: rec_yds (WR3)"]["n"] == 18  # 3 of 5 receivers
    assert rows["game: home win"]["kind"] == "binary" and rows["player: touchdown (RB1)"]["kind"] == "binary"
    assert all(row["score"] > -1e-9 for row in rows.values())  # zero, give or take the rounding of a sum
    assert all(rows[f"team: {stat}"]["n"] == 6 for stat in STATS)  # every stat, for each team
    assert rows["player: tackles (LB starter)"]["n"] == 6 and rows["player: tackles (LB backup)"]["n"] == 30
    assert rows["player: penalties (OL backup)"]["n"] == 42 and rows["player: punt_yds (P)"]["n"] == 6
    assert rows["player: fantasy (WR1)"]["kind"] == "numeric" and rows["player: pressures (DL starter)"]["n"] == 6
    together = {row["name"]: row for row in pooled(rows.values())}
    assert together["player: tackles"]["n"] == 6 * 22 and together["player: rec_yds"]["n"] == 6 * 11
    assert together["player: tackles"]["score"] >= 0
    evaluation = Evaluation([2026], 4, 3, failures, card, lines, samples)
    text = write_report(evaluation, tmp_path / "game.md").read_text()
    assert "## Betting lines" in text and "| spread | 1 |" in text and "| game: plays |" in text
    assert "## Players by role" in text and "| player: tackles |" in text and "| player: sacks (DL starter) |" in text
    assert "sim CRPS" in text and "## Reliability" in text


def test_outputs():
    ctx = synthetic_game()
    by_id = {player.id: player for player in ctx.players}
    assert role_of(by_id["HOME-LB1"]) == "LB starter" and role_of(by_id["HOME-LB4"]) == "LB backup"
    assert role_of(by_id["HOME-WR5"]) == "WR3" and role_of(by_id["HOME-K1"]) == "K"
    assert "tackles" in POSITION_STATS["DB"] and "tackles" not in POSITION_STATS["WR"] and POSITION_STATS["OL"]
    assert fantasy({"rec_yds": 80, "receptions": 6, "rec_td": 1, "fumbles_lost": 1}) == 18.0
    assert parse("player: tackles (LB starter)") == ("player", "tackles", "LB starter")
    outcome = summarize(run_game(ctx, load_game_predictors("baseline"), random.Random(0)))
    names = {name for name, _ in game_outputs(ctx, outcome)}
    assert "player: pressures (DL starter)" in names and "team: coverage_yds" in names
    early = {name for name, _ in game_outputs(synthetic_game(season=2015), outcome)}
    assert "player: tackles (DL starter)" in early and not any("pressures" in name for name in early)


@pytest.mark.skipif(not (CACHE / "play_by_play_2026.parquet").exists(), reason="nflverse cache missing")
def test_week_one_evaluation(tmp_path):
    evaluation = evaluate([2026], weeks=[1], sims=2, workers=1)
    rows = {row["name"]: row for row in evaluation.card.rows()}
    assert evaluation.games == 16 and evaluation.failures == 0
    assert rows["game: total"]["n"] == 16 and rows["team: points"]["n"] == 32
    assert 25 < rows["player: pass_yds (QB1)"]["n"] <= 32 and rows["player: fg_made (K)"]["n"] >= 32
    assert rows["player: tackles (LB starter)"]["n"] > 60 and rows["player: tackles (LB starter)"]["mean"] > 1
    assert rows["team: pressures"]["mean"] > 3 and rows["team: tackles"]["mean"] > 25
    assert rows["timeout: caller (rest of the game)"]["n"] > 2000
    assert rows["timeout: caller (last 2:00 of a half)"]["skill"] > 0
    assert rows["challenge: who and ruling"]["n"] > 2000
    report = write_report(evaluation, tmp_path / "game.md").read_text()
    assert "## Game scenario" in report and "## Betting lines" not in report
