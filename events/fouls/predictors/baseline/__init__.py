# START
# Baseline fouls predictor: at most one foul per play, at the real rate for the kind of play.
# - predict(ctx, lineups, record, allowed, rng) -> tuple[Foul, ...].
# Hand-set: the foul's timing when several are possible, its spot, and who committed it (shared.priors.fouler).
# Internals: _category (run, pass, punt, field_goal, or kickoff, from the record), _foul_spot.
# END
from events.fouls import Foul
from events.snap import Snap
from scenarios.play import Carry, Kick, Pass, facts
from shared.priors import choice, fouler, priors_of

load_priors = priors_of(__file__)  # season -> priors dict
KICK_CATEGORIES = {"punt": "punt", "field_goal": "field_goal", "pat": "field_goal"}


def predict(ctx, lineups, record, allowed, rng):
    s = ctx.situation
    p = load_priors(ctx.game.season)
    category = _category(record)
    rates = {key: count / p["snaps"][category] for key, count in p["fouls"].get(category, {}).items()}
    if rng.random() >= sum(rates.values()):
        return ()
    name, side = choice(rates, rng).split("|")
    team = s.offense if side == "offense" else s.defense
    timings = [t for t in ("live", "return", "after") if (name, team, t) in allowed]
    if not timings:
        return ()
    if "return" in timings and category in ("punt", "kickoff") and team == s.defense:
        timing = "return"
    elif "after" in timings and (timings == ["after"] or rng.random() < 0.5):
        timing = "after"
    else:
        timing = timings[0]
    passes = facts(record, Pass)
    grounding = name == "intentional_grounding" and passes
    player = passes[0].passer if grounding else fouler(ctx, lineups, name, team, rng)
    return (Foul(name, team, player, _foul_spot(ctx, record, name, timing, rng), timing),)


def _category(record):
    kicks = facts(record, Kick)
    if kicks:
        return KICK_CATEGORIES.get(kicks[0].kind, "kickoff")
    return "run" if facts(record, Snap)[0].action in ("run", "kneel") else "pass"


def _foul_spot(ctx, record, name, timing, rng):
    los = ctx.situation.x
    returns = [c for c in facts(record, Carry) if c.team != ctx.situation.offense]
    if timing == "return" and returns:
        return rng.uniform(min(returns[-1].start, returns[-1].end), max(returns[-1].start, returns[-1].end))
    targets = [p for p in facts(record, Pass) if p.receiver]
    if name == "defensive_pass_interference" and targets:
        return targets[0].x
    if name == "intentional_grounding":
        return los - rng.uniform(3, 9)
    if name in ("offensive_holding", "illegal_block_in_the_back"):
        return los + rng.uniform(-3, 5)
    return los
