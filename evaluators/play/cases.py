# START
# Event cases: an event's real inputs and real output on one real play, for scoring its predictor alone.
# - event_cases(sample, runs) -> list[Case]: every event the data records on this play.
# - Case(event, args, actual, label): args are the predictor's arguments between ctx and rng (None when
#   there is no stand-in, so the case can't be scored); actual is {output name: real value}; label names
#   the sub-case ("run", "4th down").
# - read(ctx, case, out) -> {output name: value}: the same outputs from one of the predictor's samples
#   (None where a sample doesn't have the output, like sack yards on a throw).
# - Run(lineups, calls): one simulated run of the play, traced: the lineups it sent out and every predictor
#   call's (args, output) by event.
# Stand-ins: the data doesn't record who was on the field, the formation, the defensive look, or the record
#   the fouls and injuries predictors read. Those come from the first simulated run where the offense sent
#   out the same unit as in the real play (and ran the same kind of play, for fouls). Every other input is real.
# Internals: one builder per group of events (_lineups ... _dead_ball, listed in BUILDERS) and one reader per
#   event (READERS). _unit / _kind read the real play; _args / _on_field find a stand-in.
# Carries stop at the goal line in real data, so a sample's yards are capped there and its end is a touchdown.
# END
from dataclasses import dataclass

from events.target import Target
from scenarios.play import FREE_KICKS, eligible_receivers
from shared.priors import PRESNAP, flag, kickoff_result, nullified, present, role

OFFENSE = ("run", "scramble", "pass", "sack")
DROPBACK = ("pass", "sack", "scramble")
KICK_UNITS = {"punt": "punt", "field_goal": "field_goal", "kickoff": "kickoff", "onside_kickoff": "kickoff"}
PLAY_KINDS = {"run": "run", "kneel": "run", "pass": "pass", "sack": "pass", "scramble": "pass", "spike": "pass",
              "punt": "punt", "field_goal": "field_goal", "extra_point": "field_goal", "kickoff": "kickoff"}
FIELD_GOALS = {"made": "good", "missed": "no_good", "blocked": "blocked"}  # nflverse's names -> KickAttempt's
EXTRA_POINTS = {"good": "good", "failed": "no_good", "blocked": "blocked"}


@dataclass(frozen=True)
class Case:
    event: str
    args: tuple | None
    actual: dict
    label: str = ""


@dataclass
class Run:
    lineups: object
    calls: dict  # event -> [(args, output), ...]

    @property
    def unit(self) -> str:
        return self.lineups.offense.unit

    @property
    def kind(self) -> str | None:  # run, pass, punt, field_goal, or kickoff; None if the ball wasn't snapped
        if self.unit in KICK_UNITS:
            return KICK_UNITS[self.unit]
        snaps = self.calls.get("snap")
        return None if not snaps else "run" if snaps[0][1].action in ("run", "kneel") else "pass"

    def args(self, event, where=None):
        return next((args for args, _ in self.calls.get(event, ()) if where is None or where(args)), None)


def _unit(sample) -> str | None:
    """The unit the offense really sent out (None when the play didn't count, so the data can't say)."""
    s, action = sample.context.situation, sample.actual["action"]
    if s.kind in FREE_KICKS:
        return "kickoff"
    if action == "no_play":
        return None
    if s.kind == "try":
        return "field_goal" if action == "extra_point" else "offense"
    return {"punt": "punt", "field_goal": "field_goal", "kneel": "victory"}.get(action, "offense")


def _kind(sample) -> str | None:
    """Run, pass, punt, field_goal, or kickoff (None if a pre-snap foul stopped the play)."""
    action, foul = sample.actual["action"], flag(sample)
    if action != "no_play":
        return PLAY_KINDS.get(action)
    return None if foul and foul[0] in PRESNAP else nullified(sample)


