# START
# The pass result model's inputs: what is known as the ball is in the air, as one row of numbers.
# - NAMES: the feature names, in the model's column order. RATINGS: the quarterback's and the defense's
#   completion ratings (events.strength.rating: completions over expected per attempt, shrunk by QB_PASSES
#   and DEFENSE_PASSES), read exactly. WHO: their interception rates, which the model reads coarsely
#   (shared.models).
# - RESULTS: the model's classes, in order: complete, incomplete, intercepted.
# - features(ctx, qb, receiver, air_yards) -> list[float]: one play's values (nan where unknown): the
#   situation and the game so far (events.situation), how far downfield the pass is thrown and how far
#   short of the goal line it arrives (negative in the end zone), the receiver's position, the
#   quarterback's completion rating and the one of the passes thrown against this defense, and both's
#   interceptions per attempt, this season and over earlier ones. `qb` and `receiver` are `Player`s, or
#   None (a missing quarterback is the league's: 0). The same function reads a simulated play (predict)
#   and a real one (train.py).
# END
import math

from events import situation, strength

RESULTS = ("complete", "incomplete", "intercepted")
WHO = ("qb_interceptions", "qb_interceptions_before", "defense_interceptions", "defense_interceptions_before")
RATINGS = ("qb_completions_over", "defense_completions_over")  # shrunk already: read exactly
NAMES = situation.NAMES + ("air_yards", "arrives_to_goal", "receiver_position") + RATINGS + WHO
QB_PASSES, DEFENSE_PASSES = 150, 300  # the passes a completion rating is shrunk by (chosen on 2016 to 2020)


def features(ctx, qb, receiver, air_yards) -> list[float]:
    defense = ctx.game.form(ctx.situation.defense)
    arrives = 100 - ctx.situation.x - air_yards
    return (situation.features(ctx) + [air_yards, arrives, strength.position(receiver) if receiver else math.nan]
            + [strength.rating(qb, "pass_cmp_over", "pass_att", QB_PASSES) if qb else 0.0,
               strength.rating(defense, "allowed_pass_cmp_over", "allowed_pass_att", DEFENSE_PASSES)]
            + (strength.rates(qb, "int_thrown", "pass_att") if qb else [math.nan] * 2)
            + strength.rates(defense, "allowed_int_thrown", "allowed_pass_att"))
