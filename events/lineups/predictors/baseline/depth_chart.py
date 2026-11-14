# START
# Baseline lineups: 11 players for a unit, the ones who have been playing in it.
# - quotas(group) -> (backs, tight ends, receivers, linemen): what a personnel group puts on the field
#   ("11": 1 back, 1 tight end, 3 receivers; "12+": a sixth lineman for a receiver).
# - offense_lineup(ctx, team, group, rng) / defense_lineup(ctx, team, package, rng) /
#   unit_lineup(ctx, team, unit, rng): 11 player ids for the unit.
# Backs, receivers, tight ends, defenders, and kicking-unit regulars are drawn by their recent snaps in the
#   unit (Player.snaps, sharpened a little toward the regulars), so a player is on the field about as often
#   as he has been. Linemen
#   and specialists are the ones with the most snaps; the quarterback and returners are the depth chart's.
#   Without snaps (week 1, synthetic rosters) everyone lines up by depth chart rank.
# Internals: _snaps (a player's snaps in a unit, from whatever the season's data records), _ranked (players
#   at depth slots or positions, in the order they'd take the field), _take (fill quotas without reusing
#   anyone), _fill (top up to 11), _specialist.
# END
OL_SLOTS = ("LT", "LG", "C", "RG", "RT")
FRONT_SLOTS = ("LDE", "LDT", "NT", "RDT", "RDE", "WLB", "MLB", "SLB", "LILB", "RILB", "DL", "LB")  # the last come off first
BACK_SLOTS = ("LCB", "RCB", "SS", "FS", "NB", "DB")
BACKS = {"goal_line": 3, "base": 4, "nickel": 5, "dime": 6}  # defensive backs in each package
COVERAGE = (("LB", 3), ("DB", 3), ("TE", 2), ("RB", 1))  # punt and kickoff coverage players, after specialists
KICK_UNITS = ("punt", "punt_return", "kickoff", "kick_return")  # where a team's regular special teamers play
REGULARS = ("RB", "FB", "WR", "TE", "OL", "DL", "LB", "DB")  # positions a kicking unit is filled from
INF = float("inf")
SHARPEN = 1.5  # draw by snaps to this power: plain shares put the regulars on the field too rarely


def quotas(group) -> tuple[int, int, int, int]:
    backs, tight_ends, extra = int(group[0]), int(group[1]), group.count("+")
    return backs, tight_ends, max(0, 5 - backs - tight_ends - extra), 5 + extra


def _snaps(player, unit) -> float:
    """Recent snaps in the unit. Data without the kicking units counts all special teams snaps for the four
    that share their players."""
    snaps = dict(player.snaps)
    return snaps.get(unit, snaps.get("special_teams", 0.0) if unit in KICK_UNITS else 0.0)


def _ranked(ctx, team, unit, slots, positions, exclude=(), backups=False, rng=None):
    """Players at the given depth slots or positions. With an rng, players who have snaps in the unit come
    first, drawn without replacement by their snaps to the power SHARPEN (so the first k are on the field
    about as often as they have been); without one, the most snaps first. Then the best depth chart rank at the earliest
    slot (or backups first, for coverage units)."""
    def order(p):
        best, slot = min([(r, slots.index(s)) for s, r in p.depth if s in slots], default=(50, len(slots)))
        rank = (best == 1, -best) if backups else (best, slot, p.position not in positions)
        snaps = _snaps(p, unit)
        return (rng.expovariate(1.0) / snaps ** SHARPEN if rng and snaps else -snaps if snaps else INF), rank
    pool = [p for p in ctx.roster(team) if p.id not in exclude
            and (p.position in positions or any(s in slots for s, _ in p.depth))]
    return [p.id for p in sorted(pool, key=order)]


def _take(ctx, team, unit, chosen, quota, backups=False, rng=None):
    for position, count in quota:
        chosen += _ranked(ctx, team, unit, (position,), (position,), chosen, backups, rng)[:count]
    return chosen


def _fill(ctx, team, chosen, positions=REGULARS):
    """Top up to 11 with any unused players (never a second quarterback or specialist unless needed)."""
    extra = [p.id for p in ctx.roster(team) if p.id not in chosen and p.position in positions]
    extra += [p.id for p in ctx.roster(team) if p.id not in chosen and p.id not in extra]
    return tuple((chosen + extra)[:11])


