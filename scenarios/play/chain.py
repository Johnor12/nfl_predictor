# START
# The play's event chain.
# - run_play(ctx, predictors, rng) -> PlayResult: runs one play end to end.
# - IllegalChoice: raised when a predictor returns something the rules don't allow.
# - allowed_units(ctx, rules): which units the offense may send out (where coaching decisions live).
# - _Play: one play in progress. Methods in chain order:
#   run (lineups, formations, pre-snap, action, fouls, enforcement, injuries, then outcome.finish),
#   scrimmage (snap and action), dropback (rush, target, pass result), punt, place_kick, free_kick,
#   after_kick (shared kick results), and the shared building blocks carry and loose_ball, which end in
#   dead_at (end-zone rules: safety or touchback) or a touchdown.
# Live-ball methods return a Dead (how/where the ball died and who gets it). Penalty enforcement is in
# fouls.py, the next situation and clock in outcome.py, stats in stats.py.
# END
import dataclasses

from rulebook import rules_for
from scenarios.play import fouls as foul_rules
from scenarios.play import outcome
from scenarios.play.context import FREE_KICKS
from scenarios.play.field import (clamp_x, eligible_receivers, field_goal_distance, formation_errors,
                                  line_of_scrimmage, lineup_errors, other, rel, to_x)
from scenarios.play.record import Carry, Dead, Kick, LooseBall, Pass, Sack

RUSH_RESULTS = ("throw", "sack", "scramble", "throwaway", "strip_sack")
CARRY_ENDS = ("tackled", "out_of_bounds", "fumble", "down")
UNIT_ACTIONS = {
    "offense": ("run", "pass", "kneel", "spike"),
    "victory": ("kneel",),
    "punt": ("punt", "run", "pass"),
    "field_goal": ("field_goal", "run", "pass"),
}


class IllegalChoice(Exception):
    pass


def _require(ok, message):
    if not ok:
        raise IllegalChoice(message)


def allowed_units(ctx, rules) -> tuple[str, ...]:
    s = ctx.situation
    if s.kind == "scrimmage":
        return ("offense", "punt", "field_goal", "victory")
    if s.kind == "try":
        return ("offense", "field_goal")
    trailing = s.score[s.offense] < s.score[s.defense]
    onside = {"any": True, "trailing": trailing, "trailing_q4": trailing and s.quarter >= 4}[rules.onside_declared]
    return ("kickoff", "onside_kickoff") if onside else ("kickoff",)


def run_play(ctx, predictors, rng):
    return _Play(ctx, predictors, rng).run()


