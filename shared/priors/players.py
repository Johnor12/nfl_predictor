# START
# Picking players on the field for baseline predictors.
# - on_field(ctx, lineups, team): the team's 11 player ids.
# - pick(ctx, players, group_weights, rng, exclude=(), own=None): one player, weighted by position group
#   (groups without a weight get 2% of the total). A group's weight is split evenly among its players, or
#   with `own` (an `Own`) by what each of them has done before: his own rate, shrunk toward the rate of his
#   group's players on the field.
# - pick_many(ctx, players, group_weights, n, rng, own=None): n distinct players.
# - some(ctx, players, rng, happened, second, group_weights, own=None): nobody, one player, or two: whether
#   it happened at all and whether a second player had a part are {"yes": n, "no": n} counts.
# - Own(stats, per): the stats (summed) and the snap counts (summed) a player's own rate is read from, this
#   season's and the earlier seasons' (which count CAREER of this season's). TACKLES (per snap on defense
#   and special teams), PASS_RUSH, COVERAGE: a defender's tackles, sacks and hits, and passes defended, per
#   snap on defense. FLAGS: anyone's penalties per snap. From the charting: HURRIES, BLITZES, MISSES (missed tackles), TARGETED (thrown at in coverage).
# - own_shares(players, own) -> [float]: each player's share of what the group does, summing to 1.
# - returner(ctx, players, slot, rng): the best-ranked player at a depth chart slot ("PR", "KR"), else a pick.
# - fouler(ctx, lineups, name, team, rng, groups=None): who committed a foul: by the position groups that
#   commit it (`groups`, a {group: count} from the priors; anyone without) and each player's own flags.
# - usage(player, stat, got, on_play, per_snap): how often the player gets the ball on a play he is on the field
#   for: his depth chart role's rate, scaled by how his own past compares with his role's (USAGE_SNAPS, hand-set).
# END
from collections import Counter
from dataclasses import dataclass

from shared.priors.buckets import group, role
from shared.priors.sampling import rate

USAGE_SNAPS = 100  # a player's own season counts as much as his role once he has played this many snaps
CAREER = 0.5       # what the earlier seasons' totals count for, next to this season's
OWN_EVENTS = 5     # a player's own rate counts as much as his group's once the group's rate would have him at
#                    this many tackles (or sacks, or passes defended)
ANYONE = {"DL": 1, "LB": 1, "DB": 1, "OL": 1, "WR": 1, "TE": 1, "RB": 1}


@dataclass(frozen=True)
class Own:
    stats: tuple[str, ...]
    per: tuple[str, ...]


TACKLES = Own(("tackles", "assists"), ("defense_snaps", "special_teams_snaps"))  # a box score's are both units'
PASS_RUSH = Own(("sacks", "qb_hits"), ("defense_snaps",))
COVERAGE = Own(("passes_defended",), ("defense_snaps",))
FLAGS = Own(("penalties",), ("offense_snaps", "defense_snaps", "special_teams_snaps"))
HURRIES = Own(("hurries",), ("defense_snaps",))
BLITZES = Own(("blitzes",), ("defense_snaps",))
MISSES = Own(("missed_tackles",), ("defense_snaps",))
TARGETED = Own(("coverage_targets",), ("defense_snaps",))


def _past(player, own) -> tuple[float, float]:
    """(what he did, his snaps): this season's totals plus CAREER of the earlier seasons'."""
    now, before = player.stats, player.career
    total = lambda stats: sum(now.get(stat, 0.0) + CAREER * before.get(stat, 0.0) for stat in stats)  # noqa: E731
    return total(own.stats), total(own.per)


def own_shares(players, own) -> list[float]:
    """The group's rate is its players' pooled one. A player's is his own, shrunk toward it by the snaps in
    which the group's rate makes OWN_EVENTS: a rare thing (a sack) takes more snaps to show than a common
    one (a tackle). A player without snaps, or a group without any, is the group's rate."""
    past = [_past(player, own) for player in players]
    done, snaps = sum(d for d, _ in past), sum(n for _, n in past)
    if not done or not snaps:
        return [1 / len(players)] * len(players)
    prior = OWN_EVENTS * snaps / done  # the snaps the group takes for OWN_EVENTS
    rates = [(d + OWN_EVENTS) / (n + prior) for d, n in past]
    return [r / sum(rates) for r in rates]


def on_field(ctx, lineups, team) -> tuple[str, ...]:
    return lineups.offense.players if team == ctx.situation.offense else lineups.defense.players


def pick(ctx, players, group_weights, rng, exclude=(), own=None) -> str:
    players = [pid for pid in players if pid not in exclude]
    groups = [group(ctx.by_id[pid]) for pid in players]
    default = 0.02 * sum(group_weights.values())
    if own is None:
        sizes = Counter(groups)
        return rng.choices(players, [group_weights.get(g, default) / sizes[g] for g in groups])[0]
    weights = [0.0] * len(players)
    for g in sorted(set(groups)):
        members = [i for i, name in enumerate(groups) if name == g]
        shares = own_shares([ctx.by_id[players[i]] for i in members], own)
        for i, share in zip(members, shares):
            weights[i] = group_weights.get(g, default) * share
    return rng.choices(players, weights)[0]


def pick_many(ctx, players, group_weights, n, rng, own=None) -> tuple[str, ...]:
    chosen = []
    for _ in range(n):
        chosen.append(pick(ctx, players, group_weights, rng, chosen, own))
    return tuple(chosen)


def some(ctx, players, rng, happened, second, group_weights, own=None) -> tuple[str, ...]:
    if not happened or rng.random() >= rate(happened, "yes"):
        return ()
    n = 2 if second and rng.random() < rate(second, "yes") else 1
    return pick_many(ctx, players, group_weights, n, rng, own)


def returner(ctx, players, slot, rng) -> str:
    ranked = [pid for pid in players if ctx.by_id[pid].rank(slot)]
    if ranked:
        return min(ranked, key=lambda pid: ctx.by_id[pid].rank(slot))
    return pick(ctx, players, {"DB": 6, "WR": 3, "RB": 1}, rng)


def fouler(ctx, lineups, name, team, rng, groups=None) -> str:
    return pick(ctx, on_field(ctx, lineups, team), groups or ANYONE, rng, own=FLAGS)


def usage(player, stat, got, on_play, per_snap) -> float:
    """`on_play[role]` and `per_snap[role]` count {got: n, "other": n} for the players of a depth chart role:
    on the plays where the ball goes to somebody (designed runs, targeted passes), and on every offensive
    snap. A player's own past only comes per snap (his `stat` over his offense_snaps: this season's, plus
    CAREER of the earlier seasons'), so his rate per snap, shrunk toward his role's by USAGE_SNAPS snaps,
    scales his role's rate on such a play."""
    key = role(player)
    base, snap_rate = rate(on_play.get(key, {}), got), rate(per_snap.get(key, {}), got)
    done, snaps = _past(player, Own((stat,), ("offense_snaps",)))
    if not snaps or not snap_rate:
        return base
    return base * (done + USAGE_SNAPS * snap_rate) / (snaps + USAGE_SNAPS) / snap_rate
