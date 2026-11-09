# START
# The baseline predictors: every event sampled from simple priors (priors_<season>.json) plus hand-set rules.
# - Baseline(priors): one method per event, with the signatures in scenarios/play/events.py.
#   lineups (unit choice: kneel/end-of-half rules, then 4th-down priors; personnel; depth-chart fill),
#   offensive_formation, defensive_formation, pre_snap, snap (run/pass rate, ball carrier), pass_rush, target,
#   pass_result, carry, loose_ball, punt_kick, punt_result, kick_attempt, free_kick, kick_result, fouls, injuries.
# - Hand-set (no data yet): personnel mix, kneel/spike/end-of-half rules, two-point chart, onside kicks,
#   play clock usage, play durations, loose-ball recovery odds for muffs/blocks/bad snaps, injury lengths,
#   and which positions commit each foul.
# Helpers: _choice (sample a weights dict), _hist (sample a histogram), _rate, _blend (counts backed off to a
# coarser distribution), Baseline._pick (a player on the field weighted by position group).
# END
from collections import Counter

from predictors.baseline.lineups import (defense_lineup, offense_formation, offense_lineup, package_for,
                                         personnel, unit_lineup)
from predictors.baseline.priors import PRESNAP
from predictors.baseline.roles import air_bucket, dist_bucket, fg_bin, field_bucket, goal_bucket, group, role, script
from rulebook import rules_for
from scenarios.play import FREE_KICKS, allowed_units
from scenarios.play.events import (CarryEnd, DefensiveFormation, Foul, FreeKick, Injury, KickAttempt, KickOutcome,
                                   Lineup, Lineups, PassResult, PassRush, PreSnap, PuntKick, Recovery, Snap, Target)
from scenarios.play.record import Carry, Kick, Pass, facts

RECOVERY_YARDS = {"0": 70, "2": 10, "5": 8, "10": 5, "20": 4, "40": 2, "70": 1}
RETURN_ENDS = {"tackled": 93, "out_of_bounds": 6, "fumble": 1}
FOULERS = {
    "false_start": {"OL": 8, "TE": 1, "WR": 1}, "delay_of_game": {"QB": 1}, "encroachment": {"DL": 1},
    "neutral_zone_infraction": {"DL": 4, "LB": 1}, "defensive_offside": {"DL": 3, "LB": 1},
    "illegal_formation": {"OL": 1, "WR": 2, "TE": 1}, "illegal_shift": {"WR": 2, "TE": 1, "RB": 1},
    "offensive_holding": {"OL": 8, "TE": 1.5, "WR": 0.5}, "defensive_holding": {"DB": 4, "LB": 1},
    "illegal_contact": {"DB": 1}, "defensive_pass_interference": {"DB": 6, "LB": 1},
    "offensive_pass_interference": {"WR": 3, "TE": 1}, "ineligible_downfield_pass": {"OL": 1},
    "roughing_the_passer": {"DL": 4, "LB": 1}, "face_mask": {"DL": 1, "LB": 1, "DB": 1},
}


def _choice(weights, rng):
    keys = [k for k, v in weights.items() if v > 0]
    return rng.choices(keys, [weights[k] for k in keys])[0]


def _hist(hist, rng):
    return float(_choice(hist, rng))


def _rate(counts, key):
    total = sum(counts.values())
    return counts.get(key, 0) / total if total else 0.0


def _blend(counts, fallback, k=10.0):
    total = sum(fallback.values()) or 1
    return {key: counts.get(key, 0) + k * fallback.get(key, 0) / total for key in set(counts) | set(fallback)}


