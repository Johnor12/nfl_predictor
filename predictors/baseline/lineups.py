# START
# Baseline personnel, lineups, and formations, filled from the depth chart.
# - PERSONNEL: offensive personnel groups -> (backs, tight ends, wide receivers).
# - personnel(situation, rng) -> str: hand-set personnel mix by situation (no 2026 participation data yet).
# - offense_lineup(ctx, team, personnel) / defense_lineup(ctx, team, package) / unit_lineup(ctx, team, unit):
#   11 player ids for the unit, best available by depth chart rank with position fallbacks.
# - package_for(personnel) -> str: the defense's matching package (base, nickel, dime).
# - offense_formation(ctx, lineup, shotgun, rng) -> Formation: a legal alignment for the unit.
# Internals: _ranked (players ordered by depth at slots), _take (fill quotas without reusing anyone).
# END
from scenarios.play.events import Formation

PERSONNEL = {"10": (1, 0, 4), "11": (1, 1, 3), "12": (1, 2, 2), "13": (1, 3, 1), "21": (2, 1, 2), "22": (2, 2, 1)}
OL_SLOTS = ("LT", "LG", "C", "RG", "RT")
DEF_SLOTS = ("LDE", "LDT", "NT", "RDT", "RDE", "WLB", "LILB", "MLB", "RILB", "SLB", "LCB", "RCB", "SS", "FS")
LB_REMOVAL = {"4-3": ("SLB", "MLB", "WLB"), "3-4": ("RILB", "LILB", "SLB", "WLB")}  # who comes off for an extra DB
COVERAGE = (("LB", 3), ("DB", 3), ("TE", 2), ("RB", 1))  # punt and kickoff coverage players, after specialists


def personnel(s, rng) -> str:
    lead = s.score[s.offense] - s.score[s.defense]
    hurry = (s.quarter == 4 and s.clock <= 300 and lead < 0) or (s.quarter == 2 and s.clock <= 120)
    if hurry:
        weights = {"11": 0.85, "10": 0.1, "12": 0.05}
    elif s.kind == "try" or (s.distance or 10) <= 1 or s.x >= 97:
        weights = {"11": 0.25, "12": 0.3, "13": 0.15, "22": 0.3}
    else:
        weights = {"11": 0.64, "12": 0.2, "21": 0.06, "13": 0.04, "22": 0.04, "10": 0.02}
    return rng.choices(list(weights), list(weights.values()))[0]


def package_for(personnel_group) -> str:
    receivers = PERSONNEL.get(personnel_group, (1, 1, 3))[2]
    return "dime" if receivers >= 4 else "nickel" if receivers == 3 else "base"


def _ranked(ctx, team, slots, positions, exclude=(), backups=False):
    """Players at the given depth slots or positions, best first (or backups first for coverage units)."""
    def rank(p):
        ranks = [r for s, r in p.depth if s in slots]
        best = min(ranks) if ranks else 50
        return (best == 1, -best) if backups else (best, p.position not in positions)
    pool = [p for p in ctx.roster(team) if p.id not in exclude
            and (p.position in positions or any(s in slots for s, _ in p.depth))]
    return [p.id for p in sorted(pool, key=rank)]


def _take(ctx, team, chosen, quotas, backups=False):
    for position, count in quotas:
        pool = _ranked(ctx, team, (position,), (position,), chosen, backups)
        chosen += pool[:count]
    return chosen


def _fill(ctx, team, chosen, positions=("WR", "TE", "RB", "LB", "DB", "DL", "OL", "FB")):
    """Top up to 11 with any unused players (never a second quarterback or specialist unless needed)."""
    extra = [p.id for p in ctx.roster(team) if p.id not in chosen and p.position in positions]
    extra += [p.id for p in ctx.roster(team) if p.id not in chosen and p.id not in extra]
    return tuple((chosen + extra)[:11])


def _specialist(ctx, team, slot, position, chosen):
    pool = _ranked(ctx, team, (slot,), (position,), chosen)
    return pool[:1]


def offense_lineup(ctx, team, personnel_group) -> tuple[str, ...]:
    backs, tight_ends, receivers = PERSONNEL[personnel_group]
    chosen = _ranked(ctx, team, ("QB",), ("QB",))[:1]
    for slot in OL_SLOTS:
        chosen += _ranked(ctx, team, (slot,), (), chosen)[:1]
    chosen += _ranked(ctx, team, OL_SLOTS, ("OL",), chosen)[:5 - sum(ctx.by_id[p].position == "OL" for p in chosen)]
    chosen += _ranked(ctx, team, ("RB",), ("RB",), chosen)[:1]
    if backs == 2:
        chosen += (_ranked(ctx, team, ("FB",), ("FB",), chosen) or _ranked(ctx, team, ("RB",), ("RB",), chosen))[:1]
    chosen = _take(ctx, team, chosen, (("TE", tight_ends), ("WR", receivers)))
    return _fill(ctx, team, chosen, ("WR", "TE", "RB", "FB"))


