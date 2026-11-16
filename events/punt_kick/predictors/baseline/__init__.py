# START
# Baseline punt kick predictor: block rate and punt distance by field position, from the priors.
# - predict(ctx, lineups, punter, rng, distance=distance) -> PuntKick. Another implementation can hand in its
#   own `distance` and keep the rest (events/punt_kick/predictors/gbm).
# - distance(ctx, punter, rng) -> float: how far the punt goes, drawn from histogram(ctx).
# - histogram(ctx) -> {"yards": count}: the distances of punts from this part of the field.
# Hand-set: who blocks punts and hang time.
# END
from events.punt_kick import PuntKick
from shared.priors import field_bucket, hist, pick, priors_of, rate

load_priors = priors_of(__file__)  # (season, week) -> priors dict


def histogram(ctx) -> dict:
    p = load_priors(ctx.game.season, ctx.game.week)
    return p["punt_distance"].get(field_bucket(ctx.situation.x)) or p["punt_distance"]["3"]


def distance(ctx, punter, rng) -> float:
    return hist(histogram(ctx), rng)


def predict(ctx, lineups, punter, rng, distance=distance):
    p = load_priors(ctx.game.season, ctx.game.week)
    if rng.random() < rate(p["punt_blocked"], "yes"):
        return PuntKick(0.0, pick(ctx, lineups.defense.players, {"DL": 5, "LB": 3, "DB": 2}, rng), 2.0)
    return PuntKick(distance(ctx, punter, rng), None, max(5.0, rng.gauss(7.0, 0.5)))
