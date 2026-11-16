# START
# Baseline pass rush predictor: the dropback's result, rushers, sack yardage, and quarterback hits from the priors.
# - predict(ctx, lineups, formation, defense, rng, dropback=dropback) -> PassRush. Another implementation can
#   hand in its own `dropback` and keep the rest (events/pass_rush/predictors/gbm).
# - dropback(ctx, formation, league) -> {"throw": weight, "sack": weight, "scramble": weight}: the league's
#   sack and scramble rates (the priors' `dropback` counts), moved toward the quarterback's own this season.
# Who sacks or hits him: by position group, and each defender's own sacks and hits per snap
# (shared.priors.PASS_RUSH). What a charter adds, at the charted rates: who blitzed on the dropback, and who
# hurried a throw the quarterback wasn't hit on (each by position group and the defender's own past).
# Hand-set: time to throw, scramble, or throw away, how long a sack takes, and DROPBACKS.
# END
from events.pass_rush import PassRush
from shared.priors import BLITZES, HURRIES, PASS_RUSH, choice, hist, pick, pick_many, priors_of, rate, some

load_priors = priors_of(__file__)  # (season, week) -> priors dict
SECONDS = {"throw": (2.7, 0.6), "scramble": (3.3, 0.7), "throwaway": (3.6, 0.8)}  # mean, sd
DROPBACKS = 150  # a quarterback's own season counts as much as the league once he has dropped back this often
OWN = {"sack": "times_sacked", "scramble": "scrambles"}  # dropback result -> the quarterback's season stat


def dropback(ctx, formation, league) -> dict:
    """Throw, sack, or scramble: how often the quarterback has been sacked and has scrambled this season,
    shrunk toward the league's rates by DROPBACKS dropbacks."""
    qb = ctx.by_id[formation.qb]
    dropbacks = qb.stats.get("dropbacks", 0)
    if not dropbacks:
        return league
    total = sum(league.values())
    rates = {key: (qb.stats.get(stat, 0) + DROPBACKS * league[key] / total) / (dropbacks + DROPBACKS)
             for key, stat in OWN.items()}
    return {**rates, "throw": 1 - sum(rates.values())}


def predict(ctx, lineups, formation, defense, rng, dropback=dropback):
    p = load_priors(ctx.game.season, ctx.game.week)
    outcome = choice(dropback(ctx, formation, p["dropback"]), rng)
    if outcome == "throw" and rng.random() < rate(p["throwaway"], "yes"):
        outcome = "throwaway"
    rushers = int(min(8, max(3, hist(p["rushers"], rng))))
    defenders = lineups.defense.players
    blitzers = some(ctx, defenders, rng, p.get("blitzed"), p.get("second_blitzer"), p.get("blitzer"), BLITZES)
    if outcome == "sack":
        shared = rng.random() < rate(p["shared_sack"], "yes")
        sackers = pick_many(ctx, defenders, p["sacker"], 2 if shared else 1, rng, PASS_RUSH)
        result = "strip_sack" if rng.random() < rate(p["strip_sack"], "fumble") else "sack"
        return PassRush(rushers, result, max(2.5, rng.gauss(5.5, 1.0)), sackers, sackers,
                        max(0.0, hist(p["sack_yards"], rng)), blitzers=blitzers)
    hit = outcome == "throw" and rng.random() < rate(p["qb_hit"], "hit")
    hitters = (pick(ctx, defenders, p["sacker"], rng, own=PASS_RUSH),) if hit else ()
    thrown = outcome in ("throw", "throwaway") and not hit
    hurriers = some(ctx, defenders, rng, thrown and p.get("hurried"), p.get("second_hurrier"), p.get("hurrier"), HURRIES)
    mean, sd = SECONDS[outcome]
    return PassRush(rushers, outcome, max(1.0, rng.gauss(mean, sd)), hitters, hurriers=hurriers, blitzers=blitzers)
