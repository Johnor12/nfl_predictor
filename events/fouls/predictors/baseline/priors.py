# START
# Builds the baseline fouls priors from real plays.
# - observe(tally, sample): snaps[category]: plays per category (run, pass, punt, field_goal, kickoff);
#   fouls[category][type|side]: flags during or after the play. Pre-snap fouls belong to events/pre_snap.
#   personal[type]: the 15-yard personal fouls called, and flagrant: yes or no, whether the player was
#   disqualified for one. fouler[type][position group]: who the flag was on.
# A play wiped out by a penalty is counted under what it was (shared.priors.nullified).
# END
from shared.priors import PRESNAP, flag, flagged, flagrant, nullified

PERSONAL = ("unnecessary_roughness", "unsportsmanlike_conduct", "face_mask", "roughing_the_passer")
CATEGORIES = {"run": "run", "scramble": "run", "kneel": "run", "pass": "pass", "sack": "pass", "spike": "pass",
              "punt": "punt", "field_goal": "field_goal", "extra_point": "field_goal", "kickoff": "kickoff"}


def observe(t, sample):
    action = sample.actual["action"]
    foul = flag(sample)
    presnap = bool(foul) and foul[0] in PRESNAP
    category = CATEGORIES.get(action) if action != "no_play" else None if presnap else nullified(sample)
    if not category:
        return
    t.c["snaps"][category] += 1
    if foul and not presnap:
        t.c[f"fouls|{category}"]["|".join(foul)] += 1
        if flagged(sample):
            t.c[f"fouler|{foul[0]}"][flagged(sample)] += 1
        if foul[0] in PERSONAL:
            t.c["personal"][foul[0]] += 1
            t.c["flagrant"]["yes" if flagrant(sample) else "no"] += 1
