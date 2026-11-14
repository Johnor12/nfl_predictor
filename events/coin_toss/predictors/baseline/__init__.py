# START
# Baseline coin toss predictor: a fair coin.
# - predict(ctx, rng) -> str: the home or the away team, 50/50.
# END


def predict(ctx, rng):
    return ctx.game.home if rng.random() < 0.5 else ctx.game.away
