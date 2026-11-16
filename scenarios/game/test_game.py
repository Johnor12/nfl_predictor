# START
# Tests for the game scenario (no data needed).
# - test_fuzz_invariants: games from random legal predictors, regular season and playoff; every invariant holds.
# - test_baseline_games: baseline games are valid, repeat by seed, and look like football.
# - test_kneel_downs_end_in_a_tie / test_a_playoff_game_has_a_winner: how a game ends.
# - test_timeouts / test_a_timeout_takes_what_ran_before_it / test_the_snap_that_never_came: stoppages called
#   by a predictor (one by each team in a dead ball at most), the running clock before the call, and the
#   clock running out (or reaching the two-minute warning) before the snap.
# - test_overtime_formats: who has had a possession and when the score ends the game, on hand-built plays.
# - test_a_third_overtime_period_starts_with_a_kickoff: a postseason game that goes on and on.
# - test_injured_players_sit_out / test_emergency_replacements: availability, and the stand-ins at a position
#   a team can't play without.
# - test_an_injury_after_the_two_minute_warning_costs_a_timeout: the charge, and the excess timeout's runoff.
# - test_challenges: what a challenge costs, how many a team has, and when it may not.
# - test_a_fair_catch_kick_extends_the_half: the kick with no time left, and the half ending without it.
# - test_disqualified_players_are_out_for_the_game: a second unsportsmanlike conduct foul, over two plays.
# - test_ten_second_runoff: the runoff, and the timeout that avoids it.
# Helpers: play(...) is a fake overtime play result with only the fields Overtime reads.
# END
import random
from types import SimpleNamespace

import pytest

from events.challenge import Challenge
from events.fouls import Foul
from events.injuries import Injury
from events.kick_attempt import KickAttempt
from events.lineups import Lineup, Lineups
from events.lineups.predictors.baseline.depth_chart import unit_lineup
from events.pre_snap import PreSnap
from events.punt_kick import PuntKick
from events.punt_result import PuntResult
from events.timeout import Timeout
from scenarios.game import Stoppage, clock, describe_game, load_game_predictors, run_game, validate_game, validate_game_context
from scenarios.game.overtime import Overtime
from scenarios.game.roster import Availability
from scenarios.game.testing import chaos_game_predictors, synthetic_game, with_events
from scenarios.play import Carry, IllegalChoice, Kick, facts
from scenarios.play.testing import synthetic_roster
from shared.rulebook import rules_for

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
    def first(team, **counts):  # the first available players at each position
        return tuple(p.id for position, count in counts.items()
                     for p in [p for p in ctx.roster(team) if p.position == position][:count])

    return Lineups(Lineup("victory", "22", first(s.offense, QB=1, OL=5, RB=2, TE=2, WR=1)),
                   Lineup("defense", "base", first(s.defense, DL=4, LB=3, DB=4)))


