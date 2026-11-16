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
#   at depth slots or positions, in the order they'd take the field), _pool (what _ranked needs to know about
#   each of them, remembered for as long as the same players are active: ranking is most of a simulated
#   game's time otherwise), _linemen (offensive linemen), _take (fill quotas without reusing anyone), _fill
#   (top up to 11). SPECIALISTS: each kicking unit's specialists.
# END
OL_SLOTS = ("LT", "LG", "C", "RG", "RT")
FRONT_SLOTS = ("LDE", "LDT", "NT", "RDT", "RDE", "WLB", "MLB", "SLB", "LILB", "RILB", "DL", "LB")  # the last come off first
BACK_SLOTS = ("LCB", "RCB", "SS", "FS", "NB", "DB")
BACKS = {"goal_line": 3, "base": 4, "nickel": 5, "dime": 6}  # defensive backs in each package
COVERAGE = (("LB", 3), ("DB", 3), ("TE", 2), ("RB", 1))  # punt and kickoff coverage players, after specialists
KICK_UNITS = ("punt", "punt_return", "kickoff", "kick_return")  # where a team's regular special teamers play
REGULARS = ("RB", "FB", "WR", "TE", "OL", "DL", "LB", "DB")  # positions a kicking unit is filled from
SPECIALISTS = {  # unit -> its specialists as (depth slot, position), in the order they are picked
    "punt": (("P", "P"), ("LS", "LS")), "kickoff": (("PK", "K"),),
    "field_goal": (("PK", "K"), ("H", "P"), ("LS", "LS")),
}
INF = float("inf")
SHARPEN = 1.5  # draw by snaps to this power: plain shares put the regulars on the field too rarely
KEPT = 64  # sets of active players whose pools are remembered (a game goes through a few as players get hurt)
_POOLS = {}  # id of a tuple of active players -> (the tuple, {_pool's other arguments: its result})


def quotas(group) -> tuple[int, int, int, int]:
    backs, tight_ends, extra = int(group[0]), int(group[1]), group.count("+")
    return backs, tight_ends, max(0, 5 - backs - tight_ends - extra), 5 + extra


def _snaps(player, unit) -> float:
    """Recent snaps in the unit. Data without the kicking units counts all special teams snaps for the four
    that share their players."""
    snaps = dict(player.snaps)
    return snaps.get(unit, snaps.get("special_teams", 0.0) if unit in KICK_UNITS else 0.0)


def _pool(players, team, unit, slots, positions, backups):
    """The team's players at the given depth slots or positions, in roster order, as (id, snaps in the unit
    to the power SHARPEN, depth chart rank), and their ids with the most snaps first. Nothing here changes
    while the same players are active, so it is worked out once for them, not on every play."""
    if id(players) not in _POOLS:
        if len(_POOLS) >= KEPT:
            _POOLS.clear()
        _POOLS[id(players)] = (players, {})  # holding the tuple keeps its id its own
    pools = _POOLS[id(players)][1]
    key = (team, unit, slots, positions, backups)
    if key not in pools:
        pool, order = [], []
        for p in players:
            if p.team == team and (p.position in positions or any(s in slots for s, _ in p.depth)):
                best, slot = min([(r, slots.index(s)) for s, r in p.depth if s in slots], default=(50, len(slots)))
                rank = (best == 1, -best) if backups else (best, slot, p.position not in positions)
                snaps = _snaps(p, unit)
                pool.append((p.id, snaps ** SHARPEN if snaps else 0.0, rank))
                order.append((-snaps if snaps else INF, rank, len(order), p.id))  # its place keeps ties in roster order
        pools[key] = pool, [entry[-1] for entry in sorted(order)]
    return pools[key]


def _ranked(ctx, team, unit, slots, positions, exclude=(), backups=False, rng=None):
    """Players at the given depth slots or positions. With an rng, players who have snaps in the unit come
    first, drawn without replacement by their snaps to the power SHARPEN (so the first k are on the field
    about as often as they have been); without one, the most snaps first. Then the best depth chart rank at the earliest
    slot (or backups first, for coverage units)."""
    pool, by_snaps = _pool(ctx.players, team, unit, slots, positions, backups)
    if not rng:
        return [pid for pid in by_snaps if pid not in exclude]
    drawn = [(rng.expovariate(1.0) / weight if weight else INF, rank, i, pid)
             for i, (pid, weight, rank) in enumerate(pool) if pid not in exclude]  # i keeps ties in roster order
    return [entry[-1] for entry in sorted(drawn)]