def _args(runs, unit, event, where=None):
    """The arguments of the first matching call to `event` among the runs that sent out `unit` (None: any)."""
    found = (run.args(event, where) for run in runs if unit in (None, run.unit))
    return next((args for args in found if args is not None), None)


def _on_field(runs, unit):
    return next((run.lineups for run in runs if run.unit == unit), None)


def _lineups(sample, runs):
    s, unit = sample.context.situation, _unit(sample)
    if unit and s.kind == "scrimmage":
        yield Case("lineups", (), {"unit": unit}, "4th down" if s.down == 4 else "downs 1-3")
    elif unit and s.kind == "try":
        yield Case("lineups", (), {"unit": unit}, "try")


def _formations(sample, runs):
    row, charting = sample.row, sample.charting
    if sample.context.situation.kind == "scrimmage" and sample.actual["action"] in OFFENSE:
        yield Case("offensive_formation", _args(runs, "offense", "offensive_formation"),
                   {"shotgun": bool(row.shotgun == 1)})
        if charting is not None and charting.n_defense_box > 0:
            yield Case("defensive_formation", _args(runs, "offense", "defensive_formation"),
                       {"box": float(charting.n_defense_box)})


def _pre_snap(sample, runs):
    if sample.context.situation.kind not in FREE_KICKS:
        foul = flag(sample)
        yield Case("pre_snap", _args(runs, _unit(sample), "pre_snap"),
                   {"foul": "|".join(foul) if foul and foul[0] in PRESNAP else "none"})


def _snap(sample, runs):
    """The snap and the dropback behind it: snap, pass_rush, target, pass_result."""
    ctx, row, charting, action = sample.context, sample.row, sample.charting, sample.actual["action"]
    if ctx.situation.kind != "scrimmage" or action not in OFFENSE + ("spike",):
        return
    args = _args(runs, "offense", "snap")
    lineups, formation, defense = args[:3] if args else (None, None, None)
    actual = {"action": action if action in ("run", "spike") else "pass"}
    if action == "run" and row.rusher_player_id in ctx.by_id:
        actual["carrier"] = role(ctx.by_id[row.rusher_player_id])
    yield Case("snap", args, actual)
    if action in DROPBACK:
        throwaway = action == "pass" and charting is not None and bool(charting.is_throw_away)
        actual = {"result": "throwaway" if throwaway else "throw" if action == "pass" else action}
        if action == "sack":
            actual["sack yards"] = max(0.0, -float(row.yards_gained))
        if charting is not None and charting.n_pass_rushers > 0:
            actual["rushers"] = float(charting.n_pass_rushers)
        yield Case("pass_rush", args and (lineups, formation, defense), actual)
    if action == "pass" and present(row.receiver_player_id):
        actual = {}
        if row.receiver_player_id in ctx.by_id:
            actual["receiver"] = role(ctx.by_id[row.receiver_player_id])
        if present(row.air_yards):
            actual["air yards"] = float(row.air_yards)
        if present(row.pass_location):
            actual["direction"] = str(row.pass_location)
        yield Case("target", args and (lineups, formation, eligible_receivers(ctx, formation)), actual)
        if present(row.air_yards):
            result = "intercepted" if row.interception == 1 else "complete" if row.complete_pass == 1 else "incomplete"
            target = Target(row.receiver_player_id, float(row.air_yards), actual.get("direction", "middle"))
            yield Case("pass_result", args and (lineups, target), {"result": result})


