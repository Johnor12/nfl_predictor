# START
# Baseline pre-snap predictor: play clock used (hand-set by game script) and pre-snap fouls at the real rate.
# - predict(ctx, lineups, formation, allowed, rng) -> PreSnap.
# Internals: _play_clock_used (hurry, bleed, or normal pace).
# END
from events.fouls import Foul
from events.pre_snap import PreSnap
from shared.priors import choice, fouler, priors_of, script

load_priors = priors_of(__file__)  # season -> priors dict


def predict(ctx, lineups, formation, allowed, rng):
    s = ctx.situation
    p = load_priors(ctx.game.season)
    rates = {key: count / p["snaps"]["n"] for key, count in p["fouls"].items()}
    foul = None
    if rng.random() < sum(rates.values()):
        name, side = choice(rates, rng).split("|")
        team = s.offense if side == "offense" else s.defense
        timing = next((t for t in ("presnap", "snap") if (name, team, t) in allowed), None)
        if timing:
            player = formation.qb if name == "delay_of_game" else fouler(ctx, lineups, name, team, rng)
            foul = Foul(name, team, player, s.x, timing)
    return PreSnap(_play_clock_used(s, rng), foul)


def _play_clock_used(s, rng):  # hand-set
    clock = s.play_clock
    pace = script(s) if s.kind == "scrimmage" else "normal"
    if pace == "hurry" and s.clock_running:
        return rng.uniform(8, 18)
    if pace == "bleed":
        return rng.uniform(clock - 3, clock - 0.5)
    return rng.uniform(clock - 15, clock - 3)
