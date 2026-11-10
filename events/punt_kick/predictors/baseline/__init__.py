# START
# Baseline punt kick predictor: block rate and punt distance by field position, from the priors.
# - predict(ctx, lineups, punter, rng) -> PuntKick.
# Hand-set: who blocks punts and hang time.
# END
from events.punt_kick import PuntKick
from shared.priors import field_bucket, hist, pick, priors_of, rate

load_priors = priors_of(__file__)  # season -> priors dict


def predict(ctx, lineups, punter, rng):
    p = load_priors(ctx.game.season)
    if rng.random() < rate(p["punt_blocked"], "yes"):
        return PuntKick(0.0, pick(ctx, lineups.defense.players, {"DL": 5, "LB": 3, "DB": 2}, rng), 2.0)
    distances = p["punt_distance"].get(field_bucket(ctx.situation.x)) or p["punt_distance"]["3"]
    return PuntKick(hist(distances, rng), None, max(4.5, rng.gauss(6.0, 0.5)))
