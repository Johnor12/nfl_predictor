# START
# Baseline snap predictor: run or pass by game script, down, and distance; the ball carrier by how often each
# back on the field carries when he is out there (by depth chart role, and his own carries this season).
# - predict(ctx, lineups, formation, defense, allowed, rng, pass_rate=pass_rate) -> Snap. Another
#   implementation can hand in its own `pass_rate` and keep the rest (events/snap/predictors/gbm).
# - pass_rate(ctx, lineups, formation, defense) -> float: how often the offense drops back here (the
#   script's rate backed off to the normal script's; the two-point play mix on a try).
# A punt or field goal unit kicks, or fakes it (a run or a pass) at the real rate.
# Hand-set: the bad snap rate, kneels from the victory formation, spikes late in a half with no timeouts, and
# who runs with a fake (anyone in the backfield).
# END
from events.snap import Snap
from shared.priors import blend, choice, dist_bucket, priors_of, rate, script, usage

load_priors = priors_of(__file__)  # (season, week) -> priors dict


def pass_rate(ctx, lineups, formation, defense) -> float:
    s = ctx.situation
    p = load_priors(ctx.game.season, ctx.game.week)
    if s.kind == "try":
        return rate(p["two_point_play"], "pass")
    key = f"{s.down}|{dist_bucket(s.distance)}"
    counts = p["pass_rate"].get(f"{script(s)}|{key}", {})
    return rate(blend(counts, p["pass_rate"].get(f"normal|{key}", {})), "pass")


def predict(ctx, lineups, formation, defense, allowed, rng, pass_rate=pass_rate):
    s = ctx.situation
    p = load_priors(ctx.game.season, ctx.game.week)
    bad = rng.random() < 0.003
    unit = lineups.offense.unit
    if unit in ("punt", "field_goal"):
        fakes = p.get("fake", {}).get(unit, {}) if s.kind == "scrimmage" else {}
        action = choice({a: n for a, n in fakes.items() if a == "kick" or a in allowed}, rng) if fakes else "kick"
        if action == "run":
            return Snap("run", rng.choice(formation.backfield), bad)
        return Snap(unit if action == "kick" else "pass", bad_snap=bad)
    if unit == "victory":
        return Snap("kneel")
    lead = s.score[s.offense] - s.score[s.defense]
    if (s.kind == "scrimmage" and s.clock_running and s.quarter in (2, 4) and s.clock <= 30 and s.down < 4
            and s.timeouts[s.offense] == 0 and (s.quarter == 2 or lead <= 0) and rng.random() < 0.6):
        return Snap("spike")  # hand-set
    if rng.random() < pass_rate(ctx, lineups, formation, defense):
        return Snap("pass", bad_snap=bad)
    backs = list(formation.backfield)
    weights = [usage(ctx.by_id[pid], "carries", "carried", p["carry_rate"], p["carries_per_snap"]) or 0.001
               for pid in backs]
    return Snap("run", rng.choices(backs, weights)[0], bad)

