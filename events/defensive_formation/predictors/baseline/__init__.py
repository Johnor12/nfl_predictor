# START
# Baseline defensive formation predictor: box count from the priors, deep safeties hand-set.
# - predict(ctx, lineups, formation, rng) -> DefensiveFormation.
# END
from events.defensive_formation import DefensiveFormation
from shared.priors import dist_bucket, hist, priors_of

load_priors = priors_of(__file__)  # season -> priors dict


def predict(ctx, lineups, formation, rng):
    s = ctx.situation
    boxes = load_priors(ctx.game.season)["box"].get(f"{s.down}|{dist_bucket(s.distance)}") if s.kind == "scrimmage" else None
    box = int(hist(boxes, rng)) if boxes else 8
    return DefensiveFormation(box, 2 if (s.distance or 10) >= 7 and rng.random() < 0.6 else 1)
