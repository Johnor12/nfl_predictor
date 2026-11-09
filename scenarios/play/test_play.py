# START
# Tests for the play scenario.
# - test_fuzz_invariants: thousands of plays from random legal predictors and situations; every invariant holds.
# - Hand-built rule tests: scripted predictor outputs for specific rules (scoring, end zones, kicks, fouls).
# Helpers: situation(...) builds a HOME-offense context; base() is a quiet scripted predictor set
# (fixed lineups/formation, no fouls); play(ctx, **outputs) runs one play with outputs scripted.
# END
import random

from scenarios.play import run_play, validate_play
from scenarios.play.events import (CarryEnd, DefensiveFormation, Foul, Formation, FreeKick, KickAttempt, KickOutcome,
                                   Lineup, Lineups, PassResult, PassRush, PreSnap, PuntKick, Recovery, Snap, Target)
from scenarios.play.testing import chaos_predictors, scripted, synthetic_context

H, A = "HOME", "AWAY"
OFFENSE = Lineup("offense", "11", ("HOME-QB1", "HOME-OL1", "HOME-OL2", "HOME-OL3", "HOME-OL4", "HOME-OL5",
                                   "HOME-RB1", "HOME-WR1", "HOME-WR2", "HOME-WR3", "HOME-TE1"))
DEFENSE = Lineup("defense", "base", ("AWAY-DL1", "AWAY-DL2", "AWAY-DL3", "AWAY-DL4", "AWAY-LB1", "AWAY-LB2",
                                     "AWAY-LB3", "AWAY-DB1", "AWAY-DB2", "AWAY-DB3", "AWAY-DB4"))
FORMATION = Formation("singleback", ("HOME-WR1", "HOME-OL1", "HOME-OL2", "HOME-OL3", "HOME-OL4", "HOME-OL5", "HOME-TE1"),
                      ("HOME-QB1", "HOME-RB1", "HOME-WR2", "HOME-WR3"), "HOME-QB1", True)
PUNT = Lineup("punt", None, ("HOME-P1", "HOME-LS1", "HOME-LB1", "HOME-LB2", "HOME-LB3", "HOME-DB1", "HOME-DB2",
                             "HOME-DB3", "HOME-TE1", "HOME-TE2", "HOME-TE3"))
PUNT_FORMATION = Formation("punt", ("HOME-DB1", "HOME-LB1", "HOME-LB2", "HOME-LS1", "HOME-LB3", "HOME-TE1", "HOME-DB2"),
                           ("HOME-P1", "HOME-DB3", "HOME-TE2", "HOME-TE3"), "HOME-P1", False)
FIELD_GOAL = Lineup("field_goal", None, ("HOME-K1", "HOME-P1", "HOME-LS1", "HOME-OL1", "HOME-OL2", "HOME-OL3",
                                         "HOME-OL4", "HOME-OL5", "HOME-TE1", "HOME-TE2", "HOME-TE3"))
FG_FORMATION = Formation("field goal", ("HOME-TE1", "HOME-OL1", "HOME-OL2", "HOME-LS1", "HOME-OL3", "HOME-OL4", "HOME-OL5"),
                         ("HOME-P1", "HOME-K1", "HOME-TE2", "HOME-TE3"), "HOME-P1", False)
KICKOFF = Lineup("kickoff", None, ("HOME-K1", "HOME-LB1", "HOME-LB2", "HOME-LB3", "HOME-DB1", "HOME-DB2", "HOME-DB3",
                                   "HOME-TE1", "HOME-TE2", "HOME-RB2", "HOME-WR4"))
RETURN = Lineup("kick_return", None, DEFENSE.players)


def situation(kind="scrimmage", x=50.0, down=1, distance=10.0, **kw):
    fields = dict(kind=kind, offense=H, defense=A, x=x, down=down, distance=distance, score={H: 0, A: 0},
                  quarter=1, clock=600.0, clock_running=True, timeouts={H: 3, A: 3})
    fields.update(kw)
    return synthetic_context(random.Random(0), **fields)


def base():
    return scripted(chaos_predictors(), lineups=Lineups(OFFENSE, DEFENSE), offensive_formation=FORMATION,
                    defensive_formation=DefensiveFormation(7, 1), pre_snap=PreSnap(10.0), fouls=(), injuries=())


def play(ctx, **outputs):
    result = run_play(ctx, scripted(base(), **outputs), random.Random(0))
    assert validate_play(result) == []
    return result


