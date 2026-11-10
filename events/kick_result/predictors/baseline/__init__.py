# START
# Baseline kick result predictor: return, touchback, or muff by where the kickoff comes down.
# - predict(ctx, lineups, landing_x, allowed, rng) -> KickResult.
# Hand-set: onside recovery rate, muff rate, and fair catch rate (where fair catches are allowed).
# The returner is the top kick returner on the field by depth chart.
# END
from events.kick_result import KickResult
from shared.priors import choice, priors_of, returner

load_priors = priors_of(__file__)  # season -> priors dict


def predict(ctx, lineups, landing_x, allowed, rng):
    receivers = lineups.defense.players
    if "kicking_recovery" in allowed:  # onside kick
        if rng.random() < 0.15:
            return KickResult("kicking_recovery", rng.choice(lineups.offense.players))
        return KickResult("return", returner(ctx, receivers, "KR", rng))
    zone = "end_zone" if landing_x >= 100 else "landing_zone"
    weights = {k: v for k, v in load_priors(ctx.game.season)["kickoff_result"][zone].items() if k in allowed}
    total = sum(weights.values())
    if "muff" in allowed:
        weights["muff"] = weights.get("muff", 0) + 0.01 * total
    if "fair_catch" in allowed:
        weights["fair_catch"] = 0.3 * total
    result = choice(weights, rng)
    return KickResult(result, None if result == "touchback" else returner(ctx, receivers, "KR", rng))
