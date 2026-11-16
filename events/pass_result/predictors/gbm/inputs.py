# START
# The pass result model's inputs: what is known as the ball is in the air, as one row of numbers.
# - NAMES: the feature names, in the model's column order. WHO: the ones about the quarterback and the
#   defense, which the model reads coarsely (shared.models).
# - RESULTS: the model's classes, in order: complete, incomplete, intercepted.
# - features(ctx, qb, receiver, air_yards) -> list[float]: one play's values (nan where unknown): the
#   situation and the game so far (events.situation), how far downfield the pass is thrown and how far
#   short of the goal line it arrives (negative in the end zone), the receiver's position, the
#   quarterback's completions and interceptions per attempt, and the same for the passes thrown against
#   this defense, each this season and over earlier ones. `qb` and `receiver` are `Player`s, or None. The
#   same function reads a simulated play (predict) and a real one (train.py).
# END
import math

from events import situation, strength

RESULTS = ("complete", "incomplete", "intercepted")
WHO = ("qb_completions", "qb_completions_before", "qb_interceptions", "qb_interceptions_before",
       "defense_completions", "defense_completions_before", "defense_interceptions", "defense_interceptions_before")
NAMES = situation.NAMES + ("air_yards", "arrives_to_goal", "receiver_position") + WHO


def features(ctx, qb, receiver, air_yards) -> list[float]:
    defense = ctx.game.form(ctx.situation.defense)
    passer = (strength.rates(qb, "pass_cmp", "pass_att") + strength.rates(qb, "int_thrown", "pass_att")
              if qb else [math.nan] * 4)
    arrives = 100 - ctx.situation.x - air_yards
    return (situation.features(ctx) + [air_yards, arrives, strength.position(receiver) if receiver else math.nan] + passer
            + strength.rates(defense, "allowed_pass_cmp", "allowed_pass_att")
            + strength.rates(defense, "allowed_int_thrown", "allowed_pass_att"))
