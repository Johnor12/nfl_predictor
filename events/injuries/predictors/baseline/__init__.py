# START
# Baseline injuries predictor: at most one injury per play, at the real rate.
# - predict(ctx, lineups, record, rng) -> tuple[Injury, ...].
# Hand-set: ball carriers and tacklers are hurt more often than the rest, and how long the player is out.
# END
from events.injuries import Injury
from scenarios.play import Carry, facts
from shared.priors import priors_of

load_priors = priors_of(__file__)  # season -> priors dict


def predict(ctx, lineups, record, rng):
    injury = load_priors(ctx.game.season)["injury"]
    if rng.random() >= injury["injured"] / injury["plays"]:
        return ()
    carries = facts(record, Carry)
    involved = [c.player for c in carries] + [t for c in carries for t in c.tacklers]
    everyone = lineups.offense.players + lineups.defense.players
    player = rng.choice(involved) if involved and rng.random() < 0.6 else rng.choice(everyone)
    return (Injury(player, rng.choices([2, 8, 999], [0.45, 0.2, 0.35])[0]),)