def run(yards, how="tackled", **kw):
    return dict(snap=Snap("run", "HOME-RB1"), carry=CarryEnd(yards, how, ("AWAY-LB1",), seconds=4.0), **kw)


def test_fuzz_invariants():
    predictors = chaos_predictors()
    for seed in range(5000):
        rng = random.Random(seed)
        result = run_play(synthetic_context(rng), predictors, rng)
        assert validate_play(result) == [], seed


def test_run_gain_and_first_down():
    r = play(situation(x=40, down=3, distance=4), **run(6))
    assert r.stats["HOME-RB1"] == {"rush_att": 1, "rush_yds": 6}
    assert r.stats["AWAY-LB1"] == {"tackles": 1}
    assert (r.next.offense, r.next.x, r.next.down, r.next.distance) == (H, 46, 1, 10)
    assert r.clock_after == "running" and r.elapsed == 14.0


def test_touchdown_counts_yards_to_the_goal_line():
    r = play(situation(x=95, distance=5), **run(12))
    assert r.stats["HOME-RB1"]["rush_yds"] == 5 and r.stats["HOME-RB1"]["rush_td"] == 1
    assert r.scores == ((H, 6, "touchdown"),)
    assert (r.next.kind, r.next.offense, r.next.score[H]) == ("try", H, 6)


def test_safety_and_safety_kick():
    r = play(situation(x=1), **run(-3))
    assert r.next.kind == "safety_kick" and r.scores == ((A, 2, "safety"),)
    assert (r.next.kind, r.next.offense, r.next.x) == ("safety_kick", H, 20)


def test_turnover_on_downs_after_incomplete_pass():
    r = play(situation(x=60, down=4, distance=3), snap=Snap("pass"), pass_rush=PassRush(4, "throw", 3.0),
             target=Target("HOME-WR1", 12, "left"), pass_result=PassResult("incomplete", "AWAY-DB1"))
    assert (r.next.offense, r.next.x, r.next.down) == (A, 40, 1)
    assert r.stats["HOME-QB1"] == {"pass_att": 1} and r.stats["AWAY-DB1"] == {"passes_defended": 1}


def test_completion_with_fumble_credits_yards_to_the_fumble_spot():
    r = play(situation(x=30), snap=Snap("pass"), pass_rush=PassRush(4, "throw", 2.5),
             target=Target("HOME-TE1", 8, "middle"), pass_result=PassResult("complete"),
             carry=[CarryEnd(7, "fumble", forced_by="AWAY-LB2"), CarryEnd(0, "down")],
             loose_ball=Recovery(A, "AWAY-DB2", 44))
    assert r.stats["HOME-QB1"]["pass_yds"] == r.stats["HOME-TE1"]["rec_yds"] == 15
    assert r.stats["HOME-TE1"]["fumbles_lost"] == 1 and r.stats["AWAY-LB2"]["forced_fumbles"] == 1
    assert (r.next.offense, r.next.x) == (A, 56)


def test_sack_yards_are_team_yards():
    r = play(situation(x=50), snap=Snap("pass"),
             pass_rush=PassRush(5, "sack", 3.0, sackers=("AWAY-DL1", "AWAY-DL2"), sack_yards=8))
    assert r.stats["HOME-QB1"] == {"sacked": 1} and r.stats["AWAY-DL1"] == {"sacks": 0.5}
    assert r.team_stats[H]["sack_yards"] == 8 and (r.next.x, r.next.down) == (42, 2)


def test_interception_in_end_zone_downed_is_a_touchback():
    r = play(situation(x=80), snap=Snap("pass"), pass_rush=PassRush(4, "throw", 3.0),
             target=Target("HOME-WR2", 25, "right"), pass_result=PassResult("intercepted", "AWAY-DB3"),
             carry=CarryEnd(0, "down"))
    assert (r.next.kind, r.next.offense, r.next.x) == ("scrimmage", A, 20) and not r.scores


def test_momentum_rule_on_interception_inside_the_5():
    r = play(situation(x=90), snap=Snap("pass"), pass_rush=PassRush(4, "throw", 3.0),
             target=Target("HOME-WR2", 7, "right"), pass_result=PassResult("intercepted", "AWAY-DB3"),
             carry=CarryEnd(-6, "tackled", ("HOME-WR2",)))
    assert (r.next.kind, r.next.offense, r.next.x) == ("scrimmage", A, 3) and not r.scores