def _specialist(ctx, team, unit, slot, position, chosen):
    return _ranked(ctx, team, unit, (slot,), (position,), chosen)[:1]


def offense_lineup(ctx, team, group, rng) -> tuple[str, ...]:
    backs, tight_ends, receivers, linemen = quotas(group)
    chosen = _ranked(ctx, team, None, ("QB",), ("QB",))[:1]  # the depth chart knows the starter better than snaps do
    chosen += _ranked(ctx, team, "offense", OL_SLOTS, ("OL",), chosen)[:linemen]
    chosen += _ranked(ctx, team, "offense", ("RB",), ("RB",), chosen, rng=rng)[:min(backs, 1)]
    fullbacks = _ranked(ctx, team, "offense", ("FB",), ("FB",), chosen)[:1]  # a second back is the fullback
    chosen += (fullbacks + _ranked(ctx, team, "offense", ("RB",), ("RB",), chosen, rng=rng))[:max(0, backs - 1)]
    chosen = _take(ctx, team, "offense", chosen, (("TE", tight_ends), ("WR", receivers)), rng=rng)
    return _fill(ctx, team, chosen, ("WR", "TE", "RB", "FB"))


def defense_lineup(ctx, team, package, rng) -> tuple[str, ...]:
    backs = BACKS[package]
    chosen = _ranked(ctx, team, "defense", BACK_SLOTS, ("DB",), rng=rng)[:backs]
    chosen += _ranked(ctx, team, "defense", FRONT_SLOTS, ("DL", "LB"), chosen, rng=rng)[:11 - backs]
    return _fill(ctx, team, chosen, ("DB", "LB", "DL"))


def unit_lineup(ctx, team, unit, rng) -> tuple[str, ...]:
    if unit == "victory":
        return offense_lineup(ctx, team, "22", rng)
    if unit == "defense":
        return defense_lineup(ctx, team, "base", rng)
    unit = "kickoff" if unit == "onside_kickoff" else unit
    specialist = lambda slot, position: _specialist(ctx, team, unit, slot, position, chosen)
    chosen = []
    if unit == "punt":
        chosen += specialist("P", "P") + specialist("LS", "LS")
    elif unit == "kickoff":
        chosen += specialist("PK", "K")
    elif unit == "field_goal":
        chosen += specialist("PK", "K") + specialist("H", "P") + specialist("LS", "LS")
    elif unit == "punt_return":
        chosen += _ranked(ctx, team, None, ("PR",), (), chosen)[:1]
    elif unit == "kick_return":
        chosen += _ranked(ctx, team, None, ("KR",), (), chosen)[:2]
    regulars = _ranked(ctx, team, unit, (), REGULARS, chosen, rng=rng)  # whoever has been playing in the unit
    chosen += [pid for pid in regulars if _snaps(ctx.by_id[pid], unit) > 0][:11 - len(chosen)]
    if unit == "punt":
        chosen = _take(ctx, team, unit, chosen, COVERAGE, backups=True)
    elif unit == "kickoff":
        chosen = _take(ctx, team, unit, chosen, (("LB", 3), ("DB", 4), ("TE", 1), ("RB", 1), ("WR", 1)), backups=True)
    elif unit == "field_goal":
        chosen += _ranked(ctx, team, unit, OL_SLOTS, ("OL",), chosen)[:5]
        chosen = _take(ctx, team, unit, chosen, (("TE", 11),))
    elif unit == "punt_return":
        chosen = _take(ctx, team, unit, chosen, (("DL", 2), ("LB", 3), ("DB", 4)), backups=True)
    elif unit == "field_goal_block":
        chosen = _take(ctx, team, unit, chosen, (("DL", 5), ("LB", 3), ("DB", 3)))
    elif unit == "kick_return":
        chosen = _take(ctx, team, unit, chosen, (("LB", 3), ("DB", 2), ("TE", 2), ("RB", 1), ("WR", 1)), backups=True)
    return _fill(ctx, team, chosen)
