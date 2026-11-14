# START
# Tests for the game scenario (no data needed).
# - test_fuzz_invariants: games from random legal predictors, regular season and playoff; every invariant holds.
# - test_baseline_games: baseline games are valid, repeat by seed, and look like football.
# - test_kneel_downs_end_in_a_tie / test_a_playoff_game_has_a_winner: how a game ends.
# - test_timeouts / test_the_snap_that_never_came: stoppages called by a predictor, and the clock running
#   out (or reaching the two-minute warning) before the snap.
# - test_overtime_formats: who has had a possession and when the score ends the game, on hand-built plays.
# - test_injured_players_sit_out: availability, and the last players at a required position playing through.
# - test_disqualified_players_are_out_for_the_game: a second unsportsmanlike conduct foul, over two plays.
# - test_ten_second_runoff: the runoff, and the timeout that avoids it.
# Helpers: play(...) is a fake overtime play result with only the fields Overtime reads.
# END
import random
from types import SimpleNamespace

import pytest

from events.fouls import Foul
from events.injuries import Injury
from events.lineups import Lineup, Lineups
from events.pre_snap import PreSnap
from scenarios.game import Stoppage, describe_game, load_game_predictors, run_game, validate_game, validate_game_context
from scenarios.game.overtime import Overtime
from scenarios.game.roster import Availability
from scenarios.game.testing import chaos_game_predictors, synthetic_game, with_events
from scenarios.play import Carry, IllegalChoice
from scenarios.play.testing import synthetic_roster

H, A = "HOME", "AWAY"


def stoppages(result, kind):
    return [e for e in result.record if isinstance(e, Stoppage) and e.kind == kind]


def test_fuzz_invariants():
    predictors = chaos_game_predictors()
    for seed in range(12):
        result = run_game(synthetic_game(playoff=seed % 3 == 0), predictors, random.Random(seed))
        assert validate_game(result) == [], seed


def test_baseline_games():
    ctx, predictors = synthetic_game(), load_game_predictors("baseline")
    assert validate_game_context(ctx) == []
    games = [run_game(ctx, predictors, random.Random(seed)) for seed in range(8)]
    assert all(validate_game(game) == [] for game in games)
    again = run_game(ctx, predictors, random.Random(3))
    assert (again.score, again.stats) == (games[3].score, games[3].stats)
    assert len({tuple(game.score.values()) for game in games}) > 4
    assert all(100 < len(game.plays) < 260 for game in games)
    assert 20 < sum(sum(game.score.values()) for game in games) / 8 < 75
    assert all(len(stoppages(game, "two_minute_warning")) >= 2 for game in games)
    assert all(game.plays[0].context.situation.kind == "kickoff" for game in games)
    assert "coin toss" in describe_game(games[0], plays=True) and f"@ {H}" in describe_game(games[0])
    with pytest.raises(ValueError):
        load_game_predictors("baseline", handoff="baseline")


def kneel(ctx, rng):
    """Every scrimmage down is a kneel; everything else is the baseline's."""
    s = ctx.situation
    if s.kind != "scrimmage":
        return BASELINE.play.lineups(ctx, rng)
    offense = [f"{s.offense}-{name}" for name in ("QB1", "OL1", "OL2", "OL3", "OL4", "OL5", "RB1", "RB2", "TE1", "TE2", "WR1")]
    defense = [f"{s.defense}-{name}" for name in ("DL1", "DL2", "DL3", "DL4", "LB1", "LB2", "LB3", "DB1", "DB2", "DB3", "DB4")]
    return Lineups(Lineup("victory", "22", tuple(offense)), Lineup("defense", "base", tuple(defense)))


BASELINE = load_game_predictors("baseline")
QUIET = with_events(BASELINE, lineups=kneel, timeout=lambda ctx, rng: None,
                    pre_snap=lambda *args: PreSnap(30.0), fouls=lambda *args: (), injuries=lambda *args: ())


def test_kneel_downs_end_in_a_tie():
    result = run_game(synthetic_game(), with_events(QUIET, coin_toss=lambda ctx, rng: A,
                                                    toss_choice=lambda ctx, winner, allowed, rng: allowed[-1]),
                      random.Random(0))
    assert validate_game(result) == []
    assert result.score == {H: 0, A: 0} and result.winner is None and result.quarters == 5
    assert [e.quarter for e in stoppages(result, "period_end")] == [1, 2, 3, 4, 5]
    assert [e.quarter for e in stoppages(result, "two_minute_warning")] == [2, 4, 5]
    kickoffs = [p.context.situation for p in result.plays if p.context.situation.kind == "kickoff"]
    assert [(s.quarter, s.offense, s.clock) for s in kickoffs] == [(1, A, 900.0), (3, H, 900.0), (5, A, 600.0)]
    assert kickoffs[2].timeouts == {H: 2, A: 2}  # the away team deferred, then chose to kick in overtime
    after_warning = next(p for p in result.plays if p.context.situation.quarter == 2 and p.context.situation.clock <= 120)
    assert after_warning.context.situation.clock == 120 and not after_warning.context.situation.clock_running
    assert all(len(p.context.history) == i for i, p in enumerate(result.plays))


