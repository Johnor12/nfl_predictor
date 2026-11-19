# START
# The run-or-pass model's inputs: what the offense knows at the snap, as one row of numbers.
# - NAMES: the feature names, in the model's column order. RATINGS: the last two, read exactly.
# - features(ctx, group, shotgun, box) -> list[float]: one play's values (nan where unknown): the situation
#   and the game so far (events.situation), the offense's personnel group (`Lineup.personnel`), whether it
#   is in the shotgun, the defenders in the box, and two pass ratings (events.strength.rating: dropbacks
#   over expected per play, shrunk by OFFENSE_PLAYS and DEFENSE_PLAYS): how much more than its situations
#   called for this offense has passed, and offenses against this defense. The same function reads a
#   simulated play (predict) and a real one (train.py), so the two can't drift apart.
# END
from events import situation, strength

RATINGS = ("offense_pass_over", "defense_pass_over")  # shrunk already: read exactly
NAMES = situation.NAMES + situation.PERSONNEL + ("shotgun", "box") + RATINGS
OFFENSE_PLAYS, DEFENSE_PLAYS = 300, 600  # the plays a pass rating is shrunk by


def features(ctx, group, shotgun, box) -> list[float]:
    offense, defense = ctx.game.form(ctx.situation.offense), ctx.game.form(ctx.situation.defense)
    return (situation.features(ctx) + situation.personnel(group) + [shotgun, box]
            + [strength.rating(offense, "dropbacks_over", "plays", OFFENSE_PLAYS),
               strength.rating(defense, "allowed_dropbacks_over", "allowed_plays", DEFENSE_PLAYS)])
