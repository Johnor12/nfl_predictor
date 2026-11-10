# START
# Baseline snap predictor: run or pass by game script, down, and distance; the ball carrier by depth chart role.
# - predict(ctx, lineups, formation, defense, allowed, rng) -> Snap.
# Hand-set: the bad snap rate, kneels from the victory formation, and spikes late in a half with no timeouts.
# Internals: _pass_rate (the script's rate backed off to the normal script's).
# END
from events.snap import Snap
from shared.priors import blend, dist_bucket, priors_of, rate, role, script

load_priors = priors_of(__file__)  # season -> priors dict


def predict(ctx, lineups, formation, defense, allowed, rng):
    s = ctx.situation
    p = load_priors(ctx.game.season)
    bad = rng.random() < 0.003
    unit = lineups.offense.unit
    if unit in ("punt", "field_goal"):
        return Snap(unit, bad_snap=bad)
    if unit == "victory":
        return Snap("kneel")
    lead = s.score[s.offense] - s.score[s.defense]
    if (s.kind == "scrimmage" and s.clock_running and s.quarter in (2, 4) and s.clock <= 30 and s.down < 4
            and s.timeouts[s.offense] == 0 and (s.quarter == 2 or lead <= 0) and rng.random() < 0.6):
        return Snap("spike")  # hand-set
    if rng.random() < _pass_rate(s, p):
        return Snap("pass", bad_snap=bad)
    backs = list(formation.backfield)
    weights = [p["run_carrier"].get(role(ctx.by_id[pid]), 1) for pid in backs]
    return Snap("run", rng.choices(backs, weights)[0], bad)


def _pass_rate(s, p):
    if s.kind == "try":
        return rate(p["two_point_play"], "pass")
    key = f"{s.down}|{dist_bucket(s.distance)}"
    counts = p["pass_rate"].get(f"{script(s)}|{key}", {})
    return rate(blend(counts, p["pass_rate"].get(f"normal|{key}", {})), "pass")
