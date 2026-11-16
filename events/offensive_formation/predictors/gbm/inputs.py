# START
# The shotgun model's inputs: what the offense knows as it lines up, as one row of numbers.
# - NAMES: the feature names, in the model's column order. WHO: the ones about the team, which the model
#   reads coarsely (shared.models).
# - features(ctx, group) -> list[float]: one play's values (nan where unknown): the situation and the game
#   so far (events.situation), the offense's personnel group (`Lineup.personnel`, None where the data
#   doesn't say), and how often this team has been in the shotgun: this season before the game, over earlier
#   seasons, and the plays this season's rate rests on (events.strength, from the team's form). The same
#   function reads a simulated play (predict) and a real one (train.py).
# END
from events import situation, strength

WHO = ("team_shotgun", "team_shotgun_before", "team_plays")
NAMES = situation.NAMES + situation.PERSONNEL + WHO


def features(ctx, group) -> list[float]:
    team = ctx.game.form(ctx.situation.offense)
    return (situation.features(ctx) + situation.personnel(group)
            + strength.rates(team, "shotgun", "plays") + [strength.total(team, "plays")])
