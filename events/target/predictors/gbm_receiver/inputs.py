# START
# The receiver model's inputs: what is known about each player the quarterback could throw to, as rows of
# numbers.
# - NAMES: the feature names, in the model's column order. RECEIVERS: the positions it chooses among.
# - candidates(ctx, players, shotgun) -> list[list[float]]: one row per player who could be thrown to (a list
#   of `Player`s): the situation and the shotgun, the same in every row, then the player: his position and
#   depth chart rank, his targets per snap on offense (this season, and over earlier ones), each also as his
#   share of the candidates' rates added up (who else is out there is most of what decides it), his targets
#   this season, how deep he is thrown to, his years in the league, and who the candidates are (how many,
#   and how many receivers, tight ends, and backs). The same function reads a simulated play (predict) and
#   a real one (train.py).
# END
import math
from collections import Counter

from events import situation, strength

RECEIVERS = ("RB", "FB", "WR", "TE")
NAMES = situation.NAMES + ("shotgun", "position", "rank", "rate", "rate_before", "share", "share_before", "targets",
                           "depth", "depth_before", "experience", "candidates", "receivers", "tight_ends", "backs")


def candidates(ctx, players, shotgun) -> list[list[float]]:
    play = situation.features(ctx) + [shotgun]
    rates = [strength.rates(player, "targets", "offense_snaps") for player in players]
    totals = [sum(rate[i] for rate in rates if not math.isnan(rate[i])) for i in (0, 1)]
    positions = Counter(player.position for player in players)
    out = [len(players), positions["WR"], positions["TE"], positions["RB"] + positions["FB"]]
    rows = []
    for player, rate in zip(players, rates):
        rank = player.rank(player.position)
        shares = [r / total if total else math.nan for r, total in zip(rate, totals)]
        rows.append(play + [strength.position(player), math.nan if rank is None else rank, *rate, *shares,
                            strength.total(player, "targets"), *strength.rates(player, "target_air_yds", "targets"),
                            strength.experience(player)] + out)
    return rows