def test_fourth_down_fumble_recovered_by_teammate_is_spotted_at_the_fumble():
    r = play(situation(x=50, down=4, distance=10), **run(6, "fumble"),
             loose_ball=Recovery(H, "HOME-WR1", 60))
    assert (r.next.offense, r.next.x) == (A, 44)  # spotted at the fumble (56), short of the line: turnover on downs


def test_forward_fumble_out_of_bounds_comes_back():
    r = play(situation(x=50), **run(4, "fumble"), loose_ball=Recovery(None, None, 61))
    assert (r.next.offense, r.next.x, r.next.down) == (H, 54, 2)


def test_punt_into_end_zone_is_a_touchback():
    r = play(situation(x=55, down=4), lineups=Lineups(PUNT, DEFENSE), offensive_formation=PUNT_FORMATION,
             snap=Snap("punt"), punt_kick=PuntKick(50, seconds=4.5), punt_result=KickOutcome("touchback"))
    assert (r.next.offense, r.next.x) == (A, 20) and r.stats["HOME-P1"]["punt_yds"] == 45


def test_punt_return_and_fair_catch():
    r = play(situation(x=30, down=4), lineups=Lineups(PUNT, DEFENSE), offensive_formation=PUNT_FORMATION,
             snap=Snap("punt"), punt_kick=PuntKick(45), punt_result=KickOutcome("return", "AWAY-DB4"),
             carry=CarryEnd(12, "tackled", ("HOME-LB2",)))
    assert (r.next.offense, r.next.x) == (A, 37) and r.stats["AWAY-DB4"]["punt_ret_yds"] == 12
    r = play(situation(x=30, down=4), lineups=Lineups(PUNT, DEFENSE), offensive_formation=PUNT_FORMATION,
             snap=Snap("punt"), punt_kick=PuntKick(45), punt_result=KickOutcome("fair_catch", "AWAY-DB4"))
    assert (r.next.offense, r.next.x) == (A, 25)


def test_missed_field_goal_spot_of_kick_or_the_20():
    fg = dict(lineups=Lineups(FIELD_GOAL, DEFENSE), offensive_formation=FG_FORMATION, snap=Snap("field_goal"))
    r = play(situation(x=65, down=4), **fg, kick_attempt=KickAttempt("no_good", seconds=3.0))
    assert (r.next.offense, r.next.x) == (A, 42)  # spot of the kick: 7 yards behind the line
    r = play(situation(x=90, down=4), **fg, kick_attempt=KickAttempt("no_good"))
    assert (r.next.offense, r.next.x) == (A, 20)  # spot of the kick is inside the 20
    r = play(situation(x=85, down=4), **fg, kick_attempt=KickAttempt("good"))
    assert r.scores == ((H, 3, "field_goal"),) and r.stats["HOME-K1"] == {"fg_att": 1, "fg_made": 1}
    assert (r.next.kind, r.next.offense, r.next.x) == ("kickoff", H, 35)


def test_try_kick_from_the_15_and_two_point_try():
    r = play(situation("try", x=98, down=None, distance=None), lineups=Lineups(FIELD_GOAL, DEFENSE),
             offensive_formation=FG_FORMATION, snap=Snap("field_goal"), kick_attempt=KickAttempt("good"))
    assert r.scores == ((H, 1, "extra_point"),) and r.next.kind == "kickoff"
    assert r.record[0].offense.unit == "field_goal" and r.stats["HOME-K1"] == {"xp_att": 1, "xp_made": 1}
    r = play(situation("try", x=98, down=None, distance=None), **run(3))
    assert r.scores == ((H, 2, "two_point"),) and r.stats["HOME-RB1"] == {"two_pt": 1}


def test_penalty_on_a_kicked_try_carries_to_the_retry():
    kick = dict(lineups=Lineups(FIELD_GOAL, DEFENSE), offensive_formation=FG_FORMATION)
    r = play(situation("try", x=98, down=None, distance=None), **kick,
             pre_snap=PreSnap(10.0, Foul("false_start", H, "HOME-OL1", 85, "presnap")))
    assert (r.next.kind, r.next.x) == ("try", 93)
    r = play(r.context.__class__(r.context.game, r.next, r.context.players), **kick, snap=Snap("field_goal"),
             kick_attempt=KickAttempt("good"))
    assert r.record[-1].x == 80 and r.scores == ((H, 1, "extra_point"),)  # kicked from the 20