class _Play:
    def __init__(self, ctx, predictors, rng):
        self.ctx, self.p, self.rng = ctx, predictors, rng
        self.rules = rules_for(ctx.game.season)
        self.off, self.de = ctx.situation.offense, ctx.situation.defense
        self.record = []

    def add(self, fact):
        self.record.append(fact)
        return fact

    def check_player(self, pid, team, role):
        lineup = self.lineups.offense if team == self.off else self.lineups.defense
        _require(pid in lineup.players, f"{role} {pid} is not on the field for {team}")

    def check_foul(self, foul, allowed):
        _require((foul.type, foul.team, foul.timing) in allowed, f"foul not possible on this play: {foul}")
        self.check_player(foul.player, foul.team, "fouling player")
        _require(-10 <= foul.x <= 110, f"foul spot off the field: {foul}")

    def run(self):
        ctx, p, rng = self.ctx, self.p, self.rng
        self.lineups = self.add(p.lineups(ctx, rng))
        _require(not lineup_errors(ctx, self.lineups), lineup_errors(ctx, self.lineups))
        _require(self.lineups.offense.unit in allowed_units(ctx, self.rules), f"unit {self.lineups.offense.unit}")
        self.los = line_of_scrimmage(ctx, self.rules, self.lineups)
        fouls = []
        if ctx.situation.kind in FREE_KICKS:
            live = self.free_kick()
        else:
            self.formation = self.add(p.offensive_formation(ctx, self.lineups, rng))
            _require(not formation_errors(ctx, self.lineups, self.formation),
                     formation_errors(ctx, self.lineups, self.formation))
            self.defense = self.add(p.defensive_formation(ctx, self.lineups, self.formation, rng))
            allowed = foul_rules.presnap_fouls(ctx)
            pre = p.pre_snap(ctx, self.lineups, self.formation, allowed, rng)
            _require(pre.seconds >= 0, "negative pre-snap time")
            self.add(dataclasses.replace(pre, foul=None))
            if pre.foul:
                self.check_foul(pre.foul, allowed)
                fouls.append(pre.foul)
            live = None if pre.foul and pre.foul.timing == "presnap" else self.scrimmage()
        if live is not None:
            allowed = foul_rules.live_fouls(ctx, tuple(self.record), live)
            for foul in p.fouls(ctx, self.lineups, tuple(self.record), allowed, rng):
                self.check_foul(foul, allowed)
                fouls.append(foul)
        for foul in fouls:
            self.add(foul)
        enforcement = foul_rules.enforce(ctx, self.rules, self.los, live, tuple(fouls))
        injuries = tuple(p.injuries(ctx, self.lineups, tuple(self.record), rng))
        for injury in injuries:
            _require(injury.player in self.lineups.offense.players + self.lineups.defense.players,
                     f"injured player {injury.player} was not on the field")
        return outcome.finish(ctx, self.rules, self.los, tuple(self.record), live, enforcement, injuries)

    # --- scrimmage downs ---

    def scrimmage(self):
        ctx, f, los, off = self.ctx, self.formation, self.los, self.off
        unit = self.lineups.offense.unit
        allowed = UNIT_ACTIONS[unit]
        if not any(ctx.by_id[pid].position == "K" for pid in self.lineups.offense.players):
            allowed = tuple(a for a in allowed if a != "field_goal")
        snap = self.add(self.p.snap(ctx, self.lineups, f, self.defense, allowed, self.rng))
        _require(snap.action in allowed, f"action {snap.action} not possible from {unit}")
        if snap.bad_snap:
            depth = {"punt": 14, "field_goal": 7}.get(unit, 1 if f.under_center else 5)
            return self.loose_ball("bad_snap", los - depth, off, impetus=off, fumbler=f.qb)
        if snap.action == "run":
            _require(snap.ball_to in f.backfield, f"handoff to {snap.ball_to}, who isn't in the backfield")
            return self.carry("run", snap.ball_to, off, los)
        if snap.action == "kneel":
            return self.carry("kneel", f.qb, off, los)
        if snap.action == "spike":
            self.add(Pass(f.qb, None, los, None, "spike"))
            return Dead(off, los, "incomplete")
        if snap.action == "pass":
            return self.dropback()
        if snap.action == "punt":
            return self.punt()
        return self.place_kick()

    def dropback(self):
        ctx, f, los, off, de = self.ctx, self.formation, self.los, self.off, self.de
        rush = self.add(self.p.pass_rush(ctx, self.lineups, f, self.defense, self.rng))
        _require(rush.result in RUSH_RESULTS and rush.seconds >= 0, f"pass rush {rush}")
        for pid in rush.hitters + rush.sackers:
            self.check_player(pid, de, "pass rusher")
        if rush.result in ("sack", "strip_sack"):
            _require(rush.sackers and rush.sack_yards >= 0, f"sack {rush}")
            spot = clamp_x(los - rush.sack_yards)
            self.add(Sack(f.qb, rush.sackers, spot))
            if rush.result == "strip_sack":
                return self.loose_ball("fumble", spot, off, impetus=off, fumbler=f.qb, forced_by=rush.sackers[0])
            return self.dead_at(off, spot, "tackled", start=los, impetus=off)
        if rush.result == "scramble":
            return self.carry("scramble", f.qb, off, los)
        if rush.result == "throwaway":
            self.add(Pass(f.qb, None, los, None, "throwaway"))
            return Dead(off, los, "incomplete")
        eligible = eligible_receivers(ctx, f)
        target = self.p.target(ctx, self.lineups, f, eligible, self.rng)
        _require(target.receiver in eligible, f"{target.receiver} is not an eligible receiver")
        spot = min(109.5, max(-9.5, los + target.air_yards))  # a pass caught beyond the end line is incomplete
        target = dataclasses.replace(target, air_yards=spot - los)
        result = self.p.pass_result(ctx, self.lineups, target, self.rng)
        _require(result.result in ("complete", "incomplete", "intercepted"), f"pass result {result}")
        _require(result.result != "intercepted" or result.defender, "interception without a defender")
        if result.defender:
            self.check_player(result.defender, de, "pass defender")
        self.add(Pass(f.qb, target.receiver, spot, target.direction, result.result, result.defender))
        if result.result == "incomplete":
            return Dead(off, los, "incomplete")
        if result.result == "complete":
            return self.carry("catch", target.receiver, off, spot)
        return self.carry("interception", result.defender, de, spot, impetus=off)

    def punt(self):
        ctx, los, off, de = self.ctx, self.los, self.off, self.de
        punter = self.formation.qb
        kick = self.p.punt_kick(ctx, self.lineups, punter, self.rng)
        if kick.blocked_by:
            self.check_player(kick.blocked_by, de, "blocker")
            self.add(Kick("punt", punter, los, None, "blocked", kick.blocked_by, kick.seconds))
            return self.loose_ball("blocked_kick", los - 12, off, impetus=off)
        land = min(110.0, los + max(0.0, kick.distance))
        allowed = ("touchback",) if land >= 100 else ("fair_catch", "return", "downed", "out_of_bounds", "muff")
        result = self.p.punt_result(ctx, self.lineups, land, allowed, self.rng)
        _require(result.result in allowed, f"punt result {result.result} not in {allowed}")
        self.add(Kick("punt", punter, los, land, result.result, result.player, kick.seconds))
        dead = self.after_kick(result, land, self.rules.touchback_line, "punt_return")
        return dataclasses.replace(dead, kick=True)

    def place_kick(self):
        ctx, los, off, de, rules = self.ctx, self.los, self.off, self.de, self.rules
        kicker = next(pid for pid in self.lineups.offense.players if ctx.by_id[pid].position == "K")
        kind = "pat" if ctx.situation.kind == "try" else "field_goal"
        spot = los - rules.field_goal_snap_depth
        distance = field_goal_distance(rules, los)
        attempt = self.p.kick_attempt(ctx, self.lineups, kicker, distance, self.rng)
        _require(attempt.result in ("good", "no_good", "blocked"), f"kick attempt {attempt}")
        if attempt.result == "blocked":
            self.check_player(attempt.blocked_by, de, "blocker")
            self.add(Kick(kind, kicker, los, None, "blocked", attempt.blocked_by, attempt.seconds))
            return self.loose_ball("blocked_kick", spot, off, impetus=off)
        self.add(Kick(kind, kicker, los, None, attempt.result, None, attempt.seconds))
        if attempt.result == "good":
            return Dead(off, los, "kick_good")
        if kind == "pat":
            return Dead(off, los, "kick_missed")
        line = min(99.0, max(rules.touchback_line, rel(ctx, de, spot)))  # spot of the kick, or the defense's 20
        return Dead(de, to_x(ctx, de, line), "kick_missed", kick=True)

    # --- free kicks ---

    def free_kick(self):
        ctx, rules, s, off, de = self.ctx, self.rules, self.ctx.situation, self.off, self.de
        onside = self.lineups.offense.unit == "onside_kickoff"
        kind = "onside_kickoff" if onside else s.kind
        spot = self.los
        kick = self.p.free_kick(ctx, self.lineups, onside, self.rng)
        self.check_player(kick.kicker, off, "kicker")
        distance = max(kick.distance, rules.onside_min_distance if onside else 0.0)
        land = min(110.0, spot + distance)
        dynamic = rules.dynamic_kickoff and s.kind == "kickoff"
        if kick.out_of_bounds:
            line = rules.kickoff_out_of_bounds_line if dynamic else rel(ctx, de, spot + 25)
            self.add(Kick(kind, kick.kicker, spot, land, "out_of_bounds", seconds=kick.seconds))
            return Dead(de, to_x(ctx, de, line), "kick_out_of_bounds", kick=True)
        if dynamic and not onside and rel(ctx, de, land) > rules.landing_zone_start:
            self.add(Kick(kind, kick.kicker, spot, land, "short", seconds=kick.seconds))
            return Dead(de, to_x(ctx, de, rules.kickoff_short_line), "kick_short", kick=True)
        if onside:
            allowed = ("kicking_recovery", "return", "muff")
        elif land >= 100:
            allowed = ("touchback", "return")
        elif dynamic:
            allowed = ("return", "muff", "touchback")  # touchback: lands in the landing zone, rolls into the end zone
        elif rules.kickoff_fair_catch or s.kind == "safety_kick":
            allowed = ("return", "muff", "fair_catch")
        else:
            allowed = ("return", "muff")
        result = self.p.kick_result(ctx, self.lineups, land, allowed, self.rng)
        _require(result.result in allowed, f"kick result {result.result} not in {allowed}")
        self.add(Kick(kind, kick.kicker, spot, land, result.result, result.player, kick.seconds))
        if dynamic:
            touchback = rules.kickoff_touchback_line if land >= 100 else rules.landing_zone_touchback_line
        else:
            touchback = rules.kickoff_touchback_line if s.kind == "kickoff" else rules.touchback_line
        return dataclasses.replace(self.after_kick(result, land, touchback, "kick_return"), kick=True)

    def after_kick(self, result, land, touchback_line, return_kind):
        off, de = self.off, self.de
        if result.result == "kicking_recovery":
            self.check_player(result.player, off, "recovering player")
            if rel(self.ctx, off, land) >= 100:  # recovered in the receiving team's end zone
                self.add(Carry(result.player, off, "recovery", 100.0, 100.0, "touchdown"))
                return Dead(off, 100.0, "touchdown")
            return Dead(off, land, "recovered")
        if result.result == "touchback":
            return self.touchback(de, touchback_line)
        if result.result in ("downed", "out_of_bounds"):
            return self.dead_at(de, land, result.result, land, impetus=off, touchback_line=touchback_line)
        self.check_player(result.player, de, "returner")
        if result.result == "fair_catch":
            return self.dead_at(de, land, "fair_catch", land, impetus=off, touchback_line=touchback_line)
        if result.result == "return":
            return self.carry(return_kind, result.player, de, land, impetus=off, touchback_line=touchback_line)
        return self.loose_ball("muff", land, de, impetus=off)

    # --- shared building blocks ---

    def carry(self, kind, player, team, start, impetus=None, touchback_line=None):
        ctx = self.ctx
        self.check_player(player, team, "ball carrier")
        goal = to_x(ctx, team, 100)
        r0 = rel(ctx, team, start)
        if r0 >= 100:  # possession gained in the opponent's end zone
            self.add(Carry(player, team, kind, goal, goal, "touchdown"))
            return Dead(team, goal, "touchdown")
        out = self.p.carry(ctx, self.lineups, kind, player, r0, self.rng)
        _require(out.how in CARRY_ENDS and out.seconds >= 0, f"carry {out}")
        _require(out.forced_by is None or out.how == "fumble", "forced fumble without a fumble")
        for pid in out.tacklers + ((out.forced_by,) if out.forced_by else ()):
            self.check_player(pid, other(ctx, team), "tackler")
        r1 = min(110.0, max(-10.0, r0 + out.yards))
        if r1 <= 0 < r0 <= 5 and impetus not in (None, team):
            r1 = r0  # momentum: possession gained inside the 5 and carried into the end zone stays at the spot
        if r1 >= 100:
            self.add(Carry(player, team, kind, start, goal, "touchdown", seconds=out.seconds))
            return Dead(team, goal, "touchdown")
        end = to_x(ctx, team, r1)
        self.add(Carry(player, team, kind, start, end, out.how, out.tacklers, out.forced_by, out.seconds))
        if out.how == "fumble":
            return self.loose_ball("fumble", end, team, impetus=team, fumbler=player, forced_by=out.forced_by)
        return self.dead_at(team, end, out.how, start, impetus or team, touchback_line)

    def loose_ball(self, cause, x, last_team, impetus, fumbler=None, forced_by=None):
        ctx = self.ctx
        x = clamp_x(x)
        rec = self.p.loose_ball(ctx, self.lineups, cause, x, last_team, self.rng)
        if rec.team is not None:
            self.check_player(rec.player, rec.team, "recovering player")
        rx = clamp_x(rec.x)
        self.add(LooseBall(cause, x, last_team, fumbler, forced_by, rec.team, rec.player, rx, rec.seconds))
        if rec.team is None:  # out of bounds
            if rel(ctx, last_team, rx) >= 100:
                return self.touchback(other(ctx, last_team))
            if cause == "fumble" and rel(ctx, last_team, rx) > rel(ctx, last_team, x):
                rx = x  # a fumble forward out of bounds comes back to the spot of the fumble
            if rel(ctx, last_team, rx) <= 0:
                return Dead(last_team, rx, "safety") if impetus == last_team else self.touchback(last_team)
            return Dead(last_team, rx, "out_of_bounds")
        team = rec.team
        if rel(ctx, team, rx) >= 100:
            goal = to_x(ctx, team, 100)
            self.add(Carry(rec.player, team, "recovery", goal, goal, "touchdown"))
            return Dead(team, goal, "touchdown")
        if self.may_advance(cause, team, rec.player, last_team, fumbler):
            return self.carry("recovery", rec.player, team, rx, impetus=impetus)
        if cause in ("fumble", "bad_snap") and rel(ctx, team, rx) > rel(ctx, team, x):
            rx = x  # spotted at the fumble, unless recovered behind it
        return self.dead_at(team, rx, "recovered", rx, impetus)

    def may_advance(self, cause, team, player, last_team, fumbler):
        s = self.ctx.situation
        if cause == "muff":
            return team != self.off  # the kicking team may recover a muffed kick but not advance it
        if cause in ("fumble", "bad_snap") and team == last_team == self.off and player != fumbler:
            late = (s.quarter in (2, 4) and s.clock <= 120) or s.quarter >= 5
            return not (s.down == 4 or s.kind == "try" or late)
        return True

    def dead_at(self, team, x, how, start, impetus, touchback_line=None):
        r = rel(self.ctx, team, x)
        if r > 0:
            return Dead(team, x, how)
        if impetus != team and rel(self.ctx, team, start) <= 0:
            return self.touchback(team, touchback_line)
        return Dead(team, x, "safety")

    def touchback(self, team, line=None):
        return Dead(team, to_x(self.ctx, team, line or self.rules.touchback_line), "touchback")
