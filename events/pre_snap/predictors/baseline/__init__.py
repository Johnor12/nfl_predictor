# START
# Baseline pre-snap predictor: play clock used (by game script: from the real time between snaps on a full
# play clock, hand-set after an administrative stoppage) and pre-snap fouls at the real rate, on the
# position groups they are called on and each player's own flags (shared.priors.fouler).
# - predict(ctx, lineups, formation, allowed, rng) -> PreSnap.
# Internals: _play_clock_used (hurry, bleed, or normal pace).
# END
from events.fouls import Foul
from events.pre_snap import PreSnap
from shared.priors import choice, fouler, priors_of, script, wait
from shared.rulebook import rules_for

load_priors = priors_of(__file__)  # (season, week) -> priors dict


def predict(ctx, lineups, formation, allowed, rng):
    s = ctx.situation
    p = load_priors(ctx.game.season, ctx.game.week)
    rates = {key: count / p["snaps"]["n"] for key, count in p["fouls"].items()}
    foul = None
    if rng.random() < sum(rates.values()):
        name, side = choice(rates, rng).split("|")
        team = s.offense if side == "offense" else s.defense
        timing = next((t for t in ("presnap", "snap") if (name, team, t) in allowed), None)
        if timing:
            groups = p.get("fouler", {}).get(name)
            player = formation.qb if name == "delay_of_game" else fouler(ctx, lineups, name, team, rng, groups)
            foul = Foul(name, team, player, s.x, timing)
    return PreSnap(_play_clock_used(ctx, p, rng), foul)


def _play_clock_used(ctx, p, rng):
    s = ctx.situation
    clock = s.play_clock
    pace = script(s) if s.kind == "scrimmage" else "normal"
    if clock == rules_for(ctx.game.season).play_clock and s.clock_running:
        return min(clock - 1.0, wait(p["snap_gap"][pace], rng))
    if pace == "hurry" and s.clock_running:  # the rest is hand-set
        return rng.uniform(8, 18)
    if pace == "bleed":
        return rng.uniform(clock - 3, clock - 0.5)
    return rng.uniform(clock - 15, clock - 3)
