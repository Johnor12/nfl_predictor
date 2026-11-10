# START
# Baseline lineups predictor: the unit from hand-set rules and 4th-down priors, filled from the depth chart.
# - predict(ctx, rng) -> Lineups.
# Internals: _unit (kneel and end-of-half rules, then the unit priors by down, distance, and field position,
# backed off to down and field position when a cell is thin), _two_point_rate, _kneel, _onside.
# Personnel and the depth-chart fill are in depth_chart.py; priors.py builds the priors.
# END
from collections import Counter

from events.lineups import Lineup, Lineups
from events.lineups.predictors.baseline.depth_chart import (defense_lineup, offense_lineup, package_for, personnel,
                                                            unit_lineup)
from scenarios.play import FREE_KICKS, allowed_units
from shared.priors import blend, choice, dist_bucket, field_bucket, priors_of, rate
from shared.rulebook import rules_for

load_priors = priors_of(__file__)  # season -> priors dict
DEFENSE_UNITS = {"punt": "punt_return", "field_goal": "field_goal_block", "victory": "defense"}


def predict(ctx, rng):
    s = ctx.situation
    if s.kind in FREE_KICKS:
        unit = "onside_kickoff" if _onside(ctx, rng) else "kickoff"
        return Lineups(Lineup(unit, None, unit_lineup(ctx, s.offense, unit)),
                       Lineup("kick_return", None, unit_lineup(ctx, s.defense, "kick_return")))
    unit = _unit(ctx, rng)
    if unit == "offense":
        group = personnel(s, rng)
        package = package_for(group)
        return Lineups(Lineup("offense", group, offense_lineup(ctx, s.offense, group)),
                       Lineup("defense", package, defense_lineup(ctx, s.defense, package)))
    defense_unit = DEFENSE_UNITS[unit]
    return Lineups(Lineup(unit, "22" if unit == "victory" else None, unit_lineup(ctx, s.offense, unit)),
                   Lineup(defense_unit, None, unit_lineup(ctx, s.defense, defense_unit)))


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


def _unit(ctx, rng):
    s = ctx.situation
    p = load_priors(ctx.game.season)
    if s.kind == "try":
        return "offense" if rng.random() < _two_point_rate(s, p) else "field_goal"
    lead = s.score[s.offense] - s.score[s.defense]
    if _kneel(s):
        return "victory"
    if s.quarter in (2, 4) and s.clock <= 8 and s.x >= 60 and (s.quarter == 2 or -3 <= lead <= 0):
        return "field_goal"  # hand-set: kick at the end of a half
    field = field_bucket(s.x)
    counts = p["unit"].get(f"{s.down}|{dist_bucket(s.distance)}|{field}", {})
    if sum(counts.values()) < 20:
        fallback = Counter()
        for key, value in p["unit"].items():
            down, _, bucket = key.split("|")
            if down == str(s.down) and bucket == field:
                fallback.update(value)
        counts = blend(counts, fallback)
    return choice(counts or {"offense": 1}, rng)