def test_a_playoff_game_has_a_winner():
    for seed in range(4):
        result = run_game(synthetic_game(playoff=True), chaos_game_predictors(), random.Random(seed))
        assert result.winner is not None
    with pytest.raises(RuntimeError):  # nobody can score, so a playoff game never ends
        run_game(synthetic_game(playoff=True), QUIET, random.Random(0))


def test_timeouts():
    def home_at_the_start_of_the_second(ctx, rng):
        s = ctx.situation
        return H if s.quarter == 2 and s.timeouts[H] == 3 else None

    result = run_game(synthetic_game(), with_events(QUIET, timeout=home_at_the_start_of_the_second), random.Random(0))
    assert validate_game(result) == []
    assert [(e.team, e.quarter) for e in stoppages(result, "timeout")] == [(H, 2)]
    first = next(p.context.situation for p in result.plays if p.context.situation.quarter == 2)
    assert first.timeouts == {H: 2, A: 3} and not first.clock_running
    third = next(p.context.situation for p in result.plays if p.context.situation.quarter == 3)
    assert third.timeouts == {H: 3, A: 3}
    with pytest.raises(IllegalChoice):  # a fourth timeout in a half
        run_game(synthetic_game(), with_events(QUIET, timeout=lambda ctx, rng: H), random.Random(0))


def test_the_snap_that_never_came():
    result = run_game(synthetic_game(), QUIET, random.Random(0))
    for before, after in zip(result.plays, result.plays[1:]):
        s, t = before.context.situation, after.context.situation
        if s.quarter == t.quarter and t.clock_running:
            assert t.clock == pytest.approx(s.clock - before.elapsed) and t.clock > 30  # 30 seconds run off before a snap
        if s.quarter in (1, 3) and t.quarter == s.quarter + 1:
            assert t.clock == 900 and not t.clock_running and (t.offense, t.down, t.x) == (before.next.offense, before.next.down, before.next.x)


def play(offense, score, next_offense, next_kind="scrimmage", kind="scrimmage", scores=(), carries=(), no_play=False):
    defense = A if offense == H else H
    record = tuple(Carry("x", team, "interception", 50.0, 50.0, "tackled") for team in carries)
    return SimpleNamespace(context=SimpleNamespace(situation=SimpleNamespace(kind=kind, offense=offense, defense=defense)),
                           next=SimpleNamespace(kind=next_kind, offense=next_offense, score=dict(zip((H, A), score))),
                           record=record, scores=scores, no_play=no_play)


def test_overtime_formats():
    kickoff = play(A, (0, 0), H, kind="kickoff")  # the away team kicks off; the home team has the ball
    field_goal = play(H, (3, 0), H, next_kind="kickoff", scores=((H, 3, "field_goal"),))
    touchdown = play(H, (6, 0), H, next_kind="try", scores=((H, 6, "touchdown"),))

    both = Overtime("both_possess", (H, A))
    assert not both.over(kickoff) and not both.over(touchdown)
    assert not both.over(play(H, (7, 0), H, next_kind="kickoff", scores=((H, 1, "extra_point"),)))
    assert not both.over(play(H, (7, 0), A, kind="kickoff"))
    assert not both.over(play(A, (7, 6), A, next_kind="try", scores=((A, 6, "touchdown"),)))  # the try still matters
    assert both.over(play(A, (7, 8), A, next_kind="kickoff", kind="try", scores=((A, 2, "two_point"),)))

    both = Overtime("both_possess", (H, A))
    assert not both.over(kickoff) and not both.over(field_goal) and not both.over(play(H, (3, 0), A, kind="kickoff"))
    assert both.over(play(A, (3, 0), H))  # the away team's possession ended without a score

    both = Overtime("both_possess", (H, A))
    assert not both.over(kickoff) and not both.over(field_goal) and not both.over(play(H, (3, 0), A, kind="kickoff"))
    assert both.over(play(A, (3, 6), A, next_kind="try", scores=((A, 6, "touchdown"),)))  # no try needed

    both = Overtime("both_possess", (H, A))
    assert not both.over(kickoff)
    wiped_out = play(H, (0, 0), H, carries=(A,), no_play=True)  # an interception called back by a penalty
    assert not both.over(wiped_out) and not both.over(field_goal)
    both = Overtime("both_possess", (H, A))
    assert not both.over(kickoff)
    assert both.over(play(H, (0, 6), A, next_kind="try", carries=(A,), scores=((A, 6, "touchdown"),)))  # pick-six
    both = Overtime("both_possess", (H, A))
    assert not both.over(kickoff)
    assert both.over(play(H, (0, 2), H, next_kind="safety_kick", scores=((A, 2, "safety"),)))

    modified = Overtime("modified", (H, A))
    assert not modified.over(kickoff) and not modified.over(field_goal)
    assert not modified.over(play(H, (3, 0), A, kind="kickoff"))
    assert not modified.over(play(A, (3, 3), A, next_kind="kickoff", scores=((A, 3, "field_goal"),)))
    assert modified.over(play(A, (3, 3), H, kind="kickoff")) is False
    assert modified.over(play(H, (6, 3), H, next_kind="kickoff", scores=((H, 3, "field_goal"),)))  # now sudden death
    modified = Overtime("modified", (H, A))
    assert not modified.over(kickoff) and modified.over(touchdown)
    assert Overtime("sudden_death", (H, A)).over(field_goal)


