# START
# Fouls: the catalog, which fouls are possible on a play, and penalty enforcement.
# - FoulRule / CATALOG: yardage, who can commit it, when, and how it's enforced.
# - Timings: presnap (dead ball, no snap), snap (at the snap; live ball, e.g. offside -> free play),
#   live (during the down, before any change of possession), return (during a return after a change of
#   possession), after (dead ball, after the play).
# - presnap_fouls(ctx) / live_fouls(ctx, record, live): the (type, team, timing) triples a predictor may return.
# - enforce(ctx, rules, los, live, fouls) -> Enforcement: accept/decline (hardcoded: the offended team takes
#   whichever result is worth more, see outcome.value), offsetting fouls, and enforcement spots.
# Simplifications: one accepted foul per team per play; kicking-team fouls on kicks are always tacked on to
# the end of the play (no re-kick option); fouls on a score's ensuing kickoff only for dead-ball fouls.
# END
import dataclasses
from dataclasses import dataclass

from scenarios.play import outcome
from scenarios.play.context import FREE_KICKS
from scenarios.play.field import other, rel, to_x
from scenarios.play.events import PassRush, Snap
from scenarios.play.record import Carry, Dead, Kick, LooseBall, Pass, facts


@dataclass(frozen=True)
class FoulRule:
    yards: int                    # 0 for a spot foul
    by: str                       # ball (team with the ball), no_ball, or either
    timings: tuple[str, ...]
    needs: str = "scrimmage"      # play feature required: scrimmage, any, dropback, target, throwaway, scrimmage_kick, kick_catch
    auto_first: bool = False      # automatic first down (when committed by the team without the ball)
    loss_of_down: bool = False
    from_spot: bool = False       # enforced from the spot of the foul when that's behind the enforcement spot


CATALOG = {
    "false_start": FoulRule(5, "ball", ("presnap",)),
    "delay_of_game": FoulRule(5, "ball", ("presnap",)),
    "encroachment": FoulRule(5, "no_ball", ("presnap",)),
    "neutral_zone_infraction": FoulRule(5, "no_ball", ("presnap",)),
    "defensive_offside": FoulRule(5, "no_ball", ("snap",)),
    "defensive_too_many_men": FoulRule(5, "no_ball", ("snap",)),
    "illegal_formation": FoulRule(5, "ball", ("snap",)),
    "illegal_shift": FoulRule(5, "ball", ("snap",)),
    "offensive_holding": FoulRule(10, "ball", ("live", "return"), needs="any", from_spot=True),
    "illegal_block_in_the_back": FoulRule(10, "ball", ("live", "return"), needs="any", from_spot=True),
    "defensive_holding": FoulRule(5, "no_ball", ("live",), auto_first=True),
    "illegal_contact": FoulRule(5, "no_ball", ("live",), needs="dropback", auto_first=True),
    "defensive_pass_interference": FoulRule(0, "no_ball", ("live",), needs="target", auto_first=True),
    "offensive_pass_interference": FoulRule(10, "ball", ("live",), needs="target"),
    "ineligible_downfield_pass": FoulRule(5, "ball", ("live",), needs="target"),
    "intentional_grounding": FoulRule(10, "ball", ("live",), needs="throwaway", loss_of_down=True, from_spot=True),
    "roughing_the_passer": FoulRule(15, "no_ball", ("live",), needs="dropback", auto_first=True),
    "roughing_the_kicker": FoulRule(15, "no_ball", ("live",), needs="scrimmage_kick", auto_first=True),
    "running_into_the_kicker": FoulRule(5, "no_ball", ("live",), needs="scrimmage_kick"),
    "fair_catch_interference": FoulRule(15, "ball", ("live",), needs="kick_catch"),
    "face_mask": FoulRule(15, "either", ("live", "return"), needs="any", auto_first=True),
    "unnecessary_roughness": FoulRule(15, "either", ("live", "return", "after"), needs="any", auto_first=True),
    "unsportsmanlike_conduct": FoulRule(15, "either", ("after",), needs="any", auto_first=True),
}


