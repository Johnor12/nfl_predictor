# START
# The coin toss scenario's public API.
# - run_coin_toss(ctx, predictors, rng) -> Toss: who won, what they chose, and who kicks off.
# - TossContext (input), Toss (output), allowed_choices(ctx).
# - TossPredictors (one function per event) and load_toss_predictors (each event's implementation by name).
# END
from scenarios.coin_toss.toss import Toss, TossContext, TossPredictors, allowed_choices, load_toss_predictors, run_coin_toss

__all__ = ["run_coin_toss", "Toss", "TossContext", "TossPredictors", "load_toss_predictors", "allowed_choices"]
