# START
# A play's outcome in a few values, with the names nflverse uses for a real play.
# - summarize(result) -> dict: action, yards, points by team, touchdown, turnover, penalty, first_down,
#   complete, field_goal_result, extra_point_result, kick_distance, touchback, return_yards, seconds. Same keys
#   and meaning as a real play's outcome (shared/nflverse/contexts.py _actual), so the two can be compared.
# - play_summary(result) -> PlaySummary: the entry the game scenario adds to the next play's history (same
#   tags as shared/nflverse/contexts.py _summary).
# END
from events.pass_rush import PassRush
from events.snap import Snap
from scenarios.play.context import PlaySummary
from scenarios.play.field import field_goal_distance
from scenarios.play.record import Kick, Pass, facts
from shared.rulebook import rules_for

KICK_ACTIONS = {"punt": "punt", "field_goal": "field_goal", "pat": "extra_point", "kickoff": "kickoff",
                "safety_kick": "kickoff", "onside_kickoff": "kickoff"}
RUSH_ACTIONS = {"sack": "sack", "strip_sack": "sack", "scramble": "scramble"}
FIELD_GOAL_RESULTS = {"good": "made", "no_good": "missed", "blocked": "blocked"}  # nflverse's names
EXTRA_POINT_RESULTS = {"good": "good", "no_good": "failed", "blocked": "blocked"}


def _action(r, kick) -> str:
    if r.no_play:
        return "no_play"
    if kick:
        return KICK_ACTIONS[kick.kind]
    rush = facts(r.record, PassRush)
    return RUSH_ACTIONS.get(rush[0].result, "pass") if rush else facts(r.record, Snap)[0].action


def summarize(r) -> dict:
    s = r.context.situation
    offense, teams = r.team_stats[s.offense], r.team_stats.values()
    kick = next(iter(facts(r.record, Kick)), None)
    place_kick = kick.kind if kick and kick.kind in ("field_goal", "pat") else None
    if place_kick:
        kick_distance = field_goal_distance(rules_for(r.context.game.season), kick.x)
    else:
        kick_distance = kick.land - kick.x if kick and kick.land is not None else None
    return {
        "action": _action(r, kick),
        "yards": offense.get("rush_yds", 0) + offense.get("rec_yds", 0) - offense.get("sack_yards", 0),
        "points": {team: sum(points for scorer, points, _ in r.scores if scorer == team) for team in s.score},
        "touchdown": any(how == "touchdown" for _, _, how in r.scores),
        "turnover": any(t.get("int_thrown", 0) or t.get("fumbles_lost", 0) for t in teams),
        "penalty": bool(r.accepted or r.declined),
        "first_down": s.kind == "scrimmage" and (
            (r.next.kind == "scrimmage" and r.next.offense == s.offense and r.next.down == 1)
            or any(team == s.offense and how == "touchdown" for team, _, how in r.scores)),  # a touchdown counts
        "complete": any(p.result == "complete" for p in facts(r.record, Pass)),
        "field_goal_result": FIELD_GOAL_RESULTS.get(kick.result) if place_kick == "field_goal" else None,
        "extra_point_result": EXTRA_POINT_RESULTS.get(kick.result) if place_kick == "pat" else None,
        "kick_distance": kick_distance,
        "touchback": r.live is not None and r.live.how == "touchback",
        "return_yards": sum(t.get(key, 0) for t in teams for key in ("punt_ret_yds", "kick_ret_yds")),
        "seconds": r.elapsed,
    }


def play_summary(r) -> PlaySummary:
    out, teams = summarize(r), r.team_stats.values()
    tags = [tag for tag, happened in (
        ("touchdown", out["touchdown"]), ("interception", any(t.get("int_thrown", 0) for t in teams)),
        ("fumble lost", any(t.get("fumbles_lost", 0) for t in teams)), ("penalty", out["penalty"]),
        ("first down", out["first_down"])) if happened]
    return PlaySummary(r.context.situation.offense, out["action"], float(out["yards"]), ", ".join(tags))
