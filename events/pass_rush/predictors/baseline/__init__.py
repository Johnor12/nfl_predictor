# START
# Baseline pass rush predictor: the dropback's result, rushers, sack yardage, and quarterback hits from the priors.
# - predict(ctx, lineups, formation, defense, rng) -> PassRush.
# Hand-set: time to throw, sack, scramble, or throw away, and the split-sack rate.
# END
from events.pass_rush import PassRush
from shared.priors import choice, hist, pick, pick_many, priors_of, rate

load_priors = priors_of(__file__)  # season -> priors dict
SECONDS = {"throw": (2.7, 0.6), "scramble": (3.3, 0.7), "throwaway": (3.6, 0.8)}  # mean, sd


def predict(ctx, lineups, formation, defense, rng):
    p = load_priors(ctx.game.season)
    outcome = choice(p["dropback"], rng)
    rushers = int(min(8, max(3, hist(p["rushers"], rng))))
    defenders = lineups.defense.players
    if outcome == "sack":
        sackers = pick_many(ctx, defenders, p["sacker"], 2 if rng.random() < 0.1 else 1, rng)
        result = "strip_sack" if rng.random() < rate(p["strip_sack"], "fumble") else "sack"
        return PassRush(rushers, result, max(1.5, rng.gauss(3.4, 0.8)), sackers, sackers,
                        max(0.0, hist(p["sack_yards"], rng)))
    hit = outcome == "throw" and rng.random() < rate(p["qb_hit"], "hit")
    hitters = (pick(ctx, defenders, p["sacker"], rng),) if hit else ()
    mean, sd = SECONDS[outcome]
    return PassRush(rushers, outcome, max(1.0, rng.gauss(mean, sd)), hitters)