BASELINE = load_game_predictors("baseline")
QUIET = with_events(BASELINE, lineups=kneel, timeout=lambda *args: None, challenge=lambda *args: None,
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
    def home_at_the_start_of_the_second(ctx, called, rng):
        s = ctx.situation
        return Timeout(H) if s.quarter == 2 and s.timeouts[H] == 3 else None

    result = run_game(synthetic_game(), with_events(QUIET, timeout=home_at_the_start_of_the_second), random.Random(0))
    assert validate_game(result) == []
    assert [(e.team, e.quarter) for e in stoppages(result, "timeout")] == [(H, 2)]
    first = next(p.context.situation for p in result.plays if p.context.situation.quarter == 2)
    assert first.timeouts == {H: 2, A: 3} and not first.clock_running
    third = next(p.context.situation for p in result.plays if p.context.situation.quarter == 3)
    assert third.timeouts == {H: 3, A: 3}
    with pytest.raises(IllegalChoice):  # a fourth timeout in a half
        run_game(synthetic_game(), with_events(QUIET, timeout=lambda ctx, called, rng: None if called else Timeout(H)),
                 random.Random(0))

    def one_each(ctx, called, rng):  # the away team answers the home team's timeout with its own
        s = ctx.situation
        if s.quarter != 2 or s.timeouts[A] < 3:
            return None
        return Timeout(A) if called == H else None if called else Timeout(H)

    result = run_game(synthetic_game(), with_events(QUIET, timeout=one_each), random.Random(0))
    assert validate_game(result) == []
    assert [(e.team, e.quarter, e.clock) for e in stoppages(result, "timeout")] == [(H, 2, 900.0), (A, 2, 900.0)]
    with pytest.raises(IllegalChoice):  # the same team twice in one dead ball
        run_game(synthetic_game(), with_events(QUIET, timeout=lambda ctx, called, rng: Timeout(H)), random.Random(0))


def test_a_timeout_takes_what_ran_before_it():
    def late_in_the_play_clock(ctx, called, rng):
        s = ctx.situation
        return Timeout(H, 35.0) if s.quarter == 1 and s.clock_running and s.timeouts[H] == 3 else None

    result = run_game(synthetic_game(), with_events(QUIET, timeout=late_in_the_play_clock), random.Random(0))
    assert validate_game(result) == []
    called = stoppages(result, "timeout")[0]
    before, after = [(a, b) for a, b in zip(result.plays, result.plays[1:])
                     if b.context.situation.timeouts[H] == 2 and a.next.timeouts[H] == 3][0]
    assert called.clock == after.context.situation.clock == pytest.approx(before.next.clock - 35)
    assert not after.context.situation.clock_running
    game = synthetic_game().game
    running = SimpleNamespace(quarter=4, clock=130.0, clock_running=True)
    assert clock.at_timeout(game, running, 35.0) == 121.0  # called before the two-minute warning stops the clock
    assert clock.at_timeout(game, SimpleNamespace(quarter=4, clock=20.0, clock_running=True), 35.0) == 1.0
    assert clock.at_timeout(game, SimpleNamespace(quarter=1, clock=500.0, clock_running=False), 35.0) == 500.0


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


def test_a_third_overtime_period_starts_with_a_kickoff():
    class Enough(Exception):
        pass

    first = {}  # the situation each period starts from

    def watch(ctx, called, rng):
        s = ctx.situation
        first.setdefault(s.quarter, s)
        if s.quarter == 10:
            raise Enough

    away_receives = dict(coin_toss=lambda ctx, rng: A, toss_choice=lambda ctx, winner, allowed, rng: "receive")
    with pytest.raises(Enough):  # nobody can score
        run_game(synthetic_game(playoff=True), with_events(QUIET, timeout=watch, **away_receives), random.Random(0))
    assert [(first[q].kind, first[q].offense) for q in (5, 7, 9)] == [("kickoff", H), ("kickoff", A), ("kickoff", H)]
    assert [first[q].kind for q in (6, 8, 10)] == ["scrimmage"] * 3  # play goes on from where it was
    assert first[6].timeouts == first[5].timeouts and (first[7].timeouts, first[7].clock) == ({H: 3, A: 3}, 900.0)


def test_injured_players_sit_out():
    players = synthetic_roster(H) + synthetic_roster(A)
    roster = Availability(players)
    assert roster.active() is players
    roster.played((Injury("HOME-RB1", 2), Injury("AWAY-WR1", 999)), (), 0)
    assert roster.absences == [("HOME-RB1", 1, 2), ("AWAY-WR1", 1, 999)]
    active = {p.id for p in roster.active()}
    assert "HOME-RB1" not in active and "AWAY-WR1" not in active
    roster.played((), (), 1)
    assert "HOME-RB1" not in {p.id for p in roster.active()}
    same = roster.active()
    roster.played((), (), 2)
    assert "HOME-RB1" in {p.id for p in roster.active()} and "AWAY-WR1" not in {p.id for p in roster.active()}
    roster.played((), (), 3)
    assert roster.active() is not same and len(roster.active()) == len(players) - 1

    def often(ctx, lineups, record, rng):
        if rng.random() > 0.3:
            return ()
        return (Injury(rng.choice(lineups.offense.players + lineups.defense.players), rng.choice([1, 3, 10, 10, 999])),)

    for predictors in (chaos_game_predictors(), BASELINE):
        result = run_game(synthetic_game(), with_events(predictors, injuries=often), random.Random(0))
        assert validate_game(result) == [] and len(result.absences) > 30


def test_emergency_replacements():
    roster = Availability(synthetic_roster(H) + synthetic_roster(A))
    positions = lambda: {p.id: p.position for p in roster.active()}
    roster.played((Injury("HOME-K1", 999), Injury("HOME-QB1", 2)), (), 0)
    now = positions()
    assert "HOME-K1" not in now and now["HOME-DB1"] == "K" and now["HOME-P1"] == "P"  # the punter is needed where he is
    assert "HOME-QB1" not in now and now["HOME-QB2"] == "QB" and now["HOME-RB1"] == "RB"  # the backup plays
    roster.played((Injury("HOME-QB2", 999),), (), 1)
    assert positions()["HOME-RB1"] == "QB"  # nobody left: a back takes the snaps
    roster.played((), (), 2)
    assert positions()["HOME-RB1"] == "RB" and positions()["HOME-QB1"] == "QB"  # until the starter is back
    for i in range(4):
        roster.played((Injury(f"HOME-OL{i + 1}", 999),), (), 3 + i)
    now = positions()
    assert sum(position == "OL" for pid, position in now.items() if pid.startswith(H)) == 5 and now["HOME-DL1"] == "OL"
    assert all(p.position == q.position for p, q in zip(roster.active(), synthetic_roster(A)[::-1]) if p.id == q.id)
    roster.played((), ("HOME-P1",), 7)  # a disqualified punter: the backup quarterback would punt, but he is hurt
    assert positions()["HOME-DB2"] == "P" and len(roster.absences) == 8
    no_punter = tuple(p for p in synthetic_roster(H) if p.position != "P")
    roster = Availability(no_punter)  # a team that came without a punter isn't given one
    roster.played((Injury("HOME-RB1", 1),), (), 0)
    assert all(p.position != "P" for p in roster.active())


def test_an_injury_after_the_two_minute_warning_costs_a_timeout():
    def hurt(ctx, lineups, record, rng):  # an offensive player, on every scrimmage down late in the first half
        s = ctx.situation
        return (Injury(lineups.offense.players[-1], 1),) if s.kind == "scrimmage" and s.quarter == 2 and s.clock <= 120 else ()

    result = run_game(synthetic_game(), with_events(QUIET, injuries=hurt), random.Random(0))
    assert validate_game(result) == []
    charged, excess = stoppages(result, "injury_timeout"), stoppages(result, "excess_timeout")
    assert charged and excess and all(e.quarter == 2 and e.clock <= 120 for e in charged + excess)
    for team in (H, A):
        mine = [e for e in result.record if isinstance(e, Stoppage) and e.team == team and e.quarter == 2]
        kinds = [e.kind for e in mine]
        assert kinds[:3] == ["injury_timeout"] * min(3, len(kinds)) and set(kinds[3:]) <= {"excess_timeout"}
    for i, entry in enumerate(result.record):
        if entry in excess:  # the offense had no timeout left: ten seconds come off a running clock
            runoff = result.record[i + 1]
            assert (runoff.kind, runoff.clock) == ("runoff", max(0.0, entry.clock - 10))
        if entry in charged + excess:  # never for a down that turned the ball over
            before = result.record[i - 1]
            assert before.next.offense == before.context.situation.offense == entry.team
    game, fine = synthetic_game().game, SimpleNamespace(kind="scrimmage", quarter=2, clock=500.0, offense=H, defense=A)
    assert clock.injury_timeouts(game, fine, SimpleNamespace(injuries=(Injury("HOME-QB1", 1),))) == ()  # before the warning


def test_challenges():
    def home(won):
        return lambda ctx, outcome, allowed, rng: Challenge(H, won) if H in allowed else None

    result = run_game(synthetic_game(), with_events(QUIET, challenge=home(False)), random.Random(0))
    assert validate_game(result) == []
    lost = stoppages(result, "challenge_lost")  # two a game, and each one lost costs a timeout
    assert [(e.team, e.quarter) for e in lost] == [(H, 1), (H, 1)] and not stoppages(result, "timeout")
    second = next(p.context.situation for p in result.plays if p.context.situation.quarter == 2)
    assert second.timeouts == {H: 1, A: 3}
    result = run_game(synthetic_game(), with_events(QUIET, challenge=home(True)), random.Random(0))
    assert validate_game(result) == []
    assert len(stoppages(result, "challenge_won")) == 3  # a third for winning, and no timeout lost
    assert all(p.context.situation.timeouts[H] == 3 for p in result.plays if p.context.situation.quarter <= 4)
    with pytest.raises(IllegalChoice):
        run_game(synthetic_game(), with_events(QUIET, challenge=lambda *args: Challenge("NOBODY", True)), random.Random(0))

    game, s = synthetic_game().game, SimpleNamespace(quarter=1, clock=500.0, offense=H, defense=A)
    may = lambda season, used, s=s, timeouts={H: 3, A: 0}: clock.challengers(game, rules_for(season), s, timeouts, {H: used, A: []})
    assert may(2026, []) == (H,)  # the away team has no timeout to lose
    assert may(2026, [True, False]) == (H,) and may(2026, [False, False]) == () and may(2026, [True, True, True]) == ()
    assert may(2023, [True, False]) == () and may(2023, [True, True]) == (H,)  # both had to be won before 2024
    assert may(2026, [], SimpleNamespace(quarter=4, clock=100.0, offense=H, defense=A)) == ()  # after the warning
    assert may(2026, [], SimpleNamespace(quarter=5, clock=500.0, offense=H, defense=A)) == ()  # overtime


def test_a_fair_catch_kick_extends_the_half():
    def punt_then_kick(kicks):
        def lineups(ctx, rng):
            s = ctx.situation
            if s.kind != "scrimmage" or s.quarter != 2:
                return kneel(ctx, rng)
            if s.fair_catch_kick and s.clock == 0:
                unit, other = ("fair_catch_kick", "field_goal_block") if kicks else ("victory", "defense")
            elif s.clock <= 40 and s.clock_running:
                unit, other = "punt", "punt_return"
            else:
                return kneel(ctx, rng)
            return Lineups(Lineup(unit, None, unit_lineup(ctx, s.offense, unit, rng)),
                           Lineup(other, None, unit_lineup(ctx, s.defense, other, rng)))
        return lineups

    def last_second(ctx, lineups, formation, allowed, rng):  # the punt is snapped with a second left
        return PreSnap(ctx.situation.clock - 1.0 if lineups.offense.unit == "punt" else 30.0)

    def play_out(kicks):
        fair_catch = lambda ctx, lineups, land, allowed, rng: PuntResult("fair_catch", lineups.defense.players[0])
        events = dict(lineups=punt_then_kick(kicks), pre_snap=last_second, punt_kick=lambda *args: PuntKick(5.0, None, 4.0),
                      punt_result=fair_catch, kick_attempt=lambda *args: KickAttempt("good", None, 3.0))
        result = run_game(synthetic_game(), with_events(QUIET, **events), random.Random(0))
        assert validate_game(result) == []
        half = [p for p in result.plays if p.context.situation.quarter == 2]
        return result, half[-2:], [p for p in half if facts(p.record, Kick)]

    result, (punt, kick), kicks = play_out(True)
    assert len(kicks) == 2 and punt.next.fair_catch_kick and punt.next.clock == 0
    assert kick.context.situation.clock == 0 and facts(kick.record, Kick)[0].kind == "fair_catch_kick"
    assert kick.scores == ((punt.next.offense, 3, "field_goal"),) and sum(result.score.values()) == 3
    result, (_, punt), kicks = play_out(False)  # the team lets the half end: no down is played
    assert len(kicks) == 1 and punt.next.fair_catch_kick and sum(result.score.values()) == 0


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
