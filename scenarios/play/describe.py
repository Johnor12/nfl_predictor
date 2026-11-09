# START
# Human-readable narration of a play, for audits and debugging.
# - describe_play(result) -> str: the situation, each event in the record, fouls, scores, and the next situation.
# - describe_situation(situation) -> str: e.g. "Q1 14:56 ARI 1&10 at ARI 30".
# - yard_line(offense, defense, x) -> str: e.g. "ARI 30" for x=30, "LAC 43" for x=57.
# END
from rulebook import rules_for
from scenarios.play.events import Foul, Formation, Injury, Lineups, PassRush, Snap
from scenarios.play.field import field_goal_distance
from scenarios.play.record import Carry, Kick, LooseBall, Pass, Sack


def yard_line(offense, defense, x):
    if x <= 0 or x >= 100:
        return f"{defense if x >= 100 else offense} end zone"
    if round(x) == 50:
        return "50"
    return f"{offense} {round(x)}" if x < 50 else f"{defense} {round(100 - x)}"


def describe_situation(s):
    clock = f"{int(s.clock // 60)}:{int(s.clock % 60):02d}"
    where = yard_line(s.offense, s.defense, s.x)
    if s.kind == "scrimmage":
        what = f"{s.down}&{'goal' if s.distance >= 100 - s.x - 1e-9 else round(s.distance)} at {where}"
    else:
        what = f"{s.kind.replace('_', ' ')} at {where}"
    score = "-".join(str(s.score[t]) for t in (s.offense, s.defense))
    return f"Q{s.quarter} {clock} {s.offense} {what} ({s.offense} {score})"


def describe_play(result) -> str:
    ctx = result.context
    s = ctx.situation
    rules = rules_for(ctx.game.season)

    def name(pid):
        return ctx.by_id[pid].name if pid else "?"

    def at(x):
        return yard_line(s.offense, s.defense, x)

    lines = [describe_situation(s)]
    for f in result.record:
        if isinstance(f, Lineups):
            lines.append(f"  lineups: {s.offense} {f.offense.unit} {f.offense.personnel or ''} vs "
                         f"{s.defense} {f.defense.unit} {f.defense.personnel or ''}")
        elif isinstance(f, Formation):
            alignment = "" if f.name in ("punt", "field goal") else ", under center" if f.under_center else ", shotgun"
            lines.append(f"  formation: {f.name}{alignment}, {name(f.qb)} takes the snap")
        elif isinstance(f, Snap) and f.bad_snap:
            lines.append("  bad snap")
        elif isinstance(f, PassRush):
            lines.append(f"  dropback: {f.rushers} rushers, {f.result} after {f.seconds:.1f}s")
        elif isinstance(f, Sack):
            lines.append(f"  {name(f.passer)} sacked at {at(f.x)} by {', '.join(map(name, f.sackers))}")
        elif isinstance(f, Pass):
            to = f" {f.direction} to {name(f.receiver)} at {at(f.x)}" if f.receiver else ""
            by = f" ({name(f.defender)})" if f.defender else ""
            lines.append(f"  {name(f.passer)} pass{to}: {f.result}{by}")
        elif isinstance(f, Carry):
            sign = 1 if f.team == s.offense else -1
            tackle = f" ({', '.join(map(name, f.tacklers))})" if f.tacklers else ""
            lines.append(f"  {name(f.player)} {f.kind.replace('_', ' ')} from {at(f.start)} to {at(f.end)} "
                         f"({sign * (f.end - f.start) + 0.0:+.0f}), {f.how.replace('_', ' ')}{tackle}")
        elif isinstance(f, LooseBall):
            got = (f"recovered by {name(f.player)} ({f.team}) at {at(f.recovery_x)}" if f.team
                   else f"out of bounds at {at(f.recovery_x)}")
            lines.append(f"  {f.cause.replace('_', ' ')} at {at(f.x)}, {got}")
        elif isinstance(f, Kick):
            land = f" to {at(f.land)}" if f.land is not None else f" ({field_goal_distance(rules, f.x)} yards)"
            by = f" ({name(f.player)})" if f.player else ""
            lines.append(f"  {name(f.kicker)} {f.kind.replace('_', ' ')} from {at(f.x)}{land}: {f.result.replace('_', ' ')}{by}")
        elif isinstance(f, Foul):
            verdict = "accepted" if f in result.accepted else "declined" if f in result.declined else "?"
            lines.append(f"  FLAG {f.type.replace('_', ' ')} on {f.team} {name(f.player)} ({f.timing}), {verdict}")
        elif isinstance(f, Injury):
            lines.append(f"  injury: {name(f.player)} out {f.plays_out} plays")
    for team, points, how in result.scores:
        lines.append(f"  SCORE {team} +{points} ({how.replace('_', ' ')})")
    if result.no_play:
        lines.append("  no play")
    lines.append(f"  next: {describe_situation(result.next)} | {result.elapsed:.0f}s used, clock {result.clock_after}")
    return "\n".join(lines)