def test_dynamic_kickoff_rules():
    ko = dict(lineups=Lineups(KICKOFF, RETURN))
    ctx = situation("kickoff", x=35, down=None, distance=None)
    r = play(ctx, **ko, free_kick=FreeKick("HOME-K1", 40), kick_result=KickOutcome("return", "AWAY-DB1"))
    assert (r.next.offense, r.next.x) == (A, 40)  # short of the landing zone
    r = play(ctx, **ko, free_kick=FreeKick("HOME-K1", 70), kick_result=KickOutcome("touchback"))
    assert (r.next.offense, r.next.x) == (A, 35)  # in the end zone in the air
    r = play(ctx, **ko, free_kick=FreeKick("HOME-K1", 60), kick_result=KickOutcome("touchback"))
    assert (r.next.offense, r.next.x) == (A, 20)  # landing zone, then into the end zone
    r = play(ctx, **ko, free_kick=FreeKick("HOME-K1", 62), kick_result=KickOutcome("return", "AWAY-DB1"),
             carry=CarryEnd(25, "tackled", ("HOME-LB1",)))
    assert (r.next.offense, r.next.x) == (A, 28) and r.stats["AWAY-DB1"]["kick_ret_yds"] == 25
    r = play(ctx, **ko, free_kick=FreeKick("HOME-K1", 50, out_of_bounds=True))
    assert (r.next.offense, r.next.x) == (A, 40)


def test_half_the_distance_and_presnap_fouls():
    r = play(situation(x=6), pre_snap=PreSnap(20.0, Foul("false_start", H, "HOME-OL2", 6, "presnap")))
    assert r.no_play and (r.next.x, r.next.down, r.next.distance) == (3, 1, 13)
    assert r.stats == {"HOME-OL2": {"penalties": 1}} and r.clock_after == "ready"


def test_offensive_holding_in_own_end_zone_is_a_safety():
    r = play(situation(x=3), **run(2), fouls=(Foul("offensive_holding", H, "HOME-OL1", -1, "live"),))
    assert r.scores == ((A, 2, "safety"),) and r.no_play


def test_defensive_pass_interference_is_a_spot_foul():
    pass_play = dict(snap=Snap("pass"), pass_rush=PassRush(4, "throw", 3.0), target=Target("HOME-WR1", 35, "left"),
                     pass_result=PassResult("incomplete", "AWAY-DB1"))
    r = play(situation(x=40), **pass_play, fouls=(Foul("defensive_pass_interference", A, "AWAY-DB1", 75, "live"),))
    assert (r.next.offense, r.next.x, r.next.down) == (H, 75, 1) and r.no_play
    r = play(situation(x=80), **pass_play, fouls=(Foul("defensive_pass_interference", A, "AWAY-DB1", 104, "live"),))
    assert (r.next.x, r.next.distance) == (99, 1)


def test_accept_or_decline():
    pass_play = dict(snap=Snap("pass"), pass_rush=PassRush(4, "throw", 3.0), target=Target("HOME-WR1", 10, "left"),
                     pass_result=PassResult("incomplete"))
    holding = (Foul("offensive_holding", H, "HOME-OL3", 50, "live"),)
    r = play(situation(x=50, down=3, distance=5), **pass_play, fouls=holding)
    assert r.declined == holding and (r.next.offense, r.next.down) == (H, 4)
    r = play(situation(x=50, down=1, distance=10), **run(3), fouls=holding)
    assert r.accepted == holding and (r.next.x, r.next.down, r.next.distance) == (40, 1, 20)


def test_offsetting_fouls_replay_the_down():
    fouls = (Foul("offensive_holding", H, "HOME-OL3", 50, "live"), Foul("face_mask", A, "AWAY-LB1", 55, "live"))
    r = play(situation(x=50, down=2, distance=7), **run(5), fouls=fouls)
    assert r.no_play and (r.next.x, r.next.down, r.next.distance) == (50, 2, 7)


def test_personal_foul_after_a_gain_is_added_on():
    r = play(situation(x=30, down=2, distance=8), **run(5),
             fouls=(Foul("unnecessary_roughness", A, "AWAY-LB1", 35, "after"),))
    assert not r.no_play and r.stats["HOME-RB1"]["rush_yds"] == 5
    assert (r.next.x, r.next.down) == (50, 1)


def test_out_of_bounds_clock():
    early = play(situation(x=30, quarter=2, clock=400.0), **run(5, "out_of_bounds"))
    late = play(situation(x=30, quarter=2, clock=100.0), **run(5, "out_of_bounds"))
    assert (early.clock_after, late.clock_after) == ("ready", "snap")
