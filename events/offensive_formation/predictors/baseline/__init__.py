# START
# Baseline offensive formation predictor: a legal alignment for the unit, shotgun or under center by the priors.
# - predict(ctx, lineups, rng) -> Formation.
# Internals: _formation (hand-set templates: punt, field goal, and an offense with linemen in the middle,
# tight ends and receivers filling the line to 7, and at most 4 in the backfield).
# END
from events.offensive_formation import Formation
from shared.priors import dist_bucket, priors_of, rate

load_priors = priors_of(__file__)  # season -> priors dict


def predict(ctx, lineups, rng):
    s = ctx.situation
    if lineups.offense.unit == "victory":
        shotgun = False
    elif s.kind == "scrimmage":
        counts = load_priors(ctx.game.season)["shotgun"].get(f"{s.down}|{dist_bucket(s.distance)}", {})
        shotgun = rng.random() < (rate(counts, "shotgun") if counts else 0.6)
    else:
        shotgun = rng.random() < 0.5
    return _formation(ctx, lineups.offense, shotgun)


def _formation(ctx, lineup, shotgun) -> Formation:
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
        snapper = (of("LS") or of("OL")[:1])[0]
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
    line = tuple(ends_on_line[:1] + middle + ends_on_line[1:])
    return Formation(f"{lineup.personnel or lineup.unit} personnel", line, tuple(backfield), qb, not shotgun)