def _carries(sample, runs):
    ctx, row, action = sample.context, sample.row, sample.actual["action"]
    s = ctx.situation

    def carry(unit, kind, carrier, yard_line, yards, end=None):
        if carrier in ctx.by_id and present(yards) and 0 < yard_line < 100:
            lineups = _on_field(runs, unit)
            actual = {"yards": float(yards)} | ({"end": end} if end else {})
            yield Case("carry", lineups and (lineups, kind, carrier, float(yard_line)), actual, kind)

    if s.kind == "scrimmage" and action in ("run", "scramble"):
        yield from carry("offense", action, row.rusher_player_id, s.x, row.yards_gained, _carry_end(row))
    if s.kind == "scrimmage" and action == "pass" and present(row.air_yards):
        if row.complete_pass == 1:
            yield from carry("offense", "catch", row.receiver_player_id, s.x + row.air_yards,
                             row.yards_after_catch, _carry_end(row))
        if row.interception == 1:
            yield from carry("offense", "interception", row.interception_player_id, 100 - s.x - row.air_yards,
                             row.return_yards)
    if (s.kind == "scrimmage" and action == "punt" and row.punt_blocked != 1 and row.punt_fair_catch != 1
            and present(row.kick_distance)):
        yield from carry("punt", "punt_return", row.punt_returner_player_id, 100 - s.x - row.kick_distance,
                         row.return_yards)
    if (kickoff_result(sample) or (None, None))[1] == "return":
        yield from carry("kickoff", "kick_return", row.kickoff_returner_player_id, 100 - s.x - row.kick_distance,
                         row.return_yards)


def _carry_end(row) -> str:
    return ("fumble" if row.fumble == 1 else "touchdown" if row.touchdown == 1
            else "out_of_bounds" if row.out_of_bounds == 1 else "tackled")


def _loose_ball(sample, runs):
    s, row = sample.context.situation, sample.row
    if s.kind == "scrimmage" and sample.actual["action"] in OFFENSE and row.fumble == 1:
        lineups = _on_field(runs, "offense")
        x = min(99.0, max(1.0, s.x + float(row.yards_gained)))
        yield Case("loose_ball", lineups and (lineups, "fumble", x, s.offense), {"lost": bool(row.fumble_lost == 1)})


def _punt(sample, runs):
    ctx, row = sample.context, sample.row
    s = ctx.situation
    if s.kind != "scrimmage" or sample.actual["action"] != "punt":
        return
    blocked, kicked = row.punt_blocked == 1, present(row.kick_distance)
    if row.punter_player_id in ctx.by_id:
        lineups = _on_field(runs, "punt")
        actual = {"blocked": bool(blocked)} | ({"distance": float(row.kick_distance)} if kicked and not blocked else {})
        yield Case("punt_kick", lineups and (lineups, row.punter_player_id), actual)
    if kicked and not blocked and s.x + row.kick_distance < 100 and row.touchback != 1:
        result = ("fair_catch" if row.punt_fair_catch == 1 else "downed" if row.punt_downed == 1
                  else "out_of_bounds" if row.punt_out_of_bounds == 1
                  else "muff" if row.fumble == 1 and row.return_yards == 0 else "return")
        args = _args(runs, "punt", "punt_result", lambda a: len(a[2]) > 1)  # a call for a punt that stayed in play
        yield Case("punt_result", args and (args[0], float(s.x + row.kick_distance), args[2]), {"result": result})


def _place_kick(sample, runs):
    ctx, row, action = sample.context, sample.row, sample.actual["action"]
    field_goal = ctx.situation.kind == "scrimmage" and action == "field_goal"
    extra_point = ctx.situation.kind == "try" and action == "extra_point"
    result = (FIELD_GOALS.get(row.field_goal_result) if field_goal
              else EXTRA_POINTS.get(row.extra_point_result) if extra_point else None)
    if result and present(row.kick_distance) and row.kicker_player_id in ctx.by_id:
        lineups = _on_field(runs, "field_goal")
        yield Case("kick_attempt", lineups and (lineups, row.kicker_player_id, float(row.kick_distance)),
                   {"result": result}, "field goal" if field_goal else "extra point")