class Baseline:
    def __init__(self, priors):
        self.p = priors

    # --- helpers ---

    def _on_field(self, ctx, lineups, team):
        return lineups.offense.players if team == ctx.situation.offense else lineups.defense.players

    def _pick(self, ctx, players, group_weights, rng, exclude=()):
        players = [pid for pid in players if pid not in exclude]
        sizes = Counter(group(ctx.by_id[pid]) for pid in players)
        weights = [group_weights.get(group(ctx.by_id[pid]), 0.02 * sum(group_weights.values())) / sizes[group(ctx.by_id[pid])]
                   for pid in players]
        return rng.choices(players, weights)[0]

    def _pick_many(self, ctx, players, group_weights, n, rng):
        chosen = []
        for _ in range(n):
            chosen.append(self._pick(ctx, players, group_weights, rng, chosen))
        return tuple(chosen)

    def _returner(self, ctx, players, slot, rng):
        ranked = [pid for pid in players if ctx.by_id[pid].rank(slot)]
        if ranked:
            return min(ranked, key=lambda pid: ctx.by_id[pid].rank(slot))
        return self._pick(ctx, players, {"DB": 6, "WR": 3, "RB": 1}, rng)

    # --- lineups and formations ---

    def lineups(self, ctx, rng):
        s = ctx.situation
        if s.kind in FREE_KICKS:
            unit = "onside_kickoff" if self._onside(ctx, rng) else "kickoff"
            return Lineups(Lineup(unit, None, unit_lineup(ctx, s.offense, unit)),
                           Lineup("kick_return", None, unit_lineup(ctx, s.defense, "kick_return")))
        unit = self._unit(ctx, rng)
        if unit == "offense":
            group_ = personnel(s, rng)
            package = package_for(group_)
            return Lineups(Lineup("offense", group_, offense_lineup(ctx, s.offense, group_)),
                           Lineup("defense", package, defense_lineup(ctx, s.defense, package)))
        defense_unit = {"punt": "punt_return", "field_goal": "field_goal_block", "victory": "defense"}[unit]
        return Lineups(Lineup(unit, "22" if unit == "victory" else None, unit_lineup(ctx, s.offense, unit)),
                       Lineup(defense_unit, None, unit_lineup(ctx, s.defense, defense_unit)))

    def _onside(self, ctx, rng):  # hand-set
        s = ctx.situation
        if "onside_kickoff" not in allowed_units(ctx, rules_for(ctx.game.season)):
            return False
        trailing_by = s.score[s.defense] - s.score[s.offense]
        return s.quarter >= 4 and s.clock <= 180 and 0 < trailing_by <= 16 and rng.random() < 0.85

    def _two_point_rate(self, s):  # data rate plus a hand-set late-game chart
        lead = s.score[s.offense] - s.score[s.defense]
        if s.quarter >= 4 and s.clock <= 600 and lead in (-2, -5, -10, 1, 5):
            return 0.75
        return _rate(self.p["two_point"], "attempt")

    def _kneel(self, s):  # hand-set
        lead = s.score[s.offense] - s.score[s.defense]
        if s.quarter >= 4 and lead > 0:
            burnable = 40 * (5 - s.down - s.timeouts[s.defense]) - (0 if s.clock_running else 40)
            return s.clock <= burnable
        return s.quarter == 2 and s.clock <= 30 and s.x <= 50

    def _unit(self, ctx, rng):
        s = ctx.situation
        if s.kind == "try":
            return "offense" if rng.random() < self._two_point_rate(s) else "field_goal"
        lead = s.score[s.offense] - s.score[s.defense]
        if self._kneel(s):
            return "victory"
        if s.quarter in (2, 4) and s.clock <= 8 and s.x >= 60 and (s.quarter == 2 or -3 <= lead <= 0):
            return "field_goal"  # hand-set: kick at the end of a half
        field = field_bucket(s.x)
        counts = self.p["unit"].get(f"{s.down}|{dist_bucket(s.distance)}|{field}", {})
        if sum(counts.values()) < 20:
            fallback = Counter()
            for key, value in self.p["unit"].items():
                down, _, bucket = key.split("|")
                if down == str(s.down) and bucket == field:
                    fallback.update(value)
            counts = _blend(counts, fallback)
        return _choice(counts or {"offense": 1}, rng)

    def offensive_formation(self, ctx, lineups, rng):
        s = ctx.situation
        if lineups.offense.unit == "victory":
            shotgun = False
        elif s.kind == "scrimmage":
            counts = self.p["shotgun"].get(f"{s.down}|{dist_bucket(s.distance)}", {})
            shotgun = rng.random() < (_rate(counts, "shotgun") if counts else 0.6)
        else:
            shotgun = rng.random() < 0.5
        return offense_formation(ctx, lineups.offense, shotgun, rng)

    def defensive_formation(self, ctx, lineups, formation, rng):
        s = ctx.situation
        hist = self.p["box"].get(f"{s.down}|{dist_bucket(s.distance)}") if s.kind == "scrimmage" else None
        box = int(_hist(hist, rng)) if hist else 8
        return DefensiveFormation(box, 2 if (s.distance or 10) >= 7 and rng.random() < 0.6 else 1)

    # --- pre-snap and snap ---

    def _play_clock_used(self, s, rng):  # hand-set
        clock = s.play_clock
        pace = script(s) if s.kind == "scrimmage" else "normal"
        if pace == "hurry" and s.clock_running:
            return rng.uniform(8, 18)
        if pace == "bleed":
            return rng.uniform(clock - 3, clock - 0.5)
        return rng.uniform(clock - 15, clock - 3)

    def pre_snap(self, ctx, lineups, formation, allowed, rng):
        s = ctx.situation
        rates = self.p["fouls"].get("presnap", {})
        foul = None
        if rng.random() < sum(rates.values()):
            name, side = _choice(rates, rng).split("|")
            team = s.offense if side == "offense" else s.defense
            timing = next((t for t in ("presnap", "snap") if (name, team, t) in allowed), None)
            if timing:
                player = formation.qb if name == "delay_of_game" else self._fouler(ctx, lineups, name, team, rng)
                foul = Foul(name, team, player, s.x, timing)
        return PreSnap(self._play_clock_used(s, rng), foul)

    def _pass_rate(self, s):
        if s.kind == "try":
            return _rate(self.p["two_point_play"], "pass")
        key = f"{s.down}|{dist_bucket(s.distance)}"
        counts = self.p["pass_rate"].get(f"{script(s)}|{key}", {})
        return _rate(_blend(counts, self.p["pass_rate"].get(f"normal|{key}", {})), "pass")

    def snap(self, ctx, lineups, formation, defense, allowed, rng):
        s = ctx.situation
        bad = rng.random() < 0.003
        unit = lineups.offense.unit
        if unit in ("punt", "field_goal"):
            return Snap(unit, bad_snap=bad)
        if unit == "victory":
            return Snap("kneel")
        lead = s.score[s.offense] - s.score[s.defense]
        if (s.kind == "scrimmage" and s.clock_running and s.quarter in (2, 4) and s.clock <= 30 and s.down < 4
                and s.timeouts[s.offense] == 0 and (s.quarter == 2 or lead <= 0) and rng.random() < 0.6):
            return Snap("spike")  # hand-set
        if rng.random() < self._pass_rate(s):
            return Snap("pass", bad_snap=bad)
        backs = list(formation.backfield)
        weights = [self.p["run_carrier"].get(role(ctx.by_id[pid]), 1) for pid in backs]
        return Snap("run", rng.choices(backs, weights)[0], bad)

    # --- passing ---

    def pass_rush(self, ctx, lineups, formation, defense, rng):
        p = self.p
        outcome = _choice(p["dropback"], rng)
        rushers = int(min(8, max(3, _hist(p["rushers"], rng))))
        defenders = lineups.defense.players
        if outcome == "sack":
            sackers = self._pick_many(ctx, defenders, p["sacker"], 2 if rng.random() < 0.1 else 1, rng)
            result = "strip_sack" if rng.random() < _rate(p["strip_sack"], "fumble") else "sack"
            return PassRush(rushers, result, max(1.5, rng.gauss(3.4, 0.8)), sackers, sackers,
                            max(0.0, _hist(p["sack_yards"], rng)))
        hit = outcome == "throw" and rng.random() < _rate(p["qb_hit"], "hit")
        hitters = (self._pick(ctx, defenders, p["sacker"], rng),) if hit else ()
        mean, sd = {"throw": (2.7, 0.6), "scramble": (3.3, 0.7), "throwaway": (3.6, 0.8)}[outcome]
        return PassRush(rushers, outcome, max(1.0, rng.gauss(mean, sd)), hitters)

    def target(self, ctx, lineups, formation, eligible, rng):
        weights = [self.p["target"].get(role(ctx.by_id[pid]), 5) for pid in eligible]
        receiver = rng.choices(eligible, weights)[0]
        los = ctx.situation.x
        hist = self.p["air_yards_goal"][goal_bucket(100 - los)] if los >= 90 else self.p["air_yards"]
        for _ in range(20):  # keep the pass inside the end line, since the field compresses near the goal
            air = _hist(hist, rng)
            if los + air <= 108:
                break
        return Target(receiver, min(air, 108 - los), _choice(self.p["direction"], rng))

    def pass_result(self, ctx, lineups, target, rng):
        los = ctx.situation.x
        counts = (self.p["pass_result_goal"][goal_bucket(100 - los)] if los >= 90
                  else self.p["pass_result"][air_bucket(target.air_yards)])
        result = _choice(counts, rng)
        defenders = lineups.defense.players
        if result == "intercepted":
            return PassResult(result, self._pick(ctx, defenders, {"DB": 80, "LB": 18, "DL": 2}, rng))
        if result == "incomplete" and rng.random() < _rate(self.p["defended"], "yes"):
            return PassResult(result, self._pick(ctx, defenders, {"DB": 85, "LB": 13, "DL": 2}, rng))
        return PassResult(result)

    # --- ball carriers and loose balls ---

    def carry(self, ctx, lineups, kind, carrier, yard_line, rng):
        if kind == "kneel":
            return CarryEnd(-1.0 if yard_line > 2 else 0.0, "down", seconds=1.0)
        goal = self.p.get(f"{kind}_goal", {}).get(goal_bucket(100 - yard_line)) if yard_line >= 90 else None
        hist = RECOVERY_YARDS if kind == "recovery" else goal or self.p[kind]  # goal to go: compressed gains
        yards = _hist(hist, rng)
        how = _choice(self.p["carry_end"].get(kind, RETURN_ENDS), rng)
        if kind == "scramble" and how == "tackled" and rng.random() < 0.3:
            how = "down"  # slide
        team = ctx.by_id[carrier].team
        opponents = lineups.defense.players if team == ctx.situation.offense else lineups.offense.players
        tacklers = ()
        if how in ("tackled", "fumble") or (how == "out_of_bounds" and rng.random() < 0.5):
            weights = self.p["tackler"]["kick" if kind in ("punt_return", "kick_return") else "scrimmage"]
            n = 2 if rng.random() < _rate(self.p["assisted"], "yes") else 1
            tacklers = self._pick_many(ctx, opponents, weights, n, rng)
        forced = tacklers[0] if how == "fumble" and tacklers and rng.random() < 0.7 else None
        return CarryEnd(yards, how, tacklers, forced, 2.0 + abs(yards) / 7 + rng.uniform(0, 1.5))

    def loose_ball(self, ctx, lineups, cause, x, last_team, rng):
        s = ctx.situation
        other = s.defense if last_team == s.offense else s.offense
        if cause == "fumble" and rng.random() < 0.04:
            ahead = 1 if last_team == s.offense else -1
            return Recovery(None, None, x + ahead * rng.uniform(-2, 4), 1.0)
        lost = {"fumble": _rate(self.p["fumble_recovery"], "lost"), "bad_snap": 0.2, "muff": 0.45,
                "blocked_kick": 0.6}[cause]
        team = other if rng.random() < lost else last_team
        return Recovery(team, rng.choice(self._on_field(ctx, lineups, team)), x + rng.uniform(-3, 3),
                        rng.uniform(0.5, 2.0))

    # --- kicks ---

    def punt_kick(self, ctx, lineups, punter, rng):
        if rng.random() < _rate(self.p["punt_blocked"], "yes"):
            return PuntKick(0.0, self._pick(ctx, lineups.defense.players, {"DL": 5, "LB": 3, "DB": 2}, rng), 2.0)
        hist = self.p["punt_distance"].get(field_bucket(ctx.situation.x)) or self.p["punt_distance"]["3"]
        return PuntKick(_hist(hist, rng), None, max(4.5, rng.gauss(6.0, 0.5)))

    def punt_result(self, ctx, lineups, landing_x, allowed, rng):
        if allowed == ("touchback",):
            return KickOutcome("touchback")
        r = 100 - landing_x
        bucket = "inside_10" if r <= 10 else "inside_20" if r <= 20 else "open"
        result = _choice({k: v for k, v in self.p["punt_result"][bucket].items() if k in allowed}, rng)
        returner = self._returner(ctx, lineups.defense.players, "PR", rng)
        return KickOutcome(result, returner if result in ("fair_catch", "return", "muff") else None)

    def kick_attempt(self, ctx, lineups, kicker, distance, rng):
        if ctx.situation.kind == "try":
            counts = {"good": self.p["pat"].get("good", 0), "no_good": self.p["pat"].get("failed", 0),
                      "blocked": self.p["pat"].get("blocked", 0)}
        else:
            fg = self.p["fg"].get(fg_bin(distance), {})
            counts = {"good": fg.get("made", 0), "no_good": fg.get("missed", 0) + (distance > 66) * 1000,
                      "blocked": fg.get("blocked", 0)}
        result = _choice(counts, rng)
        blocker = self._pick(ctx, lineups.defense.players, {"DL": 8, "LB": 1, "DB": 1}, rng) if result == "blocked" else None
        return KickAttempt(result, blocker, max(3.0, rng.gauss(4.0, 0.3)))

    def free_kick(self, ctx, lineups, onside, rng):
        players = lineups.offense.players
        kicker = next((pid for pid in players if ctx.by_id[pid].position == "K"),
                      next((pid for pid in players if ctx.by_id[pid].position == "P"), players[0]))
        if onside:
            return FreeKick(kicker, rng.uniform(10, 15), False, 2.0)
        out_of_bounds = rng.random() < _rate(self.p["kickoff_oob"], "yes")
        return FreeKick(kicker, _hist(self.p["kickoff_distance"], rng), out_of_bounds, max(3.0, rng.gauss(4.0, 0.3)))

    def kick_result(self, ctx, lineups, landing_x, allowed, rng):
        receivers = lineups.defense.players
        if "kicking_recovery" in allowed:  # onside kick, hand-set recovery rate
            if rng.random() < 0.15:
                return KickOutcome("kicking_recovery", rng.choice(lineups.offense.players))
            return KickOutcome("return", self._returner(ctx, receivers, "KR", rng))
        zone = "end_zone" if landing_x >= 100 else "landing_zone"
        weights = {k: v for k, v in self.p["kickoff_result"][zone].items() if k in allowed}
        total = sum(weights.values())
        if "muff" in allowed:
            weights["muff"] = weights.get("muff", 0) + 0.01 * total
        if "fair_catch" in allowed:
            weights["fair_catch"] = 0.3 * total
        result = _choice(weights, rng)
        return KickOutcome(result, None if result == "touchback" else self._returner(ctx, receivers, "KR", rng))

    # --- fouls and injuries ---

    def _fouler(self, ctx, lineups, name, team, rng, record=()):
        passes = facts(record, Pass)
        if name == "intentional_grounding" and passes:
            return passes[0].passer
        weights = FOULERS.get(name, {"DL": 1, "LB": 1, "DB": 1, "OL": 1, "WR": 1, "TE": 1, "RB": 1})
        return self._pick(ctx, self._on_field(ctx, lineups, team), weights, rng)

    def _category(self, record):
        kicks = facts(record, Kick)
        if kicks:
            return {"punt": "punt", "field_goal": "field_goal", "pat": "field_goal"}.get(kicks[0].kind, "kickoff")
        action = facts(record, Snap)[0].action
        return "run" if action in ("run", "kneel") else "pass"

    def _foul_spot(self, ctx, record, name, timing, rng):
        los = ctx.situation.x
        returns = [c for c in facts(record, Carry) if c.team != ctx.situation.offense]
        if timing == "return" and returns:
            return rng.uniform(min(returns[-1].start, returns[-1].end), max(returns[-1].start, returns[-1].end))
        targets = [p for p in facts(record, Pass) if p.receiver]
        if name == "defensive_pass_interference" and targets:
            return targets[0].x
        if name == "intentional_grounding":
            return los - rng.uniform(3, 9)
        if name in ("offensive_holding", "illegal_block_in_the_back"):
            return los + rng.uniform(-3, 5)
        return los

    def fouls(self, ctx, lineups, record, allowed, rng):
        s = ctx.situation
        category = self._category(record)
        rates = {k: v for k, v in self.p["fouls"].get(category, {}).items() if k.split("|")[0] not in PRESNAP}
        if rng.random() >= sum(rates.values()):
            return ()
        name, side = _choice(rates, rng).split("|")
        team = s.offense if side == "offense" else s.defense
        timings = [t for t in ("live", "return", "after") if (name, team, t) in allowed]
        if not timings:
            return ()
        if "return" in timings and category in ("punt", "kickoff") and team == s.defense:
            timing = "return"
        elif "after" in timings and (timings == ["after"] or rng.random() < 0.5):
            timing = "after"
        else:
            timing = timings[0]
        player = self._fouler(ctx, lineups, name, team, rng, record)
        return (Foul(name, team, player, self._foul_spot(ctx, record, name, timing, rng), timing),)

    def injuries(self, ctx, lineups, record, rng):
        injury = self.p["injury"]
        if rng.random() >= injury["injured"] / injury["plays"]:
            return ()
        involved = [c.player for c in facts(record, Carry)] + [t for c in facts(record, Carry) for t in c.tacklers]
        everyone = lineups.offense.players + lineups.defense.players
        player = rng.choice(involved) if involved and rng.random() < 0.6 else rng.choice(everyone)
        return (Injury(player, rng.choices([2, 8, 999], [0.45, 0.2, 0.35])[0]),)
