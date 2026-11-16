# START
# Tests across the events' predictor implementations (no network needed).
# - test_baseline_plays_are_valid: thousands of synthetic plays with every baseline predictor pass the validator.
# - test_default_plays_are_valid: the same with each event's default implementation (events.predictor), and
#   every event of the game has one.
# - test_load_predictors_rejects_unknown_events.
# - test_baseline_timeouts_need_a_timeout: only a team with a timeout left calls one, and the other team may
#   answer with its own.
# - test_baseline_challenges: only a team that may challenge does, at about the real rate.
# - test_a_players_past_moves_who_is_credited: a defender who has made tackles makes more of them, and the
#   charted stats (pressures, coverage, missed tackles, drops) come out of simulated plays.
# - test_fake_kicks: the baseline fakes a punt now and then, and a fake plays out with the default predictors.
# - test_fair_catch_kick_with_the_default_predictors: tried as a half runs out, and it plays out.
# END
import random
from collections import Counter

import pytest

import dataclasses

from events.offensive_formation import Formation
from events.snap import Snap
from scenarios.play import Kick, Pass, facts, load_predictors, run_play, summarize, validate_play
from scenarios.play.testing import synthetic_context, with_history


def test_baseline_plays_are_valid():
    predictors = load_predictors("baseline")
    for seed in range(3000):
        rng = random.Random(seed)
        result = run_play(synthetic_context(rng), predictors, rng)
        assert validate_play(result) == [], seed


def test_default_plays_are_valid():
    from scenarios.game import load_game_predictors
    predictors = load_game_predictors().play  # the play's, the coin toss's, and the timeout's defaults all load
    assert predictors == load_predictors()
    for seed in range(500):
        rng = random.Random(seed)
        result = run_play(synthetic_context(rng), predictors, rng)
        assert validate_play(result) == [], seed


def test_load_predictors_rejects_unknown_events():
    with pytest.raises(ValueError):
        load_predictors("baseline", handoff="baseline")


def test_baseline_timeouts_need_a_timeout():
    from scenarios.game import load_game_predictors
    timeout = load_game_predictors("baseline").timeout
    late = dict(kind="scrimmage", quarter=4, clock=100.0, clock_running=True, x=50.0, down=1, distance=10.0)
    rng = random.Random(0)
    ctx = synthetic_context(rng, **late, score={"HOME": 20, "AWAY": 17}, timeouts={"HOME": 0, "AWAY": 3},
                            offense="HOME", defense="AWAY")
    calls = [timeout(ctx, None, rng) for _ in range(500)]
    teams = [call.team for call in calls if call]
    assert set(teams) == {"AWAY"} and len(teams) > 100  # the trailing defense stops the clock
    assert all(0 <= call.seconds < 40 for call in calls if call)
    ctx = synthetic_context(rng, **late, score={"HOME": 20, "AWAY": 17}, timeouts={"HOME": 0, "AWAY": 0},
                            offense="HOME", defense="AWAY")
    assert {timeout(ctx, None, rng) for _ in range(200)} == {None}
    ctx = synthetic_context(rng, **late, score={"HOME": 20, "AWAY": 17}, timeouts={"HOME": 2, "AWAY": 2},
                            offense="HOME", defense="AWAY")
    answers = [timeout(ctx, "AWAY", rng) for _ in range(2000)]  # after the away team's timeout
    assert {call.team for call in answers if call} == {"HOME"} and 10 < sum(map(bool, answers)) < 400


def test_baseline_challenges():
    from scenarios.game import load_game_predictors
    challenge = load_game_predictors("baseline").challenge
    rng = random.Random(0)
    ctx = synthetic_context(rng, kind="scrimmage", offense="HOME", defense="AWAY", down=1, distance=10.0, x=30.0)
    outcome = summarize(run_play(ctx, load_predictors("baseline"), rng)) | {
        "action": "pass", "complete": True, "first_down": True, "touchdown": False, "turnover": False}
    calls = [challenge(ctx, outcome, ("HOME", "AWAY"), rng) for _ in range(20000)]
    made = [call for call in calls if call]
    assert 20 < len(made) < 400 and {call.team for call in made} == {"HOME", "AWAY"}  # about one completion in 150
    assert {call.won for call in made} == {True, False}
    only_home = [challenge(ctx, outcome, ("HOME",), rng) for _ in range(20000)]
    assert {call.team for call in only_home if call} == {"HOME"}


