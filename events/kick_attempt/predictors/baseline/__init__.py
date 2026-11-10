# START
# Baseline kick attempt predictor: field goals by distance bin and extra points, from the priors.
# - predict(ctx, lineups, kicker, distance, rng) -> KickAttempt.
# Hand-set: no makes beyond 66 yards, who blocks kicks, and the kick's duration.
# END
from events.kick_attempt import KickAttempt
from shared.priors import choice, fg_bin, pick, priors_of

load_priors = priors_of(__file__)  # season -> priors dict


def predict(ctx, lineups, kicker, distance, rng):
    p = load_priors(ctx.game.season)
    if ctx.situation.kind == "try":
        pat = p["pat"]
        counts = {"good": pat.get("good", 0), "no_good": pat.get("failed", 0), "blocked": pat.get("blocked", 0)}
    else:
        fg = p["fg"].get(fg_bin(distance), {})
        counts = {"good": fg.get("made", 0), "no_good": fg.get("missed", 0) + (distance > 66) * 1000,
                  "blocked": fg.get("blocked", 0)}
    result = choice(counts, rng)
    blocker = pick(ctx, lineups.defense.players, {"DL": 8, "LB": 1, "DB": 1}, rng) if result == "blocked" else None
    return KickAttempt(result, blocker, max(3.0, rng.gauss(4.0, 0.3)))
