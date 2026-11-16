# START
# Baseline lineups predictor: the unit from hand-set rules and 4th-down priors, the personnel group and the
# defense's package from the priors, and 11 players who have been playing in the unit.
# - predict(ctx, rng, units=units) -> Lineups. Another implementation can hand in its own `units` and keep
#   the rest (events/lineups/predictors/gbm).
# - units(ctx) -> {unit: weight}: which unit a team sends out on a scrimmage down (the 4th-down decision):
#   the unit priors by down, distance, and field position, backed off to down and field position when a
#   cell is thin.
# Internals: _unit (the two-point choice, the kneel, end-of-half, and fair-catch kick rules, then `units`),
# _two_point_rate, _kneel, _fair_catch_kick, _onside, _personnel (by game script, down, and distance, backed
# off to the normal script), _package (by personnel group).
# Choosing the players is in depth_chart.py; priors.py builds the priors.
# END
from collections import Counter

from events.lineups import Lineup, Lineups
from events.lineups.predictors.baseline.depth_chart import defense_lineup, offense_lineup, unit_lineup
from scenarios.play import FREE_KICKS, allowed_units
from shared.priors import blend, choice, dist_bucket, field_bucket, priors_of, rate, script
from shared.rulebook import TRY, rules_for

load_priors = priors_of(__file__, rules={"two_point": TRY})  # (season, week) -> priors dict
DEFENSE_UNITS = {"punt": "punt_return", "field_goal": "field_goal_block", "fair_catch_kick": "field_goal_block",
                 "victory": "defense"}


def units(ctx) -> dict:
    s, p = ctx.situation, load_priors(ctx.game.season, ctx.game.week)
    field = field_bucket(s.x)
    counts = p["unit"].get(f"{s.down}|{dist_bucket(s.distance)}|{field}", {})
    if sum(counts.values()) < 20:
        fallback = Counter()
        for key, value in p["unit"].items():
            down, _, bucket = key.split("|")
            if down == str(s.down) and bucket == field:
                fallback.update(value)
        counts = blend(counts, fallback)
    return counts


def predict(ctx, rng, units=units):
    s = ctx.situation
    if s.kind in FREE_KICKS:
        unit = "onside_kickoff" if _onside(ctx, rng) else "kickoff"
        return Lineups(Lineup(unit, None, unit_lineup(ctx, s.offense, unit, rng)),
                       Lineup("kick_return", None, unit_lineup(ctx, s.defense, "kick_return", rng)))
    p = load_priors(ctx.game.season, ctx.game.week)
    unit = _unit(ctx, p, rng, units)
    if unit == "offense":
        group = _personnel(s, p, rng)
        package = _package(group, p, rng)
        return Lineups(Lineup("offense", group, offense_lineup(ctx, s.offense, group, rng)),
                       Lineup("defense", package, defense_lineup(ctx, s.defense, package, rng)))
    defense_unit = DEFENSE_UNITS[unit]
    return Lineups(Lineup(unit, "22" if unit == "victory" else None, unit_lineup(ctx, s.offense, unit, rng)),
                   Lineup(defense_unit, None, unit_lineup(ctx, s.defense, defense_unit, rng)))


def _onside(ctx, rng):  # hand-set
    s = ctx.situation
    if "onside_kickoff" not in allowed_units(ctx, rules_for(ctx.game.season)):
        return False
    trailing_by = s.score[s.defense] - s.score[s.offense]
    return s.quarter >= 4 and s.clock <= 180 and 0 < trailing_by <= 16 and rng.random() < 0.85


def _two_point_rate(s, p):  # data rate plus a hand-set late-game chart
    lead = s.score[s.offense] - s.score[s.defense]
    if s.quarter >= 4 and s.clock <= 600 and lead in (-2, -5, -10, 1, 5):
        return 0.75
    return rate(p["two_point"], "attempt")


def _kneel(s):  # hand-set
    lead = s.score[s.offense] - s.score[s.defense]
    if s.quarter >= 4 and lead > 0:
        burnable = 40 * (5 - s.down - s.timeouts[s.defense]) - (0 if s.clock_running else 40)
        return s.clock <= burnable
    return s.quarter == 2 and s.clock <= 30 and s.x <= 50


def _fair_catch_kick(s):  # hand-set: a free three points as a half runs out, from where a kick can get there
    lead = s.score[s.offense] - s.score[s.defense]
    return s.fair_catch_kick and s.clock <= 5 and s.x >= 42 and (s.quarter == 2 or (s.quarter >= 4 and -3 <= lead <= 0))


def _personnel(s, p, rng):
    if s.kind == "try":
        return choice(p["personnel"]["try"], rng)
    key = f"{s.down}|{dist_bucket(s.distance)}"
    counts = blend(p["personnel"].get(f"{script(s)}|{key}", {}), p["personnel"].get(f"normal|{key}", {}))
    return choice(counts, rng)


def _package(group, p, rng):
    return choice(p["package"].get(group) or p["package"]["11"], rng)


def _unit(ctx, p, rng, units):
    s = ctx.situation
    if s.kind == "try":
        return "offense" if rng.random() < _two_point_rate(s, p) else "field_goal"
    lead = s.score[s.offense] - s.score[s.defense]
    if _fair_catch_kick(s):
        return "fair_catch_kick"
    if _kneel(s):
        return "victory"
    if s.quarter in (2, 4) and s.clock <= 8 and s.x >= 60 and (s.quarter == 2 or -3 <= lead <= 0):
        return "field_goal"  # hand-set: kick at the end of a half
    return choice(units(ctx) or {"offense": 1}, rng)
