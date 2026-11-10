# START
# Baseline loose ball predictor: who recovers, near the spot of the ball.
# - predict(ctx, lineups, cause, x, last_team, rng) -> Recovery.
# From data: how often a fumble is lost. Hand-set: recovery odds for bad snaps, muffs, and blocked kicks,
# fumbles out of bounds, the recovering player (anyone on the field), and where and how long it takes.
# END
from events.loose_ball import Recovery
from shared.priors import on_field, priors_of, rate

load_priors = priors_of(__file__)  # season -> priors dict


def predict(ctx, lineups, cause, x, last_team, rng):
    s = ctx.situation
    other = s.defense if last_team == s.offense else s.offense
    if cause == "fumble" and rng.random() < 0.04:
        ahead = 1 if last_team == s.offense else -1
        return Recovery(None, None, x + ahead * rng.uniform(-2, 4), 1.0)
    lost = {"fumble": rate(load_priors(ctx.game.season)["fumble_recovery"], "lost"), "bad_snap": 0.2, "muff": 0.45,
            "blocked_kick": 0.6}[cause]
    team = other if rng.random() < lost else last_team
    return Recovery(team, rng.choice(on_field(ctx, lineups, team)), x + rng.uniform(-3, 3), rng.uniform(0.5, 2.0))
