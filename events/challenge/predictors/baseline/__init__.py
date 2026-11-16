# START
# Baseline challenge predictor: the real rate at which the offense or the defense challenges a play and
# wins or loses, by the kind of play and how it came out.
# - predict(ctx, outcome, allowed, rng) -> Challenge | None.
# - play_key(outcome) -> str: the bucket the rates are counted and sampled by (shared with priors.py).
# - challengeable(situation) -> bool: a coach may challenge a play from here (priors.py counts only these).
# A team that may not challenge can't; its share goes to nobody.
# END
from events.challenge import Challenge
from shared.priors import choice, priors_of

load_priors = priors_of(__file__)  # (season, week) -> priors dict
ACTIONS = {"run": "run", "scramble": "run", "sack": "sack", "punt": "kick", "kickoff": "kick",
           "field_goal": "kick", "extra_point": "kick"}
RESULTS = ("touchdown", "turnover", "first_down")


def play_key(outcome) -> str:
    action = outcome["action"]
    kind = ("complete" if outcome["complete"] else "incomplete") if action == "pass" else ACTIONS.get(action, "other")
    return f"{kind}|{next((result for result in RESULTS if outcome[result]), 'other')}"


def challengeable(s) -> bool:
    return s.quarter <= 4 and not (s.quarter in (2, 4) and s.clock <= 120)


def predict(ctx, outcome, allowed, rng):
    s = ctx.situation
    counts = dict(load_priors(ctx.game.season, ctx.game.week)["challenge"].get(play_key(outcome), {}))
    for side, team in (("offense", s.offense), ("defense", s.defense)):
        if team not in allowed:
            counts["none"] = counts.get("none", 0) + counts.pop(f"{side}_won", 0) + counts.pop(f"{side}_lost", 0)
    drawn = choice(counts, rng) if sum(counts.values()) else "none"
    if drawn == "none":
        return None
    side, _, ruling = drawn.partition("_")
    return Challenge(s.offense if side == "offense" else s.defense, ruling == "won")
