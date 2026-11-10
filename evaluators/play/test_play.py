# START
# Tests for the play evaluator.
# - test_the_scenario_scores_well_against_itself: synthetic plays whose "real" outcome is one more simulated
#   run are calibrated by construction: no negative skill, a flat PIT (no data needed).
# - test_runs_are_traced: every simulated run becomes one Run with its lineups and each call's arguments.
# - test_event_cases_for_a_run / test_no_stand_in_no_score: a hand-built real run play gives each event its
#   real inputs and output; without a matching simulated run the cases have no arguments and go unscored.
# - test_week_one_evaluation: a real week scores every event, with skill where the baseline has information.
#   Skipped unless the 2026 files are already in .cache/nflverse.
# END
import random
from types import SimpleNamespace

import pytest

from evaluators.play import evaluate, write_report
from evaluators.play.cases import event_cases
from evaluators.play.evaluate import _runs, _score_events, _score_play, _traced
from evaluators.play.report import EVENTS
from evaluators.scoring import Scorecard
from scenarios.play import load_predictors, run_play
from scenarios.play.testing import synthetic_context
from shared.nflverse.download import CACHE
from shared.priors import Sample
from simulators.play import simulate_play, summarize

NAN = float("nan")


def test_the_scenario_scores_well_against_itself():
    predictors, card = load_predictors("baseline"), Scorecard()
    for i in range(400):
        ctx = synthetic_context(random.Random(i))
        actual = summarize(run_play(ctx, predictors, random.Random(-i - 1)))
        _score_play(card, ctx, actual, simulate_play(ctx, predictors, sims=30, index=i)[0])
    rows = {row["name"]: row for row in card.rows()}
    assert {"play: yards (scrimmage)", "play: action (try)", "play: return yards (free kick)"} <= set(rows)
    assert rows["play: yards (scrimmage)"]["n"] > 250 and rows["play: yards (scrimmage)"]["sims"] == 30
    assert all(row["skill"] is None or row["skill"] > -0.1 for row in rows.values() if row["n"] > 250)
    assert rows["play: action (scrimmage)"]["skill"] > 0.1
    assert all(0.03 < share < 0.2 for share in card.pit("play: yards (scrimmage)"))


def _real_run(rng):
    """A first-and-10 run for 7 yards by the offense's top back, as a Sample with only the columns cases read."""
    ctx = synthetic_context(rng, kind="scrimmage", x=30.0, down=1, distance=10.0, quarter=1, clock=600.0)
    back = next(p for p in ctx.roster(ctx.situation.offense) if p.position == "RB")
    row = SimpleNamespace(rusher_player_id=back.id, yards_gained=7.0, shotgun=1, fumble=0, touchdown=0,
                          out_of_bounds=0, penalty=0, penalty_type=None, penalty_team=None, desc="run for 7 yards")
    return Sample(ctx, {"action": "run"}, row, None), back


def _traced_runs(ctx, sims=40):
    traced, calls = _traced(load_predictors("baseline"))
    results, failures = simulate_play(ctx, traced, sims)
    return _runs(calls), results, failures


def test_runs_are_traced():
    sample, _ = _real_run(random.Random(0))
    runs, results, failures = _traced_runs(sample.context)
    assert len(runs) == len(results) == 40 and not failures
    assert all(run.unit == result.record[0].offense.unit for run, result in zip(runs, results))
    offense = next(run for run in runs if run.unit == "offense" and run.args("snap"))
    lineups, formation, defense, allowed = offense.args("snap")
    assert lineups is offense.lineups and "run" in allowed and offense.kind in ("run", "pass")


def test_event_cases_for_a_run():
    sample, back = _real_run(random.Random(0))
    runs, _, _ = _traced_runs(sample.context)
    cases = {(case.event, case.label): case for case in event_cases(sample, runs)}
    assert set(cases) == {("lineups", "downs 1-3"), ("offensive_formation", ""), ("pre_snap", ""), ("snap", ""),
                          ("carry", "run"), ("fouls", ""), ("injuries", "")}
    assert all(case.args is not None for case in cases.values())
    carry = cases["carry", "run"]
    assert carry.args[1:] == ("run", back.id, 30.0) and carry.actual == {"yards": 7.0, "end": "tackled"}
    assert cases["snap", ""].actual == {"action": "run", "carrier": "RB1"}
    assert cases["lineups", "downs 1-3"].actual == {"unit": "offense"}
    assert cases["offensive_formation", ""].actual == {"shotgun": True}
    assert cases["fouls", ""].actual == {"foul": "none"} and cases["injuries", ""].actual == {"injury": False}
    card = Scorecard()
    _score_events(card, load_predictors("baseline"), sample, runs, 40, random.Random(0))
    rows = {row["name"]: row for row in card.rows()}
    assert rows["carry: yards (run)"]["n"] == 1 and rows["carry: yards (run)"]["sims"] == 40
    assert rows["snap: carrier"]["n"] == 1 and rows["snap: carrier"]["sims"] < 40  # only the samples that ran
    assert rows["lineups: unit (downs 1-3)"]["sims"] == 40


def test_no_stand_in_no_score():
    sample, _ = _real_run(random.Random(0))
    cases = event_cases(sample, [])
    assert [case.event for case in cases if case.args is None] == ["offensive_formation", "pre_snap", "snap",
                                                                   "carry", "fouls", "injuries"]
    card = Scorecard()
    _score_events(card, load_predictors("baseline"), sample, [], 40, random.Random(0))
    assert all(row["n"] == 0 and row["unscored"] == 1 for row in card.rows())


@pytest.mark.skipif(not (CACHE / "play_by_play_2026.parquet").exists(), reason="nflverse cache missing")
def test_week_one_evaluation(tmp_path):
    evaluation = evaluate(2026, weeks=[1], sims=4, workers=1)
    rows = {row["name"]: row for row in evaluation.card.rows()}
    assert evaluation.plays > 2000 and evaluation.failures == 0
    assert {name.split(": ")[0] for name in rows} == {"play", *EVENTS}
    assert all(row["score"] >= -1e-9 or row["kind"] != "categorical" for row in rows.values() if row["n"])
    assert rows["play: yards (scrimmage)"]["n"] > 2000 and rows["play: yards (scrimmage)"]["skill"] > 0
    assert rows["lineups: unit (4th down)"]["skill"] > 0.3 and rows["kick_result: result"]["skill"] > 0.3
    assert rows["carry: yards (run)"]["unscored"] < 0.05 * rows["carry: yards (run)"]["n"]
    report = write_report(evaluation, tmp_path / "play.md").read_text()
    assert "## Event predictors" in report and "## Reliability" in report
