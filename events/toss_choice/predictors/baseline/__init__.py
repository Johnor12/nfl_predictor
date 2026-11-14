# START
# Baseline toss choice predictor: hand-set rates (play-by-play data doesn't record the toss).
# - predict(ctx, winner, allowed, rng) -> str.
# The opening toss is almost always deferred. In overtime the winner takes the ball when a touchdown on the
# first possession wins the game, and is split when both teams are guaranteed a possession.
# END
from shared.rulebook import rules_for

OPENING = {"defer": 0.9, "receive": 0.1}
OVERTIME = {"sudden_death": {"receive": 0.98, "kick": 0.02}, "modified": {"receive": 0.97, "kick": 0.03},
            "both_possess": {"receive": 0.5, "kick": 0.5}}


def predict(ctx, winner, allowed, rng):
    rules = rules_for(ctx.game.season)
    form = rules.playoff_overtime_format if ctx.game.playoff else rules.overtime_format
    weights = OVERTIME[form] if ctx.overtime else OPENING
    choices = [c for c in allowed if c in weights]
    return rng.choices(choices, [weights[c] for c in choices])[0]
