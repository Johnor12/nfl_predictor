# START
# What a dead ball means under the rules, and assembling the PlayResult.
# - next_situation(ctx, rules, los, dead) -> (Situation, scores): scoring, downs and distance, possession,
#   and the kind of the next play (try after a touchdown, kickoff after a try or field goal, safety kick).
# - expected_points(situation) / value(ctx, rules, los, dead, team): a rough worth of a result for a team,
#   used only by the hardcoded accept/decline rule in penalties.py.
# - finish(ctx, rules, los, record, live, enforcement, injuries) -> PlayResult: adds stats, elapsed time,
#   what the clock does next, and the untimed-down / 10-second-runoff flags.
# END
import dataclasses

from events.pass_rush import PassRush
from events.pre_snap import PreSnap
from scenarios.play import stats
from scenarios.play.context import FREE_KICKS
from scenarios.play.field import other, rel
from scenarios.play.record import Carry, Kick, LooseBall, PlayResult, facts


def _scores(ctx, rules, dead):
    s = ctx.situation
    if s.kind == "try":
        if dead.how == "touchdown" and dead.team == s.offense:
            return ((s.offense, 2, "two_point"),)
        if dead.how == "touchdown" and rules.defensive_try_points:
            return ((dead.team, 2, "defensive_two_point"),)
        if dead.how == "kick_good":
            return ((s.offense, 1, "extra_point"),)
        if dead.how == "safety":
            return ((other(ctx, dead.team), 1, "safety"),)
        return ()
    if dead.how == "touchdown":
        return ((dead.team, 6, "touchdown"),)
    if dead.how == "kick_good":
        return ((s.offense, 3, "field_goal"),)
    if dead.how == "safety":
        return ((other(ctx, dead.team), 2, "safety"),)
    return ()


def _shift(r, yards):
    """Move a yard line by signed yards, never more than half the distance to the goal line it moves toward."""
    return r + min(yards, (100 - r) / 2) if yards >= 0 else r - min(-yards, r / 2)


def next_situation(ctx, rules, los, dead):
    s = ctx.situation
    off = s.offense
    scores = _scores(ctx, rules, dead)
    score = dict(s.score)
    for team, points, _ in scores:
        score[team] += points

    def make(kind, team, x, down=None, distance=None):
        return dataclasses.replace(s, kind=kind, offense=team, defense=other(ctx, team), x=x,
                                   down=down, distance=distance, score=score)

    def first_down(team, r):
        return make("scrimmage", team, r, 1, min(10.0, 100 - r))

    if s.kind == "try":
        if dead.no_play and not scores:
            return make("try", off, min(99.0, max(1.0, rel(ctx, off, dead.x) + s.x - los))), scores
        return make("kickoff", off, _shift(rules.kickoff_line, dead.succeeding)), scores
    if dead.how == "touchdown":
        return make("try", dead.team, _shift(100 - rules.two_point_line, dead.succeeding)), scores
    if dead.how == "kick_good":
        return make("kickoff", off, _shift(rules.kickoff_line, dead.succeeding)), scores
    if dead.how == "safety":
        return make("safety_kick", dead.team, _shift(rules.safety_kick_line, dead.succeeding)), scores
    if s.kind in FREE_KICKS and dead.series == "replay":
        return make(s.kind, off, rel(ctx, off, dead.x)), scores
    if dead.team != off or dead.kick or s.kind in FREE_KICKS:
        return first_down(dead.team, rel(ctx, dead.team, dead.x)), scores
    r = rel(ctx, off, dead.x)
    line = rel(ctx, off, los) + s.distance
    if dead.series == "first" or r >= line:
        return first_down(off, r), scores
    down = s.down + (0 if dead.series == "replay" else 1)
    if down > 4:
        return first_down(s.defense, 100 - r), scores
    return make("scrimmage", off, r, down, line - r), scores


def expected_points(s) -> float:
    if s.kind == "try":
        return 0.95
    if s.kind in FREE_KICKS:
        return -0.6

    def first(r):
        return -1.2 + 0.075 * r

    r, d = s.x, s.distance
    if s.down < 4:
        return first(r) - (0.0, 0.45, 1.0)[s.down - 1] - 0.06 * (d - 10)
    punt = -first(max(20.0, 100 - r - 40))
    p_fg = max(0.0, min(0.98, 1.9 - 0.025 * (117 - r)))
    fg = p_fg * 2.4 - (1 - p_fg) * first(max(20.0, 100 - r + 7))
    p_go = max(0.05, 0.65 - 0.06 * d)
    go = p_go * first(min(99.0, r + d)) - (1 - p_go) * first(100 - r)
    return max(punt, fg, go)


def value(ctx, rules, los, dead, team) -> float:
    nxt, scores = next_situation(ctx, rules, los, dead)
    points = sum(p if t == team else -p for t, p, _ in scores)
    ep = expected_points(nxt)
    return points + (ep if nxt.offense == team else -ep)


def _elapsed(ctx, record, live):
    s = ctx.situation
    seconds = sum(f.seconds for f in facts(record, PreSnap)) if s.clock_running else 0.0
    if live is None:
        return seconds
    for f in record:
        if isinstance(f, (PassRush, Carry, LooseBall)):
            seconds += f.seconds
        elif isinstance(f, Kick) and f.kind in ("punt", "field_goal", "pat"):
            seconds += f.seconds  # a free kick's hang time doesn't run the clock
    return seconds


def _clock_after(ctx, live, final, nxt, scores, enforcement, remaining):
    s = ctx.situation
    if live is None:
        return "ready" if s.clock_running else "snap"
    if scores or s.kind != "scrimmage" or nxt.kind != "scrimmage" or nxt.offense != s.offense or final.kick:
        return "snap"
    if "incomplete" in (live.how, final.how):
        return "snap"
    if enforcement.accepted:
        return "ready"
    if final.how == "out_of_bounds":
        late = (s.quarter == 2 and remaining <= 120) or (s.quarter == 4 and remaining <= 300) or s.quarter >= 5
        return "snap" if late else "ready"
    return "running"


def finish(ctx, rules, los, record, live, enforcement, injuries) -> PlayResult:
    s = ctx.situation
    final = enforcement.final
    nxt, scores = next_situation(ctx, rules, los, final)
    elapsed = _elapsed(ctx, record, live)
    remaining = max(0.0, s.clock - elapsed)
    clock_after = _clock_after(ctx, live, final, nxt, scores, enforcement, remaining)
    administrative = bool(enforcement.accepted) or nxt.offense != s.offense or nxt.kind != "scrimmage"
    nxt = dataclasses.replace(nxt, clock=remaining, clock_running=clock_after == "running",
                              play_clock=rules.admin_play_clock if administrative else rules.play_clock)
    player_stats = stats.credit(ctx, los, record, final, enforcement.accepted)
    team_stats = stats.team_totals(ctx, los, record, final, player_stats, enforcement.penalty_yards)
    during = [f for f in enforcement.accepted if f.timing != "after"]
    untimed = any(f.team == s.defense for f in during) and s.clock - elapsed <= 0
    runoff = (any(f.team == s.offense for f in during) and s.clock_running
              and s.quarter in (2, 4) and s.clock <= 60)
    return PlayResult(ctx, record, live, final, enforcement.accepted, enforcement.declined,
                      enforcement.penalty_yards, scores, nxt, player_stats, team_stats, elapsed,
                      clock_after, untimed, runoff, injuries)
