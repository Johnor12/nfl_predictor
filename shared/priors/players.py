# START
# Picking players on the field for baseline predictors.
# - on_field(ctx, lineups, team): the team's 11 player ids.
# - pick(ctx, players, group_weights, rng, exclude=()): one player, weighted by position group (the weight
#   is split evenly within a group; groups without a weight get 2% of the total).
# - pick_many(ctx, players, group_weights, n, rng): n distinct players.
# - returner(ctx, players, slot, rng): the best-ranked player at a depth chart slot ("PR", "KR"), else a pick.
# - fouler(ctx, lineups, name, team, rng): who committed a foul, by the positions that usually do (FOULERS, hand-set).
# END
from collections import Counter

from shared.priors.buckets import group

ANYONE = {"DL": 1, "LB": 1, "DB": 1, "OL": 1, "WR": 1, "TE": 1, "RB": 1}
FOULERS = {
    "false_start": {"OL": 8, "TE": 1, "WR": 1}, "delay_of_game": {"QB": 1}, "encroachment": {"DL": 1},
    "neutral_zone_infraction": {"DL": 4, "LB": 1}, "defensive_offside": {"DL": 3, "LB": 1},
    "illegal_formation": {"OL": 1, "WR": 2, "TE": 1}, "illegal_shift": {"WR": 2, "TE": 1, "RB": 1},
    "offensive_holding": {"OL": 8, "TE": 1.5, "WR": 0.5}, "defensive_holding": {"DB": 4, "LB": 1},
    "illegal_contact": {"DB": 1}, "defensive_pass_interference": {"DB": 6, "LB": 1},
    "offensive_pass_interference": {"WR": 3, "TE": 1}, "ineligible_downfield_pass": {"OL": 1},
    "roughing_the_passer": {"DL": 4, "LB": 1}, "face_mask": {"DL": 1, "LB": 1, "DB": 1},
}


def on_field(ctx, lineups, team) -> tuple[str, ...]:
    return lineups.offense.players if team == ctx.situation.offense else lineups.defense.players


def pick(ctx, players, group_weights, rng, exclude=()) -> str:
    players = [pid for pid in players if pid not in exclude]
    groups = [group(ctx.by_id[pid]) for pid in players]
    sizes = Counter(groups)
    default = 0.02 * sum(group_weights.values())
    return rng.choices(players, [group_weights.get(g, default) / sizes[g] for g in groups])[0]


def pick_many(ctx, players, group_weights, n, rng) -> tuple[str, ...]:
    chosen = []
    for _ in range(n):
        chosen.append(pick(ctx, players, group_weights, rng, chosen))
    return tuple(chosen)


def returner(ctx, players, slot, rng) -> str:
    ranked = [pid for pid in players if ctx.by_id[pid].rank(slot)]
    if ranked:
        return min(ranked, key=lambda pid: ctx.by_id[pid].rank(slot))
    return pick(ctx, players, {"DB": 6, "WR": 3, "RB": 1}, rng)


def fouler(ctx, lineups, name, team, rng) -> str:
    return pick(ctx, on_field(ctx, lineups, team), FOULERS.get(name, ANYONE), rng)
