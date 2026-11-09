# START
# Running real inputs through the play scenario.
# - run_audit(season, weeks=None, sims=1, seed=0) -> Audit: validates every real context, simulates each one
#   `sims` times with the baseline predictors, validates every simulated play, and keeps outcome summaries.
# - sim_outcome(result) -> dict: a simulated play summarized with the same keys as the real one
#   (see nflverse/contexts.py _actual): action, yards, points, touchdown, turnover, penalty, first_down, ...
# - Audit: plays, input_errors, failures, actual/simulated (context, outcome) pairs, examples.
# END
import random
import traceback
from dataclasses import dataclass, field

from nflverse import real_plays
from predictors.baseline import baseline_predictors
from rulebook import rules_for
from scenarios.play import describe_play, run_play, validate_context, validate_play
from scenarios.play.events import PassRush, Snap
from scenarios.play.field import field_goal_distance
from scenarios.play.record import Kick, Pass, facts

KICK_ACTIONS = {"punt": "punt", "field_goal": "field_goal", "pat": "extra_point", "kickoff": "kickoff",
                "safety_kick": "kickoff", "onside_kickoff": "kickoff"}


@dataclass
class Audit:
    season: int
    plays: list
    input_errors: list = field(default_factory=list)   # (RealPlay, message)
    failures: list = field(default_factory=list)       # (RealPlay, message, narration or traceback)
    actual: list = field(default_factory=list)         # (context, outcome)
    simulated: list = field(default_factory=list)      # (context, outcome)
    examples: list = field(default_factory=list)       # (RealPlay, PlayResult)


def sim_outcome(r) -> dict:
    s, record = r.context.situation, r.record
    kicks, snaps = facts(record, Kick), facts(record, Snap)
    if r.no_play:
        action = "no_play"
    elif kicks:
        action = KICK_ACTIONS[kicks[0].kind]
    else:
        action = snaps[0].action
        rush = facts(record, PassRush)
        if rush:
            action = {"sack": "sack", "strip_sack": "sack", "scramble": "scramble"}.get(rush[0].result, "pass")
    team = {}
    for pid, line in r.stats.items():
        for key, value in line.items():
            team.setdefault(r.context.by_id[pid].team, {}).setdefault(key, 0)
            team[r.context.by_id[pid].team][key] += value
    off = team.get(s.offense, {})
    kick = kicks[0] if kicks else None
    if kick and kick.kind in ("field_goal", "pat"):
        kick_distance = field_goal_distance(rules_for(r.context.game.season), kick.x)
    else:
        kick_distance = kick.land - kick.x if kick and kick.land is not None else None
    returns = sum(t.get(k, 0) for t in team.values() for k in ("punt_ret_yds", "kick_ret_yds"))
    return {
        "action": action,
        "yards": off.get("rush_yds", 0) + off.get("rec_yds", 0) - r.team_stats[s.offense].get("sack_yards", 0),
        "points": {t: sum(p for scorer, p, _ in r.scores if scorer == t) for t in s.score},
        "touchdown": any(how == "touchdown" for _, _, how in r.scores),
        "turnover": any(t.get("int_thrown", 0) or t.get("fumbles_lost", 0) for t in team.values()),
        "penalty": bool(r.accepted or r.declined),
        "first_down": (s.kind == "scrimmage" and r.next.kind == "scrimmage" and r.next.offense == s.offense
                       and r.next.down == 1),
        "complete": any(p.result == "complete" for p in facts(record, Pass)),
        "field_goal_result": {"good": "made", "no_good": "missed", "blocked": "blocked"}.get(kick.result) if kick and kick.kind == "field_goal" else None,
        "extra_point_result": {"good": "good", "no_good": "failed", "blocked": "blocked"}.get(kick.result) if kick and kick.kind == "pat" else None,
        "kick_distance": kick_distance,
        "touchback": r.live is not None and r.live.how == "touchback",
        "return_yards": returns,
        "seconds": r.elapsed,
    }


def run_audit(season: int = 2026, weeks=None, sims: int = 1, seed: int = 0, examples: int = 30) -> Audit:
    plays = real_plays(season, weeks)
    predictors = baseline_predictors(season)
    audit = Audit(season, plays)
    every = max(1, len(plays) // examples)
    for i, rp in enumerate(plays):
        audit.input_errors += [(rp, e) for e in validate_context(rp.context)]
        audit.actual.append((rp.context, rp.actual))
        for k in range(sims):
            rng = random.Random(seed * 1_000_003 + i * 101 + k)
            try:
                result = run_play(rp.context, predictors, rng)
            except Exception as e:
                audit.failures.append((rp, f"{type(e).__name__}: {e}", traceback.format_exc()))
                continue
            errors = validate_play(result)
            if errors:
                audit.failures.append((rp, "; ".join(errors), describe_play(result)))
            audit.simulated.append((rp.context, sim_outcome(result)))
            if k == 0 and i % every == 0:
                audit.examples.append((rp, result))
    return audit
