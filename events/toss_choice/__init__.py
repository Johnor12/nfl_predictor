# START
# The toss choice event: what the team that won the coin toss does with it (see README.md).
# - Predictor: predict(ctx, winner, allowed, rng) -> str, one of `allowed`. ctx is the coin toss scenario's
#   TossContext.
# - CHOICES: receive (take the ball), kick (give it away), defer (kick now and choose at the second half).
# END
CHOICES = ("receive", "kick", "defer")