@dataclass(frozen=True)
class Enforcement:
    final: Dead
    accepted: tuple
    declined: tuple
    penalty_yards: dict[str, float]   # yards assessed against each team


def _teams(ctx, by, ball_team):
    if by == "ball":
        return (ball_team,)
    if by == "no_ball":
        return (other(ctx, ball_team),)
    return (ball_team, other(ctx, ball_team))


def presnap_fouls(ctx) -> frozenset:
    return frozenset((name, team, timing) for name, rule in CATALOG.items()
                     for timing in rule.timings if timing in ("presnap", "snap")
                     for team in _teams(ctx, rule.by, ctx.situation.offense))


def _features(record) -> set[str]:
    out = {"any"}
    if facts(record, Snap):
        out.add("scrimmage")
    if facts(record, PassRush):
        out.add("dropback")
    for p in facts(record, Pass):
        if p.receiver:
            out.add("target")
        if p.result == "throwaway":
            out.add("throwaway")
    for k in facts(record, Kick):
        if k.kind in ("punt", "field_goal", "pat"):
            out.add("scrimmage_kick")
        if k.result in ("fair_catch", "return", "muff"):
            out.add("kick_catch")
    return out


def live_fouls(ctx, record, live) -> frozenset:
    off = ctx.situation.offense
    features = _features(record)
    gained = any(c.team != off for c in facts(record, Carry)) or any(b.team not in (off, None) for b in facts(record, LooseBall))
    returner = live.team if live.team != off and gained else None
    out = set()
    for name, rule in CATALOG.items():
        if rule.needs not in features:
            continue
        for timing in rule.timings:
            if timing == "live":
                out.update((name, team, timing) for team in _teams(ctx, rule.by, off))
            elif timing == "return" and returner:
                out.update((name, team, timing) for team in _teams(ctx, rule.by, returner))
            elif timing == "after":
                out.update((name, team, timing) for team in _teams(ctx, "either", off))
    return frozenset(out)


def _move(ctx, x, fouler, yards):
    """Move the ball toward the fouler's goal line, never more than half the distance to it."""
    r = rel(ctx, fouler, x)
    moved = min(yards, max(r, 0.0) / 2)
    return to_x(ctx, fouler, r - moved), moved


def _in_field(ctx, team, x):
    """A spot in an end zone (after a score, safety, or touchback) moved to the nearest 1-yard line."""
    r = rel(ctx, team, x)
    return x if 0 < r < 100 else to_x(ctx, team, 1.0 if r <= 0 else 99.0)


def _tack_on(ctx, live, foul):
    """Play stands; the yardage is enforced from where it ended, against the fouling team."""
    x, yards = _move(ctx, _in_field(ctx, live.team, live.x), foul.team, CATALOG[foul.type].yards)
    first = CATALOG[foul.type].auto_first and foul.team != live.team
    return Dead(live.team, x, "penalty", kick=live.kick, series="first" if first else "normal"), yards