def test_a_players_past_moves_who_is_credited():
    rng = random.Random(0)
    ctx = synthetic_context(rng, kind="scrimmage", offense="HOME", defense="AWAY", down=1, distance=10.0, x=30.0)
    ctx = with_history(ctx, "AWAY-LB1", {"tackles": 90, "assists": 30, "defense_snaps": 600})
    ctx = with_history(ctx, "AWAY-LB2", {"tackles": 15, "assists": 5, "defense_snaps": 600})
    predictors, totals = load_predictors(), Counter()
    for _ in range(3000):
        for pid, line in run_play(ctx, predictors, rng).stats.items():
            for stat, value in line.items():
                totals[pid, stat] += value
                totals[stat] += value
    made = lambda pid: totals[pid, "tackles"] + totals[pid, "assists"]  # noqa: E731
    assert made("AWAY-LB1") > 2 * made("AWAY-LB2") > 0
    charted = ("pressures", "hurries", "blitzes", "missed_tackles", "coverage_targets", "coverage_yds", "pressured",
               "blitzed", "drops", "bad_throws", "rush_broken_tackles", "rec_broken_tackles", "rush_yds_before_contact")
    assert all(totals[stat] > 0 for stat in charted), [stat for stat in charted if not totals[stat]]
    assert totals["pressures"] >= totals["hurries"] + totals["sacks"] and totals["drops"] == totals["pass_drops"]
    assert totals["coverage_cmp"] <= totals["pass_cmp"] and totals["coverage_targets"] <= totals["targets"]


def test_fake_kicks():
    base, rng = load_predictors(), random.Random(0)
    ctx = synthetic_context(rng, kind="scrimmage", offense="HOME", defense="AWAY", down=4, distance=8.0, x=30.0,
                            quarter=1, clock=600.0, fair_catch_kick=False)
    punt = next(r for r in (run_play(ctx, base, rng) for _ in range(200)) if r.record[0].offense.unit == "punt")
    lineups, formation = punt.record[0], next(f for f in punt.record if isinstance(f, Formation))
    snaps = [base.snap(ctx, lineups, formation, None, ("punt", "run", "pass"), rng) for _ in range(20000)]
    fakes = [snap for snap in snaps if snap.action != "punt"]
    assert 20 < len(fakes) < 400 and {snap.action for snap in fakes} == {"run", "pass"}  # about one punt in 200
    assert all(snap.ball_to in formation.backfield for snap in fakes if snap.action == "run")

    def fake(ctx, lineups, formation, defense, allowed, rng):
        if lineups.offense.unit not in ("punt", "field_goal") or ctx.situation.kind != "scrimmage":
            return base.snap(ctx, lineups, formation, defense, allowed, rng)
        return Snap("pass") if rng.random() < 0.5 else Snap("run", rng.choice(formation.backfield))

    faked = 0
    for seed in range(300):  # the trained predictors get a punter throwing and a protector running
        rng = random.Random(seed)
        result = run_play(synthetic_context(rng, kind="scrimmage", down=4), dataclasses.replace(base, snap=fake), rng)
        assert validate_play(result) == [], seed
        faked += result.record[0].offense.unit in ("punt", "field_goal") and not facts(result.record, Kick)
    assert faked > 50


def test_fair_catch_kick_with_the_default_predictors():
    late = dict(kind="scrimmage", quarter=2, clock=3.0, clock_running=False, x=60.0, down=1, distance=10.0,
                fair_catch_kick=True)
    kinds = set()
    for seed in range(40):
        rng = random.Random(seed)
        result = run_play(synthetic_context(rng, **late), load_predictors(), rng)
        assert validate_play(result) == [] and not facts(result.record, Pass)
        kinds |= {(kick.kind, kick.result) for kick in facts(result.record, Kick)}
    assert kinds == {("fair_catch_kick", "good"), ("fair_catch_kick", "no_good")}
    rng = random.Random(0)  # with time to play, or without the catch, it's an ordinary down
    result = run_play(synthetic_context(rng, **late | {"clock": 600.0}), load_predictors(), rng)
    assert result.record[0].offense.unit == "offense"
