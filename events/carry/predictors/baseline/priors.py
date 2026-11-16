# START
# Builds the baseline carry priors from real plays.
# - observe(tally, sample): yardage histograms by kind of carry: run[position group of the carrier],
#   scramble, catch[air bucket|position group of the receiver] (yards after the catch), interception,
#   punt_return, kick_return; run_goal / catch_goal[goal bucket]: goal-to-go histograms;
#   carry_end[kind]: tackled, out_of_bounds, or fumble; lateral[run|catch]: yes or no;
#   tackler[scrimmage|kick][position group]; assisted: yes or no.
#   For a run, a scramble, a catch, and a punt or kick return that didn't score, by how it ended:
#   credited[kind|end]: yes or no, whether anybody got a tackle; shared[kind]: yes (two assists) or no (one
#   tackle; a tackle with an assist counts half each way, so both totals come out);
#   tackler[kind|solo] and tackler[kind|assisted][position group]: who made them.
# - observe_totals(tally, totals): from Pro Football Reference's charting (2018 on), which only comes per
#   player and game: broken[run|catch]: yes or no, whether the carrier broke a tackle; missed: yes or no,
#   whether a defender missed one on a carry nobody broke a tackle on (their charters count twice the misses
#   they count broken tackles), and misser[position group]; after_contact: a run's yards after contact, of
#   its yards.
# Run, scramble, and catch histograms only use carries that started 50+ yards from the goal line, so long
# gains aren't cut short by touchdowns.
# END
from shared.priors import air_bucket, goal_bucket, group, kickoff_result, present

CARRIERS = {"run": ("QB", "RB", "WR", "TE"), "catch": ("RB", "WR", "TE")}  # position groups with their own histogram


def observe(t, sample):
    s, row, action = sample.context.situation, sample.row, sample.actual["action"]
    if action == "no_play" or s.kind == "try":
        return
    if action in ("run", "scramble") or (action == "pass" and row.complete_pass == 1):
        kind = "catch" if action == "pass" else action
        yards = row.yards_after_catch if kind == "catch" else row.yards_gained
        to_goal = row.yardline_100 - (row.air_yards if kind == "catch" else 0)
        carrier = sample.context.by_id.get(row.receiver_player_id if kind == "catch" else row.rusher_player_id)
        if to_goal >= 50 and kind == "scramble":
            t.hist[kind].append(yards)
        elif to_goal >= 50 and carrier and group(carrier) in CARRIERS[kind]:
            cell = f"{air_bucket(row.air_yards)}|{group(carrier)}" if kind == "catch" else group(carrier)
            t.hist[f"{kind}|{cell}"].append(yards)
        elif 0 < to_goal <= 10 and kind != "scramble":
            t.hist[f"{kind}_goal|{goal_bucket(to_goal)}"].append(yards)
        end = "fumble" if row.fumble == 1 else "out_of_bounds" if row.out_of_bounds == 1 else "tackled"
        t.c[f"carry_end|{kind}"][end] += 1
        _tackle(t, sample, kind)
        if kind != "scramble":
            lateral = row.lateral_reception if kind == "catch" else row.lateral_rush
            t.c[f"lateral|{kind}"]["yes" if lateral == 1 else "no"] += 1
    if row.interception == 1:
        t.hist["interception"].append(row.return_yards)
    if action == "punt" and row.punt_blocked != 1 and present(row.punt_returner_player_id) and row.punt_fair_catch != 1:
        t.hist["punt_return"].append(row.return_yards)
        _tackle(t, sample, "punt_return")
    if (kickoff_result(sample) or (None, None))[1] == "return":
        t.hist["kick_return"].append(row.return_yards)
        _tackle(t, sample, "kick_return")
    players = sample.context.by_id
    for pid in (row.solo_tackle_1_player_id, row.assist_tackle_1_player_id, row.tackle_with_assist_1_player_id):
        if pid in players:
            t.c[f"tackler|{'kick' if action in ('punt', 'kickoff') else 'scrimmage'}"][group(players[pid])] += 1
    solo, assist = present(row.solo_tackle_1_player_id), present(row.assist_tackle_1_player_id)
    if action in ("run", "pass", "scramble") and (solo or assist):
        t.c["assisted"]["yes" if assist else "no"] += 1


def _tackle(t, sample, kind):
    """Who the box score credited on a carry that didn't score."""
    row, players = sample.row, sample.context.by_id
    if row.touchdown == 1:
        return
    end = "fumble" if row.fumble == 1 else "out_of_bounds" if row.out_of_bounds == 1 else "tackled"
    solo = [pid for pid in (row.solo_tackle_1_player_id, row.solo_tackle_2_player_id,
                            row.tackle_with_assist_1_player_id, row.tackle_with_assist_2_player_id) if present(pid)]
    assists = [pid for pid in (row.assist_tackle_1_player_id, row.assist_tackle_2_player_id,
                               row.assist_tackle_3_player_id, row.assist_tackle_4_player_id) if present(pid)]
    t.c[f"credited|{kind}|{end}"]["yes" if solo or assists else "no"] += 1
    if solo or assists:
        t.c[f"shared|{kind}"]["yes"] += 0.5 * bool(assists) + 0.5 * (not solo)
        t.c[f"shared|{kind}"]["no"] += 0.5 * bool(solo) + 0.5 * (not assists)
    for how, pids in (("solo", solo), ("assisted", assists)):
        for pid in pids:
            if pid in players:
                t.c[f"tackler|{kind}|{how}"][group(players[pid])] += 1


def observe_totals(t, totals):
    missed, after = totals.total("missed_tackles"), totals.total("rush_yds_after_contact")
    if not missed or not after:
        return  # a week nobody charted
    carries = {"run": totals.total("rush_att"), "catch": totals.total("receptions")}
    broken = {"run": totals.total("rush_broken_tackles"), "catch": totals.total("rec_broken_tackles")}
    for kind in carries:
        t.c[f"broken|{kind}"]["yes"] += broken[kind]
        t.c[f"broken|{kind}"]["no"] += carries[kind] - broken[kind]
    unbroken = sum(carries.values()) - sum(broken.values())
    t.c["missed"]["yes"] += min(unbroken, max(0.0, missed - sum(broken.values())))
    t.c["missed"]["no"] += unbroken - min(unbroken, max(0.0, missed - sum(broken.values())))
    for position, n in totals.groups("missed_tackles").items():
        t.c["misser"][position] += n
    t.c["after_contact"]["yes"] += after
    t.c["after_contact"]["no"] += max(0.0, totals.total("rush_yds") - after)
