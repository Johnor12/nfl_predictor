# START
# Tests for the game evaluator.
# - test_the_scenario_scores_against_itself: synthetic games whose "real" outcome is one more simulated run
#   get every output scored, the lines' samples kept, and a full report (no data needed).
# - test_week_one_evaluation: a real week scores games, teams, players, and the timeout predictor. Skipped
#   unless the 2026 files are already in .cache/nflverse.
# END
import random
from types import SimpleNamespace

import pytest

from evaluators.game import Evaluation, evaluate, evaluate_games, game_outputs, write_report
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
    assert all(row["score"] >= 0 for row in rows.values())
    evaluation = Evaluation(2026, [1], 4, 3, failures, card, lines, samples)
    text = write_report(evaluation, tmp_path / "game.md").read_text()
    assert "## Betting lines" in text and "| spread | 1 |" in text and "| game: plays |" in text
    assert "sim CRPS" in text and "## Reliability" in text


@pytest.mark.skipif(not (CACHE / "play_by_play_2026.parquet").exists(), reason="nflverse cache missing")
def test_week_one_evaluation(tmp_path):
    evaluation = evaluate(2026, weeks=[1], sims=2, workers=1)
    rows = {row["name"]: row for row in evaluation.card.rows()}
    assert evaluation.games == 16 and evaluation.failures == 0
    assert rows["game: total"]["n"] == 16 and rows["team: points"]["n"] == 32
    assert 25 < rows["player: pass_yds (QB1)"]["n"] <= 32 and rows["player: fg_made (K)"]["n"] >= 32
    assert rows["timeout: caller (rest of the game)"]["n"] > 2000
    assert rows["timeout: caller (last 2:00 of a half)"]["skill"] > 0
    report = write_report(evaluation, tmp_path / "game.md").read_text()
    assert "## Game scenario" in report and "## Betting lines" not in report