def _kickoff(sample, runs):
    s, row = sample.context.situation, sample.row
    if s.kind != "kickoff" or sample.actual["action"] != "kickoff" or "onside" in str(row.desc).lower():
        return
    out = row.kickoff_out_of_bounds == 1 or row.penalty_type == "Kickoff Out of Bounds"
    lineups = _on_field(runs, "kickoff")
    actual = {"out of bounds": bool(out)}
    if not out and present(row.kick_distance):
        actual["distance"] = float(row.kick_distance)
    yield Case("free_kick", lineups and (lineups, False), actual)
    landed = kickoff_result(sample)
    if landed:
        land = float(s.x + row.kick_distance)
        args = _args(runs, "kickoff", "kick_result", lambda a: (a[1] >= 100) == (land >= 100))  # the same zone
        yield Case("kick_result", args and (args[0], land, args[2]), {"result": landed[1]})


def _dead_ball(sample, runs):
    """Fouls during or after the play, and injuries."""
    action, foul, kind = sample.actual["action"], flag(sample), _kind(sample)
    if kind:
        args = next((run.args("fouls") for run in runs if run.kind == kind and run.args("fouls")), None)
        yield Case("fouls", args, {"foul": "|".join(foul) if foul and foul[0] not in PRESNAP else "none"})
    if action != "no_play":
        yield Case("injuries", _args(runs, _unit(sample), "injuries"), {"injury": "injured" in str(sample.row.desc)})


BUILDERS = (_lineups, _formations, _pre_snap, _snap, _carries, _loose_ball, _punt, _place_kick, _kickoff, _dead_ball)


def event_cases(sample, runs) -> list[Case]:
    return [case for build in BUILDERS for case in build(sample, runs)]


def _foul(ctx, foul) -> str:
    if foul is None:
        return "none"
    return f"{foul.type}|{'offense' if foul.team == ctx.situation.offense else 'defense'}"


def _pass_rush(ctx, args, out):
    sack = out.result in ("sack", "strip_sack")
    return {"result": "sack" if sack else out.result, "sack yards": float(out.sack_yards) if sack else None,
            "rushers": float(out.rushers)}


def _carry(ctx, args, out):
    to_goal = 100 - args[3]
    end = "touchdown" if out.yards >= to_goal else "tackled" if out.how == "down" else out.how
    return {"yards": float(min(out.yards, to_goal)), "end": end}


READERS = {
    "lineups": lambda ctx, args, out: {"unit": out.offense.unit},
    "offensive_formation": lambda ctx, args, out: {"shotgun": not out.under_center},
    "defensive_formation": lambda ctx, args, out: {"box": float(out.box)},
    "pre_snap": lambda ctx, args, out: {"foul": _foul(ctx, out.foul)},
    "snap": lambda ctx, args, out: {"action": out.action,
                                    "carrier": role(ctx.by_id[out.ball_to]) if out.action == "run" else None},
    "pass_rush": _pass_rush,
    "target": lambda ctx, args, out: {"receiver": role(ctx.by_id[out.receiver]), "air yards": float(out.air_yards),
                                      "direction": out.direction},
    "pass_result": lambda ctx, args, out: {"result": out.result},
    "carry": _carry,
    "loose_ball": lambda ctx, args, out: {"lost": out.team not in (None, args[3])},
    "punt_kick": lambda ctx, args, out: {"blocked": out.blocked_by is not None,
                                         "distance": None if out.blocked_by else float(out.distance)},
    "punt_result": lambda ctx, args, out: {"result": out.result},
    "kick_attempt": lambda ctx, args, out: {"result": out.result},
    "free_kick": lambda ctx, args, out: {"out of bounds": bool(out.out_of_bounds),
                                         "distance": None if out.out_of_bounds else float(out.distance)},
    "kick_result": lambda ctx, args, out: {"result": out.result},
    "fouls": lambda ctx, args, out: {"foul": _foul(ctx, out[0] if out else None)},
    "injuries": lambda ctx, args, out: {"injury": bool(out)},
}


def read(ctx, case, out) -> dict:
    return READERS[case.event](ctx, case.args, out)
