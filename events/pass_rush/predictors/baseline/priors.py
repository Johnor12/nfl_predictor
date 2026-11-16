# START
# Builds the baseline pass rush priors from real plays.
# - observe(tally, sample): dropback: throw, sack, or scramble; sack_yards: histogram; strip_sack: fumble or
#   no; sacker[position group]; shared_sack: yes or no, whether two defenders split it; qb_hit: hit or no on
#   targeted passes.
#   From the charting, in seasons that have it: throwaway: yes or no on throws; rushers: histogram of pass
#   rushers.
# - observe_totals(tally, totals): from Pro Football Reference's charting (2018 on), which only comes per
#   player and game: hurried: yes or no, on a throw without a hit; blitzed: yes or no, on a dropback;
#   second_hurrier and second_blitzer: yes or no, whether another defender had a part; hurrier and
#   blitzer[position group].
# END
from shared.priors import group, present


def observe(t, sample):
    s, row, f, action = sample.context.situation, sample.row, sample.charting, sample.actual["action"]
    if action == "no_play" or s.kind == "try":
        return
    if action in ("pass", "sack", "scramble"):
        t.c["dropback"][action if action != "pass" else "throw"] += 1
        if f is not None and action == "pass":
            t.c["throwaway"]["yes" if f.is_throw_away else "no"] += 1
        if f is not None and f.n_pass_rushers > 0:
            t.hist["rushers"].append(f.n_pass_rushers)
    if action == "sack":
        t.hist["sack_yards"].append(-row.yards_gained)
        t.c["strip_sack"]["fumble" if row.fumble == 1 else "no"] += 1
        t.c["shared_sack"]["yes" if present(row.half_sack_1_player_id) else "no"] += 1
        players = sample.context.by_id
        for pid in (row.sack_player_id, row.half_sack_1_player_id):
            if pid in players:
                t.c["sacker"][group(players[pid])] += 1
    if action == "pass" and present(row.receiver_player_id):
        t.c["qb_hit"]["hit" if row.qb_hit == 1 else "no"] += 1


def observe_totals(t, totals):
    hurried, blitzed = totals.total("hurried"), totals.total("blitzed")
    if not hurried or not blitzed:
        return  # a week nobody charted
    counts = {"hurried": (hurried, totals.total("pass_att") - totals.total("hit")),
              "blitzed": (blitzed, totals.total("pass_att") + totals.total("sacked")),
              "second_hurrier": (totals.total("hurries") - hurried, hurried),
              "second_blitzer": (totals.total("blitzes") - blitzed, blitzed)}
    for name, (yes, of) in counts.items():
        t.c[name]["yes"] += max(0.0, min(yes, of))
        t.c[name]["no"] += of - max(0.0, min(yes, of))
    for name, stat in (("hurrier", "hurries"), ("blitzer", "blitzes")):
        for position, n in totals.groups(stat).items():
            t.c[name][position] += n
