# START
# Baseline punt result predictor: fair catch, return, downed, out of bounds, or muff by where the punt lands.
# - predict(ctx, lineups, landing_x, allowed, rng) -> PuntResult.
# The returner is the top punt returner on the field by depth chart.
# END
from events.punt_result import PuntResult
from shared.priors import choice, priors_of, returner

load_priors = priors_of(__file__)  # season -> priors dict


def predict(ctx, lineups, landing_x, allowed, rng):
    if allowed == ("touchback",):
        return PuntResult("touchback")
    r = 100 - landing_x
    bucket = "inside_10" if r <= 10 else "inside_20" if r <= 20 else "open"
    results = load_priors(ctx.game.season)["punt_result"][bucket]
    result = choice({k: v for k, v in results.items() if k in allowed}, rng)
    player = returner(ctx, lineups.defense.players, "PR", rng)
    return PuntResult(result, player if result in ("fair_catch", "return", "muff") else None)
