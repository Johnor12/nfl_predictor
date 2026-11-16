# START
# Tests for comparing two evaluations (no data needed).
# - test_two_runs_compare_case_by_case: an evaluation saved and loaded compares as itself with no change;
#   against a run with another seed every output has its cases matched, and `names` narrows them down.
# END
import random
from types import SimpleNamespace

from evaluators.compare import compare, load, save, table
from evaluators.game import Evaluation, evaluate_games
from scenarios.game import load_game_predictors, run_game
from scenarios.game.testing import synthetic_game
from simulators.game import summarize


def test_two_runs_compare_case_by_case(tmp_path):
    ctx, predictors = synthetic_game(), load_game_predictors("baseline")
    games = [SimpleNamespace(context=ctx, actual=summarize(run_game(ctx, predictors, random.Random(-i - 1))))
             for i in range(2)]
    runs = [Evaluation([2026], 4, 2, 0, evaluate_games(games, sims=4, seed=seed, predictors=predictors, workers=1)[0], [], {})
            for seed in (0, 1)]
    same = compare(runs[0], load(save(runs[0], tmp_path / "run.pkl")))
    assert len(same) == len(runs[0].card.outputs) and all(row["z"] == 0 and not row["change"] for row in same)
    rows = {row["name"]: row for row in compare(runs[0], runs[1])}
    assert rows["team: pass_yds"]["n"] == 4 and rows["team: pass_yds"]["before"] != rows["team: pass_yds"]["after"]
    assert rows["team: pass_yds"]["mean"] == sum(game.actual["teams"][team].get("pass_yds", 0) for game in games
                                                 for team in ("HOME", "AWAY")) / 4
    tackles = compare(runs[0], runs[1], ["tackles (LB"])
    assert {row["name"] for row in tackles} == {"player: tackles (LB starter)", "player: tackles (LB backup)",
                                                "player: missed_tackles (LB starter)", "player: missed_tackles (LB backup)"}
    assert len(table(tackles)) == 6 and table(tackles)[2].startswith("| player: ")
