# START
# Builds the baseline pass result priors from real plays.
# - observe(tally, sample): pass_result[air bucket] and pass_result_goal[goal bucket] (inside the 10):
#   complete, incomplete, or intercepted; defended: yes or no on incompletions;
#   defender[incomplete|intercepted][position group]: who defended or intercepted the pass.
# - observe_totals(tally, totals): from Pro Football Reference's charting (2018 on), which only comes per
#   player and game: covered: yes or no, whether a targeted pass was charted against a defender in coverage,
#   and coverage[position group]: who; drop: yes or no on incompletions; bad_throw: yes or no on the
#   incompletions that weren't dropped.
# END
from shared.priors import air_bucket, goal_bucket, group, present


def observe(t, sample):
    s, row, action = sample.context.situation, sample.row, sample.actual["action"]
    if s.kind == "try" or action != "pass" or not present(row.receiver_player_id):
        return
    if present(row.air_yards):
        result = "intercepted" if row.interception == 1 else "complete" if row.complete_pass == 1 else "incomplete"
        if row.yardline_100 <= 10:
            t.c[f"pass_result_goal|{goal_bucket(row.yardline_100)}"][result] += 1
        else:
            t.c[f"pass_result|{air_bucket(row.air_yards)}"][result] += 1
    if row.incomplete_pass == 1:
        t.c["defended"]["yes" if present(row.pass_defense_1_player_id) else "no"] += 1
    players = sample.context.by_id
    for result, pid in (("incomplete", row.incomplete_pass == 1 and row.pass_defense_1_player_id),
                        ("intercepted", row.interception == 1 and row.interception_player_id)):
        if pid in players:
            t.c[f"defender|{result}"][group(players[pid])] += 1


def observe_totals(t, totals):
    covered, drops = totals.total("coverage_targets"), totals.total("drops")
    if not covered or not drops:
        return  # a week nobody charted
    targets = totals.total("targets")
    missed = targets - totals.total("receptions") - totals.total("int_thrown")  # targeted incompletions
    bad = min(totals.total("bad_throws"), missed - drops)
    for name, (yes, of) in {"covered": (min(covered, targets), targets), "drop": (drops, missed),
                            "bad_throw": (bad, missed - drops)}.items():
        t.c[name]["yes"] += yes
        t.c[name]["no"] += of - yes
    for position, n in totals.groups("coverage_targets").items():
        t.c["coverage"][position] += n
