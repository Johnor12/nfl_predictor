# START
# Builds the baseline carry priors from real plays.
# - observe(tally, sample): yardage histograms by kind of carry: run, scramble, catch (yards after the
#   catch), interception, punt_return, kick_return; run_goal / catch_goal[goal bucket]: goal-to-go histograms;
#   carry_end[kind]: tackled, out_of_bounds, or fumble; tackler[scrimmage|kick][position group]; assisted: yes or no.
# Run, scramble, and catch histograms only use carries that started 50+ yards from the goal line, so long
# gains aren't cut short by touchdowns.
# END
from shared.priors import goal_bucket, group, kickoff_result, present


def observe(t, sample):
    s, row, action = sample.context.situation, sample.row, sample.actual["action"]
    if action == "no_play" or s.kind == "try":
        return
    if action in ("run", "scramble") or (action == "pass" and row.complete_pass == 1):
        kind = "catch" if action == "pass" else action
        yards = row.yards_after_catch if kind == "catch" else row.yards_gained
        to_goal = row.yardline_100 - (row.air_yards if kind == "catch" else 0)
        if to_goal >= 50:
            t.hist[kind].append(yards)
        elif 0 < to_goal <= 10 and kind != "scramble":
            t.hist[f"{kind}_goal|{goal_bucket(to_goal)}"].append(yards)
        end = "fumble" if row.fumble == 1 else "out_of_bounds" if row.out_of_bounds == 1 else "tackled"
        t.c[f"carry_end|{kind}"][end] += 1
    if row.interception == 1:
        t.hist["interception"].append(row.return_yards)
    if action == "punt" and row.punt_blocked != 1 and present(row.punt_returner_player_id) and row.punt_fair_catch != 1:
        t.hist["punt_return"].append(row.return_yards)
    if (kickoff_result(sample) or (None, None))[1] == "return":
        t.hist["kick_return"].append(row.return_yards)
    players = sample.context.by_id
    for pid in (row.solo_tackle_1_player_id, row.assist_tackle_1_player_id, row.tackle_with_assist_1_player_id):
        if pid in players:
            t.c[f"tackler|{'kick' if action in ('punt', 'kickoff') else 'scrimmage'}"][group(players[pid])] += 1
    solo, assist = present(row.solo_tackle_1_player_id), present(row.assist_tackle_1_player_id)
    if action in ("run", "pass", "scramble") and (solo or assist):
        t.c["assisted"]["yes" if assist else "no"] += 1
