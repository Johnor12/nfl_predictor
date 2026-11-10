# START
# Simulating the play scenario many times.
# - simulate_plays(contexts, predictors, sims=1, seed=0, examples=30) -> PlaySimulation: runs every context
#   `sims` times (each run has its own seed, so any play can be rerun), validates every play, and summarizes it.
# - simulate_play(ctx, predictors, sims=1, seed=0, index=0) -> (results, failures): one context's runs as
#   PlayResults, for callers that work through a season one play at a time. `index` is the context's
#   position in the simulation (it is part of each run's seed).
# - summarize(result) -> dict: a simulated play with the same keys as a real one (shared/nflverse/contexts.py
#   _actual): action, yards, points, touchdown, turnover, penalty, first_down, ... plus seconds.
# - PlaySimulation: outcomes (context, summary) for every play that ran; failures (context index, message,
#   narration or traceback) for plays that raised or broke an invariant; examples (context index, PlayResult),
#   the first run of about `examples` evenly spaced contexts.
# END
import random
import traceback
from dataclasses import dataclass, field

from events.pass_rush import PassRush
from events.snap import Snap
from scenarios.play import Kick, Pass, describe_play, facts, field_goal_distance, run_play, validate_play
from shared.rulebook import rules_for

KICK_ACTIONS = {"punt": "punt", "field_goal": "field_goal", "pat": "extra_point", "kickoff": "kickoff",
                "safety_kick": "kickoff", "onside_kickoff": "kickoff"}
RUSH_ACTIONS = {"sack": "sack", "strip_sack": "sack", "scramble": "scramble"}
FIELD_GOAL_RESULTS = {"good": "made", "no_good": "missed", "blocked": "blocked"}  # nflverse's names
EXTRA_POINT_RESULTS = {"good": "good", "no_good": "failed", "blocked": "blocked"}


@dataclass
class PlaySimulation:
    outcomes: list = field(default_factory=list)
    failures: list = field(default_factory=list)
    examples: list = field(default_factory=list)


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


def simulate_play(ctx, predictors, sims: int = 1, seed: int = 0, index: int = 0) -> tuple[list, list]:
    results, failures = [], []
    for k in range(sims):
        rng = random.Random(seed * 1_000_003 + index * 101 + k)
        try:
            result = run_play(ctx, predictors, rng)
        except Exception as e:
            failures.append((index, f"{type(e).__name__}: {e}", traceback.format_exc()))
            continue
        errors = validate_play(result)
        if errors:
            failures.append((index, "; ".join(errors), describe_play(result)))
        results.append(result)
    return results, failures


def simulate_plays(contexts, predictors, sims: int = 1, seed: int = 0, examples: int = 30) -> PlaySimulation:
    sim = PlaySimulation()
    kept = set(range(0, len(contexts), max(1, len(contexts) // examples))) if examples else set()
    for i, ctx in enumerate(contexts):
        results, failures = simulate_play(ctx, predictors, sims, seed, i)
        sim.failures += failures
        sim.outcomes += [(ctx, summarize(result)) for result in results]
        if results and i in kept:
            sim.examples.append((i, results[0]))
    return sim