def defense_lineup(ctx, team, package) -> tuple[str, ...]:
    chosen, slot_of = [], {}
    for slot in DEF_SLOTS:
        pick = _ranked(ctx, team, (slot,), (), chosen)[:1]
        chosen += pick
        slot_of.update({pid: slot for pid in pick})
    if len(chosen) < 11:  # no usable depth chart: a 4-3 by position
        chosen = _take(ctx, team, chosen, (("DL", 4), ("LB", 3), ("DB", 4)))[:11]
    extra_backs = {"base": 0, "nickel": 1, "dime": 2}[package]
    removal = LB_REMOVAL["3-4" if "NT" in slot_of.values() else "4-3"]
    for _ in range(extra_backs):
        lb = next((pid for slot in removal for pid in chosen if slot_of.get(pid) == slot), None)
        if lb:
            chosen.remove(lb)
        chosen += (_ranked(ctx, team, ("NB", "LCB", "RCB", "SS", "FS"), ("DB",), chosen))[:1]
    return _fill(ctx, team, chosen[:11], ("DB", "LB", "DL"))


def unit_lineup(ctx, team, unit) -> tuple[str, ...]:
    if unit == "victory":
        return offense_lineup(ctx, team, "22")
    if unit == "defense":
        return defense_lineup(ctx, team, "base")
    chosen = []
    if unit == "punt":
        chosen += _specialist(ctx, team, "P", "P", chosen) + _specialist(ctx, team, "LS", "LS", chosen)
        chosen = _take(ctx, team, chosen, COVERAGE, backups=True)
    elif unit in ("kickoff", "onside_kickoff"):
        chosen += _specialist(ctx, team, "PK", "K", chosen)
        chosen = _take(ctx, team, chosen, (("LB", 3), ("DB", 4), ("TE", 1), ("RB", 1), ("WR", 1)), backups=True)
    elif unit == "field_goal":
        chosen += _specialist(ctx, team, "PK", "K", chosen) + _specialist(ctx, team, "H", "P", chosen)
        chosen += _specialist(ctx, team, "LS", "LS", chosen)
        for slot in OL_SLOTS:
            chosen += _ranked(ctx, team, (slot,), ("OL",), chosen)[:1]
        chosen = _take(ctx, team, chosen, (("TE", 11 - len(chosen)),))
    elif unit == "punt_return":
        chosen += _ranked(ctx, team, ("PR",), (), chosen)[:1]
        chosen = _take(ctx, team, chosen, (("DL", 2), ("LB", 3), ("DB", 4)), backups=True)
    elif unit == "field_goal_block":
        chosen = _take(ctx, team, chosen, (("DL", 5), ("LB", 3), ("DB", 3)))
    elif unit == "kick_return":
        chosen += _ranked(ctx, team, ("KR",), (), chosen)[:2]
        chosen = _take(ctx, team, chosen, (("LB", 3), ("DB", 2), ("TE", 2), ("RB", 1), ("WR", 1)), backups=True)
    return _fill(ctx, team, chosen)


def offense_formation(ctx, lineup, shotgun, rng) -> Formation:
    position = {pid: ctx.by_id[pid].position for pid in lineup.players}
    of = lambda *kinds: [pid for pid in lineup.players if position[pid] in kinds]
    if lineup.unit == "punt":
        punter = (of("P") or [lineup.players[0]])[0]
        others = [pid for pid in lineup.players if pid != punter]
        snapper = (of("LS") or others[:1])[0]
        rest = [pid for pid in others if pid != snapper]
        line = tuple(rest[:3] + [snapper] + rest[3:6])
        return Formation("punt", line, tuple([punter] + rest[6:]), punter, False)
    if lineup.unit == "field_goal":
        kicker = of("K")[0]
        holder = (of("P") or [pid for pid in lineup.players if pid != kicker and position[pid] != "OL"][:1])[0]
        snapper = (of("LS") or [pid for pid in of("OL")][:1])[0]
        others = [pid for pid in lineup.players if pid not in (kicker, holder, snapper)]
        others.sort(key=lambda pid: position[pid] != "OL")
        line = tuple(others[:3] + [snapper] + others[3:6])
        return Formation("field goal", line, (holder, kicker) + tuple(others[6:]), holder, False)
    qb = (of("QB") or [lineup.players[0]])[0]
    linemen = [pid for pid in of("OL") if pid != qb]
    backs = [pid for pid in of("RB", "FB") if pid != qb]
    ends = [pid for pid in of("TE") if pid != qb] + [pid for pid in of("WR") if pid != qb]
    others = [pid for pid in lineup.players if pid not in linemen + backs + ends + [qb]]
    line, backfield = list(linemen), [qb] + backs
    candidates = ends + others
    while candidates and (len(line) < 7 or len(backfield) + len(candidates) > 4):
        line.append(candidates.pop(0))
    backfield += candidates
    ends_on_line = [pid for pid in line if position[pid] != "OL"]
    middle = [pid for pid in line if position[pid] == "OL"]
    left = ends_on_line[:1]
    line = tuple(left + middle + ends_on_line[1:])
    return Formation(f"{lineup.personnel or lineup.unit} personnel", line, tuple(backfield), qb, not shotgun)
