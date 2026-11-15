# START
# Baseline pass rush predictor: the dropback's result, rushers, sack yardage, and quarterback hits from the priors.
# - predict(ctx, lineups, formation, defense, rng) -> PassRush.
# Hand-set: time to throw, scramble, or throw away, how long a sack takes, the split-sack rate, and DROPBACKS.
# Internals: _dropback (the league's sack and scramble rates, moved toward the quarterback's own this season).
# END
from events.pass_rush import PassRush
from shared.priors import choice, hist, pick, pick_many, priors_of, rate

load_priors = priors_of(__file__)  # (season, week) -> priors dict
SECONDS = {"throw": (2.7, 0.6), "scramble": (3.3, 0.7), "throwaway": (3.6, 0.8)}  # mean, sd
DROPBACKS = 150  # a quarterback's own season counts as much as the league once he has dropped back this often
OWN = {"sack": "times_sacked", "scramble": "scrambles"}  # dropback result -> the quarterback's season stat


def predict(ctx, lineups, formation, defense, rng):
    p = load_priors(ctx.game.season, ctx.game.week)
    outcome = choice(_dropback(ctx.by_id[formation.qb], p["dropback"]), rng)
    if outcome == "throw" and rng.random() < rate(p["throwaway"], "yes"):
        outcome = "throwaway"
    rushers = int(min(8, max(3, hist(p["rushers"], rng))))
    defenders = lineups.defense.players
    if outcome == "sack":
        sackers = pick_many(ctx, defenders, p["sacker"], 2 if rng.random() < 0.1 else 1, rng)
        result = "strip_sack" if rng.random() < rate(p["strip_sack"], "fumble") else "sack"
        return PassRush(rushers, result, max(2.5, rng.gauss(5.5, 1.0)), sackers, sackers,
                        max(0.0, hist(p["sack_yards"], rng)))
    hit = outcome == "throw" and rng.random() < rate(p["qb_hit"], "hit")
    hitters = (pick(ctx, defenders, p["sacker"], rng),) if hit else ()
    mean, sd = SECONDS[outcome]
    return PassRush(rushers, outcome, max(1.0, rng.gauss(mean, sd)), hitters)


def _dropback(qb, league) -> dict:
    """Throw, sack, or scramble: how often the quarterback has been sacked and has scrambled this season,
    shrunk toward the league's rates by DROPBACKS dropbacks."""
    dropbacks = qb.stats.get("dropbacks", 0)
    if not dropbacks:
        return league
    total = sum(league.values())
    rates = {key: (qb.stats.get(stat, 0) + DROPBACKS * league[key] / total) / (dropbacks + DROPBACKS)
             for key, stat in OWN.items()}
    return {**rates, "throw": 1 - sum(rates.values())}