def test_injured_players_sit_out():
    players = synthetic_roster(H) + synthetic_roster(A)
    roster = Availability(players)
    roster.played((Injury("HOME-RB1", 2), Injury("HOME-K1", 999), Injury("AWAY-WR1", 999)), (), 0)
    assert roster.absences == [("HOME-RB1", 1, 2), ("AWAY-WR1", 1, 999)]  # the only kicker plays through it
    active = {p.id for p in roster.active()}
    assert "HOME-RB1" not in active and "AWAY-WR1" not in active and "HOME-K1" in active
    roster.played((), (), 1)
    assert "HOME-RB1" not in {p.id for p in roster.active()}
    same = roster.active()
    roster.played((), (), 2)
    assert "HOME-RB1" in {p.id for p in roster.active()} and "AWAY-WR1" not in {p.id for p in roster.active()}
    roster.played((), (), 3)
    assert roster.active() is not same and len(roster.active()) == len(players) - 1
    for i in range(4):
        roster.played((Injury(f"HOME-OL{i + 1}", 999),), (), 4 + i)
    assert sum(p.team == H and p.position == "OL" for p in roster.active()) == 5  # 8 linemen, 3 can be lost

    def often(ctx, lineups, record, rng):
        if rng.random() > 0.3:
            return ()
        return (Injury(rng.choice(lineups.offense.players + lineups.defense.players), rng.choice([1, 3, 10, 10, 999])),)

    hurt = with_events(chaos_game_predictors(), injuries=often)
    result = run_game(synthetic_game(), hurt, random.Random(0))
    assert validate_game(result) == [] and len(result.absences) > 40


def test_disqualified_players_are_out_for_the_game():
    def taunting(ctx, lineups, record, allowed, rng):  # the home team's first receiver, on every scrimmage play
        player = f"{H}-WR1"
        if ctx.situation.kind != "scrimmage" or player not in lineups.offense.players + lineups.defense.players:
            return ()
        return (Foul("unsportsmanlike_conduct", H, player, 50.0, "after"),)

    result = run_game(synthetic_game(), with_events(chaos_game_predictors(), fouls=taunting), random.Random(1))
    assert validate_game(result) == []
    ejected = [i for i, play in enumerate(result.plays) if play.disqualified]
    assert len(ejected) == 1 and (f"{H}-WR1", ejected[0] + 1, 999) in result.absences
    taunts = [i for i, play in enumerate(result.plays)
              if any(isinstance(f, Foul) and f.type == "unsportsmanlike_conduct" for f in play.record)]
    assert taunts == [taunts[0], ejected[0]]  # warned on the first, gone on the second


def test_ten_second_runoff():
    def false_start(ctx, lineups, formation, allowed, rng):
        s = ctx.situation
        late = s.quarter == 2 and s.clock <= 50 and s.clock_running and s.kind == "scrimmage"
        return PreSnap(5.0, Foul("false_start", s.offense, lineups.offense.players[1], s.x, "presnap") if late else None)

    result = run_game(synthetic_game(), with_events(QUIET, pre_snap=false_start), random.Random(0))
    assert validate_game(result) == []
    flagged = [p for p in result.plays if p.runoff_option]
    spent = [p for p in flagged if p.next.timeouts[p.context.situation.offense] > 0]
    assert len(stoppages(result, "timeout")) == len(spent) > 0  # a timeout avoids the runoff while there is one
    runoffs = stoppages(result, "runoff")
    assert len(runoffs) == len(flagged) - len(spent) > 0        # then ten seconds come off
    assert runoffs[0].clock == max(0.0, next(p for p in flagged if p not in spent).next.clock - 10)
