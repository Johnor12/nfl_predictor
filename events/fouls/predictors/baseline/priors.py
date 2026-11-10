# START
# Builds the baseline fouls priors from real plays.
# - observe(tally, sample): snaps[category]: plays per category (run, pass, punt, field_goal, kickoff);
#   fouls[category][type|side]: flags during or after the play. Pre-snap fouls belong to events/pre_snap.
# Internals: _nullified (the category of a play a penalty wiped out, from its description).
# END
from shared.priors import PRESNAP, flag

CATEGORIES = {"run": "run", "scramble": "run", "kneel": "run", "pass": "pass", "sack": "pass", "spike": "pass",
              "punt": "punt", "field_goal": "field_goal", "extra_point": "field_goal", "kickoff": "kickoff"}


def _nullified(desc):
    """nflverse labels a play wiped out by a penalty no_play; its description still says what it was."""
    play = str(desc).lower().split("penalty")[0]
    if "punt" in play:
        return "punt"
    if "field goal" in play or "extra point" in play:
        return "field_goal"
    if " kicks " in play:
        return "kickoff"
    if " pass " in play or "sacked" in play or "scrambles" in play:
        return "pass"
    return "run"


def observe(t, sample):
    action = sample.actual["action"]
    foul = flag(sample)
    presnap = bool(foul) and foul[0] in PRESNAP
    category = CATEGORIES.get(action) if action != "no_play" else None if presnap else _nullified(sample.row.desc)
    if not category:
        return
    t.c["snaps"][category] += 1
    if foul and not presnap:
        t.c[f"fouls|{category}"]["|".join(foul)] += 1
