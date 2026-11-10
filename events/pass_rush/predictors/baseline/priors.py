# START
# Builds the baseline pass rush priors from real plays.
# - observe(tally, sample): dropback: throw, sack, scramble, or throwaway; rushers: histogram of charted
#   pass rushers; sack_yards: histogram; strip_sack: fumble or no; sacker[position group]; qb_hit: hit or no
#   on targeted passes.
# END
from shared.priors import group, present


def observe(t, sample):
    s, row, f, action = sample.context.situation, sample.row, sample.charting, sample.actual["action"]
    if action == "no_play" or s.kind == "try":
        return
    if action in ("pass", "sack", "scramble"):
        throwaway = f is not None and bool(f.is_throw_away)
        t.c["dropback"][action if action != "pass" else "throwaway" if throwaway else "throw"] += 1
        if f is not None and f.n_pass_rushers > 0:
            t.hist["rushers"].append(f.n_pass_rushers)
    if action == "sack":
        t.hist["sack_yards"].append(-row.yards_gained)
        t.c["strip_sack"]["fumble" if row.fumble == 1 else "no"] += 1
        players = sample.context.by_id
        for pid in (row.sack_player_id, row.half_sack_1_player_id):
            if pid in players:
                t.c["sacker"][group(players[pid])] += 1
    if action == "pass" and present(row.receiver_player_id):
        t.c["qb_hit"]["hit" if row.qb_hit == 1 else "no"] += 1
