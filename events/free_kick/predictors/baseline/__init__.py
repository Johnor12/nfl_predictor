# START
# Baseline free kick predictor: kickoff distance and out-of-bounds rate from the priors.
# - predict(ctx, lineups, onside, rng) -> FreeKick.
# Hand-set: onside kicks travel 10-15 yards, and hang time. The kicker is the K (else the P) on the field.
# END
from events.free_kick import FreeKick
from shared.priors import hist, priors_of, rate

load_priors = priors_of(__file__)  # season -> priors dict


def predict(ctx, lineups, onside, rng):
    players = lineups.offense.players
    kicker = next((pid for pid in players if ctx.by_id[pid].position == "K"),
                  next((pid for pid in players if ctx.by_id[pid].position == "P"), players[0]))
    if onside:
        return FreeKick(kicker, rng.uniform(10, 15), False, 2.0)
    p = load_priors(ctx.game.season)
    out_of_bounds = rng.random() < rate(p["kickoff_oob"], "yes")
    return FreeKick(kicker, hist(p["kickoff_distance"], rng), out_of_bounds, max(3.0, rng.gauss(4.0, 0.3)))