def _enforce_during(ctx, los, live, foul):
    """A foul during the down (timings snap, live, return). Returns (result, yards)."""
    s, rule = ctx.situation, CATALOG[foul.type]
    off, de = s.offense, s.defense
    if foul.timing == "return":
        returner = live.team
        if foul.team != returner:
            return _tack_on(ctx, live, foul)
        if rel(ctx, returner, foul.x) <= 0:
            return Dead(returner, foul.x, "safety", kick=live.kick), 0.0
        base = foul.x if rel(ctx, returner, foul.x) < rel(ctx, returner, live.x) else _in_field(ctx, returner, live.x)
        x, yards = _move(ctx, base, returner, rule.yards)
        return Dead(returner, x, "penalty", kick=live.kick), yards
    if s.kind in FREE_KICKS:
        return _tack_on(ctx, live, foul)
    if foul.team == off:
        if live.kick and live.team == de:  # kicking team foul on a punt the receiving team ended up with
            return _tack_on(ctx, live, foul)
        if rule.from_spot and rel(ctx, off, foul.x) <= 0:
            return Dead(off, foul.x, "safety", no_play=True), 0.0
        if foul.type == "intentional_grounding":
            r = min(rel(ctx, off, _move(ctx, los, off, rule.yards)[0]), rel(ctx, off, foul.x))
            return Dead(off, to_x(ctx, off, r), "penalty", series="loss", no_play=True), rel(ctx, off, los) - r
        base = foul.x if rule.from_spot and rel(ctx, off, foul.x) < rel(ctx, off, los) else los
        x, yards = _move(ctx, base, off, rule.yards)
        series = "loss" if rule.loss_of_down else "replay"
        return Dead(off, x, "penalty", series=series, no_play=True), yards + rel(ctx, off, los) - rel(ctx, off, base)
    if rule.yards == 0:  # spot foul: first down at the spot (at the 1 if in the end zone), at least 1 yard
        r = min(99.0, max(rel(ctx, off, foul.x), rel(ctx, off, los) + 1))
        return Dead(off, to_x(ctx, off, r), "penalty", series="first", no_play=True), r - rel(ctx, off, los)
    stands = (rule.yards == 15 and s.kind != "try" and live.team == off and not live.kick and live.how not in
              ("incomplete", "touchdown", "safety", "kick_good", "kick_missed")
              and rel(ctx, off, live.x) > rel(ctx, off, los))
    x, yards = _move(ctx, live.x if stands else los, de, rule.yards)
    series = "first" if rule.auto_first else "replay"
    return Dead(off, x, "penalty", series=series, no_play=not stands), yards


def _enforce_after(ctx, rules, los, current, foul):
    """A dead-ball foul after the play, enforced from the succeeding spot. Returns (result, yards)."""
    rule = CATALOG[foul.type]
    nxt, _ = outcome.next_situation(ctx, rules, los, current)
    if nxt.kind != "scrimmage":  # after a score or a try: carried over to the try or kickoff
        sign = -1 if foul.team == nxt.offense else 1
        return dataclasses.replace(current, succeeding=current.succeeding + sign * rule.yards), rule.yards
    x, yards = _move(ctx, to_x(ctx, nxt.offense, nxt.x), foul.team, rule.yards)
    if nxt.offense != ctx.situation.offense:
        return dataclasses.replace(current, team=nxt.offense, x=x), yards
    first = rule.auto_first and foul.team != nxt.offense
    return dataclasses.replace(current, x=x, series="first" if first else current.series), yards


def enforce(ctx, rules, los, live, fouls) -> Enforcement:
    s = ctx.situation
    yards = {s.offense: 0.0, s.defense: 0.0}
    if live is None:  # dead-ball foul before the snap: no play
        foul = fouls[0]
        x, moved = _move(ctx, los, foul.team, CATALOG[foul.type].yards)
        yards[foul.team] += moved
        return Enforcement(Dead(s.offense, x, "penalty", series="replay", no_play=True), (foul,), (), yards)
    during = [f for f in fouls if f.timing != "after"]
    after = [f for f in fouls if f.timing == "after"]
    final, accepted, declined = live, [], []
    if len({f.team for f in during}) == 2:  # offsetting: replay the down
        final = Dead(s.offense, los, "offsetting", series="replay", no_play=True)
        accepted += during
    elif during:
        offended = other(ctx, during[0].team)
        options = [(live, None, 0.0)]
        for f in during:
            result, moved = _enforce_during(ctx, los, live, f)
            options.append((result, f, moved))
        final, chosen, moved = max(options, key=lambda o: outcome.value(ctx, rules, los, o[0], offended))
        if chosen:
            accepted.append(chosen)
            yards[chosen.team] += moved
        declined += [f for f in during if f is not chosen]
    if len({f.team for f in after}) == 2:  # offsetting dead-ball fouls: no yardage
        accepted += after
    else:
        for f in after:
            offended = other(ctx, f.team)
            enforced, moved = _enforce_after(ctx, rules, los, final, f)
            if outcome.value(ctx, rules, los, enforced, offended) >= outcome.value(ctx, rules, los, final, offended):
                final = enforced
                accepted.append(f)
                yards[f.team] += moved
            else:
                declined.append(f)
    return Enforcement(final, tuple(accepted), tuple(declined), yards)