def _take(ctx, team, unit, chosen, quota, backups=False, rng=None):
    for position, count in quota:
        chosen += _ranked(ctx, team, unit, (position,), (position,), chosen, backups, rng)[:count]
    return chosen


def _fill(ctx, team, chosen, positions=REGULARS):
    """Top up to 11 with any unused players (never a second quarterback or specialist unless needed)."""
    if len(chosen) >= 11:
        return tuple(chosen[:11])
    extra = [p.id for p in ctx.roster(team) if p.id not in chosen and p.position in positions]
    extra += [p.id for p in ctx.roster(team) if p.id not in chosen and p.id not in extra]
    return tuple((chosen + extra)[:11])


def _linemen(ctx, team, unit, chosen, count):
    """Offensive linemen by position only: a depth chart that lists someone else at a line slot is wrong."""
    ranked = _ranked(ctx, team, unit, OL_SLOTS, ("OL",), chosen)
    return [pid for pid in ranked if ctx.by_id[pid].position == "OL"][:count]


def offense_lineup(ctx, team, group, rng) -> tuple[str, ...]:
    backs, tight_ends, receivers, linemen = quotas(group)
    chosen = _ranked(ctx, team, None, ("QB",), ("QB",))[:1]  # the depth chart knows the starter better than snaps do
    chosen += _linemen(ctx, team, "offense", chosen, linemen)
    chosen += _ranked(ctx, team, "offense", ("RB",), ("RB",), chosen, rng=rng)[:min(backs, 1)]
    fullbacks = _ranked(ctx, team, "offense", ("FB",), ("FB",), chosen)[:1]  # a second back is the fullback
    chosen += (fullbacks + _ranked(ctx, team, "offense", ("RB",), ("RB",), chosen + fullbacks, rng=rng))[:max(0, backs - 1)]
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
    unit = {"onside_kickoff": "kickoff", "fair_catch_kick": "field_goal"}.get(unit, unit)
    chosen = []
    for slot, position in SPECIALISTS.get(unit, ()):  # one at a time, so nobody fills two jobs
        ranked = _ranked(ctx, team, unit, (slot,), (position,), chosen)
        chosen += sorted(ranked, key=lambda pid: ctx.by_id[pid].position != position)[:1]  # a kicker before a punter listed at kicker
    if unit == "punt_return":
        chosen += _ranked(ctx, team, None, ("PR",), (), chosen)[:1]
    elif unit == "kick_return":
        chosen += _ranked(ctx, team, None, ("KR",), (), chosen)[:2]
    played = {pid for pid, weight, _ in _pool(ctx.players, team, unit, (), REGULARS, False)[0] if weight}
    regulars = _ranked(ctx, team, unit, (), REGULARS, chosen, rng=rng)  # whoever has been playing in the unit
    chosen += [pid for pid in regulars if pid in played][:11 - len(chosen)]
    if unit == "punt":
        chosen = _take(ctx, team, unit, chosen, COVERAGE, backups=True)
    elif unit == "kickoff":
        chosen = _take(ctx, team, unit, chosen, (("LB", 3), ("DB", 4), ("TE", 1), ("RB", 1), ("WR", 1)), backups=True)
    elif unit == "field_goal":
        chosen += _linemen(ctx, team, unit, chosen, 5)
        chosen = _take(ctx, team, unit, chosen, (("TE", 11),))
    elif unit == "punt_return":
        chosen = _take(ctx, team, unit, chosen, (("DL", 2), ("LB", 3), ("DB", 4)), backups=True)
    elif unit == "field_goal_block":
        chosen = _take(ctx, team, unit, chosen, (("DL", 5), ("LB", 3), ("DB", 3)))
    elif unit == "kick_return":
        chosen = _take(ctx, team, unit, chosen, (("LB", 3), ("DB", 2), ("TE", 2), ("RB", 1), ("WR", 1)), backups=True)
    return _fill(ctx, team, chosen)
